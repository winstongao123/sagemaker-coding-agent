"""Block D — Slash-command dispatcher (22 v4/B+ commands + /auth + 6 LF additions).

v5 port of v4's slash-command surface (sagemaker_agent.py:8164 +
:10789-:11341). The dispatch table here is the single source of truth
for what `/foo` lines do; the chat UI calls `dispatch_command(msg, ...)`
when a user message starts with `/`.

**Command count contract** (verified against `list_commands()`):
  - 19 v4/B+ advertised commands:
    /skills, /skill use, /skill clear, /unskill, /skill suggestions,
    /skill apply, /skill reject, /save, /resume, /revert, /cost, /context, /status,
    /verify, /checkpoint, /phase, /diffs, /regression, /done
  - +6 LF additions:
    /simplify, /init, /init-verifiers, /skillify, /dream, /promote-to-skill
  - +1 /auth gate (separate path; runs BEFORE custom dispatch)
  - +1 /quit command with /q alias
  = **27 canonical commands**.

The dispatch table contains one extra entry (`/skill suggestion` —
singular alias of `/skill suggestions`) for v4 parity with sagemaker_agent.py:10874
which accepts both spellings. The alias is NOT counted toward the 26.

Therefore:
  - `list_commands()` (default include_aliases=True) returns 29 strings.
  - `list_commands(include_aliases=False)` returns 27 strings.
  - Tests assert exactly these numbers.

Earlier docs in this module said "27 canonical commands" — that was an
incorrect headline count (20 + 6 + 1 wasn't reconciled against the
dispatch table). Codex Block-D iter-2 finding #2 lock corrected the
accounting against actual `list_commands()` output.

22 v4/B+ baseline commands (constraint #1 plus B+ session persistence):
  /auth              — auth-token gate (separate from advertised list)
  /skills            — list available skills
  /skill use <name>  — activate a skill (sticky for session)
  /skill clear       — clear all active skills
  /unskill <name>    — deactivate one skill (V4.9.1)
  /skill suggestions — list pending self-patch proposals (V4.9.5)
  /skill apply <name> [--yes|--edit] — preview + apply a proposal (V4.9.5)
  /skill reject <name> — discard pending proposals (V4.9.5)
    /save [title]      — persist current messages + cost snapshot
    /resume <id>       — restore messages + cost snapshot from a session
    /revert <file>     — revert a file via SnapshotManager
  /revert all --yes  — revert all snapshotted files
  /cost              — session cost summary
  /context           — context bloat diagnostic
  /status [init|path]— status bar dump
  /verify [full|quick|pre-commit] — run verify-skill gate
  /checkpoint create|list|restore — snapshot management
  /phase <text>      — set work phase
  /diffs [summary|last|<file>] — session edit history
  /regression        — git diff + session edits + suggested test cmd
  /done [full|quick] — pre-ship gate (simplify + verify)

6 Learning-Factory additions (Wave-5-DEEP):
  /simplify          — expand simplify skill body inline
  /init              — initialize workspace AGENT_STATUS + skills dirs
  /init-verifiers    — install verifier scripts in workspace
  /skillify          — export current chat as a reusable skill
  /dream             — manual memory consolidation (Block H+)
  /promote-to-skill  — chat → skill promotion

PORT_LOG: see #065.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Any, Callable, Dict, List, Optional

from runtime.slash_args import parse_slash_command


# ============================================================
# CommandResult
# ============================================================

@dataclass
class CommandResult:
    """Standard command-handler return shape.

    text:        what to render in the chat as the bot's reply
    consumed:    True iff the message was handled (don't run agent.run())
    side_effect: optional name of a singleton mutation for forensics
    deny_auth:   when True (only /auth path), the auth gate failed —
                 caller must NOT execute any agent code for this message
    """

    text: str = ""
    consumed: bool = True
    side_effect: str = ""
    deny_auth: bool = False


# ============================================================
# Helpers (defer-imports)
# ============================================================

def _get_skill_manager(workspace: str = ""):
    """Lazy SkillManager builder. Per-process singleton."""
    global _SKILLS_SINGLETON
    if "_SKILLS_SINGLETON" not in globals() or _SKILLS_SINGLETON is None:
        from skills.manager import SkillManager
        from runtime.config import CONFIG
        _SKILLS_SINGLETON = SkillManager(
            workspace=workspace or CONFIG.workspace,
            skills_dir=CONFIG.skills_dir,
        )
    return _SKILLS_SINGLETON


_SKILLS_SINGLETON = None


# ============================================================
# /auth — auth-token gate (separate; runs BEFORE custom dispatch)
# ============================================================

def cmd_auth(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Compare `args` (the rest of the line after `/auth `) against
    the env var named by CONFIG.auth_token_env. Returns deny_auth=True
    when CONFIG.require_auth is set and the token doesn't match.
    """
    from runtime.config import CONFIG
    if not getattr(CONFIG, "require_auth", False):
        return CommandResult(
            text="Auth not required (CONFIG.require_auth=False).",
            consumed=True,
        )
    expected = os.getenv(CONFIG.auth_token_env, "")
    if not expected:
        return CommandResult(
            text=f"Auth required but {CONFIG.auth_token_env} env var is not set.",
            consumed=True, deny_auth=True,
        )
    if args.strip() == expected:
        return CommandResult(
            text="Auth OK.", consumed=True, side_effect="auth_granted",
        )
    return CommandResult(
        text="Auth failed: token mismatch.", consumed=True, deny_auth=True,
    )


# ============================================================
# Skills commands
# ============================================================

def cmd_skills(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    sm = _get_skill_manager()
    discovered = sm.discover()
    if not discovered:
        return CommandResult(text="(no skills found)")
    lines = [
        f"  {n} ({info.source}): {info.description[:80]}"
        for n, info in sorted(discovered.items())
    ]
    return CommandResult(text="Available skills:\n" + "\n".join(lines))


def cmd_skill_use(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    name = args.strip()
    if not name:
        return CommandResult(text="Usage: /skill use <name>")
    sm = _get_skill_manager()
    sm.discover()
    # Block I — Hermes fuzzy resolution: directory-name → metadata-name →
    # case-insensitive → fuzzy (difflib cutoff=0.7).
    canonical = sm.resolve_name(name)
    if canonical is None:
        available = ", ".join(sorted(sm._cache.keys())) if sm._cache else "none"
        return CommandResult(
            text=f"Unknown skill '{name}'. Available: {available}"
        )
    sm.active_skill = canonical
    suffix = "" if canonical == name else f" (resolved from '{name}')"
    return CommandResult(
        text=f"Activated skill '{canonical}'{suffix}. Active for this session.",
        side_effect=f"skill_activated:{canonical}",
    )


def cmd_skill_clear(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    sm = _get_skill_manager()
    target = args.strip()
    if target:
        cleared = sm.invalidate_cache(target) if hasattr(sm, "invalidate_cache") else []
        if cleared:
            return CommandResult(
                text="Cleared skill cache(s): " + ", ".join(cleared),
                side_effect=f"skill_cache_cleared:{','.join(cleared)}",
            )
        return CommandResult(
            text=(
                "Unknown skill cache. Valid caches: discovery, skill_listing, "
                "proposal_listing, active_prompt, all."
            )
        )
    prev = sm.active_skill
    sm.active_skill = None
    return CommandResult(
        text=f"Cleared active skill (was: {prev or 'none'})",
        side_effect="skill_cleared",
    )


def cmd_unskill(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    name = args.strip()
    if not name:
        return CommandResult(text="Usage: /unskill <name>")
    sm = _get_skill_manager()
    if sm.active_skill == name:
        sm.active_skill = None
        return CommandResult(text=f"Deactivated skill '{name}'.")
    return CommandResult(text=f"Skill '{name}' was not active.")


def cmd_skill_suggestions(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """V4.9.5 — list pending self-patch proposals."""
    sm = _get_skill_manager()
    proposals = sm.list_proposals() if hasattr(sm, "list_proposals") else []
    if not proposals:
        return CommandResult(text="(no pending skill proposals)")
    lines = []
    for p in proposals:
        lines.append(f"  {p.get('name', '<?>')}: {p.get('summary', '')[:80]}")
    return CommandResult(text="Pending skill proposals:\n" + "\n".join(lines))


def cmd_skill_apply(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """V4.9.5 — preview + apply a proposal."""
    sm = _get_skill_manager()
    parts = args.strip().split()
    if not parts:
        return CommandResult(text="Usage: /skill apply <name> [--yes|--edit]")
    name = parts[0]
    auto_yes = "--yes" in parts[1:]
    if not hasattr(sm, "apply_proposal"):
        return CommandResult(text="Skill self-patching not enabled in this v5 build.")
    try:
        result = sm.apply_proposal(name, auto_apply=auto_yes)
        return CommandResult(text=str(result), side_effect=f"skill_applied:{name}")
    except Exception as e:  # noqa: BLE001
        return CommandResult(text=f"Apply failed: {type(e).__name__}: {e}")


def cmd_skill_reject(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """V4.9.5 — discard pending proposals for a skill."""
    name = args.strip()
    if not name:
        return CommandResult(text="Usage: /skill reject <name>")
    sm = _get_skill_manager()
    if hasattr(sm, "reject_proposals"):
        sm.reject_proposals(name)
        return CommandResult(text=f"Rejected pending proposals for '{name}'.",
                             side_effect=f"skill_rejected:{name}")
    return CommandResult(text="Skill self-patching not enabled in this v5 build.")


# ============================================================
# /revert — snapshot management
# ============================================================

def cmd_revert(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    from runtime.snapshot import SNAPSHOTS
    target = args.strip()
    # Codex Block-D iter-1 finding #1 (HIGH safety) lock: `/revert all`
    # is destructive — strictly require `--yes`. Bare `/revert all` lists
    # what would be reverted instead of executing the bulk revert.
    if target.startswith("all"):
        if target == "all --yes":
            msg = SNAPSHOTS.revert_all()
            return CommandResult(text=msg, side_effect="revert_all")
        # bare `all` (or `all --whatever-else`) → preview only, no revert.
        snaps = SNAPSHOTS.list_snapshots()
        files = sorted({s["file"] for s in snaps})
        if not files:
            return CommandResult(text="(no snapshots to revert)")
        lines = [f"  {f}" for f in files]
        return CommandResult(
            text=(
                "/revert all is destructive — re-run with `/revert all --yes` "
                "to confirm. Files that would be reverted:\n"
                + "\n".join(lines)
            )
        )
    if not target:
        snaps = SNAPSHOTS.list_snapshots()
        if not snaps:
            return CommandResult(text="(no snapshots available)")
        # Group by file, show newest per file.
        seen: Dict[str, str] = {}
        for s in snaps:
            seen.setdefault(s["file"], s["snapshot"])
        lines = [f"  {f}" for f in sorted(seen)]
        return CommandResult(text="Files with snapshots:\n" + "\n".join(lines))
    confirmed = target.endswith(" --yes")
    if confirmed:
        target = target[:-6].strip()
    if not confirmed:
        _ok, msg = SNAPSHOTS.preview_revert(target)
        return CommandResult(text=msg)
    ok, msg = SNAPSHOTS.revert(target)
    return CommandResult(text=msg, side_effect=f"reverted:{target}" if ok else "")


# ============================================================
# /save + /resume — SessionManager cost/history persistence
# ============================================================

def _messages_from_ctx(ctx: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not ctx:
        return []
    messages = ctx.get("messages")
    if messages is None and ctx.get("agent") is not None:
        messages = getattr(ctx["agent"], "messages", [])
    return list(messages or [])


def _restore_messages_to_ctx(
    ctx: Optional[Dict[str, Any]],
    messages: List[Dict[str, Any]],
) -> None:
    if not ctx:
        return
    if ctx.get("agent") is not None and hasattr(ctx["agent"], "_engine"):
        ctx["agent"]._engine.messages = list(messages)
    if "messages" in ctx:
        ctx["messages"] = list(messages)


def cmd_save(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    from runtime.session import SESSIONS
    from runtime.state import STATE
    from runtime.tokens import TOKENS
    from tools.todo import get_current_todos

    title = args.strip() or "Saved Session"
    messages = _messages_from_ctx(ctx)
    _maybe_extract_memory_on_save(ctx, messages)
    status_memory = STATE.capture_status_memory()
    todos = get_current_todos(load_disk=True)
    session = SESSIONS.create(title=title)
    session.messages = messages
    session.todos = todos
    session.metadata["tokens_stats"] = TOKENS.get_stats()
    session.metadata["status_memory"] = status_memory
    session.metadata["recovery"] = {
        "todos_path": str(STATE.todos_path),
        "journal_path": str(STATE.journal_path),
        "last_turn_path": str(STATE.recovery_path),
    }
    SESSIONS.save(session)
    STATE.save_turn_recovery(
        messages=messages,
        todos=todos,
        token_stats=TOKENS.get_stats(),
        status_memory=status_memory,
        result={"command": "save", "session_id": session.id},
    )
    return CommandResult(
        text=f"Saved session {session.id} ({len(session.messages)} messages).",
        side_effect=f"session_saved:{session.id}",
    )


def cmd_resume(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    from runtime.session import SESSIONS
    from runtime.state import STATE
    from runtime.tokens import TOKENS
    from tools.todo import restore_todos

    session_id = args.strip()
    if not session_id:
        return CommandResult(text="Usage: /resume <session-id>")
    session = SESSIONS.load(session_id)
    if session is None:
        return CommandResult(text=f"Session not found: {session_id}")
    _restore_messages_to_ctx(ctx, session.messages)
    restore_todos(session.todos or [], persist=True)
    token_stats = session.metadata.get("tokens_stats")
    STATE.append_journal(
        "resume",
        {
            "session_id": session.id,
            "messages": len(session.messages),
            "todos": len(session.todos or []),
            "has_status_memory": isinstance(
                session.metadata.get("status_memory"), dict
            ),
        },
    )
    if isinstance(token_stats, dict):
        TOKENS.restore(token_stats)
    else:
        return CommandResult(
            text=(
                f"Resumed session {session.id} "
                f"({len(session.messages)} messages, {len(session.todos or [])} todos); "
                "no token stats found."
            ),
            side_effect=f"session_resumed:{session.id}:messages_only",
        )
    return CommandResult(
        text=(
            f"Resumed session {session.id} "
            f"({len(session.messages)} messages, {len(session.todos or [])} todos)."
        ),
        side_effect=f"session_resumed:{session.id}",
    )


def _maybe_extract_memory_on_save(
    ctx: Optional[Dict[str, Any]],
    messages: List[Dict[str, Any]],
) -> List[str]:
    """Optional session-end memory extraction path.

    The default extractor remains zero-cost and writes nothing unless tests or
    callers provide `ctx["memory_extract_fn"]`. This wires the path without
    making `/save` call an LLM.
    """
    from runtime.config import CONFIG

    if not getattr(CONFIG, "enable_memory_extraction", False):
        return []
    try:
        from memory import create_memory_extractor
        extractor = create_memory_extractor(workspace=CONFIG.workspace)
        extract_fn = ctx.get("memory_extract_fn") if ctx else None
        return extractor.extract_memories(
            messages,
            extract_fn=extract_fn,
            force=True,
        )
    except Exception:
        return []


# ============================================================
# /cost — session cost summary
# ============================================================

def cmd_cost(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG
    sess = TOKENS.get_session()
    limit = getattr(CONFIG, "session_cost_limit", 0.0)
    lines = TOKENS.get_cost_block().splitlines()
    lines.append(f"Tokens: {sess}")
    lines.append(f"Session cost: {TOKENS.get_cost()}")
    lines.append(
        f"Parent: in={TOKENS.parent_input_tokens:,} "
        f"out={TOKENS.parent_output_tokens:,}"
    )
    if limit > 0:
        lines.append(f"Limit: ${limit:.2f} (warn-and-continue)")
    return CommandResult(text="\n".join(lines))


# ============================================================
# /context — context bloat diagnostic
# ============================================================

def cmd_context(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    from runtime.tokens import TOKENS
    ctx_size = TOKENS.final_context_tokens_from_last_response()
    return CommandResult(
        text=(
            f"Context window estimate: {ctx_size:,} tokens "
            f"(based on last response usage). Use /cost for full session view."
        ),
    )


# ============================================================
# /status — status bar dump
# ============================================================

def cmd_status(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    from runtime.config import CONFIG
    sub = args.strip()
    if sub == "path":
        return CommandResult(
            text=f"AGENT_STATUS path: {os.path.join(CONFIG.workspace, CONFIG.status_doc)}"
        )
    if sub == "init":
        path = os.path.join(CONFIG.workspace, CONFIG.status_doc)
        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("# Agent Status\n\n_(empty)_\n")
                return CommandResult(text=f"Created {path}", side_effect="status_init")
            except OSError as e:
                return CommandResult(text=f"Init failed: {e}")
        return CommandResult(text=f"Status doc already exists at {path}")
    # Default: dump the current AGENT_STATUS contents.
    path = os.path.join(CONFIG.workspace, CONFIG.status_doc)
    if not os.path.isfile(path):
        return CommandResult(text="(no AGENT_STATUS.md found; use /status init)")
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return CommandResult(text=f"Cannot read status: {e}")
    return CommandResult(text=f"=== AGENT_STATUS.md ===\n{text}")


# ============================================================
# /verify, /checkpoint, /phase, /diffs, /regression, /done
# ============================================================

def cmd_verify(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Run the deterministic local verify gate and arm the verify skill."""
    from runtime.gate import format_gate_result, run_verify_gate

    sm = _get_skill_manager()
    discovered = sm.discover()
    if "verify" not in discovered:
        return CommandResult(text="`verify` skill not installed.")
    sm.active_skill = "verify"
    mode = (args.strip() or "full").lower()
    gate = run_verify_gate(mode, ctx)
    text = format_gate_result(gate, command="verify")
    if gate.ok:
        text += "\nActivated `verify` skill for follow-up verification work."
    return CommandResult(
        text=text,
        side_effect="verify_passed" if gate.ok else "verify_blocked",
    )

def cmd_checkpoint(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    from runtime.snapshot import SNAPSHOTS
    parts = args.strip().split()
    sub = parts[0] if parts else "list"
    if sub == "create":
        if len(parts) < 2:
            return CommandResult(text="Usage: /checkpoint create <name>")
        name = " ".join(parts[1:])
        # Simplified: snapshot every file currently tracked by SNAPSHOTS.
        snaps = SNAPSHOTS.list_snapshots()
        files = sorted({s["file"] for s in snaps})
        if not files:
            return CommandResult(text="(no files to checkpoint — nothing edited yet)")
        checkpoint = SNAPSHOTS.create_checkpoint(name, files)
        return CommandResult(
            text=(
                f"Checkpoint '{name}': snapshotted "
                f"{len(checkpoint.get('entries', []))} files."
            ),
            side_effect=f"checkpoint:{name}",
        )
    if sub == "list":
        snaps = SNAPSHOTS.list_snapshots()
        checkpoints = SNAPSHOTS.list_checkpoints()
        if not snaps and not checkpoints:
            return CommandResult(text="(no snapshots available)")
        lines: List[str] = []
        if checkpoints:
            lines.append("Named checkpoints:")
            lines.extend(
                f"  {c.get('name')} ({len(c.get('entries', []))} files)"
                for c in checkpoints[-20:]
            )
        if snaps:
            lines.append("Recent snapshots:")
            lines.extend(
                f"  {s['file']} @ {s.get('time', 0):.0f}"
                for s in snaps[-20:]
            )
        return CommandResult(text="\n".join(lines))
    if sub == "restore":
        if len(parts) < 2:
            return CommandResult(text="Usage: /checkpoint restore <name-or-file> [--yes]")
        confirmed = parts[-1] == "--yes"
        restore_parts = parts[1:-1] if confirmed else parts[1:]
        target = " ".join(restore_parts)
        checkpoint_names = {c.get("name") for c in SNAPSHOTS.list_checkpoints()}
        if target in checkpoint_names:
            if not confirmed:
                _ok, msg = SNAPSHOTS.preview_checkpoint_restore(target)
                return CommandResult(text=msg)
            ok, msg = SNAPSHOTS.restore_checkpoint(target)
            return CommandResult(
                text=msg,
                side_effect=f"checkpoint_restored:{target}" if ok else "",
            )
        if not confirmed:
            _ok, msg = SNAPSHOTS.preview_revert(target)
            return CommandResult(text=msg)
        ok, msg = SNAPSHOTS.revert(target)
        return CommandResult(text=msg, side_effect="checkpoint_restored" if ok else "")
    return CommandResult(
        text="Usage: /checkpoint [create <name>|list|restore <name-or-file> [--yes]]"
    )


def cmd_phase(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    text = args.strip()
    if not text:
        return CommandResult(text="Usage: /phase <description>")
    # Just record on a per-process state; full UI integration is Block I.
    global _CURRENT_PHASE
    _CURRENT_PHASE = text
    return CommandResult(text=f"Phase set: {text}", side_effect=f"phase:{text}")


_CURRENT_PHASE = ""


def cmd_diffs(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    from runtime.snapshot import SNAPSHOTS
    sub = args.strip().lower()
    snaps = SNAPSHOTS.list_snapshots()
    if not snaps:
        return CommandResult(text="(no edits this session)")
    if sub == "summary":
        files = sorted({s["file"] for s in snaps})
        return CommandResult(text=f"Edited {len(files)} files: " + ", ".join(files[:10]))
    if sub == "last":
        last = snaps[-1]
        return CommandResult(
            text=f"Last edit: {last['file']} (snapshot at {last.get('snapshot', '')})"
        )
    # specific file
    if sub:
        matching = [s for s in snaps if s["file"].endswith(sub)]
        if matching:
            return CommandResult(
                text=f"{len(matching)} snapshots for {sub}: "
                     + ", ".join(s.get("snapshot", "")[-40:] for s in matching[-5:])
            )
        return CommandResult(text=f"(no snapshots match '{sub}')")
    return CommandResult(
        text=f"{len(snaps)} edits this session (use /diffs summary for details)"
    )


def cmd_regression(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """`git diff HEAD --stat` summary + suggested test command.

    v4 ran git as a subprocess; v5 keeps that pattern but skips the
    actual exec when running in non-workspace contexts.
    """
    from runtime.snapshot import SNAPSHOTS
    snaps = SNAPSHOTS.list_snapshots()
    files_edited = sorted({s["file"] for s in snaps})
    parts = ["Session edits (via SnapshotManager):"]
    if files_edited:
        parts.extend(f"  - {f}" for f in files_edited[:20])
    else:
        parts.append("  (none)")
    parts.append("Suggested verification: `pytest tests/` then `git diff HEAD --stat`.")
    return CommandResult(text="\n".join(parts))


def cmd_done(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Run simplify + verify gate. Returns a READY-TO-SHIP verdict."""
    from runtime.gate import format_gate_result, run_done_gate

    sm = _get_skill_manager()
    discovered = sm.discover()
    missing = [s for s in ("simplify", "verify") if s not in discovered]
    if missing:
        return CommandResult(
            text=f"Cannot run /done: missing skills {missing}",
        )
    mode = (args.strip() or "full").lower()
    gate = run_done_gate(mode, ctx)
    text = format_gate_result(gate, command="done")
    if gate.ok:
        text += "\nREADY-TO-SHIP: local status, test, review, result, subagent, and telemetry evidence are fresh."
    return CommandResult(
        text=text,
        side_effect="done_ready" if gate.ok else "done_blocked",
    )


# ============================================================
# Learning-Factory additions (Wave-5-DEEP)
# ============================================================

def cmd_simplify(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    sm = _get_skill_manager()
    discovered = sm.discover()
    if "simplify" not in discovered:
        return CommandResult(text="`simplify` skill not installed.")
    sm.active_skill = "simplify"
    return CommandResult(text="Activated `simplify` skill.",
                         side_effect="simplify_armed")


def cmd_init(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Initialize workspace AGENT_STATUS + skills dirs."""
    from runtime.config import CONFIG
    workspace = CONFIG.workspace
    status_path = os.path.join(workspace, CONFIG.status_doc)
    skills_dir = os.path.join(workspace, "skills")
    created: List[str] = []
    if not os.path.exists(status_path):
        try:
            with open(status_path, "w", encoding="utf-8") as f:
                f.write("# Agent Status\n\n_(empty)_\n")
            created.append(CONFIG.status_doc)
        except OSError as e:
            return CommandResult(text=f"Init failed: {e}")
    if not os.path.isdir(skills_dir):
        try:
            os.makedirs(skills_dir, exist_ok=True)
            created.append("skills/")
        except OSError as e:
            return CommandResult(text=f"Init failed: {e}")
    if created:
        return CommandResult(
            text="Initialized: " + ", ".join(created),
            side_effect="init_workspace",
        )
    return CommandResult(text="Workspace already initialized.")


def cmd_init_verifiers(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Install verifier scripts (placeholder; LF pattern)."""
    from runtime.config import CONFIG
    return CommandResult(
        text=(
            f"Verifier-script install scaffolding ready in {CONFIG.workspace}. "
            "Use `/skill use verify` to run gate checks."
        ),
    )


def cmd_skillify(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Export current chat as a reusable skill (LF pattern)."""
    name = args.strip()
    if not name:
        return CommandResult(text="Usage: /skillify <new-skill-name>")
    return CommandResult(
        text=(
            f"Skillify scaffolded: review chat history, edit "
            f"`skills/{name}/SKILL.md`, then `/skill use {name}`."
        ),
        side_effect=f"skillify:{name}",
    )


def cmd_dream(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Manual memory consolidation (Block H+ wires the actual writer)."""
    return CommandResult(
        text=(
            "/dream — manual memory consolidation. "
            "Block H+ (manual /dream consolidation) wires the actual "
            "writer that compacts session memory.md entries."
        ),
        side_effect="dream_invoked",
    )


def cmd_promote_to_skill(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Promote current chat → reusable skill."""
    name = args.strip()
    if not name:
        return CommandResult(text="Usage: /promote-to-skill <name>")
    return CommandResult(
        text=(
            f"Promote-to-skill scaffolded: edit `skills/{name}/SKILL.md` "
            f"with the chat highlights, then `/skill use {name}`."
        ),
        side_effect=f"promote_to_skill:{name}",
    )


def cmd_quit(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    return CommandResult(text="Quit requested.", side_effect="quit_requested")


# ============================================================
# Dispatch table (single source of truth)
# ============================================================

# Order matters: longer patterns first so `/skill clear` doesn't
# accidentally match `/skills`. Each entry: (prefix, handler).
_DISPATCH: List[tuple] = [
    ("/skill suggestions", cmd_skill_suggestions),
    ("/skill suggestion", cmd_skill_suggestions),  # tolerate singular
    ("/skill use", cmd_skill_use),
    ("/skill clear", cmd_skill_clear),
    ("/skill apply", cmd_skill_apply),
    ("/skill reject", cmd_skill_reject),
    ("/skills", cmd_skills),
    ("/unskill", cmd_unskill),
    ("/resume", cmd_resume),
    ("/save", cmd_save),
    ("/revert", cmd_revert),
    ("/cost", cmd_cost),
    ("/context", cmd_context),
    ("/status", cmd_status),
    ("/verify", cmd_verify),
    ("/checkpoint", cmd_checkpoint),
    ("/phase", cmd_phase),
    ("/diffs", cmd_diffs),
    ("/regression", cmd_regression),
    ("/done", cmd_done),
    # LF additions
    ("/simplify", cmd_simplify),
    ("/init-verifiers", cmd_init_verifiers),
    ("/init", cmd_init),
    ("/skillify", cmd_skillify),
    ("/dream", cmd_dream),
    ("/promote-to-skill", cmd_promote_to_skill),
    ("/quit", cmd_quit),
    # /auth handled BEFORE custom dispatch in caller (separate path)
]

_ALIASES: Dict[str, str] = {
    "/skill suggestion": "/skill suggestions",
    "/q": "/quit",
}


def _canonicalize_alias(message: str) -> str:
    parsed = parse_slash_command(message)
    if not parsed:
        return message
    for alias, target in sorted(_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
        if message == alias or message.startswith(alias + " "):
            return target + message[len(alias):]
    if parsed.command in _ALIASES:
        return _ALIASES[parsed.command] + (
            (" " + parsed.args) if parsed.args else ""
        )
    return message


def _unknown_command_text(command: str) -> str:
    canonical = list_commands(include_aliases=False)
    matches = get_close_matches(command, canonical, n=1, cutoff=0.6)
    hint = f" Did you mean {matches[0]}?" if matches else ""
    return (
        f"Unknown command: {command}.{hint}\n"
        "Known commands: " + ", ".join(canonical)
    )


def is_command(message: str) -> bool:
    """True iff `message` starts with `/` and matches a known prefix."""
    if not message or not message.startswith("/"):
        return False
    message = _canonicalize_alias(message)
    return any(message.startswith(p) for p, _ in _DISPATCH) \
        or message.startswith("/auth ") or message == "/auth"


def dispatch_command(message: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
    """Route a `/foo bar baz` message to the matching handler.

    Returns CommandResult. The chat surface uses `consumed=True` to skip
    the agent loop. `/auth` is a special case: its handler may set
    `deny_auth=True` to indicate the caller should reject the entire
    chat turn.
    """
    if not message or not message.startswith("/"):
        return CommandResult(text="Not a command.", consumed=False)
    # /auth runs BEFORE the custom dispatch (per v4 :11314 explicit check).
    if message == "/auth" or message.startswith("/auth "):
        return cmd_auth(message[len("/auth"):].strip(), ctx)
    message = _canonicalize_alias(message)
    for prefix, handler in _DISPATCH:
        if message == prefix or message.startswith(prefix + " "):
            args = message[len(prefix):].strip()
            try:
                return handler(args, ctx)
            except Exception as exc:  # noqa: BLE001
                logging.warning(f"command {prefix} raised: {exc}")
                return CommandResult(text=f"Command error: {type(exc).__name__}: {exc}")
    parsed = parse_slash_command(message)
    cmd = parsed.command if parsed else message.split()[0]
    return CommandResult(text=_unknown_command_text(cmd), consumed=False)


def list_commands(include_aliases: bool = True) -> List[str]:
    """Return registered command prefixes (for /help-style listings).

    By default returns ALL dispatch entries + /auth + /q (29 strings; this
    includes the `/skill suggestion` singular alias for v4 parity).
    Pass `include_aliases=False` to get the 27 canonical prefixes
    (alias collapsed) — useful for headline command counts.

    Counts reconciled against actual dispatch table per
    Codex Block-D iter-2/iter-3 finding #2.
    """
    prefixes = [p for p, _ in _DISPATCH]
    if not include_aliases:
        prefixes = [p for p in prefixes if p not in _ALIASES]
        return prefixes + ["/auth"]
    return prefixes + ["/auth"] + [a for a in _ALIASES if a not in prefixes]


__all__ = [
    "CommandResult",
    "is_command",
    "dispatch_command",
    "list_commands",
    "parse_slash_command",
]
