# Claude Code Settings Guide for Number Five Project

**Generated**: 2026-03-26
**Sources**: PS_ClaudeCode_Insights (26 sessions), everything-claude-code, awesome-claude-code, 7 local repos, web research

---

## Winston's Usage Profile (from 26 sessions)

### Strengths
- Iterative refinement (6/26 sessions, strongest type)
- Multi-domain orchestration (QR codes + Power BI + GCP in one session)
- Persistent workflow memory (OneDrive sync encoded in Claude memory)
- 218 Bash calls across sessions (power user)

### Friction Points
1. **Scope ambiguity** (9 instances) — "all", "this", "everything" without specifics
2. **Incremental rework** (6 sessions) — folder moves one at a time instead of plan-first
3. **Misleading counts** — git commit numbers confused between staged/local/remote
4. **Tool capability mismatches** — attempting blocked website scraping

### Recommended Settings Based on Usage

```json
// ~/.claude/settings.json — changes made 2026-03-26
{
  "permissions": {
    "additionalDirectories": [
      "D:\\OneDrive - ArcSage\\Number-Five-Internal"  // was "Arcsage Austrump Winston GCP"
    ]
  }
}
```

---

## Tools Configured for Number Five

### 1. Codex Review Command (`.claude/commands/codex-review.md`)
- Adapted from `codex_reviews/codex-review-command.md`
- Enhanced for Number Five: reads CLAUDE.md + CROSS_DEPENDENCIES.md + ERROR_LOG.md
- Sends 8 cross-dependency checks to Codex as review criteria
- Usage: `/codex-review` after each major phase (1.1, 1.2, etc.)

### 2. Codex Auto-Review Hook (available but NOT auto-enabled)
- Source: `codex_reviews/codex-review-hook.sh`
- Runs after every Claude response that changes files
- For Number Five: recommend manual `/codex-review` at milestones instead of auto
- Reason: auto-review on every change uses too many Codex calls for a large migration

### 3. CLAUDE.md Hierarchy
```
Number-Five/CLAUDE.md              — master reference, 12-step workflow
Main/Email/CLAUDE.md               — email architecture, services, 3x verify
Main/Voice/CLAUDE.md               — voice architecture (future)
Main/Platform/CLAUDE.md            — shared infra (future)
```

---

## Key Patterns from Top Repos

### From everything-claude-code (109k stars)
- **Verification loop** (6-phase): build → types → lint → tests → security → diff
- **Code-reviewer agent**: security + quality + performance checks
- **TDD-guide agent**: RED → GREEN → REFACTOR enforcement
- **Strategic compact**: compact at logical boundaries, not token thresholds
- **Memory persistence hooks**: save decisions before compaction, reload on start

### From awesome-claude-code (32.5k stars)
- **GSD (get-shit-done)**: spec-driven development, fresh context per phase
- **context-engineering-kit**: advanced context patterns, reflexion/memory
- **TypeScript Quality Hooks**: auto-format + type-check after edits
- **Claude Squad**: multiple agents in workspaces (for Stage 3)

### From web research
- **Document & Clear pattern**: dump progress to .md, /clear, resume fresh
- **Writer/Reviewer pattern**: implement in Session A, review in Session B
- **CLAUDE.md instruction budget**: ~150-200 instructions max before compliance drops
- **Parallel sessions**: `claude -p` for batch processing (useful for 20k leads)

---

## Number Five Specific Workflow

### 12-Step Process
```
UNDERSTAND (3x verify):
1. Read CLAUDE.md + CROSS_DEPENDENCIES.md
2. Read baseline_n8n/ JSON section
3. Read extracted JS from Archived/N8N/migration/extracted-code/
4. List all nodes, edges, logic branches
5. Check cross-dependencies
6. Confirm nothing missing

BUILD:
7. Write tests FIRST (TDD)
8. Implement
9. Run ALL tests
10. Walk through 8 cross-dependency checks
11. Update CHANGELOGS.md + ERROR_LOG.md
12. Commit and push
```

### After Each Major Phase
- Run `/codex-review` (sends to GPT-5.3-Codex)
- Tag milestone (e.g., `v1-phase1.1-rubric`)
- Update docs

### 8 Cross-Dependencies (must verify after EVERY change)
1. Counter sync (outbound_count, llm_out_count, last_llm_reply_at)
2. Two-phase rubric update (pre-send → send → post-send)
3. Opt-out propagation (5 places)
4. Gmail normalization (4 places)
5. Email domain fixer (3 places)
6. Bilingual templates (6 messages, EN+ZH)
7. Score never decreases (Math.max)
8. Qualification threshold (>= 67)

---

## Files Created/Modified

### In Number-Five repo:
- `Documentations/WORKFLOW_GUIDE.md` — complete workflow guide
- `Documentations/TOOLS_SETUP.md` — tools setup instructions
- `Documentations/REFERENCE_REPOS.md` — index of all reference repos
- `.claude/commands/codex-review.md` — Codex review command adapted for milestones
- `Main/Email/docs/ERROR_LOG.md` — error tracking template
- `Main/Voice/docs/ERROR_LOG.md` — error tracking template
- `Main/Platform/docs/ERROR_LOG.md` — error tracking template

### In global settings:
- `~/.claude/settings.json` — updated OneDrive path

---

## Future Enhancements (Add When Needed)

| Tool | When | Install |
|------|------|---------|
| PostgreSQL MCP | Before Phase 1.3 (inbound email) | `npx @anthropic-ai/mcp-server-postgres` |
| TypeScript Quality Hooks | When first .ts files exist | PostToolUse hook in settings.json |
| gcloud MCP | Before Cloud Run deployment | `googleapis/gcloud-mcp` |
| GSD | Phase 2+ | `npx get-shit-done-cc@latest` |
| Pre-commit test hook | When test suite exists | PreToolUse hook on `git commit` |
