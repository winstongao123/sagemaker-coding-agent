1. files changed: compact_v5/compact_v5/ui/chat_ui.py; compact_v5/compact_v5/tools/task.py
2. intended scope: visible subagent lifecycle, child output, final envelope/cost/cache/artifact rendering
3. engine touched? no
4. prompt/security/Bedrock touched? no request shape, prompt, security, compaction, or receipt persistence semantics changed
5. regression risk: medium-low; task tool now forwards child output to parent UI callback but still returns the same envelope/result to the model
