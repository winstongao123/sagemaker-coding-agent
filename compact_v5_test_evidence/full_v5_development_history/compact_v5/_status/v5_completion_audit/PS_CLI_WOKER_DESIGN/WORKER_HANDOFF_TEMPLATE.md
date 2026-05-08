# Worker Handoff Template

Use this when the running worker needs to recover or continue without losing
scope.

```text
Reread and follow:
compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md
compact_v5/_status/v5_completion_audit/CLAUDE_REVIEWER_BASE_PROMPT.md
compact_v5/_status/v5_completion_audit/PS_COMPACTION_RESUME_CHECKLIST.md
compact_v5/_status/v5_completion_audit/STATUS.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/README.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/FLOW.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/WORKER_LED_LOOP.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/FAILURE_MODES.md

Current required behavior:
1. Trust SYNTHESIS_MASTER.md and block ledgers, not prior claims.
1a. After compaction/interruption, run the compaction resume checklist and
    recompute remaining work with `scope_audit.py --block <BLOCK>`.
2. After every meaningful code/test/doc/ledger change, save a fresh Claude
   prompt that includes CLAUDE_REVIEWER_BASE_PROMPT.md.
3. Run Claude directly with read-only settings and save stdout/stderr under
   reviews/ and logs/.
4. Read the saved Claude review.
5. Update:
   compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/REVIEWER_VERDICT.md
   compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md
   compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/STATUS.md
   compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/WORKER_SELF_REVIEW.md
6. If Claude rejects or requests fixes, fix and repeat.
7. Do not mark a block done while blocking rows remain.
8. Do not run AWS/R-tier spend, Codex review, nested codex exec, or git
   commit/tag/push without approval.
```
