# Worker Prompt - compact_v5 S3 Real-Use Fix Plan

Date: 2026-05-11
Branch: `v5-build`
Active runtime tree: `compact_v5/`
Ship zip: `compact_v5.zip`

## Mission

Fix the remaining compact_v5 real-use blockers found from the user transcript:

`list file and bucket structure of my s3`

The previous UI live-supervisor work is **not enough**. It fixed live streaming
and some card rendering, but this S3 session still exposed open blockers:

1. thinking block in the wrong place;
2. tool cards not collapsed/grouped;
3. task drift from S3 inventory to compact_v5 source-tree inventory;
4. wrong self-diagnosis of the sandbox as Bedrock-only;
5. broken/contradictory S3 read path;
6. high cost from blocked retries, verbose output, tool_search overhead, and
   Thinking ON in the deployed run.

Authoritative diagnostic docs:

- `compact_v5_test_evidence/compact_v5/docs/PS_PS_FINAL_TEST_v3_REAL_USE_ISSUES.md`
- `compact_v5_test_evidence/compact_v5/docs/PS_PS_FINAL_TEST_v3_UI_ISSUES.md`
- `compact_v5_test_evidence/final_results/S3_REAL_USE_DIAGNOSTIC_CONSOLIDATED_20260511.html`

## Non-negotiable Rules

- Work only from the active flattened tree: `compact_v5/`.
- Do **not** recreate or depend on `compact_v5/compact_v5/`.
- Preserve v5 architecture. No broad rewrites.
- Before each block, run `git status --short --branch`.
- After each block, save:
  - the block prompt,
  - the exact git diff,
  - test output,
  - Claude independent review prompt,
  - Claude independent review output.
- Claude must review each block independently using subscription auth, not API
  credit/token auth.
- If Claude returns REQUEST_CHANGES or finds a HIGH/MEDIUM runtime issue,
  fix and re-review that block before moving on.
- Do not mark solved until the proof gate for that row passes.
- Rebuild `compact_v5.zip` after runtime/status changes and verify it.
- Commit and push only scoped changes. Do not stage unrelated local noise.

## Claude CLI Subscription Protocol

Use the installed Claude Code CLI:

```powershell
$claude = "C:\Users\winst\AppData\Roaming\npm\claude.cmd"
Test-Path $claude
& $claude --version
```

Run Claude with subscription/user settings and with API-token routes cleared:

```powershell
$env:ANTHROPIC_API_KEY = $null
$env:CLAUDE_CODE_USE_BEDROCK = $null
& $claude `
  --setting-sources user `
  --permission-mode dontAsk `
  -p "@compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_NAME_claude_review_prompt.md" `
  > compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_NAME_claude_review.md `
  2> compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_NAME_claude_review.err.log
```

Do **not** set `ANTHROPIC_API_KEY`. If Claude says `Credit balance is too low`,
you accidentally used an API-token route. Stop and rerun with the environment
cleared as above.

Claude is an independent reviewer. Do not ask Claude to rubber-stamp. Give it
the architecture context, the diff, the tests, and ask for an explicit verdict:

- `APPROVE`
- `APPROVE_WITH_NITS`
- `REQUEST_CHANGES`
- `BLOCKED`

## Review Artifact Directory

Create:

```text
compact_v5_test_evidence/final_results/s3_real_use_reviews/
```

For every block, save:

```text
BLOCK_NAME_worker_prompt.md
BLOCK_NAME_diff.patch
BLOCK_NAME_tests.log
BLOCK_NAME_claude_review_prompt.md
BLOCK_NAME_claude_review.md
BLOCK_NAME_claude_review.err.log
BLOCK_NAME_status.md
```

## Block 0 - Preflight / Drift Baseline

Goal: prove the starting point before code changes.

Steps:

1. Run `git status --short --branch`.
2. Confirm active files exist:
   - `compact_v5/ui/chat_ui.py`
   - `compact_v5/tools/python_exec.py`
   - `compact_v5/security/dangerous_patterns.py`
   - `compact_v5/security/manager.py`
   - `compact_v5/prompt/`
   - `compact_v5/core/query_engine.py`
3. Grep and save evidence:
   - thinking rendering in `chat_ui.py`;
   - tool card rendering in `chat_ui.py`;
   - `linecache`, `boto3`, `aws_bedrock_only`, `aws s3`;
   - final-claim/evidence guard logic;
   - tool deferral and `list_dir`.
4. Do not change source in Block 0.
5. Ask Claude to review whether the planned block order is scoped and safe.

Proof gate:

- Claude understands active tree `compact_v5/`.
- Claude confirms no stale nested-path assumption.
- Baseline artifacts are saved.

## Block 1 - S3 Safe-Read Path

Goal: one allowed path must be able to list S3 buckets/prefixes when
`CONFIG.aws_bedrock_only=False`.

Preferred fix shape:

- Add a dedicated safe read-only S3 tool such as `aws_s3_list`.
- It should support:
  - list buckets;
  - list first-level prefixes/objects for a bucket;
  - optional prefix;
  - limit/max items;
  - no delete/admin/write operations.
- Keep it small and explicit. Do not expose general AWS CLI.
- If using boto3, fix sandbox imports only as needed and prove it does not open
  dangerous AWS services.

Allowed files:

- `compact_v5/tools/`
- `compact_v5/security/`
- `compact_v5/prompt/security.md`
- tests under `compact_v5/tests/`

No-touch unless Claude approves the need:

- `compact_v5/core/query_engine.py`
- `compact_v5/agent.py`
- `compact_v5/runtime/bedrock_client.py`

Tests:

- Unit test safe S3 tool with a fake boto3/client object.
- Test Bedrock-only ON blocks non-Bedrock AWS access.
- Test destructive S3/API operations are not exposed.
- Test the blocked `aws s3` CLI guidance points to the safe tool, not generic
  broken Python fallback.

Proof gate:

- In mock/local tests, the safe S3 path lists buckets/prefixes.
- In real SageMaker/AWS smoke, the user prompt can list S3 structure without
  attempting blocked `aws s3`.
- Claude independently approves the tool/security boundary.

## Block 2 - Accurate Sandbox Diagnosis

Goal: the agent must not claim Bedrock-only when Bedrock-only is OFF.

Fix shape:

- Add prompt/runtime guidance so restriction apologies name the actual blocker:
  bash allowlist, Python import sandbox, Bedrock-only, approval, or missing AWS
  permissions.
- Consider a small deterministic helper for formatting restriction causes
  rather than relying on the model to infer.

Tests:

- Simulate blocked `aws s3` while `CONFIG.aws_bedrock_only=False`; expected
  diagnosis mentions bash/security allowlist, not Bedrock-only.
- Simulate Python sandbox import failure; expected diagnosis mentions Python
  sandbox/import allowlist.

Proof gate:

- Transcript-style smoke does not contradict the status bar.
- Claude approves no prompt drift or over-broad security claims.

## Block 3 - Intent Drift Guard

Goal: fallback choices must stay anchored to the original user request.

Fix shape:

- Add a low-cost deterministic or optional guard before final answers:
  "Does this answer address the original/current user intent?"
- For the S3 transcript, if the fallback only lists local directories, final
  answer must say it did **not** answer S3 and must offer the next S3-relevant
  step.
- Prefer local deterministic checks where possible. Avoid adding a new LLM call
  on every turn unless gated/configured.

Tests:

- Transcript replay:
  1. user asks S3 structure;
  2. S3 path blocked;
  3. user picks local fallback;
  4. final answer must be labeled partial/not-S3, not presented as the S3
     answer.
- Existing final-claim/evidence guard tests still pass.

Proof gate:

- The S3 fallback transcript no longer drifts.
- Claude approves the guard does not create broad new cost or behavior drift.

## Block 4 - Tool Cards Collapse / Grouping

Goal: tool calls/results should be visible but not noisy.

Current correction:

- A `tool` role already exists in `compact_v5/ui/chat_ui.py`.
- Do **not** re-add it.
- Fix default-collapsed rendering and grouping.

Fix shape:

- Render tool body inside closed `<details>` or a Jupyter-safe equivalent.
- Summary should show tool name, phase, status, short preview, and maybe output
  size.
- Group call requested + result by `tool_use_id` where available.
- For parallel dispatch, show a compact parent summary such as
  "Ran 3 read-only commands in parallel" with nested tool cards.

Tests:

- HTML fixture/smoke verifies tool cards are collapsed by default.
- Tool result still accessible when expanded.
- Parallel grouped output does not dump six raw rows.

Proof gate:

- Screenshot or rendered HTML evidence saved.
- Claude approves no regression to live streaming/subagent visibility.

## Block 5 - Thinking Placement / Collapse

Goal: reasoning/thinking should not appear as plain text after metrics.

Current correction:

- Source constructor default is `thinking_enabled=False`.
- The user run showed Thinking ON; diagnose config/session/deployed zip before
  changing defaults again.

Fix shape:

- Move captured thinking out of the metrics footer.
- Preferred: separate collapsed reasoning/audit row or collapsed panel above
  the metrics strip.
- If Jupyter strips `<details>`, use an ipywidgets-safe toggle fallback.

Tests:

- HTML fixture/smoke verifies thinking is not below metrics.
- Thinking is collapsed by default or hidden behind a toggle.
- Assistant answer body remains clean.

Proof gate:

- Screenshot or rendered HTML evidence saved.
- Claude approves placement and no markdown regression.

## Block 6 - Cost Controls For Simple Inventory Tasks

Goal: the same S3 inventory task should avoid obvious waste.

Fix shape:

- One-strike rule: if a tool returns blocked/not allowed, do not retry the same
  tool shape.
- Short blocked-error summaries in UI and model-visible history.
- Suppress large follow-up menus unless user asks for options.
- Measure Thinking ON source: config, session restore, notebook widget, or user
  toggle. Do not blindly flip defaults if source is already OFF.
- Measure `tool_search` tax for common tools before changing deferral.

Tests/measurements:

- Replay blocked AWS shape and confirm no repeated `aws s3` retry.
- Token/call estimate before/after for S3-style prompt.
- Prompt metrics before/after if deferral changes.

Proof gate:

- Same task has fewer calls and shorter output in mock replay.
- No security regression.
- Claude approves cost controls are scoped and not hiding needed evidence.

## Block 7 - Final Integration / Zip / Real AWS Smoke

Steps:

1. Run focused tests for each block.
2. Run all relevant smoke tests.
3. Rebuild `compact_v5.zip` from `compact_v5/`.
4. Verify zip:
   - `zipfile.testzip() is None`;
   - required members present;
   - forbidden folders absent: tests, `.sageagent_state`, `_status`, `MAIN`,
     `compact_v5_test_evidence`, `__pycache__`;
   - required member hashes match source.
5. Run real SageMaker/AWS S3 smoke if credentials/permissions are available.
6. Save final SPEC vs SHIPPED table.
7. Run final independent Claude review over the complete diff, tests, zip
   verification, and real/mocked S3 evidence.

Final proof gate:

- Every block review is `APPROVE` or `APPROVE_WITH_NITS` with no unresolved
  HIGH/MEDIUM issue.
- Final Claude review says `SHIP DECISION: APPROVE`.
- Git contains the final source/docs/zip changes.
- User-facing final status clearly says what is solved and what, if anything,
  remains environment-dependent.

## Independent Claude Final Review Prompt Skeleton

Use this structure for each block and the final review:

```text
You are an independent reviewer for compact_v5, a SageMaker notebook coding
agent. You are not the implementer.

Active tree: compact_v5/
Do not assume compact_v5/compact_v5/ exists.

Architecture context:
- compact_v5/ui/chat_ui.py owns notebook UI rendering/live output.
- compact_v5/tools/ owns tool schemas/executors.
- compact_v5/security/ owns command and Python sandbox policy.
- compact_v5/core/query_engine.py owns LLM/tool loop, final-claim guard, and
  tool_search deferral.
- compact_v5/agent.py is the public Agent wrapper.
- compact_v5.zip is built from the flattened compact_v5/ tree.

User-visible failure being fixed:
[paste exact block failure]

Files changed:
[list]

Diff:
[paste or reference BLOCK_NAME_diff.patch]

Tests/evidence:
[paste or reference BLOCK_NAME_tests.log]

Review tasks:
1. Check if this fixes the stated failure.
2. Check architecture drift, security regression, prompt/cache/token bloat, UI
   regression, and zip/deployment risk.
3. Check whether the proof gate is satisfied.
4. Return one verdict only:
   APPROVE, APPROVE_WITH_NITS, REQUEST_CHANGES, or BLOCKED.
5. List HIGH/MEDIUM/LOW findings with file/line references where possible.
```
