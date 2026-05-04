# Folder Map

Status: ACTIVE
Created: 2026-05-04

This is the clean map for `compact_v5/_status/v5_completion_audit/`.

```text
sagemaker-coding-agent/
  AGENTS.md
v5_completion_audit/
  README.md
  STATUS.md
  00_MASTER_PROTOCOL.md
  03_LEDGER_SCHEMA.md
  04_COMMANDS.md
  06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md
  CLAUDE_REVIEWER_BASE_PROMPT.md
  PS_WORKER_REVIEWER_DECISION.md
  PS_COMPACTION_RESUME_CHECKLIST.md
  claude-reviewer-settings.json
  TEST_CASE_PREP.md
  ../PS_AGENT_SELF_REFLECTION.md
  ../scripts/scope_audit.py
  ../scripts/verify_scope_completeness.ps1
  blocks/
  ledger/
  logs/
  prompts/
  reviews/
  PS_CLI_WOKER_DESIGN/
    LEARNING_FACTORY_ADAPTATION.md
    PROGRESS_VISIBILITY.md
    CLAUDE_REVIEWER_AUTH.md
    WORKER_REVIEWER_TRANSCRIPT_RULE.md
    GIT_CHECKPOINT_POLICY.md
```

## Active Entrypoints

| Path | Use |
|---|---|
| `../../../AGENTS.md` | Repo-level Codex instructions |
| `README.md` | Human orientation |
| `STATUS.md` | Current state and next action |
| `04_COMMANDS.md` | Commands to start/monitor the process |
| `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` | Prompt for the Codex worker |
| `CLAUDE_REVIEWER_BASE_PROMPT.md` | Mandatory base for every Claude review |
| `PS_WORKER_REVIEWER_DECISION.md` | Worker/reviewer pairing decision and flow |
| `PS_COMPACTION_RESUME_CHECKLIST.md` | Resume/pickup checklist after compaction or interruption |
| `_status/PS_AGENT_SELF_REFLECTION.md` | Mandatory checklist before done/ready claims |
| `_status/scripts/scope_audit.py` | Mechanical row-scope audit |
| `_status/scripts/verify_scope_completeness.ps1` | Strict wrapper for scope audit |
| `PS_CLI_WOKER_DESIGN/` | Reusable design and recovery notes |
| `PS_CLI_WOKER_DESIGN/LEARNING_FACTORY_ADAPTATION.md` | Learning Factory rules translated to this Codex/Claude workflow |
| `PS_CLI_WOKER_DESIGN/PROGRESS_VISIBILITY.md` | Required worker heartbeat cadence and fields |
| `PS_CLI_WOKER_DESIGN/CLAUDE_REVIEWER_AUTH.md` | Ensures Claude reviewer uses subscription auth, not inherited API-key credits |
| `PS_CLI_WOKER_DESIGN/WORKER_REVIEWER_TRANSCRIPT_RULE.md` | Requires every worker/reviewer prompt, response, log, verdict, and heartbeat to be saved |
| `PS_CLI_WOKER_DESIGN/GIT_CHECKPOINT_POLICY.md` | Requires specific-file commit and push after each clean block close |

## Evidence Folders

| Path | Use |
|---|---|
| `blocks/` | Per-block ledgers, statuses, tests, verdicts, self-reviews |
| `prompts/` | Exact prompts sent to worker/reviewer |
| `reviews/` | Exact Claude review outputs |
| `logs/` | Command stderr/stdout logs |
| `ledger/` | Cross-block review matrices and ledger summaries |

## Removed From Active Workflow

The abandoned supervisor and old prompt files were removed from the active
folder. Historical artifacts may still mention them because those artifacts are
kept as evidence of what happened.
