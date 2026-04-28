# SESSION STATE — sagemaker-coding-agent

## 2026-04-28 — V4.10.4 Release: Sub-agent work-context handoff (closes largest review gap)

### Context
After v4.10.3 + final cleanup, user's Codex follow-up review pointed out the most important remaining weak spot: **sub-agents only got env-details (cwd / git HEAD / depth) but NOT the work context (current goal, active todos, changed files)**. AGENT_STATUS.md was loaded only at top-level (`subagent_depth==0`) by `_load_project_status()`. If the parent forgot to brief them in the `task` tool's `prompt` argument, sub-agents flew blind on the larger goal.

### V4.10.4 Changes
1. **`_build_subagent_handoff_block()`** — new helper returning a bounded handoff block with three optional sections (each fail-quiet, never-raise):
   - AGENT_STATUS.md slice (capped at `_SUBAGENT_STATUS_MAX_CHARS = 4000`)
   - Active todos via `build_todo_restoration_message()` (capped at `_SUBAGENT_TODOS_MAX_CHARS = 2000`)
   - Last 10 changed file paths from `_RECENT_DIFFS` (paths only, no diff bodies)
2. Wired into `_run_task_tool` AFTER `_build_subagent_env_details` and BEFORE `prompt_suffix` — appended to `sub_prompt` after the cached SYSTEM_PROMPT boundary so the static prompt-cache prefix is preserved unchanged.
3. **`CONFIG.enable_subagent_handoff: bool = True`** — opt-out flag for users preferring v4.10.3 env-details-only behavior.
4. **`_sanitize_handoff()`** — replaces literal `# === DYNAMIC ===` in user-supplied AGENT_STATUS or todo content with `# === DYNAMIC === (sanitized)` so a future cache-splitter implementation can't be fooled by user content.

### Codex review (1 fix round)
- ISSUES (round 1): constants named `_MAX_BYTES` but enforced via Python `str` `len()` (CHARS not BYTES); user-supplied content not sanitized for cache-boundary marker.
- PASS (round 2): both fixed (renamed to `_MAX_CHARS` for truthful naming, added `_sanitize_handoff` on AGENT_STATUS + todos paths, 2 new sanitizer tests).

### Verification
- `test_v410_subagent_handoff.py` — **11/11 PASS**
- Full v4.10.x + regression suite: **85/85 across 9 files** (10 + 6 + 10 + 13 + 5 + 12 + 6 + 11 + 12 v4.9 = 85)

### Why this matters
With v4.10.3 alone, a parent that spawned a `verify` sub-agent and forgot "the goal is X, see AGENT_STATUS.md Plan section" got a verify agent that probed whatever files looked interesting — easy to miss the actual point. With v4.10.4 the sub-agent always gets cwd + git + AGENT_STATUS goal + todos + changed files, regardless of what the parent's prompt says. Closes the largest remaining gap from the production-readiness review.

### Version: 4.10.3 → 4.10.4

### Round-6 doc-polish (post-v4.10.4)
User flagged remaining stale references after v4.10.4 ship: "22/23 tools" and "V4.10.3" in HTML/doc banners. Cleaned in this pass:
- PRODUCTION_READINESS_STATUS.md header V4.10.3 → V4.10.4
- RUNNABLE_APPLICABILITY_REVIEW.md target V4.10.3 → V4.10.4 + status block extended with v4.10.4 entry
- v3_architecture.html: all v4.10.2 markers → v4.10.4 (was stuck two versions behind), tool count 22 → 23
- PS_FLOWCHART_V4.html: V4.10.2 → V4.10.4 + subtitle expanded with v4.10.2/3/4 narrative
- PS_DEEP_DIVE_RUNNABLE.html: banner extended to describe v4.10.0/1/2/3/4 (was v4.10.0/1/2)
- HERMES_VS_CODING_AGENT.html: banner extended with v4.10.3 + v4.10.4 entries
- USER_GUIDE.md: 22 tools → 23 tools (literal)

Legacy docs left unchanged (intentional — historical V3-era / pre-v4.10 analysis):
- Documentations/[CRITICAL]_V4_TOKEN_EFFICIENCY.md
- PS_ClaudeCode_Insights/[CRITICAL]_V4_TOKEN_EFFICIENCY.md
- MAIN/tests/competition/COMPETITION_RESULTS.md
- gap_analysis_v4_vs_runnable.md


## 2026-04-28 — V4.10.3 Release: Codex production-readiness review apply

### Context
User pasted a Codex production-readiness review filtered for the SageMaker self-use target. Audit showed 14 of 18 "must learn / apply" items were already done in v4.10.2; 4 small additions worth applying. All additive — zero functional code changes to existing paths.

### V4.10.3 Changes
1. **Ship-gate verifier** — new `compact_v4/verify_ship_zip.py` script. Asserts: 5 required runtime files at root, 9 required skill subfolders with SKILL.md, no forbidden artefacts (test tempdirs, caches, .proposed/, MAIN/agent wrapper, .pyc/.swp/.DS_Store), version sanity (4.10.x), required v4.10.x features present (notebook_edit, context_collapse, enforce_verify_contract, BEDROCK_MODEL_CONTEXT_WINDOWS, skill auto-trigger default OFF), Sonnet 4.5 default, no deep wrapper directories outside skills/. Exit 0 = ship-ready, exit 1 = blocker.
2. **Cache-boundary regression test** — new `MAIN/agent/test_v410_cache_boundary.py`. 6 tests guarding the static prompt prefix: marker presence, ≥1024-token threshold, byte-stability across calls, sub-agent prefix matches parent, dynamic content lives ONLY after boundary, BedrockClient boundary constant matches test constant.
3. **Many-skill stress test** — extended `test_v410_skill_listing_budget.py` with `test_many_skill_workspace_stress`. Verifies cap behavior at 100 and 1000 skills.
4. **Clearer permission denials** — `SecurityManager.validate_command` denial messages now include WHY (allowlist), closest-prefix suggestion, and recommended Python tool alternative. Pattern denials include the matching pattern and recovery hint.

### Test/live split confirmed
Already correctly gated. Deterministic tests in `MAIN/agent/test_v410_*.py` (no Bedrock, fast, run on every change). Live Bedrock tests in `MAIN/tests/test_production.py` (manually invoked, not part of the v4.10.x regression run).

### Verification
- Full v4.10.x + regression suite: **74/74 across 8 files** (10 + 6 + 10 + 13 + 5 + 12 + 6 cache-boundary + 12 v4.9 auto-trigger = 74)
- `verify_ship_zip.py` PASSES on the freshly-rebuilt zip
- Codex review pre-commit: PASS

### Version: 4.10.2 → 4.10.3

### Final docs/working-tree cleanup (Codex round 4)
After v4.10.3 shipped (commit 6f56e48), Codex flagged 3 remaining gaps:
- PRODUCTION_READINESS_STATUS.md still said V4.10.0 / 159 tests. Updated to V4.10.3 / 160 deterministic tests / known-limitations section addressing the 4 weak spots Codex called out (no ToolSearch deferred-schema, simpler Todo, prompt-dependent sub-agent handoff, no Runnable benchmark trace).
- RUNNABLE_APPLICABILITY_REVIEW.md still targeted V4.9.7. Updated to V4.10.3 with v4.10.0/1/2/3 status by-version note.
- Working tree had untracked v4.9.6/v4.9.7 in-flight items: per-version changelogs (CHANGELOG_v4.9.6.md, CHANGELOG_v4.9.7.md), test_v493_enhancements / test_v49_auto_trigger / test_v42_gap_closure modifications, _rebuild_zip.py + V4_8_SKILL_AUTOTRIGGER_AUDIT.md doc updates. All committed in this cleanup pass. analyze_*.py scratch files added to .gitignore.

Outstanding (deliberately deferred, documented as caveats):
- Live Bedrock smoke test on real SageMaker (user-side, out of scope for me)
- Long-task token-cost benchmark vs Runnable (out of scope; cache-boundary test proves cache *can* activate, hit-rate measurement is a separate exercise)

### Round-5 hygiene (final gitignore sweep)
After c3a70ba, the agent kept leaving runtime artefacts in MAIN/ and MAIN/tests/ subdirs (`.exec_budget.json`, `.snapshots/`, `.tool_cache/`, `analyze_sales.py`, `refactor_me.py` scratch). Existing .gitignore rules only matched the top-level paths. Generalised to `**/.snapshots/`, `**/.tool_cache/`, `**/.exec_budget.json`, `compact_v4/**/analyze_*.py`, `compact_v4/**/refactor_me.py`. Working tree now clean except the unrelated `_archive` submodule pointer drift. Pure repo hygiene; no code change.


## 2026-04-28 — V4.10.2 Release (Codex-surfaced contradiction fix): verify-contract softened

### Context
After v4.10.1 shipped, user asked detailed production-readiness questions about subagents/skills/teams and pushed for another Codex review. Codex confirmed the layered safety (no keyword auto-spawn, no team-coordination vestiges, context_collapse wired correctly) BUT surfaced a real contradiction in the system prompt: the Sub-agent Coordination + Verification Contract sections said verify was MANDATORY after 3+ logic edits, while the Doing Tasks section said SUGGEST and don't auto-run. Model behaviour was unpredictable depending on which sentence won attention. Also caught: a stale "Haiku default" comment in the model dropdown.

### V4.10.2 Changes
1. **Verify-contract softened.** All three system-prompt sections (Sub-agent Coordination, Verification Contract, `verify` agent type description in `task` tool) now align: SUGGEST `/verify` after 3+ logic-changing edits, wait for user confirm, do NOT auto-spawn unless `CONFIG.enforce_verify_contract=True`.
2. **`CONFIG.enforce_verify_contract: bool = False`** — new opt-in flag for production-discipline workflows. Default OFF means casual self-use sessions don't get over-spammed with verify subagents.
3. **Stale comment fix.** "Model selector — default to Haiku" comment updated to reflect v4.10.1's Sonnet 4.5 default.

### Codex review record (this session)
- Pre-fix: Codex flagged the contradiction explicitly + the stale comment + 1 minor wording drift.
- Post-fix: PASS expected (no functional code change, prompt-only edits + 1 config flag).

### Verification
- 67/67 tests still green (no functional change)
- `CONFIG.enforce_verify_contract` defaults False, sanity-check confirms

### Version: 4.10.1 → 4.10.2

### Final consistency sweep (Codex round 2 + manual round 3)
After the initial v4.10.2 fix, a second Codex pass found three remaining inconsistencies:
- L6686 todo_write nudge still said "you should spawn verify" (verbiage from old MANDATORY rule). Softened to "SUGGEST /verify and wait for confirmation; only auto-spawn if CONFIG.enforce_verify_contract=True".
- chat.ipynb cell 0 title still said V4.10.1; bumped to V4.10.2 + new highlight bullet for the verify-contract softening.
- v3_architecture.html and PS_FLOWCHART_V4.html still had v4.10.1 markers; bumped to v4.10.2.
All fixed in the same v4.10.2 commit.

A third manual sweep (during user's 6-question audit) caught two more:
- v3_architecture.html L215 narrative had over-replaced "v4.10.1" with "v4.10.2" — reframed correctly: v4.10.0 = 5 phases, v4.10.1 = Context Collapse + Sonnet, v4.10.2 = verify-contract softening.
- HERMES_VS_CODING_AGENT.html and PS_DEEP_DIVE_RUNNABLE.html banners still said "v4.10.0 update" only; now describe all 3 v4.10.x same-day releases.


## 2026-04-28 — V4.10.1 Release (same-day follow-up): Context Collapse + default Sonnet 4.5

### Context
After v4.10.0 shipped (commit 213528a), user asked to fix the deferred #41b Context Collapse now (no v4.11 wait) and switch the default model from Haiku 4.5 to Sonnet 4.5.

### V4.10.1 Changes
1. **#41b Context Collapse (segment-level):** new `context_collapse(messages)` walks oldest-to-newest, finds runs of 3+ consecutive stale tool round-trips (assistant tool_use + user marker-only tool_result, where marker is what microcompact produces), and replaces each run with a 2-message synthetic pair (assistant ack + user "continue") so Bedrock role alternation is preserved. Wired into BOTH the proactive 70%-trigger path (after microcompact) AND the reactive-compact path. Strict classification:
   - any assistant block type other than `text` / `tool_use` (thinking / image / document / etc.) blocks the collapse — never drops signal
   - marker match is exact equality (not substring) so a real tool result containing the marker text is never misclassified as stale
2. **Default model: Haiku 4.5 → Sonnet 4.5** (`au.anthropic.claude-sonnet-4-5-20250929-v1:0`). Cost note: ~10x per-token, but prompt-cache checkpoint threshold drops 4096 → 1024 tokens so caching activates earlier and offsets some of the cost. `BEDROCK_MODELS` reordered with Sonnet 4.5 first.

### Codex review (1 round)
- ISSUES (round 1): unknown assistant block types accepted; marker substring not exact-match.
- PASS (round 2): both fixes applied + 2 new tests (`test_thinking_block_protects_from_collapse`, `test_marker_substring_in_real_result_not_collapsed`).

### Verification
- `test_v410_context_collapse.py` — **12/12 PASS**
- Full v4.10.x + regression suite: **67/67 across 7 files** (9 + 6 + 10 + 13 + 5 + 12 v4.10.x = 55, plus 12 v4.9 auto-trigger regression = 67)
- Default-model sanity: `CONFIG.model_id == 'au.anthropic.claude-sonnet-4-5-20250929-v1:0'`, auto-derived `context_max_tokens=200000`

### Version: 4.10.0 → 4.10.1


## 2026-04-28 — V4.10.0 Release: Runnable parity (notebook_edit, skill budget, env-details, context window, reactive compact)

### Context
Deep rescan of `compact_v4` vs `gg-claude-code-runnable` produced a 55-row check table. User asked to fix items #10, #24, #41a, #44, #47 and ship as v4.10.0. #41b (Context Collapse, segment-level summary) deferred to v4.11.0 — non-trivial (~200 LOC), low ROI for self-use.

### V4.10.0 Changes (sagemaker_agent.py + tests + docs + HTMLs + zip)

Five additions, each with its own per-phase Codex review (gpt-5.3-codex, read-only). Codex caught 9 real correctness issues across the five phases; all fixed and re-verified before any phase advanced.

1. **#24 Skill listing token budget cap** — `SkillManager.list_for_prompt` caps the listing at 1% of context window, hard-clamped at 2000 tokens. Hint reserve computed upfront so the cap is strict on every path including degenerate "no name fits". Auto-trigger surfacing also caps each description at 250 chars. Mirrors Runnable `SKILL_BUDGET_CONTEXT_PERCENT`. **9/9 tests.**

2. **#47 Per-sub-agent env-details** — `_build_subagent_env_details` injects 4–6 line block (agent type, depth/max, workspace cwd, git HEAD, working-tree status) into every sub-agent prompt AFTER the cached SYSTEM_PROMPT boundary. 5s timeout per git probe, fail-quiet, never raises. Mirrors Runnable `enhanceSystemPromptWithEnvDetails`. **6/6 tests.**

3. **#44 context_window auto-derive from model_id** — new `BEDROCK_MODEL_CONTEXT_WINDOWS` map covers every Bedrock model in `BEDROCK_MODELS`. `CONFIG.context_max_tokens` auto-derives from model_id at startup; `agent_config.json` override wins (validated as positive int, NOT bool-as-int). When AWS exposes 1M variants the only change is one entry in the map. **10/10 tests.**

4. **#10 notebook_edit surgical .ipynb cell tool** — insert / replace / delete one cell. Atomic write (tmp + rename), preserves cell `id` on replace, resets `execution_count`/`outputs` on code cells. Always returns `Error:` string never raises (broad `Exception`, not just `OSError`). One-line system prompt addition tells the model to prefer `notebook_edit` over `create_notebook` for existing notebooks. Mirrors Runnable `NotebookEditTool`. **13/13 tests.**

5. **#41a Reactive Compact on CONTEXT_OVERFLOW** — when Bedrock rejects with "prompt is too long" / "too many tokens" / "input is too long", agent runs microcompact (or placeholder-summary fallback if microcompact freed less than `MICROCOMPACT_MIN_SAVINGS` — deliberately NO additional LLM call), clears file-read state, sets `_cache_broken_by_compact` (both branches), and retries the same request once. Cap: 1 reactive recovery per `run()` call. Other error categories surface unchanged. Retry stop-check mirrors original token-billing parity. Mirrors spirit of Runnable `reactiveCompact`. **5/5 tests.**

### Skill auto-load STILL DEFAULT OFF
The v4.9.6 fix is intact (both `CONFIG.enable_skill_auto_trigger` and per-skill frontmatter `auto_trigger` default False). `test_v49_auto_trigger.py` regression: **12/12 still green**.

### Codex issues caught & fixed (per phase)
1. Phase 1: first-entry-over-budget overshoot (loop guard)
2. Phase 1: truncation hint cost not budget-accounted (upfront reserve)
3. Phase 1: degenerate-budget overshoot (hint-only path bounds check)
4. Phase 3: invalid JSON value froze default (validate type before honour)
5. Phase 3: `bool`-as-`int` JSON trap (explicit `isinstance bool` exclusion)
6. Phase 3: weak e2e test (rewrote with injected fake-model + window=1.5M)
7. Phase 4: narrow `OSError` catch on notebook write (broadened to `Exception`)
8. Phase 5: file-read state cleared only on placeholder branch (now both)
9. Phase 5: retry stop-check missing `TOKENS.add` (parity with original)

### Verification
- 55/55 new V4.10.0 tests across 5 files all green (9 + 6 + 10 + 13 + 5 + 12 v4.9 regression = 55 + 12 = **67/67**)
- Cache integrity preserved: every dynamic addition lives AFTER the `# === DYNAMIC ===` boundary; cached SYSTEM_PROMPT prefix is byte-identical across turns
- System prompt grew by 2 lines total (one in `# Documents` for `notebook_edit`, one updating tools comment) — small-model friendly
- compact_v4.zip rebuilt: 57 files / 245.7 KB / runtime-only (no test files in ship)
- HTML reports updated: `v3_architecture.html` (full v4.10.0 section), `PS_FLOWCHART_V4.html` (banner + stats), `PS_DEEP_DIVE_RUNNABLE.html` (Runnable-parity callout), `HERMES_VS_CODING_AGENT.html` (banner)
- Live status doc: `compact_v4/docs/V4_10_0_PLAN.md`
- CHANGELOG updated with full v4.10.0 entry

### Net code change
+2164 / -62 across 15 files. New constants: `SKILL_LISTING_BUDGET_PERCENT`, `SKILL_LISTING_DESC_CAP`, `SKILL_LISTING_HARD_CAP_TOKENS`, `_SUBAGENT_ENV_GIT_TIMEOUT_S`, `BEDROCK_MODEL_CONTEXT_WINDOWS`, `DEFAULT_CONTEXT_WINDOW`. New helpers: `_build_subagent_env_details`, `_normalise_ipynb_source`, `_auto_derive_context_window`, `resolve_context_window`, `tool_notebook_edit`. New tool registered: `notebook_edit`.

### Version: 4.9.7 → 4.10.0

### Follow-up doc commit (same day)
After commit 213528a shipped, the live status doc `compact_v4/docs/V4_10_0_PLAN.md` was finalized with: all 5 phases + HTML/Doc/Ship/Push/Re-review marked DONE; per-phase Codex record table; closed-gap roster (5 of 6); deferred-to-v4.11.0 note (#41b Context Collapse); post-ship deep re-review verdict (v4.10.0 ≥ Runnable on every dimension that matters for self-use SageMaker); cache integrity / Haiku-friendliness / metrics correctness / skill-load safety all verified. No code changes — doc-only.


## 2026-04-23 — V4.9.5 Release: self-patching skills with safety rails (opt-in, handy use)

### Context
After v4.9.4, user re-classified the deployment scope: NOT insurance-only — this is for handy/personal use. The previously-rejected hermes self-patching pattern came back on the table. Designed with 4 (now 8) safety rails so user stays in control of every change. Opt-in via `CONFIG.enable_skill_patching = True` (default OFF).

### V4.9.5 Changes (sagemaker_agent.py + skills + docs)
1. **CONFIG.enable_skill_patching: bool = False** — opt-in flag for the whole feature
2. **SkillManager.propose_patch / list_proposals / get_latest_proposal / apply_proposal / reject_proposal** — full lifecycle methods using `skills/<name>/.proposed/<timestamp>.md` convention
3. **`_log_skill_patch_event()` helper** — JSONL audit log at `audit_logs/skill_patches.jsonl`
4. **New `tool_skill_propose_patch`** registered in TOOLS (no-ops when flag is OFF)
5. **Three new slash commands**: `/skill suggestions`, `/skill apply <name> [--yes|--edit]` (with unified diff preview), `/skill reject <name>`
6. **SYSTEM_PROMPT** gains "Skill self-patching (V4.9.5, opt-in)" section: only propose when flag on AND user corrected 3+ times
7. **USER_GUIDE.md** gains "Self-patching skills" section with full example session + safety-rails table
8. **chat.md + chat.ipynb** cell 0 + cell 4 — version banner bumped to v4.9.5, v4.9.X highlights, new commands documented
9. **Version**: 4.9.4 → 4.9.5

### Safety rails (8 total)
1. Default OFF (`CONFIG.enable_skill_patching = False`)
2. Propose-not-apply (`.proposed/<ts>.md`, never live)
3. Diff preview before apply (unified diff format)
4. Snapshot before apply (existing SNAPSHOTS → `/revert <path>` undoes)
5. Audit log per event (JSONL)
6. `--edit` flag for tweaking proposed file
7. Empty-name validation
8. Tool no-ops when flag is OFF

### Verification
- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version `4.9.5`
- `test_v495_self_patching.py` (NEW) — **19/19 PASS**
- All regression: **92/92 total tests green** (1 + 9 + 11 + 10 + 11 + 32 + 19)
- No Codex this round (per project rule)

### Net code change
~370 lines added across SkillManager, tool, slash handlers, audit log helper, SYSTEM_PROMPT addition, plus ~250 lines test, plus markdown updates to USER_GUIDE.md / chat.md / chat.ipynb.

## 2026-04-23 — V4.9.4 Release: hermes patterns (cost ceiling + structured errors + smarter compaction)

### Context
After v4.9.3 user pushed back: had we really learned agent coordination + self-healing + memory/context management from hermes? Honest audit said no — IterationBudget, ErrorClassifier, jittered backoff, pre-compact pruning, auxiliary-model compaction, and structured summary were all real-value patterns I had wrongly deferred to "v4.10". User said "i want comeple udapgate of v4". v4.9.4 closes those 6 gaps.

### V4.9.4 Changes (sagemaker_agent.py)
1. **IterationBudget** class + Agent.iteration_budget kwarg + Agent.run() consume per turn + sub-agent inheritance. Default 90 via CONFIG.max_iteration_budget. Stops runaway sub-agent cost.
2. **BedrockErrorCategory enum + ErrorClassifier**. ~10 Bedrock SDK categories with explicit recovery: throttle / validation-cache / validation-other / context-overflow / model-not-ready / model-timeout / access-denied / service-unavailable / transient-network / unknown.
3. **RetryPolicy** jittered exponential backoff (base=1s, cap=30s, max=4). Wired into BedrockClient.chat() via classify → retry-or-raise loop. Cache-validation fallback preserved as one-shot inside the same loop.
4. **Compactor._prune_tool_results_for_summary** — pre-LLM cheap pass trims oversized tool_result (head 800 + tail 400, threshold 2000). Idempotent. Doesn't mutate input. Handles both string and list forms.
5. **Compactor._summary_client + CONFIG.compaction_model** — opt-in auxiliary model for compaction. Default empty = use main. Aux clients cached per model_id. Token tracking charges aux model when used.
6. **Compactor.create_summary_prompt** gains "Resolved Questions" + "Pending Questions" sections (10, 11). Existing 9 sections preserved.
7. **Version**: 4.9.3 → 4.9.4

### New tests
- `test_v494_hermes_patterns.py` — 32 tests across 6 sections + cross-cutting Agent constructor checks

### Verification
- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version `4.9.4`
- **73/73 deterministic tests green** (1 + 9 + 11 + 10 + 11 + 32) across all suites
- Smoke-tested all 6 items: IterationBudget exhaust, all 10 ErrorClassifier categories, RetryPolicy decisions, pruning preserves small/trims large, aux client returns main when unconfigured, summary template has Resolved + Pending
- No Codex this round (Bedrock-only patch — per `feedback_codex_skip_bedrock_patches.md`)

### Net code change
+336 / -33 lines in sagemaker_agent.py. 1 new test file (~370 lines, 32 tests).

### Still deferred (genuinely out of scope)
- Session-search via FTS5 + LLM (high cost, unclear demand)
- Permission rule engine (UX redesign)
- Mixture-of-models voting (cost concern, defer until justified)

## 2026-04-23 — V4.9.3 Patch: cross-repo enhancements (Bedrock-only fit)

### Context
After v4.9.2 doc alignment / minimum-ship zip, user requested deep-scan comparison vs `gg-claude-code-runnable`, `hermes-agent`, and `Learning_Factory` to identify enhancements. User clarified hard constraints: **SageMaker + Bedrock-only + no external network from insurance company**. That filter rejected MCP, OpenRouter, multi-platform messaging, self-patching skills upfront. Pre-implementation scan revealed doom-loop detection already exists (line 7368), so that candidate was dropped too. Final scope: 5 small enhancements, all local-only.

### V4.9.3 Changes (sagemaker_agent.py + skills)
1. **Prompt-injection scanner** (`_scan_for_prompt_injection`) — wired into `_load_persistent_memory()`, `load_project_instructions()`, `SkillManager.read_skill()`. Patterns: instruction-override, role-hijack, fake `<system-reminder>` / `<important-instructions>` tags, exposed AWS/API credentials, invisible/format-confusion chars (Unicode TS#36). Advisory-only `[INJECTION-SCAN]` warnings via `logging.warning()`.
2. **CSO description validator** in `SkillManager.discover()` — `[CSO-CHECK]` warning when a skill's frontmatter description text doesn't start with "Use when". Insurance-side cleanup target — 9 of 10 currently-shipped skills will warn.
3. **New `skills/reflexion/SKILL.md`** — 3-pass critique-refine-judge loop. Slash-only (`auto_trigger: false`). CSO-compliant.
4. **SYSTEM_PROMPT "Handling Critique" section** gains spec-first ordering bullet — address spec/correctness BEFORE code-quality findings.
5. **Version**: 4.9.2 → 4.9.3

### Verification
- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version `4.9.3`
- `test_v493_enhancements.py` (NEW) — **11/11 PASS** (8 scanner + 2 CSO + 1 reflexion-discovery)
- All regression: **41/41 total tests green** (1 path_fix + 9 v4.7.1 + 11 v4.9 + 10 v4.9.1 + 11 v4.9.3)
- No Codex review (per project rule for Bedrock-only patches that don't touch general algorithms)
- Self-review: forward-reference of `_scan_for_prompt_injection` from `read_skill` (line 2294) to module-level helper (line ~6286) verified to resolve at runtime via Python's name resolution

### Rejected (so future-you doesn't re-litigate)
- MCP integration — external network not allowed
- OpenRouter / provider fallback chain — external network not allowed
- Multi-platform messaging gateway — wrong UX target (SageMaker notebook only)
- Self-patching skills — insurance compliance frowns on agent-modified runtime artefacts
- Multi-stage compaction — current single-stage is adequate
- Mixture-of-models voting — cost concern, defer until justified
- Error classifier — defer to v4.10 (significant work)
- Permission rule engine — defer to v4.10 (bigger feature)

## 2026-04-23 — V4.9.2 Patch: doc alignment + minimum-ship zip

### Context
v4.9.1 production-readiness scan flagged 3 doc gaps (D1, D2, D3): `/unskill` was implemented but not documented in user-facing docs (USER_GUIDE.md, chat.md) or the agent's own SYSTEM_PROMPT command list. Also surfaced: shipping zip carried test files, dev artefacts, internal audit docs, and runtime caches not needed in production. Both addressed in this patch.

### V4.9.2 Changes
- **USER_GUIDE.md**: command table gained `/unskill` row; workflow block updated; sticky-deactivation behaviour documented on `/skill clear` and `/unskill`
- **chat.md**: slash-commands table gained `/unskill` row
- **SYSTEM_PROMPT** ([sagemaker_agent.py:6629](compact_v4/MAIN/agent/sagemaker_agent.py)): `# Commands` line gained `/skills`, `/skill use`, `/skill clear`, `/unskill` so agent self-knowledge is complete
- **`_rebuild_zip.py`**: tightened to minimum-ship profile — drops `test_*.py`, `TEST_LOG.md`, `v3_architecture.html`, `V4_NOTES.md`, `docs/*` audit, `.gitignore`, `.git/`, `__pycache__/`, `.pytest_cache/`, `.snapshots/`, `.code_index/`
- **Version**: 4.9.1 → 4.9.2

### Zip shape
- v4.9.1: 40 files, 321 KB
- v4.9.2: **25 files, 239 KB** (25% smaller, dev clutter removed)

### Verification
- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version reports `4.9.2`
- 30/30 tests still green (11 v4.9 + 10 v4.9.1 + 9 v4.7.1)
- Zip extracted, `__version__ = "4.9.2"` confirmed inside zip
- Manual zip listing reviewed — no powerbi, no test files, no dev artefacts

## 2026-04-23 — V4.9.1 Patch: /unskill + sticky deactivation + prompt tightening

### Context
v4.9.0 shipped the main audit §6 fix (auto_trigger honoured) earlier today, but audit §8 items #4 (/unskill) and a latent bug in the "Handling Critique" prompt (implicit re-read, missing workspace-absent fallback, no concise-ACCEPT exception) remained. Also during diff review of v4.9.1, one logic bug was caught: `/unskill <nonexistent>` silently accepted junk names. All resolved here.

### V4.9.1 Changes (sagemaker_agent.py)
- **New `/unskill <name>` command** — per-skill deactivation, validates against `SKILLS._cache`, rejects nonexistent names with the available list
- **Sticky deactivation** — new `ui_state["deactivated_skills"]` set. `/unskill` and `/skill clear` populate it. Auto-match loop skips any member. `/skill use <name>` lifts the block for that skill. New Session button resets the set.
- **SYSTEM_PROMPT "Handling Critique" tightened**:
  - "Re-open the source file" → "Call `read_file` on the source being discussed" (concrete tool call)
  - New fallback line for critiques of code not in the workspace
  - ACCEPT label now says: state concisely for clear-cut critiques, don't pad evidence
- **Logic bug fixed during diff review**: `/unskill <nonexistent>` no longer silently adds junk to deactivated set
- **Version**: 4.9.0 → 4.9.1

### New files
- `compact_v4/MAIN/agent/test_v491_unskill.py` — 10 tests covering /unskill, sticky deactivation, /skill use re-enable, auto-match skip, new-session reset
- `compact_v4/MAIN/changelogs/CHANGELOG_v4.9.1.md`

### Verification
- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version reports 4.9.1
- **30/30 tests green**: 11/11 v4.9 + 10/10 v4.9.1 + 9/9 v4.7.1 regression
- Diff re-read: 1 logic bug caught and fixed before shipping (validation missing)
- **No Codex review** this round — per user direction: Codex is a generic code-review tool, adds little for patches touching Bedrock agent UI handlers + prompt text. Self-review covers it.

### Audit §8 status after v4.9.1
| # | Item | Status |
|---|---|---|
| 1 | Thinking-mode temp=1 | Out of scope — Bedrock API constraint, cannot override |
| 2 | Re-read source rule | **DONE** (v4.9.0), tightened v4.9.1 |
| 3 | Partial-agreement scaffold | **DONE** (v4.9.0), tightened v4.9.1 |
| 4 | `/unskill` command | **DONE** v4.9.1 |
| 5 | Skill injection char count | **DONE** (v4.9.0) |

## 2026-04-23 — V4.9.0 Release: skill auto_trigger fix + critique-handling rule

### Context
V4.8.0 shipped `auto_trigger: false` as a frontmatter flag to disable keyword auto-discovery of skills, but the implementation was incomplete: the parser gated only the local `_triggers` variable, not the actual auto-match loop in `create_chat_ui`. Consequence: clara-review (and every other skill with `auto_trigger: false`) still auto-activated whenever the user message substring-contained the name words. Surfaced by 2026-04-23 debate case study where `Clara_WIP/foo.ipynb ... peer review` silently injected ~8000 chars of ClaRA audit methodology into the prompt, contaminating a Textract/Bedrock review.

### V4.9.0 Changes (sagemaker_agent.py)
- **SkillInfo.auto_trigger field** added (default True), populated by parser
- **Auto-match loop now honours auto_trigger: false** — skills with the flag are skipped by the keyword matcher
- **Word-boundary keyword match** — switched from substring `in` to token-set `issubset`. "review" no longer matches "unreviewable"; "clara" no longer matches "Clara_WIP" via bare `in`. Same regex (`[a-z0-9]+`) used on both sides so non-hyphen separators (qa_review, docs.v2) match consistently — fix applied after Codex review flagged the tokenization mismatch.
- **Dead `phrase_hit` branch removed** — `phrase = s_name.replace("-", " ")` made that branch a weaker duplicate of the main one, never fired independently.
- **SYSTEM_PROMPT: "Handling Critique of Your Own Work" section** — re-read source before defending, per-point ACCEPT/PARTIAL/REJECT with evidence, treat pasted critique as user message not tool output. Addresses the sycophancy-at-temp=0 / paranoia-at-temp=1 swing observed in the debate case study.
- **Auto-match banner includes char count** — `Auto-matched skill: clara-review (~8123 chars injected)` so user sees prompt cost.
- **Version**: 4.8.0 → 4.9.0

### New files
- `compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md` — full audit: intent vs reality, 5-defect chain, case study, patch spec, test plan, out-of-scope items
- `compact_v4/MAIN/changelogs/CHANGELOG_v4.9.0.md` — per-change ship log
- `compact_v4/MAIN/agent/test_v49_auto_trigger.py` — 11 tests covering parser, auto-match, word-boundary, non-hyphen separator, discover_relevant, real-skills-dir smoke

### Verification
- `py_compile` / `ast.parse` / `import sagemaker_agent` — clean
- `test_v49_auto_trigger.py` — **11/11 PASS**
- `test_v471_enhancements.py` regression — **9/9 PASS**
- Codex review (`gpt-5.3-codex`, read-only): round 1 flagged tokenization inconsistency → fix applied → round 2 PASS

### Known non-regressions (pre-existing)
- `test_v46_complex.py "Skill discovery works"` FAIL — reproduces on unmodified v4.8.0 master. Caused by v4.8.0 setting `auto_trigger: false` on security-review (its `triggers` became None, so `discover_relevant` correctly skips it). Test is outdated vs post-v4.8 behaviour, not caused by v4.9.

### Out of scope (tracked in audit §8)
- Thinking-mode `temperature=1` calibration (Bedrock API constraint)
- `/unskill <name>` command (existing `/skill clear` + fix covers most cases)
- Hoverable skill chip in UI (char-count in banner is MVP)

## 2026-04-18 — Cleanup: .gitignore cruft patterns

Added `.codex_review/`, `.codex_tmp/`, `*compact_v4.zip`, `package-lock.json`,
`package.json` to stop noise in working tree. Pushed to `sageagent` master.

## 2026-04-18 — Security hardening: .gitignore

Added `.env.*`, `*.pem`, `*.key`, `credentials*.json`,
`service-account*.json` patterns. No code changes. Pushed to `sageagent`.

## Last Session: 2026-04-13 — V4.8.0 Release + PS_Deep E-Book

### V4.8.0 Changes (sagemaker_agent.py)
- All 8 skills: auto_trigger disabled. Skills only activate via /command or explicit request.
  - verify, simplify, review, security-review, batch, coding-standards, clara: auto_trigger: false
  - report: keeps keyword triggers ("create a report") since that's explicit intent
- /done and /verify are no longer auto-forced. Agent suggests them after 3+ file edits, user decides.
- SkillManager: new auto_trigger: false frontmatter support to disable keyword auto-discovery
- [CRITICAL] Chat window resizable (500px default, drag + slider 200-1200px)
- [CRITICAL] Prefer chat answers over file generation (system prompt + per-turn reminder)
- [CRITICAL] CSV/Excel data validation accuracy (system prompt section)
- Security: wget/bash restrictions relaxed (pipe-to-shell still blocked)
- Budget: display-only metric, never stops execution, editable text input
- Harness: post-compact FILE_CACHE.clear_context()
- Harness: per-turn critical reminder injection (system-reminder tags)
- Harness: enhanced cache breakage warning with cost impact
- Version: 4.3.1 → 4.8.0

### PS_Deep E-Book (new)
- PS_ClaudeCode_Insights/PS_Deep/PS_DEEP_DIVE_RUNNABLE.html — 10-chapter standalone e-book
- 8 research docs covering all 2,010 files of Runnable codebase
- Gap analysis: V4 vs Runnable (97% equivalent, 6 actionable gaps → now 3 remain)

### Updated HTMLs
- PS_FLOWCHART_RUNNABLE.html — stats corrected, sub-agent section expanded
- PS_FLOWCHART_V4.html — agent comparison table added

### Hermes vs Coding Agent HTML (new)
- PS_ClaudeCode_Insights/HERMES_VS_CODING_AGENT.html — 7-tab comparison (self-improving vs coding loop)
- Screenshots added to PS_ClaudeCode_Insights/screenshots/
- 2026-04-25: relocated copy added at compact_v4/docs/HERMES_VS_CODING_AGENT.html so it ships with the v4 docs bundle (original was previously committed to winstonpgao/hermes-agent fork; that fork is being flattened back to upstream).

### chat.ipynb cleanup
- Removed coding-standards SKILL.md (merged into main skills)
- Updated chat.ipynb markdown

### Pre-commit hook added
- .git/hooks/pre-commit — rejects files with invalid Unicode (unpaired surrogates)
- Prevents API Error 400 "invalid high surrogate in string"

### compact_v4.zip rebuilt (clean)
- Was 129 files / 3.6MB (included __pycache__, audit_logs, .pytest_cache, truncated_outputs, .benchmarks, .code_index, .snapshots, sessions)
- Now 53 files / 0.4MB — source code, skills, tests, changelogs only

### To Resume
- V4.8.0 needs AWS Bedrock testing before final ship
- Remaining gaps: auto-nudge on 3+ tasks, multi-agent FP filtering, fork cache sharing (blocked on Bedrock)
- Consider adding chat_height_slider to the layout row in chat.ipynb as well
