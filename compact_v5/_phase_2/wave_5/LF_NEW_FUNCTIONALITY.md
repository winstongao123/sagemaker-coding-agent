# Learning Factory NEW FUNCTIONALITY SCAN — v5.0.1 Adoption

**Date**: 2026-05-01  
**Scope**: D:/Github/Learning_Factory/ line-by-line scan for NEW patterns vs v4  
**Status**: COMPLETE — 26 patterns scanned; 5 NEW-to-consider; 16 out-of-scope; 5 already in v5 plan

---

## FINDINGS SUMMARY

Learning Factory is a **process/workflow framework** (not architecture). It brings:
- **5 already in v5 plan**: state persistence, audit, pre-flight, CHANGELOG (no new code)
- **16 out-of-scope**: MCP, voice, HTML widgets, multi-project, global memory (irrelevant to single-user SageMaker)
- **5 NEW patterns** for v5.0.1: 4 via inherited hooks (CSO enforcement, task granularity, tool-failure detection, session cleanup) + 1 new command (skill-promotion workflow)

**Result**: v5 >= LF on process maturity. Recommend adopting 4 active patterns (3 inherited hooks + 1 new command). Defer session-end cleanup to v5.0.2.

---

## THE 5 NEW PATTERNS

### 1. CSO "Use when [symptoms]" Description Enforcement
**Source**: hooks/cso-check.sh (102 LOC)  
**How**: PreToolUse Bash hook blocks git commit if new descriptions lack "Use when" prefix  
**Why**: Better LLM agent discovery  
**v5 Decision**: ADOPT via inherited hook — document convention in CLAUDE.md  
**Cost**: 0 (external hook)  
**Evidence**: PORT_LOG row "CSO convention (R-105) inherited via LF hook"

### 2. Task Granularity Enforcement (>15 line blocks)
**Source**: hooks/task-granularity-check.sh (101 LOC)  
**How**: PreToolUse Bash hook blocks git commit if TASKS.md blocks exceed 15 lines  
**Why**: Atomic 2-5 min tasks enable parallel dispatch  
**v5 Decision**: ADOPT via inherited hook — reinforce in BUILD_GUIDE  
**Cost**: 0 (external hook)  
**Evidence**: PORT_LOG row "Task granularity enforcement inherited via LF hook"

### 3. Tool-Failure Loop Detection
**Source**: hooks/tool-failure-detect.sh (137 LOC)  
**How**: Tracks tool calls per session; blocks if 5+ same-tool calls OR 3+ consecutive failures  
**Why**: Prevent runaway agent loops (token waste)  
**v5 Decision**: OPTIONAL (safety enhancement) — inherit hook, document bypass  
**Cost**: 0 (external hook)  
**Evidence**: PORT_LOG row "Tool-failure loop detection (optional, CowAgent pattern)"

### 4. Session-End Cleanup Hook
**Source**: hooks/session-end.sh (50 LOC)  
**How**: Stop hook consolidates logs, dumps STATE.md, auto-pushes  
**Why**: Housekeeping automation  
**v5 Decision**: DEFER to v5.0.2 (v5 has explicit Save button; auto-save already implemented)  
**Cost**: N/A  
**Evidence**: Documented deferral (not silent drop)

### 5. Skill-Promotion Workflow
**Source**: docs/SKILL_PROMOTION_PROTOCOL.md + commands/promote-to-skill.md + hermes-agent  
**How**: Agent proposes complex task's learnings as SKILL.md → state/skill-proposals/ → Owner approves → ~/.claude/skills/<name>/  
**Why**: Turn hard-won wisdom into durable reusable skills  
**v5 Decision**: ADOPT (full implementation) — Block D command (~200 LOC) + Block K workflow  
**Cost**: ~200 LOC command handler  
**Evidence**: PORT_LOG rows + lock test "Skill-promotion workflow (/promote-to-skill command)"

---

## GRAFTING PLAN FOR v5.0.1

**Inherited (no code change)**:
- CSO enforcement → document in CLAUDE.md
- Task granularity → reinforce BUILD_GUIDE
- Tool-failure detection → document bypass CLAUDE.md

**New Code**:
- /promote-to-skill command handler (~200 LOC, Block D)
- state/skill-proposals/ directory scaffold

**Documentation**:
- CLAUDE.md: add Conventions section (~50 LOC)
- BUILD_GUIDE.md: task granularity guideline (~10 LOC)
- PORT_LOG.md: add 4-5 new rows (~30 LOC)

**Testing**:
- test_skill_promotion_workflow.py: agent proposes skill → assert file written (~40 LOC)

---

## FILES TO CREATE/MODIFY

| File | Change | Lines | Block |
|------|--------|-------|-------|
| agent/sagemaker_agent.py | /promote-to-skill handler | ~200 | D |
| agent/CLAUDE.md | Conventions section | ~50 | K |
| agent/BUILD_GUIDE.md | Granularity guideline | ~10 | K |
| state/skill-proposals/.gitkeep | Directory scaffold | 0 | K |
| _phase_2/wave_5/PORT_LOG.md | New rows | ~30 | K |
| tests/test_skill_promotion_workflow.py | Lock test | ~40 | Q |

---

## FINAL VERDICT

Adopt 4 active patterns for v5.0.1:
1. CSO description enforcement (inherited hook)
2. Task granularity enforcement (inherited hook)
3. Tool-failure loop detection (inherited hook, optional)
4. Skill-promotion workflow (new command)

Defer session-end cleanup to v5.0.2 (not blocking).

**Cost**: Minimal. **Risk**: Negligible (LF proven across 20+ repos). **Recommendation**: ADOPT.

---

## 16 OUT-OF-SCOPE ITEMS (explicitly documented)

Anti-simulation hook, HTML Playwright check, Quality report generation, Remote agent doctrine, MCP framework, Voice/IDE/keybindings, Multi-project registry, Nightly /dream, Per-project skill-proposals, Hybrid search (Chroma), Skill TDD, Red Flags tables, CLAIM-CONFIRM queue, Granular chunking, Smoke tests v5.0.1, Soft nightly skills.

All irrelevant to single-user SageMaker + Bedrock-only + no deferrals. All explicitly documented with reasons.

