"""Restriction diagnostics for tool errors.

These helpers keep user-facing blocker explanations tied to the actual
enforcement layer instead of guessing that every AWS failure is Bedrock-only.
"""
from __future__ import annotations

import re


_RUNTIME_IMPORT_RE = re.compile(
    r"ImportError:\s+Security:\s+import '([^']+)' is not in the allowed modules list"
)


def python_exec_security_block_diagnosis(message: str, *, aws_bedrock_only: bool) -> str:
    """Explain a python_exec static validation block without changing policy."""
    lowered = message.lower()
    if "import not allowed" in lowered or "blocked import" in lowered:
        return (
            "Python sandbox import allowlist blocked this code. "
            f"Bedrock-only is {'ON' if aws_bedrock_only else 'OFF'} for this run; "
            "do not report this as a Bedrock-only restriction unless the block "
            "message explicitly says aws_bedrock_only=true."
        )
    return ""


def python_exec_runtime_diagnosis(output: str, *, aws_bedrock_only: bool) -> str:
    """Explain runtime sandbox import-hook failures from captured stderr."""
    match = _RUNTIME_IMPORT_RE.search(output or "")
    if not match:
        return ""
    module_name = match.group(1)
    return (
        f"Python sandbox import allowlist blocked module '{module_name}'. "
        f"Bedrock-only is {'ON' if aws_bedrock_only else 'OFF'} for this run; "
        "do not report this as a Bedrock-only restriction unless the block "
        "message explicitly says aws_bedrock_only=true."
    )
