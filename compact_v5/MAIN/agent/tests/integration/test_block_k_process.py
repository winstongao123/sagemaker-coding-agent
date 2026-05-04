"""Block K process-discipline locks.

These tests map directly to `SYNTHESIS_MASTER.md:377-390`:

K-1 audit-directory shape
K-2 PORT_LOG Evidence tier column
K-3 changelog-as-postmortem shape
K-4 preflight 5-category gate
K-5 three-critic AXIS A/B/C
K-6 A44 no-change-detector-tests policy
K-7 A39 no-wire-dead-code without E2E
K-8 A41 hermetic test parity
"""
from __future__ import annotations

import re
from pathlib import Path


_THIS_DIR = Path(__file__).resolve().parent
_AGENT_DIR = _THIS_DIR.parent.parent
_MAIN_DIR = _AGENT_DIR.parent
_V5_ROOT = _MAIN_DIR.parent
_REPO_ROOT = _V5_ROOT.parent
_STATUS_DIR = _V5_ROOT / "_status"
_TESTS_ROOT = _AGENT_DIR / "tests"

_SYNTHESIS_POINTER = _V5_ROOT / "_phase_2" / "wave_5_deep" / "00-SYNTHESIS.md"
_AUDIT_README = _V5_ROOT / "docs" / "audits" / "README.md"
_PORT_LOG = _STATUS_DIR / "V5_RUNNABLE_PORT_LOG.md"
_CHANGELOG = _V5_ROOT / "CHANGELOG.md"
_PREFLIGHT = _V5_ROOT / "docs" / "PREFLIGHT_PROTOCOL.md"
_THREE_CRITIC = _V5_ROOT / "docs" / "audits" / "THREE_CRITIC_REVIEW.md"
_AGENTS = _REPO_ROOT / "AGENTS.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8")


def _split_markdown_row(line: str) -> list[str]:
    """Split a markdown table row on unescaped pipe characters."""
    return [part.strip() for part in re.split(r"(?<!\\)\|", line.strip("|"))]


def test_k1_audit_dir_shape_pointer_and_docs():
    pointer = _read(_SYNTHESIS_POINTER)
    readme = _read(_AUDIT_README)

    assert "SYNTHESIS_MASTER.md" in pointer
    assert "optional polish" in pointer
    assert "<date>-<topic>/" in readme
    assert "00-SYNTHESIS.md" in readme
    assert "01-<source-or-critic>_1.md" in readme
    assert "SYNTHESIS_MASTER.md:709-710" in readme


def test_k2_port_log_evidence_tier_column_and_values():
    text = _read(_PORT_LOG)
    header = next(line for line in text.splitlines() if line.startswith("| ID |"))
    columns = _split_markdown_row(header)

    assert "Evidence tier" in columns
    tier_index = columns.index("Evidence tier")
    allowed = {"VERIFIED", "LISTED"}

    rows = [
        _split_markdown_row(line)
        for line in text.splitlines()
        if re.match(r"^\|\s*[0-9A-Z][0-9A-Z-]*\s*\|", line)
        and not line.startswith("| ID |")
    ]
    assert rows, "PORT_LOG has no data rows"
    bad_rows = []
    for row in rows:
        if len(row) != len(columns):
            bad_rows.append((row[0], f"column count {len(row)} != {len(columns)}"))
            continue
        if row[tier_index] not in allowed:
            bad_rows.append((row[0], f"bad Evidence tier {row[tier_index]!r}"))
    assert not bad_rows

    k_rows = {row[0]: row for row in rows if row[0] in {str(n) for n in range(115, 123)}}
    assert set(k_rows) == {str(n) for n in range(115, 123)}
    assert {row[tier_index] for row in k_rows.values()} == {"VERIFIED"}


def test_k3_changelog_postmortem_shape_documented():
    text = _read(_CHANGELOG)
    assert "Changelog Postmortem Entry Shape" in text
    for heading in ("### Symptom", "### Root cause", "### Fix", "### Verification"):
        assert heading in text


def test_k4_preflight_5_category_gate_documented():
    text = _read(_PREFLIGHT)
    for heading in (
        "## 1. Hooks",
        "## 2. Permissions",
        "## 3. Reviewer",
        "## 4. Tree",
        "## 5. Session-State",
    ):
        assert heading in text
    for required in (
        "scope_audit.py --block <BLOCK>",
        "ANTHROPIC_API_KEY",
        "git add -A",
        "CLAUDE_REVIEWER_BASE_PROMPT.md",
    ):
        assert required in text


def test_k5_three_critic_axis_abc_value_timing_cost():
    text = _read(_THREE_CRITIC)
    assert "three separate critic prompts per block" in text
    assert "## AXIS A - Value" in text
    assert "## AXIS B - Timing" in text
    assert "## AXIS C - Cost" in text
    assert "Claude still reconstructs canonical scope" in text


_BAD_CHANGE_DETECTOR_PATTERNS = [
    re.compile(r'assert\s+"[\w_]+"\s+in\s+(?:MODELS|TOOLS|COMMANDS|BEDROCK_MODELS)\b'),
    re.compile(r"assert\s+len\(\s*[A-Z][A-Z_0-9]+\s*\)\s*==\s*\d+"),
    re.compile(r"assert\s+[A-Z][A-Z0-9_]*_COUNT\s*==\s*\d+"),
]
_A44_OPTOUT_MARKER = "# noqa: A44"
_A44_OPTOUT_REASONS = {
    ("test_block_g.py", 78): (
        "Block G AGENT_TYPES keys are explicitly tested above; the count lock "
        "is v4 parity evidence, not a catalog-size detector."
    ),
}


def test_k6_a44_no_change_detector_tests_policy_and_audit():
    agents = _read(_AGENTS)
    assert "A44 - No Change-Detector Tests" in agents
    assert "invariants" in agents
    assert "# noqa: A44" in agents

    findings = []
    for path in _TESTS_ROOT.rglob("test_*.py"):
        if path.name == "test_block_k_process.py":
            continue
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _A44_OPTOUT_MARKER in line:
                assert (path.name, line_no) in _A44_OPTOUT_REASONS
                continue
            if any(pattern.search(line) for pattern in _BAD_CHANGE_DETECTOR_PATTERNS):
                findings.append(f"{path.name}:{line_no}: {line.strip()}")
    assert not findings, "A44 change-detector tests found:\n" + "\n".join(findings)


def test_k7_a39_no_wire_dead_code_without_e2e_policy():
    text = _read(_AGENTS)
    assert "A39 - No Wire-Dead-Code Without E2E Evidence" in text
    assert "not shipped merely because a registry entry" in text
    assert "concrete local lock-test evidence" in text
    assert "N/A_CONSTRAINT" in text


def test_k8_a41_hermetic_test_parity_policy():
    text = _read(_AGENTS)
    assert "A41 - Hermetic Test Parity" in text
    assert "ambient credentials" in text
    assert "host timezone" in text
    assert "locale" in text
    assert "AWS/R-tier behavior stays behind explicit env gates" in text


def test_block_k_8_of_8_test_count():
    expected = {
        "test_k1_audit_dir_shape_pointer_and_docs",
        "test_k2_port_log_evidence_tier_column_and_values",
        "test_k3_changelog_postmortem_shape_documented",
        "test_k4_preflight_5_category_gate_documented",
        "test_k5_three_critic_axis_abc_value_timing_cost",
        "test_k6_a44_no_change_detector_tests_policy_and_audit",
        "test_k7_a39_no_wire_dead_code_without_e2e_policy",
        "test_k8_a41_hermetic_test_parity_policy",
    }
    present = {
        name for name, value in globals().items()
        if name.startswith("test_k") and callable(value)
    }
    assert expected <= present
