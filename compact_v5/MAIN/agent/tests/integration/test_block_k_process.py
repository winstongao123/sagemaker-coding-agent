"""Block K — Process discipline (LF AXIS C + per-block user gate +
STATE/RESUME + 3-critic + A44 test refactor).

5 tests per TEST_DESIGN §Block K:
  - test_axis_c_template_present
  - test_state_resume_anchor_per_block
  - test_per_block_user_approval_gate_documented
  - test_a44_no_change_detector_tests_audit
  - test_lint_phase_id

All T4 ($0). Block K ships when 5/5 green.

PORT_LOG: see Block K row.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


# Path resolution.
_THIS_DIR = Path(__file__).resolve().parent  # tests/integration
_AGENT_DIR = _THIS_DIR.parent.parent  # MAIN/agent
_MAIN_DIR = _AGENT_DIR.parent  # MAIN
_V5_ROOT = _MAIN_DIR.parent  # compact_v5
_REPO_ROOT = _V5_ROOT.parent  # sagemaker-coding-agent
_STATUS_DIR = _V5_ROOT / "_status"
_CODEX_TEMPLATE = _STATUS_DIR / "CODEX_REVIEW_TEMPLATE.md"
_RESUME = _STATUS_DIR / "RESUME.md"
_LINT_PHASE_ID = _AGENT_DIR / "tests" / "lint_phase_id.py"
_BUILD_STATUS = _STATUS_DIR / "V5_BUILD_STATUS.md"
_TESTS_ROOT = _AGENT_DIR / "tests"


# ============================================================
# K-1 — AXIS A + B + C in CODEX_REVIEW_TEMPLATE
# ============================================================

def test_axis_c_template_present():
    """`_status/CODEX_REVIEW_TEMPLATE.md` contains AXIS A + AXIS B +
    AXIS C sections.

    Per LF AXIS C requirement (user 2026-05-01): every Codex review
    must cover errors+bugs (A) + Runnable/v5-architecture-fidelity (B)
    + reference-repo coverage gaps (C).
    """
    assert _CODEX_TEMPLATE.is_file(), f"missing {_CODEX_TEMPLATE}"
    text = _CODEX_TEMPLATE.read_text(encoding="utf-8")
    # Must mention all three axes as section headers.
    assert "AXIS A" in text, "CODEX_REVIEW_TEMPLATE.md missing AXIS A section"
    assert "AXIS B" in text, "CODEX_REVIEW_TEMPLATE.md missing AXIS B section"
    assert "AXIS C" in text, "CODEX_REVIEW_TEMPLATE.md missing AXIS C section"
    # AXIS C must specifically reference v4 baseline / coverage gaps.
    assert (
        "Reference-repo coverage" in text or "reference-repo coverage" in text
    ), "AXIS C section must reference reference-repo coverage gaps"
    # The 4 disposition categories from LF must be in AXIS C.
    for cat in ("MUST", "DEFER", "DROP", "N/A"):
        assert cat in text, f"AXIS C must define disposition category '{cat}'"


# ============================================================
# K-2 — STATE/RESUME anchor per Block tag
# ============================================================

def test_state_resume_anchor_per_block():
    """Every committed `v5.0.1-block-*` tag must have a corresponding
    entry in V5_BUILD_STATUS.md.

    Implementation: list git tags matching `v5.0.1-block-*`. For each,
    extract the block id (e.g. `block-t`, `block-j`). Each must appear
    in V5_BUILD_STATUS.md (case-insensitive, hyphen-tolerant).

    This is a STATE-discipline test: it prevents tagging without a
    corresponding status entry.
    """
    if not _BUILD_STATUS.is_file():
        pytest.skip(f"V5_BUILD_STATUS.md missing at {_BUILD_STATUS}")
    try:
        tags_out = subprocess.check_output(
            ["git", "tag", "-l", "v5.0.1-block-*"],
            cwd=str(_REPO_ROOT), text=True, timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        pytest.skip(f"git tag query failed: {exc}")
    tags = [t.strip() for t in tags_out.splitlines() if t.strip()]
    if not tags:
        pytest.skip("no v5.0.1-block-* tags exist yet")

    status_text = _BUILD_STATUS.read_text(encoding="utf-8").lower()
    missing = []
    for tag in tags:
        # tag = "v5.0.1-block-t"  →  block_id = "t"
        m = re.match(r"v5\.0\.1-block-(.+)$", tag)
        if not m:
            continue
        block_id = m.group(1).lower()
        # Look for "Block T" (case-insensitive). The hyphen stays out
        # of the search because we strip it from the id.
        # block-h-plus → "h plus" or "h-plus" — search for either.
        # Simplest: search for "Block <ID>" with hyphen tolerance.
        candidates = [
            f"block {block_id}",
            f"block-{block_id}",
            f"block {block_id.replace('-', ' ')}",
            f"block-{block_id.replace('-', '+')}",  # h-plus → h+
        ]
        # Also try the block-id with `+` for the h-plus naming.
        if block_id.endswith("-plus"):
            candidates.append(f"block {block_id[:-5]}+")
            candidates.append(f"block-{block_id[:-5]}+")
        if not any(c in status_text for c in candidates):
            missing.append((tag, block_id))
    assert not missing, (
        f"V5_BUILD_STATUS.md missing entries for tags: {missing}. "
        f"Each tag needs a 'Block X' section in the status doc."
    )


# ============================================================
# K-3 — Per-Block user approval gate documented in RESUME.md
# ============================================================

def test_per_block_user_approval_gate_documented():
    """`_status/RESUME.md` must explicitly forbid tagging if any
    open Codex finding has severity ≥ CHANGES_REQUESTED.

    Per LF / 3-critic gate model + per-block user-approval discipline.
    """
    assert _RESUME.is_file(), f"missing {_RESUME}"
    text = _RESUME.read_text(encoding="utf-8")
    # The exact phrase TEST_DESIGN §Block K row 3 specifies (loosely
    # — we check a strong pattern, not byte-identical text).
    assert (
        "FORBIDDEN" in text and "CHANGES_REQUESTED" in text
    ), (
        "RESUME.md must contain FORBIDDEN-on-CHANGES_REQUESTED gate "
        "language (per LF / TEST_DESIGN §Block K row 3)."
    )
    # Step 5 must mention the close ritual.
    assert "Step 5" in text, "RESUME.md missing Step 5 (Close the Block)"


# ============================================================
# K-4 — A44 no-change-detector test audit
# ============================================================

# Patterns that indicate a "test detects existence" rather than
# "test enforces a behavior". Per A44 and Codex 3-axis review: tests
# should check INVARIANTS (e.g. behavior-preserving), not surface
# strings (e.g. "tool name X is in the registry list").
#
# Example bad: assert "create_word" in TOOL_NAMES
# Example bad: assert TOOL_COUNT == 25
# Example good: assert call_create_word(args) writes valid .docx
#
# This test scans `tests/` for the bad patterns and reports them.
# It's INFORMATIONAL — failing tests are an audit signal, not an
# automatic block. We allowlist the existing v4-baseline-coverage
# tests (where "X in TOOLS" IS the v4 contract being asserted).

_BAD_PATTERNS = [
    # "X in MODELS / TOOLS / COMMANDS" — surface-string membership check
    # against a hardcoded global list. Very narrow regex: only catch
    # checks against the specific globals the A44 audit names. We do
    # NOT flag `"X" in some_local_list` because that's typically a
    # behavior-derived collection.
    re.compile(r'assert\s+"[\w_]+"\s+in\s+(?:MODELS|TOOLS|COMMANDS|BEDROCK_MODELS)\b'),
    # "X in <ALL_CAPS_GLOBAL>" but NOT when the symbol contains
    # _ALLOWED, _BLOCKED, _PATTERNS, _PREFIXES — those are intentional
    # security/baseline locks. Only catch unannotated all-caps constants.
    # (left aspirational — current pattern below is conservative.)
    # "len(SOMETHING_UPPERCASE) == N" — count check against an
    # uppercase module-level constant. This IS the change-detector
    # pattern A44 forbids: every additive change requires a test edit.
    re.compile(r'assert\s+len\(\s*[A-Z][A-Z_0-9]+\s*\)\s*==\s*\d+'),
    # "<COUNT_VAR> == N" — explicit count constant check.
    re.compile(r'assert\s+[A-Z_]+_COUNT\s*==\s*\d+'),
]

# Allowlist: tests that are LEGITIMATELY checking presence (e.g. v4
# baseline coverage = tool registration locks per Constraint #1).
_ALLOWLIST_FILES = {
    "test_block_t.py",      # Block T checks all 10 active v4 tools register
    "test_block_l.py",      # Block L checks all 18 BedrockErrorCategory members
    "test_block_b.py",      # BEDROCK_EXTRA_PARAMS_HEADERS membership lock
    "test_block_h_plus.py", # /dream MANUAL — locks list of forbidden auto-fire patterns
    "test_block_j_ship_gate.py",  # Block J meta-count test names 7+1 named tests
    "test_block_k_process.py",    # this file — meta about itself
    "test_block_g.py",      # AGENT_TYPES allowlist locks per type
    "test_block_g3.py",     # coordinator-prompt marker locks
    "test_skills.py",       # bundled-skill set lock
    "test_skill_manager.py",# Hermes filter required-tool count locks
    "test_subagent.py",     # shared-budget identity lock
    "test_parity_critical.py",  # v4-parity invariant locks
}


def test_a44_no_change_detector_tests_audit():
    """Scan tests/ for "change-detector" patterns (assert "X" in HARDCODED_LIST,
    assert COUNT == N) and require they live in the allowlist.

    Per A44 (no-change-detector pattern): tests should verify behavior
    invariants, NOT surface strings. Where surface-string assertions
    ARE legitimate (e.g. v4-baseline coverage locks per Constraint #1),
    add the file to `_ALLOWLIST_FILES` with a one-line justification.
    """
    findings: list = []
    for path in _TESTS_ROOT.rglob("test_*.py"):
        if path.name in _ALLOWLIST_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pat in _BAD_PATTERNS:
                if pat.search(line):
                    findings.append((path.name, line_no, line.strip()))
                    break
    assert not findings, (
        "A44 audit failed — change-detector patterns found in non-allowlisted "
        "test files:\n" + "\n".join(f"  {n}:{ln}: {s}" for n, ln, s in findings)
        + "\n\nFix: rewrite as behavior assertion, OR add file to "
        "_ALLOWLIST_FILES in test_block_k_process.py with a one-line "
        "justification (must be a v4-baseline-coverage lock)."
    )


# ============================================================
# K-5 — lint_phase_id.py present + parseable
# ============================================================

def test_lint_phase_id():
    """`tests/lint_phase_id.py` exists, is importable, and exposes
    the expected check structure."""
    assert _LINT_PHASE_ID.is_file(), f"missing {_LINT_PHASE_ID}"
    text = _LINT_PHASE_ID.read_text(encoding="utf-8")
    # The script must run a list of named checks; keep this loose so
    # implementation changes don't break the lock test, but strong
    # enough to ensure the contract.
    for marker in (
        "Phase ID",            # check #1
        "V5_BUILD_STATUS.md",  # check #2
        "Codex review file",   # check #3
        "last commit subject", # check #4
        "tag does not exist",  # check #5
    ):
        assert marker in text, (
            f"lint_phase_id.py missing expected check '{marker}'"
        )
    # Syntactically valid Python (compile check).
    import py_compile
    try:
        py_compile.compile(str(_LINT_PHASE_ID), doraise=True)
    except py_compile.PyCompileError as exc:
        raise AssertionError(f"lint_phase_id.py failed to compile: {exc}")


# ============================================================
# Block K — meta count lock (TEST_DESIGN parity)
# ============================================================

def test_block_k_5_of_5_test_count():
    """Block K ships when 5/5 green per TEST_DESIGN §Block K."""
    expected = [
        "test_axis_c_template_present",
        "test_state_resume_anchor_per_block",
        "test_per_block_user_approval_gate_documented",
        "test_a44_no_change_detector_tests_audit",
        "test_lint_phase_id",
    ]
    import sys as _sys
    mod = _sys.modules[__name__]
    for name in expected:
        assert hasattr(mod, name), f"Block K test '{name}' missing from this module"
