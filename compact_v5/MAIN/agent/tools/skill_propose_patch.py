"""Phase 10 skill_propose_patch tool — opt-in skill self-improvement.

ADAPT port of v4's `tool_skill_propose_patch` executor at
`compact_v4/MAIN/agent/sagemaker_agent.py:6709`. Same 8 safety rails as v4.9.5:

1. Opt-in via `CONFIG.enable_skill_patching=True` (default OFF — tool returns
   no-op message when flipped OFF).
2. Propose-not-apply — patch lands in `skills/<name>/.proposed/<ts>.md`,
   never overwrites live SKILL.md.
3. Diff preview — reviewer sees the proposed body next to the live one
   (Phase 11 UX).
4. Snapshot — applying a proposal snapshots the live file first
   (`runtime/snapshot.py`).
5. Audit log — proposal write + apply both audit-logged.
6. Time-stamped filename — proposals never overwrite each other.
7. Per-skill `.proposed/` dir — proposals can't leak across skills.
8. Require both `reason` and `new_content` — caller must justify and provide
   full body (not a diff).

Marked `should_defer=True` per ADR-016 — extremely low-frequency surface
even when patching is opted in.

PORT_LOG: #027.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import build_tool, register
from .skill import _get_skill_manager


_DESCRIPTION = """Propose an improvement to a skill's SKILL.md (opt-in self-patching, never auto-applies).

REQUIRES: `CONFIG.enable_skill_patching = True`. When the flag is OFF (default), this tool returns a no-op message and does NOT write a proposal. If the user wants self-patching enabled, they must set the config flag explicitly.

When opted in, proposals land in `skills/<name>/.proposed/<ts>.md` for human review. The live SKILL.md is NEVER overwritten by this tool — only the user (via `/skill apply` in Phase 11 UX) can promote a proposal to the live file. The 8 safety rails (opt-in, propose-not-apply, diff preview, snapshot, audit log, time-stamped filenames, per-skill `.proposed/` directory, required reason + full new_content) prevent silent skill drift.

Inputs:
- name        : skill name to propose a patch for (must already be registered).
- reason      : 1-sentence explanation of why this patch helps.
- new_content : the FULL replacement SKILL.md body — NOT a diff.

Use this tool when:
- A skill's instructions caused a specific failure you can articulate.
- The patch makes the skill clearer / safer / more accurate (not just shorter).

Do NOT use this tool to:
- Apply a patch directly — that's a user decision, surfaced via `/skill apply`.
- Patch a skill speculatively without a concrete failure to point to.
- Add experimental rules — propose only what you'd be comfortable defending."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "Skill name to patch (must be registered).",
        },
        "reason": {
            "type": "string",
            "description": "One sentence explaining why this patch helps.",
        },
        "new_content": {
            "type": "string",
            "description": "Full replacement SKILL.md body. Not a diff.",
        },
    },
    "required": ["name", "reason", "new_content"],
}


def _skill_propose_patch_executor(
    args: Dict[str, Any], context: Optional[Dict[str, Any]] = None
) -> str:
    # Codex Phase-10 finding (MEDIUM): respect `CONFIG.enable_skills` gate
    # (parity with v4). If skills are entirely disabled, propose-patch is
    # also a no-op.
    from runtime.config import CONFIG
    if not bool(getattr(CONFIG, "enable_skills", True)):
        return (
            "Skills disabled (CONFIG.enable_skills=False). "
            "skill_propose_patch is a no-op in this session."
        )
    # v4.9.5 contract: opt-in flag gate. When OFF, return a clear no-op
    # message so the model knows to suggest the improvement in chat instead.
    if not bool(getattr(CONFIG, "enable_skill_patching", False)):
        return (
            "Skill patching is OFF (CONFIG.enable_skill_patching=False, default). "
            "No proposal written. "
            "If the user wants to enable: set `CONFIG.enable_skill_patching = True` "
            "and re-issue the call. Otherwise, suggest the improvement in chat."
        )

    name = str(args.get("name", "")).strip()
    reason = str(args.get("reason", "")).strip()
    new_content = args.get("new_content", "")

    if not name:
        return "Error: 'name' is required."
    if not reason:
        return "Error: 'reason' is required (one sentence explaining why this patch helps)."
    if not isinstance(new_content, str) or not new_content.strip():
        return "Error: 'new_content' is required (the full replacement SKILL.md body, not a diff)."

    sm = _get_skill_manager(context)
    ok, payload = sm.propose_patch(name=name, reason=reason, new_content=new_content)
    if not ok:
        return f"Error: {payload}"
    return (
        f"Proposal written to {payload}.\n"
        f"Live SKILL.md NOT modified. "
        f"User must run `/skill apply {name}` (Phase 11 UX) to promote this proposal."
    )


def _register():
    """Idempotent registration. Called by tools/__init__.py:bootstrap_built_ins."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "skill_propose_patch") is not None:
        return
    register(build_tool(
        name="skill_propose_patch",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_skill_propose_patch_executor,
        is_read_only=False,         # writes to .proposed/ when opted in
        is_destructive=False,
        is_concurrency_safe=False,
        requires_approval=False,    # NO approval needed — proposal is itself the approval gate
        should_defer=True,          # extremely low-frequency
        always_load=False,
        search_hint="skill patch propose self-improve self-patching learning loop",
    ))
