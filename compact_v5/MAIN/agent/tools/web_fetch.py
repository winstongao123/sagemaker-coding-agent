"""V5 tools/web_fetch.py — DISABLED 2026-05-03 per user decision.

Originally Block T tool (PORT_LOG #103, ADR-038). v5.0.1 ships WITHOUT
this tool active because v5's single-user SageMaker context is typically
VPC-isolated with no outbound HTTP — shipping web_fetch as dead code
creates a security/SSRF surface for zero benefit.

Constraint #1 (v4.10.10 baseline) is honored as DECISION-DROP-PER-USER
in V5_RUNNABLE_PORT_LOG.md (NOT silent narrowing — explicit user override
on 2026-05-03).

Re-enable steps (single-user override):
  1. Delete the `raise NotImplementedError(...)` below.
  2. Restore the import + `_web_fetch._register()` lines in
     tools/__init__.py (currently commented `# DISABLED 2026-05-03`).
  3. Verify SSRF-block coverage in tests/integration/test_block_t.py
     still applies in your network context.

The implementation below the guard is retained verbatim for forward
re-enable; it is unreachable code by design.
"""
from __future__ import annotations

raise NotImplementedError(
    "web_fetch is disabled in v5.0.1 (user decision 2026-05-03). "
    "v4 had it; v5 single-user SageMaker context typically has no outbound HTTP. "
    "Re-enable: register in tools/__init__.py + remove this guard."
)


# =====================================================================
# UNREACHABLE — kept for forward re-enable. See module docstring above.
# =====================================================================

import re
from typing import Any, Dict, List, Optional

from .registry import build_tool, register


def _html_to_markdown_lite(html: str) -> str:
    text = html
    for level in range(1, 4):
        pattern = re.compile(rf"<h{level}[^>]*>(.*?)</h{level}>", re.IGNORECASE | re.DOTALL)
        text = pattern.sub(lambda m: "\n" + ("#" * level) + " " + re.sub(r"<[^>]+>", "", m.group(1)).strip() + "\n", text)
    text = re.sub(r"<pre[^>]*>(.*?)</pre>", lambda m: "\n```\n" + re.sub(r"<[^>]+>", "", m.group(1)) + "\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_SSRF_BLOCKED_HOSTS = frozenset({
    "localhost", "127.0.0.1", "::1", "0.0.0.0",
    "169.254.169.254",
    "metadata.google.internal",
    "metadata",
    "kubernetes.default",
    "kubernetes.default.svc",
})


def _is_ssrf_blocked(url: str) -> bool:
    import urllib.parse
    import ipaddress

    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower().strip().rstrip(".")
        if not host:
            return True
        if host in _SSRF_BLOCKED_HOSTS:
            return True
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        except ValueError:
            pass
    except Exception:
        return True
    return False


def _web_fetch_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    url = str(args.get("url") or "").strip()
    if not url:
        return "Error: url is required"
    if not (url.startswith("http://") or url.startswith("https://")):
        return "Error: url must start with http:// or https://"
    if _is_ssrf_blocked(url):
        return f"Error: URL blocked (private/internal/metadata host): {url}"
    timeout = int(args.get("timeout_s") or 15)
    try:
        import requests
    except ImportError:
        return "Error: requests not installed; install via `pip install requests`"
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=False, stream=True)
        if resp.status_code < 200 or resp.status_code >= 300:
            return (
                f"Error: HTTP {resp.status_code} (redirects disabled for SSRF safety; "
                f"resolve manually if intended)"
            )
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
    except Exception as exc:
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
        requires_approval=True,
        should_defer=True,
        max_result_size_chars=50000,
    ))
