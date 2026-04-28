"""Rebuild compact_v4.zip — MINIMUM-SHIP profile.

v4.9.2: tightened to ship only what's needed to RUN the agent in a SageMaker
notebook environment. Drops dev artefacts, test files, audit docs, historical
HTMLs, and powerbi skills (per user request, kept out since v4.9.0).

Kept (runtime essentials only):
- sagemaker_agent.py (the agent, at zip root)
- chat.ipynb (entry notebook, at zip root — md companion excluded)
- USER_GUIDE.md (full user docs, at zip root)
- memory.md (auto-loaded persistent memory file, even if empty, at zip root)
- AGENT_STATUS.md (auto-loaded long-running task handoff file, at zip root)
- skills/<all skill SKILL.md and dependent files>

Zip layout intentionally strips the source `MAIN/agent/` prefix so extraction does
not create deep wrapper folders. Skill subfolders are preserved because the agent
expects `skills/<name>/SKILL.md`.

Dropped:
- chat.md (md companion of chat.ipynb — redundant with USER_GUIDE.md)
- changelogs/CHANGELOG_v4.X.X.md (per-version release notes — repo-only)
- top-level CHANGELOG.md (release index — repo-only)
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

SRC_DIR = os.path.join("MAIN", "agent")
# v4.10.5: ship zip lives at REPO ROOT, not inside compact_v4/. The user
# moved it there as the canonical deliverable location. The "compact_v4/"
# prefix is for SOURCE; the zip is the ASSET.
OUT_ZIP = os.path.join("..", "compact_v4.zip")
ARCHIVE_PREFIX = SRC_DIR.replace(os.sep, "/") + "/"

# Extra paths to include at the zip root (outside MAIN/).
EXTRA_FILES = []   # release-context files (CHANGELOG.md, etc.) are NOT shipped — runtime-only zip
EXTRA_DIRS = []    # docs/ deliberately excluded — audit docs are internal, not shipped to users

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
# v4.10.x: glob patterns for test-tempdir directories that
# tempfile.mkdtemp(dir=CONFIG.workspace) leaves behind in MAIN/agent/. The
# tests deliberately use the workspace as the parent dir so SECURITY.validate_path
# accepts the file. Without this filter the ship zip can carry 50+ stale test fixtures.
EXCLUDE_DIR_PATTERNS = [
    "v410_nb_*",          # test_v410_notebook_edit.py tempdirs
    "v410_skills_*",      # test_v410_skill_listing_budget.py tempdirs
    "v410_subagent_env_*",  # test_v410_subagent_env.py tempdirs
    "v410_ctxwin_*",      # test_v410_context_window.py tempdirs
]
EXCLUDE_REL_PATHS = {
    "MAIN/tests",                # whole tests/ dir — dev-only, not shipped
    "MAIN/tests/competition",    # legacy, kept for clarity
    "MAIN/changelogs",           # per-version release notes — repo-only, not part of runtime ship
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
    # v4.10.x: glob-pattern match against any path part (catches test-tempdirs
    # like MAIN/agent/v410_nb_edit_xxxxx that tempfile.mkdtemp leaves behind).
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
                rel_p = _archive_name(abs_p)
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
