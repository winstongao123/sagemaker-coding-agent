# Claude CLI Review: UI-TOOL-CARDS

Repo: d:/Github/sagemaker-coding-agent
Active ship tree: compact_v5/compact_v5/
Scope: v5.0.2 UI live-supervisor upgrade, UI observability only.

Review this block diff only. Questions you must answer:
- Does this block preserve v5 architecture?
- Any code drift from the UI-only scope?
- Any regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim guard, subagent receipts, or cost/cache accounting?
- Are tests/checks sufficient?
- Verdict: APPROVE / REQUEST_CHANGES

Context: this block adds v4-style tool/thinking/system cards and wires QueryEngine.tool_gen_callback to the UI. Any engine touch should be callback-only observability.

## Diff
```diff
diff --git a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-TOOL-CARDS_before/chat_ui.py b/compact_v5/compact_v5/ui/chat_ui.py
index 6ee4174..3838dfe 100644
--- a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-TOOL-CARDS_before/chat_ui.py
+++ b/compact_v5/compact_v5/ui/chat_ui.py
@@ -21,6 +21,7 @@ PORT_LOG: #030.
 from __future__ import annotations
 
 import logging
+import json
 import re
 import threading
 from datetime import datetime
@@ -510,14 +511,39 @@ class V4WidgetChatUI(WidgetChatUI):
                 else:
                     role, text, ts = message
                     meta = {}
-                color = "#26c6da" if role == "user" else ("#42a5f5" if role == "assistant" else "#ef5350")
-                label = "You" if role == "user" else ("Agent" if role == "assistant" else "System")
                 if role == "assistant":
+                    color = "#42a5f5"
+                    label = "Agent"
                     body = self._render_assistant_markdown(text, c["fg"], self._dark_mode)
+                elif role == "tool":
+                    color = "#ffb74d"
+                    label = f"Tool: {self._escape((meta or {}).get('tool_name', 'tool'))}"
+                    phase = self._escape((meta or {}).get("phase", "result"))
+                    body = (
+                        f"<div style='color:{c['muted']};font-size:11px;margin-bottom:4px;'>"
+                        f"{phase}</div>"
+                        f"<pre style='white-space:pre-wrap;max-height:260px;overflow:auto;"
+                        f"background:{'#151515' if self._dark_mode else '#f7f7f7'};"
+                        f"border:1px solid {c['border']};border-radius:6px;padding:8px;"
+                        "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
+                        f"font-size:12px;color:{c['fg']};'>{self._escape(text)}</pre>"
+                    )
+                elif role == "thinking":
+                    color = "#ab47bc"
+                    label = "Thinking"
+                    body = (
+                        f"<details open><summary style='cursor:pointer;color:{color};'>"
+                        "Reasoning / thinking</summary>"
+                        f"<div style='color:{c['muted']};font-size:12px;line-height:1.45;"
+                        f"margin-top:4px;'>{self._escape(text).replace(chr(10), '<br>')}</div></details>"
+                    )
                 else:
+                    color = "#ffd166" if role == "system" else "#ef5350"
+                    label = "System" if role == "system" else self._escape(role.title())
                     body = self._escape(text).replace("\n", "<br>")
                 meta_html = self._render_turn_meta(meta, c) if role == "assistant" else ""
-                rows.append(f"<div style='margin:8px 0;border-left:3px solid {color};padding-left:10px;'><b style='color:{color};'>[{ts}] {label}:</b><div style='color:{c['fg']};margin-top:4px;line-height:1.5;'>{body}</div>{meta_html}</div>")
+                bg = "rgba(255,255,255,0.025)" if self._dark_mode else "rgba(0,0,0,0.025)"
+                rows.append(f"<div style='margin:8px 0;border-left:3px solid {color};background:{bg};padding:8px 10px;border-radius:6px;'><b style='color:{color};'>[{ts}] {label}:</b><div style='color:{c['fg']};margin-top:4px;line-height:1.5;'>{body}</div>{meta_html}</div>")
             content = "".join(rows)
         self._chat_display.value = f"<div style='height:{self._chat_height}px;min-height:200px;max-height:90vh;overflow-y:auto;overflow-x:hidden;border:1px solid {c['border']};background:{c['bg']};display:flex;flex-direction:column-reverse;width:100%;box-sizing:border-box;resize:vertical;'><div style='padding:10px;font-family:system-ui,-apple-system,sans-serif;'>{content}</div></div>"
 
@@ -922,8 +948,17 @@ class V4WidgetChatUI(WidgetChatUI):
             "reasoning_state": f"Thinking {thinking_state} (budget {thinking_budget})",
         }
 
-    def _append_message(self, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> int:
-        self._messages.append((role, content, datetime.now().strftime("%H:%M:%S"), meta or {}))
+    def _append_message(
+        self,
+        role: str,
+        content: str,
+        meta: Optional[Dict[str, Any]] = None,
+        tool_name: str = "",
+    ) -> int:
+        msg_meta = dict(meta or {})
+        if tool_name:
+            msg_meta["tool_name"] = tool_name
+        self._messages.append((role, content, datetime.now().strftime("%H:%M:%S"), msg_meta))
         self._render_chat()
         return len(self._messages) - 1
 
@@ -948,6 +983,13 @@ class V4WidgetChatUI(WidgetChatUI):
         stripped = chunk.strip()
         if not stripped:
             return None
+        tool_match = re.match(r"^\[([A-Za-z_][\w.-]*)\s+result\]:\s*(.*)$", stripped, re.DOTALL)
+        if tool_match:
+            tool = tool_match.group(1)
+            body = tool_match.group(2).strip()
+            self._append_message("tool", body, {"phase": "result from output stream"}, tool_name=tool)
+            self._render_status()
+            return None
         if stripped.startswith("["):
             self._append_message("system", stripped)
             self._render_status()
@@ -957,6 +999,23 @@ class V4WidgetChatUI(WidgetChatUI):
         self._render_status()
         return index
 
+    def _on_tool_generation(self, event: Dict[str, Any]) -> None:
+        event_type = str(event.get("type", "tool_generation"))
+        name = str(event.get("name", "tool") or "tool")
+        if event_type == "tool_generation":
+            try:
+                body = json.dumps(event.get("input", {}) or {}, indent=2, sort_keys=True, default=str)
+            except Exception:
+                body = str(event.get("input", {}) or {})
+            self._append_message("tool", body, {"phase": "call requested"}, tool_name=name)
+        elif event_type == "tool_result":
+            body = str(event.get("content", "") or "")
+            if len(body) > 12000:
+                body = body[:12000] + "\n\n[tool result truncated in UI; full result remains in runtime conversation/audit]"
+            phase = "error result" if event.get("is_error") else "result"
+            self._append_message("tool", body, {"phase": phase}, tool_name=name)
+        self._render_status()
+
     def _dispatch_ui_command(self, command: str) -> None:
         try:
             from commands import dispatch_command
@@ -1006,10 +1065,26 @@ class V4WidgetChatUI(WidgetChatUI):
             streamed = []
             self._live_assistant_index = None
             before_stats = self._stats_snapshot()
-            result = self.agent.run(
-                msg,
-                output_fn=lambda s: self._live_output_router(s, streamed),
-            )
+            previous_tool_callback = None
+            try:
+                engine = getattr(self.agent, "_engine", None)
+                if engine is not None:
+                    previous_tool_callback = getattr(engine, "tool_gen_callback", None)
+                    engine.tool_gen_callback = self._on_tool_generation
+            except Exception:
+                previous_tool_callback = None
+            try:
+                result = self.agent.run(
+                    msg,
+                    output_fn=lambda s: self._live_output_router(s, streamed),
+                )
+            finally:
+                try:
+                    engine = getattr(self.agent, "_engine", None)
+                    if engine is not None:
+                        engine.tool_gen_callback = previous_tool_callback
+                except Exception:
+                    pass
             after_stats = self._stats_snapshot()
             turn_meta = self._turn_meta_from_stats(before_stats, after_stats, result)
             if self._live_assistant_index is not None and result.text:
diff --git a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-TOOL-CARDS_before/query_engine.py b/compact_v5/compact_v5/core/query_engine.py
index 6c63ce2..233fcc8 100644
--- a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-TOOL-CARDS_before/query_engine.py
+++ b/compact_v5/compact_v5/core/query_engine.py
@@ -1531,6 +1531,7 @@ class QueryEngine:
                 "output_fn": output_fn,
             })
             text = _coerce_tool_result_to_text(raw)
+            self._notify_tool_result(call, text, is_error=False)
             try:
                 from runtime.audit import AUDIT as _AUDIT
                 _AUDIT.log(
@@ -1581,6 +1582,11 @@ class QueryEngine:
                 _failure_key,
                 f"{type(exc).__name__}: {exc}",
             )
+            self._notify_tool_result(
+                call,
+                f"error_during_execution: {type(exc).__name__}: {exc}",
+                is_error=True,
+            )
             return {
                 "type": "tool_result",
                 "tool_use_id": call.id,
@@ -1900,6 +1906,24 @@ class QueryEngine:
                     type(exc).__name__, exc,
                 )
 
+    def _notify_tool_result(self, call: Any, text: str, *, is_error: bool) -> None:
+        if self.tool_gen_callback is None:
+            return
+        event = {
+            "type": "tool_result",
+            "tool_use_id": getattr(call, "id", ""),
+            "name": getattr(call, "name", ""),
+            "content": text,
+            "is_error": bool(is_error),
+        }
+        try:
+            self.tool_gen_callback(event)
+        except Exception as exc:  # noqa: BLE001 - callbacks are best-effort UI hooks
+            logging.warning(
+                "[tool-result-callback] %s: %s",
+                type(exc).__name__, exc,
+            )
+
     # ------------------------------------------------------------
     # Internal: A-33 prompt-cache invariant policy
     # ------------------------------------------------------------

```

