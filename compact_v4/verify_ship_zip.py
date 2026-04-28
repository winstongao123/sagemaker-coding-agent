"""V4.10.3 #18: Ship-gate verifier for compact_v4.zip.

Run this BEFORE every release. Fails loudly if the zip carries dev artefacts,
test tempdirs, missing required runtime files, or stale version markers.

Usage:
    python verify_ship_zip.py              # default: compact_v4.zip
    python verify_ship_zip.py path/to.zip  # specify zip

Exit code:
    0 = clean, ship-ready
    1 = at least one assertion failed (unit-test style report)
"""

from __future__ import annotations

import os
import re
import sys
import zipfile

# Required runtime files that MUST be at the zip root (flat layout).
REQUIRED_AT_ROOT = {
    "sagemaker_agent.py",
    "chat.ipynb",
    "USER_GUIDE.md",
    "memory.md",
    "AGENT_STATUS.md",
}

# Required skill subfolders (must each have a SKILL.md).
REQUIRED_SKILLS = {
    "batch", "clara", "design", "reflexion", "report", "review",
    "security-review", "simplify", "verify",
}

# Patterns whose presence is a ship-blocker (dev artefacts that leaked through).
FORBIDDEN_PATTERNS = [
    re.compile(r"^v410_nb_"),         # test_v410_notebook_edit.py tempdirs
    re.compile(r"^v410_skills_"),     # test_v410_skill_listing_budget.py tempdirs
    re.compile(r"^v410_subagent_env_"),  # test_v410_subagent_env.py tempdirs
    re.compile(r"^v410_ctxwin_"),     # test_v410_context_window.py tempdirs
    re.compile(r"(^|/)test_.*\.py$"),  # any test file
    re.compile(r"(^|/)__pycache__"),
    re.compile(r"(^|/)\.pytest_cache"),
    re.compile(r"(^|/)\.snapshots"),
    re.compile(r"(^|/)\.code_index"),
    re.compile(r"(^|/)audit_logs"),
    re.compile(r"(^|/)truncated_outputs"),
    re.compile(r"(^|/)\.proposed/"),  # skill self-patching proposals — repo only
    re.compile(r"(^|/)MAIN/agent/"),  # the unflattened wrapper folder
    re.compile(r"\.pyc$"),
    re.compile(r"\.swp$"),
    re.compile(r"\.DS_Store$"),
]


def _check(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    return condition


def main(zip_path: str = "compact_v4.zip") -> int:
    if not os.path.exists(zip_path):
        print(f"ERROR: zip not found: {zip_path}")
        return 1

    print(f"Verifying ship zip: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path):,} bytes\n")

    z = zipfile.ZipFile(zip_path)
    names = z.namelist()
    print(f"Total entries: {len(names)}\n")

    failures = 0

    print("== Required runtime files at root ==")
    for required in sorted(REQUIRED_AT_ROOT):
        if not _check(f"root file: {required}", required in names):
            failures += 1

    print()
    print("== Required skill subfolders ==")
    for skill in sorted(REQUIRED_SKILLS):
        skill_md = f"skills/{skill}/SKILL.md"
        if not _check(f"skill: {skill_md}", skill_md in names):
            failures += 1

    print()
    print("== No forbidden artefacts ==")
    for entry in names:
        for pat in FORBIDDEN_PATTERNS:
            if pat.search(entry):
                print(f"  [FAIL] forbidden artefact: {entry}  (matched /{pat.pattern}/)")
                failures += 1
                break

    print()
    print("== Version sanity inside zip ==")
    try:
        agent_bytes = z.read("sagemaker_agent.py")
        agent_text = agent_bytes.decode("utf-8", errors="ignore")
        m = re.search(r'__version__ = "([\d.]+)"', agent_text)
        if not _check("__version__ found", bool(m)):
            failures += 1
        else:
            ver = m.group(1)
            print(f"        version: {ver}")
            if not _check("version is 4.10.x", ver.startswith("4.10."), f"got {ver}"):
                failures += 1
        if not _check(
            "default model is Sonnet 4.5",
            "claude-sonnet-4-5-20250929-v1:0" in agent_text,
        ):
            failures += 1
        if not _check("notebook_edit tool present", "def tool_notebook_edit(" in agent_text):
            failures += 1
        if not _check("context_collapse fn present", "def context_collapse(" in agent_text):
            failures += 1
        if not _check(
            "enforce_verify_contract config present",
            "enforce_verify_contract" in agent_text,
        ):
            failures += 1
        if not _check(
            "BEDROCK_MODEL_CONTEXT_WINDOWS present",
            "BEDROCK_MODEL_CONTEXT_WINDOWS" in agent_text,
        ):
            failures += 1
        if not _check(
            "skill auto-trigger default OFF",
            "enable_skill_auto_trigger: bool = False" in agent_text,
        ):
            failures += 1
    except KeyError:
        print("  [FAIL] sagemaker_agent.py missing from zip — already counted above")

    print()
    print("== Layout checks ==")
    deep_paths = [n for n in names if n.count("/") >= 3 and not n.startswith("skills/")]
    if not _check(
        f"no deep wrapper dirs (>= 3 slashes outside skills/)",
        not deep_paths,
        f"found {len(deep_paths)}: {deep_paths[:3]}" if deep_paths else "",
    ):
        failures += 1

    print()
    if failures == 0:
        print("RESULT: PASS — zip is ship-ready.")
        return 0
    else:
        print(f"RESULT: FAIL — {failures} blocker(s). Do NOT ship.")
        return 1


if __name__ == "__main__":
    zp = sys.argv[1] if len(sys.argv) > 1 else "compact_v4.zip"
    sys.exit(main(zp))
