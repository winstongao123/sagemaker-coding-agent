# Block E+F Prompts

Date: 2026-05-04

## Iter1

Prompt path: `compact_v5/_status/v5_completion_audit/prompts/block-e-f-claude-review-iter1.md`

Status: saved, ready to send to Claude.

This prompt embeds `CLAUDE_REVIEWER_BASE_PROMPT.md`, requires Claude to read
canonical context from disk first, and requires Block E+F reconstruction from
`SYNTHESIS_MASTER.md` before trusting worker context.

Required invocation: clear `ANTHROPIC_API_KEY` only for the Claude subprocess
and use `--setting-sources user`.

## Iter2

Prompt path: `compact_v5/_status/v5_completion_audit/prompts/block-e-f-claude-review-iter2.md`

Status: saved, ready to send to Claude.

Purpose: re-review after automatic fixes for Claude iter1 LOW findings on
EF-3 signature-stripping breadth and EF-5 multi-tool generation event coverage.
The prompt embeds `CLAUDE_REVIEWER_BASE_PROMPT.md` and again requires
canonical disk-first scope reconstruction from `SYNTHESIS_MASTER.md`.
