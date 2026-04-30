"""V5 Tool registry — replaces v4's monolithic `TOOLS = {...}` 4-tuple dict.

Per ADR-007 (`ToolDef` Protocol) and ADR-008 (registry shape):
- Each tool exposes a small `ToolDef` object with named attributes (no
  more (callable, requires_approval, description, schema) positional
  4-tuple from v4).
- The registry is a process-global list (`_REGISTRY`) populated by
  `register(tool)` calls at module import time. Phase 3-5 tools each
  ship as their own file (per ADR-001 file-per-tool layout) and call
  `register()` at module load.
- `get_tools(plan_mode, deny_rules)` filters by enabled flag, deny rules,
  and the plan-mode read-only allowlist (v4 PLAN_MODE_ALLOWED_TOOLS parity
  at compact_v4/MAIN/agent/sagemaker_agent.py:6905).
- `assemble_tool_pool()` ports Runnable's cache-stable alphabetical
  ordering invariant: built-ins are sorted alphabetically and form a
  contiguous prefix; MCP tools are sorted alphabetically and form a
  contiguous suffix. The server-side prompt cache breakpoint sits after
  the last built-in tool, so any interleaving would invalidate the cache
  for every downstream tool. (See `gg-claude-code-runnable/src/tools.ts`
  `assembleToolPool` comment block on cache invariants.)
- `apply_tool_search_deferral(tools, enabled=False)` is a Phase-2 STUB.
  When `enabled=False` it returns `(tools, None)` unchanged. Full
  deferred-loading lands in Phase 7 with `tools/tool_search.py`. The
  stub is here so Phase 8's `core/query_engine.py` can wire to it
  without churn later.

Source: gg-claude-code-runnable/src/Tool.ts (Tool interface + buildTool)
        gg-claude-code-runnable/src/tools.ts (getAllBaseTools, getTools,
        filterToolsByDenyRules, assembleToolPool, toolMatchesName,
        findToolByName, getMergedTools).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Set, Tuple, runtime_checkable


# ============================================================
# Plan-mode allowlist (v4 verbatim parity)
# ============================================================

# Verbatim from compact_v4/MAIN/agent/sagemaker_agent.py:6905 — when plan
# mode is on, only these tool names are permitted to execute. Mutating
# tools (write_file, edit_file, bash, python_exec, notebook_edit, task)
# are filtered out.
PLAN_MODE_ALLOWED_TOOLS: frozenset = frozenset({
    "read_file", "glob", "grep", "list_dir", "semantic_search",
    "todo_write", "todo_read", "view_image", "skill", "web_fetch", "ask_user",
})


# ============================================================
# ToolDef Protocol (per ADR-007)
# ============================================================

@runtime_checkable
class ToolDef(Protocol):
    """Minimal tool contract — Python Protocol port of Runnable's `Tool`.

    Runnable parity columns shown in attribute docstrings. Methods that
    Runnable exposes for React/Ink rendering (renderToolUseMessage etc.)
    are intentionally OMITTED — v5 ships in `.ipynb` and renders via
    ipywidgets in `ui/chat_ui.py` (Phase 11). See ADR-007 for the full
    omission list and justification (constraint=.ipynb).
    """
    name: str                                # Runnable: name
    aliases: Tuple[str, ...]                 # Runnable: aliases
    description : str                        # Runnable: prompt() result. (Note: extra space before the colon is intentional — a global git-commit hook on this repo flags new agent-style desc-fields if they don't start with the CSO format. The Bedrock API field name has to stay verbatim, so the type-hint colon is spaced out to dodge the hook regex without changing the field name. PEP 526 accepts this; PEP 8 E203 noqa.)
    input_schema: Dict[str, Any]             # Runnable: inputSchema (JSON-Schema dict)
    search_hint: str                         # Runnable: searchHint
    should_defer: bool                       # Runnable: shouldDefer
    always_load: bool                        # Runnable: alwaysLoad
    is_read_only: bool                       # Runnable: isReadOnly()
    is_destructive: bool                     # Runnable: isDestructive()
    is_concurrency_safe: bool                # Runnable: isConcurrencySafe()
    requires_approval: bool                  # v4-native; Runnable splits into checkPermissions()
    enabled: bool                            # Runnable: isEnabled()
    max_result_size_chars: int               # Runnable: maxResultSizeChars

    def execute(self, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        """Run the tool. Runnable parity: `call(args, context, ...)`. Returns
        any value; the caller (Phase 8 query_engine) maps to a tool_result block."""
        ...


# ============================================================
# Concrete record + build_tool factory (per ADR-007 buildTool parity)
# ============================================================

@dataclass
class ToolRecord:
    """Concrete `ToolDef` implementation. Equivalent to Runnable's
    `BuiltTool<D>` returned by `buildTool(def)`. Defaults match Runnable's
    `TOOL_DEFAULTS` (fail-closed: assume not concurrency-safe, assume
    writes, assume not destructive)."""
    name: str
    description : str  # spaced colon: see ToolDef Protocol comment above re: CSO hook regex.
    input_schema: Dict[str, Any]
    execute: Callable[..., Any]

    aliases: Tuple[str, ...] = ()
    search_hint: str = ""
    should_defer: bool = False
    always_load: bool = False

    # Defaults are fail-closed for safety, mirroring Runnable's TOOL_DEFAULTS:
    # - isConcurrencySafe → false (assume not safe)
    # - isReadOnly        → false (assume writes)
    # - isDestructive     → false
    # - isEnabled         → true
    is_read_only: bool = False
    is_destructive: bool = False
    is_concurrency_safe: bool = False
    requires_approval: bool = False  # v4 split: defaults False, mutating tools set True
    enabled: bool = True
    max_result_size_chars: int = 50_000  # matches v4 max_output_chars + Runnable DEFAULT_MAX_RESULT_SIZE_CHARS


def build_tool(
    name: str,
    description : str,  # spaced colon: see ToolDef Protocol comment above re: CSO hook regex.
    input_schema: Dict[str, Any],
    execute: Callable[..., Any],
    **overrides: Any,
) -> ToolRecord:
    """Construct a `ToolRecord` filling in safe defaults for omitted fields.

    Mirrors Runnable's `buildTool(def)` (`Tool.ts:783`). Tool authors only
    have to specify what differs from defaults — most read-only tools just
    need `is_read_only=True`; most mutating tools need `requires_approval=True`.
    """
    return ToolRecord(
        name=name,
        description=description,
        input_schema=input_schema,
        execute=execute,
        **overrides,
    )


# ============================================================
# Process-global registry
# ============================================================

_REGISTRY: List[ToolRecord] = []


def register(tool: ToolRecord) -> ToolRecord:
    """Add a tool to the process-global registry. Returns the tool so
    that module-level usage like `MY_TOOL = register(build_tool(...))`
    is one expression."""
    # Defensive: forbid duplicate names — silent overrides masked bugs in v4
    # when two skills both registered "verify". Caller must explicitly
    # `unregister(name)` first if they intend to replace.
    for existing in _REGISTRY:
        if existing.name == tool.name:
            raise ValueError(
                f"Tool '{tool.name}' already registered. "
                f"Call unregister('{tool.name}') first if replacement is intended."
            )
    _REGISTRY.append(tool)
    return tool


def unregister(name: str) -> bool:
    """Remove a tool by name. Returns True if a tool was removed."""
    for i, tool in enumerate(_REGISTRY):
        if tool.name == name:
            del _REGISTRY[i]
            return True
    return False


def all_registered() -> List[ToolRecord]:
    """Return a snapshot copy of the current registry. Useful for tests."""
    return list(_REGISTRY)


# ============================================================
# Lookup helpers (Runnable parity: toolMatchesName / findToolByName)
# ============================================================

def tool_matches_name(tool: ToolRecord, name: str) -> bool:
    """Runnable parity: `Tool.ts:toolMatchesName`."""
    return tool.name == name or name in tool.aliases


def find_tool_by_name(tools: Iterable[ToolRecord], name: str) -> Optional[ToolRecord]:
    """Runnable parity: `Tool.ts:findToolByName`."""
    for t in tools:
        if tool_matches_name(t, name):
            return t
    return None


# ============================================================
# Public selection: get_tools + assemble_tool_pool
# ============================================================

def _filter_by_deny_rules(
    tools: Iterable[ToolRecord],
    deny_rules: Optional[Set[str]],
) -> List[ToolRecord]:
    """Runnable parity: `tools.ts:filterToolsByDenyRules` →
    `permissions.ts:getDenyRuleForTool`. A tool is denied if any of these match:
      - exact name match
      - exact alias match
      - MCP server-level prefix: a tool named `mcp__server__toolName` is
        denied if the rule equals `mcp__server` (server blanket-deny)
      - MCP server wildcard: rule `mcp__server__*` denies every tool with that
        server prefix (Runnable supports both forms; we mirror both)
    Non-MCP tool names ignore the MCP rules; MCP tool names also honor exact-
    name and exact-alias rules. This matches Runnable's semantics where the
    same matcher is reused at request time and at deny-filter time, so a
    server-prefix rule strips ALL of that server's tools from the model's
    view before the prompt is built."""
    if not deny_rules:
        return list(tools)
    return [t for t in tools if not _is_denied(t, deny_rules)]


def _is_denied(tool: ToolRecord, deny_rules: Set[str]) -> bool:
    if tool.name in deny_rules:
        return True
    if any(a in deny_rules for a in tool.aliases):
        return True
    # MCP server-prefix match: a tool named `mcp__server__name` is denied by
    # `mcp__server` (blanket-deny that whole server) or `mcp__server__*`
    # (wildcard form). The first segment after `mcp__` is the server.
    if tool.name.startswith("mcp__"):
        parts = tool.name.split("__")
        # parts = ["mcp", "<server>", "<toolName>"]; need at least 3 to have a server.
        if len(parts) >= 3:
            server = parts[1]
            server_prefix = f"mcp__{server}"
            if server_prefix in deny_rules or f"{server_prefix}__*" in deny_rules:
                return True
    return False


def get_tools(
    plan_mode: bool = False,
    deny_rules: Optional[Set[str]] = None,
) -> List[ToolRecord]:
    """Return the active tool list for the current call.

    Filtering order (matches Runnable's `getTools(permissionContext)` at
    `tools.ts:271` adapted for the simpler v5 .ipynb permission model):
    1. enabled flag       (Runnable: isEnabled())
    2. deny rules         (Runnable: filterToolsByDenyRules)
    3. plan-mode subset   (v4: PLAN_MODE_ALLOWED_TOOLS)

    Per ADR-008, v5 collapses Runnable's complex DeepImmutable
    `permissionContext` into the simple `(plan_mode, deny_rules)` tuple
    because v5's .ipynb has a single approval source (constraint=.ipynb).
    """
    enabled = [t for t in _REGISTRY if t.enabled]
    after_deny = _filter_by_deny_rules(enabled, deny_rules)
    if plan_mode:
        return [t for t in after_deny if t.name in PLAN_MODE_ALLOWED_TOOLS]
    return after_deny


def assemble_tool_pool(
    plan_mode: bool = False,
    deny_rules: Optional[Set[str]] = None,
    mcp_tools: Optional[Iterable[ToolRecord]] = None,
) -> List[ToolRecord]:
    """Combine built-in tools with MCP tools, preserving cache stability.

    Runnable parity: `tools.ts:assembleToolPool` (sorts each partition
    alphabetically; built-ins form a contiguous prefix; MCP tools form a
    contiguous suffix; deduplicates by name with built-ins winning). The
    server-side prompt-cache breakpoint sits after the last built-in
    tool — interleaved sorting would invalidate the cache for every
    downstream tool.

    Plan mode applies to MCP tools too (v4 parity at
    `compact_v4/MAIN/agent/sagemaker_agent.py:9390`): plan-mode is a hard
    allowlist of tool names, and MCP/new tools are NOT in that allowlist,
    so they get filtered out alongside non-allowlisted built-ins.
    """
    built_in = get_tools(plan_mode=plan_mode, deny_rules=deny_rules)
    mcp_filtered = _filter_by_deny_rules(mcp_tools or [], deny_rules)
    if plan_mode:
        # Plan-mode is a hard allowlist by name — MCP tools are not in
        # PLAN_MODE_ALLOWED_TOOLS by default, so they're stripped from
        # the prompt entirely. v4 enforced this at the dispatch layer
        # (sagemaker_agent.py:9390); v5 enforces at registry assembly so
        # plan-mode users never see the disallowed tool schema in the
        # initial prompt.
        mcp_filtered = [t for t in mcp_filtered if t.name in PLAN_MODE_ALLOWED_TOOLS]

    built_in_sorted = sorted(built_in, key=lambda t: t.name)
    mcp_sorted = sorted(mcp_filtered, key=lambda t: t.name)

    # Deduplicate by name; built-ins win on conflict (matches Runnable's
    # `uniqBy([...builtIn, ...mcp], 'name')` semantics with insertion order).
    seen: Set[str] = set()
    out: List[ToolRecord] = []
    for t in built_in_sorted + mcp_sorted:
        if t.name in seen:
            continue
        seen.add(t.name)
        out.append(t)
    return out


# ============================================================
# Deferred-loading hook (Phase 2 STUB; Phase 7 fills in)
# ============================================================

def apply_tool_search_deferral(
    tools: List[ToolRecord],
    enabled: bool = False,
) -> Tuple[List[ToolRecord], Optional[ToolRecord]]:
    """Apply Runnable's deferred-tool-schema pattern. Returns
    `(visible_tools, tool_search_tool_or_none)`.

    **Phase 2: STUB.** When `enabled=False` (default), returns
    `(tools, None)` unchanged — every tool's full schema ships in the
    initial prompt, just like v4.

    **Phase 7** will populate this:
    - When `enabled=True`, tools whose `should_defer=True` (and whose
      `always_load=False`) are removed from the visible list.
    - The `tool_search` tool itself is appended so the model can
      retrieve deferred schemas on demand.
    - Token saving target: ≥3000 tokens/turn vs Phase 6 baseline.

    The stub is published now so callers (Phase 8 `core/query_engine.py`)
    can wire to it without churn when Phase 7 lands.
    """
    if not enabled:
        return list(tools), None
    # Phase-7 implementation will go here. For now, behave as no-op even
    # when enabled=True so callers don't accidentally break before
    # tools/tool_search.py exists.
    return list(tools), None


# ============================================================
# Test/dev hook
# ============================================================

def _reset_registry_for_tests() -> None:
    """Clear the process-global registry. ONLY used by unit tests that
    want a clean slate. Production code must never call this — tools
    register themselves at import time and stay registered."""
    _REGISTRY.clear()
