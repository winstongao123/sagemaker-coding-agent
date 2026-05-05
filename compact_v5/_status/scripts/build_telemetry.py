"""build_telemetry.py — R-tier + Block V telemetry aggregator.

Per PS_V5_TEST_PLAYBOOK.md §1 + WORKER_HINT_2026-05-03.md §9.3.

Aggregates raw audit_log JSONL + raw test stdout .log into a single
telemetry.json file matching the schema in PS_V5_TEST_SET.md "Per-test
diagnostic telemetry".

Inputs:
  --test    R-tier test name (e.g. R1, R12, V1)
  --call    AWS call number for this test (1, 2, or 3)
  --audit-log  path to MAIN/agent/audit_logs/<session_id>.jsonl
                (or directory — script will pick the latest jsonl in it)
  --raw-log    path to compact_v5/_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log
  --output     path to write the telemetry.json
  [--metrics-side-channel]  optional path to a JSON written by the test
                            itself (e.g. _r1_metrics.json) for fields the
                            audit_log doesn't carry (final TOKENS state).

Output: single JSON file at --output. Schema documented inline below.

The actual v5 audit_log only emits `tool_dispatch` events (no per-turn
chat_response usage), so this aggregator:
  - Groups tool_dispatch events into "turns" using a simple heuristic:
    consecutive dispatches within 30s belong to the same turn.
  - Pulls aggregate token/cost data from --metrics-side-channel (if
    provided) for total tokens, cost_usd, and outcome.
  - Counts REPEATED tool calls by (tool_name, args_hash) pairs.
  - Detects compact / subagent events via action types.
  - Falls back gracefully when fields are missing (records 'unknown'
    rather than crashing).

Validation: after writing, the script also JSON-parses the output and
checks required keys. Exits with code 1 if validation fails.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Required top-level keys per PLAYBOOK §1 validation.
REQUIRED_TOP_LEVEL_KEYS = {
    "test", "call", "per_turn", "tool_call_summary",
    "compaction_events", "subagent_dispatches",
    "cache_efficiency_trend", "agent_attribution",
    "failure_loop_events", "outcome",
}


def _stable_args_hash(args: Any) -> str:
    """Deterministic short hash of tool call args for REPEATED-call detection."""
    try:
        s = json.dumps(args, sort_keys=True, default=str)
    except Exception:
        s = repr(args)
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()[:12]


def _parse_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read a JSONL file. Each line = one event. Skip malformed lines."""
    events: List[Dict[str, Any]] = []
    if not path.is_file():
        return events
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # tolerate corruption
    return events


def _resolve_audit_log(audit_log_arg: Path) -> Optional[Path]:
    """If audit_log_arg is a file, return it. If a dir, pick the
    most recently modified .jsonl inside."""
    if audit_log_arg.is_file():
        return audit_log_arg
    if audit_log_arg.is_dir():
        candidates = sorted(
            audit_log_arg.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None
    return None


def _ts_to_seconds(ts_str: str) -> float:
    """Convert ISO-ish timestamp to fractional seconds since epoch.
    v5 audit_log uses ISO-8601 without timezone (e.g. '2026-05-03T16:25:32.873382')."""
    try:
        # Strip trailing Z if present.
        s = ts_str.rstrip("Z")
        # datetime.fromisoformat handles ISO-8601 fractional seconds.
        from datetime import datetime
        dt = datetime.fromisoformat(s)
        return dt.timestamp()
    except Exception:
        return 0.0


def _group_into_turns(events: List[Dict[str, Any]], window_s: float = 30.0) -> List[List[Dict[str, Any]]]:
    """Group chronologically-sorted tool_dispatch events into "turns".

    Heuristic: consecutive events within `window_s` belong to the same
    turn. A gap larger than `window_s` opens a new turn. This is a
    proxy for the true per-Bedrock-turn boundary because v5's audit_log
    doesn't emit a `chat_response` event with turn_number today.

    Per PLAYBOOK §1: "if [turn_number is] missing, use timestamp ordering".
    """
    if not events:
        return []
    # Sort by timestamp.
    events_sorted = sorted(events, key=lambda e: _ts_to_seconds(e.get("timestamp", "")))
    turns: List[List[Dict[str, Any]]] = [[events_sorted[0]]]
    last_t = _ts_to_seconds(events_sorted[0].get("timestamp", ""))
    for ev in events_sorted[1:]:
        t = _ts_to_seconds(ev.get("timestamp", ""))
        if t - last_t > window_s and turns[-1]:
            turns.append([])
        turns[-1].append(ev)
        last_t = t
    return turns


def _aggregate_per_turn(turns: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """One per_turn record per heuristic turn."""
    out = []
    for i, turn_events in enumerate(turns, start=1):
        timestamps = [_ts_to_seconds(e.get("timestamp", "")) for e in turn_events]
        wallclock = max(timestamps) - min(timestamps) if timestamps else 0.0
        tool_calls = [
            {
                "name": e.get("tool_name", "unknown"),
                "args_summary": str(e.get("parameters", ""))[:160],
                "args_hash": _stable_args_hash(e.get("parameters", {})),
                "user_approved": e.get("user_approved", None),
                "result_summary": str(e.get("result_summary", ""))[:160],
            }
            for e in turn_events
            if e.get("action") == "tool_dispatch"
        ]
        # PLAYBOOK §4.5 Gap A: pull chat_response.thinking + .usage from
        # any chat_response event in this turn (v5's BedrockClient emits
        # this when extended thinking is enabled; falls back to None+0
        # when the audit_log doesn't carry it).
        thinking_text: Optional[str] = None
        thinking_tokens: int = 0
        tokens_in_t: Optional[int] = None
        tokens_out_t: Optional[int] = None
        cache_read_t: Optional[int] = None
        cache_write_t: Optional[int] = None
        agent_text_chars_t: Optional[int] = None
        for ev in turn_events:
            if ev.get("action") == "chat_response":
                params = ev.get("parameters") or {}
                resp = ev.get("response") or params.get("response") or params or {}
                if isinstance(resp, dict):
                    th = resp.get("thinking")
                    if isinstance(th, str) and th:
                        thinking_text = (thinking_text or "") + th
                        thinking_tokens += len(th.split())
                    text = resp.get("text")
                    if isinstance(text, str):
                        agent_text_chars_t = (agent_text_chars_t or 0) + len(text)
                    usage = resp.get("usage", {}) or {}
                    if usage.get("input_tokens") is not None:
                        tokens_in_t = (tokens_in_t or 0) + int(usage.get("input_tokens", 0) or 0)
                    if usage.get("output_tokens") is not None:
                        tokens_out_t = (tokens_out_t or 0) + int(usage.get("output_tokens", 0) or 0)
                    if usage.get("cache_read_input_tokens") is not None:
                        cache_read_t = (cache_read_t or 0) + int(usage.get("cache_read_input_tokens", 0) or 0)
                    if usage.get("cache_creation_input_tokens") is not None:
                        cache_write_t = (cache_write_t or 0) + int(usage.get("cache_creation_input_tokens", 0) or 0)
        cache_hit_pct: Optional[float] = None
        if tokens_in_t is not None and (cache_read_t or 0) + (cache_write_t or 0) + tokens_in_t > 0:
            denom = (cache_read_t or 0) + (cache_write_t or 0) + tokens_in_t
            cache_hit_pct = round((cache_read_t or 0) / denom, 4) if denom > 0 else 0.0
        out.append({
            "turn": i,
            "tool_calls": tool_calls,
            "wallclock_s": round(wallclock, 3),
            # Per-turn token data — populated when audit_log emits
            # `chat_response` events; null otherwise for Block V to flag.
            "tokens_in": tokens_in_t,
            "tokens_out": tokens_out_t,
            "cache_read_tokens": cache_read_t,
            "cache_write_tokens": cache_write_t,
            "cache_hit_pct": cache_hit_pct,
            "agent_text_chars": agent_text_chars_t,
            # PLAYBOOK §4.5 Gap A — extended thinking visibility (PS#4).
            "thinking_text": thinking_text,
            "thinking_tokens": thinking_tokens,
        })
    return out


def _summarize_tool_calls(turns: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Per-tool count + REPEATED detection across the whole session."""
    per_tool: Dict[str, int] = {}
    seen_pairs: Dict[Tuple[str, str], int] = {}
    total = 0
    for turn_events in turns:
        for ev in turn_events:
            if ev.get("action") != "tool_dispatch":
                continue
            name = ev.get("tool_name", "unknown")
            ah = _stable_args_hash(ev.get("parameters", {}))
            pair = (name, ah)
            seen_pairs[pair] = seen_pairs.get(pair, 0) + 1
            per_tool[name] = per_tool.get(name, 0) + 1
            total += 1
    repeated = sum(c for c in seen_pairs.values() if c > 1) - sum(1 for c in seen_pairs.values() if c > 1)
    return {
        "TOTAL_calls": total,
        "REPEATED_calls": repeated,
        "per_tool": per_tool,
        "unique_calls": len(seen_pairs),
    }


TYPED_COMPACTION_ACTIONS = {
    "compact_auto_start",
    "compact_auto_end",
    "compact_auto_skipped",
    "compact_micro_start",
    "compact_micro_end",
    "compact_micro_failed",
    "compact_failed",
}


def _extract_compaction_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter audit_log for typed compact/recovery actions.

    SOFTWARE-COMPACT-TELEMETRY requires typed actions so R-tier evidence does
    not rely on substring guessing. Historical compact-like actions are still
    included with typed=False for backwards-compatible old logs.
    """
    out = []
    for e in events:
        action = str(e.get("action", ""))
        typed = action in TYPED_COMPACTION_ACTIONS
        if typed or "compact" in action.lower():
            out.append({
                "timestamp": e.get("timestamp"),
                "action": action,
                "typed": typed,
                "parameters": e.get("parameters") or {},
                "result_summary": str(e.get("result_summary", ""))[:200],
            })
    return out


def _extract_subagent_dispatches(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter audit_log for subagent-related actions (tool_name=='task' is the dispatch)."""
    out = []
    for e in events:
        if e.get("tool_name") == "task" and e.get("action") == "tool_dispatch":
            params = e.get("parameters", {}) or {}
            out.append({
                "timestamp": e.get("timestamp"),
                "agent_type": params.get("subagent_type") or params.get("agent_type") or "unknown",
                "task_summary": str(params.get("description") or params.get("prompt") or "")[:160],
                "result_summary": str(e.get("result_summary", ""))[:200],
            })
    return out


FAILURE_LOOP_ACTIONS = {
    "tool_failure_recorded",
    "tool_failure_loop_warning",
    "tool_failure_loop_blocked",
}


def _extract_failure_loop_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract repeated-failure loop telemetry from audit events."""
    out = []
    for e in events:
        action = str(e.get("action", ""))
        if action not in FAILURE_LOOP_ACTIONS:
            continue
        params = e.get("parameters") or {}
        out.append({
            "timestamp": e.get("timestamp"),
            "action": action,
            "tool_name": e.get("tool_name"),
            "args_hash": params.get("args_hash"),
            "failure_count": params.get("failure_count"),
            "consecutive_failures": params.get("consecutive_failures"),
            "result_summary": str(e.get("result_summary", ""))[:200],
        })
    return out


def _avg(values: List[float]) -> Optional[float]:
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 4)


def _cache_trend(per_turn: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    """Return cache-hit trend from per-turn chat_response usage when present."""
    hits = [pt.get("cache_hit_pct") for pt in per_turn if pt.get("cache_hit_pct") is not None]
    return {
        "first_5_turns_avg_hit_pct": _avg(hits[:5]),
        "last_5_turns_avg_hit_pct": _avg(hits[-5:]),
        "session_avg_hit_pct": _avg(hits),
    }


def _agent_attribution(side_channel: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return parent/subagent/reviewer token-cost attribution.

    The side channel should use TokenTracker.get_stats() or
    TokenTracker.get_otel_counters() output. Missing fields stay present with
    empty/zero values so R-tier review can distinguish "not used" from
    "telemetry missing".
    """
    if not side_channel:
        return {
            "parent": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "cost_usd": 0.0,
            },
            "subagents": {},
            "reviewers": {},
        }

    parent = {
        "input_tokens": int(side_channel.get("parent_input_tokens", 0) or 0),
        "output_tokens": int(side_channel.get("parent_output_tokens", 0) or 0),
        "cache_read_tokens": int(side_channel.get("parent_cache_read_tokens", 0) or 0),
        "cache_write_tokens": int(side_channel.get("parent_cache_write_tokens", 0) or 0),
        "cost_usd": float(side_channel.get("parent_cost_usd", 0.0) or 0.0),
    }
    sub_in = side_channel.get("subagent_input_tokens", {}) or {}
    sub_out = side_channel.get("subagent_output_tokens", {}) or {}
    sub_cache_read = side_channel.get("subagent_cache_read_tokens", {}) or {}
    sub_cache_write = side_channel.get("subagent_cache_write_tokens", {}) or {}
    sub_cost = side_channel.get("subagent_cost_usd", {}) or {}
    subagents: Dict[str, Dict[str, Any]] = {}
    reviewers: Dict[str, Dict[str, Any]] = {}
    for name in sorted(
        set(sub_in) | set(sub_out) | set(sub_cache_read) | set(sub_cache_write) | set(sub_cost)
    ):
        row = {
            "input_tokens": int(sub_in.get(name, 0) or 0),
            "output_tokens": int(sub_out.get(name, 0) or 0),
            "cache_read_tokens": int(sub_cache_read.get(name, 0) or 0),
            "cache_write_tokens": int(sub_cache_write.get(name, 0) or 0),
            "cost_usd": float(sub_cost.get(name, 0.0) or 0.0),
        }
        subagents[name] = row
        if name == "review" or "review" in str(name).lower():
            reviewers[name] = row
    return {
        "parent": parent,
        "subagents": subagents,
        "reviewers": reviewers,
    }


_RE_COST_LINE = re.compile(r"\[Cost\s+\$([0-9.]+)\s+passed\s+budget\s+\$([0-9.]+)\s+— continuing\.\]")
_RE_MAX_TURNS = re.compile(r"\[Max turns reached:\s*(\d+)\]")
_RE_R_METRICS = re.compile(r"\[R\d+ METRICS\]\s+(\{.*\})")


def _parse_outcome_from_log(raw_log: Optional[Path], side_channel: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Derive completed/stop_reason/cost_cap_hit/max_turns_hit from the raw .log
    plus the optional test-side-channel JSON (e.g. _r1_metrics.json)."""
    out: Dict[str, Any] = {
        "completed": None,
        "stop_reason": None,
        "max_turns_hit": False,
        "cost_cap_hit": False,
        "tokens_in_total": None,
        "tokens_out_total": None,
        "cost_usd": None,
        "wallclock_s_total": None,
        "artifacts_valid": {},
        "agent_text_chars_total": None,
    }
    if side_channel:
        out["tokens_in_total"] = side_channel.get("tokens_in")
        out["tokens_out_total"] = side_channel.get("tokens_out")
        out["cost_usd"] = side_channel.get("cost_usd")
        out["wallclock_s_total"] = side_channel.get("wallclock_s")
        out["stop_reason"] = side_channel.get("stop_reason")
        if side_channel.get("chart_exists") is not None:
            out["artifacts_valid"]["chart"] = bool(side_channel.get("chart_exists"))
        if side_channel.get("report_exists") is not None:
            out["artifacts_valid"]["report"] = bool(side_channel.get("report_exists"))
        out["completed"] = (
            side_channel.get("stop_reason") not in ("max_turns", None)
            if side_channel.get("stop_reason") is not None else None
        )
    if raw_log and raw_log.is_file():
        try:
            text = raw_log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        if "Max turns reached" in text or _RE_MAX_TURNS.search(text):
            out["max_turns_hit"] = True
            out["stop_reason"] = out.get("stop_reason") or "max_turns"
            out["completed"] = False
        cost_lines = _RE_COST_LINE.findall(text)
        if cost_lines:
            # Cost-cap warning fired; cap hit if final cost >= cap.
            try:
                final_cost = float(cost_lines[-1][0])
                final_cap = float(cost_lines[-1][1])
                if final_cost >= final_cap:
                    out["cost_cap_hit"] = True
            except (ValueError, IndexError):
                pass
        # Pull last R-METRICS line if present (test self-emitted JSON).
        m_iter = list(_RE_R_METRICS.finditer(text))
        if m_iter:
            try:
                metrics_inline = json.loads(m_iter[-1].group(1))
                if out["tokens_in_total"] is None:
                    out["tokens_in_total"] = metrics_inline.get("tokens_in")
                if out["tokens_out_total"] is None:
                    out["tokens_out_total"] = metrics_inline.get("tokens_out")
                if out["cost_usd"] is None:
                    out["cost_usd"] = metrics_inline.get("cost_usd")
                if out["wallclock_s_total"] is None:
                    out["wallclock_s_total"] = metrics_inline.get("wallclock_s")
                if out["stop_reason"] is None:
                    out["stop_reason"] = metrics_inline.get("stop_reason")
                if metrics_inline.get("chart_exists") is not None:
                    out["artifacts_valid"]["chart"] = bool(metrics_inline.get("chart_exists"))
                if metrics_inline.get("report_exists") is not None:
                    out["artifacts_valid"]["report"] = bool(metrics_inline.get("report_exists"))
            except json.JSONDecodeError:
                pass
        # PASSED / FAILED markers from pytest output.
        if " passed" in text and " failed" not in text:
            if out["completed"] is None:
                out["completed"] = True
        elif " failed" in text and out["completed"] is None:
            out["completed"] = False
    return out


def _validate_telemetry(t: Dict[str, Any]) -> List[str]:
    """Return list of validation errors. Empty list = valid."""
    errors: List[str] = []
    missing = REQUIRED_TOP_LEVEL_KEYS - set(t.keys())
    if missing:
        errors.append(f"missing required top-level keys: {sorted(missing)}")
    if not isinstance(t.get("per_turn"), list):
        errors.append("per_turn must be a list")
    if isinstance(t.get("outcome"), dict):
        completed = t["outcome"].get("completed")
        if completed not in (True, False, None):
            errors.append(f"outcome.completed must be bool or None; got {completed!r}")
    else:
        errors.append("outcome must be an object")
    return errors


def build_telemetry(
    test: str,
    call: int,
    audit_log_path: Path,
    raw_log_path: Optional[Path],
    side_channel_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Pure aggregation function — used by both the CLI and the lock tests."""
    side_channel: Optional[Dict[str, Any]] = None
    if side_channel_path and side_channel_path.is_file():
        try:
            side_channel = json.loads(side_channel_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            side_channel = None

    audit_jsonl = _resolve_audit_log(audit_log_path)
    events = _parse_jsonl(audit_jsonl) if audit_jsonl else []
    turns = _group_into_turns(events)
    per_turn = _aggregate_per_turn(turns)
    tool_summary = _summarize_tool_calls(turns)
    compaction = _extract_compaction_events(events)
    subagent = _extract_subagent_dispatches(events)
    failure_loop = _extract_failure_loop_events(events)
    cache_trend = _cache_trend(per_turn)
    agent_attr = _agent_attribution(side_channel)
    outcome = _parse_outcome_from_log(raw_log_path, side_channel)

    return {
        "schema_version": 1,
        "test": test,
        "call": call,
        "audit_log_path": str(audit_jsonl) if audit_jsonl else None,
        "raw_log_path": str(raw_log_path) if raw_log_path else None,
        "side_channel_path": str(side_channel_path) if side_channel_path else None,
        "per_turn": per_turn,
        "tool_call_summary": tool_summary,
        "compaction_events": compaction,
        "subagent_dispatches": subagent,
        "cache_efficiency_trend": cache_trend,
        "agent_attribution": agent_attr,
        "failure_loop_events": failure_loop,
        "outcome": outcome,
        "events_seen": len(events),
        "turns_seen": len(turns),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--test", required=True, help="R-tier test ID (R1, R12, V1, ...)")
    p.add_argument("--call", required=True, type=int, help="AWS call number")
    p.add_argument("--audit-log", required=True, type=Path,
                   help="Path to a single audit_log JSONL or a directory containing them.")
    p.add_argument("--raw-log", required=True, type=Path,
                   help="Path to r-tier-<TEST>-aws-call<N>.log file.")
    p.add_argument("--output", required=True, type=Path,
                   help="Where to write the telemetry JSON.")
    p.add_argument("--metrics-side-channel", type=Path, default=None,
                   help="Optional path to test-emitted JSON (e.g. _r1_metrics.json).")
    args = p.parse_args()

    telemetry = build_telemetry(
        test=args.test,
        call=args.call,
        audit_log_path=args.audit_log,
        raw_log_path=args.raw_log if args.raw_log.is_file() else None,
        side_channel_path=args.metrics_side_channel,
    )

    # Validate before writing.
    errors = _validate_telemetry(telemetry)
    if errors:
        print(f"build_telemetry validation FAILED:\n  - " + "\n  - ".join(errors), file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(telemetry, indent=2, default=str), encoding="utf-8")

    # Re-parse to confirm.
    try:
        json.loads(args.output.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"build_telemetry post-write JSON-parse FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"OK build_telemetry wrote {args.output} "
          f"({len(telemetry['per_turn'])} turns, "
          f"{telemetry['tool_call_summary']['TOTAL_calls']} tool calls, "
          f"{len(telemetry['compaction_events'])} compaction events, "
          f"{len(telemetry['subagent_dispatches'])} subagent dispatches, "
          f"{len(telemetry['failure_loop_events'])} failure-loop events)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
