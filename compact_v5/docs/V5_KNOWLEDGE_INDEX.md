# v5 Knowledge Index

Last updated: 2026-05-14

This is the short pickup map for future v5 work. It separates active truth from
historical evidence so agents do not drift into old paths.

## Active v5 Truth

- `compact_v5/AGENT_STATUS.md` - current status, recent fixes, readiness, and
  target SageMaker caveats.
- `compact_v5/chat.md` - shipped notebook guide, troubleshooting, workspace
  evidence layout, and package policy.
- `compact_v5/memory.md` - compact durable lessons that should be loaded into
  future v5 sessions.
- `compact_v5/docs/V5_NEXT_BACKLOG.md` - **forward-looking** block catalogue.
  Every Runnable + Hermes adoption item lives here with priority, effort,
  source file:line refs, and "where it lands in v5". Single source of truth
  for "what's next for v5". Replaces the historical-only V5_PLAN.md.
- `compact_v5_ship.zip` - current company runtime package.

## Curated Learning Archive

- `compact_v5_test_evidence/final_results/learning_archive_20260513/README.md`
- `compact_v5_test_evidence/final_results/learning_archive_20260513/v5_build_learnings/`
- `compact_v5_test_evidence/final_results/learning_archive_20260513/software_engineering_learnings/`

This archive is the clean reading surface. Raw evidence stays in its original
locations to preserve old review/status links.

## Latest Organization And Drift Audit

- `compact_v5_test_evidence/final_results/20260513_docs_org_and_learning_factory_audit.md`

Main conclusion: durable learning settings help, but they do not prevent drift
when the active bootstrap file is stale, evidence is scattered, or the important
rules are only written in prose. Critical v5 behavior should be encoded in
runtime defaults, tests, package verification, and short current docs.

## Historical References

- `compact_v4/` - latest v4 notebook/reference baseline.
- `PS_ClaudeCode_Insights/` - earlier Runnable Claude Code architecture scans.
- `compact_v5_test_evidence/` - raw v5 development/test/review evidence.
- `D:\Github\gg_claude_code\gg-claude-code-runnable` - local Runnable Claude
  Code reference used for the 2026-05-12 and 2026-05-13 v5 scans.
- `D:\Github\Learning_Factory` - Learning Factory reference system.

Historical references are not active instructions unless a current status or
index file names the specific lesson to apply.

## Package Note

The ship zip currently excludes `docs/`, including this index. The runtime zip
does include root `chat.md`, `AGENT_STATUS.md`, and `memory.md`, so shipped
users still receive the essential guide/status/memory files without the full
development archive.

