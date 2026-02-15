"""
Power BI PBIR Project Generator
Generates a complete Power BI Desktop project (.pbip) with:
- 6-page sales analytics dashboard with slicers on each page
- Enriched TMDL semantic model (multi-year, channel, segment, targets, margins)
- PBIR report definition with chart/table visuals across all pages

Usage:
    python generate_project.py
    Then open AIPower.pbip in Power BI Desktop (Developer Mode with PBIR enabled)
"""

import os
import json
import csv
import uuid
import random
import shutil

# ============================================================
# CONFIG
# ============================================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = "SalesTest"
SAFE_MODE_NO_PREBUILT_VISUALS = False
VISUAL_FILTER_RAW = os.environ.get("AIPOWER_VISUALS", "all").strip()
PRESERVE_MANUAL_REPORT_LAYOUT = False


def _parse_visual_filter(raw: str):
    """Parse visual filter from env var.
    - all: include all visuals
    - none: include no visuals
    - comma list: include listed visual names only
    """
    if not raw:
        return None
    token = raw.lower()
    if token == "all":
        return None
    if token == "none":
        return set()
    return {x.strip() for x in raw.split(",") if x.strip()}

# Deterministic UUIDs based on name (reproducible builds)
def make_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"aipower.{name}"))

# ============================================================
# SAMPLE DATA
# ============================================================
CITIES = [
    ("Melbourne", "VIC"),
    ("Sydney", "NSW"),
    ("Brisbane", "QLD"),
    ("Perth", "WA"),
    ("Adelaide", "SA"),
    ("Canberra", "ACT"),
    ("Hobart", "TAS"),
    ("Darwin", "NT"),
]

MONTHS = [
    ("January", 1), ("February", 2), ("March", 3), ("April", 4),
    ("May", 5), ("June", 6), ("July", 7), ("August", 8),
    ("September", 9), ("October", 10), ("November", 11), ("December", 12),
]
YEARS = [2023, 2024]

# Base revenue per month (AUD) - realistic for B2B/enterprise sales
CITY_BASE_REVENUE = {
    "Sydney": 185000, "Melbourne": 155000, "Brisbane": 95000,
    "Perth": 82000, "Adelaide": 62000, "Canberra": 48000,
    "Hobart": 30000, "Darwin": 24000,
}

# Seasonal multiplier (Australian seasons: summer=Dec-Feb, winter=Jun-Aug)
MONTH_SEASONALITY = {
    1: 0.85, 2: 0.90, 3: 1.05, 4: 1.10, 5: 1.08, 6: 0.95,
    7: 0.88, 8: 0.92, 9: 1.02, 10: 1.12, 11: 1.18, 12: 0.95,
}

# Average turnaround days by city (business days)
CITY_TURNAROUND = {
    "Sydney": 1.8, "Melbourne": 2.1, "Brisbane": 2.4,
    "Perth": 3.5, "Adelaide": 2.6, "Canberra": 1.6,
    "Hobart": 3.8, "Darwin": 4.2,
}

# Orders per $1000 revenue (approximation)
ORDERS_PER_1K = {
    "Sydney": 2.8, "Melbourne": 3.0, "Brisbane": 3.2,
    "Perth": 2.5, "Adelaide": 3.4, "Canberra": 2.2,
    "Hobart": 3.6, "Darwin": 3.0,
}

REGION_BY_STATE = {
    "NSW": "East",
    "VIC": "South",
    "QLD": "North",
    "WA": "West",
    "SA": "South",
    "ACT": "East",
    "TAS": "South",
    "NT": "North",
}

CHANNEL_SPLIT = {
    "Online": 0.42,
    "Retail": 0.35,
    "Partner": 0.23,
}
SEGMENTS = ["Enterprise", "SMB", "Consumer"]
PRODUCT_CATEGORIES = ["Hardware", "Software", "Services", "Accessories"]
SALES_STAGES = ["1-Qualify", "2-Develop", "3-Propose", "4-Close"]
WIN_LOSS_STATUSES = ["Won", "Lost"]

random.seed(42)  # Reproducible

def generate_data():
    """Generate multi-year sales data with channel, targets, and operations fields."""
    rows = []
    for year in YEARS:
        year_growth = 1.0 if year == 2023 else 1.09
        for city, state in CITIES:
            base_rev = CITY_BASE_REVENUE[city]
            base_tat = CITY_TURNAROUND[city]
            base_opm = ORDERS_PER_1K[city]
            region = REGION_BY_STATE[state]
            for month_name, month_num in MONTHS:
                seasonal = MONTH_SEASONALITY[month_num]
                noise = random.uniform(0.92, 1.08)
                total_revenue = round(base_rev * seasonal * noise * year_growth, 2)
                total_orders = max(1, round(total_revenue / 1000 * base_opm * random.uniform(0.9, 1.1)))
                total_target_revenue = round(total_revenue * random.uniform(0.95, 1.10), 2)
                total_target_orders = max(1, round(total_orders * random.uniform(0.95, 1.10)))
                year_month_sort = year * 100 + month_num
                year_month = f"{year}-{month_num:02d}"
                date_key = year_month_sort
                quarter = f"Q{((month_num - 1) // 3) + 1}"
                for channel, split in CHANNEL_SPLIT.items():
                    channel_weight = split * random.uniform(0.9, 1.1)
                    revenue = round(total_revenue * channel_weight, 2)
                    orders = max(1, round(total_orders * channel_weight * random.uniform(0.9, 1.1)))
                    avg_order = round(revenue / orders, 2) if orders > 0 else 0
                    discount_pct = round(random.uniform(2.0, 12.0), 2)
                    cogs_ratio = random.uniform(0.52, 0.76)
                    cogs = round(revenue * cogs_ratio, 2)
                    gross_profit = round(revenue - cogs, 2)
                    tat = round(base_tat * random.uniform(0.85, 1.20) + (0.25 if month_num in (6, 7, 8) else 0), 2)
                    target_tat = round(base_tat * random.uniform(0.90, 1.05), 2)
                    # Online engagement % - higher for Online channel, grows over time
                    base_online = 65.0 if channel == "Online" else random.uniform(15.0, 35.0)
                    trend_boost = (year - 2023) * 5 + month_num * 0.3  # gradual growth
                    online_pct = round(min(100.0, base_online + trend_boost + random.uniform(-8, 8)), 2)
                    satisfaction = round(random.uniform(3.5, 4.9), 2)
                    segment = random.choice(SEGMENTS)
                    category = random.choice(PRODUCT_CATEGORIES)
                    stage = random.choice(SALES_STAGES)
                    win_loss = random.choices(WIN_LOSS_STATUSES, weights=[0.72, 0.28], k=1)[0]
                    pipeline_amount = round(revenue * random.uniform(1.10, 1.65), 2)
                    forecast_pct = round((revenue / max(1, total_target_revenue * channel_weight)) * 100, 2)
                    territory = state
                    city_key = f"{state}-{city.replace(' ', '')}"
                    channel_key = channel
                    segment_key = segment
                    product_key = category
                    rows.append({
                        "DateKey": date_key,
                        "CityKey": city_key,
                        "ChannelKey": channel_key,
                        "SegmentKey": segment_key,
                        "ProductKey": product_key,
                        "City": city,
                        "State": state,
                        "Region": region,
                        "Year": year,
                        "Quarter": quarter,
                        "Month": month_name,
                        "MonthNum": month_num,
                        "YearMonth": year_month,
                        "YearMonthSort": year_month_sort,
                        "Channel": channel,
                        "Segment": segment,
                        "ProductCategory": category,
                        "Territory": territory,
                        "SalesStage": stage,
                        "WinLossStatus": win_loss,
                        "Revenue": revenue,
                        "RevenueTarget": round(total_target_revenue * channel_weight, 2),
                        "PipelineAmount": pipeline_amount,
                        "ForecastPct": forecast_pct,
                        "Orders": orders,
                        "OrdersTarget": max(1, round(total_target_orders * channel_weight)),
                        "AvgOrderValue": avg_order,
                        "DiscountPct": discount_pct,
                        "COGS": cogs,
                        "GrossProfit": gross_profit,
                        "TurnaroundDays": tat,
                        "TurnaroundTargetDays": target_tat,
                        "OnlinePercent": online_pct,
                        "SatisfactionScore": satisfaction,
                    })
    return rows

# ============================================================
# FILE GENERATORS
# ============================================================

def write_file(rel_path: str, content: str):
    """Write a file relative to PROJECT_DIR.
    All PBIP files use UTF-8 without BOM per Microsoft docs."""
    full_path = os.path.join(PROJECT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print(f"  Created: {rel_path}")

def write_json(rel_path: str, obj: dict):
    """Write a JSON file."""
    write_file(rel_path, json.dumps(obj, indent=2, ensure_ascii=False))

def write_csv_file(rel_path: str, rows: list):
    """Write a CSV file."""
    full_path = os.path.join(PROJECT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(full_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Created: {rel_path}")


# ---- Project entry point ----

def gen_pbip():
    write_json(f"{PROJECT_NAME}.pbip", {
        "version": "1.0",
        "artifacts": [
            {
                "report": {
                    "path": f"{PROJECT_NAME}.Report"
                }
            }
        ],
        "settings": {
            "enableAutoRecovery": True
        }
    })

def gen_gitignore():
    write_file(".gitignore", """**/.pbi/localSettings.json
**/.pbi/cache.abf
*.pbix
__pycache__/
""")


# ---- Semantic Model (TMDL) ----

def gen_semantic_model(data_rows):
    # definition.pbism
    write_json(f"{PROJECT_NAME}.SemanticModel/definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0"
    })

    # model.tmdl
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/model.tmdl",
        'model Model\n'
        '\tculture: en-AU\n'
        '\tdefaultPowerBIDataSourceVersion: powerBI_V3\n'
    )

    # Build embedded M expression with data
    m_rows = []
    for r in data_rows:
        m_rows.append(
            f'\t\t\t\t\t\t{{'
            f'{r["DateKey"]}, "{r["CityKey"]}", "{r["ChannelKey"]}", "{r["SegmentKey"]}", "{r["ProductKey"]}", '
            f'"{r["City"]}", "{r["State"]}", "{r["Region"]}", {r["Year"]}, "{r["Quarter"]}", '
            f'"{r["Month"]}", {r["MonthNum"]}, "{r["YearMonth"]}", {r["YearMonthSort"]}, '
            f'"{r["Channel"]}", "{r["Segment"]}", "{r["ProductCategory"]}", '
            f'"{r["Territory"]}", "{r["SalesStage"]}", "{r["WinLossStatus"]}", '
            f'{r["Revenue"]}, {r["RevenueTarget"]}, {r["PipelineAmount"]}, {r["ForecastPct"]}, '
            f'{r["Orders"]}, {r["OrdersTarget"]}, '
            f'{r["AvgOrderValue"]}, {r["DiscountPct"]}, {r["COGS"]}, {r["GrossProfit"]}, '
            f'{r["TurnaroundDays"]}, {r["TurnaroundTargetDays"]}, {r["OnlinePercent"]}, {r["SatisfactionScore"]}'
            f'}}'
        )
    m_data_literal = ",\n".join(m_rows)

    m_expression = (
        'let\n'
        '\t\t\t\tSource = #table(\n'
        '\t\t\t\t\ttype table [\n'
        '\t\t\t\t\t\tDateKey = Int64.Type,\n'
        '\t\t\t\t\t\tCityKey = text, ChannelKey = text, SegmentKey = text, ProductKey = text,\n'
        '\t\t\t\t\t\tCity = text, State = text, Region = text,\n'
        '\t\t\t\t\t\tYear = Int64.Type, Quarter = text, Month = text,\n'
        '\t\t\t\t\t\tMonthNum = Int64.Type, YearMonth = text, YearMonthSort = Int64.Type,\n'
        '\t\t\t\t\t\tChannel = text, Segment = text, ProductCategory = text,\n'
        '\t\t\t\t\t\tTerritory = text, SalesStage = text, WinLossStatus = text,\n'
        '\t\t\t\t\t\tRevenue = number, RevenueTarget = number, PipelineAmount = number, ForecastPct = number,\n'
        '\t\t\t\t\t\tOrders = Int64.Type, OrdersTarget = Int64.Type,\n'
        '\t\t\t\t\t\tAvgOrderValue = number, DiscountPct = number, COGS = number, GrossProfit = number,\n'
        '\t\t\t\t\t\tTurnaroundDays = number, TurnaroundTargetDays = number,\n'
        '\t\t\t\t\t\tOnlinePercent = number, SatisfactionScore = number\n'
        '\t\t\t\t\t],\n'
        '\t\t\t\t\t{\n'
        f'{m_data_literal}\n'
        '\t\t\t\t\t}\n'
        '\t\t\t\t),\n'
        '\t\t\t\tCleanText = Table.TransformColumns(\n'
        '\t\t\t\t\tSource,\n'
        '\t\t\t\t\t{\n'
        '\t\t\t\t\t\t{"City", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"State", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Region", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Month", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Channel", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Segment", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"ProductCategory", each Text.Trim(_), type text}\n'
        '\t\t\t\t\t}\n'
        '\t\t\t\t),\n'
        '\t\t\t\tFillMissingText = Table.ReplaceValue(CleanText, null, "Unknown", Replacer.ReplaceValue, {"City", "State", "Region", "Channel", "Segment", "ProductCategory"}),\n'
        '\t\t\t\tNormalizeMetrics = Table.TransformColumns(\n'
        '\t\t\t\t\tFillMissingText,\n'
        '\t\t\t\t\t{\n'
        '\t\t\t\t\t\t{"OnlinePercent", each if _ < 0 then 0 else if _ > 100 then 100 else _, type number},\n'
        '\t\t\t\t\t\t{"DiscountPct", each if _ < 0 then 0 else if _ > 100 then 100 else _, type number},\n'
        '\t\t\t\t\t\t{"SatisfactionScore", each if _ < 1 then 1 else if _ > 5 then 5 else _, type number}\n'
        '\t\t\t\t\t}\n'
        '\t\t\t\t),\n'
        '\t\t\t\tAddSortKey = Table.AddColumn(NormalizeMetrics, "YearMonthKey", each [Year] * 100 + [MonthNum], Int64.Type),\n'
        '\t\t\t\tSortRows = Table.Sort(AddSortKey, {{"YearMonthKey", Order.Ascending}, {"City", Order.Ascending}, {"Channel", Order.Ascending}}),\n'
        '\t\t\t\tDropHelper = Table.RemoveColumns(SortRows, {"YearMonthKey"}),\n'
        '\t\t\t\tFilterInvalid = Table.SelectRows(DropHelper, each [Revenue] >= 0 and [Orders] > 0 and [TurnaroundDays] >= 0)\n'
        '\t\t\tin\n'
        '\t\t\t\tFilterInvalid'
    )

    # SalesData.tmdl - Table definition with columns, measures, and partition
    tmdl = (
        f'table SalesData\n'
        f'\tlineageTag: {make_uuid("table.SalesData")}\n'
        f'\n'
        # ---- Measures ----
        f'\tmeasure \'Total Revenue\' = SUM(SalesData[Revenue])\n'
        f'\t\tformatString: $#,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalRevenue")}\n'
        f'\n'
        f'\tmeasure \'Revenue Won\' = CALCULATE(SUM(SalesData[Revenue]), SalesData[WinLossStatus] = "Won")\n'
        f'\t\tformatString: $#,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.RevenueWon")}\n'
        f'\n'
        f'\tmeasure \'Qualified Pipeline\' = SUM(SalesData[PipelineAmount])\n'
        f'\t\tformatString: $#,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.QualifiedPipeline")}\n'
        f'\n'
        f'\tmeasure \'Total Revenue Target\' = SUM(SalesData[RevenueTarget])\n'
        f'\t\tformatString: $#,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalRevenueTarget")}\n'
        f'\n'
        f'\tmeasure \'Revenue Variance\' = [Total Revenue] - [Total Revenue Target]\n'
        f'\t\tformatString: $#,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.RevenueVariance")}\n'
        f'\n'
        f'\tmeasure \'Revenue Attainment %\' = DIVIDE([Total Revenue], [Total Revenue Target])\n'
        f'\t\tformatString: #,##0.0"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.RevenueAttainmentPct")}\n'
        f'\n'
        f'\tmeasure \'Total Orders\' = SUM(SalesData[Orders])\n'
        f'\t\tformatString: #,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalOrders")}\n'
        f'\n'
        f'\tmeasure \'Total Orders Target\' = SUM(SalesData[OrdersTarget])\n'
        f'\t\tformatString: #,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalOrdersTarget")}\n'
        f'\n'
        f'\tmeasure \'Total Gross Profit\' = SUM(SalesData[GrossProfit])\n'
        f'\t\tformatString: $#,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalGrossProfit")}\n'
        f'\n'
        f'\tmeasure \'Gross Margin %\' = DIVIDE([Total Gross Profit], [Total Revenue])\n'
        f'\t\tformatString: #,##0.0"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.GrossMarginPct")}\n'
        f'\n'
        f'\tmeasure \'Avg Order Value\' = AVERAGE(SalesData[AvgOrderValue])\n'
        f'\t\tformatString: $#,##0.00\n'
        f'\t\tlineageTag: {make_uuid("measure.AvgOrderValue")}\n'
        f'\n'
        f'\tmeasure \'Avg Turnaround Days\' = AVERAGE(SalesData[TurnaroundDays])\n'
        f'\t\tformatString: #,##0.00\n'
        f'\t\tlineageTag: {make_uuid("measure.AvgTurnaround")}\n'
        f'\n'
        f'\tmeasure \'Turnaround Target Days\' = AVERAGE(SalesData[TurnaroundTargetDays])\n'
        f'\t\tformatString: #,##0.00\n'
        f'\t\tlineageTag: {make_uuid("measure.TurnaroundTargetDays")}\n'
        f'\n'
        f'\tmeasure \'Turnaround Gap\' = [Avg Turnaround Days] - [Turnaround Target Days]\n'
        f'\t\tformatString: #,##0.00\n'
        f'\t\tlineageTag: {make_uuid("measure.TurnaroundGap")}\n'
        f'\n'
        f'\tmeasure \'Avg Discount %\' = AVERAGE(SalesData[DiscountPct])\n'
        f'\t\tformatString: #,##0.00"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.AvgDiscountPct")}\n'
        f'\n'
        f'\tmeasure \'Forecast %\' = AVERAGE(SalesData[ForecastPct])\n'
        f'\t\tformatString: #,##0.0"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.ForecastPct")}\n'
        f'\n'
        f'\tmeasure \'Avg Satisfaction\' = AVERAGE(SalesData[SatisfactionScore])\n'
        f'\t\tformatString: #,##0.00\n'
        f'\t\tlineageTag: {make_uuid("measure.AvgSatisfaction")}\n'
        f'\n'
        f'\tmeasure \'Avg Online %\' = AVERAGE(SalesData[OnlinePercent])\n'
        f'\t\tformatString: #,##0.0"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.AvgOnlinePct")}\n'
        f'\n'
        f'\tmeasure \'Online Revenue\' = CALCULATE(SUM(SalesData[Revenue]), SalesData[Channel] = "Online")\n'
        f'\t\tformatString: $#,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.OnlineRevenue")}\n'
        f'\n'
        f'\tmeasure \'Online Revenue %\' = DIVIDE([Online Revenue], [Total Revenue])\n'
        f'\t\tformatString: #,##0.0"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.OnlineRevPct")}\n'
        f'\n'
        # ---- Columns ----
        f'\tcolumn DateKey\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.DateKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: DateKey\n'
        f'\n'
        f'\tcolumn CityKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.CityKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: CityKey\n'
        f'\n'
        f'\tcolumn ChannelKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.ChannelKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: ChannelKey\n'
        f'\n'
        f'\tcolumn SegmentKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.SegmentKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: SegmentKey\n'
        f'\n'
        f'\tcolumn ProductKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.ProductKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: ProductKey\n'
        f'\n'
        f'\tcolumn City\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.City")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: City\n'
        f'\n'
        f'\tcolumn State\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.State")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: State\n'
        f'\n'
        f'\tcolumn Region\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Region")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Region\n'
        f'\n'
        f'\tcolumn Year\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.Year")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Year\n'
        f'\n'
        f'\tcolumn Quarter\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Quarter")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Quarter\n'
        f'\n'
        f'\tcolumn Month\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Month")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Month\n'
        f'\t\tsortByColumn: MonthNum\n'
        f'\n'
        f'\tcolumn MonthNum\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.MonthNum")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: MonthNum\n'
        f'\n'
        f'\tcolumn YearMonth\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.YearMonth")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: YearMonth\n'
        f'\t\tsortByColumn: YearMonthSort\n'
        f'\n'
        f'\tcolumn YearMonthSort\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.YearMonthSort")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: YearMonthSort\n'
        f'\n'
        f'\tcolumn Channel\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Channel")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Channel\n'
        f'\n'
        f'\tcolumn Segment\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Segment")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Segment\n'
        f'\n'
        f'\tcolumn ProductCategory\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.ProductCategory")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: ProductCategory\n'
        f'\n'
        f'\tcolumn Territory\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Territory")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Territory\n'
        f'\n'
        f'\tcolumn SalesStage\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.SalesStage")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: SalesStage\n'
        f'\n'
        f'\tcolumn WinLossStatus\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.WinLossStatus")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: WinLossStatus\n'
        f'\n'
        f'\tcolumn Revenue\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.Revenue")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: Revenue\n'
        f'\n'
        f'\tcolumn RevenueTarget\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.RevenueTarget")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: RevenueTarget\n'
        f'\n'
        f'\tcolumn PipelineAmount\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.PipelineAmount")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: PipelineAmount\n'
        f'\n'
        f'\tcolumn ForecastPct\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.ForecastPct")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: ForecastPct\n'
        f'\n'
        f'\tcolumn Orders\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.Orders")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: Orders\n'
        f'\n'
        f'\tcolumn OrdersTarget\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.OrdersTarget")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: OrdersTarget\n'
        f'\n'
        f'\tcolumn AvgOrderValue\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.AvgOrderValue")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: AvgOrderValue\n'
        f'\n'
        f'\tcolumn DiscountPct\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.DiscountPct")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: DiscountPct\n'
        f'\n'
        f'\tcolumn COGS\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.COGS")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: COGS\n'
        f'\n'
        f'\tcolumn GrossProfit\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.GrossProfit")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: GrossProfit\n'
        f'\n'
        f'\tcolumn TurnaroundDays\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.TurnaroundDays")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: TurnaroundDays\n'
        f'\n'
        f'\tcolumn TurnaroundTargetDays\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.TurnaroundTargetDays")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: TurnaroundTargetDays\n'
        f'\n'
        f'\tcolumn OnlinePercent\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.OnlinePercent")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: OnlinePercent\n'
        f'\n'
        f'\tcolumn SatisfactionScore\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.SatisfactionScore")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: SatisfactionScore\n'
        f'\n'
        # ---- Partition ----
        f'\tpartition SalesData = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\t{m_expression}\n'
    )

    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/SalesData.tmdl", tmdl)

    # Dimension tables for star schema (self-contained M to avoid query dependency load errors)
    def _m_str(text: str) -> str:
        return '"' + str(text).replace('"', '""') + '"'

    dim_date_rows = sorted(
        {
            (r["DateKey"], r["Year"], r["Quarter"], r["Month"], r["MonthNum"], r["YearMonth"])
            for r in data_rows
        },
        key=lambda x: x[0],
    )
    dim_city_rows = sorted(
        {(r["CityKey"], r["City"], r["State"], r["Region"]) for r in data_rows},
        key=lambda x: x[0],
    )
    dim_channel_rows = sorted(
        {(r["ChannelKey"], r["Channel"]) for r in data_rows},
        key=lambda x: x[0],
    )
    dim_segment_rows = sorted(
        {(r["SegmentKey"], r["Segment"]) for r in data_rows},
        key=lambda x: x[0],
    )
    dim_product_rows = sorted(
        {(r["ProductKey"], r["ProductCategory"]) for r in data_rows},
        key=lambda x: x[0],
    )

    dim_date_literal = ",\n".join(
        [
            f'\t\t\t\t\t\t{{{d[0]}, {d[1]}, {_m_str(d[2])}, {_m_str(d[3])}, {d[4]}, {_m_str(d[5])}}}'
            for d in dim_date_rows
        ]
    )
    dim_city_literal = ",\n".join(
        [f'\t\t\t\t\t\t{{{_m_str(c[0])}, {_m_str(c[1])}, {_m_str(c[2])}, {_m_str(c[3])}}}' for c in dim_city_rows]
    )
    dim_channel_literal = ",\n".join(
        [f'\t\t\t\t\t\t{{{_m_str(c[0])}, {_m_str(c[1])}}}' for c in dim_channel_rows]
    )
    dim_segment_literal = ",\n".join(
        [f'\t\t\t\t\t\t{{{_m_str(s[0])}, {_m_str(s[1])}}}' for s in dim_segment_rows]
    )
    dim_product_literal = ",\n".join(
        [f'\t\t\t\t\t\t{{{_m_str(p[0])}, {_m_str(p[1])}}}' for p in dim_product_rows]
    )

    dim_date = (
        f'table DimDate\n'
        f'\tlineageTag: {make_uuid("table.DimDate")}\n'
        f'\n'
        f'\tcolumn DateKey\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.DimDate.DateKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: DateKey\n'
        f'\n'
        f'\tcolumn Year\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.DimDate.Year")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Year\n'
        f'\n'
        f'\tcolumn Quarter\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimDate.Quarter")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Quarter\n'
        f'\n'
        f'\tcolumn Month\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimDate.Month")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Month\n'
        f'\t\tsortByColumn: MonthNum\n'
        f'\n'
        f'\tcolumn MonthNum\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.DimDate.MonthNum")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: MonthNum\n'
        f'\n'
        f'\tcolumn YearMonth\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimDate.YearMonth")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: YearMonth\n'
        f'\t\tsortByColumn: DateKey\n'
        f'\n'
        f'\tpartition DimDate = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [DateKey = Int64.Type, Year = Int64.Type, Quarter = text, Month = text, MonthNum = Int64.Type, YearMonth = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_date_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimDate.tmdl", dim_date)

    dim_city = (
        f'table DimCity\n'
        f'\tlineageTag: {make_uuid("table.DimCity")}\n'
        f'\n'
        f'\tcolumn CityKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimCity.CityKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: CityKey\n'
        f'\n'
        f'\tcolumn City\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimCity.City")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: City\n'
        f'\n'
        f'\tcolumn State\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimCity.State")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: State\n'
        f'\n'
        f'\tcolumn Region\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimCity.Region")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Region\n'
        f'\n'
        f'\tpartition DimCity = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [CityKey = text, City = text, State = text, Region = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_city_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimCity.tmdl", dim_city)

    dim_channel = (
        f'table DimChannel\n'
        f'\tlineageTag: {make_uuid("table.DimChannel")}\n'
        f'\n'
        f'\tcolumn ChannelKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimChannel.ChannelKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: ChannelKey\n'
        f'\n'
        f'\tcolumn Channel\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimChannel.Channel")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Channel\n'
        f'\n'
        f'\tpartition DimChannel = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [ChannelKey = text, Channel = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_channel_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimChannel.tmdl", dim_channel)

    dim_segment = (
        f'table DimSegment\n'
        f'\tlineageTag: {make_uuid("table.DimSegment")}\n'
        f'\n'
        f'\tcolumn SegmentKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimSegment.SegmentKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: SegmentKey\n'
        f'\n'
        f'\tcolumn Segment\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimSegment.Segment")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Segment\n'
        f'\n'
        f'\tpartition DimSegment = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [SegmentKey = text, Segment = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_segment_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimSegment.tmdl", dim_segment)

    dim_product = (
        f'table DimProduct\n'
        f'\tlineageTag: {make_uuid("table.DimProduct")}\n'
        f'\n'
        f'\tcolumn ProductKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimProduct.ProductKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: ProductKey\n'
        f'\n'
        f'\tcolumn ProductCategory\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.DimProduct.ProductCategory")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: ProductCategory\n'
        f'\n'
        f'\tpartition DimProduct = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [ProductKey = text, ProductCategory = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_product_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimProduct.tmdl", dim_product)

    # Relationships for star schema
    relationships_tmdl = (
        f'relationship {make_uuid("rel.SalesData.DateKey->DimDate.DateKey")}\n'
        f'\tfromColumn: SalesData.DateKey\n'
        f'\ttoColumn: DimDate.DateKey\n'
        f'\n'
        f'relationship {make_uuid("rel.SalesData.CityKey->DimCity.CityKey")}\n'
        f'\tfromColumn: SalesData.CityKey\n'
        f'\ttoColumn: DimCity.CityKey\n'
        f'\n'
        f'relationship {make_uuid("rel.SalesData.ChannelKey->DimChannel.ChannelKey")}\n'
        f'\tfromColumn: SalesData.ChannelKey\n'
        f'\ttoColumn: DimChannel.ChannelKey\n'
        f'\n'
        f'relationship {make_uuid("rel.SalesData.SegmentKey->DimSegment.SegmentKey")}\n'
        f'\tfromColumn: SalesData.SegmentKey\n'
        f'\ttoColumn: DimSegment.SegmentKey\n'
        f'\n'
        f'relationship {make_uuid("rel.SalesData.ProductKey->DimProduct.ProductKey")}\n'
        f'\tfromColumn: SalesData.ProductKey\n'
        f'\ttoColumn: DimProduct.ProductKey\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/relationships.tmdl", relationships_tmdl)


# ---- Report (PBIR) ----

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


def gen_report():
    report_base = f"{PROJECT_NAME}.Report"
    defn = f"{report_base}/definition"

    # definition.pbir - points to semantic model
    write_json(f"{report_base}/definition.pbir", {
        "version": "4.0",
        "datasetReference": {
            "byPath": {
                "path": f"../{PROJECT_NAME}.SemanticModel",
            }
        },
    })

    # version.json
    write_json(f"{defn}/version.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0",
    })

    # report.json - report-level settings and base theme
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

    # Six-page comprehensive report
    p_exec = "10b8272ebf47e725ad5d"
    p_revenue = "b1f2c3d4e5f60718293a"
    p_turnaround = "a4d6df077cc9bd1a5763"
    p_city = "c9e4ab7812d34f5601bc"
    p_channel = "d5f7a9bc1e23456789ab"
    p_target = "e6a8bc2d3f45678901cd"

    if SAFE_MODE_NO_PREBUILT_VISUALS:
        page_order = [p_exec]
    else:
        page_order = [p_exec, p_revenue, p_turnaround, p_city, p_channel, p_target]

    write_json(f"{defn}/pages/pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_order,
        "activePageName": p_exec,
    })

    T = "SalesData"
    D_DATE = "DimDate"
    D_CITY = "DimCity"
    D_CHANNEL = "DimChannel"
    D_SEGMENT = "DimSegment"
    D_PRODUCT = "DimProduct"
    visual_filter = _parse_visual_filter(VISUAL_FILTER_RAW)

    def include_visual(name: str) -> bool:
        return visual_filter is None or name in visual_filter

    def write_page(page_id: str, page_title: str):
        write_json(f"{defn}/pages/{page_id}/page.json", {
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

    write_page(p_exec, "Executive Overview")
    write_page(p_revenue, "Revenue Analysis")
    write_page(p_turnaround, "Turnaround & Performance")
    write_page(p_city, "City Comparison")
    write_page(p_channel, "Channel & Product Mix")
    write_page(p_target, "Target & KPI Tracking")

    if SAFE_MODE_NO_PREBUILT_VISUALS:
        return

    # ---- Header banner on every page (dark navy bar like Contoso reference) ----
    def write_header_bar(page_path: str, page_title: str, subtitle: str = "Sales Overview"):
        """Write a dark navy header bar visual at the top of a page."""
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
                        "text": _lit_str(f"  REGIONAL SALES  |  {page_title}"),
                        "fontColor": _solid_color("#FFFFFF"),
                        "fontSize": _lit_num(13),
                    }}],
                },
            },
            "howCreated": "Default",
        })

    def write_nav_bar(page_path: str, active_index: int):
        """Write a pageNavigator visual for actual page navigation."""
        write_json(f"{page_path}/visuals/_PageNav/visual.json", {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
            "name": make_uuid(f"pagenav.{page_path}"),
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

    # ---------- Page 1: Executive Overview (NO slicers - clean exec view) ----------
    page1 = f"{defn}/pages/{p_exec}"
    write_header_bar(page1, "Executive Overview")
    write_nav_bar(page1, active_index=0)

    # 4 KPI Cards (y=72, h=68)
    if include_visual("ExecKPIRevenueWon"):
        write_json(f"{page1}/visuals/ExecKPIRevenueWon/visual.json", _visual_json(
            name="kpi001122334455667788",
            visual_type="card",
            x=10, y=72, w=305, h=68, tab_order=3, title="Revenue Won",
            query_state={
                "Values": {"projections": [_projection(_measure_field(T, "Revenue Won"), "SalesData.Revenue Won", "Revenue Won", True)]},
            },
        ))
    if include_visual("ExecKPIQualifiedPipeline"):
        write_json(f"{page1}/visuals/ExecKPIQualifiedPipeline/visual.json", _visual_json(
            name="kpi112233445566778899",
            visual_type="card",
            x=325, y=72, w=305, h=68, tab_order=4, title="Qualified Pipeline",
            query_state={
                "Values": {"projections": [_projection(_measure_field(T, "Qualified Pipeline"), "SalesData.Qualified Pipeline", "Qualified Pipeline", True)]},
            },
        ))
    if include_visual("ExecKPIRevenueGoal"):
        write_json(f"{page1}/visuals/ExecKPIRevenueGoal/visual.json", _visual_json(
            name="kpi223344556677889900",
            visual_type="card",
            x=640, y=72, w=305, h=68, tab_order=5, title="Revenue Goal",
            query_state={
                "Values": {"projections": [_projection(_agg_col_field(T, "RevenueTarget", 0), "Sum(SalesData.RevenueTarget)", "Revenue Goal", True)]},
            },
        ))
    if include_visual("ExecKPIForecast"):
        write_json(f"{page1}/visuals/ExecKPIForecast/visual.json", _visual_json(
            name="kpi334455667788990011",
            visual_type="card",
            x=955, y=72, w=315, h=68, tab_order=6, title="Forecast %",
            query_state={
                "Values": {"projections": [_projection(_measure_field(T, "Forecast %"), "SalesData.Forecast %", "Forecast %", True)]},
            },
        ))

    # Donut: Revenue by Region (y=146, h=195)
    if include_visual("ExecRevenueByRegion"):
        write_json(f"{page1}/visuals/ExecRevenueByRegion/visual.json", _visual_json(
            name="f1a7b4c29d6e3f8051aa",
            visual_type="donutChart",
            x=10, y=146, w=380, h=195, tab_order=7, title="Revenue by Region",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "Region"), "DimCity.Region", "Region", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Combo: Revenue (bars) + Orders (line) by Month (y=146, h=195)
    if include_visual("ExecRevenueOrdersCombo"):
        write_json(f"{page1}/visuals/ExecRevenueOrdersCombo/visual.json", _visual_json(
            name="c5e8f709a1b2d3c4e5f6",
            visual_type="lineClusteredColumnComboChart",
            x=400, y=146, w=870, h=195, tab_order=8, title="Revenue & Orders Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
                "Y2": {"projections": [_projection(_agg_col_field(T, "Orders", 0), "Sum(SalesData.Orders)", "Orders")]},
            },
        ))

    # Row 2: Bar chart + Area chart (y=347, h=160)
    if include_visual("ExecTopCitiesBar"):
        write_json(f"{page1}/visuals/ExecTopCitiesBar/visual.json", _visual_json(
            name="ba4c1d2e3f4a5b6c7d8e",
            visual_type="clusteredBarChart",
            x=10, y=347, w=625, h=160, tab_order=9, title="Revenue by City",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))
    if include_visual("ExecMonthlyArea"):
        write_json(f"{page1}/visuals/ExecMonthlyArea/visual.json", _visual_json(
            name="ae5d6c7b8a9f0e1d2c3b",
            visual_type="areaChart",
            x=645, y=347, w=625, h=160, tab_order=10, title="Monthly Revenue Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Executive Summary Table (y=513, h=200) - left half
    if include_visual("ExecSummaryTable"):
        write_json(f"{page1}/visuals/ExecSummaryTable/visual.json", _visual_json(
            name="9012ab34cd56ef7890ab",
            visual_type="tableEx",
            x=10, y=513, w=625, h=200, tab_order=11, title="Executive Summary",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(D_CITY, "City"), "DimCity.City", "City"),
                        _projection(_col_field(D_CITY, "Region"), "DimCity.Region", "Region"),
                        _projection(_measure_field(T, "Total Revenue"), "SalesData.Total Revenue", "Revenue"),
                        _projection(_measure_field(T, "Total Orders"), "SalesData.Total Orders", "Orders"),
                        _projection(_measure_field(T, "Avg Order Value"), "SalesData.Avg Order Value", "Avg Order $"),
                    ]
                }
            },
        ))

    # Funnel: Revenue by Segment (y=513, h=200) - right half
    if include_visual("ExecFunnelSegment"):
        write_json(f"{page1}/visuals/ExecFunnelSegment/visual.json", _visual_json(
            name="f2b3c4d5e6a7b8c9d0e1",
            visual_type="funnel",
            x=645, y=513, w=625, h=200, tab_order=12, title="Revenue by Segment",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_SEGMENT, "Segment"), "DimSegment.Segment", "Segment", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # ---------- Page 2: Revenue Analysis (2 slicers + stacked/donut/treemap/line) ----------
    page2 = f"{defn}/pages/{p_revenue}"
    write_header_bar(page2, "Revenue Analysis")
    write_nav_bar(page2, active_index=1)

    # Slicers (y=72, h=36)
    if include_visual("RevSlicerCity"):
        write_json(f"{page2}/visuals/RevSlicerCity/visual.json", _visual_json(
            name="dd44ee55ff66aa77bb88",
            visual_type="slicer",
            x=10, y=72, w=625, h=36, tab_order=0, title="City",
            query_state={"Values": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]}},
        ))
    if include_visual("RevSlicerYear"):
        write_json(f"{page2}/visuals/RevSlicerYear/visual.json", _visual_json(
            name="ee55ff66aa77bb88cc99",
            visual_type="slicer",
            x=645, y=72, w=625, h=36, tab_order=1, title="Year",
            query_state={"Values": {"projections": [_projection(_col_field(D_DATE, "Year"), "DimDate.Year", "Year", True)]}},
        ))

    # Grouped Column: Revenue by Channel per City (y=112, h=200)
    if include_visual("RevStackedByChannel"):
        write_json(f"{page2}/visuals/RevStackedByChannel/visual.json", _visual_json(
            name="11aa22bb33cc44dd55ee",
            visual_type="clusteredColumnChart",
            x=10, y=112, w=780, h=200, tab_order=3, title="Revenue by City & Channel",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Series": {"projections": [_projection(_col_field(D_CHANNEL, "Channel"), "DimChannel.Channel", "Channel")]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Donut: Revenue by Channel (y=112, h=200)
    if include_visual("RevDonutChannel"):
        write_json(f"{page2}/visuals/RevDonutChannel/visual.json", _visual_json(
            name="22bb33cc44dd55ee66ff",
            visual_type="donutChart",
            x=800, y=112, w=470, h=200, tab_order=4, title="Revenue by Channel",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CHANNEL, "Channel"), "DimChannel.Channel", "Channel", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Treemap: Revenue by State > City (y=318, h=180)
    if include_visual("RevTreemap"):
        write_json(f"{page2}/visuals/RevTreemap/visual.json", _visual_json(
            name="33cc44dd55ee66ff77aa",
            visual_type="treemap",
            x=10, y=318, w=625, h=180, tab_order=5, title="Revenue by State & City",
            query_state={
                "Group": {"projections": [
                    _projection(_col_field(D_CITY, "State"), "DimCity.State", "State"),
                    _projection(_col_field(D_CITY, "City"), "DimCity.City", "City"),
                ]},
                "Values": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Line: Revenue by Month (y=318, h=180)
    if include_visual("RevMonthlyTrend"):
        write_json(f"{page2}/visuals/RevMonthlyTrend/visual.json", _visual_json(
            name="44dd55ee66ff77aa88bb",
            visual_type="lineChart",
            x=645, y=318, w=625, h=180, tab_order=6, title="Monthly Revenue Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Revenue Detail Table (y=504, h=170) - left half
    if include_visual("RevDetailTable"):
        write_json(f"{page2}/visuals/RevDetailTable/visual.json", _visual_json(
            name="55ee66ff77aa88bb99cc",
            visual_type="tableEx",
            x=10, y=504, w=625, h=170, tab_order=7, title="Revenue Detail",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(D_CITY, "City"), "DimCity.City", "City"),
                        _projection(_col_field(D_CHANNEL, "Channel"), "DimChannel.Channel", "Channel"),
                        _projection(_measure_field(T, "Total Revenue"), "SalesData.Total Revenue", "Revenue"),
                        _projection(_measure_field(T, "Total Orders"), "SalesData.Total Orders", "Orders"),
                    ]
                }
            },
        ))

    # Donut: Revenue by Product (y=504, h=170) - right half
    if include_visual("RevDonutProduct"):
        write_json(f"{page2}/visuals/RevDonutProduct/visual.json", _visual_json(
            name="d2a3b4c5e6f7a8b9c0d1",
            visual_type="donutChart",
            x=645, y=504, w=625, h=170, tab_order=8, title="Revenue by Product",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_PRODUCT, "ProductCategory"), "DimProduct.ProductCategory", "Product", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # ---------- Page 3: Performance (bar/area/waterfall/line) ----------
    page3 = f"{defn}/pages/{p_turnaround}"
    write_header_bar(page3, "Turnaround & Performance")
    write_nav_bar(page3, active_index=2)

    # Slicers (y=72, h=36)
    if include_visual("PerfSlicerCity"):
        write_json(f"{page3}/visuals/PerfSlicerCity/visual.json", _visual_json(
            name="0011aa22bb33cc44dd55",
            visual_type="slicer",
            x=10, y=72, w=625, h=36, tab_order=0, title="City",
            query_state={"Values": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]}},
        ))
    if include_visual("PerfSlicerMonth"):
        write_json(f"{page3}/visuals/PerfSlicerMonth/visual.json", _visual_json(
            name="1122bb33cc44dd55ee66",
            visual_type="slicer",
            x=645, y=72, w=625, h=36, tab_order=1, title="Month",
            query_state={"Values": {"projections": [_projection(_col_field(D_DATE, "Month"), "DimDate.Month", "Month", True)]}},
        ))

    # Bar: Turnaround by City (y=112, h=200)
    if include_visual("PerfTurnaroundByCity"):
        write_json(f"{page3}/visuals/PerfTurnaroundByCity/visual.json", _visual_json(
            name="66ff77aa88bb99cc00dd",
            visual_type="clusteredBarChart",
            x=10, y=112, w=625, h=200, tab_order=3, title="Avg Turnaround Days by City",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "TurnaroundDays", 1), "Avg(SalesData.TurnaroundDays)", "Turnaround")]},
            },
        ))

    # Area: Turnaround Trend (y=112, h=200)
    if include_visual("PerfTurnaroundTrend"):
        write_json(f"{page3}/visuals/PerfTurnaroundTrend/visual.json", _visual_json(
            name="77aa88bb99cc00dd11ee",
            visual_type="areaChart",
            x=645, y=112, w=625, h=200, tab_order=4, title="Monthly Turnaround Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "TurnaroundDays", 1), "Avg(SalesData.TurnaroundDays)", "Turnaround")]},
            },
        ))

    # Waterfall: Revenue by City (y=318, h=180)
    if include_visual("PerfRevenueWaterfall"):
        write_json(f"{page3}/visuals/PerfRevenueWaterfall/visual.json", _visual_json(
            name="88bb99cc00dd11ee22ff",
            visual_type="waterfallChart",
            x=10, y=318, w=625, h=180, tab_order=5, title="Revenue Contribution by City",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Line: Online % Trend (y=318, h=180)
    if include_visual("PerfOnlineTrend"):
        write_json(f"{page3}/visuals/PerfOnlineTrend/visual.json", _visual_json(
            name="99cc00dd11ee22ff33aa",
            visual_type="lineChart",
            x=645, y=318, w=625, h=180, tab_order=6, title="Online % Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "OnlinePercent", 1), "Avg(SalesData.OnlinePercent)", "Online %")]},
            },
        ))

    # Performance Detail Table (y=504, h=170) - left half
    if include_visual("PerfDetailTable"):
        write_json(f"{page3}/visuals/PerfDetailTable/visual.json", _visual_json(
            name="00dd11ee22ff33aa44bb",
            visual_type="tableEx",
            x=10, y=504, w=625, h=170, tab_order=7, title="Performance Detail",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(D_CITY, "City"), "DimCity.City", "City"),
                        _projection(_measure_field(T, "Avg Turnaround Days"), "SalesData.Avg Turnaround Days", "Turnaround"),
                        _projection(_measure_field(T, "Avg Online %"), "SalesData.Avg Online %", "Online %"),
                        _projection(_measure_field(T, "Total Revenue"), "SalesData.Total Revenue", "Revenue"),
                    ]
                }
            },
        ))

    # Donut: Revenue by Channel (y=504, h=170) - right half
    if include_visual("PerfDonutChannel"):
        write_json(f"{page3}/visuals/PerfDonutChannel/visual.json", _visual_json(
            name="p3a4b5c6d7e8f9a0b1c2",
            visual_type="donutChart",
            x=645, y=504, w=625, h=170, tab_order=8, title="Revenue by Channel",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CHANNEL, "Channel"), "DimChannel.Channel", "Channel", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # ---------- Page 4: City Comparison (1 slicer + bar/donut) ----------
    page4 = f"{defn}/pages/{p_city}"
    write_header_bar(page4, "City Comparison")
    write_nav_bar(page4, active_index=3)

    # Slicer (y=72, h=36)
    if include_visual("CitySlicerCity"):
        write_json(f"{page4}/visuals/CitySlicerCity/visual.json", _visual_json(
            name="3344dd55ee66ff77aa88",
            visual_type="slicer",
            x=10, y=72, w=1260, h=36, tab_order=0, title="Select Cities",
            query_state={"Values": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]}},
        ))

    # Bar: City Revenue Rank (y=112, h=200)
    if include_visual("CityRevenueRank"):
        write_json(f"{page4}/visuals/CityRevenueRank/visual.json", _visual_json(
            name="11ee22ff33aa44bb55cc",
            visual_type="clusteredBarChart",
            x=10, y=112, w=625, h=200, tab_order=3, title="City Revenue Ranking",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Bar: City Orders Rank (y=112, h=200)
    if include_visual("CityOrdersRank"):
        write_json(f"{page4}/visuals/CityOrdersRank/visual.json", _visual_json(
            name="22ff33aa44bb55cc66dd",
            visual_type="clusteredBarChart",
            x=645, y=112, w=625, h=200, tab_order=4, title="City Orders Ranking",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Orders", 0), "Sum(SalesData.Orders)", "Orders")]},
            },
        ))

    # Donut: Revenue Share by City (y=318, h=180)
    if include_visual("CityRevenueDonut"):
        write_json(f"{page4}/visuals/CityRevenueDonut/visual.json", _visual_json(
            name="33aa44bb55cc66dd77ee",
            visual_type="donutChart",
            x=10, y=318, w=625, h=180, tab_order=5, title="Revenue Share by City",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Bar: City Turnaround Rank (y=318, h=180)
    if include_visual("CityTurnaroundRank"):
        write_json(f"{page4}/visuals/CityTurnaroundRank/visual.json", _visual_json(
            name="44bb55cc66dd77ee88ff",
            visual_type="clusteredBarChart",
            x=645, y=318, w=625, h=180, tab_order=6, title="City Turnaround Ranking",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "TurnaroundDays", 1), "Avg(SalesData.TurnaroundDays)", "Turnaround")]},
            },
        ))

    # City Comparison Table (y=504, h=170) - left half
    if include_visual("CityComparisonTable"):
        write_json(f"{page4}/visuals/CityComparisonTable/visual.json", _visual_json(
            name="55cc66dd77ee88ff99aa",
            visual_type="tableEx",
            x=10, y=504, w=625, h=170, tab_order=7, title="City Comparison",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(D_CITY, "City"), "DimCity.City", "City"),
                        _projection(_measure_field(T, "Total Revenue"), "SalesData.Total Revenue", "Revenue"),
                        _projection(_measure_field(T, "Total Orders"), "SalesData.Total Orders", "Orders"),
                        _projection(_measure_field(T, "Avg Turnaround Days"), "SalesData.Avg Turnaround Days", "Turnaround"),
                    ]
                }
            },
        ))

    # Line: Revenue Trend by Month (y=504, h=170) - right half
    if include_visual("CityRevenueTrend"):
        write_json(f"{page4}/visuals/CityRevenueTrend/visual.json", _visual_json(
            name="c4d5e6f7a8b9c0d1e2f3",
            visual_type="lineChart",
            x=645, y=504, w=625, h=170, tab_order=8, title="Revenue Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # ---------- Page 5: Channel & Product Mix (funnel/donut/treemap/stacked) ----------
    page5 = f"{defn}/pages/{p_channel}"
    write_header_bar(page5, "Channel & Product Mix")
    write_nav_bar(page5, active_index=4)

    # Slicers (y=72, h=36)
    if include_visual("ChanSlicerChannel"):
        write_json(f"{page5}/visuals/ChanSlicerChannel/visual.json", _visual_json(
            name="aa1011bb1213cc1415dd",
            visual_type="slicer",
            x=10, y=72, w=625, h=36, tab_order=0, title="Channel",
            query_state={"Values": {"projections": [_projection(_col_field(D_CHANNEL, "Channel"), "DimChannel.Channel", "Channel", True)]}},
        ))
    if include_visual("ChanSlicerYear"):
        write_json(f"{page5}/visuals/ChanSlicerYear/visual.json", _visual_json(
            name="bb2021cc2223dd2425ee",
            visual_type="slicer",
            x=645, y=72, w=625, h=36, tab_order=1, title="Year",
            query_state={"Values": {"projections": [_projection(_col_field(D_DATE, "Year"), "DimDate.Year", "Year", True)]}},
        ))

    # Funnel: Revenue by Segment (y=112, h=200)
    if include_visual("ChanFunnelSegment"):
        write_json(f"{page5}/visuals/ChanFunnelSegment/visual.json", _visual_json(
            name="dd4041ee4243ff4445aa",
            visual_type="funnel",
            x=10, y=112, w=625, h=200, tab_order=3, title="Revenue by Segment",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_SEGMENT, "Segment"), "DimSegment.Segment", "Segment", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Donut: Revenue by Channel (y=112, h=200)
    if include_visual("ChanDonutChannel"):
        write_json(f"{page5}/visuals/ChanDonutChannel/visual.json", _visual_json(
            name="ee5051ff5253aa5455bb",
            visual_type="donutChart",
            x=645, y=112, w=625, h=200, tab_order=4, title="Revenue by Channel",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CHANNEL, "Channel"), "DimChannel.Channel", "Channel", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Treemap: Revenue by Product Category (y=318, h=180)
    if include_visual("ChanTreemapProduct"):
        write_json(f"{page5}/visuals/ChanTreemapProduct/visual.json", _visual_json(
            name="ff6061aa6263bb6465cc",
            visual_type="treemap",
            x=10, y=318, w=625, h=180, tab_order=5, title="Revenue by Product Category",
            query_state={
                "Group": {"projections": [
                    _projection(_col_field(D_PRODUCT, "ProductCategory"), "DimProduct.ProductCategory", "Product"),
                ]},
                "Values": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Grouped Bar: Revenue by Channel per Region (y=318, h=180)
    if include_visual("ChanStackedRegion"):
        write_json(f"{page5}/visuals/ChanStackedRegion/visual.json", _visual_json(
            name="aa7071bb7273cc7475dd",
            visual_type="clusteredBarChart",
            x=645, y=318, w=625, h=180, tab_order=6, title="Revenue by Region & Channel",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "Region"), "DimCity.Region", "Region", True)]},
                "Series": {"projections": [_projection(_col_field(D_CHANNEL, "Channel"), "DimChannel.Channel", "Channel")]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Channel Detail Table (y=504, h=170) - left half
    if include_visual("ChanDetailTable"):
        write_json(f"{page5}/visuals/ChanDetailTable/visual.json", _visual_json(
            name="cc9091dd9293ee9495ff",
            visual_type="tableEx",
            x=10, y=504, w=625, h=170, tab_order=7, title="Channel Detail",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(D_CHANNEL, "Channel"), "DimChannel.Channel", "Channel"),
                        _projection(_col_field(D_PRODUCT, "ProductCategory"), "DimProduct.ProductCategory", "Product"),
                        _projection(_measure_field(T, "Total Revenue"), "SalesData.Total Revenue", "Revenue"),
                        _projection(_measure_field(T, "Total Gross Profit"), "SalesData.Total Gross Profit", "Profit"),
                    ]
                }
            },
        ))

    # Bar: Satisfaction by Segment (y=504, h=170) - right half
    if include_visual("ChanSatisfactionBar"):
        write_json(f"{page5}/visuals/ChanSatisfactionBar/visual.json", _visual_json(
            name="c5d6e7f8a9b0c1d2e3f4",
            visual_type="clusteredBarChart",
            x=645, y=504, w=625, h=170, tab_order=8, title="Satisfaction by Segment",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_SEGMENT, "Segment"), "DimSegment.Segment", "Segment", True)]},
                "Y": {"projections": [_projection(_measure_field(T, "Avg Satisfaction"), "SalesData.Avg Satisfaction", "Satisfaction")]},
            },
        ))

    # ---------- Page 6: Target & KPI Tracking (combo/waterfall/bar) ----------
    page6 = f"{defn}/pages/{p_target}"
    write_header_bar(page6, "Target & KPI Tracking")
    write_nav_bar(page6, active_index=5)

    # Slicers (y=72, h=36)
    if include_visual("TgtSlicerCity"):
        write_json(f"{page6}/visuals/TgtSlicerCity/visual.json", _visual_json(
            name="dd0011ee2233ff4455aa",
            visual_type="slicer",
            x=10, y=72, w=625, h=36, tab_order=0, title="City",
            query_state={"Values": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]}},
        ))
    if include_visual("TgtSlicerYear"):
        write_json(f"{page6}/visuals/TgtSlicerYear/visual.json", _visual_json(
            name="ee1122ff3344aa5566bb",
            visual_type="slicer",
            x=645, y=72, w=625, h=36, tab_order=1, title="Year",
            query_state={"Values": {"projections": [_projection(_col_field(D_DATE, "Year"), "DimDate.Year", "Year", True)]}},
        ))

    # Combo: Revenue vs Target (y=112, h=200)
    if include_visual("TgtRevenueCombo"):
        write_json(f"{page6}/visuals/TgtRevenueCombo/visual.json", _visual_json(
            name="aa3344bb5566cc7788dd",
            visual_type="lineClusteredColumnComboChart",
            x=10, y=112, w=625, h=200, tab_order=3, title="Revenue vs Target",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
                "Y2": {"projections": [_projection(_agg_col_field(T, "RevenueTarget", 0), "Sum(SalesData.RevenueTarget)", "Rev Target")]},
            },
        ))

    # Combo: Orders vs Target (y=112, h=200)
    if include_visual("TgtOrdersCombo"):
        write_json(f"{page6}/visuals/TgtOrdersCombo/visual.json", _visual_json(
            name="bb4455cc6677dd8899ee",
            visual_type="lineClusteredColumnComboChart",
            x=645, y=112, w=625, h=200, tab_order=4, title="Orders vs Target",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Orders", 0), "Sum(SalesData.Orders)", "Orders")]},
                "Y2": {"projections": [_projection(_agg_col_field(T, "OrdersTarget", 0), "Sum(SalesData.OrdersTarget)", "Orders Target")]},
            },
        ))

    # Waterfall: Revenue Variance by City (y=318, h=180)
    if include_visual("TgtRevenueWaterfall"):
        write_json(f"{page6}/visuals/TgtRevenueWaterfall/visual.json", _visual_json(
            name="cc5566dd7788ee9900ff",
            visual_type="waterfallChart",
            x=10, y=318, w=625, h=180, tab_order=5, title="Revenue Contribution by City",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))

    # Bar: Turnaround vs Target (y=318, h=180)
    if include_visual("TgtTurnaroundBar"):
        write_json(f"{page6}/visuals/TgtTurnaroundBar/visual.json", _visual_json(
            name="dd6677ee8899ff0011aa",
            visual_type="clusteredBarChart",
            x=645, y=318, w=625, h=180, tab_order=6, title="Turnaround vs Target by City",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_CITY, "City"), "DimCity.City", "City", True)]},
                "Y": {
                    "projections": [
                        _projection(_agg_col_field(T, "TurnaroundDays", 1), "Avg(SalesData.TurnaroundDays)", "Turnaround"),
                        _projection(_agg_col_field(T, "TurnaroundTargetDays", 1), "Avg(SalesData.TurnaroundTargetDays)", "Target Days"),
                    ]
                },
            },
        ))

    # Target KPI Detail Table (y=504, h=170) - left half
    if include_visual("TgtDetailTable"):
        write_json(f"{page6}/visuals/TgtDetailTable/visual.json", _visual_json(
            name="ee7788ff9900aa1122bb",
            visual_type="tableEx",
            x=10, y=504, w=625, h=170, tab_order=7, title="Target Detail",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(D_CITY, "City"), "DimCity.City", "City"),
                        _projection(_measure_field(T, "Total Revenue"), "SalesData.Total Revenue", "Revenue"),
                        _projection(_measure_field(T, "Total Revenue Target"), "SalesData.Total Revenue Target", "Rev Target"),
                        _projection(_measure_field(T, "Total Orders"), "SalesData.Total Orders", "Orders"),
                    ]
                }
            },
        ))

    # Area: Revenue vs Target Trend (y=504, h=170) - right half
    if include_visual("TgtRevenueTrend"):
        write_json(f"{page6}/visuals/TgtRevenueTrend/visual.json", _visual_json(
            name="t6a7b8c9d0e1f2a3b4c5",
            visual_type="areaChart",
            x=645, y=504, w=625, h=170, tab_order=8, title="Revenue Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Revenue", 0), "Sum(SalesData.Revenue)", "Revenue")]},
            },
        ))


# ---- CSV backup (reference data) ----

def gen_csv(data_rows):
    write_csv_file("data/sales_data.csv", data_rows)


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"Generating Power BI PBIR Project: {PROJECT_NAME}")
    print(f"Output: {PROJECT_DIR}")
    print()

    # Clean previous artifacts to avoid stale files/folders causing runtime issues.
    # Keep report folder by default so manual shell visuals (header/navigation/buttons)
    # created in Desktop are not deleted on each generation.
    artifact_dirs = [f"{PROJECT_NAME}.SemanticModel", "data"]
    if not PRESERVE_MANUAL_REPORT_LAYOUT:
        artifact_dirs.insert(0, f"{PROJECT_NAME}.Report")

    for artifact_dir in artifact_dirs:
        full = os.path.join(PROJECT_DIR, artifact_dir)
        if os.path.isdir(full):
            shutil.rmtree(full)

    # Generate data
    print("[1/5] Generating sample data...")
    data = generate_data()
    print(
        f"  Generated {len(data)} rows "
        f"({len(CITIES)} cities x {len(MONTHS)} months x {len(YEARS)} years x {len(CHANNEL_SPLIT)} channels)"
    )

    # Project files
    print("[2/5] Creating project structure...")
    gen_pbip()
    gen_gitignore()

    # Semantic model
    print("[3/5] Building semantic model (TMDL)...")
    gen_semantic_model(data)

    # Report
    print("[4/5] Building report (PBIR)...")
    gen_report()

    # CSV backup
    print("[5/5] Exporting CSV data...")
    gen_csv(data)

    # Summary
    print()
    print("=" * 60)
    print("PROJECT GENERATED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("To open in Power BI Desktop:")
    print(f"  1. Open Power BI Desktop")
    print(f"  2. Enable preview features:")
    print(f"     File > Options > Preview features")
    print(f"     [x] Power BI Project (.pbip) save option")
    print(f"     [x] Store reports using enhanced metadata format (PBIR)")
    print(f"     [x] Store semantic model using TMDL format")
    print(f"  3. Restart Power BI Desktop")
    print(f"  4. Open: {os.path.join(PROJECT_DIR, PROJECT_NAME + '.pbip')}")
    print()
    print("Dashboard pages:")
    print("  Page 1: Executive Overview (no slicers, donut + combo + bar + area chart)")
    print("    - 4 KPIs, donut by region, revenue/orders combo, summary table")
    print("  Page 2: Revenue Analysis (stacked, donut, treemap, line)")
    print("    - Stacked by channel/city, donut by channel, treemap, trend")
    print("  Page 3: Turnaround & Performance (bar, area, waterfall, line)")
    print("    - Turnaround by city, area trend, waterfall, online % trend")
    print("  Page 4: City Comparison (bar, donut)")
    print("    - Revenue/orders ranking bars, revenue share donut, turnaround")
    print("  Page 5: Channel & Product Mix (funnel, donut, treemap, stacked)")
    print("    - Segment funnel, channel donut, product treemap, stacked bar")
    print("  Page 6: Target & KPI Tracking (combo, waterfall, bar)")
    print("    - Revenue/orders vs target combos, waterfall, turnaround bar")
    print()
    print("Data: 8 Australian capital cities, 24 months (2023-2024),")
    print("      3 channels, segments, categories, and target metrics")
    print("Cities: Melbourne, Sydney, Brisbane, Perth, Adelaide,")
    print("        Canberra, Hobart, Darwin")
    print()
    print("If visuals do not render on first open, refresh once and")
    print("confirm PBIP/PBIR/TMDL preview features are enabled.")


if __name__ == "__main__":
    main()

