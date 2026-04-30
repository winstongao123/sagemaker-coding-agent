"""V5 tools package — public surface.

Per ADR-001 (file-per-tool layout), each tool ships in its own module and
calls `register(...)` at import time. Phase 2 lands the registry only;
Phases 3-5 import each tool's module here so registration fires.

The flat-zip ship surface (Phase 13) collapses these subpackages back to
root level next to chat.ipynb; the dev-time package hierarchy is local
discipline only.
"""
from __future__ import annotations

# Re-export the public registry surface so callers can do:
#     from tools import build_tool, register, get_tools
from .registry import (  # noqa: F401  (public re-exports)
    PLAN_MODE_ALLOWED_TOOLS,
    ToolDef,
    ToolRecord,
    all_registered,
    apply_tool_search_deferral,
    assemble_tool_pool,
    build_tool,
    find_tool_by_name,
    get_tools,
    register,
    tool_matches_name,
    unregister,
)

# Phase 3-5 will add lines like:
#     from . import read_file as _read_file       # noqa: F401  (registers on import)
#     from . import grep as _grep                 # noqa: F401
# Each per-tool module calls `register(build_tool(...))` at import time so
# `get_tools()` returns the populated list. Phase 2 leaves the registry
# empty by design — the smoke tests assert empty-state behavior.
