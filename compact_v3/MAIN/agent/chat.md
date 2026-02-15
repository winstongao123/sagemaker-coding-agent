# chat.ipynb - Compact Guide

## Cells
- Cell 0 (markdown): Overview, version history (V1/V2/V3), link to USER_GUIDE.md
- Cell 1 (code): `pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl`
- Cell 2 (code): Configuration widgets (model, temp, thinking, workspace, max turns, mock)
- Cell 3 (code): Apply widget config to `CONFIG`, launch agent with `create_chat_ui()`
- Cell 4 (markdown): Reference docs (token display, tools, sub-agents, commands, skills, security, cost)

## Quick Start
1. Run Cell 1 (install deps -- once)
2. Run Cell 2 (configure settings via widgets)
3. Run Cell 3 (start chatting)

## Key Settings (Cell 2 Widgets)
- **Model**: dropdown, default Claude 3 Haiku (8 models: Haiku/Sonnet/Opus across 3/3.5/4.5/4.6)
- **Temperature**: 0.0 (deterministic) to 1.0 (max creativity), default 0.0
- **Extended Thinking**: checkbox, default Off (slower, better reasoning)
- **Thinking Budget**: 1024-16000 tokens, default 4096
- **Max Turns**: slider 5-100, default 60
- **Workspace**: text input, default `.` (current directory)
- **Mock Mode**: checkbox, default Off (test UI without API)
- **Region**: hardcoded Sydney (ap-southeast-2)

Models are imported from `sagemaker_agent.BEDROCK_MODELS` (single source of truth).

## What Cell 4 Documents
- **Token Display & Cost Monitor**: API totals, cost, context window %, true context (~3,350 overhead/call)
- **Tools** (22): file ops, bash/python exec, docs/charts/pdf, vision, semantic search, todos, web, skills, sub-agents, ask_user
- **Sub-agents** (5): build, plan, explore, general, review
- **Skills** (5): review, verify, coding-standards, powerbi-dashboard (V1), powerbi-dashboard-v2
- **Commands** (12): /skills, /skill use|clear, /commands, /cost, /revert, /compact, /save, /verify, /checkpoint
- **Security** (8 layers): 3-layer bash, 3-layer Python, SSRF, workspace boundary, write guard, permissions, audit, approval
- **Error Recovery** (5): tool name repair, arg auto-fix, type conversion, fuzzy suggest, malformed JSON recovery
- **Cost Tracking**: Bedrock pricing table (8 models, AU 10% premium for Claude 4.5+)
