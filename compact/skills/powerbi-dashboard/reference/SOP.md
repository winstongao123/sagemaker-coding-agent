# SOP: Power BI Dashboard Generation via PBIR JSON

Standard Operating Procedure for a coding agent to generate a complete Power BI dashboard
from scratch using the PBIR (Power BI Interactive Report) format.

**Reference implementation**: `D:\Github\AIPower\generate_project.py`

---

## Overview

This SOP produces a `.pbip` project containing:
- Semantic model (TMDL format) with tables, columns, measures, relationships
- Report (PBIR format) with pages, visuals, styling
- Sample CSV data

The output opens directly in Power BI Desktop with preview features enabled.

---

## Step 1: Project Structure

Create the following directory structure:

```
{ProjectName}/
  {ProjectName}.pbip                          # Entry point
  .gitignore
  data/
    sales_data.csv                            # Sample data
  theme/
    {ProjectName}-Theme.json                  # Color theme reference
  docs/
    PBIR_STYLING_GUIDE.md                     # Styling documentation
  {ProjectName}.SemanticModel/
    definition.pbism                          # Model entry point
    definition/
      model.tmdl                             # Model config (compatibility, culture)
      tables/
        {TableName}.tmdl                     # One file per table
      relationships.tmdl                     # All relationships
  {ProjectName}.Report/
    definition.pbir                           # Report entry point
    definition/
      version.json                           # PBIR version
      report.json                            # Report config
      pages/
        pages.json                           # Page order list
        {page_id}/
          page.json                          # Page config (background, dimensions)
          visuals/
            {VisualName}/
              visual.json                    # Visual definition
```

## Step 2: Key File Templates

### `.pbip` (entry point)
```json
{
  "version": "1.0",
  "artifacts": [
    {
      "report": { "path": "{ProjectName}.Report" },
      "semanticModel": { "path": "{ProjectName}.SemanticModel" }
    }
  ]
}
```

### `definition.pbism` (semantic model entry)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/definition/semanticModel/1.0.0/schema.json",
  "compatibilityLevel": 1604
}
```

### `definition.pbir` (report entry)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/definition/2.0.0/schema.json",
  "datasetReference": {
    "byPath": { "path": "../{ProjectName}.SemanticModel" },
    "byConnection": null
  }
}
```

### `version.json`
```json
{ "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/semanticModelDefinitionVersion/1.0.0/schema.json", "version": "4.0" }
```

### `report.json`
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.5.0/schema.json",
  "themeCollection": { "baseTheme": { "name": "CY25SU12", "reportVersionAtImport": "5.62", "type": "SharedResources" } },
  "id": "{uuid}"
}
```

**WARNING**: Do NOT add `customTheme` to `themeCollection` without `reportVersionAtImport` - it causes a strict PBIR schema failure that blocks report loading entirely.

## Step 3: Semantic Model (TMDL)

### model.tmdl
```
model Model
  culture: en-US
  defaultPowerBIDataSourceVersion: powerBI_V3
  sourceQueryCulture: en-AU
  dataAccessOptions
    fastCombine
    legacyRedirects
    returnErrorValuesAsNull
```

### Table TMDL pattern
```
table {TableName}
  lineageTag: {uuid}

  column {ColumnName}
    dataType: {string|int64|double|dateTime|boolean}
    formatString: {format}
    lineageTag: {uuid}
    summarizeBy: {sum|average|none}
    sourceColumn: {ColumnName}
    annotation SummarizationSetBy = Automatic

  measure '{Measure Name}' = {DAX expression}
    formatString: {format}
    lineageTag: {uuid}

  partition {TableName} = m
    mode: import
    source =
      let
        Source = Csv.Document(File.Contents("{path}"), ...),
        ...
      in
        Result
```

### relationships.tmdl
```
relationship {uuid}
  fromColumn: {Table}.{Column}
  toColumn: {Table}.{Column}
```

## Step 4: Report Pages

### pages.json
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pages/1.0.0/schema.json",
  "pageOrder": ["{page1_id}", "{page2_id}", ...]
}
```

### page.json (with background)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
  "name": "{page_id}",
  "displayName": "{Page Title}",
  "displayOption": "FitToPage",
  "width": 1280,
  "height": 720,
  "objects": {
    "background": [{
      "properties": {
        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F3F6FB'"}}}}},
        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
      }
    }]
  }
}
```

## Step 5: Visual JSON

### PBIR Expression Pattern (critical)

All formatting values use this wrapper:
```json
{"expr": {"Literal": {"Value": "<value>"}}}
```

Value types:
- Decimal: `"28D"` (font size 28pt)
- Boolean: `"true"` / `"false"`
- String: `"'Segoe UI Semibold'"` (single-quoted)
- Color: nested in `{"solid": {"color": ...}}`

### Visual JSON structure
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "{unique_id}",
  "position": { "x": 10, "y": 90, "z": 0, "width": 305, "height": 72, "tabOrder": 3 },
  "visual": {
    "visualType": "{card|slicer|clusteredColumnChart|clusteredBarChart|lineChart|tableEx}",
    "query": { "queryState": { ... } },
    "visualContainerObjects": { ... },
    "objects": { ... }
  },
  "howCreated": "Default"
}
```

### Query State Patterns

**Card (KPI)**:
```json
{ "Values": { "projections": [{ "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "TableName"}}, "Property": "MeasureName"}}, "queryRef": "...", "nativeQueryRef": "...", "active": true }] } }
```

**Column Chart / Bar Chart**:
```json
{
  "Category": { "projections": [{ "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "...", "active": true }] },
  "Y": { "projections": [{ "field": {"Aggregation": {"Expression": {"Column": ...}, "Function": 0}}, "queryRef": "Sum(...)", "nativeQueryRef": "..." }] }
}
```
Aggregation Function values: 0=Sum, 1=Average, 2=Min, 3=Max, 5=Count

**Table**:
```json
{ "Values": { "projections": [{ "field": ..., "queryRef": "...", "nativeQueryRef": "..." }, ...] } }
```

**Slicer**:
```json
{ "Values": { "projections": [{ "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "...", "active": true }] } }
```

**Donut Chart** (same as Column/Bar):
```json
{
  "Category": { "projections": [{ "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "...", "active": true }] },
  "Y": { "projections": [{ "field": {"Aggregation": ...}, "queryRef": "Sum(...)", "nativeQueryRef": "..." }] }
}
```

**Combo Chart** (lineClusteredColumnComboChart):
```json
{
  "Category": { "projections": [{ "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "...", "active": true }] },
  "Y": { "projections": [{ "field": {"Aggregation": ...}, "queryRef": "Sum(...)", "nativeQueryRef": "..." }] },
  "Y2": { "projections": [{ "field": {"Aggregation": ...}, "queryRef": "Sum(...)", "nativeQueryRef": "..." }] }
}
```
Note: `"Y"` maps to bar/column series, `"Y2"` maps to the line overlay. **Do NOT use "Column y"/"Line y"** - those are invalid role names.

**Grouped Column/Bar with Series** (clusteredColumnChart / clusteredBarChart with Series field):
```json
{
  "Category": { "projections": [{ "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "...", "active": true }] },
  "Series": { "projections": [{ "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "..." }] },
  "Y": { "projections": [{ "field": {"Aggregation": ...}, "queryRef": "Sum(...)", "nativeQueryRef": "..." }] }
}
```
Note: **`stackedColumnChart` and `stackedBarChart` are NOT valid built-in visual types.** Use `clusteredColumnChart`/`clusteredBarChart` with a `Series` field instead - Power BI auto-groups the bars by the Series dimension.

**Treemap**:
```json
{
  "Group": { "projections": [
    { "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "..." },
    { "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "..." }
  ]},
  "Values": { "projections": [{ "field": {"Aggregation": ...}, "queryRef": "Sum(...)", "nativeQueryRef": "..." }] }
}
```
Multiple fields in `Group` create a hierarchy (e.g., State > City).

**Waterfall Chart**:
```json
{
  "Category": { "projections": [{ "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "...", "active": true }] },
  "Y": { "projections": [{ "field": {"Aggregation": ...}, "queryRef": "Sum(...)", "nativeQueryRef": "..." }] }
}
```

**Funnel**:
```json
{
  "Category": { "projections": [{ "field": {"Column": ...}, "queryRef": "...", "nativeQueryRef": "...", "active": true }] },
  "Y": { "projections": [{ "field": {"Aggregation": ...}, "queryRef": "Sum(...)", "nativeQueryRef": "..." }] }
}
```

**Area Chart**: Same query pattern as Line Chart (Category + Y).

## Step 6: Styling

### Container Objects (visualContainerObjects)
Applied to ALL visuals for consistent chrome:

```json
{
  "visualHeader": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
  "background": [{"properties": {
    "show": {"expr": {"Literal": {"Value": "true"}}},
    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
  }}],
  "border": [{"properties": {
    "show": {"expr": {"Literal": {"Value": "true"}}},
    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#D0DAE8'"}}}}}
  }}],
  "title": [{"properties": {
    "show": {"expr": {"Literal": {"Value": "true"}}},
    "text": {"expr": {"Literal": {"Value": "'Visual Title'"}}},
    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}},
    "fontSize": {"expr": {"Literal": {"Value": "13D"}}}
  }}]
}
```

### Visual Objects (objects) by Type

**Card**: `calloutValue` (font size/color/family), `categoryLabel` (show, color, fontSize)

**Chart**: `categoryAxis` (labelColor, fontSize), `valueAxis` (labelColor, fontSize, gridlineShow, gridlineColor), `labels` (show, color, fontSize)

**Table**: `columnHeaders` (fontColor, backColor, fontSize, fontFamily), `values` (fontSize, fontColor, backColor), `total` (fontColor, backColor), `grid` (gridVertical, gridHorizontal, rowPadding)

**Slicer**: `general` (outlineColor, outlineWeight), `selection` (selectAllCheckboxEnabled)

**Donut Chart**: `legend` (show, position, fontSize, fontColor), `labels` (show, color, fontSize, labelStyle)

**Combo Chart**: `categoryAxis`, `valueAxis`, `labels`, `lineStyles` (strokeWidth)

**Grouped Column/Bar (with Series)**: `legend` (show, position, fontSize), `categoryAxis`, `valueAxis`, `labels`

**Area Chart**: `categoryAxis`, `valueAxis`, `labels` (same as standard chart)

**Treemap**: `categoryLabels` (show, fontSize, fontColor), `labels` (show, fontSize, labelStyle)

**Waterfall Chart**: `sentimentColors` (increaseFill, decreaseFill, totalFill), `categoryAxis`, `valueAxis`, `labels`

**Funnel**: `labels` (show, color, fontSize, labelStyle), `categoryLabels` (show, fontSize, fontColor)

## Step 7: Page Layout Grid (1280x720)

Standard layout zones to avoid overlaps:

### Executive page (Page 1 - NO slicers):
```
y=0     Header Bar (h=40, z=1000)
y=40    Page Navigator (h=32, z=999) - pageNavigator visual
y=72    KPI Cards row (h=68) - 4 cards
y=146   Charts row 1 (h=195) - donut + combo chart
y=347   Charts row 2 (h=160) - bar chart + area chart
y=513   Summary Table (h=200, w=625) + Companion Visual (h=200, w=625)
```

### Detail pages (Pages 2-6 - with slicers):
```
y=0     Header Bar (h=40, z=1000)
y=40    Page Navigator (h=32, z=999) - pageNavigator visual
y=72    Slicers row (h=36) - 2 side-by-side slicers
y=112   Charts row 1 (h=200) - 2 columns at x=10/645, w=625 each
y=318   Charts row 2 (h=180)
y=504   Detail Table (h=170, w=625) + Companion Visual (h=170, w=625)
```

Bottom row: table on left (x=10, w=625) + companion chart on right (x=645, w=625).
Margins: x=10 left padding, 10px gap between columns.

## Step 8: Header Bar + Navigation Bar

### Header Bar
Implemented as a `card` visual with empty query (safer than `shape`):

```json
{
  "position": {"x": 0, "y": 0, "z": 1000, "width": 1280, "height": 40, "tabOrder": 0},
  "visual": {
    "visualType": "card",
    "query": {"queryState": {}},
    "visualContainerObjects": {
      "visualHeader": [{"properties": {"show": false_expr}}],
      "background": [{"properties": {"show": true_expr, "color": navy_color, "transparency": zero}}],
      "border": [{"properties": {"show": false_expr}}],
      "title": [{"properties": {"show": true_expr, "text": title_text, "fontColor": white_color, "fontSize": 13D}}]
    }
  }
}
```

### Page Navigator
A single `pageNavigator` visual on each page provides real page navigation:

```
Position: y=40, h=32, z=999, w=1280
visualType: "pageNavigator"
query: {"queryState": {}}
```

The `pageNavigator` is a built-in Power BI visual type that automatically creates clickable tabs
for all report pages. It auto-syncs with page names, ordering, and additions/removals.
Styling is applied via `objects` (fill, text, outline) and `visualContainerObjects` (background, border).

**IMPORTANT**: Do NOT use `card` visuals for navigation - they are decorative only and cannot navigate.
Do NOT use `actionButton` unless you need individual button behavior with custom actions.

## Step 9: Color Palette

Standard professional blue palette:

| Color   | Role                    |
|---------|-------------------------|
| #0F172A | Header bar, callout text |
| #1E3A8A | Table headers, data labels |
| #2563EB | Chart accent             |
| #F3F6FB | Page background          |
| #FFFFFF | Card background          |
| #D0DAE8 | Borders                  |
| #EEF3FA | Slicer background, totals |
| #475569 | Axis labels              |
| #64748B | Category labels          |
| #E2E8F0 | Grid lines               |

## Step 10: Validation Checklist

1. Run `python generate_project.py` - no errors
2. All `.json` files parse with `json.load()`
3. All TMDL files are UTF-8 with BOM (`\ufeff` prefix)
4. No visual overlaps (verify y + h < next_y for each row)
5. All `nativeQueryRef` values are sanitized (no special chars for simple names)
6. Page background color is set on all pages
7. Header bar present on all pages (z=1000 for top layer)
8. Open in Power BI Desktop - refresh data model, verify visuals render

## Key Lessons Learned

1. **Never use `themeCollection.customTheme`** without `reportVersionAtImport` - blocks loading
2. **TMDL requires UTF-8 BOM** - use `encoding='utf-8-sig'` when writing
3. **M expressions in TMDL** must be indented correctly within `source =` blocks
4. **Slicer visual type** is `"slicer"`, table is `"tableEx"` (not "table")
5. **`nativeQueryRef`** should NOT have special chars unless the column name requires them
6. Use `card` with empty query for header bars - simpler than `shape` visual type
7. Apply styling via `visualContainerObjects` + `objects` per visual, NOT via theme linking
8. The `z` property in position controls layering (header=z=1000, nav=z=999)
9. Aggregation Function enum: 0=Sum, 1=Avg, 2=Min, 3=Max, 5=Count
10. All literal string values in PBIR must be wrapped in single quotes: `"'text'"`
11. **Slicer dropdowns overlap content below** - avoid by: removing slicers from exec page, using compact slicers (h=36) on detail pages
12. **Navigation**: Use `pageNavigator` visual type for real page navigation - NOT card visuals (decorative only)
13. **Combo chart query roles**: `"Y"` for bar/column series, `"Y2"` for line series. **Do NOT use `"Column y"`/`"Line y"`** - those are invalid
14. **Treemap hierarchy**: Multiple fields in `"Group"` projections create parent>child hierarchy
15. **Waterfall sentiment colors**: `increaseFill`, `decreaseFill`, `totalFill` under `sentimentColors` object
16. **Visual diversity**: Use 8-10 chart types across a dashboard for storytelling (donut, combo, treemap, waterfall, funnel, area, bar, line, card)
17. **Executive page design**: No slicers - use cross-filtering between visuals; keep max 6-7 content visuals
18. **`stackedColumnChart` / `stackedBarChart` are NOT valid built-in types** - use `clusteredColumnChart`/`clusteredBarChart` with a `Series` field instead
19. **`pageNavigator`** auto-creates page tabs and syncs with report pages - much better than manual card/button navigation
20. **Use `_measure_field` for table columns** - Inline aggregations (`_agg_col_field`) show as "Sum of ColumnName" in table headers. Using pre-defined measures (`_measure_field`) shows the measure name instead, giving better control over display names. Always use measures in `tableEx` projections for numeric fields.
21. **`nativeQueryRef` does NOT control table column headers** - Power BI tables show the field property name (columns) or default aggregation label (aggregations). Only measures show their measure name as the header. To control display names reliably, define measures in the semantic model.
22. **Dimension table M partitions must use `#table()` syntax** - Use hardcoded `#table(type table [...], {...})` for dimension data. **Do NOT use `DISTINCT()`** - that is a DAX function, not valid M/Power Query. Extract unique dimension values in Python, then emit them as literal `#table()` rows in the TMDL partition source.
23. **TMDL M expression indentation is critical** - The `let`/`in` block must align at exactly 3 tabs under `source =` (2 tabs). Body lines at 4 tabs. If `let` is at 4 tabs, the TMDL parser cannot match `in` at 3 tabs and throws `UnknownKeyword 'in'`. Pattern: `\tpartition` → `\t\tsource =` → `\t\t\tlet` → `\t\t\t\tbody` → `\t\t\tin` → `\t\t\t\tresult`.
24. **Field reference rules by visual type**:
    - **`tableEx`**: Use `_measure_field` for numeric columns (clean headers, SOP #20)
    - **`clusteredBarChart` / `clusteredColumnChart`**: Use `_measure_field` for AVERAGE metrics, `_agg_col_field` with Sum (Function 0) for SUM metrics
    - **`lineClusteredColumnComboChart`**: Use `_agg_col_field` with **Sum only** (Function 0). Average aggregation (Function 1) in combo chart Y/Y2 renders blank. If you need averages in a combo chart, replace with a `clusteredBarChart` + `_measure_field` instead.
    - **`lineChart` / `areaChart` / `donutChart`**: `_agg_col_field` with Sum works reliably
    - **`card`**: Always use `_measure_field`
25. **`Number.Min` / `Number.Max` do NOT exist in Power Query M** - These are not valid M functions. To clamp values, use `if` expressions: `each if _ < 0 then 0 else if _ > 100 then 100 else _`. Using invalid M functions causes entire columns to show "Error" in data, making all charts using those columns blank.

## Step 11: Supported Visual Types Reference

| visualType | Query Roles | Best For |
|---|---|---|
| `card` | Values (Measure) | KPIs, header bars |
| `slicer` | Values (Column) | Filtering |
| `pageNavigator` | (none - auto) | Page navigation tabs |
| `clusteredColumnChart` | Category + Y (+ optional Series) | Comparing values by category |
| `clusteredBarChart` | Category + Y (+ optional Series) | Rankings, horizontal comparisons |
| `lineChart` | Category + Y | Trends over time |
| `areaChart` | Category + Y | Trends with volume emphasis |
| `donutChart` | Category + Y | Proportions/shares |
| `lineClusteredColumnComboChart` | Category + Y + Y2 | Dual-metric comparison |
| `treemap` | Group + Values | Hierarchical proportions |
| `waterfallChart` | Category + Y | Incremental contributions |
| `funnel` | Category + Y | Pipeline/stage analysis |
| `tableEx` | Values (multiple) | Detailed data |

**INVALID visual types** (do not use): `stackedColumnChart`, `stackedBarChart` - these are NOT built-in Power BI visual types. Use `clusteredColumnChart`/`clusteredBarChart` with a `Series` field instead.

## Skill Wrapper (Future)

To wrap this as a Claude Code skill:
1. Create a skill that accepts: project name, data source, page definitions
2. The skill calls `generate_project.py` with parameters
3. Returns the generated `.pbip` path for the user to open in Power BI Desktop
4. The SOP above provides the complete pattern for the skill implementation
5. The skill should support both the query patterns (Step 5) and styling (Step 6) for all 14 visual types listed in Step 11
