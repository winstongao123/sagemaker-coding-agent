import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "MAIN"))
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

    def test_safe_exec_env_strips_common_secret_names(self):
        old_api = os.environ.get("MY_API_KEY")
        old_auth = os.environ.get("SERVICE_AUTH")
        try:
            os.environ["MY_API_KEY"] = "abc"
            os.environ["SERVICE_AUTH"] = "def"
            env = sa._safe_exec_env()
            self.assertNotIn("MY_API_KEY", env)
            self.assertNotIn("SERVICE_AUTH", env)
        finally:
            if old_api is None:
                os.environ.pop("MY_API_KEY", None)
            else:
                os.environ["MY_API_KEY"] = old_api
            if old_auth is None:
                os.environ.pop("SERVICE_AUTH", None)
            else:
                os.environ["SERVICE_AUTH"] = old_auth

    def test_get_tool_definitions_respects_allowlist(self):
        defs = sa.get_tool_definitions({"read_file", "todo_read"})
        names = {d["name"] for d in defs}
        self.assertEqual(names, {"read_file", "todo_read"})

    def test_skill_manager_lists_and_reads_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = os.path.join(tmp, "skills")
            os.makedirs(skills_dir, exist_ok=True)
            skill_path = os.path.join(skills_dir, "code_review.md")
            with open(skill_path, "w", encoding="utf-8") as f:
                f.write("# Code Review\nUse strict checks.")

            sm = sa.SkillManager(tmp, "./skills")
            listed = sm.list_skills()
            self.assertTrue(any(s["name"] == "code_review" for s in listed))

            ok, txt = sm.read_skill("code_review")
            self.assertTrue(ok)
            self.assertIn("Code Review", txt)

    def test_task_tool_runs_with_agent_type(self):
        client = sa.BedrockClient(sa.CONFIG.model_id, sa.CONFIG.region, mock_mode=True)
        agent = sa.Agent(client, session_id="task_test")
        out = agent._run_task_tool({"prompt": "List files", "subagent_type": "plan", "description": "test"}, output_fn=lambda _: None)
        self.assertIsInstance(out, str)


if __name__ == "__main__":
    unittest.main()
