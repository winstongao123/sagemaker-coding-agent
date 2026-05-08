Reading additional input from stdin...
OpenAI Codex v0.128.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.5
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 019df025-2652-7011-9e97-ac8bccee371f
--------
user
# Codex CLI version: codex-cli 0.128.0
# Model used: gpt-5.5
# Reasoning effort: high
# Date: 2026-05-04

You are reviewing the PRE-FLIGHT design of an R-tier real-AWS test
before any Bedrock call is made. Each AWS call costs real money (cap
$0.50). Catch broken design / missing assertions / wasted-spend BEFORE
hitting Bedrock.

CONTEXT
- Test: R2 — large preamble triggers compaction-handling path on real Bedrock
- Block(s) being validated: Block A (Compactor + auto-compact + cache
  invariants) + Block B (TokenTracker accumulates 80K+ in single call)
- What it claims to prove: v5 handles a single Bedrock call with ~80K
  tokens of preamble + a follow-up question. PASS if the agent returns
  the correct simple answer (5) without the Compactor / cache-edits
  invariant crashing the loop.
- Cost cap (session_cost_limit): $0.50
- Model: au.anthropic.claude-haiku-4-5-20251001-v1:0
- Test file: compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py
- Scenario fixture: 2700 lines of lorem-ipsum (~78K tokens) prepended to
  a "What is 2 + 3?" question. tools=[] (pure reasoning, no tool calls).

KEY DESIGN INFO (verbatim):

Pre-flight applied (already infrastructure-fixed):
- CONFIG.require_tool_approval = False (R-tier un-attended)
- CONFIG.max_tokens = 64 (model only needs one digit reply)
- CONFIG.session_cost_limit = 0.50 (hard halt via on_stop_check)
- max_turns = 4 (sanity bound; expected = 1 turn)
- AU geo profile (+10% premium already applied via TOKENS.get_geo_multiplier)
- Unicode-safe output_fn already wrapped at engine init.

Cost math (AU geo): input ~78K × $1.10/MTok = ~$0.086 + output ~10 ×
$5.50/MTok = $0.000055 ≈ $0.086 per call. Single-turn task. WELL under
$0.50 cap.

Test code (key sections, full file ~150 LOC):

Setup block:
```python
CONFIG.workspace = str(tmp_path)
CONFIG.session_cost_limit = $0.50
CONFIG.model_id = au.anthropic.claude-haiku-4-5-20251001-v1:0
CONFIG.max_tokens = 64
CONFIG.require_tool_approval = False
sec_mgr.rebuild_singleton_for_tests()
TOKENS.reset()
```

Agent + run:
```python
client = BedrockClient(model_id=_HAIKU_45_AU, region="ap-southeast-2", mock_mode=False)
def _hard_cost_halt():
    return TOKENS.is_over_budget() ...
agent = Agent(client=client, max_turns=4, on_stop_check=_hard_cost_halt)
recap = (_LOREM_LINE + "\n") * 2700  # ~60K words
prompt = _R2_PROMPT_TEMPLATE.format(recap=recap)
result = agent.run(prompt, tools=[])
```

Prompt template:
"""
You are reviewing a long conversation history. Below is a recap of
prior context — most of it is filler. After the recap, please answer
ONE SHORT question.

=== RECAP (do not summarize back; just keep in mind) ===
{recap}
=== END RECAP ===

QUESTION: What is 2 + 3? Answer with a single number, no explanation.
"""

Assertions:
- result.stop_reason != "max_turns"
- result.text non-empty
- "5" in result.text OR "five" in result.text.lower()
- cost_used <= $0.50
- tokens_in > 50_000 (sanity: large preamble was actually sent)

Side-channel: writes _r2_metrics.json with tokens/cost/wallclock + final_text.

PRODUCE THREE INDEPENDENT VERDICTS.

=== AXIS A — Test design soundness ===
- Does the scenario actually exercise compaction? Note: with a single-
  turn task, Compactor.run won't trigger (it fires on per-turn check
  after 80% threshold). R2 as designed tests "Bedrock can handle large
  input" + "v5 doesn't crash" — NOT "Compactor fires + cuts safely".
  Is that scope acceptable for $0.50, or does R2 need to force
  multi-turn to actually exercise compaction?
- Are assertions specific (number 5 in response), not loose (any text)?
- Could the test pass even if v5 silently corrupted the prompt? (model
  could still answer 5 if even part of the question survived.)
- Setup/teardown correct (workspace + SECURITY + CONFIG restoration)?
- "5" string check: could match in "the 5th word" etc — too loose?

=== AXIS B — Cost-control soundness ===
- AU Haiku-4.5 pricing: $1.10/MTok in / $5.50/MTok out (10% premium).
  Estimate: 78K input × $1.10 + 64 output × $5.50 ≈ $0.086 per call.
  WELL under $0.50 cap. Acceptable for a sanity test.
- session_cost_limit enforced via on_stop_check.
- max_turns=4 caps loops.
- For long-session: not applicable (single turn).

=== AXIS C — Coverage of v5 EMPIRICAL evidence ===
- R2 contributes: real Bedrock 80K input acceptance, BedrockClient
  large-payload handling, TokenTracker accumulating 78K+ input in one
  add() call.
- Does it test Compactor at all? Probably NOT, given single-turn
  design. If you want compaction proof, R2 would need 2-3 turns where
  the message buffer crosses the threshold.
- Block V dropped — no v4 head-to-head.

=== FINAL ===
PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL | REJECT (do not run AWS)

If REJECT: required fixes (e.g. expand to multi-turn to actually fire
Compactor) before next pre-flight.
If APPROVE: log r_tier_review_log.md and proceed to AWS call.

Files for deeper exploration:
- compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py (~150 LOC)
- compact_v5/MAIN/agent/core/compactor.py (Block A Compactor)
- compact_v5/MAIN/agent/core/query_engine.py (auto-compact gate at :543)
codex
I’ll inspect the named test and compaction gate before giving the three verdicts. Since this is a pre-flight review, I’ll stay read-only and focus on whether the test proves its stated claim before spend.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/query_engine.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/compactor.py' in D:\Github\sagemaker-coding-agent
 succeeded in 1789ms:
"""R-tier R2 ƒ?" 80K-token preamble triggers compaction; next call PASSes.

Per PS_V5_TEST_PLAYBOOK.md / PS_V5_TEST_SET.md ATier 1 R2:
  Load 80K-token preamble, refactor ƒ+' check compaction fires +
  cache_edits invalidates only changed tools.

What it claims to prove:
  Block A (Compactor) end-to-end on real Bedrock:
  - When messages cross the auto-compact threshold, Compactor.run fires.
  - Post-compact next Bedrock call succeeds (no 400 from cut-mid-pair).
  - The cache_edits/cache invariant doesn't crash the loop under load.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.

Note vs R4 / R16: R4 tests cold-cache 30-min wait (PS#3); R16 tests
sustained 100+ turn coding work. R2 specifically tests COMPACTION
firing on a single big preamble + follow-up.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R2_COST_CAP_USD = 0.50

# Build a ~80K-token preamble out of repeated lorem-ipsum (cheaper to
# generate than reading a real file). 1 word ƒ%^ 1.3 tokens for English
# text ƒ+' 60K words ƒ%^ 78K tokens.
_LOREM_LINE = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
    "eiusmod tempor incididunt ut labore et dolore magna aliqua. "
)
# Each line ƒ%^ 22 words ƒ+' 60K words / 22 ƒ%^ 2700 lines.
_LOREM_LINES = 2700

_R2_PROMPT_TEMPLATE = """You are reviewing a long conversation history. Below is a recap of
prior context ƒ?" most of it is filler. After the recap, please answer
ONE SHORT question.

=== RECAP (do not summarize back; just keep in mind) ===
{recap}
=== END RECAP ===

QUESTION: What is 2 + 3? Answer with a single number, no explanation.
"""


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R2 is real-AWS gated.",
)
def test_r2_compaction_under_load(tmp_path, monkeypatch):
    """R-tier R2 ƒ?" large preamble + follow-up succeed without 400.

    PASS criteria:
      - Both turns return non-empty text.
      - Final answer correct (5).
      - No max_turns / cost_cap breach.
      - cost ƒ% $0.50.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    cwd_before = os.getcwd()
    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.session_cost_limit = _R2_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        # Per-turn output cap; model only needs to write one digit.
        CONFIG.max_tokens = 64
        CONFIG.require_tool_approval = False
        sec_mgr.rebuild_singleton_for_tests()
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R2_COST_CAP_USD
            )

        agent = Agent(
            client=client,
            max_turns=4,
            on_stop_check=_hard_cost_halt,
        )

        recap = (_LOREM_LINE + "\n") * _LOREM_LINES
        prompt = _R2_PROMPT_TEMPLATE.format(recap=recap)
        approx_tokens_in = len(prompt) // 4

        t0 = time.time()
        result = agent.run(prompt, tools=[])
        wallclock_s = time.time() - t0

        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output

        # Side-channel metrics for build_telemetry.
        metrics = {
            "test": "R2",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "wallclock_s": round(wallclock_s, 2),
            "approx_prompt_tokens": approx_tokens_in,
            "preamble_lines": _LOREM_LINES,
            "tool_calls": int(getattr(result, "turns_used", 0)),
            "cost_usd": round(cost_used, 4),
            "stop_reason": result.stop_reason,
            "final_text": (result.text or "").strip()[:200],
        }
        (tmp_path / "_r2_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R2 METRICS] {json.dumps(metrics)}")

        assert result.stop_reason != "max_turns", (
            f"R2 hit max_turns; metrics={metrics}"
        )
        assert result.text and result.text.strip(), (
            f"R2 returned empty final text. metrics={metrics}"
        )
        # Loose answer check ƒ?" model should respond with "5" somewhere.
        # Different verbalizations OK ("5", "5.", "Five", "= 5").
        text_l = result.text.lower()
        assert ("5" in result.text) or ("five" in text_l), (
            f"R2 expected answer 5 in response. got: {result.text!r}"
        )
        assert cost_used <= _R2_COST_CAP_USD, (
            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
            f"metrics={metrics}"
        )
        # Sanity: with an ~80K-token preamble, Bedrock should report
        # input_tokens >= 70K on the first call (some overhead).
        assert tokens_in > 50_000, (
            f"R2 expected large input_tokens (~80K); got {tokens_in}. "
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
            CONFIG.require_tool_approval = saved_require_approval
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2684ms:
"""V5 core/query_engine.py ƒ?" main agent loop (Phase 8 deliverable, ADR-014).

Per ADR-014: minimal, focused port of Runnable's `QueryEngine.ts` (1295 LOC)
adapted to the v5 .ipynb shape. v4's monolithic `Agent.run` (~1500 LOC) is
replaced by this ~400 LOC module with explicit IN-SCOPE / OUT-OF-SCOPE.

PORT_LOG: #019.

IN SCOPE (Phase 8):
- Per-turn loop with end_turn / max_turns / budget exhausted exits.
- IterationBudget gate at the top of each turn (shared with sub-agents).
- Phase 7 deferred-loading wiring contract:
    * `apply_tool_search_deferral(tools, enabled=True)` per turn.
    * `tool_search_discovered_names()` extraction from tool_search results.
    * Discovered names are added to the next turn's tools= API param.
- Tool dispatch via `find_tool_by_name(...).execute(args, context)`.
- tool_use ƒ+' tool_result message accumulation in the model-visible
  conversation buffer.
- Bedrock invocation through `BedrockClient.chat(...)`.
- System prompt assembly via `prompt.build_system_prompt(ctx)`.
- run_one_turn(...) helper for unit tests (single-turn, no loop).

OUT OF SCOPE ƒ?" explicitly deferred to later phases (per ADR-014):
- Microcompact / context_collapse ƒ?" Phase 11 UX (PS Issue #4 widget surface).
- 2-stage smart compaction (prune + LLM summary) ƒ?" Phase 11.
- Skill auto-trigger ƒ?" Phase 10 (`SKILLS.discover_relevant`).
- Plan mode injection of skills into prompt ƒ?" Phase 10.
- Sub-agent forkSubagent ƒ?" Phase 9 (`subagent/spawn.py`).
- File-read state tracking ƒ?" Phase 4 already lands this; engine respects but
  doesn't reset on compact (no compact in Phase 8).
- Diminishing-returns / repetition guard ƒ?" deferred.
- Notebook UX (output_fn callback contract) ƒ?" Phase 11 owns the UI shape;
  Phase 8 takes a `output_fn: Callable[[str], None] = print` so tests can
  capture, but real notebook integration lives in Phase 11.

The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
concurrent `run()` calls on the same engine are NOT supported (matches v4).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .budget import IterationBudget
from .errors import BedrockErrorCategory, ErrorClassifier


# ============================================================
# Result envelope
# ============================================================

@dataclass
class QueryResult:
    """Outcome of a `QueryEngine.run(...)` call.

    `text`           ƒ?" final assistant text (last end_turn turn's text block).
    `messages`       ƒ?" full message buffer including the user turn that
                       triggered this call. Caller may discard or persist.
    `stop_reason`    ƒ?" "end_turn" | "max_turns" | "budget_exhausted" |
                       "context_overflow" | "fatal_error".
    `turns_used`     ƒ?" count of model turns executed during this run.
    `budget_used`    ƒ?" IterationBudget.used() snapshot at exit.
    `error`          ƒ?" short message when stop_reason indicates failure.
    """
    text: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    stop_reason: str = ""
    turns_used: int = 0
    budget_used: int = 0
    error: Optional[str] = None


# ============================================================
# Helpers
# ============================================================

def _build_tools_api_payload(tools: List[Any]) -> List[Dict[str, Any]]:
    """Convert ToolRecord list into Bedrock `tools=` API payload shape.

    Bedrock expects: [{"name": ..., "description": ..., "input_schema": ...}, ...]
    """
    out: List[Dict[str, Any]] = []
    for t in tools:
        out.append({
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
        })
    return out


def _coerce_tool_result_to_text(value: Any) -> str:
    """Map any tool-execute return value into a Bedrock tool_result text string.

    Tool implementations return diverse shapes (str / dict / list). Bedrock's
    tool_result content needs a string. Prefer str() for primitives, JSON for
    structured shapes ƒ?" same convention as v4 dispatch."""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)
    return str(value)


def count_tool_calls(messages: List[Dict[str, Any]], tool_name: str) -> int:
    """Count how many tool_use blocks for `tool_name` appear in `messages`.

    Block M-2 (PORT_LOG #084) ƒ?" verbatim port of Runnable's countToolCalls
    at QueryEngine.ts:1004-1048. Used by the structured-output retry-limit
    guard: when the model produces malformed structured output N times in
    a row, the engine halts cleanly instead of looping.

    Iterates assistant messages; each tool_use block with matching name
    counts once.
    """
    if not tool_name:
        return 0
    count = 0
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == tool_name
            ):
                count += 1
    return count


def _truncate_tool_result(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = text[: max_chars - 200]
    return (
        head
        + f"\n\n[... truncated: tool_result exceeded {max_chars} chars; "
        f"original size {len(text)} chars ...]"
    )


def _make_unicode_safe_output_fn(fn: Callable[[str], None]) -> Callable[[str], None]:
    """Wrap an output_fn so UnicodeEncodeError doesn't kill the agent loop.

    R-tier R1 PHASE B iter-1 fix (2026-05-03): on Windows the default
    stdout encoding is cp1252, which can't encode emoji like ƒo. (U+2705).
    The model frequently emits emoji in summary blocks. Without this
    wrapper, the very first call to `print(response.text)` raises
    UnicodeEncodeError and the entire agent loop dies ƒ?" even though
    the agent's actual work (chart.png + report.docx) was done.

    Strategy:
    1. Try the callable as-is (no behavior change on UTF-8 terminals).
    2. On UnicodeEncodeError, fall back to the terminal's encoding with
       errors='replace' (preserves more chars than ASCII).
    3. If THAT still fails, ASCII-replace as the final safe net.

    This is symmetric to Block H's input-side surrogate sanitization ƒ?"
    Bedrock returns valid UTF-8; the *terminal* may not be configured
    for it. Pure platform robustness; no behavioral change otherwise.
    """
    import sys as _sys

    def _safe(text: str) -> None:
        try:
            fn(text)
            return
        except UnicodeEncodeError:
            pass
        try:
            enc = getattr(_sys.stdout, "encoding", None) or "ascii"
            fn(text.encode(enc, "replace").decode(enc, "replace"))
        except (UnicodeEncodeError, LookupError):
            fn(text.encode("ascii", "replace").decode("ascii"))
    return _safe


# ============================================================
# QueryEngine
# ============================================================

class QueryEngine:
    """Main agent loop. Owns the message buffer + iteration budget for one
    `run()` call. Sub-agents (Phase 9) will share the same IterationBudget
    instance via `forkSubagent`-style construction.
    """

    DEFAULT_MAX_TURNS = 50  # v4 in-place default; UI may override per call.

    def __init__(
        self,
        client: Any,
        max_turns: int = DEFAULT_MAX_TURNS,
        budget: Optional[IterationBudget] = None,
        on_stop_check: Optional[Callable[[], bool]] = None,
        skill_manager: Optional[Any] = None,
        agent_kind: str = "parent",
        session_id: Optional[str] = None,
        synthetic_output_tool_name: Optional[str] = None,
        max_structured_output_retries: int = 3,
    ):
        """Construct a QueryEngine.

        Args:
            client: BedrockClient (or mock with the same `chat(...)` shape).
            max_turns: hard upper bound on turns per `run()` call.
            budget: shared IterationBudget. If None, a fresh one is created.
            on_stop_check: optional callable returning True if the user has
                requested a stop (notebook UX). Phase 11 wires this to the
                Stop button.
            skill_manager: optional `skills.manager.SkillManager`. When
                supplied, the engine (a) injects the active skill body into
                the dynamic tail of the system prompt, and (b) appends a
                Hermes-filtered "skills relevant to this task" reminder to
                the first user turn (Phase 10 wiring contract ƒ?" Codex
                Phase-10 BLOCKER fix). When None, no skill machinery runs
                ƒ?" preserves Phase 1-8 backwards compatibility for tests.
        """
        self.client = client
        self.max_turns = max(1, int(max_turns))
        self.budget = budget if budget is not None else IterationBudget()
        self.on_stop_check = on_stop_check
        self.skill_manager = skill_manager
        # Block B: per-agent attribution key for TOKENS.add(). "parent" by
        # default; sub-agents pass their type-string ("build", "explore",
        # "verify", etc.) via subagent.spawn._new_child_engine.
        self.agent_kind = agent_kind
        # Block B: session_id used by AUDIT.log on each tool dispatch.
        # Block B+ will swap this to the SessionManager-issued id; for
        # now we mint a process-lifetime id so audit lines are at least
        # grouped per-engine.
        if session_id is None:
            import uuid as _uuid
            session_id = _uuid.uuid4().hex[:12]
        self.session_id = session_id

        # Block M-2: structured-output retry guard (PORT_LOG #084 ƒ?" Runnable
        # QueryEngine.ts:1004-1048 countToolCalls + MAX_STRUCTURED_OUTPUT_RETRIES).
        # When `synthetic_output_tool_name` is set, the engine counts how many
        # times that tool appears in self.messages during this run() and
        # halts with stop_reason="error_max_structured_output_retries" at the
        # retry limit. Default name=None disables the check (v5 has no
        # built-in structured-output mode; this is a hook for future support).
        self.synthetic_output_tool_name = synthetic_output_tool_name
        self.max_structured_output_retries = max(1, int(max_structured_output_retries))

        self.messages: List[Dict[str, Any]] = []
        # Tool names that have been "discovered" via tool_search this run.
        # Their schemas are added to per-turn `tools=` API param until the
        # run ends. v5 does NOT persist discovery across `run()` calls ƒ?" the
        # set is fresh each user message (matches Runnable's per-message
        # discovered set).
        self._discovered_tool_names: Set[str] = set()
        # Block F2 ƒ?" per-run BudgetTracker for iteration-budget auto-continuation.
        # Created lazily inside run() when CONFIG.enable_token_budget_continuation
        # is True; reset each run() so continuation state never leaks across
        # user messages.
        self._budget_tracker: Optional[Any] = None

    # ------------------------------------------------------------
    # Public entry: run(...)
    # ------------------------------------------------------------

    def run(
        self,
        user_message: str,
        system_prompt: str,
        tools: List[Any],
        plan_mode: bool = False,
        output_fn: Callable[[str], None] = print,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> QueryResult:
        """Execute the agent loop until a stop condition is reached.

        See class docstring for the IN-SCOPE / OUT-OF-SCOPE list.
        """
        # R-tier R1 PHASE B iter-1 fix: wrap output_fn to swallow
        # UnicodeEncodeError on Windows cp1252 stdout. The agent emits
        # valid UTF-8 (e.g. ƒo. U+2705 in summary blocks); a raw print()
        # on a default-Windows console crashes the entire loop. Block H
        # surrogate sanitization handles INPUT; this is the symmetric
        # output-side robustness. Codex R1 PhaseB iter-1 APPROVE_FIX.
        output_fn = _make_unicode_safe_output_fn(output_fn)
        # Codex Phase-08 finding (high): the discovered-tool set MUST be reset
        # at each run() entry. The contract docstring promises "fresh each
        # user message" but the previous version persisted it across runs,
        # which would silently widen the per-turn tools= payload on later
        # runs. Lock test: test_discovered_tools_reset_between_runs.
        self._discovered_tool_names = set()
        # Block B+ Codex finding #1 (HIGH) lock: reset the per-run cost
        # over-budget warning flag so subsequent run() calls re-emit the
        # warning once each (instead of staying silent for the lifetime
        # of the engine).
        self._warned_over_budget = False
        # Block C ƒ?" exec-limit gate (PS#7 fix) + repetition detector.
        # Counters live on the QueryEngine. Codex iter-1 finding #3:
        # unconditional reset at run() entry so counters DON'T leak
        # across run() calls (the v4 contract; sub-agent dispatch is
        # the only legitimate cross-run sharing path, handled via
        # parent_engine forwarding).
        self._exec_call_count = 0  # bash + python_exec only
        self._recent_tool_calls: list = []  # [(name, args_hash), ...]
        # Block F2 ƒ?" fresh BudgetTracker per run() so continuation state
        # never leaks across user messages.
        self._budget_tracker = None
        # Block M-1 (PORT_LOG #085) ƒ?" Runnable QueryEngine.ts:238 verbatim:
        # discoveredSkillNames.clear() at run() entry. Prevents
        # path/trigger-activated skills from contaminating the next user
        # message's flow. Best-effort; never blocks run() on missing
        # skill_manager.
        try:
            if self.skill_manager is not None and hasattr(
                self.skill_manager, "_pending_activations"
            ):
                with self.skill_manager._pending_lock:
                    self.skill_manager._pending_activations.clear()
        except Exception:
            pass
        # Block M-2 (PORT_LOG #084) ƒ?" capture the baseline structured-output
        # tool-call count at run-entry. Calls THIS run = current_count -
        # baseline. Initial count when the run starts may be non-zero if
        # messages were carried over from a previous run() (continued
        # session); the retry limit is per-run, not per-session.
        self._initial_structured_output_calls = (
            count_tool_calls(self.messages, self.synthetic_output_tool_name)
            if self.synthetic_output_tool_name else 0
        )

        # Block C+ ƒ?" message rate limit (v4 :8731-8740). Lives on the
        # engine so per-session caps are tracked.
        if not hasattr(self, "_rate_limiter"):
            from ui.approval_dialog import RateLimiter
            from runtime.config import CONFIG as _CFG
            self._rate_limiter = RateLimiter(
                max_per_minute=getattr(_CFG, "max_user_messages_per_minute", 100),
                max_per_session=getattr(_CFG, "max_user_messages_per_session", 1500),
            )
        _rate_msg = self._rate_limiter.check()
        if _rate_msg is not None:
            return QueryResult(
                text=_rate_msg,
                messages=list(self.messages),
                stop_reason="rate_limited",
                turns_used=0,
                budget_used=self.budget.used(),
                error=_rate_msg,
            )

        # Append user turn (Bedrock requires alternation; merge into trailing
        # user if needed ƒ?" matches v4 sagemaker_agent.py:8744).
        if self.messages and self.messages[-1].get("role") == "user":
            prev = self.messages[-1]
            prev_content = prev.get("content", "")
            if isinstance(prev_content, str):
                prev["content"] = prev_content + "\n\n" + user_message
            elif isinstance(prev_content, list):
                prev_content.append({"type": "text", "text": user_message})
            else:
                self.messages.append({"role": "user", "content": user_message})
        else:
            self.messages.append({"role": "user", "content": user_message})

        # Defer-import to avoid circular import at module-load.
        from tools.registry import (
            PLAN_MODE_ALLOWED_TOOLS,
            apply_tool_search_deferral,
            find_tool_by_name,
        )
        from tools.tool_search import tool_search_discovered_names

        # Phase 10 wiring (Codex BLOCKER fix): if a SkillManager is bound to
        # this engine, inject (a) the active skill body into the dynamic
        # tail of the system prompt and (b) a Hermes-filtered "skills
        # relevant to this task" reminder onto the first user turn so the
        # model sees the suggestions. The Hermes filter passes the visible
        # tool names so skills with `requires_tools` are pruned when the
        # required tools aren't currently available.
        effective_system_prompt = system_prompt
        # Block G3 ƒ?" coordinator-mode prompt augmentation. Default OFF.
        # Only the PARENT agent gets the coordinator block (sub-agents are
        # workers, not coordinators). Best-effort try/except.
        try:
            from runtime.config import CONFIG as _CFG_G3
            if (
                getattr(_CFG_G3, "coordinator_mode_enabled", False)
                and self.agent_kind == "parent"
            ):
                from coordinator.system_prompt import get_coordinator_system_prompt
                from coordinator.user_context import get_coordinator_user_context
                effective_system_prompt = (
                    effective_system_prompt + "\n\n" + get_coordinator_system_prompt()
                )
                # Block G3 iter-2 (Codex iter-1 finding #3 MEDIUM lock):
                # PORT_LOG #093 promises G3-2 user context is INJECTED into
                # the coordinator's first user message. Append it to the
                # trailing user turn (the user_message we just appended).
                # This mirrors Runnable's QueryEngine.ts:302-307 behavior.
                _ws = getattr(_CFG_G3, "workspace", None)
                _ctx_block = get_coordinator_user_context(workspace=_ws)
                if _ctx_block and self.messages and self.messages[-1].get("role") == "user":
                    _last = self.messages[-1]
                    _existing = _last.get("content")
                    _injection = "\n\n" + _ctx_block
                    if isinstance(_existing, str):
                        _last["content"] = _existing + _injection
                    elif isinstance(_existing, list):
                        _last["content"] = list(_existing) + [
                            {"type": "text", "text": _ctx_block}
                        ]
        except Exception as _g3_exc:
            logging.warning(
                "[coordinator-prompt] %s: %s",
                type(_g3_exc).__name__, _g3_exc,
            )

        if self.skill_manager is not None:
            try:
                active_block = self.skill_manager.get_active_skill_prompt(
                    session_id=self.session_id,
                )
                if active_block:
                    # Block G3 iter-2 (Codex iter-1 finding #1 HIGH lock):
                    # append to the existing effective_system_prompt (which
                    # already carries the coordinator block when that's on);
                    # don't reset to bare `system_prompt + active_block` ƒ?"
                    # that would silently discard the coordinator block.
                    effective_system_prompt = effective_system_prompt + active_block
                visible_tool_names = {t.name for t in tools}
                relevant = self.skill_manager.discover_relevant(
                    user_message, active_tools=visible_tool_names,
                )
                if relevant:
                    reminder = (
                        "\n\n# Skills Relevant to This Task\n"
                        "Consider using: " + ", ".join(relevant) +
                        "\nUse the `skill` tool to activate one if it matches."
                    )
                    last_user = self.messages[-1]
                    content = last_user.get("content")
                    if isinstance(content, str):
                        last_user["content"] = content + reminder
                    elif isinstance(content, list):
                        content.append({"type": "text", "text": reminder})
            except Exception as exc:  # noqa: BLE001 ƒ?" skill machinery never raises into agent loop
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

            # Block M-2 (PORT_LOG #084) ƒ?" structured-output retry-limit
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

            # Budget gate ƒ?" shared with sub-agents (Phase 9).
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
                # Promote previously-discovered tools from deferred ƒ+' visible.
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
            try:
                response = self.client.chat(
                    messages=turn_messages,
                    system=effective_system_prompt,
                    tools=_build_tools_api_payload(visible_tools),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    thinking_enabled=thinking_enabled,
                    thinking_budget=thinking_budget,
                )
            except Exception as exc:  # noqa: BLE001 ƒ?" classify and surface
                category, recovery, debug = ErrorClassifier.classify(exc)
                output_fn(f"[Bedrock {category}: {debug}]")
                if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
                    stop_reason = "context_overflow"
                else:
                    stop_reason = "fatal_error"
                return QueryResult(
                    text=last_text,
                    messages=list(self.messages),
                    stop_reason=stop_reason,
                    turns_used=turns_used,
                    budget_used=self.budget.used(),
                    error=f"{category}: {debug}",
                )

            turns_used += 1

            # Block B (PORT_LOG #039+#040): record token usage + per-agent
            # attribution. "parent" or sub-agent type-string. Best-effort ƒ?"
            # never break the agent loop if the singleton import fails.
            try:
                from runtime.tokens import TOKENS as _TOKENS
                _TOKENS.add(
                    response.usage or {},
                    model_id=getattr(self.client, "model_id", None),
                    agent_kind=self.agent_kind,
                )
                try:
                    from runtime.audit import AUDIT as _AUDIT_CHAT
                    _AUDIT_CHAT.log(
                        session_id=self.session_id,
                        action="chat_response",
                        tool_name="(engine)",
                        parameters={
                            "turn": turns_used,
                            "response": {
                                "usage": response.usage or {},
                                "thinking": getattr(response, "thinking", "") or "",
                                "text": response.text or "",
                                "stop_reason": getattr(response, "stop_reason", ""),
                                "tool_calls": [
                                    {
                                        "id": getattr(c, "id", ""),
                                        "name": getattr(c, "name", ""),
                                        "input": getattr(c, "input", {}),
                                    }
                                    for c in (response.tool_calls or [])
                                ],
                            },
                        },
                        result_summary=(
                            f"stop={getattr(response, 'stop_reason', '')}; "
                            f"tools={len(response.tool_calls or [])}; "
                            f"text_chars={len(response.text or '')}; "
                            f"thinking_chars={len(getattr(response, 'thinking', '') or '')}"
                        ),
                        user_approved=False,
                    )
                except Exception:
                    pass
                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
                # warning. v4 sagemaker_agent.py:8787 prints
                #   `[Cost ${session_cost} passed budget ${limit} ƒ?" continuing.]`
                # NOT a hard halt ƒ?" per user 2026-05-03 update to plan v3,
                # v5 matches v4 UX: warn and continue. True hard halt is at
                # cloud-budget level (AWS Budget Action / GCP).
                from runtime.config import CONFIG as _CFG
                limit = getattr(_CFG, "session_cost_limit", 0.0)
                # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
                # the warning (`>` would skip parity-100% cases).
                if limit > 0 and _TOKENS.session_cost >= limit:
                    if not getattr(self, "_warned_over_budget", False):
                        output_fn(
                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
                            f"budget ${limit:.2f} ƒ?" continuing.]"
                        )
                        self._warned_over_budget = True
            except Exception:
                pass

            # Append assistant turn (text + tool_use blocks, plus thinking).
            assistant_content = self._build_assistant_content(response)
            self.messages.append({"role": "assistant", "content": assistant_content})

            if response.text:
                last_text = response.text

            # Block A ƒ?" auto-compact gate. Per-turn check: if the
            # message buffer has crossed the 80% threshold AND the
            # circuit breaker allows another attempt, run Compactor.
            try:
                from core.compactor import Compactor, AUTO_COMPACT
                from runtime.config import CONFIG as _CFG_AC
                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
                if Compactor.should_compact(self.messages, _max_ctx):
                    _ok, _why = AUTO_COMPACT.try_attempt()
                    if _ok:
                        _result = Compactor.run(self.client, self.messages, _max_ctx)
                        if _result.success:
                            output_fn(
                                f"[auto-compact] saved "
                                f"{_result.tokens_before - _result.tokens_after:,} "
                                f"tokens; continuing."
                            )
                            self.messages = _result.messages_after
                    else:
                        # Cooldown / cap message ƒ?" log once per turn, no
                        # spam since try_attempt returns reason text.
                        output_fn(f"[auto-compact skipped: {_why}]")
            except Exception:
                pass

            # Stop conditions: end_turn / no tool_use blocks ƒ+' final answer.
            if not response.tool_calls:
                # Block F2 ƒ?" auto-continuation under iteration budget. Only
                # parent agents (not sub-agents) and only when CONFIG flag
                # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
                # halt has priority inside check_iteration_budget().
                try:
                    from runtime.config import CONFIG as _CFG_F2
                    if getattr(_CFG_F2, "enable_token_budget_continuation", False):
                        from core.budget_continuation import (
                            check_iteration_budget,
                            create_budget_tracker,
                            ContinueDecision,
                            StopDecision,
                        )
                        if self._budget_tracker is None:
                            self._budget_tracker = create_budget_tracker()
                        _is_sub = self.agent_kind != "parent"
                        _sc = 0.0
                        try:
                            from runtime.tokens import TOKENS as _TOKENS_F2
                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
                        except Exception:
                            _sc = 0.0
                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
                        decision = check_iteration_budget(
                            self._budget_tracker,
                            iter_used=self.budget.used(),
                            iter_total=self.budget.total(),
                            is_subagent=_is_sub,
                            session_cost=_sc,
                            session_cost_limit=_scl,
                        )
                        if isinstance(decision, ContinueDecision):
                            # Surface the assistant's interim text + nudge to keep
                            # working. Continuing the for-loop re-invokes Bedrock.
                            if response.text:
                                output_fn(response.text)
                            self.messages.append({
                                "role": "user",
                                "content": decision.nudge_message,
                            })
                            continue
                        # Codex iter-1 finding #1 lock: surface StopDecision
                        # telemetry. Runnable logs the equivalent completion
                        # event at query.ts:1343-1354. v5 routes through the
                        # AUDIT singleton so /diffs / /regression forensics
                        # can observe budget-driven stops; stderr-style
                        # logging.info also surfaces it for headless runs.
                        if isinstance(decision, StopDecision):
                            _ce = decision.completion_event
                            _reason = decision.reason or ""
                            if _ce is not None or _reason in {"cost_cap", "diminishing", "above_threshold"}:
                                logging.info(
                                    "[budget-continuation] stop reason=%s event=%s",
                                    _reason, _ce,
                                )
                                try:
                                    from runtime.audit import AUDIT as _AUDIT_F2
                                    _AUDIT_F2.log(
                                        session_id=self.session_id,
                                        action="budget_continuation_stop",
                                        tool_name="(engine)",
                                        parameters={"reason": _reason},
                                        result_summary=str(_ce or ""),
                                        user_approved=False,
                                    )
                                except Exception:
                                    pass
                except Exception as _f2_exc:
                    # Codex iter-1 finding #2 lock: best-effort wrap MUST
                    # surface a diagnostic when F2 is opt-in enabled ƒ?" silent
                    # fail-closed makes opt-in users see "no auto-continue"
                    # with zero clue why. logging.warning matches the
                    # cost-runtime warning pattern at [Cost ...] above.
                    logging.warning(
                        "[budget-continuation] %s: %s",
                        type(_f2_exc).__name__, _f2_exc,
                    )

                stop_reason = "end_turn"
                if response.text:
                    output_fn(response.text)
                break

            # Tool dispatch ƒ?" emit one tool_result per tool_use call.
            tool_results: List[Dict[str, Any]] = []
            for call in response.tool_calls:
                tool = find_tool_by_name(tools, call.name)
                if tool is None:
                    # Unknown tool name ƒ?" return error to model so it can
                    # recover (v4 parity: dispatch never raises).
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": f"Error: unknown tool '{call.name}'",
                        "is_error": True,
                    })
                    # Block B (Codex finding #2 HIGH lock): every dispatch
                    # path ƒ?" including unknown-tool ƒ?" must be audited so
                    # forensics can see what the model attempted to call.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="tool_unknown",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=f"unknown tool '{call.name}'",
                            user_approved=False,
                        )
                    except Exception:
                        pass
                    continue

                # Plan-mode dispatch gate ƒ?" strict allowlist by name (v4
                # PLAN_MODE_ALLOWED_TOOLS, sagemaker_agent.py:9390 + 6905).
                # Codex Phase-08 finding (medium): the prior version exempted
                # `always_load=True` tools, which would let `tool_search`
                # itself (or any future always_load mutating tool) execute
                # in plan mode despite v4 forbidding it. The allowlist is
                # defense-in-depth on top of registry filtering: even if a
                # disallowed mutating tool reaches dispatch (e.g. discovered
                # via tool_search after enabled=True), it cannot run.
                # Lock test: test_engine_plan_mode_blocks_always_load_mutating_tool.
                if plan_mode and call.name not in PLAN_MODE_ALLOWED_TOOLS:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": (
                            f"Error: tool '{call.name}' is not in "
                            "PLAN_MODE_ALLOWED_TOOLS; blocked in plan mode."
                        ),
                        "is_error": True,
                    })
                    # Block B (Codex finding #2 HIGH lock): plan-mode
                    # block is an audit-relevant security event.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="plan_mode_blocked",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=(
                                f"plan-mode allowlist blocked '{call.name}'"
                            ),
                            user_approved=False,
                        )
                    except Exception:
                        pass
                    continue

                # Block C ƒ?" exec-limit gate (PS#7 fix). Only bash +
                # python_exec count toward this limit. v4 verbatim
                # message at sagemaker_agent.py:9482-9489 ƒ?" preserved
                # so the model can recover by switching to non-counted
                # tools.
                if call.name in {"bash", "python_exec"}:
                    from runtime.config import CONFIG as _CFG
                    cap = getattr(_CFG, "max_exec_calls_per_session", 200)
                    if self._exec_call_count >= cap:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": call.id,
                            "content": (
                                f"Blocked: bash + python_exec call limit "
                                f"reached ({cap}/session). "
                                "OTHER TOOLS STILL WORK: read_file, grep, "
                                "glob, edit_file, write_file, notebook_edit, "
                                "task, ask_user, view_image, web_fetch are "
                                "NOT counted by this limit."
                            ),
                            "is_error": True,
                        })
                        continue

                # Block C ƒ?" repetition detector. Same (tool_name,
                # args_hash) appearing 3+ times in the last 6 calls is
                # almost always a stuck loop. v4 sagemaker_agent.py:9156-9180
                # threshold=2 (block on 3rd duplicate).
                import hashlib as _hashlib
                import json as _json
                try:
                    _args_hash = _hashlib.sha256(
                        _json.dumps(call.input or {}, sort_keys=True, default=str).encode()
                    ).hexdigest()[:12]
                except Exception:
                    _args_hash = ""
                _key = (call.name, _args_hash)
                _recent = self._recent_tool_calls[-6:]
                if _recent.count(_key) >= 2:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": (
                            f"Blocked: same call to '{call.name}' with "
                            f"identical arguments has been issued 3 times "
                            "in a row. This is almost always a stuck loop. "
                            "Try a different approach, different arguments, "
                            "or use ask_user to clarify."
                        ),
                        "is_error": True,
                    })
                    continue
                # Track this call (rolling window of last 12).
                self._recent_tool_calls.append(_key)
                if len(self._recent_tool_calls) > 12:
                    self._recent_tool_calls = self._recent_tool_calls[-12:]

                # Block C ƒ?" JSON-repair tool args before dispatch. If
                # Bedrock streamed back malformed JSON in tool_use.input,
                # try to recover gracefully instead of falling through
                # to a tool-side type error.
                _repaired_input = call.input
                if isinstance(call.input, str):
                    # When tool_use.input arrives as a JSON string (some
                    # Bedrock variants), parse + repair before dispatch.
                    try:
                        from security.json_repair import repair_tool_call_arguments
                        _repaired_input = repair_tool_call_arguments(call.input)
                    except Exception:
                        _repaired_input = {}

                # Block C+ ƒ?" approval gate. When CONFIG.require_tool_approval
                # AND tool.requires_approval are BOTH True (and we're not
                # in mock_mode for tests), surface a PermissionDialog
                # and block until decided. always-allow decisions stick
                # on CONFIG._always_allowed[tool.name]. Mock detection
                # checks the BedrockClient instance (not CONFIG) because
                # tests construct their own client without flipping the
                # global CONFIG.mock_mode flag.
                from runtime.config import CONFIG as _CFG_AT
                _is_mock = bool(
                    getattr(_CFG_AT, "mock_mode", False)
                    or getattr(self.client, "mock_mode", False)
                )
                if (not _is_mock
                        and getattr(_CFG_AT, "require_tool_approval", False)
                        and getattr(tool, "requires_approval", False)):
                    if not hasattr(_CFG_AT, "_always_allowed"):
                        _CFG_AT._always_allowed = {}
                    if not _CFG_AT._always_allowed.get(call.name):
                        try:
                            from ui.approval_dialog import PermissionDialog
                            _model_reason = ""
                            if isinstance(_repaired_input, dict):
                                _model_reason = str(_repaired_input.get("reason", ""))
                            # Block C+ Codex iter-1 finding #1 (HIGH) lock:
                            # for edit_file / write_file, render an inline
                            # diff for the approval body so users see the
                            # actual change before approving (Phase-4
                            # ADR-010 commitment).
                            _diff_html = None
                            if call.name in {"edit_file", "write_file"} and isinstance(_repaired_input, dict):
                                try:
                                    from ui.diff_widget import (
                                        render_inline_diff,
                                        render_new_file_diff,
                                    )
                                    import os as _os_diff
                                    _fp = _repaired_input.get("file_path", "")
                                    if call.name == "edit_file":
                                        _old = _repaired_input.get("old_string", "")
                                        _new = _repaired_input.get("new_string", "")
                                        if _fp and _os_diff.path.isfile(_fp):
                                            with open(_fp, "r", encoding="utf-8", errors="replace") as _f:
                                                _before = _f.read()
                                            _after = _before.replace(_old, _new, 1)
                                            _diff_html = render_inline_diff(_fp, _before, _after)
                                    else:  # write_file
                                        _content = _repaired_input.get("content", "")
                                        _mode = _repaired_input.get("mode", "write")
                                        if _fp and _os_diff.path.isfile(_fp) and _mode == "write":
                                            with open(_fp, "r", encoding="utf-8", errors="replace") as _f:
                                                _before = _f.read()
                                            _diff_html = render_inline_diff(_fp, _before, _content)
                                        else:
                                            _diff_html = render_new_file_diff(_fp, _content)
                                except Exception:
                                    _diff_html = None
                            _dlg = PermissionDialog(
                                tool_name=call.name,
                                parameters=_repaired_input or {},
                                reason=_model_reason,
                                diff_html=_diff_html,
                            )
                            _result = _dlg.prompt()
                            if not _result.approved:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": call.id,
                                    "content": (
                                        f"User denied approval for "
                                        f"`{call.name}`: {_result.reason}"
                                    ),
                                    "is_error": True,
                                })
                                continue
                            # Approved ƒ?" sticky if user clicked Always.
                        except Exception as _approval_exc:
                            logging.warning(
                                f"approval gate failed: {_approval_exc}; "
                                "defaulting to deny"
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": call.id,
                                "content": (
                                    f"Approval gate error for `{call.name}`; "
                                    f"defaulting to deny."
                                ),
                                "is_error": True,
                            })
                            continue

                # Execute. Tool implementations may raise; we trap and surface
                # the error to the model rather than the human user.
                # `parent_engine` is passed for Phase 9 task tool ƒ?" the sub-agent
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
                except Exception as exc:  # noqa: BLE001 ƒ?" surface to model
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
                            session_id=self.session_id,
                            action="tool_error",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=f"{type(exc).__name__}: {exc}",
                            user_approved=False,
                        )
                    except Exception:
                        pass

            # Append the tool_results as a user turn (Bedrock convention).
            self.messages.append({"role": "user", "content": tool_results})

        else:  # for-loop fell through without break
            stop_reason = "max_turns"
            output_fn(f"[Max turns reached: {self.max_turns}]")

        return QueryResult(
            text=last_text,
            messages=list(self.messages),
            stop_reason=stop_reason or "end_turn",
            turns_used=turns_used,
            budget_used=self.budget.used(),
        )

    # ------------------------------------------------------------
    # Internal: assemble assistant turn content from a Bedrock Response
    # ------------------------------------------------------------

    @staticmethod
    def _build_assistant_content(response: Any) -> List[Dict[str, Any]]:
        """Construct a Bedrock-shaped assistant content list from a Response.

        Order: thinking blocks (if any) ƒ+' text ƒ+' tool_use. The thinking
        block is preserved so the next turn's API call carries it back to
        the model (Bedrock requires this for extended thinking continuity).
        """
        blocks: List[Dict[str, Any]] = []
        thinking = getattr(response, "thinking", "") or ""
        if thinking:
            blocks.append({"type": "thinking", "thinking": thinking})
        if response.text:
            blocks.append({"type": "text", "text": response.text})
        for call in response.tool_calls:
            blocks.append({
                "type": "tool_use",
                "id": call.id,
                "name": call.name,
                "input": call.input,
            })
        return blocks

    # ------------------------------------------------------------
    # Internal: deferred-tools system reminder injection
    # ------------------------------------------------------------

    @staticmethod
    def _inject_deferred_reminder(
        messages: List[Dict[str, Any]],
        deferred_names: List[str],
    ) -> List[Dict[str, Any]]:
        """Append a `<system-reminder>` block listing deferred tool names so
        the model knows what's available via tool_search.

        The reminder is injected as a transient text block on the trailing
        user turn ƒ?" it does not mutate `self.messages`, so it does not leak
        into subsequent turns once the model has loaded the schemas it needs.
        """
        if not deferred_names:
            return messages
        reminder = (
            "<system-reminder>\n"
            "The following deferred tools are available via tool_search. Their schemas "
            "are NOT loaded ƒ?" calling them directly will fail. Use tool_search with "
            "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
            + "\n".join(sorted(deferred_names))
            + "\n</system-reminder>"
        )
        # Transient append: copy the trailing user message and add the reminder
        # as an extra text block. If the trailing turn is not user-role, we
        # append a fresh user message ƒ?" but this should never happen because
        # the loop only invokes Bedrock right after a user turn or tool_results.
        out = list(messages)
        if not out or out[-1].get("role") != "user":
            out.append({"role": "user", "content": [{"type": "text", "text": reminder}]})
            return out
        last = dict(out[-1])
        content = last.get("content")
        if isinstance(content, str):
            last["content"] = [
                {"type": "text", "text": content},
                {"type": "text", "text": reminder},
            ]
        elif isinstance(content, list):
            last["content"] = list(content) + [{"type": "text", "text": reminder}]
        else:
            last["content"] = [{"type": "text", "text": reminder}]
        out[-1] = last
        return out


# ============================================================
# Single-turn helper for unit tests
# ============================================================

def run_one_turn(
    client: Any,
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[Any],
    max_tokens: int = 4096,
    temperature: float = 0.0,
    thinking_enabled: bool = False,
    thinking_budget: int = 4096,
) -> Any:
    """Run a single Bedrock invocation with Phase 7 deferral applied.

    Returns the raw `Response` object. Tests use this to assert wiring without
    spinning up the full multi-turn loop.
    """
    from tools.registry import apply_tool_search_deferral

    visible_tools, _deferred = apply_tool_search_deferral(tools, enabled=True)
    return client.chat(
        messages=messages,
        system=system_prompt,
        tools=_build_tools_api_payload(visible_tools),
        max_tokens=max_tokens,
        temperature=temperature,
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
    )
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3370ms:
"""Block A ƒ?" Compactor + auto-compact circuit breaker + Runnable cache_edits.

v5 port of v4's `Compactor` class (compact_v4/MAIN/agent/sagemaker_agent.py
lines 186-635, ~449 LOC). Adapted for v5's nested-package layout. Plus:
  - Auto-compact circuit breaker (Hermes-style cooldown)
  - Runnable cache_edits adaptation (cache_control on prompt sections ƒ?"
    Bedrock equivalent of the Anthropic-direct cache_edits param)
  - B-2 countTokensViaHaikuFallback (deferred from Block B per ADR-021)
  - B+5 recursive advisor sub-cost accounting (deferred from Block B+
    per ADR-022 ƒ?" auxiliary compaction-summary model)

The Compactor is the load-bearing piece for context-window management.
At 80% of max context, `should_compact()` returns True; the chat loop
calls `Compactor.run(messages, client)` which prunes oversized tool
results, asks Bedrock for an LLM summary, and replaces old messages
with the summary + last N messages.

PORT_LOG: see #066-#070.
"""
from __future__ import annotations

import copy
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ============================================================
# CompactionResult
# ============================================================

@dataclass
class CompactionResult:
    """Outcome of a compact() call."""

    success: bool
    summary: str = ""
    messages_after: List[Dict[str, Any]] = field(default_factory=list)
    tokens_before: int = 0
    tokens_after: int = 0
    error: str = ""


# ============================================================
# AutoCompactCircuitBreaker (Hermes-style cooldown)
# ============================================================

class AutoCompactCircuitBreaker:
    """Prevents auto-compact runaway by enforcing a cooldown window.

    Pattern: when auto-compact fires, mark the timestamp. If
    `should_attempt()` is called again within `cooldown_seconds`, return
    False ƒ?" caller must continue without re-compacting. Hermes
    run_agent.py uses this to prevent compact-after-compact loops where
    a freshly-compacted context still trips the 80% trigger because
    the summary itself is large.

    Per Wave-5-DEEP H5 (auto-compact circuit breaker; A28 cache-invariant).
    """

    def __init__(self, cooldown_seconds: int = 30, max_per_session: int = 10):
        # cooldown_seconds=0 is a valid setting (test scenarios + caller
        # who only wants the session cap as a gate). We clamp at >= 0.
        self.cooldown_seconds = max(0, int(cooldown_seconds))
        self.max_per_session = max(1, int(max_per_session))
        self._lock = threading.Lock()
        self._last_attempt: float = 0.0
        self._session_count = 0

    def should_attempt(self) -> Tuple[bool, str]:
        """True iff a compact attempt is allowed right now.

        Returns (allowed, reason). When False, the reason explains why
        (session cap hit / cooldown active) so the caller can surface
        a clear log message. Session cap checked FIRST ƒ?" once exhausted,
        no further attempts make sense regardless of cooldown.
        """
        with self._lock:
            if self._session_count >= self.max_per_session:
                return False, (
                    f"auto-compact session cap reached "
                    f"({self._session_count}/{self.max_per_session})"
                )
            now = time.time()
            since = now - self._last_attempt
            if self._last_attempt > 0 and since < self.cooldown_seconds:
                return False, (
                    f"auto-compact cooldown active "
                    f"({since:.0f}s elapsed, "
                    f"{self.cooldown_seconds}s required)"
                )
            return True, ""

    def record_attempt(self) -> None:
        """Mark a compact attempt ƒ?" caller calls this after a successful
        OR failed compact so cooldown applies either way (a failed
        compact still consumed time + tokens)."""
        with self._lock:
            self._last_attempt = time.time()
            self._session_count += 1

    def reset(self) -> None:
        with self._lock:
            self._last_attempt = 0.0
            self._session_count = 0

    def try_attempt(self) -> Tuple[bool, str]:
        """Atomic check+record: if allowed, record the attempt and
        return (True, ""). If not allowed, return (False, reason)
        without recording. Concurrent callers cannot both pass the
        check before either records ƒ?" this closes the TOCTOU window
        in should_attempt() + record_attempt() that Codex iter-1
        finding #3 (MEDIUM) flagged.
        """
        with self._lock:
            if self._session_count >= self.max_per_session:
                return False, (
                    f"auto-compact session cap reached "
                    f"({self._session_count}/{self.max_per_session})"
                )
            now = time.time()
            since = now - self._last_attempt
            if self._last_attempt > 0 and since < self.cooldown_seconds:
                return False, (
                    f"auto-compact cooldown active "
                    f"({since:.0f}s elapsed, "
                    f"{self.cooldown_seconds}s required)"
                )
            # Atomic record.
            self._last_attempt = now
            self._session_count += 1
            return True, ""


# ============================================================
# Compactor (v4 port)
# ============================================================

class Compactor:
    """Smart context compaction: prune oversized tool results, then
    LLM-summarize old messages, replace with summary + last N.

    Verbatim port of v4 sagemaker_agent.py:186-635 with adaptations:
    - estimate_tokens delegates to runtime/tokens.estimate_message_tokens
      (drops tiktoken dependency for SageMaker-native deployment).
    - create_llm_summary uses v5 BedrockClient.chat() shape.
    - Auxiliary-model routing (v4.9.4 compaction_model) preserved with
      per-agent attribution via TokenTracker.add(agent_kind="advisor")
      ƒ?" this is the B+5 recursive advisor sub-cost accounting that
      ADR-022 deferred from Block B+ to Block A.
    """

    PRUNE_PROTECT_TOKENS = 40_000
    PRUNE_MIN_SAVINGS = 10_000
    SUMMARY_TRIGGER_PERCENT = 0.80
    KEEP_LAST_MESSAGES = 3
    MAX_PTL_RETRIES = 3

    SUMMARY_TOOL_RESULT_THRESHOLD = 8_000
    SUMMARY_TOOL_RESULT_HEAD = 2_000
    SUMMARY_TOOL_RESULT_TAIL = 1_000

    PROTECTED_TOOLS = {"todo_write", "todo_read", "semantic_search"}

    FIXED_OVERHEAD_TOKENS = 6_000

    # Aux client cache (per-process); built lazily.
    _aux_client_cache: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Token estimation
    # --------------------------------------------------------

    @classmethod
    def estimate_tokens(cls, text_or_messages: Any) -> int:
        """Estimate token count for a string OR list of messages.

        Delegates to `runtime.tokens.estimate_message_tokens` for strings
        and `rough_token_count_for_message` for message dicts.
        """
        from runtime.tokens import (
            estimate_message_tokens,
            rough_token_count_for_message,
        )
        if isinstance(text_or_messages, str):
            return estimate_message_tokens(text_or_messages)
        if isinstance(text_or_messages, list):
            return sum(rough_token_count_for_message(m) for m in text_or_messages)
        if isinstance(text_or_messages, dict):
            return rough_token_count_for_message(text_or_messages)
        return 0

    # --------------------------------------------------------
    # Prune oversized tool results
    # --------------------------------------------------------

    @classmethod
    def prune_tool_outputs(
        cls,
        messages: List[Dict[str, Any]],
        max_context: int,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Truncate tool results that are far past PRUNE_PROTECT_TOKENS.

        Keeps the head + tail of each oversized result so the model
        retains some signal but the bulk is removed. Returns
        (pruned_messages, tokens_saved).
        """
        if not messages:
            return messages, 0

        pruned = copy.deepcopy(messages)
        tool_name_map: Dict[str, str] = {}
        # Build tool_use_id ƒ+' tool_name map so we can skip protected tools.
        for msg in pruned:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tool_name_map[item.get("id", "")] = item.get("name", "")

        # Walk most-recent ƒ+' oldest; protect the last PROTECT_TOKENS worth.
        running_tokens = 0
        tokens_saved = 0
        for msg in reversed(pruned):
            content = msg.get("content")
            if not isinstance(content, list):
                running_tokens += cls.estimate_tokens(msg)
                continue
            for block in content:
                if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                    continue
                tool_name = tool_name_map.get(block.get("tool_use_id", ""), "")
                if tool_name in cls.PROTECTED_TOOLS:
                    continue
                inner = block.get("content")
                if isinstance(inner, str):
                    block_tokens = cls.estimate_tokens(inner)
                    running_tokens += block_tokens
                    if running_tokens > cls.PRUNE_PROTECT_TOKENS \
                       and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
                        head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
                        tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
                        new_text = (
                            f"{head}\n... [pruned "
                            f"{len(inner) - len(head) - len(tail):,} chars] ...\n{tail}"
                        )
                        block["content"] = new_text
                        tokens_saved += cls.estimate_tokens(inner) - cls.estimate_tokens(new_text)
                elif isinstance(inner, list):
                    for sub in inner:
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            txt = sub.get("text", "")
                            running_tokens += cls.estimate_tokens(txt)
                            if running_tokens > cls.PRUNE_PROTECT_TOKENS \
                               and len(txt) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
                                head = txt[: cls.SUMMARY_TOOL_RESULT_HEAD]
                                tail = txt[-cls.SUMMARY_TOOL_RESULT_TAIL :]
                                new_text = (
                                    f"{head}\n... [pruned "
                                    f"{len(txt) - len(head) - len(tail):,} chars] ...\n{tail}"
                                )
                                sub["text"] = new_text
                                tokens_saved += cls.estimate_tokens(txt) - cls.estimate_tokens(new_text)
        # Codex Block-A iter-1 finding #2 (MEDIUM) lock: v4 invariant ƒ?"
        # if savings are too small, return ORIGINAL messages (don't
        # accept the fidelity loss for marginal token wins). Per v4
        # PRUNE_MIN_SAVINGS = 10,000 tokens (constant kept above).
        if tokens_saved < cls.PRUNE_MIN_SAVINGS:
            return messages, 0
        return pruned, tokens_saved

    # --------------------------------------------------------
    # Should compact?
    # --------------------------------------------------------

    @classmethod
    def should_compact(cls, messages: List[Dict[str, Any]], max_tokens: int) -> bool:
        """True iff token estimate > 80% of max_tokens (with overhead)."""
        try:
            from runtime.tokens import TOKENS
            overhead = TOKENS.final_context_tokens_from_last_response()
            if overhead == 0:
                overhead = cls.FIXED_OVERHEAD_TOKENS
        except Exception:
            overhead = cls.FIXED_OVERHEAD_TOKENS
        total = cls.estimate_tokens(messages) + overhead
        return total > max_tokens * cls.SUMMARY_TRIGGER_PERCENT

    # --------------------------------------------------------
    # Auxiliary-model routing (B+5 ƒ?" recursive advisor sub-cost)
    # --------------------------------------------------------

    @classmethod
    def _summary_client(cls, main_client) -> Any:
        """Return the client to use for summary generation.

        Per v4.9.4: when CONFIG.compaction_model is set, build a
        Bedrock client for that cheaper auxiliary model so summaries
        don't pay main-model rates. Per ADR-022 / B+5: TOKENS.add()
        with `agent_kind="advisor"` so the auxiliary cost is attributed
        separately in /cost output.
        """
        from runtime.config import CONFIG
        aux_model = (getattr(CONFIG, "compaction_model", "") or "").strip()
        if not aux_model or aux_model == getattr(main_client, "model_id", ""):
            return main_client
        cached = cls._aux_client_cache.get(aux_model)
        if cached is not None:
            return cached
        try:
            from runtime.bedrock_client import BedrockClient
            aux = BedrockClient(
                aux_model,
                getattr(main_client, "region", "ap-southeast-2"),
                getattr(main_client, "mock_mode", False),
            )
            cls._aux_client_cache[aux_model] = aux
            logging.info(f"[COMPACT] Using auxiliary compaction model: {aux_model}")
            return aux
        except Exception as exc:  # noqa: BLE001
            logging.warning(
                f"[COMPACT] Auxiliary model '{aux_model}' init failed; "
                f"using main client: {exc}"
            )
            return main_client

    # --------------------------------------------------------
    # LLM summary
    # --------------------------------------------------------

    @classmethod
    def create_llm_summary(
        cls,
        client: Any,
        messages: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Ask Bedrock to summarize the conversation. Returns None on
        failure. Per v4 verbatim with v5 adaptations:
        - Pre-prune oversized tool results for the summary input.
        - Optionally route through CONFIG.compaction_model (advisor).
        - Attribute advisor tokens via TOKENS.add(agent_kind='advisor').
        """
        from runtime.tokens import TOKENS

        pruned_messages = cls._prune_tool_results_for_summary(messages)
        summary_client = cls._summary_client(client)

        SUMMARY_SYSTEM_PROMPT = (
            "You are summarizing a coding conversation. You have ZERO tools "
            "available ƒ?" do NOT attempt any tool calls. Be concise but "
            "preserve:\n"
            "1. Current task and goal\n"
            "2. Key files modified or read\n"
            "3. Important decisions made\n"
            "4. Where we left off\n"
            "5. What needs to happen next\n"
            "6. Resolved questions\n"
            "7. Pending questions"
        )

        summary_input = list(pruned_messages)
        # Bedrock requires user/assistant alternation.
        if summary_input and summary_input[-1].get("role") == "user":
            summary_input.append({
                "role": "assistant",
                "content": "[Preparing summary...]",
            })
        summary_input.append({
            "role": "user",
            "content": (
                "Summarize the conversation above per the rubric. Be concise."
            ),
        })

        attempts = 0
        while attempts <= cls.MAX_PTL_RETRIES:
            try:
                response = summary_client.chat(
                    messages=summary_input,
                    system=SUMMARY_SYSTEM_PROMPT,
                    tools=None,
                    max_tokens=2000,
                    temperature=0.0,
                )
                if response and response.usage:
                    # B+5 (ADR-022 remap): attribute advisor cost separately.
                    agent_kind = (
                        "advisor"
                        if summary_client is not client
                        else "parent"
                    )
                    TOKENS.add(
                        response.usage,
                        model_id=getattr(summary_client, "model_id", None),
                        agent_kind=agent_kind,
                    )
                if response and response.text:
                    return response.text
                return None
            except Exception as exc:  # noqa: BLE001
                err = str(exc).lower()
                is_ptl = ("prompt" in err and "long" in err) \
                    or "too many tokens" in err
                if not is_ptl:
                    logging.warning(f"[COMPACT] LLM summary failed: {exc}")
                    return None
                attempts += 1
                summary_input = cls._truncate_head_for_ptl_retry(summary_input)
                if not summary_input:
                    logging.warning("[COMPACT] PTL retries exhausted")
                    return None
        return None

    @classmethod
    def _prune_tool_results_for_summary(
        cls,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Cheap pre-LLM pass: drop oversized tool_result bodies."""
        out: List[Dict[str, Any]] = []
        for msg in messages:
            content = msg.get("content")
            if not isinstance(content, list):
                out.append(msg)
                continue
            new_blocks: List[Any] = []
            mutated = False
            for block in content:
                if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                    new_blocks.append(block)
                    continue
                inner = block.get("content")
                if isinstance(inner, str) and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
                    head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
                    tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
                    new_block = dict(block)
                    new_block["content"] = (
                        f"{head}\n... [pruned for summary] ...\n{tail}"
                    )
                    new_blocks.append(new_block)
                    mutated = True
                else:
                    new_blocks.append(block)
            if mutated:
                new_msg = dict(msg)
                new_msg["content"] = new_blocks
                out.append(new_msg)
            else:
                out.append(msg)
        return out

    @classmethod
    def _truncate_head_for_ptl_retry(
        cls,
        messages: List[Dict[str, Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        """Drop the first 25% of messages so PTL retry has a smaller
        input. Returns None when input is already minimal.

        Codex Block-A iter-1 finding #1 (HIGH) lock: Bedrock requires
        message lists to start with role=user. If the head-slice
        produces a list starting with role=assistant, prepend a
        user-marker so the retry doesn't fail Bedrock validation
        (which would early-abort the PTL recovery loop).
        Per v4_compactor_section.txt:189.
        """
        if len(messages) < 4:
            return None
        drop_n = max(1, len(messages) // 4)
        truncated = messages[drop_n:]
        if not truncated:
            return None
        # Guarantee user-first ordering for Bedrock.
        if truncated[0].get("role") != "user":
            truncated = [{
                "role": "user",
                "content": "[continuing from earlier in the conversation]",
            }] + truncated
        return truncated

    # --------------------------------------------------------
    # Compact: replace old messages with summary
    # --------------------------------------------------------

    @classmethod
    def compact(
        cls,
        messages: List[Dict[str, Any]],
        summary: str,
    ) -> List[Dict[str, Any]]:
        """Replace old messages with a summary + last N messages."""
        if not summary:
            return messages
        keep_last = cls.KEEP_LAST_MESSAGES
        recent = messages[-keep_last:] if len(messages) > keep_last else []
        summary_msg = {
            "role": "user",
            "content": (
                f"[CONVERSATION SUMMARY]\n{summary}\n"
                "[END SUMMARY ƒ?" Continuing from here]"
            ),
        }
        return [summary_msg] + recent

    @classmethod
    def run(
        cls,
        client: Any,
        messages: List[Dict[str, Any]],
        max_tokens: int = 200_000,
    ) -> CompactionResult:
        """End-to-end: prune ƒ+' summarize ƒ+' compact. Single entry point."""
        before_tokens = cls.estimate_tokens(messages)
        if not cls.should_compact(messages, max_tokens):
            return CompactionResult(
                success=False,
                error="compact not needed (under 80% trigger)",
                tokens_before=before_tokens,
                tokens_after=before_tokens,
                messages_after=list(messages),
            )
        pruned, _saved = cls.prune_tool_outputs(messages, max_tokens)
        summary = cls.create_llm_summary(client, pruned)
        if not summary:
            return CompactionResult(
                success=False,
                error="LLM summary returned empty",
                tokens_before=before_tokens,
                tokens_after=cls.estimate_tokens(pruned),
                messages_after=pruned,
            )
        new_messages = cls.compact(pruned, summary)
        after_tokens = cls.estimate_tokens(new_messages)
        return CompactionResult(
            success=True,
            summary=summary,
            messages_after=new_messages,
            tokens_before=before_tokens,
            tokens_after=after_tokens,
        )


# ============================================================
# Runnable cache_edits ƒ?" Bedrock cache_control adaptation
# ============================================================

def apply_cache_control_to_blocks(
    blocks: List[Dict[str, Any]],
    cache_break_at: int = -1,
) -> List[Dict[str, Any]]:
    """Apply Bedrock-style `cache_control` to message blocks.

    Bedrock equivalent of Anthropic-direct `cache_edits` (Runnable's
    name): mark the block at `cache_break_at` (default -1 = last) with
    `{"cache_control": {"type": "ephemeral"}}` so prefix-replay works
    on subsequent turns. Block A's compaction output is the natural
    place to set this ƒ?" the summary block becomes the new cache prefix.

    Per Runnable cache_edits.ts (reference) + Hermes A28 cache-invariant
    (no mid-turn cache flips).
    """
    if not blocks:
        return blocks
    if cache_break_at == -1:
        cache_break_at = len(blocks) - 1
    if cache_break_at < 0 or cache_break_at >= len(blocks):
        return blocks
    out = list(blocks)
    target = dict(out[cache_break_at])
    target["cache_control"] = {"type": "ephemeral"}
    out[cache_break_at] = target
    return out


# ============================================================
# B-2 ƒ?" countTokensViaHaikuFallback (deferred from Block B per ADR-021)
# ============================================================

def count_tokens_via_haiku_fallback(
    messages: List[Dict[str, Any]],
    main_client: Any,
) -> Optional[int]:
    """Fallback token counter when BedrockClient.count_tokens is
    unavailable: use Haiku (cheaper) to count tokens via a
    1-token-budget chat call. Returns the input_tokens reported.

    Per Runnable services/tokenEstimation.ts:251-325 (R4 #42).
    Block A consumer: uses this when Compactor needs an accurate
    count and the live client doesn't expose count_tokens (older boto3).
    """
    if main_client is None:
        return None
    if getattr(main_client, "mock_mode", False):
        # In mock mode, use the rough estimator from runtime/tokens.
        from runtime.tokens import rough_token_count_for_message
        return sum(rough_token_count_for_message(m) for m in messages)
    try:
        from runtime.bedrock_client import BedrockClient
        haiku_client = BedrockClient(
            "anthropic.claude-haiku-4-5-20251001-v1:0",
            getattr(main_client, "region", "ap-southeast-2"),
            mock_mode=False,
        )
        # Send a max_tokens=1 call so we get the input usage cheaply.
        response = haiku_client.chat(
            messages=messages,
            system="Token-count fallback. Reply with a single dot.",
            tools=None,
            max_tokens=1,
            temperature=0.0,
        )
        if response and response.usage:
            return int(response.usage.get("input_tokens", 0))
    except Exception as exc:  # noqa: BLE001
        logging.warning(f"haiku-fallback token count failed: {exc}")
    return None


# ============================================================
# Module-level singleton circuit breaker
# ============================================================

AUTO_COMPACT = AutoCompactCircuitBreaker()


__all__ = [
    "Compactor",
    "CompactionResult",
    "AutoCompactCircuitBreaker",
    "AUTO_COMPACT",
    "apply_cache_control_to_blocks",
    "count_tokens_via_haiku_fallback",
]
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
The test file confirms a mismatch between the docstring and the actual run: the implementation is one `agent.run(...)` call with no tools, not the two-turn compaction scenario the header describes. I’m narrowing the engine path now to see exactly when auto-compact is evaluated.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "Compactor|AUTO_COMPACT|should_compact|compact" compact_v5/MAIN/agent/core/query_engine.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"TOKENS\\.add|session_input|session_cost|is_over_budget|cost\" compact_v5/MAIN/agent -g \"*.py\"" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"class Agent|def run\\(\" compact_v5/MAIN/agent/agent.py compact_v5/MAIN/agent -g \"agent.py\"" in D:\Github\sagemaker-coding-agent
 succeeded in 2839ms:
24:- Microcompact / context_collapse — Phase 11 UX (PS Issue #4 widget surface).
25:- 2-stage smart compaction (prune + LLM summary) — Phase 11.
30:  doesn't reset on compact (no compact in Phase 8).
619:            # Block A — auto-compact gate. Per-turn check: if the
621:            # circuit breaker allows another attempt, run Compactor.
623:                from core.compactor import Compactor, AUTO_COMPACT
626:                if Compactor.should_compact(self.messages, _max_ctx):
627:                    _ok, _why = AUTO_COMPACT.try_attempt()
629:                        _result = Compactor.run(self.client, self.messages, _max_ctx)
632:                                f"[auto-compact] saved "
640:                        output_fn(f"[auto-compact skipped: {_why}]")
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2860ms:
compact_v5/MAIN/agent\agent.py:166:        # per-turn output cost) would have no effect because QueryEngine.run
compact_v5/MAIN/agent\agent.py:192:        wants a fresh conversation but still respects the cost ceiling
compact_v5/MAIN/agent\commands.py:11:    /skill apply, /skill reject, /revert, /cost, /context, /status,
compact_v5/MAIN/agent\commands.py:43:  /cost              — session cost summary
compact_v5/MAIN/agent\commands.py:282:# /cost — session cost summary
compact_v5/MAIN/agent\commands.py:285:def cmd_cost(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
compact_v5/MAIN/agent\commands.py:288:    cost = TOKENS.get_cost()
compact_v5/MAIN/agent\commands.py:291:    limit = getattr(CONFIG, "session_cost_limit", 0.0)
compact_v5/MAIN/agent\commands.py:297:        f"Session cost: {cost}",
compact_v5/MAIN/agent\commands.py:318:            f"(based on last response usage). Use /cost for full session view."
compact_v5/MAIN/agent\commands.py:600:    ("/cost", cmd_cost),
compact_v5/MAIN/agent\core\budget_continuation.py:14:  session_cost >= session_cost_limit, halt. Runnable's tokenBudget had no
compact_v5/MAIN/agent\core\budget_continuation.py:15:  cost-cap interaction; v5 adds it because TOKENS.session_cost is a 1st-class
compact_v5/MAIN/agent\core\budget_continuation.py:25:diminishing returns kick in OR cost-cap is hit.
compact_v5/MAIN/agent\core\budget_continuation.py:72:    reason: str = ""  # "complete" | "diminishing" | "above_threshold" | "cost_cap" | "no_budget" | "subagent"
compact_v5/MAIN/agent\core\budget_continuation.py:87:    session_cost: float = 0.0,
compact_v5/MAIN/agent\core\budget_continuation.py:88:    session_cost_limit: float = 0.0,
compact_v5/MAIN/agent\core\budget_continuation.py:92:    Cost-cap halts BEFORE the under-90% check so a near-budget cost can't be
compact_v5/MAIN/agent\core\budget_continuation.py:104:    if session_cost_limit > 0 and session_cost >= session_cost_limit:
compact_v5/MAIN/agent\core\budget_continuation.py:111:                "cost": session_cost,
compact_v5/MAIN/agent\core\budget_continuation.py:112:                "cost_limit": session_cost_limit,
compact_v5/MAIN/agent\core\budget_continuation.py:115:            reason="cost_cap",
compact_v5/MAIN/agent\core\budget.py:11:max_turns times, blowing the cost ceiling. Insurance/audit values
compact_v5/MAIN/agent\core\budget.py:12:predictable cost ceilings per user request. Counter is shared across
compact_v5/MAIN/agent\core\cache.py:168:    invalidated. This is the single most-debugged class of cost-spike
compact_v5/MAIN/agent\core\compactor.py:9:  - B+5 recursive advisor sub-cost accounting (deferred from Block B+
compact_v5/MAIN/agent\core\compactor.py:151:      — this is the B+5 recursive advisor sub-cost accounting that
compact_v5/MAIN/agent\core\compactor.py:293:    # Auxiliary-model routing (B+5 — recursive advisor sub-cost)
compact_v5/MAIN/agent\core\compactor.py:302:        don't pay main-model rates. Per ADR-022 / B+5: TOKENS.add()
compact_v5/MAIN/agent\core\compactor.py:303:        with `agent_kind="advisor"` so the auxiliary cost is attributed
compact_v5/MAIN/agent\core\compactor.py:304:        separately in /cost output.
compact_v5/MAIN/agent\core\compactor.py:344:        - Attribute advisor tokens via TOKENS.add(agent_kind='advisor').
compact_v5/MAIN/agent\core\compactor.py:389:                    # B+5 (ADR-022 remap): attribute advisor cost separately.
compact_v5/MAIN/agent\core\compactor.py:395:                    TOKENS.add(
compact_v5/MAIN/agent\runtime\config.py:34:    # Cost note: Sonnet 4.5 is ~10x the per-token cost of Haiku 4.5, but the
compact_v5/MAIN/agent\runtime\config.py:36:    # (Sonnet), so caching activates earlier and offsets some of the cost on
compact_v5/MAIN/agent\runtime\config.py:37:    # multi-turn sessions. To switch back to Haiku for cost-sensitive runs,
compact_v5/MAIN/agent\runtime\config.py:90:    session_cost_limit: float = 0.0  # 0 = no limit. Warns at 80%, stops at 100%.
compact_v5/MAIN/agent\runtime\config.py:135:    # budget AND not diminishing-returns AND session_cost < session_cost_limit
compact_v5/MAIN/agent\runtime\config.py:228:        "aws_bedrock_only": bool, "disable_local_traces": bool, "session_cost_limit": float,
compact_v5/MAIN/agent\runtime\cleanup_registry.py:10:Uses: TokenTracker cost-flush at exit (B+7); SnapshotManager log flush
compact_v5/MAIN/agent\core\query_engine.py:233:        # Block B: per-agent attribution key for TOKENS.add(). "parent" by
compact_v5/MAIN/agent\core\query_engine.py:302:        # Block B+ Codex finding #1 (HIGH) lock: reset the per-run cost
compact_v5/MAIN/agent\core\query_engine.py:554:                _TOKENS.add(
compact_v5/MAIN/agent\core\query_engine.py:592:                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
compact_v5/MAIN/agent\core\query_engine.py:594:                #   `[Cost ${session_cost} passed budget ${limit} — continuing.]`
compact_v5/MAIN/agent\core\query_engine.py:599:                limit = getattr(_CFG, "session_cost_limit", 0.0)
compact_v5/MAIN/agent\core\query_engine.py:602:                if limit > 0 and _TOKENS.session_cost >= limit:
compact_v5/MAIN/agent\core\query_engine.py:605:                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
compact_v5/MAIN/agent\core\query_engine.py:665:                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
compact_v5/MAIN/agent\core\query_engine.py:668:                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
compact_v5/MAIN/agent\core\query_engine.py:674:                            session_cost=_sc,
compact_v5/MAIN/agent\core\query_engine.py:675:                            session_cost_limit=_scl,
compact_v5/MAIN/agent\core\query_engine.py:696:                            if _ce is not None or _reason in {"cost_cap", "diminishing", "above_threshold"}:
compact_v5/MAIN/agent\core\query_engine.py:718:                    # cost-runtime warning pattern at [Cost ...] above.
compact_v5/MAIN/agent\runtime\env_validation.py:5:cost_limit, retention_days, etc.) so config loaders never crash on
compact_v5/MAIN/agent\runtime\tokens.py:5:- per-agent input/output/cost attribution (B-11 + Plan v3 §Block B)
compact_v5/MAIN/agent\runtime\tokens.py:74:# list price for Haiku 4.5 and Sonnet 4.5. The local cost tracker MUST
compact_v5/MAIN/agent\runtime\tokens.py:306:    """Thread-safe tracker for API token usage, cost, and cache hits per session.
compact_v5/MAIN/agent\runtime\tokens.py:309:    sub-agent token costs can be reported separately while still rolling
compact_v5/MAIN/agent\runtime\tokens.py:310:    up to the same `session_cost` total. Per Plan v3 §Block B + B-11.
compact_v5/MAIN/agent\runtime\tokens.py:346:        self.session_input = 0
compact_v5/MAIN/agent\runtime\tokens.py:354:        self.session_cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:355:        self.last_cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:363:        self.parent_cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:366:        self.subagent_cost: Dict[str, float] = {}
compact_v5/MAIN/agent\runtime\tokens.py:395:            self.session_input += input_tokens
compact_v5/MAIN/agent\runtime\tokens.py:397:            self.session_total = self.session_input + self.session_output
compact_v5/MAIN/agent\runtime\tokens.py:409:            cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:413:                # this, local cost tracker undercounts AWS billing by 10%.
compact_v5/MAIN/agent\runtime\tokens.py:418:                cost = (
compact_v5/MAIN/agent\runtime\tokens.py:424:                self.session_cost += cost
compact_v5/MAIN/agent\runtime\tokens.py:425:                self.last_cost = cost
compact_v5/MAIN/agent\runtime\tokens.py:432:                        f"TokenTracker: no pricing for model '{mid}' — cost will show as $0. "
compact_v5/MAIN/agent\runtime\tokens.py:435:                self.last_cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:441:                self.parent_cost += cost
compact_v5/MAIN/agent\runtime\tokens.py:449:                self.subagent_cost[agent_kind] = (
compact_v5/MAIN/agent\runtime\tokens.py:450:                    self.subagent_cost.get(agent_kind, 0.0) + cost
compact_v5/MAIN/agent\runtime\tokens.py:454:            limit = self._config.session_cost_limit
compact_v5/MAIN/agent\runtime\tokens.py:455:            if limit > 0 and self.session_cost > 0:
compact_v5/MAIN/agent\runtime\tokens.py:456:                pct = self.session_cost / limit
compact_v5/MAIN/agent\runtime\tokens.py:460:                        f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
compact_v5/MAIN/agent\runtime\tokens.py:465:                        f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
compact_v5/MAIN/agent\runtime\tokens.py:472:    def is_over_budget(self) -> bool:
compact_v5/MAIN/agent\runtime\tokens.py:473:        limit = self._config.session_cost_limit
compact_v5/MAIN/agent\runtime\tokens.py:474:        return limit > 0 and self.session_cost >= limit
compact_v5/MAIN/agent\runtime\tokens.py:481:            f"In:{self.session_input:,} Out:{self.session_output:,} "
compact_v5/MAIN/agent\runtime\tokens.py:493:    def get_cost(self) -> str:
compact_v5/MAIN/agent\runtime\tokens.py:494:        cost_str = (
compact_v5/MAIN/agent\runtime\tokens.py:495:            f"${self.session_cost:.4f}"
compact_v5/MAIN/agent\runtime\tokens.py:496:            if self.session_cost < 0.01
compact_v5/MAIN/agent\runtime\tokens.py:497:            else f"${self.session_cost:.2f}"
compact_v5/MAIN/agent\runtime\tokens.py:499:        if self.session_cache_read > 0 and self.session_input > 0:
compact_v5/MAIN/agent\runtime\tokens.py:500:            cache_pct = min(100, (self.session_cache_read / self.session_input) * 100)
compact_v5/MAIN/agent\runtime\tokens.py:502:            cost_str += f" (cache {cache_pct:.0f}% | saved ~${savings:.4f})"
compact_v5/MAIN/agent\runtime\tokens.py:503:        return cost_str
compact_v5/MAIN/agent\runtime\tokens.py:507:            "session_input": self.session_input,
compact_v5/MAIN/agent\runtime\tokens.py:515:            "session_cost_usd": round(self.session_cost, 6),
compact_v5/MAIN/agent\runtime\tokens.py:516:            "last_cost_usd": round(self.last_cost, 6),
compact_v5/MAIN/agent\runtime\tokens.py:519:            "parent_cost_usd": round(self.parent_cost, 6),
compact_v5/MAIN/agent\runtime\tokens.py:522:            "subagent_cost_usd": {k: round(v, 6) for k, v in self.subagent_cost.items()},
compact_v5/MAIN/agent\runtime\tokens.py:528:        Used by Block B+ SessionManager `/resume` to rehydrate cost
compact_v5/MAIN/agent\runtime\tokens.py:529:        across sessions (Runnable cost-tracker.ts:87-175 / R11 N8).
compact_v5/MAIN/agent\runtime\tokens.py:532:            self.session_input = int(stats.get("session_input", 0))
compact_v5/MAIN/agent\runtime\tokens.py:534:            self.session_total = self.session_input + self.session_output
compact_v5/MAIN/agent\runtime\tokens.py:540:            self.session_cost = float(stats.get("session_cost_usd", 0.0))
compact_v5/MAIN/agent\runtime\tokens.py:541:            self.last_cost = float(stats.get("last_cost_usd", 0.0))
compact_v5/MAIN/agent\runtime\tokens.py:544:            self.parent_cost = float(stats.get("parent_cost_usd", 0.0))
compact_v5/MAIN/agent\runtime\tokens.py:547:            self.subagent_cost = {
compact_v5/MAIN/agent\runtime\tokens.py:548:                k: float(v) for k, v in stats.get("subagent_cost_usd", {}).items()
compact_v5/MAIN/agent\runtime\tokens.py:565:            return self.session_input  # cold start fallback
compact_v5/MAIN/agent\runtime\tokens.py:593:# Block B+ (PORT_LOG #054): atexit cost-flush via cleanup_registry.
compact_v5/MAIN/agent\runtime\tokens.py:594:# Per Runnable costHook.ts:6-22 (R11 N14). On normal exit / SIGINT /
compact_v5/MAIN/agent\runtime\tokens.py:595:# SIGTERM, log the final session cost so operators can audit
compact_v5/MAIN/agent\runtime\tokens.py:597:def _flush_cost_on_exit() -> None:
compact_v5/MAIN/agent\runtime\tokens.py:598:    if TOKENS.session_cost > 0:
compact_v5/MAIN/agent\runtime\tokens.py:600:            f"session-final cost: {TOKENS.get_cost()} "
compact_v5/MAIN/agent\runtime\tokens.py:602:            f"in={TOKENS.session_input:,} out={TOKENS.session_output:,})"
compact_v5/MAIN/agent\runtime\tokens.py:608:    _register_cleanup(_flush_cost_on_exit)
compact_v5/MAIN/agent\ui\widgets.py:81:                # Color cue for cost ceiling — red when ≥ 90% consumed.
compact_v5/MAIN/agent\ui\chat_ui.py:307:        # runtime turn ceiling / cost-ceiling guards.
compact_v5/MAIN/agent\skills\manager.py:733:            cost = _estimate_tokens(name + ", ")
compact_v5/MAIN/agent\skills\manager.py:734:            if used + cost + hint_reserve > budget_tokens:
compact_v5/MAIN/agent\skills\manager.py:738:            used += cost
compact_v5/MAIN/agent\subagent\agent_types.py:14:  shared IterationBudget, which is the cost-cap; max_turns is the
compact_v5/MAIN/agent\subagent\agent_types.py:36:# only needs the answer, not surrounding cleanup. Keeps token cost
compact_v5/MAIN/agent\subagent\spawn.py:75:    Block B: `agent_type` is forwarded as `agent_kind` so TOKENS.add()
compact_v5/MAIN/agent\subagent\spawn.py:76:    attributes the child's input/output/cost to the right per-agent
compact_v5/MAIN/agent\tests\integration\test_block_b.py:53:    TOKENS.add({"input_tokens": 100, "output_tokens": 50}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:54:    TOKENS.add({"input_tokens": 200, "output_tokens": 75}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:56:    assert TOKENS.session_input == 300
compact_v5/MAIN/agent\tests\integration\test_block_b.py:150:    TOKENS.add({"input_tokens": 100, "output_tokens": 50}, model_id="test-model", agent_kind="parent")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:151:    TOKENS.add({"input_tokens": 80, "output_tokens": 40}, model_id="test-model", agent_kind="build")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:152:    TOKENS.add({"input_tokens": 60, "output_tokens": 30}, model_id="test-model", agent_kind="explore")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:153:    TOKENS.add({"input_tokens": 50, "output_tokens": 25}, model_id="test-model", agent_kind="parent")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:163:    assert TOKENS.session_input == 290
compact_v5/MAIN/agent\tests\integration\test_block_b.py:165:    # Parent + sum of sub-agent costs == session total.
compact_v5/MAIN/agent\tests\integration\test_block_b.py:166:    parent_cost = TOKENS.parent_cost
compact_v5/MAIN/agent\tests\integration\test_block_b.py:167:    sub_cost_total = sum(TOKENS.subagent_cost.values())
compact_v5/MAIN/agent\tests\integration\test_block_b.py:168:    assert abs(TOKENS.session_cost - (parent_cost + sub_cost_total)) < 1e-6
compact_v5/MAIN/agent\tests\integration\test_block_b.py:206:    TOKENS.add({"input_tokens": 100, "output_tokens": 30}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:207:    TOKENS.add({"input_tokens": 120, "output_tokens": 35}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:208:    TOKENS.add({"input_tokens": 140, "output_tokens": 40}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:211:    assert TOKENS.session_input == 360
compact_v5/MAIN/agent\tests\integration\test_block_b.py:240:    This test costs ~$0.005 worth of Bedrock CountTokens API calls when
compact_v5/MAIN/agent\tests\integration\test_block_b.py:399:    TOKENS.add({
compact_v5/MAIN/agent\tests\integration\test_block_b.py:410:# Wiring lock — TOKENS.add fires on QueryEngine response (mock client)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:415:    user can see /cost reflect work done. Wired in core/query_engine.py
compact_v5/MAIN/agent\tests\integration\test_block_b.py:427:    assert TOKENS.session_input + TOKENS.session_output > 0
compact_v5/MAIN/agent\tests\integration\test_block_b.py:438:    default-config prefix; without stripping, default-path TOKENS.add
compact_v5/MAIN/agent\tests\integration\test_block_b.py:460:def test_au_prefixed_model_records_real_cost():
compact_v5/MAIN/agent\tests\integration\test_block_b.py:461:    """Lock test for Codex iter-1 finding #1 (HIGH): TOKENS.add against
compact_v5/MAIN/agent\tests\integration\test_block_b.py:462:    `au.`-prefixed model id must record a non-zero cost (was $0 before fix).
compact_v5/MAIN/agent\tests\integration\test_block_b.py:466:    `get_geo_multiplier(raw_mid) = 1.10` so the recorded cost is now
compact_v5/MAIN/agent\tests\integration\test_block_b.py:473:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b.py:482:    assert TOKENS.session_cost > 0
compact_v5/MAIN/agent\tests\integration\test_block_b.py:483:    assert abs(TOKENS.session_cost - 0.01155) < 1e-6
compact_v5/MAIN/agent\tests\integration\test_block_b.py:598:    audit event so real-AWS runs can be reviewed per-turn for cost, cache,
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:1:"""Block B+ — SessionManager + cost-limit + AGENT_STATUS auto-load + FileCache.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:7:  T1 test_session_save_load_preserves_cost         save at $2.09 → load → TOKENS.session_cost == 2.09 (PS#5)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:8:  T1 test_session_cost_limit_warns_at_100pct       v5 = warn-and-continue (per user 2026-05-03 Plan v3 update)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:11:  T2 test_subagent_token_attribution               TOKENS.parent_input_tokens > 0 AND subagent["build"] > 0 AND session_cost == sum
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:88:# T1 — Save / load preserves session cost (PS#5)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:91:def test_session_save_load_preserves_cost(tmp_path):
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:92:    """PS#5: session cost must persist across /save → /resume.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:97:    and asserting the singleton ends up at the recorded cost.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:103:    s = sm.create(title="cost-restore")
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:105:    # Simulate a session of work that accumulates cost.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:106:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:110:    expected_cost = TOKENS.session_cost
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:111:    assert expected_cost > 0
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:119:    assert TOKENS.session_cost == 0.0
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:124:    assert abs(TOKENS.session_cost - expected_cost) < 1e-6
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:128:# T1 — session_cost_limit warn-and-continue (per user 2026-05-03)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:131:def test_session_cost_limit_warns_at_100pct(monkeypatch, caplog):
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:142:    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.005)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:146:        # Push session_cost above the limit.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:147:        TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:152:    # is_over_budget reports True, but the tracker did NOT raise; the
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:154:    assert TOKENS.is_over_budget()
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:156:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:161:        "v5 contract: TOKENS.add must NOT raise / refuse after over-budget; "
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:301:    each goes to its own bucket. session_cost == sum of buckets."""
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:305:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:311:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:321:    assert TOKENS.parent_cost > 0
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:322:    assert TOKENS.subagent_cost["build"] > 0
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:325:        TOKENS.session_cost
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:326:        - (TOKENS.parent_cost + sum(TOKENS.subagent_cost.values()))
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:337:    share one cost view."""
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:348:    cost_after_a1 = TOKENS.session_cost
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:350:    cost_after_a2 = TOKENS.session_cost
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:353:    assert cost_after_a2 >= cost_after_a1
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:437:def test_cost_warning_resets_each_run(monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:442:    the session even when costs keep growing."""
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:448:    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.0001)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:454:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:474:def test_cost_warning_fires_on_exact_100_percent(monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:481:    # Force session_cost == session_cost_limit exactly.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:482:    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.001)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:487:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:491:    assert abs(TOKENS.session_cost - 0.001) < 1e-9
compact_v5/MAIN/agent\tests\integration\test_agent_max_tokens_propagation.py:6:output cost) would have no effect because QueryEngine.run defaults to
compact_v5/MAIN/agent\tests\integration\test_block_d.py:11:  - Chat-UI integration: ConsoleChatUI.send("/cost") routes to dispatcher.
compact_v5/MAIN/agent\tests\integration\test_block_d.py:50:        "/revert", "/cost", "/context", "/status",
compact_v5/MAIN/agent\tests\integration\test_block_d.py:77:    assert is_command("/cost")
compact_v5/MAIN/agent\tests\integration\test_block_d.py:135:# T1 — /cost dispatches to TokenTracker
compact_v5/MAIN/agent\tests\integration\test_block_d.py:138:def test_cost_command_includes_session_summary():
compact_v5/MAIN/agent\tests\integration\test_block_d.py:143:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_d.py:147:    cr = dispatch_command("/cost")
compact_v5/MAIN/agent\tests\integration\test_block_d.py:149:    assert "Session cost:" in cr.text
compact_v5/MAIN/agent\tests\integration\test_block_d.py:316:    """ConsoleChatUI.send('/cost') must hit the dispatcher and NOT
compact_v5/MAIN/agent\tests\integration\test_block_d.py:334:    out = ui.send("/cost")
compact_v5/MAIN/agent\tests\integration\test_block_d.py:335:    assert "Session cost:" in out
compact_v5/MAIN/agent\tests\integration\test_block_d.py:336:    assert not invoked["agent_run"], "/cost must NOT invoke agent.run()"
compact_v5/MAIN/agent\tests\integration\test_block_a.py:13:  - B+5 advisor sub-cost attribution via TOKENS.add(agent_kind="advisor").
compact_v5/MAIN/agent\tests\integration\test_block_a.py:289:# B+5 — advisor sub-cost attribution
compact_v5/MAIN/agent\tests\integration\test_block_a.py:292:def test_advisor_cost_attributed_when_aux_model_set(monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_block_a.py:294:    used, summary tokens go into TOKENS.subagent_cost['advisor'].
compact_v5/MAIN/agent\tests\integration\test_block_a.py:323:    # Add some pricing so cost is non-zero (hitchk test pricing fallback)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:328:    # Advisor bucket present (cost may be 0 if aux-model has no pricing,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:9:- test_f2_respects_cost_cap
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:12:  ("F2 auto-continuation respects cost cap + opt-in"):
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:73:def test_check_respects_cost_cap_even_under_90pct():
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:74:    """session_cost >= session_cost_limit → halt even if iter_used < 90%."""
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:86:        session_cost=2.50,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:87:        session_cost_limit=2.00,  # already over cap
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:90:    assert decision.reason == "cost_cap"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:91:    assert decision.completion_event["cost"] == 2.50
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:92:    assert decision.completion_event["cost_limit"] == 2.00
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:93:    # Tracker NOT advanced when cost-capped
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:201:    """F2 reads TOKENS.session_cost; reset before each test for determinism."""
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:282:def test_f2_respects_cost_cap(reset_tokens):
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:283:    """TEST_DESIGN row 3: even if iter_used < 90%, if session_cost >=
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:284:    session_cost_limit → halt without nudge."""
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:292:    _prev_limit = CONFIG.session_cost_limit
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:294:    CONFIG.session_cost_limit = 1.00
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:296:        # Inflate session_cost above the limit BEFORE the run.
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:297:        TOKENS.session_cost = 1.50
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:316:        CONFIG.session_cost_limit = _prev_limit
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:425:    cost-cap, diminishing, above-threshold), the engine must surface its
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:438:    _prev_limit = CONFIG.session_cost_limit
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:440:    CONFIG.session_cost_limit = 1.00
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:443:        TOKENS.session_cost = 1.50  # over cap → StopDecision reason="cost_cap"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:446:            ("text", "Should halt on cost-cap before completion."),
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:457:        # session_id, with reason=cost_cap.
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:466:        assert f2_stops[0]["parameters"]["reason"] == "cost_cap"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:468:        assert "1.5" in f2_stops[0]["result_summary"] or "cost_cap" in f2_stops[0]["result_summary"]
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:471:        CONFIG.session_cost_limit = _prev_limit
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:569:def test_f2_completion_event_includes_pct_for_cost_cap(reset_tokens):
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:570:    """Codex iter-2 finding #2 lock: cost-cap StopDecision.completion_event
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:586:        session_cost=2.50,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:587:        session_cost_limit=2.00,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:590:    assert decision.reason == "cost_cap"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:593:    assert "pct" in ce, "cost-cap completion_event must include pct"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:595:    assert ce["cost"] == 2.50
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:72:      - No max_turns / cost_cap breach.
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:73:      - cost ≤ $0.50.
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:83:    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:90:        CONFIG.session_cost_limit = _R2_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:102:        def _hard_cost_halt():
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:103:            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:104:                TOKENS.session_cost >= _R2_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:110:            on_stop_check=_hard_cost_halt,
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:121:        cost_used = TOKENS.session_cost
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:122:        tokens_in = TOKENS.session_input
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:137:            "cost_usd": round(cost_used, 4),
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:158:        assert cost_used <= _R2_COST_CAP_USD, (
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:159:            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:172:        if saved_cost_limit is not None:
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:173:            CONFIG.session_cost_limit = saved_cost_limit
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:13:  - session_cost_limit enforcement
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:89:      - Total cost <= R1 cap ($1.00).
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:107:    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:114:        CONFIG.session_cost_limit = _R1_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:116:        # Codex Phase A iter-1 cost-risk fix: cap per-turn output.
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:124:        # (Workspace + python AST + bash allowlist + cost cap still enforce
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:134:        # Agent + run with HARD cost halt
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:143:        # Codex Phase A iter-1 cost-risk fix: v5's session_cost_limit is a
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:148:        def _hard_cost_halt():
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:149:            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:150:                TOKENS.session_cost >= _R1_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:158:            on_stop_check=_hard_cost_halt,
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:170:        cost_used = TOKENS.session_cost
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:171:        tokens_in = TOKENS.session_input
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:186:            "cost_usd": round(cost_used, 4),
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:248:        # Assert: cost within R1 cap.
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:249:        assert cost_used <= _R1_COST_CAP_USD, (
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:250:            f"R1 cost ${cost_used:.4f} exceeded cap ${_R1_COST_CAP_USD}. "
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:257:        if saved_cost_limit is not None:
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:258:            CONFIG.session_cost_limit = saved_cost_limit
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:68:    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:77:        CONFIG.session_cost_limit = _R17_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:91:        def _hard_cost_halt():
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:92:            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:93:                TOKENS.session_cost >= _R17_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:101:            on_stop_check=_hard_cost_halt,
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:125:        cost_used = TOKENS.session_cost
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:126:        tokens_in = TOKENS.session_input
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:140:            "cost_usd": round(cost_used, 4),
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:162:        assert cost_used <= _R17_COST_CAP_USD, (
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:163:            f"R17 cost ${cost_used:.4f} exceeded cap ${_R17_COST_CAP_USD}."
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:169:        if saved_cost_limit is not None:
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:170:            CONFIG.session_cost_limit = saved_cost_limit
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:268:    cost. The full ≥3000-token target lands as Phases 9-10 add more tools."""
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:276:    def schemas_token_cost(tools_list):
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:282:    full_cost = schemas_token_cost(full)
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:283:    visible_cost = schemas_token_cost(visible)
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:284:    savings = full_cost - visible_cost
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:20:Total Block J AWS cost when RUN_REAL_BEDROCK=1: ~$0.02.
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:50:# T4 — Zip rebuild + extract + import (no AWS cost)
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:309:    cost more than Block J's $0.02 cap, AND auto-compaction is wired in
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:316:      - costs ~$0.01.
compact_v5/MAIN/agent\tools\skill.py:34:Skill auto-trigger is OFF by default. Skills only load when a user runs `/skill activate <name>` (Phase 11 UX) or you call `skill activate <name>` explicitly. v4 made auto-trigger opt-in (`CONFIG.enable_skill_auto_trigger=True`) because silent skill injection bloated cost.
compact_v5/MAIN/agent\tools\task.py:35:Sub-agents run with a FRESH conversation but share the parent agent's iteration budget — they cannot collectively exceed the cost ceiling. Use a sub-agent when:
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:1:"""Lock test for R-tier R1 PHASE A iter-3 fix: cost tracker applies
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:5:path for Haiku 4.5) would undercount billed cost by 10% locally — letting
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:49:def test_token_cost_applies_geo_premium_for_au_profile():
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:65:        cost_global = t_global.session_cost
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:67:        # Geo tracker — same usage; should be 1.10x cost.
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:71:        cost_geo = t_geo.session_cost
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:73:        assert cost_global > 0, "global cost must be non-zero"
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:74:        assert cost_geo > 0, "geo cost must be non-zero"
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:75:        # Geo cost must be 1.10x global cost (+/- floating-point tolerance).
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:76:        ratio = cost_geo / cost_global
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:78:            f"expected ratio ~1.10; got {ratio:.6f} (global={cost_global}, geo={cost_geo})"
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:84:def test_token_cost_no_premium_for_global_profile():
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:91:    expected_input_cost = (1000 / 1000) * MODEL_COSTS[global_id]["input"]
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:92:    expected_output_cost = (1000 / 1000) * MODEL_COSTS[global_id]["output"]
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:93:    expected_total = expected_input_cost + expected_output_cost
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:101:        assert abs(t.session_cost - expected_total) < 1e-9, (
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:102:            f"global cost expected {expected_total}, got {t.session_cost}"
compact_v5/MAIN/agent\tests\integration\test_block_n.py:138:        "Changing this affects Bedrock concurrency cost — review with care."
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:232:    """Side-channel _<test>_metrics.json populates outcome.cost_usd etc."""
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:240:            "cost_usd": 0.04, "wallclock_s": 12.3,
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:249:        "tokens_in": 5000, "tokens_out": 2000, "cost_usd": 0.04,
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:259:    assert out["cost_usd"] == 0.04
compact_v5/MAIN/agent\tests\integration\test_block_t.py:128:            {"month": "Jan", "sales": 100, "cost": 60},
compact_v5/MAIN/agent\tests\integration\test_block_t.py:129:            {"month": "Feb", "sales": 120, "cost": 70},
compact_v5/MAIN/agent\tests\integration\test_block_t.py:135:        "y_columns": ["sales", "cost"],
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:4:coverage, missing evidence files, and cost-cap drift before another AWS call
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:33:def test_r_tier_gate_matrix_is_complete_and_costed():
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:51:def test_r_tier_gate_detects_cost_cap_excess(tmp_path):
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:56:        json.dumps({"test": "R1", "call": 1, "cost_usd": 2.0}) + "\n",
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:60:    errors = gate.check_costs(tmp_path)
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:61:    assert any("R1 cost" in e for e in errors)
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:70:    assert gate.check_costs(tmp_path) == []
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:117:            "cost_usd": 0.01,
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:163:            "completed": True, "cost_usd": 0.01, "verdict": "GENUINE_PASS",
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3167ms:
compact_v5/MAIN/agent/agent.py:60:class Agent:
compact_v5/MAIN/agent/agent.py:122:    def run(
compact_v5/MAIN/agent\agent.py:60:class Agent:
compact_v5/MAIN/agent\agent.py:122:    def run(
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/query_engine.py | Select-Object -Skip 530 -First 140' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/agent.py | Select-Object -Skip 100 -First 120' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/runtime/tokens.py | Select-Object -Skip 60 -First 110; Get-Content -Path compact_v5/MAIN/agent/runtime/tokens.py | Select-Object -Skip 380 -First 105' in D:\Github\sagemaker-coding-agent
 succeeded in 1938ms:
            except Exception as exc:  # noqa: BLE001 ƒ?" classify and surface
                category, recovery, debug = ErrorClassifier.classify(exc)
                output_fn(f"[Bedrock {category}: {debug}]")
                if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
                    stop_reason = "context_overflow"
                else:
                    stop_reason = "fatal_error"
                return QueryResult(
                    text=last_text,
                    messages=list(self.messages),
                    stop_reason=stop_reason,
                    turns_used=turns_used,
                    budget_used=self.budget.used(),
                    error=f"{category}: {debug}",
                )

            turns_used += 1

            # Block B (PORT_LOG #039+#040): record token usage + per-agent
            # attribution. "parent" or sub-agent type-string. Best-effort ƒ?"
            # never break the agent loop if the singleton import fails.
            try:
                from runtime.tokens import TOKENS as _TOKENS
                _TOKENS.add(
                    response.usage or {},
                    model_id=getattr(self.client, "model_id", None),
                    agent_kind=self.agent_kind,
                )
                try:
                    from runtime.audit import AUDIT as _AUDIT_CHAT
                    _AUDIT_CHAT.log(
                        session_id=self.session_id,
                        action="chat_response",
                        tool_name="(engine)",
                        parameters={
                            "turn": turns_used,
                            "response": {
                                "usage": response.usage or {},
                                "thinking": getattr(response, "thinking", "") or "",
                                "text": response.text or "",
                                "stop_reason": getattr(response, "stop_reason", ""),
                                "tool_calls": [
                                    {
                                        "id": getattr(c, "id", ""),
                                        "name": getattr(c, "name", ""),
                                        "input": getattr(c, "input", {}),
                                    }
                                    for c in (response.tool_calls or [])
                                ],
                            },
                        },
                        result_summary=(
                            f"stop={getattr(response, 'stop_reason', '')}; "
                            f"tools={len(response.tool_calls or [])}; "
                            f"text_chars={len(response.text or '')}; "
                            f"thinking_chars={len(getattr(response, 'thinking', '') or '')}"
                        ),
                        user_approved=False,
                    )
                except Exception:
                    pass
                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
                # warning. v4 sagemaker_agent.py:8787 prints
                #   `[Cost ${session_cost} passed budget ${limit} ƒ?" continuing.]`
                # NOT a hard halt ƒ?" per user 2026-05-03 update to plan v3,
                # v5 matches v4 UX: warn and continue. True hard halt is at
                # cloud-budget level (AWS Budget Action / GCP).
                from runtime.config import CONFIG as _CFG
                limit = getattr(_CFG, "session_cost_limit", 0.0)
                # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
                # the warning (`>` would skip parity-100% cases).
                if limit > 0 and _TOKENS.session_cost >= limit:
                    if not getattr(self, "_warned_over_budget", False):
                        output_fn(
                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
                            f"budget ${limit:.2f} ƒ?" continuing.]"
                        )
                        self._warned_over_budget = True
            except Exception:
                pass

            # Append assistant turn (text + tool_use blocks, plus thinking).
            assistant_content = self._build_assistant_content(response)
            self.messages.append({"role": "assistant", "content": assistant_content})

            if response.text:
                last_text = response.text

            # Block A ƒ?" auto-compact gate. Per-turn check: if the
            # message buffer has crossed the 80% threshold AND the
            # circuit breaker allows another attempt, run Compactor.
            try:
                from core.compactor import Compactor, AUTO_COMPACT
                from runtime.config import CONFIG as _CFG_AC
                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
                if Compactor.should_compact(self.messages, _max_ctx):
                    _ok, _why = AUTO_COMPACT.try_attempt()
                    if _ok:
                        _result = Compactor.run(self.client, self.messages, _max_ctx)
                        if _result.success:
                            output_fn(
                                f"[auto-compact] saved "
                                f"{_result.tokens_before - _result.tokens_after:,} "
                                f"tokens; continuing."
                            )
                            self.messages = _result.messages_after
                    else:
                        # Cooldown / cap message ƒ?" log once per turn, no
                        # spam since try_attempt returns reason text.
                        output_fn(f"[auto-compact skipped: {_why}]")
            except Exception:
                pass

            # Stop conditions: end_turn / no tool_use blocks ƒ+' final answer.
            if not response.tool_calls:
                # Block F2 ƒ?" auto-continuation under iteration budget. Only
                # parent agents (not sub-agents) and only when CONFIG flag
                # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
                # halt has priority inside check_iteration_budget().
                try:
                    from runtime.config import CONFIG as _CFG_F2
                    if getattr(_CFG_F2, "enable_token_budget_continuation", False):
                        from core.budget_continuation import (
                            check_iteration_budget,
                            create_budget_tracker,
                            ContinueDecision,
                            StopDecision,
                        )
                        if self._budget_tracker is None:
                            self._budget_tracker = create_budget_tracker()
                        _is_sub = self.agent_kind != "parent"
                        _sc = 0.0
                        try:
                            from runtime.tokens import TOKENS as _TOKENS_F2
                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
                        except Exception:
                            _sc = 0.0
                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
                        decision = check_iteration_budget(
                            self._budget_tracker,
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2760ms:
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

    def run(
        self,
        message: str,
        tools: Optional[List[Any]] = None,
        output_fn: Callable[[str], None] = print,
    ) -> QueryResult:
        """Execute a single user turn. Returns the `QueryResult`."""
        # Lazy-import to avoid circular import on package init
        from prompt import build_system_prompt, CACHE_BOUNDARY
        from tools import all_registered

        # Block B+: AGENT_STATUS auto-load on first run() call. Reads
        # `<workspace>/AGENT_STATUS.md` (or CONFIG.status_doc) and
        # appends it to the dynamic tail of the system prompt so the
        # agent picks up handoff context from a previous session.
        # Reads file ONCE per Agent instance (idempotent).
        if not self._agent_status_loaded and self._system_prompt is None:
            try:
                self._agent_status_text = _load_agent_status_text()
            except Exception:
                self._agent_status_text = None
            self._agent_status_loaded = True

        system_prompt = self._system_prompt or build_system_prompt(ctx={})
        if self._agent_status_text:
            # Append to the dynamic tail (after CACHE_BOUNDARY) so the
            # cache-aware prefix replay (Block G2 territory) still works.
            if CACHE_BOUNDARY in system_prompt:
                system_prompt = (
                    system_prompt + "\n\n## Handoff: AGENT_STATUS\n\n"
                    + self._agent_status_text
                )
            else:
                system_prompt = (
                    system_prompt + CACHE_BOUNDARY
                    + "\n\n## Handoff: AGENT_STATUS\n\n"
                    + self._agent_status_text
                )
        active_tools = list(tools) if tools is not None else all_registered()

        self._stop_requested = False  # reset between runs
        # R-tier R1 PHASE A iter-2 fix: propagate CONFIG.max_tokens +
        # CONFIG.temperature into the per-call Bedrock kwargs. Without
        # this, R-tier tests that override CONFIG.max_tokens (to cap
        # per-turn output cost) would have no effect because QueryEngine.run
        # defaults to max_tokens=4096 / temperature=0.0.
        from runtime.config import CONFIG as _CFG
        _max_tokens = getattr(_CFG, "max_tokens", 4096)
        _temperature = getattr(_CFG, "temperature", 0.0)
        result = self._engine.run(
            user_message=message,
            system_prompt=system_prompt,
            tools=active_tools,
            plan_mode=self._plan_mode,
            output_fn=output_fn,
            thinking_enabled=self._thinking_enabled,
            thinking_budget=self._thinking_budget,
            max_tokens=_max_tokens,
            temperature=_temperature,
        )
        return result

    def stop(self) -> None:
        """Request the next-turn checkpoint to break out of the loop."""
        self._stop_requested = True

    def clear(self, reset_budget: bool = False) -> None:
        """Reset the conversation buffer. Optionally also reset the budget.

        By default the budget is preserved across `clear()` so a user who
        wants a fresh conversation but still respects the cost ceiling
        doesn't have to pass anything special. Pass `reset_budget=True`
        for the more aggressive reset.
        """
        self._engine.messages = []
        self._engine._discovered_tool_names = set()
        if reset_budget:
            self.budget.reset()

    # ------------------------------------------------------------
    # Read-only views (used by Phase 11 widgets)
    # ------------------------------------------------------------

    @property
    def messages(self) -> list:
        """Snapshot of the conversation buffer (for the chat UI to render)."""
        return list(self._engine.messages)

    @property
    def thinking_enabled(self) -> bool:
        return self._thinking_enabled

    @property
    def thinking_budget(self) -> int:
        return self._thinking_budget

    def set_thinking(self, enabled: bool, budget: Optional[int] = None) -> None:
        """Update thinking-mode settings (PS Issue #4 UI hook)."""
        self._thinking_enabled = bool(enabled)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3483ms:
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "anthropic.claude-haiku-4-5-20251001-v1:0": {"input": 0.001, "output": 0.005},
    "anthropic.claude-sonnet-4-5-20250929-v1:0": {"input": 0.003, "output": 0.015},
    # Phase-1 baseline kept for parity tests
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 0.003, "output": 0.015},
}

# Backwards-compat alias (v4 internal name used inside TokenTracker.add).
_MODEL_PRICING = MODEL_COSTS


# R-tier R1 PHASE A iter-3 fix: AWS Bedrock geo inference profiles
# (au. / us. / eu. / apac.) carry a 10% premium over the global Anthropic
# list price for Haiku 4.5 and Sonnet 4.5. The local cost tracker MUST
# apply this multiplier to avoid undercounting actual AWS spend (which
# would let R-tier tests "pass cap locally" while exceeding it in real
# AWS billing).
#
# Sources (verified 2026-05-03):
#   - AWS Bedrock model card for Haiku 4.5 documents au./us./eu./apac.
#     as Geo Inference IDs.
#   - Anthropic pricing docs
#     (https://platform.claude.com/docs/en/about-claude/pricing) state
#     regional/multi-region endpoints carry a 10% premium over global.
#   - v5 internal corroboration: clara/prompts/HOW_TO_USE.md:31 prices
#     Haiku (AU) at $1.10 confirming the premium.
#
# Global / standard prefix `anthropic.` = 1.0x.
# Geo prefixes `au.` / `us.` / `eu.` / `apac.` = 1.10x.
GEO_INFERENCE_PREMIUM = 1.10
_GEO_PREFIXES = ("au.", "apac.", "us.", "eu.")


def get_geo_multiplier(model_id: str) -> float:
    """Return the price multiplier for a Bedrock model id.

    1.0  = global (`anthropic.<...>`)
    1.10 = geo inference profile (`au.<...>`, `us.<...>`, `eu.<...>`, `apac.<...>`)

    Source: AWS Bedrock model card for Haiku 4.5 documents au./us./eu./apac.
    as Geo Inference IDs. Anthropic pricing
    (https://platform.claude.com/docs/en/about-claude/pricing) states
    regional/multi-region endpoints carry a 10% premium over global.
    v5 internal: clara/prompts/HOW_TO_USE.md:31 prices Haiku (AU) at $1.10
    confirming the premium.
    """
    if not model_id:
        return 1.0
    if any(model_id.startswith(p) for p in _GEO_PREFIXES):
        return GEO_INFERENCE_PREMIUM
    return 1.0


def canonicalize_model_id(model_id: str) -> str:
    """Strip Bedrock cross-region inference prefixes for pricing lookup.

    Bedrock inference-profile prefixes covered:
        au.   ƒ?" Australia (Sydney; ap-southeast-2 default)
        apac. ƒ?" Asia-Pacific
        us.   ƒ?" United States (legacy us-east-1 / us-west-2)
        eu.   ƒ?" Europe (legacy eu-west-1 / eu-central-1)

    Source: AWS Bedrock model card for Haiku 4.5 documents au./us./eu./apac.
    as Geo Inference IDs. Anthropic pricing
    (https://platform.claude.com/docs/en/about-claude/pricing) states
    regional/multi-region endpoints carry a 10% premium over global.
    v5 internal: clara/prompts/HOW_TO_USE.md:31 prices Haiku (AU) at $1.10
    confirming the premium.

    Codex Block-B finding #1 (HIGH) lock: `au.` was missing originally,
    causing CONFIG.model_id="au.anthropic.claude-sonnet-4-5-..." to
    miss MODEL_COSTS entirely and TOKENS to record $0.

    NOTE: stripping the prefix gets the BASE rate from MODEL_COSTS;
    callers must additionally apply `get_geo_multiplier()` to charge the
    +10% premium on geo-inference profiles. R-tier R1 iter-3 fix.
    """
    if not model_id:
        return model_id
    for prefix in _GEO_PREFIXES:
        if model_id.startswith(prefix):
            return model_id[len(prefix):]
    return model_id


# ============================================================
# R4 #14 ƒ?" EXCLUDED_MODELS_FOR_CACHE_BREAK (MUST)
# ============================================================
#
# Haiku-4.5 cache hashing in Bedrock is non-deterministic in a way that
# the prompt-cache-break detector misreads as a "section flipped". Add
# Haiku to the exclusion set so cache-break warnings don't fire on Haiku
# sessions. This is a MUST per Wave-5-DEEP R4 #14.

EXCLUDED_MODELS_FOR_CACHE_BREAK: set = {
    "anthropic.claude-haiku-4-5-20251001-v1:0",
}


# ============================================================
# B-5 ƒ?" IMAGE_MAX_TOKEN_SIZE (R4 #38)
# ============================================================
#
# Per Anthropic billing: each image consumed by Bedrock counts for at
# most 2000 tokens regardless of resolution. Used by the rough estimator
# below.

IMAGE_MAX_TOKEN_SIZE: int = 2000



        agent_kind: attribution bucket. "parent" (default) for the main
        agent loop; sub-agent type-strings ("build", "explore", "verify",
        "plan", "review", "general") for spawned children. The session
        rollup totals always include both.
        """
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
        cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)

        with self._lock:
            self.last_input = input_tokens
            self.last_output = output_tokens
            self.session_input += input_tokens
            self.session_output += output_tokens
            self.session_total = self.session_input + self.session_output
            self.session_cache_read += cache_read
            self.session_cache_write += cache_write
            self.api_calls += 1
            # B-8 ƒ?" record last usage so estimators can walk back.
            self._last_usage_record = dict(usage)

            raw_mid = model_id or self._config.model_id
            mid = canonicalize_model_id(raw_mid)
            if model_id:
                self._model_id = model_id
            pricing = MODEL_COSTS.get(mid)
            cost = 0.0
            if pricing:
                # R-tier R1 PHASE A iter-3 fix: apply geo-inference
                # premium (1.10x) for au./us./eu./apac. profiles. Without
                # this, local cost tracker undercounts AWS billing by 10%.
                geo_mult = get_geo_multiplier(raw_mid)
                base_input = pricing["input"] * geo_mult
                base_output = pricing["output"] * geo_mult
                regular_input = max(0, input_tokens - cache_read - cache_write)
                cost = (
                    (regular_input / 1000) * base_input
                    + (cache_read / 1000) * base_input * 0.1
                    + (cache_write / 1000) * base_input * 1.25
                    + (output_tokens / 1000) * base_output
                )
                self.session_cost += cost
                self.last_cost = cost
            else:
                if not hasattr(self, "_warned_models"):
                    self._warned_models = set()
                if mid not in self._warned_models:
                    self._warned_models.add(mid)
                    logging.warning(
                        f"TokenTracker: no pricing for model '{mid}' ƒ?" cost will show as $0. "
                        f"Add to MODEL_COSTS dict in runtime/tokens.py."
                    )
                self.last_cost = 0.0

            # Per-agent attribution (additive ƒ?" same singleton, separate buckets).
            if agent_kind == "parent":
                self.parent_input_tokens += input_tokens
                self.parent_output_tokens += output_tokens
                self.parent_cost += cost
            else:
                self.subagent_input_tokens[agent_kind] = (
                    self.subagent_input_tokens.get(agent_kind, 0) + input_tokens
                )
                self.subagent_output_tokens[agent_kind] = (
                    self.subagent_output_tokens.get(agent_kind, 0) + output_tokens
                )
                self.subagent_cost[agent_kind] = (
                    self.subagent_cost.get(agent_kind, 0.0) + cost
                )

            # Budget gate (verbatim from v4).
            limit = self._config.session_cost_limit
            if limit > 0 and self.session_cost > 0:
                pct = self.session_cost / limit
                if pct >= 1.0 and not self._budget_stopped:
                    self._budget_stopped = True
                    logging.warning(
                        f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
                    )
                elif pct >= 0.8 and not self._budget_warned:
                    self._budget_warned = True
                    logging.warning(
                        f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
                    )

    # --------------------------------------------------------
    # Read-only views (v4 verbatim)
    # --------------------------------------------------------

    def is_over_budget(self) -> bool:
        limit = self._config.session_cost_limit
        return limit > 0 and self.session_cost >= limit

    def get_last(self) -> str:
        return f"In:{self.last_input:,} Out:{self.last_output:,}"

    def get_session(self) -> str:
        return (
            f"In:{self.session_input:,} Out:{self.session_output:,} "
            f"Total:{self.session_total:,}"
        )

    def get_cache_savings_usd(self) -> float:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "context_max_tokens|max_tokens" compact_v5/MAIN/agent/runtime/config.py compact_v5/MAIN/agent/tests/integration/test_block_a.py compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/runtime/config.py | Select-Object -First 130' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/tests/integration/test_block_a.py | Select-Object -Skip 200 -First 120' in D:\Github\sagemaker-coding-agent
 succeeded in 2712ms:
"""V5 Config ƒ?" verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:1018-1287.

Per ADR-006: Config + JSONC loader is a pure v4 reuse, no Runnable adoption.
Behavior unchanged from v4.10.10 final state. Only structural change: lives in
its own module instead of inline in the monolith.

Source: compact_v4/MAIN/agent/sagemaker_agent.py:1018 (Config dataclass),
        :1152 (_strip_jsonc_comments), :1190 (_load_config_file),
        :1205 (_apply_config_file), :1285 (CONFIG = Config()).

The flat-zip ship surface (Phase 13) collapses this back to root-level
`config.py` next to chat.ipynb; v5 source-tree namespacing is dev-time only.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict


# ============================================================
# CONFIG (verbatim port from v4)
# ============================================================

@dataclass
class Config:
    """Agent configuration."""
    # AWS Settings
    region: str = "ap-southeast-2"  # Sydney
    # Default runtime model: Sonnet 4.5 inference profile.
    # V4.10.1: default switched from Haiku 4.5 to Sonnet 4.5 (user-set, 2026-04-28).
    # Cost note: Sonnet 4.5 is ~10x the per-token cost of Haiku 4.5, but the
    # prompt-cache checkpoint threshold drops from 4096 (Haiku) to 1024 tokens
    # (Sonnet), so caching activates earlier and offsets some of the cost on
    # multi-turn sessions. To switch back to Haiku for cost-sensitive runs,
    # set model_id to "au.anthropic.claude-haiku-4-5-20251001-v1:0" in agent_config.json.
    model_id: str = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # Workspace - use absolute paths to avoid confusion
    workspace: str = os.getcwd()
    sessions_dir: str = os.path.join(os.getcwd(), "sessions")
    audit_dir: str = os.path.join(os.getcwd(), "audit_logs")

    # Limits
    max_turns: int = 60
    max_tokens: int = 16384  # Must be > thinking_budget when thinking enabled
    max_history: int = 20
    max_output_chars: int = 50000  # Matches Runnable's DEFAULT_MAX_RESULT_SIZE_CHARS (50K)
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # Context limits (Claude 3.5 = 200K tokens)
    context_max_tokens: int = 200000

    # Model parameters
    temperature: float = 0.0
    thinking_enabled: bool = False  # Extended thinking OFF by default
    thinking_budget: int = 8192  # Tokens for thinking (1024-16000)

    # Testing
    mock_mode: bool = False  # Set True to test without Bedrock API

    # Security policy
    allowed_paths: list = None  # Additional directories accessible outside workspace
    bash_allow_interpreters: bool = False  # Block python/node via bash (use python_exec)
    bash_allow_docker: bool = False        # If True, allow docker/docker-compose via bash

    # Runtime isolation / execution limits
    execution_mode: str = "local"  # local | docker
    exec_docker_image: str = "python:3.11-slim"
    exec_docker_network_disabled: bool = True
    exec_docker_readonly_rootfs: bool = True
    exec_docker_cpus: float = 1.0
    exec_docker_memory: str = "1g"
    exec_docker_pids_limit: int = 128

    # Operational controls
    require_auth: bool = False
    require_tool_approval: bool = True
    auth_token_env: str = "SAGEMAKER_AGENT_AUTH_TOKEN"
    max_user_messages_per_minute: int = 10
    max_user_messages_per_session: int = 150
    # V4.10.10: 40 -> 200. Old 40-call ceiling was hit mid-task in real SageMaker
    # sessions (real log: agent finished call 40 at 06:29 then spent 5 minutes
    # confused about which tools were still available). Only bash + python_exec
    # are counted; read_file/grep/glob/edit_file/etc are unaffected.
    max_exec_calls_per_session: int = 200
    max_exec_seconds_per_session: int = 900
    session_cost_limit: float = 0.0  # 0 = no limit. Warns at 80%, stops at 100%.
    audit_retention_days: int = 30

    # AWS scope
    aws_bedrock_only: bool = False  # Set True to block all boto3 except bedrock-runtime
    disable_local_traces: bool = False  # Set True for zero local footprint

    # V4.7.1 local-git baseline maintenance
    auto_commit_every: int = 0

    # V4 capabilities
    load_claude_md: bool = True
    enable_prompt_cache: bool = True
    enable_memory_extraction: bool = False
    enable_status_doc: bool = True
    status_doc: str = "AGENT_STATUS.md"
    enable_skills: bool = True
    enable_skill_auto_trigger: bool = False  # V4.9.6: global opt-in; no skill auto-loads by default
    skills_dir: str = "./skills"
    enable_mcp: bool = False
    mcp_servers: Dict = field(default_factory=dict)
    mcp_timeout_seconds: int = 30
    subagent_max_depth: int = 2
    enable_worktree: bool = True

    # V4.9.4: shared iteration budget across parent + sub-agents (hermes pattern).
    # V4.10.10: default bumped 90 -> 600 for normal SageMaker development.
    max_iteration_budget: int = 600

    # V4.9.4: optional auxiliary model for compaction summaries
    compaction_model: str = ""

    # V4.9.5: opt-in self-patching skills
    enable_skill_patching: bool = False

    # V4.10.2: control whether the verify-after-3-edits Verification Contract is
    # MANDATORY or merely SUGGESTED. Default False = suggest-and-let-user-confirm.
    enforce_verify_contract: bool = False

    # V4.10.4: control sub-agent handoff block
    enable_subagent_handoff: bool = True
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2855ms:
compact_v5/MAIN/agent/tests/integration/test_block_a.py:61:    assert Compactor.should_compact(msgs, max_tokens=100_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:63:    assert not Compactor.should_compact(msgs, max_tokens=400_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:70:    assert not Compactor.should_compact(msgs, max_tokens=200_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:184:    result = Compactor.run(client, msgs, max_tokens=100_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:197:    result = Compactor.run(client, msgs, max_tokens=200_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:459:    def fake_run(client_arg, messages, max_tokens=200_000):
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:85:    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:93:        CONFIG.max_tokens = 64
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:176:        if saved_max_tokens is not None:
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:177:            CONFIG.max_tokens = saved_max_tokens
compact_v5/MAIN/agent/runtime/config.py:48:    max_tokens: int = 16384  # Must be > thinking_budget when thinking enabled
compact_v5/MAIN/agent/runtime/config.py:54:    context_max_tokens: int = 200000
compact_v5/MAIN/agent/runtime/config.py:221:        "region": str, "model_id": str, "max_turns": int, "max_tokens": int,
compact_v5/MAIN/agent/runtime/config.py:240:        "context_max_tokens": int,
compact_v5/MAIN/agent/runtime/config.py:267:        if key in ("max_turns", "max_tokens", "max_history", "subagent_max_depth") and val < 1:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3439ms:

# ============================================================
# T1 ƒ?" AutoCompactCircuitBreaker
# ============================================================

def test_circuit_breaker_cooldown_blocks_repeated_attempts():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=10, max_per_session=100)
    ok, _ = cb.should_attempt()
    assert ok
    cb.record_attempt()
    ok2, reason = cb.should_attempt()
    assert not ok2
    assert "cooldown" in reason.lower()


def test_circuit_breaker_session_cap():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=0, max_per_session=2)
    cb.record_attempt()
    cb.record_attempt()
    ok, reason = cb.should_attempt()
    assert not ok
    assert "session cap" in reason.lower()


def test_circuit_breaker_reset():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=10, max_per_session=2)
    cb.record_attempt()
    cb.record_attempt()
    assert not cb.should_attempt()[0]
    cb.reset()
    assert cb.should_attempt()[0]


# ============================================================
# T1 ƒ?" apply_cache_control_to_blocks
# ============================================================

def test_apply_cache_control_marks_last_ephemeral():
    from core.compactor import apply_cache_control_to_blocks

    blocks = [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
    out = apply_cache_control_to_blocks(blocks)
    assert "cache_control" not in out[0]
    assert out[1]["cache_control"] == {"type": "ephemeral"}


def test_apply_cache_control_at_specific_index():
    from core.compactor import apply_cache_control_to_blocks

    blocks = [{"type": "text", "text": str(i)} for i in range(3)]
    out = apply_cache_control_to_blocks(blocks, cache_break_at=0)
    assert out[0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in out[1]
    assert "cache_control" not in out[2]


def test_apply_cache_control_empty_list():
    from core.compactor import apply_cache_control_to_blocks
    assert apply_cache_control_to_blocks([]) == []


# ============================================================
# B-2 ƒ?" count_tokens_via_haiku_fallback
# ============================================================

def test_count_tokens_haiku_fallback_in_mock_mode():
    from core.compactor import count_tokens_via_haiku_fallback
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    msgs = [{"role": "user", "content": "hello world"}]
    n = count_tokens_via_haiku_fallback(msgs, client)
    assert isinstance(n, int)
    assert n > 0


def test_count_tokens_haiku_fallback_handles_none_client():
    from core.compactor import count_tokens_via_haiku_fallback
    assert count_tokens_via_haiku_fallback([], None) is None


# ============================================================
# B+5 ƒ?" advisor sub-cost attribution
# ============================================================

def test_advisor_cost_attributed_when_aux_model_set(monkeypatch):
    """When CONFIG.compaction_model is set AND a different aux client is
    used, summary tokens go into TOKENS.subagent_cost['advisor'].
    Closes the B+5 deferral from ADR-022."""
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient, Response
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG

    # Set up: main client + auxiliary client (we mock the aux build).
    main_client = BedrockClient(model_id="main-model", region="us-east-1", mock_mode=True)
    aux_client = BedrockClient(model_id="aux-model", region="us-east-1", mock_mode=True)

    monkeypatch.setattr(CONFIG, "compaction_model", "aux-model")
    Compactor._aux_client_cache = {}  # reset cache

    # Spy on _summary_client to verify aux is selected.
    monkeypatch.setattr(
        Compactor, "_summary_client",
        classmethod(lambda cls, mc: aux_client),
    )

    def fake_aux_chat(*args, **kwargs):
        return Response(
            text="advisor-built summary",
            usage={"input_tokens": 500, "output_tokens": 100},
        )

    monkeypatch.setattr(aux_client, "chat", fake_aux_chat)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py -Pattern \"result = agent.run|assert \\(\\\"5\\\"|tokens_in >|CONFIG.context_max|_LOREM_LINES|def test_r2|CONFIG.session_cost_limit|require_tool_approval|max_turns=4\"" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path compact_v5/MAIN/agent/core/query_engine.py -Pattern "auto-compact gate|should_compact|Compactor.run|if not response.tool_calls|TOKENS.add|session_cost_limit"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path compact_v5/MAIN/agent/runtime/config.py -Pattern "context_max_tokens|max_tokens|session_cost_limit|require_tool_approval"' in D:\Github\sagemaker-coding-agent
2026-05-03T23:21:56.926744Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 1.9 seconds
Output:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 
Select-String : A positional parameter cannot be found that accepts argument '5\|tokens_in 
>|CONFIG.context_max|_LOREM_LINES|def test_r2|CONFIG.session_cost_limit|require_tool_approval|max_turns=4'.
At line:2 char:1
+ Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compac ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Select-String], ParameterBindingException
    + FullyQualifiedErrorId : PositionalParameterNotFound,Microsoft.PowerShell.Commands.SelectStringCommand
 

 exited 1 in 1855ms:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 
Select-String : A positional parameter cannot be found that accepts argument '5\|tokens_in 
>|CONFIG.context_max|_LOREM_LINES|def test_r2|CONFIG.session_cost_limit|require_tool_approval|max_turns=4'.
At line:2 char:1
+ Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compac ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Select-String], ParameterBindingException
    + FullyQualifiedErrorId : PositionalParameterNotFound,Microsoft.PowerShell.Commands.SelectStringCommand
 

 succeeded in 2646ms:

compact_v5\MAIN\agent\core\query_engine.py:233:        # Block B: per-agent attribution key for TOKENS.add(). "parent" 
by
compact_v5\MAIN\agent\core\query_engine.py:554:                _TOKENS.add(
compact_v5\MAIN\agent\core\query_engine.py:599:                limit = getattr(_CFG, "session_cost_limit", 0.0)
compact_v5\MAIN\agent\core\query_engine.py:619:            # Block A - auto-compact gate. Per-turn check: if the
compact_v5\MAIN\agent\core\query_engine.py:626:                if Compactor.should_compact(self.messages, _max_ctx):
compact_v5\MAIN\agent\core\query_engine.py:629:                        _result = Compactor.run(self.client, 
self.messages, _max_ctx)
compact_v5\MAIN\agent\core\query_engine.py:645:            if not response.tool_calls:
compact_v5\MAIN\agent\core\query_engine.py:668:                        _scl = float(getattr(_CFG_F2, 
"session_cost_limit", 0.0))
compact_v5\MAIN\agent\core\query_engine.py:675:                            session_cost_limit=_scl,


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3356ms:

compact_v5\MAIN\agent\runtime\config.py:48:    max_tokens: int = 16384  # Must be > thinking_budget when thinking 
enabled
compact_v5\MAIN\agent\runtime\config.py:54:    context_max_tokens: int = 200000
compact_v5\MAIN\agent\runtime\config.py:80:    require_tool_approval: bool = True
compact_v5\MAIN\agent\runtime\config.py:90:    session_cost_limit: float = 0.0  # 0 = no limit. Warns at 80%, stops at 
100%.
compact_v5\MAIN\agent\runtime\config.py:135:    # budget AND not diminishing-returns AND session_cost < 
session_cost_limit
compact_v5\MAIN\agent\runtime\config.py:221:        "region": str, "model_id": str, "max_turns": int, "max_tokens": 
int,
compact_v5\MAIN\agent\runtime\config.py:227:        "require_auth": bool, "require_tool_approval": bool,
compact_v5\MAIN\agent\runtime\config.py:228:        "aws_bedrock_only": bool, "disable_local_traces": bool, 
"session_cost_limit": float,
compact_v5\MAIN\agent\runtime\config.py:240:        "context_max_tokens": int,
compact_v5\MAIN\agent\runtime\config.py:267:        if key in ("max_turns", "max_tokens", "max_history", 
"subagent_max_depth") and val < 1:


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py -Pattern "_LOREM_LINES|def test_r2|CONFIG.session_cost_limit|CONFIG.max_tokens|require_tool_approval|max_turns=4|result = agent.run|tokens_in > 50_000|five"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py -Pattern '\"5\" in result.text'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path compact_v5/MAIN/agent/core/compactor.py -Pattern "SUMMARY_TRIGGER_PERCENT|KEEP_LAST_MESSAGES|def should_compact|def run"' in D:\Github\sagemaker-coding-agent
 succeeded in 1901ms:

compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:48:_LOREM_LINES = 2700
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:66:def test_r2_compaction_under_load(tmp_path, monkeypatch):
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:86:    saved_require_approval = getattr(CONFIG, 
"require_tool_approval", None)
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:90:        CONFIG.session_cost_limit = _R2_COST_CAP_USD
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:93:        CONFIG.max_tokens = 64
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:94:        CONFIG.require_tool_approval = False
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:109:            max_turns=4,
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:113:        recap = (_LOREM_LINE + "\n") * _LOREM_LINES
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:118:        result = agent.run(prompt, tools=[])
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:135:            "preamble_lines": _LOREM_LINES,
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:153:        # Different verbalizations OK ("5", "5.", "Five", "= 
5").
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:155:        assert ("5" in result.text) or ("five" in text_l), (
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:164:        assert tokens_in > 50_000, (
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:173:            CONFIG.session_cost_limit = saved_cost_limit
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:177:            CONFIG.max_tokens = saved_max_tokens
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:179:            CONFIG.require_tool_approval = 
saved_require_approval


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2632ms:

compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:155:        assert ("5" in result.text) or ("five" in text_l), (


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3348ms:

compact_v5\MAIN\agent\core\compactor.py:157:    SUMMARY_TRIGGER_PERCENT = 0.80
compact_v5\MAIN\agent\core\compactor.py:158:    KEEP_LAST_MESSAGES = 3
compact_v5\MAIN\agent\core\compactor.py:280:    def should_compact(cls, messages: List[Dict[str, Any]], max_tokens: 
int) -> bool:
compact_v5\MAIN\agent\core\compactor.py:290:        return total > max_tokens * cls.SUMMARY_TRIGGER_PERCENT
compact_v5\MAIN\agent\core\compactor.py:497:        keep_last = cls.KEEP_LAST_MESSAGES
compact_v5\MAIN\agent\core\compactor.py:509:    def run(


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
One more important detail emerged: `CONFIG.context_max_tokens` defaults to `200_000`, so the auto-compact threshold is about `160_000` estimated tokens, not `80_000`. The current ~78K input is below the actual gate, so even the post-response compaction check will not fire.
codex
**Axis A: REJECT**
The design does not exercise compaction. In [test_r2_compact.py](</mnt/data?>) the test sends one ~78K-token prompt, but auto-compact checks `Compactor.should_compact(...)` against `CONFIG.context_max_tokens=200_000`, so the real trigger is ~160K estimated tokens. Current R2 is below that and ends after the first model response.

The assertion that `"5" in result.text` is also loose. Use an exact-ish regex such as `^\s*(5|five)[\.\s]*$`. This test could also pass if most of the preamble were dropped, as long as the final question survived.

Setup is mostly fine, but if this becomes a real compaction test it should reset `AUTO_COMPACT` and probably reset `TOKENS` in `finally` to avoid cross-test leakage.

**Axis B: APPROVE WITH CAVEAT**
For the current single-call design, cost control is acceptable: ~78K input on AU Haiku 4.5 is about `$0.086`, `max_tokens=64` bounds output, `max_turns=4` bounds accidental loops, and `session_cost_limit=$0.50` is wired through `on_stop_check`.

Caveat: if R2 is changed to force compaction, the compaction summary is an additional Bedrock call. Recompute the cap before running; a two-large-turn design plus summary could approach `$0.40-$0.50`.

**Axis C: REJECT**
Current R2 provides empirical evidence for large Bedrock input handling and `TokenTracker` accumulation of 50K+ input tokens. It does not provide empirical evidence for Block A compaction, cache-edits invariants, safe message cutting, or “post-compact next Bedrock call succeeds.”

**PRE-FLIGHT VERDICT: REJECT**

Do not run AWS for this as “R2 compaction.” Required fixes:

1. Either rename/scope it to “large input sanity + TokenTracker” and remove Block A claims, or make it actually cross the compaction threshold.
2. Add an assertion that compaction occurred, for example captured `[auto-compact]`, `Compactor.run` call count, `TOKENS.api_calls >= 2`, or final `agent.messages` containing `[CONVERSATION SUMMARY]`.
3. Add a post-compaction follow-up call that must answer correctly from the compacted buffer.
4. Tighten the final answer assertion to exact `5` / `five`.
5. Reset `AUTO_COMPACT` and token/config state cleanly around the test.
tokens used
54,431
**Axis A: REJECT**
The design does not exercise compaction. In [test_r2_compact.py](</mnt/data?>) the test sends one ~78K-token prompt, but auto-compact checks `Compactor.should_compact(...)` against `CONFIG.context_max_tokens=200_000`, so the real trigger is ~160K estimated tokens. Current R2 is below that and ends after the first model response.

The assertion that `"5" in result.text` is also loose. Use an exact-ish regex such as `^\s*(5|five)[\.\s]*$`. This test could also pass if most of the preamble were dropped, as long as the final question survived.

Setup is mostly fine, but if this becomes a real compaction test it should reset `AUTO_COMPACT` and probably reset `TOKENS` in `finally` to avoid cross-test leakage.

**Axis B: APPROVE WITH CAVEAT**
For the current single-call design, cost control is acceptable: ~78K input on AU Haiku 4.5 is about `$0.086`, `max_tokens=64` bounds output, `max_turns=4` bounds accidental loops, and `session_cost_limit=$0.50` is wired through `on_stop_check`.

Caveat: if R2 is changed to force compaction, the compaction summary is an additional Bedrock call. Recompute the cap before running; a two-large-turn design plus summary could approach `$0.40-$0.50`.

**Axis C: REJECT**
Current R2 provides empirical evidence for large Bedrock input handling and `TokenTracker` accumulation of 50K+ input tokens. It does not provide empirical evidence for Block A compaction, cache-edits invariants, safe message cutting, or “post-compact next Bedrock call succeeds.”

**PRE-FLIGHT VERDICT: REJECT**

Do not run AWS for this as “R2 compaction.” Required fixes:

1. Either rename/scope it to “large input sanity + TokenTracker” and remove Block A claims, or make it actually cross the compaction threshold.
2. Add an assertion that compaction occurred, for example captured `[auto-compact]`, `Compactor.run` call count, `TOKENS.api_calls >= 2`, or final `agent.messages` containing `[CONVERSATION SUMMARY]`.
3. Add a post-compaction follow-up call that must answer correctly from the compacted buffer.
4. Tighten the final answer assertion to exact `5` / `five`.
5. Reset `AUTO_COMPACT` and token/config state cleanly around the test.
