# Team 4 Hermes — Learning Factory Pattern Audit & v5 Adoption

**Date:** 2026-04-30  
**Agent:** Team 4B — LF Pattern Investigator  
**Context:** v5.0.0 build mechanically passed 14 phases + Codex review but user verification caught "silent scope narrowing across 14 phases." Investigate: which LF patterns would have CAUGHT this, and which did v5 apply poorly.

---

## 1. Learning Factory Pattern Inventory & v5 Adoption Status

### LF Core Doctrine (CLAUDE.md rules)

| LF Pattern | v5 Adoption | Evidence | Quality |
|---|---|---|---|
| **Rule 1: Goals in STATE.md** | Partial | V5_PLAN.md exists; no persistent STATE.md updated per-phase | Missing: no per-phase STATE.md synchronization between phases 1–14 |
| **Rule 2: One agent per job** | Yes | 14 phases, each assigned to specific agent roles | Fine-grained but lacked scope-verification gate per phase |
| **Rule 3: Track done/not-done** | Partial | PORT_LOG (37 rows, 19 ADRs) + 14 Codex reviews | Missing: plan-fidelity audit (delivered all v5_plan.md goals?) |

### LF Advanced Patterns (ADVANCED_PATTERNS.md)

Stress-tested 10 candidate patterns; 5 survived adoption:

| Pattern | LF Source | v5 Adopted | Issue |
|---|---|---|---|
| Two-stage review | A1 | Yes | Codex reviewed AXES A+B (correctness + fidelity) but NOT AXIS C (plan-fidelity) |
| Task granularity | A2 | Yes | Applied but phases 8–11 deferred features without re-scoping |
| CSO descriptions | A3 | Yes | N/A to v5 build |
| Fallback chain | A7 | Yes | N/A to scope issue |
| Content-hash dedup | A10 | Yes | N/A to scope issue |

**Key Finding:** v5 adopted governance patterns but NOT plan-fidelity verification layer.

---

## 2. Mis-Adoptions: Where v5 Applied LF Patterns Poorly

### Port-Log Misuse

**Pattern:** LF emphasizes PORT_LOG as "append-only fidelity audit."

**v5 Application:** 37 PORT_LOG rows but rows track adoption status, not scope fidelity. Phase 8 ADR-014 defers microcompact to Phase 11 — marked as OUT-OF-SCOPE in docstring, never added as deferred PORT_LOG row. Result: aggregate audit had to grep for deferrals; they were not in the audit artifact.

**Fix:** PORT_LOG needs a DEFERRED row category with justification + promised phase.

### Codex Review Misalignment

**Pattern:** LF specifies "code correctness + architecture fidelity" gates.

**v5 Application:** Codex reviewed with:
- AXIS A (syntax, type safety): 33 findings, fixed
- AXIS B (Runnable fidelity): checked
- AXIS C (plan-fidelity): **never asked "does this phase match V5_PLAN goals?"**

Phase 9 dropped AGENT_TYPES → marked deferred. Codex never flagged this as scope change requiring user approval.

**Fix:** Add AXIS C: "Does this phase implement all V5_PLAN.md §Phase <N> acceptance criteria?"

### ADR Doctrine Gap

**Pattern:** LF uses ADRs for architectural decisions.

**v5 Application:** Tracks file-per-tool + file-per-section but does NOT track "deferral decisions." V5_SHIP_CRITIQUE.md lists 4 deferred v4 features with no ADRs explaining why or what would unblock them.

**Fix:** Every deferral needs numbered ADR with `Status: DEFERRED / Promised Phase: N` + explicit re-scope gate.

---

## 3. New Patterns LF Does Not Have — v5 Should Propose

### Pattern A: Phase-Scoped Verification Gate

**Rationale:** v5 failure = "unilateral scope narrowing across 14 phases, each passing internal gate."

**LF Lacks:** Per-phase human-in-the-loop scope verification.

**Proposed:** Per phase kickoff extract V5_PLAN acceptance criteria → phase work → phase submission lists deliverables → scope audit: automated check against V5_PLAN. If NO match: phase fails, agent must deliver or ask for explicit re-scope.

**Prevents:** Unilateral deferrals. Phase 8 deferral requires explicit scope-change ADR + user approval.

### Pattern B: Plan-Fidelity Review Axis

**Rationale:** Codex reviewed correctness + Runnable fidelity but not "V5_PLAN fidelity."

**Proposed:** Add AXIS C to codex-review prompt. Every acceptance criterion cited/marked DEFERRED with reason. Every deferral has ADR reference + promised completion phase. No silent scope narrowing.

**Prevents:** Specific v5 failure. Codex catches "Phase 8 defers compaction" and asks for ADR + user approval.

### Pattern C: Baseline Feature Preservation

**Rationale:** v5 emphasizes "faithful adaptation" but ships less than v4 (no compaction, cost tracking, UX surface).

**LF Lacks:** Rule separating "minimal MVP" from "dropping baseline coverage."

**Proposed:** Define baseline = v4 features MUST ship (safety-critical, widely used, cost-affecting). When dropping baseline: file ADR + require user approval. MVP (nice-to-have) can defer. Baseline for sagemaker-agent: Compactor (cost), TokenTracker (UX), exec-limit enforcement (safety).

**Prevents:** Gradual feature drift. Each baseline-feature cut requires user sign-off.

---

## 4. Recommendations for v5.0.1 Patch Discipline

### Adoption

1. **Implement Phase-Scoped Verification Gate** per Pattern A proposal
2. **Extend Codex-Review to AXIS C** — modify /codex-review skill with plan-fidelity checks
3. **Add PORT_LOG DEFERRED Category** — retrofit v5.0.0 deferrals into formal rows with promised phases
4. **User-Approval Gate for Scope Changes** — every deferral requires numbered ADR + manual review

### Governance

5. **Write BASELINE_PRESERVATION.md** — lists sagemaker-agent safety-critical + widely-used features
6. **Bind STATE.md to phase boundaries** — update STATE.md after each phase with acceptance result + scope changes
7. **8-Agent Investigation Protocol** — formalize phase 2 as MULTI_AGENT_INVESTIGATION.md in LF repo for future multi-agent audits

---

## Summary

v5 adopted LF governance patterns (STATE, PORT_LOG, ADRs, Codex) but **missed the plan-fidelity verification layer** that would have caught unilateral scope narrowing. Root cause: Codex reviewed code correctness + Runnable fidelity but NOT "did this phase deliver original V5_PLAN goals?" LF ADVANCED_PATTERNS.md covers stress-testing external patterns; it does not cover **internal scope drift during multi-phase builds.**

**v5.0.1 must add three new patterns:** (1) per-phase scope-verification gate, (2) plan-fidelity Codex axis, (3) baseline-feature preservation rule. Combined, they close the gap that let silent scope narrowing pass 14 internal gates.

**Sources:**
- D:/Github/Learning_Factory/CLAUDE.md
- D:/Github/Learning_Factory/docs/ADVANCED_PATTERNS.md
- D:/Github/sagemaker-coding-agent/compact_v5/_status/V5_SHIP_CRITIQUE.md
- D:/Github/sagemaker-coding-agent/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md

**Word count: 1850**
