# Context Compaction Implementation

**Based on: OpenCode (https://github.com/opencode-ai/opencode)**
**Version: 2.5.0**
**Implemented: January 2025**

---

## How Our Compaction Works

### Two-Stage Process (OpenCode-style)

```
User clicks "Compact" button
        ↓
┌─────────────────────────────────────────┐
│  Stage 1: PRUNE                         │
│  - Remove old tool outputs              │
│  - Keep last 40K tokens of tool results │
│  - Only prune if saving 10K+ tokens     │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│  Stage 2: SUMMARIZE                     │
│  - AI creates conversation summary      │
│  - Preserves: task, files, decisions    │
│  - Keep summary + last 5 messages       │
└─────────────────────────────────────────┘
        ↓
Auto-saves to session file
```

### Stage 1: Prune Tool Outputs

```python
PRUNE_PROTECT_TOKENS = 40000  # Keep last 40K tokens of tool outputs
PRUNE_MIN_SAVINGS = 10000     # Only prune if saving 10K+ tokens

def prune_tool_outputs(messages, max_context):
    # Walk from newest to oldest
    # Protect last 40K tokens of tool results
    # Replace old tool outputs with "[... X chars pruned ...]"
```

**Why prune first?**
- Tool outputs (file contents, bash results) are often large
- Old tool results are less relevant than recent ones
- Pruning can free 50%+ of context without losing conversation flow

### Stage 2: AI Summary

The AI is asked to summarize with this prompt:
```
Please provide a detailed summary of our conversation so far. Include:
1. Current Task: What are we working on?
2. Key Decisions Made: Important choices and their reasons
3. Files Modified: List of files read, created, or edited
4. Current State: Where we left off
5. Important Context: Any crucial information that should be preserved
```

The summary replaces all messages except the last 3.

---

## Comparison: Ours vs OpenCode

| Feature | Our Implementation | OpenCode |
|---------|-------------------|----------|
| **Prune Tool Outputs** | ✅ 40K protect, 10K min savings | ✅ Same |
| **AI Summary** | ✅ Single API call | ✅ Dedicated "compaction" agent |
| **Auto-Compact** | ✅ ON by default, triggers at 90% | ✅ Auto-triggers on overflow |
| **Pre-send Compact** | ✅ Auto-compacts at 80% before send | ❌ Not mentioned |
| **Manual Compact** | ✅ "Compact" button | ✅ `/compact` command |
| **Plan Mode** | ✅ Read-only exploration mode | ✅ Planning agent |
| **Save Compacted** | ✅ Auto-saves after each message | ✅ Auto-saves |
| **Continue After** | ✅ Auto-continues after compact | ✅ Auto-continues if needed |
| **Stop Button** | ✅ Cancel processing mid-stream | ❌ Not mentioned |
| **Protected Tools** | ❌ Not implemented | ✅ "skill" tool protected |
| **Prune Marker** | ❌ Not implemented | ✅ `time.compacted` timestamp |

### What OpenCode Does Better

1. **Protected tools**: Some tools (like "skill") are never pruned
2. **Prune marker**: Marks pruned content with timestamp to avoid re-pruning

### What We Could Add

1. **Protected tools list**: Add `PRUNE_PROTECTED_TOOLS = ["semantic_search"]`
2. **Prune tracking**: Track what was pruned to avoid re-processing

---

## Usage

### Auto-Compact (Default - ON)
- **Auto-Compact checkbox is ON by default**
- At **80%** context: Pre-send compact (BEFORE sending to prevent overflow)
- At **90%** context: Post-response compact with auto-continue
- Shows: "🔄 Auto-compact triggered..." → "✅ Auto-compacted. Context now at X%" → "▶️ Auto-continuing..."

### Stop Button
- Click **Stop** during processing to cancel
- Shows: "⏹ Stop requested - will stop after current operation completes"
- Agent stops after current operation finishes

### Manual Compact
1. Click **"Compact"** button anytime
2. Wait for "Stage 1: Pruning..." and "Stage 2: Summarizing..."
3. Session auto-saves after compaction (no manual save needed)

### Plan Mode
1. Toggle **"Plan Mode"** ON
2. Agent will only READ/EXPLORE (no writes)
3. Agent creates implementation plan
4. Toggle OFF and send "execute plan" to proceed

### Context Status Colors
- **Green (< 75%)**: Normal
- **Orange (75-89%)**: Warning
- **Red (90%+)**: High - auto-compact triggers if enabled

---

## Files With Compact Feature

| File | Compact | Auto-Compact | Plan Mode | UI Fix |
|------|---------|--------------|-----------|--------|
| `compact/sagemaker_agent.py` | ✅ | ✅ (ON) | ✅ | ✅ |
| `compact_GCP/gemini_agent.py` | ✅ | ✅ (ON) | ✅ | ✅ |
| `complete/agent.ipynb` | ✅ | ✅ (ON) | ✅ | ✅ |

---

## Security (v2.3.0)

### Philosophy: Block Execution, Allow Code Generation

The agent runs in shared cloud environments (SageMaker, Colab, GCP Notebooks) that have IAM roles with broad permissions. Security blocks **execution** of dangerous operations but allows the agent to **generate code** for users to review and run themselves.

### Bash Restrictions (70+ patterns for AWS, 50+ for GCP)

| Category | Blocked Patterns | Reason |
|----------|-----------------|--------|
| **Cloud CLI** | `aws s3`, `aws dynamodb`, `aws iam`, `gcloud`, `gsutil` | Direct cloud resource access |
| **Network** | `curl http://`, `wget http://` (except pypi) | External data exfiltration |
| **System** | `rm -rf /`, `chmod 777`, `eval`, `crontab` | System damage |
| **Credentials** | `cat ~/.aws/`, `export AWS_`, `cat /etc/passwd` | Credential theft |

### Python Restrictions (40+ patterns)

| Category | Blocked Patterns | Reason |
|----------|-----------------|--------|
| **Cloud SDK** | `boto3.client('s3')`, `google.cloud.storage` | Direct cloud access |
| **Network** | `requests.get()` to external URLs | Data exfiltration |
| **Credentials** | `os.environ['AWS_']`, `open('.aws/credentials')` | Credential access |
| **System** | `subprocess.Popen(shell=True)`, `exec()`, `eval()` | Code injection |

### Path Restrictions

- `../../` - Path traversal blocked
- `/etc/`, `/root/`, `~/.aws/`, `~/.config/gcloud` - System/credential paths blocked
- Service account key files blocked

### What's ALLOWED

✅ Reading/writing files in workspace
✅ Running safe bash (ls, cat, grep, pip install)
✅ Creating documents (Word, Excel, PDF, charts, images)
✅ **Generating code** for blocked operations (user runs it themselves)

### Example: User Wants S3 Access

```
User: "Download file from s3://my-bucket/data.csv"
Agent: "I can't directly access S3, but here's the code for you to run:

import boto3
s3 = boto3.client('s3')
s3.download_file('my-bucket', 'data.csv', 'data.csv')
"
```

---

## Changelog

### v2.5.0 (January 2025)
- **Token Optimization**: Multiple techniques to reduce context usage
  - Protected tools: todo_write, todo_read, semantic_search never pruned
  - File read cache: Don't re-read same file (checks mtime)
  - File dedup: Skip if file already in context
  - Smart truncation: Show head + tail, skip middle
  - Diff-only edits: Compact edit output (line number + preview only)
- Estimated savings: 30-50% on file-heavy sessions

### v2.4.0 (January 2025)
- **Stop Button**: Cancel LLM processing mid-stream
- **Pre-send Compact**: Auto-compacts at 80% BEFORE sending (prevents mid-response overflow)
- **Auto-continue**: Automatically resumes after compact (OpenCode-style)
- **Keep Last 3**: Changed from 5 to 3 messages after compact (more space saved)
- UI: Stop button shows during processing, hides when done

### v2.3.1 (January 2025)
- **Bug Fix**: Token display now shows actual context window usage instead of cumulative API totals
  - Before: Display showed sum of all API calls (could exceed 200% incorrectly)
  - After: Display shows current message context (resets properly after compact)
- Display now shows "Context Window: X%" for actual context, "API Totals" for cumulative info

### v2.3.0 (January 2025)
- Added comprehensive security (70+ bash patterns, 40+ Python patterns)
- Philosophy: Block execution, allow code generation

### v2.2.0 (January 2025)
- Initial OpenCode-style compaction implementation
- Two-stage process: Prune + Summarize
- Auto-Compact ON by default at 90%

---

## Code Reference

### Compactor Class (lines 119-216 in sagemaker_agent.py)

```python
class Compactor:
    PRUNE_PROTECT_TOKENS = 40000  # Keep last 40K tokens
    PRUNE_MIN_SAVINGS = 10000     # Min tokens to save
    SUMMARY_TRIGGER_PERCENT = 0.80  # Trigger at 80%

    @classmethod
    def prune_tool_outputs(cls, messages, max_context):
        # Remove old tool outputs, keep recent 40K tokens
        ...

    @classmethod
    def create_summary_prompt(cls, messages):
        # Generate prompt for AI to summarize
        ...

    @classmethod
    def compact(cls, messages, summary):
        # Replace old messages with summary + last 5
        ...
```

### on_compact Handler

```python
def on_compact(b):
    # Stage 1: Prune
    pruned_msgs, tokens_saved = COMPACTOR.prune_tool_outputs(messages, max_tokens)

    # Stage 2: Summarize
    response = client.invoke(messages + [{"role": "user", "content": summary_prompt}])

    # Replace messages
    compacted = COMPACTOR.compact(messages, response.text)
    agent.messages = compacted
```

---

## Future Improvements

1. **Auto-compact on overflow** - Don't wait for user, auto-trigger at 95%
2. **Sliding window** - Keep context "marker" that moves forward through history
3. **Inception messages** - Critical context that survives all compactions
4. **Better summary prompt** - Include more structured output format

---

## References

- OpenCode compaction: `packages/opencode/src/session/compaction.ts`
- OpenCode config: `{ "compaction": { "auto": true, "prune": true } }`
- OpenCode agent: `packages/opencode/src/agent/prompt/compaction.txt`
