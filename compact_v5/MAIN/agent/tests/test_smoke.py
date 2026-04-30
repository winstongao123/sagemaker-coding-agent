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


def test_phase_01_runtime_files_present():
    """Phase 01 acceptance: runtime/bedrock_client.py + runtime/config.py exist.

    Phase 0's emptiness guard was relaxed once Phase 1 landed
    (per the original comment: "Once Phase 1 lands, this test gets
    removed / relaxed"). Replaced with a positive presence check
    so Phase 1's ports cannot silently regress.
    """
    expected = [
        os.path.join(_AGENT_ROOT, "runtime", "bedrock_client.py"),
        os.path.join(_AGENT_ROOT, "runtime", "config.py"),
        os.path.join(_AGENT_ROOT, "tests", "unit", "test_bedrock.py"),
    ]
    missing = [p for p in expected if not os.path.isfile(p)]
    assert not missing, f"Phase 01 expected files missing: {missing}"


if __name__ == "__main__":
    tests = [
        ("every_package_imports_cleanly", test_every_package_imports_cleanly),
        ("phase_01_runtime_files_present", test_phase_01_runtime_files_present),
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
