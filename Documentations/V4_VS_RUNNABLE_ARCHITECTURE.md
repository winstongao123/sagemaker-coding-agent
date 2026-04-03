# V4 vs Runnable — Architecture Deep Comparison

**Date**: 2026-04-02
**Scope**: Dynamic prompts, sub-agents, verification, tool authorization, monitoring

---

## 1. Dynamic System Prompt

| Aspect | V4 | Runnable |
|--------|-----|----------|
| **Base prompt** | Static string (`SYSTEM_PROMPT`) | Section-based assembly (500+ lines) |
| **Dynamic additions** | Append memory + skills + CLAUDE.md | Conditional sections included/excluded |
| **Cache boundary** | `# === DYNAMIC ===` | `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` |
| **Conditional sections** | No — always sends full prompt | Yes — IDE, agent, MCP sections added only when relevant |
| **Winner** | | **Runnable** (more efficient, context-aware) |

**V4 gap**: System prompt is static base + append. Runnable builds prompts from sections and only includes what's relevant (e.g., no IDE instructions outside IDE, no MCP instructions without MCP servers). V4 sends everything every turn.

**For SageMaker scope**: Not a problem. V4's prompt is ~3,650 tokens — small relative to 200K context. Conditional exclusion would save ~500 tokens/turn, which is noise. The gap matters at scale (thousands of users, cost optimization) but not for single-user Jupyter.

---

## 2. Sub-Agent Roles

### V4 (6 types)

| Type | Tools | Turns | Prompt Suffix | Unique Feature |
|------|-------|-------|---------------|----------------|
| build | All 25+ | 25 | "Complete fully, don't gold-plate" | Full execution |
| plan | 11 (read-only) | 15 | Read-only enforced | Architecture analysis |
| explore | 5 (search) | 10 | "Fast search, absolute paths" | Quick codebase navigation |
| verify | 7 | 15 | **"Try to BREAK it"** | Adversarial testing |
| review | 6 | 10 | Security/quality checklist | Code review |
| general | 16 | 15 | "Don't leave half-done" | Multi-step tasks |

**V4 unique**: Adversarial verify agent, structured output (Scope/Result/Key files/Issues).

### Runnable (5 types)

| Type | Tools | Unique Feature |
|------|-------|----------------|
| general | All | Default task executor |
| plan | Read-only | Planning/decomposition |
| explore | Search | Code navigation |
| verify | Testing | Validation (non-adversarial) |
| guide | Self-docs | Claude Code help |

**Runnable unique**: Git worktree isolation (agents work on isolated repo copy), remote agents.

### Verdict
**Tie** — different strengths. V4 has adversarial verify + structured output. Runnable has worktree isolation + remote agents. For SageMaker (single user, no parallel agents), V4's verify is more useful.

---

## 3. Verification Mechanism

### V4 Verification Stack

1. **Verify sub-agent**: Adversarial — prompt says "try to BREAK it." Returns PASS/FAIL/PARTIAL.
2. **Verify skill** (`/verify`): 6-phase shell-based checks:
   - Phase 1: Build (pip/npm)
   - Phase 2: Type check (mypy/tsc)
   - Phase 3: Lint (ruff/eslint)
   - Phase 4: Tests (pytest/npm test)
   - Phase 5: Security (grep for secrets)
   - Phase 6: Diff (git diff review)
3. **Diminishing returns**: Warns if 3+ turns produce <500 output tokens.
4. **Pre-edit staleness**: Aborts edit if file changed since last read.
5. **Doom-loop detection**: Warns on identical repeated tool calls.

### Runnable Verification
- `stop_reason: end_turn` = LLM decides it's done
- No adversarial testing
- No quality scoring
- No automated verification workflow

### What Neither Has
- Auto-run tests after every code edit
- Quality gate blocking completion until tests pass
- Diff review before declaring done
- Automated test → fix → retest loop

### Verdict
**V4 better** — verify agent + verify skill + multiple detection mechanisms. Runnable trusts the LLM to self-judge. V4 provides tools to CHECK after the LLM claims completion.

---

## 4. Tool Authorization & Performance Monitoring

### Authorization

| Feature | V4 | Runnable |
|---------|-----|----------|
| Per-tool approval | Yes (Approve/Always/Deny dialog) | Yes (allow/deny/ask rules) |
| Session memory | "Always allow" set | Persistent rules |
| Plan mode restriction | Yes (read-only tools) | Yes (permission modes) |
| Glob pattern rules | No | Yes (`*.py` → allow bash) |
| Hooks (pre/post tool) | No | Yes (event-action system) |
| Security validation | 16 layers (AST, bash, AWS, path) | Permission rules |
| **Winner** | | **Runnable** (more granular rules) |

### Monitoring

| Feature | V4 | Runnable |
|---------|-----|----------|
| Token tracking | Per-turn, per-session | Per-session |
| Cost display | Real-time ($, cache savings) | Telemetry (not user-facing) |
| Audit log | Every tool call + integrity hash | Analytics events |
| OpenTelemetry | No | Yes (full pipeline) |
| External export | No | OTLP/Datadog/Prometheus |
| Feature flags | No | GrowthBook |
| Per-tool timing | No | Yes |
| **Winner** | | **Runnable** (enterprise monitoring) |

### For SageMaker Scope
**V4 is sufficient.** You're a single user in a notebook — you don't need OTEL pipelines, Datadog dashboards, or glob-pattern permission rules. V4's approval dialog + cost display + audit log covers your needs. Runnable's monitoring is for teams running Claude Code at scale with CI/CD integrations.

---

## 5. Diminishing Returns — Known Issue

The warning `"3 consecutive turns with <500 output tokens"` fires too aggressively during normal multi-tool workflows. When the agent calls read_file → grep → glob, each turn produces short output (tool results, not prose). The agent is working correctly — it's just doing tool calls before giving the final answer.

**Root cause**: The threshold counts ALL turns, including tool-call turns that naturally produce short output.

**Fix needed**: Only count turns where the agent produced NO tool calls. If the agent called a tool, it's working, not stuck. The warning should only fire when the agent produces 3+ turns of short TEXT with no tool calls.

**Status**: Known, documented, not yet fixed. See fix recommendation in this file.

---

*Document generated from independent codebase analysis, 2026-04-02.*
