# compact_v2 Review (Post-fix Audit)

Date: 2026-02-13
Scope: `compact_v2` vs practical OpenCode parity for single-user SageMaker usage.

## What I Re-Checked
- Syntax: `python -m py_compile sagemaker_agent.py`
- Tests: `pytest` + `unittest` on `compact_v2/tests`
- Runtime probes for critical paths:
  - `python_exec` import path
  - `web_fetch` SSRF guards
  - command expansion flow

## Current Verification Result
- `py_compile`: pass
- `pytest`: 82 passed
- `unittest`: 25 passed
- Confirmed fixed:
  - `python_exec` runtime import hook no longer crashes on normal imports
  - `web_fetch` now blocks private/internal hosts and caps response size
  - SageMaker approval flow no longer deadlocks (auto-approve behavior)
  - session load/saves and deep-copy protections remain in place

## Confirmed Improvements Implemented
1. `python_exec` runtime hook fix
- File: `sagemaker_agent.py` around `_PYTHON_EXEC_PREAMBLE`
- Change: hook support symbols are preserved so import allowlist works at runtime.

2. `web_fetch` hardening
- File: `sagemaker_agent.py` `tool_web_fetch`
- Change: private/internal host blocking (`_is_private_ip`), redirect blocking, and max bytes (`_WEB_FETCH_MAX_BYTES`).

3. SageMaker approval UX fix
- File: `sagemaker_agent.py` `request_approval`
- Change: SageMaker detection path auto-approves instead of blocking the run.

4. Tests expanded and passing
- Files: `tests/test_security_manager.py`, `tests/test_security_integration.py`, `tests/test_operational_controls.py`, `tests/test_v2_features.py`

## Remaining Gaps / Edge Cases

### A) Recommended to Fix (real gap)
1. Command-level `agent` hint is recorded but not actually enforced for execution
- Evidence:
  - Hint is stored: `ui_state["_cmd_agent_type"]` after command expansion.
  - No subsequent usage to force dispatch through `task` / sub-agent routing.
- Impact:
  - `/command` with configured `agent` may behave like normal prompt expansion only.
- Priority: Medium (functionality parity gap).

### B) Optional for Your Single-User SageMaker Setup
1. Approval model in SageMaker is auto-approve when toggle is ON
- This is intentional to avoid unclickable widget deadlock in SageMaker kernels.
- For your usage (single operator), acceptable.
- For shared/multi-user notebooks, not sufficient as a control boundary.

2. No hard OS/container isolation in standard SageMaker Studio kernels
- If Docker daemon is unavailable, execution is local-process policy sandboxing.
- For personal controlled use, acceptable with guardrails.
- For stricter enterprise controls, run in a hardened container/runtime profile.

### C) Cosmetic / UX Polish (non-blocking)
1. Some text symbols appear mojibake in UI status/system strings (encoding artifacts).
- Impact: readability only.
- Priority: Low.

## Practical Readiness (Your Target Context)
- For single-user SageMaker coding assistant: **Good / usable now**.
- For shared enterprise production with strict isolation/audit requirements: **Needs infra hardening**, not only Python-code changes.

## OpenCode Parity (Pragmatic)
- Core coding workflow parity (your scope): high and improved significantly.
- Intentional non-parity accepted by your constraints:
  - full MCP ecosystem breadth
  - strict runtime/container isolation everywhere
  - full TUI behavior parity

## Suggested Next (if you want V4.1)
1. Wire `ui_state["_cmd_agent_type"]` into send flow so command config can force `task` sub-agent type (`plan`/`build`/etc.).
2. Clean mojibake text literals in UI messages.
3. Add one integration test for command->agent dispatch path.

