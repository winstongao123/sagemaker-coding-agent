---
name: powerbi-dashboard
description: Generate complete Power BI dashboards (.pbip) from a text description. Creates star schema data models, DAX measures, 14 chart types, and professional styling.
---

# Power BI Dashboard Generator Skill

You are an expert Power BI PBIR dashboard generator. You create professional Power BI projects (.pbip) using the PBIR (Power BI Enhanced Report) JSON format and TMDL (Tabular Model Definition Language) for semantic models.

## How This Skill Works

1. The user describes their dashboard requirements (data source, metrics, pages)
2. Choose the right generator:
   - **Level 1 (Quick Path)**: Sales/business dashboards → copy & edit `generate_template.py`
   - **Level 2 (Custom Domain)**: Any domain (healthcare, HR, education, etc.) → copy & edit `generate_engine.py` SCHEMA
3. Run the generator to produce a complete `.pbip` project
4. The user opens it in Power BI Desktop

## Reference Files

Before generating, read these reference documents for correct patterns:
- `reference/SOP.md` - Complete SOP with all visual types, query patterns, and 25 lessons learned
- `reference/STYLING.md` - Styling reference (colors, fonts, layouts)
- `reference/theme.json` - Color palette

## Generator Template

`generate_template.py` is a working generator that produces a 6-page sales dashboard. Use it as the base and customize:

### Customization Levels (choose ONE):

#### Level 1 — Quick Path (1-2 pages, ≤15 turns) ← USE THIS BY DEFAULT
Only change these. Do NOT touch `generate_data()` or `gen_semantic_model()`:
1. **`PROJECT_NAME`** — change to user's project name
2. **`gen_report()` page definitions** — remove unwanted pages, keep only the pages you need
3. **`gen_report()` visuals** — adjust/replace visuals on remaining pages to show user's requested charts
4. **`write_header_bar()` brand name** — change header text (nested inside `gen_report()`)

The template's existing data includes:
- **Fact columns**: Revenue, RevenueTarget, Orders, OrdersTarget, PipelineAmount, ForecastPct, COGS, GrossProfit, AvgOrderValue, DiscountPct, SatisfactionScore, TurnaroundDays, OnlinePercent, SalesStage, WinLossStatus
- **Dimensions**: DimDate (Year/Quarter/Month), DimCity (City/State/Region), DimChannel (Channel), DimSegment (Segment), DimProduct (ProductKey/ProductCategory), Territory
- **DAX measures (20)**: Total Revenue, Revenue Won, Qualified Pipeline, Total Revenue Target, Revenue Variance, Revenue Attainment %, Total Orders, Total Orders Target, Total Gross Profit, Gross Margin %, Avg Order Value, Avg Turnaround Days, Turnaround Target Days, Turnaround Gap, Avg Discount %, Forecast %, Avg Satisfaction, Avg Online %, Online Revenue, Online Revenue %

This is rich enough for most sales/business dashboards. The agent MUST reuse these existing measures and columns — do NOT invent new ones that don't exist in the data.

#### Level 2 — Custom Domain via Engine (any data schema, ≤20 turns) ← USE FOR NON-SALES DOMAINS
Use `generate_engine.py` — a config-driven engine where you edit ONLY the `SCHEMA` dict at the top. The engine handles all coupling (data generation, M expressions, TMDL, relationships, visuals) automatically.

**When to use Level 2**: The user wants a dashboard for a completely different domain (education, healthcare, HR, manufacturing, etc.) that doesn't fit the sales data model.

**How it works**: Copy `generate_engine.py`, edit only the `SCHEMA` dict, run it. The engine reads the SCHEMA and auto-generates everything — data, star schema, M expressions with preprocessing, TMDL files, and report pages with auto-layout. No manual coupling needed.

### What NOT to change:
- Helper functions (`_lit_bool`, `_lit_num`, `_solid_color`, `_projection`, etc.)
- `_visual_json()` auto-styling logic
- Visual type styling helpers (`_card_visual_objects`, `_chart_visual_objects`, etc.)
- PBIR schema references and JSON structure

## Helper Function Reference (DO NOT MODIFY — use as-is)

These functions are in `generate_template.py`. Call them when building visual `query_state` dicts:

### Field References
```python
_col_field(table, column)           # Column reference → use for Category, Group, Series, slicer Values
_measure_field(table, measure)      # Measure reference → use for card Values, table Values
_agg_col_field(table, column, func) # Aggregated column → use for chart Y, Y2
#   func: 0=Sum, 1=Average, 2=Min, 3=Max, 5=Count
```

### Projection Builder
```python
_projection(field, query_ref, native_query_ref=None, active=False)
# field: result of _col_field/_measure_field/_agg_col_field
# query_ref: "TableName.Column" or "Sum(Table.Col)"
# native_query_ref: display name (defaults to query_ref)
# active: True for slicer/category fields
```

### Visual Builder
```python
_visual_json(name, visual_type, x, y, w, h, query_state, tab_order=0, title=None)
# name: unique UUID (use make_uuid("prefix"))
# visual_type: one of the 14 supported types
# query_state: dict of query roles → projections (see table below)
# title: display title string
```

### Example: Building a clusteredColumnChart
```python
write_json(f"{page_path}/visuals/MyChart/visual.json", _visual_json(
    name=make_uuid("revenue.region"),
    visual_type="clusteredColumnChart",
    x=10, y=146, w=625, h=195, tab_order=2, title="Revenue by Region",
    query_state={
        "Category": {"projections": [_projection(_col_field("DimCity", "Region"), "DimCity.Region", "Region", True)]},
        "Y": {"projections": [_projection(_agg_col_field("SalesData", "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
    },
))
```

### Example: Building a card
```python
write_json(f"{page_path}/visuals/KPIRevenue/visual.json", _visual_json(
    name=make_uuid("kpi.revenue"),
    visual_type="card",
    x=10, y=72, w=200, h=68, tab_order=0, title="Total Revenue",
    query_state={
        "Values": {"projections": [_projection(_measure_field("SalesData", "Total Revenue"), "SalesData.Total Revenue")]},
    },
))
```

## Level 2 Engine: SCHEMA Reference

The `generate_engine.py` SCHEMA dict has these sections. Edit ONLY these — do NOT modify engine functions below the `ENGINE` marker.

### SCHEMA Structure
```python
SCHEMA = {
    "project_name": "MyProject",       # Output folder name
    "brand_label": "MY DASHBOARD",      # Header bar text
    "seed": 42,                         # Random seed for reproducible data
    "fact_table": "FactTableName",      # Fact table name used in DAX/M

    "date": {                           # Date dimension (auto-generated)
        "years": [2023, 2024],
        "dim_table": "DimDate",
        "key_column": "DateKey",
    },

    "dimensions": [ ... ],              # Dimension tables (see below)
    "fact_columns": [ ... ],            # Fact table metric columns
    "measures": [ ... ],                # DAX measures
    "relationships": [ ... ],           # Star schema relationships
    "m_preprocessing": { ... },         # M/Power Query data cleaning steps
    "sort_by_column": { ... },          # Column sort-by mappings
    "pages": [ ... ],                   # Dashboard pages with visuals
}
```

### Dimension Config
```python
{"dim_table": "DimFaculty", "key_column": "FacultyKey",
 "columns": [
     {"name": "FacultyKey", "type": "string"},
     {"name": "Faculty", "type": "string"},
 ],
 "values": [
     {"FacultyKey": "Business", "Faculty": "Business"},
     {"FacultyKey": "Engineering", "Faculty": "Engineering"},
 ],
 "assignment": "cross"}  # REQUIRED: "cross" = cartesian product, "random" = random per row
```

### Fact Column Gen Types
```python
{"name": "Revenue", "type": "double", "summarize": "sum",
 "gen": {"type": "random_float", "min": 1000, "max": 50000, "decimals": 2}}
{"name": "Count", "type": "int64", "summarize": "sum",
 "gen": {"type": "random_int", "min": 10, "max": 500}}
{"name": "Status", "type": "string", "summarize": "none",
 "gen": {"type": "random_choice", "choices": ["Active", "Inactive"]}}
{"name": "Status", "type": "string", "summarize": "none",
 "gen": {"type": "weighted_choice", "choices": ["Pass", "Fail"], "weights": [0.8, 0.2]}}
{"name": "Region", "type": "string", "summarize": "none",
 "gen": {"type": "from_dim", "dim": "DimCity", "col": "Region"}}
```

### Visual Query Shorthand (in page visuals)
```python
{"measure": "Total Revenue"}              # → _measure_field(fact_table, "Total Revenue")
{"col": ["DimCity", "Region"]}             # → _col_field("DimCity", "Region")
{"agg_col": ["Revenue", 0]}               # → _agg_col_field(fact_table, "Revenue", 0=Sum)
{"agg_col": ["Score", 1]}                 # → _agg_col_field(fact_table, "Score", 1=Avg)
```

### Page Visual Config
```python
{"id": "page01", "title": "Overview", "has_slicers": False, "slicers": [], "visuals": [
    {"type": "card", "title": "Total Revenue", "query": {"Values": [{"measure": "Total Revenue"}]}},
    {"type": "clusteredBarChart", "title": "By City", "query": {
        "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
]}
```
Slicers support two formats plus optional width override:
```python
{"title": "City", "col": ["DimCity", "City"]}                              # Shorthand
{"title": "City", "query": {"Values": [{"col": ["DimCity", "City"]}]}}     # Full query format
{"title": "Select Cities", "col": ["DimCity", "City"], "w": 1260}          # With custom width
```
Default slicer width: 2 slicers split 625px each; 1 slicer uses full 1260px (or custom `w`).

### M Preprocessing Config
```python
"m_preprocessing": {
    "text_trim": ["City", "Name"],              # Text.Trim on these columns
    "null_fill_text": ["City", "Name"],          # Replace null with "Unknown"
    "normalize": [{"column": "Score", "min": 0, "max": 100}],  # Clamp values
    "add_sort_key": {"name": "SortKey", "expr": "[Year] * 100 + [MonthNum]", "type": "Int64.Type"},
    "sort_by": [["SortKey", "Ascending"]],       # Table.Sort
    "drop_columns": ["SortKey"],                 # Remove helper columns
    "filter_expr": "[Revenue] >= 0",             # Table.SelectRows
}
```

## Supported Visual Types (14 total)

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
| `lineClusteredColumnComboChart` | Category + Y + Y2 | Dual-metric (clustered bars + line) |
| `lineStackedColumnComboChart` | Category + Y + Y2 | Dual-metric (stacked bars + line) |
| `treemap` | Group + Values | Hierarchy |
| `waterfallChart` | Category + Y | Variance |
| `funnel` | Category + Y | Pipeline |
| `tableEx` | Values (multiple) | Detail data |

## Critical Rules

0. **NEVER use `create_excel` or any Excel-based tool as a fallback.** This skill produces Power BI `.pbip` projects only. If you cannot create a Power BI dashboard for any reason, explain the issue to the user — do NOT silently fall back to Excel. Even if `ask_user` times out or the user skips the question, proceed with reasonable defaults and create the `.pbip` project.
1. **NEVER write a generator from scratch.** The template is 95KB / 2187 lines — you CANNOT reproduce it from memory. You MUST use `cp` (bash copy) to copy `generate_template.py` first, then use `edit_file` for targeted changes. If you use `write_file` to create the generator, you are violating this rule. The template's helper functions, `gen_pbip()` schema, styling, and PBIR JSON patterns are validated against Power BI Desktop — inventing your own will produce broken dashboards.
2. **INVALID visual types**: `stackedColumnChart`, `stackedBarChart` - use `clusteredColumnChart`/`clusteredBarChart` with a `Series` field instead
3. **Combo chart query roles**: `Y` = bars, `Y2` = line. NEVER use `"Column y"`/`"Line y"`
4. **Field reference by visual type**: Tables use `_measure_field()`. Bar/column charts use `_measure_field()` for averages, `_agg_col_field(Sum)` for sums. Combo charts use `_agg_col_field(Sum)` ONLY - Average in combo Y/Y2 renders blank. For average metrics, use a bar chart instead of combo.
5. **Navigation**: Use `pageNavigator` visual type - NOT card visuals (decorative only)
6. **File encoding**: UTF-8 **without** BOM (`encoding="utf-8"`) for ALL files including `.tmdl`. Do NOT use `utf-8-sig`.
7. **Literal strings**: Must be single-quoted: `"'text'"`, numbers suffixed with D: `"13D"`
8. **Max visuals per page**: 6-7 content visuals. Executive page: no slicers.
9. **Layout**: 1280x720 canvas. Header h=40, PageNav h=32, content starts at y=72.
10. **Dimension table M partitions**: Use hardcoded `#table()` syntax. NEVER use `DISTINCT()` (DAX, not valid M/Power Query).
11. **TMDL M expression indentation**: `let`/`in` at 3 tabs, body at 4 tabs. Wrong indentation causes `UnknownKeyword 'in'` error. Follow the template exactly.

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
8. Read `reference/SOP.md` **completely** (use offset to read ALL pages — lessons learned start at line 460+)

#### Level 1 Build Path (sales/business dashboards — DEFAULT)
9. **Copy the template file using bash `cp`. Do NOT use write_file.** Run:
   ```
   mkdir -p {project_name}
   cp skills/powerbi-dashboard/generate_template.py {project_name}/generate_project.py
   ```
10. **Edit the copied file using `edit_file` (surgical edits):**
    - `PROJECT_NAME = "AIPower"` → change to user's project name (~line 24)
    - `write_header_bar()` → change brand name (~line 1398, nested inside `gen_report()`)
    - `gen_report()` → remove unwanted page blocks, adjust visuals on remaining pages (~line 1267)
    - DO NOT change `generate_data()` or `gen_semantic_model()` — reuse the existing data schema
    - Do NOT touch helper functions, `gen_pbip()`, `gen_gitignore()`, `_visual_json()`, or any `_lit_*`/`_solid_color`/`_projection` functions.
11. Run `python {project_name}/generate_project.py`

#### Level 2 Build Path (custom domain — non-sales data)
9. **Copy the engine file using bash `cp`. Do NOT use write_file.** Run:
   ```
   mkdir -p {project_name}
   cp skills/powerbi-dashboard/generate_engine.py {project_name}/generate_project.py
   ```
10. **Edit ONLY the `SCHEMA` dict in the copied file using `edit_file`:**
    - `"project_name"` → user's project name
    - `"brand_label"` → dashboard header text
    - `"fact_table"` → fact table name matching the domain
    - `"date"` → year range for the data
    - `"dimensions"` → define dimension tables with columns and values
    - `"fact_columns"` → define metrics with gen specs (random_int, random_float, etc.)
    - `"measures"` → define DAX measures with format strings
    - `"relationships"` → star schema FK→PK relationships
    - `"m_preprocessing"` → M/Power Query cleaning steps
    - `"sort_by_column"` → column sort mappings
    - `"pages"` → dashboard pages with visual query shorthand
    - Do NOT modify anything below the `ENGINE` marker line
11. Run `python {project_name}/generate_project.py`

#### Common Steps (both levels)
12. If errors occur, read the error, fix the specific issue with `edit_file`, and re-run. Do NOT rewrite the entire file for small fixes.
13. Validate: all JSON parses, no visual overlaps, correct indentation
14. Tell user to open `{project_name}/{project_name}.pbip` in Power BI Desktop
