"""Block B — TokenTracker + AuditLogger + SnapshotManager + tokenEstimation.

8 lock tests per TEST_DESIGN.md §Block B + 2 ADR-020 remap lock tests
(0-3 BEDROCK_EXTRA_PARAMS_HEADERS, 0-8 validate_bounded_int_env_var).

  T1 test_token_tracker_singleton                  TOKENS singleton; update() accumulates
  T1 test_audit_logger_writes_jsonl                every entry → valid JSONL line
  T1 test_snapshot_manager_creates_backup          edit_file creates .snapshots/<file>_<ts>.bak
  T1 test_token_tracker_per_agent_breakdown        parent_input + subagent_input["build"] independent
  T2 test_count_tokens_with_bedrock_mocked         mocked count_tokens parsed correctly
  T1 test_token_accounting_input_cumulative        input KEEPS-LATEST? — actually session SUMS;
                                                    test the documented v5 contract
  T1 test_haiku_excluded_from_cache_break          Haiku-4.5 in EXCLUDED_MODELS_FOR_CACHE_BREAK (R4 #14)
  T5 test_count_tokens_real_bedrock_haiku          real Bedrock count (gated; skip without env)

  + test_extra_params_in_body_not_headers          ADR-020 remap 0-3 lock
  + test_env_validation_clamps_and_rejects_bad_input  ADR-020 remap 0-8 lock
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


@pytest.fixture(autouse=True)
def fresh_tokens(monkeypatch):
    """Reset TOKENS between tests so no leakage across the suite."""
    from runtime.tokens import TOKENS
    TOKENS.reset()
    yield
    TOKENS.reset()


# ============================================================
# T1 — TokenTracker singleton + update accumulates
# ============================================================

def test_token_tracker_singleton():
    from runtime.tokens import TOKENS, TokenTracker
    assert isinstance(TOKENS, TokenTracker)

    TOKENS.add({"input_tokens": 100, "output_tokens": 50}, model_id="test-model")
    TOKENS.add({"input_tokens": 200, "output_tokens": 75}, model_id="test-model")

    assert TOKENS.session_input == 300
    assert TOKENS.session_output == 125
    assert TOKENS.session_total == 425
    assert TOKENS.api_calls == 2
    # Last-call values reflect the most recent add().
    assert TOKENS.last_input == 200
    assert TOKENS.last_output == 75


# ============================================================
# T1 — AuditLogger writes JSONL
# ============================================================

def test_audit_logger_writes_jsonl(tmp_path):
    from runtime.audit import AuditLogger

    audit = AuditLogger(audit_dir=str(tmp_path))
    audit.log(
        session_id="abc123",
        action="tool_dispatch",
        tool_name="read_file",
        parameters={"file_path": "/etc/passwd"},
        result_summary="ok",
        user_approved=True,
    )

    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert "abc123" in files[0].name
    assert files[0].suffix == ".jsonl"

    with open(files[0], "r", encoding="utf-8") as f:
        line = f.readline()
    entry = json.loads(line)
    assert entry["session_id"] == "abc123"
    assert entry["action"] == "tool_dispatch"
    assert entry["tool_name"] == "read_file"
    assert entry["parameters"]["file_path"] == "/etc/passwd"
    assert entry["result_summary"] == "ok"
    assert entry["user_approved"] is True
    # Tamper-detection hash present.
    assert entry["hash"] and len(entry["hash"]) == 32


def test_audit_logger_redacts_sensitive_params(tmp_path):
    from runtime.audit import AuditLogger

    audit = AuditLogger(audit_dir=str(tmp_path))
    audit.log(
        session_id="s",
        action="tool_dispatch",
        tool_name="bash",
        parameters={"command": "echo hi", "api_key": "sk-secret"},
    )

    files = list(tmp_path.iterdir())
    with open(files[0], "r", encoding="utf-8") as f:
        entry = json.loads(f.readline())
    assert entry["parameters"]["command"] == "echo hi"
    assert entry["parameters"]["api_key"] == "[REDACTED]"


# ============================================================
# T1 — SnapshotManager creates a backup
# ============================================================

def test_snapshot_manager_creates_backup(tmp_path):
    from runtime.snapshot import SnapshotManager

    target = tmp_path / "data.txt"
    target.write_text("original", encoding="utf-8")

    sm = SnapshotManager(workspace=str(tmp_path))
    snap_path = sm.save(str(target))

    assert snap_path is not None
    assert os.path.isfile(snap_path)
    with open(snap_path, "r", encoding="utf-8") as f:
        assert f.read() == "original"

    # Now mutate + revert.
    target.write_text("changed", encoding="utf-8")
    ok, msg = sm.revert(str(target))
    assert ok, msg
    assert target.read_text(encoding="utf-8") == "original"


# ============================================================
# T1 — Per-agent attribution (parent vs sub-agent buckets)
# ============================================================

def test_token_tracker_per_agent_breakdown():
    from runtime.tokens import TOKENS

    TOKENS.add({"input_tokens": 100, "output_tokens": 50}, model_id="test-model", agent_kind="parent")
    TOKENS.add({"input_tokens": 80, "output_tokens": 40}, model_id="test-model", agent_kind="build")
    TOKENS.add({"input_tokens": 60, "output_tokens": 30}, model_id="test-model", agent_kind="explore")
    TOKENS.add({"input_tokens": 50, "output_tokens": 25}, model_id="test-model", agent_kind="parent")

    assert TOKENS.parent_input_tokens == 150
    assert TOKENS.parent_output_tokens == 75
    assert TOKENS.subagent_input_tokens["build"] == 80
    assert TOKENS.subagent_output_tokens["build"] == 40
    assert TOKENS.subagent_input_tokens["explore"] == 60
    assert TOKENS.subagent_output_tokens["explore"] == 30

    # Roll-up still matches.
    assert TOKENS.session_input == 290
    assert TOKENS.session_output == 145
    # Parent + sum of sub-agent costs == session total.
    parent_cost = TOKENS.parent_cost
    sub_cost_total = sum(TOKENS.subagent_cost.values())
    assert abs(TOKENS.session_cost - (parent_cost + sub_cost_total)) < 1e-6


# ============================================================
# T2 — count_tokens with mocked Bedrock
# ============================================================

def test_count_tokens_with_bedrock_mocked():
    """Mock-mode count_tokens returns a positive int derived from rough est."""
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    n = client.count_tokens(
        messages=[{"role": "user", "content": "hello world"}],
        system="you are helpful",
    )
    assert isinstance(n, int)
    assert n > 0


# ============================================================
# T1 — Token accounting: documented v5 contract
# ============================================================

def test_token_accounting_session_sums_input_and_output():
    """v5 TokenTracker SUMS input across calls (parity with v4).

    The Plan v3 §Block B B-11 row notes Runnable's
    `LocalAgentTask.tsx:50-95` adopts a different semantics where
    parent input is KEEPS-LATEST per turn (because input is cumulative
    in Anthropic-API-direct usage payloads). v5 currently tracks the
    Bedrock `input_tokens` per call and sums them — Bedrock returns a
    PER-CALL count, not a cumulative one. This lock test pins the v5
    Bedrock semantics so future Anthropic-direct adopters can't silently
    flip it.
    """
    from runtime.tokens import TOKENS

    TOKENS.add({"input_tokens": 100, "output_tokens": 30}, model_id="test-model")
    TOKENS.add({"input_tokens": 120, "output_tokens": 35}, model_id="test-model")
    TOKENS.add({"input_tokens": 140, "output_tokens": 40}, model_id="test-model")

    # Bedrock semantics: each call's input_tokens is a per-call measure.
    assert TOKENS.session_input == 360
    assert TOKENS.session_output == 105
    # last_input always reflects the most recent call.
    assert TOKENS.last_input == 140
    assert TOKENS.last_output == 40


# ============================================================
# T1 — R4 #14 MUST: Haiku excluded from cache-break detection
# ============================================================

def test_haiku_excluded_from_cache_break():
    """Haiku-4.5 has non-deterministic cache-hash behavior on Bedrock that
    the prompt-cache-break detector misreads as a "section flipped". The
    EXCLUDED_MODELS_FOR_CACHE_BREAK Set must contain Haiku-4.5 so detection
    skips that case. Per Wave-5-DEEP R4 #14 (MUST)."""
    from runtime.tokens import EXCLUDED_MODELS_FOR_CACHE_BREAK

    assert "anthropic.claude-haiku-4-5-20251001-v1:0" in EXCLUDED_MODELS_FOR_CACHE_BREAK


# ============================================================
# T5 — real Bedrock count (gated; skip without env)
# ============================================================

def test_count_tokens_real_bedrock_haiku():
    """Real Bedrock count_tokens call against Haiku-4.5. Skipped unless
    the user opts in via RUN_REAL_BEDROCK=1.

    This test costs ~$0.005 worth of Bedrock CountTokens API calls when
    enabled. Per BUILDER_PROMPT.md §Step 7 "T5 real-Bedrock smoke" gate
    — Block B is in the high-risk list."""
    if not os.getenv("RUN_REAL_BEDROCK"):
        pytest.skip("RUN_REAL_BEDROCK not set; skipping real-Bedrock smoke.")

    from runtime.bedrock_client import BedrockClient

    region = os.getenv("AWS_REGION", "ap-southeast-2")
    client = BedrockClient(
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        region=region,
        mock_mode=False,
    )
    n = client.count_tokens(
        messages=[{"role": "user", "content": "Hello, Bedrock."}],
        system="You are a helpful assistant.",
    )
    assert isinstance(n, int) and n > 0


# ============================================================
# ADR-020 remap 0-3 — BEDROCK_EXTRA_PARAMS_HEADERS in body, not headers
# ============================================================

def test_extra_params_in_body_not_headers():
    """`BEDROCK_EXTRA_PARAMS_HEADERS` documents which Anthropic-direct
    beta names belong in additionalModelRequestFields (Bedrock's body
    field), NOT in HTTP headers. Bedrock silently drops `anthropic-beta`
    style headers, so getting this wrong = silent feature loss.

    Per Block 0 item 0-3 (R8 #74 MUST) remapped to Block B in ADR-020.
    """
    from runtime.bedrock_client import BEDROCK_EXTRA_PARAMS_HEADERS

    assert isinstance(BEDROCK_EXTRA_PARAMS_HEADERS, frozenset)
    # The 2 known beta names that ride the body, not headers, on Bedrock.
    assert "interleaved-thinking-2025-05-14" in BEDROCK_EXTRA_PARAMS_HEADERS
    assert "context-1m-2025-08-07" in BEDROCK_EXTRA_PARAMS_HEADERS


# ============================================================
# ADR-020 remap 0-8 — validate_bounded_int_env_var
# ============================================================

def test_env_validation_clamps_and_rejects_bad_input(caplog):
    """`validate_bounded_int_env_var` clamps out-of-range values, returns
    default for non-integer / unset values, and logs a WARNING in both
    bad cases so operators can spot drift.

    Per Block 0 item 0-8 remapped to Block B in ADR-020.
    """
    from runtime.env_validation import validate_bounded_int_env_var

    # Unset → default
    val = validate_bounded_int_env_var(
        "NEVER_SET_VAR_X", minimum=0, maximum=100, default=42, env={},
    )
    assert val == 42

    # Below minimum → clamped to minimum + WARNING
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        val = validate_bounded_int_env_var(
            "X", minimum=10, maximum=100, default=42, env={"X": "5"},
        )
    assert val == 10
    assert any("below minimum" in r.getMessage() for r in caplog.records)

    # Above maximum → clamped to maximum + WARNING
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        val = validate_bounded_int_env_var(
            "X", minimum=10, maximum=100, default=42, env={"X": "999"},
        )
    assert val == 100
    assert any("above maximum" in r.getMessage() for r in caplog.records)

    # Non-integer → default + WARNING
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        val = validate_bounded_int_env_var(
            "X", minimum=10, maximum=100, default=42, env={"X": "not-a-number"},
        )
    assert val == 42
    assert any("not an integer" in r.getMessage() for r in caplog.records)


# ============================================================
# Bonus — ToolResult dataclass shape (B-13 V1 gap #1 MUST)
# ============================================================

def test_tool_result_dataclass_shape():
    from runtime.tokens import ToolResult

    r = ToolResult(
        output="hello",
        tool_name="read_file",
        truncated=True,
        total_size=10_000,
        shown_size=5_000,
    )
    assert r.output == "hello"
    assert r.truncated is True
    assert r.total_size == 10_000
    assert r.shown_size == 5_000
    assert r.error is False
    assert r.error_message == ""


# ============================================================
# Bonus — Runnable tokenEstimation helpers (B-3, B-4, B-6, B-7, B-9)
# ============================================================

def test_bytes_per_token_for_file_type():
    from runtime.tokens import bytes_per_token_for_file_type

    assert bytes_per_token_for_file_type("data.json") == 2.0
    assert bytes_per_token_for_file_type("data.csv") == 3.0
    assert bytes_per_token_for_file_type("notes.md") == 4.0
    assert bytes_per_token_for_file_type("unknown.xyz") == 4.0
    assert bytes_per_token_for_file_type("") == 4.0


def test_estimate_message_tokens_4_3_padding():
    from runtime.tokens import estimate_message_tokens

    assert estimate_message_tokens("") == 0
    # len=12 → 12/3=4 → 4*4/3=5.33 → ceil round to 5
    assert estimate_message_tokens("hello world!") == 5


def test_has_thinking_blocks():
    from runtime.tokens import has_thinking_blocks

    assert not has_thinking_blocks({"role": "assistant", "content": "plain text"})
    assert not has_thinking_blocks({"role": "assistant", "content": [{"type": "text", "text": "x"}]})
    assert has_thinking_blocks({
        "role": "assistant",
        "content": [{"type": "thinking", "thinking": "..."}],
    })
    assert has_thinking_blocks({
        "role": "assistant",
        "content": [{"type": "redacted_thinking", "data": "..."}],
    })


def test_rough_token_count_image_capped():
    from runtime.tokens import IMAGE_MAX_TOKEN_SIZE, rough_token_count_for_block

    assert rough_token_count_for_block({"type": "image"}) == IMAGE_MAX_TOKEN_SIZE
    assert rough_token_count_for_block({"type": "input_image"}) == IMAGE_MAX_TOKEN_SIZE


def test_final_context_tokens_from_last_response():
    from runtime.tokens import TOKENS

    # Cold start fallback.
    assert TOKENS.final_context_tokens_from_last_response() == 0
    TOKENS.add({
        "input_tokens": 1000,
        "output_tokens": 100,
        "cache_read_input_tokens": 500,
        "cache_creation_input_tokens": 200,
    }, model_id="test-model")
    # context = input + cache_read + cache_write
    assert TOKENS.final_context_tokens_from_last_response() == 1700


# ============================================================
# Wiring lock — TOKENS.add fires on QueryEngine response (mock client)
# ============================================================

def test_query_engine_wires_tokens_add():
    """Every Bedrock response in the engine loop must update TOKENS so the
    user can see /cost reflect work done. Wired in core/query_engine.py
    Block B section."""
    from runtime.tokens import TOKENS
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    TOKENS.reset()
    a.run("hi")
    # Mock Bedrock's reply has a non-zero usage (see bedrock_client mock).
    assert TOKENS.api_calls >= 1
    assert TOKENS.session_input + TOKENS.session_output > 0
    # Parent attribution since it's the main agent loop.
    assert TOKENS.parent_input_tokens > 0 or TOKENS.parent_output_tokens > 0


# ============================================================
# Codex iter-1 finding-lock tests (regression prevention)
# ============================================================

def test_canonicalize_model_id_strips_au_prefix():
    """Codex Block-B iter-1 finding #1 (HIGH) lock: `au.` is the v5
    default-config prefix; without stripping, default-path TOKENS.add
    would record $0. Per ADR-021 + canonicalize_model_id docstring."""
    from runtime.tokens import canonicalize_model_id

    assert canonicalize_model_id(
        "au.anthropic.claude-sonnet-4-5-20250929-v1:0"
    ) == "anthropic.claude-sonnet-4-5-20250929-v1:0"
    assert canonicalize_model_id(
        "apac.anthropic.claude-haiku-4-5-20251001-v1:0"
    ) == "anthropic.claude-haiku-4-5-20251001-v1:0"
    assert canonicalize_model_id(
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    ) == "anthropic.claude-sonnet-4-5-20250929-v1:0"
    assert canonicalize_model_id(
        "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
    ) == "anthropic.claude-haiku-4-5-20251001-v1:0"
    # Bare canonical form passes through unchanged.
    assert canonicalize_model_id(
        "anthropic.claude-haiku-4-5-20251001-v1:0"
    ) == "anthropic.claude-haiku-4-5-20251001-v1:0"


def test_au_prefixed_model_records_real_cost():
    """Lock test for Codex iter-1 finding #1 (HIGH): TOKENS.add against
    `au.`-prefixed model id must record a non-zero cost (was $0 before fix).

    R-tier R1 PHASE A iter-3 follow-up: au. carries +10% geo-inference
    premium (per AWS Bedrock model card + Anthropic pricing). v5 applies
    `get_geo_multiplier(raw_mid) = 1.10` so the recorded cost is now
    1.10x the global base rate. See test_geo_inference_premium.py for
    the dedicated lock tests on the multiplier itself.
    """
    from runtime.tokens import TOKENS

    TOKENS.reset()
    TOKENS.add(
        {"input_tokens": 1000, "output_tokens": 500},
        model_id="au.anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
    # Sonnet 4.5 = $0.003/1k input, $0.015/1k output (global base rates).
    # Geo multiplier (au.) = 1.10.
    # Expected: (1000/1000 * 0.003 + 500/1000 * 0.015) * 1.10
    #         = (0.003 + 0.0075) * 1.10
    #         = 0.0105 * 1.10 = 0.01155
    assert TOKENS.session_cost > 0
    assert abs(TOKENS.session_cost - 0.01155) < 1e-6


def test_audit_log_on_unknown_tool_dispatch(tmp_path, monkeypatch):
    """Codex iter-1 finding #2 (HIGH) lock: every dispatch path is audited.
    The unknown-tool branch must call AUDIT.log with action='tool_unknown'.
    Without this, forensics misses what the model attempted to call."""
    from runtime.audit import AuditLogger
    import runtime.audit as audit_mod

    # Pin AUDIT to a tmp directory so the lock test is hermetic.
    test_audit = AuditLogger(audit_dir=str(tmp_path))
    monkeypatch.setattr(audit_mod, "AUDIT", test_audit)

    # Dispatch an unknown tool via QueryEngine.
    from runtime.bedrock_client import BedrockClient, ToolCall, Response
    from core.query_engine import QueryEngine

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)

    # Build a fake Response with a tool_call to a non-existent tool.
    fake_response = Response(
        text="",
        tool_calls=[ToolCall(id="t1", name="this_tool_does_not_exist", input={})],
        stop_reason="tool_use",
    )
    final_response = Response(text="done", tool_calls=[], stop_reason="end_turn")

    call_count = {"n": 0}
    def fake_chat(*args, **kwargs):
        call_count["n"] += 1
        return fake_response if call_count["n"] == 1 else final_response

    monkeypatch.setattr(client, "chat", fake_chat)

    engine = QueryEngine(client=client, max_turns=3)
    engine.run(user_message="trigger unknown tool", system_prompt="test", tools=[])

    # Audit log should contain a tool_unknown entry.
    files = list(tmp_path.iterdir())
    assert files, "AUDIT.log did not write any file for unknown-tool dispatch"
    actions = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    actions.append(json.loads(line)["action"])
    assert "tool_unknown" in actions, (
        f"unknown-tool path must call AUDIT.log; saw actions={actions}"
    )


def test_audit_log_on_plan_mode_block(tmp_path, monkeypatch):
    """Codex iter-1 finding #2 (HIGH) lock: plan-mode blocked dispatch is a
    security event and must be audited. action='plan_mode_blocked'."""
    from runtime.audit import AuditLogger
    import runtime.audit as audit_mod

    test_audit = AuditLogger(audit_dir=str(tmp_path))
    monkeypatch.setattr(audit_mod, "AUDIT", test_audit)

    from runtime.bedrock_client import BedrockClient, ToolCall, Response
    from core.query_engine import QueryEngine
    from tools.registry import build_tool, register, _reset_registry_for_tests
    from tools import bootstrap_built_ins

    _reset_registry_for_tests()
    bootstrap_built_ins()
    # Add a non-allowlisted mutating tool to dispatch in plan mode.
    register(build_tool(
        name="mutator_test",
        description="Use when the test needs a mutating tool not in PLAN_MODE_ALLOWED_TOOLS.",
        input_schema={"type": "object", "properties": {}},
        execute=lambda args, context=None: "should not run",
    ))

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)

    fake_response = Response(
        text="",
        tool_calls=[ToolCall(id="m1", name="mutator_test", input={})],
        stop_reason="tool_use",
    )
    final_response = Response(text="done", tool_calls=[], stop_reason="end_turn")
    call_count = {"n": 0}
    def fake_chat(*args, **kwargs):
        call_count["n"] += 1
        return fake_response if call_count["n"] == 1 else final_response

    monkeypatch.setattr(client, "chat", fake_chat)

    from tools.registry import all_registered
    engine = QueryEngine(client=client, max_turns=3)
    engine.run(
        user_message="trigger plan-mode block",
        system_prompt="test",
        tools=all_registered(),
        plan_mode=True,
    )

    files = list(tmp_path.iterdir())
    assert files, "AUDIT.log did not write any file for plan-mode block"
    actions = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    actions.append(json.loads(line)["action"])
    assert "plan_mode_blocked" in actions, (
        f"plan-mode block path must call AUDIT.log; saw actions={actions}"
    )


def test_count_tokens_includes_thinking_when_messages_have_thinking():
    """Codex iter-1 finding #3 (MEDIUM) lock: count_tokens body switches to
    max_tokens=2048 + thinking config when any message contains a
    thinking block. Per Runnable services/tokenEstimation.ts:437-495."""
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=False)
    captured: Dict[str, Any] = {}

    class _FakeBedrock:
        def count_tokens(self, **kwargs):
            captured.update(kwargs)
            return {"inputTokens": 42}

    client.client = _FakeBedrock()

    msg_with_thinking = {
        "role": "assistant",
        "content": [{"type": "thinking", "thinking": "..."}],
    }
    n = client.count_tokens(messages=[msg_with_thinking], system="x")
    assert n == 42

    body = json.loads(captured["input"]["invokeModel"]["body"].decode("utf-8"))
    assert body["max_tokens"] == 2048, (
        f"thinking-message count_tokens must use max_tokens=2048; got {body['max_tokens']}"
    )
    assert body.get("thinking", {}).get("type") == "enabled"


def test_count_tokens_omits_thinking_when_messages_plain():
    """Lock: plain messages don't trigger the thinking-config switch."""
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=False)
    captured: Dict[str, Any] = {}

    class _FakeBedrock:
        def count_tokens(self, **kwargs):
            captured.update(kwargs)
            return {"inputTokens": 10}

    client.client = _FakeBedrock()
    client.count_tokens(messages=[{"role": "user", "content": "hi"}])

    body = json.loads(captured["input"]["invokeModel"]["body"].decode("utf-8"))
    assert body["max_tokens"] == 1
    assert "thinking" not in body


def test_extra_params_includes_tool_search_beta():
    """Codex iter-1 finding #4 (MEDIUM) lock: 3rd Runnable beta name
    `tool-search-tool-2025-10-19` belongs in body, not headers."""
    from runtime.bedrock_client import BEDROCK_EXTRA_PARAMS_HEADERS
    assert "tool-search-tool-2025-10-19" in BEDROCK_EXTRA_PARAMS_HEADERS
    # Sanity: still a frozenset, still has all 3 entries.
    assert len(BEDROCK_EXTRA_PARAMS_HEADERS) >= 3


def test_env_validation_wired_into_config(monkeypatch):
    """Codex iter-1 finding #5 (MEDIUM) lock: validate_bounded_int_env_var
    is actually USED by runtime/config.py at module load. We exercise the
    contract by importing config fresh with an env override and asserting
    CONFIG.max_turns reflects the validated value."""
    import importlib
    import runtime.config as config_mod

    monkeypatch.setenv("SAGEMAKER_AGENT_MAX_TURNS", "42")
    # Force re-import so the bottom-of-file wiring runs against the env.
    importlib.reload(config_mod)
    try:
        assert config_mod.CONFIG.max_turns == 42, (
            f"env-validated max_turns must be 42; got {config_mod.CONFIG.max_turns}"
        )
    finally:
        # Restore by reloading without the override so other tests aren't
        # affected (monkeypatch will undo the env var on teardown anyway).
        monkeypatch.delenv("SAGEMAKER_AGENT_MAX_TURNS", raising=False)
        importlib.reload(config_mod)


def test_env_validation_clamps_out_of_range(monkeypatch, caplog):
    """Lock: out-of-range env value is clamped + logs WARNING."""
    import importlib
    import runtime.config as config_mod

    monkeypatch.setenv("SAGEMAKER_AGENT_MAX_TURNS", "999999")  # above max
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        importlib.reload(config_mod)
    try:
        assert config_mod.CONFIG.max_turns == 10_000, (
            f"out-of-range max_turns must clamp to maximum 10_000; got "
            f"{config_mod.CONFIG.max_turns}"
        )
        assert any("above maximum" in r.getMessage() for r in caplog.records), (
            "out-of-range env override must log WARNING"
        )
    finally:
        monkeypatch.delenv("SAGEMAKER_AGENT_MAX_TURNS", raising=False)
        importlib.reload(config_mod)


def test_snapshot_save_path_under_lock_no_collision(tmp_path):
    """Codex iter-1 finding #6 (LOW) lock: ts + uuid suffix means concurrent
    same-ms saves of the same file produce distinct snap_paths and distinct
    log entries. Without the fix, two saves in the same millisecond would
    collide on snap_path. We simulate two saves and verify uniqueness."""
    from runtime.snapshot import SnapshotManager

    target = tmp_path / "data.txt"
    target.write_text("v1", encoding="utf-8")

    sm = SnapshotManager(workspace=str(tmp_path))
    snaps = [sm.save(str(target)) for _ in range(5)]
    assert all(s is not None for s in snaps)
    # All 5 snap_paths must be distinct (uuid suffix prevents same-ms
    # collision).
    assert len(set(snaps)) == 5
    # Log has 5 entries pointing at 5 distinct snapshot files.
    assert len(sm.list_snapshots(str(target))) == 5
