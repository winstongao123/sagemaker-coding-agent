"""V5 security/dangerous_patterns.py — bash command denylist + allowlist.

Source: compact_v4/MAIN/agent/sagemaker_agent.py:1325-1577 + 1706-1738
(extracted as constants from the SecurityManager class so the regex
lists are a single grep target for security audits).

All patterns are VERBATIM from v4. Modifying these is a security-
critical change and requires Codex review with extra scrutiny.
"""
from __future__ import annotations

import re
from typing import List, Tuple

# ============================================================
# CATASTROPHIC_PATTERNS — Layer -1, hard-blocked, cannot be bypassed
# ============================================================
# Hard-blocked regardless of allowlist, config, or user approval. Patterns
# precompile at import time — fail-closed if any regex is malformed.

CATASTROPHIC_PATTERNS: List[Tuple[str, str]] = [
    # rm targeting / or ~ with any recursive flag variant
    (r"\brm\b.*(?:-[^\s]*r|-r\b|--recursive\b).*\s+/\s*$",   "Catastrophic: rm recursive on root /"),
    (r"\brm\b.*(?:-[^\s]*r|-r\b|--recursive\b).*\s+/\*",     "Catastrophic: rm recursive on /*"),
    (r"\brm\b.*(?:-[^\s]*r|-r\b|--recursive\b).*\s+~/?\s*$", "Catastrophic: rm recursive on home ~"),
    (r"\brm\b.*(?:-[^\s]*r|-r\b|--recursive\b).*\s+~/?/?\*", "Catastrophic: rm recursive on ~/*"),
    # dd reading from /dev/zero or /dev/urandom (dangerous regardless of output target)
    (r"\bdd\b.*\bif=/dev/(zero|urandom|random)\b", "Catastrophic: dd from /dev/zero or /dev/urandom"),
    # Disk formatting and partitioning
    (r"\bmkfs\b",  "Catastrophic: disk format operation"),
    (r"\bfdisk\b", "Catastrophic: disk partitioning"),
    (r"\bparted\b", "Catastrophic: disk partitioning"),
    # Fork bomb
    (r":\s*\(\)\s*\{[^}]*:\s*\|[^}]*:\s*&[^}]*\}\s*;", "Catastrophic: fork bomb"),
    # Recursive chmod on root
    (r"\bchmod\b.*-R\b.*\b(777|000)\b.*\s+/", "Catastrophic: recursive chmod on /"),
    # Direct disk device write
    (r">\s*/dev/(sd[a-z]|hd[a-z]|nvme\d+n\d+)(\b|$)", "Catastrophic: direct disk device write"),
    # Shutdown/halt (irreversible on a running server)
    (r"\bshutdown\b", "Catastrophic: system shutdown"),
    (r"\b(?:init|telinit)\s+0\b", "Catastrophic: system halt via init 0"),
]

# Precompile at import time — bad regex fails immediately, fail-closed.
CATASTROPHIC_COMPILED: List[Tuple[re.Pattern, str]] = [
    (re.compile(p), reason) for p, reason in CATASTROPHIC_PATTERNS
]


# ============================================================
# DANGEROUS_PATTERNS — Layer 2, regex denylist for bash arguments
# ============================================================
# 70+ patterns: destructive ops, path traversal, cloud CLI, git destructive,
# obfuscation, network attacks, credential theft, system damage, etc.

DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
    # === DESTRUCTIVE FILE OPERATIONS ===
    (r"\brm\s+-rf\s+/", "Recursive delete from root"),
    (r"\brm\s+-rf\s+~", "Recursive delete home"),
    (r"\brm\s+-rf\s+\*", "Recursive delete wildcard"),
    (r"\brm\s+-rf\s+\.\.", "Recursive delete parent"),
    (r"\brm\s+(-[a-z]*f[a-z]*\s+)?/(?!tmp)", "Delete system files"),
    (r":\s*\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", "Fork bomb"),

    # === PATH TRAVERSAL ===
    (r"\.\./\.\./\.\.", "Deep path traversal (../../../)"),
    (r"cat\s+\.\./", "Read parent directory files"),
    (r"cp\s+.*\.\./", "Copy to parent directory"),
    (r"mv\s+.*\.\./", "Move to parent directory"),

    # === DISK/SYSTEM OPERATIONS ===
    (r"\bdd\s+if=", "Direct disk access"),
    (r"\bmkfs", "Filesystem creation"),
    (r"\bfdisk", "Disk partitioning"),
    (r"\bparted", "Disk partitioning"),
    (r"\bmount\s+", "Mount filesystem"),
    (r"\bumount\s+", "Unmount filesystem"),
    (r"\b>\s*/dev/sd", "Direct device write"),
    (r"\b>\s*/dev/null.*2>&1.*&$", "Background with no output (suspicious)"),

    # === AWS CLI - RESOURCE ACCESS (SageMaker IAM protection) ===
    (r"\baws\s+s3\s+", "AWS S3 access - use provided code instead"),
    (r"\baws\s+s3api\s+", "AWS S3 API access - use provided code instead"),
    (r"\baws\s+dynamodb\s+", "AWS DynamoDB access - use provided code instead"),
    (r"\baws\s+lambda\s+", "AWS Lambda access - use provided code instead"),
    (r"\baws\s+ec2\s+", "AWS EC2 access - restricted"),
    (r"\baws\s+iam\s+", "AWS IAM access - restricted"),
    (r"\baws\s+sts\s+", "AWS STS access - restricted"),
    (r"\baws\s+secretsmanager\s+", "AWS Secrets Manager - restricted"),
    (r"\baws\s+ssm\s+", "AWS Systems Manager - restricted"),
    (r"\baws\s+kms\s+", "AWS KMS access - restricted"),
    (r"\baws\s+rds\s+", "AWS RDS access - restricted"),
    (r"\baws\s+sqs\s+", "AWS SQS access - use provided code instead"),
    (r"\baws\s+sns\s+", "AWS SNS access - use provided code instead"),
    (r"\baws\s+logs\s+", "AWS CloudWatch Logs - restricted"),
    (r"\baws\s+cloudformation\s+", "AWS CloudFormation - restricted"),
    (r"\baws\s+sagemaker\s+(?!help)", "AWS SageMaker CLI - use SDK in code instead"),

    # === GIT REMOTES / GITHUB ===
    (r"\bgit\s+(push|pull|fetch|clone)\b", "Git remote operation unavailable in SageMaker; use local git tree only"),
    (r"\bgit\s+remote\s+(add|remove|rm|rename|set-url|set-head|prune)\b", "Git remote modification unavailable in SageMaker; use local git tree only"),

    # === GIT DESTRUCTIVE FLAGS (V4.10.7) ===
    (r"\bgit\s+reset\s+--hard\b", "Git destructive reset (loses uncommitted work)"),
    (r"\bgit\s+clean\s+-[a-z]*[fd]", "Git clean -fd removes untracked files (no undo)"),
    (r"\bgit\s+checkout\s+--?\s*(\.|HEAD|--all)", "Git destructive working-tree checkout"),
    (r"\bgit\s+restore\s+(--source|--worktree|--staged)?\s*\.", "Git restore on whole tree"),
    (r"\bgit\s+reflog\s+expire\b", "Git reflog expire (purges recovery history)"),
    (r"\bgit\s+gc\s+--prune", "Git aggressive prune (purges loose objects)"),

    # === CLOUD CLI HARD-BLOCK (V4.10.7) ===
    (r"\bgh\s+", "GitHub CLI blocked: gh not allowed in compact (no GitHub publishing from SageMaker)"),
    (r"\bgcloud\s+", "Cloud CLI blocked: gcloud (GCP) not allowed"),
    (r"\bgsutil\s+", "Cloud CLI blocked: gsutil (GCS) not allowed"),
    (r"\bbq\s+", "Cloud CLI blocked: bq (BigQuery) not allowed"),
    (r"\baz\s+", "Cloud CLI blocked: az (Azure) not allowed"),
    (r"\bazcopy\s+", "Cloud CLI blocked: azcopy (Azure Storage) not allowed"),
    (r"\bkubectl\s+", "Orchestration CLI blocked: kubectl not allowed"),
    (r"\bhelm\s+", "Orchestration CLI blocked: helm not allowed"),
    (r"\bkustomize\s+", "Orchestration CLI blocked: kustomize not allowed"),
    (r"\bterraform\s+", "IaC CLI blocked: terraform not allowed"),
    (r"\bterragrunt\s+", "IaC CLI blocked: terragrunt not allowed"),
    (r"\bpulumi\s+", "IaC CLI blocked: pulumi not allowed"),
    (r"\bdoctl\s+", "Cloud CLI blocked: doctl (DigitalOcean) not allowed"),
    (r"\boci\s+", "Cloud CLI blocked: oci (Oracle Cloud) not allowed"),
    (r"\bibmcloud\s+", "Cloud CLI blocked: ibmcloud not allowed"),
    (r"\blinode-cli\s+", "Cloud CLI blocked: linode-cli not allowed"),
    (r"\bhcloud\s+", "Cloud CLI blocked: hcloud (Hetzner) not allowed"),
    (r"\bheroku\s+", "Platform CLI blocked: heroku not allowed"),
    (r"\bvercel\s+", "Platform CLI blocked: vercel not allowed"),
    (r"\bnetlify\s+", "Platform CLI blocked: netlify not allowed"),
    (r"\bwrangler\s+", "Platform CLI blocked: wrangler (Cloudflare Workers) not allowed"),
    (r"\bcloudflared\s+", "Platform CLI blocked: cloudflared not allowed"),
    (r"\bflyctl\s+", "Platform CLI blocked: flyctl (Fly.io) not allowed"),
    (r"\brailway\s+", "Platform CLI blocked: railway not allowed"),
    (r"\brender-cli\s+", "Platform CLI blocked: render-cli not allowed"),

    # === PACKAGE DESTRUCTIVE (V4.10.7) ===
    (r"\bpip\d?\s+uninstall\b", "Package uninstall (pip) — requires approval"),
    (r"\bconda\s+(remove|uninstall|env\s+remove)\b", "Conda remove — requires approval"),
    (r"\bnpm\s+uninstall\b", "npm uninstall — requires approval"),
    (r"\b(yarn|pnpm|bun)\s+remove\b", "Package remove (yarn/pnpm/bun)"),
    (r"\b(apt|apt-get)\s+(remove|purge|autoremove)\b", "apt remove/purge"),
    (r"\byum\s+(remove|erase)\b", "yum remove/erase"),
    (r"\bdnf\s+(remove|erase)\b", "dnf remove/erase"),
    (r"\bbrew\s+(uninstall|remove)\b", "brew uninstall"),

    # === STORAGE / VOLUME / FILESYSTEM DESTRUCTIVE (V4.10.7) ===
    (r"\blvremove\b", "LVM logical volume remove"),
    (r"\bvgremove\b", "LVM volume group remove"),
    (r"\bpvremove\b", "LVM physical volume remove"),
    (r"\bzfs\s+destroy\b", "ZFS destroy"),
    (r"\bbtrfs\s+(subvolume\s+delete|filesystem\s+delete)\b", "Btrfs destroy"),
    (r"\bmdadm\s+--remove\b", "mdadm RAID remove"),
    (r"\bcryptsetup\s+(luksClose|erase|luksRemoveKey)\b", "LUKS erase/close"),
    (r"\btar\s+.*--(remove-files|delete)\b", "tar destructive flag"),
    (r"\b(rsync|scp)\s+.*--delete\b", "rsync/scp --delete (deletes at destination)"),

    # === PERMISSION / OWNERSHIP DESTRUCTIVE (V4.10.7) ===
    (r"\bchmod\s+(-R\s+)?0?00\b", "chmod 000 (locks files inaccessible)"),
    (r"\bchattr\s+[+-]i\b", "chattr immutable change (can lock files unrecoverably)"),

    # === SYSTEM-FILE OVERWRITE (V4.10.7) ===
    (r">\s*(/etc|/usr|/sbin|/bin|/lib|/boot)/", "Redirect into system directory"),
    (r"\b(echo|cat|printf)\s+.*>\s*(/etc/sudoers|/etc/passwd|/etc/shadow|/etc/hosts|/root/\.ssh)", "Overwrite sensitive system file"),

    # === PERSISTENCE / SCHEDULING (V4.10.7) ===
    (r"\bcrontab\s+(-r|-e|-i)\b", "crontab modify/remove"),
    (r"\bat\s+(now|\+)", "at scheduled job"),
    (r"\bsystemctl\s+(mask|disable|enable|stop|start|restart)\s+", "systemctl service control"),
    (r"\bservice\s+\S+\s+(stop|start|restart)\b", "service control"),
    (r"\bpm2\s+(delete|kill|stop|restart)\b", "pm2 process control"),
    (r"\bsupervisorctl\s+(stop|remove|update)\b", "supervisorctl control"),

    # === DATABASE CLI (V4.10.7) ===
    (r"\b(psql|mysql|mongosh?|redis-cli|cqlsh|sqlite3)\s+", "Database CLI not allowed (use Python with approval gate)"),

    # === NETWORK - EXTERNAL REQUESTS (V4.8.0: relaxed; only block pipe-to-shell) ===
    (r"\bcurl\s+.*\|\s*(ba)?sh", "Pipe to shell — RCE risk"),
    (r"\bwget\s+.*\|\s*(ba)?sh", "Pipe to shell — RCE risk"),
    (r"\bbase64\s+-d.*\|\s*(ba)?sh", "Encoded payload execution"),

    # === COMMAND SUBSTITUTION / VARIABLE EXPANSION ===
    (r"\$\(.*\baws\s+", "Command substitution with AWS CLI"),
    (r"`.*\baws\s+", "Backtick substitution with AWS CLI"),
    (r"\$\(.*\bcurl\s+", "Command substitution with curl"),
    (r"\$\(.*\bwget\s+", "Command substitution with wget"),

    # === REMOTE CODE EXECUTION ===
    (r"\beval\s+\$", "Eval with variable"),
    (r"\beval\s+['\"]", "Eval string execution"),
    (r"\beval\s+.*\$\(", "Eval with command substitution"),
    (r"\beval\s+[^|;&]*`[^`]*\b(curl|wget|fetch|base64|xxd|hexdump)\b", "Eval of remote-fetch/decode backtick (download, inspect, then run)"),
    (r"\bpython[23]?\s+-c\b", "Python -c bypasses python_exec security; use python_exec tool instead"),
    (r"\bperl\s+-e", "Perl one-liner"),

    # === PRIVILEGE ESCALATION ===
    (r"\bsudo\s+", "Sudo command"),
    (r"\bsu\s+-", "Switch user"),
    (r"\bchmod\s+[47]77", "Overly permissive chmod"),
    (r"\bchmod\s+\+s", "SetUID/SetGID"),
    (r"\bchown\s+root", "Change owner to root"),

    # === NETWORK ATTACKS ===
    (r"\bnc\s+-[a-z]*l", "Network listener"),
    (r"\bnetcat\s+-[a-z]*l", "Network listener"),
    (r"\bnmap\s+", "Port scanning"),
    (r"\biptables\s+", "Firewall modification"),

    # === CREDENTIAL/DATA THEFT ===
    (r"\bcat\s+.*(passwd|shadow|sudoers)", "Read system credentials"),
    (r"\bhistory\s*$", "Read command history"),
    (r"\bcat\s+.*\.ssh/", "Read SSH keys"),
    (r"\bexport\s+.*_(KEY|SECRET|TOKEN|PASSWORD)", "Export credentials"),
    (r"\benv\s*$", "List environment variables"),
    (r"\bprintenv\s+(AWS_|SECRET|TOKEN|KEY|PASSWORD)", "Print sensitive env vars"),
    (r"\becho\s+\$AWS_", "Echo AWS credentials"),

    # === SYSTEM DAMAGE ===
    (r"\bshutdown", "System shutdown"),
    (r"\breboot", "System reboot"),
    (r"\binit\s+[0-6]", "Change runlevel"),
    (r"\bsystemctl\s+(stop|disable|mask)\s+(ssh|sshd|network)", "Disable critical services"),
    (r"\bkillall\s+-9", "Force kill all"),
    (r"\bpkill\s+-9", "Force kill processes"),

    # === CRYPTO/RANSOMWARE ===
    (r"\bopenssl\s+enc\s+-aes.*-in\s+/", "Encrypt system files"),
    (r"\bgpg\s+--encrypt.*-r\s+", "GPG encrypt"),
    (r"\bfind\s+/.*-exec.*rm", "Find and delete system files"),
    (r"\.onion", "Tor hidden service"),
    (r"\btor\s+", "Tor usage"),

    # === OBFUSCATION HARDENING (V4.10.8) ===
    (r"\bbase64\s+(?:-d|--decode|-D)[^|;&]*\|\s*(?:sudo\s+)?(?:zsh|dash|ksh|fish|python\d?|perl|ruby|node|pwsh|powershell)\b", "Base64-decoded payload piped into interpreter — decode and inspect first"),
    (r"\bxxd\s+(?:-r|-p)[^|;&]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh|python\d?|perl|ruby|node)\b", "Hex-decoded payload (xxd) piped into shell — decode and inspect first"),
    (r"\b(?:od|hexdump)\s+[^|;&]*\|\s*(?:tr|sed|awk)[^|;&]*\|\s*(?:sh|bash)\b", "Hex-decode chain piped to shell"),

    # === RECURSIVE FOLDER REMOVAL (V4.10.8) — HARD BLOCK ===
    (r"\brm\s+(?:-[a-zA-Z]*[rR][a-zA-Z]*\b|--recursive\b)", "Recursive folder delete blocked. Single-file rm allowed; folder cleanup goes through 🧹 Clean button or your own terminal."),
    (r"\brmdir\b", "rmdir blocked. Folder removal must be manual or via 🧹 Clean button."),
    (r"(?i)\bRemove-Item\b[^|;&]*-(?:Recurse|R)\b", "PowerShell Remove-Item -Recurse blocked. Folder removal must be manual."),
]


# ============================================================
# Network commands (Layer 3)
# ============================================================
# v4.8.0: curl/wget removed (now in BASE_ALLOWED_COMMANDS for legit
# downloads — pipe-to-shell still blocked by DANGEROUS_PATTERNS).

NETWORK_COMMANDS: List[str] = ["nc", "netcat", "ssh", "scp", "rsync", "ftp", "telnet"]


# ============================================================
# Command allowlists (Layer 1)
# ============================================================
# Anything not on these lists is blocked by validate_command regardless
# of denylist match. Adding a base command here requires a security review.

BASE_ALLOWED_COMMANDS = {
    # Version control
    "git",
    # File operations (safe subset)
    "ls", "dir", "cat", "head", "tail", "wc", "sort", "uniq", "diff", "file",
    "find", "tree", "du", "df", "stat", "md5sum", "sha256sum",
    "cp", "mv", "mkdir", "touch",  # write ops still need approval
    # Text processing
    "grep", "rg", "awk", "sed", "cut", "tr", "xargs", "tee",
    "echo", "printf",
    # Package management
    "pip", "pip3", "conda", "npm", "yarn", "pnpm", "bun",
    # Build tools
    "make", "cmake", "gcc", "g++", "clang",
    # System info (read-only)
    "pwd", "whoami", "hostname", "uname", "date", "which", "where", "type",
    "env", "printenv",  # denylist still blocks sensitive patterns
    # Archive
    "tar", "zip", "unzip", "gzip", "gunzip",
    # Testing
    "pytest", "jest", "mocha", "cargo",
    # Misc safe utilities
    "jq", "yq", "less", "more", "true", "false", "test",
    # V4.8.0: Allow bash scripts and wget downloads (pipe-to-shell still blocked by denylist)
    "bash", "sh", "wget", "curl",
}

INTERPRETER_COMMANDS = {"python", "python3", "node", "ruby", "go", "cargo", "rustc", "javac", "java"}
CONTAINER_COMMANDS = {"docker", "docker-compose"}
