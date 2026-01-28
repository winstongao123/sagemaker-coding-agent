"""
Bedrock Client - AWS Bedrock API wrapper for Claude models

Supports mock mode for testing without Bedrock access.
"""
import boto3
import json
import re
from typing import Generator, List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToolCall:
    """Represents a tool call from the model."""

    id: str
    name: str
    input: dict


@dataclass
class Response:
    """Parsed response from Bedrock."""

    text: str
    tool_calls: List[ToolCall]
    stop_reason: str
    usage: dict


class BedrockClient:
    """Client for AWS Bedrock Claude models."""

    def __init__(self, model_id: str, region: str = "ap-southeast-2", mock_mode: bool = False):
        """
        Initialize Bedrock client.

        Args:
            model_id: Bedrock model identifier
            region: AWS region (default: Sydney)
            mock_mode: If True, return mock responses without calling Bedrock
        """
        self.model_id = model_id
        self.region = region
        self.mock_mode = mock_mode

        if not mock_mode:
            self.client = boto3.client("bedrock-runtime", region_name=region)
        else:
            self.client = None
            print("[MOCK MODE] Bedrock client running in mock mode - no API calls")

    def _mock_response(self, messages: List[Dict], tools: Optional[List[Dict]]) -> Response:
        """Generate a mock response for testing."""
        last_msg = messages[-1]["content"] if messages else ""

        # Simple mock logic based on message content
        if isinstance(last_msg, str):
            msg_lower = last_msg.lower()

            # If asking to list/read files, mock a tool call
            if "list" in msg_lower and "file" in msg_lower:
                return Response(
                    text="I'll list the files for you.",
                    tool_calls=[ToolCall(id="mock_1", name="list_dir", input={"path": "."})],
                    stop_reason="tool_use",
                    usage={"input_tokens": 100, "output_tokens": 50}
                )
            elif "read" in msg_lower:
                # Extract filename if mentioned
                return Response(
                    text="I'll read that file.",
                    tool_calls=[ToolCall(id="mock_2", name="read_file", input={"file_path": "config.py"})],
                    stop_reason="tool_use",
                    usage={"input_tokens": 100, "output_tokens": 50}
                )
            elif "search" in msg_lower or "find" in msg_lower:
                return Response(
                    text="I'll search for that.",
                    tool_calls=[ToolCall(id="mock_3", name="grep", input={"pattern": "TODO", "path": "."})],
                    stop_reason="tool_use",
                    usage={"input_tokens": 100, "output_tokens": 50}
                )

        # Default: just return text
        return Response(
            text=f"[MOCK] I received your message. In mock mode, I can simulate tool calls but not actually reason. Your message was: {str(last_msg)[:100]}...",
            tool_calls=[],
            stop_reason="end_turn",
            usage={"input_tokens": 100, "output_tokens": 50}
        )

    def chat(
        self,
        messages: List[Dict],
        system: str,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Response:
        """
        Send chat request to Bedrock Claude.

        Args:
            messages: Conversation messages
            system: System prompt
            tools: Tool definitions
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            Parsed Response object
        """
        # Mock mode - return fake response
        if self.mock_mode:
            return self._mock_response(messages, tools)

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            body["tools"] = tools

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
        )

        result = json.loads(response["body"].read())
        return self._parse_response(result)

    def stream_chat(
        self,
        messages: List[Dict],
        system: str,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        on_text: Optional[callable] = None,
    ) -> Response:
        """
        Stream chat response from Bedrock Claude.

        Args:
            messages: Conversation messages
            system: System prompt
            tools: Tool definitions
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            on_text: Callback for streaming text chunks

        Returns:
            Final parsed Response object
        """
        # Mock mode - return fake response
        if self.mock_mode:
            response = self._mock_response(messages, tools)
            if on_text and response.text:
                on_text(response.text)
            return response

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            body["tools"] = tools

        response = self.client.invoke_model_with_response_stream(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
        )

        # Collect streaming response
        content_blocks = []
        current_block = None
        current_text = ""
        stop_reason = ""
        usage = {}

        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            event_type = chunk.get("type")

            if event_type == "content_block_start":
                current_block = chunk.get("content_block", {})
                if current_block.get("type") == "text":
                    current_text = current_block.get("text", "")

            elif event_type == "content_block_delta":
                delta = chunk.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    current_text += text
                    if on_text:
                        on_text(text)
                elif delta.get("type") == "input_json_delta":
                    # Tool input being streamed
                    if current_block:
                        current_block["partial_input"] = current_block.get("partial_input", "") + delta.get(
                            "partial_json", ""
                        )

            elif event_type == "content_block_stop":
                if current_block:
                    if current_block.get("type") == "text":
                        current_block["text"] = current_text
                    elif current_block.get("type") == "tool_use":
                        # Parse the accumulated JSON
                        if "partial_input" in current_block:
                            try:
                                current_block["input"] = json.loads(current_block["partial_input"])
                            except json.JSONDecodeError:
                                current_block["input"] = {}
                            del current_block["partial_input"]
                    content_blocks.append(current_block)
                current_block = None
                current_text = ""

            elif event_type == "message_delta":
                stop_reason = chunk.get("delta", {}).get("stop_reason", "")
                usage = chunk.get("usage", {})

            elif event_type == "message_stop":
                pass

        # Build final result
        result = {"content": content_blocks, "stop_reason": stop_reason, "usage": usage}

        return self._parse_response(result)

    def _parse_response(self, result: dict) -> Response:
        """Parse Bedrock response into Response object."""
        text = ""
        tool_calls = []

        for block in result.get("content", []):
            block_type = block.get("type")

            if block_type == "text":
                text += block.get("text", "")
            elif block_type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id", ""),
                        name=block.get("name", ""),
                        input=block.get("input", {}),
                    )
                )

        return Response(
            text=text,
            tool_calls=tool_calls,
            stop_reason=result.get("stop_reason", ""),
            usage=result.get("usage", {}),
        )

    @staticmethod
    def discover_models(region: str = "ap-southeast-2") -> Dict[str, Any]:
        """
        Discover available Bedrock Claude models and check permissions.

        Returns:
            Dictionary with available models and permission issues
        """
        bedrock = boto3.client("bedrock", region_name=region)
        runtime = boto3.client("bedrock-runtime", region_name=region)

        results = {
            "region": region,
            "available_models": [],
            "permission_issues": [],
            "recommended_model": None,
        }

        # Claude models to check (newest first)
        claude_models = [
            ("anthropic.claude-3-5-sonnet-20241022-v2:0", "Claude 3.5 Sonnet v2"),
            ("anthropic.claude-3-5-sonnet-20240620-v1:0", "Claude 3.5 Sonnet"),
            ("anthropic.claude-3-opus-20240229-v1:0", "Claude 3 Opus"),
            ("anthropic.claude-3-sonnet-20240229-v1:0", "Claude 3 Sonnet"),
            ("anthropic.claude-3-haiku-20240307-v1:0", "Claude 3 Haiku"),
        ]

        for model_id, display_name in claude_models:
            try:
                # Test invoke with minimal tokens
                response = runtime.invoke_model(
                    modelId=model_id,
                    body=json.dumps(
                        {
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 10,
                            "messages": [{"role": "user", "content": "Hi"}],
                        }
                    ),
                    contentType="application/json",
                )
                results["available_models"].append(
                    {"id": model_id, "name": display_name, "status": "available"}
                )

                if results["recommended_model"] is None:
                    results["recommended_model"] = model_id

            except runtime.exceptions.AccessDeniedException:
                results["permission_issues"].append(
                    {"model": model_id, "name": display_name, "error": "Access denied - model not enabled"}
                )
            except runtime.exceptions.ValidationException:
                results["permission_issues"].append(
                    {"model": model_id, "name": display_name, "error": f"Not available in {region}"}
                )
            except Exception as e:
                results["permission_issues"].append(
                    {"model": model_id, "name": display_name, "error": str(e)}
                )

        return results
