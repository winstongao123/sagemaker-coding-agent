"""V5 Phase 01 unit tests: BedrockClient + Config + thinking-config-on-every-call.

Locks the contract for ADR-005 (BedrockClient port) and addresses PS Issue #4
verification (thinking config sent on every call, not just first message —
the model decides per turn whether to USE the budget).

Tests are runnable without boto3 by using mock_mode=True throughout. Real
Bedrock invocation paths are integration-tested in Phase 8.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from unittest import mock

# Make `runtime` importable from this test (mirrors flat-zip ship layout).
_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Config tests
# ============================================================

def test_config_singleton_loads():
    """CONFIG singleton at module import time without raising."""
    from runtime.config import CONFIG
    assert CONFIG is not None
    assert CONFIG.region == "ap-southeast-2"
    # default model id should be Sonnet 4.5 (v4.10.1 user choice)
    assert "sonnet" in CONFIG.model_id.lower()


def test_config_v4_critical_defaults_preserved():
    """v4.10.10 final-state critical defaults are preserved verbatim."""
    from runtime.config import Config
    c = Config()
    # PS Issue #2: iteration budget bumped 90 -> 600
    assert c.max_iteration_budget == 600
    # PS Issue #7: exec call limit bumped 40 -> 200
    assert c.max_exec_calls_per_session == 200
    # v4.9.6: skill auto-trigger off by default
    assert c.enable_skill_auto_trigger is False
    # v4.10.4: subagent handoff on by default
    assert c.enable_subagent_handoff is True
    # v4.10.2: enforce_verify_contract suggest-not-mandatory by default
    assert c.enforce_verify_contract is False
    # v4.9.5: skill self-patching opt-in
    assert c.enable_skill_patching is False
    # prompt cache on by default (Bedrock GA feature)
    assert c.enable_prompt_cache is True
    # context window for Sonnet/Haiku 4.5
    assert c.context_max_tokens == 200000


def test_strip_jsonc_comments_handles_strings_and_blocks():
    """JSONC comment stripper preserves strings and handles // and /* */."""
    from runtime.config import _strip_jsonc_comments

    # Line comment
    src = '{\n  "a": 1, // line comment\n  "b": 2\n}'
    out = _strip_jsonc_comments(src)
    assert "// line comment" not in out
    assert '"a": 1' in out and '"b": 2' in out

    # Block comment
    src = '{\n  "a": 1, /* block */\n  "b": 2\n}'
    out = _strip_jsonc_comments(src)
    assert "/* block */" not in out
    assert '"a": 1' in out and '"b": 2' in out

    # // INSIDE a string must be preserved (not treated as comment)
    src = '{"url": "http://example.com"}'
    out = _strip_jsonc_comments(src)
    assert out == src  # unchanged


# ============================================================
# BedrockClient mock-mode tests
# ============================================================

def test_bedrock_client_mock_mode_no_boto():
    """mock_mode=True allows BedrockClient instantiation without boto3 client."""
    from runtime.bedrock_client import BedrockClient
    c = BedrockClient(model_id="test", region="ap-southeast-2", mock_mode=True)
    assert c.client is None
    assert c.mock_mode is True


def test_bedrock_client_mock_response_shape():
    """Mock response returns Response with parsed text/tool_calls/stop_reason."""
    from runtime.bedrock_client import BedrockClient, Response
    c = BedrockClient(model_id="test", region="ap-southeast-2", mock_mode=True)
    resp = c.chat(
        messages=[{"role": "user", "content": "hello"}],
        system="you are helpful",
    )
    assert isinstance(resp, Response)
    assert resp.stop_reason in ("end_turn", "tool_use")


def test_bedrock_client_mock_routes_list_files_to_list_dir():
    """Mock heuristic: 'list files' triggers list_dir tool call (smoke v4 parity)."""
    from runtime.bedrock_client import BedrockClient
    c = BedrockClient(model_id="test", region="ap-southeast-2", mock_mode=True)
    resp = c.chat(
        messages=[{"role": "user", "content": "please list files in current dir"}],
        system="you are helpful",
    )
    assert resp.stop_reason == "tool_use"
    assert any(tc.name == "list_dir" for tc in resp.tool_calls)


# ============================================================
# PS Issue #4 verification: thinking config sent EVERY call
# ============================================================

def test_thinking_config_sent_on_every_call_when_enabled(monkeypatch):
    """PS Issue #4 (verification): when thinking_enabled=True, the thinking
    config block must be in body of EVERY Bedrock invocation, not just the
    first one. The agent layer always sends; the model decides per turn
    whether to actually use the budget. This was a v4 confusion the user
    flagged in PS_actual_use_problems.md (Issue #4)."""
    from runtime.bedrock_client import BedrockClient

    captured_bodies: list[Dict] = []

    class _FakeBedrockClient:
        def invoke_model(self, modelId: str, body: str, contentType: str = ""):
            captured_bodies.append(json.loads(body))
            # Return a minimal valid Bedrock response shape
            return {
                "body": _FakeBody(
                    json.dumps(
                        {
                            "content": [{"type": "text", "text": "ok"}],
                            "stop_reason": "end_turn",
                            "usage": {"input_tokens": 10, "output_tokens": 5},
                        }
                    ).encode("utf-8")
                ),
            }

    class _FakeBody:
        def __init__(self, data: bytes):
            self._data = data
        def read(self):
            return self._data

    # Inject the fake client at construction time so boto3 is never imported
    # (Codex Phase-01 review finding 1).
    c = BedrockClient(
        model_id="test",
        region="ap-southeast-2",
        mock_mode=False,
        client=_FakeBedrockClient(),
    )

    # Send 3 separate chat() calls with thinking_enabled=True. ALL three must
    # include the `thinking` block in the body.
    for i in range(3):
        c.chat(
            messages=[{"role": "user", "content": f"turn {i}"}],
            system="static system prompt under cache boundary marker",
            thinking_enabled=True,
            thinking_budget=4096,
        )

    assert len(captured_bodies) == 3, f"expected 3 invocations, got {len(captured_bodies)}"
    for i, body in enumerate(captured_bodies):
        assert "thinking" in body, (
            f"Bedrock call #{i} missing 'thinking' config — PS Issue #4 regression. "
            f"Agent must send thinking config on EVERY call when enabled, not just first."
        )
        assert body["thinking"]["type"] == "enabled"
        assert body["thinking"]["budget_tokens"] == 4096
        # When thinking enabled, temperature must be forced to 1
        assert body["temperature"] == 1


def test_thinking_config_NOT_sent_when_disabled():
    """When thinking_enabled=False, the thinking block must NOT appear in body."""
    from runtime.bedrock_client import BedrockClient

    captured_bodies: list[Dict] = []

    class _FakeBedrockClient:
        def invoke_model(self, modelId: str, body: str, contentType: str = ""):
            captured_bodies.append(json.loads(body))
            return {"body": _FakeBody(json.dumps({"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn", "usage": {}}).encode("utf-8"))}

    class _FakeBody:
        def __init__(self, data: bytes):
            self._data = data
        def read(self):
            return self._data

    c = BedrockClient(
        model_id="test",
        region="ap-southeast-2",
        mock_mode=False,
        client=_FakeBedrockClient(),
    )

    c.chat(
        messages=[{"role": "user", "content": "hi"}],
        system="prompt",
        thinking_enabled=False,
        temperature=0.5,
    )

    assert len(captured_bodies) == 1
    assert "thinking" not in captured_bodies[0]
    assert captured_bodies[0]["temperature"] == 0.5  # not forced to 1


# ============================================================
# Cache-boundary placement (validates Phase-1 prep for Phase-6 sectioned prompt)
# ============================================================

def test_cache_boundary_split_marker():
    """If system prompt contains the v4 boundary marker, the cache_control
    block MUST split on it: static cached, dynamic uncached."""
    from runtime.bedrock_client import BedrockClient

    captured: list[Dict] = []

    class _Fake:
        def invoke_model(self, modelId, body, contentType=""):
            captured.append(json.loads(body))
            return {"body": _Body(json.dumps({"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn", "usage": {}}).encode("utf-8"))}

    class _Body:
        def __init__(self, d):
            self._d = d
        def read(self):
            return self._d

    c = BedrockClient(
        model_id="test",
        region="ap-southeast-2",
        mock_mode=False,
        client=_Fake(),
    )

    static_part = "STATIC: I am cached"
    dynamic_part = "DYNAMIC: per-turn skill injection"
    system = static_part + "\n\n# === DYNAMIC ===\n" + dynamic_part

    c.chat(
        messages=[{"role": "user", "content": "x"}],
        system=system,
    )

    assert len(captured) == 1
    sys_field = captured[0]["system"]
    # Should be a list of blocks, with cache_control on the static one
    assert isinstance(sys_field, list)
    assert len(sys_field) == 2
    assert sys_field[0]["text"] == static_part
    assert sys_field[0]["cache_control"]["type"] == "ephemeral"
    assert dynamic_part in sys_field[1]["text"]
    assert "cache_control" not in sys_field[1]


def test_cache_disabled_when_config_off(monkeypatch):
    """If CONFIG.enable_prompt_cache is False, system stays as a plain string."""
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient

    captured: list[Dict] = []

    class _Fake:
        def invoke_model(self, modelId, body, contentType=""):
            captured.append(json.loads(body))
            return {"body": _Body(json.dumps({"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn", "usage": {}}).encode("utf-8"))}

    class _Body:
        def __init__(self, d):
            self._d = d
        def read(self):
            return self._d

    monkeypatch.setattr(CONFIG, "enable_prompt_cache", False)
    c = BedrockClient(
        model_id="test",
        region="ap-southeast-2",
        mock_mode=False,
        client=_Fake(),
    )

    c.chat(
        messages=[{"role": "user", "content": "x"}],
        system="plain prompt",
    )

    assert captured[0]["system"] == "plain prompt"  # plain string, not list


def test_internal_message_fields_not_sent_to_bedrock(monkeypatch):
    """Internal compaction/message metadata must not reach Bedrock payloads."""
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient

    captured: list[Dict] = []

    class _Fake:
        def invoke_model(self, modelId, body, contentType=""):
            captured.append(json.loads(body))
            return {"body": _Body(json.dumps({"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn", "usage": {}}).encode("utf-8"))}

    class _Body:
        def __init__(self, d):
            self._d = d
        def read(self):
            return self._d

    monkeypatch.setattr(CONFIG, "enable_prompt_cache", False)
    c = BedrockClient(
        model_id="test",
        region="ap-southeast-2",
        mock_mode=False,
        client=_Fake(),
    )

    c.chat(
        messages=[
            {
                "role": "user",
                "content": "x",
                "is_meta": False,
                "compact_metadata": {"source": "test"},
                "compact_boundary": True,
            }
        ],
        system="plain prompt",
    )

    sent = captured[0]["messages"][0]
    assert sent == {"role": "user", "content": "x"}


# ============================================================
# Cache-fallback retry path (Codex Phase-01 review finding 2)
# ============================================================

def test_cache_validation_error_strips_cache_and_retries_once():
    """When Bedrock rejects cache_control with a ValidationException, BedrockClient
    must (1) flatten system to a plain string, (2) set prompt_cache_supported=False,
    (3) retry exactly once and succeed. Thinking config must still be sent on the
    retry when thinking_enabled=True."""
    from runtime.bedrock_client import BedrockClient

    captured: list[Dict] = []

    class _ValidationException(Exception):
        pass

    class _FlakyClient:
        def __init__(self):
            self.calls = 0

        def invoke_model(self, modelId, body, contentType=""):
            self.calls += 1
            captured.append(json.loads(body))
            if self.calls == 1:
                # Mimic Bedrock's "cache_control not supported" error shape.
                # ErrorClassifier matches "validationexception" + "cache_control"
                # case-insensitively in the exception's str().
                raise _ValidationException(
                    "ValidationException: cache_control blocks are not supported "
                    "for this model/region (prompt-caching unavailable)"
                )
            return {
                "body": _Body(
                    json.dumps(
                        {
                            "content": [{"type": "text", "text": "ok"}],
                            "stop_reason": "end_turn",
                            "usage": {"input_tokens": 5, "output_tokens": 2},
                        }
                    ).encode("utf-8")
                )
            }

    class _Body:
        def __init__(self, d):
            self._d = d
        def read(self):
            return self._d

    flaky = _FlakyClient()
    c = BedrockClient(
        model_id="test",
        region="ap-southeast-2",
        mock_mode=False,
        client=flaky,
    )
    assert c.prompt_cache_supported is True

    static_part = "STATIC under cache boundary"
    dynamic_part = "DYNAMIC tail"
    system = static_part + "\n\n# === DYNAMIC ===\n" + dynamic_part

    resp = c.chat(
        messages=[{"role": "user", "content": "x"}],
        system=system,
        thinking_enabled=True,
        thinking_budget=4096,
    )

    # Two invocations: the first failed with cache validation, the second
    # succeeded with cache stripped.
    assert flaky.calls == 2, f"expected 2 invocations, got {flaky.calls}"
    assert len(captured) == 2

    # First body: had cache_control blocks (the original cache-on attempt).
    first_sys = captured[0]["system"]
    assert isinstance(first_sys, list)
    assert any(
        isinstance(b, dict) and "cache_control" in b for b in first_sys
    ), "first attempt should have included cache_control blocks"

    # Second body: cache stripped, system flattened to plain string.
    second_sys = captured[1]["system"]
    assert isinstance(second_sys, str), (
        "after cache fallback, system must be a plain string, "
        f"got {type(second_sys).__name__}"
    )
    assert static_part in second_sys
    assert dynamic_part in second_sys

    # Thinking config must still be sent on the retry (PS Issue #4 invariant
    # holds even through cache fallback).
    assert captured[1]["thinking"]["type"] == "enabled"
    assert captured[1]["thinking"]["budget_tokens"] == 4096
    assert captured[1]["temperature"] == 1

    # Client state: future calls should skip cache entirely.
    assert c.prompt_cache_supported is False

    # Response parsed cleanly.
    assert resp.stop_reason == "end_turn"


# ============================================================
# Standalone runner (mirrors v4 test pattern)
# ============================================================

if __name__ == "__main__":
    tests = [
        ("config_singleton_loads",                      test_config_singleton_loads),
        ("config_v4_critical_defaults_preserved",       test_config_v4_critical_defaults_preserved),
        ("strip_jsonc_comments_handles_strings_and_blocks", test_strip_jsonc_comments_handles_strings_and_blocks),
        ("bedrock_client_mock_mode_no_boto",            test_bedrock_client_mock_mode_no_boto),
        ("bedrock_client_mock_response_shape",          test_bedrock_client_mock_response_shape),
        ("bedrock_client_mock_routes_list_files_to_list_dir", test_bedrock_client_mock_routes_list_files_to_list_dir),
        ("thinking_NOT_sent_when_disabled",             test_thinking_config_NOT_sent_when_disabled),
        ("cache_boundary_split_marker",                 test_cache_boundary_split_marker),
        ("cache_validation_error_strips_cache_and_retries_once", test_cache_validation_error_strips_cache_and_retries_once),
    ]

    # The two monkeypatch-using tests need pytest fixtures; run them via pytest if available.
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}:\n  {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1

    # Manually run the monkeypatch ones using a tiny shim
    class _MP:
        def __init__(self):
            self._undo = []
        def setattr(self, target, name, value):
            old = getattr(target, name)
            self._undo.append((target, name, old))
            setattr(target, name, value)
        def cleanup(self):
            for t, n, o in self._undo:
                setattr(t, n, o)

    for name, fn in [
        ("thinking_config_sent_on_every_call_when_enabled", test_thinking_config_sent_on_every_call_when_enabled),
        ("cache_disabled_when_config_off",                  test_cache_disabled_when_config_off),
    ]:
        mp = _MP()
        try:
            fn(mp)
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}:\n  {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
        finally:
            mp.cleanup()

    total = len(tests) + 2
    print(f"\n{total - failed}/{total} Phase 01 tests passed")
    sys.exit(1 if failed else 0)
