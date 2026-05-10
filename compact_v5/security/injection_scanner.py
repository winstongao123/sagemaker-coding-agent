"""Block C item 0-10 (ADR-020 remap from Block 0) — prompt-injection scanner.

v4-native port of `_scan_for_prompt_injection` + `_INJECTION_PATTERNS`
from `compact_v4/MAIN/agent/sagemaker_agent.py:7509-7541`. The scanner
is used to flag content (skill bodies, tool outputs, user-supplied files)
that may contain instruction-injection attempts before that content is
spliced into the system prompt or shown to the model.

12 patterns + invisible-character class. Per Plan v3 §Block C and
SYNTHESIS_MASTER §Block 0 row 0-10 (MUST, FALSE-POSITIVE-AT-CODE-LEVEL
in the original Block-0 audit but corrected to v4-native port).

PORT_LOG: see #058.
"""
from __future__ import annotations

import re
from typing import List


# ============================================================
# 12 v4-native injection patterns
# ============================================================
#
# These match common instruction-injection shapes seen in user-uploaded
# documents, web-fetched content, and skill bodies. Hits are reported,
# not auto-blocked — the calling site decides whether to refuse or just
# warn.

_INJECTION_PATTERNS: List[tuple] = [
    (re.compile(r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts?|rules?)\b"),
     "ignore-previous-instructions"),
    (re.compile(r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts?)\b"),
     "disregard-previous"),
    (re.compile(r"(?i)\bforget\s+(everything\s+)?(you('?| ha)ve\s+been\s+told|above)\b"),
     "forget-instructions"),
    (re.compile(r"(?i)\b(reveal|display|print|show)\s+(your\s+)?(system\s+)?prompt\b"),
     "reveal-prompt"),
    (re.compile(r"(?i)\bjailbreak\b|\bDAN\b|\bdo\s+anything\s+now\b"),
     "jailbreak-token"),
    (re.compile(r"(?i)\b(act|behave|pretend|roleplay|imagine)\s+(as|you('?re|\s+are))\s+(if\s+)?(an?\s+)?(unrestricted|uncensored|jailbroken|developer|evil|malicious)\b"),
     "roleplay-jailbreak"),
    (re.compile(r"(?i)<(\s*)?(system|/system)(\s*)?>"),
     "fake-system-tag"),
    (re.compile(r"(?i)\[\s*system\s*\]|\[\s*assistant\s*\]"),
     "fake-role-bracket"),
    (re.compile(r"(?i)\bnew\s+(system\s+)?prompt[:.]"),
     "new-prompt-marker"),
    (re.compile(r"(?i)\bend\s+(of\s+)?(prompt|instructions)\b"),
     "end-prompt-marker"),
    (re.compile(r"(?i)\bexecute\s+the\s+following\s+(command|code|script)\b"),
     "execute-following"),
    (re.compile(r"(?i)\bbypass\s+(security|safety|filters?|restrictions?)\b"),
     "bypass-security"),
]


# Invisible / zero-width character class — bidi controls + format chars
# that can be used to hide instructions from human reviewers.
_INVISIBLE_CHARS = re.compile(
    "["
    "​‌‍"  # ZWSP, ZWNJ, ZWJ
    "‎‏"        # LRM, RLM
    "‪-‮"       # bidi formatting
    "⁠-⁤"       # word joiner et al.
    "﻿"              # BOM
    "]"
)


def scan_for_prompt_injection(content: str, source_label: str = "") -> List[str]:
    """Return a list of human-readable warnings for a content blob.

    Empty list = clean. The caller decides what to do with non-empty
    results (typically: log + refuse to splice into the system prompt,
    or surface a warning to the user before continuing).
    """
    if not content or not isinstance(content, str):
        return []
    warnings: List[str] = []
    for pat, label in _INJECTION_PATTERNS:
        if pat.search(content):
            prefix = f"{source_label}: " if source_label else ""
            warnings.append(f"{prefix}injection-pattern '{label}' matched")
    if _INVISIBLE_CHARS.search(content):
        prefix = f"{source_label}: " if source_label else ""
        warnings.append(f"{prefix}invisible/zero-width characters present")
    return warnings


__all__ = ["scan_for_prompt_injection"]
