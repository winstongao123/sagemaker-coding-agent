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


if __name__ == "__main__":
    unittest.main()
