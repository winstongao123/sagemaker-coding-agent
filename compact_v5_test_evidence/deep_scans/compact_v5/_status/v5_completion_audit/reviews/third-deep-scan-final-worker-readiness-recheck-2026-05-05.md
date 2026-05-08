F1:
- `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` Required Read Order (lines 56–86) now includes `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` (#26), `reviews/third-deep-scan-claude-architecture-review-2026-05-05.md` (#27), and `reviews/third-deep-scan-final-worker-readiness-claude-review-2026-05-05.md` (#28). `SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md` is also present at #24, and `PS_SOFTWARE_PROJECT_WORKFLOW.md` at #23. SATISFIED.

F2:
- Block Order in `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` line 316 reads exactly: `A -> E+F -> L -> N -> K -> T -> C -> B -> B+ -> C+ -> D -> F2 -> I -> G -> G2 -> G3 -> H -> H+ -> M -> J -> 0 -> SOFTWARE-ASYNC-DECISION -> SOFTWARE-STATE -> SOFTWARE-CHECKPOINT -> SOFTWARE-SHELL -> SOFTWARE-RESULTS -> SOFTWARE-SUBAGENT -> SOFTWARE-COMPACT-TELEMETRY -> SOFTWARE-GATE`.
- `BLOCK_ORDER_AND_COVERAGE.md` line 55 carries the identical sequence and lines 18–25 + 105–119 make `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` the canonical scope for the eight `SOFTWARE-*` blocks, with manual ledger fallback documented.
- `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` lines 318–322 also state SOFTWARE-* canonical scope source is `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` (not SYNTHESIS_MASTER) and require explicit per-block manual ledgers. SATISFIED.

F3:
- `STATUS.md` lines 47–55 (Third deep scan section) tell a fresh worker explicitly: "After M, J, and 0 close, the worker must continue through: SOFTWARE-ASYNC-DECISION -> SOFTWARE-STATE -> SOFTWARE-CHECKPOINT -> SOFTWARE-SHELL -> SOFTWARE-RESULTS -> SOFTWARE-SUBAGENT -> SOFTWARE-COMPACT-TELEMETRY -> SOFTWARE-GATE", with the no-AWS-spend gate restated. `BLOCK_ORDER_AND_COVERAGE.md` line 35 also says "After M, J, and 0 close, the worker must continue into the SOFTWARE-* hardening queue." SATISFIED.

REMAINING BLOCKERS:
- None for the three F1/F2/F3 fixes. Worker entry-points now reference SOFTWARE-* and `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` consistently.
- Note (non-blocking, out of scope of this recheck): no `blocks/SOFTWARE-*/` ledger directories exist on disk yet; that is expected since no SOFTWARE-* block has started, and the prompt instructs the worker to create explicit manual ledgers when entering each block.

VERDICT: APPROVE

