# Phase 2 Wave 2: V4 Section 4 (Lines 9000–12088) Line-by-Line Investigation

**Canonical Reference:** v4 chat.ipynb UI + sagemaker_agent.py:9735 create_chat_ui()
**Scope:** Chat UI rendering, all widgets, callbacks, slash commands, approval dialogs, status bar, token display
**v5 Target:** ui/chat_ui.py, ui/widgets.py, ui/diff_widget.py

---

## Executive Summary

V4 lines 9000–12088 ship a comprehensive chat UI with 2000 LOC covering:
- Markdown rendering (_render_assistant_markdown + _format_inline_md)
- Chat display with HTML scrolling (render_chat + render_todos)
- 16 slash commands (/cost /status /save /load /compact /clean /skill /verify /done /phase /revert /diffs /regression /checkpoint /context /auth)
- Approval + ask-user dialogs with timeout logic
- Model dropdown + sub-agent overrides
- Dark-mode toggle with live re-render
- Token + cost tracking display
- Budget slider + Auto-Compact checkbox
- Chat height adjustment slider
- Session management (save/load/new)
- Checkpoint system (/checkpoint create/restore/list)

**V5 Status:** CRITICAL SHIPPING GAPS
- V5 chat_ui.py is minimal MVP (~220 LOC), intentionally deferring Phase-11 scope
- NO markdown rendering, NO slash commands, NO model switcher, NO approval dialogs, NO session restore
- NO cost tracking display, NO chat height slider, NO sub-agent overrides

---

## Widget-by-Widget Audit Summary

| Category | Count | PRESENT | PARTIAL | MISSING | Status |
|----------|-------|---------|---------|---------|--------|
| Input/Output Buttons | 4 | 2 | 1 | 1 | **FAIL** |
| Chat Display & Rendering | 6 | 0 | 0 | 6 | **FAIL** |
| Slash Commands | 16 | 0 | 0 | 16 | **FAIL** |
| Approval Dialog | 12 | 0 | 0 | 12 | **FAIL** |
| Ask-User Dialog | 8 | 0 | 0 | 8 | **FAIL** |
| Status Bar Components | 8 | 0 | 0 | 8 | **FAIL** |
| Model Selector | 6 | 0 | 0 | 6 | **FAIL** |
| Parameter Controls | 9 | 0 | 1 | 8 | **FAIL** |
| Session Management | 8 | 0 | 0 | 8 | **FAIL** |
| Compaction Controls | 5 | 1 | 0 | 4 | **FAIL** |
| Dark Mode Support | 3 | 0 | 0 | 3 | **FAIL** |
| Cleanup | 2 | 0 | 0 | 2 | **FAIL** |
| **TOTAL** | **87** | **3** | **2** | **82** | **CRITICAL** |

---

## Critical Missing Widgets (v5.0.1 Blockers)

### Markdown Rendering (V4 9776–9922)
- **Missing:** _format_inline_md, _render_assistant_markdown
- **Impact:** Users see raw markdown instead of formatted tables/lists/code/headers
- **Severity:** HIGH — All agent output is unreadable

### Approval Dialog (V4 10046–10626)
- **Missing:** approval_output, approve_btn, approve_always_btn, deny_btn, request_approval()
- **Impact:** Agent can write arbitrary files without user oversight
- **Severity:** HIGH — Security requirement

### Token/Cost Display (V4 10025, 10377–10479)
- **Missing:** tokens_html, update_tokens_display()
- **Impact:** No visibility into cost; context overflow % hidden
- **Severity:** HIGH — Cost awareness

### Slash Commands (V4 10805–11310)
16 commands entirely missing:
- /skills, /skill use, /skill clear, /unskill, /skill suggestions, /skill apply, /skill reject
- /cost, /context, /status, /phase, /verify
- /checkpoint create/restore/list
- /diffs, /regression, /revert, /done

**Impact:** Skill workflow, cost tracking, session persistence all unreachable
**Severity:** HIGH — Core user workflows

### Model Selector (V4 10068–10298)
- **Missing:** model_dropdown, validate_model_connection, on_model_change
- **Impact:** Can't switch models at runtime; hardcoded to CONFIG.model_id
- **Severity:** HIGH — Multi-model flexibility lost

### Status Bar (V4 10023, 10308–10357)
- **Missing:** status_html, mode_html, update_mode_display()
- **Impact:** User can't see Plan Mode status, token usage, model availability
- **Severity:** HIGH — Operational visibility

### Session Persistence UI (V4 10077–11790)
- **Missing:** session_dropdown, session_name_input, load_btn, new_btn, on_save(), on_load()
- **Impact:** Can't resume sessions; cost tracking lost across sessions
- **Severity:** HIGH — Continuity

---

## What Breaks If Missing (Per Feature)

### Skill System
- Slash commands: /skills, /skill use, /skill clear, /unskill, /skill apply, /skill reject, /skill suggestions
- **Breaks:** User can't discover skills; auto-match can't be disabled; skill patches unreachable

### Cost Awareness
- Slash command: /cost
- Token display: tokens_html with breakdown (input, output, cache, cost per call)
- Context progress bar showing % used
- **Breaks:** No cost visibility; users don't know session is expensive until invoice arrives

### Session Management
- Buttons: Save, Load, New
- Slash commands: /checkpoint create/restore/list
- Auto-save callback after each message
- **Breaks:** Can't resume interrupted work; milestone tracking gone; multi-session continuity impossible

### Quality Gates
- Slash commands: /verify, /done, /regression, /diffs
- **Breaks:** Adversarial testing workflow disabled; ship-gate (simplify + verify + gate) inaccessible

### Dark Mode
- Checkbox + callback (on_dark_mode_change)
- Live re-render of chat HTML with theme colors
- **Breaks:** Fixed light colors; unreadable on dark notebooks; no theme preference

### Approval (Security)
- Dialog box with tool input preview
- Approve / Always / Deny buttons
- Timeout logic (5 min max)
- **Breaks:** Agent can call bash without permission; write_file unrestricted

---

## Implementation Gaps Detail

**Chat Display (6 missing components):**
1. _format_inline_md (inline code/bold/italic)
2. _render_assistant_markdown (table/list/code block parsing)
3. render_chat() (message history to HTML)
4. Tool result <details> (expandable blocks)
5. Inline image [INLINE_IMAGE:base64] support
6. CSS flex-direction column-reverse for auto-scroll

**Session Management (8 missing):**
1. session_dropdown (load UI)
2. session_name_input (save naming)
3. load_btn, new_btn, save_btn
4. on_save(), on_load(), on_new() callbacks
5. Auto-save per message (threading)

**Status Bar (8 missing):**
1. status_html (● Ready / Processing)
2. mode_html (Plan/Thinking/Auth/Approval state)
3. tokens_html (full token breakdown)
4. update_mode_display()
5. update_tokens_display()
6. Context % bar
7. Budget % bar
8. Cost tracking per turn

**Parameters (8 missing):**
1. temp_slider (0.0–1.0)
2. chat_height_slider (200–1200px)
3. dark_mode_checkbox + callback
4. approval_checkbox
5. budget_input (cost limit display)
6. Callbacks: on_temp_change, on_dark_mode_change, on_approval_toggle

---

## Conclusion

**V4 vs. V5 Shipped:**
- V4: 2000 LOC, 87 widgets, full-featured notebook UI
- V5: 220 LOC, 3 widgets (Send/Stop/Clear), MVP only

**V5 can send messages and see thinking budget. Everything else is missing.**

**Tier-1 (v5.0.1 ship-blockers):**
1. Approval dialog — security
2. Token/cost display — transparency
3. Markdown rendering — readability
4. Slash commands (/cost, /status, /skill, /save, /load) — workflow
5. Model switcher — flexibility

**Effort:** ~1500 LOC to achieve parity.

