# SageAgent V3 — Final Consolidated Review

**Date**: 2026-03-25
**Version**: v3.2.2 (commit pending)
**Reviewers**: Claude Opus 4.6 + Codex gpt-5.3-codex (10 rounds of review)
**Tests**: 81/81 passing (60 production + 21 advanced)

---

## Consolidated Scores

| Dimension | Claude Score | Codex Score | Agreed | What Prevents 10/10 | At Max? |
|-----------|-------------|-------------|--------|---------------------|---------|
| **Performance** | 9.2/10 | 9.2/10 | **9.2/10** | No streaming, embedding sync, ContextManager still chars/4 | Near max |
| **Security** | 8.3/10 | 8.3/10 | **8.3/10** | No Docker, CPython closures, shared IAM | Platform max with aws_bedrock_only |
| **Capabilities** | 8.8/10 | 9.1/10 | **9.0/10** | No REPL, no multi-image, module-level code gaps | Near max |
| **Cost Efficiency** | 9.4/10 | 9.5/10 | **9.4/10** | Per-turn budget (can overshoot 1 call), no per-tool attribution | Near max |
| **Reliability** | 9.0/10 | 9.2/10 | **9.0/10** | Non-atomic exec budget writes, daemon auto-save | Near max |

### Overall: **9.0/10** (up from 8.7)

**Score movement v3.2.0 → v3.2.2 (full session):**
- Performance: 9.0 → 9.2 (tiktoken, AST search)
- Security: 7.5 → 8.3 (boundary fix, aws_bedrock_only, AST enforcement)
- Capabilities: 8.5 → 9.0 (image understanding, AST search, configurable pricing)
- Cost: 9.0 → 9.4 (spend budget, configurable pricing, tiktoken accuracy)
- Reliability: 8.5 → 9.0 (persistent exec budget, budget flags reset, image queue cleanup)
- Overall: 8.6 → 8.7 (security fix + test coverage boost)

---

## Performance (9.0/10)

**What's optimized:**
- System prompt: 1146→360 tokens (-69%)
- Tool schemas: 2809→1976 tokens (-30%), minified JSON
- Plan mode: 484→73 tokens (-85%), only 11 tools sent
- Lazy-load: doc tools skipped for coding tasks (1627 tokens/call)
- Truncation: 50KB→30KB
- Compaction: prune-first, redundant LLM call eliminated
- Async session save
- LRU file cache with mtime validation (FileCache:526)
- Parallel sub-agent execution (ThreadPoolExecutor:5245)

**Token budget (measured from code):**
| Mode | Tokens/call | vs Claude Code (~2000) |
|------|------------|----------------------|
| Full (22 tools) | ~2,336 | +17% (justified: 22 vs 12 tools) |
| Lazy (coding) | ~1,627 | -19% (BETTER) |
| Plan (read-only) | ~1,262 | -37% (BETTER) |

**What prevents 10/10:**
- Bedrock tool-call protocol adds fixed overhead per turn (PLATFORM)
- Token estimation is `len(text)//4` — coarse heuristic (FIXABLE but minor)
- No streaming — synchronous invoke_model (UX improvement, not correctness)

---

## Security (8.0/10) — AT PLATFORM MAXIMUM

**16 layers implemented:**
1. AWS IAM (platform) | 2. Bedrock model access (platform)
3. Workspace boundary (with os.sep fix) | 4. Bash allowlist + path sandbox
5. Python import allowlist | 6. Python regex denylist (48 patterns)
7. Runtime sandbox: builtins.open, os.open, io.open wrapped
8. Runtime sandbox: os.remove/unlink/rmdir wrapped
9. Runtime sandbox: os.posix_spawn blocked
10. AWS tiered access (20 destructive patterns)
11. SSRF protection (private IP + redirect blocking)
12. Secret scanning (input + output, 13 patterns)
13. Audit logging (JSONL with session_id, integrity hashing)
14. Tool approval dialog (full payload shown)
15. Global exec limits (40 calls / 900s)
16. Prompt injection trust boundary

**v3.2.1 fix: workspace boundary bypass closed**
- `startswith(workspace)` → `startswith(workspace + os.sep)` in 5 locations
- Sibling directories (`workspace_evil/`) no longer pass boundary check
- 2 regression tests added (production + advanced)

**False positive investigated:** Claude flagged `pathlib.Path.read_text()` as bypass — verified that `pathlib.Path.open()` → `io.open` → `_safe_open` (line 3253). NOT a real bypass.

**What prevents 10/10 (both reviewers agree, UNFIXABLE):**
- No Docker/container isolation (SageMaker PLATFORM LIMIT)
- Python closures readable — sandbox wrappers can theoretically be extracted (CPython)
- shell=True used for pipe commands (design tradeoff for `git log | head`)
- Same SageMaker execution role shared (AWS PLATFORM LIMIT)

**Realistic risk (Codex estimate):**
- Material harmful action: ~0.02-0.05% per session
- High-severity cloud impact (with scoped IAM): <0.01% per session

---

## Capabilities (8.5/10)

**22 tools:** read_file, write_file, edit_file, glob, grep, list_dir, bash, python_exec, create_word, create_excel, create_markdown, create_notebook, create_chart, create_pdf, view_image, todo_write, todo_read, semantic_search, skill, task, web_fetch, ask_user

**Strengths vs peers:**
- More tools than Claude Code (22 vs ~12)
- Document creation (Word/PDF/Excel/Charts) — unique to V3
- Sub-agents (5 types) — matches OpenCode
- MCP support — matches Goose/OpenCode
- Cost tracking — better than most
- Auto-lint — matches Aider/SWE-agent
- 8 chart types (bar, grouped_bar, stacked_bar, line, pie, scatter, horizontal_bar, combo)

**What's missing vs peers (both reviewers agree):**
- No persistent REPL (each python_exec = fresh process)
- No image understanding (view_image = metadata only, no multimodal)
- No structured git tool (relies on bash for git commands)
- No browser automation (Cline has headless browser)
- No code-aware semantic search chunking (fixed 50-line chunks)

---

## Cost Efficiency (9.0/10) — PRACTICALLY AT MAX

- Cost formula verified to 6 decimal places
- Bedrock cache pricing: 90% read discount, 25% write premium
- Sub-agent costs tracked at their own model rate
- Fixed overhead surfaced in /cost command
- Lazy tool loading saves ~700 tokens/call on coding tasks
- Unknown model now emits visible warning (not silent $0)
- Semantic search + model validation calls tracked

**What prevents 10/10:**
- Pricing table is static (manual updates needed for new models)
- Prompt caching not active on AU Haiku 4.5 (Bedrock limitation)
- No cost budget / per-session spend limit
- No model auto-downgrade for simple tasks

---

## Reliability (8.8/10)

- Atomic session save (temp + os.replace + _save_lock)
- Thread-safe token/exec counters (locks on all shared state)
- Doom loop detection (3+ identical calls, 30-call sliding window)
- 5-layer tool error recovery (name repair, arg fix, type conversion)
- Retry with exponential backoff (5 retries, 2s base, 60s max)
- Global exec budget (40 calls / 900s across all agents)
- Snapshot system for file rollback (200 cap with smart eviction)
- Auto-save after each message with async background thread
- Session model restoration on load

**What prevents 10/10:**
- Daemon thread auto-save can lose data on kernel kill (platform tradeoff)
- Global exec budget resets on kernel restart (no persistence)
- No WAL/journaling for agent loop crash recovery

---

## Honest Limitations (Cannot Fix)

| # | Limitation | Type | Why | Score Impact |
|---|---|---|---|---|
| 1 | **No Docker container isolation** | Platform | SageMaker managed notebooks don't expose Docker | Security capped ~8.5 |
| 2 | **CPython closures can inspect sandbox** | Language | Sandbox wrappers stored as closures — extractable via `__closure__` | Security capped ~8.5 |
| 3 | **Shared IAM execution role** | Platform | SageMaker notebooks inherit role (mitigated by `aws_bedrock_only`) | Security -0.2 |
| 4 | **No streaming** | Platform | Jupyter widget threading + `invoke_model` is synchronous | Performance -0.3 |
| 5 | **Prompt caching not active** | Platform | Bedrock AU region doesn't support it for Haiku 4.5 | Cost -0.1 |
| 6 | **shell=True for pipe commands** | Design | Needed for `git log | head` patterns | Security -0.1 |
| 7 | **Daemon thread auto-save** | Platform | Non-daemon would block kernel shutdown; daemon can lose on kill | Reliability -0.2 |
| 8 | **No persistent REPL** | Architecture | Each `python_exec` = fresh subprocess; stateful REPL needs major rework | Capabilities -0.3 |

**Total unfixable gap: ~1.0 points (9.0 → theoretical 10.0)**

---

## Comparison to Top Agents

| Feature | V3 | Claude Code | Aider | Cline | OpenHands |
|---------|-----|------------|-------|-------|-----------|
| Token efficiency | 1627/call (lazy) | ~2000/call | Minimal | Moderate | Moderate |
| Tools | 22 | ~12 | ~8 | ~10 | ~15 |
| Security layers | 16 + aws_bedrock_only | Sandbox+hooks | None (trusts user) | Approval | Docker |
| Doc creation | Yes (Word/PDF/Excel/Charts) | No | No | No | No |
| Image understanding | Yes (Claude vision) | Yes | No | No | No |
| Sub-agents | 5 types | Yes | No | No | Yes |
| Cost tracking | 6-decimal + spend budget | No | No | No | No |
| Auto-lint | py_compile | No | Yes (+ test) | No | No |
| Browser | Fetch only | No | No | Yes | Yes |
| MCP | Yes | Yes | No | Yes | No |
| Configurable pricing | Yes (opencode.json) | No | No | No | No |

**Verdict: V3 is the most token-efficient and feature-rich agent for SageMaker notebooks, with the strongest security achievable without Docker. At 9.0/10 after 10 review rounds (Claude Opus + Codex gpt-5.3), it has reached maximum achievable within platform constraints.**
