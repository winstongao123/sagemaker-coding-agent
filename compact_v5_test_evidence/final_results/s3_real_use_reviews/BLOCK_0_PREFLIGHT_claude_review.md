## Block 0 Preflight — Independent Review

**Verdict: APPROVE_WITH_NITS**

Block 0 is a clean read-only baseline. Diff is empty (0 bytes, as expected for "Files changed: none"), tests.log is 821 lines of grep evidence + file-existence checks, and the active tree claim is correct.

### Verification performed
- `compact_v5/compact_v5/` does **not** exist (Glob: 0 hits) — no stale nested-path assumption present
- Every active file the prompt cites exists: `compact_v5/ui/chat_ui.py`, `compact_v5/tools/python_exec.py`, `compact_v5/security/dangerous_patterns.py`, `compact_v5/security/manager.py`, `compact_v5/prompt/` (23 files), `compact_v5/core/query_engine.py`
- Final-claim guard confirmed at `compact_v5/core/query_engine.py:1110, 1134`
- tool_search deferral confirmed at `compact_v5/core/query_engine.py:544-547, 696, 1256, 2430-2432`
- `compact_v5.zip` present at repo root

### Findings

**MEDIUM**
1. **Block ordering risk: 1 before 3 may produce a false negative for the S3 path fix.** If the agent drifts to local-tree inventory (the open Block-3 issue) on the failing prompt "list file and bucket structure of my s3", it may never reach the S3 code path Block 1 is fixing. Either reorder to `3 → 1`, or require Block 1's evidence to include a prompt that forces an S3 call (e.g., explicit `s3://` URI) so the safe-read path is actually exercised. Reference: `compact_v5/AGENT_STATUS.md:128-130`.

2. **Block 6 is multi-lever.** "Cost controls for simple inventory tasks" combines retries + verbosity + tool_search + thinking — four distinct cost drivers explicitly called out in `AGENT_STATUS.md:131-132`. Recommend split into 6a (tool_search/retries) and 6b (thinking/verbosity) so a regression in one lever doesn't gate the other.

**LOW**
3. **No zip-vs-tree drift baseline captured.** Prompt declares "compact_v5.zip is built from the flattened compact_v5/ tree" but Block 0 evidence has no `compact_v5.zip` mtime/sha256 + per-file mtime snapshot. Without it, Block 7 ("zip / real AWS smoke") can't prove the zip matches the tree it was reviewed against. One-line `Get-FileHash` + `Get-Date` per file would close this.

4. **Out-of-scope git noise unannotated.** `tests.log:5-9` shows untracked `_archive/compare_code/gg-claude-code-runnable`, `.sageagent_state/`, `_zip_review/`, `memory.md` — none touch `compact_v5/`. Annotate as pre-existing project-root noise so a later reviewer doesn't think Block 0 left state behind.

### Sufficient to begin Block 1?
Yes — modulo Finding #1, which is operational guidance (force an S3 prompt), not a baseline gap.
