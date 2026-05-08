"""Mechanical scope-completeness audit for the v5.0.1 redo.

This script is intentionally ledger-aware. Grep hits are useful clues, but the
gate that prevents scope drift is simpler and harder to game:

1. Parse expected row ids from SYNTHESIS_MASTER.md.
2. Parse the matching per-block LEDGER.md.
3. Report missing ledger rows, ship-blocking dispositions, and weak evidence.

No AWS calls are made. No files are modified.

Examples:
  py -3.11 compact_v5/_status/scripts/scope_audit.py --block A
  py -3.11 compact_v5/_status/scripts/scope_audit.py --all --summary
  py -3.11 compact_v5/_status/scripts/scope_audit.py --block A --json
  py -3.11 compact_v5/_status/scripts/scope_audit.py --block A --strict
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
SYNTHESIS_PATH = REPO_ROOT / "compact_v5" / "_phase_2" / "wave_5_deep" / "SYNTHESIS_MASTER.md"
AUDIT_ROOT = REPO_ROOT / "compact_v5" / "_status" / "v5_completion_audit"
BLOCKS_ROOT = AUDIT_ROOT / "blocks"

BLOCKS = [
    "0",
    "A",
    "B",
    "B+",
    "C",
    "C+",
    "D",
    "E+F",
    "F2",
    "G",
    "G2",
    "G3",
    "H",
    "H+",
    "I",
    "L",
    "M",
    "N",
    "T",
    "J",
    "K",
]

SHIP_BLOCKING = {"PARTIAL", "MISSING"}
USER_APPROVED_NONBLOCKING = {"DEFERRED_USER_APPROVED", "DROPPED_USER_APPROVED", "N/A_CONSTRAINT"}
FINAL_DISPOSITIONS = {"SHIPPED", *SHIP_BLOCKING, *USER_APPROVED_NONBLOCKING}


def disposition_count_key(disposition: str) -> str:
    """Map ledger dispositions to internal summary-count keys."""
    return disposition.strip().lower().replace("/", "")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def split_markdown_row(line: str) -> list[str]:
    """Split a markdown table row, ignoring pipes inside inline code spans."""
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]

    cells: list[str] = []
    current: list[str] = []
    in_code = False
    for char in text:
        if char == "`":
            in_code = not in_code
            current.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def row_belongs_to_block(row_id: str, block: str) -> bool:
    if block in {"B+", "C+", "H+"}:
        return bool(re.fullmatch(re.escape(block) + r"\d+", row_id))
    if block == "E+F":
        return row_id.startswith("EF-")
    if block == "G2":
        return row_id == "G2" or row_id.startswith("G2-")
    if block in {"F2", "G3"}:
        return row_id.startswith(block + "-")
    return row_id.startswith(block + "-")


def parse_synthesis_rows(block: str) -> list[dict[str, str]]:
    text = read_text(SYNTHESIS_PATH)
    rows: list[dict[str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.startswith("|"):
            continue
        cells = split_markdown_row(line)
        if len(cells) < 2:
            continue
        row_id = cells[0]
        if not re.fullmatch(r"[A-Z0-9+]+-?\d+", row_id):
            continue
        if not row_belongs_to_block(row_id, block):
            continue
        rows.append(
            {
                "row_id": row_id,
                "capability": cells[1],
                "source": cells[2] if len(cells) > 2 else "",
                "file_line": cells[3] if len(cells) > 3 else "",
                "priority": cells[5] if len(cells) > 5 else "",
                "fit": cells[6] if len(cells) > 6 else "",
                "synthesis_line": str(line_no),
            }
        )
    return rows


def block_dir_name(block: str) -> str:
    return block


def parse_markdown_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    text = read_text(path)
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = split_markdown_row(line)
        if not cells:
            continue
        if header is None and "row_id" in cells:
            header = cells
            continue
        if header is None:
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        if len(cells) < len(header):
            continue
        rows.append(dict(zip(header, cells)))
    return header or [], rows


def parse_ledger_rows(block: str) -> dict[str, dict[str, str]]:
    ledger = BLOCKS_ROOT / block_dir_name(block) / "LEDGER.md"
    _, rows = parse_markdown_table(ledger)
    return {row.get("row_id", ""): row for row in rows if row.get("row_id")}


def is_noneish(value: str) -> bool:
    cleaned = (value or "").strip().upper()
    return cleaned in {"", "NONE", "NONE_FOUND", "N/A", "NOT_INCLUDED_IN_REVIEW"}


def evidence_problems(row: dict[str, str]) -> list[str]:
    problems: list[str] = []
    disposition = row.get("disposition", "").strip()
    if disposition != "SHIPPED":
        return problems
    if is_noneish(row.get("code_evidence", "")):
        problems.append("missing code_evidence")
    test = row.get("test_evidence", "")
    if is_noneish(test) and not test.startswith("NO_TEST_JUSTIFICATION:"):
        problems.append("missing test_evidence")
    if is_noneish(row.get("port_log", "")):
        problems.append("missing port_log")
    return problems


def audit_block(block: str) -> dict[str, Any]:
    expected = parse_synthesis_rows(block)
    ledger = parse_ledger_rows(block)
    items: list[dict[str, Any]] = []
    counts = {
        "expected": len(expected),
        "ledger_rows": len(ledger),
        "ledger_missing": 0,
        "shipped": 0,
        "partial": 0,
        "missing": 0,
        "deferred_user_approved": 0,
        "dropped_user_approved": 0,
        "na_constraint": 0,
        "weak_shipped_evidence": 0,
        "unknown_disposition": 0,
    }

    for spec in expected:
        row_id = spec["row_id"]
        ledger_row = ledger.get(row_id)
        if ledger_row is None:
            counts["ledger_missing"] += 1
            items.append(
                {
                    **spec,
                    "status": "LEDGER_MISSING",
                    "disposition": "LEDGER_MISSING",
                    "evidence_problems": ["row absent from block ledger"],
                    "ship_blocking": True,
                }
            )
            continue

        disposition = ledger_row.get("disposition", "").strip()
        disposition_key = disposition_count_key(disposition)
        if disposition_key in counts:
            counts[disposition_key] += 1
        elif disposition not in FINAL_DISPOSITIONS:
            counts["unknown_disposition"] += 1

        problems = evidence_problems(ledger_row)
        if problems:
            counts["weak_shipped_evidence"] += 1

        ship_blocking = (
            disposition in SHIP_BLOCKING
            or disposition == ""
            or disposition == "LEDGER_MISSING"
            or bool(problems)
            or disposition not in FINAL_DISPOSITIONS
        )
        items.append(
            {
                **spec,
                "status": disposition or "UNKNOWN",
                "disposition": disposition or "UNKNOWN",
                "code_evidence": ledger_row.get("code_evidence", ""),
                "test_evidence": ledger_row.get("test_evidence", ""),
                "port_log": ledger_row.get("port_log", ""),
                "adr": ledger_row.get("adr", ""),
                "reviewer_verdict": ledger_row.get("reviewer_verdict", ""),
                "evidence_problems": problems,
                "ship_blocking": ship_blocking,
            }
        )

    extra_rows = sorted(set(ledger) - {row["row_id"] for row in expected})
    ship_blocking_rows = [item["row_id"] for item in items if item["ship_blocking"]]
    verdict = "READY_TO_REVIEW_CLOSE" if not ship_blocking_rows else "NEEDS_IMPLEMENTATION"
    if not expected:
        verdict = "NO_SPEC_ROWS_FOUND"
    if counts["ledger_missing"]:
        verdict = "LEDGER_INCOMPLETE"

    return {
        "block": block,
        "counts": counts,
        "extra_ledger_rows": extra_rows,
        "ship_blocking_rows": ship_blocking_rows,
        "items": items,
        "verdict": verdict,
    }


def render_block(audit: dict[str, Any]) -> str:
    c = audit["counts"]
    lines = [
        f"=== Block {audit['block']} ===",
        f"Expected rows: {c['expected']}",
        f"Ledger rows: {c['ledger_rows']}",
        (
            "SHIPPED: {shipped}  PARTIAL: {partial}  MISSING: {missing}  "
            "DEFERRED: {deferred_user_approved}  DROPPED: {dropped_user_approved}  "
            "N/A: {na_constraint}"
        ).format(**c),
        (
            "Ledger missing: {ledger_missing}  Weak shipped evidence: "
            "{weak_shipped_evidence}  Unknown disposition: {unknown_disposition}"
        ).format(**c),
        f"Ship-blocking rows: {', '.join(audit['ship_blocking_rows']) if audit['ship_blocking_rows'] else 'NONE'}",
        f"Verdict: {audit['verdict']}",
        "",
        "| row_id | disposition | ship_blocking | evidence_problems | capability |",
        "|---|---|---:|---|---|",
    ]
    for item in audit["items"]:
        problems = "; ".join(item["evidence_problems"]) if item["evidence_problems"] else ""
        capability = item["capability"].replace("|", "\\|")
        lines.append(
            f"| {item['row_id']} | {item['disposition']} | "
            f"{'YES' if item['ship_blocking'] else 'NO'} | {problems} | {capability} |"
        )
    if audit["extra_ledger_rows"]:
        lines.extend(["", f"Extra ledger rows not in SYNTHESIS_MASTER: {', '.join(audit['extra_ledger_rows'])}"])
    return "\n".join(lines)


def render_summary(audits: list[dict[str, Any]]) -> str:
    lines = [
        "| Block | Expected | Ledger | Shipped | Partial | Missing | Blocking | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for audit in audits:
        c = audit["counts"]
        lines.append(
            f"| {audit['block']} | {c['expected']} | {c['ledger_rows']} | "
            f"{c['shipped']} | {c['partial']} | {c['missing']} | "
            f"{len(audit['ship_blocking_rows'])} | {audit['verdict']} |"
        )
    total_expected = sum(a["counts"]["expected"] for a in audits)
    total_blocking = sum(len(a["ship_blocking_rows"]) for a in audits)
    lines.extend(["", f"TOTAL_EXPECTED_ROWS: {total_expected}", f"TOTAL_SHIP_BLOCKING_ROWS: {total_blocking}"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", help="Specific block, for example A, B+, E+F, H+")
    parser.add_argument("--all", action="store_true", help="Audit all known blocks")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--summary", action="store_true", help="Emit one summary table")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any blocking row remains")
    args = parser.parse_args()

    if args.all:
        blocks = BLOCKS
    elif args.block:
        blocks = [args.block]
    else:
        parser.error("Use --block <BLOCK> or --all")

    audits = [audit_block(block) for block in blocks]

    if args.json:
        print(json.dumps(audits, indent=2))
    elif args.summary or len(audits) > 1:
        print(render_summary(audits))
    else:
        print(render_block(audits[0]))

    if args.strict and any(a["ship_blocking_rows"] or a["counts"]["ledger_missing"] for a in audits):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
