# BLOCK_3_INTENT_DRIFT_GUARD — Review

## 1. v5 architecture preservation — ✅
The guard mirrors the existing `_final_claim_guard_message` pattern exactly:
- One-shot flag `_intent_drift_guard_sent` initialised next to `_final_claim_guard_sent` at `query_engine.py:423`.
- Triggers at the same final-text branch (`query_engine.py:1118-1127`) just after the final-claim guard, with identical `continue`/`break` semantics.
- Emits a meta user message via `xml_tag(XML_SYSTEM_REMINDER_TAG, ...)` with `is_meta: True` — same shape compaction already understands.
- Helpers `_is_s3_inventory_request` and `_final_text_has_s3_answer_or_blocker` are pure static functions → testable, no hidden state.

## 2. Scope drift — ✅
Only `compact_v5/core/query_engine.py` and the new `tests/test_s3_intent_drift_guard.py` are touched. No edits to Bedrock request shape, thinking signatures, tool dispatch, compaction, security manager, subagent receipts, or cost/cache accounting.

## 3. Regression risk — LOW
- Guard returns "" early when: (a) already fired, (b) request isn't S3 inventory, (c) text is empty, (d) the answer already contains an S3 answer/blocker term, (e) no local-source signal present. Ordering is correct (`query_engine.py:2284-2308`) — a legitimate S3 answer never gets re-routed.
- One-shot flag prevents loop amplification.
- The injected meta-message is the same shape as the final-claim guard's, so token accounting, prompt caching, and compaction behave identically.

## 4. Tests/checks — ✅ for this block, with two minor gaps
Covered: detection, local-tree drift triggers guard, real S3 answer suppresses, AWS-credential blocker suppresses.
Not covered (low priority, optional):
- One-shot behaviour (second call returns "" once `_intent_drift_guard_sent=True`).
- Negative case for non-S3 transcripts (e.g., "explain compact_v5") confirming `_is_s3_inventory_request` returns False end-to-end through `_intent_drift_guard_message`.
- Tests are smoke-style (`__main__`), not pytest-discoverable, but this matches the convention already used elsewhere in compact_v5.

## Issues found

**LOW — `local_signals` token "workspace" is broad** (`query_engine.py:2304`)
A legitimate S3 explanation like "I'd need to access your S3 *workspace* bucket" could trip the signal — but only if the text *also* lacks every S3 answer/blocker term, which makes the false-positive surface small. No fix required; flagging for awareness.

**LOW — Blocker term "approval" is generic** (`query_engine.py:2359`)
An unrelated "this action requires approval" final answer that also contains "s3" would suppress the guard. Practical impact tiny. No fix required.

**INFO — Patch file UTF-16 encoded**
`BLOCK_3_INTENT_DRIFT_GUARD_diff.patch` is written as UTF-16, which makes review tooling treat every other byte as null. The actual source files in the repo are well-formed UTF-8 — packaging issue only, not a code defect.

## Verdict: **APPROVE**

Block 3 is narrowly scoped, follows the established guard pattern, and introduces no regression risk to Bedrock shape, thinking signatures, tool dispatch, compaction, security, subagent receipts, or cost/cache accounting. The two LOW items above are polish, not blockers.
