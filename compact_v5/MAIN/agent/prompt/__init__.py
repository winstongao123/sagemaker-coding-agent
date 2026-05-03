"""V5 prompt package — assembles the system prompt from sections.

Per ADR-002 + ADR-012:
  - 19 file-per-section `.md` files (`identity.md`, `tool_classes.md`, ...)
  - `sections.py` — section registry + token-cap enforcement
  - `_CACHE_BOUNDARY.md` — explicit marker matching v4's `# === DYNAMIC ===`
                          line so Phase-1's BedrockClient still splits
                          correctly.

`build_system_prompt(ctx)` returns the assembled prompt as a single
string with the cache-boundary marker between static and dynamic
content. Phase 1's `BedrockClient.chat()` already applies
`cache_control={"type":"ephemeral"}` to the static prefix when the
string contains the marker — Phase 6 just locks the structure.

Phase 6 ships ZERO dynamic sections. The dynamic group is reserved for:
  - todo_restoration (Phase 8 — after auto-compact)
  - file_restoration (Phase 8 — after auto-compact)
  - skill_active (Phase 10 — per-skill auto-trigger content)
  - iteration_budget_status (Phase 8 — current budget)

When the dynamic list is empty (Phase 6 default), the assembled prompt
is just the static prefix + the cache-boundary marker. BedrockClient
then caches the entire static prefix as one block.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .sections import (  # noqa: F401  (public re-exports)
    SECTION_ORDER,
    STATIC_TOKEN_BUDGET,
    Section,
    all_sections,
    build_static_prefix,
    check_section_caps,
    clear_section_cache,
    estimate_tokens,
    section_text,
    section_token_estimate,
    total_static_tokens,
)


# ============================================================
# Cache-boundary marker — SINGLE SOURCE OF TRUTH
# ============================================================
#
# Codex Phase-06 review finding 3 fix: this is the ONLY canonical
# definition of the boundary string. `core/cache.py` imports it.
# `runtime/bedrock_client.py` (Phase 1) keeps a local string literal
# that MUST be byte-equal to this constant; the equality is locked by
# `test_boundary_constants_match_across_modules`.
#
# Format: leading `\n\n` separates the boundary from the preceding
# section's content; the trailing line is intentionally NOT terminated
# with a newline so `prompt.split(CACHE_BOUNDARY, 1)` produces a
# `dynamic_part` that starts EXACTLY where the dynamic content begins
# (a leading `\n` in dynamic_part is preserved verbatim).
CACHE_BOUNDARY = "\n\n# === DYNAMIC ==="

# Backwards-compat alias used by some early Phase-6 callers — keep as
# a simple alias of the canonical name. (The single-source-of-truth
# constant is `CACHE_BOUNDARY`; `CACHE_BOUNDARY_MARKER` was the original
# Phase-6 name. Both refer to the same value.)
CACHE_BOUNDARY_MARKER = CACHE_BOUNDARY


def _read_boundary_file() -> str:
    """Read the boundary file. The marker line `# === DYNAMIC ===` must
    be present somewhere in the body (BedrockClient splits on it)."""
    boundary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_CACHE_BOUNDARY.md")
    if not os.path.isfile(boundary_path):
        raise FileNotFoundError(f"_CACHE_BOUNDARY.md missing at {boundary_path}")
    with open(boundary_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# Public builder
# ============================================================

def build_system_prompt(ctx: Optional[Dict[str, Any]] = None) -> str:
    """Assemble the full system prompt = static prefix + boundary + dynamic.

    Args:
      ctx: optional context dict for dynamic sections. Keys recognised
           Phase 6 (all optional, all empty by default):
             - dynamic_blocks: List[str] of additional dynamic content
                               (e.g., todo_restoration, file_restoration).
                               Phase 8+ will populate these.

    Returns:
      Single string with the static prefix, the cache-boundary marker,
      and any dynamic blocks joined with `\\n\\n`. BedrockClient splits
      on the marker for cache_control placement.
    """
    ctx = ctx or {}
    static = build_static_prefix()
    dynamic_blocks: List[str] = list(ctx.get("dynamic_blocks") or [])

    # Block E+F (PORT_LOG #071, Codex iter-1 finding #1 lock): wire
    # render_env_block into the dynamic tail so every system prompt
    # carries the OS / shell / model-cutoff / cache-stable date block.
    # Best-effort — never break prompt assembly if env_block import
    # fails. ctx["skip_env_block"]=True opts out (used by tests that
    # pin a specific prompt).
    if not ctx.get("skip_env_block"):
        try:
            from prompt.env_block import render_env_block
            env_text = render_env_block(
                workspace=ctx.get("workspace"),
                model_id=ctx.get("model_id"),
            )
            if env_text and env_text not in dynamic_blocks:
                dynamic_blocks.insert(0, env_text)
        except Exception:
            pass

    # Always include the boundary marker even if dynamic_blocks is empty.
    # BedrockClient handles "boundary present, no dynamic content" by caching
    # the full static prefix as one block.
    # CACHE_BOUNDARY already starts with `\n\n` so we concatenate directly
    # rather than join with `"\n\n"` (which would double the leading newlines).
    body = static + CACHE_BOUNDARY
    if dynamic_blocks:
        body += "\n" + "\n\n".join(dynamic_blocks)
    return body


def assert_static_prompt_under_budget() -> None:
    """Raise if the static prefix exceeds STATIC_TOKEN_BUDGET or any
    section exceeds its individual cap. Used by the audit gate
    (`tests/aggregate_audit.py`) before Phase 7."""
    violations = check_section_caps(strict=True)
    if violations:
        raise AssertionError(
            "Phase 6 token-cap audit failed:\n  " + "\n  ".join(violations)
        )
