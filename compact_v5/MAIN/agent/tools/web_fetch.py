"""V5 tools/web_fetch.py — Block T web_fetch tool.

PORT_LOG: #103. ADR-038.

Fetches a URL and returns it as plain markdown-flavored text. Uses
`requests` (lazy import). Strips HTML to text via a minimal tag-stripper
since we don't want to pull `html2text` as a hard dep.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .registry import build_tool, register


def _html_to_markdown_lite(html: str) -> str:
    """Minimal HTML → text/markdown converter. Strips tags, preserves
    headings (H1-H3) as markdown.

    Not a full html2text replacement; v4 used html2text. v5 inlines a
    minimal version to avoid the hard dep. Headings stay as # / ## /
    ### markers; code blocks stay as triple-backtick; everything else
    flattens to plain text.
    """
    text = html
    # Headings.
    for level in range(1, 4):
        pattern = re.compile(rf"<h{level}[^>]*>(.*?)</h{level}>", re.IGNORECASE | re.DOTALL)
        text = pattern.sub(lambda m: "\n" + ("#" * level) + " " + re.sub(r"<[^>]+>", "", m.group(1)).strip() + "\n", text)
    # Code blocks.
    text = re.sub(r"<pre[^>]*>(.*?)</pre>", lambda m: "\n```\n" + re.sub(r"<[^>]+>", "", m.group(1)) + "\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
    # Paragraphs.
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    # Strip remaining tags.
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common entities.
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )
    # Collapse whitespace.
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _web_fetch_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    url = str(args.get("url") or "").strip()
    if not url:
        return "Error: url is required"
    if not (url.startswith("http://") or url.startswith("https://")):
        return "Error: url must start with http:// or https://"
    timeout = int(args.get("timeout_s") or 15)
    try:
        import requests
    except ImportError:
        return "Error: requests not installed; install via `pip install requests`"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return f"Error: {type(exc).__name__}: {exc}"
    content_type = resp.headers.get("Content-Type", "").lower()
    body = resp.text or ""
    if "html" in content_type or body.lstrip().startswith(("<!doctype", "<html")):
        return _html_to_markdown_lite(body)
    return body


_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {"type": "string"},
        "timeout_s": {"type": "integer", "default": 15},
    },
    "required": ["url"],
}


def _register():
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "web_fetch") is not None:
        return
    register(build_tool(
        name="web_fetch",
        description="Fetch a URL and return its content as plain text / markdown.",
        input_schema=_SCHEMA,
        execute=_web_fetch_executor,
        requires_approval=False,
        should_defer=True,
        max_result_size_chars=50000,
    ))
