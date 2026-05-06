"""Zero-cost locks required by the remaining R-tier disposition review."""
from __future__ import annotations

import json
import os
import sys


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_r18_e4_skill_activation_is_canonical_name_not_alias(tmp_path):
    """R18-E4: v5 skill activation is canonical-name based, not alias based."""
    from skills.manager import SkillManager

    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "review"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: review\n"
        "description: Use when reviewing code changes.\n"
        "aliases: rvw, codecheck\n"
        "---\n"
        "# Review\n",
        encoding="utf-8",
    )

    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(skills_dir))
    discovered = sm.discover()

    assert "review" in discovered
    assert sm.resolve_name("review") == "review"
    assert sm.resolve_name("Review") == "review"
    assert sm.resolve_name("rvw") is None
    assert sm.resolve_name("codecheck") is None


def test_r18_e11_subagent_timeout_survives_parent_compaction_and_resume():
    """R18-E11: timeout envelope can be compacted and parent can continue."""
    from core import IterationBudget, QueryEngine
    from core.compactor import Compactor
    from runtime.bedrock_client import Response
    from tools import all_registered, find_tool_by_name

    class _Client:
        mock_mode = True
        model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"

        def __init__(self):
            self.calls = 0

        def chat(self, *args, **kwargs):
            self.calls += 1
            return Response("parent continued after timeout", [], "end_turn", {})

    budget = IterationBudget(max_iterations=1)
    budget.consume()
    parent = QueryEngine(client=_Client(), max_turns=3, budget=budget)
    parent.messages = [
        {"role": "user", "content": "project checkpoint: ALPHA-17"},
        {"role": "assistant", "content": "checkpoint recorded"},
        {"role": "user", "content": "dispatch child and recover if it times out"},
    ]
    task_tool = find_tool_by_name(all_registered(), "task")

    out = task_tool.execute(
        {"prompt": "do a slow child task", "subagent_type": "general"},
        context={"parent_engine": parent, "parent_depth": 0},
    )
    payload = out.split("[subagent_result_envelope]", 1)[1].strip()
    envelope = json.loads(payload)
    assert envelope["stop_reason"] == "budget_exhausted"
    assert envelope["heartbeat"]["timed_out"] is True

    parent.messages.append({"role": "user", "content": out})
    compacted = Compactor.compact(
        parent.messages,
        "Project checkpoint ALPHA-17 remains active; child timed out and parent should continue.",
    )
    compacted_text = json.dumps(compacted, ensure_ascii=False)
    assert "ALPHA-17" in compacted_text
    assert "child timed out" in compacted_text

    parent.messages = compacted
    parent.budget = IterationBudget(max_iterations=2)
    result = parent.run("continue from the timeout", "system", [])

    assert result.stop_reason == "end_turn"
    assert "parent continued after timeout" in result.text


def test_r18_e13_unicode_rtl_memory_round_trips_through_dream(tmp_path):
    """R18-E13: Unicode/RTL memory survives the read/write/dream path."""
    from runtime.dream import run_dream

    original = (
        "# Memory\n"
        "- Preferred greeting: hello, \u4f60\u597d, \u0645\u0631\u062d\u0628\u0627, "
        "\u05e9\u05dc\u05d5\u05dd, \U0001f600\n"
        "- RTL note: \u05e2\u05d1\u05e8\u05d9\u05ea then English then "
        "\u0627\u0644\u0639\u0631\u0628\u064a\u0629.\n"
        "- Escaped surrogate-like text remains literal: "
        "\\\\u" "d83d" "\\\\u" "de00\n"
    )
    (tmp_path / "memory.md").write_text(original, encoding="utf-8")

    result = run_dream(str(tmp_path), consolidator=lambda existing, manifest: existing)

    assert result.success is True
    assert (tmp_path / "memory.md").read_text(encoding="utf-8") == original
    assert (tmp_path / "memory.md.bak").read_text(encoding="utf-8") == original
    assert result.phases_executed == ["Orient", "Gather", "Consolidate", "Prune+Index"]
