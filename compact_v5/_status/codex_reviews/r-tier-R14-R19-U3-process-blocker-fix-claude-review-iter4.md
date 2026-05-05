# Independent Review — Evidence-Ledger Update (iter4)

**Verdict: `APPROVE_FIX_AND_HAIKU_RETRY_PATH`**

AWS may proceed only to a fresh Stage 5 **Phase A design review** with `R_TIER_CALL=2`. Spend still requires Phase A `APPROVE_FOR_AWS_CALL`, explicit user spend approval, and AWS Budget headroom check.

## Acceptance Criteria

### 1. Diagnostic spend preserved without hiding/resetting — PASS
`r_tier_metrics.jsonl` rows 11–14 keep:
- R19-U3 call1 `$0.1090` `verdict=PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW` `completed=false`
- R19-U6 call1 `$0.0175` `verdict=CALL1_FUNCTIONAL_PASS_BUNDLE_BLOCKED` `completed=false`
- R19-U7 call1 `$0.0221` `verdict=CALL1_FUNCTIONAL_PASS_BUNDLE_BLOCKED` `completed=false` `breaker_fired=true`
- R18-E7 call1 `$0.1022` `verdict=PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW` `completed=false`

Costs, tool counters, and failure-loop counts are intact. `r_tier_review_log.md` rows 13–16 mirror the same diagnostic/non-ready classification. `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md:63-66` records that the gate change preserves these rows. No row was deleted, rewritten, or moved under cap.

### 2. Gate change is safe — PASS
- `r_tier_gate.py:23-29` adds `DIAGNOSTIC_NON_READY_VERDICTS = {FAIL, PROCESS_BLOCKER, PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW, DIAGNOSTIC_NON_READY, CALL1_FUNCTIONAL_PASS_BUNDLE_BLOCKED}` matching every diagnostic verdict actually present in the ledger.
- `check_costs` (`:197-227`) still sums every row including diagnostic ones into both `total` and `by_test`; the 20% buffer ceiling is applied per-test and matrix-wide. Diagnostic spend continues to count against budget.
- `check_test_evidence` (`:293-299`) still requires a `completed=True` row with `verdict in {GENUINE_PASS, READY}` before READY: `if not escalated and not pass_rows: errors.append(...)`. Diagnostic rows alone cannot satisfy READY.
- `:308-317` collects `diagnostic_calls` and accepts diagnostic rows only as "neither pass/ready nor diagnostic non-ready" rejections. Anything outside both sets still errors.
- `:360-369` only relaxes `outcome.completed` / `cost_cap_hit` telemetry checks for the specific `call` numbers that have a diagnostic verdict in JSONL. Pass-call telemetry is still strictly checked.
- R13/R14/R15 fixture-bound assertions (`:318-337`) remain gated on `row_is_pass`, so a diagnostic row cannot smuggle a missing `changed_files_within_fixture`. R16 subchecks and R19-U7 `breaker_fired` checks (`:370-399`) remain unconditional.
- New lock test `test_r_tier_gate_preserves_diagnostic_rows_before_later_pass` (`test_r_tier_gate.py:126-196`) constructs the exact diagnostic-then-pass shape (call1 `PROCESS_BLOCKER` `completed=False` + call2 `GENUINE_PASS` `completed=True`) and asserts `check_test_evidence(...) == []`. The pre-existing `test_r_tier_gate_detects_cost_cap_excess` continues to enforce cap math, and `test_r_tier_gate_rejects_semantic_bug_quality` still blocks `SEMANTIC_BUG_DETECTED`.
- Local pytest report `16 passed, 2 skipped` is consistent with these locks.

### 3. Haiku-only retry path remains valid — PASS
- `test_r14_multifile_refactor.py:26,257,267` pin `_HAIKU_45_AU = au.anthropic.claude-haiku-4-5-20251001-v1:0`, set `CONFIG.model_id = _HAIKU_45_AU`, and instantiate `BedrockClient(model_id=_HAIKU_45_AU, ...)`. No Sonnet fallback path exists in the runner.
- `test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:27,487,495` do the same for the Stage 5 bundle.
- Process-quality is still mandatory in the executable READY condition: R14 (`:319-324,369-371,388-389`) requires `read_or_search_before_edit AND not repeated_guard_loop AND stop_reason != max_turns`; Stage 5 (`:375-410`) requires `not repeated_guard_loop AND stop_reason != max_turns` plus R19-U3 `search_before_edit` (grep/glob, not `read_file`). `process_quality_ok` is ANDed into `completed_by_test` and `verdict`.
- R18-E7 hard ceiling at `$0.12` enforced via `_hard_ceiling("R18-E7")` (`:43-44`), `cap=_hard_ceiling(test_id)` in `_run_member`, and `assert metrics["cost_usd"] <= _hard_ceiling(metrics["test"])` (`:518`). Planned cap remains `$0.10` (`:32`); the prompt narrows replay to offset 2600 (`:88-91`).

### 4. Phase A gate ordering — PASS
- `R_TIER_EVIDENCE_CONTRACT.md:241-247` codifies "Historical diagnostic/non-ready metrics rows must remain in `r_tier_metrics.jsonl` and continue to count toward cumulative spend. A later READY gate may pass only when there is also a completed `GENUINE_PASS`/`READY` metrics row."
- The gate semantics implement that contract exactly.
- `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md:67-69, 145-147` reaffirm that no AWS retry is allowed until Claude CLI approves the local fix and retry path. The fix-summary `:144-147` repeats that constraint.
- The iter4 change is purely local (gate.py + zero-cost gate test); it does not enable spend by itself.

## Findings

### MEDIUM
None.

### LOW
- **LOW-A (new, evidence-ledger scope, non-blocking)**: `DIAGNOSTIC_NON_READY_VERDICTS` includes the bare string `"FAIL"`. Any future runner that writes `verdict="FAIL"` will be treated as diagnostic for telemetry-relaxation purposes, even when the run was a generic crash unrelated to the R14/R19-U3 process-blocker class. Cost still counts, READY still requires a separate pass row, but the call's telemetry will not be checked for `outcome.completed=true`. Consider tightening to `{"DIAGNOSTIC_NON_READY", "PROCESS_BLOCKER", "PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW", "CALL1_FUNCTIONAL_PASS_BUNDLE_BLOCKED"}` and migrating the runners to write a more specific diagnostic verdict instead of bare `"FAIL"` before R16.
- **LOW-2 / LOW-3 (carry from iter3, runtime-side, non-blocking for Stage 5 retry)**: `_predict_guard_failure_class` returns `python_exec_error` unconditionally for any `python_exec`, and `_failure_class` keys on `"error_during_execution"` while `_looks_like_tool_failure` keys on `"error_during_execution:"`. Address both before R16 long-app runs.

### INFO
- The lock test only models R1, but the gate logic is test-id-agnostic for the diagnostic-vs-pass discrimination, and the live R19-U3 / R18-E7 / R19-U6 / R19-U7 rows already exercise all four diagnostic verdicts in cost-summing without any test-id-specific code path.
- R14 retains the `_hard_cost_halt = over_budget OR _r14_ready` halt (`test_r14_multifile_refactor.py:269-273`). Because `process_quality_ok` is evaluated post-halt and is hard-asserted (`:388-389`), an artifact-correct/process-bad run will halt early and then fail the test, not silently pass. Asymmetry vs. Stage 5 R19-U3 (which restricts "search before edit" to `grep`/`glob`) is consistent with each prompt's spec.

## AWS Disposition

**AWS may proceed to a fresh Stage 5 Phase A design review with `R_TIER_CALL=2`.** Required before any spend:

1. New Phase A prompt + Claude `APPROVE_FOR_AWS_CALL` over the iter3+iter4 evidence package.
2. Explicit user spend approval and AWS Budget headroom check.
3. R18-E7 retry must hold the `$0.10` planned cap and the user-approved `$0.12` hard ceiling. Stop on `cost_usd > $0.12`.
4. Any recurrence of the R14/R19-U3 guard-class loop in the retry stops the matrix per `R_TIER_EVIDENCE_CONTRACT.md` guard-loop rule.
5. If Haiku still cannot pass after this fix and Claude-reviewed retry path, **stop and escalate**; do not switch R14/R19-U3 to Sonnet.
6. LOW-A, LOW-2, LOW-3 stay open and should be resolved before R16.

Do not delete, hide, or reclassify any call1 evidence during the retry.
