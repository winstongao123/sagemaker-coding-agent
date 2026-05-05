# Block Order And Coverage Gate

Status: ACTIVE
Created: 2026-05-04

This file prevents confusion between the original build sequence in
`SYNTHESIS_MASTER.md` and the v5.0.1 redo sequence.

## Canonical Scope

The canonical scope is still:

`compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`

Every row parsed by `scope_audit.py --all --summary` must be accounted for
before any AWS/R-tier spend, final ready-for-testing claim, or tag.

Current mechanical totals from the audit script:

```text
TOTAL_EXPECTED_ROWS: 233
```

Blocks A, E+F, L, N, K, T, C, B, B+, C+, D, F2, and I are closed/pushed. Block G
has complete local scope coverage and is waiting for Claude row-by-row closure
review. The remaining audit rows are still ship-blocking until each block is
ledgered, implemented or explicitly user-dispositioned, Claude-reviewed, and
pushed.

Latest current summary:

```text
TOTAL_EXPECTED_ROWS: 233
TOTAL_SHIP_BLOCKING_ROWS: 42
```

Evidence: fresh `scope_audit.py --all --summary` run on 2026-05-05.

## Redo Order

The redo order intentionally starts with Block A because it was the known
critical failure. After A, the worker continues through the remaining blocks in
the active redo order below:

```text
A -> E+F -> L -> N -> K -> T -> C -> B -> B+ -> C+ -> D -> F2 -> I -> G -> G2 -> G3 -> H -> H+ -> M -> J -> 0
```

This order is not the original build order. It is acceptable because every
block is still gated by mechanical coverage and Claude review.

## Original Build Order Reference

The original build order in `SYNTHESIS_MASTER.md:641-665` is:

```text
0 -> B -> B+ -> C -> C+ -> D -> A -> E+F -> F2 -> I -> M -> G -> G3 -> G2 -> H -> H+ -> L -> N -> T -> J -> K
```

Workers may cite this when explaining why E+F follows A in the original plan.

## Known Audit Blocks

The audit script currently knows these 21 blocks:

```text
0, A, B, B+, C, C+, D, E+F, F2, G, G2, G3, H, H+, I, L, M, N, T, J, K
```

Rows currently parsed from `SYNTHESIS_MASTER.md`:

| Block | Expected rows | Notes |
|---|---:|---|
| 0 | 10 | Audit rows exist in scope parser. |
| A | 43 | Closed and pushed. |
| B | 16 | Closed and pushed. |
| B+ | 8 | Closed and pushed. |
| C | 19 | Closed and pushed. |
| C+ | 3 | Closed and pushed. |
| D | 13 | Closed and pushed. |
| E+F | 8 | Closed and pushed. |
| F2 | 1 | Closed and pushed. |
| G | 8 | Local scope clean; pending Claude closure review/push. |
| G2 | 1 | Pending. |
| G3 | 2 | Pending. |
| H | 20 | Pending. |
| H+ | 1 | Pending. |
| I | 13 | Closed and pushed. |
| L | 28 | Closed and pushed. |
| M | 0 | No rows in current parser; still needs closure note/reviewer confirmation if protocol requires. |
| N | 19 | Closed and pushed. |
| T | 12 | Closed and pushed. |
| J | 0 | No rows in current parser; no AWS spend without explicit user approval. |
| K | 8 | Closed and pushed. |

## Coverage Gate

Before any final AWS/R-tier phase:

```powershell
py -3.11 compact_v5\_status\scripts\scope_audit.py --all --summary
py -3.11 compact_v5\_status\scripts\scope_audit.py --all --strict
```

Required result:

- every nonzero-row block has ledger rows equal to expected rows;
- every row is `SHIPPED`, `N/A_CONSTRAINT`, `DEFERRED_USER_APPROVED`, or
  `DROPPED_USER_APPROVED`;
- no `PARTIAL`, `MISSING`, weak shipped evidence, unknown disposition, or
  ledger-missing rows remain;
- all user-approved defer/drop rows cite the exact approval;
- every closed block has a Claude approval and a pushed git checkpoint.

If `--all --strict` fails, do not run AWS/R-tier tests and do not claim final
readiness.
