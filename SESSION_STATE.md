# SESSION STATE — sagemaker-coding-agent

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
