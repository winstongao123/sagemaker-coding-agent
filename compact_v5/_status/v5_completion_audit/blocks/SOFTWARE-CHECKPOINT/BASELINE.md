# SOFTWARE-CHECKPOINT Baseline

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Canonical source:

- `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` DS3-S2 and DS3-S8.
- `PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md` checkpoint continuity requirements.
- `BLOCK_ORDER_AND_COVERAGE.md` row for `SOFTWARE-CHECKPOINT`.

Scope:

- Durable named checkpoint index.
- Restart-safe checkpoint listing.
- Safe preview-before-mutation for single-file revert and checkpoint restore.
- Preserve existing `/revert all --yes` safety behavior.
