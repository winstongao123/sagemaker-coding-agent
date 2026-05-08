# L1 — Learning Factory hooks/ + scripts/ + tools/ Deep Scan

**Date**: 2026-05-01
**Slice**: `D:/Github/Learning_Factory/{hooks,scripts,tools}` + root executables
**Method**: Glob enumeration + line-by-line Read of every shell/python file
**Purpose**: Verify Wave-5 prior LF scan (5 NEW patterns), find anything missed, classify against v5 Plan v3 Block K
**Constraints**: v5.0.1 = single-user SageMaker, Bedrock-only, v4 chat.ipynb canonical UI, NO DEFERRALS

---

## 1. FILES AUDIT (every executable, line counts verified)

`tools/` does NOT exist. Only hooks/ + scripts/ + 2 root scripts.

### hooks/ (25 files — all bash, all read line-by-line)

| # | File | LOC | Hook event | Purpose | Verdict vs v5 |
|---|------|-----|-----------|---------|---------------|
| 1 | anti-simulation.sh | 33 | PreToolUse Edit/Write | Block `from moto`, `localstack`, `DRY_RUN=true`, `localhost:4566` in code | OUT-OF-SCOPE (v5 is real Bedrock) |
| 2 | auto-push.sh | 42 | Stop | Reminds Claude to commit/push/update docs/STATE | OUT-OF-SCOPE (UI lives in chat.ipynb, no STATE.md model) |
| 3 | auto-review.sh | 69 | PostToolUse Edit/Write | Heuristic grep: secrets, env-leaks, TODO, bare except, console.log | OUT-OF-SCOPE (host-side, not agent-side) |
| 4 | codex-judge-gate.sh | 169 | PreToolUse Bash on git commit | Codex gpt-5.3-codex independent review of staged diff (rubric: regressions/security/scope/doc-sync/error-handling); blocks on FAIL | OUT-OF-SCOPE (v5 has no codex inside SageMaker) |
| 5 | micro-checkpoint.sh | 94 | PostToolUse Edit/Write | Every 5 edits OR 10 min: emits checkpoint reminder (Just did / Next / Drift check) | OUT-OF-SCOPE (host-side Claude Code rule, not v5 SageMaker agent) |
| 6 | post-compact.sh | 21 | PostCompact | After compact: re-read CLAUDE.md + STATE.md + compression record, continue | OUT-OF-SCOPE (no compaction concept in v5 chat.ipynb) |
| 7 | pre-commit-diff-review.sh | 105 | PreToolUse Bash on git commit | Dumps `git diff --cached` to Claude, requires self-review acknowledgement; 2-min marker | OUT-OF-SCOPE (host-side dev workflow) |
| 8 | pre-compact-compress.sh | 95 | PreCompact | Asks Claude to write structured compression record (Goal/Constraints/Progress/Decisions/Files/NextSteps/Critical) before compact | OUT-OF-SCOPE (no compact event in v5) |
| 9 | pre-edit-checkpoint.sh | 152 | PreToolUse Edit/Write | Shadow-git snapshot per file (30s throttle, 200 max FIFO) for /rollback | OUT-OF-SCOPE (Bedrock agent has no host file system to shadow-git) |
| 10 | quality-check.sh | 103 | Stop | Deterministic quality gate: secrets, long functions (>30 LOC), missing docstrings, TODO, empty catches | OUT-OF-SCOPE (host-side) |
| 11 | sanitize-output.sh | 84 | PostToolUse Bash | Strips lone UTF-16 surrogates from Bash output to prevent API 400 | PLATFORM BUG WORKAROUND — irrelevant inside SageMaker |
| 12 | session-start.sh | 51 | SessionStart | Cleans zombie task dirs, surfaces recent sessions + learned skills | OUT-OF-SCOPE (no SessionStart event in v5) |
| 13 | sync-to-ralph.sh | 36 | manual command | Copies unchecked STATE.md tasks → .ralph/fix_plan.md for ralph autonomous loop | OUT-OF-SCOPE (Ralph not in v5) |
| 14 | test-on-stop.sh | 96 | Stop | Auto-runs test runner (bun/pytest/cargo) when code files changed | OUT-OF-SCOPE (host-side Claude Code) |
| 15 | type-check.sh | 51 | PostToolUse Edit/Write | py_compile + tsc --noEmit on touched file | OUT-OF-SCOPE (host-side) |
| 16 | verify-before-commit.sh | 66 | PreToolUse Bash on git commit | Blocks commit if STATE.md not modified <5 min OR CHANGELOG.md not modified <5 min when code staged | OUT-OF-SCOPE (host-side) |
| 17 | html-playwright-check.sh | 92 | PostToolUse Edit/Write | Spawns Playwright, screenshots HTML, checks console + Mermaid render errors | OUT-OF-SCOPE (no HTML output, v4 chat.ipynb canonical) |
| 18 | pre-compact.sh | 39 | PreCompact | Logs compaction event, marks active session file | OUT-OF-SCOPE |
| 19 | session-end.sh | 64 | Stop | Updates/creates ~/.claude/sessions/<date>-session.tmp | **PATTERN #4 in prior Wave-5; deferred to v5.0.2** |
| 20 | cso-check.sh | 102 | PreToolUse Bash on git commit | Blocks commit when added `description:` doesn't start with "Use when" | **PATTERN #1 in prior Wave-5 (CSO)** |
| 21 | task-granularity-check.sh | 101 | PreToolUse Bash on git commit | Blocks commit when new `### T-XXX` task block in TASKS.md/IMPL_TODO.md exceeds 15 lines | **PATTERN #2 in prior Wave-5 (granularity)** |
| 22 | tool-failure-detect.sh | 137 | PreToolUse all tools | Tracks (tool, args_hash) per session_id; blocks 5+ same-args, 3+ consecutive failures, 8+ session failures | **PATTERN #3 in prior Wave-5 (loop break)** |
| 23 | smart-approval.sh | 181 | PreToolUse Bash | OPT-IN tiered Codex judge for ambiguous commands (chmod/chown/curl-pipe-sh/pip install/mass-rm/...). 14 ambiguous patterns. Session approval cache. Bash-4 required (Mac graceful skip). | NEW — host-side Codex; OUT-OF-SCOPE for Bedrock |
| 24 | nonstop.sh | 68 | Stop | Session-scoped (or global) flag blocks Stop with decision-framework nudge; bounded by NONSTOP_MAX | OUT-OF-SCOPE (v5 has explicit Save/Stop UI) |
| 25 | pre-bash-safety.sh | 279 | PreToolUse Bash | **HARD destructive-command gate** — rm -rf system paths (Linux/Win/Mac), git destructive ops, curl-pipe-sh, base64\|sh, eval $(curl...), AWS/GCP/Azure/k8s/helm/terraform/pulumi/heroku/vercel/wrangler/fly/railway destroys, fs/lvm/mkfs/dd, crontab -r/systemctl disable, SQL inline DROP/TRUNCATE, redis FLUSHALL, chmod 000/chattr +i, base64-decode\|shell, hex-decode chains, redirect to system paths. v4.10.7 cross-surface parity (mirrors `compact_v4/agent/sagemaker_agent.py DANGEROUS_PATTERNS`). | **ALREADY IN v4 → already in v5** (parity, not new) |

### scripts/ (1 active)

| # | File | LOC | Purpose | Verdict |
|---|------|-----|---------|---------|
| 26 | factory-report.py | 684 | OBSERVE+REPORT only: aggregates `~/.claude/usage-data/` facets+session-meta over N-day window into HTML report (top frictions, per-project, suggestion cards, acceptance accept/reject CLI, PII redaction). v1.7.0. | OUT-OF-SCOPE (host-side Claude Code observability) |
| 27 | red-team-scan.sh | 113 | Prints 3-agent prompt template (Scan / Red-team / Timeline) for external-repo pattern adoption per D-0090 audit protocol | **DOCTRINE / PROCESS — relevant to v5 build, not runtime** |
| (27a) | __pycache__/factory-report.cpython-311.pyc | — | Compiled cache | n/a |

### Root executables

| # | File | LOC | Purpose | Verdict |
|---|------|-----|---------|---------|
| 28 | setup.sh | 352 | Auto-installs commands/agents/hooks/skills/CLAUDE.md/settings to `~/.claude/`, clones everything-claude-code, optionally gstack/ralph/codex CLI, auto-activates nonstop globally. v1.7.0. | OUT-OF-SCOPE (host-side bootstrap) |
| 29 | import-memories.sh | 88 | Copies factory's portable memories/*.md into a Claude Code project memory dir | OUT-OF-SCOPE |

**Total scanned: 29 files, ~3,250 LOC of bash + ~684 LOC of Python.**

---

## 2. CAPABILITIES TABLE — every distinct behavior

| Capability | Source file(s) | In v5 plan? | Note |
|---|---|---|---|
| Block destructive shell commands (rm -rf system, AWS/GCP/Azure/k8s/terraform destroy, curl\|sh, base64\|sh, git push --force/--delete, FLUSHALL, etc.) | pre-bash-safety.sh | YES — v4.10.7 parity already in v5 baseline | Already mirrored in compact_v4/agent/sagemaker_agent.py DANGEROUS_PATTERNS |
| Block staged-diff commits without "Use when" CSO description | cso-check.sh | YES — Wave-5 #1 ADOPT (inherited hook + CLAUDE.md doc) | Plan v3 Block K |
| Block oversized (>15 line) task blocks in IMPL_TODO/TASKS/plan*.md | task-granularity-check.sh | YES — Wave-5 #2 ADOPT (inherited hook + BUILD_GUIDE doc) | Plan v3 Block K |
| Detect tool-call loops + stuck-failure + session-corruption | tool-failure-detect.sh | YES — Wave-5 #3 ADOPT (inherited hook, optional) | Plan v3 Block K (CowAgent pattern) |
| Session-end housekeeping (touch session file, update timestamps) | session-end.sh | DEFERRED Wave-5 #4 — **VIOLATES NO-DEFERRALS RULE** (see CONFLICT below) | |
| Skill-promotion workflow (/promote-to-skill) | skills/promote-to-skill (referenced by setup, not in hooks/scripts) | YES — Wave-5 #5 ADOPT (~200 LOC Block D + Block K) | Plan v3 Block D + K |
| Codex gpt-5.3-codex commit-gate (independent reviewer) | codex-judge-gate.sh | NO — Bedrock-only constraint | Skip-Codex memory rule |
| Self-review staged diff before commit | pre-commit-diff-review.sh | NO — host-side dev workflow | |
| STATE.md / CHANGELOG freshness gate before commit | verify-before-commit.sh | NO — host-side; v5 doesn't use STATE.md | |
| Auto-run tests on code change (Stop hook) | test-on-stop.sh | NO — v5 chat.ipynb is interactive UI, not test runner | |
| Heuristic post-edit code review (grep secrets/TODO/console.log/empty catch) | auto-review.sh, quality-check.sh | NO — overlaps anti-simulation; not value-add for Bedrock single-user | |
| Type-check post-edit (py_compile / tsc) | type-check.sh | NO — host-side | |
| Block AWS-simulation imports (moto/localstack/DRY_RUN) | anti-simulation.sh | NO — v5 doesn't import simulated AWS; rule lives in agent prompt | |
| Shadow-git per-file checkpoint + /rollback | pre-edit-checkpoint.sh | NO — Bedrock agent has no host fs; v5 uses Bedrock conversation history | |
| Sanitize lone UTF-16 surrogates from Bash output | sanitize-output.sh | NO — Claude Code platform bug, not Bedrock concern | |
| Micro-checkpoint drift reminders every N edits/min | micro-checkpoint.sh | PARTIAL — v5 has Block-level approval gates which serve same role | Plan v3 Block K |
| PreCompact structured compression + PostCompact restore | pre-compact-compress.sh, post-compact.sh, pre-compact.sh | NO — v5 chat.ipynb has no compaction; uses Bedrock cache_control + RESUME log instead | |
| Stop-hook nudge to keep working until tasks done | nonstop.sh, auto-push.sh | NO — v5 UI has explicit Save/Continue buttons | |
| Smart-approval ambiguous-command Codex judge (chmod/curl-pipe/pip install) | smart-approval.sh | NO — Bedrock-only, no Codex; opt-in SMART_APPROVAL=1 isn't useful | |
| HTML Playwright auto-screenshot + console/Mermaid error block | html-playwright-check.sh | NO — v5 produces no HTML | |
| Sync STATE.md unchecked tasks → .ralph/fix_plan.md | sync-to-ralph.sh | NO — Ralph not in v5 | |
| SessionStart zombie-task cleanup | session-start.sh | NO — no SessionStart event | |
| Insights/usage-data aggregation HTML report | scripts/factory-report.py | NO — host-side observability of Claude Code, not v5 agent | |
| 3-agent red-team-scan prompt template for external-pattern adoption | scripts/red-team-scan.sh | DOCTRINE — already followed in Wave-2..5 audit protocol | Process, not code |
| Auto-installer for hooks/skills/commands/settings.json + clone everything-claude-code/ralph/gstack/codex | setup.sh | NO — host bootstrap | |
| Portable-memory import to Claude Code project dir | import-memories.sh | NO — host bootstrap | |

---

## 3. ALREADY-IN-PLAN (Plan v3 Block K)

Plan v3 already commits to:
- **CSO "Use when" convention** in CLAUDE.md (cso-check.sh inherited)
- **Task granularity ≤15 lines** in BUILD_GUIDE (task-granularity-check.sh inherited)
- **Tool-failure loop break** documented (tool-failure-detect.sh inherited as optional)
- **/promote-to-skill workflow** Block D handler + state/skill-proposals/ scaffold
- **STATE/RESUME log** + **PORT_LOG schema** + **per-block approval gates** + **AXIS-C reference coverage gap log**

**No new Plan-v3 changes required from this scan**. Three "inherited hook" patterns are documentation-only (no code into v5); skill-promotion is the only new code.

---

## 4. OUT-OF-SCOPE (16+ items, all reasoned)

| Item | Why out-of-scope |
|---|---|
| anti-simulation.sh | v5 talks to real Bedrock; no localstack/moto/DRY_RUN exists. Anti-rule belongs in agent prompt, not host hook. |
| auto-push.sh, sync-to-ralph.sh | v5 chat.ipynb is the UI; no STATE.md model, no Ralph. |
| auto-review.sh, quality-check.sh, type-check.sh | Host-side dev workflow. v5 doesn't write code on host machine. |
| codex-judge-gate.sh, smart-approval.sh, pre-commit-diff-review.sh | Bedrock-only constraint forbids OpenAI Codex inside SageMaker (memory: "Skip Codex for Bedrock Patches"). |
| verify-before-commit.sh | Host commit gate; not relevant to Bedrock loop. |
| test-on-stop.sh | v5 is an interactive coding agent in chat.ipynb, not a test runner. |
| micro-checkpoint.sh | v5 has explicit Block-level user approval gates (Plan v3 Block K) which serve the same drift-prevention role at the right granularity. |
| post-compact.sh, pre-compact.sh, pre-compact-compress.sh | v5 chat.ipynb has no /compact event. Uses Bedrock cache_control + RESUME log for the same goal. |
| pre-edit-checkpoint.sh | Bedrock agent edits via tool calls into S3/ipynb cells; host shadow-git not applicable. |
| sanitize-output.sh | Claude Code platform bug (Bash stdout surrogates). Bedrock loop doesn't have this surface. |
| nonstop.sh | v5 chat.ipynb has explicit Save/Continue/Stop buttons; user is at keyboard. |
| html-playwright-check.sh | v5 produces no HTML output (canonical UI = chat.ipynb). |
| session-start.sh, session-end.sh | Claude Code session events; v5 has no equivalent lifecycle. **session-end.sh is also Wave-5 #4 deferred — see CONFLICT below.** |
| scripts/factory-report.py | Host-side observability of Claude Code usage; v5 doesn't run on Claude Code. |
| setup.sh, import-memories.sh | Host bootstrap. |
| scripts/red-team-scan.sh | Doctrine, not runtime — already followed in Phase 2 audit protocol. |

---

## 5. NEW PATTERNS — verification of prior Wave-5 5-pattern claim

| Wave-5 Pattern | Source file | Verified in this scan? |
|---|---|---|
| #1 CSO "Use when" check | cso-check.sh | YES (102 LOC, line 32: matcher git commit; line 60: scans `+description:`; line 71: `prefix !~ /^use when/`) |
| #2 Task granularity ≤15 lines | task-granularity-check.sh | YES (101 LOC, line 44: only IMPL_TODO/TASKS/plan*.md; line 56: tracks `+###` block size; line 69: `if (count > 15)` block) |
| #3 Tool-failure detection (5+ same / 3+ failed / 8+ total) | tool-failure-detect.sh | YES (137 LOC, line 91: `consecutive >= 5` block; line 103: `consecutive_failed >= 3`; line 115: `total_failed >= 8`) |
| #4 Session-end cleanup | session-end.sh | YES (64 LOC) — but see CONFLICT |
| #5 Skill-promotion workflow | NOT in hooks/ or scripts/ | Lives at `skills/promote-to-skill/` (skills tree, not hooks tree). Confirmed via setup.sh line 80–95 referencing `skills/`. Out of scope of this slice but verified to exist. |

All 5 verified.

---

## 6. NEW PATTERNS MISSED BY PRIOR WAVE-5 — anything additional?

| Candidate found | In prior Wave-5? | v5 Decision |
|---|---|---|
| **smart-approval.sh** (181 LOC) — tiered Codex-judge for ambiguous commands (14 patterns: chmod/chown/curl\|sh/wget\|sh/npm i -g/pip install/rm wildcard/find -delete/xargs rm/docker -v host-mount/systemctl/service/SQL DROP/mv root). Session approval cache. | NOT mentioned | **OUT-OF-SCOPE** — needs OpenAI Codex which Bedrock-only forbids. Pattern itself (tiered judge for ambiguous command class) is interesting but architecturally requires external LLM. v5's hard-block list in pre-bash-safety.sh + agent prompt is sufficient for single-user SageMaker. |
| **scripts/red-team-scan.sh** — codified 3-agent (Scan / Red-team / Timeline-Guardian) prompt template for external-repo pattern adoption per D-0090 audit. | NOT mentioned | **DOCTRINE — already followed in Wave 2..5 audits**. Worth surfacing in v5's `/wave_5_deep/` build process documentation but no runtime code change. |
| **pre-bash-safety.sh** v4.10.7 cross-surface parity (cloud destroys: AWS/GCP/Azure/k8s/helm/terraform/terragrunt/pulumi/doctl/heroku/vercel/netlify/wrangler/flyctl/railway; storage: lvremove/mkfs/dd/zfs destroy/btrfs delete/cryptsetup; SQL CLI inline DROP/TRUNCATE; redis FLUSHALL; chmod 000; chattr +i; redirect to system paths; v4.10.8 obfuscation hardening: base64\|sh, xxd\|sh, eval $(curl), eval `wget`, hex-decode chains). | Implicitly — already in v4 baseline | **ALREADY IN v5 BASELINE** (v4.10.7 parity). Useful confirmation: the LF `pre-bash-safety.sh` is the **exact mirror** of the v4 SageMaker `DANGEROUS_PATTERNS` per file comments (line 88: "Mirror of compact_v4/agent/sagemaker_agent.py DANGEROUS_PATTERNS so the gate fires *regardless of authority level*"). v5 inherits this verbatim. |
| **factory-report.py acceptance loop** — accept/reject CLI + cooldown demotion (>=2 rejections = bottom rank) + per-friction badge | NOT mentioned | **OUT-OF-SCOPE** — host-side Claude Code self-observation. Could inspire a v5.x "agent self-observation report" but not for v5.0.1 (no deferrals doesn't mean adopt every adjacent pattern; this is purely Claude-Code-host observability). |
| **micro-checkpoint quality-reports/checkpoints.md log** — append-only audit of every drift-prompt trigger | NOT mentioned | **PARTIALLY COVERED** by v5's RESUME log + PORT_LOG. Not new. |
| **import-memories.sh** picker-prompt UX | NOT mentioned | OUT-OF-SCOPE — host bootstrap. |

**Conclusion**: 0 NEW runtime patterns found beyond prior Wave-5's 5. One DOCTRINE pattern (red-team-scan.sh 3-agent template) worth surfacing in v5 build process docs.

---

## 7. CONFLICT WITH NO-DEFERRALS RULE — session-end.sh

Prior Wave-5 marked **#4 session-end cleanup as DEFERRED to v5.0.2**. Per `feedback_v5_no_deferrals.md` (binding 2026-04-30): _"do NOT defer Runnable enhancements; v5 = v4 + Runnable + Hermes + LF combined; everything in v5.0.1, no v5.0.2 punt."_

Re-evaluation:
- session-end.sh is a Claude-Code Stop hook that touches `~/.claude/sessions/<date>-session.tmp`.
- In v5 chat.ipynb the equivalent moment is "user clicks Save / closes notebook".
- v5 already implements **explicit auto-save** (per Wave-5 LF doc: _"v5 has explicit Save button; auto-save already implemented"_).
- LF's session-end.sh creates a Markdown session log; v5's auto-save persists conversation+context to S3 / .ipynb.

**Verdict**: Not a deferred feature — it is **NOT APPLICABLE** to v5 architecture. The functional outcome (persist session state on stop) is **already implemented in v5.0.1 via auto-save**, just at a different architectural layer. Recommendation: **rewrite Wave-5 #4 status from "DEFER to v5.0.2" → "NOT APPLICABLE — equivalent already in v5.0.1 auto-save (different layer)"**. This removes the no-deferrals violation.

---

## 8. SUMMARY

- **29 files scanned** (25 hooks + 2 scripts + 2 root). Zero `tools/` directory.
- **Prior Wave-5 5-pattern claim VERIFIED**: cso-check, task-granularity-check, tool-failure-detect, session-end, skill-promotion all present and behave as documented.
- **0 NEW runtime patterns missed**. One DOCTRINE pattern (red-team-scan.sh) worth crediting in v5 build process documentation.
- **smart-approval.sh** is a previously-unsurfaced 181-LOC ambiguous-command Codex-judge — correctly out-of-scope for Bedrock-only.
- **pre-bash-safety.sh** v4.10.7/v4.10.8 confirmed as **exact mirror** of v4 `DANGEROUS_PATTERNS` (already in v5 baseline) — covers cloud, k8s, IaC, PaaS, storage, persistence, DB CLI, redirect, lockout, obfuscation (base64\|sh, xxd\|sh, eval $(curl), eval \`wget\`, hex-chain).
- **No-deferrals violation surfaced**: session-end.sh "DEFER to v5.0.2" should be re-classified to "NOT APPLICABLE — auto-save already covers it in v5.0.1".
- **Plan v3 Block K already correctly absorbs** the 4 active LF patterns (3 inherited hooks via documentation + 1 new /promote-to-skill command). No Plan-v3 changes required from this slice.
- **AXIS-C coverage**: LF hooks/scripts contribute 4 inherited patterns + 1 doctrine pattern; remaining 24 are correctly out-of-scope (host-side, Codex-required, or Claude-Code-platform-specific).

**RESULT**: This deep-scan **CONFIRMS** the prior Wave-5 finding with zero net new adoptions and one corrective re-classification (session-end.sh). Plan v3 Block K is sufficient.
