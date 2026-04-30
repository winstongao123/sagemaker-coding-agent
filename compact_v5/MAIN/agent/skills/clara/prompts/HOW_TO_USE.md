# How to Use These Split Prompts with compact_v3

## Before You Start

### 0. Blocker Status: ALL FIXED
All 4 blocker bugs in compact_v3 have been fixed in the current `sagemaker_agent.py`. No patches needed. See `AGENT_BUGS.md` for proof with line numbers.

The workflow is ready to run as-is.

### 1. Agent Config — Add to `opencode.json`
Copy these overrides into your `opencode.json` to set sub-agent turn limits and model assignments:

```json
{
  "model_id": "au.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "agents": {
    "explore": { "max_turns": 20, "model": "au.anthropic.claude-haiku-4-5-20251001-v1:0" },
    "review": { "max_turns": 20 },
    "general": { "max_turns": 25 }
  }
}
```

### 1b. Model Selection per Prompt

compact_v3 supports per-sub-agent model overrides. Default: Claude 4.5 across the board.

| Role | Model | ID | Cost/1M in |
|------|-------|-----|------------|
| **Main agent** | Claude 4.5 Sonnet (AU) | `au.anthropic.claude-sonnet-4-5-20250929-v1:0` | $3.30 |
| **explore sub-agents** | Claude 4.5 Haiku (AU) | `au.anthropic.claude-haiku-4-5-20251001-v1:0` | $1.10 |
| **review sub-agents** | Claude 4.5 Sonnet (AU, same as main) | inherits from main | $3.30 |
| **general sub-agents** | Claude 4.5 Sonnet (AU, same as main) | inherits from main | $3.30 |

**Per-prompt cost estimates:**

| Prompt | Main Model | Sub-Agent Model | Est. Token Usage | Est. Cost |
|--------|-----------|----------------|-----------------|-----------|
| 01 Discovery | 4.5 Sonnet | 4.5 Haiku (explore) | ~80K in + 30K out | ~$0.80 |
| 02 Component 1 | 4.5 Sonnet | 4.5 Sonnet (review) | ~150K in + 50K out | ~$1.35 |
| 03 Components 2&3 | 4.5 Sonnet | 4.5 Sonnet (general) | ~150K in + 50K out | ~$1.35 |
| 04 Prod Readiness | 4.5 Sonnet | 4.5 Haiku (explore) | ~120K in + 40K out | ~$1.05 |
| 05 Synthesis | 4.5 Sonnet | None (read+write) | ~100K in + 60K out | ~$1.30 |
| **Total** | | | **~600K in + 230K out** | **~$5.85** |

Note: AU regional models have 10% premium over US pricing. All estimates include cache discounts.

### 2. Workspace
Set the agent's **workspace** to the ClaRA codebase root folder (the folder containing all 3 components). This is critical — the agent can only read files within its workspace.

### 3. Pre-Flight Checklist

Before running Prompt 1, verify ALL of the following:

- [ ] `opencode.json` has the agent config from step 1
- [ ] Workspace points to ClaRA codebase root
- [ ] `00_CONTEXT.md` is copied into the ClaRA root: `cp 00_CONTEXT.md <ClaRA_root>/00_CONTEXT.md`
- [ ] Output folder exists: `mkdir -p output`
- [ ] Reference folder exists: `mkdir -p reference`
- [ ] **(Recommended)** Copy your End-to-End Review as `reference/end_to_end_review.md` into the workspace. This lets Prompt 2 validate and enhance your existing report instead of starting from scratch.
- [ ] **(Optional)** If you have a framework comparison doc, copy it as `reference/framework_comparison.md`
- [ ] Confirm the agent can read files: test with "read 00_CONTEXT.md and tell me the first heading"

---

## Running the Prompts

### Run order: 01 -> 02 -> 03 -> 04 -> 05 (sequential, NOT parallel)

Each prompt depends on outputs from previous prompts.

---

### Prompt 1: Discovery
**Paste into chat:**
> Read 00_CONTEXT.md first. Then follow the instructions in 01_DISCOVERY.md exactly. Write all findings to output/01_discovery.md as you complete each section. Do not hold findings in memory.

**Expected time**: 5-10 minutes

**Success criteria:**
- [ ] `output/01_discovery.md` exists and is non-empty
- [ ] Contains file tree with component mapping
- [ ] Contains dependency list (from requirements.txt or import scanning)
- [ ] Contains AWS resource inventory table
- [ ] Contains code metrics (lines per component)
- [ ] All 9 sections present

**If incomplete:** Paste: "Continue from where output/01_discovery.md left off. Read the file and pick up from the last completed section."

---

### Prompt 2: Component 1 Validation
**Paste into chat:**
> Read 00_CONTEXT.md and output/01_discovery.md first. Then follow 02_COMPONENT1.md exactly. Use `review` sub-agents for bug validation — spawn one per bug. Write findings to output/02_component1.md after each section.

**Expected time**: 10-15 minutes

**Success criteria:**
- [ ] All 9 bugs show CONFIRMED/NOT CONFIRMED with file:function references
- [ ] CHECK_REGISTRY table is complete (all 21 checks listed)
- [ ] Document Extraction code (Phase 1) files identified
- [ ] Pipeline configurations listed
- [ ] If `reference/end_to_end_review.md` exists: validation findings present

---

### Prompt 3: Components 2 & 3
**Paste into chat:**
> Read 00_CONTEXT.md and output/01_discovery.md first. Then follow 03_COMPONENT2_3.md exactly. Use `general` sub-agents for orchestration tracing. Write findings to output/03_component2_3.md after each section.

**Expected time**: 10-15 minutes

**Success criteria:**
- [ ] Agent definitions table populated
- [ ] Orchestration diagram (ASCII) present
- [ ] SQL queries listed with injection risk assessment
- [ ] UI assessment complete (even if minimal)
- [ ] PS_ file summaries included (if PS_ files found in C2/C3)

---

### Prompt 4: Production Readiness
**Paste into chat:**
> Read 00_CONTEXT.md, then read output/01_discovery.md, output/02_component1.md, and output/03_component2_3.md. Follow 04_PROD_READINESS.md exactly. Write findings to output/04_prod_readiness.md after each section.

**Expected time**: 8-12 minutes

**Success criteria:**
- [ ] R/A/G scorecard complete (9 areas x 3 components = 27 ratings)
- [ ] Each rating has file:function evidence
- [ ] Cost per claim breakdown calculated
- [ ] Cost projections at 3 volume tiers
- [ ] FTE impact table with `[verified]`/`[assumed]` labels

---

### Prompt 5: Synthesis & Roadmap
**Paste into chat:**
> Read 00_CONTEXT.md, then read ALL files in output/ folder (01 through 04). If reference/framework_comparison.md exists, read that too. Follow 05_SYNTHESIS.md exactly. Write the final report to output/05_FINAL_REPORT.md section by section. Write business case to output/05b_BUSINESS_CASE_INPUT.md.

**Expected time**: 10-15 minutes

**Success criteria:**
- [ ] `output/05_FINAL_REPORT.md` — 3000-5000 words, 13 sections, tables over prose
- [ ] `output/05b_BUSINESS_CASE_INPUT.md` — 1000-2000 words, non-technical, numbers-focused
- [ ] Consolidated bug list (highest severity wins for duplicates)
- [ ] Risk register with likelihood/impact
- [ ] Phased roadmap (P0/P1/P2) in dependency order

---

## Framework Comparison (Do Separately)
The agent cannot do the Bedrock Inline Agents vs Agent Core vs LangGraph comparison from code alone. Do this separately:

**Option A**: Ask Claude directly (not through the agent):
> "Compare Bedrock Inline Agents, Amazon Bedrock Agent Core, and LangGraph for a regulated life insurance claims AI system (Australian market, APRA/ASIC compliance, audit trails required). Fill in this comparison matrix: [paste matrix from original prompt]"

**Option B**: Research and write `reference/framework_comparison.md` yourself, then it gets picked up by Prompt 5.

---

## Failure Recovery

| Problem | Fix |
|---------|-----|
| Agent hits max turns mid-prompt | Start a new session. Paste: "Continue from where output/0X_xxx.md left off. Read the file and pick up from the last completed section." |
| Agent doesn't use sub-agents | Be explicit: "Use a review sub-agent to validate BUG-001" |
| Output file is empty/incomplete | Check if compaction happened (look for "[CONVERSATION SUMMARY]" in chat). If so, restart that prompt from the last completed section. |
| Agent reads files but forgets findings | It's compacting. Remind: "Write your findings to the output file NOW before continuing." |
| Agent skips a section | Paste: "You skipped section X.Y. Go back and complete it. Write findings to output file." |
| Agent says "file already in context" | This should not happen (Blocker 1 is fixed). If it does: restart the session. |
| Sub-agent returns "[INCOMPLETE]" | The sub-agent hit its turn limit. The full output is still returned (Blocker 3 fixed). Check if findings are sufficient; if not, spawn another sub-agent to continue. |
| Grep returns "[WARNING: Results capped]" | Normal behavior. Agent should narrow the search path. If it doesn't, remind: "Your grep was capped. Search one component folder at a time." |

### Disconnection Recovery
Sessions auto-save in compact_v3. If disconnected:
1. Reload the SageMaker session
2. Check `output/` folder — all written sections are preserved
3. Start a new chat and paste: "Read output/0X_xxx.md. I was on section X.Y. Continue from there."

Output files are the source of truth, not the chat history. As long as the agent wrote findings to file before disconnection, nothing is lost.

---

## What You Get at the End

```
output/
├── 01_discovery.md          # File tree, imports, AWS inventory, git history, code metrics
├── 02_component1.md         # Bug validation, CHECK_REGISTRY, extraction code, test evidence
├── 03_component2_3.md       # Agent definitions, orchestration, SQL, UI assessment
├── 04_prod_readiness.md     # R/A/G scorecard, gap analysis, cost projections, FTE impact
├── 05_FINAL_REPORT.md       # Consolidated technical report with roadmap, risks, gates
└── 05b_BUSINESS_CASE_INPUT.md  # Business-friendly summary for Ben/Francis/GLT
```

### Two Deliverables
1. **Production Readiness Assessment** (05_FINAL_REPORT.md) — Full technical review for Ben
2. **Business Case Input** (05b_BUSINESS_CASE_INPUT.md) — Cost/benefit, ROI, risk summary for Francis/GLT

### Future Development Reference
All output files double as **technical reference for the dev team**. Every finding has file:function references, [verified]/[assumed] labels, and specific enough detail that a developer can act on each item without re-reading the full codebase.
