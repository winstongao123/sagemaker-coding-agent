"""V5 BedrockClient — verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560.

Per ADR-005: BedrockClient is a pure v4 reuse (Bedrock-native, already
production-tested). The only Phase-1 change is structural — the class lives
in its own module instead of inline in the v4 monolith.

Sophisticated cache-break detection (Runnable promptCacheBreakDetection.ts)
is DEFERRED to Phase 6 because it requires multi-block system prompts that
v5 doesn't have until prompt/sections.py lands. Phase 6 ADR will track that
adoption.

Phase 1 simplification: the full retry-classifier + jittered-backoff loop
lives in v4's BedrockClient. For Phase 1, we keep that loop intact (it's
already battle-tested), but the helper classes (BedrockErrorCategory,
ErrorClassifier, RetryPolicy) are imported from a temporary local module
inside this file. Phase 8 will extract them to core/errors.py + core/retry.py
with cleaner separation. This avoids a circular Phase-1/Phase-8 dependency.

PS Issue #4 verification (per V5_PS_ISSUES_MAPPING.md): tests/unit/test_bedrock.py
must verify thinking config is sent on EVERY Bedrock call when
CONFIG.thinking_enabled=True (not just the first turn).

Source: compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# botocore.config import is local-deferred so unit tests with mock_mode=True
# can import this module without boto3 installed. Real flows will import on demand.

# CONFIG is imported lazily within methods to avoid circular import during Phase 1.


# ============================================================
# Response / ToolCall (lightweight value types — verbatim from v4)
# ============================================================

@dataclass
class ToolCall:
    """A tool invocation request from the model."""
    id: str
    name: str
    input: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Parsed Bedrock response."""
    text: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    stop_reason: str = ""
    usage: Dict[str, Any] = field(default_factory=dict)
    thinking: str = ""


# ============================================================
# Error categories + classifier + retry policy
# (Verbatim port from v4. Phase 8 will extract to core/errors.py + core/retry.py.)
# ============================================================

class BedrockErrorCategory:
    """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy."""
    THROTTLE = "throttle"  # ThrottlingException, rate-limited
    SERVICE_UNAVAILABLE = "service_unavailable"
    MODEL_NOT_READY = "model_not_ready"
    NETWORK = "network"
    VALIDATION_CACHE = "validation_cache"  # cache_control rejected — strip and retry once
    VALIDATION_OTHER = "validation_other"
    CONTEXT_OVERFLOW = "context_overflow"  # prompt-too-long
    ACCESS_DENIED = "access_denied"
    UNKNOWN = "unknown"


class ErrorClassifier:
    """Classifies Bedrock exceptions into a (category, recovery, debug_msg) triple.

    Verbatim port of v4's classifier — Phase 8 may refactor for cleaner
    separation but Phase 1 keeps it bundled with BedrockClient to minimize
    cross-module dependencies.
    """

    @staticmethod
    def classify(exc: Exception):
        msg_lower = str(exc).lower()
        cls_name = type(exc).__name__.lower()

        if "validationexception" in msg_lower and (
            "cache_control" in msg_lower
            or "prompt-caching" in msg_lower
            or "cache" in msg_lower
        ):
            return BedrockErrorCategory.VALIDATION_CACHE, "strip_cache_retry", str(exc)[:200]
        if "validationexception" in msg_lower and (
            "prompt is too long" in msg_lower
            or "too many tokens" in msg_lower
            or "input length" in msg_lower
        ):
            return BedrockErrorCategory.CONTEXT_OVERFLOW, "compact_retry", str(exc)[:200]
        if "validationexception" in msg_lower:
            return BedrockErrorCategory.VALIDATION_OTHER, "no_retry", str(exc)[:200]
        if "throttlingexception" in msg_lower or "rate" in msg_lower:
            return BedrockErrorCategory.THROTTLE, "backoff", str(exc)[:200]
        if "serviceunavailable" in msg_lower or "503" in msg_lower:
            return BedrockErrorCategory.SERVICE_UNAVAILABLE, "backoff", str(exc)[:200]
        if "modelnotready" in msg_lower or "not ready" in msg_lower:
            return BedrockErrorCategory.MODEL_NOT_READY, "backoff", str(exc)[:200]
        if "accessdenied" in msg_lower or "403" in msg_lower or "unauthorized" in msg_lower:
            return BedrockErrorCategory.ACCESS_DENIED, "no_retry", str(exc)[:200]
        if (
            "endpointconnectionerror" in cls_name
            or "connecttimeout" in cls_name
            or "readtimeout" in cls_name
            or "connectionerror" in cls_name
        ):
            return BedrockErrorCategory.NETWORK, "backoff", str(exc)[:200]
        return BedrockErrorCategory.UNKNOWN, "no_retry", str(exc)[:200]


class RetryPolicy:
    """Jittered exponential backoff (v4 verbatim).

    MAX_RETRIES=4 means up to 5 total attempts (initial + 4 retries).
    Sleep curve: ~1s, 2s, 4s, 8s with up-to-30% jitter.
    """
    MAX_RETRIES = 4
    BASE_SECONDS = 1.0
    JITTER_FRACTION = 0.30
    BACKOFF_RECOVERY = {"backoff"}

    @staticmethod
    def should_retry(attempt: int, recovery: str) -> bool:
        if attempt >= RetryPolicy.MAX_RETRIES:
            return False
        return recovery in RetryPolicy.BACKOFF_RECOVERY

    @staticmethod
    def backoff_seconds(attempt: int) -> float:
        import random
        base = RetryPolicy.BASE_SECONDS * (2 ** attempt)
        jitter = base * RetryPolicy.JITTER_FRACTION * (2 * random.random() - 1)
        return max(0.1, base + jitter)


# ============================================================
# BedrockClient (v4 verbatim port)
# ============================================================

# botocore Config preset for retry tuning (v4 default).
def _bedrock_client_config():
    """Return a botocore Config with v4's retry tuning. Local-imports botocore."""
    from botocore.config import Config as _BotoConfig
    return _BotoConfig(
        retries={"max_attempts": 1, "mode": "standard"},  # we handle retries ourselves
        read_timeout=120,
        connect_timeout=10,
    )


class BedrockClient:
    """AWS Bedrock Claude client with mock mode for testing.

    Verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:2378.
    Behavior unchanged — same prompt-cache fallback semantics, same retry
    classifier, same thinking-mode handling.

    PS Issue #4 verification: `chat()` always sends `thinking` config when
    `thinking_enabled=True`, regardless of which call this is in the session.
    The fact that the model only RETURNS thinking blocks on some turns is a
    model-side decision; v5 always SENDS the config so the model has the
    option. test_bedrock.py verifies this.
    """

    def __init__(
        self,
        model_id: str,
        region: str,
        mock_mode: bool = False,
        client: Any = None,
    ):
        """Construct a BedrockClient.

        Args:
            model_id: Bedrock inference profile id.
            region: AWS region.
            mock_mode: if True, no real Bedrock calls; `_mock_response()` is used.
            client: optional pre-built bedrock-runtime client. If provided,
                boto3 is NOT imported. This lets unit tests inject a fake
                client without requiring boto3 to be installed (Codex Phase-01
                review finding 1).
        """
        self.model_id = model_id
        self.region = region
        self.mock_mode = mock_mode
        self.prompt_cache_supported = True  # set False after first cache fallback
        self._cache_threshold_warned = False
        if mock_mode:
            self.client = None
        elif client is not None:
            self.client = client
        else:
            import boto3
            self.client = boto3.client(
                "bedrock-runtime", region_name=region, config=_bedrock_client_config()
            )

    # ---------- mock-mode helpers ----------

    def _mock_response(self, messages, tools) -> Response:
        """Generate mock response for testing (v4 verbatim, simplified)."""
        last = messages[-1]["content"] if messages else ""
        if isinstance(last, str):
            low = last.lower()
            if "list" in low and ("file" in low or "dir" in low):
                return Response(
                    "I'll list the files.",
                    [ToolCall("m1", "list_dir", {"path": "."})],
                    "tool_use",
                    {},
                )
            if "read" in low:
                return Response(
                    "I'll read that file.",
                    [ToolCall("m2", "read_file", {"file_path": "README.md"})],
                    "tool_use",
                    {},
                )
        return Response(
            f"[MOCK] Received: {str(last)[:100]}...",
            [],
            "end_turn",
            {"input_tokens": 100, "output_tokens": 50},
        )

    # ---------- main chat entry ----------

    def chat(
        self,
        messages: List[Dict],
        system: Any,  # str OR list-of-blocks (with cache_control)
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
    ) -> Response:
        """Send chat request to Bedrock.

        Args:
            messages: Conversation messages
            system: System prompt (str or pre-formatted multi-block list with cache_control)
            tools: Tool definitions
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0.0-1.0)
            thinking_enabled: Enable extended thinking mode
            thinking_budget: Max tokens for thinking (1024-16000)
        """
        if self.mock_mode:
            return self._mock_response(messages, tools)

        # Lazy import CONFIG to avoid circular import during Phase 1.
        from runtime.config import CONFIG

        # V4.1 #14: Prompt cache boundary.
        # If cache enabled and supported, split system string into static (cached)
        # + dynamic (uncached) blocks. Bedrock supports prompt caching natively
        # via cache_control blocks in content. No anthropic_beta header needed.
        # Haiku 4.5: min 4096 tokens/checkpoint. Sonnet 4.5: min 1024.
        cache_active = CONFIG.enable_prompt_cache and self.prompt_cache_supported
        if cache_active and isinstance(system, list):
            # Already formatted as cache blocks by caller — pass as-is
            system_field = system
            use_cache = True
        elif cache_active and isinstance(system, str):
            # Split at the dynamic boundary marker if present, else cache full prompt
            _CACHE_BOUNDARY = "\n\n# === DYNAMIC ==="
            if _CACHE_BOUNDARY in system:
                static_part, dynamic_part = system.split(_CACHE_BOUNDARY, 1)
                # Bedrock rejects empty/whitespace text blocks — only add dynamic if non-empty
                if dynamic_part.strip():
                    system_field = [
                        {
                            "type": "text",
                            "text": static_part,
                            "cache_control": {"type": "ephemeral"},
                        },
                        {"type": "text", "text": dynamic_part},
                    ]
                else:
                    system_field = [
                        {
                            "type": "text",
                            "text": static_part,
                            "cache_control": {"type": "ephemeral"},
                        },
                    ]
            else:
                # No boundary — cache the whole prompt as static
                system_field = [
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"},
                    },
                ]
            use_cache = True
        else:
            system_field = system
            use_cache = False

        body: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_field,
            "messages": messages,
        }
        # Note: Bedrock prompt caching is activated by cache_control blocks in
        # content. No anthropic_beta header needed (that header is for the direct
        # Anthropic API only).

        # Extended thinking mode (requires temperature=1).
        # PS Issue #4: this block runs on EVERY chat() call when thinking_enabled
        # is True — not just first message. The model decides per turn whether
        # to USE the budget. tests/unit/test_bedrock.py asserts this contract.
        if thinking_enabled:
            body["thinking"] = {
                "type": "enabled",
                "budget_tokens": min(max(thinking_budget, 1024), 16000),
            }
            body["temperature"] = 1  # Required for thinking mode
        else:
            body["temperature"] = temperature

        if tools:
            body["tools"] = tools

        # V4.9.4: jittered exponential backoff on transient/throttle errors.
        # Cache-validation: strip cache blocks and retry once (existing v4.1 #14).
        attempt = 0
        last_exc: Optional[Exception] = None
        while True:
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body, separators=(",", ":")),
                    contentType="application/json",
                )
                break  # success
            except Exception as e:
                last_exc = e
                category, recovery, debug_msg = ErrorClassifier.classify(e)

                # Cache-validation: strip cache blocks, retry once
                if (
                    category == BedrockErrorCategory.VALIDATION_CACHE
                    and use_cache
                    and self.prompt_cache_supported
                ):
                    logging.warning(
                        f"[BEDROCK] Prompt cache not supported by this model/region, falling back: {debug_msg}"
                    )
                    self.prompt_cache_supported = False
                    if isinstance(system, str):
                        body["system"] = system
                    else:
                        body["system"] = "\n\n".join(
                            b.get("text", "") for b in system if isinstance(b, dict)
                        )
                    use_cache = False
                    continue

                # Throttle / transient / etc.: retry with jitter
                if RetryPolicy.should_retry(attempt, recovery):
                    sleep_s = RetryPolicy.backoff_seconds(attempt)
                    logging.warning(
                        f"[BEDROCK] {category} (recovery={recovery}, attempt={attempt + 1}/"
                        f"{RetryPolicy.MAX_RETRIES + 1}, sleep={sleep_s:.1f}s): {debug_msg}"
                    )
                    time.sleep(sleep_s)
                    attempt += 1
                    continue

                # Anything else: surface it
                logging.error(f"[BEDROCK] {category} (recovery={recovery}, no-retry): {debug_msg}")
                raise

        result = json.loads(response["body"].read())
        return self._parse(result)

    # ---------- response parsing ----------

    def _parse(self, result: dict) -> Response:
        """Parse Bedrock response into Response value type (v4 verbatim)."""
        text = ""
        thinking = ""
        tool_calls: List[ToolCall] = []
        for block in result.get("content", []):
            block_type = block.get("type")
            if block_type == "text":
                text += block.get("text", "")
            elif block_type == "thinking":
                thinking += block.get("thinking", "")
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
            thinking=thinking,
        )
