"""
Security Manager - CRITICAL SECURITY MODULE

Enforces:
- Workspace boundary (path traversal prevention)
- Secret detection (API keys, passwords, credentials)
- Command validation (dangerous command blocking)
- Output truncation (token explosion prevention)
"""
import os
import re
import hashlib
from pathlib import Path
from typing import Set, Optional, Tuple, List, Dict
from dataclasses import dataclass, field


@dataclass
class SecurityConfig:
    """Security configuration."""

    # Workspace boundary
    workspace_root: str
    allowed_paths: Set[str] = field(default_factory=set)

    # File limits
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_output_size: int = 50 * 1024  # 50KB

    # Timeout limits
    default_timeout: int = 120  # seconds
    max_timeout: int = 600  # 10 minutes

    # Network
    allow_network: bool = False


class SecurityManager:
    """Enforces security boundaries for the agent."""

    # Patterns for secret detection (10 patterns)
    SECRET_PATTERNS = [
        (r"(?i)(api[_-]?key|apikey)\s*[=:]\s*[\"']?[\w-]{20,}", "API Key"),
        (r"(?i)(secret|password|passwd|pwd)\s*[=:]\s*[\"']?[^\s\"']{8,}", "Password/Secret"),
        (r"(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*[\"']?[A-Z0-9]{20}", "AWS Access Key"),
        (r"(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*[\"']?[A-Za-z0-9/+=]{40}", "AWS Secret Key"),
        (r"(?i)(bearer\s+)[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+", "JWT Token"),
        (r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Key"),
        (r"(?i)(mongodb|postgres|mysql|redis)://[^\s]+:[^\s]+@", "Database Connection String"),
        (r"(?i)(gh[ps]_[A-Za-z0-9_]{36,})", "GitHub Token"),
        (r"(?i)(xox[baprs]-[A-Za-z0-9-]+)", "Slack Token"),
        (r"(?i)(gcp[_-]?api[_-]?key)\s*[=:]\s*[\"']?[\w-]{20,}", "GCP API Key"),
    ]

    # Dangerous file patterns
    SENSITIVE_FILES = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "credentials.json",
        "secrets.json",
        "config.secret.json",
        "id_rsa",
        "id_ed25519",
        "id_dsa",
        "id_ecdsa",
        ".aws/credentials",
        ".ssh/config",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "service-account.json",  # GCP credentials
        "service_account.json",  # GCP credentials
    }

    # Extended dangerous bash patterns (51 patterns)
    DANGEROUS_PATTERNS = [
        # Destructive file operations
        (r"\brm\s+-rf\s+/", "Recursive delete from root"),
        (r"\brm\s+-rf\s+~", "Recursive delete home"),
        (r"\brm\s+-rf\s+\*", "Recursive delete wildcard"),
        (r"\brm\s+-rf\s+\.\.", "Recursive delete parent"),
        (r"\brm\s+(-[a-z]*f[a-z]*\s+)?/(?!tmp)", "Delete system files"),
        (r":\s*\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", "Fork bomb"),
        # Disk/system operations
        (r"\bdd\s+if=", "Direct disk access"),
        (r"\bmkfs", "Filesystem creation"),
        (r"\bfdisk", "Disk partitioning"),
        (r"\bparted", "Disk partitioning"),
        (r"\bmount\s+", "Mount filesystem"),
        (r"\bumount\s+", "Unmount filesystem"),
        (r"\b>\s*/dev/sd", "Direct device write"),
        (r"\b>\s*/dev/null.*2>&1.*&$", "Background with no output (suspicious)"),
        # Remote code execution
        (r"\bcurl\s+.*\|\s*(ba)?sh", "Pipe to shell"),
        (r"\bwget\s+.*\|\s*(ba)?sh", "Pipe to shell"),
        (r"\bbase64\s+-d.*\|\s*(ba)?sh", "Encoded payload execution"),
        (r"\beval\s+\$", "Eval with variable"),
        (r"\beval\s+['\"]", "Eval string execution"),
        (r"\bpython[23]?\s+-c.*exec\(", "Python exec injection"),
        (r"\bperl\s+-e", "Perl one-liner"),
        (r"\b(python|python3|node|ruby|perl)\s+-c\s+['\"].*eval", "Code injection"),
        # Privilege escalation
        (r"\bsudo\s+", "Sudo command"),
        (r"\bsu\s+-", "Switch user"),
        (r"\bchmod\s+[47]77", "Overly permissive chmod"),
        (r"\bchmod\s+\+s", "SetUID/SetGID"),
        (r"\bchown\s+root", "Change owner to root"),
        # Network attacks
        (r"\bnc\s+-[a-z]*l", "Network listener"),
        (r"\bnetcat\s+-[a-z]*l", "Network listener"),
        (r"\bnmap\s+", "Port scanning"),
        (r"\biptables\s+", "Firewall modification"),
        # Credential/data theft
        (r"\bcat\s+.*(passwd|shadow|sudoers)", "Read system credentials"),
        (r"\bhistory\s*$", "Read command history"),
        (r"\bcat\s+.*\.ssh/", "Read SSH keys"),
        (r"\bexport\s+.*_(KEY|SECRET|TOKEN|PASSWORD)", "Export credentials"),
        # System damage
        (r"\bshutdown", "System shutdown"),
        (r"\breboot", "System reboot"),
        (r"\binit\s+[0-6]", "Change runlevel"),
        (r"\bsystemctl\s+(stop|disable|mask)\s+(ssh|sshd|network)", "Disable critical services"),
        (r"\bkillall\s+-9", "Force kill all"),
        (r"\bpkill\s+-9", "Force kill processes"),
        # Crypto/ransomware patterns
        (r"\bopenssl\s+enc\s+-aes.*-in\s+/", "Encrypt system files"),
        (r"\bgpg\s+--encrypt.*-r\s+", "GPG encrypt"),
        (r"\bfind\s+/.*-exec.*rm", "Find and delete system files"),
        (r"\.onion", "Tor hidden service"),
        (r"\btor\s+", "Tor usage"),
    ]

    # Dangerous Python code patterns (24 patterns)
    DANGEROUS_PYTHON = [
        (r"\bos\.system\s*\(", "os.system() - use subprocess instead"),
        (r"\bos\.popen\s*\(", "os.popen() - dangerous"),
        (r"\bsubprocess\..*shell\s*=\s*True", "subprocess with shell=True"),
        (r"\beval\s*\(", "eval() - code injection risk"),
        (r"\bexec\s*\(", "exec() - code injection risk"),
        (r"\bcompile\s*\(.*exec", "compile() for exec"),
        (r"\b__import__\s*\(", "Dynamic import"),
        (r"\bimportlib\.import_module\s*\(", "Dynamic import"),
        (r"\bopen\s*\(['\"]/(etc|usr|var|bin|sbin)", "Access system directories"),
        (r"\bopen\s*\(['\"]C:\\\\Windows", "Access Windows system"),
        (r"\bshutil\.rmtree\s*\(['\"]/(|home|usr|etc|var)", "Delete system directories"),
        (r"\bshutil\.rmtree\s*\(['\"]C:\\\\", "Delete Windows system"),
        (r"\bos\.remove\s*\(['\"]/(etc|usr|bin)", "Delete system files"),
        (r"\bos\.rmdir\s*\(['\"]/(etc|usr|bin)", "Delete system directories"),
        (r"\bctypes\.", "ctypes - low-level access"),
        (r"\bsocket\..*bind\s*\(", "Network server binding"),
        (r"\bsocket\..*listen\s*\(", "Network listening"),
        (r"\brequests\.(get|post).*verify\s*=\s*False", "Disable SSL verification"),
        (r"\burllib.*verify\s*=\s*False", "Disable SSL verification"),
        (r"\bpickle\.loads?\s*\(", "pickle - deserialization attack risk"),
        (r"\byaml\.load\s*\([^,)]+\)$", "yaml.load without Loader (unsafe)"),
        (r"\bgetattr\s*\(.*,\s*['\"]__", "Access dunder attributes"),
    ]

    # Network commands
    NETWORK_COMMANDS = ["curl", "wget", "nc", "netcat", "ssh", "scp", "rsync", "ftp", "telnet"]

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.workspace = Path(config.workspace_root).resolve()

    def validate_path(self, path: str) -> Tuple[bool, str]:
        """
        Check if path is within allowed workspace boundary.

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                resolved = (self.workspace / path).resolve()
            else:
                resolved = Path(path).resolve()

            # Must be within workspace
            try:
                resolved.relative_to(self.workspace)
            except ValueError:
                return False, f"Path outside workspace: {path}"

            # Check for sensitive files
            filename = resolved.name
            if filename in self.SENSITIVE_FILES:
                return False, f"Access to sensitive file blocked: {filename}"

            # Check parent directories for sensitive patterns
            for part in resolved.parts:
                if part.startswith(".env"):
                    return False, f"Access to .env file blocked: {path}"
                if part in (".aws", ".ssh") and len(resolved.parts) > resolved.parts.index(part) + 1:
                    return False, f"Access to credentials directory blocked: {path}"

            return True, "OK"

        except Exception as e:
            return False, f"Invalid path: {e}"

    def scan_for_secrets(self, content: str) -> List[Dict]:
        """
        Scan content for potential secrets.

        Returns:
            List of findings with type and warning message
        """
        findings = []
        for pattern, secret_type in self.SECRET_PATTERNS:
            try:
                matches = re.findall(pattern, content)
                if matches:
                    findings.append(
                        {
                            "type": secret_type,
                            "count": len(matches),
                            "warning": f"Found {len(matches)} potential {secret_type}(s)",
                        }
                    )
            except re.error:
                continue
        return findings

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate bash command for dangerous patterns.

        Returns:
            Tuple of (is_valid, message)
        """
        # Check dangerous patterns
        for pattern, reason in self.DANGEROUS_PATTERNS:
            try:
                if re.search(pattern, command, re.IGNORECASE):
                    return False, f"Blocked: {reason}"
            except re.error:
                continue

        # Block network commands if not allowed
        if not self.config.allow_network:
            for cmd in self.NETWORK_COMMANDS:
                # Match command at word boundary
                if re.search(rf"\b{cmd}\b", command):
                    return False, f"Network command blocked: {cmd}"

        return True, "OK"

    def validate_python(self, code: str) -> Tuple[bool, str]:
        """
        Validate Python code for dangerous patterns.

        Returns:
            Tuple of (is_valid, message)
        """
        for pattern, reason in self.DANGEROUS_PYTHON:
            try:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    return False, reason
            except re.error:
                continue
        return True, "OK"

    def truncate_output(self, output: str, max_size: Optional[int] = None) -> Tuple[str, bool]:
        """
        Truncate output to prevent token explosion.

        Returns:
            Tuple of (output, was_truncated)
        """
        max_size = max_size or self.config.max_output_size

        if len(output) <= max_size:
            return output, False

        # Truncate and add notice
        truncated = output[:max_size]
        omitted = len(output) - max_size
        truncated += f"\n\n... [OUTPUT TRUNCATED - {omitted:,} bytes omitted]"
        return truncated, True

    def validate_file_size(self, path: str) -> Tuple[bool, str]:
        """Check if file size is within limits."""
        try:
            if not os.path.isabs(path):
                path = str(self.workspace / path)

            if os.path.exists(path):
                size = os.path.getsize(path)
                if size > self.config.max_file_size:
                    return False, f"File too large: {size:,} bytes (max: {self.config.max_file_size:,})"
            return True, "OK"
        except Exception as e:
            return False, f"Cannot check file size: {e}"

    def hash_content(self, content: str) -> str:
        """Generate hash for audit trail."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def sanitize_for_display(self, content: str, max_length: int = 100) -> str:
        """Sanitize content for safe display (redact potential secrets)."""
        sanitized = content
        for pattern, _ in self.SECRET_PATTERNS:
            try:
                sanitized = re.sub(pattern, "[REDACTED]", sanitized)
            except re.error:
                continue

        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."

        return sanitized
