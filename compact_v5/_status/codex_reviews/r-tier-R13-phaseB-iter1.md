# R13 Phase B Iter1 Failure Diagnosis

Date: 2026-05-05

AWS call: R13 call 1

Result: failed before billable model usage.

Raw log: `compact_v5/_status/codex_reviews/r-tier-R13-aws-call1.log`

Observed failure:

- Bedrock rejected the first request with `ValidationException`.
- Error text: `messages.0.is_meta: Extra inputs are not permitted`.
- R13 side metrics recorded `api_calls=0`, `cost_usd=0.0`, `stop_reason=fatal_error`, `score_passed=0`, `score_total=5`.

Root cause:

- `QueryEngine` stores internal message bookkeeping fields such as `is_meta` in `self.messages`.
- `BedrockClient.chat()` sent the message dictionaries to Bedrock unchanged.
- Bedrock accepts only API message fields such as `role` and `content`; it rejects internal top-level keys.

Fix applied:

- `compact_v5/MAIN/agent/runtime/bedrock_client.py` now strips internal top-level message fields before serializing chat and CountTokens payloads.
- Stripped fields: `is_meta`, `compact_metadata`, `compact_boundary`.
- The in-memory engine messages are not mutated.

Lock test:

- `compact_v5/MAIN/agent/tests/unit/test_bedrock.py::test_internal_message_fields_not_sent_to_bedrock`

Local gates after fix:

- `py -3.11 -m py_compile compact_v5/MAIN/agent/runtime/bedrock_client.py compact_v5/MAIN/agent/tests/unit/test_bedrock.py compact_v5/MAIN/agent/tests/r_tier/test_r13_coding_accuracy.py` passed.
- `py -3.11 -m pytest compact_v5/MAIN/agent/tests/unit/test_bedrock.py compact_v5/MAIN/agent/tests/r_tier/test_r13_coding_accuracy.py -q` -> `12 passed, 1 skipped`.
- `py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_a.py -q` -> `53 passed`.

Retry decision:

- Retry is justified only after fresh Claude Phase A approval on the fixed code.
- The failed call used no local R13 spend and did not consume meaningful AWS model cost because `api_calls=0`.
