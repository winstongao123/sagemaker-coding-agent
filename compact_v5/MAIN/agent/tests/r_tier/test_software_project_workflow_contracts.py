"""Zero-cost contracts for long software-project use.

These tests make the v5.0.1 product target executable before AWS spend:
v5 must be evaluated as a long-running software-writing agent, not only a
snippet generator. They do not call Bedrock; they verify that the R-tier plan
and local command surface include the status/save/resume/checkpoint/verify
discipline needed for autonomous coding work.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest


_THIS = Path(__file__).resolve()
_AGENT_ROOT = _THIS.parents[2]
_REPO_ROOT = _THIS.parents[5]
_MATRIX_PATH = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_test_matrix.json"
_WORKFLOW_DOC = (
    _REPO_ROOT
    / "compact_v5"
    / "_status"
    / "v5_completion_audit"
    / "PS_SOFTWARE_PROJECT_WORKFLOW.md"
)
_OPTIMIZED_AWS_PLAN = (
    _REPO_ROOT
    / "compact_v5"
    / "_status"
    / "v5_completion_audit"
    / "OPTIMIZED_AWS_VALIDATION_PLAN.md"
)
_REVISIT_PLAN = (
    _REPO_ROOT
    / "compact_v5"
    / "_status"
    / "v5_completion_audit"
    / "SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md"
)
_AWS_TEST_LOOP = (
    _REPO_ROOT
    / "compact_v5"
    / "_status"
    / "v5_completion_audit"
    / "PS_AWS_TEST_EXECUTION_LOOP.md"
)
_EVIDENCE_CONTRACT = _REPO_ROOT / "compact_v5" / "_status" / "R_TIER_EVIDENCE_CONTRACT.md"

if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


def _load_readiness_specs():
    spec_path = _THIS.parent / "test_r6_to_r19_readiness_specs.py"
    module_spec = importlib.util.spec_from_file_location(
        "_r_tier_readiness_specs",
        spec_path,
    )
    assert module_spec is not None
    module = importlib.util.module_from_spec(module_spec)
    assert module_spec.loader is not None
    module_spec.loader.exec_module(module)
    return module.SCENARIO_SPECS


SOFTWARE_PROJECT_CONTRACTS = {
    "R13": {
        "purpose": "coding accuracy",
        "must_include": ["tests", "score", "unrelated", "4/5"],
        "telemetry": ["outcome", "tool_call_summary", "quality_review"],
        "commands": ["/verify", "/done"],
    },
    "R14": {
        "purpose": "multi-file refactor",
        "must_include": ["pytest", "grep", "stale"],
        "telemetry": ["tool_call_summary", "REPEATED_calls", "quality_review"],
        "commands": ["/checkpoint", "/verify", "/done"],
    },
    "R15": {
        "purpose": "debugging",
        "must_include": ["bugs", "false-positive", "diagnosis"],
        "telemetry": ["outcome", "tool_call_summary", "quality_review"],
        "commands": ["/checkpoint", "/verify", "/done"],
    },
    "R16": {
        "purpose": "long app build",
        "must_include": ["app tests", "compaction", "cache", "software_builder_subchecks"],
        "telemetry": [
            "compaction_events",
            "cache_efficiency_trend",
            "tool_call_summary",
            "quality_review",
            "software_builder_subchecks",
        ],
        "commands": [
            "/status",
            "/phase",
            "/save",
            "/resume",
            "/checkpoint",
            "/verify",
            "/done",
            "/cost",
            "/context",
        ],
    },
    "R19-U1": {
        "purpose": "ambiguity handling",
        "must_include": ["clarification", "no speculative edit"],
        "telemetry": ["outcome", "tool_call_summary", "quality_review"],
        "commands": ["/status"],
    },
    "R19-U2": {
        "purpose": "contradiction handling",
        "must_include": ["conflict", "clarification"],
        "telemetry": ["outcome", "quality_review"],
        "commands": ["/status"],
    },
    "R19-U3": {
        "purpose": "hidden dependency refactor",
        "must_include": ["search", "edit", "tests"],
        "telemetry": ["tool_call_summary", "REPEATED_calls", "quality_review"],
        "commands": ["/checkpoint", "/verify"],
    },
    "R19-U6": {
        "purpose": "bad tool output recovery",
        "must_include": ["bad output", "retry", "alternative"],
        "telemetry": ["tool_call_summary", "outcome", "quality_review"],
        "commands": ["/status"],
    },
    "R19-U7": {
        "purpose": "repeated-call recovery",
        "must_include": ["third repeated call", "alternative"],
        "telemetry": ["tool_call_summary", "REPEATED_calls", "quality_review"],
        "commands": ["/context", "/status"],
    },
    "R19-U10": {
        "purpose": "long coherence",
        "must_include": ["final task", "compactions", "coherence"],
        "telemetry": [
            "compaction_events",
            "cache_efficiency_trend",
            "tool_call_summary",
            "quality_review",
        ],
        "commands": [
            "/status",
            "/phase",
            "/save",
            "/resume",
            "/checkpoint",
            "/verify",
            "/done",
            "/cost",
            "/context",
        ],
    },
}


def test_software_project_scenarios_have_hardening_contracts():
    """R13-R16/R19 must test real software-project behavior, not markers."""
    matrix = {row["id"]: row for row in json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))}
    specs = _load_readiness_specs()

    for scenario_id, contract in SOFTWARE_PROJECT_CONTRACTS.items():
        assert scenario_id in matrix
        assert scenario_id in specs
        spec = specs[scenario_id]

        acceptance_text = " ".join(spec["acceptance"]).lower()
        for phrase in contract["must_include"]:
            assert phrase.lower() in acceptance_text, (
                f"{scenario_id} acceptance must mention {phrase!r}"
            )

        assert matrix[scenario_id]["kind"] == "real"
        assert spec["mode"] == "real_aws_gated"
        assert float(matrix[scenario_id]["cost_cap_usd"]) == pytest.approx(
            float(spec["cost_cap_usd"])
        )
        assert contract["telemetry"], f"{scenario_id} needs telemetry contract"
        assert contract["commands"], f"{scenario_id} needs command workflow contract"


def test_existing_commands_are_the_project_workflow_surface():
    """Use existing commands; do not add an overlapping /project-* family."""
    from commands import list_commands

    commands = set(list_commands(include_aliases=True))
    required = {
        "/status",
        "/phase",
        "/save",
        "/resume",
        "/checkpoint",
        "/verify",
        "/done",
        "/cost",
        "/context",
        "/dream",
    }

    assert required <= commands
    assert not [cmd for cmd in commands if cmd.startswith("/project")]


def test_save_resume_status_phase_preserve_long_task_state(tmp_path, monkeypatch):
    """Local contract for compaction/resume-style task continuity.

    This is the zero-cost version of the R16/R19-U10 requirement: a long task
    must have status, phase, messages, and token/cost state available after
    save/resume.
    """
    from commands import dispatch_command
    from runtime.config import CONFIG
    from runtime.session import SessionManager
    import runtime.session as session_mod
    from runtime.tokens import TOKENS

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    monkeypatch.setattr(
        session_mod,
        "SESSIONS",
        SessionManager(sessions_dir=str(tmp_path / "sessions")),
    )

    TOKENS.reset()
    status = dispatch_command("/status init")
    assert status.consumed
    assert (tmp_path / "AGENT_STATUS.md").is_file()

    phase = dispatch_command("/phase build payment API")
    assert phase.side_effect == "phase:build payment API"

    TOKENS.add({
        "input_tokens": 1200,
        "output_tokens": 300,
        "cache_read_input_tokens": 100,
        "cache_creation_input_tokens": 50,
    })
    ctx = {
        "messages": [
            {"role": "user", "content": "build payment API"},
            {"role": "assistant", "content": "next: implement tests"},
        ]
    }

    saved = dispatch_command("/save payment-api-session", ctx=ctx)
    assert saved.side_effect.startswith("session_saved:")
    session_id = saved.side_effect.split(":", 1)[1]

    ctx["messages"] = []
    TOKENS.reset()
    resumed = dispatch_command(f"/resume {session_id}", ctx=ctx)

    assert resumed.side_effect == f"session_resumed:{session_id}"
    assert ctx["messages"][0]["content"] == "build payment API"
    assert ctx["messages"][1]["content"] == "next: implement tests"
    assert TOKENS.api_calls == 1
    assert TOKENS.session_input == 1200
    assert TOKENS.session_output == 300
    assert TOKENS.session_cache_read == 100
    assert TOKENS.session_cache_write == 50


def test_reviewer_subagent_token_cost_attribution_is_visible(monkeypatch):
    """Reviewer/subagent usage must be visible before AWS evidence is trusted."""
    from runtime.config import CONFIG
    from runtime.tokens import TokenTracker

    tracker = TokenTracker(config=CONFIG)
    tracker.add(
        {
            "input_tokens": 1000,
            "output_tokens": 200,
            "cache_read_input_tokens": 100,
            "cache_creation_input_tokens": 50,
        },
        model_id=CONFIG.model_id,
        agent_kind="parent",
    )
    tracker.add(
        {
            "input_tokens": 500,
            "output_tokens": 120,
            "cache_read_input_tokens": 40,
            "cache_creation_input_tokens": 20,
        },
        model_id=CONFIG.model_id,
        agent_kind="review",
    )

    stats = tracker.get_stats()
    assert stats["subagent_input_tokens"]["review"] == 500
    assert stats["subagent_output_tokens"]["review"] == 120
    assert stats["subagent_cache_read_tokens"]["review"] == 40
    assert stats["subagent_cache_write_tokens"]["review"] == 20
    assert stats["subagent_cost_usd"]["review"] > 0

    cost_block = tracker.get_cost_block()
    assert "parent=$" in cost_block
    assert "review=$" in cost_block
    assert "review=$" in cost_block and "cache=40/20" in cost_block
    assert "Cache: read=140 write=70 total=210" in cost_block

    otel = tracker.get_otel_counters()
    assert otel["agents.subagent.cost_usd"]["review"] > 0
    assert otel["agents.subagent.cache_read"]["review"] == 40
    assert otel["agents.subagent.cache_write"]["review"] == 20
    assert otel["tokens.cache_read"] == 140
    assert otel["tokens.cache_write"] == 70


def test_software_project_workflow_doc_is_persistent_and_command_consolidated():
    text = _WORKFLOW_DOC.read_text(encoding="utf-8")

    for token in [
        "long-running software-writing work",
        "Do not add a parallel `/project-*` command family",
        "auto-compaction",
        "AGENT_STATUS",
        "R13",
        "R16",
        "R19-U10",
        "Reviewer/subagent token and cost attribution",
    ]:
        assert token in text


def test_optimized_aws_validation_plan_supports_98_percent_confidence_gate():
    """AWS spend should be bundled, reviewed, and evidence-driven."""
    text = _OPTIMIZED_AWS_PLAN.read_text(encoding="utf-8")

    for token in [
        "98% confidence",
        "Phase A Claude approval",
        "Final independent review",
        "tool_call_summary",
        "token counts",
        "cache read/write counts",
        "parent/subagent/reviewer",
        "reviewer/subagent breakdown",
        "compaction/cache evidence",
        "uncontrolled repeated calls",
        "lost status",
        "lost memory",
        "missing reviewer/subagent token attribution",
        "SOFTWARE-STATE",
        "SOFTWARE-CHECKPOINT",
        "SOFTWARE-COMPACT-TELEMETRY",
        "software_builder_subchecks",
        "R19-U1+R19-U2",
        "R19-U3+R19-U6+R19-U7",
        "cost-cap-hit counts as one failed attempt",
    ]:
        assert token in text

    for scenario_id in [
        "R13",
        "R14",
        "R15",
        "R16",
        "R19-U1",
        "R19-U2",
        "R19-U3",
        "R19-U6",
        "R19-U7",
        "R19-U10",
    ]:
        assert scenario_id in text

    assert "Do not duplicate" in text
    assert "Use AWS only for tests that reveal multiple production qualities" in text


def test_aws_test_execution_loop_requires_review_fix_retry_and_escalation():
    text = _AWS_TEST_LOOP.read_text(encoding="utf-8")

    for token in [
        "worker preflight",
        "Claude Phase A",
        "explicit spend approval",
        "AWS execution",
        "Metadata capture",
        "Worker post-run review",
        "Claude Phase C",
        "3 meaningful fix/retry attempts",
        "ESCALATION-<TEST>.md",
    ]:
        assert token in text


def test_r_tier_evidence_contract_has_typed_software_builder_fields():
    text = _EVIDENCE_CONTRACT.read_text(encoding="utf-8")

    for token in [
        "software_builder_subchecks",
        "status_round_trip",
        "todo_round_trip",
        "named_checkpoint_round_trip",
        "verify_done_stale_evidence_blocked",
        "compaction_event_emitted",
        "cache_evidence_recorded",
        "changed_files_within_fixture",
        "score_passed>=4",
        "breaker_fired=true",
        "MODEL_LIMITATION",
        "R19-U1+R19-U2",
        "R19-U3+R19-U6+R19-U7",
        "cost-cap-hit counts as one failed attempt",
    ]:
        assert token in text


def test_software_builder_block_revisit_plan_is_explicit():
    """Completed blocks should not churn, but concrete gaps must reopen them."""
    text = _REVISIT_PLAN.read_text(encoding="utf-8")

    for token in [
        "Do not reopen a completed/pushed block",
        "a new local test or optimized AWS test fails",
        "Claude final review finds a concrete gap",
        "Completed Blocks",
        "Remaining Blocks Carrying The Goal",
        "F2",
        "I",
        "G",
        "G2",
        "G3",
        "H",
        "H+",
    ]:
        assert token in text
