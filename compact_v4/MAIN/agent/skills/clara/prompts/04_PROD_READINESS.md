# Prompt 4: Production Readiness Assessment

> **Pre-requisite**: Read `00_CONTEXT.md`, then read ALL prior outputs:
> - `output/01_discovery.md`
> - `output/02_component1.md`
> - `output/03_component2_3.md`
> **Output file**: `output/04_prod_readiness.md`
> **Estimated turns**: 15-20
> **Expected output**: ~3000-4000 words, R/A/G scorecard + detailed sections + cost projections

## EXECUTION STRATEGY
- This prompt is analysis-heavy. Use targeted `grep` scans, not full file reads.
- Use `explore` sub-agents for grep-heavy scans (e.g., "find all print statements across the codebase").
- Reference file:function from prior outputs — only re-read files when you need to verify something specific.
- **CRITICAL**: After each section, IMMEDIATELY append to `output/04_prod_readiness.md`.
- **Append method**: See `00_CONTEXT.md` "APPEND METHOD" section. Use `write_file` with `mode: "append"`.

---

## LABELING RULE

For every finding in this prompt:
- `[verified]` = you confirmed from code in this session or a prior prompt's output
- `[assumed]` = from context, estimates, or the existing review — not code-confirmed
- `[NOT VERIFIED — requires access to X]` = you cannot check this from the codebase

---

## Tasks

For EACH area below, assess EACH component (C1, C2, C3) separately. Rate using the R/A/G thresholds defined in `00_CONTEXT.md`.

### 4.1 Security

**PII Assessment** (use the PII patterns from `00_CONTEXT.md`):
- [ ] Grep for each PII pattern type: TFN, policy numbers, DOB, medical data, names, addresses
- [ ] Check: are these sent to the LLM in prompt strings? → grep for PII field names near `invoke_model`, `bedrock`, `prompt`
- [ ] Check: are these logged? → grep for PII field names near `print(`, `logger.`, `logging.`
- [ ] Check: are these stored unencrypted in S3 or local files?

**Other security checks**:
- [ ] Credential storage — for each credential found in discovery, how is it stored?
- [ ] Input validation — any validation on user messages before sending to agent?
- [ ] Prompt injection defences — any sanitisation of user input?
- [ ] Sensitive data in codebase — any .env files, API keys, passwords committed?

| Area | C1 | C2 | C3 | Evidence | Critical Gaps |
|------|----|----|----|---------|----|
| PII in prompts | R/A/G | R/A/G | R/A/G | [file:function] | |
| PII in logs | R/A/G | R/A/G | R/A/G | [file:function] | |
| Credentials | R/A/G | R/A/G | R/A/G | [file:function] | |
| Input validation | R/A/G | R/A/G | R/A/G | [file:function] | |

**Write to output file now**

### 4.2 Observability
- [ ] Logging: grep for `print(`, `logger.`, `logging.`, `CloudWatch` — what's logged per component?
- [ ] Metrics: any timing capture? token counting? cost tracking? error rate tracking?
- [ ] Agent tracing: can you see the full reasoning chain? Is it logged?
- [ ] Dashboards/alerting: any CloudWatch dashboards, SNS alerts, PagerDuty?

Rate: GREEN = structured logging + metrics + tracing. RED = no logging or only `print()`. AMBER = some logging but inconsistent.
**Write to output file now**

### 4.3 Traceability & Audit
- [ ] Decision logging: are check results + reasoning + evidence saved?
- [ ] Correlation ID: can you trace a single claim across all components?
- [ ] Prompt/model version recording: does each assessment record which model + prompt version was used?
- [ ] Reproducibility: is temperature = 0.0? Any randomness in the pipeline?
**Write to output file now**

### 4.4 Compliance (APRA/ASIC)
- [ ] Explainability: can a regulator understand why a claim was assessed a certain way?
- [ ] PDS version integrity: BUG-009 status — is the right PDS version used?
- [ ] Human override: can an assessor override the AI decision?
- [ ] Data retention: how long are results kept? Where?
- [ ] Model governance: change management process for prompts/model updates?

Rate: GREEN = audit trail + explainability + PDS version tracking + human override. RED = no audit trail, no explainability.
**Write to output file now**

### 4.5 Versioning & Source Control
- [ ] Is ALL code in Git? What's missing? (reference 00_CONTEXT known gaps)
- [ ] Prompt versioning: are prompts versioned or just inline strings?
- [ ] Agent config versioning: are agent definitions tracked?
- [ ] Branching strategy? Code review evidence (PRs)?
- [ ] IaC for AWS resources? (CloudFormation, CDK, Terraform)
**Write to output file now**

### 4.6 Testing
- [ ] Unit tests — any test files? pytest? unittest?
- [ ] Integration tests — any end-to-end test scripts?
- [ ] Agent evaluation — any prompt testing or LLM output validation?
- [ ] CI/CD pipeline configs (.github/workflows, buildspec.yml, Jenkinsfile)?
- [ ] Test data management — how are test cases managed?

Rate: GREEN = pytest/unittest with >50% coverage. RED = zero test files. AMBER = test files exist but minimal or only manual notebooks.
**Write to output file now**

### 4.7 Error Handling & Resilience
For EACH external call type, check separately:

| Service | Retry Logic? | Timeout? | Error Catch? | Graceful Degradation? | File:Function |
|---------|-------------|---------|-------------|---------------------|---------------|
| Bedrock API | ? | ? | ? | ? | ? |
| S3 | ? | ? | ? | ? | ? |
| Snowflake | ? | ? | ? | ? | ? |
| Textract | ? | ? | ? | ? | ? |
| Lambda | ? | ? | ? | ? | ? |

Also check:
- Rate limit (429) handling?
- Token limit (>200K) handling?
- Fallback model if Claude unavailable?
- If one sub-agent fails, does the whole system crash?

Rate: GREEN = retry + timeout + graceful degradation on all external calls. RED = no error handling. AMBER = some try/except but no retry/timeout.
**Write to output file now**

### 4.8 Deployment & Operations
- [ ] Current runtime: SageMaker notebook? EC2? Lambda?
- [ ] How to deploy: manual? script? IaC?
- [ ] Dependency management: pinned versions? requirements.txt?
- [ ] Monitoring: any health checks? uptime monitoring?
**Write to output file now**

### 4.9 Cost & Performance
- [ ] Token tracking: is token usage recorded per assessment?
- [ ] Cost per assessment: calculated? logged?
- [ ] Caching: any caching of S3 reads, Bedrock responses, Snowflake queries?
- [ ] S3 call optimization: are the 62 redundant calls addressed?
- [ ] Parallelisation: any checks run in parallel?
- [ ] Batch processing: any queue/async infrastructure for multiple claims?
**Write to output file now**

---

## CONSOLIDATED R/A/G SCORECARD

After completing all 9 areas, compile the summary scorecard:

| Area | C1 | C2 | C3 | Critical Gaps |
|------|----|----|----|----|
| Security | R/A/G | R/A/G | R/A/G | ... |
| Observability | R/A/G | R/A/G | R/A/G | ... |
| Traceability | R/A/G | R/A/G | R/A/G | ... |
| Compliance | R/A/G | R/A/G | R/A/G | ... |
| Versioning | R/A/G | R/A/G | R/A/G | ... |
| Testing | R/A/G | R/A/G | R/A/G | ... |
| Error Handling | R/A/G | R/A/G | R/A/G | ... |
| Deployment | R/A/G | R/A/G | R/A/G | ... |
| Cost/Perf | R/A/G | R/A/G | R/A/G | ... |

**Write the scorecard as the LAST append to the output file.** It naturally summarises all prior sections. The Output Format section below lists it first for reading order, but write it last since you need all 9 area assessments complete before you can fill it in.

---

### 4.10 Cost Projections (for Business Case)

**Step 1: Verify baseline** from code/artifacts (from prior prompt outputs):
- Current cost per claim: $X — `[verified]` or `[assumed from context]`?
- Token counts: input/output per claim
- S3 API calls per claim
- Textract calls per claim (if applicable)

**Step 2: Calculate cost breakdown per claim (use `python_exec` for arithmetic if available):**
1. **Bedrock cost** = (input_tokens / 1000) × $0.003 + (output_tokens / 1000) × $0.015 (Claude 3.5 Sonnet US base)
2. Apply ~10% regional premium for ap-southeast-2
3. **S3 cost** = GET requests × $0.0004/1000 + PUT requests × $0.005/1000
4. **Textract cost** = pages × $0.0015 (detect text) or $0.015 (analyse document)
5. **Snowflake cost** = `[assumed — requires warehouse sizing data]`
6. **Total per claim** = sum of above

**Step 3: Project at scale:**

| Volume | Daily Claims | Cost/Claim | Monthly Cost | Annual Cost | Notes |
|--------|-------------|-----------|-------------|-------------|-------|
| Pilot | 10/day | $X | calculated | calculated | Current architecture |
| Phase 1 | 50/day | $Y | calculated | calculated | With S3 caching (saves ~$0.19/claim) |
| Scale | 200/day | $Z | calculated | calculated | With parallelisation + prompt caching |

**Step 4: Optimisation opportunities:**
- S3 caching: 62 redundant calls eliminated → $X saved per claim
- Prompt caching: Bedrock cache pricing = 90% discount on cached input tokens → $Y saved
- Check parallelisation: same cost, higher throughput (X claims/hr → Y claims/hr)
- Model selection: Haiku for simple checks = ~75% cheaper per token for those checks
- Batch processing: amortise fixed costs across multiple claims

Tag each projection: `[verified from code]` or `[assumed — calculation based on X]`
**Write to output file now**

### 4.11 FTE Impact Estimate
- Manual claim time: **3 hours per claim** `[assumed — requires validation from Mary/claims team]`
- Clara processing time: extract from code artifacts — verify the 95.2s baseline
- Human review time after Clara: **30 minutes** `[assumed — requires validation]`
- **Net time saving per claim**: calculated
- **Annual FTE equivalent**: at Y claims/year, saves Z FTE-hours

| Metric | Manual Process | Clara-Assisted | Saving | Source |
|--------|---------------|----------------|--------|--------|
| Time per claim | ~3 hrs | ~30 min review | ~2.5 hrs | `[assumed]` |
| Claims per assessor/day | ~2.5 | ~10+ | 4x throughput | `[assumed]` |
| Cost per claim (labour) | $X | $Y | $Z saved | `[assumed — requires salary data]` |

**Write to output file now**

---

## Output Format
Your `output/04_prod_readiness.md` should have:

1. **R/A/G Scorecard** (summary table at top — 9 areas × 3 components)
2. **Detailed findings per area** (sections 4.1-4.9 with file:function references)
3. **Cost per claim breakdown** (Bedrock, S3, Textract, Snowflake)
4. **Cost projections at scale** (pilot/phase1/scale volumes)
5. **Optimisation opportunities** with estimated savings
6. **FTE Impact Analysis** (manual vs Clara-assisted, clearly labeled estimates vs verified)
