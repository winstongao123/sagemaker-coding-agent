"""R-tier evidence and cost gate.

Cheap local guard for the v5.0.1 real-AWS validation process. It does not
invoke Bedrock. It verifies that the executable R-tier suite and persisted
evidence match the user contract before the worker advances.

Usage examples:
  python compact_v5/_status/scripts/r_tier_gate.py --repo-root .
  python compact_v5/_status/scripts/r_tier_gate.py --repo-root . --test R1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


TOTAL_COST_CAP_USD = 14.25
USER_APPROVED_RETRY_BUFFER_MULTIPLIER = 1.20
MATRIX_REL_PATH = Path("compact_v5") / "_status" / "r_tier_test_matrix.json"
DIAGNOSTIC_NON_READY_VERDICTS = {
    "FAIL",
    "PROCESS_BLOCKER",
    "PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW",
    "DIAGNOSTIC_NON_READY",
    "DEFERRED-NOT-IMPLEMENTED",
    "CALL1_FUNCTIONAL_PASS_BUNDLE_BLOCKED",
    "TEST_DESIGN_FIX_REQUIRED_CLAUDE_REVIEW_BLOCKED",
}

# 42 v5-only scenarios: R1-R17, R18 E1-E15, R19 U1-U10.
EXPECTED_SCENARIOS: Tuple[str, ...] = tuple(
    [f"R{i}" for i in range(1, 18)]
    + [f"R18-E{i}" for i in range(1, 16)]
    + [f"R19-U{i}" for i in range(1, 11)]
)

PER_SCENARIO_CAPS: Dict[str, float] = {
    "R1": 1.00, "R2": 0.50, "R3": 0.50, "R4": 0.20,
    "R5": 0.50, "R6": 0.30, "R7": 0.50, "R8": 0.00,
    "R9": 0.30, "R10": 1.00, "R11": 1.50, "R12": 0.20,
    "R13": 0.50, "R14": 0.75, "R15": 0.50, "R16": 1.00,
    "R17": 0.30,
    **{f"R18-E{i}": cap for i, cap in enumerate(
        [0.30, 0.00, 0.10, 0.10, 0.00, 0.10, 0.10, 0.10,
         0.00, 0.10, 0.20, 0.00, 0.10, 0.20, 0.20],
        start=1,
    )},
    **{f"R19-U{i}": cap for i, cap in enumerate(
        [0.20, 0.20, 0.50, 0.40, 0.30, 0.20, 0.20, 0.30, 0.30, 0.50],
        start=1,
    )},
}


def _load_matrix(repo_root: Path) -> List[dict]:
    matrix_path = repo_root / MATRIX_REL_PATH
    if not matrix_path.is_file():
        return []
    try:
        data = json.loads(_read_text(matrix_path))
    except json.JSONDecodeError:
        return [{"_malformed_matrix": str(matrix_path)}]
    return data if isinstance(data, list) else [{"_malformed_matrix": str(matrix_path)}]


def _expected_from_matrix(repo_root: Path) -> Tuple[Tuple[str, ...], Dict[str, float]]:
    matrix = _load_matrix(repo_root)
    valid = [row for row in matrix if isinstance(row, dict) and row.get("id")]
    if not valid:
        return EXPECTED_SCENARIOS, PER_SCENARIO_CAPS
    ids = tuple(str(row["id"]) for row in valid)
    caps: Dict[str, float] = {}
    for row in valid:
        try:
            caps[str(row["id"])] = float(row.get("cost_cap_usd", 0.0) or 0.0)
        except (TypeError, ValueError):
            caps[str(row["id"])] = 0.0
    return ids, caps


def check_matrix(repo_root: Path) -> List[str]:
    """Verify the canonical matrix is present, complete, and cost-capped."""
    errors: List[str] = []
    matrix_path = repo_root / MATRIX_REL_PATH
    if not matrix_path.is_file():
        return [f"missing test matrix: {matrix_path}"]
    matrix = _load_matrix(repo_root)
    if any("_malformed_matrix" in row for row in matrix if isinstance(row, dict)):
        return [f"malformed test matrix JSON: {matrix_path}"]
    ids = [str(row.get("id", "")) for row in matrix if isinstance(row, dict)]
    missing = [sid for sid in EXPECTED_SCENARIOS if sid not in ids]
    extra = [sid for sid in ids if sid and sid not in EXPECTED_SCENARIOS]
    if missing:
        errors.append(f"test matrix missing IDs: {', '.join(missing)}")
    if extra:
        errors.append(f"test matrix has unexpected IDs: {', '.join(extra)}")
    if len(ids) != len(set(ids)):
        errors.append("test matrix contains duplicate IDs")
    for row in matrix:
        if not isinstance(row, dict):
            errors.append("test matrix contains non-object row")
            continue
        for key in ("id", "title", "kind", "model", "cost_cap_usd", "status", "benefit", "ready_criteria"):
            if key not in row or row.get(key) in ("", None):
                errors.append(f"{row.get('id', '<unknown>')}: matrix missing {key}")
    total = 0.0
    for row in matrix:
        if not isinstance(row, dict):
            continue
        try:
            total += float(row.get("cost_cap_usd", 0.0) or 0.0)
        except (TypeError, ValueError):
            errors.append(f"{row.get('id', '<unknown>')}: invalid cost_cap_usd")
    if round(total, 2) != TOTAL_COST_CAP_USD:
        errors.append(f"test matrix cap total ${total:.2f} != expected ${TOTAL_COST_CAP_USD:.2f}")
    return errors


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _load_metrics(path: Path) -> List[dict]:
    if not path.is_file():
        return []
    rows: List[dict] = []
    for line in _read_text(path).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"_malformed": line})
    return rows


def _glob_any(base: Path, patterns: Iterable[str]) -> bool:
    return any(any(base.glob(p)) for p in patterns)


def _glob_paths(base: Path, patterns: Iterable[str]) -> List[Path]:
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(base.glob(pattern))
    return sorted(paths, key=lambda p: p.name)


def _latest_text(base: Path, patterns: Iterable[str]) -> str:
    paths = _glob_paths(base, patterns)
    return _read_text(paths[-1]) if paths else ""


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    return any(needle in text for needle in needles)


def _phase_a_latest_decision_is_approval(base: Path, test_id: str) -> bool:
    """Return whether the latest decision-bearing Phase A review approves.

    Older evidence includes a few post-fix Phase A confirmation reviews whose
    final reviewer wording is "AWS call #N may proceed/is justified" rather
    than the exact original APPROVE_FOR_AWS_CALL token. The final gate should
    honor the latest decision-bearing review, while still letting a later
    REJECT override an earlier approval.
    """
    decision: bool | None = None
    for path in _glob_paths(base, [f"r-tier-{test_id}-phaseA-iter*.md"]):
        text = _read_text(path)
        if "PRE-FLIGHT VERDICT: REJECT" in text or "\nREJECT" in text:
            decision = False
        if _contains_any(
            text,
            (
                "APPROVE_FOR_AWS_CALL",
                "APPROVE_FOR_LOCAL_MOCK",
                "APPROVE_FOR_DISPOSITION",
                "APPROVE_DISPOSITION_PLAN",
                "AWS call #1 may proceed",
                "AWS call #2 is justified",
            ),
        ):
            decision = True
    return decision is True


def check_suite_materialized(repo_root: Path) -> List[str]:
    """Verify the executable R-tier test suite exists for the expected IDs."""
    errors: List[str] = []
    r_tier = repo_root / "compact_v5" / "MAIN" / "agent" / "tests" / "r_tier"
    if not r_tier.is_dir():
        return [f"missing R-tier directory: {r_tier}"]

    all_text = "\n".join(_read_text(p) for p in r_tier.glob("test_*.py"))
    expected, _caps = _expected_from_matrix(repo_root)
    for scenario in expected:
        if scenario.startswith("R18-"):
            marker = scenario.split("-", 1)[1]
            if "R18" not in all_text or marker not in all_text:
                errors.append(f"missing executable marker for {scenario}")
        elif scenario.startswith("R19-"):
            marker = scenario.split("-", 1)[1]
            if "R19" not in all_text or marker not in all_text:
                errors.append(f"missing executable marker for {scenario}")
        else:
            if scenario not in all_text:
                errors.append(f"missing executable marker for {scenario}")
    return errors


def check_costs(repo_root: Path) -> List[str]:
    """Verify local metrics stay within total and per-scenario caps.

    The matrix cap is the planned budget. The hard local retry ceiling allows
    the user-approved 20% buffer per recorded call while preserving cumulative
    spend history. Diagnostic/non-ready spend remains in the total matrix spend;
    a later retry has its own explicit hard ceiling and does not erase the
    diagnostic row that came before it.
    """
    errors: List[str] = []
    metrics_path = repo_root / "compact_v5" / "_status" / "r_tier_metrics.jsonl"
    if not metrics_path.is_file():
        return [f"missing metrics file: {metrics_path}"]
    rows = _load_metrics(metrics_path)
    total = 0.0
    by_test: Dict[str, float] = {}
    diagnostic_by_test: Dict[str, bool] = {}
    _expected, caps = _expected_from_matrix(repo_root)
    for i, row in enumerate(rows, start=1):
        if "_malformed" in row:
            errors.append(f"malformed JSONL metrics row {i}: {row['_malformed'][:120]}")
            continue
        test = str(row.get("test", ""))
        try:
            cost = float(row.get("cost_usd", 0.0) or 0.0)
        except (TypeError, ValueError):
            errors.append(f"metrics row {i} has invalid cost_usd: {row.get('cost_usd')!r}")
            continue
        total += cost
        by_test[test] = by_test.get(test, 0.0) + cost
        if row.get("verdict") in DIAGNOSTIC_NON_READY_VERDICTS:
            diagnostic_by_test[test] = True
        cap = caps.get(test)
        if cap is not None:
            ceiling = cap * USER_APPROVED_RETRY_BUFFER_MULTIPLIER
            if cost > ceiling + 1e-9:
                errors.append(
                    f"{test} row {i} cost ${cost:.4f} exceeds scenario cap ${cap:.2f} "
                    f"plus 20% retry buffer (${ceiling:.2f})"
                )
    total_ceiling = TOTAL_COST_CAP_USD * USER_APPROVED_RETRY_BUFFER_MULTIPLIER
    if total > total_ceiling:
        errors.append(
            f"total R-tier cost ${total:.4f} exceeds matrix cap "
            f"${TOTAL_COST_CAP_USD:.2f} plus 20% retry buffer "
            f"(${total_ceiling:.2f})"
        )
    for test, cost in sorted(by_test.items()):
        cap = caps.get(test)
        if cap is not None and not diagnostic_by_test.get(test):
            ceiling = cap * USER_APPROVED_RETRY_BUFFER_MULTIPLIER
            if cost > ceiling + 1e-9:
                errors.append(
                    f"{test} cost ${cost:.4f} exceeds scenario cap ${cap:.2f} "
                    f"plus 20% retry buffer (${ceiling:.2f})"
                )
    return errors


def check_test_evidence(repo_root: Path, test_id: str) -> List[str]:
    """Verify persisted review/log/telemetry/quality files for one test ID."""
    errors: List[str] = []
    status = repo_root / "compact_v5" / "_status"
    reviews = status / "codex_reviews"
    review_log = status / "r_tier_review_log.md"
    metrics = status / "r_tier_metrics.jsonl"

    escalation = reviews / f"ESCALATION-{test_id}.md"
    review_log_text = _read_text(review_log)
    metric_rows = _load_metrics(metrics)
    rows_for_test = [
        r for r in metric_rows
        if str(r.get("test")) == test_id and "_malformed" not in r
    ]
    matrix_rows = {
        str(row.get("id")): row
        for row in _load_matrix(repo_root)
        if isinstance(row, dict) and row.get("id")
    }
    is_mock = str(matrix_rows.get(test_id, {}).get("kind", "")).lower() == "mock"
    is_disposition = str(matrix_rows.get(test_id, {}).get("status", "")).upper() == "DISPOSITION_OK"
    pass_rows = [
        row for row in rows_for_test
        if row.get("completed") is True
        and row.get("verdict") in {"GENUINE_PASS", "READY", "DISPOSITION_OK"}
    ]
    phase_c_text = _latest_text(reviews, [f"r-tier-{test_id}-phaseC-iter*.md"])
    has_later_ready_evidence = (
        bool(pass_rows)
        and ("GENUINE_PASS" in phase_c_text or (is_disposition and "DISPOSITION_OK" in phase_c_text))
        and test_id in review_log_text
        and ("READY" in review_log_text or (is_disposition and "DISPOSITION_OK" in review_log_text))
    )
    escalated = escalation.is_file() and not has_later_ready_evidence

    required_patterns = {
        "phase A prompt": [f"r-tier-{test_id}-phaseA-iter*-prompt.txt"],
        "phase A review": [f"r-tier-{test_id}-phaseA-iter*.md"],
    }
    if is_disposition:
        required_patterns["reviewed disposition"] = [f"r-tier-{test_id}-disposition-iter*.md"]
    else:
        required_patterns["AWS/raw call log"] = (
            [f"r-tier-{test_id}-local-call*.log"]
            if is_mock else [f"r-tier-{test_id}-aws-call*.log"]
        )
    if not escalated:
        required_patterns["phase C post-pass review"] = [f"r-tier-{test_id}-phaseC-iter*.md"]
    for label, patterns in required_patterns.items():
        if not _glob_any(reviews, patterns):
            errors.append(f"{test_id}: missing {label} in {reviews}")

    phase_a_text = _latest_text(reviews, [f"r-tier-{test_id}-phaseA-iter*.md"])
    if phase_a_text and not _phase_a_latest_decision_is_approval(reviews, test_id):
        errors.append(f"{test_id}: latest phase A decision does not approve AWS call")

    if not escalated:
        if phase_c_text and "GENUINE_PASS" not in phase_c_text and not (
            is_disposition and "DISPOSITION_OK" in phase_c_text
        ):
            errors.append(f"{test_id}: phase C review lacks GENUINE_PASS")

    call_prefix = "local-call" if is_mock else "aws-call"
    if not is_disposition and not _glob_any(status, [f"r-tier-{test_id}-{call_prefix}*-telemetry.json"]):
        errors.append(f"{test_id}: missing telemetry.json in {status}")
    if not is_disposition and not _glob_any(status, [f"r-tier-{test_id}-{call_prefix}*-quality.md"]):
        errors.append(f"{test_id}: missing quality.md in {status}")
    quality_text = _latest_text(status, [f"r-tier-{test_id}-{call_prefix}*-quality.md"])
    if quality_text:
        if "SEMANTIC_BUG_DETECTED" in quality_text:
            errors.append(f"{test_id}: quality review contains SEMANTIC_BUG_DETECTED")
        if not _contains_any(
            quality_text,
            ("NEAR_IDEAL", "WORKING_BUT_SUBOPTIMAL", "INEFFICIENT"),
        ):
            errors.append(f"{test_id}: quality review lacks an accepted composite verdict")

    if not review_log.is_file() or test_id not in review_log_text:
        errors.append(f"{test_id}: missing row in {review_log}")
    elif not escalated and "READY" not in review_log_text and not (
        is_disposition and "DISPOSITION_OK" in review_log_text
    ):
        errors.append(f"{test_id}: review log row lacks READY")

    diagnostic_calls: set[int] = set()
    if not rows_for_test:
        errors.append(f"{test_id}: missing JSONL metrics row in {metrics}")
    else:
        required_metric_keys = {
            "test", "call", "date", "model", "tokens_in", "tokens_out",
            "cache_hit_pct", "wallclock_s", "tool_calls", "completed",
            "cost_usd", "verdict",
        }
        if not escalated and not pass_rows:
            errors.append(f"{test_id}: missing completed pass/ready JSONL metrics row")
        for row in rows_for_test:
            missing = required_metric_keys - set(row.keys())
            if missing:
                errors.append(f"{test_id}: metrics row missing keys {sorted(missing)}")
            row_is_pass = (
                row.get("completed") is True
                and row.get("verdict") in {"GENUINE_PASS", "READY", "DISPOSITION_OK"}
            )
            row_is_diagnostic = row.get("verdict") in DIAGNOSTIC_NON_READY_VERDICTS
            if row_is_diagnostic:
                try:
                    diagnostic_calls.add(int(row.get("call")))
                except (TypeError, ValueError):
                    pass
            if not escalated and not row_is_pass and not row_is_diagnostic:
                errors.append(
                    f"{test_id}: metrics row is neither pass/ready nor diagnostic non-ready"
                )
            if test_id in {"R13", "R14", "R15"}:
                if not row_is_pass:
                    continue
                if row.get("changed_files_within_fixture") is not True:
                    errors.append(
                        f"{test_id}: metrics row must set changed_files_within_fixture=true"
                    )
            if test_id == "R13":
                if not row_is_pass:
                    continue
                try:
                    passed = int(row.get("score_passed", -1))
                    total_score = int(row.get("score_total", -1))
                except (TypeError, ValueError):
                    passed = -1
                    total_score = -1
                if total_score != 5 or passed < 4:
                    errors.append(
                        "R13: READY metrics must show score_total=5 and score_passed>=4"
                    )

    # If an escalation exists, it must be reflected in the review log.
    if escalated:
        if test_id not in review_log_text or "ESCALATED" not in review_log_text:
            errors.append(f"{test_id}: escalation file exists but review log lacks ESCALATED row")

    # Basic telemetry sanity for every telemetry file.
    if is_disposition:
        return errors

    # Basic telemetry sanity for every telemetry file.
    for fp in status.glob(f"r-tier-{test_id}-{call_prefix}*-telemetry.json"):
        try:
            data = json.loads(_read_text(fp))
        except json.JSONDecodeError as exc:
            errors.append(f"{test_id}: malformed telemetry {fp.name}: {exc}")
            continue
        for key in (
            "test", "call", "per_turn", "tool_call_summary",
            "compaction_events", "subagent_dispatches",
            "cache_efficiency_trend", "outcome",
        ):
            if key not in data:
                errors.append(f"{test_id}: telemetry {fp.name} missing key {key}")
        if data.get("per_turn") == []:
            errors.append(f"{test_id}: telemetry {fp.name} has empty per_turn")
        try:
            telemetry_call = int(data.get("call"))
        except (TypeError, ValueError):
            telemetry_call = -1
        is_diagnostic_telemetry = telemetry_call in diagnostic_calls
        if not escalated and not is_diagnostic_telemetry and isinstance(data.get("outcome"), dict):
            if data["outcome"].get("completed") is not True:
                errors.append(f"{test_id}: telemetry {fp.name} outcome.completed is not true")
            if data["outcome"].get("cost_cap_hit") is True:
                errors.append(f"{test_id}: telemetry {fp.name} reports cost_cap_hit")
        if test_id == "R16":
            subchecks = data.get("software_builder_subchecks")
            required_subchecks = {
                "status_round_trip",
                "todo_round_trip",
                "named_checkpoint_round_trip",
                "verify_done_stale_evidence_blocked",
                "compaction_event_emitted",
                "cache_evidence_recorded",
                "cost_context_reported",
                "final_artifact_quality_passed",
            }
            if not isinstance(subchecks, dict):
                errors.append(
                    f"R16: telemetry {fp.name} missing software_builder_subchecks object"
                )
            else:
                missing_subchecks = [
                    key for key in sorted(required_subchecks)
                    if subchecks.get(key) is not True
                ]
                if missing_subchecks:
                    errors.append(
                        f"R16: telemetry {fp.name} missing/false subchecks {missing_subchecks}"
                    )
        if test_id == "R19-U7":
            if data.get("breaker_fired") is not True:
                errors.append(
                    f"R19-U7: telemetry {fp.name} must set breaker_fired=true"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--test", help="Specific test ID to verify, e.g. R1 or R19-U3")
    parser.add_argument("--skip-suite", action="store_true",
                        help="Skip executable-suite materialization check.")
    parser.add_argument("--skip-evidence", action="store_true",
                        help="Skip per-test evidence checks for local development only.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    errors: List[str] = []
    errors.extend(check_matrix(repo_root))
    if not args.skip_suite:
        errors.extend(check_suite_materialized(repo_root))
    errors.extend(check_costs(repo_root))
    if args.test:
        errors.extend(check_test_evidence(repo_root, args.test))
    elif not args.skip_evidence:
        expected, _caps = _expected_from_matrix(repo_root)
        for test_id in expected:
            errors.extend(check_test_evidence(repo_root, test_id))

    if errors:
        print("R-tier gate FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("R-tier gate PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
