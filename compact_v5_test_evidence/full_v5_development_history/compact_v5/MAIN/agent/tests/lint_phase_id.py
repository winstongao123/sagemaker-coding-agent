"""Pre-tag lint check: enforces canonical Phase ID consistency.

Per V5_PLAN.md Risk #14, this check MUST pass before any `v5-phase-{ID}` tag
is created. It cross-validates:
  (a) V5_BUILD_STATUS.md "Phase ID" field
  (b) git tag name about to be created (passed via env or argv)
  (c) Codex review filename (`_status/codex_reviews/phase-{ID}.md`)
  (d) "Last commit" subject line (must contain `v5/phase-{ID}:`)

Canonical ID schema: 00..13 zero-padded, plus `08_5` for the thin-slice
parity gate. No bare `8.5`, no unpadded `0`/`1`/etc.

Usage:
    python tests/lint_phase_id.py 00              # check Phase 0 readiness
    python tests/lint_phase_id.py 08_5            # check Phase 8.5
"""
from __future__ import annotations

import os
import re
import subprocess
import sys


_CANONICAL_IDS = {f"{i:02d}" for i in range(14)} | {"08_5"}

# Repo root sniffing — works whether script is run from compact_v5/MAIN/agent/tests/ or repo root.
_THIS = os.path.abspath(__file__)
_AGENT_ROOT = os.path.dirname(os.path.dirname(_THIS))                    # compact_v5/MAIN/agent
_V5_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))                 # compact_v5
_REPO_ROOT = os.path.dirname(_V5_ROOT)                                   # sagemaker-coding-agent
_STATUS = os.path.join(_V5_ROOT, "_status")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _git(*args: str, cwd: str = _REPO_ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _check_canonical(pid: str) -> None:
    if pid not in _CANONICAL_IDS:
        raise AssertionError(
            f"Phase ID '{pid}' is not canonical. Allowed: {sorted(_CANONICAL_IDS)}"
        )


def _check_status_doc(pid: str) -> None:
    """V5_BUILD_STATUS.md must contain the canonical ID in 'Phase ID:' field."""
    src = _read(os.path.join(_STATUS, "V5_BUILD_STATUS.md"))
    m = re.search(r"Phase ID:\s*(\S+)", src)
    if not m:
        raise AssertionError("V5_BUILD_STATUS.md missing 'Phase ID:' field")
    found = m.group(1)
    if found != pid:
        raise AssertionError(
            f"V5_BUILD_STATUS.md Phase ID is '{found}' but lint was called with '{pid}'"
        )


def _check_codex_review_file(pid: str) -> None:
    """phase-{pid}.md must exist for tag-readiness (Phase 0 is special: no Codex
    review needed because no Runnable patterns adopted; flag as soft-skip)."""
    path = os.path.join(_STATUS, "codex_reviews", f"phase-{pid}.md")
    if pid == "00":
        # Phase 0 is scaffold-only; Codex review optional (table is empty).
        # We still expect SOMETHING at this path for traceability — even an empty stub.
        if not os.path.exists(path):
            print(
                f"  [WARN] Phase 00 has no codex review file ({path}); "
                f"create even an empty stub to record 'scaffold-only, no Runnable port'.",
                file=sys.stderr,
            )
        return
    if not os.path.exists(path):
        raise AssertionError(
            f"Codex review file missing: {path}. Run codex review before tagging."
        )


def _check_last_commit_subject(pid: str) -> None:
    """Last commit on v5-build must mention `v5/phase-{pid}:` in its subject."""
    try:
        subj = _git("log", "-1", "--pretty=%s", "v5-build")
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"git log failed (is v5-build branch present?): {e}")
    expected = f"v5/phase-{pid}:"
    if expected not in subj:
        raise AssertionError(
            f"Last commit subject '{subj}' does not start with '{expected}'. "
            f"Expected convention: 'v5/phase-{pid}: <imperative subject>'"
        )


def _check_no_existing_tag(pid: str) -> None:
    """Tag must NOT yet exist (we're checking pre-tag readiness)."""
    try:
        existing = _git("tag", "-l", f"v5-phase-{pid}")
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"git tag -l failed: {e}")
    if existing.strip():
        raise AssertionError(
            f"Tag v5-phase-{pid} already exists. Lint is for pre-tag check; "
            f"don't re-tag (use a patch tag like v5-phase-{pid}.1 instead)."
        )


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <phase-id>  (e.g. 00, 03, 08_5, 13)", file=sys.stderr)
        return 2
    pid = sys.argv[1]

    checks = [
        ("canonical ID schema",         lambda: _check_canonical(pid)),
        ("V5_BUILD_STATUS.md Phase ID", lambda: _check_status_doc(pid)),
        ("Codex review file present",   lambda: _check_codex_review_file(pid)),
        ("last commit subject",         lambda: _check_last_commit_subject(pid)),
        ("tag does not exist yet",      lambda: _check_no_existing_tag(pid)),
    ]
    failed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
            failed += 1
    print(f"\n{len(checks) - failed}/{len(checks)} checks passed for phase {pid}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
