"""Phase 5 python_exec tool — verbatim port from v4. NO Runnable analog.

Per ADR-011:
- Executor body is a verbatim port of v4 `tool_python_exec` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:5409` + the closure-based
  runtime sandbox preamble at `:5293`.
- Runnable does NOT have a dedicated python_exec tool — Runnable tells
  the model to use Bash for Python. v5/v4 keep a dedicated tool because:
  (a) plan-mode forbids bash but should still allow safe python execution,
  (b) the closure-based runtime sandbox (allowlist import hook + workspace-
  scoped open() / os.open() / io.open() + os.remove block) is significantly
  more restrictive than spawning a generic python subprocess via shell,
  (c) `python_exec` runs in a temp file with `-I` (isolated mode) so site
  imports don't leak the user's pip cache.

NO PORT_LOG row — pure v4 reuse, no Runnable adoption. Documented inline
in this module + ADR-011.
"""
from __future__ import annotations

import os
import sys
import tempfile
from typing import Any, Dict, Optional

from .registry import build_tool, register
# Codex Phase-05 review finding 1: see tools/bash.py for rationale —
# import the security.manager MODULE, not the SECURITY singleton.
# Dereference `_security_manager.SECURITY` inside the executor so
# rebuild_singleton_for_tests() picks up cleanly.
from security import manager as _security_manager
from security.manager import (
    docker_base_cmd,
    run_subprocess,
    safe_exec_env,
)
from security.diagnostics import (
    python_exec_runtime_diagnosis,
    python_exec_security_block_diagnosis,
)


_DESCRIPTION = """Execute Python code in a sandboxed subprocess.

Usage:
- The agent runs a fresh subprocess for each call, with `-I` (isolated mode) so site-packages don't leak.
- A closure-based runtime sandbox is injected as a preamble: import allowlist (math, json, re, pathlib, numpy, pandas, sklearn, matplotlib, boto3 [bedrock-runtime only], etc. — see security/dangerous_python.py for the full list), `open()` workspace boundary, `os.remove`/`os.unlink`/`os.rmdir` blocked outside workspace, `os.posix_spawn` blocked.
- `subprocess`, `socket`, `requests`, `urllib`, `pickle`, `multiprocessing`, `signal`, `ctypes` are all BLOCKED at import time.
- `boto3` is allowed but destructive operations (`delete_*`, `terminate_instances`, `delete_stack`, IAM/STS/KMS clients) are blocked by regex denylist. When `aws_bedrock_only=true`, only `boto3.client('bedrock-runtime')` is allowed.
- Default timeout 60s, max 300s.
- Output is captured (stdout + stderr); large outputs are smart-truncated.
- Approval is required before any code runs.

WHEN to use:
- Data processing / analysis (numpy, pandas, sklearn, matplotlib)
- AWS Bedrock model calls (`boto3.client('bedrock-runtime')`)
- Local file processing inside the workspace
- Any logic that doesn't fit a one-liner shell command

WHEN NOT to use:
- Reading a file → use read_file
- Editing a file → use edit_file
- Searching content → use grep
- Running tests → use bash with pytest (pytest output is more legible than capturing through python_exec)
- Network requests → BLOCKED. v5 has no GitHub network at runtime."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": "Python source code to execute.",
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds. Default 60, max 300.",
        },
    },
    "required": ["code"],
}


# ============================================================
# Closure-based runtime sandbox preamble (v4 verbatim from :5293)
# ============================================================

def _build_python_preamble() -> str:
    """Build runtime sandbox preamble injected into every python_exec script.

    Uses closures so sandbox internals are not accessible to user code.
    Verbatim port of v4 `_build_python_preamble`.
    """
    from runtime.config import CONFIG
    workspace = os.path.realpath(CONFIG.workspace)
    _extra_paths = [os.path.realpath(str(p)) for p in _security_manager.SECURITY.allowed_paths]
    extra_paths_repr = repr(tuple(_extra_paths))
    return f'''
# === RUNTIME SANDBOX (closure-based, not accessible to user code) ===
def _install_sandbox():
    import builtins as _b, os as _os

    # --- 1. Import hook (allowlist) ---
    _orig_import = _b.__import__
    _ALLOWED = {{
        "math", "statistics", "decimal", "fractions", "random", "string",
        "re", "json", "csv", "collections", "itertools", "functools",
        "datetime", "time", "calendar", "textwrap", "pprint",
        "pathlib", "io", "struct", "base64", "hashlib", "hmac",
        "copy", "typing", "dataclasses", "enum", "abc",
        "operator", "bisect", "heapq", "array",
        "difflib", "unicodedata", "html", "xml",
        "os", "glob", "fnmatch", "shutil",
        "numpy", "pandas", "scipy", "sklearn",
        "matplotlib", "seaborn", "plotly", "altair",
        "openpyxl", "xlsxwriter", "docx",
        "PIL", "reportlab", "fpdf",
        "boto3", "botocore",
        "tabulate", "yaml", "toml", "configparser",
        "logging", "warnings", "traceback", "inspect",
        "argparse", "numbers", "contextlib",
        "builtins", "_thread", "_io", "_collections", "_collections_abc",
        "_operator",
        "encodings", "codecs", "_codecs", "_signal", "_abc",
        "_stat", "_weakref", "_functools", "_locale",
        "posixpath", "ntpath", "genericpath", "stat",
        "sys", "types", "zipimport", "_frozen_importlib",
        "_frozen_importlib_external", "_bootlocale", "copyreg",
        "_json", "_csv", "_datetime", "_struct", "_decimal", "_random",
        "_hashlib", "_bisect", "_heapq", "_statistics",
        "_sre", "sre_compile", "sre_parse", "sre_constants", "_string",
        # Python 3.11 transitive imports observed during Phase 05 testing:
        "keyword", "reprlib", "_pyio", "_compat_pickle", "_warnings",
    }}
    def _safe_import(name, *args, **kwargs):
        level = args[3] if len(args) > 3 else kwargs.get("level", 0)
        if level > 0:
            return _orig_import(name, *args, **kwargs)
        top = name.split(".")[0]
        if top in _ALLOWED:
            return _orig_import(name, *args, **kwargs)
        raise ImportError(f"Security: import '{{name}}' is not in the allowed modules list")
    _b.__import__ = _safe_import

    # --- 2. Workspace boundary for open() (runtime, not regex) ---
    _WORKSPACE = {repr(workspace)}
    _WORKSPACE_SEP = _WORKSPACE + _os.sep  # Prevent sibling-dir bypass
    _orig_open = _b.open
    _EXTRA_PATHS = {extra_paths_repr}
    _EXTRA_PREFIXES = tuple(p + _os.sep for p in _EXTRA_PATHS)
    _SAFE_READ_PREFIXES = (_WORKSPACE_SEP, "/tmp/") + _EXTRA_PREFIXES
    _SAFE_WRITE_PREFIXES = (_WORKSPACE_SEP,) + _EXTRA_PREFIXES
    _SAFE_READ_EXACT = (_WORKSPACE, "/tmp") + _EXTRA_PATHS
    _SAFE_WRITE_EXACT = (_WORKSPACE,) + _EXTRA_PATHS
    def _safe_open(file, mode="r", *args, **kwargs):
        if isinstance(file, (str, _os.PathLike)):
            real = _os.path.realpath(str(file))
            is_write = any(c in str(mode) for c in "wxa+")
            prefixes = _SAFE_WRITE_PREFIXES if is_write else _SAFE_READ_PREFIXES
            exact = _SAFE_WRITE_EXACT if is_write else _SAFE_READ_EXACT
            if not (real in exact or any(real.startswith(p) for p in prefixes)):
                raise PermissionError(f"Security: cannot {{'write' if is_write else 'read'}} outside workspace: {{real}}")
        return _orig_open(file, mode, *args, **kwargs)
    _b.open = _safe_open

    # --- 2b. Wrap os.open (low-level fd-based) ---
    _orig_os_open = _os.open
    def _safe_os_open(path, flags, *args, **kwargs):
        real = _os.path.realpath(str(path))
        is_write = bool(flags & (_os.O_WRONLY | _os.O_RDWR | _os.O_CREAT | _os.O_TRUNC | _os.O_APPEND))
        prefixes = _SAFE_WRITE_PREFIXES if is_write else _SAFE_READ_PREFIXES
        exact = _SAFE_WRITE_EXACT if is_write else _SAFE_READ_EXACT
        if not (real in exact or any(real.startswith(p) for p in prefixes)):
            raise PermissionError(f"Security: os.open blocked outside workspace: {{real}}")
        return _orig_os_open(path, flags, *args, **kwargs)
    _os.open = _safe_os_open

    # --- 2c. Wrap io.open ---
    import io as _io
    _io.open = _safe_open

    # --- 3. Block os.remove/unlink/rmdir outside workspace ---
    for _fn_name in ("remove", "unlink", "rmdir"):
        _orig_fn = getattr(_os, _fn_name, None)
        if _orig_fn:
            def _make_safe(orig, name):
                def _safe(path, *a, **kw):
                    real = _os.path.realpath(str(path))
                    if not (real == _WORKSPACE or real.startswith(_WORKSPACE_SEP)):
                        raise PermissionError(f"Security: {{name}}() blocked outside workspace: {{real}}")
                    return orig(path, *a, **kw)
                return _safe
            setattr(_os, _fn_name, _make_safe(_orig_fn, _fn_name))

    # --- 4. Block os.posix_spawn ---
    for _sp in ("posix_spawn", "posix_spawnp"):
        if hasattr(_os, _sp):
            def _blocked_spawn(*a, **kw):
                raise PermissionError(f"Security: os.posix_spawn blocked (use bash tool instead)")
            setattr(_os, _sp, _blocked_spawn)

_install_sandbox()
del _install_sandbox
'''


def _python_exec_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Phase-5 python_exec executor — verbatim port of v4 `tool_python_exec`.

    Sequence:
      1. SECURITY.validate_python(code) — regex denylist + AST allowlist.
      2. Build the closure-based runtime sandbox preamble.
      3. Write preamble + code to a temp file inside CONFIG.workspace.
      4. Run subprocess with `python -I <tempfile>` (isolated mode).
      5. If execution_mode='docker', wrap in docker_base_cmd().
      6. Capture stdout + stderr; smart-truncate; return.
      7. Always unlink the temp file in `finally`.
    """
    import subprocess as _subprocess
    from runtime.config import CONFIG

    code = args.get("code")
    if not isinstance(code, str) or not code:
        return "Error: code is required and must be a non-empty string"

    abort_event = _combined_abort_event(context)
    if abort_event is not None and abort_event.is_set():
        return "Error: execution aborted before start"

    raw_timeout = args.get("timeout", 60)
    try:
        timeout = int(raw_timeout)
    except (TypeError, ValueError):
        return f"Error: timeout must be an integer; got {raw_timeout!r}"
    timeout = min(max(timeout, 1), 300)

    ok, msg = _security_manager.SECURITY.validate_python(code)
    if not ok:
        diagnosis = python_exec_security_block_diagnosis(
            msg, aws_bedrock_only=CONFIG.aws_bedrock_only
        )
        if diagnosis:
            return f"Security blocked: {msg}\n[diagnosis]\n{diagnosis}"
        return f"Security blocked: {msg}"

    # Build preamble at call time (captures current CONFIG state).
    preamble = _build_python_preamble()

    workspace = _current_workspace()
    fd, temp_path = tempfile.mkstemp(suffix=".py", prefix="agent_exec_", dir=workspace)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(preamble)
            f.write(code)

        if CONFIG.execution_mode == "docker":
            from security.manager import ensure_docker_image_ready
            ensure_docker_image_ready()
            rel = os.path.relpath(temp_path, workspace).replace("\\", "/")
            docker_cmd = docker_base_cmd()
            docker_cmd.extend([CONFIG.exec_docker_image, "python", "-I", f"/workspace/{rel}"])
            result = run_subprocess(
                docker_cmd, timeout=timeout, shell=False,
                cwd=workspace, env=safe_exec_env(),
            )
        else:
            result = run_subprocess(
                [sys.executable, "-I", temp_path],
                timeout=timeout, shell=False,
                cwd=workspace, env=safe_exec_env(),
            )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        diagnosis = python_exec_runtime_diagnosis(
            output, aws_bedrock_only=CONFIG.aws_bedrock_only
        )
        if diagnosis:
            output += f"\n[diagnosis]\n{diagnosis}"
        return _security_manager.SECURITY.truncate_output(output) if output else "(no output)"
    except _subprocess.TimeoutExpired:
        return f"Error: code timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def _register():
    """Idempotent registration of python_exec."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "python_exec") is not None:
        return find_tool_by_name(all_registered(), "python_exec")
    return register(build_tool(
        name="python_exec",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_python_exec_executor,
        is_read_only=False,
        is_destructive=True,         # Can mutate filesystem inside workspace
        is_concurrency_safe=False,
        requires_approval=True,      # HIGH_RISK_TOOLS membership
        search_hint="execute python sandboxed",
    ))


def _current_workspace() -> str:
    from runtime.config import CONFIG
    from runtime.execution_context import current_cwd
    return current_cwd(CONFIG.workspace) or CONFIG.workspace


def _combined_abort_event(context: Optional[Dict[str, Any]]) -> Optional[Any]:
    if not isinstance(context, dict):
        return None
    events = []
    event = context.get("abort_event")
    if event is not None:
        events.append(event)
    extra = context.get("abort_events")
    if isinstance(extra, (list, tuple)):
        events.extend(e for e in extra if e is not None)
    if not events:
        return None
    from runtime.execution_context import combined_abort_signal
    return combined_abort_signal(*events)
