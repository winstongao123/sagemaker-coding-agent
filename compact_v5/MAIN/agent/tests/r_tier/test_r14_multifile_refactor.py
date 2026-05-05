"""R-tier R14 - multi-file refactor test.

Validates that the real Bedrock-backed agent can perform a cross-file symbol
rename, update visible call sites, run tests, and prove no stale symbol remains.
The test is skipped unless RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


_AGENT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R14_COST_CAP_USD = 0.75
_OLD_SYMBOL = "compute_discounted_total"
_NEW_SYMBOL = "calculate_order_total"

_FIXTURE_FILES = {
    "inventory_app/__init__.py": '''\
from .pricing import compute_discounted_total
from .orders import build_order_summary

__all__ = ["compute_discounted_total", "build_order_summary"]
''',
    "inventory_app/pricing.py": '''\
def compute_discounted_total(items, discount_pct=0):
    subtotal = sum(item["qty"] * item["unit_price"] for item in items)
    discount = subtotal * (discount_pct / 100)
    return round(subtotal - discount, 2)
''',
    "inventory_app/orders.py": '''\
from .pricing import compute_discounted_total


def build_order_summary(items, customer_tier):
    discount = 10 if customer_tier == "gold" else 0
    return {
        "item_count": sum(item["qty"] for item in items),
        "total": compute_discounted_total(items, discount),
    }
''',
    "inventory_app/reports.py": '''\
from .pricing import compute_discounted_total


def render_total_line(items, discount_pct):
    total = compute_discounted_total(items, discount_pct)
    return f"Total after discount: ${total:.2f}"
''',
    "tests/test_orders.py": '''\
from inventory_app import build_order_summary, compute_discounted_total
from inventory_app.reports import render_total_line


def test_calculates_discounted_total():
    items = [{"qty": 2, "unit_price": 5.0}, {"qty": 1, "unit_price": 4.0}]
    assert compute_discounted_total(items, discount_pct=25) == 10.5


def test_order_summary_uses_discounted_total_for_gold_customers():
    items = [{"qty": 3, "unit_price": 10.0}]
    assert build_order_summary(items, "gold") == {"item_count": 3, "total": 27.0}


def test_report_uses_same_total_helper():
    items = [{"qty": 1, "unit_price": 12.0}]
    assert render_total_line(items, 50) == "Total after discount: $6.00"
''',
    "README.md": '''\
# Inventory App

The public pricing helper is `compute_discounted_total`.

Visible call sites:
- inventory_app/orders.py calls compute_discounted_total for order summaries.
- inventory_app/reports.py calls compute_discounted_total for report output.
- tests/test_orders.py imports compute_discounted_total directly.
''',
}

_R14_PROMPT = f"""You are working in the current directory.

Refactor the inventory_app package by renaming the public helper
`{_OLD_SYMBOL}` to `{_NEW_SYMBOL}` everywhere in this fixture.

Requirements:
- Update source files, tests, exports, and README.md references.
- Preserve behavior.
- Run pytest.
- Search/grep the fixture for `{_OLD_SYMBOL}` after editing and ensure there
  are no stale references.
- Do not create files outside the current directory.
- Stop once pytest passes and the stale-symbol search is clean.
"""


def _write_fixture(workspace: Path) -> None:
    for rel, text in _FIXTURE_FILES.items():
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")


def _run_pytest(workspace: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=str(workspace),
        text=True,
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _grep_stale_symbol(workspace: Path) -> list[str]:
    hits: list[str] = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        parts = set(path.parts)
        if {"__pycache__", ".pytest_cache", ".sageagent_state"} & parts:
            continue
        if path.suffix not in {".py", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _OLD_SYMBOL in line:
                hits.append(f"{path.relative_to(workspace).as_posix()}:{line_no}:{line}")
    return hits


def _new_symbol_visible(workspace: Path) -> bool:
    required_files = [
        "inventory_app/__init__.py",
        "inventory_app/pricing.py",
        "inventory_app/orders.py",
        "inventory_app/reports.py",
        "tests/test_orders.py",
        "README.md",
    ]
    return all(_NEW_SYMBOL in (workspace / rel).read_text(encoding="utf-8") for rel in required_files)


def _r14_ready(workspace: Path) -> bool:
    code, _output = _run_pytest(workspace)
    return code == 0 and not _grep_stale_symbol(workspace) and _new_symbol_visible(workspace)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R14 is real-AWS gated.",
)
def test_r14_multifile_refactor(tmp_path):
    """R14 passes when pytest is green and stale-symbol grep is clean."""
    from agent import Agent
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    _write_fixture(tmp_path)
    pre_code, pre_output = _run_pytest(tmp_path)
    assert pre_code == 0, f"R14 fixture should start green before refactor. output={pre_output}"
    initial_stale_hits = _grep_stale_symbol(tmp_path)
    assert len(initial_stale_hits) >= 6, f"R14 fixture must expose visible old-symbol call sites: {initial_stale_hits}"

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"R14-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-R14-aws-call{call}-side-metrics.json"

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    cwd_before = os.getcwd()
    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R14_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 2048
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt() -> bool:
            over_budget = TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R14_COST_CAP_USD
            )
            return over_budget or _r14_ready(tmp_path)

        captured_stdout: list[str] = []

        def _stdout_capture(text: str) -> None:
            captured_stdout.append(text)
            print(text)

        agent = Agent(client=client, max_turns=18, on_stop_check=_hard_cost_halt)
        t0 = time.time()
        result = agent.run(_R14_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        post_code, post_output = _run_pytest(tmp_path)
        stale_hits = _grep_stale_symbol(tmp_path)
        new_symbol_visible = _new_symbol_visible(tmp_path)
        workspace_files = sorted(
            p.relative_to(tmp_path).as_posix()
            for p in tmp_path.rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and ".pytest_cache" not in p.parts
            and ".sageagent_state" not in p.parts
        )
        expected_files = sorted(_FIXTURE_FILES.keys())
        unexpected_files = sorted(set(workspace_files) - set(expected_files))
        cost_used = float(TOKENS.session_cost)

        metrics = {
            "test": "R14",
            "call": call,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(TOKENS.session_input),
            "tokens_out": int(TOKENS.session_output),
            "cache_hit_pct": 0.0,
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": int(getattr(result, "turns_used", 0)),
            "api_calls": int(TOKENS.api_calls),
            "subagent_calls": 0,
            "reviewer_calls": 0,
            "subagent_tokens_in": 0,
            "subagent_tokens_out": 0,
            "subagent_cost_usd": 0.0,
            "reviewer_tokens_in": 0,
            "reviewer_tokens_out": 0,
            "reviewer_cost_usd": 0.0,
            "changed_files_within_fixture": True,
            "pre_refactor_pytest_passed": pre_code == 0,
            "post_refactor_pytest_passed": post_code == 0,
            "post_refactor_pytest_output_tail": post_output[-2000:],
            "initial_stale_hit_count": len(initial_stale_hits),
            "stale_symbol_grep_output": stale_hits,
            "stale_symbol_count": len(stale_hits),
            "new_symbol_visible": bool(new_symbol_visible),
            "fixture_note_visible_call_sites": True,
            "unexpected_files": unexpected_files,
            "completed": bool(
                result.stop_reason in {"end_turn", "user_stop"}
                and post_code == 0
                and not stale_hits
                and new_symbol_visible
                and not unexpected_files
                and cost_used <= _R14_COST_CAP_USD
            ),
            "cost_usd": round(cost_used, 4),
            "verdict": "GENUINE_PASS" if (
                post_code == 0
                and not stale_hits
                and new_symbol_visible
                and not unexpected_files
                and cost_used <= _R14_COST_CAP_USD
            ) else "FAIL",
            "stop_reason": result.stop_reason,
            "audit_dir": str(audit_dir),
        }
        side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[R14_AUDIT_DIR] {audit_dir}")
        print(f"[R14_SIDE_METRICS] {side_metrics}")
        print(f"[R14_METRICS] {json.dumps(metrics, sort_keys=True)}")

        assert result.stop_reason in {"end_turn", "user_stop"}, (
            f"R14 ended with non-ready stop_reason={result.stop_reason!r}. metrics={metrics}"
        )
        assert post_code == 0, f"R14 pytest failed after refactor. metrics={metrics}"
        assert not stale_hits, f"R14 stale-symbol grep found old names. metrics={metrics}"
        assert new_symbol_visible, f"R14 new symbol missing from visible call sites. metrics={metrics}"
        assert not unexpected_files, f"R14 produced unexpected files {unexpected_files}. metrics={metrics}"
        assert cost_used <= _R14_COST_CAP_USD, (
            f"R14 cost ${cost_used:.4f} exceeded cap ${_R14_COST_CAP_USD}. metrics={metrics}"
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
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
