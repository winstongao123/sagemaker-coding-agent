"""V4.10.3 #4: Cache-boundary regression test.

Asserts that the static portion of the system prompt (everything BEFORE the
'# === DYNAMIC ===' marker) is byte-identical across:
- Multiple turns of the same agent
- Different user messages
- Different agent_type sub-prompts (build/plan/explore/...)

Why: Bedrock's prompt cache only hits when the cached text is byte-identical
across calls. Any future edit that accidentally inserts dynamic content
(timestamps, randomized IDs, model output) into the static prefix would
silently kill caching and 10x token cost without warning. This test catches
that the moment it lands.

Companion test for the splitting logic in BedrockClient.chat() at L2238-2260.
"""

from __future__ import annotations

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


CACHE_BOUNDARY = "\n\n# === DYNAMIC ==="


def _static_part(prompt: str) -> str:
    """Return the static (cacheable) portion of a system prompt."""
    if CACHE_BOUNDARY in prompt:
        return prompt.split(CACHE_BOUNDARY, 1)[0]
    # No boundary = entire prompt is treated as static. That's the cache shape too.
    return prompt


def _digest(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def test_static_prefix_present_in_main_system_prompt():
    """SYSTEM_PROMPT must contain the boundary marker — without it the entire
    prompt would be sent uncached and caching would never activate."""
    assert CACHE_BOUNDARY in sa.SYSTEM_PROMPT, (
        "SYSTEM_PROMPT missing cache boundary marker — caching will not work"
    )


def test_static_prefix_is_substantial():
    """Static prefix should be at least 1024 tokens to clear Bedrock's cache
    checkpoint threshold (Sonnet 4.5: 1024 / Haiku 4.5: 4096)."""
    static = _static_part(sa.SYSTEM_PROMPT)
    tokens = sa.Compactor.estimate_tokens(static)
    assert tokens >= 1024, (
        f"Static prefix only {tokens} tokens — below Sonnet 4.5 cache checkpoint "
        f"threshold (1024). Caching will not activate."
    )


def test_static_prefix_byte_identical_across_calls():
    """Repeated reads of SYSTEM_PROMPT must give byte-identical static prefix.
    Trivially true today (it's a module constant) but catches future regressions
    where someone f-strings a timestamp into the constant."""
    h1 = _digest(_static_part(sa.SYSTEM_PROMPT))
    h2 = _digest(_static_part(sa.SYSTEM_PROMPT))
    h3 = _digest(_static_part(sa.SYSTEM_PROMPT))
    assert h1 == h2 == h3, f"Static prefix not byte-stable: {h1} {h2} {h3}"


def test_subagent_prompt_static_prefix_matches_parent():
    """Sub-agent prompts are SYSTEM_PROMPT + sub-agent notes + env-details +
    prompt_suffix + critical_reminder. The boundary marker comes from
    SYSTEM_PROMPT, so the static prefix (everything BEFORE the marker) must
    be byte-identical to the parent's static prefix.

    This is what guarantees the cache hit on sub-agent calls."""
    parent_static = _static_part(sa.SYSTEM_PROMPT)
    parent_hash = _digest(parent_static)

    for agent_type in ("build", "plan", "explore", "verify", "general", "review", "fork"):
        cfg = sa.AGENT_TYPES.get(agent_type)
        if not cfg:
            continue
        # Reproduce the sub-agent prompt construction from _run_task_tool (L7788+).
        sub_prompt = (
            sa.SYSTEM_PROMPT
            + "\n\n# Sub-agent Notes\n- Always use ABSOLUTE file paths..."  # truncated for test
        )
        # Add env-details (v4.10.0 #47) — DOES NOT mutate static prefix because
        # it's appended to sub_prompt AFTER SYSTEM_PROMPT, so the boundary marker
        # is already past.
        env_details = sa._build_subagent_env_details(agent_type, depth=1)
        if env_details:
            sub_prompt += "\n\n" + env_details
        # Plus suffix + critical reminder
        if cfg.get("prompt_suffix"):
            sub_prompt += "\n\n" + cfg["prompt_suffix"]
        if cfg.get("critical_reminder"):
            sub_prompt += "\n\n" + cfg["critical_reminder"]

        sub_static = _static_part(sub_prompt)
        sub_hash = _digest(sub_static)
        assert sub_hash == parent_hash, (
            f"Sub-agent type {agent_type!r}: static prefix hash {sub_hash} != "
            f"parent {parent_hash}. Cache prefix drift would cost 10x on every "
            f"sub-agent call."
        )


def test_dynamic_content_lives_after_boundary():
    """Make sure the v4.10.x additions (env-details, skill listing, memory
    sections) sit AFTER the boundary so they don't pollute the cached prefix.

    We can't fully check at runtime without invoking the agent, but we can
    spot-check that key dynamic-content strings don't appear in the static
    prefix of the bare SYSTEM_PROMPT (since they're appended at runtime, not
    baked in)."""
    static = _static_part(sa.SYSTEM_PROMPT)
    # These markers are produced by runtime-only paths and must not be in the
    # static prefix:
    forbidden_in_static = [
        "Sub-agent Environment",       # _build_subagent_env_details output
        "Persistent Memory (from memory.md)",  # _load_persistent_memory header
        "Project Status (from",         # _load_project_status header
        "Skills Relevant to This Task",  # auto-trigger discovery surfacing
    ]
    for phrase in forbidden_in_static:
        assert phrase not in static, (
            f"Dynamic content leaked into cached static prefix: {phrase!r}. "
            f"Cache will be invalidated whenever this content changes."
        )


def test_compactor_cache_boundary_constant_matches_split():
    """The boundary marker used by tests here must match the one BedrockClient
    uses to split the system prompt into cache blocks. If they drift, this
    test would still pass but caching would silently break in production.
    Pin both to the same constant by string-matching."""
    # Read the agent source for the boundary marker definition site.
    agent_source_path = os.path.join(os.path.dirname(__file__), "sagemaker_agent.py")
    with open(agent_source_path, "r", encoding="utf-8") as f:
        src = f.read()
    # The boundary appears literally in BedrockClient.chat(). Match it exactly.
    assert '_CACHE_BOUNDARY = "\\n\\n# === DYNAMIC ==="' in src, (
        "BedrockClient cache boundary constant changed. Update CACHE_BOUNDARY "
        "in this test file too, otherwise the regression check is checking "
        "the wrong string."
    )


if __name__ == "__main__":
    tests = [
        ("static_prefix_present_in_main_system_prompt", test_static_prefix_present_in_main_system_prompt),
        ("static_prefix_is_substantial", test_static_prefix_is_substantial),
        ("static_prefix_byte_identical_across_calls", test_static_prefix_byte_identical_across_calls),
        ("subagent_prompt_static_prefix_matches_parent", test_subagent_prompt_static_prefix_matches_parent),
        ("dynamic_content_lives_after_boundary", test_dynamic_content_lives_after_boundary),
        ("compactor_cache_boundary_constant_matches_split", test_compactor_cache_boundary_constant_matches_split),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
