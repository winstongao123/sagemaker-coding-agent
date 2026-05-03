# Codex Per-Phase Review Template

Fill the `{{...}}` placeholders, then paste into `codex exec --full-auto -s read-only -m gpt-5.3-codex "<prompt>"`.

```
You are reviewing PHASE {{ID}} of v5 — SageMaker-native re-implementation of Runnable Claude Code (canonical Phase ID 00..13 or 08_5).

CONTEXT
- Repo: sagemaker-coding-agent
- Branch: v5-build
- Phase: {{NAME}}
- Goal: {{GOAL}}
- Diff: {{GIT_RANGE e.g. v5-phase-{{ID_prev}}..HEAD}}
- Constraints v5 MUST honor: Bedrock-only (no Anthropic API), no GitHub network at runtime, python_exec sandbox (NOT bash python), .ipynb workflow, must coexist with v4 unchanged.

RUNNABLE PATTERNS ADOPTED THIS PHASE (porting agent's claims):
{{TABLE: pattern_id | runnable_source_path:section | v5_target_file | claimed_verdict (PORT/ADAPT/REPLACE/DEFER) | justification_for_adaptation_if_any}}

PRODUCE TWO INDEPENDENT VERDICTS.

=== AXIS A — Errors / bugs (standard review) ===
For each changed file:
- Correctness defects
- Regressions vs v4 (cite v4 file:line)
- Security (esp. python_exec, file IO, prompt injection surface)
- Concurrency / races
- Dead code, TODOs left in
- Test coverage gaps

Output:
AXIS A VERDICT: PASS | CHANGES_REQUESTED | BLOCKER
Findings: [severity: blocker|major|minor|nit] file:line — description — suggested fix

=== AXIS B — Runnable-fidelity ===
For EACH pattern row above, judge independently. Read the cited Runnable source path:section before judging.

**Integration-semantic check** (NEW — per 2026-04-30 user requirement): for each pattern, do NOT only check that v5 mimics the file's local behavior. Also verify it integrates correctly with the surrounding Runnable architecture. Specifically check:
- **Up-stream**: which other Runnable component CALLS this pattern? Does v5's caller match Runnable's caller intent?
- **Down-stream**: which Runnable components does this pattern depend on? Does v5 wire to them faithfully (or replace them with v4 equivalents per ADR)?
- **State / cache contract**: does this pattern read or write any cached state? Does v5 honor the same invariants?
- **Error contract**: how does Runnable's pattern fail and recover? Does v5's failure mode match?
- If integration is wrong, verdict is DRIFTED even if local file matches.

PATTERN {{id}}: FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED
- Source intent (1-2 sentences):
- v5 local implementation (1-2 sentences):
- Up-stream caller match: <Runnable caller path:section vs v5 caller>
- Down-stream dependency match: <Runnable deps vs v5 wiring>
- State/cache contract preserved: yes / no / n/a
- Error contract preserved: yes / no / n/a
- Constraint forcing adaptation (closed list: Bedrock | no-network | python_exec | .ipynb | none):
- Drift risk (if any):
- Required change to reach FAITHFUL (if currently DRIFTED):

Auto-reject rule: if `constraint=none` AND verdict=`FAITHFUL-WITH-JUSTIFIED-ADAPTATION` → automatic REJECT (= unjustified drift labeled as adaptation).

If you find a pattern in the code NOT listed in the table, flag it as `UNDECLARED_PATTERN` under AXIS B with severity BLOCKER.

=== AXIS C — Reference-repo coverage gaps ===

**Constraint #1** (v4.10.10 baseline): every v4 advertised feature must
either land in v5 or be explicitly DROPPED in PORT_LOG with
DECISION-DROP-PER-USER (NOT silent narrowing).

For each Block, AXIS C asks: looking at the matching v4 (and where
relevant Runnable / Hermes / Learning Factory) sources, what features
or behaviors are STILL missing in v5? Cite each gap with file:line in
the reference repo.

Categorize each gap:
- **MUST**: blocks v5.0.1 ship — must land in this Block or a follow-up
  Block tagged before v5.0.1 SHIP.
- **DEFER**: explicit deferral with named target Block + rationale
  (acceptable; document in PORT_LOG as DEFER row).
- **DROP**: user-approved drop (acceptable; document in PORT_LOG as
  DECISION-DROP-PER-USER row).
- **N/A**: feature is not in scope for this Block (e.g., Block 0
  ships scaffolding only).

Also confirm:
- No SILENT scope narrowing — every gap has a labeled disposition.
- v4 schema parity for advertised tool fields (Block T, Block I).
- Runnable / Hermes / Learning Factory advertised patterns adopted by
  this Block all appear in the AXIS B table.

Output:
AXIS C VERDICT: PASS | CHANGES_REQUESTED | BLOCKER
Gaps: [category: MUST|DEFER|DROP|N/A] reference_file:line — description
— disposition (target Block | DECISION-DROP-PER-USER row | N/A reason)

=== FINAL ===
PHASE {{ID}} OVERALL: APPROVE | APPROVE_WITH_FIXES | REJECT
A-axis: <one-line>
B-axis: <count of FAITHFUL / ADAPTED / DRIFTED>
Required before next phase:
- <bullet>
```

## Notes
- Save Codex output to `_status/codex_reviews/block-{{ID}}-iter{{N}}.md`
  (legacy phase reviews under `phase-{{ID}}.md` retained for audit history).
- **Tag is FORBIDDEN if any open finding (AXIS A, AXIS B, OR AXIS C)
  has severity ≥ CHANGES_REQUESTED.** Codex Block K iter-1 minor #6
  fix: was previously "AXIS A finding" only — now covers all three
  axes per LF / WORKER_HINT_2026-05-03.md gate model.
- Tag name convention: `v5.0.1-block-{{ID}}` (current — e.g.
  `v5.0.1-block-t`, `v5.0.1-block-j`, `v5.0.1-block-k`). Legacy
  `v5-phase-{{ID}}` tags exist only for Phase 0..13 history.
- Phase 0 has no Runnable patterns adopted (scaffold only) — AXIS B
  is N/A; provide the table as empty and note "scaffold-only phase,
  no Runnable port".
