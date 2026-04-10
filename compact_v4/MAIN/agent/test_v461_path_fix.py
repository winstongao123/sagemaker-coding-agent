"""V4.6.1 Path Resolution Fix — Unit Tests

Reproduces the exact failure case: agent launched in a subfolder, user asks
about a file that lives in a sibling of the workspace but within an
auto-detected allowed root (git repo). Verifies the fix makes the agent able
to find it without bash escaping.
"""

import os
import sys
import tempfile
import shutil
import subprocess

# Import BEFORE setting CONFIG.workspace so module-level singletons pick up test workspace.
# We use a fresh process per test to rebuild SECURITY with the new workspace.

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def make_fake_repo(base):
    """Create a fake git repo with a subfolder workspace and a target file
    at the repo root level that the workspace-bound tools shouldn't find
    without the fix."""
    repo = os.path.join(base, "fake_repo")
    os.makedirs(repo)
    # git init so auto-detect picks it up
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    # Workspace is a subfolder
    ws = os.path.join(repo, "subproj", "agent")
    os.makedirs(ws)
    # Target file lives OUTSIDE the workspace but INSIDE the repo
    target_dir = os.path.join(repo, "wins_docs", "compact_v4")
    os.makedirs(target_dir)
    target_file = os.path.join(target_dir, "sagemaker_agent.py")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("# fake V4 file\n" + "x = 1\n" * 100)
    return repo, ws, target_file


def run_in_subprocess(script, ws):
    """Run a test script with CONFIG.workspace = ws in a fresh Python process."""
    env = os.environ.copy()
    env["PYTHONPATH"] = HERE + os.pathsep + env.get("PYTHONPATH", "")
    env["V461_TEST_WS"] = ws
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, env=env, timeout=30,
    )
    return result.stdout, result.stderr, result.returncode


TEST_SCRIPT = r"""
import os, sys
ws = os.environ["V461_TEST_WS"]
# Set workspace BEFORE import
import sagemaker_agent as sa
sa.CONFIG.workspace = ws
# Rebuild SECURITY with new workspace (auto-detects git repo root)
sa._auto_allowed = sa._auto_detect_allowed_paths(ws, [])
sa.SECURITY = sa.SecurityManager(
    ws,
    allow_interpreters=sa.CONFIG.bash_allow_interpreters,
    allow_docker=sa.CONFIG.bash_allow_docker,
    allowed_paths=sa._auto_allowed,
)

# Check 1: allowed_paths includes repo root
print(f"ALLOWED_PATHS={[str(p) for p in sa.SECURITY.allowed_paths]}")

# Check 2: _build_workspace_info mentions both roots
info = sa._build_workspace_info()
print(f"WS_INFO_LINES={len(info.splitlines())}")
print(f"WS_INFO_HAS_ROOT={'Root:' in info}")
print(f"WS_INFO_HAS_ACCESSIBLE={'Also accessible' in info}")

# Check 3: tool_glob finds the target file with no explicit path
result = sa.tool_glob({"pattern": "**/sagemaker_agent.py"})
print(f"GLOB_RESULT_HAS_FILE={'sagemaker_agent.py' in result and 'No files found' not in result}")
print(f"GLOB_RESULT_HAS_FALLTHROUGH_NOTE={'Searched' in result}")
print("---GLOB_RAW---")
print(result[:500])
print("---END---")

# Check 4: tool_read_file via relative path finds it (uses _resolve_path → allowed_paths)
rf = sa.tool_read_file({"file_path": "wins_docs/compact_v4/sagemaker_agent.py"})
print(f"READ_FOUND={'fake V4 file' in rf}")
print(f"READ_ERROR={'Error' in rf[:20]}")

# Check 5: tool_read_file on nonexistent file returns helpful error
rf_bad = sa.tool_read_file({"file_path": "no_such_dir/nope.py"})
print(f"BAD_READ_HAS_WORKSPACE={'Workspace root:' in rf_bad}")
print(f"BAD_READ_HAS_GLOB_HINT={'glob' in rf_bad.lower()}")

# Check 6: validate_path rejection gives rich error
ok, msg = sa.SECURITY.validate_path("../../../etc/passwd")
print(f"VALIDATE_REJECTED={not ok}")
print(f"VALIDATE_MSG_HAS_WORKSPACE={'Workspace root:' in msg}")
"""


def main():
    with tempfile.TemporaryDirectory() as tmp:
        repo, ws, target = make_fake_repo(tmp)
        print(f"[TEST] Fake repo: {repo}")
        print(f"[TEST] Workspace: {ws}")
        print(f"[TEST] Target:    {target}")
        print()

        stdout, stderr, rc = run_in_subprocess(TEST_SCRIPT, ws)
        if rc != 0:
            print("STDERR:")
            print(stderr)
            print("STDOUT:")
            print(stdout)
            print("FAIL: subprocess crashed")
            sys.exit(1)

        # Parse line-by-line
        lines = {}
        for line in stdout.splitlines():
            if "=" in line and not line.startswith("---"):
                k, _, v = line.partition("=")
                lines[k] = v

        print("--- TEST OUTPUT ---")
        print(stdout)
        print("-------------------")

        checks = {
            "repo root in allowed_paths": "fake_repo" in lines.get("ALLOWED_PATHS", ""),
            "workspace info has Root": lines.get("WS_INFO_HAS_ROOT") == "True",
            "workspace info has Also-accessible": lines.get("WS_INFO_HAS_ACCESSIBLE") == "True",
            "glob found file via fallthrough": lines.get("GLOB_RESULT_HAS_FILE") == "True",
            "glob result notes multi-root search": lines.get("GLOB_RESULT_HAS_FALLTHROUGH_NOTE") == "True",
            "read_file found file via allowed_paths": lines.get("READ_FOUND") == "True",
            "read_file no error on valid path": lines.get("READ_ERROR") == "False",
            "bad read_file mentions workspace": lines.get("BAD_READ_HAS_WORKSPACE") == "True",
            "bad read_file suggests glob": lines.get("BAD_READ_HAS_GLOB_HINT") == "True",
            "validate_path rejects escape": lines.get("VALIDATE_REJECTED") == "True",
            "validate_path error mentions workspace": lines.get("VALIDATE_MSG_HAS_WORKSPACE") == "True",
        }

        all_pass = True
        for name, passed in checks.items():
            mark = "PASS" if passed else "FAIL"
            if not passed:
                all_pass = False
            print(f"  [{mark}] {name}")

        print()
        if all_pass:
            print("ALL CHECKS PASS")
            sys.exit(0)
        else:
            print("SOME CHECKS FAILED")
            sys.exit(1)


if __name__ == "__main__":
    main()
