# Prompt 5: Synthesis, Roadmap & Final Report

> **Pre-requisite**: Read `00_CONTEXT.md`, then read ALL prior outputs:
> - `output/01_discovery.md`
> - `output/02_component1.md`
> - `output/03_component2_3.md`
> - `output/04_prod_readiness.md`
> - `reference/framework_comparison.md` (if provided — see note below)
> **Output files** (TWO separate files):
> 1. `output/05_FINAL_REPORT.md` — technical report (sections 5.1-5.8)
> 2. `output/05b_BUSINESS_CASE_INPUT.md` — business summary (section 5.9)
> **Estimated turns**: 15-20
> **Expected output**: Main report ~3000-5000 words. Business case ~1000-2000 words.

## FILE ASSIGNMENT TABLE

| Section | Output File | Word Target |
|---------|-----------|-------------|
| 5.1a Agent Instruction Prompts | `output/05_FINAL_REPORT.md` | 300-500 |
| 5.1b Claims Check Prompts | `output/05_FINAL_REPORT.md` | 300-500 |
| 5.2 Architecture Diagrams | `output/05_FINAL_REPORT.md` | 500-800 |
| 5.3 Consolidated Bug List | `output/05_FINAL_REPORT.md` | 400-600 |
| 5.4 Risk Register | `output/05_FINAL_REPORT.md` | 300-500 |
| 5.5 Production Roadmap | `output/05_FINAL_REPORT.md` | 500-800 |
| 5.6 Integration Design | `output/05_FINAL_REPORT.md` | 300-400 |
| 5.7 Target Architecture | `output/05_FINAL_REPORT.md` | 300-400 |
| 5.8 Production Gates | `output/05_FINAL_REPORT.md` | 200-300 |
| Framework Comparison | `output/05_FINAL_REPORT.md` | 300-500 (if reference file exists) |
| Executive Summary | `output/05_FINAL_REPORT.md` | 100-150 (write last, 10 lines max) |
| 5.9 Business Case Summary | `output/05b_BUSINESS_CASE_INPUT.md` | 1000-2000 |

**Do NOT mix content between files.** Technical findings go to the main report. Business summary goes to the business case file.

## NOTE ON FRAMEWORK COMPARISON
If `reference/framework_comparison.md` exists, incorporate it into Section 6 of the final report.
If it does NOT exist, write: "## 6. Framework Comparison\nPENDING — done separately." and move on.

## EXECUTION STRATEGY
- This is a SYNTHESIS prompt. You should mostly READ prior outputs and WRITE the final report.
- Only re-read source code files if you need to verify or clarify a specific finding.
- **Build the report section by section, writing each to the output file immediately.**
- **Append method**: See `00_CONTEXT.md`. First write creates the file. Subsequent writes use `mode: "append"`.

## FUTURE DEVELOPMENT REFERENCE
All outputs from this prompt serve as **factual technical reference for future development**. Write as if a developer will use these files to plan and implement changes. Be specific: file:function references, concrete recommendations, measurable criteria.

---

## Tasks

### 5.0 Executive Summary (write LAST, after all other sections)
After completing ALL sections below (5.1 through 5.10), return to the main report and append a 10-line Executive Summary. Write it for Ben/Francis — no jargon, focus on: what Clara does, current state, top 3 gaps, cost/benefit headline, recommended timeline. This goes at the logical top of the report but is written last because it summarises everything.
**Append to `output/05_FINAL_REPORT.md` as the final write.**

### 5.1a Agent Instruction Prompts
From `output/03_component2_3.md` the **Agent Definitions Table** section, review each agent's instruction text.

| File:Function | Purpose (1-2 sentences) | Model | Temp | Output Format | Quality Issues |
|-------------|------------------------|-------|------|--------------|----------------|

Evaluate: Is it deterministic (temperature 0?)? Does it handle edge cases? Any ambiguity?
**Write to `output/05_FINAL_REPORT.md` now**

### 5.1b Claims Check Prompts
From `output/02_component1.md` the **CHECK_REGISTRY** section, for each check that calls Bedrock: find the prompt template in the source file.

Evaluate per prompt:
- Any logical flaws that could cause wrong claim decisions?
- Is the output format parseable? (JSON schema defined? or just free text?)
- Does it handle missing data gracefully?

**Write to `output/05_FINAL_REPORT.md` now**

### 5.2 Architecture Diagrams (text-based)
Create 4 text diagrams from the findings:

1. **System Architecture**: All components, AWS services, data stores, connections
2. **Agent Orchestration Map**: Supervisor -> sub-agents -> tools -> data sources
3. **Data Flow**: User input -> processing -> data sources -> output
4. **Sequence Diagram**: Single claim journey from UI to final report

Use ASCII box drawing or markdown-compatible diagram notation.
**Write to `output/05_FINAL_REPORT.md` now**

### 5.3 Consolidated Bug List
Merge from all outputs:
- 9 known bugs (validated status from Prompt 2)
- Any NEW bugs found in Prompts 2, 3, 4

**Bug merge rule**: If the same bug appears in multiple prompts, keep the entry with the highest severity and most detail. Do not duplicate. **Preserve `[verified]`/`[assumed]` labels from source outputs.**

| ID | Severity | Component | File:Function | Description | Confirmed | Business Impact |
|----|----------|-----------|-------------|-------------|-----------|----------------|

Order by: CRITICAL first, then HIGH, then MEDIUM, then LOW.
**Write to `output/05_FINAL_REPORT.md` now**

### 5.4 Risk Register

| Risk ID | Component | Category | Description | Likelihood | Impact | Mitigation | Owner |
|---------|-----------|----------|-------------|-----------|--------|------------|-------|

Categories: Security, Compliance, Operational, Technical, Data
Likelihood/Impact: High/Medium/Low

Derive risks from: bugs (5.3), R/A/G scorecard (Prompt 4), known gaps (00_CONTEXT.md).
**Write to `output/05_FINAL_REPORT.md` now**

### 5.5 Production Readiness Roadmap

**For each NOT IMPLEMENTED or PARTIALLY IMPLEMENTED finding from Prompt 4:**

| Item ID | Description | Component | Priority | Effort | Dependencies | Risk if Deferred |
|---------|-------------|-----------|----------|--------|-------------|-----------------|

Priority: P0 (blocker — must fix before production), P1 (required for launch), P2 (post-launch)
Effort: S (< 1 week), M (1-3 weeks), L (1-2 months)

**Dependency order**: List items so that dependencies come before dependent items. For example:
- "Set up CI/CD pipeline" (P0) must come before "Add automated testing" (P1)
- "Create requirements.txt" (P0) must come before "Pin all dependency versions" (P1)

Then organise into phases:

**Phase A: Pre-Production Blockers (P0)**
- List all P0 items in dependency order
- Estimated total effort

**Phase B: Production Launch (P1)**
- List all P1 items in dependency order
- Estimated total effort

**Phase C: Post-Launch Hardening (P2)**
- List all P2 items
- Estimated total effort

**Write to `output/05_FINAL_REPORT.md` now**

### 5.6 Integration Design
Based on Component 2 & 3 findings, propose:
- How Component 2 should invoke Component 1 (API contract)
- Data format for input/output
- Error handling and timeout strategy (95s baseline + margin)
- What needs to be built
- Batch processing integration (queue mechanism)

**Write to `output/05_FINAL_REPORT.md` now**

### 5.7 Target Architecture (if enough information)
Based on all findings:
- Recommend deployment architecture (Lambda/ECS/Step Functions)
- Scalability considerations for 100/500/1000 cases/day
- Cost projection at scale (reference Prompt 4 calculations)
- Batch processing recommendation (from 00_CONTEXT.md batch context)

**Write to `output/05_FINAL_REPORT.md` now**

### 5.8 Production Readiness Gates
Define measurable criteria for go-live:

| Gate | Metric | Target | Current State | Source |
|------|--------|--------|--------------|--------|

Examples: test coverage %, latency P95, PII redaction verified, audit trail completeness, model governance in place.
Tag Current State as `[verified]` or `[assumed]`.

**Write to `output/05_FINAL_REPORT.md` now**

---

### 5.9 Business Case Summary
**Write to `output/05b_BUSINESS_CASE_INPUT.md`** (NOT the main report):

#### 1. Current State Summary (for Francis/GLT)
- What Clara does today (2-3 sentences, no jargon)
- Current performance metrics (cost, speed, accuracy)
- What state it's in (prototype on SageMaker notebooks, not production)

#### 2. What's Needed for Production
- Top 10 gaps, described in business language
- Effort estimates (total: X person-months)
- External dependencies (cloud engineering, compliance, platform teams)

#### 3. Cost-Benefit Analysis
From Prompt 4 outputs:
- Investment needed: infrastructure, team effort, AWS costs
- Projected savings: FTE time reduction, cost per claim at scale
- Break-even estimate (if calculable)
- ROI projection (conservative/moderate/optimistic)

#### 4. Risk Summary (for Francis)
Top 5 risks in business terms:
| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|

#### 5. Proposed Timeline
Align with Francis's Q3 target:
- Q2 Apr-Jun: What gets done (Phase A + Phase B start)
- Q3 Jul-Sep: Production deployment for narrow scope
- Q4 Oct-Dec: Scale and iterate

#### 6. Team & Resource Requirements
- Current team: who does what
- Additional needs: platform, DevOps, compliance, testing
- Estimated FTE requirement for each phase

**Write to `output/05b_BUSINESS_CASE_INPUT.md` now**

---

## Final Report Structure
Assemble `output/05_FINAL_REPORT.md` with these sections:

1. **Executive Summary** (10 lines max — written for Ben/Francis, not engineers)
2. **Codebase Inventory** (from Prompt 1)
3. **Architecture Diagrams** (from 5.2)
4. **Component Assessments** (from Prompts 2 + 3)
5. **Production Readiness Scorecard** (from Prompt 4)
6. **Framework Comparison** (from reference file, or "PENDING — done separately")
7. **Prompt Review** (from 5.1)
8. **Bugs & Issues** (from 5.3)
9. **Risk Register** (from 5.4)
10. **Production Readiness Roadmap** (from 5.5)
11. **Integration Design** (from 5.6)
12. **Production Readiness Gates** (from 5.8)
13. **Cost & Scale Projections** (from Prompt 4 sections 4.10-4.11)

Additionally produce ONE separate file:
- `output/05b_BUSINESS_CASE_INPUT.md` — business-friendly summary for Ben/Francis

**Target: 3,000-5,000 words for main report. Tables over prose. Every sentence = a finding, reference, or recommendation.**
**Business case input: 1,000-2,000 words. Non-technical language. Numbers-focused.**
