# v5 Build Learnings

This folder is the curated pickup point for lessons about building, stabilizing,
testing, and packaging compact_v5.

Key themes:
- v5 must stay SageMaker notebook first.
- Project evidence belongs under `<project>/compact_v5_wip/`.
- Runtime counters are the source of truth for cost/cache/token claims.
- UI progress, model transcript, and WIP audit are separate streams.
- Final coding-task noise should be fixed at the runtime-control layer, not by
  broadly changing model behavior.
- v5 leads Runnable on 14 axes (encoding safety, banned-subsystem guard,
  allowlist permissions, deterministic verify/done gate, etc.). Defend
  these wins instead of regressing to Runnable's design where v5 is stronger.

Recommended read order:
1. `20260513_runnable_additional_deep_scan.md` (now includes Rounds 4-9;
   rounds 7-9 added 2026-05-13 with new v5 wins on retry, sandbox, encoding,
   skill conditionals, banned-guard, and 7 post-final-test backlog items)
2. `runnable_claude_code_deep_dive_v5_stability.md`
3. `final_test_v5_responds_investigation.md`
4. `V5_PRODUCTION_TEST_READINESS_20260512.md`
5. `UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md`
6. `20260513_self_review_readiness.md`

## Backlog items added by rounds 7-9 (post-final-test)

- Heartbeat callback during long retry backoff (`core/retry.py`)
- AutoDream gate (time + session) wired into post-turn hook (`runtime/dream.py`)
- Per-turn telemetry events emitted to audit JSONL (`runtime/audit.py`)
- Cache-break per-source state machine + diff file output
  (`core/cache_break_detection.py`)
- Image/notebook cohesion in `read_file` (or document the separation)
- User-defined output styles (Phase 12+)
- 5-event minimal hooks contract — defer unless a customer asks
