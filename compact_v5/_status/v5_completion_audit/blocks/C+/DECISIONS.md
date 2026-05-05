# Block C+ Decisions

Date: 2026-05-05

## C+1 Drop

`SYNTHESIS_MASTER.md:119` explicitly records `Verdict: DROP (KEEP /phase)` for
formal EnterPlanMode/ExitPlanMode tools. The ledger therefore uses
`DROPPED_USER_APPROVED` and cites `/phase` as the retained lighter-weight v4
equivalent.

## C+2 Snapshot Evidence

C+2 is implemented by the existing SnapshotManager and edit/write tool
pre-mutation snapshot calls. The C+ audit adds explicit row evidence rather
than duplicating the runtime.

## C+3 Abort Evidence

C+3 is marked already covered by C-17 in `SYNTHESIS_MASTER.md:121`. The C+
audit points to the existing C-17 implementation and lock test that verifies
QueryEngine forwards abort events and bash/python_exec consume them before
launch.
