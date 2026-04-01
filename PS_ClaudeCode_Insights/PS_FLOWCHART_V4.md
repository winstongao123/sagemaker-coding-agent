# SageMaker Coding Agent V4.2.1

Beginner-friendly architecture map of the real V4 code in `compact_v4/MAIN/agent/sagemaker_agent.py`, plus an apple-to-apple comparison against the Claude Code runnable source.

Updated: 2026-04-01

## Quick Stats

| Metric | Value |
|---|---|
| Tools | 22 |
| Security layers | 5 |
| PTL retry attempts | 3 |
| Read-only parallel workers | 6 |
| Result caps | 50K per tool / 200K per batch |
| Primary runtime | AWS Bedrock |

## 1. Architecture

Simple mental model: V4 is a Bedrock-first coding agent for Jupyter and SageMaker. The loop is still:

`user asks -> model reasons -> tools run -> model continues`

V4 adds extra layers around that loop to make it cheaper, safer, and easier to use in notebook environments.

### Main Turn Lifecycle

1. User sends a message.
2. V4 builds the system prompt and loads memory plus `CLAUDE.md`.
3. V4 checks whether cache is cold or the context window is getting too full.
4. V4 may run microcompact or full compact before the next model call.
5. V4 calls Bedrock Claude.
6. V4 parses text and `tool_use` blocks.
7. Read-only tools are batched and run in parallel.
8. Write or risky tools run serially with approvals.
9. Tool results are appended and the model continues.

### Context and Compaction

- `Microcompact`: trims stale tool output when context grows or when Bedrock cache is cold.
- `Full compact`: produces a summary when the conversation is too large.
- `PTL retry`: if the summary request itself is too large, V4 now drops the oldest part and retries up to 3 times.

Beginner analogy: compaction is like cleaning a desk without throwing away the important pages. Old clutter gets summarized so the agent can keep working.

### Safety Model

- Workspace path validation
- Catastrophic command hard block
- Read-only bash auto-classifier
- Approval gating for risky tools
- Partial-view warning and file staleness protection

## 2. Harness and Coordination

### Runtime harness responsibilities

- system prompt assembly
- memory and `CLAUDE.md` injection
- file-context tracking
- approval and safety gating
- compaction and retry handling
- tool execution orchestration
- sub-agent spawning and result reintegration

### Sub-agent coordination

- V4 supports typed sub-agents such as explore, plan, review, build, and general.
- It enforces a depth limit.
- It can override the model per sub-agent type.
- It can run multiple delegated task calls in parallel.
- It restores parent file-context markers after child runs finish.

Important limitation: V4 still does not match runnable's worktree-style isolation, so shared globals remain a weaker point.

### Memory and context management

| Area | Runnable | V4.2.1 | What matters |
|---|---|---|---|
| Memory structure | Per-file memory items + MEMORY.md index | Single `memory.md` with typed sections | Runnable scales better; V4 is simpler to inspect in notebooks. |
| Memory extraction | Forked sub-agent with full conversation context | Single in-process LLM extraction path | Runnable is richer; V4 is lighter. |
| File context dedup | Unchanged-file stub + in-context discipline | Same practical protection now present | V4 closed the repeated unchanged-read waste path. |
| Compaction | Cached MC + time MC + snip + full compact | Time-aware microcompact + full compact + PTL retry | V4 still lacks snip and server-side cache edits. |
| Post-compact cleanup | Broad cache-sensitive cleanup | Strong cleanup, but message mutation still hurts cache purity | Runnable remains stronger for cache stability. |

## 3. Runnable Comparison

This is the apple-to-apple section: what Claude Code runnable has, what V4 now matches, and what is still intentionally different.

| Feature | Claude Code Runnable | V4.2.1 | Status | Notes |
|---|---|---|---|---|
| Parallel read-only tools | Yes, up to 10 and starts while stream is still arriving | Yes, batches consecutive read-only tools with up to 6 workers | Closed | Remaining difference: runnable also streams tool start while the model is still speaking. |
| `FILE_UNCHANGED_STUB` | Yes | Yes | Closed | Audit verified the stub now wins before the generic in-context dedup hint. |
| PTL retry during compaction | Yes, `truncateHeadForPTLRetry()` | Yes, oldest summary slice dropped and retried up to 3 times | Closed | Simpler than runnable, but the failure mode is now handled. |
| Time-based microcompact | Yes | Yes | Closed | Useful after long idle gaps when Bedrock cache is likely cold. |
| Prompt cache boundary | Yes | Yes | Closed | V4 uses Bedrock-safe cache checkpoints and fallback logic. |
| Snip compaction tier | Yes, feature-flagged | No | Open | Good future middle ground between microcompact and full summary. |
| Server-side `cache_edits` | Yes on Anthropic direct path | No | Open | AWS docs do not document runnable-style server cache deletion on Bedrock. This is an inference from official docs. |
| Streaming tool execution | Yes | No | Open | Less attractive in notebook UX than in a terminal CLI. |
| Immutable message objects | Yes | No | Open | V4 still mutates some message content during microcompact. |
| Per-file memory store | Yes | No | Intentional | V4 keeps a flatter memory model because SageMaker sessions are usually easier to inspect manually. |
| Memory extraction as forked sub-agent | Yes | No | Open | Runnable's memory extraction harness is richer and more context-aware. |
| Prompt cache break diagnostics | Yes | No | Open | V4 falls back correctly, but cannot explain cache misses as deeply. |
| Worktree-isolated sub-agents | Yes | No | Open | Runnable is safer for parallel editing; V4 is simpler for one-user SageMaker sessions. |
| Parallel sub-agent execution | Yes | Yes | Closed | V4 can already run several delegated task calls in parallel. |
| Sub-agent model override | Not emphasized | Yes | V4 edge | V4 can steer sub-agent types toward different Bedrock models more directly. |
| Sub-agent state isolation | Stronger | Partial | Open | Shared globals like `_FILE_READ_TIMES` are still a concurrency risk if many sub-agents overlap. |

## 4. What V4 Does Better

### Bedrock-first resilience

- Prompt-cache fallback is tuned for Bedrock validation behavior.
- Token and cost tracking are local and visible to the SageMaker user.
- Cold-cache detection is practical for notebook sessions with long idle gaps.

### Safer notebook UX

- Hard-block catastrophic command patterns before approval logic.
- Read-only bash auto-classifier avoids noisy approval popups for safe reads.
- Approval reset on compact prevents stale "always allow" decisions from living forever.

### Better business-user output

- Built-in Word, Excel, PDF, chart, notebook, and markdown generation.
- Designed for Jupyter sharing, demoing, and report-style workflows.
- Useful when the user wants deliverables, not only code diffs.

### Practical SageMaker packaging

- Single-file agent is easier to copy into notebooks and managed workspaces.
- Session persistence and audit logs are easier to inspect locally.
- Model override support lets different sub-agent types use different Bedrock models.

## 5. Beginner Guide

### What is the system prompt?

Think of the system prompt as the agent's job description taped to the monitor. It says things like:

- be safe
- stay inside the workspace
- use tools correctly
- format answers clearly

Every turn, the model reads that job description before it decides what to do.

### What is compaction?

Compaction is like cleaning a work desk. If the desk gets too full, the agent summarizes older conversation, keeps the recent pages, and keeps the last important file reads nearby.

### Why is prompt caching important?

If the static part of the prompt is the same on many turns, Bedrock can reuse that repeated prefix instead of charging full price every time.

Beginner analogy: the agent stops photocopying the same instruction manual on every loop.

### Why not copy runnable exactly?

Because the environment is different. Runnable is a CLI product built for Anthropic's own stack and a terminal-first workflow. V4 is optimized for SageMaker, notebooks, Bedrock pricing, and users who often want reports and visible widgets, not only terminal throughput.

### Why are there still some gaps?

Some gaps are worth future work, like snip compaction. Others are not worth the complexity yet in SageMaker, like full streaming tool execution in a notebook UI. And one big item, server-side `cache_edits`, depends on what Bedrock exposes at the API level, not only on local Python code.

## 6. Bedrock and Verification

### Local verification completed

- `python -m py_compile compact_v4/MAIN/agent/sagemaker_agent.py compact_v4/MAIN/tests/test_v42_gap_closure.py`
- `python -m pytest compact_v4/MAIN/tests/test_v42_gap_closure.py -q`
- Result: `3 passed`
- `npx playwright test PS_ClaudeCode_Insights/tests/flowcharts.spec.js --reporter=line`
- Result: `2 passed`

Regression tests cover:

- unchanged-file stub behavior
- prompt-too-long summary retry
- read-only parallel dispatch
- V4 HTML tab switching
- Runnable HTML tab switching and every detail modal in `NODE_DETAILS`

### Live AWS Bedrock check completed

- Date: `2026-04-01`
- V4 default runtime target: `au.anthropic.claude-haiku-4-5-20251001-v1:0`
- Prompt-cache validation target: `au.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Region used by V4 config: `ap-southeast-2`
- Legacy baseline `anthropic.claude-3-haiku-20240307-v1:0`: returned `OK` but rejected `system.0.cache_control`, so fallback was required
- Preferred runtime `au.anthropic.claude-haiku-4-5-20251001-v1:0`: returned `OK` and accepted cache fields
- Prompt-cache verification `au.anthropic.claude-sonnet-4-5-20250929-v1:0`: returned `OK` and showed real cache write on call 1 plus cache read on call 2 with a long static prompt

Practical finding:

- caching is not uniformly available across all Claude model IDs
- legacy Claude 3 Haiku needs fallback
- AU 4.5 inference-profile models are the correct AWS path here

### PDF coverage audit

Honest answer: the HTML now covers the major source-verifiable points the PDFs were strong on, especially:

- query harness
- tool orchestration
- prompt caching
- permission race design
- memory structure
- sub-agent and worktree concepts
- post-compact cleanup concepts

What was corrected against source:

- subscription-tiered parallelism
- Capybara as a separate model tier
- inflated file and line-count claims

What is not claimed from PDFs alone:

- UI-only details
- any point we could not verify in code

### Bedrock prompt caching notes

Practical conclusion: for Bedrock, keep using cache checkpoints and `cache_control`-style prompt boundaries. Do not depend on Anthropic beta headers in the Bedrock path.

Official references:

- AWS Bedrock Prompt Caching: <https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html>
- AWS Supported Models for Prompt Caching: <https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching-supported-models.html>
- Anthropic Prompt Caching Guide: <https://docs.claude.com/en/docs/build-with-claude/prompt-caching>

Inference from official docs: AWS documents prompt caching with checkpoints and supported-model rules, but does not document runnable-style `cache_edits` support on Bedrock. That is why V4 still uses message-level microcompact instead of runnable's server-side cache deletion path.

## 7. Honest Final Answers

| Question | Answer |
|---|---|
| Did V4 learn the high-value runnable lessons? | Yes, for the most important SageMaker-safe items: prompt cache boundary, memory guardrails, approval reset, cold-cache microcompact, file dedup stub, parallel read-only tools, PTL-safe compaction retry, and practical sub-agent coordination. |
| Is V4 fully identical to runnable? | No. Snip compaction, streaming tool execution, immutable message design, memory extraction as a fork, cache-break diagnostics, worktree isolation, and deeper sub-agent isolation are still open or intentionally different. |
| Is this the best AWS-focused version in this repo? | Yes, V4.2.1 is the best AWS-targeted version in this repo right now, especially with Haiku 4.5 as the default runtime and Sonnet 4.5 reserved for cache verification or harder turns. |
| Is caching actually working on AWS? | Yes, but not uniformly across all models. It fails on legacy Claude 3 Haiku, works on the AU 4.5 inference-profile models, and was directly verified with a real cache write then cache read on Sonnet 4.5. |

## 8. Source of Truth

- V4 source: `compact_v4/MAIN/agent/sagemaker_agent.py`
- Runnable comparison source: `compare_code/gg-claude-code-runnable`
