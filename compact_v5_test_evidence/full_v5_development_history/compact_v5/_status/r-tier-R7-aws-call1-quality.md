# R7 AWS Call1 Quality Review

Date: 2026-05-06

Verdict: GENUINE_PASS

Composite verdict: NEAR_IDEAL

## Artifact Quality

- Correctness: PASS. The same Agent session made two Bedrock calls. The first
  used `au.anthropic.claude-haiku-4-5-20251001-v1:0`; the second used
  `au.anthropic.claude-sonnet-4-5-20250929-v1:0`.
- Context preservation: PASS. The Sonnet response recalled the exact
  pre-switch marker `R7-CONTEXT-VIOLET-913`.
- Switch assertion strength: PASS. The side metrics `used_model_ids` list is
  captured by wrapping the live `BedrockClient.chat` call before invocation, so
  it reflects the model id used on the wire for each call.
- Cache evidence: PASS. Numeric cache fields are present. The second Sonnet
  call recorded `cache_creation_input_tokens=3212`; side metrics preserve
  per-model usage and canonical telemetry records `cache_write_tokens=3212`.

## Process Quality

- Tool use: NEAR_IDEAL. The run exposed no tools and made zero tool calls.
- Failure loops: PASS. Canonical telemetry has zero failure-loop events.
- Model-switch traceability: PASS. The audit log contains a typed
  `model_switch` event with `path=same_agent_session`, and side metrics record
  the exact Haiku -> Sonnet model path.
- Cost/resource use: PASS. Total cost was `$0.0175`, below the `$0.50` planned
  cap and `$0.60` hard retry ceiling.
- Scope discipline: PASS. Only the approved R7 runner executed; no unrelated
  tests or AWS calls were batched.

## Evidence Note

Canonical telemetry has one aggregate `per_turn` row because both separate
`Agent.run()` calls log their local engine turn as `turn=1`; the row aggregates
the two `chat_response` audit events. This is not a blocker for R7 because the
raw audit and side metrics carry the load-bearing two-call evidence:

- first `chat_response`: Haiku-side usage and marker storage text;
- typed `model_switch`: Haiku -> Sonnet in the same session;
- second `chat_response`: Sonnet-side cache-write usage and marker recall text;
- side metrics `used_model_ids`: exact Haiku then Sonnet model ids.

## Conclusion

R7 is a genuine pass and an acceptable production-readiness signal for the live
Haiku-to-Sonnet same-session model-switch/cache invariant. No process-quality
follow-up is required from this run.
