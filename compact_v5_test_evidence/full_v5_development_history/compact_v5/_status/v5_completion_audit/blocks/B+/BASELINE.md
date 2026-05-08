# Block B+ Baseline

Date: 2026-05-05

## Git Baseline

- `git rev-parse HEAD`: `e0b38fa18275d415327374c882abefddcfb00292`
- Latest `v5.0.1-block-*` tags listed at baseline included
  `v5.0.1-block-k` through `v5.0.1-block-0`; no tag was created.
- `git status --short` showed many pre-existing dirty files outside the B+
  slice, plus the B+ status/log files from the interrupted smoke attempt. These
  were not reverted.

## Scope Baseline

Initial B+ audit before ledger creation:

```text
=== Block B+ ===
Expected rows: 8
Ledger rows: 0
Ship-blocking rows: B+1, B+2, B+3, B+4, B+5, B+6, B+7, B+8
Verdict: LEDGER_INCOMPLETE
```

The first `py -3.11` scope-audit attempt failed in the sandbox because the
Windows Store Python app path could not be launched. The same audit via the
available Python executable and later the escalated Python 3.11 runner confirmed
the mechanical state above.
