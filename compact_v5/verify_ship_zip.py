"""Phase 13 ship-gate verifier for compact_v5.zip (ADAPT from v4 verify_ship_zip.py).

Run this BEFORE every release. Fails loudly if the zip carries dev
artefacts, test files, missing required runtime files, or stale markers.

Usage:
    python verify_ship_zip.py              # default: ../compact_v5.zip
    python verify_ship_zip.py path/to.zip  # specify zip

Exit code:
    0 = clean, ship-ready
    1 = at least one assertion failed

PORT_LOG: #037.
"""

from __future__ import annotations

import os
import re
import sys
import zipfile


# Required runtime files at the zip root (flat layout — `MAIN/agent/` prefix stripped).
REQUIRED_AT_ROOT = {
    "chat.ipynb",
    "chat.md",
    "entry.py",
    "__init__.py",
}

# Required package directories (each must contain a __init__.py at minimum).
REQUIRED_PACKAGES = {
    "core", "tools", "skills", "runtime", "prompt", "ui", "subagent",
    "security",
}

# Required runtime tools (subset — full list in tools/__init__.py).
REQUIRED_TOOLS = {
    "read_file.py", "write_file.py", "edit_file.py",
    "bash.py", "python_exec.py",
    "grep.py", "glob.py", "list_dir.py",
    "view_image.py", "notebook_edit.py",
    "tool_search.py", "task.py", "skill.py", "skill_propose_patch.py",
}

# Required skill directories (10 v4 production skills, ported byte-for-byte).
REQUIRED_SKILLS = {
    "batch", "clara", "design", "html", "reflexion",
    "report", "review", "security-review", "simplify", "verify",
}

FORBIDDEN_PATTERNS = [
    re.compile(r"(^|/)tests(/|$)"),    # entire tests dir — dev only
    re.compile(r"(^|/)test_.*\.py$"),  # any individual test file
    re.compile(r"(^|/)__pycache__"),
    re.compile(r"(^|/)\.pytest_cache"),
    re.compile(r"(^|/)\.snapshots"),
    re.compile(r"(^|/)\.ipynb_checkpoints"),
    re.compile(r"(^|/)audit_logs"),
    re.compile(r"(^|/)sessions(/|$)"),
    re.compile(r"(^|/)truncated_outputs"),
    re.compile(r"(^|/)\.proposed/"),
    re.compile(r"(^|/)MAIN/agent/"),   # unflattened wrapper folder
    re.compile(r"(^|/)changelogs(/|$)"),
    re.compile(r"(^|/)_status(/|$)"),
    re.compile(r"\.pyc$"),
    re.compile(r"\.swp$"),
    re.compile(r"\.DS_Store$"),
]


def _check(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" -- {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    return condition


def main(zip_path: str = "../compact_v5.zip") -> int:
    if not os.path.exists(zip_path):
        print(f"ERROR: zip not found: {zip_path}")
        return 1

    print(f"Verifying ship zip: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path):,} bytes\n")

    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()

    print(f"Total entries: {len(names)}\n")
    failures = 0

    print("== Required runtime files at root ==")
    for required in sorted(REQUIRED_AT_ROOT):
        if not _check(f"root/{required}", required in names):
            failures += 1

    print("\n== Required package directories ==")
    for pkg in sorted(REQUIRED_PACKAGES):
        ok = any(n.startswith(pkg + "/__init__.py") or n == pkg + "/__init__.py" for n in names)
        if not _check(f"{pkg}/__init__.py", ok):
            failures += 1

    print("\n== Required tool modules ==")
    for tool in sorted(REQUIRED_TOOLS):
        ok = f"tools/{tool}" in names
        if not _check(f"tools/{tool}", ok):
            failures += 1

    print("\n== Required skill directories ==")
    for skill in sorted(REQUIRED_SKILLS):
        ok = any(n.startswith(f"skills/{skill}/SKILL.md") for n in names)
        if not _check(f"skills/{skill}/SKILL.md", ok):
            failures += 1

    print("\n== Forbidden patterns (dev artefacts) ==")
    for pat in FORBIDDEN_PATTERNS:
        offenders = [n for n in names if pat.search(n)]
        if offenders:
            failures += 1
            sample = offenders[:3]
            print(f"  [FAIL] pattern {pat.pattern!r} matches {len(offenders)} entries; sample: {sample}")
        else:
            print(f"  [PASS] pattern {pat.pattern!r} clean")

    print("\n== Result ==")
    if failures:
        print(f"  RESULT: FAIL -- {failures} assertion(s) failed")
        return 1
    print(f"  RESULT: PASS -- zip is ship-ready")
    return 0


if __name__ == "__main__":
    z = sys.argv[1] if len(sys.argv) > 1 else "../compact_v5.zip"
    sys.exit(main(z))
