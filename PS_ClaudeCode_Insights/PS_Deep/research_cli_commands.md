# CLAUDE CODE CLI, COMMANDS, SKILLS & UI SYSTEMS

## 1. CLI IMPLEMENTATION (src/cli/)

### Key Files
- **cli/print.ts** (218KB) — Output printing, ANSI colors, NDJSON, structured logging
- **cli/structuredIO.ts** — Structured I/O for remote/bridge mode
- **cli/remoteIO.ts** — Remote I/O for mobile/web clients
- **cli/handlers/** — auth.ts (OAuth), mcp.tsx (MCP servers), plugins.ts, util.tsx
- **cli/update.ts** — Auto-update checking

---

## 2. COMMANDS SYSTEM (90+ Commands)

### Command Types
- **local** — Execute synchronously, return text
- **local-jsx** — Render Ink UI components
- **prompt** — Send text to model as skills

### Command Discovery Pipeline
1. Bundled skills (compiled into binary)
2. Built-in plugin skills
3. Skill directory commands (~/.claude/skills/ and .claude/skills/)
4. Workflow commands (if enabled)
5. Plugin commands
6. Built-in commands

### Complete Command List

**Core Session:** /clear, /compact, /resume, /session, /cost, /usage, /stats, /rename, /rewind

**Configuration:** /config, /keybindings, /theme, /color, /model, /effort, /fast, /privacy-settings, /hooks, /permissions

**Development:** /diff, /review, /ultrareview, /security-review, /branch, /plan

**Files/Tasks:** /add-dir, /files, /tasks, /tag, /export, /copy

**Integrations:** /install-github-app, /install-slack-app, /mcp, /plugin, /reload-plugins

**Productivity:** /btw, /help, /vision, /context, /memory, /summary

**Editor:** /ide, /desktop, /chrome, /mobile

**User:** /feedback, /login, /logout, /init, /doctor, /skills, /upgrade, /stickers

**Advanced:** /vim, /voice, /agents, /remote-control, /statusline

**Feature-Gated:** /brief (KAIROS), /assistant (KAIROS), /proactive, /force-snip (HISTORY_SNIP), /workflows, /ultraplan, /buddy, /fork, /peers

**Internal:** /commit, /init-verifiers, /backfill-sessions, /good-claude, /issue, /version, /bridge-kick, /env, /debug-tool-call, /mock-limits, /heapdump

### Remote Mode Safety
- REMOTE_SAFE_COMMANDS: session, exit, clear, help, theme, color, vim, cost, usage, copy, btw, feedback, plan, keybindings, statusline, stickers, mobile
- BRIDGE_SAFE_COMMANDS: compact, clear, cost, summary, files
- Prompt-type commands always safe, local-jsx blocked from bridge

---

## 3. SKILLS SYSTEM (src/skills/)

### Skill Types by Source
- User skills: ~/.claude/skills/*.md
- Project skills: .claude/skills/*.md
- Bundled skills: Registered programmatically
- Plugin skills: From installed plugins
- MCP skills: From MCP servers

### Skill Frontmatter
```yaml
---
name: Custom Name
description: What this skill does
whenToUse: When to invoke
argumentHint: <args>
model: claude-3-opus
allowedTools: [read, bash]
hooks: { pre-execution: [...] }
effort: high
context: inline | fork
---
```

### Skill Lifecycle
Discovery → Parsing → Validation → Registration → Invocation → Execution

---

## 4. UI & RENDERING (Ink Framework)

### Key Components
- **ink.ts** — Box, Text, Button, Link, Newline, Spacer, RawAnsi
- **Hooks:** useApp(), useInput(), useStdin(), useSelection(), useTerminalViewport(), useAnimationFrame()
- **screens/REPL.tsx** (900KB) — Main chat interface
- **components/** — 200+ UI components
- **interactiveHelpers.tsx** — showDialog(), showSetupDialog(), exitWithError()
- **dialogLaunchers.tsx** — 30+ typed dialog launch wrappers

---

## 5. KEYBINDING SYSTEM (120+ Bindings)

### Contexts
- **Global (13):** ctrl+c, ctrl+d, ctrl+l, ctrl+t, ctrl+o, ctrl+r, ctrl+shift+f/p
- **Chat (20):** escape, enter, up/down, shift+tab, meta+p/o/t, ctrl+x ctrl+k, ctrl+s
- **Autocomplete (4):** tab, escape, up/down
- **Settings (8):** escape, up/down, k/j, space, enter, /
- **Confirmation (8):** y/enter, n/escape, up/down, tab, space, ctrl+e/d
- **Transcript, HistorySearch, Task, Scroll, Help, Attachments, Footer, MessageSelector, MessageActions, DiffDialog, ModelPicker, Select, Plugin** — additional context-specific bindings

### Customization
- File: ~/.claude/keybindings.json
- Chord support: meta+k meta+c
- Reserved keys: ctrl+c, ctrl+d cannot be rebound
- Platform-specific: Windows VT mode handling

---

## 6. VIM MODE
Toggle via /vim command. Vim-style motion keys and operators in chat input.

## 7. VOICE INPUT
Push-to-talk (space key). Feature-gated (VOICE_MODE). Claude AI subscriber feature.

## 8. OUTPUT STYLES
Customizable via .claude/output-styles/*.md with frontmatter styling rules.
