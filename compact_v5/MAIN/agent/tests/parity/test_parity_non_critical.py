"""Phase 12 — Non-critical parity scenarios (V5_PLAN.md §Phase 12, ADR-018).

≥9/10 must pass. Failures are documented in PORT_LOG #035 (parity
appendix) with rationale.

Scenarios encode v4-equivalent behavior where exact byte-equality isn't
required for ship — these are surface details where v5 may legitimately
diverge from v4 (e.g. better-engineered error wording, per-tool result
caps vs global cap). The point of the gate: catch any DRIFT > 1
non-critical scenario at once.

10 non-critical scenarios:
  01. tool_result truncation length (v5 per-tool cap)
  02. error message exact wording (close enough)
  03. skill description CSO format advisory
  04. audit-log line format on skill propose
  05. widget HTML markup contains progress element
  06. depth-exceeded message wording
  07. plan-mode error message wording
  08. tool_search wire format (<functions>...</functions>)
  09. frontmatter parser CSV+YAML list both work
  10. env-details line count (≤6 — v4 contract)
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


@pytest.fixture(autouse=True)
def _fresh_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


# ============================================================
# 01 — tool_result truncation respects per-tool max_result_size_chars
# v4 had global cap; v5 tightens to per-tool. (Documented divergence.)
# ============================================================

def test_noncritical_01_tool_result_truncation_respects_per_tool_cap():
    from core.query_engine import _truncate_tool_result
    text = "x" * 5000
    truncated = _truncate_tool_result(text, max_chars=1000)
    assert len(truncated) <= 1000
    assert "truncated" in truncated.lower()


# ============================================================
# 02 — error message wording: registry deduplication
# ============================================================

def test_noncritical_02_registry_duplicate_error_message():
    from tools.registry import build_tool, register, ToolRecord

    register(build_tool(
        name="dup_test_tool",
        description="x",
        input_schema={"type": "object", "properties": {}},
        execute=lambda a, context=None: "ok",
    ))
    with pytest.raises(ValueError) as exc_info:
        register(build_tool(
            name="dup_test_tool",
            description="y",
            input_schema={"type": "object", "properties": {}},
            execute=lambda a, context=None: "x",
        ))
    msg = str(exc_info.value)
    assert "already registered" in msg
    assert "unregister" in msg


# ============================================================
# 03 — Skill description CSO format advisory
# v4 logs DEBUG (not WARNING) when description doesn't start with "Use when"
# ============================================================

def test_noncritical_03_skill_description_cso_advisory(tmp_path, caplog):
    import logging
    from skills.manager import SkillManager

    sd = tmp_path / "skills"
    (sd / "noncso").mkdir(parents=True)
    (sd / "noncso" / "SKILL.md").write_text(
        "---\nname: noncso\ndescription: Some description without CSO format.\n---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    with caplog.at_level(logging.DEBUG, logger="root"):
        sm.discover()
    advisories = [r for r in caplog.records if "CSO-CHECK" in r.message]
    assert len(advisories) >= 1, "v4 contract: log DEBUG for non-CSO descriptions"


# ============================================================
# 04 — Audit log line format on skill propose
# ============================================================

def test_noncritical_04_skill_audit_log_line_format(tmp_path, caplog):
    import logging
    from skills.manager import SkillManager

    sd = tmp_path / "skills"
    (sd / "audit").mkdir(parents=True)
    (sd / "audit" / "SKILL.md").write_text(
        "---\nname: audit\ndescription: Use when audit.\n---\noriginal", encoding="utf-8")
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    sm.discover()
    with caplog.at_level(logging.INFO):
        ok, _ = sm.propose_patch("audit", "improve clarity", "patched body")
    assert ok
    audit_lines = [r for r in caplog.records if "skill-audit" in r.message]
    assert len(audit_lines) >= 1


# ============================================================
# 05 — Widget HTML markup contains <progress> tag
# ============================================================

def test_noncritical_05_budget_widget_html_has_progress_element():
    from core import IterationBudget
    from ui.widgets import IterationBudgetWidget
    w = IterationBudgetWidget(budget=IterationBudget(max_iterations=10))
    html = w.render_html()
    assert "<progress" in html
    assert "max=" in html


# ============================================================
# 06 — Depth-exceeded message wording
# ============================================================

def test_noncritical_06_depth_exceeded_wording():
    from core import QueryEngine, IterationBudget
    from subagent.spawn import spawn_subagent

    parent = QueryEngine(client=None, max_turns=1, budget=IterationBudget())
    result = spawn_subagent(
        parent_engine=parent, prompt="x", agent_type="general",
        parent_depth=2, max_depth=2,
    )
    assert result.stop_reason == "depth_exceeded"
    assert "depth" in (result.error or "").lower()


# ============================================================
# 07 — Plan-mode error message contains tool name + plan-mode reference
# ============================================================

def test_noncritical_07_plan_mode_error_wording():
    from core import QueryEngine
    from tools import all_registered
    from runtime.bedrock_client import Response, ToolCall

    class _C:
        def __init__(self):
            self.calls = 0
        def chat(self, **kw):
            self.calls += 1
            if self.calls == 1:
                return Response(text="", tool_calls=[ToolCall("p", "edit_file", {"file_path": "x", "old_string": "a", "new_string": "b"})], stop_reason="tool_use")
            return Response(text="ok", tool_calls=[], stop_reason="end_turn")

    eng = QueryEngine(client=_C(), max_turns=3)
    result = eng.run("edit", system_prompt="sys", tools=all_registered(), plan_mode=True)
    err_msg = result.messages[2]["content"][0]["content"]
    assert "edit_file" in err_msg
    low = err_msg.lower()
    assert "plan mode" in low or "plan_mode_allowed_tools" in low


# ============================================================
# 08 — tool_search wire format <functions>...</functions>
# ============================================================

def test_noncritical_08_tool_search_wire_format():
    from tools import find_tool_by_name, all_registered
    ts = find_tool_by_name(all_registered(), "tool_search")
    out = ts.execute({"query": "select:view_image"})
    assert "<functions>" in out
    assert "</functions>" in out
    assert "view_image" in out


# ============================================================
# 09 — Frontmatter parser handles CSV + YAML list for both fields
# ============================================================

def test_noncritical_09_frontmatter_csv_and_yaml_list_both_work(tmp_path):
    from skills.manager import SkillManager

    sd = tmp_path / "skills"
    (sd / "csv_form").mkdir(parents=True)
    (sd / "csv_form" / "SKILL.md").write_text(
        "---\nname: csv_form\ndescription: x\nrequires_tools: bash, python_exec\n---\nbody",
        encoding="utf-8")
    (sd / "yaml_form").mkdir(parents=True)
    (sd / "yaml_form" / "SKILL.md").write_text(
        "---\nname: yaml_form\ndescription: x\nrequires_tools:\n  - bash\n  - python_exec\n---\nbody",
        encoding="utf-8")
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    sm.discover()
    assert sm._cache["csv_form"].requires_tools == ["bash", "python_exec"]
    assert sm._cache["yaml_form"].requires_tools == ["bash", "python_exec"]


# ============================================================
# 10 — env-details ≤ 6 lines (v4 Haiku-budget contract)
# ============================================================

def test_noncritical_10_env_details_line_count():
    from subagent.env import build_env_details
    out = build_env_details(agent_type="general", depth=1, workspace="/tmp")
    line_count = len(out.splitlines())
    assert line_count <= 6, f"env-details v4 contract: ≤6 lines, got {line_count}"
