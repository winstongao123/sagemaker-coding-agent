# File & Folder Relationships

> Quick reference: what is what, where things live, and how they connect.

---

## Codebases

| Name | Path | What it is |
|------|------|-----------|
| **Runnable Claude Code** | Was in `gg-claude-code-runnable/` | Source code of Claude Code (TypeScript, 1,438 files). Reference only — we learn from it. |
| **V4 (SageMaker Agent)** | `compact_v4/MAIN/agent/sagemaker_agent.py` | Our coding agent. Single Python file, ~8,500 lines. Ships to company. |
| **how-claude-code-works** | `https://github.com/Windy3f3f3f/how-claude-code-works` | Forked analysis repo of Runnable. Not yet cloned locally. |

## Analysis & Learning Docs

| Path | What it is |
|------|-----------|
| `PS_ClaudeCode_Insights/` | ALL analysis of Runnable Claude Code lives here |
| `PS_ClaudeCode_Insights/PS_DEEP_ANALYSIS_V2.md` | V2 audit — 10 features extracted |
| `PS_ClaudeCode_Insights/PS_DEEP_ANALYSIS_V3.md` | V3 audit — 6 features extracted |
| `PS_ClaudeCode_Insights/PS_PROMPT_COMPARISON.md` | Side-by-side: ALL Runnable prompts vs V4 prompts |
| `PS_ClaudeCode_Insights/PS_LEARNING_JOURNEY.md` | What was learned, implemented, skipped, and why |
| `PS_ClaudeCode_Insights/PS_WEBDOC_LEARNINGS.md` | PDF 1-7 claim verification (IN PROGRESS) |
| `PS_ClaudeCode_Insights/Web_doc/` | PDFs 1-7 + HTML reports (Task B) |
| `PS_ClaudeCode_Insights/TASK_B_HANDOVER.md` | Detailed spec for building the two HTMLs |

## V4 Ship Package

| Path | What it is |
|------|-----------|
| `compact_v4/compact_v4.zip` | **THE zip to ship** — 21 files, 189KB |
| `compact_v4/MAIN/agent/sagemaker_agent.py` | Core agent V4.3.1 |
| `compact_v4/MAIN/agent/chat.ipynb` | Jupyter UI + docs (must stay in sync) |
| `compact_v4/MAIN/agent/chat.md` | Markdown mirror of chat.ipynb (must stay in sync) |
| `compact_v4/MAIN/agent/USER_GUIDE.md` | Full user guide |
| `compact_v4/MAIN/agent/TEST_LOG.md` | All test results |
| `compact_v4/CHANGELOG.md` | Version history |
| `compact_v4/MAIN/agent/skills/` | All skills (review, verify, coding-standards, report, clara) |

## Clara Review

| Path | What it is | Status |
|------|-----------|--------|
| `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\` | **Source of truth** for Clara prompts | CURRENT |
| `D:\Github\planning_bot\` | Git backup of Clara prompts | SYNCED (2026-04-02) |
| `compact_v4/MAIN/agent/skills/clara/` | V4 skill (methodology + orchestration) | DONE |
| `compact_v4/MAIN/agent/skills/clara/prompts/` | Clara prompt files in V4 zip | DONE (self-contained) |

**Relationship**: OneDrive = source → synced to planning_bot (git) → copied into V4 zip (self-contained package)

## Sync Rules

When V4 code changes:
1. Update `sagemaker_agent.py`
2. Update `chat.ipynb` (cell-0 version, cell-4 docs)
3. Update `chat.md` (mirror of ipynb)
4. Update `CHANGELOG.md`
5. Rebuild `compact_v4.zip`
6. Push to `sageagent`

When Clara prompts change:
1. Update in OneDrive (source of truth)
2. Sync to `planning_bot` and push
3. Copy to `compact_v4/MAIN/agent/skills/clara/prompts/`
4. Rebuild zip and push

## Git Remotes

| Repo | Remote | URL |
|------|--------|-----|
| sagemaker-coding-agent | `sageagent` | `https://github.com/winstonpgao/sageagent.git` |
| sagemaker-coding-agent | `origin` | (DO NOT push here) |
| planning_bot | `origin` | `https://github.com/winstonpgao/planning_bot.git` |
