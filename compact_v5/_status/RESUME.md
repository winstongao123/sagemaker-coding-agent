# RESUME PROTOCOL — v5.0.1 build (post-Wave-6, Block-based)

Use this checklist cold (zero prior context, after compaction, in a new session) to land ready to code.

---

## Step 1 — Read in this EXACT order, do NOT skip or skim

```
1. compact_v5/_phase_2/wave_6/WORKER_HINT_2026-05-03.md    # ★ READ FIRST — supersedes BUILDER_PROMPT/SYNTHESIS_MASTER
                                                            #   Sonnet 4.5 (no 4.6), web_fetch DROPPED, Block U (HTMLs),
                                                            #   R13-R16 enhanced, Block V v4-vs-v5, R-tier 3-AWS-call cap,
                                                            #   test→review→fix loop, R_TIER_REVIEW_TEMPLATE routing
2. compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md            # ★ R-tier review prompts — TEMPLATE A/B/C for AWS tests
3. compact_v5/_phase_2/wave_6/BUILDER_PROMPT.md            # the worker prompt — your job spec
4. compact_v5/_status/V5_BUILD_STATUS.md                   # current state + next pickup
5. compact_v5/_status/V5_DESIGN_DECISIONS.md               # ADR log (append-only)
6. compact_v5/_status/V5_RUNNABLE_PORT_LOG.md              # PORT_LOG rows so far
7. compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md     # canonical post-DEEP per-Block scope
8. compact_v5/_phase_2/wave_6/PS_Plan_Edge_Cases_Thinking.md  # 111 user scenarios
9. compact_v5/_phase_2/wave_6/TEST_DESIGN.md               # per-Block test catalogue
10. compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md    # Block-level scoping
11. Last 3 commits: `git log -n 3 v5-build`
12. Most recent Codex review: `_status/codex_reviews/block-<PREV>.md`
```

`MEMORY.md` (`~/.claude/projects/d--Github/memory/MEMORY.md`) is auto-loaded by Claude Code at session start and is the cross-session memory anchor.

## Step 2 — Verify state consistency (STOP on any mismatch)

```bash
git status                                                  # clean, OR only files in V5_BUILD_STATUS "Remaining"
git rev-parse v5-build                                      # = "Last commit sha" in V5_BUILD_STATUS.md
git for-each-ref refs/tags/v5.0.1-block-* \
   --sort=-version:refname --format='%(refname:short)' --count=1
                                                            # = expected prior tag in V5_BUILD_STATUS.md
cd compact_v5/MAIN/agent && pytest -q                       # = "Tests status" in V5_BUILD_STATUS.md
cd ../.. && python verify_ship_zip.py                       # zip extract+import succeed
```

If ANY check fails → STOP. Do not code. Report drift to user.

## Step 3 — Pick up the current Block

- Read `V5_BUILD_STATUS.md` "Next session: pick up at Block X"
- Take `BUILDER_PROMPT.md` and fill the 3 placeholders for Block X:
  - `<BLOCK_ID>` and `<BLOCK_NAME>` (from sequence)
  - "Block-specific scope" → paste from `SYNTHESIS_MASTER.md` §3 for Block X
  - "Block-specific test list" → paste from `TEST_DESIGN.md` §X
  - "Block-specific scenarios" → paste matching scenarios from `PS_Plan_Edge_Cases_Thinking.md`
- Update `V5_BUILD_STATUS.md`: bump "Last updated", set `State=IN_PROGRESS`

## Step 4 — As you work (drift prevention)

- Every Runnable/Hermes/LF pattern adopted → append row to `V5_RUNNABLE_PORT_LOG.md`
- Every non-trivial choice → append ADR to `V5_DESIGN_DECISIONS.md`
- Every meaningful step → `git commit` (specific files, never `-A`)
- Every 30 minutes / every 10 commits / before any context-heavy task → re-read `V5_BUILD_STATUS.md` "Next session pickup" line to confirm you're still on the right Block
- If you hit any STOP-and-ASK trigger from `BUILDER_PROMPT.md` → stop and report to user

## Step 5 — Close the Block

```bash
cd compact_v5/MAIN/agent && pytest tests/                   # T1+T2 green
papermill chat.ipynb /tmp/out.ipynb                         # T3 smoke
cd ../.. && python _rebuild_zip.py && python verify_ship_zip.py  # T4

# T5 only if your Block is high-risk (B, A, G3, G2, H+, N) or J
RUN_REAL_BEDROCK=1 AWS_REGION=ap-southeast-2 \
  pytest tests/integration/test_real_bedrock_smoke.py::test_<block>
```

Then run Codex 3-axis review (template in `_status/CODEX_REVIEW_TEMPLATE.md`):
```bash
cd D:/Github/sagemaker-coding-agent
codex exec --full-auto -s read-only -m gpt-5.5 --skip-git-repo-check \
  "$(cat _status/codex_reviews/block-<X>-prompt.txt)" \
  > _status/codex_reviews/block-<X>.md
```

If Codex CHANGES_REQUESTED or REJECT → fix, recommit, re-Codex. Tag is FORBIDDEN if any open finding ≥ CHANGES_REQUESTED.

## Step 6 — User-approval gate (Step 11 of BUILDER_PROMPT)

**STOP. Ask user**: "Block <X> ready. Codex APPROVE. <N> tests green. Diff at commit <sha>. Approve?"

User MUST explicitly approve. If user says fix something: fix, recommit, re-Codex, re-ask.

## Step 7 — Tag + push + close ritual

After user approval:
```bash
git tag v5.0.1-block-<X>
git push sageagent v5-build
git push sageagent v5.0.1-block-<X>

python _rebuild_zip.py                                      # if not already done
# Sync compact_v5.zip to OneDrive (project rule)
# Update HTML companion docs if architecture changed
# Sync chat.md if Block 0/E+F/F
```

Update:
- `_status/V5_BUILD_STATUS.md`: State=DONE for Block <X>; "Next session pick up at Block <NEXT>"
- `~/.claude/projects/d--Github/memory/project_v5_phase2_final_state.md`: Block <X> done
- Commit doc updates

NOW you can start the next Block (back to Step 1).

---

## Block sequence (22 Blocks per WORKER_HINT_2026-05-03.md)

`Block 0 → B → B+ → C → C+ → D → A → E+F → F2 → I → M → G → G3 → G2 → H → H+ → L → N → T → J → K → U`

(Block U HTMLs added 2026-05-03 — see WORKER_HINT §3)

After all 22 Blocks + R-tier (R1-R12 + R13-R16 enhanced) + Block V v4-vs-v5 head-to-head + final user acceptance: **v5.0.1 SHIPS**.

Real-AWS test discipline (per WORKER_HINT §10): max 3 AWS calls per test, BOTH worker AND Codex must APPROVE before each call. Use R_TIER_REVIEW_TEMPLATE.md TEMPLATE A (pre-flight) / B (failed-test diagnosis) / C (post-pass sanity).

## Drift prevention checklist (every session)

| Check | What it catches |
|---|---|
| Git sha matches V5_BUILD_STATUS | Someone committed without updating status |
| Last tag matches expected | Tagging out of order |
| Pytest count matches status | Tests added/removed without status update |
| Zip extract+import succeeds | Packaging regression |
| `MEMORY.md` consistent with project state | Memory drift across sessions |
| BUILDER_PROMPT placeholders filled correctly for current Block | Worker confused about scope |
| Open Codex findings = 0 | Forgot to address review |

If any check fails: STOP, report to user.

## When to ask user (escalation matrix)

| Situation | Action |
|---|---|
| Step 6 every Block | ALWAYS stop, ask, wait for explicit approval |
| New finding NOT in SYNTHESIS_MASTER | Stop, document, ask before adding scope |
| Codex CHANGES_REQUESTED you disagree with | Stop, ask user |
| Real-Bedrock test fails unexplained | Stop, ask (don't burn money retrying) |
| Constraint conflict (v4 needs X but X violates Y) | Stop, ask |
| LOC budget overrun >25% | Stop, ask |
| Discover new v4 baseline gap | Stop, document, ask |
| ANY destructive op (force-push, reset --hard) | NEVER without explicit user approval |
| Block needs to be split into 2 sub-Blocks | Stop, ask before splitting |
