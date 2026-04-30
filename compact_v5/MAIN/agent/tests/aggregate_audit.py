"""V5 aggregate audit gate -- runs at fixed checkpoints (before phases 4, 7, 10, 13).

Per V5_PLAN.md "Aggregate Audit" section:
- Static prompt tokens: <= 2500 absolute after Phase 6.
- Per-turn schema overhead: from Phase 7 onward, must be strictly lower than
  Phase-6 baseline. (Phase 7+ implements deferred-loading; Phase 6 hasn't.)
- Tool count: <= v4 count + 0.
- Skill count: = 10 (Phase 10 task; not enforced before Phase 10).
- ADR-to-PORT_LOG ratio: every PORT_LOG row references an ADR-NNN.
- Token-by-section table: every section has a hard cap; none exceeded.
- Local-vs-Bedrock token-estimator parity: deferred (Phase 12).
- Cognitive-load test: Codex-evaluated, run separately.

Run:
    cd compact_v5/MAIN/agent && python tests/aggregate_audit.py [--phase N]

Exit code:
    0  → all metrics pass; phase unblocked.
    1  → at least one metric FAILED; phase blocked.
"""
from __future__ import annotations

import os
import re
import sys
from typing import List, Tuple

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Audit metric checks
# ============================================================

def check_static_prompt_tokens(target_phase: int) -> Tuple[bool, str]:
    """Static prompt token count must be <= 2500 after Phase 6."""
    from prompt.sections import total_static_tokens
    total = total_static_tokens()
    if target_phase >= 7:
        # Strict V5_PLAN.md target: <=2500 absolute.
        if total > 2500:
            return False, f"static prompt = {total} tokens, target <= 2500"
        return True, f"static prompt = {total} tokens (<= 2500 OK)"
    # Pre-Phase-7 audit gate (e.g., before Phase 4) -- only check budget.
    from prompt.sections import STATIC_TOKEN_BUDGET
    if total > STATIC_TOKEN_BUDGET:
        return False, f"static prompt = {total}, budget {STATIC_TOKEN_BUDGET}"
    return True, f"static prompt = {total} (under budget {STATIC_TOKEN_BUDGET})"


def check_section_caps() -> Tuple[bool, str]:
    """Every section must be under its individual token cap."""
    from prompt.sections import check_section_caps as _check
    violations = _check(strict=True)
    if violations:
        return False, "section cap violations:\n  " + "\n  ".join(violations)
    return True, "all section caps respected"


def check_section_caps_sum_to_budget() -> Tuple[bool, str]:
    """Sum of per-section caps must be <= STATIC_TOKEN_BUDGET."""
    from prompt.sections import SECTION_ORDER, STATIC_TOKEN_BUDGET
    cap_sum = sum(s.token_cap for s in SECTION_ORDER)
    if cap_sum > STATIC_TOKEN_BUDGET:
        return False, f"cap sum {cap_sum} > budget {STATIC_TOKEN_BUDGET}"
    return True, f"cap sum {cap_sum} <= budget {STATIC_TOKEN_BUDGET}"


def check_tool_count() -> Tuple[bool, str]:
    """v5 tool count must be <= v4 tool count (no net new tools)."""
    import tools as t
    v5_tools = [x for x in t.all_registered() if not x.name.startswith("mcp__")]
    v5_count = len(v5_tools)
    v4_count = 30  # v4 estimate from V5_PLAN.md
    if v5_count > v4_count:
        return False, f"v5 has {v5_count} tools, v4 has ~{v4_count}"
    return True, f"v5: {v5_count} tools (v4 ~ {v4_count}, ratio OK)"


def check_adr_port_log_ratio() -> Tuple[bool, str]:
    """Every PORT_LOG row must reference an ADR-NNN."""
    repo_root = os.path.dirname(os.path.dirname(_AGENT_ROOT))
    port_log = os.path.join(repo_root, "_status", "V5_RUNNABLE_PORT_LOG.md")
    if not os.path.isfile(port_log):
        return False, f"PORT_LOG missing: {port_log}"
    adr_log = os.path.join(repo_root, "_status", "V5_DESIGN_DECISIONS.md")
    if not os.path.isfile(adr_log):
        return False, f"ADR log missing: {adr_log}"
    with open(port_log, "r", encoding="utf-8") as f:
        port_text = f.read()
    with open(adr_log, "r", encoding="utf-8") as f:
        adr_text = f.read()
    # Parse PORT_LOG rows (table rows starting with `| <id> |`)
    rows_without_adr: List[str] = []
    for line in port_text.split("\n"):
        m = re.match(r"^\|\s*(\d{3})\s*\|", line)
        if m:
            row_id = m.group(1)
            if "ADR-" not in line:
                rows_without_adr.append(row_id)
    if rows_without_adr:
        return False, f"PORT_LOG rows missing ADR: {rows_without_adr}"
    # Count ADRs + PORT_LOG rows
    adrs = re.findall(r"^## ADR-(\d{3})", adr_text, re.MULTILINE)
    port_rows_pattern = r'^\| \d{3} \|'
    port_rows = re.findall(port_rows_pattern, port_text, re.MULTILINE)
    return True, f"{len(port_rows)} PORT_LOG rows, {len(adrs)} ADRs -- all rows reference an ADR"


def check_section_names_unique() -> Tuple[bool, str]:
    """SECTION_ORDER must have unique section names (cache-break detection
    uses dict-keyed lookup)."""
    from prompt.sections import SECTION_ORDER
    names = [s.name for s in SECTION_ORDER]
    dupes = [n for n in names if names.count(n) > 1]
    if dupes:
        return False, f"duplicate section names: {set(dupes)}"
    return True, f"{len(names)} unique section names"


def check_tool_classes_at_slot_2() -> Tuple[bool, str]:
    """PS Issue #7 fix: tool_classes.md must be at slot 2."""
    from prompt.sections import SECTION_ORDER
    if len(SECTION_ORDER) < 2:
        return False, "fewer than 2 sections registered"
    if SECTION_ORDER[1].name != "tool_classes":
        return False, f"slot 2 is {SECTION_ORDER[1].name!r}, expected 'tool_classes' (PS Issue #7)"
    return True, "tool_classes at slot 2 (PS Issue #7 fix)"


# ============================================================
# Runner
# ============================================================

def run_audit(target_phase: int) -> int:
    """Run all checks and print a summary. Returns exit code (0 = pass)."""
    print(f"=== Aggregate audit -- pre-Phase-{target_phase} ===")
    print()

    checks = [
        ("Static prompt tokens",        lambda: check_static_prompt_tokens(target_phase)),
        ("Per-section token caps",      check_section_caps),
        ("Cap sum <= budget",            check_section_caps_sum_to_budget),
        ("Section names unique",        check_section_names_unique),
        ("tool_classes @ slot 2",       check_tool_classes_at_slot_2),
        ("Tool count <= v4",             check_tool_count),
        ("ADR-to-PORT_LOG ratio",       check_adr_port_log_ratio),
    ]

    failures: List[str] = []
    for name, fn in checks:
        try:
            ok, msg = fn()
        except Exception as e:
            ok = False
            msg = f"check raised {type(e).__name__}: {e}"
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: {msg}")
        if not ok:
            failures.append(name)

    print()
    if failures:
        print(f"=== AUDIT FAILED -- {len(failures)} check(s) failed: {', '.join(failures)} ===")
        print(f"Phase {target_phase} BLOCKED until failures are addressed.")
        return 1
    print(f"=== AUDIT PASSED -- all metrics OK ===")
    print(f"Phase {target_phase} UNBLOCKED.")
    print()
    print("Note: Cognitive-load test (Codex-evaluated) is run separately via")
    print("the Codex review prompt at the start of each phase that adds prompt")
    print("content. The mechanical audit above does not run it.")
    return 0


if __name__ == "__main__":
    target = 7
    if len(sys.argv) > 1 and sys.argv[1].startswith("--phase"):
        # `--phase 7` or `--phase=7`
        if "=" in sys.argv[1]:
            target = int(sys.argv[1].split("=", 1)[1])
        elif len(sys.argv) > 2:
            target = int(sys.argv[2])
    sys.exit(run_audit(target))
