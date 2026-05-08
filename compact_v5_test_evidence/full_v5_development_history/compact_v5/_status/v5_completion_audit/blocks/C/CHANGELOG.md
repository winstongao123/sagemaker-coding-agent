# Block C Changelog

Date: 2026-05-04

## Initialization

- Reconstructed Block C from `SYNTHESIS_MASTER.md:89-113`.
- Created a 19-row ledger for runtime safety gates.
- Saved baseline scope audit showing 19 ledger-missing ship blockers before implementation.

## Implementation

- Added/verified explicit SecurityManager completion-audit evidence for C-1.
- Extended the secret scanner evidence for 38 total patterns and added `SecurityManager.redact_secrets()` for C-2.
- Verified edit-file safety helpers and runtime wiring for C-3 through C-8:
  quote normalization, quote-style preservation, BOM detection, UNC guard, line-ending round trip, and staleness content fallback.
- Verified bash safety helper coverage and bash output annotations for C-9 through C-14.
- Added `runtime/file_safety.py` and wired `read_file` binary refusal for C-15.
- Added XML escaping helpers and routed `xml_tag()` content through escaping for C-16.
- Added `runtime/execution_context.py` and wired bash/python_exec cwd lookup through context-local cwd for C-17; python_exec temp files now use the same context workspace.
- Extended JSON repair with `_escape_invalid_chars_in_json_strings()` and verified QueryEngine repair wiring for C-18 and C-19.
- After Claude iter1 LOW findings, wired C-11/C-12 helper checks into `SecurityManager.validate_command()` and added runtime lock tests.
- After Claude iter1 LOW finding, wired QueryEngine abort events into tool context and made bash/python_exec consume combined abort events before launch.

## Verification

- `python -m py_compile <Block C touched files>`: PASS.
- `python -m pytest tests/integration/test_block_c.py -q`: PASS, 26 passed.
- `python -m pytest tests/unit/test_security_manager.py -q`: PASS, 69 passed and 3 skipped.
- `python -m pytest tests/integration/test_block_t.py -q`: PASS, 17 passed and 14 skipped.
- After Claude iter1 LOW fixes: `python -m pytest tests/integration/test_block_c.py -q`: PASS, 28 passed.
- After Claude iter1 LOW fixes: `python -m pytest tests/unit/test_security_manager.py -q`: PASS, 69 passed and 3 skipped.

## Postmortem

### Symptom

Block C ledger initialized with all 19 rows marked `MISSING`; local iter1 tests then showed two setup failures after adding lock tests.

### Root Cause

The ledger was intentionally initialized before evidence was collected, and the new tests constructed SecurityManager/path validation outside the repo's singleton/config pattern.

### Fix

Updated tests to build/rebuild the configured SecurityManager singleton, completed local Block C helper/runtime wiring, and wrote per-row evidence into LEDGER, PORT_LOG rows #135-#153, and ADR-049.

### Verification

The focused Block C, SecurityManager, and Block T XML regression suites pass locally. Claude iter1 produced actionable LOW findings before timing out; those findings have been fixed and require fresh scope audit plus Claude iter2 before block close.
