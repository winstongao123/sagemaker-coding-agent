"""Phase 4 notebook_edit tool — REUSE v4 executor + ADAPT Runnable prompt.

Per ADR-010:
- Executor body is a Phase-4 minimal port of v4 `tool_notebook_edit` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:5921`. Atomic write (tmp file
  + rename) preserved. Insert / replace / delete actions supported.
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/NotebookEditTool/prompt.ts`.

PORT_LOG: row #008.
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from .registry import build_tool, register
from . import _path_validation as path_security


_DESCRIPTION = """Edit a single cell in an existing Jupyter notebook (.ipynb).

Usage:
- The notebook_path parameter must be an absolute path, ending with .ipynb.
- The cell_index is 0-indexed.
- action='replace': overwrite the cell at cell_index. Requires cell_type and source.
- action='insert':  add a new cell at cell_index (cell_index=-1 appends to the end). Requires cell_type and source.
- action='delete':  remove the cell at cell_index.
- cell_type must be 'code' or 'markdown'.
- Atomic write: the tool writes to a temp file and renames so a partial failure cannot corrupt the live notebook.
- Approval prompt shows a focused diff of the cell that's about to change (per V5_PLAN.md Phase 4).
- Approval is required before the change happens.

WHEN to use:
- Editing or restructuring notebook cells (e.g., adding new analysis cells, fixing markdown, replacing code).

WHEN NOT to use:
- Editing a non-notebook file → use edit_file or write_file.
- Reading a notebook → use read_file (v5 read_file flattens cells for you)."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "notebook_path": {
            "type": "string",
            "description": "Absolute path to the .ipynb file.",
        },
        "action": {
            "type": "string",
            "enum": ["replace", "insert", "delete"],
            "description": "What to do at cell_index.",
        },
        "cell_index": {
            "type": "integer",
            "description": "0-based cell position. -1 = append (insert only).",
        },
        "cell_type": {
            "type": "string",
            "enum": ["code", "markdown"],
            "description": "Required for insert/replace.",
        },
        "source": {
            "type": "string",
            "description": "Cell content. Required for insert/replace.",
        },
    },
    "required": ["notebook_path", "action", "cell_index"],
}


_VALID_ACTIONS = ("replace", "insert", "delete")
_VALID_CELL_TYPES = ("code", "markdown")


def _normalise_source(source: str) -> List[str]:
    """nbformat: cell `source` is canonical as a list of lines, each ending
    with a newline (except optionally the last). Splitting via splitlines
    + re-attaching `\n` matches the v4 convention."""
    if "\n" not in source:
        return [source]
    lines = source.splitlines(keepends=True)
    return lines


def _atomic_write_json(path: str, data: Dict) -> None:
    """Write JSON via tmp + rename so a partial failure can't corrupt the live file."""
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".nbedit_", suffix=".tmp", dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        # Cleanup tmp on failure
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _validate_args(args: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Return (action_lower, error_msg). Either error_msg is set, or action is set."""
    notebook_path = args.get("notebook_path")
    action = (args.get("action") or "").lower()
    if not isinstance(notebook_path, str) or not notebook_path:
        return None, "Error: notebook_path is required and must be a non-empty string"
    if action not in _VALID_ACTIONS:
        return None, f"Error: action must be one of {_VALID_ACTIONS}; got {action!r}"
    cell_index = args.get("cell_index")
    if not isinstance(cell_index, int):
        return None, "Error: cell_index must be an integer (use -1 to append on insert)"
    if action in ("insert", "replace"):
        ct = (args.get("cell_type") or "").lower() or None
        if ct not in _VALID_CELL_TYPES:
            return None, f"Error: cell_type must be one of {_VALID_CELL_TYPES} for insert/replace"
        if not isinstance(args.get("source"), str):
            return None, "Error: source is required and must be a string for insert/replace"
    return action, None


def _notebook_edit_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    action, err = _validate_args(args)
    if err:
        return err

    notebook_path = args["notebook_path"]
    if not notebook_path.endswith(".ipynb"):
        return f"Error: target must be a .ipynb file; got {notebook_path}"

    ok, msg = path_security.validate_path(notebook_path)
    if not ok:
        return f"Error: {msg}"

    abs_path = path_security.resolve_path(notebook_path)
    if not os.path.exists(abs_path):
        return f"Error: notebook does not exist: {abs_path}"

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
    except json.JSONDecodeError as e:
        return f"Error: notebook is not valid JSON ({e})"
    except OSError as e:
        return f"Error: cannot read notebook ({e})"

    cells = nb.get("cells")
    if not isinstance(cells, list):
        return "Error: notebook structure invalid (cells is not a list)"

    cell_index = args["cell_index"]
    n = len(cells)

    if action == "insert":
        # cell_index < 0 OR >= n => append
        if cell_index < 0 or cell_index > n:
            cell_index = n
        new_cell: Dict[str, Any] = {
            "cell_type": args["cell_type"],
            "metadata": {},
            "source": _normalise_source(args["source"]),
        }
        if args["cell_type"] == "code":
            new_cell["execution_count"] = None
            new_cell["outputs"] = []
        cells.insert(cell_index, new_cell)
        info = f"Inserted {args['cell_type']} cell at index {cell_index}; notebook now has {len(cells)} cells."
    elif action == "replace":
        if cell_index < 0 or cell_index >= n:
            return f"Error: cell_index {cell_index} out of bounds (0..{n - 1})"
        old = cells[cell_index]
        new_cell = {
            "cell_type": args["cell_type"],
            "metadata": old.get("metadata", {}) or {},
            "source": _normalise_source(args["source"]),
        }
        if isinstance(old.get("id"), str):
            new_cell["id"] = old["id"]
        if args["cell_type"] == "code":
            new_cell["execution_count"] = None
            new_cell["outputs"] = []
        cells[cell_index] = new_cell
        info = f"Replaced cell at index {cell_index} with {args['cell_type']} cell."
    else:  # delete
        if cell_index < 0 or cell_index >= n:
            return f"Error: cell_index {cell_index} out of bounds (0..{n - 1})"
        cells.pop(cell_index)
        info = f"Deleted cell at index {cell_index}; notebook now has {len(cells)} cells."

    try:
        _atomic_write_json(abs_path, nb)
    except Exception as e:
        # v4 parity (sagemaker_agent.py:6024): catch any failure (OSError,
        # JSON serialization errors, encoding issues) and surface as a
        # model-readable Error: string. The atomic-write contract guarantees
        # the original notebook is unchanged regardless of failure type.
        # Codex Phase-04 review finding 1 fix (was: except OSError only).
        return f"Error writing notebook ({type(e).__name__}: {e})"

    return info


def _register():
    """Idempotent registration of notebook_edit. See read_file.py:_register."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "notebook_edit") is not None:
        return find_tool_by_name(all_registered(), "notebook_edit")
    return register(build_tool(
        name="notebook_edit",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_notebook_edit_executor,
        is_read_only=False,
        is_destructive=True,
        is_concurrency_safe=False,
        requires_approval=True,
        # Phase 7 ADR-013: deferred. Notebook editing is rare relative
        # to file editing — tool_search loads the schema on demand.
        should_defer=True,
        search_hint="edit jupyter notebook cell",
    ))
