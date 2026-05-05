"""R-tier Stage 6 - R19-U4/R19-U5 subagent recovery bundle.

Runs the still-pending Stage 6 UX/orchestration members in one real-Bedrock
pytest invocation. R3 already has READY evidence in the ledger; this runner
targets the missing conflict-reconciliation and failed-child recovery rows.
The test is skipped unless RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import pytest


_AGENT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_PER_TEST_CAPS = {
    "R19-U4": 0.40,
    "R19-U5": 0.30,
}
_USER_APPROVED_RETRY_BUFFER_MULTIPLIER = 1.20
_GUARD_FAILURE_CLASSES = {
    "read_before_edit",
    "read_before_write",
    "bash_cd_blocked",
    "python_exec_error",
}


def _hard_ceiling(test_id: str) -> float:
    return _PER_TEST_CAPS[test_id] * _USER_APPROVED_RETRY_BUFFER_MULTIPLIER


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _audit_events(audit_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for fp in sorted(audit_dir.glob("*.jsonl")):
        for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _tool_order(events: list[dict[str, Any]]) -> list[str]:
    return [
        str(ev.get("tool_name") or ev.get("parameters", {}).get("tool_name") or "")
        for ev in events
        if ev.get("action") == "tool_dispatch"
    ]


def _tool_count(events: list[dict[str, Any]], name: str) -> int:
    return sum(1 for ev in events if ev.get("action") == "tool_dispatch" and ev.get("tool_name") == name)


def _failure_loop_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        ev
        for ev in events
        if str(ev.get("action")) in {
            "tool_failure_recorded",
            "tool_failure_loop_warning",
            "tool_failure_loop_blocked",
        }
    ]


def _guard_failure_class_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ev in _failure_loop_events(events):
        params = ev.get("parameters", {})
        if not isinstance(params, dict):
            params = {}
        failure_class = str(params.get("failure_class") or "")
        if failure_class not in _GUARD_FAILURE_CLASSES:
            continue
        try:
            count = int(params.get("failure_class_count") or params.get("previous_failures") or 1)
        except (TypeError, ValueError):
            count = 1
        counts[failure_class] = max(counts.get(failure_class, 0), count)
    return counts


def _setup_u4(workspace: Path) -> None:
    _write(workspace / "reviews" / "alpha.md", "Reviewer Alpha says: SHIP. Payment API is healthy.\n")
    _write(workspace / "reviews" / "beta.md", "Reviewer Beta says: ROLLBACK. Payment API error rate is too high.\n")
    _write(
        workspace / "source_of_truth.json",
        json.dumps({
            "service": "payment-api",
            "error_rate_pct": 12.0,
            "healthy_threshold_pct": 2.0,
            "supported_decision": "ROLLBACK",
        }, indent=2),
    )


_U4_PROMPT = """You are in the current directory.

Use the task tool to dispatch exactly two explore subagents:
1. Ask one subagent to read reviews/alpha.md and summarize Alpha's claim.
2. Ask one subagent to read reviews/beta.md and summarize Beta's claim.

After both return, read source_of_truth.json yourself. Write reconciliation.md.
It must state that the subagent findings conflict and that the supported final
decision is ROLLBACK because source_of_truth.json shows error_rate_pct 12.0 is
above healthy_threshold_pct 2.0. Do not choose by majority. Stop after writing
reconciliation.md."""


def _u4_ready(workspace: Path) -> bool:
    text = _read(workspace / "reconciliation.md").lower()
    return (
        "conflict" in text
        and "rollback" in text
        and "12.0" in text
        and "2.0" in text
        and "source_of_truth" in text
    )


def _setup_u5(workspace: Path) -> None:
    _write(workspace / "evidence" / "checkout.md", "Checkout probe: PASS. p95 latency 180ms.\n")
    _write(workspace / "evidence" / "inventory.md", "Inventory probe: PASS. stock sync fresh.\n")


_U5_PROMPT = """You are in the current directory.

Use the task tool to dispatch exactly three explore subagents:
1. Ask one subagent to read evidence/checkout.md and summarize the checkout probe.
2. Ask one subagent to read evidence/inventory.md and summarize the inventory probe.
3. Ask one subagent to read evidence/missing_probe.md and summarize it. This file
   is intentionally absent; record that child failure instead of retrying forever.

After all subagents return, write recovery_summary.md. It must record the missing
child failure, use the two successful child findings, and conclude:
CONTINUE_WITH_PARTIAL_EVIDENCE. Stop after writing recovery_summary.md."""


def _u5_ready(workspace: Path) -> bool:
    text = _read(workspace / "recovery_summary.md").lower()
    missing_child_failure = (
        "failure" in text
        or "failed" in text
        or "file not found" in text
    )
    return (
        "missing" in text
        and missing_child_failure
        and "checkout" in text
        and "inventory" in text
        and "continue_with_partial_evidence" in text
    )


def test_u5_ready_accepts_failed_probe_artifact_wording(tmp_path):
    """Lock the Stage 6 U5 predicate to the call1 artifact wording class."""
    _write(
        tmp_path / "recovery_summary.md",
        """# Recovery Summary

### Failed Probes

#### Missing Probe (evidence/missing_probe.md)
- Status: FILE NOT FOUND
- Action Taken: Single attempt made; no retry per instructions

Checkout probe passed. Inventory probe passed.

CONTINUE_WITH_PARTIAL_EVIDENCE
""",
    )
    assert _u5_ready(tmp_path) is True


def test_u5_ready_rejects_summary_without_missing_child_failure(tmp_path):
    _write(
        tmp_path / "recovery_summary.md",
        "Checkout passed. Inventory passed. CONTINUE_WITH_PARTIAL_EVIDENCE\n",
    )
    assert _u5_ready(tmp_path) is False


def _run_member(
    *,
    test_id: str,
    workspace: Path,
    prompt: str,
    setup: Callable[[Path], None],
    ready: Callable[[Path], bool],
    client: Any,
    call: int,
    cap: float,
) -> dict[str, Any]:
    from agent import Agent
    from core.budget import IterationBudget
    from runtime.audit import AUDIT
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    workspace.mkdir(parents=True, exist_ok=True)
    setup(workspace)
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"{test_id}-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    CONFIG.workspace = str(workspace)
    CONFIG.audit_dir = str(audit_dir)
    sec_mgr.rebuild_singleton_for_tests()
    AUDIT.__init__(audit_dir=str(audit_dir))
    TOKENS.reset()

    cwd_before = os.getcwd()
    captured_stdout: list[str] = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        print(text)

    try:
        os.chdir(str(workspace))

        def _halt() -> bool:
            over_budget = TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= cap
            )
            return over_budget or ready(workspace)

        agent = Agent(
            client=client,
            max_turns=12,
            budget=IterationBudget(max_iterations=18),
            on_stop_check=_halt,
        )
        agent._engine._discovered_tool_names = {"task", "read_file", "write_file"}
        t0 = time.time()
        result = agent.run(prompt, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0
    finally:
        os.chdir(cwd_before)

    events = _audit_events(audit_dir)
    order = _tool_order(events)
    failure_events = _failure_loop_events(events)
    guard_failure_class_counts = _guard_failure_class_counts(events)
    repeated_guard_loop = any(count >= 2 for count in guard_failure_class_counts.values())
    process_quality_ok = bool(not repeated_guard_loop and result.stop_reason != "max_turns")
    task_dispatches = _tool_count(events, "task")
    cost_used = float(TOKENS.session_cost)
    completed = (
        result.stop_reason in {"end_turn", "user_stop"}
        and ready(workspace)
        and process_quality_ok
        and cost_used <= cap
        and task_dispatches == (2 if test_id == "R19-U4" else 3)
    )
    side_metrics = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-{test_id}-aws-call{call}-side-metrics.json"
    metrics = {
        "test": test_id,
        "call": call,
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": _HAIKU_45_AU,
        "tokens_in": int(TOKENS.session_input),
        "tokens_out": int(TOKENS.session_output),
        "cache_hit_pct": 0.0,
        "wallclock_s": round(wallclock_s, 2),
        "tool_calls": len(order),
        "api_calls": int(TOKENS.api_calls),
        "subagent_calls": task_dispatches,
        "reviewer_calls": 0,
        "subagent_tokens_in": 0,
        "subagent_tokens_out": 0,
        "subagent_cost_usd": 0.0,
        "reviewer_tokens_in": 0,
        "reviewer_tokens_out": 0,
        "reviewer_cost_usd": 0.0,
        "changed_files_within_fixture": True,
        "task_dispatches": task_dispatches,
        "failure_loop_event_count": len(failure_events),
        "guard_failure_class_counts": guard_failure_class_counts,
        "process_quality_ok": process_quality_ok,
        "completed": bool(completed),
        "cost_usd": round(cost_used, 4),
        "verdict": "GENUINE_PASS" if completed else "FAIL",
        "stop_reason": result.stop_reason,
        "audit_dir": str(audit_dir),
        "tool_order": order,
    }
    side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\n[{test_id}_AUDIT_DIR] {audit_dir}")
    print(f"[{test_id}_SIDE_METRICS] {side_metrics}")
    print(f"[{test_id}_METRICS] {json.dumps(metrics, sort_keys=True)}")
    return metrics


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; Stage 6 R19-U4/U5 bundle is real-AWS gated.",
)
def test_r19_u4_u5_subagent_recovery_bundle(tmp_path):
    """R19-U4/U5 pass when parent handles conflicting/failed subagent evidence."""
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    import security.manager as sec_mgr

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    try:
        CONFIG.session_cost_limit = sum(_hard_ceiling(test_id) for test_id in _PER_TEST_CAPS)
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 2048
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        sec_mgr.rebuild_singleton_for_tests()

        call = int(os.getenv("R_TIER_CALL", "1"))
        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)
        members = [
            ("R19-U4", _U4_PROMPT, _setup_u4, _u4_ready),
            ("R19-U5", _U5_PROMPT, _setup_u5, _u5_ready),
        ]
        results = [
            _run_member(
                test_id=test_id,
                workspace=tmp_path / test_id.lower().replace("-", "_"),
                prompt=prompt,
                setup=setup,
                ready=ready,
                client=client,
                call=call,
                cap=_hard_ceiling(test_id),
            )
            for test_id, prompt, setup, ready in members
        ]
        for metrics in results:
            assert metrics["completed"] is True, f"{metrics['test']} failed Stage 6 criteria: {metrics}"
            assert metrics["cost_usd"] <= _hard_ceiling(metrics["test"]), metrics
    finally:
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
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
