# Claude CLI Review: UI-LIVE-STREAM

Repo: d:/Github/sagemaker-coding-agent
Active ship tree: compact_v5/compact_v5/
Scope: v5.0.2 UI live-supervisor upgrade, UI observability only.

Review this block diff only. Questions you must answer:
- Does this block preserve v5 architecture?
- Any code drift from the UI-only scope?
- Any regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim guard, subagent receipts, or cost/cache accounting?
- Are tests/checks sufficient?
- Verdict: APPROVE / REQUEST_CHANGES

Context:
- The active ship tree is untracked in this worktree, so the saved patch below is from git diff --no-index between a pre-block snapshot and the active file.
- This block should only make output_fn render live during agent.run() and keep existing per-turn metadata.

## Diff

```diff
diff --git "a/compact_v5_test_evidence\\final_results\\ui_live_supervisor_reviews\\_snapshots\\UI-LIVE-STREAM_before_chat_ui.py" b/compact_v5/compact_v5/ui/chat_ui.py
index d1482ea..6ee4174 100644
--- "a/compact_v5_test_evidence\\final_results\\ui_live_supervisor_reviews\\_snapshots\\UI-LIVE-STREAM_before_chat_ui.py"
+++ b/compact_v5/compact_v5/ui/chat_ui.py
@@ -282,6 +282,7 @@ class V4WidgetChatUI(WidgetChatUI):
         self._run_thread = None
         self._run_lock = threading.Lock()
         self._render_generation = 0
+        self._live_assistant_index = None
         self._build()
 
     @staticmethod
@@ -921,9 +922,40 @@ class V4WidgetChatUI(WidgetChatUI):
             "reasoning_state": f"Thinking {thinking_state} (budget {thinking_budget})",
         }
 
-    def _append_message(self, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
+    def _append_message(self, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> int:
         self._messages.append((role, content, datetime.now().strftime("%H:%M:%S"), meta or {}))
         self._render_chat()
+        return len(self._messages) - 1
+
+    def _set_message_meta(self, index: Optional[int], meta: Dict[str, Any]) -> None:
+        if index is None or index < 0 or index >= len(self._messages):
+            return
+        message = self._messages[index]
+        if len(message) == 4:
+            role, text, ts, old_meta = message
+        else:
+            role, text, ts = message
+            old_meta = {}
+        merged = dict(old_meta or {})
+        merged.update(meta or {})
+        self._messages[index] = (role, text, ts, merged)
+        self._render_chat()
+
+    def _live_output_router(self, text: Any, streamed: list[str]) -> Optional[int]:
+        """Render engine output immediately while preserving final turn metadata."""
+        chunk = str(text)
+        streamed.append(chunk)
+        stripped = chunk.strip()
+        if not stripped:
+            return None
+        if stripped.startswith("["):
+            self._append_message("system", stripped)
+            self._render_status()
+            return None
+        index = self._append_message("assistant", chunk)
+        self._live_assistant_index = index
+        self._render_status()
+        return index
 
     def _dispatch_ui_command(self, command: str) -> None:
         try:
@@ -972,18 +1004,22 @@ class V4WidgetChatUI(WidgetChatUI):
                 except Exception as cmd_exc:
                     logging.warning(f"[chat-ui] slash-command dispatch error: {cmd_exc}")
             streamed = []
+            self._live_assistant_index = None
             before_stats = self._stats_snapshot()
-            result = self.agent.run(msg, output_fn=lambda s: streamed.append(str(s)))
+            result = self.agent.run(
+                msg,
+                output_fn=lambda s: self._live_output_router(s, streamed),
+            )
             after_stats = self._stats_snapshot()
             turn_meta = self._turn_meta_from_stats(before_stats, after_stats, result)
-            ops = [s.strip() for s in streamed if str(s).strip().startswith("[")]
-            if ops:
-                self._append_message("system", "\n".join(ops[-30:]))
-            self._append_message(
-                "assistant",
-                result.text or "\n".join(streamed) or f"stop_reason: {result.stop_reason}",
-                meta=turn_meta,
-            )
+            if self._live_assistant_index is not None and result.text:
+                self._set_message_meta(self._live_assistant_index, turn_meta)
+            else:
+                self._append_message(
+                    "assistant",
+                    result.text or "\n".join(streamed) or f"stop_reason: {result.stop_reason}",
+                    meta=turn_meta,
+                )
         except Exception as exc:  # noqa: BLE001
             logging.exception("[chat-ui] agent.run() raised")
             self._append_message("system", f"[chat-ui] error: {type(exc).__name__}: {exc}")

```

