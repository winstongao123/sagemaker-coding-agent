# SOFTWARE-CHECKPOINT Ledger

Status: CLOSED_PUSHED
Date: 2026-05-05

Manual software-builder ledger:

| row_id | gap_id | requirement | implementation | code_evidence | test_evidence | doc_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|
| SOFTWARE-CHECKPOINT-1 | DS3-S2 | Checkpoint index must be durable across restart. | `SnapshotManager` writes `.snapshots/index.json` atomically and reloads snapshots/checkpoints on new manager construction. | `runtime/snapshot.py:54`; `runtime/snapshot.py:75`; `runtime/snapshot.py:139` | `tests/integration/test_software_checkpoint.py::test_snapshot_index_survives_manager_restart` | `blocks/SOFTWARE-CHECKPOINT/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-CHECKPOINT-2 | DS3-S2 | Named checkpoints must be durable and restart-listable. | `/checkpoint create <name>` records named checkpoints, `/checkpoint list` shows named checkpoints after restart. | `runtime/snapshot.py:174`; `runtime/snapshot.py:178`; `commands.py:547`; `commands.py:557` | `tests/integration/test_software_checkpoint.py::test_named_checkpoint_restore_requires_confirm_and_lists_after_restart` | `blocks/SOFTWARE-CHECKPOINT/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-CHECKPOINT-3 | DS3-S8 | Single-file revert must preview before mutation. | `/revert <file>` previews and requires `/revert <file> --yes` before copying snapshot content. | `runtime/snapshot.py:201`; `commands.py:300`; `commands.py:304` | `tests/integration/test_software_checkpoint.py::test_revert_requires_preview_before_single_file_mutation`; Block D regression log | `blocks/SOFTWARE-CHECKPOINT/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-CHECKPOINT-4 | DS3-S8 | Checkpoint restore must preview before mutation. | `/checkpoint restore <name-or-file>` previews and requires `--yes`; named checkpoint restore copies all recorded entries only after confirmation. | `runtime/snapshot.py:232`; `runtime/snapshot.py:248`; `commands.py:576`; `commands.py:583`; `commands.py:585` | `tests/integration/test_software_checkpoint.py::test_named_checkpoint_restore_requires_confirm_and_lists_after_restart` | `blocks/SOFTWARE-CHECKPOINT/DECISIONS.md` | SHIPPED | None. | APPROVED |

Manual ledger summary:

```text
EXPECTED_ROWS: 4
LEDGER_ROWS: 4
SHIPPED: 4
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0
```
