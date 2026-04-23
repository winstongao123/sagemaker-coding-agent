# CHANGELOG — V4.9.2 (2026-04-23)

## Summary

Documentation alignment + minimum-ship zip profile. No behavioural change. Closes the three doc gaps surfaced by the v4.9.1 production-readiness scan (D1, D2, D3) and trims the shipping bundle to runtime essentials only.

## Changes

### 1. Doc alignment — `/unskill` documented everywhere

All three places where slash commands are listed now include `/unskill`:

- **`USER_GUIDE.md`** command table: added row for `/unskill <name>` with its sticky-deactivation semantics. Updated the `/skill use` and `/skill clear` rows to mention sticky behaviour.
- **`chat.md`** slash-commands table: added "Deactivate one skill (sticky)" row.
- **`SYSTEM_PROMPT`** `# Commands` line ([sagemaker_agent.py:6629](compact_v4/MAIN/agent/sagemaker_agent.py)): added `/skills`, `/skill use`, `/skill clear`, `/unskill` so the agent's own self-knowledge is complete.

This is essential because previously the agent could be asked "how do I deactivate just one skill?" and answer "use `/skill clear`" — wrong. With v4.9.2 it will correctly recommend `/unskill <name>`.

### 2. Minimum-ship zip profile

`_rebuild_zip.py` tightened to ship only what's needed to RUN the agent in a SageMaker notebook environment.

**Result:** `compact_v4.zip` shrunk from 40 files / 321 KB (v4.9.1) → **25 files / 239 KB** (v4.9.2). 25% size reduction, dev clutter removed.

**Dropped (dev-only, not needed in production):**
- All `test_*.py` files (20+ tests across `MAIN/agent/` and `MAIN/tests/`)
- `TEST_LOG.md`, `v3_architecture.html`, `V4_NOTES.md`
- `docs/V4_*.md` (audit/internal design docs)
- `.gitignore`, `__pycache__/`, `.pytest_cache/`, `.snapshots/`, `.code_index/`, `.git/`
- `_rebuild_zip.py` (the meta tool itself)

**Kept (runtime essentials):**
- `MAIN/agent/sagemaker_agent.py` (the agent)
- `MAIN/agent/chat.ipynb` (entry notebook)
- `MAIN/agent/USER_GUIDE.md` (full user docs — chat.md md-companion of the notebook is excluded since it duplicates this file)
- `MAIN/agent/memory.md` (auto-loaded, even if empty)
- `MAIN/agent/skills/<all skill files>` including `clara/prompts/*` and `clara/FULL_REVIEW.md`
- `MAIN/changelogs/CHANGELOG_v4.X.X.md` (release context)
- `CHANGELOG.md` (top-level index)

### 3. Version bump

`__version__`: `4.9.1` → `4.9.2`.

## Files Changed

| File | Change |
|---|---|
| `compact_v4/MAIN/agent/sagemaker_agent.py` | +1 line in `# Commands` SYSTEM_PROMPT block, version bump |
| `compact_v4/MAIN/agent/USER_GUIDE.md` | +1 row in command table, +1 line in workflow block |
| `compact_v4/MAIN/agent/chat.md` | +1 row in slash-commands table |
| `compact_v4/_rebuild_zip.py` | Tighter exclude lists + minimum-ship profile docstring |
| `compact_v4/compact_v4.zip` | Rebuilt (25 files, 239 KB) |
| `compact_v4/MAIN/changelogs/CHANGELOG_v4.9.2.md` | NEW |
| `compact_v4/CHANGELOG.md` | v4.9.2 entry |
| `SESSION_STATE.md` | v4.9.2 entry |

## Verification

- `py_compile` / `ast.parse` / warnings-as-errors import — clean, version reports `4.9.2`
- 30/30 tests still green (11 v4.9 + 10 v4.9.1 + 9 v4.7.1)
- Zip extracted, `__version__ = "4.9.2"` confirmed inside zip
- 25 files in zip — manually counted, no powerbi, no test files, no dev artefacts

## Migration

None. v4.9.2 is doc-only + zip-shape changes. The agent behaves identically to v4.9.1 (same tool handlers, same auto-match logic, same SYSTEM_PROMPT critique-handling section). Only the agent's self-knowledge of its own commands has been completed.

If you were depending on test files being in the shipped zip (you shouldn't be), pull them from the git repo at `compact_v4/MAIN/agent/test_*.py` instead.
