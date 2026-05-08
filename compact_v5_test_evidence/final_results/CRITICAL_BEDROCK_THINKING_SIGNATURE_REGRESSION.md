# Critical Bedrock Thinking Signature Regression

Date: 2026-05-08

## User-visible failure

A simple second-turn question failed in SageMaker with:

```text
ValidationException: messages.1.content.0.thinking.signature: Field required
```

## Root cause

v5 parsed Bedrock `thinking` output as display text only and discarded the model-supplied `signature`. The next turn rebuilt assistant history as:

```python
{"type": "thinking", "thinking": "..."}
```

That shape is invalid for Bedrock extended thinking. If a thinking block is replayed, Bedrock requires the original signed block.

## Why prior tests missed it

Earlier tests covered:

- thinking config is sent;
- thinking metrics/UI are visible;
- count-token uses thinking settings;
- one-turn reasoning visibility.

They did not cover the critical two-turn replay path: model returns signed thinking on turn 1, v5 stores assistant history, then Bedrock receives that history on turn 2. That is why the bug survived until an actual interactive session with thinking enabled.

## Fix

- Preserve signed thinking blocks on parse.
- Replay only signed thinking blocks.
- Never synthesize unsigned thinking from display-only text.
- Defensively sanitize old unsigned thinking blocks before Bedrock chat and token-count calls.
- Drop thinking blocks entirely when retrying on a fallback model, because signatures are model-bound.

## Regression proof

Local zero-cost regression command passed:

```text
thinking_signature_fix_local_tests: PASS
```

The proof checks signed preservation, unsigned omission, old-history sanitization, and fallback stripping.

## Required future coverage

Any future thinking/reasoning acceptance test must include at least two turns with real assistant history replay, not just a one-turn smoke.

## Post-review cleanup

Claude's first review approved the fix and noted that `count_tokens` computed `uses_thinking` from raw messages before sanitization. v5 now sanitizes first, then decides whether the token-count request needs thinking config. This makes chat and count-token paths share the same signed-thinking invariant.
