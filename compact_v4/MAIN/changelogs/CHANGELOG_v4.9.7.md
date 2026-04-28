# CHANGELOG - V4.9.7 (2026-04-28)

## Summary

V4.9.7 is a focused follow-up to the deep `compact_v4` vs `gg_claude_code/gg-claude-code-runnable` review.

Runnable has a richer context-analysis surface. For this SageMaker self-use agent, the useful part is not the full remote/plugin stack; it is the ability to see what is consuming context during a long run. V4.9.7 adds that as a local-only `/context` diagnostic.

## What Changed

### 1. `/context` Slash Command

Added a notebook chat command:

```text
/context
```

It reports:

- total message count
- current context percentage and level
- message body token estimate
- fixed overhead estimate for system prompt, tool schemas, and Bedrock wrapper
- top tool request token sources
- top tool result token sources
- duplicate full-file reads
- a suggested next action

Suggested actions are intentionally practical:

- compact if context is already high
- switch to `grep` or offset-based reads if duplicate file reads dominate
- narrow tool output if a large command result dominates
- otherwise continue and keep `AGENT_STATUS.md` current

### 2. Context Analyzer Helper

Added `analyze_context_messages()` and `format_context_report()` so the diagnostic is testable outside the UI.

The analyzer is approximate and local-only. It uses existing token estimation and scans message blocks for:

- user/assistant text
- tool requests
- tool results
- repeated `read_file` results for the same path

This is deliberately smaller than runnable's full context-analysis subsystem because the deployment target is a single-file SageMaker notebook agent.

### 3. Regression Test

Added `test_context_report_surfaces_tool_bloat_and_duplicate_reads()` to ensure the report catches:

- repeated reads of the same file
- large bash/tool-result sources
- the `/context` report sections users rely on during long-running tasks

## Files Changed

| File | Change |
|---|---|
| `MAIN/agent/sagemaker_agent.py` | Version bump to `4.9.7`; added context analyzer helpers; added `/context` UI command. |
| `MAIN/tests/test_v42_gap_closure.py` | Added regression coverage for duplicate-read and tool-bloat context reporting. |
| `MAIN/agent/USER_GUIDE.md` | Documents `/context` and the long-run diagnostic workflow. |
| `MAIN/agent/chat.md` | Companion docs updated to V4.9.7. |
| `MAIN/agent/chat.ipynb` | Notebook title and quick command list updated. |
| `docs/PRODUCTION_READINESS_STATUS.md` | Status updated to V4.9.7 with `/context` as a fixed context-visibility gap. |
| `CHANGELOG.md` | Added V4.9.7 top-level entry. |
| `compact_v4.zip` | Rebuilt after verification with 22 files / 225.4 KB and flat runtime root layout. |

## Verification

Targeted deterministic coverage after this patch:

- `py_compile` on changed Python files: **PASS**
- `chat.ipynb` JSON validation: **PASS**
- Full targeted deterministic suite: **106/106 PASS**
- Zip rebuild: **PASS**, 22 files / 225.4 KB, no `MAIN/agent/` wrapper prefix

Still required before a production-grade claim:

1. Clean legacy/live Bedrock test harnesses.
2. Run a real SageMaker notebook smoke test with Bedrock.
3. Perform a final security pass on command execution, workspace boundaries, and prompt-injection surfaces.
