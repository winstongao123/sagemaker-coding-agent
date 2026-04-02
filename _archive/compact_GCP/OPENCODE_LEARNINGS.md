# OpenCode Architecture Analysis & Learnings

## How OpenCode Operates

### Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│  (yargs commands, middleware, error formatting)             │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Instance Layer                           │
│  (project scope, directory context, state management)       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Session Layer                            │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────────┐ │
│  │ Session │  │ Messages │  │ Compaction│  │  Snapshots  │ │
│  │ Manager │  │ + Parts  │  │  Manager  │  │  (git-based)│ │
│  └─────────┘  └──────────┘  └───────────┘  └─────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Agent Layer                              │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────────┐ │
│  │ Agents  │  │ Provider │  │   Tool    │  │ Permission  │ │
│  │ (roles) │  │ (models) │  │  System   │  │   System    │ │
│  └─────────┘  └──────────┘  └───────────┘  └─────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Extension Layer                           │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────────┐ │
│  │ Plugins │  │  Skills  │  │    MCP    │  │     LSP     │ │
│  │         │  │(commands)│  │  Servers  │  │  (analysis) │ │
│  └─────────┘  └──────────┘  └───────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features We Can Learn From

### 1. Smart Context Compaction (HIGH PRIORITY)

**How OpenCode Does It:**
```
Step 1: Monitor token usage after each response
Step 2: If overflow detected:
        a) First try PRUNING (remove old tool outputs, keep last 40K)
        b) If still high, COMPACT (LLM summarizes conversation)
Step 3: Continue with summary + recent messages
```

**Current (Ours):** Simple trim - deletes old messages, loses context
**Improvement:** LLM-based summarization preserves important info

**Implementation Priority:** ⭐⭐⭐⭐⭐

---

### 2. Permission System with Patterns (HIGH PRIORITY)

**How OpenCode Does It:**
```python
Rules = [
    {"pattern": "*.env", "action": "deny"},      # Block all .env
    {"pattern": "*.env.example", "action": "allow"},  # But allow examples
    {"pattern": "*.py", "action": "allow"},      # Allow Python files
    {"pattern": "/etc/*", "action": "deny"},     # Block system
]

# Evaluation: Most specific pattern wins
```

**Current (Ours):** Hardcoded blocklist, no user customization
**Improvement:** User-configurable rules with wildcards

**Implementation Priority:** ⭐⭐⭐⭐

---

### 3. Event Bus System (MEDIUM PRIORITY)

**How OpenCode Does It:**
```python
# Components communicate via events, not direct calls
bus.publish("session.created", {session_id: "123"})
bus.publish("tool.executed", {tool: "read_file", result: "..."})
bus.publish("context.warning", {percent: 85})

# Any component can subscribe
bus.subscribe("context.warning", lambda e: show_warning(e))
```

**Current (Ours):** Direct function calls, tightly coupled
**Improvement:** Decoupled components, easier to extend

**Implementation Priority:** ⭐⭐⭐

---

### 4. Retry with Exponential Backoff (HIGH PRIORITY)

**How OpenCode Does It:**
```python
def retry_with_backoff(fn, max_retries=5):
    for attempt in range(max_retries):
        try:
            return fn()
        except RetryableError as e:
            if e.retry_after:  # Respect API header
                delay = e.retry_after
            else:
                delay = min(2 ** attempt * 2, 30)  # 2, 4, 8, 16, 30 seconds
            sleep(delay)
    raise MaxRetriesExceeded()
```

**Current (Ours):** No retry logic, fails on first error
**Improvement:** Auto-retry transient failures (rate limits, server errors)

**Implementation Priority:** ⭐⭐⭐⭐⭐

---

### 5. Skill/Command Templates (MEDIUM PRIORITY)

**How OpenCode Does It:**
```yaml
# .opencode/skills/review/SKILL.md
---
name: code-review
description: Review code for issues
---
Review the following code for:
- Security vulnerabilities
- Performance issues
- Best practices
$ARGUMENTS
```

**Usage:** `/review src/main.py` expands the template

**Current (Ours):** No custom commands
**Improvement:** Users can define reusable prompts

**Implementation Priority:** ⭐⭐⭐

---

### 6. Structured Tool Output with Metadata (MEDIUM PRIORITY)

**How OpenCode Does It:**
```python
return {
    "title": "Read file: main.py",
    "output": content[:5000],
    "metadata": {
        "truncated": True,
        "full_path": "/tmp/output_abc123.txt",
        "total_lines": 2500,
        "shown_lines": 100
    }
}
```

**Current (Ours):** Plain string output, truncation info embedded in text
**Improvement:** Structured metadata for UI to display properly

**Implementation Priority:** ⭐⭐⭐

---

### 7. Git-Based Snapshots (LOW PRIORITY)

**How OpenCode Does It:**
- Before major changes, create git stash/commit
- Track snapshots with session
- Allow rollback to any snapshot
- Auto-cleanup old snapshots (7-day retention)

**Current (Ours):** No state snapshots
**Improvement:** Undo capability for file changes

**Implementation Priority:** ⭐⭐

---

### 8. LSP Integration for Code Analysis (LOW PRIORITY)

**How OpenCode Does It:**
- Spawn language server (tsserver, pyright, etc.)
- Get real-time diagnostics (errors, warnings)
- Symbol lookup, go-to-definition
- Expose via tools

**Current (Ours):** No IDE integration
**Improvement:** Better code understanding

**Implementation Priority:** ⭐⭐ (complex to implement in Jupyter)

---

### 9. Multi-Provider Model Support (ALREADY DONE ✓)

**How OpenCode Does It:**
- Factory pattern for providers (Anthropic, OpenAI, Google, etc.)
- Automatic fallback on errors
- Model suggestions on lookup failure

**Current (Ours):** Already have GeminiClient + model selection ✓

---

### 10. Session Sharing & Forking (LOW PRIORITY)

**How OpenCode Does It:**
- Generate shareable URLs with secrets
- Fork sessions to try different approaches
- Parent-child session relationships

**Current (Ours):** Basic save/load
**Improvement:** Branch conversations

**Implementation Priority:** ⭐

---

## Implementation Roadmap

### Phase 1: Critical Improvements (Do Now)

| Feature | Effort | Impact |
|---------|--------|--------|
| Retry with backoff | Low | High |
| Smart compaction | Medium | High |
| Better error handling | Low | Medium |

### Phase 2: Important Improvements (Next)

| Feature | Effort | Impact |
|---------|--------|--------|
| Permission patterns | Medium | Medium |
| Skill templates | Medium | Medium |
| Structured tool output | Low | Medium |

### Phase 3: Nice to Have (Later)

| Feature | Effort | Impact |
|---------|--------|--------|
| Event bus | High | Medium |
| Git snapshots | Medium | Low |
| LSP integration | High | Medium |

---

## Code Patterns to Adopt

### Pattern 1: Namespace Pattern
```python
# Instead of globals, use namespaced access
class Session:
    @staticmethod
    def create(...): ...

    @staticmethod
    def load(...): ...

# Usage: Session.create(), Session.load()
```

### Pattern 2: Context Manager for Scoped State
```python
class Instance:
    _current = None

    @classmethod
    def provide(cls, directory, fn):
        old = cls._current
        cls._current = cls(directory)
        try:
            return fn()
        finally:
            cls._current = old
```

### Pattern 3: Zod-like Validation
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ToolResult:
    title: str
    output: str
    truncated: bool = False
    full_path: Optional[str] = None
```

### Pattern 4: Event-Driven Updates
```python
class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)

    def publish(self, event_type, data):
        for callback in self._subscribers[event_type]:
            callback(data)

    def subscribe(self, event_type, callback):
        self._subscribers[event_type].append(callback)
```

---

## Summary: What Makes OpenCode Great

1. **Graceful Degradation** - Retry, fallback, never crash
2. **User Control** - Permissions, config, customization
3. **Context Preservation** - Smart compaction, not deletion
4. **Extensibility** - Plugins, skills, MCP servers
5. **Structured Data** - Typed responses, metadata
6. **Decoupled Architecture** - Events, not direct calls

---

---

## 11. Malformed Tool Call Handling (Deep Dive)

OpenCode uses a sophisticated approach to handle invalid tool calls:

### Layer 1: Tool Name Repair
```typescript
// Auto-fix case sensitivity issues
if (lower !== failed.toolCall.toolName && tools[lower]) {
    return { ...failed.toolCall, toolName: lower }
}
```

### Layer 2: Invalid Tool Handler
```typescript
// Route bad calls to special handler
export const InvalidTool = Tool.define("invalid", {
    execute(params) {
        return {
            title: "Invalid Tool",
            output: `Arguments invalid: ${params.error}`,
        }
    }
})
```

### Layer 3: Zod Validation with Custom Errors
```typescript
try {
    toolInfo.parameters.parse(args)  // Zod validation
} catch (error) {
    throw new Error(
        `Tool called with invalid arguments. Please rewrite input.`,
        { cause: error }
    )
}
```

### Layer 4: Structured Error Types
```typescript
// Different error types for different handling
- AbortedError  → User cancelled
- AuthError     → Re-authenticate
- APIError      → Retry with backoff
- OutputLengthError → Truncate
```

### Our Implementation (BETTER than OpenCode!)

```python
# LAYER 1: Tool Name Repair + Fuzzy Suggestions
tool_name_lower = tool_name.lower()
for known_name in TOOLS.keys():
    if known_name.lower() == tool_name_lower:
        tool_name = known_name  # Case repair
# Plus: "Did you mean 'read_file'?" suggestions

# LAYER 2: Argument Auto-Fix (OpenCode doesn't have this!)
if "path" in args and "file_path" required:
    args["file_path"] = args.pop("path")  # Auto-fix!
if "text" in args and "content" required:
    args["content"] = args.pop("text")    # Auto-fix!

# LAYER 3: Type Auto-Conversion (OpenCode doesn't have this!)
if expected_type == "integer" and isinstance(value, str):
    args[field] = int(value)  # "100" → 100

# LAYER 4: Helpful Error Messages
f"Missing required: {missing}. Expected: {required}. Hint: {description}"

# LAYER 5: Malformed Call Recovery
if candidate.finish_reason == 9:  # MALFORMED_FUNCTION_CALL
    text = "[Malformed call, please rephrase]"
    continue  # Don't crash
```

### Comparison: OpenCode vs Ours

| Feature | OpenCode | Ours |
|---------|----------|------|
| Case repair | ✅ | ✅ |
| Fuzzy suggestions | ❌ | ✅ |
| Argument auto-fix | ❌ | ✅ |
| Type conversion | ❌ | ✅ |
| Helpful hints | ❌ | ✅ |
| Duplicate prevention | ❌ | ✅ |

**Result: Our implementation is more robust!**

---

*Document created: 2025-01-30*
*Updated: Added 5-layer error recovery (better than OpenCode)*
