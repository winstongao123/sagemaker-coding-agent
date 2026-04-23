"""Rebuild compact_v4.zip — MINIMUM-SHIP profile.

v4.9.2: tightened to ship only what's needed to RUN the agent in a SageMaker
notebook environment. Drops dev artefacts, test files, audit docs, historical
HTMLs, and powerbi skills (per user request, kept out since v4.9.0).

Kept (runtime essentials):
- sagemaker_agent.py (the agent)
- chat.ipynb / chat.md (entry notebook + user-facing chat docs)
- USER_GUIDE.md (user docs)
- memory.md (auto-loaded persistent memory file, even if empty)
- skills/<all skill SKILL.md and dependent files>
- changelogs/CHANGELOG_v4.X.X.md (release notes)
- top-level CHANGELOG.md (release index)

Dropped (dev only):
- test_*.py (all test suites — dev verification, not runtime)
- TEST_LOG.md (dev artefact)
- v3_architecture.html (historical, superseded by changelogs)
- skills/clara/V4_NOTES.md (per-version dev notes)
- docs/ (audit docs, internal)
- .gitignore, .git/, __pycache__/, .pytest_cache/, .snapshots/, .code_index/
- _rebuild_zip.py (this file — meta tool)
- powerbi-dashboard, powerbi-dashboard-v2 (per user)
"""

from __future__ import annotations
import os
import zipfile
import fnmatch

SRC_DIR = "MAIN"
OUT_ZIP = "compact_v4.zip"

# Extra paths to include at the zip root (outside MAIN/).
EXTRA_FILES = ["CHANGELOG.md"]
EXTRA_DIRS = []  # docs/ deliberately excluded — audit docs are internal, not shipped to users

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".code_index",       # runtime code-index cache (can be 5MB+)
    ".git",              # internal git state (sub-repos inside skills/, etc.)
    ".pytest_cache",     # pytest scratch
    ".snapshots",        # per-edit snapshot history
    ".verify-cache",     # verify-agent scratch
    "audit_logs",
    "sessions",
    "truncated_outputs",
    "powerbi-dashboard",
    "powerbi-dashboard-v2",
}
EXCLUDE_REL_PATHS = {
    "MAIN/tests",                # whole tests/ dir — dev-only, not shipped
    "MAIN/tests/competition",    # legacy, kept for clarity
}
EXCLUDE_FILE_PATTERNS = [
    "*.pyc",
    ".DS_Store",
    "*.swp",
    ".exec_budget.json",         # per-session exec budget, not for shipping
    ".gitignore",                # dev/git artefact
    "test_*.py",                 # all test files — dev only
    "*_test.py",
    "TEST_LOG.md",               # dev artefact
    "v3_architecture.html",      # historical doc, superseded by changelogs
    "V4_NOTES.md",               # per-version dev notes (lives inside skills/clara/)
    "chat.md",                   # md companion to chat.ipynb — redundant with USER_GUIDE.md, kept in repo only
    # FULL_REVIEW.md (clara skill orchestration) is KEPT — part of the runtime skill workflow
]


def _rel(path: str) -> str:
    return os.path.relpath(path, ".").replace(os.sep, "/")


def _is_dir_excluded(rel_path: str) -> bool:
    parts = rel_path.split("/")
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
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
        # Walk MAIN
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
                rel_p = _rel(abs_p)
                z.write(abs_p, rel_p)
                files_added += 1
                total_raw += os.path.getsize(abs_p)

        # Extra files
        for rf in EXTRA_FILES:
            if os.path.isfile(rf):
                z.write(rf, rf)
                files_added += 1
                total_raw += os.path.getsize(rf)

        # Extra dirs (e.g. docs/)
        for ed in EXTRA_DIRS:
            if not os.path.isdir(ed):
                continue
            for root, dirs, files in os.walk(ed):
                rel_root = _rel(root)
                dirs[:] = [d for d in dirs if not _is_dir_excluded(f"{rel_root}/{d}")]
                if _is_dir_excluded(rel_root):
                    continue
                for f in files:
                    if _is_file_excluded(f):
                        continue
                    abs_p = os.path.join(root, f)
                    rel_p = _rel(abs_p)
                    z.write(abs_p, rel_p)
                    files_added += 1
                    total_raw += os.path.getsize(abs_p)

    zip_size = os.path.getsize(OUT_ZIP)
    print(
        f"Files: {files_added}  Raw: {total_raw/1024:.1f} KB  "
        f"Zip: {zip_size/1024:.1f} KB  ({zip_size/total_raw*100:.0f}%)"
    )


if __name__ == "__main__":
    main()
