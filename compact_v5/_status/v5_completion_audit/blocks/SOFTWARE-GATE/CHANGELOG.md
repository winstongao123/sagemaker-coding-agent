# SOFTWARE-GATE Changelog

Status: IMPLEMENTED_PENDING_CLAUDE_REVIEW
Date: 2026-05-05

Changed implementation:

- `compact_v5/MAIN/agent/runtime/gate.py`
  - added deterministic local evidence checks for status, tests, reviews, large result artifacts, subagent envelopes, and telemetry;
  - persists `last_verify.json` and `last_done.json` under `.sageagent_state/gates/`;
  - blocks stale/missing evidence and unresolved failure-loop telemetry.
- `compact_v5/MAIN/agent/commands.py`
  - `/verify` now runs the local gate and returns `verify_passed` or `verify_blocked`;
  - `/done` now requires a fresh passing verify record and returns `done_ready` only after rechecking evidence.
- `compact_v5/MAIN/agent/prompt/commands.md`
  - documents `/verify` and `/done` as enforced local evidence gates.

Changed tests:

- `compact_v5/MAIN/agent/tests/integration/test_software_gate.py`
  - verifies missing test/review evidence blocks `/verify`;
  - verifies `/done` requires a fresh passing `/verify` record;
  - verifies stale status after verification blocks `/done`;
  - verifies repeated failure-loop telemetry blocks close.

Affected original blocks:

- Block D command surface is strengthened but not reopened. The change is reviewed under active `SOFTWARE-GATE` scope because it is prompted by DS3-S4/PS3-9/DS3-S18.
