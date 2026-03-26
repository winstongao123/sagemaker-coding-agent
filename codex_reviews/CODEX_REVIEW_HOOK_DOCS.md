# Codex Auto-Review Hook for Claude Code

## What It Does

Automatically sends Claude Code's changes to OpenAI Codex CLI for independent code review. No manual triggers — it runs whenever Claude edits code.

## How It Works

```
Claude Code finishes a response
        ↓
Stop event fires (built into Claude Code app)
        ↓
codex-review.sh runs automatically
        ↓
Checks: git diff HEAD
        ↓
No changes? ──→ Exit (zero cost, instant)
        ↓
Has changes? ──→ Reads project context + sends diff to Codex
        ↓
Codex reviews in read-only sandbox
        ↓
LGTM? ──→ Claude stops normally
        ↓
Issues found? ──→ Blocks Claude, feeds review back
        ↓
Claude reads Codex feedback and fixes issues
        ↓
Loop guard prevents infinite cycles
```

## Key Concept: Claude Doesn't Know

Claude (the AI) has no involvement in this process. The **Claude Code application** (the harness) runs the hook. It's like a git pre-commit hook — triggered by the system, not by the AI.

- Claude doesn't run `git diff`
- Claude doesn't call Codex
- Claude only sees Codex feedback IF issues are found (via the block mechanism)

## Step-by-Step Walkthrough

### Example 1: General chat (NO review happens)

```
You type: "what is React?"
        ↓
Claude (AI) responds: "React is a JavaScript library..."
        ↓
Claude Code (app, NOT AI) fires Stop event
        ↓
App sees settings.json says: "on Stop, run codex-review.sh"
        ↓
App runs codex-review.sh
        ↓
Script runs bash command: git diff HEAD
        ↓
Result: empty (no files on disk changed)
        ↓
Script exits immediately. Nothing happens. Zero cost.
```

### Example 2: Code editing (review happens)

```
You type: "fix the bug in app.py"
        ↓
Claude (AI) edits app.py → file saved to disk
        ↓
Claude responds: "I've fixed the bug"
        ↓
Claude Code (app, NOT AI) fires Stop event
        ↓
App sees settings.json says: "on Stop, run codex-review.sh"
        ↓
App runs codex-review.sh
        ↓
Script runs bash command: git diff HEAD
        ↓
Result: shows app.py changes (file on disk differs from last commit)
        ↓
Script reads project docs (CLAUDE.md, README, design docs, changelog)
        ↓
Script runs: echo "$DIFF" | codex exec --full-auto -s read-only "review this..."
        ↓
Codex reviews the diff
        ↓
LGTM → Claude stops normally
Issues → Claude gets feedback, fixes them
```

### How it knows "coding" vs "chatting"

`git diff HEAD` checks **files on disk** vs the last git commit. It doesn't read Claude's message or understand what Claude said. It's purely filesystem-based:

- Claude edited a file → file on disk changed → `git diff` has output → review triggers
- Claude only chatted → no files changed → `git diff` is empty → script exits

### Who does what

```
┌─────────────────┐
│   You (human)    │ ← types a request, does nothing else
└────────┬────────┘
         ↓
┌─────────────────┐
│  Claude (AI)     │ ← responds / edits files. Has NO idea the hook exists
└────────┬────────┘
         ↓
┌─────────────────┐
│ Claude Code (app)│ ← fires Stop event, runs the script. NOT the AI.
└────────┬────────┘
         ↓
┌─────────────────┐
│ codex-review.sh  │ ← bash script. Runs git diff, reads docs, calls Codex
└────────┬────────┘
         ↓
┌─────────────────┐
│  Codex CLI       │ ← reviews the diff, returns LGTM or issues
└─────────────────┘
```

### The wiring: settings.json

The Claude Code app knows to run the script because of this config:

```json
"hooks": {
  "Stop": [           ←  "when Claude finishes a response..."
    {
      "hooks": [
        {
          "command": "$HOME/.claude/hooks/codex-review.sh"   ← "...run this script"
        }
      ]
    }
  ]
}
```

Same concept as other systems:

| System | Config file | Trigger | Runs |
|--------|------------|---------|------|
| Git hook | `.git/hooks/pre-commit` | You run `git commit` | Git runs the script |
| Cron job | `crontab` | Clock hits schedule | OS runs the script |
| **This setup** | `settings.json` | Claude finishes responding | Claude Code app runs the script |

## Files

| File | Purpose |
|------|---------|
| `~/.claude/hooks/codex-review.sh` | The hook script |
| `~/.claude/settings.json` | Registers the hook on the `Stop` event |

## Settings Configuration

In `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/codex-review.sh",
            "timeout": 120000,
            "statusMessage": "Codex reviewing changes..."
          }
        ]
      }
    ]
  }
}
```

- **type: command** — runs a shell script
- **timeout: 120000** — 2 minute max (review usually takes 10-30s)
- **statusMessage** — shows "Codex reviewing changes..." in the status bar

## What Context Codex Receives

The script reads project docs from disk before calling Codex. Always fresh, never stale.

| Source | Command | What It Provides |
|--------|---------|-----------------|
| `CLAUDE.md` | `head -100` | Project conventions and rules |
| `README.md` | `head -50` | What the project is about |
| Design docs | `head -80` | How things should work (checks `PS_Internal/course_design/`, `docs/DESIGN.md`, `DESIGN.md`) |
| Changelog | `head -50` | Recent changes (checks `PS_Internal/bug_fixes/V3_CHANGELOG.md`, `CHANGELOG.md`) |
| Git log | `git log --oneline -10` | Last 10 commits for context |
| Git diff | `git diff HEAD` (max 500 lines) | The actual code changes to review |

## What Codex Checks

1. Bugs, logic errors, security issues
2. Does the change match the project's design and conventions?
3. For UI/HTML changes: layout issues, broken links, accessibility
4. For chatbot/app changes: does it match intended behavior
5. Missing error handling at system boundaries

## Important: Open the Right Folder

The hook uses the VS Code window's working directory (`cwd`). For it to work:

- **Open the git repo folder directly** in VS Code (`File → Open Folder → pick the repo`)
- Each VS Code window = one project = one isolated reviewer
- Opening `~/Documents` won't work (not a git repo)

```
Window 1: Open ~/Documents/Github/PDF/          → Codex reviews PDF only
Window 2: Open ~/Documents/Github/Arcsage/       → Codex reviews Arcsage only
Window 3: Open ~/Documents/                      → No review (not a git repo)
```

Multiple Claude Code sessions in different windows each get their own independent review.

## When It Does NOT Run

- General discussion (no code changes = no git diff = skip)
- Not inside a git repo (skip)
- VS Code opened on a non-git folder like `~/Documents` (skip)
- Re-entry after a block (loop guard — `stop_hook_active: true` = skip)

## Loop Guard

Without protection, this could loop forever:

```
Claude edits → Codex finds issue → Claude fixes → Codex finds new issue → ...
```

The guard: when Claude is re-entering after being blocked (`stop_hook_active: true`), the hook exits immediately. This means **one review cycle per Claude response** — Codex reviews once, Claude fixes, done.

## Codex CLI Flags

```bash
codex exec --full-auto -s read-only "prompt..."
```

| Flag | Purpose |
|------|---------|
| `exec` | Non-interactive, one-shot (no session) |
| `--full-auto` | No approval prompts |
| `-s read-only` | Sandbox: Codex can only read, never modify your code |

## Prerequisites

- **Codex CLI**: `npm install -g @openai/codex`
- **Codex auth**: `codex login` (one-time, uses OpenAI subscription)
- **jq**: `brew install jq` (JSON parsing in the script)
- **PATH**: `~/.npm-global/bin` must be in PATH (set in `~/.zshrc`)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Hook doesn't fire | Restart Claude Code session (hooks load at startup) |
| "codex not found" | Check PATH includes `~/.npm-global/bin` |
| Codex auth expired | Run `codex login` again |
| Review takes too long | Large diff — script truncates at 500 lines |
| Hook runs on chat | Shouldn't — check `git diff HEAD` returns empty |
| Infinite loop | Loop guard handles this — check `stop_hook_active` logic |

## Cost

- **General chat**: Zero Codex calls
- **Code changes**: 1 Codex call per Claude response (uses your OpenAI subscription)
- **Context reading**: Free (local file reads)
