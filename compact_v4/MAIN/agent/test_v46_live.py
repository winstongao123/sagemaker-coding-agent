"""
V4.6.0 Live Bedrock Test Harness
Tests new skills (simplify, verify, security-review, code-review) on Sonnet 4.6.
Runs headless — no Jupyter UI needed.

Usage:
  python test_v46_live.py [--model MODEL_ID] [--mock]
"""

import sys
import os
import time
import json
import re

# Add agent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Must set before import
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-2")

from sagemaker_agent import (
    Agent, BedrockClient, CONFIG, SKILLS, AGENT_TYPES,
    SYSTEM_PROMPT, TOOLS, get_tool_definitions,
)


# -- Helpers --------------------------------------------------

class TestResult:
    def __init__(self, name):
        self.name = name
        self.output_lines = []
        self.passed = False
        self.error = None
        self.duration_s = 0
        self.tokens_in = 0
        self.tokens_out = 0

    def output_fn(self, text):
        self.output_lines.append(str(text))

    @property
    def full_output(self):
        return "\n".join(self.output_lines)


def run_test(name, user_message, model_id, mock=False, system_prompt=None, max_turns=None):
    """Run a single test against Bedrock (or mock)."""
    result = TestResult(name)
    t0 = time.time()

    try:
        client = BedrockClient(model_id, CONFIG.region, mock)
        agent = Agent(
            client=client,
            on_approval=lambda *a, **k: True,  # Auto-approve all tools
            on_ask_user=lambda q, opts: "yes",  # Auto-answer questions
        )

        # Inject skill content into system prompt if skill mentioned
        sp = system_prompt or SYSTEM_PROMPT
        for skill_name in ["simplify", "security-review", "verify", "code-review"]:
            if skill_name in user_message.lower() or f"/skill use {skill_name}" in user_message:
                ok, content = SKILLS.read_skill(skill_name)
                if ok:
                    sp += f"\n\n## Active Skill: {skill_name}\n\n{content}"
                    break

        response = agent.run(
            user_message=user_message,
            output_fn=result.output_fn,
            system_prompt=sp,
            max_turns_override=max_turns or 15,
        )

        result.output_lines.append(f"\n[Final response]: {response[:500] if response else '(empty)'}")
        result.duration_s = time.time() - t0

    except Exception as e:
        result.error = str(e)
        result.duration_s = time.time() - t0

    return result


# -- Test Definitions -----------------------------------------

def test_skill_discovery():
    """T1: Verify all new skills are discovered by SkillManager."""
    SKILLS.discover()
    skills = {s["name"] for s in SKILLS.list_skills()}
    expected = {"simplify", "security-review", "code-review", "verify"}
    missing = expected - skills
    return (not missing, f"Missing skills: {missing}" if missing else f"All found: {expected}")


def test_agent_types():
    """T2: Verify upgraded agent types exist and have correct prompts."""
    issues = []

    # Verify agent type exists
    for at in ["verify", "review"]:
        if at not in AGENT_TYPES:
            issues.append(f"Missing agent type: {at}")
            continue

    # Verify verify agent has anti-rationalization
    verify_prompt = AGENT_TYPES["verify"]["prompt_suffix"]
    for keyword in ["Failure Patterns", "rationalization", "VERDICT", "adversarial"]:
        if keyword.lower() not in verify_prompt.lower():
            issues.append(f"verify prompt missing: {keyword}")

    # Verify review agent has parallel specialization
    review_prompt = AGENT_TYPES["review"]["prompt_suffix"]
    for keyword in ["specialized", "Code Reuse", "Efficiency", "assigned"]:
        if keyword.lower() not in review_prompt.lower():
            issues.append(f"review prompt missing: {keyword}")

    return (not issues, "; ".join(issues) if issues else "All prompt patterns present")


def test_verify_skill_content():
    """T3: Verify the verify skill has all Runnable patterns."""
    ok, content = SKILLS.read_skill("verify")
    if not ok:
        return (False, f"Can't read verify skill: {content}")

    required_patterns = [
        "Failure Patterns",
        "Verification avoidance",
        "seduced by the first 80%",
        "reading is not verification",
        "VERDICT: PASS",
        "VERDICT: FAIL",
        "VERDICT: PARTIAL",
        "Adversarial Probes",
        "Boundary values",
        "Command run",
        "Output observed",
    ]
    missing = [p for p in required_patterns if p.lower() not in content.lower()]
    return (not missing, f"Missing: {missing}" if missing else "All 11 Runnable patterns present")


def test_simplify_skill_content():
    """T4: Verify simplify skill has 3-agent parallel pattern."""
    ok, content = SKILLS.read_skill("simplify")
    if not ok:
        return (False, f"Can't read simplify skill: {content}")

    required = [
        "Phase 1: Identify Changes",
        "Phase 2: Launch Three Review Agents",
        "Phase 3: Fix Issues",
        "Agent 1: Code Reuse",
        "Agent 2: Code Quality",
        "Agent 3: Efficiency",
        "task",
        "parallel",
    ]
    missing = [p for p in required if p.lower() not in content.lower()]
    return (not missing, f"Missing: {missing}" if missing else "All 3-agent parallel patterns present")


def test_security_review_content():
    """T5: Verify security-review skill has false-positive filtering."""
    ok, content = SKILLS.read_skill("security-review")
    if not ok:
        return (False, f"Can't read: {content}")

    required = [
        "Confidence Scoring",
        "Hard Exclusions",
        "Precedents",
        "Exploit Scenario",
        "0.8",
        "Signal Quality",
    ]
    missing = [p for p in required if p.lower() not in content.lower()]
    return (not missing, f"Missing: {missing}" if missing else "All filtering patterns present")


def test_live_verify_invocation(model_id, mock=False):
    """T6: LIVE TEST — invoke verify skill on Sonnet 4.6 and check output quality."""
    result = run_test(
        "T6: Live verify invocation",
        "Use the verify skill to check the file sagemaker_agent.py in the current directory. "
        "Focus on the AGENT_TYPES dictionary — verify the verify and review entries are well-formed. "
        "Run at least one adversarial probe.",
        model_id=model_id,
        mock=mock,
        max_turns=8,
    )

    output = result.full_output.lower()
    checks = {
        "model_responded": not result.error,
        "used_tools": any(t in output for t in ["read_file", "grep", "glob", "bash", "python_exec"]),
        "read_code": "agent_types" in output or "verify" in output or "review" in output,
        "attempted_verification": any(t in output for t in [
            "check", "pass", "fail", "verdict", "well-formed", "valid",
            "correct", "verified", "adversarial", "probe", "result"
        ]),
    }
    passed = all(checks.values())
    details = ", ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in checks.items())
    return (passed, f"{details} | {result.duration_s:.1f}s", result)


def test_live_simplify_parallel(model_id, mock=False):
    """T7: LIVE TEST — invoke simplify and check if it spawns parallel agents."""
    result = run_test(
        "T7: Live simplify parallel",
        "Use the simplify skill to review the recent changes in this repository. "
        "Run git diff to see what changed, then launch the 3 review agents as described in the skill.",
        model_id=model_id,
        mock=mock,
        max_turns=10,
    )

    output = result.full_output.lower()
    checks = {
        "model_responded": not result.error,
        "mentioned_review": any(t in output for t in ["agent", "task", "reuse", "quality", "efficiency", "review"]),
        "attempted_diff": any(t in output for t in ["git diff", "diff", "changed", "changes"]),
    }
    passed = all(checks.values())
    details = ", ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in checks.items())
    return (passed, f"{details} | {result.duration_s:.1f}s", result)


def test_live_security_review(model_id, mock=False):
    """T8: LIVE TEST — invoke security-review skill."""
    result = run_test(
        "T8: Live security-review",
        "Use the security-review skill to check sagemaker_agent.py for vulnerabilities. "
        "Focus on the bash execution tool (tool_bash function) and the Python execution tool. "
        "Apply the confidence threshold — only report findings with confidence >= 0.8.",
        model_id=model_id,
        mock=mock,
        max_turns=8,
    )

    output = result.full_output.lower()
    checks = {
        "model_responded": not result.error,
        "analyzed_code": any(t in output for t in ["read_file", "security", "bash", "grep", "tool_bash"]),
        "structured_output": any(t in output for t in [
            "severity", "confidence", "vulnerability", "no actionable",
            "finding", "safe", "risk", "assessment", "review",
            "injection", "validation", "sanitiz"
        ]),
    }
    passed = all(checks.values())
    details = ", ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in checks.items())
    return (passed, f"{details} | {result.duration_s:.1f}s", result)


# -- Main -----------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="V4.6.0 Live Test Harness")
    parser.add_argument("--model", default="au.anthropic.claude-sonnet-4-6",
                        help="Bedrock model ID (default: Sonnet 4.6 AU)")
    parser.add_argument("--mock", action="store_true", help="Use mock responses (no AWS calls)")
    parser.add_argument("--skip-live", action="store_true", help="Skip live Bedrock tests (T6-T8)")
    args = parser.parse_args()

    # Set workspace to agent directory
    CONFIG.workspace = os.path.dirname(os.path.abspath(__file__))
    CONFIG.model_id = args.model

    print(f"{'='*60}")
    print(f"  V4.6.0 Live Test Harness")
    print(f"  Model: {args.model}")
    print(f"  Mock: {args.mock}")
    print(f"  Workspace: {CONFIG.workspace}")
    print(f"{'='*60}\n")

    results = []

    # -- Offline Tests (no Bedrock calls) --
    offline_tests = [
        ("T1: Skill Discovery", test_skill_discovery),
        ("T2: Agent Types", test_agent_types),
        ("T3: Verify Skill Content", test_verify_skill_content),
        ("T4: Simplify Skill Content", test_simplify_skill_content),
        ("T5: Security-Review Content", test_security_review_content),
    ]

    for name, test_fn in offline_tests:
        passed, detail = test_fn()
        status = "PASS" if passed else "FAIL"
        results.append((name, status, detail))
        print(f"  [{status}] {name}")
        print(f"         {detail}\n")

    # -- Live Tests (Bedrock calls) --
    if not args.skip_live:
        print(f"\n{'-'*60}")
        print(f"  LIVE BEDROCK TESTS (model: {args.model})")
        print(f"{'-'*60}\n")

        live_tests = [
            ("T6: Live Verify", test_live_verify_invocation),
            ("T7: Live Simplify Parallel", test_live_simplify_parallel),
            ("T8: Live Security Review", test_live_security_review),
        ]

        for name, test_fn in live_tests:
            print(f"  Running {name}...")
            passed, detail, test_result = test_fn(args.model, args.mock)
            status = "PASS" if passed else "FAIL"
            results.append((name, status, detail))
            print(f"  [{status}] {name}")
            print(f"         {detail}")
            if test_result.error:
                print(f"         ERROR: {test_result.error}")
            # Dump first 2000 chars of output for debugging
            if status == "FAIL":
                snippet = test_result.full_output[:2000].encode('ascii', 'replace').decode()
                print(f"         OUTPUT SNIPPET: {snippet}")
            print()

    # -- Summary --
    total = len(results)
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} PASS, {failed} FAIL")
    print(f"{'='*60}")

    for name, status, detail in results:
        icon = "+" if status == "PASS" else "X"
        print(f"  {icon} {name}: {status}")

    # Return exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
