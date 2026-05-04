# Ledger Schema

Every block ledger must use this schema.

## Required Table

| Column | Required | Meaning |
|---|---|---|
| `row_id` | yes | Canonical id from `SYNTHESIS_MASTER`, for example `A-16`. |
| `capability` | yes | Capability text from `SYNTHESIS_MASTER`. |
| `source` | yes | Source repo/file:line from `SYNTHESIS_MASTER`. |
| `priority` | yes | Priority from plan: MUST/HIGH/MED/LOW. |
| `fit` | yes | Fit/adaptation verdict from plan. |
| `expected_target` | yes | Expected v5 target file/module. |
| `code_evidence` | yes | Current production code file:line, or `NONE_FOUND`. |
| `test_evidence` | yes | Test file:line, or `NONE_FOUND`, or `NO_TEST_JUSTIFICATION:<reason>`. |
| `port_log` | yes | PORT_LOG row id, or `NONE_FOUND`. |
| `adr` | yes | ADR id/section, or `NONE_FOUND`. |
| `historical_review` | yes | Review file:line showing row included, or `NOT_INCLUDED_IN_REVIEW`. |
| `git_evidence` | yes | Commit/tag/blame evidence. |
| `disposition` | yes | One of the allowed dispositions below. |
| `action_needed` | yes | Concrete next action. |
| `reviewer_verdict` | later | Filled after independent reviewer. |

## Allowed Dispositions

| Disposition | Ship meaning |
|---|---|
| `SHIPPED` | Can ship if reviewer verifies evidence. |
| `PARTIAL` | Ship-blocking unless explicitly accepted by user. |
| `MISSING` | Ship-blocking unless explicitly dropped/deferred by user. |
| `DEFERRED_USER_APPROVED` | Not ship-blocking only with explicit user approval citation. |
| `DROPPED_USER_APPROVED` | Not ship-blocking only with explicit user approval citation. |
| `N/A_CONSTRAINT` | Not ship-blocking only with hard-constraint citation. |

## Required Summary

Each ledger must end with:

```text
EXPECTED_ROWS:
LEDGER_ROWS:
SHIPPED:
PARTIAL:
MISSING:
DEFERRED_USER_APPROVED:
DROPPED_USER_APPROVED:
N/A_CONSTRAINT:
SHIP_BLOCKING_ROWS:
```

## Reviewer Rejection Rules

Reviewer must reject if:

1. `EXPECTED_ROWS != LEDGER_ROWS`.
2. Any row id from `SYNTHESIS_MASTER` is missing.
3. Any `SHIPPED` row lacks code evidence.
4. Any runtime `SHIPPED` row lacks test evidence and justification.
5. Any defer/drop lacks explicit user approval.
6. Any worker prompt narrows scope.
7. Any block status says DONE while ledger has ship-blocking rows.
