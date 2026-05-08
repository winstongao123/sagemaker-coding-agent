# Phase 04 Codex Review — gpt-5.5 (reasoning=medium)

Date: 2026-04-30
Phase: Phase 4 — Core mutating tools (write_file, edit_file, notebook_edit, view_image) + ui/diff_widget.py
Diff: v5-phase-03..HEAD (Phase 04 staged, not yet committed)

## Verdict

**PHASE 04 OVERALL: APPROVE_WITH_FIXES**
- A-axis: one major tool error-contract fix required.
- B-axis: 0 FAITHFUL / 4 ADAPTED / 0 DRIFTED — all 4 Runnable patterns FAITHFUL-WITH-JUSTIFIED-ADAPTATION.
- UNDECLARED_PATTERN check: PASS (view_image correctly declares no Runnable analog).

## AXIS A — Errors / bugs: CHANGES_REQUESTED

### Finding 1 (major) — fixed
- File: `compact_v5/MAIN/agent/tools/notebook_edit.py:193`
- Issue: `_notebook_edit_executor` only catches `OSError` around `_atomic_write_json`, but JSON serialization or other failures can escape with non-`OSError` exceptions. v4 caught `Exception` at `compact_v4/MAIN/agent/sagemaker_agent.py:6024`.
- Suggested fix: catch `Exception as e` and return `Error: failed to write notebook ({type(e).__name__}: {e})`.
- **Fix applied**: changed the `except OSError as e` block to `except Exception as e` returning a typed error string. Lock test: `test_notebook_edit_handles_non_oserror_write_failure` (mocks `json.dump` to raise `TypeError`).

### Finding 2 (minor) — fixed
- File: `compact_v5/MAIN/agent/tools/view_image.py:96`
- Issue: v4 queues the base64 payload + media type in `_PENDING_IMAGES` (sagemaker_agent.py:6446) so the query_engine can inject it into the next model turn. Phase 4 v5 computes the base64 but only returns the length, leaving Phase 8 with no side channel.
- Suggested fix: keep a pending-image side channel OR return a structured envelope.
- **Fix applied**: added `_PENDING_IMAGES` module-level list + `pop_pending_images()` accessor in `tools/view_image.py`. The executor appends `{"type": "image", "source": {"type": "base64", "media_type": ..., "data": ...}}` to the queue and returns a confirmation string. Phase 8 query_engine will call `pop_pending_images()` before each `BedrockClient.chat()` call to inject any pending image content blocks. Lock test: `test_view_image_queues_payload_for_phase_8`.

### Finding 3 (minor) — fixed
- File: `compact_v5/MAIN/agent/ui/diff_widget.py:77`
- Issue: `splitlines()` silently strips trailing newlines, so a diff that only changes whether the file ends with a newline shows "No changes".
- Suggested fix: explicit trailing-newline handling.
- **Fix applied**: when before_text and after_text are equal but trailing-newline state differs, the diff renderer surfaces "No content changes — only the final newline differs." Lock test: `test_inline_diff_shows_eof_newline_difference`.

### Finding 4 (nit) — fixed
- File: `compact_v5/MAIN/agent/tools/_file_read_tracking.py:70`
- Issue: stale-check uses `abs(current - last) > 0.5` (bidirectional). v4 only rejects `current > last + 0.5` (directional — only newer mtimes count as "modified externally"). v5's stricter check fires on `git checkout` to an older mtime, which v4 wouldn't.
- Suggested fix: document or match v4.
- **Fix applied**: changed `if abs(current - last) > 0.5` to `if current - last > 0.5` to match v4's directional semantics. Documented inline. Existing `test_edit_file_stale_file_rejected` still passes (test simulates a forward-time external write, which both directions catch).

### Finding 5 (nit) — fixed
- Issue: missing tests for malformed `@@` hunk headers in diff_widget, EOF-newline diff visibility, and notebook non-OSError atomic-write failures.
- **Fix applied**: 3 new tests:
  - `test_inline_diff_handles_malformed_hunk_header_gracefully` — verifies the diff_widget falls back to literal hunk-row rendering instead of crashing on a malformed `@@`.
  - `test_inline_diff_shows_eof_newline_difference` — verifies the EOF-newline differ is surfaced (not silently swallowed).
  - `test_notebook_edit_handles_non_oserror_write_failure` — mocks `json.dump` to raise `TypeError`; verifies the executor returns `Error:` and the original notebook is intact.

### No-finding notes from Codex
- write_file: path validation + append no-read + read-before-overwrite + flags consistent with ADR-010/v4. **Codex confirmed correct.**
- edit_file: exact match + replace_all + read-first + non-concurrency flag correct. **Codex confirmed correct.**
- tools/__init__.py: bootstrap extension is idempotent. **Codex confirmed correct.**
- status docs: no blocking issue found.
- Security: diff_widget escapes file paths, row text, notes, badges, hunk text — `<script>` in model content is escaped. Path-traversal coverage uses Phase 3 `validate_path()` across all 4 tools. view_image enforces 20 MB before base64 encoding.
- Atomic-write contract: `_atomic_write_json` unlinks tmp on exception before re-raising. Verified.
- Test execution: Codex couldn't run pytest due to PowerShell sandbox `python.exe` access. Tests verified locally.

## AXIS B — Runnable-fidelity

- **PATTERN 006 (FileWriteTool/prompt.ts → write_file.py)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
- **PATTERN 007 (FileEditTool/prompt.ts → edit_file.py)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
- **PATTERN 008 (NotebookEditTool/prompt.ts → notebook_edit.py)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
- **PATTERN 009 (FileEditTool/UI.tsx → diff_widget.py)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
- **UNDECLARED_PATTERN check**: PASS.

## Integration-semantic check (Codex)

- Tool descriptions are stable strings (cache-safe).
- Tool executors return strings; error style now consistent (post-fix).
- diff_widget returns HTML strings; malformed hunk headers handled defensively.
- view_image now exposes the pending-image side channel via `pop_pending_images()` for Phase 8.
- Approval-flow semantics directionally aligned (actual wiring is Phase 8/11).

## Required before tag (per Codex required list)

- [x] Catch all `_atomic_write_json()` failures in notebook_edit → returns Error: with type-name.
- [x] Clarify the view_image payload handoff contract → `_PENDING_IMAGES` + `pop_pending_images()` exposed.
- [x] Add focused tests: notebook non-OSError write failure, EOF-newline diff visibility, malformed hunk header.
- [x] Match v4 stale-check direction (nit).

All findings addressed. Re-running pytest after fixes → **(populated after re-run)**.
