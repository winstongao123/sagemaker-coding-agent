# Block B Decisions

Date: 2026-05-04

## ADR

- ADR-050: Block B token accounting completion-audit redo.

## Adaptations

- B-2: Kept the Bedrock-applicable Haiku fallback subset in `core/compactor.py`. Runnable's token-search field stripping is not active in the v5.0.1 Bedrock-only token-count fallback path.
- B-9: Adapted `finalContextTokensFromLastResponse` to Bedrock top-level `usage` by using input plus cache-read plus cache-creation tokens.
- B-10: Kept the configured v5 Bedrock pricing rows for Haiku 4.5 and Sonnet 4.5, plus the existing 3.5 baseline compatibility row. The canonical row names Sonnet 4.6, but current v5 runtime config and entrypoint expose Sonnet 4.5 and no Sonnet 4.6 model id; ADR-050 documents this exact runtime constraint.
- B-15: The plan labeled ContextManager as already present, but the current `core/budget.py` only had `IterationBudget`. The redo added the v4-compatible `ContextManager` surface instead of preserving a false-positive doc-only claim.
- B-16: The lorem generator is scoped under `tests/utils` as a local test utility, not production runtime, matching the canonical row's context-window testing purpose.

## Explicit Non-Actions

- No AWS/R-tier spend.
- No Codex review or nested `codex exec`.
- No git tag or final-ready approval.
