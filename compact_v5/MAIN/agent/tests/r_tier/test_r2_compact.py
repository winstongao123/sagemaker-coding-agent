"""R-tier R2 — large preamble crosses Compactor threshold, follow-up
turn succeeds against the COMPACTED buffer.

Per PS_V5_TEST_PLAYBOOK / PS_V5_TEST_SET §Tier 1 R2:
  Validates Block A (Compactor + auto-compact + cache invariants) on
  real Bedrock end-to-end:
    - Turn 1: large preamble + simple question → assistant answer.
      Crosses Compactor.should_compact threshold (80% of
      context_max_tokens).
    - Auto-compact fires after the response — summarises history into
      one [CONVERSATION SUMMARY] system block, freeing tokens.
    - Turn 2: follow-up question. Bedrock must accept the post-compact
      message buffer (no 400 from cut-mid-pair) and answer correctly
      using only the compact summary.

Codex R2 PHASE A iter-1 fixes applied (REJECT → re-pre-flight):
  1. Default CONFIG.context_max_tokens=200_000 means real trigger is
     ~160K. We monkey-patch CONFIG.context_max_tokens=100_000 for this
     test so the existing 78K preamble crosses the 80% gate (80K).
     Cheaper than pushing to 165K real tokens AND tests same code path.
  2. Tightened final answer regex (single-token "5" or "five" reply
     expected from max_tokens=64; pattern in code below).
  3. Compaction-occurred assertion: TOKENS.api_calls accounts for
     initial turn + compaction summary call + follow-up turn ≥ 3 if
     compact fired; OR captured "[auto-compact]" line in stdout.
  4. Follow-up turn against the compacted buffer (asks recall question
     answerable from system summary).
  5. AUTO_COMPACT.reset() + TOKENS.reset() in finally for hermetic test.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R2_COST_CAP_USD = 0.50

# 2700 lines of lorem ≈ 60K words ≈ 78K tokens. With CONFIG.context_max_tokens
# = 100_000 (test override), this crosses the 80%-of-100K = 80K threshold.
_LOREM_LINE = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
    "eiusmod tempor incididunt ut labore et dolore magna aliqua. "
)
_LOREM_LINES = 2700

_R2_PROMPT_T1 = """You are reviewing a long conversation history. Below is a recap of
prior context — most of it is filler. After the recap, please answer
ONE SHORT question.

=== RECAP (do not summarize back; just keep in mind) ===
{recap}
=== END RECAP ===

QUESTION: What is 2 + 3? Answer with a single number, no explanation.
"""

# Follow-up — forces a 2nd Bedrock call against the post-compact buffer.
_R2_PROMPT_T2 = (
    "What was the previous question I asked? Reply with the question only "
    "(one short sentence)."
)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R2 is real-AWS gated.",
)
def test_r2_compaction_under_load(tmp_path, monkeypatch):
    """R-tier R2 — large preamble + follow-up succeed across compaction.

    PASS criteria:
      - Turn 1 produces a tight "5"/"Five" answer.
      - Turn 2 is answered against the compacted buffer (recalls the
        previous question or a paraphrase).
      - Auto-compact fired (TOKENS.api_calls >= 2 — model+compact-summary
        on turn 1 alone — OR "[auto-compact]" appears in captured stdout).
      - cost ≤ $0.50.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from core.compactor import AUTO_COMPACT
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_ctx_max = getattr(CONFIG, "context_max_tokens", None)
    cwd_before = os.getcwd()

    # Codex iter-1 fix #5: clean state in finally + at start.
    AUTO_COMPACT.reset() if hasattr(AUTO_COMPACT, "reset") else None

    captured_stdout: list = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        # Also forward to print so pytest -s shows it.
        try:
            print(text)
        except Exception:
            pass

    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.session_cost_limit = _R2_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 64
        CONFIG.require_tool_approval = False
        # Codex iter-1 fix #1: lower threshold so 78K crosses the 80% gate.
        CONFIG.context_max_tokens = 100_000
        sec_mgr.rebuild_singleton_for_tests()
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R2_COST_CAP_USD
            )

        agent = Agent(
            client=client,
            max_turns=4,
            on_stop_check=_hard_cost_halt,
        )

        recap = (_LOREM_LINE + "\n") * _LOREM_LINES
        prompt_t1 = _R2_PROMPT_T1.format(recap=recap)
        approx_tokens_in = len(prompt_t1) // 4

        t0 = time.time()
        # Turn 1 — large preamble.
        result_t1 = agent.run(prompt_t1, tools=[], output_fn=_stdout_capture)
        wall_t1 = time.time() - t0
        tokens_in_t1 = TOKENS.session_input
        api_calls_after_t1 = TOKENS.api_calls
        # Turn 2 — follow-up against (likely-compacted) buffer.
        t1 = time.time()
        result_t2 = agent.run(_R2_PROMPT_T2, tools=[], output_fn=_stdout_capture)
        wall_t2 = time.time() - t1
        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        # Detect compaction — STRONG signals only (Codex iter-2 fix):
        # MUST have explicit "[auto-compact]" log line OR find a
        # [CONVERSATION SUMMARY] / "summary of prior" / "compact" marker
        # in agent.messages. api_calls heuristic is too weak alone — a
        # failed summary call still increments api_calls.
        full_stdout = "\n".join(captured_stdout)
        compact_log_seen = "[auto-compact]" in full_stdout
        # Inspect messages buffer for compaction artifact.
        summary_marker_seen = False
        for msg in agent.messages:
            content = msg.get("content")
            text_blob = ""
            if isinstance(content, str):
                text_blob = content
            elif isinstance(content, list):
                for blk in content:
                    if isinstance(blk, dict):
                        text_blob += " " + str(blk.get("text", ""))
            if any(s in text_blob for s in (
                "[CONVERSATION SUMMARY]",
                "[Conversation Summary]",
                "## Summary of prior conversation",
                "summary of the prior",
            )):
                summary_marker_seen = True
                break
        # T2 input MUST drop materially vs T1 input — proof that
        # turn 2 sent a smaller (compacted) buffer to Bedrock.
        t2_input_estimate = tokens_in - tokens_in_t1
        t2_dropped_materially = t2_input_estimate < (tokens_in_t1 * 0.5)
        compact_proven = compact_log_seen or summary_marker_seen
        compact_likely = compact_proven and t2_dropped_materially

        metrics = {
            "test": "R2",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "tokens_in_after_turn1": int(tokens_in_t1),
            "tokens_in_t2_estimate": int(t2_input_estimate),
            "t2_dropped_materially_vs_t1": bool(t2_dropped_materially),
            "wallclock_s": round(wall_t1 + wall_t2, 2),
            "wallclock_t1_s": round(wall_t1, 2),
            "wallclock_t2_s": round(wall_t2, 2),
            "approx_prompt_tokens": approx_tokens_in,
            "preamble_lines": _LOREM_LINES,
            "context_max_tokens_test_override": CONFIG.context_max_tokens,
            "api_calls": int(api_calls),
            "api_calls_after_t1": int(api_calls_after_t1),
            "compact_log_seen": compact_log_seen,
            "summary_marker_seen": summary_marker_seen,
            "compact_proven": compact_proven,
            "compact_likely": compact_likely,
            "tool_calls_t1": int(getattr(result_t1, "turns_used", 0)),
            "tool_calls_t2": int(getattr(result_t2, "turns_used", 0)),
            "cost_usd": round(cost_used, 4),
            "stop_reason_t1": result_t1.stop_reason,
            "stop_reason_t2": result_t2.stop_reason,
            "final_text_t1": (result_t1.text or "").strip()[:200],
            "final_text_t2": (result_t2.text or "").strip()[:200],
        }
        (tmp_path / "_r2_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R2 METRICS] {json.dumps(metrics)}")

        # Codex iter-1 fix #2: tight regex on turn-1 answer.
        t1_text = (result_t1.text or "").strip()
        # Accept "5", "5.", "Five", "Five.", "= 5", with optional
        # leading "=" or whitespace.
        assert re.match(r"^\s*=?\s*(5|five)\b\.?\s*$", t1_text, re.IGNORECASE), (
            f"R2 turn 1 expected exact answer 5/five; got: {t1_text!r}. "
            f"metrics={metrics}"
        )
        assert result_t1.stop_reason != "max_turns", (
            f"R2 turn 1 hit max_turns. metrics={metrics}"
        )
        # Turn 2 — recall via compacted buffer.
        # Codex iter-2 fix: removed "5" from accepted recall — that
        # could pass from a weak summary that lost the actual question.
        # Must mention the original prompt's specific arithmetic.
        t2_text = (result_t2.text or "").lower()
        assert t2_text, f"R2 turn 2 empty response. metrics={metrics}"
        assert ("2 + 3" in t2_text or "2+3" in t2_text or "what is 2" in t2_text), (
            f"R2 turn 2 didn't recall the SPECIFIC prior question (2+3). "
            f"got: {result_t2.text!r}. metrics={metrics}"
        )
        # Codex iter-2 fix #3: STRONG compaction proof — explicit log
        # OR summary marker in messages, AND turn-2 input dropped
        # materially vs turn-1 input.
        assert compact_proven, (
            f"R2 expected compaction PROVEN: either '[auto-compact]' in "
            f"stdout or [CONVERSATION SUMMARY] marker in agent.messages. "
            f"current: log_seen={compact_log_seen}, "
            f"summary_marker={summary_marker_seen}. metrics={metrics}"
        )
        assert t2_dropped_materially, (
            f"R2 expected turn-2 input ≪ turn-1 input (proves buffer "
            f"compacted). t1_in={tokens_in_t1}, t2_in_estimate="
            f"{t2_input_estimate}. metrics={metrics}"
        )
        # Cost.
        assert cost_used <= _R2_COST_CAP_USD, (
            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
            f"metrics={metrics}"
        )
        # Sanity: large input was actually sent.
        assert tokens_in_t1 > 50_000, (
            f"R2 expected turn-1 input_tokens >50K; got {tokens_in_t1}. "
            f"metrics={metrics}"
        )
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec
        if saved_cost_limit is not None:
            CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
        if saved_ctx_max is not None:
            CONFIG.context_max_tokens = saved_ctx_max
        # Codex iter-1 fix #5.
        if hasattr(AUTO_COMPACT, "reset"):
            AUTO_COMPACT.reset()
        TOKENS.reset()
