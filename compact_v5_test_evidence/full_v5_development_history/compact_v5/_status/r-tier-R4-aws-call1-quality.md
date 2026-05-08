# R4 AWS Call1 Quality Review

Date: 2026-05-06
Model: `au.anthropic.claude-haiku-4-5-20251001-v1:0`
Cost: `$0.0230` against `$0.20` planned cap and `$0.24` hard ceiling

## Functional Result

Result: PASS

R4 call1 exercised the A-16 production cold-cache branch without a 30-minute
wall-clock wait by using the supported injectable threshold:

- `CONFIG.cold_cache_threshold_seconds=1`
- seeded idle gap: `5` seconds
- typed events: `compact_micro_start`, `compact_micro_end`
- `microcompact_applied=true`
- `microcompact_saved_tokens=50360`
- `microcompact_marker_count=2`
- final model answer: `R4 cold-cache microcompact ready.`

The test still measures the time-based cold-cache microcompact code path in
`QueryEngine.run()`. It does not downgrade R4 to a weaker idle-resume-only
claim.

## Process Result

Result: PASS

Process quality is acceptable for production-readiness evidence:

- one short Haiku Bedrock turn;
- zero tool calls;
- zero repeated calls;
- zero failure-loop events;
- no `compact_micro_failed` event;
- non-empty canonical telemetry with numeric cache fields;
- parent attribution recorded `cache_write_tokens=16668`;
- no subagent/reviewer attribution required because R4 does not delegate.

The visible stdout line `[i] Cold cache detected ... proactive microcompact`
confirms the user-facing path fired, while typed audit events provide the
machine-checkable evidence.

## Composite Verdict

Codex conclusion: NEAR_IDEAL

This is a genuine production-readiness signal for A-16/R4. The older
`ESCALATION-R4.md` remains preserved as historical evidence of the previous
deferment, but it is superseded by this READY run after the user required A-16
before production.
