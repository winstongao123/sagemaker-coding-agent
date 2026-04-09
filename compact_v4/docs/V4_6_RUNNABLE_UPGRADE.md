# V4.6.0 — Runnable-Grade Review System

## What This Upgrade Does

Ports Runnable's (Claude Code internal) best prompt engineering patterns into V4's skill + sub-agent system, closing 3 critical capability gaps.

## Gap Analysis: Before vs After

| Capability | V4.5 (Before) | V4.6 (After) | Runnable |
|-----------|---------------|-------------|----------|
| Review approach | Single agent, monolithic checklist | 3 parallel agents (reuse + quality + efficiency) | 3 parallel agents (simplify) |
| Verification mindset | Confirmatory ("does it work?") | Adversarial ("how can I break it?") | Adversarial (verification agent) |
| Anti-rationalization | None | 4 named excuses + counters | 6 named excuses + counters |
| Evidence format | Free-form report | Command + Output + Result (mandatory) | Command + Output + Result (mandatory) |
| Type-specific strategies | Generic checklist | 7 change types with specific steps | 10 change types with specific steps |
| Security review | Basic checklist in review skill | Dedicated 3-phase skill with confidence scoring | 3-phase command with false-positive filtering |
| False-positive filtering | None | 14 hard exclusions, 7 precedents, confidence 0.8+ | 16 hard exclusions, 12 precedents, confidence 0.8+ |
| Feedback loop | None — review is final | Feedback Refinement section in review skill | Simplify aggregates + fixes directly |
| Fix capability | Review reports only | Review + simplify both fix issues directly | Simplify fixes directly |
| Machine-parseable output | None | VERDICT: PASS/FAIL/PARTIAL | VERDICT: PASS/FAIL/PARTIAL |
| Adversarial probes | "Test edge cases" (vague) | Specific: boundary, concurrency, idempotency, orphan | Specific: concurrency, boundary, idempotency, orphan |

## New Skills

### `/skill use simplify`
3-agent parallel review that FIXES issues, not just reports them.

```
Phase 1: git diff → identify changes
Phase 2: Launch 3 agents in parallel:
  - Agent 1 (review): Code Reuse — search for duplicates
  - Agent 2 (review): Code Quality — anti-patterns
  - Agent 3 (review): Efficiency — performance issues
Phase 3: Aggregate → fix each issue → summarize
```

### `/skill use security-review`
Focused vulnerability assessment with aggressive false-positive filtering.

```
Step 1: Repository context research (understand existing security posture)
Step 2: Comparative analysis (deviations from established patterns)
Step 3: Vulnerability assessment (trace data flow, injection points)
Filter: Only HIGH/MEDIUM findings with confidence >= 0.8
```

## Upgraded Skills

### `/skill use verify` (Rewritten)
Adversarial verification specialist. Key additions:
- **Failure patterns**: Names verification avoidance and "seduced by first 80%"
- **Anti-rationalization**: "reading is not verification", "probably is not verified"
- **Evidence requirement**: Every PASS needs Command + Output (no narrative)
- **Adversarial probe requirement**: Must try to break something before PASS

### `/skill use code-review` (Rewritten)
Now uses 3-agent parallel review (like simplify) plus security check and feedback loop.

## Runnable Prompt Engineering Patterns Ported

### 1. Parallel Agent Specialization
**Pattern**: Decompose review into orthogonal concerns (reuse vs quality vs efficiency), launch all in parallel, aggregate.
**Why it works**: Each agent goes deeper on one dimension than a single agent covering everything.
**V4 implementation**: `simplify` and `code-review` skills use `task` tool with 3 parallel `subagent_type: "review"` calls.

### 2. Anti-Rationalization Prompting
**Pattern**: Name the exact excuses LLMs use to skip verification, then counter each one.
**Runnable examples**:
- "The code looks correct based on my reading" → reading is not verification. Run it.
- "The implementer's tests already pass" → the implementer is an LLM. Verify independently.
- "I don't have a browser" → did you check for playwright tools?
**V4 implementation**: Verify skill + verify agent type prompt_suffix include 4 named rationalizations.

### 3. Evidence-Based Verification
**Pattern**: Every check must have Command run + Output observed + Result. No narrative claims accepted.
**Why it works**: Prevents the LLM from "reading code" and declaring PASS without actually running anything.
**V4 implementation**: Both verify skill and verify agent type enforce this format with good/bad examples.

### 4. Type-Specific Strategies
**Pattern**: Different verification approach per change type (backend, CLI, bug fix, refactoring, etc.)
**Why it works**: "Run tests" is too generic. "Start server, curl endpoints, verify response shapes" is actionable.
**V4 implementation**: Verify skill includes 8 change types with specific verification steps.

### 5. False-Positive Filtering
**Pattern**: Confidence scoring (0.8+), hard exclusions (DOS, regex DOS, etc.), precedents (UUIDs unguessable, etc.)
**Why it works**: A report with 2 real vulnerabilities beats one with 10 false positives.
**V4 implementation**: Security-review skill includes 14 exclusions, 7 precedents, 4 signal quality questions.

### 6. Machine-Parseable Verdicts
**Pattern**: End with `VERDICT: PASS`, `VERDICT: FAIL`, or `VERDICT: PARTIAL` — parseable by caller.
**V4 implementation**: Both verify skill and verify agent type require this exact format.

### 7. Adversarial Probe Requirement
**Pattern**: Before issuing PASS, must have run at least one adversarial probe (boundary, concurrency, idempotency).
**Why it works**: Happy-path verification is worthless. The value is in finding what breaks.
**V4 implementation**: Verify skill's "Before Issuing PASS" section enforces this.

### 8. Feedback Refinement
**Pattern**: Review results can be refined based on user feedback (re-examine, update, fix).
**V4 implementation**: Code-review skill's "Feedback Refinement" section supports iterative improvement.

## Architecture Comparison

```
RUNNABLE REVIEW ARCHITECTURE:
  /simplify → git diff → 3 parallel Agent() calls → aggregate → fix
  /ultrareview → remote CCR session → bughunter orchestrator → findings
  verification agent → adversarial testing → VERDICT
  security-review → 3-phase analysis → confidence filter → report

V4.6 REVIEW ARCHITECTURE:
  /skill use simplify → git diff → 3 parallel task() calls → aggregate → fix
  /skill use code-review → security check → 3 parallel task() calls → aggregate → fix → feedback loop
  /skill use verify → adversarial testing → VERDICT
  /skill use security-review → 3-phase analysis → confidence filter → report
  verify agent type → adversarial sub-agent with anti-rationalization
  review agent type → specialized parallel reviewer
```

## Remaining Differences (V4 vs Runnable)

| Feature | Runnable Has | V4.6 Status |
|---------|-------------|-------------|
| Remote review sessions (ultrareview) | Yes — CCR bughunter | No — local only |
| Fork semantics (cheap context-inheriting agents) | Yes | No — fresh sub-agents only |
| Auto-invocation via trigger phrases | Yes — when_to_use field | No — manual /skill use |
| Billing/quota gating | Yes — overage dialog | No — Bedrock pricing only |
| Browser automation (Playwright, Chrome MCP) | Yes — verification agent | No — CLI/curl only |
| Reactive compaction | Yes — microcompaction | V4 has basic compaction |

These are infrastructure differences, not prompt quality. The prompt patterns (which drive actual review quality) are now at parity.
