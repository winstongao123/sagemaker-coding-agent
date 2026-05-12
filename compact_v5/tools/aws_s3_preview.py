"""Read-only bounded S3 object preview tool."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import build_tool, register


_DESCRIPTION = """Preview a small, read-only slice of an S3 object.

Usage:
- Provide `bucket` and `key`.
- `max_bytes` defaults to 8192 and is hard-capped at 65536.
- Uses S3 Range reads, so large objects are not downloaded in full.

WHEN to use:
- User asks to inspect, preview, sample, or investigate specific S3 files.
- Follow-up asks like "pick two files and tell me what you found" after an S3 listing.

WHEN NOT to use:
- Listing buckets/prefixes; use aws_s3_list.
- Binary object dumps or large downloads.
- Any S3 write/delete/copy/admin operation."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "bucket": {"type": "string", "description": "S3 bucket name."},
        "key": {"type": "string", "description": "Object key inside the bucket."},
        "max_bytes": {
            "type": "integer",
            "description": "Maximum bytes to preview. Default 8192, hard cap 65536.",
        },
    },
    "required": ["bucket", "key"],
}


def _s3_client(context: Optional[Dict[str, Any]] = None) -> Any:
    if isinstance(context, dict) and context.get("s3_client") is not None:
        return context["s3_client"]
    import boto3

    return boto3.client("s3")


def _max_bytes(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 8192
    return max(1, min(65536, parsed))


def _looks_binary(data: bytes) -> bool:
    if not data:
        return False
    if b"\x00" in data:
        return True
    textish = sum(1 for b in data if b in (9, 10, 13) or 32 <= b <= 126)
    return (textish / max(1, len(data))) < 0.85


def _aws_s3_preview_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    from runtime.config import CONFIG

    if bool(getattr(CONFIG, "aws_bedrock_only", False)):
        return (
            "Blocked: S3 preview is disabled because CONFIG.aws_bedrock_only=True. "
            "Turn Bedrock-only off to allow read-only S3 object preview."
        )

    bucket = str(args.get("bucket", "") or "").strip()
    if bucket.startswith("s3://"):
        bucket = bucket[5:]
    bucket = bucket.strip("/")
    key = str(args.get("key", "") or "").lstrip("/")
    max_bytes = _max_bytes(args.get("max_bytes"))
    if not bucket:
        return "Error: bucket is required"
    if not key:
        return "Error: key is required"

    try:
        client = _s3_client(context)
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", "") == "boto3":
            return (
                "Error: boto3 is not installed in this Python environment. "
                "Install boto3 in the SageMaker kernel or run in the packaged "
                "SageMaker runtime that includes the AWS SDK."
            )
        return f"Error: missing Python module while creating S3 client: {exc.name}"
    except Exception as exc:  # noqa: BLE001
        return f"Error: could not create S3 client: {type(exc).__name__}: {exc}"

    try:
        response = client.get_object(
            Bucket=bucket,
            Key=key,
            Range=f"bytes=0-{max_bytes - 1}",
        )
        body = response.get("Body")
        data = body.read() if hasattr(body, "read") else bytes(body or b"")
    except Exception as exc:  # noqa: BLE001
        return f"Error: could not preview s3://{bucket}/{key}: {type(exc).__name__}: {exc}"

    content_type = str(response.get("ContentType", "") or "unknown")
    content_range = str(response.get("ContentRange", "") or "")
    truncated = bool(content_range) or len(data) >= max_bytes
    header = [
        f"S3 preview for s3://{bucket}/{key}",
        f"Content-Type: {content_type}",
        f"Bytes read: {len(data)}",
        f"Truncated: {'true' if truncated else 'false'}",
    ]
    if content_range:
        header.append(f"Content-Range: {content_range}")
    if _looks_binary(data):
        header.append("Preview: binary or unsupported content; not dumping bytes into chat.")
        return "\n".join(header)

    text = data.decode("utf-8", errors="replace")
    if "\ufffd" in text and content_type == "unknown":
        header.append("Preview: undecodable bytes detected; showing safe replacement characters only.")
    header.append("Preview:")
    header.append(text)
    return "\n".join(header)


def _register():
    """Idempotent registration of aws_s3_preview."""
    from .registry import all_registered, find_tool_by_name

    existing = find_tool_by_name(all_registered(), "aws_s3_preview")
    if existing is not None:
        return existing
    return register(build_tool(
        name="aws_s3_preview",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_aws_s3_preview_executor,
        is_read_only=True,
        is_concurrency_safe=False,
        requires_approval=True,
        should_defer=False,
        always_load=True,
        search_hint="s3 object file preview read sample investigate",
    ))
