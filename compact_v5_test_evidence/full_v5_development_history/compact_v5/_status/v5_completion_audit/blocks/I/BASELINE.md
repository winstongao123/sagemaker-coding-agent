# Block I Baseline

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:210-228`

Expected rows:

| row_id | capability | source | priority | fit | expected target |
|---|---|---|---|---|---|
| I-1 | Conditional skills via `paths:` frontmatter | Runnable `skills/loadSkillsDir.ts:159-178` | HIGH | CLEAN | Auto-activate matching skills by touched paths. |
| I-2 | `disable_model_invocation` flag | Runnable `bundledSkills.ts:84` | MED | CLEAN | Hide user-only skills from model-invocation surfaces. |
| I-3 | `enabled_when` skill predicate | Runnable `bundled/remember.ts:71` | MED | CLEAN | Gate skill visibility on config predicates. |
| I-4 | realpath-dedup in skill load | Runnable `loadSkillsDir.ts:638-810` | HIGH | CLEAN | Avoid symlink/duplicate-path double loading. |
| I-5 | Skill discovery on every edit | Runnable `FileEditTool.ts:404-423` | MED | CLEAN | Trigger path-based skill activation after edits. |
| I-6 | `${CLAUDE_SKILL_DIR}` + `${CLAUDE_SESSION_ID}` substitution | Runnable `loadSkillsDir.ts:344-396` | LOW | CLEAN | Substitute safe skill/session variables without shell execution. |
| I-7 | `skills/init/` | Runnable `commands/init.ts` | MED | CLEAN | Folded D-8 scaffold prompt skill. |
| I-8 | `skills/init-verifiers/` | Runnable `commands/init-verifiers.ts` | MED | CLEAN | Folded D-9 verifier scaffold prompt skill. |
| I-9 | `skills/skillify/` | Runnable `bundled/skillify.ts` | MED | CLEAN | Folded D-10 skillify prompt skill. |
| I-10 | `skills/debug/` | Runnable `bundled/debug.ts:1-103` | LOW | CLEAN | Debug triage skill. |
| I-11 | `skills/remember/` 4-step review | Runnable `bundled/remember.ts:9-62` | LOW | CLEAN | Manual memory-capture skill. |
| I-12 | Frontmatter parser improvements | Runnable `utils/frontmatterParser.ts:1-371` | HIGH | CLEAN | Auto-quote/list tolerance, brace expansion, and description coercion. |
| I-13 | `tool_skill` + `tool_skill_propose_patch` registry rows | v4 `sagemaker_agent.py:6674, 6703` | LOW | doc-only | Confirm existing tool registry rows and Block D dispatcher note. |

Initial audit condition:

- `scope_audit.py --block I` reported `LEDGER_INCOMPLETE` because the block artifact ledger did not exist.
- Existing PORT_LOG rows #073 through #083 and ADR-029 covered most rows.
- I-12 had historical deferral language; the redo patches the parser and adds lock tests instead of relying on a deferral.
