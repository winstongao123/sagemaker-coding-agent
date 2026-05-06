"""Lock tests for _status/scripts/r_tier_gate.py.

The gate is intentionally local-only: it catches missing executable R-tier
coverage, missing evidence files, and cost-cap drift before another AWS call
is made.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


_THIS = Path(__file__).resolve()
_V5_ROOT = _THIS.parents[4]
_SCRIPT_PATH = _V5_ROOT / "_status" / "scripts" / "r_tier_gate.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("r_tier_gate", str(_SCRIPT_PATH))
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_r_tier_gate_script_exists_and_compiles():
    assert _SCRIPT_PATH.is_file()
    import py_compile
    py_compile.compile(str(_SCRIPT_PATH), doraise=True)


def test_r_tier_gate_matrix_is_complete_and_costed():
    gate = _load_gate()
    repo_root = _V5_ROOT.parent

    assert gate.check_matrix(repo_root) == []


def test_r_tier_gate_detects_missing_suite(tmp_path):
    gate = _load_gate()
    r_tier = tmp_path / "compact_v5" / "MAIN" / "agent" / "tests" / "r_tier"
    r_tier.mkdir(parents=True)
    (r_tier / "test_r1_dashboard.py").write_text("# R1 only\n", encoding="utf-8")

    errors = gate.check_suite_materialized(tmp_path)
    assert any("R2" in e for e in errors)
    assert any("R19-U10" in e for e in errors)


def test_r_tier_gate_detects_cost_cap_excess(tmp_path):
    gate = _load_gate()
    status = tmp_path / "compact_v5" / "_status"
    status.mkdir(parents=True)
    (status / "r_tier_metrics.jsonl").write_text(
        json.dumps({"test": "R1", "call": 1, "cost_usd": 2.0}) + "\n",
        encoding="utf-8",
    )

    errors = gate.check_costs(tmp_path)
    assert any("R1 cost" in e for e in errors)


def test_r_tier_gate_allows_diagnostic_plus_retry_over_single_call_ceiling(tmp_path):
    gate = _load_gate()
    status = tmp_path / "compact_v5" / "_status"
    status.mkdir(parents=True)
    rows = [
        {"test": "R18-E7", "call": 1, "cost_usd": 0.1022, "verdict": "PROCESS_BLOCKER"},
        {"test": "R18-E7", "call": 2, "cost_usd": 0.0226, "verdict": "GENUINE_PASS"},
    ]
    (status / "r_tier_metrics.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    assert gate.check_costs(tmp_path) == []


def test_r_tier_gate_allows_initialized_empty_metrics(tmp_path):
    gate = _load_gate()
    status = tmp_path / "compact_v5" / "_status"
    status.mkdir(parents=True)
    (status / "r_tier_metrics.jsonl").write_text("", encoding="utf-8")

    assert gate.check_costs(tmp_path) == []


def test_r_tier_gate_accepts_complete_single_test_evidence(tmp_path):
    gate = _load_gate()
    status = tmp_path / "compact_v5" / "_status"
    reviews = status / "codex_reviews"
    reviews.mkdir(parents=True)

    (reviews / "r-tier-R1-phaseA-iter1-prompt.txt").write_text("prompt", encoding="utf-8")
    (reviews / "r-tier-R1-phaseA-iter1.md").write_text(
        "PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL", encoding="utf-8"
    )
    (reviews / "r-tier-R1-aws-call1.log").write_text("passed", encoding="utf-8")
    (reviews / "r-tier-R1-phaseC-iter1.md").write_text(
        "POST-PASS VERDICT: GENUINE_PASS", encoding="utf-8"
    )
    (status / "r-tier-R1-aws-call1-telemetry.json").write_text(
        json.dumps({
            "test": "R1", "call": 1,
            "per_turn": [{"turn": 1}],
            "tool_call_summary": {"TOTAL_calls": 0, "REPEATED_calls": 0},
            "compaction_events": [],
            "subagent_dispatches": [],
            "cache_efficiency_trend": {},
            "outcome": {"completed": True},
        }),
        encoding="utf-8",
    )
    (status / "r-tier-R1-aws-call1-quality.md").write_text(
        "Codex conclusion: NEAR_IDEAL", encoding="utf-8"
    )
    (status / "r_tier_review_log.md").write_text(
        "| R1 | READY | $0.01 |\n", encoding="utf-8"
    )
    (status / "r_tier_metrics.jsonl").write_text(
        json.dumps({
            "test": "R1",
            "call": 1,
            "date": "2026-05-03T00:00:00Z",
            "model": "claude-haiku-4-5",
            "tokens_in": 100,
            "tokens_out": 20,
            "cache_hit_pct": 0.5,
            "wallclock_s": 1.0,
            "tool_calls": 2,
            "completed": True,
            "cost_usd": 0.01,
            "verdict": "GENUINE_PASS",
        }) + "\n",
        encoding="utf-8",
    )

    assert gate.check_test_evidence(tmp_path, "R1") == []


def test_r_tier_gate_preserves_diagnostic_rows_before_later_pass(tmp_path):
    gate = _load_gate()
    status = tmp_path / "compact_v5" / "_status"
    reviews = status / "codex_reviews"
    reviews.mkdir(parents=True)

    (reviews / "r-tier-R1-phaseA-iter1-prompt.txt").write_text("prompt", encoding="utf-8")
    (reviews / "r-tier-R1-phaseA-iter1.md").write_text(
        "PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL", encoding="utf-8"
    )
    (reviews / "r-tier-R1-aws-call1.log").write_text("failed", encoding="utf-8")
    (reviews / "r-tier-R1-aws-call2.log").write_text("passed", encoding="utf-8")
    (reviews / "r-tier-R1-phaseC-iter1.md").write_text(
        "POST-PASS VERDICT: GENUINE_PASS", encoding="utf-8"
    )
    for call, completed in ((1, False), (2, True)):
        (status / f"r-tier-R1-aws-call{call}-telemetry.json").write_text(
            json.dumps({
                "test": "R1", "call": call,
                "per_turn": [{"turn": 1}],
                "tool_call_summary": {"TOTAL_calls": 0, "REPEATED_calls": 0},
                "compaction_events": [],
                "subagent_dispatches": [],
                "cache_efficiency_trend": {},
                "outcome": {"completed": completed, "cost_cap_hit": False},
            }),
            encoding="utf-8",
        )
    (status / "r-tier-R1-aws-call2-quality.md").write_text(
        "Codex conclusion: NEAR_IDEAL", encoding="utf-8"
    )
    (status / "r_tier_review_log.md").write_text(
        "| R1 | PROCESS_BLOCKER | $0.01 |\n| R1 | READY | $0.02 |\n",
        encoding="utf-8",
    )
    rows = [
        {
            "test": "R1",
            "call": 1,
            "date": "2026-05-03T00:00:00Z",
            "model": "claude-haiku-4-5",
            "tokens_in": 100,
            "tokens_out": 20,
            "cache_hit_pct": 0.5,
            "wallclock_s": 1.0,
            "tool_calls": 2,
            "completed": False,
            "cost_usd": 0.01,
            "verdict": "PROCESS_BLOCKER",
        },
        {
            "test": "R1",
            "call": 2,
            "date": "2026-05-03T00:01:00Z",
            "model": "claude-haiku-4-5",
            "tokens_in": 100,
            "tokens_out": 20,
            "cache_hit_pct": 0.5,
            "wallclock_s": 1.0,
            "tool_calls": 2,
            "completed": True,
            "cost_usd": 0.02,
            "verdict": "GENUINE_PASS",
        },
    ]
    (status / "r_tier_metrics.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    assert gate.check_test_evidence(tmp_path, "R1") == []


def test_r_tier_gate_uses_latest_phase_a_decision_not_exact_latest_token(tmp_path):
    gate = _load_gate()
    status = tmp_path / "compact_v5" / "_status"
    reviews = status / "codex_reviews"
    reviews.mkdir(parents=True)

    (reviews / "r-tier-R1-phaseA-iter1-prompt.txt").write_text("prompt", encoding="utf-8")
    (reviews / "r-tier-R1-phaseA-iter1.md").write_text(
        "PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL", encoding="utf-8"
    )
    (reviews / "r-tier-R1-phaseA-iter2.md").write_text(
        "The fix is sound. AWS call #2 is justified.", encoding="utf-8"
    )
    (reviews / "r-tier-R1-aws-call1.log").write_text("passed", encoding="utf-8")
    (reviews / "r-tier-R1-phaseC-iter1.md").write_text(
        "POST-PASS VERDICT: GENUINE_PASS", encoding="utf-8"
    )
    (status / "r-tier-R1-aws-call1-telemetry.json").write_text(
        json.dumps({
            "test": "R1", "call": 1,
            "per_turn": [{"turn": 1}],
            "tool_call_summary": {"TOTAL_calls": 0, "REPEATED_calls": 0},
            "compaction_events": [],
            "subagent_dispatches": [],
            "cache_efficiency_trend": {},
            "outcome": {"completed": True},
        }),
        encoding="utf-8",
    )
    (status / "r-tier-R1-aws-call1-quality.md").write_text(
        "Codex conclusion: NEAR_IDEAL", encoding="utf-8"
    )
    (status / "r_tier_review_log.md").write_text(
        "| R1 | READY | $0.01 |\n", encoding="utf-8"
    )
    (status / "r_tier_metrics.jsonl").write_text(
        json.dumps({
            "test": "R1",
            "call": 1,
            "date": "2026-05-03T00:00:00Z",
            "model": "claude-haiku-4-5",
            "tokens_in": 100,
            "tokens_out": 20,
            "cache_hit_pct": 0.5,
            "wallclock_s": 1.0,
            "tool_calls": 2,
            "completed": True,
            "cost_usd": 0.01,
            "verdict": "GENUINE_PASS",
        }) + "\n",
        encoding="utf-8",
    )

    assert gate.check_test_evidence(tmp_path, "R1") == []


def test_r_tier_gate_rejects_semantic_bug_quality(tmp_path):
    gate = _load_gate()
    status = tmp_path / "compact_v5" / "_status"
    reviews = status / "codex_reviews"
    reviews.mkdir(parents=True)

    (reviews / "r-tier-R1-phaseA-iter1-prompt.txt").write_text("prompt", encoding="utf-8")
    (reviews / "r-tier-R1-phaseA-iter1.md").write_text(
        "PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL", encoding="utf-8"
    )
    (reviews / "r-tier-R1-aws-call1.log").write_text("passed", encoding="utf-8")
    (reviews / "r-tier-R1-phaseC-iter1.md").write_text(
        "POST-PASS VERDICT: GENUINE_PASS", encoding="utf-8"
    )
    (status / "r-tier-R1-aws-call1-telemetry.json").write_text(
        json.dumps({
            "test": "R1", "call": 1,
            "per_turn": [{"turn": 1}],
            "tool_call_summary": {"TOTAL_calls": 0, "REPEATED_calls": 0},
            "compaction_events": [],
            "subagent_dispatches": [],
            "cache_efficiency_trend": {},
            "outcome": {"completed": True},
        }),
        encoding="utf-8",
    )
    (status / "r-tier-R1-aws-call1-quality.md").write_text(
        "Codex conclusion: SEMANTIC_BUG_DETECTED", encoding="utf-8"
    )
    (status / "r_tier_review_log.md").write_text(
        "| R1 | READY | $0.01 |\n", encoding="utf-8"
    )
    (status / "r_tier_metrics.jsonl").write_text(
        json.dumps({
            "test": "R1", "call": 1, "date": "2026-05-03T00:00:00Z",
            "model": "claude-haiku-4-5", "tokens_in": 1, "tokens_out": 1,
            "cache_hit_pct": 0.0, "wallclock_s": 1.0, "tool_calls": 0,
            "completed": True, "cost_usd": 0.01, "verdict": "GENUINE_PASS",
        }) + "\n",
        encoding="utf-8",
    )

    errors = gate.check_test_evidence(tmp_path, "R1")
    assert any("SEMANTIC_BUG_DETECTED" in e for e in errors)
