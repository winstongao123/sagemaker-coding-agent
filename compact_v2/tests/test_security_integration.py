import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "MAIN"))
import sagemaker_agent as sa


class SecurityIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.prev_exec_mode = sa.CONFIG.execution_mode
        sa.CONFIG.execution_mode = "local"

    def tearDown(self):
        sa.CONFIG.execution_mode = self.prev_exec_mode

    def test_tool_bash_blocks_disallowed_interpreter(self):
        out = sa.tool_bash({"command": "python -c \"print(1)\""})
        self.assertIn("Blocked:", out)

    def test_tool_bash_blocks_chained_disallowed_command(self):
        out = sa.tool_bash({"command": "git status; powershell -Command whoami"})
        self.assertIn("Blocked:", out)

    def test_tool_bash_blocks_redirection_outside_workspace(self):
        out = sa.tool_bash({"command": "echo hello > ../outside_workspace.txt"})
        self.assertIn("Blocked:", out)
        self.assertIn("redirection target", out)

    def test_tool_bash_allows_fd_duplication_redirection(self):
        out = sa.tool_bash({"command": "git status 2>&1"})
        self.assertNotIn("Blocked:", out)

    def test_tool_python_exec_blocks_from_import_system(self):
        code = "from os import system\nsystem('echo should_not_run')"
        out = sa.tool_python_exec({"code": code, "timeout": 10})
        self.assertIn("Security blocked:", out)

    def test_tool_python_exec_blocks_alias_system_call(self):
        code = "import os as o\no.system('echo should_not_run')"
        out = sa.tool_python_exec({"code": code, "timeout": 10})
        self.assertIn("Security blocked:", out)


if __name__ == "__main__":
    unittest.main()
