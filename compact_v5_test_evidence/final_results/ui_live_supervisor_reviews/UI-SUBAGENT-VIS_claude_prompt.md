# Claude CLI Review: UI-SUBAGENT-VIS

Repo: d:/Github/sagemaker-coding-agent
Active ship tree: compact_v5/compact_v5/
Scope: v5.0.2 UI live-supervisor upgrade, UI observability only.

Review this block diff only. Questions you must answer:
- Does this block preserve v5 architecture?
- Any code drift from the UI-only scope?
- Any regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim guard, subagent receipts, or cost/cache accounting?
- Are tests/checks sufficient?
- Verdict: APPROVE / REQUEST_CHANGES

Context: this block forwards selected synchronous child subagent output through the existing parent output_fn and renders subagent envelope/cost/cache/artifact paths in the UI.

## Diff
```diff
diff --git a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-SUBAGENT-VIS_before/chat_ui.py b/compact_v5/compact_v5/ui/chat_ui.py
index 3838dfe..7696053 100644
--- a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-SUBAGENT-VIS_before/chat_ui.py
+++ b/compact_v5/compact_v5/ui/chat_ui.py
@@ -537,6 +537,30 @@ class V4WidgetChatUI(WidgetChatUI):
                         f"<div style='color:{c['muted']};font-size:12px;line-height:1.45;"
                         f"margin-top:4px;'>{self._escape(text).replace(chr(10), '<br>')}</div></details>"
                     )
+                elif role == "subagent":
+                    color = "#66bb6a"
+                    kind = self._escape((meta or {}).get("subagent_type", "subagent"))
+                    phase = self._escape((meta or {}).get("phase", "update"))
+                    label = f"Subagent: {kind}"
+                    stop = self._escape((meta or {}).get("stop_reason", ""))
+                    cost = self._escape((meta or {}).get("cost_usd", ""))
+                    cache = self._escape((meta or {}).get("cache", ""))
+                    paths = meta.get("artifact_paths", []) if isinstance(meta, dict) else []
+                    details = []
+                    if stop:
+                        details.append(f"stop {stop}")
+                    if cost:
+                        details.append(f"cost {cost}")
+                    if cache:
+                        details.append(f"cache {cache}")
+                    if isinstance(paths, list) and paths:
+                        safe_paths = "<br>".join(self._escape(p) for p in paths[:8])
+                        details.append(f"artifacts<br>{safe_paths}")
+                    detail_html = (
+                        f"<div style='color:{c['muted']};font-size:11px;margin-bottom:4px;'>"
+                        f"{phase}" + ((" | " + " | ".join(details)) if details else "") + "</div>"
+                    )
+                    body = detail_html + self._render_assistant_markdown(text, c["fg"], self._dark_mode)
                 else:
                     color = "#ffd166" if role == "system" else "#ef5350"
                     label = "System" if role == "system" else self._escape(role.title())
@@ -983,6 +1007,29 @@ class V4WidgetChatUI(WidgetChatUI):
         stripped = chunk.strip()
         if not stripped:
             return None
+        sub_match = re.match(r"^\[subagent:([^:\]]+)(?::child)?\]\s*(.*)$", stripped, re.DOTALL)
+        if sub_match:
+            kind = sub_match.group(1)
+            body = sub_match.group(2).strip()
+            phase = "child output" if ":child]" in stripped.split(" ", 1)[0] else "lifecycle"
+            meta = {"subagent_type": kind, "phase": phase}
+            finished = re.search(
+                r"finished:\s*stop=([^\s]+)\s+turns=(\d+)\s+cost=\$([0-9.]+)\s+cache=([0-9,]+/[0-9,]+)",
+                body,
+            )
+            if finished:
+                meta.update({
+                    "phase": "finished",
+                    "stop_reason": finished.group(1),
+                    "turns": finished.group(2),
+                    "cost_usd": f"${finished.group(3)}",
+                    "cache": finished.group(4),
+                })
+            elif body.startswith("started:"):
+                meta["phase"] = "started"
+            self._append_message("subagent", body, meta)
+            self._render_status()
+            return None
         tool_match = re.match(r"^\[([A-Za-z_][\w.-]*)\s+result\]:\s*(.*)$", stripped, re.DOTALL)
         if tool_match:
             tool = tool_match.group(1)
@@ -999,6 +1046,33 @@ class V4WidgetChatUI(WidgetChatUI):
         self._render_status()
         return index
 
+    def _parse_subagent_result(self, body: str) -> Optional[Dict[str, Any]]:
+        marker = "[subagent_result_envelope]"
+        if marker not in body:
+            return None
+        before, after = body.split(marker, 1)
+        try:
+            envelope, _end = json.JSONDecoder().raw_decode(after.strip())
+        except Exception:
+            return None
+        if not isinstance(envelope, dict):
+            return None
+        artifacts = envelope.get("artifact_paths", [])
+        if not artifacts and "[subagent_artifacts]" in body:
+            artifact_text = body.split("[subagent_artifacts]", 1)[1]
+            artifacts = [line.strip() for line in artifact_text.splitlines() if line.strip()]
+        cache = envelope.get("cache", {}) if isinstance(envelope.get("cache"), dict) else {}
+        meta = {
+            "phase": "result envelope",
+            "subagent_type": envelope.get("agent_type") or envelope.get("role") or "subagent",
+            "stop_reason": envelope.get("stop_reason", ""),
+            "cost_usd": f"${float(envelope.get('cost_usd', 0.0) or 0.0):.4f}",
+            "cache": f"{int(cache.get('read_tokens', 0) or 0):,}/{int(cache.get('write_tokens', 0) or 0):,}",
+            "artifact_paths": list(artifacts or []),
+        }
+        selected = before.strip() or str(envelope.get("summary", "") or "(no child output)")
+        return {"text": selected, "meta": meta}
+
     def _on_tool_generation(self, event: Dict[str, Any]) -> None:
         event_type = str(event.get("type", "tool_generation"))
         name = str(event.get("name", "tool") or "tool")
@@ -1010,6 +1084,10 @@ class V4WidgetChatUI(WidgetChatUI):
             self._append_message("tool", body, {"phase": "call requested"}, tool_name=name)
         elif event_type == "tool_result":
             body = str(event.get("content", "") or "")
+            if name == "task":
+                parsed = self._parse_subagent_result(body)
+                if parsed:
+                    self._append_message("subagent", parsed["text"], parsed["meta"])
             if len(body) > 12000:
                 body = body[:12000] + "\n\n[tool result truncated in UI; full result remains in runtime conversation/audit]"
             phase = "error result" if event.get("is_error") else "result"
diff --git a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-SUBAGENT-VIS_before/task.py b/compact_v5/compact_v5/tools/task.py
index bede34f..ddc9e25 100644
--- a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-SUBAGENT-VIS_before/task.py
+++ b/compact_v5/compact_v5/tools/task.py
@@ -252,6 +252,13 @@ def _task_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = Non
     from subagent.spawn import spawn_subagent
 
     summary = description or prompt.replace("\n", " ")[:120]
+    child_output_count = 0
+
+    def _subagent_output(text: str) -> None:
+        nonlocal child_output_count
+        child_output_count += 1
+        output_fn(f"[subagent:{subagent_type}:child] {text}")
+
     output_fn(f"[subagent:{subagent_type}] started: {summary}")
     result = spawn_subagent(
         parent_engine=parent_engine,
@@ -260,7 +267,7 @@ def _task_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = Non
         parent_depth=parent_depth,
         model_id=subagent_model or None,
         plan_mode=bool(context.get("plan_mode", False)),
-        output_fn=output_fn,
+        output_fn=_subagent_output,
     )
     token_delta = result.token_delta or {}
     output_fn(
@@ -274,6 +281,8 @@ def _task_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = Non
             cache_write=int(token_delta.get("cache_write_tokens", 0) or 0),
         )
     )
+    if child_output_count:
+        output_fn(f"[subagent:{subagent_type}] streamed child updates={child_output_count}")
 
     envelope_data = result.to_envelope()
     artifact_paths = _persist_subagent_receipts(

```

