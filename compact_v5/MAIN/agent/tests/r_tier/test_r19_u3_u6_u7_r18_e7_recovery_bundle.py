"""R-tier Stage 5 - recovery/results bundle.

Runs R19-U3, R19-U6, R19-U7, and R18-E7 in one real-Bedrock pytest
invocation while preserving per-test side metrics and audit logs. The test is
skipped unless RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
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
    "R19-U3": 0.50,
    "R19-U6": 0.20,
    "R19-U7": 0.20,
    "R18-E7": 0.10,
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

_U3_PROMPT = """You are working in the current directory.

Change the standard discount from 5% to 7% and keep the billing tests passing.

Requirements:
- Use grep or glob first to find all references before editing anything.
- Update the source, dependent tests, and docs that mention the standard discount.
- Do not modify unrelated code.
- Run pytest before you finish.
- Create change_summary.md with the files changed and the final pytest result.
- Use ASCII-only content in change_summary.md; do not use emoji, arrows, or other
  non-ASCII symbols.
"""

_U6_PROMPT = """You are working in the current directory.

Create recovery_report.md with the deployment health and active route.

Requirements:
- Call unstable_status first.
- If unstable_status returns malformed output, recover by retrying it once or by
  reading fallback_status.json.
- The report must mention malformed output recovery and the final status.
"""

_U7_PROMPT = """You are working in the current directory.

Exercise the repeated-call circuit breaker using loop_bait.

Requirements:
- Call loop_bait with key "same" until the runtime blocks the repeated identical
  call.
- Once it is blocked, do not call loop_bait again.
- Read fallback_plan.md and create circuit_breaker_report.md with the blocked
  repeated call and fallback code.
"""

_E7_PROMPT = """You are working in the current directory.

Call large_result to inspect the synthetic build log. The important checksum is
hidden in the large output body after the preview, not in the preview. If the
tool result is persisted or truncated, use result_replay with the stable
sageagent-result:// ref. The checksum record is near offset 2600; replay a small
slice around that offset instead of scanning the whole artifact. Create
long_output_report.md with the checksum and a short note that result_replay was
used.
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_fixture(workspace: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        if {".sageagent_state", "__pycache__", ".pytest_cache"} & set(path.parts):
            continue
        hashes[path.relative_to(workspace).as_posix()] = _sha256(path)
    return hashes


def _changed_file_count(before: dict[str, str], after: dict[str, str]) -> int:
    keys = set(before) | set(after)
    return sum(1 for key in keys if before.get(key) != after.get(key))


def _audit_events(audit_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for fp in sorted(audit_dir.glob("*.jsonl")):
        for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def _tool_count(events: list[dict[str, Any]], name: str) -> int:
    return sum(1 for ev in events if ev.get("action") == "tool_dispatch" and ev.get("tool_name") == name)


def _tool_order(events: list[dict[str, Any]]) -> list[str]:
    return [str(ev.get("tool_name")) for ev in events if ev.get("action") == "tool_dispatch"]


def _combined_text(events: list[dict[str, Any]], captured_stdout: list[str]) -> str:
    chunks = list(captured_stdout)
    for ev in events:
        chunks.append(str(ev.get("parameters") or ""))
        chunks.append(str(ev.get("result_summary") or ""))
        if ev.get("action") == "chat_response":
            resp = ((ev.get("parameters") or {}).get("response") or {})
            if isinstance(resp.get("text"), str):
                chunks.append(resp["text"])
    return "\n".join(chunks).lower()


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


def _run_pytest(workspace: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "test_billing.py", "-q"],
        cwd=str(workspace),
        text=True,
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _setup_u3(workspace: Path) -> None:
    _write(
        workspace / "discounts.py",
        'STANDARD_DISCOUNT = 0.05\n\n\ndef standard_discount():\n    return STANDARD_DISCOUNT\n',
    )
    _write(
        workspace / "billing.py",
        'from discounts import standard_discount\n\n\ndef discounted_total(amount):\n    return round(amount * (1 - standard_discount()), 2)\n',
    )
    _write(
        workspace / "test_billing.py",
        'from billing import discounted_total\n\n\ndef test_standard_discount_total():\n    assert discounted_total(100.0) == 95.0\n',
    )
    _write(
        workspace / "docs" / "discount_policy.md",
        "The standard discount is 5% for eligible accounts.\n",
    )


def _setup_u6(workspace: Path) -> None:
    _write(
        workspace / "fallback_status.json",
        '{"status":"green","active_route":"blue","source":"fallback"}\n',
    )


def _setup_u7(workspace: Path) -> None:
    _write(
        workspace / "fallback_plan.md",
        "After the repeated-call breaker fires, use fallback code SAFE-FALLBACK-77.\n",
    )


def _setup_e7(workspace: Path) -> None:
    _write(workspace / "README.md", "Use large_result to fetch the synthetic build log.\n")


def _u3_ready(workspace: Path) -> bool:
    code, _output = _run_pytest(workspace)
    return (
        code == 0
        and "0.07" in (workspace / "discounts.py").read_text(encoding="utf-8", errors="replace")
        and "93.0" in (workspace / "test_billing.py").read_text(encoding="utf-8", errors="replace")
        and "7%" in (workspace / "docs" / "discount_policy.md").read_text(encoding="utf-8", errors="replace")
        and (workspace / "change_summary.md").is_file()
    )


def _report_has(workspace: Path, rel: str, terms: tuple[str, ...]) -> bool:
    path = workspace / rel
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    return all(term in text for term in terms)


def _custom_tools(test_id: str) -> tuple[list[Any], Callable[[], dict[str, Any]]]:
    from tools import all_registered
    from tools.registry import build_tool

    state: dict[str, Any] = {"calls": 0}
    tools = list(all_registered())

    if test_id == "R19-U6":
        def _unstable_status(args: dict[str, Any], context: Any = None) -> str:
            state["calls"] += 1
            if state["calls"] == 1:
                return "<<malformed-status::{ route=blue status"
            return '{"status":"green","active_route":"blue","source":"retry"}'

        tools.append(build_tool(
            name="unstable_status",
            description="Fixture deployment status tool. The first call returns malformed output; retry or use fallback_status.json.",
            input_schema={"type": "object", "properties": {}},
            execute=_unstable_status,
            is_read_only=True,
            max_result_size_chars=2000,
        ))

    if test_id == "R19-U7":
        def _loop_bait(args: dict[str, Any], context: Any = None) -> str:
            state["calls"] += 1
            return "Error: deterministic repeated-call bait failure"

        tools.append(build_tool(
            name="loop_bait",
            description="Fixture repeated-call bait. It always fails so the runtime repeated-call breaker can be observed.",
            input_schema={
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
            execute=_loop_bait,
            is_read_only=True,
            max_result_size_chars=2000,
        ))

    if test_id == "R18-E7":
        def _large_result(args: dict[str, Any], context: Any = None) -> str:
            state["calls"] += 1
            head = "BUILD LOG START\n" + ("head-line ok\n" * 90)
            middle = "\nSTAGE5-CHECKSUM: kiwi-1842\n"
            tail = "tail-line ok\n" * 90 + "BUILD LOG END\n"
            return head + ("middle filler\n" * 105) + middle + ("more filler\n" * 120) + tail

        tools.append(build_tool(
            name="large_result",
            description="Returns a large synthetic build log whose checksum is hidden outside the preview.",
            input_schema={"type": "object", "properties": {}},
            execute=_large_result,
            is_read_only=True,
            max_result_size_chars=2000,
        ))

    return tools, lambda: dict(state)


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
    from runtime.audit import AUDIT
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    setup(workspace)
    before_hashes = _hash_fixture(workspace)
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"{test_id}-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    CONFIG.workspace = str(workspace)
    CONFIG.audit_dir = str(audit_dir)
    sec_mgr.rebuild_singleton_for_tests()
    AUDIT.__init__(audit_dir=str(audit_dir))
    TOKENS.reset()

    tools, state_fn = _custom_tools(test_id)

    def _halt() -> bool:
        return TOKENS.session_cost >= cap or ready(workspace)

    captured_stdout: list[str] = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        print(text)

    cwd_before = os.getcwd()
    try:
        os.chdir(str(workspace))
        agent = Agent(client=client, max_turns=16, on_stop_check=_halt)
        t0 = time.time()
        result = agent.run(prompt, tools=tools, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0
    finally:
        os.chdir(cwd_before)

    after_hashes = _hash_fixture(workspace)
    events = _audit_events(audit_dir)
    text = _combined_text(events, captured_stdout)
    order = _tool_order(events)
    failure_events = _failure_loop_events(events)
    guard_failure_class_counts = _guard_failure_class_counts(events)
    changed_files_count = _changed_file_count(before_hashes, after_hashes)
    edit_count = sum(_tool_count(events, name) for name in ("edit_file", "write_file", "notebook_edit"))
    exec_count = sum(_tool_count(events, name) for name in ("bash", "python_exec"))
    cost_used = float(TOKENS.session_cost)

    first_search = min([i for i, name in enumerate(order) if name in {"grep", "glob"}], default=None)
    first_edit = min([i for i, name in enumerate(order) if name in {"edit_file", "write_file"}], default=None)
    search_before_edit = first_search is not None and first_edit is not None and first_search < first_edit
    breaker_fired = any(ev.get("action") == "tool_failure_loop_blocked" for ev in failure_events)
    result_replay_used = _tool_count(events, "result_replay") >= 1
    result_ref_seen = "sageagent-result://" in text
    repeated_guard_loop = any(count >= 2 for count in guard_failure_class_counts.values())
    process_quality_ok = bool(not repeated_guard_loop and result.stop_reason != "max_turns")

    post_pytest_passed = None
    if test_id == "R19-U3":
        code, post_output = _run_pytest(workspace)
        _write(workspace / "post_bundle_pytest_output.txt", post_output)
        post_pytest_passed = code == 0
        process_quality_ok = bool(process_quality_ok and search_before_edit)

    completed_by_test = {
        "R19-U3": bool(
            ready(workspace)
            and post_pytest_passed is True
            and search_before_edit
            and edit_count >= 1
            and process_quality_ok
        ),
        "R19-U6": bool(
            _report_has(workspace, "recovery_report.md", ("malformed", "green", "blue"))
            and (state_fn().get("calls", 0) >= 2 or _tool_count(events, "read_file") >= 1)
            and process_quality_ok
        ),
        "R19-U7": bool(
            breaker_fired
            and state_fn().get("calls", 0) == 2
            and _report_has(workspace, "circuit_breaker_report.md", ("blocked", "safe-fallback-77"))
            and process_quality_ok
        ),
        "R18-E7": bool(
            result_replay_used
            and result_ref_seen
            and _report_has(workspace, "long_output_report.md", ("kiwi-1842", "result_replay"))
            and process_quality_ok
        ),
    }
    completed = (
        result.stop_reason in {"end_turn", "user_stop"}
        and completed_by_test[test_id]
        and cost_used <= cap
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
        "tool_calls": sum(1 for ev in events if ev.get("action") == "tool_dispatch") + len([
            ev for ev in failure_events if ev.get("action") == "tool_failure_loop_blocked"
        ]),
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
        "changed_files_count": changed_files_count,
        "edit_tool_count": edit_count,
        "exec_tool_count": exec_count,
        "search_before_edit": search_before_edit if test_id == "R19-U3" else None,
        "post_pytest_passed": post_pytest_passed,
        "malformed_injection_seen": "<<malformed-status" in text if test_id == "R19-U6" else None,
        "custom_tool_calls": state_fn().get("calls", 0),
        "breaker_fired": breaker_fired if test_id == "R19-U7" else None,
        "failure_loop_event_count": len(failure_events),
        "guard_failure_class_counts": guard_failure_class_counts,
        "process_quality_ok": process_quality_ok,
        "result_replay_used": result_replay_used if test_id == "R18-E7" else None,
        "result_ref_seen": result_ref_seen if test_id == "R18-E7" else None,
        "completed": bool(completed),
        "cost_usd": round(cost_used, 4),
        "verdict": "GENUINE_PASS" if completed else "FAIL",
        "stop_reason": result.stop_reason,
        "audit_dir": str(audit_dir),
        "tool_order": order,
        "response_excerpt": text[-2000:],
    }
    side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\n[{test_id}_AUDIT_DIR] {audit_dir}")
    print(f"[{test_id}_SIDE_METRICS] {side_metrics}")
    print(f"[{test_id}_METRICS] {json.dumps(metrics, sort_keys=True)}")
    return metrics


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; Stage 5 recovery/results bundle is real-AWS gated.",
)
def test_r19_u3_u6_u7_r18_e7_recovery_results_bundle(tmp_path):
    """Stage 5 passes when all recovery/result members satisfy evidence criteria."""
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
            ("R19-U3", _U3_PROMPT, _setup_u3, _u3_ready),
            ("R19-U6", _U6_PROMPT, _setup_u6, lambda p: _report_has(p, "recovery_report.md", ("green", "blue"))),
            ("R19-U7", _U7_PROMPT, _setup_u7, lambda p: _report_has(p, "circuit_breaker_report.md", ("safe-fallback-77",))),
            ("R18-E7", _E7_PROMPT, _setup_e7, lambda p: _report_has(p, "long_output_report.md", ("kiwi-1842",))),
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
            assert metrics["completed"] is True, f"{metrics['test']} failed Stage 5 criteria: {metrics}"
            assert metrics["cost_usd"] <= _hard_ceiling(metrics["test"]), metrics
        u7 = next(row for row in results if row["test"] == "R19-U7")
        assert u7["breaker_fired"] is True, u7
        assert u7["custom_tool_calls"] == 2, u7
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
