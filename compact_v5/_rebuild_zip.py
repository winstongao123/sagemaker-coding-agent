"""Rebuild compact_v5.zip — MINIMUM-SHIP profile (Phase 13, ADR-019).

ADAPT port of compact_v4/_rebuild_zip.py for v5's nested-package layout.
v5's source lives at `MAIN/agent/` with packages: agent/, core/, tools/,
skills/, runtime/, prompt/, ui/, subagent/, security/, mcp/. The zip
flattens the `MAIN/agent/` prefix but preserves the package directory
structure underneath so imports work in the unzipped tree.

PORT_LOG: #036.

Kept (runtime essentials):
- chat.ipynb (entry notebook, at zip root)
- chat.md (companion — kept; v4 dropped it but v5 keeps it because it documents
            PS Issues #2 + #4 widget surface and the OUT-OF-SCOPE list)
- memory.md, AGENT_STATUS.md (auto-loaded persistent files at zip root)
- agent/__init__.py + agent.py (Agent class)
- entry.py (cell-0 import target)
- core/ (budget, errors, retry, query_engine, cache)
- tools/ (registry + 12 tool modules)
- skills/ (manager + 10 SKILL.md directories)
- runtime/ (config, bedrock_client, audit, snapshot, file_cache, session, semantic_search)
- prompt/ (sections + 19 .md files + _CACHE_BOUNDARY.md + __init__.py)
- ui/ (chat_ui, widgets, diff_widget)
- subagent/ (env, handoff, spawn)
- security/ (manager, dangerous_patterns, dangerous_python, high_risk)
- mcp/ (stdio_client, http_client, manager)

Dropped (dev-only artefacts):
- tests/ (entire suite — dev verification, not runtime)
- changelogs/ (per-phase release notes — repo-only)
- _status/ (V5_BUILD_STATUS, V5_DESIGN_DECISIONS, V5_RUNNABLE_PORT_LOG, codex_reviews)
- docs/ (audit docs internal)
- _archive/ (historical references)
- __pycache__/, .pytest_cache/, .snapshots/, .ipynb_checkpoints/
- _rebuild_zip.py + verify_ship_zip.py (meta tools — repo-only)
- powerbi-dashboard variants (not in v5 base)
- bulky optional skill reference/example assets under skills/html/references/
- Clara long-form review prompt pack/reference notes; keep skills/clara/SKILL.md
"""

from __future__ import annotations

import fnmatch
import os
import zipfile

SRC_DIR = os.path.join("MAIN", "agent")
OUT_ZIP = os.path.join("..", "compact_v5.zip")
ARCHIVE_PREFIX = SRC_DIR.replace(os.sep, "/") + "/"

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".snapshots",
    ".ipynb_checkpoints",
    "audit_logs",
    "sessions",
    "truncated_outputs",
    "powerbi-dashboard",
    "powerbi-dashboard-v2",
    ".verify-cache",
    ".code_index",
}
EXCLUDE_DIR_PATTERNS = []
EXCLUDE_REL_PATHS = {
    "MAIN/agent/tests",   # entire tests dir — dev only
    "tests",              # also catches it after the SRC_DIR strip
    "MAIN/agent/skills/html/references",
    "skills/html/references",
    "MAIN/agent/skills/clara/prompts",
    "skills/clara/prompts",
    "MAIN/agent/skills/clara/FULL_REVIEW.md",
    "skills/clara/FULL_REVIEW.md",
    "MAIN/agent/skills/clara/V4_NOTES.md",
    "skills/clara/V4_NOTES.md",
}
EXCLUDE_FILE_PATTERNS = [
    "*.pyc",
    ".DS_Store",
    "*.swp",
    ".gitignore",
    ".exec_budget.json",
    "test_*.py",
    "*_test.py",
    "TEST_LOG.md",
]


def _rel(path: str) -> str:
    return os.path.relpath(path, ".").replace(os.sep, "/")


def _archive_name(path: str) -> str:
    """Map source paths into the flat runtime zip layout."""
    rel_path = _rel(path)
    if rel_path.startswith(ARCHIVE_PREFIX):
        return rel_path[len(ARCHIVE_PREFIX):]
    return rel_path


def _is_dir_excluded(rel_path: str) -> bool:
    parts = rel_path.split("/")
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
        return True
    for pat in EXCLUDE_DIR_PATTERNS:
        if any(fnmatch.fnmatch(p, pat) for p in parts):
            return True
    for ex in EXCLUDE_REL_PATHS:
        if rel_path == ex or rel_path.startswith(ex + "/"):
            return True
    return False


def _is_file_excluded(name: str) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in EXCLUDE_FILE_PATTERNS)


def main():
    files_added = 0
    total_raw = 0

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, dirs, files in os.walk(SRC_DIR):
            rel_root = _rel(root)
            dirs[:] = [
                d
                for d in dirs
                if not _is_dir_excluded(f"{rel_root}/{d}" if rel_root != "." else d)
            ]
            if _is_dir_excluded(rel_root):
                continue
            for f in files:
                if _is_file_excluded(f):
                    continue
                abs_p = os.path.join(root, f)
                rel_p = _archive_name(abs_p)
                if rel_p in EXCLUDE_REL_PATHS:
                    continue
                z.write(abs_p, rel_p)
                files_added += 1
                total_raw += os.path.getsize(abs_p)

    zip_size = os.path.getsize(OUT_ZIP)
    print(
        f"Files: {files_added}  Raw: {total_raw / 1024:.1f} KB  "
        f"Zip: {zip_size / 1024:.1f} KB  "
        f"({zip_size / max(1, total_raw) * 100:.0f}%)"
    )


if __name__ == "__main__":
    main()
