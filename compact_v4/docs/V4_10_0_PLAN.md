# compact_v4 v4.10.0 — Plan & Live Status

**Started:** 2026-04-28
**Source:** Deep rescan of compact_v4 vs gg-claude-code-runnable (this session)
**Constraint:** SageMaker Bedrock-only, no GitHub, has local git tree, single-file deploy.

---

## Scope

6 fixes from the rescan check table, addressing items #10, #24, #41a, #41b, #44, #47.

---

## Live status (update at every phase boundary)

| Phase | Item | Description | LOC est | Status | Codex verdict | Notes |
|---|---|---|---|---|---|---|
| 1 | #24 | Skill listing token budget cap | ~50 (incl. fixes) | **DONE** | **PASS** (after 2 fix rounds) | Codex caught: first-entry overshoot, hint cost not budgeted, degenerate path overshoot. All fixed. 9/9 tests green. |
| 2 | #47 | Per-subagent env-details injection | ~75 | **DONE** | **PASS** | Codex confirms: spawn safety, cache prefix integrity, Haiku size cap. 6/6 tests green. |
| 3 | #44 | `context_window` config + Bedrock model→window map + threshold rebasing | ~80 (incl. fixes) | **DONE** | **PASS** (after 2 fix rounds) | Codex caught: invalid-JSON freeze, bool-as-int trap, weak e2e test. All fixed. 10/10 tests green. |
| 4 | #10 | `notebook_edit` surgical .ipynb cell tool | ~165 (incl. fix) | **DONE** | **PASS** (after 1 fix round) | Codex caught: write phase narrow-exception (json.dump TypeError could escape). Broadened to Exception. 13/13 tests green. |
| 5 | #41a | Reactive Compact on `CONTEXT_OVERFLOW` (compact + retry once) | ~110 (incl. fixes) | **DONE** | **PASS** (after 1 fix round) | Codex caught: file-read state + cache-broken flag only set on one branch (now both); retry stop path missing usage tracking. All fixed. 5/5 tests green. |
| 6 (v4.10.1) | #41b | Context Collapse (segment-level stale tool summary) | ~100 | **DONE** | **PASS** (after 1 fix round) | Collapses 3+ consecutive already-microcompacted tool round-trips into a synthetic Bedrock-safe pair. Codex caught: unknown assistant block types accepted; marker substring not exact. Both fixed. **12/12 tests green.** |
| HTML | — | Update v3_architecture.html, PS_FLOWCHART_V4, PS_DEEP_DIVE_RUNNABLE, HERMES_VS_CODING_AGENT | — | **DONE** | — | All 4 updated with v4.10.0 banner / section / stats |
| Doc | — | CHANGELOG.md, USER_GUIDE.md, SESSION_STATE.md | — | **DONE** | — | v4.10.0 entries added to all three |
| Ship | — | rebuild compact_v4.zip (runtime-only) | — | **DONE** | — | 22 files / 234.6 KB / runtime-only, flat root layout |
| Push | — | commit + push to sageagent remote | — | **DONE** | — | commit 213528a; +2215 / -62 across 16 files |
| Re-review | — | Post-ship deep re-review vs Runnable | — | **DONE** | — | See "Outcome" section below |

---

## Workflow rules (per CLAUDE.md)

1. Phase = code → unit test → `git diff` self-review → Codex review (gpt-5.3-codex, read-only sandbox).
2. Codex 100% pass required before next phase. Exceptions: prompt-template-only changes (per `feedback_codex_skip_bedrock_patches`).
3. After all 5 phases ship green: HTML updates, doc updates, zip rebuild, final diff.
4. No version bump until phases 1–5 all pass and zip rebuilt.
5. Update this status table after each phase.

---

## Phase 1 — #24 Skill listing token budget

**File:** `MAIN/agent/sagemaker_agent.py` — `SkillManager.list_for_prompt` (~L2621-2628).
**Current behavior:** dumps `"Available: " + ", ".join(self._cache.keys())` (no budget).
**New behavior:** cap listing at `min(SKILL_LISTING_BUDGET_PERCENT * context_window, SKILL_LISTING_HARD_CAP_TOKENS)`. Per-skill description capped at 250 chars (Runnable parity).
**Constants added at module top:**
- `SKILL_LISTING_BUDGET_PERCENT: float = 0.01` (1% of context, mirrors Runnable)
- `SKILL_LISTING_DESC_CAP: int = 250`
- `SKILL_LISTING_HARD_CAP_TOKENS: int = 2000` (safety upper bound)

**Test:** `test_v410_skill_listing_budget.py` — 3 cases (under-cap pass-through, over-cap truncation, desc-trim per skill).

---

## Phase 2 — #47 Per-subagent env-details injection

**File:** `MAIN/agent/sagemaker_agent.py` — `_run_task_tool` sub_prompt build (~L7674).
**Current:** `sub_prompt = SYSTEM_PROMPT + "# Sub-agent Notes\n..."`.
**New:** append a fresh-env block: `cwd=<workspace>`, `git status`/`git rev-parse HEAD` snapshot (5s timeout, fail-quiet), agent type + parent depth.
**Why:** every subagent inherits parent's worktree path correctly, so a fresh subagent should see the same workspace state the parent had — particularly relevant after the V4.4 worktree swap.

**Test:** `test_v410_subagent_env.py` — 1 case (sub_prompt contains cwd line and agent_type line; gracefully degrades when not in git repo).

**Codex:** SKIP per `feedback_codex_skip_bedrock_patches` (prompt template change only).

---

## Phase 3 — #44 context_window + model→window map

**File:** `MAIN/agent/sagemaker_agent.py`.
**Changes:**
- Add `BEDROCK_MODEL_CONTEXT_WINDOWS: Dict[str, int]` near `BEDROCK_MODELS` (~L8751) covering Haiku 4.5 / Sonnet 4.5 / Sonnet 4.6 / Opus 4.5 / Opus 4.6 / 3.5 Sonnet (200K each as of 2026-04). Comment marks where 1M variants will land when AWS exposes them.
- `Config` keeps existing `context_max_tokens: int = 200000` (L1028); add helper `_resolve_context_window(model_id, override)` that returns `override` if set, else `BEDROCK_MODEL_CONTEXT_WINDOWS.get(model_id, 200000)`.
- On `Agent.__init__` and on `BedrockClient.__init__`, log: `[i] Model X using context window=Y`.
- No threshold-percent constant changes needed: existing `should_compact` already multiplies by `CONFIG.context_max_tokens` — just ensure that value is correctly auto-derived.

**Test:** `test_v410_context_window.py` — 3 cases (Haiku 4.5→200K, unknown model→200K fallback, override wins).

---

## Phase 4 — #10 NotebookEdit tool

**File:** `MAIN/agent/sagemaker_agent.py`.
**New function:** `tool_notebook_edit(args)` near `tool_create_notebook` (~L5463).
**Args:**
- `path` (str, required) — absolute or workspace-relative .ipynb
- `action` (str, required) — `"insert" | "replace" | "delete"`
- `cell_index` (int, required) — 0-based; `-1` = append (insert only)
- `cell_type` (str, optional) — `"code" | "markdown"`, required for insert/replace, ignored for delete
- `source` (str, optional) — required for insert/replace, ignored for delete

**Behavior:**
- Read .ipynb as JSON
- For insert: insert new cell at `cell_index` (or append if -1 / ≥len)
- For replace: replace cell at `cell_index`; preserve `id` if present
- For delete: remove cell at `cell_index`
- Validate index bounds, action enum, cell_type enum
- Use `SECURITY.validate_path` like `tool_create_notebook`
- Atomic write (tmp + rename)
- Return: `Edited <path>: <action> at cell <i> (now <N> cells)`

**Tool registration:** add to `TOOLS` dict near `create_notebook` (~L6750), `requires_approval=True`.

**System prompt:** add one line to "# Documents" section noting `notebook_edit` for surgical .ipynb cell ops.

**Test:** `test_v410_notebook_edit.py` — 6 cases (insert middle, insert append, replace code cell, replace markdown, delete, out-of-bounds error).

---

## Phase 5 — #41a Reactive Compact on CONTEXT_OVERFLOW

**File:** `MAIN/agent/sagemaker_agent.py`.
**Wiring point:** the agent's main `run()` loop's `except Exception` block around L8242-8249, where `_llm_result[1]` is raised after `RETRY.execute(make_request, ...)` exhausts retries.

**New logic:**
1. Classify `e` via `ErrorClassifier.classify(e)`.
2. If `category == CONTEXT_OVERFLOW` AND `not getattr(self, "_reactive_compact_done_this_turn", False)`:
   - Set flag `self._reactive_compact_done_this_turn = True`.
   - Output `[Reactive compact: prompt rejected by Bedrock — compacting + retrying]`.
   - Run `microcompact(self.messages)` first; if savings sufficient, retry.
   - Else run full LLM compact (`COMPACTOR.create_llm_summary` → `COMPACTOR.compact`); if summary fails, abort to existing fallback.
   - Retry the same `make_request()` once via `RETRY.execute`.
   - If retry also fails → fall through to existing error path.
3. Reset `self._reactive_compact_done_this_turn` at the top of each turn (after a successful response, before next iteration of the turn loop).

**Cap:** **1 reactive compact + 1 retry per turn**, hard-coded — no infinite loops.

**Test:** `test_v410_reactive_compact.py` — 3 cases:
1. Mock client raises CONTEXT_OVERFLOW once then succeeds → reactive compact triggered, retry succeeds, agent continues.
2. Mock client raises CONTEXT_OVERFLOW twice → reactive compact triggered once, second failure surfaces normally.
3. Non-CONTEXT_OVERFLOW error → reactive compact NOT triggered, error surfaces normally.

---

## Acceptance criteria

| Check | Pass condition |
|---|---|
| All 5 phases coded | yes/no |
| All new unit tests pass locally | `python -m pytest test_v410_*.py` green |
| Existing tests still pass | full `pytest MAIN/agent/` green |
| `git diff` self-review clean | no stray prints, no commented code, version bumps consistent |
| **Codex review per phase (every phase)** | "100% clean" verdict — no consolidated review, **per-phase** |
| **Cache integrity** | Static prompt content (above `# === DYNAMIC ===` boundary) NOT modified per-turn; tool descriptions stable across turns; skill listing computed at module-load only |
| **Small-model friendliness (Haiku 4.5)** | Main system prompt grows by ≤10 lines total across all 5 phases; new tool description for `notebook_edit` ≤ 8 lines; no nested directives or conditionals in prompt |
| **Metrics correctness** | All token-percent triggers rebase against `context_max_tokens` (not hardcoded); reactive compact does NOT double-count tokens; `cache_broken_by_compact` flag reset correctly on retry |
| **Skill-load safety** | `enable_skill_auto_trigger` stays `False` by default; skill listing budget does NOT change activation logic; existing `test_v49_auto_trigger.py` regression test still passes |
| HTML updates | 4 target files updated with v4.10.0 banner + change log |
| CHANGELOG.md | v4.10.0 entry with all 5 items |
| USER_GUIDE.md | new tool docs (notebook_edit) + reactive compact note |
| compact_v4.zip rebuilt | runtime-only; no test files; size sanity-check |
| **Push to sageagent remote** | per CLAUDE.md: this repo pushes to `sageagent`, not `origin` |
| **Post-ship deep re-review** | Run a second deep scan of v4.10.0 vs Runnable; confirm parity or advantage on all relevant dimensions |

---

## Outcome (2026-04-28)

**Status: SHIPPED.** Commit `213528a` on `master`, pushed to `sageagent` remote.

### Closed gaps (5 of 6)
- #10 NotebookEdit ✅
- #24 Skill listing budget ✅
- #41a Reactive Compact ✅
- #44 1M-readiness via model→window map + JSON-validated override ✅
- #47 Per-sub-agent env-details ✅

### Closed follow-up gap (v4.10.1, same-day)
- #41b Context Collapse (segment-level summary) — shipped as v4.10.1, the same-day follow-up to v4.10.0. Microcompact clears stale tool output bodies, then `context_collapse()` collapses runs of 3+ stale tool round-trips into one synthetic Bedrock-safe pair. Also v4.10.1 changed the default model from Haiku 4.5 to Sonnet 4.5 (cache activates from 1024 tokens vs 4096).

### Codex per-phase review record
| Phase | Round 1 | Round 2 | Round 3 | Final |
|---|---|---|---|---|
| 1 #24 | ISSUES (3 bugs) | ISSUES (1 bug) | PASS | PASS |
| 2 #47 | PASS | — | — | PASS |
| 3 #44 | ISSUES (2 bugs) | ISSUES (2 bugs) | PASS | PASS |
| 4 #10 | ISSUES (1 bug) | PASS | — | PASS |
| 5 #41a | ISSUES (3 bugs) | PASS | — | PASS |

**9 real correctness issues caught and fixed** before any phase advanced. Issues: first-entry-over-budget overshoot, hint cost not budgeted, degenerate-budget overshoot, freeze-on-invalid-JSON, bool-as-int trap, weak e2e test, narrow OSError catch, file-read state cleared only on one branch, retry stop-check missing token-billing parity.

### Post-ship deep re-review verdict

**For self-use SageMaker coding agent: v4.10.0 ≥ Runnable on every dimension that matters.** The remaining Runnable advantages depend on infrastructure that doesn't exist on Bedrock/SageMaker (multi-scope cache, ant-only feature gates, GitHub tooling, cron/notifications, 1M beta header). v4.10.0 adds 11 SageMaker-specific advantages Runnable doesn't have (single-file deploy, Bedrock-native auth, AGENT_STATUS.md handoff, custom compaction model, skill self-patching, spec-first critique, mandatory verification, document tools, python_exec, no-network guardrails, dual-gate skill-auto-load default OFF).

**Caching activation verified:** every v4.10.0 addition sits AFTER the `# === DYNAMIC ===` marker; the cached `SYSTEM_PROMPT` prefix is byte-identical across turns. Bedrock ephemeral cache will activate when static prefix exceeds the per-model checkpoint size (4096 tokens for Haiku 4.5).

**Haiku-friendliness verified:** main system prompt grew by 2 lines net. Sub-agent prompts grew by 4–6 lines (env-details only). No nested directives.

**Metrics correctness verified:** all percent triggers (`MICROCOMPACT_TRIGGER_PERCENT=0.70`, `SUMMARY_TRIGGER_PERCENT=0.80`) compute against `CONFIG.context_max_tokens`, which auto-derives from `model_id` via `BEDROCK_MODEL_CONTEXT_WINDOWS`. Reactive compact does not double-count tokens.

**Skill-load safety (the previous bug):** fully resolved. Dual-gate default OFF (`enable_skill_auto_trigger=False` global + `auto_trigger=false` per-skill). `test_v49_auto_trigger.py` 12/12 still green.

### Test totals
- New v4.10.0: 9 + 6 + 10 + 13 + 5 = **43 tests, all PASS**
- v4.10.1 #41b: 12 tests, all PASS
- Plus v4.9.x auto-trigger regression: 12/12 still green
- Combined new/regression subset: **67/67 across 7 files** (43 + 12 + 12)

### Ship metadata
- Commit: `213528a`
- Files: 16 changed (+2215 / -62)
- Zip: `compact_v4.zip` 22 files / 234.6 KB / runtime-only, flat root layout
- Remote: pushed to `sageagent`
