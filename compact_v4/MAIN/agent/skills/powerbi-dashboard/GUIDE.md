# Power BI Dashboard Generator - Beginner Guide

## What Is This?

This is a **Claude Code skill** that generates complete Power BI dashboards from a text description. You describe your data and what you want to see, and the AI builds a fully working `.pbip` project you can open in Power BI Desktop.

No manual drag-and-drop. No clicking through menus. Just describe your dashboard and get a professional result.

## What It Generates

A single Python script (`generate_project.py`) that outputs:

| Output | Description |
|--------|-------------|
| `.pbip` project file | Entry point for Power BI Desktop |
| Semantic model (TMDL) | Tables, columns, measures, relationships (star schema) |
| Report pages (PBIR) | Pages with charts, KPIs, tables, slicers, navigation |
| Sample data (CSV) | Embedded in the model + exported for reference |
| M query preprocessing | Data cleaning, null handling, normalization, sorting |

## What You Can Ask For

### Data domains (any topic works)
- Sales & revenue dashboards
- University enrollment tracking
- HR & workforce analytics
- Financial reporting
- Marketing campaign performance
- Supply chain / inventory
- Customer support metrics
- Any dataset you can describe

### Dashboard features
- **4-8 pages** with different analytical focus areas
- **13 chart types**: KPI cards, bar charts, line charts, area charts, donut charts, combo charts (dual-axis), treemaps, waterfall charts, funnels, tables, slicers, page navigation
- **Star schema** data model with fact + dimension tables
- **DAX measures** (SUM, AVERAGE, CALCULATE, DIVIDE, etc.)
- **M query preprocessing** (text trimming, null handling, metric normalization, sorting, filtering)
- **Cross-filtering** between visuals
- **Professional styling** (consistent colors, fonts, borders, backgrounds)

### What the AI does automatically
The skill guides the AI through a full data engineering pipeline:

1. **Data analysis** - Identifies fact tables vs dimensions, determines grain, spots categorical vs numeric columns
2. **Star schema design** - Extracts dimension tables from fact data, creates foreign key relationships
3. **M query preprocessing** - Generates Power Query M code for text trimming, null handling, metric normalization, sorting, and invalid row filtering
4. **DAX measures** - Creates appropriate measures (SUM for additive, AVERAGE for rates, CALCULATE/DIVIDE for ratios) with format strings
5. **Visual selection** - Picks the right chart type for each metric (donut for proportions, combo for dual-axis, treemap for hierarchy, etc.)
6. **Layout design** - Arranges visuals on a 1280x720 grid with consistent spacing

### Example prompts
```
"Create a 4-page university enrollment dashboard with enquiries,
enrollments, conversion rates, and student demographics"

"Build a sales dashboard with 6 pages: executive overview, revenue
analysis, performance tracking, city comparison, channel mix, and
target tracking"

"Generate an HR dashboard showing headcount, turnover, hiring
pipeline, and department breakdowns"

"Here's my CSV data [paste schema]. Build a dashboard from it."
```

## How to Use

### Prerequisites
1. **Python 3.8+** installed
2. **Power BI Desktop** with these preview features enabled:
   - File > Options > Preview features:
     - Power BI Project (.pbip) save option
     - Store reports using enhanced metadata format (PBIR)
     - Store semantic model using TMDL format
   - Restart Power BI Desktop after enabling

### Step 1: Set up the skill

**Option A** - Claude Code custom command:
```bash
# Copy to your project's commands directory
mkdir -p .claude/commands/
cp -r path/to/AIPower/skill/ .claude/commands/powerbi-dashboard/
```
Then invoke with `/powerbi-dashboard` in Claude Code.

**Option B** - Direct reference:
Point your coding agent to `skill/powerbi-dashboard.md` as the prompt. The agent reads the SOP and template, then customizes the generator.

### Step 2: Describe your dashboard

Tell the agent:
- **Project name** (becomes the folder name)
- **Data description** (what entities, what metrics, what dimensions)
- **Pages** (what analytical views you want)
- **Key measures** (what calculations matter)

### Step 3: Agent generates

The agent will:
1. Read the SOP and template for correct patterns
2. Create a customized `generate_project.py`
3. Run it to produce all PBIR/TMDL files
4. Validate the output

### Step 4: Open in Power BI Desktop

1. Open Power BI Desktop
2. File > Open > navigate to `{project_name}/{project_name}.pbip`
3. The dashboard loads with all pages, charts, and data
4. Click "Refresh" if data doesn't appear on first load

## Scope and Limitations

### What it CAN do
- Generate any dashboard with embedded sample data
- Star schema data models (1 fact table + N dimension tables)
- Up to 8 pages with 6-7 visuals each
- 13 different chart types with professional styling
- M query data preprocessing pipeline
- DAX measures with formatting
- Relationships, slicers, cross-filtering
- Page navigation tabs

### What it CANNOT do
- Connect to live data sources (SQL Server, APIs, etc.) - it generates sample data
- Custom visuals from AppSource marketplace
- Row-level security (RLS)
- Incremental refresh policies
- Direct Lake / DirectQuery mode
- Power BI Service deployment (publish to web)
- Drill-through pages (planned for future)

### After generation
Once you open the `.pbip` in Power BI Desktop, you can:
- Swap the embedded sample data for your real data source
- Add more visuals manually via the Power BI UI
- Publish to Power BI Service
- Set up scheduled refresh

## Architecture

```
skill/
  powerbi-dashboard.md     <- Skill prompt (agent reads this)
  generate_template.py     <- Working template (agent customizes this)
  reference/
    SOP.md                 <- 24 lessons learned, all patterns
    STYLING.md             <- Colors, fonts, layout reference
    theme.json             <- Color palette
  tested/                  <- Test project (university dashboard)
    generate_project.py    <- Customized generator
    tested.pbip            <- Generated output
```

The skill works by:
1. Agent reads `powerbi-dashboard.md` (instructions + rules)
2. Agent reads `reference/SOP.md` (patterns + lessons)
3. Agent copies `generate_template.py` and customizes it
4. Python script generates all JSON/TMDL files
5. Power BI Desktop opens the `.pbip` project

## Tested Examples

| Dashboard | Pages | Data | Charts |
|-----------|-------|------|--------|
| AIPower (Sales) | 6 pages | 600 rows, 5 dims | 10 chart types, 40+ visuals |
| tested (University) | 4 pages | 360 rows, 4 dims | 10 chart types, 42 visuals |

Both dashboards open and render correctly in Power BI Desktop.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| TMDL parsing error `UnknownKeyword 'in'` | M expression indentation wrong | `let`/`in` at 3 tabs, body at 4 tabs (SOP #23) |
| Chart shows blank (data has "Error") | M query uses `Number.Min`/`Number.Max` | These don't exist in M. Use `if` expressions to clamp values (SOP #25) |
| Chart shows blank (data is fine) | Wrong field reference for visual type | See SOP #24 for per-visual-type rules |
| Table headers show "Sum of X" | Used `_agg_col_field` in table | Use `_measure_field` for tables (SOP #20) |
| Dimension table error with DISTINCT() | Used DAX function in M partition | Use `#table()` syntax (SOP #22) |
| Slicer dropdown overlaps content | Dropdown covers other visuals | Use tile/list mode slicers, not dropdowns |
| `stackedColumnChart` not found | Invalid visual type | Use `clusteredColumnChart` with Series field (SOP #18) |
| Combo chart Y axis wrong | Used "Column y"/"Line y" roles | Use `Y` for bars, `Y2` for line (SOP #13) |

## FAQ

**Q: Can I use my own data instead of sample data?**
A: Yes. After opening in Power BI Desktop, go to Transform Data and change the data source from the embedded `#table()` to your CSV, SQL, or API connection.

**Q: How many pages can I have?**
A: The template supports up to 8 pages. More is possible but the navigation bar gets crowded.

**Q: Can I change the colors?**
A: Yes. Edit the color constants in `generate_project.py` or modify `theme.json` and reference it.

**Q: Does it work with Power BI Service (cloud)?**
A: The generated `.pbip` opens in Power BI Desktop. From there you can publish to Power BI Service normally.

**Q: Can I add more visuals after generation?**
A: Yes. The generated project is a standard Power BI project. You can add, edit, or remove visuals in Power BI Desktop just like any other report.
