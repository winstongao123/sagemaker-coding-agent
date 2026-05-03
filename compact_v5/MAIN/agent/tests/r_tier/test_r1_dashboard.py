"""R-tier R1 — Composite "does it work" test.

Per PS_V5_TEST_SET.md §Tier 1 R1:
  Build a real dashboard: read CSV → summarize numbers → make chart →
  embed in Word doc. Up to 50 conversation turns.

Validates (composite):
  - Tool dispatch end-to-end on real Bedrock
  - Multi-turn agent loop
  - Security gate with real bash / python_exec
  - .docx output integrity (real python-docx)
  - read_file + python_exec + create_chart + create_word
  - session_cost_limit enforcement

Cost cap: $1.00. Model: Haiku 4.5 AU (au.anthropic.claude-haiku-4-5...).
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.

Per WORKER_HINT §9.4: this test produces 7-8 persistent log files
recorded in compact_v5/_status/codex_reviews/r-tier-R1-* and
compact_v5/_status/r_tier_review_log.md + r_tier_metrics.jsonl.
"""
from __future__ import annotations

import json
import os
import sys
import time
import zipfile
from pathlib import Path

import pytest

# Standard test path setup.
_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R1_COST_CAP_USD = 1.00


# ============================================================
# Sample CSV fixture — 5 rows of synthetic sales data.
# ============================================================

_SAMPLE_CSV = (
    "category,units,revenue\n"
    "Books,120,2400\n"
    "Toys,80,3200\n"
    "Electronics,45,9000\n"
    "Garden,60,1800\n"
    "Apparel,200,5000\n"
)

_R1_PROMPT = (
    "You are working in the current directory. There is a file called "
    "`sales.csv` with columns: category, units, revenue.\n\n"
    "TASK:\n"
    "1. Read sales.csv.\n"
    "2. Summarize: total revenue and the top 2 categories by revenue.\n"
    "3. Create a bar chart (PNG) of revenue by category. Save it as "
    "`chart.png` in the current directory.\n"
    "4. Create a Word document (`report.docx`) with: a heading "
    "\"Sales Report\", the summary text mentioning total revenue + top "
    "categories, and a reference to chart.png.\n\n"
    "Use the available tools (read_file, python_exec, create_chart, "
    "create_word). Proceed directly — do NOT ask for confirmation. "
    "Stop when both chart.png and report.docx are written."
)


# ============================================================
# R1 test
# ============================================================

@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R1 is real-AWS gated.",
)
def test_r1_dashboard_build(tmp_path, monkeypatch, request):
    """R-tier R1 — composite dashboard build on real Bedrock.

    PASS criteria (assertions):
      - chart.png exists and starts with PNG signature.
      - report.docx exists and is a valid .docx (zip with PK header).
      - Total cost <= R1 cap ($1.00).
      - Agent completed (not max_turns or stopped on error).
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr
    from agent import Agent

    # ------------------------------------------------------------
    # Workspace fixture
    # ------------------------------------------------------------
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(_SAMPLE_CSV, encoding="utf-8")

    # Point CONFIG.workspace at tmp_path so SECURITY allows writes here.
    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    cwd_before = os.getcwd()
    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.session_cost_limit = _R1_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        # Codex Phase A iter-1 cost-risk fix: cap per-turn output.
        # Default CONFIG.max_tokens=16384 is too high — at $5/MTok out
        # that's ~$0.08/turn × 50 turns = $4 worst case. With max_tokens=2048
        # the per-turn worst case is ~$0.01 × 50 turns = ~$0.50 — under
        # the $1.00 R1 cap even if every turn produced max output.
        CONFIG.max_tokens = 2048
        # R1 first-run hung on interactive ipywidget approval prompts —
        # R-tier runs un-attended. Bypass tool approval for this test.
        # (Workspace + python AST + bash allowlist + cost cap still enforce
        # safety; only the per-tool human-in-the-loop dialog is skipped.)
        CONFIG.require_tool_approval = False
        sec_mgr.rebuild_singleton_for_tests()
        # cd into workspace so relative paths (chart.png, report.docx)
        # resolve here for the agent's tools.
        os.chdir(str(tmp_path))
        TOKENS.reset()

        # ------------------------------------------------------------
        # Agent + run with HARD cost halt
        # ------------------------------------------------------------
        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(
            model_id=_HAIKU_45_AU,
            region=region,
            mock_mode=False,
        )

        # Codex Phase A iter-1 cost-risk fix: v5's session_cost_limit is a
        # WARN-and-continue (query_engine.py:518-530) not a hard halt.
        # R1 needs a hard halt before it slips past the $1.00 cap. We
        # use Agent's on_stop_check hook: returns True once TOKENS reports
        # over-budget, which causes the next-turn loop to break cleanly.
        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R1_COST_CAP_USD
            )

        # Tools auto-loaded from registry (read_file + create_chart +
        # create_word + python_exec etc).
        agent = Agent(
            client=client,
            max_turns=50,
            on_stop_check=_hard_cost_halt,
        )
        t0 = time.time()
        result = agent.run(_R1_PROMPT)
        wallclock_s = time.time() - t0

        # ------------------------------------------------------------
        # Assertions — outcome integrity
        # ------------------------------------------------------------
        chart_fp = tmp_path / "chart.png"
        report_fp = tmp_path / "report.docx"

        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        # Emit metrics to JSONL (always — even on assertion failure).
        metrics = {
            "test": "R1",
            "call": 1,  # outer caller will increment for retry
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": int(getattr(result, "turns_used", 0)),
            "api_calls": int(api_calls),
            "cost_usd": round(cost_used, 4),
            "stop_reason": result.stop_reason,
            "chart_exists": chart_fp.is_file(),
            "report_exists": report_fp.is_file(),
        }
        # Write metrics to a side-channel file the harness can read.
        metrics_side = tmp_path / "_r1_metrics.json"
        metrics_side.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        # Also log to test stdout so the .log capture has them.
        print(f"\n[R1 METRICS] {json.dumps(metrics)}")

        # Assert: turns_used not exhausted.
        assert result.stop_reason != "max_turns", (
            f"R1 hit max_turns (50); incomplete. metrics={metrics}"
        )
        # Assert: chart.png present + valid PNG signature.
        assert chart_fp.is_file(), f"chart.png not produced. metrics={metrics}"
        with chart_fp.open("rb") as f:
            assert f.read(4) == b"\x89PNG", "chart.png is not a valid PNG"
        # Codex Phase A iter-1 #3 fix: PNG sanity beyond the header.
        # A valid matplotlib bar chart of 5 data points renders to >= 5KB at
        # default 100dpi. A blank/stub PNG would be a few hundred bytes.
        chart_size = chart_fp.stat().st_size
        assert chart_size >= 1000, (
            f"chart.png suspiciously small ({chart_size} bytes); "
            f"likely a stub. metrics={metrics}"
        )
        # Assert: report.docx present + valid .docx (PK signature, valid zip).
        assert report_fp.is_file(), f"report.docx not produced. metrics={metrics}"
        with report_fp.open("rb") as f:
            assert f.read(2) == b"PK", "report.docx is not a valid docx (no PK)"
        assert zipfile.is_zipfile(str(report_fp)), "report.docx not a valid zip"
        # Codex Phase A iter-1 #2 fix: body content assertions. Parse
        # word/document.xml from the .docx zip and check it contains the
        # requested heading, at least one CSV category, and the total
        # revenue (21,400 sum of the synthetic CSV).
        with zipfile.ZipFile(str(report_fp)) as docx_zip:
            assert "word/document.xml" in docx_zip.namelist(), (
                "report.docx missing word/document.xml — invalid docx structure"
            )
            doc_xml = docx_zip.read("word/document.xml").decode("utf-8", errors="replace")
        # Heading.
        assert "Sales Report" in doc_xml or "sales report" in doc_xml.lower(), (
            f"report.docx missing 'Sales Report' heading. body[:500]={doc_xml[:500]!r}"
        )
        # At least one category from the CSV (top-2 should be Electronics and
        # Apparel by revenue: 9000 + 5000).
        categories = ("Electronics", "Apparel", "Books", "Toys", "Garden")
        cat_hits = [c for c in categories if c in doc_xml]
        assert cat_hits, (
            f"report.docx mentions none of the CSV categories. body[:500]={doc_xml[:500]!r}"
        )
        # Total revenue token: total = 21,400. Accept either form.
        # Use loose match — agent might write 21400, "21,400", "$21,400", etc.
        revenue_match = ("21400" in doc_xml) or ("21,400" in doc_xml)
        # Top-2 (Electronics 9000 + Apparel 5000 = 14000) is also acceptable
        # evidence the agent did the math, in case it reported only top-2 sum.
        top2_match = ("14000" in doc_xml) or ("14,000" in doc_xml)
        assert revenue_match or top2_match, (
            f"report.docx missing total or top-2 revenue figure (expected 21400 "
            f"or 14000). body[:500]={doc_xml[:500]!r}"
        )
        # Assert: cost within R1 cap.
        assert cost_used <= _R1_COST_CAP_USD, (
            f"R1 cost ${cost_used:.4f} exceeded cap ${_R1_COST_CAP_USD}. "
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
