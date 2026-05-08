# Block H+ Decisions

Date: 2026-05-05

## Manual Only

H+ preserves the user decision from 2026-05-01: `/dream` is manual-only. The
Runnable daemon scheduler, background auto-fire behavior, and
`SAGEMAKER_AUTO_DREAM` style environment auto-enable are intentionally dropped.

## Runtime Shape

- `runtime/dream.py` owns the consolidation prompt, lock, backup, rollback, dry
  run, and `run_dream` entry point.
- `commands.py` owns the `/dream` command surface and emits
  `side_effect="dream_invoked"`.
- `ui/chat_ui.py` consumes that side effect and invokes the engine
  synchronously.
- Real LLM consolidation remains behind caller-provided consolidator and R-tier
  approval; local tests use dry-run/mocked consolidators.
