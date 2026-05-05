# R15 Phase B Iteration 1 - Harness False Positive

AWS call: r-tier-R15-aws-call1.log
Side metrics: r-tier-R15-aws-call1-side-metrics.json
Cost: $0.1668
Classification: NOT READY due harness assertion, not model debugging failure.

Observed result:
- pre_fix_failed=true; fixture started with two failing tests and one passing false-positive test.
- post_fix_passed=true; final pytest output was 3 passed.
- false_positive_area_unchanged=true; classify_customer stayed intact.
- test_file_unchanged=true; test_order_utils.py hash matched the initial hash.
- diagnosis_trace=true; diagnosis.md contained both failing test names and root-cause terms.
- stop_reason=user_stop; the halt-after-ready guard fired after tests and diagnosis were complete.
- verdict=FAIL and completed=false because unexpected_files included runner/runtime artifacts.

Root cause:
The R15 runner treated pytest's own .pytest_cache files and the agent runtime's .sageagent_state trace files as unexpected model-created project files. These are not source edits and are created by the test harness/runtime, not by the model as speculative changes. The assertion was therefore over-strict and produced a false negative after a real pass.

Fix:
Update workspace file collection in test_r15_debugging.py to ignore __pycache__, .pytest_cache, and .sageagent_state when computing unexpected_files. The source/test/diagnosis allowlist remains strict: order_utils.py and diagnosis.md are the only allowed agent-facing project files beyond runner-created test_order_utils.py and pre/post pytest output captures.

Retry rationale:
This is one meaningful R15 AWS attempt. Remaining R15 cap after call1 is $0.3332. The retry uses the same fixture and model, with only the harness false-positive artifact filter corrected. Local gates must pass and Claude Phase A must re-approve before AWS call2.