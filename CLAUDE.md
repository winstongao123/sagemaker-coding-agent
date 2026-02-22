# SageMaker Coding Agent

## Overview
AI coding agent that runs in SageMaker/Jupyter notebooks. Generates Power BI dashboards from CSV data using LLMs. Multiple versions from simple to production-grade.

## Versions

| Version | Path | Description |
|---------|------|-------------|
| **V3 (current)** | `compact_v3/MAIN/agent/` | Review agent, /verify, /checkpoint, 5 skills, v3.1.0 |
| V2 | `compact_v2/MAIN/agent/` | External config, cost tracking, error recovery |
| V1 | `compact/` | Single-file AWS Bedrock (chat.ipynb + sagemaker_agent.py) |
| GCP | `compact_GCP/` | Single-file GCP Vertex AI (chat.ipynb + gemini_agent.py) |
| Complete | `complete/` | Modular multi-file (core/, tools/, config.py, agent.ipynb) |

## V3 Structure (`compact_v3/MAIN/agent/`)
```
sagemaker_agent.py      # Core agent (v3.1.0) - source of truth
chat.ipynb              # Jupyter notebook entry point
chat.md                 # Companion doc (copy of .py)
sagemaker_agent.md      # Companion doc (copy of .py)
USER_GUIDE.md           # User guide
skills/
├── coding-standards/   # Code style enforcement
├── review/             # Code review agent
├── verify/             # Verification skill
├── powerbi-dashboard/  # V1 dashboard generator (sales/business only)
└── powerbi-dashboard-v2/  # V2 dashboard generator (any domain)
```

## Key Rules
- **Source of truth**: `.py` and `.ipynb` files, NOT companion `.md` files
- **After code changes**: update `.md` companion (copy .py to .md), update CHANGELOG, push
- **Version**: Always increment `__version__` in `sagemaker_agent.py` on feature changes
- **Skills sync**: `compact_v3/MAIN/agent/skills/` is the canonical source for Power BI skills. Sync to `D:\Github\AIPower\skill/` and `skill-v2/`.

## Git
- **Push to**: `sageagent` remote (`https://github.com/winstonpgao/sageagent.git`)
- **Do NOT push to**: `origin` (permission denied for winstonpgao)

## Tests
- `compact_v3/MAIN/tests/` - 6 Power BI test dashboards (enrollment, csv, healthcare, hr, logistics, marketing)
