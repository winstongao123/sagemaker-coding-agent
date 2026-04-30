# V5 Build Status

Last updated: 2026-04-30 (Phase 01 DONE)
Updated by: Phase 01 close pass

## Current phase
- Phase ID: 01 (canonical: 00..13 or 08_5)
- Phase name: Phase 1 — Bedrock client + Config
- State: DONE
- Started: 2026-04-30
- Target completion: 2026-04-30

## Done in this phase so far
- [x] Read v4 BedrockClient (`compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560`) — verbatim source for the port
- [x] Append **ADR-005**: "BedrockClient: REUSE v4 verbatim (Bedrock-native), defer Runnable cache-break detection to Phase 6"
- [x] Append **ADR-006**: "Config + JSONC loader: REUSE v4 verbatim"
- [x] Both ADRs are pure-v4-reuse → **no Runnable port row added** to `V5_RUNNABLE_PORT_LOG.md` (correct: Runnable's `claude.ts` is Anthropic-direct, not applicable to Bedrock; `promptCacheBreakDetection.ts` deferred to Phase 6 per ADR-005)
- [x] Write `runtime/bedrock_client.py` (~340 LOC; verbatim port from v4 + lazy CONFIG import + injectable client param)
- [x] Write `runtime/config.py` (~290 LOC; verbatim port from v4)
- [x] Write `tests/unit/test_bedrock.py` (13 tests covering: Config singleton, v4 critical defaults, JSONC stripper, BedrockClient mock mode, mock response shapes, mock heuristics, **PS Issue #4 — thinking config sent on EVERY call when enabled (3-call assertion)**, thinking NOT sent when disabled, cache boundary split marker, cache disabled when CONFIG off, **cache-validation fallback strips cache + retries once + preserves thinking config (Codex finding 2)**)
- [x] Relax `tests/test_smoke.py` Phase-0-only emptiness guard → positive Phase-01 presence check
- [x] `pytest tests/` — 13/13 PASS
- [x] Codex review (gpt-5.5, reasoning=medium) saved to `_status/codex_reviews/phase-01.md` → **APPROVE_WITH_FIXES**, B-axis N/A
- [x] Address all 3 Codex findings:
  - [x] **Major** — `BedrockClient.__init__` now accepts injectable `client=` param so unit tests no longer require boto3 to be installed
  - [x] **Minor** — Added `test_cache_validation_error_strips_cache_and_retries_once` covering the cache-fallback retry path
  - [x] **Minor** — This `V5_BUILD_STATUS.md` rewritten to match actual Phase 01 state and the no-Runnable-port decision

## Remaining for this phase
- [x] `MAIN/changelogs/CHANGELOG_v5_phase_01.md` written
- [x] `python tests/lint_phase_id.py 01` — 4/5 pre-commit (commit-subject check is the only fail, expected pre-commit; will pass post-commit)
- [x] git commit (subject: `v5/phase-01: port v4 BedrockClient + Config to runtime/`)
- [x] git tag `v5-phase-01`
- [x] Update this file: State=DONE, "Next session: pick up at" → Phase 02

## Tests status
- Last `pytest` run: 2026-04-30 — **PASS — 13/13** (`tests/test_smoke.py` 2/2 + `tests/unit/test_bedrock.py` 11/11 including the 2 new Codex-finding tests)
- Failing tests (if any): none

## Codex review status (current phase)
- Last review: 2026-04-30 (gpt-5.5, reasoning=medium) — **APPROVE_WITH_FIXES**
- Findings: 1 major + 2 minor — all addressed (see "Done in this phase so far" above)
- Open review comments: 0
- Saved at: `_status/codex_reviews/phase-01.md`

## Git
- Branch: v5-build
- Last commit: f0c2c3c "v5/phase-01: port v4 BedrockClient + Config to runtime/ + Codex fixes"
- Last tag: v5-phase-01

## Blockers
- none

## Next session: pick up at
- **Start Phase 02 — Tool Protocol + registry.** Read Runnable `tools.ts` + `Tool.ts` BEFORE writing code. Port to `compact_v5/MAIN/agent/tools/registry.py` (replaces v4's monolithic `TOOLS = {}` dict at `compact_v4/MAIN/agent/sagemaker_agent.py:7105`). Include the deferred-tool-search hook `apply_tool_search_deferral()` as a stub (full deferred loading lands in Phase 7). Append ADR-007 + ADR-008 documenting the Tool Protocol shape and the registry pattern. Add `tests/unit/test_registry.py` covering: registry lists tools without loading schemas, deferred tools annotated, plan-mode subset filter, feature gates.
- Resume protocol: see `_status/RESUME.md`.
