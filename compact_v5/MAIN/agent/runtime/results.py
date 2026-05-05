"""Durable tool-result artifact storage.

SOFTWARE-RESULTS closes the gap where QueryEngine could truncate large
tool_result bodies without a stable way to inspect the full output later.
The store writes full result text under the workspace and returns compact,
model-visible replacement text containing a replayable reference.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


RESULT_REF_PREFIX = "sageagent-result://"
DEFAULT_REPLACEMENT_PREVIEW_CHARS = 4000


def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(str(tmp_path), str(path))
    except Exception:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def _safe_component(value: Any, default: str = "unknown") -> str:
    text = str(value or default).strip() or default
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text)[:80].strip("-") or default


def _preview(text: str, max_chars: int = DEFAULT_REPLACEMENT_PREVIEW_CHARS) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    keep_head = max(0, int(max_chars * 0.65))
    keep_tail = max(0, max_chars - keep_head - 120)
    return (
        text[:keep_head].rstrip()
        + "\n\n[... middle omitted from model-visible result ...]\n\n"
        + (text[-keep_tail:].lstrip() if keep_tail else "")
    )


@dataclass(frozen=True)
class ToolResultArtifact:
    schema: str
    result_id: str
    ref: str
    session_id: str
    tool_name: str
    tool_use_id: str
    reason: str
    char_count: int
    byte_count: int
    sha256: str
    path: str
    created_at: str


class ToolResultStore:
    """Workspace-scoped artifact store for large tool outputs."""

    _lock = threading.Lock()

    def __init__(self, workspace: Optional[str] = None, config: Any = None):
        self._workspace_override = workspace
        self._config_override = config

    @property
    def _config(self):
        if self._config_override is not None:
            return self._config_override
        from runtime.config import CONFIG as _CFG
        return _CFG

    @property
    def workspace(self) -> Path:
        root = self._workspace_override or getattr(self._config, "workspace", os.getcwd())
        return Path(root).resolve()

    @property
    def disabled(self) -> bool:
        return bool(getattr(self._config, "disable_local_traces", False))

    @property
    def root(self) -> Path:
        return self.workspace / ".sageagent_state" / "tool_results"

    @property
    def index_path(self) -> Path:
        return self.root / "index.jsonl"

    def persist(
        self,
        text: str,
        *,
        session_id: str,
        tool_name: str,
        tool_use_id: str,
        reason: str,
    ) -> Optional[ToolResultArtifact]:
        if self.disabled:
            return None
        body = str(text)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        safe_session = _safe_component(session_id, "session")
        safe_tool = _safe_component(tool_name, "tool")
        safe_tid = _safe_component(tool_use_id, "tool-use")
        result_id = f"{safe_tool}-{safe_tid}-{digest[:16]}"
        rel_path = Path(safe_session) / f"{result_id}.txt"
        abs_path = self.root / rel_path
        artifact = ToolResultArtifact(
            schema="sageagent.tool_result_artifact.v1",
            result_id=result_id,
            ref=f"{RESULT_REF_PREFIX}{safe_session}/{result_id}",
            session_id=safe_session,
            tool_name=str(tool_name or ""),
            tool_use_id=str(tool_use_id or ""),
            reason=str(reason or ""),
            char_count=len(body),
            byte_count=len(body.encode("utf-8")),
            sha256=digest,
            path=str(abs_path),
            created_at=_utc_now(),
        )
        with self._lock:
            if not abs_path.is_file():
                _atomic_write_text(abs_path, body)
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            with self.index_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(artifact), sort_keys=True) + "\n")
        return artifact

    def parse_ref(self, ref: str) -> Optional[Tuple[str, str]]:
        if not isinstance(ref, str) or not ref.startswith(RESULT_REF_PREFIX):
            return None
        tail = ref[len(RESULT_REF_PREFIX):].strip("/")
        parts = tail.split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return None
        return _safe_component(parts[0], "session"), _safe_component(parts[1], "result")

    def resolve(self, ref: str) -> Optional[Path]:
        parsed = self.parse_ref(ref)
        if parsed is None:
            return None
        session_id, result_id = parsed
        path = (self.root / session_id / f"{result_id}.txt").resolve()
        try:
            path.relative_to(self.root.resolve())
        except ValueError:
            return None
        return path

    def read(self, ref: str, *, offset: int = 0, limit: Optional[int] = None) -> str:
        path = self.resolve(ref)
        if path is None:
            return f"Error: invalid result reference: {ref}"
        if not path.is_file():
            return f"Error: result artifact not found: {ref}"
        text = path.read_text(encoding="utf-8", errors="replace")
        start = max(0, int(offset or 0))
        if limit is None:
            return text[start:]
        stop = start + max(0, int(limit))
        return text[start:stop]


RESULTS = ToolResultStore()


def build_replacement_text(original: str, artifact: ToolResultArtifact) -> str:
    preview = _preview(original)
    return (
        f"[tool_result persisted: {artifact.ref}]\n"
        f"[reason: {artifact.reason}; original_chars={artifact.char_count}; "
        f"sha256={artifact.sha256}]\n"
        f"[replay: result_replay ref=\"{artifact.ref}\"]\n\n"
        f"{preview}"
    )


def persist_tool_result_block(
    block: Dict[str, Any],
    *,
    session_id: str,
    reason: str,
    store: ToolResultStore = RESULTS,
) -> Dict[str, Any]:
    if not isinstance(block, dict) or block.get("type") != "tool_result":
        return block
    text = str(block.get("content", ""))
    artifact = store.persist(
        text,
        session_id=session_id,
        tool_name=str(block.get("_sageagent_tool_name") or ""),
        tool_use_id=str(block.get("tool_use_id") or ""),
        reason=reason,
    )
    if artifact is None:
        clean = dict(block)
        clean.pop("_sageagent_tool_name", None)
        clean.pop("_sageagent_max_result_chars", None)
        return clean
    out = dict(block)
    out["content"] = build_replacement_text(text, artifact)
    out.pop("_sageagent_tool_name", None)
    out.pop("_sageagent_max_result_chars", None)
    return out


def persist_large_tool_results(
    blocks: List[Dict[str, Any]],
    *,
    session_id: str,
    per_tool_limit: int,
    message_budget: int,
    store: ToolResultStore = RESULTS,
) -> List[Dict[str, Any]]:
    """Persist and replace any result that would otherwise be truncated.

    The per-tool limit catches single oversized outputs. The aggregate budget
    catches the subtle case where several individually-allowed outputs would
    be clamped by the Bedrock user-message budget.
    """
    total = sum(
        len(str(block.get("content", "")))
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "tool_result"
    )
    aggregate_over_budget = bool(message_budget > 0 and total > message_budget)
    out: List[Dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "tool_result":
            out.append(block)
            continue
        text = str(block.get("content", ""))
        block_limit = block.get("_sageagent_max_result_chars", per_tool_limit)
        try:
            block_limit = int(block_limit)
        except (TypeError, ValueError):
            block_limit = per_tool_limit
        over_tool = bool(block_limit > 0 and len(text) > block_limit)
        if over_tool or aggregate_over_budget:
            reasons = []
            if over_tool:
                reasons.append(f"per_tool_limit>{block_limit}")
            if aggregate_over_budget:
                reasons.append(f"message_budget>{message_budget}")
            out.append(
                persist_tool_result_block(
                    block,
                    session_id=session_id,
                    reason=",".join(reasons),
                    store=store,
                )
            )
        else:
            clean = dict(block)
            clean.pop("_sageagent_tool_name", None)
            clean.pop("_sageagent_max_result_chars", None)
            out.append(clean)
    return out


__all__ = [
    "DEFAULT_REPLACEMENT_PREVIEW_CHARS",
    "RESULTS",
    "RESULT_REF_PREFIX",
    "ToolResultArtifact",
    "ToolResultStore",
    "build_replacement_text",
    "persist_large_tool_results",
    "persist_tool_result_block",
]
