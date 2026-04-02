# PS_[05] OpenClaw vs V4 Comparison

> **What is OpenClaw?** Open-source reimplementation of Claude Code (Runnable). Repo: `github.com/ultraworkers/claw-code` (cloned as `openclaw/`)
> **Claim**: "Best cover of Runnable"
> **Verdict**: OpenClaw is a FULL reimplementation (not just analysis). It has some novel patterns but V4 already covers the core agentic engineering.
> **Created**: 2026-04-02

---

## Feature Comparison

| Feature | OpenClaw | V4 (v4.3.2) | Gap for V4? |
|---------|----------|-------------|-------------|
| Agent Loop | ReAct via Pi runtime (3rd-party) | ReAct (own implementation) | NO — V4 owns the loop, more control |
| Context Compression | 3-tier + hooks-driven | 3-tier (70%/80%/90%) + circuit breaker | NO — equivalent |
| Sub-Agents | ACP thread-bound sessions | 6 types (explore/verify/plan/review/general/build) | NO — V4 has more types |
| Memory | Plugin-based (swappable backends) | 4-type hardcoded (USER/FEEDBACK/PROJECT/REFERENCE) | MINOR — V4 works fine, plugin architecture is over-engineering for single-file agent |
| Security | Tool-level gating + sandbox + approval | 16 layers (bash/python/AWS/path/catastrophic) | NO — V4 is MORE comprehensive |
| Prompt Caching | Bedrock wrapper + cache-ttl | Bedrock cache_control + cache-breakage detection | NO — V4 is equivalent or better |
| Tools | 25+ bundled + plugin-discoverable | 25+ with WHEN-not-WHAT descriptions | NO — equivalent |
| Hooks | Rich: bootstrap, pre/post-compaction, session events | Limited (on_compact_fn, on_approval) | **MAYBE** — see analysis below |
| Tool Groups | Declarative allow-lists with group refs | Per-agent-type tool sets | MINOR — similar concept, different implementation |

## What OpenClaw Does Better (Honest)

### 1. Hook-Driven Extensibility
OpenClaw has pluggable hooks for compaction (before/after), bootstrap, and session events. V4 has `on_compact_fn` (single callback) and `on_approval` but NOT a general hook system.

**Should V4 adopt?** PROBABLY NOT for now. V4 is a single-file agent for SageMaker. A hook system adds complexity that benefits multi-developer teams, not single-agent deployments. If V4 becomes a platform (multiple users customizing behavior), then yes.

### 2. Thread-Bound Session Isolation (ACP)
OpenClaw's ACP (Async Control Plane) creates thread-contextualized sub-agent sessions with cleaner isolation than V4's save/clear/restore pattern.

**Should V4 adopt?** NO. V4's context isolation works correctly. ACP is cleaner architecturally but adds dependency on an async runtime that doesn't exist in SageMaker Jupyter.

### 3. Plugin-First Memory
OpenClaw allows swapping memory backends (file, database, etc.) via plugins.

**Should V4 adopt?** NO. V4's file-based memory.md is the right choice for SageMaker. Plugin architecture is over-engineering for a single-file deployment.

## What V4 Does Better

1. **16 security layers** vs OpenClaw's tool-level gating
2. **6 explicit sub-agent types** with prescribed output formats vs OpenClaw's generic spawning
3. **WHEN-not-WHAT tool descriptions** — OpenClaw doesn't have this pattern
4. **Bedrock-specific optimizations** — cache-breakage detection, cold-cache microcompact, Haiku threshold awareness
5. **Verify agent** — adversarial testing sub-agent (OpenClaw doesn't have this)
6. **Cost-aware token tracking** with cache savings display

## Conclusion

**OpenClaw confirms V4 is on the right track.** The core patterns (ReAct loop, 3-tier compression, sub-agents, memory, caching) are the same. OpenClaw's novel contributions (hooks, ACP, plugins) are architectural elegance that benefit platform developers, NOT single-agent SageMaker deployments.

**Nothing in OpenClaw requires V4 changes.** V4 remains at maximum for its context.

---

*Analyzed: 2026-04-02. OpenClaw repo at D:\Github\openclaw\*
