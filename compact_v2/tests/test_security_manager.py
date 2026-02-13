import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sagemaker_agent import SecurityManager


class SecurityManagerTests(unittest.TestCase):
    def setUp(self):
        self.workspace = os.getcwd()
        self.sec = SecurityManager(self.workspace)

    def test_extract_base_command_splits_all_segments(self):
        bases = self.sec._extract_base_command("git status | grep foo && ls -la; cat README.md")
        self.assertEqual(bases, ["git", "grep", "ls", "cat"])

    def test_validate_command_blocks_disallowed_after_separator(self):
        ok, msg = self.sec.validate_command("git status; powershell -Command whoami")
        self.assertFalse(ok)
        self.assertIn("Command not allowed", msg)

    def test_validate_command_blocks_interpreter_by_default(self):
        ok, msg = self.sec.validate_command("python -c \"print(1)\"")
        self.assertFalse(ok)
        self.assertIn("Command not allowed", msg)

    def test_validate_command_blocks_docker_by_default(self):
        ok, msg = self.sec.validate_command("docker ps")
        self.assertFalse(ok)
        self.assertIn("Command not allowed", msg)

    def test_validate_command_allows_safe_command(self):
        ok, msg = self.sec.validate_command("git status")
        self.assertTrue(ok, msg)

    def test_validate_command_allows_interpreter_when_explicitly_enabled(self):
        sec = SecurityManager(self.workspace, allow_interpreters=True)
        ok, msg = sec.validate_command("python --version")
        self.assertTrue(ok, msg)

    def test_validate_python_blocks_non_allowlisted_import(self):
        ok, msg = self.sec.validate_python("import pathlib2\nprint('x')")
        self.assertFalse(ok)
        self.assertIn("Import not allowed", msg)

    def test_validate_python_blocks_dangerous_import(self):
        ok, msg = self.sec.validate_python("import subprocess\nprint('x')")
        self.assertFalse(ok)
        self.assertIn("Blocked import", msg)

    def test_validate_python_allows_safe_import(self):
        ok, msg = self.sec.validate_python("import json\nprint(json.dumps({'a': 1}))")
        self.assertTrue(ok, msg)

    def test_validate_python_blocks_from_os_import_system(self):
        ok, msg = self.sec.validate_python("from os import system\nsystem('echo x')")
        self.assertFalse(ok)
        self.assertTrue("Blocked import member" in msg or "Blocked call via imported alias" in msg)

    def test_validate_python_blocks_underscore_module_not_allowlisted(self):
        ok, msg = self.sec.validate_python("import _ctypes\nprint('x')")
        self.assertFalse(ok)
        self.assertIn("Import not allowed", msg)


if __name__ == "__main__":
    unittest.main()
