"""
V4.9.4 tests — hermes-pattern enhancements (Bedrock-only fit).

Covers all 6 items from the v4.9.4 cross-repo enhancement pass:

  1. IterationBudget — shared parent + sub-agent counter
  2. ErrorClassifier — categorises Bedrock SDK exceptions
  3. RetryPolicy — jittered exponential backoff decisions
  4. Compactor._prune_tool_results_for_summary — pre-LLM oversized tool_result trim
  5. Compactor._summary_client — opt-in auxiliary model for compaction
  6. Compactor.create_summary_prompt — structured "Resolved / Pending Questions" sections

Run: python test_v494_hermes_patterns.py
"""

from __future__ import annotations
import os
import sys
import logging
import traceback
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa  # type: ignore

# Silence import-time CSO warnings during tests
logging.disable(logging.WARNING)

RESULTS: List[Tuple[str, bool, str]] = []


def _run(name: str, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
        print(f"  ok  {name}")
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
        print(f"  FAIL {name}")
        print(f"       AssertionError: {e}")
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"  FAIL {name}")
        print(f"       {type(e).__name__}: {e}")
        traceback.print_exc()


# ============================================================
# Item 1 — IterationBudget
# ============================================================

def test_iteration_budget_basic_consume():
    b = sa.IterationBudget(max_iterations=3)
    assert b.consume() is True
    assert b.consume() is True
    assert b.consume() is True
    assert b.used() == 3
    assert b.remaining() == 0


def test_iteration_budget_exhaust_returns_false():
    b = sa.IterationBudget(max_iterations=2)
    assert b.consume() is True
    assert b.consume() is True
    assert b.consume() is False, "fourth consume should fail (budget exhausted)"
    assert b.used() == 2  # used count must NOT increment past max
    assert b.consume() is False  # still false on subsequent calls


def test_iteration_budget_default_ceiling():
    b = sa.IterationBudget()
    assert b.total() == sa.IterationBudget.DEFAULT_MAX
    assert b.remaining() == sa.IterationBudget.DEFAULT_MAX


def test_iteration_budget_zero_or_negative_clamped():
    b = sa.IterationBudget(max_iterations=0)
    assert b.total() == 1, "zero/negative should clamp to 1"
    b2 = sa.IterationBudget(max_iterations=-5)
    assert b2.total() == 1


def test_iteration_budget_threadsafe_no_overshoot():
    """Concurrent consumes must never collectively exceed the ceiling."""
    import threading
    b = sa.IterationBudget(max_iterations=100)
    successes = []

    def worker():
        for _ in range(50):
            if b.consume():
                successes.append(1)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(successes) == 100, f"expected exactly 100 successful consumes, got {len(successes)}"
    assert b.used() == 100


# ============================================================
# Item 2 — ErrorClassifier
# ============================================================

def _classify(msg):
    return sa.ErrorClassifier.classify(Exception(msg))


def test_classifier_throttle():
    cat, rec, _ = _classify("ThrottlingException: Rate exceeded")
    assert cat == sa.BedrockErrorCategory.THROTTLE
    assert rec == sa.BedrockErrorCategory.RECOVERY_RETRY_JITTER


def test_classifier_validation_cache():
    cat, rec, _ = _classify("ValidationException: cache_control not supported on this model")
    assert cat == sa.BedrockErrorCategory.VALIDATION_CACHE
    assert rec == sa.BedrockErrorCategory.RECOVERY_RETRY_ONCE


def test_classifier_validation_other():
    cat, rec, _ = _classify("ValidationException: invalid request body")
    assert cat == sa.BedrockErrorCategory.VALIDATION_OTHER
    assert rec == sa.BedrockErrorCategory.RECOVERY_ABORT


def test_classifier_context_overflow():
    cat, rec, _ = _classify("Prompt is too long for this model")
    assert cat == sa.BedrockErrorCategory.CONTEXT_OVERFLOW
    assert rec == sa.BedrockErrorCategory.RECOVERY_SHRINK_INPUT


def test_classifier_model_not_ready():
    cat, rec, _ = _classify("ModelNotReadyException: model is loading")
    assert cat == sa.BedrockErrorCategory.MODEL_NOT_READY
    assert rec == sa.BedrockErrorCategory.RECOVERY_RETRY_JITTER


def test_classifier_model_timeout():
    cat, rec, _ = _classify("ModelTimeoutException: model timed out")
    assert cat == sa.BedrockErrorCategory.MODEL_TIMEOUT
    assert rec == sa.BedrockErrorCategory.RECOVERY_RETRY_JITTER


def test_classifier_access_denied():
    cat, rec, _ = _classify("AccessDeniedException: not authorized for this model")
    assert cat == sa.BedrockErrorCategory.ACCESS_DENIED
    assert rec == sa.BedrockErrorCategory.RECOVERY_ABORT


def test_classifier_service_unavailable():
    cat, rec, _ = _classify("ServiceUnavailableException: service is unavailable")
    assert cat == sa.BedrockErrorCategory.SERVICE_UNAVAILABLE
    assert rec == sa.BedrockErrorCategory.RECOVERY_RETRY_JITTER


def test_classifier_transient_network():
    cat, rec, _ = _classify("ConnectionResetError: connection reset by peer")
    assert cat == sa.BedrockErrorCategory.TRANSIENT_NETWORK
    assert rec == sa.BedrockErrorCategory.RECOVERY_RETRY_JITTER


def test_classifier_unknown_default():
    cat, rec, _ = _classify("Some completely unrelated error message")
    assert cat == sa.BedrockErrorCategory.UNKNOWN
    assert rec == sa.BedrockErrorCategory.RECOVERY_ABORT


# ============================================================
# Item 3 — RetryPolicy
# ============================================================

def test_retry_policy_should_retry_on_jitter_recovery():
    assert sa.RetryPolicy.should_retry(0, sa.BedrockErrorCategory.RECOVERY_RETRY_JITTER) is True


def test_retry_policy_no_retry_on_abort():
    assert sa.RetryPolicy.should_retry(0, sa.BedrockErrorCategory.RECOVERY_ABORT) is False


def test_retry_policy_no_retry_past_max():
    over = sa.RetryPolicy.MAX_RETRIES + 1
    assert sa.RetryPolicy.should_retry(over, sa.BedrockErrorCategory.RECOVERY_RETRY_JITTER) is False


def test_retry_policy_backoff_growing_with_jitter():
    """Backoff should be in the half-open interval [0, cap_for_attempt)."""
    for attempt in range(5):
        s = sa.RetryPolicy.backoff_seconds(attempt)
        assert 0 <= s <= sa.RetryPolicy.CAP_SECONDS, f"attempt {attempt}: {s} out of range"


def test_retry_policy_negative_attempt_handled():
    s = sa.RetryPolicy.backoff_seconds(-1)
    assert 0 <= s <= sa.RetryPolicy.BASE_SECONDS


# ============================================================
# Item 4 — Compactor._prune_tool_results_for_summary
# ============================================================

def test_prune_passes_small_tool_results_unchanged():
    msgs = [
        {"role": "user", "content": "hi"},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "tiny"}]},
    ]
    out = sa.Compactor._prune_tool_results_for_summary(msgs)
    assert out[1]["content"][0]["content"] == "tiny"


def test_prune_trims_large_string_tool_result():
    big = "X" * 5000
    msgs = [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": big}]}]
    out = sa.Compactor._prune_tool_results_for_summary(msgs)
    pruned = out[0]["content"][0]["content"]
    assert "[pruned" in pruned, f"pruning marker missing: {pruned[:200]}"
    assert len(pruned) < len(big), "pruned output should be smaller than input"


def test_prune_trims_large_text_block_inside_list_content():
    big = "Y" * 5000
    msgs = [
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "t1", "content": [
                    {"type": "text", "text": big},
                    {"type": "text", "text": "small companion"},
                ]}
            ]
        }
    ]
    out = sa.Compactor._prune_tool_results_for_summary(msgs)
    inner = out[0]["content"][0]["content"]
    assert any("[pruned" in b.get("text", "") for b in inner if isinstance(b, dict))
    assert any(b.get("text", "") == "small companion" for b in inner if isinstance(b, dict))


def test_prune_does_not_mutate_input():
    big = "Z" * 5000
    msgs = [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": big}]}]
    sa.Compactor._prune_tool_results_for_summary(msgs)
    # original must be unchanged
    assert msgs[0]["content"][0]["content"] == big, "input must not be mutated"


# ============================================================
# Item 5 — Compactor._summary_client (auxiliary model)
# ============================================================

def test_summary_client_returns_main_when_no_aux_configured():
    assert sa.CONFIG.compaction_model == ""

    class _Fake:
        model_id = "main-model"
        region = "ap-southeast-2"
        mock_mode = True

    main = _Fake()
    assert sa.Compactor._summary_client(main) is main


def test_summary_client_returns_main_when_aux_equals_main():
    """When aux model is the same as main, no separate client needed."""
    old = sa.CONFIG.compaction_model
    try:
        sa.CONFIG.compaction_model = "main-model"

        class _Fake:
            model_id = "main-model"
            region = "ap-southeast-2"
            mock_mode = True

        main = _Fake()
        assert sa.Compactor._summary_client(main) is main
    finally:
        sa.CONFIG.compaction_model = old


def test_summary_client_builds_aux_when_configured():
    """When aux model differs from main, build (and cache) a Bedrock client for it."""
    old = sa.CONFIG.compaction_model
    try:
        sa.CONFIG.compaction_model = "anthropic.claude-haiku-4-5-test"

        class _FakeMain:
            model_id = "anthropic.claude-sonnet-4-5-main"
            region = "ap-southeast-2"
            mock_mode = True

        # Reset aux cache for clean test
        if hasattr(sa.Compactor, "_aux_client_cache"):
            sa.Compactor._aux_client_cache.clear()

        main = _FakeMain()
        aux = sa.Compactor._summary_client(main)
        assert aux is not main, "aux client should be a different instance"
        assert aux.model_id == "anthropic.claude-haiku-4-5-test"
        # Second call should hit the cache (same instance)
        aux2 = sa.Compactor._summary_client(main)
        assert aux2 is aux, "aux client should be cached, not rebuilt"
    finally:
        sa.CONFIG.compaction_model = old


# ============================================================
# Item 6 — Structured summary template
# ============================================================

def test_summary_template_has_resolved_questions_section():
    prompt = sa.Compactor.create_summary_prompt([])
    assert "Resolved Questions" in prompt, "structured Resolved Questions section missing"


def test_summary_template_has_pending_questions_section():
    prompt = sa.Compactor.create_summary_prompt([])
    assert "Pending Questions" in prompt, "structured Pending Questions section missing"


def test_summary_template_keeps_original_9_sections():
    prompt = sa.Compactor.create_summary_prompt([])
    for section_name in [
        "Primary Request and Intent",
        "Files and Code Sections",
        "Errors and Fixes",
        "User Messages",
        "Pending Tasks",
        "Current Work",
        "Next Step",
    ]:
        assert section_name in prompt, f"original section '{section_name}' should remain"


# ============================================================
# Cross-cutting — Agent constructor accepts iteration_budget
# ============================================================

def test_agent_constructor_accepts_iteration_budget():
    """Agent.__init__ must accept iteration_budget kwarg without raising."""

    class _StubClient:
        model_id = "stub"
        region = "ap-southeast-2"
        mock_mode = True

    a = sa.Agent(_StubClient(), iteration_budget=sa.IterationBudget(5))
    assert a.iteration_budget.total() == 5


def test_agent_creates_default_budget_when_none_passed():
    class _StubClient:
        model_id = "stub"
        region = "ap-southeast-2"
        mock_mode = True

    a = sa.Agent(_StubClient())
    assert a.iteration_budget is not None
    assert a.iteration_budget.total() == sa.CONFIG.max_iteration_budget


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("V4.9.4 hermes-pattern enhancements")
    print("=" * 60)

    print("\n[1] IterationBudget")
    _run("basic consume", test_iteration_budget_basic_consume)
    _run("exhaust returns False", test_iteration_budget_exhaust_returns_false)
    _run("default ceiling", test_iteration_budget_default_ceiling)
    _run("zero/negative clamped to 1", test_iteration_budget_zero_or_negative_clamped)
    _run("threadsafe no overshoot", test_iteration_budget_threadsafe_no_overshoot)

    print("\n[2] ErrorClassifier")
    _run("throttle", test_classifier_throttle)
    _run("validation-cache", test_classifier_validation_cache)
    _run("validation-other", test_classifier_validation_other)
    _run("context-overflow", test_classifier_context_overflow)
    _run("model-not-ready", test_classifier_model_not_ready)
    _run("model-timeout", test_classifier_model_timeout)
    _run("access-denied", test_classifier_access_denied)
    _run("service-unavailable", test_classifier_service_unavailable)
    _run("transient-network", test_classifier_transient_network)
    _run("unknown default", test_classifier_unknown_default)

    print("\n[3] RetryPolicy")
    _run("should retry on jitter recovery", test_retry_policy_should_retry_on_jitter_recovery)
    _run("no retry on abort", test_retry_policy_no_retry_on_abort)
    _run("no retry past max", test_retry_policy_no_retry_past_max)
    _run("backoff in valid range", test_retry_policy_backoff_growing_with_jitter)
    _run("negative attempt handled", test_retry_policy_negative_attempt_handled)

    print("\n[4] Pre-compact tool-result pruning")
    _run("small tool_result unchanged", test_prune_passes_small_tool_results_unchanged)
    _run("large string tool_result trimmed", test_prune_trims_large_string_tool_result)
    _run("large text block in list trimmed", test_prune_trims_large_text_block_inside_list_content)
    _run("input not mutated", test_prune_does_not_mutate_input)

    print("\n[5] Auxiliary-model compaction")
    _run("returns main when no aux configured", test_summary_client_returns_main_when_no_aux_configured)
    _run("returns main when aux == main", test_summary_client_returns_main_when_aux_equals_main)
    _run("builds + caches aux client when configured", test_summary_client_builds_aux_when_configured)

    print("\n[6] Structured summary template")
    _run("Resolved Questions section present", test_summary_template_has_resolved_questions_section)
    _run("Pending Questions section present", test_summary_template_has_pending_questions_section)
    _run("original 9 sections preserved", test_summary_template_keeps_original_9_sections)

    print("\n[Cross-cutting] Agent constructor")
    _run("accepts iteration_budget kwarg", test_agent_constructor_accepts_iteration_budget)
    _run("creates default budget when none passed", test_agent_creates_default_budget_when_none_passed)

    print()
    print("=" * 60)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"Result: {passed}/{total} passed")
    if passed != total:
        print()
        print("Failures:")
        for name, ok, msg in RESULTS:
            if not ok:
                print(f"  - {name}: {msg}")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
