# Skill self-patching (opt-in)

ONLY when `enable_skill_patching=True`. If False, suggest in chat instead.

**Propose only if ALL 4**:
1. **Repeated**: same correction 3+ times this session.
2. **Non-trivial**: domain knowledge / workflow rule, not a one-off.
3. **Generalisable**: helps future runs.
4. **Real-pitfall**: original SKILL.md caused mistake / broken output.

`memory.md` for facts; skill patches for procedural knowledge meeting all 4.

**HOW**: `skill_propose_patch(name, reason, new_content)` where `new_content` = FULL replacement SKILL.md body (frontmatter included), not a diff. Writes to `.proposed/<ts>.md` for `/skill suggestions`. Live SKILL.md NEVER auto-modified. Mention once.
