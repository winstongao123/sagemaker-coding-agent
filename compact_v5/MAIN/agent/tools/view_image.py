"""Phase 4 view_image tool — REUSE v4 verbatim. NO Runnable analog.

Per ADR-010:
- Executor body is a Phase-4 minimal port of v4 `tool_view_image` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:6419`.
- Runnable's FileReadTool handles images natively (Anthropic API supports
  multimodal in `content` array). v5 keeps a dedicated tool because:
  (a) v4 has it, (b) the SageMaker chat.ipynb workflow surfaces image
  loading as an explicit user-driven action, (c) the dedicated tool name
  makes tracing / audit clearer.
- Phase 4 deliverable: validate path + size + format, return metadata
  string. The "inject image into next API call" mechanism (v4's
  `_PENDING_IMAGES` queue) is a Phase-8 query_engine concern; this
  module exposes the validated `bytes` + `media_type` so Phase 8 can
  build the Bedrock content block.

NO PORT_LOG row — no Runnable adoption (Runnable handles images via the
read tool).
"""
from __future__ import annotations

import base64
import os
from typing import Any, Dict, List, Optional

from .registry import build_tool, register
from . import _path_validation as path_security


_DESCRIPTION = """Load an image file so the model can see it visually.

Usage:
- file_path must be an absolute path to an image file (PNG, JPG, JPEG, GIF, WEBP).
- Maximum size: 20 MB.
- The image is base64-encoded and queued for inclusion in the next model turn so the model can describe / analyse it. The model is multimodal and can interpret the visual content directly.
- Approval is NOT required (read-only operation; no filesystem mutation).

WHEN to use:
- The user uploads or references a screenshot / diagram / chart and you need to see it.
- Verifying a UI rendering produced by an earlier action (e.g., a Playwright screenshot of a page just modified).

WHEN NOT to use:
- Reading text content of any file → use read_file (it handles .ipynb cells, plain text, code).
- Reading a PDF → use read_file (Phase 4 view_image is image-only)."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to a PNG / JPG / GIF / WEBP image (max 20 MB).",
        },
    },
    "required": ["file_path"],
}


_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
_MAX_IMAGE_SIZE = 20 * 1024 * 1024


# ============================================================
# Pending-images side channel for Phase 8 query_engine
# (Codex Phase-04 review finding 2 fix)
# ============================================================
# v4 has `_PENDING_IMAGES: List[Dict]` in sagemaker_agent.py around line
# 6456 — a process-global list the BedrockClient.chat() inlines into the
# next user-message content array as image blocks. v5 mirrors this so
# Phase 8's query_engine can consume queued images without a refactor.
import threading as _threading
_PENDING_IMAGES: List[Dict[str, Any]] = []
_PENDING_LOCK = _threading.Lock()


def pop_pending_images() -> List[Dict[str, Any]]:
    """Atomically drain the pending-images queue and return its contents.
    Phase 8 query_engine calls this before each `BedrockClient.chat()` call
    so any images queued by `view_image` get inlined as image content blocks
    in the next user message. Each list item is a Bedrock-shaped dict:
        {"type": "image", "source": {"type": "base64", "media_type": <m>, "data": <b64>}}
    """
    with _PENDING_LOCK:
        out = list(_PENDING_IMAGES)
        _PENDING_IMAGES.clear()
    return out


def reset_pending_images_for_tests() -> None:
    """Clear the pending queue. Tests only."""
    with _PENDING_LOCK:
        _PENDING_IMAGES.clear()


def _view_image_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    file_path = args.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return "Error: file_path is required and must be a non-empty string"

    ok, msg = path_security.validate_path(file_path)
    if not ok:
        return f"Error: {msg}"

    abs_path = path_security.resolve_path(file_path)
    if not os.path.exists(abs_path):
        return f"Error: image not found: {abs_path}"
    if not os.path.isfile(abs_path):
        return f"Error: not a file: {abs_path}"

    ext = os.path.splitext(abs_path)[1].lower()
    if ext not in _MEDIA_TYPES:
        supported = ", ".join(sorted(set(_MEDIA_TYPES.values())))
        return f"Error: unsupported format {ext!r}. Supported: {supported}"

    try:
        size = os.path.getsize(abs_path)
    except OSError as e:
        return f"Error: cannot stat image: {e}"
    if size > _MAX_IMAGE_SIZE:
        return f"Error: image too large: {size / (1024 * 1024):.1f} MB (max 20 MB)"

    try:
        with open(abs_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
    except OSError as e:
        return f"Error: cannot read image bytes: {e}"

    # Queue the Bedrock-shaped image content block for Phase 8 to consume
    # via `pop_pending_images()` before the next `BedrockClient.chat()`
    # call. Codex Phase-04 finding 2: v5 must expose a side channel
    # equivalent to v4 `_PENDING_IMAGES` (sagemaker_agent.py:6456) so
    # query_engine can inject the image into the model's next turn.
    block = {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": _MEDIA_TYPES[ext],
            "data": data,
        },
    }
    with _PENDING_LOCK:
        _PENDING_IMAGES.append(block)

    return (
        f"Image loaded for visual analysis: {abs_path} "
        f"({size:,} bytes, {_MEDIA_TYPES[ext]}). "
        f"Queued for inclusion in the next model turn."
    )


def _register():
    """Idempotent registration of view_image. See read_file.py:_register."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "view_image") is not None:
        return find_tool_by_name(all_registered(), "view_image")
    return register(build_tool(
        name="view_image",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_view_image_executor,
        is_read_only=True,
        is_destructive=False,
        is_concurrency_safe=True,
        requires_approval=False,    # Read-only image load
        # Phase 7 ADR-013: deferred. Image-loading is rare; tool_search
        # loads the schema on demand when the model needs it.
        should_defer=True,
        search_hint="load image for visual analysis",
    ))
