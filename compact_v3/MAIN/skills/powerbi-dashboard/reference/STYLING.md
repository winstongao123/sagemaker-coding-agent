# PBIR Visual Styling Guide

How the AIPower dashboard styling was implemented using PBIR JSON format.

## Architecture Overview

Power BI PBIR (Power BI Interactive Report) stores reports as JSON files:
```
AIPower.Report/
  definition/
    report.json              # Report-level config
    pages/
      {page_id}/
        page.json            # Page background, dimensions
        visuals/
          {visual_name}/
            visual.json      # Visual type, position, query, formatting
```

Styling is applied at three levels:
1. **Page level** (`page.json` → `objects.background`) - page background color
2. **Container level** (`visual.json` → `visual.visualContainerObjects`) - border, background, title, header visibility
3. **Visual level** (`visual.json` → `visual.objects`) - data formatting (axes, labels, colors, fonts)

## PBIR Expression Patterns

All formatting values in PBIR use a specific expression wrapper pattern:

### Literal Expression (core pattern)
```json
{"expr": {"Literal": {"Value": "<value>"}}}
```

### Value Type Suffixes
| Type    | Suffix | Example               | Meaning                  |
|---------|--------|-----------------------|--------------------------|
| Decimal | `D`    | `"28D"`               | Font size 28pt           |
| Integer | `L`    | `"0L"`                | Integer zero             |
| Boolean | none   | `"true"` / `"false"`  | Boolean value            |
| String  | `''`   | `"'Segoe UI Semibold'"` | String with single quotes |

### Solid Color Pattern
Colors use a nested solid→color→expr structure:
```json
{
  "solid": {
    "color": {
      "expr": {
        "Literal": {
          "Value": "'#1E3A8A'"
        }
      }
    }
  }
}
```

## Helper Functions in generate_project.py

We built a set of Python helpers to generate these patterns:

### Primitive Helpers
```python
def _lit(value: str) -> dict:
    """Wrap a raw value as a PBIR Literal expression."""
    return {"expr": {"Literal": {"Value": value}}}

def _lit_bool(b: bool) -> dict:
    return _lit("true" if b else "false")

def _lit_str(s: str) -> dict:
    return _lit(f"'{s}'")

def _lit_num(n) -> dict:
    return _lit(f"{n}D")

def _solid_color(hex_color: str) -> dict:
    return {"solid": {"color": _lit_str(hex_color)}}
```

### Container Objects (visualContainerObjects)

`_base_container_objects()` generates the container wrapper for every visual:
- **visualHeader** → hidden (removes the `...` menu icon)
- **background** → white (#FFFFFF) with 0% transparency
- **border** → light gray (#D0DAE8) with show=true
- **title** → dark navy text (#0F172A) at 13pt

`_slicer_container_objects()` overrides with:
- Light blue background (#EEF3FA)
- Smaller title (11pt)

### Visual Objects (visual.objects)

These control the data-rendering portions of each visual type:

#### `_card_visual_objects()` - KPI Cards
```
calloutValue: 28pt, Segoe UI Semibold, navy (#0F172A)
categoryLabel: 11pt, gray (#64748B), show=true
```

#### `_chart_visual_objects()` - Bar/Column/Line Charts
```
categoryAxis: slate gray labels (#475569), 10pt
valueAxis: slate gray labels, 10pt, gridlines (#E2E8F0)
labels: (optional) dark blue (#1E3A8A), 10pt - enabled for bar/column, off for line
```

#### `_table_visual_objects()` - Tables
```
columnHeaders: white text (#FFFFFF) on dark blue (#1E3A8A), 11pt Semibold
values: dark slate text (#1E293B) on white, 10pt
total: dark blue text on light blue (#EEF3FA), 10pt Semibold
grid: vertical + horizontal gridlines, 3pt row padding
```

## Page Background

Applied in `write_page()` via `page.json` objects:
```json
{
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

This gives every page a light gray-blue background (#F3F6FB).

## Header Bar + Navigation Bar

### Header Bar
Implemented as a `card` visual with empty query, positioned at z=1000 (highest z-order):
- Position: x=0, y=0, w=1280, h=40
- Background: dark navy (#0F172A)
- Title: white text (#FFFFFF), 13pt
- Border: hidden
- Visual header: hidden
- Text format: `"  REGIONAL SALES  |  {Page Title}"`

Using a `card` visual instead of a `shape` avoids the complex shape PBIR schema requirements.

### Page Navigator
A single `pageNavigator` visual on each page provides real, clickable page navigation:
- Position: y=40, h=32, z=999, w=1280
- visualType: `"pageNavigator"` (built-in Power BI visual)
- Auto-syncs with report page names and ordering
- Styling: `objects.fill` (tab background), `objects.text` (font), `objects.outline` (border)
- Background: white (#FFFFFF), text: gray (#475569), outline: light border (#D0DAE8)

**IMPORTANT**: Do NOT use card visuals for navigation - they are decorative only.
Do NOT use actionButton unless individual button behavior with custom actions is needed.

## Auto-Styling in _visual_json()

The `_visual_json()` function automatically applies styling based on visual type:

```python
# Container-level styling
if visual_type == "slicer":
    visual["visual"]["visualContainerObjects"] = _slicer_container_objects(title)
else:
    visual["visual"]["visualContainerObjects"] = _base_container_objects(title=title)

# Visual-level data formatting (14 types supported)
if visual_type == "card":
    visual["visual"]["objects"] = _card_visual_objects()
elif visual_type in ("clusteredColumnChart", "clusteredBarChart", "lineChart"):
    # Charts with a Series field get legend styling
    if visual_type in ("clusteredColumnChart", "clusteredBarChart") and "Series" in query_state:
        visual["visual"]["objects"] = _stacked_visual_objects()
    else:
        visual["visual"]["objects"] = _chart_visual_objects(show_labels=...)
elif visual_type == "tableEx":
    visual["visual"]["objects"] = _table_visual_objects()
elif visual_type == "donutChart":
    visual["visual"]["objects"] = _donut_visual_objects()
elif visual_type in ("lineClusteredColumnComboChart", ...):
    visual["visual"]["objects"] = _combo_visual_objects()
elif visual_type == "areaChart":
    visual["visual"]["objects"] = _area_visual_objects()
elif visual_type == "treemap":
    visual["visual"]["objects"] = _treemap_visual_objects()
elif visual_type == "waterfallChart":
    visual["visual"]["objects"] = _waterfall_visual_objects()
elif visual_type == "funnel":
    visual["visual"]["objects"] = _funnel_visual_objects()
```

### New Visual Styling Helpers (v2)

#### `_donut_visual_objects()` - Donut/Pie Charts
```
legend: show, position=Right, 10pt, #475569
labels: show, #1E3A8A, 10pt, labelStyle="Category, percent of total"
```

#### `_combo_visual_objects()` - Combo Charts (bars + line)
```
categoryAxis: #475569 labels, 10pt
valueAxis: #475569 labels, 10pt, gridlines
lineStyles: strokeWidth=3
labels: hidden
```

#### `_stacked_visual_objects()` - Stacked Column/Bar
```
legend: show, position=Top, 10pt
categoryAxis: #475569 labels, 10pt
valueAxis: #475569 labels, 10pt, gridlines
labels: hidden
```

#### `_treemap_visual_objects()` - Treemaps
```
categoryLabels: white text (#FFFFFF), 11pt
labels: show, 10pt, labelStyle="Category, data"
```

#### `_waterfall_visual_objects()` - Waterfall Charts
```
sentimentColors: increase=#22C55E (green), decrease=#EF4444 (red), total=#2563EB (blue)
categoryAxis + valueAxis: standard styling
labels: show, #1E3A8A, 10pt
```

#### `_funnel_visual_objects()` - Funnel Charts
```
labels: show, #1E3A8A, 11pt, labelStyle="Both"
categoryLabels: show, #0F172A, 11pt
```

## Color Palette

Defined in `theme/AIPower-SalesTheme.json` (NOT linked as custom theme to avoid schema issues):

| Role            | Color   | Usage                          |
|-----------------|---------|--------------------------------|
| Primary Dark    | #0F172A | Header bar, card titles        |
| Primary Blue    | #1E3A8A | Table headers, data labels     |
| Accent Blue     | #2563EB | Charts (data color 2)          |
| Light Blue      | #60A5FA | Charts (data color 3)          |
| Page Background | #F3F6FB | Page background                |
| Card Background | #FFFFFF | Visual card background         |
| Border          | #D0DAE8 | Visual card borders            |
| Slicer BG       | #EEF3FA | Slicer/total row background    |
| Text Primary    | #0F172A | Titles, callout values         |
| Text Secondary  | #475569 | Axis labels                    |
| Text Muted      | #64748B | Category labels                |

## Key Decisions

### Why not link the custom theme via themeCollection?
Adding `themeCollection.customTheme` in `report.json` requires a `reportVersionAtImport` field.
If missing, Power BI throws a strict PBIR schema failure that blocks report loading entirely.
Instead, all styling is applied directly at the visual level — safer and more predictable.

### Why use `card` for the header bar instead of `shape`?
The `shape` visual type has a complex PBIR schema for defining fill, line, rotation, etc.
A `card` with an empty query and styled container objects achieves the same visual result
(colored rectangle with text) with much simpler JSON.

### Why `visualContainerObjects` vs `objects`?
- `visualContainerObjects` = container chrome (background, border, title, visual header icon)
- `objects` = visual-specific data rendering (axes, labels, column headers, callout values)
Both use the same Literal expression pattern, but target different aspects of the visual.

## Page Layout (1280 x 720 canvas)

### Executive page (no slicers):
```
y=0     ┌──────────── Header Bar (h=40) ────────────┐
y=40    ├── Page Navigator (h=32) ──────────────────┤
y=72    ├── KPI ── KPI ── KPI ── KPI ───────────────┤  (h=68)
y=146   ├── Donut (w=380) ── Combo Chart (w=870) ──┤  (h=195)
y=347   ├── Bar (w=625) ──── Area (w=625) ─────────┤  (h=160)
y=513   ├── Table (w=625) ── Funnel (w=625) ───────┤  (h=200)
y=720   └──────────────────────────────────────────┘
```

### Detail pages (with slicers):
```
y=0     ┌──────────── Header Bar (h=40) ────────────┐
y=40    ├── Page Navigator (h=32) ──────────────────┤
y=72    ├── Slicer (w=625) ── Slicer (w=625) ──────┤  (h=36)
y=112   ├── Chart (w=625) ───── Chart (w=625) ─────┤  (h=200)
y=318   ├── Chart (w=625) ───── Chart (w=625) ─────┤  (h=180)
y=504   ├── Table (w=625) ───── Chart (w=625) ─────┤  (h=170)
y=720   └──────────────────────────────────────────┘
```

### Table Display Names
Use `_measure_field()` for numeric columns in tables (not `_agg_col_field()`).
Inline aggregations show "Sum of ColumnName" as headers; measures show the measure name.

## File References

- Generator: `generate_project.py` (helpers at ~line 953, _visual_json at ~line 1060)
- Theme: `theme/AIPower-SalesTheme.json`
- Report config: `AIPower.Report/definition/report.json`
- Page files: `AIPower.Report/definition/pages/{id}/page.json`
- Visual files: `AIPower.Report/definition/pages/{id}/visuals/{name}/visual.json`
