# SOFTWARE-RESULTS Tests

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Saved logs:

- `logs/software-results-tests.log`
- `logs/software-results-regression-tests.log`
- `logs/software-results-py-compile.log`

Commands:

```powershell
cd D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
py -3.11 -m pytest tests/integration/test_software_results.py -q
py -3.11 -m pytest tests/integration/test_block_t.py::test_block_t_query_engine_enforces_tool_result_message_budget tests/parity/test_parity_non_critical.py::test_noncritical_01_tool_result_truncation_respects_per_tool_cap tests/r_tier/test_software_project_workflow_contracts.py::test_optimized_aws_validation_plan_supports_98_percent_confidence_gate -q
py -3.11 -m py_compile runtime/results.py tools/result_replay.py core/query_engine.py tools/__init__.py tools/registry.py tests/integration/test_software_results.py tests/integration/test_block_t.py tests/r_tier/test_software_project_workflow_contracts.py
```

Results:

- SOFTWARE-RESULTS focused suite: `4 passed`
- Regression/doc-contract suite: `3 passed`
- py_compile: PASS

No AWS/R-tier tests were run.
