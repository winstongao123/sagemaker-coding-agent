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


def test_dream_lock_contextmanager_pattern(tmp_path):
    """DreamLock supports `with` context-manager pattern."""
    from runtime.dream import DreamLock, LOCK_FILENAME

    workspace = str(tmp_path)
    with DreamLock(workspace):
        # Inside the block, the lock file exists.
        assert (tmp_path / LOCK_FILENAME).exists()
    # After exit, lock is released.
    assert not (tmp_path / LOCK_FILENAME).exists()
