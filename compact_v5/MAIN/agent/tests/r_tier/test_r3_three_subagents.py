"""R-tier R3 — three sub-agent dispatches + parent synthesis.

Per PS_V5_TEST_PLAYBOOK / PS_V5_TEST_SET §Tier 1 R3:
  Validates Phase 9 task tool (sub-agent spawn) end-to-end on real
  Bedrock:
    - Parent receives a coding-survey task across 3 small Python files.
    - Parent dispatches 3 sub-agents (subagent_type='explore'),
      one per file.
    - Each sub-agent reads its assigned file and reports the function
      name + 1-line summary + the TODO comment text.
    - Parent synthesizes the 3 results into a single findings.md.

Codex iter-2 fix #3 — scope: this test validates **Phase 9 only**.
  The earlier docstring claimed Block G3 (coordinator-mode prompt)
  coverage as well, but the explicit user prompt directly instructs
  three `task` calls, so a passing R3 does NOT prove the coordinator
  block was injected — that path needs its own assertion (covered
  by Block-G3 unit tests in tests/integration/test_block_g3.py).
  R3 keeps coordinator_mode_enabled=True only to exercise the
  augmented system prompt without claiming it.

Note on "parallel": v5's task tool is `is_concurrency_safe=False` —
  spawn is synchronous. The 3 dispatches are SEQUENTIAL on the
  parent's call stack. The TEST_PLAYBOOK label "Three parallel
  sub-agents" reflects the v4/Runnable phrasing; on v5 we test the
  real implementation: 3 ordered sub-agent dispatches with parent
  synthesis. True async parallel sub-agents land in a future phase.

Validation pillars:
  - subagent_dispatches audit entries == 3 (Phase 9 task tool spawn).
  - All 3 dispatches are subagent_type='explore'.
  - Each task dispatch prompt names exactly ONE assigned file
    (one-to-one task→file mapping).
  - The 3 utility files were read by CHILD sessions (not the parent
    session), proving the explore children did the work.
  - Zero parent-session read_file dispatches (so the parent didn't
    bypass the children).
  - findings.md exists and contains all 3 function names + the 3
    distinctive TODO body phrases (children's transcription survived
    the parent synthesis without lossy compression).
  - Parent stop_reason != max_turns.
  - Cost <= $0.50.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R3_COST_CAP_USD = 0.50

# ============================================================
# 3 small Python file fixtures — distinctive function names + TODOs
# so each sub-agent has unambiguous content to extract.
# ============================================================

_UTILS_A = '''"""Module A — string utilities."""


def kebab_case(text: str) -> str:
    """Convert spaces and underscores to hyphens; lowercase the result.

    Examples:
      'Hello World' -> 'hello-world'
      'snake_case_text' -> 'snake-case-text'
    """
    # TODO(R3-marker-A): handle Unicode whitespace beyond ASCII space.
    return text.replace("_", " ").lower().replace(" ", "-")
'''

_UTILS_B = '''"""Module B — numeric utilities."""


def clamp(value: float, lo: float, hi: float) -> float:
    """Constrain *value* to the inclusive range [lo, hi].

    If lo > hi the function returns *value* unchanged.
    """
    # TODO(R3-marker-B): raise ValueError when lo > hi instead of silent fall-through.
    if lo > hi:
        return value
    return max(lo, min(hi, value))
'''

_UTILS_C = '''"""Module C — list utilities."""


def chunked(items, size):
    """Yield successive *size*-length chunks from *items*.

    The final chunk may be shorter than *size* if the input length
    is not a multiple of *size*.
    """
    # TODO(R3-marker-C): support negative or zero size with a clear error.
    for i in range(0, len(items), size):
        yield items[i:i + size]
'''

_FUNCTION_NAMES = ("kebab_case", "clamp", "chunked")
# Codex Phase B iter-1 fix (after AWS call #1 fail): the original
# `_MARKERS` tuple checked for `R3-marker-A/B/C` literals which the
# children naturally drop when extracting "TODO text" (model treats
# the parenthetical marker as metadata). Replaced with distinctive
# TODO BODY phrases that the children DO transcribe — same
# falsifiability with model-realistic extraction.
_TODO_BODIES = (
    "Unicode whitespace",            # utils_a.py TODO body fragment
    "raise ValueError when lo > hi",  # utils_b.py TODO body fragment
    "negative or zero size",         # utils_c.py TODO body fragment
)

_R3_PROMPT = (
    "There are three Python files in the current directory: utils_a.py, "
    "utils_b.py, utils_c.py. Each defines exactly ONE public function "
    "and contains exactly ONE `# TODO(...)` comment.\n\n"
    "TASK:\n"
    "1. Spawn THREE sub-agents using the `task` tool, ONE PER FILE. Use "
    "subagent_type='explore' for each (read-only is sufficient).\n"
    "   - Sub-agent 1 prompt: 'Read utils_a.py. Report the function name, "
    "what the function does in one sentence, and the exact TODO comment "
    "text from that file. Reply in this format:\\nFUNCTION: <name>\\n"
    "SUMMARY: <one-sentence>\\nTODO: <todo text>'\n"
    "   - Sub-agent 2 prompt: same but for utils_b.py.\n"
    "   - Sub-agent 3 prompt: same but for utils_c.py.\n"
    "2. After ALL three sub-agents return, write a single Markdown report "
    "named `findings.md` in the current directory using the `write_file` "
    "tool. The report MUST contain three sections (one per file), each "
    "with the function name, one-sentence summary, and the TODO text "
    "extracted by the corresponding sub-agent.\n\n"
    "Do NOT ask for confirmation. Proceed directly. Stop when "
    "findings.md is written."
)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R3 is real-AWS gated.",
)
def test_r3_three_subagents_synthesis(tmp_path):
    """R-tier R3 — three sub-agent dispatches + parent synthesis.

    PASS criteria:
      - audit_log records exactly 3 task-tool dispatches with subagent_type='explore'.
      - findings.md exists.
      - findings.md mentions all 3 function names AND all 3 TODO body phrases.
      - parent stop_reason != max_turns.
      - cost <= $0.50.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from runtime.audit import AUDIT
    from core.budget import IterationBudget
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_coord = getattr(CONFIG, "coordinator_mode_enabled", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    cwd_before = os.getcwd()

    captured_stdout: list = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        try:
            print(text)
        except Exception:
            pass

    try:
        # ------------------------------------------------------------
        # Workspace fixture — 3 utility files
        # ------------------------------------------------------------
        (tmp_path / "utils_a.py").write_text(_UTILS_A, encoding="utf-8")
        (tmp_path / "utils_b.py").write_text(_UTILS_B, encoding="utf-8")
        (tmp_path / "utils_c.py").write_text(_UTILS_C, encoding="utf-8")

        # Audit dir lives next to the workspace so we can re-read its
        # JSONL after the run for the subagent_dispatches assertion.
        audit_dir = tmp_path / "audit_logs"
        audit_dir.mkdir(exist_ok=True)

        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R3_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        # Cap per-turn output cost. R3 worst case = parent (~10 turns) +
        # 3 children (~3 turns each) ≈ 19 turns × max_tokens. Keep tight.
        CONFIG.max_tokens = 2048
        CONFIG.require_tool_approval = False
        CONFIG.coordinator_mode_enabled = True
        # Codex iter-1 fix #3 (low): explicit local-traces enable so the
        # audit_log JSONLs we read for `subagent_dispatches` and
        # children-read assertions are guaranteed to write.
        CONFIG.disable_local_traces = False
        sec_mgr.rebuild_singleton_for_tests()
        # Re-init audit singleton with the new audit_dir.
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R3_COST_CAP_USD
            )

        # Codex iter-1 fix #4 (cost-risk): explicit shared IterationBudget
        # cap. Default is 600 — way too high for an R-tier $0.50 test.
        # Parent ~10 + 3 children ~3 each ≈ 19 turns expected; cap at 24
        # gives modest retry headroom while halting any runaway loop
        # well within the cost cap.
        shared_budget = IterationBudget(max_iterations=24)
        agent = Agent(
            client=client,
            max_turns=18,  # parent budget — children share IterationBudget
            budget=shared_budget,
            on_stop_check=_hard_cost_halt,
        )

        # Pre-promote `task` + `write_file` from deferred → visible so the
        # parent doesn't need a tool_search round-trip just to dispatch.
        # Phase 9 (task tool) is what we're validating; tool_search is
        # already covered by other Block-tagged tests.
        agent._engine._discovered_tool_names = {"task", "write_file"}

        # Codex iter-2 fix #1 (medium): capture the parent's session_id
        # BEFORE run(), so we can split audit entries into parent vs
        # child sessions for the read_file evidence assertion.
        parent_session_id = agent._engine.session_id

        t0 = time.time()
        result = agent.run(_R3_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        # ------------------------------------------------------------
        # Read audit_log for subagent_dispatches + child read_file calls
        # ------------------------------------------------------------
        # AUDIT writes one JSONL per session per date (parent + children
        # have distinct session_ids per spawn.py:77). Collect all entries.
        audit_entries: list = []
        for f in audit_dir.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                audit_entries.append(e)

        task_dispatches = [
            e for e in audit_entries
            if e.get("tool_name") == "task" and e.get("action") == "tool_dispatch"
        ]
        explore_dispatches = [
            d for d in task_dispatches
            if (d.get("parameters") or {}).get("subagent_type") == "explore"
        ]
        # Codex iter-1 fix #2 + iter-2 fix #1 (medium): children-actually-read
        # evidence — must come from CHILD sessions, not the parent session.
        # Without the session split, the parent could discover read_file via
        # tool_search and read all 3 files itself, passing the assertion
        # without using the sub-agents.
        all_read_file_dispatches = [
            e for e in audit_entries
            if e.get("tool_name") == "read_file" and e.get("action") == "tool_dispatch"
        ]
        parent_read_file_dispatches = [
            e for e in all_read_file_dispatches
            if e.get("session_id") == parent_session_id
        ]
        child_read_file_dispatches = [
            e for e in all_read_file_dispatches
            if e.get("session_id") != parent_session_id
        ]
        files_read_by_children = set()
        for e in child_read_file_dispatches:
            params = e.get("parameters") or {}
            fp = str(params.get("file_path") or params.get("path") or "")
            for fname in ("utils_a.py", "utils_b.py", "utils_c.py"):
                if fname in fp:
                    files_read_by_children.add(fname)
        # Codex iter-2 fix #2 (medium): each `task` prompt MUST mention
        # exactly ONE of the 3 utility files. Confirms the parent
        # scoped each dispatch to a specific file (one-to-one mapping)
        # rather than dispatching 3 generic prompts.
        task_prompt_file_targets: list = []
        for d in task_dispatches:
            params = d.get("parameters") or {}
            prompt_text = str(params.get("prompt") or "")
            hit_files = [
                fname for fname in ("utils_a.py", "utils_b.py", "utils_c.py")
                if fname in prompt_text
            ]
            task_prompt_file_targets.append(hit_files)

        findings_fp = tmp_path / "findings.md"
        findings_text = (
            findings_fp.read_text(encoding="utf-8") if findings_fp.is_file() else ""
        )
        function_hits = [n for n in _FUNCTION_NAMES if n in findings_text]
        todo_body_hits = [b for b in _TODO_BODIES if b in findings_text]

        metrics = {
            "test": "R3",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": int(getattr(result, "turns_used", 0)),
            "api_calls": int(api_calls),
            "cost_usd": round(cost_used, 4),
            "stop_reason": result.stop_reason,
            "task_dispatches": len(task_dispatches),
            "explore_dispatches": len(explore_dispatches),
            "parent_read_file_dispatches": len(parent_read_file_dispatches),
            "child_read_file_dispatches": len(child_read_file_dispatches),
            "files_read_by_children": sorted(files_read_by_children),
            "task_prompt_file_targets": task_prompt_file_targets,
            "parent_session_id": parent_session_id,
            "findings_exists": findings_fp.is_file(),
            "function_hits": function_hits,
            "todo_body_hits": todo_body_hits,
            "findings_size_bytes": (
                findings_fp.stat().st_size if findings_fp.is_file() else 0
            ),
            "coordinator_mode_enabled": True,
        }
        (tmp_path / "_r3_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R3 METRICS] {json.dumps(metrics)}")

        # ------------------------------------------------------------
        # Assertions
        # ------------------------------------------------------------
        assert result.stop_reason != "max_turns", (
            f"R3 parent hit max_turns (18); incomplete. metrics={metrics}"
        )
        # Codex iter-1 fix #1 (medium): exactly 3 dispatches — not >=3.
        # The R3 claim is "three sub-agents, one per file"; retries weaken
        # both falsifiability and cost-control.
        assert len(task_dispatches) == 3, (
            f"R3 expected EXACTLY 3 task-tool dispatches; got "
            f"{len(task_dispatches)}. metrics={metrics}"
        )
        assert len(explore_dispatches) == 3, (
            f"R3 expected EXACTLY 3 dispatches with subagent_type='explore'; "
            f"got {len(explore_dispatches)}. metrics={metrics}"
        )
        # Codex iter-1 fix #2 + iter-2 fix #1 (medium): each utility file
        # MUST be read from a CHILD session (not the parent's session).
        assert files_read_by_children == {"utils_a.py", "utils_b.py", "utils_c.py"}, (
            f"R3 expected each child to read its assigned utils_*.py; "
            f"child sessions actually read: {sorted(files_read_by_children)}. "
            f"child_read_file_dispatches={len(child_read_file_dispatches)}. "
            f"metrics={metrics}"
        )
        # Codex iter-2 fix #1 (medium): the parent must NOT bypass the
        # children by reading utils_*.py itself. Allow the parent to
        # have its own read_file dispatches for OTHER files (none expected
        # in this test, but be permissive about generic read_file calls
        # that hit some unrelated path) — but ensure none of them target
        # the 3 utility files.
        parent_target_hits = []
        for e in parent_read_file_dispatches:
            params = e.get("parameters") or {}
            fp = str(params.get("file_path") or params.get("path") or "")
            for fname in ("utils_a.py", "utils_b.py", "utils_c.py"):
                if fname in fp:
                    parent_target_hits.append((fname, fp))
        assert not parent_target_hits, (
            f"R3 parent session bypassed children by reading utils_*.py "
            f"directly: {parent_target_hits}. metrics={metrics}"
        )
        # Codex iter-2 fix #2 (medium): one-to-one task→file mapping —
        # each task dispatch's prompt mentions exactly ONE utility file,
        # and the 3 dispatches collectively cover all 3 files.
        targets_singletons = [t for t in task_prompt_file_targets if len(t) == 1]
        assert len(targets_singletons) == 3, (
            f"R3 expected each of 3 task prompts to mention exactly ONE "
            f"utility file; got: {task_prompt_file_targets}. metrics={metrics}"
        )
        targeted_files = {t[0] for t in targets_singletons}
        assert targeted_files == {"utils_a.py", "utils_b.py", "utils_c.py"}, (
            f"R3 expected the 3 task prompts to collectively target all 3 "
            f"utility files; got {sorted(targeted_files)}. metrics={metrics}"
        )
        assert findings_fp.is_file(), (
            f"R3 findings.md not produced. metrics={metrics}"
        )
        assert len(function_hits) == 3, (
            f"R3 findings.md missing function name(s). expected all of "
            f"{_FUNCTION_NAMES}; found {function_hits}. "
            f"body[:500]={findings_text[:500]!r}"
        )
        assert len(todo_body_hits) == 3, (
            f"R3 findings.md missing TODO body content. expected all of "
            f"{_TODO_BODIES}; found {todo_body_hits}. "
            f"body[:500]={findings_text[:500]!r}"
        )
        assert cost_used <= _R3_COST_CAP_USD, (
            f"R3 cost ${cost_used:.4f} exceeded cap ${_R3_COST_CAP_USD}. "
            f"metrics={metrics}"
        )
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec
        if saved_cost_limit is not None:
            CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
        if saved_coord is not None:
            CONFIG.coordinator_mode_enabled = saved_coord
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
            AUDIT.__init__(audit_dir=saved_audit_dir)
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
        TOKENS.reset()
