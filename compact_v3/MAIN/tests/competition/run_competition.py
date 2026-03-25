#!/usr/bin/env python3
"""
SageAgent V3 — 10 Complex Task Competition
Runs 10 medium-to-hard tasks through V3 agent with real Bedrock API.
Tracks: correctness, cost, latency, tool calls, and diagnosis info.

Usage: cd compact_v3/MAIN/agent && python3 ../tests/competition/run_competition.py
"""
import sys, os, json, time, tempfile, shutil

AGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agent")
sys.path.insert(0, AGENT_DIR)

LIVE_MODEL = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "ap-southeast-2"
COMP_DIR = os.path.dirname(__file__)

# ============================================================
# HELPERS
# ============================================================
RESULTS = []

def run_agent(task, system=None, max_turns=12):
    """Run V3 agent on a task, return (result, outputs, cost, calls, elapsed)."""
    from sagemaker_agent import Agent, BedrockClient, TOKENS
    client = BedrockClient(model_id=LIVE_MODEL, region=REGION)
    c0, t0 = TOKENS.session_cost, TOKENS.api_calls
    outputs = []
    agent = Agent(client, f"comp_{int(time.time())}",
                  on_approval=lambda *a, **k: True,
                  on_ask_user=lambda *a, **k: "yes, proceed")
    start = time.time()
    result = agent.run(task,
                       system_prompt=system or "You are an expert coding assistant. Use tools to complete tasks. Be thorough and precise.",
                       output_fn=lambda t: outputs.append(t),
                       max_turns_override=max_turns)
    elapsed = time.time() - start
    cost = TOKENS.session_cost - c0
    calls = TOKENS.api_calls - t0
    return result, outputs, cost, calls, elapsed


def score_task(task_id, name, prompt, check_fn, max_turns=12):
    """Run a task through V3 and score it."""
    print(f"\n{'='*60}")
    print(f"TASK {task_id}: {name}")
    print(f"{'='*60}")
    try:
        result, outputs, cost, calls, elapsed = run_agent(prompt, max_turns=max_turns)
        passed, detail = check_fn(result, outputs)
        status = "PASS" if passed else "FAIL"
    except Exception as e:
        import traceback
        result, cost, calls, elapsed = str(e), 0, 0, 0
        passed, detail = False, f"ERROR: {e}\n{traceback.format_exc()}"
        status = "ERROR"

    icon = {"PASS": "✓", "FAIL": "✗", "ERROR": "!"}[status]
    print(f"  [{icon}] {status} ({elapsed:.1f}s, ${cost:.4f}, {calls} calls)")
    print(f"  Detail: {detail[:200]}")

    entry = {
        "task_id": task_id,
        "name": name,
        "status": status,
        "passed": passed,
        "detail": detail[:500],
        "cost": cost,
        "calls": calls,
        "elapsed": elapsed,
        "result_preview": result[:300] if result else "",
    }
    RESULTS.append(entry)
    return passed


# ============================================================
# SETUP: Create test files for tasks
# ============================================================
from sagemaker_agent import CONFIG
WS = CONFIG.workspace

def setup_files():
    """Create all test files needed for the 10 tasks."""

    # --- Task 1: Multi-file bug (3 files, bug spans across them) ---
    os.makedirs(os.path.join(WS, "comp_task1"), exist_ok=True)
    with open(os.path.join(WS, "comp_task1/models.py"), "w") as f:
        f.write('''class User:
    def __init__(self, name, email, role="user"):
        self.name = name
        self.email = email
        self.role = role

    def is_admin(self):
        return self.role == "admin"

    def to_dict(self):
        return {"name": self.name, "email": self.email, "role": self.role}
''')
    with open(os.path.join(WS, "comp_task1/auth.py"), "w") as f:
        f.write('''from models import User

def authenticate(username, password, user_db):
    """Authenticate user and return User object or None."""
    for user_data in user_db:
        if user_data["username"] == username and user_data["password"] == password:
            return User(user_data["name"], user_data["email"], user_data.get("role", "user"))
    return None

def check_permission(user, required_role):
    """Check if user has required permission level."""
    role_hierarchy = {"user": 1, "editor": 2, "admin": 3}
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 99)
    return user_level >= required_level
''')
    with open(os.path.join(WS, "comp_task1/api.py"), "w") as f:
        f.write('''from auth import authenticate, check_permission

USER_DB = [
    {"username": "alice", "password": "pass123", "name": "Alice", "email": "alice@co.com", "role": "admin"},
    {"username": "bob", "password": "pass456", "name": "Bob", "email": "bob@co.com", "role": "editor"},
    {"username": "charlie", "password": "pass789", "name": "Charlie", "email": "charlie@co.com"},
]

def delete_user(current_user, target_username):
    """Delete a user. Only admins can delete. Bug: doesn't check permission!"""
    # BUG: This should check if current_user is admin before deleting
    for i, u in enumerate(USER_DB):
        if u["username"] == target_username:
            USER_DB.pop(i)
            return {"status": "deleted", "user": target_username}
    return {"status": "not_found"}

def update_user_role(current_user, target_username, new_role):
    """Update user role. Bug: allows privilege escalation!"""
    # BUG: editor can promote themselves to admin
    if not check_permission(current_user, "editor"):
        return {"status": "forbidden"}
    for u in USER_DB:
        if u["username"] == target_username:
            u["role"] = new_role
            return {"status": "updated", "new_role": new_role}
    return {"status": "not_found"}
''')

    # --- Task 2: CSV data for analysis ---
    with open(os.path.join(WS, "comp_task2_sales.csv"), "w") as f:
        f.write("month,product,revenue,units,region\n")
        import random
        random.seed(42)
        products = ["Widget A", "Widget B", "Gadget X"]
        regions = ["North", "South", "East", "West"]
        for month in range(1, 13):
            for prod in products:
                for region in regions:
                    rev = random.randint(5000, 50000)
                    units = random.randint(50, 500)
                    f.write(f"2025-{month:02d},{prod},{rev},{units},{region}\n")

    # --- Task 3: Code with security issues ---
    with open(os.path.join(WS, "comp_task3_vulnerable.py"), "w") as f:
        f.write('''import sqlite3
import os
import pickle

def get_user(username):
    """Get user from database."""
    conn = sqlite3.connect("users.db")
    # SQL INJECTION: string formatting in query
    query = f"SELECT * FROM users WHERE username = '{username}'"
    result = conn.execute(query).fetchone()
    conn.close()
    return result

def render_page(user_input):
    """Render HTML page with user content."""
    # XSS: unsanitized user input in HTML
    return f"<html><body><h1>Welcome {user_input}</h1></body></html>"

def load_config(filepath):
    """Load configuration from file."""
    # INSECURE DESERIALIZATION: pickle from untrusted source
    with open(filepath, "rb") as f:
        return pickle.load(f)

def run_command(user_cmd):
    """Run a system command."""
    # COMMAND INJECTION: unsanitized shell command
    os.system(f"echo {user_cmd}")

def hash_password(password):
    """Hash a password."""
    # WEAK CRYPTO: MD5 for passwords
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

API_KEY = "sk-proj-abc123def456"  # HARDCODED SECRET
''')

    # --- Task 4: Duplicated code to refactor ---
    with open(os.path.join(WS, "comp_task4_duplicate.py"), "w") as f:
        f.write('''import json
from datetime import datetime

def process_orders(orders_file):
    """Process orders from JSON file."""
    with open(orders_file) as f:
        data = json.load(f)
    results = []
    for item in data:
        if item.get("status") != "active":
            continue
        total = item["quantity"] * item["price"]
        tax = total * 0.1
        discount = total * 0.05 if item.get("member") else 0
        final = total + tax - discount
        results.append({
            "id": item["id"],
            "total": round(final, 2),
            "processed_at": datetime.now().isoformat()
        })
    return results

def process_invoices(invoices_file):
    """Process invoices from JSON file."""
    with open(invoices_file) as f:
        data = json.load(f)
    results = []
    for item in data:
        if item.get("status") != "active":
            continue
        total = item["quantity"] * item["price"]
        tax = total * 0.1
        discount = total * 0.05 if item.get("member") else 0
        final = total + tax - discount
        results.append({
            "id": item["id"],
            "total": round(final, 2),
            "processed_at": datetime.now().isoformat()
        })
    return results

def process_refunds(refunds_file):
    """Process refunds from JSON file."""
    with open(refunds_file) as f:
        data = json.load(f)
    results = []
    for item in data:
        if item.get("status") != "active":
            continue
        total = item["quantity"] * item["price"]
        tax = total * 0.1
        discount = total * 0.05 if item.get("member") else 0
        final = total + tax - discount
        results.append({
            "id": item["id"],
            "total": round(final, 2),
            "processed_at": datetime.now().isoformat()
        })
    return results
''')

    # --- Task 5: API spec for client generation ---
    with open(os.path.join(WS, "comp_task5_api_spec.json"), "w") as f:
        json.dump({
            "base_url": "https://api.example.com/v1",
            "endpoints": [
                {"method": "GET", "path": "/users", "params": ["page", "limit"], "returns": "list of users"},
                {"method": "GET", "path": "/users/{id}", "params": [], "returns": "single user"},
                {"method": "POST", "path": "/users", "body": {"name": "str", "email": "str"}, "returns": "created user"},
                {"method": "PUT", "path": "/users/{id}", "body": {"name": "str", "email": "str"}, "returns": "updated user"},
                {"method": "DELETE", "path": "/users/{id}", "params": [], "returns": "204 no content"},
            ]
        }, f, indent=2)

    # --- Task 6: Create a test image for vision ---
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(["Q1", "Q2", "Q3", "Q4"], [150, 230, 180, 310], color=["#e74c3c", "#3498db", "#2ecc71", "#f1c40f"])
        ax.set_title("Quarterly Revenue ($K)", fontsize=16)
        ax.set_ylabel("Revenue ($K)")
        # Intentional issues: no grid, no data labels, cramped spacing, missing legend
        fig.savefig(os.path.join(WS, "comp_task6_chart.png"), dpi=100, bbox_inches="tight")
        plt.close()
    except Exception:
        pass  # Skip if matplotlib not available

    # --- Task 7: Slow code to optimize ---
    with open(os.path.join(WS, "comp_task7_slow.py"), "w") as f:
        f.write('''def find_duplicates(items):
    """Find all duplicate items in a list. SLOW: O(n^2)."""
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates

def count_word_frequencies(text):
    """Count word frequencies. SLOW: rebuilds list each time."""
    words = text.lower().split()
    frequencies = []
    counted = []
    for word in words:
        if word not in counted:
            count = 0
            for w in words:
                if w == word:
                    count += 1
            frequencies.append((word, count))
            counted.append(word)
    return sorted(frequencies, key=lambda x: -x[1])

def merge_sorted_lists(list1, list2):
    """Merge two sorted lists. SLOW: sorts after concatenation instead of merge."""
    result = list1 + list2
    # Bubble sort instead of merge
    for i in range(len(result)):
        for j in range(len(result) - 1):
            if result[j] > result[j+1]:
                result[j], result[j+1] = result[j+1], result[j]
    return result
''')

    # --- Task 8: Code without tests ---
    with open(os.path.join(WS, "comp_task8_untested.py"), "w") as f:
        f.write('''from datetime import datetime, timedelta

class Scheduler:
    """Simple task scheduler."""

    def __init__(self):
        self.tasks = []

    def add_task(self, name, due_date, priority=1):
        """Add a task. Priority 1=low, 2=medium, 3=high."""
        if not name or not name.strip():
            raise ValueError("Task name cannot be empty")
        if priority not in (1, 2, 3):
            raise ValueError(f"Invalid priority: {priority}")
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
        self.tasks.append({"name": name.strip(), "due": due_date, "priority": priority, "done": False})

    def complete_task(self, name):
        """Mark a task as done."""
        for task in self.tasks:
            if task["name"] == name and not task["done"]:
                task["done"] = True
                return True
        return False

    def get_overdue(self, now=None):
        """Get all overdue incomplete tasks."""
        now = now or datetime.now()
        return [t for t in self.tasks if not t["done"] and t["due"] < now]

    def get_by_priority(self, priority):
        """Get tasks by priority level."""
        return [t for t in self.tasks if t["priority"] == priority and not t["done"]]

    def get_next_week(self, now=None):
        """Get tasks due in the next 7 days."""
        now = now or datetime.now()
        week_later = now + timedelta(days=7)
        return [t for t in self.tasks if not t["done"] and now <= t["due"] <= week_later]

    def summary(self):
        """Get task summary statistics."""
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["done"])
        overdue = len(self.get_overdue())
        return {"total": total, "done": done, "pending": total - done, "overdue": overdue}
''')

    # --- Task 9: Multi-agent project files ---
    os.makedirs(os.path.join(WS, "comp_task9_project"), exist_ok=True)
    for name, content in [
        ("README.md", "# MyApp\nA Flask web app. Needs: routes, models, tests.\n"),
        ("requirements.txt", "flask>=3.0\npytest\nsqlalchemy\n"),
        ("app.py", "# TODO: implement Flask app with /health, /users endpoints\n"),
        ("models.py", "# TODO: implement User model with SQLAlchemy\n"),
        ("tests/test_app.py", "# TODO: implement tests for /health and /users\n"),
    ]:
        path = os.path.join(WS, "comp_task9_project", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

    # --- Task 10: Requirements doc ---
    with open(os.path.join(WS, "comp_task10_requirements.txt"), "w") as f:
        f.write("""Build a Python CLI tool called "taskr" that:
1. Stores tasks in a JSON file (~/.taskr.json)
2. Commands: add, list, done, delete, search
3. Each task has: id (auto-increment), title, created_at, done (bool), tags (list)
4. `taskr add "Buy groceries" --tags shopping,home`
5. `taskr list` shows all pending tasks, `taskr list --all` includes done
6. `taskr done <id>` marks task as done
7. `taskr delete <id>` removes task
8. `taskr search <keyword>` searches title and tags
9. Must handle edge cases: empty list, invalid id, duplicate tags
10. Include argparse CLI, at least 5 unit tests
""")

    print("Setup complete: 10 task files created")

setup_files()


# ============================================================
# TASK 1: Multi-File Bug Hunt (3 files, 2 security bugs)
# ============================================================
def check_t1(result, outputs):
    r = result.lower()
    found_delete_bug = "delete" in r and ("admin" in r or "permission" in r or "check" in r)
    found_escalation_bug = "escalat" in r or ("editor" in r and "admin" in r) or "privilege" in r
    # Check if agent actually fixed the code
    api_path = os.path.join(WS, "comp_task1/api.py")
    if os.path.exists(api_path):
        code = open(api_path).read()
        has_delete_fix = "check_permission" in code and "delete_user" in code and "admin" in code.split("delete_user")[1][:200] if "delete_user" in code else False
        has_escalation_fix = "admin" in code.split("update_user_role")[1][:300] if "update_user_role" in code else False
    else:
        has_delete_fix = has_escalation_fix = False
    score = sum([found_delete_bug, found_escalation_bug, has_delete_fix, has_escalation_fix])
    return score >= 3, f"delete_bug={'✓' if found_delete_bug else '✗'}, escalation={'✓' if found_escalation_bug else '✗'}, delete_fixed={'✓' if has_delete_fix else '✗'}, escalation_fixed={'✓' if has_escalation_fix else '✗'}"

score_task(1, "Multi-file bug hunt (2 security bugs across 3 files)",
    "Read all files in comp_task1/. There are 2 security bugs that span across the files. "
    "Find both bugs, explain what makes them dangerous, and fix them using edit_file. "
    "Bug 1 is in delete_user. Bug 2 is in update_user_role.",
    check_t1)


# ============================================================
# TASK 2: CSV → Chart → Word Report
# ============================================================
def check_t2(result, outputs):
    chart_exists = os.path.exists(os.path.join(WS, "comp_task2_chart.png"))
    report_exists = os.path.exists(os.path.join(WS, "comp_task2_report.docx"))
    mentioned_data = any(w in result.lower() for w in ["revenue", "product", "region", "widget", "gadget"])
    return chart_exists and report_exists and mentioned_data, f"chart={'✓' if chart_exists else '✗'}, report={'✓' if report_exists else '✗'}, analysis={'✓' if mentioned_data else '✗'}"

score_task(2, "CSV → Chart → Word report pipeline",
    "Read comp_task2_sales.csv. Analyze the data: find total revenue by product and by region. "
    "Create a bar chart (comp_task2_chart.png) showing revenue by product. "
    "Then create a Word report (comp_task2_report.docx) with: title, summary of findings, the chart embedded, and a recommendation.",
    check_t2)


# ============================================================
# TASK 3: Security Audit (6 vulnerabilities)
# ============================================================
def check_t3(result, outputs):
    r = result.lower()
    found = {
        "sql_injection": "sql" in r and "inject" in r,
        "xss": "xss" in r or "cross.site" in r or "sanitiz" in r,
        "pickle": "pickle" in r or "deserializ" in r,
        "cmd_injection": "command" in r and "inject" in r or "os.system" in r,
        "weak_hash": "md5" in r or "weak" in r and "hash" in r,
        "hardcoded_secret": "api_key" in r or "hardcod" in r or "secret" in r,
    }
    count = sum(found.values())
    detail = ", ".join(f"{k}={'✓' if v else '✗'}" for k, v in found.items())
    return count >= 5, f"{count}/6 found: {detail}"

score_task(3, "Security audit (find 6 OWASP vulnerabilities)",
    "Read comp_task3_vulnerable.py and perform a thorough security audit. "
    "Find ALL security vulnerabilities. For each one: name the vulnerability type (OWASP category), "
    "explain the risk, show the vulnerable line, and suggest a fix. There are at least 6 issues.",
    check_t3)


# ============================================================
# TASK 4: Refactor Duplicate Code
# ============================================================
def check_t4(result, outputs):
    path = os.path.join(WS, "comp_task4_duplicate.py")
    if not os.path.exists(path):
        return False, "file not found"
    code = open(path).read()
    # Check: should have a shared function, and the 3 process_ functions should call it
    has_shared = "def " in code and code.count("def process_") < 3  # Should reduce to fewer functions
    # Or: has a helper function that the others call
    lines = code.split("\n")
    func_count = sum(1 for l in lines if l.strip().startswith("def "))
    is_shorter = len(lines) < 55  # Original is ~60 lines, refactored should be shorter
    no_duplicate = code.count("tax = total * 0.1") <= 1  # Should only appear once
    return no_duplicate and (is_shorter or func_count <= 4), f"funcs={func_count}, lines={len(lines)}, single_tax={'✓' if no_duplicate else '✗'}"

score_task(4, "Refactor duplicate code into shared module",
    "Read comp_task4_duplicate.py. The three functions have nearly identical logic. "
    "Refactor to extract the shared calculation into a single helper function. "
    "The three process_ functions should call the helper. Use edit_file to modify the file in place.",
    check_t4)


# ============================================================
# TASK 5: REST API Client + Tests
# ============================================================
def check_t5(result, outputs):
    client_path = os.path.join(WS, "comp_task5_client.py")
    test_path = os.path.join(WS, "comp_task5_test.py")
    client_exists = os.path.exists(client_path)
    test_exists = os.path.exists(test_path)
    if client_exists:
        code = open(client_path).read()
        has_get = "def get" in code or "def list" in code or "def fetch" in code
        has_post = "def create" in code or "def post" in code
        has_delete = "def delete" in code
        has_error = "except" in code or "raise" in code or "status_code" in code
    else:
        has_get = has_post = has_delete = has_error = False
    if test_exists:
        test_code = open(test_path).read()
        test_count = test_code.count("def test_")
    else:
        test_count = 0
    return client_exists and test_exists and has_get and has_post and test_count >= 3, \
        f"client={'✓' if client_exists else '✗'}, tests={test_count}, get={'✓' if has_get else '✗'}, post={'✓' if has_post else '✗'}, delete={'✓' if has_delete else '✗'}, errors={'✓' if has_error else '✗'}"

score_task(5, "Generate REST API client + tests from spec",
    "Read comp_task5_api_spec.json. Generate a Python API client (comp_task5_client.py) that: "
    "implements all 5 endpoints, uses requests library, has proper error handling (raise on non-2xx), "
    "and has type hints. Also generate tests (comp_task5_test.py) with at least 5 test functions using unittest.mock.",
    check_t5)


# ============================================================
# TASK 6: Image Analysis (Vision)
# ============================================================
def check_t6(result, outputs):
    r = result.lower()
    if not os.path.exists(os.path.join(WS, "comp_task6_chart.png")):
        return False, "test image not created (matplotlib missing?)"
    saw_chart = "chart" in r or "bar" in r or "revenue" in r or "quarter" in r
    gave_feedback = "grid" in r or "label" in r or "legend" in r or "improv" in r or "suggest" in r or "missing" in r
    return saw_chart and gave_feedback, f"understood={'✓' if saw_chart else '✗'}, feedback={'✓' if gave_feedback else '✗'}"

score_task(6, "Image analysis: describe chart and suggest improvements",
    "Use view_image to look at comp_task6_chart.png. Describe what the chart shows (data, type, colors). "
    "Then suggest at least 3 specific improvements to make it more professional (e.g., missing elements, readability).",
    check_t6)


# ============================================================
# TASK 7: Performance Optimization
# ============================================================
def check_t7(result, outputs):
    path = os.path.join(WS, "comp_task7_slow.py")
    if not os.path.exists(path):
        return False, "file not found"
    code = open(path).read()
    r = result.lower()
    # Check optimizations
    uses_set_or_dict = "set(" in code or "dict(" in code or "Counter" in code or "{}" in code
    no_bubble = "bubble" not in code.lower() and code.count("for j in range") == 0
    explained = "o(n" in r or "complex" in r or "time" in r or "efficien" in r
    return uses_set_or_dict and no_bubble and explained, \
        f"set/dict={'✓' if uses_set_or_dict else '✗'}, no_bubble={'✓' if no_bubble else '✗'}, explained={'✓' if explained else '✗'}"

score_task(7, "Performance optimization: fix 3 slow algorithms",
    "Read comp_task7_slow.py. There are 3 functions with O(n²) or worse performance. "
    "For each: explain the current complexity, show the optimized version, and state the new complexity. "
    "Fix all 3 functions using edit_file.",
    check_t7)


# ============================================================
# TASK 8: Test Generation
# ============================================================
def check_t8(result, outputs):
    test_path = os.path.join(WS, "comp_task8_tests.py")
    if not os.path.exists(test_path):
        # Check if agent wrote to a different name
        for name in os.listdir(WS):
            if "task8" in name and "test" in name and name.endswith(".py"):
                test_path = os.path.join(WS, name)
                break
    if not os.path.exists(test_path):
        return False, "no test file created"
    code = open(test_path).read()
    test_count = code.count("def test_")
    has_edge = "empty" in code.lower() or "invalid" in code.lower() or "error" in code.lower() or "raise" in code.lower()
    has_import = "Scheduler" in code
    return test_count >= 5 and has_edge and has_import, f"tests={test_count}, edge_cases={'✓' if has_edge else '✗'}, imports={'✓' if has_import else '✗'}"

score_task(8, "Generate comprehensive tests for Scheduler class",
    "Read comp_task8_untested.py. Write comprehensive tests (comp_task8_tests.py) for the Scheduler class. "
    "Cover: add_task (valid + invalid), complete_task (exists + not exists), get_overdue, get_by_priority, "
    "get_next_week, summary. Include edge cases: empty scheduler, invalid priority, empty name. At least 8 test functions.",
    check_t8)


# ============================================================
# TASK 9: Multi-Agent Orchestration
# ============================================================
def check_t9(result, outputs):
    proj = os.path.join(WS, "comp_task9_project")
    app_code = open(os.path.join(proj, "app.py")).read() if os.path.exists(os.path.join(proj, "app.py")) else ""
    models_code = open(os.path.join(proj, "models.py")).read() if os.path.exists(os.path.join(proj, "models.py")) else ""
    has_routes = "route" in app_code.lower() or "@app" in app_code
    has_health = "health" in app_code.lower()
    has_model = "class" in models_code and ("User" in models_code or "user" in models_code.lower())
    has_flask = "Flask" in app_code or "flask" in app_code
    return has_routes and has_health and has_model and has_flask, \
        f"routes={'✓' if has_routes else '✗'}, health={'✓' if has_health else '✗'}, model={'✓' if has_model else '✗'}, flask={'✓' if has_flask else '✗'}"

score_task(9, "Multi-step project: implement Flask app from TODOs",
    "Look at comp_task9_project/. Read README.md for requirements. Then: "
    "1) Implement models.py with a User class (id, name, email, created_at). "
    "2) Implement app.py with Flask routes: GET /health (returns {status: ok}), GET /users (returns list), POST /users (creates user). "
    "3) Use proper error handling and JSON responses.",
    check_t9, max_turns=15)


# ============================================================
# TASK 10: Full Project Scaffold from Requirements
# ============================================================
def check_t10(result, outputs):
    taskr_path = os.path.join(WS, "taskr.py")
    if not os.path.exists(taskr_path):
        for name in os.listdir(WS):
            if "taskr" in name and name.endswith(".py"):
                taskr_path = os.path.join(WS, name)
                break
    if not os.path.exists(taskr_path):
        return False, "taskr.py not created"
    code = open(taskr_path).read()
    has_argparse = "argparse" in code
    has_add = "add" in code and "title" in code.lower()
    has_list = "list" in code
    has_done = "done" in code
    has_json = "json" in code
    has_search = "search" in code
    # Check for test file
    test_exists = any("test" in f and "taskr" in f for f in os.listdir(WS) if f.endswith(".py"))
    return has_argparse and has_add and has_list and has_done and has_json, \
        f"argparse={'✓' if has_argparse else '✗'}, add={'✓' if has_add else '✗'}, list={'✓' if has_list else '✗'}, done={'✓' if has_done else '✗'}, json={'✓' if has_json else '✗'}, search={'✓' if has_search else '✗'}, tests={'✓' if test_exists else '✗'}"

score_task(10, "Full project scaffold from requirements",
    "Read comp_task10_requirements.txt. Build the complete 'taskr' CLI tool as taskr.py. "
    "Implement ALL features listed in the requirements. Use argparse for CLI. "
    "Also write at least 5 tests in test_taskr.py.",
    check_t10, max_turns=15)


# ============================================================
# CLEANUP
# ============================================================
def cleanup():
    """Remove test files."""
    for name in ["comp_task1", "comp_task9_project"]:
        path = os.path.join(WS, name)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    for f in os.listdir(WS):
        if f.startswith("comp_task") or f.startswith("taskr") or f.startswith("test_taskr"):
            path = os.path.join(WS, f)
            if os.path.isfile(path):
                os.unlink(path)

cleanup()


# ============================================================
# RESULTS REPORT
# ============================================================
print("\n" + "=" * 70)
print("V3 COMPETITION RESULTS")
print("=" * 70)

total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["passed"])
total_cost = sum(r["cost"] for r in RESULTS)
total_time = sum(r["elapsed"] for r in RESULTS)
total_calls = sum(r["calls"] for r in RESULTS)

print(f"\n{'Task':<50s} {'Status':>6s} {'Time':>6s} {'Cost':>8s} {'Calls':>5s}")
print("-" * 75)
for r in RESULTS:
    icon = "✓" if r["passed"] else "✗"
    print(f"  [{icon}] {r['name'][:46]:<46s} {r['status']:>6s} {r['elapsed']:>5.1f}s ${r['cost']:>6.4f} {r['calls']:>5d}")
print("-" * 75)
print(f"  {'TOTAL':<48s} {passed}/{total} {total_time:>5.1f}s ${total_cost:>6.4f} {total_calls:>5d}")
print(f"\n  Pass rate: {passed/total*100:.0f}%")
print(f"  Avg cost per task: ${total_cost/total:.4f}")
print(f"  Avg time per task: {total_time/total:.1f}s")

# Save results to JSON
results_path = os.path.join(COMP_DIR, "v3_results.json")
with open(results_path, "w") as f:
    json.dump({
        "agent": "SageAgent V3.2.2",
        "model": LIVE_MODEL,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": {"total": total, "passed": passed, "cost": total_cost, "time": total_time, "calls": total_calls},
        "tasks": RESULTS,
    }, f, indent=2)
print(f"\n  Results saved: {results_path}")
print("=" * 70)
