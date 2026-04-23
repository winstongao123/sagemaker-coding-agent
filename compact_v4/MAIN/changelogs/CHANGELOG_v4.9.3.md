# CHANGELOG — V4.9.3 (2026-04-23)

## Summary

Five small enhancements pulled from a deep-scan comparison against `gg-claude-code-runnable`, `hermes-agent`, and `Learning_Factory` — filtered through the constraints of the actual deployment target (**SageMaker + Bedrock-only + no external network, insurance-company environment**).

Items that didn't fit the constraints (MCP, OpenRouter routing, multi-platform messaging, self-patching skills) were rejected. Items that turned out to already exist (doom-loop detection at line 7368) were dropped from the plan after a quick scan.

## What was added

### 1. Prompt-injection scanner on context-file loads — security
Reads of `memory.md`, `CLAUDE.md`, and skill SKILL.md content are now scanned for likely injection markers before the content lands in the system prompt:

- Instruction-override patterns (`ignore (all) (previous|prior|above) instructions`)
- Role-hijack (`you are now a/an X`)
- Fake `<system-reminder>` / `<important-instructions>` tags
- Exposed credentials (`AWS_KEY=...`, `API_TOKEN=...` patterns)
- Invisible / bidirectional / format-confusion characters (Unicode TS#36)

**Advisory only** — emits `[INJECTION-SCAN]` warnings to `logging.warning()`. Does NOT block load. False-positive avoidance — code examples and docs legitimately mention "ignore" in some contexts. Insurance-compliance audit team can configure log capture to surface these warnings.

Defends against: malicious skill author crafting a SKILL.md with injection payloads; careless edit to `memory.md` adding instructions; user accidentally including a leaked AWS key in `CLAUDE.md`.

Source: hermes `prompt_builder.py:36-72`. Implementation: ~50 lines in `sagemaker_agent.py`.

### 2. CSO description validator on skill discovery — quality
When `SkillManager.discover()` parses a `SKILL.md` frontmatter, if the description text doesn't start with `"Use when"` it emits a `[CSO-CHECK]` warning identifying the skill.

**Advisory only** — does NOT block skill load. The 10 currently-shipped skills will all warn until their descriptions are updated to "Use when [trigger]" format. This is intentional surface-area for incremental cleanup — see `Learning_Factory` ADVANCED_PATTERNS.md R-105 for the rationale.

Source: Learning_Factory `cso-check.sh`. Implementation: 5 lines.

### 3. New `/reflexion` skill — quality lift for high-stakes outputs
New skill at [`skills/reflexion/SKILL.md`](compact_v4/MAIN/agent/skills/reflexion/SKILL.md). Three-pass loop:

1. **Critique** — step outside the writer's voice, list specific weaknesses with quoted phrases
2. **Refine** — apply each critique line as a focused edit
3. **Judge** — compare refined vs original, decide if another loop iteration is warranted

Slash-command-only (`auto_trigger: false`). CSO-compliant description. Triples LLM cost — only invoke for high-stakes reviews (claim assessments, audit reports, multi-section design docs).

Source: Learning_Factory `reflexion` skill. Implementation: 1 new SKILL.md file, ~80 lines markdown, no Python changes.

### 4. SYSTEM_PROMPT — spec-first ordering in "Handling Critique" section
Added one bullet to the v4.9 critique-handling section: **address spec/correctness compliance before code quality**. Don't dilute spec findings by mixing them with style findings.

Source: Learning_Factory ADVANCED_PATTERNS.md `:42-48`. Implementation: 1 line in SYSTEM_PROMPT.

### 5. Version bump
`__version__`: `4.9.2` → `4.9.3`.

## What was rejected (so future-you doesn't re-litigate)

| Candidate | Source | Reason rejected |
|---|---|---|
| MCP server integration | gg-claude-code-runnable | Insurance company doesn't allow external network from SageMaker |
| Multi-stage compaction (proactive + reactive + snip) | gg-claude-code-runnable | Existing single-stage compaction is adequate; ~300 lines for marginal gain not worth it |
| Permission rule engine (per-tool allowlist) | gg-claude-code-runnable | Bigger feature — defer to v4.10 if needed |
| Tool-call loop detection | Learning_Factory | **Already exists** at `sagemaker_agent.py:7368-7422` ("doom loop detection"), more robust than the proposed pattern |
| Provider fallback chain (OpenRouter etc.) | hermes-agent | External network not allowed |
| Self-patching skills | hermes-agent | Insurance compliance frowns on agent-modified runtime artefacts |
| Multi-platform messaging gateway | hermes-agent | SageMaker users use the notebook, not Telegram/Discord |
| Mixture-of-models voting (Sonnet + Haiku judge) | hermes-agent | Doubles cost per review — defer until cost/benefit is validated |
| Error classifier with structured recovery taxonomy | hermes-agent | Significant cleanup work — defer to v4.10 |

## Files Changed

| File | Change |
|---|---|
| `compact_v4/MAIN/agent/sagemaker_agent.py` | +57 -2 lines: scanner helper + 3 wire-in points (memory load, project instructions load, skill read), CSO check in discover(), spec-first prompt bullet, version bump |
| `compact_v4/MAIN/agent/skills/reflexion/SKILL.md` | NEW — 80-line skill markdown |
| `compact_v4/MAIN/agent/test_v493_enhancements.py` | NEW — 11 tests |
| `compact_v4/MAIN/changelogs/CHANGELOG_v4.9.3.md` | NEW |
| `compact_v4/CHANGELOG.md` | v4.9.3 entry |
| `SESSION_STATE.md` | v4.9.3 entry |
| `compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md` | §11 appended — enhancements pulled from cross-repo comparison |
| `compact_v4/compact_v4.zip` | Rebuilt (still 20 files / ~205 KB, includes new reflexion skill) |

## Verification

- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version reports `4.9.3`
- `test_v493_enhancements.py` (new) — **11/11 PASS**
- `test_v491_unskill.py` (regression) — **10/10 PASS**
- `test_v49_auto_trigger.py` (regression) — **11/11 PASS**
- `test_v471_enhancements.py` (regression) — **9/9 PASS**
- `test_v461_path_fix.py` (regression) — PASS
- **Total: 41/41 tests green**
- No Codex review this round (per project rule for Bedrock-only patches that don't touch general algorithms — see `feedback_codex_skip_bedrock_patches.md`)
- Self-review: every diff hunk re-read; one minor (forward reference of `_scan_for_prompt_injection` from `SkillManager.read_skill` line 2294 to module-level helper line ~6286) verified to work via Python's runtime name resolution
- Smoke-tested scanner against clean / injected / invisible-char inputs

## Migration

None. Fully additive:
- The scanner emits warnings only — no behavioural change for the agent
- The CSO check emits warnings only — existing skills continue to work, descriptions can be updated incrementally
- The new `/reflexion` skill is opt-in via slash command
- The SYSTEM_PROMPT addition is one bullet in an existing section
