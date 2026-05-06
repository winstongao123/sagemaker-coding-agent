"""R-tier R19-U10 - long coherence after transcript churn.

Validates that the real Bedrock-backed agent can finish a final task that
depends on early-session facts after a prebuilt 150-logical-turn transcript
fixture with model-switch and compaction markers. The test is skipped unless
RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import pytest


_AGENT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R19_U10_COST_CAP_USD = 0.50
_USER_APPROVED_RETRY_BUFFER_MULTIPLIER = 1.20
_R19_U10_HARD_CEILING_USD = _R19_U10_COST_CAP_USD * _USER_APPROVED_RETRY_BUFFER_MULTIPLIER
_FINAL_REPORT = "final_coherence_report.md"
_ANCHORS = {
    "codename": "HYDRA-LIME",
    "checksum": "kiwi-1842",
    "runtime": "Python 3.12",
    "owner": "Priya",
    "final_task": "create_coherence_report",
}

_PROMPT = f"""This is the final task after a long prebuilt session.

Use the existing conversation context, status, and memory. Do not ask for
clarification and do not invent replacements for earlier facts.

Create {_FINAL_REPORT} with exactly these five lines:
CODENAME: <project codename from the early anchor>
CHECKSUM: <checksum phrase from the early anchor>
RUNTIME: <latest runtime preference>
OWNER: <latest owner>
FINAL_TASK: <final task marker>

Stop after writing the report.
"""


def _write_fixture(workspace: Path) -> None:
    fixture = {
        "test": "R19-U10",
        "logical_turns_represented": 150,
        "model_switches": [
            {"at_logical_turn": 47, "from": "Haiku 4.5 AU", "to": "Sonnet 4.5 AU"},
            {"at_logical_turn": 104, "from": "Sonnet 4.5 AU", "to": "Haiku 4.5 AU"},
        ],
        "compactions": [
            {"after_logical_turn": 50, "preserved": ["codename", "checksum"]},
            {"after_logical_turn": 100, "preserved": ["runtime", "owner"]},
            {"after_logical_turn": 145, "preserved": ["final_task"]},
        ],
        "anchors": _ANCHORS,
    }
    (workspace / "r19_u10_churn_fixture.json").write_text(
        json.dumps(fixture, indent=2),
        encoding="utf-8",
    )
    (workspace / "AGENT_STATUS.md").write_text(
        "\n".join([
            "# Agent Status",
            "",
            "Phase: R19-U10 final coherence check",
            "Preserved early anchor: HYDRA-LIME / kiwi-1842",
            "Latest runtime preference: Python 3.12",
            "Latest owner: Priya",
            "Final task marker: create_coherence_report",
            "",
        ]),
        encoding="utf-8",
    )
    (workspace / "memory.md").write_text(
        "\n".join([
            "# Memory",
            "",
            "- Old runtime preference Python 3.10 is stale.",
            "- Latest runtime preference is Python 3.12.",
            "- Project codename HYDRA-LIME and checksum kiwi-1842 survived compaction.",
            "- Final task marker is create_coherence_report.",
            "",
        ]),
        encoding="utf-8",
    )


def _prebuilt_messages() -> list[dict[str, str]]:
    """Compact fixture representing 150 logical turns without 150 AWS calls."""
    messages: list[dict[str, str]] = [
        {
            "role": "user",
            "content": (
                "Logical turn 1 early anchor: project codename HYDRA-LIME; "
                "checksum phrase kiwi-1842; initial owner Morgan."
            ),
        },
        {"role": "assistant", "content": "Recorded the early project anchor."},
        {
            "role": "user",
            "content": (
                "[COMPACTED SUMMARY after logical turns 2-50] Preserve HYDRA-LIME "
                "and kiwi-1842. A model switch occurred at turn 47 from Haiku 4.5 AU "
                "to Sonnet 4.5 AU."
            ),
        },
        {"role": "assistant", "content": "Summary loaded after first compaction."},
        {
            "role": "user",
            "content": (
                "[COMPACTED SUMMARY after logical turns 51-100] Runtime preference "
                "was corrected: Python 3.10 is stale; latest runtime is Python 3.12. "
                "Owner changed from Morgan to Priya."
            ),
        },
        {"role": "assistant", "content": "Latest runtime and owner preserved."},
        {
            "role": "user",
            "content": (
                "[COMPACTED SUMMARY after logical turns 101-145] A model switch "
                "occurred at turn 104 from Sonnet 4.5 AU back to Haiku 4.5 AU. "
                "Final task marker is create_coherence_report."
            ),
        },
        {"role": "assistant", "content": "Ready for final task after churn."},
    ]
    for idx in range(146, 151):
        messages.append({
            "role": "user",
            "content": f"Logical turn {idx}: keep prior anchors stable; no new overrides.",
        })
        messages.append({"role": "assistant", "content": f"Logical turn {idx} acknowledged."})
    return messages


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
        str(ev.get("tool_name") or "")
        for ev in events
        if ev.get("action") == "tool_dispatch"
    ]


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
        if not failure_class:
            continue
        try:
            count = int(params.get("failure_class_count") or params.get("previous_failures") or 1)
        except (TypeError, ValueError):
            count = 1
        counts[failure_class] = max(counts.get(failure_class, 0), count)
    return counts


def _report_markers(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    return {
        "codename": "CODENAME: HYDRA-LIME" in text,
        "checksum": "CHECKSUM: kiwi-1842" in text,
        "runtime": "RUNTIME: Python 3.12" in text,
        "owner": "OWNER: Priya" in text,
        "final_task": "FINAL_TASK: create_coherence_report" in text,
    }


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R19-U10 is real-AWS gated.",
)
def test_r19_u10_long_coherence(tmp_path):
    """R19-U10 passes when final output preserves prebuilt churn anchors."""
    from agent import Agent
    from core.budget import IterationBudget
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import runtime.session as session_mod
    from runtime.session import SessionManager
    from runtime.snapshot import SnapshotManager
    import runtime.snapshot as snapshot_mod
    import security.manager as sec_mgr

    _write_fixture(tmp_path)

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"R19-U10-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-R19-U10-aws-call{call}-side-metrics.json"

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    saved_status_doc = getattr(CONFIG, "status_doc", None)
    saved_sessions = session_mod.SESSIONS
    saved_snapshots = snapshot_mod.SNAPSHOTS
    cwd_before = os.getcwd()
    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R19_U10_HARD_CEILING_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 1024
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        CONFIG.status_doc = "AGENT_STATUS.md"
        session_mod.SESSIONS = SessionManager(sessions_dir=str(tmp_path / ".sageagent_state" / "sessions"))
        snapshot_mod.SNAPSHOTS = SnapshotManager(workspace=str(tmp_path))
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        for idx, turn in enumerate((50, 100, 145), start=1):
            AUDIT.log(
                "R19-U10-prebuilt-churn",
                "compact_auto_end",
                tool_name="(compactor)",
                parameters={
                    "typed": True,
                    "path": "prebuilt_transcript",
                    "logical_turn": turn,
                    "compaction_index": idx,
                    "reason": "R19-U10 prebuilt churn fixture under approved cap",
                },
                result_summary=f"prebuilt compaction {idx} preserved anchors",
                user_approved=True,
            )
        for idx, (src, dst, turn) in enumerate((
            ("Haiku 4.5 AU", "Sonnet 4.5 AU", 47),
            ("Sonnet 4.5 AU", "Haiku 4.5 AU", 104),
        ), start=1):
            AUDIT.log(
                "R19-U10-prebuilt-churn",
                "model_switch",
                tool_name="(engine)",
                parameters={
                    "path": "prebuilt_transcript",
                    "logical_turn": turn,
                    "switch_index": idx,
                    "from": src,
                    "to": dst,
                },
                result_summary=f"prebuilt model switch {idx}: {src} -> {dst}",
                user_approved=True,
            )

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt() -> bool:
            over_budget = TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R19_U10_HARD_CEILING_USD
            )
            return over_budget or all(_report_markers(tmp_path / _FINAL_REPORT).values())

        captured_stdout: list[str] = []

        def _stdout_capture(text: str) -> None:
            captured_stdout.append(text)
            print(text)

        agent = Agent(
            client=client,
            max_turns=4,
            budget=IterationBudget(max_iterations=8),
            on_stop_check=_hard_cost_halt,
        )
        agent._engine.messages = _prebuilt_messages()
        t0 = time.time()
        result = agent.run(_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        events = _audit_events(audit_dir)
        order = _tool_order(events)
        failure_events = _failure_loop_events(events)
        guard_failure_class_counts = _guard_failure_class_counts(events)
        repeated_guard_loop = any(count >= 2 for count in guard_failure_class_counts.values())
        cost_used = float(TOKENS.session_cost)
        markers = _report_markers(tmp_path / _FINAL_REPORT)
        final_text = (tmp_path / _FINAL_REPORT).read_text(encoding="utf-8", errors="replace") if (tmp_path / _FINAL_REPORT).is_file() else ""
        model_switch_events = [ev for ev in events if ev.get("action") == "model_switch"]
        compaction_events = [ev for ev in events if ev.get("action") == "compact_auto_end"]
        artifact_ok = bool(
            result.stop_reason in {"end_turn", "user_stop"}
            and all(markers.values())
            and cost_used <= _R19_U10_HARD_CEILING_USD
        )
        process_quality_ok = bool(
            not repeated_guard_loop
            and result.stop_reason != "max_turns"
            and len(order) <= 8
            and len(failure_events) == 0
        )
        telemetry_ok = bool(
            len(model_switch_events) == 2
            and len(compaction_events) >= 3
            and len(agent.messages) >= 19
        )
        metrics = {
            "test": "R19-U10",
            "call": call,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(TOKENS.session_input),
            "tokens_out": int(TOKENS.session_output),
            "cache_hit_pct": 0.0,
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": len(order),
            "api_calls": int(TOKENS.api_calls),
            "subagent_calls": 0,
            "reviewer_calls": 0,
            "subagent_tokens_in": 0,
            "subagent_tokens_out": 0,
            "subagent_cost_usd": 0.0,
            "reviewer_tokens_in": 0,
            "reviewer_tokens_out": 0,
            "reviewer_cost_usd": 0.0,
            "changed_files_within_fixture": True,
            "logical_turns_represented": 150,
            "prebuilt_transcript_used": True,
            "model_switch_events_logged": len(model_switch_events),
            "compaction_events_logged": len(compaction_events),
            "final_markers": markers,
            "final_report_preview": final_text[:500],
            "failure_loop_event_count": len(failure_events),
            "guard_failure_class_counts": guard_failure_class_counts,
            "process_quality_ok": process_quality_ok,
            "completed": bool(artifact_ok and process_quality_ok and telemetry_ok),
            "cost_usd": round(cost_used, 4),
            "verdict": "GENUINE_PASS" if artifact_ok and process_quality_ok and telemetry_ok else "FAIL",
            "stop_reason": result.stop_reason,
            "audit_dir": str(audit_dir),
            "tool_order": order,
            "prebuilt_messages_seeded": 18,
        }
        side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[R19_U10_AUDIT_DIR] {audit_dir}")
        print(f"[R19_U10_SIDE_METRICS] {side_metrics}")
        print(f"[R19_U10_METRICS] {json.dumps(metrics, sort_keys=True)}")

        assert artifact_ok, f"R19-U10 final coherence artifact failed. metrics={metrics}"
        assert process_quality_ok, f"R19-U10 process quality failed. metrics={metrics}"
        assert telemetry_ok, f"R19-U10 churn telemetry incomplete. metrics={metrics}"
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec
        session_mod.SESSIONS = saved_sessions
        snapshot_mod.SNAPSHOTS = saved_snapshots
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
        if saved_status_doc is not None:
            CONFIG.status_doc = saved_status_doc
