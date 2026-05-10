# Claude CLI Review: UI-STOP-STATUS

Repo: d:/Github/sagemaker-coding-agent
Active ship tree: compact_v5/compact_v5/
Scope: v5.0.2 UI live-supervisor upgrade, UI observability only.

Review this block diff only. Questions you must answer:
- Does this block preserve v5 architecture?
- Any code drift from the UI-only scope?
- Any regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim guard, subagent receipts, or cost/cache accounting?
- Are tests/checks sufficient?
- Verdict: APPROVE / REQUEST_CHANGES

Context: this block only changes notebook wording/status to explain cooperative Stop.

## Diff
```diff
diff --git a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-STOP-STATUS_before/chat_ui.py b/compact_v5/compact_v5/ui/chat_ui.py
index 601f0ef..c03d0fe 100644
--- a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-STOP-STATUS_before/chat_ui.py
+++ b/compact_v5/compact_v5/ui/chat_ui.py
@@ -284,6 +284,7 @@ class V4WidgetChatUI(WidgetChatUI):
         self._run_lock = threading.Lock()
         self._render_generation = 0
         self._live_assistant_index = None
+        self._ui_running = False
         self._build()
 
     @staticmethod
@@ -365,7 +366,13 @@ class V4WidgetChatUI(WidgetChatUI):
 
         self._input = widgets.Textarea(placeholder="Type your message...", layout=widgets.Layout(width="100%", height="80px"))
         self._send_btn = widgets.Button(description="Send", button_style="primary", icon="paper-plane")
-        self._stop_btn = widgets.Button(description="Stop", button_style="danger", icon="stop", layout=widgets.Layout(display="none"))
+        self._stop_btn = widgets.Button(
+            description="Stop",
+            button_style="danger",
+            icon="stop",
+            tooltip="Cooperative stop: request halt, then finish the current Bedrock/tool/subagent call.",
+            layout=widgets.Layout(display="none"),
+        )
         self._clear_btn = widgets.Button(description="Clear", button_style="warning", icon="trash")
         self._compact_btn = widgets.Button(description="Compact", button_style="", icon="compress")
         self._clean_btn = widgets.Button(
@@ -876,7 +883,18 @@ class V4WidgetChatUI(WidgetChatUI):
         )
         subagent_count = len(stats.get("subagent_cost_usd", {}) or {})
         self._render_todos()
-        self._status_html.value = "<span style='color:#4caf50'><b>* Ready</b></span>"
+        if self._ui_running and bool(getattr(self.agent, "_stop_requested", False)):
+            self._status_html.value = (
+                "<span style='color:#ff9800'><b>* Stop requested</b> "
+                "finishing current Bedrock/tool/subagent call</span>"
+            )
+        elif self._ui_running:
+            self._status_html.value = (
+                "<span style='color:#ff9800'><b>* Running</b> "
+                "(Stop is cooperative: current Bedrock/tool/subagent call will finish)</span>"
+            )
+        else:
+            self._status_html.value = "<span style='color:#4caf50'><b>* Ready</b></span>"
         self._tokens_html.value = (
             "<div style='font-size:11px;color:gray;line-height:1.5;'>"
             "<div style='display:flex;flex-wrap:wrap;gap:4px 18px;align-items:center;'>"
@@ -1125,7 +1143,11 @@ class V4WidgetChatUI(WidgetChatUI):
         self._append_message("user", msg)
         self._stop_btn.layout.display = ""
         self._send_btn.disabled = True
-        self._status_html.value = "<span style='color:#ff9800'><b>* Running</b></span>"
+        self._ui_running = True
+        self._status_html.value = (
+            "<span style='color:#ff9800'><b>* Running</b> "
+            "(Stop is cooperative: current Bedrock/tool/subagent call will finish)</span>"
+        )
 
         def _run() -> None:
             with self._run_lock:
@@ -1188,13 +1210,21 @@ class V4WidgetChatUI(WidgetChatUI):
         finally:
             self._stop_btn.layout.display = "none"
             self._send_btn.disabled = False
+            self._ui_running = False
             self.budget_widget.update()
             self.thinking_widget.refresh()
             self._render_status()
 
     def _on_stop(self, _btn) -> None:
         self.agent.stop()
-        self._append_message("system", "[stop requested]")
+        self._status_html.value = (
+            "<span style='color:#ff9800'><b>* Stop requested</b> "
+            "finishing current Bedrock/tool/subagent call</span>"
+        )
+        self._append_message(
+            "system",
+            "[stop requested] Finishing the current Bedrock/tool/subagent call; the agent will halt at the next cooperative checkpoint.",
+        )
         self._render_status()
 
     def _on_clear(self, _btn) -> None:

```

