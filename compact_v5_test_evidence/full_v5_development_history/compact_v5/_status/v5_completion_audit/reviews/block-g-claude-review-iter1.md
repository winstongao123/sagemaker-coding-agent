All G-5 test evidence is verified. I have enough context to produce the closure review.

```text
EXPECTED ROW COUNT: 8
LEDGER ROW COUNT: 8
DISPOSITION COUNTS:
- SHIPPED: 8
- PARTIAL: 0
- MISSING: 0
- DEFERRED_USER_APPROVED: 0
- DROPPED_USER_APPROVED: 0
- N/A_CONSTRAINT: 0

REVIEWED ROWS:
- G-1: APPROVE - load_agent_memory_prompt at agent_memory.py:107 + memory_scope="project" on review agent at agent_types.py:158 + spawn injection at spawn.py:333; lock tests test_block_g.py:705 (project-scoped read) and test_block_g.py:755 (review subagent runtime injection); PORT_LOG #195 supersedes prior #090 deferral; ADR-031 §Linked port-log rows lists #195.
- G-2: APPROVE - is_agent_memory_path at agent_memory.py:83 with normalized commonpath via _resolve at agent_memory.py:29; lock test test_block_g.py:733 covers traversal, sibling-prefix, and inside paths; PORT_LOG #195; ADR-031 link.
- G-3: APPROVE - ONE_SHOT_BUILTIN_AGENT_TYPES frozenset computed at agent_types.py:174-178 (in-sync with one_shot=True flags such as line 103); lock test_block_g.py:81 covers explore/plan/verify/review one_shot membership and general/build/fork exclusion; PORT_LOG #086; ADR-031.
- G-4: APPROVE - get_agent_prompt(name, is_coordinator) at agent_types.py:188-203 drops SUBAGENT_NOTES via .replace at line 202; lock test_block_g.py:340 verifies coordinator slim prompt vs full prompt; PORT_LOG #086; ADR-031.
- G-5: APPROVE - IterationBudget class at core/budget.py:27 sharing wired through _new_child_engine at spawn.py:68 (budget=parent_engine.budget); lock tests test_block_g.py:267 + test_subagent.py:62 + test_subagent.py:400 cover object-identity sharing both via _new_child_engine and full spawn path; PORT_LOG #016; ADR-014/015/031.
- G-6: APPROVE - DEFAULT_AGENT_PROMPT verbatim phrasing at agent_types.py:38-44 with Runnable's "Do NOT add features, refactor, or introduce abstractions" wording; lock test_block_g.py:351 asserts the no-gold-plating phrasing; PORT_LOG #086; ADR-031.
- G-7: APPROVE - SUBAGENT_NOTES at agent_types.py:50-56 (tool-call-announcement, parallel-research, parent-cannot-see-tool-calls lines), wired into every AGENT_TYPES.system_suffix (e.g., line 91 for general); locks test_block_g.py:340 (presence in non-coordinator prompt) and test_block_g.py:81 (one-shot lock indirectly proves Notes wired); PORT_LOG #086; ADR-031.
- G-8: APPROVE - canonical row text says "already Block G2 in plan" so Block G2 helpers are the legitimate evidence: build_forked_messages at fork.py:126 and serialize_for_cache_prefix/cache_prefix_match_length at fork.py:206-231; lock tests test_block_g2.py:67 (byte-identical prefix across two children) and test_block_g2.py:142 (deterministic key-order serialization); PORT_LOG #094; ADR-033. Cache-prefix runtime wiring from spawn_subagent for agent_type="fork" remains an explicit ADR-033 §4 deferral and is not part of the G-8 canonical scope.

FINDINGS:
- LOW blocks/G/LEDGER.md G-8: code_evidence cites `subagent/__init__.py:28`, but line 28 is `AGENT_MEMORY_SCOPES` inside the `from .agent_memory import (...)` block. The fork re-exports actually start at `subagent/__init__.py:36` (`from .fork import (...)`). The re-export exists, but the line number is mislabeled.
- LOW _status/V5_DESIGN_DECISIONS.md ADR-031 §Notes / not in scope (around lines 2041-2043) still says "G-2 isAgentMemoryPath per-agent memory isolation lands in Block H along with the memory extraction infrastructure". This is now stale because PORT_LOG #195 and blocks/G/DECISIONS.md ship G-2 in Block G. The supersession is captured in PORT_LOG #090 ("superseded by #195"), PORT_LOG #195, and ADR-031 §Linked port-log rows (line 2032), but the prose §Notes section was not updated for this redo.
- LOW _status/V5_DESIGN_DECISIONS.md ADR-033 §4 + §Notes documents that fork-subagent cache-prefix replay is "NOT wired into spawn_subagent yet" and that wiring lands in Block L. The agent_type="fork" entry exists in AGENT_TYPES (agent_types.py:160-170) but spawn_subagent does not invoke build_forked_messages for it, so a runtime-spawned fork agent does not actually share a byte-identical API prefix today. This matches the canonical row text ("already Block G2 in plan") and is an explicit deferral, but the residual runtime gap should be tracked against Block L close.

DISPUTED FINDINGS:
- NONE: this is the first compliant Claude review for Block G, so no worker disputes have been registered.

REMAINING SHIP-BLOCKING ROWS: 0

VERDICT: APPROVE
SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW
```

End-of-turn summary: All 8 canonical Block G rows are present in the ledger as SHIPPED with valid code, test, PORT_LOG, and ADR evidence; no AWS/R-tier was claimed and no `/project-*` commands were added. Three LOW findings (a mislabeled line number for G-8 in the ledger, a stale ADR-031 §Notes prose section about G-2, and the documented ADR-033 §4 fork-runtime-wiring deferral) are advisory and not ship-blocking — verdict APPROVE / SHIP DECISION READY_FOR_BLOCK_CLOSE_REVIEW.
