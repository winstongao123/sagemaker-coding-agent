# Block L Decisions

Date: 2026-05-04

## Decisions

- Treat all 28 canonical Block L rows as local ship rows; no row is deferred,
  dropped, or marked N/A.
- Preserve v5's Bedrock-only synchronous runtime while adopting the Runnable
  and Hermes semantics through local helpers and Bedrock request wiring.
- Test daemon-thread responsiveness and heartbeat behavior with short local
  timeouts instead of AWS/R-tier wall-clock calls.
- Keep the retry curve backward-compatible by making persistent retry opt-in
  through `SAGEMAKER_UNATTENDED_RETRY=1`.
- Implement Bedrock guardrails as optional config fields and invoke kwargs;
  no guardrail call is made unless configured.

## Evidence

- PORT_LOG: #113.
- ADR: ADR-045.
- Tests: `logs/block-l-py-compile.log`, `logs/block-l-pytest.log`.

No human decision is currently needed for Block L.
