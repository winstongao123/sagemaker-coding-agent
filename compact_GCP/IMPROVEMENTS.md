# Gemini Agent Improvements

## Comparison: `compact/` (AWS) vs `compact_GCP/` (GCP Gemini)

This document tracks all improvements made to the GCP Gemini agent compared to the original AWS SageMaker agent.

---

## 1. Model Support

| Feature | AWS (Original) | GCP (Improved) |
|---------|---------------|----------------|
| Models | Single: Claude 3.5 Sonnet | **6+ models** |
| Selection | Hardcoded | Dropdown UI |
| Config | Fixed | Environment variables |

**GCP Available Models:**
- `gemini-2.5-pro-preview-05-06` - Best quality
- `gemini-2.5-flash-preview-04-17` - Fast + smart
- `gemini-2.0-flash-001` - Stable (recommended)
- `gemini-1.5-pro-001` - High quality
- `gemini-1.5-flash-001` - Very fast

---

## 2. Security (Major Improvement)

### Bash Command Blocking

| AWS | GCP |
|-----|-----|
| 11 patterns | **51 patterns** |

**New GCP protections:**
- Fork bombs (`:(){:|:&};`)
- Disk operations (`fdisk`, `parted`, `mount`)
- Privilege escalation (`su -`, `chmod +s`, `chown root`)
- Network attacks (`nmap`, `iptables`)
- Credential theft (`cat /etc/shadow`, `.ssh/`)
- System damage (`shutdown`, `reboot`, `killall -9`)
- Crypto/ransomware patterns
- Tor/onion services

### Python Code Validation (NEW)

AWS: **None**
GCP: **24 dangerous patterns blocked**

```python
# Blocked patterns:
os.system()           # Shell injection
eval(), exec()        # Code injection
subprocess shell=True # Command injection
pickle.loads()        # Deserialization attack
open('/etc/...')      # System file access
shutil.rmtree('/')    # System deletion
socket.bind()         # Network server
ctypes.*              # Low-level access
```

### Secret Detection

| Type | AWS | GCP |
|------|-----|-----|
| Patterns | 9 | **10** |
| New | - | GCP API Key |

### Sensitive Files

| AWS | GCP |
|-----|-----|
| 10 files | **12 files** |
| New | `service-account.json`, `service_account.json` |

---

## 3. Token & Context Management

| Feature | AWS | GCP |
|---------|-----|-----|
| Context Window | 200K tokens | **1M tokens** |
| Max Output | 5,000 chars | **50,000 chars** |
| Truncation | Basic (cut off) | **Smart (save to disk)** |

### Smart Truncation (NEW)
- Large outputs saved to `./truncated_outputs/`
- Preview returned to context (saves tokens)
- Dual threshold: 2000 lines OR 50KB
- Directional: head or tail

---

## 4. UI Improvements

| Feature | AWS | GCP |
|---------|-----|-----|
| Model Selector | No | **Yes (dropdown)** |
| Duplicate Prevention | No | **Yes (dedup tracking)** |
| Tool Output | Always expanded | **Collapsed (OpenCode style)** |
| Threading | Sync (blocks) | Sync (fixed) |

### Collapsible Tool Output
```html
<details>
  <summary>📖 read_file ✓ preview...</summary>
  <pre>Full content here...</pre>
</details>
```

---

## 5. Configuration

### AWS (Hardcoded)
```python
region = "ap-southeast-2"
model_id = "anthropic.claude-3-5-sonnet..."
```

### GCP (Environment Variables)
```python
project_id = os.environ.get("GEMINI_PROJECT", "default")
region = os.environ.get("GEMINI_REGION", "us-central1")
model_id = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-001")
temperature = os.environ.get("GEMINI_TEMPERATURE", "0.0")
thinking_enabled = os.environ.get("GEMINI_THINKING", "true")
thinking_budget = os.environ.get("GEMINI_THINKING_BUDGET", "8192")
```

---

## 6. Tools (Same Count, Enhanced)

Both: **15 tools**

| Tool | AWS | GCP |
|------|-----|-----|
| read_file | ✓ | ✓ + better limits |
| write_file | ✓ | ✓ |
| edit_file | ✓ | ✓ |
| list_dir | ✓ | ✓ |
| glob | ✓ | ✓ |
| grep | ✓ | ✓ |
| bash | ✓ | ✓ + more security |
| python_exec | ✓ | ✓ + **code validation** |
| create_word | ✓ | ✓ |
| create_excel | ✓ | ✓ |
| create_markdown | ✓ | ✓ |
| view_image | ✓ | ✓ |
| semantic_search | ✓ | ✓ |
| todo_write | ✓ | ✓ |
| todo_read | ✓ | ✓ |

---

## 7. Session Management (IMPROVED)

**Features:**
- JSON storage in `./sessions/`
- Create, load, save, delete
- **NO auto-save** - sessions only saved when clicking "Save" button
- Custom session naming via text input
- "New" button for fresh sessions
- `clear_output(wait=True)` prevents duplicate UI widgets

**New UI Widgets:**
```python
session_name_input = widgets.Text(placeholder='Session name (optional)')
new_btn = widgets.Button(description='New', button_style='success')

---

## 8. Summary Table

```
IMPROVEMENT AREA          | BEFORE (AWS)    | AFTER (GCP)
--------------------------|-----------------|------------------
Model Support             | 1               | 6+
Context Window            | 200K            | 1M
Max Output                | 5K chars        | 50K chars
Bash Security Patterns    | 11              | 51
Python Security           | None            | 24 patterns
Output Truncation         | Basic           | Smart (disk save)
Tool Output UI            | Expanded        | Collapsed
Model Selection UI        | None            | Dropdown
Configuration             | Hardcoded       | Env variables
Duplicate Prevention      | None            | Dedup tracking
API Retry Logic           | None            | Exponential backoff
Context Compaction        | Simple trim     | Smart prune+summarize
Error Recovery            | Fail on first   | Auto-retry 5x
Tool Output               | Plain string    | Structured metadata
Session Management        | Auto-save all   | Manual save + naming
UI Widget Handling        | Duplicates      | clear_output
```

---

## Files Changed

- `gemini_agent.py` - Main agent (rewritten for GCP)
- `IMPROVEMENTS.md` - This documentation
- `GUIDE.md` - Usage guide

---

## Usage

```python
# In Jupyter/Colab:
%run gemini_agent.py
create_chat_ui()
```

**Environment setup (optional):**
```bash
export GEMINI_PROJECT="your-project-id"
export GEMINI_REGION="us-central1"
export GEMINI_MODEL="gemini-2.5-flash-preview-04-17"
```

---

## 9. Token Tracking Explained

```
📊 In: 763,606 | Out: 11,306 | Total: 774,912 | Calls: 49
Context: 3% (26,632 tokens)
```

| Metric | Meaning |
|--------|---------|
| **In** | Cumulative tokens SENT to API (all calls combined) |
| **Out** | Cumulative tokens RECEIVED from API |
| **Total** | Billing total (In + Out) |
| **Context** | Current conversation size in memory |

**Why In >> Context?**

Each API call sends the FULL conversation history:
- Call 1: 1k tokens
- Call 2: 2k tokens (includes call 1 context)
- Call N: grows with conversation

Cumulative = sum of all calls = much larger than current context.

---

## 10. New Features (OpenCode-Inspired)

### Retry with Exponential Backoff
```python
# Automatic retry for transient errors
- Rate limit (429)
- Server errors (500, 502, 503, 504)
- Quota exceeded
- Exponential backoff: 2s, 4s, 8s, 16s, 30s max
- Respects Retry-After headers
```

### Smart Context Compaction
```python
# Instead of simple deletion:
Step 1: Prune old tool outputs (keep last 40K tokens)
Step 2: If still high, create conversation summary
Step 3: Keep summary + last 5 messages
# Result: Preserves important context!
```

### Structured Tool Output
```python
@dataclass
class ToolResult:
    output: str
    title: str
    truncated: bool
    total_size: int
    shown_size: int
    metadata: Dict
```

### Tool Error Recovery (BETTER than OpenCode!)

**Problem:** LLMs sometimes generate invalid tool calls (wrong names, bad arguments)

**Comparison: OpenCode vs Our Implementation**

| Feature | OpenCode | Ours | Winner |
|---------|----------|------|--------|
| Tool name case repair | ✅ `Bash`→`bash` | ✅ Same | Tie |
| Fuzzy tool suggestions | ❌ No | ✅ "Did you mean X?" | **Ours** |
| Argument auto-fix | ❌ No | ✅ `path`→`file_path` | **Ours** |
| Type auto-conversion | ❌ No | ✅ `"123"`→`123` | **Ours** |
| Helpful error messages | ⚠️ Basic | ✅ Shows schema + hints | **Ours** |
| Malformed call recovery | ⚠️ Route to handler | ✅ Extract text + continue | **Ours** |
| Duplicate call prevention | ❌ No | ✅ Skip consecutive rewrites | **Ours** |

**Our 5-Layer Error Recovery:**

```python
# LAYER 1: Tool Name Repair
"Read_File" → "read_file"  # Case fix
"readfile" → "read_file"   # Fuzzy match suggestion

# LAYER 2: Argument Auto-Fix
{"path": "x.py"} → {"file_path": "x.py"}      # Common alias
{"text": "hello"} → {"content": "hello"}       # Common alias
{"query": "def"} → {"pattern": "def"}          # For grep

# LAYER 3: Type Auto-Conversion
{"limit": "100"} → {"limit": 100}  # String to int
{"timeout": 30} → {"timeout": "30"}  # Int to string (if needed)

# LAYER 4: Validation with Helpful Errors
"Missing required: ['content']. Expected: ['file_path', 'content']. Hint: Write content to file."

# LAYER 5: Execution Error Recovery
TypeError → Show expected schema
KeyError → Show required fields
Exception → Show tool description
```

**Auto-Fix Examples:**

| LLM Sends | We Fix To | Result |
|-----------|-----------|--------|
| `Read_File(path="x.py")` | `read_file(file_path="x.py")` | ✅ Works |
| `bash(cmd="ls")` | `bash(command="ls")` | ✅ Works |
| `grep(query="def")` | `grep(pattern="def")` | ✅ Works |
| `write_file(text="hi")` | `write_file(content="hi")` | ✅ Works |
| `readfile(...)` | "Did you mean read_file?" | ✅ Helpful |

**Result: More robust than OpenCode!**

---

## 11. Test Results (Verified)

| Feature | Status | Notes |
|---------|--------|-------|
| Security blocking | ✅ | `rm -rf /` blocked |
| Excel creation | ✅ | sales_report.xlsx |
| Word creation | ✅ | report.docx |
| Code generation | ✅ | DataProcessor class |
| Codebase analysis | ✅ | Found 14 classes |
| Bug finding | ✅ | ZeroDivisionError |
| Multi-file creation | ✅ | REST API structure |
| Code explanation | ✅ | SecurityManager |

---

*Last updated: 2025-01-31*
