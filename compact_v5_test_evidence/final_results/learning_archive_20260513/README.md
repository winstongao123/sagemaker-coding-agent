# Learning Archive - 2026-05-13

Purpose:

This folder gives a clean pickup surface for the recent v5 learning evidence.
It does not move or replace the original evidence files; it indexes and copies
the most relevant recent docs into two folders:

- `v5_build_learnings/`: product/runtime lessons for building and testing v5.
- `software_engineering_learnings/`: broader coding-agent and software
  engineering lessons that should transfer beyond v5.

Original evidence remains in `compact_v5_test_evidence/final_results/` so old
review links and status references keep working.

## Current Readiness Summary

v5 is ready for final SageMaker testing from the current source/zip, with one
honest caveat: final proof still requires the target SageMaker fresh-kernel UI
run. Local tests and package verification pass, and the remaining new scan
items are improvement backlog, not blockers.

Three more deep-scan rounds (rounds 7-9, 2026-05-13) confirmed this: zero new
blockers, 6 new v5 wins, 7 post-final-test backlog items. See
`20260513_runnable_additional_deep_scan.md` (sections "Rounds 7-9").

Current package:
- `compact_v5_ship.zip`
- SHA256: `79d04c5d7162da04f4b1a9a1c20f80b2cc901571b7ea90681c8c48009ad99a6c`
  (refreshed after widget-fix verification 2026-05-13; prior hash was
  `87256ae1ef1cc173896eae9081e58abf31ac542fa96845de8caa3486c696c869`)

Self-review:
- `../20260513_self_review_readiness.md` (rounds 4-6)
- `../20260513_rounds_7_9_self_review.md` (rounds 7-9, this session)

Docs/organization audit:
- `../20260513_docs_org_and_learning_factory_audit.md`

Pickup rule:
- Start with the active docs (`CLAUDE.md`, `AGENTS.md`,
  `compact_v5/AGENT_STATUS.md`, `compact_v5/chat.md`,
  `compact_v5/memory.md`, `compact_v5/docs/V5_KNOWLEDGE_INDEX.md`), then use
  this archive for supporting evidence. Do not treat older raw evidence trees
  as active instructions unless a current doc points to the specific file.
