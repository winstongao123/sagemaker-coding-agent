1. files changed: compact_v5/compact_v5/ui/chat_ui.py; compact_v5/compact_v5/core/query_engine.py
2. intended scope: v4-style live tool/thinking/system cards and read-only tool callback event wiring
3. engine touched? yes, callback notification only after tool execution/error
4. prompt/security/Bedrock touched? no request shape, prompt, security gate, or returned tool_result content changed
5. regression risk: medium; callback side effects are best-effort UI only, but tool dispatch path now invokes the existing callback for result visibility
