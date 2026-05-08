Findings confirmed: the plan documents are corrected, but the worker entry-points (`06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`, `BLOCK_ORDER_AND_COVERAGE.md`, `STATUS.md`) do not yet reference the `SOFTWARE-*` blocks or `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`. No `blocks/SOFTWARE-*/` ledger directories exist yet either. Producing the review now.

---

REVIEWED FILES:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/reviews/third-deep-scan-claude-architecture-review-2026-05-05.md`
- `compact_v5/_status/v5_completion_audit/reviews/third-deep-scan-final-worker-readiness-claude-review-2026-05-05.md` (empty stub — this review file)
- `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`
- `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`
- `compact_v5/_status/v5_completion_audit/SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md`
- `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`
- `compact_v5/_status/v5_completion_audit/reviews/` directory listing
- Filesystem checks under `compact_v5/_status/v5_completion_audit/blocks/` for `SOFTWARE-STATE` / `SOFTWARE-SHELL`

FINDINGS:

1. **Runnable source path is correct and primary.** `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` line 31–32 names `D:\Github\gg_claude_code\gg-claude-code-runnable` as the primary Runnable reference and explicitly demotes the archived `_archive/compare_code/...` copy to "earlier comparison only." Matches the prompt's stated primary path.

2. **Prior architecture review's three required fixes are visible in the plan:**
   - **M-1 (per-turn `AGENT_STATUS.md` + `memory.md` injection, memory-extraction default flip):** folded into `SOFTWARE-STATE` scope (lines 146–151). Explicit text: "must explicitly wire bounded per-turn `AGENT_STATUS.md` and `memory.md` prompt/context injection and either enable memory extraction by default … or expose an opt-in path that R16 and R19-U10 exercise."
   - **M-2 (cross-platform process-tree kill):** folded into `SOFTWARE-SHELL` scope (lines 156–158). Explicit Windows JobObject / `CREATE_NEW_PROCESS_GROUP` and POSIX `os.killpg` language is present.
   - **M-3 (typed compaction audit actions):** folded into `SOFTWARE-COMPACT-TELEMETRY` scope (lines 164–169). Explicit `compact_auto_start` / `compact_auto_end` / `compact_micro_start` / `compact_micro_end` / `compact_failed` actions called out so `build_telemetry.py` can stop using substring matching.

3. **DS3-S* → SOFTWARE-* traceability table is present** (lines 178–199). Every confirmed gap is mapped to a specific SOFTWARE-* block, including DS3-S11 (memory wiring → STATE) and DS3-S18 (failure-loop telemetry → COMPACT-TELEMETRY + GATE), which the previous review flagged as implicit.

4. **The four zero-cost local tests required by the prior review are now listed** in `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` lines 250–256 and mirrored in `TEST_CASE_PREP.md` lines 105–111: `_TODOS` survives `/save`+`/resume`, `/done` refuses with explicit reason on stale evidence, shell timeout kills sleeping child tree with sentinel-file proof, real auto/microcompact emits typed audit actions consumed by `build_telemetry.py`.

5. **R16 sub-check separation is reflected in `OPTIMIZED_AWS_VALIDATION_PLAN.md`** (lines 70–79): status round-trip / todo round-trip / named-checkpoint round-trip / verify-blocked-on-stale-evidence / compaction event emitted / shell background lifecycle / final artifact quality. Cache fallback assertion is also pre-stated (lines 81–83).

6. **Async deferral is honestly recorded** in `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` (DS3-S6 → `SOFTWARE-ASYNC-DECISION`, current recommendation: defer). `OPTIMIZED_AWS_VALIDATION_PLAN.md` Stop Rules (line 96) requires honest reporting of subagent attribution.

7. **Worker entry-points are NOT updated.** This is the dominant readiness gap:
   - `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` Required Read Order (lines 56–84) does **not** include `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`. A worker that follows the file faithfully will never be told the `SOFTWARE-*` blocks exist.
   - `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` Block Order (line 313): `A -> E+F -> L -> N -> K -> T -> C -> B -> B+ -> C+ -> D -> F2 -> I -> G -> G2 -> G3 -> H -> H+ -> M -> J -> 0`. No `SOFTWARE-*` blocks appear. The worker would stop after `0`, not continue into the new blocks.
   - `BLOCK_ORDER_AND_COVERAGE.md` lists "21 audit blocks" only and has no row for `SOFTWARE-*`. Ripgrep for `SOFTWARE-` returns zero matches in either file.
   - No `blocks/SOFTWARE-STATE/` or `blocks/SOFTWARE-SHELL/` ledger directories exist on disk. There is no `LEDGER.md` template or canonical row source for the new blocks; `SYNTHESIS_MASTER.md` does not contain them, so Absolute Rule #2 ("`SYNTHESIS_MASTER.md` is canonical scope") needs an explicit carve-out for SOFTWARE-* blocks pointing to `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` as their canonical scope source.
   - `STATUS.md` "Next Action" still says "continue Block M from files." There is no statement that after `M -> J -> 0` close, the worker proceeds into the SOFTWARE-* queue.

8. **Test-plan side wiring is consistent.** `TEST_CASE_PREP.md` lines 96–116 do reference `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` and `SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md`. So the test-plan side is correctly cross-linked even though the worker driver is not.

9. **`SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md` is a good churn-control mechanism** (no reopening completed blocks without trigger), and matches the architecture review's expectation. It does not, however, list the SOFTWARE-* blocks themselves under "Remaining Blocks Carrying The Goal" — it still uses F2/I/G/G2/G3/H/H+/M/J/0 framing and could mislead the worker into thinking the SOFTWARE-* work is folded into existing blocks rather than new ones.

10. **The "third-deep-scan-final-worker-readiness-claude-review-2026-05-05.md" file already exists as a 1-line empty stub.** This is the file I am writing. Confirmed empty (offset 0/1 reads return file-too-short).

MISSING HIGH/CRITICAL GAPS:

No new architecture gap beyond the third-scan list. No critical Runnable / Hermes / Learning Factory / v4 capability is missing from the SOFTWARE-* scopes once M-1/M-2/M-3 are folded in (which they are). The remaining issue is documentation/queue-wiring, not architecture.

PLAN READINESS:

The plan documents (`THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`, `OPTIMIZED_AWS_VALIDATION_PLAN.md`, `TEST_CASE_PREP.md`, `SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md`) are READY. Architecture is coherent; ordering (`ASYNC-DECISION → STATE → CHECKPOINT → SHELL → RESULTS → SUBAGENT → COMPACT-TELEMETRY → GATE`) is correct, with `GATE` last because it consumes the evidence surfaces; no command surface conflicts (no `/project-*` introduced); test/AWS plan updates are sufficient and concrete. Pre-AWS evidence contracts can be updated by the worker from these files alone.

WORKER PROMPT READINESS:

NOT READY without three small file edits. A worker continuing strictly from files cannot today:

- discover the SOFTWARE-* blocks (not in Required Read Order);
- know where SOFTWARE-* blocks fit in the queue (not in Block Order or `BLOCK_ORDER_AND_COVERAGE.md`);
- find a canonical scope source for SOFTWARE-* rows (`SYNTHESIS_MASTER.md` doesn't contain them, and Absolute Rule #2 says it is the canonical source).

Required worker-prompt fixes before continuation:

- F1. Add `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` and `SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md` to the Required Read Order list in `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` (TEST_CASE_PREP and OPTIMIZED_AWS_VALIDATION_PLAN are already there).
- F2. Extend Block Order in `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` and `BLOCK_ORDER_AND_COVERAGE.md` to: `... -> M -> J -> 0 -> SOFTWARE-ASYNC-DECISION -> SOFTWARE-STATE -> SOFTWARE-CHECKPOINT -> SOFTWARE-SHELL -> SOFTWARE-RESULTS -> SOFTWARE-SUBAGENT -> SOFTWARE-COMPACT-TELEMETRY -> SOFTWARE-GATE`. Mark each as having canonical scope sourced from `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` rather than `SYNTHESIS_MASTER.md`, with `scope_audit.py` extended to recognize them or with a documented manual-row fallback until it is.
- F3. In `STATUS.md`, after the `Block H+ closed` block, add an explicit "Next stages after M/J/0 close: SOFTWARE-* queue per `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`" sentence so a fresh worker sees the long-task continuation without chat memory.

Optional but recommended: add an "Block Order" note to `SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md` listing the eight new SOFTWARE-* blocks alongside the completed-block table, so revisit triggers and new-block scope are in one place.

VERDICT: APPROVE_WITH_FIXES

The third-deep-scan plan and `SOFTWARE-*` block plan are architecturally fit and correctly incorporate the prior architecture review's M-1/M-2/M-3 refinements, traceability table, four zero-cost tests, R16 sub-check separation, and async deferral. The remaining work to be Codex-worker-ready is purely queue/documentation wiring (F1/F2/F3 above): add the third-deep-scan and revisit-plan files to the worker's Required Read Order, extend Block Order to include the eight `SOFTWARE-*` blocks with `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` as their scope source, and add a STATUS.md pointer so a freshly-resumed worker discovers the continuation from files alone. With those three edits applied, worker continuation from files (no chat memory) is achievable; without them, the worker will stop after Block 0 and never start the `SOFTWARE-*` queue.

