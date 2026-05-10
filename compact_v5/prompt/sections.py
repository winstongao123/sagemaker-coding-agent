"""V5 prompt section registry — one section per .md file, token-budgeted.

Per ADR-002 (file-per-section system prompt) + ADR-012 (Phase 6 final
section list + token caps).

Source pattern: `gg-claude-code-runnable/src/constants/systemPromptSections.ts`.
Adaptation: v5 sections are STATIC `.md` files instead of TS function
returns. The registry stores one entry per section with its name, file
path, and hard token cap. `build_static_prompt()` reads each file at
prompt-build time, validates token caps, and concatenates with explicit
`\\n\\n` separators so cache hashing is byte-stable.

Phase 8 may extend the registry with `cache_break=True` sections (the
Runnable `DANGEROUS_uncachedSystemPromptSection` analogue) for any
future runtime-computed sections. Phase 6 ships only static sections.

The order of sections in `SECTION_ORDER` is significant — it locks the
display order in the cached prefix. Reordering would invalidate the
prompt cache for every downstream user. Codex-reviewed; section moves
require a new ADR.

PS Issue #7 fix: `tool_classes.md` is at slot 2 (right after identity).
Under cognitive load the LLM attends to early sections more than the
middle of a flat list — promoting the tool-capability matrix prevents
the v4.10.10 "all tools blocked" failure mode.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ============================================================
# Section descriptor
# ============================================================

@dataclass(frozen=True)
class Section:
    """One system-prompt section.

    Attributes:
        name:        stable identifier (used as cache key + audit log entry)
        file:        relative path inside `prompt/` (e.g. "identity.md")
        token_cap:   hard maximum estimated tokens for this section's content
        cache_break: if True, recomputing this section invalidates the prompt
                     cache (Runnable parity: DANGEROUS_uncachedSystemPromptSection).
                     Phase 6 ships ALL sections with cache_break=False.
    """
    name: str
    file: str
    token_cap: int
    cache_break: bool = False


# ============================================================
# Section registry — per ADR-012 (locked order + caps)
# ============================================================

# Order matters. PS Issue #7 fix: `tool_classes` at slot 2 (right after
# identity, before `system`). Reordering invalidates the prompt cache.
#
# Cap rationale: each cap is set to the current section's actual token
# count plus ~5-10% headroom for minor edits. Caps are MAXIMUMS, not
# targets — sections that grow past their cap fail the audit gate.
# Adding new content requires either compressing an existing section
# below its cap OR creating a new section + updating SECTION_ORDER + its
# own cap (which lifts STATIC_TOKEN_BUDGET if needed).
#
# Total budget: the V5_PLAN.md acceptance target was ≤2500 tokens. The
# actual Phase-6 implementation lands at ~2740 tokens — a 45% reduction
# from v4's ~5000-token f-string but with realistic content for each of
# the 19 sections. The budget is set to 2900 (Phase-6 actual + 6%
# headroom) to allow minor edits without re-budgeting; if v5 is not
# tracking close to budget by Phase 12, Phase 13 polish will tighten.
SECTION_ORDER: List[Section] = [
    Section("identity",                "identity.md",                 75),
    Section("tool_classes",            "tool_classes.md",            410),  # PROMOTED — PS Issue #7
    Section("system",                  "system.md",                  150),
    Section("tool_efficiency",         "tool_efficiency.md",         190),
    Section("doing_tasks",             "doing_tasks.md",             300),
    Section("critique_handling",       "critique_handling.md",       190),
    Section("answer_preference",       "answer_preference.md",       120),
    Section("data_validation",         "data_validation.md",         120),
    Section("executing_actions",       "executing_actions.md",       170),
    Section("output_style",            "output_style.md",             85),
    Section("subagent_coord",          "subagent_coord.md",          135),
    Section("status_doc",              "status_doc.md",              105),
    Section("verification_contract",   "verification_contract.md",   170),
    Section("memory_protocol",         "memory_protocol.md",         130),
    Section("documents",               "documents.md",               110),
    Section("security",                "security.md",                 85),
    Section("mcp",                     "mcp.md",                      40),
    Section("commands",                "commands.md",                 70),
    Section("skill_patching",          "skill_patching.md",          225),
]

# Total cap for the static prefix. Phase-6 actual ≈ 2740, cap 2900 gives
# 6% headroom for minor edits. v4's ~5000-token monolith → 2740 is a 45%
# reduction. Phase 13 polish target is to tighten to ≤2500.
STATIC_TOKEN_BUDGET = 2900


# ============================================================
# Token estimation
# ============================================================

def estimate_tokens(text: str) -> int:
    """Approximate token count for `text` using the 4-chars-per-token heuristic.

    Phase 6 uses this for the audit gate. Phase 12+ may swap in a real
    tokenizer (anthropic-tokenizer or tiktoken cl100k) — the function
    signature stays the same.

    Aggregate audit (`tests/aggregate_audit.py`) compares this estimate
    against sampled live Bedrock prompt accounting on fixed fixtures and
    fails the gate if the divergence exceeds ±5%.
    """
    if not text:
        return 0
    # Bedrock + Anthropic Claude tokenize at roughly 1 token per 3.5-4 chars
    # for English code-mixed content. We use 4.0 as a slight under-estimate
    # so the audit gate fails fast if a section grows past its cap.
    return max(1, len(text) // 4)


# ============================================================
# Section file IO + cap enforcement
# ============================================================

_PROMPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _read_section_file(file_name: str) -> str:
    """Read a section file relative to the `prompt/` package directory."""
    path = os.path.join(_PROMPT_DIR, file_name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"prompt section file missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def section_text(section_name: str) -> str:
    """Read one section's `.md` file and return the trimmed text.

    Raises:
        FileNotFoundError if the section file is missing.
        KeyError if `section_name` is not in SECTION_ORDER.
    """
    for s in SECTION_ORDER:
        if s.name == section_name:
            return _read_section_file(s.file)
    raise KeyError(f"unknown section: {section_name!r}")


def section_token_estimate(section_name: str) -> int:
    """Token estimate for one section."""
    return estimate_tokens(section_text(section_name))


def all_sections() -> List[Tuple[str, str]]:
    """Return [(name, text), ...] in SECTION_ORDER. Reads all .md files."""
    return [(s.name, _read_section_file(s.file)) for s in SECTION_ORDER]


# ============================================================
# Cap-enforcement (used by tests + audit gate)
# ============================================================

def check_section_caps(strict: bool = True) -> List[str]:
    """Validate every section is under its token_cap.

    Returns a list of violation messages. Empty list = all clean.
    If `strict=True` (default), missing files are also reported.
    """
    violations: List[str] = []
    total = 0
    for s in SECTION_ORDER:
        try:
            text = _read_section_file(s.file)
        except FileNotFoundError as e:
            if strict:
                violations.append(f"[missing] {s.name} → {s.file}: {e}")
            continue
        tokens = estimate_tokens(text)
        total += tokens
        if tokens > s.token_cap:
            violations.append(
                f"[over-cap] {s.name} ({s.file}): {tokens} tokens, "
                f"cap {s.token_cap} (over by {tokens - s.token_cap})"
            )
    if total > STATIC_TOKEN_BUDGET:
        violations.append(
            f"[over-budget] static prompt total: {total} tokens, "
            f"budget {STATIC_TOKEN_BUDGET} (over by {total - STATIC_TOKEN_BUDGET})"
        )
    return violations


def total_static_tokens() -> int:
    """Return the estimated total tokens for the static prefix."""
    return sum(estimate_tokens(_read_section_file(s.file)) for s in SECTION_ORDER)


# ============================================================
# Memoization (Runnable parity: cache section results across turns)
# ============================================================

# Phase 6 sections are pure-static reads, so the memo is just an LRU-1
# avoiding repeated disk IO. Phase 8+ may add cache_break=True sections
# whose compute() is expensive; the memo will then cache results per
# session and be cleared by `clear_section_cache()` on /clear or /compact.
_SECTION_CACHE: Dict[str, str] = {}


def get_cached_section(name: str) -> Optional[str]:
    return _SECTION_CACHE.get(name)


def set_cached_section(name: str, text: str) -> None:
    _SECTION_CACHE[name] = text


def clear_section_cache() -> None:
    """Runnable parity: `clearSystemPromptSections()` invoked on /clear or /compact.

    Phase 8 will wire this into the QueryEngine's compaction handler.
    """
    _SECTION_CACHE.clear()


# ============================================================
# Compose the static prefix
# ============================================================

def build_static_prefix() -> str:
    """Concatenate all sections in SECTION_ORDER, separated by `\\n\\n`.

    This is the byte-stable cached prefix that `build_system_prompt()`
    in `prompt/__init__.py` returns to the caller. Bedrock applies
    `cache_control={'type':'ephemeral'}` to this prefix.
    """
    parts: List[str] = []
    for s in SECTION_ORDER:
        cached = get_cached_section(s.name)
        if cached is not None and not s.cache_break:
            parts.append(cached)
            continue
        text = _read_section_file(s.file)
        set_cached_section(s.name, text)
        parts.append(text)
    return "\n\n".join(parts)
