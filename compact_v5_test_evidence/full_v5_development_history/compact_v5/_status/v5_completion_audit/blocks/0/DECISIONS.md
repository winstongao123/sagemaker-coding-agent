# Block 0 Decisions

Date: 2026-05-05

## D-001: Honor ADR-020 Remap Without Reopening Completed Blocks

Rows 0-2 through 0-10 are Block 0-origin rows, but the canonical source and
ADR-020 explicitly remap them to the owning implementation blocks. This closure
records the rows under Block 0 and cites the already closed owning block
evidence rather than rewriting completed ledgers.

Affected completed blocks cited by this Block 0 closure:

- Block B: 0-3 and 0-8.
- Block B+: 0-7 and 0-9.
- Block C: 0-5 and 0-10.
- Block E+F: 0-2, 0-4, and 0-6.

No code changes were made for Block 0 unless Claude identifies a concrete gap.
