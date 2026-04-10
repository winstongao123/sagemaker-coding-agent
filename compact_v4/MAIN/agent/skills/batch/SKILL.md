---
name: batch
description: Coordinator-worker orchestration for large multi-file tasks. Decomposes work into 3-30 independent units, spawns parallel workers in isolated worktrees.
triggers: batch, large refactor, migrate all, update all, refactor across, bulk change, many files, parallel workers, refactor all, change all, across all files
---

# Batch: Coordinator-Worker Orchestration

For large tasks spanning 5+ files. You are the COORDINATOR — you plan, synthesize, and direct. Workers implement.

**RULE: You NEVER write code yourself. Workers NEVER plan. Roles are separated.**

## Phase 1: Research & Plan (You are read-only)

1. Investigate the codebase to understand scope. Use explore agents for parallel research.
2. Identify ALL files that need changes. Be thorough — missing files means missing workers.
3. Find the project's build/test commands (package.json, Makefile, pyproject.toml).
4. Find an e2e test recipe that workers can run to verify their changes work.

## Phase 2: Decompose into Work Units

Write a numbered list of independent work units. Each unit must be:

- **Implementable alone** — no dependency on other units completing first
- **Verifiable alone** — worker can run tests to confirm their change works
- **Roughly uniform size** — split large units, merge trivial ones
- **3-30 units total** — fewer than 3 means this isn't a batch task; more than 30 means units are too granular

For each unit, specify:
```
Unit N: [short title]
Files: [list of files to modify]
Change: [specific description of what to change]
Test: [how to verify this unit works]
```

## Phase 3: Present Plan for Approval

Show the user:
1. Total scope (N units, M files)
2. The full unit list
3. The e2e test recipe
4. Estimated cost (N workers x ~10 turns each)

**WAIT for user approval before spawning workers.**

## Phase 4: Spawn Workers

Launch ALL workers in a single message using the `task` tool with multiple parallel calls:

```
For each unit:
  task(
    subagent_type: "build",
    description: "Unit N: [title]",
    prompt: [include ALL of the following]:
      - The user's original goal (one sentence)
      - This unit's specific task (from Phase 2)
      - Files to modify (absolute paths)
      - Exact change description
      - Codebase conventions to follow
      - e2e test recipe (how to verify)
      - "When done: commit your changes with a descriptive message"
  )
```

**CRITICAL**: Each worker prompt must be SELF-CONTAINED. Workers have no context from this conversation (unless using fork type). Include everything they need.

## Phase 5: Track Progress

As workers complete, update a status table:

```
| Unit | Status | Result |
|------|--------|--------|
| 1: Auth middleware | DONE | 3 files changed, tests pass |
| 2: Rate limiter | RUNNING | ... |
| 3: Error handler | PENDING | ... |
```

- **DONE**: Worker completed successfully
- **FAILED**: Worker hit an error — note what failed, decide if retry needed
- **RUNNING**: Still in progress

## Phase 6: Synthesize & Report

After all workers complete:
1. Summarize what was accomplished
2. List any failures and what to do about them
3. Run the e2e test recipe yourself to verify the overall result
4. Spawn a verify agent on the combined changes

**You are the quality gate. Workers executed — you must verify the result makes sense as a whole.**

## When NOT to Use Batch

- Task affects fewer than 5 files — just do it directly
- Changes are interdependent (file B depends on file A's output) — do sequentially
- Task requires deep reasoning, not mechanical changes — use plan + build instead
- You're unsure what needs to change — do research first, THEN batch
