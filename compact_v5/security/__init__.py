"""V5 security/ package — re-exports the public surface.

Phase-3-4 tools imported `tools._path_validation`. That stub now
delegates to `security.manager.SECURITY.validate_path`. Phase 5+
modules should import directly from `security` for the new APIs:

    from security import SECURITY, validate_path, resolve_path
    from security import HIGH_RISK_TOOLS, is_high_risk
    from security.manager import (
        kill_active_process, safe_exec_env, run_subprocess,
        validate_shell_redirections, docker_base_cmd,
    )
"""
from __future__ import annotations

from .high_risk import HIGH_RISK_TOOLS, is_high_risk  # noqa: F401
from .manager import (  # noqa: F401  (public re-exports)
    SecurityManager,
    SECRET_PATTERNS,
    SENSITIVE_FILES,
    _resolve_path,
    _auto_detect_allowed_paths,
    docker_base_cmd,
    ensure_docker_image_ready,
    kill_active_process,
    rebuild_singleton_for_tests,
    resolve_path,
    run_subprocess,
    safe_exec_env,
    validate_path,
    validate_shell_redirections,
)


# `SECURITY` is intentionally NOT re-exported as a static binding here.
#
# Codex Phase-05 review finding 3 clarified: Python's `from security
# import SECURITY` is a one-shot binding — the module-level __getattr__
# below fires once at the import site, then the local name `SECURITY`
# caches that value. A subsequent `rebuild_singleton_for_tests()` will
# swap `security.manager.SECURITY` but the imported local stays stale.
#
# Live-lookup access patterns:
#   import security as sec; sec.SECURITY              # uses __getattr__ per access — LIVE
#   import security.manager as sm; sm.SECURITY        # regular attribute lookup — LIVE
#   from security import get_security; get_security() # function call — LIVE
#
# Stale-after-rebuild patterns (avoid in code that may rebuild):
#   from security import SECURITY                     # one-shot import binding
#   from security.manager import SECURITY             # one-shot import binding
#
# Tools that need to track rebuilds (bash, python_exec) import the
# `security.manager` MODULE and dereference `module.SECURITY` at call
# time — see tools/bash.py for the canonical pattern.
def __getattr__(name):
    if name == "SECURITY":
        from . import manager
        return manager.SECURITY
    raise AttributeError(f"module 'security' has no attribute {name!r}")


def get_security():
    """Return the current SECURITY singleton. Always live (looks up
    `security.manager.SECURITY` at call time, so rebuilds are picked up).

    Use this in code paths that prefer a function-call style over the
    `import security as sec; sec.SECURITY` pattern."""
    from . import manager
    return manager.SECURITY
