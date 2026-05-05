"""SOFTWARE-SHELL process lifecycle tests."""
from __future__ import annotations

import os
import sys
import time


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_foreground_timeout_kills_child_process_tree(tmp_path):
    import subprocess
    from security.manager import run_subprocess, safe_exec_env

    sentinel = tmp_path / "survived.txt"
    child = tmp_path / "child.py"
    child.write_text(
        "import pathlib, sys, time\n"
        "time.sleep(2)\n"
        "pathlib.Path(sys.argv[1]).write_text('survived', encoding='utf-8')\n",
        encoding="utf-8",
    )
    parent_code = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, {str(child)!r}, {str(sentinel)!r}])\n"
        "time.sleep(10)\n"
    )

    try:
        run_subprocess(
            [sys.executable, "-c", parent_code],
            timeout=1,
            shell=False,
            cwd=str(tmp_path),
            env=safe_exec_env(),
        )
        raise AssertionError("expected timeout")
    except subprocess.TimeoutExpired:
        pass

    time.sleep(3)
    assert not sentinel.exists(), "child process survived timeout kill"


def test_background_shell_job_start_poll_wait_kill(tmp_path, monkeypatch):
    from runtime.config import CONFIG
    from runtime.shell_jobs import ShellJobManager

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    manager = ShellJobManager(workspace=str(tmp_path))
    code = "import time; print('job-start', flush=True); time.sleep(10)"
    status = manager.start(
        [sys.executable, "-c", code],
        shell=False,
        cwd=str(tmp_path),
        env={"PYTHONIOENCODING": "utf-8"},
        command="python sleep job",
    )
    assert status["status"] in {"running", "finished"}
    job_id = status["id"]

    polled = manager.status(job_id)
    assert polled["id"] == job_id
    assert "job-start" in polled["stdout_tail"] or polled["status"] == "running"

    waited = manager.wait(job_id, timeout=0.1)
    assert waited["id"] == job_id

    killed = manager.kill(job_id)
    assert killed["status"] in {"killed", "finished"}
    assert (tmp_path / ".sageagent_state" / "shell_jobs" / "index.json").is_file()
