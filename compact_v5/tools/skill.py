"""Phase 10 skill tool — list / activate / read / deactivate (Phase 10, ADR-016).

ADAPT port of v4's `tool_skill` executor. Surface:
- skill list           → returns names + descriptions
- skill read <name>    → returns SKILL.md body (≤12000 chars, v4 cap)
- skill activate <name> → marks the skill active so its body is injected
                          into subsequent system prompts
- skill deactivate     → clears active skill

Uses the SkillManager singleton from `skills/manager.py`.

Marked `should_defer=True` per ADR-016 — skill is low-frequency once
auto-trigger is OFF (default).

PORT_LOG: #026.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import build_tool, register


_DESCRIPTION = """List, activate, read, and deactivate skills.

Skills are reusable methodology bundles (e.g. `verify`, `clara`, `batch`) stored as SKILL.md files. When a skill is "active", its body is injected into the system prompt so the model follows that methodology for the rest of the session.

Subcommands:
- `list`              — show all available skills (name + 1-line description).
- `read <name>`       — read a skill's full SKILL.md body without activating it (for inspection).
- `activate <name>`   — make a skill active. Its body is injected into the system prompt for subsequent turns.
- `deactivate`        — clear the active skill.

Skill auto-trigger is OFF by default. Skills only load when a user runs `/skill activate <name>` (Phase 11 UX) or you call `skill activate <name>` explicitly. v4 made auto-trigger opt-in (`CONFIG.enable_skill_auto_trigger=True`) because silent skill injection bloated cost.

Use the skill tool when:
- The user types `/<skill-name>` or asks "use the X skill".
- The task matches a methodology bundle (e.g. user asks for adversarial verification → activate `verify`).

Do NOT use the skill tool to:
- Re-read every SKILL.md every turn (active skills already inject their body).
- Activate a skill speculatively if you're unsure — ask the user first."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "subcommand": {
            "type": "string",
            "description": "One of: list / read / activate / deactivate.",
        },
        "name": {
            "type": "string",
            "description": "Skill name (required for read / activate; ignored otherwise).",
        },
    },
    "required": ["subcommand"],
}


def _get_skill_manager(context: Optional[Dict[str, Any]]) -> Any:
    """Resolve the SkillManager singleton.

    Priority order:
      1. context['skill_manager'] — explicit injection by query_engine /
         Phase 11 UX. Preferred for testability.
      2. A module-level singleton built lazily from CONFIG. The path mirrors
         v4 which had a process-global SKILLS instance.
    """
    if isinstance(context, dict):
        sm = context.get("skill_manager")
        if sm is not None:
            return sm
    # Lazy-built singleton — matches v4's `SKILLS = SkillManager(...)` shape.
    from skills.manager import SkillManager
    from runtime.config import CONFIG
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = SkillManager(
            workspace=str(CONFIG.workspace),
            skills_dir=getattr(CONFIG, "skills_dir", "./skills"),
            enable_auto_trigger=bool(getattr(CONFIG, "enable_skill_auto_trigger", False)),
        )
    return _SINGLETON


_SINGLETON = None


def _skill_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Execute the skill tool. Always returns a string (never raises)."""
    # Codex Phase-10 finding (MEDIUM): v4 has a `CONFIG.enable_skills` gate
    # so the operator can completely disable skills (e.g. for a constrained
    # SageMaker session). v5 must respect the same gate.
    from runtime.config import CONFIG
    if not bool(getattr(CONFIG, "enable_skills", True)):
        return (
            "Skills disabled (CONFIG.enable_skills=False). "
            "Skill list / read / activate / deactivate are no-ops in this session."
        )

    sub = str(args.get("subcommand", "")).strip().lower()
    if not sub:
        return "Error: subcommand is required (one of: list / read / activate / deactivate)"
    sm = _get_skill_manager(context)

    if sub == "list":
        sm.discover()
        # Block I-2 (Codex iter-1 finding #2 fix): the skill TOOL is the
        # model-facing surface, so it must use list_model_invocable() to
        # hide skills with disable_model_invocation:true. Users still see
        # them via /skill use (commands.py routes through resolve_name()).
        records = sm.list_model_invocable()
        if not records:
            return "(no skills discovered)"
        return "\n".join(
            f"- {r['name']}: {r['description'] or '(no description)'}"
            for r in records
        )

    if sub == "read":
        name = str(args.get("name", "")).strip()
        if not name:
            return "Error: 'name' is required for `read` subcommand"
        # Block I-2 (Codex iter-1 finding #2 fix): reject model-invoked
        # read of disable_model_invocation:true skills. Users can still
        # see the body via /skill use <name> (commands.py path).
        sm.discover()
        skill = sm._cache.get(name)
        if skill is not None and skill.disable_model_invocation:
            return (
                f"Error: skill '{name}' is user-invocable only "
                "(disable_model_invocation: true). The user must run "
                f"`/skill use {name}` directly."
            )
        ok, payload = sm.read_skill(name)
        if not ok:
            return f"Error: {payload}"
        return payload

    if sub == "activate":
        name = str(args.get("name", "")).strip()
        if not name:
            return "Error: 'name' is required for `activate` subcommand"
        # Block I-2 (Codex iter-1 finding #2 fix): same reject-on-model
        # path for activate. Skill must be user-activated via /skill use.
        sm.discover()
        skill = sm._cache.get(name)
        if skill is not None and skill.disable_model_invocation:
            return (
                f"Error: skill '{name}' is user-invocable only "
                "(disable_model_invocation: true). The user must run "
                f"`/skill use {name}` to activate it."
            )
        ok, msg = sm.activate(name)
        return msg

    if sub == "deactivate":
        sm.deactivate()
        return "Active skill cleared."

    return (
        f"Error: unknown subcommand '{sub}'. "
        "Use one of: list / read / activate / deactivate."
    )


def _register():
    """Idempotent registration. Called by tools/__init__.py:bootstrap_built_ins."""
    from .registry import find_tool_by_name, all_registered
    # Codex Phase-10 finding (MEDIUM): reset singleton FIRST, before the
    # early-return check. Otherwise calling `_register()` after a
    # _reset_registry_for_tests() + monkeypatch CONFIG.workspace flow could
    # leave a stale singleton bound to the previous workspace.
    global _SINGLETON
    _SINGLETON = None
    if find_tool_by_name(all_registered(), "skill") is not None:
        return  # already registered (singleton already cleared above)

    register(build_tool(
        name="skill",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_skill_executor,
        is_read_only=True,          # read/list/activate are state-changes but
                                    # don't touch the filesystem; activate is
                                    # plan-mode-safe (read-only allowlist parity).
        is_destructive=False,
        is_concurrency_safe=True,
        requires_approval=False,
        should_defer=True,          # Phase 7 deferred set; loaded via tool_search
        always_load=False,
        search_hint="skill methodology activate read list verify clara batch reflexion review report design html simplify security",
    ))
