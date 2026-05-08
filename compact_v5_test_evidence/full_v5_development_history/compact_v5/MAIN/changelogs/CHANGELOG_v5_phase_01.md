# CHANGELOG — v5 Phase 01

**Phase**: 01 — Bedrock client + Config
**Date closed**: 2026-04-30
**Tag**: `v5-phase-01`
**Branch**: `v5-build`

## Goal

Move v4's `BedrockClient` and `Config` (+ JSONC loader) out of the `compact_v4/MAIN/agent/sagemaker_agent.py` monolith into dedicated modules under `compact_v5/MAIN/agent/runtime/`. Add unit tests that lock the contract for **PS Issue #4**: thinking config must be sent on EVERY Bedrock call when `thinking_enabled=True`, not just the first message of a session.

## ADRs accepted this phase

- **ADR-005** — BedrockClient: REUSE v4 verbatim (Bedrock-native), defer Runnable cache-break detection to Phase 6
  - v4's BedrockClient is already Bedrock-native; Runnable's `claude.ts` is Anthropic-direct (subscriber/OAuth flows) and not applicable.
  - Runnable's sophisticated `promptCacheBreakDetection.ts` requires multi-block system prompts that don't exist until Phase 6's `prompt/sections.py` lands. Porting now would build a detector against a structure that doesn't exist yet → **DEFER to Phase 6**.
- **ADR-006** — Config + JSONC loader: REUSE v4 verbatim
  - v4 Config is Bedrock-tuned (no Anthropic equivalent). Verbatim port preserves all critical defaults: `max_iteration_budget=600` (PS Issue #2), `max_exec_calls_per_session=200` (PS Issue #7), `enable_skill_auto_trigger=False` (v4.9.6), `enforce_verify_contract=False` (v4.10.2), `enable_skill_patching=False` (v4.9.5), `enable_prompt_cache=True`, Sonnet 4.5 default model.

## Files added

| Path | LOC | Purpose |
|------|-----|---------|
| `compact_v5/MAIN/agent/runtime/bedrock_client.py` | ~340 | Verbatim port from v4 (`sagemaker_agent.py:2378-2560`). Includes `ToolCall`, `Response`, `BedrockErrorCategory`, `ErrorClassifier`, `RetryPolicy`, `BedrockClient`. Lazy `CONFIG` import to avoid circular dependency. New: `client=` kwarg for test injection (no boto3 required in unit tests). |
| `compact_v5/MAIN/agent/runtime/config.py` | ~290 | Verbatim port from v4 (`sagemaker_agent.py:1018-1287`). `Config` dataclass + `_strip_jsonc_comments` + `_load_config_file` + `_apply_config_file` + `CONFIG = Config()` singleton. |
| `compact_v5/MAIN/agent/tests/unit/test_bedrock.py` | ~370 | 11 unit tests. |
| `compact_v5/_status/codex_reviews/phase-01.md` | — | Phase 01 Codex review record. |

## Files modified

| Path | Change |
|------|--------|
| `compact_v5/MAIN/agent/tests/test_smoke.py` | Phase-0 emptiness guard relaxed (per its own comment "Once Phase 1 lands, this test gets removed / relaxed") and replaced with positive Phase-01 file-presence check. |
| `compact_v5/_status/V5_BUILD_STATUS.md` | Phase 01 progress reflected; Codex findings closure documented. |
| `compact_v5/_status/V5_DESIGN_DECISIONS.md` | Appended ADR-005 + ADR-006. |

## Tests

- `pytest tests/` — **13/13 PASS** in 0.07s
  - `tests/test_smoke.py::test_every_package_imports_cleanly` — every v5 package imports cleanly
  - `tests/test_smoke.py::test_phase_01_runtime_files_present` — Phase 01 ports exist
  - `tests/unit/test_bedrock.py` — 11 tests
    - `test_config_singleton_loads`
    - `test_config_v4_critical_defaults_preserved` — locks v4 critical default values
    - `test_strip_jsonc_comments_handles_strings_and_blocks` — JSONC stripper preserves strings
    - `test_bedrock_client_mock_mode_no_boto`
    - `test_bedrock_client_mock_response_shape`
    - `test_bedrock_client_mock_routes_list_files_to_list_dir`
    - **`test_thinking_config_sent_on_every_call_when_enabled`** — PS Issue #4 lock: 3 chat() calls, all 3 must include `body["thinking"]` block + `temperature=1`
    - `test_thinking_config_NOT_sent_when_disabled`
    - `test_cache_boundary_split_marker` — `# === DYNAMIC ===` splits system into static (cached) + dynamic (uncached) blocks
    - `test_cache_disabled_when_config_off` — `CONFIG.enable_prompt_cache=False` → plain-string system
    - **`test_cache_validation_error_strips_cache_and_retries_once`** — cache-fallback retry path: first call fails with `ValidationException: cache_control`, second call succeeds with cache stripped, `prompt_cache_supported=False` after, thinking config preserved on retry

## Codex review

- Model: `gpt-5.5` (reasoning=medium) via `codex exec --full-auto -s read-only`
- Verdict: **APPROVE_WITH_FIXES** → all fixes landed in this same phase before tagging
- AXIS A findings (3): all addressed
  - **Major**: tests required real boto3 because `BedrockClient(..., mock_mode=False)` imported boto3 in `__init__` before the fake client could be assigned → fixed by adding `client=` kwarg
  - **Minor**: cache-fallback retry path not covered → added `test_cache_validation_error_strips_cache_and_retries_once`
  - **Minor**: `V5_BUILD_STATUS.md` stale (referenced a Runnable cache-placement port row that ADR-005 explicitly does NOT create) → rewritten to reflect actual state
- AXIS B verdict: **N/A** (pure-v4-reuse phase, no Runnable patterns adopted; Codex confirmed no `claude.ts` / OAuth / subscriber / global-cache detector code was secretly ported)

## PS Issue mapping addressed

- **PS Issue #4 (thinking visible only on first message)** — STRUCTURAL FIX LOCKED IN.
  - The `thinking` body block is constructed inside `BedrockClient.chat()` on every invocation when `thinking_enabled=True`, not in a session-level "first message" branch. The model decides per-turn whether to RETURN a thinking block; the agent layer always SENDS the config so the budget is available every turn.
  - Test `test_thinking_config_sent_on_every_call_when_enabled` sends 3 chat() calls and asserts every captured body has the thinking block + `temperature=1`. Phase 01 cannot regress this without the test failing.
  - Verification continues in Phase 11 (UI thinking budget slider) and Phase 6 (system prompt note explaining model-side per-turn decision).

## What is intentionally NOT in this phase

- Sectioned multi-block system prompts (Phase 6).
- Sophisticated cache-break detection from Runnable's `promptCacheBreakDetection.ts` (Phase 6, when multi-block prompts exist).
- Extraction of `ErrorClassifier` + `RetryPolicy` to dedicated `core/errors.py` + `core/retry.py` (Phase 8 — they live inside `runtime/bedrock_client.py` for now to avoid Phase-1/Phase-8 circular dependency).

## Pickup point for next session

Phase 02 — Tool Protocol + registry. Read Runnable `tools.ts` + `Tool.ts`, port to `compact_v5/MAIN/agent/tools/registry.py` with the deferred-tool-search hook stub (full deferred loading lands in Phase 7). Resume protocol: `_status/RESUME.md`.
