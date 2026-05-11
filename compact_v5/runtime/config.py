"""V5 Config — verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:1018-1287.

Per ADR-006: Config + JSONC loader is a pure v4 reuse, no Runnable adoption.
Behavior unchanged from v4.10.10 final state. Only structural change: lives in
its own module instead of inline in the monolith.

Source: compact_v4/MAIN/agent/sagemaker_agent.py:1018 (Config dataclass),
        :1152 (_strip_jsonc_comments), :1190 (_load_config_file),
        :1205 (_apply_config_file), :1285 (CONFIG = Config()).

The flat-zip ship surface (Phase 13) collapses this back to root-level
`config.py` next to chat.ipynb; v5 source-tree namespacing is dev-time only.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict


# ============================================================
# CONFIG (verbatim port from v4)
# ============================================================

@dataclass
class Config:
    """Agent configuration."""
    # AWS Settings
    region: str = "ap-southeast-2"  # Sydney
    # Default runtime model: Sonnet 4.5 inference profile.
    # V4.10.1: default switched from Haiku 4.5 to Sonnet 4.5 (user-set, 2026-04-28).
    # Cost note: Sonnet 4.5 is ~10x the per-token cost of Haiku 4.5, but the
    # prompt-cache checkpoint threshold drops from 4096 (Haiku) to 1024 tokens
    # (Sonnet), so caching activates earlier and offsets some of the cost on
    # multi-turn sessions. To switch back to Haiku for cost-sensitive runs,
    # set model_id to "au.anthropic.claude-haiku-4-5-20251001-v1:0" in agent_config.json.
    model_id: str = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # Workspace - use absolute paths to avoid confusion
    workspace: str = os.getcwd()
    sessions_dir: str = os.path.join(os.getcwd(), "sessions")
    audit_dir: str = os.path.join(os.getcwd(), "audit_logs")

    # Limits
    max_turns: int = 60
    max_tokens: int = 16384  # Must be > thinking_budget when thinking enabled
    max_history: int = 20
    max_output_chars: int = 50000  # Matches Runnable's DEFAULT_MAX_RESULT_SIZE_CHARS (50K)
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # Context limits (Claude 3.5 = 200K tokens)
    context_max_tokens: int = 200000

    # Model parameters
    temperature: float = 0.0
    thinking_enabled: bool = False  # Extended thinking OFF by default
    thinking_budget: int = 8192  # Tokens for thinking (1024-16000)
    disable_thinking_for_simple_s3_inventory: bool = True

    # Testing
    mock_mode: bool = False  # Set True to test without Bedrock API

    # Security policy
    allowed_paths: list = None  # Additional directories accessible outside workspace
    bash_allow_interpreters: bool = False  # Block python/node via bash (use python_exec)
    bash_allow_docker: bool = False        # If True, allow docker/docker-compose via bash

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
    require_tool_approval: bool = True
    auth_token_env: str = "SAGEMAKER_AGENT_AUTH_TOKEN"
    max_user_messages_per_minute: int = 10
    max_user_messages_per_session: int = 150
    # V4.10.10: 40 -> 200. Old 40-call ceiling was hit mid-task in real SageMaker
    # sessions (real log: agent finished call 40 at 06:29 then spent 5 minutes
    # confused about which tools were still available). Only bash + python_exec
    # are counted; read_file/grep/glob/edit_file/etc are unaffected.
    max_exec_calls_per_session: int = 200
    max_exec_seconds_per_session: int = 900
    session_cost_limit: float = 0.0  # 0 = no limit. Warn-and-continue UX threshold.
    max_budget_usd: float = 0.0  # 0 = no hard cap. QueryEngine halts at or above this value.
    audit_retention_days: int = 30

    # AWS scope
    aws_bedrock_only: bool = False  # Set True to block all boto3 except bedrock-runtime
    disable_local_traces: bool = False  # Set True for zero local footprint

    # V4.7.1 local-git baseline maintenance
    auto_commit_every: int = 0

    # V4 capabilities
    load_claude_md: bool = True
    enable_prompt_cache: bool = True
    enable_memory_extraction: bool = False
    enable_status_doc: bool = True
    status_doc: str = "AGENT_STATUS.md"
    enable_skills: bool = True
    enable_skill_auto_trigger: bool = False  # V4.9.6: global opt-in; no skill auto-loads by default
    skills_dir: str = "./skills"
    enable_mcp: bool = False
    mcp_servers: Dict = field(default_factory=dict)
    mcp_timeout_seconds: int = 30
    subagent_max_depth: int = 2
    enable_worktree: bool = True

    # V4.9.4: shared iteration budget across parent + sub-agents (hermes pattern).
    # V4.10.10: default bumped 90 -> 600 for normal SageMaker development.
    max_iteration_budget: int = 600

    # V4.9.4: optional auxiliary model for compaction summaries
    compaction_model: str = ""
    cold_cache_threshold_seconds: int = 30 * 60
    cache_ttl: str = "5m"
    bedrock_guardrail_identifier: str = ""
    bedrock_guardrail_version: str = ""
    bedrock_guardrail_trace: str = ""
    bedrock_stale_call_seconds: int = 0
    bedrock_heartbeat_seconds: int = 30
    bedrock_disable_keepalive_on_retry: bool = True

    # V4.9.5: opt-in self-patching skills
    enable_skill_patching: bool = False

    # V4.10.2: control whether the verify-after-3-edits Verification Contract is
    # MANDATORY or merely SUGGESTED. Default False = suggest-and-let-user-confirm.
    enforce_verify_contract: bool = False

    # V4.10.4: control sub-agent handoff block
    enable_subagent_handoff: bool = True

    # Block F2: opt-in auto-continuation under iteration budget. Default OFF
    # (Wave 6 NLT row #21 — explicit opt-in contract). When True, a parent
    # agent loop that emits end_turn while iter_used < 90% of iteration
    # budget AND not diminishing-returns AND session_cost < session_cost_limit
    # auto-continues with a "Keep working — do not summarize." nudge.
    enable_token_budget_continuation: bool = False

    # Block G3: opt-in coordinator mode. Default OFF. When True, the parent
    # agent's system prompt is augmented with the coordinator block from
    # coordinator/system_prompt.py — codifies the 4-phases /
    # never-delegate-understanding / continue-vs-spawn / parallel-research-
    # serial-write rules.
    coordinator_mode_enabled: bool = False

    # Custom commands
    custom_commands: Dict = field(default_factory=dict)

    # Permission overrides (from config file)
    permission_rules: Dict = field(default_factory=dict)

    # Agent type overrides (from config file)
    agent_overrides: Dict = field(default_factory=dict)


# ============================================================
# JSONC loader (v4 verbatim)
# ============================================================

def _strip_jsonc_comments(text: str) -> str:
    """Strip // comments from JSONC, preserving // inside quoted strings."""
    result = []
    i = 0
    in_string = False
    while i < len(text):
        ch = text[i]
        if in_string:
            result.append(ch)
            if ch == '\\' and i + 1 < len(text):
                result.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
        else:
            if ch == '"':
                in_string = True
                result.append(ch)
                i += 1
            elif ch == '/' and i + 1 < len(text) and text[i + 1] == '/':
                # Skip to end of line
                while i < len(text) and text[i] != '\n':
                    i += 1
            elif ch == '/' and i + 1 < len(text) and text[i + 1] == '*':
                # Block comment /* ... */
                i += 2
                while i + 1 < len(text) and not (text[i] == '*' and text[i + 1] == '/'):
                    i += 1
                if i + 1 < len(text):
                    i += 2  # skip */
            else:
                result.append(ch)
                i += 1
    return "".join(result)


def _load_config_file(workspace: str) -> Dict:
    """Load optional agent_config.json or agent_config.jsonc from workspace."""
    for name in ("agent_config.json", "agent_config.jsonc"):
        path = os.path.join(workspace, name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                text = _strip_jsonc_comments(text)
                return json.loads(text)
            except Exception:
                pass
    return {}


def _apply_config_file(config: Config) -> None:
    """Merge external config file into Config dataclass with type validation."""
    ext = _load_config_file(config.workspace)
    if not ext:
        return

    # Scalar fields with expected types for validation
    _SCALAR_FIELDS: Dict[str, type] = {
        "region": str, "model_id": str, "max_turns": int, "max_tokens": int,
        "max_history": int, "temperature": float, "thinking_enabled": bool,
        "thinking_budget": int, "disable_thinking_for_simple_s3_inventory": bool, "mock_mode": bool,
        "bash_allow_interpreters": bool, "bash_allow_docker": bool,
        "execution_mode": str, "exec_docker_image": str,
        "exec_docker_network_disabled": bool, "exec_docker_readonly_rootfs": bool,
        "require_auth": bool, "require_tool_approval": bool,
        "aws_bedrock_only": bool, "disable_local_traces": bool, "session_cost_limit": float,
        "max_budget_usd": float, "maxBudgetUsd": float,
        "load_claude_md": bool,
        "enable_prompt_cache": bool,
        "enable_memory_extraction": bool,
        "enable_status_doc": bool, "status_doc": str,
        "enable_skills": bool, "enable_skill_auto_trigger": bool, "skills_dir": str,
        "enable_mcp": bool, "mcp_timeout_seconds": int, "subagent_max_depth": int,
        "enable_worktree": bool,
        "max_user_messages_per_minute": int, "max_user_messages_per_session": int,
        "max_exec_calls_per_session": int, "max_exec_seconds_per_session": int,
        "max_iteration_budget": int,
        "audit_retention_days": int,
        "context_max_tokens": int,
        "compaction_model": str,
        "cache_ttl": str,
        "bedrock_guardrail_identifier": str,
        "bedrock_guardrail_version": str,
        "bedrock_guardrail_trace": str,
        "bedrock_stale_call_seconds": int,
        "bedrock_heartbeat_seconds": int,
        "bedrock_disable_keepalive_on_retry": bool,
        "enable_skill_patching": bool,
        "enforce_verify_contract": bool,
        "enable_subagent_handoff": bool,
        "enable_token_budget_continuation": bool,
        "coordinator_mode_enabled": bool,
    }
    for key, expected_type in _SCALAR_FIELDS.items():
        if key not in ext:
            continue
        val = ext[key]
        # Allow int where float expected
        if expected_type is float and isinstance(val, int):
            val = float(val)
        if not isinstance(val, expected_type):
            logging.warning(
                f"Config: '{key}' expected {expected_type.__name__}, got {type(val).__name__} — skipped"
            )
            continue
        # Range validation for numeric fields
        if key == "temperature" and not (0.0 <= val <= 1.0):
            logging.warning(f"Config: temperature={val} out of range [0.0, 1.0] — skipped")
            continue
        if key == "thinking_budget" and not (1024 <= val <= 64000):
            logging.warning(f"Config: thinking_budget={val} out of range [1024, 64000] — skipped")
            continue
        if key in ("max_turns", "max_tokens", "max_history", "subagent_max_depth") and val < 1:
            logging.warning(f"Config: {key}={val} must be positive — skipped")
            continue
        setattr(config, key, val)

    # Structured fields
    if "mcp" in ext and isinstance(ext["mcp"], dict):
        config.mcp_servers = ext["mcp"]
        if config.mcp_servers:
            config.enable_mcp = True

    if "commands" in ext and isinstance(ext["commands"], dict):
        config.custom_commands = ext["commands"]

    if "permissions" in ext and isinstance(ext["permissions"], dict):
        config.permission_rules = ext["permissions"]

    if "agents" in ext and isinstance(ext["agents"], dict):
        config.agent_overrides = ext["agents"]

    # Allowed paths — list of absolute directory paths the agent can read AND write outside workspace
    # Also accepts legacy key "allowed_read_paths" for backward compatibility
    _ap_key = (
        "allowed_paths" if "allowed_paths" in ext
        else ("allowed_read_paths" if "allowed_read_paths" in ext else None)
    )
    if _ap_key:
        val = ext[_ap_key]
        if isinstance(val, list) and all(isinstance(p, str) for p in val):
            config.allowed_paths = val
        else:
            logging.warning(f"Config: '{_ap_key}' must be a list of strings — skipped")


# ============================================================
# Module-level singleton (v4 pattern)
# ============================================================

CONFIG = Config()
_apply_config_file(CONFIG)

# Block B (Codex finding #5 MEDIUM lock): wire validate_bounded_int_env_var
# into the runtime numeric knobs so env-var overrides clamp safely + log
# WARNING on bad input. Per ADR-021 §Linked port-log rows #045.
try:
    from runtime.env_validation import validate_bounded_int_env_var as _vbiev
    CONFIG.max_turns = _vbiev(
        "SAGEMAKER_AGENT_MAX_TURNS",
        minimum=1, maximum=10_000, default=CONFIG.max_turns,
    )
    CONFIG.max_iteration_budget = _vbiev(
        "SAGEMAKER_AGENT_MAX_ITERATION_BUDGET",
        minimum=1, maximum=100_000, default=CONFIG.max_iteration_budget,
    )
    CONFIG.audit_retention_days = _vbiev(
        "SAGEMAKER_AGENT_AUDIT_RETENTION_DAYS",
        minimum=0, maximum=3650, default=CONFIG.audit_retention_days,
    )
    CONFIG.max_exec_calls_per_session = _vbiev(
        "SAGEMAKER_AGENT_MAX_EXEC_CALLS",
        minimum=1, maximum=100_000, default=CONFIG.max_exec_calls_per_session,
    )
    CONFIG.max_exec_seconds_per_session = _vbiev(
        "SAGEMAKER_AGENT_MAX_EXEC_SECONDS",
        minimum=0, maximum=86_400, default=CONFIG.max_exec_seconds_per_session,
    )
except Exception:  # pragma: no cover — env-validation is best-effort
    # If anything goes wrong, keep CONFIG defaults; never block import.
    pass
