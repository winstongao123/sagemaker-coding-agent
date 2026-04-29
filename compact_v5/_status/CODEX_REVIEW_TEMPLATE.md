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

=== FINAL ===
PHASE {{ID}} OVERALL: APPROVE | APPROVE_WITH_FIXES | REJECT
A-axis: <one-line>
B-axis: <count of FAITHFUL / ADAPTED / DRIFTED>
Required before next phase:
- <bullet>
```

## Notes
- Save Codex output to `_status/codex_reviews/phase-{{ID}}.md`.
- Do NOT tag `v5-phase-{{ID}}` if any AXIS A finding ≥ CHANGES_REQUESTED is unresolved.
- Phase 0 has no Runnable patterns adopted (scaffold only) — AXIS B is N/A; provide the table as empty and note "scaffold-only phase, no Runnable port".
