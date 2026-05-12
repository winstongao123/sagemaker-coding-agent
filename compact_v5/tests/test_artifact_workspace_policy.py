from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.artifacts import ascii_contract_error, resolve_user_artifact_path


def test_relative_deliverable_rebases_out_of_runtime_package():
    cfg = SimpleNamespace(
        workspace="/home/sagemaker-user/compact_v5_ship",
        user_artifacts_root="/home/sagemaker-user/sageagent_workspace",
    )

    path = resolve_user_artifact_path("S3_Structure_Diagram.md", cfg)

    assert path.replace("\\", "/").endswith(
        "/home/sagemaker-user/sageagent_workspace/S3_Structure_Diagram.md"
    )


def test_relative_source_file_stays_in_workspace():
    cfg = SimpleNamespace(
        workspace="/home/sagemaker-user/compact_v5_ship",
        user_artifacts_root="/home/sagemaker-user/sageagent_workspace",
    )

    path = resolve_user_artifact_path("notes_cli/models.py", cfg)

    assert path == "notes_cli/models.py"


def test_ascii_contract_rejects_non_ascii_when_requested():
    error = ascii_contract_error("hello " + chr(8594) + " world")
    assert "ASCII-only" in error
    assert not ascii_contract_error("hello --> world")


if __name__ == "__main__":
    test_relative_deliverable_rebases_out_of_runtime_package()
    test_relative_source_file_stays_in_workspace()
    test_ascii_contract_rejects_non_ascii_when_requested()
    print("artifact workspace policy smoke: OK")
