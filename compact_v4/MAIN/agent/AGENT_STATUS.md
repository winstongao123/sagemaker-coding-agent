# Agent Status

Last updated: 2026-04-29

Purpose: durable handoff state for long-running SageAgent work. Keep this file concise and current.

## Current Goal
- Build and maintain a reliable self-use SageMaker coding agent.

## Standing User Instructions
- Do not silently auto-load skills.
- Keep a clear plan and update progress during long-running work.
- Run a code diff review before calling critical changes done.
- Verify with commands and report exact results.
- Do not claim production readiness without evidence.

## Plan
- v4.10.7 destructive-command hardening shipped 2026-04-28 (commit `3fd8d51` on `sageagent/master`).
- Cross-surface propagation done same day: Claude Code global hook + Learning_Factory source-of-truth hook + OPC inherits + Codex gap documented.
- Doc/HTML/companion sweep done same day to bump every artifact to v4.10.7 (USER_GUIDE, chat.md, chat.ipynb, v3_architecture.html, HERMES_VS_CODING_AGENT.html).
- v4.10.8 obfuscation hardening + recursive folder removal hard-block shipped 2026-04-28: closes residual encoded-payload escape route + adds policy-driven folder-removal block per user instruction "I will not use the agent for folder removal".
- v4.10.9 backtick eval+downloader parity shipped 2026-04-29: closes Codex's third local-hook finding from v4.10.8 round in v4 itself. Defense-in-depth only — eval is already excluded from v4's bash allowlist; zero new false-positive risk.
- v4.10.10 `aws_bedrock_only` UI toggle shipped 2026-04-29: cell 2 of chat.ipynb now has a Bedrock-only checkbox (default ticked = strict). In-place refinements after comprehensive Codex re-review: defensive `(?i)` inline flag on Remove-Item regex + clearer cell-by-cell setup text in cell 0. Re-review after fixes: PASS (no findings). 134 destructive + 122 unit tests still green.
- v4.10.10 round 2 in-place actual-use fixes (2026-04-29): max_exec_calls_per_session 40→200, max_iteration_budget 90→600 + UI slider, CSO warnings WARNING→DEBUG, exec-limit error rewritten to tell LLM which tools still work, session_cost save/load wired correctly to TOKENS singleton (Codex caught Agent-vs-TOKENS bug). Full doc: compact_v4/docs/PS_actual_use_problems.md.

## Progress
- v4.10.7 added ~50 new `DANGEROUS_PATTERNS` (bash) covering cloud destructive subcommands, git destructive, storage/volume, persistence, DB CLI inline, system-path overwrite, perm lockout, `curl|sh`. Plus ~12 new `DANGEROUS_PYTHON` patterns (cursor.execute DROP, drop_all, dropDatabase, deleteMany, flushall, shutil.rmtree on system paths).
- HIGH_RISK_TOOLS = {bash, python_exec, task, web_fetch} confirmed excluded from `always_allow` shortcut at line 10414; "Always Approve" button hidden for these tools at line 10423.
- v4.10.8 added 6 more bash patterns (obfuscation: `base64 -d | <interp>` extended interpreter set, `xxd -r/-p | <shell>`, `od/hexdump | tr | sh`; recursive folder: `rm -r/-rf/-fr/-R/--recursive`, `rmdir`, PowerShell `Remove-Item -Recurse`) and 4 more Python patterns (folder removal: `shutil.rmtree`, `os.rmdir`, `os.removedirs`, `Path(...).rmdir()` — all blanket-blocked from `python_exec`).
- 129/129 cases pass in `test_v410_destructive_coverage.py` (up from 107). 22/22 cases pass in hook obfuscation self-test.
- Cross-surface: obfuscation patterns mirrored to `~/.claude/hooks/pre-bash-safety.sh` + `Learning_Factory/hooks/pre-bash-safety.sh`. Folder-removal block intentionally NOT in local hook (would break routine `rm -rf node_modules/`, `.next/`, `dist/`, etc.).

## Blockers And Risks
- Codex CLI has no PreToolUse hook surface — destructive-command coverage there relies on Codex's built-in sandbox + per-command approval, not the v4.10.7 mirror. Acceptable today; revisit if Codex adds hooks.
- `origin` remote on this repo is `winstongao123/sagemaker-coding-agent.git` (not the canonical `sageagent`). Always push to `sageagent` per CLAUDE.md.

## Files Changed
- `compact_v4/MAIN/agent/sagemaker_agent.py` — DANGEROUS_PATTERNS + DANGEROUS_PYTHON additions; `__version__ = "4.10.7"`.
- `compact_v4/MAIN/agent/test_v410_destructive_coverage.py` — new (107 cases).
- `compact_v4/CHANGELOG.md` — v4.10.7 entry top.
- `SESSION_STATE.md` — v4.10.7 release entry.
- `compact_v4/MAIN/agent/USER_GUIDE.md` — v4.10.7 section + title bump.
- `compact_v4/MAIN/agent/chat.md` — v4.10.7 + v4.10.6 sections + title bump.
- `compact_v4/MAIN/agent/chat.ipynb` — cell 0 markdown bumped.
- `compact_v4/MAIN/agent/v3_architecture.html` — banners bumped + new v4.10.7 card in What's New section.
- `compact_v4/docs/HERMES_VS_CODING_AGENT.html` — v4.10.7 entry added to release banner.
- `compact_v4.zip` — pending rebuild after this sweep.

## Verification
- `python compact_v4/MAIN/agent/test_v410_destructive_coverage.py` → 107/107 pass.
- LF hook self-test (`_test_destructive.sh`) → 37/37 pass.
- Ship-gate: pending re-run after zip rebuild.

## Next Step
- Rebuild `compact_v4.zip` via `_rebuild_zip.py` to pick up doc/HTML bumps, run `verify_ship_zip.py` ship-gate, commit + push to `sageagent/master`.
