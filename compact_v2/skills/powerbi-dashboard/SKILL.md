---
name: powerbi-dashboard
description: Generate complete Power BI .pbip dashboards from text descriptions (13 chart types, star schema, 4-8 pages)
---

# Power BI Dashboard Generator Skill

You are an expert Power BI PBIR dashboard generator. You create professional Power BI projects (.pbip) using the PBIR (Power BI Enhanced Report) JSON format and TMDL (Tabular Model Definition Language) for semantic models.

## How This Skill Works

1. The user describes their dashboard requirements (data source, metrics, pages)
2. You customize `generate_template.py` to match their needs
3. Run the generator to produce a complete `.pbip` project
4. The user opens it in Power BI Desktop

## Reference Files

Before generating, read these reference documents for correct patterns:
- `reference/SOP.md` - Complete SOP with all visual types, query patterns, and 25 lessons learned
- `reference/STYLING.md` - Styling reference (colors, fonts, layouts)
- `reference/theme.json` - Color palette

## Generator Template

`generate_template.py` is a working generator that produces a 6-page sales dashboard. Use it as the base and customize:

### What to customize per project:
1. **`PROJECT_NAME`** - The project folder name
2. **`generate_sample_data()`** - Replace with user's data schema or keep sample data
3. **Semantic model** - Tables, columns, relationships, measures in `write_semantic_model()`
4. **Report pages** - Page definitions, visuals, layouts in `write_report()`
5. **Header bar text** - Brand name in `write_header_bar()`

### What NOT to change:
- Helper functions (`_lit_bool`, `_lit_num`, `_solid_color`, `_projection`, etc.)
- `_visual_json()` auto-styling logic
- Visual type styling helpers (`_card_visual_objects`, `_chart_visual_objects`, etc.)
- PBIR schema references and JSON structure

## Supported Visual Types (13 total)

| visualType | Query Roles | Use For |
|---|---|---|
| `card` | Values (Measure) | KPIs |
| `slicer` | Values (Column) | Filters |
| `pageNavigator` | (none) | Page navigation |
| `clusteredColumnChart` | Category + Y (+ Series) | Category comparison |
| `clusteredBarChart` | Category + Y (+ Series) | Rankings |
| `lineChart` | Category + Y | Trends |
| `areaChart` | Category + Y | Trends with volume |
| `donutChart` | Category + Y | Proportions |
| `lineClusteredColumnComboChart` | Category + Y + Y2 | Dual-metric |
| `treemap` | Group + Values | Hierarchy |
| `waterfallChart` | Category + Y | Variance |
| `funnel` | Category + Y | Pipeline |
| `tableEx` | Values (multiple) | Detail data |

## Critical Rules

1. **INVALID visual types**: `stackedColumnChart`, `stackedBarChart` - use `clusteredColumnChart`/`clusteredBarChart` with a `Series` field instead
2. **Combo chart query roles**: `Y` = bars, `Y2` = line. NEVER use `"Column y"`/`"Line y"`
3. **Field reference by visual type**: Tables use `_measure_field()`. Bar/column charts use `_measure_field()` for averages, `_agg_col_field(Sum)` for sums. Combo charts use `_agg_col_field(Sum)` ONLY - Average in combo Y/Y2 renders blank. For average metrics, use a bar chart instead of combo.
4. **Navigation**: Use `pageNavigator` visual type - NOT card visuals (decorative only)
5. **TMDL encoding**: UTF-8 with BOM (`utf-8-sig`) for `.tmdl` files
6. **Literal strings**: Must be single-quoted: `"'text'"`, numbers suffixed with D: `"13D"`
7. **Max visuals per page**: 6-7 content visuals. Executive page: no slicers.
8. **Layout**: 1280x720 canvas. Header h=40, PageNav h=32, content starts at y=72.
9. **Dimension table M partitions**: Use hardcoded `#table()` syntax. NEVER use `DISTINCT()` (DAX, not valid M/Power Query).
10. **TMDL M expression indentation**: `let`/`in` at 3 tabs, body at 4 tabs. Wrong indentation causes `UnknownKeyword 'in'` error. Follow the template exactly.

## Page Layout Template

### Executive page (no slicers):
```
y=0     Header Bar (h=40, z=1000)
y=40    Page Navigator (h=32, z=999)
y=72    KPI Cards (h=68)
y=146   Charts row 1 (h=195)
y=347   Charts row 2 (h=160)
y=513   Table (w=625) + Chart (w=625) (h=200)
```

### Detail pages (with slicers):
```
y=0     Header Bar (h=40, z=1000)
y=40    Page Navigator (h=32, z=999)
y=72    Slicers (h=36)
y=112   Charts row 1 (h=200)
y=318   Charts row 2 (h=180)
y=504   Table (w=625) + Chart (w=625) (h=170)
```

## Workflow

### Phase 1: Requirements Gathering
1. Ask user: project name, data description (or provide a CSV/schema), desired pages/metrics

### Phase 2: Data Analysis & Model Design
2. **Analyze the data structure**:
   - Identify the fact table (transactions/events with numeric measures)
   - Identify dimension candidates (categorical columns: who, what, where, when)
   - Determine grain (one row = one what?)
3. **Design star schema**:
   - Fact table: keep foreign keys + numeric measures + any degenerate dimensions
   - Dimension tables: extract unique values for each dimension (DimDate, DimProduct, etc.)
   - Relationships: fact FK → dimension PK (many-to-one)
4. **Define measures** (DAX):
   - SUM for additive metrics (revenue, orders, counts)
   - AVERAGE for rates/scores (satisfaction, percentages)
   - CALCULATE + DIVIDE for ratios (conversion rate, attainment %)
   - Format strings: `$#,##0` for currency, `#,##0` for integers, `#,##0.0"%"` for percentages
5. **Plan M query preprocessing**:
   - Text trimming (`Text.Trim`) for string columns
   - Null handling (`Table.ReplaceValue` with "Unknown" or 0)
   - Metric normalization: use `if` expressions to clamp (NOT `Number.Min`/`Number.Max` which don't exist in M)
   - Sorting (`Table.Sort` by date/category keys)
   - Invalid row filtering (`Table.SelectRows`)

### Phase 3: Dashboard Design
6. **Plan pages** (4-8 pages):
   - Page 1: Executive Overview (KPIs + high-level charts, no slicers)
   - Pages 2-N: Detail pages (slicers + focused charts + data table)
   - Each page: max 6-7 content visuals
7. **Choose chart types per page** (use 8-10 different types across the dashboard):
   - KPIs → `card`
   - Proportions → `donutChart`
   - Trends → `lineChart`, `areaChart`
   - Comparisons → `clusteredBarChart`, `clusteredColumnChart`
   - Dual metrics → `lineClusteredColumnComboChart`
   - Hierarchy → `treemap`
   - Variance → `waterfallChart`
   - Pipeline → `funnel`
   - Detail → `tableEx`

### Phase 4: Build & Validate
8. Read `reference/SOP.md` for patterns (especially Steps 4-7, 11)
9. Copy `generate_template.py` to `{project_name}/generate_project.py`
10. Customize: data generation, semantic model, report pages, visuals
11. Run `python generate_project.py`
12. Validate: all JSON parses, no visual overlaps, correct indentation
13. Tell user to open `{project_name}/{project_name}.pbip` in Power BI Desktop
