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
    "project_name": "AIPower",
    "brand_label": "REGIONAL SALES",
    "seed": 42,
    "fact_table": "SalesData",

    "date": {
        "years": [2023, 2024],
        "dim_table": "DimDate",
        "key_column": "DateKey",
    },

    "dimensions": [
        {
            "dim_table": "DimCity", "key_column": "CityKey",
            "columns": [
                {"name": "CityKey", "type": "string"},
                {"name": "City", "type": "string"},
                {"name": "State", "type": "string"},
                {"name": "Region", "type": "string"},
            ],
            "values": [
                {"CityKey": "VIC-Melbourne", "City": "Melbourne", "State": "VIC", "Region": "South"},
                {"CityKey": "NSW-Sydney", "City": "Sydney", "State": "NSW", "Region": "East"},
                {"CityKey": "QLD-Brisbane", "City": "Brisbane", "State": "QLD", "Region": "North"},
                {"CityKey": "WA-Perth", "City": "Perth", "State": "WA", "Region": "West"},
                {"CityKey": "SA-Adelaide", "City": "Adelaide", "State": "SA", "Region": "South"},
                {"CityKey": "ACT-Canberra", "City": "Canberra", "State": "ACT", "Region": "East"},
                {"CityKey": "TAS-Hobart", "City": "Hobart", "State": "TAS", "Region": "South"},
                {"CityKey": "NT-Darwin", "City": "Darwin", "State": "NT", "Region": "North"},
            ],
            "assignment": "cross",
        },
        {
            "dim_table": "DimChannel", "key_column": "ChannelKey",
            "columns": [
                {"name": "ChannelKey", "type": "string"},
                {"name": "Channel", "type": "string"},
            ],
            "values": [
                {"ChannelKey": "Online", "Channel": "Online"},
                {"ChannelKey": "Retail", "Channel": "Retail"},
                {"ChannelKey": "Partner", "Channel": "Partner"},
            ],
            "assignment": "cross",
        },
        {
            "dim_table": "DimSegment", "key_column": "SegmentKey",
            "columns": [
                {"name": "SegmentKey", "type": "string"},
                {"name": "Segment", "type": "string"},
            ],
            "values": [
                {"SegmentKey": "Enterprise", "Segment": "Enterprise"},
                {"SegmentKey": "SMB", "Segment": "SMB"},
                {"SegmentKey": "Consumer", "Segment": "Consumer"},
            ],
            "assignment": "random",
        },
        {
            "dim_table": "DimProduct", "key_column": "ProductKey",
            "columns": [
                {"name": "ProductKey", "type": "string"},
                {"name": "ProductCategory", "type": "string"},
            ],
            "values": [
                {"ProductKey": "Hardware", "ProductCategory": "Hardware"},
                {"ProductKey": "Software", "ProductCategory": "Software"},
                {"ProductKey": "Services", "ProductCategory": "Services"},
                {"ProductKey": "Accessories", "ProductCategory": "Accessories"},
            ],
            "assignment": "random",
        },
    ],

    "fact_columns": [
        {"name": "Territory", "type": "string", "summarize": "none", "gen": {"type": "from_dim", "dim": "DimCity", "col": "State"}},
        {"name": "SalesStage", "type": "string", "summarize": "none", "gen": {"type": "random_choice", "choices": ["1-Qualify", "2-Develop", "3-Propose", "4-Close"]}},
        {"name": "WinLossStatus", "type": "string", "summarize": "none", "gen": {"type": "weighted_choice", "choices": ["Won", "Lost"], "weights": [0.72, 0.28]}},
        {"name": "Revenue", "type": "double", "summarize": "sum", "gen": {"type": "random_float", "min": 5000, "max": 200000, "decimals": 2}},
        {"name": "RevenueTarget", "type": "double", "summarize": "sum", "gen": {"type": "random_float", "min": 5000, "max": 220000, "decimals": 2}},
        {"name": "PipelineAmount", "type": "double", "summarize": "sum", "gen": {"type": "random_float", "min": 6000, "max": 300000, "decimals": 2}},
        {"name": "ForecastPct", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 50, "max": 150, "decimals": 2}},
        {"name": "Orders", "type": "int64", "summarize": "sum", "gen": {"type": "random_int", "min": 5, "max": 600}},
        {"name": "OrdersTarget", "type": "int64", "summarize": "sum", "gen": {"type": "random_int", "min": 5, "max": 660}},
        {"name": "AvgOrderValue", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 100, "max": 1500, "decimals": 2}},
        {"name": "DiscountPct", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 2.0, "max": 12.0, "decimals": 2}},
        {"name": "COGS", "type": "double", "summarize": "sum", "gen": {"type": "random_float", "min": 3000, "max": 150000, "decimals": 2}},
        {"name": "GrossProfit", "type": "double", "summarize": "sum", "gen": {"type": "random_float", "min": 2000, "max": 80000, "decimals": 2}},
        {"name": "TurnaroundDays", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 1.0, "max": 5.0, "decimals": 2}},
        {"name": "TurnaroundTargetDays", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 1.5, "max": 4.0, "decimals": 2}},
        {"name": "OnlinePercent", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 15, "max": 80, "decimals": 2}},
        {"name": "SatisfactionScore", "type": "double", "summarize": "average", "gen": {"type": "random_float", "min": 3.5, "max": 4.9, "decimals": 2}},
    ],

    "measures": [
        {"name": "Total Revenue", "dax": "SUM(SalesData[Revenue])", "format": "$#,##0"},
        {"name": "Revenue Won", "dax": "CALCULATE(SUM(SalesData[Revenue]), SalesData[WinLossStatus] = \"Won\")", "format": "$#,##0"},
        {"name": "Qualified Pipeline", "dax": "SUM(SalesData[PipelineAmount])", "format": "$#,##0"},
        {"name": "Total Revenue Target", "dax": "SUM(SalesData[RevenueTarget])", "format": "$#,##0"},
        {"name": "Revenue Variance", "dax": "[Total Revenue] - [Total Revenue Target]", "format": "$#,##0"},
        {"name": "Revenue Attainment %", "dax": "DIVIDE([Total Revenue], [Total Revenue Target])", "format": "#,##0.0\"%\""},
        {"name": "Total Orders", "dax": "SUM(SalesData[Orders])", "format": "#,##0"},
        {"name": "Total Orders Target", "dax": "SUM(SalesData[OrdersTarget])", "format": "#,##0"},
        {"name": "Total Gross Profit", "dax": "SUM(SalesData[GrossProfit])", "format": "$#,##0"},
        {"name": "Gross Margin %", "dax": "DIVIDE([Total Gross Profit], [Total Revenue])", "format": "#,##0.0\"%\""},
        {"name": "Avg Order Value", "dax": "AVERAGE(SalesData[AvgOrderValue])", "format": "$#,##0.00"},
        {"name": "Avg Turnaround Days", "dax": "AVERAGE(SalesData[TurnaroundDays])", "format": "#,##0.00"},
        {"name": "Turnaround Target Days", "dax": "AVERAGE(SalesData[TurnaroundTargetDays])", "format": "#,##0.00"},
        {"name": "Turnaround Gap", "dax": "[Avg Turnaround Days] - [Turnaround Target Days]", "format": "#,##0.00"},
        {"name": "Avg Discount %", "dax": "AVERAGE(SalesData[DiscountPct])", "format": "#,##0.00\"%\""},
        {"name": "Forecast %", "dax": "AVERAGE(SalesData[ForecastPct])", "format": "#,##0.0\"%\""},
        {"name": "Avg Satisfaction", "dax": "AVERAGE(SalesData[SatisfactionScore])", "format": "#,##0.00"},
        {"name": "Avg Online %", "dax": "AVERAGE(SalesData[OnlinePercent])", "format": "#,##0.0\"%\""},
        {"name": "Online Revenue", "dax": "CALCULATE(SUM(SalesData[Revenue]), SalesData[Channel] = \"Online\")", "format": "$#,##0"},
        {"name": "Online Revenue %", "dax": "DIVIDE([Online Revenue], [Total Revenue])", "format": "#,##0.0\"%\""},
    ],

    "relationships": [
        {"from": "SalesData.DateKey", "to": "DimDate.DateKey"},
        {"from": "SalesData.CityKey", "to": "DimCity.CityKey"},
        {"from": "SalesData.ChannelKey", "to": "DimChannel.ChannelKey"},
        {"from": "SalesData.SegmentKey", "to": "DimSegment.SegmentKey"},
        {"from": "SalesData.ProductKey", "to": "DimProduct.ProductKey"},
    ],

    "m_preprocessing": {
        "text_trim": ["City", "State", "Region", "Month", "Channel", "Segment", "ProductCategory"],
        "null_fill_text": ["City", "State", "Region", "Channel", "Segment", "ProductCategory"],
        "normalize": [
            {"column": "OnlinePercent", "min": 0, "max": 100},
            {"column": "DiscountPct", "min": 0, "max": 100},
            {"column": "SatisfactionScore", "min": 1, "max": 5},
        ],
        "add_sort_key": {"name": "YearMonthKey", "expr": "[Year] * 100 + [MonthNum]", "type": "Int64.Type"},
        "sort_by": [["YearMonthKey", "Ascending"], ["City", "Ascending"], ["Channel", "Ascending"]],
        "drop_columns": ["YearMonthKey"],
        "filter_expr": "[Revenue] >= 0 and [Orders] > 0 and [TurnaroundDays] >= 0",
    },

    "sort_by_column": {"Month": "MonthNum", "YearMonth": "YearMonthSort"},

    "pages": [
        # ── Page 1: Executive Overview ──
        {"id": "exec01", "title": "Executive Overview", "has_slicers": False, "slicers": [], "visuals": [
            {"type": "card", "title": "Revenue Won", "query": {"Values": [{"measure": "Revenue Won"}]}},
            {"type": "card", "title": "Qualified Pipeline", "query": {"Values": [{"measure": "Qualified Pipeline"}]}},
            {"type": "card", "title": "Revenue Goal", "query": {"Values": [{"agg_col": ["RevenueTarget", 0]}]}},
            {"type": "card", "title": "Forecast %", "query": {"Values": [{"measure": "Forecast %"}]}},
            {"type": "donutChart", "title": "Revenue by Region", "query": {
                "Category": [{"col": ["DimCity", "Region"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "lineClusteredColumnComboChart", "title": "Revenue & Orders Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}],
                "Y": [{"agg_col": ["Revenue", 0]}], "Y2": [{"agg_col": ["Orders", 0]}]}},
            {"type": "clusteredBarChart", "title": "Revenue by City", "query": {
                "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "areaChart", "title": "Monthly Revenue Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "tableEx", "title": "Executive Summary", "query": {"Values": [
                {"col": ["DimCity", "City"]}, {"col": ["DimCity", "Region"]},
                {"measure": "Total Revenue"}, {"measure": "Total Orders"}, {"measure": "Avg Order Value"}]}},
            {"type": "funnel", "title": "Revenue by Segment", "query": {
                "Category": [{"col": ["DimSegment", "Segment"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
        ]},

        # ── Page 2: Revenue Analysis ──
        {"id": "revenue02", "title": "Revenue Analysis", "has_slicers": True, "slicers": [
            {"title": "City", "col": ["DimCity", "City"]},
            {"title": "Year", "col": ["DimDate", "Year"]},
        ], "visuals": [
            {"type": "clusteredColumnChart", "title": "Revenue by City & Channel", "query": {
                "Category": [{"col": ["DimCity", "City"]}],
                "Series": [{"col": ["DimChannel", "Channel"]}],
                "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "donutChart", "title": "Revenue by Channel", "query": {
                "Category": [{"col": ["DimChannel", "Channel"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "treemap", "title": "Revenue by State & City", "query": {
                "Group": [{"col": ["DimCity", "State"]}, {"col": ["DimCity", "City"]}],
                "Values": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "lineChart", "title": "Monthly Revenue Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "tableEx", "title": "Revenue Detail", "query": {"Values": [
                {"col": ["DimCity", "City"]}, {"col": ["DimChannel", "Channel"]},
                {"measure": "Total Revenue"}, {"measure": "Total Orders"}]}},
            {"type": "donutChart", "title": "Revenue by Product", "query": {
                "Category": [{"col": ["DimProduct", "ProductCategory"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
        ]},

        # ── Page 3: Turnaround & Performance ──
        {"id": "perf03", "title": "Turnaround & Performance", "has_slicers": True, "slicers": [
            {"title": "City", "col": ["DimCity", "City"]},
            {"title": "Month", "col": ["DimDate", "Month"]},
        ], "visuals": [
            {"type": "clusteredBarChart", "title": "Avg Turnaround Days by City", "query": {
                "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["TurnaroundDays", 1]}]}},
            {"type": "areaChart", "title": "Monthly Turnaround Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["TurnaroundDays", 1]}]}},
            {"type": "waterfallChart", "title": "Revenue Contribution by City", "query": {
                "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "lineChart", "title": "Online % Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["OnlinePercent", 1]}]}},
            {"type": "tableEx", "title": "Performance Detail", "query": {"Values": [
                {"col": ["DimCity", "City"]},
                {"measure": "Avg Turnaround Days"}, {"measure": "Avg Online %"}, {"measure": "Total Revenue"}]}},
            {"type": "donutChart", "title": "Revenue by Channel", "query": {
                "Category": [{"col": ["DimChannel", "Channel"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
        ]},

        # ── Page 4: City Comparison ──
        {"id": "city04", "title": "City Comparison", "has_slicers": True, "slicers": [
            {"title": "Select Cities", "col": ["DimCity", "City"], "w": 1260},
        ], "visuals": [
            {"type": "clusteredBarChart", "title": "City Revenue Ranking", "query": {
                "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "clusteredBarChart", "title": "City Orders Ranking", "query": {
                "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["Orders", 0]}]}},
            {"type": "donutChart", "title": "Revenue Share by City", "query": {
                "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "clusteredBarChart", "title": "City Turnaround Ranking", "query": {
                "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["TurnaroundDays", 1]}]}},
            {"type": "tableEx", "title": "City Comparison", "query": {"Values": [
                {"col": ["DimCity", "City"]},
                {"measure": "Total Revenue"}, {"measure": "Total Orders"}, {"measure": "Avg Turnaround Days"}]}},
            {"type": "lineChart", "title": "Revenue Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
        ]},

        # ── Page 5: Channel & Product Mix ──
        {"id": "channel05", "title": "Channel & Product Mix", "has_slicers": True, "slicers": [
            {"title": "Channel", "col": ["DimChannel", "Channel"]},
            {"title": "Year", "col": ["DimDate", "Year"]},
        ], "visuals": [
            {"type": "funnel", "title": "Revenue by Segment", "query": {
                "Category": [{"col": ["DimSegment", "Segment"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "donutChart", "title": "Revenue by Channel", "query": {
                "Category": [{"col": ["DimChannel", "Channel"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "treemap", "title": "Revenue by Product Category", "query": {
                "Group": [{"col": ["DimProduct", "ProductCategory"]}],
                "Values": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "clusteredBarChart", "title": "Revenue by Region & Channel", "query": {
                "Category": [{"col": ["DimCity", "Region"]}],
                "Series": [{"col": ["DimChannel", "Channel"]}],
                "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "tableEx", "title": "Channel Detail", "query": {"Values": [
                {"col": ["DimChannel", "Channel"]}, {"col": ["DimProduct", "ProductCategory"]},
                {"measure": "Total Revenue"}, {"measure": "Total Gross Profit"}]}},
            {"type": "clusteredBarChart", "title": "Satisfaction by Segment", "query": {
                "Category": [{"col": ["DimSegment", "Segment"]}], "Y": [{"measure": "Avg Satisfaction"}]}},
        ]},

        # ── Page 6: Target & KPI Tracking ──
        {"id": "target06", "title": "Target & KPI Tracking", "has_slicers": True, "slicers": [
            {"title": "City", "col": ["DimCity", "City"]},
            {"title": "Year", "col": ["DimDate", "Year"]},
        ], "visuals": [
            {"type": "lineClusteredColumnComboChart", "title": "Revenue vs Target", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}],
                "Y": [{"agg_col": ["Revenue", 0]}], "Y2": [{"agg_col": ["RevenueTarget", 0]}]}},
            {"type": "lineClusteredColumnComboChart", "title": "Orders vs Target", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}],
                "Y": [{"agg_col": ["Orders", 0]}], "Y2": [{"agg_col": ["OrdersTarget", 0]}]}},
            {"type": "waterfallChart", "title": "Revenue Contribution by City", "query": {
                "Category": [{"col": ["DimCity", "City"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
            {"type": "clusteredBarChart", "title": "Turnaround vs Target by City", "query": {
                "Category": [{"col": ["DimCity", "City"]}],
                "Y": [{"agg_col": ["TurnaroundDays", 1]}, {"agg_col": ["TurnaroundTargetDays", 1]}]}},
            {"type": "tableEx", "title": "Target Detail", "query": {"Values": [
                {"col": ["DimCity", "City"]},
                {"measure": "Total Revenue"}, {"measure": "Total Revenue Target"}, {"measure": "Total Orders"}]}},
            {"type": "areaChart", "title": "Revenue Trend", "query": {
                "Category": [{"col": ["DimDate", "YearMonth"]}], "Y": [{"agg_col": ["Revenue", 0]}]}},
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
    """Generate or load data rows from SCHEMA config.

    If data_source.type == "csv", reads from a CSV file.
    Otherwise generates synthetic data from SCHEMA gen specs.
    """
    data_source = schema.get("data_source", {"type": "generated"})
    if isinstance(data_source, dict) and data_source.get("type") == "csv":
        return _load_csv_data(schema)

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


def _load_csv_data(schema):
    """Load data from a CSV file and map to SCHEMA columns."""
    data_source = schema["data_source"]
    csv_path = data_source["path"]

    # Resolve path relative to generate_project.py
    full_path = os.path.join(PROJECT_DIR, csv_path)
    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"CSV file not found: {full_path}")

    # Read CSV (utf-8-sig handles BOM from Excel exports)
    with open(full_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)
    if not raw_rows:
        raise ValueError(f"CSV file is empty: {full_path}")

    # Column mapping: {schema_column_name: csv_column_name}
    col_map = data_source.get("column_mapping", {})

    # Build type map from all SCHEMA columns
    type_map = {}
    date_cfg = schema["date"]
    type_map[date_cfg["key_column"]] = "int64"
    for dim in schema.get("dimensions", []):
        for c in dim["columns"]:
            type_map[c["name"]] = c["type"]
    for fc in schema.get("fact_columns", []):
        type_map[fc["name"]] = fc["type"]
    # Standard date value columns
    for name, typ in [("Year", "int64"), ("Quarter", "string"), ("Month", "string"),
                      ("MonthNum", "int64"), ("YearMonth", "string"), ("YearMonthSort", "int64")]:
        type_map[name] = typ

    # Check if we need to derive date columns from a date_column
    date_column = data_source.get("date_column")  # e.g. "Date" (YYYY-MM-DD format)

    rows = []
    for raw in raw_rows:
        row = {}

        # If date_column is specified, parse it to derive date fields
        if date_column:
            csv_date_col = col_map.get(date_column, date_column)
            date_str = raw.get(csv_date_col, "")
            if date_str:
                # Parse YYYY-MM-DD or YYYY-MM or MM/DD/YYYY
                try:
                    if "/" in date_str:
                        parts = date_str.split("/")
                        if len(parts[2]) == 4:  # MM/DD/YYYY
                            year, month_idx = int(parts[2]), int(parts[0])
                        else:  # MM/DD/YY — add 2000 for 2-digit years
                            year = int(parts[2])
                            if year < 100:
                                year += 2000
                            month_idx = int(parts[0])
                    elif "-" in date_str:
                        parts = date_str.split("-")
                        year, month_idx = int(parts[0]), int(parts[1])
                    else:
                        year, month_idx = 2024, 1
                except (ValueError, IndexError):
                    year, month_idx = 2024, 1

                dk = year * 100 + month_idx
                row[date_cfg["key_column"]] = dk
                row["Year"] = year
                row["Quarter"] = f"Q{((month_idx - 1) // 3) + 1}"
                row["Month"] = MONTH_NAMES[month_idx - 1] if 1 <= month_idx <= 12 else "January"
                row["MonthNum"] = month_idx
                row["YearMonth"] = f"{year}-{month_idx:02d}"
                row["YearMonthSort"] = dk

        # Map all other columns
        for schema_col, col_type in type_map.items():
            if schema_col in row:
                continue  # Already set (e.g. date fields)
            csv_col = col_map.get(schema_col, schema_col)
            if csv_col in raw:
                val = raw[csv_col].strip() if raw[csv_col] else ""
                if col_type == "int64":
                    try:
                        row[schema_col] = int(float(val)) if val else 0
                    except ValueError:
                        row[schema_col] = 0
                elif col_type == "double":
                    try:
                        row[schema_col] = round(float(val), 2) if val else 0.0
                    except ValueError:
                        row[schema_col] = 0.0
                else:
                    row[schema_col] = val
            else:
                # Column not in CSV — use type-appropriate default
                if col_type == "int64":
                    row[schema_col] = 0
                elif col_type == "double":
                    row[schema_col] = 0.0
                else:
                    row[schema_col] = ""

        rows.append(row)

    print(f"  Loaded {len(rows)} rows from {csv_path}")
    return rows


def _auto_populate_dim_values(data_rows, schema):
    """Auto-populate dimension values from loaded data when not explicitly provided.

    Call this after generate_data() when using CSV data source.
    Modifies schema dimensions in-place.
    """
    for dim in schema.get("dimensions", []):
        if dim.get("values"):
            continue  # Already has explicit values
        cols = dim["columns"]
        seen = set()
        values = []
        for row in data_rows:
            key = tuple(row.get(c["name"], "") for c in cols)
            if key not in seen:
                seen.add(key)
                val = {c["name"]: row.get(c["name"], "") for c in cols}
                values.append(val)
        dim["values"] = sorted(values, key=lambda v: v[cols[0]["name"]])
        print(f"  Auto-extracted {len(values)} unique values for {dim['dim_table']}")


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

    # Calculated columns (DAX-computed, no sourceColumn)
    for cc in schema.get("calculated_columns", []):
        name = cc["name"]
        dax = cc["dax"]
        dtype = tmdl_type_map.get(cc.get("type", "double"), "double")
        summarize = cc.get("summarize", "none")
        fmt = cc.get("format", "")
        slug = re.sub(r'[^A-Za-z0-9]', '', name)
        lines.append(f"\tcolumn '{name}' = {dax}")
        lines.append(f'\t\tdataType: {dtype}')
        lines.append(f'\t\tlineageTag: {make_uuid("calcCol." + slug)}')
        lines.append(f'\t\tsummarizeBy: {summarize}')
        if fmt:
            lines.append(f'\t\tformatString: {fmt}')
        lines.append(f'\t\tisDataTypeInferred: true')
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
                name=make_uuid(f"visual.{page_id}.{vi}.{v_title}"),
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
    pn = schema["project_name"]
    data_source = schema.get("data_source", {"type": "generated"})
    if isinstance(data_source, dict) and data_source.get("type") == "csv":
        # Copy source CSV to output data/ folder
        src = os.path.join(PROJECT_DIR, data_source["path"])
        dst = os.path.join(PROJECT_DIR, f"data/{pn}_data.csv")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  Copied: data/{pn}_data.csv")
    else:
        write_csv_file(f"data/{pn}_data.csv", data_rows)


# ============================================================
# MAIN
# ============================================================

def main():
    schema = SCHEMA
    pn = schema["project_name"]
    print(f"Generating Power BI project: {pn}")
    print(f"Output: {PROJECT_DIR}")
    print()

    data_source = schema.get("data_source", {"type": "generated"})
    is_csv = isinstance(data_source, dict) and data_source.get("type") == "csv"

    # Load data BEFORE cleanup (CSV source file may be inside project dir)
    if is_csv:
        print(f"[1/5] Loading CSV data from {data_source['path']}...")
    else:
        print("[1/5] Generating data...")
    data = generate_data(schema)
    if is_csv:
        _auto_populate_dim_values(data, schema)
    print(f"  Total rows: {len(data)}")

    # Clean previous output (after data is loaded)
    for d in [f"{pn}.Report", f"{pn}.SemanticModel", "data"]:
        full = os.path.join(PROJECT_DIR, d)
        if os.path.isdir(full):
            shutil.rmtree(full)

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
