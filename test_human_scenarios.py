"""
Human Usage Scenario Tests for SageMaker Coding Agent

5 realistic scenarios with 5 steps each, simulating actual human usage.
Generates real output files for review.
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'compact'))

# Import agent (compact version)
from sagemaker_agent import (
    Config, CONFIG, BedrockClient, Agent, TOOLS, SECURITY,
    get_tool_definitions, tool_glob, tool_read_file, tool_write_file,
    tool_grep, tool_list_dir, tool_bash, tool_python_exec,
    tool_create_word, tool_create_excel, tool_create_markdown,
    tool_todo_write, tool_todo_read, _FILES_READ
)


class HumanScenarioTester:
    """Simulates human usage patterns with real tool execution."""

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(tempfile.gettempdir(), 'sagemaker_test_output')
        os.makedirs(self.output_dir, exist_ok=True)
        self.results = []
        self.original_workspace = CONFIG.workspace
        CONFIG.workspace = self.output_dir

    def log(self, msg: str):
        """Log with timestamp."""
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] {msg}")
        self.results.append(f"[{ts}] {msg}")

    def execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool and return result."""
        self.log(f"  [Calling {tool_name}]")
        self.log(f"  Args: {json.dumps(args, indent=2)[:200]}")

        tool_func = TOOLS.get(tool_name)
        if not tool_func:
            return f"Error: Unknown tool {tool_name}"

        try:
            result = tool_func[0](args)
            self.log(f"  [Result]: {result[:300]}{'...' if len(result) > 300 else ''}")
            return result
        except Exception as e:
            self.log(f"  [Error]: {e}")
            return f"Error: {e}"

    def run_scenario(self, name: str, steps: list) -> dict:
        """Run a scenario with multiple steps."""
        self.log(f"\n{'='*60}")
        self.log(f"SCENARIO: {name}")
        self.log(f"{'='*60}")

        results = {"name": name, "steps": [], "passed": True}

        for i, step in enumerate(steps, 1):
            self.log(f"\n--- Step {i}: {step['description']} ---")

            result = self.execute_tool(step['tool'], step['args'])

            step_result = {
                "step": i,
                "description": step['description'],
                "tool": step['tool'],
                "result": result[:500],
                "passed": "Error" not in result
            }
            results["steps"].append(step_result)

            if not step_result["passed"] and step.get("required", True):
                results["passed"] = False

        return results


def scenario_1_document_creation(tester: HumanScenarioTester) -> dict:
    """
    Scenario 1: User wants to create project documentation

    Simulates a user asking for Word and Excel documents.
    """
    steps = [
        {
            "description": "Check current directory contents",
            "tool": "list_dir",
            "args": {"path": tester.output_dir}
        },
        {
            "description": "Create project requirements Excel spreadsheet",
            "tool": "create_excel",
            "args": {
                "filepath": os.path.join(tester.output_dir, "project_requirements.xlsx"),
                "data": [
                    {"ID": "REQ-001", "Title": "User Authentication", "Priority": "High", "Status": "In Progress"},
                    {"ID": "REQ-002", "Title": "File Upload", "Priority": "Medium", "Status": "Pending"},
                    {"ID": "REQ-003", "Title": "Dashboard", "Priority": "High", "Status": "Pending"},
                    {"ID": "REQ-004", "Title": "API Integration", "Priority": "Low", "Status": "Not Started"},
                    {"ID": "REQ-005", "Title": "Report Generation", "Priority": "Medium", "Status": "Pending"}
                ],
                "sheet_name": "Requirements"
            }
        },
        {
            "description": "Create project overview Word document",
            "tool": "create_word",
            "args": {
                "filepath": os.path.join(tester.output_dir, "project_overview.docx"),
                "content": """Project Overview: SageMaker Coding Agent

Executive Summary:
The SageMaker Coding Agent is a secure AI-powered coding assistant designed for AWS SageMaker environments. It provides developers with intelligent code assistance while maintaining strict security boundaries.

Key Features:
- 15 specialized tools for file operations, search, and document creation
- Secure workspace boundary enforcement
- Session management for continuous workflows
- Real-time progress visibility

Technical Stack:
- Python 3.8+
- AWS Bedrock (Claude models)
- Jupyter notebooks (ipywidgets UI)
- Document generation (python-docx, openpyxl)

Next Steps:
1. Complete testing phase
2. Deploy to production SageMaker
3. User training sessions""",
                "title": "SageMaker Coding Agent - Project Overview"
            }
        },
        {
            "description": "Create technical notes in Markdown",
            "tool": "create_markdown",
            "args": {
                "filepath": os.path.join(tester.output_dir, "technical_notes.md"),
                "content": """# Technical Notes

## Architecture

The agent uses a ReAct (Reason + Act) loop:

1. Receive user message
2. Call LLM for reasoning
3. Execute tool if needed
4. Observe result
5. Repeat until complete

## Security Features

- Workspace boundary enforcement
- Secret detection in files
- Dangerous command blocking
- Audit logging

## Performance

- Average response time: 2-5 seconds
- Token efficiency: ~1000 tokens per turn
- Max context: 200K tokens
"""
            }
        },
        {
            "description": "Verify all documents were created",
            "tool": "list_dir",
            "args": {"path": tester.output_dir}
        }
    ]

    return tester.run_scenario("Document Creation Workflow", steps)


def scenario_2_code_project_setup(tester: HumanScenarioTester) -> dict:
    """
    Scenario 2: User sets up a new Python project

    Simulates creating project structure with todo tracking.
    """
    project_dir = os.path.join(tester.output_dir, "my_project")
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)

    steps = [
        {
            "description": "Create todo list for project setup",
            "tool": "todo_write",
            "args": {
                "todos": [
                    {"content": "Create main.py", "status": "in_progress", "activeForm": "Creating main.py"},
                    {"content": "Create utils.py", "status": "pending", "activeForm": "Creating utils.py"},
                    {"content": "Create test file", "status": "pending", "activeForm": "Creating test file"},
                    {"content": "Create requirements.txt", "status": "pending", "activeForm": "Creating requirements"},
                    {"content": "Verify structure", "status": "pending", "activeForm": "Verifying structure"}
                ]
            }
        },
        {
            "description": "Create main.py with application code",
            "tool": "write_file",
            "args": {
                "file_path": os.path.join(project_dir, "src", "main.py"),
                "content": '''"""Main application module."""

import argparse
from utils import validate_input, process_data


def main():
    """Entry point for the application."""
    parser = argparse.ArgumentParser(description="Data Processing Tool")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--output", default="output.json", help="Output file path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        print(f"Processing: {args.input}")

    # Validate and process
    if validate_input(args.input):
        result = process_data(args.input)
        print(f"Processed {len(result)} records")
        return 0
    else:
        print("Error: Invalid input")
        return 1


if __name__ == "__main__":
    exit(main())
'''
            }
        },
        {
            "description": "Create utils.py with helper functions",
            "tool": "write_file",
            "args": {
                "file_path": os.path.join(project_dir, "src", "utils.py"),
                "content": '''"""Utility functions for data processing."""

import os
import json
from typing import List, Dict, Any


def validate_input(file_path: str) -> bool:
    """Validate input file exists and is readable."""
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, 'r') as f:
            f.read(1)
        return True
    except (IOError, PermissionError):
        return False


def process_data(file_path: str) -> List[Dict[str, Any]]:
    """Process input file and return structured data."""
    results = []

    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                results.append({
                    "line": line_num,
                    "content": line,
                    "length": len(line)
                })

    return results


def save_results(results: List[Dict], output_path: str) -> bool:
    """Save results to JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        return True
    except IOError:
        return False
'''
            }
        },
        {
            "description": "Create test file",
            "tool": "write_file",
            "args": {
                "file_path": os.path.join(project_dir, "tests", "test_utils.py"),
                "content": '''"""Tests for utility functions."""

import pytest
import tempfile
import os
from src.utils import validate_input, process_data


def test_validate_input_existing_file():
    """Test validation passes for existing file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        assert validate_input(temp_path) == True
    finally:
        os.unlink(temp_path)


def test_validate_input_nonexistent_file():
    """Test validation fails for non-existent file."""
    assert validate_input("/nonexistent/path/file.txt") == False


def test_process_data():
    """Test data processing returns correct structure."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("line one\\nline two\\nline three\\n")
        temp_path = f.name

    try:
        results = process_data(temp_path)
        assert len(results) == 3
        assert results[0]["line"] == 1
        assert results[0]["content"] == "line one"
    finally:
        os.unlink(temp_path)
'''
            }
        },
        {
            "description": "Verify project structure with glob",
            "tool": "glob",
            "args": {
                "pattern": "**/*.py",
                "path": project_dir
            }
        }
    ]

    return tester.run_scenario("Python Project Setup", steps)


def scenario_3_code_search_and_analysis(tester: HumanScenarioTester) -> dict:
    """
    Scenario 3: User analyzes existing codebase

    Simulates searching and reading code files.
    """
    # Use the sagemaker-coding-agent directory for analysis
    agent_dir = os.path.dirname(os.path.abspath(__file__))

    steps = [
        {
            "description": "Find all Python files in project",
            "tool": "glob",
            "args": {
                "pattern": "**/*.py",
                "path": agent_dir
            }
        },
        {
            "description": "Search for security-related code",
            "tool": "grep",
            "args": {
                "pattern": "security|validate|blocked",
                "path": agent_dir,
                "glob": "**/*.py",
                "case_insensitive": True,
                "limit": 20
            }
        },
        {
            "description": "Search for tool definitions",
            "tool": "grep",
            "args": {
                "pattern": "def tool_",
                "path": os.path.join(agent_dir, "compact"),
                "output_mode": "content",
                "context": 1,
                "limit": 10
            }
        },
        {
            "description": "Read the main agent file (first 50 lines)",
            "tool": "read_file",
            "args": {
                "file_path": os.path.join(agent_dir, "compact", "sagemaker_agent.py"),
                "limit": 50
            }
        },
        {
            "description": "List directory structure",
            "tool": "list_dir",
            "args": {
                "path": agent_dir
            }
        }
    ]

    return tester.run_scenario("Code Search and Analysis", steps)


def scenario_4_data_analysis_with_excel(tester: HumanScenarioTester) -> dict:
    """
    Scenario 4: User creates data analysis report

    Simulates creating Excel with analyzed data.
    """
    steps = [
        {
            "description": "Create sales data Excel file",
            "tool": "create_excel",
            "args": {
                "filepath": os.path.join(tester.output_dir, "sales_report.xlsx"),
                "data": [
                    {"Month": "January", "Sales": 15000, "Expenses": 8000, "Profit": 7000, "Growth": "N/A"},
                    {"Month": "February", "Sales": 18000, "Expenses": 9000, "Profit": 9000, "Growth": "28.6%"},
                    {"Month": "March", "Sales": 22000, "Expenses": 10000, "Profit": 12000, "Growth": "33.3%"},
                    {"Month": "April", "Sales": 25000, "Expenses": 11000, "Profit": 14000, "Growth": "16.7%"},
                    {"Month": "May", "Sales": 28000, "Expenses": 12000, "Profit": 16000, "Growth": "14.3%"},
                    {"Month": "June", "Sales": 32000, "Expenses": 13000, "Profit": 19000, "Growth": "18.8%"},
                ],
                "sheet_name": "Monthly Sales"
            }
        },
        {
            "description": "Create analysis summary document",
            "tool": "create_word",
            "args": {
                "filepath": os.path.join(tester.output_dir, "sales_analysis.docx"),
                "content": """Sales Performance Analysis Report
Q1-Q2 2024

Executive Summary:
Sales have shown consistent growth over the first two quarters, with total revenue of $140,000 and net profit of $77,000.

Key Findings:
1. Strong month-over-month growth averaging 22%
2. Expense ratio decreased from 53% to 41%
3. Profit margins improved from 47% to 59%

Recommendations:
- Scale marketing efforts in Q3
- Optimize operational costs
- Expand product line based on customer feedback

Data Source: See attached Excel file (sales_report.xlsx)""",
                "title": "Sales Performance Analysis - Q1/Q2 2024"
            }
        },
        {
            "description": "Create Python script for data processing",
            "tool": "write_file",
            "args": {
                "file_path": os.path.join(tester.output_dir, "analyze_sales.py"),
                "content": '''"""Sales data analysis script."""

import pandas as pd

def analyze_sales(filepath: str) -> dict:
    """Analyze sales data from Excel file."""
    df = pd.read_excel(filepath)

    analysis = {
        "total_sales": df["Sales"].sum(),
        "total_expenses": df["Expenses"].sum(),
        "total_profit": df["Profit"].sum(),
        "avg_monthly_sales": df["Sales"].mean(),
        "best_month": df.loc[df["Sales"].idxmax(), "Month"],
        "profit_margin": (df["Profit"].sum() / df["Sales"].sum()) * 100
    }

    return analysis

if __name__ == "__main__":
    result = analyze_sales("sales_report.xlsx")
    print("Sales Analysis Results:")
    for key, value in result.items():
        print(f"  {key}: {value}")
'''
            }
        },
        {
            "description": "Create Markdown summary",
            "tool": "create_markdown",
            "args": {
                "filepath": os.path.join(tester.output_dir, "sales_summary.md"),
                "content": """# Sales Summary Q1-Q2 2024

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Sales | $140,000 |
| Total Profit | $77,000 |
| Average Monthly Growth | 22% |
| Best Month | June |

## Files Generated

1. `sales_report.xlsx` - Raw data
2. `sales_analysis.docx` - Full report
3. `analyze_sales.py` - Analysis script

## Next Steps

- [ ] Review with stakeholders
- [ ] Plan Q3 strategy
- [ ] Update forecasts
"""
            }
        },
        {
            "description": "List all generated files",
            "tool": "list_dir",
            "args": {"path": tester.output_dir}
        }
    ]

    return tester.run_scenario("Data Analysis with Excel/Word", steps)


def scenario_5_error_handling_and_recovery(tester: HumanScenarioTester) -> dict:
    """
    Scenario 5: User encounters and handles errors

    Simulates error scenarios and recovery patterns.
    """
    steps = [
        {
            "description": "Try to read non-existent file",
            "tool": "read_file",
            "args": {
                "file_path": "/nonexistent/path/file.txt"
            },
            "required": False  # Expected to fail
        },
        {
            "description": "Try to write outside workspace (should be blocked)",
            "tool": "write_file",
            "args": {
                "file_path": "/etc/test_blocked.txt",
                "content": "This should be blocked"
            },
            "required": False  # Expected to fail
        },
        {
            "description": "Try grep with invalid regex",
            "tool": "grep",
            "args": {
                "pattern": "[invalid(regex",
                "path": tester.output_dir
            },
            "required": False  # Expected to fail
        },
        {
            "description": "Create valid file after errors",
            "tool": "write_file",
            "args": {
                "file_path": os.path.join(tester.output_dir, "recovery_test.txt"),
                "content": "This file was created after handling errors.\nThe agent recovered successfully."
            }
        },
        {
            "description": "Verify file was created",
            "tool": "read_file",
            "args": {
                "file_path": os.path.join(tester.output_dir, "recovery_test.txt")
            }
        }
    ]

    return tester.run_scenario("Error Handling and Recovery", steps)


def run_all_scenarios():
    """Run all human usage scenarios."""
    print("=" * 70)
    print("HUMAN USAGE SCENARIO TESTS")
    print("SageMaker Coding Agent")
    print("=" * 70)
    print(f"Output directory: Will be shown below")
    print()

    # Create tester
    tester = HumanScenarioTester()
    print(f"Output directory: {tester.output_dir}")
    print()

    # Run all scenarios
    scenarios = [
        scenario_1_document_creation,
        scenario_2_code_project_setup,
        scenario_3_code_search_and_analysis,
        scenario_4_data_analysis_with_excel,
        scenario_5_error_handling_and_recovery,
    ]

    all_results = []

    for scenario_func in scenarios:
        try:
            result = scenario_func(tester)
            all_results.append(result)
        except Exception as e:
            print(f"ERROR in {scenario_func.__name__}: {e}")
            all_results.append({
                "name": scenario_func.__name__,
                "passed": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in all_results if r.get("passed", False))
    total = len(all_results)

    for result in all_results:
        status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
        print(f"{status} - {result['name']}")
        if "steps" in result:
            for step in result["steps"]:
                step_status = "✓" if step["passed"] else "✗"
                print(f"    {step_status} Step {step['step']}: {step['description']}")

    print(f"\nTotal: {passed}/{total} scenarios passed")
    print(f"\n📁 Output files created in: {tester.output_dir}")
    print("\nGenerated files to review:")
    for f in os.listdir(tester.output_dir):
        filepath = os.path.join(tester.output_dir, f)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            print(f"  - {f} ({size:,} bytes)")

    return all_results


if __name__ == "__main__":
    results = run_all_scenarios()
