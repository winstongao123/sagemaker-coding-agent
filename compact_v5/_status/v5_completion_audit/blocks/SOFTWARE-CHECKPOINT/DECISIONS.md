# SOFTWARE-CHECKPOINT Decisions

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Decisions:

- Keep snapshot files in the existing `.snapshots/` directory and add a durable
  `index.json` beside them.
- Store both raw snapshot entries and named checkpoint entries in the index.
- Make `create_checkpoint()` replace an existing checkpoint with the same name
  to keep restore semantics unambiguous.
- Keep direct `SnapshotManager.revert()` as the mutating primitive for internal
  callers, but make slash-command restore/revert preview by default.
- Require `--yes` for `/revert <file>` and `/checkpoint restore <name-or-file>`.

Out of scope:

- Full UI confirmation widgets and rich ask-user UX remain outside this block.
