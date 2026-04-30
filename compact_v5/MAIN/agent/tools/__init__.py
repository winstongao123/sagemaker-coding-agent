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

# Per ADR-001 file-per-tool layout: each per-tool module exposes a
# `_register()` function that idempotently adds the tool to the global
# registry. `bootstrap_built_ins()` calls each one. We import the modules
# below so they're loadable, but registration only fires when bootstrap
# is called.
#
# Codex Phase-03 review finding 1: import-time `register(...)` was unsafe
# across `_reset_registry_for_tests()` + reimport (per-tool modules stay
# cached in sys.modules). The `_register()` + `bootstrap_built_ins()`
# pattern fixes this — tests can call `_reset_registry_for_tests()` then
# `bootstrap_built_ins()` to restore the default state.
#
# Phase 3 — core read-only tools (per ADR-009):
from . import read_file as _read_file   # noqa: F401  defines _register()
from . import grep as _grep             # noqa: F401  defines _register()
from . import glob as _glob             # noqa: F401  defines _register()
from . import list_dir as _list_dir     # noqa: F401  defines _register()
#
# Phase 4 — core mutating tools + view_image (per ADR-010):
from . import write_file as _write_file       # noqa: F401  defines _register()
from . import edit_file as _edit_file         # noqa: F401  defines _register()
from . import notebook_edit as _notebook_edit # noqa: F401  defines _register()
from . import view_image as _view_image       # noqa: F401  defines _register()
#
# Phase 5 will add: bash, python_exec
# Phase 7 will add: tool_search
# Phase 9 will add: task (sub-agent dispatch)
# Phase 10 will add: skill, skill_propose_patch, todo_*, semantic_search,
#                    create_word/excel/pdf/chart/markdown/notebook,
#                    web_fetch, ask_user


def bootstrap_built_ins():
    """Register every v5 built-in tool. Idempotent: if a tool is already
    registered, the per-module `_register()` is a no-op.

    Call sequence:
      - Once at package import time (last line of this file).
      - Test fixtures call this AFTER `_reset_registry_for_tests()` to
        restore the default tool set without process restart.

    Returns the list of tool records that exist after bootstrap (for
    test-side assertions)."""
    _read_file._register()
    _grep._register()
    _glob._register()
    _list_dir._register()
    # Phase 4 — mutating tools + view_image
    _write_file._register()
    _edit_file._register()
    _notebook_edit._register()
    _view_image._register()
    # Phase 5-13 will add their modules here as they land.
    return all_registered()


# Trigger initial registration so production `import tools` produces a
# fully populated registry (matching the Phase-2 contract: `get_tools()`
# returns the active tool list without any extra setup).
bootstrap_built_ins()
