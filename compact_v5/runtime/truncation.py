"""V5 runtime/truncation.py — verbatim port of v4 Truncation class.

Source: compact_v4/MAIN/agent/sagemaker_agent.py:756-861.
Lives in `runtime/` because it's used by both `security.manager.truncate_output`
and individual tool executors (bash, python_exec). Keeping it independent
of `security/` avoids a circular import (security imports Truncation,
tools also use Truncation, security is imported by tools).
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, Tuple


class Truncation:
    """Smart truncation for large outputs — saves full content, returns preview.

    v4 verbatim port. Used by:
      - SecurityManager.truncate_output (output cap for any tool)
      - tool_bash (head 100 + tail 50 lines for shell output)
      - tool_python_exec (head/tail for Python output)
      - tool_read_file (head 50 + tail 30 for >500-line files)
    """

    MAX_LINES = 1500
    MAX_BYTES = 30 * 1024  # 30 KB (~7.5K tokens — reduced from 50KB to save context)
    MAX_LINE_LENGTH = 2000
    TRUNCATED_DIR = "./truncated_outputs"

    @classmethod
    def smart_truncate(cls, text: str, head_lines: Optional[int] = None,
                       tail_lines: Optional[int] = None) -> Tuple[str, bool]:
        """Smart truncation: show head + tail, skip middle.
        Uses proportional split (60/40) up to MAX_LINES if head/tail not specified.
        Returns: (truncated_text, was_truncated)"""
        lines = text.split("\n")
        total_lines = len(lines)
        total_bytes = len(text.encode("utf-8"))

        if total_lines <= cls.MAX_LINES and total_bytes <= cls.MAX_BYTES:
            return text, False

        max_keep = max(0, min(cls.MAX_LINES, total_lines - 10))
        if head_lines is None:
            head_lines = int(max_keep * 0.6)
        if tail_lines is None:
            tail_lines = max_keep - head_lines

        if total_lines < head_lines + tail_lines + 10:
            return text, False

        head = lines[:head_lines]
        tail = lines[-tail_lines:] if tail_lines > 0 else []
        skipped = total_lines - head_lines - tail_lines

        result_parts = []
        result_parts.extend(head)
        result_parts.append(
            f"\n... [{skipped} lines skipped — use grep to search "
            f"or read_file with offset={head_lines}] ...\n"
        )
        result_parts.extend(tail)

        return "\n".join(result_parts), True

    @classmethod
    def truncate(cls, text: str, direction: str = "head") -> Tuple[str, bool, Optional[str]]:
        """Truncate text if it exceeds limits.
        Returns: (truncated_text, was_truncated, saved_path)"""
        lines = text.split("\n")
        total_lines = len(lines)
        total_bytes = len(text.encode("utf-8"))

        if total_lines <= cls.MAX_LINES and total_bytes <= cls.MAX_BYTES:
            return text, False, None

        # Save full output to disk (skip in stealth mode)
        from runtime.config import CONFIG
        saved_path: Optional[str] = None
        if not CONFIG.disable_local_traces:
            os.makedirs(cls.TRUNCATED_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_path = os.path.join(cls.TRUNCATED_DIR, f"output_{timestamp}.txt")
            with open(saved_path, "w", encoding="utf-8") as f:
                f.write(text)

        output_lines = []
        current_bytes = 0

        if direction == "head":
            for i, line in enumerate(lines):
                if i >= cls.MAX_LINES:
                    break
                if len(line) > cls.MAX_LINE_LENGTH:
                    line = line[:cls.MAX_LINE_LENGTH] + "..."
                line_bytes = len(line.encode("utf-8")) + 1
                if current_bytes + line_bytes > cls.MAX_BYTES:
                    break
                output_lines.append(line)
                current_bytes += line_bytes
        else:  # tail
            for i in range(len(lines) - 1, -1, -1):
                if len(output_lines) >= cls.MAX_LINES:
                    break
                line = lines[i]
                if len(line) > cls.MAX_LINE_LENGTH:
                    line = line[:cls.MAX_LINE_LENGTH] + "..."
                line_bytes = len(line.encode("utf-8")) + 1
                if current_bytes + line_bytes > cls.MAX_BYTES:
                    break
                output_lines.insert(0, line)
                current_bytes += line_bytes

        truncated_count = total_lines - len(output_lines)
        result = "\n".join(output_lines)
        result += f"\n\n...{truncated_count} lines truncated ({total_bytes:,} bytes total)..."
        if saved_path:
            result += f"\n[Full output saved: {saved_path}]"
        result += (
            f"\n[TIP: Use grep to search, or read_file with offset parameter "
            f"for specific sections.]"
        )
        return result, True, saved_path
