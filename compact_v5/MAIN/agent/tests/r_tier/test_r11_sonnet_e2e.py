"""R-tier R11 - Sonnet 4.5 end-to-end composite workflow.

R11 validates production-model compatibility by running an R1-style dashboard
workflow on Sonnet 4.5 AU: read CSV, compute summary, create a PNG chart, and
create a Word report with verifiable body content.

This is intentionally not bundled with R1/R7/R17:
  - R1 proves the composite workflow on Haiku.
  - R7 proves a live Haiku -> Sonnet model switch without tools.
  - R17 proves Sonnet thinking visibility without tools/artifacts.
  - R11 proves the full tool/artifact loop works on Sonnet itself.

Cost cap: $1.50 planned / $1.80 hard retry ceiling. Model: Sonnet 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import pytest


_AGENT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


_SONNET_45_AU = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"
_R11_COST_CAP_USD = 1.50
_R11_HARD_CEILING_USD = _R11_COST_CAP_USD * 1.20

_SAMPLE_CSV = (
    "category,units,revenue\n"
    "Books,120,2400\n"
    "Toys,80,3200\n"
    "Electronics,45,9000\n"
    "Garden,60,1800\n"
    "Apparel,200,5000\n"
)

_R11_PROMPT = (
    "You are working in the current directory. There is a file called "
    "`sales.csv` with columns: category, units, revenue.\n\n"
    "TASK:\n"
    "1. Read sales.csv.\n"
    "2. Summarize total revenue and the top 2 categories by revenue.\n"
    "3. Create a bar chart PNG of revenue by category and save it as "
    "`chart.png` in the current directory.\n"
    "4. Create a Word document `report.docx` with heading `Sales Report`, "
    "summary text mentioning total revenue and top categories, and a reference "
    "to chart.png.\n\n"
    "Use the available tools. Proceed directly; do not ask for confirmation. "
    "Stop when both chart.png and report.docx are written."
)


def _audit_events(audit_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for fp in sorted(audit_dir.glob("*.jsonl")):
        for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _docx_text(docx_path: Path) -> str:
    with zipfile.ZipFile(str(docx_path)) as docx_zip:
        if "word/document.xml" not in docx_zip.namelist():
            return ""
        return docx_zip.read("word/document.xml").decode("utf-8", errors="replace")


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R11 is real-AWS gated.",
)
def test_r11_sonnet_composite_dashboard_workflow(tmp_path):
    """R11 passes when Sonnet completes the R1-style artifact workflow."""
    from agent import Agent
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = (
        _REPO_ROOT
        / "compact_v5"
        / "_status"
        / "r_tier_runtime"
        / f"R11-call{call}-audit"
    )
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = (
        _REPO_ROOT
        / "compact_v5"
        / "_status"
        / f"r-tier-R11-aws-call{call}-side-metrics.json"
    )

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_temperature = getattr(CONFIG, "temperature", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    saved_enable_prompt_cache = getattr(CONFIG, "enable_prompt_cache", None)
    cwd_before = os.getcwd()

    try:
        (tmp_path / "sales.csv").write_text(_SAMPLE_CSV, encoding="utf-8")

        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R11_HARD_CEILING_USD
        CONFIG.model_id = _SONNET_45_AU
        CONFIG.max_tokens = 2048
        CONFIG.temperature = 0.0
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        CONFIG.enable_prompt_cache = True
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_SONNET_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt() -> bool:
            if hasattr(TOKENS, "is_over_budget"):
                return TOKENS.is_over_budget()
            return TOKENS.session_cost >= _R11_HARD_CEILING_USD

        agent = Agent(client=client, max_turns=35, on_stop_check=_hard_cost_halt)
        t0 = time.time()
        result = agent.run(_R11_PROMPT)
        wallclock_s = time.time() - t0

        chart_fp = tmp_path / "chart.png"
        report_fp = tmp_path / "report.docx"
        chart_exists = chart_fp.is_file()
        report_exists = report_fp.is_file()
        chart_png_valid = False
        chart_size = 0
        if chart_exists:
            chart_size = chart_fp.stat().st_size
            with chart_fp.open("rb") as fh:
                chart_png_valid = fh.read(4) == b"\x89PNG"
        report_docx_valid = report_exists and zipfile.is_zipfile(str(report_fp))
        doc_xml = _docx_text(report_fp) if report_docx_valid else ""
        heading_ok = "Sales Report" in doc_xml or "sales report" in doc_xml.lower()
        category_hits = [
            c for c in ("Electronics", "Apparel", "Books", "Toys", "Garden")
            if c in doc_xml
        ]
        revenue_match = ("21400" in doc_xml) or ("21,400" in doc_xml)
        top2_match = ("14000" in doc_xml) or ("14,000" in doc_xml)

        events = _audit_events(audit_dir)
        tool_dispatches = [e for e in events if e.get("action") == "tool_dispatch"]
        failure_loop_events = [
            e for e in events
            if str(e.get("action")) in {
                "tool_failure_recorded",
                "tool_failure_loop_warning",
                "tool_failure_loop_blocked",
            }
        ]
        stats = TOKENS.get_stats() if hasattr(TOKENS, "get_stats") else {}
        model_usage = stats.get("model_usage", {}) if isinstance(stats, dict) else {}
        cost_used = float(TOKENS.session_cost)
        completed = bool(
            result.stop_reason != "max_turns"
            and chart_exists
            and chart_png_valid
            and chart_size >= 1000
            and report_docx_valid
            and heading_ok
            and bool(category_hits)
            and (revenue_match or top2_match)
            and cost_used <= _R11_HARD_CEILING_USD
        )
        metrics = {
            "test": "R11",
            "call": call,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _SONNET_45_AU,
            "tokens_in": int(TOKENS.session_input),
            "tokens_out": int(TOKENS.session_output),
            "cache_hit_pct": round(
                float(TOKENS.session_cache_read)
                / max(
                    1,
                    int(TOKENS.session_input)
                    + int(TOKENS.session_cache_read)
                    + int(TOKENS.session_cache_write),
                ),
                4,
            ),
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": len(tool_dispatches),
            "api_calls": int(TOKENS.api_calls),
            "subagent_calls": 0,
            "reviewer_calls": 0,
            "subagent_tokens_in": 0,
            "subagent_tokens_out": 0,
            "subagent_cost_usd": 0.0,
            "reviewer_tokens_in": 0,
            "reviewer_tokens_out": 0,
            "reviewer_cost_usd": 0.0,
            "cost_usd": round(cost_used, 4),
            "cost_cap_usd": _R11_COST_CAP_USD,
            "hard_ceiling_usd": _R11_HARD_CEILING_USD,
            "stop_reason": result.stop_reason,
            "chart_exists": chart_exists,
            "chart_png_valid": chart_png_valid,
            "chart_size": chart_size,
            "report_exists": report_exists,
            "report_docx_valid": report_docx_valid,
            "heading_ok": heading_ok,
            "category_hits": category_hits,
            "revenue_or_top2_match": revenue_match or top2_match,
            "model_usage": model_usage,
            "session_cache_read": int(TOKENS.session_cache_read),
            "session_cache_write": int(TOKENS.session_cache_write),
            "parent_cache_read_tokens": int(TOKENS.parent_cache_read_tokens),
            "parent_cache_write_tokens": int(TOKENS.parent_cache_write_tokens),
            "tool_names": [str(e.get("tool_name")) for e in tool_dispatches],
            "failure_loop_events": len(failure_loop_events),
            "process_quality_ok": len(failure_loop_events) == 0 and cost_used <= _R11_HARD_CEILING_USD,
            "completed": completed,
            "verdict": "GENUINE_PASS" if completed else "FAIL",
            "audit_dir": str(audit_dir),
            "final_text": (result.text or "")[:500],
        }
        side_metrics.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
        print(f"\n[R11_AUDIT_DIR] {audit_dir}")
        print(f"[R11_SIDE_METRICS] {side_metrics}")
        print(f"[R11_METRICS] {json.dumps(metrics, sort_keys=True, default=str)}")

        assert result.stop_reason != "max_turns", f"R11 hit max_turns. metrics={metrics}"
        assert chart_exists, f"R11 did not produce chart.png. metrics={metrics}"
        assert chart_png_valid, f"R11 chart.png is not a PNG. metrics={metrics}"
        assert chart_size >= 1000, f"R11 chart.png too small ({chart_size}). metrics={metrics}"
        assert report_exists, f"R11 did not produce report.docx. metrics={metrics}"
        assert report_docx_valid, f"R11 report.docx invalid. metrics={metrics}"
        assert heading_ok, f"R11 report.docx missing Sales Report heading. metrics={metrics}"
        assert category_hits, f"R11 report.docx missing CSV categories. metrics={metrics}"
        assert revenue_match or top2_match, (
            f"R11 report.docx missing revenue evidence 21400/14000. metrics={metrics}"
        )
        assert not failure_loop_events, f"R11 had failure-loop events: {failure_loop_events}"
        assert cost_used <= _R11_HARD_CEILING_USD, (
            f"R11 cost ${cost_used:.4f} exceeded cap ${_R11_COST_CAP_USD:.2f} "
            f"plus 20% retry buffer (${_R11_HARD_CEILING_USD:.2f}). metrics={metrics}"
        )
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_temperature is not None:
            CONFIG.temperature = saved_temperature
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
        if saved_enable_prompt_cache is not None:
            CONFIG.enable_prompt_cache = saved_enable_prompt_cache
        sec_mgr.SECURITY = saved_sec
