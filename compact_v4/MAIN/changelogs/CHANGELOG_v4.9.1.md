# CHANGELOG — V4.9.1 (2026-04-23)

## Summary

Patch release completing audit §8 coverage from v4.9.0.

- `/unskill <name>` command for per-skill deactivation
- Sticky deactivation — `/skill clear` and `/unskill` now prevent silent auto-re-match in the same session
- Tightened "Handling Critique" SYSTEM_PROMPT section — three gap fixes surfaced in post-v4.9.0 self-review
- One logic bug found and fixed in diff review: `/unskill <nonexistent>` no longer silently succeeds

No Codex review this round — patch scope is Bedrock-agent UI handlers and prompt text, nothing Codex's generic code-review lens adds value to. Self-review + 30/30 tests only.

## Changes

### 1. New `/unskill <name>` command
- Syntax: `/unskill clara-review` → removes from `active_skills`, adds to `deactivated_skills`
- Reports with correct verb: `Deactivated skill: ...` if it was active, `Blocked auto-match for skill: ...` if only in auto-match range
- Validates `name` against `SKILLS._cache` — rejects nonexistent skill names with the available list (prevents silent junk-in-deactivated-set bug)
- Empty name shows usage hint

### 2. Sticky deactivation (new `ui_state["deactivated_skills"]` set)
- `/unskill <name>` → adds to set
- `/skill clear` → adds ALL previously-active skills to set
- `/skill use <name>` → removes from set (explicit re-enable lifts the block)
- Auto-match loop ([line ~9377](compact_v4/MAIN/agent/sagemaker_agent.py)) skips any skill in the set
- New Session button clears the set (both reset paths covered)
- Session-scoped only — not persisted to saved session metadata (design: "please don't auto-match now" is a live signal, not a durable preference)

### 3. SYSTEM_PROMPT — "Handling Critique" tightened (v4.9.0 section at line 6553)
- "Re-open the source file" → "Call `read_file` on the source being discussed" (measurable tool call, not a mental concept)
- New fallback line: if the source isn't accessible (not in workspace, from past session, etc.), say so explicitly and don't fabricate file references
- ACCEPT label gained: "For clear-cut critiques (typos, obvious errors), state ACCEPT concisely without padding evidence to look thorough" — prevents over-verification on trivial cases

### 4. Logic bug fixed
- Pre-fix: `/unskill <nonexistent>` silently added the fake name to `deactivated_skills` and printed `Blocked auto-match for skill: nonexistent`.
- Post-fix: validates against `SKILLS._cache` first, rejects with a list of available names.

### 5. Version bump
`__version__`: `4.9.0` → `4.9.1`.

## Files Changed

| File | Change |
|---|---|
| `compact_v4/MAIN/agent/sagemaker_agent.py` | +40 -6 lines across 6 regions (ui_state init × 3, /skill use, /skill clear, /unskill, auto-match loop, SYSTEM_PROMPT) |
| `compact_v4/MAIN/agent/test_v491_unskill.py` | NEW — 10 tests |
| `compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md` | Appended §9 — audit §8 closure summary |
| `compact_v4/MAIN/changelogs/CHANGELOG_v4.9.1.md` | NEW |
| `compact_v4/CHANGELOG.md` | v4.9.1 entry |
| `SESSION_STATE.md` | v4.9.1 entry |

## Verification

### Self-review
- `py_compile`: PASS
- `ast.parse`: PASS
- `import sagemaker_agent` (warnings-as-errors): PASS, version `4.9.1`
- `test_v491_unskill.py` (new): **10/10 PASS**
- `test_v49_auto_trigger.py` (regression): **11/11 PASS**
- `test_v471_enhancements.py` (regression): **9/9 PASS**
- **Total: 30/30 tests green**
- Final diff re-read: clean; one logic bug (validation) caught and fixed during diff review

### Why no Codex this round
Codex adds value when changes touch general-purpose code patterns (tokenization, algorithm edge cases — which it did catch in v4.9.0 round 1). v4.9.1 is two UI handlers + prompt text. Codex's lens on Bedrock-specific agent internals adds little over what self-review already covers. Explicit per-session decision by the user. This is not a shortcut — the quality gates (11+10+9 tests, static checks, manual diff review) all passed.

## Audit §8 closure

| Audit §8 item | Status after v4.9.1 |
|---|---|
| #1 Thinking-mode `temperature=1` calibration | **Out of scope — Bedrock API constraint, cannot override** |
| #2 "Re-read source before defending" rule | **DONE in v4.9.0**, tightened further in v4.9.1 (concrete `read_file` tool call) |
| #3 Partial-agreement scaffold | **DONE in v4.9.0**, tightened further in v4.9.1 (ACCEPT concise-for-clear-cases exception + workspace-absent fallback) |
| #4 `/unskill` command | **DONE in v4.9.1** |
| #5 Skill-injection char count | **DONE in v4.9.0** |

Additional item discovered during v4.9.1 work:
- **Sticky deactivation after explicit clear** — not in original audit §8, found while implementing /unskill. Without this, `/skill clear` could be silently undone on the next user message. Added to v4.9.1.

## Migration

None. Fully backwards compatible.
- `deactivated_skills` is a new `ui_state` field that defaults to `set()` on init.
- Old sessions loaded without the field still work — `.get("deactivated_skills", set())` handles the default.
- `/unskill` is additive — existing `/skill use`, `/skill clear`, `/skills` commands unchanged in behaviour (just extended with sticky tracking).
