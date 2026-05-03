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

_BLOCK_ID_TO_DOC_TOKEN = {
    # Map git-tag block id → the token that should appear in
    # V5_BUILD_STATUS.md "Block <X> status" lines. Most are identity;
    # h-plus and h_plus normalize to "H+" per existing doc convention.
    "h-plus": "H+",
    "g3":     "G3",
    "g2":     "G2",
    "e-f":    "E+F",
    "f2":     "F2",
    "b-plus": "B+",
    "c-plus": "C+",
}


def _block_doc_token(block_id: str) -> str:
    """Return the canonical 'Block <X>' doc token for a git-tag block id."""
    if block_id in _BLOCK_ID_TO_DOC_TOKEN:
        return _BLOCK_ID_TO_DOC_TOKEN[block_id]
    return block_id.upper()


def test_state_resume_anchor_per_block():
    """Every committed `v5.0.1-block-*` tag must have a corresponding
    entry in V5_BUILD_STATUS.md AND the recorded sha must match the
    tag's actual sha.

    This is a STATE-discipline test: it prevents tagging without a
    corresponding status entry AND catches stale `Block X status: DONE
    — tag ... at <sha>; pushed.` lines pointing at the wrong commit.

    Codex Block K iter-1 major #2 fix: the v1 of this test only checked
    loose substrings (e.g. `block t` in any text), which false-passed
    on incidental mentions. v2 parses each `Block <X> status: DONE —
    tag ... at <sha>` line strictly + verifies the sha matches the
    tag's actual sha (per TEST_DESIGN §Block K row 2 "Last commit sha
    matching").
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

    status_text = _BUILD_STATUS.read_text(encoding="utf-8")
    # Parse "Block <TOKEN> status: ... at <SHA>; ..." lines.
    # We accept hyphen-or-plus and digit forms; capture the block-token + sha.
    # Token can be:
    #   - "0"           (Block 0)
    #   - "B" / "C" / "D" / "T" / "J" / "K" / "L" / "M" / "N" / "I" / "G" / "H" / "A"
    #   - "B+" / "C+" / "H+"   (combined tokens)
    #   - "G2" / "G3" / "F2" / "08_5"  (digit suffix tokens)
    #   - "E+F"        (compound)
    status_re = re.compile(
        r"^-?\s*Block\s+(?P<token>[A-Z0-9][A-Z0-9+_]*)\s+status:[^`]*`(?P<tag>v5\.0\.1-block-[a-z0-9_-]+)`\s+at\s+`(?P<sha>[0-9a-f]+)`",
        re.MULTILINE,
    )
    parsed: dict = {}
    for m in status_re.finditer(status_text):
        parsed[m.group("tag")] = (m.group("token"), m.group("sha"))

    findings: list = []
    for tag in tags:
        m = re.match(r"v5\.0\.1-block-(.+)$", tag)
        if not m:
            continue
        block_id = m.group(1).lower()
        expected_token = _block_doc_token(block_id)
        # Check 1: tag has a parsed status row.
        if tag not in parsed:
            # An IN_PROGRESS block (e.g. Block K right now) has no DONE
            # row yet — skip if NO tag exists for it. But here tag DOES
            # exist, so a DONE row is required.
            findings.append((tag, "no DONE row in V5_BUILD_STATUS.md"))
            continue
        token, recorded_sha = parsed[tag]
        # Check 2: token matches expected (case-insensitive — Block convention is upper).
        if token.upper() != expected_token.upper():
            findings.append(
                (tag, f"DONE row token '{token}' != expected '{expected_token}'")
            )
            continue
        # Check 3: recorded sha matches actual tag sha (short prefix tolerance).
        try:
            actual_sha = subprocess.check_output(
                ["git", "rev-parse", tag], cwd=str(_REPO_ROOT), text=True, timeout=5,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue  # can't resolve — don't false-fail
        if not actual_sha.startswith(recorded_sha):
            findings.append(
                (tag, f"recorded sha '{recorded_sha}' != actual '{actual_sha[:12]}'")
            )
    assert not findings, (
        "V5_BUILD_STATUS.md drift detected:\n"
        + "\n".join(f"  {tag}: {msg}" for tag, msg in findings)
        + "\n\nFix: update V5_BUILD_STATUS.md `## Block status` lines to "
        "match actual git tags (token + sha)."
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
    # "X in MODELS / TOOLS / COMMANDS / BEDROCK_MODELS" — surface-string
    # membership check against a hardcoded global list. Narrow regex:
    # only catch checks against the specific globals A44 calls out by
    # name. We do NOT flag `"X" in some_local_list` because that's
    # typically a behavior-derived collection.
    re.compile(r'assert\s+"[\w_]+"\s+in\s+(?:MODELS|TOOLS|COMMANDS|BEDROCK_MODELS)\b'),
    # "len(SOMETHING_UPPERCASE) == N" — count check against an
    # uppercase module-level constant. This IS the change-detector
    # pattern A44 forbids: every additive change requires a test edit.
    re.compile(r'assert\s+len\(\s*[A-Z][A-Z_0-9]+\s*\)\s*==\s*\d+'),
    # "<COUNT_VAR> == N" — explicit count constant check.
    # Codex iter-1 minor #4 fix: was `[A-Z_]+_COUNT` which missed
    # constants with digits like `R13_COUNT` or `BLOCK_5_COUNT`.
    re.compile(r'assert\s+[A-Z][A-Z0-9_]*_COUNT\s*==\s*\d+'),
]

# Per-line A44 opt-out marker. Adding this comment to a single
# `assert ...` line tells the audit "this surface-string assertion
# is intentional v4-baseline-coverage; not a change-detector smell".
# Using a line marker (not a whole-file allowlist) so reviewers can see
# exactly which assertions are exempt and why.
_A44_OPTOUT_MARKER = "# noqa: A44"

# Codex iter-1 major #3 fix: the previous whole-file allowlist hid any
# future bad pattern in those files. Replaced with line-level opt-out
# (above). The mapping below records the JUSTIFICATION for each opt-out
# location so reviewers can audit; the actual exemption is the inline
# comment, not membership in this dict.
_A44_OPTOUT_REASONS = {
    # File:line → reason. Update when a new opt-out is added.
    ("test_block_g.py", 78):
        "Block G AGENT_TYPES keys are explicitly tested above; the "
        "len() check is a redundant lock so the count and the set "
        "stay in sync (Constraint #1 v4 parity for sub-agent types).",
}


def test_a44_no_change_detector_tests_audit():
    """Scan tests/ for "change-detector" patterns and require each
    occurrence to carry a per-line `# noqa: A44` opt-out comment.

    Per A44 (no-change-detector pattern): tests should verify behavior
    invariants, NOT surface strings. Where surface-string assertions
    ARE legitimate (e.g. v4-baseline coverage locks per Constraint #1),
    annotate the specific assertion line with `# noqa: A44` and add
    a justification entry to `_A44_OPTOUT_REASONS`.

    Codex Block K iter-1 major #3 fix: was whole-file allowlist; now
    line-level so reviewers can audit each exempt assertion individually.
    """
    findings: list = []
    for path in _TESTS_ROOT.rglob("test_*.py"):
        # Skip THIS file (meta — the regex patterns themselves contain
        # the patterns we audit for).
        if path.name == "test_block_k_process.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _A44_OPTOUT_MARKER in line:
                continue  # explicit per-line opt-out
            for pat in _BAD_PATTERNS:
                if pat.search(line):
                    findings.append((path.name, line_no, line.strip()))
                    break
    assert not findings, (
        "A44 audit failed — change-detector patterns found without "
        f"`{_A44_OPTOUT_MARKER}` opt-out marker:\n"
        + "\n".join(f"  {n}:{ln}: {s}" for n, ln, s in findings)
        + f"\n\nFix: rewrite as behavior assertion, OR append "
        f"`{_A44_OPTOUT_MARKER}` to that line and add a one-line "
        "justification entry to `_A44_OPTOUT_REASONS` in "
        "test_block_k_process.py (must be a v4-baseline-coverage lock)."
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
