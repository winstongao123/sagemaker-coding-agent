---
name: code-review
description: Comprehensive code review — parallel agents for reuse, quality, efficiency + security checklist + iterative feedback
triggers: /review, /code-review, review my code, review this pr
auto_trigger: false
---

# Code Review

Systematic code review using parallel specialized analysis. This review both identifies issues AND fixes them.

## Phase 1: Identify Scope

Determine what to review:

```bash
git diff --stat
git diff
```

If no git changes, review files the user specified or most recently modified files.

## Phase 2: Security Check (CRITICAL — must fix before merge)

Review ALL changed files for these security issues. Any finding here blocks the review:

- [ ] No hardcoded secrets (API keys, passwords, tokens, connection strings)
- [ ] No SQL injection (string concatenation in queries → use parameterized queries)
- [ ] No command injection (unsanitized input passed to shell commands)
- [ ] No XSS vulnerabilities (unescaped user input rendered in HTML)
- [ ] Input validation on all user-facing endpoints
- [ ] No path traversal risks (user-controlled file paths → validate and sanitize)
- [ ] Authentication and authorization checks present on protected routes
- [ ] Sensitive data not logged or exposed in error messages

If ANY security issue is found, report it immediately as **[CRITICAL]** and fix it before proceeding.

## Phase 3: Launch Three Review Agents in Parallel

Use the `task` tool to launch all three agents concurrently in a single message. Use `subagent_type: "review"` for all three.

**CRITICAL**: You MUST include the full diff output from Phase 1 in each agent's prompt. Sub-agents cannot run `git diff` themselves (they may not have bash access or may be in a different working directory). Copy-paste the diff into each agent's prompt text. Also include the list of changed file paths (absolute paths) so agents can `read_file` to explore further.

### Agent 1: Code Reuse Review

1. **Search for existing utilities and helpers** that could replace newly written code. Look in utility directories, shared modules, and files adjacent to the changed ones.
2. **Flag any new function that duplicates existing functionality.** Suggest the existing function.
3. **Flag inline logic that could use an existing utility** — hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards.

### Agent 2: Code Quality Review

1. **Redundant state**: state duplicating existing state, cached values that could be derived
2. **Parameter sprawl**: adding new parameters instead of restructuring
3. **Copy-paste with variation**: near-duplicate code blocks → unify with shared abstraction
4. **Leaky abstractions**: exposing internal details, breaking abstraction boundaries
5. **Stringly-typed code**: raw strings where constants/enums/typed alternatives exist
6. **Dead code**: unused imports, commented-out blocks, unreachable branches
7. **Complexity**: functions >50 lines, nesting >4 levels, bare except/catch
8. **Naming**: unclear variables, misleading function names, magic numbers without constants

### Agent 3: Efficiency Review

1. **Unnecessary work**: redundant computations, repeated file reads, duplicate API calls, N+1 patterns
2. **Missed concurrency**: independent operations running sequentially
3. **Hot-path bloat**: blocking work added to startup or per-request paths
4. **No-op updates**: state updates in loops that fire unconditionally
5. **TOCTOU**: pre-checking existence before operating (operate directly, handle error)
6. **Memory**: unbounded data structures, missing cleanup, listener leaks
7. **Overly broad operations**: reading entire files when a portion suffices

## Phase 4: Aggregate and Fix

Wait for all three agents. Aggregate findings. Fix each issue directly:
- If a finding is a false positive, note it and skip — do not argue with the finding.
- For each fix, verify it doesn't break existing functionality.

## Phase 5: Report

### 1. Summary
One paragraph overview of code quality and readiness.

### 2. Issues Found
List each issue with severity and location:
- **[CRITICAL]** `file.py:42` — Description of the security/correctness issue
- **[HIGH]** `file.py:87` — Description of the quality issue
- **[MEDIUM]** `file.py:123` — Description of the improvement
- **[LOW]** `file.py:156` — Minor style or readability note

### 3. Issues Fixed
List what was fixed in this review pass (with file:line references).

### 4. Positive Observations
Note what was done well (good patterns, clean abstractions, thorough error handling).

### 5. Suggestions
Non-blocking improvements for future consideration.

### 6. Rating
**X/10** — with brief justification:
- 9-10: Production-ready, well-tested, no issues
- 7-8: Good quality, minor issues only
- 5-6: Functional but needs improvements before production
- 3-4: Significant issues that must be addressed
- 1-2: Major security or correctness problems

## Feedback Refinement

If the user provides feedback on review findings:
1. Re-examine the specific areas mentioned
2. Search for additional evidence supporting or refuting the feedback
3. Update the review with revised findings
4. Apply fixes if the feedback identifies real issues
