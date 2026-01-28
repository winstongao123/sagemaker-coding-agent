#!/usr/bin/env python3
"""
Unit Tests for SageMaker Coding Agent

Run with: python -m pytest tests/test_all.py -v
Or simply: python tests/test_all.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import json


class TestBedrockClient(unittest.TestCase):
    """Test BedrockClient mock mode."""

    def test_mock_mode_initialization(self):
        """Test client initializes in mock mode."""
        from core.bedrock_client import BedrockClient

        client = BedrockClient("test-model", mock_mode=True)
        self.assertTrue(client.mock_mode)
        self.assertIsNone(client.client)

    def test_mock_chat_response(self):
        """Test mock chat returns response."""
        from core.bedrock_client import BedrockClient

        client = BedrockClient("test-model", mock_mode=True)
        response = client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            system="You are a helpful assistant"
        )

        self.assertIsNotNone(response)
        self.assertIsNotNone(response.text)
        self.assertEqual(response.stop_reason, "end_turn")

    def test_mock_tool_call_list_files(self):
        """Test mock returns tool call for list files."""
        from core.bedrock_client import BedrockClient

        client = BedrockClient("test-model", mock_mode=True)
        response = client.chat(
            messages=[{"role": "user", "content": "list files here"}],
            system="You are a helpful assistant",
            tools=[{"name": "list_dir"}]
        )

        self.assertEqual(len(response.tool_calls), 1)
        self.assertEqual(response.tool_calls[0].name, "list_dir")


class TestSecurity(unittest.TestCase):
    """Test security module."""

    def test_path_validation_within_workspace(self):
        """Test valid path within workspace."""
        from core.security import SecurityManager, SecurityConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig(workspace_root=tmpdir)
            security = SecurityManager(config)

            test_path = os.path.join(tmpdir, "test.py")
            valid, msg = security.validate_path(test_path)
            self.assertTrue(valid)

    def test_path_validation_outside_workspace(self):
        """Test path outside workspace is blocked."""
        from core.security import SecurityManager, SecurityConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig(workspace_root=tmpdir)
            security = SecurityManager(config)

            valid, msg = security.validate_path("/etc/passwd")
            self.assertFalse(valid)
            self.assertIn("outside", msg.lower())

    def test_secret_detection_api_key(self):
        """Test API key detection."""
        from core.security import SecurityManager, SecurityConfig

        config = SecurityConfig(workspace_root="/tmp")
        security = SecurityManager(config)

        content = "API_KEY=sk-1234567890abcdefghijklmnop"
        findings = security.scan_for_secrets(content)
        self.assertTrue(len(findings) > 0)

    def test_secret_detection_clean(self):
        """Test clean content has no findings."""
        from core.security import SecurityManager, SecurityConfig

        config = SecurityConfig(workspace_root="/tmp")
        security = SecurityManager(config)

        content = "def hello(): print('hello world')"
        findings = security.scan_for_secrets(content)
        self.assertEqual(len(findings), 0)

    def test_dangerous_command_blocked(self):
        """Test dangerous commands are blocked."""
        from core.security import SecurityManager, SecurityConfig

        config = SecurityConfig(workspace_root="/tmp")
        security = SecurityManager(config)

        valid, msg = security.validate_command("rm -rf /")
        self.assertFalse(valid)

    def test_safe_command_allowed(self):
        """Test safe commands are allowed."""
        from core.security import SecurityManager, SecurityConfig

        config = SecurityConfig(workspace_root="/tmp")
        security = SecurityManager(config)

        valid, msg = security.validate_command("git status")
        self.assertTrue(valid)


class TestAudit(unittest.TestCase):
    """Test audit logging."""

    def test_log_creates_entry(self):
        """Test logging creates an entry."""
        from core.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(tmpdir)
            audit.log("test_session", "test_action", "test_tool", {"param": "value"})

            entries = audit.get_session_log("test_session")
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["action"], "test_action")

    def test_sensitive_data_redacted(self):
        """Test sensitive data is redacted."""
        from core.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(tmpdir)
            audit.log("test_session", "action", parameters={"password": "secret123"})

            entries = audit.get_session_log("test_session")
            self.assertEqual(entries[0]["parameters"]["password"], "[REDACTED]")


class TestPermissions(unittest.TestCase):
    """Test permission system."""

    def test_read_tools_auto_allow(self):
        """Test read-only tools are auto-allowed."""
        from core.permissions import PermissionManager

        pm = PermissionManager()
        result = pm.check_permission("session1", "read_file", "/path/file.py")
        self.assertTrue(result.allowed)

    def test_write_tools_need_approval(self):
        """Test write tools need approval."""
        from core.permissions import PermissionManager

        pm = PermissionManager()  # No approval handler
        result = pm.check_permission("session1", "bash", "ls -la")
        self.assertFalse(result.allowed)  # Denied without handler


class TestTools(unittest.TestCase):
    """Test tool implementations."""

    def test_todo_write_and_read(self):
        """Test todo list functionality."""
        from tools.todo import todo_write, todo_read, clear_todos

        clear_todos()

        # Create mock context
        ctx = MagicMock()
        ctx.working_dir = "/tmp"

        # Write todos
        result = todo_write({
            "todos": [
                {"content": "Task 1", "activeForm": "Working on Task 1", "status": "pending"},
                {"content": "Task 2", "activeForm": "Working on Task 2", "status": "in_progress"},
            ]
        }, ctx)

        self.assertIn("Task 1", result)
        self.assertIn("Task 2", result)

        # Read todos
        result = todo_read({}, ctx)
        self.assertIn("Task 1", result)
        self.assertIn("[>]", result)  # in_progress shown as [>]


class TestConfig(unittest.TestCase):
    """Test configuration."""

    def test_config_load_default(self):
        """Test default config loads."""
        from config import AgentConfig

        config = AgentConfig()
        self.assertEqual(config.region, "ap-southeast-2")
        self.assertIsNotNone(config.primary_model)

    def test_config_save_and_load(self):
        """Test config save and load."""
        from config import AgentConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")

            config1 = AgentConfig(region="us-east-1")
            config1.save(path)

            config2 = AgentConfig.load(path)
            self.assertEqual(config2.region, "us-east-1")


class TestIntegration(unittest.TestCase):
    """Integration tests with mock mode."""

    def test_full_agent_loop_mock(self):
        """Test full agent loop in mock mode."""
        from core.bedrock_client import BedrockClient
        from core.tools import ToolRegistry

        # Create mock client
        client = BedrockClient("test-model", mock_mode=True)

        # Test a simple chat
        response = client.chat(
            messages=[{"role": "user", "content": "Hello, help me with coding"}],
            system="You are a coding assistant"
        )

        self.assertIsNotNone(response.text)
        print(f"Mock response: {response.text[:100]}...")


def run_tests():
    """Run all tests and print summary."""
    print("=" * 60)
    print("SageMaker Coding Agent - Unit Tests")
    print("=" * 60)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBedrockClient))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestAudit))
    suite.addTests(loader.loadTestsFromTestCase(TestPermissions))
    suite.addTests(loader.loadTestsFromTestCase(TestTools))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 60)
    if result.wasSuccessful():
        print("ALL TESTS PASSED!")
    else:
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
