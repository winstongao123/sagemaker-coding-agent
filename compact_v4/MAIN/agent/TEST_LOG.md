# V4 Behavioral Test Log

## V4.3.0 — Bedrock Behavioral Tests
**Date**: 2026-04-01
**Version**: 4.3.0
**Primary model**: `au.anthropic.claude-haiku-4-5-20251001-v1:0` (Haiku 4.5)
**Secondary model**: `au.anthropic.claude-sonnet-4-5-20250929-v1:0` (Sonnet 4.5)
**Region**: ap-southeast-2
**Tester**: Claude Code + user (Winston)

---

### Test Results

| ID | Test | Model | Expected | Actual | Status | Notes |
|----|------|-------|----------|--------|--------|-------|
| T1 | Cache indicator: Haiku below threshold | Haiku 4.5 | Show `INACTIVE` warning once | `[Cache: INACTIVE — prompt below model threshold...]` shown | **PASS** | Haiku 4.5 needs 4096 tok min; system+tools ~3565 tok |
| T2 | Cache WRITE+HIT: Sonnet 4.5 | Sonnet 4.5 | WRITE turn 1, HIT turn 2 | HIT on both turns (cache warm from prior test run) | **PASS** | Cache was warm from 3min prior run (5-min TTL). HIT is correct. |
| T3 | Parallel RO tools | Haiku 4.5 | glob + grep complete, no extra sequential calls, no error | Completed without error | **PASS** | msg_count=4 (user, assistant with 2 tools, tool results) |
| T4 | Subagent isolation | Haiku 4.5 | Subagent spawned, result returned, no parent context leak | Subagent invoked successfully | **PASS** | `[Sub-agent: explore]` present in output |
| T5 | Memory byte/line cap (V3-B) | Haiku 4.5 | 300-line memory truncated to ≤200 lines with WARNING | lines=206 (200 content + 6 header), WARNING shown | **PASS** | 200-line cap working correctly |

**Pass rate: 5/5** (T2 was flagged as FAIL by automated check due to strict WRITE expectation, but actual behavior was correct)

---

### Cache Behavior — Key Finding

**Haiku 4.5 caching NOT available** for current prompt size:
- System prompt: ~424 estimated tokens
- System + tools: ~3,565 actual tokens (per Bedrock usage field)
- Haiku 4.5 minimum cache threshold: **4,096 tokens**
- Result: Cache never activates on Haiku 4.5 with current setup

**Sonnet 4.5 caching WORKS**:
- Turn 1: `cache_creation_input_tokens: 3,228` (WRITE)
- Turn 2: `cache_read_input_tokens: 3,228` (HIT, saved ~$0.0032/turn)
- Savings per turn: ~90% of 3,228 × Sonnet input price

**Recommendation**: Use Sonnet 4.5 (`au.anthropic.claude-sonnet-4-5-20250929-v1:0`) when prompt caching is needed. Haiku 4.5 can be used for short, one-off tasks where caching won't activate anyway.

**Cache indicator behavior verified**:
- Haiku 4.5: `[Cache: INACTIVE — prompt below model threshold. Switch to Sonnet 4.5 for caching.]` (shown once)
- Sonnet 4.5: `[Cache: WRITE 3,228 tok]` on first turn, `[Cache: HIT 3,228 tok (saved ~$0.0032)]` on subsequent turns

---

### Edge Cases & Other Observations

| Observation | Status |
|-------------|--------|
| Empty dynamic system prompt block → Bedrock ValidationException | **FIXED** in V4.3.0 (only add dynamic block if non-empty) |
| microcompact cold-cache path uses keep_n=1 (more aggressive) | **Verified** via mock test: 4/5 results cleared vs 2/5 normal |
| Memory 300-line input capped to 200 lines with truncation warning | **Verified** (T5) |
| Auto-memory "already wrote" skip: scans messages for memory.md tool_use | **Verified** via code review (no Bedrock test needed — pure logic) |
| Diminishing returns warning: 3+ turns <500 output tokens → advisory | **Verified** via mock test (not triggered in short tests — expected) |

---

### Parallel RO Tool Detail (T3)

**Prompt**: "Use glob to find all .py files and grep for the word def in sagemaker_agent.py."
**Expected**: Agent calls both tools in parallel (not sequentially), returns combined results
**msg_count=4**: `[user, assistant(2 tool_uses), user(2 tool_results), assistant(text)]` — correct parallel structure
**No redundant tool calls**: Confirmed — agent did not re-call tools after first batch

---

### Subagent Isolation Detail (T4)

**Prompt**: "Use the task tool to run an explore subagent that lists files in the current directory."
**Result**: Sub-agent spawned with `explore` type, file cache isolated (thread-local context), parent context restored after completion
**No context leak**: Sub-agent file cache cleared on entry, parent context restored after `finally` block

---

## V4.2.1 Reference Tests (pre-V4.3.0, 2026-04-01)

| Test | Status | Notes |
|------|--------|-------|
| Bedrock ping: Haiku 3 | PASS | `anthropic.claude-3-haiku-20240307-v1:0` returned OK |
| FILE_UNCHANGED_STUB | PASS | Unchanged file returns stub instead of content |
| PTL retry (3 attempts) | PASS | prompt-too-long error triggers trim + retry |
| Parallel RO tools (V2-I) | PASS | 3-file parallel read confirmed |
| Cache beta header removed | PASS | No `anthropic_beta` header — Bedrock-native cache_control |
