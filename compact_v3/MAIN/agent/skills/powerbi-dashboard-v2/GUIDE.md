# Power BI Dashboard Generator V2 - Guide

## What Is This?

A **config-driven Power BI dashboard generator** for any data domain. You describe your domain (healthcare, education, HR, retail, etc.) and the AI fills in a SCHEMA dict. The engine reads the SCHEMA and generates a complete `.pbip` project.

Unlike V1 (which reuses a fixed sales data model), V2 creates a **brand new star schema** for each domain.

## What It Generates

A single Python script (`generate_project.py`) that outputs:

| Output | Description |
|--------|-------------|
| `.pbip` project file | Entry point for Power BI Desktop |
| Semantic model (TMDL) | Custom tables, columns, measures, relationships |
| Report pages (PBIR) | Pages with auto-laid-out charts, KPIs, tables, slicers |
| Data (CSV) | Generated from SCHEMA specs **or** ingested from a real CSV file |
| M query preprocessing | Data cleaning, null handling, normalization, sorting |
| Calculated columns | Optional DAX-computed row-level columns |

## Data Source Modes

### Mode A: Generated Sample Data (default)
Engine generates random data using `fact_columns[].gen` specs (random_int, random_float, random_choice, weighted_choice, from_dim). Good for demos and prototyping.

### Mode B: CSV Data Ingestion
Engine reads a real CSV file, auto-extracts dimension values, auto-parses dates, type-converts columns, and embeds real data as M `#table()` literals. Good for production dashboards with real data.

## V1 vs V2

| | V1 (Template) | V2 (Engine) |
|---|---|---|
| File | `generate_template.py` | `generate_engine.py` |
| Data model | Fixed sales schema | Any domain via SCHEMA dict |
| Data source | Generated only | Generated or CSV ingestion |
| Calculated columns | No | Yes |
| Agent edits | Visuals only | SCHEMA dict only |
| Use when | Sales/business dashboards | Any domain (healthcare, HR, education, retail, etc.) |
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
"Create a retail sales dashboard from this CSV file: data/retail_sales.csv.
Track revenue, profit, and customer metrics by store and category."

"Create a university enrollment dashboard tracking enquiries,
applications, enrollments by faculty and campus"

"Build an HR workforce dashboard with headcount, turnover,
hiring pipeline by department, location, and job level"

"Generate a patient outcomes dashboard with admissions,
readmissions, satisfaction scores by department and ward"
```

## Standard Power BI Development Process

This table shows how the V2 skill maps to the standard Power BI development workflow:

| Step | Standard Process (Human) | V2 Skill (Agent) | Status |
|------|-------------------------|-------------------|--------|
| 1. Gather requirements | Interview stakeholders, define KPIs | Agent asks user for domain, metrics, pages | Covered |
| 2. Connect to data | Power Query: SQL, CSV, Excel, API | CSV ingestion or generated sample data | CSV covered |
| 3. Clean & transform | Power Query M steps (trim, null, filter) | `m_preprocessing` in SCHEMA | Covered |
| 4. Design data model | Star schema: fact + dimensions + relationships | SCHEMA: `dimensions`, `relationships` | Covered |
| 5. Create DAX measures | SUM, AVERAGE, CALCULATE, DIVIDE, etc. | `measures` in SCHEMA | Covered |
| 6. Create calculated columns | Row-level DAX computations | `calculated_columns` in SCHEMA | Covered |
| 7. Build report pages | Drag-and-drop visuals, set properties | `pages` + visual query shorthand | Covered |
| 8. Add slicers/filters | Drop slicer visuals, configure | `slicers` in page config | Covered |
| 9. Add navigation | Buttons, bookmarks, drill-through | `pageNavigator` auto-generated | Partial |
| 10. Apply theme/formatting | Custom theme JSON, conditional formatting | Fixed professional theme | Partial |
| 11. Test & validate | Check data accuracy, cross-filter behavior | Python runs, validates JSON structure | Covered |
| 12. Publish | Deploy to Power BI Service | User publishes manually | Not covered |

**Coverage**: 9/12 steps fully covered, 2 partial, 1 not covered (publishing).

## Example: End-to-End Process (CSV Mode)

Here is a complete example showing how the skill works with a real CSV file.

### 1. User provides a CSV file

`source_data/retail_sales.csv`:
```
Date,Store,Region,Category,Product,UnitsSold,Revenue,Cost,CustomerCount,ReturnCount
2023-01-15,Downtown,East,Electronics,Laptop,12,18000.00,14400.00,45,1
2023-01-15,Downtown,East,Electronics,Phone,28,14000.00,9800.00,82,3
2023-01-15,Mall,East,Clothing,Shoes,30,4500.00,2700.00,72,2
...
```

### 2. Agent analyzes the CSV

Agent reads the CSV and identifies:
- **Fact table**: Each row is a sales transaction record
- **Dimensions**: Store (Downtown/Mall/Suburb), Category (Electronics/Clothing), Date
- **Measures**: Revenue, Cost, UnitsSold, CustomerCount, ReturnCount
- **Calculated columns needed**: Profit (Revenue - Cost), ProfitMargin, ReturnRate

### 3. Agent designs the star schema

```
                  DimStore
                    |
DimDate --- RetailSales --- DimCategory
```

### 4. Agent copies the engine and edits SCHEMA

```bash
mkdir -p RetailDash
cp skills/powerbi-dashboard-v2/generate_engine.py RetailDash/generate_project.py
mkdir -p RetailDash/source_data
cp user_data/retail_sales.csv RetailDash/source_data/retail_sales.csv
```

Then agent edits the SCHEMA dict:

```python
SCHEMA = {
    "project_name": "RetailDash",
    "brand_label": "RETAIL SALES ANALYTICS",
    "fact_table": "RetailSales",

    "data_source": {
        "type": "csv",
        "path": "source_data/retail_sales.csv",
        "date_column": "Date",
    },

    "date": {"years": [2023], "dim_table": "DimDate", "key_column": "DateKey"},

    "dimensions": [
        {
            "dim_table": "DimStore",
            "key_column": "Store",
            "columns": [
                {"name": "Store", "type": "string"},
                {"name": "Region", "type": "string"},
            ],
            # values omitted — engine auto-extracts from CSV
        },
        {
            "dim_table": "DimCategory",
            "key_column": "Category",
            "columns": [
                {"name": "Category", "type": "string"},
                {"name": "Product", "type": "string"},
            ],
        },
    ],

    "fact_columns": [
        {"name": "UnitsSold", "type": "int64", "summarize": "sum"},
        {"name": "Revenue", "type": "double", "summarize": "sum"},
        {"name": "Cost", "type": "double", "summarize": "sum"},
        {"name": "CustomerCount", "type": "int64", "summarize": "sum"},
        {"name": "ReturnCount", "type": "int64", "summarize": "sum"},
    ],

    "calculated_columns": [
        {"name": "Profit", "dax": "[Revenue] - [Cost]",
         "type": "double", "summarize": "sum", "format": "$#,##0.00"},
        {"name": "ProfitMargin", "dax": "DIVIDE([Revenue] - [Cost], [Revenue])",
         "type": "double", "summarize": "average", "format": "#,##0.0%"},
    ],

    "measures": [
        {"name": "Total Revenue", "dax": "SUM(RetailSales[Revenue])", "format": "$#,##0"},
        {"name": "Total Profit", "dax": "SUM(RetailSales[Profit])", "format": "$#,##0"},
        {"name": "Avg Margin", "dax": "AVERAGE(RetailSales[ProfitMargin])", "format": "#,##0.0%"},
        {"name": "Total Units", "dax": "SUM(RetailSales[UnitsSold])", "format": "#,##0"},
        {"name": "Total Customers", "dax": "SUM(RetailSales[CustomerCount])", "format": "#,##0"},
    ],

    "relationships": [
        {"from": "RetailSales.DateKey", "to": "DimDate.DateKey"},
        {"from": "RetailSales.Store", "to": "DimStore.Store"},
        {"from": "RetailSales.Category", "to": "DimCategory.Category"},
    ],

    "pages": [
        {
            "id": "exec01", "title": "Executive Overview",
            "has_slicers": False, "slicers": [],
            "visuals": [
                {"type": "card", "title": "Total Revenue",
                 "query": {"Values": [{"measure": "Total Revenue"}]}},
                {"type": "card", "title": "Total Profit",
                 "query": {"Values": [{"measure": "Total Profit"}]}},
                {"type": "clusteredBarChart", "title": "Revenue by Store",
                 "query": {"Category": [{"col": ["DimStore", "Store"]}],
                           "Y": [{"agg_col": ["Revenue", 0]}]}},
                {"type": "donutChart", "title": "Revenue by Category",
                 "query": {"Category": [{"col": ["DimCategory", "Category"]}],
                           "Y": [{"agg_col": ["Revenue", 0]}]}},
            ],
        },
        {
            "id": "detail02", "title": "Store Performance",
            "has_slicers": True,
            "slicers": [
                {"title": "Store", "col": ["DimStore", "Store"]},
                {"title": "Year", "col": ["DimDate", "Year"]},
            ],
            "visuals": [
                {"type": "lineChart", "title": "Revenue Trend",
                 "query": {"Category": [{"col": ["DimDate", "YearMonth"]}],
                           "Y": [{"agg_col": ["Revenue", 0]}]}},
                {"type": "tableEx", "title": "Store Detail",
                 "query": {"Values": [
                     {"col": ["DimStore", "Store"]},
                     {"measure": "Total Revenue"},
                     {"measure": "Total Profit"},
                     {"measure": "Avg Margin"},
                 ]}},
            ],
        },
    ],
}
```

### 5. Agent runs the generator

```bash
python RetailDash/generate_project.py
```

Output:
```
Loaded 72 rows from source_data/retail_sales.csv
Auto-extracted 3 DimStore values
Auto-extracted 4 DimCategory values
Generated RetailDash with 72 data rows, 2 pages.
Open RetailDash/RetailDash.pbip in Power BI Desktop.
```

### 6. User opens in Power BI Desktop

Open `RetailDash/RetailDash.pbip` in Power BI Desktop. The dashboard loads with:
- Real data from the CSV embedded in the model
- Star schema with DimStore, DimCategory, DimDate relationships
- DAX measures computing totals and averages
- Calculated columns for Profit and ProfitMargin
- Professional charts, cards, and tables with auto-layout

## Tested Examples

| Dashboard | Domain | Data Source | Pages | Rows | Dims | Measures | Calc Cols |
|-----------|--------|-------------|-------|------|------|----------|-----------|
| AIPower (engine default) | Regional Sales | Generated | 6 | 576 | 5 | 20 | 0 |
| UniEnroll (tests/enrollment/) | University Enrollment | Generated | 4 | 432 | 5 | 13 | 0 |
| HealthDash (tests/healthcare/) | Healthcare | Generated | 5 | 480 | 4 | 14 | 0 |
| RetailDash (tests/csv/) | Retail Sales | CSV (72 rows) | 3 | 72 | 2 | 10 | 3 |
| HRDash (tests/hr/) | HR Workforce | Generated | 3 | 480 | 3 | 10 | 3 |
| LogiDash (tests/logistics/) | Supply Chain | Generated | 4 | 60 | 3 | 9 | 3 |
| MarketDash (tests/marketing/) | Marketing | Generated | 3 | 360 | 3 | 11 | 4 |

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
    generate_project.py    <- University enrollment example (generated data)
```

Test projects (in compact_v3/MAIN/tests/):
```
tests/
  enrollment/              <- Enrollment test (generated data, 4 pages)
  csv/                     <- Retail CSV test (real CSV data, 3 pages, calculated columns)
    source_data/
      retail_sales.csv     <- Source CSV file (72 rows)
    generate_project.py
  healthcare/              <- Healthcare test (generated data, 5 pages)
  hr/                      <- HR Workforce (3 pages, calc cols, M preprocessing, funnel+waterfall+treemap)
  logistics/               <- Supply Chain (4 pages, calc cols, M normalize+sort, combo charts)
  marketing/               <- Marketing (3 pages, 4 calc cols, M filter+sort+drop, all visual types)
```

## Testing Instructions

### Enrollment Test (Generated Data)
```bash
cd compact_v3/MAIN/tests/enrollment
python generate_project.py
```
Expected: `Generated UniEnroll with 432 data rows, 4 pages.`
Then open `UniEnroll/UniEnroll.pbip` in Power BI Desktop.

### CSV Ingestion Test
```bash
cd compact_v3/MAIN/tests/csv
python generate_project.py
```
Expected: `Loaded 72 rows from source_data/retail_sales.csv` + auto-extracted dimensions.
Then open `RetailDash/RetailDash.pbip` in Power BI Desktop.

### Healthcare Test
```bash
cd compact_v3/MAIN/tests/healthcare
python generate_project.py
```
Expected: `Generated HealthDash with 480 data rows, 5 pages.`
Then open `HealthDash/HealthDash.pbip` in Power BI Desktop.

### HR Workforce Test
```bash
cd compact_v3/MAIN/tests/hr
python generate_project.py
```
Expected: 480 rows, 3 pages. Calc cols: TenureBand, SalaryBand, NetHires. M preprocessing: text_trim + null_fill_text.
Then open `HRDash/HRDash.pbip` in Power BI Desktop.

### Logistics Test
```bash
cd compact_v3/MAIN/tests/logistics
python generate_project.py
```
Expected: 60 rows, 4 pages. Calc cols: DeliveryStatus, FreightPerUnit, DamageRate. M preprocessing: normalize + sort_by.
Then open `LogiDash/LogiDash.pbip` in Power BI Desktop.

### Marketing Test
```bash
cd compact_v3/MAIN/tests/marketing
python generate_project.py
```
Expected: 360 rows, 3 pages. Calc cols: ROI, CPA, CTR, PerformanceTier. M preprocessing: filter_expr + add_sort_key + sort_by + drop_columns.
Then open `MarketDash/MarketDash.pbip` in Power BI Desktop.

### What to Verify in Power BI Desktop
1. **Dashboard opens without errors** — no "corrupt file" or schema errors
2. **All pages load** — check page navigator at top shows all expected pages
3. **Data appears in visuals** — charts show bars/lines, cards show numbers, tables show rows
4. **Slicers work** — click a slicer value and verify charts filter correctly
5. **Relationships work** — check Model view shows correct star schema with lines connecting tables
6. **Calculated columns exist** (CSV test only) — in Data view, check fact table has Profit, ProfitMargin, ReturnRate columns
7. **Measures compute** — hover over a card to verify the measure formula in the formula bar

### If Something Breaks
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| File won't open | Preview features not enabled | Enable PBIR + TMDL in Power BI Options |
| "Values for 'name' property must be unique" | Duplicate visual UUIDs | Already fixed — re-run generator |
| Chart shows blank | Query shorthand doesn't match SCHEMA columns/measures | Check visual `query` in pages |
| TMDL parse error | Engine function was modified | Restore engine from original `generate_engine.py` |
| Missing table in Model view | Relationship references wrong table name | Check `relationships` in SCHEMA |
| CSV file not found | Wrong `data_source.path` | Path is relative to `generate_project.py` |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| TMDL `UnknownKeyword 'in'` | Don't edit engine functions - indentation is precise |
| Chart shows blank | Check visual query shorthand matches SCHEMA columns/measures |
| KeyError on dimension | Ensure `dim_table` name in SCHEMA matches relationship refs |
| Missing measure | Add to `"measures"` list in SCHEMA |
| Wrong aggregation | Check agg function code: 0=Sum, 1=Avg, 2=Min, 3=Max, 5=Count |
| CSV column not found | Check `column_mapping`: key=SCHEMA name, value=CSV header name |
| Calculated column blank | Ensure referenced columns exist in `fact_columns` |
| Date not parsed | Use YYYY-MM-DD or MM/DD/YYYY format in CSV date column |
