"""Phase 3 path-validation stub.

Provides the minimal path-resolution + boundary check that the Phase 3
read-only tools need (read_file, grep, glob, list_dir). This is a
*scoped subset* of v4's `SecurityManager.validate_path` from
`compact_v4/MAIN/agent/sagemaker_agent.py`.

Phase 5 retires this module: the full v4 `security/manager.py` lands
verbatim, and the 4 tool modules will switch their imports from
`tools._path_validation` to `security.manager`. This split exists
because Phase 5 is when the full security package lands per V5_PLAN.md;
Phase 3 cannot depend on it.

What this stub COVERS:
  - Workspace boundary check (resolved path must be inside CONFIG.workspace
    or one of CONFIG.allowed_paths)
  - Symlink / `..` traversal escape detection (via realpath comparison)
  - Relative-path resolution against CONFIG.workspace

What this stub does NOT cover (Phase 5 adds):
  - 134-case destructive-command pattern matching (bash / python_exec only)
  - DANGEROUS_PYTHON regex set (python_exec only)
  - HIGH_RISK_TOOLS approval-prompt machinery
  - Audit logging
  - Output truncation

The Phase 5 ADR will document the retirement and assert v5-vs-v4
behavior parity for the path-validation portion.
"""
from __future__ import annotations

import os
from typing import List, Tuple


def resolve_path(path: str) -> str:
    """Make `path` absolute. Relative paths resolve against CONFIG.workspace
    (matching v4's `_resolve_path` at compact_v4 sagemaker_agent.py)."""
    # Lazy import: tools/* can be imported by tests before CONFIG settles.
    from runtime.config import CONFIG
    if os.path.isabs(path):
        return path
    return os.path.join(CONFIG.workspace, path)


def _allowed_roots() -> List[str]:
    """Return [workspace] + allowed_paths, all as realpath-normalized strings.

    Mirrors v4's `SecurityManager.allowed_paths` set construction. The realpath
    normalization is critical: comparing raw paths can be defeated by a symlink
    pointing outside the workspace; comparing realpath catches that.
    """
    from runtime.config import CONFIG
    roots = [os.path.realpath(CONFIG.workspace)]
    extra = CONFIG.allowed_paths or []
    for ap in extra:
        if isinstance(ap, str) and ap:
            roots.append(os.path.realpath(ap))
    return roots


def validate_path(path: str) -> Tuple[bool, str]:
    """Validate that `path` is inside the workspace or an allowed_paths root.

    Returns `(ok, msg)`:
      - `(True, "")` if the path is allowed (whether or not it currently exists)
      - `(False, "<reason>")` otherwise

    This MIRRORS v4's `SecurityManager.validate_path` contract: Phase 3 tool
    code calls this exactly the way v4 tools called the SecurityManager method,
    so swapping in the full Phase 5 implementation is a one-line import change.
    """
    if not isinstance(path, str) or not path:
        return False, "empty or non-string path"

    abs_path = resolve_path(path)
    real = os.path.realpath(abs_path)
    roots = _allowed_roots()

    # `os.path.commonpath` is the safest cross-platform containment check.
    # `startswith` on a string is unsafe when one root prefixes another (e.g.,
    # `/work` vs `/work2`). commonpath returns the largest common ancestor;
    # if it equals one of our allowed roots, `real` is inside that root.
    for root in roots:
        try:
            common = os.path.commonpath([real, root])
        except ValueError:
            # Different drives on Windows raise ValueError — that's a definite
            # "not inside this root" answer; try the next root.
            continue
        if os.path.normcase(common) == os.path.normcase(root):
            return True, ""

    workspace = roots[0]
    return False, (
        f"path outside workspace: {abs_path} (resolved {real}). "
        f"Workspace root: {workspace}. "
        f"Add the directory to CONFIG.allowed_paths if access is intentional."
    )
