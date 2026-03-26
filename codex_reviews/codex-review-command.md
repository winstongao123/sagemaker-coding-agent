Run Codex CLI to review code in the current project.

## What to review

Determine what to review based on the user's argument:

1. **No argument or general instruction** (e.g., `/codex-review`, `/codex-review focus on security`):
   - Run `git diff HEAD` for uncommitted changes
   - If no diff, check untracked files with `git ls-files --others --exclude-standard`
   - If still nothing, tell user "no changes to review"

2. **User mentions specific files** (e.g., `/codex-review check pipeline.py`):
   - Read those files and send their full content to Codex (not just diff)

3. **User gives a custom instruction** (e.g., `/codex-review is this production ready?`):
   - Use git diff if available, otherwise read key project files
   - Pass the user's FULL instruction word-for-word as the review focus — do NOT summarize it

## Project context to read

ALWAYS read these before sending to Codex:
- CLAUDE.md (project conventions, first 100 lines)
- README.md (project purpose, first 50 lines)
- REQUIREMENTS_LOG.md (user's requirements history, last 50 lines — so Codex knows WHAT was requested)
- Design docs: DESIGN.md, docs/DESIGN.md, PS_Internal/course_design/*.md (first 80 lines each)
- Changelog: CHANGELOG.md, PS_Internal/bug_fixes/V3_CHANGELOG.md (first 50 lines)
- `git log --oneline -10` (recent commits)

## How to call Codex

### Step 1: SHOW the user what you're sending to Codex

Before running Codex, print a message like:

```
**Sending to Codex (gpt-5.3-codex):**
- Files: app.py, chat.html
- Focus: [user's instruction]
- Context: CLAUDE.md, README.md loaded
```

### Step 2: Save prompt to a temp file and run Codex

Write the full prompt to `/tmp/codex_prompt.txt`, then run:

```bash
export PATH="$HOME/.npm-global/bin:$PATH" && cd <PROJECT_DIR> && codex exec --full-auto -s read-only -m gpt-5.3-codex "$(cat /tmp/codex_prompt.txt)"
```

Key points:
- Run `cd` into the project directory so Codex can browse files itself
- Keep the prompt under 4000 chars — summarize context, don't dump entire docs
- If reviewing many files, tell Codex which files to check rather than piping all content
- For large diffs (>500 lines), split into multiple Codex calls by file group

The REVIEW_PROMPT should include:
- Brief project context (2-3 sentences, not full docs)
- List of files to check (Codex reads them itself)
- The user's FULL instruction word-for-word (NEVER summarize the user's request)
- Default checks: bugs, security, logic errors, design match, requirements match

### Step 3: SHOW the full Codex response

After Codex finishes, you MUST print the COMPLETE Codex response. Format it as:

```
---
**Codex Review Results (gpt-5.3-codex):**

[paste the ENTIRE codex output here, do not summarize or trim]
---
```

Then ask: "Want me to fix any of these issues?"

## IMPORTANT RULES
- ALWAYS use `-m gpt-5.3-codex` — NEVER change the model unless the user explicitly says to use a different one
- ALWAYS `cd` into the project directory so Codex can read files in its sandbox
- ALWAYS show what you sent to Codex BEFORE running it
- ALWAYS show the COMPLETE Codex response AFTER running it — NEVER summarize, trim, or paraphrase
- NEVER change or summarize the user's instruction — pass it word-for-word to Codex
- Do NOT add your own review on top — just show what Codex said
- If Codex found issues, ask the user if they want you to fix them
- For large reviews, split into multiple focused Codex calls rather than one huge call

## Examples
- `/codex-review` → review git diff
- `/codex-review focus on security` → review git diff with security focus
- `/codex-review check pipeline.py` → review that file
- `/codex-review is this production ready?` → review with that question
- `/codex-review use o3` → review with o3 model instead
