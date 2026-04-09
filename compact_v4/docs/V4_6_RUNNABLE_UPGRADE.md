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

## Remaining Gaps — Full Honest Audit (7 Items)

Deep audit conducted 2026-04-10 comparing every behavioral pattern in Runnable's codebase against V4.6.0.

### Gap Summary

| # | Gap | Type | Fixable? | Effort | Impact |
|---|-----|------|---------|--------|--------|
| 1 | Verification contract in system prompt | PROMPT | Yes | 5 min | HIGH — model doesn't know it MUST verify after 3+ edits |
| 2 | `when_to_use` guidance for agent types | PROMPT | Yes | 10 min | MEDIUM — model doesn't know which agent to pick |
| 3 | Multi-agent false-positive filtering | SKILL | Yes | 15 min | MEDIUM — security review relies on single agent's judgment |
| 4 | Auto-nudge after 3+ task completions | CODE | Yes (Python) | Medium | HIGH — model forgets to verify unless reminded |
| 5 | `criticalSystemReminder` injection | CODE | Yes (Python) | Medium | MEDIUM — verify sub-agents can drift from format |
| 6 | Fork semantics (context-inheriting agents) | ARCHITECTURE | No | High | MEDIUM — sub-agents are expensive and context-blind |
| 7 | Skill discovery auto-surfacing | CODE | No | High | MEDIUM — model can't use skills it doesn't know about |

### Gap 1: Verification Contract in System Prompt (PROMPT fix)

**What Runnable does**: System prompt at `prompts.ts:394` states: "When non-trivial implementation happens (3+ file edits, backend/API changes, infrastructure changes), independent adversarial verification MUST happen before reporting completion. Spawn Agent with subagent_type=verification."

**What V4 has**: System prompt says "After 3+ file edits: spawn a verify sub-agent before reporting completion." But it's buried in "Doing Tasks" section, not a standalone contract.

**Fix**: Move to a dedicated `# Verification Contract` section in SYSTEM_PROMPT with stronger language.

### Gap 2: `when_to_use` Guidance for Agent Types (PROMPT fix)

**What Runnable does**: Each agent definition has a `whenToUse` field displayed in the Agent tool description:
- `explore`: "Fast agent for exploring codebases. Use when you need to find files, search code..."
- `verification`: "Use to verify implementation is correct. Invoke after 3+ file edits, backend/API changes..."
- `plan`: "Software architect agent for designing implementation plans..."

**What V4 has**: Agent types have `description` but it's only shown in the task tool's enum, not as guidance. The model sees "build, plan, explore, verify, general, review" but not WHEN to use each.

**Fix**: Expand the task tool description to include `when_to_use` for each agent type.

### Gap 3: Multi-Agent False-Positive Filtering (SKILL fix)

**What Runnable does**: Security review spawns parallel sub-agents, each independently verifying one finding. Only findings where confidence >= 0.8 survive. This is a 3-stage pipeline:
```
Stage 1: Agent A finds all potential vulnerabilities
Stage 2: Agents B, C, D (parallel) each verify 2-3 findings independently
Stage 3: Only findings verified with confidence >= 0.8 kept
```

**What V4 has**: Single agent does find + filter + report. Works, but single agents are more likely to confirm their own findings.

**Fix**: Update security-review skill to use 2-stage pattern with parallel verification agents.

### Gap 4: Auto-Nudge After 3+ Task Completions (CODE fix)

**What Runnable does**: `TodoWriteTool.ts:104-107` detects when 3+ tasks are marked complete without a verification step. Injects a NOTE into the tool result: "You just closed out 3+ tasks and none was a verification step. Before writing your final summary, spawn the verification agent..."

**What V4 has**: No automatic detection. Model must remember on its own.

**Fix**: Add nudge injection in `tool_todo_write()` when 3+ tasks move to "completed" status and none has "verif" in the name.

### Gap 5: `criticalSystemReminder` Injection (CODE fix)

**What Runnable does**: Agent definitions can set `criticalSystemReminder_EXPERIMENTAL` — a short string that's injected as a `<system-reminder>` attachment at EVERY user turn during the sub-agent's conversation. Example for verification agent: "CRITICAL: This is a VERIFICATION-ONLY task. You CANNOT edit, write, or create files IN THE PROJECT DIRECTORY."

**What V4 has**: The reminder is appended to `prompt_suffix` (seen once at start), not re-injected every turn.

**Fix**: Add `critical_reminder` field to AGENT_TYPES. In the agent loop, inject it as a system-level message before each LLM call.

### Gap 6: Fork Semantics — Context-Inheriting Agents (ARCHITECTURE — cannot fix)

**What it is**: Runnable can "fork" an agent — the fork inherits the parent's full conversation history and shares the prompt cache.

```
FRESH SUB-AGENT (V4):
  Parent has 50 messages of context
  Sub-agent starts with messages = [] (zero context)
  Must explain everything in the prompt text
  Pays full price for new prompt cache
  
FORK (Runnable):
  Parent has 50 messages
  Fork starts with all 50 messages pre-loaded
  Prompt is just a short directive ("now review what we discussed")
  Reuses parent's prompt cache (~$0 startup cost)
  Knows everything the parent knows
```

**Why it matters**:
- **Cost**: Forks share cache (nearly free). V4 sub-agents build new cache (~$0.01-0.05 each).
- **Quality**: Forks know the full conversation context. V4 sub-agents only know what's in their prompt.
- **Speed**: Forks skip re-uploading system prompt. V4 sub-agents re-upload everything.

**Why V4 can't add it**: V4's `Agent.__init__` creates `self.messages = []`. Fork would require:
1. Shared message history (reference, not copy — or efficient copy)
2. Shared cache tokens (BedrockClient would need to pass cache state)
3. Thread-safe branching (fork modifies messages without corrupting parent)
4. Bedrock API support for cache sharing across requests (may not exist)

This is a fundamental architecture change to `Agent`, `BedrockClient`, and the threading model.

**Impact**: Medium. For review/verify work (short-lived sub-agents with focused tasks), fresh sub-agents work fine because the prompt contains all needed context. Forks matter more for long research tasks where context accumulation is valuable.

### Gap 7: Skill Discovery Auto-Surfacing (CODE — cannot fix easily)

**What it is**: Runnable automatically searches "which skills match the current task?" and injects suggestions into the conversation.

```
MANUAL (V4):
  User types "fix this bug"
  Agent has NO IDEA that verify/simplify skills exist
  Never runs verification unless user explicitly says "/skill use verify"

AUTO-SURFACING (Runnable):
  User types "fix this bug"
  System searches: "which skills match 'fix bug'?"
  Finds: verify (when_to_use: "after implementation"), simplify (when_to_use: "review changes")
  Injects: "<system-reminder>Skills relevant to your task: verify, simplify</system-reminder>"
  Model sees suggestion → decides to use verify after fixing
```

**How Runnable implements it**: `prefetch.ts` calls a remote HTTP skill search service during query execution. Results are injected as `skill_discovery` attachments into the conversation. Feature-gated behind `EXPERIMENTAL_SKILL_SEARCH`.

**Why V4 can't easily add it**:
- Option A: Remote service — V4 has no HTTP service infrastructure for skill search.
- Option B: Keyword matching in Python — fragile, high false positive rate.
- Option C: Use LLM to decide — costs an extra API call per turn ($$$).
- Option D: Static mapping (skill → trigger keywords) — works but limited.

**Practical alternative for V4**: Option D is viable. Add a `triggers` field to skill YAML frontmatter listing keywords. In the agent loop, scan the user message for matches and inject a reminder. Example:
```yaml
---
name: verify
triggers: ["verify", "check", "test", "after edits", "before commit"]
---
```
This is ~30 lines of Python and covers 80% of cases.

**Impact**: Medium. Users who know V4's skills invoke them manually. New users miss skills entirely.

### Capability Rating After All Gaps Documented

| State | Weighted Rating | What's Included |
|-------|----------------|-----------------|
| V4.5 (before this session) | ~40% | Basic checklist review, confirmatory verification |
| V4.6.0 (current) | ~85% | Parallel review, adversarial verify, security review, evidence format |
| V4.6.0 + gaps #1-3 fixed | ~92% | + verification contract, agent guidance, FP filtering |
| V4.6.0 + gaps #1-5 fixed | ~97% | + auto-nudge, critical reminder injection |
| Theoretical maximum (no fork/discovery) | ~97% | Ceiling without architecture rework |
| Runnable | 100% | Fork semantics + skill discovery + infrastructure |
