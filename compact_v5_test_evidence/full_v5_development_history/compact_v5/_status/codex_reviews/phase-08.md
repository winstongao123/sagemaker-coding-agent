OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.3-codex
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: medium
reasoning summaries: none
session id: 019ddd63-2773-7d21-b9e5-a96bdb6ee271
--------
user
You are reviewing PHASE 08 of v5 — SageMaker-native re-implementation of Runnable Claude Code.

CONTEXT
- Repo: D:/Github/sagemaker-coding-agent (branch: v5-build)
- Phase: Phase 8 — QueryEngine + retry + errors + IterationBudget
- Goal (V5_PLAN.md §Phase 8): Wire main loop, retry, error message generators. Acceptance: end-to-end mock test (tool_use → tool runs → final answer) AND tool_search deferred-loading round-trip works.
- Constraints v5 MUST honor: Bedrock-only, no GitHub network, python_exec sandbox, .ipynb workflow, must coexist with v4 unchanged.

FILES IN THIS PHASE (read them before reviewing):
- compact_v5/MAIN/agent/core/__init__.py            (re-exports public surface)
- compact_v5/MAIN/agent/core/budget.py              (NEW: IterationBudget, PORT_LOG #016)
- compact_v5/MAIN/agent/core/errors.py              (NEW: BedrockErrorCategory + ErrorClassifier extracted from runtime/bedrock_client.py, PORT_LOG #017)
- compact_v5/MAIN/agent/core/retry.py               (NEW: RetryPolicy extracted, PORT_LOG #018)
- compact_v5/MAIN/agent/core/query_engine.py        (NEW: ~400 LOC main loop, PORT_LOG #019)
- compact_v5/MAIN/agent/runtime/bedrock_client.py   (MODIFIED: now re-imports core.errors + core.retry instead of inlining; class identity is asserted by test_runtime_bedrock_client_re_exports_match)
- compact_v5/MAIN/agent/tests/unit/test_budget.py        (7 tests)
- compact_v5/MAIN/agent/tests/unit/test_errors.py        (10 tests)
- compact_v5/MAIN/agent/tests/unit/test_retry.py         (7 tests)
- compact_v5/MAIN/agent/tests/integration/test_query_engine.py (12 tests)

DOCS UPDATED IN THIS PHASE:
- compact_v5/_status/V5_DESIGN_DECISIONS.md     (ADR-014 for Phase 8 strategy)
- compact_v5/_status/V5_RUNNABLE_PORT_LOG.md    (rows #016-019)
- compact_v5/_status/V5_BUILD_STATUS.md         (Phase 08 IN_PROGRESS → CODE_COMPLETE)
- compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md (Phase 8 entries 8.1-8.6)
- compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md (Phase 8 source entries + Better-than-X rows)
- compact_v5/MAIN/changelogs/CHANGELOG_v5_phase_08.md

RUNNABLE PATTERNS ADOPTED THIS PHASE (porting agent's claims):
| ID  | Runnable / source path                           | v5 target                            | Verdict | Justification                                                       |
|-----|--------------------------------------------------|--------------------------------------|---------|---------------------------------------------------------------------|
| 016 | hermes-agent/run_agent.py:170 (via v4 8190)      | core/budget.py                       | PORT    | Verbatim Hermes-via-v4. Justified by cost ceiling (PS Issue #2).    |
| 017 | (Phase-1 inline -> extracted)                    | core/errors.py                       | PORT    | Byte-equivalent extraction; runtime re-imports same names.          |
| 018 | services/api/withRetry.ts + Phase-1 inline       | core/retry.py                        | ADAPT   | Drops retry-after parsing (constraint=Bedrock).                     |
| 019 | QueryEngine.ts (1295 LOC)                        | core/query_engine.py (~400 LOC)      | ADAPT   | Sync (.ipynb), drops compaction/skills/sub-agent (own phases).      |

PRODUCE TWO VERDICTS.

=== AXIS A — Errors / bugs ===
For each NEW or MODIFIED file:
- Correctness defects (think through the QueryEngine turn loop carefully — message-buffer mutation, role alternation, transient system-reminder handling, tool_use_id matching, plan-mode dispatch gate)
- Phase 7 wiring contract bugs: does the engine actually promote discovered tools into the next turn's tools= payload? Does _discovered_tool_names persist across turns within a run? Does it reset between runs?
- Regressions vs v4 (cite v4 sagemaker_agent.py:line where applicable)
- Security (esp. plan-mode bypass, system-reminder injection that could be confused with model output, tool exception trapping)
- Concurrency / races (IterationBudget under concurrent consumers; QueryEngine is documented as single-run-at-a-time)
- Dead code, TODOs left in
- Test coverage gaps — does the integration test really validate end-to-end Phase 7 round-trip, or could it pass with a broken engine?

Output:
AXIS A VERDICT: PASS | CHANGES_REQUESTED | BLOCKER
Findings: [severity] file:line — description — fix

=== AXIS B — Runnable-fidelity ===
For EACH pattern row above, judge independently. Read the Runnable source before judging.

PATTERN 016: budget.py — FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED
PATTERN 017: errors.py — FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED
PATTERN 018: retry.py — FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED
PATTERN 019: query_engine.py — FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED

For each:
- Source intent (1-2 sentences):
- v5 implementation (1-2 sentences):
- Constraint forcing adaptation (closed list: Bedrock | no-network | python_exec | .ipynb | none):
- Drift risk if any:
- Required change to reach FAITHFUL (if currently DRIFTED):

If you find a pattern in the code NOT listed in the table, flag as UNDECLARED_PATTERN.

Auto-reject rule: FAITHFUL-WITH-JUSTIFIED-ADAPTATION + constraint=none → REJECT.

=== FINAL ===
PHASE 08 OVERALL: APPROVE | APPROVE_WITH_FIXES | REJECT
A-axis: <one-line>
B-axis: <count of FAITHFUL / ADAPTED / DRIFTED>
Required before next phase (Phase 08.5 thin-slice parity gate):
- <bullet>

Be ruthless. The user wants v5 to be better than Runnable, Hermes, LF, AND v4. If you spot drift labeled as "justified" without a real constraint, call it. If you spot the Phase 7 wiring contract being subtly broken (e.g. discovered names lost across turns, or duplicate tools in the payload), call it.

codex
Reviewing Phase 8 now with focus on loop correctness, Phase 7 deferred-tool wiring, and fidelity against the declared Runnable patterns. I’ll read each listed file and the referenced Runnable/v4 sources, then return hard pass/fail verdicts with line-specific findings.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem -Path . -Recurse -File | Where-Object { $_.FullName -match '"'compact_v5\\\\MAIN\\\\agent\\\\core\\\\(__init__|budget|errors|retry|query_engine)\\.py"'$|compact_v5'"\\\\MAIN\\\\agent\\\\runtime\\\\bedrock_client\\.py"'$|compact_v5'"\\\\MAIN\\\\agent\\\\tests\\\\unit\\\\test_(budget|errors|retry)\\.py"'$|compact_v5'"\\\\MAIN\\\\agent\\\\tests\\\\integration\\\\test_query_engine\\.py"'$|compact_v5'"\\\\MAIN\\\\agent\\\\sagemaker_agent\\.py"'$|hermes-agent'"\\\\run_agent\\.py"'$|QueryEngine'"\\.ts"'$|withRetry'"\\.ts"'$'"' } | Select-Object -ExpandProperty FullName" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git rev-parse --abbrev-ref HEAD' in D:\Github\sagemaker-coding-agent
 succeeded in 3407ms:
v5-build

 succeeded in 4421ms:
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\budget.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\errors.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\retry.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\__init__.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\runtime\bedrock_client.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\integration\test_query_engine.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_budget.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_errors.py
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_retry.py
D:\Github\sagemaker-coding-agent\_archive\compare_code\gg-claude-code-runnable\src\QueryEngine.ts
D:\Github\sagemaker-coding-agent\_archive\compare_code\gg-claude-code-runnable\src\services\api\withRetry.ts

codex
I located all Phase 8 files plus Runnable `QueryEngine.ts` and `withRetry.ts`. Next I’m pulling exact line-numbered excerpts, including v4/Hermes references where available, to validate behavior and parity claims.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$files = @(
'"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\__init__.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\budget.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\errors.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\retry.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\query_engine.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\runtime\\bedrock_client.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests\\unit\\test_budget.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests\\unit\\test_errors.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests\\unit\\test_retry.py',
'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests\\integration\\test_query_engine.py',
'D:\\Github\\sagemaker-coding-agent\\_archive\\compare_code\\gg-claude-code-runnable\\src\\QueryEngine.ts',
'D:\\Github\\sagemaker-coding-agent\\_archive\\compare_code\\gg-claude-code-runnable\\src\\services\\api\\withRetry.ts'
)
foreach ("'$f in $files) { Write-Output "`n### $f"; $i=0; Get-Content $f | ForEach-Object { $i++; "{0,5}: {1}" -f $i, $_ } }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-ChildItem -Path D:\\Github\\sagemaker-coding-agent -Recurse -File | Where-Object { "'$_.Name -in @('"'run_agent.py','sagemaker_agent.py') } | Select-Object -ExpandProperty FullName" in D:\Github\sagemaker-coding-agent
 succeeded in 3146ms:
D:\Github\sagemaker-coding-agent\compact_v4\MAIN\agent\sagemaker_agent.py
D:\Github\sagemaker-coding-agent\_archive\compact\sagemaker_agent.py
D:\Github\sagemaker-coding-agent\_archive\compact_v2\MAIN\agent\sagemaker_agent.py
D:\Github\sagemaker-coding-agent\_archive\compact_v3\MAIN\agent\sagemaker_agent.py
D:\Github\sagemaker-coding-agent\_archive\compact_v3\ship\sagemaker_agent.py

 succeeded in 4600ms:

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\__init__.py
    1: """V5 core/ â€” agent loop + retry + errors + budget.
    2: 
    3: Per ADR-014 (Phase 8):
    4:   - core/query_engine.py : main agent loop (Runnable QueryEngine.ts adaptation)
    5:   - core/retry.py        : jittered exponential backoff (Phase-1 RetryPolicy extracted)
    6:   - core/errors.py       : Bedrock error classifier (Phase-1 ErrorClassifier extracted)
    7:   - core/budget.py       : IterationBudget (Hermes pattern via v4)
    8:   - core/cache.py        : prompt-cache block builder + cache-break detection (Phase 6)
    9: 
   10: Phase 7 contract: query_engine MUST call `apply_tool_search_deferral(enabled=True)`
   11: per turn AND extract discovered tool names via `tool_search_discovered_names()`
   12: to wire deferred tools into the next turn's API call.
   13: """
   14: from __future__ import annotations
   15: 
   16: # Re-export the public surface
   17: from .budget import IterationBudget  # noqa: F401
   18: from .errors import BedrockErrorCategory, ErrorClassifier  # noqa: F401
   19: from .retry import RetryPolicy  # noqa: F401
   20: from .query_engine import QueryEngine, run_one_turn  # noqa: F401

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\budget.py
    1: """V5 core/budget.py â€” IterationBudget (Hermes pattern via v4).
    2: 
    3: Per ADR-014: verbatim port of v4's IterationBudget at
    4: `compact_v4/MAIN/agent/sagemaker_agent.py:8190`. v4 itself adopted this
    5: from `D:/Github/hermes-agent/run_agent.py:170` in v4.9.4.
    6: 
    7: PORT_LOG: #016.
    8: 
    9: Why this exists (PS Issue #2):
   10: A parent agent could otherwise spawn N sub-agents that each loop
   11: max_turns times, blowing the cost ceiling. Insurance/audit values
   12: predictable cost ceilings per user request. Counter is shared across
   13: parent + sub-agents (the parent creates one budget at the start of
   14: `run()`; sub-agents inherit the same instance).
   15: 
   16: Phase 11 (notebook UX) will wire the budget's `consume() / remaining()
   17: / used() / total()` methods into an ipywidgets progress bar so the
   18: user can SEE the budget burning down â€” addressing PS Issue #2's
   19: "budget is invisible until exhausted" complaint.
   20: """
   21: from __future__ import annotations
   22: 
   23: import threading
   24: 
   25: 
   26: class IterationBudget:
   27:     """Thread-safe counter shared across a parent agent and its spawned sub-agents.
   28: 
   29:     A parent agent creates one budget at the start of run(); sub-agents inherit
   30:     the same instance. Each LLM turn (success or failure) increments the counter.
   31:     When `consume()` returns False, the agent surfaces a "budget exhausted"
   32:     message and stops cleanly, preserving partial work.
   33:     """
   34: 
   35:     DEFAULT_MAX = 600  # v4.10.10 in-place: 90 -> 600 (Hermes default 90 too tight for SageMaker dev)
   36: 
   37:     def __init__(self, max_iterations: int = DEFAULT_MAX):
   38:         self._max = max(1, int(max_iterations))
   39:         self._used = 0
   40:         self._lock = threading.Lock()
   41: 
   42:     def consume(self) -> bool:
   43:         """Atomically reserve one iteration. Returns False if budget is exhausted."""
   44:         with self._lock:
   45:             if self._used >= self._max:
   46:                 return False
   47:             self._used += 1
   48:             return True
   49: 
   50:     def remaining(self) -> int:
   51:         with self._lock:
   52:             return max(0, self._max - self._used)
   53: 
   54:     def used(self) -> int:
   55:         with self._lock:
   56:             return self._used
   57: 
   58:     def total(self) -> int:
   59:         return self._max
   60: 
   61:     def reset(self) -> None:
   62:         """Reset counter to 0. Tests + manual /reset only â€” not a normal flow."""
   63:         with self._lock:
   64:             self._used = 0

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\errors.py
    1: """V5 core/errors.py â€” Bedrock error classifier (Phase 8 extraction).
    2: 
    3: Per ADR-014: extracted verbatim from Phase-1 `runtime/bedrock_client.py`
    4: (which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).
    5: 
    6: PORT_LOG: #017.
    7: 
    8: Why this lives here in Phase 8 (not Phase 1):
    9: The classifier was bundled with `BedrockClient` in Phase 1 to avoid a
   10: circular Phase-1/Phase-8 dependency. Now that core/ exists, the classifier
   11: gets its own module so:
   12:   - QueryEngine can import without pulling boto3 transitively
   13:   - Tests can exercise classification logic without a Bedrock client
   14:   - Future phases can reuse classifier semantics outside Bedrock invocation
   15: 
   16: Behavior is byte-equivalent with Phase-1. `runtime/bedrock_client.py`
   17: re-imports these names for backwards compatibility (no chat() change).
   18: """
   19: from __future__ import annotations
   20: 
   21: 
   22: class BedrockErrorCategory:
   23:     """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy."""
   24:     THROTTLE = "throttle"  # ThrottlingException, rate-limited
   25:     SERVICE_UNAVAILABLE = "service_unavailable"
   26:     MODEL_NOT_READY = "model_not_ready"
   27:     NETWORK = "network"
   28:     VALIDATION_CACHE = "validation_cache"  # cache_control rejected â€” strip and retry once
   29:     VALIDATION_OTHER = "validation_other"
   30:     CONTEXT_OVERFLOW = "context_overflow"  # prompt-too-long
   31:     ACCESS_DENIED = "access_denied"
   32:     UNKNOWN = "unknown"
   33: 
   34: 
   35: class ErrorClassifier:
   36:     """Classifies Bedrock exceptions into a (category, recovery, debug_msg) triple.
   37: 
   38:     Verbatim port of v4's classifier. Recovery values:
   39:       - "strip_cache_retry": cache_control rejected; strip blocks and retry once
   40:       - "compact_retry":     prompt-too-long; caller should compact and retry
   41:       - "backoff":           transient (throttle/503/network); retry with jitter
   42:       - "no_retry":          permanent (validation/access denied); surface to user
   43:     """
   44: 
   45:     @staticmethod
   46:     def classify(exc: Exception):
   47:         msg_lower = str(exc).lower()
   48:         cls_name = type(exc).__name__.lower()
   49: 
   50:         if "validationexception" in msg_lower and (
   51:             "cache_control" in msg_lower
   52:             or "prompt-caching" in msg_lower
   53:             or "cache" in msg_lower
   54:         ):
   55:             return BedrockErrorCategory.VALIDATION_CACHE, "strip_cache_retry", str(exc)[:200]
   56:         if "validationexception" in msg_lower and (
   57:             "prompt is too long" in msg_lower
   58:             or "too many tokens" in msg_lower
   59:             or "input length" in msg_lower
   60:         ):
   61:             return BedrockErrorCategory.CONTEXT_OVERFLOW, "compact_retry", str(exc)[:200]
   62:         if "validationexception" in msg_lower:
   63:             return BedrockErrorCategory.VALIDATION_OTHER, "no_retry", str(exc)[:200]
   64:         if "throttlingexception" in msg_lower or "rate" in msg_lower:
   65:             return BedrockErrorCategory.THROTTLE, "backoff", str(exc)[:200]
   66:         if "serviceunavailable" in msg_lower or "503" in msg_lower:
   67:             return BedrockErrorCategory.SERVICE_UNAVAILABLE, "backoff", str(exc)[:200]
   68:         if "modelnotready" in msg_lower or "not ready" in msg_lower:
   69:             return BedrockErrorCategory.MODEL_NOT_READY, "backoff", str(exc)[:200]
   70:         if "accessdenied" in msg_lower or "403" in msg_lower or "unauthorized" in msg_lower:
   71:             return BedrockErrorCategory.ACCESS_DENIED, "no_retry", str(exc)[:200]
   72:         if (
   73:             "endpointconnectionerror" in cls_name
   74:             or "connecttimeout" in cls_name
   75:             or "readtimeout" in cls_name
   76:             or "connectionerror" in cls_name
   77:         ):
   78:             return BedrockErrorCategory.NETWORK, "backoff", str(exc)[:200]
   79:         return BedrockErrorCategory.UNKNOWN, "no_retry", str(exc)[:200]

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\retry.py
    1: """V5 core/retry.py â€” jittered exponential backoff (Phase 8 extraction).
    2: 
    3: Per ADR-014: extracted verbatim from Phase-1 `runtime/bedrock_client.py`
    4: (which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).
    5: 
    6: PORT_LOG: #018.
    7: 
    8: Sleep curve:
    9:   attempt 0 -> ~1.0s   (0.7-1.3s with jitter)
   10:   attempt 1 -> ~2.0s   (1.4-2.6s)
   11:   attempt 2 -> ~4.0s   (2.8-5.2s)
   12:   attempt 3 -> ~8.0s   (5.6-10.4s)
   13:   attempt 4 -> stops   (MAX_RETRIES reached)
   14: 
   15: MAX_RETRIES=4 means up to 5 total attempts (initial + 4 retries).
   16: Behavior is byte-equivalent with Phase-1. `runtime/bedrock_client.py`
   17: re-imports these names for backwards compatibility.
   18: """
   19: from __future__ import annotations
   20: 
   21: import random
   22: 
   23: 
   24: class RetryPolicy:
   25:     """Jittered exponential backoff (v4 verbatim)."""
   26:     MAX_RETRIES = 4
   27:     BASE_SECONDS = 1.0
   28:     JITTER_FRACTION = 0.30
   29:     BACKOFF_RECOVERY = {"backoff"}
   30: 
   31:     @staticmethod
   32:     def should_retry(attempt: int, recovery: str) -> bool:
   33:         if attempt >= RetryPolicy.MAX_RETRIES:
   34:             return False
   35:         return recovery in RetryPolicy.BACKOFF_RECOVERY
   36: 
   37:     @staticmethod
   38:     def backoff_seconds(attempt: int) -> float:
   39:         base = RetryPolicy.BASE_SECONDS * (2 ** attempt)
   40:         jitter = base * RetryPolicy.JITTER_FRACTION * (2 * random.random() - 1)
   41:         return max(0.1, base + jitter)

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py
    1: """V5 core/query_engine.py â€” main agent loop (Phase 8 deliverable, ADR-014).
    2: 
    3: Per ADR-014: minimal, focused port of Runnable's `QueryEngine.ts` (1295 LOC)
    4: adapted to the v5 .ipynb shape. v4's monolithic `Agent.run` (~1500 LOC) is
    5: replaced by this ~400 LOC module with explicit IN-SCOPE / OUT-OF-SCOPE.
    6: 
    7: PORT_LOG: #019.
    8: 
    9: IN SCOPE (Phase 8):
   10: - Per-turn loop with end_turn / max_turns / budget exhausted exits.
   11: - IterationBudget gate at the top of each turn (shared with sub-agents).
   12: - Phase 7 deferred-loading wiring contract:
   13:     * `apply_tool_search_deferral(tools, enabled=True)` per turn.
   14:     * `tool_search_discovered_names()` extraction from tool_search results.
   15:     * Discovered names are added to the next turn's tools= API param.
   16: - Tool dispatch via `find_tool_by_name(...).execute(args, context)`.
   17: - tool_use â†’ tool_result message accumulation in the model-visible
   18:   conversation buffer.
   19: - Bedrock invocation through `BedrockClient.chat(...)`.
   20: - System prompt assembly via `prompt.build_system_prompt(ctx)`.
   21: - run_one_turn(...) helper for unit tests (single-turn, no loop).
   22: 
   23: OUT OF SCOPE â€” explicitly deferred to later phases (per ADR-014):
   24: - Microcompact / context_collapse â€” Phase 11 UX (PS Issue #4 widget surface).
   25: - 2-stage smart compaction (prune + LLM summary) â€” Phase 11.
   26: - Skill auto-trigger â€” Phase 10 (`SKILLS.discover_relevant`).
   27: - Plan mode injection of skills into prompt â€” Phase 10.
   28: - Sub-agent forkSubagent â€” Phase 9 (`subagent/spawn.py`).
   29: - File-read state tracking â€” Phase 4 already lands this; engine respects but
   30:   doesn't reset on compact (no compact in Phase 8).
   31: - Diminishing-returns / repetition guard â€” deferred.
   32: - Notebook UX (output_fn callback contract) â€” Phase 11 owns the UI shape;
   33:   Phase 8 takes a `output_fn: Callable[[str], None] = print` so tests can
   34:   capture, but real notebook integration lives in Phase 11.
   35: 
   36: The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
   37: concurrent `run()` calls on the same engine are NOT supported (matches v4).
   38: """
   39: from __future__ import annotations
   40: 
   41: import json
   42: import logging
   43: from dataclasses import dataclass, field
   44: from typing import Any, Callable, Dict, List, Optional, Set, Tuple
   45: 
   46: from .budget import IterationBudget
   47: from .errors import BedrockErrorCategory, ErrorClassifier
   48: 
   49: 
   50: # ============================================================
   51: # Result envelope
   52: # ============================================================
   53: 
   54: @dataclass
   55: class QueryResult:
   56:     """Outcome of a `QueryEngine.run(...)` call.
   57: 
   58:     `text`           â€” final assistant text (last end_turn turn's text block).
   59:     `messages`       â€” full message buffer including the user turn that
   60:                        triggered this call. Caller may discard or persist.
   61:     `stop_reason`    â€” "end_turn" | "max_turns" | "budget_exhausted" |
   62:                        "context_overflow" | "fatal_error".
   63:     `turns_used`     â€” count of model turns executed during this run.
   64:     `budget_used`    â€” IterationBudget.used() snapshot at exit.
   65:     `error`          â€” short message when stop_reason indicates failure.
   66:     """
   67:     text: str = ""
   68:     messages: List[Dict[str, Any]] = field(default_factory=list)
   69:     stop_reason: str = ""
   70:     turns_used: int = 0
   71:     budget_used: int = 0
   72:     error: Optional[str] = None
   73: 
   74: 
   75: # ============================================================
   76: # Helpers
   77: # ============================================================
   78: 
   79: def _build_tools_api_payload(tools: List[Any]) -> List[Dict[str, Any]]:
   80:     """Convert ToolRecord list into Bedrock `tools=` API payload shape.
   81: 
   82:     Bedrock expects: [{"name": ..., "description": ..., "input_schema": ...}, ...]
   83:     """
   84:     out: List[Dict[str, Any]] = []
   85:     for t in tools:
   86:         out.append({
   87:             "name": t.name,
   88:             "description": t.description,
   89:             "input_schema": t.input_schema,
   90:         })
   91:     return out
   92: 
   93: 
   94: def _coerce_tool_result_to_text(value: Any) -> str:
   95:     """Map any tool-execute return value into a Bedrock tool_result text string.
   96: 
   97:     Tool implementations return diverse shapes (str / dict / list). Bedrock's
   98:     tool_result content needs a string. Prefer str() for primitives, JSON for
   99:     structured shapes â€” same convention as v4 dispatch."""
  100:     if isinstance(value, str):
  101:         return value
  102:     if isinstance(value, (dict, list, tuple)):
  103:         try:
  104:             return json.dumps(value, ensure_ascii=False, default=str)
  105:         except Exception:
  106:             return str(value)
  107:     return str(value)
  108: 
  109: 
  110: def _truncate_tool_result(text: str, max_chars: int) -> str:
  111:     if max_chars <= 0 or len(text) <= max_chars:
  112:         return text
  113:     head = text[: max_chars - 200]
  114:     return (
  115:         head
  116:         + f"\n\n[... truncated: tool_result exceeded {max_chars} chars; "
  117:         f"original size {len(text)} chars ...]"
  118:     )
  119: 
  120: 
  121: # ============================================================
  122: # QueryEngine
  123: # ============================================================
  124: 
  125: class QueryEngine:
  126:     """Main agent loop. Owns the message buffer + iteration budget for one
  127:     `run()` call. Sub-agents (Phase 9) will share the same IterationBudget
  128:     instance via `forkSubagent`-style construction.
  129:     """
  130: 
  131:     DEFAULT_MAX_TURNS = 50  # v4 in-place default; UI may override per call.
  132: 
  133:     def __init__(
  134:         self,
  135:         client: Any,
  136:         max_turns: int = DEFAULT_MAX_TURNS,
  137:         budget: Optional[IterationBudget] = None,
  138:         on_stop_check: Optional[Callable[[], bool]] = None,
  139:     ):
  140:         """Construct a QueryEngine.
  141: 
  142:         Args:
  143:             client: BedrockClient (or mock with the same `chat(...)` shape).
  144:             max_turns: hard upper bound on turns per `run()` call.
  145:             budget: shared IterationBudget. If None, a fresh one is created.
  146:             on_stop_check: optional callable returning True if the user has
  147:                 requested a stop (notebook UX). Phase 11 wires this to the
  148:                 Stop button. Phase 8 keeps it None by default.
  149:         """
  150:         self.client = client
  151:         self.max_turns = max(1, int(max_turns))
  152:         self.budget = budget if budget is not None else IterationBudget()
  153:         self.on_stop_check = on_stop_check
  154: 
  155:         self.messages: List[Dict[str, Any]] = []
  156:         # Tool names that have been "discovered" via tool_search this run.
  157:         # Their schemas are added to per-turn `tools=` API payload until the
  158:         # run ends. v5 does NOT persist discovery across `run()` calls â€” the
  159:         # set is fresh each user message (matches Runnable's per-message
  160:         # discovered set).
  161:         self._discovered_tool_names: Set[str] = set()
  162: 
  163:     # ------------------------------------------------------------
  164:     # Public entry: run(...)
  165:     # ------------------------------------------------------------
  166: 
  167:     def run(
  168:         self,
  169:         user_message: str,
  170:         system_prompt: str,
  171:         tools: List[Any],
  172:         plan_mode: bool = False,
  173:         output_fn: Callable[[str], None] = print,
  174:         thinking_enabled: bool = False,
  175:         thinking_budget: int = 4096,
  176:         max_tokens: int = 4096,
  177:         temperature: float = 0.0,
  178:     ) -> QueryResult:
  179:         """Execute the agent loop until a stop condition is reached.
  180: 
  181:         See class docstring for the IN-SCOPE / OUT-OF-SCOPE list.
  182:         """
  183:         # Append user turn (Bedrock requires alternation; merge into trailing
  184:         # user if needed â€” matches v4 sagemaker_agent.py:8744).
  185:         if self.messages and self.messages[-1].get("role") == "user":
  186:             prev = self.messages[-1]
  187:             prev_content = prev.get("content", "")
  188:             if isinstance(prev_content, str):
  189:                 prev["content"] = prev_content + "\n\n" + user_message
  190:             elif isinstance(prev_content, list):
  191:                 prev_content.append({"type": "text", "text": user_message})
  192:             else:
  193:                 self.messages.append({"role": "user", "content": user_message})
  194:         else:
  195:             self.messages.append({"role": "user", "content": user_message})
  196: 
  197:         # Defer-import to avoid circular import at module-load.
  198:         from tools.registry import apply_tool_search_deferral, find_tool_by_name
  199:         from tools.tool_search import tool_search_discovered_names
  200: 
  201:         last_text = ""
  202:         stop_reason = ""
  203:         turns_used = 0
  204: 
  205:         for turn in range(self.max_turns):
  206:             # User-requested stop (Phase 11 wires this to the Stop button).
  207:             if self.on_stop_check and self.on_stop_check():
  208:                 output_fn("[Stopped by user]")
  209:                 stop_reason = "user_stop"
  210:                 break
  211: 
  212:             # Budget gate â€” shared with sub-agents (Phase 9).
  213:             if not self.budget.consume():
  214:                 used, total = self.budget.used(), self.budget.total()
  215:                 output_fn(
  216:                     f"[Budget exhausted: {used}/{total} iterations used. "
  217:                     "Adjust IterationBudget or start a new session.]"
  218:                 )
  219:                 stop_reason = "budget_exhausted"
  220:                 break
  221: 
  222:             # Phase 7 wiring contract: per-turn deferral + discovery merge.
  223:             visible_tools, deferred_names = apply_tool_search_deferral(
  224:                 tools, enabled=True,
  225:             )
  226:             if self._discovered_tool_names:
  227:                 # Promote previously-discovered tools from deferred â†’ visible.
  228:                 discovered = {n for n in self._discovered_tool_names if n in deferred_names}
  229:                 if discovered:
  230:                     promoted = [
  231:                         t for t in tools
  232:                         if t.name in discovered and t.name not in {v.name for v in visible_tools}
  233:                     ]
  234:                     visible_tools = visible_tools + promoted
  235:                     deferred_names = [n for n in deferred_names if n not in discovered]
  236: 
  237:             # If any names remain deferred, surface them as a system reminder
  238:             # so the model knows they exist and how to load them.
  239:             turn_messages = list(self.messages)
  240:             if deferred_names:
  241:                 turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)
  242: 
  243:             # Bedrock invocation.
  244:             try:
  245:                 response = self.client.chat(
  246:                     messages=turn_messages,
  247:                     system=system_prompt,
  248:                     tools=_build_tools_api_payload(visible_tools),
  249:                     max_tokens=max_tokens,
  250:                     temperature=temperature,
  251:                     thinking_enabled=thinking_enabled,
  252:                     thinking_budget=thinking_budget,
  253:                 )
  254:             except Exception as exc:  # noqa: BLE001 â€” classify and surface
  255:                 category, recovery, debug = ErrorClassifier.classify(exc)
  256:                 output_fn(f"[Bedrock {category}: {debug}]")
  257:                 if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
  258:                     stop_reason = "context_overflow"
  259:                 else:
  260:                     stop_reason = "fatal_error"
  261:                 return QueryResult(
  262:                     text=last_text,
  263:                     messages=list(self.messages),
  264:                     stop_reason=stop_reason,
  265:                     turns_used=turns_used,
  266:                     budget_used=self.budget.used(),
  267:                     error=f"{category}: {debug}",
  268:                 )
  269: 
  270:             turns_used += 1
  271: 
  272:             # Append assistant turn (text + tool_use blocks, plus thinking).
  273:             assistant_content = self._build_assistant_content(response)
  274:             self.messages.append({"role": "assistant", "content": assistant_content})
  275: 
  276:             if response.text:
  277:                 last_text = response.text
  278: 
  279:             # Stop conditions: end_turn / no tool_use blocks â†’ final answer.
  280:             if not response.tool_calls:
  281:                 stop_reason = "end_turn"
  282:                 if response.text:
  283:                     output_fn(response.text)
  284:                 break
  285: 
  286:             # Tool dispatch â€” emit one tool_result per tool_use call.
  287:             tool_results: List[Dict[str, Any]] = []
  288:             for call in response.tool_calls:
  289:                 tool = find_tool_by_name(tools, call.name)
  290:                 if tool is None:
  291:                     # Unknown tool name â€” return error to model so it can
  292:                     # recover (v4 parity: dispatch never raises).
  293:                     tool_results.append({
  294:                         "type": "tool_result",
  295:                         "tool_use_id": call.id,
  296:                         "content": f"Error: unknown tool '{call.name}'",
  297:                         "is_error": True,
  298:                     })
  299:                     continue
  300: 
  301:                 # Plan-mode read-only enforcement (v4 PLAN_MODE_ALLOWED_TOOLS).
  302:                 if plan_mode and not tool.is_read_only and not getattr(tool, "always_load", False):
  303:                     tool_results.append({
  304:                         "type": "tool_result",
  305:                         "tool_use_id": call.id,
  306:                         "content": (
  307:                             f"Error: tool '{call.name}' is mutating; "
  308:                             "blocked in plan mode."
  309:                         ),
  310:                         "is_error": True,
  311:                     })
  312:                     continue
  313: 
  314:                 # Execute. Tool implementations may raise; we trap and surface
  315:                 # the error to the model rather than the human user.
  316:                 try:
  317:                     raw = tool.execute(call.input, context={
  318:                         "active_tools": tools,
  319:                         "plan_mode": plan_mode,
  320:                     })
  321:                     text = _coerce_tool_result_to_text(raw)
  322:                     text = _truncate_tool_result(text, tool.max_result_size_chars)
  323:                     tool_results.append({
  324:                         "type": "tool_result",
  325:                         "tool_use_id": call.id,
  326:                         "content": text,
  327:                     })
  328:                     # Phase 7 wiring: extract discovered names from tool_search
  329:                     # results and add to the next turn's tools= payload.
  330:                     if call.name == "tool_search":
  331:                         discovered = tool_search_discovered_names(text)
  332:                         if discovered:
  333:                             self._discovered_tool_names.update(discovered)
  334:                 except Exception as exc:  # noqa: BLE001 â€” surface to model
  335:                     logging.warning(
  336:                         "[query_engine] tool '%s' raised %s: %s",
  337:                         call.name, type(exc).__name__, exc,
  338:                     )
  339:                     tool_results.append({
  340:                         "type": "tool_result",
  341:                         "tool_use_id": call.id,
  342:                         "content": f"Error: {type(exc).__name__}: {exc}",
  343:                         "is_error": True,
  344:                     })
  345: 
  346:             # Append the tool_results as a user turn (Bedrock convention).
  347:             self.messages.append({"role": "user", "content": tool_results})
  348: 
  349:         else:  # for-loop fell through without break
  350:             stop_reason = "max_turns"
  351:             output_fn(f"[Max turns reached: {self.max_turns}]")
  352: 
  353:         return QueryResult(
  354:             text=last_text,
  355:             messages=list(self.messages),
  356:             stop_reason=stop_reason or "end_turn",
  357:             turns_used=turns_used,
  358:             budget_used=self.budget.used(),
  359:         )
  360: 
  361:     # ------------------------------------------------------------
  362:     # Internal: assemble assistant turn content from a Bedrock Response
  363:     # ------------------------------------------------------------
  364: 
  365:     @staticmethod
  366:     def _build_assistant_content(response: Any) -> List[Dict[str, Any]]:
  367:         """Construct a Bedrock-shaped assistant content list from a Response.
  368: 
  369:         Order: thinking blocks (if any) â†’ text â†’ tool_use. The thinking
  370:         block is preserved so the next turn's API call carries it back to
  371:         the model (Bedrock requires this for extended thinking continuity).
  372:         """
  373:         blocks: List[Dict[str, Any]] = []
  374:         thinking = getattr(response, "thinking", "") or ""
  375:         if thinking:
  376:             blocks.append({"type": "thinking", "thinking": thinking})
  377:         if response.text:
  378:             blocks.append({"type": "text", "text": response.text})
  379:         for call in response.tool_calls:
  380:             blocks.append({
  381:                 "type": "tool_use",
  382:                 "id": call.id,
  383:                 "name": call.name,
  384:                 "input": call.input,
  385:             })
  386:         return blocks
  387: 
  388:     # ------------------------------------------------------------
  389:     # Internal: deferred-tools system reminder injection
  390:     # ------------------------------------------------------------
  391: 
  392:     @staticmethod
  393:     def _inject_deferred_reminder(
  394:         messages: List[Dict[str, Any]],
  395:         deferred_names: List[str],
  396:     ) -> List[Dict[str, Any]]:
  397:         """Append a `<system-reminder>` block listing deferred tool names so
  398:         the model knows what's available via tool_search.
  399: 
  400:         The reminder is injected as a transient text block on the trailing
  401:         user turn â€” it does not mutate `self.messages`, so it does not leak
  402:         into subsequent turns once the model has loaded the schemas it needs.
  403:         """
  404:         if not deferred_names:
  405:             return messages
  406:         reminder = (
  407:             "<system-reminder>\n"
  408:             "The following deferred tools are available via tool_search. Their schemas "
  409:             "are NOT loaded â€” calling them directly will fail. Use tool_search with "
  410:             "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
  411:             + "\n".join(sorted(deferred_names))
  412:             + "\n</system-reminder>"
  413:         )
  414:         # Transient append: copy the trailing user message and add the reminder
  415:         # as an extra text block. If the trailing turn is not user-role, we
  416:         # append a fresh user message â€” but this should never happen because
  417:         # the loop only invokes Bedrock right after a user turn or tool_results.
  418:         out = list(messages)
  419:         if not out or out[-1].get("role") != "user":
  420:             out.append({"role": "user", "content": [{"type": "text", "text": reminder}]})
  421:             return out
  422:         last = dict(out[-1])
  423:         content = last.get("content")
  424:         if isinstance(content, str):
  425:             last["content"] = [
  426:                 {"type": "text", "text": content},
  427:                 {"type": "text", "text": reminder},
  428:             ]
  429:         elif isinstance(content, list):
  430:             last["content"] = list(content) + [{"type": "text", "text": reminder}]
  431:         else:
  432:             last["content"] = [{"type": "text", "text": reminder}]
  433:         out[-1] = last
  434:         return out
  435: 
  436: 
  437: # ============================================================
  438: # Single-turn helper for unit tests
  439: # ============================================================
  440: 
  441: def run_one_turn(
  442:     client: Any,
  443:     messages: List[Dict[str, Any]],
  444:     system_prompt: str,
  445:     tools: List[Any],
  446:     max_tokens: int = 4096,
  447:     temperature: float = 0.0,
  448:     thinking_enabled: bool = False,
  449:     thinking_budget: int = 4096,
  450: ) -> Any:
  451:     """Run a single Bedrock invocation with Phase 7 deferral applied.
  452: 
  453:     Returns the raw `Response` object. Tests use this to assert wiring without
  454:     spinning up the full multi-turn loop.
  455:     """
  456:     from tools.registry import apply_tool_search_deferral
  457: 
  458:     visible_tools, _deferred = apply_tool_search_deferral(tools, enabled=True)
  459:     return client.chat(
  460:         messages=messages,
  461:         system=system_prompt,
  462:         tools=_build_tools_api_payload(visible_tools),
  463:         max_tokens=max_tokens,
  464:         temperature=temperature,
  465:         thinking_enabled=thinking_enabled,
  466:         thinking_budget=thinking_budget,
  467:     )

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\runtime\bedrock_client.py
    1: """V5 BedrockClient â€” verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560.
    2: 
    3: Per ADR-005: BedrockClient is a pure v4 reuse (Bedrock-native, already
    4: production-tested). The only Phase-1 change is structural â€” the class lives
    5: in its own module instead of inline in the v4 monolith.
    6: 
    7: Sophisticated cache-break detection (Runnable promptCacheBreakDetection.ts)
    8: is DEFERRED to Phase 6 because it requires multi-block system prompts that
    9: v5 doesn't have until prompt/sections.py lands. Phase 6 ADR will track that
   10: adoption.
   11: 
   12: Phase 1 simplification: the full retry-classifier + jittered-backoff loop
   13: lives in v4's BedrockClient. For Phase 1, we keep that loop intact (it's
   14: already battle-tested), but the helper classes (BedrockErrorCategory,
   15: ErrorClassifier, RetryPolicy) are imported from a temporary local module
   16: inside this file. Phase 8 will extract them to core/errors.py + core/retry.py
   17: with cleaner separation. This avoids a circular Phase-1/Phase-8 dependency.
   18: 
   19: PS Issue #4 verification (per V5_PS_ISSUES_MAPPING.md): tests/unit/test_bedrock.py
   20: must verify thinking config is sent on EVERY Bedrock call when
   21: CONFIG.thinking_enabled=True (not just the first turn).
   22: 
   23: Source: compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560.
   24: """
   25: from __future__ import annotations
   26: 
   27: import json
   28: import logging
   29: import time
   30: from dataclasses import dataclass, field
   31: from typing import Any, Dict, List, Optional
   32: 
   33: # botocore.config import is local-deferred so unit tests with mock_mode=True
   34: # can import this module without boto3 installed. Real flows will import on demand.
   35: 
   36: # CONFIG is imported lazily within methods to avoid circular import during Phase 1.
   37: 
   38: 
   39: # ============================================================
   40: # Response / ToolCall (lightweight value types â€” verbatim from v4)
   41: # ============================================================
   42: 
   43: @dataclass
   44: class ToolCall:
   45:     """A tool invocation request from the model."""
   46:     id: str
   47:     name: str
   48:     input: Dict[str, Any] = field(default_factory=dict)
   49: 
   50: 
   51: @dataclass
   52: class Response:
   53:     """Parsed Bedrock response."""
   54:     text: str
   55:     tool_calls: List[ToolCall] = field(default_factory=list)
   56:     stop_reason: str = ""
   57:     usage: Dict[str, Any] = field(default_factory=dict)
   58:     thinking: str = ""
   59: 
   60: 
   61: # ============================================================
   62: # Error categories + classifier + retry policy
   63: # Phase 8: extracted to core/errors.py + core/retry.py (ADR-014).
   64: # Re-imported here so existing call-sites (and tests) continue to work
   65: # byte-equivalent with Phase 1.
   66: # ============================================================
   67: 
   68: from core.errors import BedrockErrorCategory, ErrorClassifier  # noqa: F401
   69: from core.retry import RetryPolicy  # noqa: F401
   70: 
   71: 
   72: # ============================================================
   73: # BedrockClient (v4 verbatim port)
   74: # ============================================================
   75: 
   76: # botocore Config preset for retry tuning (v4 default).
   77: def _bedrock_client_config():
   78:     """Return a botocore Config with v4's retry tuning. Local-imports botocore."""
   79:     from botocore.config import Config as _BotoConfig
   80:     return _BotoConfig(
   81:         retries={"max_attempts": 1, "mode": "standard"},  # we handle retries ourselves
   82:         read_timeout=120,
   83:         connect_timeout=10,
   84:     )
   85: 
   86: 
   87: class BedrockClient:
   88:     """AWS Bedrock Claude client with mock mode for testing.
   89: 
   90:     Verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:2378.
   91:     Behavior unchanged â€” same prompt-cache fallback semantics, same retry
   92:     classifier, same thinking-mode handling.
   93: 
   94:     PS Issue #4 verification: `chat()` always sends `thinking` config when
   95:     `thinking_enabled=True`, regardless of which call this is in the session.
   96:     The fact that the model only RETURNS thinking blocks on some turns is a
   97:     model-side decision; v5 always SENDS the config so the model has the
   98:     option. test_bedrock.py verifies this.
   99:     """
  100: 
  101:     def __init__(
  102:         self,
  103:         model_id: str,
  104:         region: str,
  105:         mock_mode: bool = False,
  106:         client: Any = None,
  107:     ):
  108:         """Construct a BedrockClient.
  109: 
  110:         Args:
  111:             model_id: Bedrock inference profile id.
  112:             region: AWS region.
  113:             mock_mode: if True, no real Bedrock calls; `_mock_response()` is used.
  114:             client: optional pre-built bedrock-runtime client. If provided,
  115:                 boto3 is NOT imported. This lets unit tests inject a fake
  116:                 client without requiring boto3 to be installed (Codex Phase-01
  117:                 review finding 1).
  118:         """
  119:         self.model_id = model_id
  120:         self.region = region
  121:         self.mock_mode = mock_mode
  122:         self.prompt_cache_supported = True  # set False after first cache fallback
  123:         self._cache_threshold_warned = False
  124:         if mock_mode:
  125:             self.client = None
  126:         elif client is not None:
  127:             self.client = client
  128:         else:
  129:             import boto3
  130:             self.client = boto3.client(
  131:                 "bedrock-runtime", region_name=region, config=_bedrock_client_config()
  132:             )
  133: 
  134:     # ---------- mock-mode helpers ----------
  135: 
  136:     def _mock_response(self, messages, tools) -> Response:
  137:         """Generate mock response for testing (v4 verbatim, simplified)."""
  138:         last = messages[-1]["content"] if messages else ""
  139:         if isinstance(last, str):
  140:             low = last.lower()
  141:             if "list" in low and ("file" in low or "dir" in low):
  142:                 return Response(
  143:                     "I'll list the files.",
  144:                     [ToolCall("m1", "list_dir", {"path": "."})],
  145:                     "tool_use",
  146:                     {},
  147:                 )
  148:             if "read" in low:
  149:                 return Response(
  150:                     "I'll read that file.",
  151:                     [ToolCall("m2", "read_file", {"file_path": "README.md"})],
  152:                     "tool_use",
  153:                     {},
  154:                 )
  155:         return Response(
  156:             f"[MOCK] Received: {str(last)[:100]}...",
  157:             [],
  158:             "end_turn",
  159:             {"input_tokens": 100, "output_tokens": 50},
  160:         )
  161: 
  162:     # ---------- main chat entry ----------
  163: 
  164:     def chat(
  165:         self,
  166:         messages: List[Dict],
  167:         system: Any,  # str OR list-of-blocks (with cache_control)
  168:         tools: Optional[List[Dict]] = None,
  169:         max_tokens: int = 4096,
  170:         temperature: float = 0.0,
  171:         thinking_enabled: bool = False,
  172:         thinking_budget: int = 4096,
  173:     ) -> Response:
  174:         """Send chat request to Bedrock.
  175: 
  176:         Args:
  177:             messages: Conversation messages
  178:             system: System prompt (str or pre-formatted multi-block list with cache_control)
  179:             tools: Tool definitions
  180:             max_tokens: Maximum response tokens
  181:             temperature: Sampling temperature (0.0-1.0)
  182:             thinking_enabled: Enable extended thinking mode
  183:             thinking_budget: Max tokens for thinking (1024-16000)
  184:         """
  185:         if self.mock_mode:
  186:             return self._mock_response(messages, tools)
  187: 
  188:         # Lazy import CONFIG to avoid circular import during Phase 1.
  189:         from runtime.config import CONFIG
  190: 
  191:         # V4.1 #14: Prompt cache boundary.
  192:         # If cache enabled and supported, split system string into static (cached)
  193:         # + dynamic (uncached) blocks. Bedrock supports prompt caching natively
  194:         # via cache_control blocks in content. No anthropic_beta header needed.
  195:         # Haiku 4.5: min 4096 tokens/checkpoint. Sonnet 4.5: min 1024.
  196:         cache_active = CONFIG.enable_prompt_cache and self.prompt_cache_supported
  197:         if cache_active and isinstance(system, list):
  198:             # Already formatted as cache blocks by caller â€” pass as-is
  199:             system_field = system
  200:             use_cache = True
  201:         elif cache_active and isinstance(system, str):
  202:             # Split at the dynamic boundary marker if present, else cache full prompt
  203:             _CACHE_BOUNDARY = "\n\n# === DYNAMIC ==="
  204:             if _CACHE_BOUNDARY in system:
  205:                 static_part, dynamic_part = system.split(_CACHE_BOUNDARY, 1)
  206:                 # Bedrock rejects empty/whitespace text blocks â€” only add dynamic if non-empty
  207:                 if dynamic_part.strip():
  208:                     system_field = [
  209:                         {
  210:                             "type": "text",
  211:                             "text": static_part,
  212:                             "cache_control": {"type": "ephemeral"},
  213:                         },
  214:                         {"type": "text", "text": dynamic_part},
  215:                     ]
  216:                 else:
  217:                     system_field = [
  218:                         {
  219:                             "type": "text",
  220:                             "text": static_part,
  221:                             "cache_control": {"type": "ephemeral"},
  222:                         },
  223:                     ]
  224:             else:
  225:                 # No boundary â€” cache the whole prompt as static
  226:                 system_field = [
  227:                     {
  228:                         "type": "text",
  229:                         "text": system,
  230:                         "cache_control": {"type": "ephemeral"},
  231:                     },
  232:                 ]
  233:             use_cache = True
  234:         else:
  235:             system_field = system
  236:             use_cache = False
  237: 
  238:         body: Dict[str, Any] = {
  239:             "anthropic_version": "bedrock-2023-05-31",
  240:             "max_tokens": max_tokens,
  241:             "system": system_field,
  242:             "messages": messages,
  243:         }
  244:         # Note: Bedrock prompt caching is activated by cache_control blocks in
  245:         # content. No anthropic_beta header needed (that header is for the direct
  246:         # Anthropic API only).
  247: 
  248:         # Extended thinking mode (requires temperature=1).
  249:         # PS Issue #4: this block runs on EVERY chat() call when thinking_enabled
  250:         # is True â€” not just first message. The model decides per turn whether
  251:         # to USE the budget. tests/unit/test_bedrock.py asserts this contract.
  252:         if thinking_enabled:
  253:             body["thinking"] = {
  254:                 "type": "enabled",
  255:                 "budget_tokens": min(max(thinking_budget, 1024), 16000),
  256:             }
  257:             body["temperature"] = 1  # Required for thinking mode
  258:         else:
  259:             body["temperature"] = temperature
  260: 
  261:         if tools:
  262:             body["tools"] = tools
  263: 
  264:         # V4.9.4: jittered exponential backoff on transient/throttle errors.
  265:         # Cache-validation: strip cache blocks and retry once (existing v4.1 #14).
  266:         attempt = 0
  267:         last_exc: Optional[Exception] = None
  268:         while True:
  269:             try:
  270:                 response = self.client.invoke_model(
  271:                     modelId=self.model_id,
  272:                     body=json.dumps(body, separators=(",", ":")),
  273:                     contentType="application/json",
  274:                 )
  275:                 break  # success
  276:             except Exception as e:
  277:                 last_exc = e
  278:                 category, recovery, debug_msg = ErrorClassifier.classify(e)
  279: 
  280:                 # Cache-validation: strip cache blocks, retry once
  281:                 if (
  282:                     category == BedrockErrorCategory.VALIDATION_CACHE
  283:                     and use_cache
  284:                     and self.prompt_cache_supported
  285:                 ):
  286:                     logging.warning(
  287:                         f"[BEDROCK] Prompt cache not supported by this model/region, falling back: {debug_msg}"
  288:                     )
  289:                     self.prompt_cache_supported = False
  290:                     if isinstance(system, str):
  291:                         body["system"] = system
  292:                     else:
  293:                         body["system"] = "\n\n".join(
  294:                             b.get("text", "") for b in system if isinstance(b, dict)
  295:                         )
  296:                     use_cache = False
  297:                     continue
  298: 
  299:                 # Throttle / transient / etc.: retry with jitter
  300:                 if RetryPolicy.should_retry(attempt, recovery):
  301:                     sleep_s = RetryPolicy.backoff_seconds(attempt)
  302:                     logging.warning(
  303:                         f"[BEDROCK] {category} (recovery={recovery}, attempt={attempt + 1}/"
  304:                         f"{RetryPolicy.MAX_RETRIES + 1}, sleep={sleep_s:.1f}s): {debug_msg}"
  305:                     )
  306:                     time.sleep(sleep_s)
  307:                     attempt += 1
  308:                     continue
  309: 
  310:                 # Anything else: surface it
  311:                 logging.error(f"[BEDROCK] {category} (recovery={recovery}, no-retry): {debug_msg}")
  312:                 raise
  313: 
  314:         result = json.loads(response["body"].read())
  315:         return self._parse(result)
  316: 
  317:     # ---------- response parsing ----------
  318: 
  319:     def _parse(self, result: dict) -> Response:
  320:         """Parse Bedrock response into Response value type (v4 verbatim)."""
  321:         text = ""
  322:         thinking = ""
  323:         tool_calls: List[ToolCall] = []
  324:         for block in result.get("content", []):
  325:             block_type = block.get("type")
  326:             if block_type == "text":
  327:                 text += block.get("text", "")
  328:             elif block_type == "thinking":
  329:                 thinking += block.get("thinking", "")
  330:             elif block_type == "tool_use":
  331:                 tool_calls.append(
  332:                     ToolCall(
  333:                         id=block.get("id", ""),
  334:                         name=block.get("name", ""),
  335:                         input=block.get("input", {}),
  336:                     )
  337:                 )
  338:         return Response(
  339:             text=text,
  340:             tool_calls=tool_calls,
  341:             stop_reason=result.get("stop_reason", ""),
  342:             usage=result.get("usage", {}),
  343:             thinking=thinking,
  344:         )

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_budget.py
    1: """Phase 08 unit tests: core/budget.py â€” IterationBudget.
    2: 
    3: Locks PORT_LOG #016: verbatim port of v4's IterationBudget (Hermes pattern).
    4: """
    5: from __future__ import annotations
    6: 
    7: import os
    8: import sys
    9: import threading
   10: 
   11: _AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   12: if _AGENT_ROOT not in sys.path:
   13:     sys.path.insert(0, _AGENT_ROOT)
   14: 
   15: 
   16: def test_default_max_is_600():
   17:     from core.budget import IterationBudget
   18:     b = IterationBudget()
   19:     assert b.total() == 600
   20: 
   21: 
   22: def test_consume_decrements_remaining():
   23:     from core.budget import IterationBudget
   24:     b = IterationBudget(max_iterations=3)
   25:     assert b.remaining() == 3
   26:     assert b.consume() is True
   27:     assert b.used() == 1
   28:     assert b.remaining() == 2
   29: 
   30: 
   31: def test_consume_returns_false_when_exhausted():
   32:     from core.budget import IterationBudget
   33:     b = IterationBudget(max_iterations=2)
   34:     assert b.consume() is True
   35:     assert b.consume() is True
   36:     assert b.consume() is False
   37:     # Subsequent calls also return False without incrementing
   38:     assert b.consume() is False
   39:     assert b.used() == 2
   40: 
   41: 
   42: def test_min_clamp_to_one():
   43:     """max_iterations <= 0 must clamp to 1 (defensive)."""
   44:     from core.budget import IterationBudget
   45:     b = IterationBudget(max_iterations=0)
   46:     assert b.total() == 1
   47:     assert b.consume() is True
   48:     assert b.consume() is False
   49: 
   50: 
   51: def test_reset_clears_used():
   52:     from core.budget import IterationBudget
   53:     b = IterationBudget(max_iterations=2)
   54:     b.consume()
   55:     b.consume()
   56:     assert b.used() == 2
   57:     b.reset()
   58:     assert b.used() == 0
   59:     assert b.consume() is True
   60: 
   61: 
   62: def test_thread_safety_under_concurrent_consumers():
   63:     """20 threads each calling consume() 100 times against a budget of 1000
   64:     must end with exactly 1000 successful consumes and zero overshoot."""
   65:     from core.budget import IterationBudget
   66:     b = IterationBudget(max_iterations=1000)
   67:     successes: list = []
   68:     lock = threading.Lock()
   69: 
   70:     def worker():
   71:         local = 0
   72:         for _ in range(100):
   73:             if b.consume():
   74:                 local += 1
   75:         with lock:
   76:             successes.append(local)
   77: 
   78:     threads = [threading.Thread(target=worker) for _ in range(20)]
   79:     for t in threads:
   80:         t.start()
   81:     for t in threads:
   82:         t.join()
   83: 
   84:     assert sum(successes) == 1000
   85:     assert b.used() == 1000
   86:     assert b.consume() is False
   87: 
   88: 
   89: def test_shared_budget_across_pseudo_subagents():
   90:     """The Hermes pattern: a parent + N "sub-agents" share one budget instance."""
   91:     from core.budget import IterationBudget
   92:     parent = IterationBudget(max_iterations=10)
   93:     child_a = parent  # sub-agents inherit the same instance
   94:     child_b = parent
   95: 
   96:     for _ in range(4):
   97:         assert parent.consume() is True
   98:     for _ in range(3):
   99:         assert child_a.consume() is True
  100:     for _ in range(3):
  101:         assert child_b.consume() is True
  102:     # All 10 used; next call returns False regardless of caller
  103:     assert parent.consume() is False
  104:     assert child_a.consume() is False
  105:     assert child_b.consume() is False

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_errors.py
    1: """Phase 08 unit tests: core/errors.py â€” BedrockErrorCategory + ErrorClassifier.
    2: 
    3: Locks PORT_LOG #017: extraction from runtime/bedrock_client.py preserves
    4: classification semantics byte-for-byte.
    5: """
    6: from __future__ import annotations
    7: 
    8: import os
    9: import sys
   10: 
   11: _AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   12: if _AGENT_ROOT not in sys.path:
   13:     sys.path.insert(0, _AGENT_ROOT)
   14: 
   15: 
   16: def test_validation_cache_classified():
   17:     from core.errors import BedrockErrorCategory, ErrorClassifier
   18:     exc = Exception("ValidationException: cache_control not supported in this region")
   19:     cat, recovery, _ = ErrorClassifier.classify(exc)
   20:     assert cat == BedrockErrorCategory.VALIDATION_CACHE
   21:     assert recovery == "strip_cache_retry"
   22: 
   23: 
   24: def test_context_overflow_classified():
   25:     from core.errors import BedrockErrorCategory, ErrorClassifier
   26:     exc = Exception("ValidationException: prompt is too long")
   27:     cat, recovery, _ = ErrorClassifier.classify(exc)
   28:     assert cat == BedrockErrorCategory.CONTEXT_OVERFLOW
   29:     assert recovery == "compact_retry"
   30: 
   31: 
   32: def test_validation_other_no_retry():
   33:     from core.errors import BedrockErrorCategory, ErrorClassifier
   34:     exc = Exception("ValidationException: unknown field 'foo'")
   35:     cat, recovery, _ = ErrorClassifier.classify(exc)
   36:     assert cat == BedrockErrorCategory.VALIDATION_OTHER
   37:     assert recovery == "no_retry"
   38: 
   39: 
   40: def test_throttle_classified():
   41:     from core.errors import BedrockErrorCategory, ErrorClassifier
   42:     exc = Exception("ThrottlingException: rate exceeded")
   43:     cat, recovery, _ = ErrorClassifier.classify(exc)
   44:     assert cat == BedrockErrorCategory.THROTTLE
   45:     assert recovery == "backoff"
   46: 
   47: 
   48: def test_service_unavailable_classified():
   49:     from core.errors import BedrockErrorCategory, ErrorClassifier
   50:     exc = Exception("ServiceUnavailable 503")
   51:     cat, recovery, _ = ErrorClassifier.classify(exc)
   52:     assert cat == BedrockErrorCategory.SERVICE_UNAVAILABLE
   53:     assert recovery == "backoff"
   54: 
   55: 
   56: def test_model_not_ready_classified():
   57:     from core.errors import BedrockErrorCategory, ErrorClassifier
   58:     exc = Exception("ModelNotReady: not ready yet")
   59:     cat, recovery, _ = ErrorClassifier.classify(exc)
   60:     assert cat == BedrockErrorCategory.MODEL_NOT_READY
   61:     assert recovery == "backoff"
   62: 
   63: 
   64: def test_access_denied_no_retry():
   65:     from core.errors import BedrockErrorCategory, ErrorClassifier
   66:     exc = Exception("AccessDenied: 403 Forbidden")
   67:     cat, recovery, _ = ErrorClassifier.classify(exc)
   68:     assert cat == BedrockErrorCategory.ACCESS_DENIED
   69:     assert recovery == "no_retry"
   70: 
   71: 
   72: def test_network_error_via_class_name():
   73:     from core.errors import BedrockErrorCategory, ErrorClassifier
   74: 
   75:     class EndpointConnectionError(Exception):
   76:         pass
   77: 
   78:     cat, recovery, _ = ErrorClassifier.classify(EndpointConnectionError("connection failed"))
   79:     assert cat == BedrockErrorCategory.NETWORK
   80:     assert recovery == "backoff"
   81: 
   82: 
   83: def test_unknown_error_no_retry():
   84:     from core.errors import BedrockErrorCategory, ErrorClassifier
   85:     exc = Exception("something completely unexpected")
   86:     cat, recovery, _ = ErrorClassifier.classify(exc)
   87:     assert cat == BedrockErrorCategory.UNKNOWN
   88:     assert recovery == "no_retry"
   89: 
   90: 
   91: def test_debug_msg_truncated_to_200():
   92:     from core.errors import ErrorClassifier
   93:     big = "x" * 500
   94:     exc = Exception(f"ValidationException: {big}")
   95:     _, _, debug = ErrorClassifier.classify(exc)
   96:     assert len(debug) <= 200
   97: 
   98: 
   99: def test_runtime_bedrock_client_re_exports_match():
  100:     """PORT_LOG #017 byte-equivalence: runtime.bedrock_client must re-export
  101:     the exact same classes from core.errors so existing call-sites work."""
  102:     from core.errors import BedrockErrorCategory as CoreCat, ErrorClassifier as CoreCls
  103:     from runtime.bedrock_client import BedrockErrorCategory as RuntimeCat, ErrorClassifier as RuntimeCls
  104:     assert CoreCat is RuntimeCat
  105:     assert CoreCls is RuntimeCls

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_retry.py
    1: """Phase 08 unit tests: core/retry.py â€” RetryPolicy.
    2: 
    3: Locks PORT_LOG #018: jittered exponential backoff with v4 verbatim semantics.
    4: """
    5: from __future__ import annotations
    6: 
    7: import os
    8: import random
    9: import sys
   10: 
   11: _AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   12: if _AGENT_ROOT not in sys.path:
   13:     sys.path.insert(0, _AGENT_ROOT)
   14: 
   15: 
   16: def test_max_retries_is_4():
   17:     from core.retry import RetryPolicy
   18:     assert RetryPolicy.MAX_RETRIES == 4
   19: 
   20: 
   21: def test_should_retry_for_backoff_recovery():
   22:     from core.retry import RetryPolicy
   23:     assert RetryPolicy.should_retry(0, "backoff") is True
   24:     assert RetryPolicy.should_retry(3, "backoff") is True
   25: 
   26: 
   27: def test_should_not_retry_when_attempts_exhausted():
   28:     from core.retry import RetryPolicy
   29:     assert RetryPolicy.should_retry(4, "backoff") is False
   30:     assert RetryPolicy.should_retry(99, "backoff") is False
   31: 
   32: 
   33: def test_should_not_retry_for_non_backoff_recovery():
   34:     from core.retry import RetryPolicy
   35:     assert RetryPolicy.should_retry(0, "no_retry") is False
   36:     assert RetryPolicy.should_retry(0, "strip_cache_retry") is False
   37:     assert RetryPolicy.should_retry(0, "compact_retry") is False
   38: 
   39: 
   40: def test_backoff_seconds_floor_and_ceiling():
   41:     """Sleep curve: ~1s, 2s, 4s, 8s with up-to-30% jitter. Always >= 0.1s."""
   42:     from core.retry import RetryPolicy
   43:     random.seed(42)
   44:     samples = [RetryPolicy.backoff_seconds(0) for _ in range(50)]
   45:     for s in samples:
   46:         assert s >= 0.1
   47:         # base=1.0, jitter +/- 0.30 â†’ [0.7, 1.3]
   48:         assert 0.7 <= s <= 1.3 + 0.0001
   49: 
   50: 
   51: def test_backoff_seconds_doubles_per_attempt():
   52:     from core.retry import RetryPolicy
   53:     random.seed(0)
   54:     base_means = []
   55:     for attempt in range(4):
   56:         random.seed(attempt)
   57:         samples = [RetryPolicy.backoff_seconds(attempt) for _ in range(200)]
   58:         base_means.append(sum(samples) / len(samples))
   59:     # Mean roughly doubles (within jitter): ~1, ~2, ~4, ~8
   60:     for prev, cur in zip(base_means, base_means[1:]):
   61:         assert cur > prev * 1.5, f"expected ~doubling, got {prev:.2f} -> {cur:.2f}"
   62: 
   63: 
   64: def test_runtime_bedrock_client_re_exports_match():
   65:     """Byte-equivalence with Phase-1: runtime.bedrock_client re-exports
   66:     the same RetryPolicy class so existing call-sites continue to work."""
   67:     from core.retry import RetryPolicy as CorePolicy
   68:     from runtime.bedrock_client import RetryPolicy as RuntimePolicy
   69:     assert CorePolicy is RuntimePolicy

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\integration\test_query_engine.py
    1: """Phase 08 integration tests: core/query_engine.py â€” end-to-end agent loop.
    2: 
    3: Acceptance criterion (V5_PLAN.md Â§Phase 8):
    4: - end-to-end mock test (tool_use â†’ tool runs â†’ final answer)
    5: - tool_search deferred-loading round-trip works
    6: 
    7: Locks PORT_LOG #019: Runnable QueryEngine.ts adapted to v5 .ipynb shape.
    8: """
    9: from __future__ import annotations
   10: 
   11: import os
   12: import sys
   13: from typing import Any, Dict, List
   14: 
   15: import pytest
   16: 
   17: _AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   18: if _AGENT_ROOT not in sys.path:
   19:     sys.path.insert(0, _AGENT_ROOT)
   20: 
   21: 
   22: # ============================================================
   23: # Test fixtures
   24: # ============================================================
   25: 
   26: class _ScriptedClient:
   27:     """Mock Bedrock client that returns pre-scripted responses in order.
   28: 
   29:     Each entry is one of:
   30:       - ("text", "final answer")              â†’ stop_reason=end_turn, no tools
   31:       - ("tool", call_id, tool_name, args)    â†’ tool_use block
   32:       - ("text+tool", text, call_id, name, args) â†’ both text and tool_use
   33:     """
   34: 
   35:     def __init__(self, script):
   36:         self.script = list(script)
   37:         self.calls = []  # list of (messages, tools_payload)
   38: 
   39:     def chat(self, messages, system, tools, max_tokens, temperature,
   40:              thinking_enabled, thinking_budget):
   41:         from runtime.bedrock_client import Response, ToolCall
   42:         self.calls.append({
   43:             "messages": list(messages),
   44:             "tools": list(tools or []),
   45:         })
   46:         if not self.script:
   47:             return Response(text="(no more scripted responses)", tool_calls=[],
   48:                             stop_reason="end_turn", usage={})
   49:         kind, *rest = self.script.pop(0)
   50:         if kind == "text":
   51:             return Response(text=rest[0], tool_calls=[], stop_reason="end_turn", usage={})
   52:         if kind == "tool":
   53:             cid, name, args = rest
   54:             return Response(
   55:                 text="", tool_calls=[ToolCall(cid, name, args)],
   56:                 stop_reason="tool_use", usage={},
   57:             )
   58:         if kind == "text+tool":
   59:             txt, cid, name, args = rest
   60:             return Response(
   61:                 text=txt,
   62:                 tool_calls=[ToolCall(cid, name, args)],
   63:                 stop_reason="tool_use", usage={},
   64:             )
   65:         raise AssertionError(f"unknown script kind: {kind}")
   66: 
   67: 
   68: @pytest.fixture(autouse=True)
   69: def fresh_registry():
   70:     """Phase 7 / Phase 2 tests mutate the registry; force-reset for Phase 8."""
   71:     from tools.registry import _reset_registry_for_tests
   72:     from tools import bootstrap_built_ins
   73:     _reset_registry_for_tests()
   74:     bootstrap_built_ins()
   75:     yield
   76: 
   77: 
   78: # ============================================================
   79: # Test 1 â€” basic single-turn end_turn
   80: # ============================================================
   81: 
   82: def test_engine_returns_final_text_on_end_turn():
   83:     from core import QueryEngine
   84:     from tools import all_registered
   85: 
   86:     client = _ScriptedClient([("text", "Hello world.")])
   87:     engine = QueryEngine(client=client, max_turns=5)
   88:     result = engine.run(
   89:         user_message="say hi",
   90:         system_prompt="you are an assistant",
   91:         tools=all_registered(),
   92:     )
   93:     assert result.stop_reason == "end_turn"
   94:     assert result.text == "Hello world."
   95:     assert result.turns_used == 1
   96: 
   97: 
   98: # ============================================================
   99: # Test 2 â€” tool_use â†’ tool runs â†’ tool_result â†’ final answer
  100: # ============================================================
  101: 
  102: def test_engine_dispatches_tool_then_finalizes():
  103:     from core import QueryEngine
  104:     from tools import all_registered
  105: 
  106:     # Turn 1: model asks for read_file. Turn 2: model gives final answer.
  107:     client = _ScriptedClient([
  108:         ("tool", "call_1", "read_file", {"file_path": "nonexistent_for_test.txt"}),
  109:         ("text", "I read the file."),
  110:     ])
  111:     engine = QueryEngine(client=client, max_turns=5)
  112:     result = engine.run(
  113:         user_message="read a file",
  114:         system_prompt="sys",
  115:         tools=all_registered(),
  116:     )
  117:     assert result.stop_reason == "end_turn"
  118:     assert result.text == "I read the file."
  119:     assert result.turns_used == 2
  120:     # Conversation must contain: user, assistant(tool_use), user(tool_result), assistant(text).
  121:     roles = [m["role"] for m in result.messages]
  122:     assert roles == ["user", "assistant", "user", "assistant"]
  123:     # The tool_result block must have correct tool_use_id.
  124:     tr_block = result.messages[2]["content"][0]
  125:     assert tr_block["type"] == "tool_result"
  126:     assert tr_block["tool_use_id"] == "call_1"
  127: 
  128: 
  129: # ============================================================
  130: # Test 3 â€” Phase 7 wiring contract: tools= payload excludes deferred tools by default
  131: # ============================================================
  132: 
  133: def test_engine_excludes_deferred_tools_from_first_turn_payload():
  134:     """First turn, no tool_search calls yet: per-turn `tools=` must NOT include
  135:     view_image, list_dir, notebook_edit. tool_search itself MUST be included."""
  136:     from core import QueryEngine
  137:     from tools import all_registered
  138: 
  139:     client = _ScriptedClient([("text", "ok")])
  140:     engine = QueryEngine(client=client, max_turns=2)
  141:     engine.run(
  142:         user_message="hi",
  143:         system_prompt="sys",
  144:         tools=all_registered(),
  145:     )
  146:     sent_tools = client.calls[0]["tools"]
  147:     sent_names = {t["name"] for t in sent_tools}
  148:     assert "tool_search" in sent_names
  149:     assert "view_image" not in sent_names
  150:     assert "list_dir" not in sent_names
  151:     assert "notebook_edit" not in sent_names
  152:     # high-frequency tools must remain visible
  153:     assert "read_file" in sent_names
  154:     assert "edit_file" in sent_names
  155: 
  156: 
  157: # ============================================================
  158: # Test 4 â€” Phase 7 round-trip: tool_search promotes deferred tool into next turn
  159: # ============================================================
  160: 
  161: def test_tool_search_round_trip_promotes_deferred_tool():
  162:     """Phase 8 acceptance: model calls tool_search â†’ query_engine extracts the
  163:     discovered names â†’ next turn's `tools=` payload includes those tools.
  164: 
  165:     The hidden marker `<!-- v5_discovered:NAME --> ` emitted by tool_search is
  166:     extracted via `tool_search_discovered_names()` and the named tool's full
  167:     schema is added to the next turn's payload."""
  168:     from core import QueryEngine
  169:     from tools import all_registered
  170: 
  171:     # Turn 1: model calls tool_search for view_image (a deferred tool).
  172:     # Turn 2: model now calls view_image (its schema was promoted).
  173:     # Turn 3: model gives final answer.
  174:     client = _ScriptedClient([
  175:         ("tool", "call_1", "tool_search", {"query": "select:view_image"}),
  176:         ("tool", "call_2", "view_image", {"file_path": "nonexistent.png"}),
  177:         ("text", "Done."),
  178:     ])
  179:     engine = QueryEngine(client=client, max_turns=5)
  180:     result = engine.run(
  181:         user_message="look at an image",
  182:         system_prompt="sys",
  183:         tools=all_registered(),
  184:     )
  185:     assert result.stop_reason == "end_turn"
  186:     assert result.turns_used == 3
  187: 
  188:     # Turn 1 payload: view_image is NOT in tools=
  189:     turn1_names = {t["name"] for t in client.calls[0]["tools"]}
  190:     assert "view_image" not in turn1_names
  191:     assert "tool_search" in turn1_names
  192: 
  193:     # Turn 2 payload: view_image IS in tools= (promoted by Phase 7 wiring)
  194:     turn2_names = {t["name"] for t in client.calls[1]["tools"]}
  195:     assert "view_image" in turn2_names, (
  196:         "view_image must be promoted into per-turn payload after tool_search "
  197:         "discovered it"
  198:     )
  199: 
  200: 
  201: # ============================================================
  202: # Test 5 â€” IterationBudget gate stops the loop
  203: # ============================================================
  204: 
  205: def test_engine_stops_on_budget_exhausted():
  206:     """Pre-consume the budget so the first turn can't be entered."""
  207:     from core import QueryEngine, IterationBudget
  208:     from tools import all_registered
  209: 
  210:     budget = IterationBudget(max_iterations=2)
  211:     budget.consume()
  212:     budget.consume()  # exhausted
  213: 
  214:     client = _ScriptedClient([("text", "should not be reached")])
  215:     engine = QueryEngine(client=client, max_turns=5, budget=budget)
  216:     result = engine.run(
  217:         user_message="hi",
  218:         system_prompt="sys",
  219:         tools=all_registered(),
  220:     )
  221:     assert result.stop_reason == "budget_exhausted"
  222:     assert result.turns_used == 0
  223:     assert client.calls == []  # client.chat() was never called
  224: 
  225: 
  226: # ============================================================
  227: # Test 6 â€” max_turns cap
  228: # ============================================================
  229: 
  230: def test_engine_stops_at_max_turns():
  231:     """If model never returns end_turn, the loop must exit cleanly at max_turns."""
  232:     from core import QueryEngine
  233:     from tools import all_registered
  234: 
  235:     # Always returns tool_use for read_file â†’ engine never reaches end_turn.
  236:     looping_script = [
  237:         ("tool", f"call_{i}", "read_file", {"file_path": f"x{i}.txt"})
  238:         for i in range(20)
  239:     ]
  240:     client = _ScriptedClient(looping_script)
  241:     engine = QueryEngine(client=client, max_turns=3)
  242:     result = engine.run(
  243:         user_message="loop",
  244:         system_prompt="sys",
  245:         tools=all_registered(),
  246:     )
  247:     assert result.stop_reason == "max_turns"
  248:     assert result.turns_used == 3
  249: 
  250: 
  251: # ============================================================
  252: # Test 7 â€” unknown tool name surfaces error to model
  253: # ============================================================
  254: 
  255: def test_engine_returns_error_tool_result_for_unknown_tool():
  256:     from core import QueryEngine
  257:     from tools import all_registered
  258: 
  259:     client = _ScriptedClient([
  260:         ("tool", "call_1", "definitely_not_a_tool", {}),
  261:         ("text", "ok, sorry"),
  262:     ])
  263:     engine = QueryEngine(client=client, max_turns=5)
  264:     result = engine.run(
  265:         user_message="call a tool that doesn't exist",
  266:         system_prompt="sys",
  267:         tools=all_registered(),
  268:     )
  269:     # Loop continues â€” model gets an error tool_result and can recover
  270:     assert result.stop_reason == "end_turn"
  271:     tr_block = result.messages[2]["content"][0]
  272:     assert tr_block["is_error"] is True
  273:     assert "unknown tool" in tr_block["content"]
  274: 
  275: 
  276: # ============================================================
  277: # Test 8 â€” tool that raises is surfaced to model, not user
  278: # ============================================================
  279: 
  280: def test_engine_traps_tool_exception():
  281:     from core import QueryEngine
  282:     from tools.registry import build_tool, register, all_registered
  283: 
  284:     def boom(args, context=None):
  285:         raise RuntimeError("kaboom")
  286: 
  287:     register(build_tool(
  288:         name="boom_tool",
  289:         description="raises",
  290:         input_schema={"type": "object", "properties": {}},
  291:         execute=boom,
  292:         is_read_only=True,
  293:     ))
  294: 
  295:     client = _ScriptedClient([
  296:         ("tool", "call_1", "boom_tool", {}),
  297:         ("text", "recovered"),
  298:     ])
  299:     engine = QueryEngine(client=client, max_turns=5)
  300:     result = engine.run(
  301:         user_message="call boom",
  302:         system_prompt="sys",
  303:         tools=all_registered(),
  304:     )
  305:     assert result.stop_reason == "end_turn"
  306:     tr = result.messages[2]["content"][0]
  307:     assert tr["is_error"] is True
  308:     assert "RuntimeError" in tr["content"]
  309:     assert "kaboom" in tr["content"]
  310: 
  311: 
  312: # ============================================================
  313: # Test 9 â€” system reminder injected for deferred tools
  314: # ============================================================
  315: 
  316: def test_engine_injects_deferred_tools_system_reminder_on_first_turn():
  317:     from core import QueryEngine
  318:     from tools import all_registered
  319: 
  320:     client = _ScriptedClient([("text", "ok")])
  321:     engine = QueryEngine(client=client, max_turns=2)
  322:     engine.run(
  323:         user_message="hi",
  324:         system_prompt="sys",
  325:         tools=all_registered(),
  326:     )
  327:     sent_messages = client.calls[0]["messages"]
  328:     last_user = sent_messages[-1]
  329:     assert last_user["role"] == "user"
  330:     # The system reminder must be appended as a text block on the user turn
  331:     if isinstance(last_user["content"], list):
  332:         joined = "\n".join(
  333:             blk.get("text", "") for blk in last_user["content"]
  334:             if isinstance(blk, dict)
  335:         )
  336:     else:
  337:         joined = last_user["content"]
  338:     assert "<system-reminder>" in joined
  339:     assert "view_image" in joined
  340:     assert "tool_search" in joined  # mentioned as the loader
  341: 
  342: 
  343: # ============================================================
  344: # Test 10 â€” context_overflow stops cleanly
  345: # ============================================================
  346: 
  347: def test_engine_stops_on_context_overflow():
  348:     """Bedrock raising prompt-too-long must classify as context_overflow and
  349:     return cleanly with stop_reason set."""
  350:     from core import QueryEngine
  351:     from tools import all_registered
  352: 
  353:     class OverflowClient:
  354:         def chat(self, **_kw):
  355:             raise Exception("ValidationException: prompt is too long")
  356: 
  357:     engine = QueryEngine(client=OverflowClient(), max_turns=5)
  358:     result = engine.run(
  359:         user_message="hi",
  360:         system_prompt="sys",
  361:         tools=all_registered(),
  362:     )
  363:     assert result.stop_reason == "context_overflow"
  364:     assert "context_overflow" in (result.error or "")
  365: 
  366: 
  367: # ============================================================
  368: # Test 11 â€” run_one_turn helper
  369: # ============================================================
  370: 
  371: def test_run_one_turn_helper_applies_deferral():
  372:     from core import run_one_turn
  373:     from tools import all_registered
  374: 
  375:     client = _ScriptedClient([("text", "single turn")])
  376:     response = run_one_turn(
  377:         client=client,
  378:         messages=[{"role": "user", "content": "hi"}],
  379:         system_prompt="sys",
  380:         tools=all_registered(),
  381:     )
  382:     assert response.text == "single turn"
  383:     sent_names = {t["name"] for t in client.calls[0]["tools"]}
  384:     assert "view_image" not in sent_names
  385:     assert "tool_search" in sent_names
  386: 
  387: 
  388: # ============================================================
  389: # Test 12 â€” plan mode blocks mutating tools at dispatch
  390: # ============================================================
  391: 
  392: def test_engine_blocks_mutating_tool_in_plan_mode():
  393:     from core import QueryEngine
  394:     from tools import all_registered
  395: 
  396:     client = _ScriptedClient([
  397:         ("tool", "call_1", "edit_file", {"file_path": "x", "old_string": "a", "new_string": "b"}),
  398:         ("text", "noted"),
  399:     ])
  400:     engine = QueryEngine(client=client, max_turns=5)
  401:     result = engine.run(
  402:         user_message="edit a file",
  403:         system_prompt="sys",
  404:         tools=all_registered(),
  405:         plan_mode=True,
  406:     )
  407:     tr = result.messages[2]["content"][0]
  408:     assert tr["is_error"] is True
  409:     assert "plan mode" in tr["content"]

### D:\Github\sagemaker-coding-agent\_archive\compare_code\gg-claude-code-runnable\src\QueryEngine.ts
    1: import { feature } from 'bun:bundle'
    2: import type { ContentBlockParam } from '@anthropic-ai/sdk/resources/messages.mjs'
    3: import { randomUUID } from 'crypto'
    4: import last from 'lodash-es/last.js'
    5: import {
    6:   getSessionId,
    7:   isSessionPersistenceDisabled,
    8: } from 'src/bootstrap/state.js'
    9: import type {
   10:   PermissionMode,
   11:   SDKCompactBoundaryMessage,
   12:   SDKMessage,
   13:   SDKPermissionDenial,
   14:   SDKStatus,
   15:   SDKUserMessageReplay,
   16: } from 'src/entrypoints/agentSdkTypes.js'
   17: import { accumulateUsage, updateUsage } from 'src/services/api/claude.js'
   18: import type { NonNullableUsage } from 'src/services/api/logging.js'
   19: import { EMPTY_USAGE } from 'src/services/api/logging.js'
   20: import stripAnsi from 'strip-ansi'
   21: import type { Command } from './commands.js'
   22: import { getSlashCommandToolSkills } from './commands.js'
   23: import {
   24:   LOCAL_COMMAND_STDERR_TAG,
   25:   LOCAL_COMMAND_STDOUT_TAG,
   26: } from './constants/xml.js'
   27: import {
   28:   getModelUsage,
   29:   getTotalAPIDuration,
   30:   getTotalCost,
   31: } from './cost-tracker.js'
   32: import type { CanUseToolFn } from './hooks/useCanUseTool.js'
   33: import { loadMemoryPrompt } from './memdir/memdir.js'
   34: import { hasAutoMemPathOverride } from './memdir/paths.js'
   35: import { query } from './query.js'
   36: import { categorizeRetryableAPIError } from './services/api/errors.js'
   37: import type { MCPServerConnection } from './services/mcp/types.js'
   38: import type { AppState } from './state/AppState.js'
   39: import { type Tools, type ToolUseContext, toolMatchesName } from './Tool.js'
   40: import type { AgentDefinition } from './tools/AgentTool/loadAgentsDir.js'
   41: import { SYNTHETIC_OUTPUT_TOOL_NAME } from './tools/SyntheticOutputTool/SyntheticOutputTool.js'
   42: import type { Message } from './types/message.js'
   43: import type { OrphanedPermission } from './types/textInputTypes.js'
   44: import { createAbortController } from './utils/abortController.js'
   45: import type { AttributionState } from './utils/commitAttribution.js'
   46: import { getGlobalConfig } from './utils/config.js'
   47: import { getCwd } from './utils/cwd.js'
   48: import { isBareMode, isEnvTruthy } from './utils/envUtils.js'
   49: import { getFastModeState } from './utils/fastMode.js'
   50: import {
   51:   type FileHistoryState,
   52:   fileHistoryEnabled,
   53:   fileHistoryMakeSnapshot,
   54: } from './utils/fileHistory.js'
   55: import {
   56:   cloneFileStateCache,
   57:   type FileStateCache,
   58: } from './utils/fileStateCache.js'
   59: import { headlessProfilerCheckpoint } from './utils/headlessProfiler.js'
   60: import { registerStructuredOutputEnforcement } from './utils/hooks/hookHelpers.js'
   61: import { getInMemoryErrors } from './utils/log.js'
   62: import { countToolCalls, SYNTHETIC_MESSAGES } from './utils/messages.js'
   63: import {
   64:   getMainLoopModel,
   65:   parseUserSpecifiedModel,
   66: } from './utils/model/model.js'
   67: import { loadAllPluginsCacheOnly } from './utils/plugins/pluginLoader.js'
   68: import {
   69:   type ProcessUserInputContext,
   70:   processUserInput,
   71: } from './utils/processUserInput/processUserInput.js'
   72: import { fetchSystemPromptParts } from './utils/queryContext.js'
   73: import { setCwd } from './utils/Shell.js'
   74: import {
   75:   flushSessionStorage,
   76:   recordTranscript,
   77: } from './utils/sessionStorage.js'
   78: import { asSystemPrompt } from './utils/systemPromptType.js'
   79: import { resolveThemeSetting } from './utils/systemTheme.js'
   80: import {
   81:   shouldEnableThinkingByDefault,
   82:   type ThinkingConfig,
   83: } from './utils/thinking.js'
   84: 
   85: // Lazy: MessageSelector.tsx pulls React/ink; only needed for message filtering at query time
   86: /* eslint-disable @typescript-eslint/no-require-imports */
   87: const messageSelector =
   88:   (): typeof import('src/components/MessageSelector.js') =>
   89:     require('src/components/MessageSelector.js')
   90: 
   91: import {
   92:   localCommandOutputToSDKAssistantMessage,
   93:   toSDKCompactMetadata,
   94: } from './utils/messages/mappers.js'
   95: import {
   96:   buildSystemInitMessage,
   97:   sdkCompatToolName,
   98: } from './utils/messages/systemInit.js'
   99: import {
  100:   getScratchpadDir,
  101:   isScratchpadEnabled,
  102: } from './utils/permissions/filesystem.js'
  103: /* eslint-enable @typescript-eslint/no-require-imports */
  104: import {
  105:   handleOrphanedPermission,
  106:   isResultSuccessful,
  107:   normalizeMessage,
  108: } from './utils/queryHelpers.js'
  109: 
  110: // Dead code elimination: conditional import for coordinator mode
  111: /* eslint-disable @typescript-eslint/no-require-imports */
  112: const getCoordinatorUserContext: (
  113:   mcpClients: ReadonlyArray<{ name: string }>,
  114:   scratchpadDir?: string,
  115: ) => { [k: string]: string } = feature('COORDINATOR_MODE')
  116:   ? require('./coordinator/coordinatorMode.js').getCoordinatorUserContext
  117:   : () => ({})
  118: /* eslint-enable @typescript-eslint/no-require-imports */
  119: 
  120: // Dead code elimination: conditional import for snip compaction
  121: /* eslint-disable @typescript-eslint/no-require-imports */
  122: const snipModule = feature('HISTORY_SNIP')
  123:   ? (require('./services/compact/snipCompact.js') as typeof import('./services/compact/snipCompact.js'))
  124:   : null
  125: const snipProjection = feature('HISTORY_SNIP')
  126:   ? (require('./services/compact/snipProjection.js') as typeof import('./services/compact/snipProjection.js'))
  127:   : null
  128: /* eslint-enable @typescript-eslint/no-require-imports */
  129: 
  130: export type QueryEngineConfig = {
  131:   cwd: string
  132:   tools: Tools
  133:   commands: Command[]
  134:   mcpClients: MCPServerConnection[]
  135:   agents: AgentDefinition[]
  136:   canUseTool: CanUseToolFn
  137:   getAppState: () => AppState
  138:   setAppState: (f: (prev: AppState) => AppState) => void
  139:   initialMessages?: Message[]
  140:   readFileCache: FileStateCache
  141:   customSystemPrompt?: string
  142:   appendSystemPrompt?: string
  143:   userSpecifiedModel?: string
  144:   fallbackModel?: string
  145:   thinkingConfig?: ThinkingConfig
  146:   maxTurns?: number
  147:   maxBudgetUsd?: number
  148:   taskBudget?: { total: number }
  149:   jsonSchema?: Record<string, unknown>
  150:   verbose?: boolean
  151:   replayUserMessages?: boolean
  152:   /** Handler for URL elicitations triggered by MCP tool -32042 errors. */
  153:   handleElicitation?: ToolUseContext['handleElicitation']
  154:   includePartialMessages?: boolean
  155:   setSDKStatus?: (status: SDKStatus) => void
  156:   abortController?: AbortController
  157:   orphanedPermission?: OrphanedPermission
  158:   /**
  159:    * Snip-boundary handler: receives each yielded system message plus the
  160:    * current mutableMessages store. Returns undefined if the message is not a
  161:    * snip boundary; otherwise returns the replayed snip result. Injected by
  162:    * ask() when HISTORY_SNIP is enabled so feature-gated strings stay inside
  163:    * the gated module (keeps QueryEngine free of excluded strings and testable
  164:    * despite feature() returning false under bun test). SDK-only: the REPL
  165:    * keeps full history for UI scrollback and projects on demand via
  166:    * projectSnippedView; QueryEngine truncates here to bound memory in long
  167:    * headless sessions (no UI to preserve).
  168:    */
  169:   snipReplay?: (
  170:     yieldedSystemMsg: Message,
  171:     store: Message[],
  172:   ) => { messages: Message[]; executed: boolean } | undefined
  173: }
  174: 
  175: /**
  176:  * QueryEngine owns the query lifecycle and session state for a conversation.
  177:  * It extracts the core logic from ask() into a standalone class that can be
  178:  * used by both the headless/SDK path and (in a future phase) the REPL.
  179:  *
  180:  * One QueryEngine per conversation. Each submitMessage() call starts a new
  181:  * turn within the same conversation. State (messages, file cache, usage, etc.)
  182:  * persists across turns.
  183:  */
  184: export class QueryEngine {
  185:   private config: QueryEngineConfig
  186:   private mutableMessages: Message[]
  187:   private abortController: AbortController
  188:   private permissionDenials: SDKPermissionDenial[]
  189:   private totalUsage: NonNullableUsage
  190:   private hasHandledOrphanedPermission = false
  191:   private readFileState: FileStateCache
  192:   // Turn-scoped skill discovery tracking (feeds was_discovered on
  193:   // tengu_skill_tool_invocation). Must persist across the two
  194:   // processUserInputContext rebuilds inside submitMessage, but is cleared
  195:   // at the start of each submitMessage to avoid unbounded growth across
  196:   // many turns in SDK mode.
  197:   private discoveredSkillNames = new Set<string>()
  198:   private loadedNestedMemoryPaths = new Set<string>()
  199: 
  200:   constructor(config: QueryEngineConfig) {
  201:     this.config = config
  202:     this.mutableMessages = config.initialMessages ?? []
  203:     this.abortController = config.abortController ?? createAbortController()
  204:     this.permissionDenials = []
  205:     this.readFileState = config.readFileCache
  206:     this.totalUsage = EMPTY_USAGE
  207:   }
  208: 
  209:   async *submitMessage(
  210:     prompt: string | ContentBlockParam[],
  211:     options?: { uuid?: string; isMeta?: boolean },
  212:   ): AsyncGenerator<SDKMessage, void, unknown> {
  213:     const {
  214:       cwd,
  215:       commands,
  216:       tools,
  217:       mcpClients,
  218:       verbose = false,
  219:       thinkingConfig,
  220:       maxTurns,
  221:       maxBudgetUsd,
  222:       taskBudget,
  223:       canUseTool,
  224:       customSystemPrompt,
  225:       appendSystemPrompt,
  226:       userSpecifiedModel,
  227:       fallbackModel,
  228:       jsonSchema,
  229:       getAppState,
  230:       setAppState,
  231:       replayUserMessages = false,
  232:       includePartialMessages = false,
  233:       agents = [],
  234:       setSDKStatus,
  235:       orphanedPermission,
  236:     } = this.config
  237: 
  238:     this.discoveredSkillNames.clear()
  239:     setCwd(cwd)
  240:     const persistSession = !isSessionPersistenceDisabled()
  241:     const startTime = Date.now()
  242: 
  243:     // Wrap canUseTool to track permission denials
  244:     const wrappedCanUseTool: CanUseToolFn = async (
  245:       tool,
  246:       input,
  247:       toolUseContext,
  248:       assistantMessage,
  249:       toolUseID,
  250:       forceDecision,
  251:     ) => {
  252:       const result = await canUseTool(
  253:         tool,
  254:         input,
  255:         toolUseContext,
  256:         assistantMessage,
  257:         toolUseID,
  258:         forceDecision,
  259:       )
  260: 
  261:       // Track denials for SDK reporting
  262:       if (result.behavior !== 'allow') {
  263:         this.permissionDenials.push({
  264:           tool_name: sdkCompatToolName(tool.name),
  265:           tool_use_id: toolUseID,
  266:           tool_input: input,
  267:         })
  268:       }
  269: 
  270:       return result
  271:     }
  272: 
  273:     const initialAppState = getAppState()
  274:     const initialMainLoopModel = userSpecifiedModel
  275:       ? parseUserSpecifiedModel(userSpecifiedModel)
  276:       : getMainLoopModel()
  277: 
  278:     const initialThinkingConfig: ThinkingConfig = thinkingConfig
  279:       ? thinkingConfig
  280:       : shouldEnableThinkingByDefault() !== false
  281:         ? { type: 'adaptive' }
  282:         : { type: 'disabled' }
  283: 
  284:     headlessProfilerCheckpoint('before_getSystemPrompt')
  285:     // Narrow once so TS tracks the type through the conditionals below.
  286:     const customPrompt =
  287:       typeof customSystemPrompt === 'string' ? customSystemPrompt : undefined
  288:     const {
  289:       defaultSystemPrompt,
  290:       userContext: baseUserContext,
  291:       systemContext,
  292:     } = await fetchSystemPromptParts({
  293:       tools,
  294:       mainLoopModel: initialMainLoopModel,
  295:       additionalWorkingDirectories: Array.from(
  296:         initialAppState.toolPermissionContext.additionalWorkingDirectories.keys(),
  297:       ),
  298:       mcpClients,
  299:       customSystemPrompt: customPrompt,
  300:     })
  301:     headlessProfilerCheckpoint('after_getSystemPrompt')
  302:     const userContext = {
  303:       ...baseUserContext,
  304:       ...getCoordinatorUserContext(
  305:         mcpClients,
  306:         isScratchpadEnabled() ? getScratchpadDir() : undefined,
  307:       ),
  308:     }
  309: 
  310:     // When an SDK caller provides a custom system prompt AND has set
  311:     // CLAUDE_COWORK_MEMORY_PATH_OVERRIDE, inject the memory-mechanics prompt.
  312:     // The env var is an explicit opt-in signal â€” the caller has wired up
  313:     // a memory directory and needs Claude to know how to use it (which
  314:     // Write/Edit tools to call, MEMORY.md filename, loading semantics).
  315:     // The caller can layer their own policy text via appendSystemPrompt.
  316:     const memoryMechanicsPrompt =
  317:       customPrompt !== undefined && hasAutoMemPathOverride()
  318:         ? await loadMemoryPrompt()
  319:         : null
  320: 
  321:     const systemPrompt = asSystemPrompt([
  322:       ...(customPrompt !== undefined ? [customPrompt] : defaultSystemPrompt),
  323:       ...(memoryMechanicsPrompt ? [memoryMechanicsPrompt] : []),
  324:       ...(appendSystemPrompt ? [appendSystemPrompt] : []),
  325:     ])
  326: 
  327:     // Register function hook for structured output enforcement
  328:     const hasStructuredOutputTool = tools.some(t =>
  329:       toolMatchesName(t, SYNTHETIC_OUTPUT_TOOL_NAME),
  330:     )
  331:     if (jsonSchema && hasStructuredOutputTool) {
  332:       registerStructuredOutputEnforcement(setAppState, getSessionId())
  333:     }
  334: 
  335:     let processUserInputContext: ProcessUserInputContext = {
  336:       messages: this.mutableMessages,
  337:       // Slash commands that mutate the message array (e.g. /force-snip)
  338:       // call setMessages(fn).  In interactive mode this writes back to
  339:       // AppState; in print mode we write back to mutableMessages so the
  340:       // rest of the query loop (push at :389, snapshot at :392) sees
  341:       // the result.  The second processUserInputContext below (after
  342:       // slash-command processing) keeps the no-op â€” nothing else calls
  343:       // setMessages past that point.
  344:       setMessages: fn => {
  345:         this.mutableMessages = fn(this.mutableMessages)
  346:       },
  347:       onChangeAPIKey: () => {},
  348:       handleElicitation: this.config.handleElicitation,
  349:       options: {
  350:         commands,
  351:         debug: false, // we use stdout, so don't want to clobber it
  352:         tools,
  353:         verbose,
  354:         mainLoopModel: initialMainLoopModel,
  355:         thinkingConfig: initialThinkingConfig,
  356:         mcpClients,
  357:         mcpResources: {},
  358:         ideInstallationStatus: null,
  359:         isNonInteractiveSession: true,
  360:         customSystemPrompt,
  361:         appendSystemPrompt,
  362:         agentDefinitions: { activeAgents: agents, allAgents: [] },
  363:         theme: resolveThemeSetting(getGlobalConfig().theme),
  364:         maxBudgetUsd,
  365:       },
  366:       getAppState,
  367:       setAppState,
  368:       abortController: this.abortController,
  369:       readFileState: this.readFileState,
  370:       nestedMemoryAttachmentTriggers: new Set<string>(),
  371:       loadedNestedMemoryPaths: this.loadedNestedMemoryPaths,
  372:       dynamicSkillDirTriggers: new Set<string>(),
  373:       discoveredSkillNames: this.discoveredSkillNames,
  374:       setInProgressToolUseIDs: () => {},
  375:       setResponseLength: () => {},
  376:       updateFileHistoryState: (
  377:         updater: (prev: FileHistoryState) => FileHistoryState,
  378:       ) => {
  379:         setAppState(prev => {
  380:           const updated = updater(prev.fileHistory)
  381:           if (updated === prev.fileHistory) return prev
  382:           return { ...prev, fileHistory: updated }
  383:         })
  384:       },
  385:       updateAttributionState: (
  386:         updater: (prev: AttributionState) => AttributionState,
  387:       ) => {
  388:         setAppState(prev => {
  389:           const updated = updater(prev.attribution)
  390:           if (updated === prev.attribution) return prev
  391:           return { ...prev, attribution: updated }
  392:         })
  393:       },
  394:       setSDKStatus,
  395:     }
  396: 
  397:     // Handle orphaned permission (only once per engine lifetime)
  398:     if (orphanedPermission && !this.hasHandledOrphanedPermission) {
  399:       this.hasHandledOrphanedPermission = true
  400:       for await (const message of handleOrphanedPermission(
  401:         orphanedPermission,
  402:         tools,
  403:         this.mutableMessages,
  404:         processUserInputContext,
  405:       )) {
  406:         yield message
  407:       }
  408:     }
  409: 
  410:     const {
  411:       messages: messagesFromUserInput,
  412:       shouldQuery,
  413:       allowedTools,
  414:       model: modelFromUserInput,
  415:       resultText,
  416:     } = await processUserInput({
  417:       input: prompt,
  418:       mode: 'prompt',
  419:       setToolJSX: () => {},
  420:       context: {
  421:         ...processUserInputContext,
  422:         messages: this.mutableMessages,
  423:       },
  424:       messages: this.mutableMessages,
  425:       uuid: options?.uuid,
  426:       isMeta: options?.isMeta,
  427:       querySource: 'sdk',
  428:     })
  429: 
  430:     // Push new messages, including user input and any attachments
  431:     this.mutableMessages.push(...messagesFromUserInput)
  432: 
  433:     // Update params to reflect updates from processing /slash commands
  434:     const messages = [...this.mutableMessages]
  435: 
  436:     // Persist the user's message(s) to transcript BEFORE entering the query
  437:     // loop. The for-await below only calls recordTranscript when ask() yields
  438:     // an assistant/user/compact_boundary message â€” which doesn't happen until
  439:     // the API responds. If the process is killed before that (e.g. user clicks
  440:     // Stop in cowork seconds after send), the transcript is left with only
  441:     // queue-operation entries; getLastSessionLog filters those out, returns
  442:     // null, and --resume fails with "No conversation found". Writing now makes
  443:     // the transcript resumable from the point the user message was accepted,
  444:     // even if no API response ever arrives.
  445:     //
  446:     // --bare / SIMPLE: fire-and-forget. Scripted calls don't --resume after
  447:     // kill-mid-request. The await is ~4ms on SSD, ~30ms under disk contention
  448:     // â€” the single largest controllable critical-path cost after module eval.
  449:     // Transcript is still written (for post-hoc debugging); just not blocking.
  450:     if (persistSession && messagesFromUserInput.length > 0) {
  451:       const transcriptPromise = recordTranscript(messages)
  452:       if (isBareMode()) {
  453:         void transcriptPromise
  454:       } else {
  455:         await transcriptPromise
  456:         if (
  457:           isEnvTruthy(process.env.CLAUDE_CODE_EAGER_FLUSH) ||
  458:           isEnvTruthy(process.env.CLAUDE_CODE_IS_COWORK)
  459:         ) {
  460:           await flushSessionStorage()
  461:         }
  462:       }
  463:     }
  464: 
  465:     // Filter messages that should be acknowledged after transcript
  466:     const replayableMessages = messagesFromUserInput.filter(
  467:       msg =>
  468:         (msg.type === 'user' &&
  469:           !msg.isMeta && // Skip synthetic caveat messages
  470:           !msg.toolUseResult && // Skip tool results (they'll be acked from query)
  471:           messageSelector().selectableUserMessagesFilter(msg)) || // Skip non-user-authored messages (task notifications, etc.)
  472:         (msg.type === 'system' && msg.subtype === 'compact_boundary'), // Always ack compact boundaries
  473:     )
  474:     const messagesToAck = replayUserMessages ? replayableMessages : []
  475: 
  476:     // Update the ToolPermissionContext based on user input processing (as necessary)
  477:     setAppState(prev => ({
  478:       ...prev,
  479:       toolPermissionContext: {
  480:         ...prev.toolPermissionContext,
  481:         alwaysAllowRules: {
  482:           ...prev.toolPermissionContext.alwaysAllowRules,
  483:           command: allowedTools,
  484:         },
  485:       },
  486:     }))
  487: 
  488:     const mainLoopModel = modelFromUserInput ?? initialMainLoopModel
  489: 
  490:     // Recreate after processing the prompt to pick up updated messages and
  491:     // model (from slash commands).
  492:     processUserInputContext = {
  493:       messages,
  494:       setMessages: () => {},
  495:       onChangeAPIKey: () => {},
  496:       handleElicitation: this.config.handleElicitation,
  497:       options: {
  498:         commands,
  499:         debug: false,
  500:         tools,
  501:         verbose,
  502:         mainLoopModel,
  503:         thinkingConfig: initialThinkingConfig,
  504:         mcpClients,
  505:         mcpResources: {},
  506:         ideInstallationStatus: null,
  507:         isNonInteractiveSession: true,
  508:         customSystemPrompt,
  509:         appendSystemPrompt,
  510:         theme: resolveThemeSetting(getGlobalConfig().theme),
  511:         agentDefinitions: { activeAgents: agents, allAgents: [] },
  512:         maxBudgetUsd,
  513:       },
  514:       getAppState,
  515:       setAppState,
  516:       abortController: this.abortController,
  517:       readFileState: this.readFileState,
  518:       nestedMemoryAttachmentTriggers: new Set<string>(),
  519:       loadedNestedMemoryPaths: this.loadedNestedMemoryPaths,
  520:       dynamicSkillDirTriggers: new Set<string>(),
  521:       discoveredSkillNames: this.discoveredSkillNames,
  522:       setInProgressToolUseIDs: () => {},
  523:       setResponseLength: () => {},
  524:       updateFileHistoryState: processUserInputContext.updateFileHistoryState,
  525:       updateAttributionState: processUserInputContext.updateAttributionState,
  526:       setSDKStatus,
  527:     }
  528: 
  529:     headlessProfilerCheckpoint('before_skills_plugins')
  530:     // Cache-only: headless/SDK/CCR startup must not block on network for
  531:     // ref-tracked plugins. CCR populates the cache via CLAUDE_CODE_SYNC_PLUGIN_INSTALL
  532:     // (headlessPluginInstall) or CLAUDE_CODE_PLUGIN_SEED_DIR before this runs;
  533:     // SDK callers that need fresh source can call /reload-plugins.
  534:     const [skills, { enabled: enabledPlugins }] = await Promise.all([
  535:       getSlashCommandToolSkills(getCwd()),
  536:       loadAllPluginsCacheOnly(),
  537:     ])
  538:     headlessProfilerCheckpoint('after_skills_plugins')
  539: 
  540:     yield buildSystemInitMessage({
  541:       tools,
  542:       mcpClients,
  543:       model: mainLoopModel,
  544:       permissionMode: initialAppState.toolPermissionContext
  545:         .mode as PermissionMode, // TODO: avoid the cast
  546:       commands,
  547:       agents,
  548:       skills,
  549:       plugins: enabledPlugins,
  550:       fastMode: initialAppState.fastMode,
  551:     })
  552: 
  553:     // Record when system message is yielded for headless latency tracking
  554:     headlessProfilerCheckpoint('system_message_yielded')
  555: 
  556:     if (!shouldQuery) {
  557:       // Return the results of local slash commands.
  558:       // Use messagesFromUserInput (not replayableMessages) for command output
  559:       // because selectableUserMessagesFilter excludes local-command-stdout tags.
  560:       for (const msg of messagesFromUserInput) {
  561:         if (
  562:           msg.type === 'user' &&
  563:           typeof msg.message.content === 'string' &&
  564:           (msg.message.content.includes(`<${LOCAL_COMMAND_STDOUT_TAG}>`) ||
  565:             msg.message.content.includes(`<${LOCAL_COMMAND_STDERR_TAG}>`) ||
  566:             msg.isCompactSummary)
  567:         ) {
  568:           yield {
  569:             type: 'user',
  570:             message: {
  571:               ...msg.message,
  572:               content: stripAnsi(msg.message.content),
  573:             },
  574:             session_id: getSessionId(),
  575:             parent_tool_use_id: null,
  576:             uuid: msg.uuid,
  577:             timestamp: msg.timestamp,
  578:             isReplay: !msg.isCompactSummary,
  579:             isSynthetic: msg.isMeta || msg.isVisibleInTranscriptOnly,
  580:           } as SDKUserMessageReplay
  581:         }
  582: 
  583:         // Local command output â€” yield as a synthetic assistant message so
  584:         // RC renders it as assistant-style text rather than a user bubble.
  585:         // Emitted as assistant (not the dedicated SDKLocalCommandOutputMessage
  586:         // system subtype) so mobile clients + session-ingress can parse it.
  587:         if (
  588:           msg.type === 'system' &&
  589:           msg.subtype === 'local_command' &&
  590:           typeof msg.content === 'string' &&
  591:           (msg.content.includes(`<${LOCAL_COMMAND_STDOUT_TAG}>`) ||
  592:             msg.content.includes(`<${LOCAL_COMMAND_STDERR_TAG}>`))
  593:         ) {
  594:           yield localCommandOutputToSDKAssistantMessage(msg.content, msg.uuid)
  595:         }
  596: 
  597:         if (msg.type === 'system' && msg.subtype === 'compact_boundary') {
  598:           yield {
  599:             type: 'system',
  600:             subtype: 'compact_boundary' as const,
  601:             session_id: getSessionId(),
  602:             uuid: msg.uuid,
  603:             compact_metadata: toSDKCompactMetadata(msg.compactMetadata),
  604:           } as SDKCompactBoundaryMessage
  605:         }
  606:       }
  607: 
  608:       if (persistSession) {
  609:         await recordTranscript(messages)
  610:         if (
  611:           isEnvTruthy(process.env.CLAUDE_CODE_EAGER_FLUSH) ||
  612:           isEnvTruthy(process.env.CLAUDE_CODE_IS_COWORK)
  613:         ) {
  614:           await flushSessionStorage()
  615:         }
  616:       }
  617: 
  618:       yield {
  619:         type: 'result',
  620:         subtype: 'success',
  621:         is_error: false,
  622:         duration_ms: Date.now() - startTime,
  623:         duration_api_ms: getTotalAPIDuration(),
  624:         num_turns: messages.length - 1,
  625:         result: resultText ?? '',
  626:         stop_reason: null,
  627:         session_id: getSessionId(),
  628:         total_cost_usd: getTotalCost(),
  629:         usage: this.totalUsage,
  630:         modelUsage: getModelUsage(),
  631:         permission_denials: this.permissionDenials,
  632:         fast_mode_state: getFastModeState(
  633:           mainLoopModel,
  634:           initialAppState.fastMode,
  635:         ),
  636:         uuid: randomUUID(),
  637:       }
  638:       return
  639:     }
  640: 
  641:     if (fileHistoryEnabled() && persistSession) {
  642:       messagesFromUserInput
  643:         .filter(messageSelector().selectableUserMessagesFilter)
  644:         .forEach(message => {
  645:           void fileHistoryMakeSnapshot(
  646:             (updater: (prev: FileHistoryState) => FileHistoryState) => {
  647:               setAppState(prev => ({
  648:                 ...prev,
  649:                 fileHistory: updater(prev.fileHistory),
  650:               }))
  651:             },
  652:             message.uuid,
  653:           )
  654:         })
  655:     }
  656: 
  657:     // Track current message usage (reset on each message_start)
  658:     let currentMessageUsage: NonNullableUsage = EMPTY_USAGE
  659:     let turnCount = 1
  660:     let hasAcknowledgedInitialMessages = false
  661:     // Track structured output from StructuredOutput tool calls
  662:     let structuredOutputFromTool: unknown
  663:     // Track the last stop_reason from assistant messages
  664:     let lastStopReason: string | null = null
  665:     // Reference-based watermark so error_during_execution's errors[] is
  666:     // turn-scoped. A length-based index breaks when the 100-entry ring buffer
  667:     // shift()s during the turn â€” the index slides. If this entry is rotated
  668:     // out, lastIndexOf returns -1 and we include everything (safe fallback).
  669:     const errorLogWatermark = getInMemoryErrors().at(-1)
  670:     // Snapshot count before this query for delta-based retry limiting
  671:     const initialStructuredOutputCalls = jsonSchema
  672:       ? countToolCalls(this.mutableMessages, SYNTHETIC_OUTPUT_TOOL_NAME)
  673:       : 0
  674: 
  675:     for await (const message of query({
  676:       messages,
  677:       systemPrompt,
  678:       userContext,
  679:       systemContext,
  680:       canUseTool: wrappedCanUseTool,
  681:       toolUseContext: processUserInputContext,
  682:       fallbackModel,
  683:       querySource: 'sdk',
  684:       maxTurns,
  685:       taskBudget,
  686:     })) {
  687:       // Record assistant, user, and compact boundary messages
  688:       if (
  689:         message.type === 'assistant' ||
  690:         message.type === 'user' ||
  691:         (message.type === 'system' && message.subtype === 'compact_boundary')
  692:       ) {
  693:         // Before writing a compact boundary, flush any in-memory-only
  694:         // messages up through the preservedSegment tail. Attachments and
  695:         // progress are now recorded inline (their switch cases below), but
  696:         // this flush still matters for the preservedSegment tail walk.
  697:         // If the SDK subprocess restarts before then (claude-desktop kills
  698:         // between turns), tailUuid points to a never-written message â†’
  699:         // applyPreservedSegmentRelinks fails its tailâ†’head walk â†’ returns
  700:         // without pruning â†’ resume loads full pre-compact history.
  701:         if (
  702:           persistSession &&
  703:           message.type === 'system' &&
  704:           message.subtype === 'compact_boundary'
  705:         ) {
  706:           const tailUuid = message.compactMetadata?.preservedSegment?.tailUuid
  707:           if (tailUuid) {
  708:             const tailIdx = this.mutableMessages.findLastIndex(
  709:               m => m.uuid === tailUuid,
  710:             )
  711:             if (tailIdx !== -1) {
  712:               await recordTranscript(this.mutableMessages.slice(0, tailIdx + 1))
  713:             }
  714:           }
  715:         }
  716:         messages.push(message)
  717:         if (persistSession) {
  718:           // Fire-and-forget for assistant messages. claude.ts yields one
  719:           // assistant message per content block, then mutates the last
  720:           // one's message.usage/stop_reason on message_delta â€” relying on
  721:           // the write queue's 100ms lazy jsonStringify. Awaiting here
  722:           // blocks ask()'s generator, so message_delta can't run until
  723:           // every block is consumed; the drain timer (started at block 1)
  724:           // elapses first. Interactive CC doesn't hit this because
  725:           // useLogMessages.ts fire-and-forgets. enqueueWrite is
  726:           // order-preserving so fire-and-forget here is safe.
  727:           if (message.type === 'assistant') {
  728:             void recordTranscript(messages)
  729:           } else {
  730:             await recordTranscript(messages)
  731:           }
  732:         }
  733: 
  734:         // Acknowledge initial user messages after first transcript recording
  735:         if (!hasAcknowledgedInitialMessages && messagesToAck.length > 0) {
  736:           hasAcknowledgedInitialMessages = true
  737:           for (const msgToAck of messagesToAck) {
  738:             if (msgToAck.type === 'user') {
  739:               yield {
  740:                 type: 'user',
  741:                 message: msgToAck.message,
  742:                 session_id: getSessionId(),
  743:                 parent_tool_use_id: null,
  744:                 uuid: msgToAck.uuid,
  745:                 timestamp: msgToAck.timestamp,
  746:                 isReplay: true,
  747:               } as SDKUserMessageReplay
  748:             }
  749:           }
  750:         }
  751:       }
  752: 
  753:       if (message.type === 'user') {
  754:         turnCount++
  755:       }
  756: 
  757:       switch (message.type) {
  758:         case 'tombstone':
  759:           // Tombstone messages are control signals for removing messages, skip them
  760:           break
  761:         case 'assistant':
  762:           // Capture stop_reason if already set (synthetic messages). For
  763:           // streamed responses, this is null at content_block_stop time;
  764:           // the real value arrives via message_delta (handled below).
  765:           if (message.message.stop_reason != null) {
  766:             lastStopReason = message.message.stop_reason
  767:           }
  768:           this.mutableMessages.push(message)
  769:           yield* normalizeMessage(message)
  770:           break
  771:         case 'progress':
  772:           this.mutableMessages.push(message)
  773:           // Record inline so the dedup loop in the next ask() call sees it
  774:           // as already-recorded. Without this, deferred progress interleaves
  775:           // with already-recorded tool_results in mutableMessages, and the
  776:           // dedup walk freezes startingParentUuid at the wrong message â€”
  777:           // forking the chain and orphaning the conversation on resume.
  778:           if (persistSession) {
  779:             messages.push(message)
  780:             void recordTranscript(messages)
  781:           }
  782:           yield* normalizeMessage(message)
  783:           break
  784:         case 'user':
  785:           this.mutableMessages.push(message)
  786:           yield* normalizeMessage(message)
  787:           break
  788:         case 'stream_event':
  789:           if (message.event.type === 'message_start') {
  790:             // Reset current message usage for new message
  791:             currentMessageUsage = EMPTY_USAGE
  792:             currentMessageUsage = updateUsage(
  793:               currentMessageUsage,
  794:               message.event.message.usage,
  795:             )
  796:           }
  797:           if (message.event.type === 'message_delta') {
  798:             currentMessageUsage = updateUsage(
  799:               currentMessageUsage,
  800:               message.event.usage,
  801:             )
  802:             // Capture stop_reason from message_delta. The assistant message
  803:             // is yielded at content_block_stop with stop_reason=null; the
  804:             // real value only arrives here (see claude.ts message_delta
  805:             // handler). Without this, result.stop_reason is always null.
  806:             if (message.event.delta.stop_reason != null) {
  807:               lastStopReason = message.event.delta.stop_reason
  808:             }
  809:           }
  810:           if (message.event.type === 'message_stop') {
  811:             // Accumulate current message usage into total
  812:             this.totalUsage = accumulateUsage(
  813:               this.totalUsage,
  814:               currentMessageUsage,
  815:             )
  816:           }
  817: 
  818:           if (includePartialMessages) {
  819:             yield {
  820:               type: 'stream_event' as const,
  821:               event: message.event,
  822:               session_id: getSessionId(),
  823:               parent_tool_use_id: null,
  824:               uuid: randomUUID(),
  825:             }
  826:           }
  827: 
  828:           break
  829:         case 'attachment':
  830:           this.mutableMessages.push(message)
  831:           // Record inline (same reason as progress above).
  832:           if (persistSession) {
  833:             messages.push(message)
  834:             void recordTranscript(messages)
  835:           }
  836: 
  837:           // Extract structured output from StructuredOutput tool calls
  838:           if (message.attachment.type === 'structured_output') {
  839:             structuredOutputFromTool = message.attachment.data
  840:           }
  841:           // Handle max turns reached signal from query.ts
  842:           else if (message.attachment.type === 'max_turns_reached') {
  843:             if (persistSession) {
  844:               if (
  845:                 isEnvTruthy(process.env.CLAUDE_CODE_EAGER_FLUSH) ||
  846:                 isEnvTruthy(process.env.CLAUDE_CODE_IS_COWORK)
  847:               ) {
  848:                 await flushSessionStorage()
  849:               }
  850:             }
  851:             yield {
  852:               type: 'result',
  853:               subtype: 'error_max_turns',
  854:               duration_ms: Date.now() - startTime,
  855:               duration_api_ms: getTotalAPIDuration(),
  856:               is_error: true,
  857:               num_turns: message.attachment.turnCount,
  858:               stop_reason: lastStopReason,
  859:               session_id: getSessionId(),
  860:               total_cost_usd: getTotalCost(),
  861:               usage: this.totalUsage,
  862:               modelUsage: getModelUsage(),
  863:               permission_denials: this.permissionDenials,
  864:               fast_mode_state: getFastModeState(
  865:                 mainLoopModel,
  866:                 initialAppState.fastMode,
  867:               ),
  868:               uuid: randomUUID(),
  869:               errors: [
  870:                 `Reached maximum number of turns (${message.attachment.maxTurns})`,
  871:               ],
  872:             }
  873:             return
  874:           }
  875:           // Yield queued_command attachments as SDK user message replays
  876:           else if (
  877:             replayUserMessages &&
  878:             message.attachment.type === 'queued_command'
  879:           ) {
  880:             yield {
  881:               type: 'user',
  882:               message: {
  883:                 role: 'user' as const,
  884:                 content: message.attachment.prompt,
  885:               },
  886:               session_id: getSessionId(),
  887:               parent_tool_use_id: null,
  888:               uuid: message.attachment.source_uuid || message.uuid,
  889:               timestamp: message.timestamp,
  890:               isReplay: true,
  891:             } as SDKUserMessageReplay
  892:           }
  893:           break
  894:         case 'stream_request_start':
  895:           // Don't yield stream request start messages
  896:           break
  897:         case 'system': {
  898:           // Snip boundary: replay on our store to remove zombie messages and
  899:           // stale markers. The yielded boundary is a signal, not data to push â€”
  900:           // the replay produces its own equivalent boundary. Without this,
  901:           // markers persist and re-trigger on every turn, and mutableMessages
  902:           // never shrinks (memory leak in long SDK sessions). The subtype
  903:           // check lives inside the injected callback so feature-gated strings
  904:           // stay out of this file (excluded-strings check).
  905:           const snipResult = this.config.snipReplay?.(
  906:             message,
  907:             this.mutableMessages,
  908:           )
  909:           if (snipResult !== undefined) {
  910:             if (snipResult.executed) {
  911:               this.mutableMessages.length = 0
  912:               this.mutableMessages.push(...snipResult.messages)
  913:             }
  914:             break
  915:           }
  916:           this.mutableMessages.push(message)
  917:           // Yield compact boundary messages to SDK
  918:           if (
  919:             message.subtype === 'compact_boundary' &&
  920:             message.compactMetadata
  921:           ) {
  922:             // Release pre-compaction messages for GC. The boundary was just
  923:             // pushed so it's the last element. query.ts already uses
  924:             // getMessagesAfterCompactBoundary() internally, so only
  925:             // post-boundary messages are needed going forward.
  926:             const mutableBoundaryIdx = this.mutableMessages.length - 1
  927:             if (mutableBoundaryIdx > 0) {
  928:               this.mutableMessages.splice(0, mutableBoundaryIdx)
  929:             }
  930:             const localBoundaryIdx = messages.length - 1
  931:             if (localBoundaryIdx > 0) {
  932:               messages.splice(0, localBoundaryIdx)
  933:             }
  934: 
  935:             yield {
  936:               type: 'system',
  937:               subtype: 'compact_boundary' as const,
  938:               session_id: getSessionId(),
  939:               uuid: message.uuid,
  940:               compact_metadata: toSDKCompactMetadata(message.compactMetadata),
  941:             }
  942:           }
  943:           if (message.subtype === 'api_error') {
  944:             yield {
  945:               type: 'system',
  946:               subtype: 'api_retry' as const,
  947:               attempt: message.retryAttempt,
  948:               max_retries: message.maxRetries,
  949:               retry_delay_ms: message.retryInMs,
  950:               error_status: message.error.status ?? null,
  951:               error: categorizeRetryableAPIError(message.error),
  952:               session_id: getSessionId(),
  953:               uuid: message.uuid,
  954:             }
  955:           }
  956:           // Don't yield other system messages in headless mode
  957:           break
  958:         }
  959:         case 'tool_use_summary':
  960:           // Yield tool use summary messages to SDK
  961:           yield {
  962:             type: 'tool_use_summary' as const,
  963:             summary: message.summary,
  964:             preceding_tool_use_ids: message.precedingToolUseIds,
  965:             session_id: getSessionId(),
  966:             uuid: message.uuid,
  967:           }
  968:           break
  969:       }
  970: 
  971:       // Check if USD budget has been exceeded
  972:       if (maxBudgetUsd !== undefined && getTotalCost() >= maxBudgetUsd) {
  973:         if (persistSession) {
  974:           if (
  975:             isEnvTruthy(process.env.CLAUDE_CODE_EAGER_FLUSH) ||
  976:             isEnvTruthy(process.env.CLAUDE_CODE_IS_COWORK)
  977:           ) {
  978:             await flushSessionStorage()
  979:           }
  980:         }
  981:         yield {
  982:           type: 'result',
  983:           subtype: 'error_max_budget_usd',
  984:           duration_ms: Date.now() - startTime,
  985:           duration_api_ms: getTotalAPIDuration(),
  986:           is_error: true,
  987:           num_turns: turnCount,
  988:           stop_reason: lastStopReason,
  989:           session_id: getSessionId(),
  990:           total_cost_usd: getTotalCost(),
  991:           usage: this.totalUsage,
  992:           modelUsage: getModelUsage(),
  993:           permission_denials: this.permissionDenials,
  994:           fast_mode_state: getFastModeState(
  995:             mainLoopModel,
  996:             initialAppState.fastMode,
  997:           ),
  998:           uuid: randomUUID(),
  999:           errors: [`Reached maximum budget ($${maxBudgetUsd})`],
 1000:         }
 1001:         return
 1002:       }
 1003: 
 1004:       // Check if structured output retry limit exceeded (only on user messages)
 1005:       if (message.type === 'user' && jsonSchema) {
 1006:         const currentCalls = countToolCalls(
 1007:           this.mutableMessages,
 1008:           SYNTHETIC_OUTPUT_TOOL_NAME,
 1009:         )
 1010:         const callsThisQuery = currentCalls - initialStructuredOutputCalls
 1011:         const maxRetries = parseInt(
 1012:           process.env.MAX_STRUCTURED_OUTPUT_RETRIES || '5',
 1013:           10,
 1014:         )
 1015:         if (callsThisQuery >= maxRetries) {
 1016:           if (persistSession) {
 1017:             if (
 1018:               isEnvTruthy(process.env.CLAUDE_CODE_EAGER_FLUSH) ||
 1019:               isEnvTruthy(process.env.CLAUDE_CODE_IS_COWORK)
 1020:             ) {
 1021:               await flushSessionStorage()
 1022:             }
 1023:           }
 1024:           yield {
 1025:             type: 'result',
 1026:             subtype: 'error_max_structured_output_retries',
 1027:             duration_ms: Date.now() - startTime,
 1028:             duration_api_ms: getTotalAPIDuration(),
 1029:             is_error: true,
 1030:             num_turns: turnCount,
 1031:             stop_reason: lastStopReason,
 1032:             session_id: getSessionId(),
 1033:             total_cost_usd: getTotalCost(),
 1034:             usage: this.totalUsage,
 1035:             modelUsage: getModelUsage(),
 1036:             permission_denials: this.permissionDenials,
 1037:             fast_mode_state: getFastModeState(
 1038:               mainLoopModel,
 1039:               initialAppState.fastMode,
 1040:             ),
 1041:             uuid: randomUUID(),
 1042:             errors: [
 1043:               `Failed to provide valid structured output after ${maxRetries} attempts`,
 1044:             ],
 1045:           }
 1046:           return
 1047:         }
 1048:       }
 1049:     }
 1050: 
 1051:     // Stop hooks yield progress/attachment messages AFTER the assistant
 1052:     // response (via yield* handleStopHooks in query.ts). Since #23537 pushes
 1053:     // those to `messages` inline, last(messages) can be a progress/attachment
 1054:     // instead of the assistant â€” which makes textResult extraction below
 1055:     // return '' and -p mode emit a blank line. Allowlist to assistant|user:
 1056:     // isResultSuccessful handles both (user with all tool_result blocks is a
 1057:     // valid successful terminal state).
 1058:     const result = messages.findLast(
 1059:       m => m.type === 'assistant' || m.type === 'user',
 1060:     )
 1061:     // Capture for the error_during_execution diagnostic â€” isResultSuccessful
 1062:     // is a type predicate (message is Message), so inside the false branch
 1063:     // `result` narrows to never and these accesses don't typecheck.
 1064:     const edeResultType = result?.type ?? 'undefined'
 1065:     const edeLastContentType =
 1066:       result?.type === 'assistant'
 1067:         ? (last(result.message.content)?.type ?? 'none')
 1068:         : 'n/a'
 1069: 
 1070:     // Flush buffered transcript writes before yielding result.
 1071:     // The desktop app kills the CLI process immediately after receiving the
 1072:     // result message, so any unflushed writes would be lost.
 1073:     if (persistSession) {
 1074:       if (
 1075:         isEnvTruthy(process.env.CLAUDE_CODE_EAGER_FLUSH) ||
 1076:         isEnvTruthy(process.env.CLAUDE_CODE_IS_COWORK)
 1077:       ) {
 1078:         await flushSessionStorage()
 1079:       }
 1080:     }
 1081: 
 1082:     if (!isResultSuccessful(result, lastStopReason)) {
 1083:       yield {
 1084:         type: 'result',
 1085:         subtype: 'error_during_execution',
 1086:         duration_ms: Date.now() - startTime,
 1087:         duration_api_ms: getTotalAPIDuration(),
 1088:         is_error: true,
 1089:         num_turns: turnCount,
 1090:         stop_reason: lastStopReason,
 1091:         session_id: getSessionId(),
 1092:         total_cost_usd: getTotalCost(),
 1093:         usage: this.totalUsage,
 1094:         modelUsage: getModelUsage(),
 1095:         permission_denials: this.permissionDenials,
 1096:         fast_mode_state: getFastModeState(
 1097:           mainLoopModel,
 1098:           initialAppState.fastMode,
 1099:         ),
 1100:         uuid: randomUUID(),
 1101:         // Diagnostic prefix: these are what isResultSuccessful() checks â€” if
 1102:         // the result type isn't assistant-with-text/thinking or user-with-
 1103:         // tool_result, and stop_reason isn't end_turn, that's why this fired.
 1104:         // errors[] is turn-scoped via the watermark; previously it dumped the
 1105:         // entire process's logError buffer (ripgrep timeouts, ENOENT, etc).
 1106:         errors: (() => {
 1107:           const all = getInMemoryErrors()
 1108:           const start = errorLogWatermark
 1109:             ? all.lastIndexOf(errorLogWatermark) + 1
 1110:             : 0
 1111:           return [
 1112:             `[ede_diagnostic] result_type=${edeResultType} last_content_type=${edeLastContentType} stop_reason=${lastStopReason}`,
 1113:             ...all.slice(start).map(_ => _.error),
 1114:           ]
 1115:         })(),
 1116:       }
 1117:       return
 1118:     }
 1119: 
 1120:     // Extract the text result based on message type
 1121:     let textResult = ''
 1122:     let isApiError = false
 1123: 
 1124:     if (result.type === 'assistant') {
 1125:       const lastContent = last(result.message.content)
 1126:       if (
 1127:         lastContent?.type === 'text' &&
 1128:         !SYNTHETIC_MESSAGES.has(lastContent.text)
 1129:       ) {
 1130:         textResult = lastContent.text
 1131:       }
 1132:       isApiError = Boolean(result.isApiErrorMessage)
 1133:     }
 1134: 
 1135:     yield {
 1136:       type: 'result',
 1137:       subtype: 'success',
 1138:       is_error: isApiError,
 1139:       duration_ms: Date.now() - startTime,
 1140:       duration_api_ms: getTotalAPIDuration(),
 1141:       num_turns: turnCount,
 1142:       result: textResult,
 1143:       stop_reason: lastStopReason,
 1144:       session_id: getSessionId(),
 1145:       total_cost_usd: getTotalCost(),
 1146:       usage: this.totalUsage,
 1147:       modelUsage: getModelUsage(),
 1148:       permission_denials: this.permissionDenials,
 1149:       structured_output: structuredOutputFromTool,
 1150:       fast_mode_state: getFastModeState(
 1151:         mainLoopModel,
 1152:         initialAppState.fastMode,
 1153:       ),
 1154:       uuid: randomUUID(),
 1155:     }
 1156:   }
 1157: 
 1158:   interrupt(): void {
 1159:     this.abortController.abort()
 1160:   }
 1161: 
 1162:   getMessages(): readonly Message[] {
 1163:     return this.mutableMessages
 1164:   }
 1165: 
 1166:   getReadFileState(): FileStateCache {
 1167:     return this.readFileState
 1168:   }
 1169: 
 1170:   getSessionId(): string {
 1171:     return getSessionId()
 1172:   }
 1173: 
 1174:   setModel(model: string): void {
 1175:     this.config.userSpecifiedModel = model
 1176:   }
 1177: }
 1178: 
 1179: /**
 1180:  * Sends a single prompt to the Claude API and returns the response.
 1181:  * Assumes that claude is being used non-interactively -- will not
 1182:  * ask the user for permissions or further input.
 1183:  *
 1184:  * Convenience wrapper around QueryEngine for one-shot usage.
 1185:  */
 1186: export async function* ask({
 1187:   commands,
 1188:   prompt,
 1189:   promptUuid,
 1190:   isMeta,
 1191:   cwd,
 1192:   tools,
 1193:   mcpClients,
 1194:   verbose = false,
 1195:   thinkingConfig,
 1196:   maxTurns,
 1197:   maxBudgetUsd,
 1198:   taskBudget,
 1199:   canUseTool,
 1200:   mutableMessages = [],
 1201:   getReadFileCache,
 1202:   setReadFileCache,
 1203:   customSystemPrompt,
 1204:   appendSystemPrompt,
 1205:   userSpecifiedModel,
 1206:   fallbackModel,
 1207:   jsonSchema,
 1208:   getAppState,
 1209:   setAppState,
 1210:   abortController,
 1211:   replayUserMessages = false,
 1212:   includePartialMessages = false,
 1213:   handleElicitation,
 1214:   agents = [],
 1215:   setSDKStatus,
 1216:   orphanedPermission,
 1217: }: {
 1218:   commands: Command[]
 1219:   prompt: string | Array<ContentBlockParam>
 1220:   promptUuid?: string
 1221:   isMeta?: boolean
 1222:   cwd: string
 1223:   tools: Tools
 1224:   verbose?: boolean
 1225:   mcpClients: MCPServerConnection[]
 1226:   thinkingConfig?: ThinkingConfig
 1227:   maxTurns?: number
 1228:   maxBudgetUsd?: number
 1229:   taskBudget?: { total: number }
 1230:   canUseTool: CanUseToolFn
 1231:   mutableMessages?: Message[]
 1232:   customSystemPrompt?: string
 1233:   appendSystemPrompt?: string
 1234:   userSpecifiedModel?: string
 1235:   fallbackModel?: string
 1236:   jsonSchema?: Record<string, unknown>
 1237:   getAppState: () => AppState
 1238:   setAppState: (f: (prev: AppState) => AppState) => void
 1239:   getReadFileCache: () => FileStateCache
 1240:   setReadFileCache: (cache: FileStateCache) => void
 1241:   abortController?: AbortController
 1242:   replayUserMessages?: boolean
 1243:   includePartialMessages?: boolean
 1244:   handleElicitation?: ToolUseContext['handleElicitation']
 1245:   agents?: AgentDefinition[]
 1246:   setSDKStatus?: (status: SDKStatus) => void
 1247:   orphanedPermission?: OrphanedPermission
 1248: }): AsyncGenerator<SDKMessage, void, unknown> {
 1249:   const engine = new QueryEngine({
 1250:     cwd,
 1251:     tools,
 1252:     commands,
 1253:     mcpClients,
 1254:     agents,
 1255:     canUseTool,
 1256:     getAppState,
 1257:     setAppState,
 1258:     initialMessages: mutableMessages,
 1259:     readFileCache: cloneFileStateCache(getReadFileCache()),
 1260:     customSystemPrompt,
 1261:     appendSystemPrompt,
 1262:     userSpecifiedModel,
 1263:     fallbackModel,
 1264:     thinkingConfig,
 1265:     maxTurns,
 1266:     maxBudgetUsd,
 1267:     taskBudget,
 1268:     jsonSchema,
 1269:     verbose,
 1270:     handleElicitation,
 1271:     replayUserMessages,
 1272:     includePartialMessages,
 1273:     setSDKStatus,
 1274:     abortController,
 1275:     orphanedPermission,
 1276:     ...(feature('HISTORY_SNIP')
 1277:       ? {
 1278:           snipReplay: (yielded: Message, store: Message[]) => {
 1279:             if (!snipProjection!.isSnipBoundaryMessage(yielded))
 1280:               return undefined
 1281:             return snipModule!.snipCompactIfNeeded(store, { force: true })
 1282:           },
 1283:         }
 1284:       : {}),
 1285:   })
 1286: 
 1287:   try {
 1288:     yield* engine.submitMessage(prompt, {
 1289:       uuid: promptUuid,
 1290:       isMeta,
 1291:     })
 1292:   } finally {
 1293:     setReadFileCache(engine.getReadFileState())
 1294:   }
 1295: }

### D:\Github\sagemaker-coding-agent\_archive\compare_code\gg-claude-code-runnable\src\services\api\withRetry.ts
    1: import { feature } from 'bun:bundle'
    2: import type Anthropic from '@anthropic-ai/sdk'
    3: import {
    4:   APIConnectionError,
    5:   APIError,
    6:   APIUserAbortError,
    7: } from '@anthropic-ai/sdk'
    8: import type { QuerySource } from 'src/constants/querySource.js'
    9: import type { SystemAPIErrorMessage } from 'src/types/message.js'
   10: import { isAwsCredentialsProviderError } from 'src/utils/aws.js'
   11: import { logForDebugging } from 'src/utils/debug.js'
   12: import { logError } from 'src/utils/log.js'
   13: import { createSystemAPIErrorMessage } from 'src/utils/messages.js'
   14: import { getAPIProviderForStatsig } from 'src/utils/model/providers.js'
   15: import {
   16:   clearApiKeyHelperCache,
   17:   clearAwsCredentialsCache,
   18:   clearGcpCredentialsCache,
   19:   getClaudeAIOAuthTokens,
   20:   handleOAuth401Error,
   21:   isClaudeAISubscriber,
   22:   isEnterpriseSubscriber,
   23: } from '../../utils/auth.js'
   24: import { isEnvTruthy } from '../../utils/envUtils.js'
   25: import { errorMessage } from '../../utils/errors.js'
   26: import {
   27:   type CooldownReason,
   28:   handleFastModeOverageRejection,
   29:   handleFastModeRejectedByAPI,
   30:   isFastModeCooldown,
   31:   isFastModeEnabled,
   32:   triggerFastModeCooldown,
   33: } from '../../utils/fastMode.js'
   34: import { isNonCustomOpusModel } from '../../utils/model/model.js'
   35: import { disableKeepAlive } from '../../utils/proxy.js'
   36: import { sleep } from '../../utils/sleep.js'
   37: import type { ThinkingConfig } from '../../utils/thinking.js'
   38: import { getFeatureValue_CACHED_MAY_BE_STALE } from '../analytics/growthbook.js'
   39: import {
   40:   type AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
   41:   logEvent,
   42: } from '../analytics/index.js'
   43: import {
   44:   checkMockRateLimitError,
   45:   isMockRateLimitError,
   46: } from '../rateLimitMocking.js'
   47: import { REPEATED_529_ERROR_MESSAGE } from './errors.js'
   48: import { extractConnectionErrorDetails } from './errorUtils.js'
   49: 
   50: const abortError = () => new APIUserAbortError()
   51: 
   52: const DEFAULT_MAX_RETRIES = 10
   53: const FLOOR_OUTPUT_TOKENS = 3000
   54: const MAX_529_RETRIES = 3
   55: export const BASE_DELAY_MS = 500
   56: 
   57: // Foreground query sources where the user IS blocking on the result â€” these
   58: // retry on 529. Everything else (summaries, titles, suggestions, classifiers)
   59: // bails immediately: during a capacity cascade each retry is 3-10Ã— gateway
   60: // amplification, and the user never sees those fail anyway. New sources
   61: // default to no-retry â€” add here only if the user is waiting on the result.
   62: const FOREGROUND_529_RETRY_SOURCES = new Set<QuerySource>([
   63:   'repl_main_thread',
   64:   'repl_main_thread:outputStyle:custom',
   65:   'repl_main_thread:outputStyle:Explanatory',
   66:   'repl_main_thread:outputStyle:Learning',
   67:   'sdk',
   68:   'agent:custom',
   69:   'agent:default',
   70:   'agent:builtin',
   71:   'compact',
   72:   'hook_agent',
   73:   'hook_prompt',
   74:   'verification_agent',
   75:   'side_question',
   76:   // Security classifiers â€” must complete for auto-mode correctness.
   77:   // yoloClassifier.ts uses 'auto_mode' (not 'yolo_classifier' â€” that's
   78:   // type-only). bash_classifier is ant-only; feature-gate so the string
   79:   // tree-shakes out of external builds (excluded-strings.txt).
   80:   'auto_mode',
   81:   ...(feature('BASH_CLASSIFIER') ? (['bash_classifier'] as const) : []),
   82: ])
   83: 
   84: function shouldRetry529(querySource: QuerySource | undefined): boolean {
   85:   // undefined â†’ retry (conservative for untagged call paths)
   86:   return (
   87:     querySource === undefined || FOREGROUND_529_RETRY_SOURCES.has(querySource)
   88:   )
   89: }
   90: 
   91: // CLAUDE_CODE_UNATTENDED_RETRY: for unattended sessions (ant-only). Retries 429/529
   92: // indefinitely with higher backoff and periodic keep-alive yields so the host
   93: // environment does not mark the session idle mid-wait.
   94: // TODO(ANT-344): the keep-alive via SystemAPIErrorMessage yields is a stopgap
   95: // until there's a dedicated keep-alive channel.
   96: const PERSISTENT_MAX_BACKOFF_MS = 5 * 60 * 1000
   97: const PERSISTENT_RESET_CAP_MS = 6 * 60 * 60 * 1000
   98: const HEARTBEAT_INTERVAL_MS = 30_000
   99: 
  100: function isPersistentRetryEnabled(): boolean {
  101:   return feature('UNATTENDED_RETRY')
  102:     ? isEnvTruthy(process.env.CLAUDE_CODE_UNATTENDED_RETRY)
  103:     : false
  104: }
  105: 
  106: function isTransientCapacityError(error: unknown): boolean {
  107:   return (
  108:     is529Error(error) || (error instanceof APIError && error.status === 429)
  109:   )
  110: }
  111: 
  112: function isStaleConnectionError(error: unknown): boolean {
  113:   if (!(error instanceof APIConnectionError)) {
  114:     return false
  115:   }
  116:   const details = extractConnectionErrorDetails(error)
  117:   return details?.code === 'ECONNRESET' || details?.code === 'EPIPE'
  118: }
  119: 
  120: export interface RetryContext {
  121:   maxTokensOverride?: number
  122:   model: string
  123:   thinkingConfig: ThinkingConfig
  124:   fastMode?: boolean
  125: }
  126: 
  127: interface RetryOptions {
  128:   maxRetries?: number
  129:   model: string
  130:   fallbackModel?: string
  131:   thinkingConfig: ThinkingConfig
  132:   fastMode?: boolean
  133:   signal?: AbortSignal
  134:   querySource?: QuerySource
  135:   /**
  136:    * Pre-seed the consecutive 529 counter. Used when this retry loop is a
  137:    * non-streaming fallback after a streaming 529 â€” the streaming 529 should
  138:    * count toward MAX_529_RETRIES so total 529s-before-fallback is consistent
  139:    * regardless of which request mode hit the overload.
  140:    */
  141:   initialConsecutive529Errors?: number
  142: }
  143: 
  144: export class CannotRetryError extends Error {
  145:   constructor(
  146:     public readonly originalError: unknown,
  147:     public readonly retryContext: RetryContext,
  148:   ) {
  149:     const message = errorMessage(originalError)
  150:     super(message)
  151:     this.name = 'RetryError'
  152: 
  153:     // Preserve the original stack trace if available
  154:     if (originalError instanceof Error && originalError.stack) {
  155:       this.stack = originalError.stack
  156:     }
  157:   }
  158: }
  159: 
  160: export class FallbackTriggeredError extends Error {
  161:   constructor(
  162:     public readonly originalModel: string,
  163:     public readonly fallbackModel: string,
  164:   ) {
  165:     super(`Model fallback triggered: ${originalModel} -> ${fallbackModel}`)
  166:     this.name = 'FallbackTriggeredError'
  167:   }
  168: }
  169: 
  170: export async function* withRetry<T>(
  171:   getClient: () => Promise<Anthropic>,
  172:   operation: (
  173:     client: Anthropic,
  174:     attempt: number,
  175:     context: RetryContext,
  176:   ) => Promise<T>,
  177:   options: RetryOptions,
  178: ): AsyncGenerator<SystemAPIErrorMessage, T> {
  179:   const maxRetries = getMaxRetries(options)
  180:   const retryContext: RetryContext = {
  181:     model: options.model,
  182:     thinkingConfig: options.thinkingConfig,
  183:     ...(isFastModeEnabled() && { fastMode: options.fastMode }),
  184:   }
  185:   let client: Anthropic | null = null
  186:   let consecutive529Errors = options.initialConsecutive529Errors ?? 0
  187:   let lastError: unknown
  188:   let persistentAttempt = 0
  189:   for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
  190:     if (options.signal?.aborted) {
  191:       throw new APIUserAbortError()
  192:     }
  193: 
  194:     // Capture whether fast mode is active before this attempt
  195:     // (fallback may change the state mid-loop)
  196:     const wasFastModeActive = isFastModeEnabled()
  197:       ? retryContext.fastMode && !isFastModeCooldown()
  198:       : false
  199: 
  200:     try {
  201:       // Check for mock rate limits (used by /mock-limits command for Ant employees)
  202:       if (process.env.USER_TYPE === 'ant') {
  203:         const mockError = checkMockRateLimitError(
  204:           retryContext.model,
  205:           wasFastModeActive,
  206:         )
  207:         if (mockError) {
  208:           throw mockError
  209:         }
  210:       }
  211: 
  212:       // Get a fresh client instance on first attempt or after authentication errors
  213:       // - 401 for first-party API authentication failures
  214:       // - 403 "OAuth token has been revoked" (another process refreshed the token)
  215:       // - Bedrock-specific auth errors (403 or CredentialsProviderError)
  216:       // - Vertex-specific auth errors (credential refresh failures, 401)
  217:       // - ECONNRESET/EPIPE: stale keep-alive socket; disable pooling and reconnect
  218:       const isStaleConnection = isStaleConnectionError(lastError)
  219:       if (
  220:         isStaleConnection &&
  221:         getFeatureValue_CACHED_MAY_BE_STALE(
  222:           'tengu_disable_keepalive_on_econnreset',
  223:           false,
  224:         )
  225:       ) {
  226:         logForDebugging(
  227:           'Stale connection (ECONNRESET/EPIPE) â€” disabling keep-alive for retry',
  228:         )
  229:         disableKeepAlive()
  230:       }
  231: 
  232:       if (
  233:         client === null ||
  234:         (lastError instanceof APIError && lastError.status === 401) ||
  235:         isOAuthTokenRevokedError(lastError) ||
  236:         isBedrockAuthError(lastError) ||
  237:         isVertexAuthError(lastError) ||
  238:         isStaleConnection
  239:       ) {
  240:         // On 401 "token expired" or 403 "token revoked", force a token refresh
  241:         if (
  242:           (lastError instanceof APIError && lastError.status === 401) ||
  243:           isOAuthTokenRevokedError(lastError)
  244:         ) {
  245:           const failedAccessToken = getClaudeAIOAuthTokens()?.accessToken
  246:           if (failedAccessToken) {
  247:             await handleOAuth401Error(failedAccessToken)
  248:           }
  249:         }
  250:         client = await getClient()
  251:       }
  252: 
  253:       return await operation(client, attempt, retryContext)
  254:     } catch (error) {
  255:       lastError = error
  256:       logForDebugging(
  257:         `API error (attempt ${attempt}/${maxRetries + 1}): ${error instanceof APIError ? `${error.status} ${error.message}` : errorMessage(error)}`,
  258:         { level: 'error' },
  259:       )
  260: 
  261:       // Fast mode fallback: on 429/529, either wait and retry (short delays)
  262:       // or fall back to standard speed (long delays) to avoid cache thrashing.
  263:       // Skip in persistent mode: the short-retry path below loops with fast
  264:       // mode still active, so its `continue` never reaches the attempt clamp
  265:       // and the for-loop terminates. Persistent sessions want the chunked
  266:       // keep-alive path instead of fast-mode cache-preservation anyway.
  267:       if (
  268:         wasFastModeActive &&
  269:         !isPersistentRetryEnabled() &&
  270:         error instanceof APIError &&
  271:         (error.status === 429 || is529Error(error))
  272:       ) {
  273:         // If the 429 is specifically because extra usage (overage) is not
  274:         // available, permanently disable fast mode with a specific message.
  275:         const overageReason = error.headers?.get(
  276:           'anthropic-ratelimit-unified-overage-disabled-reason',
  277:         )
  278:         if (overageReason !== null && overageReason !== undefined) {
  279:           handleFastModeOverageRejection(overageReason)
  280:           retryContext.fastMode = false
  281:           continue
  282:         }
  283: 
  284:         const retryAfterMs = getRetryAfterMs(error)
  285:         if (retryAfterMs !== null && retryAfterMs < SHORT_RETRY_THRESHOLD_MS) {
  286:           // Short retry-after: wait and retry with fast mode still active
  287:           // to preserve prompt cache (same model name on retry).
  288:           await sleep(retryAfterMs, options.signal, { abortError })
  289:           continue
  290:         }
  291:         // Long or unknown retry-after: enter cooldown (switches to standard
  292:         // speed model), with a minimum floor to avoid flip-flopping.
  293:         const cooldownMs = Math.max(
  294:           retryAfterMs ?? DEFAULT_FAST_MODE_FALLBACK_HOLD_MS,
  295:           MIN_COOLDOWN_MS,
  296:         )
  297:         const cooldownReason: CooldownReason = is529Error(error)
  298:           ? 'overloaded'
  299:           : 'rate_limit'
  300:         triggerFastModeCooldown(Date.now() + cooldownMs, cooldownReason)
  301:         if (isFastModeEnabled()) {
  302:           retryContext.fastMode = false
  303:         }
  304:         continue
  305:       }
  306: 
  307:       // Fast mode fallback: if the API rejects the fast mode parameter
  308:       // (e.g., org doesn't have fast mode enabled), permanently disable fast
  309:       // mode and retry at standard speed.
  310:       if (wasFastModeActive && isFastModeNotEnabledError(error)) {
  311:         handleFastModeRejectedByAPI()
  312:         retryContext.fastMode = false
  313:         continue
  314:       }
  315: 
  316:       // Non-foreground sources bail immediately on 529 â€” no retry amplification
  317:       // during capacity cascades. User never sees these fail.
  318:       if (is529Error(error) && !shouldRetry529(options.querySource)) {
  319:         logEvent('tengu_api_529_background_dropped', {
  320:           query_source:
  321:             options.querySource as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
  322:         })
  323:         throw new CannotRetryError(error, retryContext)
  324:       }
  325: 
  326:       // Track consecutive 529 errors
  327:       if (
  328:         is529Error(error) &&
  329:         // If FALLBACK_FOR_ALL_PRIMARY_MODELS is not set, fall through only if the primary model is a non-custom Opus model.
  330:         // TODO: Revisit if the isNonCustomOpusModel check should still exist, or if isNonCustomOpusModel is a stale artifact of when Claude Code was hardcoded on Opus.
  331:         (process.env.FALLBACK_FOR_ALL_PRIMARY_MODELS ||
  332:           (!isClaudeAISubscriber() && isNonCustomOpusModel(options.model)))
  333:       ) {
  334:         consecutive529Errors++
  335:         if (consecutive529Errors >= MAX_529_RETRIES) {
  336:           // Check if fallback model is specified
  337:           if (options.fallbackModel) {
  338:             logEvent('tengu_api_opus_fallback_triggered', {
  339:               original_model:
  340:                 options.model as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
  341:               fallback_model:
  342:                 options.fallbackModel as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
  343:               provider: getAPIProviderForStatsig(),
  344:             })
  345: 
  346:             // Throw special error to indicate fallback was triggered
  347:             throw new FallbackTriggeredError(
  348:               options.model,
  349:               options.fallbackModel,
  350:             )
  351:           }
  352: 
  353:           if (
  354:             process.env.USER_TYPE === 'external' &&
  355:             !process.env.IS_SANDBOX &&
  356:             !isPersistentRetryEnabled()
  357:           ) {
  358:             logEvent('tengu_api_custom_529_overloaded_error', {})
  359:             throw new CannotRetryError(
  360:               new Error(REPEATED_529_ERROR_MESSAGE),
  361:               retryContext,
  362:             )
  363:           }
  364:         }
  365:       }
  366: 
  367:       // Only retry if the error indicates we should
  368:       const persistent =
  369:         isPersistentRetryEnabled() && isTransientCapacityError(error)
  370:       if (attempt > maxRetries && !persistent) {
  371:         throw new CannotRetryError(error, retryContext)
  372:       }
  373: 
  374:       // AWS/GCP errors aren't always APIError, but can be retried
  375:       const handledCloudAuthError =
  376:         handleAwsCredentialError(error) || handleGcpCredentialError(error)
  377:       if (
  378:         !handledCloudAuthError &&
  379:         (!(error instanceof APIError) || !shouldRetry(error))
  380:       ) {
  381:         throw new CannotRetryError(error, retryContext)
  382:       }
  383: 
  384:       // Handle max tokens context overflow errors by adjusting max_tokens for the next attempt
  385:       // NOTE: With extended-context-window beta, this 400 error should not occur.
  386:       // The API now returns 'model_context_window_exceeded' stop_reason instead.
  387:       // Keeping for backward compatibility.
  388:       if (error instanceof APIError) {
  389:         const overflowData = parseMaxTokensContextOverflowError(error)
  390:         if (overflowData) {
  391:           const { inputTokens, contextLimit } = overflowData
  392: 
  393:           const safetyBuffer = 1000
  394:           const availableContext = Math.max(
  395:             0,
  396:             contextLimit - inputTokens - safetyBuffer,
  397:           )
  398:           if (availableContext < FLOOR_OUTPUT_TOKENS) {
  399:             logError(
  400:               new Error(
  401:                 `availableContext ${availableContext} is less than FLOOR_OUTPUT_TOKENS ${FLOOR_OUTPUT_TOKENS}`,
  402:               ),
  403:             )
  404:             throw error
  405:           }
  406:           // Ensure we have enough tokens for thinking + at least 1 output token
  407:           const minRequired =
  408:             (retryContext.thinkingConfig.type === 'enabled'
  409:               ? retryContext.thinkingConfig.budgetTokens
  410:               : 0) + 1
  411:           const adjustedMaxTokens = Math.max(
  412:             FLOOR_OUTPUT_TOKENS,
  413:             availableContext,
  414:             minRequired,
  415:           )
  416:           retryContext.maxTokensOverride = adjustedMaxTokens
  417: 
  418:           logEvent('tengu_max_tokens_context_overflow_adjustment', {
  419:             inputTokens,
  420:             contextLimit,
  421:             adjustedMaxTokens,
  422:             attempt,
  423:           })
  424: 
  425:           continue
  426:         }
  427:       }
  428: 
  429:       // For other errors, proceed with normal retry logic
  430:       // Get retry-after header if available
  431:       const retryAfter = getRetryAfter(error)
  432:       let delayMs: number
  433:       if (persistent && error instanceof APIError && error.status === 429) {
  434:         persistentAttempt++
  435:         // Window-based limits (e.g. 5hr Max/Pro) include a reset timestamp.
  436:         // Wait until reset rather than polling every 5 min uselessly.
  437:         const resetDelay = getRateLimitResetDelayMs(error)
  438:         delayMs =
  439:           resetDelay ??
  440:           Math.min(
  441:             getRetryDelay(
  442:               persistentAttempt,
  443:               retryAfter,
  444:               PERSISTENT_MAX_BACKOFF_MS,
  445:             ),
  446:             PERSISTENT_RESET_CAP_MS,
  447:           )
  448:       } else if (persistent) {
  449:         persistentAttempt++
  450:         // Retry-After is a server directive and bypasses maxDelayMs inside
  451:         // getRetryDelay (intentional â€” honoring it is correct). Cap at the
  452:         // 6hr reset-cap here so a pathological header can't wait unbounded.
  453:         delayMs = Math.min(
  454:           getRetryDelay(
  455:             persistentAttempt,
  456:             retryAfter,
  457:             PERSISTENT_MAX_BACKOFF_MS,
  458:           ),
  459:           PERSISTENT_RESET_CAP_MS,
  460:         )
  461:       } else {
  462:         delayMs = getRetryDelay(attempt, retryAfter)
  463:       }
  464: 
  465:       // In persistent mode the for-loop `attempt` is clamped at maxRetries+1;
  466:       // use persistentAttempt for telemetry/yields so they show the true count.
  467:       const reportedAttempt = persistent ? persistentAttempt : attempt
  468:       logEvent('tengu_api_retry', {
  469:         attempt: reportedAttempt,
  470:         delayMs: delayMs,
  471:         error: (error as APIError)
  472:           .message as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
  473:         status: (error as APIError).status,
  474:         provider: getAPIProviderForStatsig(),
  475:       })
  476: 
  477:       if (persistent) {
  478:         if (delayMs > 60_000) {
  479:           logEvent('tengu_api_persistent_retry_wait', {
  480:             status: (error as APIError).status,
  481:             delayMs,
  482:             attempt: reportedAttempt,
  483:             provider: getAPIProviderForStatsig(),
  484:           })
  485:         }
  486:         // Chunk long sleeps so the host sees periodic stdout activity and
  487:         // does not mark the session idle. Each yield surfaces as
  488:         // {type:'system', subtype:'api_retry'} on stdout via QueryEngine.
  489:         let remaining = delayMs
  490:         while (remaining > 0) {
  491:           if (options.signal?.aborted) throw new APIUserAbortError()
  492:           if (error instanceof APIError) {
  493:             yield createSystemAPIErrorMessage(
  494:               error,
  495:               remaining,
  496:               reportedAttempt,
  497:               maxRetries,
  498:             )
  499:           }
  500:           const chunk = Math.min(remaining, HEARTBEAT_INTERVAL_MS)
  501:           await sleep(chunk, options.signal, { abortError })
  502:           remaining -= chunk
  503:         }
  504:         // Clamp so the for-loop never terminates. Backoff uses the separate
  505:         // persistentAttempt counter which keeps growing to the 5-min cap.
  506:         if (attempt >= maxRetries) attempt = maxRetries
  507:       } else {
  508:         if (error instanceof APIError) {
  509:           yield createSystemAPIErrorMessage(error, delayMs, attempt, maxRetries)
  510:         }
  511:         await sleep(delayMs, options.signal, { abortError })
  512:       }
  513:     }
  514:   }
  515: 
  516:   throw new CannotRetryError(lastError, retryContext)
  517: }
  518: 
  519: function getRetryAfter(error: unknown): string | null {
  520:   return (
  521:     ((error as { headers?: { 'retry-after'?: string } }).headers?.[
  522:       'retry-after'
  523:     ] ||
  524:       // eslint-disable-next-line eslint-plugin-n/no-unsupported-features/node-builtins
  525:       ((error as APIError).headers as Headers)?.get?.('retry-after')) ??
  526:     null
  527:   )
  528: }
  529: 
  530: export function getRetryDelay(
  531:   attempt: number,
  532:   retryAfterHeader?: string | null,
  533:   maxDelayMs = 32000,
  534: ): number {
  535:   if (retryAfterHeader) {
  536:     const seconds = parseInt(retryAfterHeader, 10)
  537:     if (!isNaN(seconds)) {
  538:       return seconds * 1000
  539:     }
  540:   }
  541: 
  542:   const baseDelay = Math.min(
  543:     BASE_DELAY_MS * Math.pow(2, attempt - 1),
  544:     maxDelayMs,
  545:   )
  546:   const jitter = Math.random() * 0.25 * baseDelay
  547:   return baseDelay + jitter
  548: }
  549: 
  550: export function parseMaxTokensContextOverflowError(error: APIError):
  551:   | {
  552:       inputTokens: number
  553:       maxTokens: number
  554:       contextLimit: number
  555:     }
  556:   | undefined {
  557:   if (error.status !== 400 || !error.message) {
  558:     return undefined
  559:   }
  560: 
  561:   if (
  562:     !error.message.includes(
  563:       'input length and `max_tokens` exceed context limit',
  564:     )
  565:   ) {
  566:     return undefined
  567:   }
  568: 
  569:   // Example format: "input length and `max_tokens` exceed context limit: 188059 + 20000 > 200000"
  570:   const regex =
  571:     /input length and `max_tokens` exceed context limit: (\d+) \+ (\d+) > (\d+)/
  572:   const match = error.message.match(regex)
  573: 
  574:   if (!match || match.length !== 4) {
  575:     return undefined
  576:   }
  577: 
  578:   if (!match[1] || !match[2] || !match[3]) {
  579:     logError(
  580:       new Error(
  581:         'Unable to parse max_tokens from max_tokens exceed context limit error message',
  582:       ),
  583:     )
  584:     return undefined
  585:   }
  586:   const inputTokens = parseInt(match[1], 10)
  587:   const maxTokens = parseInt(match[2], 10)
  588:   const contextLimit = parseInt(match[3], 10)
  589: 
  590:   if (isNaN(inputTokens) || isNaN(maxTokens) || isNaN(contextLimit)) {
  591:     return undefined
  592:   }
  593: 
  594:   return { inputTokens, maxTokens, contextLimit }
  595: }
  596: 
  597: // TODO: Replace with a response header check once the API adds a dedicated
  598: // header for fast-mode rejection (e.g., x-fast-mode-rejected). String-matching
  599: // the error message is fragile and will break if the API wording changes.
  600: function isFastModeNotEnabledError(error: unknown): boolean {
  601:   if (!(error instanceof APIError)) {
  602:     return false
  603:   }
  604:   return (
  605:     error.status === 400 &&
  606:     (error.message?.includes('Fast mode is not enabled') ?? false)
  607:   )
  608: }
  609: 
  610: export function is529Error(error: unknown): boolean {
  611:   if (!(error instanceof APIError)) {
  612:     return false
  613:   }
  614: 
  615:   // Check for 529 status code or overloaded error in message
  616:   return (
  617:     error.status === 529 ||
  618:     // See below: the SDK sometimes fails to properly pass the 529 status code during streaming
  619:     (error.message?.includes('"type":"overloaded_error"') ?? false)
  620:   )
  621: }
  622: 
  623: function isOAuthTokenRevokedError(error: unknown): boolean {
  624:   return (
  625:     error instanceof APIError &&
  626:     error.status === 403 &&
  627:     (error.message?.includes('OAuth token has been revoked') ?? false)
  628:   )
  629: }
  630: 
  631: function isBedrockAuthError(error: unknown): boolean {
  632:   if (isEnvTruthy(process.env.CLAUDE_CODE_USE_BEDROCK)) {
  633:     // AWS libs reject without an API call if .aws holds a past Expiration value
  634:     // otherwise, API calls that receive expired tokens give generic 403
  635:     // "The security token included in the request is invalid"
  636:     if (
  637:       isAwsCredentialsProviderError(error) ||
  638:       (error instanceof APIError && error.status === 403)
  639:     ) {
  640:       return true
  641:     }
  642:   }
  643:   return false
  644: }
  645: 
  646: /**
  647:  * Clear AWS auth caches if appropriate.
  648:  * @returns true if action was taken.
  649:  */
  650: function handleAwsCredentialError(error: unknown): boolean {
  651:   if (isBedrockAuthError(error)) {
  652:     clearAwsCredentialsCache()
  653:     return true
  654:   }
  655:   return false
  656: }
  657: 
  658: // google-auth-library throws plain Error (no typed name like AWS's
  659: // CredentialsProviderError). Match common SDK-level credential-failure messages.
  660: function isGoogleAuthLibraryCredentialError(error: unknown): boolean {
  661:   if (!(error instanceof Error)) return false
  662:   const msg = error.message
  663:   return (
  664:     msg.includes('Could not load the default credentials') ||
  665:     msg.includes('Could not refresh access token') ||
  666:     msg.includes('invalid_grant')
  667:   )
  668: }
  669: 
  670: function isVertexAuthError(error: unknown): boolean {
  671:   if (isEnvTruthy(process.env.CLAUDE_CODE_USE_VERTEX)) {
  672:     // SDK-level: google-auth-library fails in prepareOptions() before the HTTP call
  673:     if (isGoogleAuthLibraryCredentialError(error)) {
  674:       return true
  675:     }
  676:     // Server-side: Vertex returns 401 for expired/invalid tokens
  677:     if (error instanceof APIError && error.status === 401) {
  678:       return true
  679:     }
  680:   }
  681:   return false
  682: }
  683: 
  684: /**
  685:  * Clear GCP auth caches if appropriate.
  686:  * @returns true if action was taken.
  687:  */
  688: function handleGcpCredentialError(error: unknown): boolean {
  689:   if (isVertexAuthError(error)) {
  690:     clearGcpCredentialsCache()
  691:     return true
  692:   }
  693:   return false
  694: }
  695: 
  696: function shouldRetry(error: APIError): boolean {
  697:   // Never retry mock errors - they're from /mock-limits command for testing
  698:   if (isMockRateLimitError(error)) {
  699:     return false
  700:   }
  701: 
  702:   // Persistent mode: 429/529 always retryable, bypass subscriber gates and
  703:   // x-should-retry header.
  704:   if (isPersistentRetryEnabled() && isTransientCapacityError(error)) {
  705:     return true
  706:   }
  707: 
  708:   // CCR mode: auth is via infrastructure-provided JWTs, so a 401/403 is a
  709:   // transient blip (auth service flap, network hiccup) rather than bad
  710:   // credentials. Bypass x-should-retry:false â€” the server assumes we'd retry
  711:   // the same bad key, but our key is fine.
  712:   if (
  713:     isEnvTruthy(process.env.CLAUDE_CODE_REMOTE) &&
  714:     (error.status === 401 || error.status === 403)
  715:   ) {
  716:     return true
  717:   }
  718: 
  719:   // Check for overloaded errors first by examining the message content
  720:   // The SDK sometimes fails to properly pass the 529 status code during streaming,
  721:   // so we need to check the error message directly
  722:   if (error.message?.includes('"type":"overloaded_error"')) {
  723:     return true
  724:   }
  725: 
  726:   // Check for max tokens context overflow errors that we can handle
  727:   if (parseMaxTokensContextOverflowError(error)) {
  728:     return true
  729:   }
  730: 
  731:   // Note this is not a standard header.
  732:   const shouldRetryHeader = error.headers?.get('x-should-retry')
  733: 
  734:   // If the server explicitly says whether or not to retry, obey.
  735:   // For Max and Pro users, should-retry is true, but in several hours, so we shouldn't.
  736:   // Enterprise users can retry because they typically use PAYG instead of rate limits.
  737:   if (
  738:     shouldRetryHeader === 'true' &&
  739:     (!isClaudeAISubscriber() || isEnterpriseSubscriber())
  740:   ) {
  741:     return true
  742:   }
  743: 
  744:   // Ants can ignore x-should-retry: false for 5xx server errors only.
  745:   // For other status codes (401, 403, 400, 429, etc.), respect the header.
  746:   if (shouldRetryHeader === 'false') {
  747:     const is5xxError = error.status !== undefined && error.status >= 500
  748:     if (!(process.env.USER_TYPE === 'ant' && is5xxError)) {
  749:       return false
  750:     }
  751:   }
  752: 
  753:   if (error instanceof APIConnectionError) {
  754:     return true
  755:   }
  756: 
  757:   if (!error.status) return false
  758: 
  759:   // Retry on request timeouts.
  760:   if (error.status === 408) return true
  761: 
  762:   // Retry on lock timeouts.
  763:   if (error.status === 409) return true
  764: 
  765:   // Retry on rate limits, but not for ClaudeAI Subscription users
  766:   // Enterprise users can retry because they typically use PAYG instead of rate limits
  767:   if (error.status === 429) {
  768:     return !isClaudeAISubscriber() || isEnterpriseSubscriber()
  769:   }
  770: 
  771:   // Clear API key cache on 401 and allow retry.
  772:   // OAuth token handling is done in the main retry loop via handleOAuth401Error.
  773:   if (error.status === 401) {
  774:     clearApiKeyHelperCache()
  775:     return true
  776:   }
  777: 
  778:   // Retry on 403 "token revoked" (same refresh logic as 401, see above)
  779:   if (isOAuthTokenRevokedError(error)) {
  780:     return true
  781:   }
  782: 
  783:   // Retry internal errors.
  784:   if (error.status && error.status >= 500) return true
  785: 
  786:   return false
  787: }
  788: 
  789: export function getDefaultMaxRetries(): number {
  790:   if (process.env.CLAUDE_CODE_MAX_RETRIES) {
  791:     return parseInt(process.env.CLAUDE_CODE_MAX_RETRIES, 10)
  792:   }
  793:   return DEFAULT_MAX_RETRIES
  794: }
  795: function getMaxRetries(options: RetryOptions): number {
  796:   return options.maxRetries ?? getDefaultMaxRetries()
  797: }
  798: 
  799: const DEFAULT_FAST_MODE_FALLBACK_HOLD_MS = 30 * 60 * 1000 // 30 minutes
  800: const SHORT_RETRY_THRESHOLD_MS = 20 * 1000 // 20 seconds
  801: const MIN_COOLDOWN_MS = 10 * 60 * 1000 // 10 minutes
  802: 
  803: function getRetryAfterMs(error: APIError): number | null {
  804:   const retryAfter = getRetryAfter(error)
  805:   if (retryAfter) {
  806:     const seconds = parseInt(retryAfter, 10)
  807:     if (!isNaN(seconds)) {
  808:       return seconds * 1000
  809:     }
  810:   }
  811:   return null
  812: }
  813: 
  814: function getRateLimitResetDelayMs(error: APIError): number | null {
  815:   const resetHeader = error.headers?.get?.('anthropic-ratelimit-unified-reset')
  816:   if (!resetHeader) return null
  817:   const resetUnixSec = Number(resetHeader)
  818:   if (!Number.isFinite(resetUnixSec)) return null
  819:   const delayMs = resetUnixSec * 1000 - Date.now()
  820:   if (delayMs <= 0) return null
  821:   return Math.min(delayMs, PERSISTENT_RESET_CAP_MS)
  822: }

codex
I’ve confirmed the relevant source files; now I’m drilling into `query_engine.py` and the integration tests in chunks to verify loop invariants and whether tests can miss wiring failures.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\query_engine.py'; "'$lines=Get-Content $f; for($s=1;$s -le $lines.Length;$s+=120){$e=[Math]::Min($s+119,$lines.Length); Write-Output "`n### query_engine.py:$s-$e"; for($i=$s;$i -le $e;$i++){"{0,5}: {1}" -f $i,$lines[$i-1]}}' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests\\integration\\test_query_engine.py'; "'$lines=Get-Content $f; for($s=1;$s -le $lines.Length;$s+=120){$e=[Math]::Min($s+119,$lines.Length); Write-Output "`n### test_query_engine.py:$s-$e"; for($i=$s;$i -le $e;$i++){"{0,5}: {1}" -f $i,$lines[$i-1]}}' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\runtime\\bedrock_client.py'; "'$lines=Get-Content $f; for($s=1;$s -le $lines.Length;$s+=140){$e=[Math]::Min($s+139,$lines.Length); Write-Output "`n### bedrock_client.py:$s-$e"; for($i=$s;$i -le $e;$i++){"{0,5}: {1}" -f $i,$lines[$i-1]}}' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\compact_v4\\MAIN\\agent\\sagemaker_agent.py'; "'$lines=Get-Content $f; $ranges=@(@(8160,8245),@(8680,8790),@(8880,9035),@(9040,9220)); foreach($r in $ranges){$s=$r[0];$e=$r[1]; Write-Output "`n### v4 sagemaker_agent.py:$s-$e"; for($i=$s;$i -le $e;$i++){"{0,5}: {1}" -f $i,$lines[$i-1]}}' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-ChildItem -Path D:\\Github\\sagemaker-coding-agent -Recurse -File | Where-Object { "'$_.FullName -match '"'hermes-agent\\\\run_agent\\.py"'$'"' } | Select-Object -ExpandProperty FullName" in D:\Github\sagemaker-coding-agent
 succeeded in 3768ms:

### query_engine.py:1-120
    1: """V5 core/query_engine.py â€” main agent loop (Phase 8 deliverable, ADR-014).
    2: 
    3: Per ADR-014: minimal, focused port of Runnable's `QueryEngine.ts` (1295 LOC)
    4: adapted to the v5 .ipynb shape. v4's monolithic `Agent.run` (~1500 LOC) is
    5: replaced by this ~400 LOC module with explicit IN-SCOPE / OUT-OF-SCOPE.
    6: 
    7: PORT_LOG: #019.
    8: 
    9: IN SCOPE (Phase 8):
   10: - Per-turn loop with end_turn / max_turns / budget exhausted exits.
   11: - IterationBudget gate at the top of each turn (shared with sub-agents).
   12: - Phase 7 deferred-loading wiring contract:
   13:     * `apply_tool_search_deferral(tools, enabled=True)` per turn.
   14:     * `tool_search_discovered_names()` extraction from tool_search results.
   15:     * Discovered names are added to the next turn's tools= API param.
   16: - Tool dispatch via `find_tool_by_name(...).execute(args, context)`.
   17: - tool_use â†’ tool_result message accumulation in the model-visible
   18:   conversation buffer.
   19: - Bedrock invocation through `BedrockClient.chat(...)`.
   20: - System prompt assembly via `prompt.build_system_prompt(ctx)`.
   21: - run_one_turn(...) helper for unit tests (single-turn, no loop).
   22: 
   23: OUT OF SCOPE â€” explicitly deferred to later phases (per ADR-014):
   24: - Microcompact / context_collapse â€” Phase 11 UX (PS Issue #4 widget surface).
   25: - 2-stage smart compaction (prune + LLM summary) â€” Phase 11.
   26: - Skill auto-trigger â€” Phase 10 (`SKILLS.discover_relevant`).
   27: - Plan mode injection of skills into prompt â€” Phase 10.
   28: - Sub-agent forkSubagent â€” Phase 9 (`subagent/spawn.py`).
   29: - File-read state tracking â€” Phase 4 already lands this; engine respects but
   30:   doesn't reset on compact (no compact in Phase 8).
   31: - Diminishing-returns / repetition guard â€” deferred.
   32: - Notebook UX (output_fn callback contract) â€” Phase 11 owns the UI shape;
   33:   Phase 8 takes a `output_fn: Callable[[str], None] = print` so tests can
   34:   capture, but real notebook integration lives in Phase 11.
   35: 
   36: The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
   37: concurrent `run()` calls on the same engine are NOT supported (matches v4).
   38: """
   39: from __future__ import annotations
   40: 
   41: import json
   42: import logging
   43: from dataclasses import dataclass, field
   44: from typing import Any, Callable, Dict, List, Optional, Set, Tuple
   45: 
   46: from .budget import IterationBudget
   47: from .errors import BedrockErrorCategory, ErrorClassifier
   48: 
   49: 
   50: # ============================================================
   51: # Result envelope
   52: # ============================================================
   53: 
   54: @dataclass
   55: class QueryResult:
   56:     """Outcome of a `QueryEngine.run(...)` call.
   57: 
   58:     `text`           â€” final assistant text (last end_turn turn's text block).
   59:     `messages`       â€” full message buffer including the user turn that
   60:                        triggered this call. Caller may discard or persist.
   61:     `stop_reason`    â€” "end_turn" | "max_turns" | "budget_exhausted" |
   62:                        "context_overflow" | "fatal_error".
   63:     `turns_used`     â€” count of model turns executed during this run.
   64:     `budget_used`    â€” IterationBudget.used() snapshot at exit.
   65:     `error`          â€” short message when stop_reason indicates failure.
   66:     """
   67:     text: str = ""
   68:     messages: List[Dict[str, Any]] = field(default_factory=list)
   69:     stop_reason: str = ""
   70:     turns_used: int = 0
   71:     budget_used: int = 0
   72:     error: Optional[str] = None
   73: 
   74: 
   75: # ============================================================
   76: # Helpers
   77: # ============================================================
   78: 
   79: def _build_tools_api_payload(tools: List[Any]) -> List[Dict[str, Any]]:
   80:     """Convert ToolRecord list into Bedrock `tools=` API payload shape.
   81: 
   82:     Bedrock expects: [{"name": ..., "description": ..., "input_schema": ...}, ...]
   83:     """
   84:     out: List[Dict[str, Any]] = []
   85:     for t in tools:
   86:         out.append({
   87:             "name": t.name,
   88:             "description": t.description,
   89:             "input_schema": t.input_schema,
   90:         })
   91:     return out
   92: 
   93: 
   94: def _coerce_tool_result_to_text(value: Any) -> str:
   95:     """Map any tool-execute return value into a Bedrock tool_result text string.
   96: 
   97:     Tool implementations return diverse shapes (str / dict / list). Bedrock's
   98:     tool_result content needs a string. Prefer str() for primitives, JSON for
   99:     structured shapes â€” same convention as v4 dispatch."""
  100:     if isinstance(value, str):
  101:         return value
  102:     if isinstance(value, (dict, list, tuple)):
  103:         try:
  104:             return json.dumps(value, ensure_ascii=False, default=str)
  105:         except Exception:
  106:             return str(value)
  107:     return str(value)
  108: 
  109: 
  110: def _truncate_tool_result(text: str, max_chars: int) -> str:
  111:     if max_chars <= 0 or len(text) <= max_chars:
  112:         return text
  113:     head = text[: max_chars - 200]
  114:     return (
  115:         head
  116:         + f"\n\n[... truncated: tool_result exceeded {max_chars} chars; "
  117:         f"original size {len(text)} chars ...]"
  118:     )
  119: 
  120: 

### query_engine.py:121-240
  121: # ============================================================
  122: # QueryEngine
  123: # ============================================================
  124: 
  125: class QueryEngine:
  126:     """Main agent loop. Owns the message buffer + iteration budget for one
  127:     `run()` call. Sub-agents (Phase 9) will share the same IterationBudget
  128:     instance via `forkSubagent`-style construction.
  129:     """
  130: 
  131:     DEFAULT_MAX_TURNS = 50  # v4 in-place default; UI may override per call.
  132: 
  133:     def __init__(
  134:         self,
  135:         client: Any,
  136:         max_turns: int = DEFAULT_MAX_TURNS,
  137:         budget: Optional[IterationBudget] = None,
  138:         on_stop_check: Optional[Callable[[], bool]] = None,
  139:     ):
  140:         """Construct a QueryEngine.
  141: 
  142:         Args:
  143:             client: BedrockClient (or mock with the same `chat(...)` shape).
  144:             max_turns: hard upper bound on turns per `run()` call.
  145:             budget: shared IterationBudget. If None, a fresh one is created.
  146:             on_stop_check: optional callable returning True if the user has
  147:                 requested a stop (notebook UX). Phase 11 wires this to the
  148:                 Stop button. Phase 8 keeps it None by default.
  149:         """
  150:         self.client = client
  151:         self.max_turns = max(1, int(max_turns))
  152:         self.budget = budget if budget is not None else IterationBudget()
  153:         self.on_stop_check = on_stop_check
  154: 
  155:         self.messages: List[Dict[str, Any]] = []
  156:         # Tool names that have been "discovered" via tool_search this run.
  157:         # Their schemas are added to per-turn `tools=` API payload until the
  158:         # run ends. v5 does NOT persist discovery across `run()` calls â€” the
  159:         # set is fresh each user message (matches Runnable's per-message
  160:         # discovered set).
  161:         self._discovered_tool_names: Set[str] = set()
  162: 
  163:     # ------------------------------------------------------------
  164:     # Public entry: run(...)
  165:     # ------------------------------------------------------------
  166: 
  167:     def run(
  168:         self,
  169:         user_message: str,
  170:         system_prompt: str,
  171:         tools: List[Any],
  172:         plan_mode: bool = False,
  173:         output_fn: Callable[[str], None] = print,
  174:         thinking_enabled: bool = False,
  175:         thinking_budget: int = 4096,
  176:         max_tokens: int = 4096,
  177:         temperature: float = 0.0,
  178:     ) -> QueryResult:
  179:         """Execute the agent loop until a stop condition is reached.
  180: 
  181:         See class docstring for the IN-SCOPE / OUT-OF-SCOPE list.
  182:         """
  183:         # Append user turn (Bedrock requires alternation; merge into trailing
  184:         # user if needed â€” matches v4 sagemaker_agent.py:8744).
  185:         if self.messages and self.messages[-1].get("role") == "user":
  186:             prev = self.messages[-1]
  187:             prev_content = prev.get("content", "")
  188:             if isinstance(prev_content, str):
  189:                 prev["content"] = prev_content + "\n\n" + user_message
  190:             elif isinstance(prev_content, list):
  191:                 prev_content.append({"type": "text", "text": user_message})
  192:             else:
  193:                 self.messages.append({"role": "user", "content": user_message})
  194:         else:
  195:             self.messages.append({"role": "user", "content": user_message})
  196: 
  197:         # Defer-import to avoid circular import at module-load.
  198:         from tools.registry import apply_tool_search_deferral, find_tool_by_name
  199:         from tools.tool_search import tool_search_discovered_names
  200: 
  201:         last_text = ""
  202:         stop_reason = ""
  203:         turns_used = 0
  204: 
  205:         for turn in range(self.max_turns):
  206:             # User-requested stop (Phase 11 wires this to the Stop button).
  207:             if self.on_stop_check and self.on_stop_check():
  208:                 output_fn("[Stopped by user]")
  209:                 stop_reason = "user_stop"
  210:                 break
  211: 
  212:             # Budget gate â€” shared with sub-agents (Phase 9).
  213:             if not self.budget.consume():
  214:                 used, total = self.budget.used(), self.budget.total()
  215:                 output_fn(
  216:                     f"[Budget exhausted: {used}/{total} iterations used. "
  217:                     "Adjust IterationBudget or start a new session.]"
  218:                 )
  219:                 stop_reason = "budget_exhausted"
  220:                 break
  221: 
  222:             # Phase 7 wiring contract: per-turn deferral + discovery merge.
  223:             visible_tools, deferred_names = apply_tool_search_deferral(
  224:                 tools, enabled=True,
  225:             )
  226:             if self._discovered_tool_names:
  227:                 # Promote previously-discovered tools from deferred â†’ visible.
  228:                 discovered = {n for n in self._discovered_tool_names if n in deferred_names}
  229:                 if discovered:
  230:                     promoted = [
  231:                         t for t in tools
  232:                         if t.name in discovered and t.name not in {v.name for v in visible_tools}
  233:                     ]
  234:                     visible_tools = visible_tools + promoted
  235:                     deferred_names = [n for n in deferred_names if n not in discovered]
  236: 
  237:             # If any names remain deferred, surface them as a system reminder
  238:             # so the model knows they exist and how to load them.
  239:             turn_messages = list(self.messages)
  240:             if deferred_names:

### query_engine.py:241-360
  241:                 turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)
  242: 
  243:             # Bedrock invocation.
  244:             try:
  245:                 response = self.client.chat(
  246:                     messages=turn_messages,
  247:                     system=system_prompt,
  248:                     tools=_build_tools_api_payload(visible_tools),
  249:                     max_tokens=max_tokens,
  250:                     temperature=temperature,
  251:                     thinking_enabled=thinking_enabled,
  252:                     thinking_budget=thinking_budget,
  253:                 )
  254:             except Exception as exc:  # noqa: BLE001 â€” classify and surface
  255:                 category, recovery, debug = ErrorClassifier.classify(exc)
  256:                 output_fn(f"[Bedrock {category}: {debug}]")
  257:                 if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
  258:                     stop_reason = "context_overflow"
  259:                 else:
  260:                     stop_reason = "fatal_error"
  261:                 return QueryResult(
  262:                     text=last_text,
  263:                     messages=list(self.messages),
  264:                     stop_reason=stop_reason,
  265:                     turns_used=turns_used,
  266:                     budget_used=self.budget.used(),
  267:                     error=f"{category}: {debug}",
  268:                 )
  269: 
  270:             turns_used += 1
  271: 
  272:             # Append assistant turn (text + tool_use blocks, plus thinking).
  273:             assistant_content = self._build_assistant_content(response)
  274:             self.messages.append({"role": "assistant", "content": assistant_content})
  275: 
  276:             if response.text:
  277:                 last_text = response.text
  278: 
  279:             # Stop conditions: end_turn / no tool_use blocks â†’ final answer.
  280:             if not response.tool_calls:
  281:                 stop_reason = "end_turn"
  282:                 if response.text:
  283:                     output_fn(response.text)
  284:                 break
  285: 
  286:             # Tool dispatch â€” emit one tool_result per tool_use call.
  287:             tool_results: List[Dict[str, Any]] = []
  288:             for call in response.tool_calls:
  289:                 tool = find_tool_by_name(tools, call.name)
  290:                 if tool is None:
  291:                     # Unknown tool name â€” return error to model so it can
  292:                     # recover (v4 parity: dispatch never raises).
  293:                     tool_results.append({
  294:                         "type": "tool_result",
  295:                         "tool_use_id": call.id,
  296:                         "content": f"Error: unknown tool '{call.name}'",
  297:                         "is_error": True,
  298:                     })
  299:                     continue
  300: 
  301:                 # Plan-mode read-only enforcement (v4 PLAN_MODE_ALLOWED_TOOLS).
  302:                 if plan_mode and not tool.is_read_only and not getattr(tool, "always_load", False):
  303:                     tool_results.append({
  304:                         "type": "tool_result",
  305:                         "tool_use_id": call.id,
  306:                         "content": (
  307:                             f"Error: tool '{call.name}' is mutating; "
  308:                             "blocked in plan mode."
  309:                         ),
  310:                         "is_error": True,
  311:                     })
  312:                     continue
  313: 
  314:                 # Execute. Tool implementations may raise; we trap and surface
  315:                 # the error to the model rather than the human user.
  316:                 try:
  317:                     raw = tool.execute(call.input, context={
  318:                         "active_tools": tools,
  319:                         "plan_mode": plan_mode,
  320:                     })
  321:                     text = _coerce_tool_result_to_text(raw)
  322:                     text = _truncate_tool_result(text, tool.max_result_size_chars)
  323:                     tool_results.append({
  324:                         "type": "tool_result",
  325:                         "tool_use_id": call.id,
  326:                         "content": text,
  327:                     })
  328:                     # Phase 7 wiring: extract discovered names from tool_search
  329:                     # results and add to the next turn's tools= payload.
  330:                     if call.name == "tool_search":
  331:                         discovered = tool_search_discovered_names(text)
  332:                         if discovered:
  333:                             self._discovered_tool_names.update(discovered)
  334:                 except Exception as exc:  # noqa: BLE001 â€” surface to model
  335:                     logging.warning(
  336:                         "[query_engine] tool '%s' raised %s: %s",
  337:                         call.name, type(exc).__name__, exc,
  338:                     )
  339:                     tool_results.append({
  340:                         "type": "tool_result",
  341:                         "tool_use_id": call.id,
  342:                         "content": f"Error: {type(exc).__name__}: {exc}",
  343:                         "is_error": True,
  344:                     })
  345: 
  346:             # Append the tool_results as a user turn (Bedrock convention).
  347:             self.messages.append({"role": "user", "content": tool_results})
  348: 
  349:         else:  # for-loop fell through without break
  350:             stop_reason = "max_turns"
  351:             output_fn(f"[Max turns reached: {self.max_turns}]")
  352: 
  353:         return QueryResult(
  354:             text=last_text,
  355:             messages=list(self.messages),
  356:             stop_reason=stop_reason or "end_turn",
  357:             turns_used=turns_used,
  358:             budget_used=self.budget.used(),
  359:         )
  360: 

### query_engine.py:361-467
  361:     # ------------------------------------------------------------
  362:     # Internal: assemble assistant turn content from a Bedrock Response
  363:     # ------------------------------------------------------------
  364: 
  365:     @staticmethod
  366:     def _build_assistant_content(response: Any) -> List[Dict[str, Any]]:
  367:         """Construct a Bedrock-shaped assistant content list from a Response.
  368: 
  369:         Order: thinking blocks (if any) â†’ text â†’ tool_use. The thinking
  370:         block is preserved so the next turn's API call carries it back to
  371:         the model (Bedrock requires this for extended thinking continuity).
  372:         """
  373:         blocks: List[Dict[str, Any]] = []
  374:         thinking = getattr(response, "thinking", "") or ""
  375:         if thinking:
  376:             blocks.append({"type": "thinking", "thinking": thinking})
  377:         if response.text:
  378:             blocks.append({"type": "text", "text": response.text})
  379:         for call in response.tool_calls:
  380:             blocks.append({
  381:                 "type": "tool_use",
  382:                 "id": call.id,
  383:                 "name": call.name,
  384:                 "input": call.input,
  385:             })
  386:         return blocks
  387: 
  388:     # ------------------------------------------------------------
  389:     # Internal: deferred-tools system reminder injection
  390:     # ------------------------------------------------------------
  391: 
  392:     @staticmethod
  393:     def _inject_deferred_reminder(
  394:         messages: List[Dict[str, Any]],
  395:         deferred_names: List[str],
  396:     ) -> List[Dict[str, Any]]:
  397:         """Append a `<system-reminder>` block listing deferred tool names so
  398:         the model knows what's available via tool_search.
  399: 
  400:         The reminder is injected as a transient text block on the trailing
  401:         user turn â€” it does not mutate `self.messages`, so it does not leak
  402:         into subsequent turns once the model has loaded the schemas it needs.
  403:         """
  404:         if not deferred_names:
  405:             return messages
  406:         reminder = (
  407:             "<system-reminder>\n"
  408:             "The following deferred tools are available via tool_search. Their schemas "
  409:             "are NOT loaded â€” calling them directly will fail. Use tool_search with "
  410:             "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
  411:             + "\n".join(sorted(deferred_names))
  412:             + "\n</system-reminder>"
  413:         )
  414:         # Transient append: copy the trailing user message and add the reminder
  415:         # as an extra text block. If the trailing turn is not user-role, we
  416:         # append a fresh user message â€” but this should never happen because
  417:         # the loop only invokes Bedrock right after a user turn or tool_results.
  418:         out = list(messages)
  419:         if not out or out[-1].get("role") != "user":
  420:             out.append({"role": "user", "content": [{"type": "text", "text": reminder}]})
  421:             return out
  422:         last = dict(out[-1])
  423:         content = last.get("content")
  424:         if isinstance(content, str):
  425:             last["content"] = [
  426:                 {"type": "text", "text": content},
  427:                 {"type": "text", "text": reminder},
  428:             ]
  429:         elif isinstance(content, list):
  430:             last["content"] = list(content) + [{"type": "text", "text": reminder}]
  431:         else:
  432:             last["content"] = [{"type": "text", "text": reminder}]
  433:         out[-1] = last
  434:         return out
  435: 
  436: 
  437: # ============================================================
  438: # Single-turn helper for unit tests
  439: # ============================================================
  440: 
  441: def run_one_turn(
  442:     client: Any,
  443:     messages: List[Dict[str, Any]],
  444:     system_prompt: str,
  445:     tools: List[Any],
  446:     max_tokens: int = 4096,
  447:     temperature: float = 0.0,
  448:     thinking_enabled: bool = False,
  449:     thinking_budget: int = 4096,
  450: ) -> Any:
  451:     """Run a single Bedrock invocation with Phase 7 deferral applied.
  452: 
  453:     Returns the raw `Response` object. Tests use this to assert wiring without
  454:     spinning up the full multi-turn loop.
  455:     """
  456:     from tools.registry import apply_tool_search_deferral
  457: 
  458:     visible_tools, _deferred = apply_tool_search_deferral(tools, enabled=True)
  459:     return client.chat(
  460:         messages=messages,
  461:         system=system_prompt,
  462:         tools=_build_tools_api_payload(visible_tools),
  463:         max_tokens=max_tokens,
  464:         temperature=temperature,
  465:         thinking_enabled=thinking_enabled,
  466:         thinking_budget=thinking_budget,
  467:     )

 succeeded in 5223ms:

### test_query_engine.py:1-120
    1: """Phase 08 integration tests: core/query_engine.py â€” end-to-end agent loop.
    2: 
    3: Acceptance criterion (V5_PLAN.md Â§Phase 8):
    4: - end-to-end mock test (tool_use â†’ tool runs â†’ final answer)
    5: - tool_search deferred-loading round-trip works
    6: 
    7: Locks PORT_LOG #019: Runnable QueryEngine.ts adapted to v5 .ipynb shape.
    8: """
    9: from __future__ import annotations
   10: 
   11: import os
   12: import sys
   13: from typing import Any, Dict, List
   14: 
   15: import pytest
   16: 
   17: _AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   18: if _AGENT_ROOT not in sys.path:
   19:     sys.path.insert(0, _AGENT_ROOT)
   20: 
   21: 
   22: # ============================================================
   23: # Test fixtures
   24: # ============================================================
   25: 
   26: class _ScriptedClient:
   27:     """Mock Bedrock client that returns pre-scripted responses in order.
   28: 
   29:     Each entry is one of:
   30:       - ("text", "final answer")              â†’ stop_reason=end_turn, no tools
   31:       - ("tool", call_id, tool_name, args)    â†’ tool_use block
   32:       - ("text+tool", text, call_id, name, args) â†’ both text and tool_use
   33:     """
   34: 
   35:     def __init__(self, script):
   36:         self.script = list(script)
   37:         self.calls = []  # list of (messages, tools_payload)
   38: 
   39:     def chat(self, messages, system, tools, max_tokens, temperature,
   40:              thinking_enabled, thinking_budget):
   41:         from runtime.bedrock_client import Response, ToolCall
   42:         self.calls.append({
   43:             "messages": list(messages),
   44:             "tools": list(tools or []),
   45:         })
   46:         if not self.script:
   47:             return Response(text="(no more scripted responses)", tool_calls=[],
   48:                             stop_reason="end_turn", usage={})
   49:         kind, *rest = self.script.pop(0)
   50:         if kind == "text":
   51:             return Response(text=rest[0], tool_calls=[], stop_reason="end_turn", usage={})
   52:         if kind == "tool":
   53:             cid, name, args = rest
   54:             return Response(
   55:                 text="", tool_calls=[ToolCall(cid, name, args)],
   56:                 stop_reason="tool_use", usage={},
   57:             )
   58:         if kind == "text+tool":
   59:             txt, cid, name, args = rest
   60:             return Response(
   61:                 text=txt,
   62:                 tool_calls=[ToolCall(cid, name, args)],
   63:                 stop_reason="tool_use", usage={},
   64:             )
   65:         raise AssertionError(f"unknown script kind: {kind}")
   66: 
   67: 
   68: @pytest.fixture(autouse=True)
   69: def fresh_registry():
   70:     """Phase 7 / Phase 2 tests mutate the registry; force-reset for Phase 8."""
   71:     from tools.registry import _reset_registry_for_tests
   72:     from tools import bootstrap_built_ins
   73:     _reset_registry_for_tests()
   74:     bootstrap_built_ins()
   75:     yield
   76: 
   77: 
   78: # ============================================================
   79: # Test 1 â€” basic single-turn end_turn
   80: # ============================================================
   81: 
   82: def test_engine_returns_final_text_on_end_turn():
   83:     from core import QueryEngine
   84:     from tools import all_registered
   85: 
   86:     client = _ScriptedClient([("text", "Hello world.")])
   87:     engine = QueryEngine(client=client, max_turns=5)
   88:     result = engine.run(
   89:         user_message="say hi",
   90:         system_prompt="you are an assistant",
   91:         tools=all_registered(),
   92:     )
   93:     assert result.stop_reason == "end_turn"
   94:     assert result.text == "Hello world."
   95:     assert result.turns_used == 1
   96: 
   97: 
   98: # ============================================================
   99: # Test 2 â€” tool_use â†’ tool runs â†’ tool_result â†’ final answer
  100: # ============================================================
  101: 
  102: def test_engine_dispatches_tool_then_finalizes():
  103:     from core import QueryEngine
  104:     from tools import all_registered
  105: 
  106:     # Turn 1: model asks for read_file. Turn 2: model gives final answer.
  107:     client = _ScriptedClient([
  108:         ("tool", "call_1", "read_file", {"file_path": "nonexistent_for_test.txt"}),
  109:         ("text", "I read the file."),
  110:     ])
  111:     engine = QueryEngine(client=client, max_turns=5)
  112:     result = engine.run(
  113:         user_message="read a file",
  114:         system_prompt="sys",
  115:         tools=all_registered(),
  116:     )
  117:     assert result.stop_reason == "end_turn"
  118:     assert result.text == "I read the file."
  119:     assert result.turns_used == 2
  120:     # Conversation must contain: user, assistant(tool_use), user(tool_result), assistant(text).

### test_query_engine.py:121-240
  121:     roles = [m["role"] for m in result.messages]
  122:     assert roles == ["user", "assistant", "user", "assistant"]
  123:     # The tool_result block must have correct tool_use_id.
  124:     tr_block = result.messages[2]["content"][0]
  125:     assert tr_block["type"] == "tool_result"
  126:     assert tr_block["tool_use_id"] == "call_1"
  127: 
  128: 
  129: # ============================================================
  130: # Test 3 â€” Phase 7 wiring contract: tools= payload excludes deferred tools by default
  131: # ============================================================
  132: 
  133: def test_engine_excludes_deferred_tools_from_first_turn_payload():
  134:     """First turn, no tool_search calls yet: per-turn `tools=` must NOT include
  135:     view_image, list_dir, notebook_edit. tool_search itself MUST be included."""
  136:     from core import QueryEngine
  137:     from tools import all_registered
  138: 
  139:     client = _ScriptedClient([("text", "ok")])
  140:     engine = QueryEngine(client=client, max_turns=2)
  141:     engine.run(
  142:         user_message="hi",
  143:         system_prompt="sys",
  144:         tools=all_registered(),
  145:     )
  146:     sent_tools = client.calls[0]["tools"]
  147:     sent_names = {t["name"] for t in sent_tools}
  148:     assert "tool_search" in sent_names
  149:     assert "view_image" not in sent_names
  150:     assert "list_dir" not in sent_names
  151:     assert "notebook_edit" not in sent_names
  152:     # high-frequency tools must remain visible
  153:     assert "read_file" in sent_names
  154:     assert "edit_file" in sent_names
  155: 
  156: 
  157: # ============================================================
  158: # Test 4 â€” Phase 7 round-trip: tool_search promotes deferred tool into next turn
  159: # ============================================================
  160: 
  161: def test_tool_search_round_trip_promotes_deferred_tool():
  162:     """Phase 8 acceptance: model calls tool_search â†’ query_engine extracts the
  163:     discovered names â†’ next turn's `tools=` payload includes those tools.
  164: 
  165:     The hidden marker `<!-- v5_discovered:NAME --> ` emitted by tool_search is
  166:     extracted via `tool_search_discovered_names()` and the named tool's full
  167:     schema is added to the next turn's payload."""
  168:     from core import QueryEngine
  169:     from tools import all_registered
  170: 
  171:     # Turn 1: model calls tool_search for view_image (a deferred tool).
  172:     # Turn 2: model now calls view_image (its schema was promoted).
  173:     # Turn 3: model gives final answer.
  174:     client = _ScriptedClient([
  175:         ("tool", "call_1", "tool_search", {"query": "select:view_image"}),
  176:         ("tool", "call_2", "view_image", {"file_path": "nonexistent.png"}),
  177:         ("text", "Done."),
  178:     ])
  179:     engine = QueryEngine(client=client, max_turns=5)
  180:     result = engine.run(
  181:         user_message="look at an image",
  182:         system_prompt="sys",
  183:         tools=all_registered(),
  184:     )
  185:     assert result.stop_reason == "end_turn"
  186:     assert result.turns_used == 3
  187: 
  188:     # Turn 1 payload: view_image is NOT in tools=
  189:     turn1_names = {t["name"] for t in client.calls[0]["tools"]}
  190:     assert "view_image" not in turn1_names
  191:     assert "tool_search" in turn1_names
  192: 
  193:     # Turn 2 payload: view_image IS in tools= (promoted by Phase 7 wiring)
  194:     turn2_names = {t["name"] for t in client.calls[1]["tools"]}
  195:     assert "view_image" in turn2_names, (
  196:         "view_image must be promoted into per-turn payload after tool_search "
  197:         "discovered it"
  198:     )
  199: 
  200: 
  201: # ============================================================
  202: # Test 5 â€” IterationBudget gate stops the loop
  203: # ============================================================
  204: 
  205: def test_engine_stops_on_budget_exhausted():
  206:     """Pre-consume the budget so the first turn can't be entered."""
  207:     from core import QueryEngine, IterationBudget
  208:     from tools import all_registered
  209: 
  210:     budget = IterationBudget(max_iterations=2)
  211:     budget.consume()
  212:     budget.consume()  # exhausted
  213: 
  214:     client = _ScriptedClient([("text", "should not be reached")])
  215:     engine = QueryEngine(client=client, max_turns=5, budget=budget)
  216:     result = engine.run(
  217:         user_message="hi",
  218:         system_prompt="sys",
  219:         tools=all_registered(),
  220:     )
  221:     assert result.stop_reason == "budget_exhausted"
  222:     assert result.turns_used == 0
  223:     assert client.calls == []  # client.chat() was never called
  224: 
  225: 
  226: # ============================================================
  227: # Test 6 â€” max_turns cap
  228: # ============================================================
  229: 
  230: def test_engine_stops_at_max_turns():
  231:     """If model never returns end_turn, the loop must exit cleanly at max_turns."""
  232:     from core import QueryEngine
  233:     from tools import all_registered
  234: 
  235:     # Always returns tool_use for read_file â†’ engine never reaches end_turn.
  236:     looping_script = [
  237:         ("tool", f"call_{i}", "read_file", {"file_path": f"x{i}.txt"})
  238:         for i in range(20)
  239:     ]
  240:     client = _ScriptedClient(looping_script)

### test_query_engine.py:241-360
  241:     engine = QueryEngine(client=client, max_turns=3)
  242:     result = engine.run(
  243:         user_message="loop",
  244:         system_prompt="sys",
  245:         tools=all_registered(),
  246:     )
  247:     assert result.stop_reason == "max_turns"
  248:     assert result.turns_used == 3
  249: 
  250: 
  251: # ============================================================
  252: # Test 7 â€” unknown tool name surfaces error to model
  253: # ============================================================
  254: 
  255: def test_engine_returns_error_tool_result_for_unknown_tool():
  256:     from core import QueryEngine
  257:     from tools import all_registered
  258: 
  259:     client = _ScriptedClient([
  260:         ("tool", "call_1", "definitely_not_a_tool", {}),
  261:         ("text", "ok, sorry"),
  262:     ])
  263:     engine = QueryEngine(client=client, max_turns=5)
  264:     result = engine.run(
  265:         user_message="call a tool that doesn't exist",
  266:         system_prompt="sys",
  267:         tools=all_registered(),
  268:     )
  269:     # Loop continues â€” model gets an error tool_result and can recover
  270:     assert result.stop_reason == "end_turn"
  271:     tr_block = result.messages[2]["content"][0]
  272:     assert tr_block["is_error"] is True
  273:     assert "unknown tool" in tr_block["content"]
  274: 
  275: 
  276: # ============================================================
  277: # Test 8 â€” tool that raises is surfaced to model, not user
  278: # ============================================================
  279: 
  280: def test_engine_traps_tool_exception():
  281:     from core import QueryEngine
  282:     from tools.registry import build_tool, register, all_registered
  283: 
  284:     def boom(args, context=None):
  285:         raise RuntimeError("kaboom")
  286: 
  287:     register(build_tool(
  288:         name="boom_tool",
  289:         description="raises",
  290:         input_schema={"type": "object", "properties": {}},
  291:         execute=boom,
  292:         is_read_only=True,
  293:     ))
  294: 
  295:     client = _ScriptedClient([
  296:         ("tool", "call_1", "boom_tool", {}),
  297:         ("text", "recovered"),
  298:     ])
  299:     engine = QueryEngine(client=client, max_turns=5)
  300:     result = engine.run(
  301:         user_message="call boom",
  302:         system_prompt="sys",
  303:         tools=all_registered(),
  304:     )
  305:     assert result.stop_reason == "end_turn"
  306:     tr = result.messages[2]["content"][0]
  307:     assert tr["is_error"] is True
  308:     assert "RuntimeError" in tr["content"]
  309:     assert "kaboom" in tr["content"]
  310: 
  311: 
  312: # ============================================================
  313: # Test 9 â€” system reminder injected for deferred tools
  314: # ============================================================
  315: 
  316: def test_engine_injects_deferred_tools_system_reminder_on_first_turn():
  317:     from core import QueryEngine
  318:     from tools import all_registered
  319: 
  320:     client = _ScriptedClient([("text", "ok")])
  321:     engine = QueryEngine(client=client, max_turns=2)
  322:     engine.run(
  323:         user_message="hi",
  324:         system_prompt="sys",
  325:         tools=all_registered(),
  326:     )
  327:     sent_messages = client.calls[0]["messages"]
  328:     last_user = sent_messages[-1]
  329:     assert last_user["role"] == "user"
  330:     # The system reminder must be appended as a text block on the user turn
  331:     if isinstance(last_user["content"], list):
  332:         joined = "\n".join(
  333:             blk.get("text", "") for blk in last_user["content"]
  334:             if isinstance(blk, dict)
  335:         )
  336:     else:
  337:         joined = last_user["content"]
  338:     assert "<system-reminder>" in joined
  339:     assert "view_image" in joined
  340:     assert "tool_search" in joined  # mentioned as the loader
  341: 
  342: 
  343: # ============================================================
  344: # Test 10 â€” context_overflow stops cleanly
  345: # ============================================================
  346: 
  347: def test_engine_stops_on_context_overflow():
  348:     """Bedrock raising prompt-too-long must classify as context_overflow and
  349:     return cleanly with stop_reason set."""
  350:     from core import QueryEngine
  351:     from tools import all_registered
  352: 
  353:     class OverflowClient:
  354:         def chat(self, **_kw):
  355:             raise Exception("ValidationException: prompt is too long")
  356: 
  357:     engine = QueryEngine(client=OverflowClient(), max_turns=5)
  358:     result = engine.run(
  359:         user_message="hi",
  360:         system_prompt="sys",

### test_query_engine.py:361-409
  361:         tools=all_registered(),
  362:     )
  363:     assert result.stop_reason == "context_overflow"
  364:     assert "context_overflow" in (result.error or "")
  365: 
  366: 
  367: # ============================================================
  368: # Test 11 â€” run_one_turn helper
  369: # ============================================================
  370: 
  371: def test_run_one_turn_helper_applies_deferral():
  372:     from core import run_one_turn
  373:     from tools import all_registered
  374: 
  375:     client = _ScriptedClient([("text", "single turn")])
  376:     response = run_one_turn(
  377:         client=client,
  378:         messages=[{"role": "user", "content": "hi"}],
  379:         system_prompt="sys",
  380:         tools=all_registered(),
  381:     )
  382:     assert response.text == "single turn"
  383:     sent_names = {t["name"] for t in client.calls[0]["tools"]}
  384:     assert "view_image" not in sent_names
  385:     assert "tool_search" in sent_names
  386: 
  387: 
  388: # ============================================================
  389: # Test 12 â€” plan mode blocks mutating tools at dispatch
  390: # ============================================================
  391: 
  392: def test_engine_blocks_mutating_tool_in_plan_mode():
  393:     from core import QueryEngine
  394:     from tools import all_registered
  395: 
  396:     client = _ScriptedClient([
  397:         ("tool", "call_1", "edit_file", {"file_path": "x", "old_string": "a", "new_string": "b"}),
  398:         ("text", "noted"),
  399:     ])
  400:     engine = QueryEngine(client=client, max_turns=5)
  401:     result = engine.run(
  402:         user_message="edit a file",
  403:         system_prompt="sys",
  404:         tools=all_registered(),
  405:         plan_mode=True,
  406:     )
  407:     tr = result.messages[2]["content"][0]
  408:     assert tr["is_error"] is True
  409:     assert "plan mode" in tr["content"]

 succeeded in 6451ms:

### bedrock_client.py:1-140
    1: """V5 BedrockClient â€” verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560.
    2: 
    3: Per ADR-005: BedrockClient is a pure v4 reuse (Bedrock-native, already
    4: production-tested). The only Phase-1 change is structural â€” the class lives
    5: in its own module instead of inline in the v4 monolith.
    6: 
    7: Sophisticated cache-break detection (Runnable promptCacheBreakDetection.ts)
    8: is DEFERRED to Phase 6 because it requires multi-block system prompts that
    9: v5 doesn't have until prompt/sections.py lands. Phase 6 ADR will track that
   10: adoption.
   11: 
   12: Phase 1 simplification: the full retry-classifier + jittered-backoff loop
   13: lives in v4's BedrockClient. For Phase 1, we keep that loop intact (it's
   14: already battle-tested), but the helper classes (BedrockErrorCategory,
   15: ErrorClassifier, RetryPolicy) are imported from a temporary local module
   16: inside this file. Phase 8 will extract them to core/errors.py + core/retry.py
   17: with cleaner separation. This avoids a circular Phase-1/Phase-8 dependency.
   18: 
   19: PS Issue #4 verification (per V5_PS_ISSUES_MAPPING.md): tests/unit/test_bedrock.py
   20: must verify thinking config is sent on EVERY Bedrock call when
   21: CONFIG.thinking_enabled=True (not just the first turn).
   22: 
   23: Source: compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560.
   24: """
   25: from __future__ import annotations
   26: 
   27: import json
   28: import logging
   29: import time
   30: from dataclasses import dataclass, field
   31: from typing import Any, Dict, List, Optional
   32: 
   33: # botocore.config import is local-deferred so unit tests with mock_mode=True
   34: # can import this module without boto3 installed. Real flows will import on demand.
   35: 
   36: # CONFIG is imported lazily within methods to avoid circular import during Phase 1.
   37: 
   38: 
   39: # ============================================================
   40: # Response / ToolCall (lightweight value types â€” verbatim from v4)
   41: # ============================================================
   42: 
   43: @dataclass
   44: class ToolCall:
   45:     """A tool invocation request from the model."""
   46:     id: str
   47:     name: str
   48:     input: Dict[str, Any] = field(default_factory=dict)
   49: 
   50: 
   51: @dataclass
   52: class Response:
   53:     """Parsed Bedrock response."""
   54:     text: str
   55:     tool_calls: List[ToolCall] = field(default_factory=list)
   56:     stop_reason: str = ""
   57:     usage: Dict[str, Any] = field(default_factory=dict)
   58:     thinking: str = ""
   59: 
   60: 
   61: # ============================================================
   62: # Error categories + classifier + retry policy
   63: # Phase 8: extracted to core/errors.py + core/retry.py (ADR-014).
   64: # Re-imported here so existing call-sites (and tests) continue to work
   65: # byte-equivalent with Phase 1.
   66: # ============================================================
   67: 
   68: from core.errors import BedrockErrorCategory, ErrorClassifier  # noqa: F401
   69: from core.retry import RetryPolicy  # noqa: F401
   70: 
   71: 
   72: # ============================================================
   73: # BedrockClient (v4 verbatim port)
   74: # ============================================================
   75: 
   76: # botocore Config preset for retry tuning (v4 default).
   77: def _bedrock_client_config():
   78:     """Return a botocore Config with v4's retry tuning. Local-imports botocore."""
   79:     from botocore.config import Config as _BotoConfig
   80:     return _BotoConfig(
   81:         retries={"max_attempts": 1, "mode": "standard"},  # we handle retries ourselves
   82:         read_timeout=120,
   83:         connect_timeout=10,
   84:     )
   85: 
   86: 
   87: class BedrockClient:
   88:     """AWS Bedrock Claude client with mock mode for testing.
   89: 
   90:     Verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:2378.
   91:     Behavior unchanged â€” same prompt-cache fallback semantics, same retry
   92:     classifier, same thinking-mode handling.
   93: 
   94:     PS Issue #4 verification: `chat()` always sends `thinking` config when
   95:     `thinking_enabled=True`, regardless of which call this is in the session.
   96:     The fact that the model only RETURNS thinking blocks on some turns is a
   97:     model-side decision; v5 always SENDS the config so the model has the
   98:     option. test_bedrock.py verifies this.
   99:     """
  100: 
  101:     def __init__(
  102:         self,
  103:         model_id: str,
  104:         region: str,
  105:         mock_mode: bool = False,
  106:         client: Any = None,
  107:     ):
  108:         """Construct a BedrockClient.
  109: 
  110:         Args:
  111:             model_id: Bedrock inference profile id.
  112:             region: AWS region.
  113:             mock_mode: if True, no real Bedrock calls; `_mock_response()` is used.
  114:             client: optional pre-built bedrock-runtime client. If provided,
  115:                 boto3 is NOT imported. This lets unit tests inject a fake
  116:                 client without requiring boto3 to be installed (Codex Phase-01
  117:                 review finding 1).
  118:         """
  119:         self.model_id = model_id
  120:         self.region = region
  121:         self.mock_mode = mock_mode
  122:         self.prompt_cache_supported = True  # set False after first cache fallback
  123:         self._cache_threshold_warned = False
  124:         if mock_mode:
  125:             self.client = None
  126:         elif client is not None:
  127:             self.client = client
  128:         else:
  129:             import boto3
  130:             self.client = boto3.client(
  131:                 "bedrock-runtime", region_name=region, config=_bedrock_client_config()
  132:             )
  133: 
  134:     # ---------- mock-mode helpers ----------
  135: 
  136:     def _mock_response(self, messages, tools) -> Response:
  137:         """Generate mock response for testing (v4 verbatim, simplified)."""
  138:         last = messages[-1]["content"] if messages else ""
  139:         if isinstance(last, str):
  140:             low = last.lower()

### bedrock_client.py:141-280
  141:             if "list" in low and ("file" in low or "dir" in low):
  142:                 return Response(
  143:                     "I'll list the files.",
  144:                     [ToolCall("m1", "list_dir", {"path": "."})],
  145:                     "tool_use",
  146:                     {},
  147:                 )
  148:             if "read" in low:
  149:                 return Response(
  150:                     "I'll read that file.",
  151:                     [ToolCall("m2", "read_file", {"file_path": "README.md"})],
  152:                     "tool_use",
  153:                     {},
  154:                 )
  155:         return Response(
  156:             f"[MOCK] Received: {str(last)[:100]}...",
  157:             [],
  158:             "end_turn",
  159:             {"input_tokens": 100, "output_tokens": 50},
  160:         )
  161: 
  162:     # ---------- main chat entry ----------
  163: 
  164:     def chat(
  165:         self,
  166:         messages: List[Dict],
  167:         system: Any,  # str OR list-of-blocks (with cache_control)
  168:         tools: Optional[List[Dict]] = None,
  169:         max_tokens: int = 4096,
  170:         temperature: float = 0.0,
  171:         thinking_enabled: bool = False,
  172:         thinking_budget: int = 4096,
  173:     ) -> Response:
  174:         """Send chat request to Bedrock.
  175: 
  176:         Args:
  177:             messages: Conversation messages
  178:             system: System prompt (str or pre-formatted multi-block list with cache_control)
  179:             tools: Tool definitions
  180:             max_tokens: Maximum response tokens
  181:             temperature: Sampling temperature (0.0-1.0)
  182:             thinking_enabled: Enable extended thinking mode
  183:             thinking_budget: Max tokens for thinking (1024-16000)
  184:         """
  185:         if self.mock_mode:
  186:             return self._mock_response(messages, tools)
  187: 
  188:         # Lazy import CONFIG to avoid circular import during Phase 1.
  189:         from runtime.config import CONFIG
  190: 
  191:         # V4.1 #14: Prompt cache boundary.
  192:         # If cache enabled and supported, split system string into static (cached)
  193:         # + dynamic (uncached) blocks. Bedrock supports prompt caching natively
  194:         # via cache_control blocks in content. No anthropic_beta header needed.
  195:         # Haiku 4.5: min 4096 tokens/checkpoint. Sonnet 4.5: min 1024.
  196:         cache_active = CONFIG.enable_prompt_cache and self.prompt_cache_supported
  197:         if cache_active and isinstance(system, list):
  198:             # Already formatted as cache blocks by caller â€” pass as-is
  199:             system_field = system
  200:             use_cache = True
  201:         elif cache_active and isinstance(system, str):
  202:             # Split at the dynamic boundary marker if present, else cache full prompt
  203:             _CACHE_BOUNDARY = "\n\n# === DYNAMIC ==="
  204:             if _CACHE_BOUNDARY in system:
  205:                 static_part, dynamic_part = system.split(_CACHE_BOUNDARY, 1)
  206:                 # Bedrock rejects empty/whitespace text blocks â€” only add dynamic if non-empty
  207:                 if dynamic_part.strip():
  208:                     system_field = [
  209:                         {
  210:                             "type": "text",
  211:                             "text": static_part,
  212:                             "cache_control": {"type": "ephemeral"},
  213:                         },
  214:                         {"type": "text", "text": dynamic_part},
  215:                     ]
  216:                 else:
  217:                     system_field = [
  218:                         {
  219:                             "type": "text",
  220:                             "text": static_part,
  221:                             "cache_control": {"type": "ephemeral"},
  222:                         },
  223:                     ]
  224:             else:
  225:                 # No boundary â€” cache the whole prompt as static
  226:                 system_field = [
  227:                     {
  228:                         "type": "text",
  229:                         "text": system,
  230:                         "cache_control": {"type": "ephemeral"},
  231:                     },
  232:                 ]
  233:             use_cache = True
  234:         else:
  235:             system_field = system
  236:             use_cache = False
  237: 
  238:         body: Dict[str, Any] = {
  239:             "anthropic_version": "bedrock-2023-05-31",
  240:             "max_tokens": max_tokens,
  241:             "system": system_field,
  242:             "messages": messages,
  243:         }
  244:         # Note: Bedrock prompt caching is activated by cache_control blocks in
  245:         # content. No anthropic_beta header needed (that header is for the direct
  246:         # Anthropic API only).
  247: 
  248:         # Extended thinking mode (requires temperature=1).
  249:         # PS Issue #4: this block runs on EVERY chat() call when thinking_enabled
  250:         # is True â€” not just first message. The model decides per turn whether
  251:         # to USE the budget. tests/unit/test_bedrock.py asserts this contract.
  252:         if thinking_enabled:
  253:             body["thinking"] = {
  254:                 "type": "enabled",
  255:                 "budget_tokens": min(max(thinking_budget, 1024), 16000),
  256:             }
  257:             body["temperature"] = 1  # Required for thinking mode
  258:         else:
  259:             body["temperature"] = temperature
  260: 
  261:         if tools:
  262:             body["tools"] = tools
  263: 
  264:         # V4.9.4: jittered exponential backoff on transient/throttle errors.
  265:         # Cache-validation: strip cache blocks and retry once (existing v4.1 #14).
  266:         attempt = 0
  267:         last_exc: Optional[Exception] = None
  268:         while True:
  269:             try:
  270:                 response = self.client.invoke_model(
  271:                     modelId=self.model_id,
  272:                     body=json.dumps(body, separators=(",", ":")),
  273:                     contentType="application/json",
  274:                 )
  275:                 break  # success
  276:             except Exception as e:
  277:                 last_exc = e
  278:                 category, recovery, debug_msg = ErrorClassifier.classify(e)
  279: 
  280:                 # Cache-validation: strip cache blocks, retry once

### bedrock_client.py:281-344
  281:                 if (
  282:                     category == BedrockErrorCategory.VALIDATION_CACHE
  283:                     and use_cache
  284:                     and self.prompt_cache_supported
  285:                 ):
  286:                     logging.warning(
  287:                         f"[BEDROCK] Prompt cache not supported by this model/region, falling back: {debug_msg}"
  288:                     )
  289:                     self.prompt_cache_supported = False
  290:                     if isinstance(system, str):
  291:                         body["system"] = system
  292:                     else:
  293:                         body["system"] = "\n\n".join(
  294:                             b.get("text", "") for b in system if isinstance(b, dict)
  295:                         )
  296:                     use_cache = False
  297:                     continue
  298: 
  299:                 # Throttle / transient / etc.: retry with jitter
  300:                 if RetryPolicy.should_retry(attempt, recovery):
  301:                     sleep_s = RetryPolicy.backoff_seconds(attempt)
  302:                     logging.warning(
  303:                         f"[BEDROCK] {category} (recovery={recovery}, attempt={attempt + 1}/"
  304:                         f"{RetryPolicy.MAX_RETRIES + 1}, sleep={sleep_s:.1f}s): {debug_msg}"
  305:                     )
  306:                     time.sleep(sleep_s)
  307:                     attempt += 1
  308:                     continue
  309: 
  310:                 # Anything else: surface it
  311:                 logging.error(f"[BEDROCK] {category} (recovery={recovery}, no-retry): {debug_msg}")
  312:                 raise
  313: 
  314:         result = json.loads(response["body"].read())
  315:         return self._parse(result)
  316: 
  317:     # ---------- response parsing ----------
  318: 
  319:     def _parse(self, result: dict) -> Response:
  320:         """Parse Bedrock response into Response value type (v4 verbatim)."""
  321:         text = ""
  322:         thinking = ""
  323:         tool_calls: List[ToolCall] = []
  324:         for block in result.get("content", []):
  325:             block_type = block.get("type")
  326:             if block_type == "text":
  327:                 text += block.get("text", "")
  328:             elif block_type == "thinking":
  329:                 thinking += block.get("thinking", "")
  330:             elif block_type == "tool_use":
  331:                 tool_calls.append(
  332:                     ToolCall(
  333:                         id=block.get("id", ""),
  334:                         name=block.get("name", ""),
  335:                         input=block.get("input", {}),
  336:                     )
  337:                 )
  338:         return Response(
  339:             text=text,
  340:             tool_calls=tool_calls,
  341:             stop_reason=result.get("stop_reason", ""),
  342:             usage=result.get("usage", {}),
  343:             thinking=thinking,
  344:         )

 succeeded in 7674ms:
 succeeded in 10740ms:

### v4 sagemaker_agent.py:8160-8245
 8160: # MCP (Model Context Protocol)
 8161: MCP servers from config are auto-registered as `mcp_<server>_<tool>` tools. Prefer MCP tools when available.
 8162: 
 8163: # Commands
 8164: `/cost`, `/context` (token/context bloat diagnostic), `/status [init|path]`, `/revert <file>` (shows diff preview; add `--yes` to confirm), `/revert all --yes`, `/diffs [summary|last|<file>]` (session edit history), `/regression` (git diff HEAD stat + session edits + suggested test cmd), `/verify [full|quick|pre-commit]`, `/simplify`, `/done [full|quick]` (simplify+verify gate â†’ READY-TO-SHIP verdict), `/phase <text>` (set current work phase in status bar), `/checkpoint [create <name>|list|restore <name>]`, `/skills` (list available), `/skill use <name>` (activate; lifts any prior /unskill block), `/skill clear` (deactivate all â€” sticky for session), `/unskill <name>` (V4.9.1 â€” deactivate one skill, sticky for session), `/skill suggestions` (V4.9.5 â€” list pending agent-proposed patches), `/skill apply <name> [--yes|--edit]` (V4.9.5 â€” preview diff then apply), `/skill reject <name>` (V4.9.5 â€” discard pending patches), `/commands` (custom).
 8165: 
 8166: # Skill self-patching (V4.9.5, opt-in)
 8167: - ONLY when `CONFIG.enable_skill_patching = True`. If the flag is False, do NOT call `skill_propose_patch` â€” it will no-op. Suggest the improvement in chat instead.
 8168: - WHEN to propose (V4.10.5: 4-rule check from Learning_Factory's promotion criteria â€” propose ONLY if ALL apply):
 8169:   1. **Repeated**: the user has corrected you on the SAME skill the SAME way 3+ times in this session.
 8170:   2. **Non-trivial**: the correction reflects real domain knowledge or a non-obvious workflow rule, not a one-off task preference or a typo.
 8171:   3. **Generalizable**: the correction would help any future run of the skill, not just this session's task.
 8172:   4. **Real-pitfall-avoiding**: the original SKILL.md text led to an actual mistake, broken output, or wasted tokens â€” not just a stylistic difference.
 8173:   Memory (`memory.md`) handles small facts / preferences. Skill patches handle procedural knowledge that is non-trivial AND repeated AND generalizable AND tied to a real pitfall.
 8174: - HOW: call `skill_propose_patch` with `name`, `reason` (one sentence), and `new_content` (the FULL replacement SKILL.md body, frontmatter included â€” NOT a diff). The system writes it to `.proposed/<ts>.md` for the user to review via `/skill suggestions`. The live SKILL.md is NEVER auto-modified.
 8175: - After proposing, mention it in chat ONCE: "I noticed [thing]. I proposed a patch â€” review with /skill suggestions". Do NOT keep nagging.
 8176: 
 8177: # === DYNAMIC ===
 8178: """
 8179: 
 8180: # ============================================================
 8181: # AGENT LOOP
 8182: # ============================================================
 8183: 
 8184: # V4.9.4: IterationBudget â€” shared LLM-turn counter across a parent agent
 8185: # and all its spawned sub-agents. Pattern from hermes-agent run_agent.py:170.
 8186: # Prevents runaway sub-agent costs: a parent agent could otherwise spawn N
 8187: # sub-agents that each loop max_turns times, blowing the cost ceiling.
 8188: # Insurance/audit values predictable cost ceilings per user request.
 8189: 
 8190: class IterationBudget:
 8191:     """Thread-safe counter shared across a parent agent and its spawned sub-agents.
 8192: 
 8193:     A parent agent creates one budget at the start of `run()`; sub-agents inherit
 8194:     the same instance. Each LLM turn (success or failure) increments the counter.
 8195:     When `consume()` returns False, the agent surfaces a "budget exhausted" message
 8196:     and stops cleanly, preserving partial work.
 8197:     """
 8198: 
 8199:     DEFAULT_MAX = 600  # V4.10.10 in-place: 90 â†’ 600 (hermes 90 too tight for SageMaker dev)
 8200: 
 8201:     def __init__(self, max_iterations: int = DEFAULT_MAX):
 8202:         self._max = max(1, int(max_iterations))
 8203:         self._used = 0
 8204:         self._lock = threading.Lock()
 8205: 
 8206:     def consume(self) -> bool:
 8207:         """Atomically reserve one iteration. Returns False if budget is exhausted."""
 8208:         with self._lock:
 8209:             if self._used >= self._max:
 8210:                 return False
 8211:             self._used += 1
 8212:             return True
 8213: 
 8214:     def remaining(self) -> int:
 8215:         with self._lock:
 8216:             return max(0, self._max - self._used)
 8217: 
 8218:     def used(self) -> int:
 8219:         with self._lock:
 8220:             return self._used
 8221: 
 8222:     def total(self) -> int:
 8223:         return self._max
 8224: 
 8225: 
 8226: # Global exec budget â€” shared across all agents and sub-agents, persisted across kernel restarts
 8227: _GLOBAL_EXEC_CALLS = 0
 8228: _GLOBAL_EXEC_SECONDS = 0.0
 8229: _GLOBAL_EXEC_LOCK = threading.Lock()
 8230: _EXEC_BUDGET_FILE = os.path.join(CONFIG.workspace, ".exec_budget.json")
 8231: 
 8232: 
 8233: def _load_global_exec():
 8234:     """Load persisted exec budget from disk (survives kernel restart)."""
 8235:     global _GLOBAL_EXEC_CALLS, _GLOBAL_EXEC_SECONDS
 8236:     if os.path.exists(_EXEC_BUDGET_FILE):
 8237:         try:
 8238:             with open(_EXEC_BUDGET_FILE) as f:
 8239:                 data = json.load(f)
 8240:             with _GLOBAL_EXEC_LOCK:
 8241:                 _GLOBAL_EXEC_CALLS = data.get("calls", 0)
 8242:                 _GLOBAL_EXEC_SECONDS = data.get("seconds", 0.0)
 8243:         except Exception:
 8244:             pass
 8245: 

### v4 sagemaker_agent.py:8680-8790
 8680:                 output_fn(_msg)
 8681:             except Exception:
 8682:                 pass
 8683:             self._workspace_announced = True
 8684:         # Use provided system prompt or default.
 8685:         # NOTE: Skill injection is handled ONLY by the UI send flow (on_send),
 8686:         # which appends active skill content before calling agent.run().
 8687:         # Do NOT inject skills here â€” it would cause double-injection.
 8688:         # Inject persistent memory into system prompt (only for top-level agent, not sub-agents)
 8689:         _base_prompt = system_prompt or SYSTEM_PROMPT
 8690:         # V4.6.1: Inject workspace info BEFORE the dynamic marker so it's part of
 8691:         # the cached block (doesn't change during session). Helps agent find files
 8692:         # that live in allowed_paths outside the workspace root.
 8693:         _ws_info = _build_workspace_info()
 8694:         _DYN_MARK = "\n\n# === DYNAMIC ==="
 8695:         if _DYN_MARK in _base_prompt:
 8696:             _base_prompt = _base_prompt.replace(_DYN_MARK, f"\n\n{_ws_info}{_DYN_MARK}", 1)
 8697:         else:
 8698:             _base_prompt += f"\n\n{_ws_info}"
 8699:         if self.subagent_depth == 0:
 8700:             _base_prompt += _load_persistent_memory()
 8701:             _base_prompt += _load_project_status()
 8702:             # V4.6 Gap #7: Skill discovery auto-surfacing.
 8703:             # Match user message against skill triggers, suggest relevant skills.
 8704:             # Only for top-level agent (sub-agents don't need discovery).
 8705:             _relevant = SKILLS.discover_relevant(user_message)
 8706:             if _relevant:
 8707:                 _skill_names = ", ".join(_relevant)
 8708:                 # V4.10.0 #24: cap each description at SKILL_LISTING_DESC_CAP chars
 8709:                 # so a single verbose SKILL.md cannot bloat the dynamic prompt section.
 8710:                 def _trim_desc(d: str) -> str:
 8711:                     d = (d or "").strip().replace("\n", " ")
 8712:                     if len(d) > SKILL_LISTING_DESC_CAP:
 8713:                         return d[: SKILL_LISTING_DESC_CAP - 3] + "..."
 8714:                     return d
 8715:                 _descriptions = "; ".join(
 8716:                     f"{s}: {_trim_desc(SKILLS._cache[s].description)}"
 8717:                     for s in _relevant if s in SKILLS._cache
 8718:                 )
 8719:                 _base_prompt += (f"\n\n# Skills Relevant to This Task\n"
 8720:                                  f"Consider using: {_skill_names}\n"
 8721:                                  f"({_descriptions})\n"
 8722:                                  f"Use the skill tool to activate one if it matches your task.")
 8723:         self._system_prompt = _base_prompt
 8724:         self._plan_mode = plan_mode  # Store for tool execution check
 8725: 
 8726:         # Session/user rate limiting
 8727:         if count_towards_limits:
 8728:             now = time.time()
 8729:             while self.user_msg_timestamps and now - self.user_msg_timestamps[0] > 60:
 8730:                 self.user_msg_timestamps.popleft()
 8731:             if len(self.user_msg_timestamps) >= CONFIG.max_user_messages_per_minute:
 8732:                 msg = f"Rate limit exceeded: max {CONFIG.max_user_messages_per_minute} messages/min"
 8733:                 output_fn(msg)
 8734:                 AUDIT.log(self.session_id, "rate_limit", result_summary=msg, user_approved=False)
 8735:                 return msg
 8736:             if self.user_msg_count >= CONFIG.max_user_messages_per_session:
 8737:                 msg = f"Session message limit reached: {CONFIG.max_user_messages_per_session}"
 8738:                 output_fn(msg)
 8739:                 AUDIT.log(self.session_id, "session_limit", result_summary=msg, user_approved=False)
 8740:                 return msg
 8741:             self.user_msg_timestamps.append(now)
 8742:             self.user_msg_count += 1
 8743: 
 8744:         # Ensure proper role alternation for Bedrock (must alternate user/assistant)
 8745:         if self.messages and self.messages[-1].get("role") == "user":
 8746:             # Merge into previous user message (no fake assistant placeholders)
 8747:             prev = self.messages[-1]
 8748:             prev_content = prev.get("content", "")
 8749:             if isinstance(prev_content, str):
 8750:                 prev["content"] = prev_content + "\n\n" + user_message
 8751:             elif isinstance(prev_content, list):
 8752:                 # Previous content is a list (e.g., tool_results) â€” append text block
 8753:                 prev_content.append({"type": "text", "text": user_message})
 8754:             else:
 8755:                 self.messages.append({"role": "user", "content": user_message})
 8756:         else:
 8757:             self.messages.append({"role": "user", "content": user_message})
 8758:         AUDIT.log(self.session_id, "user_message", parameters={"message": user_message[:200]})
 8759: 
 8760:         _effective_max_turns = max_turns_override if max_turns_override is not None else CONFIG.max_turns
 8761:         response = None
 8762:         # V4.10.0 #41a: per-run reactive-compact flag. Once we run reactive compact for
 8763:         # this user message we don't run it again, even across turns â€” if the second
 8764:         # attempt also fails on context, something else is wrong and the user should see it.
 8765:         _reactive_compact_done_this_call = False
 8766:         for turn in range(_effective_max_turns):
 8767:             # Check if stop was requested
 8768:             if self.on_stop_check and self.on_stop_check():
 8769:                 output_fn("[Stopped by user]")
 8770:                 return response.text if response else ""
 8771: 
 8772:             # V4.9.4: Shared iteration budget â€” stops parent + sub-agents from collectively
 8773:             # blowing the cost ceiling. Surfaces a clear "budget exhausted" message so the
 8774:             # user sees WHY work stopped (vs silent truncation).
 8775:             if not self.iteration_budget.consume():
 8776:                 _used, _total = self.iteration_budget.used(), self.iteration_budget.total()
 8777:                 output_fn(
 8778:                     f"[Budget exhausted: {_used}/{_total} iterations used across this agent + "
 8779:                     f"sub-agents. Adjust CONFIG.max_iteration_budget or start a new session.]"
 8780:                 )
 8781:                 return response.text if response else ""
 8782: 
 8783:             # V4.8.0: Budget is display-only metric â€” never stops execution
 8784:             # Show warning but continue. User controls stop via Stop button.
 8785:             if TOKENS.is_over_budget() and not getattr(self, '_budget_warned_this_run', False):
 8786:                 self._budget_warned_this_run = True
 8787:                 output_fn(f"[Cost ${TOKENS.session_cost:.4f} passed budget ${CONFIG.session_cost_limit:.2f} â€” continuing. Adjust Budget $ or click Stop.]")
 8788: 
 8789:             # Check context usage
 8790:             warning = CONTEXT.check_and_warn(self.messages)

### v4 sagemaker_agent.py:8880-9035
 8880:                 # Doc tools: only when documents/charts mentioned
 8881:                 _DOC_TOOLS = {"create_word", "create_excel", "create_chart", "create_pdf", "create_notebook", "notebook_edit", "create_markdown"}
 8882:                 # Note: "word" can false-positive on "password" â€” use " word " with spaces or check tool names
 8883:                 _DOC_KEYWORDS = {"chart", "report", "document", "docx", " word ", "excel", "xlsx", "pdf",
 8884:                                  "notebook", "ipynb", "plot", "graph", "spreadsheet", "visualization",
 8885:                                  "markdown", "readme", "create_word", "create_excel", "create_chart"}
 8886:                 if not any(kw in _recent_text for kw in _DOC_KEYWORDS):
 8887:                     _exclude |= _DOC_TOOLS
 8888:                 # Vision: only when image mentioned
 8889:                 if not any(kw in _recent_text for kw in {"image", "screenshot", "png", "jpg", "jpeg", "gif",
 8890:                                                           "photo", "picture", "look at", "view_image", "img",
 8891:                                                           "diagram", "figure"}):
 8892:                     _exclude.add("view_image")
 8893:                 # Semantic search: only when semantic/deep/meaning search mentioned
 8894:                 if not any(kw in _recent_text for kw in {"semantic", "meaning", "find where", "code search",
 8895:                                                           "semantic_search", "references", "callers",
 8896:                                                           "who calls", "used by"}):
 8897:                     _exclude.add("semantic_search")
 8898:                 # Web fetch: only when URL mentioned
 8899:                 if not any(kw in _recent_text for kw in {"http", "url", "fetch", "web_fetch", "website",
 8900:                                                           "link", "uri", "browse"}):
 8901:                     _exclude.add("web_fetch")
 8902:                 if _exclude:
 8903:                     _active_allowlist = set(TOOLS.keys()) - _exclude
 8904:             # Inject pending images into the conversation for Claude's vision
 8905:             if _PENDING_IMAGES:
 8906:                 _imgs = list(_PENDING_IMAGES)
 8907:                 _PENDING_IMAGES.clear()
 8908:                 # Find last user or tool_result message and append image blocks
 8909:                 for _m in reversed(self.messages):
 8910:                     if _m.get("role") in ("user",):
 8911:                         content = _m.get("content", "")
 8912:                         if isinstance(content, str):
 8913:                             _m["content"] = [{"type": "text", "text": content}] + _imgs
 8914:                         elif isinstance(content, list):
 8915:                             _m["content"] = content + _imgs
 8916:                         break
 8917: 
 8918:             # V4.2 V2-E: Time-based microcompact â€” if gap since last API call exceeds threshold,
 8919:             # Bedrock's server-side prompt cache has likely expired. Proactively clear old tool
 8920:             # results so we don't re-upload a large context the server will re-tokenise anyway.
 8921:             _now = time.time()
 8922:             if (self._last_api_call_time > 0 and
 8923:                     _now - self._last_api_call_time > COLD_CACHE_THRESHOLD_SECONDS):
 8924:                 _gap_min = (_now - self._last_api_call_time) / 60
 8925:                 # V4.3 V3-C: cold-cache path uses KEEP_LAST_N_COLD_CACHE (more aggressive than normal)
 8926:                 # Mirrors runnable's keepRecent=5 â€” since cache expired anyway, clear older results
 8927:                 _mc_msgs, _mc_saved = microcompact(self.messages, keep_n_override=KEEP_LAST_N_COLD_CACHE)
 8928:                 if _mc_saved > MICROCOMPACT_MIN_SAVINGS:
 8929:                     self.messages = _mc_msgs
 8930:                     output_fn(f"[i] Cold cache detected ({_gap_min:.0f}min gap) â€” "
 8931:                               f"proactive microcompact freed ~{_mc_saved:,} tokens")
 8932: 
 8933:             # V4.8.0: Inject critical reminder each turn to prevent drift in long conversations.
 8934:             # This is appended as a system-reminder in the last user message, NOT modifying system prompt
 8935:             # (which would break prompt cache). Mirrors Runnable's per-turn behavioral guardrails.
 8936:             _TURN_REMINDER = (
 8937:                 "\n<system-reminder>\n"
 8938:                 "CRITICAL PER-TURN REMINDERS:\n"
 8939:                 "- Answer in chat. Do NOT create files unless user explicitly requested a file.\n"
 8940:                 "- For data (CSV/Excel): validate row counts, check for duplicates, verify join logic.\n"
 8941:                 "- If task involves 3+ edits, verify before reporting done.\n"
 8942:                 "</system-reminder>"
 8943:             )
 8944:             # Append to last user message if not already present
 8945:             if self.messages and self.messages[-1].get("role") == "user":
 8946:                 _last_content = self.messages[-1].get("content", "")
 8947:                 if isinstance(_last_content, str) and "<system-reminder>" not in _last_content:
 8948:                     self.messages[-1]["content"] = _last_content + _TURN_REMINDER
 8949: 
 8950:             def make_request():
 8951:                 return self.client.chat(
 8952:                     self.messages,
 8953:                     self._system_prompt,
 8954:                     get_tool_definitions(_active_allowlist),
 8955:                     CONFIG.max_tokens,
 8956:                     CONFIG.temperature,
 8957:                     CONFIG.thinking_enabled,
 8958:                     CONFIG.thinking_budget,
 8959:                 )
 8960: 
 8961:             def on_retry(attempt, max_retries, delay, error):
 8962:                 output_fn(f"[Retry {attempt}/{max_retries} in {delay:.1f}s: {error[:50]}...]")
 8963: 
 8964:             try:
 8965:                 # Run LLM call in daemon thread so stop button can interrupt
 8966:                 _llm_result = [None, None]  # [response, error]
 8967:                 def _call_llm():
 8968:                     try:
 8969:                         _llm_result[0] = RETRY.execute(make_request, on_retry)
 8970:                     except Exception as e:
 8971:                         _llm_result[1] = e
 8972: 
 8973:                 llm_thread = threading.Thread(target=_call_llm, daemon=True)
 8974:                 llm_thread.start()
 8975: 
 8976:                 # Poll for completion, checking stop flag every 0.1s for responsive stop
 8977:                 while llm_thread.is_alive():
 8978:                     if self.on_stop_check and self.on_stop_check():
 8979:                         # Track cost if response arrived before stop (Bedrock already billed)
 8980:                         if _llm_result[0] and _llm_result[0].usage:
 8981:                             TOKENS.add(_llm_result[0].usage, model_id=self.client.model_id)
 8982:                         output_fn("[Stopped by user]")
 8983:                         return _llm_result[0].text if _llm_result[0] else ""
 8984:                     llm_thread.join(timeout=0.1)
 8985: 
 8986:                 if _llm_result[1]:
 8987:                     raise _llm_result[1]
 8988:                 response = _llm_result[0]
 8989:             except Exception as e:
 8990:                 # V4.10.0 #41a: Reactive Compact. When Bedrock rejects with
 8991:                 # CONTEXT_OVERFLOW (prompt too long / too many tokens), run
 8992:                 # microcompact + (if needed) full compact, then retry the same
 8993:                 # request once. Capped at 1 reactive retry per run() so we
 8994:                 # cannot infinite-loop. Any other error category surfaces normally.
 8995:                 _category = None
 8996:                 try:
 8997:                     _category, _, _ = ErrorClassifier.classify(e)
 8998:                 except Exception:
 8999:                     pass
 9000:                 if (_category == BedrockErrorCategory.CONTEXT_OVERFLOW
 9001:                         and not _reactive_compact_done_this_call):
 9002:                     _reactive_compact_done_this_call = True
 9003:                     output_fn(
 9004:                         "[Reactive compact: Bedrock rejected the prompt as too long â€” "
 9005:                         "compacting and retrying once]"
 9006:                     )
 9007:                     # Try microcompact first (zero extra LLM calls). If it
 9008:                     # freed enough, retry. Otherwise apply a placeholder-summary
 9009:                     # compaction without burning another LLM call â€” calling
 9010:                     # the same model with the same overflowing context to
 9011:                     # generate a summary would just fail again. Reactive
 9012:                     # path is for FAST recovery, not for quality summarisation.
 9013:                     _mc_msgs, _mc_saved = microcompact(self.messages)
 9014:                     if _mc_saved >= MICROCOMPACT_MIN_SAVINGS:
 9015:                         self.messages = _mc_msgs
 9016:                         output_fn(f"[Reactive: microcompact freed ~{_mc_saved:,} tokens]")
 9017:                     # V4.10.0 #41b: piggyback context_collapse on the
 9018:                         # reactive path too â€” squeezes more space when the
 9019:                         # immediate retry needs every byte it can get.
 9020:                         _cc_msgs, _cc_segments = context_collapse(self.messages)
 9021:                         if _cc_segments > 0:
 9022:                             self.messages = _cc_msgs
 9023:                             output_fn(f"[Reactive: collapsed {_cc_segments} stale research segment(s)]")
 9024:                     else:
 9025:                         output_fn("[Reactive: microcompact insufficient â€” placeholder compaction]")
 9026:                         _summary = (
 9027:                             "Conversation reactively compacted because Bedrock rejected the "
 9028:                             "prompt as too long. Older turns elided; continue from the most "
 9029:                             "recent context."
 9030:                         )
 9031:                         self.messages = COMPACTOR.compact(self.messages, _summary)
 9032:                     # Codex review 2026-04-28: cache-breakage flag and file-read
 9033:                     # state apply to BOTH reactive paths. Microcompact rewrites
 9034:                     # tool-result blocks (still invalidates the messages prefix
 9035:                     # at Bedrock) and may have purged read_file results that the

### v4 sagemaker_agent.py:9040-9220
 9040:                         _FILE_READ_TIMES.clear()
 9041:                         _FILE_PARTIAL_READS.clear()
 9042:                     # Retry the same call exactly once.
 9043:                     try:
 9044:                         _retry_result = [None, None]
 9045:                         def _retry_llm():
 9046:                             try:
 9047:                                 _retry_result[0] = RETRY.execute(make_request, on_retry)
 9048:                             except Exception as _re:
 9049:                                 _retry_result[1] = _re
 9050:                         _retry_thread = threading.Thread(target=_retry_llm, daemon=True)
 9051:                         _retry_thread.start()
 9052:                         while _retry_thread.is_alive():
 9053:                             if self.on_stop_check and self.on_stop_check():
 9054:                                 # Codex review 2026-04-28: parity with the original
 9055:                                 # stop path â€” if the response arrived before stop,
 9056:                                 # Bedrock has already billed us, so account for it.
 9057:                                 if _retry_result[0] and _retry_result[0].usage:
 9058:                                     TOKENS.add(_retry_result[0].usage, model_id=self.client.model_id)
 9059:                                 output_fn("[Stopped during reactive retry]")
 9060:                                 return _retry_result[0].text if _retry_result[0] else ""
 9061:                             _retry_thread.join(timeout=0.1)
 9062:                         if _retry_result[1]:
 9063:                             raise _retry_result[1]
 9064:                         response = _retry_result[0]
 9065:                         output_fn("[Reactive compact: retry succeeded]")
 9066:                     except Exception as _retry_e:
 9067:                         _retry_msg = (
 9068:                             f"[AGENT ERROR] Retry after reactive compact also failed: {_retry_e}"
 9069:                         )
 9070:                         output_fn(_retry_msg)
 9071:                         AUDIT.log(self.session_id, "error", result_summary=str(_retry_e))
 9072:                         return _retry_msg
 9073:                 else:
 9074:                     error_msg = f"[AGENT ERROR] Error calling Bedrock: {e}"
 9075:                     output_fn(error_msg)
 9076:                     AUDIT.log(self.session_id, "error", result_summary=str(e))
 9077:                     return error_msg
 9078: 
 9079:             # Track token usage BEFORE stop check â€” Bedrock already billed us
 9080:             if response and response.usage:
 9081:                 TOKENS.add(response.usage, model_id=self.client.model_id)
 9082:                 if self.on_tokens:
 9083:                     self.on_tokens(TOKENS.get_stats())
 9084:                 self._last_api_call_time = time.time()  # V4.2 V2-E: update cold-cache timestamp
 9085:                 # V4.3 V3-E: Per-turn cache indicator (only for top-level agent to avoid noise from sub-agents)
 9086:                 if self.subagent_depth == 0:
 9087:                     _cache_attempted = CONFIG.enable_prompt_cache and self.client.prompt_cache_supported
 9088:                     _cache_line = TOKENS.format_cache_line(response.usage, cache_attempted=_cache_attempted, client=self.client)
 9089:                     if _cache_line:
 9090:                         output_fn(_cache_line)
 9091:                     # V4.3.2: Cache-breakage detection after compact. If compact happened and
 9092:                     # this turn shows cache_read > 0, cache is restored. If cache_read == 0 and
 9093:                     # we expected caching, the compact invalidated the cache (new prefix).
 9094:                     if self._cache_broken_by_compact:
 9095:                         _cr = response.usage.get("cache_read_input_tokens", 0)
 9096:                         if _cr > 0:
 9097:                             self._cache_broken_by_compact = False  # Cache restored
 9098:                         elif _cache_attempted:
 9099:                             # V4.8.0: Enhanced cache breakage warning with cost impact
 9100:                             output_fn("[âš  Cache miss after compact â€” cost spike expected. Next turn rebuilds cache.]")
 9101:                             self._cache_broken_by_compact = False  # Only warn once
 9102:                 # V4.3.3: Diminishing returns detection (mirrors runnable tokenBudget.ts)
 9103:                 # If 3+ consecutive TEXT-ONLY turns produce <200 output tokens, agent may be stuck.
 9104:                 # Skip turns with tool calls â€” those naturally have short output (the agent is working).
 9105:                 # Only warn once per run() call; only for top-level agent.
 9106:                 if self.subagent_depth == 0 and not self._diminishing_warned:
 9107:                     _has_tool_calls = bool(response.tool_calls)
 9108:                     if not _has_tool_calls:
 9109:                         _out_toks = response.usage.get("output_tokens", 0)
 9110:                         self._turn_output_tokens.append(_out_toks)
 9111:                         if len(self._turn_output_tokens) > 3:
 9112:                             self._turn_output_tokens = self._turn_output_tokens[-3:]
 9113:                         if (len(self._turn_output_tokens) >= 3 and
 9114:                                 all(t < 200 for t in self._turn_output_tokens)):
 9115:                             self._diminishing_warned = True
 9116:                             output_fn("[i] Diminishing returns: 3 consecutive text responses with <200 output tokens. "
 9117:                                       "Agent may be stuck â€” consider stopping and rephrasing.")
 9118:                     else:
 9119:                         # Tool call turns reset the counter â€” agent is actively working
 9120:                         self._turn_output_tokens.clear()
 9121: 
 9122:             # Check stop again after LLM returns (user may have clicked during the call)
 9123:             if self.on_stop_check and self.on_stop_check():
 9124:                 # Persist response to history before returning (prevents context loss)
 9125:                 if response and response.text:
 9126:                     self.messages.append({"role": "assistant", "content": response.text})
 9127:                 output_fn("[Stopped by user]")
 9128:                 return response.text if response else ""
 9129: 
 9130:             # Output thinking (if enabled)
 9131:             if response.thinking and self.on_thinking:
 9132:                 self.on_thinking(response.thinking)
 9133: 
 9134:             # Output text
 9135:             if response.text:
 9136:                 output_fn(response.text)
 9137: 
 9138:             # No tool calls = done â€” persist to conversation history
 9139:             if not response.tool_calls:
 9140:                 if response.text:
 9141:                     self.messages.append({"role": "assistant", "content": response.text})
 9142:                 AUDIT.log(self.session_id, "response", result_summary=response.text[:200] if response.text else "")
 9143:                 return response.text or ""
 9144: 
 9145:             # Doom loop detection: generate a unique key per tool call that distinguishes
 9146:             # genuinely different calls from truly repetitive ones.
 9147:             _skipped_ids = set()
 9148:             for tc in response.tool_calls:
 9149:                 _inp = tc.input
 9150:                 if tc.name == "todo_write":
 9151:                     continue  # Expected to repeat during planning
 9152:                 elif tc.name in ("python_exec",):
 9153:                     target = hashlib.md5(_inp.get("code", "").encode()).hexdigest()[:16]
 9154:                 elif tc.name in ("create_pdf", "create_chart", "create_excel"):
 9155:                     target = hashlib.md5(str(_inp).encode()).hexdigest()[:16]
 9156:                 elif tc.name == "read_file":
 9157:                     # V4.10.10 [Actual Use Issue 7]: include `limit` in the dedup key.
 9158:                     # V4.10.10 round 3 (Codex C2 HIGH): normalize path so abs vs relative
 9159:                     # forms (`./a.py` vs `/full/path/a.py`) hash to the same key.
 9160:                     fp = _inp.get("file_path") or _inp.get("path") or _inp.get("filepath") or ""
 9161:                     try:
 9162:                         fp_norm = os.path.realpath(os.path.abspath(fp)) if fp else ""
 9163:                     except Exception:
 9164:                         fp_norm = fp  # fall back to raw if path is malformed (shouldn't break dedup)
 9165:                     offset = _inp.get("offset") or _inp.get("line_start") or _inp.get("start_line") or 0
 9166:                     limit = _inp.get("limit") or _inp.get("line_count") or 0
 9167:                     target = f"{fp_norm}@{offset}:{limit}"
 9168:                 elif tc.name == "edit_file":
 9169:                     fp = _inp.get("file_path") or _inp.get("path") or _inp.get("filepath") or ""
 9170:                     old_str = _inp.get("old_string") or _inp.get("old_str") or ""
 9171:                     target = fp + "#" + hashlib.md5(old_str.encode()).hexdigest()[:12]
 9172:                 elif tc.name == "grep":
 9173:                     pattern = _inp.get("pattern") or _inp.get("regex") or ""
 9174:                     path = _inp.get("path") or _inp.get("directory") or ""
 9175:                     target = f"{path}:{pattern}"
 9176:                 elif tc.name == "bash":
 9177:                     cmd = _inp.get("command") or ""
 9178:                     target = hashlib.md5(cmd.encode()).hexdigest()[:16]
 9179:                 else:
 9180:                     target = hashlib.md5(str(_inp).encode()).hexdigest()[:16]
 9181:                 key = (tc.name, target)
 9182: 
 9183:                 repeat_count = sum(1 for h in self.tool_history if h == key)
 9184:                 # V4.10.10 [Actual Use Issue 7]: read_file gets a tighter 2-repeat cap
 9185:                 # (real session showed it re-reading 3+ times before the loop breaker fired).
 9186:                 # Other tools keep the standard 3-repeat threshold.
 9187:                 _threshold = 2 if tc.name == "read_file" else 3
 9188:                 if repeat_count >= _threshold:
 9189:                     output_fn(f"[Warning: Repetitive {tc.name} calls detected ({_threshold}+ identical), stopping]")
 9190:                     # Build complete assistant message with tool_use blocks for proper history
 9191:                     assistant_content = []
 9192:                     if response.text:
 9193:                         assistant_content.append({"type": "text", "text": response.text})
 9194:                     for tc2 in response.tool_calls:
 9195:                         assistant_content.append({"type": "tool_use", "id": tc2.id, "name": tc2.name, "input": tc2.input})
 9196:                     self.messages.append({"role": "assistant", "content": assistant_content})
 9197:                     # Add stub tool_results for proper user/assistant alternation
 9198:                     stub_results = [{"type": "tool_result", "tool_use_id": tc2.id,
 9199:                                      "content": "Stopped: repetitive call detected"} for tc2 in response.tool_calls]
 9200:                     self.messages.append({"role": "user", "content": stub_results})
 9201:                     return response.text or ""
 9202: 
 9203:                 # Consecutive duplicate write/edit to same file+content = skip
 9204:                 if tc.name in ("write_file",) and self.tool_history:
 9205:                     last_key = self.tool_history[-1] if self.tool_history else None
 9206:                     if last_key and last_key[0] == tc.name and last_key[1] == target:
 9207:                         output_fn(f"[Skipping duplicate {tc.name} to '{target[:30]}']")
 9208:                         _skipped_ids.add(tc.id)
 9209:                         continue
 9210: 
 9211:                 self.tool_history.append(key)
 9212: 
 9213:             # Build assistant message
 9214:             assistant_content = []
 9215:             if response.text:
 9216:                 assistant_content.append({"type": "text", "text": response.text})
 9217:             for tc in response.tool_calls:
 9218:                 assistant_content.append({"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.input})
 9219:             self.messages.append({"role": "assistant", "content": assistant_content})
 9220: 

codex
I’ve validated most of the loop against v4; I still need the v4 dispatch section immediately after assistant append to compare plan-mode gating and tool-result behavior line-for-line before final verdicts.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\compact_v4\\MAIN\\agent\\sagemaker_agent.py'; "'$lines=Get-Content $f; $s=9220; $e=9365; Write-Output "### v4 sagemaker_agent.py:$s-$e"; for($i=$s;$i -le $e;$i++){"{0,5}: {1}" -f $i,$lines[$i-1]}' in D:\Github\sagemaker-coding-agent
 succeeded in 2931ms:
### v4 sagemaker_agent.py:9220-9365
 9220: 
 9221:             # Parallel sub-agent execution: detect multiple task calls in same response
 9222:             _task_tcs = [tc for tc in response.tool_calls if tc.name == "task" and tc.id not in _skipped_ids]
 9223:             _parallel_results = {}  # tc.id -> result (populated if parallel execution used)
 9224:             if len(_task_tcs) >= 2:
 9225:                 # Pre-check approval for parallel tasks (must happen before execution)
 9226:                 _task_tool_info = TOOLS.get("task")
 9227:                 _task_needs_approval = _task_tool_info[1] if _task_tool_info else False
 9228:                 _approved_tcs = []
 9229:                 if _task_needs_approval and self.on_approval:
 9230:                     for tc in _task_tcs:
 9231:                         approved = self.on_approval("task", tc.input or {})
 9232:                         AUDIT.log(self.session_id, "approval_request", "task", tc.input,
 9233:                                  "Approved" if approved else "Denied", approved)
 9234:                         if approved:
 9235:                             _approved_tcs.append(tc)
 9236:                         else:
 9237:                             # V4.10.10 round 3 (Team A2 HIGH): action-guidance instead of bare 22-char string.
 9238:                             _parallel_results[tc.id] = (
 9239:                                 "Blocked: user denied this specific call. Do NOT retry the identical command. "
 9240:                                 "Either (a) explain to the user why you need it and ask_user for confirmation with "
 9241:                                 "a different scope/argument, or (b) switch to read-only tools (read_file, grep, glob) "
 9242:                                 "to make progress without this call."
 9243:                             )
 9244:                 else:
 9245:                     _approved_tcs = _task_tcs
 9246: 
 9247:                 _serialize_build_tasks = (
 9248:                     CONFIG.enable_worktree and
 9249:                     any(str((tc.input or {}).get("subagent_type", "general")).strip() == "build" for tc in _approved_tcs)
 9250:                 )
 9251:                 if len(_approved_tcs) >= 2 and not _serialize_build_tasks:
 9252:                     _output_lock = threading.Lock()
 9253:                     def _thread_safe_output(text):
 9254:                         with _output_lock:
 9255:                             output_fn(text)
 9256:                     _thread_safe_output(f"[Running {len(_approved_tcs)} sub-agents in parallel...]")
 9257:                     # Save parent's FILE_CACHE context, restore after all threads complete
 9258:                     _parent_ctx = FILE_CACHE.save_and_clear_context()
 9259:                     def _run_parallel_sub(tc_item):
 9260:                         # Each thread gets its own isolated context via thread-local storage
 9261:                         FILE_CACHE.enter_thread_local_context()
 9262:                         args = tc_item.input or {}
 9263:                         try:
 9264:                             result = self._run_task_tool(args, _thread_safe_output, _skip_cache_isolation=True)
 9265:                         except Exception as e:
 9266:                             result = f"[AGENT ERROR] Sub-agent failed: {e}"
 9267:                         finally:
 9268:                             FILE_CACHE.exit_thread_local_context()
 9269:                         return tc_item.id, result
 9270:                     try:
 9271:                         with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(_approved_tcs), 4)) as pool:
 9272:                             future_to_tc = {pool.submit(_run_parallel_sub, tc): tc for tc in _approved_tcs}
 9273:                             for f in concurrent.futures.as_completed(future_to_tc):
 9274:                                 tc_item = future_to_tc[f]
 9275:                                 try:
 9276:                                     tc_id, result = f.result()
 9277:                                     _parallel_results[tc_id] = SECURITY.truncate_output(result)
 9278:                                 except Exception as e:
 9279:                                     _parallel_results[tc_item.id] = f"[AGENT ERROR] Sub-agent failed: {e}"
 9280:                     except Exception as e:
 9281:                         # Pool creation failed â€” tasks without results run sequentially in dispatch
 9282:                         output_fn(f"[Parallel execution failed: {e}. Falling back to sequential.]")
 9283:                     finally:
 9284:                         FILE_CACHE.restore_context(_parent_ctx)
 9285:                 elif len(_approved_tcs) >= 2 and _serialize_build_tasks:
 9286:                     # CONFIG.workspace is process-global, so parallel build agents cannot
 9287:                     # safely point at different worktrees. The dispatch loop below runs
 9288:                     # them sequentially; each build call then gets its own worktree.
 9289:                     output_fn("[Build sub-agents run sequentially to preserve worktree isolation]")
 9290:                 elif len(_approved_tcs) == 1:
 9291:                     # Only 1 approved â€” run sequentially (will be handled in main dispatch loop)
 9292:                     pass
 9293: 
 9294:             # V4.2 V2-I: Parallel read-only tool execution (like runnable's partitionToolCalls)
 9295:             # Batch consecutive read-only tools and run them concurrently for ~40% latency reduction.
 9296:             _RO_TOOLS = frozenset({"read_file", "glob", "grep", "list_dir", "semantic_search", "view_image"})
 9297:             _ro_parallel_results: Dict[str, str] = {}
 9298:             if len(response.tool_calls) >= 2:
 9299:                 _ro_batch: list = []
 9300:                 for _tc in response.tool_calls:
 9301:                     _tn = _tc.name
 9302:                     _is_ro = (_tn in _RO_TOOLS or
 9303:                               (_tn == "bash" and _classify_bash_ro(_tc.input.get("command", ""))))
 9304:                     if _is_ro and _tc.id not in _skipped_ids:
 9305:                         _ro_batch.append(_tc)
 9306:                     else:
 9307:                         # Non-RO tool breaks the batch â€” execute any accumulated RO batch
 9308:                         if len(_ro_batch) >= 2:
 9309:                             try:
 9310:                                 with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(_ro_batch), 6)) as _pool:
 9311:                                     def _exec_ro(_t):
 9312:                                         _f = TOOLS.get(_t.name, [None])[0]
 9313:                                         if _f:
 9314:                                             return _t.id, _f(_t.input)
 9315:                                         return _t.id, f"Unknown tool: {_t.name}"
 9316:                                     for _fut in concurrent.futures.as_completed([_pool.submit(_exec_ro, _t) for _t in _ro_batch]):
 9317:                                         try:
 9318:                                             _tid, _res = _fut.result()
 9319:                                             _ro_parallel_results[_tid] = _res
 9320:                                         except Exception as _e:
 9321:                                             pass
 9322:                             except Exception:
 9323:                                 pass  # Fall back to sequential
 9324:                         _ro_batch = []
 9325:                 # Flush final batch
 9326:                 if len(_ro_batch) >= 2:
 9327:                     try:
 9328:                         with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(_ro_batch), 6)) as _pool:
 9329:                             def _exec_ro_final(_t):
 9330:                                 _f = TOOLS.get(_t.name, [None])[0]
 9331:                                 if _f:
 9332:                                     return _t.id, _f(_t.input)
 9333:                                 return _t.id, f"Unknown tool: {_t.name}"
 9334:                             for _fut in concurrent.futures.as_completed([_pool.submit(_exec_ro_final, _t) for _t in _ro_batch]):
 9335:                                 try:
 9336:                                     _tid, _res = _fut.result()
 9337:                                     _ro_parallel_results[_tid] = _res
 9338:                                 except Exception:
 9339:                                     pass
 9340:                     except Exception:
 9341:                         pass
 9342: 
 9343:             # Execute tools with 5-layer error recovery
 9344:             tool_results = []
 9345:             for tc in response.tool_calls:
 9346:                 # Skip tools flagged as duplicates by doom loop detector
 9347:                 if tc.id in _skipped_ids:
 9348:                     tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "Skipped: duplicate call"})
 9349:                     continue
 9350:                 # Check stop before each tool
 9351:                 if self.on_stop_check and self.on_stop_check():
 9352:                     tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": "Stopped by user"})
 9353:                     continue
 9354:                 # === LAYER 1: Tool Name Repair ===
 9355:                 tool_name = tc.name
 9356:                 tool_info = TOOLS.get(tool_name)
 9357: 
 9358:                 # Try case-insensitive lookup
 9359:                 if not tool_info:
 9360:                     tool_name_lower = tool_name.lower()
 9361:                     for known_name in TOOLS.keys():
 9362:                         if known_name.lower() == tool_name_lower:
 9363:                             tool_name = known_name
 9364:                             tool_info = TOOLS.get(tool_name)
 9365:                             output_fn(f"[Auto-fixed tool name: {tc.name} â†’ {tool_name}]")

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\compact_v4\\MAIN\\agent\\sagemaker_agent.py'; "'$lines=Get-Content $f; $s=9366; $e=9525; Write-Output "### v4 sagemaker_agent.py:$s-$e"; for($i=$s;$i -le $e;$i++){"{0,5}: {1}" -f $i,$lines[$i-1]}' in D:\Github\sagemaker-coding-agent
 succeeded in 2555ms:
### v4 sagemaker_agent.py:9366-9525
 9366:                             break
 9367: 
 9368:                 # Try fuzzy match for common typos
 9369:                 if not tool_info:
 9370:                     similar = [n for n in TOOLS.keys() if n.startswith(tool_name[:4]) or tool_name.startswith(n[:4])]
 9371:                     if similar:
 9372:                         suggestion = similar[0]
 9373:                         tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
 9374:                             "content": f"Unknown tool: '{tc.name}'. Did you mean '{suggestion}'? Available tools: {', '.join(sorted(TOOLS.keys()))}"})
 9375:                         continue
 9376:                     tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
 9377:                         "content": f"Unknown tool: '{tc.name}'. Available tools: {', '.join(sorted(TOOLS.keys()))}"})
 9378:                     continue
 9379: 
 9380:                 func, needs_approval, description, schema = tool_info
 9381: 
 9382:                 # Additional allowlist constraint (used by delegated sub-agents).
 9383:                 if self.tool_allowlist is not None and tool_name not in self.tool_allowlist:
 9384:                     tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
 9385:                         "content": f"Tool blocked by policy in this run: {tool_name}"})
 9386:                     continue
 9387: 
 9388:                 # === PLAN MODE ENFORCEMENT ===
 9389:                 # Allowlist: only permitted tools can run in Plan Mode (blocks MCP/new tools too)
 9390:                 if getattr(self, '_plan_mode', False) and tool_name not in PLAN_MODE_ALLOWED_TOOLS:
 9391:                     output_fn(f"[â›” PLAN MODE: {tool_name} blocked - read-only mode]")
 9392:                     tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
 9393:                         "content": f"â›” PLAN MODE ACTIVE: '{tool_name}' is blocked. In Plan Mode, only read-only tools are allowed: {', '.join(sorted(PLAN_MODE_ALLOWED_TOOLS))}. Turn off Plan Mode to execute write operations."})
 9394:                     continue
 9395: 
 9396:                 # === LAYER 2: Argument Validation & Auto-Fix ===
 9397:                 args = tc.input
 9398:                 required_fields = schema.get("required", []) if schema else []
 9399:                 properties = schema.get("properties", {}) if schema else {}
 9400: 
 9401:                 # Check for missing required fields and try auto-fix
 9402:                 missing = [f for f in required_fields if f not in args or args[f] is None]
 9403:                 if missing:
 9404:                     for field in missing:
 9405:                         # Auto-fix: path â†’ file_path
 9406:                         if field == "file_path" and "path" in args:
 9407:                             args["file_path"] = args.pop("path")
 9408:                             output_fn(f"[Auto-fixed: path â†’ file_path]")
 9409:                         elif field == "file_path" and "filepath" in args:
 9410:                             args["file_path"] = args.pop("filepath")
 9411:                             output_fn(f"[Auto-fixed: filepath â†’ file_path]")
 9412:                         elif field == "content" and "text" in args:
 9413:                             args["content"] = args.pop("text")
 9414:                             output_fn(f"[Auto-fixed: text â†’ content]")
 9415:                         elif field == "pattern" and "query" in args:
 9416:                             args["pattern"] = args.pop("query")
 9417:                             output_fn(f"[Auto-fixed: query â†’ pattern]")
 9418:                         elif field == "command" and "cmd" in args:
 9419:                             args["command"] = args.pop("cmd")
 9420:                             output_fn(f"[Auto-fixed: cmd â†’ command]")
 9421: 
 9422:                     # Re-check after fixes
 9423:                     missing = [f for f in required_fields if f not in args or args[f] is None]
 9424:                     if missing:
 9425:                         tool_results.append({"type": "tool_result", "tool_use_id": tc.id,
 9426:                             "content": f"Missing required arguments for '{tool_name}': {missing}. Expected: {required_fields}. Hint: {description}"})
 9427:                         continue
 9428: 
 9429:                 # === LAYER 3: Type Validation & Auto-Convert ===
 9430:                 for field, value in list(args.items()):
 9431:                     if field in properties:
 9432:                         expected_type = properties[field].get("type")
 9433:                         if expected_type == "integer" and isinstance(value, str) and value.isdigit():
 9434:                             args[field] = int(value)
 9435:                             output_fn(f"[Auto-fixed: converted {field} to integer]")
 9436:                         elif expected_type == "string" and isinstance(value, (int, float)):
 9437:                             args[field] = str(value)
 9438: 
 9439:                 # === LAYER 4: Permission Check ===
 9440:                 # Skip approval for parallel results (already approved before parallel execution)
 9441:                 # V4.1 #11: Also skip approval for provably read-only bash commands
 9442:                 _is_ro_bash = (
 9443:                     tool_name == "bash"
 9444:                     and CONFIG.require_tool_approval
 9445:                     and _classify_bash_ro(args.get("command", ""))
 9446:                 )
 9447:                 if tc.id not in _parallel_results and needs_approval and self.on_approval and not _is_ro_bash:
 9448:                     approved = self.on_approval(tool_name, args)
 9449:                     AUDIT.log(self.session_id, "approval_request", tool_name, args,
 9450:                              "Approved" if approved else "Denied", approved)
 9451:                     if not approved:
 9452:                         # V4.10.10 round 3 (Team A2 HIGH): action-guidance, not bare string.
 9453:                         _denied_msg = (
 9454:                             "Blocked: user denied this specific call. Do NOT retry the identical command. "
 9455:                             "Either (a) explain to the user why you need it and ask_user for confirmation with "
 9456:                             "a different scope/argument, or (b) switch to read-only tools (read_file, grep, glob) "
 9457:                             "to make progress without this call."
 9458:                         )
 9459:                         tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": _denied_msg})
 9460:                         continue
 9461: 
 9462:                 # === LAYER 5: Execute with Error Recovery ===
 9463:                 output_fn(f"[Calling {tool_name}...]")
 9464:                 try:
 9465:                     # Use pre-computed parallel result if available (task or RO batch)
 9466:                     if tc.id in _ro_parallel_results:
 9467:                         result = _ro_parallel_results[tc.id]
 9468:                     elif tc.id in _parallel_results:
 9469:                         result = _parallel_results[tc.id]
 9470:                     elif tool_name == "task":
 9471:                         result = self._run_task_tool(args, output_fn)
 9472:                     elif tool_name == "ask_user":
 9473:                         result = self._run_ask_user_tool(args, output_fn)
 9474:                     else:
 9475:                         if tool_name in {"bash", "python_exec"}:
 9476:                             # Check GLOBAL budget (shared across all agents + sub-agents)
 9477:                             with _GLOBAL_EXEC_LOCK:
 9478:                                 if _GLOBAL_EXEC_CALLS >= CONFIG.max_exec_calls_per_session:
 9479:                                     # V4.10.10 round 3: tool capability matrix at point of failure.
 9480:                                     # Codex review B2 caught the prior "ask user to start a new session"
 9481:                                     # nudged premature escalation â€” reworded to point at read-only tools first.
 9482:                                     result = (
 9483:                                         f"Blocked: bash + python_exec call limit reached ({CONFIG.max_exec_calls_per_session}/session). "
 9484:                                         f"STILL AVAILABLE (no session limit): read_file, grep, glob, edit_file, write_file, "
 9485:                                         f"notebook_edit, task, ask_user, view_image, web_fetch. "
 9486:                                         f"Most diagnostics can finish with these â€” try grep/read_file/edit_file FIRST. "
 9487:                                         f"Only ask the user to start a new session if a strictly-bash-or-python operation "
 9488:                                         f"is the bottleneck."
 9489:                                     )
 9490:                                     tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": result})
 9491:                                     AUDIT.log(self.session_id, "execution_blocked", tool_name, tc.input, result, False)
 9492:                                     continue
 9493:                                 if _GLOBAL_EXEC_SECONDS >= CONFIG.max_exec_seconds_per_session:
 9494:                                     # V4.10.10 round 3: parallel fix for the time-budget branch (Team A2 HIGH â€”
 9495:                                     # the round-2 fix only covered the call-count branch; same misleading
 9496:                                     # terse format remained here.)
 9497:                                     result = (
 9498:                                         f"Blocked: bash + python_exec time budget reached "
 9499:                                         f"({CONFIG.max_exec_seconds_per_session}s/session). "
 9500:                                         f"STILL AVAILABLE (no session limit): read_file, grep, glob, edit_file, write_file, "
 9501:                                         f"notebook_edit, task, ask_user, view_image, web_fetch. "
 9502:                                         f"Continue with these read/edit tools â€” they're not counted by this limit."
 9503:                                     )
 9504:                                     tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": result})
 9505:                                     AUDIT.log(self.session_id, "execution_blocked", tool_name, tc.input, result, False)
 9506:                                     continue
 9507:                             if CONFIG.execution_mode == "docker":
 9508:                                 _ensure_docker_image_ready()
 9509:                         start_ts = time.time()
 9510:                         result = func(args)
 9511:                         elapsed = time.time() - start_ts
 9512:                         if tool_name in {"bash", "python_exec"}:
 9513:                             self.exec_calls += 1
 9514:                             self.exec_seconds += elapsed
 9515:                             # Update global budget (shared across sub-agents)
 9516:                             _update_global_exec(1, elapsed)
 9517:                 except TypeError as e:
 9518:                     result = f"TypeError: {e}. Check argument types. Expected schema: {schema}"
 9519:                 except KeyError as e:
 9520:                     result = f"KeyError: {e}. Required fields: {required_fields}"
 9521:                 except Exception as e:
 9522:                     # V4.10.10 round 3 (Team A2 MEDIUM): include substitution guidance so a generic
 9523:                     # exception doesn't push the agent into giving-up mode. Hermes "failure-message-as-instruction".
 9524:                     result = (
 9525:                         f"Error executing {tool_name}: {e}. "

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$files=@('"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests\\unit\\test_budget.py','D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests\\unit\\test_errors.py','D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests\\unit\\test_retry.py','D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\errors.py','D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\retry.py','D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core\\budget.py'); foreach("'$f in $files){Write-Output "`n### $f"; $i=0; Get-Content $f | % { $i++; "{0,5}: {1}" -f $i,$_}}' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"test_runtime_bedrock_client_re_exports_match|re_exports_match|apply_tool_search_deferral|tool_search_discovered_names|_discovered_tool_names\" D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tests D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\core D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\runtime" in D:\Github\sagemaker-coding-agent
 succeeded in 3349ms:

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_budget.py
    1: """Phase 08 unit tests: core/budget.py â€” IterationBudget.
    2: 
    3: Locks PORT_LOG #016: verbatim port of v4's IterationBudget (Hermes pattern).
    4: """
    5: from __future__ import annotations
    6: 
    7: import os
    8: import sys
    9: import threading
   10: 
   11: _AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   12: if _AGENT_ROOT not in sys.path:
   13:     sys.path.insert(0, _AGENT_ROOT)
   14: 
   15: 
   16: def test_default_max_is_600():
   17:     from core.budget import IterationBudget
   18:     b = IterationBudget()
   19:     assert b.total() == 600
   20: 
   21: 
   22: def test_consume_decrements_remaining():
   23:     from core.budget import IterationBudget
   24:     b = IterationBudget(max_iterations=3)
   25:     assert b.remaining() == 3
   26:     assert b.consume() is True
   27:     assert b.used() == 1
   28:     assert b.remaining() == 2
   29: 
   30: 
   31: def test_consume_returns_false_when_exhausted():
   32:     from core.budget import IterationBudget
   33:     b = IterationBudget(max_iterations=2)
   34:     assert b.consume() is True
   35:     assert b.consume() is True
   36:     assert b.consume() is False
   37:     # Subsequent calls also return False without incrementing
   38:     assert b.consume() is False
   39:     assert b.used() == 2
   40: 
   41: 
   42: def test_min_clamp_to_one():
   43:     """max_iterations <= 0 must clamp to 1 (defensive)."""
   44:     from core.budget import IterationBudget
   45:     b = IterationBudget(max_iterations=0)
   46:     assert b.total() == 1
   47:     assert b.consume() is True
   48:     assert b.consume() is False
   49: 
   50: 
   51: def test_reset_clears_used():
   52:     from core.budget import IterationBudget
   53:     b = IterationBudget(max_iterations=2)
   54:     b.consume()
   55:     b.consume()
   56:     assert b.used() == 2
   57:     b.reset()
   58:     assert b.used() == 0
   59:     assert b.consume() is True
   60: 
   61: 
   62: def test_thread_safety_under_concurrent_consumers():
   63:     """20 threads each calling consume() 100 times against a budget of 1000
   64:     must end with exactly 1000 successful consumes and zero overshoot."""
   65:     from core.budget import IterationBudget
   66:     b = IterationBudget(max_iterations=1000)
   67:     successes: list = []
   68:     lock = threading.Lock()
   69: 
   70:     def worker():
   71:         local = 0
   72:         for _ in range(100):
   73:             if b.consume():
   74:                 local += 1
   75:         with lock:
   76:             successes.append(local)
   77: 
   78:     threads = [threading.Thread(target=worker) for _ in range(20)]
   79:     for t in threads:
   80:         t.start()
   81:     for t in threads:
   82:         t.join()
   83: 
   84:     assert sum(successes) == 1000
   85:     assert b.used() == 1000
   86:     assert b.consume() is False
   87: 
   88: 
   89: def test_shared_budget_across_pseudo_subagents():
   90:     """The Hermes pattern: a parent + N "sub-agents" share one budget instance."""
   91:     from core.budget import IterationBudget
   92:     parent = IterationBudget(max_iterations=10)
   93:     child_a = parent  # sub-agents inherit the same instance
   94:     child_b = parent
   95: 
   96:     for _ in range(4):
   97:         assert parent.consume() is True
   98:     for _ in range(3):
   99:         assert child_a.consume() is True
  100:     for _ in range(3):
  101:         assert child_b.consume() is True
  102:     # All 10 used; next call returns False regardless of caller
  103:     assert parent.consume() is False
  104:     assert child_a.consume() is False
  105:     assert child_b.consume() is False

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_errors.py
    1: """Phase 08 unit tests: core/errors.py â€” BedrockErrorCategory + ErrorClassifier.
    2: 
    3: Locks PORT_LOG #017: extraction from runtime/bedrock_client.py preserves
    4: classification semantics byte-for-byte.
    5: """
    6: from __future__ import annotations
    7: 
    8: import os
    9: import sys
   10: 
   11: _AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   12: if _AGENT_ROOT not in sys.path:
   13:     sys.path.insert(0, _AGENT_ROOT)
   14: 
   15: 
   16: def test_validation_cache_classified():
   17:     from core.errors import BedrockErrorCategory, ErrorClassifier
   18:     exc = Exception("ValidationException: cache_control not supported in this region")
   19:     cat, recovery, _ = ErrorClassifier.classify(exc)
   20:     assert cat == BedrockErrorCategory.VALIDATION_CACHE
   21:     assert recovery == "strip_cache_retry"
   22: 
   23: 
   24: def test_context_overflow_classified():
   25:     from core.errors import BedrockErrorCategory, ErrorClassifier
   26:     exc = Exception("ValidationException: prompt is too long")
   27:     cat, recovery, _ = ErrorClassifier.classify(exc)
   28:     assert cat == BedrockErrorCategory.CONTEXT_OVERFLOW
   29:     assert recovery == "compact_retry"
   30: 
   31: 
   32: def test_validation_other_no_retry():
   33:     from core.errors import BedrockErrorCategory, ErrorClassifier
   34:     exc = Exception("ValidationException: unknown field 'foo'")
   35:     cat, recovery, _ = ErrorClassifier.classify(exc)
   36:     assert cat == BedrockErrorCategory.VALIDATION_OTHER
   37:     assert recovery == "no_retry"
   38: 
   39: 
   40: def test_throttle_classified():
   41:     from core.errors import BedrockErrorCategory, ErrorClassifier
   42:     exc = Exception("ThrottlingException: rate exceeded")
   43:     cat, recovery, _ = ErrorClassifier.classify(exc)
   44:     assert cat == BedrockErrorCategory.THROTTLE
   45:     assert recovery == "backoff"
   46: 
   47: 
   48: def test_service_unavailable_classified():
   49:     from core.errors import BedrockErrorCategory, ErrorClassifier
   50:     exc = Exception("ServiceUnavailable 503")
   51:     cat, recovery, _ = ErrorClassifier.classify(exc)
   52:     assert cat == BedrockErrorCategory.SERVICE_UNAVAILABLE
   53:     assert recovery == "backoff"
   54: 
   55: 
   56: def test_model_not_ready_classified():
   57:     from core.errors import BedrockErrorCategory, ErrorClassifier
   58:     exc = Exception("ModelNotReady: not ready yet")
   59:     cat, recovery, _ = ErrorClassifier.classify(exc)
   60:     assert cat == BedrockErrorCategory.MODEL_NOT_READY
   61:     assert recovery == "backoff"
   62: 
   63: 
   64: def test_access_denied_no_retry():
   65:     from core.errors import BedrockErrorCategory, ErrorClassifier
   66:     exc = Exception("AccessDenied: 403 Forbidden")
   67:     cat, recovery, _ = ErrorClassifier.classify(exc)
   68:     assert cat == BedrockErrorCategory.ACCESS_DENIED
   69:     assert recovery == "no_retry"
   70: 
   71: 
   72: def test_network_error_via_class_name():
   73:     from core.errors import BedrockErrorCategory, ErrorClassifier
   74: 
   75:     class EndpointConnectionError(Exception):
   76:         pass
   77: 
   78:     cat, recovery, _ = ErrorClassifier.classify(EndpointConnectionError("connection failed"))
   79:     assert cat == BedrockErrorCategory.NETWORK
   80:     assert recovery == "backoff"
   81: 
   82: 
   83: def test_unknown_error_no_retry():
   84:     from core.errors import BedrockErrorCategory, ErrorClassifier
   85:     exc = Exception("something completely unexpected")
   86:     cat, recovery, _ = ErrorClassifier.classify(exc)
   87:     assert cat == BedrockErrorCategory.UNKNOWN
   88:     assert recovery == "no_retry"
   89: 
   90: 
   91: def test_debug_msg_truncated_to_200():
   92:     from core.errors import ErrorClassifier
   93:     big = "x" * 500
   94:     exc = Exception(f"ValidationException: {big}")
   95:     _, _, debug = ErrorClassifier.classify(exc)
   96:     assert len(debug) <= 200
   97: 
   98: 
   99: def test_runtime_bedrock_client_re_exports_match():
  100:     """PORT_LOG #017 byte-equivalence: runtime.bedrock_client must re-export
  101:     the exact same classes from core.errors so existing call-sites work."""
  102:     from core.errors import BedrockErrorCategory as CoreCat, ErrorClassifier as CoreCls
  103:     from runtime.bedrock_client import BedrockErrorCategory as RuntimeCat, ErrorClassifier as RuntimeCls
  104:     assert CoreCat is RuntimeCat
  105:     assert CoreCls is RuntimeCls

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_retry.py
    1: """Phase 08 unit tests: core/retry.py â€” RetryPolicy.
    2: 
    3: Locks PORT_LOG #018: jittered exponential backoff with v4 verbatim semantics.
    4: """
    5: from __future__ import annotations
    6: 
    7: import os
    8: import random
    9: import sys
   10: 
   11: _AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   12: if _AGENT_ROOT not in sys.path:
   13:     sys.path.insert(0, _AGENT_ROOT)
   14: 
   15: 
   16: def test_max_retries_is_4():
   17:     from core.retry import RetryPolicy
   18:     assert RetryPolicy.MAX_RETRIES == 4
   19: 
   20: 
   21: def test_should_retry_for_backoff_recovery():
   22:     from core.retry import RetryPolicy
   23:     assert RetryPolicy.should_retry(0, "backoff") is True
   24:     assert RetryPolicy.should_retry(3, "backoff") is True
   25: 
   26: 
   27: def test_should_not_retry_when_attempts_exhausted():
   28:     from core.retry import RetryPolicy
   29:     assert RetryPolicy.should_retry(4, "backoff") is False
   30:     assert RetryPolicy.should_retry(99, "backoff") is False
   31: 
   32: 
   33: def test_should_not_retry_for_non_backoff_recovery():
   34:     from core.retry import RetryPolicy
   35:     assert RetryPolicy.should_retry(0, "no_retry") is False
   36:     assert RetryPolicy.should_retry(0, "strip_cache_retry") is False
   37:     assert RetryPolicy.should_retry(0, "compact_retry") is False
   38: 
   39: 
   40: def test_backoff_seconds_floor_and_ceiling():
   41:     """Sleep curve: ~1s, 2s, 4s, 8s with up-to-30% jitter. Always >= 0.1s."""
   42:     from core.retry import RetryPolicy
   43:     random.seed(42)
   44:     samples = [RetryPolicy.backoff_seconds(0) for _ in range(50)]
   45:     for s in samples:
   46:         assert s >= 0.1
   47:         # base=1.0, jitter +/- 0.30 â†’ [0.7, 1.3]
   48:         assert 0.7 <= s <= 1.3 + 0.0001
   49: 
   50: 
   51: def test_backoff_seconds_doubles_per_attempt():
   52:     from core.retry import RetryPolicy
   53:     random.seed(0)
   54:     base_means = []
   55:     for attempt in range(4):
   56:         random.seed(attempt)
   57:         samples = [RetryPolicy.backoff_seconds(attempt) for _ in range(200)]
   58:         base_means.append(sum(samples) / len(samples))
   59:     # Mean roughly doubles (within jitter): ~1, ~2, ~4, ~8
   60:     for prev, cur in zip(base_means, base_means[1:]):
   61:         assert cur > prev * 1.5, f"expected ~doubling, got {prev:.2f} -> {cur:.2f}"
   62: 
   63: 
   64: def test_runtime_bedrock_client_re_exports_match():
   65:     """Byte-equivalence with Phase-1: runtime.bedrock_client re-exports
   66:     the same RetryPolicy class so existing call-sites continue to work."""
   67:     from core.retry import RetryPolicy as CorePolicy
   68:     from runtime.bedrock_client import RetryPolicy as RuntimePolicy
   69:     assert CorePolicy is RuntimePolicy

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\errors.py
    1: """V5 core/errors.py â€” Bedrock error classifier (Phase 8 extraction).
    2: 
    3: Per ADR-014: extracted verbatim from Phase-1 `runtime/bedrock_client.py`
    4: (which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).
    5: 
    6: PORT_LOG: #017.
    7: 
    8: Why this lives here in Phase 8 (not Phase 1):
    9: The classifier was bundled with `BedrockClient` in Phase 1 to avoid a
   10: circular Phase-1/Phase-8 dependency. Now that core/ exists, the classifier
   11: gets its own module so:
   12:   - QueryEngine can import without pulling boto3 transitively
   13:   - Tests can exercise classification logic without a Bedrock client
   14:   - Future phases can reuse classifier semantics outside Bedrock invocation
   15: 
   16: Behavior is byte-equivalent with Phase-1. `runtime/bedrock_client.py`
   17: re-imports these names for backwards compatibility (no chat() change).
   18: """
   19: from __future__ import annotations
   20: 
   21: 
   22: class BedrockErrorCategory:
   23:     """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy."""
   24:     THROTTLE = "throttle"  # ThrottlingException, rate-limited
   25:     SERVICE_UNAVAILABLE = "service_unavailable"
   26:     MODEL_NOT_READY = "model_not_ready"
   27:     NETWORK = "network"
   28:     VALIDATION_CACHE = "validation_cache"  # cache_control rejected â€” strip and retry once
   29:     VALIDATION_OTHER = "validation_other"
   30:     CONTEXT_OVERFLOW = "context_overflow"  # prompt-too-long
   31:     ACCESS_DENIED = "access_denied"
   32:     UNKNOWN = "unknown"
   33: 
   34: 
   35: class ErrorClassifier:
   36:     """Classifies Bedrock exceptions into a (category, recovery, debug_msg) triple.
   37: 
   38:     Verbatim port of v4's classifier. Recovery values:
   39:       - "strip_cache_retry": cache_control rejected; strip blocks and retry once
   40:       - "compact_retry":     prompt-too-long; caller should compact and retry
   41:       - "backoff":           transient (throttle/503/network); retry with jitter
   42:       - "no_retry":          permanent (validation/access denied); surface to user
   43:     """
   44: 
   45:     @staticmethod
   46:     def classify(exc: Exception):
   47:         msg_lower = str(exc).lower()
   48:         cls_name = type(exc).__name__.lower()
   49: 
   50:         if "validationexception" in msg_lower and (
   51:             "cache_control" in msg_lower
   52:             or "prompt-caching" in msg_lower
   53:             or "cache" in msg_lower
   54:         ):
   55:             return BedrockErrorCategory.VALIDATION_CACHE, "strip_cache_retry", str(exc)[:200]
   56:         if "validationexception" in msg_lower and (
   57:             "prompt is too long" in msg_lower
   58:             or "too many tokens" in msg_lower
   59:             or "input length" in msg_lower
   60:         ):
   61:             return BedrockErrorCategory.CONTEXT_OVERFLOW, "compact_retry", str(exc)[:200]
   62:         if "validationexception" in msg_lower:
   63:             return BedrockErrorCategory.VALIDATION_OTHER, "no_retry", str(exc)[:200]
   64:         if "throttlingexception" in msg_lower or "rate" in msg_lower:
   65:             return BedrockErrorCategory.THROTTLE, "backoff", str(exc)[:200]
   66:         if "serviceunavailable" in msg_lower or "503" in msg_lower:
   67:             return BedrockErrorCategory.SERVICE_UNAVAILABLE, "backoff", str(exc)[:200]
   68:         if "modelnotready" in msg_lower or "not ready" in msg_lower:
   69:             return BedrockErrorCategory.MODEL_NOT_READY, "backoff", str(exc)[:200]
   70:         if "accessdenied" in msg_lower or "403" in msg_lower or "unauthorized" in msg_lower:
   71:             return BedrockErrorCategory.ACCESS_DENIED, "no_retry", str(exc)[:200]
   72:         if (
   73:             "endpointconnectionerror" in cls_name
   74:             or "connecttimeout" in cls_name
   75:             or "readtimeout" in cls_name
   76:             or "connectionerror" in cls_name
   77:         ):
   78:             return BedrockErrorCategory.NETWORK, "backoff", str(exc)[:200]
   79:         return BedrockErrorCategory.UNKNOWN, "no_retry", str(exc)[:200]

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\retry.py
    1: """V5 core/retry.py â€” jittered exponential backoff (Phase 8 extraction).
    2: 
    3: Per ADR-014: extracted verbatim from Phase-1 `runtime/bedrock_client.py`
    4: (which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).
    5: 
    6: PORT_LOG: #018.
    7: 
    8: Sleep curve:
    9:   attempt 0 -> ~1.0s   (0.7-1.3s with jitter)
   10:   attempt 1 -> ~2.0s   (1.4-2.6s)
   11:   attempt 2 -> ~4.0s   (2.8-5.2s)
   12:   attempt 3 -> ~8.0s   (5.6-10.4s)
   13:   attempt 4 -> stops   (MAX_RETRIES reached)
   14: 
   15: MAX_RETRIES=4 means up to 5 total attempts (initial + 4 retries).
   16: Behavior is byte-equivalent with Phase-1. `runtime/bedrock_client.py`
   17: re-imports these names for backwards compatibility.
   18: """
   19: from __future__ import annotations
   20: 
   21: import random
   22: 
   23: 
   24: class RetryPolicy:
   25:     """Jittered exponential backoff (v4 verbatim)."""
   26:     MAX_RETRIES = 4
   27:     BASE_SECONDS = 1.0
   28:     JITTER_FRACTION = 0.30
   29:     BACKOFF_RECOVERY = {"backoff"}
   30: 
   31:     @staticmethod
   32:     def should_retry(attempt: int, recovery: str) -> bool:
   33:         if attempt >= RetryPolicy.MAX_RETRIES:
   34:             return False
   35:         return recovery in RetryPolicy.BACKOFF_RECOVERY
   36: 
   37:     @staticmethod
   38:     def backoff_seconds(attempt: int) -> float:
   39:         base = RetryPolicy.BASE_SECONDS * (2 ** attempt)
   40:         jitter = base * RetryPolicy.JITTER_FRACTION * (2 * random.random() - 1)
   41:         return max(0.1, base + jitter)

### D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\budget.py
    1: """V5 core/budget.py â€” IterationBudget (Hermes pattern via v4).
    2: 
    3: Per ADR-014: verbatim port of v4's IterationBudget at
    4: `compact_v4/MAIN/agent/sagemaker_agent.py:8190`. v4 itself adopted this
    5: from `D:/Github/hermes-agent/run_agent.py:170` in v4.9.4.
    6: 
    7: PORT_LOG: #016.
    8: 
    9: Why this exists (PS Issue #2):
   10: A parent agent could otherwise spawn N sub-agents that each loop
   11: max_turns times, blowing the cost ceiling. Insurance/audit values
   12: predictable cost ceilings per user request. Counter is shared across
   13: parent + sub-agents (the parent creates one budget at the start of
   14: `run()`; sub-agents inherit the same instance).
   15: 
   16: Phase 11 (notebook UX) will wire the budget's `consume() / remaining()
   17: / used() / total()` methods into an ipywidgets progress bar so the
   18: user can SEE the budget burning down â€” addressing PS Issue #2's
   19: "budget is invisible until exhausted" complaint.
   20: """
   21: from __future__ import annotations
   22: 
   23: import threading
   24: 
   25: 
   26: class IterationBudget:
   27:     """Thread-safe counter shared across a parent agent and its spawned sub-agents.
   28: 
   29:     A parent agent creates one budget at the start of run(); sub-agents inherit
   30:     the same instance. Each LLM turn (success or failure) increments the counter.
   31:     When `consume()` returns False, the agent surfaces a "budget exhausted"
   32:     message and stops cleanly, preserving partial work.
   33:     """
   34: 
   35:     DEFAULT_MAX = 600  # v4.10.10 in-place: 90 -> 600 (Hermes default 90 too tight for SageMaker dev)
   36: 
   37:     def __init__(self, max_iterations: int = DEFAULT_MAX):
   38:         self._max = max(1, int(max_iterations))
   39:         self._used = 0
   40:         self._lock = threading.Lock()
   41: 
   42:     def consume(self) -> bool:
   43:         """Atomically reserve one iteration. Returns False if budget is exhausted."""
   44:         with self._lock:
   45:             if self._used >= self._max:
   46:                 return False
   47:             self._used += 1
   48:             return True
   49: 
   50:     def remaining(self) -> int:
   51:         with self._lock:
   52:             return max(0, self._max - self._used)
   53: 
   54:     def used(self) -> int:
   55:         with self._lock:
   56:             return self._used
   57: 
   58:     def total(self) -> int:
   59:         return self._max
   60: 
   61:     def reset(self) -> None:
   62:         """Reset counter to 0. Tests + manual /reset only â€” not a normal flow."""
   63:         with self._lock:
   64:             self._used = 0

 succeeded in 4100ms:
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:13:    * `apply_tool_search_deferral(tools, enabled=True)` per turn.
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:14:    * `tool_search_discovered_names()` extraction from tool_search results.
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:161:        self._discovered_tool_names: Set[str] = set()
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:198:        from tools.registry import apply_tool_search_deferral, find_tool_by_name
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:199:        from tools.tool_search import tool_search_discovered_names
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:223:            visible_tools, deferred_names = apply_tool_search_deferral(
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:226:            if self._discovered_tool_names:
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:228:                discovered = {n for n in self._discovered_tool_names if n in deferred_names}
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:331:                        discovered = tool_search_discovered_names(text)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:333:                            self._discovered_tool_names.update(discovered)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:456:    from tools.registry import apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:458:    visible_tools, _deferred = apply_tool_search_deferral(tools, enabled=True)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\integration\test_query_engine.py:166:    extracted via `tool_search_discovered_names()` and the named tool's full
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\__init__.py:10:Phase 7 contract: query_engine MUST call `apply_tool_search_deferral(enabled=True)`
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\__init__.py:11:per turn AND extract discovered tool names via `tool_search_discovered_names()`
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_errors.py:99:def test_runtime_bedrock_client_re_exports_match():
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_retry.py:64:def test_runtime_bedrock_client_re_exports_match():
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:5:apply_tool_search_deferral stub + plan-mode subset).
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:338:def test_apply_tool_search_deferral_disabled_returns_unchanged():
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:342:    from tools import build_tool, register, get_tools, apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:346:    visible, deferred_names = apply_tool_search_deferral(tools, enabled=False)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:351:def test_apply_tool_search_deferral_enabled_without_tool_search_safe():
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:355:    from tools import build_tool, register, get_tools, apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:360:    visible, deferred_names = apply_tool_search_deferral(tools, enabled=True)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:365:def test_apply_tool_search_deferral_enabled_with_tool_search_partitions():
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:369:    from tools import build_tool, register, get_tools, apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:374:    visible, deferred_names = apply_tool_search_deferral(tools, enabled=True)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:420:        ("apply_tool_search_deferral_disabled",              test_apply_tool_search_deferral_disabled_returns_unchanged),
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:421:        ("apply_tool_search_deferral_enabled_without_tool_search", test_apply_tool_search_deferral_enabled_without_tool_search_safe),
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_registry.py:422:        ("apply_tool_search_deferral_enabled_partitions",    test_apply_tool_search_deferral_enabled_with_tool_search_partitions),
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:1:"""Phase 07 unit tests: tools/tool_search.py + apply_tool_search_deferral.
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:74:# apply_tool_search_deferral — integration with registry
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:79:    from tools import all_registered, apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:81:    visible, deferred_names = apply_tool_search_deferral(tools, enabled=False)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:89:    from tools import all_registered, apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:91:    visible, deferred_names = apply_tool_search_deferral(tools, enabled=True)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:113:    from tools import all_registered, apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:115:    visible, deferred_names = apply_tool_search_deferral(tools, enabled=True)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:129:    from tools import all_registered, apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:131:    visible, deferred_names = apply_tool_search_deferral(tools_without_search, enabled=True)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:269:    from tools import all_registered, apply_tool_search_deferral
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:274:    visible, ts = apply_tool_search_deferral(full, enabled=True)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:371:def test_tool_search_discovered_names_extraction(workspace_safe_environ):
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:372:    """Phase-8 contract lock: tool_search_discovered_names parses the hidden
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:376:    from tools.tool_search import tool_search_discovered_names
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:379:    discovered = tool_search_discovered_names(out)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:384:def test_tool_search_discovered_names_empty_on_no_matches(workspace_safe_environ):
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:386:    from tools.tool_search import tool_search_discovered_names
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:389:    discovered = tool_search_discovered_names(out)
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:393:def test_tool_search_discovered_names_handles_missing_marker():
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:395:    from tools.tool_search import tool_search_discovered_names
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:396:    assert tool_search_discovered_names("just some unrelated text") == []
D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\unit\test_tool_search.py:397:    assert tool_search_discovered_names("") == []

codex
I found a potential contract-risk area around how deferred names are promoted; I’m now checking the registry’s exact deferral implementation to confirm whether promotion semantics can leak non-registered names or duplicate payload entries.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent\\tools\\registry.py'; "'$lines=Get-Content $f; $matches=Select-String -Path $f -Pattern '"'def apply_tool_search_deferral|def find_tool_by_name|always_load|deferred' ; foreach("'$m in $matches){$ln=$m.LineNumber; $s=[Math]::Max(1,$ln-35); $e=[Math]::Min($lines.Length,$ln+70); Write-Output "`n### registry.py:$s-$e around line $ln"; for($i=$s;$i -le $e;$i++){"{0,5}: {1}" -f $i,$lines[$i-1]}}' in D:\Github\sagemaker-coding-agent
 succeeded in 2917ms:

### registry.py:1-93 around line 23
    1: """V5 Tool registry â€” replaces v4's monolithic `TOOLS = {...}` 4-tuple dict.
    2: 
    3: Per ADR-007 (`ToolDef` Protocol) and ADR-008 (registry shape):
    4: - Each tool exposes a small `ToolDef` object with named attributes (no
    5:   more (callable, requires_approval, description, schema) positional
    6:   4-tuple from v4).
    7: - The registry is a process-global list (`_REGISTRY`) populated by
    8:   `register(tool)` calls at module import time. Phase 3-5 tools each
    9:   ship as their own file (per ADR-001 file-per-tool layout) and call
   10:   `register()` at module load.
   11: - `get_tools(plan_mode, deny_rules)` filters by enabled flag, deny rules,
   12:   and the plan-mode read-only allowlist (v4 PLAN_MODE_ALLOWED_TOOLS parity
   13:   at compact_v4/MAIN/agent/sagemaker_agent.py:6905).
   14: - `assemble_tool_pool()` ports Runnable's cache-stable alphabetical
   15:   ordering invariant: built-ins are sorted alphabetically and form a
   16:   contiguous prefix; MCP tools are sorted alphabetically and form a
   17:   contiguous suffix. The server-side prompt cache breakpoint sits after
   18:   the last built-in tool, so any interleaving would invalidate the cache
   19:   for every downstream tool. (See `gg-claude-code-runnable/src/tools.ts`
   20:   `assembleToolPool` comment block on cache invariants.)
   21: - `apply_tool_search_deferral(tools, enabled=False)` is a Phase-2 STUB.
   22:   When `enabled=False` it returns `(tools, None)` unchanged. Full
   23:   deferred-loading lands in Phase 7 with `tools/tool_search.py`. The
   24:   stub is here so Phase 8's `core/query_engine.py` can wire to it
   25:   without churn later.
   26: 
   27: Source: gg-claude-code-runnable/src/Tool.ts (Tool interface + buildTool)
   28:         gg-claude-code-runnable/src/tools.ts (getAllBaseTools, getTools,
   29:         filterToolsByDenyRules, assembleToolPool, toolMatchesName,
   30:         findToolByName, getMergedTools).
   31: """
   32: from __future__ import annotations
   33: 
   34: from dataclasses import dataclass
   35: from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Set, Tuple, runtime_checkable
   36: 
   37: 
   38: # ============================================================
   39: # Plan-mode allowlist (v4 verbatim parity)
   40: # ============================================================
   41: 
   42: # Verbatim from compact_v4/MAIN/agent/sagemaker_agent.py:6905 â€” when plan
   43: # mode is on, only these tool names are permitted to execute. Mutating
   44: # tools (write_file, edit_file, bash, python_exec, notebook_edit, task)
   45: # are filtered out.
   46: PLAN_MODE_ALLOWED_TOOLS: frozenset = frozenset({
   47:     "read_file", "glob", "grep", "list_dir", "semantic_search",
   48:     "todo_write", "todo_read", "view_image", "skill", "web_fetch", "ask_user",
   49: })
   50: 
   51: 
   52: # ============================================================
   53: # ToolDef Protocol (per ADR-007)
   54: # ============================================================
   55: 
   56: @runtime_checkable
   57: class ToolDef(Protocol):
   58:     """Minimal tool contract â€” Python Protocol port of Runnable's `Tool`.
   59: 
   60:     Runnable parity columns shown in attribute docstrings. Methods that
   61:     Runnable exposes for React/Ink rendering (renderToolUseMessage etc.)
   62:     are intentionally OMITTED â€” v5 ships in `.ipynb` and renders via
   63:     ipywidgets in `ui/chat_ui.py` (Phase 11). See ADR-007 for the full
   64:     omission list and justification (constraint=.ipynb).
   65:     """
   66:     name: str                                # Runnable: name
   67:     aliases: Tuple[str, ...]                 # Runnable: aliases
   68:     description : str                        # Runnable: prompt() result. (Note: extra space before the colon is intentional â€” a global git-commit hook on this repo flags new agent-style desc-fields if they don't start with the CSO format. The Bedrock API field name has to stay verbatim, so the type-hint colon is spaced out to dodge the hook regex without changing the field name. PEP 526 accepts this; PEP 8 E203 noqa.)
   69:     input_schema: Dict[str, Any]             # Runnable: inputSchema (JSON-Schema dict)
   70:     search_hint: str                         # Runnable: searchHint
   71:     should_defer: bool                       # Runnable: shouldDefer
   72:     always_load: bool                        # Runnable: alwaysLoad
   73:     is_read_only: bool                       # Runnable: isReadOnly()
   74:     is_destructive: bool                     # Runnable: isDestructive()
   75:     is_concurrency_safe: bool                # Runnable: isConcurrencySafe()
   76:     requires_approval: bool                  # v4-native; Runnable splits into checkPermissions()
   77:     enabled: bool                            # Runnable: isEnabled()
   78:     max_result_size_chars: int               # Runnable: maxResultSizeChars
   79: 
   80:     def execute(self, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
   81:         """Run the tool. Runnable parity: `call(args, context, ...)`. Returns
   82:         any value; the caller (Phase 8 query_engine) maps to a tool_result block."""
   83:         ...
   84: 
   85: 
   86: # ============================================================
   87: # Concrete record + build_tool factory (per ADR-007 buildTool parity)
   88: # ============================================================
   89: 
   90: @dataclass
   91: class ToolRecord:
   92:     """Concrete `ToolDef` implementation. Equivalent to Runnable's
   93:     `BuiltTool<D>` returned by `buildTool(def)`. Defaults match Runnable's

### registry.py:37-142 around line 72
   37: 
   38: # ============================================================
   39: # Plan-mode allowlist (v4 verbatim parity)
   40: # ============================================================
   41: 
   42: # Verbatim from compact_v4/MAIN/agent/sagemaker_agent.py:6905 â€” when plan
   43: # mode is on, only these tool names are permitted to execute. Mutating
   44: # tools (write_file, edit_file, bash, python_exec, notebook_edit, task)
   45: # are filtered out.
   46: PLAN_MODE_ALLOWED_TOOLS: frozenset = frozenset({
   47:     "read_file", "glob", "grep", "list_dir", "semantic_search",
   48:     "todo_write", "todo_read", "view_image", "skill", "web_fetch", "ask_user",
   49: })
   50: 
   51: 
   52: # ============================================================
   53: # ToolDef Protocol (per ADR-007)
   54: # ============================================================
   55: 
   56: @runtime_checkable
   57: class ToolDef(Protocol):
   58:     """Minimal tool contract â€” Python Protocol port of Runnable's `Tool`.
   59: 
   60:     Runnable parity columns shown in attribute docstrings. Methods that
   61:     Runnable exposes for React/Ink rendering (renderToolUseMessage etc.)
   62:     are intentionally OMITTED â€” v5 ships in `.ipynb` and renders via
   63:     ipywidgets in `ui/chat_ui.py` (Phase 11). See ADR-007 for the full
   64:     omission list and justification (constraint=.ipynb).
   65:     """
   66:     name: str                                # Runnable: name
   67:     aliases: Tuple[str, ...]                 # Runnable: aliases
   68:     description : str                        # Runnable: prompt() result. (Note: extra space before the colon is intentional â€” a global git-commit hook on this repo flags new agent-style desc-fields if they don't start with the CSO format. The Bedrock API field name has to stay verbatim, so the type-hint colon is spaced out to dodge the hook regex without changing the field name. PEP 526 accepts this; PEP 8 E203 noqa.)
   69:     input_schema: Dict[str, Any]             # Runnable: inputSchema (JSON-Schema dict)
   70:     search_hint: str                         # Runnable: searchHint
   71:     should_defer: bool                       # Runnable: shouldDefer
   72:     always_load: bool                        # Runnable: alwaysLoad
   73:     is_read_only: bool                       # Runnable: isReadOnly()
   74:     is_destructive: bool                     # Runnable: isDestructive()
   75:     is_concurrency_safe: bool                # Runnable: isConcurrencySafe()
   76:     requires_approval: bool                  # v4-native; Runnable splits into checkPermissions()
   77:     enabled: bool                            # Runnable: isEnabled()
   78:     max_result_size_chars: int               # Runnable: maxResultSizeChars
   79: 
   80:     def execute(self, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
   81:         """Run the tool. Runnable parity: `call(args, context, ...)`. Returns
   82:         any value; the caller (Phase 8 query_engine) maps to a tool_result block."""
   83:         ...
   84: 
   85: 
   86: # ============================================================
   87: # Concrete record + build_tool factory (per ADR-007 buildTool parity)
   88: # ============================================================
   89: 
   90: @dataclass
   91: class ToolRecord:
   92:     """Concrete `ToolDef` implementation. Equivalent to Runnable's
   93:     `BuiltTool<D>` returned by `buildTool(def)`. Defaults match Runnable's
   94:     `TOOL_DEFAULTS` (fail-closed: assume not concurrency-safe, assume
   95:     writes, assume not destructive)."""
   96:     name: str
   97:     description : str  # spaced colon: see ToolDef Protocol comment above re: CSO hook regex.
   98:     input_schema: Dict[str, Any]
   99:     execute: Callable[..., Any]
  100: 
  101:     aliases: Tuple[str, ...] = ()
  102:     search_hint: str = ""
  103:     should_defer: bool = False
  104:     always_load: bool = False
  105: 
  106:     # Defaults are fail-closed for safety, mirroring Runnable's TOOL_DEFAULTS:
  107:     # - isConcurrencySafe â†’ false (assume not safe)
  108:     # - isReadOnly        â†’ false (assume writes)
  109:     # - isDestructive     â†’ false
  110:     # - isEnabled         â†’ true
  111:     is_read_only: bool = False
  112:     is_destructive: bool = False
  113:     is_concurrency_safe: bool = False
  114:     requires_approval: bool = False  # v4 split: defaults False, mutating tools set True
  115:     enabled: bool = True
  116:     max_result_size_chars: int = 50_000  # matches v4 max_output_chars + Runnable DEFAULT_MAX_RESULT_SIZE_CHARS
  117: 
  118: 
  119: def build_tool(
  120:     name: str,
  121:     description : str,  # spaced colon: see ToolDef Protocol comment above re: CSO hook regex.
  122:     input_schema: Dict[str, Any],
  123:     execute: Callable[..., Any],
  124:     **overrides: Any,
  125: ) -> ToolRecord:
  126:     """Construct a `ToolRecord` filling in safe defaults for omitted fields.
  127: 
  128:     Mirrors Runnable's `buildTool(def)` (`Tool.ts:783`). Tool authors only
  129:     have to specify what differs from defaults â€” most read-only tools just
  130:     need `is_read_only=True`; most mutating tools need `requires_approval=True`.
  131:     """
  132:     return ToolRecord(
  133:         name=name,
  134:         description=description,
  135:         input_schema=input_schema,
  136:         execute=execute,
  137:         **overrides,
  138:     )
  139: 
  140: 
  141: # ============================================================
  142: # Process-global registry

### registry.py:69-174 around line 104
   69:     input_schema: Dict[str, Any]             # Runnable: inputSchema (JSON-Schema dict)
   70:     search_hint: str                         # Runnable: searchHint
   71:     should_defer: bool                       # Runnable: shouldDefer
   72:     always_load: bool                        # Runnable: alwaysLoad
   73:     is_read_only: bool                       # Runnable: isReadOnly()
   74:     is_destructive: bool                     # Runnable: isDestructive()
   75:     is_concurrency_safe: bool                # Runnable: isConcurrencySafe()
   76:     requires_approval: bool                  # v4-native; Runnable splits into checkPermissions()
   77:     enabled: bool                            # Runnable: isEnabled()
   78:     max_result_size_chars: int               # Runnable: maxResultSizeChars
   79: 
   80:     def execute(self, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
   81:         """Run the tool. Runnable parity: `call(args, context, ...)`. Returns
   82:         any value; the caller (Phase 8 query_engine) maps to a tool_result block."""
   83:         ...
   84: 
   85: 
   86: # ============================================================
   87: # Concrete record + build_tool factory (per ADR-007 buildTool parity)
   88: # ============================================================
   89: 
   90: @dataclass
   91: class ToolRecord:
   92:     """Concrete `ToolDef` implementation. Equivalent to Runnable's
   93:     `BuiltTool<D>` returned by `buildTool(def)`. Defaults match Runnable's
   94:     `TOOL_DEFAULTS` (fail-closed: assume not concurrency-safe, assume
   95:     writes, assume not destructive)."""
   96:     name: str
   97:     description : str  # spaced colon: see ToolDef Protocol comment above re: CSO hook regex.
   98:     input_schema: Dict[str, Any]
   99:     execute: Callable[..., Any]
  100: 
  101:     aliases: Tuple[str, ...] = ()
  102:     search_hint: str = ""
  103:     should_defer: bool = False
  104:     always_load: bool = False
  105: 
  106:     # Defaults are fail-closed for safety, mirroring Runnable's TOOL_DEFAULTS:
  107:     # - isConcurrencySafe â†’ false (assume not safe)
  108:     # - isReadOnly        â†’ false (assume writes)
  109:     # - isDestructive     â†’ false
  110:     # - isEnabled         â†’ true
  111:     is_read_only: bool = False
  112:     is_destructive: bool = False
  113:     is_concurrency_safe: bool = False
  114:     requires_approval: bool = False  # v4 split: defaults False, mutating tools set True
  115:     enabled: bool = True
  116:     max_result_size_chars: int = 50_000  # matches v4 max_output_chars + Runnable DEFAULT_MAX_RESULT_SIZE_CHARS
  117: 
  118: 
  119: def build_tool(
  120:     name: str,
  121:     description : str,  # spaced colon: see ToolDef Protocol comment above re: CSO hook regex.
  122:     input_schema: Dict[str, Any],
  123:     execute: Callable[..., Any],
  124:     **overrides: Any,
  125: ) -> ToolRecord:
  126:     """Construct a `ToolRecord` filling in safe defaults for omitted fields.
  127: 
  128:     Mirrors Runnable's `buildTool(def)` (`Tool.ts:783`). Tool authors only
  129:     have to specify what differs from defaults â€” most read-only tools just
  130:     need `is_read_only=True`; most mutating tools need `requires_approval=True`.
  131:     """
  132:     return ToolRecord(
  133:         name=name,
  134:         description=description,
  135:         input_schema=input_schema,
  136:         execute=execute,
  137:         **overrides,
  138:     )
  139: 
  140: 
  141: # ============================================================
  142: # Process-global registry
  143: # ============================================================
  144: 
  145: _REGISTRY: List[ToolRecord] = []
  146: 
  147: 
  148: def register(tool: ToolRecord) -> ToolRecord:
  149:     """Add a tool to the process-global registry. Returns the tool so
  150:     that module-level usage like `MY_TOOL = register(build_tool(...))`
  151:     is one expression."""
  152:     # Defensive: forbid duplicate names â€” silent overrides masked bugs in v4
  153:     # when two skills both registered "verify". Caller must explicitly
  154:     # `unregister(name)` first if they intend to replace.
  155:     for existing in _REGISTRY:
  156:         if existing.name == tool.name:
  157:             raise ValueError(
  158:                 f"Tool '{tool.name}' already registered. "
  159:                 f"Call unregister('{tool.name}') first if replacement is intended."
  160:             )
  161:     _REGISTRY.append(tool)
  162:     return tool
  163: 
  164: 
  165: def unregister(name: str) -> bool:
  166:     """Remove a tool by name. Returns True if a tool was removed."""
  167:     for i, tool in enumerate(_REGISTRY):
  168:         if tool.name == name:
  169:             del _REGISTRY[i]
  170:             return True
  171:     return False
  172: 
  173: 
  174: def all_registered() -> List[ToolRecord]:

### registry.py:153-258 around line 188
  153:     # when two skills both registered "verify". Caller must explicitly
  154:     # `unregister(name)` first if they intend to replace.
  155:     for existing in _REGISTRY:
  156:         if existing.name == tool.name:
  157:             raise ValueError(
  158:                 f"Tool '{tool.name}' already registered. "
  159:                 f"Call unregister('{tool.name}') first if replacement is intended."
  160:             )
  161:     _REGISTRY.append(tool)
  162:     return tool
  163: 
  164: 
  165: def unregister(name: str) -> bool:
  166:     """Remove a tool by name. Returns True if a tool was removed."""
  167:     for i, tool in enumerate(_REGISTRY):
  168:         if tool.name == name:
  169:             del _REGISTRY[i]
  170:             return True
  171:     return False
  172: 
  173: 
  174: def all_registered() -> List[ToolRecord]:
  175:     """Return a snapshot copy of the current registry. Useful for tests."""
  176:     return list(_REGISTRY)
  177: 
  178: 
  179: # ============================================================
  180: # Lookup helpers (Runnable parity: toolMatchesName / findToolByName)
  181: # ============================================================
  182: 
  183: def tool_matches_name(tool: ToolRecord, name: str) -> bool:
  184:     """Runnable parity: `Tool.ts:toolMatchesName`."""
  185:     return tool.name == name or name in tool.aliases
  186: 
  187: 
  188: def find_tool_by_name(tools: Iterable[ToolRecord], name: str) -> Optional[ToolRecord]:
  189:     """Runnable parity: `Tool.ts:findToolByName`."""
  190:     for t in tools:
  191:         if tool_matches_name(t, name):
  192:             return t
  193:     return None
  194: 
  195: 
  196: # ============================================================
  197: # Public selection: get_tools + assemble_tool_pool
  198: # ============================================================
  199: 
  200: def _filter_by_deny_rules(
  201:     tools: Iterable[ToolRecord],
  202:     deny_rules: Optional[Set[str]],
  203: ) -> List[ToolRecord]:
  204:     """Runnable parity: `tools.ts:filterToolsByDenyRules` â†’
  205:     `permissions.ts:getDenyRuleForTool`. A tool is denied if any of these match:
  206:       - exact name match
  207:       - exact alias match
  208:       - MCP server-level prefix: a tool named `mcp__server__toolName` is
  209:         denied if the rule equals `mcp__server` (server blanket-deny)
  210:       - MCP server wildcard: rule `mcp__server__*` denies every tool with that
  211:         server prefix (Runnable supports both forms; we mirror both)
  212:     Non-MCP tool names ignore the MCP rules; MCP tool names also honor exact-
  213:     name and exact-alias rules. This matches Runnable's semantics where the
  214:     same matcher is reused at request time and at deny-filter time, so a
  215:     server-prefix rule strips ALL of that server's tools from the model's
  216:     view before the prompt is built."""
  217:     if not deny_rules:
  218:         return list(tools)
  219:     return [t for t in tools if not _is_denied(t, deny_rules)]
  220: 
  221: 
  222: def _is_denied(tool: ToolRecord, deny_rules: Set[str]) -> bool:
  223:     if tool.name in deny_rules:
  224:         return True
  225:     if any(a in deny_rules for a in tool.aliases):
  226:         return True
  227:     # MCP server-prefix match: a tool named `mcp__server__name` is denied by
  228:     # `mcp__server` (blanket-deny that whole server) or `mcp__server__*`
  229:     # (wildcard form). The first segment after `mcp__` is the server.
  230:     if tool.name.startswith("mcp__"):
  231:         parts = tool.name.split("__")
  232:         # parts = ["mcp", "<server>", "<toolName>"]; need at least 3 to have a server.
  233:         if len(parts) >= 3:
  234:             server = parts[1]
  235:             server_prefix = f"mcp__{server}"
  236:             if server_prefix in deny_rules or f"{server_prefix}__*" in deny_rules:
  237:                 return True
  238:     return False
  239: 
  240: 
  241: def get_tools(
  242:     plan_mode: bool = False,
  243:     deny_rules: Optional[Set[str]] = None,
  244: ) -> List[ToolRecord]:
  245:     """Return the active tool list for the current call.
  246: 
  247:     Filtering order (matches Runnable's `getTools(permissionContext)` at
  248:     `tools.ts:271` adapted for the simpler v5 .ipynb permission model):
  249:     1. enabled flag       (Runnable: isEnabled())
  250:     2. deny rules         (Runnable: filterToolsByDenyRules)
  251:     3. plan-mode subset   (v4: PLAN_MODE_ALLOWED_TOOLS)
  252: 
  253:     Per ADR-008, v5 collapses Runnable's complex DeepImmutable
  254:     `permissionContext` into the simple `(plan_mode, deny_rules)` tuple
  255:     because v5's .ipynb has a single approval source (constraint=.ipynb).
  256:     """
  257:     enabled = [t for t in _REGISTRY if t.enabled]
  258:     after_deny = _filter_by_deny_rules(enabled, deny_rules)

### registry.py:275-380 around line 310
  275:     tool â€” interleaved sorting would invalidate the cache for every
  276:     downstream tool.
  277: 
  278:     Plan mode applies to MCP tools too (v4 parity at
  279:     `compact_v4/MAIN/agent/sagemaker_agent.py:9390`): plan-mode is a hard
  280:     allowlist of tool names, and MCP/new tools are NOT in that allowlist,
  281:     so they get filtered out alongside non-allowlisted built-ins.
  282:     """
  283:     built_in = get_tools(plan_mode=plan_mode, deny_rules=deny_rules)
  284:     mcp_filtered = _filter_by_deny_rules(mcp_tools or [], deny_rules)
  285:     if plan_mode:
  286:         # Plan-mode is a hard allowlist by name â€” MCP tools are not in
  287:         # PLAN_MODE_ALLOWED_TOOLS by default, so they're stripped from
  288:         # the prompt entirely. v4 enforced this at the dispatch layer
  289:         # (sagemaker_agent.py:9390); v5 enforces at registry assembly so
  290:         # plan-mode users never see the disallowed tool schema in the
  291:         # initial prompt.
  292:         mcp_filtered = [t for t in mcp_filtered if t.name in PLAN_MODE_ALLOWED_TOOLS]
  293: 
  294:     built_in_sorted = sorted(built_in, key=lambda t: t.name)
  295:     mcp_sorted = sorted(mcp_filtered, key=lambda t: t.name)
  296: 
  297:     # Deduplicate by name; built-ins win on conflict (matches Runnable's
  298:     # `uniqBy([...builtIn, ...mcp], 'name')` semantics with insertion order).
  299:     seen: Set[str] = set()
  300:     out: List[ToolRecord] = []
  301:     for t in built_in_sorted + mcp_sorted:
  302:         if t.name in seen:
  303:             continue
  304:         seen.add(t.name)
  305:         out.append(t)
  306:     return out
  307: 
  308: 
  309: # ============================================================
  310: # Deferred-loading hook (Phase 2 STUB; Phase 7 fills in)
  311: # ============================================================
  312: 
  313: def apply_tool_search_deferral(
  314:     tools: List[ToolRecord],
  315:     enabled: bool = False,
  316: ) -> Tuple[List[ToolRecord], List[str]]:
  317:     """Runnable parity (Phase 7 ADR-013): defer `should_defer=True` tools behind
  318:     tool_search.
  319: 
  320:     Codex Phase-07 review fix #1 (BLOCKER): the v1 signature returned
  321:     `(visible_tools, tool_search_tool_or_None)` and tool_search appeared in
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""

### registry.py:278-381 around line 313
  278:     Plan mode applies to MCP tools too (v4 parity at
  279:     `compact_v4/MAIN/agent/sagemaker_agent.py:9390`): plan-mode is a hard
  280:     allowlist of tool names, and MCP/new tools are NOT in that allowlist,
  281:     so they get filtered out alongside non-allowlisted built-ins.
  282:     """
  283:     built_in = get_tools(plan_mode=plan_mode, deny_rules=deny_rules)
  284:     mcp_filtered = _filter_by_deny_rules(mcp_tools or [], deny_rules)
  285:     if plan_mode:
  286:         # Plan-mode is a hard allowlist by name â€” MCP tools are not in
  287:         # PLAN_MODE_ALLOWED_TOOLS by default, so they're stripped from
  288:         # the prompt entirely. v4 enforced this at the dispatch layer
  289:         # (sagemaker_agent.py:9390); v5 enforces at registry assembly so
  290:         # plan-mode users never see the disallowed tool schema in the
  291:         # initial prompt.
  292:         mcp_filtered = [t for t in mcp_filtered if t.name in PLAN_MODE_ALLOWED_TOOLS]
  293: 
  294:     built_in_sorted = sorted(built_in, key=lambda t: t.name)
  295:     mcp_sorted = sorted(mcp_filtered, key=lambda t: t.name)
  296: 
  297:     # Deduplicate by name; built-ins win on conflict (matches Runnable's
  298:     # `uniqBy([...builtIn, ...mcp], 'name')` semantics with insertion order).
  299:     seen: Set[str] = set()
  300:     out: List[ToolRecord] = []
  301:     for t in built_in_sorted + mcp_sorted:
  302:         if t.name in seen:
  303:             continue
  304:         seen.add(t.name)
  305:         out.append(t)
  306:     return out
  307: 
  308: 
  309: # ============================================================
  310: # Deferred-loading hook (Phase 2 STUB; Phase 7 fills in)
  311: # ============================================================
  312: 
  313: def apply_tool_search_deferral(
  314:     tools: List[ToolRecord],
  315:     enabled: bool = False,
  316: ) -> Tuple[List[ToolRecord], List[str]]:
  317:     """Runnable parity (Phase 7 ADR-013): defer `should_defer=True` tools behind
  318:     tool_search.
  319: 
  320:     Codex Phase-07 review fix #1 (BLOCKER): the v1 signature returned
  321:     `(visible_tools, tool_search_tool_or_None)` and tool_search appeared in
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:289-381 around line 324
  289:         # (sagemaker_agent.py:9390); v5 enforces at registry assembly so
  290:         # plan-mode users never see the disallowed tool schema in the
  291:         # initial prompt.
  292:         mcp_filtered = [t for t in mcp_filtered if t.name in PLAN_MODE_ALLOWED_TOOLS]
  293: 
  294:     built_in_sorted = sorted(built_in, key=lambda t: t.name)
  295:     mcp_sorted = sorted(mcp_filtered, key=lambda t: t.name)
  296: 
  297:     # Deduplicate by name; built-ins win on conflict (matches Runnable's
  298:     # `uniqBy([...builtIn, ...mcp], 'name')` semantics with insertion order).
  299:     seen: Set[str] = set()
  300:     out: List[ToolRecord] = []
  301:     for t in built_in_sorted + mcp_sorted:
  302:         if t.name in seen:
  303:             continue
  304:         seen.add(t.name)
  305:         out.append(t)
  306:     return out
  307: 
  308: 
  309: # ============================================================
  310: # Deferred-loading hook (Phase 2 STUB; Phase 7 fills in)
  311: # ============================================================
  312: 
  313: def apply_tool_search_deferral(
  314:     tools: List[ToolRecord],
  315:     enabled: bool = False,
  316: ) -> Tuple[List[ToolRecord], List[str]]:
  317:     """Runnable parity (Phase 7 ADR-013): defer `should_defer=True` tools behind
  318:     tool_search.
  319: 
  320:     Codex Phase-07 review fix #1 (BLOCKER): the v1 signature returned
  321:     `(visible_tools, tool_search_tool_or_None)` and tool_search appeared in
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:292-381 around line 327
  292:         mcp_filtered = [t for t in mcp_filtered if t.name in PLAN_MODE_ALLOWED_TOOLS]
  293: 
  294:     built_in_sorted = sorted(built_in, key=lambda t: t.name)
  295:     mcp_sorted = sorted(mcp_filtered, key=lambda t: t.name)
  296: 
  297:     # Deduplicate by name; built-ins win on conflict (matches Runnable's
  298:     # `uniqBy([...builtIn, ...mcp], 'name')` semantics with insertion order).
  299:     seen: Set[str] = set()
  300:     out: List[ToolRecord] = []
  301:     for t in built_in_sorted + mcp_sorted:
  302:         if t.name in seen:
  303:             continue
  304:         seen.add(t.name)
  305:         out.append(t)
  306:     return out
  307: 
  308: 
  309: # ============================================================
  310: # Deferred-loading hook (Phase 2 STUB; Phase 7 fills in)
  311: # ============================================================
  312: 
  313: def apply_tool_search_deferral(
  314:     tools: List[ToolRecord],
  315:     enabled: bool = False,
  316: ) -> Tuple[List[ToolRecord], List[str]]:
  317:     """Runnable parity (Phase 7 ADR-013): defer `should_defer=True` tools behind
  318:     tool_search.
  319: 
  320:     Codex Phase-07 review fix #1 (BLOCKER): the v1 signature returned
  321:     `(visible_tools, tool_search_tool_or_None)` and tool_search appeared in
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:293-381 around line 328
  293: 
  294:     built_in_sorted = sorted(built_in, key=lambda t: t.name)
  295:     mcp_sorted = sorted(mcp_filtered, key=lambda t: t.name)
  296: 
  297:     # Deduplicate by name; built-ins win on conflict (matches Runnable's
  298:     # `uniqBy([...builtIn, ...mcp], 'name')` semantics with insertion order).
  299:     seen: Set[str] = set()
  300:     out: List[ToolRecord] = []
  301:     for t in built_in_sorted + mcp_sorted:
  302:         if t.name in seen:
  303:             continue
  304:         seen.add(t.name)
  305:         out.append(t)
  306:     return out
  307: 
  308: 
  309: # ============================================================
  310: # Deferred-loading hook (Phase 2 STUB; Phase 7 fills in)
  311: # ============================================================
  312: 
  313: def apply_tool_search_deferral(
  314:     tools: List[ToolRecord],
  315:     enabled: bool = False,
  316: ) -> Tuple[List[ToolRecord], List[str]]:
  317:     """Runnable parity (Phase 7 ADR-013): defer `should_defer=True` tools behind
  318:     tool_search.
  319: 
  320:     Codex Phase-07 review fix #1 (BLOCKER): the v1 signature returned
  321:     `(visible_tools, tool_search_tool_or_None)` and tool_search appeared in
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:297-381 around line 332
  297:     # Deduplicate by name; built-ins win on conflict (matches Runnable's
  298:     # `uniqBy([...builtIn, ...mcp], 'name')` semantics with insertion order).
  299:     seen: Set[str] = set()
  300:     out: List[ToolRecord] = []
  301:     for t in built_in_sorted + mcp_sorted:
  302:         if t.name in seen:
  303:             continue
  304:         seen.add(t.name)
  305:         out.append(t)
  306:     return out
  307: 
  308: 
  309: # ============================================================
  310: # Deferred-loading hook (Phase 2 STUB; Phase 7 fills in)
  311: # ============================================================
  312: 
  313: def apply_tool_search_deferral(
  314:     tools: List[ToolRecord],
  315:     enabled: bool = False,
  316: ) -> Tuple[List[ToolRecord], List[str]]:
  317:     """Runnable parity (Phase 7 ADR-013): defer `should_defer=True` tools behind
  318:     tool_search.
  319: 
  320:     Codex Phase-07 review fix #1 (BLOCKER): the v1 signature returned
  321:     `(visible_tools, tool_search_tool_or_None)` and tool_search appeared in
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:307-381 around line 342
  307: 
  308: 
  309: # ============================================================
  310: # Deferred-loading hook (Phase 2 STUB; Phase 7 fills in)
  311: # ============================================================
  312: 
  313: def apply_tool_search_deferral(
  314:     tools: List[ToolRecord],
  315:     enabled: bool = False,
  316: ) -> Tuple[List[ToolRecord], List[str]]:
  317:     """Runnable parity (Phase 7 ADR-013): defer `should_defer=True` tools behind
  318:     tool_search.
  319: 
  320:     Codex Phase-07 review fix #1 (BLOCKER): the v1 signature returned
  321:     `(visible_tools, tool_search_tool_or_None)` and tool_search appeared in
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:320-381 around line 355
  320:     Codex Phase-07 review fix #1 (BLOCKER): the v1 signature returned
  321:     `(visible_tools, tool_search_tool_or_None)` and tool_search appeared in
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:322-381 around line 357
  322:     BOTH `visible` AND as the second return â€” Phase 8 callers appending the
  323:     second one would send duplicate schemas. The new signature returns
  324:     `(visible_tools, deferred_tool_names)`:
  325: 
  326:     - `visible_tools`: the per-turn tools list to send to Bedrock as `tools=`.
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:327-381 around line 362
  327:                       INCLUDES tool_search (always_load=True). NO duplication.
  328:     - `deferred_tool_names`: list of tool names that were filtered out. Phase 8
  329:                       query_engine emits these as a `<system-reminder>` block
  330:                       so the model knows what's available via tool_search.
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:331-381 around line 366
  331: 
  332:     A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
  333:     name != "tool_search".
  334: 
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

### registry.py:335-381 around line 370
  335:     When `enabled=False`, returns `(tools, [])` â€” backwards compatible with the
  336:     Phase-2 stub for Phases 2-6 (no deferral active).
  337:     """
  338:     if not enabled:
  339:         return list(tools), []
  340: 
  341:     # Find tool_search in the input list. If absent, deferral cannot
  342:     # work (model has no way to load deferred tools), so return full list
  343:     # unchanged with a logged warning.
  344:     has_tool_search = any(t.name == "tool_search" for t in tools)
  345:     if not has_tool_search:
  346:         import logging
  347:         logging.warning(
  348:             "[apply_tool_search_deferral] tool_search not in input list -- "
  349:             "deferral disabled for this call. Ensure tools.bootstrap_built_ins() "
  350:             "ran before calling."
  351:         )
  352:         return list(tools), []
  353: 
  354:     # Partition: visible (always-loaded + non-deferrable + tool_search itself)
  355:     # vs deferred names.
  356:     visible: List[ToolRecord] = []
  357:     deferred_names: List[str] = []
  358:     for t in tools:
  359:         if t.name == "tool_search":
  360:             visible.append(t)  # tool_search ALWAYS in visible (single source)
  361:             continue
  362:         if t.always_load:
  363:             visible.append(t)
  364:             continue
  365:         if t.should_defer:
  366:             deferred_names.append(t.name)
  367:             continue  # schema NOT in the per-turn prompt; name announced via system-reminder
  368:         visible.append(t)
  369: 
  370:     return visible, deferred_names
  371: 
  372: 
  373: # ============================================================
  374: # Test/dev hook
  375: # ============================================================
  376: 
  377: def _reset_registry_for_tests() -> None:
  378:     """Clear the process-global registry. ONLY used by unit tests that
  379:     want a clean slate. Production code must never call this â€” tools
  380:     register themselves at import time and stay registered."""
  381:     _REGISTRY.clear()

codex
I’ve confirmed the v5 registry behavior; next I’m checking Runnable’s `QueryEngine.ts` for the exact semantics of discovered-tool persistence and reminder injection to determine whether v5 drift is justified or not.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\_archive\\compare_code\\gg-claude-code-runnable\\src\\QueryEngine.ts'; rg -n \"discovered|tool_search|system-reminder|plan mode|isReadOnly|partitionToolCalls|messages|end_turn|stop_reason|defer|shouldDefer|alwaysLoad\" "'$f' in D:\Github\sagemaker-coding-agent
 succeeded in 2777ms:
2:import type { ContentBlockParam } from '@anthropic-ai/sdk/resources/messages.mjs'
62:import { countToolCalls, SYNTHETIC_MESSAGES } from './utils/messages.js'
94:} from './utils/messages/mappers.js'
98:} from './utils/messages/systemInit.js'
172:  ) => { messages: Message[]; executed: boolean } | undefined
181: * turn within the same conversation. State (messages, file cache, usage, etc.)
192:  // Turn-scoped skill discovery tracking (feeds was_discovered on
197:  private discoveredSkillNames = new Set<string>()
238:    this.discoveredSkillNames.clear()
336:      messages: this.mutableMessages,
373:      discoveredSkillNames: this.discoveredSkillNames,
411:      messages: messagesFromUserInput,
422:        messages: this.mutableMessages,
424:      messages: this.mutableMessages,
430:    // Push new messages, including user input and any attachments
431:    this.mutableMessages.push(...messagesFromUserInput)
434:    const messages = [...this.mutableMessages]
450:    if (persistSession && messagesFromUserInput.length > 0) {
451:      const transcriptPromise = recordTranscript(messages)
465:    // Filter messages that should be acknowledged after transcript
466:    const replayableMessages = messagesFromUserInput.filter(
469:          !msg.isMeta && // Skip synthetic caveat messages
471:          messageSelector().selectableUserMessagesFilter(msg)) || // Skip non-user-authored messages (task notifications, etc.)
474:    const messagesToAck = replayUserMessages ? replayableMessages : []
490:    // Recreate after processing the prompt to pick up updated messages and
493:      messages,
521:      discoveredSkillNames: this.discoveredSkillNames,
558:      // Use messagesFromUserInput (not replayableMessages) for command output
560:      for (const msg of messagesFromUserInput) {
609:        await recordTranscript(messages)
624:        num_turns: messages.length - 1,
626:        stop_reason: null,
642:      messagesFromUserInput
663:    // Track the last stop_reason from assistant messages
676:      messages,
687:      // Record assistant, user, and compact boundary messages
694:        // messages up through the preservedSegment tail. Attachments and
716:        messages.push(message)
718:          // Fire-and-forget for assistant messages. claude.ts yields one
720:          // one's message.usage/stop_reason on message_delta — relying on
728:            void recordTranscript(messages)
730:            await recordTranscript(messages)
734:        // Acknowledge initial user messages after first transcript recording
735:        if (!hasAcknowledgedInitialMessages && messagesToAck.length > 0) {
737:          for (const msgToAck of messagesToAck) {
759:          // Tombstone messages are control signals for removing messages, skip them
762:          // Capture stop_reason if already set (synthetic messages). For
765:          if (message.message.stop_reason != null) {
766:            lastStopReason = message.message.stop_reason
774:          // as already-recorded. Without this, deferred progress interleaves
779:            messages.push(message)
780:            void recordTranscript(messages)
802:            // Capture stop_reason from message_delta. The assistant message
803:            // is yielded at content_block_stop with stop_reason=null; the
805:            // handler). Without this, result.stop_reason is always null.
806:            if (message.event.delta.stop_reason != null) {
807:              lastStopReason = message.event.delta.stop_reason
833:            messages.push(message)
834:            void recordTranscript(messages)
858:              stop_reason: lastStopReason,
895:          // Don't yield stream request start messages
898:          // Snip boundary: replay on our store to remove zombie messages and
912:              this.mutableMessages.push(...snipResult.messages)
917:          // Yield compact boundary messages to SDK
922:            // Release pre-compaction messages for GC. The boundary was just
925:            // post-boundary messages are needed going forward.
930:            const localBoundaryIdx = messages.length - 1
932:              messages.splice(0, localBoundaryIdx)
956:          // Don't yield other system messages in headless mode
960:          // Yield tool use summary messages to SDK
988:          stop_reason: lastStopReason,
1004:      // Check if structured output retry limit exceeded (only on user messages)
1031:            stop_reason: lastStopReason,
1051:    // Stop hooks yield progress/attachment messages AFTER the assistant
1053:    // those to `messages` inline, last(messages) can be a progress/attachment
1058:    const result = messages.findLast(
1090:        stop_reason: lastStopReason,
1103:        // tool_result, and stop_reason isn't end_turn, that's why this fired.
1112:            `[ede_diagnostic] result_type=${edeResultType} last_content_type=${edeLastContentType} stop_reason=${lastStopReason}`,
1143:      stop_reason: lastStopReason,

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$f='"'D:\\Github\\sagemaker-coding-agent\\_archive\\compare_code\\gg-claude-code-runnable\\src\\QueryEngine.ts'; "'$lines=Get-Content $f; $ranges=@(@(180,260),@(340,390),@(500,550)); foreach($r in $ranges){$s=$r[0];$e=$r[1]; Write-Output "`n### QueryEngine.ts:$s-$e"; for($i=$s;$i -le $e;$i++){"{0,5}: {1}" -f $i,$lines[$i-1]}}' in D:\Github\sagemaker-coding-agent
 succeeded in 3833ms:

### QueryEngine.ts:180-260
  180:  * One QueryEngine per conversation. Each submitMessage() call starts a new
  181:  * turn within the same conversation. State (messages, file cache, usage, etc.)
  182:  * persists across turns.
  183:  */
  184: export class QueryEngine {
  185:   private config: QueryEngineConfig
  186:   private mutableMessages: Message[]
  187:   private abortController: AbortController
  188:   private permissionDenials: SDKPermissionDenial[]
  189:   private totalUsage: NonNullableUsage
  190:   private hasHandledOrphanedPermission = false
  191:   private readFileState: FileStateCache
  192:   // Turn-scoped skill discovery tracking (feeds was_discovered on
  193:   // tengu_skill_tool_invocation). Must persist across the two
  194:   // processUserInputContext rebuilds inside submitMessage, but is cleared
  195:   // at the start of each submitMessage to avoid unbounded growth across
  196:   // many turns in SDK mode.
  197:   private discoveredSkillNames = new Set<string>()
  198:   private loadedNestedMemoryPaths = new Set<string>()
  199: 
  200:   constructor(config: QueryEngineConfig) {
  201:     this.config = config
  202:     this.mutableMessages = config.initialMessages ?? []
  203:     this.abortController = config.abortController ?? createAbortController()
  204:     this.permissionDenials = []
  205:     this.readFileState = config.readFileCache
  206:     this.totalUsage = EMPTY_USAGE
  207:   }
  208: 
  209:   async *submitMessage(
  210:     prompt: string | ContentBlockParam[],
  211:     options?: { uuid?: string; isMeta?: boolean },
  212:   ): AsyncGenerator<SDKMessage, void, unknown> {
  213:     const {
  214:       cwd,
  215:       commands,
  216:       tools,
  217:       mcpClients,
  218:       verbose = false,
  219:       thinkingConfig,
  220:       maxTurns,
  221:       maxBudgetUsd,
  222:       taskBudget,
  223:       canUseTool,
  224:       customSystemPrompt,
  225:       appendSystemPrompt,
  226:       userSpecifiedModel,
  227:       fallbackModel,
  228:       jsonSchema,
  229:       getAppState,
  230:       setAppState,
  231:       replayUserMessages = false,
  232:       includePartialMessages = false,
  233:       agents = [],
  234:       setSDKStatus,
  235:       orphanedPermission,
  236:     } = this.config
  237: 
  238:     this.discoveredSkillNames.clear()
  239:     setCwd(cwd)
  240:     const persistSession = !isSessionPersistenceDisabled()
  241:     const startTime = Date.now()
  242: 
  243:     // Wrap canUseTool to track permission denials
  244:     const wrappedCanUseTool: CanUseToolFn = async (
  245:       tool,
  246:       input,
  247:       toolUseContext,
  248:       assistantMessage,
  249:       toolUseID,
  250:       forceDecision,
  251:     ) => {
  252:       const result = await canUseTool(
  253:         tool,
  254:         input,
  255:         toolUseContext,
  256:         assistantMessage,
  257:         toolUseID,
  258:         forceDecision,
  259:       )
  260: 

### QueryEngine.ts:340-390
  340:       // rest of the query loop (push at :389, snapshot at :392) sees
  341:       // the result.  The second processUserInputContext below (after
  342:       // slash-command processing) keeps the no-op â€” nothing else calls
  343:       // setMessages past that point.
  344:       setMessages: fn => {
  345:         this.mutableMessages = fn(this.mutableMessages)
  346:       },
  347:       onChangeAPIKey: () => {},
  348:       handleElicitation: this.config.handleElicitation,
  349:       options: {
  350:         commands,
  351:         debug: false, // we use stdout, so don't want to clobber it
  352:         tools,
  353:         verbose,
  354:         mainLoopModel: initialMainLoopModel,
  355:         thinkingConfig: initialThinkingConfig,
  356:         mcpClients,
  357:         mcpResources: {},
  358:         ideInstallationStatus: null,
  359:         isNonInteractiveSession: true,
  360:         customSystemPrompt,
  361:         appendSystemPrompt,
  362:         agentDefinitions: { activeAgents: agents, allAgents: [] },
  363:         theme: resolveThemeSetting(getGlobalConfig().theme),
  364:         maxBudgetUsd,
  365:       },
  366:       getAppState,
  367:       setAppState,
  368:       abortController: this.abortController,
  369:       readFileState: this.readFileState,
  370:       nestedMemoryAttachmentTriggers: new Set<string>(),
  371:       loadedNestedMemoryPaths: this.loadedNestedMemoryPaths,
  372:       dynamicSkillDirTriggers: new Set<string>(),
  373:       discoveredSkillNames: this.discoveredSkillNames,
  374:       setInProgressToolUseIDs: () => {},
  375:       setResponseLength: () => {},
  376:       updateFileHistoryState: (
  377:         updater: (prev: FileHistoryState) => FileHistoryState,
  378:       ) => {
  379:         setAppState(prev => {
  380:           const updated = updater(prev.fileHistory)
  381:           if (updated === prev.fileHistory) return prev
  382:           return { ...prev, fileHistory: updated }
  383:         })
  384:       },
  385:       updateAttributionState: (
  386:         updater: (prev: AttributionState) => AttributionState,
  387:       ) => {
  388:         setAppState(prev => {
  389:           const updated = updater(prev.attribution)
  390:           if (updated === prev.attribution) return prev

### QueryEngine.ts:500-550
  500:         tools,
  501:         verbose,
  502:         mainLoopModel,
  503:         thinkingConfig: initialThinkingConfig,
  504:         mcpClients,
  505:         mcpResources: {},
  506:         ideInstallationStatus: null,
  507:         isNonInteractiveSession: true,
  508:         customSystemPrompt,
  509:         appendSystemPrompt,
  510:         theme: resolveThemeSetting(getGlobalConfig().theme),
  511:         agentDefinitions: { activeAgents: agents, allAgents: [] },
  512:         maxBudgetUsd,
  513:       },
  514:       getAppState,
  515:       setAppState,
  516:       abortController: this.abortController,
  517:       readFileState: this.readFileState,
  518:       nestedMemoryAttachmentTriggers: new Set<string>(),
  519:       loadedNestedMemoryPaths: this.loadedNestedMemoryPaths,
  520:       dynamicSkillDirTriggers: new Set<string>(),
  521:       discoveredSkillNames: this.discoveredSkillNames,
  522:       setInProgressToolUseIDs: () => {},
  523:       setResponseLength: () => {},
  524:       updateFileHistoryState: processUserInputContext.updateFileHistoryState,
  525:       updateAttributionState: processUserInputContext.updateAttributionState,
  526:       setSDKStatus,
  527:     }
  528: 
  529:     headlessProfilerCheckpoint('before_skills_plugins')
  530:     // Cache-only: headless/SDK/CCR startup must not block on network for
  531:     // ref-tracked plugins. CCR populates the cache via CLAUDE_CODE_SYNC_PLUGIN_INSTALL
  532:     // (headlessPluginInstall) or CLAUDE_CODE_PLUGIN_SEED_DIR before this runs;
  533:     // SDK callers that need fresh source can call /reload-plugins.
  534:     const [skills, { enabled: enabledPlugins }] = await Promise.all([
  535:       getSlashCommandToolSkills(getCwd()),
  536:       loadAllPluginsCacheOnly(),
  537:     ])
  538:     headlessProfilerCheckpoint('after_skills_plugins')
  539: 
  540:     yield buildSystemInitMessage({
  541:       tools,
  542:       mcpClients,
  543:       model: mainLoopModel,
  544:       permissionMode: initialAppState.toolPermissionContext
  545:         .mode as PermissionMode, // TODO: avoid the cast
  546:       commands,
  547:       agents,
  548:       skills,
  549:       plugins: enabledPlugins,
  550:       fastMode: initialAppState.fastMode,

web search: 
web search: 
codex
AXIS A VERDICT: CHANGES_REQUESTED

Findings:
- [high] [query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:161) / [query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:167) — `_discovered_tool_names` is never cleared at `run()` start, so deferred-tool discoveries leak across separate user runs. This violates your Phase 7 wiring contract expectation (“persist within run, reset between runs”) and can silently widen tool payload on later runs. Fix: clear `self._discovered_tool_names` at top of `run()`.
- [medium] [query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:302) — plan-mode gate is `if plan_mode and not tool.is_read_only and not tool.always_load`, which allows any mutating tool marked `always_load=True` to bypass plan mode. v4 enforced explicit allowlist (`PLAN_MODE_ALLOWED_TOOLS`) at dispatch ([compact_v4 sagemaker_agent.py](/D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py:9390)). Fix: enforce allowlist-by-name (or explicit non-bypass invariant) instead of `always_load` exemption.
- [medium][test gap] [test_query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_query_engine.py:161) — no test covers cross-run reset of discovered tools; current leak would pass all tests. Add a test: run #1 does `tool_search select:view_image`; run #2 without `tool_search` must not include `view_image` in turn-1 payload.
- [low][test gap] [test_query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_query_engine.py:392) — plan-mode test only covers `edit_file` (non-`always_load`). It would not catch the `always_load` bypass class. Add a synthetic mutating `always_load=True` tool and assert block in plan mode.

AXIS B VERDICT

PATTERN 016 (`core/budget.py`): FAITHFUL
- Source intent: shared thread-safe iteration ceiling across parent/sub-agents to bound cost.
- v5 implementation: class body and semantics match v4 `IterationBudget` (same locking and counters; plus benign `reset()` helper).
- Constraint forcing adaptation: none.
- Drift risk if any: minimal (`reset()` is additive, test/manual only).
- Required change to reach FAITHFUL: none.

PATTERN 017 (`core/errors.py`): FAITHFUL
- Source intent: classify Bedrock invoke failures into recovery categories.
- v5 implementation: extraction is behaviorally identical; runtime re-exports preserve class identity.
- Constraint forcing adaptation: none.
- Drift risk if any: low.
- Required change to reach FAITHFUL: none.

PATTERN 018 (`core/retry.py`): FAITHFUL-WITH-JUSTIFIED-ADAPTATION
- Source intent: retry transient failures with jittered exponential backoff.
- v5 implementation: keeps simple backoff policy used in v4 Bedrock path; excludes direct-API features (e.g., `Retry-After` handling in Runnable `withRetry.ts`).
- Constraint forcing adaptation: Bedrock.
- Drift risk if any: lower sophistication under some transient patterns, but aligned with Bedrock client error surface.
- Required change to reach FAITHFUL: none required under Bedrock-only constraint.

PATTERN 019 (`core/query_engine.py`): FAITHFUL-WITH-JUSTIFIED-ADAPTATION
- Source intent: orchestrate turn loop, tool execution, message flow, and deferred tool loading.
- v5 implementation: captures core loop, tool_use/tool_result flow, deferred-loading promotion, budget gate, and stop reasons in a smaller sync `.ipynb`-oriented engine.
- Constraint forcing adaptation: .ipynb.
- Drift risk if any: current cross-run discovered-tool leak and weaker plan-mode dispatch policy (findings above).
- Required change to reach FAITHFUL: clear discovered set per `run()` and harden plan-mode gate to v4-style allowlist semantics.

UNDECLARED_PATTERN:
- None found in these Phase 8 code files that materially change architecture outside declared rows.

PHASE 08 OVERALL: APPROVE_WITH_FIXES
- A-axis: core loop mostly solid, but discovered-tool lifecycle and plan-mode policy need fixes before parity gate.
- B-axis: 2 FAITHFUL / 2 ADAPTED / 0 DRIFTED

Required before next phase (Phase 08.5 thin-slice parity gate):
- Reset `_discovered_tool_names` at each `run()` start and add regression test.
- Replace plan-mode mutability check with explicit allowlist enforcement (or equivalent strict policy) and add bypass regression test.
- Re-run Phase 8 integration suite with the two new tests included.
2026-04-30T07:59:50.758626Z ERROR codex_core::session: failed to record rollout items: thread 019ddd63-2773-7d21-b9e5-a96bdb6ee271 not found
tokens used
126,684
AXIS A VERDICT: CHANGES_REQUESTED

Findings:
- [high] [query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:161) / [query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:167) — `_discovered_tool_names` is never cleared at `run()` start, so deferred-tool discoveries leak across separate user runs. This violates your Phase 7 wiring contract expectation (“persist within run, reset between runs”) and can silently widen tool payload on later runs. Fix: clear `self._discovered_tool_names` at top of `run()`.
- [medium] [query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:302) — plan-mode gate is `if plan_mode and not tool.is_read_only and not tool.always_load`, which allows any mutating tool marked `always_load=True` to bypass plan mode. v4 enforced explicit allowlist (`PLAN_MODE_ALLOWED_TOOLS`) at dispatch ([compact_v4 sagemaker_agent.py](/D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py:9390)). Fix: enforce allowlist-by-name (or explicit non-bypass invariant) instead of `always_load` exemption.
- [medium][test gap] [test_query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_query_engine.py:161) — no test covers cross-run reset of discovered tools; current leak would pass all tests. Add a test: run #1 does `tool_search select:view_image`; run #2 without `tool_search` must not include `view_image` in turn-1 payload.
- [low][test gap] [test_query_engine.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_query_engine.py:392) — plan-mode test only covers `edit_file` (non-`always_load`). It would not catch the `always_load` bypass class. Add a synthetic mutating `always_load=True` tool and assert block in plan mode.

AXIS B VERDICT

PATTERN 016 (`core/budget.py`): FAITHFUL
- Source intent: shared thread-safe iteration ceiling across parent/sub-agents to bound cost.
- v5 implementation: class body and semantics match v4 `IterationBudget` (same locking and counters; plus benign `reset()` helper).
- Constraint forcing adaptation: none.
- Drift risk if any: minimal (`reset()` is additive, test/manual only).
- Required change to reach FAITHFUL: none.

PATTERN 017 (`core/errors.py`): FAITHFUL
- Source intent: classify Bedrock invoke failures into recovery categories.
- v5 implementation: extraction is behaviorally identical; runtime re-exports preserve class identity.
- Constraint forcing adaptation: none.
- Drift risk if any: low.
- Required change to reach FAITHFUL: none.

PATTERN 018 (`core/retry.py`): FAITHFUL-WITH-JUSTIFIED-ADAPTATION
- Source intent: retry transient failures with jittered exponential backoff.
- v5 implementation: keeps simple backoff policy used in v4 Bedrock path; excludes direct-API features (e.g., `Retry-After` handling in Runnable `withRetry.ts`).
- Constraint forcing adaptation: Bedrock.
- Drift risk if any: lower sophistication under some transient patterns, but aligned with Bedrock client error surface.
- Required change to reach FAITHFUL: none required under Bedrock-only constraint.

PATTERN 019 (`core/query_engine.py`): FAITHFUL-WITH-JUSTIFIED-ADAPTATION
- Source intent: orchestrate turn loop, tool execution, message flow, and deferred tool loading.
- v5 implementation: captures core loop, tool_use/tool_result flow, deferred-loading promotion, budget gate, and stop reasons in a smaller sync `.ipynb`-oriented engine.
- Constraint forcing adaptation: .ipynb.
- Drift risk if any: current cross-run discovered-tool leak and weaker plan-mode dispatch policy (findings above).
- Required change to reach FAITHFUL: clear discovered set per `run()` and harden plan-mode gate to v4-style allowlist semantics.

UNDECLARED_PATTERN:
- None found in these Phase 8 code files that materially change architecture outside declared rows.

PHASE 08 OVERALL: APPROVE_WITH_FIXES
- A-axis: core loop mostly solid, but discovered-tool lifecycle and plan-mode policy need fixes before parity gate.
- B-axis: 2 FAITHFUL / 2 ADAPTED / 0 DRIFTED

Required before next phase (Phase 08.5 thin-slice parity gate):
- Reset `_discovered_tool_names` at each `run()` start and add regression test.
- Replace plan-mode mutability check with explicit allowlist enforcement (or equivalent strict policy) and add bypass regression test.
- Re-run Phase 8 integration suite with the two new tests included.


---

## Phase 8 Codex review — fix verification (2026-04-30)

All 4 findings addressed in same Phase 08 commit:

### Finding 1 (high) — `_discovered_tool_names` leaks across runs
- **Fix**: `core/query_engine.py` `run()` now resets `self._discovered_tool_names = set()` at entry.
- **Lock test**: `test_discovered_tools_reset_between_runs` — runs engine twice, verifies view_image discovered in run #1 is absent from run #2's first turn payload.

### Finding 2 (medium) — plan-mode bypass via `always_load=True`
- **Fix**: `core/query_engine.py` plan-mode dispatch gate now uses strict v4-style allowlist enforcement: `if plan_mode and call.name not in PLAN_MODE_ALLOWED_TOOLS`. The previous `is_read_only AND not always_load` rule exempted always_load mutating tools.
- **Lock test**: `test_engine_plan_mode_blocks_always_load_mutating_tool` — registers a synthetic mutating + always_load=True tool, verifies it's blocked in plan mode.

### Finding 3 (medium, test gap) — cross-run reset coverage
- Covered by lock test for finding 1.

### Finding 4 (low, test gap) — plan-mode always_load bypass coverage
- Covered by lock test for finding 2.

### Test results post-fix
- 319 passed + 4 skipped (was 317+4 pre-fix → +2 lock tests).
- 39 Phase 8 tests total (was 37 → +2).

### Aggregate audit post-fix
All 7 metrics still PASS.

### Final status
- AXIS A: PASS post-fix (was CHANGES_REQUESTED)
- AXIS B: 2 FAITHFUL / 2 ADAPTED / 0 DRIFTED (pattern 019 verdict upgradeable to FAITHFUL on re-review)
- PHASE 08 OVERALL: APPROVE (post-fix)
