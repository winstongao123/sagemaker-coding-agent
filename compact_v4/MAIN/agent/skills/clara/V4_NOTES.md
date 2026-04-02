# Clara Prompts — V4 Compatibility Notes

The Clara review prompts (00-05) were written for compact_v3. When running on V4, note these differences:

## Config Changes (V3 -> V4)

| V3 (prompts reference) | V4 equivalent |
|------------------------|---------------|
| `opencode.json` | `CONFIG` object in Cell 3 of chat.ipynb |
| `compact_v3` | `compact_v4` |
| `sagemaker_agent.py` v3.x | `sagemaker_agent.py` v4.3.1 |

## V4 Advantages for Clara Review

1. **Prompt caching**: Sonnet 4.5 caches system+tools after turn 1 (~90% savings on subsequent turns). Use Sonnet for long reviews.
2. **Structured sub-agent output**: V4.3.1 sub-agents return Scope/Result/Key files/Issues format — aligns with Clara's evidence-based output.
3. **Diminishing returns detection**: V4 warns if agent is stuck (3+ low-output turns). Useful during long Clara sessions.
4. **FILE_UNCHANGED_STUB**: Re-reading unchanged files saves tokens — helpful when Clara reads the same file multiple times across phases.
5. **Memory cap**: 200-line cap prevents memory bloat across Clara sessions.

## Tool Names (unchanged)

V4 uses identical tool names to V3: `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `bash`, `python_exec`, `task`, `view_image`, `semantic_search`, `web_fetch`, `skill`, `ask_user`, `todo_write`, `todo_read`.

`write_file` still supports `mode: "append"` — critical for Clara's incremental output strategy.

## Sub-Agent Types (unchanged)

V4 has same types: `explore`, `plan`, `review`, `build`, `general`. Turn limits configurable via CONFIG.

## Agent Config for Clara (V4)

In Cell 3 of chat.ipynb, add before `create_chat_ui()`:

```python
# Clara review config
CONFIG.model_id = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"  # Sonnet for main
CONFIG.session_cost_limit = 10.0  # Higher limit for 5-phase review (~$6 estimated)
CONFIG.max_turns = 80  # Allow longer sessions
```

Sub-agent model overrides are not yet per-type in V4. All sub-agents use the main model. To use Haiku for explore sub-agents, the user would need to manually switch CONFIG.model_id between phases.

## Blocker Bugs — All Fixed

All 4 blockers from AGENT_BUGS.md are fixed in V4:
- B1: write_file FileCache (fixed)
- B2: Sub-agent cache isolation (fixed)
- B3: Sub-agent max-turns output (fixed)
- B4: grep cap warning (fixed)

## Recommended Workflow

The prompt files are included in the zip — no separate copying needed.

1. Unzip `compact_v4.zip` on SageMaker
2. Load skill: `/skill use clara-full-review`
3. Set workspace to ClaRA codebase root
4. Copy prompt files into workspace:
   ```bash
   cp MAIN/agent/skills/clara/prompts/00_CONTEXT.md <clara_root>/
   ```
5. Start: "Start the ClaRA review" (or select specific components)
6. For each phase, agent will use FULL_REVIEW.md as orchestration guide
7. Paste the phase-specific prompt (01-05) when agent asks for phase details

## Prompts Included in This Package

The `skills/clara/prompts/` folder contains the full review prompt suite:

| File | Phase | What it covers |
|------|-------|---------------|
| `00_CONTEXT.md` | All | ClaRA context, evidence rules, R/A/G thresholds, PII patterns |
| `01_DISCOVERY.md` | Phase 1 | File tree, dependencies, AWS inventory, code metrics |
| `02_COMPONENT1.md` | Phase 2 | Bug validation, CHECK_REGISTRY, extraction code |
| `03_COMPONENT2_3.md` | Phase 3 | Agent definitions, orchestration, SQL, UI |
| `04_PROD_READINESS.md` | Phase 4 | R/A/G scorecard, cost projections, FTE impact |
| `05_SYNTHESIS.md` | Phase 5 | Final report + business case |
| `HOW_TO_USE.md` | Setup | Pre-flight, model config, cost estimates, failure recovery |

Source of truth: `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\`
Git backup: `github.com/winstonpgao/planning_bot` (main branch)
