"""
Context Manager - Monitors context usage and handles compaction
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class ContextCheckpoint:
    """Checkpoint saved before context compaction."""

    timestamp: str
    context_usage_percent: float
    current_task: str
    important_data: Dict
    last_user_messages: List[str]  # Last 3 user messages
    last_assistant_messages: List[str]  # Last 3 assistant responses
    next_steps: List[str]


class ContextManager:
    """Monitors context usage and handles compaction."""

    # Context limits (Claude 3.5 Sonnet = 200K tokens)
    MAX_TOKENS = 200_000
    WARNING_THRESHOLD_80 = 0.80
    WARNING_THRESHOLD_90 = 0.90
    WARNING_THRESHOLD_95 = 0.95

    def __init__(self, workspace_dir: str = "."):
        """
        Initialize context manager.

        Args:
            workspace_dir: Directory for checkpoint file
        """
        self.workspace_dir = workspace_dir
        self.checkpoint_path = os.path.join(workspace_dir, "_context_checkpoint.json")
        self.message_count = 0
        self.last_warning_level = 0

    def estimate_tokens(self, messages: List[Dict]) -> int:
        """
        Rough token estimation (4 chars = 1 token).

        Args:
            messages: List of conversation messages

        Returns:
            Estimated token count
        """
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

    def get_usage_percent(self, messages: List[Dict]) -> float:
        """
        Get current context usage as percentage.

        Args:
            messages: List of conversation messages

        Returns:
            Usage percentage (0.0 to 1.0)
        """
        tokens = self.estimate_tokens(messages)
        return tokens / self.MAX_TOKENS

    def check_and_warn(self, messages: List[Dict]) -> Optional[str]:
        """
        Check context usage and return warning if needed.

        Args:
            messages: List of conversation messages

        Returns:
            Warning message or None
        """
        usage = self.get_usage_percent(messages)
        tokens = self.estimate_tokens(messages)

        if usage >= self.WARNING_THRESHOLD_95:
            if self.last_warning_level < 95:
                self.last_warning_level = 95
                return f"[!] Context at 95% ({tokens:,}/{self.MAX_TOKENS:,} tokens). Compaction imminent!"

        elif usage >= self.WARNING_THRESHOLD_90:
            if self.last_warning_level < 90:
                self.last_warning_level = 90
                return f"[!] Context at 90% ({tokens:,}/{self.MAX_TOKENS:,} tokens). Approaching limit."

        elif usage >= self.WARNING_THRESHOLD_80:
            if self.last_warning_level < 80:
                self.last_warning_level = 80
                self.save_checkpoint(messages)
                return f"[i] Context at 80% ({tokens:,}/{self.MAX_TOKENS:,} tokens). Checkpoint saved."

        return None

    def save_checkpoint(
        self,
        messages: List[Dict],
        current_task: str = "",
        important_data: Optional[Dict] = None,
        next_steps: Optional[List[str]] = None,
    ):
        """
        Save context checkpoint before potential compaction.

        Args:
            messages: Current conversation messages
            current_task: Description of current task
            important_data: Important data to preserve
            next_steps: List of planned next steps
        """
        # Extract last 3 user/assistant messages
        user_msgs = []
        asst_msgs = []

        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "")

            # Convert content to string
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        text_parts.append(block.get("text", "") or block.get("content", ""))
                    else:
                        text_parts.append(str(block))
                content_str = " ".join(text_parts)
            else:
                content_str = str(content)

            # Truncate to 500 chars
            content_str = content_str[:500]

            if role == "user":
                user_msgs.append(content_str)
            elif role == "assistant":
                asst_msgs.append(content_str)

        checkpoint = ContextCheckpoint(
            timestamp=datetime.now().isoformat(),
            context_usage_percent=self.get_usage_percent(messages),
            current_task=current_task,
            important_data=important_data or {},
            last_user_messages=user_msgs[-3:],
            last_assistant_messages=asst_msgs[-3:],
            next_steps=next_steps or [],
        )

        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(asdict(checkpoint), f, indent=2)

    def load_checkpoint(self) -> Optional[ContextCheckpoint]:
        """
        Load checkpoint from previous session.

        Returns:
            ContextCheckpoint or None if not found
        """
        if not os.path.exists(self.checkpoint_path):
            return None

        try:
            with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ContextCheckpoint(**data)
        except (json.JSONDecodeError, TypeError):
            return None

    def has_checkpoint(self) -> bool:
        """Check if checkpoint exists."""
        return os.path.exists(self.checkpoint_path)

    def delete_checkpoint(self):
        """Delete checkpoint after task complete."""
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path)

    def format_checkpoint_summary(self) -> str:
        """
        Format checkpoint for display to user.

        Returns:
            Formatted checkpoint summary
        """
        cp = self.load_checkpoint()
        if not cp:
            return "No checkpoint found."

        lines = [
            "## Context Checkpoint Loaded",
            f"**Saved:** {cp.timestamp}",
            f"**Usage:** {cp.context_usage_percent:.1%}",
            "",
            "### Last User Messages:",
        ]

        for i, msg in enumerate(cp.last_user_messages, 1):
            lines.append(f"{i}. {msg[:100]}...")

        lines.extend(
            [
                "",
                "### Current Task:",
                cp.current_task or "Not specified",
                "",
                "### Next Steps:",
            ]
        )

        if cp.next_steps:
            for step in cp.next_steps:
                lines.append(f"- {step}")
        else:
            lines.append("None specified")

        return "\n".join(lines)

    def get_status(self, messages: List[Dict]) -> Dict:
        """
        Get current context status.

        Returns:
            Status dictionary with tokens, percentage, and warning level
        """
        tokens = self.estimate_tokens(messages)
        usage = tokens / self.MAX_TOKENS

        return {
            "tokens": tokens,
            "max_tokens": self.MAX_TOKENS,
            "usage_percent": usage,
            "warning_level": (
                "critical"
                if usage >= 0.95
                else "high" if usage >= 0.90 else "medium" if usage >= 0.80 else "normal"
            ),
            "has_checkpoint": self.has_checkpoint(),
        }
