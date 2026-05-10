"""V5 skills/ — SkillManager + 10 production skills (Phase 10, ADR-016).

Per ADR-016:
- `manager.py` — SkillManager class (discover / read / activate / propose-patch).
- `<10 skill dirs>/SKILL.md` — byte-for-byte port from `compact_v4/MAIN/agent/skills/`:
    batch / clara / design / html / reflexion / report / review /
    security-review / simplify / verify.

PORT_LOG: #025 (manager) + #029 (skill content copied verbatim).
"""
from __future__ import annotations

from .manager import SkillInfo, SkillManager  # noqa: F401  public re-exports
