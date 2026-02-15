# Power BI Dashboard Generator V2 - Guide

## What Is This?

A **config-driven Power BI dashboard generator** for any data domain. You describe your domain (healthcare, education, HR, etc.) and the AI fills in a SCHEMA dict. The engine reads the SCHEMA and generates a complete `.pbip` project.

Unlike V1 (which reuses a fixed sales data model), V2 creates a **brand new star schema** for each domain.

## What It Generates

A single Python script (`generate_project.py`) that outputs:

| Output | Description |
|--------|-------------|
| `.pbip` project file | Entry point for Power BI Desktop |
| Semantic model (TMDL) | Custom tables, columns, measures, relationships |
| Report pages (PBIR) | Pages with auto-laid-out charts, KPIs, tables, slicers |
| Sample data (CSV) | Generated from SCHEMA specs, embedded in model |
| M query preprocessing | Data cleaning, null handling, normalization, sorting |

## V1 vs V2

| | V1 (Template) | V2 (Engine) |
|---|---|---|
| File | `generate_template.py` | `generate_engine.py` |
| Data model | Fixed sales schema | Any domain via SCHEMA dict |
| Agent edits | Visuals only | SCHEMA dict only |
| Use when | Sales/business dashboards | Healthcare, HR, education, etc. |
| Complexity | Simpler (reuses existing data) | More flexible (custom star schema) |

## How to Use

### Prerequisites
1. **Python 3.8+** installed
2. **Power BI Desktop** with preview features enabled:
   - File > Options > Preview features:
     - Power BI Project (.pbip) save option
     - Store reports using enhanced metadata format (PBIR)
     - Store semantic model using TMDL format
   - Restart Power BI Desktop after enabling

### Setup
```bash
# Copy to your project's commands directory
mkdir -p .claude/commands/
cp -r path/to/skills/powerbi-dashboard-v2/ .claude/commands/powerbi-dashboard-v2/
```
Then invoke with `/powerbi-dashboard-v2` in Claude Code.

### Example Prompts
```
"Create a university enrollment dashboard tracking enquiries,
applications, enrollments by faculty and campus"

"Build an HR workforce dashboard with headcount, turnover,
hiring pipeline by department, location, and job level"

"Generate a patient outcomes dashboard with admissions,
readmissions, satisfaction scores by department and ward"
```

### What Happens
1. Agent reads SKILL.md + reference/SOP.md
2. Agent copies `generate_engine.py` to your project
3. Agent edits the SCHEMA dict (dimensions, measures, pages)
4. Python runs and generates all PBIR/TMDL files
5. You open `{project_name}/{project_name}.pbip` in Power BI Desktop

## Tested Examples

| Dashboard | Domain | Pages | Data |
|-----------|--------|-------|------|
| AIPower (default) | Regional Sales | 6 pages | 576 rows, 5 dims, 20 measures |
| UniEnroll (tested/) | University Enrollment | 4 pages | 432 rows, 4 dims, 13 measures |

Both open and render correctly in Power BI Desktop.

## Architecture

```
powerbi-dashboard-v2/
  SKILL.md                 <- Skill prompt (agent reads this)
  generate_engine.py       <- Config-driven engine (agent copies + edits SCHEMA)
  GUIDE.md                 <- This file (human-readable)
  reference/
    SOP.md                 <- 25 lessons learned, all patterns
    STYLING.md             <- Colors, fonts, layout reference
    theme.json             <- Color palette
  tested/
    generate_project.py    <- University enrollment example
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| TMDL `UnknownKeyword 'in'` | Don't edit engine functions - indentation is precise |
| Chart shows blank | Check visual query shorthand matches SCHEMA columns/measures |
| KeyError on dimension | Ensure `dim_table` name in SCHEMA matches relationship refs |
| Missing measure | Add to `"measures"` list in SCHEMA |
| Wrong aggregation | Check agg function code: 0=Sum, 1=Avg, 2=Min, 3=Max, 5=Count |
