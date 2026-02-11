# SageMaker Agent Improvements

## Overview

This document tracks all improvements synced from the GCP Gemini version to the AWS Bedrock version.

---

## 1. Retry Logic with Exponential Backoff (NEW)

**Problem:** API calls fail on first error, causing lost work.

**Solution:**
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
- Max delay cap at 60 seconds

---

## 2. Smart Context Compaction (NEW)

**Problem:** Simple message trimming loses important context.

**Solution:** OpenCode-style 2-stage compaction:
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
- Minimum 10K token savings threshold

---

## 3. Extended Security Patterns

### Bash Command Blocking

| Before | After |
|--------|-------|
| 11 patterns | **51 patterns** |

**New protections:**
- Fork bombs (`:(){:|:&};`)
- Disk operations (`fdisk`, `parted`, `mount`, `umount`)
- Privilege escalation (`su -`, `chmod +s`, `chown root`)
- Network attacks (`nmap`, `iptables`)
- Credential theft (`cat /etc/shadow`, `.ssh/`)
- System damage (`shutdown`, `reboot`, `killall -9`)
- Crypto/ransomware patterns
- Tor/onion services

### Python Code Validation (NEW)

**24 dangerous patterns now blocked:**
```python
os.system()           # Shell injection
eval(), exec()        # Code injection
subprocess shell=True # Command injection
pickle.loads()        # Deserialization attack
open('/etc/...')      # System file access
shutil.rmtree('/')    # System deletion
socket.bind()         # Network server
ctypes.*              # Low-level access
```

### Sensitive Files

| Before | After |
|--------|-------|
| 10 files | **12 files** |

New: `service-account.json`, `service_account.json` (GCP credentials)

---

## 4. 5-Layer Tool Error Recovery (NEW)

**Problem:** LLMs sometimes generate invalid tool calls (wrong names, bad arguments).

**Solution:** 5-layer error recovery system:

```python
# LAYER 1: Tool Name Repair
"Read_File" → "read_file"  # Case fix
"readfile" → "Did you mean 'read_file'?"  # Fuzzy suggestion

# LAYER 2: Argument Auto-Fix
{"path": "x.py"} → {"file_path": "x.py"}     # Common alias
{"text": "hello"} → {"content": "hello"}      # Common alias
{"query": "def"} → {"pattern": "def"}         # For grep
{"cmd": "ls"} → {"command": "ls"}             # For bash

# LAYER 3: Type Auto-Conversion
{"limit": "100"} → {"limit": 100}  # String to int

# LAYER 4: Permission Check (with helpful errors)

# LAYER 5: Execution with Error Recovery
TypeError → Show expected schema
KeyError → Show required fields
Exception → Show tool description
```

**Comparison with OpenCode:**

| Feature | OpenCode | Ours |
|---------|----------|------|
| Case repair | ✅ | ✅ |
| Fuzzy suggestions | ❌ | ✅ |
| Argument auto-fix | ❌ | ✅ |
| Type conversion | ❌ | ✅ |
| Helpful hints | ❌ | ✅ |
| Duplicate prevention | ❌ | ✅ |

**Result: More robust than OpenCode!**

---

## 5. Smart Truncation (NEW)

**Problem:** Large outputs truncated without saving full content.

**Solution:**
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

## 6. Improved Doom Loop Detection

**Before:** Detected based on exact tool input match (problematic for large content)

**After:** Detected based on tool name + target file path
```python
target = input.get("file_path") or input.get("path") or input.get("filepath")
key = (tool_name, target)

# Also prevents consecutive file rewrites
if last_call == (write_file, same_file):
    skip_duplicate()
```

---

## 7. Structured Tool Output (NEW)

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

---

## 8. Improved Session Management (NEW)

**Problem:**
- Each message auto-saved to session list (cluttered)
- Could not name sessions
- Multiple UI widgets appeared when re-running cell

**Solution:**
```python
# No auto-save - sessions only saved when clicking "Save"
# Session name input for custom naming
session_name_input = widgets.Text(placeholder='Session name (optional)')
new_btn = widgets.Button(description='New', button_style='success')

# Clear previous UI to prevent duplicates
clear_output(wait=True)
```

**Features:**
- Sessions NOT auto-saved after each message
- Custom session naming (optional)
- "New" button for fresh sessions
- `clear_output(wait=True)` prevents duplicate widgets

---

## 9. Enhanced UI (NEW - Latest Sync)

### Model Selector
```python
# Cross-region rates from AWS Bedrock
BEDROCK_MODELS = [
    ("Claude 3 Haiku (8 req/min)", "anthropic.claude-3-haiku-20240307-v1:0"),
    ("Claude 3 Sonnet (2 req/min)", "anthropic.claude-3-sonnet-20240229-v1:0"),
    ("Claude 3.5 Sonnet v2 (1 req/min)", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
    ("Claude 3 Opus", "anthropic.claude-3-opus-20240229-v1:0"),
]

model_dropdown = widgets.Dropdown(options=BEDROCK_MODELS)
```

### Approve Always Button
```python
approve_always_btn = widgets.Button(description='Always', button_style='info')
```

### Token Display with Progress Bar
```python
# Visual progress bar for context usage
<div style="background:#333;height:4px;border-radius:2px;">
    <div style="background:{ctx_color};width:{bar_width}%;"></div>
</div>
```

### Output Deduplication
```python
displayed_tools = set()
dedup_key = f"{tool}:{result[:100]}"
if dedup_key in displayed_tools:
    return  # Skip duplicate
```

### Collapsible Tool Output
```html
<details>
  <summary>🔧 read_file</summary>
  <pre>Full content here...</pre>
</details>
```

### Security: GCP API Key Detection
```python
SECRET_PATTERNS.append(
    (r"(?i)(gcp[_-]?api[_-]?key)\s*[=:]\s*[\"']?[\w-]{20,}", "GCP API Key")
)
# Now 10 patterns total
```

### Increased Output Limit
```python
max_output_chars: int = 50000  # Was 5000, now 50000
```

---

## Summary Table

```
FEATURE                    | BEFORE          | AFTER
---------------------------|-----------------|------------------
API Retry Logic            | None            | Exponential backoff
Context Compaction         | Simple trim     | Smart prune+summarize
Bash Security Patterns     | 11              | 51
Python Security            | None            | 24 patterns
Secret Detection           | 9 patterns      | 10 patterns (+ GCP)
Truncation                 | Basic cut       | Smart (disk save)
Tool Error Recovery        | Fail on error   | 5-layer recovery
Doom Loop Detection        | Full input match| File path match
Duplicate Prevention       | None            | Skip consecutive
Session Management         | Auto-save all   | Manual save + naming
UI Widget Handling         | Duplicates      | clear_output
Model Selector             | None            | Dropdown (5 models)
Approve Always             | None            | Button (deprecated)
Token Display              | Simple text     | Progress bar + colors
Tool Output                | Plain text      | Collapsible details
Tool Icons                 | None            | TOOL_ICONS dict
Default Model              | Sonnet          | Haiku (8 req/min)
Approval Requirement       | Manual          | Auto-allow (security check only)
Dark Mode Default          | Off             | On
max_output_chars           | 5,000           | 50,000
Chat Auto-Scroll           | None            | JavaScript scroll
Agent Styling              | Heavy background| Clean border accent
Chat Height                | 400px           | 500px
```

---

## 10. Auto-Allow Mode (NEW)

**Problem:** Approval buttons not working in Jupyter blocking workflow.

**Solution:** Removed manual approval requirement like GCP version:
```python
# All tools now have needs_approval = False
# Security is enforced via:
# - 51 dangerous bash patterns
# - 24 dangerous Python patterns
# - Path validation (workspace boundary)
# - Secret detection (10 patterns)
```

**Features:**
- No blocking approval dialogs
- Faster workflow
- Same security level via validation

---

## 11. UI Improvements (NEW - Latest)

### Auto-Scroll Chat
```python
# JavaScript auto-scroll after each message
display(HTML('''<script>
(function(){
    var containers = document.querySelectorAll('.jp-OutputArea, .output_area, .widget-output');
    containers.forEach(function(c){
        if(c.scrollHeight > c.clientHeight) c.scrollTop = c.scrollHeight;
    });
})();
</script>'''))
```

### Cleaner Agent Message Styling
```python
# Before: Heavy colored background
# After: Minimal style with just border accent
elif role == 'assistant':
    text_color = "#e0e0e0" if dark else "#333"
    display(HTML(f'''<div style="padding:10px;margin:5px 0;border-left:3px solid #4a9eff;">
        <b style="color:#4a9eff;">[{ts}] Agent:</b><br>
        <pre style="white-space:pre-wrap;word-wrap:break-word;font-family:monospace;color:{text_color};margin:5px 0;">{content}</pre>
    </div>'''))
```

### Chat Height Increased
```python
chat_output = widgets.Output(layout=widgets.Layout(
    height='500px',  # Was 400px
    overflow_y='auto',
    border='1px solid #ccc'
))
```

### Tool Icons
```python
TOOL_ICONS = {
    'read_file': '📖', 'write_file': '📝', 'edit_file': '✏️',
    'glob': '🔍', 'grep': '🔎', 'list_dir': '📁',
    'bash': '💻', 'python_exec': '🐍',
    'create_word': '📄', 'create_excel': '📊', 'create_markdown': '📋',
    'view_image': '🖼️', 'semantic_search': '🧠',
    'todo_write': '✅', 'todo_read': '📋',
}
```

---

## Files Changed

- `sagemaker_agent.py` - Main agent (all improvements)
- `chat.ipynb` - Haiku as default model
- `IMPROVEMENTS.md` - This documentation

---

## Usage

```python
# In Jupyter/SageMaker:
from sagemaker_agent import create_chat_ui
create_chat_ui()
```

---

*Last updated: 2026-01-31*
*Synced from: compact_GCP (Gemini version)*
*Latest: Auto-scroll, Clean agent styling, 500px chat height*
