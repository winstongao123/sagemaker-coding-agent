# Claude Reviewer Prompt - Block A Ledger Audit

You are the independent Claude Code reviewer for the v5.0.1 completion redo.

Do not trust the worker's row list. Independently read:

1. `compact_v5/_status/v5_completion_audit/00_MASTER_PROTOCOL.md`
2. `compact_v5/_status/v5_completion_audit/03_LEDGER_SCHEMA.md`
3. `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`
4. `compact_v5/_status/PS_CRITICAL_WORKER_PROBLEM.md`

Then review Block A:

- `compact_v5/_status/v5_completion_audit/blocks/A/BASELINE.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/WORKER_SELF_REVIEW.md`

Required review:

1. Regenerate the expected Block A row list directly from `SYNTHESIS_MASTER.md`.
2. Compare it to `blocks/A/LEDGER.md`.
3. Reject if any canonical row is absent.
4. Reject if any shipped row lacks code evidence, test evidence, PORT_LOG evidence, or ADR evidence.
5. Reject if any non-shipped row is marked non-blocking without explicit user approval.
6. Verify that the prior Codex review prompt was narrowed and therefore does not close full Block A scope.
7. Confirm whether the worker's disposition counts match the ledger.

Return:

- Expected row count.
- Ledger row count.
- Disposition counts.
- Findings, if any.
- Verdict: APPROVE or REJECT.

Do not run Codex CLI. Do not spend AWS/R-tier.
