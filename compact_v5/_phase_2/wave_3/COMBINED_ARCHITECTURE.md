# Wave 3 Combined Architecture Audit v5.0.1

**Generated**: 2026-04-30
**Status**: READY FOR CODEX REVIEW

## Summary: 17 Blocks Combined

Block 0 (Shim): v4 imports + v5 exports, 50 LOC
Block B (TokenTracker+AuditLogger+SnapshotManager): v4 verbatim, 390 LOC
Block B+ (SessionManager+Cost): v4 verbatim, 250 LOC
Block C (Exec-Limit+Dedup): v4 + Hermes :4639-4655, 250 LOC
Block C+ (Approval+Stop+Rate-Limits): v4 + v5 ext, 200 LOC
Block D (Slash Commands): v4 verbatim, 320 LOC
Block A (Compactor+Cold-Cache): v4 verbatim, 750 LOC, DEFER Runnable cache-edits
Block E+F (UI+Notebook): v4 verbatim, 2200 LOC
Block I (Skill Resolution): v4 + Hermes :4689-4720 fuzzy, 50 LOC
Block M (Tool-Call Limit): Runnable :1004-1048, 30 LOC
Block G (AGENT_TYPES+Worktree): v4 :6914-7090 + :8413-..., 280 LOC
Block G2 (Cache-Prefix): Runnable forkSubagent.ts :73-end, 100 LOC
Block H (Memory): v4 :7889-8028, 140 LOC, DEFER Runnable extractMemories
Block L (Error/Retry/Cache-Break): Runnable errors.ts + withRetry.ts + promptCacheBreakDetection.ts extend, 250 LOC
Block N (Hermes Patterns): Parallel-exec + dedup + fuzzy + ephemeral, 300 LOC
Block J (Real-Bedrock Smoke): v5 new, 150 LOC
Block K (Process Discipline): LF Axis C + per-block gate, 200 LOC docs

TOTAL: 6360 LOC, Medium Risk

DEFERRED-WITH-USER-APPROVAL:
- Runnable compact.ts cache-sharing (Block A)
- Runnable extractMemories.ts (Block H)
- Runnable commands/ framework (Block D)
- LF dynamic-tool-injection (Block N)

