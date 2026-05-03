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
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


TOTAL_COST_CAP_USD = 14.25

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


def check_suite_materialized(repo_root: Path) -> List[str]:
    """Verify the executable R-tier test suite exists for the expected IDs."""
    errors: List[str] = []
    r_tier = repo_root / "compact_v5" / "MAIN" / "agent" / "tests" / "r_tier"
    if not r_tier.is_dir():
        return [f"missing R-tier directory: {r_tier}"]

    all_text = "\n".join(_read_text(p) for p in r_tier.glob("test_*.py"))
    for scenario in EXPECTED_SCENARIOS:
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
    """Verify local metrics stay within total and per-scenario caps."""
    errors: List[str] = []
    metrics_path = repo_root / "compact_v5" / "_status" / "r_tier_metrics.jsonl"
    rows = _load_metrics(metrics_path)
    if not rows:
        return [f"missing or empty metrics file: {metrics_path}"]
    total = 0.0
    by_test: Dict[str, float] = {}
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
    if total > TOTAL_COST_CAP_USD:
        errors.append(f"total R-tier cost ${total:.4f} exceeds cap ${TOTAL_COST_CAP_USD:.2f}")
    for test, cost in sorted(by_test.items()):
        cap = PER_SCENARIO_CAPS.get(test)
        if cap is not None and cost > cap + 1e-9:
            errors.append(f"{test} cost ${cost:.4f} exceeds scenario cap ${cap:.2f}")
    return errors


def check_test_evidence(repo_root: Path, test_id: str) -> List[str]:
    """Verify persisted review/log/telemetry/quality files for one test ID."""
    errors: List[str] = []
    status = repo_root / "compact_v5" / "_status"
    reviews = status / "codex_reviews"
    review_log = status / "r_tier_review_log.md"
    metrics = status / "r_tier_metrics.jsonl"

    required_patterns = {
        "phase A prompt": [f"r-tier-{test_id}-phaseA-iter*-prompt.txt"],
        "phase A review": [f"r-tier-{test_id}-phaseA-iter*.md"],
        "AWS/raw call log": [f"r-tier-{test_id}-aws-call*.log"],
        "phase C post-pass review": [f"r-tier-{test_id}-phaseC-iter*.md"],
    }
    for label, patterns in required_patterns.items():
        if not _glob_any(reviews, patterns):
            errors.append(f"{test_id}: missing {label} in {reviews}")

    if not _glob_any(status, [f"r-tier-{test_id}-aws-call*-telemetry.json"]):
        errors.append(f"{test_id}: missing telemetry.json in {status}")
    if not _glob_any(status, [f"r-tier-{test_id}-aws-call*-quality.md"]):
        errors.append(f"{test_id}: missing quality.md in {status}")

    if not review_log.is_file() or test_id not in _read_text(review_log):
        errors.append(f"{test_id}: missing row in {review_log}")

    metric_rows = _load_metrics(metrics)
    if not any(str(r.get("test")) == test_id for r in metric_rows if "_malformed" not in r):
        errors.append(f"{test_id}: missing JSONL metrics row in {metrics}")

    # If an escalation exists, it must be reflected in the review log.
    escalation = reviews / f"ESCALATION-{test_id}.md"
    if escalation.is_file():
        log_text = _read_text(review_log)
        if test_id not in log_text or "ESCALATED" not in log_text:
            errors.append(f"{test_id}: escalation file exists but review log lacks ESCALATED row")

    # Basic telemetry sanity for every telemetry file.
    for fp in status.glob(f"r-tier-{test_id}-aws-call*-telemetry.json"):
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
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--test", help="Specific test ID to verify, e.g. R1 or R19-U3")
    parser.add_argument("--skip-suite", action="store_true",
                        help="Skip executable-suite materialization check.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    errors: List[str] = []
    if not args.skip_suite:
        errors.extend(check_suite_materialized(repo_root))
    errors.extend(check_costs(repo_root))
    if args.test:
        errors.extend(check_test_evidence(repo_root, args.test))

    if errors:
        print("R-tier gate FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("R-tier gate PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
