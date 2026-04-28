"""V4.10.0 #47 — Per-subagent env-details injection.

Tests:
1. env_details contains agent_type, depth, workspace cwd lines.
2. env_details still works when workspace is not a git repo (fail-quiet).
3. env_details respects timeout / never raises (uncatchable failure would
   break sub-agent spawn).
4. Output is short (≤ 6 lines) — small-model friendly.
5. Output is deterministic for the same workspace state.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


def _make_temp_workspace(init_git: bool = False) -> str:
    tmp = tempfile.mkdtemp(prefix="v410_subagent_env_")
    if init_git:
        try:
            subprocess.run(["git", "init", "-q"], cwd=tmp, timeout=5, check=False)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp, timeout=5, check=False)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp, timeout=5, check=False)
            with open(os.path.join(tmp, "README.md"), "w") as f:
                f.write("test\n")
            subprocess.run(["git", "add", "."], cwd=tmp, timeout=5, check=False)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp, timeout=5, check=False)
        except Exception:
            pass
    return tmp


def test_env_details_contains_required_lines():
    ws = _make_temp_workspace(init_git=False)
    out = sa._build_subagent_env_details("build", depth=1, workspace=ws)
    assert "# Sub-agent Environment" in out
    assert "Agent type: build" in out
    assert "Sub-agent depth: 1" in out
    assert f"Workspace cwd: {ws}" in out


def test_env_details_works_in_non_git_dir():
    """Fail-quiet: a non-git workspace should still produce the core lines,
    just without the Git HEAD / working-tree lines."""
    ws = _make_temp_workspace(init_git=False)
    out = sa._build_subagent_env_details("plan", depth=2, workspace=ws)
    assert "Agent type: plan" in out
    assert "Sub-agent depth: 2" in out
    # Without git init, the git lines should be absent — but no exception.
    # We don't assert their absence too strictly because the parent dir may
    # itself be a git repo on the developer's machine.
    assert "# Sub-agent Environment" in out


def test_env_details_in_git_repo_includes_head():
    ws = _make_temp_workspace(init_git=True)
    out = sa._build_subagent_env_details("verify", depth=1, workspace=ws)
    assert "Agent type: verify" in out
    # Git lines should appear when git init succeeded
    assert ("Git HEAD:" in out) or ("Git working tree:" in out), f"Expected git info: {out!r}"


def test_env_details_short_for_small_model():
    """Small-model friendliness: max 6 short lines."""
    ws = _make_temp_workspace(init_git=True)
    out = sa._build_subagent_env_details("explore", depth=1, workspace=ws)
    lines = out.splitlines()
    assert len(lines) <= 6, f"Env details too long ({len(lines)} lines) for small models"
    for ln in lines:
        assert len(ln) <= 200, f"Env line too long: {ln!r}"


def test_env_details_deterministic_for_cache():
    """Two consecutive calls in the same dir/state must produce the same string,
    so the dynamic-section bytes don't churn unnecessarily."""
    ws = _make_temp_workspace(init_git=True)
    a = sa._build_subagent_env_details("general", depth=1, workspace=ws)
    b = sa._build_subagent_env_details("general", depth=1, workspace=ws)
    assert a == b, f"Env details not deterministic across calls"


def test_env_details_never_raises():
    """Even with a totally bogus workspace path, the helper must not raise —
    a sub-agent spawn must never fail because git lookup misbehaved."""
    bogus = "/this/path/should/never/exist/for_v410_test_xxxx"
    out = sa._build_subagent_env_details("review", depth=1, workspace=bogus)
    assert "Agent type: review" in out  # core lines still present


if __name__ == "__main__":
    tests = [
        ("env_details_contains_required_lines", test_env_details_contains_required_lines),
        ("env_details_works_in_non_git_dir", test_env_details_works_in_non_git_dir),
        ("env_details_in_git_repo_includes_head", test_env_details_in_git_repo_includes_head),
        ("env_details_short_for_small_model", test_env_details_short_for_small_model),
        ("env_details_deterministic_for_cache", test_env_details_deterministic_for_cache),
        ("env_details_never_raises", test_env_details_never_raises),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
