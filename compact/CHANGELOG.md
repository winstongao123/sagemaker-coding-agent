# Changelog

## Latest

### Production hardening
- Added docker execution mode for `bash` and `python_exec`.
- Added auth gate (`/auth <token>`) with env token support.
- Added rate limits and session execution quotas.
- Added audit retention pruning.

### Security hardening
- Fixed command-chain parsing in bash validation (`|`, `;`, `&&`, `||`, `&`, newline).
- Added strict command allowlist defaults.
- Tightened Python checks:
  - AST import allowlist
  - blocked dangerous import members (`from os import system`)
  - blocked dangerous alias calls
  - runtime import hook tightened

### Testing
- Added and expanded tests under `tests/`:
  - `test_security_manager.py`
  - `test_security_integration.py`
  - `test_operational_controls.py`

## Docs refresh
- Reorganized docs for beginners.
- Added `DOCS_INDEX.md` as entry point.
- Replaced stale large markdown snapshots with concise, current references.
