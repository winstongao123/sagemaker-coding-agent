"""R-tier R15 - planted-bug debugging test.

Validates that the real Bedrock-backed agent can diagnose two failing tests,
fix only the planted bugs, preserve a tempting false-positive helper, and leave
test evidence for the debugging path. The test is skipped unless
RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import hashlib
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
_R15_COST_CAP_USD = 0.50

_FALSE_POSITIVE_BLOCK = '''\
def classify_customer(customer):
    """Existing behavior: VIP customers keep their tier label unchanged."""
    tier = customer.get("tier", "standard")
    if customer.get("vip"):
        return f"vip:{tier}"
    return tier
'''.strip()

_BUGGY_MODULE = f'''\
from datetime import datetime


def summarize_invoice(lines, tax_rate=0.0):
    """Return rounded subtotal and total for invoice line items."""
    subtotal = sum(line["qty"] + line["unit_price"] for line in lines)
    return {{
        "subtotal": round(subtotal, 2),
        "total": round(subtotal * (1 + tax_rate), 2),
    }}


def parse_due_date(raw):
    """Accept an ISO YYYY-MM-DD date and return the same normalized date."""
    return datetime.strptime(raw, "%m-%d-%Y").date().isoformat()


{_FALSE_POSITIVE_BLOCK}
'''.strip()

_TEST_MODULE = '''\
from order_utils import classify_customer, parse_due_date, summarize_invoice


def test_summarize_invoice_multiplies_quantity_by_unit_price():
    lines = [
        {"sku": "A-1", "qty": 2, "unit_price": 3.50},
        {"sku": "B-9", "qty": 1, "unit_price": 4.00},
    ]
    assert summarize_invoice(lines, tax_rate=0.08) == {"subtotal": 11.00, "total": 11.88}


def test_parse_due_date_accepts_iso_yyyy_mm_dd():
    assert parse_due_date("2026-05-06") == "2026-05-06"


def test_classify_customer_false_positive_area_is_already_correct():
    assert classify_customer({"tier": "gold", "vip": True}) == "vip:gold"
    assert classify_customer({"tier": "silver", "vip": False}) == "silver"
'''.strip()

_R15_PROMPT = """You are working in the current directory.

The project has two planted bugs in order_utils.py and one helper that already
works. Your task is debugging, not a refactor.

Requirements:
- Read test_order_utils.py and order_utils.py.
- Run the tests before editing so you see the failures.
- Fix only the two planted bugs needed for the failing tests.
- Do not edit test_order_utils.py.
- Do not change classify_customer; it is the false-positive area and already works.
- Create diagnosis.md with the failing tests observed, root cause for each bug,
  and the final test command/output summary.
- Run the tests after editing and stop once they pass.
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_fixture_pytest(workspace: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "test_order_utils.py", "-q"],
        cwd=str(workspace),
        text=True,
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _false_positive_area_unchanged(path: Path) -> bool:
    return _FALSE_POSITIVE_BLOCK in path.read_text(encoding="utf-8", errors="replace")


def _diagnosis_trace_valid(workspace: Path) -> bool:
    diagnosis = workspace / "diagnosis.md"
    if not diagnosis.is_file():
        return False
    text = diagnosis.read_text(encoding="utf-8", errors="replace").lower()
    required = (
        "test_summarize_invoice_multiplies_quantity_by_unit_price",
        "test_parse_due_date_accepts_iso_yyyy_mm_dd",
        "qty",
        "unit_price",
        "yyyy-mm-dd",
    )
    return all(term in text for term in required)


def _r15_ready(workspace: Path) -> bool:
    code, _output = _run_fixture_pytest(workspace)
    return (
        code == 0
        and _false_positive_area_unchanged(workspace / "order_utils.py")
        and _diagnosis_trace_valid(workspace)
    )


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R15 is real-AWS gated.",
)
def test_r15_debugging_planted_bugs(tmp_path):
    """R15 passes when planted bugs are fixed and false-positive code is intact."""
    from agent import Agent
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    order_utils = tmp_path / "order_utils.py"
    tests = tmp_path / "test_order_utils.py"
    order_utils.write_text(_BUGGY_MODULE + "\n", encoding="utf-8")
    tests.write_text(_TEST_MODULE + "\n", encoding="utf-8")
    initial_test_hash = _sha256(tests)

    pre_code, pre_output = _run_fixture_pytest(tmp_path)
    (tmp_path / "pre_fix_pytest_output.txt").write_text(pre_output, encoding="utf-8")
    assert pre_code != 0, "R15 fixture must start with failing tests."
    assert "2 failed, 1 passed" in pre_output or "2 failed" in pre_output

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"R15-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-R15-aws-call{call}-side-metrics.json"

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
        CONFIG.session_cost_limit = _R15_COST_CAP_USD
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
                TOKENS.session_cost >= _R15_COST_CAP_USD
            )
            return over_budget or _r15_ready(tmp_path)

        captured_stdout: list[str] = []

        def _stdout_capture(text: str) -> None:
            captured_stdout.append(text)
            print(text)

        agent = Agent(client=client, max_turns=18, on_stop_check=_hard_cost_halt)
        t0 = time.time()
        result = agent.run(_R15_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        post_code, post_output = _run_fixture_pytest(tmp_path)
        (tmp_path / "post_fix_pytest_output.txt").write_text(post_output, encoding="utf-8")

        false_positive_area_unchanged = _false_positive_area_unchanged(order_utils)
        test_file_unchanged = _sha256(tests) == initial_test_hash
        diagnosis_trace = _diagnosis_trace_valid(tmp_path)
        expected_agent_files = {"order_utils.py", "diagnosis.md"}
        workspace_files = {
            p.relative_to(tmp_path).as_posix()
            for p in tmp_path.rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and ".pytest_cache" not in p.parts
            and ".sageagent_state" not in p.parts
        }
        runner_files = {
            "test_order_utils.py",
            "pre_fix_pytest_output.txt",
            "post_fix_pytest_output.txt",
        }
        unexpected_files = sorted(workspace_files - expected_agent_files - runner_files)
        cost_used = float(TOKENS.session_cost)

        metrics = {
            "test": "R15",
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
            "pre_fix_failed": pre_code != 0,
            "pre_fix_output_tail": pre_output[-2000:],
            "post_fix_passed": post_code == 0,
            "post_fix_output_tail": post_output[-2000:],
            "false_positive_area_unchanged": bool(false_positive_area_unchanged),
            "test_file_unchanged": bool(test_file_unchanged),
            "diagnosis_trace": bool(diagnosis_trace),
            "unexpected_files": unexpected_files,
            "completed": bool(
                result.stop_reason in {"end_turn", "user_stop"}
                and post_code == 0
                and false_positive_area_unchanged
                and test_file_unchanged
                and diagnosis_trace
                and not unexpected_files
                and cost_used <= _R15_COST_CAP_USD
            ),
            "cost_usd": round(cost_used, 4),
            "verdict": "GENUINE_PASS" if (
                post_code == 0
                and false_positive_area_unchanged
                and test_file_unchanged
                and diagnosis_trace
                and not unexpected_files
                and cost_used <= _R15_COST_CAP_USD
            ) else "FAIL",
            "stop_reason": result.stop_reason,
            "audit_dir": str(audit_dir),
        }
        side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[R15_AUDIT_DIR] {audit_dir}")
        print(f"[R15_SIDE_METRICS] {side_metrics}")
        print(f"[R15_METRICS] {json.dumps(metrics, sort_keys=True)}")

        assert result.stop_reason in {"end_turn", "user_stop"}, (
            f"R15 ended with non-ready stop_reason={result.stop_reason!r}. metrics={metrics}"
        )
        assert post_code == 0, f"R15 post-fix tests failed. metrics={metrics}"
        assert false_positive_area_unchanged, f"R15 changed false-positive area. metrics={metrics}"
        assert test_file_unchanged, f"R15 edited test file. metrics={metrics}"
        assert diagnosis_trace, f"R15 missing diagnosis trace. metrics={metrics}"
        assert not unexpected_files, f"R15 produced unexpected files {unexpected_files}. metrics={metrics}"
        assert cost_used <= _R15_COST_CAP_USD, (
            f"R15 cost ${cost_used:.4f} exceeded cap ${_R15_COST_CAP_USD}. metrics={metrics}"
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
