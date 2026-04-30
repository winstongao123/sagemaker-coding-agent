# Skill self-patching (opt-in)

ONLY when `enable_skill_patching=True`. If False, don't call `skill_propose_patch`. Suggest in chat instead.

**Propose only if ALL 4 apply**:
1. **Repeated**: same correction 3+ times this session.
2. **Non-trivial**: domain knowledge or non-obvious workflow rule, not a one-off preference.
3. **Generalisable**: helps any future run, not just this session.
4. **Real-pitfall**: original SKILL.md led to actual mistake / broken output / wasted tokens.

`memory.md` for facts. Skill patches for procedural knowledge that meets all 4.

**HOW**: `skill_propose_patch(name, reason, new_content)`. `new_content` is the FULL replacement SKILL.md body (frontmatter included), not a diff. System writes to `.proposed/<ts>.md` for `/skill suggestions`. Live SKILL.md is NEVER auto-modified.

Mention once after proposing. Don't keep nagging.
