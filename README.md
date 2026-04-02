# SageMaker Coding Agent — V4.3.2

AI coding agent for AWS SageMaker notebooks. 25+ tools, 16 security layers, 6 sub-agent types, prompt caching. Built by studying Claude Code (Runnable) source code.

## Ship to Company
```
compact_v4/compact_v4.zip    # 60 files, 3.1MB — upload to Teams
```

## Learn the Architecture
```
PS_ClaudeCode_Insights/Web_doc/PS_FLOWCHART_RUNNABLE.html   # Runnable Claude Code
PS_ClaudeCode_Insights/Web_doc/PS_FLOWCHART_V4.html         # V4 agent
```
Open both side by side. Tab 3 (Cross-Compare) shows harness engineering comparison.

## Version History
| Version | Date | Key Changes |
|---------|------|-------------|
| **V4.3.2** | 2026-04-02 | Cache-breakage detection, verify agent, WHEN tool descriptions, OpenClaw comparison |
| V4.3.1 | 2026-04-01 | Prompt engineering upgrade from Runnable (6 system sections, 7 tool descriptions) |
| V4.3.0 | 2026-04-01 | Diminishing returns, memory caps, cache indicator |
| V4.2.x | 2026-04-01 | Token optimization (FILE_UNCHANGED_STUB, parallel RO, PTL retry) |
| V4.1.0 | 2026-04-01 | Cache boundary, catastrophic blocks, 4-type memory |
| V3 | 2026-03 | Previous version (in `_archive/compact_v3/`) |
| V2 | 2026-02 | Earlier version (in `_archive/compact_v2/`) |
| V1 | 2026-01 | Prototype (in `_archive/compact/`) |

See `compact_v4/CHANGELOG.md` for full details.
