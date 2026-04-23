# SESSION STATE — sagemaker-coding-agent

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
