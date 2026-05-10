"""Runtime execution context helpers for cwd and cooperative abort signals."""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional


_CURRENT_CWD: ContextVar[Optional[str]] = ContextVar("cwd", default=None)


def current_cwd(default: Optional[str] = None) -> Optional[str]:
    """Return the active context-local cwd, falling back to default."""
    return _CURRENT_CWD.get() or default


@contextmanager
def use_cwd(path: str) -> Iterator[None]:
    """Temporarily set the context-local cwd for tool execution."""
    token = _CURRENT_CWD.set(path)
    try:
        yield
    finally:
        _CURRENT_CWD.reset(token)


def combined_abort_signal(*events: asyncio.Event) -> asyncio.Event:
    """Combine asyncio.Event abort sources into one event."""
    combined = asyncio.Event()
    if any(event.is_set() for event in events):
        combined.set()
        return combined

    async def _watch(event: asyncio.Event) -> None:
        await event.wait()
        combined.set()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return combined
    for event in events:
        loop.create_task(_watch(event))
    return combined
