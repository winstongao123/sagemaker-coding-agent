"""Phase 06 unit tests: prompt/ package assembly + token budget.

Locks the contract for ADR-002 + ADR-012:
- 19 file-per-section .md files exist
- Each section is under its individual token_cap
- Total static prefix is under STATIC_TOKEN_BUDGET (2900)
- Total is significantly below v4's ~5000-token monolith (≥40% reduction)
- `tool_classes` is at slot 2 (PS Issue #7 promotion fix)
- Cache-boundary marker is present in build_system_prompt output
- BedrockClient cache-block split logic works on the assembled prompt
- Memoization (clear_section_cache) works
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Section files exist + are non-empty
# ============================================================

def test_all_section_files_exist():
    from prompt.sections import SECTION_ORDER, _PROMPT_DIR
    for s in SECTION_ORDER:
        path = os.path.join(_PROMPT_DIR, s.file)
        assert os.path.isfile(path), f"missing section file: {path}"


def test_all_sections_have_non_empty_content():
    from prompt.sections import SECTION_ORDER, section_text
    for s in SECTION_ORDER:
        text = section_text(s.name)
        assert text.strip(), f"section {s.name} is empty"


def test_cache_boundary_marker_file_exists():
    from prompt import _read_boundary_file, CACHE_BOUNDARY, CACHE_BOUNDARY_MARKER
    body = _read_boundary_file()
    # The marker line itself (without surrounding newlines) must appear
    assert "# === DYNAMIC ===" in body
    # The exported constant matches v4's BedrockClient split string EXACTLY
    # (no trailing newline). Codex Phase-06 finding 3 fix: single source of truth.
    assert CACHE_BOUNDARY == "\n\n# === DYNAMIC ==="
    assert CACHE_BOUNDARY_MARKER == CACHE_BOUNDARY  # legacy alias same value


# ============================================================
# Token budget — V5_PLAN.md Phase 6 acceptance criterion
# ============================================================

def test_no_section_over_individual_cap():
    from prompt.sections import check_section_caps
    violations = check_section_caps(strict=True)
    assert violations == [], (
        "Phase 6 token-cap audit failed:\n  " + "\n  ".join(violations)
    )


def test_total_static_prompt_under_budget():
    from prompt.sections import total_static_tokens, STATIC_TOKEN_BUDGET
    total = total_static_tokens()
    assert total <= STATIC_TOKEN_BUDGET, (
        f"static prompt exceeds budget: {total} > {STATIC_TOKEN_BUDGET}"
    )


def test_static_prompt_significantly_smaller_than_v4():
    """v4's SYSTEM_PROMPT was estimated at ~5000 tokens. v5 must be at
    least 40% smaller (≤3000 tokens) — the structural fix for PS Issue #7."""
    from prompt.sections import total_static_tokens
    total = total_static_tokens()
    # v4 estimated 5000; require ≥40% reduction (≤3000).
    v4_estimate = 5000
    reduction_pct = 100 * (v4_estimate - total) / v4_estimate
    assert reduction_pct >= 40, (
        f"v5 reduction {reduction_pct:.0f}% (v5={total}, v4≈{v4_estimate}); "
        f"target ≥40%."
    )


# ============================================================
# PS Issue #7 — tool_classes promotion lock test
# ============================================================

def test_tool_classes_section_at_slot_2():
    """The buried-matrix failure mode is structurally fixed by promoting
    `tool_classes` to slot 2 (right after `identity`). This test locks
    that ordering — any reorder fails the test, forcing a re-evaluation."""
    from prompt.sections import SECTION_ORDER
    assert SECTION_ORDER[0].name == "identity"
    assert SECTION_ORDER[1].name == "tool_classes", (
        f"PS Issue #7 fix requires tool_classes at slot 2; got "
        f"{SECTION_ORDER[1].name!r} (full order: "
        f"{[s.name for s in SECTION_ORDER[:5]]})"
    )


# ============================================================
# Cache-boundary placement
# ============================================================

def test_build_system_prompt_includes_marker():
    from prompt import build_system_prompt
    prompt = build_system_prompt()
    assert "# === DYNAMIC ===" in prompt


def test_build_system_prompt_static_prefix_first():
    """The cached prefix must come BEFORE the boundary marker."""
    from prompt import build_system_prompt
    prompt = build_system_prompt()
    boundary_idx = prompt.index("# === DYNAMIC ===")
    # identity is the first section
    identity_idx = prompt.index("You are SageMaker Coding Agent")
    assert identity_idx < boundary_idx


def test_build_system_prompt_with_dynamic_blocks():
    """Phase-8 integration: build_system_prompt accepts dynamic blocks
    that get joined after the boundary."""
    from prompt import build_system_prompt
    prompt = build_system_prompt({"dynamic_blocks": ["[TODO RESTORATION]\n- task 1\n- task 2"]})
    boundary_idx = prompt.index("# === DYNAMIC ===")
    todo_idx = prompt.index("[TODO RESTORATION]")
    assert boundary_idx < todo_idx


# ============================================================
# Cache-block builder — Phase 1 BedrockClient parity
# ============================================================

def test_build_cache_blocks_splits_on_marker():
    from core.cache import build_cache_blocks
    prompt = "STATIC PART\n\n# === DYNAMIC ===\nDYNAMIC PART"
    blocks = build_cache_blocks(prompt)
    assert len(blocks) == 2
    assert blocks[0].cache_control is True
    assert "STATIC PART" in blocks[0].text
    assert blocks[1].cache_control is False
    assert "DYNAMIC PART" in blocks[1].text


def test_build_cache_blocks_no_dynamic_after_boundary():
    """Marker present but dynamic part is empty → single cached block."""
    from core.cache import build_cache_blocks
    prompt = "STATIC PART\n\n# === DYNAMIC ==="
    blocks = build_cache_blocks(prompt)
    assert len(blocks) == 1
    assert blocks[0].cache_control is True


def test_build_cache_blocks_no_marker_caches_whole_prompt():
    from core.cache import build_cache_blocks
    blocks = build_cache_blocks("just a single block, no marker")
    assert len(blocks) == 1
    assert blocks[0].cache_control is True


def test_build_cache_blocks_to_bedrock_format():
    """After Codex Phase-06 finding 2 fix, build_cache_blocks preserves
    the dynamic part EXACTLY (including the leading `\\n` after the marker)
    so that the direct-block path is byte-equivalent to runtime/bedrock_client.py.
    """
    from core.cache import build_cache_blocks
    blocks = build_cache_blocks("STATIC\n\n# === DYNAMIC ===\nDYN")
    bedrock = [b.to_bedrock() for b in blocks]
    assert bedrock[0] == {"type": "text", "text": "STATIC", "cache_control": {"type": "ephemeral"}}
    # Dynamic part includes the leading `\n` (preserved verbatim, no lstrip)
    assert bedrock[1] == {"type": "text", "text": "\nDYN"}


# ============================================================
# Memoization
# ============================================================

def test_section_cache_memoizes_disk_reads():
    from prompt.sections import (
        clear_section_cache, get_cached_section, set_cached_section,
        section_text, build_static_prefix,
    )
    clear_section_cache()
    # First call populates cache as it reads each file.
    _ = build_static_prefix()
    # After build, the cache should hold every section.
    assert get_cached_section("identity") is not None
    assert get_cached_section("tool_classes") is not None


def test_clear_section_cache_empties_memo():
    from prompt.sections import clear_section_cache, set_cached_section, get_cached_section
    set_cached_section("test_section", "test content")
    assert get_cached_section("test_section") == "test content"
    clear_section_cache()
    assert get_cached_section("test_section") is None


# ============================================================
# Codex Phase-06 review fixes — lock tests
# ============================================================

def test_section_caps_sum_to_static_token_budget():
    """Codex Phase-06 finding 1 lock: the sum of individual section
    token caps must NOT exceed STATIC_TOKEN_BUDGET. If a section grows
    near its cap, the aggregate could otherwise still bust the budget."""
    from prompt.sections import SECTION_ORDER, STATIC_TOKEN_BUDGET
    cap_sum = sum(s.token_cap for s in SECTION_ORDER)
    assert cap_sum <= STATIC_TOKEN_BUDGET, (
        f"Sum of section caps ({cap_sum}) exceeds STATIC_TOKEN_BUDGET "
        f"({STATIC_TOKEN_BUDGET}). 'All sections under cap' could still "
        f"bust the budget. Tighten per-section caps or lift the budget."
    )


def test_section_names_are_unique():
    """Codex Phase-06 finding 4 lock: detect_cache_break uses dict
    lookup keyed by section name; duplicate names would silently
    collapse. Lock the uniqueness invariant."""
    from prompt.sections import SECTION_ORDER
    names = [s.name for s in SECTION_ORDER]
    assert len(names) == len(set(names)), (
        f"SECTION_ORDER contains duplicate names: {names}. "
        f"Each section name must be unique for cache-break detection."
    )


def test_boundary_constants_match_across_modules():
    """Codex Phase-06 finding 3 lock: the cache-boundary string MUST be
    byte-identical across `prompt`, `core.cache`, and the literal in
    `runtime/bedrock_client.py`. Mismatches silently break cache-block
    parity between the runtime path and the direct-block path."""
    from prompt import CACHE_BOUNDARY as prompt_boundary
    from core.cache import CACHE_BOUNDARY_MARKER as cache_boundary

    # Both core.cache and prompt resolve to the same literal value.
    assert prompt_boundary == cache_boundary
    # The literal in runtime/bedrock_client.py must also match. Read the
    # source file and parse out the literal so this test catches any
    # accidental drift in the Phase-1 constant.
    import os as _os
    _agent_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    bedrock_path = _os.path.join(_agent_root, "runtime", "bedrock_client.py")
    with open(bedrock_path, "r", encoding="utf-8") as f:
        bedrock_src = f.read()
    # The Phase-1 literal: `_CACHE_BOUNDARY = "\n\n# === DYNAMIC ==="`
    assert '_CACHE_BOUNDARY = "\\n\\n# === DYNAMIC ==="' in bedrock_src, (
        "Phase-1 BedrockClient literal must match the canonical "
        "CACHE_BOUNDARY constant (no trailing newline)."
    )


def test_build_cache_blocks_dynamic_part_is_byte_equivalent():
    """Codex Phase-06 finding 2 lock: build_cache_blocks must preserve
    the dynamic part EXACTLY (no lstrip), matching what
    runtime/bedrock_client.py:_build_system_field would emit."""
    from core.cache import build_cache_blocks, CACHE_BOUNDARY_MARKER
    # Dynamic part with intentional leading newline + content
    prompt = f"STATIC{CACHE_BOUNDARY_MARKER}\nDYNAMIC line 1\nDYNAMIC line 2"
    blocks = build_cache_blocks(prompt)
    assert len(blocks) == 2
    # The dynamic block must start with \n (preserving the byte after the marker)
    assert blocks[1].text.startswith("\n"), (
        f"dynamic_part should preserve leading newline; got "
        f"{blocks[1].text[:20]!r}"
    )
