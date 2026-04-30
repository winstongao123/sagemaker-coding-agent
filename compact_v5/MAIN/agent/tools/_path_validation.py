"""Phase-3 path-validation stub — Phase 5 conversion to delegating shim.

Phase 3 (ADR-009) shipped this as a standalone ~80-LOC implementation of
the workspace boundary check + symlink escape detection.

Phase 5 (ADR-011) ships the full v4 `SecurityManager` in `security/manager.py`.
This module is now a **delegating shim** so the 8 Phase 3-4 tool modules
that imported `from . import _path_validation as path_security` keep
working without a touch.

The shim:
  - Imports `validate_path` and `resolve_path` from `security.manager`.
  - Re-exports them with the same names + signatures the Phase 3 stub had.

Phase 13 (final cutover) may decide to retire the shim entirely and
update the 8 tool modules to import `from security import validate_path`
directly. Until then, the indirection is harmless and preserves a
historical link from the Phase 3 boundary to the Phase 5 implementation.

If you're reading this, the actual logic lives in
`compact_v5/MAIN/agent/security/manager.py`.
"""
from __future__ import annotations

# Forward to the real implementation. `validate_path` and `resolve_path`
# in `security.manager` have the SAME signature + return contract as the
# original Phase-3 stub — that was an explicit Phase-3 decision so the
# Phase-5 swap would be a one-line import change.
from security.manager import resolve_path  # noqa: F401  (public re-export)
from security.manager import validate_path  # noqa: F401  (public re-export)
