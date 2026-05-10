---
name: reflexion
description: Use when a draft analysis, code-review, plan, or written response needs a quality lift before delivery. Runs a 3-pass critique-refine-judge loop on the draft to surface gaps and tighten reasoning.
triggers: /reflexion
auto_trigger: false
---

# Reflexion — Self-Refinement Loop

Use this skill when you have produced a **draft** (code review, plan, analysis, written response, design doc) and want a second pass to surface gaps before delivering to the user. Based on the **Reflexion** pattern from the context-engineering literature: structured self-critique improves output quality more reliably than re-prompting.

## When to use

- After producing a code review with **>3 findings** and you suspect some are weak.
- After writing a multi-section design doc or plan and you want a sanity check.
- After producing an answer where the user's stake is high (e.g. claim assessment, audit report) and a single-pass response feels under-cooked.
- When the user explicitly says "please double-check" or "review your own work".

## When NOT to use

- For one-line answers, factual lookups, or simple confirmations — the loop overhead isn't worth it.
- For tasks where the user has already iterated with you 3+ rounds — they've effectively done reflexion themselves.
- When token budget is tight (this skill triples LLM calls for the same task).

## The 3-pass loop

### Pass 1 — Critique your own draft

Take the draft you produced. Step outside the writer's voice and put on a critic's hat. Generate a `CRITIQUE` block that lists, for each section of the draft:

- **Specifics that are wrong** (factual errors, broken file:line references, unsupported claims) — cite evidence.
- **Specifics that are weak** (hedging, hand-waving, "it depends" without explaining when) — cite the exact phrase.
- **Specifics that are missing** (gaps in the analysis, edge cases not considered, alternative interpretations) — name the gap.

Strict rule: every critique line must point at **a specific phrase or section** of the draft. No generic "could be tighter" — that's not actionable.

### Pass 2 — Refine the draft

Apply each `CRITIQUE` line as a concrete edit. Output a `REFINED` block that is the draft, rewritten section-by-section, addressing the critique. If a critique line says "X is wrong", the refined version corrects X. If it says "Y is missing", the refined version adds Y. If a critique line points at hedging, the refined version commits or removes the claim.

Strict rule: do NOT add NEW content beyond what the critique called for. Refinement is a focused edit, not a rewrite from scratch.

### Pass 3 — Judge: refined vs original

Compare `REFINED` to the original draft. Output a `JUDGEMENT` block that answers:

1. **Did refinement actually improve the output?** Yes / No / Marginal — with one-sentence reason.
2. **Are there critique points that the refinement DIDN'T fully address?** List them.
3. **Should we go around the loop again?** Yes / No — only Yes if the answer to #1 is "Marginal" AND the answer to #2 is non-empty.

If `JUDGEMENT` says "go again", run pass 1-3 once more on the refined draft. **Maximum two iterations** — diminishing returns kick in fast and token cost compounds.

## Output format

Three labelled blocks, in order. Final delivery to user is the last `REFINED` block.

```
=== CRITIQUE ===
- [section-X] specific weakness, with evidence: "<quoted phrase from draft>"
- [section-Y] missing: <what's not there>
- ...

=== REFINED ===
<the draft, rewritten>

=== JUDGEMENT ===
Improved: yes/no/marginal — <one-sentence reason>
Unaddressed critique points: <list or "none">
Loop again: yes/no — <reason>
```

## Cost note

This skill **triples** the LLM cost for the source task (1 draft + 1 critique + 1 refine + 1 judge ≈ 3-4x base). Only invoke when the quality lift justifies the spend. For routine code review on small diffs, prefer `/code-review` directly.

## Pairs well with

- **`/code-review`** — produce the draft review with `/code-review`, then run `/reflexion` to tighten.
- **`/clara-review`** — for ClaRA Phase 5 synthesis where output goes to non-technical stakeholders, reflexion catches hedging that would confuse them.
- **`/design`** — after producing 2-3 design options, reflexion can surface which option's tradeoffs were under-analysed.
