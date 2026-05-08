# Phase 01 Codex Review — gpt-5.5 (reasoning=medium)

Date: 2026-04-30
Phase: Phase 1 — Bedrock client + Config
Diff: v5-phase-00..HEAD (Phase 01 staged, not yet committed)

## Verdict

**PHASE 01 OVERALL: APPROVE_WITH_FIXES**
- A-axis: implementation looks v4-faithful, but tests need boto3-free construction and cache-fallback coverage.
- B-axis: N/A, scaffold + pure-v4-reuse phase.

## AXIS A — Errors / bugs: CHANGES_REQUESTED

### Finding 1 (major)
- File: `compact_v5/MAIN/agent/tests/unit/test_bedrock.py:153`
- Issue: Non-mock unit tests instantiate `BedrockClient(..., mock_mode=False)`, which imports real `boto3` before the fake client is assigned. Contradicts the file's "runnable without boto3" contract and can fail in clean unit environments.
- Suggested fix: inject a fake boto3 module/client before construction, or add optional client injection to `BedrockClient`.

### Finding 2 (minor)
- File: `compact_v5/MAIN/agent/tests/unit/test_bedrock.py:215`
- Issue: Cache fallback retry path not covered. Tests cover cache block placement and cache disabled, but not `ValidationException` → strip `cache_control` → retry once → `prompt_cache_supported=False`.
- Suggested fix: add a fake client that fails once with cache validation, succeeds on retry, and assert second body has plain string system plus thinking still present if enabled.

### Finding 3 (minor)
- File: `compact_v5/_status/V5_BUILD_STATUS.md:14`
- Issue: Status doc stale/inconsistent: says "nothing done yet," tests "not yet written," and still references Runnable cache-placement ADAPT/PORT_LOG row even though ADR-005 says no Runnable port.
- Suggested fix: update before phase close.

### PS Issue #4 verification
- COVERED. `test_thinking_config_sent_on_every_call_when_enabled` sends 3 calls and asserts `thinking` and forced `temperature=1` on every body.

## AXIS B — Runnable-fidelity: N/A

No Runnable client code appears ported into the new runtime files. Search found only explanatory references to `promptCacheBreakDetection.ts`; no `claude.ts` Anthropic/OAuth/subscriber/global-cache detector logic is present. Deferring `promptCacheBreakDetection.ts` to Phase 6 is reasonable because current Phase 1 only has v4 string/list system prompt handling, not the future multi-block prompt section structure the detector needs.

## Required before tag

- [x] Fix the non-mock unit tests so they run without real boto3 — added `client=` kwarg to `BedrockClient.__init__`; tests now inject a fake client at construction time.
- [x] Add cache fallback retry coverage — `test_cache_validation_error_strips_cache_and_retries_once` asserts: 2 invocations, first had cache_control, second flattened to plain string, `prompt_cache_supported=False` after, thinking config preserved on retry.
- [x] Update `V5_BUILD_STATUS.md` to match actual Phase 01 state and no-Runnable-port decision.

All findings addressed before commit. `pytest tests/` → 13/13 PASS.
