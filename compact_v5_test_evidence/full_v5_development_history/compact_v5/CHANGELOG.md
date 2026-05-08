# compact_v5 changelog

## Changelog Postmortem Entry Shape

For every non-trivial bug fix, reviewer finding closure, or process incident,
add a short postmortem entry with these subsections:

### Symptom

What failed or what risk was observed.

### Root cause

Why the failure or risk existed.

### Fix

What changed, including the primary code or process artifact.

### Verification

Which local test, scope audit, reviewer verdict, or explicit no-test
justification proves the fix.

## v5.0.1-block-i completion-audit redo (2026-05-05)

### Symptom

Block I had no v5 completion-audit artifact folder or row ledger, and the
existing ADR still described I-12 frontmatter parser improvements as deferred.

### Root cause

The earlier Block I implementation landed most skill discovery and activation
behavior, but the redo process requires every canonical row to be ledgered and
the no-deferrals rule means I-12 needed concrete parser/test evidence instead
of a historical remap note.

### Fix

Extended `skills/manager.py` frontmatter normalization for I-12: bracketed
CSV-like scalars, quoted tokens, one-level brace expansion for path globs, and
non-string description coercion. Added Block I parser lock tests and updated
PORT_LOG/ADR evidence. No `/project-*` commands were added.

### Verification

- `py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_i.py -q`: 23 passed, 1 skipped.

## v5.0.1-block-g completion-audit redo (2026-05-05)

### Symptom

Block G had no v5 completion-audit artifact folder or row ledger, and G-1/G-2
were still described as a historical memory deferral even though the canonical
scope treats them as Block G rows.

### Root cause

The earlier Block G work shipped subagent role, prompt, worktree, and budget
behavior, but per-agent memory prompt loading and memory-path safety had been
split away from the block without a user-approved disposition.

### Fix

Added `subagent/agent_memory.py` for scoped per-agent `MEMORY.md` prompt
loading and normalized agent-memory path checks. Added `AgentType.memory_scope`
and wired review-agent project memory prompt injection into `spawn_subagent`.
Updated PORT_LOG/ADR evidence and created the Block G audit artifacts.

### Verification

- `py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_g.py compact_v5/MAIN/agent/tests/integration/test_block_g2.py compact_v5/MAIN/agent/tests/integration/test_subagent.py -q`: 49 passed, 1 skipped.
- `py -3.11 -m py_compile ...`: PASS.
- `py -3.11 compact_v5/_status/scripts/scope_audit.py --block G`: READY_TO_REVIEW_CLOSE, 8 shipped, 0 ship-blocking rows.

## v5.0.1-block-d completion-audit redo (2026-05-05)

### Symptom

Block D had no v5 completion-audit artifact folder or row ledger. The scope
audit therefore reported D-1 through D-13 as ship-blocking even though the older
dispatcher covered only the aggregate slash-command surface.

### Root cause

The earlier Block D evidence predated the Wave-5-DEEP row split and did not
cover Runnable deltas for parallel skill discovery, source-aware skill listing,
named cache invalidation, `/q` alias/helpful unknown-command UX, bundled
scaffolder prompt skills, or custom slash argument parsing.

### Fix

Finished the D rows in `commands.py`, `skills/manager.py`, and the new
`runtime/slash_args.py`. Added bundled user-invoked prompt skills for `init`,
`init-verifiers`, and `skillify`; source labels and budget filters for skill
listing; named cache invalidation; `/quit` plus `/q`; and indexed/named
argument substitution. The implementation follows the software-project workflow
constraint by consolidating behavior into existing commands rather than adding
new `/project-*` commands.

### Verification

- `py -3.11 -m pytest tests/integration/test_block_d.py -q`: 31 passed.
- `py -3.11 -m pytest tests/integration/test_block_h_plus.py::test_dream_invoked_via_console_chat_ui tests/integration/test_block_i.py::test_skillify_4_round_interview -q`: 2 passed.
- `py -3.11 -m py_compile commands.py skills/manager.py runtime/slash_args.py`: PASS.

## v5.0.1-block-b-plus completion-audit redo (2026-05-05)

### Symptom

Block B+ had no v5 completion-audit ledger, so `scope_audit.py --block B+`
reported 8 expected rows, 0 ledger rows, and all B+ rows ship-blocking.

### Root cause

The earlier Block B+ build shipped several cost/session/runtime pieces, but
B+3, B+4, and B+6 were documented as future Block I remaps rather than having
current B+ row-level implementation and test evidence.

### Fix

Added explicit B+ row evidence for all 8 canonical rows. `TokenTracker` now
exposes canonical per-model usage, a four-line cost block, local-only
OTel-style counters, and context-window refresh state; `/cost` uses the
four-line summary. After Claude iter6 found that B+1 had only manual
save/restore plumbing, `/save` and `/resume` were wired through the production
command path so session messages and `TOKENS.get_stats()` metadata persist and
`TOKENS.restore()` rehydrates cost counters on resume. B+ lock tests cover the
new surfaces plus exit flush and Config row evidence.

### Verification

- `py -3.11 -m pytest tests/integration/test_block_b_plus.py -q`: 29 passed.
- `py -3.11 -m pytest tests/integration/test_block_d.py -q`: 22 passed.
- `py -3.11 -m pytest tests/integration/test_block_a.py::test_advisor_cost_attributed_when_aux_model_set tests/integration/test_block_a.py::test_advisor_falls_back_to_parent_when_no_aux -q`: 2 passed.
- `py -3.11 -m py_compile commands.py ui/chat_ui.py tests/integration/test_block_b_plus.py tests/integration/test_block_d.py`: PASS.

## v5.0.1-block-t completion-audit utility closure (2026-05-04)

### Symptom

Block T previously had aggregate tool-surface evidence but no row-level closure
for the v4/Runnable utility fold-ins T-1 through T-12. The missing rows included
semantic coercion, range-read errors, lockfiles, API limits, tool-result
budgets, XML tag constants, and explicit disposition for web_fetch/UI-only
tagging.

### Root cause

Earlier Block T work closed the visible v4 tools as a bundle. That left several
small utility rows unimplemented or undocumented, and it did not prove the
already-present tools against the canonical SYNTHESIS_MASTER row list.

### Fix

Added `runtime/tool_surface.py` for shared Block T constants/helpers, wired the
helpers into `read_file`, `view_image`, `tool_search`, and QueryEngine
tool-result turn assembly, and updated Block T ledger/PORT_LOG/ADR evidence for
all 12 canonical rows. The user-highlighted Block N parallel dispatch risk was
rechecked with the existing single-tool dispatch pipeline and regression tests.

### Verification

Local zero-cost validation: py_compile PASS; Block T suite 17 passed/14 skipped;
Phase 4 tools 39 passed; tool_search 32 passed; skills 12 passed; Block N
parallel-risk subset 3 passed/25 deselected. Claude iter1 LOW audit counter
finding fixed with a scope_audit normalization helper and Block K process lock
test; refreshed Block T strict audit reports 10 shipped, 1 dropped, 1 N/A, 0
blocking. No AWS/R-tier test was run.

## v5.0.1-block-e-f — env_block + ADR-020 0-2/0-4/0-6 remap closure (2026-05-03)

Codex review: 2-iter cycle (gpt-5.3-codex throughout):
- iter 1 (2 files): REJECT with 3 findings (HIGH integration gap —
  env_block helper orphaned; MEDIUM session-start mismatch using
  non-memoized helper; LOW POSIX shell test no-op).
- All 3 fixed; 3 finding-lock tests added.
- iter 2 (3 files): APPROVE.

Eighth Block of the v5.0.1 21-Block build. Phase 6 (sectioned prompt)
+ Phase 11 (notebook UX) already shipped most of the v4-vs-Runnable
Block E+F surface in v5.0.0; this Block closes the 3 remaining
ADR-020 remap rows for env-block content.

NEW:
- `prompt/env_block.py` (~125 LOC):
  - `get_session_start_date()` lru_cached for cache-stable date
  - `get_local_month_year()` human "May 2026" form
  - `get_knowledge_cutoff(model_id)` 5-model lookup with cross-region
    prefix stripping
  - `get_os_string()` / `get_shell_hint()` platform-aware
  - `render_env_block()` assembles markdown body with Notes appendix
    (no-streaming reminder + Windows-shell hint when applicable)

TESTS: 12 new in `tests/integration/test_block_e_f.py`.

PORT_LOG #071 + ADR-027.

Pytest: 587 passed + 5 skipped (was 575 + 5 at Block A; +12 net new).
verify_ship_zip.py: PASS (112 files / 310.5 KB / 37%).

## v5.0.1-block-a — Compactor + auto-compact circuit breaker + cache_edits (2026-05-03)

Codex review: 2-iter cycle (gpt-5.3-codex throughout):
- iter 1 (3 files): REJECT with 4 findings (1 HIGH PTL retry user-first
  bug, 3 MEDIUM: PRUNE_MIN_SAVINGS rollback lost, CB check+record TOCTOU,
  helpers unwired into runtime).
- All 4 fixed; 4 finding-lock tests added.
- iter 2 (4 files): APPROVE.

Seventh Block of the v5.0.1 21-Block build. The load-bearing piece for
long-session context-window management. Closes B-2 + B+5 deferrals
from ADR-021/ADR-022.

NEW:
- `core/compactor.py` (~430 LOC):
  - `Compactor` class — verbatim port of v4 sagemaker_agent.py:186-635
    (multi-mode compaction: prune + summarize + replace). estimate_tokens
    delegates to runtime/tokens helpers (drops tiktoken). PROTECTED_TOOLS
    invariant preserved (todo_write/todo_read/semantic_search never pruned).
  - `AutoCompactCircuitBreaker` + `AUTO_COMPACT` singleton — Hermes
    cooldown + session-cap pattern. Session cap checked first.
  - `apply_cache_control_to_blocks` — Bedrock equivalent of Runnable's
    Anthropic-direct cache_edits.
  - `count_tokens_via_haiku_fallback` — closes B-2 deferral.
  - `_summary_client` + advisor attribution — closes B+5 deferral.

TESTS: 21 new in `tests/integration/test_block_a.py`.

PORT_LOG #066-#070 + ADR-026.

Pytest: 571 passed + 5 skipped (was 550 + 5 at Block D; +21 net new).
verify_ship_zip.py: PASS (111 files / 307.1 KB / 37%).

## v5.0.1-block-d — Slash-command dispatcher (2026-05-03)

Codex review: 4-iteration cycle (gpt-5.3-codex throughout):
- iter 1 (3 files): APPROVE_WITH_FIXES with 2 findings (1 HIGH safety
  — /revert all without --yes was destructive; 1 MEDIUM coverage
  accounting drift).
- iter 2 (3 files): APPROVE_WITH_FIXES — finding #1 closed; #2 still
  flagged as inconsistent (my "27 canonical" claim didn't match actual
  dispatch table).
- Recounted dispatch: 17 v4 advertised + /auth + 6 LF = 24 canonical;
  +1 alias (/skill suggestion) = 25 in full listing. Reconciled module
  docstring + test assertions to exactly these numbers.
- iter 3 (2 files): REJECT — list_commands() inner docstring still
  said 26/27.
- iter 4 (1 file): APPROVE — inner docstring also reconciled.

3 finding-lock tests added (/revert all safety, alias routing,
canonical count). Total Block D tests: 22.

Sixth Block of the v5.0.1 21-Block build. Closes constraint #1
(v4.10.10 baseline) for the slash-command surface — 20 v4 commands +
/auth gate + 6 Learning-Factory additions.

NEW:
- `commands.py` (~450 LOC) — flat dispatch table + 27 handler functions
  + CommandResult dataclass + `is_command()` / `dispatch_command()` /
  `list_commands()` public API.

WIRED:
- `ui/chat_ui.py` — both ConsoleChatUI.send and WidgetChatUI._on_send
  route `/foo` messages through commands.dispatch BEFORE agent.run().

Commands (20 v4 + 6 LF + /auth = 27):
  /auth — auth-token gate
  /skills, /skill use, /skill clear, /unskill, /skill suggestions,
  /skill apply, /skill reject — skill mgmt (V4.9.1+V4.9.5 surface)
  /revert (incl. `all --yes`) — SnapshotManager
  /cost, /context, /status (incl. init/path) — diagnostics
  /verify, /checkpoint (create/list/restore), /phase, /diffs (summary/
  last/<file>), /regression, /done — workflow gates
  /simplify, /init, /init-verifiers, /skillify, /dream,
  /promote-to-skill — Learning-Factory additions

TESTS: 19 new in `tests/integration/test_block_d.py`.

PORT_LOG #065 + ADR-025.

Pytest: 547 passed + 5 skipped (was 528 + 5 at Block C+; +19 net new).
verify_ship_zip.py: PASS (110 files / 300.1 KB / 37%).

## v5.0.1-block-c-plus — Approval/diff + rate limits + ipywidgets fallback (2026-05-03)

Codex review: 2-iteration cycle (gpt-5.3-codex throughout):
- iter 1 (3 files): REJECT with 3 findings (2 HIGH wiring, 1 MEDIUM
  test coverage).
- All 3 fixed; each has 1+ covering lock test (3 new lock tests added).
- iter 2 (4 files): APPROVE — all 3 fixes verified clean.

Fifth Block of the v5.0.1 21-Block build. Wires the approval/diff
flow (Phase-4 ADR-010 commitment) + Block-C UI-only helpers
(C-11/C-12/C-13/C-14 cd+git/multi-cd/pipe-segment/comment-label)
through the new PermissionDialog. Closes ADR-023 §Notes / known scope
remaps for Block-C UI items.

NEW:
- `ui/approval_dialog.py` (~280 LOC): PermissionDialog + RateLimiter +
  ApprovalResult. Sticky always-allow (CONFIG._always_allowed), reason
  prompt, ipywidgets-or-text-fallback, headless 60s watchdog, non-TTY
  defaults-to-deny.

WIRED:
- `core/query_engine.py`: rate-limit gate at run() entry (returns
  stop_reason="rate_limited" without consuming budget); approval gate
  before tool.execute() (gated on require_tool_approval +
  tool.requires_approval + NOT client.mock_mode); on deny, returns
  user-denied tool_result so model can recover.

TESTS: 14 new in `tests/integration/test_block_c_plus.py` covering all
7 TEST_DESIGN §Block C+ items + 4 Block-C remap locks
(test_approval_renders_*) + 3 lifecycle locks (sticky-flag,
sliding-window expiry, run() entry wiring).

PORT_LOG #064 + ADR-024.

Pytest: 525 passed + 5 skipped (was 511 + 5 at Block C; +14 net new).
verify_ship_zip.py: PASS (109 files / 292.8 KB / 37%).

## v5.0.1-block-c — Runtime safety + JSON repair + injection scan + bash hardening (2026-05-03)

Codex review: 2-iteration cycle (gpt-5.3-codex throughout):
- iter 1 (6 files): APPROVE_WITH_FIXES with 4 findings (2 HIGH wiring,
  2 MEDIUM correctness).
- All 4 fixed; each has 1+ covering lock test (4 new lock tests added).
- iter 2 (5 files): APPROVE — all 4 fixes verified clean.

Fourth Block of the v5.0.1 21-Block build. Closes PS#7 (exec-limit) +
9 Wave-5-DEEP findings + 2 ADR-020 remap rows (0-5 scratchpad, 0-10
v4-native injection scanner).

NEW security modules (all self-contained):
- `security/json_repair.py` (~115 LOC) — Hermes-style malformed-JSON repair.
- `security/injection_scanner.py` (~100 LOC) — 12 v4 patterns + invisible chars.
- `security/scratchpad.py` (~110 LOC) — per-process scratchpad with GC.
- `security/edit_file_safety.py` (~190 LOC) — quote norm + UTF-16 BOM + UNC
  + CRLF round-trip + Windows staleness fallback.
- `security/bash_safety.py` (~225 LOC) — exit-code semantics + 13-pattern
  destructive catalog + cd+git + multi-cd + pipe-segment splitter.

EXTENDED:
- `security/manager.py` SECRET_PATTERNS: 13 → 38 (added 25 gitleaks patterns:
  OpenAI sk-/sk-proj-, Google AIza/ya29, Mailchimp, Mailgun, Twilio, Square,
  Stripe live/test, GitLab PAT, npm, Hugging Face, Replicate, Pinecone,
  x-api-key, PGP, Heroku, Cloudflare).
- `tools/edit_file.py`: wired UNC reject + UTF-16 BOM + quote norm + line-ending
  round-trip.
- `tools/bash.py`: wired interpret_command_result for non-zero exit codes.
- `core/query_engine.py`: exec-limit gate (PS#7 fix; bash+python_exec only;
  v4 verbatim "OTHER TOOLS STILL WORK" message) + repetition detector
  (3rd identical call blocks with stuck-loop message) + JSON repair on
  tool_use.input parsing.

TESTS: 17 new in `tests/integration/test_block_c.py`. All 12 TEST_DESIGN
§Block C tests + 2 ADR-020 remap lock tests + 3 helper-coverage tests.

PS#7 STRUCTURALLY ADDRESSED: exec-limit gate + verbatim recovery message
locked by test_exec_limit_200_then_201_blocked.

PORT_LOG #057-#063 + ADR-023.

Pytest: 507 passed + 5 skipped (was 490 + 5 at Block B+; +17 net new).
verify_ship_zip.py: PASS (108 files / 286.8 KB / 37%).

## v5.0.1-block-b-plus — SessionManager + cost-limit + AGENT_STATUS + FileCache (2026-05-03)

Codex review: 3-iteration cycle — gpt-5.3-codex throughout (gpt-5.5 was
hanging on long file lists; reverted per ~/.claude/CLAUDE.md update).
- iter 1 (gpt-5.3-codex, 13-file prompt): APPROVE_WITH_FIXES, 4 findings
  (1 HIGH cost-warning state leak + > vs >=, 2 MEDIUM, 1 LOW).
- All 4 fixed; each has 1+ covering lock test (6 new lock tests added).
- iter 2 (gpt-5.3-codex, 5-file focused prompt): APPROVE_WITH_FIXES on
  finding #2 — entry.py guard could false-positive on external pip-installed
  mcp packages (suffix-match was too broad).
- Tightened guard to compare realpath against v5 agent package root.
- Added 2 lock tests that ACTUALLY exercise the guard (drop fake in-tree
  mcp/ → assert ImportError; add external mcp via syspath_prepend → assert
  entry imports cleanly).
- iter 3 (gpt-5.3-codex, 2-file focused prompt): APPROVE.
- Lesson: focused 2-5 file Codex prompts via stdin pipe complete reliably
  in 1-3 min. 13-file prompts complete in 5-10 min with gpt-5.3-codex
  (vs hanging with gpt-5.5).

Third Block of the v5.0.1 21-Block build. Closes the persistence + handoff
machinery that consumes Block B's data layer.

- NEW `runtime/session.py` (~165 LOC): Session dataclass + SessionManager
  + SESSIONS singleton (verbatim from v4:2578-2659). Atomic save via
  tempfile.mkstemp + os.replace. Schema-tolerant load.
- NEW `runtime/file_cache.py` (~165 LOC): FileCache + FILE_CACHE singleton
  (verbatim from v4:893-1017). Verified APIs: get/put + is/mark/clear_in_context
  + save_and_clear_context/restore_context + enter/exit_thread_local_context
  + clear_all. RLock + threading.local for parallel sub-agents.
- NEW `runtime/cleanup_registry.py` (~95 LOC): atexit + SIGINT/SIGTERM
  callback registry. Per ADR-020 Block 0 item 0-7 remap.
- NEW `runtime/feature_flags.py` (~85 LOC): feature_enabled +
  is_banned + assert_not_banned. Banned set: mcp / streaming /
  anthropic_api_direct (per v5.0.1 hard constraints #9, #10). Per
  ADR-020 Block 0 item 0-9 remap.
- WIRED `core/query_engine.py`: per-run cost runtime warning at 100%+
  of session_cost_limit (warn-and-continue per user 2026-05-03 Plan v3
  update; matches v4 UX).
- WIRED `subagent/spawn.py`: FILE_CACHE.save_and_clear_context before
  child.run + FILE_CACHE.restore_context in finally. Sub-agents see a
  clean slate; parent's set is preserved even if child raises.
- WIRED `agent/__init__.py`: AGENT_STATUS auto-load on first Agent.run().
  Reads CONFIG.workspace/AGENT_STATUS.md (8 KB cap), appends to dynamic
  tail of system prompt after CACHE_BOUNDARY (prefix replay preserved).
  Idempotent — once per Agent instance.
- WIRED `runtime/tokens.py`: cleanup_registry registers `_flush_cost_on_exit`
  so session-final cost is logged at WARNING even on Ctrl+C.
- LAZY @property `_config` on TokenTracker / AuditLogger / SnapshotManager
  / SessionManager so `importlib.reload(runtime.config)` in tests doesn't
  strand singletons on a stale CONFIG instance. Caught when Block B+'s
  test_session_cost_limit_warns_at_100pct intermittently failed after
  Block B's test_env_validation_wired_into_config reloaded config.
- 14 new tests in `tests/integration/test_block_b_plus.py`. PS#5 + PS#6
  closed via test_session_save_load_preserves_cost +
  test_tokens_singleton_is_budget_source.
- PORT_LOG #048-#055 + ADR-022.
- Pytest: 483 pass + 5 skip (was 469 + 5 at Block B; +14 net new).
- verify_ship_zip.py: PASS (104 files / 272.4 KB / 38%).

## v5.0.1-block-b — TokenTracker + AuditLogger + SnapshotManager + tokenEstimation (2026-05-03)

Second Block of the v5.0.1 21-Block build. Closes the v5.0.0 PS_problems
#5 (session cost not persisted) + #6 (budget read from wrong source).

- NEW `runtime/tokens.py` (~480 LOC): TokenTracker (verbatim from v4) +
  per-agent attribution (parent_input/output/cost + subagent_*[type]
  dicts) + MODEL_COSTS for Haiku 4.5 / Sonnet 4.6 + EXCLUDED_MODELS_
  FOR_CACHE_BREAK Haiku set + IMAGE_MAX_TOKEN_SIZE + canonicalize_model_id
  + Runnable tokenEstimation helpers (bytes_per_token_for_file_type +
  estimate_message_tokens 4/3 padding + has_thinking_blocks +
  rough_token_count_for_block + final_context_tokens_from_last_response
  + token_count_with_estimation) + ToolResult dataclass.
- NEW `runtime/audit.py` (~155 LOC): AuditEntry + AuditLogger (verbatim
  from v4) + AUDIT singleton.
- NEW `runtime/snapshot.py` (~135 LOC): SnapshotManager (verbatim from
  v4) + SNAPSHOTS singleton.
- NEW `runtime/env_validation.py` (~60 LOC): validate_bounded_int_env_var
  (per ADR-020 Block 0 item 0-8 remap).
- EXTENDED `runtime/bedrock_client.py`: BEDROCK_EXTRA_PARAMS_HEADERS
  frozenset (per ADR-020 Block 0 item 0-3 remap) + count_tokens method
  (B-1, R4 #41 MUST). Mock-mode falls through to rough estimator.
- WIRED `core/query_engine.py`: TOKENS.add(usage, model_id, agent_kind)
  after every chat() return; AUDIT.log on every tool dispatch (success
  + failure paths); new agent_kind + session_id ctor params.
- WIRED `subagent/spawn.py`: `_new_child_engine` accepts `agent_type`
  and forwards as `agent_kind` so sub-agent costs go to the right bucket.
- WIRED `tools/edit_file.py` + `tools/write_file.py`: SNAPSHOTS.save
  best-effort before mutation. Failure does not block the write.
- TESTS: 28 new in `tests/integration/test_block_b.py` (27 pass + 1
  T5 skipped without RUN_REAL_BEDROCK). 18 original + 10 finding-lock
  tests added after Codex iter 1. Plus 3 mock signature updates in
  `tests/integration/test_subagent.py` to accept the new kwarg.
- Codex AXIS A/B/C iter 1 (gpt-5.5): APPROVE_WITH_FIXES with 6 findings
  (1 HIGH AU pricing, 1 HIGH dual audit-log paths, 3 MEDIUM, 1 LOW). All
  6 fixed; each has 1+ covering lock test.
- Codex iter 2 (gpt-5.3-codex, focused 6-file prompt): **APPROVE** —
  all 6 fixes verified clean. gpt-5.5 had hung on the same review;
  gpt-5.3-codex (the Codex-CLI-tuned variant) completed in ~6 min /
  27k tokens.
- Codex model rule (codified in BUILDER_PROMPT.md + global CLAUDE.md):
  use `-m gpt-5.3-codex` for ALL Codex reviews — it's the variant the
  Codex CLI was specifically tuned for. gpt-5.5 over-explores file
  reads with `reasoning effort: high` and stalls on prompts >~10 files.
- PORT_LOG #039-#047 + ADR-021. Closes 9 Wave-5-DEEP findings (B-1 +
  B-3..B-11 + B-13 + R4 #14 + R8 #74) + Block-0 ADR-020 remap rows 0-3
  + 0-8.
- Pytest: 469 pass + 5 skip (was 442 + 4 at Block 0; +27 pass + 1 skip).
- verify_ship_zip.py: PASS (100 files / 263.6 KB / 38%).

## v5.0.1-block-0 — `sagemaker_agent.py` shim + notebook smoke gate (2026-05-02)

First Block of the v5.0.1 21-Block build (Mode B autonomous; Codex-only-gate).

- NEW `compact_v5/MAIN/agent/sagemaker_agent.py` (39 LOC): re-exports v5's
  public surface (`Agent`, `BEDROCK_MODELS`, `CONFIG`, `IterationBudget`,
  `SkillManager`, `create_chat_ui`) at the v4-canonical import path.
  Hard-constraint #2 (v4 chat.ipynb works on v5 unchanged) satisfied.
- NEW `tests/integration/test_block0_shim.py` (5 lock tests per
  TEST_DESIGN §Block 0): T1 imports / T1 PS#1 CSO-quiet at WARNING / T3
  notebook smoke gate (cells 1-3 parse + exec under mock_mode) / T2
  widget/console renders / T1 v4 import compat.
- PORT_LOG #038 + ADR-020 added; SYNTHESIS_MASTER §Block 0 head note +
  ADR-020 remap table declare landing Block + lock test for each of
  items 0-1..0-10 (constraint #3 — no deferrals).
- TEST_DESIGN §Block 0 implementation notes added explaining T3 manual
  exec vs papermill choice + T2 ConsoleChatUI fallback contract.
- Tests: 442 pass + 4 skip (was 437 + 4 at v5.0.0; +5 net new).
- verify_ship_zip.py: PASS (96 files / 249.0 KB / 38%).
- Codex AXIS A/B/C: APPROVE (iter 2 after 3 fixes from iter 1 —
  UNDECLARED_PATTERN, test-design drift, PORT_LOG #036 typo all closed).

## v5.0.0 — Build candidate, SHIP BLOCKED (2026-04-30)

> User verdict: **operation FAILED.** All four verification questions
> returned unsatisfactory answers. v5 deferred features without
> permission and did not meet V5_PLAN.md success metric #1 (functional
> parity with v4.10.10). See `_status/V5_SHIP_CRITIQUE.md` for the full
> failure analysis and the v5.0.1 patch agenda.
>
> The 14-phase build mechanically closed all internal gates (tests,
> audit, parity, Codex). The build is preserved at git tag `v5.0.0` for
> traceability, but should NOT be treated as a release until the v5.0.1
> patch (Compactor + TokenTracker + exec-limit enforcement + skill
> name-mismatch fix + real-Bedrock smoke + parity UX) lands.

SageMaker-native re-implementation of Runnable Claude Code. Built across
14 phases (00 → 13, plus 08.5 hard parity gate). Per-phase changelogs at
`MAIN/changelogs/CHANGELOG_v5_phase_NN.md`. Every phase Codex-reviewed
with all flagged issues fixed in same commit + lock tests.

### Phases

- **Phase 00** — Scaffold + ADR/PORT_LOG doctrine + canonical Phase ID.
- **Phase 01** — BedrockClient + Config (verbatim port from v4).
- **Phase 02** — Tool Protocol + registry + plan-mode allowlist + MCP filter.
- **Phase 03** — Core read-only tools (read_file / grep / glob / list_dir).
- **Phase 04** — Core mutating tools + diff_widget approval UX.
- **Phase 05** — bash + python_exec + security/ package (134-case verbatim).
- **Phase 06** — 19-section prompt @ ≤ 2500 tokens + cache-break detection.
              **PS Issue #7 fix**: tool_classes promoted to slot 2.
- **Phase 07** — ToolSearchTool deferred loading (~770 tokens/turn savings).
- **Phase 08** — QueryEngine + retry + errors + IterationBudget (PS Issue #2 data model).
- **Phase 08.5** — Thin-slice parity gate (10/10 critical scenarios).
- **Phase 09** — Sub-agent + Task tool with shared IterationBudget.
- **Phase 10** — Skills + auto-trigger + Hermes filter.
              **PS Issue #1 fix**: skills filtered by available tools.
- **Phase 11** — Notebook UX + entry + thinking/budget UI.
              **PS Issue #2 fix**: visible IterationBudget widget.
              **PS Issue #4 fix**: visible thinking budget widget.
- **Phase 12** — Parity tests vs v4: 15/15 critical + 10/10 non-critical PASS.
- **Phase 13** — Cutover + ship zip + tag v5.0.0 (this release).

### Final state

- **Tests**: 437 pass + 4 skip.
- **Static prompt**: 2498 tokens (within 2500 budget; 45% reduction vs v4 ~5000).
- **Per-turn schema**: ~3230 tokens (vs Phase 6 baseline ~4000; ~770/turn saved).
- **Tool count**: 14 (vs v4 ~30 — flatter surface).
- **Skill count**: 10 production skills (byte-for-byte from v4).
- **PS Issues resolved**: #1 (Hermes filter), #2 (visible budget), #4 (visible thinking), #7 (tool_classes promotion).
- **PORT_LOG**: 37 rows / 19 ADRs / aggregate audit 7/7 metrics PASS.

### Codex review record

Every phase Codex-reviewed (gpt-5.3-codex via stdin). Findings:
- **Phase 06**: 1 major + 2 minor + 1 nit → all fixed.
- **Phase 07**: 4 BLOCKERS → all fixed with lock tests.
- **Phase 08**: 4 findings (cross-run reset, plan-mode bypass) → all fixed.
- **Phase 09**: 7 findings (depth threading, immutability, agent-type) → all fixed.
- **Phase 10**: 9 findings (BLOCKER runtime integration) → all fixed.
- **Phase 11**: 5 findings (CONFIG threading, fallback rendering) → all fixed.
- **Phase 12**: gate-only, no production code.
- All others: clean APPROVE first pass.

### What v5 is NOT

- NOT a v4 replacement on `main` (v4 stays untouched).
- NOT auto-deployed (user explicitly tags + ships).
- NOT a refactor — sibling implementation with clean port map.

### Hard constraints (preserved from v4)

- Bedrock-only (no Anthropic API; uses boto3 `bedrock-runtime`).
- No GitHub network at runtime (local git only inside SageMaker).
- `python_exec` is the canonical Python execution tool (NOT bash python).
- Ships as flat zip — `chat.ipynb` runs without `pip install` of a v5 package.
- All 10 v4 production skills preserved byte-for-byte.
- All v4 destructive-command coverage preserved verbatim (134-case).

### Acceptance gates (V5_PLAN.md success metric)

- [x] Functional parity with v4.10.10 (Phase 12: 15/15 + 10/10 PASS).
- [x] Static system prompt ≤ 2500 tokens (2498 actual).
- [x] Per-turn token overhead ≥ 3000 lower than v4 (deferred-loading active).
- [x] Runnable patterns FAITHFUL or FAITHFUL-WITH-JUSTIFIED-ADAPTATION (no DRIFTED).
- [x] `pytest -q` green (437 pass + 4 skip).
