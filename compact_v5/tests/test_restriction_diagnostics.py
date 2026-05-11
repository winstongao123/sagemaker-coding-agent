from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.config import CONFIG
from security import manager as security_manager
from security.diagnostics import (
    python_exec_runtime_diagnosis,
    python_exec_security_block_diagnosis,
)
from tools.python_exec import _python_exec_executor


def _assert_contains(text, *needles):
    for needle in needles:
        assert needle in text, f"missing {needle!r} from {text!r}"


def test_bash_s3_block_names_allowlist_not_bedrock_only():
    original = CONFIG.aws_bedrock_only
    try:
        CONFIG.aws_bedrock_only = False
        ok, message = security_manager.SECURITY.validate_command("aws s3 ls")
        assert ok is False
        _assert_contains(message, "AWS S3 CLI is blocked by the bash allowlist", "aws_s3_list")
        assert "aws_bedrock_only=true" not in message
    finally:
        CONFIG.aws_bedrock_only = original


def test_python_static_import_block_names_python_sandbox():
    diagnosis = python_exec_security_block_diagnosis(
        "Import not allowed: linecache. Only approved modules are permitted.",
        aws_bedrock_only=False,
    )
    _assert_contains(diagnosis, "Python sandbox import allowlist", "Bedrock-only is OFF")


def test_python_runtime_import_block_names_python_sandbox():
    output = "[stderr]\nImportError: Security: import 'linecache' is not in the allowed modules list"
    diagnosis = python_exec_runtime_diagnosis(output, aws_bedrock_only=False)
    _assert_contains(diagnosis, "Python sandbox import allowlist", "linecache", "Bedrock-only is OFF")


def test_python_exec_static_block_includes_diagnosis():
    original = CONFIG.aws_bedrock_only
    try:
        CONFIG.aws_bedrock_only = False
        result = _python_exec_executor({"code": "import linecache\nprint('x')"})
        _assert_contains(
            result,
            "Security blocked: Import not allowed: linecache",
            "[diagnosis]",
            "Python sandbox import allowlist",
            "Bedrock-only is OFF",
        )
    finally:
        CONFIG.aws_bedrock_only = original


if __name__ == "__main__":
    test_bash_s3_block_names_allowlist_not_bedrock_only()
    test_python_static_import_block_names_python_sandbox()
    test_python_runtime_import_block_names_python_sandbox()
    test_python_exec_static_block_includes_diagnosis()
    print("restriction diagnostics smoke: OK")
