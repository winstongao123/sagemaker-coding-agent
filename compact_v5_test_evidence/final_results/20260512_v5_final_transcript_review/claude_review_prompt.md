You are an independent senior code reviewer. Review this compact_v5 fix set based on the user's final-test transcript investigation.

Context:
- Transcript: tests/PS_Final_test/final_test_v5_responds.md
- Observed final coding task outcome was mostly successful, but v5 wasted turns near the end.
- Issue 1: QueryEngine._missing_requested_paths over-captured English phrases such as process requirements, add/list, and cost/context as required file paths. It also checked relative deliverables only under CONFIG.workspace even when the user gave an explicit project root like /home/sagemaker-user/TEST_v5_FINAL_READY.
- Issue 2: tools/bash.py ran non-piped commands with shell=False, so commands like wc -l notes_cli_final/*.py did not expand globs and produced false No such file failures.
- Fixes: stricter path extraction, explicit-root relative deliverable lookup, bash glob shell execution, and focused regression tests.
- Local verification already passed: py -3.10 -m pytest tests -q => 61 passed.

Please review for regressions or missing cases. Return exactly:
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
index 4b9c1fd..f3e348e 100644
--- a/compact_v5/core/query_engine.py
+++ b/compact_v5/core/query_engine.py
@@ -2665,36 +2665,71 @@ class QueryEngine:
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
+        def _looks_like_deliverable_path(item: str) -> bool:
             lowered = item.lower()
-            if lowered.startswith(("http://", "https://")):
-                continue
-            if not (
-                "/" in item
-                or "\\" in item
-                or lowered.endswith((".zip", "readme.md", "agent_status.md", "pyproject.toml"))
-            ):
-                continue
-            candidates.add(item)
+            if re.match(r"^[A-Za-z]:[\\/]", item) or item.startswith(("/", "\\", "~")):
+                return True
+            if item.endswith(("/", "\\")):
+                return True
+            if re.search(r"\.(?:py|md|txt|json|toml|yaml|yml|ipynb|zip)$", lowered):
+                return True
+            return False
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
+        for pattern in (quoted_path_pattern, plain_path_pattern):
+            for raw in pattern.findall(requested):
+                item = _clean(raw)
+                lowered = item.lower()
+                if (
+                    item
+                    and not lowered.startswith(("http://", "https://"))
+                    and _looks_like_deliverable_path(item)
+                ):
+                    candidates.add(item)
+
+        roots: List[str] = []
+        workspace_abs = os.path.abspath(os.path.expanduser(workspace or os.getcwd()))
+        roots.append(workspace_abs)
+        for item in sorted(candidates):
+            expanded = os.path.abspath(os.path.expanduser(item))
+            if os.path.isabs(expanded) and os.path.isdir(expanded):
+                roots.append(expanded)
 
         missing: List[str] = []
         for item in sorted(candidates):
             rel = item.replace("\\", os.sep).replace("/", os.sep)
-            path = rel if os.path.isabs(rel) else os.path.join(workspace, rel)
+            expanded = os.path.abspath(os.path.expanduser(rel))
+            if os.path.isabs(expanded) and (
+                item.startswith(("/", "\\", "~")) or re.match(r"^[A-Za-z]:[\\/]", item)
+            ):
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
@@ -2740,7 +2775,13 @@ class QueryEngine:
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
index 0bf600e..fbf63ce 100644
--- a/compact_v5/tools/bash.py
+++ b/compact_v5/tools/bash.py
@@ -51,6 +51,7 @@ Usage:
 - Workspace boundary: any absolute path mentioned in the command must be inside CONFIG.workspace or one of CONFIG.allowed_paths. /tmp/, /usr/bin/, /usr/local/bin/, /bin/, /opt/ are allowed.
 - `python_exec` is the canonical Python execution tool — DO NOT use `python -c` via bash (the denylist blocks it explicitly).
 - Output is captured (stdout + stderr); large outputs are smart-truncated (head 100 + tail 50 lines).
+- Shell globs such as `*.py` are expanded safely by the shell; use `find`/`glob` for large file inventories.
 - Default timeout 120s, max 600s.
 - Managed background jobs are available with `background=true`; use `action=poll|wait|kill` and `job_id` to manage them. Logs are stored under `.sageagent_state/shell_jobs/`.
 - Approval is required before any command runs.
@@ -168,7 +169,7 @@ def _bash_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = Non
                 cwd=_current_workspace(), env=safe_exec_env(),
             )
         else:
-            needs_shell = bool(re.search(r"[|><;]|&&|\|\||`|\$\(", command))
+            needs_shell = bool(re.search(r"[|><;*?\[\]]|&&|\|\||`|\$\(", command))
             if needs_shell:
                 redir_ok, redir_msg = validate_shell_redirections(command)
                 if not redir_ok:
```
