"""V5 security/dangerous_python.py — python_exec denylist + import allowlist.

Source: compact_v4/MAIN/agent/sagemaker_agent.py:1580-1982
(extracted as constants from SecurityManager).

All patterns are VERBATIM from v4. Modifying these is a security-
critical change.
"""
from __future__ import annotations

from typing import List, Set, Dict, Tuple


# ============================================================
# DANGEROUS_PYTHON — Layer 1 regex denylist (catches obfuscated patterns)
# ============================================================

DANGEROUS_PYTHON: List[Tuple[str, str]] = [
    # === CODE INJECTION ===
    (r"\bos\.system\s*\(", "os.system() - use subprocess instead"),
    (r"\bos\.popen\s*\(", "os.popen() - dangerous"),
    (r"\bsubprocess\..*shell\s*=\s*True", "subprocess with shell=True (also caught by broader subprocess block)"),
    (r"\beval\s*\(", "eval() - code injection risk"),
    (r"\bexec\s*\(", "exec() - code injection risk"),
    (r"\bcompile\s*\(.*exec", "compile() for exec"),
    (r"\b__import__\s*\(", "Dynamic import"),
    (r"\bimportlib\.import_module\s*\(", "Dynamic import"),

    # === FILE SYSTEM ACCESS ===
    (r"\bopen\s*\(['\"]/(etc|usr|var|bin|sbin)", "Access system directories"),
    (r"\bopen\s*\(['\"]C:\\\\Windows", "Access Windows system"),
    (r"\bshutil\.rmtree\s*\(['\"]/(|home|usr|etc|var)", "Delete system directories"),
    (r"\bshutil\.rmtree\s*\(['\"]C:\\\\", "Delete Windows system"),
    (r"\bos\.remove\s*\(['\"]/(etc|usr|bin)", "Delete system files"),
    (r"\bos\.rmdir\s*\(['\"]/(etc|usr|bin)", "Delete system directories"),
    (r"\bopen\s*\(['\"]\.\.\/\.\.\/.*/", "Path traversal in open()"),

    # === AWS SDK (boto3) - TIERED ACCESS ===
    # ALWAYS BLOCKED: destructive/admin services
    (r"boto3\.client\s*\(\s*['\"]iam['\"]", "IAM access - BLOCKED (can escalate privileges)"),
    (r"boto3\.client\s*\(\s*['\"]sts['\"]", "STS access - BLOCKED (can assume roles)"),
    (r"boto3\.client\s*\(\s*['\"]secretsmanager['\"]", "Secrets Manager - BLOCKED"),
    (r"boto3\.client\s*\(\s*['\"]ssm['\"]", "Systems Manager - BLOCKED (can run commands on EC2)"),
    (r"boto3\.client\s*\(\s*['\"]kms['\"]", "KMS access - BLOCKED (encryption keys)"),
    (r"boto3\.client\s*\(\s*['\"]ec2['\"]", "EC2 access - BLOCKED (can terminate instances)"),
    (r"boto3\.client\s*\(\s*['\"]rds['\"]", "RDS access - BLOCKED (can delete databases)"),
    (r"boto3\.client\s*\(\s*['\"]organizations['\"]", "Organizations - BLOCKED"),
    (r"boto3\.client\s*\(\s*['\"]cloudformation['\"]", "CloudFormation - BLOCKED (can delete stacks)"),
    # ALWAYS BLOCKED: destructive operations on ANY service
    (r"\.delete_bucket\s*\(", "S3 delete_bucket - BLOCKED (destructive)"),
    (r"\.delete_object\s*\(", "S3 delete_object - BLOCKED (destructive). Use versioning instead."),
    (r"\.delete_objects\s*\(", "S3 bulk delete - BLOCKED (destructive)"),
    (r"\.delete_table\s*\(", "DynamoDB delete_table - BLOCKED (destructive)"),
    (r"\.delete_item\s*\(", "DynamoDB delete_item - BLOCKED (destructive)"),
    (r"\.delete_function\s*\(", "Lambda delete - BLOCKED (destructive)"),
    (r"\.terminate_instances\s*\(", "EC2 terminate - BLOCKED (destructive)"),
    (r"\.delete_stack\s*\(", "CloudFormation delete - BLOCKED (destructive)"),
    (r"\.remove_permission\s*\(", "Remove permission - BLOCKED (destructive)"),
    (r"\.delete_policy\s*\(", "Delete policy - BLOCKED (destructive)"),
    (r"\.put_bucket_policy\s*\(", "Modify bucket policy - BLOCKED (security-sensitive)"),
    # INDIRECTION BYPASSES
    (r"\.session\.Session\(\)\.client\s*\(\s*['\"](?:iam|sts|kms|ssm|secretsmanager|ec2|rds|organizations|cloudformation)['\"]", "Admin service via Session() - BLOCKED"),
    (r"boto3\.resource\s*\(\s*['\"]", "boto3.resource() - BLOCKED (use client API with explicit calls)"),
    (r"getattr\s*\([^,]+,\s*['\"]delete", "getattr+delete evasion - BLOCKED"),
    (r"getattr\s*\([^,]+,\s*['\"]terminate", "getattr+terminate evasion - BLOCKED"),
    (r"getattr\s*\([^,]+,\s*['\"]remove_permission", "getattr+remove_permission evasion - BLOCKED"),
    (r"\.objects\..*\.delete\s*\(", "Bulk object delete via resource API - BLOCKED"),

    # === ENVIRONMENT/CREDENTIALS ===
    (r"\bos\.environ\s*\[\s*['\"]AWS_", "Access AWS credentials from env"),
    (r"\bos\.getenv\s*\(\s*['\"]AWS_", "Get AWS credentials from env"),
    (r"\bos\.environ\.get\s*\(\s*['\"]AWS_", "Get AWS credentials from env"),

    # === SUBPROCESS (blocks all subprocess execution, not just shell=True) ===
    (r"\bsubprocess\.(run|Popen|call|check_output|check_call)\s*\(", "subprocess execution - blocked"),

    # === NETWORK ===
    (r"\bctypes\.", "ctypes - low-level access"),
    (r"\bsocket\..*bind\s*\(", "Network server binding"),
    (r"\bsocket\..*listen\s*\(", "Network listening"),
    (r"\bsocket\..*connect\s*\(", "Network connection - blocked for security"),
    (r"\brequests\.(get|post|put|delete|patch|head)\s*\(", "HTTP request - blocked for security"),
    (r"\burllib\.request\.(urlopen|urlretrieve)\s*\(", "HTTP request - blocked for security"),
    (r"\bhttp\.client\.HTTP", "HTTP client - blocked for security"),
    (r"\bhttpx\.", "httpx HTTP client - blocked for security"),
    (r"\baiohttp\.", "aiohttp HTTP client - blocked for security"),
    (r"\burllib3\.", "urllib3 HTTP client - blocked for security"),
    (r"169\.254\.169\.254", "EC2 metadata endpoint - blocked for security"),
    (r"\brequests\.(get|post).*verify\s*=\s*False", "Disable SSL verification"),
    (r"\burllib.*verify\s*=\s*False", "Disable SSL verification"),

    # === DATABASE DESTRUCTIVE VIA PYTHON (V4.10.7) ===
    (r"\.(execute|executemany|execute_query|exec_driver_sql|raw|run|scalar)\s*\(\s*[fr]?['\"]\s*(?i:DROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|USER)|TRUNCATE\s+TABLE|DELETE\s+FROM)", "Raw SQL destructive via Python (DROP/TRUNCATE/DELETE)"),
    (r"\.\s*metadata\s*\.\s*drop_all\s*\(", "SQLAlchemy metadata.drop_all (drops all tables)"),
    (r"\bMetaData\s*\([^)]*\)\s*\.\s*drop_all\s*\(", "SQLAlchemy MetaData(...).drop_all"),
    (r"\bdrop_all\s*\(\s*(engine|bind\s*=)", "drop_all on engine/bind"),
    (r"\bsession\.delete\s*\(", "ORM session.delete"),
    (r"\bsession\.execute\s*\(\s*[fr]?['\"]\s*(?i:DROP|TRUNCATE|DELETE\s+FROM)", "ORM session.execute destructive SQL"),
    (r"\.dropDatabase\s*\(\s*\)", "MongoDB dropDatabase()"),
    (r"\.deleteMany\s*\(\s*\{\s*\}\s*\)", "MongoDB deleteMany({}) — wipes collection"),
    (r"\.flushdb\s*\(\)|\.flushall\s*\(\)", "Redis FLUSHDB / FLUSHALL"),

    # === FILESYSTEM DESTRUCTIVE VIA PYTHON (V4.10.7) ===
    (r"\bos\.unlink\s*\(\s*['\"]/?(etc|usr|sbin|bin|lib|boot|root)/", "os.unlink on system path"),
    (r"\bpathlib\.Path\s*\(\s*['\"]/?(etc|usr|sbin|bin|lib|boot|root)/.*\)\.\s*(unlink|rmdir)", "pathlib destructive on system path"),

    # === RECURSIVE FOLDER REMOVAL FROM PYTHON (V4.10.8) — HARD BLOCK ===
    (r"\bshutil\.rmtree\s*\(", "shutil.rmtree blocked from python_exec. Use os.unlink for single files; the 🧹 Clean button handles bulk dir cleanup with hardcoded paths."),
    (r"\bos\.rmdir\s*\(", "os.rmdir blocked. Folder removal must be manual or via 🧹 Clean button."),
    (r"\bos\.removedirs\s*\(", "os.removedirs blocked. Folder removal must be manual."),
    (r"\bPath\s*\([^)]*\)\s*\.\s*rmdir\s*\(", "Path.rmdir blocked. Folder removal must be manual."),

    # === DESERIALIZATION ===
    (r"\bpickle\.loads?\s*\(", "pickle - deserialization attack risk"),
    (r"\byaml\.load\s*\([^,)]+\)$", "yaml.load without Loader (unsafe)"),

    # === OTHER ===
    (r"\bgetattr\s*\(.*,\s*['\"]__", "Access dunder attributes"),
    (r"\bgetattr\s*\(\s*(os|shutil|subprocess|sys)\b", "Dynamic attribute access on sensitive module"),
    (r"\bsys\.modules\b", "sys.modules access - blocked for security"),
]


# ============================================================
# Import allowlist + denylist (Layer 2 AST validation)
# ============================================================

ALLOWED_PYTHON_MODULES: Set[str] = {
    # Standard library - safe data processing
    "math", "statistics", "decimal", "fractions", "random", "string",
    "re", "json", "csv", "collections", "itertools", "functools",
    "datetime", "time", "calendar", "textwrap", "pprint",
    "pathlib", "io", "struct", "base64", "hashlib", "hmac",
    "copy", "typing", "dataclasses", "enum", "abc",
    "operator", "bisect", "heapq", "array",
    "difflib", "unicodedata", "html", "xml",
    # File I/O (workspace-restricted by other controls)
    "os", "os.path", "glob", "fnmatch", "shutil",
    # Data science / analysis
    "numpy", "pandas", "scipy", "sklearn",
    "matplotlib", "matplotlib.pyplot", "seaborn",
    "plotly", "altair",
    # Document creation
    "openpyxl", "xlsxwriter", "docx",
    "PIL", "reportlab", "fpdf",
    # AWS SDK (destructive ops blocked by regex denylist)
    "boto3", "botocore",
    # Misc safe
    "tabulate", "yaml", "toml", "configparser",
    "logging", "warnings", "traceback", "inspect",
    "argparse",
}

BLOCKED_PYTHON_MODULES: Set[str] = {
    "subprocess", "os.system", "shlex",
    "socket", "http", "urllib", "urllib3", "requests", "httpx", "aiohttp",
    "asyncio",  # can be used to run network code
    "ctypes", "cffi",  # FFI
    "pickle", "shelve", "marshal",  # deserialization
    "importlib", "runpy",  # dynamic imports
    "code", "codeop", "compileall",  # code execution
    "multiprocessing", "concurrent",  # process spawning
    "signal",  # signal manipulation
    "google.cloud", "azure",  # cloud SDKs
}

BLOCKED_PYTHON_MEMBERS: Dict[str, Set[str]] = {
    "os": {
        "system", "popen",
        "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
        "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
        "startfile",
    },
    "shutil": {"rmtree"},
    "pathlib": {"Path.unlink", "Path.rmdir"},
}


ALLOWED_AWS_HINT = """
AWS access tiers (SageMaker execution role):
- READ: s3 get/list/head, bedrock invoke, textract, comprehend → ALLOWED (runs directly, approval dialog)
- WRITE: s3 put_object, dynamodb put_item, lambda invoke → ALLOWED (runs directly, approval dialog)
- DESTRUCTIVE: delete_object, delete_table, terminate_instances → BLOCKED (regex denylist, no override)
- ADMIN: iam, sts, kms, ssm, secretsmanager → BLOCKED (regex denylist, no override)
"""
