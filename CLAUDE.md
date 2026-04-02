# SageMaker Coding Agent

## Current: V4.3.2 (2026-04-02)

AI coding agent for SageMaker/Jupyter. 25+ tools, 16 security layers, 6 sub-agent types, prompt caching, 4-type memory. Learned from Claude Code (Runnable) source code analysis.

## Quick Start
- **Ship to company**: `compact_v4/compact_v4.zip` (60 files, via Teams)
- **Learn architecture**: Open both HTMLs in `PS_ClaudeCode_Insights/Web_doc/` side by side

## Folder Structure

```
compact_v4/                    ★ CURRENT — V4.3.2 agent (ship this)
├── MAIN/agent/
│   ├── sagemaker_agent.py     Core agent (~8,500 lines)
│   ├── chat.md                Companion doc (md version of ipynb)
│   ├── USER_GUIDE.md          Full user documentation
│   ├── TEST_LOG.md            34 Bedrock tests (all PASS)
│   ├── memory.md              Persistent memory template
│   └── skills/                6 skills (clara, review, verify, etc.)
├── CHANGELOG.md               v4.0.0 through v4.3.2
└── compact_v4.zip             Ship-ready (60 files, 3.1MB)

PS_ClaudeCode_Insights/        ★ LEARNING — Runnable Claude Code analysis
├── PS_[01]_DEEP_ANALYSIS_V2.md    Codebase audit #1 (10 features)
├── PS_[02]_DEEP_ANALYSIS_V3.md    Codebase audit #2 (6 features)
├── PS_[03]_PROMPT_ANALYSIS.md     All 24 Runnable prompts tracked
├── PS_[03a]_PROMPT_COMPARISON.md  Side-by-side prompt comparison
├── PS_[04]_LEARNING_JOURNEY.md    Full implementation narrative
├── PS_[05]_VS_OPENCLAW.md         OpenClaw comparison
└── Web_doc/
    ├── PS_FLOWCHART_RUNNABLE.html ★ Open this (Runnable architecture)
    ├── PS_FLOWCHART_V4.html       ★ Open this (V4 architecture)
    └── PS_WEBDOC_LEARNINGS.md     PDF 1-7 cross-reference

Documentations/                MASTER_CHECKLIST.md (completion tracking)
SESSION_STATE.md               Handover doc for next agent session
_archive/                      Old versions (V1-V3), working files, temp
```

## Git Rules
- Push to `sageagent` remote ONLY (`https://github.com/winstonpgao/sageagent.git`)
- After code changes: update CHANGELOG, chat.md, rebuild zip, push
- Skills canonical source: `compact_v4/MAIN/agent/skills/`

## V4.3.2 Highlights
- 35 features learned from Runnable Claude Code + 9 V4-original
- 16 security layers (bash allowlist, Python AST, AWS bedrock-only, etc.)
- 6 sub-agent types: explore, verify, plan, review, general, build
- Prompt caching active on Haiku (pushed past 4,096-token threshold)
- WHEN-not-WHAT tool descriptions (reduces wasted tool calls)
- Cache-breakage detection after compact
- 34 Bedrock tests pass, Codex reviewed 10/10
