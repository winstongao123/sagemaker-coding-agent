"""Shared human-readable formatting helpers for runtime/UI surfaces.

Block E+F EF-4: centralize common file size, duration, token, and cost
formatting so status widgets and runtime warnings do not drift.
"""
from __future__ import annotations


def format_file_size(num_bytes: int | float) -> str:
    """Return a compact binary-size string such as ``1.5 MB``."""
    try:
        size = float(num_bytes)
    except Exception:
        size = 0.0
    sign = "-" if size < 0 else ""
    size = abs(size)
    units = ("B", "KB", "MB", "GB", "TB")
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1
    if idx == 0:
        return f"{sign}{int(round(size))} {units[idx]}"
    return f"{sign}{size:.1f} {units[idx]}"


def format_duration(seconds: int | float) -> str:
    """Return a compact duration string from seconds."""
    try:
        total = float(seconds)
    except Exception:
        total = 0.0
    sign = "-" if total < 0 else ""
    total = abs(total)
    if total < 1:
        return f"{sign}{int(round(total * 1000))} ms"
    if total < 60:
        return f"{sign}{total:.1f} s"
    minutes = int(total // 60)
    remaining = int(round(total % 60))
    if minutes < 60:
        return f"{sign}{minutes}m {remaining}s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{sign}{hours}h {minutes}m"


def format_tokens(tokens: int | float) -> str:
    """Return token counts with thousands separators."""
    try:
        value = int(round(float(tokens)))
    except Exception:
        value = 0
    return f"{value:,} tokens"


def format_cost(usd: int | float) -> str:
    """Return a USD amount with stable precision for small costs."""
    try:
        value = float(usd)
    except Exception:
        value = 0.0
    if abs(value) < 0.01:
        return f"${value:.4f}"
    return f"${value:.2f}"
