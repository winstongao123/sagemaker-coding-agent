"""Block N — Parallel tool execution + dynamic tool refs + dedup + fuzzy
+ ephemeral prompt.

Source: Hermes run_agent.py + Runnable services/tools/dispatch.

Tests per TEST_DESIGN §Block N (9 tests; T2 timing-sensitive
parallel-exec tests + T5 deferred to Block J / R-tier):
- test_fuzzy_tool_name_typo_resolves (T1)
- test_ephemeral_system_prompt_not_persisted (T1)
- test_dynamic_tool_ref_injection_at_init (T1)
- test_max_tool_workers_4 (T1)
- test_tool_call_dedup_blocks_redundant (T2 — structural)
- test_n7_partial_tool_names_warning_on_disconnect (T2 — structural)
- test_parallel_exec_3_independent_reads (T2 — DEFERRED to Block J)
- test_parallel_exec_path_conflict_serializes_writes (T2 — DEFERRED)
- test_n_real_3_parallel_reads_haiku (T5 — DEFERRED to R-tier)
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# TEST_DESIGN row 4 — fuzzy tool name typo
# ============================================================

def test_fuzzy_tool_name_typo_resolves():
    """`read_filee` → fuzzy resolves to `read_file`."""
    from core import fuzzy_resolve_tool_name

    tools = ["read_file", "write_file", "edit_file", "bash", "grep"]
    assert fuzzy_resolve_tool_name("read_filee", tools) == "read_file"
    assert fuzzy_resolve_tool_name("read_fil", tools) == "read_file"
    assert fuzzy_resolve_tool_name("READ_FILE", tools) == "read_file"  # case-insens
    # Below cutoff → None.
    assert fuzzy_resolve_tool_name("xyzpdq", tools) is None
    assert fuzzy_resolve_tool_name("", tools) is None
    assert fuzzy_resolve_tool_name("read_file", []) is None


# ============================================================
# TEST_DESIGN row 5 — ephemeral system prompt not persisted
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
# TEST_DESIGN row 6 — dynamic tool ref injection (Hermes A36)
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
    # bash had no ref → unchanged.
    assert out[2]["description"] == "Run shell."
    # Original schemas unmodified (dict copies).
    assert "See also" not in schemas[0]["description"]


# ============================================================
# TEST_DESIGN row 7 — MAX_TOOL_WORKERS = 4 constant
# ============================================================

def test_max_tool_workers_4():
    """`_MAX_TOOL_WORKERS=4` constant; 5 parallel calls → 4 in flight + 1 queued.

    Block N constant lock — the actual ThreadPoolExecutor wiring lands in
    Block J real-AWS gate. This test pins the constant value so a future
    refactor doesn't silently change Hermes parallelism.
    """
    from core import MAX_TOOL_WORKERS

    assert MAX_TOOL_WORKERS == 4, (
        "MAX_TOOL_WORKERS must equal 4 (Hermes parallel ceiling). "
        "Changing this affects Bedrock concurrency cost — review with care."
    )


# ============================================================
# TEST_DESIGN row 3 — tool call dedup
# ============================================================

def test_tool_call_dedup_blocks_redundant():
    """Same `(tool_name, args)` 3x in one batch → 2 calls deduped."""
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
# TEST_DESIGN row 8 — partial tool-call warning on disconnect (Hermes H2)
# ============================================================

def test_n7_partial_tool_names_warning_on_disconnect():
    """Mid-call disconnect → warning + synthetic tool_result stub."""
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
    """Empty interrupted list → no warning, no stubs."""
    from core import partial_tool_call_warning

    captured = []
    stubs = partial_tool_call_warning([], output_fn=lambda s: captured.append(s))
    assert stubs == []
    assert captured == []


# ============================================================
# Behavioral lock tests
# ============================================================

def test_detect_path_conflicts_finds_write_conflicts():
    """detect_path_conflicts returns dict of canonical path → calls when
    2+ writes target the same path. Keys are normpath+abspath (Codex
    iter-1 #2 — handles relative-vs-absolute). Test compares
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
# DEFERRED tests (Block J real-AWS gate or R-tier)
# ============================================================

@pytest.mark.skip(
    reason="Block N T2 parallel-exec timing test deferred to Block J "
    "real-AWS gate (timing-sensitive — depends on actual ThreadPoolExecutor "
    "wiring into core/query_engine.py + real Bedrock latency). Per ADR-037 §3."
)
def test_parallel_exec_3_independent_reads():
    pass


@pytest.mark.skip(
    reason="Block N T2 path-conflict timing test deferred to Block J "
    "real-AWS gate. The detect_path_conflicts helper is locked by "
    "test_detect_path_conflicts_finds_write_conflicts; the END-TO-END "
    "serialization test belongs with the executor wiring."
)
def test_parallel_exec_path_conflict_serializes_writes():
    pass


@pytest.mark.skip(
    reason="Block N T5 real-Haiku 3-parallel test deferred to R-tier R3 "
    "(sub-agent dispatch + cache-prefix). ~$0.005."
)
def test_n_real_3_parallel_reads_haiku():
    pass
