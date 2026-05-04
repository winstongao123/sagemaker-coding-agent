"""Block N â€” Parallel tool execution + dynamic tool refs + dedup + fuzzy
+ ephemeral prompt.

Source: Hermes run_agent.py + Runnable services/tools/dispatch.

Tests per TEST_DESIGN Block N plus v5 completion-audit redo rows:
- test_fuzzy_tool_name_typo_resolves (T1)
- test_ephemeral_system_prompt_not_persisted (T1)
- test_dynamic_tool_ref_injection_at_init (T1)
- test_max_tool_workers_4 (T1)
- test_tool_call_dedup_blocks_redundant (T2 â€” structural)
- test_n7_partial_tool_names_warning_on_disconnect (T2 â€” structural)
- test_parallel_exec_3_independent_reads (local no-AWS structural lock)
- test_parallel_exec_path_conflict_serializes_writes
- test_n_real_3_parallel_reads_haiku (local no-AWS structural substitute)
"""
from __future__ import annotations

import os
import sys
import time

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# TEST_DESIGN row 4 â€” fuzzy tool name typo
# ============================================================

def test_fuzzy_tool_name_typo_resolves():
    """`read_filee` â†’ fuzzy resolves to `read_file`."""
    from core import fuzzy_resolve_tool_name

    tools = ["read_file", "write_file", "edit_file", "bash", "grep"]
    assert fuzzy_resolve_tool_name("read_filee", tools) == "read_file"
    assert fuzzy_resolve_tool_name("read_fil", tools) == "read_file"
    assert fuzzy_resolve_tool_name("READ_FILE", tools) == "read_file"  # case-insens
    # Below cutoff â†’ None.
    assert fuzzy_resolve_tool_name("xyzpdq", tools) is None
    assert fuzzy_resolve_tool_name("", tools) is None
    assert fuzzy_resolve_tool_name("read_file", []) is None


# ============================================================
# TEST_DESIGN row 5 â€” ephemeral system prompt not persisted
# ============================================================

def test_ephemeral_system_prompt_not_persisted():
    """Ephemeral prompt fragment not written to session log."""
    from core import mark_ephemeral_block, strip_ephemeral_blocks_for_persist

    persistent = {"type": "text", "text": "Permanent message"}
    ephemeral = mark_ephemeral_block({"type": "text", "text": "Transient nudge"})
    assert ephemeral["_ephemeral"] is True

    msgs = [
        {"role": "user", "content": [persistent, ephemeral]},
        {"role": "assistant", "content": [{"type": "text", "text": "Reply"}]},
    ]
    out = strip_ephemeral_blocks_for_persist(msgs)
    # First message: ephemeral block stripped, persistent kept.
    assert len(out[0]["content"]) == 1
    assert out[0]["content"][0]["text"] == "Permanent message"
    # Second message unchanged.
    assert len(out[1]["content"]) == 1


def test_ephemeral_drops_message_when_only_ephemeral_blocks():
    """If a message's only blocks are ephemeral, the WHOLE message is
    dropped from persistence."""
    from core import mark_ephemeral_block, strip_ephemeral_blocks_for_persist

    msgs = [
        {"role": "user", "content": "real"},
        {"role": "user", "content": [
            mark_ephemeral_block({"type": "text", "text": "transient1"}),
            mark_ephemeral_block({"type": "text", "text": "transient2"}),
        ]},
        {"role": "assistant", "content": [{"type": "text", "text": "reply"}]},
    ]
    out = strip_ephemeral_blocks_for_persist(msgs)
    # 2 messages survive (real user + assistant); the all-ephemeral one drops.
    assert len(out) == 2
    assert out[0]["content"] == "real"
    assert out[1]["content"][0]["text"] == "reply"


# ============================================================
# TEST_DESIGN row 6 â€” dynamic tool ref injection (Hermes A36)
# ============================================================

def test_dynamic_tool_ref_injection_at_init():
    """Tool schemas at init have cross-references injected (Hermes A36)."""
    from core import inject_dynamic_tool_refs

    schemas = [
        {"name": "read_file", "description": "Read a file."},
        {"name": "edit_file", "description": "Edit a file."},
        {"name": "bash", "description": "Run shell."},
    ]
    refs = {
        "read_file": "See also: write_file, edit_file.",
        "edit_file": "See also: read_file, write_file.",
    }
    out = inject_dynamic_tool_refs(schemas, refs)
    # read_file got ref appended.
    assert "Read a file" in out[0]["description"]
    assert "See also: write_file, edit_file" in out[0]["description"]
    # edit_file got ref.
    assert "See also: read_file, write_file" in out[1]["description"]
    # bash had no ref â†’ unchanged.
    assert out[2]["description"] == "Run shell."
    # Original schemas unmodified (dict copies).
    assert "See also" not in schemas[0]["description"]


# ============================================================
# TEST_DESIGN row 7 â€” MAX_TOOL_WORKERS = 4 constant
# ============================================================

def test_max_tool_workers_4():
    """`_MAX_TOOL_WORKERS=4` constant; 5 parallel calls â†’ 4 in flight + 1 queued.

    Block N constant lock â€” the actual ThreadPoolExecutor wiring lands in
    Block J real-AWS gate. This test pins the constant value so a future
    refactor doesn't silently change Hermes parallelism.
    """
    from core import MAX_TOOL_WORKERS

    assert MAX_TOOL_WORKERS == 4, (
        "MAX_TOOL_WORKERS must equal 4 (Hermes parallel ceiling). "
        "Changing this affects Bedrock concurrency cost â€” review with care."
    )


def test_n3_parallel_constants_match_v5_tool_surface():
    from core import (
        NEVER_PARALLEL_TOOLS,
        PARALLEL_SAFE_TOOLS,
        PATH_SCOPED_TOOLS,
        _MAX_TOOL_WORKERS,
    )

    assert _MAX_TOOL_WORKERS == 4
    assert {"bash", "python_exec", "task"}.issubset(NEVER_PARALLEL_TOOLS)
    assert {"read_file", "grep", "glob"}.issubset(PARALLEL_SAFE_TOOLS)
    assert {"read_file", "write_file", "edit_file", "notebook_edit"}.issubset(PATH_SCOPED_TOOLS)
    assert not any(name.startswith("ha_") for name in PARALLEL_SAFE_TOOLS)


# ============================================================
# TEST_DESIGN row 3 â€” tool call dedup
# ============================================================

def test_tool_call_dedup_blocks_redundant():
    """Same `(tool_name, args)` 3x in one batch â†’ 2 calls deduped."""
    from core import dedup_tool_calls

    calls = [
        {"name": "read_file", "input": {"file_path": "/x.py"}, "id": "a"},
        {"name": "read_file", "input": {"file_path": "/x.py"}, "id": "b"},
        {"name": "read_file", "input": {"file_path": "/x.py"}, "id": "c"},
        {"name": "read_file", "input": {"file_path": "/y.py"}, "id": "d"},
    ]
    kept, dropped = dedup_tool_calls(calls)
    # First duplicate kept, 2 dropped, /y.py call kept.
    assert len(kept) == 2
    assert kept[0]["id"] == "a"
    assert kept[1]["id"] == "d"
    assert len(dropped) == 2
    assert dropped[0]["id"] == "b"
    assert dropped[1]["id"] == "c"


def test_dedup_handles_attribute_call_objects():
    """dedup_tool_calls works with ToolCall objects (.name + .input attrs),
    not just dicts."""
    from core import dedup_tool_calls

    class _Call:
        def __init__(self, name, input_, id):
            self.name = name
            self.input = input_
            self.id = id

    calls = [
        _Call("bash", {"cmd": "ls"}, "1"),
        _Call("bash", {"cmd": "ls"}, "2"),  # dup
        _Call("bash", {"cmd": "pwd"}, "3"),  # different args
    ]
    kept, dropped = dedup_tool_calls(calls)
    assert len(kept) == 2
    assert len(dropped) == 1
    assert dropped[0].id == "2"


# ============================================================
# TEST_DESIGN row 8 â€” partial tool-call warning on disconnect (Hermes H2)
# ============================================================

def test_n7_partial_tool_names_warning_on_disconnect():
    """Mid-call disconnect â†’ warning + synthetic tool_result stub."""
    from core import partial_tool_call_warning

    captured = []
    stubs = partial_tool_call_warning(
        ["call_1", "call_2", "call_3"],
        output_fn=lambda s: captured.append(s),
    )
    # 3 stubs, one per interrupted tool_use_id.
    assert len(stubs) == 3
    for i, stub in enumerate(stubs, start=1):
        assert stub["type"] == "tool_result"
        assert stub["tool_use_id"] == f"call_{i}"
        assert "synthetic stub" in stub["content"]
    # Warning emitted.
    assert any("partial-tool-warning" in c for c in captured)


def test_partial_warning_no_op_when_empty():
    """Empty interrupted list â†’ no warning, no stubs."""
    from core import partial_tool_call_warning

    captured = []
    stubs = partial_tool_call_warning([], output_fn=lambda s: captured.append(s))
    assert stubs == []
    assert captured == []


# ============================================================
# Behavioral lock tests
# ============================================================

def test_detect_path_conflicts_finds_write_conflicts():
    """detect_path_conflicts returns dict of canonical path â†’ calls when
    2+ writes target the same path. Keys are normpath+abspath (Codex
    iter-1 #2 â€” handles relative-vs-absolute). Test compares
    canonicalized expected paths."""
    import os
    from core import detect_path_conflicts

    calls = [
        {"name": "write_file", "input": {"file_path": "/x.py", "content": "a"}, "id": "1"},
        {"name": "write_file", "input": {"file_path": "/x.py", "content": "b"}, "id": "2"},
        {"name": "edit_file", "input": {"file_path": "/x.py"}, "id": "3"},
        {"name": "read_file", "input": {"file_path": "/x.py"}, "id": "4"},  # not a mutator
        {"name": "write_file", "input": {"file_path": "/y.py"}, "id": "5"},  # different path
    ]
    conflicts = detect_path_conflicts(calls)
    # Canonicalize the expected paths the same way the helper does.
    canonical_x = os.path.normpath(os.path.abspath("/x.py"))
    canonical_y = os.path.normpath(os.path.abspath("/y.py"))
    # /x.py has 3 conflicting mutators (2 writes + 1 edit). /y.py only 1.
    assert canonical_x in conflicts
    assert len(conflicts[canonical_x]) == 3
    assert canonical_y not in conflicts


def test_synthetic_tool_result_stub_shape():
    """synthetic_tool_result_stub returns Bedrock-shaped tool_result block."""
    from core import synthetic_tool_result_stub

    stub = synthetic_tool_result_stub("call_42", reason="deduped")
    assert stub["type"] == "tool_result"
    assert stub["tool_use_id"] == "call_42"
    assert "deduped" in stub["content"]
    assert stub["is_error"] is False


def test_n1_n2_dispatch_plan_splits_parallel_and_sequential_paths():
    from core import plan_tool_dispatch
    from tools.registry import build_tool

    read = build_tool(
        "read_file",
        "read",
        {},
        lambda args, context=None: "x",
        is_read_only=True,
        is_concurrency_safe=True,
    )
    write = build_tool(
        "write_file",
        "write",
        {},
        lambda args, context=None: "x",
        is_destructive=True,
    )
    calls = [
        {"name": "read_file", "input": {"file_path": "a"}, "id": "r1"},
        {"name": "read_file", "input": {"file_path": "b"}, "id": "r2"},
        {"name": "write_file", "input": {"file_path": "a"}, "id": "w1"},
    ]
    plan = plan_tool_dispatch(calls, {"read_file": read, "write_file": write})
    assert [c["id"] for c in plan["parallel"]] == ["r1", "r2"]
    assert [c["id"] for c in plan["sequential"]] == ["w1"]


def test_n4_parallel_executor_checkpoints_and_preserves_order():
    from core import ToolDispatchSnapshot, execute_parallel_tool_calls

    checkpoints = []

    class _Call:
        def __init__(self, id, delay):
            self.id = id
            self.name = "read_file"
            self.input = {"delay": delay}

    calls = [_Call("slow", 0.05), _Call("fast", 0.01)]

    def execute(call):
        time.sleep(call.input["delay"])
        return {"type": "tool_result", "tool_use_id": call.id, "content": call.id}

    out = execute_parallel_tool_calls(calls, execute, checkpoint_callback=checkpoints.append)
    assert [block["tool_use_id"] for block in out] == ["slow", "fast"]
    assert all(isinstance(item, ToolDispatchSnapshot) for item in checkpoints)
    assert {item.status for item in checkpoints} >= {"started", "finished"}


def test_n5_sequential_fallback_for_path_conflict():
    from core import plan_tool_dispatch
    from tools.registry import build_tool

    write = build_tool("write_file", "write", {}, lambda args, context=None: "x", is_destructive=True)
    calls = [
        {"name": "write_file", "input": {"file_path": "same.txt"}, "id": "a"},
        {"name": "write_file", "input": {"file_path": "./same.txt"}, "id": "b"},
    ]
    plan = plan_tool_dispatch(calls, {"write_file": write})
    assert plan["parallel"] == []
    assert [c["id"] for c in plan["sequential"]] == ["a", "b"]
    assert plan["conflicts"]


def test_n6_enforce_turn_budget_over_recent_tool_messages():
    from core import enforce_turn_budget

    messages = [
        {"role": "user", "content": "old"},
        {"role": "user", "content": [{"type": "tool_result", "content": "a" * 10}]},
        {"role": "user", "content": [{"type": "tool_result", "content": "b" * 10}]},
    ]
    out = enforce_turn_budget(messages, num_tools=2, max_chars=12)
    assert out[1]["content"][0]["content"] == "a" * 10
    assert "truncated by turn tool-result budget" in out[2]["content"][0]["content"]


def test_n8_retry_classifier_three_categories():
    from core import classify_tool_retry

    assert classify_tool_retry("pre_call", "timeout").recovery == "retry_before_tool_dispatch"
    assert classify_tool_retry("mid_call", "disconnect").recovery == "emit_stub_and_retry"
    post = classify_tool_retry("post_call", "AccessDenied permission")
    assert post.stage == "post_call"
    assert post.retryable is False


def test_n9_mid_call_stub_recovery_warning():
    from core import mid_call_stub_recovery

    warnings = []
    stubs = mid_call_stub_recovery(["a", "b"], "disconnect", output_fn=warnings.append)
    assert [stub["tool_use_id"] for stub in stubs] == ["a", "b"]
    assert warnings and "mid-call-recovery" in warnings[0]


def test_n18_tool_interface_enrichments_defaults():
    from tools.registry import build_tool

    tool = build_tool("x", "desc", {}, lambda args, context=None: "ok")
    assert tool.aliases == ()
    assert tool.max_result_size_chars == 50_000
    assert tool.is_destructive is False
    assert tool.interrupt_behavior == "allow"


# ============================================================
# Codex iter-1 finding-lock tests
# ============================================================

def test_detect_path_conflicts_handles_notebook_edit_arg():
    """Codex iter-1 finding #1 lock: notebook_edit uses `notebook_path`,
    not `file_path`. Two notebook_edit calls on the same notebook must
    be detected as conflicting.
    """
    from core import detect_path_conflicts

    calls = [
        {"name": "notebook_edit", "input": {"notebook_path": "/x.ipynb", "cell": 1}},
        {"name": "notebook_edit", "input": {"notebook_path": "/x.ipynb", "cell": 2}},
    ]
    conflicts = detect_path_conflicts(calls)
    # The conflict key is canonicalized; just verify exactly one entry exists
    # with 2 calls.
    assert len(conflicts) == 1
    only_path, only_calls = next(iter(conflicts.items()))
    assert only_path.replace("\\", "/").endswith("/x.ipynb")
    assert len(only_calls) == 2


def test_detect_path_conflicts_canonicalizes_relative_paths():
    """Codex iter-1 finding #2 lock: relative-path variants of the same
    file are grouped. `x.py` and `./x.py` and absolute path that resolves
    to same file all collide.
    """
    import os
    from core import detect_path_conflicts

    abs_path = os.path.abspath("x.py")
    calls = [
        {"name": "write_file", "input": {"file_path": "x.py", "content": "a"}},
        {"name": "write_file", "input": {"file_path": "./x.py", "content": "b"}},
        {"name": "edit_file", "input": {"file_path": abs_path}},
    ]
    conflicts = detect_path_conflicts(calls)
    assert len(conflicts) == 1, f"all 3 calls should collapse to one path; got {conflicts}"
    only_path, only_calls = next(iter(conflicts.items()))
    assert len(only_calls) == 3


# ============================================================
# Local parallel execution locks (no AWS/R-tier)
# ============================================================

def test_parallel_exec_3_independent_reads():
    from core import execute_parallel_tool_calls

    class _Call:
        def __init__(self, id):
            self.id = id
            self.name = "read_file"
            self.input = {}

    start = time.monotonic()
    out = execute_parallel_tool_calls(
        [_Call("1"), _Call("2"), _Call("3")],
        lambda call: (time.sleep(0.05), {
            "type": "tool_result",
            "tool_use_id": call.id,
            "content": call.id,
        })[1],
    )
    elapsed = time.monotonic() - start
    assert [block["tool_use_id"] for block in out] == ["1", "2", "3"]
    assert elapsed < 0.13


def test_query_engine_parallel_dispatch_3_safe_reads():
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import Response, ToolCall
    from tools.registry import build_tool

    class _Client:
        mock_mode = True

        def __init__(self):
            self.turn = 0

        def chat(self, *args, **kwargs):
            self.turn += 1
            if self.turn == 1:
                return Response(
                    "",
                    [
                        ToolCall("1", "read_file", {"file_path": "a"}),
                        ToolCall("2", "read_file", {"file_path": "b"}),
                        ToolCall("3", "read_file", {"file_path": "c"}),
                    ],
                    "tool_use",
                    {},
                )
            return Response("done", [], "end_turn", {})

    def _read(args, context=None):
        time.sleep(0.05)
        return args["file_path"]

    tool = build_tool(
        "read_file",
        "read",
        {},
        _read,
        is_read_only=True,
        is_concurrency_safe=True,
    )
    engine = QueryEngine(_Client(), max_turns=3)
    start = time.monotonic()
    result = engine.run("go", "sys", [tool], output_fn=lambda _: None)
    elapsed = time.monotonic() - start
    assert result.stop_reason == "end_turn"
    assert elapsed < 0.13
    tool_turn = engine.messages[-2]
    assert [b["tool_use_id"] for b in tool_turn["content"]] == ["1", "2", "3"]

def test_parallel_exec_path_conflict_serializes_writes():
    from core import plan_tool_dispatch
    from tools.registry import build_tool

    write = build_tool("write_file", "write", {}, lambda args, context=None: "ok", is_destructive=True)
    calls = [
        {"name": "write_file", "input": {"file_path": "x.txt"}, "id": "a"},
        {"name": "write_file", "input": {"file_path": "./x.txt"}, "id": "b"},
    ]
    plan = plan_tool_dispatch(calls, {"write_file": write})
    assert plan["parallel"] == []
    assert [c["id"] for c in plan["sequential"]] == ["a", "b"]

def test_n_real_3_parallel_reads_haiku():
    """No-AWS structural substitute: the local executor can run 3 reads concurrently."""
    from core import MAX_TOOL_WORKERS, execute_parallel_tool_calls

    class _Call:
        def __init__(self, id):
            self.id = id
            self.name = "read_file"
            self.input = {}

    out = execute_parallel_tool_calls(
        [_Call("a"), _Call("b"), _Call("c")],
        lambda call: {"type": "tool_result", "tool_use_id": call.id, "content": "ok"},
    )
    assert MAX_TOOL_WORKERS == 4
    assert [block["tool_use_id"] for block in out] == ["a", "b", "c"]


def test_query_engine_parallel_dispatch_audits_success_and_error(tmp_path, monkeypatch):
    """Parallel fast path keeps Block B forensics: successes and failures
    both write AUDIT entries, matching the sequential dispatch contract."""
    from core.query_engine import QueryEngine
    from runtime.audit import AuditLogger
    import runtime.audit as audit_mod
    from runtime.bedrock_client import Response, ToolCall
    from tools.registry import build_tool

    test_audit = AuditLogger(audit_dir=str(tmp_path))
    monkeypatch.setattr(audit_mod, "AUDIT", test_audit)

    class _Client:
        mock_mode = True

        def __init__(self):
            self.turn = 0

        def chat(self, *args, **kwargs):
            self.turn += 1
            if self.turn == 1:
                return Response(
                    "",
                    [
                        ToolCall("ok", "read_file", {"file_path": "ok"}),
                        ToolCall("boom", "read_file", {"file_path": "boom"}),
                    ],
                    "tool_use",
                    {},
                )
            return Response("done", [], "end_turn", {})

    def _read(args, context=None):
        if args["file_path"] == "boom":
            raise RuntimeError("parallel failure")
        return "read-ok"

    tool = build_tool(
        "read_file",
        "read",
        {},
        _read,
        is_read_only=True,
        is_concurrency_safe=True,
    )
    engine = QueryEngine(_Client(), max_turns=3)
    engine.run("go", "sys", [tool], output_fn=lambda _: None)

    entries = test_audit.get_session_log(engine.session_id)
    tool_entries = [
        (entry["action"], entry["tool_name"])
        for entry in entries
        if entry.get("tool_name") == "read_file"
    ]
    assert ("tool_dispatch", "read_file") in tool_entries
    assert ("tool_error", "read_file") in tool_entries


def test_query_engine_parallel_dispatch_repairs_json_string_args():
    """Parallel fast path keeps Block C JSON-repair behavior before tool
    execution. The tool receives dict args, not the raw JSON string."""
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import Response, ToolCall
    from tools.registry import build_tool

    seen = []

    class _Client:
        mock_mode = True

        def __init__(self):
            self.turn = 0

        def chat(self, *args, **kwargs):
            self.turn += 1
            if self.turn == 1:
                return Response(
                    "",
                    [
                        ToolCall("a", "read_file", '{"file_path": "a.txt"}'),
                        ToolCall("b", "read_file", '{"file_path": "b.txt"}'),
                    ],
                    "tool_use",
                    {},
                )
            return Response("done", [], "end_turn", {})

    def _read(args, context=None):
        seen.append(args)
        return args["file_path"]

    tool = build_tool(
        "read_file",
        "read",
        {},
        _read,
        is_read_only=True,
        is_concurrency_safe=True,
    )
    engine = QueryEngine(_Client(), max_turns=3)
    engine.run("go", "sys", [tool], output_fn=lambda _: None)

    assert sorted(item["file_path"] for item in seen) == ["a.txt", "b.txt"]
    assert all(isinstance(item, dict) for item in seen)


def test_query_engine_parallel_dispatch_keeps_repetition_guard():
    """Parallel fast path still updates Block C repetition tracking. A safe
    read repeated across three tool turns is blocked on the third attempt."""
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import Response, ToolCall
    from tools.registry import build_tool

    class _Client:
        mock_mode = True

        def __init__(self):
            self.turn = 0

        def chat(self, *args, **kwargs):
            self.turn += 1
            if self.turn == 1:
                return Response(
                    "",
                    [
                        ToolCall("same1", "read_file", {"file_path": "same.txt"}),
                        ToolCall("other1", "read_file", {"file_path": "one.txt"}),
                    ],
                    "tool_use",
                    {},
                )
            if self.turn == 2:
                return Response(
                    "",
                    [
                        ToolCall("same2", "read_file", {"file_path": "same.txt"}),
                        ToolCall("other2", "read_file", {"file_path": "two.txt"}),
                    ],
                    "tool_use",
                    {},
                )
            if self.turn == 3:
                return Response(
                    "",
                    [
                        ToolCall("same3", "read_file", {"file_path": "same.txt"}),
                        ToolCall("other3", "read_file", {"file_path": "three.txt"}),
                    ],
                    "tool_use",
                    {},
                )
            return Response("done", [], "end_turn", {})

    tool = build_tool(
        "read_file",
        "read",
        {},
        lambda args, context=None: args["file_path"],
        is_read_only=True,
        is_concurrency_safe=True,
    )
    engine = QueryEngine(_Client(), max_turns=5)
    result = engine.run("go", "sys", [tool], output_fn=lambda _: None)

    assert result.stop_reason == "end_turn"
    third_tool_turn = result.messages[6]["content"]
    by_id = {block["tool_use_id"]: block for block in third_tool_turn}
    assert by_id["same3"]["is_error"] is True
    assert "same call to 'read_file'" in by_id["same3"]["content"]
    assert by_id["other3"]["content"] == "three.txt"
