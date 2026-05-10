1. files changed: compact_v5/compact_v5/ui/chat_ui.py
2. intended scope: live notebook output routing during agent.run(), preserving per-turn metadata
3. engine touched? no
4. prompt/security/Bedrock touched? no
5. regression risk: low-to-medium; UI thread now re-renders during callbacks, no request/tool semantics changed
