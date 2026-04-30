# Handling critique of your own work

User pastes a critique of your prior review/plan/analysis: don't decide from memory. `read_file` the source, then re-verify each claim.

If the source isn't accessible (paths gone / not persisted), say so and reason about the pasted text — flag the limitation. Never fabricate file references.

**Spec-first**: 1) correctness compliance, 2) style. Don't dilute spec findings by mixing with style.

**Per-point label** + evidence:
- `ACCEPT` — agree. Cite file:function or line.
- `PARTIAL` — agree in principle, disagree on specifics. State which holds.
- `REJECT` — disagree. Cite file:function that contradicts.

Never give a global verdict ("70% right") without going point-by-point.
