"""V5 security/manager.py — SecurityManager class + subprocess helpers.

Source: compact_v4/MAIN/agent/sagemaker_agent.py:1298-2148 (SecurityManager
class) + :2107 (`_auto_detect_allowed_paths`) + :4212 (`_resolve_path`) +
:4988-5160 (subprocess helpers `_safe_exec_env`, `_run_subprocess`,
`_validate_shell_redirections`, `_docker_base_cmd`,
`_ensure_docker_image_ready`, `_kill_active_process`).

This is a verbatim port. The only structural changes:
- Constants extracted to `dangerous_patterns.py` + `dangerous_python.py`
  (security audit boundary: regex lists in their own files).
- Imports adjusted for v5 package layout.
- v4 `Truncation` import path now `runtime.truncation` (Phase-5 home).
- v4 `CONFIG` import path now `runtime.config`.

Phase 5 retires the Phase-3 `tools/_path_validation.py` stub: it is
converted to a delegating shim that forwards to this module's
`SECURITY.validate_path`, so the 8 Phase 3-4 tool modules keep their
imports unchanged.
"""
from __future__ import annotations

import logging
import os
import re
import shlex
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .dangerous_patterns import (
    BASE_ALLOWED_COMMANDS,
    CATASTROPHIC_COMPILED,
    CONTAINER_COMMANDS,
    DANGEROUS_PATTERNS,
    INTERPRETER_COMMANDS,
    NETWORK_COMMANDS,
)
from .dangerous_python import (
    ALLOWED_PYTHON_MODULES,
    BLOCKED_PYTHON_MEMBERS,
    BLOCKED_PYTHON_MODULES,
    DANGEROUS_PYTHON,
)


# ============================================================
# Secret detection patterns (used by scan_secrets)
# ============================================================

SECRET_PATTERNS: List[Tuple[str, str]] = [
    # v4 baseline patterns (13)
    (r"(?i)(api[_-]?key|apikey)\s*[=:]\s*[\"']?[\w-]{20,}", "API Key"),
    (r"(?i)(secret|password|passwd|pwd)\s*[=:]\s*[\"']?[^\s\"']{8,}", "Password/Secret"),
    (r"(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*[\"']?[A-Z0-9]{20}", "AWS Access Key"),
    (r"(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*[\"']?[A-Za-z0-9/+=]{40}", "AWS Secret Key"),
    (r"(?i)(bearer\s+)[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+", "JWT Token"),
    (r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Key"),
    (r"(?i)(mongodb|postgres|mysql|redis)://[^\s]+:[^\s]+@", "Database URL"),
    (r"(?i)(gh[ps]_[A-Za-z0-9_]{36,})", "GitHub Token"),
    (r"(?i)(xox[baprs]-[A-Za-z0-9-]+)", "Slack Token"),
    (r"(?i)(gcp[_-]?api[_-]?key)\s*[=:]\s*[\"']?[\w-]{20,}", "GCP API Key"),
    (r"sk-ant-[A-Za-z0-9_\-]{20,}", "Anthropic API Key"),
    (r"AKIA[A-Z0-9]{16}", "AWS Access Key ID (bare)"),
    (r"(?i)(ANTHROPIC_API_KEY)\s*[=:]\s*[\"']?\S+", "Anthropic API Key assignment"),
    # Block C C-2 (R5 A1) — 25 NEW gitleaks patterns ported from
    # Runnable services/teamMemorySync/secretScanner.ts. Total: 38.
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI API Key (sk-)"),
    (r"sk-proj-[A-Za-z0-9_\-]{40,}", "OpenAI Project Key (sk-proj-)"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key (AIza)"),
    (r"ya29\.[0-9A-Za-z\-_]+", "Google OAuth Access Token (ya29)"),
    (r"[a-z0-9]{32}-us[0-9]{1,2}", "Mailchimp API Key"),
    (r"key-[a-zA-Z0-9]{32}", "Mailgun API Key"),
    (r"SK[a-z0-9]{32}", "Twilio Auth Token"),
    (r"AC[a-z0-9]{32}", "Twilio Account SID"),
    (r"sq0atp-[0-9A-Za-z\-_]{22}", "Square OAuth Token"),
    (r"sq0csp-[0-9A-Za-z\-_]{43}", "Square Access Token"),
    (r"access_token,production\$[0-9a-z]{161}[0-9a-f]{32}", "Square OAuth Production Secret"),
    (r"(?i)(stripe[_-]?(api[_-]?)?key)\s*[=:]\s*[\"']?(sk|pk|rk)_(live|test)_[A-Za-z0-9]{24,}", "Stripe API Key"),
    (r"sk_live_[0-9a-zA-Z]{24,}", "Stripe Live Secret Key"),
    (r"rk_live_[0-9a-zA-Z]{24,}", "Stripe Restricted Live Key"),
    (r"pk_live_[0-9a-zA-Z]{24,}", "Stripe Live Publishable Key"),
    (r"glpat-[A-Za-z0-9\-_]{20,}", "GitLab Personal Access Token"),
    (r"npm_[A-Za-z0-9]{36}", "npm Access Token"),
    (r"(?i)hf_[A-Za-z0-9]{32,}", "Hugging Face Token"),
    (r"r8_[A-Za-z0-9]{32,}", "Replicate API Token"),
    (r"pcsk_[A-Za-z0-9_]{20,}", "Pinecone API Key"),
    (r"(?i)x-api-key\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{20,}", "Generic x-api-key header"),
    (r"-----BEGIN PGP PRIVATE KEY BLOCK-----", "PGP Private Key Block"),
    (r"-----BEGIN ENCRYPTED PRIVATE KEY-----", "Encrypted Private Key (PEM)"),
    (r"(?i)heroku[_-]?api[_-]?key\s*[=:]\s*[\"']?[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "Heroku API Key"),
    (r"(?i)cloudflare[_-]?api[_-]?(token|key)\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{30,}", "Cloudflare API Token"),
]


SENSITIVE_FILES = frozenset({
    ".env", ".env.local", ".env.production", ".env.development",
    "credentials.json", "secrets.json", "config.secret.json",
    "id_rsa", "id_ed25519", "id_dsa", "id_ecdsa",
    ".netrc", ".npmrc", ".pypirc",
    "service-account.json", "service_account.json",  # GCP credentials
})


# ============================================================
# Workspace path resolution (v4 _resolve_path verbatim)
# ============================================================

def _resolve_path(raw_path: str) -> str:
    """Resolve a path against CONFIG.workspace if relative. v4 parity."""
    from runtime.config import CONFIG
    if os.path.isabs(raw_path):
        return raw_path
    return os.path.join(CONFIG.workspace, raw_path)


# ============================================================
# SecurityManager class — v4 verbatim port
# ============================================================

class SecurityManager:
    """Security controls: workspace boundary, secret detection, command filtering.

    v4 verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:1298.
    Constants extracted to dangerous_patterns.py + dangerous_python.py for
    auditability; behavior identical.
    """

    SECRET_PATTERNS = SECRET_PATTERNS
    SENSITIVE_FILES = SENSITIVE_FILES
    _CATASTROPHIC_COMPILED = CATASTROPHIC_COMPILED
    DANGEROUS_PATTERNS = DANGEROUS_PATTERNS
    DANGEROUS_PYTHON = DANGEROUS_PYTHON
    BASE_ALLOWED_COMMANDS = BASE_ALLOWED_COMMANDS
    INTERPRETER_COMMANDS = INTERPRETER_COMMANDS
    CONTAINER_COMMANDS = CONTAINER_COMMANDS
    NETWORK_COMMANDS = NETWORK_COMMANDS
    ALLOWED_PYTHON_MODULES = ALLOWED_PYTHON_MODULES
    BLOCKED_PYTHON_MODULES = BLOCKED_PYTHON_MODULES
    BLOCKED_PYTHON_MEMBERS = BLOCKED_PYTHON_MEMBERS

    def __init__(
        self,
        workspace: str,
        allow_network: bool = False,
        allow_interpreters: bool = False,
        allow_docker: bool = False,
        allowed_paths: Optional[list] = None,
    ):
        self.workspace = Path(workspace).resolve()
        self.allow_network = allow_network
        self.allowed_paths: List[Path] = []
        for p in (allowed_paths or []):
            if not p or not p.strip():
                logging.warning("SecurityManager: empty allowed_path — skipped")
                continue
            if not os.path.isabs(p):
                logging.warning(f"SecurityManager: allowed_path '{p}' is not absolute — skipped")
                continue
            try:
                resolved = Path(p).resolve()
                if resolved.is_dir():
                    self.allowed_paths.append(resolved)
                else:
                    logging.warning(f"SecurityManager: allowed_path '{p}' is not a directory — skipped")
            except Exception:
                logging.warning(f"SecurityManager: allowed_path '{p}' is invalid — skipped")
        if self.allowed_paths:
            logging.info(f"SecurityManager: allowed_paths = {[str(p) for p in self.allowed_paths]}")
        self.ALLOWED_COMMANDS = set(self.BASE_ALLOWED_COMMANDS)
        if allow_interpreters:
            self.ALLOWED_COMMANDS.update(self.INTERPRETER_COMMANDS)
        if allow_docker:
            self.ALLOWED_COMMANDS.update(self.CONTAINER_COMMANDS)

    # ------------------------------------------------------------
    # validate_path
    # ------------------------------------------------------------

    def validate_path(self, path: str) -> Tuple[bool, str]:
        """Check if path is within workspace or allowed_paths (read AND write)."""
        try:
            if not os.path.isabs(path):
                resolved = (self.workspace / path).resolve()
            else:
                resolved = Path(path).resolve()

            in_workspace = False
            try:
                resolved.relative_to(self.workspace)
                in_workspace = True
            except ValueError:
                pass

            in_allowed = False
            if not in_workspace:
                for allowed in self.allowed_paths:
                    try:
                        resolved.relative_to(allowed)
                        in_allowed = True
                        break
                    except ValueError:
                        continue

            if not in_workspace and not in_allowed:
                ws_str = str(self.workspace).replace("\\", "/")
                allowed_str = ", ".join(str(p).replace("\\", "/") for p in self.allowed_paths) or "(none)"
                return False, (
                    f"Path outside workspace: {path} (resolved: "
                    f"{str(resolved).replace(chr(92), '/')}). "
                    f"Workspace root: {ws_str}. Allowed roots: {allowed_str}. "
                    f"Use a path under one of those, or run "
                    f"`glob \"**/<filename>\"` to locate the file."
                )

            if resolved.name in self.SENSITIVE_FILES:
                return False, f"Access to sensitive file blocked: {resolved.name}"

            for part in resolved.parts:
                if part.startswith(".env"):
                    return False, "Access to .env file blocked"

            return True, "OK"
        except Exception as e:
            return False, f"Invalid path: {e}"

    # ------------------------------------------------------------
    # validate_command (bash)
    # ------------------------------------------------------------

    def _extract_base_command(self, command: str) -> list:
        """Extract base command names from all shell segments.
        Handles env var prefixes and command chains/pipes (; | && || &)."""
        stripped = command.strip()
        if not stripped:
            return []

        segments = re.split(r'\s*(?:\|\||&&|[|;\n]|(?<![<>])&(?![>]))\s*', stripped)
        bases = []
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            seg = re.sub(r'^(?:\s*[\w.:-]+=\S+\s+)+', '', seg).strip()
            if not seg:
                continue
            try:
                parts = shlex.split(seg)
            except ValueError:
                parts = seg.split()
            if not parts:
                continue
            bases.append(Path(parts[0]).name)
        return bases

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Check if bash command is safe.
        Layer -1: Catastrophic patterns — hard-blocked, cannot be bypassed.
        Layer 0:  Bedrock-only mode — block aws CLI entirely.
        Layer 1:  Allowlist — base command must be in ALLOWED_COMMANDS.
        Layer 2:  Denylist — regex patterns block dangerous arguments.
        Layer 3:  Network commands — block unless allow_network.
        Layer 4:  Workspace boundary check on absolute paths.
        """
        from runtime.config import CONFIG

        # Layer -1: Catastrophic
        for compiled, reason in self._CATASTROPHIC_COMPILED:
            if compiled.search(command):
                return False, f"HARD BLOCKED — {reason}. This operation is permanently disabled."

        # Block C C-11/C-12: consume approval-sensitive cwd command
        # helpers in the runtime validation path instead of leaving them
        # as detection-only helpers.
        try:
            from security.bash_safety import (
                has_cd_git_compound_with_bare_repo,
                has_multiple_cd,
            )
            if has_cd_git_compound_with_bare_repo(command):
                return False, (
                    "cd into a bare Git repository followed by a git command "
                    "requires a separate explicit command; blocked to avoid "
                    "bare-repo fsmonitor side effects."
                )
            if has_multiple_cd(command):
                return False, (
                    "Multiple cd segments require separate explicit commands "
                    "so approval and workspace semantics stay clear."
                )
        except Exception:
            pass

        # Layer 0: Bedrock-only
        if getattr(CONFIG, "aws_bedrock_only", False) and re.search(r'\baws\s', command):
            return False, "AWS CLI blocked (aws_bedrock_only=true). v5 only uses Bedrock via Python SDK."

        # Layer 1: Allowlist
        bases = self._extract_base_command(command)
        if not bases:
            return False, "Empty command — pass a non-empty shell command to bash."
        for base in bases:
            if base not in self.ALLOWED_COMMANDS:
                allowed = sorted(self.ALLOWED_COMMANDS)
                suggestions = [a for a in allowed if a.startswith(base[:3]) and a != base][:5]
                hint = f" Closest allowed: {', '.join(suggestions)}." if suggestions else ""
                return False, (
                    f"Command not allowed: '{base}'.{hint} "
                    f"This SageMaker agent restricts bash to a fixed allowlist for safety. "
                    f"Full allowlist: {', '.join(allowed)}. "
                    f"If you need '{base}', try the Python equivalent (e.g. 'python_exec' tool, "
                    f"or read/write/edit_file for file ops)."
                )

        # Layer 2: Denylist
        for pattern, reason in self.DANGEROUS_PATTERNS:
            try:
                if re.search(pattern, command, re.IGNORECASE):
                    return False, (
                        f"Blocked: {reason}. "
                        f"Pattern matched: /{pattern}/. "
                        f"Rephrase the command to avoid the dangerous pattern, or use a "
                        f"dedicated tool (read_file / edit_file / python_exec) instead of bash."
                    )
            except re.error:
                continue

        # Layer 3: Network commands
        if not self.allow_network:
            for cmd in self.NETWORK_COMMANDS:
                if re.search(rf"\b{cmd}\b", command):
                    return False, f"Network command blocked: {cmd}"

        # Layer 4: Workspace boundary on absolute paths
        workspace = os.path.realpath(CONFIG.workspace)
        workspace_prefix = workspace + os.sep
        _extra_prefixes = []
        for ap in self.allowed_paths:
            rp = os.path.realpath(str(ap))
            _extra_prefixes.append((rp, rp + os.sep))
        for token in re.findall(r'(?:^|\s)(/[^\s;|&>]+)', command):
            real_token = os.path.realpath(token)
            if real_token == workspace or real_token.startswith(workspace_prefix):
                continue
            if real_token.startswith(("/usr/bin/", "/usr/local/bin/", "/bin/", "/opt/", "/tmp/")):
                continue
            if any(real_token == rp or real_token.startswith(rp_sep) for rp, rp_sep in _extra_prefixes):
                continue
            return False, f"Path outside workspace: '{token}'. Use relative paths within {workspace}"

        return True, "OK"

    # ------------------------------------------------------------
    # validate_python (regex denylist + AST allowlist)
    # ------------------------------------------------------------

    def validate_python(self, code: str) -> Tuple[bool, str]:
        """Check if Python code is safe using regex denylist + AST import allowlist."""
        from runtime.config import CONFIG

        # Layer 0: Bedrock-only — block all boto3 clients except bedrock-runtime
        if getattr(CONFIG, "aws_bedrock_only", False):
            boto3_client_match = re.findall(r"\.client\s*\(\s*['\"]([^'\"]+)['\"]", code)
            for svc in boto3_client_match:
                if svc not in ("bedrock-runtime",):
                    return False, f"AWS service '{svc}' blocked (aws_bedrock_only=true). Only bedrock-runtime is allowed."
            if re.search(r"botocore\.session", code):
                return False, "botocore.session blocked (aws_bedrock_only=true). Only bedrock-runtime via boto3 is allowed."
            if re.search(r"getattr\s*\([^,]+,\s*['\"]client['\"]", code):
                return False, "getattr(..., 'client') blocked (aws_bedrock_only=true). Use boto3.client('bedrock-runtime') directly."
            import ast as _ast
            try:
                _tree = _ast.parse(code)
                for _node in _ast.walk(_tree):
                    if isinstance(_node, _ast.Call) and isinstance(_node.func, _ast.Attribute) and _node.func.attr == "client":
                        if _node.args:
                            arg = _node.args[0]
                            if isinstance(arg, _ast.Constant) and arg.value == "bedrock-runtime":
                                continue
                            elif isinstance(arg, _ast.Constant) and isinstance(arg.value, str):
                                return False, f"AWS service '{arg.value}' blocked (aws_bedrock_only=true). Only bedrock-runtime is allowed."
                            else:
                                return False, "Dynamic .client() call blocked (aws_bedrock_only=true). Use boto3.client('bedrock-runtime') with a literal string."
            except SyntaxError:
                pass

        # Layer 1: Regex denylist
        for pattern, reason in self.DANGEROUS_PYTHON:
            try:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    return False, reason
            except re.error:
                continue

        # Layer 2: AST-based import validation (ALLOWLIST)
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return True, "OK"

        alias_to_module: Dict[str, str] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in self.BLOCKED_PYTHON_MODULES or alias.name in self.BLOCKED_PYTHON_MODULES:
                        return False, f"Blocked import: {alias.name}"
                    if mod not in self.ALLOWED_PYTHON_MODULES:
                        return False, f"Import not allowed: {alias.name}. Only approved modules are permitted."
                    alias_to_module[alias.asname or mod] = mod
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module.split(".")[0]
                    if mod in self.BLOCKED_PYTHON_MODULES or node.module in self.BLOCKED_PYTHON_MODULES:
                        return False, f"Blocked import: {node.module}"
                    if mod not in self.ALLOWED_PYTHON_MODULES:
                        return False, f"Import not allowed: {node.module}. Only approved modules are permitted."
                    for alias in node.names:
                        member = alias.name
                        if mod in self.BLOCKED_PYTHON_MEMBERS and member in self.BLOCKED_PYTHON_MEMBERS[mod]:
                            return False, f"Blocked import member: from {node.module} import {member}"
                        alias_to_module[alias.asname or member] = f"{mod}.{member}"

        # Layer 3: AST call validation
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                base_name = node.func.value.id
                resolved = alias_to_module.get(base_name, base_name)
                top = resolved.split(".")[0]
                attr = node.func.attr
                if top in self.BLOCKED_PYTHON_MEMBERS and attr in self.BLOCKED_PYTHON_MEMBERS[top]:
                    return False, f"Blocked call: {top}.{attr}()"
            if isinstance(node.func, ast.Name):
                resolved = alias_to_module.get(node.func.id, "")
                if resolved.startswith("os.") and resolved.split(".", 1)[1] in self.BLOCKED_PYTHON_MEMBERS["os"]:
                    return False, f"Blocked call via imported alias: {resolved}()"

        return True, "OK"

    # ------------------------------------------------------------
    # scan_secrets / truncate_output
    # ------------------------------------------------------------

    def scan_secrets(self, content: str) -> List[Dict]:
        """Scan content for potential secrets. Returns list of {type, count} dicts."""
        findings = []
        for pattern, secret_type in self.SECRET_PATTERNS:
            try:
                matches = re.findall(pattern, content)
                if matches:
                    findings.append({"type": secret_type, "count": len(matches)})
            except re.error:
                continue
        return findings

    def redact_secrets(self, content: str, marker: str = "[REDACTED_SECRET]") -> str:
        """Redact known secret patterns from content."""
        redacted = content
        for pattern, _secret_type in self.SECRET_PATTERNS:
            try:
                redacted = re.sub(pattern, marker, redacted)
            except re.error:
                continue
        return redacted

    def truncate_output(self, output: str, max_size: Optional[int] = None,
                        use_smart: bool = True) -> str:
        """Truncate output using smart truncation (saves full to disk if large)."""
        from runtime.truncation import Truncation
        from runtime.config import CONFIG
        if use_smart:
            truncated, _was_truncated, _saved_path = Truncation.truncate(output)
            return truncated
        max_size = max_size or getattr(CONFIG, "max_output_chars", 50_000)
        if len(output) <= max_size:
            return output
        return output[:max_size] + f"\n[Truncated - {len(output):,} chars total]"


# ============================================================
# Auto-detect allowed paths (v4 verbatim)
# ============================================================

def _auto_detect_allowed_paths(workspace: str, existing_paths: list) -> list:
    """Expand allowed_paths based on environment.
    1. SageMaker: add /home/ec2-user/SageMaker/ or /home/sagemaker-user/.
    2. Git repo: if workspace is a sub-directory, add the repo root."""
    extra = list(existing_paths or [])

    for sm_root in ["/home/ec2-user/SageMaker", "/home/sagemaker-user"]:
        if os.path.isdir(sm_root) and sm_root not in extra:
            extra.append(sm_root)
            logging.info(f"Auto-detected SageMaker environment: {sm_root} (added to allowed_paths)")
            break

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, cwd=workspace,
        )
        if result.returncode == 0:
            repo_root = os.path.realpath(result.stdout.strip())
            ws_resolved = os.path.realpath(workspace)
            if ws_resolved.startswith(repo_root + os.sep) and repo_root not in extra:
                extra.append(repo_root)
                logging.info(f"Auto-detected git repo root: {repo_root} (added to allowed_paths)")
    except Exception:
        pass

    return extra


# ============================================================
# Subprocess helpers (v4 verbatim — used by bash + python_exec tools)
# ============================================================

# Active subprocess tracking — Stop button kills running processes.
_active_process: Optional[subprocess.Popen] = None
_active_process_lock = threading.Lock()
_docker_image_ready = False
_docker_image_lock = threading.Lock()


def kill_active_process() -> None:
    """Kill the active subprocess if one is running. Called by stop handler."""
    global _active_process
    with _active_process_lock:
        if _active_process and _active_process.poll() is None:
            try:
                _active_process.kill()
            except OSError:
                pass


def safe_exec_env() -> Dict[str, str]:
    """Build a minimally-sensitive environment for local execution."""
    blocked_markers = (
        "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL",
        "API_KEY", "PRIVATE_KEY", "AUTH",
    )
    env = {
        k: v for k, v in os.environ.items()
        if not any(s in k.upper() for s in blocked_markers)
        and k.upper() not in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN")
    }
    env["TERM"] = "dumb"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_subprocess(cmd_arg, timeout: int, shell: bool, cwd: str,
                   env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    """Run subprocess with active-process tracking for Stop support."""
    global _active_process
    proc = subprocess.Popen(
        cmd_arg,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
        env=env,
    )
    with _active_process_lock:
        _active_process = proc
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    finally:
        with _active_process_lock:
            _active_process = None
    return subprocess.CompletedProcess(cmd_arg, proc.returncode, stdout, stderr)


def validate_shell_redirections(command: str) -> Tuple[bool, str]:
    """Validate shell redirection targets stay inside workspace."""
    try:
        tokens = shlex.split(command, posix=(os.name != "nt"))
    except ValueError:
        return False, "invalid shell syntax for redirection validation"

    redir_ops = {">", ">>", "<", "1>", "1>>", "2>", "2>>", "&>", "&>>"}
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        target: Optional[str] = None

        if re.match(r"^\d*(?:<|>)&\d+$", token):
            idx += 1
            continue
        if token in {"<<", "<<-"}:
            if idx + 1 >= len(tokens):
                return False, "heredoc missing marker"
            idx += 2
            continue
        if token.startswith("<<"):
            idx += 1
            continue

        if token in redir_ops:
            if idx + 1 >= len(tokens):
                return False, "redirection missing target"
            target = tokens[idx + 1]
            idx += 2
        else:
            m = re.match(r"^(?:\d*>>?|\d*<<?|&>>?)(.+)$", token)
            if m:
                target = m.group(1).strip()
            idx += 1

        if not target:
            continue
        if target in {"/dev/null", "/dev/stdout", "/dev/stderr"}:
            continue
        if any(sym in target for sym in ["$", "*", "?", "~"]):
            return False, f"dynamic redirection target not allowed: {target}"

        ok, msg = SECURITY.validate_path(target)
        if not ok:
            return False, f"redirection target blocked: {msg}"

    return True, "OK"


def docker_base_cmd() -> List[str]:
    """Build hardened docker run args for isolated command execution."""
    from runtime.config import CONFIG
    if not shutil.which("docker"):
        raise RuntimeError("Docker runtime requested but 'docker' is not available")

    cmd = [
        "docker", "run", "--rm",
        "--workdir", "/workspace",
        "--volume", f"{CONFIG.workspace}:/workspace",
        "--user", "65534:65534",
        "--cpus", str(CONFIG.exec_docker_cpus),
        "--memory", str(CONFIG.exec_docker_memory),
        "--pids-limit", str(CONFIG.exec_docker_pids_limit),
    ]
    if CONFIG.exec_docker_network_disabled:
        cmd.extend(["--network", "none"])
    if CONFIG.exec_docker_readonly_rootfs:
        cmd.append("--read-only")
    return cmd


def ensure_docker_image_ready() -> None:
    """Ensure docker image exists locally so first pull doesn't count against exec budget."""
    global _docker_image_ready
    from runtime.config import CONFIG
    if CONFIG.execution_mode != "docker":
        return
    if _docker_image_ready:
        return
    with _docker_image_lock:
        if _docker_image_ready:
            return
        inspect_cmd = ["docker", "image", "inspect", CONFIG.exec_docker_image]
        inspect = run_subprocess(inspect_cmd, timeout=20, shell=False,
                                 cwd=CONFIG.workspace, env=safe_exec_env())
        if inspect.returncode != 0:
            pull_cmd = ["docker", "pull", CONFIG.exec_docker_image]
            pull = run_subprocess(pull_cmd, timeout=240, shell=False,
                                  cwd=CONFIG.workspace, env=safe_exec_env())
            if pull.returncode != 0:
                err = (pull.stderr or pull.stdout or "docker pull failed").strip()
                raise RuntimeError(f"Docker image unavailable: {err[:200]}")
        _docker_image_ready = True


# ============================================================
# Module-level singleton (v4 SECURITY pattern)
# ============================================================

def _build_singleton() -> SecurityManager:
    """Build the SECURITY singleton with auto-detected allowed_paths."""
    from runtime.config import CONFIG
    auto_allowed = _auto_detect_allowed_paths(CONFIG.workspace, CONFIG.allowed_paths or [])
    return SecurityManager(
        CONFIG.workspace,
        allow_interpreters=getattr(CONFIG, "bash_allow_interpreters", False),
        allow_docker=getattr(CONFIG, "bash_allow_docker", False),
        allowed_paths=auto_allowed,
    )


SECURITY = _build_singleton()


def rebuild_singleton_for_tests() -> SecurityManager:
    """Rebuild the SECURITY singleton — tests use this after monkeypatching CONFIG."""
    global SECURITY
    SECURITY = _build_singleton()
    return SECURITY


# ============================================================
# Module-level conveniences (preserve v4 import shapes)
# ============================================================

def validate_path(path: str) -> Tuple[bool, str]:
    """Module-level convenience that delegates to SECURITY.validate_path.
    Used by `tools/_path_validation.py` shim and direct callers."""
    return SECURITY.validate_path(path)


def resolve_path(path: str) -> str:
    """Module-level convenience that delegates to `_resolve_path`.
    Used by `tools/_path_validation.py` shim."""
    return _resolve_path(path)
