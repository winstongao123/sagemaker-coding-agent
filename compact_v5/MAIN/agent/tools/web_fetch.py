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


_MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB cap (v4 parity)
_SSRF_BLOCKED_HOSTS = frozenset({
    "localhost", "127.0.0.1", "::1", "0.0.0.0",
    "169.254.169.254",  # AWS instance metadata
    "metadata.google.internal",  # GCP metadata
})


def _is_ssrf_blocked(url: str) -> bool:
    """Codex iter-1 CRITICAL fix: block private/internal hosts.

    Returns True if the URL hostname resolves to a private IP range
    (10.x / 172.16-31.x / 192.168.x / loopback) or matches a blocked
    hostname. v4 parity at sagemaker_agent.py:6799.
    """
    import urllib.parse
    import ipaddress

    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower().strip()
        if not host:
            return True
        if host in _SSRF_BLOCKED_HOSTS:
            return True
        # Try parsing as IP.
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        except ValueError:
            # Not an IP; hostname-form. Allow public DNS names.
            pass
    except Exception:
        return True  # fail-closed on parse errors
    return False


def _web_fetch_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    url = str(args.get("url") or "").strip()
    if not url:
        return "Error: url is required"
    if not (url.startswith("http://") or url.startswith("https://")):
        return "Error: url must start with http:// or https://"
    # Codex iter-1 CRITICAL fix: SSRF protection.
    if _is_ssrf_blocked(url):
        return f"Error: URL blocked (private/internal/metadata host): {url}"
    timeout = int(args.get("timeout_s") or 15)
    try:
        import requests
    except ImportError:
        return "Error: requests not installed; install via `pip install requests`"
    try:
        # Codex iter-1 CRITICAL fix: allow_redirects=False (v4 parity)
        # AND stream + 2MB read cap.
        resp = requests.get(url, timeout=timeout, allow_redirects=False, stream=True)
        # Reject non-2xx (including 3xx redirects since allow_redirects=False).
        if resp.status_code < 200 or resp.status_code >= 300:
            return (
                f"Error: HTTP {resp.status_code} (redirects disabled for SSRF safety; "
                f"resolve manually if intended)"
            )
        # Read up to _MAX_RESPONSE_BYTES.
        chunks: List[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=8192):
            chunks.append(chunk)
            total += len(chunk)
            if total > _MAX_RESPONSE_BYTES:
                return (
                    f"Error: response exceeds 2MB cap ({total} bytes; "
                    "v4 parity safety limit)"
                )
        body_bytes = b"".join(chunks)
        try:
            body = body_bytes.decode("utf-8", errors="replace")
        except Exception:
            body = body_bytes.decode("latin-1", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return f"Error: {type(exc).__name__}: {exc}"
    content_type = resp.headers.get("Content-Type", "").lower()
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
        description="Fetch a URL and return its content as plain text / markdown. SSRF-blocked + 2MB cap + no redirects.",
        input_schema=_SCHEMA,
        execute=_web_fetch_executor,
        requires_approval=True,  # Codex iter-1 CRITICAL: web_fetch is high-risk.
        should_defer=True,
        max_result_size_chars=50000,
    ))
