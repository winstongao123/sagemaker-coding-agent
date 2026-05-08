# Codex Plan v4 — Final APPROVE (2026-05-01)

Model: gpt-5.5 via `codex exec --full-auto -s read-only -m gpt-5.5`.

## Verdict

**APPROVE** on all 3 axes (Q1 + Q2 + Q3).

## Review history (post-no-deferrals correction)

| Round | Verdict | Key findings | Resolution |
|---|---|---|---|
| v4 #1 | REJECT | Stale Codex-PENDING text + canonical-path drift (`create_chat_ui.py` extract refs vs `sagemaker_agent.py` source) + FileCache wrong line + Runnable extractMemories/sessionMemory paths broken + Block N row count + LOC math + tokenEstimation unassigned + slash-command decision-table conflicts + sub-agent attribution test missing | All addressed: canonical paths reset, FileCache class :893-1017, Runnable memory paths fixed (`services/extractMemories/extractMemories.ts` + `services/SessionMemory/sessionMemory.ts`), Block N at 5 rows, tokenEstimation → Block B, decision table replaced with verified Runnable cross-check, sub-agent attribution acceptance test added to B+ |
| v4 #2 | REJECT | FileCache method names wrong (cited save_context/restore_context/current_context — actual APIs are save_and_clear_context/restore_context/enter_thread_local_context/exit_thread_local_context) + Runnable commands "10-command table" listed names that don't exist + Block 12 reference + /save /load mis-attributed |
| v4 #3 | REJECT | v4 slash-command undercount (had 7, v4 actually ships 19 advertised at :8164 + handlers :10789-:11341) + /context wrongly classified as not-in-v4 + stale "10 Runnable-only" math + UI-button vs slash-command boundary |
| v4 #4 | APPROVE_WITH_FIXES | /auth misdescribed as "AWS auth" (actually notebook auth-token gate) + 19/20 command count inconsistency + §0 stale ref + Q3 "/save /load /compact /clean slash command suite" wording |
| v4 #5 | REJECT | v4 tool surface (11 tools) missing entirely from plan: create_word/excel/markdown/notebook/chart/pdf, todo_write/read, semantic_search, web_fetch, ask_user. Q1 "21 vs 22" rows inconsistency. Q1 line 59 stale "/auth = AWS auth" |
| v4 #6 | APPROVE_WITH_FIXES | Sequence at :398 omits new Block T + Block T impl refs vague + Q3 IterationBudgetWidget/ThinkingBudgetWidget claims unbacked |
| v4 #7 | APPROVE_WITH_FIXES | 161 vs 172 row-count consistency + "v5 > Runnable > v4" stale phrasing at :96 + :440 vs Q3 settled "v5 ≥ Runnable AND v5 > v4 decisively" + Q3 "Block 9" doesn't exist (renamed to Block G) |
| v4 #8 | **APPROVE** | All prior issues addressed. Q1 + Q2 + Q3 APPROVE. |

## Final scope (18 blocks, ~11,330 LOC)

`Block 0 → notebook smoke gate → B → B+ → C → C+ → D → A → E+F → I → M → G → G2 → H → L → N → T → J → K`

- **Block 0**: sagemaker_agent.py shim (50 LOC) — v4 chat.ipynb canonical UI compatibility.
- **Block B**: TokenTracker + AuditLogger + SnapshotManager + Runnable tokenEstimation (440 LOC).
- **Block B+**: SessionManager + AGENT_STATUS auto-load + FileCache class verbatim + sub-agent attribution acceptance test (325 LOC).
- **Block C**: Runtime safety gates — exec-limit + repetition + misleading-error-fix (250 LOC).
- **Block C+**: Approval gate + diff_widget wiring + rate-limits + PermissionDialog richer (200 LOC).
- **Block D**: Full v4 19-advertised + /auth = 20 command-like inputs + dispatcher + CommandRegistry (700 LOC).
- **Block A**: Compactor + cold-cache + auto-compact circuit breaker COMBINED v4 + Runnable services/compact/* (3300 LOC).
- **Block E+F**: HTML chat rendering + cell 2 widgets + complete session UI + IterationBudgetWidget + ThinkingBudgetWidget (2300 LOC).
- **Block I**: Skill name resolution v4 + Hermes fuzzy match (50 LOC).
- **Block M**: Phase 8 critical fixes — discoveredSkillNames reset + structured-output retry counter (30 LOC).
- **Block G**: AGENT_TYPES (7) + worktree spawn + handoff/env builders (280 LOC).
- **Block G2**: forkSubagent cache-prefix replay (100 LOC).
- **Block H**: Memory extraction COMBINED v4 + Runnable extractMemories + sessionMemory (1252 LOC).
- **Block L**: Runnable error/retry/cache-break extensions (250 LOC).
- **Block N**: Hermes net-new (parallel exec + dedup + fuzzy + ephemeral prompt + dynamic tool ref injection) (300 LOC).
- **Block T**: v4 tool surface parity — 11 missing v4 tools verbatim (1100 LOC).
- **Block J**: Real-Bedrock smoke + zip extract+import verify (150 LOC).
- **Block K**: Process discipline (LF AXIS C + per-block user gate + STATE/RESUME) (200 LOC docs).

## Coverage claims (Q1 evidence matrix verified)

- v4: 110+ rows ported with `compact_v4/MAIN/agent/sagemaker_agent.py` line refs verified by grep + Read.
- Runnable: 30+ rows ported (compact services + extractMemories + sessionMemory + tokenEstimation + PermissionDialog + dispatcher pattern + cache_edits + autoCompact + per-tool schema hashing + 18 error categories + retry-after).
- Hermes: 5 PORT_LOG rows in Block N + 1 cross-block reuse (Block I fuzzy) + 7 patterns covered by v4 baseline = 13 total.
- LF: 5 patterns adopted (STATE/RESUME, AXIS C plan-fidelity gate, per-block approval, PORT_LOG schema, Codex-3-axis template).

## Deferral count: 0

Per user no-deferrals directive 2026-04-30 / 2026-05-01.

## Status

**READY FOR BLOCK 0** pending user start signal. Per Block K discipline, each block requires explicit user approval before next starts.
