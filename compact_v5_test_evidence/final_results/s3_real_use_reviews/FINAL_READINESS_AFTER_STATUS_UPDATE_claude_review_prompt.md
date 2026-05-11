# Independent Claude Review Prompt - Final S3 Readiness After Status Update

You are an independent reviewer. Do not edit files. Inspect the repository and
answer with a clear verdict.

Repository root:
`D:\Github\sagemaker-coding-agent`

Branch:
`v5-build`

Context:
- The compact v5 active ship tree is flat: `compact_v5/`.
- The worker previously implemented S3 real-use fixes in Blocks 0-7 and got
  Claude APPROVE reviews for each block.
- A later review found the runtime fixes were shipped, but some documentation
  still said the S3 punch list was open/not fixed.
- Codex has now updated only status/evidence docs plus the zip verification
  report, and rebuilt `compact_v5.zip` from the existing 158-member manifest.

Please validate:
1. Are the stale "open punch list / not fixed" statements for the S3 P0/P1
   issues removed or corrected in:
   - `compact_v5_test_evidence/FINAL_TEST_SUITE_INDEX.md`
   - `compact_v5_test_evidence/compact_v5/docs/PS_PS_FINAL_TEST_v3_REAL_USE_ISSUES.md`
   - `compact_v5_test_evidence/final_results/S3_REAL_USE_DIAGNOSTIC_CONSOLIDATED_20260511.html`
   - `compact_v5/AGENT_STATUS.md`
2. Does the updated wording preserve the important nuance:
   - P0/P1 S3 validation blockers are shipped/reviewed.
   - P2 or cross-thread items remain deferred, not falsely claimed as complete.
   - target SageMaker validation is still required before calling production 100%.
3. Does `compact_v5.zip` appear rebuilt from the flat `compact_v5/` tree with
   member count 158, no forbidden folders, `testzip=None`, and required-member
   hash parity recorded in:
   `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md`
4. Do the focused tests and compile checks recorded by Codex look sufficient
   for this docs/status/zip follow-up?
   - `py -3.10 -m pytest` six S3/UI smoke tests: 23 passed.
   - `python -m py_compile` production files passed.
5. Is there any remaining HIGH or MEDIUM blocker that should prevent saying:
   - 100% ready for target SageMaker validation
   - 98% production-ready pending final target environment smoke?

Important boundaries:
- Do not require solving deferred P2/cross-thread improvements unless they are
  actually S3 P0/P1 validation blockers.
- Treat unrelated dirty paths as out of scope:
  `_archive/compare_code/gg-claude-code-runnable`, `.sageagent_state/`,
  `_zip_review/`, `memory.md`.

Return:
- VERDICT: APPROVE or REQUEST_CHANGES
- HIGH/MEDIUM findings if any, with file paths and reason
- LOW notes if any
- A short final readiness statement in plain English
