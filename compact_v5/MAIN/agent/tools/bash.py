"""Phase 5 bash tool — REUSE v4 executor + ADAPT Runnable prompt text.

Per ADR-011:
- Executor body is a verbatim port of v4 `tool_bash` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:5239`. Allowlist + denylist +
  workspace-boundary checks all delegate to the Phase 5 `SECURITY`
  singleton in `security.manager`.
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/BashTool/prompt.ts`. v5 drops the
  ~300 lines of Runnable-specific content (undercover instructions, gh
  attribution, background-task notes, sandbox manager refs, multi-USER_TYPE
  branches) — those are inapplicable to the Bedrock + .ipynb runtime.
  v5 keeps the core: "use this for shell commands; don't pipe to shell;
  prefer dedicated tools where possible".

PORT_LOG: row #010 (Runnable BashTool/prompt.ts → tools/bash.py).

PS Issue mapping addressed:
- Issue #6 (wiring-bug pattern): description does NOT promise features
  the executor doesn't implement (no `run_in_background`, no `sandbox`,
  no Runnable-only flags).
- Issue #7 (buried matrix): description ends with explicit WHEN/WHEN NOT
  triage section.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .registry import build_tool, register
# Codex Phase-05 review finding 1: import the security.manager MODULE,
# not the SECURITY value. `from security.manager import SECURITY` would
# bind a one-shot snapshot at import time; `rebuild_singleton_for_tests()`
# would then leave this executor referencing the old singleton. We
# dereference `_security_manager.SECURITY` inside the executor function
# so the lookup happens at call time.
from security import manager as _security_manager
from security.manager import (
    docker_base_cmd,
    run_subprocess,
    safe_exec_env,
    validate_shell_redirections,
)


_DESCRIPTION = """Execute a shell command with allowlist enforcement.

Usage:
- The agent executes commands through a fixed allowlist (`git`, `ls`, `cat`, `grep`, `pip`, `pytest`, etc.). Anything outside the allowlist is blocked with a hint about the closest allowed alternative.
- A regex denylist additionally blocks dangerous arguments (recursive rm, sudo, AWS CLI, GitHub publishing, cloud CLIs, fork bombs, obfuscated payloads, etc.) — see security/dangerous_patterns.py for the full list.
- Workspace boundary: any absolute path mentioned in the command must be inside CONFIG.workspace or one of CONFIG.allowed_paths. /tmp/, /usr/bin/, /usr/local/bin/, /bin/, /opt/ are allowed.
- `python_exec` is the canonical Python execution tool — DO NOT use `python -c` via bash (the denylist blocks it explicitly).
- Output is captured (stdout + stderr); large outputs are smart-truncated (head 100 + tail 50 lines).
- Default timeout 120s, max 600s.
- Approval is required before any command runs.

WHEN to use:
- Running git operations (status / log / diff / commit / branch — local only; push/pull/fetch/clone are blocked in SageMaker)
- Running pytest, jest, mocha, cargo (testing)
- Running pip / conda / npm / yarn / pnpm / bun (package management — install OK, uninstall requires extra approval)
- Running build tools (make / cmake / gcc / g++ / clang)
- File operations the dedicated tools don't cover (tar, zip/unzip, du, df, stat)

WHEN NOT to use:
- Reading a file → use read_file (better output formatting + cache)
- Editing a file → use edit_file (exact-string replacement, atomic, with diff preview)
- Searching content → use grep (built-in, no `grep` allowlist surprises)
- Listing a directory → use list_dir (works in plan mode, where bash is forbidden)
- Running Python code → use python_exec (sandboxed, allowlist of imports)
- Network downloads piped to shell (e.g. `curl ... | sh`) — HARD BLOCKED, no exceptions"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "Shell command to execute. Must use only allowlisted base commands.",
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds. Default 120, max 600.",
        },
    },
    "required": ["command"],
}


def _bash_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Phase-5 bash executor — verbatim port of v4 `tool_bash`.

    The executor sequence:
      1. Validate command via SECURITY.validate_command (catastrophic /
         allowlist / denylist / network / workspace-boundary).
      2. Build subprocess args; if local mode and the command uses shell
         operators (|, >, <, ;, &&, ||, `, $()), validate redirection
         targets stay inside workspace, then run with shell=True. Otherwise
         shlex.split + shell=False.
      3. If execution_mode='docker', wrap in docker_base_cmd().
      4. Run with safe_exec_env() (env vars stripped of credentials).
      5. Smart-truncate output (head 100 / tail 50 lines).
      6. Return string suitable for tool_result wrapping.
    """
    import subprocess as _subprocess
    from runtime.config import CONFIG
    from runtime.truncation import Truncation

    command = args.get("command")
    if not isinstance(command, str) or not command:
        return "Error: command is required and must be a non-empty string"

    raw_timeout = args.get("timeout", 120)
    try:
        timeout = int(raw_timeout)
    except (TypeError, ValueError):
        return f"Error: timeout must be an integer; got {raw_timeout!r}"
    timeout = min(max(timeout, 1), 600)

    ok, msg = _security_manager.SECURITY.validate_command(command)
    if not ok:
        return f"Blocked: {msg}"

    try:
        if CONFIG.execution_mode == "docker":
            from security.manager import ensure_docker_image_ready
            ensure_docker_image_ready()
            docker_cmd = docker_base_cmd()
            docker_cmd.extend([CONFIG.exec_docker_image, "sh", "-lc", command])
            result = run_subprocess(
                docker_cmd, timeout=timeout, shell=False,
                cwd=CONFIG.workspace, env=safe_exec_env(),
            )
        else:
            needs_shell = bool(re.search(r"[|><;]|&&|\|\||`|\$\(", command))
            if needs_shell:
                redir_ok, redir_msg = validate_shell_redirections(command)
                if not redir_ok:
                    return f"Blocked: {redir_msg}"
                cmd_arg = command
                use_shell = True
            else:
                import shlex as _shlex
                try:
                    cmd_arg = _shlex.split(command)
                except ValueError:
                    cmd_arg = command.split()
                use_shell = False
            result = run_subprocess(
                cmd_arg, timeout=timeout, shell=use_shell,
                cwd=CONFIG.workspace, env=safe_exec_env(),
            )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"

        if not output:
            return "(no output)"

        truncated, _was_truncated = Truncation.smart_truncate(
            output, head_lines=100, tail_lines=50,
        )
        return _security_manager.SECURITY.truncate_output(truncated)
    except _subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def _register():
    """Idempotent registration of bash."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "bash") is not None:
        return find_tool_by_name(all_registered(), "bash")
    return register(build_tool(
        name="bash",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_bash_executor,
        is_read_only=False,
        is_destructive=True,         # Can mutate filesystem / system state
        is_concurrency_safe=False,   # Two bashes against same workspace race
        requires_approval=True,      # HIGH_RISK_TOOLS membership
        search_hint="execute shell command allowlist",
    ))
