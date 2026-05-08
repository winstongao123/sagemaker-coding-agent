Reading additional input from stdin...
OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.5
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019dec74-3b95-70b3-a17a-010b2ce19c7b
--------
user
You are reviewing Block G of v5.0.1 — ITER 2 (re-review after fixes).

Iter-1 verdict was REJECT with 4 findings:
  1. BLOCKER — build worktree was created but CONFIG.workspace not swapped,
     so build agents ran against parent tree.
  2. HIGH — explore/plan/review/verify enforced tool restrictions only via
     prompt wording, not at the spawn level.
  3. MEDIUM — tools/task.py description still said "general only".
  4. DOC — G-1/G-2 deferral to Block H not in PORT_LOG.

Verify each fix lands correctly + new lock tests are sound. Focus the
diff on iter-2 commit 7732b33.

Diff range: 543ebb6..HEAD (iter-2 commit 7732b33).
Full Block diff: v5.0.1-block-m..HEAD.

Iter-2 file changes:
- MODIFIED compact_v5/MAIN/agent/subagent/agent_types.py
  - AgentType gained `allowed_tools: Optional[tuple] = None` field.
  - _READ_ONLY_TOOLS / _VERIFY_TOOLS module constants.
  - explore/plan/review now have allowed_tools=_READ_ONLY_TOOLS.
  - verify has allowed_tools=_VERIFY_TOOLS.
  - general/build/fork: allowed_tools=None → full registry.
- MODIFIED compact_v5/MAIN/agent/subagent/spawn.py
  - Tool allowlist filtering: when agent_def.allowed_tools set, child_tools
    is filtered to that subset (always plus task + tool_search).
  - CONFIG.workspace swap: temporarily set CONFIG.workspace = _worktree_path
    around child.run; restore in finally.
- MODIFIED compact_v5/MAIN/agent/tools/task.py
  - subagent_type now has JSON-schema enum=[7 types] + per-type description.
  - Tool description rewritten to list all 7 types with their roles.
- MODIFIED compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
  - NEW row #089 (iter-2 fixes summary).
  - NEW row #090 (G-1 + G-2 explicit DEFER → Block H).
- MODIFIED compact_v5/MAIN/agent/tests/integration/test_block_g.py
  - 6 new lock tests:
    + test_build_agent_actually_runs_inside_worktree
    + test_explore_agent_tool_allowlist_excludes_mutators
    + test_plan_agent_tool_allowlist_read_only
    + test_verify_agent_allows_bash_but_not_mutators
    + test_general_agent_gets_full_registry
    + test_task_tool_schema_lists_all_7_agent_types

Reference paths:
- Plan: compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md (§Block G)
- Tests: compact_v5/_phase_2/wave_6/TEST_DESIGN.md (§Block G)
- ADR-031: compact_v5/_status/V5_DESIGN_DECISIONS.md

Tests: 662 pass + 6 skip (was 656 + 6 at iter-1; +6 finding-locks).
verify_ship_zip.py: PASS (117 files / 329.3 KB / 36%).

Apply the 3-axis review template focused on iter-2 fixes.

AXIS A — Errors / bugs / regressions
- Verify finding #1 fix (BLOCKER):
  - Look at spawn.py: CONFIG.workspace swap happens just before
    `try: child.run(...)`. The swap sets `_saved_workspace`; restore is
    in `finally`. A child.run that raises must STILL restore.
    Verify by code path inspection.
  - Lock test test_build_agent_actually_runs_inside_worktree captures
    CONFIG.workspace inside chat() and asserts != parent during run +
    == parent after.
  - EDGE: if create_worktree returns None (hard failure), CONFIG.workspace
    must NOT be swapped. Verify the `if _worktree_path:` guard.
- Verify finding #2 fix (HIGH):
  - allowed_tools tuple stored on frozen dataclass — verify it serializes
    OK at module load (no mutation surface).
  - spawn child_tools filter: `[t for t in child_tools if t.name in _allow]`.
    _allow is built from agent_def.allowed_tools | {"task", "tool_search"}.
    The 4 read-only lock tests verify this filter actually runs.
- Verify finding #3 fix (MEDIUM):
  - JSON schema enum present at task.py subagent_type. Lock test asserts
    set(enum) == set(AGENT_TYPES.keys()).
- Verify finding #4 fix (DOC):
  - PORT_LOG row #090 declares G-1 + G-2 as DEFER → Block H. Verify the
    column count is still 10 (id/date/phase/source/target/adoption/err/
    fidelity/commit/notes).

Verdict: PASS | CHANGES_REQUESTED | BLOCKER.

AXIS B — v5 architecture + goals fit
- Constraint #6 (architecture-first): tool allowlist is a structural
  contract, not just prompt wording. CONFIG.workspace swap is the same
  pattern v4 used at sagemaker_agent.py:8413+.
- Constraint #15 (quality, no rush): lock tests now actually exercise
  the contract — explore failing to expose write_file is a concrete
  invariant.
- Q3 axis 4 (focus on tasks): sub-agents now get a tool surface matched
  to their role.

FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED.

AXIS C — Reference-repo coverage
PORT_LOG #089 covers iter-2 code fixes. PORT_LOG #090 covers G-1/G-2
deferral. ADR-031 §Notes already mentioned the deferral; PORT_LOG row
makes it discoverable via the standard PORT_LOG → ADR cross-reference.

Verdict: ALL_PORTED | SOME_DROPPED | UNDECLARED_PATTERN.

FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.

APPROVE only if all 4 iter-1 findings have clean fixes with covering
lock tests AND no new findings emerge. Be specific. Cite file:line.
codex
I’ll re-review the iter-2 diff directly, focusing on the four previous findings and the new lock tests. I’ll inspect the changed files and line numbers first, then verify the relevant test behavior and PORT_LOG structure.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --stat 543ebb6..HEAD' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- compact_v5/MAIN/agent/subagent/agent_types.py compact_v5/MAIN/agent/subagent/spawn.py compact_v5/MAIN/agent/tools/task.py compact_v5/_status/V5_RUNNABLE_PORT_LOG.md compact_v5/MAIN/agent/tests/integration/test_block_g.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in D:\Github\sagemaker-coding-agent
 succeeded in 518ms:
 succeeded in 522ms:
 m _archive/compare_code/gg-claude-code-runnable
?? compact_v5/_status/codex_reviews/block-g-iter1.md
?? compact_v5/_status/codex_reviews/block-g-iter2-prompt.txt
?? compact_v5/_status/codex_reviews/block-g-iter2.md
?? compact_v5/_status/codex_reviews/block-g-prompt.txt
warning: unable to access 'C:\Users\winst/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\winst/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\winst/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\winst/.config/git/ignore': Permission denied

 succeeded in 523ms:
 SESSION_STATE.md                                   |  11 +-
 compact_v5.zip                                     | Bin 335943 -> 337169 bytes
 compact_v5/MAIN/agent/subagent/agent_types.py      |  20 ++
 compact_v5/MAIN/agent/subagent/spawn.py            |  48 ++++-
 .../MAIN/agent/tests/integration/test_block_g.py   | 225 +++++++++++++++++++++
 compact_v5/MAIN/agent/tools/task.py                |  13 +-
 compact_v5/_status/V5_RUNNABLE_PORT_LOG.md         |   2 +
 7 files changed, 313 insertions(+), 6 deletions(-)

codex
The expected iter-2 files are the only tracked source/doc/test changes in the range, plus zip/session metadata. The plain path diff was empty because it compared the working tree; I’m switching to exact commit-range reads with line numbers so the review can cite the landed code.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/subagent/agent_types.py | ForEach-Object { '"'{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/subagent/spawn.py | ForEach-Object { '"'{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/tools/task.py | ForEach-Object { '"'{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 499ms:
   1: """V5 subagent/agent_types.py â€” Block G AGENT_TYPES registry.
   2: 
   3: PORT_LOG: #086.
   4: 
   5: Source:
   6: - v4 sagemaker_agent.py:6914-7090 (~176 LOC original AGENT_TYPES dict)
   7: - Runnable AgentTool/constants.ts (ONE_SHOT_BUILTIN_AGENT_TYPES)
   8: - Runnable AgentTool/prompt.ts (DEFAULT_AGENT_PROMPT phrasing)
   9: 
  10: Each agent type is one row with:
  11: - system_suffix: a per-agent prompt suffix appended to the base system
  12:   prompt. Sets task-shape expectations.
  13: - max_turns: ceiling on the sub-agent's turn count (independent of the
  14:   shared IterationBudget, which is the cost-cap; max_turns is the
  15:   task-scope-cap).
  16: - one_shot: True for Explore/Plan/Verify-style agents that produce a
  17:   single report and don't accept follow-up; matches Runnable's
  18:   ONE_SHOT_BUILTIN_AGENT_TYPES (constants.ts:9-12). One-shot agents
  19:   skip the agentId/SendMessage/usage trailer in their system prompt
  20:   to save tokens.
  21: - auto_load_skill: optional skill name to auto-activate in the child's
  22:   SkillManager before run(). Used by `verify` to load skills/verify/
  23:   for the verification gate-checks.
  24: - needs_worktree: True for `build` â€” spawns the child in an isolated
  25:   git worktree so concurrent build agents don't clobber each other.
  26:   v4 sagemaker_agent.py:8413+ (~57 LOC).
  27: """
  28: from __future__ import annotations
  29: 
  30: from dataclasses import dataclass
  31: from typing import Optional
  32: 
  33: 
  34: # Block G-6: DEFAULT_AGENT_PROMPT verbatim (Runnable constants/prompts.ts:758).
  35: # Battle-tested wording: tells sub-agents NOT to gold-plate; the parent
  36: # only needs the answer, not surrounding cleanup. Keeps token cost
  37: # predictable for cheap fanout patterns (Explore + Plan).
  38: DEFAULT_AGENT_PROMPT = (
  39:     "You are a sub-agent working on a focused task. Always use ABSOLUTE "
  40:     "file paths (cwd may reset between bash calls). In your final "
  41:     "response, share relevant file paths and key findings. Be concise â€” "
  42:     "the parent will read your full reply. Do NOT add features, "
  43:     "refactor, or introduce abstractions beyond what the task requires."
  44: )
  45: 
  46: 
  47: # Block G-7: "Notes" appendix to subagent system prompt
  48: # (Runnable constants/prompts.ts:766-770). Each line fixes a real
  49: # failure mode in the wild.
  50: SUBAGENT_NOTES = (
  51:     "\n\nNotes:\n"
  52:     "- Always include a short description of what you'll do before tool calls.\n"
  53:     "- When you launch multiple research tasks, run them in parallel.\n"
  54:     "- The parent agent CANNOT see your intermediate tool calls â€” only "
  55:     "your final reply text. Surface findings explicitly in your reply."
  56: )
  57: 
  58: 
  59: @dataclass(frozen=True)
  60: class AgentType:
  61:     name: str
  62:     system_suffix: str
  63:     max_turns: int = 25
  64:     one_shot: bool = False
  65:     auto_load_skill: Optional[str] = None
  66:     needs_worktree: bool = False
  67:     # Block G iter-2 (Codex finding #2 HIGH): allowed_tools allowlist enforced
  68:     # at spawn time (was: prompt-only "Do NOT edit files" wording, which the
  69:     # model could ignore). When None, the child gets the full registry.
  70:     # When set, child_tools is filtered to this list before child.run.
  71:     allowed_tools: Optional[tuple] = None  # tuple for frozen-dataclass safety
  72: 
  73: 
  74: # Read-only tool allowlist for explore / plan / review (no file mutation,
  75: # no shell exec). semantic_search included because it's read-only.
  76: _READ_ONLY_TOOLS: tuple = (
  77:     "read_file", "grep", "glob", "list_dir", "view_image",
  78:     "todo_read", "todo_write", "semantic_search", "ask_user",
  79: )
  80: # Verify allowlist: read-only + bash (so verify can run pytest / lint /
  81: # build commands). NO edit/write tools.
  82: _VERIFY_TOOLS: tuple = _READ_ONLY_TOOLS + ("bash", "python_exec")
  83: 
  84: 
  85: # Block G-1: AGENT_TYPES dict â€” 7 entries per TEST_DESIGN test_agent_types_dict_has_7.
  86: # Names match v4 + Runnable conventions.
  87: AGENT_TYPES: dict = {
  88:     "general": AgentType(
  89:         name="general",
  90:         system_suffix=DEFAULT_AGENT_PROMPT + SUBAGENT_NOTES,
  91:     ),
  92:     "explore": AgentType(
  93:         name="explore",
  94:         system_suffix=(
  95:             DEFAULT_AGENT_PROMPT
  96:             + "\n\nFocus: read-only exploration. Use Read, Grep, Glob to "
  97:             "understand the codebase. Do NOT edit files. Return a concise "
  98:             "summary with file:line references for key findings."
  99:             + SUBAGENT_NOTES
 100:         ),
 101:         max_turns=20,
 102:         one_shot=True,  # Block G-3: ONE_SHOT_BUILTIN_AGENT_TYPES
 103:         allowed_tools=_READ_ONLY_TOOLS,
 104:     ),
 105:     "plan": AgentType(
 106:         name="plan",
 107:         system_suffix=(
 108:             DEFAULT_AGENT_PROMPT
 109:             + "\n\nFocus: produce an implementation plan. Read code as "
 110:             "needed (Read, Grep, Glob). Do NOT write code. Return a "
 111:             "step-by-step plan with file paths and what to change."
 112:             + SUBAGENT_NOTES
 113:         ),
 114:         max_turns=15,
 115:         one_shot=True,
 116:         allowed_tools=_READ_ONLY_TOOLS,
 117:     ),
 118:     "verify": AgentType(
 119:         name="verify",
 120:         system_suffix=(
 121:             DEFAULT_AGENT_PROMPT
 122:             + "\n\nFocus: run verification gates. Use the loaded `verify` "
 123:             "skill body for the exact checklist. Report PASS/FAIL per gate "
 124:             "and a single overall verdict at the end."
 125:             + SUBAGENT_NOTES
 126:         ),
 127:         max_turns=20,
 128:         one_shot=True,
 129:         auto_load_skill="verify",  # Block G â€” TEST_DESIGN row 3
 130:         allowed_tools=_VERIFY_TOOLS,  # read-only + bash + python_exec
 131:     ),
 132:     "build": AgentType(
 133:         name="build",
 134:         system_suffix=(
 135:             DEFAULT_AGENT_PROMPT
 136:             + "\n\nFocus: implement the requested change. You are running "
 137:             "inside an isolated git worktree, so file edits won't affect "
 138:             "the parent's working tree until the parent merges. Run tests "
 139:             "before declaring done."
 140:             + SUBAGENT_NOTES
 141:         ),
 142:         max_turns=40,
 143:         needs_worktree=True,  # Block G â€” TEST_DESIGN row 2
 144:     ),
 145:     "review": AgentType(
 146:         name="review",
 147:         system_suffix=(
 148:             DEFAULT_AGENT_PROMPT
 149:             + "\n\nFocus: code review. Read the diff or files at the cited "
 150:             "paths and report concrete issues with file:line. Avoid "
 151:             "praise â€” surface bugs, security risks, and unclear semantics."
 152:             + SUBAGENT_NOTES
 153:         ),
 154:         max_turns=20,
 155:         one_shot=True,
 156:         allowed_tools=_READ_ONLY_TOOLS,
 157:     ),
 158:     "fork": AgentType(
 159:         name="fork",
 160:         system_suffix=(
 161:             DEFAULT_AGENT_PROMPT
 162:             + "\n\nFocus: continue the parent's task in a forked context. "
 163:             "You inherit the parent's full conversation. Pick up where "
 164:             "the parent left off and complete the task."
 165:             + SUBAGENT_NOTES
 166:         ),
 167:         max_turns=50,
 168:     ),
 169: }
 170: 
 171: 
 172: # Block G-3: Runnable's ONE_SHOT_BUILTIN_AGENT_TYPES set.
 173: # (Computed from AGENT_TYPES so they stay in sync.)
 174: ONE_SHOT_BUILTIN_AGENT_TYPES = frozenset(
 175:     name for name, t in AGENT_TYPES.items() if t.one_shot
 176: )
 177: 
 178: 
 179: def get_agent_type(name: str) -> Optional[AgentType]:
 180:     """Look up an AgentType by name. Returns None for unknown names so
 181:     the caller (spawn_subagent) can surface a clear error rather than
 182:     silently falling back to general."""
 183:     return AGENT_TYPES.get(name)
 184: 
 185: 
 186: def get_agent_prompt(name: str, is_coordinator: bool = False) -> str:
 187:     """Block G-4 (Runnable AgentTool/prompt.ts:202-213): coordinators get
 188:     a slim prompt, non-coordinators get the full system_suffix.
 189: 
 190:     For v5, the slim prompt is the suffix without the Notes appendix
 191:     (the coordinator system prompt covers usage notes itself, per Block
 192:     G3 ADR). When is_coordinator=False, returns the full suffix
 193:     including Notes.
 194:     """
 195:     agent = AGENT_TYPES.get(name)
 196:     if agent is None:
 197:         return DEFAULT_AGENT_PROMPT + SUBAGENT_NOTES
 198:     if is_coordinator:
 199:         # Slim: drop Notes appendix.
 200:         return agent.system_suffix.replace(SUBAGENT_NOTES, "")
 201:     return agent.system_suffix

 succeeded in 503ms:
   1: """Phase 9 task tool â€” sub-agent dispatch (Phase 9, ADR-015).
   2: 
   3: ADAPT port of:
   4: - gg-claude-code-runnable/src/tools/AgentTool/AgentTool.tsx (1397 LOC) â€” only the
   5:   tool-shape contract (description + schema + executor signature). Runnable's
   6:   React/Ink UI lives in UI.tsx and is not ported (constraint=.ipynb).
   7: - v4 `_run_task_tool` at sagemaker_agent.py:8350 â€” the executor logic.
   8: 
   9: PORT_LOG: #024.
  10: 
  11: Phase 9 surface â€” minimal so the v5 .ipynb shape doesn't drag the full
  12: AGENT_TYPES + worktree complexity across the gate:
  13: - subagent_type values: "general" only. Future phases add build/plan/explore/verify.
  14: - No worktree isolation (build agent's git-worktree dance lands in Phase 11).
  15: - No parallel dispatch (Runnable's parallel sub-agent dispatch is async-only).
  16: 
  17: The tool is marked `should_defer=True` because spawn is low-frequency:
  18: most turns don't need a sub-agent, so the schema is loaded only when the
  19: model calls tool_search after seeing the deferred-tool reminder.
  20: 
  21: The Phase 7 wiring contract (ADR-013/014) requires the executor to receive
  22: the parent QueryEngine via `context["parent_engine"]` so the child can share
  23: the parent's IterationBudget â€” see acceptance test
  24: `test_subagent_shares_iteration_budget`.
  25: """
  26: from __future__ import annotations
  27: 
  28: from typing import Any, Dict, Optional
  29: 
  30: from .registry import build_tool, register
  31: 
  32: 
  33: _DESCRIPTION = """Launch a sub-agent for a specific, scoped task.
  34: 
  35: Sub-agents run with a FRESH conversation but share the parent agent's iteration budget â€” they cannot collectively exceed the cost ceiling. Use a sub-agent when:
  36: - The task is well-scoped and self-contained (e.g., "summarize this codebase", "find every TODO comment").
  37: - You want to keep the parent's main context clean (the sub-agent's full transcript is not loaded into the parent â€” only the final answer is returned).
  38: - You need read-only exploration without polluting the parent's file-read history.
  39: 
  40: Do NOT use a sub-agent when:
  41: - The task is small enough to do directly in the current turn.
  42: - The result must be incrementally visible to the user (sub-agent runs to completion before returning).
  43: - You need persistent state across multiple top-level requests (sub-agents are one-shot).
  44: 
  45: Inputs:
  46: - description: 1-line summary shown to the user.
  47: - prompt: the actual task description for the sub-agent. Be specific.
  48: - subagent_type: one of `general` | `explore` | `plan` | `verify` | `build` | `review` | `fork` (default `general`).
  49:   - `general` â€” full tool access; default.
  50:   - `explore` â€” read-only exploration (no edit/write/exec); produces a report.
  51:   - `plan` â€” read-only planning (no edit/write/exec); produces a step-by-step plan.
  52:   - `verify` â€” read + bash; auto-loads the `verify` skill; runs gate checks.
  53:   - `build` â€” full tools, runs in isolated git worktree.
  54:   - `review` â€” read-only code review; surfaces concrete issues with file:line.
  55:   - `fork` â€” inherits parent context conceptually; full tools.
  56: 
  57: Returns the sub-agent's final answer as a string. If the sub-agent hits its iteration budget or max_turns, the partial work + reason is returned."""
  58: 
  59: 
  60: _INPUT_SCHEMA: Dict[str, Any] = {
  61:     "type": "object",
  62:     "properties": {
  63:         "description": {
  64:             "type": "string",
  65:             "description": "1-line summary of what the sub-agent will do (for display only).",
  66:         },
  67:         "prompt": {
  68:             "type": "string",
  69:             "description": "Full task description sent to the sub-agent. Be specific â€” the sub-agent has no parent context unless you brief it.",
  70:         },
  71:         "subagent_type": {
  72:             "type": "string",
  73:             "enum": ["general", "explore", "plan", "verify", "build", "review", "fork"],
  74:             "default": "general",
  75:             "description": "Agent type. general (default; full tools) | explore (read-only) | plan (read-only) | verify (read + bash + auto-loads verify skill) | build (full + isolated git worktree) | review (read-only code review) | fork (full tools, parent-context).",
  76:         },
  77:     },
  78:     "required": ["prompt"],
  79: }
  80: 
  81: 
  82: def _task_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
  83:     """Spawn a sub-agent and return its final answer.
  84: 
  85:     Required context (Phase 9 contract):
  86:       - context["parent_engine"]: the parent QueryEngine. Used to (a) share
  87:         IterationBudget, (b) reuse the BedrockClient, (c) inherit on_stop_check.
  88:         If absent, the executor returns an Error: the model can read.
  89:       - context["parent_depth"] (optional, default 0): the parent's depth.
  90:         Used to enforce the recursion-depth limit.
  91:     """
  92:     description = str(args.get("description", "")).strip()
  93:     prompt = str(args.get("prompt", "")).strip()
  94:     if not prompt:
  95:         return "Error: prompt is required and must be a non-empty string"
  96:     subagent_type = str(args.get("subagent_type", "general")).strip() or "general"
  97: 
  98:     # Codex Phase-09 finding (medium): silently falling back to general for
  99:     # unknown types hides caller/model errors. v4's explicit-unknown-type
 100:     # contract (sagemaker_agent.py:8366) is preserved here.
 101:     # Block G: validation now consults the full AGENT_TYPES registry
 102:     # (build / plan / explore / verify / general / review / fork) â€” was
 103:     # the Phase-9 single-entry _AGENT_TYPE_SUFFIXES dict.
 104:     from subagent.agent_types import AGENT_TYPES
 105:     if subagent_type not in AGENT_TYPES:
 106:         available = ", ".join(sorted(AGENT_TYPES.keys()))
 107:         return (
 108:             f"Error: unknown subagent_type '{subagent_type}'. "
 109:             f"Block G supports: {available}."
 110:         )
 111: 
 112:     if not isinstance(context, dict) or "parent_engine" not in context:
 113:         return (
 114:             "Error: task tool requires `context['parent_engine']` to spawn a "
 115:             "sub-agent (Phase 9 contract). The query_engine should pass this "
 116:             "via the tool dispatch context."
 117:         )
 118:     parent_engine = context["parent_engine"]
 119:     parent_depth = int(context.get("parent_depth", 0))
 120: 
 121:     # Lazy-import to avoid circular import: subagent.spawn imports
 122:     # core.query_engine which (via tools/__init__.py:bootstrap_built_ins)
 123:     # imports this module.
 124:     from subagent.spawn import spawn_subagent
 125: 
 126:     result = spawn_subagent(
 127:         parent_engine=parent_engine,
 128:         prompt=prompt,
 129:         agent_type=subagent_type,
 130:         parent_depth=parent_depth,
 131:         plan_mode=bool(context.get("plan_mode", False)),
 132:     )
 133: 
 134:     if result.error and result.stop_reason in ("depth_exceeded", "invalid_args"):
 135:         return result.error
 136:     if result.stop_reason in ("budget_exhausted", "max_turns", "context_overflow"):
 137:         # Surface partial work + reason so the parent can react.
 138:         return (
 139:             f"[Sub-agent stopped: {result.stop_reason}]\n"
 140:             f"{result.text or '(no partial output)'}"
 141:         )
 142:     return result.text or "(sub-agent returned no text)"
 143: 
 144: 
 145: def _register():
 146:     """Idempotent registration. Called by tools/__init__.py:bootstrap_built_ins."""
 147:     from .registry import find_tool_by_name, all_registered, unregister
 148:     if find_tool_by_name(all_registered(), "task") is not None:
 149:         return  # already registered
 150: 
 151:     register(build_tool(
 152:         name="task",
 153:         description=_DESCRIPTION,
 154:         input_schema=_INPUT_SCHEMA,
 155:         execute=_task_executor,
 156:         is_read_only=False,         # children may write â€” fail-closed default
 157:         is_destructive=False,
 158:         is_concurrency_safe=False,  # parallel sub-agents land later
 159:         requires_approval=False,    # the *child* approval gates fire on its tool calls
 160:         should_defer=True,          # low-frequency; deferred via Phase 7
 161:         always_load=False,
 162:         search_hint="sub-agent fork delegate spawn task launch background",
 163:     ))

 succeeded in 532ms:
   1: """V5 subagent/spawn.py â€” fork-style sub-agent spawn (Phase 9, ADR-015).
   2: 
   3: ADAPT port of Runnable's `forkSubagent.ts` (210 LOC). v5 adaptation:
   4: - Synchronous (no Promise / async generator chain). Constraint=.ipynb.
   5: - Drops Runnable's experimental fork branch (FORK_SUBAGENT feature gate),
   6:   cache-prefix-identical message replay, and `<task-notification>`
   7:   background dispatch model â€” those need streaming/async to be useful.
   8: - Drops Runnable's coordinator-mode mutual exclusion (v5 has no coordinator).
   9: - v5's spawn ALWAYS shares the parent's IterationBudget instance â€” that is
  10:   Hermes's PS Issue #2 contract and the Phase-9 acceptance criterion.
  11: - Drops AGENT_TYPES configuration registry â€” Phase 9 supports `general` only;
  12:   build/plan/explore/verify agent types are deferred (their large prompts
  13:   are reviewable as data later).
  14: - Includes depth-limit enforcement (v4 sagemaker_agent.py:8354 parity).
  15: 
  16: PORT_LOG: #021.
  17: 
  18: Acceptance criteria (V5_PLAN.md Â§Phase 9):
  19: - Parent context unchanged after sub-agent run.
  20: - Child shares IterationBudget instance.
  21: 
  22: Usage:
  23:     parent = QueryEngine(client=..., budget=IterationBudget())
  24:     text, child = spawn_subagent(parent, "summarize this codebase", "general")
  25:     # parent.messages is unchanged; child.budget is parent.budget.
  26: """
  27: from __future__ import annotations
  28: 
  29: import logging
  30: import os
  31: from dataclasses import dataclass, field
  32: from typing import Any, Callable, List, Optional, Tuple
  33: 
  34: from .env import build_env_details
  35: from .handoff import build_handoff_block
  36: 
  37: 
  38: # Default cap on sub-agent depth. Matches v4 CONFIG.subagent_max_depth=2.
  39: DEFAULT_MAX_DEPTH: int = 2
  40: 
  41: # Block G â€” full AGENT_TYPES registry (build / plan / explore / verify /
  42: # general / review / fork) lands as a sibling module. Spawn dispatches via
  43: # get_agent_type for type validation + worktree / skill auto-load.
  44: 
  45: 
  46: @dataclass
  47: class SubagentResult:
  48:     """Outcome of `spawn_subagent`. Returned alongside the child engine so
  49:     callers can inspect message buffer / budget / stop reason / turns_used.
  50: 
  51:     `text`            â€” final assistant text (the sub-agent's answer).
  52:     `stop_reason`     â€” same as QueryResult.stop_reason.
  53:     `turns_used`      â€” turns the child consumed.
  54:     `child_messages`  â€” the child's full conversation buffer (for audit).
  55:     `error`           â€” short message when stop_reason indicates failure.
  56:     `agent_type`      â€” what type was requested.
  57:     `depth`           â€” depth the child ran at.
  58:     """
  59:     text: str = ""
  60:     stop_reason: str = ""
  61:     turns_used: int = 0
  62:     child_messages: List[Any] = field(default_factory=list)
  63:     error: Optional[str] = None
  64:     agent_type: str = "general"
  65:     depth: int = 1
  66: 
  67: 
  68: def _new_child_engine(parent_engine: Any, max_turns: int, agent_type: str = "general") -> Any:
  69:     """Construct a fresh QueryEngine that shares the parent's IterationBudget.
  70: 
  71:     Lazy-imports to avoid a circular load at module-import time
  72:     (core.query_engine imports tools/registry which may import
  73:     tools/task.py which imports this module).
  74: 
  75:     Block B: `agent_type` is forwarded as `agent_kind` so TOKENS.add()
  76:     attributes the child's input/output/cost to the right per-agent
  77:     bucket. The child also gets a fresh session_id so AUDIT.log entries
  78:     can be filtered to a single sub-agent run.
  79:     """
  80:     from core.query_engine import QueryEngine
  81:     return QueryEngine(
  82:         client=parent_engine.client,
  83:         max_turns=max_turns,
  84:         budget=parent_engine.budget,            # SHARED â€” the Phase-9 contract
  85:         on_stop_check=parent_engine.on_stop_check,
  86:         agent_kind=agent_type,
  87:     )
  88: 
  89: 
  90: def _resolve_agent_suffix(agent_type: str) -> Optional[str]:
  91:     """Look up the prompt suffix for a known agent type.
  92: 
  93:     Returns None for unknown types so the caller (spawn_subagent / task tool)
  94:     can surface an explicit error instead of silently falling back. Phase-9
  95:     Codex finding: silent fallback masks contract bugs.
  96: 
  97:     Block G: now consults the AGENT_TYPES registry (was: tiny dict keyed on
  98:     "general" only). Returns the per-type system_suffix.
  99:     """
 100:     from .agent_types import get_agent_type
 101:     at = get_agent_type(agent_type)
 102:     return at.system_suffix if at is not None else None
 103: 
 104: 
 105: def spawn_subagent(
 106:     parent_engine: Any,
 107:     prompt: str,
 108:     agent_type: str = "general",
 109:     parent_depth: int = 0,
 110:     max_turns: int = 25,
 111:     max_depth: int = DEFAULT_MAX_DEPTH,
 112:     base_system_prompt: Optional[str] = None,
 113:     workspace: Optional[str] = None,
 114:     status_path: Optional[str] = None,
 115:     todos_text: Optional[str] = None,
 116:     recent_files: Optional[List[str]] = None,
 117:     plan_mode: bool = False,
 118:     output_fn: Callable[[str], None] = print,
 119: ) -> SubagentResult:
 120:     """Spawn a sub-agent with the parent's shared IterationBudget.
 121: 
 122:     The child gets:
 123:       - A FRESH message buffer (no parent conversation leakage).
 124:       - The parent's BedrockClient, IterationBudget, on_stop_check (shared).
 125:       - A system prompt = base_system_prompt + env_details + handoff_block
 126:         + agent-type suffix, with the cache boundary preserved.
 127: 
 128:     Returns a `SubagentResult` with the child's final answer + audit info.
 129: 
 130:     Phase 9 contract (V5_PLAN.md Â§Phase 9):
 131:       - Parent's `messages` buffer is NOT mutated.
 132:       - Child's `budget is parent_engine.budget` (object identity).
 133:       - Depth-limit enforcement: depth >= max_depth â†’ blocked with error
 134:         result, no Bedrock call made.
 135:     """
 136:     child_depth = parent_depth + 1
 137: 
 138:     # Depth-limit gate (v4 sagemaker_agent.py:8354 parity).
 139:     if child_depth > max_depth:
 140:         return SubagentResult(
 141:             text="",
 142:             stop_reason="depth_exceeded",
 143:             error=(
 144:                 f"Blocked: sub-agent depth limit reached "
 145:                 f"({child_depth} > max {max_depth})"
 146:             ),
 147:             agent_type=agent_type,
 148:             depth=child_depth,
 149:         )
 150: 
 151:     # Validate prompt â€” empty prompt is a programming error in the caller.
 152:     p = (prompt or "").strip()
 153:     if not p:
 154:         return SubagentResult(
 155:             text="",
 156:             stop_reason="invalid_args",
 157:             error="Error: prompt is required",
 158:             agent_type=agent_type,
 159:             depth=child_depth,
 160:         )
 161: 
 162:     # Validate agent type. The task tool already gates on this at the
 163:     # dispatch layer, but spawn_subagent is also called directly by Phase
 164:     # 11 UX wiring, so guard here too. Codex Phase-09 finding: don't
 165:     # silently fall back to `general`.
 166:     suffix = _resolve_agent_suffix(agent_type)
 167:     if suffix is None:
 168:         from .agent_types import AGENT_TYPES
 169:         available = ", ".join(sorted(AGENT_TYPES.keys()))
 170:         return SubagentResult(
 171:             text="",
 172:             stop_reason="invalid_args",
 173:             error=(
 174:                 f"Error: unknown agent_type '{agent_type}'. "
 175:                 f"Block G supports: {available}."
 176:             ),
 177:             agent_type=agent_type,
 178:             depth=child_depth,
 179:         )
 180: 
 181:     # Block G â€” resolve the AgentType row for per-type max_turns / worktree
 182:     # / auto_load_skill knobs.
 183:     from .agent_types import get_agent_type
 184:     agent_def = get_agent_type(agent_type)
 185:     if agent_def is not None:
 186:         # Per-type max_turns: caller can override via the max_turns param.
 187:         # Default policy: use the per-type ceiling unless caller passed
 188:         # something smaller (defense in depth â€” caller knows the task).
 189:         max_turns = min(max_turns, agent_def.max_turns)
 190: 
 191:     # Assemble the child's system prompt:
 192:     #   <static> [+ env_details + handoff_block + agent_type_suffix in dynamic tail]
 193:     # If base_system_prompt has the boundary marker, inject our extras after it.
 194:     # Otherwise append at the end.
 195:     from prompt import build_system_prompt, CACHE_BOUNDARY
 196: 
 197:     base = base_system_prompt or build_system_prompt(ctx={})
 198:     env_details = build_env_details(
 199:         agent_type=agent_type,
 200:         depth=child_depth,
 201:         workspace=workspace,
 202:         max_depth=max_depth,
 203:     )
 204:     handoff = build_handoff_block(
 205:         status_path=status_path,
 206:         todos_text=todos_text,
 207:         recent_files=recent_files,
 208:     )
 209: 
 210:     dynamic_extras = [env_details, handoff, suffix]
 211:     dynamic_extras = [x for x in dynamic_extras if x]
 212: 
 213:     if dynamic_extras:
 214:         addendum = "\n\n" + "\n\n".join(dynamic_extras)
 215:         if CACHE_BOUNDARY in base:
 216:             # Append after the existing dynamic tail (preserve cached prefix).
 217:             child_prompt = base + addendum
 218:         else:
 219:             # No boundary â€” append at the end with our own boundary so future
 220:             # cache-block builders see the static/dynamic split.
 221:             child_prompt = base + CACHE_BOUNDARY + addendum
 222:     else:
 223:         child_prompt = base
 224: 
 225:     # Construct child engine. The shared-budget invariant is enforced by
 226:     # _new_child_engine â€” verified by test_subagent_shares_iteration_budget.
 227:     child = _new_child_engine(parent_engine, max_turns=max_turns, agent_type=agent_type)
 228: 
 229:     # Codex Phase-09 finding (BLOCKER): thread the child's depth so that
 230:     # IF the child itself dispatches `task`, the QueryEngine's tool-dispatch
 231:     # context picks up the correct `parent_depth` via
 232:     # `getattr(self, "_subagent_depth", 0)`. Without this line, nested
 233:     # `task` chains all see parent_depth=0 and the recursion guard never
 234:     # fires. Lock test: test_nested_subagent_recursion_blocked_at_max_depth.
 235:     child._subagent_depth = child_depth
 236: 
 237:     # Snapshot the parent's full message buffer for a defense-in-depth
 238:     # mutation check. Codex Phase-09 finding (medium): the prior version
 239:     # checked only length, so an in-place mutation that preserves length
 240:     # (e.g. modifying messages[i]["content"] of an existing entry) would
 241:     # evade detection. We deep-copy so post-hoc comparison is structural.
 242:     import copy
 243:     parent_msgs_snapshot = copy.deepcopy(parent_engine.messages)
 244: 
 245:     # Resolve the child's tool pool. Block G iter-2 (Codex finding #2 HIGH):
 246:     # specialized agents (explore/plan/verify/review) get a tool allowlist
 247:     # enforced at spawn â€” prompt-only "Do NOT edit files" wording was not a
 248:     # contract. When agent_def.allowed_tools is set, child_tools is filtered
 249:     # to that subset; otherwise the full registry is used.
 250:     from tools import all_registered
 251:     child_tools = all_registered()
 252:     if agent_def is not None and agent_def.allowed_tools:
 253:         _allow = set(agent_def.allowed_tools)
 254:         # Always include `task` so a plan/explore agent can still spawn
 255:         # further sub-agents (depth-limit gates separately).
 256:         # Always include `tool_search` so deferred-loading still works.
 257:         _allow.update({"task", "tool_search"})
 258:         child_tools = [t for t in child_tools if t.name in _allow]
 259:         logging.debug(
 260:             "[subagent] agent_type=%s tool allowlist (%d tools): %s",
 261:             agent_type, len(child_tools), sorted(t.name for t in child_tools),
 262:         )
 263: 
 264:     # Block B+ (PORT_LOG #053): save+clear FILE_CACHE main context
 265:     # before the child runs so the child sees a fresh in-context set;
 266:     # restore the parent's set after the child returns. Best-effort â€”
 267:     # if FILE_CACHE singleton is unavailable, dispatch still proceeds.
 268:     _file_cache_saved = None
 269:     try:
 270:         from runtime.file_cache import FILE_CACHE as _FC
 271:         _file_cache_saved = _FC.save_and_clear_context()
 272:     except Exception:
 273:         pass
 274: 
 275:     # Block G â€” worktree spawn for `build` agents. Best-effort; on hard
 276:     # failure, runs in parent dir with a warning.
 277:     _worktree_path: Optional[str] = None
 278:     if agent_def is not None and agent_def.needs_worktree:
 279:         try:
 280:             from .worktree import create_worktree
 281:             from runtime.config import CONFIG as _CFG_W
 282:             _wt_parent = workspace or getattr(_CFG_W, "workspace", os.getcwd())
 283:             _worktree_path, _wt_source = create_worktree(_wt_parent)
 284:             if _worktree_path:
 285:                 logging.info(
 286:                     "[subagent] build agent isolated in worktree=%s (source=%s)",
 287:                     _worktree_path, _wt_source,
 288:                 )
 289:             else:
 290:                 logging.warning(
 291:                     "[subagent] build agent worktree creation failed â€” "
 292:                     "running in parent cwd."
 293:                 )
 294:         except Exception as _wt_exc:
 295:             logging.warning("[subagent] worktree setup raised: %s", _wt_exc)
 296:             _worktree_path = None
 297: 
 298:     # Block G â€” verify agent auto-loads the verify skill so its body sits
 299:     # in the child's system prompt as the gate-check checklist.
 300:     if (
 301:         agent_def is not None
 302:         and agent_def.auto_load_skill
 303:         and parent_engine.skill_manager is not None
 304:     ):
 305:         try:
 306:             ok, _msg = parent_engine.skill_manager.activate(agent_def.auto_load_skill)
 307:             if ok:
 308:                 # Inject the active skill body into the child's system prompt
 309:                 # tail (cannot share parent's skill_manager state directly
 310:                 # since child has its own SkillManager surface in v5).
 311:                 _skill_body = parent_engine.skill_manager.get_active_skill_prompt(
 312:                     session_id=getattr(parent_engine, "session_id", ""),
 313:                 )
 314:                 if _skill_body:
 315:                     child_prompt = child_prompt + _skill_body
 316:         except Exception as _sk_exc:
 317:             logging.warning(
 318:                 "[subagent] verify-skill auto-load failed: %s", _sk_exc,
 319:             )
 320: 
 321:     # Block G iter-2 (Codex finding #1 BLOCKER): swap CONFIG.workspace to
 322:     # the worktree path so tools that read `CONFIG.workspace` (bash cwd,
 323:     # security path checks, edit_file allowed-paths) actually run inside
 324:     # the isolated worktree. Restore in finally so the parent sees its
 325:     # original workspace afterward â€” even if child.run raises.
 326:     _saved_workspace = None
 327:     if _worktree_path:
 328:         try:
 329:             from runtime.config import CONFIG as _CFG_S
 330:             _saved_workspace = _CFG_S.workspace
 331:             _CFG_S.workspace = _worktree_path
 332:             logging.debug(
 333:                 "[subagent] swapped CONFIG.workspace=%s -> %s for build agent",
 334:                 _saved_workspace, _worktree_path,
 335:             )
 336:         except Exception as _ws_exc:
 337:             logging.warning(
 338:                 "[subagent] CONFIG.workspace swap failed: %s", _ws_exc,
 339:             )
 340:             _saved_workspace = None
 341: 
 342:     try:
 343:         # The child runs synchronously to completion or budget exhaustion.
 344:         result = child.run(
 345:             user_message=p,
 346:             system_prompt=child_prompt,
 347:             tools=child_tools,
 348:             plan_mode=plan_mode,
 349:             output_fn=output_fn,
 350:         )
 351:     finally:
 352:         # Always restore parent's in-context set, even if child raised.
 353:         if _file_cache_saved is not None:
 354:             try:
 355:                 from runtime.file_cache import FILE_CACHE as _FC
 356:                 _FC.restore_context(_file_cache_saved)
 357:             except Exception:
 358:                 pass
 359:         # Block G iter-2 â€” restore CONFIG.workspace before worktree cleanup
 360:         # so subsequent parent-side tools see the original workspace again.
 361:         if _saved_workspace is not None:
 362:             try:
 363:                 from runtime.config import CONFIG as _CFG_S
 364:                 _CFG_S.workspace = _saved_workspace
 365:             except Exception:
 366:                 pass
 367:         # Block G â€” worktree cleanup on child completion (or failure).
 368:         # Best-effort; logs but doesn't block.
 369:         if _worktree_path:
 370:             try:
 371:                 from .worktree import cleanup_worktree
 372:                 cleanup_worktree(_worktree_path)
 373:             except Exception as _wt_cleanup_exc:
 374:                 logging.warning(
 375:                     "[subagent] worktree cleanup raised: %s", _wt_cleanup_exc,
 376:                 )
 377: 
 378:     # Defense-in-depth: confirm the parent buffer wasn't mutated. Structural
 379:     # comparison via the deep snapshot â€” catches in-place edits that preserve
 380:     # length as well as length-changing mutations.
 381:     if parent_engine.messages != parent_msgs_snapshot:
 382:         # This should never happen if the contract holds. Surface a clear
 383:         # error rather than silently corrupt parent state.
 384:         return SubagentResult(
 385:             text=result.text,
 386:             stop_reason="parent_context_mutated",
 387:             error=(
 388:                 "Internal error: parent_engine.messages was mutated by "
 389:                 "sub-agent dispatch. Phase-9 contract violated."
 390:             ),
 391:             child_messages=result.messages,
 392:             agent_type=agent_type,
 393:             depth=child_depth,
 394:         )
 395: 
 396:     return SubagentResult(
 397:         text=result.text,
 398:         stop_reason=result.stop_reason,
 399:         turns_used=result.turns_used,
 400:         child_messages=result.messages,
 401:         error=result.error,
 402:         agent_type=agent_type,
 403:         depth=child_depth,
 404:     )

codex
The workspace swap is present and restored in a `finally`, with the `if _worktree_path:` guard before mutation. I’m checking the tests now for whether they cover the exception/cleanup edge cases strongly enough and whether the allowlist assertions would catch a regression in actual spawned tool surfaces.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/tests/integration/test_block_g.py | ForEach-Object { '"'{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/_status/V5_RUNNABLE_PORT_LOG.md | ForEach-Object { if ($i -ge 80) { '"'{0,4}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff 543ebb6..HEAD -- compact_v5/MAIN/agent/subagent/agent_types.py compact_v5/MAIN/agent/subagent/spawn.py compact_v5/MAIN/agent/tools/task.py compact_v5/_status/V5_RUNNABLE_PORT_LOG.md compact_v5/MAIN/agent/tests/integration/test_block_g.py' in D:\Github\sagemaker-coding-agent
 succeeded in 496ms:
diff --git a/compact_v5/MAIN/agent/subagent/agent_types.py b/compact_v5/MAIN/agent/subagent/agent_types.py
index 4bd9698..e096f10 100644
--- a/compact_v5/MAIN/agent/subagent/agent_types.py
+++ b/compact_v5/MAIN/agent/subagent/agent_types.py
@@ -64,6 +64,22 @@ class AgentType:
     one_shot: bool = False
     auto_load_skill: Optional[str] = None
     needs_worktree: bool = False
+    # Block G iter-2 (Codex finding #2 HIGH): allowed_tools allowlist enforced
+    # at spawn time (was: prompt-only "Do NOT edit files" wording, which the
+    # model could ignore). When None, the child gets the full registry.
+    # When set, child_tools is filtered to this list before child.run.
+    allowed_tools: Optional[tuple] = None  # tuple for frozen-dataclass safety
+
+
+# Read-only tool allowlist for explore / plan / review (no file mutation,
+# no shell exec). semantic_search included because it's read-only.
+_READ_ONLY_TOOLS: tuple = (
+    "read_file", "grep", "glob", "list_dir", "view_image",
+    "todo_read", "todo_write", "semantic_search", "ask_user",
+)
+# Verify allowlist: read-only + bash (so verify can run pytest / lint /
+# build commands). NO edit/write tools.
+_VERIFY_TOOLS: tuple = _READ_ONLY_TOOLS + ("bash", "python_exec")
 
 
 # Block G-1: AGENT_TYPES dict — 7 entries per TEST_DESIGN test_agent_types_dict_has_7.
@@ -84,6 +100,7 @@ AGENT_TYPES: dict = {
         ),
         max_turns=20,
         one_shot=True,  # Block G-3: ONE_SHOT_BUILTIN_AGENT_TYPES
+        allowed_tools=_READ_ONLY_TOOLS,
     ),
     "plan": AgentType(
         name="plan",
@@ -96,6 +113,7 @@ AGENT_TYPES: dict = {
         ),
         max_turns=15,
         one_shot=True,
+        allowed_tools=_READ_ONLY_TOOLS,
     ),
     "verify": AgentType(
         name="verify",
@@ -109,6 +127,7 @@ AGENT_TYPES: dict = {
         max_turns=20,
         one_shot=True,
         auto_load_skill="verify",  # Block G — TEST_DESIGN row 3
+        allowed_tools=_VERIFY_TOOLS,  # read-only + bash + python_exec
     ),
     "build": AgentType(
         name="build",
@@ -134,6 +153,7 @@ AGENT_TYPES: dict = {
         ),
         max_turns=20,
         one_shot=True,
+        allowed_tools=_READ_ONLY_TOOLS,
     ),
     "fork": AgentType(
         name="fork",
diff --git a/compact_v5/MAIN/agent/subagent/spawn.py b/compact_v5/MAIN/agent/subagent/spawn.py
index 6ae6661..38002c5 100644
--- a/compact_v5/MAIN/agent/subagent/spawn.py
+++ b/compact_v5/MAIN/agent/subagent/spawn.py
@@ -242,11 +242,24 @@ def spawn_subagent(
     import copy
     parent_msgs_snapshot = copy.deepcopy(parent_engine.messages)
 
-    # Resolve the child's tool pool. Phase 9 keeps it simple: the child
-    # gets the full registry (subject to plan-mode if requested). Future
-    # phases may filter by AGENT_TYPES["tools"].
+    # Resolve the child's tool pool. Block G iter-2 (Codex finding #2 HIGH):
+    # specialized agents (explore/plan/verify/review) get a tool allowlist
+    # enforced at spawn — prompt-only "Do NOT edit files" wording was not a
+    # contract. When agent_def.allowed_tools is set, child_tools is filtered
+    # to that subset; otherwise the full registry is used.
     from tools import all_registered
     child_tools = all_registered()
+    if agent_def is not None and agent_def.allowed_tools:
+        _allow = set(agent_def.allowed_tools)
+        # Always include `task` so a plan/explore agent can still spawn
+        # further sub-agents (depth-limit gates separately).
+        # Always include `tool_search` so deferred-loading still works.
+        _allow.update({"task", "tool_search"})
+        child_tools = [t for t in child_tools if t.name in _allow]
+        logging.debug(
+            "[subagent] agent_type=%s tool allowlist (%d tools): %s",
+            agent_type, len(child_tools), sorted(t.name for t in child_tools),
+        )
 
     # Block B+ (PORT_LOG #053): save+clear FILE_CACHE main context
     # before the child runs so the child sees a fresh in-context set;
@@ -305,6 +318,27 @@ def spawn_subagent(
                 "[subagent] verify-skill auto-load failed: %s", _sk_exc,
             )
 
+    # Block G iter-2 (Codex finding #1 BLOCKER): swap CONFIG.workspace to
+    # the worktree path so tools that read `CONFIG.workspace` (bash cwd,
+    # security path checks, edit_file allowed-paths) actually run inside
+    # the isolated worktree. Restore in finally so the parent sees its
+    # original workspace afterward — even if child.run raises.
+    _saved_workspace = None
+    if _worktree_path:
+        try:
+            from runtime.config import CONFIG as _CFG_S
+            _saved_workspace = _CFG_S.workspace
+            _CFG_S.workspace = _worktree_path
+            logging.debug(
+                "[subagent] swapped CONFIG.workspace=%s -> %s for build agent",
+                _saved_workspace, _worktree_path,
+            )
+        except Exception as _ws_exc:
+            logging.warning(
+                "[subagent] CONFIG.workspace swap failed: %s", _ws_exc,
+            )
+            _saved_workspace = None
+
     try:
         # The child runs synchronously to completion or budget exhaustion.
         result = child.run(
@@ -322,6 +356,14 @@ def spawn_subagent(
                 _FC.restore_context(_file_cache_saved)
             except Exception:
                 pass
+        # Block G iter-2 — restore CONFIG.workspace before worktree cleanup
+        # so subsequent parent-side tools see the original workspace again.
+        if _saved_workspace is not None:
+            try:
+                from runtime.config import CONFIG as _CFG_S
+                _CFG_S.workspace = _saved_workspace
+            except Exception:
+                pass
         # Block G — worktree cleanup on child completion (or failure).
         # Best-effort; logs but doesn't block.
         if _worktree_path:
diff --git a/compact_v5/MAIN/agent/tests/integration/test_block_g.py b/compact_v5/MAIN/agent/tests/integration/test_block_g.py
index b1ca5a0..35ae588 100644
--- a/compact_v5/MAIN/agent/tests/integration/test_block_g.py
+++ b/compact_v5/MAIN/agent/tests/integration/test_block_g.py
@@ -358,6 +358,231 @@ def test_default_agent_prompt_has_no_gold_plating_phrasing():
     assert "refactor" in DEFAULT_AGENT_PROMPT.lower()
 
 
+# ============================================================
+# Codex iter-1 finding-lock tests
+# ============================================================
+
+def test_build_agent_actually_runs_inside_worktree(tmp_path):
+    """Codex iter-1 finding #1 BLOCKER lock: spawn_subagent must swap
+    CONFIG.workspace to the worktree path during child.run so tools
+    that read CONFIG.workspace (bash cwd, security path checks,
+    edit_file allowed-paths) actually execute inside the worktree.
+    Restored in finally so the parent sees its original workspace.
+    """
+    from core import QueryEngine
+    from core.budget import IterationBudget
+    from runtime.config import CONFIG
+    from subagent.spawn import spawn_subagent
+
+    workspace = str(tmp_path)
+    _saved_ws = CONFIG.workspace
+    CONFIG.workspace = workspace
+
+    # Capture CONFIG.workspace as observed by the child during chat.
+    seen_during_run = {}
+
+    class _ObservingClient:
+        def __init__(self):
+            self.calls = []
+            self.model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
+            self.mock_mode = True
+            self.script = [("text", "build done")]
+
+        def chat(self, messages, system, tools, max_tokens, temperature,
+                 thinking_enabled, thinking_budget):
+            from runtime.bedrock_client import Response
+            seen_during_run["cfg_ws"] = CONFIG.workspace
+            kind, *rest = self.script.pop(0)
+            return Response(text=rest[0], tool_calls=[],
+                            stop_reason="end_turn", usage={})
+
+    try:
+        client = _ObservingClient()
+        parent = QueryEngine(client=client, max_turns=5,
+                             budget=IterationBudget(max_iterations=10))
+        result = spawn_subagent(
+            parent_engine=parent,
+            prompt="build x",
+            agent_type="build",
+            workspace=workspace,
+        )
+        assert result.stop_reason == "end_turn"
+        # During child.run, CONFIG.workspace must point INTO the worktree.
+        assert "cfg_ws" in seen_during_run
+        observed = seen_during_run["cfg_ws"]
+        # Worktree path is somewhere under the requested workspace dir.
+        assert observed != workspace, (
+            "CONFIG.workspace must be swapped to worktree, not left as parent"
+        )
+        # Restored after spawn returns.
+        assert CONFIG.workspace == workspace, (
+            "CONFIG.workspace must be restored after build sub-agent completes"
+        )
+    finally:
+        CONFIG.workspace = _saved_ws
+
+
+def test_explore_agent_tool_allowlist_excludes_mutators():
+    """Codex iter-1 finding #2 HIGH lock: explore agent gets a read-only
+    allowlist enforced at spawn — write_file / edit_file / bash /
+    python_exec are NOT in the child's tool pool. Prompt-only
+    'Do NOT edit files' would not be a contract; this is.
+    """
+    from core import QueryEngine
+    from core.budget import IterationBudget
+    from subagent.spawn import spawn_subagent
+
+    seen_tools = {}
+
+    class _SnoopClient:
+        def __init__(self):
+            self.model_id = "x"
+            self.mock_mode = True
+
+        def chat(self, messages, system, tools, max_tokens, temperature,
+                 thinking_enabled, thinking_budget):
+            from runtime.bedrock_client import Response
+            seen_tools["names"] = {t["name"] for t in (tools or [])}
+            return Response(text="explored", tool_calls=[],
+                            stop_reason="end_turn", usage={})
+
+    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
+                         budget=IterationBudget(max_iterations=10))
+    spawn_subagent(parent, "explore x", agent_type="explore")
+    names = seen_tools.get("names", set())
+    # Mutating tools must be ABSENT.
+    for forbidden in ("write_file", "edit_file", "bash", "python_exec"):
+        assert forbidden not in names, (
+            f"explore agent must NOT see '{forbidden}' (Codex iter-1 #2)"
+        )
+    # Read-only tools must be PRESENT.
+    for required in ("read_file", "grep", "glob"):
+        assert required in names, (
+            f"explore agent must see '{required}'"
+        )
+
+
+def test_plan_agent_tool_allowlist_read_only():
+    """plan agent: same read-only allowlist as explore."""
+    from core import QueryEngine
+    from core.budget import IterationBudget
+    from subagent.spawn import spawn_subagent
+
+    seen_tools = {}
+
+    class _SnoopClient:
+        def __init__(self):
+            self.model_id = "x"
+            self.mock_mode = True
+
+        def chat(self, messages, system, tools, max_tokens, temperature,
+                 thinking_enabled, thinking_budget):
+            from runtime.bedrock_client import Response
+            seen_tools["names"] = {t["name"] for t in (tools or [])}
+            return Response(text="planned", tool_calls=[],
+                            stop_reason="end_turn", usage={})
+
+    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
+                         budget=IterationBudget(max_iterations=10))
+    spawn_subagent(parent, "plan x", agent_type="plan")
+    names = seen_tools.get("names", set())
+    for forbidden in ("write_file", "edit_file", "bash", "python_exec"):
+        assert forbidden not in names
+
+
+def test_verify_agent_allows_bash_but_not_mutators():
+    """verify agent: read-only + bash + python_exec (so it can run
+    pytest / lint / build), but NO file mutation tools."""
+    from core import QueryEngine
+    from core.budget import IterationBudget
+    from skills.manager import SkillManager
+    from subagent.spawn import spawn_subagent
+
+    seen_tools = {}
+
+    class _SnoopClient:
+        def __init__(self):
+            self.model_id = "x"
+            self.mock_mode = True
+
+        def chat(self, messages, system, tools, max_tokens, temperature,
+                 thinking_enabled, thinking_budget):
+            from runtime.bedrock_client import Response
+            seen_tools["names"] = {t["name"] for t in (tools or [])}
+            return Response(text="verified", tool_calls=[],
+                            stop_reason="end_turn", usage={})
+
+    import tempfile
+    with tempfile.TemporaryDirectory() as td:
+        # Set up a minimal SkillManager so verify-skill auto-load doesn't crash.
+        sm = SkillManager(workspace=td, skills_dir=td + "/skills")
+        sm.discover()
+        parent = QueryEngine(client=_SnoopClient(), max_turns=5,
+                             budget=IterationBudget(max_iterations=10),
+                             skill_manager=sm)
+        spawn_subagent(parent, "verify x", agent_type="verify")
+        names = seen_tools.get("names", set())
+        assert "bash" in names, "verify agent must have bash for running checks"
+        assert "python_exec" in names
+        for forbidden in ("write_file", "edit_file"):
+            assert forbidden not in names
+
+
+def test_general_agent_gets_full_registry():
+    """general agent (no allowed_tools allowlist) sees the full registry."""
+    from core import QueryEngine
+    from core.budget import IterationBudget
+    from subagent.spawn import spawn_subagent
+    from tools import all_registered
+
+    seen_tools = {}
+
+    class _SnoopClient:
+        def __init__(self):
+            self.model_id = "x"
+            self.mock_mode = True
+
+        def chat(self, messages, system, tools, max_tokens, temperature,
+                 thinking_enabled, thinking_budget):
+            from runtime.bedrock_client import Response
+            seen_tools["names"] = {t["name"] for t in (tools or [])}
+            return Response(text="ok", tool_calls=[],
+                            stop_reason="end_turn", usage={})
+
+    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
+                         budget=IterationBudget(max_iterations=10))
+    spawn_subagent(parent, "x", agent_type="general")
+    names = seen_tools.get("names", set())
+    full = {t.name for t in all_registered()}
+    # general gets the full set (or close to it — all_registered may include
+    # tool_search which is always promoted; subset check from below).
+    # All write/exec tools available for general.
+    for required in ("write_file", "edit_file", "bash", "python_exec",
+                     "read_file", "grep"):
+        assert required in names or required in full
+
+
+def test_task_tool_schema_lists_all_7_agent_types():
+    """Codex iter-1 finding #3 MEDIUM lock: tools/task.py JSON schema
+    `subagent_type` enum lists all 7 agent types AGENT_TYPES.keys() — not
+    just 'general'."""
+    from tools import all_registered
+    from subagent import AGENT_TYPES
+
+    task_tool = next((t for t in all_registered() if t.name == "task"), None)
+    assert task_tool is not None
+    schema = task_tool.input_schema
+    enum = schema["properties"]["subagent_type"].get("enum", [])
+    assert set(enum) == set(AGENT_TYPES.keys()), (
+        f"task tool subagent_type enum {set(enum)} must == AGENT_TYPES.keys() "
+        f"{set(AGENT_TYPES.keys())} (Codex iter-1 #3)"
+    )
+    # Description should mention each major type.
+    desc = schema["properties"]["subagent_type"].get("description", "")
+    for at in ("explore", "plan", "verify", "build"):
+        assert at in desc, f"task tool subagent_type description must mention {at!r}"
+
+
 def test_agent_max_turns_clamped_by_per_type_ceiling():
     """spawn_subagent clamps max_turns to min(caller-supplied, agent_type ceiling)."""
     from core import QueryEngine
diff --git a/compact_v5/MAIN/agent/tools/task.py b/compact_v5/MAIN/agent/tools/task.py
index b7c0462..f6244b3 100644
--- a/compact_v5/MAIN/agent/tools/task.py
+++ b/compact_v5/MAIN/agent/tools/task.py
@@ -45,7 +45,14 @@ Do NOT use a sub-agent when:
 Inputs:
 - description: 1-line summary shown to the user.
 - prompt: the actual task description for the sub-agent. Be specific.
-- subagent_type: "general" (default; full tool access). Other types are reserved for future phases.
+- subagent_type: one of `general` | `explore` | `plan` | `verify` | `build` | `review` | `fork` (default `general`).
+  - `general` — full tool access; default.
+  - `explore` — read-only exploration (no edit/write/exec); produces a report.
+  - `plan` — read-only planning (no edit/write/exec); produces a step-by-step plan.
+  - `verify` — read + bash; auto-loads the `verify` skill; runs gate checks.
+  - `build` — full tools, runs in isolated git worktree.
+  - `review` — read-only code review; surfaces concrete issues with file:line.
+  - `fork` — inherits parent context conceptually; full tools.
 
 Returns the sub-agent's final answer as a string. If the sub-agent hits its iteration budget or max_turns, the partial work + reason is returned."""
 
@@ -63,7 +70,9 @@ _INPUT_SCHEMA: Dict[str, Any] = {
         },
         "subagent_type": {
             "type": "string",
-            "description": "Agent type. 'general' (default) for full tool access. Other types reserved for future phases.",
+            "enum": ["general", "explore", "plan", "verify", "build", "review", "fork"],
+            "default": "general",
+            "description": "Agent type. general (default; full tools) | explore (read-only) | plan (read-only) | verify (read + bash + auto-loads verify skill) | build (full + isolated git worktree) | review (read-only code review) | fork (full tools, parent-context).",
         },
     },
     "required": ["prompt"],
diff --git a/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md b/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
index 3aa457b..5d112a2 100644
--- a/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
+++ b/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
@@ -140,6 +140,8 @@ Format: one row per Runnable pattern adopted. Never delete rows. Mark superseded
 | 086 | 2026-05-03 | Block G (G-1, G-3, G-4, G-6, G-7) | v4 sagemaker_agent.py:6914-7090 (AGENT_TYPES dict) + Runnable AgentTool/constants.ts:9-12 (ONE_SHOT_BUILTIN_AGENT_TYPES) + AgentTool/prompt.ts:202-213 (getPrompt(isCoordinator)) + constants/prompts.ts:758 (DEFAULT_AGENT_PROMPT) + :766-770 (Notes) | compact_v5/MAIN/agent/subagent/agent_types.py: AGENT_TYPES dict (7 entries: build/plan/explore/verify/general/review/fork) + AgentType dataclass + DEFAULT_AGENT_PROMPT verbatim + SUBAGENT_NOTES + ONE_SHOT_BUILTIN_AGENT_TYPES frozenset + get_agent_type / get_agent_prompt(is_coordinator) | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Per-type max_turns + one_shot + auto_load_skill + needs_worktree knobs. coordinator-mode slim prompt drops Notes appendix (Block G3 will reuse). Lock tests: 4 in test_block_g.py (dict-has-7 / one-shot-set / coordinator-drops-notes / default-agent-prompt-no-gold-plating). ADR-031. |
 | 087 | 2026-05-03 | Block G (worktree) | v4 sagemaker_agent.py:8413+ (build agent worktree spawn) | compact_v5/MAIN/agent/subagent/worktree.py: create_worktree() / cleanup_worktree() + git/fallback_copy/fallback_tempdir tiers | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Best-effort: never raises into spawn loop; falls back to fallback_copy or tempdir if git unavailable. Wired into spawn_subagent: agent_def.needs_worktree → create_worktree before child.run, cleanup_worktree in finally clause. Lock tests: build-spawns-worktree + worktree-cleanup-on-completion. ADR-031. |
 | 088 | 2026-05-03 | Block G (spawn dispatch + verify auto-load) | v4 sagemaker_agent.py:8366+ | compact_v5/MAIN/agent/subagent/spawn.py:_resolve_agent_suffix consults agent_types.get_agent_type; spawn_subagent applies per-type max_turns ceiling + worktree creation + verify-skill auto-load before child.run; tools/task.py validation uses AGENT_TYPES | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Replaced Phase-9 placeholder _AGENT_TYPE_SUFFIXES (general-only) with full registry lookup. Per-type max_turns clamped to caller-supplied. verify-skill auto-load: parent.skill_manager.activate(agent_def.auto_load_skill) + body spliced into child_prompt before run. Lock tests: 14 in test_block_g.py covering 8 TEST_DESIGN rows + 6 behavior locks. ADR-031. |
+| 089 | 2026-05-03 | Block G iter-2 (Codex iter-1 fixes) | Codex iter-1 BLOCKER + HIGH + MEDIUM + DOC findings | compact_v5/MAIN/agent/subagent/agent_types.py: AgentType.allowed_tools field + _READ_ONLY_TOOLS / _VERIFY_TOOLS allowlists; spawn.py: tool allowlist filtering + CONFIG.workspace swap into worktree during child.run with restore in finally; tools/task.py: JSON-schema enum + description listing all 7 types | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | (a) BLOCKER fix: build agents now actually run inside the worktree — CONFIG.workspace temporarily swapped + restored in finally. (b) HIGH fix: explore/plan/review get _READ_ONLY_TOOLS allowlist (no edit/write/exec); verify gets _VERIFY_TOOLS (read + bash + python_exec, no edit/write); general/build/fork get full registry. Always include task + tool_search across the board for legitimate sub-spawn / deferred-loading. (c) MEDIUM fix: tools/task.py subagent_type now has JSON-schema enum=AGENT_TYPES.keys() + description lists all 7. (d) DOC fix: see PORT_LOG #090. Lock tests: 6 added (build-runs-in-worktree / explore-allowlist / plan-allowlist / verify-allowlist / general-full-registry / task-schema-lists-7). ADR-031. |
+| 090 | 2026-05-03 | Block G (G-1, G-2 explicit deferral) | Runnable AgentTool/agentMemory.ts:138-177 (G-1 loadAgentMemoryPrompt) + :68-104 (G-2 isAgentMemoryPath) | (deferred — lands in Block H) | DEFER | (no code change) | (n/a) | (n/a) | Codex Block G iter-1 AXIS C closure. Per ADR-031 §Notes: G-1 (per-agent-scoped memory.md) + G-2 (path-traversal-safe agent memory paths) belong with Block H's memory extraction infrastructure (extractMemories.ts) where `loadAgentMemoryPrompt` is called. Deferring to Block H ensures the memory subsystem is built end-to-end as one architectural unit rather than splitting the API across two blocks. Lock test for G-2 path-traversal will land in Block H's test suite. NO silent scope narrowing — explicit deferral with target-Block + linked source file:line. |
 | 083 | 2026-05-03 | Block I (Axis C closure) | Codex Block I iter-1 AXIS C — undeclared cross-references | _status/V5_RUNNABLE_PORT_LOG.md (this row) + ADR-029 §6 | doc-only | PASS | (no code change) | 43d1ebe | Codex iter-1 AXIS C cleanup row. (a) **I-12 frontmatter parser improvements** (R8 #24, #50): DEFERRED to Block N per ADR-029 §6 (architectural fit — frontmatter expansion lands with Block N's dynamic-section + AGENTS.md infrastructure). (b) **Wave 6 row #93** (`PORT_LOG enumerates skills/verify/ as bundled`): closed via existing PORT_LOG #029 (Phase-10 byte-for-byte copy of 10 v4 production skills including verify). Block I makes no change to the bundled set; Phase-10 row is the canonical evidence. (c) **Wave 6 gap #8 — tool-vs-skill precedence** (PS_Plan_Edge_Cases_Thinking.md #93 / W6_multi_file_tasks.md:327-371): v5 disposition is **tools win for offline SageMaker / Bedrock-only deployments** because Block T's document tools (create_word, create_excel, create_chart, etc.) are zero-network-dependency and run inside the agent process; bundled skills (Runnable's debug, remember, etc.) are designed for the network-rich Anthropic-API-direct world and may reference tools that v5 doesn't ship (constraint #9 + #10). The model resolves a request by: (1) check direct tool registry first; (2) if no tool fits, check active skill body; (3) only suggest /skill use <name> when the user's task explicitly maps to a skill's CSO description. Block I lands the bundled debug + remember skills but they are auxiliary surfaces, not replacements for tools. ADR-029. |
 
 **Phase 10 acceptance** (V5_PLAN.md): "all 10 skills load; auto-trigger respects v4.9.6 default-OFF." Both validated:

 succeeded in 542ms:
   1: """Block G â€” AGENT_TYPES + worktree + handoff/env.
   2: 
   3: Source:
   4: - v4 sagemaker_agent.py:6914-7090 (AGENT_TYPES dict, ~176 LOC)
   5: - v4 sagemaker_agent.py:8413+ (worktree spawn for build, ~57 LOC)
   6: - Runnable AgentTool/constants.ts (ONE_SHOT_BUILTIN_AGENT_TYPES)
   7: - Runnable AgentTool/prompt.ts:202-213 (getPrompt(isCoordinator))
   8: - Runnable constants/prompts.ts:758 (DEFAULT_AGENT_PROMPT) + :766-770 (Notes)
   9: 
  10: Tests per TEST_DESIGN Â§Block G (8 T1+T2 tests, $0):
  11: - test_agent_types_dict_has_7
  12: - test_subagent_build_spawns_worktree
  13: - test_subagent_verify_loads_verify_skill
  14: - test_subagent_handoff_block_built
  15: - test_subagent_env_details_built
  16: - test_max_subagent_depth_2_blocks_grandchild
  17: - test_iteration_budget_shared_object_identity
  18: - test_worktree_cleanup_on_completion
  19: """
  20: from __future__ import annotations
  21: 
  22: import os
  23: import sys
  24: 
  25: import pytest
  26: 
  27: _AGENT_ROOT = os.path.dirname(
  28:     os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  29: )
  30: if _AGENT_ROOT not in sys.path:
  31:     sys.path.insert(0, _AGENT_ROOT)
  32: 
  33: 
  34: # ============================================================
  35: # Scripted client + fixtures
  36: # ============================================================
  37: 
  38: class _ScriptedClient:
  39:     def __init__(self, script):
  40:         self.script = list(script)
  41:         self.calls = []
  42:         self.model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
  43:         self.mock_mode = True
  44: 
  45:     def chat(self, messages, system, tools, max_tokens, temperature,
  46:              thinking_enabled, thinking_budget):
  47:         from runtime.bedrock_client import Response
  48:         self.calls.append({"system": system, "messages": list(messages)})
  49:         if not self.script:
  50:             return Response(text="(end)", tool_calls=[],
  51:                             stop_reason="end_turn", usage={})
  52:         kind, *rest = self.script.pop(0)
  53:         if kind == "text":
  54:             return Response(text=rest[0], tool_calls=[],
  55:                             stop_reason="end_turn", usage={})
  56:         raise AssertionError(f"unknown kind {kind}")
  57: 
  58: 
  59: @pytest.fixture(autouse=True)
  60: def fresh_registry():
  61:     from tools.registry import _reset_registry_for_tests
  62:     from tools import bootstrap_built_ins
  63:     _reset_registry_for_tests()
  64:     bootstrap_built_ins()
  65:     yield
  66: 
  67: 
  68: # ============================================================
  69: # TEST_DESIGN row 1 â€” AGENT_TYPES has exactly 7 entries
  70: # ============================================================
  71: 
  72: def test_agent_types_dict_has_7():
  73:     """AGENT_TYPES.keys() == {build, plan, explore, verify, general, review, fork}."""
  74:     from subagent import AGENT_TYPES
  75: 
  76:     expected = {"build", "plan", "explore", "verify", "general", "review", "fork"}
  77:     assert set(AGENT_TYPES.keys()) == expected
  78:     assert len(AGENT_TYPES) == 7
  79: 
  80: 
  81: def test_one_shot_builtin_agent_types_has_explore_plan_verify_review():
  82:     """Block G-3 lock: ONE_SHOT_BUILTIN_AGENT_TYPES (Runnable parity)
  83:     skips the agentId/SendMessage/usage trailer for one-shot agents."""
  84:     from subagent import ONE_SHOT_BUILTIN_AGENT_TYPES
  85: 
  86:     # Per agent_types.py: explore, plan, verify, review are one-shot.
  87:     # general, build, fork are not.
  88:     assert "explore" in ONE_SHOT_BUILTIN_AGENT_TYPES
  89:     assert "plan" in ONE_SHOT_BUILTIN_AGENT_TYPES
  90:     assert "verify" in ONE_SHOT_BUILTIN_AGENT_TYPES
  91:     assert "review" in ONE_SHOT_BUILTIN_AGENT_TYPES
  92:     assert "general" not in ONE_SHOT_BUILTIN_AGENT_TYPES
  93:     assert "build" not in ONE_SHOT_BUILTIN_AGENT_TYPES
  94:     assert "fork" not in ONE_SHOT_BUILTIN_AGENT_TYPES
  95: 
  96: 
  97: # ============================================================
  98: # TEST_DESIGN row 2 â€” build agent spawns worktree
  99: # ============================================================
 100: 
 101: def test_subagent_build_spawns_worktree(tmp_path, monkeypatch):
 102:     """task(subagent_type=\"build\") creates worktrees/<id>/ (mocked git)."""
 103:     from core import QueryEngine
 104:     from core.budget import IterationBudget
 105:     from subagent.spawn import spawn_subagent
 106:     from subagent.worktree import WORKTREE_SUBDIR
 107: 
 108:     # Use tmp_path as the workspace; non-git so we get the fallback_copy path.
 109:     workspace = str(tmp_path)
 110: 
 111:     client = _ScriptedClient([("text", "build done")])
 112:     parent = QueryEngine(client=client, max_turns=5,
 113:                          budget=IterationBudget(max_iterations=20))
 114: 
 115:     result = spawn_subagent(
 116:         parent_engine=parent,
 117:         prompt="build something",
 118:         agent_type="build",
 119:         workspace=workspace,
 120:     )
 121:     assert result.stop_reason == "end_turn"
 122: 
 123:     # The worktree directory should have been created under workspace.
 124:     wt_root = os.path.join(workspace, WORKTREE_SUBDIR)
 125:     # Directory should exist (created by create_worktree); cleanup may have
 126:     # removed the inner <id>/ dir but the parent worktrees/ dir persists.
 127:     # Codex review note: cleanup_worktree removes the inner dir; the test
 128:     # asserts the WORKTREE_SUBDIR was created at all.
 129:     assert os.path.isdir(wt_root), (
 130:         f"Expected worktrees/ dir at {wt_root} after build agent spawn"
 131:     )
 132: 
 133: 
 134: # ============================================================
 135: # TEST_DESIGN row 3 â€” verify agent loads verify skill
 136: # ============================================================
 137: 
 138: def test_subagent_verify_loads_verify_skill(tmp_path):
 139:     """task(subagent_type=\"verify\") loads verify skill in sub-agent context.
 140: 
 141:     The parent's SkillManager has the verify skill activated and its body
 142:     is spliced into the child's system prompt (visible in the chat call's
 143:     `system` arg).
 144:     """
 145:     from core import QueryEngine
 146:     from core.budget import IterationBudget
 147:     from skills.manager import SkillManager
 148:     from subagent.spawn import spawn_subagent
 149: 
 150:     # Set up an isolated SkillManager with a verify skill.
 151:     skills_dir = tmp_path / "skills"
 152:     skills_dir.mkdir()
 153:     verify_dir = skills_dir / "verify"
 154:     verify_dir.mkdir()
 155:     (verify_dir / "SKILL.md").write_text(
 156:         "---\nname: verify\ndescription: Use when running gate checks.\n---\n"
 157:         "Run gate checks: pytest, lint, build.",
 158:         encoding="utf-8",
 159:     )
 160:     sm = SkillManager(workspace=str(tmp_path), skills_dir=str(skills_dir))
 161:     sm.discover()
 162: 
 163:     client = _ScriptedClient([("text", "PASS all gates")])
 164:     parent = QueryEngine(
 165:         client=client, max_turns=5,
 166:         budget=IterationBudget(max_iterations=10),
 167:         skill_manager=sm,
 168:     )
 169:     spawn_subagent(
 170:         parent_engine=parent,
 171:         prompt="verify the build",
 172:         agent_type="verify",
 173:     )
 174: 
 175:     # The chat() call's `system` arg must contain the verify skill body.
 176:     assert len(client.calls) >= 1
 177:     sys_prompt = client.calls[0]["system"]
 178:     assert "Active Skill: verify" in sys_prompt or "Run gate checks" in sys_prompt
 179:     assert sm.active_skill == "verify"
 180: 
 181: 
 182: # ============================================================
 183: # TEST_DESIGN row 4 â€” handoff block builds
 184: # ============================================================
 185: 
 186: def test_subagent_handoff_block_built():
 187:     """_build_subagent_handoff_block produces v4-equivalent text."""
 188:     from subagent.handoff import build_handoff_block
 189: 
 190:     block = build_handoff_block(
 191:         status_path="/tmp/STATUS.md",
 192:         todos_text="- [ ] Fix bug\n- [x] Write test",
 193:         recent_files=["src/foo.py", "tests/test_foo.py"],
 194:     )
 195:     # Some recognizable handoff structure.
 196:     assert isinstance(block, str)
 197:     assert len(block) > 0
 198:     # Either status path or todos appear when supplied.
 199:     assert "STATUS" in block or "todos" in block.lower() or "handoff" in block.lower()
 200: 
 201: 
 202: def test_subagent_handoff_block_empty_when_no_inputs():
 203:     from subagent.handoff import build_handoff_block
 204: 
 205:     block = build_handoff_block(
 206:         status_path=None, todos_text=None, recent_files=None,
 207:     )
 208:     # No inputs â†’ empty / minimal block.
 209:     assert isinstance(block, str)
 210: 
 211: 
 212: # ============================================================
 213: # TEST_DESIGN row 5 â€” env_details builds
 214: # ============================================================
 215: 
 216: def test_subagent_env_details_built():
 217:     """_build_subagent_env_details includes cwd + git status + tool list."""
 218:     from subagent.env import build_env_details
 219: 
 220:     body = build_env_details(
 221:         agent_type="general",
 222:         depth=1,
 223:         max_depth=2,
 224:     )
 225:     assert isinstance(body, str)
 226:     assert len(body) > 0
 227:     # Per env.py contract: includes agent_type, depth, max_depth references.
 228:     assert "general" in body or "agent_type" in body.lower()
 229: 
 230: 
 231: # ============================================================
 232: # TEST_DESIGN row 6 â€” max depth 2 blocks grandchild (Wave 6 GAP fix)
 233: # ============================================================
 234: 
 235: def test_max_subagent_depth_2_blocks_grandchild():
 236:     """parent â†’ child OK; child â†’ grandchild blocked with depth-limit error."""
 237:     from core import QueryEngine
 238:     from core.budget import IterationBudget
 239:     from subagent.spawn import spawn_subagent
 240: 
 241:     client = _ScriptedClient([("text", "child says hi")])
 242:     parent = QueryEngine(client=client, max_turns=5,
 243:                          budget=IterationBudget(max_iterations=10))
 244: 
 245:     # Spawn at depth=1 (parent_depth=0 â†’ child_depth=1) â€” OK.
 246:     result1 = spawn_subagent(
 247:         parent_engine=parent, prompt="child", agent_type="general",
 248:         parent_depth=0, max_depth=2,
 249:     )
 250:     assert result1.depth == 1
 251:     assert result1.stop_reason == "end_turn"
 252: 
 253:     # Now simulate child trying to spawn grandchild (parent_depth=2 means
 254:     # child_depth=3, which exceeds max_depth=2).
 255:     result2 = spawn_subagent(
 256:         parent_engine=parent, prompt="gc", agent_type="general",
 257:         parent_depth=2, max_depth=2,
 258:     )
 259:     assert result2.stop_reason == "depth_exceeded"
 260:     assert "depth limit" in (result2.error or "").lower()
 261: 
 262: 
 263: # ============================================================
 264: # TEST_DESIGN row 7 â€” IterationBudget shared object identity
 265: # ============================================================
 266: 
 267: def test_iteration_budget_shared_object_identity():
 268:     """parent and sub-agent share SAME IterationBudget object."""
 269:     from core import QueryEngine
 270:     from core.budget import IterationBudget
 271:     from subagent.spawn import _new_child_engine
 272: 
 273:     parent_budget = IterationBudget(max_iterations=10)
 274:     parent = QueryEngine(client=_ScriptedClient([]), max_turns=5,
 275:                          budget=parent_budget)
 276:     child = _new_child_engine(parent, max_turns=5, agent_type="general")
 277:     # Object identity check (not equality) â€” Phase 9 contract.
 278:     assert child.budget is parent_budget
 279:     assert child.budget is parent.budget
 280: 
 281: 
 282: # ============================================================
 283: # TEST_DESIGN row 8 â€” worktree cleanup on completion
 284: # ============================================================
 285: 
 286: def test_worktree_cleanup_on_completion(tmp_path):
 287:     """sub-agent completion removes worktree."""
 288:     from core import QueryEngine
 289:     from core.budget import IterationBudget
 290:     from subagent.spawn import spawn_subagent
 291:     from subagent.worktree import WORKTREE_SUBDIR
 292: 
 293:     workspace = str(tmp_path)
 294: 
 295:     client = _ScriptedClient([("text", "build done")])
 296:     parent = QueryEngine(client=client, max_turns=5,
 297:                          budget=IterationBudget(max_iterations=10))
 298: 
 299:     result = spawn_subagent(
 300:         parent_engine=parent,
 301:         prompt="build x",
 302:         agent_type="build",
 303:         workspace=workspace,
 304:     )
 305:     assert result.stop_reason == "end_turn"
 306: 
 307:     # cleanup_worktree should have removed the inner <id>/ dir; only the
 308:     # worktrees/ parent dir persists (or is empty).
 309:     wt_root = os.path.join(workspace, WORKTREE_SUBDIR)
 310:     if os.path.isdir(wt_root):
 311:         # Empty after cleanup (or only contains zero or one stale dir if
 312:         # cleanup partially failed). The strict assertion: no inner dirs.
 313:         children = [c for c in os.listdir(wt_root) if not c.startswith(".")]
 314:         assert len(children) == 0, (
 315:             f"worktree cleanup failed; leftover: {children}"
 316:         )
 317: 
 318: 
 319: # ============================================================
 320: # Behavioral lock tests
 321: # ============================================================
 322: 
 323: def test_unknown_agent_type_returns_explicit_error():
 324:     """spawn_subagent on unknown type returns SubagentResult with
 325:     stop_reason=invalid_args, NOT silent fallback to general."""
 326:     from core import QueryEngine
 327:     from core.budget import IterationBudget
 328:     from subagent.spawn import spawn_subagent
 329: 
 330:     parent = QueryEngine(client=_ScriptedClient([]), max_turns=5,
 331:                          budget=IterationBudget(max_iterations=10))
 332: 
 333:     result = spawn_subagent(
 334:         parent_engine=parent, prompt="x", agent_type="nonexistent_type",
 335:     )
 336:     assert result.stop_reason == "invalid_args"
 337:     assert "unknown agent_type" in (result.error or "").lower()
 338: 
 339: 
 340: def test_get_agent_prompt_coordinator_drops_notes():
 341:     """Block G-4 lock: get_agent_prompt(name, is_coordinator=True) drops
 342:     the Notes appendix (coordinator system prompt covers usage notes)."""
 343:     from subagent.agent_types import get_agent_prompt, SUBAGENT_NOTES
 344: 
 345:     full = get_agent_prompt("general", is_coordinator=False)
 346:     slim = get_agent_prompt("general", is_coordinator=True)
 347:     assert SUBAGENT_NOTES in full
 348:     assert SUBAGENT_NOTES not in slim
 349: 
 350: 
 351: def test_default_agent_prompt_has_no_gold_plating_phrasing():
 352:     """Block G-6 lock: DEFAULT_AGENT_PROMPT contains the battle-tested
 353:     'don't gold-plate' wording from Runnable constants/prompts.ts:758."""
 354:     from subagent.agent_types import DEFAULT_AGENT_PROMPT
 355: 
 356:     # Battle-tested phrasing â€” agents must not over-engineer.
 357:     assert "Do NOT add features" in DEFAULT_AGENT_PROMPT
 358:     assert "refactor" in DEFAULT_AGENT_PROMPT.lower()
 359: 
 360: 
 361: # ============================================================
 362: # Codex iter-1 finding-lock tests
 363: # ============================================================
 364: 
 365: def test_build_agent_actually_runs_inside_worktree(tmp_path):
 366:     """Codex iter-1 finding #1 BLOCKER lock: spawn_subagent must swap
 367:     CONFIG.workspace to the worktree path during child.run so tools
 368:     that read CONFIG.workspace (bash cwd, security path checks,
 369:     edit_file allowed-paths) actually execute inside the worktree.
 370:     Restored in finally so the parent sees its original workspace.
 371:     """
 372:     from core import QueryEngine
 373:     from core.budget import IterationBudget
 374:     from runtime.config import CONFIG
 375:     from subagent.spawn import spawn_subagent
 376: 
 377:     workspace = str(tmp_path)
 378:     _saved_ws = CONFIG.workspace
 379:     CONFIG.workspace = workspace
 380: 
 381:     # Capture CONFIG.workspace as observed by the child during chat.
 382:     seen_during_run = {}
 383: 
 384:     class _ObservingClient:
 385:         def __init__(self):
 386:             self.calls = []
 387:             self.model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
 388:             self.mock_mode = True
 389:             self.script = [("text", "build done")]
 390: 
 391:         def chat(self, messages, system, tools, max_tokens, temperature,
 392:                  thinking_enabled, thinking_budget):
 393:             from runtime.bedrock_client import Response
 394:             seen_during_run["cfg_ws"] = CONFIG.workspace
 395:             kind, *rest = self.script.pop(0)
 396:             return Response(text=rest[0], tool_calls=[],
 397:                             stop_reason="end_turn", usage={})
 398: 
 399:     try:
 400:         client = _ObservingClient()
 401:         parent = QueryEngine(client=client, max_turns=5,
 402:                              budget=IterationBudget(max_iterations=10))
 403:         result = spawn_subagent(
 404:             parent_engine=parent,
 405:             prompt="build x",
 406:             agent_type="build",
 407:             workspace=workspace,
 408:         )
 409:         assert result.stop_reason == "end_turn"
 410:         # During child.run, CONFIG.workspace must point INTO the worktree.
 411:         assert "cfg_ws" in seen_during_run
 412:         observed = seen_during_run["cfg_ws"]
 413:         # Worktree path is somewhere under the requested workspace dir.
 414:         assert observed != workspace, (
 415:             "CONFIG.workspace must be swapped to worktree, not left as parent"
 416:         )
 417:         # Restored after spawn returns.
 418:         assert CONFIG.workspace == workspace, (
 419:             "CONFIG.workspace must be restored after build sub-agent completes"
 420:         )
 421:     finally:
 422:         CONFIG.workspace = _saved_ws
 423: 
 424: 
 425: def test_explore_agent_tool_allowlist_excludes_mutators():
 426:     """Codex iter-1 finding #2 HIGH lock: explore agent gets a read-only
 427:     allowlist enforced at spawn â€” write_file / edit_file / bash /
 428:     python_exec are NOT in the child's tool pool. Prompt-only
 429:     'Do NOT edit files' would not be a contract; this is.
 430:     """
 431:     from core import QueryEngine
 432:     from core.budget import IterationBudget
 433:     from subagent.spawn import spawn_subagent
 434: 
 435:     seen_tools = {}
 436: 
 437:     class _SnoopClient:
 438:         def __init__(self):
 439:             self.model_id = "x"
 440:             self.mock_mode = True
 441: 
 442:         def chat(self, messages, system, tools, max_tokens, temperature,
 443:                  thinking_enabled, thinking_budget):
 444:             from runtime.bedrock_client import Response
 445:             seen_tools["names"] = {t["name"] for t in (tools or [])}
 446:             return Response(text="explored", tool_calls=[],
 447:                             stop_reason="end_turn", usage={})
 448: 
 449:     parent = QueryEngine(client=_SnoopClient(), max_turns=5,
 450:                          budget=IterationBudget(max_iterations=10))
 451:     spawn_subagent(parent, "explore x", agent_type="explore")
 452:     names = seen_tools.get("names", set())
 453:     # Mutating tools must be ABSENT.
 454:     for forbidden in ("write_file", "edit_file", "bash", "python_exec"):
 455:         assert forbidden not in names, (
 456:             f"explore agent must NOT see '{forbidden}' (Codex iter-1 #2)"
 457:         )
 458:     # Read-only tools must be PRESENT.
 459:     for required in ("read_file", "grep", "glob"):
 460:         assert required in names, (
 461:             f"explore agent must see '{required}'"
 462:         )
 463: 
 464: 
 465: def test_plan_agent_tool_allowlist_read_only():
 466:     """plan agent: same read-only allowlist as explore."""
 467:     from core import QueryEngine
 468:     from core.budget import IterationBudget
 469:     from subagent.spawn import spawn_subagent
 470: 
 471:     seen_tools = {}
 472: 
 473:     class _SnoopClient:
 474:         def __init__(self):
 475:             self.model_id = "x"
 476:             self.mock_mode = True
 477: 
 478:         def chat(self, messages, system, tools, max_tokens, temperature,
 479:                  thinking_enabled, thinking_budget):
 480:             from runtime.bedrock_client import Response
 481:             seen_tools["names"] = {t["name"] for t in (tools or [])}
 482:             return Response(text="planned", tool_calls=[],
 483:                             stop_reason="end_turn", usage={})
 484: 
 485:     parent = QueryEngine(client=_SnoopClient(), max_turns=5,
 486:                          budget=IterationBudget(max_iterations=10))
 487:     spawn_subagent(parent, "plan x", agent_type="plan")
 488:     names = seen_tools.get("names", set())
 489:     for forbidden in ("write_file", "edit_file", "bash", "python_exec"):
 490:         assert forbidden not in names
 491: 
 492: 
 493: def test_verify_agent_allows_bash_but_not_mutators():
 494:     """verify agent: read-only + bash + python_exec (so it can run
 495:     pytest / lint / build), but NO file mutation tools."""
 496:     from core import QueryEngine
 497:     from core.budget import IterationBudget
 498:     from skills.manager import SkillManager
 499:     from subagent.spawn import spawn_subagent
 500: 
 501:     seen_tools = {}
 502: 
 503:     class _SnoopClient:
 504:         def __init__(self):
 505:             self.model_id = "x"
 506:             self.mock_mode = True
 507: 
 508:         def chat(self, messages, system, tools, max_tokens, temperature,
 509:                  thinking_enabled, thinking_budget):
 510:             from runtime.bedrock_client import Response
 511:             seen_tools["names"] = {t["name"] for t in (tools or [])}
 512:             return Response(text="verified", tool_calls=[],
 513:                             stop_reason="end_turn", usage={})
 514: 
 515:     import tempfile
 516:     with tempfile.TemporaryDirectory() as td:
 517:         # Set up a minimal SkillManager so verify-skill auto-load doesn't crash.
 518:         sm = SkillManager(workspace=td, skills_dir=td + "/skills")
 519:         sm.discover()
 520:         parent = QueryEngine(client=_SnoopClient(), max_turns=5,
 521:                              budget=IterationBudget(max_iterations=10),
 522:                              skill_manager=sm)
 523:         spawn_subagent(parent, "verify x", agent_type="verify")
 524:         names = seen_tools.get("names", set())
 525:         assert "bash" in names, "verify agent must have bash for running checks"
 526:         assert "python_exec" in names
 527:         for forbidden in ("write_file", "edit_file"):
 528:             assert forbidden not in names
 529: 
 530: 
 531: def test_general_agent_gets_full_registry():
 532:     """general agent (no allowed_tools allowlist) sees the full registry."""
 533:     from core import QueryEngine
 534:     from core.budget import IterationBudget
 535:     from subagent.spawn import spawn_subagent
 536:     from tools import all_registered
 537: 
 538:     seen_tools = {}
 539: 
 540:     class _SnoopClient:
 541:         def __init__(self):
 542:             self.model_id = "x"
 543:             self.mock_mode = True
 544: 
 545:         def chat(self, messages, system, tools, max_tokens, temperature,
 546:                  thinking_enabled, thinking_budget):
 547:             from runtime.bedrock_client import Response
 548:             seen_tools["names"] = {t["name"] for t in (tools or [])}
 549:             return Response(text="ok", tool_calls=[],
 550:                             stop_reason="end_turn", usage={})
 551: 
 552:     parent = QueryEngine(client=_SnoopClient(), max_turns=5,
 553:                          budget=IterationBudget(max_iterations=10))
 554:     spawn_subagent(parent, "x", agent_type="general")
 555:     names = seen_tools.get("names", set())
 556:     full = {t.name for t in all_registered()}
 557:     # general gets the full set (or close to it â€” all_registered may include
 558:     # tool_search which is always promoted; subset check from below).
 559:     # All write/exec tools available for general.
 560:     for required in ("write_file", "edit_file", "bash", "python_exec",
 561:                      "read_file", "grep"):
 562:         assert required in names or required in full
 563: 
 564: 
 565: def test_task_tool_schema_lists_all_7_agent_types():
 566:     """Codex iter-1 finding #3 MEDIUM lock: tools/task.py JSON schema
 567:     `subagent_type` enum lists all 7 agent types AGENT_TYPES.keys() â€” not
 568:     just 'general'."""
 569:     from tools import all_registered
 570:     from subagent import AGENT_TYPES
 571: 
 572:     task_tool = next((t for t in all_registered() if t.name == "task"), None)
 573:     assert task_tool is not None
 574:     schema = task_tool.input_schema
 575:     enum = schema["properties"]["subagent_type"].get("enum", [])
 576:     assert set(enum) == set(AGENT_TYPES.keys()), (
 577:         f"task tool subagent_type enum {set(enum)} must == AGENT_TYPES.keys() "
 578:         f"{set(AGENT_TYPES.keys())} (Codex iter-1 #3)"
 579:     )
 580:     # Description should mention each major type.
 581:     desc = schema["properties"]["subagent_type"].get("description", "")
 582:     for at in ("explore", "plan", "verify", "build"):
 583:         assert at in desc, f"task tool subagent_type description must mention {at!r}"
 584: 
 585: 
 586: def test_agent_max_turns_clamped_by_per_type_ceiling():
 587:     """spawn_subagent clamps max_turns to min(caller-supplied, agent_type ceiling)."""
 588:     from core import QueryEngine
 589:     from core.budget import IterationBudget
 590:     from subagent.spawn import spawn_subagent
 591:     from subagent.agent_types import AGENT_TYPES
 592: 
 593:     # explore.max_turns = 20; pass 100 to spawn â€” should clamp to 20.
 594:     client = _ScriptedClient([("text", "x")])
 595:     parent = QueryEngine(client=client, max_turns=200,
 596:                          budget=IterationBudget(max_iterations=200))
 597: 
 598:     # We can't easily inspect the child's max_turns post-completion, but we
 599:     # can call _new_child_engine indirectly via spawn and check the agent
 600:     # ran within the per-type ceiling. The integration check is implicit:
 601:     # spawn_subagent passes the resolved max_turns into _new_child_engine.
 602:     result = spawn_subagent(
 603:         parent_engine=parent, prompt="x", agent_type="explore",
 604:         max_turns=100,
 605:     )
 606:     assert result.stop_reason == "end_turn"
 607:     # explore.max_turns = 20 ceiling â€” even though caller asked for 100.
 608:     assert AGENT_TYPES["explore"].max_turns == 20

 succeeded in 532ms:
  80: - Critical: 15/15 PASS (100%).
  81: - Non-critical: 10/10 PASS (100%, exceeds 90% gate).
  82: - Documented divergences from v4: per-tool `max_result_size_chars` cap (vs v4's global cap) â€” see `test_noncritical_01_tool_result_truncation_respects_per_tool_cap`. This is an INTENTIONAL improvement, not a regression.
  83: 
  84: **Phase 12 parity differences appendix** (kept here for ship-gate audit):
  85: - v5 uses per-tool `max_result_size_chars` cap (50_000 default) vs v4's single global cap. Each tool's truncation behavior matches its declared cap.
  86: - v5's plan-mode dispatch uses strict `PLAN_MODE_ALLOWED_TOOLS` allowlist; v4 used `is_read_only` heuristic. Codex Phase-08 finding (v5 strict is correct).
  87: - v5's skill `propose_patch` uses UUID-suffixed timestamp; v4 used second-only. v5 prevents collisions.
  88: - v5's `discover_relevant` accepts an `active_tools` parameter for Hermes filter; v4 had no equivalent.
  89: - v5's `IterationBudget` and `thinking_budget` are visible via widgets; v4 had no UI surface for either.
  90: 
  91: | 036 | 2026-04-30 | 13 | v4 _rebuild_zip.py (181 LOC) | compact_v5/_rebuild_zip.py | ADAPT | PASS | n/a | (pending) | Walks v5 nested-package layout (`MAIN/agent/{core,tools,skills,runtime,prompt,ui,subagent,security,mcp}`) and flattens the `MAIN/agent/` prefix while preserving package directories. Excludes tests/, changelogs/, _status/, docs/, _archive/, __pycache__, .pytest_cache. constraint=.ipynb (different source layout vs v4 monolith). ADR-019. |
  92: | 037 | 2026-04-30 | 13 | v4 verify_ship_zip.py (161 LOC) | compact_v5/verify_ship_zip.py | ADAPT | PASS | n/a | (pending) | v5 runtime file list: chat.ipynb + chat.md + entry.py + __init__.py at root; required packages (core, tools, skills, runtime, prompt, ui, subagent, security); 14 required tools; 10 required skills. Same forbidden-pattern surface as v4 + 2 new patterns (changelogs/, _status/). constraint=.ipynb. ADR-019. |
  93: | 038 | 2026-05-02 | Block 0 | v4 chat.ipynb cells 2+3 `from sagemaker_agent import {BEDROCK_MODELS, CONFIG, create_chat_ui}` (compact_v4/MAIN/agent/chat.ipynb) | compact_v5/MAIN/agent/sagemaker_agent.py (re-exports `entry` public surface at v4-canonical import path) | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 19e7823 | **v5.0.1 Block 0**. Hard-constraint #2 (v4 chat.ipynb = canonical UI, UNCHANGED). Tiny shim â€” implementations live in their proper v5 modules; this only re-binds names. Re-exports: Agent / BEDROCK_MODELS / CONFIG / IterationBudget / SkillManager / create_chat_ui. 5 lock tests in tests/integration/test_block0_shim.py per TEST_DESIGN Â§Block 0 (T1 imports / T1 PS#1 CSO-quiet at WARNING / T3 chat.ipynb cells 1-3 / T2 widget renders / T1 v4 import compat). Test 3 also acts as the post-Block-0 notebook smoke gate. ADR-020. |
  94: | 039 | 2026-05-03 | Block B | v4 TokenTracker (compact_v4/MAIN/agent/sagemaker_agent.py:3565-3753) | compact_v5/MAIN/agent/runtime/tokens.py:`TokenTracker` + `TOKENS` singleton | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Verbatim port of v4 TokenTracker class (188 LOC). Adaptations: constructor accepts a config object (vs reading global CONFIG at import-time) so tests can pin behavior; logging.warning replaces v4's print() for budget warnings; cache-savings + per-turn cache line UI surfaces preserved. Per-agent attribution (parent_input/output/cost + subagent_input/output/cost dicts) extends v4 to satisfy Plan v3 Â§Block B + B-11 (R7 N8). Lock tests: test_token_tracker_singleton + test_token_tracker_per_agent_breakdown + test_token_accounting_session_sums_input_and_output. ADR-021. |
  95: | 040 | 2026-05-03 | Block B | Runnable utils/modelCost.ts:1-232 (R8 #34 / #68) + cost-tracker.ts:181-226 (R11 N9) | runtime/tokens.py:`MODEL_COSTS` + `EXCLUDED_MODELS_FOR_CACHE_BREAK` + `IMAGE_MAX_TOKEN_SIZE` + `canonicalize_model_id` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Bedrock-only subset of Runnable's MODEL_COSTS table (Haiku 4.5 + Sonnet 4.6 + 3.5-baseline). Cache-aware pricing math from v4 (cache_read=10%, cache_write=125%) preserved. EXCLUDED_MODELS_FOR_CACHE_BREAK Set adds Haiku-4.5 per R4 #14 (MUST). IMAGE_MAX_TOKEN_SIZE=2000 per R4 #38 (MUST). canonicalize_model_id strips `apac.`/`us.`/`eu.` prefixes for pricing lookup (R11 N9). Lock test: test_haiku_excluded_from_cache_break. ADR-021. |
  96: | 041 | 2026-05-03 | Block B | Runnable services/tokenEstimation.ts (R4 #38-44, R8 #15-16) + microCompact.ts:164-205 | runtime/tokens.py: `bytes_per_token_for_file_type` + `estimate_message_tokens` + `has_thinking_blocks` + `rough_token_count_for_block` + `rough_token_count_for_message` + `final_context_tokens_from_last_response` + `token_count_with_estimation` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | TS â†’ Python sync ports of Runnable's per-block-type token math. Drops tool-search-strip subset of countTokensViaHaikuFallback (B-2) â€” v5 doesn't yet have a token-emit budget cap. Used by Block A Compactor (when it lands) to drive context-window decisions without hitting Bedrock for every estimate. Lock tests: test_bytes_per_token_for_file_type + test_estimate_message_tokens_4_3_padding + test_has_thinking_blocks + test_rough_token_count_image_capped + test_final_context_tokens_from_last_response. ADR-021. |
  97: | 042 | 2026-05-03 | Block B | v4 ToolResult dataclass (compact_v4/MAIN/agent/sagemaker_agent.py:867-886, V1 gap #1 MUST) | runtime/tokens.py:`ToolResult` | PORT | PASS | FAITHFUL | (pending) | Truncated/total_size/shown_size/error metadata envelope so tool callers can introspect what came back from Bedrock truncation. Used by edit_file/write_file/bash result paths (wired in Block C+ when approval flow expands). Lock test: test_tool_result_dataclass_shape. ADR-021. |
  98: | 043 | 2026-05-03 | Block B | v4 AuditLogger + AuditEntry (compact_v4/MAIN/agent/sagemaker_agent.py:2156-2253) | compact_v5/MAIN/agent/runtime/audit.py:`AuditLogger` + `AuditEntry` + `AUDIT` singleton | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Verbatim port of v4 AuditLogger (~80 LOC) + AuditEntry dataclass with SHA256 tamper-detect hash. Adaptations: constructor accepts config object; logging.warning replaces v4's bare print on permission failures. Wired in core/query_engine.py: AUDIT.log fires on every tool dispatch (success + failure). Sensitive-key sanitizer preserves the v4 redaction set. Lock tests: test_audit_logger_writes_jsonl + test_audit_logger_redacts_sensitive_params. ADR-021. |
  99: | 044 | 2026-05-03 | Block B | v4 SnapshotManager (compact_v4/MAIN/agent/sagemaker_agent.py:4418-4510) | compact_v5/MAIN/agent/runtime/snapshot.py:`SnapshotManager` + `SNAPSHOTS` singleton | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Verbatim port of v4 SnapshotManager (~92 LOC). Constructor takes config object. Wired in tools/edit_file.py + tools/write_file.py (best-effort SNAPSHOTS.save before mutation). LRU eviction at 200 entries (v4 invariant preserved). Lock test: test_snapshot_manager_creates_backup. skills/manager.py apply_proposal wiring deferred to Block I (skill resolution) where the apply path lands. ADR-021. |
 100: | 045 | 2026-05-03 | Block B (remap of Block 0 item 0-8) | Runnable utils/envValidation.ts:1-39 (R8 #32) | compact_v5/MAIN/agent/runtime/env_validation.py:`validate_bounded_int_env_var` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Single helper for sanitizing all numeric env knobs (max_turns, budget, cost_limit, retention_days). Clamps to [min, max], returns default + WARNING on parse failure or out-of-range. Per ADR-020 Â§Notes / known scope remaps row 0-8. Lock test: test_env_validation_clamps_and_rejects_bad_input. ADR-021. |
 101: | 046 | 2026-05-03 | Block B (remap of Block 0 item 0-3) | Runnable constants/betas.ts:38-43 (R8 #74 MUST) | compact_v5/MAIN/agent/runtime/bedrock_client.py:`BEDROCK_EXTRA_PARAMS_HEADERS` frozenset | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | frozenset documenting which Anthropic-direct beta names belong in `additionalModelRequestFields` (Bedrock body), NOT in HTTP headers. Bedrock silently drops `anthropic-beta`-style headers. Per ADR-020 Â§Notes / known scope remaps row 0-3. Lock test: test_extra_params_in_body_not_headers. ADR-021. |
 102: | 047 | 2026-05-03 | Block B | Runnable services/tokenEstimation.ts:437-495 (R4 #41 MUST) | compact_v5/MAIN/agent/runtime/bedrock_client.py:`BedrockClient.count_tokens` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Real Bedrock CountTokens API call via boto3. Mock-mode falls through to rough_token_count helpers from runtime/tokens.py so the call shape is exercised without hitting Bedrock. T5 real-Bedrock test gated by RUN_REAL_BEDROCK env (~$0.005). Lock tests: test_count_tokens_with_bedrock_mocked + test_count_tokens_real_bedrock_haiku. ADR-021. |
 103: | 048 | 2026-05-03 | Block B+ | v4 SessionManager + Session dataclass (compact_v4/MAIN/agent/sagemaker_agent.py:2578-2659) | compact_v5/MAIN/agent/runtime/session.py:`Session` + `SessionManager` + `SESSIONS` singleton | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Verbatim port of v4 SessionManager (~80 LOC) + Session dataclass. Atomic save via tempfile.mkstemp + os.replace. Tolerates schema evolution on load (drops unknown fields). Constructor takes config object; CONFIG lookup is lazy via @property to survive importlib.reload(runtime.config) in tests. Lock tests: test_session_manager_atomic_save + test_session_load_round_trip + test_session_save_load_preserves_cost (closes PS#5). ADR-022. |
 104: | 049 | 2026-05-03 | Block B+ | v4 FileCache (compact_v4/MAIN/agent/sagemaker_agent.py:893-1017) | compact_v5/MAIN/agent/runtime/file_cache.py:`FileCache` + `FILE_CACHE` singleton | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Verbatim port of v4 FileCache (~125 LOC) â€” verified APIs: get/put (mtime-validated LRU), is_in_context/mark_in_context/clear_context/discard_from_context, save_and_clear_context/restore_context (Plan v3 Â§Block B+ acceptance), enter_thread_local_context/exit_thread_local_context (parallel sub-agents), clear_all. Threading.RLock + threading.local for per-thread context isolation. Wired in subagent/spawn.py: save+clear before child runs, restore after (try/finally). Lock tests: test_filecache_thread_local_isolation + test_filecache_save_and_restore_round_trip. ADR-022. |
 105: | 050 | 2026-05-03 | Block B+ (remap of Block 0 item 0-7) | Runnable utils/cleanupRegistry.ts:1-26 (R8 #18) | compact_v5/MAIN/agent/runtime/cleanup_registry.py:`register` + `_run_all` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | atexit + SIGINT/SIGTERM handler with best-effort callback list. TokenTracker registers `_flush_cost_on_exit` so session-final cost is logged even on Ctrl+C. Per ADR-020 Â§Notes / known scope remaps row 0-7. Tolerates Jupyter kernel signal-handler hijacking (signal.signal install wrapped in try/except). Lock tests: test_cleanup_registry_register_and_fire + test_cleanup_registry_callback_error_does_not_skip_others. ADR-022. |
 106: | 051 | 2026-05-03 | Block B+ (remap of Block 0 item 0-9) | Runnable entry.ts:1-17 (R11 N23) | compact_v5/MAIN/agent/runtime/feature_flags.py:`feature_enabled` + `is_banned` + `assert_not_banned` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Fail-closed feature flag helper. Banned set: mcp / streaming / anthropic_api_direct (per v5.0.1 hard constraints #9, #10). Soft features (skill_patching / skill_auto_trigger / memory_extraction) default-OFF, env-overridable. Banned features ignore env override. Per ADR-020 Â§Notes / known scope remaps row 0-9. Lock tests: test_feature_flag_fail_closed_for_banned + test_feature_flag_env_override_for_soft_features. ADR-022. |
 107: | 052 | 2026-05-03 | Block B+ | v4 sagemaker_agent.py:8787 cost-runtime-warning print | compact_v5/MAIN/agent/core/query_engine.py (post-chat() add: `[Cost ${cost} passed budget ${limit} â€” continuing.]`) | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Once-per-run warn at 100%+ of session_cost_limit. NOT a hard halt â€” per user 2026-05-03 Plan v3 update, v5 matches v4 UX (warn-and-continue). True hard halt is at cloud-budget level (AWS Budget Action / GCP Cloud Function). Lock test: test_session_cost_limit_warns_at_100pct. ADR-022. |
 108: | 053 | 2026-05-03 | Block B+ | Plan v3 Â§Block B+ FileCache thread-local sub-agent boundary | compact_v5/MAIN/agent/subagent/spawn.py (FILE_CACHE.save_and_clear_context before child.run / restore_context in finally) | ADD | PASS | FAITHFUL | (pending) | Wires FileCache save/restore around sub-agent dispatch so the child sees a clean in-context set and the parent's set is restored even if the child raises. Best-effort â€” singleton import failure does not block dispatch. Lock test: test_filecache_thread_local_isolation (covers the contract end-to-end via threading.Thread). ADR-022. |
 109: | 054 | 2026-05-03 | Block B+ | Runnable costHook.ts:6-22 (R11 N14) | runtime/tokens.py: `_flush_cost_on_exit` registered via cleanup_registry | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Atexit cost flush logs the final session cost at WARNING so post-hoc forensics can audit even after abrupt close. Pairs with #050 (cleanup_registry). No test (signal-firing test would be flaky on Windows); covered by integration: cleanup_registry tests verify the registration mechanism. ADR-022. |
 110: | 055 | 2026-05-03 | Block B+ | v4 sagemaker_agent.py:8700-8722 (`_load_persistent_memory` / `_load_project_status` AGENT_STATUS auto-load) | compact_v5/MAIN/agent/__init__.py: `_load_agent_status_text` + Agent.run first-call hook | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | First Agent.run() reads CONFIG.workspace/AGENT_STATUS.md (capped at 8 KB) and appends to dynamic tail of system prompt (after CACHE_BOUNDARY so prefix replay still works). Honors CONFIG.enable_status_doc=False. Idempotent â€” read once per Agent instance. Lock tests: test_agent_status_auto_load + test_agent_status_auto_load_disabled. ADR-022. |
 111: | 056 | 2026-05-03 | Block B+ (entry-guard) | (Block B+ Codex iter-1 finding #2 follow-up) | compact_v5/MAIN/agent/entry.py: import-time guard rejecting in-tree banned packages (`mcp/` per constraint #9) via realpath comparison | ADD | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Active probe via importlib.util.find_spec; only raises when spec.origin resolves under v5 agent root (real path), so external pip-installed packages don't false-positive. Lock tests: test_entry_guard_raises_if_banned_package_reintroduced_in_tree + test_entry_guard_does_not_false_positive_on_external_mcp. ADR-022. |
 112: | 057 | 2026-05-03 | Block C | Hermes run_agent.py:547-641 (R7-N graceful tool-arg JSON repair) | compact_v5/MAIN/agent/security/json_repair.py:`repair_tool_call_arguments` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Stand-alone helper that tries 5 progressively-aggressive repair strategies (as-is / strip / shape-fix / newline-escape / final fallback `{}`). Wired in core/query_engine.py: when tool_use.input arrives as a JSON string (some Bedrock variants), parse + repair before dispatch. Lock test: test_json_repair_malformed_args. ADR-023. |
 113: | 058 | 2026-05-03 | Block C (remap of Block 0 item 0-10) | v4 sagemaker_agent.py:7509-7541 (`_scan_for_prompt_injection` + `_INJECTION_PATTERNS`) | compact_v5/MAIN/agent/security/injection_scanner.py:`scan_for_prompt_injection` | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | 12 v4 patterns (ignore-previous, disregard-prior, forget-instructions, reveal-prompt, jailbreak-token, roleplay-jailbreak, fake-system-tag, fake-role-bracket, new-prompt-marker, end-prompt-marker, execute-following, bypass-security) + invisible/zero-width character class (ZWSP/ZWNJ/ZWJ/LRM/RLM/bidi/BOM). Per ADR-020 Â§Notes / known scope remaps row 0-10. Lock test: test_injection_scanner_v4_native. ADR-023. |
 114: | 059 | 2026-05-03 | Block C (remap of Block 0 item 0-5) | Runnable constants/prompts.ts:797-819 (R8 #77 â€” getScratchpadInstructions) | compact_v5/MAIN/agent/security/scratchpad.py:`get_scratchpad_dir` + `is_in_scratchpad` + `get_scratchpad_instructions` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Per-process scratchpad dir under platform tempdir with UUID suffix; pre-allowlisted via is_in_scratchpad helper; GC registered via cleanup_registry on SIGINT/SIGTERM/atexit. Per ADR-020 Â§Notes / known scope remaps row 0-5. Lock tests: test_scratchpad_dir_pre_allowlisted_and_gc + test_scratchpad_instructions_render. ADR-023. |
 115: | 060 | 2026-05-03 | Block C | Runnable FileEditTool/utils.ts (R1 #115 quote-norm + #116 quote-preserve) + FileEditTool.ts (R1 #121 UTF-16 BOM + #122 CRLF round-trip + #123 UNC + #111 Windows staleness fallback) | compact_v5/MAIN/agent/security/edit_file_safety.py: 7 helpers + tools/edit_file.py wiring | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Helpers: normalize_quotes / preserve_quote_style / detect_utf16_bom / is_unc_path_windows / normalize_line_endings / restore_line_endings / is_staleness_false_positive. Wired in tools/edit_file.py: UNC reject before path validation, BOM detection before read, normalize quotes + line endings before match, restore line endings before write, write back in detected encoding. Lock tests: test_quote_normalization_curly_to_straight + test_utf16_bom_detected + test_unc_path_skip_windows. ADR-023. |
 116: | 061 | 2026-05-03 | Block C | Runnable BashTool/{commandSemantics.ts (R1 #49 exit-code semantics) + destructiveCommandWarning.ts (R1 #50) + bashCommandHelpers.ts (R1 #53 cd+git + #54 multi-cd + #55 pipe-segment) + commentLabel.ts (R1 #48)} | compact_v5/MAIN/agent/security/bash_safety.py: 7 helpers + tools/bash.py wiring | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Helpers: interpret_command_result / destructive_command_warning / has_cd_git_compound_with_bare_repo / has_multiple_cd / split_pipe_segments / pipe_segment_permission_check / extract_bash_comment_label. Destructive catalog (13 patterns): rm -rf / git push --force / git reset --hard / git clean / DROP/TRUNCATE / kubectl delete / terraform destroy / docker rm/rmi/prune / dd to /dev/ / fork bomb / aws s3 rb --force / redis FLUSHALL. Wired in tools/bash.py: interpret_command_result post-exec to annotate non-zero exit codes. Lock tests: test_bash_exit_code_semantics + test_destructive_command_warning + test_cd_git_compound_with_bare_repo + test_multiple_cd_detection + test_pipe_segment_permission_check + test_extract_bash_comment_label. ADR-023. |
 117: | 062 | 2026-05-03 | Block C | v4 sagemaker_agent.py:9477-9489 (exec-limit gate) + :9156-9180 (repetition detector) | compact_v5/MAIN/agent/core/query_engine.py: `_exec_call_count` + `_recent_tool_calls` + dispatch-loop checks | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | PS#7 fix. 200-call cap on bash + python_exec only (read_file/grep/glob/edit_file/etc unaffected). v4 verbatim "OTHER TOOLS STILL WORK" guidance preserved. Repetition detector: same (tool_name, args_hash) appearing 3+ times in last 6 calls returns explicit "stuck loop" error to model. Counters reset between run() calls. Lock tests: test_exec_limit_200_then_201_blocked (PS#7 closure) + test_repetition_detector_blocks_3rd_dup. ADR-023. |
 118: | 063 | 2026-05-03 | Block C | Runnable services/teamMemorySync/secretScanner.ts (R5 A1 â€” 25 gitleaks patterns) | compact_v5/MAIN/agent/security/manager.py:`SECRET_PATTERNS` extended | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Combined pattern catalog: 13 v4 + 25 gitleaks = 38 patterns. New: OpenAI sk- / sk-proj- / Google AIza / Google ya29 / Mailchimp / Mailgun / Twilio Auth+SID / Square OAuth+Access+production / Stripe sk_live/rk_live/pk_live / GitLab PAT / npm / Hugging Face / Replicate / Pinecone / x-api-key / PGP / Encrypted PEM / Heroku / Cloudflare. Lock tests: test_secret_scanner_38_patterns + test_secret_scanner_detects_new_gitleaks_patterns. ADR-023. |
 119: | 064 | 2026-05-03 | Block C+ | v4 sagemaker_agent.py:9444 (approval gate dispatch check) + :10306 + :10491-10605 (pending_approval/on_approve/on_deny) + :8731-8740 (rate limit) | compact_v5/MAIN/agent/ui/approval_dialog.py: `PermissionDialog` + `RateLimiter` + ApprovalResult; core/query_engine.py wiring | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Approval gate fires when `CONFIG.require_tool_approval AND tool.requires_approval AND not client.mock_mode`. Buttons: Approve / Deny / Always-allow (sticky in CONFIG._always_allowed). Reason prompt surfaces tool_use input.reason. Block C UI-only helpers (cd+git C-11 / multi-cd C-12 / pipe-segment C-13 / comment-label C-14) rendered as warning lines. Text-mode fallback for headless / non-ipywidgets hosts (60s watchdog timeout; non-TTY defaults to deny). RateLimiter sliding-window: 100 messages/min + 1500/session defaults. Lock tests: 17 in test_block_c_plus.py covering all 7 TEST_DESIGN Â§Block C+ items + 4 Block-C remap locks + 3 lifecycle locks + 3 real-path locks. ADR-024. |
 120: | 065 | 2026-05-03 | Block D | v4 sagemaker_agent.py:8164 (advertised commands) + :10789-:11341 (per-command handlers) + :11314 (/auth gate-before-dispatch) + LF /dream/skillify/promote-to-skill patterns | compact_v5/MAIN/agent/commands.py: 25-entry dispatcher + ui/chat_ui.py routing | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | 17 v4 advertised + /auth + 6 LF additions = 24 canonical commands; +1 alias (/skill suggestion) = 25 in dispatch. CommandResult shape (text / consumed / side_effect / deny_auth). /auth runs BEFORE custom dispatch per v4:11314. Wired in ConsoleChatUI.send + WidgetChatUI._on_send. /revert all requires `--yes` strictly (Codex iter-1 HIGH safety lock). Lock tests: 22 in test_block_d.py (19 initial + 3 finding-locks for revert-all-safety, alias-routing, canonical-count). ADR-025. |
 121: | 066 | 2026-05-03 | Block A | v4 Compactor (compact_v4/MAIN/agent/sagemaker_agent.py:186-635, ~449 LOC) | compact_v5/MAIN/agent/core/compactor.py:`Compactor` | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Multi-mode compaction (prune oversized tool_results + LLM summary + replace old with summary + last N). estimate_tokens delegates to runtime/tokens helpers (drops tiktoken dep for SageMaker-native deployment). Auxiliary-model routing (v4.9.4 compaction_model) preserved with per-agent attribution via TOKENS.add(agent_kind="advisor") â€” closes B+5 deferral from ADR-022. PROTECTED_TOOLS preserves todo_write/todo_read/semantic_search results (v4 invariant). Lock tests: 12 in test_block_a.py covering estimate / prune / should_compact / compact / create_llm_summary / run end-to-end. ADR-026. |
 122: | 067 | 2026-05-03 | Block A | Hermes auto-compact circuit breaker pattern | core/compactor.py:`AutoCompactCircuitBreaker` + `AUTO_COMPACT` singleton | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Cooldown (default 30s) + per-session cap (default 10). Session cap checked first so exhausted runs fail fast. should_attempt() returns (allowed, reason) for clear logging. record_attempt() called by Compactor.run() on success OR failure. Per Wave-5-DEEP H5 + A28 cache-invariant. Lock tests: cooldown blocks repeated, session cap enforced, reset clears state. ADR-026. |
 123: | 068 | 2026-05-03 | Block A | Runnable cache_edits.ts (Anthropic-direct cache_edits param) | core/compactor.py:`apply_cache_control_to_blocks` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Bedrock equivalent of Anthropic-direct cache_edits: marks block at cache_break_at index with `{"cache_control": {"type": "ephemeral"}}`. Default = last block. Used by Compactor.run() output: the new summary block becomes the cache prefix for subsequent turns. Per Hermes A28 cache-invariant (no mid-turn cache flips). Lock tests: marks-last / specific-index / empty-list. ADR-026. |
 124: | 069 | 2026-05-03 | Block A (remap of Block B B-2) | Runnable services/tokenEstimation.ts:251-325 (R4 #42) | core/compactor.py:`count_tokens_via_haiku_fallback` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Fallback token counter when BedrockClient.count_tokens unavailable (older boto3): use Haiku 4.5 with max_tokens=1 to get input usage cheaply. Mock-mode falls through to rough estimator. Closes B-2 deferral from ADR-021 (B-2 was deferred from Block B because the consumer is Compactor, which lives in Block A). Lock tests: mock-mode + None-client. ADR-026. |
 125: | 070 | 2026-05-03 | Block A (remap of Block B+ B+5) | v4.9.4 compaction_model auxiliary-model pattern (compact_v4/MAIN/agent/sagemaker_agent.py compactor `_summary_client`) | core/compactor.py:`Compactor._summary_client` + advisor agent_kind | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Per-class aux-client cache. When CONFIG.compaction_model is set AND differs from main_client.model_id, builds a Bedrock client for the aux model. summary tokens go to `TOKENS.subagent_input_tokens["advisor"]` so /cost shows the aux-model cost separately. Closes B+5 deferral from ADR-022 (B+5 was deferred from Block B+ because the auxiliary model is invoked only via Compactor). Lock tests: aux-set â†’ advisor bucket; aux-empty â†’ parent bucket. ADR-026. |
 126: | 071 | 2026-05-03 | Block E+F (remap of Block 0 items 0-2/0-4/0-6) | Runnable constants/prompts.ts:606-770 (R8 #76/#79 env block) + :712-730 (R8 #39 knowledge cutoff) + constants/common.ts:1-34 (R8 #67 date helpers) | compact_v5/MAIN/agent/prompt/env_block.py: get_session_start_date / get_local_month_year / get_knowledge_cutoff / get_os_string / get_shell_hint / render_env_block | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Closes ADR-020 Â§Notes / known scope remaps rows 0-2 (cache-stable date helpers) + 0-4 (Windows-shell hint, OS, Notes appendix) + 0-6 (model-specific knowledge cutoff with cross-region prefix stripping). Date stays at month-year resolution to prevent midnight cache busts. _KNOWLEDGE_CUTOFFS table covers Haiku 4.5 / Sonnet 4.5 / Sonnet 4.6 / 3.5 baseline. Lock tests: 12 in test_block_e_f.py. ADR-027. |
 127: | 072 | 2026-05-03 | Block F2 (NEW) | Runnable query/tokenBudget.ts:1-93 (createBudgetTracker / checkTokenBudget / COMPLETION_THRESHOLD=0.9 / DIMINISHING_THRESHOLD=500-tokens) + utils/tokenBudget.ts:66-73 (getBudgetContinuationMessage) + query.ts:1308-1355 (engine wiring) | compact_v5/MAIN/agent/core/budget_continuation.py:`BudgetTracker` + `check_iteration_budget` + `get_budget_continuation_message`; runtime/config.py:`enable_token_budget_continuation` flag (default OFF); core/query_engine.py end_turn branch wiring | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | dd33507 | NEEDS-ADAPTATION per Wave 5-DEEP Â§Block F2: Runnable's tokenBudget tracks turn-output-tokens vs a user-set token budget parsed from the message text ("+500k"); v5 reuses the existing IterationBudget surface (counts turns) â€” same semantic, fewer surfaces, matches scenario #21 wording. DIMINISHING_THRESHOLD adapted from 500 tokens â†’ 2 iterations. Cost-cap halt added (Wave 6 NLT row #21): even when iter_used < 90%, if session_cost â‰¥ session_cost_limit â†’ halt. Sub-agents always halt (parent-only auto-continuation, matches Runnable agentId early-out at tokenBudget.ts:51). Default-OFF opt-in (Wave 6 NLT row #21 contract). Tracker reset to None at run() entry â€” never leaks state across user messages. F2 logic best-effort wrapped in try/except so it never blocks normal end_turn. Lock tests: 20 in test_block_f2.py â€” 7 pure-function + 3 TEST_DESIGN-named + 4 behavioral locks (initial 14) + 3 iter-2 finding-locks (StopDecision audit / exception-logged / snapshot-restore-pattern) + 3 iter-3 finding-locks (pct in completion_event for cost_cap / diminishing / above_threshold). Codex 3-iter cycle: APPROVE_WITH_FIXES (3 findings) â†’ APPROVE_WITH_FIXES (2 findings) â†’ APPROVE clean. ADR-028. |
 128: | 073 | 2026-05-03 | Block I (I-1) | Runnable skills/loadSkillsDir.ts:159-178 (parseSkillPaths) | skills/manager.py: SkillInfo.paths + discover() paths-frontmatter parsing + activate_for_path(); tools/edit_file.py wiring | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | Strips trailing /** suffix; collapses all-`**` patterns to None (unconditional). fnmatch matching against both full path and basename. activate_for_path called from edit_file post-write; skips already-active skill. ADR-029. |
 129: | 074 | 2026-05-03 | Block I (I-2) | Runnable skills/bundledSkills.ts:84 (disable_model_invocation) | skills/manager.py: SkillInfo.disable_model_invocation + list_model_invocable() / list_user_invocable() | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | True/false frontmatter flag. Hides skill from model-invocation surfaces (skill_tool / discover_relevant) but keeps it user-invocable via /skill use. New skills/remember/SKILL.md uses this flag (memory writes are deliberate human acts). ADR-029. |
 130: | 075 | 2026-05-03 | Block I (I-3) | Runnable skills/bundled/remember.ts:71 (enabled_when) | skills/manager.py: SkillInfo.enabled_when + _enabled_when_truthy() + discover() gate | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | enabled_when names a CONFIG attribute; if truthy at discover() time the skill loads, else it's skipped entirely (not just hidden). Fail-closed when CONFIG can't be imported so a flag-name typo doesn't accidentally activate an opt-in skill. ADR-029. |
 131: | 076 | 2026-05-03 | Block I (I-4) | Runnable skills/loadSkillsDir.ts:638-810 (seenFileIds Map dedup) | skills/manager.py: discover() seen_realpaths set | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | os.path.realpath dedup; first-wins ordering matches Runnable Map. Local to discover() so re-discovery on instance still works (lock test). Closes R9 #23 symlink-double-load bug. ADR-029. |
 132: | 077 | 2026-05-03 | Block I (I-5) | Runnable skills/FileEditTool.ts:404-423 (path-triggered skill activation) | tools/edit_file.py post-write skill_manager.activate_for_path call; core/query_engine.py dispatch context passes skill_manager + session_id | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | edit_file consumes context["skill_manager"] (best-effort; never blocks edit on skill-activation hook). Activated skill name appended to tool_result text so the model sees the activation. Block I-5 + I-1 coupled â€” paths frontmatter without this hook doesn't fire. ADR-029. |
 133: | 078 | 2026-05-03 | Block I (I-6) | Runnable skills/loadSkillsDir.ts:344-396 (${CLAUDE_SKILL_DIR} / ${CLAUDE_SESSION_ID} substitution) | skills/manager.py: substitute_skill_vars() | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | Replaces ${CLAUDE_SKILL_DIR} with skill.base_dir (forward-slash on Windows) + ${CLAUDE_SESSION_ID} with engine session_id. Block I-6 SECURITY: v5 deliberately does NOT port executeShellCommandsInPrompt (Runnable's bash !`...` exec) â€” constraint #10 + #9. Variable subst is therefore safe; no shell exec path. ADR-029. |
 134: | 079 | 2026-05-03 | Block I (Hermes fuzzy) | Hermes run_agent.py:4685-4724 (fast-path-then-difflib resolver) | skills/manager.py: resolve_name() exact â†’ case-insensitive â†’ suffix-strip â†’ difflib.get_close_matches(cutoff=0.7) | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | Adapted from tool-name resolver to skill-name resolver. Cutoff=0.7 verbatim. Suffix strip handles _skill/-skill/skill. commands.py /skill use cmd_skill_use now routes through resolve_name (replaces previous startswith-3-letter suggestion). ADR-029. |
 135: | 080 | 2026-05-03 | Block I (I-10) | Runnable skills/bundled/debug.ts:1-103 | compact_v5/MAIN/agent/skills/debug/SKILL.md NEW | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | Triage skill: tail audit_logs, identify symptom â†’ root cause â†’ ONE next action. Adapted from Runnable's tail-audit-log script to v5's runtime/audit/ JSONL surface. CSO description "Use when the user reports the agent is stuck...". ADR-029. |
 136: | 081 | 2026-05-03 | Block I (I-11) | Runnable skills/bundled/remember.ts:9-62 (4-step review) | compact_v5/MAIN/agent/skills/remember/SKILL.md NEW | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 43d1ebe | 4-round skill: scope â†’ fit (CLAUDE.md vs CLAUDE.local.md) â†’ draft â†’ append. disable_model_invocation:true (memory writes are deliberate human acts; auto-trigger would be wrong). CSO description "Use when the user wants to capture a learning into CLAUDE.md...". ADR-029. |
 137: | 082 | 2026-05-03 | Block I (I-7..I-9, I-13) | (folded into Block D dispatcher) | commands.py: /init, /init-verifiers, /skillify, /promote-to-skill (Block D wired); tool_skill + tool_skill_propose_patch (Block D registered) | doc-only | PASS | (no code change) | 43d1ebe | Block I-7 (init scaffolder) + I-8 (init-verifiers) + I-9 (skillify) + I-13 (tool_skill registry) all already wired in Block D's commands dispatcher (PORT_LOG #065). Block I-9 lock test test_skillify_4_round_interview verifies dispatch contract (the actual 4-round interview is conducted by the LLM at runtime, prompted by side_effect). ADR-029. |
 138: | 084 | 2026-05-03 | Block M (Phase 8 critical fix #2) | Runnable QueryEngine.ts:1004-1048 (countToolCalls + structured-output retry-limit) | core/query_engine.py: count_tool_calls() helper + synthetic_output_tool_name / max_structured_output_retries QueryEngine ctor params + retry-limit halt at top of for-loop turn (stop_reason="error_max_structured_output_retries") | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 09b6114 | Default OFF (synthetic_output_tool_name=None preserves backwards compat). Per-run baseline captured at run() entry so the retry limit only counts THIS run's calls, not prior-session ones. Lock tests: 11 in test_block_m.py â€” 5 pure-function (count_tool_calls edge cases) + 3 TEST_DESIGN-named (discovered-skill-names-reset / structured-output-retry-limit-3 / infinite-loop-blocked) + 3 behavior locks (default-off-no-halt / clamp-min-1 / baseline-captured). ADR-030. |
 139: | 085 | 2026-05-03 | Block M (Phase 8 critical fix #1) | Runnable QueryEngine.ts:197 (discoveredSkillNames Set) + :238 (.clear() at run-entry) | core/query_engine.py:run() clears skill_manager._pending_activations at run() entry (best-effort try/except) | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | 09b6114 | v5 analog: SkillManager._pending_activations is the discoveredSkillNames-shaped surface. Cleared at the top of every run() so path/trigger-activated skills from a prior user message don't contaminate the next message. TEST_DESIGN catalogue name preserved verbatim ("test_discovered_tool_names_reset_per_turn") even though v5 surface is skills, not tools â€” Runnable terminology mapped via this row. ADR-030. |
 140: | 086 | 2026-05-03 | Block G (G-1, G-3, G-4, G-6, G-7) | v4 sagemaker_agent.py:6914-7090 (AGENT_TYPES dict) + Runnable AgentTool/constants.ts:9-12 (ONE_SHOT_BUILTIN_AGENT_TYPES) + AgentTool/prompt.ts:202-213 (getPrompt(isCoordinator)) + constants/prompts.ts:758 (DEFAULT_AGENT_PROMPT) + :766-770 (Notes) | compact_v5/MAIN/agent/subagent/agent_types.py: AGENT_TYPES dict (7 entries: build/plan/explore/verify/general/review/fork) + AgentType dataclass + DEFAULT_AGENT_PROMPT verbatim + SUBAGENT_NOTES + ONE_SHOT_BUILTIN_AGENT_TYPES frozenset + get_agent_type / get_agent_prompt(is_coordinator) | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Per-type max_turns + one_shot + auto_load_skill + needs_worktree knobs. coordinator-mode slim prompt drops Notes appendix (Block G3 will reuse). Lock tests: 4 in test_block_g.py (dict-has-7 / one-shot-set / coordinator-drops-notes / default-agent-prompt-no-gold-plating). ADR-031. |
 141: | 087 | 2026-05-03 | Block G (worktree) | v4 sagemaker_agent.py:8413+ (build agent worktree spawn) | compact_v5/MAIN/agent/subagent/worktree.py: create_worktree() / cleanup_worktree() + git/fallback_copy/fallback_tempdir tiers | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Best-effort: never raises into spawn loop; falls back to fallback_copy or tempdir if git unavailable. Wired into spawn_subagent: agent_def.needs_worktree â†’ create_worktree before child.run, cleanup_worktree in finally clause. Lock tests: build-spawns-worktree + worktree-cleanup-on-completion. ADR-031. |
 142: | 088 | 2026-05-03 | Block G (spawn dispatch + verify auto-load) | v4 sagemaker_agent.py:8366+ | compact_v5/MAIN/agent/subagent/spawn.py:_resolve_agent_suffix consults agent_types.get_agent_type; spawn_subagent applies per-type max_turns ceiling + worktree creation + verify-skill auto-load before child.run; tools/task.py validation uses AGENT_TYPES | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Replaced Phase-9 placeholder _AGENT_TYPE_SUFFIXES (general-only) with full registry lookup. Per-type max_turns clamped to caller-supplied. verify-skill auto-load: parent.skill_manager.activate(agent_def.auto_load_skill) + body spliced into child_prompt before run. Lock tests: 14 in test_block_g.py covering 8 TEST_DESIGN rows + 6 behavior locks. ADR-031. |
 143: | 089 | 2026-05-03 | Block G iter-2 (Codex iter-1 fixes) | Codex iter-1 BLOCKER + HIGH + MEDIUM + DOC findings | compact_v5/MAIN/agent/subagent/agent_types.py: AgentType.allowed_tools field + _READ_ONLY_TOOLS / _VERIFY_TOOLS allowlists; spawn.py: tool allowlist filtering + CONFIG.workspace swap into worktree during child.run with restore in finally; tools/task.py: JSON-schema enum + description listing all 7 types | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | (a) BLOCKER fix: build agents now actually run inside the worktree â€” CONFIG.workspace temporarily swapped + restored in finally. (b) HIGH fix: explore/plan/review get _READ_ONLY_TOOLS allowlist (no edit/write/exec); verify gets _VERIFY_TOOLS (read + bash + python_exec, no edit/write); general/build/fork get full registry. Always include task + tool_search across the board for legitimate sub-spawn / deferred-loading. (c) MEDIUM fix: tools/task.py subagent_type now has JSON-schema enum=AGENT_TYPES.keys() + description lists all 7. (d) DOC fix: see PORT_LOG #090. Lock tests: 6 added (build-runs-in-worktree / explore-allowlist / plan-allowlist / verify-allowlist / general-full-registry / task-schema-lists-7). ADR-031. |
 144: | 090 | 2026-05-03 | Block G (G-1, G-2 explicit deferral) | Runnable AgentTool/agentMemory.ts:138-177 (G-1 loadAgentMemoryPrompt) + :68-104 (G-2 isAgentMemoryPath) | (deferred â€” lands in Block H) | DEFER | (no code change) | (n/a) | (n/a) | Codex Block G iter-1 AXIS C closure. Per ADR-031 Â§Notes: G-1 (per-agent-scoped memory.md) + G-2 (path-traversal-safe agent memory paths) belong with Block H's memory extraction infrastructure (extractMemories.ts) where `loadAgentMemoryPrompt` is called. Deferring to Block H ensures the memory subsystem is built end-to-end as one architectural unit rather than splitting the API across two blocks. Lock test for G-2 path-traversal will land in Block H's test suite. NO silent scope narrowing â€” explicit deferral with target-Block + linked source file:line. |
 145: | 083 | 2026-05-03 | Block I (Axis C closure) | Codex Block I iter-1 AXIS C â€” undeclared cross-references | _status/V5_RUNNABLE_PORT_LOG.md (this row) + ADR-029 Â§6 | doc-only | PASS | (no code change) | 43d1ebe | Codex iter-1 AXIS C cleanup row. (a) **I-12 frontmatter parser improvements** (R8 #24, #50): DEFERRED to Block N per ADR-029 Â§6 (architectural fit â€” frontmatter expansion lands with Block N's dynamic-section + AGENTS.md infrastructure). (b) **Wave 6 row #93** (`PORT_LOG enumerates skills/verify/ as bundled`): closed via existing PORT_LOG #029 (Phase-10 byte-for-byte copy of 10 v4 production skills including verify). Block I makes no change to the bundled set; Phase-10 row is the canonical evidence. (c) **Wave 6 gap #8 â€” tool-vs-skill precedence** (PS_Plan_Edge_Cases_Thinking.md #93 / W6_multi_file_tasks.md:327-371): v5 disposition is **tools win for offline SageMaker / Bedrock-only deployments** because Block T's document tools (create_word, create_excel, create_chart, etc.) are zero-network-dependency and run inside the agent process; bundled skills (Runnable's debug, remember, etc.) are designed for the network-rich Anthropic-API-direct world and may reference tools that v5 doesn't ship (constraint #9 + #10). The model resolves a request by: (1) check direct tool registry first; (2) if no tool fits, check active skill body; (3) only suggest /skill use <name> when the user's task explicitly maps to a skill's CSO description. Block I lands the bundled debug + remember skills but they are auxiliary surfaces, not replacements for tools. ADR-029. |
 146: 
 147: **Phase 10 acceptance** (V5_PLAN.md): "all 10 skills load; auto-trigger respects v4.9.6 default-OFF." Both validated:
 148: - `test_all_10_v4_production_skills_load` â€” alias-aware (clara-reviewâ†’clara, code-reviewâ†’review).
 149: - `test_auto_trigger_default_off_returns_empty` + `test_auto_trigger_off_per_skill_default_off` â€” both gate-tests.
 150: - `test_skill_propose_patch_no_op_when_flag_off` â€” opt-in lock for v4.9.5 self-patching.
 151: 
 152: **Phase 10 Hermes filter (PS Issue #1)** â€” 4 lock tests in `test_skill_manager.py`:
 153: - `test_hermes_filter_skill_filtered_when_required_tool_missing`
 154: - `test_hermes_filter_skill_passes_when_all_required_tools_present`
 155: - `test_hermes_filter_skipped_when_active_tools_none` (backwards compat: no-active-tools = no filter)
 156: - `test_hermes_filter_skill_without_requires_tools_never_filtered` (backwards compat: 10 v4 skills don't declare it).
 157: 
 158: **Phase 9 acceptance** (V5_PLAN.md): "parent context unchanged; child shares IterationBudget." Both validated by `tests/integration/test_subagent.py`:
 159: - `test_subagent_shares_iteration_budget` â€” `child.budget is parent.budget` (object identity, not equality).
 160: - `test_subagent_parent_context_unchanged` â€” parent `messages` buffer length + content identical before/after.
 161: - Plus 9 more tests covering depth limit, empty prompt, shared-budget consumption, task tool registration + deferral, end-to-end QueryEngineâ†’task dispatch, and a defense-in-depth parent-context-mutation guard.
 162: 
 163: Phase 1 had no Runnable rows (pure v4 reuse â€” see ADR-005 / ADR-006). First Runnable adoption rows are Phase 02 above.
 164: 
 165: Verdict legend:
 166: - Adoption: PORT (1:1) | ADAPT (semantic match, mechanism differs) | REPLACE (v4-native chosen) | DEFER
 167: - Codex error: PASS | CHANGES_REQUESTED | BLOCKER
 168: - Codex fidelity: FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED
 169: 
 170: Enforcement note: every PORT_LOG row MUST reference an `ADR-NNN` in V5_DESIGN_DECISIONS.md (per the Addition Gate). Rows without an ADR reference are rejected by the pre-tag lint check (`tests/lint_phase_id.py`).

codex
The implementation side looks materially fixed. One test-quality issue is emerging: the “general gets full registry” lock has an `or required in full` clause that can pass even if the spawned child did not receive the tool, so I’m checking whether that is the only unsound lock before forming the verdict.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'pytest compact_v5/MAIN/agent/tests/integration/test_block_g.py -q' in D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$lines = Get-Content compact_v5/_status/V5_RUNNABLE_PORT_LOG.md; foreach ($n in 143,144) { $line=$lines[$n-1]; $cells=($line.Trim('"'|') -split '\\|').Count; Write-Output \"line "'$n cells=$cells"; Write-Output $line }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"def all_registered|class Tool|name=\\\"(write_file|edit_file|bash|python_exec|read_file|grep|glob|tool_search|task)\\\"|name='(write_file|edit_file|bash|python_exec|read_file|grep|glob|tool_search|task)'\" compact_v5/MAIN/agent/tools compact_v5/MAIN/agent/core" in D:\Github\sagemaker-coding-agent
2026-05-03T06:09:43.093438Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.6 seconds
Output:
pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ pytest compact_v5/MAIN/agent/tests/integration/test_block_g.py -q
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (pytest:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 exited 1 in 557ms:
pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ pytest compact_v5/MAIN/agent/tests/integration/test_block_g.py -q
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (pytest:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

2026-05-03T06:09:43.104643Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.6 seconds
Output:
write_file : The term 'write_file' is not recognized as the name of a cmdlet, function, script file, or operable 
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:46
+ rg -n "def all_registered|class Tool|name=\"(write_file|edit_file|bas ...
+                                              ~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (write_file:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 exited 1 in 554ms:
write_file : The term 'write_file' is not recognized as the name of a cmdlet, function, script file, or operable 
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:46
+ rg -n "def all_registered|class Tool|name=\"(write_file|edit_file|bas ...
+                                              ~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (write_file:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 succeeded in 677ms:
line 143 cells=10
| 089 | 2026-05-03 | Block G iter-2 (Codex iter-1 fixes) | Codex iter-1 BLOCKER + HIGH + MEDIUM + DOC findings | compact_v5/MAIN/agent/subagent/agent_types.py: AgentType.allowed_tools field + _READ_ONLY_TOOLS / _VERIFY_TOOLS allowlists; spawn.py: tool allowlist filtering + CONFIG.workspace swap into worktree during child.run with restore in finally; tools/task.py: JSON-schema enum + description listing all 7 types | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | (a) BLOCKER fix: build agents now actually run inside the worktree â€” CONFIG.workspace temporarily swapped + restored in finally. (b) HIGH fix: explore/plan/review get _READ_ONLY_TOOLS allowlist (no edit/write/exec); verify gets _VERIFY_TOOLS (read + bash + python_exec, no edit/write); general/build/fork get full registry. Always include task + tool_search across the board for legitimate sub-spawn / deferred-loading. (c) MEDIUM fix: tools/task.py subagent_type now has JSON-schema enum=AGENT_TYPES.keys() + description lists all 7. (d) DOC fix: see PORT_LOG #090. Lock tests: 6 added (build-runs-in-worktree / explore-allowlist / plan-allowlist / verify-allowlist / general-full-registry / task-schema-lists-7). ADR-031. |
line 144 cells=10
| 090 | 2026-05-03 | Block G (G-1, G-2 explicit deferral) | Runnable AgentTool/agentMemory.ts:138-177 (G-1 loadAgentMemoryPrompt) + :68-104 (G-2 isAgentMemoryPath) | (deferred â€” lands in Block H) | DEFER | (no code change) | (n/a) | (n/a) | Codex Block G iter-1 AXIS C closure. Per ADR-031 Â§Notes: G-1 (per-agent-scoped memory.md) + G-2 (path-traversal-safe agent memory paths) belong with Block H's memory extraction infrastructure (extractMemories.ts) where `loadAgentMemoryPrompt` is called. Deferring to Block H ensures the memory subsystem is built end-to-end as one architectural unit rather than splitting the API across two blocks. Lock test for G-2 path-traversal will land in Block H's test suite. NO silent scope narrowing â€” explicit deferral with target-Block + linked source file:line. |

codex
`pytest` is not on PATH here, so I’m retrying through `python -m pytest`. The PORT_LOG structure check passes for both added rows: 10 cells each.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest tests/integration/test_block_g.py -q' in D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n 'def all_registered|class Tool|name=\"(write_file|edit_file|bash|python_exec|read_file|grep|glob|tool_search|task)\"|name=''((write_file|edit_file|bash|python_exec|read_file|grep|glob|tool_search|task))''' compact_v5/MAIN/agent/tools compact_v5/MAIN/agent/core" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"allowed_tools|CONFIG\\.workspace|test_general_agent_gets_full_registry|test_build_agent_actually_runs_inside_worktree|subagent_type.*enum|090 \\|\" compact_v5/MAIN/agent/subagent/agent_types.py compact_v5/MAIN/agent/subagent/spawn.py compact_v5/MAIN/agent/tools/task.py compact_v5/MAIN/agent/tests/integration/test_block_g.py compact_v5/_status/V5_RUNNABLE_PORT_LOG.md" in D:\Github\sagemaker-coding-agent
 succeeded in 498ms:
compact_v5/MAIN/agent/tools\registry.py:57:class ToolDef(Protocol):
compact_v5/MAIN/agent/tools\registry.py:91:class ToolRecord:
compact_v5/MAIN/agent/tools\registry.py:174:def all_registered() -> List[ToolRecord]:

 succeeded in 499ms:
compact_v5/_status/V5_RUNNABLE_PORT_LOG.md:110:| 055 | 2026-05-03 | Block B+ | v4 sagemaker_agent.py:8700-8722 (`_load_persistent_memory` / `_load_project_status` AGENT_STATUS auto-load) | compact_v5/MAIN/agent/__init__.py: `_load_agent_status_text` + Agent.run first-call hook | PORT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | First Agent.run() reads CONFIG.workspace/AGENT_STATUS.md (capped at 8 KB) and appends to dynamic tail of system prompt (after CACHE_BOUNDARY so prefix replay still works). Honors CONFIG.enable_status_doc=False. Idempotent — read once per Agent instance. Lock tests: test_agent_status_auto_load + test_agent_status_auto_load_disabled. ADR-022. |
compact_v5/_status/V5_RUNNABLE_PORT_LOG.md:143:| 089 | 2026-05-03 | Block G iter-2 (Codex iter-1 fixes) | Codex iter-1 BLOCKER + HIGH + MEDIUM + DOC findings | compact_v5/MAIN/agent/subagent/agent_types.py: AgentType.allowed_tools field + _READ_ONLY_TOOLS / _VERIFY_TOOLS allowlists; spawn.py: tool allowlist filtering + CONFIG.workspace swap into worktree during child.run with restore in finally; tools/task.py: JSON-schema enum + description listing all 7 types | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | (a) BLOCKER fix: build agents now actually run inside the worktree — CONFIG.workspace temporarily swapped + restored in finally. (b) HIGH fix: explore/plan/review get _READ_ONLY_TOOLS allowlist (no edit/write/exec); verify gets _VERIFY_TOOLS (read + bash + python_exec, no edit/write); general/build/fork get full registry. Always include task + tool_search across the board for legitimate sub-spawn / deferred-loading. (c) MEDIUM fix: tools/task.py subagent_type now has JSON-schema enum=AGENT_TYPES.keys() + description lists all 7. (d) DOC fix: see PORT_LOG #090. Lock tests: 6 added (build-runs-in-worktree / explore-allowlist / plan-allowlist / verify-allowlist / general-full-registry / task-schema-lists-7). ADR-031. |
compact_v5/_status/V5_RUNNABLE_PORT_LOG.md:144:| 090 | 2026-05-03 | Block G (G-1, G-2 explicit deferral) | Runnable AgentTool/agentMemory.ts:138-177 (G-1 loadAgentMemoryPrompt) + :68-104 (G-2 isAgentMemoryPath) | (deferred — lands in Block H) | DEFER | (no code change) | (n/a) | (n/a) | Codex Block G iter-1 AXIS C closure. Per ADR-031 §Notes: G-1 (per-agent-scoped memory.md) + G-2 (path-traversal-safe agent memory paths) belong with Block H's memory extraction infrastructure (extractMemories.ts) where `loadAgentMemoryPrompt` is called. Deferring to Block H ensures the memory subsystem is built end-to-end as one architectural unit rather than splitting the API across two blocks. Lock test for G-2 path-traversal will land in Block H's test suite. NO silent scope narrowing — explicit deferral with target-Block + linked source file:line. |
compact_v5/MAIN/agent/subagent/spawn.py:248:    # contract. When agent_def.allowed_tools is set, child_tools is filtered
compact_v5/MAIN/agent/subagent/spawn.py:252:    if agent_def is not None and agent_def.allowed_tools:
compact_v5/MAIN/agent/subagent/spawn.py:253:        _allow = set(agent_def.allowed_tools)
compact_v5/MAIN/agent/subagent/spawn.py:321:    # Block G iter-2 (Codex finding #1 BLOCKER): swap CONFIG.workspace to
compact_v5/MAIN/agent/subagent/spawn.py:322:    # the worktree path so tools that read `CONFIG.workspace` (bash cwd,
compact_v5/MAIN/agent/subagent/spawn.py:333:                "[subagent] swapped CONFIG.workspace=%s -> %s for build agent",
compact_v5/MAIN/agent/subagent/spawn.py:338:                "[subagent] CONFIG.workspace swap failed: %s", _ws_exc,
compact_v5/MAIN/agent/subagent/spawn.py:359:        # Block G iter-2 — restore CONFIG.workspace before worktree cleanup
compact_v5/MAIN/agent/tests/integration/test_block_g.py:365:def test_build_agent_actually_runs_inside_worktree(tmp_path):
compact_v5/MAIN/agent/tests/integration/test_block_g.py:367:    CONFIG.workspace to the worktree path during child.run so tools
compact_v5/MAIN/agent/tests/integration/test_block_g.py:368:    that read CONFIG.workspace (bash cwd, security path checks,
compact_v5/MAIN/agent/tests/integration/test_block_g.py:378:    _saved_ws = CONFIG.workspace
compact_v5/MAIN/agent/tests/integration/test_block_g.py:379:    CONFIG.workspace = workspace
compact_v5/MAIN/agent/tests/integration/test_block_g.py:381:    # Capture CONFIG.workspace as observed by the child during chat.
compact_v5/MAIN/agent/tests/integration/test_block_g.py:394:            seen_during_run["cfg_ws"] = CONFIG.workspace
compact_v5/MAIN/agent/tests/integration/test_block_g.py:410:        # During child.run, CONFIG.workspace must point INTO the worktree.
compact_v5/MAIN/agent/tests/integration/test_block_g.py:415:            "CONFIG.workspace must be swapped to worktree, not left as parent"
compact_v5/MAIN/agent/tests/integration/test_block_g.py:418:        assert CONFIG.workspace == workspace, (
compact_v5/MAIN/agent/tests/integration/test_block_g.py:419:            "CONFIG.workspace must be restored after build sub-agent completes"
compact_v5/MAIN/agent/tests/integration/test_block_g.py:422:        CONFIG.workspace = _saved_ws
compact_v5/MAIN/agent/tests/integration/test_block_g.py:531:def test_general_agent_gets_full_registry():
compact_v5/MAIN/agent/tests/integration/test_block_g.py:532:    """general agent (no allowed_tools allowlist) sees the full registry."""
compact_v5/MAIN/agent/tests/integration/test_block_g.py:567:    `subagent_type` enum lists all 7 agent types AGENT_TYPES.keys() — not
compact_v5/MAIN/agent/tests/integration/test_block_g.py:575:    enum = schema["properties"]["subagent_type"].get("enum", [])
compact_v5/MAIN/agent/tests/integration/test_block_g.py:577:        f"task tool subagent_type enum {set(enum)} must == AGENT_TYPES.keys() "
compact_v5/MAIN/agent/subagent/agent_types.py:67:    # Block G iter-2 (Codex finding #2 HIGH): allowed_tools allowlist enforced
compact_v5/MAIN/agent/subagent/agent_types.py:71:    allowed_tools: Optional[tuple] = None  # tuple for frozen-dataclass safety
compact_v5/MAIN/agent/subagent/agent_types.py:103:        allowed_tools=_READ_ONLY_TOOLS,
compact_v5/MAIN/agent/subagent/agent_types.py:116:        allowed_tools=_READ_ONLY_TOOLS,
compact_v5/MAIN/agent/subagent/agent_types.py:130:        allowed_tools=_VERIFY_TOOLS,  # read-only + bash + python_exec
compact_v5/MAIN/agent/subagent/agent_types.py:156:        allowed_tools=_READ_ONLY_TOOLS,

2026-05-03T06:10:07.613722Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 15.6 seconds
Output:
Program 'python.exe' failed to run: The file cannot be accessed by the systemAt line:2 char:1
+ python -m pytest tests/integration/test_block_g.py -q
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
At line:2 char:1
+ python -m pytest tests/integration/test_block_g.py -q
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ResourceUnavailable: (:) [], ApplicationFailedException
    + FullyQualifiedErrorId : NativeCommandFailed
 

 exited 1 in 15636ms:
Program 'python.exe' failed to run: The file cannot be accessed by the systemAt line:2 char:1
+ python -m pytest tests/integration/test_block_g.py -q
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
At line:2 char:1
+ python -m pytest tests/integration/test_block_g.py -q
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ResourceUnavailable: (:) [], ApplicationFailedException
    + FullyQualifiedErrorId : NativeCommandFailed
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n 'name=\"["'^"]+"'"' compact_v5/MAIN/agent/tools | Select-Object -First 80" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Command python, py, pytest -ErrorAction SilentlyContinue | Format-Table -AutoSize' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/tools/registry.py | ForEach-Object { if ($i -ge 130 -and $i -le 210) { '"'{0,4}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 497ms:
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

2026-05-03T06:10:15.894929Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.6 seconds
Output:

CommandType Name       Version Source                                                       
----------- ----       ------- ------                                                       
Application python.exe 0.0.0.0 C:\Users\winst\AppData\Local\Microsoft\WindowsApps\python.exe



 exited 1 in 569ms:

CommandType Name       Version Source                                                       
----------- ----       ------- ------                                                       
Application python.exe 0.0.0.0 C:\Users\winst\AppData\Local\Microsoft\WindowsApps\python.exe



2026-05-03T06:10:15.975075Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.7 seconds
Output:
rg: regex parse error:
    (?:name=[^]+ compact_v5/MAIN/agent/tools)
            ^^^
error: unclosed character class

 exited 1 in 650ms:
rg: regex parse error:
    (?:name=[^]+ compact_v5/MAIN/agent/tools)
            ^^^
error: unclosed character class

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-ChildItem compact_v5/MAIN/agent/tools -Filter *.py | Select-String -Pattern 'name=\"' | Select-Object -First 120" in D:\Github\sagemaker-coding-agent
 succeeded in 606ms:

compact_v5\MAIN\agent\tools\bash.py:209:        name="bash",
compact_v5\MAIN\agent\tools\edit_file.py:261:        name="edit_file",
compact_v5\MAIN\agent\tools\glob.py:143:        name="glob",
compact_v5\MAIN\agent\tools\grep.py:163:        name="grep",
compact_v5\MAIN\agent\tools\list_dir.py:96:        name="list_dir",
compact_v5\MAIN\agent\tools\notebook_edit.py:212:        name="notebook_edit",
compact_v5\MAIN\agent\tools\python_exec.py:282:        name="python_exec",
compact_v5\MAIN\agent\tools\read_file.py:220:        name="read_file",
compact_v5\MAIN\agent\tools\skill.py:181:        name="skill",
compact_v5\MAIN\agent\tools\skill_propose_patch.py:124:        name="skill_propose_patch",
compact_v5\MAIN\agent\tools\task.py:152:        name="task",
compact_v5\MAIN\agent\tools\tool_search.py:344:        name="tool_search",
compact_v5\MAIN\agent\tools\view_image.py:163:        name="view_image",
compact_v5\MAIN\agent\tools\write_file.py:133:        name="write_file",



codex
There is one larger architectural concern to verify: read-only agents are given `task` unconditionally. Since `task` can request `build`, `general`, or `fork`, a read-only agent may be able to regain mutating tools through a child. I’m checking the task dispatch context to see whether descendants are constrained elsewhere.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "parent_depth|parent_engine|_subagent_depth|tool.execute|context=.*plan_mode|agent_kind" compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/tools/task.py compact_v5/MAIN/agent/subagent/spawn.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/core/query_engine.py | ForEach-Object { if ($i -ge 300 -and $i -le 460) { '"'{0,4}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/core/query_engine.py | ForEach-Object { if ($i -ge 520 -and $i -le 700) { '"'{0,4}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 445ms:
compact_v5/MAIN/agent/tools/task.py:22:the parent QueryEngine via `context["parent_engine"]` so the child can share
compact_v5/MAIN/agent/tools/task.py:86:      - context["parent_engine"]: the parent QueryEngine. Used to (a) share
compact_v5/MAIN/agent/tools/task.py:89:      - context["parent_depth"] (optional, default 0): the parent's depth.
compact_v5/MAIN/agent/tools/task.py:112:    if not isinstance(context, dict) or "parent_engine" not in context:
compact_v5/MAIN/agent/tools/task.py:114:            "Error: task tool requires `context['parent_engine']` to spawn a "
compact_v5/MAIN/agent/tools/task.py:118:    parent_engine = context["parent_engine"]
compact_v5/MAIN/agent/tools/task.py:119:    parent_depth = int(context.get("parent_depth", 0))
compact_v5/MAIN/agent/tools/task.py:127:        parent_engine=parent_engine,
compact_v5/MAIN/agent/tools/task.py:130:        parent_depth=parent_depth,
compact_v5/MAIN/agent/subagent/spawn.py:68:def _new_child_engine(parent_engine: Any, max_turns: int, agent_type: str = "general") -> Any:
compact_v5/MAIN/agent/subagent/spawn.py:75:    Block B: `agent_type` is forwarded as `agent_kind` so TOKENS.add()
compact_v5/MAIN/agent/subagent/spawn.py:82:        client=parent_engine.client,
compact_v5/MAIN/agent/subagent/spawn.py:84:        budget=parent_engine.budget,            # SHARED — the Phase-9 contract
compact_v5/MAIN/agent/subagent/spawn.py:85:        on_stop_check=parent_engine.on_stop_check,
compact_v5/MAIN/agent/subagent/spawn.py:86:        agent_kind=agent_type,
compact_v5/MAIN/agent/subagent/spawn.py:106:    parent_engine: Any,
compact_v5/MAIN/agent/subagent/spawn.py:109:    parent_depth: int = 0,
compact_v5/MAIN/agent/subagent/spawn.py:132:      - Child's `budget is parent_engine.budget` (object identity).
compact_v5/MAIN/agent/subagent/spawn.py:136:    child_depth = parent_depth + 1
compact_v5/MAIN/agent/subagent/spawn.py:227:    child = _new_child_engine(parent_engine, max_turns=max_turns, agent_type=agent_type)
compact_v5/MAIN/agent/subagent/spawn.py:231:    # context picks up the correct `parent_depth` via
compact_v5/MAIN/agent/subagent/spawn.py:232:    # `getattr(self, "_subagent_depth", 0)`. Without this line, nested
compact_v5/MAIN/agent/subagent/spawn.py:233:    # `task` chains all see parent_depth=0 and the recursion guard never
compact_v5/MAIN/agent/subagent/spawn.py:235:    child._subagent_depth = child_depth
compact_v5/MAIN/agent/subagent/spawn.py:243:    parent_msgs_snapshot = copy.deepcopy(parent_engine.messages)
compact_v5/MAIN/agent/subagent/spawn.py:303:        and parent_engine.skill_manager is not None
compact_v5/MAIN/agent/subagent/spawn.py:306:            ok, _msg = parent_engine.skill_manager.activate(agent_def.auto_load_skill)
compact_v5/MAIN/agent/subagent/spawn.py:311:                _skill_body = parent_engine.skill_manager.get_active_skill_prompt(
compact_v5/MAIN/agent/subagent/spawn.py:312:                    session_id=getattr(parent_engine, "session_id", ""),
compact_v5/MAIN/agent/subagent/spawn.py:381:    if parent_engine.messages != parent_msgs_snapshot:
compact_v5/MAIN/agent/subagent/spawn.py:388:                "Internal error: parent_engine.messages was mutated by "
compact_v5/MAIN/agent/core/query_engine.py:95:    """Map any tool-execute return value into a Bedrock tool_result text string.
compact_v5/MAIN/agent/core/query_engine.py:170:        agent_kind: str = "parent",
compact_v5/MAIN/agent/core/query_engine.py:200:        self.agent_kind = agent_kind
compact_v5/MAIN/agent/core/query_engine.py:269:        # parent_engine forwarding).
compact_v5/MAIN/agent/core/query_engine.py:472:                    agent_kind=self.agent_kind,
compact_v5/MAIN/agent/core/query_engine.py:543:                        _is_sub = self.agent_kind != "parent"
compact_v5/MAIN/agent/core/query_engine.py:844:                # `parent_engine` is passed for Phase 9 task tool — the sub-agent
compact_v5/MAIN/agent/core/query_engine.py:849:                    raw = tool.execute(_repaired_input, context={
compact_v5/MAIN/agent/core/query_engine.py:852:                        "parent_engine": self,
compact_v5/MAIN/agent/core/query_engine.py:853:                        "parent_depth": getattr(self, "_subagent_depth", 0),

 succeeded in 505ms:
 520:                         # Cooldown / cap message â€” log once per turn, no
 521:                         # spam since try_attempt returns reason text.
 522:                         output_fn(f"[auto-compact skipped: {_why}]")
 523:             except Exception:
 524:                 pass
 525: 
 526:             # Stop conditions: end_turn / no tool_use blocks â†’ final answer.
 527:             if not response.tool_calls:
 528:                 # Block F2 â€” auto-continuation under iteration budget. Only
 529:                 # parent agents (not sub-agents) and only when CONFIG flag
 530:                 # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
 531:                 # halt has priority inside check_iteration_budget().
 532:                 try:
 533:                     from runtime.config import CONFIG as _CFG_F2
 534:                     if getattr(_CFG_F2, "enable_token_budget_continuation", False):
 535:                         from core.budget_continuation import (
 536:                             check_iteration_budget,
 537:                             create_budget_tracker,
 538:                             ContinueDecision,
 539:                             StopDecision,
 540:                         )
 541:                         if self._budget_tracker is None:
 542:                             self._budget_tracker = create_budget_tracker()
 543:                         _is_sub = self.agent_kind != "parent"
 544:                         _sc = 0.0
 545:                         try:
 546:                             from runtime.tokens import TOKENS as _TOKENS_F2
 547:                             _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
 548:                         except Exception:
 549:                             _sc = 0.0
 550:                         _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
 551:                         decision = check_iteration_budget(
 552:                             self._budget_tracker,
 553:                             iter_used=self.budget.used(),
 554:                             iter_total=self.budget.total(),
 555:                             is_subagent=_is_sub,
 556:                             session_cost=_sc,
 557:                             session_cost_limit=_scl,
 558:                         )
 559:                         if isinstance(decision, ContinueDecision):
 560:                             # Surface the assistant's interim text + nudge to keep
 561:                             # working. Continuing the for-loop re-invokes Bedrock.
 562:                             if response.text:
 563:                                 output_fn(response.text)
 564:                             self.messages.append({
 565:                                 "role": "user",
 566:                                 "content": decision.nudge_message,
 567:                             })
 568:                             continue
 569:                         # Codex iter-1 finding #1 lock: surface StopDecision
 570:                         # telemetry. Runnable logs the equivalent completion
 571:                         # event at query.ts:1343-1354. v5 routes through the
 572:                         # AUDIT singleton so /diffs / /regression forensics
 573:                         # can observe budget-driven stops; stderr-style
 574:                         # logging.info also surfaces it for headless runs.
 575:                         if isinstance(decision, StopDecision):
 576:                             _ce = decision.completion_event
 577:                             _reason = decision.reason or ""
 578:                             if _ce is not None or _reason in {"cost_cap", "diminishing", "above_threshold"}:
 579:                                 logging.info(
 580:                                     "[budget-continuation] stop reason=%s event=%s",
 581:                                     _reason, _ce,
 582:                                 )
 583:                                 try:
 584:                                     from runtime.audit import AUDIT as _AUDIT_F2
 585:                                     _AUDIT_F2.log(
 586:                                         session_id=self.session_id,
 587:                                         action="budget_continuation_stop",
 588:                                         tool_name="(engine)",
 589:                                         parameters={"reason": _reason},
 590:                                         result_summary=str(_ce or ""),
 591:                                         user_approved=False,
 592:                                     )
 593:                                 except Exception:
 594:                                     pass
 595:                 except Exception as _f2_exc:
 596:                     # Codex iter-1 finding #2 lock: best-effort wrap MUST
 597:                     # surface a diagnostic when F2 is opt-in enabled â€” silent
 598:                     # fail-closed makes opt-in users see "no auto-continue"
 599:                     # with zero clue why. logging.warning matches the
 600:                     # cost-runtime warning pattern at [Cost ...] above.
 601:                     logging.warning(
 602:                         "[budget-continuation] %s: %s",
 603:                         type(_f2_exc).__name__, _f2_exc,
 604:                     )
 605: 
 606:                 stop_reason = "end_turn"
 607:                 if response.text:
 608:                     output_fn(response.text)
 609:                 break
 610: 
 611:             # Tool dispatch â€” emit one tool_result per tool_use call.
 612:             tool_results: List[Dict[str, Any]] = []
 613:             for call in response.tool_calls:
 614:                 tool = find_tool_by_name(tools, call.name)
 615:                 if tool is None:
 616:                     # Unknown tool name â€” return error to model so it can
 617:                     # recover (v4 parity: dispatch never raises).
 618:                     tool_results.append({
 619:                         "type": "tool_result",
 620:                         "tool_use_id": call.id,
 621:                         "content": f"Error: unknown tool '{call.name}'",
 622:                         "is_error": True,
 623:                     })
 624:                     # Block B (Codex finding #2 HIGH lock): every dispatch
 625:                     # path â€” including unknown-tool â€” must be audited so
 626:                     # forensics can see what the model attempted to call.
 627:                     try:
 628:                         from runtime.audit import AUDIT as _AUDIT
 629:                         _AUDIT.log(
 630:                             session_id=self.session_id,
 631:                             action="tool_unknown",
 632:                             tool_name=call.name,
 633:                             parameters=call.input or {},
 634:                             result_summary=f"unknown tool '{call.name}'",
 635:                             user_approved=False,
 636:                         )
 637:                     except Exception:
 638:                         pass
 639:                     continue
 640: 
 641:                 # Plan-mode dispatch gate â€” strict allowlist by name (v4
 642:                 # PLAN_MODE_ALLOWED_TOOLS, sagemaker_agent.py:9390 + 6905).
 643:                 # Codex Phase-08 finding (medium): the prior version exempted
 644:                 # `always_load=True` tools, which would let `tool_search`
 645:                 # itself (or any future always_load mutating tool) execute
 646:                 # in plan mode despite v4 forbidding it. The allowlist is
 647:                 # defense-in-depth on top of registry filtering: even if a
 648:                 # disallowed mutating tool reaches dispatch (e.g. discovered
 649:                 # via tool_search after enabled=True), it cannot run.
 650:                 # Lock test: test_engine_plan_mode_blocks_always_load_mutating_tool.
 651:                 if plan_mode and call.name not in PLAN_MODE_ALLOWED_TOOLS:
 652:                     tool_results.append({
 653:                         "type": "tool_result",
 654:                         "tool_use_id": call.id,
 655:                         "content": (
 656:                             f"Error: tool '{call.name}' is not in "
 657:                             "PLAN_MODE_ALLOWED_TOOLS; blocked in plan mode."
 658:                         ),
 659:                         "is_error": True,
 660:                     })
 661:                     # Block B (Codex finding #2 HIGH lock): plan-mode
 662:                     # block is an audit-relevant security event.
 663:                     try:
 664:                         from runtime.audit import AUDIT as _AUDIT
 665:                         _AUDIT.log(
 666:                             session_id=self.session_id,
 667:                             action="plan_mode_blocked",
 668:                             tool_name=call.name,
 669:                             parameters=call.input or {},
 670:                             result_summary=(
 671:                                 f"plan-mode allowlist blocked '{call.name}'"
 672:                             ),
 673:                             user_approved=False,
 674:                         )
 675:                     except Exception:
 676:                         pass
 677:                     continue
 678: 
 679:                 # Block C â€” exec-limit gate (PS#7 fix). Only bash +
 680:                 # python_exec count toward this limit. v4 verbatim
 681:                 # message at sagemaker_agent.py:9482-9489 â€” preserved
 682:                 # so the model can recover by switching to non-counted
 683:                 # tools.
 684:                 if call.name in {"bash", "python_exec"}:
 685:                     from runtime.config import CONFIG as _CFG
 686:                     cap = getattr(_CFG, "max_exec_calls_per_session", 200)
 687:                     if self._exec_call_count >= cap:
 688:                         tool_results.append({
 689:                             "type": "tool_result",
 690:                             "tool_use_id": call.id,
 691:                             "content": (
 692:                                 f"Blocked: bash + python_exec call limit "
 693:                                 f"reached ({cap}/session). "
 694:                                 "OTHER TOOLS STILL WORK: read_file, grep, "
 695:                                 "glob, edit_file, write_file, notebook_edit, "
 696:                                 "task, ask_user, view_image, web_fetch are "
 697:                                 "NOT counted by this limit."
 698:                             ),
 699:                             "is_error": True,
 700:                         })

 succeeded in 506ms:
 300:         if not hasattr(self, "_rate_limiter"):
 301:             from ui.approval_dialog import RateLimiter
 302:             from runtime.config import CONFIG as _CFG
 303:             self._rate_limiter = RateLimiter(
 304:                 max_per_minute=getattr(_CFG, "max_user_messages_per_minute", 100),
 305:                 max_per_session=getattr(_CFG, "max_user_messages_per_session", 1500),
 306:             )
 307:         _rate_msg = self._rate_limiter.check()
 308:         if _rate_msg is not None:
 309:             return QueryResult(
 310:                 text=_rate_msg,
 311:                 messages=list(self.messages),
 312:                 stop_reason="rate_limited",
 313:                 turns_used=0,
 314:                 budget_used=self.budget.used(),
 315:                 error=_rate_msg,
 316:             )
 317: 
 318:         # Append user turn (Bedrock requires alternation; merge into trailing
 319:         # user if needed â€” matches v4 sagemaker_agent.py:8744).
 320:         if self.messages and self.messages[-1].get("role") == "user":
 321:             prev = self.messages[-1]
 322:             prev_content = prev.get("content", "")
 323:             if isinstance(prev_content, str):
 324:                 prev["content"] = prev_content + "\n\n" + user_message
 325:             elif isinstance(prev_content, list):
 326:                 prev_content.append({"type": "text", "text": user_message})
 327:             else:
 328:                 self.messages.append({"role": "user", "content": user_message})
 329:         else:
 330:             self.messages.append({"role": "user", "content": user_message})
 331: 
 332:         # Defer-import to avoid circular import at module-load.
 333:         from tools.registry import (
 334:             PLAN_MODE_ALLOWED_TOOLS,
 335:             apply_tool_search_deferral,
 336:             find_tool_by_name,
 337:         )
 338:         from tools.tool_search import tool_search_discovered_names
 339: 
 340:         # Phase 10 wiring (Codex BLOCKER fix): if a SkillManager is bound to
 341:         # this engine, inject (a) the active skill body into the dynamic
 342:         # tail of the system prompt and (b) a Hermes-filtered "skills
 343:         # relevant to this task" reminder onto the first user turn so the
 344:         # model sees the suggestions. The Hermes filter passes the visible
 345:         # tool names so skills with `requires_tools` are pruned when the
 346:         # required tools aren't currently available.
 347:         effective_system_prompt = system_prompt
 348:         if self.skill_manager is not None:
 349:             try:
 350:                 active_block = self.skill_manager.get_active_skill_prompt(
 351:                     session_id=self.session_id,
 352:                 )
 353:                 if active_block:
 354:                     effective_system_prompt = system_prompt + active_block
 355:                 visible_tool_names = {t.name for t in tools}
 356:                 relevant = self.skill_manager.discover_relevant(
 357:                     user_message, active_tools=visible_tool_names,
 358:                 )
 359:                 if relevant:
 360:                     reminder = (
 361:                         "\n\n# Skills Relevant to This Task\n"
 362:                         "Consider using: " + ", ".join(relevant) +
 363:                         "\nUse the `skill` tool to activate one if it matches."
 364:                     )
 365:                     last_user = self.messages[-1]
 366:                     content = last_user.get("content")
 367:                     if isinstance(content, str):
 368:                         last_user["content"] = content + reminder
 369:                     elif isinstance(content, list):
 370:                         content.append({"type": "text", "text": reminder})
 371:             except Exception as exc:  # noqa: BLE001 â€” skill machinery never raises into agent loop
 372:                 logging.warning("[skill-wiring] %s: %s", type(exc).__name__, exc)
 373: 
 374:         last_text = ""
 375:         stop_reason = ""
 376:         turns_used = 0
 377: 
 378:         for turn in range(self.max_turns):
 379:             # User-requested stop (Phase 11 wires this to the Stop button).
 380:             if self.on_stop_check and self.on_stop_check():
 381:                 output_fn("[Stopped by user]")
 382:                 stop_reason = "user_stop"
 383:                 break
 384: 
 385:             # Block M-2 (PORT_LOG #084) â€” structured-output retry-limit
 386:             # guard. When `synthetic_output_tool_name` is configured, count
 387:             # how many times the model produced a malformed structured
 388:             # output (each tool_use of that synthetic tool counts). Halt
 389:             # cleanly at the retry limit instead of looping forever.
 390:             if self.synthetic_output_tool_name:
 391:                 _calls_now = count_tool_calls(
 392:                     self.messages, self.synthetic_output_tool_name,
 393:                 )
 394:                 _calls_this_run = _calls_now - self._initial_structured_output_calls
 395:                 if _calls_this_run >= self.max_structured_output_retries:
 396:                     output_fn(
 397:                         f"[error_max_structured_output_retries: "
 398:                         f"failed to provide valid structured output after "
 399:                         f"{self.max_structured_output_retries} attempts]"
 400:                     )
 401:                     stop_reason = "error_max_structured_output_retries"
 402:                     break
 403: 
 404:             # Budget gate â€” shared with sub-agents (Phase 9).
 405:             if not self.budget.consume():
 406:                 used, total = self.budget.used(), self.budget.total()
 407:                 output_fn(
 408:                     f"[Budget exhausted: {used}/{total} iterations used. "
 409:                     "Adjust IterationBudget or start a new session.]"
 410:                 )
 411:                 stop_reason = "budget_exhausted"
 412:                 break
 413: 
 414:             # Phase 7 wiring contract: per-turn deferral + discovery merge.
 415:             visible_tools, deferred_names = apply_tool_search_deferral(
 416:                 tools, enabled=True,
 417:             )
 418:             if self._discovered_tool_names:
 419:                 # Promote previously-discovered tools from deferred â†’ visible.
 420:                 discovered = {n for n in self._discovered_tool_names if n in deferred_names}
 421:                 if discovered:
 422:                     promoted = [
 423:                         t for t in tools
 424:                         if t.name in discovered and t.name not in {v.name for v in visible_tools}
 425:                     ]
 426:                     visible_tools = visible_tools + promoted
 427:                     deferred_names = [n for n in deferred_names if n not in discovered]
 428: 
 429:             # If any names remain deferred, surface them as a system reminder
 430:             # so the model knows they exist and how to load them.
 431:             turn_messages = list(self.messages)
 432:             if deferred_names:
 433:                 turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)
 434: 
 435:             # Bedrock invocation.
 436:             try:
 437:                 response = self.client.chat(
 438:                     messages=turn_messages,
 439:                     system=effective_system_prompt,
 440:                     tools=_build_tools_api_payload(visible_tools),
 441:                     max_tokens=max_tokens,
 442:                     temperature=temperature,
 443:                     thinking_enabled=thinking_enabled,
 444:                     thinking_budget=thinking_budget,
 445:                 )
 446:             except Exception as exc:  # noqa: BLE001 â€” classify and surface
 447:                 category, recovery, debug = ErrorClassifier.classify(exc)
 448:                 output_fn(f"[Bedrock {category}: {debug}]")
 449:                 if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
 450:                     stop_reason = "context_overflow"
 451:                 else:
 452:                     stop_reason = "fatal_error"
 453:                 return QueryResult(
 454:                     text=last_text,
 455:                     messages=list(self.messages),
 456:                     stop_reason=stop_reason,
 457:                     turns_used=turns_used,
 458:                     budget_used=self.budget.used(),
 459:                     error=f"{category}: {debug}",
 460:                 )

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/core/query_engine.py | ForEach-Object { if ($i -ge 828 -and $i -le 862) { '"'{0,4}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 416ms:
 828:                                 f"approval gate failed: {_approval_exc}; "
 829:                                 "defaulting to deny"
 830:                             )
 831:                             tool_results.append({
 832:                                 "type": "tool_result",
 833:                                 "tool_use_id": call.id,
 834:                                 "content": (
 835:                                     f"Approval gate error for `{call.name}`; "
 836:                                     f"defaulting to deny."
 837:                                 ),
 838:                                 "is_error": True,
 839:                             })
 840:                             continue
 841: 
 842:                 # Execute. Tool implementations may raise; we trap and surface
 843:                 # the error to the model rather than the human user.
 844:                 # `parent_engine` is passed for Phase 9 task tool â€” the sub-agent
 845:                 # spawn needs the parent's IterationBudget + BedrockClient (ADR-015).
 846:                 try:
 847:                     if call.name in {"bash", "python_exec"}:
 848:                         self._exec_call_count += 1
 849:                     raw = tool.execute(_repaired_input, context={
 850:                         "active_tools": tools,
 851:                         "plan_mode": plan_mode,
 852:                         "parent_engine": self,
 853:                         "parent_depth": getattr(self, "_subagent_depth", 0),
 854:                         # Block I-1/I-5: edit_file + write_file consume this
 855:                         # to auto-activate skills with `paths:` frontmatter.
 856:                         "skill_manager": self.skill_manager,
 857:                         "session_id": self.session_id,
 858:                     })
 859:                     text = _coerce_tool_result_to_text(raw)
 860:                     text = _truncate_tool_result(text, tool.max_result_size_chars)
 861:                     tool_results.append({
 862:                         "type": "tool_result",

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/tools/tool_search.py | ForEach-Object { if ($i -ge 260 -and $i -le 370) { '"'{0,4}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/tools/registry.py | ForEach-Object { if ($i -ge 300 -and $i -le 390) { '"'{0,4}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "def _tool_search_executor|active_tools|tool_search_discovered_names|should_defer" compact_v5/MAIN/agent/tools/tool_search.py compact_v5/MAIN/agent/tools/registry.py' in D:\Github\sagemaker-coding-agent
 succeeded in 492ms:
 260:     Phase-7 deliverable for Phase-8 wiring. Phase 8 query_engine calls this
 261:     on each tool_result for tool_search, then includes those tools in the
 262:     next turn's `tools=` API param so they become callable.
 263: 
 264:     Returns an empty list if the marker is absent or empty.
 265:     """
 266:     start = tool_result_text.find(_DISCOVERED_NAMES_TAG)
 267:     if start < 0:
 268:         return []
 269:     start += len(_DISCOVERED_NAMES_TAG)
 270:     end = tool_result_text.find(_DISCOVERED_NAMES_TAG_END, start)
 271:     if end < 0:
 272:         return []
 273:     csv = tool_result_text[start:end].strip()
 274:     if not csv:
 275:         return []
 276:     return [n.strip() for n in csv.split(",") if n.strip()]
 277: 
 278: 
 279: # ============================================================
 280: # Executor
 281: # ============================================================
 282: 
 283: def _tool_search_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
 284:     """Phase-7 tool_search executor.
 285: 
 286:     Sequence:
 287:       1. Validate query (non-empty string).
 288:       2. Normalise max_results.
 289:       3. Resolve active tool pool from context (Codex finding 2).
 290:       4. Filter to deferred subset.
 291:       5. Bare exact name fast path â†’ return that tool's schema directly.
 292:       6. Dispatch on query mode (select / +required / keyword).
 293:       7. Return `<functions>` block with matched schemas + discovered-names marker.
 294:     """
 295:     query = args.get("query")
 296:     if not isinstance(query, str) or not query.strip():
 297:         return "Error: query is required and must be a non-empty string"
 298: 
 299:     raw_max = args.get("max_results", 5)
 300:     try:
 301:         max_results = int(raw_max)
 302:     except (TypeError, ValueError):
 303:         return f"Error: max_results must be an integer; got {raw_max!r}"
 304:     max_results = max(1, min(max_results, 50))
 305: 
 306:     active_tools = _resolve_active_tools(context)
 307:     deferred_tools = [t for t in active_tools if is_deferred_tool(t.name)]
 308: 
 309:     if not deferred_tools:
 310:         return (
 311:             "<functions>\n"
 312:             "(no deferred tools in current active set -- apply_tool_search_deferral "
 313:             "may be disabled, or no tools have should_defer=True in this pool)\n"
 314:             "</functions>\n"
 315:             f"{_DISCOVERED_NAMES_TAG}{_DISCOVERED_NAMES_TAG_END}"
 316:         )
 317: 
 318:     q = query.strip()
 319: 
 320:     # Bare exact-name fast path (Codex Phase-07 review)
 321:     bare_match = _bare_exact_name_match(q, deferred_tools)
 322:     if bare_match is not None:
 323:         return _format_functions_block([bare_match], deferred_tools)
 324: 
 325:     if q.lower().startswith("select:"):
 326:         matches = _select_query(q, deferred_tools)
 327:     elif q.startswith("+"):
 328:         matches = _required_term_query(q, deferred_tools, max_results)
 329:     else:
 330:         matches = _keyword_query(q, deferred_tools, max_results)
 331: 
 332:     return _format_functions_block(matches, deferred_tools)
 333: 
 334: 
 335: # ============================================================
 336: # Idempotent registration â€” always_load=True (never deferred)
 337: # ============================================================
 338: 
 339: def _register():
 340:     """Idempotent registration of tool_search."""
 341:     if find_tool_by_name(all_registered(), "tool_search") is not None:
 342:         return find_tool_by_name(all_registered(), "tool_search")
 343:     return register(build_tool(
 344:         name="tool_search",
 345:         description=_DESCRIPTION,
 346:         input_schema=_INPUT_SCHEMA,
 347:         execute=_tool_search_executor,
 348:         is_read_only=True,
 349:         is_destructive=False,
 350:         is_concurrency_safe=True,
 351:         requires_approval=False,
 352:         always_load=True,             # NEVER deferred itself (Runnable parity)
 353:         search_hint="load deferred tool schemas",
 354:     ))

 succeeded in 498ms:
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

 succeeded in 501ms:
compact_v5/MAIN/agent/tools/tool_search.py:20:consumable structured form via `tool_search_discovered_names()`.
compact_v5/MAIN/agent/tools/tool_search.py:28:  3. Extract discovered names via `tool_search_discovered_names(...)` from
compact_v5/MAIN/agent/tools/tool_search.py:86:    - Otherwise → deferred IFF `should_defer=True`.
compact_v5/MAIN/agent/tools/tool_search.py:99:    return tool.should_defer
compact_v5/MAIN/agent/tools/tool_search.py:135:def _resolve_active_tools(context: Optional[Dict[str, Any]]) -> List[ToolRecord]:
compact_v5/MAIN/agent/tools/tool_search.py:140:    query_engine MUST pass `context["active_tools"]`. If absent, fall back to
compact_v5/MAIN/agent/tools/tool_search.py:143:    if context and isinstance(context.get("active_tools"), list):
compact_v5/MAIN/agent/tools/tool_search.py:144:        return list(context["active_tools"])
compact_v5/MAIN/agent/tools/tool_search.py:146:        "[tool_search] context['active_tools'] not provided; falling back to "
compact_v5/MAIN/agent/tools/tool_search.py:147:        "all_registered(). Phase 8 query_engine MUST pass active_tools so deny-"
compact_v5/MAIN/agent/tools/tool_search.py:257:def tool_search_discovered_names(tool_result_text: str) -> List[str]:
compact_v5/MAIN/agent/tools/tool_search.py:283:def _tool_search_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
compact_v5/MAIN/agent/tools/tool_search.py:306:    active_tools = _resolve_active_tools(context)
compact_v5/MAIN/agent/tools/tool_search.py:307:    deferred_tools = [t for t in active_tools if is_deferred_tool(t.name)]
compact_v5/MAIN/agent/tools/tool_search.py:313:            "may be disabled, or no tools have should_defer=True in this pool)\n"
compact_v5/MAIN/agent/tools/registry.py:71:    should_defer: bool                       # Runnable: shouldDefer
compact_v5/MAIN/agent/tools/registry.py:103:    should_defer: bool = False
compact_v5/MAIN/agent/tools/registry.py:317:    """Runnable parity (Phase 7 ADR-013): defer `should_defer=True` tools behind
compact_v5/MAIN/agent/tools/registry.py:332:    A tool is deferred IFF `should_defer=True` AND `always_load=False` AND
compact_v5/MAIN/agent/tools/registry.py:365:        if t.should_defer:

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "tool_search_discovered_names|_discovered_tool_names" compact_v5/MAIN/agent/core/query_engine.py' in D:\Github\sagemaker-coding-agent
 succeeded in 387ms:
14:    * `tool_search_discovered_names()` extraction from tool_search results.
226:        self._discovered_tool_names: Set[str] = set()
258:        self._discovered_tool_names = set()
338:        from tools.tool_search import tool_search_discovered_names
418:            if self._discovered_tool_names:
420:                discovered = {n for n in self._discovered_tool_names if n in deferred_names}
884:                        discovered = tool_search_discovered_names(text)
886:                            self._discovered_tool_names.update(discovered)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/core/query_engine.py | ForEach-Object { if ($i -ge 872 -and $i -le 892) { '"'{0,4}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 444ms:
 872:                             session_id=self.session_id,
 873:                             action="tool_dispatch",
 874:                             tool_name=call.name,
 875:                             parameters=call.input or {},
 876:                             result_summary=text[:500] if isinstance(text, str) else "",
 877:                             user_approved=True,
 878:                         )
 879:                     except Exception:
 880:                         pass
 881:                     # Phase 7 wiring: extract discovered names from tool_search
 882:                     # results and add to the next turn's tools= payload.
 883:                     if call.name == "tool_search":
 884:                         discovered = tool_search_discovered_names(text)
 885:                         if discovered:
 886:                             self._discovered_tool_names.update(discovered)
 887:                 except Exception as exc:  # noqa: BLE001 â€” surface to model
 888:                     logging.warning(
 889:                         "[query_engine] tool '%s' raised %s: %s",
 890:                         call.name, type(exc).__name__, exc,
 891:                     )
 892:                     tool_results.append({

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "workspace" compact_v5/MAIN/agent/runtime/config.py | Select-Object -First 40' in D:\Github\sagemaker-coding-agent
 succeeded in 591ms:
42:    workspace: str = os.getcwd()
65:    allowed_paths: list = None  # Additional directories accessible outside workspace
191:def _load_config_file(workspace: str) -> Dict:
192:    """Load optional agent_config.json or agent_config.jsonc from workspace."""
194:        path = os.path.join(workspace, name)
208:    ext = _load_config_file(config.workspace)
279:    # Allowed paths — list of absolute directory paths the agent can read AND write outside workspace

codex
**Findings**

1. **HIGH — read-only agents can still regain mutating tools through `task`.**  
   [spawn.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:252) filters read-only agents, but then unconditionally adds `task` and `tool_search` at [spawn.py:257](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:257). The `task` schema still exposes all seven agent types, including `build`, `general`, and `fork`, at [task.py:71](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py:71), and `_task_executor` forwards the requested type unchanged into `spawn_subagent` at [task.py:126](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py:126). The dispatch context only passes `parent_engine` and `parent_depth`, not the caller’s allowed descendant policy, at [query_engine.py:849](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:849).  
   Result: an `explore`/`plan`/`review` agent cannot call `write_file` directly, but can discover/call `task` and spawn a `build` or `general` child with full registry access. That means finding #2 is only partially fixed.

2. **MEDIUM — `test_general_agent_gets_full_registry` is not a sound lock.**  
   The assertion at [test_block_g.py:562](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_g.py:562) uses `assert required in names or required in full`. Since `full` is the registry snapshot, this can pass even when the spawned general child did not receive the required tool. It should assert against `names`, or compare `names` to the expected full registry surface.

**Verified Fixes**

Finding #1 is correctly fixed by code path inspection: build worktree creation is guarded by `if _worktree_path`, workspace is swapped at [spawn.py:327](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:327), `child.run(...)` starts at [spawn.py:342](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:342), and restore happens in `finally` at [spawn.py:351](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:351). If `create_worktree` returns `None`, no swap occurs.

Finding #3 is fixed: `subagent_type` has the seven-type enum at [task.py:71](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py:71), with per-type description at [task.py:75](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py:75).

Finding #4 is fixed: PORT_LOG #090 explicitly defers G-1/G-2 to Block H at [V5_RUNNABLE_PORT_LOG.md:144](/D:/Github/sagemaker-coding-agent/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md:144). I counted 10 columns for rows #089 and #090.

**Axis Verdicts**

AXIS A: **CHANGES_REQUESTED**  
AXIS B: **DRIFTED** due the read-only role surface being structurally bypassable through `task`.  
AXIS C: **ALL_PORTED**

FINAL: **REJECT**

I could not run the local pytest subset in this environment: `pytest` is not on PATH and the WindowsApps `python.exe` shim is inaccessible.
2026-05-03T06:11:52.329158Z ERROR codex_core::session: failed to record rollout items: thread 019dec74-3b95-70b3-a17a-010b2ce19c7b not found
tokens used
66,461
**Findings**

1. **HIGH — read-only agents can still regain mutating tools through `task`.**  
   [spawn.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:252) filters read-only agents, but then unconditionally adds `task` and `tool_search` at [spawn.py:257](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:257). The `task` schema still exposes all seven agent types, including `build`, `general`, and `fork`, at [task.py:71](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py:71), and `_task_executor` forwards the requested type unchanged into `spawn_subagent` at [task.py:126](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py:126). The dispatch context only passes `parent_engine` and `parent_depth`, not the caller’s allowed descendant policy, at [query_engine.py:849](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:849).  
   Result: an `explore`/`plan`/`review` agent cannot call `write_file` directly, but can discover/call `task` and spawn a `build` or `general` child with full registry access. That means finding #2 is only partially fixed.

2. **MEDIUM — `test_general_agent_gets_full_registry` is not a sound lock.**  
   The assertion at [test_block_g.py:562](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_g.py:562) uses `assert required in names or required in full`. Since `full` is the registry snapshot, this can pass even when the spawned general child did not receive the required tool. It should assert against `names`, or compare `names` to the expected full registry surface.

**Verified Fixes**

Finding #1 is correctly fixed by code path inspection: build worktree creation is guarded by `if _worktree_path`, workspace is swapped at [spawn.py:327](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:327), `child.run(...)` starts at [spawn.py:342](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:342), and restore happens in `finally` at [spawn.py:351](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/subagent/spawn.py:351). If `create_worktree` returns `None`, no swap occurs.

Finding #3 is fixed: `subagent_type` has the seven-type enum at [task.py:71](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py:71), with per-type description at [task.py:75](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py:75).

Finding #4 is fixed: PORT_LOG #090 explicitly defers G-1/G-2 to Block H at [V5_RUNNABLE_PORT_LOG.md:144](/D:/Github/sagemaker-coding-agent/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md:144). I counted 10 columns for rows #089 and #090.

**Axis Verdicts**

AXIS A: **CHANGES_REQUESTED**  
AXIS B: **DRIFTED** due the read-only role surface being structurally bypassable through `task`.  
AXIS C: **ALL_PORTED**

FINAL: **REJECT**

I could not run the local pytest subset in this environment: `pytest` is not on PATH and the WindowsApps `python.exe` shim is inaccessible.
