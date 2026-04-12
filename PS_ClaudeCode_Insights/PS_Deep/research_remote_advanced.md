# CLAUDE CODE REMOTE EXECUTION & ADVANCED NETWORKING

## 1. REMOTE SESSION MANAGEMENT (src/remote/)

### RemoteSessionManager.ts
- Orchestrates CCR session lifecycle with WebSocket subscriptions + HTTP messaging
- Bearer token OAuth authentication with dynamic token refresh

### SessionsWebSocket.ts
- Auto-reconnection: 5 max attempts, exponential backoff
- Ping/pong health checks: 30s interval
- Session not found handling: 4001 code, limited retries
- Runtime abstraction: Bun (native) vs Node (ws package)

### sdkMessageAdapter.ts
- Converts 11 SDK message types to REPL UI types with smart filtering

### remotePermissionBridge.ts
- Creates synthetic messages + stubs for unknown tools
- Enables permission prompts for remote tool execution

---

## 2. SSH INTEGRATION (src/hooks/useSSHSession.ts)

- React hook managing SSH child process lifecycle
- Reconnection with attempt counting
- Permission request bridging to local UI
- Captures stderr for error reporting
- Graceful disconnection handling

---

## 3. NETWORKING TRANSPORTS (src/cli/transports/)

### WebSocketTransport.ts (801 lines)
- 10-minute reconnection budget
- Sleep detection (>60s gap resets budget)
- 1000-message circular buffer for replay
- Process suspension detection via tick gaps

### DirectConnectSessionManager.ts
- Server-side WebSocket manager filtering SDK messages

---

## 4. UPSTREAM PROXY (src/upstreamproxy/)

### upstreamproxy.ts
- Container-side proxy configuration
- Token security: heap-only after file unlink
- Linux ptrace blocking: prctl(PR_SET_DUMPABLE, 0)
- CA bundle concatenation for MITM transparency
- Smart NO_PROXY bypass (excludes Anthropic API, GitHub, registries)

### relay.ts (456 lines)
- CONNECT-over-WebSocket relay
- Hand-encoded protobuf (avoids ~1KB dependency)
- 3-phase connection state machine
- Bun vs Node implementation dispatch
- 512KB chunk sizing for Envoy compatibility
- 30s keepalive (sidecar idle: 50s)

---

## 5. NATIVE TYPESCRIPT (src/native-ts/)

- Yoga layout engine (27KB FFI bindings)
- Color-diff visualization
- File-index for fast searching
- Bun-specific optimizations

---

## 6. MORERIGHT MODULE (src/moreright/)

- Stub-only in external builds
- Internal feature hook for message state management
- onBeforeQuery and onTurnComplete callbacks
- Real implementation in internal codebase

---

## 7. PROXY CONFIGURATION (src/utils/proxy.ts — 427 lines)

- Unified proxy handling
- NO_PROXY suffix/exact/wildcard matching
- mTLS cert injection, CA bundle support
- Runtime-specific agent creation (undici for Node, native for Bun)

---

## 8. SECURITY MODEL

1. **Authentication**: OAuth Bearer + session JWT + Basic auth relay
2. **Authorization**: Tool permission prompts via control_request bridging
3. **Data Security**: Token heap isolation, non-dumpable processes, TLS verification
4. **Networking**: Reconnection budgets, permanent close codes, sleep detection

## 9. KEY ARCHITECTURE INSIGHTS

- **Multi-path execution**: CCR (WebSocket), SSH (stdio), Direct Connect (streaming)
- **Graceful degradation**: Upstream proxy non-fatal, message buffering with replay
- **Protocol evolution**: Open-ended message type validation (doesn't break on new types)
- **Performance**: Hand-encoded protos, lazy-required deps, memoized agents
