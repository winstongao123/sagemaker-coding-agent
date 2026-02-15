"""Power BI PBIR Project Generator - Config-Driven Engine (V2)

Unlike generate_template.py (Level 1, hardcoded sales), this engine reads
a SCHEMA dict and generates a complete .pbip project for ANY domain.

Usage:
    1. Edit the SCHEMA dict below to match your domain
    2. Run: python generate_engine.py
    3. Open {project_name}.pbip in Power BI Desktop

The agent ONLY edits the SCHEMA dict. Everything below the
ENGINE marker is auto-logic - do NOT modify.
"""

import os
import json
import csv
import uuid
import random
import shutil
import re

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# ============================================================
# SCHEMA - The agent edits ONLY this section
# ============================================================

SCHEMA = {
    "project_name": "HealthDash",
    "brand_label": "PATIENT OUTCOMES",
    "seed": 77,
    "fact_table": "PatientData",

    "date": {
        "years": [2023, 2024],
        "dim_table": "DimDate",
        "key_column": "DateKey",
    },

    "dimensions": [
        {
            "dim_table": "DimDepartment", "key_column": "DeptKey",
            "columns": [
                {"name": "DeptKey", "type": "string"},
                {"name": "Department", "type": "string"},
            ],
            "values": [
                {"DeptKey": "Emergency", "Department": "Emergency"},
                {"DeptKey": "Cardiology", "Department": "Cardiology"},
                {"DeptKey": "Orthopedics", "Department": "Orthopedics"},
                {"DeptKey": "Neurology", "Department": "Neurology"},
                {"DeptKey": "Oncology", "Department": "Oncology"},
            ],
            "assignment": "cross",
        },
        {
            "dim_table": "DimWard", "key_column": "WardKey",
            "columns": [
                {"name": "WardKey", "type": "string"},
                {"name": "Ward", "type": "string"},
                {"name": "WardType", "type": "string"},
            ],
            "values": [
                {"WardKey": "Ward-A", "Ward": "Ward-A", "WardType": "General"},
                {"WardKey": "Ward-B", "Ward": "Ward-B", "WardType": "ICU"},
                {"WardKey": "Ward-C", "Ward": "Ward-C", "WardType": "Surgical"},
                {"WardKey": "Ward-D", "Ward": "Ward-D", "WardType": "Recovery"},
            ],
            "assignment": "cross",
        },
        {
            "dim_table": "DimAdmission", "key_column": "AdmissionType",
            "columns": [
                {"name": "AdmissionType", "type": "string"},
            ],
            "values": [
                {"AdmissionType": "Emergency"},
                {"AdmissionType": "Elective"},
                {"AdmissionType": "Transfer"},
            ],
            "assignment": "random",
        },
    ],

    "fact_columns": [
        {"name": "Admissions", "type": "int64", "summarize": "sum", "gen": {"type": "random_int", "min": 1, "max": 80}},
        {"name": "Discharges", "type": "int64", "summarize": "sum", "gen": {"type": "random_int", "min": 1, "max": 75}},
        {"name": "Readmissions", "type": "int64", "summarize": "sum", "gen": {"type": "random_int", "min": 0, "max": 15}},
        {"name": "AvgStayDays", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 1.5, "max": 14.0, "decimals": 1}},
        {"name": "SatisfactionScore", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 2.5, "max": 5.0, "decimals": 2}},
        {"name": "MortalityCount", "type": "int64", "summarize": "sum", "gen": {"type": "random_int", "min": 0, "max": 5}},
        {"name": "BedOccupancyPct", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 55.0, "max": 98.0, "decimals": 1}},
        {"name": "WaitTimeHours", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 0.5, "max": 8.0, "decimals": 1}},
    ],

    "measures": [
        {"name": "Total Admissions", "dax": "SUM(PatientData[Admissions])", "format": "#,##0"},
        {"name": "Total Discharges", "dax": "SUM(PatientData[Discharges])", "format": "#,##0"},
        {"name": "Total Readmissions", "dax": "SUM(PatientData[Readmissions])", "format": "#,##0"},
        {"name": "Readmission Rate %", "dax": "DIVIDE([Total Readmissions], [Total Admissions])", "format": "#,##0.0\"%\""},
        {"name": "Avg Length of Stay", "dax": "AVERAGE(PatientData[AvgStayDays])", "format": "#,##0.0"},
        {"name": "Avg Satisfaction", "dax": "AVERAGE(PatientData[SatisfactionScore])", "format": "#,##0.00"},
        {"name": "Total Mortality", "dax": "SUM(PatientData[MortalityCount])", "format": "#,##0"},
        {"name": "Mortality Rate %", "dax": "DIVIDE([Total Mortality], [Total Admissions])", "format": "#,##0.0\"%\""},
        {"name": "Avg Bed Occupancy %", "dax": "AVERAGE(PatientData[BedOccupancyPct])", "format": "#,##0.0\"%\""},
        {"name": "Avg Wait Time", "dax": "AVERAGE(PatientData[WaitTimeHours])", "format": "#,##0.0"},
    ],

    "relationships": [
        {"from": "PatientData.DateKey", "to": "DimDate.DateKey"},
        {"from": "PatientData.DeptKey", "to": "DimDepartment.DeptKey"},
        {"from": "PatientData.WardKey", "to": "DimWard.WardKey"},
        {"from": "PatientData.AdmissionType", "to": "DimAdmission.AdmissionType"},
    ],

    "m_preprocessing": {
        "text_trim": ["Department", "Ward"],
        "null_fill_text": ["Department", "Ward"],
        "normalize": [
            {"column": "SatisfactionScore", "min": 0, "max": 5},
            {"column": "BedOccupancyPct", "min": 0, "max": 100},
        ],
        "add_sort_key": {"name": "YearMonthSort", "expr": "[Year] * 100 + [MonthNum]", "type": "Int64.Type"},
        "sort_by": [["YearMonthSort", "Ascending"]],
        "drop_columns": ["YearMonthSort"],
        "filter_expr": "[Admissions] >= 0",
    },

    "sort_by_column": {"Month": "MonthNum", "YearMonth": "DateKey"},

    "pages": [
        # ── Page 1: Patient Overview ──
        {"id": "exec01", "title": "Patient Overview", "has_slicers": False, "slicers": [], "visuals": [
            {"type": "card", "title": "Total Admissions", "query": {"Values": [{"measure": "Total Admissions"}]}},
            {"type": "card", "title": "Readmission Rate %", "query": {"Values": [{"measure": "Readmission Rate %"}]}},
            {"type": "card", "title": "Avg Satisfaction", "query": {"Values": [{"measure": "Avg Satisfaction"}]}},
            {"type": "card", "title": "Avg Bed Occupancy %", "query": {"Values": [{"measure": "Avg Bed Occupancy %"}]}},
            {"type": "donutChart", "title": "Admissions by Department", "query": {
                "Category": [{"col": ["DimDepartment", "Department"]}], "Y": [{"agg_col": ["Admissions", 0]}]}},
            {"type": "lineClusteredColumnComboChart", "title": "Admissions & Discharges Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}],
                "Y": [{"agg_col": ["Admissions", 0]}], "Y2": [{"agg_col": ["Discharges", 0]}]}},
            {"type": "clusteredBarChart", "title": "Admissions by Ward", "query": {
                "Category": [{"col": ["DimWard", "Ward"]}], "Y": [{"agg_col": ["Admissions", 0]}]}},
            {"type": "areaChart", "title": "Monthly Satisfaction Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["SatisfactionScore", 1]}]}},
            {"type": "tableEx", "title": "Department Summary", "query": {"Values": [
                {"col": ["DimDepartment", "Department"]},
                {"measure": "Total Admissions"}, {"measure": "Readmission Rate %"}, {"measure": "Avg Satisfaction"}]}},
            {"type": "funnel", "title": "Admissions by Type", "query": {
                "Category": [{"col": ["DimAdmission", "AdmissionType"]}], "Y": [{"agg_col": ["Admissions", 0]}]}},
        ]},

        # ── Page 2: Department Analysis ──
        {"id": "dept02", "title": "Department Analysis", "has_slicers": True, "slicers": [
            {"title": "Department", "col": ["DimDepartment", "Department"]},
            {"title": "Year", "col": ["DimDate", "Year"]},
        ], "visuals": [
            {"type": "clusteredColumnChart", "title": "Admissions by Dept & Ward", "query": {
                "Category": [{"col": ["DimDepartment", "Department"]}],
                "Series": [{"col": ["DimWard", "Ward"]}],
                "Y": [{"agg_col": ["Admissions", 0]}]}},
            {"type": "donutChart", "title": "Readmissions by Department", "query": {
                "Category": [{"col": ["DimDepartment", "Department"]}], "Y": [{"agg_col": ["Readmissions", 0]}]}},
            {"type": "lineChart", "title": "Monthly Readmission Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["Readmissions", 0]}]}},
            {"type": "treemap", "title": "Admissions by Dept & Type", "query": {
                "Group": [{"col": ["DimDepartment", "Department"]}, {"col": ["DimAdmission", "AdmissionType"]}],
                "Values": [{"agg_col": ["Admissions", 0]}]}},
            {"type": "tableEx", "title": "Department Detail", "query": {"Values": [
                {"col": ["DimDepartment", "Department"]}, {"col": ["DimWard", "Ward"]},
                {"measure": "Total Admissions"}, {"measure": "Total Readmissions"}, {"measure": "Readmission Rate %"}]}},
            {"type": "waterfallChart", "title": "Admissions Contribution by Dept", "query": {
                "Category": [{"col": ["DimDepartment", "Department"]}], "Y": [{"agg_col": ["Admissions", 0]}]}},
        ]},

        # ── Page 3: Ward Performance ──
        {"id": "ward03", "title": "Ward Performance", "has_slicers": True, "slicers": [
            {"title": "Ward", "col": ["DimWard", "Ward"]},
            {"title": "Month", "col": ["DimDate", "Month"]},
        ], "visuals": [
            {"type": "clusteredBarChart", "title": "Bed Occupancy by Ward", "query": {
                "Category": [{"col": ["DimWard", "Ward"]}], "Y": [{"agg_col": ["BedOccupancyPct", 1]}]}},
            {"type": "lineChart", "title": "Occupancy Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["BedOccupancyPct", 1]}]}},
            {"type": "donutChart", "title": "Discharges by Ward Type", "query": {
                "Category": [{"col": ["DimWard", "WardType"]}], "Y": [{"agg_col": ["Discharges", 0]}]}},
            {"type": "areaChart", "title": "Wait Time Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["WaitTimeHours", 1]}]}},
            {"type": "tableEx", "title": "Ward Detail", "query": {"Values": [
                {"col": ["DimWard", "Ward"]}, {"col": ["DimWard", "WardType"]},
                {"measure": "Avg Bed Occupancy %"}, {"measure": "Avg Wait Time"}, {"measure": "Avg Length of Stay"}]}},
            {"type": "clusteredColumnChart", "title": "Length of Stay by Dept", "query": {
                "Category": [{"col": ["DimDepartment", "Department"]}], "Y": [{"agg_col": ["AvgStayDays", 1]}]}},
        ]},

        # ── Page 4: Patient Safety ──
        {"id": "safety04", "title": "Patient Safety", "has_slicers": True, "slicers": [
            {"title": "Department", "col": ["DimDepartment", "Department"]},
        ], "visuals": [
            {"type": "clusteredBarChart", "title": "Mortality by Department", "query": {
                "Category": [{"col": ["DimDepartment", "Department"]}], "Y": [{"agg_col": ["MortalityCount", 0]}]}},
            {"type": "lineChart", "title": "Mortality Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["MortalityCount", 0]}]}},
            {"type": "donutChart", "title": "Mortality by Ward Type", "query": {
                "Category": [{"col": ["DimWard", "WardType"]}], "Y": [{"agg_col": ["MortalityCount", 0]}]}},
            {"type": "lineClusteredColumnComboChart", "title": "Readmissions vs Satisfaction", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}],
                "Y": [{"agg_col": ["Readmissions", 0]}], "Y2": [{"agg_col": ["SatisfactionScore", 1]}]}},
            {"type": "tableEx", "title": "Safety Detail", "query": {"Values": [
                {"col": ["DimDepartment", "Department"]},
                {"measure": "Total Mortality"}, {"measure": "Mortality Rate %"}, {"measure": "Readmission Rate %"}, {"measure": "Avg Satisfaction"}]}},
            {"type": "waterfallChart", "title": "Mortality by Department", "query": {
                "Category": [{"col": ["DimDepartment", "Department"]}], "Y": [{"agg_col": ["MortalityCount", 0]}]}},
        ]},

        # ── Page 5: Trends & KPIs ──
        {"id": "trends05", "title": "Trends & KPIs", "has_slicers": True, "slicers": [
            {"title": "Year", "col": ["DimDate", "Year"]},
            {"title": "Department", "col": ["DimDepartment", "Department"]},
        ], "visuals": [
            {"type": "lineChart", "title": "Admissions Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["Admissions", 0]}]}},
            {"type": "lineChart", "title": "Satisfaction Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["SatisfactionScore", 1]}]}},
            {"type": "clusteredColumnChart", "title": "Quarterly Admissions", "query": {
                "Category": [{"col": ["DimDate", "Quarter"]}], "Y": [{"agg_col": ["Admissions", 0]}]}},
            {"type": "areaChart", "title": "Bed Occupancy Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["BedOccupancyPct", 1]}]}},
            {"type": "tableEx", "title": "KPI Summary", "query": {"Values": [
                {"col": ["DimDepartment", "Department"]},
                {"measure": "Total Admissions"}, {"measure": "Avg Length of Stay"}, {"measure": "Avg Bed Occupancy %"}, {"measure": "Avg Wait Time"}]}},
            {"type": "funnel", "title": "Discharges by Type", "query": {
                "Category": [{"col": ["DimAdmission", "AdmissionType"]}], "Y": [{"agg_col": ["Discharges", 0]}]}},
        ]},
    ],
}

# ============================================================
# ENGINE - Do NOT modify anything below this line
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def make_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"aipower.{name}"))


def _m_str(text: str) -> str:
    """Escape a string for M/Power Query literal."""
    return '"' + str(text).replace('"', '""') + '"'


def write_file(rel_path: str, content: str):
    full_path = os.path.join(PROJECT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print(f"  Created: {rel_path}")


def write_json(rel_path: str, obj: dict):
    write_file(rel_path, json.dumps(obj, indent=2, ensure_ascii=False))


def write_csv_file(rel_path: str, rows: list):
    full_path = os.path.join(PROJECT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(full_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Created: {rel_path}")


# ---- Field / query-state helpers ----

def _col_field(table: str, column: str) -> dict:
    """Build a column field reference (SQExpr)."""
    return {
        "Column": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": column,
        }
    }

def _measure_field(table: str, measure: str) -> dict:
    """Build a measure field reference (SQExpr)."""
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": measure,
        }
    }

def _agg_col_field(table: str, column: str, func: int) -> dict:
    """Build an aggregated column field reference (SQExpr Aggregation)."""
    return {
        "Aggregation": {
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": table}},
                    "Property": column,
                }
            },
            "Function": func,
        }
    }

def _projection(field: dict, query_ref: str, native_query_ref: str | None = None, active: bool = False) -> dict:
    """Build a projection entry."""
    obj = {
        "field": field,
        "queryRef": query_ref,
    }
    if native_query_ref is None:
        native_query_ref = query_ref
    obj["nativeQueryRef"] = native_query_ref
    if active:
        obj["active"] = True
    return obj

# ---- PBIR formatting expression helpers ----

def _lit(value: str) -> dict:
    """Wrap a value as a PBIR Literal expression."""
    return {"expr": {"Literal": {"Value": value}}}

def _lit_bool(b: bool) -> dict:
    return _lit("true" if b else "false")

def _lit_str(s: str) -> dict:
    return _lit(f"'{s}'")

def _lit_num(n) -> dict:
    return _lit(f"{n}D")

def _solid_color(hex_color: str) -> dict:
    return {"solid": {"color": _lit_str(hex_color)}}


def _base_container_objects(title: str | None = None, bg: str = "#FFFFFF",
                            border_color: str = "#D0DAE8", show_border: bool = True,
                            title_color: str = "#0F172A", title_size: int = 13) -> dict:
    """Standard container objects shared by all visuals."""
    objs = {
        "visualHeader": [{"properties": {"show": _lit_bool(False)}}],
        "background": [{"properties": {
            "show": _lit_bool(True),
            "color": _solid_color(bg),
            "transparency": _lit_num(0),
        }}],
        "border": [{"properties": {
            "show": _lit_bool(show_border),
            "color": _solid_color(border_color),
        }}],
    }
    if title:
        objs["title"] = [{"properties": {
            "show": _lit_bool(True),
            "text": _lit_str(title),
            "fontColor": _solid_color(title_color),
            "fontSize": _lit_num(title_size),
        }}]
    return objs

def _slicer_container_objects(title: str) -> dict:
    return _base_container_objects(title=title, bg="#EEF3FA", title_size=10)

def _card_visual_objects() -> dict:
    return {
        "calloutValue": [{"properties": {
            "color": _solid_color("#0F172A"),
            "fontSize": _lit_num(28),
            "fontFamily": _lit_str("Segoe UI Semibold"),
        }}],
        "categoryLabel": [{"properties": {
            "show": _lit_bool(True),
            "color": _solid_color("#64748B"),
            "fontSize": _lit_num(11),
        }}],
    }

def _chart_visual_objects(show_labels: bool = False) -> dict:
    objs = {
        "categoryAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
        }}],
        "valueAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
            "gridlineShow": _lit_bool(True),
            "gridlineColor": _solid_color("#E2E8F0"),
        }}],
    }
    if show_labels:
        objs["labels"] = [{"properties": {
            "show": _lit_bool(True),
            "color": _solid_color("#1E3A8A"),
            "fontSize": _lit_num(10),
        }}]
    return objs

def _table_visual_objects() -> dict:
    return {
        "columnHeaders": [{"properties": {
            "fontColor": _solid_color("#FFFFFF"),
            "backColor": _solid_color("#1E3A8A"),
            "fontSize": _lit_num(10),
            "fontFamily": _lit_str("Segoe UI Semibold"),
        }}],
        "values": [{"properties": {
            "fontSize": _lit_num(9),
            "fontColor": _solid_color("#1E293B"),
            "backColor": _solid_color("#FFFFFF"),
        }}],
        "total": [{"properties": {
            "fontColor": _solid_color("#1E3A8A"),
            "backColor": _solid_color("#EEF3FA"),
            "fontSize": _lit_num(9),
            "fontFamily": _lit_str("Segoe UI Semibold"),
        }}],
        "grid": [{"properties": {
            "gridVertical": _lit_bool(True),
            "gridHorizontal": _lit_bool(True),
            "rowPadding": _lit_num(2),
        }}],
    }


def _donut_visual_objects() -> dict:
    """Styling for donut/pie charts - legend, slice labels."""
    return {
        "legend": [{"properties": {
            "show": _lit_bool(True),
            "position": _lit_str("Right"),
            "fontSize": _lit_num(10),
            "fontColor": _solid_color("#475569"),
        }}],
        "labels": [{"properties": {
            "show": _lit_bool(True),
            "color": _solid_color("#1E3A8A"),
            "fontSize": _lit_num(10),
            "labelStyle": _lit_str("Category, percent of total"),
        }}],
    }

def _combo_visual_objects() -> dict:
    """Styling for lineClusteredColumnComboChart - dual axes."""
    return {
        "categoryAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
        }}],
        "valueAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
            "gridlineShow": _lit_bool(True),
            "gridlineColor": _solid_color("#E2E8F0"),
        }}],
        "y1AxisReferenceLine": [],
        "labels": [{"properties": {
            "show": _lit_bool(False),
        }}],
        "lineStyles": [{"properties": {
            "strokeWidth": _lit_num(3),
        }}],
    }

def _stacked_visual_objects() -> dict:
    """Styling for stacked column/bar charts - legend + axes."""
    return {
        "legend": [{"properties": {
            "show": _lit_bool(True),
            "position": _lit_str("Top"),
            "fontSize": _lit_num(10),
            "fontColor": _solid_color("#475569"),
        }}],
        "categoryAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
        }}],
        "valueAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
            "gridlineShow": _lit_bool(True),
            "gridlineColor": _solid_color("#E2E8F0"),
        }}],
        "labels": [{"properties": {
            "show": _lit_bool(False),
        }}],
    }

def _area_visual_objects() -> dict:
    """Styling for area charts - axes + fill."""
    return {
        "categoryAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
        }}],
        "valueAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
            "gridlineShow": _lit_bool(True),
            "gridlineColor": _solid_color("#E2E8F0"),
        }}],
        "labels": [{"properties": {
            "show": _lit_bool(False),
        }}],
    }

def _treemap_visual_objects() -> dict:
    """Styling for treemap - category labels + data labels."""
    return {
        "categoryLabels": [{"properties": {
            "show": _lit_bool(True),
            "fontSize": _lit_num(11),
            "fontColor": _solid_color("#FFFFFF"),
        }}],
        "labels": [{"properties": {
            "show": _lit_bool(True),
            "fontSize": _lit_num(10),
            "labelStyle": _lit_str("Category, data"),
        }}],
    }

def _waterfall_visual_objects() -> dict:
    """Styling for waterfall charts - sentiment colors + labels."""
    return {
        "sentimentColors": [{"properties": {
            "increaseFill": _solid_color("#22C55E"),
            "decreaseFill": _solid_color("#EF4444"),
            "totalFill": _solid_color("#2563EB"),
        }}],
        "categoryAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
        }}],
        "valueAxis": [{"properties": {
            "labelColor": _solid_color("#475569"),
            "fontSize": _lit_num(10),
            "gridlineShow": _lit_bool(True),
            "gridlineColor": _solid_color("#E2E8F0"),
        }}],
        "labels": [{"properties": {
            "show": _lit_bool(True),
            "color": _solid_color("#1E3A8A"),
            "fontSize": _lit_num(10),
        }}],
    }

def _funnel_visual_objects() -> dict:
    """Styling for funnel charts - labels + colors."""
    return {
        "labels": [{"properties": {
            "show": _lit_bool(True),
            "color": _solid_color("#1E3A8A"),
            "fontSize": _lit_num(11),
            "labelStyle": _lit_str("Both"),
        }}],
        "categoryLabels": [{"properties": {
            "show": _lit_bool(True),
            "fontSize": _lit_num(11),
            "fontColor": _solid_color("#0F172A"),
        }}],
    }


def _visual_json(name: str, visual_type: str, x: int, y: int, w: int, h: int,
                 query_state: dict, tab_order: int = 0, title: str | None = None) -> dict:
    """Build a visual.json object with professional styling."""
    visual = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": name,
        "position": {
            "x": x, "y": y, "z": 0,
            "width": w, "height": h,
            "tabOrder": tab_order,
        },
        "visual": {
            "visualType": visual_type,
            "query": {
                "queryState": query_state,
            },
        },
        "howCreated": "Default",
    }
    # Apply container-level objects (background, border, title, header)
    if visual_type == "slicer":
        visual["visual"]["visualContainerObjects"] = _slicer_container_objects(title or "")
    else:
        visual["visual"]["visualContainerObjects"] = _base_container_objects(title=title)

    # Apply visual-level formatting objects (data formatting, axes, labels)
    if visual_type == "card":
        visual["visual"]["objects"] = _card_visual_objects()
    elif visual_type == "slicer":
        visual["visual"]["objects"] = {
            "general": [{"properties": {
                "outlineColor": _solid_color("#D0DAE8"),
                "outlineWeight": _lit_num(1),
            }}],
            "selection": [{"properties": {
                "selectAllCheckboxEnabled": _lit_bool(True),
            }}],
        }
    elif visual_type in ("clusteredColumnChart", "clusteredBarChart", "lineChart"):
        # Charts with a Series field need legend styling
        if visual_type in ("clusteredColumnChart", "clusteredBarChart") and "Series" in query_state:
            visual["visual"]["objects"] = _stacked_visual_objects()
        else:
            visual["visual"]["objects"] = _chart_visual_objects(show_labels=(visual_type != "lineChart"))
    elif visual_type == "tableEx":
        visual["visual"]["objects"] = _table_visual_objects()
    elif visual_type == "donutChart":
        visual["visual"]["objects"] = _donut_visual_objects()
    elif visual_type in ("lineClusteredColumnComboChart", "lineStackedColumnComboChart"):
        visual["visual"]["objects"] = _combo_visual_objects()
    elif visual_type == "areaChart":
        visual["visual"]["objects"] = _area_visual_objects()
    elif visual_type == "treemap":
        visual["visual"]["objects"] = _treemap_visual_objects()
    elif visual_type == "waterfallChart":
        visual["visual"]["objects"] = _waterfall_visual_objects()
    elif visual_type == "funnel":
        visual["visual"]["objects"] = _funnel_visual_objects()

    return visual


# ---- Project scaffolding ----

def gen_pbip(schema):
    pn = schema["project_name"]
    write_json(f"{pn}.pbip", {
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{pn}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    })

def gen_gitignore():
    write_file(".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n*.pbix\n__pycache__/\n")


# ---- Data generation ----

def _get_fact_columns(schema):
    """Return ordered list of all fact table column metadata."""
    cols = []
    # Date key
    date_cfg = schema["date"]
    cols.append({"name": date_cfg["key_column"], "type": "int64", "summarize": "none"})
    # Dimension key columns
    for dim in schema["dimensions"]:
        key_col = dim["key_column"]
        key_type = "string"
        for c in dim["columns"]:
            if c["name"] == key_col:
                key_type = c["type"]
                break
        cols.append({"name": key_col, "type": key_type, "summarize": "none"})
    # Dimension non-key columns (flattened, in dim order)
    for dim in schema["dimensions"]:
        key_col = dim["key_column"]
        for c in dim["columns"]:
            if c["name"] != key_col:
                cols.append({"name": c["name"], "type": c["type"], "summarize": "none"})
    # Date value columns
    for name, typ in [("Year", "int64"), ("Quarter", "string"), ("Month", "string"),
                      ("MonthNum", "int64"), ("YearMonth", "string"), ("YearMonthSort", "int64")]:
        cols.append({"name": name, "type": typ, "summarize": "none"})
    # Additional fact columns
    for fc in schema["fact_columns"]:
        cols.append({"name": fc["name"], "type": fc["type"], "summarize": fc["summarize"]})
    return cols


def generate_data(schema):
    """Generate synthetic data rows from SCHEMA config."""
    random.seed(schema.get("seed", 42))
    date_cfg = schema["date"]
    dims = schema["dimensions"]

    # Build date periods
    periods = []
    for year in date_cfg["years"]:
        for month_idx, month_name in enumerate(MONTH_NAMES, 1):
            dk = year * 100 + month_idx
            periods.append({
                date_cfg["key_column"]: dk,
                "Year": year,
                "Quarter": f"Q{((month_idx - 1) // 3) + 1}",
                "Month": month_name,
                "MonthNum": month_idx,
                "YearMonth": f"{year}-{month_idx:02d}",
                "YearMonthSort": dk,
            })

    # Cross-product vs random dimensions
    cross_dims = [d for d in dims if d.get("assignment") == "cross"]
    random_dims = [d for d in dims if d.get("assignment") == "random"]

    # Build cartesian product of cross dimensions
    cross_combos = [()]
    for dim in cross_dims:
        cross_combos = [combo + (val,) for combo in cross_combos for val in dim["values"]]

    rows = []
    for period in periods:
        for combo in cross_combos:
            row = dict(period)
            # Add cross dim columns
            for dim, val in zip(cross_dims, combo):
                for c in dim["columns"]:
                    row[c["name"]] = val[c["name"]]
            # Add random dim columns
            for dim in random_dims:
                val = random.choice(dim["values"])
                for c in dim["columns"]:
                    row[c["name"]] = val[c["name"]]
            # Generate fact columns
            for fc in schema["fact_columns"]:
                g = fc["gen"]
                if g["type"] == "random_int":
                    row[fc["name"]] = random.randint(g["min"], g["max"])
                elif g["type"] == "random_float":
                    row[fc["name"]] = round(random.uniform(g["min"], g["max"]), g.get("decimals", 2))
                elif g["type"] == "random_choice":
                    row[fc["name"]] = random.choice(g["choices"])
                elif g["type"] == "weighted_choice":
                    row[fc["name"]] = random.choices(g["choices"], weights=g["weights"], k=1)[0]
                elif g["type"] == "from_dim":
                    row[fc["name"]] = row.get(g["col"], "")
            rows.append(row)
    return rows


# ---- M type mapping ----

def _build_m_type(col_type: str) -> str:
    """Map SCHEMA column type to M #table() type."""
    if col_type == "string":
        return "text"
    elif col_type == "int64":
        return "Int64.Type"
    elif col_type == "double":
        return "number"
    return "text"


# ---- Fact table M expression builder ----

def _build_fact_m_expression(data_rows, schema):
    """Build the complete M/Power Query expression for the fact table partition."""
    fact_cols = _get_fact_columns(schema)

    # Build column schema string for #table() type definition
    col_schema_parts = []
    for c in fact_cols:
        col_schema_parts.append(f'{c["name"]} = {_build_m_type(c["type"])}')
    col_schema_str = ", ".join(col_schema_parts)

    # Build row literals
    row_lines = []
    for r in data_rows:
        vals = []
        for c in fact_cols:
            v = r[c["name"]]
            if c["type"] == "string":
                vals.append(_m_str(v))
            else:
                vals.append(str(v))
        row_lines.append("\t\t\t\t\t\t{" + ", ".join(vals) + "}")
    row_data = ",\n".join(row_lines)

    # Build preprocessing steps
    preproc = schema.get("m_preprocessing", {})
    steps = []
    prev_step = "Source"

    # text_trim
    if "text_trim" in preproc:
        trim_cols = preproc["text_trim"]
        trim_entries = []
        for col in trim_cols:
            trim_entries.append(f'\t\t\t\t\t\t{{"{col}", each Text.Trim(_), type text}}')
        trim_body = ",\n".join(trim_entries)
        steps.append(
            f'\t\t\t\tCleanText = Table.TransformColumns(\n'
            f'\t\t\t\t\t{prev_step},\n'
            f'\t\t\t\t\t{{\n'
            f'{trim_body}\n'
            f'\t\t\t\t\t}}\n'
            f'\t\t\t\t)'
        )
        prev_step = "CleanText"

    # null_fill_text
    if "null_fill_text" in preproc:
        fill_cols = preproc["null_fill_text"]
        fill_list = ", ".join(f'"{c}"' for c in fill_cols)
        steps.append(
            f'\t\t\t\tFillMissingText = Table.ReplaceValue({prev_step}, null, "Unknown", Replacer.ReplaceValue, {{{fill_list}}})'
        )
        prev_step = "FillMissingText"

    # normalize
    if "normalize" in preproc:
        norm_entries = []
        for n in preproc["normalize"]:
            col = n["column"]
            mn = n["min"]
            mx = n["max"]
            norm_entries.append(
                f'\t\t\t\t\t\t{{"{col}", each if _ < {mn} then {mn} else if _ > {mx} then {mx} else _, type number}}'
            )
        norm_body = ",\n".join(norm_entries)
        steps.append(
            f'\t\t\t\tNormalizeMetrics = Table.TransformColumns(\n'
            f'\t\t\t\t\t{prev_step},\n'
            f'\t\t\t\t\t{{\n'
            f'{norm_body}\n'
            f'\t\t\t\t\t}}\n'
            f'\t\t\t\t)'
        )
        prev_step = "NormalizeMetrics"

    # add_sort_key
    if "add_sort_key" in preproc:
        sk = preproc["add_sort_key"]
        steps.append(
            f'\t\t\t\tAddSortKey = Table.AddColumn({prev_step}, "{sk["name"]}", each {sk["expr"]}, {sk["type"]})'
        )
        prev_step = "AddSortKey"

    # sort_by
    if "sort_by" in preproc:
        sort_parts = []
        for s in preproc["sort_by"]:
            sort_parts.append(f'{{"{s[0]}", Order.{s[1]}}}')
        sort_str = ", ".join(sort_parts)
        steps.append(
            f'\t\t\t\tSortRows = Table.Sort({prev_step}, {{{sort_str}}})'
        )
        prev_step = "SortRows"

    # drop_columns
    if "drop_columns" in preproc:
        drop_list = ", ".join(f'"{c}"' for c in preproc["drop_columns"])
        steps.append(
            f'\t\t\t\tDropHelper = Table.RemoveColumns({prev_step}, {{{drop_list}}})'
        )
        prev_step = "DropHelper"

    # filter_expr
    if "filter_expr" in preproc:
        steps.append(
            f'\t\t\t\tFilterInvalid = Table.SelectRows({prev_step}, each {preproc["filter_expr"]})'
        )
        prev_step = "FilterInvalid"

    # Build complete M expression
    step_text = ""
    for i, s in enumerate(steps):
        step_text += ",\n" + s
    # Last step has no trailing comma — already handled by join approach
    # Actually each step was appended individually; the last step in the let block must NOT have comma
    # We handle this: Source + steps joined by comma, then in/final

    m_expression = (
        'let\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [{col_schema_str}],\n'
        f'\t\t\t\t\t{{\n'
        f'{row_data}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)'
        f'{step_text}\n'
        f'\t\t\tin\n'
        f'\t\t\t\t{prev_step}'
    )

    return m_expression


# ---- Fact table TMDL builder ----

def _build_fact_tmdl(data_rows, schema):
    """Build the complete TMDL content for the fact table."""
    fact_table = schema["fact_table"]
    fact_cols = _get_fact_columns(schema)

    tmdl_type_map = {"string": "string", "int64": "int64", "double": "double"}

    lines = []
    lines.append(f'table {fact_table}')
    lines.append(f'\tlineageTag: {make_uuid("table." + fact_table)}')
    lines.append('')

    # Measures
    for m in schema["measures"]:
        name = m["name"]
        dax = m["dax"]
        fmt = m["format"]
        slug = re.sub(r'[^A-Za-z0-9]', '', name)
        lines.append(f"\tmeasure '{name}' = {dax}")
        lines.append(f'\t\tformatString: {fmt}')
        lines.append(f'\t\tlineageTag: {make_uuid("measure." + slug)}')
        lines.append('')

    # Columns
    for c in fact_cols:
        name = c["name"]
        dtype = tmdl_type_map.get(c["type"], "string")
        summarize = c.get("summarize", "none")
        lines.append(f'\tcolumn {name}')
        lines.append(f'\t\tdataType: {dtype}')
        lines.append(f'\t\tlineageTag: {make_uuid("col." + name)}')
        lines.append(f'\t\tsummarizeBy: {summarize}')
        lines.append(f'\t\tsourceColumn: {name}')
        if name in schema.get("sort_by_column", {}):
            lines.append(f'\t\tsortByColumn: {schema["sort_by_column"][name]}')
        lines.append('')

    # Partition
    m_expression = _build_fact_m_expression(data_rows, schema)
    lines.append(f'\tpartition {fact_table} = m')
    lines.append(f'\t\tmode: import')
    lines.append(f'\t\tsource =')
    lines.append(f'\t\t\t{m_expression}')

    return '\n'.join(lines) + '\n'


# ---- Dimension table TMDL builder ----

def _build_dim_tmdl(dim_config, schema):
    """Build TMDL for a regular dimension table."""
    dim_table = dim_config["dim_table"]
    columns = dim_config["columns"]
    values = dim_config["values"]

    tmdl_type_map = {"string": "string", "int64": "int64", "double": "double"}
    m_type_map = {"string": "text", "int64": "Int64.Type", "double": "number"}

    lines = []
    lines.append(f'table {dim_table}')
    lines.append(f'\tlineageTag: {make_uuid("table." + dim_table)}')
    lines.append('')

    # Columns (all summarizeBy: none for dims)
    for c in columns:
        name = c["name"]
        dtype = tmdl_type_map.get(c["type"], "string")
        lines.append(f'\tcolumn {name}')
        lines.append(f'\t\tdataType: {dtype}')
        lines.append(f'\t\tlineageTag: {make_uuid("col." + dim_table + "." + name)}')
        lines.append(f'\t\tsummarizeBy: none')
        lines.append(f'\t\tsourceColumn: {name}')
        lines.append('')

    # Build M expression for partition
    col_schema_parts = []
    for c in columns:
        col_schema_parts.append(f'{c["name"]} = {m_type_map.get(c["type"], "text")}')
    col_schema_str = ", ".join(col_schema_parts)

    # Extract unique rows from values
    seen = set()
    unique_values = []
    for v in values:
        key = tuple(v[c["name"]] for c in columns)
        if key not in seen:
            seen.add(key)
            unique_values.append(v)

    row_lines = []
    for v in unique_values:
        vals = []
        for c in columns:
            val = v[c["name"]]
            if c["type"] == "string":
                vals.append(_m_str(val))
            else:
                vals.append(str(val))
        row_lines.append("\t\t\t\t\t\t{" + ", ".join(vals) + "}")
    row_data = ",\n".join(row_lines)

    m_expression = (
        'let\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [{col_schema_str}],\n'
        f'\t\t\t\t\t{{\n'
        f'{row_data}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource'
    )

    lines.append(f'\tpartition {dim_table} = m')
    lines.append(f'\t\tmode: import')
    lines.append(f'\t\tsource =')
    lines.append(f'\t\t\t{m_expression}')

    return '\n'.join(lines) + '\n'


# ---- Date dimension TMDL builder ----

def _build_date_dim_tmdl(data_rows, schema):
    """Build TMDL for the DimDate dimension table (auto-generated from data)."""
    date_cfg = schema["date"]
    dim_table = date_cfg["dim_table"]

    # Extract unique date rows
    date_set = set()
    for r in data_rows:
        date_set.add((
            r["DateKey"], r["Year"], r["Quarter"], r["Month"], r["MonthNum"], r["YearMonth"]
        ))
    date_rows_sorted = sorted(date_set, key=lambda x: x[0])

    lines = []
    lines.append(f'table {dim_table}')
    lines.append(f'\tlineageTag: {make_uuid("table." + dim_table)}')
    lines.append('')

    # Columns
    dim_date_cols = [
        ("DateKey", "int64", None),
        ("Year", "int64", None),
        ("Quarter", "string", None),
        ("Month", "string", "MonthNum"),
        ("MonthNum", "int64", None),
        ("YearMonth", "string", "DateKey"),
    ]
    for name, dtype, sort_col in dim_date_cols:
        lines.append(f'\tcolumn {name}')
        lines.append(f'\t\tdataType: {dtype}')
        lines.append(f'\t\tlineageTag: {make_uuid("col." + dim_table + "." + name)}')
        lines.append(f'\t\tsummarizeBy: none')
        lines.append(f'\t\tsourceColumn: {name}')
        if sort_col:
            lines.append(f'\t\tsortByColumn: {sort_col}')
        lines.append('')

    # Build M expression
    row_lines = []
    for d in date_rows_sorted:
        row_lines.append(
            f'\t\t\t\t\t\t{{{d[0]}, {d[1]}, {_m_str(d[2])}, {_m_str(d[3])}, {d[4]}, {_m_str(d[5])}}}'
        )
    row_data = ",\n".join(row_lines)

    m_expression = (
        'let\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [DateKey = Int64.Type, Year = Int64.Type, Quarter = text, Month = text, MonthNum = Int64.Type, YearMonth = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{row_data}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource'
    )

    lines.append(f'\tpartition {dim_table} = m')
    lines.append(f'\t\tmode: import')
    lines.append(f'\t\tsource =')
    lines.append(f'\t\t\t{m_expression}')

    return '\n'.join(lines) + '\n'


# ---- Relationships TMDL builder ----

def _build_relationships_tmdl(schema):
    """Build relationships.tmdl content from schema relationships."""
    parts = []
    for rel in schema["relationships"]:
        from_str = rel["from"]  # "SalesData.DateKey"
        to_str = rel["to"]      # "DimDate.DateKey"
        from_table, from_col = from_str.split(".", 1)
        to_table, to_col = to_str.split(".", 1)
        rel_id = make_uuid(f"rel.{from_str}->{to_str}")
        parts.append(
            f'relationship {rel_id}\n'
            f'\tfromColumn: {from_table}.{from_col}\n'
            f'\ttoColumn: {to_table}.{to_col}\n'
        )
    return '\n'.join(parts)


# ---- Semantic model orchestrator ----

def gen_semantic_model(data_rows, schema):
    """Orchestrate writing all semantic model files."""
    pn = schema["project_name"]
    sm_base = f"{pn}.SemanticModel"
    defn = f"{sm_base}/definition"

    # definition.pbism
    write_json(f"{sm_base}/definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0"
    })

    # model.tmdl
    write_file(f"{defn}/model.tmdl",
        'model Model\n'
        '\tculture: en-AU\n'
        '\tdefaultPowerBIDataSourceVersion: powerBI_V3\n'
    )

    # Fact table TMDL
    fact_tmdl = _build_fact_tmdl(data_rows, schema)
    write_file(f"{defn}/tables/{schema['fact_table']}.tmdl", fact_tmdl)

    # Date dimension TMDL
    date_tmdl = _build_date_dim_tmdl(data_rows, schema)
    write_file(f"{defn}/tables/{schema['date']['dim_table']}.tmdl", date_tmdl)

    # Regular dimension TDMLs
    for dim in schema["dimensions"]:
        dim_tmdl = _build_dim_tmdl(dim, schema)
        write_file(f"{defn}/tables/{dim['dim_table']}.tmdl", dim_tmdl)

    # Relationships
    rel_tmdl = _build_relationships_tmdl(schema)
    write_file(f"{defn}/relationships.tmdl", rel_tmdl)


# ---- Field reference resolver ----

def _resolve_field_ref(ref, schema):
    """Translate a visual query shorthand dict to (field_dict, query_ref_str, native_query_ref_str)."""
    fact_table = schema["fact_table"]
    agg_names = {0: "Sum", 1: "Avg", 2: "Min", 3: "Max", 5: "Count"}

    if "measure" in ref:
        name = ref["measure"]
        return (
            _measure_field(fact_table, name),
            f"{fact_table}.{name}",
            name,
        )
    elif "col" in ref:
        table, column = ref["col"]
        return (
            _col_field(table, column),
            f"{table}.{column}",
            column,
        )
    elif "agg_col" in ref:
        column, func = ref["agg_col"]
        agg_name = agg_names.get(func, "Sum")
        return (
            _agg_col_field(fact_table, column, func),
            f"{agg_name}({fact_table}.{column})",
            column,
        )
    raise ValueError(f"Unknown field ref: {ref}")


# ---- Query state builder ----

def _build_query_state(visual_config, schema):
    """Build the query_state dict for _visual_json from a visual's query config."""
    query = visual_config.get("query", {})
    visual_type = visual_config.get("type", "")
    query_state = {}

    for role_name, field_refs in query.items():
        projections = []
        for ref in field_refs:
            field, query_ref, native_ref = _resolve_field_ref(ref, schema)

            # Determine active flag based on role and visual type
            active = False
            if role_name == "Category":
                active = True
            elif role_name == "Values" and visual_type == "slicer":
                active = True
            elif role_name == "Values" and visual_type == "card":
                # Card Values with measures are active
                if "measure" in ref or "agg_col" in ref:
                    active = True

            projections.append(_projection(field, query_ref, native_ref, active))
        query_state[role_name] = {"projections": projections}

    return query_state


# ---- Auto-layout ----

def _auto_layout_page(page_config):
    """Compute x, y, w, h for all visuals on a page."""
    visuals = page_config.get("visuals", [])
    has_slicers = page_config.get("has_slicers", False)

    # Separate cards and non-cards
    cards = [v for v in visuals if v.get("type") == "card"]
    non_cards = [v for v in visuals if v.get("type") != "card"]

    result = []

    if not has_slicers:
        # Executive layout (no slicers)
        # Cards row: y=72, h=68
        n_cards = len(cards)
        if n_cards > 0:
            card_w = (1260 - (n_cards - 1) * 10) // n_cards
            for i, card in enumerate(cards):
                x = 10 + i * (card_w + 10)
                # Last card takes remaining width
                w = card_w if i < n_cards - 1 else (1280 - 10 - x)
                result.append({"visual": card, "x": x, "y": 72, "w": w, "h": 68})

        # Non-card rows
        row_specs = [
            (146, 195),   # Row 1
            (347, 160),   # Row 2
            (513, 200),   # Row 3 (bottom)
        ]
    else:
        # Detail layout (has slicers)
        # No cards expected on slicer pages usually, but handle them anyway
        n_cards = len(cards)
        if n_cards > 0:
            card_w = (1260 - (n_cards - 1) * 10) // n_cards
            for i, card in enumerate(cards):
                x = 10 + i * (card_w + 10)
                w = card_w if i < n_cards - 1 else (1280 - 10 - x)
                result.append({"visual": card, "x": x, "y": 72, "w": w, "h": 68})

        row_specs = [
            (112, 200),   # Row 1
            (318, 180),   # Row 2
            (504, 170),   # Row 3 (bottom)
        ]

    # Place non-cards in rows of 2
    row_idx = 0
    i = 0
    while i < len(non_cards) and row_idx < len(row_specs):
        y, h = row_specs[row_idx]
        if i + 1 < len(non_cards):
            # Two visuals in this row
            result.append({"visual": non_cards[i], "x": 10, "y": y, "w": 625, "h": h})
            result.append({"visual": non_cards[i + 1], "x": 645, "y": y, "w": 625, "h": h})
            i += 2
        else:
            # Only one visual - full width
            result.append({"visual": non_cards[i], "x": 10, "y": y, "w": 1260, "h": h})
            i += 1
        row_idx += 1

    return result


# ---- Header bar writer ----

def write_header_bar(page_path, page_title, schema):
    """Write the header bar visual at the top of a page."""
    brand = schema.get("brand_label", "DASHBOARD")
    write_json(f"{page_path}/visuals/_HeaderBar/visual.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": make_uuid(f"header.{page_title}"),
        "position": {"x": 0, "y": 0, "z": 1000, "width": 1280, "height": 40, "tabOrder": 0},
        "visual": {
            "visualType": "card",
            "query": {"queryState": {}},
            "visualContainerObjects": {
                "visualHeader": [{"properties": {"show": _lit_bool(False)}}],
                "background": [{"properties": {
                    "show": _lit_bool(True),
                    "color": _solid_color("#0F172A"),
                    "transparency": _lit_num(0),
                }}],
                "border": [{"properties": {"show": _lit_bool(False)}}],
                "title": [{"properties": {
                    "show": _lit_bool(True),
                    "text": _lit_str(f"  {brand}  |  {page_title}"),
                    "fontColor": _solid_color("#FFFFFF"),
                    "fontSize": _lit_num(13),
                }}],
            },
        },
        "howCreated": "Default",
    })


# ---- Page navigator writer ----

def write_nav_bar(page_path, page_title):
    """Write a pageNavigator visual for page navigation."""
    write_json(f"{page_path}/visuals/_PageNav/visual.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": make_uuid(f"pagenav.{page_title}"),
        "position": {"x": 0, "y": 40, "z": 999, "width": 1280, "height": 32, "tabOrder": 1},
        "visual": {
            "visualType": "pageNavigator",
            "query": {"queryState": {}},
            "visualContainerObjects": {
                "visualHeader": [{"properties": {"show": _lit_bool(False)}}],
                "background": [{"properties": {
                    "show": _lit_bool(True),
                    "color": _solid_color("#FFFFFF"),
                    "transparency": _lit_num(0),
                }}],
                "border": [{"properties": {"show": _lit_bool(False)}}],
            },
            "objects": {
                "fill": [
                    {"properties": {
                        "show": _lit_bool(True),
                        "fillColor": _solid_color("#EEF3FA"),
                        "transparency": _lit_num(0),
                    }},
                ],
                "text": [
                    {"properties": {
                        "fontColor": _solid_color("#475569"),
                        "fontSize": _lit_num(10),
                        "fontFamily": _lit_str("Segoe UI"),
                    }},
                ],
                "outline": [
                    {"properties": {
                        "weight": _lit_num(1),
                        "outlineColor": _solid_color("#D0DAE8"),
                    }},
                ],
            },
        },
        "howCreated": "Default",
    })


# ---- Report orchestrator ----

def gen_report(schema):
    """Orchestrate writing all report files."""
    pn = schema["project_name"]
    report_base = f"{pn}.Report"
    defn = f"{report_base}/definition"

    # definition.pbir
    write_json(f"{report_base}/definition.pbir", {
        "version": "4.0",
        "datasetReference": {
            "byPath": {
                "path": f"../{pn}.SemanticModel",
            }
        },
    })

    # version.json
    write_json(f"{defn}/version.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0",
    })

    # report.json
    write_json(f"{defn}/report.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.1.0/schema.json",
        "themeCollection": {
            "baseTheme": {
                "name": "CY25SU12",
                "reportVersionAtImport": {
                    "visual": "2.5.0",
                    "report": "3.1.0",
                    "page": "2.3.0",
                },
                "type": "SharedResources",
            }
        },
        "objects": {
            "section": [
                {
                    "properties": {
                        "verticalAlignment": {
                            "expr": {
                                "Literal": {
                                    "Value": "'Top'"
                                }
                            }
                        }
                    }
                }
            ]
        },
        "resourcePackages": [
            {
                "name": "SharedResources",
                "type": "SharedResources",
                "items": [
                    {
                        "name": "CY25SU12",
                        "path": "BaseThemes/CY25SU12.json",
                        "type": "BaseTheme",
                    }
                ],
            }
        ],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
            "useDefaultAggregateDisplayName": True,
        }
    })

    # pages.json
    pages = schema["pages"]
    page_ids = [p["id"] for p in pages]
    write_json(f"{defn}/pages/pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_ids,
        "activePageName": page_ids[0] if page_ids else "",
    })

    # Write each page
    for page_idx, page_config in enumerate(pages):
        page_id = page_config["id"]
        page_title = page_config["title"]
        page_path = f"{defn}/pages/{page_id}"

        # page.json
        write_json(f"{page_path}/page.json", {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
            "name": page_id,
            "displayName": page_title,
            "displayOption": "FitToPage",
            "width": 1280,
            "height": 720,
            "objects": {
                "background": [{
                    "properties": {
                        "color": _solid_color("#F3F6FB"),
                        "transparency": _lit_num(0),
                    }
                }],
            },
        })

        # Header bar
        write_header_bar(page_path, page_title, schema)

        # Page navigator
        write_nav_bar(page_path, page_title)

        tab_order = 2  # 0=header, 1=nav

        # Slicers
        slicers = page_config.get("slicers", [])
        if page_config.get("has_slicers", False) and slicers:
            n_slicers = len(slicers)
            for si, slicer in enumerate(slicers):
                slicer_title = slicer.get("title", f"Slicer{si}")

                # Build query state for slicer
                if "query" in slicer:
                    slicer_qs = _build_query_state({"type": "slicer", "query": slicer["query"]}, schema)
                elif "col" in slicer:
                    table, col = slicer["col"]
                    slicer_qs = {
                        "Values": {"projections": [
                            _projection(_col_field(table, col), f"{table}.{col}", col, True)
                        ]}
                    }
                else:
                    slicer_qs = {}

                # Position
                if n_slicers == 1:
                    sw = slicer.get("w", 1260)
                    sx = 10
                elif n_slicers == 2:
                    sw = 625
                    sx = 10 if si == 0 else 645
                else:
                    # Distribute evenly
                    sw = (1260 - (n_slicers - 1) * 10) // n_slicers
                    sx = 10 + si * (sw + 10)

                slicer_slug = re.sub(r'[^A-Za-z0-9]', '', slicer_title)
                folder_name = f"S{si:02d}_{slicer_slug}"
                write_json(f"{page_path}/visuals/{folder_name}/visual.json", _visual_json(
                    name=make_uuid(f"slicer.{page_id}.{slicer_title}"),
                    visual_type="slicer",
                    x=sx, y=72, w=sw, h=36,
                    tab_order=tab_order,
                    title=slicer_title,
                    query_state=slicer_qs,
                ))
                tab_order += 1

        # Content visuals
        layout = _auto_layout_page(page_config)
        for vi, item in enumerate(layout):
            v = item["visual"]
            vx, vy, vw, vh = item["x"], item["y"], item["w"], item["h"]

            # Build query state
            qs = _build_query_state(v, schema)

            v_title = v.get("title", f"Visual{vi}")
            v_type = v.get("type", "card")
            title_slug = re.sub(r'[^A-Za-z0-9]', '', v_title)
            folder_name = f"V{vi:02d}_{title_slug}"

            write_json(f"{page_path}/visuals/{folder_name}/visual.json", _visual_json(
                name=make_uuid(f"visual.{page_id}.{v_title}"),
                visual_type=v_type,
                x=vx, y=vy, w=vw, h=vh,
                tab_order=tab_order,
                title=v_title,
                query_state=qs,
            ))
            tab_order += 1


# ---- CSV export ----

def gen_csv(data_rows, schema):
    """Export data rows to CSV."""
    write_csv_file("data/sales_data.csv", data_rows)


# ============================================================
# MAIN
# ============================================================

def main():
    schema = SCHEMA
    pn = schema["project_name"]
    print(f"Generating Power BI project: {pn}")
    print(f"Output: {PROJECT_DIR}")
    print()

    # Clean previous
    for d in [f"{pn}.Report", f"{pn}.SemanticModel", "data"]:
        full = os.path.join(PROJECT_DIR, d)
        if os.path.isdir(full):
            shutil.rmtree(full)

    print("[1/5] Generating data...")
    data = generate_data(schema)
    print(f"  Generated {len(data)} rows")

    print("[2/5] Creating project structure...")
    gen_pbip(schema)
    gen_gitignore()

    print("[3/5] Building semantic model (TMDL)...")
    gen_semantic_model(data, schema)

    print("[4/5] Building report (PBIR)...")
    gen_report(schema)

    print("[5/5] Exporting CSV...")
    gen_csv(data, schema)

    print()
    print("=" * 60)
    print("PROJECT GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nOpen: {os.path.join(PROJECT_DIR, pn + '.pbip')}")
    print(f"Pages: {len(schema['pages'])}")
    for p in schema["pages"]:
        print(f"  - {p['title']}")


if __name__ == "__main__":
    main()
