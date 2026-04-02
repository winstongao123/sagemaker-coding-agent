# ClaRA Review — Shared Context

> Load this file at the START of every prompt. It replaces the inline "KNOWN CONTEXT" section.

---

## PURPOSE OF THIS REVIEW

This review **gathers factual technical information** from the ClaRA codebase. The information feeds into:
- A **roadmap** for production readiness (Q3 target)
- A **business case / PPT** for Francis/GLT in Q2
- **Future technical enhancement work** — the outputs serve as reference for developers

**Focus priority**: C1 (End-to-End Claims) is most mature and already has a prior review — validate and enhance it. C2 (Agentic Framework) is the biggest unknown — deep dive. C3 (UI) is minimal — quick inventory only.

**Two output deliverables** from these prompts:
1. **Technical Findings Report** — gap analysis, risk register, phased roadmap, code-level references
2. **Business Case Input** — cost/benefit estimates, FTE impact, compliance requirements, timeline

**Key stakeholders**:
- **Francis (CTO)**: Needs ROI justification, cost projections, risk assessment for GLT
- **Ben (Head of AI)**: Needs production readiness assessment + resource plan + timeline + cost/benefit estimates
- **Mary Magdalenus (Head of Claims)**: Business sponsor, needs compliance confidence + assessor workflow impact

**Timeline**: Business case goes to GLT in Q2. Target: productionise Clara end-to-end by end of Q3.

---

## EVIDENCE AND LABELING RULES

These rules apply to ALL prompts. Every finding must be traceable.

1. **Every claim must reference `file:function`** (not line numbers — these shift between versions).
   - Example: `func_check_executor.py:load_sources_from_s3` — Good
   - Example: `line 247` — Bad (will be outdated after any edit)

2. **Unverified claims must be tagged `[assumed]`.**
   - If you read something in the existing review or context but cannot verify it from code, write: `[assumed from review]`
   - If you estimate a number, write: `[assumed — requires validation from claims team]`

3. **If you cannot verify a finding from code, state explicitly:**
   `[NOT VERIFIED — requires access to X]`

4. **Distinguish implementation status precisely:**
   - `NOT IMPLEMENTED` — zero code artifacts for this area
   - `PARTIALLY IMPLEMENTED` — some code exists but incomplete or inconsistent
   - `IMPLEMENTED` — code exists and meets a reasonable production standard
   - `[verified]` — you confirmed from code reading
   - `[assumed]` — from context/review but not code-confirmed

---

## EXISTING REVIEW REFERENCE

A prior End-to-End Review report exists for Component 1 (written by Winston, ~20 pages). If a copy exists in the workspace as `reference/end_to_end_review.md`, read it and use it as follows:
- **Prompt 2 (Component 1):** Validate the review's findings against actual code. Confirm each finding, flag discrepancies, and add NEW findings not in the review.
- **Other prompts:** Reference it where relevant but do not repeat its content verbatim.

---

## PS_ FILE HANDLING RULES

You will encounter `PS_*.md` files in ClaRA component folders. These are Winston's working notes.

- **Component 1 PS_ files: SKIP.** These have already been synthesized into the End-to-End Review. List them in the file inventory but do NOT read them.
- **Component 2 and 3 PS_ files: READ as context.** These contain analysis of the agentic framework and UI that has NOT been written up yet. Validate and build on their findings.

---

## APPEND METHOD (write_file)

compact_v3's `write_file` tool supports `mode: "append"`. Use it to add content to output files incrementally.

**How to append (used by ALL prompts):**
```
write_file(path="output/0X_filename.md", content="\n\n## Section Title\n\nYour findings here...", mode="append")
```

The first write to a new file should use the default mode (overwrite) to create the file with the header. All subsequent sections use `mode: "append"`.

**DO NOT** read the entire output file, concatenate in memory, and re-write. Use append mode directly.

---

## PII PATTERNS TO CHECK

When assessing PII exposure (Prompt 4), search for these specific Australian patterns:

| PII Type | Pattern to Search | Regex Hint |
|----------|------------------|------------|
| Tax File Number (TFN) | 9-digit number, often formatted XXX-XXX-XXX | `\d{3}[-\s]?\d{3}[-\s]?\d{3}` |
| Policy numbers | Alphanumeric, often starts with prefix | Look for `policy_number`, `policy_id`, `policyNo` |
| Account numbers | Bank BSB + account | `\d{3}-?\d{3}\s+\d{6,9}` |
| Date of birth | Various date formats | `dob`, `date_of_birth`, `birth_date` |
| Medical data | Diagnosis, conditions, treatment | `diagnosis`, `medical`, `condition`, `treatment`, `disability` |
| Addresses | Street, suburb, postcode | `address`, `street`, `suburb`, `postcode` |
| Phone numbers | Australian format | `\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4}` |
| Names | Claimant, beneficiary names | `claimant_name`, `member_name`, `beneficiary` |

Check: Are these sent to the LLM in prompts? Logged? Stored unencrypted?

---

## R/A/G RATING CRITERIA (with thresholds)

Use these concrete thresholds when rating each area per component:

| Rating | Criteria | Examples |
|--------|----------|---------|
| **RED** | No evidence of implementation. Zero code artifacts. | No test files exist. No logging framework. No error handling on API calls. |
| **AMBER** | Some code exists but incomplete, inconsistent, or below production standard. | `print()` statements but no structured logging. Try/except exists but catches generic `Exception`. Some checks have error handling, others don't. |
| **GREEN** | Implementation exists, is consistent across the component, and meets reasonable production standard. | Structured logging with levels. Retry logic with backoff. Parameterised queries. Consistent error handling on all external calls. |

**Scoring guide per area:**
- **Security**: GREEN = no PII in logs, parameterised queries, secrets in Secrets Manager, input validation. RED = hardcoded credentials or PII sent unredacted to LLM.
- **Observability**: GREEN = structured logging + metrics + tracing. RED = no logging or only `print()`. AMBER = some logging but inconsistent.
- **Testing**: GREEN = pytest/unittest with >50% coverage. RED = zero test files. AMBER = test files exist but <20% coverage or only manual test notebooks.
- **Error Handling**: GREEN = retry + timeout + graceful degradation on all external calls. RED = no error handling on API calls. AMBER = some try/except but no retry/timeout.
- **Compliance**: GREEN = audit trail + explainability + PDS version tracking + human override. RED = no audit trail, no explainability.

---

## COMPONENT DISCOVERY HINTS

The ClaRA codebase uses non-standard folder names. Use these hints to find each component:

| Component | Expected Folder Name | Fallback Search |
|-----------|---------------------|----------------|
| C1: End-to-End Claims | `end to end claim process` or similar | `glob("**/*claim*")`, `glob("**/*check*")`, grep for `CHECK_REGISTRY` |
| C2: Agentic Framework | Unknown — search for it | grep for `create_agent`, `invoke_agent`, `InlineAgent`, `supervisor`, `bedrock-agent` |
| C3: UI Layer | Unknown — search for it | grep for `streamlit`, `flask`, `react`, `copilot`, `cognito`, `.html`, `.jsx`, `.tsx` |

If a component folder is not obvious from the top-level directory listing, use grep to find key identifiers and trace back to the containing folder.

---

## BATCH PROCESSING CONTEXT

Component 1 currently processes a single claim in ~95 seconds. In production deployment, batch processing of multiple claims is a key consideration:

- **Current UX challenge**: 10-12 minutes per claim from user perspective (includes all phases)
- **Deployment architecture options** (from Winston's review, Section 8):
  - **Real-time**: User submits one claim, waits for result. Suitable for ad-hoc queries.
  - **Batch queue**: Claims queued via SQS/Step Functions, processed asynchronously. Results delivered via notification.
  - **Hybrid**: Quick checks run real-time, full assessment runs as background job.
- **Scale considerations**: At 200 claims/day, sequential processing = ~5.3 hours. Parallel processing (10 workers) = ~32 minutes.
- When assessing Components 2 and 3, check: Is there any batch/queue infrastructure? Any async processing? Any progress tracking for long-running assessments?

---

## System Overview
- **ClaRA** = Claims Resolution AI Assistant. Agentic AI for life insurance claims. Built by Acenda (formerly MLC Life Insurance, merging with Resolution Life).
- **3 components**: (1) End-to-End Claims Process, (2) Agentic Framework, (3) UI Layer
- **Component 1 is currently NOT connected to Components 2 and 3** — separate codebases/modules
- Component 1 folder is called "end to end claim process". Search for actual names of Components 2 and 3.
- **Current state**: Prototype, NOT production-ready. Runs in SageMaker notebooks only.

## Organisational Context
- RLA (Resolution Life) absorbing Acenda's organisation. Merger effective 1 April.
- Ben Thomas appointed Head of AI (accounting/analytics background, not technical). Reports to Francis (CTO).
- Francis personally set the challenge: "Productionise Clara end-to-end by end of Q3."
- Clara is Ben's #1 stated priority.
- No technical design document exists for any component.
- Some code not in Git — sitting locally with developer.

## AWS Stack
- Bedrock: Claude 3.5 Sonnet v2, model ID `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Region: `ap-southeast-2`, rate limit: 100 req/min
- Services: S3, Textract, SageMaker, Lambda, Secrets Manager, Snowflake
- Runs in SageMaker notebooks (not production deployed)

## Claim Types
- TPD retail: 21 checks
- TPD group super: 18 checks

## Component 1: End-to-End Claims Process
Two phases:
- **Phase 1: Document Extraction** — Textract + Claude extracts data from 8+ source documents into structured text
- **Phase 2: Assessment Execution** — 21 validation checks against extracted documents, generates PDF/Excel reports

Known Assessment files: `func_check_executor.py`, `func_pipeline_exec.py`, `checks_main.py`, `checks_all_combined.py`, `checks_baseline_policy_defination.py` (typo in filename), `checks_baseline_eligibility.py`, `func_generate_report.py`

Document Extraction files: NOT listed — find these (Textract OCR + Claude extraction code, quality validation code)

Source documents (8+ types in S3): ClaimForm, Bancs, TDR, AppForm, PolicyUpdates, CV, AuthorityMatrix, TFN, CertifiedID, pds_inforce_dates.json, upgrade_inforce_dates.json

Test case IDs: C-2024-333837, C-2025-342532

Performance baseline: 95.2s, $1.73/case, 472K tokens, 38 cases/hr, 74 S3 calls (62 redundant)

## 9 Known Bugs (to validate)

| ID | Severity | File -> Function | Issue |
|----|----------|-----------------|-------|
| BUG-001 | HIGH | func_check_executor.py -> load_sources_from_s3 | S3 error returns string instead of failing |
| BUG-002 | HIGH | func_check_executor.py -> invoke_bedrock_check | No Bedrock API error handling |
| BUG-003 | MEDIUM | func_check_executor.py | JSON parsing returns empty dict on failure |
| BUG-004 | MEDIUM | func_generate_report.py -> safe_extract | No logging on field extraction failure |
| BUG-005 | MEDIUM | checks_main.py | Inconsistent JSON capitalisation ("Extracted" vs "extracted") |
| BUG-006 | LOW | checks_baseline_eligibility.py | Regex without null check in C002 |
| BUG-007 | LOW | checks_baseline_policy_defination.py | Regex without null check in C001 |
| BUG-008 | CRITICAL | func_check_executor.py -> run_check | No token limit checking before Bedrock call |
| BUG-009 | CRITICAL | checks_baseline_policy_defination.py | C001 never loads policy upgrade docs, uses base PDS only |

## Component 2: Agentic Framework
- Bedrock inline agents, supervisor -> sub-agent pattern
- Sub-agents: ad-hoc query, document retrieval, knowledge lookup, claim decisioning (wraps Component 1)
- No technical design document, no versioning, no traceability, no observability, no CI/CD
- Inline agent prompts scattered without version control
- Some code not in Git (Snowflake->Secrets Manager update, CV/bank extraction, PDS diagram->JSON, reference PDFs->S3, routing changes)
- May have routing/intent classification logic — search for: router, classifier, dispatcher, intent

## Component 3: UI Layer
- Two experiments: EC2 with Cognito, and Microsoft Copilot Studio
- Chat interface for claims assessors, 10-12 min processing is UX challenge
- Likely minimal/prototype state

## Known Gaps (confirm each is still true)
No tests, no monitoring, no CI/CD, no requirements.txt, hardcoded configs, no model fallback

## Sub-Agent Types Available in compact_v3
- `explore`: Lightweight, max ~20 turns. Use for: grep searches, file listing, single-file reads. Model: Haiku.
- `review`: Medium, max ~20 turns. Use for: reading one file and answering specific questions (e.g., bug validation). Model: Sonnet.
- `general`: Full capability, max ~25 turns. Use for: multi-file analysis, tracing logic across files, complex tasks. Model: Sonnet.
- When spawning a sub-agent, provide: (1) the type, (2) a **self-contained instruction** with full file paths and what to return. Never use placeholders like `[folder]` — fill in actual paths discovered during this session.

**Sub-agent turn guidance:**
- `explore` (Haiku, 20 turns): Fast but limited reasoning. Good for: "list all .py files in X folder", "grep for Y in Z folder". Bad for: multi-step analysis.
- `review` (Sonnet, 20 turns): Good for single-file deep analysis. Enough turns to read a file, find a function, analyse it, and report.
- `general` (Sonnet, 25 turns): Use when you need to read 2-3 files and trace logic between them. 25 turns is enough for ~3 file reads + analysis + report. If you need more files, split into multiple sub-agents.

## Output Rules (apply to ALL prompts)
1. Every finding: **file path + function name** minimum. No line numbers (they shift).
2. Prompts: review quality and logic only — do NOT extract full prompt text into output.
3. Distinguish: `NOT IMPLEMENTED` vs `PARTIALLY IMPLEMENTED` vs `IMPLEMENTED`
4. If you can't find something, note explicitly — don't skip silently.
5. Flag CRITICAL issues immediately: incorrect claim decisions, PII exposure, security vulnerabilities.
6. Base ALL findings on actual code. Do not speculate. If unverifiable, state `[NOT VERIFIED — requires access to X]`.
7. **Quantify everything possible** — business case needs numbers, not just qualitative assessments.
8. **Frame findings for non-technical audience** — Ben and Francis need business language alongside technical detail.
9. **Dependency check**: At the start of each prompt, verify all prerequisite output files exist and are non-empty. If any is missing, STOP and report which file is missing.
10. **Tag every finding** as `[verified]` (confirmed from code) or `[assumed]` (from context/review/estimation).
11. **All outputs are future development reference** — write as if a developer will use these files to plan and implement changes. Be specific enough that someone can act on each finding.
