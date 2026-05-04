# Block Audit Folders

Create one folder per block using lowercase ids:

```text
blocks/a/
blocks/e-f/
blocks/l/
blocks/n/
blocks/k/
...
```

Each block folder must contain:

| File | Purpose |
|---|---|
| `BASELINE.md` | Start-state commands and outputs. |
| `LEDGER.md` | Row-by-row canonical ledger. |
| `STATUS.md` | Current block status. |
| `PROMPTS.md` | Exact worker/reviewer prompts or links to prompt files. |
| `TESTS.md` | Exact test commands and outcomes. |
| `CHANGELOG.md` | Human-readable changes made during redo. |
| `DECISIONS.md` | Local decisions or ADR links. |
| `WORKER_SELF_REVIEW.md` | Worker final self-review before reviewer. |
| `REVIEWER_VERDICT.md` | Independent reviewer output summary. |
