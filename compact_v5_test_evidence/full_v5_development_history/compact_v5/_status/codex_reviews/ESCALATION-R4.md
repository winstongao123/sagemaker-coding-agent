# ESCALATION — R4 (cold-cache microcompact / PS#3)

Date: 2026-05-04
Worker: claude-opus-4-7 (1M context)
Trigger: feature not implemented in v5 (R4 cannot test what isn't there)
Cost spent on R4 so far: $0.00 (no AWS calls made)
Cumulative R-tier spend: $0.3662 / $14.25 (R1+R2+R3 only)

## What R4 claims to test

Per `compact_v5/docs/PS_V5_TEST_SET.md` line 87:
> **R4**: Send msg → wait 30 real minutes → send next msg → check cold-cache
> compact fires + saves ≥5K tokens. Validates PS#3 structural fix end-to-end
> (the cold-cache bug from v4 production).

## What v5 actually implements

v5's `core/compactor.py` only has `Compactor.should_compact()` based on
**token count** (80% of `context_max_tokens`). There is NO time-based
trigger.

Search results across `compact_v5/MAIN/agent/`:
- `grep "cold_cache|microcompact|MICROCOMPACT|COLD_CACHE_THRESHOLD"` → only HTML/docs/chat.md mentions ("microcompact wires later if at all"); no runtime code path.
- `grep "last_call_time|elapsed_seconds|seconds_since|idle"` → no time-tracking code path.

Per `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` line 164:
> | A-16 | Time-based microcompact (60-min idle clear) (R4 #36) | Runnable | microCompact.ts:411-530 | 80 | HIGH | CLEAN | Replaces v5's 30-min reactive trigger. |

A-16 was identified as a HIGH-priority Block A item from Runnable, but
PORT_LOG #066-070 (Block A) confirms it was NOT ported in v5.0.1 —
only token-threshold-based compaction landed.

Per `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` row #019:
> v5 QueryEngine **defers** microcompact (Phase 11), context_collapse (Phase 11),
> 2-stage smart compaction (Phase 11), [...]

## Why running R4 as designed would waste AWS spend

Three test attempts × $0.20 = $0.60 burned to confirm something already
visible from `grep`: v5 doesn't have time-based microcompact. The first
AWS call would return assistant text without firing any
`[COLD-CACHE]`/`[microcompact]` log line, the assertion would fail, and
diagnosis would simply confirm the missing feature.

Worse: a 30-minute real wallclock idle inside pytest is impractical
(test would block CI for 30 min). The test design implicitly assumes
A-16's 30-min trigger is wired; without it, monkey-patching `time.time()`
proves nothing because there's no consumer of the patched time value.

## Three options for resolution

### Option A — DEFER R4 to post-A-16 ship (RECOMMENDED for v5.0.1)

Mark R4 as **DEFERRED-NOT-IMPLEMENTED** in `r_tier_review_log.md` with
a clear reason: "v5.0.1 ships token-threshold compactor (Block A); A-16
time-based microcompact (PS#3) deferred to a future v5.x patch." Move
to R5.

Pros:
- Honest about v5.0.1 scope.
- No wasted AWS spend.
- Doesn't block ship — v5.0.1 ship gate already excluded A-16 (per
  PORT_LOG #019 deferral).
- Aligns with R8 precedent (mock test, $0 cost) for cases where the
  feature shape doesn't fit a real-AWS scenario.

Cons:
- Leaves a gap in PS#3 empirical coverage. Mitigation: PS#3 v4 production
  evidence stays valid; v5.0.1 inherits v4's threshold-based fall-back
  via Compactor.

### Option B — Implement A-16 NOW (large scope; not R-tier work)

Port Runnable's `microCompact.ts:411-530` time-based trigger into v5
Compactor. Estimated ~80 LOC + lock tests + ADR. Then run R4 as designed.

Pros:
- Closes the PS#3 gap structurally.
- Empirical R4 coverage on real Bedrock.

Cons:
- This is BLOCK-A FOLLOW-UP work, not R-tier validation. Adds ~1 day
  to v5.0.1 ship. Out-of-scope for the current R-tier sweep.
- Even if implemented, the test still needs a 30-min wallclock idle
  OR a mockable time.time() — the test design needs reshaping anyway.

### Option C — Reshape R4 to test what v5 DOES have

Write R4 as a "v5 idle-resume robustness" test: send msg, sleep 5
seconds (not 30 min), send next msg, verify conversation continues
without error. Cost cap drops to ~$0.05.

Pros:
- Cheap, runnable now.
- Proves v5 doesn't crash on idle resume — a real (if weaker) capability.

Cons:
- Doesn't validate PS#3 structurally. Test name + claim must change to
  match new scope. Misleads anyone reading the playbook.

## Worker recommendation

**Option A**. Mark R4 DEFERRED in the review log, document A-16 as a
named follow-up, and continue to R5. R-tier's job is to validate what
v5 ships; trying to test missing features in real-AWS is wasted spend
and a test-design lie.

If the user prefers Option B (closing the PS#3 gap before v5.0.1 ship),
that's a separate Block-A patch with its own design + Codex review +
unit tests + then-runnable R4. Should be a separate task.

If the user prefers Option C, I can write the reshaped test in ~10 min
without AWS spend until it's ready.

## Question for user

Which option do you want me to take?

A) DEFER R4 (mark DEFERRED-NOT-IMPLEMENTED in review log, continue to R5)
B) Implement A-16 now (Block A follow-up patch + ~1 day)
C) Reshape R4 to test idle-resume robustness only (cheap, weaker claim)

If you don't reply within the working session, I will default to
**Option A** (DEFER + continue to R5) since it's the lowest-risk
non-destructive path that preserves R-tier momentum.
