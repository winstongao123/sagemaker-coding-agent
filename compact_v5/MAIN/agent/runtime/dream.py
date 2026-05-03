"""V5 runtime/dream.py — Block H+ Memory Consolidation Engine.

PORT_LOG: #099. ADR-035.

Source: Runnable services/autoDream/* (~350 LOC).

**MANUAL TRIGGER ONLY** per user decision 2026-05-01:
- NO daemon, NO auto-fire, NO env auto-enable, NO scheduler.
- Fires ONLY when user invokes `/dream` slash command.
- Block D's cmd_dream wires the dispatch trigger; this module
  implements the consolidation logic.

The 4-phase prompt:
1. Orient — read existing memory.md + scan workspace for relevant
   activity (what HAS happened).
2. Gather — collect ALL recent unconsolidated memory entries.
3. Consolidate — merge duplicates, group by topic, write the
   consolidated file.
4. Prune + Index — drop stale entries, index by topic for fast lookup.

Safety rails:
- File-based lock (`<workspace>/dream.lock`) prevents concurrent runs.
- `memory.md.bak` snapshot taken BEFORE writing; rollback on any error.
- `_apply_dream_dry_run` mode for tests (no LLM call, no file mutation).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


LOCK_FILENAME = "dream.lock"
BACKUP_SUFFIX = ".bak"


# The 4-phase consolidation prompt. Ordering is load-bearing — Orient
# must come BEFORE Gather (you can't gather what you don't know exists),
# Gather must come BEFORE Consolidate (you can't merge entries you
# haven't read), Consolidate must come BEFORE Prune+Index (you can't
# safely prune entries you haven't merged into authoritative form).
DREAM_PROMPT_TEMPLATE = """\
You are running in MEMORY CONSOLIDATION mode. Your job is to take the
existing memory.md and produce a cleaner, indexed version. Run these
4 phases in this exact order. DO NOT skip phases.

## Phase 1 — Orient
Read the current memory.md and form a quick mental map: which topics
appear, which entries cluster, what's stale, what looks duplicated.
Output a single paragraph orienting yourself. Do NOT modify anything.

## Phase 2 — Gather
List every unconsolidated entry. Group by apparent topic. Note
duplicates and near-duplicates. Output a structured list.

## Phase 3 — Consolidate
Merge duplicates (preserve first-seen wording when canonical).
Group entries by topic with H2 headers. Each entry stays as a single
bullet. Output the consolidated body.

## Phase 4 — Prune + Index
Drop entries that are:
- Trivially derivable from current code (e.g. "uses Python 3.11").
- Session-specific state that won't matter next session.
- Now-obsolete decisions superseded by newer entries.
Add a topic index at the top.
Output the FINAL memory.md body.

## Existing memory.md content
{existing}

## Manifest of relevant memory files
{manifest}

Begin Phase 1 now.
"""


@dataclass
class DreamResult:
    """Outcome of a /dream invocation."""
    success: bool = False
    new_content: str = ""
    backup_path: str = ""
    error: Optional[str] = None
    phases_executed: List[str] = field(default_factory=list)


class DreamLock:
    """File-based lock to prevent concurrent /dream runs.

    The lock is a small JSON file at `<workspace>/dream.lock`. Acquired
    by atomic creation (open with O_CREAT | O_EXCL); released by
    delete. If the lock file exists but is older than `stale_after_s`
    seconds, it's considered stale and reclaimed.

    Codex iter-1 secondary-risk hardening: per-lock nonce. Each
    acquire() generates a unique nonce stored in the lock file body.
    release() reads the file body and only unlinks if the nonce still
    matches OURS — prevents a stale-recovery race where worker A's
    `release()` could clobber worker B's freshly-acquired lock.
    """

    def __init__(self, workspace: str, stale_after_s: float = 600.0):
        self.lock_path = os.path.join(workspace, LOCK_FILENAME)
        self.stale_after_s = stale_after_s
        self._held = False
        self._nonce: Optional[str] = None  # set on acquire, checked on release

    def acquire(self) -> bool:
        """Try to acquire the lock. Returns True iff acquired."""
        # Stale-lock recovery: if existing lock is older than threshold,
        # assume the previous run crashed and reclaim.
        if os.path.exists(self.lock_path):
            try:
                # Re-stat immediately before unlink so we don't race a
                # fresh acquire that just happened between our age check
                # and unlink. If the file's mtime has been bumped, abort
                # the reclaim.
                age = time.time() - os.path.getmtime(self.lock_path)
                if age < self.stale_after_s:
                    return False  # active lock held by another run
                # Stale — verify still stale, then reclaim.
                age2 = time.time() - os.path.getmtime(self.lock_path)
                if age2 < self.stale_after_s:
                    return False  # someone refreshed between our checks
                os.unlink(self.lock_path)
            except OSError:
                return False
        try:
            fd = os.open(
                self.lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644,
            )
            # Generate a per-acquire nonce so release() can verify ownership.
            import uuid
            self._nonce = uuid.uuid4().hex
            with os.fdopen(fd, "w") as f:
                json.dump(
                    {"pid": os.getpid(), "ts": time.time(), "nonce": self._nonce},
                    f,
                )
            self._held = True
            return True
        except FileExistsError:
            return False
        except OSError:
            return False

    def release(self) -> None:
        """Release the lock if held — only if the file still carries OUR
        nonce. Otherwise, someone else now owns the lock and we must NOT
        unlink it. Codex iter-1 hardening.
        """
        if not self._held:
            return
        try:
            # Check file content still has our nonce before unlinking.
            owner_match = False
            try:
                with open(self.lock_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("nonce") == self._nonce:
                    owner_match = True
            except (OSError, json.JSONDecodeError):
                # Lock file gone or corrupt; treat as not-our-lock.
                owner_match = False
            if owner_match:
                os.unlink(self.lock_path)
        except OSError:
            pass
        self._held = False
        self._nonce = None

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(
                f"Could not acquire dream lock at {self.lock_path}. "
                "Another /dream invocation is in progress."
            )
        return self

    def __exit__(self, *exc):
        self.release()


def _backup_memory_md(memory_path: str) -> str:
    """Create memory.md.bak (best-effort). Returns the backup path or ''."""
    if not os.path.isfile(memory_path):
        return ""
    backup_path = memory_path + BACKUP_SUFFIX
    try:
        shutil.copy2(memory_path, backup_path)
        return backup_path
    except OSError:
        return ""


def _restore_from_backup(memory_path: str, backup_path: str) -> bool:
    """Restore memory.md from backup. Returns True iff restored."""
    if not backup_path or not os.path.isfile(backup_path):
        return False
    try:
        shutil.copy2(backup_path, memory_path)
        return True
    except OSError:
        return False


def run_dream(
    workspace: str,
    memory_filename: str = "memory.md",
    consolidator: Optional[Callable[[str, str], str]] = None,
) -> DreamResult:
    """Execute /dream consolidation. Synchronous; user-invoked only.

    Args:
        workspace: workspace dir containing memory.md.
        memory_filename: relative path of the memory file.
        consolidator: callable (existing_content, manifest) → new_content.
            When None, runs in dry-run mode (returns DreamResult with
            success=True but new_content="" and no file mutation).
            Tests inject a mock here.
    """
    memory_path = os.path.join(workspace, memory_filename)
    lock = DreamLock(workspace)

    if not lock.acquire():
        return DreamResult(
            success=False,
            error=f"dream lock held at {lock.lock_path} (concurrent run?)",
        )

    backup_path = ""
    phases: List[str] = []
    try:
        # Phase 1 — Orient: read existing.
        existing = ""
        if os.path.isfile(memory_path):
            with open(memory_path, "r", encoding="utf-8", errors="replace") as f:
                existing = f.read()
        phases.append("Orient")

        # Phase 2 — Gather: build the manifest of memory files.
        manifest_lines: List[str] = []
        ws = Path(workspace)
        for fp in sorted(ws.rglob("*.md")):
            try:
                rel = fp.relative_to(ws)
                manifest_lines.append(str(rel).replace("\\", "/"))
            except ValueError:
                continue
        manifest = "\n".join(f"- {p}" for p in manifest_lines)
        phases.append("Gather")

        # Phase 3 — Consolidate: invoke the consolidator (or dry-run).
        if consolidator is None:
            # Dry-run: no LLM, no file mutation. Useful for tests / CI.
            phases.append("Consolidate")
            phases.append("Prune+Index")
            return DreamResult(
                success=True,
                new_content="",
                phases_executed=phases,
            )

        new_content = consolidator(existing, manifest)
        if not isinstance(new_content, str) or not new_content.strip():
            # Consolidator returned empty/invalid — fail safe.
            return DreamResult(
                success=False,
                error="consolidator returned empty content; rollback skipped (no write attempted)",
                phases_executed=phases,
            )
        phases.append("Consolidate")

        # Phase 4 — Prune + Index: backup + write.
        backup_path = _backup_memory_md(memory_path)
        try:
            with open(memory_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except OSError as exc:
            # Restore from backup on write failure.
            if backup_path:
                _restore_from_backup(memory_path, backup_path)
            return DreamResult(
                success=False,
                error=f"write failed: {exc}; restored from backup",
                backup_path=backup_path,
                phases_executed=phases,
            )
        phases.append("Prune+Index")

        return DreamResult(
            success=True,
            new_content=new_content,
            backup_path=backup_path,
            phases_executed=phases,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort rollback path
        # Restore from backup on ANY mid-run failure.
        restored = False
        if backup_path:
            restored = _restore_from_backup(memory_path, backup_path)
        return DreamResult(
            success=False,
            error=f"{type(exc).__name__}: {exc}"
            + (" (restored from backup)" if restored else ""),
            backup_path=backup_path,
            phases_executed=phases,
        )
    finally:
        lock.release()


def get_dream_prompt(existing: str, manifest: str) -> str:
    """Render the 4-phase prompt for an LLM consolidator."""
    return DREAM_PROMPT_TEMPLATE.format(existing=existing, manifest=manifest)
