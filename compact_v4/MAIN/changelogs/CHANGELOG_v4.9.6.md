# CHANGELOG — V4.9.6 (2026-04-28)

## Summary

Production-hardening patch from the deep `compact_v4` review against `gg-claude-code-runnable`.

This release fixes high-risk runtime issues, tightens the skill policy, and adds durable long-running task status:

1. Skill keyword auto-loading is now global opt-in and default-off.
2. Compaction now produces a Bedrock-safe user-starting message history.
3. Build sub-agent worktree isolation now actually runs.
4. Dirty/untracked workspace state is overlaid into build worktrees.
5. Parallel build sub-agents serialize when worktree isolation is enabled, because `CONFIG.workspace` is process-global in the notebook kernel.
6. `AGENT_STATUS.md` is loaded every top-level run so critical instructions, plan, progress, blockers, verification, and next step can survive compaction and session drift.
7. SageMaker git handling is local-tree-only: local status/diff/log/worktree/commit are supported, while GitHub/`gh`/PR and remote git operations are not assumed.

## What Changed

### 1. No Skill Auto-Load by Default

Added `CONFIG.enable_skill_auto_trigger: bool = False`.

Keyword auto-trigger now requires both:

- global opt-in: `CONFIG.enable_skill_auto_trigger = True`
- per-skill opt-in: `auto_trigger: true`

`SkillInfo.auto_trigger` now defaults to `False`, and missing frontmatter defaults to `False`.

Explicit activation remains unchanged:

- `/skill use <name>`
- slash commands such as `/verify`, `/review`, `/batch`
- the `skill` tool when the model deliberately asks to load a skill

### 2. Bedrock-Safe Compaction

`Compactor.compact()` no longer creates an assistant-first history. It now emits:

1. `user`: conversation summary
2. `assistant`: compact acknowledgement
3. recent user-starting tail messages

This preserves role alternation and avoids Bedrock validation failures after compact.

### 3. Build Worktree Isolation Fixed

The V4.4 worktree branch was unreachable because `_worktree_path` started as `None` and worktree creation was gated on `_worktree_path is not None`.

V4.9.6 replaces that with `_worktree_ready`, so sequential `build` sub-agents now:

- create an isolated git worktree
- run inside that worktree
- merge changed/new/deleted files back on success
- discard the worktree on failure
- clean up the worktree after completion

### 4. Dirty-State Overlay

Git worktrees start from `HEAD`, but real self-use sessions often have uncommitted edits. V4.9.6 overlays dirty tracked files and untracked files into the build worktree before the sub-agent starts, so the child sees the same current workspace state as the parent.

### 5. Parallel Build Safety

Parallel `task` calls still work for read-only/review/explore/general work. When two or more `build` tasks arrive in one model response and worktree isolation is enabled, the runtime now serializes them through the normal dispatch loop. This avoids racing a process-global `CONFIG.workspace` across multiple worktrees.

### 6. Durable Long-Running Status

Added `AGENT_STATUS.md` and `CONFIG.enable_status_doc: bool = True`.

The top-level agent now loads the status doc into context on every run. The `/status` command can show the file, `/status init` creates the default template, and `/status path` prints the exact path. This complements TODOs, checkpoints, session save/load, and compaction summaries for long-running coding tasks.

### 7. Local-Git-Only SageMaker Policy

SageMaker can have a local git tree, but it should not be treated as a GitHub runtime. The system prompt and bash tool guidance now instruct the agent to use local `git status`, `git diff`, `git log`, `git worktree`, and local commits/checkpoints. Bash security blocks remote git operations such as `git push`, `git pull`, `git fetch`, `git clone`, and remote reconfiguration.

## Files Changed

| File | Change |
|---|---|
| `MAIN/agent/sagemaker_agent.py` | Version bump to `4.9.6`; global skill auto-trigger config; default-off skill metadata; compaction role-order fix; reachable worktree setup; dirty-state worktree overlay; serialized parallel build tasks; durable status-doc loader and `/status` command; local-git-only SageMaker policy; updated header docs. |
| `MAIN/agent/AGENT_STATUS.md` | New durable handoff template for current goal, standing user instructions, plan, progress, risks, changed files, verification, and next step. |
| `MAIN/tests/test_v42_gap_closure.py` | Added V4.9.6 regression coverage for compaction order, skill default-off, status-doc loading, worktree activation/merge, dirty-state overlay, and serialized parallel build tasks. |
| `MAIN/agent/test_v49_auto_trigger.py` | Updated expectations: missing `auto_trigger` now defaults false; global auto-trigger disabled blocks all keyword matches. |
| `MAIN/agent/test_v493_enhancements.py` | Test hygiene fix: CSO warning capture now re-enables logging locally, so prior tests that call `logging.disable()` cannot hide warnings. |
| `MAIN/agent/USER_GUIDE.md` | Documents no-default skill auto-load, `enable_skill_auto_trigger`, and the `AGENT_STATUS.md` long-running status workflow. |
| `MAIN/agent/chat.md` | Companion docs updated to V4.9.6, durable status handoff, and worktree hardening notes. |
| `MAIN/agent/chat.ipynb` | Banner and quick reminder updated for V4.9.6 status, skills, and worktree changes. |
| `docs/PRODUCTION_READINESS_STATUS.md` | New status document with remaining readiness gaps. |
| `CHANGELOG.md` | Top-level V4.9.6 entry. |
| `compact_v4.zip` | Rebuilt runtime bundle from the fixed files: 22 files, 223.4 KB compressed; flat runtime root layout with no `MAIN/agent/` wrapper. |

## Verification

Deterministic targeted tests:

- `test_v49_auto_trigger.py` — **11/11 PASS**
- `test_v491_unskill.py` + `test_v494_hermes_patterns.py` + `test_v495_self_patching.py` — **61/61 PASS**
- `test_v42_gap_closure.py` + `test_v493_enhancements.py` + `test_v471_enhancements.py` + `test_v461_path_fix.py` — **33/33 PASS**

Total deterministic targeted coverage: **105/105 PASS**.

Also verified:

- `py_compile` on changed Python files — PASS
- `_rebuild_zip.py` rebuilt `compact_v4.zip` — PASS; runtime bundle is 22 files / 223.4 KB with root entries `sagemaker_agent.py`, `chat.ipynb`, `AGENT_STATUS.md`, `USER_GUIDE.md`, `memory.md`, and `skills/...`

Known validation gap:

- The legacy `test_production.py` / `test_advanced.py` scripts are live Bedrock harnesses that execute work at import time and are not clean pytest suites.
- `test_v46_live.py` still contains pytest-collected live tests that require a missing `model_id` fixture.

## Production Readiness

V4.9.6 is safer for personal SageMaker self-use than V4.9.5, but it is not "100% production ready" for shared or regulated production use. See `docs/PRODUCTION_READINESS_STATUS.md`.

Minimum next gates:

1. Clean the legacy/live test harnesses so pytest can run the full deterministic suite without import-time Bedrock calls.
2. Run a real SageMaker notebook smoke test with Bedrock.
3. Perform one fresh security pass on command execution, workspace boundaries, and memory/skill prompt-injection paths.
