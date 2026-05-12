from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.query_engine import QueryEngine
from core.budget import IterationBudget
from tools import all_registered, bootstrap_built_ins


def _engine() -> QueryEngine:
    return QueryEngine(client=object(), budget=IterationBudget())


def test_s3_followup_reminder_reuses_recent_object_paths():
    qe = _engine()
    qe._run_requested_text = "pick two files to investigate and tell me what you found"
    qe.messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": (
                        "Objects:\n"
                        "- s3://bucket-a/folder/one.csv\n"
                        "- s3://bucket-a/folder/two.json\n"
                        "Prefixes:\n"
                        "- s3://bucket-a/folder/\n"
                    ),
                }
            ],
        }
    ]

    messages = [{"role": "user", "content": [{"type": "text", "text": "pick two files"}]}]
    out = qe._inject_s3_followup_reminder_if_needed(messages)
    text = "\n".join(block.get("text", "") for block in out[-1]["content"])

    assert "S3 follow-up guard" in text
    assert "s3://bucket-a/folder/one.csv" in text
    assert "s3://bucket-a/folder/two.json" in text
    assert "s3://bucket-a/folder/\n" not in text
    assert "aws_s3_preview" in text


def test_s3_followup_blocks_third_list_call_this_turn():
    bootstrap_built_ins()
    qe = _engine()
    qe._run_requested_text = "pick two files to investigate"
    qe.messages = [
        {
            "role": "user",
            "content": [{"type": "tool_result", "content": "- s3://bucket-a/a.txt"}],
        }
    ]
    qe._s3_list_calls_this_run = 2
    call = SimpleNamespace(name="aws_s3_list", id="toolu_test", input={"bucket": "bucket-a"})

    result = qe._dispatch_single_tool_call(
        call,
        tools=all_registered(),
        plan_mode=False,
        output_fn=lambda _s: None,
    )

    assert result["is_error"] is True
    assert "too many aws_s3_list calls" in result["content"]


def test_s3_truncation_guard_blocks_complete_claim():
    qe = _engine()
    qe.messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": (
                        "S3 structure for s3://bucket/\n"
                        "... output truncated at 50 items. Use continuation_token='abc'."
                    ),
                }
            ],
        }
    ]

    guard = qe._s3_truncation_guard_message("Complete. I listed all files in S3.")

    assert "S3 truncation guard" in guard


def test_status_doc_update_blocked_for_small_s3_report():
    qe = _engine()
    qe._run_requested_text = "list all files of my s3 and make an ascii diagram"

    assert qe._is_blocked_status_doc_update(
        "write_file",
        {"file_path": "AGENT_STATUS.md", "content": "done"},
    )
    qe._run_requested_text = "list all files of my s3 and update status doc"
    assert not qe._is_blocked_status_doc_update(
        "write_file",
        {"file_path": "AGENT_STATUS.md", "content": "done"},
    )


if __name__ == "__main__":
    test_s3_followup_reminder_reuses_recent_object_paths()
    test_s3_followup_blocks_third_list_call_this_turn()
    test_s3_truncation_guard_blocks_complete_claim()
    test_status_doc_update_blocked_for_small_s3_report()
    print("s3 followup discipline smoke: OK")
