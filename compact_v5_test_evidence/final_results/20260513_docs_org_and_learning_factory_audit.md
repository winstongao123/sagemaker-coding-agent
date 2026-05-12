# Docs, Organization, And Learning Factory Audit

Date: 2026-05-13

Scope:
- `D:\Github\sagemaker-coding-agent`
- `D:\Github\sagemaker-coding-agent\compact_v5`
- `D:\Github\sagemaker-coding-agent\compact_v5_test_evidence`
- `D:\Github\Learning_Factory`

## Answer

The v5 source and local evidence are much better organized than before, but the
repo documentation still had two active drift hazards:

1. Root `CLAUDE.md` still described v4.3.2 as the current product.
2. Root `AGENTS.md` pointed Codex at `compact_v5/_status/v5_completion_audit/`,
   but that active path is absent from the current `compact_v5` tree. Copies
   exist under `compact_v5_test_evidence/`, which makes them evidence archives,
   not the live control surface.

Those two issues explain how an agent with "learning factory" instructions can
still drift: the agent can load an instruction surface, but the surface itself
may be stale or point to archived paths.

## Current Organization State

Clean active surfaces:
- `compact_v5/AGENT_STATUS.md`
- `compact_v5/chat.md`
- `compact_v5/memory.md`
- `compact_v5/docs/V5_KNOWLEDGE_INDEX.md`
- `compact_v5_test_evidence/final_results/learning_archive_20260513/`

Messy but intentionally preserved evidence:
- `compact_v5_test_evidence/final_results/` still contains many raw reports,
  reviews, logs, and older result files.
- Those originals should stay in place because older review/status links point
  at them.
- The learning archive is the curated pickup surface for humans and future
  agents.

Runtime-source hygiene:
- `compact_v5/` still has local runtime/debug folders such as `.sageagent_state`,
  `audit_logs`, `sessions`, caches, and `__pycache__` in the working tree.
- The ship zip excludes those. They are not package leaks.
- For normal project use, v5 should write project evidence to
  `<project>/compact_v5_wip/`, not into the runtime source folder.

Package truth:
- `compact_v5_ship.zip` contains the runtime package plus root
  `chat.md`, `AGENT_STATUS.md`, and `memory.md`.
- The zip currently does not contain `docs/`. Older wording that implied
  `docs/htmls/V5_DESIGN_OVERVIEW.html` ships in the zip was doc drift.

## Why Drift Happened Despite Learning Factory

Learning Factory's core rules are sound:
- goals live in files;
- one agent, one job, one output;
- always know what is done and not done;
- remote agents need exact input/output boundaries;
- skills are better than giant always-loaded memories for procedural lessons.

But those rules do not help when the current repo bootstrap is stale. Drift can
still happen for five reasons:

1. Instruction load mismatch: Claude, Codex, v5, and notebook runtime may each
   load different files depending on cwd and launch method.
2. Stale canonical docs: root `CLAUDE.md` and `AGENTS.md` can confidently point
   to old or missing control files.
3. Scattered evidence: raw reports are useful for traceability, but without a
   curated index an agent may follow an old branch of history.
4. Prose-only rules: if a rule is not enforced by code, tests, package checks,
   or UI behavior, a model can forget it under context pressure.
5. Oversized memory: too much durable instruction can add token cost and create
   conflicts. A long "factory setting" is not automatically better.

## Does v5 Need Learning Factory Settings?

Yes, but only in a smaller and more disciplined form.

Do not remove Learning Factory principles. Convert them into:
- short bootstrap docs that name the active files;
- project-local status and evidence folders;
- compact memory for stable facts;
- skills for repeatable procedures;
- runtime code/tests for critical invariants;
- package verification for release truth.

Do not use Learning Factory as a huge always-loaded prompt dump. The right model
is "small operating contract plus enforced behavior."

## Why Codex Worked Without A Factory Setting

Codex did not work because durable learning is unnecessary. It worked because
this session had:
- explicit current user direction;
- direct file-system inspection;
- repo-aware tests and diffs;
- frequent status checks;
- a strong external tool discipline;
- current context loaded in the active conversation.

Codex can drift too if it starts from stale docs or skips verification. The fix
is not "no learning factory"; the fix is accurate active docs plus enforcement.

## Changes Made In This Audit

- Replaced root `CLAUDE.md` with a current v5-oriented bootstrap.
- Replaced root `AGENTS.md` with a current Codex bootstrap that no longer points
  at missing `compact_v5/_status/...` paths.
- Added `compact_v5/docs/V5_KNOWLEDGE_INDEX.md`.
- Updated `compact_v5/chat.md` to clarify package contents and link the index.
- Updated `compact_v5/AGENT_STATUS.md` and `compact_v5/memory.md` with this
  audit conclusion.

## Independent Review Follow-Up

Claude CLI subscription review:
- `compact_v5_test_evidence/final_results/20260513_docs_org_learning_factory_claude_review.md`

Review found one real medium issue outside the original doc-only scope:
`DurableStateManager` could prefer a newly created WIP scaffold over existing
legacy root `AGENT_STATUS.md` / `memory.md`. That would make the documentation
claim about legacy fallback incomplete.

Fix applied:
- `runtime/workspace.py` now exposes preferred legacy-aware status/memory path
  helpers that fall back to root legacy files when the WIP file is only the
  default scaffold.
- `runtime/state.py` and `agent.py` use those helpers.
- `tests/test_workspace_evidence_layout.py` locks the durable-state fallback.
- `.gitignore` now ignores `.sageagent_state/` directories.
- stale `.sageagent_state` dirs under the repo root and `compact_v5/` were
  swept.

Verification after follow-up:
- `py -3.10 -m pytest tests -q` from `compact_v5/` -> 64 passed.
- `py -3.10 -m pytest compact_v5\tests -q` from the repo root -> 64 passed
  after fixing cwd-coupled notebook tests.
- The notebook rerun test now locks the safer current widget contract: direct
  `launch_ui(use_widgets=True)` and no `clear_output` / `sys.modules.pop`.
- `compact_v5_ship.zip` rebuilt with 155 members, `testzip() None`, no
  forbidden members.

## Recommendation

Keep the repo as two layers:

1. Active v5 pickup layer:
   `CLAUDE.md`, `AGENTS.md`, `compact_v5/AGENT_STATUS.md`, `chat.md`,
   `memory.md`, and `docs/V5_KNOWLEDGE_INDEX.md`.
2. Historical evidence layer:
   `compact_v5_test_evidence/`, especially the curated
   `learning_archive_20260513/`.

Future agents should begin with the active pickup layer and consult historical
evidence only when a current file points to a specific report.
