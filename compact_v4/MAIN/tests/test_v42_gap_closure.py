import os
import subprocess
import sys
import time
from pathlib import Path


AGENT_DIR = os.path.join(os.path.dirname(__file__), "..", "agent")
sys.path.insert(0, AGENT_DIR)

import sagemaker_agent as sa


def _reset_file_tracking():
    sa.FILE_CACHE.clear_all()
    with sa._FILES_READ_LOCK:
        sa._FILES_READ.clear()
        sa._FILE_READ_TIMES.clear()
        sa._FILE_PARTIAL_READS.clear()


def test_file_unchanged_stub_wins_before_generic_in_context_hint(tmp_path, monkeypatch):
    monkeypatch.setattr(sa.CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(sa.SECURITY, "workspace", Path(tmp_path))
    file_path = tmp_path / "sample.py"
    file_path.write_text("print('hello')\n", encoding="utf-8")

    _reset_file_tracking()

    first = sa.tool_read_file({"file_path": str(file_path)})
    second = sa.tool_read_file({"file_path": str(file_path)})

    assert "hello" in first
    assert sa.FILE_UNCHANGED_STUB in second
    assert "File already in context" not in second


class _PromptTooLongClient:
    model_id = "mock-model"

    def __init__(self, max_messages_before_error):
        self.max_messages_before_error = max_messages_before_error
        self.calls = []

    def chat(self, messages, system, tools, max_tokens, temperature):
        self.calls.append(messages)
        if len(messages) > self.max_messages_before_error:
            raise Exception("Prompt too long for summary retry test")
        return sa.Response(
            text="Recovered summary",
            tool_calls=[],
            stop_reason="end_turn",
            usage={},
        )


def test_compactor_retries_prompt_too_long_by_truncating_head():
    messages = []
    for idx in range(18):
        role = "user" if idx % 2 == 0 else "assistant"
        messages.append({"role": role, "content": f"message {idx} " + ("x" * 200)})

    client = _PromptTooLongClient(max_messages_before_error=18)
    summary = sa.Compactor.create_llm_summary(client, messages)

    assert summary == "Recovered summary"
    assert len(client.calls) >= 2
    assert len(client.calls[-1]) < len(client.calls[0])


class _TwoTurnClient:
    model_id = "mock-model"

    def __init__(self):
        self.calls = 0

    def chat(self, messages, system, tools, max_tokens, temperature, thinking_enabled, thinking_budget):
        self.calls += 1
        if self.calls == 1:
            return sa.Response(
                text="Running read-only tools",
                tool_calls=[
                    sa.ToolCall(id="t1", name="read_file", input={"file_path": "a.py"}),
                    sa.ToolCall(id="t2", name="glob", input={"pattern": "*.py", "path": "."}),
                ],
                stop_reason="tool_use",
                usage={},
            )
        return sa.Response(text="Done", tool_calls=[], stop_reason="end_turn", usage={})


def test_parallel_read_only_tools_execute_concurrently(monkeypatch):
    original_read = sa.TOOLS["read_file"]
    original_glob = sa.TOOLS["glob"]

    def slow_read(_args):
        time.sleep(0.25)
        return "read ok"

    def slow_glob(_args):
        time.sleep(0.25)
        return "glob ok"

    monkeypatch.setitem(
        sa.TOOLS,
        "read_file",
        (
            slow_read,
            False,
            "slow read",
            {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]},
        ),
    )
    monkeypatch.setitem(
        sa.TOOLS,
        "glob",
        (
            slow_glob,
            False,
            "slow glob",
            {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]},
        ),
    )

    agent = sa.Agent(_TwoTurnClient(), session_id="parallel-test", on_approval=lambda *_args, **_kwargs: True)

    started = time.perf_counter()
    result = agent.run("run the tools", output_fn=lambda *_args, **_kwargs: None, system_prompt="test", max_turns_override=3)
    elapsed = time.perf_counter() - started

    assert result == "Done"
    assert elapsed < 0.45


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )


def _init_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.name", "SageAgent Test")
    _git(repo, "config", "user.email", "agent-test@example.local")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "baseline")


def test_compact_starts_with_user_and_alternates_roles():
    messages = [
        {"role": "user", "content": "original request"},
        {"role": "assistant", "content": "analysis"},
        {"role": "user", "content": "latest user message"},
    ]

    compacted = sa.COMPACTOR.compact(messages, "summary text")
    roles = [m["role"] for m in compacted]

    assert roles[0] == "user"
    assert "CONVERSATION SUMMARY" in compacted[0]["content"]
    assert roles[1] == "assistant"
    for left, right in zip(roles, roles[1:]):
        assert left != right, f"consecutive {left} messages after compact: {roles}"


def test_skill_auto_trigger_global_default_is_off():
    assert sa.CONFIG.enable_skill_auto_trigger is False
    info = sa.SkillInfo(name="x", description="", location="/x", base_dir="/")
    assert info.auto_trigger is False


def test_status_doc_loads_from_workspace(monkeypatch, tmp_path):
    status = tmp_path / "AGENT_STATUS.md"
    status.write_text("# Agent Status\n\n## Current Goal\n- keep durable state\n", encoding="utf-8")

    monkeypatch.setattr(sa.CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(sa.CONFIG, "enable_status_doc", True)
    monkeypatch.setattr(sa.CONFIG, "status_doc", "AGENT_STATUS.md")

    loaded = sa._load_project_status()

    assert "# Project Status" in loaded
    assert "keep durable state" in loaded


def test_status_doc_can_be_disabled(monkeypatch, tmp_path):
    (tmp_path / "AGENT_STATUS.md").write_text("# Agent Status\n", encoding="utf-8")

    monkeypatch.setattr(sa.CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(sa.CONFIG, "enable_status_doc", False)
    monkeypatch.setattr(sa.CONFIG, "status_doc", "AGENT_STATUS.md")

    assert sa._load_project_status() == ""


def test_status_doc_rejects_path_outside_workspace(monkeypatch, tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}_outside_status.md"
    outside.write_text("# Outside\n", encoding="utf-8")

    try:
        monkeypatch.setattr(sa.CONFIG, "workspace", str(tmp_path))
        monkeypatch.setattr(sa.CONFIG, "enable_status_doc", True)
        monkeypatch.setattr(sa.CONFIG, "status_doc", str(outside))

        assert sa._status_doc_path() is None
        assert sa._load_project_status() == ""
    finally:
        outside.unlink(missing_ok=True)


def test_sagemaker_git_policy_blocks_remote_operations():
    blocked_commands = [
        "git push origin main",
        "git pull --rebase",
        "git fetch origin",
        "git clone https://github.com/example/repo.git",
        "git remote set-url origin https://github.com/example/repo.git",
    ]
    for command in blocked_commands:
        ok, reason = sa.SECURITY.validate_command(command)
        assert ok is False, command
        assert "local git tree only" in reason

    for command in ["git status", "git diff HEAD --stat", "git log --oneline -1", "git remote -v"]:
        ok, reason = sa.SECURITY.validate_command(command)
        assert ok is True, f"{command}: {reason}"


def test_context_report_surfaces_tool_bloat_and_duplicate_reads():
    messages = [
        {"role": "user", "content": "inspect the file"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "r1", "name": "read_file", "input": {"file_path": "app.py"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "r1", "content": "print('one')\n" * 200},
        ]},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "r2", "name": "read_file", "input": {"file_path": "app.py"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "r2", "content": "print('one')\n" * 200},
        ]},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "b1", "name": "bash", "input": {"command": "pytest -q"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "b1", "content": "FAILED test\n" * 300},
        ]},
    ]

    stats = sa.analyze_context_messages(messages)
    report = sa.format_context_report(messages)

    assert stats["duplicate_reads"]["app.py"]["count"] == 2
    assert stats["tool_result_tokens"]["bash"] > 0
    assert "Context Diagnostic" in report
    assert "Duplicate File Reads" in report
    assert "app.py: 2 reads" in report
    assert "bash" in report


def test_build_subagent_uses_worktree_and_merges_back(monkeypatch, tmp_path):
    _init_repo(tmp_path)

    captured = {}
    outputs = []

    def fake_run(self, user_message, output_fn=print, **kwargs):
        if self.subagent_depth > 0:
            captured["workspace"] = sa.CONFIG.workspace
            Path(sa.CONFIG.workspace, "created_by_subagent.txt").write_text("from isolated build\n", encoding="utf-8")
            return "sub-agent done"
        return "parent done"

    monkeypatch.setattr(sa.CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(sa.CONFIG, "enable_worktree", True)
    monkeypatch.setattr(sa.Agent, "run", fake_run)

    parent = sa.Agent(sa.BedrockClient(sa.CONFIG.model_id, sa.CONFIG.region, mock_mode=True), session_id="wt-test")
    result = parent._run_task_tool(
        {"subagent_type": "build", "description": "write file", "prompt": "write a file"},
        outputs.append,
    )

    assert "sub-agent done" in result
    assert captured["workspace"] != str(tmp_path)
    assert Path(captured["workspace"]).exists() is False
    assert (tmp_path / "created_by_subagent.txt").read_text(encoding="utf-8") == "from isolated build\n"
    assert any("Build agent isolated" in o for o in outputs)
    assert any("merged back" in o for o in outputs)


def test_build_worktree_sees_dirty_and_untracked_parent_files(monkeypatch, tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "tracked.txt").write_text("dirty parent edit\n", encoding="utf-8")
    (tmp_path / "untracked.txt").write_text("untracked parent file\n", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "new.txt").write_text("nested untracked file\n", encoding="utf-8")

    seen = {}

    def fake_run(self, user_message, output_fn=print, **kwargs):
        if self.subagent_depth > 0:
            wt = Path(sa.CONFIG.workspace)
            seen["tracked"] = (wt / "tracked.txt").read_text(encoding="utf-8")
            seen["untracked"] = (wt / "untracked.txt").read_text(encoding="utf-8")
            seen["nested"] = (wt / "nested" / "new.txt").read_text(encoding="utf-8")
            return "saw dirty state"
        return "parent done"

    monkeypatch.setattr(sa.CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(sa.CONFIG, "enable_worktree", True)
    monkeypatch.setattr(sa.Agent, "run", fake_run)

    parent = sa.Agent(sa.BedrockClient(sa.CONFIG.model_id, sa.CONFIG.region, mock_mode=True), session_id="wt-dirty-test")
    result = parent._run_task_tool(
        {"subagent_type": "build", "description": "read dirty state", "prompt": "inspect files"},
        lambda _text: None,
    )

    assert "saw dirty state" in result
    assert seen["tracked"] == "dirty parent edit\n"
    assert seen["untracked"] == "untracked parent file\n"
    assert seen["nested"] == "nested untracked file\n"


def test_parallel_build_tasks_are_serialized_when_worktrees_enabled(monkeypatch):
    class TwoBuildTasksClient:
        model_id = "mock"
        prompt_cache_supported = False

        def __init__(self):
            self.calls = 0

        def chat(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return sa.Response(
                    "",
                    [
                        sa.ToolCall("t1", "task", {"subagent_type": "build", "description": "one", "prompt": "one"}),
                        sa.ToolCall("t2", "task", {"subagent_type": "build", "description": "two", "prompt": "two"}),
                    ],
                    "tool_use",
                    {},
                )
            return sa.Response("done", [], "end_turn", {})

    skip_flags = []
    outputs = []

    def fake_run_task(self, args, output_fn, _skip_cache_isolation=False):
        skip_flags.append(_skip_cache_isolation)
        return f"ran {args['description']}"

    monkeypatch.setattr(sa.CONFIG, "enable_worktree", True)
    monkeypatch.setattr(sa.Agent, "_run_task_tool", fake_run_task)

    agent = sa.Agent(TwoBuildTasksClient(), session_id="parallel-build-test", on_approval=lambda *_: True)
    result = agent.run("spawn two builds", outputs.append, system_prompt="test", max_turns_override=3)

    assert result == "done"
    assert skip_flags == [False, False]
    assert any("sequentially" in o for o in outputs), outputs
