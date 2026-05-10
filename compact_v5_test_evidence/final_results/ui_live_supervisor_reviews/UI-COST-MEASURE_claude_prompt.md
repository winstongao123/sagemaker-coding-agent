# Claude CLI Review: UI-COST-MEASURE

Repo: d:/Github/sagemaker-coding-agent
Active ship tree: compact_v5/compact_v5/
Scope: v5.0.2 UI live-supervisor upgrade, UI observability only.

Review this block diff only. Questions you must answer:
- Does this block preserve v5 architecture?
- Any code drift from the UI-only scope?
- Any regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim guard, subagent receipts, or cost/cache accounting?
- Are tests/checks sufficient?
- Verdict: APPROVE / REQUEST_CHANGES

Context: this block adds display-only cost driver measurement text and deliberately avoids changing model/prompt/cache/compaction/thinking defaults.

## Diff
```diff
diff --git a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-COST-MEASURE_before/chat_ui.py b/compact_v5/compact_v5/ui/chat_ui.py
index c03d0fe..f3b595d 100644
--- a/compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/_snapshots/UI-COST-MEASURE_before/chat_ui.py
+++ b/compact_v5/compact_v5/ui/chat_ui.py
@@ -903,6 +903,7 @@ class V4WidgetChatUI(WidgetChatUI):
             f"<span>Cost ${cost:.4f} | Last ${last_cost:.4f} | Without cache ${original_cost:.4f}</span>"
             f"<span>{pricing} | {cache_pct:.0f}% cached</span>"
             "</div>"
+            f"<div style='color:#8aa0b8;margin-top:4px;'>{self._escape(self._cost_driver_line(stats, cache_pct))}</div>"
             "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:8px 14px;margin-top:6px;'>"
             "<div>"
             f"<div style='color:#2ca02c;'>Context: {context_pct:.1f}% ({context_tokens:,} / {context_max:,})</div>"
@@ -977,6 +978,26 @@ class V4WidgetChatUI(WidgetChatUI):
         except Exception:
             return {"_cache_savings_usd": 0.0}
 
+    def _cost_driver_line(self, stats: Dict[str, Any], cache_pct: float) -> str:
+        """Display-only measurement hints; never changes model/cache/compaction."""
+        input_tokens = int(stats.get("session_input", 0) or 0)
+        output_tokens = int(stats.get("session_output", 0) or 0)
+        calls = int(stats.get("api_calls", 0) or 0)
+        thinking_state = "ON" if bool(getattr(self.agent, "thinking_enabled", False)) else "OFF"
+        if calls <= 0:
+            return (
+                "Cost drivers: no calls yet; measure calls, output tokens, thinking state, "
+                "cache R/W, subagent attribution, and compaction before optimizing."
+            )
+        dominant = "output" if output_tokens >= input_tokens else "input"
+        avg_out = output_tokens / max(1, calls)
+        return (
+            f"Cost drivers to measure first: {dominant} tokens dominate "
+            f"({input_tokens:,} in / {output_tokens:,} out), {calls:,} calls, "
+            f"avg {avg_out:,.0f} out/call, Thinking {thinking_state}, "
+            f"{cache_pct:.0f}% cached, subagent attribution below."
+        )
+
     def _turn_meta_from_stats(self, before: Dict[str, Any], after: Dict[str, Any], result: Any) -> Dict[str, Any]:
         def _num(key: str) -> float:
             return float(after.get(key, 0) or 0) - float(before.get(key, 0) or 0)

```

