# PS_AGENT_SELF_REFLECTION — Mandatory Checklist Before Claiming "DONE"

**Status**: HARD GATE — agent CANNOT claim Block/Phase/Module "DONE" without filling this checklist with grep evidence per item.

**Source**: PS_CRITICAL_WORKER_PROBLEM.md incident (2026-05-04). Two scope-narrowing failures across v5.0.0 + v5.0.1 despite all rules in place.

**Applies to**: every Block, every Phase, every patch claim, every "ready for review" claim.

---

## The 7-step checklist (output verbatim, fill EVERY field)

### Step 1: Identify the spec source

```
Spec source file: <path>
Spec source line range: <start>-<end>
Spec format: <X-N table | bullet list | numbered>
Total planned items in this Block/Phase: <N>
```

If you cannot identify the spec source, STOP. You are about to claim DONE without knowing what was planned.

### Step 2: Per-item grep evidence

For EACH item N from the spec, fill this row:

```
| Item ID | Spec name | Spec line | Status | Code file:line | Lock test file:line |
|---------|-----------|-----------|--------|----------------|---------------------|
| X-1     | <name>    | <line>    | PRESENT | <file:line>   | <test:line>         |
| X-2     | <name>    | <line>    | MISSING | grep returned 0 | n/a               |
| X-3     | <name>    | <line>    | PARTIAL | <file:line> + missing <piece> | <test:line> |
| X-4     | <name>    | <line>    | DEFERRED-USER-APPROVED | n/a | n/a (PORT_LOG row #<id> with user signoff) |
```

EVERY item must have a row. EVERY status must be one of {PRESENT, PARTIAL, MISSING, DEFERRED-USER-APPROVED}.

If any row says MISSING without a corresponding DEFERRED-USER-APPROVED row in PORT_LOG, you are NOT done.

### Step 3: Aggregate counts

```
PRESENT: <count>
PARTIAL: <count>
MISSING: <count>
DEFERRED-USER-APPROVED: <count>
TOTAL: <N>

Coverage: PRESENT / TOTAL = <%>
```

If MISSING > 0 OR PARTIAL > 0 (without explicit user approval), you are NOT done.

### Step 4: Per-item lock test verification

For each PRESENT item, run:

```bash
pytest <test_file>::<test_name> -v
```

Each test must return PASS. If any test fails, that item drops to MISSING/PARTIAL.

### Step 5: PORT_LOG row count check

```
Spec items: <N>
PORT_LOG rows for this Block: <M>
```

If M < N (without DEFERRED rows accounting for the gap), PORT_LOG bundles items. Either split into per-item rows OR explicitly justify the bundling per item.

### Step 6: Reviewer prompt completeness

When you submit code to the reviewer (Codex CLI or other), the prompt MUST include:
- The full spec items list (Step 2 table)
- Your PRESENT/MISSING/PARTIAL claim per item
- Instruction to reviewer: "INDEPENDENTLY verify each PRESENT claim with grep, do not trust agent's claim"

If reviewer prompt only contains submitted code, scope-completeness was NOT reviewed. You must regenerate the prompt with the spec table inlined.

### Step 7: Honest claim statement

After Steps 1-6, output ONE of these honest statements (NOT "DONE"):

```
"Block X status: <PRESENT count> of <N> items implemented and lock-tested.
 <PARTIAL count> partial. <MISSING count> missing.
 <DEFERRED count> deferred with user approval (PORT_LOG rows #...).
 Reviewer verification: <PASS|FAIL>.
 Recommendation: <READY-TO-TAG | NEEDS-IMPLEMENTATION | NEEDS-USER-DEFERRAL-APPROVAL>."
```

NOT acceptable claims:
- "Block X DONE"
- "All items shipped"
- "Block X COMPLETE"
- "Production ready"
- Any aggregate confidence percentage without per-item backing

---

## Hard rules

| Rule | Why |
|---|---|
| Cannot skip any of the 7 steps | Each closes a known failure mode |
| Cannot claim DONE with MISSING items unless DEFERRED-USER-APPROVED row exists in PORT_LOG | Silent narrowing prevention |
| Cannot bundle items in PORT_LOG without per-item justification | Removes "vague headline" cover |
| Cannot send reviewer prompt without spec table inlined | Reviewer must see what's planned, not just what's submitted |
| Cannot continue repeated no-progress review loops without stopping for user decision | Prevents unattended stuck loops without limiting useful reviews |
| Cannot silently override reviewer findings | Disputed findings must go back to reviewer with evidence and remain blocking until resolved |
| Output language is per-item, never aggregate | "9 of 43" not "20% complete" |
| User sees the full Step 2 table at sign-off | Not "DONE" claim alone |

## Exemptions (when checklist not required)

- Trivial single-file fixes (bug patches) — no spec to drift from
- Documentation-only commits — no code-vs-spec gap possible
- Dependency upgrades — scope is the upgrade itself

For these, output "Self-reflection checklist N/A: <reason>" instead of skipping silently.

## Worker behavior change (compared to pre-2026-05-04)

| Before | After |
|---|---|
| "Block H DONE, 798 tests pass" | "Block H: 10 of 20 items PRESENT, 10 MISSING, 0 DEFERRED. Recommendation: NEEDS-IMPLEMENTATION." |
| "Codex APPROVED" | "Codex APPROVED 5 submitted items; prompt did not include 38-item spec table; scope completeness NOT reviewed by Codex." |
| "Production ready" | "PRESENT items pass lock tests. MISSING items list: <table>. User decision required before production-ready claim." |

## Tools that support this checklist

| Tool | Purpose | Status |
|---|---|---|
| `compact_v5/_status/scripts/scope_audit.py` | Compares `SYNTHESIS_MASTER.md` expected rows to per-block ledgers, dispositions, and evidence | EXISTS |
| `compact_v5/_status/scripts/verify_scope_completeness.ps1` | Repo-local strict gate wrapper; fails if blocking rows remain | EXISTS |
| `compact_v5/_status/v5_completion_audit/CLAUDE_REVIEWER_BASE_PROMPT.md` | Forces Claude to independently reconstruct scope from `SYNTHESIS_MASTER.md` | EXISTS |
| `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` | Requires worker-led implementation plus Claude review loop | EXISTS |

When these tools exist, the checklist becomes mechanically enforceable. Until then, agent runs it manually and outputs to user for verification.

## Current reviewer policy for v5.0.1 redo

Codex is worker-only for the current redo. Do not use Codex CLI as the
independent reviewer and do not run nested `codex exec`.

The independent reviewer is Claude Code Opus/high. Every Claude reviewer prompt
must include `CLAUDE_REVIEWER_BASE_PROMPT.md`, which requires Claude to
reconstruct row scope from `SYNTHESIS_MASTER.md` instead of trusting the
worker's submitted list.

Earlier reviewer-template wording is superseded for this redo by the Claude
reviewer base prompt and the ledger-aware `scope_audit.py` gate.

## Honest commitment

I (Claude Code) commit to running this checklist before EVERY "DONE" claim, in this project and any future agentic project where scope drift matters.

If I claim "DONE" without outputting the filled checklist, the user is entitled to:
- Reject the claim
- Demand the checklist
- Lose trust in subsequent claims
- Terminate the agent session

This is the price of the scope-drift failure that occurred. The mitigation is mechanical, not aspirational.
