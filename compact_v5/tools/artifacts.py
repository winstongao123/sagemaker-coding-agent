"""Helpers for user-facing generated artifacts.

Runtime state stays under CONFIG.workspace. User deliverables created without an
explicit project workspace should land in a clear user folder instead of inside
the compact_v5 runtime package.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional


DELIVERABLE_EXTENSIONS = {
    ".csv",
    ".docx",
    ".html",
    ".ipynb",
    ".json",
    ".md",
    ".pdf",
    ".png",
    ".txt",
    ".xlsx",
}


def user_artifacts_root(config: Any = None) -> str:
    if config is None:
        from runtime.config import CONFIG as config
    root = str(
        getattr(config, "user_artifacts_root", "")
        or os.path.join(os.path.expanduser("~"), "sageagent_workspace")
    )
    return os.path.abspath(os.path.expanduser(root))


def _looks_like_runtime_workspace(path: str) -> bool:
    normalized = os.path.abspath(path or os.getcwd()).replace("\\", "/").lower()
    base = os.path.basename(normalized.rstrip("/"))
    if base in {"compact_v5", "compact_v5_ship"}:
        return True
    return normalized.endswith("/sagemaker-coding-agent/compact_v5")


def should_rebase_user_artifact(filepath: str, config: Any = None) -> bool:
    if not filepath or os.path.isabs(filepath):
        return False
    ext = Path(filepath).suffix.lower()
    if ext and ext not in DELIVERABLE_EXTENSIONS:
        return False
    if config is None:
        from runtime.config import CONFIG as config
    return _looks_like_runtime_workspace(str(getattr(config, "workspace", os.getcwd())))


def resolve_user_artifact_path(filepath: str, config: Any = None) -> str:
    if should_rebase_user_artifact(filepath, config=config):
        return os.path.join(user_artifacts_root(config), filepath)
    return filepath


def is_ascii_only_request(context: Optional[Dict[str, Any]] = None) -> bool:
    return bool(isinstance(context, dict) and context.get("ascii_only"))


def ascii_contract_error(text: str) -> str:
    for idx, ch in enumerate(text or ""):
        if ord(ch) >= 128:
            return (
                "Error: ASCII-only output was requested, but generated content "
                f"contains non-ASCII character U+{ord(ch):04X} at offset {idx}. "
                "Replace emoji, arrows, and box-drawing characters with plain ASCII."
            )
    return ""


def record_artifact(path: str, *, kind: str = "file", context: Optional[Dict[str, Any]] = None) -> None:
    try:
        from runtime.state import STATE

        STATE.append_artifact(path=path, kind=kind, source_tool=(context or {}).get("tool_name", ""))
    except Exception:
        pass


def recent_artifacts(limit: int = 8) -> List[Dict[str, Any]]:
    try:
        from runtime.state import STATE

        return STATE.load_artifacts(limit=limit)
    except Exception:
        return []
