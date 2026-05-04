warning: `--full-auto` is deprecated; use `--sandbox workspace-write` instead.
Reading additional input from stdin...
OpenAI Codex v0.128.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.5
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019df054-fbe5-7743-9137-4a4cd7238799
--------
user
You are reviewing the PRE-FLIGHT design of an R-tier real-AWS test before
any Bedrock call is made. Each AWS call costs real money (cap $0.50).
Your job is to catch broken test design, missing assertions, or wasted-spend
risk BEFORE we hit Bedrock.

CONTEXT
- Test: R3 — three sub-agent dispatches + parent synthesis on real Bedrock
- Block(s) being validated: Block G3 (coordinator-mode prompt) + Phase 9 (task tool / sub-agent spawn)
- What it claims to prove: v5 parent agent, with coordinator_mode_enabled=True, can dispatch 3 sub-agents (subagent_type='explore') one per file, then synthesize their reports into a single findings.md via write_file. Note: v5's task tool is `is_concurrency_safe=False` so the 3 dispatches are SEQUENTIAL on the parent's call stack — this matches the v5 implementation. The test's "three parallel" wording in the playbook is honored as "3 ordered sub-agent dispatches with parent synthesis" since true async-parallel is a future-phase capability.
- Cost cap (session_cost_limit): $0.50
- Model: claude-haiku-4-5 (au.anthropic.claude-haiku-4-5-20251001-v1:0, AU geo +10% premium = $1.10/$5.50 per MTok in/out)
- Test file: compact_v5/MAIN/agent/tests/r_tier/test_r3_three_subagents.py
- Scenario fixtures: 3 inline Python files (utils_a.py / utils_b.py / utils_c.py) created in tmp_path during the test setup

=== INLINED TEST CODE (full file, 290 lines) ===
"""R-tier R3 — three sub-agent dispatches + parent synthesis.

Per PS_V5_TEST_PLAYBOOK / PS_V5_TEST_SET §Tier 1 R3:
  Validates Block G3 (coordinator-mode prompt) + Phase 9 task tool
  (sub-agent spawn) end-to-end on real Bedrock:
    - Parent receives a coding-survey task across 3 small Python files.
    - Parent dispatches 3 sub-agents (subagent_type='explore'),
      one per file.
    - Each sub-agent reads its assigned file and reports the function
      name + 1-line summary + the TODO comment text.
    - Parent synthesizes the 3 results into a single findings.md.

Note on "parallel": v5's task tool is `is_concurrency_safe=False` —
  spawn is synchronous. The 3 dispatches are SEQUENTIAL on the
  parent's call stack. The TEST_PLAYBOOK label "Three parallel
  sub-agents" reflects the v4/Runnable phrasing; on v5 we test the
  real implementation: 3 ordered sub-agent dispatches with parent
  synthesis. True async parallel sub-agents land in a future phase.

Validation pillars:
  - subagent_dispatches audit entries == 3 (build_telemetry.py read).
  - All 3 dispatches are agent_type='explore'.
  - findings.md exists and mentions all 3 function names + TODOs.
  - Parent stop_reason != max_turns.
  - Cost <= $0.50.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R3_COST_CAP_USD = 0.50

_UTILS_A = '''"""Module A — string utilities."""


def kebab_case(text: str) -> str:
    """Convert spaces and underscores to hyphens; lowercase the result.

    Examples:
      'Hello World' -> 'hello-world'
      'snake_case_text' -> 'snake-case-text'
    """
    # TODO(R3-marker-A): handle Unicode whitespace beyond ASCII space.
    return text.replace("_", " ").lower().replace(" ", "-")
'''

_UTILS_B = '''"""Module B — numeric utilities."""


def clamp(value: float, lo: float, hi: float) -> float:
    """Constrain *value* to the inclusive range [lo, hi].

    If lo > hi the function returns *value* unchanged.
    """
    # TODO(R3-marker-B): raise ValueError when lo > hi instead of silent fall-through.
    if lo > hi:
        return value
    return max(lo, min(hi, value))
'''

_UTILS_C = '''"""Module C — list utilities."""


def chunked(items, size):
    """Yield successive *size*-length chunks from *items*.

    The final chunk may be shorter than *size* if the input length
    is not a multiple of *size*.
    """
    # TODO(R3-marker-C): support negative or zero size with a clear error.
    for i in range(0, len(items), size):
        yield items[i:i + size]
'''

_FUNCTION_NAMES = ("kebab_case", "clamp", "chunked")
_MARKERS = ("R3-marker-A", "R3-marker-B", "R3-marker-C")

_R3_PROMPT = (
    "There are three Python files in the current directory: utils_a.py, "
    "utils_b.py, utils_c.py. Each defines exactly ONE public function "
    "and contains exactly ONE `# TODO(...)` comment.\n\n"
    "TASK:\n"
    "1. Spawn THREE sub-agents using the `task` tool, ONE PER FILE. Use "
    "subagent_type='explore' for each (read-only is sufficient).\n"
    "   - Sub-agent 1 prompt: 'Read utils_a.py. Report the function name, "
    "what the function does in one sentence, and the exact TODO comment "
    "text from that file. Reply in this format:\\nFUNCTION: <name>\\n"
    "SUMMARY: <one-sentence>\\nTODO: <todo text>'\n"
    "   - Sub-agent 2 prompt: same but for utils_b.py.\n"
    "   - Sub-agent 3 prompt: same but for utils_c.py.\n"
    "2. After ALL three sub-agents return, write a single Markdown report "
    "named `findings.md` in the current directory using the `write_file` "
    "tool. The report MUST contain three sections (one per file), each "
    "with the function name, one-sentence summary, and the TODO text "
    "extracted by the corresponding sub-agent.\n\n"
    "Do NOT ask for confirmation. Proceed directly. Stop when "
    "findings.md is written."
)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R3 is real-AWS gated.",
)
def test_r3_three_subagents_synthesis(tmp_path):
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from runtime.audit import AUDIT
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_coord = getattr(CONFIG, "coordinator_mode_enabled", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    cwd_before = os.getcwd()

    captured_stdout: list = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        try:
            print(text)
        except Exception:
            pass

    try:
        (tmp_path / "utils_a.py").write_text(_UTILS_A, encoding="utf-8")
        (tmp_path / "utils_b.py").write_text(_UTILS_B, encoding="utf-8")
        (tmp_path / "utils_c.py").write_text(_UTILS_C, encoding="utf-8")

        audit_dir = tmp_path / "audit_logs"
        audit_dir.mkdir(exist_ok=True)

        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R3_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 2048
        CONFIG.require_tool_approval = False
        CONFIG.coordinator_mode_enabled = True
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R3_COST_CAP_USD
            )

        agent = Agent(
            client=client,
            max_turns=18,
            on_stop_check=_hard_cost_halt,
        )

        # Pre-promote `task` + `write_file` from deferred -> visible.
        agent._engine._discovered_tool_names = {"task", "write_file"}

        t0 = time.time()
        result = agent.run(_R3_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        task_dispatches: list = []
        for f in audit_dir.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("tool_name") == "task" and e.get("action") == "tool_dispatch":
                    task_dispatches.append(e)

        explore_dispatches = [
            d for d in task_dispatches
            if (d.get("parameters") or {}).get("subagent_type") == "explore"
        ]

        findings_fp = tmp_path / "findings.md"
        findings_text = (
            findings_fp.read_text(encoding="utf-8") if findings_fp.is_file() else ""
        )
        function_hits = [n for n in _FUNCTION_NAMES if n in findings_text]
        marker_hits = [m for m in _MARKERS if m in findings_text]

        metrics = { ... }  # JSON dump of all metrics
        (tmp_path / "_r3_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[R3 METRICS] {json.dumps(metrics)}")

        # Assertions
        assert result.stop_reason != "max_turns"
        assert len(task_dispatches) >= 3
        assert len(explore_dispatches) >= 3
        assert findings_fp.is_file()
        assert len(function_hits) == 3  # all 3 function names present
        assert len(marker_hits) == 3    # all 3 TODO markers present
        assert cost_used <= _R3_COST_CAP_USD

    finally:
        os.chdir(cwd_before)
        # ... restore all CONFIG saves + AUDIT.__init__ + TOKENS.reset()
=== END TEST CODE ===

PRODUCE THREE INDEPENDENT VERDICTS.

=== AXIS A — Test design soundness ===
- Does the scenario actually exercise what it claims? Cite the assertion(s) that would fail if v5 regressed in the relevant Block.
- Are assertions specific (test specific behavior), not loose (test "no error")?
- Will this test pass even if v5 silently does something wrong? (false-positive risk)
- Are setup/teardown correct? Files cleaned up? No state leaks?
- Could the test pass on a mock that masks a real-Bedrock bug?

Concerns to consider specifically:
  (1) The test uses `>= 3` for task_dispatches and explore_dispatches. Is that loose enough that the model could pass via 4 retries? If so, recommend tightening to == 3.
  (2) `AUDIT.__init__(audit_dir=...)` is invoked to point AUDIT at the per-test audit_dir. Is this the documented way to repoint AUDIT? Could it leave residual state from earlier tests?
  (3) `agent._engine._discovered_tool_names = {"task", "write_file"}` pre-promotes 2 tools. Is the test still empirically validating Block G3 / Phase 9 if we skip the discovery loop? (Argument FOR: tool_search discovery is covered by other Block-tagged tests; R3's job is the spawn + synthesis path.)
  (4) `findings.md` MUST have all 3 function names AND all 3 markers via `len(function_hits) == 3` / `len(marker_hits) == 3`. This is tight and falsifiable. Confirm.
  (5) Sub-agent reply format prescribed: "FUNCTION: <name>\\nSUMMARY: <one-sentence>\\nTODO: <todo text>". Does the parent need to faithfully transcribe these into findings.md, or could it summarize and lose markers? (Marker hit assertion catches this.)

Output:
AXIS A VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
Findings: [severity] file:line — issue — fix

=== AXIS B — Cost-control soundness ===
- Cost estimate worst case at AU-Haiku-4.5 = $1.10/MTok in / $5.50/MTok out.
  - Parent ~10 turns × ~5K input × 1.10 = ~$0.055 in. Output 10 × 2K (max_tokens=2048) × 5.50 = ~$0.11 out. Parent total ~$0.165.
  - Each child ~3 turns × ~3K in × 1.10 = ~$0.01. 3 children = $0.03 in. Output 9 × 1K × 5.50 = ~$0.05 out. Children total ~$0.08.
  - Total estimate: ~$0.25. Cap: $0.50. Headroom: 50%.
- session_cost_limit enforced via Agent on_stop_check (TOKENS.is_over_budget) at line in test. Confirmed hard halt path.
- max_turns=18 on parent + max_turns=20 on each `explore` sub-agent (from agent_types.py:101) = bounded. IterationBudget shared.
- Could the model loop on tool_search retries that don't return `task`? Mitigation: test pre-populates _discovered_tool_names so model sees `task` from turn 1.
- Could the parent retry sub-agent dispatches if a child fails? Sub-agent IterationBudget halts at max_turns, returns partial output. Parent could retry — `>= 3` accepts up to ~5 retries within cap.

Output:
AXIS B VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
Findings: [cost-risk] specific scenario — mitigation

=== AXIS C — Coverage of v5 EMPIRICAL evidence ===
- This test contributes empirical evidence for: Block G3 (coordinator-mode parent prompt augmentation), Phase 9 task tool (subagent spawn end-to-end on real Bedrock), audit_log subagent_dispatches recording, parent synthesis pattern.
- Falsifiable claims:
  - Parent CAN issue 3 sub-agent dispatches with the chosen agent_type (assertion: explore_dispatches >= 3).
  - Sub-agents return real content from real file reads via real Bedrock (assertion: marker_hits == 3 — only achievable if children read the files and parent transcribed faithfully).
  - findings.md content has the function names from the file dispatches (assertion: function_hits == 3).
- v5-only: Block V (head-to-head v4) DROPPED per user 2026-05-03. Do NOT request side-by-side runs.
- Coverage gap: true async-parallel sub-agent dispatch is NOT tested here (v5 doesn't ship async). Acceptable per Phase 9 docstring.

Output:
AXIS C VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
Coverage gap (if any): {{what claim still needs separate test}}

=== FINAL ===
PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL | REJECT (do not run AWS)
If REJECT: required fixes before next pre-flight review.
If APPROVE: log to r_tier_review_log.md and proceed to AWS call.
codex
I’ll verify the local test file line numbers against the inlined version so the review points are grounded in the actual file.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"task_dispatches|explore_dispatches|AUDIT\\.__init__|_discovered_tool_names|function_hits|marker_hits|on_stop_check|max_turns=18|metrics =\" compact_v5/MAIN/agent/tests/r_tier/test_r3_three_subagents.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/tests/r_tier/test_r3_three_subagents.py | Select-Object -First 320' in D:\Github\sagemaker-coding-agent
 succeeded in 2373ms:
"""R-tier R3 â€” three sub-agent dispatches + parent synthesis.

Per PS_V5_TEST_PLAYBOOK / PS_V5_TEST_SET Â§Tier 1 R3:
  Validates Block G3 (coordinator-mode prompt) + Phase 9 task tool
  (sub-agent spawn) end-to-end on real Bedrock:
    - Parent receives a coding-survey task across 3 small Python files.
    - Parent dispatches 3 sub-agents (subagent_type='explore'),
      one per file.
    - Each sub-agent reads its assigned file and reports the function
      name + 1-line summary + the TODO comment text.
    - Parent synthesizes the 3 results into a single findings.md.

Note on "parallel": v5's task tool is `is_concurrency_safe=False` â€”
  spawn is synchronous. The 3 dispatches are SEQUENTIAL on the
  parent's call stack. The TEST_PLAYBOOK label "Three parallel
  sub-agents" reflects the v4/Runnable phrasing; on v5 we test the
  real implementation: 3 ordered sub-agent dispatches with parent
  synthesis. True async parallel sub-agents land in a future phase.

Validation pillars:
  - subagent_dispatches audit entries == 3 (build_telemetry.py read).
  - All 3 dispatches are agent_type='explore'.
  - findings.md exists and mentions all 3 function names + TODOs.
  - Parent stop_reason != max_turns.
  - Cost <= $0.50.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R3_COST_CAP_USD = 0.50

# ============================================================
# 3 small Python file fixtures â€” distinctive function names + TODOs
# so each sub-agent has unambiguous content to extract.
# ============================================================

_UTILS_A = '''"""Module A â€” string utilities."""


def kebab_case(text: str) -> str:
    """Convert spaces and underscores to hyphens; lowercase the result.

    Examples:
      'Hello World' -> 'hello-world'
      'snake_case_text' -> 'snake-case-text'
    """
    # TODO(R3-marker-A): handle Unicode whitespace beyond ASCII space.
    return text.replace("_", " ").lower().replace(" ", "-")
'''

_UTILS_B = '''"""Module B â€” numeric utilities."""


def clamp(value: float, lo: float, hi: float) -> float:
    """Constrain *value* to the inclusive range [lo, hi].

    If lo > hi the function returns *value* unchanged.
    """
    # TODO(R3-marker-B): raise ValueError when lo > hi instead of silent fall-through.
    if lo > hi:
        return value
    return max(lo, min(hi, value))
'''

_UTILS_C = '''"""Module C â€” list utilities."""


def chunked(items, size):
    """Yield successive *size*-length chunks from *items*.

    The final chunk may be shorter than *size* if the input length
    is not a multiple of *size*.
    """
    # TODO(R3-marker-C): support negative or zero size with a clear error.
    for i in range(0, len(items), size):
        yield items[i:i + size]
'''

_FUNCTION_NAMES = ("kebab_case", "clamp", "chunked")
_MARKERS = ("R3-marker-A", "R3-marker-B", "R3-marker-C")

_R3_PROMPT = (
    "There are three Python files in the current directory: utils_a.py, "
    "utils_b.py, utils_c.py. Each defines exactly ONE public function "
    "and contains exactly ONE `# TODO(...)` comment.\n\n"
    "TASK:\n"
    "1. Spawn THREE sub-agents using the `task` tool, ONE PER FILE. Use "
    "subagent_type='explore' for each (read-only is sufficient).\n"
    "   - Sub-agent 1 prompt: 'Read utils_a.py. Report the function name, "
    "what the function does in one sentence, and the exact TODO comment "
    "text from that file. Reply in this format:\\nFUNCTION: <name>\\n"
    "SUMMARY: <one-sentence>\\nTODO: <todo text>'\n"
    "   - Sub-agent 2 prompt: same but for utils_b.py.\n"
    "   - Sub-agent 3 prompt: same but for utils_c.py.\n"
    "2. After ALL three sub-agents return, write a single Markdown report "
    "named `findings.md` in the current directory using the `write_file` "
    "tool. The report MUST contain three sections (one per file), each "
    "with the function name, one-sentence summary, and the TODO text "
    "extracted by the corresponding sub-agent.\n\n"
    "Do NOT ask for confirmation. Proceed directly. Stop when "
    "findings.md is written."
)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R3 is real-AWS gated.",
)
def test_r3_three_subagents_synthesis(tmp_path):
    """R-tier R3 â€” three sub-agent dispatches + parent synthesis.

    PASS criteria:
      - audit_log records >= 3 task-tool dispatches with subagent_type='explore'.
      - findings.md exists.
      - findings.md mentions all 3 function names AND all 3 TODO markers.
      - parent stop_reason != max_turns.
      - cost <= $0.50.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from runtime.audit import AUDIT
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_coord = getattr(CONFIG, "coordinator_mode_enabled", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    cwd_before = os.getcwd()

    captured_stdout: list = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        try:
            print(text)
        except Exception:
            pass

    try:
        # ------------------------------------------------------------
        # Workspace fixture â€” 3 utility files
        # ------------------------------------------------------------
        (tmp_path / "utils_a.py").write_text(_UTILS_A, encoding="utf-8")
        (tmp_path / "utils_b.py").write_text(_UTILS_B, encoding="utf-8")
        (tmp_path / "utils_c.py").write_text(_UTILS_C, encoding="utf-8")

        # Audit dir lives next to the workspace so we can re-read its
        # JSONL after the run for the subagent_dispatches assertion.
        audit_dir = tmp_path / "audit_logs"
        audit_dir.mkdir(exist_ok=True)

        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R3_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        # Cap per-turn output cost. R3 worst case = parent (~10 turns) +
        # 3 children (~3 turns each) â‰ˆ 19 turns Ã— max_tokens. Keep tight.
        CONFIG.max_tokens = 2048
        CONFIG.require_tool_approval = False
        CONFIG.coordinator_mode_enabled = True
        sec_mgr.rebuild_singleton_for_tests()
        # Re-init audit singleton with the new audit_dir.
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R3_COST_CAP_USD
            )

        agent = Agent(
            client=client,
            max_turns=18,  # parent budget â€” children share IterationBudget
            on_stop_check=_hard_cost_halt,
        )

        # Pre-promote `task` + `write_file` from deferred â†’ visible so the
        # parent doesn't need a tool_search round-trip just to dispatch.
        # Block G3 + Phase 9 are what we're validating; tool_search is
        # already covered by other Block-tagged tests.
        agent._engine._discovered_tool_names = {"task", "write_file"}

        t0 = time.time()
        result = agent.run(_R3_PROMPT, output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        # ------------------------------------------------------------
        # Read audit_log for subagent_dispatches
        # ------------------------------------------------------------
        # AUDIT writes one JSONL per session per date; collect them all
        # and filter for tool_name == 'task'.
        task_dispatches: list = []
        for f in audit_dir.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("tool_name") == "task" and e.get("action") == "tool_dispatch":
                    task_dispatches.append(e)

        explore_dispatches = [
            d for d in task_dispatches
            if (d.get("parameters") or {}).get("subagent_type") == "explore"
        ]

        findings_fp = tmp_path / "findings.md"
        findings_text = (
            findings_fp.read_text(encoding="utf-8") if findings_fp.is_file() else ""
        )
        function_hits = [n for n in _FUNCTION_NAMES if n in findings_text]
        marker_hits = [m for m in _MARKERS if m in findings_text]

        metrics = {
            "test": "R3",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": int(getattr(result, "turns_used", 0)),
            "api_calls": int(api_calls),
            "cost_usd": round(cost_used, 4),
            "stop_reason": result.stop_reason,
            "task_dispatches": len(task_dispatches),
            "explore_dispatches": len(explore_dispatches),
            "findings_exists": findings_fp.is_file(),
            "function_hits": function_hits,
            "marker_hits": marker_hits,
            "findings_size_bytes": (
                findings_fp.stat().st_size if findings_fp.is_file() else 0
            ),
            "coordinator_mode_enabled": True,
        }
        (tmp_path / "_r3_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R3 METRICS] {json.dumps(metrics)}")

        # ------------------------------------------------------------
        # Assertions
        # ------------------------------------------------------------
        assert result.stop_reason != "max_turns", (
            f"R3 parent hit max_turns (18); incomplete. metrics={metrics}"
        )
        # Exactly 3 sub-agent dispatches expected, but accept >=3 in case
        # the model retried one (Codex iter-N may tighten to ==3 after
        # observing real call patterns).
        assert len(task_dispatches) >= 3, (
            f"R3 expected >=3 task-tool dispatches; got "
            f"{len(task_dispatches)}. metrics={metrics}"
        )
        assert len(explore_dispatches) >= 3, (
            f"R3 expected >=3 dispatches with subagent_type='explore'; "
            f"got {len(explore_dispatches)}. metrics={metrics}"
        )
        assert findings_fp.is_file(), (
            f"R3 findings.md not produced. metrics={metrics}"
        )
        assert len(function_hits) == 3, (
            f"R3 findings.md missing function name(s). expected all of "
            f"{_FUNCTION_NAMES}; found {function_hits}. "
            f"body[:500]={findings_text[:500]!r}"
        )
        assert len(marker_hits) == 3, (
            f"R3 findings.md missing TODO marker(s). expected all of "
            f"{_MARKERS}; found {marker_hits}. "
            f"body[:500]={findings_text[:500]!r}"
        )
        assert cost_used <= _R3_COST_CAP_USD, (
            f"R3 cost ${cost_used:.4f} exceeded cap ${_R3_COST_CAP_USD}. "
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

 succeeded in 3028ms:
187:        AUDIT.__init__(audit_dir=str(audit_dir))
201:            max_turns=18,  # parent budget — children share IterationBudget
202:            on_stop_check=_hard_cost_halt,
209:        agent._engine._discovered_tool_names = {"task", "write_file"}
225:        task_dispatches: list = []
235:                    task_dispatches.append(e)
237:        explore_dispatches = [
238:            d for d in task_dispatches
246:        function_hits = [n for n in _FUNCTION_NAMES if n in findings_text]
247:        marker_hits = [m for m in _MARKERS if m in findings_text]
249:        metrics = {
261:            "task_dispatches": len(task_dispatches),
262:            "explore_dispatches": len(explore_dispatches),
264:            "function_hits": function_hits,
265:            "marker_hits": marker_hits,
285:        assert len(task_dispatches) >= 3, (
287:            f"{len(task_dispatches)}. metrics={metrics}"
289:        assert len(explore_dispatches) >= 3, (
291:            f"got {len(explore_dispatches)}. metrics={metrics}"
296:        assert len(function_hits) == 3, (
298:            f"{_FUNCTION_NAMES}; found {function_hits}. "
301:        assert len(marker_hits) == 3, (
303:            f"{_MARKERS}; found {marker_hits}. "
326:            AUDIT.__init__(audit_dir=saved_audit_dir)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/tests/r_tier/test_r3_three_subagents.py | Select-Object -Skip 320 -First 80' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "class Audit|def __init__|audit_dir|tool_dispatch|subagent_dispatch" compact_v5/MAIN/agent/runtime compact_v5/MAIN/agent -g "*.py"' in D:\Github\sagemaker-coding-agent
 succeeded in 2294ms:
            CONFIG.require_tool_approval = saved_require_approval
        if saved_coord is not None:
            CONFIG.coordinator_mode_enabled = saved_coord
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
            AUDIT.__init__(audit_dir=saved_audit_dir)
        TOKENS.reset()

 succeeded in 2930ms:
compact_v5/MAIN/agent\agent.py:63:    def __init__(
compact_v5/MAIN/agent/runtime\audit.py:7:`audit_dir` + `audit_retention_days` + `disable_local_traces` without
compact_v5/MAIN/agent/runtime\audit.py:25:class AuditEntry:
compact_v5/MAIN/agent/runtime\audit.py:46:class AuditLogger:
compact_v5/MAIN/agent/runtime\audit.py:59:    def __init__(self, audit_dir: Optional[str] = None, config=None):
compact_v5/MAIN/agent/runtime\audit.py:62:        self.audit_dir = audit_dir or cfg.audit_dir
compact_v5/MAIN/agent/runtime\audit.py:67:                os.makedirs(self.audit_dir, exist_ok=True)
compact_v5/MAIN/agent/runtime\audit.py:70:                logging.warning(f"AuditLogger: cannot create audit_dir {self.audit_dir}: {e}")
compact_v5/MAIN/agent/runtime\audit.py:87:        return os.path.join(self.audit_dir, f"{date}_{session_id}.jsonl")
compact_v5/MAIN/agent/runtime\audit.py:140:        if self._disabled or not os.path.isdir(self.audit_dir):
compact_v5/MAIN/agent/runtime\audit.py:143:        for filename in os.listdir(self.audit_dir):
compact_v5/MAIN/agent/runtime\audit.py:145:                path = os.path.join(self.audit_dir, filename)
compact_v5/MAIN/agent/runtime\audit.py:162:        if retention_days <= 0 or not os.path.isdir(self.audit_dir):
compact_v5/MAIN/agent/runtime\audit.py:165:        for filename in os.listdir(self.audit_dir):
compact_v5/MAIN/agent/runtime\audit.py:175:                    os.remove(os.path.join(self.audit_dir, filename))
compact_v5/MAIN/agent/runtime\audit.py:180:# Module-level singleton (parity with v4 `AUDIT = AuditLogger(CONFIG.audit_dir)`).
compact_v5/MAIN/agent/runtime\bedrock_client.py:126:    def __init__(
compact_v5/MAIN/agent\runtime\dream.py:109:    def __init__(self, workspace: str, stale_after_s: float = 600.0):
compact_v5/MAIN/agent\runtime\session.py:52:    def __init__(self, sessions_dir: Optional[str] = None, config=None):
compact_v5/MAIN/agent\runtime\config.py:44:    audit_dir: str = os.path.join(os.getcwd(), "audit_logs")
compact_v5/MAIN/agent\runtime\tokens.py:317:    def __init__(self, config=None):
compact_v5/MAIN/agent\runtime\file_cache.py:36:    def __init__(self, max_entries: int = 100):
compact_v5/MAIN/agent/runtime\tokens.py:317:    def __init__(self, config=None):
compact_v5/MAIN/agent\runtime\snapshot.py:30:    def __init__(self, workspace: Optional[str] = None, config=None):
compact_v5/MAIN/agent/runtime\snapshot.py:30:    def __init__(self, workspace: Optional[str] = None, config=None):
compact_v5/MAIN/agent\runtime\bedrock_client.py:126:    def __init__(
compact_v5/MAIN/agent/runtime\session.py:52:    def __init__(self, sessions_dir: Optional[str] = None, config=None):
compact_v5/MAIN/agent\core\compactor.py:63:    def __init__(self, cooldown_seconds: int = 30, max_per_session: int = 10):
compact_v5/MAIN/agent\runtime\audit.py:7:`audit_dir` + `audit_retention_days` + `disable_local_traces` without
compact_v5/MAIN/agent\runtime\audit.py:25:class AuditEntry:
compact_v5/MAIN/agent\runtime\audit.py:46:class AuditLogger:
compact_v5/MAIN/agent\runtime\audit.py:59:    def __init__(self, audit_dir: Optional[str] = None, config=None):
compact_v5/MAIN/agent\runtime\audit.py:62:        self.audit_dir = audit_dir or cfg.audit_dir
compact_v5/MAIN/agent\runtime\audit.py:67:                os.makedirs(self.audit_dir, exist_ok=True)
compact_v5/MAIN/agent\runtime\audit.py:70:                logging.warning(f"AuditLogger: cannot create audit_dir {self.audit_dir}: {e}")
compact_v5/MAIN/agent\runtime\audit.py:87:        return os.path.join(self.audit_dir, f"{date}_{session_id}.jsonl")
compact_v5/MAIN/agent\runtime\audit.py:140:        if self._disabled or not os.path.isdir(self.audit_dir):
compact_v5/MAIN/agent\runtime\audit.py:143:        for filename in os.listdir(self.audit_dir):
compact_v5/MAIN/agent\runtime\audit.py:145:                path = os.path.join(self.audit_dir, filename)
compact_v5/MAIN/agent\runtime\audit.py:162:        if retention_days <= 0 or not os.path.isdir(self.audit_dir):
compact_v5/MAIN/agent\runtime\audit.py:165:        for filename in os.listdir(self.audit_dir):
compact_v5/MAIN/agent\runtime\audit.py:175:                    os.remove(os.path.join(self.audit_dir, filename))
compact_v5/MAIN/agent\runtime\audit.py:180:# Module-level singleton (parity with v4 `AUDIT = AuditLogger(CONFIG.audit_dir)`).
compact_v5/MAIN/agent/runtime\file_cache.py:36:    def __init__(self, max_entries: int = 100):
compact_v5/MAIN/agent\core\budget.py:37:    def __init__(self, max_iterations: int = DEFAULT_MAX):
compact_v5/MAIN/agent\core\cache_break_detection.py:81:    def __init__(self) -> None:
compact_v5/MAIN/agent\core\query_engine.py:199:    def __init__(
compact_v5/MAIN/agent\core\query_engine.py:991:                            action="tool_dispatch",
compact_v5/MAIN/agent/runtime\dream.py:109:    def __init__(self, workspace: str, stale_after_s: float = 600.0):
compact_v5/MAIN/agent/runtime\config.py:44:    audit_dir: str = os.path.join(os.getcwd(), "audit_logs")
compact_v5/MAIN/agent\security\manager.py:144:    def __init__(
compact_v5/MAIN/agent\skills\manager.py:127:    def __init__(
compact_v5/MAIN/agent\ui\chat_ui.py:97:    def __init__(self, agent: Any):
compact_v5/MAIN/agent\ui\chat_ui.py:188:    def __init__(self, agent: Any):
compact_v5/MAIN/agent\ui\approval_dialog.py:315:    def __init__(self, max_per_minute: int = 100, max_per_session: int = 1500):
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:52:    def __init__(self, script):
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:167:        def __init__(self):
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:61:    def __init__(self, script):
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:21:  - subagent_dispatches audit entries == 3 (build_telemetry.py read).
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:151:    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:172:        # JSONL after the run for the subagent_dispatches assertion.
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:173:        audit_dir = tmp_path / "audit_logs"
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:174:        audit_dir.mkdir(exist_ok=True)
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:177:        CONFIG.audit_dir = str(audit_dir)
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:186:        # Re-init audit singleton with the new audit_dir.
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:187:        AUDIT.__init__(audit_dir=str(audit_dir))
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:221:        # Read audit_log for subagent_dispatches
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:226:        for f in audit_dir.glob("*.jsonl"):
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:234:                if e.get("tool_name") == "task" and e.get("action") == "tool_dispatch":
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:324:        if saved_audit_dir is not None:
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:325:            CONFIG.audit_dir = saved_audit_dir
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:326:            AUDIT.__init__(audit_dir=saved_audit_dir)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:72:    audit = AuditLogger(audit_dir=str(tmp_path))
compact_v5/MAIN/agent\tests\integration\test_block_b.py:75:        action="tool_dispatch",
compact_v5/MAIN/agent\tests\integration\test_block_b.py:91:    assert entry["action"] == "tool_dispatch"
compact_v5/MAIN/agent\tests\integration\test_block_b.py:103:    audit = AuditLogger(audit_dir=str(tmp_path))
compact_v5/MAIN/agent\tests\integration\test_block_b.py:106:        action="tool_dispatch",
compact_v5/MAIN/agent\tests\integration\test_block_b.py:486:def test_audit_log_on_unknown_tool_dispatch(tmp_path, monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_block_b.py:494:    test_audit = AuditLogger(audit_dir=str(tmp_path))
compact_v5/MAIN/agent\tests\integration\test_block_b.py:541:    test_audit = AuditLogger(audit_dir=str(tmp_path))
compact_v5/MAIN/agent\tests\integration\test_block_b.py:603:    test_audit = AuditLogger(audit_dir=str(tmp_path))
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:170:    def __init__(self, script):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:39:    def __init__(self, script):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:385:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:438:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:474:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:504:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:556:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:637:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:167:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:202:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:259:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:359:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:420:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:482:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_block_m.py:41:    def __init__(self, script):
compact_v5/MAIN/agent\tests\integration\test_block_n.py:172:        def __init__(self, name, input_, id):
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:148:        def __init__(self, data: bytes):
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:196:        def __init__(self, data: bytes):
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:237:        def __init__(self, d):
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:282:        def __init__(self, d):
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:320:        def __init__(self):
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:347:        def __init__(self, d):
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:440:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:49:def test_build_telemetry_aggregates_tool_dispatch_events(tmp_path):
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:50:    """Aggregator groups tool_dispatch events by chronological window
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:56:         "session_id": "s1", "action": "tool_dispatch",
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:60:         "session_id": "s1", "action": "tool_dispatch",
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:65:         "session_id": "s1", "action": "tool_dispatch",
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:70:         "session_id": "s1", "action": "tool_dispatch",
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:87:                "compaction_events", "subagent_dispatches",
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:129:         "session_id": "s1", "action": "tool_dispatch",
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:213:         "session_id": "s1", "action": "tool_dispatch",
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:227:    assert len(telemetry["subagent_dispatches"]) == 1
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:228:    assert telemetry["subagent_dispatches"][0]["agent_type"] == "explore"
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:35:    def __init__(self, script):
compact_v5/MAIN/agent\tests\integration\test_skills.py:237:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_skills.py:283:        def __init__(self):
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:93:            "subagent_dispatches": [],
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:146:            "subagent_dispatches": [],
compact_v5/MAIN/agent\tests\integration\test_subagent.py:29:    def __init__(self, script):
compact_v5/MAIN/agent\tests\integration\test_subagent.py:451:        def __init__(self, victim):
compact_v5/MAIN/agent\tests\integration\test_subagent.py:515:        def __init__(self, victim):

codex
The local file matches the provided design, with the key loose dispatch assertions at lines 285 and 289. I’m checking the audit singleton implementation next because that affects whether the audit evidence can be trusted across tests.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/runtime/audit.py | Select-Object -First 220' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/core/query_engine.py | Select-Object -Skip 960 -First 60' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "agent_types|max_turns|explore|IterationBudget|task" compact_v5/MAIN/agent -g "*.py"' in D:\Github\sagemaker-coding-agent
 succeeded in 2448ms:
"""Block B â€” AuditLogger + AuditEntry verbatim port.

Verbatim port of v4's `AuditLogger` (compact_v4/MAIN/agent/sagemaker_agent.py
lines 2173-2253) plus its `AuditEntry` dataclass (lines 2156-2170).
Adaptations for v5: constructor takes a config object (instead of reading
the global CONFIG singleton at import time) so tests can pin
`audit_dir` + `audit_retention_days` + `disable_local_traces` without
monkey-patching the live runtime.

PORT_LOG: see #043.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class AuditEntry:
    """Single audit log entry. SHA256(content_prefix) hash for tamper detection."""

    timestamp: str
    session_id: str
    action: str
    tool_name: Optional[str]
    parameters: Dict[str, Any]
    result_summary: str
    user_approved: bool
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = (
                f"{self.timestamp}|{self.session_id}|{self.action}|"
                f"{self.tool_name}|{self.result_summary}"
            )
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:32]


class AuditLogger:
    """Thread-safe append-only audit trail with integrity hashes.

    Writes one JSONL file per session+date. Sensitive parameter keys
    (password / secret / token / api_key / etc.) are redacted before
    serialization. Long string values are summarized as `[N chars]`.
    """

    SENSITIVE_KEYS = {
        "password", "secret", "key", "token", "credential",
        "api_key", "auth", "bearer", "private",
    }

    def __init__(self, audit_dir: Optional[str] = None, config=None):
        self._config_override = config
        cfg = self._config
        self.audit_dir = audit_dir or cfg.audit_dir
        self._lock = threading.Lock()
        self._disabled = cfg.disable_local_traces
        if not self._disabled:
            try:
                os.makedirs(self.audit_dir, exist_ok=True)
                self.prune_old_logs(cfg.audit_retention_days)
            except OSError as e:
                logging.warning(f"AuditLogger: cannot create audit_dir {self.audit_dir}: {e}")
                self._disabled = True

    @property
    def _config(self):
        """Resolve CONFIG lazily so reloads in tests don't strand us."""
        if self._config_override is not None:
            return self._config_override
        from runtime.config import CONFIG as _CFG  # noqa: F401
        return _CFG

    # --------------------------------------------------------
    # Path resolution
    # --------------------------------------------------------

    def _get_log_path(self, session_id: str) -> str:
        date = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.audit_dir, f"{date}_{session_id}.jsonl")

    # --------------------------------------------------------
    # Public log API
    # --------------------------------------------------------

    def log(
        self,
        session_id: str,
        action: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        result_summary: str = "",
        user_approved: bool = True,
    ):
        """Append an audit entry. No-op when stealth-mode disabled."""
        if self._disabled:
            return
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            action=action,
            tool_name=tool_name,
            parameters=self._sanitize_params(parameters or {}),
            result_summary=result_summary[:500] if result_summary else "",
            user_approved=user_approved,
        )
        log_path = self._get_log_path(session_id)
        with self._lock:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry)) + "\n")

    # --------------------------------------------------------
    # Sanitizer (verbatim from v4)
    # --------------------------------------------------------

    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        sanitized: Dict[str, Any] = {}
        for k, v in params.items():
            if any(s in k.lower() for s in self.SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 1000:
                sanitized[k] = f"[{len(v)} chars]"
            else:
                sanitized[k] = v
        return sanitized

    # --------------------------------------------------------
    # Read API
    # --------------------------------------------------------

    def get_session_log(self, session_id: str) -> List[Dict[str, Any]]:
        """Return all entries for a session_id, sorted by timestamp."""
        if self._disabled or not os.path.isdir(self.audit_dir):
            return []
        entries: List[Dict[str, Any]] = []
        for filename in os.listdir(self.audit_dir):
            if session_id in filename and filename.endswith(".jsonl"):
                path = os.path.join(self.audit_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                entries.append(json.loads(line))
                except (OSError, json.JSONDecodeError):
                    continue
        return sorted(entries, key=lambda x: x.get("timestamp", ""))

    # --------------------------------------------------------
    # Retention
    # --------------------------------------------------------

    def prune_old_logs(self, retention_days: int):
        """Delete audit logs older than retention_days based on filename date prefix."""
        if retention_days <= 0 or not os.path.isdir(self.audit_dir):
            return
        cutoff = datetime.now().date() - timedelta(days=retention_days)
        for filename in os.listdir(self.audit_dir):
            if not filename.endswith(".jsonl"):
                continue
            date_str = filename.split("_", 1)[0]
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                try:
                    os.remove(os.path.join(self.audit_dir, filename))
                except OSError:
                    pass


# Module-level singleton (parity with v4 `AUDIT = AuditLogger(CONFIG.audit_dir)`).
AUDIT = AuditLogger()


__all__ = ["AuditEntry", "AuditLogger", "AUDIT"]

 succeeded in 3444ms:
                # the error to the model rather than the human user.
                # `parent_engine` is passed for Phase 9 task tool â€” the sub-agent
                # spawn needs the parent's IterationBudget + BedrockClient (ADR-015).
                try:
                    if call.name in {"bash", "python_exec"}:
                        self._exec_call_count += 1
                    raw = tool.execute(_repaired_input, context={
                        "active_tools": tools,
                        "plan_mode": plan_mode,
                        "parent_engine": self,
                        "parent_depth": getattr(self, "_subagent_depth", 0),
                        # Block I-1/I-5: edit_file + write_file consume this
                        # to auto-activate skills with `paths:` frontmatter.
                        "skill_manager": self.skill_manager,
                        "session_id": self.session_id,
                    })
                    text = _coerce_tool_result_to_text(raw)
                    text = _truncate_tool_result(text, tool.max_result_size_chars)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": text,
                    })
                    # Block B (PORT_LOG #043): audit-log every tool dispatch
                    # so /diffs / /regression / forensics have a tamper-hashed
                    # trail. Best-effort.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="tool_dispatch",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=text[:500] if isinstance(text, str) else "",
                            user_approved=True,
                        )
                    except Exception:
                        pass
                    # Phase 7 wiring: extract discovered names from tool_search
                    # results and add to the next turn's tools= payload.
                    if call.name == "tool_search":
                        discovered = tool_search_discovered_names(text)
                        if discovered:
                            self._discovered_tool_names.update(discovered)
                except Exception as exc:  # noqa: BLE001 â€” surface to model
                    logging.warning(
                        "[query_engine] tool '%s' raised %s: %s",
                        call.name, type(exc).__name__, exc,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": f"Error: {type(exc).__name__}: {exc}",
                        "is_error": True,
                    })
                    # Audit the failed dispatch too so forensics can see what
                    # was attempted (sanitized parameters; no result body).
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(

 succeeded in 4215ms:
compact_v5/MAIN/agent\agent.py:5:  - `core.budget.IterationBudget` (Phase 8)
compact_v5/MAIN/agent\agent.py:24:from core import IterationBudget, QueryEngine
compact_v5/MAIN/agent\agent.py:66:        max_turns: int = 50,
compact_v5/MAIN/agent\agent.py:67:        budget: Optional[IterationBudget] = None,
compact_v5/MAIN/agent\agent.py:79:            max_turns: hard upper bound on turns per `run()` call.
compact_v5/MAIN/agent\agent.py:80:            budget: shared IterationBudget. If None, a fresh one is created.
compact_v5/MAIN/agent\agent.py:92:        self.budget = budget if budget is not None else IterationBudget()
compact_v5/MAIN/agent\agent.py:105:            max_turns=max_turns,
compact_v5/MAIN/agent\sagemaker_agent.py:27:    IterationBudget,
compact_v5/MAIN/agent\sagemaker_agent.py:36:    "IterationBudget",
compact_v5/MAIN/agent\entry.py:84:# IterationBudget for power users + tests (Phase 8).
compact_v5/MAIN/agent\entry.py:85:from core.budget import IterationBudget  # noqa: F401
compact_v5/MAIN/agent\coordinator\system_prompt.py:16:_TASK_TOOL_NAME = "task"
compact_v5/MAIN/agent\coordinator\system_prompt.py:39:Most tasks decompose into:
compact_v5/MAIN/agent\coordinator\system_prompt.py:54:task.
compact_v5/MAIN/agent\coordinator\system_prompt.py:60:- **Read-only tasks: run in parallel; Write tasks: one at a time per
compact_v5/MAIN/agent\coordinator\system_prompt.py:85:In v5, every `task` call spawns a worker that runs **synchronously to
compact_v5/MAIN/agent\coordinator\system_prompt.py:99:| Continuing the same role (explore that needs more depth, build retry, etc.) | Continue | Same `subagent_type` (e.g., explore→explore), restate prior findings + add the next focus |
compact_v5/MAIN/agent\coordinator\system_prompt.py:100:| Phase transition — explore findings need to be implemented | Spawn fresh | Different `subagent_type` (explore→build); brief with ONLY the relevant subset of findings + a concrete spec |
compact_v5/MAIN/agent\coordinator\system_prompt.py:104:| Completely unrelated task | Spawn fresh | New worker, brief it cleanly from scratch |
compact_v5/MAIN/agent\coordinator\system_prompt.py:109:**Critical**: Worker buffer NEVER persists across `task` calls in v5.
compact_v5/MAIN/agent\coordinator\system_prompt.py:140:  command. Give them higher-level tasks.
compact_v5/MAIN/agent\coordinator\system_prompt.py:148:- `explore` (read-only) — broad investigation, returns a report
compact_v5/MAIN/agent\coordinator\system_prompt.py:156:Match the role to the phase: Research → explore/plan/review;
compact_v5/MAIN/agent\coordinator\user_context.py:32:        "prompt). The available worker types are: explore, plan, verify, "
compact_v5/MAIN/agent\coordinator\user_context.py:35:        "task (recursive spawn for general/build/fork only), tool_search, "
compact_v5/MAIN/agent\coordinator\__init__.py:17:delegates work to `task` sub-agents.
compact_v5/MAIN/agent\coordinator\__init__.py:23:  (parent has the same engine); "spawn fresh" = new task() call.
compact_v5/MAIN/agent\core\compactor.py:355:            "1. Current task and goal\n"
compact_v5/MAIN/agent\core\budget_continuation.py:10:  existing IterationBudget surface (counts turns) instead of introducing a
compact_v5/MAIN/agent\core\budget_continuation.py:21:The Phase-11 IterationBudgetWidget made the budget VISIBLE, but a model that
compact_v5/MAIN/agent\core\__init__.py:7:  - core/budget.py       : IterationBudget (Hermes pattern via v4)
compact_v5/MAIN/agent\core\__init__.py:17:from .budget import IterationBudget  # noqa: F401
compact_v5/MAIN/agent\core\budget.py:1:"""V5 core/budget.py — IterationBudget (Hermes pattern via v4).
compact_v5/MAIN/agent\core\budget.py:3:Per ADR-014: verbatim port of v4's IterationBudget at
compact_v5/MAIN/agent\core\budget.py:11:max_turns times, blowing the cost ceiling. Insurance/audit values
compact_v5/MAIN/agent\core\budget.py:26:class IterationBudget:
compact_v5/MAIN/agent\core\query_engine.py:10:- Per-turn loop with end_turn / max_turns / budget exhausted exits.
compact_v5/MAIN/agent\core\query_engine.py:11:- IterationBudget gate at the top of each turn (shared with sub-agents).
compact_v5/MAIN/agent\core\query_engine.py:36:The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
compact_v5/MAIN/agent\core\query_engine.py:46:from .budget import IterationBudget
compact_v5/MAIN/agent\core\query_engine.py:61:    `stop_reason`    — "end_turn" | "max_turns" | "budget_exhausted" |
compact_v5/MAIN/agent\core\query_engine.py:64:    `budget_used`    — IterationBudget.used() snapshot at exit.
compact_v5/MAIN/agent\core\query_engine.py:193:    `run()` call. Sub-agents (Phase 9) will share the same IterationBudget
compact_v5/MAIN/agent\core\query_engine.py:202:        max_turns: int = DEFAULT_MAX_TURNS,
compact_v5/MAIN/agent\core\query_engine.py:203:        budget: Optional[IterationBudget] = None,
compact_v5/MAIN/agent\core\query_engine.py:215:            max_turns: hard upper bound on turns per `run()` call.
compact_v5/MAIN/agent\core\query_engine.py:216:            budget: shared IterationBudget. If None, a fresh one is created.
compact_v5/MAIN/agent\core\query_engine.py:223:                Hermes-filtered "skills relevant to this task" reminder to
compact_v5/MAIN/agent\core\query_engine.py:229:        self.max_turns = max(1, int(max_turns))
compact_v5/MAIN/agent\core\query_engine.py:230:        self.budget = budget if budget is not None else IterationBudget()
compact_v5/MAIN/agent\core\query_engine.py:234:        # default; sub-agents pass their type-string ("build", "explore",
compact_v5/MAIN/agent\core\query_engine.py:386:        # relevant to this task" reminder onto the first user turn so the
compact_v5/MAIN/agent\core\query_engine.py:463:        for turn in range(self.max_turns):
compact_v5/MAIN/agent\core\query_engine.py:494:                    "Adjust IterationBudget or start a new session.]"
compact_v5/MAIN/agent\core\query_engine.py:814:                                "task, ask_user, view_image, web_fetch are "
compact_v5/MAIN/agent\core\query_engine.py:962:                # `parent_engine` is passed for Phase 9 task tool — the sub-agent
compact_v5/MAIN/agent\core\query_engine.py:963:                # spawn needs the parent's IterationBudget + BedrockClient (ADR-015).
compact_v5/MAIN/agent\core\query_engine.py:1035:            stop_reason = "max_turns"
compact_v5/MAIN/agent\core\query_engine.py:1036:            output_fn(f"[Max turns reached: {self.max_turns}]")
compact_v5/MAIN/agent\prompt\sections.py:81:    Section("doing_tasks",             "doing_tasks.md",             300),
compact_v5/MAIN/agent\runtime\env_validation.py:4:A single helper for sanitizing all numeric env knobs (max_turns, budget,
compact_v5/MAIN/agent\runtime\config.py:47:    max_turns: int = 60
compact_v5/MAIN/agent\runtime\config.py:84:    # V4.10.10: 40 -> 200. Old 40-call ceiling was hit mid-task in real SageMaker
compact_v5/MAIN/agent\runtime\config.py:221:        "region": str, "model_id": str, "max_turns": int, "max_tokens": int,
compact_v5/MAIN/agent\runtime\config.py:267:        if key in ("max_turns", "max_tokens", "max_history", "subagent_max_depth") and val < 1:
compact_v5/MAIN/agent\runtime\config.py:313:    CONFIG.max_turns = _vbiev(
compact_v5/MAIN/agent\runtime\config.py:315:        minimum=1, maximum=10_000, default=CONFIG.max_turns,
compact_v5/MAIN/agent\subagent\__init__.py:3:Phase 9 (ADR-015): forkSubagent-style spawn with shared IterationBudget.
compact_v5/MAIN/agent\subagent\__init__.py:16:from .agent_types import (  # noqa: F401
compact_v5/MAIN/agent\ui\__init__.py:4:- `widgets.py`  — `IterationBudgetWidget` (PS Issue #2) + `ThinkingBudgetWidget` (PS Issue #4).
compact_v5/MAIN/agent\ui\__init__.py:10:from .widgets import IterationBudgetWidget, ThinkingBudgetWidget  # noqa: F401
compact_v5/MAIN/agent\ui\widgets.py:1:"""V5 ui/widgets.py — IterationBudgetWidget + ThinkingBudgetWidget (Phase 11).
compact_v5/MAIN/agent\ui\widgets.py:4:- **PS Issue #2** (visible IterationBudget): Phase 8 shipped the data model
compact_v5/MAIN/agent\ui\widgets.py:5:  (`core.budget.IterationBudget`). Phase 11 wires it to an
compact_v5/MAIN/agent\ui\widgets.py:38:# IterationBudgetWidget — PS Issue #2
compact_v5/MAIN/agent\ui\widgets.py:42:class IterationBudgetWidget:
compact_v5/MAIN/agent\ui\widgets.py:43:    """Live display of `IterationBudget` consumption.
compact_v5/MAIN/agent\ui\widgets.py:46:        w = IterationBudgetWidget(budget=engine.budget)
compact_v5/MAIN/agent\ui\widgets.py:55:    budget: Any                              # core.budget.IterationBudget
compact_v5/MAIN/agent\ui\widgets.py:189:    "IterationBudgetWidget",
compact_v5/MAIN/agent\subagent\fork.py:116:        "  Key files: <relevant file paths — include for research tasks>\n"
compact_v5/MAIN/agent\subagent\spawn.py:6:  cache-prefix-identical message replay, and `<task-notification>`
compact_v5/MAIN/agent\subagent\spawn.py:9:- v5's spawn ALWAYS shares the parent's IterationBudget instance — that is
compact_v5/MAIN/agent\subagent\spawn.py:12:  build/plan/explore/verify agent types are deferred (their large prompts
compact_v5/MAIN/agent\subagent\spawn.py:20:- Child shares IterationBudget instance.
compact_v5/MAIN/agent\subagent\spawn.py:23:    parent = QueryEngine(client=..., budget=IterationBudget())
compact_v5/MAIN/agent\subagent\spawn.py:41:# Block G — full AGENT_TYPES registry (build / plan / explore / verify /
compact_v5/MAIN/agent\subagent\spawn.py:68:def _new_child_engine(parent_engine: Any, max_turns: int, agent_type: str = "general") -> Any:
compact_v5/MAIN/agent\subagent\spawn.py:69:    """Construct a fresh QueryEngine that shares the parent's IterationBudget.
compact_v5/MAIN/agent\subagent\spawn.py:73:    tools/task.py which imports this module).
compact_v5/MAIN/agent\subagent\spawn.py:83:        max_turns=max_turns,
compact_v5/MAIN/agent\subagent\spawn.py:93:    Returns None for unknown types so the caller (spawn_subagent / task tool)
compact_v5/MAIN/agent\subagent\spawn.py:100:    from .agent_types import get_agent_type
compact_v5/MAIN/agent\subagent\spawn.py:110:    max_turns: int = 25,
compact_v5/MAIN/agent\subagent\spawn.py:120:    """Spawn a sub-agent with the parent's shared IterationBudget.
compact_v5/MAIN/agent\subagent\spawn.py:124:      - The parent's BedrockClient, IterationBudget, on_stop_check (shared).
compact_v5/MAIN/agent\subagent\spawn.py:162:    # Validate agent type. The task tool already gates on this at the
compact_v5/MAIN/agent\subagent\spawn.py:168:        from .agent_types import AGENT_TYPES
compact_v5/MAIN/agent\subagent\spawn.py:181:    # Block G — resolve the AgentType row for per-type max_turns / worktree
compact_v5/MAIN/agent\subagent\spawn.py:183:    from .agent_types import get_agent_type
compact_v5/MAIN/agent\subagent\spawn.py:186:        # Per-type max_turns: caller can override via the max_turns param.
compact_v5/MAIN/agent\subagent\spawn.py:188:        # something smaller (defense in depth — caller knows the task).
compact_v5/MAIN/agent\subagent\spawn.py:189:        max_turns = min(max_turns, agent_def.max_turns)
compact_v5/MAIN/agent\subagent\spawn.py:227:    child = _new_child_engine(parent_engine, max_turns=max_turns, agent_type=agent_type)
compact_v5/MAIN/agent\subagent\spawn.py:230:    # IF the child itself dispatches `task`, the QueryEngine's tool-dispatch
compact_v5/MAIN/agent\subagent\spawn.py:233:    # `task` chains all see parent_depth=0 and the recursion guard never
compact_v5/MAIN/agent\subagent\spawn.py:246:    # specialized agents (explore/plan/verify/review) get a tool allowlist
compact_v5/MAIN/agent\subagent\spawn.py:252:    # `task` tool for restricted agents. Otherwise a read-only explore agent
compact_v5/MAIN/agent\subagent\spawn.py:253:    # could call task(subagent_type="build") and regain mutating tools via
compact_v5/MAIN/agent\subagent\spawn.py:265:        # task is NOT auto-included — restricted agents stay restricted.
compact_v5/MAIN/agent\subagent\env.py:36:        agent_type: e.g. 'general' / 'build' / 'plan' / 'explore' / 'verify'.
compact_v5/MAIN/agent\ui\chat_ui.py:5:2. Constructs `IterationBudgetWidget` + `ThinkingBudgetWidget`.
compact_v5/MAIN/agent\ui\chat_ui.py:86:from .widgets import IterationBudgetWidget, ThinkingBudgetWidget, _IPYWIDGETS_OK
compact_v5/MAIN/agent\ui\chat_ui.py:99:        self.budget_widget = IterationBudgetWidget(budget=agent.budget)
compact_v5/MAIN/agent\ui\chat_ui.py:190:        self.budget_widget = IterationBudgetWidget(budget=agent.budget)
compact_v5/MAIN/agent\ui\chat_ui.py:294:        from core import IterationBudget
compact_v5/MAIN/agent\ui\chat_ui.py:304:        # Codex Phase-11 finding (high): thread CONFIG.max_turns +
compact_v5/MAIN/agent\ui\chat_ui.py:308:        max_turns = int(getattr(CONFIG, "max_turns", 50))
compact_v5/MAIN/agent\ui\chat_ui.py:309:        budget_max = int(getattr(CONFIG, "max_iteration_budget", IterationBudget.DEFAULT_MAX))
compact_v5/MAIN/agent\ui\chat_ui.py:312:            max_turns=max_turns,
compact_v5/MAIN/agent\ui\chat_ui.py:313:            budget=IterationBudget(max_iterations=budget_max),
compact_v5/MAIN/agent\subagent\agent_types.py:1:"""V5 subagent/agent_types.py — Block G AGENT_TYPES registry.
compact_v5/MAIN/agent\subagent\agent_types.py:12:  prompt. Sets task-shape expectations.
compact_v5/MAIN/agent\subagent\agent_types.py:13:- max_turns: ceiling on the sub-agent's turn count (independent of the
compact_v5/MAIN/agent\subagent\agent_types.py:14:  shared IterationBudget, which is the cost-cap; max_turns is the
compact_v5/MAIN/agent\subagent\agent_types.py:15:  task-scope-cap).
compact_v5/MAIN/agent\subagent\agent_types.py:39:    "You are a sub-agent working on a focused task. Always use ABSOLUTE "
compact_v5/MAIN/agent\subagent\agent_types.py:43:    "refactor, or introduce abstractions beyond what the task requires."
compact_v5/MAIN/agent\subagent\agent_types.py:53:    "- When you launch multiple research tasks, run them in parallel.\n"
compact_v5/MAIN/agent\subagent\agent_types.py:63:    max_turns: int = 25
compact_v5/MAIN/agent\subagent\agent_types.py:74:# Read-only tool allowlist for explore / plan / review (no file mutation,
compact_v5/MAIN/agent\subagent\agent_types.py:85:# Block G-1: AGENT_TYPES dict — 7 entries per TEST_DESIGN test_agent_types_dict_has_7.
compact_v5/MAIN/agent\subagent\agent_types.py:92:    "explore": AgentType(
compact_v5/MAIN/agent\subagent\agent_types.py:93:        name="explore",
compact_v5/MAIN/agent\subagent\agent_types.py:101:        max_turns=20,
compact_v5/MAIN/agent\subagent\agent_types.py:114:        max_turns=15,
compact_v5/MAIN/agent\subagent\agent_types.py:127:        max_turns=20,
compact_v5/MAIN/agent\subagent\agent_types.py:142:        max_turns=40,
compact_v5/MAIN/agent\subagent\agent_types.py:154:        max_turns=20,
compact_v5/MAIN/agent\subagent\agent_types.py:162:            + "\n\nFocus: continue the parent's task in a forked context. "
compact_v5/MAIN/agent\subagent\agent_types.py:164:            "the parent left off and complete the task."
compact_v5/MAIN/agent\subagent\agent_types.py:167:        max_turns=50,
compact_v5/MAIN/agent\runtime\tokens.py:313:    (default "parent"; sub-agents pass "build", "explore", "verify",
compact_v5/MAIN/agent\runtime\tokens.py:383:        agent loop; sub-agent type-strings ("build", "explore", "verify",
compact_v5/MAIN/agent\security\high_risk.py:18:# v4 verbatim: bash + python_exec are subprocess-launching, task is
compact_v5/MAIN/agent\security\high_risk.py:25:    "task",
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:4:  Validates Block G3 (coordinator-mode prompt) + Phase 9 task tool
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:6:    - Parent receives a coding-survey task across 3 small Python files.
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:7:    - Parent dispatches 3 sub-agents (subagent_type='explore'),
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:13:Note on "parallel": v5's task tool is `is_concurrency_safe=False` —
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:22:  - All 3 dispatches are agent_type='explore'.
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:24:  - Parent stop_reason != max_turns.
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:105:    "1. Spawn THREE sub-agents using the `task` tool, ONE PER FILE. Use "
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:106:    "subagent_type='explore' for each (read-only is sufficient).\n"
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:131:      - audit_log records >= 3 task-tool dispatches with subagent_type='explore'.
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:134:      - parent stop_reason != max_turns.
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:201:            max_turns=18,  # parent budget — children share IterationBudget
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:205:        # Pre-promote `task` + `write_file` from deferred → visible so the
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:209:        agent._engine._discovered_tool_names = {"task", "write_file"}
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:224:        # and filter for tool_name == 'task'.
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:225:        task_dispatches: list = []
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:234:                if e.get("tool_name") == "task" and e.get("action") == "tool_dispatch":
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:235:                    task_dispatches.append(e)
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:237:        explore_dispatches = [
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:238:            d for d in task_dispatches
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:239:            if (d.get("parameters") or {}).get("subagent_type") == "explore"
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:261:            "task_dispatches": len(task_dispatches),
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:262:            "explore_dispatches": len(explore_dispatches),
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:279:        assert result.stop_reason != "max_turns", (
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:280:            f"R3 parent hit max_turns (18); incomplete. metrics={metrics}"
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:285:        assert len(task_dispatches) >= 3, (
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:286:            f"R3 expected >=3 task-tool dispatches; got "
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:287:            f"{len(task_dispatches)}. metrics={metrics}"
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:289:        assert len(explore_dispatches) >= 3, (
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:290:            f"R3 expected >=3 dispatches with subagent_type='explore'; "
compact_v5/MAIN/agent\tests\r_tier\test_r3_three_subagents.py:291:            f"got {len(explore_dispatches)}. metrics={metrics}"
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:90:      - Agent completed (not max_turns or stopped on error).
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:157:            max_turns=50,
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:198:        assert result.stop_reason != "max_turns", (
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:199:            f"R1 hit max_turns (50); incomplete. metrics={metrics}"
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:145:            max_turns=4,
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:244:        assert result_t1.stop_reason != "max_turns", (
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:245:            f"R2 turn 1 hit max_turns. metrics={metrics}"
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:56:      - Agent run completes (not max_turns).
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:98:            max_turns=8,
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:103:        # Pre-empt any ask_user (single-turn task; auto-respond if the
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:151:        assert result.stop_reason != "max_turns", (
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:152:            f"R17 hit max_turns; thinking did not converge. metrics={metrics}"
compact_v5/MAIN/agent\tests\unit\test_prompt_assembly.py:129:    prompt = build_system_prompt({"dynamic_blocks": ["[TODO RESTORATION]\n- task 1\n- task 2"]})
compact_v5/MAIN/agent\tests\unit\test_registry.py:181:    Mutating tools (write_file, edit_file, bash, python_exec, task) are
compact_v5/MAIN/agent\tests\unit\test_security_manager.py:286:    assert HIGH_RISK_TOOLS == frozenset({"bash", "python_exec", "task", "web_fetch"})
compact_v5/MAIN/agent\tools\bash.py:11:  attribution, background-task notes, sandbox manager refs, multi-USER_TYPE
compact_v5/MAIN/agent\tools\grep.py:41:- ALWAYS use grep for search tasks. NEVER invoke `grep` or `rg` via bash — this dedicated tool has correct permissions and the right defaults.
compact_v5/MAIN/agent\tools\grep.py:45:- Use the task tool for open-ended searches that need multiple rounds of grep+glob.
compact_v5/MAIN/agent\tests\unit\test_subagent_env.py:29:    out = build_env_details(agent_type="explore", depth=2, workspace="/tmp/foo")
compact_v5/MAIN/agent\tests\unit\test_budget.py:1:"""Phase 08 unit tests: core/budget.py — IterationBudget.
compact_v5/MAIN/agent\tests\unit\test_budget.py:3:Locks PORT_LOG #016: verbatim port of v4's IterationBudget (Hermes pattern).
compact_v5/MAIN/agent\tests\unit\test_budget.py:17:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\unit\test_budget.py:18:    b = IterationBudget()
compact_v5/MAIN/agent\tests\unit\test_budget.py:23:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\unit\test_budget.py:24:    b = IterationBudget(max_iterations=3)
compact_v5/MAIN/agent\tests\unit\test_budget.py:32:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\unit\test_budget.py:33:    b = IterationBudget(max_iterations=2)
compact_v5/MAIN/agent\tests\unit\test_budget.py:44:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\unit\test_budget.py:45:    b = IterationBudget(max_iterations=0)
compact_v5/MAIN/agent\tests\unit\test_budget.py:52:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\unit\test_budget.py:53:    b = IterationBudget(max_iterations=2)
compact_v5/MAIN/agent\tests\unit\test_budget.py:65:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\unit\test_budget.py:66:    b = IterationBudget(max_iterations=1000)
compact_v5/MAIN/agent\tests\unit\test_budget.py:91:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\unit\test_budget.py:92:    parent = IterationBudget(max_iterations=10)
compact_v5/MAIN/agent\tools\glob.py:44:- Open-ended exploration requiring multiple rounds → use the task tool with explore type"""
compact_v5/MAIN/agent\tests\aggregate_audit.py:8:- Skill count: = 10 (Phase 10 task; not enforced before Phase 10).
compact_v5/MAIN/agent\tests\integration\test_agent_max_tokens_propagation.py:57:        agent = Agent(client=_SpyClient(), max_turns=1)
compact_v5/MAIN/agent\tests\integration\test_agent_max_tokens_propagation.py:92:        agent = Agent(client=_SpyClient(), max_turns=1)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:21:  10. Sub-agent shares parent IterationBudget (Phase 9 contract)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:26:  15. PS Issue #2 (visible IterationBudget) + PS Issue #4 (visible thinking)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:128:    eng = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:156:    eng = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:229:    eng = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:239:# 10 — Sub-agent shares parent IterationBudget (Phase 9 contract)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:244:    from core import IterationBudget
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:249:    parent = Agent(client=client, budget=IterationBudget(max_iterations=20))
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:307:    eng = QueryEngine(client=_OverflowClient(), max_turns=3)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:333:    eng = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:346:    from core import IterationBudget
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:348:    from ui.widgets import IterationBudgetWidget, ThinkingBudgetWidget
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:351:    a = Agent(client=client, budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:353:    bw = IterationBudgetWidget(budget=a.budget)
compact_v5/MAIN/agent\tools\registry.py:44:# tools (write_file, edit_file, bash, python_exec, notebook_edit, task)
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:132:    from core import IterationBudget
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:133:    from ui.widgets import IterationBudgetWidget
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:134:    w = IterationBudgetWidget(budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:145:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:148:    parent = QueryEngine(client=None, max_turns=1, budget=IterationBudget())
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:175:    eng = QueryEngine(client=_C(), max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:448:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:238:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:264:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:152:    TOKENS.add({"input_tokens": 60, "output_tokens": 30}, model_id="test-model", agent_kind="explore")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:159:    assert TOKENS.subagent_input_tokens["explore"] == 60
compact_v5/MAIN/agent\tests\integration\test_block_b.py:160:    assert TOKENS.subagent_output_tokens["explore"] == 30
compact_v5/MAIN/agent\tests\integration\test_block_b.py:518:    engine = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:575:    engine = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:625:    engine = QueryEngine(client=client, max_turns=1)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:702:    CONFIG.max_turns reflects the validated value."""
compact_v5/MAIN/agent\tests\integration\test_block_b.py:710:        assert config_mod.CONFIG.max_turns == 42, (
compact_v5/MAIN/agent\tests\integration\test_block_b.py:711:            f"env-validated max_turns must be 42; got {config_mod.CONFIG.max_turns}"
compact_v5/MAIN/agent\tests\integration\test_block_b.py:730:        assert config_mod.CONFIG.max_turns == 10_000, (
compact_v5/MAIN/agent\tests\integration\test_block_b.py:731:            f"out-of-range max_turns must clamp to maximum 10_000; got "
compact_v5/MAIN/agent\tests\integration\test_block_b.py:732:            f"{config_mod.CONFIG.max_turns}"
compact_v5/MAIN/agent\tools\skill.py:38:- The task matches a methodology bundle (e.g. user asks for adversarial verification → activate `verify`).
compact_v5/MAIN/agent\tests\integration\test_block_c.py:61:    engine = QueryEngine(client=client, max_turns=10)
compact_v5/MAIN/agent\tests\integration\test_block_c.py:120:    engine = QueryEngine(client=client, max_turns=10)
compact_v5/MAIN/agent\tests\integration\test_block_c.py:470:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:289:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:370:    engine = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tools\task.py:1:"""Phase 9 task tool — sub-agent dispatch (Phase 9, ADR-015).
compact_v5/MAIN/agent\tools\task.py:7:- v4 `_run_task_tool` at sagemaker_agent.py:8350 — the executor logic.
compact_v5/MAIN/agent\tools\task.py:13:- subagent_type values: "general" only. Future phases add build/plan/explore/verify.
compact_v5/MAIN/agent\tools\task.py:23:the parent's IterationBudget — see acceptance test
compact_v5/MAIN/agent\tools\task.py:33:_DESCRIPTION = """Launch a sub-agent for a specific, scoped task.
compact_v5/MAIN/agent\tools\task.py:36:- The task is well-scoped and self-contained (e.g., "summarize this codebase", "find every TODO comment").
compact_v5/MAIN/agent\tools\task.py:41:- The task is small enough to do directly in the current turn.
compact_v5/MAIN/agent\tools\task.py:47:- prompt: the actual task description for the sub-agent. Be specific.
compact_v5/MAIN/agent\tools\task.py:48:- subagent_type: one of `general` | `explore` | `plan` | `verify` | `build` | `review` | `fork` (default `general`).
compact_v5/MAIN/agent\tools\task.py:50:  - `explore` — read-only exploration (no edit/write/exec); produces a report.
compact_v5/MAIN/agent\tools\task.py:57:Returns the sub-agent's final answer as a string. If the sub-agent hits its iteration budget or max_turns, the partial work + reason is returned."""
compact_v5/MAIN/agent\tools\task.py:69:            "description": "Full task description sent to the sub-agent. Be specific — the sub-agent has no parent context unless you brief it.",
compact_v5/MAIN/agent\tools\task.py:73:            "enum": ["general", "explore", "plan", "verify", "build", "review", "fork"],
compact_v5/MAIN/agent\tools\task.py:75:            "description": "Agent type. general (default; full tools) | explore (read-only) | plan (read-only) | verify (read + bash + auto-loads verify skill) | build (full + isolated git worktree) | review (read-only code review) | fork (full tools, parent-context).",
compact_v5/MAIN/agent\tools\task.py:82:def _task_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
compact_v5/MAIN/agent\tools\task.py:87:        IterationBudget, (b) reuse the BedrockClient, (c) inherit on_stop_check.
compact_v5/MAIN/agent\tools\task.py:102:    # (build / plan / explore / verify / general / review / fork) — was
compact_v5/MAIN/agent\tools\task.py:104:    from subagent.agent_types import AGENT_TYPES
compact_v5/MAIN/agent\tools\task.py:114:            "Error: task tool requires `context['parent_engine']` to spawn a "
compact_v5/MAIN/agent\tools\task.py:136:    if result.stop_reason in ("budget_exhausted", "max_turns", "context_overflow"):
compact_v5/MAIN/agent\tools\task.py:148:    if find_tool_by_name(all_registered(), "task") is not None:
compact_v5/MAIN/agent\tools\task.py:152:        name="task",
compact_v5/MAIN/agent\tools\task.py:155:        execute=_task_executor,
compact_v5/MAIN/agent\tools\task.py:162:        search_hint="sub-agent fork delegate spawn task launch background",
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:4:Adapted to v5's IterationBudget surface (NEEDS-ADAPTATION verdict).
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:216:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:227:        budget = IterationBudget(max_iterations=2)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:228:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:253:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:266:        budget = IterationBudget(max_iterations=1)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:267:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:286:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:302:        budget = IterationBudget(max_iterations=100)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:303:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:327:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:337:    budget = IterationBudget(max_iterations=1000)  # 0.1% used after 1 turn
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:338:    engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:354:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:372:        budget = IterationBudget(max_iterations=100)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:373:        engine = QueryEngine(client=client, max_turns=10, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:388:    """Sub-agents inherit the IterationBudget but NOT the F2 auto-continue
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:391:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:401:        budget = IterationBudget(max_iterations=1000)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:403:            client=client, max_turns=5, budget=budget,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:404:            agent_kind="explore",  # any non-"parent" string flags subagent
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:431:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:448:        budget = IterationBudget(max_iterations=100)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:449:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:482:    the IterationBudget surface that the rest of run() relies on.
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:486:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:506:        budget = IterationBudget(max_iterations=100)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:507:        engine = QueryEngine(client=client, max_turns=2, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:654:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:666:        budget = IterationBudget(max_iterations=2)  # 2 turns then above_threshold
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:667:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_g.py:11:- test_agent_types_dict_has_7
compact_v5/MAIN/agent\tests\integration\test_block_g.py:72:def test_agent_types_dict_has_7():
compact_v5/MAIN/agent\tests\integration\test_block_g.py:73:    """AGENT_TYPES.keys() == {build, plan, explore, verify, general, review, fork}."""
compact_v5/MAIN/agent\tests\integration\test_block_g.py:76:    expected = {"build", "plan", "explore", "verify", "general", "review", "fork"}
compact_v5/MAIN/agent\tests\integration\test_block_g.py:81:def test_one_shot_builtin_agent_types_has_explore_plan_verify_review():
compact_v5/MAIN/agent\tests\integration\test_block_g.py:86:    # Per agent_types.py: explore, plan, verify, review are one-shot.
compact_v5/MAIN/agent\tests\integration\test_block_g.py:88:    assert "explore" in ONE_SHOT_BUILTIN_AGENT_TYPES
compact_v5/MAIN/agent\tests\integration\test_block_g.py:102:    """task(subagent_type=\"build\") creates worktrees/<id>/ (mocked git)."""
compact_v5/MAIN/agent\tests\integration\test_block_g.py:104:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:112:    parent = QueryEngine(client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:113:                         budget=IterationBudget(max_iterations=20))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:139:    """task(subagent_type=\"verify\") loads verify skill in sub-agent context.
compact_v5/MAIN/agent\tests\integration\test_block_g.py:146:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:165:        client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:166:        budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_block_g.py:238:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:242:    parent = QueryEngine(client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:243:                         budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:264:# TEST_DESIGN row 7 — IterationBudget shared object identity
compact_v5/MAIN/agent\tests\integration\test_block_g.py:268:    """parent and sub-agent share SAME IterationBudget object."""
compact_v5/MAIN/agent\tests\integration\test_block_g.py:270:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:273:    parent_budget = IterationBudget(max_iterations=10)
compact_v5/MAIN/agent\tests\integration\test_block_g.py:274:    parent = QueryEngine(client=_ScriptedClient([]), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:276:    child = _new_child_engine(parent, max_turns=5, agent_type="general")
compact_v5/MAIN/agent\tests\integration\test_block_g.py:289:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:296:    parent = QueryEngine(client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:297:                         budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:327:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:330:    parent = QueryEngine(client=_ScriptedClient([]), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:331:                         budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:343:    from subagent.agent_types import get_agent_prompt, SUBAGENT_NOTES
compact_v5/MAIN/agent\tests\integration\test_block_g.py:354:    from subagent.agent_types import DEFAULT_AGENT_PROMPT
compact_v5/MAIN/agent\tests\integration\test_block_g.py:373:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:401:        parent = QueryEngine(client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:402:                             budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:425:def test_explore_agent_tool_allowlist_excludes_mutators():
compact_v5/MAIN/agent\tests\integration\test_block_g.py:426:    """Codex iter-1 finding #2 HIGH lock: explore agent gets a read-only
compact_v5/MAIN/agent\tests\integration\test_block_g.py:432:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:446:            return Response(text="explored", tool_calls=[],
compact_v5/MAIN/agent\tests\integration\test_block_g.py:449:    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:450:                         budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:451:    spawn_subagent(parent, "explore x", agent_type="explore")
compact_v5/MAIN/agent\tests\integration\test_block_g.py:456:            f"explore agent must NOT see '{forbidden}' (Codex iter-1 #2)"
compact_v5/MAIN/agent\tests\integration\test_block_g.py:461:            f"explore agent must see '{required}'"
compact_v5/MAIN/agent\tests\integration\test_block_g.py:466:    """plan agent: same read-only allowlist as explore."""
compact_v5/MAIN/agent\tests\integration\test_block_g.py:468:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:485:    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:486:                         budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:497:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:520:        parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:521:                             budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_block_g.py:549:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:567:    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:568:                         budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:585:    # call sees post-deferral), but we verify by spawning an explore agent
compact_v5/MAIN/agent\tests\integration\test_block_g.py:587:    # explore's `task` is NOT in names — done in
compact_v5/MAIN/agent\tests\integration\test_block_g.py:588:    # test_restricted_agents_cannot_spawn_via_task below.
compact_v5/MAIN/agent\tests\integration\test_block_g.py:591:def test_restricted_agents_cannot_spawn_via_task(tmp_path):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:593:    (explore/plan/review) and verify must NOT have access to the `task`
compact_v5/MAIN/agent\tests\integration\test_block_g.py:594:    tool. Otherwise an explore agent could call task(subagent_type=
compact_v5/MAIN/agent\tests\integration\test_block_g.py:601:    + agent_types: assert task is NOT in the AgentType.allowed_tools
compact_v5/MAIN/agent\tests\integration\test_block_g.py:604:    from subagent.agent_types import AGENT_TYPES
compact_v5/MAIN/agent\tests\integration\test_block_g.py:606:    for restricted in ("explore", "plan", "verify", "review"):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:611:        assert "task" not in at.allowed_tools, (
compact_v5/MAIN/agent\tests\integration\test_block_g.py:612:            f"{restricted} agent must NOT have `task` in its allowlist "
compact_v5/MAIN/agent\tests\integration\test_block_g.py:615:            "says task is NOT auto-included for restricted agents."
compact_v5/MAIN/agent\tests\integration\test_block_g.py:618:    # Conversely, unrestricted agents (general/build/fork) DO get task
compact_v5/MAIN/agent\tests\integration\test_block_g.py:627:def test_explore_child_tools_excludes_task():
compact_v5/MAIN/agent\tests\integration\test_block_g.py:628:    """End-to-end lock for Codex iter-2 #1: spawn an explore child and
compact_v5/MAIN/agent\tests\integration\test_block_g.py:629:    assert the chat() tools arg does NOT include 'task'."""
compact_v5/MAIN/agent\tests\integration\test_block_g.py:631:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:648:    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:649:                         budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:650:    spawn_subagent(parent, "x", agent_type="explore")
compact_v5/MAIN/agent\tests\integration\test_block_g.py:652:    assert "task" not in names, (
compact_v5/MAIN/agent\tests\integration\test_block_g.py:653:        "explore agent must not see `task` (would regain mutators via build child)"
compact_v5/MAIN/agent\tests\integration\test_block_g.py:659:def test_task_tool_schema_lists_all_7_agent_types():
compact_v5/MAIN/agent\tests\integration\test_block_g.py:660:    """Codex iter-1 finding #3 MEDIUM lock: tools/task.py JSON schema
compact_v5/MAIN/agent\tests\integration\test_block_g.py:666:    task_tool = next((t for t in all_registered() if t.name == "task"), None)
compact_v5/MAIN/agent\tests\integration\test_block_g.py:667:    assert task_tool is not None
compact_v5/MAIN/agent\tests\integration\test_block_g.py:668:    schema = task_tool.input_schema
compact_v5/MAIN/agent\tests\integration\test_block_g.py:671:        f"task tool subagent_type enum {set(enum)} must == AGENT_TYPES.keys() "
compact_v5/MAIN/agent\tests\integration\test_block_g.py:676:    for at in ("explore", "plan", "verify", "build"):
compact_v5/MAIN/agent\tests\integration\test_block_g.py:677:        assert at in desc, f"task tool subagent_type description must mention {at!r}"
compact_v5/MAIN/agent\tests\integration\test_block_g.py:680:def test_agent_max_turns_clamped_by_per_type_ceiling():
compact_v5/MAIN/agent\tests\integration\test_block_g.py:681:    """spawn_subagent clamps max_turns to min(caller-supplied, agent_type ceiling)."""
compact_v5/MAIN/agent\tests\integration\test_block_g.py:683:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g.py:685:    from subagent.agent_types import AGENT_TYPES
compact_v5/MAIN/agent\tests\integration\test_block_g.py:687:    # explore.max_turns = 20; pass 100 to spawn — should clamp to 20.
compact_v5/MAIN/agent\tests\integration\test_block_g.py:689:    parent = QueryEngine(client=client, max_turns=200,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:690:                         budget=IterationBudget(max_iterations=200))
compact_v5/MAIN/agent\tests\integration\test_block_g.py:692:    # We can't easily inspect the child's max_turns post-completion, but we
compact_v5/MAIN/agent\tests\integration\test_block_g.py:695:    # spawn_subagent passes the resolved max_turns into _new_child_engine.
compact_v5/MAIN/agent\tests\integration\test_block_g.py:697:        parent_engine=parent, prompt="x", agent_type="explore",
compact_v5/MAIN/agent\tests\integration\test_block_g.py:698:        max_turns=100,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:701:    # explore.max_turns = 20 ceiling — even though caller asked for 100.
compact_v5/MAIN/agent\tests\integration\test_block_g.py:702:    assert AGENT_TYPES["explore"].max_turns == 20
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:68:    # Phase-transition / explore-findings-need-implementation row.
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:83:    """Prompt contains 'Read-only tasks: run in parallel; Write tasks:
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:89:    assert "Read-only tasks: run in parallel" in prompt
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:90:    assert "Write tasks: one at a time" in prompt
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:123:    assert "explore" in ctx and "build" in ctx and "verify" in ctx
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:160:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:181:        parent = QueryEngine(client=_SnoopClient(), max_turns=2,
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:182:                             budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:195:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:216:        parent = QueryEngine(client=_SnoopClient(), max_turns=2,
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:217:                             budget=IterationBudget(max_iterations=10))
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:237:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:274:            client=_SnoopClient(), max_turns=2,
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:275:            budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:320:    # NOT show a cross-type transition (e.g. explore→build). Cross-type
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:332:        # Reject any cross-type arrow (explore→build, build→verify, etc.).
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:334:            r"\b(explore|plan|verify|build|review|general|fork)→(?!\1\b)"
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:335:            r"(explore|plan|verify|build|review|general|fork)\b",
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:352:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:374:            client=_SnoopClient(), max_turns=2,
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:375:            budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:402:        # Per get_coordinator_user_context: lists explore/plan/verify/build.
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:403:        for at in ("explore", "build", "verify"):
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:413:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:434:        # agent_kind="explore" simulates a sub-agent.
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:436:            client=_SnoopClient(), max_turns=2,
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:437:            budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:438:            agent_kind="explore",
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:440:        child.run(user_message="explore x", system_prompt="base",
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:453:        assert "explore x" in joined
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:475:    from core.budget import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:496:        # agent_kind="explore" simulates a sub-agent.
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:498:            client=_SnoopClient(), max_turns=2,
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:499:            budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:500:            agent_kind="explore",
compact_v5/MAIN/agent\tests\integration\test_block_g2.py:31:    the typical pre-fork state where the model is mid-task."""
compact_v5/MAIN/agent\tests\integration\test_block_h.py:265:        {"role": "user", "content": "task"},
compact_v5/MAIN/agent\tests\integration\test_block_h.py:391:      [0] user "task"
compact_v5/MAIN/agent\tests\integration\test_block_h.py:410:        {"role": "user", "content": "task"},  # 0
compact_v5/MAIN/agent\tests\integration\test_block_h_plus.py:128:    """v5 codebase has no daemon / asyncio.create_task / atexit.register
compact_v5/MAIN/agent\tests\integration\test_block_h_plus.py:139:        re.compile(r"asyncio\.create_task\([^)]*[Dd]ream"),
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:328:    agent = Agent(client=client, max_turns=3)
compact_v5/MAIN/agent\tools\__init__.py:61:# Phase 9 — task tool (sub-agent dispatch, ADR-015):
compact_v5/MAIN/agent\tools\__init__.py:62:from . import task as _task                   # noqa: F401  defines _register()
compact_v5/MAIN/agent\tools\__init__.py:105:    # Phase 9 — task tool (sub-agent dispatch)
compact_v5/MAIN/agent\tools\__init__.py:106:    _task._register()
compact_v5/MAIN/agent\tests\integration\test_block_m.py:173:    engine = QueryEngine(client=client, max_turns=2, skill_manager=sm)
compact_v5/MAIN/agent\tests\integration\test_block_m.py:206:        max_turns=10,
compact_v5/MAIN/agent\tests\integration\test_block_m.py:229:    continue until max_turns, wasting tokens.
compact_v5/MAIN/agent\tests\integration\test_block_m.py:246:        max_turns=20,
compact_v5/MAIN/agent\tests\integration\test_block_m.py:256:    # max_turns=20 was NOT hit — the retry-limit guard fired first.
compact_v5/MAIN/agent\tests\integration\test_block_m.py:276:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_block_m.py:323:        client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:203:    """Aggregator filters compact + task (subagent dispatch) events
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:214:         "tool_name": "task",
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:215:         "parameters": {"subagent_type": "explore", "description": "find auth"},
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:228:    assert telemetry["subagent_dispatches"][0]["agent_type"] == "explore"
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:87:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:111:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:140:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:152:    # Phase 9 added `task` tool with should_defer=True — must also be excluded.
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:153:    assert "task" not in sent_names
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:184:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:207:# Test 5 — IterationBudget gate stops the loop
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:212:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:215:    budget = IterationBudget(max_iterations=2)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:220:    engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:232:# Test 6 — max_turns cap
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:235:def test_engine_stops_at_max_turns():
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:236:    """If model never returns end_turn, the loop must exit cleanly at max_turns."""
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:246:    engine = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:252:    assert result.stop_reason == "max_turns"
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:268:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:304:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:326:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:362:    engine = QueryEngine(client=OverflowClient(), max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:405:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:444:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:479:    engine = QueryEngine(client=client_run1, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:11:- IterationBudgetWidget tracks consumption after run
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:50:    assert hasattr(entry, "IterationBudget")
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:85:    assert result.stop_reason in ("end_turn", "tool_use", "max_turns")
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:177:# Test 5 — IterationBudgetWidget tracks consumption (PS Issue #2)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:181:    from ui.widgets import IterationBudgetWidget
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:182:    from core import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:184:    b = IterationBudget(max_iterations=10)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:185:    w = IterationBudgetWidget(budget=b)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:196:    from ui.widgets import IterationBudgetWidget
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:197:    from core import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:199:    w = IterationBudgetWidget(budget=IterationBudget(max_iterations=5))
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:257:def test_lazy_factory_threads_max_turns_and_budget(monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:259:    `CONFIG.max_turns` + `CONFIG.max_iteration_budget` and pass them to
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:265:    monkeypatch.setattr(CONFIG, "max_turns", 7)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:269:    assert ui.agent._engine.max_turns == 7
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:302:    from core import IterationBudget
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:305:    from ui.widgets import IterationBudgetWidget
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:308:    parent = Agent(client=client, budget=IterationBudget(max_iterations=20))
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:309:    widget = IterationBudgetWidget(budget=parent.budget)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:1:"""Phase 09 integration tests: subagent/spawn.py + tools/task.py.
compact_v5/MAIN/agent\tests\integration\test_subagent.py:5:- Child shares IterationBudget instance.
compact_v5/MAIN/agent\tests\integration\test_subagent.py:7:Locks PORT_LOG #021 (forkSubagent budget sharing) + #024 (task tool dispatch).
compact_v5/MAIN/agent\tests\integration\test_subagent.py:59:# Test 1 — child shares IterationBudget (Phase 9 ACCEPTANCE)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:66:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:69:    parent_budget = IterationBudget(max_iterations=20)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:72:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:75:    child = _new_child_engine(parent, max_turns=10)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:89:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:94:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:95:        budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:121:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:125:    parent = QueryEngine(client=client, max_turns=5, budget=IterationBudget())
compact_v5/MAIN/agent\tests\integration\test_subagent.py:146:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:151:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:152:        budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:165:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:168:    budget = IterationBudget(max_iterations=10)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:174:    parent = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:188:# Test 6 — task tool registered + deferred
compact_v5/MAIN/agent\tests\integration\test_subagent.py:191:def test_task_tool_registered_and_deferred():
compact_v5/MAIN/agent\tests\integration\test_subagent.py:194:    tool = find_tool_by_name(all_registered(), "task")
compact_v5/MAIN/agent\tests\integration\test_subagent.py:202:    assert "task" not in visible_names
compact_v5/MAIN/agent\tests\integration\test_subagent.py:203:    assert "task" in deferred_names
compact_v5/MAIN/agent\tests\integration\test_subagent.py:207:# Test 7 — task tool executor requires parent_engine in context
compact_v5/MAIN/agent\tests\integration\test_subagent.py:210:def test_task_tool_requires_parent_engine_in_context():
compact_v5/MAIN/agent\tests\integration\test_subagent.py:213:    task_tool = find_tool_by_name(all_registered(), "task")
compact_v5/MAIN/agent\tests\integration\test_subagent.py:214:    out = task_tool.execute({"prompt": "do a thing"}, context={})
compact_v5/MAIN/agent\tests\integration\test_subagent.py:220:# Test 8 — task tool executor with parent_engine spawns sub-agent
compact_v5/MAIN/agent\tests\integration\test_subagent.py:223:def test_task_tool_executor_spawns_subagent():
compact_v5/MAIN/agent\tests\integration\test_subagent.py:224:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:229:        max_turns=3,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:230:        budget=IterationBudget(max_iterations=5),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:232:    task_tool = find_tool_by_name(all_registered(), "task")
compact_v5/MAIN/agent\tests\integration\test_subagent.py:233:    out = task_tool.execute(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:241:# Test 9 — task tool surfaces budget exhaustion partial output
compact_v5/MAIN/agent\tests\integration\test_subagent.py:244:def test_task_tool_surfaces_budget_exhaustion():
compact_v5/MAIN/agent\tests\integration\test_subagent.py:245:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:249:    budget = IterationBudget(max_iterations=1)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:253:        max_turns=3,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:256:    task_tool = find_tool_by_name(all_registered(), "task")
compact_v5/MAIN/agent\tests\integration\test_subagent.py:257:    out = task_tool.execute(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:265:# Test 10 — end-to-end via QueryEngine: model calls task tool
compact_v5/MAIN/agent\tests\integration\test_subagent.py:268:def test_query_engine_dispatches_task_tool_end_to_end():
compact_v5/MAIN/agent\tests\integration\test_subagent.py:269:    """Model in turn 1 calls `task`. The QueryEngine dispatches it; the task
compact_v5/MAIN/agent\tests\integration\test_subagent.py:272:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:275:    # Parent client: turn 1 = call task tool, turn 2 = give final.
compact_v5/MAIN/agent\tests\integration\test_subagent.py:282:        ("tool", "p1", "task", {"prompt": "child task: count files"}),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:290:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:291:        budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:312:    that a child dispatching `task` itself triggers the recursion guard at
compact_v5/MAIN/agent\tests\integration\test_subagent.py:314:    spawn_subagent, every nested `task` would reset to depth 0 and unbounded
compact_v5/MAIN/agent\tests\integration\test_subagent.py:316:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:321:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:322:        budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:333:    # Now simulate the child running and dispatching `task`. We don't need
compact_v5/MAIN/agent\tests\integration\test_subagent.py:338:    child = _new_child_engine(parent, max_turns=10)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:348:    """End-to-end nested-spawn lock: a CHILD engine passing through `task`
compact_v5/MAIN/agent\tests\integration\test_subagent.py:357:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:362:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:363:        budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:375:    # reflects A's depth. Simulate what the task tool dispatch would
compact_v5/MAIN/agent\tests\integration\test_subagent.py:380:    a_engine = _new_child_engine(parent, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:405:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:410:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:411:        budget=IterationBudget(max_iterations=10),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:417:    def capturing_factory(p, max_turns, agent_type="general"):
compact_v5/MAIN/agent\tests\integration\test_subagent.py:418:        c = real_factory(p, max_turns, agent_type=agent_type)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:440:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:445:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:446:        budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:465:    monkeypatch.setattr(spawn_mod, "_new_child_engine", lambda p, max_turns, agent_type="general": _MutatorChild(p))
compact_v5/MAIN/agent\tests\integration\test_subagent.py:478:def test_task_tool_rejects_unknown_subagent_type():
compact_v5/MAIN/agent\tests\integration\test_subagent.py:482:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:487:        max_turns=3,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:488:        budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:490:    task_tool = find_tool_by_name(all_registered(), "task")
compact_v5/MAIN/agent\tests\integration\test_subagent.py:491:    out = task_tool.execute(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:504:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:509:        max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_subagent.py:510:        budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:528:    monkeypatch.setattr(spawn_mod, "_new_child_engine", lambda p, max_turns, agent_type="general": _BadChild(p))
compact_v5/MAIN/agent\tests\integration\test_skills.py:219:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_skills.py:246:    engine = QueryEngine(client=client, max_turns=2, budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_skills.py:259:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_skills.py:291:    engine = QueryEngine(client=client, max_turns=2, budget=IterationBudget(),

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/subagent/spawn.py | Select-Object -Skip 60 -First 230' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/subagent/agent_types.py | Select-Object -First 130' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/core/query_engine.py | Select-Object -Skip 450 -First 70' in D:\Github\sagemaker-coding-agent
 succeeded in 2452ms:
    turns_used: int = 0
    child_messages: List[Any] = field(default_factory=list)
    error: Optional[str] = None
    agent_type: str = "general"
    depth: int = 1


def _new_child_engine(parent_engine: Any, max_turns: int, agent_type: str = "general") -> Any:
    """Construct a fresh QueryEngine that shares the parent's IterationBudget.

    Lazy-imports to avoid a circular load at module-import time
    (core.query_engine imports tools/registry which may import
    tools/task.py which imports this module).

    Block B: `agent_type` is forwarded as `agent_kind` so TOKENS.add()
    attributes the child's input/output/cost to the right per-agent
    bucket. The child also gets a fresh session_id so AUDIT.log entries
    can be filtered to a single sub-agent run.
    """
    from core.query_engine import QueryEngine
    return QueryEngine(
        client=parent_engine.client,
        max_turns=max_turns,
        budget=parent_engine.budget,            # SHARED â€” the Phase-9 contract
        on_stop_check=parent_engine.on_stop_check,
        agent_kind=agent_type,
    )


def _resolve_agent_suffix(agent_type: str) -> Optional[str]:
    """Look up the prompt suffix for a known agent type.

    Returns None for unknown types so the caller (spawn_subagent / task tool)
    can surface an explicit error instead of silently falling back. Phase-9
    Codex finding: silent fallback masks contract bugs.

    Block G: now consults the AGENT_TYPES registry (was: tiny dict keyed on
    "general" only). Returns the per-type system_suffix.
    """
    from .agent_types import get_agent_type
    at = get_agent_type(agent_type)
    return at.system_suffix if at is not None else None


def spawn_subagent(
    parent_engine: Any,
    prompt: str,
    agent_type: str = "general",
    parent_depth: int = 0,
    max_turns: int = 25,
    max_depth: int = DEFAULT_MAX_DEPTH,
    base_system_prompt: Optional[str] = None,
    workspace: Optional[str] = None,
    status_path: Optional[str] = None,
    todos_text: Optional[str] = None,
    recent_files: Optional[List[str]] = None,
    plan_mode: bool = False,
    output_fn: Callable[[str], None] = print,
) -> SubagentResult:
    """Spawn a sub-agent with the parent's shared IterationBudget.

    The child gets:
      - A FRESH message buffer (no parent conversation leakage).
      - The parent's BedrockClient, IterationBudget, on_stop_check (shared).
      - A system prompt = base_system_prompt + env_details + handoff_block
        + agent-type suffix, with the cache boundary preserved.

    Returns a `SubagentResult` with the child's final answer + audit info.

    Phase 9 contract (V5_PLAN.md Â§Phase 9):
      - Parent's `messages` buffer is NOT mutated.
      - Child's `budget is parent_engine.budget` (object identity).
      - Depth-limit enforcement: depth >= max_depth â†’ blocked with error
        result, no Bedrock call made.
    """
    child_depth = parent_depth + 1

    # Depth-limit gate (v4 sagemaker_agent.py:8354 parity).
    if child_depth > max_depth:
        return SubagentResult(
            text="",
            stop_reason="depth_exceeded",
            error=(
                f"Blocked: sub-agent depth limit reached "
                f"({child_depth} > max {max_depth})"
            ),
            agent_type=agent_type,
            depth=child_depth,
        )

    # Validate prompt â€” empty prompt is a programming error in the caller.
    p = (prompt or "").strip()
    if not p:
        return SubagentResult(
            text="",
            stop_reason="invalid_args",
            error="Error: prompt is required",
            agent_type=agent_type,
            depth=child_depth,
        )

    # Validate agent type. The task tool already gates on this at the
    # dispatch layer, but spawn_subagent is also called directly by Phase
    # 11 UX wiring, so guard here too. Codex Phase-09 finding: don't
    # silently fall back to `general`.
    suffix = _resolve_agent_suffix(agent_type)
    if suffix is None:
        from .agent_types import AGENT_TYPES
        available = ", ".join(sorted(AGENT_TYPES.keys()))
        return SubagentResult(
            text="",
            stop_reason="invalid_args",
            error=(
                f"Error: unknown agent_type '{agent_type}'. "
                f"Block G supports: {available}."
            ),
            agent_type=agent_type,
            depth=child_depth,
        )

    # Block G â€” resolve the AgentType row for per-type max_turns / worktree
    # / auto_load_skill knobs.
    from .agent_types import get_agent_type
    agent_def = get_agent_type(agent_type)
    if agent_def is not None:
        # Per-type max_turns: caller can override via the max_turns param.
        # Default policy: use the per-type ceiling unless caller passed
        # something smaller (defense in depth â€” caller knows the task).
        max_turns = min(max_turns, agent_def.max_turns)

    # Assemble the child's system prompt:
    #   <static> [+ env_details + handoff_block + agent_type_suffix in dynamic tail]
    # If base_system_prompt has the boundary marker, inject our extras after it.
    # Otherwise append at the end.
    from prompt import build_system_prompt, CACHE_BOUNDARY

    base = base_system_prompt or build_system_prompt(ctx={})
    env_details = build_env_details(
        agent_type=agent_type,
        depth=child_depth,
        workspace=workspace,
        max_depth=max_depth,
    )
    handoff = build_handoff_block(
        status_path=status_path,
        todos_text=todos_text,
        recent_files=recent_files,
    )

    dynamic_extras = [env_details, handoff, suffix]
    dynamic_extras = [x for x in dynamic_extras if x]

    if dynamic_extras:
        addendum = "\n\n" + "\n\n".join(dynamic_extras)
        if CACHE_BOUNDARY in base:
            # Append after the existing dynamic tail (preserve cached prefix).
            child_prompt = base + addendum
        else:
            # No boundary â€” append at the end with our own boundary so future
            # cache-block builders see the static/dynamic split.
            child_prompt = base + CACHE_BOUNDARY + addendum
    else:
        child_prompt = base

    # Construct child engine. The shared-budget invariant is enforced by
    # _new_child_engine â€” verified by test_subagent_shares_iteration_budget.
    child = _new_child_engine(parent_engine, max_turns=max_turns, agent_type=agent_type)

    # Codex Phase-09 finding (BLOCKER): thread the child's depth so that
    # IF the child itself dispatches `task`, the QueryEngine's tool-dispatch
    # context picks up the correct `parent_depth` via
    # `getattr(self, "_subagent_depth", 0)`. Without this line, nested
    # `task` chains all see parent_depth=0 and the recursion guard never
    # fires. Lock test: test_nested_subagent_recursion_blocked_at_max_depth.
    child._subagent_depth = child_depth

    # Snapshot the parent's full message buffer for a defense-in-depth
    # mutation check. Codex Phase-09 finding (medium): the prior version
    # checked only length, so an in-place mutation that preserves length
    # (e.g. modifying messages[i]["content"] of an existing entry) would
    # evade detection. We deep-copy so post-hoc comparison is structural.
    import copy
    parent_msgs_snapshot = copy.deepcopy(parent_engine.messages)

    # Resolve the child's tool pool. Block G iter-2 (Codex finding #2 HIGH):
    # specialized agents (explore/plan/verify/review) get a tool allowlist
    # enforced at spawn â€” prompt-only "Do NOT edit files" wording was not a
    # contract. When agent_def.allowed_tools is set, child_tools is filtered
    # to that subset; otherwise the full registry is used.
    #
    # Block G iter-3 (Codex iter-2 finding #1 HIGH): do NOT auto-include the
    # `task` tool for restricted agents. Otherwise a read-only explore agent
    # could call task(subagent_type="build") and regain mutating tools via
    # a child â€” completely bypassing the allowlist contract. Restricted
    # agents are intentionally one-shot leaf-roles; they don't need to
    # spawn further sub-agents.
    # `tool_search` is still safe to include (it just changes which tool
    # schemas are visible; it cannot reach mutators that aren't in the
    # allowlist).
    from tools import all_registered
    child_tools = all_registered()
    if agent_def is not None and agent_def.allowed_tools:
        _allow = set(agent_def.allowed_tools)
        # Block G iter-3: tool_search is harmless (read-only metadata),
        # task is NOT auto-included â€” restricted agents stay restricted.
        _allow.add("tool_search")
        child_tools = [t for t in child_tools if t.name in _allow]
        logging.debug(
            "[subagent] agent_type=%s tool allowlist (%d tools): %s",
            agent_type, len(child_tools), sorted(t.name for t in child_tools),
        )

    # Block B+ (PORT_LOG #053): save+clear FILE_CACHE main context
    # before the child runs so the child sees a fresh in-context set;
    # restore the parent's set after the child returns. Best-effort â€”
    # if FILE_CACHE singleton is unavailable, dispatch still proceeds.
    _file_cache_saved = None
    try:
        from runtime.file_cache import FILE_CACHE as _FC
        _file_cache_saved = _FC.save_and_clear_context()
    except Exception:
        pass

    # Block G â€” worktree spawn for `build` agents. Best-effort; on hard
    # failure, runs in parent dir with a warning.
    _worktree_path: Optional[str] = None
    if agent_def is not None and agent_def.needs_worktree:
        try:
            from .worktree import create_worktree
            from runtime.config import CONFIG as _CFG_W

 succeeded in 3443ms:
                    content = last_user.get("content")
                    if isinstance(content, str):
                        last_user["content"] = content + reminder
                    elif isinstance(content, list):
                        content.append({"type": "text", "text": reminder})
            except Exception as exc:  # noqa: BLE001 â€” skill machinery never raises into agent loop
                logging.warning("[skill-wiring] %s: %s", type(exc).__name__, exc)

        last_text = ""
        stop_reason = ""
        turns_used = 0

        for turn in range(self.max_turns):
            # User-requested stop (Phase 11 wires this to the Stop button).
            if self.on_stop_check and self.on_stop_check():
                output_fn("[Stopped by user]")
                stop_reason = "user_stop"
                break

            # Block M-2 (PORT_LOG #084) â€” structured-output retry-limit
            # guard. When `synthetic_output_tool_name` is configured, count
            # how many times the model produced a malformed structured
            # output (each tool_use of that synthetic tool counts). Halt
            # cleanly at the retry limit instead of looping forever.
            if self.synthetic_output_tool_name:
                _calls_now = count_tool_calls(
                    self.messages, self.synthetic_output_tool_name,
                )
                _calls_this_run = _calls_now - self._initial_structured_output_calls
                if _calls_this_run >= self.max_structured_output_retries:
                    output_fn(
                        f"[error_max_structured_output_retries: "
                        f"failed to provide valid structured output after "
                        f"{self.max_structured_output_retries} attempts]"
                    )
                    stop_reason = "error_max_structured_output_retries"
                    break

            # Budget gate â€” shared with sub-agents (Phase 9).
            if not self.budget.consume():
                used, total = self.budget.used(), self.budget.total()
                output_fn(
                    f"[Budget exhausted: {used}/{total} iterations used. "
                    "Adjust IterationBudget or start a new session.]"
                )
                stop_reason = "budget_exhausted"
                break

            # Phase 7 wiring contract: per-turn deferral + discovery merge.
            visible_tools, deferred_names = apply_tool_search_deferral(
                tools, enabled=True,
            )
            if self._discovered_tool_names:
                # Promote previously-discovered tools from deferred â†’ visible.
                discovered = {n for n in self._discovered_tool_names if n in deferred_names}
                if discovered:
                    promoted = [
                        t for t in tools
                        if t.name in discovered and t.name not in {v.name for v in visible_tools}
                    ]
                    visible_tools = visible_tools + promoted
                    deferred_names = [n for n in deferred_names if n not in discovered]

            # If any names remain deferred, surface them as a system reminder
            # so the model knows they exist and how to load them.
            turn_messages = list(self.messages)
            if deferred_names:
                turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)

            # Bedrock invocation.

 succeeded in 4418ms:
"""V5 subagent/agent_types.py â€” Block G AGENT_TYPES registry.

PORT_LOG: #086.

Source:
- v4 sagemaker_agent.py:6914-7090 (~176 LOC original AGENT_TYPES dict)
- Runnable AgentTool/constants.ts (ONE_SHOT_BUILTIN_AGENT_TYPES)
- Runnable AgentTool/prompt.ts (DEFAULT_AGENT_PROMPT phrasing)

Each agent type is one row with:
- system_suffix: a per-agent prompt suffix appended to the base system
  prompt. Sets task-shape expectations.
- max_turns: ceiling on the sub-agent's turn count (independent of the
  shared IterationBudget, which is the cost-cap; max_turns is the
  task-scope-cap).
- one_shot: True for Explore/Plan/Verify-style agents that produce a
  single report and don't accept follow-up; matches Runnable's
  ONE_SHOT_BUILTIN_AGENT_TYPES (constants.ts:9-12). One-shot agents
  skip the agentId/SendMessage/usage trailer in their system prompt
  to save tokens.
- auto_load_skill: optional skill name to auto-activate in the child's
  SkillManager before run(). Used by `verify` to load skills/verify/
  for the verification gate-checks.
- needs_worktree: True for `build` â€” spawns the child in an isolated
  git worktree so concurrent build agents don't clobber each other.
  v4 sagemaker_agent.py:8413+ (~57 LOC).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Block G-6: DEFAULT_AGENT_PROMPT verbatim (Runnable constants/prompts.ts:758).
# Battle-tested wording: tells sub-agents NOT to gold-plate; the parent
# only needs the answer, not surrounding cleanup. Keeps token cost
# predictable for cheap fanout patterns (Explore + Plan).
DEFAULT_AGENT_PROMPT = (
    "You are a sub-agent working on a focused task. Always use ABSOLUTE "
    "file paths (cwd may reset between bash calls). In your final "
    "response, share relevant file paths and key findings. Be concise â€” "
    "the parent will read your full reply. Do NOT add features, "
    "refactor, or introduce abstractions beyond what the task requires."
)


# Block G-7: "Notes" appendix to subagent system prompt
# (Runnable constants/prompts.ts:766-770). Each line fixes a real
# failure mode in the wild.
SUBAGENT_NOTES = (
    "\n\nNotes:\n"
    "- Always include a short description of what you'll do before tool calls.\n"
    "- When you launch multiple research tasks, run them in parallel.\n"
    "- The parent agent CANNOT see your intermediate tool calls â€” only "
    "your final reply text. Surface findings explicitly in your reply."
)


@dataclass(frozen=True)
class AgentType:
    name: str
    system_suffix: str
    max_turns: int = 25
    one_shot: bool = False
    auto_load_skill: Optional[str] = None
    needs_worktree: bool = False
    # Block G iter-2 (Codex finding #2 HIGH): allowed_tools allowlist enforced
    # at spawn time (was: prompt-only "Do NOT edit files" wording, which the
    # model could ignore). When None, the child gets the full registry.
    # When set, child_tools is filtered to this list before child.run.
    allowed_tools: Optional[tuple] = None  # tuple for frozen-dataclass safety


# Read-only tool allowlist for explore / plan / review (no file mutation,
# no shell exec). semantic_search included because it's read-only.
_READ_ONLY_TOOLS: tuple = (
    "read_file", "grep", "glob", "list_dir", "view_image",
    "todo_read", "todo_write", "semantic_search", "ask_user",
)
# Verify allowlist: read-only + bash (so verify can run pytest / lint /
# build commands). NO edit/write tools.
_VERIFY_TOOLS: tuple = _READ_ONLY_TOOLS + ("bash", "python_exec")


# Block G-1: AGENT_TYPES dict â€” 7 entries per TEST_DESIGN test_agent_types_dict_has_7.
# Names match v4 + Runnable conventions.
AGENT_TYPES: dict = {
    "general": AgentType(
        name="general",
        system_suffix=DEFAULT_AGENT_PROMPT + SUBAGENT_NOTES,
    ),
    "explore": AgentType(
        name="explore",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: read-only exploration. Use Read, Grep, Glob to "
            "understand the codebase. Do NOT edit files. Return a concise "
            "summary with file:line references for key findings."
            + SUBAGENT_NOTES
        ),
        max_turns=20,
        one_shot=True,  # Block G-3: ONE_SHOT_BUILTIN_AGENT_TYPES
        allowed_tools=_READ_ONLY_TOOLS,
    ),
    "plan": AgentType(
        name="plan",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: produce an implementation plan. Read code as "
            "needed (Read, Grep, Glob). Do NOT write code. Return a "
            "step-by-step plan with file paths and what to change."
            + SUBAGENT_NOTES
        ),
        max_turns=15,
        one_shot=True,
        allowed_tools=_READ_ONLY_TOOLS,
    ),
    "verify": AgentType(
        name="verify",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: run verification gates. Use the loaded `verify` "
            "skill body for the exact checklist. Report PASS/FAIL per gate "
            "and a single overall verdict at the end."
            + SUBAGENT_NOTES
        ),
        max_turns=20,
        one_shot=True,
        auto_load_skill="verify",  # Block G â€” TEST_DESIGN row 3
        allowed_tools=_VERIFY_TOOLS,  # read-only + bash + python_exec

codex
One design gap is stronger than just the retry count: the final marker assertions prove `findings.md` has real fixture content, but not strictly that the content came from the children. A parent could dispatch three tasks, ignore their outputs, read the files itself, and still pass.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/tools/task.py | Select-Object -First 240' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/subagent/spawn.py | Select-Object -Skip 290 -First 90' in D:\Github\sagemaker-coding-agent
 succeeded in 2239ms:
"""Phase 9 task tool â€” sub-agent dispatch (Phase 9, ADR-015).

ADAPT port of:
- gg-claude-code-runnable/src/tools/AgentTool/AgentTool.tsx (1397 LOC) â€” only the
  tool-shape contract (description + schema + executor signature). Runnable's
  React/Ink UI lives in UI.tsx and is not ported (constraint=.ipynb).
- v4 `_run_task_tool` at sagemaker_agent.py:8350 â€” the executor logic.

PORT_LOG: #024.

Phase 9 surface â€” minimal so the v5 .ipynb shape doesn't drag the full
AGENT_TYPES + worktree complexity across the gate:
- subagent_type values: "general" only. Future phases add build/plan/explore/verify.
- No worktree isolation (build agent's git-worktree dance lands in Phase 11).
- No parallel dispatch (Runnable's parallel sub-agent dispatch is async-only).

The tool is marked `should_defer=True` because spawn is low-frequency:
most turns don't need a sub-agent, so the schema is loaded only when the
model calls tool_search after seeing the deferred-tool reminder.

The Phase 7 wiring contract (ADR-013/014) requires the executor to receive
the parent QueryEngine via `context["parent_engine"]` so the child can share
the parent's IterationBudget â€” see acceptance test
`test_subagent_shares_iteration_budget`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import build_tool, register


_DESCRIPTION = """Launch a sub-agent for a specific, scoped task.

Sub-agents run with a FRESH conversation but share the parent agent's iteration budget â€” they cannot collectively exceed the cost ceiling. Use a sub-agent when:
- The task is well-scoped and self-contained (e.g., "summarize this codebase", "find every TODO comment").
- You want to keep the parent's main context clean (the sub-agent's full transcript is not loaded into the parent â€” only the final answer is returned).
- You need read-only exploration without polluting the parent's file-read history.

Do NOT use a sub-agent when:
- The task is small enough to do directly in the current turn.
- The result must be incrementally visible to the user (sub-agent runs to completion before returning).
- You need persistent state across multiple top-level requests (sub-agents are one-shot).

Inputs:
- description: 1-line summary shown to the user.
- prompt: the actual task description for the sub-agent. Be specific.
- subagent_type: one of `general` | `explore` | `plan` | `verify` | `build` | `review` | `fork` (default `general`).
  - `general` â€” full tool access; default.
  - `explore` â€” read-only exploration (no edit/write/exec); produces a report.
  - `plan` â€” read-only planning (no edit/write/exec); produces a step-by-step plan.
  - `verify` â€” read + bash; auto-loads the `verify` skill; runs gate checks.
  - `build` â€” full tools, runs in isolated git worktree.
  - `review` â€” read-only code review; surfaces concrete issues with file:line.
  - `fork` â€” inherits parent context conceptually; full tools.

Returns the sub-agent's final answer as a string. If the sub-agent hits its iteration budget or max_turns, the partial work + reason is returned."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "1-line summary of what the sub-agent will do (for display only).",
        },
        "prompt": {
            "type": "string",
            "description": "Full task description sent to the sub-agent. Be specific â€” the sub-agent has no parent context unless you brief it.",
        },
        "subagent_type": {
            "type": "string",
            "enum": ["general", "explore", "plan", "verify", "build", "review", "fork"],
            "default": "general",
            "description": "Agent type. general (default; full tools) | explore (read-only) | plan (read-only) | verify (read + bash + auto-loads verify skill) | build (full + isolated git worktree) | review (read-only code review) | fork (full tools, parent-context).",
        },
    },
    "required": ["prompt"],
}


def _task_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Spawn a sub-agent and return its final answer.

    Required context (Phase 9 contract):
      - context["parent_engine"]: the parent QueryEngine. Used to (a) share
        IterationBudget, (b) reuse the BedrockClient, (c) inherit on_stop_check.
        If absent, the executor returns an Error: the model can read.
      - context["parent_depth"] (optional, default 0): the parent's depth.
        Used to enforce the recursion-depth limit.
    """
    description = str(args.get("description", "")).strip()
    prompt = str(args.get("prompt", "")).strip()
    if not prompt:
        return "Error: prompt is required and must be a non-empty string"
    subagent_type = str(args.get("subagent_type", "general")).strip() or "general"

    # Codex Phase-09 finding (medium): silently falling back to general for
    # unknown types hides caller/model errors. v4's explicit-unknown-type
    # contract (sagemaker_agent.py:8366) is preserved here.
    # Block G: validation now consults the full AGENT_TYPES registry
    # (build / plan / explore / verify / general / review / fork) â€” was
    # the Phase-9 single-entry _AGENT_TYPE_SUFFIXES dict.
    from subagent.agent_types import AGENT_TYPES
    if subagent_type not in AGENT_TYPES:
        available = ", ".join(sorted(AGENT_TYPES.keys()))
        return (
            f"Error: unknown subagent_type '{subagent_type}'. "
            f"Block G supports: {available}."
        )

    if not isinstance(context, dict) or "parent_engine" not in context:
        return (
            "Error: task tool requires `context['parent_engine']` to spawn a "
            "sub-agent (Phase 9 contract). The query_engine should pass this "
            "via the tool dispatch context."
        )
    parent_engine = context["parent_engine"]
    parent_depth = int(context.get("parent_depth", 0))

    # Lazy-import to avoid circular import: subagent.spawn imports
    # core.query_engine which (via tools/__init__.py:bootstrap_built_ins)
    # imports this module.
    from subagent.spawn import spawn_subagent

    result = spawn_subagent(
        parent_engine=parent_engine,
        prompt=prompt,
        agent_type=subagent_type,
        parent_depth=parent_depth,
        plan_mode=bool(context.get("plan_mode", False)),
    )

    if result.error and result.stop_reason in ("depth_exceeded", "invalid_args"):
        return result.error
    if result.stop_reason in ("budget_exhausted", "max_turns", "context_overflow"):
        # Surface partial work + reason so the parent can react.
        return (
            f"[Sub-agent stopped: {result.stop_reason}]\n"
            f"{result.text or '(no partial output)'}"
        )
    return result.text or "(sub-agent returned no text)"


def _register():
    """Idempotent registration. Called by tools/__init__.py:bootstrap_built_ins."""
    from .registry import find_tool_by_name, all_registered, unregister
    if find_tool_by_name(all_registered(), "task") is not None:
        return  # already registered

    register(build_tool(
        name="task",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_task_executor,
        is_read_only=False,         # children may write â€” fail-closed default
        is_destructive=False,
        is_concurrency_safe=False,  # parallel sub-agents land later
        requires_approval=False,    # the *child* approval gates fire on its tool calls
        should_defer=True,          # low-frequency; deferred via Phase 7
        always_load=False,
        search_hint="sub-agent fork delegate spawn task launch background",
    ))

 succeeded in 3089ms:
            _wt_parent = workspace or getattr(_CFG_W, "workspace", os.getcwd())
            _worktree_path, _wt_source = create_worktree(_wt_parent)
            if _worktree_path:
                logging.info(
                    "[subagent] build agent isolated in worktree=%s (source=%s)",
                    _worktree_path, _wt_source,
                )
            else:
                logging.warning(
                    "[subagent] build agent worktree creation failed â€” "
                    "running in parent cwd."
                )
        except Exception as _wt_exc:
            logging.warning("[subagent] worktree setup raised: %s", _wt_exc)
            _worktree_path = None

    # Block G â€” verify agent auto-loads the verify skill so its body sits
    # in the child's system prompt as the gate-check checklist.
    if (
        agent_def is not None
        and agent_def.auto_load_skill
        and parent_engine.skill_manager is not None
    ):
        try:
            ok, _msg = parent_engine.skill_manager.activate(agent_def.auto_load_skill)
            if ok:
                # Inject the active skill body into the child's system prompt
                # tail (cannot share parent's skill_manager state directly
                # since child has its own SkillManager surface in v5).
                _skill_body = parent_engine.skill_manager.get_active_skill_prompt(
                    session_id=getattr(parent_engine, "session_id", ""),
                )
                if _skill_body:
                    child_prompt = child_prompt + _skill_body
        except Exception as _sk_exc:
            logging.warning(
                "[subagent] verify-skill auto-load failed: %s", _sk_exc,
            )

    # Block G iter-2 (Codex finding #1 BLOCKER): swap CONFIG.workspace to
    # the worktree path so tools that read `CONFIG.workspace` (bash cwd,
    # security path checks, edit_file allowed-paths) actually run inside
    # the isolated worktree. Restore in finally so the parent sees its
    # original workspace afterward â€” even if child.run raises.
    _saved_workspace = None
    if _worktree_path:
        try:
            from runtime.config import CONFIG as _CFG_S
            _saved_workspace = _CFG_S.workspace
            _CFG_S.workspace = _worktree_path
            logging.debug(
                "[subagent] swapped CONFIG.workspace=%s -> %s for build agent",
                _saved_workspace, _worktree_path,
            )
        except Exception as _ws_exc:
            logging.warning(
                "[subagent] CONFIG.workspace swap failed: %s", _ws_exc,
            )
            _saved_workspace = None

    try:
        # The child runs synchronously to completion or budget exhaustion.
        result = child.run(
            user_message=p,
            system_prompt=child_prompt,
            tools=child_tools,
            plan_mode=plan_mode,
            output_fn=output_fn,
        )
    finally:
        # Always restore parent's in-context set, even if child raised.
        if _file_cache_saved is not None:
            try:
                from runtime.file_cache import FILE_CACHE as _FC
                _FC.restore_context(_file_cache_saved)
            except Exception:
                pass
        # Block G iter-2 â€” restore CONFIG.workspace before worktree cleanup
        # so subsequent parent-side tools see the original workspace again.
        if _saved_workspace is not None:
            try:
                from runtime.config import CONFIG as _CFG_S
                _CFG_S.workspace = _saved_workspace
            except Exception:
                pass
        # Block G â€” worktree cleanup on child completion (or failure).
        # Best-effort; logs but doesn't block.
        if _worktree_path:
            try:
                from .worktree import cleanup_worktree

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/subagent/spawn.py | Select-Object -Skip 380 -First 80' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "def is_over_budget|session_cost_limit|session_cost|api_calls|def reset" compact_v5/MAIN/agent/runtime/tokens.py compact_v5/MAIN/agent/runtime/config.py' in D:\Github\sagemaker-coding-agent
 succeeded in 2405ms:
                cleanup_worktree(_worktree_path)
            except Exception as _wt_cleanup_exc:
                logging.warning(
                    "[subagent] worktree cleanup raised: %s", _wt_cleanup_exc,
                )

    # Defense-in-depth: confirm the parent buffer wasn't mutated. Structural
    # comparison via the deep snapshot â€” catches in-place edits that preserve
    # length as well as length-changing mutations.
    if parent_engine.messages != parent_msgs_snapshot:
        # This should never happen if the contract holds. Surface a clear
        # error rather than silently corrupt parent state.
        return SubagentResult(
            text=result.text,
            stop_reason="parent_context_mutated",
            error=(
                "Internal error: parent_engine.messages was mutated by "
                "sub-agent dispatch. Phase-9 contract violated."
            ),
            child_messages=result.messages,
            agent_type=agent_type,
            depth=child_depth,
        )

    return SubagentResult(
        text=result.text,
        stop_reason=result.stop_reason,
        turns_used=result.turns_used,
        child_messages=result.messages,
        error=result.error,
        agent_type=agent_type,
        depth=child_depth,
    )

 succeeded in 3100ms:
compact_v5/MAIN/agent/runtime/tokens.py:310:    up to the same `session_cost` total. Per Plan v3 §Block B + B-11.
compact_v5/MAIN/agent/runtime/tokens.py:340:    def reset(self):
compact_v5/MAIN/agent/runtime/tokens.py:353:        self.api_calls = 0
compact_v5/MAIN/agent/runtime/tokens.py:354:        self.session_cost = 0.0
compact_v5/MAIN/agent/runtime/tokens.py:400:            self.api_calls += 1
compact_v5/MAIN/agent/runtime/tokens.py:424:                self.session_cost += cost
compact_v5/MAIN/agent/runtime/tokens.py:454:            limit = self._config.session_cost_limit
compact_v5/MAIN/agent/runtime/tokens.py:455:            if limit > 0 and self.session_cost > 0:
compact_v5/MAIN/agent/runtime/tokens.py:456:                pct = self.session_cost / limit
compact_v5/MAIN/agent/runtime/tokens.py:460:                        f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
compact_v5/MAIN/agent/runtime/tokens.py:465:                        f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
compact_v5/MAIN/agent/runtime/tokens.py:472:    def is_over_budget(self) -> bool:
compact_v5/MAIN/agent/runtime/tokens.py:473:        limit = self._config.session_cost_limit
compact_v5/MAIN/agent/runtime/tokens.py:474:        return limit > 0 and self.session_cost >= limit
compact_v5/MAIN/agent/runtime/tokens.py:495:            f"${self.session_cost:.4f}"
compact_v5/MAIN/agent/runtime/tokens.py:496:            if self.session_cost < 0.01
compact_v5/MAIN/agent/runtime/tokens.py:497:            else f"${self.session_cost:.2f}"
compact_v5/MAIN/agent/runtime/tokens.py:514:            "api_calls": self.api_calls,
compact_v5/MAIN/agent/runtime/tokens.py:515:            "session_cost_usd": round(self.session_cost, 6),
compact_v5/MAIN/agent/runtime/tokens.py:539:            self.api_calls = int(stats.get("api_calls", 0))
compact_v5/MAIN/agent/runtime/tokens.py:540:            self.session_cost = float(stats.get("session_cost_usd", 0.0))
compact_v5/MAIN/agent/runtime/tokens.py:598:    if TOKENS.session_cost > 0:
compact_v5/MAIN/agent/runtime/tokens.py:601:            f"({TOKENS.api_calls} API calls, "
compact_v5/MAIN/agent/runtime/config.py:90:    session_cost_limit: float = 0.0  # 0 = no limit. Warns at 80%, stops at 100%.
compact_v5/MAIN/agent/runtime/config.py:135:    # budget AND not diminishing-returns AND session_cost < session_cost_limit
compact_v5/MAIN/agent/runtime/config.py:228:        "aws_bedrock_only": bool, "disable_local_traces": bool, "session_cost_limit": float,

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/core/budget.py | Select-Object -First 80' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/agent.py | Select-Object -Skip 60 -First 60' in D:\Github\sagemaker-coding-agent
 succeeded in 2427ms:
"""V5 core/budget.py â€” IterationBudget (Hermes pattern via v4).

Per ADR-014: verbatim port of v4's IterationBudget at
`compact_v4/MAIN/agent/sagemaker_agent.py:8190`. v4 itself adopted this
from `D:/Github/hermes-agent/run_agent.py:170` in v4.9.4.

PORT_LOG: #016.

Why this exists (PS Issue #2):
A parent agent could otherwise spawn N sub-agents that each loop
max_turns times, blowing the cost ceiling. Insurance/audit values
predictable cost ceilings per user request. Counter is shared across
parent + sub-agents (the parent creates one budget at the start of
`run()`; sub-agents inherit the same instance).

Phase 11 (notebook UX) will wire the budget's `consume() / remaining()
/ used() / total()` methods into an ipywidgets progress bar so the
user can SEE the budget burning down â€” addressing PS Issue #2's
"budget is invisible until exhausted" complaint.
"""
from __future__ import annotations

import threading


class IterationBudget:
    """Thread-safe counter shared across a parent agent and its spawned sub-agents.

    A parent agent creates one budget at the start of run(); sub-agents inherit
    the same instance. Each LLM turn (success or failure) increments the counter.
    When `consume()` returns False, the agent surfaces a "budget exhausted"
    message and stops cleanly, preserving partial work.
    """

    DEFAULT_MAX = 600  # v4.10.10 in-place: 90 -> 600 (Hermes default 90 too tight for SageMaker dev)

    def __init__(self, max_iterations: int = DEFAULT_MAX):
        self._max = max(1, int(max_iterations))
        self._used = 0
        self._lock = threading.Lock()

    def consume(self) -> bool:
        """Atomically reserve one iteration. Returns False if budget is exhausted."""
        with self._lock:
            if self._used >= self._max:
                return False
            self._used += 1
            return True

    def remaining(self) -> int:
        with self._lock:
            return max(0, self._max - self._used)

    def used(self) -> int:
        with self._lock:
            return self._used

    def total(self) -> int:
        return self._max

    def reset(self) -> None:
        """Reset counter to 0. Tests + manual /reset only â€” not a normal flow."""
        with self._lock:
            self._used = 0

 succeeded in 3276ms:
    """Minimal public Agent wrapping the Phase 8-10 surfaces."""

    def __init__(
        self,
        client: Any,
        max_turns: int = 50,
        budget: Optional[IterationBudget] = None,
        skill_manager: Optional[Any] = None,
        on_stop_check: Optional[Callable[[], bool]] = None,
        system_prompt: Optional[str] = None,
        plan_mode: bool = False,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
    ):
        """Construct the Agent.

        Args:
            client: BedrockClient (or mock with the same `chat(...)` shape).
            max_turns: hard upper bound on turns per `run()` call.
            budget: shared IterationBudget. If None, a fresh one is created.
            skill_manager: optional SkillManager for active-skill prompt
                injection + auto-trigger reminder (Phase 10 wiring).
            on_stop_check: callable returning True if user pressed Stop.
            system_prompt: override the default `prompt.build_system_prompt`.
                If None, the static v5 prompt is used.
            plan_mode: when True, the dispatch gate enforces the v4
                PLAN_MODE_ALLOWED_TOOLS read-only allowlist.
            thinking_enabled: send thinking config on every Bedrock call.
            thinking_budget: max tokens for thinking (PS Issue #4 surfaces this).
        """
        self.client = client
        self.budget = budget if budget is not None else IterationBudget()
        self.skill_manager = skill_manager
        self._stop_requested = False

        def _combined_stop():
            if self._stop_requested:
                return True
            if on_stop_check is not None and on_stop_check():
                return True
            return False

        self._engine = QueryEngine(
            client=client,
            max_turns=max_turns,
            budget=self.budget,
            on_stop_check=_combined_stop,
            skill_manager=skill_manager,
        )
        self._system_prompt = system_prompt
        self._plan_mode = bool(plan_mode)
        self._thinking_enabled = bool(thinking_enabled)
        self._thinking_budget = int(thinking_budget)
        # Block B+: AGENT_STATUS auto-load runs once on the first run() call.
        self._agent_status_loaded = False
        self._agent_status_text: Optional[str] = None

    # ------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------

codex
AXIS A VERDICT: APPROVE_WITH_FIXES

Findings:
- [medium] `compact_v5/MAIN/agent/tests/r_tier/test_r3_three_subagents.py:285` and `:289` — `>= 3` allows retry/noisy behavior to pass even though R3 claims exactly three file-scoped dispatches. Fix: tighten both to `== 3`.
- [medium] `:225-247` — final `findings.md` assertions prove real fixture content made it into the report, but not strictly that children produced it; parent could dispatch tasks, ignore child output, read files itself, and still pass. Fix: assert each `task` audit `result_summary` contains the expected function/marker, or assert child audit logs include `read_file` calls for `utils_a.py`, `utils_b.py`, and `utils_c.py`.
- [low] `:187` — `AUDIT.__init__(audit_dir=...)` is probably sufficient because `AuditLogger.__init__` resets `audit_dir`, lock, and disabled state, but this test depends on local traces. Fix: explicitly set and restore `CONFIG.disable_local_traces = False`.
- Confirmed: `:296` and `:301` are tight/falsifiable content assertions. Requiring all three function names and all three TODO markers catches lossy parent synthesis.

AXIS B VERDICT: APPROVE_WITH_FIXES

Findings:
- [cost-risk] `:198-202` — no explicit shared `IterationBudget` is passed, so `Agent` defaults to `IterationBudget.DEFAULT_MAX = 600`; parent/children share it, but it is not a useful R-tier cap. Fix: pass a small explicit budget, e.g. `IterationBudget(max_iterations=24)`.
- [cost-risk] `:201` — parent `max_turns=18` does not bound child turns; each `explore` child can run up to 20 turns. Cost stop is checked between calls, so it can only halt after recorded spend. Fix: explicit shared iteration budget plus `== 3` dispatch assertions.
- [cost-risk] `:285/:289` — accepting retries both weakens the design and permits wasted spend. Fix: exact dispatch count.

AXIS C VERDICT: APPROVE_WITH_FIXES

Coverage gap:
- This is good empirical coverage for real Bedrock task-tool dispatch, `explore` agent type routing, audit logging, and parent report synthesis.
- It does not prove true async parallelism, which is acceptable for current v5.
- It currently does not fully prove the parent used the sub-agent outputs rather than independently reading fixtures. Add child-output or child-read assertions before running.

FINAL

PRE-FLIGHT VERDICT: REJECT

Do not run AWS yet. Required fixes: tighten dispatch counts to `== 3`, add evidence that each child produced/read its assigned file content, set `disable_local_traces=False` for the test, and pass an explicit small shared `IterationBudget`.
tokens used
52,450
AXIS A VERDICT: APPROVE_WITH_FIXES

Findings:
- [medium] `compact_v5/MAIN/agent/tests/r_tier/test_r3_three_subagents.py:285` and `:289` — `>= 3` allows retry/noisy behavior to pass even though R3 claims exactly three file-scoped dispatches. Fix: tighten both to `== 3`.
- [medium] `:225-247` — final `findings.md` assertions prove real fixture content made it into the report, but not strictly that children produced it; parent could dispatch tasks, ignore child output, read files itself, and still pass. Fix: assert each `task` audit `result_summary` contains the expected function/marker, or assert child audit logs include `read_file` calls for `utils_a.py`, `utils_b.py`, and `utils_c.py`.
- [low] `:187` — `AUDIT.__init__(audit_dir=...)` is probably sufficient because `AuditLogger.__init__` resets `audit_dir`, lock, and disabled state, but this test depends on local traces. Fix: explicitly set and restore `CONFIG.disable_local_traces = False`.
- Confirmed: `:296` and `:301` are tight/falsifiable content assertions. Requiring all three function names and all three TODO markers catches lossy parent synthesis.

AXIS B VERDICT: APPROVE_WITH_FIXES

Findings:
- [cost-risk] `:198-202` — no explicit shared `IterationBudget` is passed, so `Agent` defaults to `IterationBudget.DEFAULT_MAX = 600`; parent/children share it, but it is not a useful R-tier cap. Fix: pass a small explicit budget, e.g. `IterationBudget(max_iterations=24)`.
- [cost-risk] `:201` — parent `max_turns=18` does not bound child turns; each `explore` child can run up to 20 turns. Cost stop is checked between calls, so it can only halt after recorded spend. Fix: explicit shared iteration budget plus `== 3` dispatch assertions.
- [cost-risk] `:285/:289` — accepting retries both weakens the design and permits wasted spend. Fix: exact dispatch count.

AXIS C VERDICT: APPROVE_WITH_FIXES

Coverage gap:
- This is good empirical coverage for real Bedrock task-tool dispatch, `explore` agent type routing, audit logging, and parent report synthesis.
- It does not prove true async parallelism, which is acceptable for current v5.
- It currently does not fully prove the parent used the sub-agent outputs rather than independently reading fixtures. Add child-output or child-read assertions before running.

FINAL

PRE-FLIGHT VERDICT: REJECT

Do not run AWS yet. Required fixes: tighten dispatch counts to `== 3`, add evidence that each child produced/read its assigned file content, set `disable_local_traces=False` for the test, and pass an explicit small shared `IterationBudget`.
