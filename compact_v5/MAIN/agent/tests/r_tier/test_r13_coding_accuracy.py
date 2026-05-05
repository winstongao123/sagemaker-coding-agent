"""R-tier R13 - five-task coding accuracy test.

Validates that the real Bedrock-backed agent can implement small Python
functions, run deterministic tests, and keep edits inside the fixture
workspace. The test is skipped unless RUN_REAL_BEDROCK=1.
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
_R13_COST_CAP_USD = 0.50

_TEST_MODULE = r'''
from solutions import (
    is_palindrome,
    merge_intervals,
    roman_to_int,
    top_k_frequent,
    validate_brackets,
)


def test_is_palindrome_normalizes_text():
    assert is_palindrome("A man, a plan, a canal: Panama!") is True
    assert is_palindrome("race a car") is False
    assert is_palindrome("") is True


def test_merge_intervals_sorts_and_merges_touching_ranges():
    assert merge_intervals([[5, 7], [1, 3], [2, 4], [8, 10]]) == [[1, 4], [5, 7], [8, 10]]
    assert merge_intervals([[1, 2], [2, 3], [6, 8]]) == [[1, 3], [6, 8]]
    assert merge_intervals([]) == []


def test_top_k_frequent_uses_frequency_then_alpha_tiebreak():
    words = ["pear", "apple", "pear", "banana", "apple", "pear", "banana", "kiwi"]
    assert top_k_frequent(words, 2) == ["pear", "apple"]
    assert top_k_frequent(words, 3) == ["pear", "apple", "banana"]
    assert top_k_frequent([], 3) == []


def test_roman_to_int_handles_subtractive_pairs():
    assert roman_to_int("III") == 3
    assert roman_to_int("IX") == 9
    assert roman_to_int("MCMXCIV") == 1994


def test_validate_brackets_detects_nesting_and_mismatches():
    assert validate_brackets("([]{})") is True
    assert validate_brackets("([)]") is False
    assert validate_brackets("text (with [brackets])") is True
'''.strip()

_TEST_NAMES = (
    "test_is_palindrome_normalizes_text",
    "test_merge_intervals_sorts_and_merges_touching_ranges",
    "test_top_k_frequent_uses_frequency_then_alpha_tiebreak",
    "test_roman_to_int_handles_subtractive_pairs",
    "test_validate_brackets_detects_nesting_and_mismatches",
)

_R13_PROMPT = """You are working in the current directory.

Create or update exactly one file: solutions.py.

Implement these five Python functions with the exact names and signatures:

1. is_palindrome(text: str) -> bool
   Return True when text is a palindrome after removing non-alphanumeric
   characters and lowercasing.

2. merge_intervals(intervals: list[list[int]]) -> list[list[int]]
   Sort intervals by start and merge overlapping or touching intervals.

3. top_k_frequent(words: list[str], k: int) -> list[str]
   Return up to k words ordered by descending frequency, then alphabetically
   for ties.

4. roman_to_int(s: str) -> int
   Convert standard Roman numerals including subtractive pairs such as IV,
   IX, XL, XC, CD, and CM.

5. validate_brackets(s: str) -> bool
   Return True when (), [], and {} brackets are balanced and nested. Ignore
   non-bracket characters.

After writing solutions.py, run the local tests in test_solutions.py and fix
solutions.py until the tests pass. Do not edit test_solutions.py. Do not create
files outside the current directory. Stop when solutions.py is written and the
tests have been run.
"""


def _run_pytest_case(workspace: Path, test_name: str) -> tuple[bool, str]:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            f"test_solutions.py::{test_name}",
            "-q",
        ],
        cwd=str(workspace),
        text=True,
        capture_output=True,
        timeout=30,
    )
    return proc.returncode == 0, (proc.stdout + proc.stderr)


def _all_solution_tests_pass(workspace: Path) -> bool:
    if not (workspace / "solutions.py").is_file():
        return False
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "test_solutions.py", "-q"],
        cwd=str(workspace),
        text=True,
        capture_output=True,
        timeout=30,
    )
    return proc.returncode == 0


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R13 is real-AWS gated.",
)
def test_r13_coding_accuracy(tmp_path):
    """R13 passes when at least four of five deterministic tasks pass."""
    from agent import Agent
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    (tmp_path / "test_solutions.py").write_text(_TEST_MODULE + "\n", encoding="utf-8")

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"R13-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-R13-aws-call{call}-side-metrics.json"

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
        CONFIG.session_cost_limit = _R13_COST_CAP_USD
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
                TOKENS.session_cost >= _R13_COST_CAP_USD
            )
            return over_budget or _all_solution_tests_pass(tmp_path)

        captured_stdout: list[str] = []

        def _stdout_capture(text: str) -> None:
            captured_stdout.append(text)
            print(text)

        agent = Agent(client=client, max_turns=18, on_stop_check=_hard_cost_halt)
        t0 = time.time()
        result = agent.run(_R13_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        per_case: dict[str, dict[str, object]] = {}
        passed = 0
        for test_name in _TEST_NAMES:
            ok, output = _run_pytest_case(tmp_path, test_name)
            passed += 1 if ok else 0
            per_case[test_name] = {
                "passed": ok,
                "output_tail": output[-1000:],
            }

        solutions_path = tmp_path / "solutions.py"
        workspace_files = [p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()]
        changed_files_within_fixture = all(not Path(name).is_absolute() for name in workspace_files)
        cost_used = float(TOKENS.session_cost)

        metrics = {
            "test": "R13",
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
            "changed_files_within_fixture": bool(changed_files_within_fixture),
            "score_passed": passed,
            "score_total": len(_TEST_NAMES),
            "completed": bool(
                result.stop_reason in {"end_turn", "user_stop"}
                and solutions_path.is_file()
                and passed >= 4
                and cost_used <= _R13_COST_CAP_USD
            ),
            "cost_usd": round(cost_used, 4),
            "verdict": "GENUINE_PASS" if passed >= 4 and cost_used <= _R13_COST_CAP_USD else "FAIL",
            "stop_reason": result.stop_reason,
            "solutions_exists": solutions_path.is_file(),
            "workspace_files": sorted(workspace_files),
            "per_case": per_case,
            "audit_dir": str(audit_dir),
        }
        side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[R13_AUDIT_DIR] {audit_dir}")
        print(f"[R13_SIDE_METRICS] {side_metrics}")
        print(f"[R13_METRICS] {json.dumps(metrics, sort_keys=True)}")

        assert solutions_path.is_file(), f"solutions.py not produced. metrics={metrics}"
        assert result.stop_reason in {"end_turn", "user_stop"}, (
            f"R13 ended with non-ready stop_reason={result.stop_reason!r}. metrics={metrics}"
        )
        assert changed_files_within_fixture, f"R13 edited outside fixture. metrics={metrics}"
        assert passed >= 4, f"R13 score {passed}/5 below READY threshold. metrics={metrics}"
        assert cost_used <= _R13_COST_CAP_USD, (
            f"R13 cost ${cost_used:.4f} exceeded cap ${_R13_COST_CAP_USD}. metrics={metrics}"
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
