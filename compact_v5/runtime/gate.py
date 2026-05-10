"""Deterministic local verify/done gate for long software runs.

SOFTWARE-GATE turns `/verify` and `/done` from advisory skill prompts into
workspace-backed close gates. The gate is intentionally local and zero-cost:
it reads fresh evidence files, writes a verification record, and gives a
repeatable pass/fail result that `/done` must consume.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from runtime.state import _atomic_write_json, _utc_now


FRESHNESS_SECONDS = 24 * 60 * 60
SCHEMA = "sageagent.verify_gate.v1"


@dataclass
class EvidenceCheck:
    category: str
    ok: bool
    reason: str
    paths: List[str] = field(default_factory=list)


@dataclass
class GateResult:
    mode: str
    ok: bool
    checks: List[EvidenceCheck]
    record_path: str = ""

    @property
    def blocking_reasons(self) -> List[str]:
        return [f"{c.category}: {c.reason}" for c in self.checks if not c.ok]

    def to_record(self, command: str) -> Dict[str, Any]:
        return {
            "schema": SCHEMA,
            "command": command,
            "mode": self.mode,
            "ok": self.ok,
            "checked_at": _utc_now(),
            "checks": [
                {
                    "category": c.category,
                    "ok": c.ok,
                    "reason": c.reason,
                    "paths": c.paths,
                }
                for c in self.checks
            ],
        }


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (str, os.PathLike)):
        return [str(value)]
    if isinstance(value, Sequence):
        return [str(v) for v in value if v]
    return []


def _workspace() -> Path:
    from runtime.config import CONFIG

    return Path(getattr(CONFIG, "workspace", os.getcwd())).resolve()


def _state_dir(workspace: Optional[Path] = None) -> Path:
    return (workspace or _workspace()) / ".sageagent_state" / "gates"


def verification_record_path(workspace: Optional[Path] = None) -> Path:
    return _state_dir(workspace) / "last_verify.json"


def _resolve_path(path: str, workspace: Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = workspace / p
    return p.resolve()


def _ctx_evidence(ctx: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not ctx:
        return {}
    data = ctx.get("gate_evidence")
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _fresh_file(path: Path, freshness_seconds: int) -> Optional[str]:
    if not path.is_file():
        return "missing"
    try:
        age = time.time() - path.stat().st_mtime
    except OSError:
        return "unreadable"
    if age > freshness_seconds:
        return f"stale ({int(age)}s old > {freshness_seconds}s)"
    if not _read_text(path).strip():
        return "empty"
    return None


def _path_list(
    evidence: Dict[str, Any],
    key: str,
    workspace: Path,
    default: Iterable[Path] = (),
) -> List[Path]:
    raw = _as_list(evidence.get(key))
    if raw:
        return [_resolve_path(p, workspace) for p in raw]
    return [p.resolve() for p in default]


def _default_audit_logs(workspace: Path) -> List[Path]:
    from runtime.config import CONFIG

    audit_dir = Path(getattr(CONFIG, "audit_dir", workspace / "audit_logs"))
    if not audit_dir.is_absolute():
        audit_dir = workspace / audit_dir
    if not audit_dir.is_dir():
        return []
    try:
        return sorted(audit_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)[-5:]
    except OSError:
        return []


def _default_result_index(workspace: Path) -> List[Path]:
    path = workspace / ".sageagent_state" / "tool_results" / "index.jsonl"
    return [path] if path.is_file() else []


def _check_status(evidence: Dict[str, Any], workspace: Path, freshness_seconds: int) -> EvidenceCheck:
    from runtime.config import CONFIG

    status_path = evidence.get("status_path") or getattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    path = _resolve_path(str(status_path), workspace)
    problem = _fresh_file(path, freshness_seconds)
    if problem:
        return EvidenceCheck("status", False, problem, [str(path)])
    return EvidenceCheck("status", True, "fresh status file present", [str(path)])


def _check_paths(
    category: str,
    paths: List[Path],
    freshness_seconds: int,
    marker: Optional[re.Pattern[str]] = None,
    blocked_marker: Optional[re.Pattern[str]] = None,
) -> EvidenceCheck:
    if not paths:
        return EvidenceCheck(category, False, "no evidence paths supplied or discovered", [])
    failures: List[str] = []
    fresh_paths: List[str] = []
    for path in paths:
        problem = _fresh_file(path, freshness_seconds)
        if problem:
            failures.append(f"{path}: {problem}")
            continue
        text = _read_text(path)
        if blocked_marker and blocked_marker.search(text):
            failures.append(f"{path}: blocking marker present")
            continue
        if marker and not marker.search(text):
            failures.append(f"{path}: expected marker not found")
            continue
        fresh_paths.append(str(path))
    if fresh_paths:
        return EvidenceCheck(category, True, "fresh evidence accepted", fresh_paths)
    return EvidenceCheck(category, False, "; ".join(failures) or "no usable evidence", [str(p) for p in paths])


def _required_categories(mode: str, evidence: Dict[str, Any]) -> List[str]:
    if isinstance(evidence.get("required_categories"), Sequence) and not isinstance(
        evidence.get("required_categories"), str
    ):
        return [str(c) for c in evidence["required_categories"]]
    if mode == "quick":
        return ["status", "tests", "review"]
    return ["status", "tests", "review", "results", "subagent", "telemetry"]


def run_verify_gate(
    mode: str = "full",
    ctx: Optional[Dict[str, Any]] = None,
    *,
    persist: bool = True,
) -> GateResult:
    """Run the deterministic local evidence gate and optionally persist it."""
    workspace = _workspace()
    evidence = _ctx_evidence(ctx)
    freshness_seconds = int(evidence.get("freshness_seconds", FRESHNESS_SECONDS))
    mode = (mode or "full").lower()
    required = set(_required_categories(mode, evidence))
    audit_logs = _default_audit_logs(workspace)

    checks: List[EvidenceCheck] = []
    if "status" in required:
        checks.append(_check_status(evidence, workspace, freshness_seconds))
    if "tests" in required:
        checks.append(
            _check_paths(
                "tests",
                _path_list(evidence, "test_paths", workspace),
                freshness_seconds,
                marker=re.compile(r"\b(PASS|passed|success|ok)\b", re.I),
                blocked_marker=re.compile(r"\b(FAILED|ERROR|BLOCKED)\b", re.I),
            )
        )
    if "review" in required:
        checks.append(
            _check_paths(
                "review",
                _path_list(evidence, "review_paths", workspace),
                freshness_seconds,
                marker=re.compile(r"VERDICT:\s+APPROVE|SHIP DECISION:\s+READY_FOR", re.I),
                blocked_marker=re.compile(r"SHIP DECISION:\s+BLOCKED|VERDICT:\s+REJECT", re.I),
            )
        )
    if "results" in required:
        checks.append(
            _check_paths(
                "results",
                _path_list(evidence, "result_paths", workspace, _default_result_index(workspace)),
                freshness_seconds,
                marker=re.compile(r"sageagent-result://|tool_results|result_replay|artifact_path", re.I),
            )
        )
    if "subagent" in required:
        checks.append(
            _check_paths(
                "subagent",
                _path_list(evidence, "subagent_paths", workspace, audit_logs),
                freshness_seconds,
                marker=re.compile(r"sageagent\.subagent_result\.v1|subagent_result", re.I),
            )
        )
    if "telemetry" in required:
        checks.append(
            _check_paths(
                "telemetry",
                _path_list(evidence, "telemetry_paths", workspace, audit_logs),
                freshness_seconds,
                marker=re.compile(
                    r"compact_(auto|micro|failed)|tool_failure_(recorded|loop)|"
                    r"failure_loop_events|agent_attribution|cache_trend",
                    re.I,
                ),
                blocked_marker=re.compile(r"tool_failure_loop_(blocked|warning)", re.I),
            )
        )

    result = GateResult(mode=mode, ok=all(c.ok for c in checks), checks=checks)
    if persist:
        path = verification_record_path(workspace)
        _atomic_write_json(path, result.to_record("verify"))
        result.record_path = str(path)
    return result


def run_done_gate(mode: str = "full", ctx: Optional[Dict[str, Any]] = None) -> GateResult:
    """Require a fresh passing `/verify` record, then rerun evidence checks."""
    workspace = _workspace()
    evidence = _ctx_evidence(ctx)
    freshness_seconds = int(evidence.get("freshness_seconds", FRESHNESS_SECONDS))
    mode = (mode or "full").lower()
    checks: List[EvidenceCheck] = []

    record = verification_record_path(workspace)
    problem = _fresh_file(record, freshness_seconds)
    if problem:
        checks.append(EvidenceCheck("last_verify", False, problem, [str(record)]))
    else:
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if data.get("schema") != SCHEMA:
            checks.append(EvidenceCheck("last_verify", False, "invalid verify record schema", [str(record)]))
        elif data.get("mode") != mode:
            checks.append(
                EvidenceCheck(
                    "last_verify",
                    False,
                    f"last verify mode {data.get('mode')} does not match done mode {mode}",
                    [str(record)],
                )
            )
        elif not data.get("ok"):
            checks.append(EvidenceCheck("last_verify", False, "last verify failed", [str(record)]))
        else:
            checks.append(EvidenceCheck("last_verify", True, "fresh passing verify record", [str(record)]))

    verify_now = run_verify_gate(mode, ctx, persist=False)
    checks.extend(verify_now.checks)
    result = GateResult(mode=mode, ok=all(c.ok for c in checks), checks=checks)
    path = _state_dir(workspace) / "last_done.json"
    _atomic_write_json(path, result.to_record("done"))
    result.record_path = str(path)
    return result


def format_gate_result(result: GateResult, *, command: str) -> str:
    label = "PASSED" if result.ok else "BLOCKED"
    lines = [f"{command.upper()} {label} (mode: {result.mode})"]
    for check in result.checks:
        status = "PASS" if check.ok else "BLOCK"
        lines.append(f"- {status} {check.category}: {check.reason}")
    if result.record_path:
        lines.append(f"Evidence record: {result.record_path}")
    return "\n".join(lines)


__all__ = [
    "EvidenceCheck",
    "GateResult",
    "format_gate_result",
    "run_done_gate",
    "run_verify_gate",
    "verification_record_path",
]
