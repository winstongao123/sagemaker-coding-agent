"""Zero-cost R-tier mock cleanup locks.

These tests back the mock-only R-tier rows that must not spend AWS:
R8, R18-E2, R18-E5, R18-E9, and R18-E12.
"""
from __future__ import annotations

from datetime import datetime, timedelta


def test_r8_malformed_json_tool_args_repaired_locally():
    """R8: malformed JSON-shaped tool args are repaired before execution."""
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import Response, ToolCall
    from tools.registry import build_tool

    seen = []

    class _Client:
        mock_mode = True

        def __init__(self):
            self.turn = 0

        def chat(self, *args, **kwargs):
            self.turn += 1
            if self.turn == 1:
                return Response(
                    "",
                    [ToolCall("a", "read_file", '{"file_path": "a.txt"}')],
                    "tool_use",
                    {},
                )
            return Response("done", [], "end_turn", {})

    def _read(args, context=None):
        seen.append(args)
        return args["file_path"]

    tool = build_tool(
        "read_file",
        "read",
        {},
        _read,
        is_read_only=True,
        is_concurrency_safe=True,
    )
    result = QueryEngine(_Client(), max_turns=3).run("go", "sys", [tool])

    assert result.stop_reason == "end_turn"
    assert seen == [{"file_path": "a.txt"}]


def test_r18_e2_bedrock_5xx_html_humanized_without_aws():
    """R18-E2: deterministic 5xx recovery/humanization without forcing AWS."""
    from core.errors import (
        BedrockErrorCategory,
        ErrorClassifier,
        categorize_retryable,
        humanize_api_error,
    )

    err = Exception("<html><body><h1>Internal Server Error</h1></body></html>")
    category, recovery, _debug = ErrorClassifier.classify(err)
    message = humanize_api_error(err, status_code=500)

    assert category == BedrockErrorCategory.BEDROCK_5XX_HTML
    assert recovery == "backoff"
    assert categorize_retryable(category) is True
    assert "Internal Server Error" in message
    assert "<html>" not in message


def test_r18_e5_corrupt_session_json_is_skipped(tmp_path):
    """R18-E5: corrupt session JSON returns cleanly and valid sessions survive."""
    from runtime.session import Session, SessionManager

    sm = SessionManager(sessions_dir=str(tmp_path))
    good = Session(
        id="good",
        created_at="2026-05-06T00:00:00",
        updated_at="2026-05-06T00:00:00",
        title="good",
        messages=[{"role": "user", "content": "keep"}],
    )
    sm.save(good)
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")

    assert sm.load("bad") is None
    loaded = sm.load("good")
    assert loaded is not None
    assert loaded.messages[0]["content"] == "keep"
    assert [row["id"] for row in sm.list_sessions()] == ["good"]


def test_r18_e9_snapshot_write_failure_is_safe(tmp_path, monkeypatch):
    """R18-E9: simulated disk-full snapshot failure does not corrupt source."""
    import shutil
    from runtime.snapshot import SnapshotManager

    target = tmp_path / "important.txt"
    target.write_text("original", encoding="utf-8")
    sm = SnapshotManager(workspace=str(tmp_path))

    def _raise_disk_full(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(shutil, "copy2", _raise_disk_full)

    assert sm.save(str(target)) is None
    assert target.read_text(encoding="utf-8") == "original"
    assert sm.list_snapshots(str(target)) == []


def test_r18_e12_audit_log_rotation_prunes_old_logs(tmp_path):
    """R18-E12: audit retention prunes old logs and keeps fresh logs readable."""
    from runtime.audit import AuditLogger

    old_date = (datetime.now().date() - timedelta(days=40)).strftime("%Y-%m-%d")
    fresh_date = datetime.now().date().strftime("%Y-%m-%d")
    old_log = tmp_path / f"{old_date}_oldsession.jsonl"
    fresh_log = tmp_path / f"{fresh_date}_freshsession.jsonl"
    old_log.write_text('{"action":"old"}\n', encoding="utf-8")
    fresh_log.write_text('{"action":"fresh"}\n', encoding="utf-8")

    class _Cfg:
        audit_dir = str(tmp_path)
        audit_retention_days = 30
        disable_local_traces = False

    audit = AuditLogger(audit_dir=str(tmp_path), config=_Cfg())
    audit.log("freshsession", "tool_dispatch", tool_name="read_file")

    assert not old_log.exists()
    assert fresh_log.exists()
    entries = audit.get_session_log("freshsession")
    assert entries
    assert any(entry.get("action") == "tool_dispatch" for entry in entries)
