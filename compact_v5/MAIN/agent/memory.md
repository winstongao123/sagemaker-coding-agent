# Persistent Memory (auto-populated)

This file is auto-loaded into the system prompt's dynamic tail. Sections
are managed by the agent's memory-extraction pass (Phase 11+). Keep
edits minimal — the agent will append entries here as it learns.

## User
(no entries yet)

## Feedback
(no entries yet)

## Project
- v5 production zip intentionally excludes v4 Power BI dashboard skills
  (`powerbi-dashboard`, `powerbi-dashboard-v2`). They remain v4/reference
  material, not v5 runtime skills. Do not re-add them to the v5 ship zip unless
  the user explicitly asks for Power BI dashboard generation support.

## Reference
- Clara review support must preserve the full v4 Clara skill pack in v5:
  `SKILL.md`, `FULL_REVIEW.md`, `V4_NOTES.md`, and `prompts/00-05` plus
  `HOW_TO_USE.md`. The user wants to select ClaRA components/phases flexibly
  and add extra review requests.
