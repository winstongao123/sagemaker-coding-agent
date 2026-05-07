# compact_v5 Docs

Start here if you do not want to inspect source code directly:

- `htmls/V5_DESIGN_OVERVIEW.html` - visual, simple current-snapshot v5 architecture and production-readiness map.
- `PS_TEST_REVIEW_FINAL.md` - final evidence summary: what was tested, fixed, reviewed, skipped, and approved.
- `PS_PS_FINAL_TEST.md` - hands-on long-running software engineering acceptance test for you to run in SageMaker.
- `PS_V5_TEST_PLAYBOOK.md` - how the AWS/R-tier test loop proves production readiness.
- `PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` - what changed from v4.
- `PS_V5_LEARNINGS_FROM_REPOS.md` - lessons from Runnable, Hermes, Learning Factory, and v4.
- `V5_PLAN.md` - original build plan.

Current final state as of 2026-05-06:

- Final Claude post-AWS review approved production readiness.
- R-tier matrix is complete: 28 `READY` rows and 14 `DISPOSITION_OK` rows.
- Final R-tier gate passes.
- Total local R-tier Bedrock spend recorded in the ledger is `$1.6757`.

The HTML overview is explanatory only. The source of truth is still the code,
audit ledgers, review artifacts, metrics, and git commits.
