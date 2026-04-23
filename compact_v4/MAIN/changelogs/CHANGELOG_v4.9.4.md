# CHANGELOG — V4.9.4 (2026-04-23)

## Summary

Six hermes-pattern enhancements landed in a single pass. These were the **real gaps** identified after the v4.9.3 deep-scan comparison — items I had wrongly deferred to "v4.10" but which should have been v4.9.x because each is a measurable production-reliability or cost win, all fully Bedrock-only / no-external-network.

Net change: **+336 / -33 lines** in `sagemaker_agent.py`. **32 new tests + 41 regression = 73/73 PASS.**

## What was added

### 1. `IterationBudget` — shared parent + sub-agent counter (cost ceiling)
New thread-safe class with a `consume()` / `remaining()` / `used()` API. Default ceiling 90 (matches hermes default; tunable via `CONFIG.max_iteration_budget`).

A parent agent creates one budget at the start of `run()`; sub-agents inherit the same instance via the new `iteration_budget=` kwarg in `Agent.__init__`. Each LLM turn (success or failure) increments the counter. When `consume()` returns False, the agent surfaces a clear "Budget exhausted: N/M iterations used" message and stops cleanly, preserving partial work.

**Why:** prevents runaway sub-agent costs. Without this, a parent + N sub-agents could each loop `max_turns` times — collective ceiling unbounded. Insurance/audit values predictable cost ceilings per user request. Source: hermes `run_agent.py:170 IterationBudget`.

### 2. `ErrorClassifier` + `BedrockErrorCategory` enum
~10 categories of Bedrock SDK exceptions, each with an explicit recovery action:

| Category | Recovery | Example trigger |
|---|---|---|
| `THROTTLE` | retry-with-jitter | `ThrottlingException`, "Rate exceeded" |
| `VALIDATION_CACHE` | retry-once-after-strip | cache_control rejected |
| `VALIDATION_OTHER` | abort | other validation failures |
| `CONTEXT_OVERFLOW` | shrink-input | "Prompt is too long" |
| `MODEL_NOT_READY` | retry-with-jitter | model loading |
| `MODEL_TIMEOUT` | retry-with-jitter | model call timed out |
| `ACCESS_DENIED` | abort | IAM / role config issue |
| `SERVICE_UNAVAILABLE` | retry-with-jitter | Bedrock outage |
| `TRANSIENT_NETWORK` | retry-with-jitter | connection reset / timeout |
| `UNKNOWN` | abort | safe default |

**Why:** replaces scattered try/except with structured failure handling. Audit logs become useful (you know WHY a call failed, not just THAT it did). Bedrock-only — no provider-fallback category. Source: hermes `error_classifier.py:24-58`.

### 3. `RetryPolicy` — jittered exponential backoff
Standard pattern: `sleep = min(cap, base * 2^attempt) * uniform(0, 1)`. Defaults: base=1.0s, cap=30s, max retries=4.

Wired into `BedrockClient` invoke_model path: classify → if recovery says retry-with-jitter and attempt < max → sleep + retry; otherwise → raise. Cache-validation errors keep their existing one-shot fallback (now expressed via the same loop, behaviour preserved).

**Why:** insurance prod env will hit Bedrock per-second-token limits at peak. Naive retry storms make it worse. Standard full-jitter pattern is well-documented. Source: hermes `retry_utils.py`.

### 4. `Compactor._prune_tool_results_for_summary` — pre-LLM pass
Cheap pre-LLM pass that walks messages and replaces oversized `tool_result` content with head/tail previews:
- Threshold: 2000 chars (configurable via class attrs)
- Keeps: first 800 chars + last 400 chars
- Replaces middle with `... [pruned N chars for summary] ...`

Handles both string `content` and `[{"type":"text","text":...}]` list forms. Idempotent. Doesn't mutate input.

**Why:** wastes summary tokens otherwise. A 50KB bash-output tool result becomes ~1.2KB before the summary LLM sees it. Cuts compaction cost meaningfully on tool-heavy sessions. Source: hermes `ContextCompressor`.

### 5. `Compactor._summary_client` — opt-in auxiliary model for compaction
New `CONFIG.compaction_model: str = ""` field. If set to a Bedrock model ID (e.g. `anthropic.claude-haiku-4-5-20251001-v1:0`), the Compactor uses that model for summary generation instead of the main client. Auxiliary clients are cached per model ID.

Default: empty string = use main model (no behaviour change unless opted in).

**Why:** Haiku is ~10x cheaper than Sonnet/Opus. On long sessions where compaction runs frequently, this is a real Bedrock cost win. Bedrock-only — no provider switch, just a different `modelId` in the same region. Token tracking is updated to charge against the model that actually ran. Source: hermes `ContextCompressor` auxiliary-model pattern.

### 6. Structured "Resolved Questions / Pending Questions" sections in summary template
Added 2 new sections (10, 11) to the existing 9-section summary prompt:

- **`Resolved Questions`** — list each Q the conversation has SETTLED with one-sentence resolution
- **`Pending Questions`** — list each Q still needing resolution with status (waiting on user / blocked on X / next-up)

The existing 9 sections are preserved (no regression). Pending Questions is the FIRST thing to look at when resuming after compaction.

**Why:** prose summaries leave the next session re-discovering "what was I doing?". Explicit Q/A structure reduces resume friction. Source: hermes `ContextCompressor` summary-structure pattern.

## Files Changed

| File | Change |
|---|---|
| `compact_v4/MAIN/agent/sagemaker_agent.py` | **+336 / -33 lines.** New: `IterationBudget`, `BedrockErrorCategory`, `ErrorClassifier`, `RetryPolicy`, `Compactor._prune_tool_results_for_summary`, `Compactor._summary_client`. Modified: `BedrockClient.chat()` retry loop, `Compactor.create_llm_summary` (pre-prune + aux client), `Compactor.create_summary_prompt` (Q/A sections), `Agent.__init__` (`iteration_budget` kwarg), `Agent.run()` (`consume()` per turn), `Agent._run_task_tool()` (sub-agent inherits budget), `Config` (`max_iteration_budget`, `compaction_model`). |
| `compact_v4/MAIN/agent/test_v494_hermes_patterns.py` | NEW — 32 tests across 6 sections + cross-cutting Agent constructor checks |
| `compact_v4/MAIN/changelogs/CHANGELOG_v4.9.4.md` | NEW |
| `compact_v4/CHANGELOG.md` | v4.9.4 entry |
| `SESSION_STATE.md` | v4.9.4 entry |
| `compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md` | §12 appended — hermes patterns adopted in v4.9.4, with rejection rationale for the deferred items |
| `compact_v4/compact_v4.zip` | Rebuilt with version 4.9.4 |

## Verification

- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version reports `4.9.4`
- `test_v494_hermes_patterns.py` (NEW) — **32/32 PASS**
- `test_v493_enhancements.py` (regression) — **11/11 PASS**
- `test_v491_unskill.py` (regression) — **10/10 PASS**
- `test_v49_auto_trigger.py` (regression) — **11/11 PASS**
- `test_v471_enhancements.py` (regression) — **9/9 PASS**
- `test_v461_path_fix.py` (regression) — PASS
- **Total: 73/73 deterministic tests green**
- Smoke tests for all 6 items confirmed working (IterationBudget exhaust, all 10 ErrorClassifier categories, RetryPolicy decisions, pruning preserves small/trims large, aux client returns main when unconfigured, summary template has Resolved + Pending sections)
- No Codex review (per `feedback_codex_skip_bedrock_patches.md` — Bedrock-only patches don't need it; self-review + tests cover the surface adequately)

## Migration

Fully additive. No breaking changes:

- Default `CONFIG.max_iteration_budget = 90`. Existing flows that hit fewer than 90 turns are unaffected. Long-running multi-sub-agent flows that previously could exceed 90 will now stop cleanly with a clear message — this is a safety win, not a regression.
- Default `CONFIG.compaction_model = ""`. Compaction continues using the main model as before. To opt in to cheaper summaries, set `CONFIG.compaction_model = "anthropic.claude-haiku-4-5-20251001-v1:0"` (or any Bedrock-available model in the same region).
- Retry loop preserves existing cache-validation fallback. New: also retries on throttle / model-not-ready / model-timeout / service-unavailable / transient-network up to 4 times with jittered backoff.
- Summary template: existing 9 sections unchanged, 2 new sections appended.

## Honest assessment

This was the right scope to add. v4.9.3 was lean but missed real production-reliability patterns from hermes. v4.9.4 closes those gaps without crossing into over-engineering — every line added solves a measurable problem (cost ceiling / debug visibility / rate-limit survival / token waste / cost on long sessions / resume quality). All 6 items are verified by deterministic tests.

Truly out-of-scope items still deferred: session-search via FTS5 + LLM (high cost, unclear demand), permission rule engine (UX redesign), mixture-of-models voting (cost concern). These remain in the v4.10 "evaluate when justified" list.
