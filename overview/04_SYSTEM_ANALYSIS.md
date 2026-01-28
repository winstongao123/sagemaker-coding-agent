# System Analysis - Token Efficiency & Design Review

## Token Efficiency Analysis

### Current System Prompt Size

| Section | Tokens | Necessity |
|---------|--------|-----------|
| Tone and style | ~150 | Required |
| Professional objectivity | ~100 | Required |
| Task management | ~400 | Could reduce |
| Examples in prompt | ~300 | Could remove |
| Doing tasks | ~150 | Required |
| Tool usage policy | ~200 | Required |
| Code references | ~100 | Could reduce |
| Critical rules | ~100 | Required |
| Security context | ~150 | Required |
| Tools list | ~200 | Could remove |
| **Total** | **~1,850** | |

### Token Waste Identified

| Issue | Tokens Wasted | Fix |
|-------|---------------|-----|
| Examples in system prompt | ~300/request | Move to AGENTS.md |
| Tool list in prompt | ~200/request | Tool definitions already sent |
| Redundant rules | ~100/request | Consolidate |
| **Total Waste** | **~600/request** | |

### Optimized Prompt (Recommended)

**Current:** ~1,850 tokens
**Optimized:** ~1,250 tokens
**Savings:** 600 tokens/request = **32% reduction**

---

## Per-Request Analysis

### Current Flow (Inefficient)
```
Request 1: User asks "list files"
  System prompt:     1,850 tokens
  Tool definitions:    800 tokens
  User message:         20 tokens
  History:               0 tokens
  ─────────────────────────────────
  Total Input:       2,670 tokens

Request 2: User asks "read config.py"
  System prompt:     1,850 tokens  ← REPEATED
  Tool definitions:    800 tokens  ← REPEATED
  User message:         20 tokens
  History:            +200 tokens  ← Growing
  ─────────────────────────────────
  Total Input:       2,870 tokens

Request 10: (After conversation)
  System prompt:     1,850 tokens
  Tool definitions:    800 tokens
  User message:         50 tokens
  History:         +3,000 tokens  ← Expensive!
  ─────────────────────────────────
  Total Input:       5,700 tokens
```

### Optimization Opportunities

| Optimization | Savings | Difficulty |
|--------------|---------|------------|
| Shorter system prompt | 600 tokens/req | Easy |
| Fewer tool definitions | 200-400 tokens/req | Medium |
| History summarization | 1,000+ tokens/req | Hard |
| Session-based caching | N/A (not supported) | N/A |

---

## Design Flaws Identified

### Flaw 1: No History Summarization

**Problem:**
Conversation history grows unbounded until context limit.

**Current Behavior:**
```python
# Every message added to history
self.messages.append({"role": "user", "content": message})
self.messages.append({"role": "assistant", "content": response})
# Never trimmed!
```

**Impact:**
- After 20 turns: ~5,000 tokens just for history
- After 50 turns: ~15,000 tokens
- Context fills up fast

**Recommendation:**
Add sliding window or summarization:
```python
def trim_history(messages, max_tokens=10000):
    """Keep recent messages, summarize old ones."""
    if count_tokens(messages) > max_tokens:
        # Keep last 10 messages
        recent = messages[-10:]
        # Summarize older messages
        summary = summarize(messages[:-10])
        return [{"role": "system", "content": f"Previous: {summary}"}] + recent
    return messages
```

---

### Flaw 2: Tool Definitions Sent Every Request

**Problem:**
All 13 tool definitions (~800 tokens) sent with every API call.

**Current Behavior:**
```python
# Always sends all tools
response = client.chat(messages, system, tools=ALL_TOOLS)
```

**Impact:**
- 800 extra tokens per request
- Even for simple "hello" messages

**Recommendation:**
Dynamic tool selection:
```python
def select_tools(user_message):
    """Only include relevant tools."""
    if "file" in user_message.lower():
        return [READ_FILE, WRITE_FILE, EDIT_FILE]
    if "search" in user_message.lower():
        return [GREP, GLOB]
    # Default minimal set
    return [READ_FILE, GREP, BASH]
```

---

### Flaw 3: No Response Caching

**Problem:**
Same queries repeat the full API call.

**Example:**
```
User: "What files are in src/"
# Calls Bedrock, uses tokens

User: "What files are in src/"  (repeat)
# Calls Bedrock AGAIN, uses more tokens
```

**Recommendation:**
Add simple cache:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_read_file(path):
    return read_file(path)
```

---

### Flaw 4: Full File Content in History

**Problem:**
When agent reads a file, entire content goes into history.

**Current:**
```python
# File read result added to messages
messages.append({
    "role": "tool",
    "content": file_content  # Could be 10,000 tokens!
})
```

**Impact:**
- Reading one large file can use 10,000+ tokens
- File content persists in history forever

**Recommendation:**
Truncate in history, keep reference:
```python
def add_tool_result(messages, result, max_tokens=1000):
    if len(result) > max_tokens:
        messages.append({
            "role": "tool",
            "content": f"[File: {path}]\n{result[:max_tokens]}...\n[Truncated, full content available via read_file]"
        })
```

---

### Flaw 5: No Streaming to User

**Problem:**
Agent waits for full response before showing to user.

**Current:**
```python
response = client.chat(...)  # Blocks until complete
display(response.text)       # Then shows
```

**Impact:**
- User waits 5-30 seconds seeing nothing
- Poor user experience

**Recommendation:**
Use streaming:
```python
def stream_response(client, messages, on_token):
    for chunk in client.stream_chat(messages):
        on_token(chunk.text)  # Show immediately
```

---

### Flaw 6: Semantic Search Always Loads Index

**Problem:**
Every semantic search reloads the entire index from disk.

**Current:**
```python
def search(self, query):
    if not self.chunks:
        self._load_index()  # Loads every time
```

**Recommendation:**
Cache index in memory:
```python
_index_cache = None

def search(self, query):
    global _index_cache
    if _index_cache is None:
        _index_cache = self._load_index()
    self.chunks = _index_cache
```

---

## Architecture Issues

### Issue 1: Circular Imports Risk

**Problem:**
`tools/__init__.py` imports from `core/tools.py` which could import tools.

**Current:**
```python
# tools/__init__.py
from .file_ops import READ_FILE  # This imports from core.tools
```

**Risk:** Circular import if core/tools imports from tools/

**Status:** Currently works, but fragile.

---

### Issue 2: Global State in Todo

**Problem:**
Todo list stored in global variable.

**Current:**
```python
# tools/todo.py
_todos: List[Dict] = []  # Global!
```

**Impact:**
- Not thread-safe
- Shared across all sessions if running multiple

**Recommendation:**
Store in context or session:
```python
def todo_write(args, ctx):
    ctx.session.todos = args["todos"]
```

---

### Issue 3: No Graceful Degradation

**Problem:**
If Bedrock fails, entire system fails.

**Current:**
```python
response = client.chat(...)  # Exception crashes everything
```

**Recommendation:**
Add fallback:
```python
try:
    response = client.chat(...)
except ThrottlingException:
    return "Rate limited. Please wait and try again."
except Exception as e:
    return f"API error: {e}. Try again or check AWS status."
```

---

## Security Design Review

### Good Decisions ✓

| Decision | Why Good |
|----------|----------|
| Workspace boundary | Prevents path traversal |
| Command blocklist | Stops obvious attacks |
| Audit logging | Forensics capability |
| Approval system | User control |
| Secret redaction | Prevents key exposure in logs |

### Potential Weaknesses

| Weakness | Risk | Mitigation |
|----------|------|------------|
| Regex-based secret detection | Can be bypassed | Add ML-based detection |
| Blocklist approach | New attacks bypass | Add allowlist option |
| No rate limiting | Abuse possible | Add per-session limits |
| Plain JSON sessions | Could be tampered | Add encryption/signing |

---

## Recommendations Summary

### High Priority (Token Savings)

1. **Reduce system prompt** - Save 600 tokens/request
2. **Add history summarization** - Save 1,000+ tokens after 20 turns
3. **Truncate file content in history** - Prevent token explosion

### Medium Priority (Performance)

4. **Add response streaming** - Better UX
5. **Cache semantic search index** - Faster searches
6. **Dynamic tool selection** - Save 200-400 tokens/request

### Low Priority (Code Quality)

7. **Fix global todo state** - Thread safety
8. **Add graceful degradation** - Better error handling
9. **Review circular import risk** - Future proofing

---

## Estimated Savings

| Optimization | Token Savings | Cost Savings |
|--------------|---------------|--------------|
| Shorter prompt | 600/request | ~$1.80/1000 requests |
| Tool selection | 300/request | ~$0.90/1000 requests |
| History trim | 2,000/request (avg) | ~$6.00/1000 requests |
| **Total** | **2,900/request** | **~$8.70/1000 requests** |

At 1000 requests/day: **~$260/month savings**
