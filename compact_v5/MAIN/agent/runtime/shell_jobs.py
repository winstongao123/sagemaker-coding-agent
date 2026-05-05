"""Managed background shell jobs for SOFTWARE-SHELL."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


def _kill_process_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            import signal
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except OSError:
            pass


class ShellJobManager:
    def __init__(self, workspace: Optional[str] = None, config: Any = None):
        self._workspace_override = workspace
        self._config_override = config
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._load_index()

    @property
    def _config(self):
        if self._config_override is not None:
            return self._config_override
        from runtime.config import CONFIG as _CFG
        return _CFG

    @property
    def workspace(self) -> Path:
        root = self._workspace_override or getattr(self._config, "workspace", os.getcwd())
        return Path(root).resolve()

    @property
    def jobs_dir(self) -> Path:
        return self.workspace / ".sageagent_state" / "shell_jobs"

    @property
    def index_path(self) -> Path:
        return self.jobs_dir / "index.json"

    def _load_index(self) -> None:
        if not self.index_path.is_file():
            return
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return
        jobs = data.get("jobs", {})
        if isinstance(jobs, dict):
            for job_id, meta in jobs.items():
                if isinstance(meta, dict):
                    item = dict(meta)
                    item["proc"] = None
                    item["status"] = "unknown_after_restart"
                    self._jobs[str(job_id)] = item

    def _persist(self) -> None:
        if getattr(self._config, "disable_local_traces", False):
            return
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        jobs = {}
        for job_id, meta in self._jobs.items():
            item = {k: v for k, v in meta.items() if k != "proc"}
            jobs[job_id] = item
        payload = {"schema": "sageagent.shell_jobs.v1", "updated_at": time.time(), "jobs": jobs}
        fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=str(self.jobs_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
                f.write("\n")
            os.replace(tmp, self.index_path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def start(self, cmd_arg: Any, *, shell: bool, cwd: str, env: Dict[str, str], command: str) -> Dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = self.jobs_dir / f"{job_id}.out.log"
        stderr_path = self.jobs_dir / f"{job_id}.err.log"
        out = stdout_path.open("w", encoding="utf-8")
        err = stderr_path.open("w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                cmd_arg,
                shell=shell,
                stdout=out,
                stderr=err,
                text=True,
                cwd=cwd,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                start_new_session=(os.name != "nt"),
            )
        finally:
            # The child inherits the OS handles; closing Python file objects in
            # the parent avoids descriptor leaks while the child keeps logging.
            out.close()
            err.close()
        meta = {
            "id": job_id,
            "command": command,
            "pid": proc.pid,
            "status": "running",
            "started_at": time.time(),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "returncode": None,
            "proc": proc,
        }
        self._jobs[job_id] = meta
        self._persist()
        return self.status(job_id, tail_chars=2000)

    def status(self, job_id: str, tail_chars: int = 4000) -> Dict[str, Any]:
        meta = self._jobs.get(job_id)
        if not meta:
            return {"id": job_id, "status": "not_found"}
        proc = meta.get("proc")
        if proc is not None:
            rc = proc.poll()
            if rc is None:
                meta["status"] = "running"
            else:
                meta["status"] = "finished"
                meta["returncode"] = rc
                meta["finished_at"] = meta.get("finished_at") or time.time()
        self._persist()
        item = {k: v for k, v in meta.items() if k != "proc"}
        item["stdout_tail"] = self._tail(meta.get("stdout_path"), tail_chars)
        item["stderr_tail"] = self._tail(meta.get("stderr_path"), tail_chars)
        return item

    def wait(self, job_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        meta = self._jobs.get(job_id)
        if not meta:
            return {"id": job_id, "status": "not_found"}
        proc = meta.get("proc")
        if proc is None:
            return self.status(job_id)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return self.status(job_id)
        return self.status(job_id)

    def kill(self, job_id: str) -> Dict[str, Any]:
        meta = self._jobs.get(job_id)
        if not meta:
            return {"id": job_id, "status": "not_found"}
        proc = meta.get("proc")
        if proc is None:
            meta["status"] = "unknown_after_restart"
            meta["kill_note"] = "no live process handle is available after restart"
            return self.status(job_id)
        if proc is not None:
            _kill_process_tree(proc)
        meta["status"] = "killed"
        meta["finished_at"] = time.time()
        return self.status(job_id)

    @staticmethod
    def _tail(path: Optional[str], chars: int) -> str:
        if not path or not os.path.isfile(path):
            return ""
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return text[-chars:]


SHELL_JOBS = ShellJobManager()


__all__ = ["ShellJobManager", "SHELL_JOBS"]
