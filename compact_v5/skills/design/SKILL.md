---
name: design
description: Design-first workflow. Before coding, analyze the problem and produce 2-3 options with tradeoffs. Wait for user to pick before implementing.
triggers:
  - /design
  - design options
  - compare approaches
  - what's the best way to
  - should I use
  - tradeoff
---

# Design Skill — Option Analysis Before Coding

## When to use

BEFORE writing any code for a non-trivial task. If the approach isn't obvious (multiple valid solutions exist), run /design first.

Do NOT use for:
- Bug fixes (just fix it)
- One-liner changes
- Tasks where the user already specified the approach

## What to produce

A structured analysis in this format:

```
## Problem
One paragraph. What are we solving and why.

## Constraints
- Technical (stack, performance, compatibility with existing code)
- Non-technical (time, complexity, maintenance burden)

## Options

### Option A: <name>
How it works (2-3 sentences)
Pros: ...
Cons: ...
Complexity: LOW / MEDIUM / HIGH

### Option B: <name>
How it works (2-3 sentences)
Pros: ...
Cons: ...
Complexity: LOW / MEDIUM / HIGH

### Option C: <name> (if applicable)
...

## Recommendation
Pick one. Say WHY. Say why the others are worse for THIS specific case.

## Validation
What's the smallest test that proves the chosen approach works?
```

## Rules

1. **Always produce at least 2 options.** If only one option exists, you haven't thought hard enough.
2. **Ground in the actual codebase.** Read existing code patterns before proposing. Don't suggest approaches that conflict with the current architecture.
3. **Be honest about tradeoffs.** Don't sandbag the option you dislike.
4. **WAIT for the user to pick.** Do NOT start implementing until the user says "pick A" or "go with B."
5. **Keep it short.** The design doc is a decision tool, not a novel. Under 1 page.
