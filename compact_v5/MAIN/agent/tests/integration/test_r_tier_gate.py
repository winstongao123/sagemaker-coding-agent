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
        json.dumps({"test": "R1", "call": 1, "cost_usd": 0.01}) + "\n",
        encoding="utf-8",
    )

    assert gate.check_test_evidence(tmp_path, "R1") == []
