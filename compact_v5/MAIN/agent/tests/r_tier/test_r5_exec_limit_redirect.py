"""R-tier R5 — bash/python_exec session limit + OTHER-TOOLS-STILL-WORK
recovery on real Bedrock.

Per PS_V5_TEST_PLAYBOOK / PS_V5_TEST_SET §Tier 1 R5:
  Validates PS#7 structural fix end-to-end. v4 had the agent give up
  when the bash/python_exec session cap was hit; v5 redirects the
  model to non-counted tools (read_file, grep, glob, edit_file,
  write_file, notebook_edit, task, ask_user, view_image, web_fetch)
  via an explicit "OTHER TOOLS STILL WORK" message in the blocked
  tool_result.

R-tier scope: instead of looping 200 real python_exec calls (per the
playbook's full-budget spec at $0.50), this test sets
`CONFIG.max_exec_calls_per_session = 2` so the limit triggers on the
3rd attempt — same code path, ~10x cheaper. The semantic claim
(blocked message + agent recovery via non-counted tool) is identical.

Validation pillars:
  - audit_log records ≥ cap successful python_exec dispatches
    (the BLOCKED path at query_engine.py:805-819 returns early WITHOUT
    audit.log, so it is detected via the in-memory agent.messages
    buffer instead, where the blocked tool_result is appended).
  - The literal "OTHER TOOLS STILL WORK" appears in some tool_result
    block within agent.messages — direct proof PS#7's failure-as-
    instruction message reached the model.
  - The agent dispatches read_file for data.csv AFTER the blocked
    tool_result message (transcript-order check — proves the model
    SWITCHED to a non-counted tool BECAUSE OF the block, not by
    coincidence reading the CSV earlier).
  - The agent's final assistant text contains the marker "carol"
    (the manager's name in data.csv) — only achievable if read_file
    successfully retrieved the content + the model reasoned over it.
  - Parent stop_reason != max_turns.
  - Cost <= $0.50.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R5_COST_CAP_USD = 0.50

# Lowered cap for cheap test execution. The PS#7 code path is the
# same regardless of cap value (query_engine.py:800-819).
_TEST_EXEC_CAP = 2

# Distinctive content phrase that ONLY appears in the data.csv body —
# proof the agent recovered to read_file after exec was blocked.
_CSV_CONTENT = (
    "name,role,salary\n"
    "alice,engineer,120000\n"
    "bob,designer,95000\n"
    "carol,manager,140000\n"
)
_RECOVERY_MARKER = "carol"  # only appears in CSV; not in prompt or schemas

_R5_PROMPT = (
    "You are working in the current directory. There is a file `data.csv` "
    "with employee records.\n\n"
    "TASK (do these in order):\n"
    "1. Use `python_exec` to print the result of `1 + 1`.\n"
    "2. Use `python_exec` to print the result of `2 + 2`.\n"
    "3. Use `python_exec` to print the result of `3 + 3`.\n"
    "4. After the three computations, read `data.csv` and tell me the "
    "name of the manager (the row whose role is 'manager').\n\n"
    "If a tool returns a 'blocked' message, do NOT keep retrying that "
    "tool — switch to a different tool to make progress. Proceed "
    "directly; do NOT ask for confirmation."
)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R5 is real-AWS gated.",
)
def test_r5_exec_limit_recovery(tmp_path):
    """R-tier R5 — exec limit blocks + agent recovers via non-counted tool.

    PASS criteria:
      - audit_log has >= _TEST_EXEC_CAP successful python_exec dispatches
        (the BLOCKED path returns early without audit; query_engine.py:805-819).
      - The literal "OTHER TOOLS STILL WORK" appears in some tool_result
        block within agent.messages — direct proof PS#7's fail-as-
        instruction message reached the model.
      - A read_file(data.csv) tool_use appears in agent.messages at a
        LATER index than the blocked tool_result (transcript-order
        recovery proof).
      - Final assistant text contains "carol" (the manager's name —
        only present if read_file actually retrieved data.csv content;
        this string is NOT in the prompt or any tool schemas).
      - parent stop_reason != max_turns.
      - cost <= $0.50.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from runtime.audit import AUDIT
    from core.budget import IterationBudget
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    saved_exec_cap = getattr(CONFIG, "max_exec_calls_per_session", None)
    cwd_before = os.getcwd()

    captured_stdout: list = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        try:
            print(text)
        except Exception:
            pass

    try:
        # ------------------------------------------------------------
        # Workspace fixture — data.csv with distinctive recovery marker
        # ------------------------------------------------------------
        (tmp_path / "data.csv").write_text(_CSV_CONTENT, encoding="utf-8")

        audit_dir = tmp_path / "audit_logs"
        audit_dir.mkdir(exist_ok=True)

        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R5_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 2048
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        # Lowered cap for cheap real-AWS validation. Same code path as
        # the production cap=200; only the trigger threshold differs.
        CONFIG.max_exec_calls_per_session = _TEST_EXEC_CAP
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R5_COST_CAP_USD
            )

        # Tight IterationBudget — 3 successful exec attempts + 1 blocked
        # + 1 read_file recovery + parent synthesis ≤ 12 turns expected.
        shared_budget = IterationBudget(max_iterations=18)
        agent = Agent(
            client=client,
            max_turns=15,
            budget=shared_budget,
            on_stop_check=_hard_cost_halt,
        )
        parent_session_id = agent._engine.session_id

        t0 = time.time()
        result = agent.run(_R5_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        # ------------------------------------------------------------
        # Read audit_log
        # ------------------------------------------------------------
        audit_entries: list = []
        for f in audit_dir.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                audit_entries.append(e)

        python_exec_dispatches = [
            e for e in audit_entries
            if e.get("tool_name") == "python_exec" and e.get("action") == "tool_dispatch"
        ]
        read_file_dispatches = [
            e for e in audit_entries
            if e.get("tool_name") == "read_file" and e.get("action") == "tool_dispatch"
        ]
        # PS#7 detection. AUDIT.log is only called after a tool actually
        # executed (query_engine.py:988-996); the BLOCKED path at line
        # 805-819 returns early WITHOUT audit. So the blocked
        # tool_result is observable only in the in-memory
        # `agent.messages` buffer — appended by line 806 immediately
        # before `continue`.
        #
        # Codex iter-1 finding (medium): build a TRANSCRIPT-ORDER
        # check. We need:
        #   1. find the index of the FIRST message containing a
        #      tool_result with "OTHER TOOLS STILL WORK".
        #   2. assert read_file(data.csv) appears at a later index.
        full_stdout = "\n".join(captured_stdout)

        def _msg_contains_block_marker(msg) -> bool:
            content = msg.get("content")
            if isinstance(content, str):
                return "OTHER TOOLS STILL WORK" in content
            if isinstance(content, list):
                for blk in content:
                    if isinstance(blk, dict):
                        # tool_result blocks have content as str OR
                        # list of dicts with text field.
                        bc = blk.get("content")
                        if isinstance(bc, str) and "OTHER TOOLS STILL WORK" in bc:
                            return True
                        if isinstance(bc, list):
                            for sub in bc:
                                if isinstance(sub, dict) and "OTHER TOOLS STILL WORK" in str(sub.get("text", "")):
                                    return True
                        # plain text block (assistant-side never has the
                        # block marker, but defensively check):
                        if isinstance(blk.get("text"), str) and "OTHER TOOLS STILL WORK" in blk["text"]:
                            return True
            return False

        def _msg_has_read_file_for(msg, fname: str) -> bool:
            content = msg.get("content")
            if not isinstance(content, list):
                return False
            for blk in content:
                if isinstance(blk, dict) and blk.get("type") == "tool_use" and blk.get("name") == "read_file":
                    args = blk.get("input") or {}
                    fp = str(args.get("file_path") or args.get("path") or "")
                    if fname in fp:
                        return True
            return False

        block_marker_idx = next(
            (i for i, m in enumerate(agent.messages) if _msg_contains_block_marker(m)),
            -1,
        )
        blocked_marker_seen = block_marker_idx >= 0
        # read_file(data.csv) AFTER the block?
        read_csv_after_block = False
        if blocked_marker_seen:
            for m in agent.messages[block_marker_idx + 1 :]:
                if _msg_has_read_file_for(m, "data.csv"):
                    read_csv_after_block = True
                    break
        # Backwards-compatible audit count for diagnostics (any time):
        read_csv_dispatches = []
        for e in read_file_dispatches:
            params = e.get("parameters") or {}
            fp = str(params.get("file_path") or params.get("path") or "")
            if "data.csv" in fp:
                read_csv_dispatches.append(e)

        final_text = (result.text or "").lower()
        recovery_marker_in_text = _RECOVERY_MARKER.lower() in final_text

        metrics = {
            "test": "R5",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": int(getattr(result, "turns_used", 0)),
            "api_calls": int(api_calls),
            "cost_usd": round(cost_used, 4),
            "stop_reason": result.stop_reason,
            "exec_cap": _TEST_EXEC_CAP,
            "python_exec_dispatches": len(python_exec_dispatches),
            "read_file_dispatches": len(read_file_dispatches),
            "read_csv_dispatches": len(read_csv_dispatches),
            "blocked_marker_seen": blocked_marker_seen,
            "block_marker_idx": int(block_marker_idx),
            "read_csv_after_block": read_csv_after_block,
            "n_messages": len(agent.messages),
            "recovery_marker_in_text": recovery_marker_in_text,
            "final_text_head": final_text[:300],
        }
        (tmp_path / "_r5_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R5 METRICS] {json.dumps(metrics)}")

        # ------------------------------------------------------------
        # Assertions
        # ------------------------------------------------------------
        assert result.stop_reason != "max_turns", (
            f"R5 hit max_turns (15); incomplete. metrics={metrics}"
        )
        # AUDIT only logs SUCCESSFUL python_exec dispatches (per
        # query_engine.py:988-996, called after exec finished); the
        # BLOCKED path at line 805-819 returns early without audit.
        # Expect at least cap=2 successful python_exec dispatches in
        # the audit log; the blocked attempt is verified separately
        # via the agent.messages buffer below.
        assert len(python_exec_dispatches) >= _TEST_EXEC_CAP, (
            f"R5 expected >={_TEST_EXEC_CAP} successful python_exec dispatches "
            f"(cap was {_TEST_EXEC_CAP}); got {len(python_exec_dispatches)}. "
            f"metrics={metrics}"
        )
        # Block message must appear — proves PS#7's fail-as-instruction
        # message reached the model. Codex iter-1 fix: location-tracked
        # via `block_marker_idx` so the post-block recovery assertion
        # below has a valid pivot point.
        assert blocked_marker_seen, (
            f"R5 expected 'OTHER TOOLS STILL WORK' message after exec cap "
            f"({_TEST_EXEC_CAP}) was hit; not found in agent.messages. "
            f"n_messages={len(agent.messages)}. metrics={metrics}"
        )
        # Codex iter-1 fix (medium): TRANSCRIPT-ORDER recovery proof —
        # the read_file(data.csv) tool_use must appear at a later
        # message index than the blocked tool_result. This rules out
        # the "model happened to read data.csv early then later got
        # blocked" false-positive path.
        assert read_csv_after_block, (
            f"R5 expected a read_file(data.csv) tool_use AFTER the "
            f"blocked tool_result (block_marker_idx={block_marker_idx}, "
            f"n_messages={len(agent.messages)}). Recovery via non-counted "
            f"tool MUST follow the block, not precede it. "
            f"read_csv_dispatches_total={len(read_csv_dispatches)}. "
            f"metrics={metrics}"
        )
        # Final text must reflect actual CSV content — only achievable
        # if read_file successfully retrieved + agent reasoned over it.
        assert recovery_marker_in_text, (
            f"R5 expected final assistant text to mention "
            f"'{_RECOVERY_MARKER}' (the manager's name in data.csv). "
            f"final_text[:300]={final_text[:300]!r}. metrics={metrics}"
        )
        assert cost_used <= _R5_COST_CAP_USD, (
            f"R5 cost ${cost_used:.4f} exceeded cap ${_R5_COST_CAP_USD}. "
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
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
            AUDIT.__init__(audit_dir=saved_audit_dir)
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
        if saved_exec_cap is not None:
            CONFIG.max_exec_calls_per_session = saved_exec_cap
        TOKENS.reset()
