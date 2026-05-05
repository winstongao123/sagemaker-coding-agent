# Block D Git Close Plan

Commit only D-owned files after Claude approval and final tests:

- `compact_v5/CHANGELOG.md`
- `compact_v5/MAIN/agent/commands.py`
- `compact_v5/MAIN/agent/runtime/slash_args.py`
- `compact_v5/MAIN/agent/skills/manager.py`
- `compact_v5/MAIN/agent/skills/init/SKILL.md`
- `compact_v5/MAIN/agent/skills/init-verifiers/SKILL.md`
- `compact_v5/MAIN/agent/skills/skillify/SKILL.md`
- `compact_v5/MAIN/agent/tests/integration/test_block_d.py`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/D/`
- `compact_v5/_status/v5_completion_audit/prompts/block-d-claude-review-iter*.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-d-claude-review-iter*.md`
- `compact_v5/_status/v5_completion_audit/logs/block-d-*`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`

Do not stage unrelated dirty files listed in `BASELINE.md`. Do not use
`git add -A`, force push, tags, AWS/R-tier, Codex review, or nested `codex exec`.
