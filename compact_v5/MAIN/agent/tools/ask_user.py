"""V5 tools/ask_user.py — Block T ask_user tool.

PORT_LOG: #103. ADR-038.

Blocks until a user response arrives. v4 used input() in console mode +
ipywidgets in notebook mode. v5 supports the same two modes via a
context-injected response provider.

context["ask_user_response_provider"] (optional) — callable taking
(question) → response string. When set, ask_user uses it instead of
input(). Tests inject a mock provider to drive deterministic behavior.

Without a provider, ask_user falls back to the stdlib `input()` —
which IS blocking and IS interactive. The interactive path is what
runs in the live notebook UI; the provider path is the test surface.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import build_tool, register


def _ask_user_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    question = str(args.get("question") or "").strip()
    if not question:
        return "Error: question is required"

    # Codex iter-1 MEDIUM: support v4 `options` field.
    raw_options = args.get("options")
    options: list = []
    if isinstance(raw_options, list):
        options = [str(o).strip() for o in raw_options if str(o).strip()]
    prompt = question
    if options:
        prompt = (
            question
            + "\nOptions:\n"
            + "\n".join(f"  {i+1}. {o}" for i, o in enumerate(options))
        )

    # Test/UI hook: caller injects a response provider via context.
    provider = (context or {}).get("ask_user_response_provider")
    if callable(provider):
        try:
            response = provider(prompt)
            return str(response or "")
        except Exception as exc:  # noqa: BLE001
            return f"Error: ask_user provider raised: {type(exc).__name__}: {exc}"

    # Live console path: blocks for user input.
    try:
        import builtins
        return builtins.input(f"\n[ask_user] {prompt}\n> ").strip()
    except EOFError:
        return "(no response)"
    except Exception as exc:  # noqa: BLE001
        return f"Error: input() raised: {type(exc).__name__}: {exc}"


_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "options": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of choices to present alongside the question (v4 parity).",
        },
    },
    "required": ["question"],
}


def _register():
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "ask_user") is not None:
        return
    register(build_tool(
        name="ask_user",
        description="Ask the user a clarifying question; blocks until they respond.",
        input_schema=_SCHEMA,
        execute=_ask_user_executor,
        requires_approval=False,
        should_defer=True,
        max_result_size_chars=2000,
    ))
