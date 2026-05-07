from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import zipfile
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[3]
STATUS_DIR = ROOT / "compact_v5" / "_status" / "ps_ps_v4_fresh_compare"
WORKSPACE_ROOT = ROOT.parent / "sageagent_psps_v4_fresh_workspaces"
PROMPT_TEMPLATE = STATUS_DIR / "benchmark_task_prompt.md"
MODEL_ID = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "ap-southeast-2"
CAP_USD = 5.00


REQUIRED = [
    "mini_research_worklog/__init__.py",
    "mini_research_worklog/models.py",
    "mini_research_worklog/store.py",
    "mini_research_worklog/search.py",
    "mini_research_worklog/report.py",
    "mini_research_worklog/cli.py",
    "tests/test_models.py",
    "tests/test_store.py",
    "tests/test_search.py",
    "tests/test_cli.py",
    "docs/DESIGN.md",
    "docs/RESEARCH.md",
    "docs/TEST_REPORT.md",
    "docs/REVIEW.md",
    "docs/logs",
    "docs/reviews",
    "AGENT_STATUS.md",
    "README.md",
    "pyproject.toml",
]


def _clean_workspace(path: Path) -> None:
    resolved = path.resolve()
    allowed_root = WORKSPACE_ROOT.resolve()
    if os.path.commonpath([str(resolved), str(allowed_root)]) != str(allowed_root):
        raise RuntimeError(f"Refusing to clean unsafe workspace: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def _run_pytest(workspace: Path, log_path: Path) -> Dict[str, Any]:
    if not (workspace / "tests").exists():
        _write(log_path, "NO_TESTS_DIR\n")
        return {"returncode": None, "summary": "NO_TESTS_DIR"}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q"],
            cwd=str(workspace),
            text=True,
            capture_output=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        _write(
            log_path,
            stdout
            + "\n--- STDERR ---\n"
            + stderr
            + "\n--- HARNESS ---\nPYTEST_TIMEOUT_AFTER_240_SECONDS\n",
        )
        return {
            "returncode": "timeout",
            "summary": "PYTEST_TIMEOUT_AFTER_240_SECONDS",
        }
    _write(log_path, proc.stdout + "\n--- STDERR ---\n" + proc.stderr)
    last = (proc.stdout.strip().splitlines() or [""])[-1]
    return {"returncode": proc.returncode, "summary": last}


def _validate_zip(workspace: Path) -> Dict[str, Any]:
    zips = sorted(workspace.glob("*.zip"))
    if not zips:
        return {"valid": False, "zip": "", "error": "no zip found"}
    latest = zips[-1]
    try:
        with zipfile.ZipFile(latest, "r") as zf:
            bad = zf.testzip()
            members = len(zf.namelist())
        return {
            "valid": bad is None,
            "zip": str(latest),
            "error": "" if bad is None else f"bad member: {bad}",
            "size_bytes": latest.stat().st_size,
            "members": members,
        }
    except Exception as exc:
        return {"valid": False, "zip": str(latest), "error": f"{type(exc).__name__}: {exc}"}


def _presence(workspace: Path) -> Dict[str, bool]:
    return {item: (workspace / item).exists() for item in REQUIRED}


def _review_files(workspace: Path) -> List[str]:
    root = workspace / "docs" / "reviews"
    if not root.exists():
        return []
    return [str(p.relative_to(workspace)) for p in sorted(root.rglob("*")) if p.is_file()]


def _log_files(workspace: Path) -> List[str]:
    root = workspace / "docs" / "logs"
    if not root.exists():
        return []
    return [str(p.relative_to(workspace)) for p in sorted(root.rglob("*")) if p.is_file()]


def _configure_common(config: Any, workspace: Path) -> None:
    config.workspace = str(workspace)
    config.sessions_dir = str(workspace / ".sessions")
    config.audit_dir = str(workspace / "audit_logs")
    config.region = REGION
    config.model_id = MODEL_ID
    config.mock_mode = False
    config.require_tool_approval = False
    config.session_cost_limit = CAP_USD
    config.max_budget_usd = CAP_USD
    config.max_turns = 90
    config.max_tokens = 4096
    config.temperature = 0.0
    config.thinking_enabled = False
    config.thinking_budget = 4096
    config.context_max_tokens = 200000
    config.max_iteration_budget = 300
    config.disable_local_traces = False
    config.bash_allow_interpreters = True
    config.enable_status_doc = True
    config.status_doc = "AGENT_STATUS.md"
    if hasattr(config, "enable_subagent_handoff"):
        config.enable_subagent_handoff = True
    if hasattr(config, "enable_memory_extraction"):
        config.enable_memory_extraction = True


def run_v4(workspace: Path, prompt: str) -> Dict[str, Any]:
    agent_root = ROOT / "compact_v4" / "MAIN" / "agent"
    sys.path.insert(0, str(agent_root))
    os.chdir(str(agent_root))
    sm = importlib.import_module("sagemaker_agent")
    _configure_common(sm.CONFIG, workspace)
    client = sm.BedrockClient(sm.CONFIG.model_id, sm.CONFIG.region, sm.CONFIG.mock_mode)
    agent = sm.Agent(client)
    out: List[str] = []
    started = time.time()
    result_text = agent.run(prompt, output_fn=lambda s: out.append(str(s)))
    elapsed = time.time() - started
    stats = {
        "session_cost_usd": float(getattr(sm.TOKENS, "session_cost", 0.0) or 0.0),
        "session_input": int(getattr(sm.TOKENS, "session_input", 0) or 0),
        "session_output": int(getattr(sm.TOKENS, "session_output", 0) or 0),
        "api_calls": int(getattr(sm.TOKENS, "api_calls", 0) or 0),
    }
    return {"agent": "v4", "elapsed_seconds": elapsed, "result_text": str(result_text or ""), "outputs": out, "stats": stats}


def run_v5(workspace: Path, prompt: str) -> Dict[str, Any]:
    agent_root = ROOT / "compact_v5" / "MAIN" / "agent"
    sys.path.insert(0, str(agent_root))
    os.chdir(str(agent_root))
    entry = importlib.import_module("entry")
    bedrock_mod = importlib.import_module("runtime.bedrock_client")
    budget_mod = importlib.import_module("core.budget")
    tokens_mod = importlib.import_module("runtime.tokens")
    _configure_common(entry.CONFIG, workspace)
    client = bedrock_mod.BedrockClient(entry.CONFIG.model_id, entry.CONFIG.region, entry.CONFIG.mock_mode)
    budget = budget_mod.IterationBudget(max_iterations=entry.CONFIG.max_iteration_budget)
    agent = entry.Agent(client=client, max_turns=entry.CONFIG.max_turns, budget=budget)
    out: List[str] = []
    started = time.time()
    result = agent.run(prompt, output_fn=lambda s: out.append(str(s)))
    elapsed = time.time() - started
    return {
        "agent": "v5",
        "elapsed_seconds": elapsed,
        "result_text": getattr(result, "text", str(result)),
        "stop_reason": getattr(result, "stop_reason", ""),
        "turns_used": getattr(result, "turns_used", None),
        "outputs": out,
        "stats": tokens_mod.TOKENS.get_stats(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["v4", "v5"], required=True)
    args = parser.parse_args()

    workspace = WORKSPACE_ROOT / args.agent
    logs = STATUS_DIR / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _clean_workspace(workspace)

    prompt = PROMPT_TEMPLATE.read_text(encoding="utf-8").replace("{{WORKSPACE}}", str(workspace))
    _write(logs / f"{args.agent}-prompt.md", prompt)

    try:
        run = run_v4(workspace, prompt) if args.agent == "v4" else run_v5(workspace, prompt)
        error = ""
    except Exception:
        run = {"agent": args.agent, "outputs": [], "result_text": "", "stats": {}}
        error = traceback.format_exc()

    _write(logs / f"{args.agent}-agent-output.log", "\n".join(run.get("outputs", [])))
    _write(logs / f"{args.agent}-agent-final.txt", str(run.get("result_text", "")))
    if error:
        _write(logs / f"{args.agent}-error.log", error)

    pytest_result = _run_pytest(workspace, logs / f"{args.agent}-pytest.log")
    zip_result = _validate_zip(workspace)
    presence = _presence(workspace)
    stats = run.get("stats", {}) if isinstance(run.get("stats", {}), dict) else {}
    subagent_costs = stats.get("subagent_cost_usd", {}) or {}
    review_files = _review_files(workspace)
    log_files = _log_files(workspace)

    summary = {
        "agent": args.agent,
        "model": MODEL_ID,
        "region": REGION,
        "cap_usd": CAP_USD,
        "error": bool(error),
        "error_log": str(logs / f"{args.agent}-error.log") if error else "",
        "run": {k: v for k, v in run.items() if k not in {"outputs", "result_text"}},
        "stats": stats,
        "subagent_used": bool(subagent_costs),
        "subagent_cost_usd": subagent_costs,
        "review_files": review_files,
        "log_files": log_files,
        "pytest": pytest_result,
        "zip": zip_result,
        "required_present": presence,
        "required_present_count": sum(1 for ok in presence.values() if ok),
        "required_total": len(presence),
        "workspace": str(workspace),
    }
    # The fresh comparison is a software-engineering benchmark, not an archive
    # benchmark. A zip may be recorded if present, but it is not required for
    # acceptance unless a future prompt explicitly makes it part of REQUIRED.
    summary["acceptance_pass"] = (
        summary["required_present_count"] == summary["required_total"]
        and pytest_result.get("returncode") == 0
        and bool(review_files)
        and bool(log_files)
        and (
            args.agent != "v5"
            or (summary["subagent_used"] and summary["run"].get("stop_reason") == "end_turn")
        )
    )
    _write(logs / f"{args.agent}-summary.json", json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not error else 1


if __name__ == "__main__":
    raise SystemExit(main())
