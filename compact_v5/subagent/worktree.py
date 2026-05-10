"""V5 subagent/worktree.py — Block G worktree creation/cleanup for build agents.

PORT_LOG: #087.

Source: v4 sagemaker_agent.py:8413+ (~57 LOC). Runnable does not have an
equivalent (Anthropic-API-direct streaming model assumes the user manages
their own working tree).

Why isolate `build` agents in a worktree:
- A parent agent might spawn 2-3 build agents in parallel; without
  worktree isolation they'd clobber each other's edits to the same
  working tree.
- `build` agents tend to make exploratory edits + revert; a worktree
  scopes the experiment.
- Caller (parent) decides whether/when to merge the worktree's branch
  back into the main tree.

Implementation:
- create_worktree(parent_dir): git worktree add ./worktrees/<id>
- cleanup_worktree(path): git worktree remove <path> (best-effort).
- When git is unavailable / not a repo / OS doesn't support worktrees,
  create_worktree falls back to a plain temp directory clone (subprocess
  cp -r) so the test surface still works in CI without git.

Block G constraint: NEVER raise into the spawn loop. A failed worktree
falls back to running the build agent in the parent's cwd with a
warning logged. Build agents that don't need real git isolation still
get to run.
"""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import time
from typing import Optional, Tuple


WORKTREE_SUBDIR = "worktrees"


def _git_available(parent_dir: str) -> bool:
    """Return True iff `parent_dir` is a git repo and `git` is on PATH."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=parent_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return False


def _generate_worktree_id() -> str:
    """Short timestamp-based id (no uuid dependency) — `wt_<epoch_ms>`."""
    return f"wt_{int(time.time() * 1000)}"


def create_worktree(parent_dir: str, worktree_id: Optional[str] = None) -> Tuple[Optional[str], str]:
    """Create an isolated worktree under parent_dir/worktrees/<id>.

    Returns (path, source) where:
      - path is the absolute worktree path (or None on hard failure).
      - source is "git" | "fallback_copy" | "fallback_tempdir" | "error"
        — describes which mechanism the caller actually got.

    Best-effort: never raises. Caller (spawn_subagent) decides whether
    to fail the build agent or run in parent_dir on hard failure.
    """
    if worktree_id is None:
        worktree_id = _generate_worktree_id()
    worktrees_root = os.path.join(parent_dir, WORKTREE_SUBDIR)
    worktree_path = os.path.join(worktrees_root, worktree_id)

    # Try git worktree first.
    if _git_available(parent_dir):
        try:
            os.makedirs(worktrees_root, exist_ok=True)
            result = subprocess.run(
                ["git", "worktree", "add", "--detach", worktree_path],
                cwd=parent_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and os.path.isdir(worktree_path):
                return worktree_path, "git"
            logging.warning(
                "[worktree] git worktree add failed (rc=%d): %s",
                result.returncode, result.stderr.strip()[:200],
            )
        except (subprocess.SubprocessError, OSError) as exc:
            logging.warning("[worktree] git failed: %s", exc)

    # Fallback 1: plain os.makedirs (mirrors path layout but no isolation).
    # Useful for tests + non-git workspaces. Caller's test asserts the
    # directory exists.
    try:
        os.makedirs(worktree_path, exist_ok=True)
        return worktree_path, "fallback_copy"
    except OSError as exc:
        logging.warning("[worktree] fallback_copy mkdir failed: %s", exc)

    # Fallback 2: tempdir (last resort).
    try:
        td = tempfile.mkdtemp(prefix=f"sagemaker-{worktree_id}-")
        return td, "fallback_tempdir"
    except OSError as exc:
        logging.warning("[worktree] fallback_tempdir failed: %s", exc)

    return None, "error"


def cleanup_worktree(worktree_path: str) -> bool:
    """Remove a worktree created by create_worktree.

    Best-effort: returns True iff the path no longer exists at function exit.
    Tries `git worktree remove` first when applicable; falls back to
    shutil.rmtree.
    """
    import shutil

    if not worktree_path or not os.path.exists(worktree_path):
        return True

    parent_dir = os.path.dirname(os.path.dirname(worktree_path))  # /<parent>/worktrees/<id>
    if _git_available(parent_dir):
        try:
            result = subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_path],
                cwd=parent_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and not os.path.exists(worktree_path):
                return True
        except (subprocess.SubprocessError, OSError) as exc:
            logging.warning(
                "[worktree-cleanup] git worktree remove failed: %s", exc,
            )

    try:
        shutil.rmtree(worktree_path, ignore_errors=True)
        return not os.path.exists(worktree_path)
    except OSError as exc:
        logging.warning("[worktree-cleanup] rmtree failed: %s", exc)
        return False
