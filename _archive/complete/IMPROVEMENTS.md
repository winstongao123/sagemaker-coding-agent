# SageMaker Agent (Modular Version) - Improvements

## Overview

This document tracks all improvements synced from the GCP Gemini version to the AWS Bedrock modular version.

---

## 1. Retry Logic with Exponential Backoff (NEW)

**File:** `core/agent_loop.py`

```python
class RetryHandler:
    RETRYABLE_CODES = {429, 500, 502, 503, 504}
    RETRYABLE_MESSAGES = ["rate_limit", "overloaded", "throttl"]

    def execute(self, fn, on_retry=None):
        for attempt in range(max_retries + 1):
            try:
                return fn()
            except Exception as e:
                if is_retryable(e):
                    delay = 2^attempt + jitter
                    time.sleep(delay)
```

**Features:**
- Automatic retry for transient errors (429, 500, 502, 503, 504)
- Exponential backoff: 2s, 4s, 8s, 16s, 30s max
- Respects Retry-After headers
- Callback for retry notifications

---

## 2. Smart Context Compaction (NEW)

**File:** `core/agent_loop.py`

```python
class Compactor:
    # Stage 1: Prune old tool outputs (keep last 40K tokens)
    # Stage 2: If still high, create conversation summary
    # Result: Keep summary + last 5 messages
```

**Features:**
- Preserves important context instead of deleting
- Prunes oldest tool outputs first
- Creates intelligent summaries when needed
- Triggers at 80% context usage

---

## 3. Extended Security Patterns

**File:** `core/security.py`

### Bash Command Blocking

| Before | After |
|--------|-------|
| 14 patterns | **51 patterns** |

**New protections:**
- Fork bombs, disk operations, privilege escalation
- Network attacks, credential theft, system damage
- Crypto/ransomware patterns, Tor/onion services

### Python Code Validation (NEW)

**24 dangerous patterns now blocked:**
```python
os.system(), eval(), exec()
subprocess shell=True
pickle.loads(), ctypes.*
socket.bind(), socket.listen()
```

### Sensitive Files

| Before | After |
|--------|-------|
| 16 files | **18 files** |

New: `service-account.json`, `service_account.json` (GCP credentials)

### Secret Detection

| Before | After |
|--------|-------|
| 9 patterns | **10 patterns** |

New: GCP API Key pattern

---

## 4. Improved Doom Loop Detection

**File:** `core/agent_loop.py`

**Before:** Detected based on exact tool input match

**After:** Detected based on tool name + target file path
```python
target = input.get("file_path") or input.get("path")
key = (tool_name, target)

# Also prevents consecutive file rewrites
if last_call == (write_file, same_file):
    skip_duplicate()
```

---

## 5. Smart Truncation (NEW)

**File:** `core/agent_loop.py`

```python
class Truncation:
    MAX_LINES = 2000
    MAX_BYTES = 50 * 1024  # 50KB

    def truncate(text, direction="head"):
        if too_large:
            save_to_disk(text)  # Full content preserved
            return preview + f"[Full output saved: {path}]"
```

**Features:**
- Dual threshold: 2000 lines OR 50KB
- Full output saved to `./truncated_outputs/`
- Preview returned to context (saves tokens)
- Helpful hints for follow-up actions

---

## 6. Structured Tool Output (NEW)

**File:** `core/agent_loop.py`

```python
@dataclass
class ToolResult:
    output: str
    title: str = ""
    truncated: bool = False
    total_size: int = 0
    shown_size: int = 0
    metadata: Dict = {}
```

**Features:**
- Structured metadata for UI display
- Backward compatible (str conversion)
- Truncation info included

---

## 7. Improved Session Management (NEW)

**Note:** For UI improvements, see `compact/` version which includes:
- No auto-save (manual save only)
- Custom session naming
- "New" button for fresh sessions
- `clear_output(wait=True)` prevents duplicate widgets

---

## 8. Auto-Allow Mode (NEW)

**Problem:** Approval buttons not working in Jupyter blocking workflow.

**Solution:** Removed manual approval requirement like GCP version:
- All tools now have `requires_approval = False`
- Security enforced via validation (51 bash patterns, 24 Python patterns, path checks)

**Files Changed:**
- `tools/bash.py` - requires_approval=False
- `tools/file_ops.py` - requires_approval=False
- `tools/python_exec.py` - requires_approval=False
- `tools/document.py` - requires_approval=False

---

## 9. UI Improvements (NEW - Latest)

**File:** `agent.ipynb`

### Auto-Scroll Chat
```javascript
// JavaScript auto-scroll after each message
var containers = document.querySelectorAll('.jp-OutputArea, .output_area, .widget-output');
containers.forEach(function(c){
    if(c.scrollHeight > c.clientHeight) c.scrollTop = c.scrollHeight;
});
```

### Cleaner Agent Message Styling
```python
# Minimal style with just border accent (no heavy background)
<div style="padding:10px;margin:5px 0;border-left:3px solid #4a9eff;">
    <b style="color:#4a9eff;">[timestamp] Agent:</b>
    <pre style="color:#e0e0e0;">...</pre>
</div>
```

### Chat Height Increased
```python
chat_output = widgets.Output(layout=widgets.Layout(height='500px', ...))
```

### Tool Icons
```python
TOOL_ICONS = {
    'read_file': '📖', 'write_file': '📝', 'bash': '💻', ...
}
```

---

## Summary Table

```
FEATURE                    | BEFORE          | AFTER
---------------------------|-----------------|------------------
API Retry Logic            | None            | Exponential backoff
Context Compaction         | Simple trim     | Smart prune+summarize
Bash Security Patterns     | 14              | 51
Python Security            | None            | 24 patterns
Doom Loop Detection        | Full input match| File path match
Duplicate Prevention       | None            | Skip consecutive
Smart Truncation           | Basic cut       | Smart (disk save)
Structured Tool Output     | Plain string    | ToolResult dataclass
Default Model              | Sonnet          | Haiku (8 req/min)
Approval Requirement       | Manual          | Auto-allow (security check only)
Chat Auto-Scroll           | None            | JavaScript scroll
Agent Styling              | Heavy background| Clean border accent
Chat Height                | 400px           | 500px
Tool Icons                 | None            | TOOL_ICONS dict
```

---

## Files Changed

- `core/security.py` - Extended security patterns + validate_python()
- `core/agent_loop.py` - RetryHandler, Compactor, Truncation, ToolResult, improved doom loop
- `tools/*.py` - All requires_approval set to False
- `agent.ipynb` - Haiku as default model
- `IMPROVEMENTS.md` - This documentation

---

## Usage

```python
# In Jupyter/SageMaker:
from complete.core.agent_loop import AgentLoop
from complete.core.security import SecurityManager

# AgentLoop now includes:
# - Automatic retry with exponential backoff
# - Smart context compaction
# - Improved doom loop detection
# - Auto-allow mode (no approval dialogs)
```

---

*Last updated: 2026-01-31*
*Synced from: compact_GCP (Gemini version)*
*Latest: Auto-scroll, Clean agent styling, 500px chat height, Tool icons*
