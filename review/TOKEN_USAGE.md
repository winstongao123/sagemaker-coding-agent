# Token Usage Guide

## System Prompt Size

The system prompt (`prompts/system.txt`) uses approximately:

| Section | Tokens (approx) |
|---------|-----------------|
| Tone and style | ~150 |
| Professional objectivity | ~100 |
| Task Management + examples | ~400 |
| Doing tasks | ~150 |
| Tool usage policy | ~200 |
| Code references | ~100 |
| Critical rules | ~100 |
| Security context | ~150 |
| Available tools list | ~200 |
| **Total System Prompt** | **~1,500 tokens** |

---

## Per-Request Token Usage

### Typical Conversation Turn

| Component | Input Tokens | Output Tokens |
|-----------|-------------|---------------|
| System prompt | 1,500 | 0 |
| User message | 50-200 | 0 |
| Conversation history | 500-5,000 | 0 |
| Tool definitions | 800 | 0 |
| Assistant response | 0 | 200-1,000 |
| **Per Turn (typical)** | **3,000-7,000** | **200-1,000** |

### Tool Calls

| Tool | Input Added | Output Added |
|------|-------------|--------------|
| read_file | +50 | +500-5,000 (file content) |
| write_file | +200 | +50 |
| edit_file | +200 | +50 |
| grep | +50 | +200-2,000 |
| glob | +30 | +100-500 |
| bash | +100 | +100-2,000 |
| view_image | +50 | +1,000-5,000 (base64) |

---

## Daily Token Estimates

### Light Use (Testing/Development)
- 20 conversations/day
- 5 turns per conversation
- ~5,000 tokens per turn

**Estimate: ~500,000 tokens/day**

### Medium Use (Active Development)
- 50 conversations/day
- 10 turns per conversation
- ~7,000 tokens per turn

**Estimate: ~3,500,000 tokens/day**

### Heavy Use (Production)
- 100+ conversations/day
- 15+ turns per conversation
- Complex multi-file operations

**Estimate: ~10,000,000+ tokens/day**

---

## Bedrock Pricing (Sydney Region)

### Claude 3.5 Sonnet
| Type | Price |
|------|-------|
| Input tokens | $0.003 / 1K tokens |
| Output tokens | $0.015 / 1K tokens |

### Claude 3 Haiku (Cheaper)
| Type | Price |
|------|-------|
| Input tokens | $0.00025 / 1K tokens |
| Output tokens | $0.00125 / 1K tokens |

### Daily Cost Estimates

| Usage Level | Claude Sonnet | Claude Haiku |
|-------------|---------------|--------------|
| Light (500K tokens) | ~$4/day | ~$0.40/day |
| Medium (3.5M tokens) | ~$28/day | ~$2.80/day |
| Heavy (10M tokens) | ~$80/day | ~$8/day |

---

## Context Window Management

### Claude 3.5 Sonnet Context
- **Max context:** 200,000 tokens
- **Recommended max:** 160,000 tokens (80%)

### Warning Levels

| Level | Tokens | Action |
|-------|--------|--------|
| Normal | 0-160K | Continue normally |
| Warning | 160K (80%) | Save checkpoint |
| High | 180K (90%) | Alert user |
| Critical | 190K (95%) | Strong warning |
| Max | 200K | Context compaction |

### What Happens at Limits

1. **At 80% (160K tokens)**
   - Checkpoint saved to `_temp_context.md`
   - Includes: task, data, last 3 messages, next steps

2. **At 95% (190K tokens)**
   - Strong warning displayed
   - Recommend starting new session

3. **At 100% (200K tokens)**
   - Automatic context compaction
   - Old messages summarized

---

## Token Optimization Tips

### Reduce Input Tokens

1. **Use targeted file reads**
   ```
   "Read lines 50-100 of config.py"
   # Instead of: "Read config.py"
   ```

2. **Use specific glob patterns**
   ```
   "Find *.py in src/ folder"
   # Instead of: "Find all Python files"
   ```

3. **Clear session when done**
   - Start new session for unrelated tasks
   - Saves context from building up

### Reduce Output Tokens

1. **Be specific in requests**
   ```
   "List only .py files"
   # Instead of: "List all files"
   ```

2. **Ask for summaries**
   ```
   "Summarize the error, don't show full stack trace"
   ```

---

## Quota Recommendations

### For Development (New Account)
Request from AWS:
- Tokens per minute: **10,000**
- Tokens per day: **1,000,000**
- Requests per minute: **100**

### For Production
Request from AWS:
- Tokens per minute: **100,000**
- Tokens per day: **10,000,000**
- Requests per minute: **1,000**

---

## Monitoring Token Usage

### In Code
```python
# After each response
response = client.chat(messages, system, tools)
print(f"Input tokens: {response.usage.get('input_tokens', 0)}")
print(f"Output tokens: {response.usage.get('output_tokens', 0)}")
```

### In AWS Console
1. Go to CloudWatch
2. Find Bedrock metrics
3. Monitor: `InvocationCount`, `InputTokens`, `OutputTokens`

---

## System Prompt Token Breakdown

```
prompts/system.txt approximate token count:

# Tone and style section
"Only use emojis if..."                    ~50 tokens
"Your output will be displayed..."         ~40 tokens
"Output text to communicate..."            ~30 tokens
"NEVER create files..."                    ~30 tokens

# Professional objectivity section         ~100 tokens

# Task Management section
"You have access to todo_write..."         ~80 tokens
Example 1 (build/fix errors)               ~150 tokens
Example 2 (metrics feature)                ~150 tokens

# Doing tasks section                      ~150 tokens

# Tool usage policy section                ~200 tokens

# Code references section                  ~100 tokens

# Critical rules section                   ~100 tokens

# Security context section                 ~150 tokens

# Available tools list                     ~200 tokens

TOTAL: ~1,500 tokens
```

This system prompt is sent with EVERY request, so optimizing it can save tokens.
