# v5 Completion Audit Status

Date: 2026-05-04
Current state: WORKER-LED LOOP ACTIVE; BLOCK A, E+F, L, N, K, T, AND C CLOSED/PUSHED; NEXT BLOCK B; R-TIER TEST SPECS MATERIALIZED

## Baseline

| Item | Value |
|---|---|
| Branch | `v5-build` |
| Current HEAD when setup started | `c256d07` |
| Codex CLI | `codex-cli 0.128.0` worker-only; not reviewer |
| Claude CLI | `2.1.126 (Claude Code)`; subscription path validated as `claude-opus-4-7` after unsetting `ANTHROPIC_API_KEY` for the process |
| Claude hooks | User-level hooks include Codex gate/review hooks; reviewer commands must temporarily clear `ANTHROPIC_API_KEY` and use `--setting-sources user` plus `claude-reviewer-settings.json` so Claude Code uses subscription auth instead of API credits |
| Existing dirty items before setup | `_archive/compare_code/gg-claude-code-runnable` submodule state, `compact_v5.zip` |

## Known Critical Findings

| Finding | Status |
|---|---|
| Block A A-16 cold-cache microcompact missing | Implemented and Claude iter10 reviewed |
| Block A A-17 compactable-tool allowlist missing from canonical row evidence | Implemented and Claude iter10 reviewed |
| Block A A-21 post-compact cleanup missing in compactor path | Implemented and Claude iter10 reviewed |
| Block A A-25 post-compact stub injection missing in compactor path | Implemented and Claude iter10 reviewed |
| Block A closure | Claude iter11 returned `APPROVE`, `READY_FOR_BLOCK_CLOSE_REVIEW`, 43/43 shipped, 0 blocking rows; LOW A-22/A-30/A-37 findings fixed and re-reviewed |
| E+F narrowed to env_block remaps | Fixed and closed. Claude iter2 returned `APPROVE`, `READY_FOR_BLOCK_CLOSE_REVIEW`; 8/8 ledger rows, 0 blocking rows; pushed at `6c36e1a`. |
| R-tier 42 scenario executable gate incomplete | Resolved for executable marker materialization; still ship-blocking until Claude-reviewed Phase A, AWS/mock execution, phase C review, telemetry, metrics, and per-test gate pass |

## Next Action

R-tier test preparation:

- `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
  materializes R6-R16, R18-E1..E15, and R19-U1..U10 as zero-cost reviewable
  specs.
- `py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .` passes
  locally as of 2026-05-04.
- This does not approve AWS spend. Each scenario still needs Claude Phase A
  review and explicit approval before any real Bedrock call.
- Details: `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`

Loop decision:

- The full-auto PowerShell supervisor loop is no longer the primary workflow.
- New primary workflow: one Codex worker coordinates implementation and Claude
  review directly.
- Every Claude prompt must include
  `CLAUDE_REVIEWER_BASE_PROMPT.md`, so Claude reconstructs scope from
  `SYNTHESIS_MASTER.md` instead of trusting the worker.
- The abandoned supervisor files were removed from the active control folder to
  avoid accidental reuse.
- There is no fixed cap on useful worker/reviewer iterations. Failed handoffs,
  stale prompts, no-verdict outputs, and real reject/fix rounds are recorded for
  audit visibility, not as an automatic stop. The worker stops only when the
  loop is stuck: 3 consecutive reviewer handoff failures, 3 attempts on the same
  row/finding/test failure without meaningful change, or another process blocker.
  Then it writes `blocks/<BLOCK>/REVIEW_LOOP_BLOCKED.md`, updates status/matrix,
  and asks the user for a decision.
- If Codex disagrees with a Claude finding, Codex must send a fresh
  dispute-review prompt back to Claude with full base prompt and exact evidence.
  The finding remains ship-blocking until Claude withdraws it, Codex fixes it,
  or the user explicitly decides.

Recommended driver:

`compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`

Current active Codex worker has completed and pushed Block A, Block E+F,
Block L, Block N, Block K, Block T, and Block C:

- Block A evidence commit: `05f85f442c47c49f0bf1e6e34871b653e13ff7f3`.
- Block E+F evidence commit: `6c36e1a77868d3c0d9247cd508c87916638812fd`.
- Block L evidence commit: `35730b3e05f2592ce58ab1767860808452f80700`.
- Block N evidence commit: `2f919bf53dadd64885912a69d0cae6a739dabb6c`.
- Block K evidence commit: `c0feaad2fd9975d13655f5b3eba0d8b4a24b5e72`.
- Block T close commit: `43d27278fda49173d2cbb3422603a20d3e9e81b5`.
- Block T evidence commit: `05972befa0c97f883e152e4fe5d7be1bb4baf531`.
- Block C close commit: `18fb3dc14e9e33f3d233f50c8bcde9d14f36558e`.
- Block C evidence commit: `34374979e851b9ebf24e5a4f9bcd66f007a6cdcf`.

The next worker action is to resume from files, read
`BLOCK_ORDER_AND_COVERAGE.md`, and start Block B. Do not tag unless explicitly
approved.

Worker-led loop docs:

`compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/WORKER_LED_LOOP.md`

Codex must not run nested Codex review; Claude is the reviewer:

```powershell
cd D:\Github\sagemaker-coding-agent
codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -m gpt-5.5 -c model_reasoning_effort="high" -C D:\Github\sagemaker-coding-agent - < compact_v5\_status\v5_completion_audit\06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md
```

Before first review, use the already-validated subscription reviewer command:

```powershell
cd D:\Github\sagemaker-coding-agent
$old=$env:ANTHROPIC_API_KEY; Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue; claude -p --model opus --effort xhigh --permission-mode dontAsk --setting-sources user --settings compact_v5\_status\v5_completion_audit\claude-reviewer-settings.json --tools "" --add-dir D:\Github\sagemaker-coding-agent --output-format text "Say CLAUDE_REVIEWER_READY and the model alias you are using. Do not run tools."; if ($old) { $env:ANTHROPIC_API_KEY=$old }
```

Do not run AWS/R-tier tests, tag, or final ready-for-testing approval without
explicit user approval. Per latest user instruction, git must be updated for
rollback/traceability: after any block reaches clean close state, commit using
only specific files and push branch `v5-build` to `sageagent`; do not tag unless
explicitly approved. Long blocks may also use specific-file checkpoint commits
after reviewer-approved implementation slices.
