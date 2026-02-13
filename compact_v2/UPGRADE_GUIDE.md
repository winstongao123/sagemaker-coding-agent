# Compact V2 Upgrade Guide

What changed from `compact/` to `compact_v2/`, and how to test each feature.

---

## Feature Comparison: compact/ vs compact_v2/

### New Features (13)

| # | Feature | compact/ | compact_v2/ | Where in Code |
|---|---------|----------|-------------|---------------|
| 1 | **External Config** | Hardcoded Python dataclass | JSONC file (`opencode.json`) with merge | `_load_config_file()`, `_strip_jsonc_comments()`, `_apply_config_file()` |
| 2 | **Skills System** | Flat `*.md` in `./skills/`, first-line summary | YAML frontmatter, `**/SKILL.md` recursive glob, system prompt injection | `SkillManager` class |
| 3 | **Custom Commands** | None | Template-based slash commands from config (`$ARGUMENTS`, `$1`, `$2`) | `CommandRegistry` class |
| 4 | **Sub-Agent Types** | Single `subagent_run` with fixed tools | 4 typed agents (build/plan/explore/general) + custom via config | `AGENT_TYPES` dict, `_run_task_tool()` |
| 5 | **MCP Stdio Client** | None | Spawn local MCP servers, JSON-RPC over stdin/stdout, tool discovery | `McpStdioClient` class |
| 6 | **MCP HTTP Client** | Basic HTTP bridge to single endpoint | Full JSON-RPC with error handling, 2MB limit, custom headers | `McpHttpClient` class |
| 7 | **MCP Manager** | None | Multi-server management, dynamic tool registration, status tracking | `McpManager` class |
| 8 | **Diff Tracking** | None | Unified diff on every write/edit, stored in `_RECENT_DIFFS` | `_generate_unified_diff()` |
| 9 | **Permission Rules** | Hardcoded `HIGH_RISK_TOOLS` set | Config-based per-tool + file-pattern rules with fnmatch + command wildcards | `permission_rules` in config, `request_approval()` |
| 10 | **WebFetch Tool** | None | URL fetch with HTML-to-markdown, SSRF protection, 2MB limit | `tool_web_fetch()`, `_is_private_ip()` |
| 11 | **Cost Tracking** | Token counter only | Per-model pricing (8 Bedrock models), `/cost` command, status bar | `_MODEL_PRICING`, `TokenTracker.get_cost()` |
| 12 | **Snapshot/Revert** | None | Auto-backup before edits, `/revert` command, max 100 snapshots | `SnapshotManager` class |
| 13 | **Ask User Tool** | None | LLM asks user questions mid-conversation, free-text + multiple-choice | `tool_ask_user()`, `_run_ask_user_tool()` |

### Upgraded Features (3)

| # | Feature | compact/ | compact_v2/ | What Changed |
|---|---------|----------|-------------|--------------|
| 1 | **Config Validation** | No validation | Typed `_SCALAR_FIELDS` with range checks (temperature 0-1, thinking_budget 1024-64000) | `_apply_config_file()` |
| 2 | **SSRF Hardening** | None | `_is_private_ip()` blocks private/link-local/metadata IPs, redirect blocking | `_NoRedirectHandler`, `_WEB_FETCH_MAX_BYTES` |
| 3 | **SageMaker Approval** | Blocks on stdin (deadlock in kernel) | Auto-approve with informative message when SageMaker detected | `request_approval()` |

---

## How to Test Each Feature

### 1. External Config (`opencode.json`)

Create or edit `opencode.json` in your workspace root:
```json
{
  // This is a JSONC comment — should be stripped
  "max_turns": 5,
  "temperature": 0.5
}
```
**Verify**: Run the agent. Check that `CONFIG.max_turns` is 5 and `CONFIG.temperature` is 0.5. Invalid values (e.g., `"temperature": 2.0`) should be rejected with a warning.

### 2. Skills System

Create a skill file:
```
mkdir -p skills/myskill
```
Write `skills/myskill/SKILL.md`:
```markdown
---
name: my-skill
description: A test skill
---
## My Skill Instructions
Do something useful.
```
**Verify**: In chat, the LLM can call the `skill` tool with `{"action": "list"}` to see your skill, or `{"action": "read", "name": "my-skill"}` to load it. The existing `skills/review/SKILL.md` is a working example.

### 3. Custom Slash Commands

Add to `opencode.json`:
```json
{
  "commands": {
    "review": {
      "template": "Review this code:\n$ARGUMENTS",
      "description": "Code review",
      "agent": "plan"
    }
  }
}
```
**Verify**: Type `/commands` in chat to list them. Type `/review sagemaker_agent.py` — it should expand the template and send it as a message. If `"agent": "plan"` is set, it routes through the plan sub-agent.

### 4. Sub-Agent Types

The LLM can call the `task` tool with different agent types:
```json
{"prompt": "Find all TODO comments", "subagent_type": "explore", "description": "Find TODOs"}
```
**Verify**:
- `explore` agent only has read tools (read_file, glob, grep, list_dir, semantic_search)
- `plan` agent has read tools + todo tools, uses PLAN_MODE_PROMPT
- `build` agent has all tools
- `general` agent has read + write tools
- Check that Plan Mode ON forces all command-dispatched agents to `plan` type

### 5. MCP Stdio Client

Add to `opencode.json`:
```json
{
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["python", "my_mcp_server.py"],
      "env": {},
      "timeout": 30
    }
  }
}
```
**Verify**: On startup, the agent spawns the process, performs MCP handshake, discovers tools. Tools appear as `mcp_my-server_<toolname>` in the tool list. Status bar shows "MCP: 1 connected".

### 6. MCP HTTP Client

```json
{
  "mcp": {
    "remote": {
      "type": "remote",
      "url": "https://my-mcp-server.example.com/rpc",
      "headers": {"Authorization": "Bearer ..."},
      "timeout": 30
    }
  }
}
```
**Verify**: Same as stdio — tools are discovered and registered dynamically.

### 7. MCP Manager

**Verify**: With multiple MCP servers configured (mix of local/remote, some with `"enabled": false`):
- Disabled servers show as "disabled" in status
- Failed servers show as "failed" with error logged
- Connected servers' tools are all available
- `/commands` or status bar shows connection summary

### 8. Diff Tracking

**Verify**: Ask the LLM to edit or write a file. The tool response now includes a unified diff showing exactly what changed:
```
--- a/myfile.py
+++ b/myfile.py
@@ -1,3 +1,4 @@
 line1
+new line
 line2
 line3
```
Diffs are stored in `_RECENT_DIFFS` for the session.

### 9. Permission Rules

Add to `opencode.json`:
```json
{
  "permissions": {
    "bash": "ask",
    "read_file": "allow",
    "*.env": "deny",
    "bash:rm*": "deny"
  }
}
```
**Verify**:
- `read_file` calls proceed without approval prompt
- `bash` calls trigger approval prompt
- Reading `*.env` files is denied
- `bash` commands starting with `rm` are denied (wildcard pattern)

### 10. WebFetch Tool

The LLM can call:
```json
{"url": "https://example.com", "prompt": "Summarize this page"}
```
**Verify**:
- Public URLs return markdown-converted content
- Private IPs (127.0.0.1, 10.x.x.x, 169.254.169.254) are blocked
- Responses larger than 2MB are truncated
- Redirects to private IPs are blocked

### 11. Cost Tracking

**Verify**: After a few exchanges:
- Type `/cost` in chat — shows token breakdown by model with dollar amounts
- Status bar displays running session cost
- Different models (Haiku vs Sonnet vs Opus) have different per-token rates

### 12. Snapshot/Revert

**Verify**:
1. Ask the LLM to edit a file
2. Check `.snapshots/` directory — a backup should exist with timestamp
3. Type `/revert <filepath>` — file reverts to pre-edit state
4. Type `/revert all` — all modified files revert
5. Max 100 snapshots, oldest pruned automatically

### 13. Ask User Tool

**Verify**: Give the LLM an ambiguous task (e.g., "refactor this code"). It should call `ask_user` with a question and optional choices. A Jupyter widget appears for you to respond. Works in Plan Mode too.

### 14. Config Validation (upgraded)

**Verify**: Set invalid values in `opencode.json`:
```json
{"temperature": 2.0, "max_turns": -5, "thinking_budget": 500}
```
- `temperature: 2.0` — rejected (must be 0-1)
- `max_turns: -5` — rejected (must be positive)
- `thinking_budget: 500` — rejected (must be 1024-64000)
- Warnings logged, defaults used instead

### 15. SSRF Hardening (upgraded)

**Verify**: The `web_fetch` tool blocks:
- `http://127.0.0.1` — localhost
- `http://10.0.0.1` — private range
- `http://169.254.169.254` — AWS metadata
- `http://[fd00::1]` — IPv6 ULA
- `http://[fe80::1]` — IPv6 link-local
- Redirects to any of the above

### 16. SageMaker Approval (upgraded)

**Verify**: In a SageMaker kernel, high-risk tool calls (bash, python_exec) auto-approve instead of blocking. An informative message appears: "Auto-approved in SageMaker environment". Toggle approval ON/OFF with the approval widget.

---

## Test Suite

Run all 84 tests:
```bash
cd compact_v2
pytest tests/ -v
```

Test files:
- `tests/test_security_manager.py` — bash/Python security layers
- `tests/test_security_integration.py` — combined security scenarios
- `tests/test_operational_controls.py` — rate limiting, sessions, compaction
- `tests/test_v2_features.py` — all 59 v2-specific tests (config, skills, commands, agents, MCP, diffs, permissions, cost, snapshots, SSRF, ask_user)

---

## Quick Start

1. Copy `compact_v2/` to your SageMaker workspace
2. Optionally create `opencode.json` for custom config
3. Optionally add skills in `skills/*/SKILL.md`
4. Open `chat.ipynb` and run all cells
5. Start chatting — all features are active by default
