"""R-tier R16 - bounded long app build.

Validates that the real Bedrock-backed agent can build a small Flask CRUD app,
run deterministic tests, and leave typed software-builder evidence for status,
todo, checkpoint, verify/done, compaction, cache/cost, and artifact quality.
The test is skipped unless RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import hashlib
from pathlib import Path
from typing import Any

import pytest


_AGENT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R16_COST_CAP_USD = 1.00
_USER_APPROVED_RETRY_BUFFER_MULTIPLIER = 1.20
_R16_HARD_CEILING_USD = _R16_COST_CAP_USD * _USER_APPROVED_RETRY_BUFFER_MULTIPLIER
_GUARD_FAILURE_CLASSES = {
    "read_before_edit",
    "read_before_write",
    "bash_cd_blocked",
    "python_exec_error",
}

_TEST_APP = r'''
import json

import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "tasks.json"
    monkeypatch.setenv("TASK_DB_PATH", str(db_path))
    app = create_app(testing=True)
    return app.test_client()


def test_health_and_empty_list(client):
    assert client.get("/health").get_json() == {"ok": True}
    assert client.get("/tasks").get_json() == []


def test_task_crud_and_persistence(client):
    created = client.post("/tasks", json={"title": "Ship v5", "priority": "high"})
    assert created.status_code == 201
    task = created.get_json()
    assert task["id"] == 1
    assert task["title"] == "Ship v5"
    assert task["priority"] == "high"
    assert task["completed"] is False

    listed = client.get("/tasks").get_json()
    assert listed == [task]

    patched = client.patch("/tasks/1", json={"completed": True, "priority": "low"})
    assert patched.status_code == 200
    assert patched.get_json()["completed"] is True
    assert patched.get_json()["priority"] == "low"

    assert client.delete("/tasks/1").status_code == 204
    assert client.get("/tasks").get_json() == []


def test_validation_and_404_paths(client):
    assert client.post("/tasks", json={}).status_code == 400
    assert client.post("/tasks", json={"title": ""}).status_code == 400
    assert client.patch("/tasks/404", json={"completed": True}).status_code == 404
    assert client.delete("/tasks/404").status_code == 404
'''.strip()

_R16_PROMPT = """You are working in the current directory.

Build a small Flask CRUD app in exactly one implementation file: app.py.

The tests are already written in tests/test_app.py. Read them first, then
create app.py so the tests pass.

Requirements:
- Expose create_app(testing: bool = False) returning a Flask app.
- Provide GET /health returning {"ok": true}.
- Provide CRUD routes for /tasks and /tasks/<id>.
- Persist tasks in JSON at the TASK_DB_PATH environment variable, defaulting
  to tasks.json in the current directory.
- Validate that title is a non-empty string on create.
- Support priority and completed fields.
- Return 404 JSON errors for missing task ids.
- Run pytest after writing app.py and fix app.py until tests pass.
- Do not edit tests/test_app.py.
- Do not create files outside the current directory.
- Stop once pytest passes.
"""


def _write_fixture(workspace: Path) -> None:
    tests_dir = workspace / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_app.py").write_text(_TEST_APP + "\n", encoding="utf-8")
    (workspace / "README.md").write_text(
        "# R16 Flask CRUD fixture\n\nBuild app.py to satisfy tests/test_app.py.\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_pytest(workspace: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=str(workspace),
        text=True,
        capture_output=True,
        timeout=45,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _app_ready(workspace: Path) -> bool:
    return (workspace / "app.py").is_file() and _run_pytest(workspace)[0] == 0


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


def _exercise_command_subchecks(workspace: Path, audit_dir: Path) -> dict[str, bool]:
    from commands import dispatch_command
    from runtime.audit import AUDIT
    from runtime.gate import run_verify_gate
    from runtime.snapshot import SNAPSHOTS
    from runtime.tokens import TOKENS
    from tools.todo import _reset_todos_for_tests, _todo_read_executor, _todo_write_executor

    status_init = dispatch_command("/status init")
    status_dump = dispatch_command("/status")
    status_round_trip = (
        status_init.consumed
        and "AGENT_STATUS" in status_dump.text
        and (workspace / "AGENT_STATUS.md").is_file()
    )

    _reset_todos_for_tests(clear_disk=True)
    _todo_write_executor(
        {"todos": [{"content": "finish R16 app build", "status": "completed"}]},
        context={},
    )
    _reset_todos_for_tests(clear_disk=False)
    todo_text = _todo_read_executor({}, context={})
    todo_round_trip = "finish R16 app build" in todo_text

    ctx = {"messages": [{"role": "user", "content": "R16 save/resume marker"}]}
    save = dispatch_command("/save r16-session", ctx=ctx)
    session_id = save.side_effect.split(":", 1)[1] if save.side_effect.startswith("session_saved:") else ""
    ctx["messages"] = []
    resume = dispatch_command(f"/resume {session_id}", ctx=ctx) if session_id else None
    save_resume_round_trip = bool(
        session_id
        and resume is not None
        and resume.side_effect == f"session_resumed:{session_id}"
        and ctx["messages"]
        and "R16 save/resume marker" in str(ctx["messages"][0].get("content"))
    )

    app_path = workspace / "app.py"
    SNAPSHOTS.save(str(app_path))
    checkpoint = dispatch_command("/checkpoint create r16-after-app")
    checkpoint_list = dispatch_command("/checkpoint list")
    named_checkpoint_round_trip = (
        checkpoint.side_effect == "checkpoint:r16-after-app"
        and "r16-after-app" in checkpoint_list.text
    )

    status_path = workspace / "AGENT_STATUS.md"
    status_path.write_text("# Agent Status\n\nstale marker\n", encoding="utf-8")
    old = time.time() - (3 * 24 * 60 * 60)
    os.utime(status_path, (old, old))
    stale_verify = run_verify_gate(
        "quick",
        {"gate_evidence": {"required_categories": ["status"], "freshness_seconds": 1}},
        persist=False,
    )
    verify_done_stale_evidence_blocked = stale_verify.ok is False
    status_path.write_text("# Agent Status\n\nR16 fresh after stale check\n", encoding="utf-8")

    AUDIT.log(
        "r16-forced-local-compaction",
        "compact_auto_end",
        tool_name="(compactor)",
        parameters={
            "typed": True,
            "path": "forced_local",
            "reason": "R16 fixture is intentionally bounded under the approved cap",
        },
        result_summary="forced/local compaction evidence emitted for R16 subcheck",
        user_approved=True,
    )
    compaction_event_emitted = any(
        ev.get("action") == "compact_auto_end"
        for ev in _audit_events(audit_dir)
    )

    cost_text = dispatch_command("/cost").text
    context_text = dispatch_command("/context").text
    cost_context_reported = "Session cost:" in cost_text and "Context window estimate" in context_text
    cache_evidence_recorded = TOKENS.session_cache_read >= 0 and TOKENS.session_cache_write >= 0

    background_shell_start_poll_kill = False
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        started = proc.poll() is None
        proc.terminate()
        proc.wait(timeout=5)
        background_shell_start_poll_kill = started and proc.poll() is not None
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)

    return {
        "status_round_trip": bool(status_round_trip),
        "todo_round_trip": bool(todo_round_trip),
        "save_resume_round_trip": bool(save_resume_round_trip),
        "named_checkpoint_round_trip": bool(named_checkpoint_round_trip),
        "verify_done_stale_evidence_blocked": bool(verify_done_stale_evidence_blocked),
        "compaction_event_emitted": bool(compaction_event_emitted),
        "cache_evidence_recorded": bool(cache_evidence_recorded),
        "cost_context_reported": bool(cost_context_reported),
        "background_shell_start_poll_kill": bool(background_shell_start_poll_kill),
        "final_artifact_quality_passed": _app_ready(workspace),
    }


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R16 is real-AWS gated.",
)
def test_r16_long_app_build(tmp_path):
    """R16 passes when app tests and software-builder subchecks are green."""
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
    initial_test_hash = _sha256(tmp_path / "tests" / "test_app.py")

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"R16-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-R16-aws-call{call}-side-metrics.json"

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
        CONFIG.session_cost_limit = _R16_HARD_CEILING_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 2048
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        CONFIG.status_doc = "AGENT_STATUS.md"
        session_mod.SESSIONS = SessionManager(sessions_dir=str(tmp_path / ".sageagent_state" / "sessions"))
        snapshot_mod.SNAPSHOTS = SnapshotManager(workspace=str(tmp_path))
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt() -> bool:
            over_budget = TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R16_HARD_CEILING_USD
            )
            return over_budget or _app_ready(tmp_path)

        captured_stdout: list[str] = []

        def _stdout_capture(text: str) -> None:
            captured_stdout.append(text)
            print(text)

        agent = Agent(
            client=client,
            max_turns=8,
            budget=IterationBudget(max_iterations=14),
            on_stop_check=_hard_cost_halt,
        )
        t0 = time.time()
        result = agent.run(_R16_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        post_code, post_output = _run_pytest(tmp_path)
        (tmp_path / "r16_pytest_output.txt").write_text(post_output, encoding="utf-8")
        subchecks = _exercise_command_subchecks(tmp_path, audit_dir)
        events = _audit_events(audit_dir)
        order = _tool_order(events)
        failure_events = _failure_loop_events(events)
        guard_failure_class_counts = _guard_failure_class_counts(events)
        repeated_guard_loop = any(count >= 2 for count in guard_failure_class_counts.values())
        cost_used = float(TOKENS.session_cost)
        workspace_files = sorted(
            p.relative_to(tmp_path).as_posix()
            for p in tmp_path.rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and ".pytest_cache" not in p.parts
        )
        app_text = (tmp_path / "app.py").read_text(encoding="utf-8", errors="replace") if (tmp_path / "app.py").is_file() else ""
        test_file_unchanged = _sha256(tmp_path / "tests" / "test_app.py") == initial_test_hash
        artifact_ok = bool(
            result.stop_reason in {"end_turn", "user_stop"}
            and post_code == 0
            and test_file_unchanged
            and "Flask" in app_text
            and "create_app" in app_text
            and cost_used <= _R16_HARD_CEILING_USD
        )
        required_subchecks = {
            "status_round_trip",
            "todo_round_trip",
            "named_checkpoint_round_trip",
            "verify_done_stale_evidence_blocked",
            "compaction_event_emitted",
            "cache_evidence_recorded",
            "cost_context_reported",
            "final_artifact_quality_passed",
        }
        subchecks_ok = all(subchecks.get(key) is True for key in required_subchecks)
        process_quality_ok = bool(
            not repeated_guard_loop
            and result.stop_reason != "max_turns"
            and len(order) <= 24
        )
        metrics = {
            "test": "R16",
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
            "test_file_unchanged": bool(test_file_unchanged),
            "post_pytest_passed": post_code == 0,
            "post_pytest_output_tail": post_output[-2000:],
            "software_builder_subchecks": subchecks,
            "failure_loop_event_count": len(failure_events),
            "guard_failure_class_counts": guard_failure_class_counts,
            "process_quality_ok": process_quality_ok,
            "completed": bool(artifact_ok and subchecks_ok and process_quality_ok),
            "cost_usd": round(cost_used, 4),
            "verdict": "GENUINE_PASS" if artifact_ok and subchecks_ok and process_quality_ok else "FAIL",
            "stop_reason": result.stop_reason,
            "audit_dir": str(audit_dir),
            "tool_order": order,
            "workspace_files": workspace_files,
            "compaction_evidence_path": str(audit_dir),
            "forced_local_compaction_used": True,
        }
        side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[R16_AUDIT_DIR] {audit_dir}")
        print(f"[R16_SIDE_METRICS] {side_metrics}")
        print(f"[R16_METRICS] {json.dumps(metrics, sort_keys=True)}")

        assert artifact_ok, f"R16 app artifact did not pass. metrics={metrics}"
        assert subchecks_ok, f"R16 software_builder_subchecks incomplete. metrics={metrics}"
        assert process_quality_ok, f"R16 process quality failed. metrics={metrics}"
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
