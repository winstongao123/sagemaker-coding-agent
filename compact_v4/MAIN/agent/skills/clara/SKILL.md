---
name: clara-review
description: ClaRA codebase review methodology - evidence labeling, output rules, sub-agent coordination for 5-phase production readiness assessment
triggers: clara, claims, insurance claim, claims processing, evidence labeling, rag scoring, compliance check, pii detection
---

# ClaRA Review Skill

When reviewing the ClaRA (Claims Resolution AI Assistant) codebase, follow these rules throughout all phases.

## Evidence Rules (apply to ALL output)

1. **Every claim must reference `file:function`** (not line numbers — they shift between versions).
2. **Tag every finding:**
   - `[verified]` — confirmed from code reading in this session
   - `[assumed]` — from context, estimates, or existing review (not code-confirmed)
   - `[NOT VERIFIED — requires access to X]` — cannot check from codebase
3. **Implementation status:** Use precisely:
   - `NOT IMPLEMENTED` — zero code artifacts
   - `PARTIALLY IMPLEMENTED` — some code exists but incomplete
   - `IMPLEMENTED` — code exists and meets reasonable standard
4. **If you cannot verify a finding, state explicitly.** Do not skip silently.

## Output Rules

1. Write findings to output files incrementally — append after each section using `write_file` with `mode: "append"`.
2. Do NOT hold findings in memory — compaction will destroy them.
3. For files >500 lines, read in chunks using `offset` parameter.
4. Prompts: review quality and logic only — do NOT extract full prompt text into output.
5. **Quantify everything** — business case needs numbers.
6. **Frame findings for non-technical audience** alongside technical detail.

## R/A/G Rating Thresholds

| Rating | Criteria |
|--------|----------|
| **RED** | No evidence of implementation. Zero code artifacts. |
| **AMBER** | Some code exists but incomplete or below production standard. |
| **GREEN** | Implementation exists, consistent, meets production standard. |

Scoring guide:
- **Security**: GREEN = no PII in logs, parameterised queries, secrets in Secrets Manager. RED = hardcoded creds or PII sent to LLM.
- **Observability**: GREEN = structured logging + metrics + tracing. RED = no logging or only `print()`.
- **Testing**: GREEN = pytest with >50% coverage. RED = zero test files.
- **Error Handling**: GREEN = retry + timeout + graceful degradation. RED = no error handling.
- **Compliance**: GREEN = audit trail + explainability + human override. RED = no audit trail.

## Sub-Agent Usage

| Type | Use For | Model |
|------|---------|-------|
| **explore** (Haiku) | File listing, grep searches, single-file reads | Fast, limited reasoning |
| **review** (Sonnet) | Single-file deep analysis, bug validation | Good for read + analyze + report |
| **general** (Sonnet) | Multi-file analysis, tracing logic across files | 25 turns, read ~3 files + synthesize |

When spawning sub-agents: provide self-contained instructions with **actual file paths** (never placeholders).

## PS_ File Rules

- **Component 1 PS_ files: SKIP** (already synthesized into End-to-End Review)
- **Component 2 and 3 PS_ files: READ** (contain unreported analysis)

## PII Patterns to Check

| PII Type | Search For |
|----------|-----------|
| Tax File Number | `\d{3}[-\s]?\d{3}[-\s]?\d{3}` |
| Policy numbers | `policy_number`, `policy_id`, `policyNo` |
| Date of birth | `dob`, `date_of_birth`, `birth_date` |
| Medical data | `diagnosis`, `medical`, `condition`, `treatment` |
| Names | `claimant_name`, `member_name`, `beneficiary` |

Check: are these sent to LLM? Logged? Stored unencrypted?

## 5-Phase Review Workflow

1. **Discovery** (01) — File tree, dependencies, AWS inventory, code metrics
2. **Component 1** (02) — Bug validation, CHECK_REGISTRY, extraction code, test evidence
3. **Components 2+3** (03) — Agent definitions, orchestration, SQL, UI assessment
4. **Production Readiness** (04) — R/A/G scorecard, cost projections, FTE impact
5. **Synthesis** (05) — Final report + business case

Run sequentially. Each phase writes to `output/0X_filename.md`. Each depends on prior outputs.

## Component Discovery Hints

| Component | Search |
|-----------|--------|
| C1: End-to-End Claims | `glob("**/*claim*")`, grep for `CHECK_REGISTRY` |
| C2: Agentic Framework | grep for `create_agent`, `invoke_agent`, `InlineAgent`, `supervisor` |
| C3: UI Layer | grep for `streamlit`, `flask`, `react`, `copilot`, `cognito` |

## Failure Recovery

- Agent hits max turns: "Continue from where output/0X_xxx.md left off."
- Agent skips section: "You skipped section X.Y. Go back and complete it."
- Grep capped: Narrow search to one component folder at a time.
