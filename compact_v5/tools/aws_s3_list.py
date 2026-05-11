"""Read-only S3 inventory tool for SageMaker real-use workflows."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import build_tool, register


_DESCRIPTION = """List S3 bucket or prefix structure using read-only S3 APIs.

Usage:
- Omit `bucket` to list available bucket names.
- Provide `bucket` to list first-level prefixes and objects.
- Provide `prefix` to inspect a sub-prefix. Prefixes are separated by `/`.
- `max_items` caps returned buckets/prefixes/objects.
- If output is truncated, pass the returned `continuation_token` to fetch the
  next page.

Safety:
- This tool is read-only.
- It runs only when `CONFIG.aws_bedrock_only` is false.
- It does not expose S3 delete, put, copy, sync, policy, ACL, or admin APIs.

WHEN to use:
- User asks to list S3 buckets, folders, prefixes, files, objects, or structure.
- `aws s3` bash commands are blocked by the SageMaker bash allowlist.

WHEN NOT to use:
- Creating, deleting, copying, syncing, modifying ACL/policy, or uploading S3 data.
- Reading object content; this tool lists names only."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "bucket": {
            "type": "string",
            "description": "Optional S3 bucket name. Omit to list buckets.",
        },
        "prefix": {
            "type": "string",
            "description": "Optional prefix inside the bucket.",
        },
        "max_items": {
            "type": "integer",
            "description": "Maximum buckets/prefixes/objects to show. Default 50, max 200.",
        },
        "continuation_token": {
            "type": "string",
            "description": "Optional token returned by a previous truncated listing.",
        },
    },
    "required": [],
}


def _s3_client(context: Optional[Dict[str, Any]] = None) -> Any:
    if isinstance(context, dict) and context.get("s3_client") is not None:
        return context["s3_client"]
    import boto3

    return boto3.client("s3")


def _limit(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 50
    return max(1, min(200, parsed))


def _aws_s3_list_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    from runtime.config import CONFIG

    if bool(getattr(CONFIG, "aws_bedrock_only", False)):
        return (
            "Blocked: S3 listing is disabled because CONFIG.aws_bedrock_only=True. "
            "Turn Bedrock-only off to allow read-only S3 inventory."
        )

    bucket = str(args.get("bucket", "") or "").strip()
    if bucket.startswith("s3://"):
        bucket = bucket[5:]
    bucket = bucket.strip("/")
    prefix = str(args.get("prefix", "") or "").lstrip("/")
    max_items = _limit(args.get("max_items"))
    continuation_token = str(args.get("continuation_token", "") or "").strip()

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

    if not bucket:
        response = client.list_buckets()
        buckets = sorted(
            str(item.get("Name", ""))
            for item in response.get("Buckets", [])
            if item.get("Name")
        )
        shown = buckets[:max_items]
        if not shown:
            return "S3 buckets: (none visible to current credentials)"
        suffix = "" if len(buckets) <= max_items else f"\n... {len(buckets) - max_items} more buckets not shown"
        return "S3 buckets:\n" + "\n".join(f"- s3://{name}/" for name in shown) + suffix

    kwargs: Dict[str, Any] = {
        "Bucket": bucket,
        "Delimiter": "/",
        "MaxKeys": max_items,
    }
    if prefix:
        kwargs["Prefix"] = prefix
    if continuation_token:
        kwargs["ContinuationToken"] = continuation_token
    response = client.list_objects_v2(**kwargs)
    prefixes = [
        str(item.get("Prefix", ""))
        for item in response.get("CommonPrefixes", [])
        if item.get("Prefix")
    ]
    objects = [
        str(item.get("Key", ""))
        for item in response.get("Contents", [])
        if item.get("Key") and item.get("Key") != prefix
    ]

    lines = [f"S3 structure for s3://{bucket}/" + (prefix if prefix else "")]
    if prefixes:
        lines.append("Prefixes:")
        lines.extend(f"- s3://{bucket}/{value}" for value in prefixes[:max_items])
    if objects:
        lines.append("Objects:")
        remaining = max(0, max_items - len(prefixes[:max_items]))
        object_limit = remaining if remaining else max_items
        lines.extend(f"- s3://{bucket}/{value}" for value in objects[:object_limit])
    if not prefixes and not objects:
        lines.append("(empty or no visible objects at this prefix)")
    if response.get("IsTruncated"):
        token = str(response.get("NextContinuationToken", "") or "")
        lines.append(
            f"... output truncated at {max_items} items. "
            "Use a narrower prefix or call aws_s3_list again with "
            f"continuation_token={token!r}."
        )
    return "\n".join(lines)


def _register():
    """Idempotent registration of aws_s3_list."""
    from .registry import all_registered, find_tool_by_name

    existing = find_tool_by_name(all_registered(), "aws_s3_list")
    if existing is not None:
        return existing
    return register(build_tool(
        name="aws_s3_list",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_aws_s3_list_executor,
        is_read_only=True,
        is_concurrency_safe=True,
        requires_approval=True,
        should_defer=False,
        always_load=True,
        search_hint="s3 bucket object prefix folder inventory list structure",
    ))
