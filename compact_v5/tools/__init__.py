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
# Phase 5 — bash + python_exec (per ADR-011; security/ verbatim port from v4):
from . import bash as _bash                   # noqa: F401  defines _register()
from . import python_exec as _python_exec     # noqa: F401  defines _register()
#
# Phase 7 — tool_search (per ADR-013; Runnable ToolSearchTool port):
from . import tool_search as _tool_search     # noqa: F401  defines _register()
#
# Phase 9 — task tool (sub-agent dispatch, ADR-015):
from . import task as _task                   # noqa: F401  defines _register()
#

# Phase 10 — skill + skill_propose_patch (ADR-016):
from . import skill as _skill                            # noqa: F401  defines _register()
from . import skill_propose_patch as _skill_patch        # noqa: F401  defines _register()
# Block T (v5.0.1) — 11 v4 tools restored (ADR-038):
from . import v4_documents as _v4_documents              # noqa: F401  defines _register()
from . import todo as _todo                              # noqa: F401  defines _register()
from . import task_state as _task_state                  # noqa: F401  defines _register()
from . import semantic_search as _semantic_search        # noqa: F401  defines _register()
# DISABLED 2026-05-03 (user decision): web_fetch ships disabled in v5.0.1.
# v5 single-user SageMaker context is typically VPC-isolated. Importing the
# module raises NotImplementedError. To re-enable, uncomment the next line
# and the bootstrap call below + delete the raise in tools/web_fetch.py.
# from . import web_fetch as _web_fetch                    # noqa: F401  defines _register()
from . import ask_user as _ask_user                      # noqa: F401  defines _register()
# SOFTWARE-RESULTS: stable replay for persisted large tool outputs.
from . import result_replay as _result_replay            # noqa: F401  defines _register()


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
    # Phase 5 — bash + python_exec
    _bash._register()
    _python_exec._register()
    # Phase 7 — tool_search
    _tool_search._register()
    # Phase 9 — task tool (sub-agent dispatch)
    _task._register()
    # Phase 10 — skill + skill_propose_patch
    _skill._register()
    _skill_patch._register()
    # Block T (v5.0.1) — 11 v4 tools (ADR-038)
    _v4_documents._register()
    _todo._register()
    _task_state._register()
    _semantic_search._register()
    # _web_fetch._register()  # DISABLED 2026-05-03 per user decision (see import block above).
    _ask_user._register()
    _result_replay._register()
    return all_registered()


# Trigger initial registration so production `import tools` produces a
# fully populated registry (matching the Phase-2 contract: `get_tools()`
# returns the active tool list without any extra setup).
bootstrap_built_ins()
