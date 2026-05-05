"""SOFTWARE-GATE lock tests for enforced /verify and /done close gates."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def _seed_skills(tmp_path: Path) -> Path:
    skills = tmp_path / "skills"
    for name in ("verify", "simplify"):
        skill = skills / name
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Use when {name}.\n---\nbody\n",
            encoding="utf-8",
        )
    return skills


def _configure(tmp_path, monkeypatch):
    from runtime.config import CONFIG
    import commands as cmd_mod

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "skills_dir", str(_seed_skills(tmp_path)))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    monkeypatch.setattr(CONFIG, "disable_local_traces", False)
    cmd_mod._SKILLS_SINGLETON = None


def _fresh_evidence(tmp_path: Path):
    status = tmp_path / "AGENT_STATUS.md"
    tests = tmp_path / "logs" / "tests.log"
    review = tmp_path / "reviews" / "review.md"
    results = tmp_path / ".sageagent_state" / "tool_results" / "index.jsonl"
    subagent = tmp_path / "logs" / "subagent.jsonl"
    telemetry = tmp_path / "logs" / "telemetry.jsonl"

    status.write_text("# Agent Status\n\nCurrent phase: verify gate\n", encoding="utf-8")
    tests.parent.mkdir(parents=True, exist_ok=True)
    tests.write_text("4 passed\n", encoding="utf-8")
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(
        "VERDICT: APPROVE\nSHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW\n",
        encoding="utf-8",
    )
    results.parent.mkdir(parents=True, exist_ok=True)
    results.write_text(
        '{"ref":"sageagent-result://session/result-1","artifact_path":"x"}\n',
        encoding="utf-8",
    )
    subagent.write_text(
        '{"schema":"sageagent.subagent_result.v1","stop_reason":"end_turn"}\n',
        encoding="utf-8",
    )
    telemetry.write_text('{"action":"compact_auto_end","cache_trend":{"latest":0.5}}\n', encoding="utf-8")
    return {
        "status_path": str(status),
        "test_paths": [str(tests)],
        "review_paths": [str(review)],
        "result_paths": [str(results)],
        "subagent_paths": [str(subagent)],
        "telemetry_paths": [str(telemetry)],
    }


def test_verify_blocks_missing_test_and_review_evidence(tmp_path, monkeypatch):
    from commands import dispatch_command

    _configure(tmp_path, monkeypatch)
    (tmp_path / "AGENT_STATUS.md").write_text("fresh status", encoding="utf-8")

    result = dispatch_command("/verify full", ctx={"gate_evidence": {}})

    assert result.side_effect == "verify_blocked"
    assert "VERIFY BLOCKED" in result.text
    assert "tests:" in result.text
    assert "review:" in result.text
    assert (tmp_path / ".sageagent_state" / "gates" / "last_verify.json").is_file()


def test_done_requires_fresh_passing_verify_record(tmp_path, monkeypatch):
    from commands import dispatch_command

    _configure(tmp_path, monkeypatch)
    evidence = _fresh_evidence(tmp_path)

    before_verify = dispatch_command("/done full", ctx={"gate_evidence": evidence})
    assert before_verify.side_effect == "done_blocked"
    assert "last_verify" in before_verify.text

    verify = dispatch_command("/verify full", ctx={"gate_evidence": evidence})
    assert verify.side_effect == "verify_passed"

    done = dispatch_command("/done full", ctx={"gate_evidence": evidence})
    assert done.side_effect == "done_ready"
    assert "READY-TO-SHIP" in done.text
    assert (tmp_path / ".sageagent_state" / "gates" / "last_done.json").is_file()


def test_done_rechecks_status_freshness_after_verify(tmp_path, monkeypatch):
    from commands import dispatch_command

    _configure(tmp_path, monkeypatch)
    evidence = _fresh_evidence(tmp_path)
    evidence["freshness_seconds"] = 1

    assert dispatch_command("/verify full", ctx={"gate_evidence": evidence}).side_effect == "verify_passed"
    old = time.time() - 60
    os.utime(tmp_path / "AGENT_STATUS.md", (old, old))

    done = dispatch_command("/done full", ctx={"gate_evidence": evidence})
    assert done.side_effect == "done_blocked"
    assert "status:" in done.text
    assert "stale" in done.text


def test_done_blocks_unresolved_failure_loop_telemetry(tmp_path, monkeypatch):
    from commands import dispatch_command

    _configure(tmp_path, monkeypatch)
    evidence = _fresh_evidence(tmp_path)
    Path(evidence["telemetry_paths"][0]).write_text(
        '{"action":"tool_failure_loop_blocked","signature":"bash:boom"}\n',
        encoding="utf-8",
    )

    verify = dispatch_command("/verify full", ctx={"gate_evidence": evidence})
    assert verify.side_effect == "verify_blocked"
    assert "telemetry:" in verify.text

    done = dispatch_command("/done full", ctx={"gate_evidence": evidence})
    assert done.side_effect == "done_blocked"
    assert "tool_failure_loop" in done.text or "telemetry:" in done.text
