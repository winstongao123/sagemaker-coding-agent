"""
V4.7.1 enhancement tests.

Tests the three features added in v4.7.1:
  1. _maybe_auto_checkpoint — local-git baseline maintenance
  2. build_todo_restoration_message — post-compact TODO restoration
  3. Compactor.compact integration with TODO restoration

These are REAL tests (not static checks) — they create temp git repos,
call the actual functions, and verify observable behavior.

Run:  python test_v471_enhancements.py
"""

from __future__ import annotations
import os
import sys
import tempfile
import shutil
import subprocess
import traceback
from typing import List, Tuple

# Import the module under test
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa  # type: ignore


RESULTS: List[Tuple[str, bool, str]] = []  # [(name, passed, message)]


def _run(name: str, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
        print(f"  ✓ {name}")
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
        print(f"  ✗ {name}")
        print(f"    AssertionError: {e}")
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"  ✗ {name}")
        print(f"    {type(e).__name__}: {e}")
        traceback.print_exc()


def _init_git_repo(workspace: str):
    """Initialize a git repo with one baseline commit."""
    env = dict(os.environ)
    env["GIT_AUTHOR_NAME"] = "test"
    env["GIT_AUTHOR_EMAIL"] = "test@test"
    env["GIT_COMMITTER_NAME"] = "test"
    env["GIT_COMMITTER_EMAIL"] = "test@test"
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=workspace, check=True, env=env)
    # Create and commit a baseline file
    with open(os.path.join(workspace, "baseline.txt"), "w") as f:
        f.write("baseline\n")
    subprocess.run(["git", "add", "baseline.txt"], cwd=workspace, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "initial", "--no-verify"],
                   cwd=workspace, check=True, env=env)
    return env


def _git_log_count(workspace: str, env: dict) -> int:
    out = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        capture_output=True, text=True, cwd=workspace, env=env
    )
    return int(out.stdout.strip())


# ============ Tests ============

def test_auto_commit_disabled_by_default():
    """When auto_commit_every=0, no checkpoint should happen regardless of edits."""
    with tempfile.TemporaryDirectory() as tmp:
        env = _init_git_repo(tmp)
        old_workspace = sa.CONFIG.workspace
        old_every = sa.CONFIG.auto_commit_every
        old_counter = sa._AUTO_COMMIT_COUNTER
        try:
            sa.CONFIG.workspace = tmp
            sa.CONFIG.auto_commit_every = 0
            sa._AUTO_COMMIT_COUNTER = 0
            # Simulate 10 edits
            with open(os.path.join(tmp, "f.txt"), "w") as f:
                f.write("x")
            for _ in range(10):
                result = sa._maybe_auto_checkpoint(tmp)
                assert result is None, f"expected None when disabled, got: {result}"
            # Still just the baseline commit
            assert _git_log_count(tmp, env) == 1, "no commits should be added when disabled"
        finally:
            sa.CONFIG.workspace = old_workspace
            sa.CONFIG.auto_commit_every = old_every
            sa._AUTO_COMMIT_COUNTER = old_counter


def test_auto_commit_fires_at_threshold():
    """When auto_commit_every=3, the 3rd call should trigger a commit."""
    with tempfile.TemporaryDirectory() as tmp:
        env = _init_git_repo(tmp)
        old_workspace = sa.CONFIG.workspace
        old_every = sa.CONFIG.auto_commit_every
        old_counter = sa._AUTO_COMMIT_COUNTER
        try:
            sa.CONFIG.workspace = tmp
            sa.CONFIG.auto_commit_every = 3
            sa._AUTO_COMMIT_COUNTER = 0

            # Make a change so there's something to commit
            with open(os.path.join(tmp, "change1.txt"), "w") as f:
                f.write("first change\n")

            r1 = sa._maybe_auto_checkpoint(tmp)
            assert r1 is None, f"call 1 should not commit, got: {r1}"
            r2 = sa._maybe_auto_checkpoint(tmp)
            assert r2 is None, f"call 2 should not commit, got: {r2}"
            r3 = sa._maybe_auto_checkpoint(tmp)
            assert r3 is not None, "call 3 should trigger a commit"
            assert "auto-checkpoint" in r3, f"commit message should include 'auto-checkpoint', got: {r3}"

            count = _git_log_count(tmp, env)
            assert count == 2, f"expected 2 commits (baseline + checkpoint), got {count}"
        finally:
            sa.CONFIG.workspace = old_workspace
            sa.CONFIG.auto_commit_every = old_every
            sa._AUTO_COMMIT_COUNTER = old_counter


def test_auto_commit_noop_when_nothing_staged():
    """If nothing changed since last commit, auto-commit should be a no-op even at threshold."""
    with tempfile.TemporaryDirectory() as tmp:
        env = _init_git_repo(tmp)
        old_workspace = sa.CONFIG.workspace
        old_every = sa.CONFIG.auto_commit_every
        old_counter = sa._AUTO_COMMIT_COUNTER
        try:
            sa.CONFIG.workspace = tmp
            sa.CONFIG.auto_commit_every = 2
            sa._AUTO_COMMIT_COUNTER = 0

            # NO changes made after baseline
            sa._maybe_auto_checkpoint(tmp)
            r2 = sa._maybe_auto_checkpoint(tmp)
            assert r2 is None, f"no-op expected when nothing to commit, got: {r2}"

            count = _git_log_count(tmp, env)
            assert count == 1, f"expected 1 commit (just baseline), got {count}"
        finally:
            sa.CONFIG.workspace = old_workspace
            sa.CONFIG.auto_commit_every = old_every
            sa._AUTO_COMMIT_COUNTER = old_counter


def test_auto_commit_not_a_git_repo():
    """Outside a git repo, auto-commit should silently skip without errors."""
    with tempfile.TemporaryDirectory() as tmp:
        # NO git init
        old_workspace = sa.CONFIG.workspace
        old_every = sa.CONFIG.auto_commit_every
        old_counter = sa._AUTO_COMMIT_COUNTER
        try:
            sa.CONFIG.workspace = tmp
            sa.CONFIG.auto_commit_every = 1
            sa._AUTO_COMMIT_COUNTER = 0
            r = sa._maybe_auto_checkpoint(tmp)
            assert r is None, f"expected None (no-op) outside git repo, got: {r}"
        finally:
            sa.CONFIG.workspace = old_workspace
            sa.CONFIG.auto_commit_every = old_every
            sa._AUTO_COMMIT_COUNTER = old_counter


def test_todo_restoration_empty():
    """With no todos, restoration message should be None."""
    old_todos = list(sa._TODOS)
    try:
        sa._TODOS.clear()
        result = sa.build_todo_restoration_message()
        assert result is None, f"expected None for empty todos, got: {result}"
    finally:
        sa._TODOS.clear()
        sa._TODOS.extend(old_todos)


def test_todo_restoration_mixed_states():
    """With mixed-status todos, message should group by status and include all."""
    old_todos = list(sa._TODOS)
    try:
        sa._TODOS.clear()
        # Append to the same list object (do not rebind _TODOS)
        sa._TODOS.extend([
            {"content": "Task A done", "status": "completed", "activeForm": "Doing A"},
            {"content": "Task B active", "status": "in_progress", "activeForm": "Doing B"},
            {"content": "Task C pending", "status": "pending", "activeForm": "Doing C"},
            {"content": "Task D pending", "status": "pending", "activeForm": "Doing D"},
        ])
        result = sa.build_todo_restoration_message()
        assert result is not None, "expected restoration message, got None"
        assert "POST-COMPACT TODO RESTORATION" in result, "missing header"
        assert "Task A done" in result, "missing completed task"
        assert "Task B active" in result, "missing in_progress task"
        assert "Task C pending" in result, "missing first pending task"
        assert "Task D pending" in result, "missing second pending task"
        assert "In progress" in result, "missing 'In progress' section"
        assert "Pending" in result, "missing 'Pending' section"
        assert "Completed" in result, "missing 'Completed' section"
        # Also check order: in_progress should come before pending (we want actionable items visible first)
        assert result.index("In progress") < result.index("Pending"), "in_progress should come before pending"
    finally:
        sa._TODOS.clear()
        sa._TODOS.extend(old_todos)


def test_todo_restoration_truncates_completed():
    """With many completed todos, should only show last 3 and note the count."""
    old_todos = list(sa._TODOS)
    try:
        sa._TODOS.clear()
        completed = [{"content": f"Done {i}", "status": "completed", "activeForm": "x"} for i in range(10)]
        sa._TODOS.extend(completed)
        result = sa.build_todo_restoration_message()
        assert result is not None
        assert "Completed (10)" in result, f"expected 'Completed (10)' in output, got: {result}"
        assert "and 7 earlier" in result, f"expected '... and 7 earlier', got: {result}"
        # Should contain last 3 (Done 7, 8, 9)
        assert "Done 9" in result, "missing most recent completed"
        assert "Done 7" in result, "missing 3rd-most-recent completed"
        # Should NOT contain Done 0 (oldest)
        assert "Done 0 " not in result, "oldest completed should be truncated"
    finally:
        sa._TODOS.clear()
        sa._TODOS.extend(old_todos)


def test_compact_includes_todos():
    """Compactor.compact() should include TODO restoration in the output."""
    old_todos = list(sa._TODOS)
    try:
        sa._TODOS.clear()
        sa._TODOS.extend([
            {"content": "Fix the auth bug", "status": "in_progress", "activeForm": "Fixing auth"},
            {"content": "Write tests", "status": "pending", "activeForm": "Writing tests"},
        ])

        fake_messages = [
            {"role": "user", "content": "start coding"},
            {"role": "assistant", "content": "ok working on it"},
            {"role": "user", "content": "keep going"},
            {"role": "assistant", "content": "done with part 1"},
            {"role": "user", "content": "now part 2"},
        ]
        compacted = sa.Compactor.compact(fake_messages, "We made progress on auth fix.")

        # Flatten the text content of all messages for search
        all_text = ""
        for m in compacted:
            c = m.get("content", "")
            if isinstance(c, str):
                all_text += c + "\n"
            elif isinstance(c, list):
                for block in c:
                    if isinstance(block, dict):
                        all_text += block.get("text", "") + "\n"

        assert "Fix the auth bug" in all_text, "compacted output missing in_progress todo"
        assert "Write tests" in all_text, "compacted output missing pending todo"
        assert "POST-COMPACT TODO RESTORATION" in all_text, "missing restoration header"
        assert "CONVERSATION SUMMARY" in all_text, "missing conversation summary"
    finally:
        sa._TODOS.clear()
        sa._TODOS.extend(old_todos)


def test_compact_no_todos_no_error():
    """Compactor.compact() should work fine when there are no todos (no regression)."""
    old_todos = list(sa._TODOS)
    try:
        sa._TODOS.clear()
        fake_messages = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hi back"},
            {"role": "user", "content": "bye"},
        ]
        compacted = sa.Compactor.compact(fake_messages, "Short chat.")
        assert len(compacted) >= 1, "expected at least summary message"
        # Should NOT contain the TODO header
        all_text = ""
        for m in compacted:
            c = m.get("content", "")
            if isinstance(c, str):
                all_text += c
        assert "POST-COMPACT TODO RESTORATION" not in all_text
    finally:
        sa._TODOS.clear()
        sa._TODOS.extend(old_todos)


# ============ Main ============

def main():
    print("=" * 60)
    print("V4.7.1 enhancement tests")
    print("=" * 60)

    print("\n[auto-commit checkpoint]")
    _run("auto_commit disabled by default", test_auto_commit_disabled_by_default)
    _run("auto_commit fires at threshold", test_auto_commit_fires_at_threshold)
    _run("auto_commit no-op when nothing staged", test_auto_commit_noop_when_nothing_staged)
    _run("auto_commit no-op outside git repo", test_auto_commit_not_a_git_repo)

    print("\n[todo restoration helper]")
    _run("empty todos returns None", test_todo_restoration_empty)
    _run("mixed statuses render correctly", test_todo_restoration_mixed_states)
    _run("long completed list is truncated", test_todo_restoration_truncates_completed)

    print("\n[compact integration]")
    _run("compact includes todo restoration", test_compact_includes_todos)
    _run("compact works fine without todos", test_compact_no_todos_no_error)

    print()
    print("=" * 60)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"Result: {passed}/{total} passed")
    if passed != total:
        print()
        print("Failures:")
        for name, ok, msg in RESULTS:
            if not ok:
                print(f"  - {name}: {msg}")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
