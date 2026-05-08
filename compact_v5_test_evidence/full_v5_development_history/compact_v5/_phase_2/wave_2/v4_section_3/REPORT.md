# Phase 2 Wave 2: v4 Section 3 (Lines 6000–9000) Investigation

## Overview
Analyzed v4 sagemaker_agent.py lines 6000–9000 (charts, PDF, vision, semantic search, skills, sub-agent system, tool registry, AGENT_TYPES dict, Agent class, Agent.run loop). **Key finding: v5 drops AGENT_TYPES multi-agent registry in Phase 9, reducing from 7 agent types to 1 hardcoded general type.**

---

## Critical Finding: AGENT_TYPES Reduction

### v4: 7 Agent Types (Lines 6911–7082)
- **build** (120 chars, 25 turns): Full-access dev agent
- **plan** (200 chars, 15 turns): Read-only planning with PLAN_MODE_PROMPT
- **explore** (270 chars, 10 turns): Fast search with 4 tools
- **verify** (1400+ chars, 15 turns): Adversarial testing with 9-step framework
- **general** (120 chars, 15 turns): Default catch-all
- **review** (550 chars, 10 turns): 3-parallel code review (reuse/quality/efficiency)
- **fork** (None, 15 turns): Lightweight child with parent context reuse, flag-based

### v5 Phase 9: 1 Agent Type Only
Only `general` hardcoded in `subagent/spawn.py:41–48` (~80 chars). Reason (spawn.py:10–12): "Drops AGENT_TYPES configuration registry — Phase 9 supports general only; build/plan/explore/verify agent types are deferred (their large prompts are reviewable as data later)."

---

## What Regresses Without AGENT_TYPES

| Component | v4 Feature | v5 Status | Regression Impact |
|---|---|---|---|
| **verify agent** | 1400+ chars adversarial guidance (boundary values, concurrency, idempotency, repeat, silent-loss checks) | MISSING | No structured verification framework; testing becomes ad-hoc |
| **review agent** | 550 chars 3-parallel review (reuse/quality/efficiency with specific checks) | MISSING | No parallel review; single-pass code review only |
| **build worktree** | Git isolation to prevent agent mistakes corrupting parent | MISSING | Build sub-agent damage affects original workspace |
| **plan mode** | Read-only PLAN_MODE enforcement (blocks accidental writes during planning) | MISSING | No explicit planning discipline; agent can modify when it shouldn't |
| **explore agent** | Explicit "fast search" with 10-turn limit | MISSING | General agent has 15 turns; no explicit exploration signal |
| **fork pattern** | Lightweight child inheriting parent context (cheap background work) | MISSING | No lightweight fork semantics; general agents are heavier |
| **Config overrides** | Users override prompts/tools/max_turns in agent_config.json | MISSING | Hardcoded types; users need code changes to tune |

---

## Port Summary Table

| v4 Block | Lines | v5 Location | Status | Severity |
|---|---|---|---|---|
| Charts (matplotlib) | 6039–6256 | `tools/chart.py` | PARTIAL | LOW |
| PDF (reportlab) | 6282–6414 | `tools/pdf.py` | PARTIAL | MEDIUM |
| Vision (base64 queue) | 6419–6452 | `tools/vision.py` | PRESENT | LOW |
| Semantic search (Titan embeddings) | 6461–6669 | MISSING | MISSING | MEDIUM |
| Skill tool + patching | 6674–6735 | `tools/skill.py` | PARTIAL | MEDIUM |
| Web fetch (SSRF, redirects) | 6787–6846 | `tools/web.py` | PRESENT | LOW |
| Todo list + nudge | 6854–6895 | `tools/todo.py` | PRESENT | LOW |
| PLAN_MODE_PROMPT + tools | 6898–6908 | MISSING (plan agent deferred) | MISSING | MEDIUM |
| **AGENT_TYPES dict** (7 types) | **6911–7082** | **MISSING (only general in spawn.py:41–48)** | **MISSING** | **CRITICAL** |
| AGENT_TYPES config merge | 7084–7101 | MISSING | MISSING | CRITICAL |
| TOOLS registry (28 tools) | 7105–7400 | `tools/__init__.py` | PARTIAL | LOW |
| SYSTEM_PROMPT static | 8029–8178 | `prompt/sections.py` | PRESENT | LOW |
| IterationBudget + exec budget | 8190–8276 | `core/budget.py` | PRESENT | LOW |
| Agent.__init__() | 8281–8328 | `core/query_engine.py` | PRESENT | LOW |
| Agent._run_ask_user_tool() | 8330–8349 | `subagent/user_interaction.py` | PRESENT | LOW |
| Agent._run_task_tool() (worktree + spawn) | 8350–8550 | `subagent/spawn.py` (worktree removed) | PARTIAL | MEDIUM |
| _build_subagent_env_details() | 8695–8738 | `subagent/env.py` | PRESENT | LOW |
| _build_subagent_handoff_block() | 8771–8841 | `subagent/handoff.py` | PRESENT | LOW |
| Agent.run() main loop | 8650–8900+ | `core/query_engine.py` | PARTIAL | LOW |
| Microcompact + context collapse | 8794–8815 | `core/compaction.py` | PRESENT | LOW |
| Smart compact (2-stage) | 8817–8846 | `core/compaction.py` | PRESENT | LOW |
| LLM call + tool dispatch + retry | 8850+ | `core/query_engine.py` + `core/retry.py` | PARTIAL | LOW |

---

## Specific Gaps for Content Review (v6+)

1. **Verify Agent Prompts** (v4 lines 6938–7020, 1400+ chars)
   - Failure patterns to avoid (avoidance, seduced by 80%, false confidence)
   - Required steps (build, tests, linters, regression checks)
   - Type-specific strategies (backend/API, CLI, infrastructure, library, bug fixes, ML, database, refactoring, Python, other)
   - Adversarial probes (boundary values, concurrency, idempotency, orphan operations)
   - Rationalizations to recognize
   - Output format with command/output/result structure
   - Before PASS/FAIL checklists

2. **Review Agent Prompts** (v4 lines 7028–7074, 550 chars)
   - 3 review dimensions (reuse, quality, efficiency) with specific checks for each
   - Code reuse checks (utilities, duplication, inline logic)
   - Code quality checks (redundancy, parameter sprawl, leaky abstractions, stringly-typed, dead code)
   - Efficiency checks (unnecessary work, missed concurrency, hot-path bloat, N+1, TOCTOU, memory, overly broad)
   - Security checks (always applicable regardless of assigned focus)
   - Positive observations requirement
   - Severity + file:line + specific fix format

3. **Build Agent Isolation** (v4 lines 8413–8550)
   - Git worktree spawn, auto-init, UUID naming, dirty-state overlay
   - Prevents build mistakes from corrupting parent workspace
   - Integration with status-doc and recent-diffs

4. **Fork Agent Pattern** (v4 lines 7075–7082)
   - Lightweight child inheriting parent's full messages (no deep copy per message)
   - Directive-style prompts (short, no context needed)
   - Cheap background research while parent continues

5. **Config Override System** (v4 lines 7084–7101)
   - agent_overrides.items() → update prompt_suffix, tools, max_turns
   - Create new custom agent types via config
   - Missing in v5 hardcoded-types approach

---

## Deferred Items (Known Gaps, Noted in Code)

From v5 `subagent/spawn.py:10–12`:
> "Drops AGENT_TYPES configuration registry — Phase 9 supports general only; build/plan/explore/verify agent types are deferred (their large prompts are reviewable as data later)."

These are **intentional deferrals** for Phase 9 scope containment. v6+ will restore them from audit of v4 prompts.

