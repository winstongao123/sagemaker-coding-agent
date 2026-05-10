---
name: html
description: Use when the user asks for a presentation, design doc, flowchart, code-explanation, or architecture HTML deliverable. Brings reference templates (tabbed design, presentation slides, flowchart pages) and a screenshot-iteration workflow that substitutes for Playwright on SageMaker.
auto_trigger: false
triggers: []
---

## When to use this skill

Activate via `/skill use html` when the user asks for any of these deliverables:
- **Presentation** (single-page slide-style HTML, multiple sections, visual hierarchy)
- **Design document** (tabbed layout, sidebar nav, decision logs, status tables)
- **Flowchart page** (Mermaid diagrams as the centrepiece, business-rule annotations)
- **Code explanation** (side-by-side code + walkthrough, file-by-file deep dives)
- **Architecture report** (layers, stats, comparisons, anti-pattern callouts)

Do NOT activate for: README files, plain Markdown docs, Word/PDF reports (use `report` skill), or .ipynb notebooks (use `notebook_edit`).

---

## Reference templates (read on demand, not all at once)

Three templates ship with this skill at `skills/html/references/`. Each represents one of the user's canonical patterns. When the user's request matches one, **`read_file` ONLY that reference** before writing — do not load all three.

| Reference | When to read it | Notable structure |
|---|---|---|
| `references/tabbed_design.html` | Design docs / comparison pages with tabs / decision logs | Tab system, comparison tables, Mermaid blocks. Source: this repo's `compact_v4/docs/HERMES_VS_CODING_AGENT.html`, ~56 KB. |
| `references/presentation_slides.html` | Slide-deck-style HTML, single-page, scroll-through | Hero section, stat row, numbered sections, comparison table, code block. Clean **generic template** with `[REPLACE]` placeholders — no business content. ~8 KB. |
| `references/flowchart_page.html` | Flowchart-heavy pages (Mermaid as centrepiece) | Architecture flowchart with multiple Mermaid blocks + interactive panel sections + comparison tables. Source: this repo's `PS_ClaudeCode_Insights/PS_FLOWCHART_V4.html`, ~88 KB. |

A 4th production reference ships in v5 at `docs/htmls/V5_DESIGN_OVERVIEW.html` — the v5 architecture overview. Use it as the default architecture/report reference inside the company zip.

---

## Workflow (the screenshot-iteration loop, mandatory)

SageMaker has no Playwright / no headless browser. The agent NEVER sees the rendered HTML directly. The only way to verify the output looks right is the user-driven screenshot loop:

1. **Pick the matching reference** based on request type. State which one you'll mimic.
2. **Read the reference** with `read_file` (offset / limit if it's the 3300-line tabbed one).
3. **Write the new HTML** with `write_file` to the user's specified path. If they didn't specify one, ask via `ask_user`.
4. **State the file:// URL** so the user can open it: `file:///D:/Github/.../X.html`. If the file uses tabs, append `#tab0` so they land on the first tab.
5. **Ask the user to screenshot** the part that looks wrong (or the whole page if they want full review). Tell them to save the screenshot to `<same-folder>/_shots/<descriptive_name>.png`.
6. **`view_image` the screenshot** when they say it's saved.
7. **Edit with `edit_file`** based on what's actually wrong in the screenshot.
8. Loop steps 5-7. After **3 rounds without convergence**, use `ask_user` to confirm whether to keep iterating, redesign from scratch, or accept as-is.

**Output convention:** create a `_shots/` subdirectory inside the user's HTML folder for the screenshots. Name screenshots `v1.png`, `v2.png`, `v2_after_tab_fix.png` — descriptive, not auto-generated UUIDs.

---

## Style: house palette and components (extracted from references)

These are the patterns the user's existing HTMLs share. Use them by default unless the user asks for something different.

### CSS variable palette (matches `v3_architecture.html`)

```css
:root {
  --navy: #0f172a; --navy-light: #1e293b;
  --blue: #3b82f6; --blue-hover: #2563eb;
  --sky: #0ea5e9;
  --green: #10b981; --green-light: #d1fae5;
  --amber: #f59e0b; --amber-light: #fef3c7;
  --purple: #8b5cf6; --purple-light: #ede9fe;
  --red: #ef4444; --red-light: #fef2f2;
  --teal: #0d9488;
}
```

### Standard sections (in order, when applicable)

1. Hero (h1 + subtitle + 4-6 stat badges)
2. Stats row (4-6 numeric cards)
3. Section list with `<h2>` numbered headers ("01 What Is It", "02 How It Works", etc.)
4. Comparison tables (always with header row + row stripes)
5. "What's New" sidebar or coloured callout box
6. Footer with metadata

### Components ready to copy

- **Tab strip JS** — vanilla, no framework. Lives at lines ~150-180 of `references/tabbed_design.html`.
- **Mermaid setup** — `<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>` + `mermaid.initialize({startOnLoad:true, theme:'dark'})`.
- **Stat card** — see `references/presentation_slides.html` for the small variant; `v3_architecture.html` for the large one.

---

## Anti-patterns (user-validated rules)

These are the user's hard rules from prior reports. Violate any of them = redo:

1. **No emojis** unless the user explicitly asks. (Their CLAUDE.md and memory rules.)
2. **HTML IS KING.** Never write "see docs/X.md" or "details elsewhere" — every detail the reader needs goes inline. Tables must include WHAT / WHY / HOW / examples / anti-patterns.
3. **No truncated tables.** If there are 30 rows of data, show all 30. Don't summarize "and 27 more".
4. **No lorem ipsum / placeholder text.** Every section must be filled with real content before showing the user.
5. **Mermaid safe syntax.** No `?`, `$`, `:`, `+`, `/` in node labels. Quote subgraph names with spaces. Per the user's `feedback_mermaid_syntax` memory.
6. **No "see screenshot below" without the screenshot embedded.** If you reference a chart, embed the PNG via `create_chart` first.
7. **No backticks for file references in human-readable HTML body.** Use `<code>file/path.py</code>` so the path is selectable + copyable.

---

## Validation before declaring done

Before saying "done", run these checks:

1. Search the output HTML for `TODO`, `lorem`, `placeholder`, `XXX`, `[REPLACE]` — none should remain. Use the `grep` tool (it works in any shell the agent has) or `read_file` + Python string search if grep isn't available.
2. Check Mermaid blocks: scan for `?`, `$`, `:`, `+`, `/` inside node label brackets — flag any hits.
3. `bash` (only if installed): `python -c "import html5lib; html5lib.parse(open('<file>.html').read())"` — any parse error = fix before declaring done. If `html5lib` not installed, skip silently.
4. Check the file size is sensible: a "presentation" page <100 KB; a "tabbed design" 100-500 KB; over 1 MB = something accidentally got embedded as base64 or duplicated.
5. **Final step is always**: ask the user to screenshot. The agent never declares "done" without a user screenshot review on visually-rich HTML.

---

## Quick recipes

### Recipe 1: tabbed design doc

User says: *"build a design doc for X with tabs Architecture / Decisions / Risks / Next Steps"*

1. `read_file` `references/tabbed_design.html` lines 1-300 (CSS + tab JS) and lines 200-800 (a sample tab).
2. `write_file` the new HTML using that scaffold.
3. Replace placeholder content with X's actual content.
4. Mermaid diagrams in the Architecture tab go in the same dark theme.
5. Default tab = `#tab0` (first tab is "Architecture").
6. Get screenshot, iterate.

### Recipe 2: presentation slides

User says: *"make me a single-page presentation explaining X"*

1. `read_file` `references/presentation_slides.html`.
2. Mimic structure: hero → 3-5 main sections → conclusion.
3. Each section is a "slide" with strong heading + brief text + visual element.
4. Keep total under 100 KB.

### Recipe 3: flowchart page

User says: *"explain the X flow with diagrams"*

1. `read_file` `references/flowchart_page.html`.
2. Use Mermaid `graph TD` for top-down or `flowchart LR` for left-right.
3. Each diagram has a short paragraph explaining what it shows + key decision points.
4. Business rules go in their own section, not embedded in node labels.

### Recipe 4: architecture report

User says: *"build an architecture report comparing X and Y"*

1. `read_file` `docs/htmls/V5_DESIGN_OVERVIEW.html` — the v5 architecture overview ships with the company zip.
2. Mimic: hero stats → numbered sections → comparison table → final assessment.
3. Use the CSS palette above.

---

## Output the file:// URL

Whenever the agent writes/edits an HTML, the FINAL line of the response should be the click-to-open URL:

```
file:///D:/Github/<absolute path>.html
```

If tabbed, suffix with `#tab0` (or whichever tab is most relevant). Do not include backticks around the URL — paste it raw so the user's terminal renders it as a hyperlink.
