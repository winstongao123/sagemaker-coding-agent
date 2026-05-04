# Block T Tests

Status: LOCAL_GATES_PASS_CLAUDE_APPROVED_READY_TO_STAGE
Date: 2026-05-04

## Commands Run

1. `py -3.10 -m py_compile compact_v5/MAIN/agent/runtime/tool_surface.py compact_v5/MAIN/agent/tools/read_file.py compact_v5/MAIN/agent/tools/view_image.py compact_v5/MAIN/agent/tools/tool_search.py compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/tests/integration/test_block_t.py`
   - Result: PASS
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-py-compile-iter1.log`

2. `cd compact_v5/MAIN/agent; py -3.10 -m pytest tests/integration/test_block_t.py -q`
   - Result: 17 passed, 14 skipped
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-pytest-iter1.log`

3. `cd compact_v5/MAIN/agent; py -3.10 -m pytest tests/tools/test_phase4_mutating_tools.py -q`
   - Result: 39 passed
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-phase4-tools-regression.log`

4. `cd compact_v5/MAIN/agent; py -3.10 -m pytest tests/unit/test_tool_search.py -q`
   - Result: 32 passed
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-tool-search-regression.log`

5. `cd compact_v5/MAIN/agent; py -3.10 -m pytest tests/integration/test_skills.py -q`
   - Result: 12 passed
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-skills-regression.log`

6. `cd compact_v5/MAIN/agent; py -3.10 -m pytest tests/integration/test_block_n.py -q -k "parallel_dispatch_audits_success_and_error or parallel_dispatch_repairs_json_string_args or parallel_dispatch_keeps_repetition_guard"`
   - Result: 3 passed, 25 deselected
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-block-n-parallel-risk-regression.log`

7. `py -3.10 -m py_compile compact_v5/_status/scripts/scope_audit.py compact_v5/MAIN/agent/tests/integration/test_block_k_process.py`
   - Result: PASS
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-low-fix-py-compile.log`

8. `cd compact_v5/MAIN/agent; py -3.10 -m pytest tests/integration/test_block_k_process.py -q`
   - Result: 10 passed
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-low-fix-block-k-process.log`

9. `py -3.10 compact_v5/_status/scripts/scope_audit.py --block T`
   - Result: 12 rows, 10 shipped, 1 dropped, 1 N/A, 0 blocking, `READY_TO_REVIEW_CLOSE`
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-scope-audit-iter2.log`

10. `py -3.10 compact_v5/_status/scripts/scope_audit.py --block T --strict`
    - Result: 12 rows, 10 shipped, 1 dropped, 1 N/A, 0 blocking, `READY_TO_REVIEW_CLOSE`
    - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-scope-audit-strict-iter2.log`

11. `py -3.10 compact_v5/_status/scripts/scope_audit.py --block T`
    - Result: 12 rows, 10 shipped, 1 dropped, 1 N/A, 0 blocking, `READY_TO_REVIEW_CLOSE`
    - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-final-scope-audit.log`

12. `py -3.10 compact_v5/_status/scripts/scope_audit.py --block T --strict`
    - Result: 12 rows, 10 shipped, 1 dropped, 1 N/A, 0 blocking, `READY_TO_REVIEW_CLOSE`
    - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-final-scope-audit-strict.log`

13. `py -3.10 compact_v5/_status/scripts/scope_audit.py --block T`
    - Result: 12 rows, 10 shipped, 1 dropped, 1 N/A, 0 blocking, `READY_TO_REVIEW_CLOSE`
    - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-post-ledger-field-scope-audit.log`

14. `py -3.10 compact_v5/_status/scripts/scope_audit.py --block T --strict`
    - Result: 12 rows, 10 shipped, 1 dropped, 1 N/A, 0 blocking, `READY_TO_REVIEW_CLOSE`
    - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-post-ledger-field-scope-audit-strict.log`

15. Documentation consistency pass from `PS_CLI_WOKER_DESIGN/GIT_CHECKPOINT_POLICY.md`
    - Result: PASS, with expected pre-commit `pending Block T checkpoint` git evidence marker documented.
    - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-doc-consistency-pass.log`

16. `py -3.10 compact_v5/_status/scripts/scope_audit.py --block T --strict`
    - Result: 12 rows, 10 shipped, 1 dropped, 1 N/A, 0 blocking, `READY_TO_REVIEW_CLOSE`
    - Log: `compact_v5/_status/v5_completion_audit/logs/block-t-pre-close-scope-audit-strict.log`

## Coverage Notes

- T-1/T-2: existing Phase 4 notebook_edit/view_image executor and registry
  behavior revalidated after the view_image limit change.
- T-3/T-4/T-10/T-11/T-12: covered by Block T integration tests.
- T-5: covered by the skills integration suite.
- T-6/T-7/T-8/T-10/T-11/T-12: new Block T lock tests added in
  `tests/integration/test_block_t.py`.
- User-highlighted Block N parallel dispatch risk: revalidated with the
  existing QueryEngine parallel fast-path tests for audit/error logging, JSON
  repair, and repetition tracking.

## Reviewer Gate

- Claude iter3 closure review: `APPROVE`, `READY_FOR_BLOCK_CLOSE_REVIEW`.
