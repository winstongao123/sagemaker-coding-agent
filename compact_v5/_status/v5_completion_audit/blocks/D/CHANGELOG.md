# Block D Changelog

Date: 2026-05-05

Implemented the Wave-5-DEEP D-1 through D-13 row split:

- Added `runtime/slash_args.py` for MCP-suffix slash parsing and custom
  argument substitution.
- Added `/quit` and `/q`, plus helpful unknown-command output with the canonical
  command list.
- Extended `SkillManager` with parallel SKILL.md scan, first-wins dynamic skill
  dedupe, source labels, named cache invalidation, and source-filtered budgeted
  listings.
- Added bundled user-invoked prompt skills for `init`, `init-verifiers`, and
  `skillify`.
- Updated PORT_LOG rows #181-#193, ADR-052, and `compact_v5/CHANGELOG.md`.

Reviewer state: pending first compliant Claude review for Block D.
