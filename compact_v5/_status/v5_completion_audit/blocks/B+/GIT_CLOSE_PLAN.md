# Block B+ Git Close Plan

Status: READY_FOR_SPECIFIC_FILE_CHECKPOINT

Specific-file commit is ready after final scope/doc consistency checks.

Before close commit:

1. Rerun `scope_audit.py --block B+`.
2. Run self-reflection checklist.
3. Confirm Claude iter7 row-by-row review remains usable for B+1 through B+8.
4. Confirm INFO-only Claude findings are reflected in artifacts.
5. Update `LEDGER.md`, `REVIEWER_VERDICT.md`, `STATUS.md`,
   `CLAUDE_REVIEW_MATRIX.md`, and this file with the actual review and
   checkpoint evidence.
6. Stage only the B+ file list plus directly touched code/test/doc artifacts.
7. Commit and push to `sageagent` branch `v5-build`; do not tag.
