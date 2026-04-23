# CHANGELOG — V4.9.0 (2026-04-23)

## Summary

Targeted reliability release. Fixes the silent `auto_trigger: false` bug shipped in v4.8.0 (opt-out flag was parsed but never honoured in the keyword auto-match loop), hardens keyword matching against substring false-positives, adds a system-prompt rule for how the agent should handle critiques of its own work, and makes skill auto-injection visible to the user with an approximate char-count.

All changes are documented in detail in `compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md` — this changelog is the terse ship-log.

## Scope

One source file + one new test file:

- `compact_v4/MAIN/agent/sagemaker_agent.py` — +32 -14 lines
- `compact_v4/MAIN/agent/test_v49_auto_trigger.py` — **NEW**, 11 tests
- `compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md` — **NEW** (shipped with this release)

## Changes

### 1. [BUG FIX] `auto_trigger: false` is now honoured by the auto-match loop

**Before (v4.8.0):** frontmatter key parsed into a local variable and immediately discarded. Skills like `clara-review` with `auto_trigger: false` still auto-activated whenever a user message substring-contained the name words (e.g. a file path like `Clara_WIP/foo.ipynb` + the word "review" triggered it). Once activated the skill's ~8000 chars were injected into every system prompt for the rest of the session. The flag was effectively dead.

**After (v4.9.0):**
- `SkillInfo` dataclass gains `auto_trigger: bool = True` (line 2199).
- Parser now passes the flag through to the cached `SkillInfo` (line 2265).
- Auto-match loop in `create_chat_ui` skips skills where `auto_trigger=False` (line 9348).

**User impact:** `clara-review`, `batch`, `simplify`, `verify`, `code-review`, `security-review` (all already shipped with `auto_trigger: false`) now only activate via their explicit `/command`. Status bar stays clean unless the user actively invoked the skill.

### 2. Word-boundary keyword match (substring → token-set)

**Before:** `all(w in msg_lower for w in name_words)` — substring match. `"review"` matched inside `"unreviewable"`, `"clara"` matched inside `"Clara_WIP"` and `"clarachromatic"`.

**After:** both message and skill name are tokenized with `re.findall(r"[a-z0-9]+", ...)`, and the skill matches only when every name token appears as a whole word in the message. Same regex on both sides so non-hyphen separators (e.g. `qa_review`, `docs.v2`) match consistently.

**Also removed:** the dead `or (s_desc and any(phrase in msg_lower ...))` branch — `phrase` was literally `s_name.replace("-", " ")`, so that branch was always a weaker version of the first branch and could never fire on its own.

### 3. [SYSTEM PROMPT] "Handling Critique of Your Own Work" section

New SYSTEM_PROMPT block added before the "Answer Preference" section. Covers three failure modes observed in the 2026-04-23 debate case study (documented in the audit doc):

- **Re-read the source before agreeing or rejecting.** Reasoning about the critique text alone produces sycophancy at temp=0 and defensive rejection at temp=1 — both are wrong.
- **Per-point `ACCEPT` / `PARTIAL` / `REJECT` + evidence (file:function).** No single global verdict without going through each point.
- **A pasted critique IS a user message**, not untrusted tool output. Don't dismiss as "fabricated" or "a test".

This addresses audit §8 items #2 and #3.

### 4. Skill injection visibility — char count in activation banner

When a skill auto-activates, the system message now reads:
```
Auto-matched skill: clara-review (~8123 chars injected)
```
instead of just `Auto-matched skill: clara-review`. Makes the prompt-size cost visible.

Addresses audit §8 item #5. Wrapped in `try/except` — a missing SKILL.md falls back to the old short message silently.

### 5. Version bump

`__version__`: `4.8.0` → `4.9.0`.

## Files Changed

| File | Change |
|---|---|
| `compact_v4/MAIN/agent/sagemaker_agent.py` | +32 -14 lines across 4 regions (SkillInfo, parser, SYSTEM_PROMPT, auto-match loop) |
| `compact_v4/MAIN/agent/test_v49_auto_trigger.py` | NEW — 11 tests |
| `compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md` | NEW — full audit doc (case study, 5-defect chain, patch spec) |

## Verification

### Self-review
- `py_compile`: PASS
- `ast.parse`: PASS
- `python -W error -c 'import sagemaker_agent'`: PASS, version `4.9.0`
- `test_v49_auto_trigger.py`: **11/11 passed**
- `test_v471_enhancements.py` (regression): **9/9 passed**
- Final diff re-read: clean; one redundant `phrase_hit` branch caught and removed during self-review

### Codex review (`gpt-5.3-codex`, read-only sandbox)

Two rounds:

1. **First round — NEEDS-FIX.** Flagged tokenization inconsistency: `s_name.replace("-", " ").split()` used for skill name vs `re.findall(r"[a-z0-9]+", ...)` used for message. A skill named `qa_review` or `docs.v2` would silently fail to auto-match even when the user message contains the words. No shipped skill uses non-hyphen separators so no live regression, but a latent bug.
2. **Fix applied.** Switched skill-name tokenization to the same regex. Added test `test_name_tokenization_handles_non_hyphen_separators` covering `qa_review` + `docs.v2`.
3. **Second round — PASS.** No further issues.

## Known Non-Regressions (pre-existing)

- `test_v46_complex.py` has `Skill discovery works` marked FAIL — reproduces on unmodified v4.8.0 master (not caused by v4.9.0). The test expects `discover_relevant` to surface `security-review` for a "security" query; `security-review` shipped with `auto_trigger: false` in v4.8.0 so its `triggers` list became `None` and it is correctly skipped. Test is outdated.

## Out of scope (tracked separately)

From audit §8, NOT fixed in this release:

- Thinking-mode temperature=1 calibration (Bedrock API constraint).
- Lightweight `/unskill <name>` command (existing `/skill clear` + auto-match fix covers most cases).
- Skill-injection banner as hoverable chip in the UI (char-count in activation message is the minimum viable version).

## Migration

None. Fully backwards compatible:
- Existing skills without `auto_trigger` key default to `True` (keyword auto-match).
- Skills already carrying `auto_trigger: false` (6 of 11 shipped skills) switch from "flag ignored → still auto-match" to "flag honoured → only via /command". This is the bug being fixed, not a breaking change.
- No config changes, no schema changes, no API changes.
