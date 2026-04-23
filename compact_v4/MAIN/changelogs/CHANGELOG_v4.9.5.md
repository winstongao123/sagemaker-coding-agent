# CHANGELOG — V4.9.5 (2026-04-23)

## Summary

**Self-patching skills with safety rails.** The hermes "closed learning loop" pattern — agent proposes improvements to its own `SKILL.md` files based on user corrections — but with human-in-loop approval. Opt-in (`CONFIG.enable_skill_patching = False` by default).

User explicitly re-classified the deployment scope: NOT insurance-only, this is for handy/personal use. The previously-rejected self-patching pattern is back on the table — implemented with 4 safety rails to keep behaviour predictable.

19 new tests + 73 regression = **92/92 PASS**.

## What was added

### 1. `CONFIG.enable_skill_patching: bool = False` — opt-in flag
Default OFF. When False, the `skill_propose_patch` tool returns a no-op message ("Skill patching is disabled. Suggest the improvement in chat instead."). Only when set True does the agent actually propose patches.

### 2. `SkillManager.propose_patch(name, reason, new_content)` — propose mode
Writes the proposed SKILL.md body to `skills/<name>/.proposed/<timestamp>.md` with a metadata header (`<!-- proposed_at, skill, reason -->`). The live `SKILL.md` is NEVER touched. Validates: skill exists, reason non-empty, new_content non-empty.

### 3. `SkillManager.list_proposals()` + `get_latest_proposal(name)`
Scans all `skills/*/.proposed/*.md` files. Parses reason from header. Returns sorted list `[{skill, ts, path, reason}]`. `get_latest_proposal` returns the most recent ts when multiple stack.

### 4. `SkillManager.apply_proposal(name)` — review-confirmed merge
- Reads the latest proposal for `name`
- Strips the metadata header (don't pollute live skill body)
- Writes to live `SKILL.md` (snapshots first via existing SNAPSHOTS system → `/revert <path>` undoes the change)
- Re-discovers skills (cache refresh)
- Deletes the applied proposal file
- Audit-logs `apply` event

### 5. `SkillManager.reject_proposal(name)` — discard
Deletes ALL pending proposals for the named skill. Audit-logs `reject` event with count.

### 6. New tool `skill_propose_patch` for the agent
Schema:
```json
{
  "name":        "skill name (must exist in skills/ directory)",
  "reason":      "one sentence explaining why this patch helps",
  "new_content": "FULL replacement SKILL.md body, NOT a diff"
}
```
Refuses to act when `CONFIG.enable_skill_patching` is False (returns clear refusal message).

### 7. Three new slash commands
- `/skill suggestions` — list all pending patches across skills, with reasons
- `/skill apply <name>` — show unified diff (live vs proposed). Accepts `--yes` (apply now), `--edit` (open file for manual tweak first), or no flag (preview only)
- `/skill reject <name>` — discard pending patches, audit-log

### 8. SYSTEM_PROMPT addition — "Skill self-patching (V4.9.5, opt-in)" section
Tells the agent: only propose when `CONFIG.enable_skill_patching = True` AND the user has corrected you 3+ times on the same skill. Don't nag. Use `skill_propose_patch` tool, then mention once in chat.

### 9. Audit log helper `_log_skill_patch_event(action, skill_name, **extra)`
Appends JSONL line per event to `audit_logs/skill_patches.jsonl`. Fields: ts (ISO), action (propose/apply/reject), skill, plus event-specific extras (reason, path, count). Best-effort — never raises.

### 10. Version bump
`__version__`: `4.9.4` → `4.9.5`.

## Safety rails — design rationale

| # | Rail | Implementation |
|---|---|---|
| 1 | Default OFF | `CONFIG.enable_skill_patching = False` shipped default |
| 2 | Propose, don't auto-apply | Patches go to `.proposed/<ts>.md`, live SKILL.md untouched until `apply` |
| 3 | Diff preview before apply | `/skill apply <name>` (no flag) shows unified diff first |
| 4 | Snapshot before apply | Existing `SNAPSHOTS` system invoked — `/revert <path>` undoes |
| 5 | Audit log every event | `audit_logs/skill_patches.jsonl` JSONL append |
| 6 | `--edit` flag | User can tweak the proposed file before applying |
| 7 | Empty-name validation | Tool rejects unknown skills with available list |
| 8 | Tool no-ops when disabled | Even if agent calls the tool unprompted, nothing happens unless flag is on |

## Files Changed

| File | Change |
|---|---|
| `compact_v4/MAIN/agent/sagemaker_agent.py` | NEW: 5 SkillManager methods, `_log_skill_patch_event` helper, `tool_skill_propose_patch`, 3 slash commands. Modified: `Config.enable_skill_patching` field, SYSTEM_PROMPT critique-handling section, TOOLS registry. |
| `compact_v4/MAIN/agent/test_v495_self_patching.py` | NEW — 19 tests covering propose / list / apply / reject / opt-out / audit log / metadata stripping / unknown-skill validation |
| `compact_v4/MAIN/agent/USER_GUIDE.md` | NEW "Self-patching skills (V4.9.5, opt-in)" section + commands table rows |
| `compact_v4/MAIN/agent/chat.md` | Commands table gains 3 new rows |
| `compact_v4/MAIN/agent/chat.ipynb` | Cell 0 (banner): version 4.9.5 + v4.9.X highlights. Cell 4 (quick reminder): self-patching paragraph + table updates |
| `compact_v4/MAIN/changelogs/CHANGELOG_v4.9.5.md` | NEW |
| `compact_v4/CHANGELOG.md` | v4.9.5 entry |
| `SESSION_STATE.md` | v4.9.5 entry |
| `compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md` | §13 appended — self-patching with safety rails (handy use re-classification) |
| `compact_v4/compact_v4.zip` | Rebuilt with version 4.9.5 |

## Verification

- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version `4.9.5`
- `test_v495_self_patching.py` (NEW) — **19/19 PASS**
- `test_v494_hermes_patterns.py` (regression) — **32/32 PASS**
- `test_v493_enhancements.py` (regression) — **11/11 PASS**
- `test_v491_unskill.py` (regression) — **10/10 PASS**
- `test_v49_auto_trigger.py` (regression) — **11/11 PASS**
- `test_v471_enhancements.py` (regression) — **9/9 PASS**
- `test_v461_path_fix.py` (regression) — PASS
- **Total: 92/92 deterministic tests green**
- No Codex this round (per `feedback_codex_skip_bedrock_patches.md`)

## Migration

None. Fully additive:
- Feature OFF by default. Existing flows unaffected.
- To opt in: `CONFIG.enable_skill_patching = True` in agent config or chat.
- Existing `/skill use`, `/skill clear`, `/unskill`, `/skills` commands unchanged.
- New commands `/skill suggestions`, `/skill apply`, `/skill reject` are additive — they only emit messages when there are proposals to act on.
