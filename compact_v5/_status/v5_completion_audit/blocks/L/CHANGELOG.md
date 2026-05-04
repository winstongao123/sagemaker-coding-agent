# Block L Changelog

Date: 2026-05-04

## Changed

- Expanded `core/errors.py` with Block L prompt-too-long, max-token overflow,
  rate-limit reset, 529, connection detail, API sanitizer/humanizer,
  rollback, generic error, and structured error helpers.
- Expanded `core/retry.py` with env-gated persistent retry, one-extra primary
  recovery, and a Bedrock-adapted three-tier recovery ladder.
- Expanded `core/cache_break_detection.py` with Bedrock prompt-state
  snapshots, source LRU, cache-miss threshold, TTL classification, cache-break
  diff output, and cache-control strip/hash helpers.
- Added Bedrock runtime client invalidation/rebuild, keep-alive disable,
  daemon-call heartbeat/stale-timeout helpers, context-scaled stale deadline,
  529 fallback trigger, and guardrail request kwargs in
  `runtime/bedrock_client.py`.
- Added guardrail, heartbeat, stale-call, and keep-alive retry config knobs to
  `runtime/config.py`.
- Expanded `tests/integration/test_block_l.py` to 40 local no-AWS tests with
  executable daemon/heartbeat coverage and no skipped Block L rows.

## Validation

- Compile: PASS (`logs/block-l-py-compile.log`).
- Targeted tests: 40 passed (`logs/block-l-pytest.log`).
- No AWS/R-tier spend.
