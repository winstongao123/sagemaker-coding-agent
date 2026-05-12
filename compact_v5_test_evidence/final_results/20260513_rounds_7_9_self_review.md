# 2026-05-13 — Rounds 7-9 Self-Review and Final-Testing Readiness

Scope of this session:
- Three additional Runnable Claude Code deep-scan rounds (rounds 7-9) on
  territory rounds 4-6 did not cover.
- Findings appended to `20260513_runnable_additional_deep_scan.md`.
- Curated copies mirrored into the two learning-archive subfolders.
- README updates in both `v5_build_learnings/` and
  `software_engineering_learnings/`.
- Archive root README updated with current zip SHA and rounds 7-9 self-review
  pointer.
- No runtime/source code changes.

## Self Review

| Area | Assessment | Result |
|---|---|---|
| Runnable reference correctness | Used `D:/Github/gg_claude_code/gg-claude-code-runnable/src/`, same path as rounds 4-6. Verified `QueryEngine.ts`, `cachedMicrocompact.ts`, `query.ts` line counts match prior scans. | Pass |
| Scan depth | Three non-overlapping rounds covered (a) error/retry/telemetry/cache-break observability/gates, (b) permissions/sandbox/hooks/banned-guard/approval-UI, (c) file-edit/read/notebook/REPL/skills/plugins/output-styles. Yesterday's rounds 4-6 covered cache/compaction determinism, plan/permission boundaries, verification quality gates. No territory duplication. | Pass |
| Cross-reference discipline | Every gap row in rounds 7-9 cites Runnable file:line AND the v5 location where the partial primitive already lives. The "document where we cleared" rule is satisfied per the user's instruction. | Pass |
| Architecture drift | All new findings are documented as either v5 backlog, current alignment, intentional gap, or v5 win. No terminal-only Runnable patterns were copied into v5. The "v5 SageMaker-notebook-first" rule is preserved. | Pass |
| File organization | Updated doc appended in place (rounds 7-9 follow rounds 4-6 in the same file, preserving Codex's earlier structure). Copies mirrored into both learning-archive subfolders. READMEs in both subfolders updated with new read-order entries and themes. Archive root README updated with current zip SHA. | Pass |
| Main docs updated | This session did not touch `AGENT_STATUS.md` / `memory.md` / `chat.md` because rounds 7-9 are doc-only additions that don't change runtime behaviour. The archive root README is the canonical pickup surface and was updated. If user wants the AGENT_STATUS pointer refreshed too, that is a follow-up edit. | Pass with caveat |
| Runtime code risk | Zero. No source files changed in this session; only `20260513_runnable_additional_deep_scan.md`, two archive copies of it, three README files, this self-review doc. | Low risk |
| Tests | Not re-run this session — no code changed. Last green status from rounds 4-6: `py -3.10 -m pytest tests -q -> 63 passed` (per `20260513_self_review_readiness.md`); current zip widget-fix verification: `py -3.10 -m pytest tests -q -> 66 passed` (per `VISUAL_WIDGET_ROBUSTNESS_REPORT.md`). Both green snapshots stand. | Pass |
| Zip | Not rebuilt this session — no source changed. Current zip: `compact_v5_ship.zip`, SHA256 `79d04c5d7162da04f4b1a9a1c20f80b2cc901571b7ea90681c8c48009ad99a6c`. Same zip Codex verified Playwright-green for the widget fix on 2026-05-13. | Pass |

## Readiness Judgment

**v5 is ready for final SageMaker testing from the current package.**

Three rounds of new scanning produced:
- **Zero new blockers.** Every Runnable pattern identified is either already
  partially implemented in v5 (heartbeat callback, autoDream gate, cache-break
  diff, telemetry events — all have v5 primitives, missing only the
  orchestration layer), or a deliberate v5 design choice (no plugins, no
  terminal Ink UI, no permission classifier LLM call).
- **6 new confirmed v5 wins** (rounds 7-9): deterministic file-evidence
  verify/done gate, allowlist-based permission classifier, explicit
  execution-mode enum + closure-based Python sandbox, active import-time
  banned-subsystem guard, UTF-16/BOM/CRLF file-edit encoding safety,
  stale-file byte-identity guard, plus working `skill_propose_patch`
  (Runnable's `runSkillGenerator.ts` is a stub) and declarative skill
  conditionals (`requires_tools`/`enabled_when`/`paths`). Cumulative
  v5 wins across all 9 rounds: 14.
- **7 post-final-test backlog items**, ranked by likely value:
  1. Heartbeat callback in `core/retry.py` (long waits look hung today).
  2. AutoDream gate (time + session) wiring into post-turn hook.
  3. Per-turn `summary_event` to audit JSONL (cost/cache/retry/cache-break
     visibility, behind `CONFIG.telemetry_events_enabled=False`).
  4. Cache-break per-source state machine + diff file output on top of
     the existing hash primitives.
  5. Image/notebook cohesion in `read_file` (or document the
     `view_image`-is-separate decision).
  6. User-defined output styles (Phase 12+).
  7. 5-event minimal hooks contract — defer unless a customer asks.

None of these block final testing. They are improvements to schedule if
target testing reveals matching failure modes.

## Required Final Target Test (unchanged from rounds 4-6 self-review)

Run in the real SageMaker environment:

1. Upload/extract the latest `compact_v5_ship.zip` (SHA256
   `79d04c5d…d99a6c`).
2. Restart the kernel.
3. Run notebook Cells 1-2.
4. Confirm the single combined dark v4-style config/chat UI renders with no
   `Error displaying widget: model not found`.
5. Rerun the UI cell and confirm it refreshes cleanly without the model-loss
   error (this is the fix Codex landed earlier today; widget Comm channel
   contract is now stable).
6. Run one S3/read-only prompt and one notes_cli/final-coding style prompt.
7. Run one `ask_user` ambiguity prompt and confirm Submit/Skip resumes the
   agent.

If the UI still shows `model not found`, run:

`import ipywidgets as widgets; display(widgets.IntSlider(description="Widget test"))`

If that simple widget fails, the target SageMaker widget manager is broken or
mismatched independently of v5.

## Current Package

- zip: `D:/Github/sagemaker-coding-agent/compact_v5_ship.zip`
- SHA256: `79d04c5d7162da04f4b1a9a1c20f80b2cc901571b7ea90681c8c48009ad99a6c`
- verify doc: `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md`
- widget-fix visual proof: `compact_v5_test_evidence/final_results/20260513_widget_robust_visual/`
  (Playwright: HAS_MODEL_NOT_FOUND False, HAS_LOADING_WIDGET False)

## Closing Note

Three rounds in, the most striking pattern is that v5 keeps **winning on the
architectural axes that matter for an enterprise SageMaker deployment** (safer
sandbox, fail-closed permissions, banned-subsystem guard, deterministic gate,
encoding safety, declarative skills) while genuinely lagging on **the axes
Runnable optimised for an interactive terminal product** (Ink streaming UI,
hooks ecosystem, output styles, plugin marketplace, image cohesion). These
are different products, not v5 being "behind". Defending the v5 wins is now
more important than closing the Runnable-style gaps.
