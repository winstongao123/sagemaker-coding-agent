"""Phase 0 smoke test: verifies the v5 package skeleton imports cleanly.

This is the bare-minimum acceptance test for Phase 0. It does NOT test
behavior — only that every package directory has an importable __init__.py
and the namespace tree is consistent with the V5_PLAN.md folder layout.

Phase 1+ will add behavioral tests as components land.
"""
from __future__ import annotations

import importlib
import os
import sys

# Add the agent root to sys.path so subpackages import as `core`, `tools`, etc.
# (Mirrors the flat-zip ship layout: at runtime, all .py files sit at zip root.)
_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# Packages required to exist by Phase 0 scaffold (must all be importable).
EXPECTED_PACKAGES = [
    "core",
    "prompt",
    "tools",
    "tools.shared",
    "security",
    "runtime",
    "subagent",
    "skills",
    "ui",
    "mcp",
    "tests",
    "tests.unit",
    "tests.tools",
    "tests.integration",
    "tests.parity",
]


def test_every_package_imports_cleanly():
    """Each package directory must have an importable __init__.py."""
    failures = []
    for pkg in EXPECTED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError as e:
            failures.append(f"  [{pkg}] ImportError: {e}")
        except Exception as e:
            failures.append(f"  [{pkg}] {type(e).__name__}: {e}")
    assert not failures, "\n".join(["Packages failed to import:"] + failures)


def test_no_v4_imports_at_phase_0():
    """Phase 0 is pure scaffolding — no v4 code should be ported yet.

    This guard catches accidental Phase 1+ work landing in Phase 0.
    Recursive scan across ALL subdirectories (Codex Phase-0 review
    flagged the prior shallow check). Allowlist:
        - any __init__.py (empty package markers)
        - tests/test_smoke.py + tests/lint_phase_id.py
    Anything else is a Phase 1+ leak into Phase 0.

    Once Phase 1 lands, this test gets removed / relaxed.
    """
    allowed = {"__init__.py", "test_smoke.py", "lint_phase_id.py"}
    leaked = []
    for root, _dirs, files in os.walk(_AGENT_ROOT):
        # Skip __pycache__ etc.
        if "__pycache__" in root or ".pytest_cache" in root:
            continue
        for f in files:
            if f.endswith(".py") and f not in allowed:
                leaked.append(os.path.relpath(os.path.join(root, f), _AGENT_ROOT))
    assert not leaked, (
        f"Phase 0 scaffold should contain no .py files except __init__.py + smoke/lint tests. "
        f"Found leaks: {leaked}. Phase 1+ work has landed into Phase 0."
    )


if __name__ == "__main__":
    tests = [
        ("every_package_imports_cleanly", test_every_package_imports_cleanly),
        ("no_v4_imports_at_phase_0", test_no_v4_imports_at_phase_0),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}:\n{e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} smoke tests passed")
    sys.exit(1 if failed else 0)
