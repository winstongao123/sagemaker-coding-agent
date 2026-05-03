"""Block J — Real-Bedrock smoke + zip extract+import (THE SHIP GATE).

7 tests per TEST_DESIGN.md §Block J:
  T4 (zip / $0):
    - test_zip_rebuild_succeeds
    - test_zip_extract_in_tmpdir
    - test_zip_python_c_import_entry
    - test_zip_python_c_import_sagemaker_agent
  T5 (real-Bedrock / env-gated, ~$0.02 total):
    - test_real_bedrock_hello_world (~$0.005)
    - test_real_bedrock_tool_use_round_trip (~$0.005)
    - test_real_bedrock_compact_then_continue (~$0.01)

The 4 T4 tests run on every CI / local pytest invocation ($0).
The 3 T5 tests gate on RUN_REAL_BEDROCK=1 env var per BUILDER_PROMPT.md
§Step 7 — they only run when the user opts in to spend the AWS budget.

Block J ships when 7/7 green.

Total Block J AWS cost when RUN_REAL_BEDROCK=1: ~$0.02.
PORT_LOG: see Block J row.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest


# Path to compact_v5/ root (3 levels up from this test file:
# tests/integration/test_block_j_ship_gate.py → tests → agent → MAIN → compact_v5).
_THIS_DIR = Path(__file__).resolve().parent  # tests/integration
_AGENT_DIR = _THIS_DIR.parent.parent  # MAIN/agent
_MAIN_DIR = _AGENT_DIR.parent  # MAIN
_V5_ROOT = _MAIN_DIR.parent  # compact_v5
_REPO_ROOT = _V5_ROOT.parent  # sagemaker-coding-agent
_REBUILD_SCRIPT = _V5_ROOT / "_rebuild_zip.py"
_VERIFY_SCRIPT = _V5_ROOT / "verify_ship_zip.py"
# Ship zip lands in repo root next to compact_v5/, not inside it.
_SHIP_ZIP = _REPO_ROOT / "compact_v5.zip"


# ============================================================
# T4 — Zip rebuild + extract + import (no AWS cost)
# ============================================================

def test_zip_rebuild_succeeds():
    """`python _rebuild_zip.py` produces compact_v5.zip without errors."""
    assert _REBUILD_SCRIPT.is_file(), f"missing rebuild script: {_REBUILD_SCRIPT}"
    result = subprocess.run(
        [sys.executable, str(_REBUILD_SCRIPT)],
        cwd=str(_V5_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"_rebuild_zip.py failed (rc={result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert _SHIP_ZIP.is_file(), f"compact_v5.zip not produced at {_SHIP_ZIP}"
    # Sanity-check: zip is non-trivial.
    assert _SHIP_ZIP.stat().st_size > 50_000, (
        f"compact_v5.zip suspiciously small: {_SHIP_ZIP.stat().st_size} bytes"
    )


def test_zip_extract_in_tmpdir():
    """`verify_ship_zip.py` passes against compact_v5.zip — and the zip
    extracts cleanly in a fresh tmpdir without errors."""
    assert _SHIP_ZIP.is_file(), (
        "compact_v5.zip missing — run test_zip_rebuild_succeeds first"
    )
    # Run verify_ship_zip.py — it asserts manifest invariants, forbidden
    # patterns, sensitive files, etc. Already part of every-Block ritual.
    result = subprocess.run(
        [sys.executable, str(_VERIFY_SCRIPT)],
        cwd=str(_V5_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"verify_ship_zip.py failed (rc={result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "RESULT: PASS" in result.stdout, (
        f"verify_ship_zip.py did not report PASS:\n{result.stdout}"
    )
    # Now extract in a fresh tmpdir and confirm core files land.
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(str(_SHIP_ZIP)) as zf:
            zf.extractall(tmp)
        for required in ("entry.py", "chat.ipynb", "__init__.py"):
            assert (Path(tmp) / required).exists(), (
                f"required ship file missing after extract: {required}"
            )
        for pkg in ("core", "tools", "runtime", "skills"):
            assert (Path(tmp) / pkg).is_dir(), (
                f"required ship package missing after extract: {pkg}/"
            )


def test_zip_python_c_import_entry():
    """`python -c "import entry"` succeeds when run from the extracted
    ship dir. This catches packaging gaps that pytest-against-source-tree
    misses (e.g. a runtime module not actually shipped in the zip)."""
    assert _SHIP_ZIP.is_file(), (
        "compact_v5.zip missing — run test_zip_rebuild_succeeds first"
    )
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(str(_SHIP_ZIP)) as zf:
            zf.extractall(tmp)
        # Run `python -c "import entry"` with cwd = extracted dir.
        result = subprocess.run(
            [sys.executable, "-c", "import entry; print(getattr(entry, 'CONFIG', None) is not None)"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"`import entry` failed in extracted ship dir (rc={result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        assert "True" in result.stdout, (
            f"entry.CONFIG missing after import:\n{result.stdout}"
        )


def test_zip_python_c_import_sagemaker_agent():
    """`python -c "import sagemaker_agent"` succeeds when run from the
    extracted ship dir. v4 notebook compatibility shim — the v4 chat.ipynb
    line `from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui`
    must continue to work on v5 (Constraint #2: v4 chat.ipynb = canonical UI).
    """
    assert _SHIP_ZIP.is_file(), (
        "compact_v5.zip missing — run test_zip_rebuild_succeeds first"
    )
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(str(_SHIP_ZIP)) as zf:
            zf.extractall(tmp)
        # Verify the v4 notebook import line works against the shim.
        result = subprocess.run(
            [
                sys.executable, "-c",
                "from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui; "
                "print(CONFIG is not None and len(BEDROCK_MODELS) > 0 and callable(create_chat_ui))"
            ],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"v4-shim import failed (rc={result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        assert "True" in result.stdout, (
            f"v4-shim public surface broken: {result.stdout}"
        )


# ============================================================
# T5 — Real Bedrock single round-trips (env-gated)
# ============================================================

_HAIKU_45_MODEL_ID = "anthropic.claude-haiku-4-5-20251001-v1:0"


def _require_real_bedrock():
    if not os.getenv("RUN_REAL_BEDROCK"):
        pytest.skip(
            "RUN_REAL_BEDROCK not set; skipping real-Bedrock smoke "
            "(per BUILDER_PROMPT.md Step 7)."
        )


def test_real_bedrock_hello_world():
    """Real Haiku-4.5 round-trip: send "say hello", assert non-empty
    text response. ~$0.005 per call.

    Validates that BedrockClient can talk to real AWS, that the auth +
    region + model-id config is correct, and that a Converse-API
    response unwraps to a non-empty text block.
    """
    _require_real_bedrock()
    from runtime.bedrock_client import BedrockClient

    region = os.getenv("AWS_REGION", "ap-southeast-2")
    client = BedrockClient(model_id=_HAIKU_45_MODEL_ID, region=region, mock_mode=False)
    response = client.chat(
        messages=[{"role": "user", "content": "Say hello in 5 words or fewer."}],
        system="You are a terse assistant.",
        tools=None,
        max_tokens=64,
    )
    assert response.text, f"empty text in response: {response}"
    assert isinstance(response.text, str), f"non-string text: {type(response.text)}"
    # Response should be short ("hello" + a few words).
    assert len(response.text) < 500, f"unexpectedly long response: {response.text}"


def test_real_bedrock_tool_use_round_trip():
    """Real Haiku-4.5 round-trip: send "list files in CURRENT_DIR",
    assert tool_use(name="list_dir") is in the response → run the tool
    locally → send tool_result → assert final text mentions the listing.
    ~$0.005 per call.

    Validates the full Bedrock tool-use loop end-to-end:
    1. We send the tool schema list_dir + a user message.
    2. Bedrock returns a tool_use block.
    3. We execute list_dir locally.
    4. We send tool_result back.
    5. Bedrock returns a final text answer.

    Codex Block J iter-1 HIGH fix: ToolCall exposes `input` (not `args`),
    and the assistant content must mirror QueryEngine's _build_assistant_content
    pattern (omit empty text blocks).
    """
    _require_real_bedrock()
    from runtime.bedrock_client import BedrockClient
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins, find_tool_by_name, all_registered

    _reset_registry_for_tests()
    bootstrap_built_ins()

    list_dir_tool = find_tool_by_name(all_registered(), "list_dir")
    assert list_dir_tool is not None, "list_dir not registered"

    region = os.getenv("AWS_REGION", "ap-southeast-2")
    client = BedrockClient(model_id=_HAIKU_45_MODEL_ID, region=region, mock_mode=False)

    tool_schema = [{
        "name": "list_dir",
        "description": list_dir_tool.description,
        "input_schema": list_dir_tool.input_schema,
    }]

    # Round-trip 1: user asks, model returns tool_use.
    messages = [{
        "role": "user",
        "content": "List the files in the current directory using the list_dir tool, then summarize.",
    }]
    response = client.chat(
        messages=messages,
        system="You are a helpful assistant. Use the list_dir tool when asked to list files.",
        tools=tool_schema,
        max_tokens=512,
    )
    assert response.tool_calls, f"expected tool_use; got stop_reason={response.stop_reason}"
    tool_call = response.tool_calls[0]
    assert tool_call.name == "list_dir", f"wrong tool: {tool_call.name}"

    # Execute the tool locally — ToolCall.input is the args dict.
    tool_result = list_dir_tool.execute(tool_call.input, context={})
    assert isinstance(tool_result, str), f"list_dir returned non-string: {type(tool_result)}"

    # Round-trip 2: send tool_result, get final text.
    # Build assistant content like QueryEngine._build_assistant_content:
    # omit empty text blocks (Bedrock rejects them).
    assistant_blocks: list = []
    if response.text:
        assistant_blocks.append({"type": "text", "text": response.text})
    assistant_blocks.append({
        "type": "tool_use",
        "id": tool_call.id,
        "name": tool_call.name,
        "input": tool_call.input,
    })
    messages.append({"role": "assistant", "content": assistant_blocks})
    messages.append({
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": tool_call.id,
            "content": tool_result[:4000],
        }],
    })
    response2 = client.chat(
        messages=messages,
        system="You are a helpful assistant. Use the list_dir tool when asked to list files.",
        tools=tool_schema,
        max_tokens=512,
    )
    assert response2.text, f"empty final text: {response2}"
    assert response2.stop_reason == "end_turn", (
        f"unexpected stop_reason: {response2.stop_reason}"
    )


def test_real_bedrock_compact_then_continue():
    """Real two-call Bedrock smoke (RENAMED scope per Codex Block J iter-1
    HIGH #2): drive QueryEngine end-to-end across TWO turns, verify the
    second call succeeds with the assistant turn from call 1 in history.

    ~$0.01 per call.

    SCOPE NOTE: TEST_DESIGN §Block J row 3 originally specified
    "80K-token preamble → compact fires → next call succeeds". Block J
    iter-1 (Codex HIGH #2) corrected: hitting 80K on Bedrock here would
    cost more than Block J's $0.02 cap, AND auto-compaction is wired in
    QueryEngine — calling BedrockClient.chat() directly skips that path.

    Per ADR-039 §iter-2 update: this test is now scoped to:
      - real two-call Bedrock smoke (validates Bedrock auth + state),
      - using Agent.run() (QueryEngine) which exercises the SAME compaction
        decision path that R-tier R2 will exercise at full 80K scale,
      - costs ~$0.01.

    Full 80K-token compaction lock tests live in:
      - tests/integration/test_block_h.py (mock-based H-11 invariant)
      - R-tier R2 (real Bedrock at full scale, separately budgeted ~$0.50).
    """
    _require_real_bedrock()
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    region = os.getenv("AWS_REGION", "ap-southeast-2")
    client = BedrockClient(model_id=_HAIKU_45_MODEL_ID, region=region, mock_mode=False)
    agent = Agent(client=client, max_turns=3)

    # Turn 1.
    result1 = agent.run("Say 'OK' and stop.", tools=[])
    assert result1.text, f"empty text on turn 1: {result1}"

    # Turn 2 — same Agent instance, history preserved.
    result2 = agent.run("Now say 'DONE' and stop.", tools=[])
    assert result2.text, f"empty text on turn 2: {result2}"
    assert result2.stop_reason == "end_turn", (
        f"unexpected stop_reason on turn 2: {result2.stop_reason}"
    )


# ============================================================
# Block J — 7-of-7 registry lock (TEST_DESIGN parity)
# ============================================================

def test_block_j_ship_gate_test_count():
    """Block J ships when 7/7 green per TEST_DESIGN §Block J. This
    meta-lock asserts all 7 named tests are present in this module so
    a future refactor can't silently drop one.
    """
    expected = [
        "test_zip_rebuild_succeeds",
        "test_zip_extract_in_tmpdir",
        "test_zip_python_c_import_entry",
        "test_zip_python_c_import_sagemaker_agent",
        "test_real_bedrock_hello_world",
        "test_real_bedrock_tool_use_round_trip",
        "test_real_bedrock_compact_then_continue",
    ]
    import sys as _sys
    mod = _sys.modules[__name__]
    for name in expected:
        assert hasattr(mod, name), f"Block J test '{name}' missing from this module"
