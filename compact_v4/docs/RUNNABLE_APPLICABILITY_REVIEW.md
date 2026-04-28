# Runnable Applicability Review For compact_v4

**Date:** 2026-04-28 (originally written against V4.9.7; updated through V4.10.4)
**Reviewed against:** `D:\Github\gg_claude_code\gg-claude-code-runnable`
**Target:** compact_v4 V4.10.4, self-use SageMaker Bedrock coding agent
**Rule for V4 changes:** review first, alter runtime only when the feature clearly improves SageMaker self-use without adding GitHub/remote dependency or hidden context bloat.

## Status by V4.10.x

V4.10.0 closed 5 Runnable-parity gaps (notebook_edit, skill listing budget, sub-agent env-details, model-aware context window, reactive compact). V4.10.1 closed a 6th (segment-level Context Collapse) + flipped default model to Sonnet 4.5. V4.10.2 softened the verify-contract (suggest by default, opt-in strict mode). V4.10.3 added ship-gate verifier, cache-boundary regression test, many-skill stress test, clearer permission denials. V4.10.4 closed the largest remaining gap: sub-agents now receive a bounded work-context handoff block (AGENT_STATUS slice + active todos + last 10 changed file paths) on top of the v4.10.0 env-details — they no longer fly blind when the parent forgets to brief them.

**Of the 18 "must learn / apply" items in the production-readiness review: 14 already done in v4.10.2, 4 added in v4.10.3, 1 final largest-gap closed in v4.10.4.** See `docs/V4_10_0_PLAN.md` for the live status table and `CHANGELOG.md` for per-release detail.

## Scope Boundary

V4 is not trying to become runnable's full product stack. V4 should beat runnable for this use case:

- runs inside SageMaker/Jupyter
- uses AWS Bedrock
- works from a local git tree
- does not assume GitHub, `gh`, PR creation, push, pull, fetch, clone, or remote sessions
- keeps skills explicit unless globally and per-skill enabled
- handles long-running coding tasks with durable status and compaction safety

## Applicability Matrix

| Runnable Functionality | Runnable Evidence | Applicable To V4? | V4.9.7 Status | Decision |
|---|---|---:|---|---|
| System prompt sections and cache boundary | `src/constants/prompts.ts`, `src/constants/systemPromptSections.ts` | Yes | V4 has static/dynamic prompt boundary and Bedrock prompt cache | Keep; improve only with measured cache wins |
| Strong task/todo prompt | `src/tools/TodoWriteTool/prompt.ts`, `src/utils/tasks.ts` | Yes | V4 has `todo_write`, persisted todos, checkpoints, post-compact restoration | Keep; possible next improvement is stronger status linkage |
| Context analysis | `src/utils/contextAnalysis.ts` | Yes | V4.9.7 added `/context` diagnostic | Adopted |
| Read/search collapse | `src/utils/collapseReadSearch.ts` | Partly | V4 has file dedup, unchanged-read stub, tool-result caps, microcompact | Defer deeper UI collapse; current need is token safety, not terminal UI polish |
| Automatic compaction and retry | changelog + context utilities | Yes | V4 has Bedrock-safe compact, prompt-too-long retry, pre-prune, aux model option | Keep; strengthen only after live Bedrock smoke |
| ToolSearch/deferred schemas | `src/tools/ToolSearchTool/prompt.ts` | Partly | V4 filters tool schemas by context and plan mode, but does not lazy-load schemas | Defer; useful for huge tool ecosystems, less urgent for V4's 23 tools |
| Skill discovery/search ecosystem | `src/tools/SkillTool/prompt.ts`, `src/services/skillSearch/*` | Partly | V4 intentionally keeps explicit skill activation; auto-trigger default off | Reject auto-loading; maybe adopt bounded skill listing budgets only if skill count grows |
| Background/fork/team agents | `src/tools/AgentTool/*`, `src/utils/teammate.ts`, team memory | Partly | V4 has build/plan/explore/verify/fork agents with shared budget and worktree safety | Defer team/remote; keep focused sub-agents |
| Verification agent | `src/tools/AgentTool/built-in/verificationAgent.ts` | Yes | V4 has `/verify`, `/done`, verify skill, and regression hooks | Keep; next improvement is more automatic verification trigger documentation/tests |
| Worktree lifecycle | `src/utils/worktree.ts` | Yes | V4 build worktrees fixed, dirty/untracked overlay, merge back, cleanup, serialized builds | Adopted for local SageMaker tree |
| Remote sessions | `src/remote/*`, `src/utils/background/remote/*` | No | V4 blocks remote git/GitHub assumptions | Reject for SageMaker runtime |
| GitHub app/token/preconditions | `src/utils/background/remote/preconditions.ts`, GitHub utilities | No | V4 local git only; remote ops blocked | Reject for runtime; publish manually outside SageMaker |
| Permission engine/rules UI | `src/utils/permissions/*`, `src/components/permissions/*` | Partly | V4 has security denylist, approval dialog, config permission rules | Defer richer engine; current policy is simpler and easier to audit |
| Hooks | prompt hooks + hook utilities | Partly | V4 has slash commands/skills; no general hook runner | Defer; hooks add power but also prompt-injection and side-effect risk |
| MCP/plugin marketplace | MCP/plugin files | Partly | V4 MCP is disabled by default; skills are local | Keep opt-in only |
| Memory directory taxonomy | `src/memdir/*` | Yes, lightly | V4 has `memory.md` typed sections and `AGENT_STATUS.md` | Keep simple; avoid large memory directory unless self-use outgrows one file |
| Session resume/UI polish | session/task components | Partly | V4 has Jupyter sessions, autosave, checkpoints | Defer product UI parity; notebook ergonomics matter more |

## Current Fit Verdict

For the stated SageMaker self-use case, V4.9.7 is intentionally narrower than runnable and stronger on the runtime boundary:

- better SageMaker fit
- better Bedrock-only fit
- better local-git-only policy
- safer skill activation policy
- simpler packaging
- less GitHub/remote surface area

Runnable remains stronger as a broad CLI/product platform. Those broad strengths should only be copied into V4 when they improve this notebook runtime without importing unnecessary remote, GitHub, plugin, or context-bloat risk.

## Candidate Improvements Before Any Runtime Change

These are the only runnable-inspired improvements that look worth considering next:

1. **Status/todo linkage:** make it easier to keep `AGENT_STATUS.md` aligned with todos/checkpoints, but avoid hidden noisy auto-writes unless explicitly designed and tested.
2. **Permission explanations:** richer denial messages for bash/security blocks, modeled after runnable's permission explanation flow.
3. **Context report thresholds:** make `/context` produce stricter action when duplicate reads or tool outputs dominate.
4. **Verification trigger clarity:** strengthen tests/docs around when `/verify` or `/done` must run.
5. **Tool schema budget:** if tool count grows beyond 30-40, consider a deferred-tool or tighter schema budget strategy.

## Rejected For V4 Runtime

- GitHub app integration
- `gh` workflows and PR creation
- remote sessions/environments
- automatic skill loading by default
- broad plugin marketplace by default
- team/swarm memory systems
- hook execution by default

These are useful in runnable, but they fight the SageMaker self-use boundary.

## Review Discipline Going Forward

Before altering V4 based on runnable:

1. Identify the exact runnable mechanism and source file.
2. State why it helps SageMaker self-use.
3. State why it does not require GitHub/remote/product-platform assumptions.
4. Patch the smallest V4 surface.
5. Add a regression test.
6. Update `AGENT_STATUS.md`, `PRODUCTION_READINESS_STATUS.md`, and changelog/status docs.
7. Rebuild `compact_v4.zip` only after verification.
