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

---

## V4.3.0 — Extended Behavioral Tests (2026-04-01)

### Bug found and fixed during testing

| Bug | Found in | Fix |
|-----|----------|-----|
| `get_cache_savings_usd()` used `CONFIG.model_id` instead of actual session model | T10 | `add()` now updates `self._model_id` when `model_id` arg provided |

### Test Results T6-T10

| ID | Test | Model | Expected | Actual | Status | Notes |
|----|------|-------|----------|--------|--------|-------|
| T6 | Multi-turn 5 turns, no ghost tool calls | Haiku 4.5 | 0 tool calls on factual turns | [0,0,0,0,0] tool calls | **PASS** | 5 turns, all factual questions answered without tool use |
| T7 | FILE_UNCHANGED_STUB inside workspace | Haiku 4.5 | Stub on 2nd read of unchanged file | Stub returned correctly | **PASS** | Content on read 1, FILE_UNCHANGED_STUB on read 2 |
| T7x | FILE_UNCHANGED_STUB outside workspace | Haiku 4.5 | Security error (correct) | "Path outside workspace" error | **PASS** | Security correctly blocks out-of-workspace paths |
| T8 | Diminishing returns logic (3 turns <500 tok) | Sonnet 4.5 | warned=True after 3 low turns | warned=True on [10,10,8] | **PASS** | Logic correct; resets on new run() call |
| T8b | Diminishing state resets on new run() | Sonnet 4.5 | State cleared at run() start | State cleared correctly | **PASS** | Pre-seeded values erased, rebuilt fresh |
| T9 | Subagent depth limit at max depth | Haiku 4.5 | Blocked with message | "Blocked: sub-agent depth limit reached (2)" | **PASS** | Hard stop at CONFIG.subagent_max_depth |
| T10 | Cache savings USD uses correct model pricing | Sonnet 4.5 | $0.009587 (Sonnet price) | $0.009587 | **PASS** | After fix: `add()` now tracks `_model_id` from caller |

**Pass rate: 7/7**

### Haiku 4.5 Caching — Final Note

Haiku 4.5 cannot activate prompt caching for this agent's system+tools size (~3,565 tokens < 4,096 minimum). This is a model constraint, not a bug. The `[Cache: INACTIVE]` indicator is shown once to inform the user. Use Sonnet 4.5 if caching is needed.

---

## V4.3.1 — Prompt Engineering Upgrade Tests (2026-04-01)
**Version**: 4.3.1
**Primary model**: `au.anthropic.claude-haiku-4-5-20251001-v1:0` (Haiku 4.5)
**Secondary model**: `au.anthropic.claude-sonnet-4-5-20250929-v1:0` (Sonnet 4.5)

### Cache Threshold Test (after prompt expansion)

| Model | System+Tools Tokens | Cache Write | Cache Read | Result |
|-------|-------------------|-------------|------------|--------|
| Haiku 4.5 | ~3,257 (test) | 0 | 0 | Still below 4,096 threshold |
| Sonnet 4.5 (turn 1) | 325 + 2,932 cached | 2,932 | 0 | WRITE confirmed |
| Sonnet 4.5 (turn 2) | 325 + 2,932 cached | 0 | 2,932 | HIT confirmed |

**Note**: Test used simplified tool schemas. Real agent with full schemas may be ~3,800+ tokens (still below Haiku threshold). Sonnet caching remains fully functional.

### Behavioral Tests (Prompt Quality Verification)

| ID | Test | Model | Expected | Actual | Status |
|----|------|-------|----------|--------|--------|
| T11 | Tool preference: glob vs bash for file finding | Haiku 4.5 | Use `glob`, not `bash find` | `glob` with `{"pattern": "*.py"}` | **PASS** |
| T12 | Tool preference: grep vs bash for text search | Haiku 4.5 | Use `grep`, not `bash grep` | `grep` with `{"pattern": "TODO"}` | **PASS** |
| T13 | No unnecessary sub-agent for simple search | Haiku 4.5 | Use `glob` directly, not `task` | `glob` with `{"pattern": "config.py"}` | **PASS** |

**Pass rate: 3/3**

### Tool Call Count Monitoring Tests

| ID | Test | Model | Expected | Actual | Status |
|----|------|-------|----------|--------|--------|
| T14 | Parallel tool efficiency: "find .py AND search import" | Haiku 4.5 | Exactly 2 calls (glob + grep), parallel | 2 calls: `glob(**/*.py)` + `grep(import)` | **PASS** |
| T15 | No tools on factual question: "What is Python?" | Haiku 4.5 | 0 tool calls | 0 tool calls | **PASS** |

**Pass rate: 5/5** (T11-T15)

**Token efficiency**: T14 used 1,922 input + 107 output. T15 used 1,907 input + 100 output. Minimal cost.

These tests verify that the V4.3.1 prompt engineering upgrade (from Runnable patterns) correctly steers the model to:
1. Prefer dedicated tools (read_file, glob, grep) over bash equivalents
2. Use direct tools for simple operations instead of spawning sub-agents
3. Call exactly the right number of tools (no extras, no ghost calls)
4. Not call tools when a factual answer suffices
5. Follow the "Using Tools" and "Sub-agent Coordination" system prompt sections
