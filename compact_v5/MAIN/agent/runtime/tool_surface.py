"""Block T shared tool-surface helpers.

This module ports small Runnable utility surfaces that are used across tools
and QueryEngine dispatch:

- semantic boolean/number coercion for model-emitted string arguments;
- range file reads with a typed FileTooLargeError;
- lazy lockfile wrapper with portalocker when installed and stdlib fallback;
- API/tool/XML constants used by runtime paths.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
import time
from typing import Any, Iterator, List, Optional


MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PDF_PAGES = 100

MAX_TOOL_RESULT_MESSAGE_CHARS = 200_000
TOOL_RESULT_BUDGET_MARKER = "[truncated by tool-result message budget]"

XML_FUNCTIONS_TAG = "functions"
XML_SYSTEM_REMINDER_TAG = "system-reminder"


_TRUE_STRINGS = {"1", "true", "yes", "y", "on", "enabled"}
_FALSE_STRINGS = {"0", "false", "no", "n", "off", "disabled"}


def semantic_boolean(value: Any, default: Optional[bool] = None) -> bool:
    """Coerce model-friendly boolean spellings into bool.

    Raises ValueError for unrecognized values unless a default is supplied.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in _TRUE_STRINGS:
            return True
        if text in _FALSE_STRINGS:
            return False
    if default is not None:
        return bool(default)
    raise ValueError(f"cannot coerce {value!r} to boolean")


def semantic_number(
    value: Any,
    default: Optional[float] = None,
    *,
    integer: bool = False,
) -> float | int:
    """Coerce quoted numeric tool arguments into int/float.

    Commas are ignored so model outputs like "2,000" are accepted. Raises
    ValueError unless a default is supplied.
    """
    if isinstance(value, bool):
        if default is not None:
            return int(default) if integer else float(default)
        raise ValueError("boolean is not a number")
    try:
        if isinstance(value, str):
            stripped = value.strip().replace(",", "")
            if not stripped:
                raise ValueError("empty numeric string")
            number = float(stripped)
        elif isinstance(value, (int, float)):
            number = float(value)
        else:
            raise ValueError(f"unsupported numeric value {value!r}")
    except (TypeError, ValueError):
        if default is None:
            raise
        number = float(default)
    return int(number) if integer else number


class FileTooLargeError(Exception):
    """Raised when a file exceeds the configured read_file byte ceiling."""

    def __init__(self, path: str, size: int, max_bytes: int):
        self.path = path
        self.size = int(size)
        self.max_bytes = int(max_bytes)
        super().__init__(
            f"File too large ({self.size:,} bytes, max {self.max_bytes:,}): {path}"
        )


@dataclass(frozen=True)
class FileRangeRead:
    lines: List[str]
    total_lines: int
    file_size: int

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def read_file_in_range(
    path: str,
    *,
    offset: int = 0,
    limit: Optional[int] = None,
    max_bytes: int,
    encoding: str = "utf-8",
) -> FileRangeRead:
    """Read a line range without loading oversized files into memory."""
    size = os.path.getsize(path)
    if size > max_bytes:
        raise FileTooLargeError(path, size, max_bytes)
    start = max(0, int(offset))
    stop = None if limit is None else start + max(0, int(limit))
    selected: List[str] = []
    total = 0
    with open(path, "r", encoding=encoding, errors="replace") as handle:
        for line in handle:
            if line.endswith("\n"):
                line = line[:-1]
            if line.endswith("\r"):
                line = line[:-1]
            if total >= start and (stop is None or total < stop):
                selected.append(line)
            total += 1
    return FileRangeRead(selected, total, size)


class LazyLockFile:
    """Cross-process lockfile wrapper with lazy optional dependencies."""

    def __init__(self, path: str, timeout: float = 10.0):
        self.path = path
        self.timeout = float(timeout)
        self._handle = None
        self._portalocker = None
        self._backend = ""

    def __enter__(self) -> "LazyLockFile":
        os.makedirs(os.path.dirname(os.path.abspath(self.path)) or ".", exist_ok=True)
        self._handle = open(self.path, "a+b")
        self._handle.write(b"\0")
        self._handle.flush()
        deadline = time.monotonic() + max(0.0, self.timeout)
        try:
            import portalocker  # type: ignore
            self._portalocker = portalocker
            while True:
                try:
                    portalocker.lock(
                        self._handle,
                        portalocker.LOCK_EX | portalocker.LOCK_NB,
                    )
                    self._backend = "portalocker"
                    return self
                except Exception:
                    if time.monotonic() >= deadline:
                        self._handle.close()
                        self._handle = None
                        raise TimeoutError(
                            f"timed out acquiring lockfile: {self.path}"
                        )
                    time.sleep(0.05)
        except ImportError:
            self._portalocker = None
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    self._handle.seek(0)
                    msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
                    self._backend = "msvcrt"
                    return self
                except OSError:
                    if time.monotonic() >= deadline:
                        self._handle.close()
                        self._handle = None
                        raise TimeoutError(f"timed out acquiring lockfile: {self.path}")
                    time.sleep(0.05)
        import fcntl
        while True:
            try:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._backend = "fcntl"
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    self._handle.close()
                    self._handle = None
                    raise TimeoutError(f"timed out acquiring lockfile: {self.path}")
                time.sleep(0.05)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._handle is None:
            return
        try:
            if self._portalocker is not None:
                self._portalocker.unlock(self._handle)
            elif os.name == "nt":
                import msvcrt
                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None


def lockfile(path: str, timeout: float = 10.0) -> LazyLockFile:
    return LazyLockFile(path, timeout=timeout)


def enforce_tool_result_message_budget(
    blocks: List[dict],
    *,
    max_chars: int = MAX_TOOL_RESULT_MESSAGE_CHARS,
) -> List[dict]:
    """Clamp aggregate tool_result text within one Bedrock user message."""
    if max_chars <= 0:
        return list(blocks)
    out: List[dict] = []
    used = 0
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "tool_result":
            out.append(block)
            continue
        item = dict(block)
        text = str(item.get("content", ""))
        remaining = max_chars - used
        if remaining <= 0:
            item["content"] = TOOL_RESULT_BUDGET_MARKER
        elif len(text) > remaining:
            suffix = "\n" + TOOL_RESULT_BUDGET_MARKER
            keep = max(0, remaining - len(suffix))
            item["content"] = text[:keep] + suffix
            used = max_chars
        else:
            used += len(text)
        out.append(item)
    return out


def xml_tag(name: str, content: str) -> str:
    return f"<{name}>\n{content}\n</{name}>"


@contextmanager
def locked(path: str, timeout: float = 10.0) -> Iterator[LazyLockFile]:
    with lockfile(path, timeout=timeout) as acquired:
        yield acquired
