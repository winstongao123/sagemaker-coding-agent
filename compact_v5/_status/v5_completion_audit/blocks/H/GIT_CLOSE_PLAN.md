# Block H Git Close Plan

Status: PENDING_CLAUDE_REVIEW
Date: 2026-05-05

Do not commit/push Block H until:

1. `scope_audit.py --block H --strict` passes.
2. Claude returns a usable row-by-row verdict for H-1 through H-20.
3. Remaining ship-blocking rows are 0.
4. Any Claude findings are fixed and re-reviewed if needed.

Specific-file candidate list:

- `compact_v5/MAIN/agent/memory/extract.py`
- `compact_v5/MAIN/agent/memory/session_memory.py`
- `compact_v5/MAIN/agent/memory/compact.py`
- `compact_v5/MAIN/agent/memory/context.py`
- `compact_v5/MAIN/agent/memory/__init__.py`
- `compact_v5/MAIN/agent/prompt/__init__.py`
- `compact_v5/MAIN/agent/agent.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_h.py`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/`
- `compact_v5/_status/v5_completion_audit/prompts/block-h-claude-review-iter*.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-h-claude-review-iter*.md`
- `compact_v5/_status/v5_completion_audit/logs/block-h-*.log`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`

Exclude unrelated dirty files and do not force push or tag.
