"""V4.10.0 #41a — Reactive Compact on CONTEXT_OVERFLOW.

Tests:
1. CONTEXT_OVERFLOW once then success → reactive triggered, retry succeeds.
2. CONTEXT_OVERFLOW twice → reactive triggered once, second failure surfaces.
3. Non-CONTEXT_OVERFLOW error (e.g. AccessDenied) → reactive NOT triggered.
4. The reactive flag is per-run() call, reset on each new user message.
5. CONTEXT_OVERFLOW classification matches all 3 documented Bedrock messages.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


class _FakeClient:
    """Minimal stand-in for BedrockClient. Drives chat() return values from a queue."""

    def __init__(self, responses_or_exceptions):
        self._queue = list(responses_or_exceptions)
        self.calls = 0
        self.model_id = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
        self.prompt_cache_supported = True
        # Attributes touched by Agent.run() post-response paths (cache diagnostics, etc.)
        self._cache_threshold_warned = False
        self._cache_misses = 0
        self.region = "ap-southeast-2"
        self.mock_mode = True

    def chat(self, *args, **kwargs):
        self.calls += 1
        if not self._queue:
            raise RuntimeError("Test misconfigured: more chat() calls than queued items")
        item = self._queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _make_response(text: str = "ok") -> sa.Response:
    return sa.Response(text=text, tool_calls=[], stop_reason="end_turn", usage={"input_tokens": 100, "output_tokens": 10})


def _make_agent(client) -> sa.Agent:
    """Build a minimal Agent for the run() loop tests."""
    captured: list = []
    a = sa.Agent(
        client=client,
        session_id="test_v410_reactive",
        on_approval=lambda *_: True,
        on_ask_user=None,
        on_tokens=None,
        on_thinking=None,
        on_stop_check=None,
    )
    return a


def _capture_output():
    captured = []
    def out(msg):
        captured.append(msg)
    return out, captured


def test_classification_recognises_context_overflow():
    """Confirm ErrorClassifier still picks up the three documented prompt-too-long messages
    so the reactive path is reachable."""
    msgs = [
        "ValidationException: prompt is too long: 247811 tokens, model limit is 199876",
        "Input validation error: too many tokens for the model",
        "ValidationException: input is too long for requested model",
    ]
    for m in msgs:
        cat, rec, _ = sa.ErrorClassifier.classify(Exception(m))
        assert cat == sa.BedrockErrorCategory.CONTEXT_OVERFLOW, (
            f"Expected CONTEXT_OVERFLOW for {m!r}, got {cat}"
        )


def test_overflow_once_then_success_triggers_reactive_retry():
    """Mock client raises CONTEXT_OVERFLOW once then returns a normal response.
    Reactive compact must run, retry must succeed, and run() must return text."""
    overflow = Exception("prompt is too long: 247811 tokens, model limit is 199876")
    client = _FakeClient([overflow, _make_response("hello after compact")])
    agent = _make_agent(client)
    out_fn, captured = _capture_output()

    result = agent.run("test", output_fn=out_fn, count_towards_limits=False)

    # The retry should have happened (2 chat() calls)
    assert client.calls == 2, f"Expected 2 chat calls, got {client.calls}"
    # Result must be the normal response text, NOT an [AGENT ERROR]
    assert "hello after compact" in result, f"Reactive retry didn't recover: {result!r}"
    # The reactive marker should appear in captured output
    captured_text = "\n".join(str(c) for c in captured)
    assert "Reactive compact" in captured_text, f"Reactive marker missing from output:\n{captured_text}"


def test_overflow_twice_surfaces_normal_error():
    """If even after compact the second call fails the same way, the user sees the error."""
    overflow1 = Exception("prompt is too long: 247811 tokens, model limit is 199876")
    overflow2 = Exception("prompt is too long: 232118 tokens, model limit is 199876")
    client = _FakeClient([overflow1, overflow2])
    agent = _make_agent(client)
    out_fn, captured = _capture_output()

    result = agent.run("test", output_fn=out_fn, count_towards_limits=False)

    # 2 attempts, second one fails → retry-failure error returned
    assert client.calls == 2, f"Expected exactly 2 chat calls, got {client.calls}"
    assert "Retry after reactive compact also failed" in result, (
        f"Expected post-retry error, got: {result!r}"
    )


def test_non_context_overflow_error_does_not_trigger_reactive():
    """An AccessDenied error should propagate to the user without any reactive compact."""
    access = Exception("AccessDeniedException: not authorized to invoke model")
    client = _FakeClient([access])
    agent = _make_agent(client)
    out_fn, captured = _capture_output()

    result = agent.run("test", output_fn=out_fn, count_towards_limits=False)

    # 1 attempt, no retry — error surfaced normally
    assert client.calls == 1, f"Reactive must NOT retry non-overflow errors; got {client.calls} calls"
    assert "[AGENT ERROR]" in result, f"Expected normal error path: {result!r}"
    captured_text = "\n".join(str(c) for c in captured)
    assert "Reactive compact" not in captured_text, (
        f"Reactive marker leaked into non-overflow path:\n{captured_text}"
    )


def test_reactive_flag_resets_per_run_call():
    """The reactive-done flag must reset between separate run() calls so the
    next user message can also trigger reactive compact if needed."""
    overflow = Exception("prompt is too long: 247811 tokens, model limit is 199876")
    client = _FakeClient([
        overflow, _make_response("first ok"),       # first run() call: 2 chats
        overflow, _make_response("second ok"),      # second run() call: 2 chats
    ])
    agent = _make_agent(client)
    out_fn, _ = _capture_output()

    r1 = agent.run("first", output_fn=out_fn, count_towards_limits=False)
    r2 = agent.run("second", output_fn=out_fn, count_towards_limits=False)
    assert "first ok" in r1, r1
    assert "second ok" in r2, r2
    assert client.calls == 4, f"Expected 4 chat calls (2 per run), got {client.calls}"


if __name__ == "__main__":
    tests = [
        ("classification_recognises_context_overflow", test_classification_recognises_context_overflow),
        ("overflow_once_then_success_triggers_reactive_retry", test_overflow_once_then_success_triggers_reactive_retry),
        ("overflow_twice_surfaces_normal_error", test_overflow_twice_surfaces_normal_error),
        ("non_context_overflow_error_does_not_trigger_reactive", test_non_context_overflow_error_does_not_trigger_reactive),
        ("reactive_flag_resets_per_run_call", test_reactive_flag_resets_per_run_call),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
