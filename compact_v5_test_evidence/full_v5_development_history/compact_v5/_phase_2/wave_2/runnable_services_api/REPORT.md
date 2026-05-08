# Phase 2 Wave 2: Runnable API Services Line-by-Line Investigation

## Executive Summary

Runnable error handling (1207 LOC), retry logic (823 LOC), and cache-break detection (728 LOC) are substantially more sophisticated than v5 baseline. Runnable tracks 50+ error categories vs v5 8. Retry features 529-gating, persistent unattended mode, fast-mode fallback, max-tokens adjustment. Cache-break detection uses per-tool hashing, beta tracking, effort/overage latching. Most MISSING from v5 but architecturally clean.

## 1. ERROR CATEGORIZATION (errors.ts L1-1207)

### Missing Error Types (18 new)

| Type | Runnable | v5 Status | Adoption |
|---|---|---|---|
| API Timeout | 433-443 | MISSING | Add timeout predicate |
| Image Size (pre-call) | 448-452 | MISSING | Add pre-validation |
| Prompt Too Long + Token Parse | 560-574 | PARTIAL | Add parser |
| PDF Page Limit | 576-586 | MISSING | Add regex |
| Tool Use Concurrency | 666-706 | MISSING | Add + log Statsig |
| Invalid Model (Subscription) | 735-770 | MISSING | Add subscription gate |
| Disabled Org + Env-Var | 785-811 | MISSING | Add source tracking |
| OAuth Revoked | 838-848 | MISSING | Add (403) |
| CCR Mode Auth | 813-836 | MISSING | Add isCCRMode() |

Runnable 50+ branches vs v5 8. Extra 40 are media validation, tool diagnostics, subscription-aware, auth source tracking.

## 2. RETRY STRATEGY (withRetry.ts L1-823)

### Backoff Parameters

| Parameter | Runnable | v5 | Notes |
|---|---|---|---|
| MAX_RETRIES | 10 | 4 | 11 vs 5 total attempts |
| BASE_DELAY_MS | 500 | 1000 | Faster initial |
| Jitter | ±12.5% | ±15% | Symmetric vs bidirectional |
| Persistent Max | 5min | N/A | Unattended only |

### Specialized Paths NOT in v5

A. Foreground 529 Gating (L84-89): Background bail immediately (avoid cascade).
B. Fast Mode Fallback (L284-305): Short delay keeps cache; long triggers cooldown.
C. Opus 529 Fallback (L326-365): Switch model after 3 consecutive 529s.
D. Persistent Unattended (L96-104, L433-512): Chunked sleeps with heartbeats.
E. Max Tokens Overflow (L384-427): Adjust output limit.

## 3. CACHE-BREAK DETECTION (promptCacheBreakDetection.ts L1-728)

### Phase 1: recordPromptState (pre-call)

Tracks per-source:
- System hash (stripped + with cache_control)
- Per-tool schema hashes (77% of breaks are description-only)
- Tool names (sanitized: MCP to "mcp")
- Model, fast mode, global cache strategy, betas, auto mode, overage, cached MC, effort, extra body

### Phase 2: checkResponseForCacheBreak (post-call)

Detects break if cache read dropped >5% AND absolute drop >2000 tokens.
Attributes to 12 client-side causes + TTL expiry heuristics (1h vs 5m vs server-side).
Logs sanitized tool names to Statsig.

### Key Innovations NOT in v5

1. Per-Tool Hashing: Pinpoints which tool changed (77% of tool breaks).
2. Cache Control Hash: Catches scope/TTL flips.
3. Beta Header Tracking: Sorted list diffed.
4. MCP Tool Sanitization: Avoid leaking paths.
5. Overage State Latching: Expect no flips (TTL stable).
6. Auto Mode Sticky-On: Latch header once per session.
7. Effort Value: Resolved effort in request.
8. Extra Body Params: Hash of CLAUDE_CODE_EXTRA_BODY.
9. TTL Expiry Heuristics: Attribution to 1h/5m or server-side.

## 4. ADOPTION PRIORITIES

### ASAP (Low Effort)
- Error: Token count parser for prompt-too-long
- Error: Media size (PDF, image, request 413)
- Error: Tool use diagnostics (concurrency, duplicate IDs)
- Retry: Retry-After header parsing + conversion
- Retry: Rate-limit reset delay calculation
- Cache-Break: Per-tool schema hashing
- Cache-Break: Beta header tracking

### Next (Medium)
- Error: Auth source tracking (env-var vs OAuth vs external)
- Error: CCR mode 401/403 transient
- Retry: Foreground 529 gating by querySource
- Retry: Max tokens overflow adjustment
- Cache-Break: Effort + extra body params + overage latching
- Cache-Break: TTL expiry attribution

### Defer (High, Requires State)
- Retry: Fast mode fallback + cooldown (model-selection state)
- Retry: Model fallback Opus->Sonnet (policy + config)
- Retry: Persistent unattended retry (infra + heartbeats)

## 5. KEY INSIGHT

Runnable sophistication driven by:
1. Multi-tenant SaaS constraints (subscriber gating, CCR auth, capacity cascades, fast-mode).
2. Extended thinking support (thinking budget, effort values).
3. Obsessive cache cost tracking (per-tool hashes, overage latching, TTL heuristics).

v5 single-tenant/on-device; adopt priority: media validation > per-tool hashing > token parsing.

