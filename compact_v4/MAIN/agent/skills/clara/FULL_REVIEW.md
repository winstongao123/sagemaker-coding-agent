---
name: clara-full-review
description: Run ClaRA codebase review — all 5 phases or select specific phases/components. User pauses between phases. Produces production readiness assessment + business case.
---

# ClaRA Full Review — Selective 5-Phase Orchestration

## How to Start

**Full review (all 5 phases):**
> "Start the ClaRA review"

**Select specific phases:**
> "Run ClaRA phase 1 and 2 only"
> "Run ClaRA phase 4 (production readiness) only"
> "Skip to phase 5 synthesis" (reads existing output/ files)

**Select specific components:**
> "Run ClaRA review on Component 1 only"
> "Run ClaRA review on C2 and C3 only"
> "Review only the agentic framework (C2)"

**Select specific sections within a phase:**
> "Run phase 2 sections 2.2 and 2.10 only" (just bug validation + new bugs)
> "Run phase 4 sections 4.1 and 4.4 only" (just security + compliance)

**Resume from where you left off:**
> "Continue ClaRA review from phase 3"

When the user selects specific phases, components, or sections — run ONLY those. Skip everything else. Still write to the same output files so results are cumulative.

---

## Pre-Flight (do this FIRST, regardless of selection)

1. Confirm workspace is set to ClaRA codebase root
2. Check: `read_file 00_CONTEXT.md` — must exist and be readable
3. Create output folder: `bash mkdir -p output`
4. Create reference folder: `bash mkdir -p reference`
5. Check for optional reference: `read_file reference/end_to_end_review.md` (OK if missing)
6. If resuming (phase 2+): check which output/ files already exist. Read them for context.
7. Report pre-flight status to user. If 00_CONTEXT.md missing, STOP.

## Evidence Rules (apply throughout)

- Every claim: `file:function` reference (not line numbers)
- Tag: `[verified]` (code-confirmed) or `[assumed]` (from context/estimates)
- Write to output file after EACH section — do not hold in memory
- Use `write_file` with `mode: "append"` for incremental output

## Component Filter

When user selects specific components, apply this filter:

| Selection | What to scan | What to skip |
|-----------|-------------|-------------|
| C1 only | "end to end claim process" folder, CHECK_REGISTRY, bug validation | Agent framework, UI |
| C2 only | Agent definitions, orchestration, tools, Snowflake | Claims checks, UI |
| C3 only | UI files, Cognito, Streamlit/React | Claims checks, agent framework |
| C1 + C2 | Both above | UI |
| All (default) | Everything | Nothing |

In Phase 4 (Production Readiness), only score selected components in the R/A/G matrix.

---

## PHASE 1: Discovery
**Output**: `output/01_discovery.md`
**Sub-agents**: Use `explore` for file discovery, `bash` for git history
**Can run standalone**: Yes (no prerequisites)

Tasks:
1.1. File tree with component mapping (C1/C2/C3/SHARED)
1.2. File inventory table (all files by type)
1.3. Dependencies (requirements.txt or import scanning)
1.4. Git history (last 20 commits, contributors, branches)
1.5. AWS resource inventory (ARNs, buckets, regions, model IDs)
1.6. Configuration audit (config files, hardcoded values)
1.7. Architecture diagrams found
1.8. Code metrics (LOC by component, top 10 largest files)
1.9. Business metrics baseline (verify 95.2s, $1.73, 472K tokens)

**After completing**: Report summary to user. Ask: "Phase 1 complete. Review output/01_discovery.md. Ready for next phase?"

**WAIT for user confirmation before proceeding.**

---

## PHASE 2: Component 1 — End-to-End Claims
**Output**: `output/02_component1.md`
**Pre-req**: Phase 1 output exists (or read codebase directly if skipping phase 1)
**Sub-agents**: Use `review` for bug validation (batch by file)
**Component filter**: Only runs if C1 is selected (or all)

Tasks:
2.1. Confirm known files exist (7 files from context)
2.2. Validate all 9 bugs (BUG-001 through BUG-009) — spawn review sub-agents
2.3. Find Document Extraction code (Phase 1 — Textract + Claude)
2.4. Extract CHECK_REGISTRY (all check IDs, functions, descriptions)
2.5. Pipeline configurations (baseline_only, tpd_retail, tpd_group)
2.6. Report generation review
2.7. Invocation method (how is assessment called?)
2.8. Test evidence (test files, output artifacts, metrics)
2.9. Batch processing readiness assessment
2.10. NEW bugs found (not in the known 9)

If `reference/end_to_end_review.md` exists: operate in VALIDATION MODE (confirm/flag/extend existing review).

**After completing**: Report summary. Ask: "Phase 2 complete. Review output/02_component1.md. Ready for next phase?"

**WAIT for user confirmation.**

---

## PHASE 3: Components 2 & 3 — Agentic Framework + UI
**Output**: `output/03_component2_3.md`
**Pre-req**: Phase 1 output exists (or read codebase directly)
**Sub-agents**: Use `general` for orchestration tracing, `explore` for targeted searches
**Component filter**: Sections 3.1-3.9 only if C2 selected. Sections 3.10-3.11 only if C3 selected.

Read C2/C3 PS_ files first (if they exist).

Tasks (C2 — Agentic Framework):
3.1. Agent definitions table (name, role, model, tools, instructions)
3.2. Orchestration map (text diagram of agent flow)
3.3. Tool/action group definitions
3.4. Component 1 integration analysis (how C2 calls C1)
3.5. Data access methods (Snowflake, S3, Bancs)
3.6. SQL queries with injection risk assessment
3.7. Session and conversation management
3.8. Hardcoded values inventory
3.9. Error handling and guardrails

Tasks (C3 — UI):
3.10. UI inventory and quick assessment
3.11. Deployment architecture assessment (covers all components)

**After completing**: Report summary. Ask: "Phase 3 complete. Review output/03_component2_3.md. Ready for next phase?"

**WAIT for user confirmation.**

---

## PHASE 4: Production Readiness Assessment
**Output**: `output/04_prod_readiness.md`
**Pre-req**: Read ALL prior outputs that exist
**Sub-agents**: Use `explore` for grep-heavy scans
**Component filter**: Only score selected components in R/A/G matrix

Assess each area for selected components using R/A/G:
4.1. Security (PII in prompts/logs, credentials, input validation)
4.2. Observability (logging, metrics, tracing)
4.3. Traceability and audit (decision logging, correlation ID)
4.4. Compliance (APRA/ASIC: explainability, PDS versioning, human override)
4.5. Versioning and source control
4.6. Testing
4.7. Error handling and resilience
4.8. Deployment and operations
4.9. Cost and performance
4.10. Cost projections (per-claim breakdown, 3 volume tiers)
4.11. FTE impact estimate

Compile consolidated R/A/G scorecard (only for selected components).

**After completing**: Report summary + scorecard. Ask: "Phase 4 complete. Review output/04_prod_readiness.md. Ready for Phase 5 (final synthesis)?"

**WAIT for user confirmation.**

---

## PHASE 5: Synthesis and Final Report
**Output**: `output/05_FINAL_REPORT.md` + `output/05b_BUSINESS_CASE_INPUT.md`
**Pre-req**: Read ALL prior outputs that exist + reference/framework_comparison.md (if exists)
**Note**: If only some phases were run, synthesize from available data only. Note gaps explicitly.

Tasks:
5.1a. Agent instruction prompt review (skip if C2 not reviewed)
5.1b. Claims check prompt review (skip if C1 not reviewed)
5.2. Architecture diagrams (4 text diagrams — for reviewed components only)
5.3. Consolidated bug list (merge from all available phases)
5.4. Risk register (likelihood x impact)
5.5. Production roadmap (P0/P1/P2 in dependency order)
5.6. Integration design (how C2 should invoke C1) — skip if only one component reviewed
5.7. Target architecture recommendation
5.8. Production readiness gates (measurable go-live criteria)
5.9. Business case summary (separate file: cost/benefit, FTE, timeline, risks)
5.0. Executive summary (write last, 10 lines for Ben/Francis)

**After completing**: Report summary to user. Present deliverable list.

---

## Final Deliverables

```
output/
  01_discovery.md            — File tree, imports, AWS, code metrics
  02_component1.md           — Bug validation, CHECK_REGISTRY, extraction code
  03_component2_3.md         — Agent definitions, orchestration, SQL, UI
  04_prod_readiness.md       — R/A/G scorecard, cost projections, FTE impact
  05_FINAL_REPORT.md         — Consolidated technical report + roadmap
  05b_BUSINESS_CASE_INPUT.md — Business summary for Francis/GLT
```

Only files for completed phases will be created.

## Estimated Cost

| Phase | Model | Est. Cost |
|-------|-------|-----------|
| 01 Discovery | Sonnet + Haiku explores | ~$0.80 |
| 02 Component 1 | Sonnet + Sonnet reviews | ~$1.35 |
| 03 Components 2+3 | Sonnet + Sonnet generals | ~$1.35 |
| 04 Prod Readiness | Sonnet + Haiku explores | ~$1.05 |
| 05 Synthesis | Sonnet only | ~$1.30 |
| **Full review** | | **~$5.85** |
| **C1 only (phases 1,2,4,5)** | | **~$4.50** |
| **C2 only (phases 1,3,4,5)** | | **~$4.50** |
| **Discovery only (phase 1)** | | **~$0.80** |
