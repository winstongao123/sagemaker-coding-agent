"""
Agent Loop - Main ReAct loop with doom loop detection

Optimizations:
- History trimming to prevent token explosion
- Tool result truncation
- Retry with exponential backoff (OpenCode-style)
- Smart context compaction (OpenCode-style)
- 5-layer tool error recovery
"""
from typing import List, Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
import time
import random
import re

# Token limits
MAX_HISTORY_MESSAGES = 20  # Keep last N messages
MAX_TOOL_RESULT_CHARS = 5000  # Truncate tool results


# ============================================================
# RETRY LOGIC (OpenCode-style)
# ============================================================

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

        for msg in self.RETRYABLE_MESSAGES:
            if msg in error_str:
                match = re.search(r'retry.?after[:\s]+(\d+)', error_str)
                retry_after = float(match.group(1)) if match else None
                return True, retry_after

        for code in self.RETRYABLE_CODES:
            if str(code) in error_str:
                return True, None

        return False, None

    def get_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """Calculate delay with exponential backoff + jitter."""
        if retry_after:
            return min(retry_after, self.max_delay)
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


# ============================================================
# CONTEXT COMPACTION (OpenCode-style)
# ============================================================

class Compactor:
    """Smart context compaction - prune then summarize."""

    PRUNE_PROTECT_TOKENS = 40000
    PRUNE_MIN_SAVINGS = 10000
    SUMMARY_TRIGGER_PERCENT = 0.80

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return len(text) // 4

    @classmethod
    def prune_tool_outputs(cls, messages: List[Dict], max_context: int) -> Tuple[List[Dict], int]:
        """Prune old tool outputs while keeping recent ones."""
        if not messages:
            return messages, 0

        tool_results = []
        for i, msg in enumerate(messages):
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

        protected_tokens = 0
        tokens_saved = 0
        pruned_messages = [m.copy() for m in messages]

        for tr in reversed(tool_results):
            if protected_tokens < cls.PRUNE_PROTECT_TOKENS:
                protected_tokens += tr["tokens"]
            else:
                content = tr["item"].get("content", "")
                if len(content) > 200:
                    tr["item"]["content"] = content[:100] + f"\n[... {len(content)} chars pruned ...]\n" + content[-100:]
                    tokens_saved += tr["tokens"] - 60

        if tokens_saved < cls.PRUNE_MIN_SAVINGS:
            return messages, 0

        return pruned_messages, tokens_saved

    @classmethod
    def should_compact(cls, messages: List[Dict], max_tokens: int) -> bool:
        total_tokens = sum(cls.estimate_tokens(str(m.get("content", ""))) for m in messages)
        return total_tokens > max_tokens * cls.SUMMARY_TRIGGER_PERCENT

    @classmethod
    def compact(cls, messages: List[Dict], summary: str) -> List[Dict]:
        summary_msg = {
            "role": "assistant",
            "content": f"[CONVERSATION SUMMARY]\n{summary}\n[END SUMMARY]"
        }
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        return [summary_msg] + recent_messages


# ============================================================
# SMART TRUNCATION (OpenCode-style)
# ============================================================

import os
from datetime import datetime

class Truncation:
    """Smart truncation for large outputs - saves full content, returns preview."""

    MAX_LINES = 2000
    MAX_BYTES = 50 * 1024  # 50 KB
    MAX_LINE_LENGTH = 2000
    TRUNCATED_DIR = "./truncated_outputs"

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


def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars per token)."""
    return len(str(text)) // 4


def truncate_tool_result(result: str, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
    """Truncate tool result to save tokens."""
    if len(result) <= max_chars:
        return result
    return result[:max_chars] + f"\n\n[Truncated - {len(result)} chars total, showing first {max_chars}]"


def trim_history(messages: List[Dict], max_messages: int = MAX_HISTORY_MESSAGES) -> List[Dict]:
    """
    Trim message history to prevent context explosion.

    Keeps the most recent messages and adds a summary marker.
    """
    if len(messages) <= max_messages:
        return messages

    # Keep last max_messages
    trimmed = messages[-max_messages:]

    # Add marker that history was trimmed
    summary = {
        "role": "user",
        "content": f"[Previous {len(messages) - max_messages} messages trimmed to save context]"
    }

    return [summary] + trimmed


@dataclass
class AgentState:
    """State of the agent during execution."""

    messages: List[Dict] = field(default_factory=list)
    tool_history: deque = field(default_factory=lambda: deque(maxlen=10))
    turn_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class AgentLoop:
    """Main agent loop implementing ReAct pattern."""

    def __init__(
        self,
        client,  # BedrockClient
        registry,  # ToolRegistry
        system_prompt: str,
        context,  # ToolContext
        max_turns: int = 50,
        doom_threshold: int = 3,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
        on_text: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
        on_tool_result: Optional[Callable[[str, str], None]] = None,
        on_approval: Optional[Callable[[str, dict], bool]] = None,
        on_context_warning: Optional[Callable[[str], None]] = None,
        on_tokens: Optional[Callable[[dict], None]] = None,
    ):
        """
        Initialize agent loop.

        Args:
            client: BedrockClient for LLM calls
            registry: ToolRegistry with available tools
            system_prompt: System prompt for the agent
            context: ToolContext for tool execution
            max_turns: Maximum number of turns before stopping
            doom_threshold: Number of identical tool calls to trigger doom detection
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0.0-1.0)
            thinking_enabled: Enable extended thinking mode
            thinking_budget: Token budget for thinking (1024-16000)
            on_text: Callback for streaming text output
            on_thinking: Callback for streaming thinking output
            on_tool_call: Callback when tool is about to be called
            on_tool_result: Callback with tool result
            on_approval: Callback for permission approval
            on_context_warning: Callback for context warnings
            on_tokens: Callback for token usage updates
        """
        self.client = client
        self.registry = registry
        self.system_prompt = system_prompt
        self.context = context
        self.max_turns = max_turns
        self.doom_threshold = doom_threshold
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.thinking_enabled = thinking_enabled
        self.thinking_budget = thinking_budget
        self.on_text = on_text or print
        self.on_thinking = on_thinking
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.on_approval = on_approval
        self.on_context_warning = on_context_warning
        self.on_tokens = on_tokens
        self.state = AgentState()

    def run(self, user_message: str) -> str:
        """
        Run agent loop until completion.

        Args:
            user_message: User's input message

        Returns:
            Final response text
        """
        # Add user message
        self.state.messages.append({"role": "user", "content": user_message})

        # Initialize retry handler
        retry_handler = RetryHandler(max_retries=5, base_delay=2.0, max_delay=60.0)
        compactor = Compactor()

        final_response = ""

        while self.state.turn_count < self.max_turns:
            self.state.turn_count += 1

            # Smart compaction when context gets high (OpenCode-style)
            # Assuming 200K token context for Claude
            context_max_tokens = 200000
            if compactor.should_compact(self.state.messages, context_max_tokens):
                pruned_messages, tokens_saved = compactor.prune_tool_outputs(self.state.messages, context_max_tokens)
                if tokens_saved > 0:
                    self.state.messages = pruned_messages
                    self.on_text(f"[i] Pruned old tool outputs, saved ~{tokens_saved:,} tokens")

                if compactor.should_compact(self.state.messages, context_max_tokens):
                    self.on_text("[i] Context high - creating summary...")
                    summary = "Previous conversation covered: " + ", ".join(
                        m.get("content", "")[:50] if isinstance(m.get("content"), str) else "tool calls"
                        for m in self.state.messages[:5]
                    )
                    self.state.messages = compactor.compact(self.state.messages, summary)
                    self.on_text("[i] Conversation compacted to preserve context")

            # Call LLM with retry logic
            def make_request():
                return self.client.chat(
                    messages=self.state.messages,
                    system=self.system_prompt,
                    tools=self.registry.get_tool_definitions(),
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    thinking_enabled=self.thinking_enabled,
                    thinking_budget=self.thinking_budget,
                )

            def on_retry(attempt, max_retries, delay, error):
                self.on_text(f"[Retry {attempt}/{max_retries} in {delay:.1f}s: {error[:50]}...]")

            try:
                response = retry_handler.execute(make_request, on_retry)
            except Exception as e:
                error_msg = f"Error calling LLM: {e}"
                self.on_text(error_msg)
                return error_msg

            # Output thinking (if available)
            if response.thinking and self.on_thinking:
                self.on_thinking(response.thinking)

            # Track token usage
            if response.usage:
                input_tokens = response.usage.get("input_tokens", 0)
                output_tokens = response.usage.get("output_tokens", 0)
                self.state.total_input_tokens += input_tokens
                self.state.total_output_tokens += output_tokens
                if self.on_tokens:
                    self.on_tokens({
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_input": self.state.total_input_tokens,
                        "total_output": self.state.total_output_tokens,
                        "api_calls": self.state.turn_count,
                    })

            # Output text
            if response.text:
                self.on_text(response.text)
                final_response = response.text

            # No tool calls = done
            if not response.tool_calls:
                break

            # Improved doom loop detection (based on file path, not full content)
            for tc in response.tool_calls:
                target = tc.input.get("file_path") or tc.input.get("path") or tc.input.get("filepath") or tc.input.get("command", "")[:50] or str(tc.input)[:50]
                key = (tc.name, target)

                repeat_count = sum(1 for h in self.state.tool_history if h == key)
                if repeat_count >= self.doom_threshold:
                    self.on_text(f"[Warning: Repetitive {tc.name} calls to '{target[:30]}' detected, stopping]")
                    return final_response

                # Skip consecutive file rewrites
                if tc.name in ("write_file", "edit_file") and self.state.tool_history:
                    last_key = self.state.tool_history[-1] if self.state.tool_history else None
                    if last_key and last_key[0] == tc.name and last_key[1] == target:
                        self.on_text(f"[Skipping duplicate {tc.name} to '{target[:30]}']")
                        continue

                self.state.tool_history.append(key)

            # Build assistant message with tool calls
            assistant_content = []
            if response.text:
                assistant_content.append({"type": "text", "text": response.text})

            for tc in response.tool_calls:
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    }
                )

            self.state.messages.append({"role": "assistant", "content": assistant_content})

            # Execute tools with 5-layer error recovery
            tool_results = []
            for tc in response.tool_calls:
                # Notify about tool call
                if self.on_tool_call:
                    self.on_tool_call(tc.name, tc.input)

                # Check if tool requires approval
                tool = self.registry.get(tc.name)
                if tool and tool.requires_approval and self.on_approval:
                    approved = self.on_approval(tc.name, tc.input)
                    if not approved:
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tc.id,
                                "content": "User denied permission for this operation.",
                            }
                        )
                        continue

                # Execute tool
                result = self.registry.execute(tc.name, tc.input, self.context)

                # Notify about result
                if self.on_tool_result:
                    self.on_tool_result(tc.name, result)

                # Truncate result to save tokens
                truncated_result = truncate_tool_result(result)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tc.id, "content": truncated_result}
                )

                # Track for doom loop detection
                self.state.tool_history.append((tc.name, str(tc.input)))

            # Add tool results as user message
            self.state.messages.append({"role": "user", "content": tool_results})

            # Trim history if getting too long
            self.state.messages = trim_history(self.state.messages)

        if self.state.turn_count >= self.max_turns:
            warning = f"\n[Warning: Reached maximum turns ({self.max_turns}). Stopping.]"
            self.on_text(warning)

        return final_response

    def run_streaming(self, user_message: str) -> str:
        """
        Run agent loop with streaming output.

        Args:
            user_message: User's input message

        Returns:
            Final response text
        """
        # Add user message
        self.state.messages.append({"role": "user", "content": user_message})

        final_response = ""

        while self.state.turn_count < self.max_turns:
            self.state.turn_count += 1

            # Call LLM with streaming
            try:
                response = self.client.stream_chat(
                    messages=self.state.messages,
                    system=self.system_prompt,
                    tools=self.registry.get_tool_definitions(),
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    on_text=self.on_text,
                    on_thinking=self.on_thinking,
                    thinking_enabled=self.thinking_enabled,
                    thinking_budget=self.thinking_budget,
                )
            except Exception as e:
                error_msg = f"Error calling LLM: {e}"
                self.on_text(error_msg)
                return error_msg

            # Track token usage
            if response.usage:
                input_tokens = response.usage.get("input_tokens", 0)
                output_tokens = response.usage.get("output_tokens", 0)
                self.state.total_input_tokens += input_tokens
                self.state.total_output_tokens += output_tokens
                if self.on_tokens:
                    self.on_tokens({
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_input": self.state.total_input_tokens,
                        "total_output": self.state.total_output_tokens,
                        "api_calls": self.state.turn_count,
                    })

            if response.text:
                final_response = response.text

            # No tool calls = done
            if not response.tool_calls:
                break

            # Check doom loop
            if self._detect_doom_loop(response.tool_calls):
                warning = "\n[Warning: Detected repetitive tool calls. Breaking loop.]"
                self.on_text(warning)
                break

            # Build assistant message
            assistant_content = []
            if response.text:
                assistant_content.append({"type": "text", "text": response.text})

            for tc in response.tool_calls:
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    }
                )

            self.state.messages.append({"role": "assistant", "content": assistant_content})

            # Execute tools
            tool_results = []
            for tc in response.tool_calls:
                if self.on_tool_call:
                    self.on_tool_call(tc.name, tc.input)

                tool = self.registry.get(tc.name)
                if tool and tool.requires_approval and self.on_approval:
                    approved = self.on_approval(tc.name, tc.input)
                    if not approved:
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tc.id,
                                "content": "User denied permission for this operation.",
                            }
                        )
                        continue

                result = self.registry.execute(tc.name, tc.input, self.context)

                if self.on_tool_result:
                    self.on_tool_result(tc.name, result)

                # Truncate result to save tokens
                truncated_result = truncate_tool_result(result)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tc.id, "content": truncated_result}
                )

                self.state.tool_history.append((tc.name, str(tc.input)))

            self.state.messages.append({"role": "user", "content": tool_results})

            # Trim history if getting too long
            self.state.messages = trim_history(self.state.messages)

        return final_response

    def _detect_doom_loop(self, tool_calls: List) -> bool:
        """
        Detect if same tool called with same args multiple times.

        Args:
            tool_calls: List of tool calls from current response

        Returns:
            True if doom loop detected
        """
        if len(self.state.tool_history) < self.doom_threshold:
            return False

        for tc in tool_calls:
            key = (tc.name, str(tc.input))
            count = sum(1 for h in self.state.tool_history if h == key)
            if count >= self.doom_threshold:
                return True

        return False

    def reset(self):
        """Reset agent state for new conversation."""
        self.state = AgentState()

    def get_messages(self) -> List[Dict]:
        """Get current conversation messages."""
        return self.state.messages.copy()

    def get_turn_count(self) -> int:
        """Get current turn count."""
        return self.state.turn_count

    def get_token_usage(self) -> Dict:
        """Get current token usage statistics."""
        return {
            "input_tokens": self.state.total_input_tokens,
            "output_tokens": self.state.total_output_tokens,
            "total_tokens": self.state.total_input_tokens + self.state.total_output_tokens,
            "api_calls": self.state.turn_count,
        }
