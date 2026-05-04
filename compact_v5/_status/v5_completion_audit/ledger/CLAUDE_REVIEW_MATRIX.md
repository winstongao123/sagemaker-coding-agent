# Claude Review Matrix

Status: ACTIVE
Created: 2026-05-04
Purpose: cross-block table of Claude reviewer verdicts, row counts, and next actions.

| Block | Iter | Review path | Verdict | Expected rows | Ledger rows | Shipped | Partial | Missing | Blocking rows | Required next action |
|---|---:|---|---|---:|---:|---:|---:|---:|---|---|
| A | 1 | `reviews/block-a-claude-review-iter1.md` | APPROVE ledger audit only | 43 | 43 | 2 | 12 | 29 | 41 | A-16/A-17/A-21/A-25 now implemented locally; continue remaining Block A ship-blocking rows before closure re-review. |
| A | 2 | `reviews/block-a-claude-review-iter2.md` | NO_VERDICT / PLAN_OUTPUT | n/a | n/a | n/a | n/a | n/a | n/a | Counted attempt. Output was a plan/prompt-repair discussion, not a reviewer verdict. |
| A | 3 | `reviews/block-a-claude-review-iter3.md` | NO_VERDICT / HANDOFF_FAILED | n/a | n/a | n/a | n/a | n/a | n/a | Counted attempt. Output reports sandbox/write-strategy failures, not a reviewer verdict. |
| A | 4 | `reviews/block-a-claude-review-iter4.md` | NO_VERDICT / EMPTY_PROMPT | n/a | n/a | n/a | n/a | n/a | n/a | Counted attempt. Claude asked for the missing prompt content. |
| A | 5 | `reviews/block-a-claude-review-iter5.md` | NON_COMPLIANT_REVIEW / MISSING_BASE_AND_SHIP_DECISION | 43 | 43 | 6 | 9 | 28 | 37 | Counted attempt. Review-like output exists, but the prompt did not embed the required base prompt and output lacks `SHIP DECISION:`. |
| A | 6 | `reviews/block-a-claude-review-iter6.md` | NON_COMPLIANT_REVIEW / MISSING_BASE_AND_SHIP_DECISION | 43 | 43 | 6 | 9 | 28 | 37 | Counted attempt. Review-like APPROVE exists, but the prompt did not embed the required base prompt and output lacks `SHIP DECISION:`. Run compliant iter7 before more implementation. |
| A | 7 | `reviews/block-a-claude-review-iter7.md` | APPROVE_WITH_FIXES / SHIP DECISION NOT_DONE | 43 | 43 | 6 | 9 | 28 | 37 | Usable compliant review. A-16/A-17/A-21/A-25 batch approved. Worker has since updated ledger to 43 SHIPPED / 0 blocking pending scope audit and compliant Claude re-review. |
| A | 8 | `reviews/block-a-claude-review-iter8.md` | NO_VERDICT / HANDOFF_FAILED_AUTH_ROUTING | 43 | 43 | 43 | 0 | 0 | 0 pending Claude | Counted handoff attempt. Prompt was compliant and saved, but Claude CLI returned `Credit balance is too low` because the subprocess likely inherited `ANTHROPIC_API_KEY`; no reviewer verdict. |
| A | 9 | `reviews/block-a-claude-review-iter9.md` | NO_VERDICT / HANDOFF_FAILED_AUTH_COMMAND | 43 | 43 | 43 | 0 | 0 | 0 pending Claude | Counted handoff attempt. Auth-routing retry used the saved iter8 prompt and cleared `ANTHROPIC_API_KEY`, but PowerShell split `--setting-sources user,project,local`; no reviewer verdict. Retry with the setting source value quoted as one argument. |
| A | 10 | `reviews/block-a-claude-review-iter10.md` | APPROVE_WITH_FIXES / SHIP DECISION READY_FOR_BLOCK_CLOSE_REVIEW | 43 | 43 | 43 | 0 | 0 | 0 | Usable compliant closure-scope review. Claude verified all 43 rows and found 0 ship-blocking rows. LOW findings: A-22 test thinness, A-30 reset/evidence cleanup, A-37 inert cache_ttl knob. Worker fixed all three locally; rerun scope audit and send fresh Claude re-review. |
| A | 11 | `reviews/block-a-claude-review-iter11.md` | APPROVE / SHIP DECISION READY_FOR_BLOCK_CLOSE_REVIEW | 43 | 43 | 43 | 0 | 0 | 0 | Usable compliant re-review after LOW fixes. Claude verified A-22/A-30/A-37 fixes, found no new findings, and confirmed Block A is ready for user-level close decision. Proceed to self-reflection, final scope audit, close artifacts, then specific-file commit/push per git checkpoint policy. |
