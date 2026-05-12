# Worker Prompt - Fix compact_v5 S3 Follow-Up Tool Discipline

You are working in:

```text
d:/Github/sagemaker-coding-agent
branch: v5-build
```

Goal: fix compact_v5 so S3 follow-up requests behave like a careful human
operator. v5 already has a working read-only `aws_s3_list` path. The new
problem is over-scanning and poor follow-up discipline after S3 data is already
known.

Read first:

```text
compact_v5_test_evidence/final_results/S3_FOLLOWUP_TOOL_DISCIPLINE_ISSUES_20260512.md
compact_v5_test_evidence/final_results/s3_followup_tool_discipline_reviews/PLAN_REVIEW_CLAUDE_REREVIEW2.md
compact_v5/tools/aws_s3_list.py
compact_v5/core/parallel_dispatch.py
compact_v5/core/query_engine.py
compact_v5/prompt/tool_classes.md
compact_v5/ui/chat_ui.py
compact_v5/runtime/state.py
compact_v5/runtime/config.py
compact_v5/tools/v4_documents.py
```

If the final plan-review file is absent on first worker run, read the latest
`PLAN_REVIEW_CLAUDE*.md` in the same review folder after running Block 0.

Reference behavior from the failing transcript:

```text
User: pick two fiels to invesagte adn tell me hwat you found
Bad v5 behavior: fired 6 aws_s3_list calls and effectively rescanned S3.
Correct behavior: reuse the recent S3 inventory, pick two known object paths,
preview/investigate only those two if safe, and explain findings.
```

## Hard Rules

- Do not rewrite the agent architecture.
- Do not add destructive S3 operations.
- Do not use `aws` CLI as the primary path.
- Do not use API-token Claude review. Use Claude CLI subscription auth only.
- Do not touch unrelated dirty files.
- Do not claim "all files" or "complete" if any S3 listing is truncated.
- Do not create user deliverables inside the v5 runtime folder by default.
- Preserve v4-style UI behavior and current passing tests.

## Required Blocks

### Block 0 - Preflight / Drift Check

1. Run `git status --short`.
2. Confirm active source tree is `compact_v5/`.
3. Confirm current zip name is `compact_v5_ship.zip`.
4. Record unrelated dirty paths and leave them untouched.
5. Run current focused tests once:

```powershell
py -3.10 -m pytest compact_v5\tests -q
```

Save output under:

```text
compact_v5_test_evidence/final_results/s3_followup_tool_discipline_reviews/
```

Run Claude review for this block before editing.

### Block 1 - S3 Follow-Up Reuse Guard

Implement a minimal mechanism so recent S3 inventory evidence can be reused on
follow-up prompts. The agent should recognize follow-ups like:

```text
pick two files to investigate
choose two from those
look at two of the listed files
show relationship here
```

Do not treat "where is the file?" as an S3 follow-up. That is an artifact
memory question and belongs to Block 5.

Acceptance:

- At turn start, extract recent `aws_s3_list` object paths from a bounded
  window of `self.messages` and inject a compact reminder for S3 follow-ups.
  Use the last 6 user/assistant turns or about 8 KB of recent tool-result text,
  whichever is smaller. Prefer this minimal QueryEngine-side context over
  broad new durable state in this block.
- Mark any injected reminder ephemeral, using the existing ephemeral-block
  pattern, so it does not bloat persisted session history.
- If recent S3 object paths exist, choose from them before calling
  `aws_s3_list`.
- If no object paths exist, ask a clarifying question or list only the narrow
  relevant prefix.
- Add a regression test for this exact transcript shape.

### Block 2 - S3 Fanout Cap

Prevent broad S3 rescan for narrow follow-ups.

Important: this is not a parallel-dispatch bug. `aws_s3_list.requires_approval`
is true, so it already routes sequentially. The failure is that the model emits
many distinct `aws_s3_list` tool uses in one assistant turn, and the existing
dedup only drops identical `(name, args)` duplicates. Do not fix this by only
changing `is_concurrency_safe`.

Acceptance:

- Add a per-turn same-name cap/throttle for `aws_s3_list`, independent of
  parallel-dispatch flags. The cap is 2 `aws_s3_list` calls per
  `QueryEngine.run` user turn; the counter resets at the start of the next user
  turn.
- After the cap, return a synthetic tool result with this meaning:

```text
Blocked: too many aws_s3_list calls this turn. Reuse prior S3 results or ask for a narrower prefix.
```

- `aws_s3_list` must not rescan many buckets unless the user explicitly asks
  for a full refresh or full inventory.
- For "pick two files", at most 1-2 S3 calls are allowed, and zero is preferred
  if prior object paths are available.
- Add a focused test around dispatch/planning or a transcript replay.

### Block 3 - Safe `aws_s3_preview` Tool

Add a read-only S3 object preview tool.

Requirements:

- Name: `aws_s3_preview`.
- Inputs: `bucket`, `key`, optional `max_bytes` default around 8192 and hard
  cap around 65536.
- Read-only only.
- Respect `CONFIG.aws_bedrock_only`.
- Use S3 Range reads, not full-object reads:

```python
get_object(Range=f"bytes=0-{max_bytes-1}")
```

- Refuse or summarize safely for binary/unsupported content.
- Return metadata: bucket, key, bytes read, content type if available,
  truncated true/false.
- Register it as always loaded, mirroring `aws_s3_list`, so S3 follow-ups do
  not pay a `tool_search` round trip.
- Update any always-loaded tool registry/snapshot tests so `aws_s3_preview`
  joins `aws_s3_list` in the expected set.

Acceptance:

- Can preview small `.txt`, `.csv`, `.json`, `.md` objects in tests using a
  fake S3 client.
- Large object returns a bounded truncated preview.
- Binary object does not dump bytes into chat.

### Block 4 - Truncation Truth Gate

Prevent false "all/complete" claims when S3 listing output is truncated.

Acceptance:

- If any `aws_s3_list` result contains a continuation token or truncation
  marker, final answer must say "partial/truncated" unless continuation was
  consumed to completion.
- Enforce this near the final-text claim gate, mirroring the existing
  `_intent_drift_guard` / final-claim guard style in
  `compact_v5/core/query_engine.py`. The tool already emits truncation text;
  the gap is the model's summary claim.
- Detection should read recent tool-result text for signals such as
  `output truncated at` or a continuation-token instruction. If the model has
  consumed continuation to completion, the guard should not force "partial".
- Add regression tests for both sides: a truncated result must block
  "all/complete" wording, and a continuation consumed to completion must not
  be falsely marked partial.

### Block 5 - Workspace and Artifact Policy

Fix the file-location behavior exposed by the transcript.

Acceptance:

- Change only the default write location for newly created user deliverables
  such as Markdown, Word, Excel, PDF, notebooks, charts, reports, and generated
  diagrams.
- Do not relocate runtime/audit/state roots such as `audit_dir`,
  `.sageagent_state`, `.snapshots`, `.code_index`, `truncated_outputs`,
  `.exec_budget.json`, or session paths.
- Default user deliverables must not be written into the v5 runtime folder
  (`/home/sagemaker-user/compact_v5_ship/`, `compact_v5/`, or the package
  root).
- Add an explicit user-artifacts root, for example
  `CONFIG.user_artifacts_root = /home/sagemaker-user/sageagent_workspace`.
  Include that root in the path-validation allowed paths at startup so
  `_validate_doc_path` / `_path_validation.validate_path(...)` still pass.
- Parameterize tests so they work on Windows dev paths and SageMaker Linux
  paths; do not hardcode only `/home/sagemaker-user/...`.
- Rebase only newly created user deliverable paths to `user_artifacts_root`
  when no project workspace has been chosen. Do not rebase runtime state,
  audit, snapshots, sessions, or security files.
- If the user has not chosen a project workspace, default to a clear user
  workspace such as:

```text
/home/sagemaker-user/sageagent_workspace
```

- UI Workspace field must show the effective workspace.
- Created reports/artifacts must be tracked in state/session so "where is the
  file?" answers from recorded artifact state, not `tool_search`, `list_dir`,
  or broad file search. Recommended shape: add
  `DurableStateManager.append_artifact(...)` and expose a compact recent
  artifact reminder to the agent.
- Add tests.

### Block 6 - ASCII Contract

Honor explicit ASCII-only requests.

Acceptance:

- Enforce only when the user request contains an explicit ASCII directive.
- Define ASCII as every byte `< 0x80`.
- If user asks for ASCII diagram, generated diagram/report contains only ASCII
  bytes: no emoji, no Unicode arrows, no box drawing.
- Recommended enforcement: prompt rule plus a post-write validator in the
  relevant write/report path when an `ascii_only=True` hint is active.
- Add test.

### Block 7 - Status-Doc Guard

Prevent simple non-project tasks from editing `AGENT_STATUS.md`.

Acceptance:

- S3 inventory/report prompt must not edit `AGENT_STATUS.md` unless a concrete
  heuristic passes:
  - user explicitly mentions status/progress or asks to keep status updated;
  - the task is a long-running coding/project task;
  - `iter_used > 15`;
  - project-source writes exceed 3 files.
- Long-running coding tasks still keep `AGENT_STATUS.md` updated.
- Re-check any UI guidance that mentions `AGENT_STATUS.md`; prompt-side guard
  is the source of truth, and UI text must not nudge status updates for small
  read-only/report tasks.
- Add test.

### Block 8 - Tool ID UI Polish

Hide raw `toolu_bdrk_...` IDs by default.

Acceptance:

- Normal tool card summary is readable to nontechnical users.
- Raw id remains available only inside details/debug text. Keep `tool_use_id`
  in metadata so grouping, resume, and tests still work.
- Update any existing UI snapshot/smoke test that asserted the summary line
  contained `id toolu_bdrk_...`.
- Add/update UI smoke test.

### Block 9 - Cost Proof and Final Integration

Run a before/after-style replay or mock transcript showing:

- "pick two files" no longer rescans all buckets.
- Thinking remains OFF for simple S3 follow-up unless user enabled it.
- Calls are bounded.
- Output is concise.
- Existing tests still pass.
- `compact_v5_ship.zip` rebuilt and verified.
- Zip verification must include size, member count, SHA256, `testzip()`, and
  required-member presence for the flat ship zip.

## Claude CLI Review Instructions

Use Claude CLI with subscription auth, not API-token auth.

PowerShell command pattern:

```powershell
$env:ANTHROPIC_API_KEY=$null
Get-Content -Raw .\compact_v5_test_evidence\final_results\s3_followup_tool_discipline_reviews\BLOCK_N_prompt.md | claude -p
```

For each block:

1. Save the worker prompt:

```text
compact_v5_test_evidence/final_results/s3_followup_tool_discipline_reviews/BLOCK_N_prompt.md
```

2. Save the code diff:

```powershell
git diff -- compact_v5 > compact_v5_test_evidence/final_results/s3_followup_tool_discipline_reviews/BLOCK_N.diff
```

3. Run Claude review using the subscription command above.
4. Save output:

```text
compact_v5_test_evidence/final_results/s3_followup_tool_discipline_reviews/BLOCK_N_claude_review.md
```

5. If Claude says `REQUEST_CHANGES`, fix and run a re-review:

```text
BLOCK_N_claude_rereview.md
```

Do not proceed to the next block until Claude returns literal `APPROVE`.

## Final Deliverables

Update:

```text
compact_v5/AGENT_STATUS.md
compact_v5/memory.md
memory.md
compact_v5/chat.md
compact_v5_test_evidence/final_results/S3_FOLLOWUP_TOOL_DISCIPLINE_ISSUES_20260512.md
compact_v5_test_evidence/final_results/FUTURE_SOFTWARE_DEVELOPMENT_LESSONS_20260511.md
compact_v5_test_evidence/final_results/V5_PRODUCTION_TEST_READINESS_20260512.md
compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md
```

Run:

```powershell
py -3.10 -m py_compile compact_v5\ui\chat_ui.py compact_v5\agent.py compact_v5\core\query_engine.py compact_v5\tools\aws_s3_list.py
py -3.10 -m pytest compact_v5\tests -q
```

Rebuild and verify:

```text
compact_v5_ship.zip
```

Final answer must include:

- SPEC vs SHIPPED table.
- Tests/checks run.
- Claude review table with paths and verdicts.
- Zip size, member count, SHA256, `testzip`.
- Any unresolved risks.
