"""
V4.6.0 Complex Task Integration Test
Tests: caching, orchestration, skill discovery, tool usage, verification nudge.

Simulates a realistic multi-step coding task and validates all systems work together.
"""

import sys
import os
import time
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-2")

from sagemaker_agent import (
    Agent, BedrockClient, CONFIG, SKILLS, SYSTEM_PROMPT, TOKENS,
)
from pathlib import Path


class TestTracker:
    """Captures all agent output for analysis."""
    def __init__(self):
        self.lines = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.tool_calls = []
        self.sub_agents = []
        self.skill_surfaced = []
        self.nudge_seen = False
        self.verdict_seen = False

    def output_fn(self, text):
        text = str(text)
        self.lines.append(text)
        if "Cache: HIT" in text:
            self.cache_hits += 1
        if "Cache: MISS" in text or "Cache: miss" in text:
            self.cache_misses += 1
        if "[Calling " in text:
            tool = text.split("[Calling ")[1].split("...")[0].split("]")[0]
            self.tool_calls.append(tool)
        if "sub-agent" in text.lower() or "Running " in text and "parallel" in text.lower():
            self.sub_agents.append(text)
        if "Skills Relevant" in text or "Consider using" in text:
            self.skill_surfaced.append(text)
        if "verification step" in text.lower() or "Verification Contract" in text:
            self.nudge_seen = True
        if "VERDICT:" in text:
            self.verdict_seen = True

    @property
    def full_output(self):
        return "\n".join(self.lines)


def run_complex_test(model_id):
    """Run a multi-turn complex coding task."""
    CONFIG.workspace = os.path.dirname(os.path.abspath(__file__))
    CONFIG.model_id = model_id
    SKILLS.skills_dir = Path(os.path.join(CONFIG.workspace, "skills"))
    SKILLS.discover()

    client = BedrockClient(model_id, CONFIG.region, False)
    tracker = TestTracker()

    agent = Agent(
        client=client,
        on_approval=lambda *a, **k: True,
        on_ask_user=lambda q, opts: "yes, proceed",
    )

    print("=" * 60)
    print("  V4.6.0 COMPLEX INTEGRATION TEST")
    print(f"  Model: {model_id}")
    print("=" * 60)

    # ── Turn 1: Multi-file task (should trigger skill discovery + planning) ──
    print("\n--- TURN 1: Complex coding task ---")
    t0 = time.time()
    response1 = agent.run(
        "I need to review this code for quality issues. Read sagemaker_agent.py "
        "and check the AGENT_TYPES dictionary and the tool_todo_write function. "
        "Tell me if the auto-nudge logic is correct and if the fork agent type is well-formed.",
        output_fn=tracker.output_fn,
        max_turns_override=10,
    )
    t1 = time.time()
    print(f"  Turn 1 time: {t1-t0:.1f}s")
    print(f"  Cache hits: {tracker.cache_hits}")
    print(f"  Tools used: {tracker.tool_calls}")

    # ── Turn 2: Follow-up (tests caching — should HIT on turn 2+) ──
    print("\n--- TURN 2: Follow-up question (tests caching) ---")
    tracker2 = TestTracker()
    t2 = time.time()
    response2 = agent.run(
        "Now check the verify agent type prompt_suffix. Does it have anti-rationalization rules? "
        "Does it enforce evidence format? List all the type-specific verification strategies it includes.",
        output_fn=tracker2.output_fn,
        max_turns_override=8,
    )
    t3 = time.time()
    print(f"  Turn 2 time: {t3-t2:.1f}s")
    print(f"  Cache hits: {tracker2.cache_hits}")
    print(f"  Tools used: {tracker2.tool_calls}")

    # ── Turn 3: Trigger skill discovery ──
    print("\n--- TURN 3: Skill discovery test ---")
    tracker3 = TestTracker()

    # Test skill discovery directly
    relevant = SKILLS.discover_relevant(
        "I want to do a security review of the bash execution tool for vulnerabilities"
    )
    print(f"  Skill discovery result: {relevant}")

    # Also test via agent
    t4 = time.time()
    response3 = agent.run(
        "Now verify the changes look correct before I commit. Use the verify approach.",
        output_fn=tracker3.output_fn,
        max_turns_override=8,
    )
    t5 = time.time()
    print(f"  Turn 3 time: {t5-t4:.1f}s")
    print(f"  Cache hits: {tracker3.cache_hits}")
    print(f"  Tools used: {tracker3.tool_calls}")

    # ── Results ──
    print("\n" + "=" * 60)
    print("  INTEGRATION TEST RESULTS")
    print("=" * 60)

    total_cache_hits = tracker.cache_hits + tracker2.cache_hits + tracker3.cache_hits
    total_tools = tracker.tool_calls + tracker2.tool_calls + tracker3.tool_calls

    checks = {
        "Caching active (2+ HITs across turns)": total_cache_hits >= 2,
        "Tools used (read_file, grep, or glob)": any(
            t in total_tools for t in ["read_file", "grep", "glob"]
        ),
        "Multi-turn context preserved": len(agent.messages) >= 4,
        "Skill discovery works": len(relevant) > 0,
        "Model produced analysis": len(response1 or "") > 50,
        "Follow-up used cached context": tracker2.cache_hits >= 1,
    }

    all_pass = True
    for name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {name}")

    print(f"\n  Total cache HITs: {total_cache_hits}")
    print(f"  Total tool calls: {len(total_tools)} ({', '.join(set(total_tools))})")
    print(f"  Messages in context: {len(agent.messages)}")
    print(f"  Skills discovered for security query: {relevant}")
    print(f"  Total time: {t5-t0:.1f}s")

    # Cost
    stats = TOKENS.get_stats()
    print(f"\n  Cost: ${stats.get('total_cost', 0):.4f}")
    print(f"  Tokens in: {stats.get('total_input', 0):,}")
    print(f"  Tokens out: {stats.get('total_output', 0):,}")
    print(f"  Cache savings: ${stats.get('total_saved', 0):.4f}")

    print(f"\n  {'ALL CHECKS PASS' if all_pass else 'SOME CHECKS FAILED'}")
    return all_pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="au.anthropic.claude-haiku-4-5-20251001-v1:0")
    args = parser.parse_args()
    ok = run_complex_test(args.model)
    sys.exit(0 if ok else 1)
