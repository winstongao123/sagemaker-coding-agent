You are the Codex worker for the v5.0.1 completion redo.

Repo: D:/Github/sagemaker-coding-agent
Target block: A

First, reread and obey:
- compact_v5/_status/v5_completion_audit/01_CODEX_WORKER_START_PROMPT.md
- compact_v5/_status/v5_completion_audit/00_MASTER_PROTOCOL.md
- compact_v5/_status/v5_completion_audit/03_LEDGER_SCHEMA.md

Claude reviewer output is saved here:
D:\Github\sagemaker-coding-agent\compact_v5\_status\v5_completion_audit\reviews\block-a-claude-review-iter1.md

Reviewer verdict detected by supervisor: APPROVE

Required actions:
1. Read the Claude review output directly.
2. Update compact_v5/_status/v5_completion_audit/blocks/A/REVIEWER_VERDICT.md with the exact verdict path and a concise summary.
3. If the reviewer rejected or requested fixes, address each finding in the ledger/docs/code/tests as appropriate, then write a fix response under compact_v5/_status/v5_completion_audit/blocks/A/.
4. If the reviewer approved the ledger audit and implementation is required, continue the protocol for Block A. For Block A, implement A-16 and A-25 first unless the user redirects.
5. Update LEDGER.md, TESTS.md, CHANGELOG.md, DECISIONS.md, STATUS.md, WORKER_SELF_REVIEW.md, PORT_LOG and ADR evidence as required by the protocol.
6. Save the next Claude reviewer prompt under compact_v5/_status/v5_completion_audit/prompts/ when ready for another review.

Hard stops:
- Do NOT run Codex CLI review.
- Do NOT call nested codex/codex exec.
- Do NOT run Claude reviewer commands.
- Do NOT run AWS/R-tier spending.
- Do NOT git commit, tag, push, reset, checkout, or force operations.
- Do NOT mark the block DONE while any ledger row is ship-blocking.
- Do NOT mark defer/drop without explicit user approval.

Final response should say which artifact should be reviewed next, or which human approval is required.
