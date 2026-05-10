"""Zero-cost lock for PS_PS_PS_Check_v5_vs_v4.

Run from the repository root:

    py -3.11 compact_v5/docs/checks/ps_ps_ps_v5_vs_v4_zero_cost_check.py

This does not call AWS. It verifies the live production v5 UI path can render
v4-style assistant markdown, display prompt-cache/AWS-scope metrics, and keep
the S3 safety distinction correct.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "compact_v5"))

from entry import create_chat_ui  # noqa: E402
from runtime.config import CONFIG  # noqa: E402
from security.manager import SecurityManager  # noqa: E402


def main() -> None:
    CONFIG.mock_mode = True
    CONFIG.aws_bedrock_only = True
    CONFIG.model_id = "au.anthropic.claude-haiku-4-5-20251001-v1:0"

    ui = create_chat_ui(auto_display=False)
    assert hasattr(ui, "_bedrock_only_toggle")
    assert ui._bedrock_only_toggle.value is True

    ui._render_status()
    assert "Bedrock-only" in ui._mode_html.value
    assert "S3/Textract/Lambda blocked" in ui._tokens_html.value

    sample = (
        "**Option 1**\n"
        "```bash\n"
        "aws s3 ls\n"
        "```\n"
        "- one\n"
        "- two\n"
        "\n"
        "| A | B |\n"
        "|---|---|\n"
        "| 1 | 2 |\n"
        "<script>alert('x')</script>\n"
    )
    rendered = ui._render_assistant_markdown(sample, "#eee", True)
    assert "<b " in rendered
    assert "<pre " in rendered
    assert "<ul " in rendered
    assert "<table " in rendered
    assert "```bash" not in rendered
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered

    ui._bedrock_only_toggle.value = False
    assert CONFIG.aws_bedrock_only is False
    ui._render_status()
    assert "S3 list/get allowed" in ui._tokens_html.value

    mgr = SecurityManager(workspace=str(REPO))
    CONFIG.aws_bedrock_only = True
    ok, reason = mgr.validate_python(
        "import boto3\n"
        "s3 = boto3.client('s3')\n"
        "s3.list_buckets()\n"
    )
    assert not ok and "aws_bedrock_only" in reason

    ok, reason = mgr.validate_python(
        "import boto3\n"
        "br = boto3.client('bedrock-runtime')\n"
    )
    assert ok, reason
    print("ui_zero_cost_smoke=PASS")

    CONFIG.aws_bedrock_only = False
    ok, reason = mgr.validate_python(
        "import boto3\n"
        "s3 = boto3.client('s3')\n"
        "s3.delete_object(Bucket='x', Key='y')\n"
    )
    assert not ok, "S3 delete must stay blocked when Bedrock-only is off"
    print("security_zero_cost_smoke=PASS")

    print("PS_PS_PS_Check_v5_vs_v4 zero-cost UI/security lock: PASS")


if __name__ == "__main__":
    main()
