# SESSION STATE — sagemaker-coding-agent

## Last Session: 2026-04-13 — V4.8.0 Release + PS_Deep E-Book

### V4.8.0 Changes (sagemaker_agent.py)
- All 8 skills: auto_trigger disabled. Skills only activate via /command or explicit request.
  - verify, simplify, review, security-review, batch, coding-standards, clara: auto_trigger: false
  - report: keeps keyword triggers ("create a report") since that's explicit intent
- /done and /verify are no longer auto-forced. Agent suggests them after 3+ file edits, user decides.
- SkillManager: new auto_trigger: false frontmatter support to disable keyword auto-discovery
- [CRITICAL] Chat window resizable (500px default, drag + slider 200-1200px)
- [CRITICAL] Prefer chat answers over file generation (system prompt + per-turn reminder)
- [CRITICAL] CSV/Excel data validation accuracy (system prompt section)
- Security: wget/bash restrictions relaxed (pipe-to-shell still blocked)
- Budget: display-only metric, never stops execution, editable text input
- Harness: post-compact FILE_CACHE.clear_context()
- Harness: per-turn critical reminder injection (system-reminder tags)
- Harness: enhanced cache breakage warning with cost impact
- Version: 4.3.1 → 4.8.0

### PS_Deep E-Book (new)
- PS_ClaudeCode_Insights/PS_Deep/PS_DEEP_DIVE_RUNNABLE.html — 10-chapter standalone e-book
- 8 research docs covering all 2,010 files of Runnable codebase
- Gap analysis: V4 vs Runnable (97% equivalent, 6 actionable gaps → now 3 remain)

### Updated HTMLs
- PS_FLOWCHART_RUNNABLE.html — stats corrected, sub-agent section expanded
- PS_FLOWCHART_V4.html — agent comparison table added

### Hermes vs Coding Agent HTML (new)
- PS_ClaudeCode_Insights/HERMES_VS_CODING_AGENT.html — 7-tab comparison (self-improving vs coding loop)
- Screenshots added to PS_ClaudeCode_Insights/screenshots/

### chat.ipynb cleanup
- Removed coding-standards SKILL.md (merged into main skills)
- Updated chat.ipynb markdown

### Pre-commit hook added
- .git/hooks/pre-commit — rejects files with invalid Unicode (unpaired surrogates)
- Prevents API Error 400 "invalid high surrogate in string"

### To Resume
- V4.8.0 needs AWS Bedrock testing before final ship
- Remaining gaps: auto-nudge on 3+ tasks, multi-agent FP filtering, fork cache sharing (blocked on Bedrock)
- Rebuild compact_v4.zip and PDF/wins_docs.zip after all changes
- Consider adding chat_height_slider to the layout row in chat.ipynb as well
