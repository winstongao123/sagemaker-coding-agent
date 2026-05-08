# Block I Changelog

Date: 2026-05-05

Audit pass:

- Reconstructed I-1 through I-13 from `SYNTHESIS_MASTER.md`.
- Created Block I audit artifacts.
- Patched I-12 frontmatter parser evidence:
  - bracketed CSV-like scalar list fields;
  - quoted token stripping;
  - one-level brace expansion for path globs;
  - non-string description coercion.
- Added Block I parser lock tests.
- Updated `V5_RUNNABLE_PORT_LOG.md` with row #194 for I-12.
- Updated ADR-029 to state the old parser-deferral note is superseded.
- Preserved the software-project workflow constraint: no `/project-*` commands were added.

Validation:

- Combined Block I/D/skills tests: `66 passed, 1 skipped`.
- py_compile: `PASS`.
- `scope_audit.py --block I`: `READY_TO_REVIEW_CLOSE`, 13 shipped, 0 ship-blocking rows.
- Claude review iter1: `VERDICT: APPROVE`, `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`, 0 ship-blocking rows.
- Cleaned stale ledger citation for I-13 after Claude LOW documentation note.
