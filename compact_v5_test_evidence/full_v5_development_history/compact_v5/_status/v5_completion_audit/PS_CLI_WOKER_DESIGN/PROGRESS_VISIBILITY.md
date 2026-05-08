# Progress Visibility Rule

Status: ACTIVE
Created: 2026-05-04

The worker must make progress inspectable from files, not only terminal output.

## Required Heartbeat Cadence

Update `compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/STATUS.md`:

1. Before starting any long implementation or test slice.
2. After completing any meaningful code/test/doc/ledger slice.
3. Before creating a Claude reviewer prompt.
4. Immediately after saving a Claude reviewer prompt.
5. Immediately after Claude reviewer returns or fails.
6. Before stopping, compacting, or handing off.

## Required Fields

Every active block heartbeat must include:

- current phase:
  - `IMPLEMENTING`
  - `TESTING`
  - `UPDATING_ARTIFACTS`
  - `PREPARING_CLAUDE_REVIEW`
  - `WAITING_FOR_CLAUDE`
  - `PROCESSING_CLAUDE_REVIEW`
  - `BLOCKED`
- current task
- last completed action
- next 3 todo items
- next Claude review:
  - not ready yet, with reason
  - prompt path written
  - review running
  - review saved at path
- latest usable Claude verdict
- current blocking-row count
- blocker or human decision needed

## Rule

If an external monitor cannot answer "what is the worker doing, what is next,
and has Claude been called yet?" from `blocks/<BLOCK>/STATUS.md`, the heartbeat
is incomplete and must be updated before more implementation work.
