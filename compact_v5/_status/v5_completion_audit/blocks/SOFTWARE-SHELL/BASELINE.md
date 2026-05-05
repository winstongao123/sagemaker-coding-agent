# SOFTWARE-SHELL Baseline

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Canonical source:

- `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` DS3-S16 and DS3-S17.
- `PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md` PS3-8.
- `BLOCK_ORDER_AND_COVERAGE.md` row for `SOFTWARE-SHELL`.

Scope:

- Foreground subprocess timeout/stop must kill the process tree.
- Background shell jobs must support start, poll, wait, kill, durable logs, and
  restart-visible metadata.
- Tests must include no-orphan proof.
