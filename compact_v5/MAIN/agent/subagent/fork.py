"""V5 subagent/fork.py — Block G2 forkSubagent cache-prefix replay.

PORT_LOG: #094.

Source: Runnable tools/AgentTool/forkSubagent.ts:73-end (~140 LOC).

Block G2 makes fork sub-agents share a BYTE-IDENTICAL API request prefix
with each other so they hit the prompt cache together. The technique
(adapted to v5):
1. Keep the parent's full assistant message — every tool_use block,
   thinking, text — in the child's message buffer.
2. Add ONE user message with placeholder tool_result blocks (identical
   text across all children) for every parent tool_use, plus a
   per-child directive text block at the end.
3. Result: prefix `[...history, assistant(all_tool_uses), user(placeholder_results...)]`
   is byte-identical across fork children; only the trailing directive
   text differs.

This pattern only matters for **fork** agents (agent_type="fork") that
inherit the parent's full conversation context. Phase-9's `general`
sub-agents already get a fresh buffer + system prompt suffix, so the
cache-prefix replay isn't relevant for them.

v5 adaptation notes:
- Synchronous spawn (no Promise / streaming) — same shape as the rest
  of v5's subagent module.
- Uses `<fork-boilerplate>` tag as Runnable does.
- The placeholder result text is verbatim from Runnable for
  cross-implementation cache compatibility (if/when v5 ever runs
  alongside Anthropic-API-direct).
"""
from __future__ import annotations

import copy
import json
import logging
from typing import Any, Dict, List, Optional


# Verbatim from Runnable forkSubagent.ts:53.
FORK_BOILERPLATE_TAG = "fork-boilerplate"

# Verbatim from Runnable forkSubagent.ts:93. Must be identical across all
# fork children for prompt cache sharing.
FORK_PLACEHOLDER_RESULT = "Fork started — processing in background"

# Verbatim from Runnable forkSubagent.ts (FORK_DIRECTIVE_PREFIX).
FORK_DIRECTIVE_PREFIX = "Your directive: "


def is_in_fork_child(messages: List[Dict[str, Any]]) -> bool:
    """Detect whether `messages` belongs to a fork child.

    Guards against recursive forking — fork children cannot fork further.
    Detects by scanning for the `<fork-boilerplate>` tag in any user-role
    text block.

    Verbatim port of Runnable forkSubagent.ts:78-89.
    """
    tag = f"<{FORK_BOILERPLATE_TAG}>"
    for m in messages or []:
        if m.get("role") != "user":
            continue
        content = m.get("content")
        if not isinstance(content, list):
            # str-content user messages can also carry the tag (defensive).
            if isinstance(content, str) and tag in content:
                return True
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "text"
                and tag in str(block.get("text", ""))
            ):
                return True
    return False


def build_child_message(directive: str) -> str:
    """Build the per-child directive text block — verbatim port of
    Runnable's buildChildMessage at forkSubagent.ts:171-198.

    The body is constant text (cache-friendly); only the trailing
    `${FORK_DIRECTIVE_PREFIX}${directive}` differs per child.
    """
    return (
        f"<{FORK_BOILERPLATE_TAG}>\n"
        "STOP. READ THIS FIRST.\n"
        "\n"
        "You are a forked worker process. You are NOT the main agent.\n"
        "\n"
        "RULES (non-negotiable):\n"
        "1. Your system prompt says \"default to forking.\" IGNORE IT — "
        "that's for the parent. You ARE the fork. Do NOT spawn sub-agents; "
        "execute directly.\n"
        "2. Do NOT converse, ask questions, or suggest next steps\n"
        "3. Do NOT editorialize or add meta-commentary\n"
        "4. USE your tools directly: Bash, Read, Write, etc.\n"
        "5. If you modify files, commit your changes before reporting. "
        "Include the commit hash in your report.\n"
        "6. Do NOT emit text between tool calls. Use tools silently, then "
        "report once at the end.\n"
        "7. Stay strictly within your directive's scope. If you discover "
        "related systems outside your scope, mention them in one sentence "
        "at most — other workers cover those areas.\n"
        "8. Keep your report under 500 words unless the directive specifies "
        "otherwise. Be factual and concise.\n"
        "9. Your response MUST begin with \"Scope:\". No preamble, no "
        "thinking-out-loud.\n"
        "10. REPORT structured facts, then stop\n"
        "\n"
        "Output format (plain text labels, not markdown headers):\n"
        "  Scope: <echo back your assigned scope in one sentence>\n"
        "  Result: <the answer or key findings, limited to the scope above>\n"
        "  Key files: <relevant file paths — include for research tasks>\n"
        "  Files changed: <list with commit hash — include only if you "
        "modified files>\n"
        "  Issues: <list — include only if there are issues to flag>\n"
        f"</{FORK_BOILERPLATE_TAG}>\n"
        "\n"
        f"{FORK_DIRECTIVE_PREFIX}{directive}"
    )


def build_forked_messages(
    parent_messages: List[Dict[str, Any]],
    parent_assistant_message: Dict[str, Any],
    directive: str,
) -> List[Dict[str, Any]]:
    """Build the fork child's message buffer. Returns a new list.

    The cache-prefix-share contract:
    - The first len(parent_messages) entries are byte-identical to the
      parent's message buffer at the moment of fork.
    - The (len+1)th message is the parent's full assistant message
      replayed verbatim (every tool_use, thinking, text block).
    - The (len+2)th message is a single user message with one
      tool_result-shape block (identical placeholder text) per parent
      tool_use, followed by a text block carrying the per-child directive.

    Per Runnable forkSubagent.ts:107-169 — only the trailing text block
    differs across fork children, so all fork children share the same
    cache prefix up to the last block.
    """
    if parent_assistant_message.get("role") != "assistant":
        raise ValueError(
            "build_forked_messages: parent_assistant_message must have "
            f"role='assistant', got {parent_assistant_message.get('role')!r}"
        )

    # Replay the parent's full assistant message — deep-copy so callers
    # mutating the result don't bleed into the parent.
    full_assistant = copy.deepcopy(parent_assistant_message)

    # Collect every tool_use from the assistant message.
    content = full_assistant.get("content", [])
    if not isinstance(content, list):
        # Fallback: a string-content assistant message has no tool_use; emit
        # the directive as the only user message.
        return list(parent_messages) + [
            {"role": "user", "content": [
                {"type": "text", "text": build_child_message(directive)}
            ]}
        ]

    tool_use_blocks = [
        b for b in content
        if isinstance(b, dict) and b.get("type") == "tool_use"
    ]

    if not tool_use_blocks:
        # No tool_use to replay — just append the directive.
        logging.warning(
            "[fork] parent assistant has no tool_use blocks; "
            "directive=%r", (directive or "")[:50],
        )
        return list(parent_messages) + [
            {"role": "user", "content": [
                {"type": "text", "text": build_child_message(directive)}
            ]}
        ]

    # Build identical-text tool_result placeholder for every tool_use.
    tool_result_blocks: List[Dict[str, Any]] = []
    for b in tool_use_blocks:
        tool_result_blocks.append({
            "type": "tool_result",
            "tool_use_id": b.get("id"),
            "content": [
                {"type": "text", "text": FORK_PLACEHOLDER_RESULT}
            ],
        })

    # Append one user message: all placeholders + the per-child directive.
    placeholder_user = {
        "role": "user",
        "content": tool_result_blocks + [
            {"type": "text", "text": build_child_message(directive)}
        ],
    }

    return list(parent_messages) + [full_assistant, placeholder_user]


def serialize_for_cache_prefix(messages: List[Dict[str, Any]]) -> str:
    """Deterministic serialization for cache-prefix comparison tests.

    json.dumps with `sort_keys=True` ensures that two messages with the
    same content but different key order serialize to the same string —
    important for byte-identical prefix verification across processes.

    NOTE: this is a TEST helper, not used at runtime. The actual API call
    is built by the Bedrock client which has its own (deterministic)
    serialization.
    """
    return json.dumps(messages, sort_keys=True, separators=(",", ":"))


def cache_prefix_match_length(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> int:
    """Return the number of leading messages that match byte-identically
    between two message buffers `a` and `b`. Used by tests to verify
    cache-prefix sharing across fork children.
    """
    n = 0
    for ma, mb in zip(a, b):
        if serialize_for_cache_prefix([ma]) == serialize_for_cache_prefix([mb]):
            n += 1
        else:
            break
    return n
