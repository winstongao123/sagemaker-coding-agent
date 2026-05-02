# Agent 2B Report: Runnable → v5 Feature Gap Analysis

**Investigation Date**: 2026-04-30  
**Scope**: Single-user SageMaker .ipynb context  
**Goal**: Identify Runnable features v5 should adopt to exceed Runnable parity

---

## 1. Runnable Subsystem Inventory

Runnable (gg-claude-code-runnable/src/) is a 94-command TypeScript agent with:
- **Services** (24): AgentSummary, MagicDocs, SessionMemory, autoDream, awaySummary, compact, contextCollapse, diagnosticTracking, extractMemories, mcp, skillSearch, tips, tokenEstimation, toolUseSummary, vcr, voice
- **Commands**: cost, compact, context, debug-tool-call, clear, config, diff, doctor, etc.
- **Hooks** (80+): useCanUseTool, useTypeahead, useVoice, useVirtualScroll, useTextInput, useReplBridge, etc.
- **Architecture**: TypeScript React + Node CLI, prompt-cache sharing, forked-agent pattern

---

## 2. TRUE NON-APPLICABLE (DROP)

These features have zero value in SageMaker .ipynb:

| Subsystem | Reason |
|-----------|--------|
| voice.ts, voiceStreamSTT.ts | Jupyter notebooks do not capture audio |
| useVoice.ts (80KB) | Same |
| useVimInput.ts | CLI keybindings do not apply to notebooks |
| useGlobalKeybindings.tsx (30KB) | Desktop/web only |
| oauth/ | No multi-user auth in SageMaker Dev Mode |
| policyLimits/ | Team-level policy enforcement |
| remoteManagedSettings/ | Remote policy sync |
| teamMemorySync/ | Team shared memory |
| coordinator/ | Multi-agent task coordination |
| bridge/, buddy/ | Desktop app / IDE bridge |
| ssh/ commands | Remote shell (outside SageMaker scope) |

**Justification**: SageMaker notebooks run single kernel, single user. These target desktop/web/team.

---

## 3. GREY ZONE (OPTIONAL)

| Subsystem | Purpose | Priority |
|-----------|---------|----------|
| PromptSuggestion/ | LLM prompt completions | Low |
| tips/ | Usage tips | Very Low |
| MagicDocs/ | AI docs search | Low |
| plugins/ | Plugin registry | Medium-Low |
| outputStyles/ | Custom output rendering | Medium |

---

## 4. SHOULD ADOPT - Ordered by User Value per LOC

### Priority 1: Command System (agent/commands/)

**Runnable has**: 94 slash commands (/cost, /compact, /clear, /context, etc.)  
**v5 has**: No command infrastructure  
**Why**: Cost visibility (/cost), user-driven compaction (/compact [custom]), session control (/clear)  
**Effort**: 200 LOC  
**ROI**: ★★★★★ - Black-box to white-box observability  
**v5.0.1**: Create agent/commands/registry.py with 5 core handlers

### Priority 2: Diagnostic Tracking (agent/observability/diagnostic_tracker.py)

**Runnable has**: LSP diagnostic baseline tracking (file error/warning deltas)  
**v5 has**: None  
**Why**: Catches regressions before user notices; language-agnostic (Pyright, Pylint, mypy)  
**Effort**: 150 LOC  
**ROI**: ★★★★ - Early detection of side effects  
**v5.0.1**: Singleton service; integrate into query_engine.py post-iteration

### Priority 3: Token Estimation & Cost (agent/core/token_counter.py)

**Runnable has**: Fine-grained token counting with cache awareness  
**v5 has**: IterationBudget only  
**Why**: Real API costs; Anthropic counts cache/input/output separately; warnings on expensive ops  
**Effort**: 400 LOC  
**ROI**: ★★★★★ - Cost per turn; users avoid surprise bills  
**v5.0.1**: API: count_tokens(), estimate_cost(); wire into query loop + /cost command

### Priority 4: Memory Extraction (agent/subagent/extract_learnings.py)

**Runnable has**: Auto-extract learnings via forked agent (post-turn)  
**v5 has**: --extract-memory flag but no implementation  
**Why**: Incremental learning corpus; prevents re-explanation in future sessions  
**Effort**: 300 LOC  
**ROI**: ★★★ - Reduces friction across sessions  
**v5.0.1**: Implement flag; post-query hook calls extract_learnings()

### Priority 5: Context Collapse (agent/core/compaction.py)

**Runnable has**: Multi-strategy compaction (60KB), auto-trigger at 80% context  
**v5 has**: IterationBudget only  
**Why**: Extended session lifespan; group tool calls, collapse old turns  
**Effort**: 600 LOC  
**ROI**: ★★★★ - Sessions run 2-3x longer before OOM  
**v5.0.1**: Auto-trigger at 75% window; integrate into budget check

### Priority 6: Audit Log (agent/observability/audit_log.py)

**Runnable has**: Hooks for pre/post API calls, tool executions, errors  
**v5 has**: Query engine with minimal instrumentation  
**Why**: Debugging becomes deterministic; reproducible failures  
**Effort**: 200 LOC  
**ROI**: ★★★ - Structured JSON log with 7-day rotation  
**v5.0.1**: Emit events in query_engine.py

### Priority 7: Output Styles (agent/ui/output_style.py)

**Runnable has**: User-defined .claude/output-styles/*.md templates  
**v5 has**: Raw print/HTML output  
**Why**: Cleaner notebook output; users control formatting without code changes  
**Effort**: 100 LOC  
**ROI**: ★★ - Notebook readability  
**v5.0.1**: Load markdown templates; apply in final response formatting

### Priority 8: Skill/Tool Search Fuzzy Matcher

**Runnable has**: Fuzzy skill matching + registry  
**v5 has**: Hardcoded tool list  
**Why**: Reduces exact-name failures; extensible without restarts  
**Effort**: 100 LOC  
**ROI**: ★★ - Better discoverability  
**v5.1**: Add fuzzy matcher to agent/skills/manager.py

---

## 5. Summary Table

| Subsystem | Adopt | Effort | ROI | v5.0.1 |
|-----------|-------|--------|-----|--------|
| Commands (/cost, /compact, /clear) | YES | 60 | ★★★★★ | Patch |
| Token Counter + Cost | YES | 300 | ★★★★★ | Patch |
| Diagnostic Tracker | YES | 120 | ★★★★ | Patch |
| Compaction Engine | YES | 500 | ★★★★ | Patch |
| Memory Extraction | YES | 250 | ★★★ | Patch |
| Audit Log | YES | 200 | ★★★ | Minor |
| Output Styles | YES | 100 | ★★ | Minor |
| Skill Search Fuzzy | DEFER | 100 | ★★ | v5.1 |

**Total Effort**: ~1,700 LOC across 7 services.  
**Expected Impact**: v5.0.1 becomes observable (cost), durable (extraction), stable (diagnostics).

---

## Architecture Notes

v5 is Python; Runnable is TypeScript. Port logic, not code.
- Runnable's forkedAgent() + cache -> v5's subagent/ (exists)
- Runnable's hooks -> v5's query_engine.py callbacks (exists)
- Runnable's command registry -> v5's commands/ (needs creation)

Why these help v5 > Runnable:
- Runnable dilutes with 94 commands; v5 adopts only high-ROI ones
- Runnable services are TypeScript/React-coupled; v5 decouples via Python hooks
- Runnable's diagnostics are LSP-only; v5 can extend to Python linters (Pyright)
