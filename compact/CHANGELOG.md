# Changelog - SageMaker Coding Agent v2.8.0

## v2.8.0 - Allowlist Security Model

### bash: Command Allowlist + Conditional shell=True (Critical)

| What | Details |
|------|---------|
| **Problem** | `shell=True` with regex denylist was fundamentally bypassable. Obfuscated commands (`p''ython`, `$'\x63\x75\x72\x6c'`, hex escapes) could evade all patterns. |
| **Fix** | **3-layer validation**: (1) Extract base command from input, check against `ALLOWED_COMMANDS` allowlist (~50 safe commands: git, ls, pip, python, etc.). (2) Denylist patterns as second layer for dangerous arguments. (3) Network command blocking. For simple commands (no pipes/redirects), uses `shlex.split()` without `shell=True`. For pipe/redirect commands, `shell=True` is used but only after allowlist validation. |
| **Impact** | Unknown commands are rejected by default. The denylist is now defense-in-depth, not the primary control. |

### python_exec: AST Import Validation + Runtime Import Hook (High)

| What | Details |
|------|---------|
| **Problem** | Regex-only validation was bypassable via `__import__('subp'+'rocess')`, `getattr()`, `exec(bytes(...).decode())`, etc. |
| **Fix** | **3-layer validation**: (1) Regex denylist for obfuscation patterns. (2) AST parsing walks the code tree and blocks `import` statements for dangerous modules (`subprocess`, `socket`, `requests`, `boto3`, etc.). (3) Runtime import hook (`_PYTHON_EXEC_PREAMBLE`) prepended to all executed code - overrides `builtins.__import__` to block dangerous modules even from dynamic imports at runtime. |
| **Blocked modules** | `subprocess`, `socket`, `http`, `urllib`, `urllib3`, `requests`, `httpx`, `aiohttp`, `asyncio`, `ctypes`, `cffi`, `pickle`, `shelve`, `marshal`, `importlib`, `multiprocessing`, `concurrent`, `signal`, `boto3`, `botocore`, `shlex`. |
| **Allowed modules** | Standard library safe modules (math, json, re, collections, etc.), data science (numpy, pandas, scipy, sklearn, matplotlib), document creation (openpyxl, docx, PIL, reportlab). |

### "Approve Always" Scoped to Low-Risk Tools (High)

| What | Details |
|------|---------|
| **Problem** | One "Always" click on `bash` auto-approved all future bash commands regardless of arguments. Approving `bash ls` implicitly approved `bash rm -rf /`. |
| **Fix** | `bash` and `python_exec` are now marked as `HIGH_RISK_TOOLS`. For these: (1) "Always" button is hidden in the approval dialog. (2) Every invocation requires explicit approval with full argument display. (3) A "[HIGH RISK - review carefully]" label is shown. Low-risk tools (write_file, create_word, etc.) still support "Always" approval. |

---

## v2.7.0 - Final Security Hardening

### python_exec Subprocess Bypass (High)

| What | Details |
|------|---------|
| **Problem** | Only `subprocess.*shell=True` was blocked. `subprocess.run()`, `Popen()`, `call()`, `check_output()`, `check_call()` without `shell=True` were unblocked. Also missing: `httpx`, `aiohttp`, `urllib3`, and EC2 metadata endpoint `169.254.169.254`. |
| **Impact** | Agent-generated Python code could spawn arbitrary processes and make outbound HTTP requests, bypassing all command filtering and network restrictions. |
| **Fix** | Added 5 new `DANGEROUS_PYTHON` patterns: `subprocess.(run|Popen|call|check_output|check_call)`, `httpx.*`, `aiohttp.*`, `urllib3.*`, `169.254.169.254`. |

### Stop Button Now Kills Subprocesses (Medium)

| What | Details |
|------|---------|
| **Problem** | Stop only set a flag checked between agent turns. Running `bash` or `python_exec` subprocesses continued until their own timeout. |
| **Impact** | Long-running commands (e.g., `pip install`, infinite loops) could not be cancelled. |
| **Fix** | `tool_bash` and `tool_python_exec` now use `Popen` with a module-level `_active_process` reference protected by `_active_process_lock`. Stop handler calls `_kill_active_process()` to terminate the running subprocess immediately. |

### Security Overclaims in Prompt (Medium)

| What | Details |
|------|---------|
| **Problem** | SYSTEM_PROMPT claimed "immutable audit trail" but audit is just a local append-only JSON file with no integrity protection. |
| **Fix** | Changed to "append-only audit trail (local file)" - accurate description. |

### Plan Mode Tool List Mismatch (Low)

| What | Details |
|------|---------|
| **Problem** | PLAN_MODE_PROMPT listed only `read_file, glob, grep, list_dir, todo_write, todo_read` as allowed, but `PLAN_MODE_ALLOWED_TOOLS` also included `semantic_search` and `view_image`. |
| **Fix** | Updated prompt to list all allowed tools: added `semantic_search, view_image`. |

---

## v2.6.0 - Comprehensive Audit & Refinement

### Critical Bug Fixes

| Fix | Problem | Impact |
|-----|---------|--------|
| **Session auto-save** | Used wrong field names (`name`, `created`, `model` instead of `title`, `created_at`, `metadata`). Silent `except: pass` hid the TypeError. | Sessions never saved. All conversation history lost on restart. |
| **Compaction mutation** | `prune_tool_outputs()` used shallow copy (`m.copy()`) but mutated nested items, corrupting original message history even when pruning was abandoned. | Random message corruption during context management. |
| **Global _TODOS sync** | `render_todos()` assigned `_TODOS = ui_state["todos"]` without `global` declaration, creating a local variable. | Todo list never synced from UI back to global state. |
| **File cache after edit** | `edit_file` updated cache but didn't clear `_in_context` flag. Subsequent `read_file` returned "already in context" instead of showing edited content. | Users couldn't see their own edits. |
| **Session title overwrite** | Autosave used `session_name_input.value` which was already cleared, falling back to generic `session_<id>`. | Custom session names replaced with generic IDs after first message. |

### Security Hardening

| Fix | Vulnerability | Before | After |
|-----|---------------|--------|-------|
| **Path validation** | 8 tools (glob, grep, create_word, create_excel, create_markdown, create_chart, create_pdf, view_image, semantic_search) had no workspace boundary check. | Could write/read outside workspace with absolute paths. | All file-based tools now call `SECURITY.validate_path()`. |
| **Approval enabled** | All tools had `needs_approval=False` in registry. Approval dialog was dead code. | Write/exec operations ran without user consent. | `write_file`, `edit_file`, `bash`, `python_exec`, and all create_* tools now require approval. "Always" button works per-tool per-session. |
| **python_exec sandbox** | Inherited full `os.environ` including AWS credentials, tokens, passwords. | Agent code could access IAM role credentials. | Env vars containing SECRET, TOKEN, PASSWORD, CREDENTIAL, or AWS_*_KEY stripped. |
| **bash env leak** | Same full env inheritance. | Same credential exposure. | Same filtering applied. |
| **XSS in tool names** | `tool_name` from LLM inserted into HTML unescaped. | LLM could inject `<script>` via tool name. | `escape_html(tool_name)` applied. |
| **Shell expansion** | Command substitution `$(aws s3 ls)` and backtick `` `aws s3 ls` `` bypassed pattern matching. | AWS CLI accessible via variable expansion. | Added blocking patterns for `$(...)` and backtick substitution. |
| **Secret detection** | Missing Anthropic API keys (`sk-ant-*`) and bare AWS key IDs (`AKIA*`). | Credentials could be written to files undetected. | 3 new patterns added. |
| **Session load** | `Session(**data)` crashed on extra/unknown fields in JSON. | Corrupted session files caused load failures. | Filters to known fields before constructing. |

### Architecture Improvements

| Change | Why |
|--------|-----|
| **Single model source** | `BEDROCK_MODELS` in `sagemaker_agent.py` is now the single source of truth. `chat.ipynb` imports it via `from sagemaker_agent import BEDROCK_MODELS`. Previously two duplicate lists had to be manually synced. |
| **Compaction deep copy** | `copy.deepcopy(messages)` ensures originals are never mutated. Tool results are collected from the copy, not the original. |
| **Stop button works** | Agent class now accepts `on_stop_check` callback. Checked at top of each turn and before each tool execution. UI's `stop_requested` flag is wired through. |
| **"Always" approve** | `on_approve_always` now stores the tool name in `ui_state["always_allow"]`. `request_approval` checks this set before prompting. |
| **Audit model changes** | Switching models via dropdown now writes an audit log entry with old/new model IDs. |

### Prompt Upgrade

Expanded `SYSTEM_PROMPT` from ~30 to ~50 lines with guidance from OpenCode and Anthropic best practices:
- Professional objectivity (no hollow validation, no time estimates)
- Code conventions (match surrounding style, minimal changes)
- Investigation-first approach (read before editing, grep before reading)
- Error recovery (don't retry failed tool calls, adapt approach)
- Full document/chart tool documentation (create_chart, create_pdf)
- Security awareness section

### Credential Handling

Reverted `BedrockClient.__init__` and `SemanticSearch._ensure_client` from the `botocore.session.Session()` private-API hack back to standard `boto3.client()`, which handles credential refresh automatically via the default credential chain.

---

## Files Modified

- `compact/sagemaker_agent.py` - All code changes (single-file architecture)
- `compact/sagemaker_agent.md` - Byte-identical copy of .py
- `compact/chat.ipynb` - Now imports BEDROCK_MODELS from sagemaker_agent
- `compact/chat.md` - Markdown representation of chat.ipynb
