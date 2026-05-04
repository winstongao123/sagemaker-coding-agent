"""File safety helpers for binary-content detection."""
from __future__ import annotations

import os
from typing import Union


BINARY_EXTENSIONS = {
    ".7z",
    ".bin",
    ".bmp",
    ".class",
    ".dll",
    ".dmg",
    ".doc",
    ".docx",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".mp4",
    ".o",
    ".obj",
    ".pdf",
    ".png",
    ".pyc",
    ".so",
    ".tar",
    ".tgz",
    ".wasm",
    ".webp",
    ".xls",
    ".xlsx",
    ".zip",
}


def is_binary_content(
    content: Union[bytes, bytearray, memoryview, str],
    *,
    filename: str = "",
    sniff_bytes: int = 8192,
) -> bool:
    """Return True for known binary extensions or NUL bytes in the sample."""
    if filename:
        ext = os.path.splitext(filename.lower())[1]
        if ext in BINARY_EXTENSIONS:
            return True
    if isinstance(content, str):
        sample = content[:sniff_bytes].encode("utf-8", errors="ignore")
    else:
        sample = bytes(content[:sniff_bytes])
    return b"\0" in sample
