You are Claude Code acting as independent reviewer for SageAgent v5 UI-PARITY-FINAL.

Repo path: D:\Github\sagemaker-coding-agent

Rules:
- Read repo files yourself with read-only tools. Do not rely on this prompt as evidence.
- Do not edit files, do not run git writes, do not run AWS, do not call Codex.
- Review v5 vs v4 carefully: v4 is a reference baseline, not a ceiling. Preserve v5 architecture and improvements unless a v4 behavior is concretely required.
- The goal is v5 > v4 overall, including UI.

Review these changed files:
- compact_v5/MAIN/agent/agent.py
- compact_v5/MAIN/agent/core/query_engine.py
- compact_v5/MAIN/agent/ui/chat_ui.py
- compact_v5/MAIN/agent/tests/integration/test_notebook_smoke.py
- compact_v5/MAIN/agent/chat.md
- compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md
- compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md
- compact_v5/docs/htmls/V5_DESIGN_OVERVIEW.html
- compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
- compact_v5/_status/V5_DESIGN_DECISIONS.md
- compact_v5/_status/PS_TEST_REVIEW_FINAL.md

Also compare with v4 references around:
- compact_v4/MAIN/agent/sagemaker_agent.py create_chat_ui, Compact, Clean, Plan Mode, Auto-Compact, model/session UI behavior.

Facts to verify from files:
- Plan Mode checkbox updates Agent/QueryEngine plan_mode behavior.
- Auto-Compact checkbox gates automatic/cold-cache compaction without removing manual Compact.
- Compact button uses real v5 Compactor path.
- Clean button removes local non-session traces and keeps sessions.
- Sub-agent panel is not dead: preferences reach the dynamic prompt as guidance, without forcing needless subagents.
- Duplicate dead approval/ask-user placeholder boxes are removed; real approval/ask_user runtime paths remain.
- Docs no longer claim final v5 UI is only a minimal MVP.
- Tests meaningfully lock the above.

Return exactly this shape:
VERDICT: APPROVE or APPROVE_WITH_FIXES or REQUEST_CHANGES
SHIP DECISION: UI_READY or NOT_READY
FINDINGS:
- severity file:line finding
TEST_GAPS:
- gap or none
DOC_GAPS:
- gap or none
