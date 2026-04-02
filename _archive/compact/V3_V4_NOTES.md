# V3 to V4 Notes

## V3 Baseline (Stable)

V3 is the hardened single-agent SageMaker coding app with:
- Bedrock model switching with live connectivity checks
- Local execution default (`execution_mode=local`)
- Optional auth and optional approval gate
- Context compaction (prune + summarize)
- Session persistence + audit logs
- Security controls for path/command/python execution

This baseline remains the default behavior in `sagemaker_agent.py`.

## V4 Additions

V4 adds extensibility similar to OpenCode/Claude workflows:

1. Skills
- Local skill directory support (`CONFIG.skills_dir`, default `./skills`)
- New tools: `skill_list`, `skill_read`
- New UI commands:
  - `/skills`
  - `/skill use <name>`
  - `/skill clear`
- Active skills are appended to runtime system prompt
- Active skills persist in session metadata

2. Sub-agent delegation
- New tool: `subagent_run`
- Bounded by `CONFIG.subagent_max_depth`
- Restricted tool allowlist per delegated run
- Delegated run output is summarized and returned to parent agent

3. MCP-ready bridge (off by default)
- New tool: `mcp_call`
- Controlled by config:
  - `enable_mcp`
  - `mcp_endpoint`
  - `mcp_allowed_methods`
  - `mcp_timeout_seconds`
- JSON-RPC HTTP bridge with method allowlist

## Security Notes for V4

- `mcp_call` and `subagent_run` are approval-gated and marked high risk.
- Plan Mode blocks `mcp_call` and `subagent_run`.
- Sub-agent depth and tool allowlist prevent uncontrolled recursion.
- Skills are local `.md` files only; no remote fetch.

## Recommended Next V4 Steps

- Add dedicated tests for `/skill` command flow in notebook UI.
- Add explicit MCP response schema validation if endpoint contract is fixed.
- Add per-subagent execution budget accounting if needed for strict governance.
