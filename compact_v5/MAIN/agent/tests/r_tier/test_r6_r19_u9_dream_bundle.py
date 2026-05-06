"""R-tier R6 + R19-U9 - bundled /dream memory consolidation.

Runs one real Bedrock-backed `/dream` consolidation over a 100-entry memory
fixture and records per-test side metrics for both R6 and R19-U9. The test is
skipped unless RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import pytest


_AGENT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_PER_TEST_CAPS = {"R6": 0.30, "R19-U9": 0.30}
_BUNDLE_PLANNED_CAP_USD = sum(_PER_TEST_CAPS.values())
_USER_APPROVED_RETRY_BUFFER_MULTIPLIER = 1.20
_BUNDLE_HARD_CEILING_USD = _BUNDLE_PLANNED_CAP_USD * _USER_APPROVED_RETRY_BUFFER_MULTIPLIER

_REQUIRED_FACTS = {
    "deployment_region": "ap-southeast-2",
    "db_secret": "prod/db/password",
    "owner": "Priya",
    "incident": "INC-4242",
    "runtime": "Python 3.12",
    "codename": "HYDRA-LIME",
}
_STALE_FACT = "Python 3.10"


def _memory_fixture() -> str:
    lines = [
        "# Memory",
        "",
        "## Required Facts",
        "- Project codename HYDRA-LIME must be preserved.",
        "- Deployment region is ap-southeast-2 and must be preserved.",
        "- Database secret path is prod/db/password and must be preserved.",
        "- Current owner is Priya and must be preserved.",
        "- Incident marker INC-4242 must be preserved.",
        "- Latest runtime preference is Python 3.12 and must be preserved.",
        "",
        "## Duplicate And Stale Entries",
    ]
    for idx in range(1, 31):
        lines.append(f"- Duplicate region note {idx}: deployment region remains ap-southeast-2.")
    for idx in range(1, 21):
        lines.append(f"- Duplicate owner note {idx}: Priya owns the release checklist.")
    for idx in range(1, 16):
        lines.append(f"- Stale runtime note {idx}: Python 3.10 was an older preference.")
    for idx in range(1, 15):
        lines.append(f"- Duplicate codename note {idx}: HYDRA-LIME appears in old status.")
    for idx in range(1, 16):
        lines.append(f"- Session scratch {idx}: temporary note safe to prune after consolidation.")
    assert len([line for line in lines if line.startswith("- ")]) == 100
    return "\n".join(lines) + "\n"


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


def _fact_hits(text: str) -> dict[str, bool]:
    lower = text.lower()
    return {key: value.lower() in lower for key, value in _REQUIRED_FACTS.items()}


def _write_side_metrics(
    *,
    test_id: str,
    call: int,
    metrics: dict[str, Any],
) -> None:
    path = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-{test_id}-aws-call{call}-side-metrics.json"
    row = dict(metrics)
    row["test"] = test_id
    row["cost_cap_usd"] = _PER_TEST_CAPS[test_id]
    row["cost_usd"] = round(float(metrics["allocated_cost_usd"]), 4)
    path.write_text(json.dumps(row, indent=2), encoding="utf-8")
    print(f"[{test_id}_SIDE_METRICS] {path}")
    print(f"[{test_id}_METRICS] {json.dumps(row, sort_keys=True)}")


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R6+R19-U9 is real-AWS gated.",
)
def test_r6_r19_u9_dream_bundle(tmp_path):
    """R6/R19-U9 pass when /dream preserves facts and deduplicates stale noise."""
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.dream import get_dream_prompt, run_dream
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"R6+R19-U9-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    memory_path = tmp_path / "memory.md"
    memory_path.write_text(_memory_fixture(), encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "R6/R19-U9 fixture: run /dream once, preserve required facts, prune stale duplicates.\n",
        encoding="utf-8",
    )

    saved_ws = CONFIG.workspace
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    saved_enable_prompt_cache = getattr(CONFIG, "enable_prompt_cache", None)
    saved_sec = sec_mgr.SECURITY
    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _BUNDLE_HARD_CEILING_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 2048
        CONFIG.disable_local_traces = False
        CONFIG.enable_prompt_cache = True
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _llm_consolidator(existing: str, manifest: str) -> str:
            prompt = get_dream_prompt(existing, manifest)
            t0 = time.time()
            AUDIT.log(
                "R6-R19-U9",
                "dream_consolidation_start",
                tool_name="/dream",
                parameters={
                    "memory_entries": 100,
                    "required_facts": sorted(_REQUIRED_FACTS),
                    "bundle": ["R6", "R19-U9"],
                },
                result_summary="starting real Haiku memory consolidation",
                user_approved=True,
            )
            resp = client.chat(
                messages=[{"role": "user", "content": prompt}],
                system=(
                    "You are a precise memory consolidator. Return a concise final "
                    "memory.md body. Preserve all required facts, collapse duplicate "
                    "facts, and remove stale runtime preferences superseded by newer entries."
                ),
                tools=[],
                max_tokens=2048,
                temperature=0.0,
                thinking_enabled=False,
            )
            TOKENS.add(resp.usage or {}, model_id=_HAIKU_45_AU, agent_kind="parent")
            AUDIT.log(
                "R6-R19-U9",
                "chat_response",
                tool_name="bedrock",
                parameters={
                    "response": {
                        "text": resp.text,
                        "usage": resp.usage,
                        "stop_reason": resp.stop_reason,
                    },
                    "wallclock_s": round(time.time() - t0, 2),
                },
                result_summary=f"Bedrock returned {len(resp.text)} chars for /dream",
                user_approved=True,
            )
            return resp.text

        t0 = time.time()
        result = run_dream(str(tmp_path), consolidator=_llm_consolidator)
        wallclock_s = time.time() - t0
        consolidated = memory_path.read_text(encoding="utf-8", errors="replace")
        backup_text = (tmp_path / "memory.md.bak").read_text(encoding="utf-8", errors="replace")
        events = _audit_events(audit_dir)

        hits = _fact_hits(consolidated)
        required_facts_preserved = all(hits.values())
        latest_runtime_wins = "python 3.12" in consolidated.lower()
        stale_runtime_mentions = consolidated.lower().count(_STALE_FACT.lower())
        original_stale_mentions = backup_text.lower().count(_STALE_FACT.lower())
        duplicate_region_mentions = consolidated.lower().count("ap-southeast-2")
        original_region_mentions = backup_text.lower().count("ap-southeast-2")
        duplicate_owner_mentions = consolidated.lower().count("priya")
        original_owner_mentions = backup_text.lower().count("priya")
        deduplicated = (
            duplicate_region_mentions < original_region_mentions
            and duplicate_owner_mentions < original_owner_mentions
            and stale_runtime_mentions < original_stale_mentions
        )
        phases_ok = result.phases_executed == ["Orient", "Gather", "Consolidate", "Prune+Index"]
        lock_released = not (tmp_path / "dream.lock").exists()
        backup_ok = "HYDRA-LIME" in backup_text and "INC-4242" in backup_text
        cost_used = float(TOKENS.session_cost)
        bundle_completed = bool(
            result.success
            and required_facts_preserved
            and latest_runtime_wins
            and deduplicated
            and phases_ok
            and lock_released
            and backup_ok
            and cost_used <= _BUNDLE_HARD_CEILING_USD
        )
        process_quality_ok = bool(
            len([ev for ev in events if ev.get("action") == "chat_response"]) == 1
            and not [ev for ev in events if str(ev.get("action", "")).startswith("tool_failure")]
        )
        allocated_cost = cost_used / 2.0
        base_metrics = {
            "test": "R6+R19-U9",
            "call": call,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(TOKENS.session_input),
            "tokens_out": int(TOKENS.session_output),
            "cache_hit_pct": (
                round(TOKENS.session_cache_read / max(1, TOKENS.session_input), 4)
                if TOKENS.session_input else 0.0
            ),
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": 0,
            "api_calls": int(TOKENS.api_calls),
            "subagent_calls": 0,
            "reviewer_calls": 0,
            "subagent_tokens_in": 0,
            "subagent_tokens_out": 0,
            "subagent_cost_usd": 0.0,
            "reviewer_tokens_in": 0,
            "reviewer_tokens_out": 0,
            "reviewer_cost_usd": 0.0,
            "parent_input_tokens": int(TOKENS.parent_input_tokens),
            "parent_output_tokens": int(TOKENS.parent_output_tokens),
            "parent_cache_read_tokens": int(TOKENS.parent_cache_read_tokens),
            "parent_cache_write_tokens": int(TOKENS.parent_cache_write_tokens),
            "parent_cost_usd": round(float(TOKENS.parent_cost), 4),
            "required_fact_hits": hits,
            "required_facts_preserved": required_facts_preserved,
            "deduplicated": deduplicated,
            "latest_runtime_wins": latest_runtime_wins,
            "stale_runtime_mentions_before": original_stale_mentions,
            "stale_runtime_mentions_after": stale_runtime_mentions,
            "region_mentions_before": original_region_mentions,
            "region_mentions_after": duplicate_region_mentions,
            "owner_mentions_before": original_owner_mentions,
            "owner_mentions_after": duplicate_owner_mentions,
            "phases_executed": result.phases_executed,
            "lock_released": lock_released,
            "backup_ok": backup_ok,
            "bundle_total_cost_usd": round(cost_used, 4),
            "allocated_cost_usd": round(allocated_cost, 4),
            "process_quality_ok": process_quality_ok,
            "completed": bool(bundle_completed and process_quality_ok),
            "cost_usd": round(cost_used, 4),
            "verdict": "GENUINE_PASS" if bundle_completed and process_quality_ok else "FAIL",
            "stop_reason": "dream_success" if result.success else "dream_failed",
            "audit_dir": str(audit_dir),
            "consolidated_preview": consolidated[:1200],
            "backup_path": result.backup_path,
        }
        _write_side_metrics(test_id="R6", call=call, metrics=base_metrics)
        _write_side_metrics(test_id="R19-U9", call=call, metrics=base_metrics)
        print(f"\n[R6_R19_U9_AUDIT_DIR] {audit_dir}")
        print(f"[R6_R19_U9_METRICS] {json.dumps(base_metrics, sort_keys=True)}")

        assert bundle_completed, f"R6/R19-U9 /dream artifact failed: {base_metrics}"
        assert process_quality_ok, f"R6/R19-U9 process quality failed: {base_metrics}"
    finally:
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec
        if saved_cost_limit is not None:
            CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
        if saved_enable_prompt_cache is not None:
            CONFIG.enable_prompt_cache = saved_enable_prompt_cache
