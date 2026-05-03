"""Block H+ — Memory Consolidation Engine (`/dream` MANUAL ONLY).

Source: Runnable services/autoDream/* (~350 LOC) — but with the daemon
+ auto-fire + env-auto-enable scheduler intentionally DROPPED per user
decision 2026-05-01. v5 ships /dream as a manual-only slash command.

Tests per TEST_DESIGN §Block H+ (5 tests, $0 except T5):
- test_dream_4_phase_prompt_orient_gather_consolidate_prune
- test_dream_lock_file_prevents_concurrent_runs
- test_dream_rollback_on_failure
- test_dream_no_daemon_no_auto_fire (verifies user decision 2026-05-01)
- test_dream_real_consolidation_haiku (T5, ~$0.05; gated by RUN_REAL_BEDROCK)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# TEST_DESIGN row 1 — 4 phases in the prompt
# ============================================================

def test_dream_4_phase_prompt_orient_gather_consolidate_prune():
    """Dream prompt contains the 4 phases in correct order."""
    from runtime.dream import get_dream_prompt

    prompt = get_dream_prompt(existing="x", manifest="y")
    # Phase headers verbatim.
    assert "Phase 1 — Orient" in prompt
    assert "Phase 2 — Gather" in prompt
    assert "Phase 3 — Consolidate" in prompt
    assert "Phase 4 — Prune + Index" in prompt
    # Order check: each phase header appears AFTER the previous one.
    p1 = prompt.index("Phase 1")
    p2 = prompt.index("Phase 2")
    p3 = prompt.index("Phase 3")
    p4 = prompt.index("Phase 4")
    assert p1 < p2 < p3 < p4


# ============================================================
# TEST_DESIGN row 2 — lock file prevents concurrent runs
# ============================================================

def test_dream_lock_file_prevents_concurrent_runs(tmp_path):
    """A second /dream invocation while one is in progress fails."""
    from runtime.dream import DreamLock, run_dream

    workspace = str(tmp_path)
    (tmp_path / "memory.md").write_text("- entry 1", encoding="utf-8")

    # Acquire the lock manually as if a /dream is in progress.
    held_lock = DreamLock(workspace)
    assert held_lock.acquire() is True
    try:
        # Now a fresh run_dream call must fail to acquire.
        result = run_dream(workspace, consolidator=lambda e, m: "wont reach")
        assert result.success is False
        assert "lock" in (result.error or "").lower()
    finally:
        held_lock.release()


def test_dream_lock_releases_on_normal_completion(tmp_path):
    """After a successful /dream run, the lock file is removed."""
    from runtime.dream import LOCK_FILENAME, run_dream

    workspace = str(tmp_path)
    (tmp_path / "memory.md").write_text("- entry 1", encoding="utf-8")

    result = run_dream(workspace, consolidator=lambda e, m: "## Consolidated\n- entry 1")
    assert result.success is True
    # Lock file is removed after run.
    assert not (tmp_path / LOCK_FILENAME).exists()


# ============================================================
# TEST_DESIGN row 3 — rollback on failure
# ============================================================

def test_dream_rollback_on_failure(tmp_path):
    """Mid-run failure → memory.md.bak restored; original memory.md untouched."""
    from runtime.dream import run_dream

    workspace = str(tmp_path)
    original_content = "## Original\n- entry 1\n- entry 2"
    (tmp_path / "memory.md").write_text(original_content, encoding="utf-8")

    def failing_consolidator(existing, manifest):
        raise RuntimeError("simulated LLM failure")

    result = run_dream(workspace, consolidator=failing_consolidator)
    assert result.success is False
    assert "RuntimeError" in (result.error or "")
    # Original content unchanged (rollback restored from backup, OR
    # write was never attempted).
    after = (tmp_path / "memory.md").read_text(encoding="utf-8")
    assert after == original_content


def test_dream_rollback_when_consolidator_returns_empty(tmp_path):
    """Empty/whitespace consolidator output → fail without writing."""
    from runtime.dream import run_dream

    workspace = str(tmp_path)
    (tmp_path / "memory.md").write_text("orig", encoding="utf-8")

    result = run_dream(workspace, consolidator=lambda e, m: "")
    assert result.success is False
    assert (tmp_path / "memory.md").read_text(encoding="utf-8") == "orig"


# ============================================================
# TEST_DESIGN row 4 — no daemon / no auto-fire (user decision 2026-05-01)
# ============================================================

def test_dream_no_daemon_no_auto_fire():
    """v5 codebase has no daemon / asyncio.create_task / atexit.register
    spawning /dream automatically. No SAGEMAKER_AUTO_DREAM env var.

    Verifies user decision 2026-05-01: /dream is MANUAL only.
    """
    import re

    agent_root = Path(_AGENT_ROOT)
    forbidden_patterns = [
        # No background thread spawning a dream consolidation.
        re.compile(r"Thread\s*\(\s*target\s*=\s*\w*[Dd]ream"),
        re.compile(r"asyncio\.create_task\([^)]*[Dd]ream"),
        re.compile(r"atexit\.register\([^)]*[Dd]ream"),
        # No env-var auto-enable.
        re.compile(r"SAGEMAKER_AUTO_DREAM"),
        re.compile(r"AUTO_DREAM_ENABLED"),
    ]

    offenders = []
    for fp in agent_root.rglob("*.py"):
        # Skip the test file itself (regex strings would match).
        if fp.name == "test_block_h_plus.py":
            continue
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pat in forbidden_patterns:
            if pat.search(text):
                offenders.append(f"{fp.relative_to(agent_root)}: {pat.pattern}")

    assert not offenders, (
        "Block H+ user decision 2026-05-01 — /dream is MANUAL only. "
        f"Found auto-fire patterns:\n  " + "\n  ".join(offenders)
    )


# ============================================================
# TEST_DESIGN row 5 — real Haiku consolidation (T5; ~$0.05; gated)
# ============================================================

@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="T5 real-AWS test (~$0.05). Gate with RUN_REAL_BEDROCK=1.",
)
def test_dream_real_consolidation_haiku():
    """Real /dream invocation on test memory.md → outputs cleaner file.

    Cap: ~$0.05. Deferred to R-tier R6 (memory consolidation /dream).
    """
    pytest.skip(
        "Deferred to R-tier R6 (Memory consolidation /dream). "
        "Block H+ ships without burning AWS credit during unit-test phase."
    )


# ============================================================
# Behavioral lock tests
# ============================================================

def test_dream_dry_run_when_no_consolidator(tmp_path):
    """consolidator=None → dry-run; no file mutation, no LLM call."""
    from runtime.dream import run_dream

    workspace = str(tmp_path)
    (tmp_path / "memory.md").write_text("orig", encoding="utf-8")
    result = run_dream(workspace, consolidator=None)
    assert result.success is True
    assert result.new_content == ""
    # All 4 phases recorded for dry-run.
    assert "Orient" in result.phases_executed
    assert "Gather" in result.phases_executed
    assert "Consolidate" in result.phases_executed
    assert "Prune+Index" in result.phases_executed
    # Original file unchanged.
    assert (tmp_path / "memory.md").read_text(encoding="utf-8") == "orig"


def test_dream_creates_backup_before_write(tmp_path):
    """A successful run produces memory.md.bak alongside the new file."""
    from runtime.dream import run_dream

    workspace = str(tmp_path)
    original = "## Original\n- entry 1"
    (tmp_path / "memory.md").write_text(original, encoding="utf-8")

    result = run_dream(workspace, consolidator=lambda e, m: "## New\n- entry 1")
    assert result.success is True
    assert result.backup_path
    # backup contains original content; main file contains new content.
    assert (tmp_path / "memory.md.bak").read_text(encoding="utf-8") == original
    assert "## New" in (tmp_path / "memory.md").read_text(encoding="utf-8")


def test_dream_lock_stale_recovery(tmp_path):
    """A stale lock (older than threshold) is reclaimed on next acquire."""
    import time
    from runtime.dream import DreamLock, LOCK_FILENAME

    workspace = str(tmp_path)
    # Manually create a stale lock file (mtime in the past).
    lock_path = tmp_path / LOCK_FILENAME
    lock_path.write_text('{"pid": 99999, "ts": 0}', encoding="utf-8")
    stale_time = time.time() - 3600  # 1 hour old
    os.utime(str(lock_path), (stale_time, stale_time))

    # New lock with stale_after_s=600 should reclaim.
    lock = DreamLock(workspace, stale_after_s=600.0)
    assert lock.acquire() is True
    lock.release()


def test_dream_no_memory_md_handled(tmp_path):
    """When memory.md doesn't exist yet, run_dream still succeeds (creates it)."""
    from runtime.dream import run_dream

    workspace = str(tmp_path)
    # No memory.md created.
    result = run_dream(
        workspace, consolidator=lambda e, m: "## First\n- new entry",
    )
    assert result.success is True
    assert (tmp_path / "memory.md").read_text(encoding="utf-8") == "## First\n- new entry"
    # No backup since there was no prior file.
    assert result.backup_path == ""


# ============================================================
# Codex iter-1 finding-lock tests
# ============================================================

def test_dream_invoked_via_console_chat_ui(tmp_path, monkeypatch):
    """Codex iter-1 main finding lock: ConsoleChatUI consumes the
    "dream_invoked" side-effect and actually invokes runtime.dream.run_dream
    end-to-end. Was previously a doc claim with no code consumer.
    """
    from runtime.config import CONFIG
    from ui.chat_ui import ConsoleChatUI

    # Set workspace to tmp_path so the test exercises a real /dream run.
    _saved_ws = CONFIG.workspace
    CONFIG.workspace = str(tmp_path)
    (tmp_path / "memory.md").write_text(
        "## Existing\n- entry 1", encoding="utf-8",
    )

    # Build a fake agent + a fake client whose chat() returns canned text
    # (the consolidated body). The ConsoleChatUI._invoke_dream helper
    # uses agent.client.chat(...).text as the consolidator output.
    class _FakeResponse:
        text = "## Consolidated by Haiku\n- entry 1 (deduped)"

    class _FakeClient:
        model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
        mock_mode = True

        def chat(self, **kwargs):
            return _FakeResponse()

    class _FakeAgent:
        client = _FakeClient()

        def run(self, *a, **kw):
            from core import QueryEngine
            class _Result:
                stop_reason = "end_turn"
                text = ""
            return _Result()

        def stop(self):
            pass

        def clear(self, **kw):
            pass

    fake_agent = _FakeAgent()

    # Need iteration_budget_widget on ConsoleChatUI since send() calls
    # render_html on it. Build a minimal stub.
    class _StubWidget:
        def render_html(self) -> str:
            return ""

    ui = ConsoleChatUI.__new__(ConsoleChatUI)
    ui.agent = fake_agent
    ui.budget_widget = _StubWidget()
    ui.thinking_widget = _StubWidget()

    try:
        out = ui.send("/dream")
        # cmd_dream's text + dream invocation status concatenated.
        assert "/dream" in out.lower() or "dream" in out.lower()
        # The ENGINE actually wrote new memory.md content.
        assert (tmp_path / "memory.md").read_text(encoding="utf-8") == \
            "## Consolidated by Haiku\n- entry 1 (deduped)"
        # And the backup was created.
        assert (tmp_path / "memory.md.bak").exists()
        # Output mentions the phases.
        assert "Orient" in out or "phases" in out.lower()
    finally:
        CONFIG.workspace = _saved_ws


def test_dream_lock_release_clean_when_owner(tmp_path):
    """Codex iter-2/iter-3 lock contract: when A holds the lock and
    releases without contention, the lock_path must be removed.

    See ADR-035 §"Concurrency trade-off" for why the residual TOCTOU
    race window between read+unlink is acceptable for v5's manual-only
    deployment shape. This lock test covers the happy path; the
    cross-worker scenarios (A vs B reclaim) are covered by
    test_dream_lock_release_only_unlinks_own_nonce.
    """
    from runtime.dream import DreamLock, LOCK_FILENAME

    workspace = str(tmp_path)
    a = DreamLock(workspace)
    assert a.acquire() is True
    lock_path = tmp_path / LOCK_FILENAME
    assert lock_path.exists()
    a.release()
    assert not lock_path.exists()


def test_dream_lock_release_only_unlinks_own_nonce(tmp_path):
    """Codex iter-1 secondary-risk lock: release() must NOT unlink a lock
    file whose nonce no longer matches ours.

    Setup:
    - Worker A acquires the lock (nonce_A).
    - Worker B simulates a stale-recovery: overwrites the lock file with
      a fresh nonce_B (mimicking what B would do after deciding A's lock
      is stale).
    - Worker A calls release(). Lock file MUST still exist with nonce_B.
    """
    import json
    from runtime.dream import DreamLock, LOCK_FILENAME

    workspace = str(tmp_path)
    a = DreamLock(workspace)
    assert a.acquire() is True
    nonce_a = a._nonce

    # Simulate B reclaiming by rewriting the lock file with a fresh nonce.
    nonce_b = "B" * 32
    with open(tmp_path / LOCK_FILENAME, "w", encoding="utf-8") as f:
        json.dump({"pid": 99999, "ts": 0, "nonce": nonce_b}, f)

    # A's release must NOT remove the file (nonce no longer matches A's).
    a.release()
    assert (tmp_path / LOCK_FILENAME).exists(), (
        "release() with nonce mismatch must NOT unlink — would clobber "
        "another worker's freshly acquired lock (Codex iter-1 secondary)"
    )
    # Verify the file still has B's nonce.
    with open(tmp_path / LOCK_FILENAME, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["nonce"] == nonce_b


def test_dream_lock_contextmanager_pattern(tmp_path):
    """DreamLock supports `with` context-manager pattern."""
    from runtime.dream import DreamLock, LOCK_FILENAME

    workspace = str(tmp_path)
    with DreamLock(workspace):
        # Inside the block, the lock file exists.
        assert (tmp_path / LOCK_FILENAME).exists()
    # After exit, lock is released.
    assert not (tmp_path / LOCK_FILENAME).exists()
