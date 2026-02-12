import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import sagemaker_agent as sa


class OperationalControlsTests(unittest.TestCase):
    def test_agent_rate_limit(self):
        old_limit = sa.CONFIG.max_user_messages_per_minute
        try:
            sa.CONFIG.max_user_messages_per_minute = 1
            client = sa.BedrockClient(sa.CONFIG.model_id, sa.CONFIG.region, mock_mode=True)
            agent = sa.Agent(client, session_id="rate_limit_test")
            first = agent.run("hello")
            second = agent.run("hello again")
            self.assertIn("Rate limit exceeded", second)
            self.assertIsInstance(first, str)
        finally:
            sa.CONFIG.max_user_messages_per_minute = old_limit

    def test_audit_retention_prunes_old_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_date = (datetime.now().date() - timedelta(days=90)).strftime("%Y-%m-%d")
            recent_date = datetime.now().strftime("%Y-%m-%d")
            old_path = os.path.join(tmp, f"{old_date}_oldsession.jsonl")
            recent_path = os.path.join(tmp, f"{recent_date}_recentsession.jsonl")
            with open(old_path, "w", encoding="utf-8") as f:
                f.write("{}\n")
            with open(recent_path, "w", encoding="utf-8") as f:
                f.write("{}\n")

            logger = sa.AuditLogger(tmp)
            logger.prune_old_logs(retention_days=30)

            self.assertFalse(os.path.exists(old_path))
            self.assertTrue(os.path.exists(recent_path))

    def test_compact_preserves_role_alternation_after_summary(self):
        messages = [
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a2"},
        ]
        compacted = sa.COMPACTOR.compact(messages, "sum")
        self.assertEqual(compacted[0]["role"], "assistant")
        self.assertGreaterEqual(len(compacted), 2)
        self.assertEqual(compacted[1]["role"], "user")

    def test_internal_run_does_not_count_against_user_limits(self):
        old_limit = sa.CONFIG.max_user_messages_per_minute
        try:
            sa.CONFIG.max_user_messages_per_minute = 1
            client = sa.BedrockClient(sa.CONFIG.model_id, sa.CONFIG.region, mock_mode=True)
            agent = sa.Agent(client, session_id="internal_limit_test")
            first = agent.run("hello")
            second = agent.run("internal continue", count_towards_limits=False)
            self.assertIsInstance(first, str)
            self.assertIsInstance(second, str)
            self.assertNotIn("Rate limit exceeded", second)
            self.assertEqual(agent.user_msg_count, 1)
        finally:
            sa.CONFIG.max_user_messages_per_minute = old_limit


if __name__ == "__main__":
    unittest.main()
