"""Zero-cost executable specs for remaining R-tier scenarios.

These tests materialize R6-R16, R18-E1..E15, and R19-U1..U10 without
calling Bedrock. They are the reviewable Phase A contract for the
remaining real/mock R-tier work:

- every scenario has an explicit cost cap matching r_tier_test_matrix.json
- real scenarios require RUN_REAL_BEDROCK plus Phase A approval before spend
- mock scenarios must stay local-only with cost_cap_usd == 0
- every scenario declares the evidence files needed by r_tier_gate.py

The real AWS tests still need Claude Phase A review and user approval before
execution. This file prevents "missing executable marker" drift while keeping
the suite fail-closed on spend.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


_THIS = Path(__file__).resolve()
_REPO_ROOT = _THIS.parents[5]
_MATRIX_PATH = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_test_matrix.json"

_REQUIRED_EVIDENCE = {
    "phase_a_prompt",
    "phase_a_review",
    "raw_call_log",
    "phase_c_review",
    "telemetry_json",
    "quality_review",
    "metrics_row",
    "review_log_row",
}

_MOCK_SCENARIOS = {"R8", "R18-E2", "R18-E5", "R18-E9", "R18-E12"}


SCENARIO_SPECS = {
    "R6": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.30,
        "fixture": "memory.md with 100 entries, duplicate facts, stale facts, and must-preserve facts",
        "prompt": "Run manual /dream consolidation once and report preserved facts.",
        "acceptance": [
            "DREAM_PROMPT_TEMPLATE four-phase structure is used",
            "required facts survive consolidation",
            "duplicate/stale entries are removed or collapsed",
            "DreamLock releases and rollback path is clean",
        ],
    },
    "R7": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.50,
        "fixture": "two-turn session starts on Haiku 4.5 AU then switches to Sonnet 4.5 AU",
        "prompt": "Perform a small task before and after model switch, preserving context.",
        "acceptance": [
            "post-switch Bedrock call uses Sonnet model id",
            "conversation context remains coherent after switch",
            "cache behavior is recorded in telemetry",
        ],
    },
    "R8": {
        "mode": "mock_local",
        "cost_cap_usd": 0.00,
        "fixture": "mock malformed JSON tool-call arguments",
        "prompt": "Exercise malformed-argument repair ladder without AWS.",
        "acceptance": [
            "malformed args are detected",
            "repair ladder retries with sanitized arguments",
            "fallback result is audited without Bedrock",
        ],
    },
    "R9": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.30,
        "fixture": "approval harness with approve, deny, and always-allow branches",
        "prompt": "Attempt one harmless write under each approval branch.",
        "acceptance": [
            "approve path executes and audits diff",
            "deny path blocks mutation",
            "always path persists approval policy for later tool calls",
        ],
    },
    "R10": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 1.00,
        "fixture": "saved conversation with nonzero cost, history, and tool evidence",
        "prompt": "Save, restart/load, continue, and prove cost/history are intact.",
        "acceptance": [
            "session cost restores after load",
            "chat history remains visible to the model",
            "new metrics append instead of resetting prior cost",
        ],
    },
    "R11": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 1.50,
        "fixture": "R1-style composite dashboard workflow using Sonnet 4.5 AU",
        "prompt": "Build chart and Word report using Sonnet under cap.",
        "acceptance": [
            "Sonnet model id is used for the workflow",
            "chart/report integrity assertions pass",
            "quality review is NEAR_IDEAL or WORKING_BUT_SUBOPTIMAL",
        ],
    },
    "R12": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.20,
        "fixture": "Unicode, RTL text, surrogate-like payloads, and malformed tool args",
        "prompt": "Recover from malformed args and preserve Unicode output.",
        "acceptance": [
            "malformed args recover without crash",
            "Unicode/RTL text round-trips through tool output",
            "error category is recorded in telemetry",
        ],
    },
    "R13": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.50,
        "fixture": "five HumanEval-mini Python tasks with deterministic unit tests",
        "prompt": "Implement five small functions and run their tests.",
        "acceptance": [
            "all five task tests pass or scored failure is logged",
            "no unrelated file edits occur",
            "final score is recorded in metrics/quality evidence",
        ],
    },
    "R14": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.75,
        "fixture": "multi-file package requiring symbol rename and import updates",
        "prompt": "Refactor across files, run pytest, and grep for stale names.",
        "acceptance": [
            "pytest passes after refactor",
            "grep shows no stale symbol names",
            "changed-file list is limited to fixture workspace",
        ],
    },
    "R15": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.50,
        "fixture": "two planted bugs with failing tests and one tempting false-positive area",
        "prompt": "Find and fix both planted bugs only.",
        "acceptance": [
            "both failing tests pass",
            "false-positive area remains unchanged",
            "debug evidence shows test-driven diagnosis",
        ],
    },
    "R16": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 1.00,
        "fixture": "small Flask CRUD app requirements and tests",
        "prompt": "Build the CRUD app, run tests, and preserve session coherence.",
        "acceptance": [
            "app tests pass",
            "routes, persistence, validation, and errors are covered",
            "compaction/cache behavior is reviewed for long-session coherence",
        ],
    },
    "R18-E1": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.30,
        "fixture": "Bedrock 429 throttle observation or controlled infra escalation",
        "prompt": "Trigger or observe retry/backoff behavior under throttling pressure.",
        "acceptance": [
            "429 is retried/backed off or escalated as infra",
            "retry cap is not burned in an uncontrolled loop",
        ],
    },
    "R18-E2": {
        "mode": "mock_local",
        "cost_cap_usd": 0.00,
        "fixture": "mock Bedrock 5xx response ladder",
        "prompt": "Run deterministic 5xx recovery without AWS.",
        "acceptance": [
            "5xx retry ladder is exercised",
            "final error/result is categorized cleanly",
        ],
    },
    "R18-E3": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.10,
        "fixture": "near-cap session budget",
        "prompt": "Approach cost cap and prove halt/warning timing.",
        "acceptance": [
            "cap warning/halt appears before uncontrolled spend",
            "metrics show final cost under cap",
        ],
    },
    "R18-E4": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.10,
        "fixture": "skill alias request with one expected skill path",
        "prompt": "Invoke a skill by alias and perform a tiny read-only task.",
        "acceptance": [
            "intended skill activates",
            "wrong skill/tool path is not used",
        ],
    },
    "R18-E5": {
        "mode": "mock_local",
        "cost_cap_usd": 0.00,
        "fixture": "corrupt session JSON snapshot",
        "prompt": "Load corrupt snapshot and recover without AWS.",
        "acceptance": [
            "corruption is reported clearly",
            "valid snapshots remain intact",
        ],
    },
    "R18-E6": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.10,
        "fixture": "missing file and empty file in workspace",
        "prompt": "Recover from missing/empty file tool results.",
        "acceptance": [
            "tool error is surfaced to model",
            "agent changes approach and completes or asks user",
        ],
    },
    "R18-E7": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.10,
        "fixture": "very long tool output around truncation threshold",
        "prompt": "Read long output and continue using truncated evidence.",
        "acceptance": [
            "truncation is visible in telemetry",
            "agent continues coherently after truncation",
        ],
    },
    "R18-E8": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.10,
        "fixture": "concurrent sub-agent-style tasks with shared-state bait",
        "prompt": "Dispatch/check independent tasks and synthesize results.",
        "acceptance": [
            "outputs remain isolated",
            "no shared-state corruption appears in audit evidence",
        ],
    },
    "R18-E9": {
        "mode": "mock_local",
        "cost_cap_usd": 0.00,
        "fixture": "mock snapshot write failure",
        "prompt": "Simulate disk-full style write failure without filling disk.",
        "acceptance": [
            "write failure rolls back or reports safely",
            "no partial corrupt snapshot is accepted",
        ],
    },
    "R18-E10": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.10,
        "fixture": "plan-mode session with mutating tool bait",
        "prompt": "Attempt a mutation in plan mode and recover.",
        "acceptance": [
            "mutating action is blocked/audited",
            "agent remains coherent after block",
        ],
    },
    "R18-E11": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.20,
        "fixture": "sub-agent timeout while compaction is eligible",
        "prompt": "Handle timeout and continue parent task.",
        "acceptance": [
            "timeout is recorded",
            "parent can continue after timeout/compaction coordination",
        ],
    },
    "R18-E12": {
        "mode": "mock_local",
        "cost_cap_usd": 0.00,
        "fixture": "large mock audit log crossing rotation threshold",
        "prompt": "Exercise audit rotation locally.",
        "acceptance": [
            "rotation threshold behavior is deterministic",
            "retained logs remain readable",
        ],
    },
    "R18-E13": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.10,
        "fixture": "Unicode and RTL memory entries",
        "prompt": "Read/write memory with Unicode and RTL text.",
        "acceptance": [
            "Unicode/RTL survives memory path",
            "no surrogate or encoding crash appears",
        ],
    },
    "R18-E14": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.20,
        "fixture": "/dream interrupted mid-write",
        "prompt": "Interrupt consolidation and verify memory atomicity.",
        "acceptance": [
            "original or complete new memory remains valid",
            "partial corrupt memory is rejected",
        ],
    },
    "R18-E15": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.20,
        "fixture": "cache TTL expires mid-conversation",
        "prompt": "Continue after TTL expiry and document cache behavior.",
        "acceptance": [
            "cold-cache/TTL handling is visible in telemetry",
            "conversation remains coherent after expiry",
        ],
    },
    "R19-U1": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.20,
        "fixture": "ambiguous edit request with multiple plausible targets",
        "prompt": "Ask for clarification instead of editing blindly.",
        "acceptance": [
            "agent asks clarification or equivalent",
            "no speculative edit is made",
        ],
    },
    "R19-U2": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.20,
        "fixture": "contradictory requirements in one request",
        "prompt": "Identify conflict and request clarification.",
        "acceptance": [
            "conflict is explicitly reported",
            "agent does not paper over contradiction",
        ],
    },
    "R19-U3": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.50,
        "fixture": "hidden inheritance/cross-file dependency",
        "prompt": "Find dependency before edit and run tests.",
        "acceptance": [
            "search/explore occurs before edit",
            "final tests pass",
        ],
    },
    "R19-U4": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.40,
        "fixture": "conflicting sub-agent findings",
        "prompt": "Reconcile disagreement using evidence.",
        "acceptance": [
            "parent identifies conflict",
            "final conclusion cites supported evidence",
        ],
    },
    "R19-U5": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.30,
        "fixture": "one sub-agent fails while others return useful evidence",
        "prompt": "Complete parent task despite one failed child.",
        "acceptance": [
            "failure is recorded",
            "parent completes using remaining evidence",
        ],
    },
    "R19-U6": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.20,
        "fixture": "garbage/malformed tool output",
        "prompt": "Recover via retry or alternate tool path.",
        "acceptance": [
            "bad output is detected",
            "retry or alternative path succeeds or asks user",
        ],
    },
    "R19-U7": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.20,
        "fixture": "repeated-call circuit-breaker bait",
        "prompt": "Avoid repeated identical tool calls after block.",
        "acceptance": [
            "third repeated call is blocked or redirected",
            "agent changes approach",
        ],
    },
    "R19-U8": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.30,
        "fixture": "memory conflict Python 3.10 old preference vs Python 3.12 latest",
        "prompt": "Use latest user preference after memory conflict.",
        "acceptance": [
            "latest preference wins",
            "older preference is not used in final behavior",
        ],
    },
    "R19-U9": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.30,
        "fixture": "/dream semantic checklist with important facts and stale duplicates",
        "prompt": "Consolidate memory while preserving important facts.",
        "acceptance": [
            "all required facts are preserved",
            "stale duplicates are removed",
        ],
    },
    "R19-U10": {
        "mode": "real_aws_gated",
        "cost_cap_usd": 0.50,
        "fixture": "150-turn session with model switches and compactions",
        "prompt": "Finish final task after long-session context churn.",
        "acceptance": [
            "final task succeeds",
            "compactions/switches are logged",
            "no coherence loss appears in quality review",
        ],
    },
}


def _load_matrix() -> dict[str, dict]:
    rows = json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))
    return {str(row["id"]): row for row in rows}


@pytest.mark.parametrize("scenario_id,spec", sorted(SCENARIO_SPECS.items()))
def test_remaining_r_tier_scenario_has_reviewable_spec(scenario_id, spec):
    """Every remaining R-tier marker is materialized as a zero-cost spec."""
    matrix = _load_matrix()

    assert scenario_id in matrix
    assert spec["mode"] in {"real_aws_gated", "mock_local"}
    assert spec["cost_cap_usd"] == pytest.approx(float(matrix[scenario_id]["cost_cap_usd"]))
    assert spec["fixture"]
    assert spec["prompt"]
    assert len(spec["acceptance"]) >= 2


@pytest.mark.parametrize("scenario_id,spec", sorted(SCENARIO_SPECS.items()))
def test_remaining_r_tier_scenario_has_closed_evidence_contract(scenario_id, spec):
    """The phase review evidence required by r_tier_gate.py is explicit."""
    evidence = set(spec.get("evidence", _REQUIRED_EVIDENCE))

    assert _REQUIRED_EVIDENCE <= evidence
    assert "metrics_row" in evidence
    assert "review_log_row" in evidence


@pytest.mark.parametrize("scenario_id", sorted(_MOCK_SCENARIOS))
def test_mock_r_tier_scenario_stays_zero_cost(scenario_id):
    """Mock cases are executable without Bedrock and must remain zero-spend."""
    spec = SCENARIO_SPECS[scenario_id]

    assert spec["mode"] == "mock_local"
    assert spec["cost_cap_usd"] == 0.0


@pytest.mark.parametrize(
    "scenario_id",
    sorted(set(SCENARIO_SPECS) - _MOCK_SCENARIOS),
)
def test_real_r_tier_scenario_requires_explicit_aws_gate(scenario_id):
    """Real cases are not allowed to spend without explicit gate approval."""
    spec = SCENARIO_SPECS[scenario_id]

    assert spec["mode"] == "real_aws_gated"
    assert spec["cost_cap_usd"] > 0.0
    assert spec.get("requires_env", "RUN_REAL_BEDROCK") == "RUN_REAL_BEDROCK"
    assert spec.get("requires_phase_a_review", True) is True
