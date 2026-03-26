#!/bin/bash
# Codex auto-review hook for Claude Code
# Runs after Claude finishes a response. Only triggers when there are code changes.

export PATH="$HOME/.npm-global/bin:$PATH"

INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# Prevent infinite loop: if re-entering after a block, let Claude stop
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
if [ -z "$CWD" ]; then
  exit 0
fi

cd "$CWD" || exit 0

# Not a git repo? Skip
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi

# Get diff (staged + unstaged)
# For repos with commits, diff against HEAD
# For empty repos (no commits yet), diff against empty tree
if git rev-parse HEAD >/dev/null 2>&1; then
  DIFF=$(git diff HEAD 2>/dev/null)
else
  DIFF=$(git diff --cached 2>/dev/null)
  # Also check untracked files in empty repos
  UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null)
  if [ -n "$UNTRACKED" ]; then
    for f in $UNTRACKED; do
      DIFF="$DIFF
--- new file: $f ---
$(head -100 "$f")
"
    done
  fi
fi

# No code changes? Skip — this is just a chat
if [ -z "$DIFF" ]; then
  exit 0
fi

# Truncate large diffs to avoid token overload
DIFF=$(echo "$DIFF" | head -500)

# Build project context from available docs
CONTEXT=""

# Read CLAUDE.md if exists (project conventions)
if [ -f "$CWD/CLAUDE.md" ]; then
  CONTEXT="$CONTEXT
--- PROJECT CONVENTIONS (CLAUDE.md) ---
$(head -100 "$CWD/CLAUDE.md")
"
fi

# Read README if exists (project purpose)
if [ -f "$CWD/README.md" ]; then
  CONTEXT="$CONTEXT
--- PROJECT README ---
$(head -50 "$CWD/README.md")
"
fi

# Read any design docs if exists
for doc in "$CWD"/PS_Internal/course_design/*.md "$CWD"/docs/DESIGN.md "$CWD"/DESIGN.md; do
  if [ -f "$doc" ]; then
    CONTEXT="$CONTEXT
--- DESIGN DOC: $(basename "$doc") ---
$(head -80 "$doc")
"
    break  # only include first design doc to save tokens
  fi
done

# Read changelog if exists (recent changes for context)
for changelog in "$CWD"/PS_Internal/bug_fixes/V3_CHANGELOG.md "$CWD"/CHANGELOG.md "$CWD"/changelog.md; do
  if [ -f "$changelog" ]; then
    CONTEXT="$CONTEXT
--- RECENT CHANGELOG ---
$(head -50 "$changelog")
"
    break
  fi
done

# Recent git log for context (what's been happening)
RECENT_LOG=$(git log --oneline -10 2>/dev/null)
if [ -n "$RECENT_LOG" ]; then
  CONTEXT="$CONTEXT
--- RECENT COMMITS ---
$RECENT_LOG
"
fi

# Build the review prompt with context
PROMPT="You are a senior code reviewer. You have context about this project:

$CONTEXT

Review this git diff. Check for:
1. Bugs, logic errors, security issues
2. Does the change match the project's design and conventions?
3. For UI/HTML changes: layout issues, broken links, accessibility
4. For chatbot/app changes: does it match the intended behavior?
5. Missing error handling at system boundaries

Be concise. Only report real problems. If everything looks good, just say LGTM."

# Run Codex review in read-only sandbox
REVIEW=$(echo "$DIFF" | codex exec --full-auto -s read-only \
  "$PROMPT" \
  2>/dev/null)

# Feed review as informational context — Claude decides whether to act
if [ -n "$REVIEW" ] && ! echo "$REVIEW" | grep -qi "LGTM"; then
  jq -n --arg reason "Codex review (informational — use your judgment on whether to act):

$REVIEW" '{
    "decision": "block",
    "reason": $reason
  }'
  exit 0
fi

# Clean — let Claude stop
exit 0
