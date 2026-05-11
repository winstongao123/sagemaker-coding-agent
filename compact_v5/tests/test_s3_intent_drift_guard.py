from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.query_engine import QueryEngine


def _engine_for_request(text):
    engine = QueryEngine(client=object())
    engine.messages = [{"role": "user", "content": text}]
    engine._run_requested_text = text
    return engine


def test_s3_inventory_request_detected():
    assert QueryEngine._is_s3_inventory_request("list file and bucket structure of my s3")
    assert not QueryEngine._is_s3_inventory_request("list compact_v5 files")


def test_local_tree_answer_triggers_intent_guard():
    engine = _engine_for_request("list file and bucket structure of my s3")
    guard = engine._intent_drift_guard_message(
        "Here is the compact_v5 source tree: agent.py, core/, tools/, ui/."
    )
    assert "Intent-drift guard" in guard
    assert "aws_s3_list" in guard
    assert "repository inventory" in guard


def test_s3_answer_or_blocker_does_not_trigger_guard():
    good = _engine_for_request("list file and bucket structure of my s3")
    assert good._intent_drift_guard_message(
        "S3 buckets:\n- my-bucket\nPrefixes:\n- logs/\nObjects:\n- logs/a.txt"
    ) == ""

    blocked = _engine_for_request("list file and bucket structure of my s3")
    assert blocked._intent_drift_guard_message(
        "Unable to list S3 because AWS credentials were not available."
    ) == ""


if __name__ == "__main__":
    test_s3_inventory_request_detected()
    test_local_tree_answer_triggers_intent_guard()
    test_s3_answer_or_blocker_does_not_trigger_guard()
    print("s3 intent drift guard smoke: OK")
