# Block H Baseline

Date: 2026-05-05

Canonical scope is `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:260-285`.

Initial audit before Block H close work:

- Expected rows: 20
- Ledger rows: 0
- Ship-blocking rows: H-1 through H-20
- Verdict: `LEDGER_INCOMPLETE`

Existing code before this completion pass already covered H-1 through H-4,
H-6, H-7, H-9, H-11, H-12, and H-14. The stale historical evidence recorded
H-5, H-8, H-10, H-13, H-15, H-16, H-17, H-18, H-19, and H-20 as deferrals.

Completion pass target:

- Keep existing extraction/session-memory/API-invariant helpers.
- Implement the missing scoped-permission, wait/drain, single-file permission,
  compact-config, truncation, empty/template, env override, user context,
  system context, and onboarding rows.
- Replace deferral evidence with shipped row evidence.
