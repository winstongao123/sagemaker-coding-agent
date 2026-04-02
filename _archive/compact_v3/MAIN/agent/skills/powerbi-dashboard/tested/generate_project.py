"""
Power BI PBIR Project Generator - University Enrollment System
Generates a complete Power BI Desktop project (.pbip) with:
- 4-page university enrollment analytics dashboard with slicers
- Enriched TMDL semantic model (faculties, programs, sources, demographics)
- PBIR report definition with chart/table visuals across all pages

Usage:
    python generate_project.py
    Then open tested.pbip in Power BI Desktop (Developer Mode with PBIR enabled)
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
PROJECT_NAME = "tested"
SAFE_MODE_NO_PREBUILT_VISUALS = False
VISUAL_FILTER_RAW = os.environ.get("TESTED_VISUALS", "all").strip()
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
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tested.{name}"))

# ============================================================
# SAMPLE DATA
# ============================================================
FACULTIES = ["Business", "Engineering", "Science", "Arts", "Health"]
PROGRAMS = [
    "Accounting", "Marketing", "Finance",
    "Civil Eng", "Software Eng",
    "Computer Science", "Data Science",
    "Psychology",
    "Nursing", "Physiotherapy"
]
LEVELS = ["Undergraduate", "Postgraduate", "PhD"]
CAMPUSES = ["Main Campus", "City Campus", "Online"]
SOURCES = ["Website", "Agent", "Walk-in", "Referral", "Social Media"]

# Program to Faculty mapping
PROGRAM_FACULTY = {
    "Accounting": "Business", "Marketing": "Business", "Finance": "Business",
    "Civil Eng": "Engineering", "Software Eng": "Engineering",
    "Computer Science": "Science", "Data Science": "Science",
    "Psychology": "Arts",
    "Nursing": "Health", "Physiotherapy": "Health",
}

# Program to Level mapping (most common)
PROGRAM_LEVEL = {
    "Accounting": "Undergraduate", "Marketing": "Undergraduate", "Finance": "Postgraduate",
    "Civil Eng": "Undergraduate", "Software Eng": "Undergraduate",
    "Computer Science": "Undergraduate", "Data Science": "Postgraduate",
    "Psychology": "Undergraduate",
    "Nursing": "Undergraduate", "Physiotherapy": "Postgraduate",
}

MONTHS = [
    ("January", 1), ("February", 2), ("March", 3), ("April", 4),
    ("May", 5), ("June", 6), ("July", 7), ("August", 8),
    ("September", 9), ("October", 10), ("November", 11), ("December", 12),
]
YEARS = [2023, 2024]

random.seed(42)  # Reproducible

def generate_data():
    """Generate multi-year enrollment data with enquiries, offers, acceptances, enrollments."""
    rows = []
    for year in YEARS:
        year_growth = 1.0 if year == 2023 else 1.08
        for faculty in FACULTIES:
            for campus in CAMPUSES:
                for month_name, month_num in MONTHS:
                    # Peak months for university: Feb-Mar (semester 1), Jul-Aug (semester 2)
                    seasonal = 1.4 if month_num in (2, 3, 7, 8) else 0.7
                    noise = random.uniform(0.88, 1.12)

                    # Base enquiries per faculty per month
                    base_enquiries = random.randint(40, 120)
                    enquiries = max(20, int(base_enquiries * seasonal * noise * year_growth))

                    # Funnel conversion
                    offer_rate = random.uniform(0.60, 0.90)
                    offers = max(1, int(enquiries * offer_rate))

                    acceptance_rate = random.uniform(0.70, 0.95)
                    acceptances = max(1, int(offers * acceptance_rate))

                    enrollment_rate = random.uniform(0.80, 1.00)
                    enrollments = max(1, int(acceptances * enrollment_rate))

                    # Select a representative program for this row
                    program = random.choice([p for p, f in PROGRAM_FACULTY.items() if f == faculty])
                    level = PROGRAM_LEVEL.get(program, "Undergraduate")

                    # Tuition (scaled by enrollment count)
                    tuition_per_student = random.uniform(5000, 45000)
                    tuition = round(tuition_per_student * enrollments, 2)

                    # Satisfaction varies by faculty and improves slightly over time
                    faculty_sat_base = {"Arts": 3.8, "Business": 3.6, "Engineering": 3.4, "Health": 4.0, "Science": 3.5}
                    sat_base = faculty_sat_base.get(faculty, 3.6)
                    sat_trend = (year - 2023) * 0.15 + month_num * 0.02  # gradual improvement
                    satisfaction_score = round(min(5.0, max(1.0, sat_base + sat_trend + random.uniform(-0.5, 0.5))), 2)
                    # International % varies by faculty, higher in business/engineering, grows over time
                    faculty_intl_base = {"Arts": 15, "Business": 40, "Engineering": 45, "Health": 20, "Science": 35}
                    intl_base = faculty_intl_base.get(faculty, 25)
                    intl_trend = (year - 2023) * 3 + month_num * 0.4
                    international_pct = round(min(80.0, max(2.0, intl_base + intl_trend + random.uniform(-8, 8))), 2)

                    source = random.choice(SOURCES)

                    quarter = f"Q{((month_num - 1) // 3) + 1}"
                    year_month = f"{year}-{month_num:02d}"
                    year_month_sort = year * 100 + month_num
                    date_key = year_month_sort

                    faculty_key = faculty.replace(" ", "")
                    program_key = program.replace(" ", "")
                    source_key = source.replace(" ", "")

                    rows.append({
                        "DateKey": date_key,
                        "FacultyKey": faculty_key,
                        "ProgramKey": program_key,
                        "SourceKey": source_key,
                        "Campus": campus,
                        "Faculty": faculty,
                        "Program": program,
                        "Level": level,
                        "Year": year,
                        "Quarter": quarter,
                        "Month": month_name,
                        "MonthNum": month_num,
                        "YearMonth": year_month,
                        "YearMonthSort": year_month_sort,
                        "Source": source,
                        "Enquiries": enquiries,
                        "Offers": offers,
                        "Acceptances": acceptances,
                        "Enrollments": enrollments,
                        "Tuition": tuition,
                        "SatisfactionScore": satisfaction_score,
                        "InternationalPct": international_pct,
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
            f'{r["DateKey"]}, "{r["FacultyKey"]}", "{r["ProgramKey"]}", "{r["SourceKey"]}", '
            f'"{r["Campus"]}", "{r["Faculty"]}", "{r["Program"]}", "{r["Level"]}", '
            f'{r["Year"]}, "{r["Quarter"]}", "{r["Month"]}", {r["MonthNum"]}, '
            f'"{r["YearMonth"]}", {r["YearMonthSort"]}, "{r["Source"]}", '
            f'{r["Enquiries"]}, {r["Offers"]}, {r["Acceptances"]}, {r["Enrollments"]}, '
            f'{r["Tuition"]}, {r["SatisfactionScore"]}, {r["InternationalPct"]}'
            f'}}'
        )
    m_data_literal = ",\n".join(m_rows)

    m_expression = (
        'let\n'
        '\t\t\t\tSource = #table(\n'
        '\t\t\t\t\ttype table [\n'
        '\t\t\t\t\t\tDateKey = Int64.Type,\n'
        '\t\t\t\t\t\tFacultyKey = text, ProgramKey = text, SourceKey = text,\n'
        '\t\t\t\t\t\tCampus = text, Faculty = text, Program = text, Level = text,\n'
        '\t\t\t\t\t\tYear = Int64.Type, Quarter = text, Month = text,\n'
        '\t\t\t\t\t\tMonthNum = Int64.Type, YearMonth = text, YearMonthSort = Int64.Type,\n'
        '\t\t\t\t\t\tSource = text,\n'
        '\t\t\t\t\t\tEnquiries = Int64.Type, Offers = Int64.Type, Acceptances = Int64.Type, Enrollments = Int64.Type,\n'
        '\t\t\t\t\t\tTuition = number, SatisfactionScore = number, InternationalPct = number\n'
        '\t\t\t\t\t],\n'
        '\t\t\t\t\t{\n'
        f'{m_data_literal}\n'
        '\t\t\t\t\t}\n'
        '\t\t\t\t),\n'
        '\t\t\t\tCleanText = Table.TransformColumns(\n'
        '\t\t\t\t\tSource,\n'
        '\t\t\t\t\t{\n'
        '\t\t\t\t\t\t{"Campus", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Faculty", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Program", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Level", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Month", each Text.Trim(_), type text},\n'
        '\t\t\t\t\t\t{"Source", each Text.Trim(_), type text}\n'
        '\t\t\t\t\t}\n'
        '\t\t\t\t),\n'
        '\t\t\t\tFillMissingText = Table.ReplaceValue(CleanText, null, "Unknown", Replacer.ReplaceValue, {"Campus", "Faculty", "Program", "Level", "Source"}),\n'
        '\t\t\t\tNormalizeMetrics = Table.TransformColumns(\n'
        '\t\t\t\t\tFillMissingText,\n'
        '\t\t\t\t\t{\n'
        '\t\t\t\t\t\t{"SatisfactionScore", each if _ < 1 then 1 else if _ > 5 then 5 else _, type number},\n'
        '\t\t\t\t\t\t{"InternationalPct", each if _ < 0 then 0 else if _ > 100 then 100 else _, type number}\n'
        '\t\t\t\t\t}\n'
        '\t\t\t\t),\n'
        '\t\t\t\tSortRows = Table.Sort(NormalizeMetrics, {{"YearMonthSort", Order.Ascending}, {"Faculty", Order.Ascending}, {"Program", Order.Ascending}}),\n'
        '\t\t\t\tFilterInvalid = Table.SelectRows(SortRows, each [Enquiries] >= 0 and [Enrollments] >= 0)\n'
        '\t\t\tin\n'
        '\t\t\t\tFilterInvalid'
    )

    # EnrollmentData.tmdl - Table definition with columns, measures, and partition
    tmdl = (
        f'table EnrollmentData\n'
        f'\tlineageTag: {make_uuid("table.EnrollmentData")}\n'
        f'\n'
        # ---- Measures ----
        f'\tmeasure \'Total Enquiries\' = SUM(EnrollmentData[Enquiries])\n'
        f'\t\tformatString: #,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalEnquiries")}\n'
        f'\n'
        f'\tmeasure \'Total Enrollments\' = SUM(EnrollmentData[Enrollments])\n'
        f'\t\tformatString: #,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalEnrollments")}\n'
        f'\n'
        f'\tmeasure \'Total Offers\' = SUM(EnrollmentData[Offers])\n'
        f'\t\tformatString: #,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalOffers")}\n'
        f'\n'
        f'\tmeasure \'Total Acceptances\' = SUM(EnrollmentData[Acceptances])\n'
        f'\t\tformatString: #,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalAcceptances")}\n'
        f'\n'
        f'\tmeasure \'Conversion Rate\' = DIVIDE([Total Enrollments], [Total Enquiries])\n'
        f'\t\tformatString: #,##0.0"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.ConversionRate")}\n'
        f'\n'
        f'\tmeasure \'Offer Rate\' = DIVIDE([Total Offers], [Total Enquiries])\n'
        f'\t\tformatString: #,##0.0"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.OfferRate")}\n'
        f'\n'
        f'\tmeasure \'Total Tuition\' = SUM(EnrollmentData[Tuition])\n'
        f'\t\tformatString: $#,##0\n'
        f'\t\tlineageTag: {make_uuid("measure.TotalTuition")}\n'
        f'\n'
        f'\tmeasure \'Avg Satisfaction\' = AVERAGE(EnrollmentData[SatisfactionScore])\n'
        f'\t\tformatString: #,##0.00\n'
        f'\t\tlineageTag: {make_uuid("measure.AvgSatisfaction")}\n'
        f'\n'
        f'\tmeasure \'Avg International %\' = AVERAGE(EnrollmentData[InternationalPct])\n'
        f'\t\tformatString: #,##0.0"%"\n'
        f'\t\tlineageTag: {make_uuid("measure.AvgInternationalPct")}\n'
        f'\n'
        # ---- Columns ----
        f'\tcolumn DateKey\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.DateKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: DateKey\n'
        f'\n'
        f'\tcolumn FacultyKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.FacultyKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: FacultyKey\n'
        f'\n'
        f'\tcolumn ProgramKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.ProgramKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: ProgramKey\n'
        f'\n'
        f'\tcolumn SourceKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.SourceKey")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: SourceKey\n'
        f'\n'
        f'\tcolumn Campus\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Campus")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Campus\n'
        f'\n'
        f'\tcolumn Faculty\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Faculty")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Faculty\n'
        f'\n'
        f'\tcolumn Program\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Program")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Program\n'
        f'\n'
        f'\tcolumn Level\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Level")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Level\n'
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
        f'\tcolumn Source\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("col.Source")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Source\n'
        f'\n'
        f'\tcolumn Enquiries\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.Enquiries")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: Enquiries\n'
        f'\n'
        f'\tcolumn Offers\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.Offers")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: Offers\n'
        f'\n'
        f'\tcolumn Acceptances\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.Acceptances")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: Acceptances\n'
        f'\n'
        f'\tcolumn Enrollments\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("col.Enrollments")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: Enrollments\n'
        f'\n'
        f'\tcolumn Tuition\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.Tuition")}\n'
        f'\t\tsummarizeBy: sum\n'
        f'\t\tsourceColumn: Tuition\n'
        f'\t\tformatString: $#,##0.00\n'
        f'\n'
        f'\tcolumn SatisfactionScore\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.SatisfactionScore")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: SatisfactionScore\n'
        f'\t\tformatString: #,##0.00\n'
        f'\n'
        f'\tcolumn InternationalPct\n'
        f'\t\tdataType: double\n'
        f'\t\tlineageTag: {make_uuid("col.InternationalPct")}\n'
        f'\t\tsummarizeBy: average\n'
        f'\t\tsourceColumn: InternationalPct\n'
        f'\t\tformatString: #,##0.00\n'
        f'\n'
        # ---- Partition ----
        f'\tpartition EnrollmentData = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\t{m_expression}\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/EnrollmentData.tmdl", tmdl)

    # ---- Build dimension data from fact rows ----
    dim_date_rows = sorted(
        {(r["DateKey"], r["Year"], r["Quarter"], r["Month"], r["MonthNum"], r["YearMonth"], r["YearMonthSort"]) for r in data_rows},
        key=lambda x: x[0]
    )
    dim_date_literal = ",\n".join(
        f'\t\t\t\t\t\t{{{dk}, {yr}, "{qt}", "{mn}", {mnum}, "{ym}", {yms}}}'
        for dk, yr, qt, mn, mnum, ym, yms in dim_date_rows
    )

    dim_faculty_rows = sorted(
        {(r["FacultyKey"], r["Faculty"]) for r in data_rows},
        key=lambda x: x[1]
    )
    dim_faculty_literal = ",\n".join(
        f'\t\t\t\t\t\t{{"{fk}", "{fn}"}}' for fk, fn in dim_faculty_rows
    )

    dim_program_rows = sorted(
        {(r["ProgramKey"], r["Program"], r["Level"]) for r in data_rows},
        key=lambda x: x[1]
    )
    dim_program_literal = ",\n".join(
        f'\t\t\t\t\t\t{{"{pk}", "{pn}", "{lv}"}}' for pk, pn, lv in dim_program_rows
    )

    dim_source_rows = sorted(
        {(r["SourceKey"], r["Source"]) for r in data_rows},
        key=lambda x: x[1]
    )
    dim_source_literal = ",\n".join(
        f'\t\t\t\t\t\t{{"{sk}", "{sn}"}}' for sk, sn in dim_source_rows
    )

    # Dimension tables
    dim_date_tmdl = (
        f'table DimDate\n'
        f'\tlineageTag: {make_uuid("table.DimDate")}\n'
        f'\n'
        f'\tcolumn DateKey\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("dimdate.DateKey")}\n'
        f'\t\tisKey: true\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: DateKey\n'
        f'\n'
        f'\tcolumn Year\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("dimdate.Year")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Year\n'
        f'\n'
        f'\tcolumn Quarter\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimdate.Quarter")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Quarter\n'
        f'\n'
        f'\tcolumn Month\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimdate.Month")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Month\n'
        f'\t\tsortByColumn: MonthNum\n'
        f'\n'
        f'\tcolumn MonthNum\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("dimdate.MonthNum")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: MonthNum\n'
        f'\n'
        f'\tcolumn YearMonth\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimdate.YearMonth")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: YearMonth\n'
        f'\t\tsortByColumn: YearMonthSort\n'
        f'\n'
        f'\tcolumn YearMonthSort\n'
        f'\t\tdataType: int64\n'
        f'\t\tlineageTag: {make_uuid("dimdate.YearMonthSort")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: YearMonthSort\n'
        f'\n'
        f'\tpartition DimDate = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [DateKey = Int64.Type, Year = Int64.Type, Quarter = text, Month = text, MonthNum = Int64.Type, YearMonth = text, YearMonthSort = Int64.Type],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_date_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimDate.tmdl", dim_date_tmdl)

    dim_faculty_tmdl = (
        f'table DimFaculty\n'
        f'\tlineageTag: {make_uuid("table.DimFaculty")}\n'
        f'\n'
        f'\tcolumn FacultyKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimfaculty.FacultyKey")}\n'
        f'\t\tisKey: true\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: FacultyKey\n'
        f'\n'
        f'\tcolumn Faculty\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimfaculty.Faculty")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Faculty\n'
        f'\n'
        f'\tpartition DimFaculty = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [FacultyKey = text, Faculty = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_faculty_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimFaculty.tmdl", dim_faculty_tmdl)

    dim_program_tmdl = (
        f'table DimProgram\n'
        f'\tlineageTag: {make_uuid("table.DimProgram")}\n'
        f'\n'
        f'\tcolumn ProgramKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimprogram.ProgramKey")}\n'
        f'\t\tisKey: true\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: ProgramKey\n'
        f'\n'
        f'\tcolumn Program\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimprogram.Program")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Program\n'
        f'\n'
        f'\tcolumn Level\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimprogram.Level")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Level\n'
        f'\n'
        f'\tpartition DimProgram = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [ProgramKey = text, Program = text, Level = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_program_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimProgram.tmdl", dim_program_tmdl)

    dim_source_tmdl = (
        f'table DimSource\n'
        f'\tlineageTag: {make_uuid("table.DimSource")}\n'
        f'\n'
        f'\tcolumn SourceKey\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimsource.SourceKey")}\n'
        f'\t\tisKey: true\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: SourceKey\n'
        f'\n'
        f'\tcolumn Source\n'
        f'\t\tdataType: string\n'
        f'\t\tlineageTag: {make_uuid("dimsource.Source")}\n'
        f'\t\tsummarizeBy: none\n'
        f'\t\tsourceColumn: Source\n'
        f'\n'
        f'\tpartition DimSource = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\tlet\n'
        f'\t\t\t\tSource = #table(\n'
        f'\t\t\t\t\ttype table [SourceKey = text, Source = text],\n'
        f'\t\t\t\t\t{{\n'
        f'{dim_source_literal}\n'
        f'\t\t\t\t\t}}\n'
        f'\t\t\t\t)\n'
        f'\t\t\tin\n'
        f'\t\t\t\tSource\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/tables/DimSource.tmdl", dim_source_tmdl)

    # Relationships
    relationships_tmdl = (
        f'relationship {make_uuid("rel.EnrollmentData.DateKey->DimDate.DateKey")}\n'
        f'\tfromColumn: EnrollmentData.DateKey\n'
        f'\ttoColumn: DimDate.DateKey\n'
        f'\n'
        f'relationship {make_uuid("rel.EnrollmentData.FacultyKey->DimFaculty.FacultyKey")}\n'
        f'\tfromColumn: EnrollmentData.FacultyKey\n'
        f'\ttoColumn: DimFaculty.FacultyKey\n'
        f'\n'
        f'relationship {make_uuid("rel.EnrollmentData.ProgramKey->DimProgram.ProgramKey")}\n'
        f'\tfromColumn: EnrollmentData.ProgramKey\n'
        f'\ttoColumn: DimProgram.ProgramKey\n'
        f'\n'
        f'relationship {make_uuid("rel.EnrollmentData.SourceKey->DimSource.SourceKey")}\n'
        f'\tfromColumn: EnrollmentData.SourceKey\n'
        f'\ttoColumn: DimSource.SourceKey\n'
    )
    write_file(f"{PROJECT_NAME}.SemanticModel/definition/relationships.tmdl", relationships_tmdl)


# ---- Report (PBIR) - Helper functions COPIED FROM TEMPLATE ----

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

    # Four-page university enrollment report
    p_exec = "a1b2c3d4e5f678901234"
    p_enrollment = "b2c3d4e5f67890123456"
    p_enquiry = "c3d4e5f6789012345678"
    p_demographics = "d4e5f678901234567890"

    if SAFE_MODE_NO_PREBUILT_VISUALS:
        page_order = [p_exec]
    else:
        page_order = [p_exec, p_enrollment, p_enquiry, p_demographics]

    write_json(f"{defn}/pages/pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_order,
        "activePageName": p_exec,
    })

    T = "EnrollmentData"
    D_DATE = "DimDate"
    D_FACULTY = "DimFaculty"
    D_PROGRAM = "DimProgram"
    D_SOURCE = "DimSource"
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
    write_page(p_enrollment, "Enrollment Analysis")
    write_page(p_enquiry, "Enquiry Pipeline")
    write_page(p_demographics, "Student Demographics")

    if SAFE_MODE_NO_PREBUILT_VISUALS:
        return

    # ---- Header banner on every page ----
    def write_header_bar(page_path: str, page_title: str):
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
                        "text": _lit_str(f"  UNIVERSITY ANALYTICS  |  {page_title}"),
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
    if include_visual("ExecKPIEnrollments"):
        write_json(f"{page1}/visuals/ExecKPIEnrollments/visual.json", _visual_json(
            name="kpi001122334455667788",
            visual_type="card",
            x=10, y=72, w=305, h=68, tab_order=3, title="Total Enrollments",
            query_state={
                "Values": {"projections": [_projection(_measure_field(T, "Total Enrollments"), "EnrollmentData.Total Enrollments", "Total Enrollments", True)]},
            },
        ))
    if include_visual("ExecKPIEnquiries"):
        write_json(f"{page1}/visuals/ExecKPIEnquiries/visual.json", _visual_json(
            name="kpi112233445566778899",
            visual_type="card",
            x=325, y=72, w=305, h=68, tab_order=4, title="Total Enquiries",
            query_state={
                "Values": {"projections": [_projection(_measure_field(T, "Total Enquiries"), "EnrollmentData.Total Enquiries", "Total Enquiries", True)]},
            },
        ))
    if include_visual("ExecKPIConversion"):
        write_json(f"{page1}/visuals/ExecKPIConversion/visual.json", _visual_json(
            name="kpi223344556677889900",
            visual_type="card",
            x=640, y=72, w=305, h=68, tab_order=5, title="Conversion Rate",
            query_state={
                "Values": {"projections": [_projection(_measure_field(T, "Conversion Rate"), "EnrollmentData.Conversion Rate", "Conversion Rate", True)]},
            },
        ))
    if include_visual("ExecKPITuition"):
        write_json(f"{page1}/visuals/ExecKPITuition/visual.json", _visual_json(
            name="kpi334455667788990011",
            visual_type="card",
            x=955, y=72, w=315, h=68, tab_order=6, title="Total Tuition",
            query_state={
                "Values": {"projections": [_projection(_measure_field(T, "Total Tuition"), "EnrollmentData.Total Tuition", "Total Tuition", True)]},
            },
        ))

    # Donut: Enrollments by Faculty (y=146, h=195)
    if include_visual("ExecEnrollmentsByFaculty"):
        write_json(f"{page1}/visuals/ExecEnrollmentsByFaculty/visual.json", _visual_json(
            name="f1a7b4c29d6e3f8051aa",
            visual_type="donutChart",
            x=10, y=146, w=380, h=195, tab_order=7, title="Enrollments by Faculty",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_FACULTY, "Faculty"), "DimFaculty.Faculty", "Faculty", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # Combo: Enrollments (bars) + Enquiries (line) by Month (y=146, h=195)
    if include_visual("ExecEnrollmentsEnquiriesCombo"):
        write_json(f"{page1}/visuals/ExecEnrollmentsEnquiriesCombo/visual.json", _visual_json(
            name="c5e8f709a1b2d3c4e5f6",
            visual_type="lineClusteredColumnComboChart",
            x=400, y=146, w=870, h=195, tab_order=8, title="Enrollments & Enquiries Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "Month"), "DimDate.Month", "Month", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
                "Y2": {"projections": [_projection(_agg_col_field(T, "Enquiries", 0), "Sum(EnrollmentData.Enquiries)", "Enquiries")]},
            },
        ))

    # Row 2: Bar chart + Area chart (y=347, h=160)
    if include_visual("ExecEnrollmentsByProgram"):
        write_json(f"{page1}/visuals/ExecEnrollmentsByProgram/visual.json", _visual_json(
            name="ba4c1d2e3f4a5b6c7d8e",
            visual_type="clusteredBarChart",
            x=10, y=347, w=625, h=160, tab_order=9, title="Enrollments by Program",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_PROGRAM, "Program"), "DimProgram.Program", "Program", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))
    if include_visual("ExecMonthlyArea"):
        write_json(f"{page1}/visuals/ExecMonthlyArea/visual.json", _visual_json(
            name="ae5d6c7b8a9f0e1d2c3b",
            visual_type="areaChart",
            x=645, y=347, w=625, h=160, tab_order=10, title="Monthly Enrollment Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
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
                        _projection(_col_field(D_FACULTY, "Faculty"), "DimFaculty.Faculty", "Faculty"),
                        _projection(_measure_field(T, "Total Enrollments"), "EnrollmentData.Total Enrollments", "Enrollments"),
                        _projection(_measure_field(T, "Total Enquiries"), "EnrollmentData.Total Enquiries", "Enquiries"),
                        _projection(_measure_field(T, "Conversion Rate"), "EnrollmentData.Conversion Rate", "Conversion Rate"),
                    ]
                }
            },
        ))

    # Donut: Enrollments by Source (y=513, h=200) - right half
    if include_visual("ExecEnrollmentsBySource"):
        write_json(f"{page1}/visuals/ExecEnrollmentsBySource/visual.json", _visual_json(
            name="f2b3c4d5e6a7b8c9d0e1",
            visual_type="donutChart",
            x=645, y=513, w=625, h=200, tab_order=12, title="Enrollments by Source",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_SOURCE, "Source"), "DimSource.Source", "Source", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # ---------- Page 2: Enrollment Analysis (2 slicers + clustered bar/donut/treemap/line) ----------
    page2 = f"{defn}/pages/{p_enrollment}"
    write_header_bar(page2, "Enrollment Analysis")
    write_nav_bar(page2, active_index=1)

    # Slicers (y=72, h=36)
    if include_visual("EnrollSlicerFaculty"):
        write_json(f"{page2}/visuals/EnrollSlicerFaculty/visual.json", _visual_json(
            name="dd44ee55ff66aa77bb88",
            visual_type="slicer",
            x=10, y=72, w=625, h=36, tab_order=0, title="Faculty",
            query_state={"Values": {"projections": [_projection(_col_field(D_FACULTY, "Faculty"), "DimFaculty.Faculty", "Faculty", True)]}},
        ))
    if include_visual("EnrollSlicerYear"):
        write_json(f"{page2}/visuals/EnrollSlicerYear/visual.json", _visual_json(
            name="ee55ff66aa77bb88cc99",
            visual_type="slicer",
            x=645, y=72, w=625, h=36, tab_order=1, title="Year",
            query_state={"Values": {"projections": [_projection(_col_field(D_DATE, "Year"), "DimDate.Year", "Year", True)]}},
        ))

    # Clustered Bar: Enrollments by Program (y=112, h=200)
    if include_visual("EnrollByProgram"):
        write_json(f"{page2}/visuals/EnrollByProgram/visual.json", _visual_json(
            name="11aa22bb33cc44dd55ee",
            visual_type="clusteredBarChart",
            x=10, y=112, w=625, h=200, tab_order=3, title="Enrollments by Program",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_PROGRAM, "Program"), "DimProgram.Program", "Program", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # Donut: Enrollments by Level (y=112, h=200)
    if include_visual("EnrollByLevel"):
        write_json(f"{page2}/visuals/EnrollByLevel/visual.json", _visual_json(
            name="22bb33cc44dd55ee66ff",
            visual_type="donutChart",
            x=645, y=112, w=625, h=200, tab_order=4, title="Enrollments by Level",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_PROGRAM, "Level"), "DimProgram.Level", "Level", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # Treemap: Tuition by Faculty > Program (y=318, h=180)
    if include_visual("EnrollTuitionTreemap"):
        write_json(f"{page2}/visuals/EnrollTuitionTreemap/visual.json", _visual_json(
            name="33cc44dd55ee66ff77aa",
            visual_type="treemap",
            x=10, y=318, w=625, h=180, tab_order=5, title="Tuition by Faculty & Program",
            query_state={
                "Group": {"projections": [
                    _projection(_col_field(D_FACULTY, "Faculty"), "DimFaculty.Faculty", "Faculty"),
                    _projection(_col_field(D_PROGRAM, "Program"), "DimProgram.Program", "Program"),
                ]},
                "Values": {"projections": [_projection(_agg_col_field(T, "Tuition", 0), "Sum(EnrollmentData.Tuition)", "Tuition")]},
            },
        ))

    # Line: Monthly Enrollment Trend (y=318, h=180)
    if include_visual("EnrollMonthlyTrend"):
        write_json(f"{page2}/visuals/EnrollMonthlyTrend/visual.json", _visual_json(
            name="44dd55ee66ff77aa88bb",
            visual_type="lineChart",
            x=645, y=318, w=625, h=180, tab_order=6, title="Monthly Enrollment Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # Enrollment Detail Table (y=504, h=170) - left half
    if include_visual("EnrollDetailTable"):
        write_json(f"{page2}/visuals/EnrollDetailTable/visual.json", _visual_json(
            name="55ee66ff77aa88bb99cc",
            visual_type="tableEx",
            x=10, y=504, w=625, h=170, tab_order=7, title="Enrollment Detail",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(D_PROGRAM, "Program"), "DimProgram.Program", "Program"),
                        _projection(_col_field(D_PROGRAM, "Level"), "DimProgram.Level", "Level"),
                        _projection(_measure_field(T, "Total Enrollments"), "EnrollmentData.Total Enrollments", "Enrollments"),
                        _projection(_measure_field(T, "Total Tuition"), "EnrollmentData.Total Tuition", "Tuition"),
                    ]
                }
            },
        ))

    # Area: Tuition Trend (y=504, h=170) - right half
    if include_visual("EnrollTuitionTrend"):
        write_json(f"{page2}/visuals/EnrollTuitionTrend/visual.json", _visual_json(
            name="d2a3b4c5e6f7a8b9c0d1",
            visual_type="areaChart",
            x=645, y=504, w=625, h=170, tab_order=8, title="Tuition Revenue Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Tuition", 0), "Sum(EnrollmentData.Tuition)", "Tuition")]},
            },
        ))

    # ---------- Page 3: Enquiry Pipeline (2 slicers + donut/bar/waterfall/table) ----------
    page3 = f"{defn}/pages/{p_enquiry}"
    write_header_bar(page3, "Enquiry Pipeline")
    write_nav_bar(page3, active_index=2)

    # Slicers (y=72, h=36)
    if include_visual("EnquirySlicerSource"):
        write_json(f"{page3}/visuals/EnquirySlicerSource/visual.json", _visual_json(
            name="0011aa22bb33cc44dd55",
            visual_type="slicer",
            x=10, y=72, w=625, h=36, tab_order=0, title="Source",
            query_state={"Values": {"projections": [_projection(_col_field(D_SOURCE, "Source"), "DimSource.Source", "Source", True)]}},
        ))
    if include_visual("EnquirySlicerYear"):
        write_json(f"{page3}/visuals/EnquirySlicerYear/visual.json", _visual_json(
            name="1122bb33cc44dd55ee66",
            visual_type="slicer",
            x=645, y=72, w=625, h=36, tab_order=1, title="Year",
            query_state={"Values": {"projections": [_projection(_col_field(D_DATE, "Year"), "DimDate.Year", "Year", True)]}},
        ))

    # Donut: Enquiries by Source (y=112, h=200)
    if include_visual("EnquiryBySource"):
        write_json(f"{page3}/visuals/EnquiryBySource/visual.json", _visual_json(
            name="2233cc44dd55ee66ff77",
            visual_type="donutChart",
            x=10, y=112, w=625, h=200, tab_order=3, title="Enquiries by Source",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_SOURCE, "Source"), "DimSource.Source", "Source", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enquiries", 0), "Sum(EnrollmentData.Enquiries)", "Enquiries")]},
            },
        ))

    # Clustered Bar: Conversion by Faculty (y=112, h=200)
    if include_visual("EnquiryConversionByFaculty"):
        write_json(f"{page3}/visuals/EnquiryConversionByFaculty/visual.json", _visual_json(
            name="3344dd55ee66ff77aa88",
            visual_type="clusteredBarChart",
            x=645, y=112, w=625, h=200, tab_order=4, title="Conversion Rate by Faculty",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_FACULTY, "Faculty"), "DimFaculty.Faculty", "Faculty", True)]},
                "Y": {"projections": [_projection(_measure_field(T, "Conversion Rate"), "EnrollmentData.Conversion Rate", "Conversion Rate")]},
            },
        ))

    # Waterfall: Enquiry changes by month (y=318, h=180)
    if include_visual("EnquiryWaterfall"):
        write_json(f"{page3}/visuals/EnquiryWaterfall/visual.json", _visual_json(
            name="4455ee66ff77aa88bb99",
            visual_type="waterfallChart",
            x=10, y=318, w=625, h=180, tab_order=5, title="Monthly Enquiry Changes",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "Month"), "DimDate.Month", "Month", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enquiries", 0), "Sum(EnrollmentData.Enquiries)", "Enquiries")]},
            },
        ))

    # Clustered Bar: Offer Rate by Faculty (y=318, h=180)
    if include_visual("EnquiryOfferRate"):
        write_json(f"{page3}/visuals/EnquiryOfferRate/visual.json", _visual_json(
            name="5566ff77aa88bb99cc00",
            visual_type="clusteredBarChart",
            x=645, y=318, w=625, h=180, tab_order=6, title="Offer Rate by Faculty",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_FACULTY, "Faculty"), "DimFaculty.Faculty", "Faculty", True)]},
                "Y": {"projections": [_projection(_measure_field(T, "Offer Rate"), "EnrollmentData.Offer Rate", "Offer Rate")]},
            },
        ))

    # Table: Source pipeline (y=504, h=170) - left half
    if include_visual("EnquirySourceTable"):
        write_json(f"{page3}/visuals/EnquirySourceTable/visual.json", _visual_json(
            name="6677aa88bb99cc00dd11",
            visual_type="tableEx",
            x=10, y=504, w=625, h=170, tab_order=7, title="Pipeline by Source",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(D_SOURCE, "Source"), "DimSource.Source", "Source"),
                        _projection(_measure_field(T, "Total Enquiries"), "EnrollmentData.Total Enquiries", "Enquiries"),
                        _projection(_measure_field(T, "Total Offers"), "EnrollmentData.Total Offers", "Offers"),
                        _projection(_measure_field(T, "Total Enrollments"), "EnrollmentData.Total Enrollments", "Enrollments"),
                    ]
                }
            },
        ))

    # Donut: Enrollments by Level (y=504, h=170) - right half
    if include_visual("EnquiryEnrollmentsByLevel"):
        write_json(f"{page3}/visuals/EnquiryEnrollmentsByLevel/visual.json", _visual_json(
            name="7788bb99cc00dd11ee22",
            visual_type="donutChart",
            x=645, y=504, w=625, h=170, tab_order=8, title="Enrollments by Level",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_PROGRAM, "Level"), "DimProgram.Level", "Level", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # ---------- Page 4: Student Demographics (2 slicers + bar/donut/area/combo) ----------
    page4 = f"{defn}/pages/{p_demographics}"
    write_header_bar(page4, "Student Demographics")
    write_nav_bar(page4, active_index=3)

    # Slicers (y=72, h=36)
    if include_visual("DemoSlicerCampus"):
        write_json(f"{page4}/visuals/DemoSlicerCampus/visual.json", _visual_json(
            name="8899cc00dd11ee22ff33",
            visual_type="slicer",
            x=10, y=72, w=625, h=36, tab_order=0, title="Campus",
            query_state={"Values": {"projections": [_projection(_col_field(T, "Campus"), "EnrollmentData.Campus", "Campus", True)]}},
        ))
    if include_visual("DemoSlicerYear"):
        write_json(f"{page4}/visuals/DemoSlicerYear/visual.json", _visual_json(
            name="9900dd11ee22ff33aa44",
            visual_type="slicer",
            x=645, y=72, w=625, h=36, tab_order=1, title="Year",
            query_state={"Values": {"projections": [_projection(_col_field(D_DATE, "Year"), "DimDate.Year", "Year", True)]}},
        ))

    # Clustered Bar: Enrollments by Campus (y=112, h=200)
    if include_visual("DemoByCampus"):
        write_json(f"{page4}/visuals/DemoByCampus/visual.json", _visual_json(
            name="aa11ee22ff33aa44bb55",
            visual_type="clusteredBarChart",
            x=10, y=112, w=625, h=200, tab_order=3, title="Enrollments by Campus",
            query_state={
                "Category": {"projections": [_projection(_col_field(T, "Campus"), "EnrollmentData.Campus", "Campus", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # Donut: Level distribution (y=112, h=200)
    if include_visual("DemoByLevel"):
        write_json(f"{page4}/visuals/DemoByLevel/visual.json", _visual_json(
            name="bb22ff33aa44bb55cc66",
            visual_type="donutChart",
            x=645, y=112, w=625, h=200, tab_order=4, title="Level Distribution",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_PROGRAM, "Level"), "DimProgram.Level", "Level", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # Area: Enrollment trend (y=318, h=180)
    if include_visual("DemoEnrollmentTrend"):
        write_json(f"{page4}/visuals/DemoEnrollmentTrend/visual.json", _visual_json(
            name="cc33aa44bb55cc66dd77",
            visual_type="areaChart",
            x=10, y=318, w=625, h=180, tab_order=5, title="Enrollment Trend",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_DATE, "YearMonth"), "DimDate.YearMonth", "YearMonth", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))

    # Bar: Satisfaction by Faculty (y=318, h=180)
    if include_visual("DemoInternationalSatisfaction"):
        write_json(f"{page4}/visuals/DemoInternationalSatisfaction/visual.json", _visual_json(
            name="dd44bb55cc66dd77ee88",
            visual_type="clusteredBarChart",
            x=645, y=318, w=625, h=180, tab_order=6, title="Avg Satisfaction by Faculty",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_FACULTY, "Faculty"), "DimFaculty.Faculty", "Faculty", True)]},
                "Y": {"projections": [_projection(_measure_field(T, "Avg Satisfaction"), "EnrollmentData.Avg Satisfaction", "Satisfaction")]},
            },
        ))

    # Table: Campus demographics (y=504, h=170) - left half
    if include_visual("DemoCampusTable"):
        write_json(f"{page4}/visuals/DemoCampusTable/visual.json", _visual_json(
            name="ee55cc66dd77ee88ff99",
            visual_type="tableEx",
            x=10, y=504, w=625, h=170, tab_order=7, title="Campus Demographics",
            query_state={
                "Values": {
                    "projections": [
                        _projection(_col_field(T, "Campus"), "EnrollmentData.Campus", "Campus"),
                        _projection(_col_field(D_FACULTY, "Faculty"), "DimFaculty.Faculty", "Faculty"),
                        _projection(_measure_field(T, "Total Enrollments"), "EnrollmentData.Total Enrollments", "Enrollments"),
                        _projection(_measure_field(T, "Avg Satisfaction"), "EnrollmentData.Avg Satisfaction", "Satisfaction"),
                    ]
                }
            },
        ))

    # Donut: Enrollments by Source (y=504, h=170) - right half
    if include_visual("DemoBySource"):
        write_json(f"{page4}/visuals/DemoBySource/visual.json", _visual_json(
            name="ff66dd77ee88ff99aa00",
            visual_type="donutChart",
            x=645, y=504, w=625, h=170, tab_order=8, title="Enrollments by Source",
            query_state={
                "Category": {"projections": [_projection(_col_field(D_SOURCE, "Source"), "DimSource.Source", "Source", True)]},
                "Y": {"projections": [_projection(_agg_col_field(T, "Enrollments", 0), "Sum(EnrollmentData.Enrollments)", "Enrollments")]},
            },
        ))


def gen_csv(data_rows):
    write_csv_file("data/enrollment_data.csv", data_rows)


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"Generating Power BI PBIR Project: {PROJECT_NAME}")
    print(f"Output: {PROJECT_DIR}")
    print()

    # Clean previous artifacts to avoid stale files/folders causing runtime issues.
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
        f"({len(FACULTIES)} faculties x {len(CAMPUSES)} campuses x {len(MONTHS)} months x {len(YEARS)} years)"
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
    print("  Page 1: Executive Overview (no slicers)")
    print("    - 4 KPIs, donut by faculty, combo enrollments/enquiries, bar + area charts, summary table + donut")
    print("  Page 2: Enrollment Analysis (Faculty, Year slicers)")
    print("    - Bar by program, donut by level, treemap tuition, line trend, detail table + area")
    print("  Page 3: Enquiry Pipeline (Source, Year slicers)")
    print("    - Donut by source, bar conversion, waterfall enquiries, offer rate bar, source table + donut")
    print("  Page 4: Student Demographics (Campus, Year slicers)")
    print("    - Bar by campus, donut level, area trend, combo international/satisfaction, campus table + donut")
    print()
    print("Data: 5 faculties, 10 programs, 3 campuses, 5 sources, 24 months (2023-2024)")
    print("Faculties: Business, Engineering, Science, Arts, Health")
    print("Campuses: Main Campus, City Campus, Online")
    print()
    print("If visuals do not render on first open, refresh once and")
    print("confirm PBIP/PBIR/TMDL preview features are enabled.")


if __name__ == "__main__":
    main()
