from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import tools  # noqa: F401  bootstrap built-ins
from runtime.config import CONFIG
from security import manager as security_manager
from tools.aws_s3_list import _aws_s3_list_executor
from tools.registry import PLAN_MODE_ALLOWED_TOOLS, all_registered, find_tool_by_name


class FakeS3Client:
    def list_buckets(self):
        return {"Buckets": [{"Name": "alpha"}, {"Name": "beta"}]}

    def list_objects_v2(self, **kwargs):
        assert kwargs["Bucket"] == "alpha"
        assert kwargs["Delimiter"] == "/"
        return {
            "CommonPrefixes": [{"Prefix": "logs/"}, {"Prefix": "reports/"}],
            "Contents": [{"Key": "README.txt"}, {"Key": kwargs.get("Prefix", "")}],
            "IsTruncated": False,
        }


class TruncatedFakeS3Client(FakeS3Client):
    def list_objects_v2(self, **kwargs):
        assert kwargs["ContinuationToken"] == "abc" if "ContinuationToken" in kwargs else True
        return {
            "CommonPrefixes": [{"Prefix": "logs/"}],
            "Contents": [],
            "IsTruncated": True,
            "NextContinuationToken": "next-page",
        }


def test_aws_s3_list_lists_buckets_with_fake_client():
    old = CONFIG.aws_bedrock_only
    try:
        CONFIG.aws_bedrock_only = False
        text = _aws_s3_list_executor({}, context={"s3_client": FakeS3Client()})
    finally:
        CONFIG.aws_bedrock_only = old
    assert "s3://alpha/" in text
    assert "s3://beta/" in text


def test_aws_s3_list_lists_prefixes_and_objects_with_fake_client():
    old = CONFIG.aws_bedrock_only
    try:
        CONFIG.aws_bedrock_only = False
        text = _aws_s3_list_executor({"bucket": "s3://alpha/", "max_items": 10}, context={"s3_client": FakeS3Client()})
    finally:
        CONFIG.aws_bedrock_only = old
    assert "s3://alpha/logs/" in text
    assert "s3://alpha/reports/" in text
    assert "s3://alpha/README.txt" in text


def test_aws_s3_list_truncated_output_returns_continuation_token():
    old = CONFIG.aws_bedrock_only
    try:
        CONFIG.aws_bedrock_only = False
        text = _aws_s3_list_executor(
            {"bucket": "alpha", "continuation_token": "abc"},
            context={"s3_client": TruncatedFakeS3Client()},
        )
    finally:
        CONFIG.aws_bedrock_only = old
    assert "continuation_token='next-page'" in text


def test_bedrock_only_blocks_s3_tool():
    old = CONFIG.aws_bedrock_only
    try:
        CONFIG.aws_bedrock_only = True
        text = _aws_s3_list_executor({}, context={"s3_client": FakeS3Client()})
    finally:
        CONFIG.aws_bedrock_only = old
    assert "CONFIG.aws_bedrock_only=True" in text


def test_missing_boto3_reports_actionable_error():
    import tools.aws_s3_list as mod

    original = mod._s3_client

    def missing(_context):
        raise ModuleNotFoundError("No module named 'boto3'", name="boto3")

    try:
        mod._s3_client = missing
        text = mod._aws_s3_list_executor({"max_items": 5}, context={})
    finally:
        mod._s3_client = original
    assert "boto3 is not installed" in text
    assert "SageMaker runtime" in text


def test_aws_s3_tool_registered_read_only_and_no_destructive_schema():
    tool = find_tool_by_name(all_registered(), "aws_s3_list")
    assert tool is not None
    assert tool.is_read_only is True
    assert tool.is_destructive is False
    assert tool.name in PLAN_MODE_ALLOWED_TOOLS
    schema_text = str(tool.input_schema).lower()
    for forbidden in ("delete", "put", "copy", "sync", "acl", "policy"):
        assert forbidden not in schema_text


def test_blocked_aws_s3_cli_guidance_points_to_safe_tool():
    old = CONFIG.aws_bedrock_only
    try:
        CONFIG.aws_bedrock_only = False
        ok, msg = security_manager.SECURITY.validate_command("aws s3 ls")
        ok_bare, msg_bare = security_manager.SECURITY.validate_command("aws s3")
    finally:
        CONFIG.aws_bedrock_only = old
    assert ok is False
    assert "aws_s3_list" in msg
    assert "Bedrock-only" not in msg
    assert ok_bare is False
    assert "aws_s3_list" in msg_bare


if __name__ == "__main__":
    for test in (
        test_aws_s3_list_lists_buckets_with_fake_client,
        test_aws_s3_list_lists_prefixes_and_objects_with_fake_client,
        test_aws_s3_list_truncated_output_returns_continuation_token,
        test_bedrock_only_blocks_s3_tool,
        test_missing_boto3_reports_actionable_error,
        test_aws_s3_tool_registered_read_only_and_no_destructive_schema,
        test_blocked_aws_s3_cli_guidance_points_to_safe_tool,
    ):
        test()
        print(f"{test.__name__}: PASS")
