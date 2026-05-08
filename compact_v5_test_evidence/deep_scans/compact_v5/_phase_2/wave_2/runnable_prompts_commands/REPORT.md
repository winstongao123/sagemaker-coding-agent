# Wave 2 — Runnable prompts.ts (914 LOC) + commands/ + hooks/ vs v5

## Prompts alignment (Runnable prompts.ts vs v5's 19 .md files)

| Runnable section | Lines | v5 equivalent | Alignment | Loss |
|---|---|---|---|---|
| getSimpleIntroSection | 175-183 | identity.md | PARAPHRASED_OK | None |
| getSimpleSystemSection | 186-196 | system.md | **PARAPHRASED_LOSING_INFO** | Hooks integration + injection-flag guidance MISSING |
| Hooks guidance | 128 | — | **MISSING** | Zero hooks infrastructure in v5 |
| getSimpleDoingTasksSection | 199-252 | doing_tasks.md | PARAPHRASED_OK | ANT-only comment minimalism rules lost |
| Code style guidance | 200-209 | doing_tasks.md | **PARAPHRASED_LOSING_INFO** | "Comment WHY not WHAT", preserve-existing rules lost |
| getActionsSection | 255-266 | executing_actions.md | PARAPHRASED_OK | Aligned |
| getUsingYourToolsSection | 269-313 | tool_efficiency.md | PARAPHRASED_OK | Solid |
| getAgentToolSection | 316-319 | subagent_coord.md | **PARAPHRASED_LOSING_INFO** | Fork/background rationale lost |
| getDiscoverSkillsGuidance | 333-340 | skill_patching.md | PARAPHRASED_OK | Aligned |
| getOutputEfficiencySection | 402-427 | answer_preference.md | **PARAPHRASED_LOSING_INFO** | "Write for humans", inverted pyramid lost |
| getSessionSpecificGuidance | 352-399 | — | **PARTIAL** | Exploration/verification agent guidance MISSING |
| Verification contract | 390-394 | verification_contract.md | **PARAPHRASED_LOSING_INFO** | Formal independent adversarial flow lost |
| Proactive/Brief | 843-914 | — | **MISSING** | Tick-loop, sleep pacing, first-wake greeting MISSING entirely |
| Language support | 142-148 | — | **MISSING** | No language config |
| Scratchpad | 796-818 | — | **MISSING** | No session-scoped temp dir |
| Model override | 136-139 | — | **MISSING** | ANT-only config absent |
| MCP instructions | 160-604 | mcp.md | PARAPHRASED_OK | Connection filtering differs |

**Result: 8 major sections entirely MISSING; 5 sections paraphrased-with-info-loss.**

## Commands (120+ slash commands)

**v5 status: ALL MISSING.** v5 has zero slash-command infrastructure.

Sample lost: `/help`, `/fast`, `/commit`, `/plan`, `/cost`, `/issue`, `/branch`, `/clear`, `/compact`, `/fork`, `/agent`, `/brief`, `/model`, `/config`, `/permissions`, `/memory`, `/context`, `/mcp`, `/skills`.

Impact: All in-session interaction flows gone; v5 relies entirely on prompt guidance, no in-session affordances.

## Hooks (60+ event triggers)

**v5 status: ALL MISSING.** Zero event-driven automation.

Runnable hooks: user-prompt-submit-hook (pre-send validation), tool-call-blocked-hook (permission denial), tool execution phases (pre/post), session lifecycle (start/end), settings change (file update), task completion, auto-mode unavailable notification, shell execution hooks.

Adoption verdict: NICE-TO-HAVE for v5.0.1 (not ship-blocker). Adds complexity; subset like user-prompt-submit-hook + tool-call-blocked-hook may be worth it.

## Semantic drift catalogue (HIGH/MEDIUM)

### HIGH-SEVERITY losses

1. **Hooks as feedback source** (line 128 → MISSING): v5 cannot execute hooks.
2. **Code comment rules** (lines 200-209 → doing_tasks.md): "Comment WHY not WHAT", "preserve existing", "no task refs" — v5 generalizes away.
3. **Output communication nuance** (lines 402-427 → answer_preference.md): "Write for a person, avoid fragments/notation, semantic backtracking, inverted pyramid" — v5 collapses to "prefer chat over files".
4. **Subagent type ecosystem** (lines 316-319 + 352-399): Fork/background execution model, Explore/Verify agents — v5's `task` tool underspecified.
5. **Verification contract** (lines 390-394): Independent adversarial gate; FAIL→fix→resume→PASS→spot-check — v5 has zero verification narrative.
6. **Proactive/autonomous mode** (lines 843-914): Tick-loop, sleep pacing, first-wake greeting, responsiveness bias — ENTIRE architecture missing.

### MEDIUM-SEVERITY

7. Scratchpad directory (MISSING)
8. Language support (MISSING)
9. Model-aware knowledge cutoff (MISSING)
10. Model override config (MISSING)
11. Prompt-injection flagging (system.md loss)

## Final tally

- **Prompts**: 15/23 v5 files mapped. 8 sections entirely absent. 5 paraphrased-losing-info.
- **Commands**: 120+ Runnable → 0 in v5. Complete layer erasure.
- **Hooks**: 60+ event points → 0 in v5. Complete layer erasure.
- **Behavioral drift**: 6 high-severity + 5 medium-severity losses.

v5 traded richness for simplicity: prompt-only, no CLI/event layer. Leaner but lossy on behavioral guidance.
