# v5.0.1 BUILDER PROMPT — Comprehensive Worker Instructions

**Purpose**: This is the canonical prompt for any worker (sub-agent, Codex session, fresh Claude session) implementing a single Block of v5.0.1. Use it verbatim. Fill in `<BLOCK_ID>` and `<BLOCK_NAME>` for the specific Block.

---

# WORKER PROMPT — Build Block <BLOCK_ID>: <BLOCK_NAME>

You are building Block `<BLOCK_ID>` of v5.0.1. This Block is one of 21. Your scope is ONLY this Block — do not touch other Blocks. After your Block ships, the user approves before the next Block starts.

## MISSION

Build Block `<BLOCK_ID>` of v5.0.1, the SageMaker-native re-implementation of v4 + Runnable + Hermes + Learning Factory combined. v5.0.1 must:
- Cover all v4 baseline functionality (constraint #1: v4.10.10 floor — nothing v4 does gets dropped)
- Be ≥ Runnable on every BETTER axis (architecture / coordination / memory / context / focus / optimal-tool-use / token-optimization / long-complex-coding / security)
- Be > v4 decisively
- Avoid all 7 PS_problems structurally with named lock tests
- Handle 111 user scenarios from `wave_6/PS_Plan_Edge_Cases_Thinking.md`
- Ship for single-user Bedrock SageMaker (no MCP, no streaming, v4 chat.ipynb canonical UI)

## HARD CONSTRAINTS (15 — non-negotiable)

1. **v4.10.10 = baseline** (functional capability is the floor)
2. **v4 chat.ipynb = canonical UI** (UNCHANGED in v5 via `sagemaker_agent.py` shim)
3. **Cover ALL of v4 + Runnable + Hermes + LF** (NO DEFERRALS — every change is PORTED with source ref or DROPPED with categorical reason)
4. **Line-by-line investigation, no skip** (this Phase 2 satisfies it; you read SYNTHESIS_MASTER + PS_Plan_Edge_Cases_Thinking before coding)
5. **Minimum file structures** (consolidate post-port; reuse v5 surfaces; don't invent)
6. **Architecture-first thinking** before adopting any pattern
7. **PS_problems STRUCTURALLY fixed** with lock tests (not patched)
8. **v5 ≥ Runnable AND v5 > v4 decisively** axis-by-axis with file:line evidence
9. **Drop MCP entirely** (single-user SageMaker; no remote tool servers)
10. **Drop streaming** (SageMaker UI cannot stream; non-streaming Bedrock invoke only)
11. **Code-chunk refs BEFORE coding** (you read source file:line before writing your Block's code)
12. **NO DEFERRALS** (no v5.0.2 punt; everything in v5.0.1)
13. **Bedrock caching parity for sub-agents** (cache_control on parent + sub-agent prefix replay via Block G2 logic)
14. **Token + cost metrics covering parent AND sub-agent** (TOKENS singleton with per-agent breakdown)
15. **Quality, no rush** — better to ship fewer Blocks correctly than rush all 21

## READING ORDER (REQUIRED before writing code)

Read in this order. Do NOT skip any step.

1. **`compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`** — find your Block's section. Read every PORT_LOG row + architectural-fit verdict + LOC + graft strategy.
2. **`compact_v5/_phase_2/wave_6/PS_Plan_Edge_Cases_Thinking.md`** — find every scenario tagged with your Block. Treat each NEEDS-LOCK-TEST as an additional Q4 row you must add.
3. **`compact_v5/_phase_2/wave_6/TEST_DESIGN.md`** — find your Block's test list (T1-T5). These are the tests you write.
4. **`compact_v5/_phase_2/wave_5_deep/CONFIDENCE_REPORT.md`** §3 — re-read the 9-axis verdict to confirm what your Block contributes to "v5 > Runnable > v4".
5. **`compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md`** — your Block's section for Block-level scoping + LOC budget + Q1-Q4 evidence.
6. **`compact_v5/_phase_2/wave_3/COMBINED_ARCHITECTURE.md`** — your Block's combined-architecture decision (which repo owns shell vs internals).
7. **Source code** at the cited file:line ranges:
   - v4: `compact_v4/MAIN/agent/sagemaker_agent.py` (12,088 LOC monolith)
   - Runnable: `_archive/compare_code/gg-claude-code-runnable/src/`
   - Hermes: `D:/Github/hermes-agent/run_agent.py` + `AGENTS.md`
   - LF: `D:/Github/Learning_Factory/`
8. **Existing v5 code** at the target paths (verify what's already there from Phase 0-7 builds; you may be extending, not creating)
9. **`compact_v5/_phase_2/wave_4/Q4_BUG_COVERAGE.md`** — original Block lock tests
10. **`_status/RESUME.md`** — verify state consistency before coding

After reading all 10, you understand: what to copy from where, what to combine, what tests to write, what your Block delivers.

## PER-BLOCK PROCESS (12 steps, in order)

### Step 1 — State verification (before any code)
```bash
git status                                 # must be clean OR only files in Block X scope
git rev-parse v5-build                     # must equal "Last commit sha" in V5_BUILD_STATUS.md
cd compact_v5/MAIN/agent && pytest -q      # must match prior "Tests status"
```
If any check fails: STOP, report drift to user. Do NOT code.

### Step 2 — Read source code at cited refs
For every PORT_LOG row in your Block (per SYNTHESIS_MASTER §3), open the cited file:line in v4/Runnable/Hermes/LF and read the actual code. Do NOT trust summaries. The source is ground truth.

### Step 3 — Implement Block code
Apply the COMBINED architecture decision from `wave_3/COMBINED_ARCHITECTURE.md`. Examples:
- Block A: v4 Compactor is the SHELL; Runnable's `cache_edits` is grafted INSIDE
- Block H: v4 `_extract_and_append_memories` is the trigger event; Runnable's closure-scoped state is the implementation INSIDE
- Block C: v4's `OTHER TOOLS STILL WORK` message stays; Hermes JSON repair is added as a NEW code path

When porting Runnable TS → Python:
- TypeScript closures with state → Python class with instance state OR closure with `nonlocal`
- TypeScript async → Python sync (constraint #10: no streaming)
- TypeScript `cache_edits` (Anthropic API param) → Python `cache_control` blocks (Bedrock equivalent)
- Anthropic-API-direct features (interleaved-thinking beta, anthropic_beta header) → Bedrock `additionalModelRequestFields`

When using existing v5 code:
- DO NOT re-invent surfaces that exist (Phase 0-7 built `runtime/bedrock_client.py`, `security/`, `prompt/sections.py`, `tools/registry.py`, etc.)
- EXTEND existing code; DO NOT REPLACE unless plan says so

### Step 4 — Write tests per TEST_DESIGN
Write every T1 (unit), T2 (integration), T3 (notebook smoke), T4 (zip extract+import), and T5 (real-Bedrock single round-trip) test for your Block from the catalogue. Each test must:
- Have a clear assertion
- Be self-contained (no external deps unless mocked)
- Pass cleanly (green pytest)
- Be added to `compact_v5/MAIN/agent/tests/<unit|integration|tools|parity>/test_<block>.py`

For real-AWS T5 tests: gate them with `if not os.getenv("RUN_REAL_BEDROCK"): pytest.skip(...)`.

### Step 5 — Append PORT_LOG rows
For every change in your Block, append a row to `_status/V5_RUNNABLE_PORT_LOG.md` (NOT to Q1_EVIDENCE_MATRIX which is now historical reference). Each row:
```
| <id> | <YYYY-MM-DD> | <BLOCK_ID> | <source repo:file:line> | <v5 target> | PORTED | <verdict> | <commit sha> | <notes> |
```

Mark `evidence_tier: VERIFIED` (you read the source); never LISTED (you can read the source, so verify).

### Step 6 — Append ADRs
For any non-trivial choice (combine decision, library choice, pattern adaptation), append an ADR to `_status/V5_DESIGN_DECISIONS.md`:
```
## ADR-NNN — <title>
- Date / Phase ID / Status / Context / Options / Decision / Rationale / Runnable-fidelity impact / Affected files / Linked port-log rows
```

### Step 7 — Run all tests + ship-gate
```bash
cd compact_v5/MAIN/agent
pytest tests/                                    # T1 + T2 must be green
papermill chat.ipynb /tmp/out.ipynb              # T3 — cells 1-3 execute clean

cd ../..
python _rebuild_zip.py                           # rebuild compact_v5.zip
python verify_ship_zip.py                        # T4 — extract + import succeed

# T5 (high-risk Blocks only — see TEST_DESIGN per-Block)
RUN_REAL_BEDROCK=1 AWS_REGION=ap-southeast-2 \
  pytest tests/integration/test_real_bedrock_smoke.py::test_<block>_real_haiku
```

If ANY test fails: STOP, fix, re-run. Never tag with red tests.

### Step 8 — Codex AXIS A/B/C review

**MANDATORY pre-step (added 2026-05-03 after Block B review stalled)**:
when citing v4 source for cross-check, **PRE-EXTRACT only the cited line
ranges** to small files via `sed -n 'A,Bp' compact_v4/MAIN/agent/sagemaker_agent.py
> /tmp/v4_<name>.txt` BEFORE invoking Codex. Reading the full 12,088-LOC
v4 monolith stalls Codex (it tried to ingest the entire file once and
returned 0 bytes after 10+ minutes). Pre-extracting keeps Codex review
under 10 minutes. Same rule for any other large reference (Hermes
`run_agent.py`, etc.) — extract the cited ranges only.

The Codex prompt's "Read paths" section MUST then read like:
```
v4 source PRE-EXTRACTED (avoid 12K-LOC monolith):
  - /tmp/v4_<name>_section.txt   (...; v4 lines A-B; N LOC)
DO NOT read compact_v4/MAIN/agent/sagemaker_agent.py directly.
```

Save the prompt to `_status/codex_reviews/block-<BLOCK_ID>-prompt.txt`. Run:
```bash
cd D:/Github/sagemaker-coding-agent
codex exec --full-auto -s read-only -m gpt-5.5 --skip-git-repo-check \
  "$(cat _status/codex_reviews/block-<BLOCK_ID>-prompt.txt)" \
  > _status/codex_reviews/block-<BLOCK_ID>.md
```
Run in background via Claude Code's `run_in_background=true` so a stalled
Codex (e.g. monolith ingest) can be killed via TaskStop without losing
your terminal session.
Codex review template (copy this into the prompt):
```
You are reviewing Block <BLOCK_ID> of v5.0.1.
Diff range: v5.0.1-block-<PREV>..HEAD
Files changed: <list>

AXIS A — Errors / bugs / regressions
For each changed file: correctness defects, security, concurrency, dead code, test coverage gaps. Verdict: PASS | CHANGES_REQUESTED | BLOCKER.

AXIS B — v5 architecture + goals fit
Does this advance v5's 7 BETTER axes? Honor 15 hard constraints? FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED.

AXIS C — Reference-repo coverage
Did this Block port everything tagged for it in SYNTHESIS_MASTER §3? Drop anything? UNDECLARED_PATTERN flag if invented.

FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.
```

If Codex says CHANGES_REQUESTED or REJECT: fix, recommit, re-Codex. Do NOT tag with open findings.

### Step 9 — Update status docs
- `_status/V5_BUILD_STATUS.md`: bump "Last updated", set "Last commit sha" + "State=DONE" for current Block + "Next session: pick up at Block <NEXT>"
- Append entry to `_status/V5_RUNNABLE_PORT_LOG.md` with rows from Step 5
- Append ADRs from Step 6 to `_status/V5_DESIGN_DECISIONS.md`

### Step 10 — Git commit
```bash
git add <SPECIFIC FILES — never -A>
git commit -m "$(cat <<'EOF'
v5/block-<BLOCK_ID>: <imperative subject>

<2-4 sentences why>

Block <BLOCK_ID> ports: <list>
Tests: <count> green
Codex AXIS A/B/C: APPROVE
EOF
)"
git status                                       # verify clean
```

NEVER `git add -A` (project rule prevents .env / credentials inclusion).

### Step 11 — Tag (after Codex APPROVE)

**Two modes — choose ONCE at start of build, applies to all 21 Blocks**:

#### Mode A — User-gate (default; per-Block user review)
**STOP and ask the user**: "Block <BLOCK_ID> ready. Codex APPROVE. <N> tests green. Diff is at commit <sha>. Approve?"
User must explicitly approve before you tag. If user says fix something: fix, recommit, re-Codex, re-ask.

#### Mode B — Codex-only-gate (autonomous; user reviews FINAL product only)
User has explicitly said "Codex-only mode" or equivalent at build start. In this mode:
- **Codex APPROVE = auto-tag + auto-push + start next Block** (no user prompt)
- **Codex CHANGES_REQUESTED or REJECT = fix → recommit → re-Codex → loop until APPROVE** (no user prompt unless an ESCALATION trigger fires — see below)
- User sees status notifications but is NOT asked to approve per-Block
- Run R-tier (R1-R12) automatically after Block K completes
- **STOP at FINAL gate only**: after all 21 Blocks + R-tier, present FINAL product summary to user

**Codex resilience rule (network failure / hang fallback)**:
If Codex returns APPROVE_WITH_FIXES on iter-N, worker fixes findings AND writes one lock test per finding, and iter-(N+1) hangs >15 min with 0 bytes output OR fails with network error:
1. Kill the background Codex task.
2. Verify EVERY iter-N finding has a corresponding lock test in the new commit (grep test names against findings).
3. If YES → tag with note "iter-(N+1) skipped due to Codex network/hang; lock tests serve as durable verification" + log to `_status/codex_reviews/block-X-iter-skipped.md`.
4. If NO → ESCALATE to user before tagging.

Rationale: lock tests are STRONGER than one-shot Codex re-review (they enforce fix permanently; Codex re-review is single-snapshot opinion). This prevents Codex CLI/network issues from blocking the build indefinitely.

**Mode B HARD ESCALATION TRIGGERS (still STOP and ask user even in Mode B)**:
1. Codex stuck in REJECT loop (3+ iterations on same block, fixes not converging — DIFFERENT from network hang; this is when Codex returns substantive REJECT each time)
2. New finding NOT in SYNTHESIS_MASTER discovered (truly new, not missed note)
3. Constraint conflict (v4 needs feature X but X violates a hard constraint)
4. Real-Bedrock smoke fails for unexplained reasons (don't burn money retrying)
5. LOC budget for the Block exceeds plan estimate by >50%
6. R-tier scenario fails (R1-R12) — investigate root cause, ask user before re-test
7. Any destructive op needed (force-push, reset --hard, delete branch)
8. Block needs to be split or scope changes

If ANY of these fire in Mode B: STOP, document in V5_BUILD_STATUS, ask user.

After Codex APPROVE (or after user approval in Mode A):
```bash
git tag v5.0.1-block-<BLOCK_ID>
git push sageagent v5-build
git push sageagent v5.0.1-block-<BLOCK_ID>
```

### Step 12 — Per-Block close ritual
After tag + push:
- Rebuild zip if not already done: `python _rebuild_zip.py`
- Update HTML companion docs if architecture changed (Block E+F/A/B/H/N)
- Sync `chat.md` if Block 0/E+F/F
- Sync `compact_v5.zip` to OneDrive (per project rule)
- Update Claude memory at `~/.claude/projects/d--Github/memory/project_v5_phase2_final_state.md` with Block <BLOCK_ID> done

NOW you can start the next Block's reading order (Step 1).

## TEST REQUIREMENTS PER BLOCK

See `wave_6/TEST_DESIGN.md` §<BLOCK_ID> for the exact test list. Pass criteria:
- All T1 + T2 pass green pytest
- T3 notebook smoke clean
- T4 zip extract + import succeed
- T5 real-Bedrock smoke green (only for high-risk Blocks: B, A, G3, G2, H+, N + Block J)
- Codex AXIS A/B/C = APPROVE
- User approval

## R-TIER TESTING (run AFTER Block K, BEFORE final tag)

Once all 21 Blocks done, run R1-R12 from `wave_6/TEST_DESIGN.md` §R-tier:
- R1: 50-turn dashboard build ($1.00 cap)
- R2: 80K-token compaction ($0.50)
- R3: Sub-agent dispatch + cache-prefix ($0.50)
- R4: 30-min idle cold-cache ($0.20)
- R5: 200-bash recovery ($0.50)
- R6: Memory consolidation /dream ($0.30)
- R7: Model switch A28 invariant ($0.50)
- R8: JSON repair ($0.20)
- R9: Approval flow ($0.30)
- R10: Save/load preservation ($1.00)
- R11: Sonnet end-to-end ($1.50)
- R12: Malformed args + surrogate ($0.20)

Total R-tier cap: $7.00. If any R-test fails: investigate root cause, fix the relevant Block, re-test before tag.

## OUTPUT EXPECTATIONS PER BLOCK

When your Block is done, you must have produced:

| Output | Location |
|---|---|
| Block code | `compact_v5/MAIN/agent/<files>` |
| Tests for the Block | `compact_v5/MAIN/agent/tests/<unit\|integration\|tools\|parity>/test_<block>.py` |
| PORT_LOG rows | `_status/V5_RUNNABLE_PORT_LOG.md` (appended) |
| ADRs | `_status/V5_DESIGN_DECISIONS.md` (appended) |
| Codex review | `_status/codex_reviews/block-<BLOCK_ID>.md` |
| Status update | `_status/V5_BUILD_STATUS.md` (updated) |
| Git tag | `v5.0.1-block-<BLOCK_ID>` |
| Pushed to remote | `sageagent` |
| Rebuilt zip | `compact_v5/compact_v5.zip` |
| HTML updates | `compact_v5/docs/<file>.html` if architecture changed |
| Memory updated | `~/.claude/projects/d--Github/memory/project_v5_phase2_final_state.md` |

## BLOCKS WHERE YOU MUST STOP AND ASK USER

Step 11 always — every Block requires explicit user approval before tag. Do not auto-approve.

Additional stop-and-ask points:
- If you find a NEW finding NOT in SYNTHESIS_MASTER (truly new, not a missed note) — stop, ask user before adding scope
- If a Codex CHANGES_REQUESTED is borderline (you disagree with Codex) — stop, ask user
- If real-Bedrock smoke fails for unexplained reasons — stop, ask user (don't burn money in retries)
- If a constraint conflict arises (e.g. v4 needs feature X but X violates constraint Y) — stop, ask user
- If LOC budget for the Block exceeds estimate by >25% — stop, ask user
- If you discover a v4 baseline gap not yet documented — stop, document, ask user

## CRITICAL ANTI-PATTERNS (will cause REJECT)

- ❌ Inventing patterns not in any source repo (UNDECLARED_PATTERN)
- ❌ Silent scope narrowing (dropping a v4 feature without explicit user approval — this caused v5.0.0 to fail)
- ❌ `git add -A` (project rule)
- ❌ Skipping tests because "they take too long"
- ❌ Tagging with open Codex findings ≥ CHANGES_REQUESTED
- ❌ Auto-running real-AWS without `RUN_REAL_BEDROCK=1` env gate
- ❌ TypeScript→Python translation that drops semantics (e.g. closure-scoped throttle becomes global, breaking concurrent sub-agents)
- ❌ Replacing v4 code that wasn't broken
- ❌ Force-push, amend after tag, rebase published commits
- ❌ Adding features not in plan (gold-plating)
- ❌ Marking Block "done" before user approves
- ❌ Skipping `_status/V5_BUILD_STATUS.md` update (next session won't know where to pick up)
- ❌ Adding daemon / auto-fire / scheduler to Block H+ (user decision: manual `/dream` only)

## ESCALATION

If you hit any blocker not in the "stop-and-ask" list above:
1. Document the blocker in `_status/V5_BUILD_STATUS.md` "Blockers" section
2. Set Block state to BLOCKED
3. Stop coding, report to user

## SUCCESS CRITERION

Block `<BLOCK_ID>` is DONE when:
- ✓ Code matches plan + SYNTHESIS_MASTER + Wave 6 deltas
- ✓ All tests for the Block green (T1-T5 as applicable)
- ✓ Codex AXIS A/B/C = APPROVE
- ✓ User explicitly approved
- ✓ Tag created + pushed
- ✓ Zip rebuilt + HTML updated
- ✓ Status / PORT_LOG / ADR / memory all updated

After 21 Blocks done + Block J real-AWS gate + R1-R12 all pass + final user acceptance: **v5.0.1 SHIPS**.

---

# Block-specific scope (paste from SYNTHESIS_MASTER §<BLOCK_ID>)

> When using this prompt, paste the relevant Block section from `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` here. Each row is a PORT_LOG line you must implement.

# Block-specific test list (paste from TEST_DESIGN.md §<BLOCK_ID>)

> Paste the Block's test list from `compact_v5/_phase_2/wave_6/TEST_DESIGN.md` here.

# Block-specific scenarios (paste from PS_Plan_Edge_Cases_Thinking.md)

> Search PS_Plan_Edge_Cases_Thinking.md for scenarios tagged with this Block. Each NEEDS-LOCK-TEST becomes a Q4 row you must add.

---

**End of BUILDER_PROMPT.**

This prompt is self-contained. A worker handed this prompt + the three pasted Block-specific sections has everything needed to implement one Block correctly without re-investigating.
