---
name: report
description: Create professional Word/PDF reports with embedded charts. Orchestrates the chart-first workflow to prevent missing graphs and ugly layouts.
triggers: create report, generate report, write report, word document, pdf document, create document
---

# Professional Report Generator

You create polished Word (.docx) or PDF reports with embedded charts. Follow this workflow **exactly** to prevent missing charts and ugly layouts.

## Critical Rules

1. **ALWAYS create charts BEFORE the document.** Call `create_chart` for each chart, verify the PNG exists, THEN call `create_word` or `create_pdf` with image references.
2. **NEVER skip the chart step.** If the user wants a chart in the document, you MUST generate it as a PNG first.
3. **Use 300 DPI** (default) for all charts. Use `dpi: 150` only if the user explicitly wants smaller file size.
4. **Use `width=6.5`** in image alt text for Word: `![Chart Title|width=6.5](chart.png)` — this fills the page properly with margins.
5. **Name chart files descriptively:** `revenue_chart.png`, `trend_line.png` — NOT `chart.png`, `chart2.png`.

## Chart Quality Settings

| Parameter | Default | When to change |
|-----------|---------|----------------|
| `dpi` | 300 | Use 150 for screen-only, 600 for large-format print |
| `width` | 10 | Use 12-14 for wide/landscape charts, 8 for narrow |
| `height` | 6 | Use 8 for tall charts (stacked bar, many categories) |
| `style` | "default" | Try "seaborn-v0_8" or "ggplot" for different aesthetics |
| `xlabel` | "" | Always set for bar/line/scatter — describes the x-axis |
| `ylabel` | "" | Always set for bar/line/scatter — describes the y-axis |

## Chart Types Available

| Type | Use for | Data format |
|------|---------|-------------|
| `bar` | Category comparison | `{labels: [...], values: [...]}` |
| `grouped_bar` | Multi-series comparison | `{labels: [...], series: [{name: "...", values: [...]}, ...]}` |
| `stacked_bar` | Part-to-whole over categories | `{labels: [...], series: [{name: "...", values: [...]}, ...]}` |
| `line` | Trends over time | `{x: [...], y: [...]}` or multi: `{x: [...], series: [{name: "...", values: [...]}, ...]}` |
| `pie` | Proportions | `{labels: [...], values: [...]}` |
| `scatter` | Correlation | `{x: [...], y: [...]}` |
| `horizontal_bar` | Rankings | `{labels: [...], values: [...]}` |
| `combo` | Bars + line overlay | `{labels: [...], bar_values: [...], line_values: [...], bar_label: "...", line_label: "...", line_ylabel: "..."}` |

## Workflow

### Phase 1: Understand Requirements
1. If the user already provided enough context (topic, data, format), skip to Phase 2.
   Otherwise, ask only what's missing:
   - What is the report about? (topic, audience)
   - What data do they have? (CSV file path, or describe the data)
   - Word or PDF output?
   - How many charts/visualizations needed?

### Phase 2: Prepare Data
2. If user provides a CSV or data file:
   - Read the file with `read_file`
   - Understand columns, data types, value ranges
   - Plan which charts best represent the data
3. If user describes data verbally:
   - Structure it into chart-ready format (labels + values)

### Phase 3: Generate Charts (DO THIS FIRST)
4. For EACH chart needed:
   ```
   create_chart(
     chart_type: "bar",
     title: "Revenue by Region",
     data: {"labels": [...], "values": [...]},
     filepath: "charts/revenue_by_region.png",
     xlabel: "Region",
     ylabel: "Revenue ($)",
     dpi: 300,
     width: 10,
     height: 6,
     colors: ["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]
   )
   ```
5. **Verify each chart was created successfully** (check the tool output confirms the file path) before proceeding.

### Phase 4: Compose Document
6. For **Word** output — use markdown content with image embeds:
   ```
   create_word(
     filepath: "report.docx",
     title: "Quarterly Business Report",
     include_toc: true,
     content: "
   # Executive Summary

   This report covers Q1 2026 performance...

   ## Revenue Analysis

   ![Revenue by Region|width=6.5](charts/revenue_by_region.png)

   Revenue grew 15% year-over-year...

   ## Trend Analysis

   ![Monthly Trend|width=6.5](charts/monthly_trend.png)

   | Region | Q1 | Q2 | Q3 | Q4 |
   | --- | --- | --- | --- | --- |
   | North | $1.2M | $1.4M | $1.5M | $1.8M |

   ---PAGE---

   ## Appendix
   ..."
   )
   ```

7. For **PDF** output — use structured sections (set `page_size` to `"a4"` or `"letter"`):
   ```
   create_pdf(
     filepath: "report.pdf",
     title: "Quarterly Business Report",
     page_size: "letter",
     content: [
       {"type": "heading", "data": "Executive Summary"},
       {"type": "text", "data": "This report covers Q1 2026 performance..."},
       {"type": "heading", "data": "Revenue Analysis"},
       {"type": "image", "data": "charts/revenue_by_region.png"},
       {"type": "text", "data": "Revenue grew 15% year-over-year..."},
       {"type": "heading", "data": "Data Summary"},
       {"type": "table", "data": [["Region", "Q1", "Q2"], ["North", "$1.2M", "$1.4M"]]}
     ]
   )
   ```

### Phase 5: Review
8. After document creation, use `read_file` on the output to check for `[Image not found]` or `[Image error]` markers. If found, re-create the missing chart and regenerate the document.
9. Tell the user the output file path and what's in it.

## Professional Color Palettes

Use these tested palettes for consistent, professional charts.
**Note on colors**: For `bar`, `line`, `pie`, `grouped_bar`, `stacked_bar`, `combo`, and `horizontal_bar`, match the number of colors to the number of categories or series. For `scatter`, **omit colors** unless you want a single uniform color (pass one color string, not a list).

**Corporate Blue:**
`["#1e3a5f", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe"]`

**Warm:**
`["#b91c1c", "#dc2626", "#ef4444", "#f87171", "#fca5a5"]`

**Earth Tones:**
`["#78350f", "#a16207", "#ca8a04", "#eab308", "#facc15"]`

**Multi-Category (up to 8):**
`["#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#9333ea", "#0891b2", "#e11d48", "#4f46e5"]`

## Common Mistakes to Avoid

1. **Calling create_word/create_pdf BEFORE create_chart** — the image won't exist yet
2. **Using `chart.png` for multiple charts** — each chart needs a unique filename
3. **Forgetting `|width=6.5`** in Word image alt text — default is 6.5" but explicit is better
4. **Not reading the data file first** — always inspect CSV/data before creating charts
5. **Too many data points on one chart** — if >15 categories, use horizontal_bar or group into "Other"
6. **Mismatched colors list length** — for bar/pie, match the number of colors to the number of data points. For scatter, omit or use a single color string
7. **Missing axis labels** — always set `xlabel` and `ylabel` for bar, line, scatter, combo charts
