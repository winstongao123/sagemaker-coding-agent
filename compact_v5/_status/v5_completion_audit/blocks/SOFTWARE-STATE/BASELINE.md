# SOFTWARE-STATE Baseline

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Canonical source:

- `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` DS3-S1, DS3-S2, DS3-S3, DS3-S11.
- `PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md` PS3-1, PS3-2, PS3-3.
- `BLOCK_ORDER_AND_COVERAGE.md` software-builder table row for `SOFTWARE-STATE`.

Scope reconstructed from disk:

- Durable task/work ledger and todo persistence.
- `/save` and `/resume` preserve messages, token stats, todos, status/memory
  context, and recovery metadata.
- Crash-safe per-turn journal and last-turn recovery record exist locally.
- Top-level turns refresh current `AGENT_STATUS.md` and `memory.md` context.
- Memory extraction has a zero-cost, opt-in `/save` path; no LLM call is made
  unless the runtime explicitly supplies an extractor function.

Out of this block:

- Durable named checkpoint index and restore preview are owned by
  `SOFTWARE-CHECKPOINT`.
- Enforced `/verify` and `/done` gates are owned by `SOFTWARE-GATE`.
- Typed compaction telemetry is owned by `SOFTWARE-COMPACT-TELEMETRY`.
