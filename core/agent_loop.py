"""
Agent Loop - Main ReAct loop with doom loop detection

Optimizations:
- History trimming to prevent token explosion
- Tool result truncation
"""
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque

# Token limits
MAX_HISTORY_MESSAGES = 20  # Keep last N messages
MAX_TOOL_RESULT_CHARS = 5000  # Truncate tool results


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
        on_text: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
        on_tool_result: Optional[Callable[[str, str], None]] = None,
        on_approval: Optional[Callable[[str, dict], bool]] = None,
        on_context_warning: Optional[Callable[[str], None]] = None,
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
            on_text: Callback for streaming text output
            on_tool_call: Callback when tool is about to be called
            on_tool_result: Callback with tool result
            on_approval: Callback for permission approval
            on_context_warning: Callback for context warnings
        """
        self.client = client
        self.registry = registry
        self.system_prompt = system_prompt
        self.context = context
        self.max_turns = max_turns
        self.doom_threshold = doom_threshold
        self.on_text = on_text or print
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.on_approval = on_approval
        self.on_context_warning = on_context_warning
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

        final_response = ""

        while self.state.turn_count < self.max_turns:
            self.state.turn_count += 1

            # Call LLM
            try:
                response = self.client.chat(
                    messages=self.state.messages,
                    system=self.system_prompt,
                    tools=self.registry.get_tool_definitions(),
                )
            except Exception as e:
                error_msg = f"Error calling LLM: {e}"
                self.on_text(error_msg)
                return error_msg

            # Output text
            if response.text:
                self.on_text(response.text)
                final_response = response.text

            # No tool calls = done
            if not response.tool_calls:
                break

            # Check doom loop
            if self._detect_doom_loop(response.tool_calls):
                warning = "\n[Warning: Detected repetitive tool calls. Breaking loop.]"
                self.on_text(warning)
                break

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

            # Execute tools
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
                    on_text=self.on_text,
                )
            except Exception as e:
                error_msg = f"Error calling LLM: {e}"
                self.on_text(error_msg)
                return error_msg

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
