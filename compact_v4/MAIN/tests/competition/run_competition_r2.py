#!/usr/bin/env python3
"""
Competition Round 2 — Hard Tasks: Codebase Review, Explanation, Flowcharts, Complex Code Writing
Runs V3 (real Bedrock) on 5 hard tasks focused on the user's key needs.

Usage: cd compact_v3/MAIN/agent && python3 ../tests/competition/run_competition_r2.py
"""
import sys, os, json, time, shutil

AGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agent")
sys.path.insert(0, AGENT_DIR)

LIVE_MODEL = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "ap-southeast-2"
COMP_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS = []

def run_agent(task, system=None, max_turns=20):
    from sagemaker_agent import Agent, BedrockClient, TOKENS
    client = BedrockClient(model_id=LIVE_MODEL, region=REGION)
    c0, t0 = TOKENS.session_cost, TOKENS.api_calls
    outputs = []
    agent = Agent(client, f"r2_{int(time.time())}",
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

def score_task(task_id, name, prompt, check_fn, max_turns=20):
    print(f"\n{'='*60}")
    print(f"R2 TASK {task_id}: {name}")
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
    print(f"  Detail: {detail[:300]}")
    RESULTS.append({
        "task_id": f"R2-{task_id}", "name": name, "status": status, "passed": passed,
        "detail": detail[:500], "cost": cost, "calls": calls, "elapsed": elapsed,
        "result_preview": result[:500] if result else "",
    })
    return passed


# ============================================================
# SETUP: Create a realistic multi-file codebase for review
# ============================================================
from sagemaker_agent import CONFIG
WS = CONFIG.workspace

def setup():
    proj = os.path.join(WS, "r2_codebase")
    os.makedirs(os.path.join(proj, "core"), exist_ok=True)
    os.makedirs(os.path.join(proj, "api"), exist_ok=True)
    os.makedirs(os.path.join(proj, "utils"), exist_ok=True)

    # core/database.py — connection pool + query builder
    with open(os.path.join(proj, "core/database.py"), "w") as f:
        f.write('''"""Database layer with connection pooling and query builder."""
import sqlite3
import threading
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

class ConnectionPool:
    """Thread-safe SQLite connection pool."""

    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: List[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self._active = 0

    def get_connection(self) -> sqlite3.Connection:
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._active += 1
                return conn
            if self._active < self.max_connections:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self._active += 1
                return conn
        # Wait and retry — potential deadlock if all connections held
        import time
        time.sleep(0.1)
        return self.get_connection()  # BUG: recursive call can stackoverflow

    def release_connection(self, conn: sqlite3.Connection):
        with self._lock:
            self._pool.append(conn)
            self._active -= 1

    @contextmanager
    def connection(self):
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.release_connection(conn)


class QueryBuilder:
    """Fluent SQL query builder."""

    def __init__(self, table: str):
        self.table = table
        self._select = "*"
        self._where: List[str] = []
        self._params: List[Any] = []
        self._order: Optional[str] = None
        self._limit: Optional[int] = None
        self._joins: List[str] = []

    def select(self, *cols):
        self._select = ", ".join(cols)
        return self

    def where(self, condition: str, *params):
        self._where.append(condition)
        self._params.extend(params)
        return self

    def join(self, table: str, on: str, join_type: str = "INNER"):
        self._joins.append(f"{join_type} JOIN {table} ON {on}")
        return self

    def order_by(self, col: str, desc: bool = False):
        self._order = f"{col} {'DESC' if desc else 'ASC'}"
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def build(self) -> tuple:
        sql = f"SELECT {self._select} FROM {self.table}"
        if self._joins:
            sql += " " + " ".join(self._joins)
        if self._where:
            sql += " WHERE " + " AND ".join(self._where)
        if self._order:
            sql += f" ORDER BY {self._order}"
        if self._limit:
            sql += f" LIMIT {self._limit}"
        return sql, tuple(self._params)

    def execute(self, pool: ConnectionPool) -> List[Dict]:
        sql, params = self.build()
        with pool.connection() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
''')

    # core/auth.py — JWT-like auth with middleware
    with open(os.path.join(proj, "core/auth.py"), "w") as f:
        f.write('''"""Authentication with token-based sessions and role middleware."""
import hashlib
import hmac
import json
import time
import base64
from typing import Optional, Dict, Callable
from functools import wraps

SECRET_KEY = "change-me-in-production"  # Should come from env

class TokenManager:
    """Simple JWT-like token manager."""

    def __init__(self, secret: str = SECRET_KEY, expiry_seconds: int = 3600):
        self.secret = secret
        self.expiry = expiry_seconds

    def create_token(self, user_id: int, role: str) -> str:
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": int(time.time()) + self.expiry,
            "iat": int(time.time()),
        }
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        signature = hmac.new(self.secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        return f"{payload_b64}.{signature}"

    def verify_token(self, token: str) -> Optional[Dict]:
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return None
            payload_b64, signature = parts
            expected_sig = hmac.new(self.secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return None
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            if payload.get("exp", 0) < time.time():
                return None
            return payload
        except Exception:
            return None


def require_role(*roles):
    """Decorator: require specific role(s) for endpoint access."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            tm = TokenManager()
            payload = tm.verify_token(token)
            if not payload:
                return {"error": "Unauthorized", "status": 401}
            if payload["role"] not in roles:
                return {"error": "Forbidden", "status": 403}
            request.user = payload
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
''')

    # api/routes.py — REST endpoints
    with open(os.path.join(proj, "api/routes.py"), "w") as f:
        f.write('''"""REST API routes for user and order management."""
from core.database import ConnectionPool, QueryBuilder
from core.auth import TokenManager, require_role
from utils.validators import validate_email, validate_order, sanitize_input

# Global pool — initialized at app startup
_pool: ConnectionPool = None

def init(db_path: str):
    global _pool
    _pool = ConnectionPool(db_path)

def login(request):
    """POST /login — authenticate and return token."""
    username = request.body.get("username", "")
    password = request.body.get("password", "")
    user = QueryBuilder("users").where("username = ?", username).execute(_pool)
    if not user:
        return {"error": "Invalid credentials", "status": 401}
    import hashlib
    stored_hash = user[0]["password_hash"]
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    if stored_hash != input_hash:
        return {"error": "Invalid credentials", "status": 401}
    tm = TokenManager()
    token = tm.create_token(user[0]["id"], user[0]["role"])
    return {"token": token, "user": {"id": user[0]["id"], "name": user[0]["name"]}}

@require_role("admin", "manager")
def list_users(request):
    """GET /users — list all users (admin/manager only)."""
    page = int(request.params.get("page", 1))
    limit = int(request.params.get("limit", 20))
    offset = (page - 1) * limit
    users = QueryBuilder("users").select("id", "name", "email", "role", "created_at") \\
        .order_by("created_at", desc=True).limit(limit).execute(_pool)
    return {"users": users, "page": page}

@require_role("admin")
def delete_user(request, user_id: int):
    """DELETE /users/:id — delete user (admin only)."""
    with _pool.connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return {"status": "deleted"}

def get_orders(request, user_id: int):
    """GET /users/:id/orders — get user orders."""
    orders = QueryBuilder("orders") \\
        .join("order_items", "orders.id = order_items.order_id") \\
        .join("products", "order_items.product_id = products.id") \\
        .where("orders.user_id = ?", user_id) \\
        .select("orders.id", "orders.created_at", "orders.status",
                "products.name as product_name", "order_items.quantity", "order_items.price") \\
        .order_by("orders.created_at", desc=True) \\
        .execute(_pool)
    return {"orders": orders}

@require_role("admin", "manager")
def dashboard_stats(request):
    """GET /dashboard — aggregate stats."""
    with _pool.connection() as conn:
        total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        total_orders = conn.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
        revenue = conn.execute("SELECT SUM(oi.quantity * oi.price) as r FROM order_items oi").fetchone()["r"]
        recent = conn.execute(
            "SELECT u.name, o.created_at, o.status FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC LIMIT 5"
        ).fetchall()
    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": round(revenue or 0, 2),
        "recent_orders": [dict(r) for r in recent],
    }
''')

    # utils/validators.py
    with open(os.path.join(proj, "utils/validators.py"), "w") as f:
        f.write('''"""Input validation utilities."""
import re
from typing import Dict, Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    if not email or not isinstance(email, str):
        return False, "Email is required"
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, f"Invalid email format: {email}"
    return True, "OK"

def validate_order(data: Dict) -> Tuple[bool, str]:
    required = ["product_id", "quantity"]
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"
    if not isinstance(data["quantity"], int) or data["quantity"] < 1:
        return False, "Quantity must be a positive integer"
    if data.get("quantity", 0) > 1000:
        return False, "Quantity exceeds maximum (1000)"
    return True, "OK"

def sanitize_input(text: str) -> str:
    """Remove potentially dangerous characters."""
    return re.sub(r"[<>&\"\\']", "", text) if text else ""
''')

    # utils/__init__.py
    with open(os.path.join(proj, "utils/__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(proj, "core/__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(proj, "api/__init__.py"), "w") as f:
        f.write("")

    print(f"Setup: created {proj}/ with 4 source files (~350 lines)")

setup()


# ============================================================
# R2 TASK 1: CODEBASE REVIEW — Read all files, find bugs, rate quality
# ============================================================
def check_r2_1(result, outputs):
    r = result.lower()
    # Must find: recursive stackoverflow in ConnectionPool, SECRET_KEY hardcoded, no rate limiting
    found_recursion = "recursion" in r or "recursive" in r or "stackoverflow" in r or "stack overflow" in r
    found_secret = "secret" in r and ("hardcod" in r or "env" in r or "config" in r)
    found_architecture = any(w in r for w in ["layer", "separati", "concern", "pattern", "architect", "structure"])
    has_rating = any(w in r for w in ["rating", "score", "/10", "grade", "quality", "good", "strong", "weak"])
    detail_parts = [
        f"recursion_bug={'✓' if found_recursion else '✗'}",
        f"hardcoded_secret={'✓' if found_secret else '✗'}",
        f"architecture={'✓' if found_architecture else '✗'}",
        f"quality_rating={'✓' if has_rating else '✗'}",
    ]
    score = sum([found_recursion, found_secret, found_architecture, has_rating])
    return score >= 3, ", ".join(detail_parts)

score_task(1, "Codebase review: 4 files, find bugs, rate architecture",
    "Read ALL files in r2_codebase/ (core/database.py, core/auth.py, api/routes.py, utils/validators.py). "
    "Perform a thorough code review. For each file: identify bugs, security issues, and quality concerns. "
    "Then give an overall architecture assessment: what's good, what's bad, and a quality rating. "
    "Report only — do not edit files.",
    check_r2_1)


# ============================================================
# R2 TASK 2: CODE EXPLANATION — Explain QueryBuilder + auth flow
# ============================================================
def check_r2_2(result, outputs):
    r = result.lower()
    # Must explain: fluent API pattern, method chaining, SQL generation, token flow
    explains_fluent = "fluent" in r or "chain" in r or "builder" in r
    explains_sql = "sql" in r and ("build" in r or "generat" in r or "construct" in r)
    explains_token = "token" in r and ("creat" in r or "verify" in r or "sign" in r)
    explains_flow = "flow" in r or "step" in r or "process" in r or "1." in r
    beginner_friendly = any(w in r for w in ["means", "think of", "like", "example", "simple", "basically"])
    detail_parts = [
        f"fluent_pattern={'✓' if explains_fluent else '✗'}",
        f"sql_generation={'✓' if explains_sql else '✗'}",
        f"token_flow={'✓' if explains_token else '✗'}",
        f"step_by_step={'✓' if explains_flow else '✗'}",
        f"beginner_friendly={'✓' if beginner_friendly else '✗'}",
    ]
    score = sum([explains_fluent, explains_sql, explains_token, explains_flow, beginner_friendly])
    return score >= 4, ", ".join(detail_parts)

score_task(2, "Code explanation: explain QueryBuilder + auth flow for beginners",
    "Read r2_codebase/core/database.py and r2_codebase/core/auth.py. "
    "Explain to a BEGINNER developer: "
    "1) How does QueryBuilder work? What pattern does it use? Walk through how a query gets built step by step. "
    "2) How does the auth token flow work? How is a token created, sent, and verified? "
    "Use simple language. Give concrete examples.",
    check_r2_2)


# ============================================================
# R2 TASK 3: FLOWCHART — Generate ASCII/Mermaid diagram of request flow
# ============================================================
def check_r2_3(result, outputs):
    r = result.lower()
    # Check for diagram content
    has_diagram = any(s in result for s in ["→", "-->", "->", "├", "│", "flowchart", "graph", "sequenceDiagram"])
    has_login = "login" in r
    has_auth = "auth" in r or "token" in r or "verify" in r
    has_db = "database" in r or "query" in r or "pool" in r or "connection" in r
    has_multiple_steps = r.count("→") >= 2 or r.count("-->") >= 2 or r.count("->") >= 2 or result.count("\n") >= 10
    # Check for file output (markdown or text)
    flow_file = any(os.path.exists(os.path.join(WS, f)) for f in ["r2_flowchart.md", "r2_flowchart.txt", "flowchart.md"])
    detail_parts = [
        f"diagram={'✓' if has_diagram else '✗'}",
        f"login_flow={'✓' if has_login else '✗'}",
        f"auth_check={'✓' if has_auth else '✗'}",
        f"db_layer={'✓' if has_db else '✗'}",
        f"multi_step={'✓' if has_multiple_steps else '✗'}",
        f"file_created={'✓' if flow_file else '✗'}",
    ]
    score = sum([has_diagram, has_login, has_auth, has_db, has_multiple_steps])
    return score >= 4, ", ".join(detail_parts)

score_task(3, "Flowchart: generate request flow diagram from codebase",
    "Read ALL files in r2_codebase/. Create a flowchart (as r2_flowchart.md) showing the complete request flow: "
    "1) User sends login request → auth → token returned "
    "2) User sends authenticated request → token verified → role checked → query built → database → response "
    "Use Mermaid syntax (```mermaid flowchart TD ...) or ASCII art. Show all layers: API → Auth → Database.",
    check_r2_3)


# ============================================================
# R2 TASK 4: COMPLEX CODE WRITING — Implement a caching layer
# ============================================================
def check_r2_4(result, outputs):
    cache_path = os.path.join(WS, "r2_codebase/core/cache.py")
    if not os.path.exists(cache_path):
        # Check other locations
        for name in os.listdir(os.path.join(WS, "r2_codebase/core")):
            if "cache" in name and name.endswith(".py"):
                cache_path = os.path.join(WS, "r2_codebase/core", name)
                break
    if not os.path.exists(cache_path):
        return False, "cache.py not created"
    code = open(cache_path).read()
    has_class = "class " in code and "Cache" in code
    has_get = "def get" in code
    has_set = "def set" in code or "def put" in code or "def store" in code
    has_ttl = "ttl" in code.lower() or "expir" in code.lower() or "time" in code
    has_eviction = "evict" in code.lower() or "lru" in code.lower() or "max" in code.lower() or "capacity" in code.lower()
    has_thread_safe = "lock" in code.lower() or "threading" in code
    has_decorator = "decorator" in code.lower() or "def cache" in code.lower() or "@" in code
    lines = len(code.split("\n"))
    detail_parts = [
        f"class={'✓' if has_class else '✗'}",
        f"get={'✓' if has_get else '✗'}",
        f"set={'✓' if has_set else '✗'}",
        f"ttl={'✓' if has_ttl else '✗'}",
        f"eviction={'✓' if has_eviction else '✗'}",
        f"thread_safe={'✓' if has_thread_safe else '✗'}",
        f"decorator={'✓' if has_decorator else '✗'}",
        f"lines={lines}",
    ]
    score = sum([has_class, has_get, has_set, has_ttl, has_eviction, has_thread_safe])
    return score >= 5, ", ".join(detail_parts)

score_task(4, "Complex code writing: implement thread-safe LRU cache with TTL",
    "The r2_codebase/ project needs a caching layer. Write r2_codebase/core/cache.py that implements: "
    "1) LRUCache class with get/set/delete, max capacity, and LRU eviction "
    "2) TTL (time-to-live) — entries expire after configurable seconds "
    "3) Thread-safe (multiple threads can read/write simultaneously) "
    "4) A @cached decorator that caches function results "
    "5) Cache stats (hits, misses, evictions) "
    "This must be production quality — proper error handling, docstrings, type hints.",
    check_r2_4)


# ============================================================
# R2 TASK 5: LARGE ANALYSIS + RECOMMENDATIONS — architecture review + improvement plan
# ============================================================
def check_r2_5(result, outputs):
    r = result.lower()
    # Must cover: separation of concerns, missing pieces, improvement plan
    has_current = "current" in r and ("architect" in r or "structure" in r or "design" in r)
    has_strength = "strength" in r or "good" in r or "well" in r or "clean" in r
    has_weakness = "weakness" in r or "missing" in r or "lack" in r or "improv" in r or "concern" in r
    has_recommendations = "recommend" in r or "suggest" in r or "should" in r or "add" in r
    has_specific = any(w in r for w in ["logging", "migration", "test", "config", "middleware", "error handling", "rate limit", "monitoring"])
    has_priority = any(w in r for w in ["priority", "first", "critical", "important", "high", "phase", "step 1", "1."])
    detail_parts = [
        f"current_arch={'✓' if has_current else '✗'}",
        f"strengths={'✓' if has_strength else '✗'}",
        f"weaknesses={'✓' if has_weakness else '✗'}",
        f"recommendations={'✓' if has_recommendations else '✗'}",
        f"specific_items={'✓' if has_specific else '✗'}",
        f"prioritized={'✓' if has_priority else '✗'}",
    ]
    score = sum([has_current, has_strength, has_weakness, has_recommendations, has_specific, has_priority])
    return score >= 5, ", ".join(detail_parts)

score_task(5, "Architecture review: assess codebase + prioritized improvement plan",
    "Read ALL files in r2_codebase/. Provide a senior engineer-level architecture review: "
    "1) Current architecture: describe the layers, patterns used, and how data flows "
    "2) Strengths: what's well-designed "
    "3) Weaknesses: what's missing or poorly designed "
    "4) Improvement plan: prioritized list of what to add/fix, in order of importance "
    "Be specific — name exact files, functions, and line numbers. Report only.",
    check_r2_5)


# ============================================================
# CLEANUP
# ============================================================
def cleanup():
    proj = os.path.join(WS, "r2_codebase")
    if os.path.isdir(proj):
        shutil.rmtree(proj, ignore_errors=True)
    for f in os.listdir(WS):
        if f.startswith("r2_"):
            path = os.path.join(WS, f)
            if os.path.isfile(path):
                os.unlink(path)

cleanup()


# ============================================================
# RESULTS
# ============================================================
print("\n" + "=" * 70)
print("ROUND 2 COMPETITION RESULTS (Hard: Review, Explain, Flowchart, Code)")
print("=" * 70)

total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["passed"])
total_cost = sum(r["cost"] for r in RESULTS)
total_time = sum(r["elapsed"] for r in RESULTS)
total_calls = sum(r["calls"] for r in RESULTS)

print(f"\n{'Task':<55s} {'Status':>6s} {'Time':>6s} {'Cost':>8s} {'Calls':>5s}")
print("-" * 80)
for r in RESULTS:
    icon = "✓" if r["passed"] else "✗"
    print(f"  [{icon}] {r['name'][:51]:<51s} {r['status']:>6s} {r['elapsed']:>5.1f}s ${r['cost']:>6.4f} {r['calls']:>5d}")
print("-" * 80)
print(f"  {'TOTAL':<53s} {passed}/{total} {total_time:>5.1f}s ${total_cost:>6.4f} {total_calls:>5d}")
print(f"\n  Pass rate: {passed/total*100:.0f}%")
print(f"  Avg cost per task: ${total_cost/total:.4f}")
print(f"  Avg time per task: {total_time/total:.1f}s")

# Save
results_path = os.path.join(COMP_DIR, "v3_results_r2.json")
with open(results_path, "w") as f:
    json.dump({
        "agent": "SageAgent V3.2.2",
        "model": LIVE_MODEL,
        "round": 2,
        "focus": "Codebase review, explanation, flowchart, complex code writing",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": {"total": total, "passed": passed, "cost": total_cost, "time": total_time, "calls": total_calls},
        "tasks": RESULTS,
    }, f, indent=2)
print(f"\n  Results saved: {results_path}")
print("=" * 70)
