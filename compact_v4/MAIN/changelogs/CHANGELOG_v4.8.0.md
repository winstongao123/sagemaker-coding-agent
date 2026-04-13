# CHANGELOG — V4.8.0 (2026-04-13)

## Summary
Major UX and reliability release based on PS_Deep Runnable architecture research. 
8 fixes addressing user-reported issues + 5 gap closures from Runnable comparison.

## [CRITICAL] Fixes

### 1. Chat Window Resizable
- **Problem**: Chat display was fixed at 400px height, too small to read long responses
- **Fix**: Default height increased to 500px, added CSS `resize:vertical` for drag-to-resize, added Chat Height slider (200-1200px) in UI controls
- **Lines**: 7997 (render_chat), 8193 (slider widget), 7832 (ui_state init)

### 2. Stop Generating Files — Prefer Chat Answers
- **Problem**: Agent would create .md summary files instead of displaying answers in chat
- **Fix**: Added "[CRITICAL] Answer Preference" section to system prompt: prefer chat answers, only create files when explicitly requested, temp files go to `_temp/` subfolder
- **Lines**: 6546-6553 (SYSTEM_PROMPT), 7237-7249 (per-turn reminder injection)

### 3. Data Validation Accuracy (CSV/Excel)
- **Problem**: Agent said inflated row counts were "OK" when merging CSV/Excel, missing duplicate detection
- **Fix**: Added "Data Validation — CSV/Excel Accuracy" section to system prompt: validate row counts, check join logic, flag inflated results, cross-validate
- **Lines**: 6555-6562 (SYSTEM_PROMPT)

## Security Changes

### 4. wget/bash Restrictions Relaxed
- **Problem**: Agent blocked legitimate `wget` downloads and `bash` script execution (screenshot showed "environment has restrictions")
- **Fix**: Removed blanket `wget` and `curl` external download blocks. Only pipe-to-shell (`wget ... | bash`) still blocked. Added `bash`, `sh`, `wget`, `curl` to BASE_ALLOWED_COMMANDS. Removed `curl`/`wget` from NETWORK_COMMANDS.
- **Lines**: 1197-1201 (DANGEROUS_PATTERNS), 1352 (NETWORK_COMMANDS), 1379 (BASE_ALLOWED_COMMANDS)

## Budget System

### 5. Budget is Display-Only (Never Stops Execution)
- **Problem**: Budget limit would halt agent mid-task with `return msg`, losing work
- **Fix**: Budget now shows warning but agent continues. User controls stop via Stop button. Budget slider replaced with editable text input (BoundedFloatText, 0-999$).
- **Lines**: 7070-7076 (Agent.run budget check), 8112-8124 (budget widget)

## Harness Engineering Gaps (from PS_Deep Research)

### 6. Post-Compact FILE_CACHE Cleanup
- **Problem**: After full compaction, FILE_CACHE still thought pruned files were in context, causing agent to skip re-reading them
- **Fix**: Added `FILE_CACHE.clear_context()` in `Compactor.compact()` after summary+recent messages assembled
- **Lines**: 455 (Compactor.compact)

### 7. Critical Reminder Re-injection Each Turn
- **Problem**: Long conversations caused agent to drift off behavioral spec (format, verification, file generation)
- **Fix**: Inject `<system-reminder>` with critical rules into last user message before each LLM call. Does NOT modify system prompt (preserves prompt cache).
- **Lines**: 7237-7249 (before make_request)

### 8. Cache Breakage Warning Enhanced
- **Problem**: After compaction, cache miss caused cost spike with no user visibility
- **Fix**: Enhanced warning: "[⚠ Cache miss after compact — cost spike expected. Next turn rebuilds cache.]"
- **Lines**: 7310 (cache breakage detection)

## Version
- `__version__` bumped from "4.3.1" to "4.8.0"
- 79 insertions, 24 deletions across sagemaker_agent.py (9,945 lines total)

## Testing
- Python syntax check: PASS
- AST parse: PASS
- Backward compatible: budget_slider alias preserved for existing code references
