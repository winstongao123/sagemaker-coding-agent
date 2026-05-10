"""V5 coordinator/user_context.py — Block G3-2 worker-tools + scratchpad context.

PORT_LOG: #093 — Runnable coordinatorMode.ts:80-109 → v5 adaptation.

When coordinator mode is on, the coordinator's first user-message also
gets a "worker tools context" block describing what tools the workers
have available, plus the scratchpad directory (durable cross-worker
knowledge surface).

In v5 the scratchpad lives at `{workspace}/.scratchpad/` and is managed
by `security/scratchpad.py` (Block C / ADR-020 0-5 remap). The coordinator
prompt mentions it so workers know they can write durable notes there.
"""
from __future__ import annotations

from typing import Optional


def get_coordinator_user_context(
    scratchpad_dir: Optional[str] = None,
    workspace: Optional[str] = None,
) -> str:
    """Return the worker-tools-context string injected into the
    coordinator's first user message.

    When `scratchpad_dir` is None, falls back to `{workspace}/.scratchpad`.
    When workspace is also None, the scratchpad section is omitted.
    """
    content = (
        "Workers have access to v5's full tool set unless their agent_type "
        "restricts them (see the Sub-Agent Types section in your system "
        "prompt). The available worker types are: explore, plan, verify, "
        "build, review, general, fork. Tools include read_file, write_file, "
        "edit_file, bash, python_exec, grep, glob, list_dir, view_image, "
        "task (recursive spawn for general/build/fork only), tool_search, "
        "and the v5 document tools (create_word, create_excel, "
        "create_chart, create_markdown, create_notebook, create_pdf)."
    )

    sp = scratchpad_dir
    if sp is None and workspace:
        # Per Block C / ADR-020 0-5: scratchpad lives under workspace.
        sp = f"{workspace}/.scratchpad"
    if sp:
        content += (
            f"\n\nScratchpad directory: {sp}\n"
            "Workers can read and write here without permission prompts. "
            "Use this for durable cross-worker knowledge — structure files "
            "however fits the work."
        )

    return content
