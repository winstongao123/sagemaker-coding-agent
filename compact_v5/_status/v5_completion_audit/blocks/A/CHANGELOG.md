# Block A Audit Changelog

## 2026-05-04 Ledger-Only Audit

- Reconstructed Block A directly from `SYNTHESIS_MASTER.md:145-193`.
- Created a 43-row ledger with dispositions for A-1 through A-43.
- Recorded baseline git status, HEAD, block tags, R-tier gate output, and Block A pytest output.
- Identified ship-blocking rows, including A-16 time-based microcompact and A-25 post-compact tool_result stub injection.
- No production code was changed in this audit pass.

## 2026-05-04 A-16/A-25 Implementation Batch

- Implemented A-16 cold-cache microcompact in `core/compactor.py` and `core/query_engine.py`.
- Added pre-call idle-gap detection, keep-last-1 cold-cache clearing, and the `[i] Cold cache detected` output path.
- Implemented A-25 post-compact synthetic `tool_result` stub injection in `Compactor.compact()`.
- Implemented A-17 explicit `COMPACTABLE_TOOLS` allowlist for microcompact clearing.
- Added Block A tests for cold-cache keep-last-1, compactable-tool allowlist exclusions, 30-minute idle trigger, and orphaned `tool_use` repair.
- Added a skipped-by-default R4 executable marker at `tests/r_tier/test_r4_cold_cache.py`; it requires explicit real-AWS approval env vars before running.
- Updated Block A ledger/status/reviewer artifacts, PORT_LOG rows #105/#106/#107, and ADR-040.

## 2026-05-04 A-21 Post-Compact Cleanup

- Implemented `Compactor.run_post_compact_cleanup()` and wired it after successful `Compactor.run()`.
- Added production read-tracking cache clear and skill-listing cache clear helpers.
- QueryEngine now passes the active `skill_manager` into the compactor so post-compact cleanup can invalidate the skill listing cache without deactivating the selected skill.
- Added a Block A test for file-read tracking, file cache, skill-listing cache, and prompt-section cache invalidation.
- Updated Block A ledger/status artifacts, PORT_LOG row #108, and ADR-040.

## 2026-05-04 Broad Block A Helper Slice

- Implemented effective context reserve, named compact/token warning budgets, token warning state, auto-compact source/failure guards, summary sanitizers, API-round grouping, post-compact file/skill reinjection, memory-file exclusions, warning suppression, session activity heartbeat, abortable retry backoff, user-abort/stale-round helpers, surrogate sanitization, compact metadata/todo restoration/content replacement metadata, tool-schema token estimate, pre-API context guard, retry reset, prefix-stable normalization, `error_during_execution` diagnostics, `cache_ttl`, `is_meta` message markers, and content-hash temp paths.
- Added last-three Bedrock message `cache_control` application for prompt caching.
- Added broad Block A tests; latest local run is `48 passed` for `tests/integration/test_block_a.py`.
- Updated Block A ledger/status artifacts, PORT_LOG row #109, and ADR-041.
- Left A-13, A-27, A-33, A-34, and A-38 as explicit ship-blocking rows pending further implementation or user disposition.

## 2026-05-04 Remaining Block A Rows

- Implemented A-13 compacted parent-history fork replay via Block G2 `build_forked_messages`; streaming remains a documented no-streaming v5 adaptation.
- Implemented A-27 forced pre-compact memory extraction hook.
- Implemented A-33 active-session prompt-cache invariant freezing for model/system prompt/toolset, with `prompt_cache_now` opt-in for immediate cache breaks.
- Implemented A-34 `TransitionReason` enum and API-error transition handling.
- Implemented A-38 compact-boundary preservedSegment GC before model-visible turn construction.
- Added focused tests for A-13, A-27, A-33, A-34, and A-38; latest Block A test run is 53 passed.
- Updated Block A ledger/status artifacts, PORT_LOG row #110, and ADR-042.

## 2026-05-04 Iter10 LOW-Finding Fixes

- Fixed Claude iter10 LOW A-22 by strengthening the post-compact ordering lock test.
- Fixed Claude iter10 LOW A-30 by making `Compactor.reset_retry_counters()` clear `AUTO_COMPACT` failure state and strengthening the lock test.
- Fixed Claude iter10 LOW A-37 by wiring `CONFIG.cache_ttl` into Bedrock cache-control payloads with invalid-value fallback.
- Local validation remained green: py_compile passed and Block A suite passed with 53 tests.
- Updated Block A ledger/status artifacts, PORT_LOG row #111, and ADR-043.

## 2026-05-04 Claude Closure Review

- Saved the compliant closure prompt at `prompts/block-a-claude-review-iter8.md`.
- Recorded iter8 as `NO_VERDICT / HANDOFF_FAILED_AUTH_ROUTING` because the
  Claude subprocess inherited API-credit auth and returned `Credit balance is
  too low`.
- Recorded iter9 as `NO_VERDICT / HANDOFF_FAILED_AUTH_COMMAND` because
  `--setting-sources user,project,local` was split by PowerShell before review.
- Validated the Claude subscription reviewer path by temporarily clearing
  `ANTHROPIC_API_KEY`; smoke output is saved under
  `logs/claude-auth-smoke-20260504-163144.out.txt`.
- Recorded iter10 as the usable closure-scope review:
  `VERDICT: APPROVE_WITH_FIXES`,
  `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`.
- Claude iter10 verified 43 expected rows, 43 ledger rows, 43 SHIPPED rows, and
  0 remaining ship-blocking rows.
- Claude iter10 left three LOW findings for A-22 test thinness, A-30
  reset/evidence cleanup, and A-37 inert `cache_ttl` runtime wiring.

## 2026-05-04 Claude LOW-Fix Re-Review

- Saved the compliant LOW-fix re-review prompt at
  `prompts/block-a-claude-review-iter11.md`.
- Saved Claude stdout at `reviews/block-a-claude-review-iter11.md`.
- Saved Claude stderr at `logs/block-a-claude-review-iter11.log`.
- Claude iter11 returned `VERDICT: APPROVE` and
  `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`.
- Claude iter11 independently reconstructed 43 Block A rows from
  `SYNTHESIS_MASTER.md`, verified 43 ledger rows, 43 SHIPPED rows, and 0
  remaining ship-blocking rows.
- Claude iter11 verified A-22, A-30, and A-37 LOW findings are fixed and found
  no new Block A findings.
