You are an independent senior code reviewer doing final review after low-risk refinements.

Context:
- User asked to investigate tests/PS_Final_test/final_test_v5_responds.md for reasoning/tool/token/process issues and fix problems.
- Transcript issues fixed: false missing-path guard caused final-task churn; bash glob commands did not shell-expand and caused false No such file errors.
- Prior Claude review approved but noted low-risk refinements. Applied refinements: roots only extend from explicit requested project/folder/workspace roots; quoted relative dirs with separators are accepted as deliverables; bash doc notes POSIX/SageMaker local shell scope.
- Local verification passed: targeted tests => 5 passed, full suite => 63 passed.

Return exactly:
VERDICT: APPROVE or REQUEST_CHANGES
FINDINGS:
- severity, file/line or function, issue, required fix
REGRESSION_RISK:
- concise notes
TEST_GAPS:
- concise notes

Diff:
```diff
diff --git a/compact_v5/core/query_engine.py b/compact_v5/core/query_engine.py
index 4b9c1fd..75de5be 100644
--- a/compact_v5/core/query_engine.py
+++ b/compact_v5/core/query_engine.py
@@ -2665,36 +2665,107 @@ class QueryEngine:
         """Best-effort exact-path gate for user-provided deliverable lists."""
         if not requested:
             return []
+        requested = re.sub(r"https?://\S+", " ", requested)
         candidates: Set[str] = set()
-        path_pattern = re.compile(
-            r"(?<![A-Za-z0-9_./\\-])"
-            r"([A-Za-z0-9_.+ -]+(?:[\\/][A-Za-z0-9_.+ -]+)+/?"
-            r"|[A-Za-z0-9_.+-]+\.(?:py|md|txt|json|toml|yaml|yml|ipynb|zip))"
-        )
-        for raw in path_pattern.findall(requested):
+
+        def _clean(raw: str) -> str:
             item = raw.strip().strip("`'\".,;:")
             item = re.sub(r"^\s*[-*]\s+", "", item).strip()
-            if not item or item.startswith(("/", "\\")):
-                continue
+            return item
+
+        def _is_absolute_like(item: str) -> bool:
+            return bool(
+                re.match(r"^[A-Za-z]:[\\/]", item)
+                or item.startswith(("/", "\\", "~"))
+            )
+
+        def _looks_like_deliverable_path(
+            item: str,
+            *,
+            explicit_root: bool = False,
+            quoted: bool = False,
+        ) -> bool:
             lowered = item.lower()
-            if lowered.startswith(("http://", "https://")):
-                continue
-            if not (
-                "/" in item
-                or "\\" in item
-                or lowered.endswith((".zip", "readme.md", "agent_status.md", "pyproject.toml"))
+            if explicit_root:
+                return True
+            if item.endswith(("/", "\\")):
+                return True
+            if re.search(r"\.(?:py|md|txt|json|toml|yaml|yml|ipynb|zip)$", lowered):
+                return True
+            if quoted and (_is_absolute_like(item) or "/" in item or "\\" in item):
+                return True
+            return False
+
+        explicit_roots: Set[str] = set()
+        root_context_pattern = re.compile(
+            r"\b(?:folder|directory|project|workspace|repo|repository|root)\s+"
+            r"(?:at|in|under|to|is|:)?\s*"
+            r"(?:`([^`]+)`|'([^']+)'|\"([^\"]+)\"|"
+            r"((?:[A-Za-z]:[\\/]|[\\/]|~[\\/])[A-Za-z0-9_.+-]+"
+            r"(?:[\\/][A-Za-z0-9_.+-]+)*))",
+            re.IGNORECASE,
+        )
+        for groups in root_context_pattern.findall(requested):
+            raw = next((group for group in groups if group), "")
+            item = _clean(raw)
+            if item:
+                explicit_roots.add(item)
+                candidates.add(item)
+
+        quoted_path_pattern = re.compile(
+            r"[`'\"]("
+            r"(?:[A-Za-z]:[\\/]|[\\/]|~[\\/])?[A-Za-z0-9_.+ -]+"
+            r"(?:[\\/][A-Za-z0-9_.+ -]+)+/?"
+            r"|[A-Za-z0-9_.+ -]+\.(?:py|md|txt|json|toml|yaml|yml|ipynb|zip)"
+            r")[`'\"]"
+        )
+        plain_path_pattern = re.compile(
+            r"(?<![A-Za-z0-9_.+/\\-])("
+            r"(?:[A-Za-z]:[\\/]|[\\/]|~[\\/])?[A-Za-z0-9_.+-]+"
+            r"(?:[\\/][A-Za-z0-9_.+-]+)+/?"
+            r"|[A-Za-z0-9_.+-]+\.(?:py|md|txt|json|toml|yaml|yml|ipynb|zip)"
+            r")(?![A-Za-z0-9_.+/\\-])"
+        )
+        for pattern, quoted in ((quoted_path_pattern, True), (plain_path_pattern, False)):
+            for raw in pattern.findall(requested):
+                item = _clean(raw)
+                lowered = item.lower()
+                if (
+                    item
+                    and not lowered.startswith(("http://", "https://"))
+                    and _looks_like_deliverable_path(
+                        item,
+                        explicit_root=item in explicit_roots,
+                        quoted=quoted,
+                    )
+                ):
+                    candidates.add(item)
+
+        roots: List[str] = []
+        workspace_abs = os.path.abspath(os.path.expanduser(workspace or os.getcwd()))
+        roots.append(workspace_abs)
+        for item in sorted(candidates):
+            expanded = os.path.abspath(os.path.expanduser(item))
+            if (
+                item in explicit_roots
+                and _is_absolute_like(item)
+                and os.path.isdir(expanded)
+                and expanded not in roots
             ):
-                continue
-            candidates.add(item)
+                roots.append(expanded)
 
         missing: List[str] = []
         for item in sorted(candidates):
             rel = item.replace("\\", os.sep).replace("/", os.sep)
-            path = rel if os.path.isabs(rel) else os.path.join(workspace, rel)
+            expanded = os.path.abspath(os.path.expanduser(rel))
+            if _is_absolute_like(item):
+                paths = [expanded]
+            else:
+                paths = [os.path.join(root, rel) for root in roots]
             if item.endswith(("/", "\\")):
-                exists = os.path.isdir(path)
+                exists = any(os.path.isdir(path) for path in paths)
             else:
-                exists = os.path.exists(path)
+                exists = any(os.path.exists(path) for path in paths)
             if not exists:
                 missing.append(item)
         return missing
@@ -2740,7 +2811,13 @@ class QueryEngine:
             )
         ):
             return ""
-        log_dir = os.path.join(workspace, ".sageagent_state")
+        try:
+            from runtime.config import CONFIG
+            from runtime.workspace import state_dir
+
+            log_dir = str(state_dir(workspace, CONFIG))
+        except Exception:
+            log_dir = os.path.join(workspace, ".sageagent_state")
         log_path = os.path.join(log_dir, "final_claim_pytest.log")
         try:
             os.makedirs(log_dir, exist_ok=True)
diff --git a/compact_v5/tools/bash.py b/compact_v5/tools/bash.py
index 0bf600e..8f16f7a 100644
--- a/compact_v5/tools/bash.py
+++ b/compact_v5/tools/bash.py
@@ -51,6 +51,7 @@ Usage:
 - Workspace boundary: any absolute path mentioned in the command must be inside CONFIG.workspace or one of CONFIG.allowed_paths. /tmp/, /usr/bin/, /usr/local/bin/, /bin/, /opt/ are allowed.
 - `python_exec` is the canonical Python execution tool — DO NOT use `python -c` via bash (the denylist blocks it explicitly).
 - Output is captured (stdout + stderr); large outputs are smart-truncated (head 100 + tail 50 lines).
+- In POSIX/SageMaker local shells, globs such as `*.py` are expanded safely by the shell; use `find`/`glob` for large file inventories.
 - Default timeout 120s, max 600s.
 - Managed background jobs are available with `background=true`; use `action=poll|wait|kill` and `job_id` to manage them. Logs are stored under `.sageagent_state/shell_jobs/`.
 - Approval is required before any command runs.
@@ -168,7 +169,7 @@ def _bash_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = Non
                 cwd=_current_workspace(), env=safe_exec_env(),
             )
         else:
-            needs_shell = bool(re.search(r"[|><;]|&&|\|\||`|\$\(", command))
+            needs_shell = bool(re.search(r"[|><;*]|&&|\|\||`|\$\(", command))
             if needs_shell:
                 redir_ok, redir_msg = validate_shell_redirections(command)
                 if not redir_ok:
```

New test file tests/test_final_task_regression_guards.py:
```python
import os
from types import SimpleNamespace

from core.query_engine import QueryEngine


def test_missing_requested_paths_uses_explicit_project_root(tmp_path):
    project = tmp_path / "TEST_v5_FINAL_READY"
    for rel in (
        "notes_cli_final/models.py",
        "notes_cli_final/store.py",
        "notes_cli_final/search.py",
        "notes_cli_final/report.py",
        "notes_cli_final/cli.py",
        "tests/test_store.py",
        "tests/test_cli.py",
        "tests/test_search.py",
        "README.md",
        "AGENT_STATUS.md",
        "docs/TEST_REPORT.md",
        "docs/REVIEW.md",
        "requirements.txt",
    ):
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")
    (project / "docs/reviews").mkdir(parents=True)
    (project / "docs/logs").mkdir(parents=True)

    request = (
        f"Create a folder at {project}. Build notes_cli_final with: "
        "- notes_cli_final/models.py - notes_cli_final/store.py "
        "- notes_cli_final/search.py - notes_cli_final/report.py "
        "- notes_cli_final/cli.py - tests/test_store.py - tests/test_cli.py "
        "- tests/test_search.py - README.md - AGENT_STATUS.md "
        "- docs/TEST_REPORT.md - docs/REVIEW.md - docs/reviews/ - docs/logs/ "
        "- `requirements.txt` "
        "Tests must cover: empty store - add/list - CLI happy path. "
        "Final answer must include: cost - context - exact tests."
    )

    missing = QueryEngine._missing_requested_paths(request, str(tmp_path / "runtime"))

    assert missing == []


def test_missing_requested_paths_does_not_treat_process_text_as_paths(tmp_path):
    request = (
        "Process requirements: 1. Keep AGENT_STATUS.md updated throughout. "
        "Run targeted tests first, then all tests. "
        "Tests must cover: empty store - add/list - duplicate id prevention. "
        "Final answer must include: cost/context and SPEC vs SHIPPED. "
        "Ignore https://example.com/docs/path.py and casual system path /tmp/scratch."
    )

    missing = QueryEngine._missing_requested_paths(request, str(tmp_path))

    assert "add/list" not in missing
    assert "cost/context" not in missing
    assert "/tmp/scratch" not in missing
    assert all(" " not in item for item in missing)


def test_missing_requested_paths_keeps_explicit_root_scoped(tmp_path):
    project = tmp_path / "requested_project"
    unrelated = tmp_path / "unrelated"
    project.mkdir()
    target = unrelated / "notes_cli_final" / "models.py"
    target.parent.mkdir(parents=True)
    target.write_text("wrong root\n", encoding="utf-8")

    request = (
        f"Create a folder at {project}. Also inspect {unrelated}/ if useful. "
        "Required deliverable: notes_cli_final/models.py"
    )

    missing = QueryEngine._missing_requested_paths(request, str(tmp_path / "runtime"))

    assert "notes_cli_final/models.py" in missing


def test_missing_requested_paths_accepts_quoted_relative_directories(tmp_path):
    request = "Create the helper package directory `src/utils` before final answer."

    missing = QueryEngine._missing_requested_paths(request, str(tmp_path))

    assert "src/utils" in missing


def test_bash_executor_uses_shell_for_globs(monkeypatch, tmp_path):
    from runtime.config import CONFIG
    from security.manager import rebuild_singleton_for_tests
    from tools import bash as bash_tool

    old_workspace = CONFIG.workspace
    old_mode = CONFIG.execution_mode
    CONFIG.workspace = str(tmp_path)
    CONFIG.execution_mode = "local"
    rebuild_singleton_for_tests()

    calls = {}

    def fake_run_subprocess(cmd_arg, timeout, shell, cwd, env):
        calls.update({"cmd_arg": cmd_arg, "shell": shell, "cwd": cwd})
        return SimpleNamespace(stdout="ok\n", stderr="", returncode=0)

    monkeypatch.setattr(bash_tool, "run_subprocess", fake_run_subprocess)

    try:
        output = bash_tool._bash_executor({"command": "wc -l notes_cli_final/*.py"}, {})
    finally:
        CONFIG.workspace = old_workspace
        CONFIG.execution_mode = old_mode
        rebuild_singleton_for_tests()

    assert "ok" in output
    assert calls["shell"] is True
    assert calls["cmd_arg"] == "wc -l notes_cli_final/*.py"
    assert os.path.abspath(calls["cwd"]) == os.path.abspath(str(tmp_path))

```
