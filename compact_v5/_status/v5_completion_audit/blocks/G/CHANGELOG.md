# Block G Changelog

Date: 2026-05-05

Audit pass:

- Reconstructed G-1 through G-8 from `SYNTHESIS_MASTER.md`.
- Created Block G audit artifacts.
- Superseded historical PORT_LOG #090 G-1/G-2 deferral.
- Added `subagent/agent_memory.py` with scoped per-agent memory prompt loading and normalized agent-memory path checks.
- Added `AgentType.memory_scope` and enabled project-scoped review-agent memory.
- Wired `spawn_subagent` to append scoped memory prompt for memory-enabled agent types.
- Added Block G lock tests for memory prompt loading, traversal-safe memory path detection, and review-agent runtime prompt injection.

Validation:

- Focused Block G suite: `25 passed`.
- Combined Block G/G2/subagent tests: `49 passed, 1 skipped`.
- py_compile: `PASS`.
- `scope_audit.py --block G`: `READY_TO_REVIEW_CLOSE`, 8 shipped, 0 ship-blocking rows.
- Claude review iter1: `VERDICT: APPROVE`, `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`, 0 ship-blocking rows.
- Applied Claude LOW cleanup notes for G-8 ledger line number and ADR-031 stale G-2 prose.
