# SOFTWARE-CHECKPOINT Changelog

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Changed:

- Added durable `.snapshots/index.json` persistence and reload.
- Added named checkpoint records and restore helpers.
- Updated `/checkpoint` create/list/restore to use the durable named index.
- Updated `/revert <file>` and `/checkpoint restore` to preview unless `--yes`
  is supplied.
- Added zero-cost SOFTWARE-CHECKPOINT tests.
- Claude review iter1 approved all rows with 0 blockers.
