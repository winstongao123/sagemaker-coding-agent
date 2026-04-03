# [CRITICAL] V4 Sub-Agent Usage + Code Quality — Learned from Runnable

**Date**: 2026-04-03
**Priority**: CRITICAL — affects code writing quality, false claims, and verification
**Version**: V4.3.3

---

## 12 Gaps Found (5 CRITICAL, 4 MAJOR, 3 MODERATE)

### Implemented (Tier 1 — Highest ROI)

| # | Gap | What Runnable Has | What V4 Added | Severity |
|---|-----|------------------|--------------|----------|
| 1 | **False-claims prevention** | Explicit: never claim tests pass when they fail, never suppress failures, never manufacture green results | Added full false-claims language to system prompt | CRITICAL |
| 2 | **Mandatory verification after 3+ edits** | "Non-trivial implementation requires independent adversarial verification before reporting completion" | Added: "After 3+ file edits: spawn verify sub-agent before reporting completion" | CRITICAL |
| 3 | **Agent-specific when-to-use** | Per-agent criteria: explore (thoroughness levels), verify (3+ edits), plan (step-by-step + critical files) | Added per-agent guidance in task tool description | CRITICAL |
| 4 | **Explore thoroughness levels** | "quick/medium/very thorough" — LLM specifies depth | Added to explore agent description in task tool | MAJOR |
| 5 | **Prompt-writing guidance** | Concrete bullets: explain what/why, what you've ruled out, include file paths | Added to task tool description | MAJOR |
| 6 | **Minimal-edit principle** | "A bug fix doesn't need surrounding code cleaned up" | Added to Doing Tasks section | MAJOR |
| 7 | **Pre-completion verification** | "Before reporting complete, verify it works: run the test, check output" | Added to Doing Tasks section | MAJOR |
| 8 | **Don't peek at running agents** | "Don't read fork output mid-flight — defeats context isolation" | Added to Sub-agent Coordination | MODERATE |
| 9 | **Query-count threshold** | "Use explore agent only when task requires 3+ queries" | Added: "<3 queries use grep directly" | MODERATE |

### Acknowledged (Not Implemented — Architectural Gaps)

| # | Gap | Why Not Implemented |
|---|-----|-------------------|
| 10 | Fork vs Fresh decision tree | V4 has no fork mechanism (no git worktree). Would need architecture change. |
| 11 | Foreground vs background execution | V4 sub-agents always run foreground. Background would need threading changes. |
| 12 | Plan agent 5-step workflow | Current plan mode works. Structured output adds complexity without proven benefit. |

---

## System Prompt Changes

### Added to "# Doing Tasks":
```
- MINIMAL EDIT PRINCIPLE: A bug fix doesn't need surrounding code cleaned up.
- Before reporting complete, VERIFY it works: run the test, check output.
- Report outcomes FAITHFULLY: never claim tests pass when they fail.
  Never suppress failing checks. Never characterize incomplete work as done.
- After 3+ file edits: spawn verify sub-agent before reporting completion.
```

### Added to "# Sub-agent Coordination":
```
- Use task for 3+ queries or multi-file. Use grep directly for <3 queries.
- Verify is MANDATORY after 3+ file edits.
- Explore: specify thoroughness (quick/medium/very thorough).
- Don't peek at running sub-agent output. Wait for completion.
```

### Updated task tool description:
- Agent-specific when-to-use with evidence thresholds
- Explore thoroughness levels
- Prompt-writing bullets (explain what/why, what you've ruled out)
- "NEVER delegate understanding" with concrete anti-pattern examples

---

## Impact

These changes affect:
1. **Code writing quality** — minimal-edit principle prevents over-engineering
2. **Reliability** — mandatory verification catches bugs before user sees "done"
3. **Trust** — false-claims prevention stops manufactured green results
4. **Efficiency** — query-count threshold prevents unnecessary sub-agent spawning
5. **Codebase learning** — thoroughness levels let user control exploration depth

---

*Tagged [CRITICAL] because false claims and missing verification directly harm user trust and code quality.*
