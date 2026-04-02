# sagemaker_agent.py (Markdown Copy)

This file is an auto-generated markdown copy of `sagemaker_agent.py`.

```python
"""
SageMaker Coding Agent - Compact Version (AWS Bedrock)
A secure AI coding assistant powered by AWS Bedrock Claude.

Version: 2.5.0 (January 2025)

UI Layout:
    Row 1: [Name] [💾Save] [Session▼] [📁Load] [+New] | [Model▼]
    Row 2: [Temp] [Thinking] [Budget] [Dark] | [Plan Mode] [☑Auto-Compact]
    Chat:  HTML widget with internal scroll (fixes SageMaker drifting)
    Row 3: [Send] [Clear] [Compact] [Status]
    Row 4: Token usage with progress bar

Features Implemented:
- UI: HTML widget with internal scroll (fixes SageMaker drifting)
- UI: Auto-scroll to bottom (CSS flex-direction: column-reverse)
- UI: Dark mode toggle updates all existing messages
- UI: Session dropdown with Load/New buttons
- UI: Save button in Row 1 (after Name)
- Context: Compact button (OpenCode-style 2-stage: prune + summarize)
- Context: Auto-Compact (ON by default, triggers at 90%, keeps last 3 messages)
- Context: Pre-send compact (auto-compacts at 80% BEFORE sending to prevent overflow)
- Context: Auto-continue after compact (resumes automatically like OpenCode)
- Context: Plan Mode (enforced read-only - blocks write tools)
- Context: Token display shows actual context window % (not cumulative API totals)
- UI: Stop button (cancel LLM processing mid-stream)
- Token Optimization (v2.5.0):
  - Protected tools (todo, semantic_search never pruned)
  - File read cache (don't re-read same file)
  - File dedup (skip if already in context)
  - Smart truncation (head + tail, skip middle)
  - Diff-only edits (compact output)
- Session: Auto-save after each message (no manual save needed)
- Session: Save/Load with absolute paths (./sessions/)
- Session: Todo list persisted with session
- Tools: 22 tools including:
  - File: read_file, write_file, edit_file, glob, grep, list_dir
  - Exec: bash, python_exec
  - Docs: create_word (with images), create_excel (with charts), create_markdown, create_notebook
  - Charts/PDF: create_chart (bar/line/pie/scatter/inline), create_pdf (text/tables/images)
  - Search: semantic_search
  - Skills/MCP: skill_list, skill_read, mcp_call, subagent_run
  - Other: view_image, todo_write, todo_read

Security (70+ bash patterns, 40+ Python patterns):
- AWS CLI blocked: aws s3, aws dynamodb, aws iam, etc. (agent writes code for you)
- Network blocked: curl/wget to external URLs (except pip/pypi)
- Path traversal blocked: ../../.. patterns
- Credentials protected: AWS_*, env, printenv blocked
- System commands blocked: sudo, rm -rf, dd, etc.
- Agent CAN write code for AWS access - you run it yourself

Dependencies:
    pip install boto3 ipywidgets python-docx pandas openpyxl
    pip install matplotlib reportlab  # For charts and PDFs

Not Implemented (vs OpenCode):
- Sub-agents
- MCP server integration
- Sliding window context

Usage:
    from sagemaker_agent import create_chat_ui
    create_chat_ui()
"""

__version__ = "2.5.0"

# ============================================================
# IMPORTS
# ============================================================

import os
import json
import re
import hashlib
import subprocess
import tempfile
import sys
import base64
import time
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Tuple, Optional, Any, Set, Callable
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import copy
import glob as glob_module
import random
import shlex
import threading
import shutil
import urllib.request
import urllib.error

# ============================================================
# RETRY LOGIC (OpenCode-style)
# ============================================================

class RetryableError(Exception):
    """Error that can be retried."""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after

class RetryHandler:
    """Handles retries with exponential backoff."""

    RETRYABLE_CODES = {429, 500, 502, 503, 504}  # Rate limit + server errors
    RETRYABLE_MESSAGES = ["rate_limit", "overloaded", "temporarily unavailable", "quota exceeded", "throttl"]

    def __init__(self, max_retries: int = 5, base_delay: float = 2.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def is_retryable(self, error: Exception) -> Tuple[bool, Optional[float]]:
        """Check if error is retryable and get retry delay."""
        error_str = str(error).lower()

        # Check for rate limit / quota errors
        for msg in self.RETRYABLE_MESSAGES:
            if msg in error_str:
                # Try to extract retry-after from error message
                match = re.search(r'retry.?after[:\s]+(\d+)', error_str)
                retry_after = float(match.group(1)) if match else None
                return True, retry_after

        # Check for HTTP status codes
        for code in self.RETRYABLE_CODES:
            if str(code) in error_str:
                return True, None

        return False, None

    def get_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """Calculate delay with exponential backoff + jitter."""
        if retry_after:
            return min(retry_after, self.max_delay)

        # Exponential backoff: 2^attempt * base_delay + random jitter
        delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
        return delay

    def execute(self, fn: Callable, on_retry: Callable = None) -> Any:
        """Execute function with retry logic."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                is_retryable, retry_after = self.is_retryable(e)

                if not is_retryable or attempt >= self.max_retries:
                    raise e

                delay = self.get_delay(attempt, retry_after)

                if on_retry:
                    on_retry(attempt + 1, self.max_retries, delay, str(e))

                time.sleep(delay)

        raise last_error

# Global retry handler
RETRY = RetryHandler(max_retries=5, base_delay=2.0, max_delay=60.0)


# ============================================================
# CONTEXT COMPACTION (OpenCode-style)
# ============================================================

class Compactor:
    """Smart context compaction - prune then summarize."""

    PRUNE_PROTECT_TOKENS = 40000  # Keep last 40K tokens of tool outputs
    PRUNE_MIN_SAVINGS = 10000     # Only prune if saving 10K+ tokens
    SUMMARY_TRIGGER_PERCENT = 0.80  # Trigger at 80% context

    # Protected tools - never prune these (important for agent memory)
    PROTECTED_TOOLS = {"todo_write", "todo_read", "semantic_search"}

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimate tokens (4 chars = 1 token)."""
        return len(text) // 4

    @classmethod
    def prune_tool_outputs(cls, messages: List[Dict], max_context: int) -> Tuple[List[Dict], int]:
        """
        Prune old tool outputs while keeping recent ones.
        Returns (pruned_messages, tokens_saved).
        """
        if not messages:
            return messages, 0

        # Deep copy first, then collect and mutate only the copy
        pruned_messages = copy.deepcopy(messages)

        # Find tool result items in the COPY to potentially prune
        tool_results = []
        for i, msg in enumerate(pruned_messages):
            content = msg.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        tool_results.append({
                            "index": i,
                            "tokens": cls.estimate_tokens(str(item.get("content", ""))),
                            "item": item
                        })

        if not tool_results:
            return messages, 0

        # Walk from newest to oldest, protect last 40K tokens
        protected_tokens = 0
        tokens_saved = 0
        for tr in reversed(tool_results):
            if protected_tokens < cls.PRUNE_PROTECT_TOKENS:
                protected_tokens += tr["tokens"]
            else:
                # Prune this tool output (mutates only the deep copy)
                content = tr["item"].get("content", "")
                if len(content) > 200:
                    tr["item"]["content"] = content[:100] + f"\n[... {len(content)} chars pruned to save context ...]\n" + content[-100:]
                    tokens_saved += tr["tokens"] - 60  # Approximate new size

        if tokens_saved < cls.PRUNE_MIN_SAVINGS:
            return messages, 0  # Not worth pruning - return originals untouched

        return pruned_messages, tokens_saved

    @classmethod
    def create_summary_prompt(cls, messages: List[Dict]) -> str:
        """Create a prompt to summarize the conversation using Claude Code's 9-section format."""
        return """<analysis>
First, analyze the conversation to identify: main goal, technical concepts, files touched, errors encountered, and current progress.
</analysis>

Create a detailed summary following these EXACT sections:

1. **Primary Request and Intent**: What did the user explicitly ask for? What is their underlying goal?

2. **Key Technical Concepts**: Technologies, frameworks, libraries, patterns discussed or used.

3. **Files and Code Sections**: For each important file:
   - File path (absolute)
   - WHY it's important
   - What changes were made (if any)
   - Key code snippets (if relevant)

4. **Errors and Fixes**: For each error encountered:
   - The error message
   - How it was fixed
   - Any user feedback on the fix

5. **Problem Solving**: Problems solved during the session, and any ongoing issues still unresolved.

6. **ALL User Messages**: List EVERY user message verbatim (this prevents intent drift):
   - "message 1 exact text"
   - "message 2 exact text"
   - (continue for all messages)

7. **Pending Tasks**: Tasks mentioned but not yet completed.

8. **Current Work**: Precise current state including:
   - What step we're on
   - What was just completed
   - Relevant code context

9. **Next Step**: Only if directly in line with user's explicit request. Include direct quotes from user if applicable.

Format as a comprehensive summary that preserves all context needed to continue seamlessly."""

    @classmethod
    def should_compact(cls, messages: List[Dict], max_tokens: int) -> bool:
        """Check if compaction is needed."""
        total_tokens = sum(cls.estimate_tokens(str(m.get("content", ""))) for m in messages)
        return total_tokens > max_tokens * cls.SUMMARY_TRIGGER_PERCENT

    KEEP_LAST_MESSAGES = 3  # Keep last N messages after compact

    @classmethod
    def compact(cls, messages: List[Dict], summary: str) -> List[Dict]:
        """
        Replace old messages with summary.
        Keeps: summary + last N messages (default 3)
        """
        summary_msg = {
            "role": "assistant",
            "content": f"[CONVERSATION SUMMARY]\n{summary}\n[END SUMMARY - Continuing from here]"
        }

        # Keep last N messages for continuity
        n = cls.KEEP_LAST_MESSAGES
        recent_messages = copy.deepcopy(messages[-n:] if len(messages) > n else messages)

        # Ensure summary assistant message is followed by user role for Bedrock alternation.
        while recent_messages and recent_messages[0].get("role") != "user":
            recent_messages.pop(0)
        if not recent_messages:
            recent_messages = [{"role": "user", "content": "[Conversation compacted. Continue from summary.]"}]

        return [summary_msg] + recent_messages

# Global compactor
COMPACTOR = Compactor()


# ============================================================
# SMART TRUNCATION (OpenCode-style)
# ============================================================

class Truncation:
    """Smart truncation for large outputs - saves full content, returns preview."""

    MAX_LINES = 2000
    MAX_BYTES = 50 * 1024  # 50 KB
    MAX_LINE_LENGTH = 2000
    TRUNCATED_DIR = "./truncated_outputs"

    @classmethod
    def smart_truncate(cls, text: str, head_lines: int = 100, tail_lines: int = 50) -> Tuple[str, bool]:
        """
        Smart truncation: show head + tail, skip middle.
        Returns: (truncated_text, was_truncated)
        """
        lines = text.split('\n')
        total_lines = len(lines)
        total_bytes = len(text.encode('utf-8'))

        # Check if truncation needed
        if total_lines <= cls.MAX_LINES and total_bytes <= cls.MAX_BYTES:
            return text, False

        # Smart truncate: head + tail
        if total_lines <= head_lines + tail_lines + 10:
            return text, False  # Not worth truncating

        head = lines[:head_lines]
        tail = lines[-tail_lines:] if tail_lines > 0 else []
        skipped = total_lines - head_lines - tail_lines

        result_parts = []
        result_parts.extend(head)
        result_parts.append(f"\n... [{skipped} lines skipped - use grep to search or read_file with offset] ...\n")
        result_parts.extend(tail)

        return '\n'.join(result_parts), True

    @classmethod
    def truncate(cls, text: str, direction: str = "head") -> Tuple[str, bool, Optional[str]]:
        """
        Truncate text if it exceeds limits.
        Returns: (truncated_text, was_truncated, saved_path)
        """
        os.makedirs(cls.TRUNCATED_DIR, exist_ok=True)

        lines = text.split('\n')
        total_lines = len(lines)
        total_bytes = len(text.encode('utf-8'))

        # Check if truncation needed
        if total_lines <= cls.MAX_LINES and total_bytes <= cls.MAX_BYTES:
            return text, False, None

        # Save full output to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_path = os.path.join(cls.TRUNCATED_DIR, f"output_{timestamp}.txt")
        with open(saved_path, 'w', encoding='utf-8') as f:
            f.write(text)

        # Truncate based on direction
        output_lines = []
        current_bytes = 0

        if direction == "head":
            for i, line in enumerate(lines):
                if i >= cls.MAX_LINES:
                    break
                if len(line) > cls.MAX_LINE_LENGTH:
                    line = line[:cls.MAX_LINE_LENGTH] + "..."
                line_bytes = len(line.encode('utf-8')) + 1
                if current_bytes + line_bytes > cls.MAX_BYTES:
                    break
                output_lines.append(line)
                current_bytes += line_bytes
        else:  # tail
            for i in range(len(lines) - 1, -1, -1):
                if len(output_lines) >= cls.MAX_LINES:
                    break
                line = lines[i]
                if len(line) > cls.MAX_LINE_LENGTH:
                    line = line[:cls.MAX_LINE_LENGTH] + "..."
                line_bytes = len(line.encode('utf-8')) + 1
                if current_bytes + line_bytes > cls.MAX_BYTES:
                    break
                output_lines.insert(0, line)
                current_bytes += line_bytes

        # Build truncated output with helpful hint
        truncated_count = total_lines - len(output_lines)
        result = '\n'.join(output_lines)
        result += f"\n\n...{truncated_count} lines truncated ({total_bytes:,} bytes total)..."
        result += f"\n[Full output saved: {saved_path}]"
        result += f"\n[TIP: Use grep to search, or read_file with offset parameter for specific sections.]"

        return result, True, saved_path


# ============================================================
# STRUCTURED TOOL OUTPUT (OpenCode-style)
# ============================================================

@dataclass
class ToolResult:
    """Structured tool output with metadata."""
    output: str
    title: str = ""
    truncated: bool = False
    total_size: int = 0
    shown_size: int = 0
    metadata: Dict = field(default_factory=dict)

    def __str__(self) -> str:
        """Return output string for backward compatibility."""
        return self.output

    def to_display(self) -> str:
        """Format for display with metadata hints."""
        parts = [self.output]
        if self.truncated:
            parts.append(f"\n[Truncated: showing {self.shown_size:,} of {self.total_size:,} chars]")
        return "".join(parts)


# ============================================================
# FILE CACHE (Token Optimization)
# ============================================================

class FileCache:
    """
    Cache for file reads to avoid re-reading same file.
    Also tracks files already in context to enable dedup.
    """
    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self._cache: Dict[str, Tuple[str, float]] = {}  # path -> (content, mtime)
        self._in_context: Set[str] = set()  # Files already read in this session

    def get(self, path: str) -> Optional[str]:
        """Get cached content if file hasn't changed."""
        abs_path = os.path.abspath(path)
        if abs_path not in self._cache:
            return None

        content, cached_mtime = self._cache[abs_path]
        try:
            current_mtime = os.path.getmtime(abs_path)
            if current_mtime == cached_mtime:
                return content
        except OSError:
            pass

        # File changed or error, invalidate cache
        del self._cache[abs_path]
        return None

    def put(self, path: str, content: str) -> None:
        """Cache file content."""
        abs_path = os.path.abspath(path)
        try:
            mtime = os.path.getmtime(abs_path)
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_entries:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[abs_path] = (content, mtime)
        except OSError:
            pass

    def is_in_context(self, path: str) -> bool:
        """Check if file was already read in this session."""
        return os.path.abspath(path) in self._in_context

    def mark_in_context(self, path: str) -> None:
        """Mark file as read in this session."""
        self._in_context.add(os.path.abspath(path))

    def clear_context(self) -> None:
        """Clear context tracking (call on new session or compact)."""
        self._in_context.clear()

    def clear_all(self) -> None:
        """Clear all caches."""
        self._cache.clear()
        self._in_context.clear()

# Global file cache
FILE_CACHE = FileCache()


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class Config:
    """Agent configuration."""
    # AWS Settings
    region: str = "ap-southeast-2"  # Sydney
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"  # Haiku: 8 req/min (vs Sonnet: 1 req/min)

    # Workspace - use absolute paths to avoid confusion
    workspace: str = os.getcwd()
    sessions_dir: str = os.path.join(os.getcwd(), "sessions")
    audit_dir: str = os.path.join(os.getcwd(), "audit_logs")

    # Limits
    max_turns: int = 30
    max_tokens: int = 16384  # Must be > thinking_budget when thinking enabled
    max_history: int = 20
    max_output_chars: int = 50000  # Allow more output for large files
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # Context limits (Claude 3.5 = 200K tokens)
    context_max_tokens: int = 200000

    # Model parameters
    temperature: float = 0.0  # 0.0-1.0, higher = more creative
    thinking_enabled: bool = False  # Extended thinking OFF by default
    thinking_budget: int = 8192  # Tokens for thinking (1024-16000)

    # Testing
    mock_mode: bool = False  # Set True to test without Bedrock API

    # Security policy
    bash_allow_interpreters: bool = False  # If True, allow python/node/etc via bash tool
    bash_allow_docker: bool = False        # If True, allow docker/docker-compose via bash tool

    # Runtime isolation / execution limits
    execution_mode: str = "local"  # local | docker
    exec_docker_image: str = "python:3.11-slim"
    exec_docker_network_disabled: bool = True
    exec_docker_readonly_rootfs: bool = True
    exec_docker_cpus: float = 1.0
    exec_docker_memory: str = "1g"
    exec_docker_pids_limit: int = 128

    # Operational controls
    require_auth: bool = False
    require_tool_approval: bool = False  # For single-user SageMaker, default OFF avoids stuck approval UI
    auth_token_env: str = "SAGEMAKER_AGENT_AUTH_TOKEN"
    max_user_messages_per_minute: int = 10
    max_user_messages_per_session: int = 150
    max_exec_calls_per_session: int = 40
    max_exec_seconds_per_session: int = 900
    audit_retention_days: int = 30

    # V4 capabilities
    enable_skills: bool = True
    skills_dir: str = "./skills"
    enable_mcp: bool = False
    mcp_endpoint: str = ""
    mcp_timeout_seconds: int = 20
    mcp_allowed_methods: List[str] = field(default_factory=lambda: [
        "resources/list", "resources/read", "tools/list", "tools/call"
    ])
    subagent_max_depth: int = 1

# Initialize config
CONFIG = Config()

# Create directories
os.makedirs(CONFIG.sessions_dir, exist_ok=True)
os.makedirs(CONFIG.audit_dir, exist_ok=True)


# ============================================================
# SECURITY MODULE
# ============================================================

class SecurityManager:
    """Security controls: workspace boundary, secret detection, command filtering."""

    SECRET_PATTERNS = [
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
    ]

    SENSITIVE_FILES = {
        ".env", ".env.local", ".env.production", ".env.development",
        "credentials.json", "secrets.json", "config.secret.json",
        "id_rsa", "id_ed25519", "id_dsa", "id_ecdsa",
        ".netrc", ".npmrc", ".pypirc",
        "service-account.json", "service_account.json",  # GCP credentials
    }

    # Extended dangerous bash patterns (70+ patterns)
    DANGEROUS_PATTERNS = [
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

        # === NETWORK - EXTERNAL REQUESTS (except pip) ===
        (r"\bcurl\s+https?://(?!pypi\.|files\.pythonhosted\.|localhost|127\.0\.0\.1)", "External HTTP request - blocked for security"),
        (r"\bwget\s+https?://(?!pypi\.|files\.pythonhosted\.|localhost|127\.0\.0\.1)", "External download - blocked for security"),
        (r"\bcurl\s+.*\|\s*(ba)?sh", "Pipe to shell"),
        (r"\bwget\s+.*\|\s*(ba)?sh", "Pipe to shell"),
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
        (r"\bpython[23]?\s+-c.*exec\(", "Python exec injection"),
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
    ]

    # Dangerous Python code patterns (40+ patterns)
    DANGEROUS_PYTHON = [
        # === CODE INJECTION ===
        (r"\bos\.system\s*\(", "os.system() - use subprocess instead"),
        (r"\bos\.popen\s*\(", "os.popen() - dangerous"),
        (r"\bsubprocess\..*shell\s*=\s*True", "subprocess with shell=True (also caught by broader subprocess block)"),
        (r"\beval\s*\(", "eval() - code injection risk"),
        (r"\bexec\s*\(", "exec() - code injection risk"),
        (r"\bcompile\s*\(.*exec", "compile() for exec"),
        (r"\b__import__\s*\(", "Dynamic import"),
        (r"\bimportlib\.import_module\s*\(", "Dynamic import"),

        # === FILE SYSTEM ACCESS ===
        (r"\bopen\s*\(['\"]/(etc|usr|var|bin|sbin)", "Access system directories"),
        (r"\bopen\s*\(['\"]C:\\\\Windows", "Access Windows system"),
        (r"\bshutil\.rmtree\s*\(['\"]/(|home|usr|etc|var)", "Delete system directories"),
        (r"\bshutil\.rmtree\s*\(['\"]C:\\\\", "Delete Windows system"),
        (r"\bos\.remove\s*\(['\"]/(etc|usr|bin)", "Delete system files"),
        (r"\bos\.rmdir\s*\(['\"]/(etc|usr|bin)", "Delete system directories"),
        (r"\bopen\s*\(['\"]\.\.\/\.\.\/.*/", "Path traversal in open()"),

        # === AWS SDK (boto3) - RESOURCE ACCESS ===
        # Note: Agent can WRITE code using boto3, but can't EXECUTE it directly
        # These patterns block direct execution to protect SageMaker IAM role
        (r"boto3\.client\s*\(\s*['\"]s3['\"]", "S3 access - I'll provide code for you to run"),
        (r"boto3\.resource\s*\(\s*['\"]s3['\"]", "S3 access - I'll provide code for you to run"),
        (r"boto3\.client\s*\(\s*['\"]dynamodb['\"]", "DynamoDB access - I'll provide code for you to run"),
        (r"boto3\.client\s*\(\s*['\"]lambda['\"]", "Lambda access - I'll provide code for you to run"),
        (r"boto3\.client\s*\(\s*['\"]iam['\"]", "IAM access - restricted for security"),
        (r"boto3\.client\s*\(\s*['\"]sts['\"]", "STS access - restricted for security"),
        (r"boto3\.client\s*\(\s*['\"]secretsmanager['\"]", "Secrets Manager - restricted"),
        (r"boto3\.client\s*\(\s*['\"]ssm['\"]", "Systems Manager - restricted"),
        (r"boto3\.client\s*\(\s*['\"]kms['\"]", "KMS access - restricted"),
        (r"boto3\.client\s*\(\s*['\"]ec2['\"]", "EC2 access - restricted"),
        (r"boto3\.client\s*\(\s*['\"]rds['\"]", "RDS access - restricted"),

        # === ENVIRONMENT/CREDENTIALS ===
        (r"\bos\.environ\s*\[\s*['\"]AWS_", "Access AWS credentials from env"),
        (r"\bos\.getenv\s*\(\s*['\"]AWS_", "Get AWS credentials from env"),
        (r"\bos\.environ\.get\s*\(\s*['\"]AWS_", "Get AWS credentials from env"),

        # === SUBPROCESS (blocks all subprocess execution, not just shell=True) ===
        (r"\bsubprocess\.(run|Popen|call|check_output|check_call)\s*\(", "subprocess execution - blocked"),

        # === NETWORK ===
        (r"\bctypes\.", "ctypes - low-level access"),
        (r"\bsocket\..*bind\s*\(", "Network server binding"),
        (r"\bsocket\..*listen\s*\(", "Network listening"),
        (r"\bsocket\..*connect\s*\(", "Network connection - blocked for security"),
        (r"\brequests\.(get|post|put|delete|patch|head)\s*\(", "HTTP request - blocked for security"),
        (r"\burllib\.request\.(urlopen|urlretrieve)\s*\(", "HTTP request - blocked for security"),
        (r"\bhttp\.client\.HTTP", "HTTP client - blocked for security"),
        (r"\bhttpx\.", "httpx HTTP client - blocked for security"),
        (r"\baiohttp\.", "aiohttp HTTP client - blocked for security"),
        (r"\burllib3\.", "urllib3 HTTP client - blocked for security"),
        (r"169\.254\.169\.254", "EC2 metadata endpoint - blocked for security"),
        (r"\brequests\.(get|post).*verify\s*=\s*False", "Disable SSL verification"),
        (r"\burllib.*verify\s*=\s*False", "Disable SSL verification"),

        # === DESERIALIZATION ===
        (r"\bpickle\.loads?\s*\(", "pickle - deserialization attack risk"),
        (r"\byaml\.load\s*\([^,)]+\)$", "yaml.load without Loader (unsafe)"),

        # === OTHER ===
        (r"\bgetattr\s*\(.*,\s*['\"]__", "Access dunder attributes"),
    ]

    # Allowed AWS services for this agent (can be expanded)
    # Agent can WRITE code for these, just can't execute directly
    ALLOWED_AWS_HINT = """
To access AWS resources, I'll provide code you can run:
- S3: I'll write boto3 code for you to execute
- DynamoDB: I'll write boto3 code for you to execute
- Other AWS services: I'll provide code snippets

This protects the SageMaker IAM role from unintended access.
"""

    NETWORK_COMMANDS = ["curl", "wget", "nc", "netcat", "ssh", "scp", "rsync", "ftp", "telnet"]

    # Baseline allowlist: only these base commands can be executed via bash tool.
    # Anything not on this list is blocked regardless of denylist patterns.
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
    }

    INTERPRETER_COMMANDS = {"python", "python3", "node", "ruby", "go", "cargo", "rustc", "javac", "java"}
    CONTAINER_COMMANDS = {"docker", "docker-compose"}

    def __init__(
        self,
        workspace: str,
        allow_network: bool = False,
        allow_interpreters: bool = False,
        allow_docker: bool = False,
    ):
        self.workspace = Path(workspace).resolve()
        self.allow_network = allow_network
        self.ALLOWED_COMMANDS = set(self.BASE_ALLOWED_COMMANDS)
        if allow_interpreters:
            self.ALLOWED_COMMANDS.update(self.INTERPRETER_COMMANDS)
        if allow_docker:
            self.ALLOWED_COMMANDS.update(self.CONTAINER_COMMANDS)

    def validate_path(self, path: str) -> Tuple[bool, str]:
        """Check if path is within workspace."""
        try:
            if not os.path.isabs(path):
                resolved = (self.workspace / path).resolve()
            else:
                resolved = Path(path).resolve()

            try:
                resolved.relative_to(self.workspace)
            except ValueError:
                return False, f"Path outside workspace: {path}"

            if resolved.name in self.SENSITIVE_FILES:
                return False, f"Access to sensitive file blocked: {resolved.name}"

            for part in resolved.parts:
                if part.startswith(".env"):
                    return False, f"Access to .env file blocked"

            return True, "OK"
        except Exception as e:
            return False, f"Invalid path: {e}"

    def _extract_base_command(self, command: str) -> list:
        """Extract base command names from all shell segments.
        Handles env var prefixes and command chains/pipes (; | && || &)."""
        stripped = command.strip()
        if not stripped:
            return []

        # Split on common shell command separators so every executed segment is validated.
        segments = re.split(r'\s*(?:\|\||&&|[|;\n]|(?<![<>])&(?![>]))\s*', stripped)
        bases = []
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue

            # Strip leading env assignments like VAR=val cmd or A=1 B=2 cmd
            seg = re.sub(r'^(?:\s*[\w.:-]+=\S+\s+)+', '', seg).strip()
            if not seg:
                continue

            try:
                parts = shlex.split(seg)
            except ValueError:
                parts = seg.split()
            if not parts:
                continue

            # basename only: /usr/bin/git -> git
            bases.append(Path(parts[0]).name)
        return bases

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Check if bash command is safe.
        Layer 1: Allowlist - base command must be in ALLOWED_COMMANDS
        Layer 2: Denylist - regex patterns block dangerous argument patterns
        Layer 3: Network - block network commands unless explicitly allowed
        """
        # === LAYER 1: Command allowlist ===
        bases = self._extract_base_command(command)
        if not bases:
            return False, "Empty command"
        for base in bases:
            if base not in self.ALLOWED_COMMANDS:
                return False, f"Command not allowed: '{base}'. Allowed: {', '.join(sorted(self.ALLOWED_COMMANDS))}"

        # === LAYER 2: Denylist patterns (catch dangerous arguments/patterns) ===
        for pattern, reason in self.DANGEROUS_PATTERNS:
            try:
                if re.search(pattern, command, re.IGNORECASE):
                    return False, f"Blocked: {reason}"
            except re.error:
                continue

        # === LAYER 3: Network commands ===
        if not self.allow_network:
            for cmd in self.NETWORK_COMMANDS:
                if re.search(rf"\b{cmd}\b", command):
                    return False, f"Network command blocked: {cmd}"

        return True, "OK"

    # Modules allowed in python_exec. Anything not here is blocked at import time.
    ALLOWED_PYTHON_MODULES = {
        # Standard library - safe data processing
        "math", "statistics", "decimal", "fractions", "random", "string",
        "re", "json", "csv", "collections", "itertools", "functools",
        "datetime", "time", "calendar", "textwrap", "pprint",
        "pathlib", "io", "struct", "base64", "hashlib", "hmac",
        "copy", "typing", "dataclasses", "enum", "abc",
        "operator", "bisect", "heapq", "array",
        "difflib", "unicodedata", "html", "xml",
        # File I/O (workspace-restricted by other controls)
        "os", "os.path", "glob", "fnmatch", "shutil",
        # Data science / analysis
        "numpy", "pandas", "scipy", "sklearn",
        "matplotlib", "matplotlib.pyplot", "seaborn",
        "plotly", "altair",
        # Document creation
        "openpyxl", "xlsxwriter", "docx",
        "PIL", "reportlab", "fpdf",
        # Misc safe
        "tabulate", "yaml", "toml", "configparser",
        "logging", "warnings", "traceback", "inspect",
        "argparse", "textwrap",
    }

    # Modules explicitly blocked (even if someone tries to sneak them in)
    BLOCKED_PYTHON_MODULES = {
        "subprocess", "os.system", "shlex",
        "socket", "http", "urllib", "urllib3", "requests", "httpx", "aiohttp",
        "asyncio",  # can be used to run network code
        "ctypes", "cffi",  # FFI
        "pickle", "shelve", "marshal",  # deserialization
        "importlib", "runpy",  # dynamic imports
        "code", "codeop", "compileall",  # code execution
        "multiprocessing", "concurrent",  # process spawning
        "signal",  # signal manipulation
        "boto3", "botocore",  # AWS SDK
        "google.cloud", "azure",  # cloud SDKs
    }

    # Dangerous members that are blocked even when module is generally allowed.
    BLOCKED_PYTHON_MEMBERS = {
        "os": {"system", "popen", "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe", "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe", "startfile"},
        "shutil": {"rmtree"},
        "pathlib": {"Path.unlink", "Path.rmdir"},
    }

    def validate_python(self, code: str) -> Tuple[bool, str]:
        """Check if Python code is safe using regex denylist + AST import allowlist."""
        # Layer 1: Regex denylist (catches obfuscated patterns like __import__, exec, etc.)
        for pattern, reason in self.DANGEROUS_PYTHON:
            try:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    return False, reason
            except re.error:
                continue

        # Layer 2: AST-based import validation (ALLOWLIST - not just denylist)
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # If code can't parse, let it fail at runtime
            return True, "OK"

        alias_to_module = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    # Check denylist first (explicit block with clear message)
                    if mod in self.BLOCKED_PYTHON_MODULES or alias.name in self.BLOCKED_PYTHON_MODULES:
                        return False, f"Blocked import: {alias.name}"
                    # Then check allowlist (must be explicitly allowed)
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

        # Layer 3: AST call validation for blocked members and aliases.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            # Pattern: os.system(...)
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                base_name = node.func.value.id
                resolved = alias_to_module.get(base_name, base_name)
                top = resolved.split(".")[0]
                attr = node.func.attr
                if top in self.BLOCKED_PYTHON_MEMBERS and attr in self.BLOCKED_PYTHON_MEMBERS[top]:
                    return False, f"Blocked call: {top}.{attr}()"

            # Pattern: from os import system as s; s(...)
            if isinstance(node.func, ast.Name):
                resolved = alias_to_module.get(node.func.id, "")
                if resolved.startswith("os.") and resolved.split(".", 1)[1] in self.BLOCKED_PYTHON_MEMBERS["os"]:
                    return False, f"Blocked call via imported alias: {resolved}()"

        return True, "OK"

    def scan_secrets(self, content: str) -> List[Dict]:
        """Scan for potential secrets."""
        findings = []
        for pattern, secret_type in self.SECRET_PATTERNS:
            try:
                matches = re.findall(pattern, content)
                if matches:
                    findings.append({"type": secret_type, "count": len(matches)})
            except re.error:
                continue
        return findings

    def truncate_output(self, output: str, max_size: int = None, use_smart: bool = True) -> str:
        """Truncate output using smart truncation (saves full to disk if large)."""
        if use_smart:
            truncated, was_truncated, saved_path = Truncation.truncate(output)
            return truncated
        else:
            # Simple char-based truncation
            max_size = max_size or CONFIG.max_output_chars
            if len(output) <= max_size:
                return output
            return output[:max_size] + f"\n[Truncated - {len(output):,} chars total]"

# Initialize security
SECURITY = SecurityManager(
    CONFIG.workspace,
    allow_interpreters=CONFIG.bash_allow_interpreters,
    allow_docker=CONFIG.bash_allow_docker,
)


# ============================================================
# AUDIT LOGGING
# ============================================================

@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: str
    session_id: str
    action: str
    tool_name: Optional[str]
    parameters: Dict[str, Any]
    result_summary: str
    user_approved: bool
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = f"{self.timestamp}|{self.session_id}|{self.action}|{self.tool_name}|{self.result_summary}"
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:32]


class AuditLogger:
    """Immutable audit trail with integrity verification."""

    SENSITIVE_KEYS = {"password", "secret", "key", "token", "credential", "api_key", "auth", "bearer", "private"}

    def __init__(self, audit_dir: str):
        self.audit_dir = audit_dir
        os.makedirs(audit_dir, exist_ok=True)
        self.prune_old_logs(CONFIG.audit_retention_days)

    def _get_log_path(self, session_id: str) -> str:
        date = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.audit_dir, f"{date}_{session_id}.jsonl")

    def log(self, session_id: str, action: str, tool_name: str = None,
            parameters: Dict = None, result_summary: str = "", user_approved: bool = True):
        """Log an action to audit trail."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            action=action,
            tool_name=tool_name,
            parameters=self._sanitize_params(parameters or {}),
            result_summary=result_summary[:500] if result_summary else "",
            user_approved=user_approved,
        )
        log_path = self._get_log_path(session_id)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

    def _sanitize_params(self, params: Dict) -> Dict:
        """Remove sensitive data from parameters."""
        sanitized = {}
        for k, v in params.items():
            if any(s in k.lower() for s in self.SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 1000:
                sanitized[k] = f"[{len(v)} chars]"
            else:
                sanitized[k] = v
        return sanitized

    def get_session_log(self, session_id: str) -> List[Dict]:
        """Get all entries for a session."""
        entries = []
        for filename in os.listdir(self.audit_dir):
            if session_id in filename and filename.endswith(".jsonl"):
                path = os.path.join(self.audit_dir, filename)
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
        return sorted(entries, key=lambda x: x.get("timestamp", ""))

    def prune_old_logs(self, retention_days: int):
        """Delete audit logs older than retention_days based on filename date prefix."""
        if retention_days <= 0:
            return
        cutoff = datetime.now().date() - timedelta(days=retention_days)
        for filename in os.listdir(self.audit_dir):
            if not filename.endswith(".jsonl"):
                continue
            date_str = filename.split("_", 1)[0]
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                try:
                    os.remove(os.path.join(self.audit_dir, filename))
                except OSError:
                    pass

# Initialize audit
AUDIT = AuditLogger(CONFIG.audit_dir)


# ============================================================
# BEDROCK CLIENT
# ============================================================

import boto3

@dataclass
class ToolCall:
    id: str
    name: str
    input: dict

@dataclass
class Response:
    text: str
    tool_calls: List[ToolCall]
    stop_reason: str
    usage: dict
    thinking: str = ""  # Extended thinking content (if enabled)


class BedrockClient:
    """AWS Bedrock Claude client with mock mode for testing."""

    def __init__(self, model_id: str, region: str, mock_mode: bool = False):
        self.model_id = model_id
        self.region = region
        self.mock_mode = mock_mode
        if not mock_mode:
            self.client = boto3.client("bedrock-runtime", region_name=region)
        else:
            self.client = None
            print("[MOCK MODE] No API calls will be made")

    def _mock_response(self, messages, tools) -> Response:
        """Generate mock response for testing."""
        last = messages[-1]["content"] if messages else ""
        if isinstance(last, str):
            low = last.lower()
            if "list" in low and ("file" in low or "dir" in low):
                return Response("I'll list the files.", [ToolCall("m1", "list_dir", {"path": "."})], "tool_use", {})
            if "read" in low:
                return Response("I'll read that file.", [ToolCall("m2", "read_file", {"file_path": "README.md"})], "tool_use", {})
            if "create" in low and "excel" in low:
                return Response("I'll create an Excel file.", [ToolCall("m3", "create_excel", {"filepath": "test.xlsx", "data": [{"name": "Alice", "age": 30}]})], "tool_use", {})
            if "todo" in low:
                return Response("I'll track these tasks.", [ToolCall("m4", "todo_write", {"todos": [{"content": "Sample task", "status": "pending", "activeForm": "Working on sample task"}]})], "tool_use", {})
        return Response(f"[MOCK] Received: {str(last)[:100]}...", [], "end_turn", {"input_tokens": 100, "output_tokens": 50})

    def chat(
        self,
        messages: List[Dict],
        system: str,
        tools: List[Dict] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
    ) -> Response:
        """Send chat request to Bedrock.

        Args:
            messages: Conversation messages
            system: System prompt
            tools: Tool definitions
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0.0-1.0)
            thinking_enabled: Enable extended thinking mode
            thinking_budget: Max tokens for thinking (1024-16000)
        """
        if self.mock_mode:
            return self._mock_response(messages, tools)

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }

        # Extended thinking mode (requires temperature=1)
        if thinking_enabled:
            body["thinking"] = {
                "type": "enabled",
                "budget_tokens": min(max(thinking_budget, 1024), 16000)
            }
            body["temperature"] = 1  # Required for thinking mode
        else:
            body["temperature"] = temperature

        if tools:
            body["tools"] = tools

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json"
        )
        result = json.loads(response["body"].read())
        return self._parse(result)

    def _parse(self, result: dict) -> Response:
        """Parse Bedrock response."""
        text = ""
        thinking = ""
        tool_calls = []
        for block in result.get("content", []):
            block_type = block.get("type")
            if block_type == "text":
                text += block.get("text", "")
            elif block_type == "thinking":
                thinking += block.get("thinking", "")
            elif block_type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.get("id", ""),
                    name=block.get("name", ""),
                    input=block.get("input", {})
                ))
        return Response(text, tool_calls, result.get("stop_reason", ""), result.get("usage", {}), thinking)


# ============================================================
# SESSION MANAGEMENT
# ============================================================

@dataclass
class Session:
    """Conversation session."""
    id: str
    created_at: str
    updated_at: str
    title: str
    messages: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    todos: List[Dict] = field(default_factory=list)  # Persistent todos (OpenCode-style)


class SessionManager:
    """Persistent session storage."""

    def __init__(self, sessions_dir: str):
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)

    def create(self, title: str = "New Session") -> Session:
        """Create new session."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        now = datetime.now().isoformat()
        session = Session(id=session_id, created_at=now, updated_at=now, title=title, messages=[], metadata={})
        self.save(session)
        return session

    def save(self, session: Session):
        """Save session to disk."""
        session.updated_at = datetime.now().isoformat()
        path = os.path.join(self.sessions_dir, f"{session.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(session), f, indent=2)

    def load(self, session_id: str) -> Optional[Session]:
        """Load session from disk."""
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Filter to known fields to handle schema changes gracefully
            known_fields = {"id", "created_at", "updated_at", "title", "messages", "metadata", "todos"}
            return Session(**{k: v for k, v in data.items() if k in known_fields})
        except Exception:
            return None

    def list_sessions(self) -> List[Dict]:
        """List all sessions."""
        sessions = []
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.sessions_dir, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append({"id": data["id"], "title": data["title"], "updated_at": data["updated_at"]})
                except:
                    continue
        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)

    def delete(self, session_id: str) -> bool:
        """Delete session."""
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

# Initialize session manager
SESSIONS = SessionManager(CONFIG.sessions_dir)


# ============================================================
# SKILLS (V4)
# ============================================================

class SkillManager:
    """Simple local skill loader (.md files) from a workspace-relative directory."""

    def __init__(self, workspace: str, skills_dir: str):
        self.workspace = Path(workspace).resolve()
        self.skills_dir = (self.workspace / skills_dir).resolve() if not os.path.isabs(skills_dir) else Path(skills_dir).resolve()
        os.makedirs(self.skills_dir, exist_ok=True)

    def list_skills(self) -> List[Dict]:
        skills = []
        for fp in sorted(self.skills_dir.glob("*.md")):
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
                first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
                rel = str(fp.relative_to(self.workspace)) if self.workspace in fp.parents or fp == self.workspace else str(fp)
                skills.append({"name": fp.stem, "path": rel, "summary": first[:120]})
            except Exception:
                continue
        return skills

    def read_skill(self, name: str, max_chars: int = 12000) -> Tuple[bool, str]:
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "", str(name or ""))
        if not safe:
            return False, "Invalid skill name"
        fp = self.skills_dir / f"{safe}.md"
        if not fp.exists():
            return False, f"Skill not found: {safe}"
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
            return True, text[:max_chars]
        except Exception as e:
            return False, f"Failed reading skill: {e}"

# Initialize skills manager
SKILLS = SkillManager(CONFIG.workspace, CONFIG.skills_dir)


# ============================================================
# CONTEXT MANAGER
# ============================================================

class ContextManager:
    """Monitors context usage and provides warnings."""

    def __init__(self, max_tokens: int = 200000):
        self.max_tokens = max_tokens
        self.last_warning_level = 0

    def estimate_tokens(self, messages: List[Dict]) -> int:
        """Estimate tokens (4 chars = 1 token)."""
        total_chars = 0
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        total_chars += len(str(block.get("text", "")))
                        total_chars += len(str(block.get("content", "")))
                    else:
                        total_chars += len(str(block))
            else:
                total_chars += len(str(content))
        return total_chars // 4

    def get_usage(self, messages: List[Dict]) -> Dict:
        """Get context usage stats."""
        tokens = self.estimate_tokens(messages)
        percent = tokens / self.max_tokens
        return {
            "tokens": tokens,
            "max_tokens": self.max_tokens,
            "percent": percent,
            "level": "critical" if percent >= 0.95 else "high" if percent >= 0.90 else "medium" if percent >= 0.80 else "normal"
        }

    def check_and_warn(self, messages: List[Dict]) -> Optional[str]:
        """Check context and return warning if needed."""
        usage = self.get_usage(messages)
        percent = usage["percent"]
        tokens = usage["tokens"]

        if percent >= 0.95 and self.last_warning_level < 95:
            self.last_warning_level = 95
            return f"[!] Context at 95% ({tokens:,}/{self.max_tokens:,} tokens). Compaction imminent!"
        elif percent >= 0.90 and self.last_warning_level < 90:
            self.last_warning_level = 90
            return f"[!] Context at 90% ({tokens:,}/{self.max_tokens:,} tokens). Approaching limit."
        elif percent >= 0.80 and self.last_warning_level < 80:
            self.last_warning_level = 80
            return f"[i] Context at 80% ({tokens:,}/{self.max_tokens:,} tokens). Consider starting fresh."
        return None

    def reset(self):
        """Reset warning level."""
        self.last_warning_level = 0

# Initialize context manager
CONTEXT = ContextManager(CONFIG.context_max_tokens)


# ============================================================
# TOKEN TRACKER
# ============================================================

class TokenTracker:
    """Tracks API token usage per message and session."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all counters."""
        self.session_input = 0
        self.session_output = 0
        self.session_total = 0
        self.last_input = 0
        self.last_output = 0
        self.api_calls = 0

    def add(self, usage: dict):
        """Add usage from API response."""
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        self.last_input = input_tokens
        self.last_output = output_tokens
        self.session_input += input_tokens
        self.session_output += output_tokens
        self.session_total = self.session_input + self.session_output
        self.api_calls += 1

    def get_last(self) -> str:
        """Get last call usage as string."""
        return f"In:{self.last_input:,} Out:{self.last_output:,}"

    def get_session(self) -> str:
        """Get session total as string."""
        return f"In:{self.session_input:,} Out:{self.session_output:,} Total:{self.session_total:,}"

    def get_stats(self) -> dict:
        """Get full stats."""
        return {
            "session_input": self.session_input,
            "session_output": self.session_output,
            "session_total": self.session_total,
            "last_input": self.last_input,
            "last_output": self.last_output,
            "api_calls": self.api_calls,
        }

# Initialize token tracker
TOKENS = TokenTracker()


# ============================================================
# ALL TOOLS (15 TOOLS)
# ============================================================

# Global state
_TODOS = []  # Will be synced to ui_state["todos"] for persistence
_FILES_READ = set()

# ============== FILE OPERATIONS ==============

def tool_read_file(args: Dict) -> str:
    """Read a file with line numbers. Uses cache and smart truncation for token efficiency."""
    path = args["file_path"]
    offset = args.get("offset", 0)
    limit = args.get("limit", 500)

    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    if not os.path.isabs(path):
        path = os.path.join(CONFIG.workspace, path)

    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    abs_path = os.path.abspath(path)

    # DEDUP: If file already in context and no offset specified, return hint
    if FILE_CACHE.is_in_context(abs_path) and offset == 0:
        return f"[File already in context: {os.path.basename(path)}]\n[Use offset parameter to read specific sections, or grep to search.]"

    try:
        # Try cache first
        cached_content = FILE_CACHE.get(abs_path)
        if cached_content is not None:
            lines = cached_content.split('\n')
            cache_hit = True
        else:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            lines = content.split('\n')
            FILE_CACHE.put(abs_path, content)
            cache_hit = False

        _FILES_READ.add(abs_path)
        FILE_CACHE.mark_in_context(abs_path)

        # Select lines with offset/limit
        total_lines = len(lines)
        selected = lines[offset:offset + limit]
        result = []
        for i, line in enumerate(selected, start=offset + 1):
            if len(line) > 2000:
                line = line[:2000] + "..."
            result.append(f"{i:4}| {line}")

        output = "\n".join(result)

        # Add file info header
        header = f"[{os.path.basename(path)}] "
        if cache_hit:
            header += "[cached] "
        header += f"Lines {offset+1}-{offset+len(selected)} of {total_lines}"
        if offset + limit < total_lines:
            header += f" [use offset={offset+limit} for more]"

        # Smart truncation if output is large
        full_output = f"{header}\n{output}"
        truncated, was_truncated = Truncation.smart_truncate(full_output, head_lines=100, tail_lines=50)

        return SECURITY.truncate_output(truncated)
    except Exception as e:
        return f"Error reading file: {e}"


def tool_write_file(args: Dict) -> str:
    """Write content to file."""
    path = args["file_path"]
    content = args["content"]

    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    if not os.path.isabs(path):
        path = os.path.join(CONFIG.workspace, path)
    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    if os.path.exists(path) and os.path.abspath(path) not in _FILES_READ:
        return "Error: Must read file before writing. Use read_file first."

    secrets = SECURITY.scan_secrets(content)
    if secrets:
        types = ", ".join(s["type"] for s in secrets)
        return f"Warning: Content contains potential secrets ({types}). Review before saving."

    try:
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        _FILES_READ.add(os.path.abspath(path))
        return f"Written {len(content):,} chars to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def tool_edit_file(args: Dict) -> str:
    """Edit file by replacing exact string. Returns diff-only output for token efficiency."""
    path = args["file_path"]
    old_string = args["old_string"]
    new_string = args["new_string"]
    replace_all = args.get("replace_all", False)

    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    if not os.path.isabs(path):
        path = os.path.join(CONFIG.workspace, path)
    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    abs_path = os.path.abspath(path)
    if abs_path not in _FILES_READ:
        return "Error: Must read file before editing. Use read_file first."

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        count = content.count(old_string)
        if count == 0:
            return "Error: old_string not found in file. Must be EXACT match."
        if count > 1 and not replace_all:
            return f"Error: old_string appears {count} times. Use replace_all=true or provide more context."

        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Invalidate cache for this file and clear context marker so re-read shows updated content
        FILE_CACHE.put(abs_path, new_content)
        FILE_CACHE._in_context.discard(abs_path)

        # DIFF-ONLY OUTPUT: Show only the change context, not whole file
        # Find the line number where change occurred
        lines_before = content[:content.find(old_string)].count('\n') + 1

        # Show compact diff summary
        old_preview = old_string[:100] + "..." if len(old_string) > 100 else old_string
        new_preview = new_string[:100] + "..." if len(new_string) > 100 else new_string
        old_lines = old_string.count('\n') + 1
        new_lines = new_string.count('\n') + 1

        result = f"✓ Edited {os.path.basename(path)} (line {lines_before})\n"
        result += f"  -{old_lines} lines / +{new_lines} lines"
        if count > 1 and replace_all:
            result += f" ({count} replacements)"
        result += f"\n  Old: {repr(old_preview)}\n  New: {repr(new_preview)}"

        return result
    except Exception as e:
        return f"Error editing file: {e}"


def tool_glob(args: Dict) -> str:
    """Find files by glob pattern."""
    pattern = args["pattern"]
    path = args.get("path", CONFIG.workspace)

    if not os.path.isabs(path):
        path = os.path.join(CONFIG.workspace, path)

    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    full_pattern = os.path.join(path, pattern)
    raw_matches = glob_module.glob(full_pattern, recursive=True)[:200]
    # Per-file boundary check (symlink escape protection)
    matches = [m for m in raw_matches if SECURITY.validate_path(m)[0]][:100]
    matches = sorted(matches, key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
    return "\n".join(matches) if matches else "No files found"


def tool_grep(args: Dict) -> str:
    """Search file contents with regex."""
    pattern = args["pattern"]
    path = args.get("path", CONFIG.workspace)
    glob_pattern = args.get("glob", "**/*")
    case_insensitive = args.get("case_insensitive", False)

    if not os.path.isabs(path):
        path = os.path.join(CONFIG.workspace, path)

    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    flags = re.IGNORECASE if case_insensitive else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: Invalid regex: {e}"

    results = []
    files = glob_module.glob(os.path.join(path, glob_pattern), recursive=True)

    for filepath in files:
        if not os.path.isfile(filepath) or len(results) >= 50:
            continue
        # Per-file boundary check (symlink escape protection)
        file_ok, _ = SECURITY.validate_path(filepath)
        if not file_ok:
            continue
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        results.append(f"{filepath}:{i}: {line.strip()[:100]}")
                        if len(results) >= 50:
                            break
        except:
            continue

    return "\n".join(results) if results else "No matches found"


def tool_list_dir(args: Dict) -> str:
    """List directory contents."""
    path = args.get("path", CONFIG.workspace)

    if not os.path.isabs(path):
        path = os.path.join(CONFIG.workspace, path)

    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    if not os.path.isdir(path):
        return f"Error: Not a directory: {path}"

    try:
        entries = []
        for entry in sorted(os.listdir(path))[:100]:
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                entries.append(f"[DIR]  {entry}/")
            else:
                size = os.path.getsize(full)
                entries.append(f"[FILE] {entry} ({size:,} bytes)")
        return "\n".join(entries) if entries else "(empty directory)"
    except Exception as e:
        return f"Error: {e}"


# ============== BASH ==============

# Active subprocess tracking - allows stop handler to kill running processes
_active_process = None  # type: subprocess.Popen | None
_active_process_lock = threading.Lock()
_docker_image_ready = False
_docker_image_lock = threading.Lock()

def _kill_active_process():
    """Kill the active subprocess if one is running. Called by stop handler."""
    global _active_process
    with _active_process_lock:
        if _active_process and _active_process.poll() is None:
            try:
                _active_process.kill()
            except OSError:
                pass

def _safe_exec_env() -> Dict[str, str]:
    """Build a minimally-sensitive environment for local execution."""
    blocked_markers = (
        "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL",
        "API_KEY", "PRIVATE_KEY", "AUTH",
    )
    env = {k: v for k, v in os.environ.items()
           if not any(s in k.upper() for s in blocked_markers)
           and k.upper() not in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN")}
    env["TERM"] = "dumb"
    env["PYTHONIOENCODING"] = "utf-8"
    return env

def _run_subprocess(cmd_arg, timeout: int, shell: bool, cwd: str, env: Dict[str, str] = None) -> subprocess.CompletedProcess:
    """Run subprocess with active-process tracking for Stop support."""
    global _active_process
    proc = subprocess.Popen(
        cmd_arg,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
        env=env
    )
    with _active_process_lock:
        _active_process = proc
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    finally:
        with _active_process_lock:
            _active_process = None
    return subprocess.CompletedProcess(cmd_arg, proc.returncode, stdout, stderr)


def _ensure_docker_image_ready() -> None:
    """Ensure docker image exists locally so first pull time doesn't count against exec budget."""
    global _docker_image_ready
    if CONFIG.execution_mode != "docker":
        return
    if _docker_image_ready:
        return

    with _docker_image_lock:
        if _docker_image_ready:
            return

        inspect_cmd = ["docker", "image", "inspect", CONFIG.exec_docker_image]
        inspect = _run_subprocess(
            inspect_cmd,
            timeout=20,
            shell=False,
            cwd=CONFIG.workspace,
            env=_safe_exec_env(),
        )
        if inspect.returncode != 0:
            pull_cmd = ["docker", "pull", CONFIG.exec_docker_image]
            pull = _run_subprocess(
                pull_cmd,
                timeout=240,
                shell=False,
                cwd=CONFIG.workspace,
                env=_safe_exec_env(),
            )
            if pull.returncode != 0:
                err = (pull.stderr or pull.stdout or "docker pull failed").strip()
                raise RuntimeError(f"Docker image unavailable: {err[:200]}")
        _docker_image_ready = True


def _validate_shell_redirections(command: str) -> Tuple[bool, str]:
    """Validate shell redirection targets stay inside workspace."""
    try:
        tokens = shlex.split(command, posix=(os.name != "nt"))
    except ValueError:
        # If parsing fails, block rather than guessing redirection targets.
        return False, "invalid shell syntax for redirection validation"

    redir_ops = {">", ">>", "<", "1>", "1>>", "2>", "2>>", "&>", "&>>"}
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        target = None

        # File descriptor duplication like 2>&1 or 0<&1 is safe and has no path target.
        if re.match(r"^\d*(?:<|>)&\d+$", token):
            idx += 1
            continue

        # Heredoc markers are inline literals, not filesystem paths.
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

def _docker_base_cmd() -> List[str]:
    """Build hardened docker run args for isolated command execution."""
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
        cmd.extend(["--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m"])
    return cmd

def tool_bash(args: Dict) -> str:
    """Execute shell command with allowlist enforcement and no shell=True."""
    global _active_process
    command = args["command"]
    timeout = min(args.get("timeout", 120), 600)

    ok, msg = SECURITY.validate_command(command)
    if not ok:
        return f"Blocked: {msg}"

    try:
        if CONFIG.execution_mode == "docker":
            docker_cmd = _docker_base_cmd()
            docker_cmd.extend([CONFIG.exec_docker_image, "sh", "-lc", command])
            result = _run_subprocess(docker_cmd, timeout=timeout, shell=False, cwd=CONFIG.workspace, env=_safe_exec_env())
        else:
            # Detect shell operators that require shell=True in local mode
            needs_shell = bool(re.search(r'[|><;]|&&|\|\||`|\$\(', command))
            if needs_shell:
                redir_ok, redir_msg = _validate_shell_redirections(command)
                if not redir_ok:
                    return f"Blocked: {redir_msg}"
                cmd_arg = command
                use_shell = True
            else:
                try:
                    cmd_arg = shlex.split(command)
                except ValueError:
                    cmd_arg = command.split()
                use_shell = False
            result = _run_subprocess(cmd_arg, timeout=timeout, shell=use_shell, cwd=CONFIG.workspace, env=_safe_exec_env())

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"

        if not output:
            return "(no output)"

        # Smart truncation for large outputs
        truncated, was_truncated = Truncation.smart_truncate(output, head_lines=100, tail_lines=50)
        return SECURITY.truncate_output(truncated)
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {e}"


# ============== PYTHON EXECUTION ==============

# Runtime import hook prepended to all python_exec code.
# Uses ALLOWLIST: only permitted modules can be imported. Everything else is blocked.
_PYTHON_EXEC_PREAMBLE = '''
import builtins as _builtins
_original_import = _builtins.__import__
_ALLOWED = {
    # Standard library - safe data processing
    "math", "statistics", "decimal", "fractions", "random", "string",
    "re", "json", "csv", "collections", "itertools", "functools",
    "datetime", "time", "calendar", "textwrap", "pprint",
    "pathlib", "io", "struct", "base64", "hashlib", "hmac",
    "copy", "typing", "dataclasses", "enum", "abc",
    "operator", "bisect", "heapq", "array",
    "difflib", "unicodedata", "html", "xml",
    # File I/O
    "os", "glob", "fnmatch", "shutil",
    # Data science
    "numpy", "pandas", "scipy", "sklearn",
    "matplotlib", "seaborn", "plotly", "altair",
    # Document creation
    "openpyxl", "xlsxwriter", "docx",
    "PIL", "reportlab", "fpdf",
    # Misc safe
    "tabulate", "yaml", "toml", "configparser",
    "logging", "warnings", "traceback", "inspect",
    "argparse", "numbers", "contextlib",
    # Internal (needed by allowed packages)
    "builtins", "_thread", "_io", "_collections", "_operator",
    "encodings", "codecs", "_codecs", "_signal", "_abc",
    "_stat", "_weakref", "_functools", "_locale",
    "posixpath", "ntpath", "genericpath", "stat",
    "sys", "types", "zipimport", "_frozen_importlib",
    "_frozen_importlib_external", "_bootlocale",
}
def _safe_import(name, *args, **kwargs):
    top = name.split(".")[0]
    if top in _ALLOWED:
        return _original_import(name, *args, **kwargs)
    raise ImportError(f"Security: import '{name}' is not in the allowed modules list")
_builtins.__import__ = _safe_import
del _builtins, _original_import, _ALLOWED, _safe_import
'''

def tool_python_exec(args: Dict) -> str:
    """Execute Python code in sandboxed subprocess with import restrictions."""
    global _active_process
    code = args["code"]
    timeout = min(args.get("timeout", 60), 300)

    # Security check: regex denylist + AST import validation
    ok, msg = SECURITY.validate_python(code)
    if not ok:
        return f"Security blocked: {msg}"

    fd, temp_path = tempfile.mkstemp(suffix=".py", prefix="agent_exec_", dir=CONFIG.workspace)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            # Prepend runtime import hook, then user code
            f.write(_PYTHON_EXEC_PREAMBLE)
            f.write(code)

        if CONFIG.execution_mode == "docker":
            rel = os.path.relpath(temp_path, CONFIG.workspace).replace("\\", "/")
            docker_cmd = _docker_base_cmd()
            docker_cmd.extend([CONFIG.exec_docker_image, "python", "-I", f"/workspace/{rel}"])
            result = _run_subprocess(docker_cmd, timeout=timeout, shell=False, cwd=CONFIG.workspace, env=_safe_exec_env())
        else:
            result = _run_subprocess([sys.executable, temp_path], timeout=timeout, shell=False, cwd=CONFIG.workspace, env=_safe_exec_env())

        output = result.stdout
        stderr = result.stderr
        if stderr:
            output += f"\n[stderr]\n{stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return SECURITY.truncate_output(output) if output else "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: Code timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {e}"
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


# ============== DOCUMENT CREATION ==============

def _parse_word_content(doc, content: str, images: Dict = None):
    """Parse markdown-like content and add to Word document with styling.

    Supports:
    - # ## ### headings
    - **bold**, *italic*, ***bold-italic***
    - - bullet lists
    - 1. numbered lists
    - | tables |
    - ---PAGE--- page breaks
    - ![alt](path) or {{IMAGE:path}} image embeds
    """
    from docx.shared import Inches

    lines = content.split("\n")
    i = 0
    in_table = False
    table_data = []
    images = images or {}

    while i < len(lines):
        line = lines[i]

        # Page break
        if line.strip() == "---PAGE---":
            doc.add_page_break()
            i += 1
            continue

        # Image embed: ![alt](path) or {{IMAGE:path}}
        img_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if not img_match:
            img_match = re.match(r"\{\{IMAGE:([^}]+)\}\}", line.strip())
            if img_match:
                img_path = img_match.group(1)
                img_alt = ""
            else:
                img_path = None
        else:
            img_alt = img_match.group(1)
            img_path = img_match.group(2)

        if img_path:
            # Resolve path - strip leading ./ and normalize
            img_path = img_path.lstrip("./").lstrip(".\\")
            if not os.path.isabs(img_path):
                img_path = os.path.join(CONFIG.workspace, img_path)
            img_path = os.path.normpath(img_path)
            # Validate image path is within workspace
            img_ok, img_msg = SECURITY.validate_path(img_path)
            if not img_ok:
                doc.add_paragraph(f"[Image blocked: {img_msg}]")
                i += 1
                continue
            if os.path.exists(img_path):
                try:
                    doc.add_picture(img_path, width=Inches(5.5))
                    if img_alt:
                        caption = doc.add_paragraph(img_alt)
                        caption.alignment = 1  # Center
                except Exception as e:
                    doc.add_paragraph(f"[Image error: {e}]")
            else:
                doc.add_paragraph(f"[Image not found: {img_path}]")
            i += 1
            continue

        # Headings
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
            i += 1
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
            i += 1
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
            i += 1
            continue

        # Table detection - more robust: detect any line with | separators
        stripped = line.strip()
        # Match: | col1 | col2 | OR col1 | col2 (without leading |)
        is_table_line = (stripped.startswith("|") and "|" in stripped[1:]) or \
                        ("|" in stripped and re.match(r'^[^|]+\|.+$', stripped))

        if is_table_line:
            if not in_table:
                in_table = True
                table_data = []
            # Normalize: ensure leading/trailing | for consistent parsing
            if not stripped.startswith("|"):
                stripped = "|" + stripped
            if not stripped.endswith("|"):
                stripped = stripped + "|"
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            # Skip separator lines (all dashes/colons)
            if not all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                table_data.append(cells)
            i += 1
            continue
        elif in_table:
            if table_data:
                _add_word_table(doc, table_data)
            in_table = False
            table_data = []

        # Bullet list
        if line.strip().startswith("- "):
            para = doc.add_paragraph(style="List Bullet")
            _add_formatted_run(para, line.strip()[2:])
            i += 1
            continue

        # Numbered list
        match = re.match(r"^\d+\.\s+", line.strip())
        if match:
            para = doc.add_paragraph(style="List Number")
            _add_formatted_run(para, line.strip()[match.end():])
            i += 1
            continue

        # Regular paragraph
        if line.strip():
            para = doc.add_paragraph()
            _add_formatted_run(para, line.strip())

        i += 1

    if in_table and table_data:
        _add_word_table(doc, table_data)


def _add_formatted_run(paragraph, text: str):
    """Add text with bold/italic formatting."""
    pattern = r"(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*)"
    parts = re.split(pattern, text)
    for part in parts:
        if not part:
            continue
        if part.startswith("***") and part.endswith("***"):
            run = paragraph.add_run(part[3:-3])
            run.bold = True
            run.italic = True
        elif part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*") and part.endswith("*"):
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        else:
            paragraph.add_run(part)


def _add_word_table(doc, table_data: list):
    """Add styled table to document."""
    if not table_data:
        return
    rows = len(table_data)
    cols = max(len(row) for row in table_data)
    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"
    for i, row_data in enumerate(table_data):
        row = table.rows[i]
        for j, cell_text in enumerate(row_data):
            if j < cols:
                cell = row.cells[j]
                cell.text = cell_text
                if i == 0:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.bold = True
    doc.add_paragraph()


def tool_create_word(args: Dict) -> str:
    """Create Word document with rich styling."""
    filepath = args["filepath"]
    content = args["content"]
    title = args.get("title", "")
    include_toc = args.get("include_toc", False)
    header_text = args.get("header", "")
    footer_text = args.get("footer", "")

    if not os.path.isabs(filepath):
        filepath = os.path.join(CONFIG.workspace, filepath)
    if not filepath.endswith(".docx"):
        filepath += ".docx"

    ok, msg = SECURITY.validate_path(filepath)
    if not ok:
        return f"Error: {msg}"

    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        doc = Document()

        # Header
        if header_text:
            section = doc.sections[0]
            header = section.header
            header.paragraphs[0].text = header_text
            header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Footer
        if footer_text:
            section = doc.sections[0]
            footer = section.footer
            footer.paragraphs[0].text = footer_text
            footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Title
        if title:
            title_para = doc.add_heading(title, 0)
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Table of Contents
        if include_toc:
            doc.add_paragraph("Table of Contents", style="Heading 1")
            para = doc.add_paragraph()
            run = para.add_run()
            fld_begin = OxmlElement('w:fldChar')
            fld_begin.set(qn('w:fldCharType'), 'begin')
            run._r.append(fld_begin)
            run = para.add_run()
            instr = OxmlElement('w:instrText')
            instr.text = 'TOC \\o "1-3" \\h \\z \\u'
            run._r.append(instr)
            run = para.add_run()
            fld_end = OxmlElement('w:fldChar')
            fld_end.set(qn('w:fldCharType'), 'end')
            run._r.append(fld_end)
            doc.add_paragraph("[Right-click TOC → Update Field]")
            doc.add_page_break()

        # Parse content with styling
        _parse_word_content(doc, content)

        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        doc.save(filepath)

        features = []
        if include_toc:
            features.append("TOC")
        if header_text:
            features.append("header")
        if footer_text:
            features.append("footer")
        feat_str = f" (with {', '.join(features)})" if features else ""
        return f"Created Word document: {filepath}{feat_str}"

    except ImportError:
        return "Error: python-docx not installed. Run: pip install python-docx"
    except Exception as e:
        return f"Error: {e}"


def tool_create_excel(args: Dict) -> str:
    """Create Excel spreadsheet with optional chart."""
    filepath = args["filepath"]
    data = args["data"]
    sheet_name = args.get("sheet_name", "Sheet1")
    chart_type = args.get("chart_type")  # Optional: bar, line, pie
    chart_title = args.get("chart_title", "Chart")
    x_column = args.get("x_column")  # Column name for X axis
    y_columns = args.get("y_columns", [])  # Column names for Y axis

    if not os.path.isabs(filepath):
        filepath = os.path.join(CONFIG.workspace, filepath)
    if not filepath.endswith(".xlsx"):
        filepath += ".xlsx"

    ok, msg = SECURITY.validate_path(filepath)
    if not ok:
        return f"Error: {msg}"

    try:
        import pandas as pd
        from openpyxl import Workbook
        from openpyxl.utils.dataframe import dataframe_to_rows

        df = pd.DataFrame(data)
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # Create workbook with pandas writer for chart support
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Add chart if requested
            if chart_type and x_column and y_columns:
                from openpyxl.chart import BarChart, LineChart, PieChart, Reference
                from openpyxl.utils import get_column_letter

                ws = writer.sheets[sheet_name]

                # Determine chart class
                if chart_type == "bar":
                    chart = BarChart()
                elif chart_type == "line":
                    chart = LineChart()
                elif chart_type == "pie":
                    chart = PieChart()
                else:
                    return f"Created Excel file: {filepath} ({len(df)} rows) [chart_type '{chart_type}' not supported, use bar/line/pie]"

                chart.title = chart_title
                chart.style = 10

                # Find column indices
                cols = list(df.columns)
                x_idx = cols.index(x_column) + 1 if x_column in cols else 1

                for y_col in y_columns:
                    if y_col in cols:
                        y_idx = cols.index(y_col) + 1
                        data_ref = Reference(ws, min_col=y_idx, min_row=1, max_row=len(df)+1)
                        cats = Reference(ws, min_col=x_idx, min_row=2, max_row=len(df)+1)

                        if chart_type == "pie":
                            chart.add_data(data_ref, titles_from_data=True)
                            chart.set_categories(cats)
                        else:
                            chart.add_data(data_ref, titles_from_data=True)
                            chart.set_categories(cats)

                # Position chart
                chart.width = 15
                chart.height = 10
                anchor_col = get_column_letter(len(cols) + 2)
                ws.add_chart(chart, f"{anchor_col}2")

        return f"Created Excel file with chart: {filepath} ({len(df)} rows, {chart_type} chart)"
    except ImportError as e:
        return f"Error: pandas/openpyxl not installed. Run: pip install pandas openpyxl. ({e})"
    except Exception as e:
        return f"Error: {e}"


def tool_create_markdown(args: Dict) -> str:
    """Create Markdown file."""
    filepath = args["filepath"]
    content = args["content"]

    if not os.path.isabs(filepath):
        filepath = os.path.join(CONFIG.workspace, filepath)
    if not filepath.endswith(".md"):
        filepath += ".md"

    ok, msg = SECURITY.validate_path(filepath)
    if not ok:
        return f"Error: {msg}"

    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Created Markdown file: {filepath}"
    except Exception as e:
        return f"Error: {e}"


def tool_create_notebook(args: Dict) -> str:
    """Create a Jupyter Notebook (.ipynb) file with code and/or markdown cells."""
    filepath = args["filepath"]
    cells = args["cells"]  # List of {"type": "code"|"markdown", "source": "..."}

    if not os.path.isabs(filepath):
        filepath = os.path.join(CONFIG.workspace, filepath)
    if not filepath.endswith(".ipynb"):
        filepath += ".ipynb"

    ok, msg = SECURITY.validate_path(filepath)
    if not ok:
        return f"Error: {msg}"

    try:
        nb_cells = []
        for cell in cells:
            cell_type = cell.get("type", "code")
            source = cell.get("source", "")
            if isinstance(source, list):
                source_lines = source
            else:
                source_lines = source.split("\n") if source else [""]
                source_lines = [line + "\n" for line in source_lines[:-1]] + [source_lines[-1]]

            nb_cell = {
                "cell_type": cell_type,
                "metadata": {},
                "source": source_lines,
            }
            if cell_type == "code":
                nb_cell["execution_count"] = None
                nb_cell["outputs"] = []
            nb_cells.append(nb_cell)

        notebook = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.10.0"
                }
            },
            "cells": nb_cells,
        }

        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)
        return f"Created Jupyter Notebook: {filepath} ({len(nb_cells)} cells)"
    except Exception as e:
        return f"Error: {e}"


# ============== CHARTS & PDF ==============

def tool_create_chart(args: Dict) -> str:
    """Create chart image using matplotlib."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return "Error: matplotlib not installed. Run: pip install matplotlib"

    chart_type = args.get("chart_type", "bar")  # bar, line, pie, scatter
    title = args.get("title", "Chart")
    data = args["data"]  # {"labels": [...], "values": [...]} or {"x": [...], "y": [...]}
    filepath = args.get("filepath", "chart.png")
    xlabel = args.get("xlabel", "")
    ylabel = args.get("ylabel", "")
    colors = args.get("colors", None)

    if not os.path.isabs(filepath):
        filepath = os.path.join(CONFIG.workspace, filepath)
    if not filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.pdf')):
        filepath += ".png"

    ok, msg = SECURITY.validate_path(filepath)
    if not ok:
        return f"Error: {msg}"

    try:
        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "bar":
            labels = data.get("labels", list(range(len(data.get("values", [])))))
            values = data.get("values", [])
            bars = ax.bar(labels, values, color=colors)
            # Add value labels on bars
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val:,.0f}' if isinstance(val, (int, float)) else str(val),
                       ha='center', va='bottom', fontsize=9)

        elif chart_type == "line":
            x = data.get("x", data.get("labels", list(range(len(data.get("y", data.get("values", [])))))))
            y = data.get("y", data.get("values", []))
            ax.plot(x, y, marker='o', linewidth=2, markersize=6, color=colors[0] if colors else None)
            ax.fill_between(x, y, alpha=0.3)

        elif chart_type == "pie":
            labels = data.get("labels", [])
            values = data.get("values", [])
            ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            ax.axis('equal')

        elif chart_type == "scatter":
            x = data.get("x", [])
            y = data.get("y", [])
            ax.scatter(x, y, c=colors, alpha=0.7, s=50)

        elif chart_type == "horizontal_bar":
            labels = data.get("labels", [])
            values = data.get("values", [])
            ax.barh(labels, values, color=colors)

        else:
            return f"Error: Unknown chart type '{chart_type}'. Supported: bar, line, pie, scatter, horizontal_bar"

        ax.set_title(title, fontsize=14, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)

        plt.tight_layout()
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        # Embed chart as base64 for inline display in chat widget
        try:
            with open(filepath, "rb") as img_f:
                img_b64 = base64.b64encode(img_f.read()).decode()
            return f"Created chart: {filepath}\n[INLINE_IMAGE:{img_b64}]"
        except Exception:
            return f"Created chart: {filepath}"
    except Exception as e:
        plt.close()
        return f"Error creating chart: {e}"


def _parse_markdown_table(text: str) -> list:
    """Parse markdown table into list of lists for PDF/reportlab."""
    lines = text.strip().split("\n")
    table_data = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip separator lines (all dashes/colons)
        if re.match(r'^[\|\s\-:]+$', stripped):
            continue
        # Parse table row
        if "|" in stripped:
            # Normalize: ensure leading/trailing | for consistent parsing
            if not stripped.startswith("|"):
                stripped = "|" + stripped
            if not stripped.endswith("|"):
                stripped = stripped + "|"
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            if cells and any(c for c in cells):  # Skip empty rows
                table_data.append(cells)
    return table_data


def tool_create_pdf(args: Dict) -> str:
    """Create PDF document with text, tables, and images.

    For tables, you can provide either:
    1. Structured data: [["City", "2020"], ["Sydney", "1200000"]]
    2. Markdown table: "| City | 2020 |\\n| --- | --- |\\n| Sydney | 1200000 |"
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
    except ImportError:
        return "Error: reportlab not installed. Run: pip install reportlab"

    filepath = args.get("filepath")
    content = args.get("content")
    title = args.get("title", "Document")
    page_size = args.get("page_size", "letter")  # letter or a4

    # Validate filepath
    if not filepath or not isinstance(filepath, str):
        return "Error: 'filepath' is required and must be a string (e.g., 'report.pdf')"

    # Validate content - must be list of dicts
    if not content:
        return "Error: 'content' is required. Must be list of dicts: [{type: 'heading'|'text'|'table'|'image', data: ...}]"

    if isinstance(content, str):
        # Auto-convert string to text section
        content = [{"type": "text", "data": content}]
    elif not isinstance(content, list):
        return "Error: 'content' must be a list of sections: [{type: 'heading'|'text'|'table'|'image', data: ...}]"

    if not os.path.isabs(filepath):
        filepath = os.path.join(CONFIG.workspace, filepath)
    if not filepath.lower().endswith('.pdf'):
        filepath += ".pdf"

    ok, msg = SECURITY.validate_path(filepath)
    if not ok:
        return f"Error: {msg}"

    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        doc = SimpleDocTemplate(filepath, pagesize=letter if page_size == "letter" else A4)
        styles = getSampleStyleSheet()
        story = []

        # Add custom styles
        styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontSize=24, spaceAfter=30))
        styles.add(ParagraphStyle(name='CustomHeading', parent=styles['Heading1'], fontSize=16, spaceAfter=12))
        styles.add(ParagraphStyle(name='CustomBody', parent=styles['Normal'], fontSize=11, spaceAfter=10))

        # Add title
        story.append(Paragraph(title, styles['CustomTitle']))
        story.append(Spacer(1, 12))

        for section in content:
            # Handle string sections (auto-convert to text)
            if isinstance(section, str):
                section = {"type": "text", "data": section}
            elif not isinstance(section, dict):
                continue  # Skip invalid sections

            section_type = section.get("type", "text")
            data = section.get("data", "")

            if section_type == "heading":
                safe_heading = escape_html(str(data))
                story.append(Paragraph(safe_heading, styles['CustomHeading']))

            elif section_type == "text":
                # Handle multi-line text
                for para in str(data).split('\n\n'):
                    if para.strip():
                        safe_para = escape_html(para).replace('\n', '<br/>')
                        story.append(Paragraph(safe_para, styles['CustomBody']))

            elif section_type == "table":
                # data can be:
                # 1. list of lists: [["City", "2020"], ["Sydney", "1200000"]]
                # 2. markdown table string: "| City | 2020 |\n| --- | --- |\n| Sydney | 1200000 |"
                table_data = data
                if isinstance(data, str):
                    # Parse markdown table
                    table_data = _parse_markdown_table(data)
                if isinstance(table_data, list) and len(table_data) > 0:
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a9eff')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 12))

            elif section_type == "image":
                # data should be file path to image
                img_path = data if os.path.isabs(data) else os.path.join(CONFIG.workspace, data)
                img_ok, img_msg = SECURITY.validate_path(img_path)
                if not img_ok:
                    story.append(Paragraph(f"[Image blocked: {img_msg}]", styles["Normal"]))
                    continue
                if os.path.exists(img_path):
                    img = Image(img_path)
                    # Scale to fit page width while maintaining aspect ratio
                    orig_width = img.drawWidth
                    orig_height = img.drawHeight
                    img.drawWidth = min(orig_width, 6*inch)
                    img.drawHeight = orig_height * (img.drawWidth / orig_width)
                    story.append(img)
                    story.append(Spacer(1, 12))

            story.append(Spacer(1, 6))

        doc.build(story)
        return f"Created PDF: {filepath}"
    except Exception as e:
        return f"Error creating PDF: {e}"


# ============== VISION ==============

def tool_view_image(args: Dict) -> str:
    """Load and describe image for AI analysis."""
    path = args["file_path"]

    if not os.path.isabs(path):
        path = os.path.join(CONFIG.workspace, path)

    ok, msg = SECURITY.validate_path(path)
    if not ok:
        return f"Error: {msg}"

    if not os.path.exists(path):
        return f"Error: Image not found: {path}"

    ext = os.path.splitext(path)[1].lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
    if ext not in media_types:
        return f"Error: Unsupported format: {ext}. Supported: png, jpg, gif, webp"

    size = os.path.getsize(path)
    if size > 20 * 1024 * 1024:
        return f"Error: Image too large: {size / (1024*1024):.1f}MB (max 20MB)"

    return f"Image loaded: {path} ({size:,} bytes, {ext})"


# ============== SEMANTIC SEARCH ==============

class SemanticSearch:
    """Semantic code search using Bedrock Titan Embeddings."""

    def __init__(self, region: str = "ap-southeast-2", index_path: str = "./.code_index"):
        self.region = region
        self.index_path = index_path
        self.client = None  # Lazy init
        self.model_id = "amazon.titan-embed-text-v2:0"
        self.chunks = []

    def _ensure_client(self):
        if self.client is None:
            self.client = boto3.client("bedrock-runtime", region_name=self.region)

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text."""
        self._ensure_client()
        text = text[:8000]  # Titan limit
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({"inputText": text}),
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

    def index_codebase(self, root_dir: str, extensions: List[str] = None, chunk_size: int = 50) -> int:
        """Index all code files in directory."""
        extensions = extensions or [".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h"]
        self.chunks = []

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for filename in filenames:
                if not any(filename.endswith(ext) for ext in extensions):
                    continue
                filepath = os.path.join(dirpath, filename)
                self._index_file(filepath, chunk_size)

        self._save_index()
        return len(self.chunks)

    def _index_file(self, filepath: str, chunk_size: int = 50):
        """Split file into chunks and index each."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except IOError:
            return

        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            content = "".join(chunk_lines)
            if len(content.strip()) < 50:
                continue
            try:
                embedding = self._get_embedding(content)
                self.chunks.append({
                    "file_path": filepath,
                    "start_line": i + 1,
                    "end_line": i + len(chunk_lines),
                    "content": content,
                    "embedding": embedding,
                })
            except Exception as e:
                print(f"Warning: Failed to embed {filepath}: {e}")

    def _save_index(self):
        """Save index to disk."""
        os.makedirs(self.index_path, exist_ok=True)
        with open(os.path.join(self.index_path, "chunks.json"), "w") as f:
            json.dump(self.chunks, f)

    def _load_index(self) -> bool:
        """Load index from disk."""
        path = os.path.join(self.index_path, "chunks.json")
        if not os.path.exists(path):
            return False
        try:
            with open(path) as f:
                self.chunks = json.load(f)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Search for code matching query."""
        if not self.chunks and not self._load_index():
            return []
        query_embedding = self._get_embedding(query)
        results = []
        for chunk in self.chunks:
            if chunk.get("embedding"):
                sim = self._cosine_similarity(query_embedding, chunk["embedding"])
                results.append((chunk, sim))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def is_indexed(self) -> bool:
        """Check if codebase is indexed."""
        return os.path.exists(os.path.join(self.index_path, "chunks.json"))


# Global semantic search instance
_SEMANTIC_SEARCH = None


def tool_semantic_search(args: Dict) -> str:
    """Semantic code search using AI embeddings."""
    global _SEMANTIC_SEARCH

    action = args.get("action", "search")
    query = args.get("query", "")
    path = args.get("path", CONFIG.workspace)
    top_k = args.get("top_k", 5)

    if _SEMANTIC_SEARCH is None:
        _SEMANTIC_SEARCH = SemanticSearch(CONFIG.region, os.path.join(CONFIG.workspace, ".code_index"))

    if action == "index":
        if not os.path.isabs(path):
            path = os.path.join(CONFIG.workspace, path)
        ok, msg = SECURITY.validate_path(path)
        if not ok:
            return f"Error: {msg}"
        try:
            count = _SEMANTIC_SEARCH.index_codebase(path)
            return f"Indexed {count} code chunks from {path}"
        except Exception as e:
            return f"Error indexing: {e}"

    elif action == "search":
        if not query:
            return "Error: query is required for search"
        if not _SEMANTIC_SEARCH.is_indexed():
            return "Codebase not indexed. Run with action='index' first."
        try:
            results = _SEMANTIC_SEARCH.search(query, top_k)
            if not results:
                return "No matching code found."
            output = []
            for chunk, score in results:
                output.append(f"\n### {chunk['file_path']}:{chunk['start_line']}-{chunk['end_line']} (score: {score:.3f})")
                output.append("```")
                content = chunk['content'][:500]
                if len(chunk['content']) > 500:
                    content += "\n... (truncated)"
                output.append(content)
                output.append("```")
            return "\n".join(output)
        except Exception as e:
            return f"Error searching: {e}"

    elif action == "status":
        if _SEMANTIC_SEARCH.is_indexed():
            if not _SEMANTIC_SEARCH.chunks:
                _SEMANTIC_SEARCH._load_index()
            files = set(c["file_path"] for c in _SEMANTIC_SEARCH.chunks)
            return f"Index: {len(_SEMANTIC_SEARCH.chunks)} chunks from {len(files)} files"
        return "Codebase not indexed"

    return f"Unknown action: {action}. Use 'index', 'search', or 'status'."


# ============== V4: SKILLS / MCP / SUB-AGENT ==============

def tool_skill_list(args: Dict) -> str:
    """List available local skills."""
    if not CONFIG.enable_skills:
        return "Skills are disabled by config"
    skills = SKILLS.list_skills()
    if not skills:
        return f"No skills found in {SKILLS.skills_dir}"
    lines = [f"- {s['name']}: {s['summary']}" for s in skills]
    return "Available skills:\n" + "\n".join(lines)


def tool_skill_read(args: Dict) -> str:
    """Read one local skill file."""
    if not CONFIG.enable_skills:
        return "Skills are disabled by config"
    name = args.get("name", "")
    ok, content = SKILLS.read_skill(name)
    if not ok:
        return f"Error: {content}"
    return f"[Skill: {name}]\n{content}"


def tool_mcp_call(args: Dict) -> str:
    """MCP JSON-RPC bridge. Disabled by default."""
    if not CONFIG.enable_mcp:
        return "MCP is disabled by config"
    if not CONFIG.mcp_endpoint:
        return "MCP endpoint is not configured"

    method = str(args.get("method", "")).strip()
    params = args.get("params", {})
    if method not in set(CONFIG.mcp_allowed_methods):
        return f"Blocked: MCP method not allowed: {method}"

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params if isinstance(params, dict) else {},
    }
    req = urllib.request.Request(
        CONFIG.mcp_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=CONFIG.mcp_timeout_seconds) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return SECURITY.truncate_output(body)
    except urllib.error.HTTPError as e:
        return f"MCP HTTP error: {e.code} {e.reason}"
    except Exception as e:
        return f"MCP call failed: {e}"


def tool_subagent_run(args: Dict) -> str:
    """Sub-agent execution is handled by Agent runtime."""
    return "Error: subagent_run must be executed by Agent runtime"


# ============== TODOS ==============

# Global callback for UI sync (set by create_chat_ui)
_TODO_UI_SYNC = None

def tool_todo_write(args: Dict) -> str:
    """Update todo list and sync to UI."""
    global _TODOS, _TODO_UI_SYNC
    _TODOS = args["todos"]

    # Sync to UI if callback is set
    if _TODO_UI_SYNC:
        try:
            _TODO_UI_SYNC()
        except:
            pass  # UI might not be ready

    lines = ["Todo List Updated:"]
    for t in _TODOS:
        icon = {"pending": "⬜", "in_progress": "🔄", "completed": "✅"}.get(t.get("status"), "❓")
        lines.append(f"  {icon} {t.get('content', 'Unknown')}")
    return "\n".join(lines)


def tool_todo_read(args: Dict) -> str:
    """Read current todo list."""
    if not _TODOS:
        return "No todos."
    lines = ["Current Todos:"]
    for t in _TODOS:
        icon = {"pending": "⬜", "in_progress": "🔄", "completed": "✅"}.get(t.get("status"), "❓")
        lines.append(f"  {icon} {t.get('content', 'Unknown')}")
    return "\n".join(lines)


# ============== TOOL REGISTRY ==============

TOOLS = {
    "read_file": (tool_read_file, False, "Read file contents with line numbers",
        {"type": "object", "properties": {"file_path": {"type": "string", "description": "Path to file"}, "offset": {"type": "integer", "description": "Start line (0-indexed)"}, "limit": {"type": "integer", "description": "Max lines (default 500)"}}, "required": ["file_path"]}),

    "write_file": (tool_write_file, True, "Write content to file. Must read first if exists.",
        {"type": "object", "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}}, "required": ["file_path", "content"]}),

    "edit_file": (tool_edit_file, True, "Edit file by replacing EXACT string match. Must read first.",
        {"type": "object", "properties": {"file_path": {"type": "string"}, "old_string": {"type": "string", "description": "Exact text to replace"}, "new_string": {"type": "string"}, "replace_all": {"type": "boolean", "description": "Replace all occurrences"}}, "required": ["file_path", "old_string", "new_string"]}),

    "glob": (tool_glob, False, "Find files by glob pattern (e.g., '**/*.py')",
        {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string", "description": "Directory to search"}}, "required": ["pattern"]}),

    "grep": (tool_grep, False, "Search file contents with regex",
        {"type": "object", "properties": {"pattern": {"type": "string", "description": "Regex pattern"}, "path": {"type": "string"}, "glob": {"type": "string", "description": "Filter files"}, "case_insensitive": {"type": "boolean"}}, "required": ["pattern"]}),

    "list_dir": (tool_list_dir, False, "List directory contents",
        {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}),

    "bash": (tool_bash, True, "Run shell command. Use for git, pip, scripts.",
        {"type": "object", "properties": {"command": {"type": "string"}, "timeout": {"type": "integer", "description": "Timeout seconds (max 600)"}}, "required": ["command"]}),

    "python_exec": (tool_python_exec, True, "Execute Python code. Use for data processing, calculations, file generation.",
        {"type": "object", "properties": {"code": {"type": "string", "description": "Python code"}, "timeout": {"type": "integer", "description": "Timeout seconds (max 300)"}}, "required": ["code"]}),

    "create_word": (tool_create_word, True, "Create styled Word doc. Supports: # headings, **bold**, *italic*, - bullets, 1. numbers, | tables |, ---PAGE--- breaks, ![alt](image.png) images. NOTE: Images must be actual image files (.png/.jpg). For charts, first use create_chart to generate an image, then reference it.",
        {"type": "object", "properties": {"filepath": {"type": "string"}, "content": {"type": "string", "description": "Content with markdown formatting. Use ![caption](image.png) to embed images - must be actual image files, NOT Excel files."}, "title": {"type": "string", "description": "Centered title"}, "include_toc": {"type": "boolean", "description": "Add Table of Contents"}, "header": {"type": "string", "description": "Page header text"}, "footer": {"type": "string", "description": "Page footer text"}}, "required": ["filepath", "content"]}),

    "create_excel": (tool_create_excel, True, "Create Excel spreadsheet with optional embedded chart",
        {"type": "object", "properties": {
            "filepath": {"type": "string"},
            "data": {"type": "array", "description": "List of dicts [{\"col\": \"val\"}]"},
            "sheet_name": {"type": "string"},
            "chart_type": {"type": "string", "enum": ["bar", "line", "pie"], "description": "Optional chart type"},
            "chart_title": {"type": "string", "description": "Chart title"},
            "x_column": {"type": "string", "description": "Column name for X axis (categories)"},
            "y_columns": {"type": "array", "items": {"type": "string"}, "description": "Column names for Y axis (values)"}
        }, "required": ["filepath", "data"]}),

    "create_markdown": (tool_create_markdown, True, "Create Markdown file (.md)",
        {"type": "object", "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}}, "required": ["filepath", "content"]}),

    "create_notebook": (tool_create_notebook, True, "Create Jupyter Notebook (.ipynb) with code and markdown cells",
        {"type": "object", "properties": {
            "filepath": {"type": "string", "description": "Output path (e.g. analysis.ipynb)"},
            "cells": {"type": "array", "description": "List of cells. Each: {type: 'code'|'markdown', source: 'cell content'}",
                "items": {"type": "object", "properties": {
                    "type": {"type": "string", "enum": ["code", "markdown"], "description": "Cell type"},
                    "source": {"type": "string", "description": "Cell content (code or markdown text)"}
                }, "required": ["type", "source"]}}
        }, "required": ["filepath", "cells"]}),

    "create_chart": (tool_create_chart, True, "Create chart image (bar, line, pie, scatter). Returns image path.",
        {"type": "object", "properties": {
            "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter", "horizontal_bar"], "description": "Chart type"},
            "title": {"type": "string", "description": "Chart title"},
            "data": {"type": "object", "description": "Data: {labels: [...], values: [...]} or {x: [...], y: [...]}"},
            "filepath": {"type": "string", "description": "Output path (default: chart.png)"},
            "xlabel": {"type": "string", "description": "X-axis label"},
            "ylabel": {"type": "string", "description": "Y-axis label"},
            "colors": {"type": "array", "items": {"type": "string"}, "description": "Color list"}
        }, "required": ["data"]}),

    "create_pdf": (tool_create_pdf, True, "Create PDF with text, tables, images. Tables can be list-of-lists OR markdown format. Images must be actual image files.",
        {"type": "object", "properties": {
            "filepath": {"type": "string", "description": "Output PDF path"},
            "title": {"type": "string", "description": "Document title"},
            "content": {"type": "array", "description": "List of sections: [{type: 'heading'|'text'|'table'|'image', data: ...}]. Table data can be list-of-lists or markdown string.", "items": {"type": "object"}},
            "page_size": {"type": "string", "enum": ["letter", "a4"], "description": "Page size"}
        }, "required": ["filepath", "content"]}),

    "view_image": (tool_view_image, False, "View image (PNG, JPG, GIF, WebP)",
        {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}),

    "todo_write": (tool_todo_write, False, "Update task list for tracking multi-step work",
        {"type": "object", "properties": {"todos": {"type": "array", "items": {"type": "object", "properties": {"content": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}, "activeForm": {"type": "string"}}}}}, "required": ["todos"]}),

    "todo_read": (tool_todo_read, False, "Read current task list",
        {"type": "object", "properties": {}, "required": []}),

    "semantic_search": (tool_semantic_search, False, "Semantic code search using AI embeddings. Use action='index' to index codebase, action='search' to find code.",
        {"type": "object", "properties": {"action": {"type": "string", "enum": ["index", "search", "status"], "description": "Action: index, search, or status"}, "query": {"type": "string", "description": "Natural language search query (for search)"}, "path": {"type": "string", "description": "Directory to index (for index)"}, "top_k": {"type": "integer", "description": "Number of results (default 5)"}}, "required": ["action"]}),

    "skill_list": (tool_skill_list, False, "List available local skills from skills directory.",
        {"type": "object", "properties": {}, "required": []}),

    "skill_read": (tool_skill_read, False, "Read one local skill by name.",
        {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}),

    "mcp_call": (tool_mcp_call, True, "Call MCP endpoint via JSON-RPC (disabled unless configured).",
        {"type": "object", "properties": {"method": {"type": "string"}, "params": {"type": "object"}}, "required": ["method"]}),

    "subagent_run": (tool_subagent_run, True, "Run a bounded sub-agent for delegated tasks.",
        {"type": "object", "properties": {
            "task": {"type": "string"},
            "mode": {"type": "string", "enum": ["plan", "execute"], "description": "Sub-agent mode (default: plan)"},
            "allowed_tools": {"type": "array", "items": {"type": "string"}},
            "max_turns": {"type": "integer"}
        }, "required": ["task"]}),
}


def get_tool_definitions(allowed_tools: Optional[Set[str]] = None) -> List[Dict]:
    """Get tool definitions for Bedrock API."""
    names = list(TOOLS.keys()) if allowed_tools is None else [k for k in TOOLS.keys() if k in allowed_tools]
    return [{"name": k, "description": TOOLS[k][2], "input_schema": TOOLS[k][3]} for k in names]


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """You are SageMaker Coding Agent, a secure AI coding assistant running in AWS SageMaker Studio.

You help users with software engineering tasks: solving bugs, adding features, refactoring, explaining code, creating documents, and data analysis.

# Core Principles
- Be concise. Use markdown formatting. No emojis unless asked.
- Prioritize technical accuracy over validating user beliefs. Disagree when necessary.
- Avoid hollow validation ("Great question!", "You're absolutely right!"). Focus on facts and problem-solving.
- If uncertain, investigate first rather than confirming assumptions.
- NEVER give time estimates or predictions.

# Conventions
- Follow existing code conventions. Match the style and patterns of surrounding code.
- Make minimal, focused changes. Don't add features, refactoring, or "improvements" beyond what was asked.
- Don't add unnecessary error handling, comments, docstrings, or abstractions to code you didn't change.
- Prefer editing existing files over creating new ones. Never create files unless necessary.

# Doing Tasks
- ALWAYS read a file before editing it. Understand existing code before suggesting modifications.
- old_string in edit_file must be an EXACT match from the file content.
- Use specialized tools over bash: read_file (not cat), edit_file (not sed), glob (not find), grep (not grep).
- Reserve bash for: git commands, pip/npm install, running scripts, system operations.
- If a tool call fails, don't retry the same call. Investigate the error and adapt your approach.
- When exploring unfamiliar code, use grep/glob to locate relevant files before reading entire files.

# Parallel Execution
Call multiple tools in a single response when they are independent:
- Reading 3 different files = parallel
- glob + grep in different directories = parallel
- Creating a directory THEN writing a file into it = sequential
Maximize parallel calls for efficiency.

# Task Management
Use todo_write frequently to plan and track tasks. Break complex tasks into clear steps.
Mark each todo completed IMMEDIATELY when done - do not batch completions.
Only ONE todo should be in_progress at a time.

# Document & Chart Creation
- create_word: Formal documents, reports (.docx). Supports headings, paragraphs, tables, images.
- create_excel: Tabular data, spreadsheets (.xlsx). Data format: list of dicts. Supports charts.
- create_markdown: Documentation, notes (.md).
- create_notebook: Jupyter Notebooks (.ipynb) with code and markdown cells.
- create_chart: Data visualizations (.png) - bar, line, pie, scatter charts. Displayed inline.
- create_pdf: Reports (.pdf) - text, tables, images combined.
- For structural diagrams (architecture, flowcharts, function call graphs, class hierarchies, directory trees), output ASCII/markdown art directly in your response text using box-drawing characters (─│┌┐└┘├┤┬┴┼), arrows (→←↓↑), and tree branches (├──, └──). Do NOT use create_chart for these.

# Python Execution
Use python_exec for data processing, calculations, custom file generation, and scripting.
Code runs in the workspace directory with access to installed packages.

# Security
- Workspace boundary enforced - cannot access files outside project directory.
- Dangerous commands blocked (rm -rf, sudo, curl|bash, direct AWS CLI).
- Write operations require user approval before execution.
- All actions logged to append-only audit trail (local file).
- To access AWS resources: provide boto3 code for the user to run, don't execute directly.

# Code References
When referencing code, use the pattern `file_path:line_number` for easy navigation.
"""

# Plan Mode System Prompt (OpenCode-style)
PLAN_MODE_PROMPT = """You are in PLAN MODE. Your task is to EXPLORE and CREATE A PLAN, NOT execute.

# Plan Mode Rules
1. **READ-ONLY**: You can ONLY use these tools:
   - read_file, glob, grep, list_dir (explore codebase)
   - semantic_search, view_image (search and inspect)
   - todo_write, todo_read (track what you're planning)

2. **NO WRITES**: Do NOT use:
   - write_file, edit_file, bash, python_exec, create_word, create_excel

3. **OUTPUT**: Create a detailed plan in your response:
   - What needs to be done (steps)
   - Which files need to be modified
   - What changes will be made
   - Any risks or considerations

4. **FORMAT**: End your response with a plan summary like:
   ```
   ## Implementation Plan
   1. [Step 1]
   2. [Step 2]
   ...

   ## Files to Modify
   - file1.py: [changes]
   - file2.py: [changes]

   ## Ready to Execute?
   Turn off Plan Mode and send "execute plan" to proceed.
   ```

Remember: EXPLORE and PLAN only. No modifications!
"""

# Plan Mode - Tools that are BLOCKED (write operations)
PLAN_MODE_BLOCKED_TOOLS = {
    "write_file", "edit_file", "bash", "python_exec",
    "create_word", "create_excel", "create_markdown",
    "create_chart", "create_pdf", "mcp_call", "subagent_run"
}

# Plan Mode - Tools that are ALLOWED (read-only operations)
PLAN_MODE_ALLOWED_TOOLS = {
    "read_file", "glob", "grep", "list_dir", "semantic_search",
    "todo_write", "todo_read", "view_image", "skill_list", "skill_read"
}


# ============================================================
# AGENT LOOP
# ============================================================

class Agent:
    """Main agent loop with ReAct pattern, history trimming, and doom loop detection."""

    def __init__(
        self,
        client: BedrockClient,
        session_id: str = None,
        on_approval: Callable = None,
        on_tokens: Callable = None,
        on_thinking: Callable = None,
        on_stop_check: Callable = None,
        tool_allowlist: Optional[Set[str]] = None,
        subagent_depth: int = 0,
    ):
        self.client = client
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        self.on_approval = on_approval
        self.on_tokens = on_tokens  # Callback for token updates
        self.on_thinking = on_thinking  # Callback for thinking output
        self.on_stop_check = on_stop_check  # Callback to check if stop was requested
        self.tool_allowlist = set(tool_allowlist) if tool_allowlist else None
        self.subagent_depth = subagent_depth
        self.tool_history = deque(maxlen=10)
        self.exec_calls = 0
        self.exec_seconds = 0.0
        self.user_msg_timestamps = deque()
        self.user_msg_count = 0

    def _run_subagent_tool(self, args: Dict, output_fn: Callable) -> str:
        """Run bounded delegated task with restricted tools."""
        if self.subagent_depth >= CONFIG.subagent_max_depth:
            return f"Blocked: sub-agent depth limit reached ({CONFIG.subagent_max_depth})"

        task = str(args.get("task", "")).strip()
        if not task:
            return "Error: task is required"
        mode = str(args.get("mode", "plan")).strip().lower()
        max_turns = args.get("max_turns", 8)
        try:
            max_turns = max(1, min(int(max_turns), 20))
        except Exception:
            max_turns = 8

        default_tools = {
            "read_file", "glob", "grep", "list_dir",
            "semantic_search", "todo_read", "todo_write", "view_image", "skill_list", "skill_read"
        }
        blocked_tools = {"subagent_run"}
        requested = args.get("allowed_tools")
        if isinstance(requested, list) and requested:
            allow = set(str(t) for t in requested) & set(TOOLS.keys())
        else:
            allow = set(default_tools)
        allow = allow - blocked_tools

        sub_prompt = SYSTEM_PROMPT + "\n\nYou are a delegated sub-agent. Return concise findings and next actions."
        if mode == "plan":
            sub_prompt = sub_prompt + "\n\n" + PLAN_MODE_PROMPT

        sub = Agent(
            self.client,
            session_id=f"{self.session_id}_sub_{int(time.time())}",
            on_approval=self.on_approval,
            on_tokens=None,
            on_thinking=None,
            on_stop_check=self.on_stop_check,
            tool_allowlist=allow,
            subagent_depth=self.subagent_depth + 1,
        )
        sub_output = []
        old_turns = CONFIG.max_turns
        try:
            CONFIG.max_turns = max_turns
            result = sub.run(
                task,
                output_fn=lambda t: sub_output.append(str(t)),
                system_prompt=sub_prompt,
                plan_mode=(mode == "plan"),
                count_towards_limits=False,
            )
        finally:
            CONFIG.max_turns = old_turns
        tail = "\n".join(sub_output[-6:])
        return SECURITY.truncate_output(f"[Sub-agent mode={mode}, tools={sorted(allow)}]\n{result}\n\n[Trace]\n{tail}")

    def run(
        self,
        user_message: str,
        output_fn: Callable = print,
        system_prompt: str = None,
        plan_mode: bool = False,
        count_towards_limits: bool = True,
    ) -> str:
        """Run agent loop until completion or max turns.

        Args:
            user_message: User's message
            output_fn: Callback for output display
            system_prompt: Custom system prompt (default: SYSTEM_PROMPT, use PLAN_MODE_PROMPT for plan mode)
            plan_mode: If True, block write operations and only allow read-only tools
        """
        # Use provided system prompt or default
        self._system_prompt = system_prompt or SYSTEM_PROMPT
        self._plan_mode = plan_mode  # Store for tool execution check

        # Session/user rate limiting
        if count_towards_limits:
            now = time.time()
            while self.user_msg_timestamps and now - self.user_msg_timestamps[0] > 60:
                self.user_msg_timestamps.popleft()
            if len(self.user_msg_timestamps) >= CONFIG.max_user_messages_per_minute:
                msg = f"Rate limit exceeded: max {CONFIG.max_user_messages_per_minute} messages/min"
                output_fn(msg)
                AUDIT.log(self.session_id, "rate_limit", result_summary=msg, user_approved=False)
                return msg
            if self.user_msg_count >= CONFIG.max_user_messages_per_session:
                msg = f"Session message limit reached: {CONFIG.max_user_messages_per_session}"
                output_fn(msg)
                AUDIT.log(self.session_id, "session_limit", result_summary=msg, user_approved=False)
                return msg
            self.user_msg_timestamps.append(now)
            self.user_msg_count += 1

        # Ensure proper role alternation - if last message was user, add placeholder assistant
        if self.messages and self.messages[-1].get("role") == "user":
            self.messages.append({"role": "assistant", "content": "[Continuing...]"})

        self.messages.append({"role": "user", "content": user_message})
        AUDIT.log(self.session_id, "user_message", parameters={"message": user_message[:200]})

        response = None
        for turn in range(CONFIG.max_turns):
            # Check if stop was requested
            if self.on_stop_check and self.on_stop_check():
                output_fn("[Stopped by user]")
                return response.text if response else ""

            # Check context usage
            warning = CONTEXT.check_and_warn(self.messages)
            if warning:
                output_fn(warning)

            # Smart compaction when context gets high (OpenCode-style)
            if COMPACTOR.should_compact(self.messages, CONFIG.context_max_tokens):
                # Step 1: Try pruning old tool outputs first
                pruned_messages, tokens_saved = COMPACTOR.prune_tool_outputs(self.messages, CONFIG.context_max_tokens)
                if tokens_saved > 0:
                    self.messages = pruned_messages
                    output_fn(f"[i] Pruned old tool outputs, saved ~{tokens_saved:,} tokens")

                # Step 2: If still high, create summary
                if COMPACTOR.should_compact(self.messages, CONFIG.context_max_tokens):
                    output_fn("[i] Context high - creating summary...")
                    summary = "Previous conversation covered: " + ", ".join(
                        m.get("content", "")[:50] if isinstance(m.get("content"), str) else "tool calls"
                        for m in self.messages[:5]
                    )
                    self.messages = COMPACTOR.compact(self.messages, summary)
                    output_fn("[i] Conversation compacted to preserve context")

            # Fallback: simple trim if still too long (preserve role alternation)
            if len(self.messages) > CONFIG.max_history * 2:
                trimmed = self.messages[-CONFIG.max_history:]
                # Ensure we start with user message for proper alternation
                if trimmed and trimmed[0].get("role") == "assistant":
                    trimmed = [{"role": "user", "content": "[Earlier messages trimmed]"}] + trimmed
                self.messages = trimmed

            # Call LLM with retry logic (runs in background thread so stop button works)
            def make_request():
                return self.client.chat(
                    self.messages,
                    self._system_prompt,  # Use custom or default system prompt
                    get_tool_definitions(self.tool_allowlist),
                    CONFIG.max_tokens,
                    CONFIG.temperature,
                    CONFIG.thinking_enabled,
                    CONFIG.thinking_budget,
                )

            def on_retry(attempt, max_retries, delay, error):
                output_fn(f"[Retry {attempt}/{max_retries} in {delay:.1f}s: {error[:50]}...]")

            try:
                # Run LLM call in daemon thread so stop button can interrupt
                _llm_result = [None, None]  # [response, error]
                def _call_llm():
                    try:
                        _llm_result[0] = RETRY.execute(make_request, on_retry)
                    except Exception as e:
                        _llm_result[1] = e

                llm_thread = threading.Thread(target=_call_llm, daemon=True)
                llm_thread.start()

                # Poll for completion, checking stop flag every 0.5s
                while llm_thread.is_alive():
                    if self.on_stop_check and self.on_stop_check():
                        output_fn("[Stopped by user]")
                        return response.text if response else ""
                    llm_thread.join(timeout=0.5)

                if _llm_result[1]:
                    raise _llm_result[1]
                response = _llm_result[0]
            except Exception as e:
                error_msg = f"Error calling Bedrock: {e}"
                output_fn(error_msg)
                AUDIT.log(self.session_id, "error", result_summary=str(e))
                return error_msg

            # Check stop again after LLM returns (user may have clicked during the call)
            if self.on_stop_check and self.on_stop_check():
                output_fn("[Stopped by user]")
                return response.text if response else ""

            # Track token usage
            if response.usage:
                TOKENS.add(response.usage)
                if self.on_tokens:
                    self.on_tokens(TOKENS.get_stats())

            # Output thinking (if enabled)
            if response.thinking and self.on_thinking:
                self.on_thinking(response.thinking)

            # Output text
            if response.text:
                output_fn(response.text)

            # No tool calls = done
            if not response.tool_calls:
                AUDIT.log(self.session_id, "response", result_summary=response.text[:200] if response.text else "")
                return response.text or ""

            # Improved doom loop detection (based on file path, not full content)
            for tc in response.tool_calls:
                # For code/content-heavy tools, use hash to avoid false positives
                if tc.name == "python_exec":
                    code = tc.input.get("code", "")
                    target = hashlib.md5(code.encode()).hexdigest()[:16]
                elif tc.name == "create_pdf":
                    content = str(tc.input.get("content", ""))
                    target = hashlib.md5(content.encode()).hexdigest()[:16]
                elif tc.name == "create_chart":
                    data = str(tc.input.get("data", ""))
                    target = hashlib.md5(data.encode()).hexdigest()[:16]
                else:
                    target = tc.input.get("file_path") or tc.input.get("path") or tc.input.get("filepath") or tc.input.get("command", "")[:50] or str(tc.input)[:50]
                key = (tc.name, target)

                # Check for doom loop (same tool+target 3+ times)
                # todo_write is expected to repeat during normal planning and progress updates.
                if tc.name == "todo_write":
                    self.tool_history.append(key)
                    continue
                repeat_count = sum(1 for h in self.tool_history if h == key)
                if repeat_count >= 3:
                    output_fn(f"[Warning: Repetitive {tc.name} calls detected (3+ identical), stopping]")
                    return response.text or ""

                # Check for consecutive file rewrites (same file written twice in a row)
                if tc.name in ("write_file", "edit_file") and self.tool_history:
                    last_key = self.tool_history[-1] if self.tool_history else None
                    if last_key and last_key[0] == tc.name and last_key[1] == target:
                        output_fn(f"[Skipping duplicate {tc.name} to '{target[:30]}']")
                        continue

                self.tool_history.append(key)

            # Build assistant message
            assistant_content = []
            if response.text:
                assistant_content.append({"type": "text", "text": response.text})
            for tc in response.tool_calls:
                assistant_content.append({"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.input})
            self.messages.append({"role": "assistant", "content": assistant_content})

            # Execute tools with 5-layer error recovery
            tool_results = []
            for tc in response.tool_calls:
                # Check stop before each tool
                if self.on_stop_check and self.on_stop_check():
                    tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "Stopped by user"})
                    continue
                # === LAYER 1: Tool Name Repair ===
                tool_name = tc.name
                tool_info = TOOLS.get(tool_name)

                # Try case-insensitive lookup
                if not tool_info:
                    tool_name_lower = tool_name.lower()
                    for known_name in TOOLS.keys():
                        if known_name.lower() == tool_name_lower:
                            tool_name = known_name
                            tool_info = TOOLS.get(tool_name)
                            output_fn(f"[Auto-fixed tool name: {tc.name} → {tool_name}]")
                            break

                # Try fuzzy match for common typos
                if not tool_info:
                    similar = [n for n in TOOLS.keys() if n.startswith(tool_name[:4]) or tool_name.startswith(n[:4])]
                    if similar:
                        suggestion = similar[0]
                        tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
                            "content": f"Unknown tool: '{tc.name}'. Did you mean '{suggestion}'? Available tools: {', '.join(sorted(TOOLS.keys()))}"})
                        continue
                    tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
                        "content": f"Unknown tool: '{tc.name}'. Available tools: {', '.join(sorted(TOOLS.keys()))}"})
                    continue

                func, needs_approval, description, schema = tool_info

                # Additional allowlist constraint (used by delegated sub-agents).
                if self.tool_allowlist is not None and tool_name not in self.tool_allowlist:
                    tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
                        "content": f"Tool blocked by policy in this run: {tool_name}"})
                    continue

                # === PLAN MODE ENFORCEMENT ===
                # Block write tools when in Plan Mode
                if getattr(self, '_plan_mode', False) and tool_name in PLAN_MODE_BLOCKED_TOOLS:
                    output_fn(f"[⛔ PLAN MODE: {tool_name} blocked - read-only mode]")
                    tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
                        "content": f"⛔ PLAN MODE ACTIVE: '{tool_name}' is blocked. In Plan Mode, only read-only tools are allowed: {', '.join(sorted(PLAN_MODE_ALLOWED_TOOLS))}. Turn off Plan Mode to execute write operations."})
                    continue

                # === LAYER 2: Argument Validation & Auto-Fix ===
                args = tc.input
                required_fields = schema.get("required", []) if schema else []
                properties = schema.get("properties", {}) if schema else {}

                # Check for missing required fields and try auto-fix
                missing = [f for f in required_fields if f not in args or args[f] is None]
                if missing:
                    for field in missing:
                        # Auto-fix: path → file_path
                        if field == "file_path" and "path" in args:
                            args["file_path"] = args.pop("path")
                            output_fn(f"[Auto-fixed: path → file_path]")
                        elif field == "file_path" and "filepath" in args:
                            args["file_path"] = args.pop("filepath")
                            output_fn(f"[Auto-fixed: filepath → file_path]")
                        elif field == "content" and "text" in args:
                            args["content"] = args.pop("text")
                            output_fn(f"[Auto-fixed: text → content]")
                        elif field == "pattern" and "query" in args:
                            args["pattern"] = args.pop("query")
                            output_fn(f"[Auto-fixed: query → pattern]")
                        elif field == "command" and "cmd" in args:
                            args["command"] = args.pop("cmd")
                            output_fn(f"[Auto-fixed: cmd → command]")

                    # Re-check after fixes
                    missing = [f for f in required_fields if f not in args or args[f] is None]
                    if missing:
                        tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
                            "content": f"Missing required arguments for '{tool_name}': {missing}. Expected: {required_fields}. Hint: {description}"})
                        continue

                # === LAYER 3: Type Validation & Auto-Convert ===
                for field, value in list(args.items()):
                    if field in properties:
                        expected_type = properties[field].get("type")
                        if expected_type == "integer" and isinstance(value, str) and value.isdigit():
                            args[field] = int(value)
                            output_fn(f"[Auto-fixed: converted {field} to integer]")
                        elif expected_type == "string" and isinstance(value, (int, float)):
                            args[field] = str(value)

                # === LAYER 4: Permission Check ===
                if needs_approval and self.on_approval:
                    approved = self.on_approval(tool_name, args)
                    AUDIT.log(self.session_id, "approval_request", tool_name, args,
                             "Approved" if approved else "Denied", approved)
                    if not approved:
                        tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "User denied permission"})
                        continue

                # === LAYER 5: Execute with Error Recovery ===
                output_fn(f"[Calling {tool_name}...]")
                try:
                    if tool_name == "subagent_run":
                        result = self._run_subagent_tool(args, output_fn)
                    else:
                        if tool_name in {"bash", "python_exec"}:
                            if self.exec_calls >= CONFIG.max_exec_calls_per_session:
                                result = f"Blocked: execution call limit reached ({CONFIG.max_exec_calls_per_session}/session)"
                                tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": result})
                                AUDIT.log(self.session_id, "execution_blocked", tool_name, tc.input, result, False)
                                continue
                            if self.exec_seconds >= CONFIG.max_exec_seconds_per_session:
                                result = f"Blocked: execution time budget reached ({CONFIG.max_exec_seconds_per_session}s/session)"
                                tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": result})
                                AUDIT.log(self.session_id, "execution_blocked", tool_name, tc.input, result, False)
                                continue
                            if CONFIG.execution_mode == "docker":
                                _ensure_docker_image_ready()
                        start_ts = time.time()
                        result = func(args)
                        elapsed = time.time() - start_ts
                        if tool_name in {"bash", "python_exec"}:
                            self.exec_calls += 1
                            self.exec_seconds += elapsed
                except TypeError as e:
                    result = f"TypeError: {e}. Check argument types. Expected schema: {schema}"
                except KeyError as e:
                    result = f"KeyError: {e}. Required fields: {required_fields}"
                except Exception as e:
                    result = f"Error executing {tool_name}: {e}"

                # Truncate result
                result = SECURITY.truncate_output(result)

                # Show tool result to user (pass full result for inline images)
                if '[INLINE_IMAGE:' in result:
                    output_fn(f"[{tool_name} result]:\n{result}")  # Full result with base64 for image display
                else:
                    output_fn(f"[{tool_name} result]:\n{result[:1000]}{'...(truncated)' if len(result) > 1000 else ''}")

                # Strip inline image data before sending to LLM (saves tokens)
                import re as _re_strip
                llm_result = _re_strip.sub(r'\[INLINE_IMAGE:[A-Za-z0-9+/=]+\]', '[chart image saved]', result)
                AUDIT.log(self.session_id, "tool_call", tc.name, tc.input, llm_result[:200])
                tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": llm_result})

            self.messages.append({"role": "user", "content": tool_results})

        output_fn(f"[Reached max turns ({CONFIG.max_turns})]")
        return response.text if response else ""

    def reset(self):
        """Reset conversation."""
        global _TODOS, _FILES_READ
        self.messages = []
        self.tool_history.clear()
        _TODOS = []
        _FILES_READ = set()
        CONTEXT.reset()
        TOKENS.reset()


# ============================================================
# CHAT UI (for Jupyter)
# ============================================================

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# Available Bedrock models (cross-region rates)
BEDROCK_MODELS = [
    ("Claude 3 Haiku", "anthropic.claude-3-haiku-20240307-v1:0"),
    ("Claude 3 Sonnet", "anthropic.claude-3-sonnet-20240229-v1:0"),
    ("Claude 3.5 Sonnet v2", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
    ("Claude 3.5 Sonnet", "anthropic.claude-3-5-sonnet-20240620-v1:0"),
    ("Claude 4.5 Sonnet (AU)", "au.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    ("Claude 4.5 Haiku (AU)", "au.anthropic.claude-haiku-4-5-20251001-v1:0"),
    ("Claude 4.5 Opus (Global)", "global.anthropic.claude-opus-4-5-20251101-v1:0"),
    ("Claude 4.6 Opus (AU)", "au.anthropic.claude-opus-4-6-v1"),
]
# Single source of truth: chat.ipynb should import BEDROCK_MODELS instead of duplicating

# Tool icons for display (synced from GCP version)
TOOL_ICONS = {
    'read_file': '📖', 'write_file': '📝', 'edit_file': '✏️',
    'glob': '🔍', 'grep': '🔎', 'list_dir': '📁',
    'bash': '💻', 'python_exec': '🐍',
    'create_word': '📄', 'create_excel': '📊', 'create_markdown': '📋',
    'view_image': '🖼️', 'semantic_search': '🧠',
    'todo_write': '✅', 'todo_read': '📋',
    'skill_list': '🧩', 'skill_read': '📘',
    'mcp_call': '🔌', 'subagent_run': '🧠',
}


def create_chat_ui(mock_mode: bool = None):
    """Create and display the chat interface in Jupyter."""
    import ipywidgets as widgets
    from IPython.display import display, HTML, clear_output

    # Clear any previous UI to prevent duplicates
    clear_output(wait=True)

    # Override mock mode if specified
    if mock_mode is not None:
        CONFIG.mock_mode = mock_mode

    # Create client
    client = BedrockClient(CONFIG.model_id, CONFIG.region, CONFIG.mock_mode)

    # UI state
    ui_state = {
        "dark_mode": True,  # Default dark mode like GCP
        "client": client,
        "agent": None,
        "session": None,
        "lock": False,
        "stop_requested": False,  # For stop button
        "authenticated": not CONFIG.require_auth,
        "model_connection_ok": None,  # True/False/None(unknown)
        "model_connection_msg": "Not validated yet",
        "active_skills": [],
    }
    ui_state["model_change_lock"] = False

    # NEW APPROACH: HTML widget with scrollable div inside
    # Browser handles scrolling, not Jupyter widgets
    ui_state["messages"] = []  # Store message tuples: (role, content, tool_name, timestamp)
    ui_state["todos"] = []  # Store todos for persistence (synced with global _TODOS)

    chat_display = widgets.HTML(value='')  # Will be updated by render_chat()
    todo_display = widgets.HTML(value='')  # Todo list display

    def _format_inline_md(text: str, dark: bool) -> str:
        """Render a safe subset of inline markdown."""
        s = escape_html(text)
        code_bg = "#2b2b2b" if dark else "#f3f4f6"
        s = re.sub(r"`([^`]+)`", rf'<code style="background:{code_bg};padding:1px 4px;border-radius:4px;">\1</code>', s)
        s = re.sub(r"\*\*\*([^*]+)\*\*\*", r"<b><i>\1</i></b>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
        return s

    def _render_assistant_markdown(text: str, fg: str, dark: bool) -> str:
        """Render common markdown blocks (tables/lists/code/headers) into HTML."""
        text = str(text)
        lines = text.splitlines()
        chart_bg = "#171717" if dark else "#f6f8fa"

        def _has_markdown_table(ls: List[str]) -> bool:
            for j in range(len(ls) - 1):
                if ls[j].strip().startswith("|") and re.match(r"^\s*\|?[\s:-]+\|[\s|:-]*$", ls[j + 1]):
                    return True
            return False

        def _looks_ascii_art(ls: List[str]) -> bool:
            non_empty = [ln for ln in ls if ln.strip()]
            if len(non_empty) < 3:
                return False
            score = 0
            for ln in non_empty:
                s = ln.rstrip()
                if len(s) - len(s.lstrip()) >= 2:
                    score += 1
                if re.search(r"\+\-[-+]+", s):
                    score += 2
                if re.search(r"^\s*[\d.]+\s*\|", s):
                    score += 2
                if "|" in s:
                    score += 1
                if re.search(r"[*#xXoO]{2,}", s):
                    score += 1
            return score >= 6

        # Preserve alignment for unicode/ascii charts and box-drawing output.
        if re.search(r"[\u2500-\u257F\u2580-\u259F]", text):
            return (
                f'<pre style="background:{chart_bg};color:{fg};padding:8px;border-radius:6px;overflow:auto;'
                f'white-space:pre;line-height:1.3;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;">'
                f'{escape_html(text)}</pre>'
            )
        if _looks_ascii_art(lines) and not _has_markdown_table(lines):
            return (
                f'<pre style="background:{chart_bg};color:{fg};padding:8px;border-radius:6px;overflow:auto;'
                f'white-space:pre;line-height:1.3;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;">'
                f'{escape_html(text)}</pre>'
            )

        out = []
        i = 0
        code_bg = "#171717" if dark else "#f6f8fa"
        table_border = "#444" if dark else "#d0d7de"

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith("```"):
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                out.append(
                    f'<pre style="background:{code_bg};color:{fg};padding:8px;border-radius:6px;overflow:auto;">'
                    f'{escape_html(chr(10).join(code_lines))}</pre>'
                )
                i += 1
                continue

            if stripped.startswith("|") and (i + 1) < len(lines) and re.match(r"^\s*\|?[\s:-]+\|[\s|:-]*$", lines[i + 1]):
                headers = [escape_html(c.strip()) for c in stripped.strip("|").split("|")]
                i += 2
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    cols = [escape_html(c.strip()) for c in lines[i].strip().strip("|").split("|")]
                    rows.append(cols)
                    i += 1
                head_html = "".join([f'<th style="text-align:left;padding:6px;border:1px solid {table_border};">{h}</th>' for h in headers])
                body_html = []
                for row in rows:
                    cells = "".join([f'<td style="padding:6px;border:1px solid {table_border};">{c}</td>' for c in row])
                    body_html.append(f"<tr>{cells}</tr>")
                out.append(
                    f'<table style="border-collapse:collapse;margin:8px 0;color:{fg};">'
                    f"<thead><tr>{head_html}</tr></thead><tbody>{''.join(body_html)}</tbody></table>"
                )
                continue

            if stripped.startswith("- ") or stripped.startswith("* "):
                items = []
                while i < len(lines):
                    s = lines[i].strip()
                    if s.startswith("- ") or s.startswith("* "):
                        items.append(_format_inline_md(s[2:].strip(), dark))
                        i += 1
                    else:
                        break
                out.append("<ul style=\"margin:6px 0 6px 18px;\">" + "".join([f"<li>{x}</li>" for x in items]) + "</ul>")
                continue

            m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
            if m:
                level = len(m.group(1))
                text_part = _format_inline_md(m.group(2), dark)
                size = "18px" if level == 1 else "16px" if level == 2 else "14px"
                out.append(f'<div style="font-weight:700;font-size:{size};margin:8px 0 4px 0;color:{fg};">{text_part}</div>')
                i += 1
                continue

            if stripped:
                out.append(f'<div style="margin:2px 0;color:{fg};">{_format_inline_md(line, dark)}</div>')
            else:
                out.append("<div style=\"height:6px;\"></div>")
            i += 1

        return "".join(out)

    def render_chat():
        """Render all messages into the HTML widget with internal scroll."""
        dark = ui_state["dark_mode"]
        bg = '#1e1e1e' if dark else '#ffffff'
        fg = '#e0e0e0' if dark else '#333'
        border = '#444' if dark else '#ccc'

        msgs_html = []
        for role, content, tool_name, ts in ui_state["messages"]:
            raw = str(content)
            c = escape_html(raw).replace('\n', '<br>')
            if role == 'user':
                msgs_html.append(f'<div style="margin:8px 0;border-left:3px solid #26c6da;padding-left:10px;"><b style="color:#26c6da;">[{ts}] You:</b><div style="color:{fg};margin-top:4px;">{c}</div></div>')
            elif role == 'assistant':
                rendered = _render_assistant_markdown(raw, fg, dark)
                msgs_html.append(f'<div style="margin:8px 0;border-left:3px solid #42a5f5;padding-left:10px;"><b style="color:#42a5f5;">[{ts}] Agent:</b><div style="color:{fg};margin-top:4px;">{rendered}</div></div>')
            elif role == 'tool':
                icon = TOOL_ICONS.get(tool_name, '🔧') if tool_name else '🔧'
                tool_label = escape_html(tool_name or "Tool")
                # Check for inline images (base64-encoded charts/images)
                import re as _re
                inline_match = _re.search(r'\[INLINE_IMAGE:([A-Za-z0-9+/=]+)\]', raw)
                if inline_match:
                    img_b64 = inline_match.group(1)
                    text_part = escape_html(raw[:inline_match.start()].strip()).replace('\n', '<br>')
                    img_html = f'<div style="margin:4px 0;">{text_part}</div><img src="data:image/png;base64,{img_b64}" style="max-width:100%;border-radius:4px;margin:4px 0;" />'
                    msgs_html.append(f'<details open style="margin:5px 0;border-left:3px solid #ffa726;padding-left:10px;"><summary style="color:#ffa726;cursor:pointer;">{icon} {tool_label}</summary>{img_html}</details>')
                else:
                    msgs_html.append(f'<details style="margin:5px 0;border-left:3px solid #ffa726;padding-left:10px;"><summary style="color:#ffa726;cursor:pointer;">{icon} {tool_label}</summary><pre style="color:{fg};white-space:pre-wrap;max-height:150px;overflow:auto;font-size:11px;margin:4px 0;">{c}</pre></details>')
            elif role == 'thinking':
                msgs_html.append(f'<div style="margin:5px 0;color:#ab47bc;font-size:12px;border-left:3px solid #ab47bc;padding-left:10px;">💭 {c[:300]}...</div>')
            elif role == 'system':
                msgs_html.append(f'<div style="margin:5px 0;color:#ef5350;border-left:3px solid #ef5350;padding-left:10px;">⚠️ {c}</div>')
            else:
                msgs_html.append(f'<div style="color:{fg};">{c}</div>')

        content = ''.join(msgs_html) if msgs_html else f'<p style="color:{fg};text-align:center;padding:20px;">Type a message below to start.</p>'

        # CSS-only auto-scroll: use flex-direction: column-reverse
        # Messages are wrapped in inner div, outer div is reversed flex container
        # This makes new content appear at bottom and stay visible
        chat_display.value = f'''<div style="height:400px;max-height:400px;overflow-y:auto;overflow-x:hidden;border:1px solid {border};background:{bg};display:flex;flex-direction:column-reverse;max-width:calc(100% - 6px);margin-left:0;margin-right:auto;">
            <div style="padding:10px;font-family:system-ui,-apple-system,sans-serif;">
                {content}
            </div>
        </div>'''

    def render_todos():
        """Render todos in a collapsible panel (OpenCode-style)."""
        dark = ui_state["dark_mode"]
        bg = '#2d2d2d' if dark else '#f5f5f5'
        fg = '#e0e0e0' if dark else '#333'
        border = '#444' if dark else '#ccc'

        if not ui_state["todos"]:
            todo_display.value = ''
            return

        todos_html = []
        for t in ui_state["todos"]:
            status = t.get("status", "pending")
            content = t.get("content", "Unknown")
            if status == "completed":
                icon, color = "✅", "#4caf50"
            elif status == "in_progress":
                icon, color = "🔄", "#ff9800"
            else:
                icon, color = "⬜", "#888"
            todos_html.append(f'<div style="padding:2px 0;color:{color};font-size:12px;">{icon} {content}</div>')

        todo_display.value = f'''<details style="background:{bg};border:1px solid {border};border-radius:5px;padding:5px 10px;margin-bottom:5px;">
            <summary style="cursor:pointer;color:{fg};font-weight:bold;font-size:12px;">📋 Todos ({len([t for t in ui_state["todos"] if t.get("status") != "completed"])}/{len(ui_state["todos"])})</summary>
            <div style="margin-top:5px;">{''.join(todos_html)}</div>
        </details>'''

        # Sync global _TODOS
        global _TODOS
        _TODOS = ui_state["todos"]

    def sync_todos_from_global():
        """Sync global _TODOS to ui_state (called after tool_todo_write)."""
        global _TODOS
        ui_state["todos"] = _TODOS.copy() if _TODOS else []
        render_todos()

    # Set global callback for tool_todo_write to update UI
    global _TODO_UI_SYNC
    _TODO_UI_SYNC = sync_todos_from_global

    input_box = widgets.Textarea(placeholder='Type your message...', layout=widgets.Layout(
        width='100%', height='80px'
    ))
    send_btn = widgets.Button(description='Send', button_style='primary', icon='paper-plane')
    stop_btn = widgets.Button(description='Stop', button_style='danger', icon='stop', layout=widgets.Layout(display='none'))
    clear_btn = widgets.Button(description='Clear', button_style='warning', icon='trash')
    save_btn = widgets.Button(description='Save', button_style='info', icon='save')
    compact_btn = widgets.Button(description='Compact', button_style='', icon='compress', tooltip='Compress context by summarizing conversation')
    status_html = widgets.HTML(value='<span style="color:#4caf50"><b>● Ready</b></span>')
    mode_html = widgets.HTML(value='')
    tokens_html = widgets.HTML(value='<span style="color:gray;font-size:11px;">Tokens: 0</span>')

    # Plan Mode toggle (OpenCode-style)
    plan_mode_toggle = widgets.ToggleButton(
        value=False,
        description='Plan Mode',
        icon='map',
        button_style='',
        tooltip='When ON: Agent only reads/explores, creates plan file. When OFF: Normal execution.',
        layout=widgets.Layout(width='140px')
    )

    # Auto-compact checkbox (ON by default - always auto-compact at 90%)
    auto_compact_checkbox = widgets.Checkbox(
        value=True,
        description='Auto-Compact',
        indent=False,
        tooltip='Automatically compact when context exceeds 90%'
    )

    # Approval dialog
    approval_output = widgets.Output()
    approve_btn = widgets.Button(description='Approve', button_style='success', icon='check')
    approve_always_btn = widgets.Button(description='Always', button_style='info', icon='thumbs-up')
    deny_btn = widgets.Button(description='Deny', button_style='danger', icon='times')
    approval_box = widgets.VBox([approval_output, widgets.HBox([approve_btn, approve_always_btn, deny_btn])])
    approval_box.layout.display = 'none'

    # Model selector - default to Haiku (first option) with fallback
    model_values = [m[1] for m in BEDROCK_MODELS]
    default_model = CONFIG.model_id if CONFIG.model_id in model_values else BEDROCK_MODELS[0][1]
    model_dropdown = widgets.Dropdown(
        description='Model:',
        options=BEDROCK_MODELS,
        value=default_model,
        layout=widgets.Layout(width='280px')
    )
    # Update CONFIG to match selected model
    CONFIG.model_id = default_model

    # Session selector and name input
    session_dropdown = widgets.Dropdown(description='Session:', options=[('New Session', None)], layout=widgets.Layout(width='250px'))
    session_name_input = widgets.Text(placeholder='Session name (optional)', layout=widgets.Layout(width='200px'))
    load_btn = widgets.Button(description='Load', button_style='info', icon='folder-open')
    new_btn = widgets.Button(description='New', button_style='success', icon='plus')

    # Live parameter controls
    temp_slider = widgets.FloatSlider(
        value=CONFIG.temperature,
        min=0.0, max=1.0, step=0.1,
        description='Temperature:',
        style={'description_width': '100px'},
        layout=widgets.Layout(width='250px')
    )
    thinking_checkbox = widgets.Checkbox(
        value=CONFIG.thinking_enabled,
        description='Extended Thinking',
        style={'description_width': 'initial'}
    )
    thinking_budget_slider = widgets.IntSlider(
        value=CONFIG.thinking_budget,
        min=1024, max=16000, step=1024,
        description='Think Budget:',
        style={'description_width': '100px'},
        layout=widgets.Layout(width='250px'),
        disabled=not CONFIG.thinking_enabled
    )
    dark_mode_checkbox = widgets.Checkbox(
        value=True,  # Default on like GCP
        description='Dark Mode',
        style={'description_width': 'initial'}
    )
    approval_checkbox = widgets.Checkbox(
        value=CONFIG.require_tool_approval,
        description='Require Approval',
        style={'description_width': 'initial'},
        tooltip='If OFF, tool calls execute without manual Approve/Deny prompt.'
    )

    def validate_model_connection(model_id: str) -> Tuple[bool, str]:
        """Validate the selected model is actually callable in current account/region."""
        try:
            test_client = BedrockClient(model_id, CONFIG.region, CONFIG.mock_mode)
            if CONFIG.mock_mode:
                return True, "Mock mode (no Bedrock call)"
            _ = test_client.chat(
                messages=[{"role": "user", "content": "ping"}],
                system="Reply with OK.",
                tools=None,
                max_tokens=8,
                temperature=0.0,
            )
            return True, "Connected and available"
        except Exception as e:
            err = str(e).strip().replace("\n", " ")
            return False, err[:180] if err else "Model not available"

    # Model change handler
    def on_model_change(change):
        if ui_state.get("model_change_lock"):
            return
        new_model = change['new']
        old_model = CONFIG.model_id
        try:
            ok, conn_msg = validate_model_connection(new_model)
            if not ok:
                raise RuntimeError(conn_msg)
            new_client = BedrockClient(new_model, CONFIG.region, CONFIG.mock_mode)
            CONFIG.model_id = new_model
            ui_state["client"] = new_client
            ui_state["model_connection_ok"] = True
            ui_state["model_connection_msg"] = conn_msg
            if ui_state["agent"]:
                ui_state["agent"].client = new_client
                AUDIT.log(ui_state["agent"].session_id, "config_change", "model",
                          {"old": old_model, "new": new_model})
            add_message('system', f'Model connected: {new_model}')
            status_html.value = '<span style="color:#4caf50"><b>● Ready (model connected)</b></span>'
        except Exception as e:
            ui_state["model_change_lock"] = True
            try:
                model_dropdown.value = old_model
            finally:
                ui_state["model_change_lock"] = False
            ui_state["model_connection_ok"] = False
            ui_state["model_connection_msg"] = str(e)[:180]
            add_message('system', f'Model switch failed: {new_model}. Kept {old_model}. Error: {str(e)[:120]}')
            status_html.value = '<span style="color:#f44336"><b>● Ready (model unavailable)</b></span>'
        update_mode_display()

    def on_temp_change(change):
        CONFIG.temperature = change['new']
        update_mode_display()

    def on_thinking_change(change):
        CONFIG.thinking_enabled = change['new']
        thinking_budget_slider.disabled = not change['new']
        if change['new']:
            # Thinking requires temperature=1, show notice
            ui_state["prev_temperature"] = temp_slider.value
            temp_slider.value = 1.0
            temp_slider.disabled = True
        else:
            temp_slider.disabled = False
            if "prev_temperature" in ui_state:
                temp_slider.value = ui_state["prev_temperature"]
        update_mode_display()

    def on_budget_change(change):
        CONFIG.thinking_budget = change['new']
        update_mode_display()

    def on_dark_mode_change(change):
        ui_state["dark_mode"] = change['new']
        # Re-render chat with new colors (colors are in HTML now)
        render_chat()
        render_todos()
        # Update header
        if "header" in ui_state and ui_state["header"]:
            ui_state["header"].value = ui_state["get_header_html"]()
        # Update token display
        if "update_tokens" in ui_state:
            ui_state["update_tokens"]()
        update_mode_display()

    def on_approval_toggle(change):
        CONFIG.require_tool_approval = change['new']
        add_message('system', f'Tool approvals {"enabled" if CONFIG.require_tool_approval else "disabled"}')
        update_mode_display()

    model_dropdown.observe(on_model_change, names='value')
    temp_slider.observe(on_temp_change, names='value')
    thinking_checkbox.observe(on_thinking_change, names='value')
    thinking_budget_slider.observe(on_budget_change, names='value')
    dark_mode_checkbox.observe(on_dark_mode_change, names='value')
    approval_checkbox.observe(on_approval_toggle, names='value')
    plan_mode_toggle.observe(lambda change: update_mode_display(), names='value')

    pending_approval = {"result": None}

    def update_mode_display():
        """Render current runtime mode so users can verify active state."""
        plan = "ON" if plan_mode_toggle.value else "OFF"
        thinking = "ON" if CONFIG.thinking_enabled else "OFF"
        auth = "ON" if CONFIG.require_auth else "OFF"
        approval = "ON" if CONFIG.require_tool_approval else "OFF"
        skills_count = len(ui_state.get("active_skills", []))
        dark = ui_state.get("dark_mode", True)
        text_color = "#aab4be" if dark else "#666"
        if ui_state.get("model_connection_ok") is True:
            model_state = "Connected"
            model_color = "#4caf50"
        elif ui_state.get("model_connection_ok") is False:
            model_state = "Unavailable"
            model_color = "#f44336"
        else:
            model_state = "Unknown"
            model_color = "#ff9800"
        model_msg = escape_html(ui_state.get("model_connection_msg", "Not validated yet"))
        mode_html.value = (
            f'<div style="font-size:12px;color:{text_color};margin:4px 0;">'
            f'Model: <b>{escape_html(CONFIG.model_id)}</b> | '
            f'Status: <b style="color:{model_color}">{model_state}</b> '
            f'(<span>{model_msg}</span>) | '
            f'Plan: <b>{plan}</b> | '
            f'Thinking: <b>{thinking}</b> (budget {CONFIG.thinking_budget}) | '
            f'Auth: <b>{auth}</b> | '
            f'Approval: <b>{approval}</b> | '
            f'Skills: <b>{skills_count}</b> | '
            f'Exec: <b>{escape_html(CONFIG.execution_mode)}</b>'
            f'</div>'
        )

    def get_colors():
        """Get color scheme based on dark mode."""
        if ui_state["dark_mode"]:
            return {
                'bg': '#1e1e1e', 'fg': '#e0e0e0', 'fg_muted': '#a0a0a0',
                'border': '#444', 'bar_bg': '#333',
            }
        else:
            return {
                'bg': '#ffffff', 'fg': '#1a1a1a', 'fg_muted': '#666666',
                'border': '#ccc', 'bar_bg': '#ddd',
            }

    def update_session_list():
        sessions = SESSIONS.list_sessions()
        options = [('New Session', None)] + [(f"{s['title'][:30]} ({s['id']})", s['id']) for s in sessions[:10]]
        session_dropdown.options = options

    def update_tokens_display():
        """Update token display with progress bar."""
        stats = TOKENS.get_stats()
        c = get_colors()

        # Use message-based estimation for context % (consistent with auto-compact trigger)
        # This shows actual context window usage, not cumulative API call totals
        if ui_state["agent"] and ui_state["agent"].messages:
            ctx_tokens = CONTEXT.estimate_tokens(ui_state["agent"].messages)
        else:
            ctx_tokens = 0
        max_ctx = CONFIG.context_max_tokens  # 200000
        ctx_pct = (ctx_tokens / max_ctx * 100) if max_ctx > 0 else 0

        # Color based on context usage
        if ctx_pct >= 90:
            ctx_color = "#f44336"  # red
        elif ctx_pct >= 75:
            ctx_color = "#ff9800"  # orange
        else:
            ctx_color = "#4caf50"  # green

        # Progress bar
        bar_width = min(ctx_pct, 100)

        # Show both: cumulative totals (info) and context window % (important)
        tokens_html.value = f'''
        <div style="font-size:11px;color:{c["fg_muted"]};">
            <span>📊 API Totals - In: <b>{stats["session_input"]:,}</b> | Out: <b>{stats["session_output"]:,}</b> | Calls: {stats["api_calls"]}</span>
            <div style="margin-top:3px;">
                <span style="color:{ctx_color}">Context Window: {ctx_pct:.1f}% ({ctx_tokens:,} / {max_ctx:,})</span>
                <div style="background:{c["bar_bg"]};height:4px;border-radius:2px;margin-top:2px;">
                    <div style="background:{ctx_color};width:{bar_width}%;height:100%;border-radius:2px;"></div>
                </div>
            </div>
        </div>
        '''

    def get_theme_colors():
        """Get colors based on current theme."""
        if ui_state["dark_mode"]:
            return {"text": "#e0e0e0", "muted": "#aaa"}
        else:
            return {"text": "#333", "muted": "#666"}

    def add_message(role: str, content: str, tool_name: str = None):
        """Add message and re-render chat."""
        ts = datetime.now().strftime('%H:%M:%S')
        ui_state["messages"].append((role, content, tool_name, ts))
        render_chat()

    # Tools where "Always" approve is too dangerous (each invocation has different risk)
    HIGH_RISK_TOOLS = {"bash", "python_exec", "mcp_call", "subagent_run"}

    def request_approval(tool_name: str, tool_input: Dict) -> bool:
        import threading
        if not CONFIG.require_tool_approval:
            return True
        is_sagemaker = bool(
            os.getenv("SAGEMAKER_DOMAIN_ID")
            or os.getenv("SAGEMAKER_INTERNAL_IMAGE_URI")
            or "SAGEMAKER" in os.getenv("AWS_EXECUTION_ENV", "").upper()
        )
        if is_sagemaker:
            add_message('system', 'Approval UI can block in this SageMaker kernel. Turn OFF "Require Approval" to continue.')
            return False
        # "Always" only works for low-risk tools (file creation, etc.)
        # bash and python_exec require per-invocation approval since args vary wildly
        if tool_name not in HIGH_RISK_TOOLS and tool_name in ui_state.get("always_allow", set()):
            add_message('system', f'✓ Auto-approved: {tool_name}')
            return True
        pending_approval["result"] = None
        pending_approval["tool_name"] = tool_name
        approval_event = threading.Event()
        pending_approval["event"] = approval_event

        # Hide "Always" button for high-risk tools
        approve_always_btn.layout.display = 'none' if tool_name in HIGH_RISK_TOOLS else 'inline-block'

        dark = ui_state.get("dark_mode", True)
        card_bg = "#2b2b1f" if dark else "#fff8e1"
        card_fg = "#f0f0f0" if dark else "#111"
        card_border = "#555" if dark else "#e6d9aa"
        pre_bg = "#1f1f1f" if dark else "#fff"
        pre_border = "#444" if dark else "#ddd"

        approval_box.layout.border = f"1px solid {card_border}"
        approval_box.layout.padding = "6px"
        approval_box.layout.border_radius = "6px"
        approval_box.layout.background = "#1e1e1e" if dark else "#fafafa"

        with approval_output:
            clear_output()
            input_str = escape_html(json.dumps(tool_input, indent=2, default=str)[:500])
            safe_tool_name = escape_html(tool_name)
            risk_label = ' <span style="color:#f44336">[HIGH RISK - review carefully]</span>' if tool_name in HIGH_RISK_TOOLS else ''
            display(HTML(
                f'<div style="padding:10px;background:{card_bg};border:1px solid {card_border};border-radius:5px;color:{card_fg};">'
                f'<h4 style="margin:0 0 8px 0;color:{card_fg};">Approval Required{risk_label}</h4>'
                f'<p style="margin:0 0 8px 0;color:{card_fg};"><b>Tool:</b> {safe_tool_name}</p>'
                f'<pre style="font-size:11px;color:{card_fg};background:{pre_bg};border:1px solid {pre_border};margin:0;padding:8px;border-radius:4px;max-height:220px;overflow:auto;">{input_str}</pre>'
                f'</div>'
            ))
        approval_box.layout.display = 'block'
        send_btn.disabled = True

        # Wait with timeout (5 min max)
        max_wait = 300
        waited = 0
        while pending_approval["result"] is None and waited < max_wait:
            if ui_state.get("stop_requested"):
                pending_approval["result"] = False
                break
            approval_event.wait(timeout=0.1)
            waited += 0.1

        approval_box.layout.display = 'none'
        send_btn.disabled = False

        with approval_output:
            clear_output()

        result = pending_approval["result"]
        if result is None:
            result = False  # Timeout = deny
            add_message('system', f'⏱️ Timeout - auto-denied: {tool_name}')
        else:
            add_message('system', f'{"✓ Approved" if result else "✗ Denied"}: {tool_name}')
        return result

    def on_approve(b):
        pending_approval["result"] = True
        if pending_approval.get("event"):
            pending_approval["event"].set()

    def on_approve_always(b):
        pending_approval["result"] = True
        # Add tool to always-allow list for this session
        if "always_allow" not in ui_state:
            ui_state["always_allow"] = set()
        if pending_approval.get("tool_name"):
            ui_state["always_allow"].add(pending_approval["tool_name"])
        if pending_approval.get("event"):
            pending_approval["event"].set()

    def on_deny(b):
        pending_approval["result"] = False
        if pending_approval.get("event"):
            pending_approval["event"].set()

    approve_btn.on_click(on_approve)
    approve_always_btn.on_click(on_approve_always)
    deny_btn.on_click(on_deny)

    def on_stop(b):
        """Handle stop button click - also kills active subprocesses."""
        ui_state["stop_requested"] = True
        _kill_active_process()  # Kill any running bash/python_exec subprocess
        if pending_approval.get("event"):
            pending_approval["result"] = False
            pending_approval["event"].set()
        approval_box.layout.display = 'none'
        with approval_output:
            clear_output()
        send_btn.disabled = False
        status_html.value = '<span style="color:#ff9800"><b>⏹ Stop requested...</b></span>'
        add_message('system', '⏹ Stop requested - killing active processes')

    stop_btn.on_click(on_stop)

    def do_pre_send_compact():
        """Compact before sending if context >= 80% (prevents mid-response overflow)."""
        if not ui_state["agent"] or not ui_state["agent"].messages:
            return False

        usage = CONTEXT.get_usage(ui_state["agent"].messages)
        pct = usage["percent"] * 100

        if pct >= 80 and auto_compact_checkbox.value:
            add_message('system', f'🔄 Pre-send compact (context at {pct:.0f}%)...')
            try:
                messages = ui_state["agent"].messages
                # Stage 1: Prune
                pruned_msgs, tokens_saved = COMPACTOR.prune_tool_outputs(messages, CONFIG.context_max_tokens)
                if tokens_saved > 0:
                    ui_state["agent"].messages = pruned_msgs
                    messages = pruned_msgs
                # Stage 2: Quick summary
                summary = "Conversation summary: " + "; ".join(
                    (m.get("content", "")[:60] if isinstance(m.get("content"), str) else "tool use")
                    for m in messages[:3]
                )
                compacted = COMPACTOR.compact(messages, summary)
                ui_state["agent"].messages = compacted
                usage = CONTEXT.get_usage(compacted)
                new_pct = usage["percent"] * 100
                add_message('system', f'✅ Pre-compacted. Context: {pct:.0f}% → {new_pct:.0f}%')
                return True
            except Exception as e:
                add_message('system', f'Pre-compact failed: {e}')
        return False

    def on_send(b):
        if ui_state.get("lock"):
            return

        msg = input_box.value.strip()
        if not msg:
            return

        # Optional auth gate for multi-user/shared notebook setups.
        if CONFIG.require_auth and not ui_state.get("authenticated", False):
            auth_token = os.getenv(CONFIG.auth_token_env, "")
            if msg.startswith("/auth "):
                provided = msg[len("/auth "):].strip()
                input_box.value = ""
                if auth_token and provided == auth_token:
                    ui_state["authenticated"] = True
                    add_message('system', 'Authentication successful.')
                else:
                    add_message('system', 'Authentication failed. Use /auth <token>.')
                return
            add_message('system', f'Authentication required. Send /auth <token> (env: {CONFIG.auth_token_env}).')
            input_box.value = ""
            return

        # Local skill commands (v4)
        if msg == "/skills":
            skills = SKILLS.list_skills()
            if not skills:
                add_message('system', f'No skills found in {SKILLS.skills_dir}')
            else:
                add_message('system', "Available skills:\n" + "\n".join([f"- {s['name']}: {s['summary']}" for s in skills]))
            input_box.value = ""
            return
        if msg.startswith("/skill use "):
            name = msg[len("/skill use "):].strip()
            ok, _content = SKILLS.read_skill(name)
            if not ok:
                add_message('system', f'Skill not found: {name}')
            else:
                active = ui_state.get("active_skills", [])
                if name not in active:
                    active.append(name)
                    ui_state["active_skills"] = active
                add_message('system', f'Enabled skill: {name}')
                update_mode_display()
            input_box.value = ""
            return
        if msg == "/skill clear":
            ui_state["active_skills"] = []
            add_message('system', 'Cleared active skills')
            update_mode_display()
            input_box.value = ""
            return

        ui_state["lock"] = True
        ui_state["stop_requested"] = False  # Reset stop flag
        send_btn.disabled = True
        send_btn.layout.display = 'none'  # Hide send
        stop_btn.layout.display = 'inline-block'  # Show stop
        input_box.value = ''

        add_message('user', msg)
        status_html.value = '<span style="color:#ff9800"><b>⋯ Processing...</b></span>'

        # Create agent if needed
        if ui_state["agent"] is None:
            TOKENS.reset()
            # Use provided session name, or auto-generate from first message
            session_title = session_name_input.value.strip() if session_name_input.value.strip() else f"Chat: {msg[:40]}"
            session = SESSIONS.create(title=session_title)
            ui_state["session"] = session
            ui_state["agent"] = Agent(
                ui_state["client"],
                session.id,
                on_approval=request_approval,
                on_tokens=lambda stats: update_tokens_display(),
                on_thinking=lambda t: add_message('thinking', t) if t else None,
                on_stop_check=lambda: ui_state.get("stop_requested", False)
            )
            session_name_input.value = ''  # Clear for next session

        # Track displayed tool results to prevent duplicates
        displayed_tools = set()

        def output_fn(text):
            """Handle agent output."""
            import re
            # Skip "Calling..." messages - only show results
            if text.startswith('[Calling '):
                return  # Don't display, wait for result

            # Check for tool result pattern: [tool_name result]:
            tool_result_match = re.match(r'^\[(\w+)\s+result\]:', text)
            if tool_result_match:
                tool = tool_result_match.group(1)
                result = text[tool_result_match.end():].strip()

                # Dedup: create key from tool name + first 100 chars of result
                dedup_key = f"{tool}:{result[:100]}"
                if dedup_key in displayed_tools:
                    return  # Skip duplicate
                displayed_tools.add(dedup_key)

                add_message('tool', result, tool)
                update_tokens_display()
                return

            if text.startswith('[Warning') or text.startswith('[!') or text.startswith('[i]'):
                add_message('system', text)
            elif text.startswith('[Reached'):
                add_message('system', text)
            elif text.strip():
                add_message('assistant', text)
                update_tokens_display()

        try:
            # Pre-send compact check (prevents mid-response overflow)
            do_pre_send_compact()

            # Check if stop was requested during pre-compact
            if ui_state["stop_requested"]:
                add_message('system', '⏹ Stopped before sending')
                return

            # Determine system prompt based on plan mode
            if plan_mode_toggle.value:
                add_message('system', '📋 PLAN MODE: Agent will explore and create a plan (no modifications)')
                system_prompt = SYSTEM_PROMPT + "\n\n" + PLAN_MODE_PROMPT
            else:
                system_prompt = None  # Use default

            # Append active skills as extra runtime guidance.
            active_skills = ui_state.get("active_skills", [])
            if active_skills:
                blocks = []
                for skill_name in active_skills:
                    ok, txt = SKILLS.read_skill(skill_name, max_chars=4000)
                    if ok and txt.strip():
                        blocks.append(f"[SKILL: {skill_name}]\n{txt}")
                if blocks:
                    base_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT
                    system_prompt = base_prompt + "\n\n# Active Skills\n" + "\n\n".join(blocks)

            ui_state["agent"].run(msg, output_fn, system_prompt=system_prompt, plan_mode=plan_mode_toggle.value)

            # Update status when done
            usage = CONTEXT.get_usage(ui_state["agent"].messages)
            pct = usage["percent"] * 100

            # Auto-compact if enabled and context is high (with auto-continue)
            if auto_compact_checkbox.value and pct >= 90 and not ui_state["stop_requested"]:
                add_message('system', '🔄 Auto-compact triggered (context at {:.0f}%)...'.format(pct))
                try:
                    messages = ui_state["agent"].messages
                    # Stage 1: Prune
                    pruned_msgs, tokens_saved = COMPACTOR.prune_tool_outputs(messages, CONFIG.context_max_tokens)
                    if tokens_saved > 0:
                        ui_state["agent"].messages = pruned_msgs
                        messages = pruned_msgs
                    # Stage 2: Simple summary (auto mode uses quick summary)
                    summary = "Conversation summary: " + "; ".join(
                        (m.get("content", "")[:60] if isinstance(m.get("content"), str) else "tool use")
                        for m in messages[:3]
                    )
                    compacted = COMPACTOR.compact(messages, summary)
                    ui_state["agent"].messages = compacted
                    usage = CONTEXT.get_usage(compacted)
                    pct = usage["percent"] * 100
                    add_message('system', f'✅ Auto-compacted. Context now at {pct:.0f}%')

                    # Auto-continue after compact (OpenCode-style)
                    if not ui_state["stop_requested"]:
                        add_message('system', '▶️ Auto-continuing...')
                        ui_state["agent"].run(
                            "Continue from where we left off.",
                            output_fn,
                            system_prompt=system_prompt,
                            plan_mode=plan_mode_toggle.value,
                            count_towards_limits=False,
                        )
                        usage = CONTEXT.get_usage(ui_state["agent"].messages)
                        pct = usage["percent"] * 100

                except Exception as e:
                    add_message('system', f'Auto-compact failed: {e}')

            # Update status
            if pct >= 90:
                status_html.value = f'<span style="color:#f44336"><b>● Ready ({pct:.0f}% context - HIGH!)</b></span>'
                if not auto_compact_checkbox.value:
                    add_message('system', f'⚠️ Context at {pct:.0f}% - Click "Compact" or enable Auto-Compact.')
            elif pct >= 75:
                status_html.value = f'<span style="color:#ff9800"><b>● Ready ({pct:.0f}% context)</b></span>'
            else:
                status_html.value = f'<span style="color:#4caf50"><b>● Ready ({pct:.0f}% context)</b></span>'

            # Add plan mode indicator to status
            if plan_mode_toggle.value:
                status_html.value = status_html.value.replace('Ready', '📋 Plan Mode')

            update_tokens_display()

        except Exception as e:
            add_message('system', f'Error: {e}')
            import traceback
            traceback.print_exc()

        finally:
            ui_state["lock"] = False
            ui_state["stop_requested"] = False
            send_btn.disabled = False
            send_btn.layout.display = 'inline-block'  # Show send
            stop_btn.layout.display = 'none'  # Hide stop

            # Auto-save session after each message
            if ui_state["agent"] and ui_state["agent"].messages:
                try:
                    # Preserve existing session title; only use input if explicitly set
                    existing_title = ui_state["session"].title if ui_state["session"] else None
                    session_name = session_name_input.value.strip() or existing_title or f"session_{ui_state['agent'].session_id}"
                    ui_state["session"] = Session(
                        id=ui_state["agent"].session_id,
                        created_at=ui_state["session"].created_at if ui_state["session"] else datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat(),
                        title=session_name,
                        messages=copy.deepcopy(ui_state["agent"].messages),
                        metadata={
                            "model": model_dropdown.value,
                            "user_msg_count": ui_state["agent"].user_msg_count,
                            "exec_calls": ui_state["agent"].exec_calls,
                            "exec_seconds": ui_state["agent"].exec_seconds,
                            "active_skills": list(ui_state.get("active_skills", [])),
                        },
                        todos=_TODOS.copy() if _TODOS else []
                    )
                    SESSIONS.save(ui_state["session"])
                except Exception as e:
                    print(f"[Auto-save error: {e}]")  # Log instead of silent fail

    def on_clear(b):
        """Clear current session."""
        global _TODOS, _FILES_READ
        if ui_state["agent"]:
            ui_state["agent"].reset()
        ui_state["agent"] = None
        ui_state["session"] = None
        _TODOS = []
        _FILES_READ = set()
        TOKENS.reset()
        ui_state["messages"] = []
        ui_state["todos"] = []  # Clear todos
        ui_state["active_skills"] = []
        render_chat()
        render_todos()  # Update todo display
        status_html.value = '<span style="color:#4caf50"><b>● Ready</b></span>'
        update_tokens_display()

    def on_save(b):
        """Save current session with todos."""
        if ui_state["session"] and ui_state["agent"]:
            ui_state["session"].messages = copy.deepcopy(ui_state["agent"].messages)
            metadata = ui_state["session"].metadata or {}
            metadata["model"] = model_dropdown.value
            metadata["user_msg_count"] = ui_state["agent"].user_msg_count
            metadata["exec_calls"] = ui_state["agent"].exec_calls
            metadata["exec_seconds"] = ui_state["agent"].exec_seconds
            metadata["active_skills"] = list(ui_state.get("active_skills", []))
            ui_state["session"].metadata = metadata
            # Save todos with session (store as metadata)
            ui_state["session"].todos = ui_state["todos"].copy() if ui_state["todos"] else []
            SESSIONS.save(ui_state["session"])
            add_message('system', f'Session saved: {ui_state["session"].id} ({len(ui_state["todos"])} todos)')
            update_session_list()
        else:
            add_message('system', 'No session to save')

    def on_load(b):
        """Load selected session."""
        session_id = session_dropdown.value
        if not session_id:
            # New session - just clear
            on_clear(None)
            return

        session = SESSIONS.load(session_id)
        if not session:
            add_message('system', f'Failed to load session: {session_id}')
            return

        # Restore saved model from session metadata when possible.
        saved_model = None
        if isinstance(session.metadata, dict):
            saved_model = session.metadata.get("model")
        if saved_model and saved_model in [m[1] for m in BEDROCK_MODELS] and saved_model != model_dropdown.value:
            ui_state["model_change_lock"] = True
            try:
                model_dropdown.value = saved_model
            finally:
                ui_state["model_change_lock"] = False
            try:
                ok, conn_msg = validate_model_connection(saved_model)
                if not ok:
                    raise RuntimeError(conn_msg)
                restored_client = BedrockClient(saved_model, CONFIG.region, CONFIG.mock_mode)
                CONFIG.model_id = saved_model
                ui_state["client"] = restored_client
                ui_state["model_connection_ok"] = True
                ui_state["model_connection_msg"] = conn_msg
                add_message('system', f'Restored model from session: {saved_model}')
            except Exception as e:
                ui_state["model_connection_ok"] = False
                ui_state["model_connection_msg"] = str(e)[:180]
                add_message('system', f'Failed to restore saved model {saved_model}: {str(e)[:120]}')

        # Refresh active model health so status line is always current after load.
        active_ok, active_msg = validate_model_connection(CONFIG.model_id)
        ui_state["model_connection_ok"] = active_ok
        ui_state["model_connection_msg"] = active_msg

        # Reset and load
        TOKENS.reset()
        ui_state["session"] = session
        ui_state["agent"] = Agent(
            ui_state["client"],
            session.id,
            on_approval=request_approval,
            on_tokens=lambda stats: update_tokens_display(),
            on_thinking=lambda t: add_message('thinking', t) if t else None,
            on_stop_check=lambda: ui_state.get("stop_requested", False)
        )
        ui_state["agent"].messages = copy.deepcopy(session.messages)
        if isinstance(session.metadata, dict):
            ui_state["agent"].user_msg_count = int(session.metadata.get("user_msg_count", 0) or 0)
            ui_state["agent"].exec_calls = int(session.metadata.get("exec_calls", 0) or 0)
            ui_state["agent"].exec_seconds = float(session.metadata.get("exec_seconds", 0.0) or 0.0)
            loaded_skills = session.metadata.get("active_skills", [])
            if isinstance(loaded_skills, list):
                ui_state["active_skills"] = [str(s) for s in loaded_skills if isinstance(s, str)]

        # Display loaded messages
        ui_state["messages"] = []
        add_message('system', f'Loaded session: {session.title} ({len(session.messages)} messages)')

        for msg in session.messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                if isinstance(content, str):
                    add_message('user', content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            add_message('tool', item.get("content", "")[:200], "result")

            elif role == "assistant":
                if isinstance(content, str):
                    add_message('assistant', content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                add_message('assistant', item.get("text", ""))
                            elif item.get("type") == "tool_use":
                                add_message('tool', f'Called {item.get("name", "?")}', item.get("name"))

        # Restore todos from session (if saved)
        global _TODOS
        if hasattr(session, 'todos') and session.todos:
            _TODOS = session.todos.copy()
            ui_state["todos"] = _TODOS.copy()
            render_todos()
            add_message('system', f'Restored {len(_TODOS)} todos')
        else:
            _TODOS = []
            ui_state["todos"] = []
            render_todos()

        update_tokens_display()
        update_mode_display()

    def on_new(b):
        """Start a new session (clear current without saving)."""
        global _TODOS, _FILES_READ
        if ui_state["agent"]:
            ui_state["agent"].reset()
        ui_state["agent"] = None
        ui_state["session"] = None
        _TODOS = []
        _FILES_READ = set()
        TOKENS.reset()
        ui_state["messages"] = []
        ui_state["todos"] = []  # Clear todos
        render_chat()
        render_todos()  # Update todo display
        status_html.value = '<span style="color:#4caf50"><b>● Ready (New)</b></span>'
        update_tokens_display()
        update_mode_display()
        session_dropdown.value = None

    def on_compact(b):
        """Manually compact conversation context (OpenCode-style)."""
        if not ui_state["agent"] or not ui_state["agent"].messages:
            add_message('system', 'No conversation to compact.')
            return

        if ui_state.get("lock"):
            add_message('system', 'Please wait for current operation to finish.')
            return

        ui_state["lock"] = True
        compact_btn.disabled = True
        status_html.value = '<span style="color:#ff9800"><b>⋯ Compacting...</b></span>'

        try:
            messages = ui_state["agent"].messages
            original_count = len(messages)

            # Stage 1: Prune old tool outputs (OpenCode-style)
            pruned_msgs, tokens_saved = COMPACTOR.prune_tool_outputs(messages, CONFIG.context_max_tokens)
            if tokens_saved > 0:
                add_message('system', f'Stage 1: Pruned old tool outputs (~{tokens_saved:,} tokens saved)')
                ui_state["agent"].messages = pruned_msgs
                messages = pruned_msgs

            # Stage 2: Ask model to create summary
            add_message('system', 'Stage 2: Creating conversation summary...')

            summary_prompt = COMPACTOR.create_summary_prompt(messages)

            # Add summary request to get AI to summarize
            summary_messages = messages.copy()
            summary_messages.append({"role": "user", "content": summary_prompt})

            # Make API call to get summary
            response = ui_state["client"].chat(
                messages=summary_messages,
                system="""You are summarizing a coding conversation. Be concise but preserve:
1. Current task and goal
2. Key files modified or read
3. Important decisions made
4. Where we left off
5. What needs to happen next""",
                tools=None,
                max_tokens=2000,
                temperature=0.0
            )

            if response and response.text:
                # Compact: keep summary + last 5 messages
                compacted = COMPACTOR.compact(messages, response.text)
                ui_state["agent"].messages = compacted

                add_message('system', f'Compacted: {original_count} → {len(compacted)} messages')

                # Update context display
                usage = CONTEXT.get_usage(compacted)
                pct = usage["percent"] * 100
                add_message('system', f'Context now at {pct:.1f}% ({usage["tokens"]:,} tokens)')
            else:
                add_message('system', 'Failed to get summary from model.')

        except Exception as e:
            add_message('system', f'Compact failed: {e}')
            import traceback
            traceback.print_exc()

        finally:
            ui_state["lock"] = False
            compact_btn.disabled = False
            status_html.value = '<span style="color:#4caf50"><b>● Ready</b></span>'
            update_tokens_display()

    send_btn.on_click(on_send)
    clear_btn.on_click(on_clear)
    save_btn.on_click(on_save)
    compact_btn.on_click(on_compact)
    load_btn.on_click(on_load)
    new_btn.on_click(on_new)

    # ========== BUILD LAYOUT ==========
    # CSS fix for Output widget scroll containment
    def get_header_html():
        c = get_colors()
        session_count = len(SESSIONS.list_sessions())
        return f'''
        <div style="border-bottom:1px solid {c['border']};padding-bottom:8px;margin-bottom:8px;">
            <h2 style="margin:0;color:#4a9eff;">SageMaker Coding Agent</h2>
            <p style="margin:4px 0;color:{c['fg_muted']};font-size:12px;">
                {len(TOOLS)} tools | {session_count} saved sessions | {CONFIG.region}
            </p>
        </div>
        '''

    header = widgets.HTML(get_header_html())
    # Store references for dark mode updates
    ui_state["header"] = header
    ui_state["get_header_html"] = get_header_html
    ui_state["update_tokens"] = update_tokens_display

    # Row 1: Session & Model - [Name] [💾Save] [Session ▼] [📁Load] [+New] | [Model ▼]
    row1 = widgets.HBox([
        session_name_input, save_btn, session_dropdown, load_btn, new_btn,
        widgets.HTML('<span style="margin:0 8px;color:#777;">|</span>'),
        model_dropdown, plan_mode_toggle, auto_compact_checkbox
    ])
    row1.layout = widgets.Layout(flex_flow='row wrap', align_items='center', gap='8px 10px')

    # Row 2: Parameters
    row2 = widgets.HBox([
        temp_slider, thinking_checkbox, thinking_budget_slider, dark_mode_checkbox, approval_checkbox
    ])
    row2.layout = widgets.Layout(flex_flow='row wrap', align_items='center', gap='8px 12px')

    # Row 3: Buttons (stop_btn hidden by default, shows during processing)
    row3 = widgets.HBox([send_btn, stop_btn, clear_btn, compact_btn, status_html])

    # Full UI layout - using HTML widget for chat (no Output widget issues)
    ui = widgets.VBox([
        header,
        row1,
        row2,
        mode_html,
        todo_display,  # Collapsible todo list (OpenCode-style)
        chat_display,  # HTML widget with internal scroll
        approval_box,
        input_box,
        row3,
        tokens_html
    ])

    update_session_list()
    update_tokens_display()
    # Validate initial model once so status line reflects real connectivity.
    init_ok, init_msg = validate_model_connection(CONFIG.model_id)
    ui_state["model_connection_ok"] = init_ok
    ui_state["model_connection_msg"] = init_msg
    update_mode_display()

    # Initialize displays
    render_chat()
    render_todos()

    try:
        display(ui)
    except UnicodeEncodeError:
        # Some Windows terminals use cp1252 and fail on widget/unicode rendering.
        print("UI created. Open this in Jupyter/Studio to render widgets.")
    return None  # Don't return ui - Jupyter would display it twice


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("SageMaker Coding Agent")
    print(f"  Region: {CONFIG.region}")
    print(f"  Model: {CONFIG.model_id}")
    print(f"  Tools: {len(TOOLS)}")
    print(f"  Mock mode: {CONFIG.mock_mode}")
    print("\nTo use in Jupyter:")
    print("  from sagemaker_agent import create_chat_ui")
    print("  create_chat_ui()")
```
