"""
SageMaker Coding Agent - Configuration
"""
from dataclasses import dataclass, field
from typing import Optional, Set
import json
import os


@dataclass
class AgentConfig:
    """Agent configuration with security defaults."""

    # Region settings (default: Sydney)
    region: str = "ap-southeast-2"

    # Model preferences (Claude family)
    primary_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    fallback_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    fast_model: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # Paths
    workspace_root: str = "."
    sessions_dir: str = "./sessions"
    audit_dir: str = "./audit_logs"
    index_dir: str = "./.code_index"

    # Agent limits
    max_tokens: int = 4096
    max_turns: int = 50
    doom_loop_threshold: int = 3

    # Security settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_output_size: int = 50 * 1024  # 50KB
    default_timeout: int = 120  # seconds
    max_timeout: int = 600  # 10 minutes
    allow_network: bool = False

    # Context management
    max_context_tokens: int = 200_000
    warning_threshold_80: float = 0.80
    warning_threshold_90: float = 0.90
    warning_threshold_95: float = 0.95

    @classmethod
    def load(cls, path: str = "./agent_config.json") -> "AgentConfig":
        """Load config from JSON file."""
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return cls(**data)
        return cls()

    def save(self, path: str = "./agent_config.json"):
        """Save config to JSON file."""
        data = {
            "region": self.region,
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "fast_model": self.fast_model,
            "workspace_root": self.workspace_root,
            "sessions_dir": self.sessions_dir,
            "audit_dir": self.audit_dir,
            "max_tokens": self.max_tokens,
            "max_turns": self.max_turns,
            "doom_loop_threshold": self.doom_loop_threshold,
            "max_file_size": self.max_file_size,
            "max_output_size": self.max_output_size,
            "default_timeout": self.default_timeout,
            "allow_network": self.allow_network,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def get_workspace_abs(self) -> str:
        """Get absolute path to workspace root."""
        return os.path.abspath(self.workspace_root)
