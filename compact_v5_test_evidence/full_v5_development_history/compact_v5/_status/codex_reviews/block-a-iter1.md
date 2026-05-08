OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.3-codex
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019debe5-d275-7e72-ac39-b0edebd9cfcd
--------
user
Review Block A of v5.0.1: Compactor + auto-compact circuit breaker + cache_edits + B-2/B+5 remaps.

Block A ships:
- core/compactor.py: Compactor (v4 port lines 186-635) + AutoCompactCircuitBreaker (Hermes pattern) + apply_cache_control_to_blocks (Bedrock equiv of Runnable cache_edits) + count_tokens_via_haiku_fallback (B-2) + advisor agent_kind attribution (B+5)

Read these 3 files:
- compact_v5/MAIN/agent/core/compactor.py (full module ~430 LOC)
- compact_v5/MAIN/agent/tests/integration/test_block_a.py (21 lock tests)
- /tmp/v4_compactor_section.txt (v4 source for parity check, 449 LOC)

3-axis review:
AXIS A: errors / regressions / security (estimate_tokens delegation correctness; prune logic preserves PROTECTED_TOOLS invariant; create_llm_summary PTL retry; circuit-breaker thread safety; advisor attribution doesn't double-count). Verdict: PASS / CHANGES_REQUESTED / BLOCKER.
AXIS B: v5 fit (long-session resilience; constraint #13 Bedrock caching parity for sub-agents). Verdict: FAITHFUL / FAITHFUL-WITH-JUSTIFIED-ADAPTATION / DRIFTED.
AXIS C: covers Compactor + auto-compact + cache_edits + B-2 + B+5? Anything UNDECLARED_PATTERN?

Tests: 571 pass + 5 skip (was 550; +21 net new).

FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.

codex
Reviewing Block A now across the three files you listed, focusing on parity, invariants, and regression/security risk. I’ll first read the module and tests with line numbers, then cross-check against the v4 section for behavioral drift.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content -Path '"'/tmp/v4_compactor_section.txt' | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content -Path '"'compact_v5/MAIN/agent/core/compactor.py' | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content -Path '"'compact_v5/MAIN/agent/tests/integration/test_block_a.py' | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 531ms:
   1: """Block A â€” Compactor + auto-compact circuit breaker + Runnable cache_edits.
   2: 
   3: v5 port of v4's `Compactor` class (compact_v4/MAIN/agent/sagemaker_agent.py
   4: lines 186-635, ~449 LOC). Adapted for v5's nested-package layout. Plus:
   5:   - Auto-compact circuit breaker (Hermes-style cooldown)
   6:   - Runnable cache_edits adaptation (cache_control on prompt sections â€”
   7:     Bedrock equivalent of the Anthropic-direct cache_edits param)
   8:   - B-2 countTokensViaHaikuFallback (deferred from Block B per ADR-021)
   9:   - B+5 recursive advisor sub-cost accounting (deferred from Block B+
  10:     per ADR-022 â€” auxiliary compaction-summary model)
  11: 
  12: The Compactor is the load-bearing piece for context-window management.
  13: At 80% of max context, `should_compact()` returns True; the chat loop
  14: calls `Compactor.run(messages, client)` which prunes oversized tool
  15: results, asks Bedrock for an LLM summary, and replaces old messages
  16: with the summary + last N messages.
  17: 
  18: PORT_LOG: see #066-#070.
  19: """
  20: from __future__ import annotations
  21: 
  22: import copy
  23: import logging
  24: import threading
  25: import time
  26: from dataclasses import dataclass, field
  27: from typing import Any, Callable, Dict, List, Optional, Tuple
  28: 
  29: 
  30: # ============================================================
  31: # CompactionResult
  32: # ============================================================
  33: 
  34: @dataclass
  35: class CompactionResult:
  36:     """Outcome of a compact() call."""
  37: 
  38:     success: bool
  39:     summary: str = ""
  40:     messages_after: List[Dict[str, Any]] = field(default_factory=list)
  41:     tokens_before: int = 0
  42:     tokens_after: int = 0
  43:     error: str = ""
  44: 
  45: 
  46: # ============================================================
  47: # AutoCompactCircuitBreaker (Hermes-style cooldown)
  48: # ============================================================
  49: 
  50: class AutoCompactCircuitBreaker:
  51:     """Prevents auto-compact runaway by enforcing a cooldown window.
  52: 
  53:     Pattern: when auto-compact fires, mark the timestamp. If
  54:     `should_attempt()` is called again within `cooldown_seconds`, return
  55:     False â€” caller must continue without re-compacting. Hermes
  56:     run_agent.py uses this to prevent compact-after-compact loops where
  57:     a freshly-compacted context still trips the 80% trigger because
  58:     the summary itself is large.
  59: 
  60:     Per Wave-5-DEEP H5 (auto-compact circuit breaker; A28 cache-invariant).
  61:     """
  62: 
  63:     def __init__(self, cooldown_seconds: int = 30, max_per_session: int = 10):
  64:         self.cooldown_seconds = max(1, int(cooldown_seconds))
  65:         self.max_per_session = max(1, int(max_per_session))
  66:         self._lock = threading.Lock()
  67:         self._last_attempt: float = 0.0
  68:         self._session_count = 0
  69: 
  70:     def should_attempt(self) -> Tuple[bool, str]:
  71:         """True iff a compact attempt is allowed right now.
  72: 
  73:         Returns (allowed, reason). When False, the reason explains why
  74:         (session cap hit / cooldown active) so the caller can surface
  75:         a clear log message. Session cap checked FIRST â€” once exhausted,
  76:         no further attempts make sense regardless of cooldown.
  77:         """
  78:         with self._lock:
  79:             if self._session_count >= self.max_per_session:
  80:                 return False, (
  81:                     f"auto-compact session cap reached "
  82:                     f"({self._session_count}/{self.max_per_session})"
  83:                 )
  84:             now = time.time()
  85:             since = now - self._last_attempt
  86:             if self._last_attempt > 0 and since < self.cooldown_seconds:
  87:                 return False, (
  88:                     f"auto-compact cooldown active "
  89:                     f"({since:.0f}s elapsed, "
  90:                     f"{self.cooldown_seconds}s required)"
  91:                 )
  92:             return True, ""
  93: 
  94:     def record_attempt(self) -> None:
  95:         """Mark a compact attempt â€” caller calls this after a successful
  96:         OR failed compact so cooldown applies either way (a failed
  97:         compact still consumed time + tokens)."""
  98:         with self._lock:
  99:             self._last_attempt = time.time()
 100:             self._session_count += 1
 101: 
 102:     def reset(self) -> None:
 103:         with self._lock:
 104:             self._last_attempt = 0.0
 105:             self._session_count = 0
 106: 
 107: 
 108: # ============================================================
 109: # Compactor (v4 port)
 110: # ============================================================
 111: 
 112: class Compactor:
 113:     """Smart context compaction: prune oversized tool results, then
 114:     LLM-summarize old messages, replace with summary + last N.
 115: 
 116:     Verbatim port of v4 sagemaker_agent.py:186-635 with adaptations:
 117:     - estimate_tokens delegates to runtime/tokens.estimate_message_tokens
 118:       (drops tiktoken dependency for SageMaker-native deployment).
 119:     - create_llm_summary uses v5 BedrockClient.chat() shape.
 120:     - Auxiliary-model routing (v4.9.4 compaction_model) preserved with
 121:       per-agent attribution via TokenTracker.add(agent_kind="advisor")
 122:       â€” this is the B+5 recursive advisor sub-cost accounting that
 123:       ADR-022 deferred from Block B+ to Block A.
 124:     """
 125: 
 126:     PRUNE_PROTECT_TOKENS = 40_000
 127:     PRUNE_MIN_SAVINGS = 10_000
 128:     SUMMARY_TRIGGER_PERCENT = 0.80
 129:     KEEP_LAST_MESSAGES = 3
 130:     MAX_PTL_RETRIES = 3
 131: 
 132:     SUMMARY_TOOL_RESULT_THRESHOLD = 8_000
 133:     SUMMARY_TOOL_RESULT_HEAD = 2_000
 134:     SUMMARY_TOOL_RESULT_TAIL = 1_000
 135: 
 136:     PROTECTED_TOOLS = {"todo_write", "todo_read", "semantic_search"}
 137: 
 138:     FIXED_OVERHEAD_TOKENS = 6_000
 139: 
 140:     # Aux client cache (per-process); built lazily.
 141:     _aux_client_cache: Dict[str, Any] = {}
 142: 
 143:     # --------------------------------------------------------
 144:     # Token estimation
 145:     # --------------------------------------------------------
 146: 
 147:     @classmethod
 148:     def estimate_tokens(cls, text_or_messages: Any) -> int:
 149:         """Estimate token count for a string OR list of messages.
 150: 
 151:         Delegates to `runtime.tokens.estimate_message_tokens` for strings
 152:         and `rough_token_count_for_message` for message dicts.
 153:         """
 154:         from runtime.tokens import (
 155:             estimate_message_tokens,
 156:             rough_token_count_for_message,
 157:         )
 158:         if isinstance(text_or_messages, str):
 159:             return estimate_message_tokens(text_or_messages)
 160:         if isinstance(text_or_messages, list):
 161:             return sum(rough_token_count_for_message(m) for m in text_or_messages)
 162:         if isinstance(text_or_messages, dict):
 163:             return rough_token_count_for_message(text_or_messages)
 164:         return 0
 165: 
 166:     # --------------------------------------------------------
 167:     # Prune oversized tool results
 168:     # --------------------------------------------------------
 169: 
 170:     @classmethod
 171:     def prune_tool_outputs(
 172:         cls,
 173:         messages: List[Dict[str, Any]],
 174:         max_context: int,
 175:     ) -> Tuple[List[Dict[str, Any]], int]:
 176:         """Truncate tool results that are far past PRUNE_PROTECT_TOKENS.
 177: 
 178:         Keeps the head + tail of each oversized result so the model
 179:         retains some signal but the bulk is removed. Returns
 180:         (pruned_messages, tokens_saved).
 181:         """
 182:         if not messages:
 183:             return messages, 0
 184: 
 185:         pruned = copy.deepcopy(messages)
 186:         tool_name_map: Dict[str, str] = {}
 187:         # Build tool_use_id â†’ tool_name map so we can skip protected tools.
 188:         for msg in pruned:
 189:             content = msg.get("content")
 190:             if isinstance(content, list):
 191:                 for item in content:
 192:                     if isinstance(item, dict) and item.get("type") == "tool_use":
 193:                         tool_name_map[item.get("id", "")] = item.get("name", "")
 194: 
 195:         # Walk most-recent â†’ oldest; protect the last PROTECT_TOKENS worth.
 196:         running_tokens = 0
 197:         tokens_saved = 0
 198:         for msg in reversed(pruned):
 199:             content = msg.get("content")
 200:             if not isinstance(content, list):
 201:                 running_tokens += cls.estimate_tokens(msg)
 202:                 continue
 203:             for block in content:
 204:                 if not (isinstance(block, dict) and block.get("type") == "tool_result"):
 205:                     continue
 206:                 tool_name = tool_name_map.get(block.get("tool_use_id", ""), "")
 207:                 if tool_name in cls.PROTECTED_TOOLS:
 208:                     continue
 209:                 inner = block.get("content")
 210:                 if isinstance(inner, str):
 211:                     block_tokens = cls.estimate_tokens(inner)
 212:                     running_tokens += block_tokens
 213:                     if running_tokens > cls.PRUNE_PROTECT_TOKENS \
 214:                        and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
 215:                         head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
 216:                         tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
 217:                         new_text = (
 218:                             f"{head}\n... [pruned "
 219:                             f"{len(inner) - len(head) - len(tail):,} chars] ...\n{tail}"
 220:                         )
 221:                         block["content"] = new_text
 222:                         tokens_saved += cls.estimate_tokens(inner) - cls.estimate_tokens(new_text)
 223:                 elif isinstance(inner, list):
 224:                     for sub in inner:
 225:                         if isinstance(sub, dict) and sub.get("type") == "text":
 226:                             txt = sub.get("text", "")
 227:                             running_tokens += cls.estimate_tokens(txt)
 228:                             if running_tokens > cls.PRUNE_PROTECT_TOKENS \
 229:                                and len(txt) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
 230:                                 head = txt[: cls.SUMMARY_TOOL_RESULT_HEAD]
 231:                                 tail = txt[-cls.SUMMARY_TOOL_RESULT_TAIL :]
 232:                                 new_text = (
 233:                                     f"{head}\n... [pruned "
 234:                                     f"{len(txt) - len(head) - len(tail):,} chars] ...\n{tail}"
 235:                                 )
 236:                                 sub["text"] = new_text
 237:                                 tokens_saved += cls.estimate_tokens(txt) - cls.estimate_tokens(new_text)
 238:         return pruned, tokens_saved
 239: 
 240:     # --------------------------------------------------------
 241:     # Should compact?
 242:     # --------------------------------------------------------
 243: 
 244:     @classmethod
 245:     def should_compact(cls, messages: List[Dict[str, Any]], max_tokens: int) -> bool:
 246:         """True iff token estimate > 80% of max_tokens (with overhead)."""
 247:         try:
 248:             from runtime.tokens import TOKENS
 249:             overhead = TOKENS.final_context_tokens_from_last_response()
 250:             if overhead == 0:
 251:                 overhead = cls.FIXED_OVERHEAD_TOKENS
 252:         except Exception:
 253:             overhead = cls.FIXED_OVERHEAD_TOKENS
 254:         total = cls.estimate_tokens(messages) + overhead
 255:         return total > max_tokens * cls.SUMMARY_TRIGGER_PERCENT
 256: 
 257:     # --------------------------------------------------------
 258:     # Auxiliary-model routing (B+5 â€” recursive advisor sub-cost)
 259:     # --------------------------------------------------------
 260: 
 261:     @classmethod
 262:     def _summary_client(cls, main_client) -> Any:
 263:         """Return the client to use for summary generation.
 264: 
 265:         Per v4.9.4: when CONFIG.compaction_model is set, build a
 266:         Bedrock client for that cheaper auxiliary model so summaries
 267:         don't pay main-model rates. Per ADR-022 / B+5: TOKENS.add()
 268:         with `agent_kind="advisor"` so the auxiliary cost is attributed
 269:         separately in /cost output.
 270:         """
 271:         from runtime.config import CONFIG
 272:         aux_model = (getattr(CONFIG, "compaction_model", "") or "").strip()
 273:         if not aux_model or aux_model == getattr(main_client, "model_id", ""):
 274:             return main_client
 275:         cached = cls._aux_client_cache.get(aux_model)
 276:         if cached is not None:
 277:             return cached
 278:         try:
 279:             from runtime.bedrock_client import BedrockClient
 280:             aux = BedrockClient(
 281:                 aux_model,
 282:                 getattr(main_client, "region", "ap-southeast-2"),
 283:                 getattr(main_client, "mock_mode", False),
 284:             )
 285:             cls._aux_client_cache[aux_model] = aux
 286:             logging.info(f"[COMPACT] Using auxiliary compaction model: {aux_model}")
 287:             return aux
 288:         except Exception as exc:  # noqa: BLE001
 289:             logging.warning(
 290:                 f"[COMPACT] Auxiliary model '{aux_model}' init failed; "
 291:                 f"using main client: {exc}"
 292:             )
 293:             return main_client
 294: 
 295:     # --------------------------------------------------------
 296:     # LLM summary
 297:     # --------------------------------------------------------
 298: 
 299:     @classmethod
 300:     def create_llm_summary(
 301:         cls,
 302:         client: Any,
 303:         messages: List[Dict[str, Any]],
 304:     ) -> Optional[str]:
 305:         """Ask Bedrock to summarize the conversation. Returns None on
 306:         failure. Per v4 verbatim with v5 adaptations:
 307:         - Pre-prune oversized tool results for the summary input.
 308:         - Optionally route through CONFIG.compaction_model (advisor).
 309:         - Attribute advisor tokens via TOKENS.add(agent_kind='advisor').
 310:         """
 311:         from runtime.tokens import TOKENS
 312: 
 313:         pruned_messages = cls._prune_tool_results_for_summary(messages)
 314:         summary_client = cls._summary_client(client)
 315: 
 316:         SUMMARY_SYSTEM_PROMPT = (
 317:             "You are summarizing a coding conversation. You have ZERO tools "
 318:             "available â€” do NOT attempt any tool calls. Be concise but "
 319:             "preserve:\n"
 320:             "1. Current task and goal\n"
 321:             "2. Key files modified or read\n"
 322:             "3. Important decisions made\n"
 323:             "4. Where we left off\n"
 324:             "5. What needs to happen next\n"
 325:             "6. Resolved questions\n"
 326:             "7. Pending questions"
 327:         )
 328: 
 329:         summary_input = list(pruned_messages)
 330:         # Bedrock requires user/assistant alternation.
 331:         if summary_input and summary_input[-1].get("role") == "user":
 332:             summary_input.append({
 333:                 "role": "assistant",
 334:                 "content": "[Preparing summary...]",
 335:             })
 336:         summary_input.append({
 337:             "role": "user",
 338:             "content": (
 339:                 "Summarize the conversation above per the rubric. Be concise."
 340:             ),
 341:         })
 342: 
 343:         attempts = 0
 344:         while attempts <= cls.MAX_PTL_RETRIES:
 345:             try:
 346:                 response = summary_client.chat(
 347:                     messages=summary_input,
 348:                     system=SUMMARY_SYSTEM_PROMPT,
 349:                     tools=None,
 350:                     max_tokens=2000,
 351:                     temperature=0.0,
 352:                 )
 353:                 if response and response.usage:
 354:                     # B+5 (ADR-022 remap): attribute advisor cost separately.
 355:                     agent_kind = (
 356:                         "advisor"
 357:                         if summary_client is not client
 358:                         else "parent"
 359:                     )
 360:                     TOKENS.add(
 361:                         response.usage,
 362:                         model_id=getattr(summary_client, "model_id", None),
 363:                         agent_kind=agent_kind,
 364:                     )
 365:                 if response and response.text:
 366:                     return response.text
 367:                 return None
 368:             except Exception as exc:  # noqa: BLE001
 369:                 err = str(exc).lower()
 370:                 is_ptl = ("prompt" in err and "long" in err) \
 371:                     or "too many tokens" in err
 372:                 if not is_ptl:
 373:                     logging.warning(f"[COMPACT] LLM summary failed: {exc}")
 374:                     return None
 375:                 attempts += 1
 376:                 summary_input = cls._truncate_head_for_ptl_retry(summary_input)
 377:                 if not summary_input:
 378:                     logging.warning("[COMPACT] PTL retries exhausted")
 379:                     return None
 380:         return None
 381: 
 382:     @classmethod
 383:     def _prune_tool_results_for_summary(
 384:         cls,
 385:         messages: List[Dict[str, Any]],
 386:     ) -> List[Dict[str, Any]]:
 387:         """Cheap pre-LLM pass: drop oversized tool_result bodies."""
 388:         out: List[Dict[str, Any]] = []
 389:         for msg in messages:
 390:             content = msg.get("content")
 391:             if not isinstance(content, list):
 392:                 out.append(msg)
 393:                 continue
 394:             new_blocks: List[Any] = []
 395:             mutated = False
 396:             for block in content:
 397:                 if not (isinstance(block, dict) and block.get("type") == "tool_result"):
 398:                     new_blocks.append(block)
 399:                     continue
 400:                 inner = block.get("content")
 401:                 if isinstance(inner, str) and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
 402:                     head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
 403:                     tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
 404:                     new_block = dict(block)
 405:                     new_block["content"] = (
 406:                         f"{head}\n... [pruned for summary] ...\n{tail}"
 407:                     )
 408:                     new_blocks.append(new_block)
 409:                     mutated = True
 410:                 else:
 411:                     new_blocks.append(block)
 412:             if mutated:
 413:                 new_msg = dict(msg)
 414:                 new_msg["content"] = new_blocks
 415:                 out.append(new_msg)
 416:             else:
 417:                 out.append(msg)
 418:         return out
 419: 
 420:     @classmethod
 421:     def _truncate_head_for_ptl_retry(
 422:         cls,
 423:         messages: List[Dict[str, Any]],
 424:     ) -> Optional[List[Dict[str, Any]]]:
 425:         """Drop the first 25% of messages so PTL retry has a smaller
 426:         input. Returns None when input is already minimal."""
 427:         if len(messages) < 4:
 428:             return None
 429:         drop_n = max(1, len(messages) // 4)
 430:         return messages[drop_n:]
 431: 
 432:     # --------------------------------------------------------
 433:     # Compact: replace old messages with summary
 434:     # --------------------------------------------------------
 435: 
 436:     @classmethod
 437:     def compact(
 438:         cls,
 439:         messages: List[Dict[str, Any]],
 440:         summary: str,
 441:     ) -> List[Dict[str, Any]]:
 442:         """Replace old messages with a summary + last N messages."""
 443:         if not summary:
 444:             return messages
 445:         keep_last = cls.KEEP_LAST_MESSAGES
 446:         recent = messages[-keep_last:] if len(messages) > keep_last else []
 447:         summary_msg = {
 448:             "role": "user",
 449:             "content": (
 450:                 f"[CONVERSATION SUMMARY]\n{summary}\n"
 451:                 "[END SUMMARY â€” Continuing from here]"
 452:             ),
 453:         }
 454:         return [summary_msg] + recent
 455: 
 456:     @classmethod
 457:     def run(
 458:         cls,
 459:         client: Any,
 460:         messages: List[Dict[str, Any]],
 461:         max_tokens: int = 200_000,
 462:     ) -> CompactionResult:
 463:         """End-to-end: prune â†’ summarize â†’ compact. Single entry point."""
 464:         before_tokens = cls.estimate_tokens(messages)
 465:         if not cls.should_compact(messages, max_tokens):
 466:             return CompactionResult(
 467:                 success=False,
 468:                 error="compact not needed (under 80% trigger)",
 469:                 tokens_before=before_tokens,
 470:                 tokens_after=before_tokens,
 471:                 messages_after=list(messages),
 472:             )
 473:         pruned, _saved = cls.prune_tool_outputs(messages, max_tokens)
 474:         summary = cls.create_llm_summary(client, pruned)
 475:         if not summary:
 476:             return CompactionResult(
 477:                 success=False,
 478:                 error="LLM summary returned empty",
 479:                 tokens_before=before_tokens,
 480:                 tokens_after=cls.estimate_tokens(pruned),
 481:                 messages_after=pruned,
 482:             )
 483:         new_messages = cls.compact(pruned, summary)
 484:         after_tokens = cls.estimate_tokens(new_messages)
 485:         return CompactionResult(
 486:             success=True,
 487:             summary=summary,
 488:             messages_after=new_messages,
 489:             tokens_before=before_tokens,
 490:             tokens_after=after_tokens,
 491:         )
 492: 
 493: 
 494: # ============================================================
 495: # Runnable cache_edits â€” Bedrock cache_control adaptation
 496: # ============================================================
 497: 
 498: def apply_cache_control_to_blocks(
 499:     blocks: List[Dict[str, Any]],
 500:     cache_break_at: int = -1,
 501: ) -> List[Dict[str, Any]]:
 502:     """Apply Bedrock-style `cache_control` to message blocks.
 503: 
 504:     Bedrock equivalent of Anthropic-direct `cache_edits` (Runnable's
 505:     name): mark the block at `cache_break_at` (default -1 = last) with
 506:     `{"cache_control": {"type": "ephemeral"}}` so prefix-replay works
 507:     on subsequent turns. Block A's compaction output is the natural
 508:     place to set this â€” the summary block becomes the new cache prefix.
 509: 
 510:     Per Runnable cache_edits.ts (reference) + Hermes A28 cache-invariant
 511:     (no mid-turn cache flips).
 512:     """
 513:     if not blocks:
 514:         return blocks
 515:     if cache_break_at == -1:
 516:         cache_break_at = len(blocks) - 1
 517:     if cache_break_at < 0 or cache_break_at >= len(blocks):
 518:         return blocks
 519:     out = list(blocks)
 520:     target = dict(out[cache_break_at])
 521:     target["cache_control"] = {"type": "ephemeral"}
 522:     out[cache_break_at] = target
 523:     return out
 524: 
 525: 
 526: # ============================================================
 527: # B-2 â€” countTokensViaHaikuFallback (deferred from Block B per ADR-021)
 528: # ============================================================
 529: 
 530: def count_tokens_via_haiku_fallback(
 531:     messages: List[Dict[str, Any]],
 532:     main_client: Any,
 533: ) -> Optional[int]:
 534:     """Fallback token counter when BedrockClient.count_tokens is
 535:     unavailable: use Haiku (cheaper) to count tokens via a
 536:     1-token-budget chat call. Returns the input_tokens reported.
 537: 
 538:     Per Runnable services/tokenEstimation.ts:251-325 (R4 #42).
 539:     Block A consumer: uses this when Compactor needs an accurate
 540:     count and the live client doesn't expose count_tokens (older boto3).
 541:     """
 542:     if main_client is None:
 543:         return None
 544:     if getattr(main_client, "mock_mode", False):
 545:         # In mock mode, use the rough estimator from runtime/tokens.
 546:         from runtime.tokens import rough_token_count_for_message
 547:         return sum(rough_token_count_for_message(m) for m in messages)
 548:     try:
 549:         from runtime.bedrock_client import BedrockClient
 550:         haiku_client = BedrockClient(
 551:             "anthropic.claude-haiku-4-5-20251001-v1:0",
 552:             getattr(main_client, "region", "ap-southeast-2"),
 553:             mock_mode=False,
 554:         )
 555:         # Send a max_tokens=1 call so we get the input usage cheaply.
 556:         response = haiku_client.chat(
 557:             messages=messages,
 558:             system="Token-count fallback. Reply with a single dot.",
 559:             tools=None,
 560:             max_tokens=1,
 561:             temperature=0.0,
 562:         )
 563:         if response and response.usage:
 564:             return int(response.usage.get("input_tokens", 0))
 565:     except Exception as exc:  # noqa: BLE001
 566:         logging.warning(f"haiku-fallback token count failed: {exc}")
 567:     return None
 568: 
 569: 
 570: # ============================================================
 571: # Module-level singleton circuit breaker
 572: # ============================================================
 573: 
 574: AUTO_COMPACT = AutoCompactCircuitBreaker()
 575: 
 576: 
 577: __all__ = [
 578:     "Compactor",
 579:     "CompactionResult",
 580:     "AutoCompactCircuitBreaker",
 581:     "AUTO_COMPACT",
 582:     "apply_cache_control_to_blocks",
 583:     "count_tokens_via_haiku_fallback",
 584: ]

 succeeded in 577ms:
   1: """Block A â€” Compactor + auto-compact circuit breaker + cache_edits.
   2: 
   3: Tests cover:
   4:   - Compactor.estimate_tokens delegates to runtime/tokens helpers.
   5:   - Compactor.prune_tool_outputs head/tail truncation.
   6:   - Compactor.should_compact 80% trigger.
   7:   - Compactor.compact replaces old with summary + last N.
   8:   - Compactor.create_llm_summary calls client.chat with summary prompt.
   9:   - Compactor.run end-to-end (mock client returns canned summary).
  10:   - AutoCompactCircuitBreaker cooldown + session cap.
  11:   - apply_cache_control_to_blocks marks last block ephemeral.
  12:   - B-2 count_tokens_via_haiku_fallback (mock mode + real path stub).
  13:   - B+5 advisor sub-cost attribution via TOKENS.add(agent_kind="advisor").
  14: """
  15: from __future__ import annotations
  16: 
  17: import os
  18: import sys
  19: 
  20: import pytest
  21: 
  22: _AGENT_ROOT = os.path.dirname(
  23:     os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  24: )
  25: if _AGENT_ROOT not in sys.path:
  26:     sys.path.insert(0, _AGENT_ROOT)
  27: 
  28: 
  29: # ============================================================
  30: # T1 â€” estimate_tokens
  31: # ============================================================
  32: 
  33: def test_compactor_estimate_tokens_string():
  34:     from core.compactor import Compactor
  35: 
  36:     assert Compactor.estimate_tokens("") == 0
  37:     assert Compactor.estimate_tokens("hello world") > 0
  38: 
  39: 
  40: def test_compactor_estimate_tokens_messages():
  41:     from core.compactor import Compactor
  42: 
  43:     msgs = [
  44:         {"role": "user", "content": "hello"},
  45:         {"role": "assistant", "content": "world"},
  46:     ]
  47:     n = Compactor.estimate_tokens(msgs)
  48:     assert n > 0
  49: 
  50: 
  51: # ============================================================
  52: # T1 â€” should_compact 80% trigger
  53: # ============================================================
  54: 
  55: def test_compactor_should_compact_at_80_percent():
  56:     from core.compactor import Compactor
  57: 
  58:     # Build a message that estimates to ~80,001 tokens (above 80% of 100K).
  59:     big_text = "x" * 240_000  # ~80K tokens at 3 chars/token
  60:     msgs = [{"role": "user", "content": big_text}]
  61:     assert Compactor.should_compact(msgs, max_tokens=100_000)
  62:     # And NOT trigger at 200K max.
  63:     assert not Compactor.should_compact(msgs, max_tokens=400_000)
  64: 
  65: 
  66: def test_compactor_should_not_compact_when_small():
  67:     from core.compactor import Compactor
  68: 
  69:     msgs = [{"role": "user", "content": "tiny"}]
  70:     assert not Compactor.should_compact(msgs, max_tokens=200_000)
  71: 
  72: 
  73: # ============================================================
  74: # T1 â€” prune_tool_outputs
  75: # ============================================================
  76: 
  77: def test_compactor_prune_tool_outputs_truncates_oversized():
  78:     from core.compactor import Compactor
  79: 
  80:     huge = "y" * 30_000  # > SUMMARY_TOOL_RESULT_THRESHOLD (8K)
  81:     # Build > PRUNE_PROTECT_TOKENS so pruning kicks in.
  82:     fillers = [
  83:         {"role": "assistant", "content": [{"type": "text", "text": "x" * 60_000}]}
  84:         for _ in range(3)
  85:     ]
  86:     msgs = fillers + [
  87:         {"role": "user", "content": [{
  88:             "type": "tool_result",
  89:             "tool_use_id": "t1",
  90:             "content": huge,
  91:         }]},
  92:     ]
  93:     pruned, saved = Compactor.prune_tool_outputs(msgs, max_context=200_000)
  94:     assert saved >= 0
  95:     # Bonus: input not mutated.
  96:     assert msgs[-1]["content"][0]["content"] == huge
  97: 
  98: 
  99: def test_compactor_prune_protects_listed_tools():
 100:     from core.compactor import Compactor
 101: 
 102:     huge = "y" * 30_000
 103:     msgs = [
 104:         {"role": "assistant", "content": [{"type": "text", "text": "x" * 70_000}]},
 105:         {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "todo_write", "input": {}}]},
 106:         {"role": "user", "content": [{
 107:             "type": "tool_result",
 108:             "tool_use_id": "t1",
 109:             "content": huge,
 110:         }]},
 111:     ]
 112:     pruned, _ = Compactor.prune_tool_outputs(msgs, max_context=100_000)
 113:     # todo_write is in PROTECTED_TOOLS â€” its result must NOT be truncated.
 114:     assert pruned[-1]["content"][0]["content"] == huge
 115: 
 116: 
 117: # ============================================================
 118: # T1 â€” compact replaces old with summary + last N
 119: # ============================================================
 120: 
 121: def test_compactor_compact_with_summary():
 122:     from core.compactor import Compactor
 123: 
 124:     msgs = [
 125:         {"role": "user", "content": f"msg {i}"}
 126:         for i in range(10)
 127:     ]
 128:     summary = "User asked about X; assistant answered Y."
 129:     result = Compactor.compact(msgs, summary)
 130:     assert len(result) == 1 + Compactor.KEEP_LAST_MESSAGES
 131:     assert summary in result[0]["content"]
 132:     # Last KEEP_LAST_MESSAGES messages preserved.
 133:     for i, kept in enumerate(result[1:]):
 134:         original = msgs[-Compactor.KEEP_LAST_MESSAGES + i]
 135:         assert kept["content"] == original["content"]
 136: 
 137: 
 138: def test_compactor_compact_returns_unchanged_on_empty_summary():
 139:     from core.compactor import Compactor
 140: 
 141:     msgs = [{"role": "user", "content": "x"}]
 142:     assert Compactor.compact(msgs, summary="") == msgs
 143: 
 144: 
 145: # ============================================================
 146: # T2 â€” create_llm_summary calls client.chat
 147: # ============================================================
 148: 
 149: def test_compactor_create_llm_summary_calls_chat(monkeypatch):
 150:     from core.compactor import Compactor
 151:     from runtime.bedrock_client import BedrockClient, Response
 152: 
 153:     client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
 154: 
 155:     captured: dict = {}
 156: 
 157:     def fake_chat(*args, **kwargs):
 158:         captured["call"] = kwargs
 159:         return Response(text="canned summary", usage={"input_tokens": 100, "output_tokens": 50})
 160: 
 161:     monkeypatch.setattr(client, "chat", fake_chat)
 162:     msgs = [{"role": "user", "content": "hello"}]
 163:     summary = Compactor.create_llm_summary(client, msgs)
 164:     assert summary == "canned summary"
 165:     assert "system" in captured["call"]
 166:     assert "summarizing" in captured["call"]["system"].lower()
 167: 
 168: 
 169: def test_compactor_run_end_to_end(monkeypatch):
 170:     """Compactor.run: prune â†’ summarize â†’ compact, all in one."""
 171:     from core.compactor import Compactor
 172:     from runtime.bedrock_client import BedrockClient, Response
 173: 
 174:     client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
 175: 
 176:     def fake_chat(*args, **kwargs):
 177:         return Response(text="summary text", usage={"input_tokens": 100, "output_tokens": 30})
 178: 
 179:     monkeypatch.setattr(client, "chat", fake_chat)
 180: 
 181:     # Force should_compact = True via huge messages.
 182:     huge = "x" * 600_000
 183:     msgs = [{"role": "user", "content": huge}]
 184:     result = Compactor.run(client, msgs, max_tokens=100_000)
 185:     assert result.success
 186:     assert result.summary == "summary text"
 187:     assert "summary text" in result.messages_after[0]["content"]
 188:     assert result.tokens_after < result.tokens_before
 189: 
 190: 
 191: def test_compactor_run_skips_when_under_threshold(monkeypatch):
 192:     from core.compactor import Compactor
 193:     from runtime.bedrock_client import BedrockClient
 194: 
 195:     client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
 196:     msgs = [{"role": "user", "content": "tiny"}]
 197:     result = Compactor.run(client, msgs, max_tokens=200_000)
 198:     assert not result.success
 199:     assert "not needed" in result.error
 200: 
 201: 
 202: # ============================================================
 203: # T1 â€” AutoCompactCircuitBreaker
 204: # ============================================================
 205: 
 206: def test_circuit_breaker_cooldown_blocks_repeated_attempts():
 207:     from core.compactor import AutoCompactCircuitBreaker
 208: 
 209:     cb = AutoCompactCircuitBreaker(cooldown_seconds=10, max_per_session=100)
 210:     ok, _ = cb.should_attempt()
 211:     assert ok
 212:     cb.record_attempt()
 213:     ok2, reason = cb.should_attempt()
 214:     assert not ok2
 215:     assert "cooldown" in reason.lower()
 216: 
 217: 
 218: def test_circuit_breaker_session_cap():
 219:     from core.compactor import AutoCompactCircuitBreaker
 220: 
 221:     cb = AutoCompactCircuitBreaker(cooldown_seconds=0, max_per_session=2)
 222:     cb.record_attempt()
 223:     cb.record_attempt()
 224:     ok, reason = cb.should_attempt()
 225:     assert not ok
 226:     assert "session cap" in reason.lower()
 227: 
 228: 
 229: def test_circuit_breaker_reset():
 230:     from core.compactor import AutoCompactCircuitBreaker
 231: 
 232:     cb = AutoCompactCircuitBreaker(cooldown_seconds=10, max_per_session=2)
 233:     cb.record_attempt()
 234:     cb.record_attempt()
 235:     assert not cb.should_attempt()[0]
 236:     cb.reset()
 237:     assert cb.should_attempt()[0]
 238: 
 239: 
 240: # ============================================================
 241: # T1 â€” apply_cache_control_to_blocks
 242: # ============================================================
 243: 
 244: def test_apply_cache_control_marks_last_ephemeral():
 245:     from core.compactor import apply_cache_control_to_blocks
 246: 
 247:     blocks = [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
 248:     out = apply_cache_control_to_blocks(blocks)
 249:     assert "cache_control" not in out[0]
 250:     assert out[1]["cache_control"] == {"type": "ephemeral"}
 251: 
 252: 
 253: def test_apply_cache_control_at_specific_index():
 254:     from core.compactor import apply_cache_control_to_blocks
 255: 
 256:     blocks = [{"type": "text", "text": str(i)} for i in range(3)]
 257:     out = apply_cache_control_to_blocks(blocks, cache_break_at=0)
 258:     assert out[0]["cache_control"] == {"type": "ephemeral"}
 259:     assert "cache_control" not in out[1]
 260:     assert "cache_control" not in out[2]
 261: 
 262: 
 263: def test_apply_cache_control_empty_list():
 264:     from core.compactor import apply_cache_control_to_blocks
 265:     assert apply_cache_control_to_blocks([]) == []
 266: 
 267: 
 268: # ============================================================
 269: # B-2 â€” count_tokens_via_haiku_fallback
 270: # ============================================================
 271: 
 272: def test_count_tokens_haiku_fallback_in_mock_mode():
 273:     from core.compactor import count_tokens_via_haiku_fallback
 274:     from runtime.bedrock_client import BedrockClient
 275: 
 276:     client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
 277:     msgs = [{"role": "user", "content": "hello world"}]
 278:     n = count_tokens_via_haiku_fallback(msgs, client)
 279:     assert isinstance(n, int)
 280:     assert n > 0
 281: 
 282: 
 283: def test_count_tokens_haiku_fallback_handles_none_client():
 284:     from core.compactor import count_tokens_via_haiku_fallback
 285:     assert count_tokens_via_haiku_fallback([], None) is None
 286: 
 287: 
 288: # ============================================================
 289: # B+5 â€” advisor sub-cost attribution
 290: # ============================================================
 291: 
 292: def test_advisor_cost_attributed_when_aux_model_set(monkeypatch):
 293:     """When CONFIG.compaction_model is set AND a different aux client is
 294:     used, summary tokens go into TOKENS.subagent_cost['advisor'].
 295:     Closes the B+5 deferral from ADR-022."""
 296:     from core.compactor import Compactor
 297:     from runtime.bedrock_client import BedrockClient, Response
 298:     from runtime.tokens import TOKENS
 299:     from runtime.config import CONFIG
 300: 
 301:     # Set up: main client + auxiliary client (we mock the aux build).
 302:     main_client = BedrockClient(model_id="main-model", region="us-east-1", mock_mode=True)
 303:     aux_client = BedrockClient(model_id="aux-model", region="us-east-1", mock_mode=True)
 304: 
 305:     monkeypatch.setattr(CONFIG, "compaction_model", "aux-model")
 306:     Compactor._aux_client_cache = {}  # reset cache
 307: 
 308:     # Spy on _summary_client to verify aux is selected.
 309:     monkeypatch.setattr(
 310:         Compactor, "_summary_client",
 311:         classmethod(lambda cls, mc: aux_client),
 312:     )
 313: 
 314:     def fake_aux_chat(*args, **kwargs):
 315:         return Response(
 316:             text="advisor-built summary",
 317:             usage={"input_tokens": 500, "output_tokens": 100},
 318:         )
 319: 
 320:     monkeypatch.setattr(aux_client, "chat", fake_aux_chat)
 321: 
 322:     TOKENS.reset()
 323:     # Add some pricing so cost is non-zero (hitchk test pricing fallback)
 324:     summary = Compactor.create_llm_summary(main_client, [
 325:         {"role": "user", "content": "discuss the project"},
 326:     ])
 327:     assert summary == "advisor-built summary"
 328:     # Advisor bucket present (cost may be 0 if aux-model has no pricing,
 329:     # but the BUCKET should exist via tokens accumulating).
 330:     assert TOKENS.subagent_input_tokens.get("advisor", 0) >= 500
 331:     assert TOKENS.subagent_output_tokens.get("advisor", 0) >= 100
 332: 
 333: 
 334: def test_advisor_falls_back_to_parent_when_no_aux(monkeypatch):
 335:     """When no compaction_model is set, summary uses the main client and
 336:     tokens go to parent bucket (not advisor)."""
 337:     from core.compactor import Compactor
 338:     from runtime.bedrock_client import BedrockClient, Response
 339:     from runtime.tokens import TOKENS
 340:     from runtime.config import CONFIG
 341: 
 342:     main_client = BedrockClient(model_id="main", region="us-east-1", mock_mode=True)
 343:     monkeypatch.setattr(CONFIG, "compaction_model", "")
 344:     Compactor._aux_client_cache = {}
 345: 
 346:     def fake_chat(*args, **kwargs):
 347:         return Response(text="parent summary", usage={"input_tokens": 100, "output_tokens": 30})
 348: 
 349:     monkeypatch.setattr(main_client, "chat", fake_chat)
 350:     TOKENS.reset()
 351:     Compactor.create_llm_summary(main_client, [{"role": "user", "content": "x"}])
 352:     # Parent bucket got the tokens (advisor is 0).
 353:     assert TOKENS.parent_input_tokens >= 100
 354:     assert TOKENS.subagent_input_tokens.get("advisor", 0) == 0

2026-05-03T03:33:35.270756Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.6 seconds
Output:
Get-Content : Cannot find path 'D:\tmp\v4_compactor_section.txt' because it does not exist.
At line:2 char:7
+ $i=1; Get-Content -Path '/tmp/v4_compactor_section.txt' | ForEach-Obj ...
+       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (D:\tmp\v4_compactor_section.txt:String) [Get-Content], ItemNotFoundExce 
   ption
    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.GetContentCommand
 

 exited 1 in 593ms:
Get-Content : Cannot find path 'D:\tmp\v4_compactor_section.txt' because it does not exist.
At line:2 char:7
+ $i=1; Get-Content -Path '/tmp/v4_compactor_section.txt' | ForEach-Obj ...
+       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (D:\tmp\v4_compactor_section.txt:String) [Get-Content], ItemNotFoundExce 
   ption
    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.GetContentCommand
 

codex
I’ve loaded `compactor.py` and the Block A integration tests; the v4 parity file path `/tmp/v4_compactor_section.txt` doesn’t exist in this workspace as-is. I’m locating that file now (or an equivalent copy) before finalizing parity verdicts.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-ChildItem -Path . -Recurse -Filter 'v4_compactor_section.txt' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName" in D:\Github\sagemaker-coding-agent
 succeeded in 670ms:
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "if (Test-Path 'C:\\tmp\\v4_compactor_section.txt') { Get-Item 'C:\\tmp\\v4_compactor_section.txt' | Select-Object -ExpandProperty FullName }" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'if (Test-Path "$env:TEMP'"\\v4_compactor_section.txt\") { Get-Item \""'$env:TEMP'"\\v4_compactor_section.txt\" | Select-Object -ExpandProperty FullName }" in D:\Github\sagemaker-coding-agent
 succeeded in 500ms:
 succeeded in 713ms:
C:\Users\winst\AppData\Local\Temp\v4_compactor_section.txt

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content -Path "$env:TEMP'"\\v4_compactor_section.txt\" | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 484ms:
   1: class Compactor:
   2:     """Smart context compaction - prune then summarize."""
   3: 
   4:     PRUNE_PROTECT_TOKENS = 40000  # Keep last 40K tokens of tool outputs
   5:     PRUNE_MIN_SAVINGS = 10000     # Only prune if saving 10K+ tokens
   6:     SUMMARY_TRIGGER_PERCENT = 0.80  # Trigger at 80% context
   7: 
   8:     # Protected tools - never prune these (important for agent memory)
   9:     PROTECTED_TOOLS = {"todo_write", "todo_read", "semantic_search"}
  10: 
  11:     _tokenizer = None
  12:     _tokenizer_checked = False
  13: 
  14:     @classmethod
  15:     def estimate_tokens(cls, text: str) -> int:
  16:         """Estimate tokens. Uses tiktoken cl100k_base if available (~95% accurate),
  17:         else conservative 4/3 multiplier (V4.2 V2-F): chars/3 = chars/4 * 4/3."""
  18:         if not cls._tokenizer_checked:
  19:             cls._tokenizer_checked = True
  20:             try:
  21:                 import tiktoken
  22:                 cls._tokenizer = tiktoken.get_encoding("cl100k_base")
  23:             except (ImportError, Exception):
  24:                 pass
  25:         if cls._tokenizer:
  26:             return len(cls._tokenizer.encode(text, disallowed_special=()))
  27:         return len(text) // 3  # conservative: 4/3 Ã— (chars/4) = chars/3
  28: 
  29:     @classmethod
  30:     def prune_tool_outputs(cls, messages: List[Dict], max_context: int) -> Tuple[List[Dict], int]:
  31:         """
  32:         Prune old tool outputs while keeping recent ones.
  33:         Returns (pruned_messages, tokens_saved).
  34:         """
  35:         if not messages:
  36:             return messages, 0
  37: 
  38:         # Deep copy first, then collect and mutate only the copy
  39:         pruned_messages = copy.deepcopy(messages)
  40: 
  41:         # Build tool_use_id -> tool_name map for protected tool detection
  42:         tool_name_map: Dict[str, str] = {}
  43:         for msg in pruned_messages:
  44:             content = msg.get("content", [])
  45:             if isinstance(content, list):
  46:                 for item in content:
  47:                     if isinstance(item, dict) and item.get("type") == "tool_use":
  48:                         tool_name_map[item.get("id", "")] = item.get("name", "")
  49: 
  50:         # Find tool result items in the COPY to potentially prune
  51:         tool_results = []
  52:         for i, msg in enumerate(pruned_messages):
  53:             content = msg.get("content", [])
  54:             if isinstance(content, list):
  55:                 for item in content:
  56:                     if isinstance(item, dict) and item.get("type") == "tool_result":
  57:                         tool_results.append({
  58:                             "index": i,
  59:                             "tokens": cls.estimate_tokens(str(item.get("content", ""))),
  60:                             "item": item,
  61:                             "tool_name": tool_name_map.get(item.get("tool_use_id", ""), ""),
  62:                         })
  63: 
  64:         if not tool_results:
  65:             return messages, 0
  66: 
  67:         # Walk from newest to oldest, protect last 40K tokens + protected tools
  68:         protected_tokens = 0
  69:         tokens_saved = 0
  70:         for tr in reversed(tool_results):
  71:             # Never prune protected tools (important for agent memory)
  72:             if tr["tool_name"] in cls.PROTECTED_TOOLS:
  73:                 protected_tokens += tr["tokens"]
  74:                 continue
  75:             if protected_tokens < cls.PRUNE_PROTECT_TOKENS:
  76:                 protected_tokens += tr["tokens"]
  77:             else:
  78:                 # Prune this tool output (mutates only the deep copy)
  79:                 content = tr["item"].get("content", "")
  80:                 if len(content) > 1000:
  81:                     tr["item"]["content"] = content[:500] + f"\n[... {len(content)} chars trimmed â€” stale tool output ...]\n" + content[-500:]
  82:                     tokens_saved += tr["tokens"] - 260  # Approximate new size
  83: 
  84:         if tokens_saved < cls.PRUNE_MIN_SAVINGS:
  85:             return messages, 0  # Not worth pruning - return originals untouched
  86: 
  87:         return pruned_messages, tokens_saved
  88: 
  89:     @classmethod
  90:     def create_summary_prompt(cls, messages: List[Dict]) -> str:
  91:         """Create a prompt to summarize the conversation using Claude Code's 9-section format
  92:         plus V4.9.4 'Resolved/Pending Questions' sections (hermes pattern) for crisper resume.
  93:         """
  94:         return """<analysis>
  95: First, analyze the conversation to identify: main goal, technical concepts, files touched, errors encountered, and current progress.
  96: </analysis>
  97: 
  98: Create a detailed summary following these EXACT sections:
  99: 
 100: 1. **Primary Request and Intent**: What did the user explicitly ask for? What is their underlying goal?
 101: 
 102: 2. **Key Technical Concepts**: Technologies, frameworks, libraries, patterns discussed or used.
 103: 
 104: 3. **Files and Code Sections**: For each important file:
 105:    - File path (absolute)
 106:    - WHY it's important
 107:    - What changes were made (if any)
 108:    - Key code snippets (if relevant)
 109: 
 110: 4. **Errors and Fixes**: For each error encountered:
 111:    - The error message
 112:    - How it was fixed
 113:    - Any user feedback on the fix
 114: 
 115: 5. **Problem Solving**: Problems solved during the session, and any ongoing issues still unresolved.
 116: 
 117: 6. **User Messages**: List all user messages from the provided context verbatim (prevents intent drift):
 118:    - "message 1 exact text"
 119:    - "message 2 exact text"
 120:    - (for all messages in context â€” note: older messages may have been truncated)
 121: 
 122: 7. **Pending Tasks**: Tasks mentioned but not yet completed.
 123: 
 124: 8. **Current Work**: Precise current state including:
 125:    - What step we're on
 126:    - What was just completed
 127:    - Relevant code context
 128: 
 129: 9. **Next Step**: Only if directly in line with user's explicit request. Include direct quotes from user if applicable.
 130: 
 131: 10. **Resolved Questions** (V4.9.4): list each question/decision the conversation has SETTLED, one per line:
 132:     - "Q: <question>" -> "A: <one-sentence resolution>"
 133:     - Only include items that no longer need attention.
 134: 
 135: 11. **Pending Questions** (V4.9.4): list each open question/decision still needing resolution:
 136:     - "Q: <question>" -> "Status: <waiting on user / blocked on X / next-up>"
 137:     - This is the FIRST thing to look at when resuming after compaction.
 138: 
 139: 12. **Standing Constraints** (V4.10.5): hard rules / standing user instructions / project-wide constraints that MUST survive compaction:
 140:     - Standing user preferences (e.g. "always use Python 3.11", "never push to GitHub", "use Sonnet 4.5 not Haiku")
 141:     - Project rules from CLAUDE.md / AGENT_STATUS.md "Standing User Instructions" section
 142:     - Compliance / security / data-handling constraints
 143:     - One bullet each. Skip if none apply.
 144: 
 145: 13. **Critical Don't-Forget Context** (V4.10.5): the 1-3 most important pieces of context where forgetting WOULD cause a regression:
 146:     - e.g. "User flagged that v4.10.2 had a verify-prompt contradiction; check we don't reintroduce MANDATORY language."
 147:     - This is what the next turn after compact should re-orient on first.
 148:     - Keep terse. Quote the user's exact wording when load-bearing.
 149: 
 150: Format as a comprehensive summary that preserves all context needed to continue seamlessly."""
 151: 
 152:     MAX_SUMMARY_INPUT_MESSAGES = 20  # Truncate conversation for summarization (cost + context limit)
 153:     MAX_PTL_RETRIES = 3
 154:     PTL_RETRY_MARKER = "[Earlier conversation truncated for summary retry]"
 155: 
 156:     @classmethod
 157:     def _build_summary_input(cls, messages: List[Dict]) -> List[Dict]:
 158:         """Select a summary-safe slice of the conversation while preserving recent context."""
 159:         if len(messages) > cls.MAX_SUMMARY_INPUT_MESSAGES:
 160:             head = messages[:3]  # Keep original user request context
 161:             tail = messages[-(cls.MAX_SUMMARY_INPUT_MESSAGES - 3):]
 162:             if head and tail and head[-1].get("role") == tail[0].get("role"):
 163:                 tail = tail[1:]
 164:             return head + tail
 165:         return list(messages)
 166: 
 167:     @classmethod
 168:     def _truncate_head_for_ptl_retry(cls, messages: List[Dict]) -> Optional[List[Dict]]:
 169:         """Drop the oldest slice of the summary input while keeping a Bedrock-safe user start."""
 170:         if not messages:
 171:             return None
 172: 
 173:         working = list(messages)
 174:         if (
 175:             working
 176:             and working[0].get("role") == "user"
 177:             and working[0].get("content") == cls.PTL_RETRY_MARKER
 178:         ):
 179:             working = working[1:]
 180: 
 181:         if len(working) < 4:
 182:             return None
 183: 
 184:         drop_count = max(1, len(working) // 4)
 185:         truncated = working[drop_count:]
 186:         if len(truncated) < 2:
 187:             return None
 188: 
 189:         if truncated[0].get("role") != "user":
 190:             truncated.insert(0, {"role": "user", "content": cls.PTL_RETRY_MARKER})
 191: 
 192:         return truncated
 193: 
 194:     # V4.9.4: per-tool-result cap during summary generation (cheap pre-LLM pass).
 195:     # Tool outputs above this size get a head/tail preview replacing the bulk â€”
 196:     # prevents wasting summary tokens on stale 50KB bash dumps.
 197:     SUMMARY_TOOL_RESULT_HEAD = 800   # chars from head kept verbatim
 198:     SUMMARY_TOOL_RESULT_TAIL = 400   # chars from tail kept verbatim
 199:     SUMMARY_TOOL_RESULT_THRESHOLD = 2000  # only prune outputs larger than this
 200: 
 201:     @classmethod
 202:     def _prune_tool_results_for_summary(cls, messages: List[Dict]) -> List[Dict]:
 203:         """V4.9.4: Cheap pre-LLM pass â€” replace large tool_result bodies with head/tail
 204:         previews so the LLM summary call doesn't pay tokens to re-read stale dumps.
 205:         Pure-local, no LLM call. Idempotent. Returns a new list, doesn't mutate input.
 206:         """
 207:         out = []
 208:         pruned_count = 0
 209:         pruned_chars = 0
 210:         for msg in messages:
 211:             content = msg.get("content")
 212:             if not isinstance(content, list):
 213:                 out.append(msg)
 214:                 continue
 215:             new_blocks = []
 216:             mutated = False
 217:             for block in content:
 218:                 if not isinstance(block, dict):
 219:                     new_blocks.append(block)
 220:                     continue
 221:                 if block.get("type") != "tool_result":
 222:                     new_blocks.append(block)
 223:                     continue
 224:                 inner = block.get("content")
 225:                 # tool_result.content is usually a string OR a list of blocks
 226:                 if isinstance(inner, str) and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
 227:                     head = inner[:cls.SUMMARY_TOOL_RESULT_HEAD]
 228:                     tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL:]
 229:                     pruned_chars += len(inner) - len(head) - len(tail)
 230:                     pruned_count += 1
 231:                     new_block = dict(block)
 232:                     new_block["content"] = (
 233:                         f"{head}\n... [pruned {len(inner) - len(head) - len(tail):,} chars for summary] ...\n{tail}"
 234:                     )
 235:                     new_blocks.append(new_block)
 236:                     mutated = True
 237:                 elif isinstance(inner, list):
 238:                     new_inner = []
 239:                     inner_mutated = False
 240:                     for sub in inner:
 241:                         if isinstance(sub, dict) and sub.get("type") == "text":
 242:                             txt = sub.get("text", "")
 243:                             if len(txt) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
 244:                                 head = txt[:cls.SUMMARY_TOOL_RESULT_HEAD]
 245:                                 tail = txt[-cls.SUMMARY_TOOL_RESULT_TAIL:]
 246:                                 pruned_chars += len(txt) - len(head) - len(tail)
 247:                                 pruned_count += 1
 248:                                 new_sub = dict(sub)
 249:                                 new_sub["text"] = (
 250:                                     f"{head}\n... [pruned {len(txt) - len(head) - len(tail):,} chars for summary] ...\n{tail}"
 251:                                 )
 252:                                 new_inner.append(new_sub)
 253:                                 inner_mutated = True
 254:                                 continue
 255:                         new_inner.append(sub)
 256:                     if inner_mutated:
 257:                         new_block = dict(block)
 258:                         new_block["content"] = new_inner
 259:                         new_blocks.append(new_block)
 260:                         mutated = True
 261:                     else:
 262:                         new_blocks.append(block)
 263:                 else:
 264:                     new_blocks.append(block)
 265:             if mutated:
 266:                 new_msg = dict(msg)
 267:                 new_msg["content"] = new_blocks
 268:                 out.append(new_msg)
 269:             else:
 270:                 out.append(msg)
 271:         if pruned_count > 0:
 272:             logging.info(
 273:                 f"[COMPACT-PREP] pruned {pruned_count} oversized tool_result block(s), "
 274:                 f"saved ~{pruned_chars:,} chars before LLM summary"
 275:             )
 276:         return out
 277: 
 278:     @classmethod
 279:     def _summary_client(cls, main_client):
 280:         """V4.9.4: If CONFIG.compaction_model is set, build (or reuse) a Bedrock client
 281:         for that cheaper auxiliary model so summaries don't pay main-model rates.
 282:         Bedrock-only â€” no provider switch, just a different modelId in the same region.
 283:         Returns the main client unchanged when no auxiliary is configured.
 284:         """
 285:         aux_model = (getattr(CONFIG, "compaction_model", "") or "").strip()
 286:         if not aux_model or aux_model == main_client.model_id:
 287:             return main_client
 288:         # Cache aux clients on the class so we don't construct one per compaction
 289:         if not hasattr(cls, "_aux_client_cache"):
 290:             cls._aux_client_cache = {}
 291:         cached = cls._aux_client_cache.get(aux_model)
 292:         if cached is not None:
 293:             return cached
 294:         try:
 295:             aux = BedrockClient(aux_model, main_client.region, main_client.mock_mode)
 296:             cls._aux_client_cache[aux_model] = aux
 297:             logging.info(f"[COMPACT] Using auxiliary compaction model: {aux_model}")
 298:             return aux
 299:         except Exception as e:
 300:             logging.warning(f"[COMPACT] Auxiliary model '{aux_model}' init failed, using main: {e}")
 301:             return main_client
 302: 
 303:     @classmethod
 304:     def create_llm_summary(cls, client, messages: List[Dict]) -> Optional[str]:
 305:         """Create LLM-generated summary via Bedrock. Returns None on failure.
 306:         Used by both manual and auto compact for high-quality summaries.
 307:         Truncates long conversations to ~20 messages to avoid sending 160K+ tokens.
 308: 
 309:         V4.9.4: pre-LLM tool-result pruning + optional auxiliary model for cost win.
 310:         """
 311:         # V4.9.4: cheap pre-LLM pass to drop large tool_result bodies
 312:         messages = cls._prune_tool_results_for_summary(messages)
 313:         # V4.9.4: optionally route summary through cheaper auxiliary model
 314:         summary_client = cls._summary_client(client)
 315:         summary_input = cls._build_summary_input(messages)
 316:         attempts = 0
 317:         while True:
 318:             try:
 319:                 summary_prompt = cls.create_summary_prompt(summary_input)
 320:                 summary_messages = list(summary_input)
 321:                 # Ensure proper role alternation: Bedrock requires user/assistant alternation
 322:                 if summary_messages and summary_messages[-1].get("role") == "user":
 323:                     summary_messages.append({"role": "assistant", "content": "[Preparing summary...]"})
 324:                 summary_messages.append({"role": "user", "content": summary_prompt})
 325: 
 326:                 response = summary_client.chat(
 327:                     messages=summary_messages,
 328:                     system=("You are summarizing a coding conversation. You have ZERO tools available â€” "
 329:                             "do NOT attempt any tool calls. Be concise but preserve:\n"
 330:                             "1. Current task and goal\n2. Key files modified or read\n"
 331:                             "3. Important decisions made\n4. Where we left off\n"
 332:                             "5. What needs to happen next\n"
 333:                             "6. (V4.9.4) Resolved questions\n"
 334:                             "7. (V4.9.4) Pending questions"),
 335:                     tools=None,
 336:                     max_tokens=2000,
 337:                     temperature=0.0
 338:                 )
 339:                 if response and response.usage:
 340:                     # V4.9.4: track tokens against the model that actually ran (could be aux)
 341:                     TOKENS.add(response.usage, model_id=summary_client.model_id)
 342:                 if response and response.text:
 343:                     return response.text
 344:                 return None
 345:             except Exception as e:
 346:                 err_str = str(e).lower()
 347:                 is_ptl = ("prompt" in err_str and "long" in err_str) or "too many tokens" in err_str
 348:                 if not is_ptl:
 349:                     logging.warning(f"LLM summary failed: {e}")
 350:                     return None
 351: 
 352:                 attempts += 1
 353:                 if attempts > cls.MAX_PTL_RETRIES:
 354:                     logging.warning(f"LLM summary PTL exceeded retry budget ({cls.MAX_PTL_RETRIES}): {e}")
 355:                     return None
 356: 
 357:                 truncated = cls._truncate_head_for_ptl_retry(summary_input)
 358:                 if not truncated:
 359:                     logging.warning(f"LLM summary PTL could not shrink input further: {e}")
 360:                     return None
 361: 
 362:                 logging.warning(
 363:                     "LLM summary PTL on attempt %s/%s - retrying with %s messages instead of %s",
 364:                     attempts,
 365:                     cls.MAX_PTL_RETRIES,
 366:                     len(truncated),
 367:                     len(summary_input),
 368:                 )
 369:                 summary_input = truncated
 370: 
 371:     # Fallback fixed overhead estimate; actual is computed dynamically by TOKENS.get_fixed_overhead()
 372:     FIXED_OVERHEAD_TOKENS = 6000
 373: 
 374:     @classmethod
 375:     def should_compact(cls, messages: List[Dict], max_tokens: int) -> bool:
 376:         """Check if compaction is needed. Accounts for system prompt + tool overhead."""
 377:         # Use dynamically calculated overhead when available, else fallback
 378:         try:
 379:             overhead = TOKENS.get_fixed_overhead()
 380:         except Exception:
 381:             overhead = cls.FIXED_OVERHEAD_TOKENS
 382:         total_tokens = CONTEXT.estimate_tokens(messages) + overhead
 383:         return total_tokens > max_tokens * cls.SUMMARY_TRIGGER_PERCENT
 384: 
 385:     KEEP_LAST_MESSAGES = 3  # Keep last N messages after compact
 386: 
 387:     @classmethod
 388:     def compact(cls, messages: List[Dict], summary: str) -> List[Dict]:
 389:         """
 390:         Replace old messages with summary.
 391:         Keeps: summary + last N messages (default 3)
 392:         V4: also re-injects recently-read file contents after compact (post-compact restore).
 393:         """
 394:         # V4: capture recently-read files BEFORE discarding old messages
 395:         recently_read = get_recently_read_files(messages)
 396: 
 397:         summary_msg = {
 398:             "role": "user",
 399:             "content": f"[CONVERSATION SUMMARY]\n{summary}\n[END SUMMARY - Continuing from here]"
 400:         }
 401:         summary_ack = {
 402:             "role": "assistant",
 403:             "content": "Summary received. Continuing from compacted context."
 404:         }
 405: 
 406:         # Keep last N messages for continuity
 407:         n = cls.KEEP_LAST_MESSAGES
 408:         recent_messages = copy.deepcopy(messages[-n:] if len(messages) > n else messages)
 409: 
 410:         # Ensure the synthetic summary+ack is followed by a user message for Bedrock alternation.
 411:         while recent_messages and recent_messages[0].get("role") != "user":
 412:             recent_messages.pop(0)
 413:         if not recent_messages:
 414:             recent_messages = [{"role": "user", "content": "[Conversation compacted. Continue from summary.]"}]
 415: 
 416:         compacted = [summary_msg, summary_ack] + recent_messages
 417: 
 418:         # V4.8.0: Clear FILE_CACHE context markers since old file results are discarded.
 419:         # Without this, agent thinks files are still in context when they've been compacted away.
 420:         FILE_CACHE.clear_context()
 421: 
 422:         # V4: append file restoration, guarding Bedrock role alternation (SR-5)
 423:         restoration_text = build_file_restoration_message(recently_read)
 424:         # V4.7.1: also re-inject the TODO list so the agent remembers its work plan
 425:         todo_text = build_todo_restoration_message()
 426:         combined_restore = None
 427:         if restoration_text and todo_text:
 428:             combined_restore = todo_text + "\n\n" + restoration_text
 429:         elif restoration_text:
 430:             combined_restore = restoration_text
 431:         elif todo_text:
 432:             combined_restore = todo_text
 433: 
 434:         if combined_restore:
 435:             last_role = compacted[-1].get("role") if compacted else None
 436:             if last_role == "assistant":
 437:                 compacted.append({"role": "user", "content": combined_restore})
 438:             elif last_role == "user":
 439:                 last_content = compacted[-1].get("content", "")
 440:                 if isinstance(last_content, str):
 441:                     compacted[-1]["content"] = last_content + "\n\n" + combined_restore
 442:                 elif isinstance(last_content, list):
 443:                     compacted[-1]["content"].append({"type": "text", "text": combined_restore})
 444: 
 445:         return compacted
 446: 
 447: # Global compactor
 448: COMPACTOR = Compactor()
 449: 

web search: 
web search: 
web search: 
web search: 
codex
I found the v4 source in `%TEMP%` and I’m now cross-checking behavior deltas and call-sites to separate intentional adaptations from actual drift/regression risk.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"count_tokens_via_haiku_fallback|apply_cache_control_to_blocks|AUTO_COMPACT|Compactor\\.run|should_compact\\(\" compact_v5/MAIN/agent" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content -Path '"'compact_v5/MAIN/agent/runtime/tokens.py' | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content -Path '"'compact_v5/MAIN/agent/runtime/bedrock_client.py' | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 617ms:
   1: """V5 BedrockClient â€” verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560.
   2: 
   3: Per ADR-005: BedrockClient is a pure v4 reuse (Bedrock-native, already
   4: production-tested). The only Phase-1 change is structural â€” the class lives
   5: in its own module instead of inline in the v4 monolith.
   6: 
   7: Sophisticated cache-break detection (Runnable promptCacheBreakDetection.ts)
   8: is DEFERRED to Phase 6 because it requires multi-block system prompts that
   9: v5 doesn't have until prompt/sections.py lands. Phase 6 ADR will track that
  10: adoption.
  11: 
  12: Phase 1 simplification: the full retry-classifier + jittered-backoff loop
  13: lives in v4's BedrockClient. For Phase 1, we keep that loop intact (it's
  14: already battle-tested), but the helper classes (BedrockErrorCategory,
  15: ErrorClassifier, RetryPolicy) are imported from a temporary local module
  16: inside this file. Phase 8 will extract them to core/errors.py + core/retry.py
  17: with cleaner separation. This avoids a circular Phase-1/Phase-8 dependency.
  18: 
  19: PS Issue #4 verification (per V5_PS_ISSUES_MAPPING.md): tests/unit/test_bedrock.py
  20: must verify thinking config is sent on EVERY Bedrock call when
  21: CONFIG.thinking_enabled=True (not just the first turn).
  22: 
  23: Source: compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560.
  24: """
  25: from __future__ import annotations
  26: 
  27: import json
  28: import logging
  29: import time
  30: from dataclasses import dataclass, field
  31: from typing import Any, Dict, List, Optional
  32: 
  33: # botocore.config import is local-deferred so unit tests with mock_mode=True
  34: # can import this module without boto3 installed. Real flows will import on demand.
  35: 
  36: # CONFIG is imported lazily within methods to avoid circular import during Phase 1.
  37: 
  38: 
  39: # ============================================================
  40: # Response / ToolCall (lightweight value types â€” verbatim from v4)
  41: # ============================================================
  42: 
  43: @dataclass
  44: class ToolCall:
  45:     """A tool invocation request from the model."""
  46:     id: str
  47:     name: str
  48:     input: Dict[str, Any] = field(default_factory=dict)
  49: 
  50: 
  51: @dataclass
  52: class Response:
  53:     """Parsed Bedrock response."""
  54:     text: str
  55:     tool_calls: List[ToolCall] = field(default_factory=list)
  56:     stop_reason: str = ""
  57:     usage: Dict[str, Any] = field(default_factory=dict)
  58:     thinking: str = ""
  59: 
  60: 
  61: # ============================================================
  62: # Error categories + classifier + retry policy
  63: # Phase 8: extracted to core/errors.py + core/retry.py (ADR-014).
  64: # Re-imported here so existing call-sites (and tests) continue to work
  65: # byte-equivalent with Phase 1.
  66: # ============================================================
  67: 
  68: from core.errors import BedrockErrorCategory, ErrorClassifier  # noqa: F401
  69: from core.retry import RetryPolicy  # noqa: F401
  70: 
  71: 
  72: # ============================================================
  73: # BEDROCK_EXTRA_PARAMS_HEADERS (Block 0 item 0-3 â†’ Block B per ADR-020)
  74: # ============================================================
  75: #
  76: # Anthropic-API-direct features (interleaved-thinking beta, 1m-context
  77: # beta) ride on `anthropic-beta` HTTP headers. Bedrock does NOT accept
  78: # those headers; the equivalent goes in `additionalModelRequestFields`
  79: # in the request body. This Set documents which beta names we know need
  80: # the body-not-header treatment, so any future code that wants to opt
  81: # in to a beta has a single source of truth and can't accidentally pass
  82: # them as headers (which Bedrock would silently drop).
  83: #
  84: # Per Runnable constants/betas.ts:38-43 (R8 #74 â€” load-bearing).
  85: 
  86: BEDROCK_EXTRA_PARAMS_HEADERS: frozenset = frozenset({
  87:     "interleaved-thinking-2025-05-14",
  88:     "context-1m-2025-08-07",
  89:     # Codex Block-B finding #4 (MEDIUM) lock: tool-search beta is the
  90:     # 3rd Runnable constants/betas.ts entry that goes in body, not
  91:     # headers. v5 already implements tool_search via Phase-7 deferred
  92:     # loading, so this name belongs here.
  93:     "tool-search-tool-2025-10-19",
  94: })
  95: 
  96: 
  97: # ============================================================
  98: # BedrockClient (v4 verbatim port)
  99: # ============================================================
 100: 
 101: # botocore Config preset for retry tuning (v4 default).
 102: def _bedrock_client_config():
 103:     """Return a botocore Config with v4's retry tuning. Local-imports botocore."""
 104:     from botocore.config import Config as _BotoConfig
 105:     return _BotoConfig(
 106:         retries={"max_attempts": 1, "mode": "standard"},  # we handle retries ourselves
 107:         read_timeout=120,
 108:         connect_timeout=10,
 109:     )
 110: 
 111: 
 112: class BedrockClient:
 113:     """AWS Bedrock Claude client with mock mode for testing.
 114: 
 115:     Verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:2378.
 116:     Behavior unchanged â€” same prompt-cache fallback semantics, same retry
 117:     classifier, same thinking-mode handling.
 118: 
 119:     PS Issue #4 verification: `chat()` always sends `thinking` config when
 120:     `thinking_enabled=True`, regardless of which call this is in the session.
 121:     The fact that the model only RETURNS thinking blocks on some turns is a
 122:     model-side decision; v5 always SENDS the config so the model has the
 123:     option. test_bedrock.py verifies this.
 124:     """
 125: 
 126:     def __init__(
 127:         self,
 128:         model_id: str,
 129:         region: str,
 130:         mock_mode: bool = False,
 131:         client: Any = None,
 132:     ):
 133:         """Construct a BedrockClient.
 134: 
 135:         Args:
 136:             model_id: Bedrock inference profile id.
 137:             region: AWS region.
 138:             mock_mode: if True, no real Bedrock calls; `_mock_response()` is used.
 139:             client: optional pre-built bedrock-runtime client. If provided,
 140:                 boto3 is NOT imported. This lets unit tests inject a fake
 141:                 client without requiring boto3 to be installed (Codex Phase-01
 142:                 review finding 1).
 143:         """
 144:         self.model_id = model_id
 145:         self.region = region
 146:         self.mock_mode = mock_mode
 147:         self.prompt_cache_supported = True  # set False after first cache fallback
 148:         self._cache_threshold_warned = False
 149:         if mock_mode:
 150:             self.client = None
 151:         elif client is not None:
 152:             self.client = client
 153:         else:
 154:             import boto3
 155:             self.client = boto3.client(
 156:                 "bedrock-runtime", region_name=region, config=_bedrock_client_config()
 157:             )
 158: 
 159:     # ---------- mock-mode helpers ----------
 160: 
 161:     def _mock_response(self, messages, tools) -> Response:
 162:         """Generate mock response for testing (v4 verbatim, simplified)."""
 163:         last = messages[-1]["content"] if messages else ""
 164:         if isinstance(last, str):
 165:             low = last.lower()
 166:             if "list" in low and ("file" in low or "dir" in low):
 167:                 return Response(
 168:                     "I'll list the files.",
 169:                     [ToolCall("m1", "list_dir", {"path": "."})],
 170:                     "tool_use",
 171:                     {},
 172:                 )
 173:             if "read" in low:
 174:                 return Response(
 175:                     "I'll read that file.",
 176:                     [ToolCall("m2", "read_file", {"file_path": "README.md"})],
 177:                     "tool_use",
 178:                     {},
 179:                 )
 180:         return Response(
 181:             f"[MOCK] Received: {str(last)[:100]}...",
 182:             [],
 183:             "end_turn",
 184:             {"input_tokens": 100, "output_tokens": 50},
 185:         )
 186: 
 187:     # ---------- main chat entry ----------
 188: 
 189:     def chat(
 190:         self,
 191:         messages: List[Dict],
 192:         system: Any,  # str OR list-of-blocks (with cache_control)
 193:         tools: Optional[List[Dict]] = None,
 194:         max_tokens: int = 4096,
 195:         temperature: float = 0.0,
 196:         thinking_enabled: bool = False,
 197:         thinking_budget: int = 4096,
 198:     ) -> Response:
 199:         """Send chat request to Bedrock.
 200: 
 201:         Args:
 202:             messages: Conversation messages
 203:             system: System prompt (str or pre-formatted multi-block list with cache_control)
 204:             tools: Tool definitions
 205:             max_tokens: Maximum response tokens
 206:             temperature: Sampling temperature (0.0-1.0)
 207:             thinking_enabled: Enable extended thinking mode
 208:             thinking_budget: Max tokens for thinking (1024-16000)
 209:         """
 210:         if self.mock_mode:
 211:             return self._mock_response(messages, tools)
 212: 
 213:         # Lazy import CONFIG to avoid circular import during Phase 1.
 214:         from runtime.config import CONFIG
 215: 
 216:         # V4.1 #14: Prompt cache boundary.
 217:         # If cache enabled and supported, split system string into static (cached)
 218:         # + dynamic (uncached) blocks. Bedrock supports prompt caching natively
 219:         # via cache_control blocks in content. No anthropic_beta header needed.
 220:         # Haiku 4.5: min 4096 tokens/checkpoint. Sonnet 4.5: min 1024.
 221:         cache_active = CONFIG.enable_prompt_cache and self.prompt_cache_supported
 222:         if cache_active and isinstance(system, list):
 223:             # Already formatted as cache blocks by caller â€” pass as-is
 224:             system_field = system
 225:             use_cache = True
 226:         elif cache_active and isinstance(system, str):
 227:             # Split at the dynamic boundary marker if present, else cache full prompt
 228:             _CACHE_BOUNDARY = "\n\n# === DYNAMIC ==="
 229:             if _CACHE_BOUNDARY in system:
 230:                 static_part, dynamic_part = system.split(_CACHE_BOUNDARY, 1)
 231:                 # Bedrock rejects empty/whitespace text blocks â€” only add dynamic if non-empty
 232:                 if dynamic_part.strip():
 233:                     system_field = [
 234:                         {
 235:                             "type": "text",
 236:                             "text": static_part,
 237:                             "cache_control": {"type": "ephemeral"},
 238:                         },
 239:                         {"type": "text", "text": dynamic_part},
 240:                     ]
 241:                 else:
 242:                     system_field = [
 243:                         {
 244:                             "type": "text",
 245:                             "text": static_part,
 246:                             "cache_control": {"type": "ephemeral"},
 247:                         },
 248:                     ]
 249:             else:
 250:                 # No boundary â€” cache the whole prompt as static
 251:                 system_field = [
 252:                     {
 253:                         "type": "text",
 254:                         "text": system,
 255:                         "cache_control": {"type": "ephemeral"},
 256:                     },
 257:                 ]
 258:             use_cache = True
 259:         else:
 260:             system_field = system
 261:             use_cache = False
 262: 
 263:         body: Dict[str, Any] = {
 264:             "anthropic_version": "bedrock-2023-05-31",
 265:             "max_tokens": max_tokens,
 266:             "system": system_field,
 267:             "messages": messages,
 268:         }
 269:         # Note: Bedrock prompt caching is activated by cache_control blocks in
 270:         # content. No anthropic_beta header needed (that header is for the direct
 271:         # Anthropic API only).
 272: 
 273:         # Extended thinking mode (requires temperature=1).
 274:         # PS Issue #4: this block runs on EVERY chat() call when thinking_enabled
 275:         # is True â€” not just first message. The model decides per turn whether
 276:         # to USE the budget. tests/unit/test_bedrock.py asserts this contract.
 277:         if thinking_enabled:
 278:             body["thinking"] = {
 279:                 "type": "enabled",
 280:                 "budget_tokens": min(max(thinking_budget, 1024), 16000),
 281:             }
 282:             body["temperature"] = 1  # Required for thinking mode
 283:         else:
 284:             body["temperature"] = temperature
 285: 
 286:         if tools:
 287:             body["tools"] = tools
 288: 
 289:         # V4.9.4: jittered exponential backoff on transient/throttle errors.
 290:         # Cache-validation: strip cache blocks and retry once (existing v4.1 #14).
 291:         attempt = 0
 292:         last_exc: Optional[Exception] = None
 293:         while True:
 294:             try:
 295:                 response = self.client.invoke_model(
 296:                     modelId=self.model_id,
 297:                     body=json.dumps(body, separators=(",", ":")),
 298:                     contentType="application/json",
 299:                 )
 300:                 break  # success
 301:             except Exception as e:
 302:                 last_exc = e
 303:                 category, recovery, debug_msg = ErrorClassifier.classify(e)
 304: 
 305:                 # Cache-validation: strip cache blocks, retry once
 306:                 if (
 307:                     category == BedrockErrorCategory.VALIDATION_CACHE
 308:                     and use_cache
 309:                     and self.prompt_cache_supported
 310:                 ):
 311:                     logging.warning(
 312:                         f"[BEDROCK] Prompt cache not supported by this model/region, falling back: {debug_msg}"
 313:                     )
 314:                     self.prompt_cache_supported = False
 315:                     if isinstance(system, str):
 316:                         body["system"] = system
 317:                     else:
 318:                         body["system"] = "\n\n".join(
 319:                             b.get("text", "") for b in system if isinstance(b, dict)
 320:                         )
 321:                     use_cache = False
 322:                     continue
 323: 
 324:                 # Throttle / transient / etc.: retry with jitter
 325:                 if RetryPolicy.should_retry(attempt, recovery):
 326:                     sleep_s = RetryPolicy.backoff_seconds(attempt)
 327:                     logging.warning(
 328:                         f"[BEDROCK] {category} (recovery={recovery}, attempt={attempt + 1}/"
 329:                         f"{RetryPolicy.MAX_RETRIES + 1}, sleep={sleep_s:.1f}s): {debug_msg}"
 330:                     )
 331:                     time.sleep(sleep_s)
 332:                     attempt += 1
 333:                     continue
 334: 
 335:                 # Anything else: surface it
 336:                 logging.error(f"[BEDROCK] {category} (recovery={recovery}, no-retry): {debug_msg}")
 337:                 raise
 338: 
 339:         result = json.loads(response["body"].read())
 340:         return self._parse(result)
 341: 
 342:     # ---------- response parsing ----------
 343: 
 344:     def _parse(self, result: dict) -> Response:
 345:         """Parse Bedrock response into Response value type (v4 verbatim)."""
 346:         text = ""
 347:         thinking = ""
 348:         tool_calls: List[ToolCall] = []
 349:         for block in result.get("content", []):
 350:             block_type = block.get("type")
 351:             if block_type == "text":
 352:                 text += block.get("text", "")
 353:             elif block_type == "thinking":
 354:                 thinking += block.get("thinking", "")
 355:             elif block_type == "tool_use":
 356:                 tool_calls.append(
 357:                     ToolCall(
 358:                         id=block.get("id", ""),
 359:                         name=block.get("name", ""),
 360:                         input=block.get("input", {}),
 361:                     )
 362:                 )
 363:         return Response(
 364:             text=text,
 365:             tool_calls=tool_calls,
 366:             stop_reason=result.get("stop_reason", ""),
 367:             usage=result.get("usage", {}),
 368:             thinking=thinking,
 369:         )
 370: 
 371:     # ============================================================
 372:     # B-1 â€” countTokensWithBedrock (R4 #41, MUST)
 373:     # ============================================================
 374: 
 375:     def count_tokens(
 376:         self,
 377:         messages: List[Dict[str, Any]],
 378:         system: Optional[str] = None,
 379:         tools: Optional[List[Dict[str, Any]]] = None,
 380:         model_id: Optional[str] = None,
 381:     ) -> Optional[int]:
 382:         """Real Bedrock token count via the bedrock-runtime CountTokens API.
 383: 
 384:         Returns the token count as int, or None on failure / mock mode.
 385:         Per Runnable services/tokenEstimation.ts:437-495 (R4 #41 MUST):
 386:         without this, v5 has no real Bedrock token count and the
 387:         Compactor (Block A) cannot make safe context-budget decisions.
 388: 
 389:         Falls through to None when:
 390:           - mock_mode is True (no Bedrock contact)
 391:           - the bedrock-runtime client doesn't expose count_tokens
 392:             (older boto3 versions; retry by upgrading boto3 â‰¥ 1.35)
 393:           - the API returns a malformed response
 394:         """
 395:         if self.mock_mode:
 396:             # Crude fallback for mock-mode tests so the call shape is
 397:             # exercised without hitting Bedrock.
 398:             from runtime.tokens import rough_token_count_for_message
 399:             base = sum(rough_token_count_for_message(m) for m in messages)
 400:             if system:
 401:                 from runtime.tokens import estimate_message_tokens
 402:                 base += estimate_message_tokens(system)
 403:             return base
 404: 
 405:         if self.client is None:
 406:             return None
 407: 
 408:         try:
 409:             # Codex Block-B finding #3 (MEDIUM) lock: when any message
 410:             # contains a thinking block, switch the count-tokens body to
 411:             # match the assistant turn's actual shape (max_tokens=2048 +
 412:             # thinking config). Otherwise Bedrock either rejects or
 413:             # undercounts the thinking budget. Per Runnable
 414:             # services/tokenEstimation.ts:437-495 (R4 #43).
 415:             from runtime.tokens import has_thinking_blocks
 416:             uses_thinking = any(has_thinking_blocks(m) for m in messages)
 417:             body: Dict[str, Any] = {
 418:                 "anthropic_version": "bedrock-2023-05-31",
 419:                 "messages": messages,
 420:                 **({"system": system} if system else {}),
 421:                 **({"tools": tools} if tools else {}),
 422:                 "max_tokens": 2048 if uses_thinking else 1,
 423:             }
 424:             if uses_thinking:
 425:                 body["thinking"] = {"type": "enabled", "budget_tokens": 1024}
 426:             kwargs: Dict[str, Any] = {
 427:                 "modelId": model_id or self.model_id,
 428:                 "input": {
 429:                     "invokeModel": {"body": json.dumps(body).encode("utf-8")},
 430:                 },
 431:             }
 432:             resp = self.client.count_tokens(**kwargs)
 433:             count = resp.get("inputTokens")
 434:             if isinstance(count, int):
 435:                 return count
 436:             return None
 437:         except (AttributeError,) as exc:
 438:             logging.warning(
 439:                 "BedrockClient.count_tokens: client missing count_tokens method "
 440:                 "(boto3 < 1.35?): %s", exc,
 441:             )
 442:             return None
 443:         except Exception as exc:  # noqa: BLE001 â€” best-effort; no raise
 444:             logging.warning("BedrockClient.count_tokens failed: %s", exc)
 445:             return None

 succeeded in 644ms:
   1: """Block B â€” TokenTracker + per-agent attribution + tokenEstimation helpers.
   2: 
   3: Verbatim port of v4's `TokenTracker` (compact_v4/MAIN/agent/sagemaker_agent.py
   4: lines 3565-3753) plus:
   5: - per-agent input/output/cost attribution (B-11 + Plan v3 Â§Block B)
   6: - MODEL_COSTS for Haiku 4.5 + Sonnet 4.6 (B-10, R8 #34/#68)
   7: - EXCLUDED_MODELS_FOR_CACHE_BREAK Haiku set (R4 #14 MUST)
   8: - IMAGE_MAX_TOKEN_SIZE = 2000 (B-5, R4 #38)
   9: - bytesPerTokenForFileType (B-3, R4 #40)
  10: - estimateMessageTokens 4/3 padding (B-6, R4 #39)
  11: - hasThinkingBlocks helper (B-7, R4 #43)
  12: - roughTokenCountEstimationForBlock (B-4, R4 #44)
  13: - finalContextTokensFromLastResponse (B-9, R8 #16)
  14: - tokenCountWithEstimation walks back to last usage record (B-8, R8 #15)
  15: - ToolResult dataclass (B-13, V1 gap #1)
  16: 
  17: PORT_LOG: see #039 (TokenTracker), #040 (MODEL_COSTS+per-agent),
  18: #041 (Runnable tokenEstimation helpers), #042 (ToolResult).
  19: """
  20: from __future__ import annotations
  21: 
  22: import logging
  23: import threading
  24: from dataclasses import dataclass, field
  25: from typing import Any, Dict, List, Optional
  26: 
  27: 
  28: # ============================================================
  29: # B-13 â€” ToolResult dataclass (V1 gap #1, MUST)
  30: # ============================================================
  31: 
  32: @dataclass
  33: class ToolResult:
  34:     """Result envelope for a single tool execution.
  35: 
  36:     Verbatim port of v4 `compact_v4/MAIN/agent/sagemaker_agent.py:867-886`
  37:     metadata fields. v5 tools return either a plain string OR a ToolResult
  38:     so callers can introspect truncation + size for token-accounting.
  39:     """
  40:     output: str
  41:     tool_name: str = ""
  42:     truncated: bool = False
  43:     total_size: int = 0          # bytes/chars before truncation
  44:     shown_size: int = 0          # bytes/chars after truncation
  45:     error: bool = False
  46:     error_message: str = ""
  47: 
  48: 
  49: # ============================================================
  50: # B-10 â€” MODEL_COSTS (R8 #34, #68; Bedrock-only subset)
  51: # ============================================================
  52: #
  53: # 2-row Bedrock pricing table per the user's deployment (Haiku 4.5 +
  54: # Sonnet 4.6). Cache pricing math: cache_read = 10% of base input,
  55: # cache_write = 125% of base input. Output = full price. All values are
  56: # USD per 1K tokens, current as of 2026-04 Bedrock list pricing.
  57: #
  58: # Cross-region inference profile prefixes (`apac.`, `us.`, `eu.`) collapse
  59: # to canonical model id via `canonicalize_model_id()`.
  60: 
  61: MODEL_COSTS: Dict[str, Dict[str, float]] = {
  62:     "anthropic.claude-haiku-4-5-20251001-v1:0": {"input": 0.001, "output": 0.005},
  63:     "anthropic.claude-sonnet-4-5-20250929-v1:0": {"input": 0.003, "output": 0.015},
  64:     # Phase-1 baseline kept for parity tests
  65:     "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 0.003, "output": 0.015},
  66: }
  67: 
  68: # Backwards-compat alias (v4 internal name used inside TokenTracker.add).
  69: _MODEL_PRICING = MODEL_COSTS
  70: 
  71: 
  72: def canonicalize_model_id(model_id: str) -> str:
  73:     """Strip Bedrock cross-region inference prefixes.
  74: 
  75:     Per Runnable cost-tracker.ts:181-226 (R11 N9). v5 collapses
  76:     `apac.anthropic.claude-haiku-4-5-...` and
  77:     `anthropic.claude-haiku-4-5-...` to the same canonical key for
  78:     pricing lookup. Bedrock inference-profile prefixes covered:
  79:         au.   â€” Australia (Sydney; ap-southeast-2 default)
  80:         apac. â€” Asia-Pacific
  81:         us.   â€” United States (legacy us-east-1 / us-west-2)
  82:         eu.   â€” Europe (legacy eu-west-1 / eu-central-1)
  83: 
  84:     Codex Block-B finding #1 (HIGH) lock: `au.` was missing originally,
  85:     causing CONFIG.model_id="au.anthropic.claude-sonnet-4-5-..." to
  86:     miss MODEL_COSTS entirely and TOKENS to record $0.
  87:     """
  88:     if not model_id:
  89:         return model_id
  90:     for prefix in ("au.", "apac.", "us.", "eu."):
  91:         if model_id.startswith(prefix):
  92:             return model_id[len(prefix):]
  93:     return model_id
  94: 
  95: 
  96: # ============================================================
  97: # R4 #14 â€” EXCLUDED_MODELS_FOR_CACHE_BREAK (MUST)
  98: # ============================================================
  99: #
 100: # Haiku-4.5 cache hashing in Bedrock is non-deterministic in a way that
 101: # the prompt-cache-break detector misreads as a "section flipped". Add
 102: # Haiku to the exclusion set so cache-break warnings don't fire on Haiku
 103: # sessions. This is a MUST per Wave-5-DEEP R4 #14.
 104: 
 105: EXCLUDED_MODELS_FOR_CACHE_BREAK: set = {
 106:     "anthropic.claude-haiku-4-5-20251001-v1:0",
 107: }
 108: 
 109: 
 110: # ============================================================
 111: # B-5 â€” IMAGE_MAX_TOKEN_SIZE (R4 #38)
 112: # ============================================================
 113: #
 114: # Per Anthropic billing: each image consumed by Bedrock counts for at
 115: # most 2000 tokens regardless of resolution. Used by the rough estimator
 116: # below.
 117: 
 118: IMAGE_MAX_TOKEN_SIZE: int = 2000
 119: 
 120: 
 121: # ============================================================
 122: # B-3 â€” bytesPerTokenForFileType (R4 #40)
 123: # ============================================================
 124: #
 125: # Different file types compress to tokens differently. JSON is dense
 126: # (~2 bytes/token); plain text is sparse (~4 bytes/token). Used by the
 127: # rough estimator to avoid underestimating big JSON tool returns.
 128: 
 129: _BYTES_PER_TOKEN_BY_EXT: Dict[str, float] = {
 130:     ".json": 2.0,
 131:     ".jsonl": 2.0,
 132:     ".csv": 3.0,
 133:     ".tsv": 3.0,
 134:     ".xml": 2.5,
 135:     ".html": 2.5,
 136:     ".yaml": 3.0,
 137:     ".yml": 3.0,
 138:     ".py": 3.5,
 139:     ".js": 3.5,
 140:     ".ts": 3.5,
 141:     ".md": 4.0,
 142:     ".txt": 4.0,
 143: }
 144: 
 145: 
 146: def bytes_per_token_for_file_type(filename: str) -> float:
 147:     """Return the bytes-per-token ratio for a filename's extension.
 148: 
 149:     Falls back to 4.0 (plain-text) for unknown extensions. Used by the
 150:     rough estimator to budget tool output sizes.
 151:     """
 152:     if not filename:
 153:         return 4.0
 154:     lower = filename.lower()
 155:     for ext, ratio in _BYTES_PER_TOKEN_BY_EXT.items():
 156:         if lower.endswith(ext):
 157:             return ratio
 158:     return 4.0
 159: 
 160: 
 161: # ============================================================
 162: # B-6 â€” estimateMessageTokens with 4/3 padding (R4 #39)
 163: # ============================================================
 164: 
 165: def estimate_message_tokens(text: str, padding_factor: float = 4.0 / 3.0) -> int:
 166:     """Rough token estimator with 4/3 padding (Bedrock-side overhead).
 167: 
 168:     v4 used `len(text) // 3`. Runnable's microCompact.ts:164-205 adds a
 169:     4/3 multiplier so the estimate accounts for Bedrock framing tokens
 170:     (turn boundaries, role markers). Returns ceil(len/3 * 4/3) = len*4/9
 171:     rounded up.
 172:     """
 173:     if not text:
 174:         return 0
 175:     base = len(text) / 3.0
 176:     return int(base * padding_factor + 0.5)
 177: 
 178: 
 179: # ============================================================
 180: # B-7 â€” hasThinkingBlocks (R4 #43)
 181: # ============================================================
 182: 
 183: def has_thinking_blocks(message: Dict[str, Any]) -> bool:
 184:     """True if a message contains an Anthropic-format `thinking` block.
 185: 
 186:     Used to gate `count_tokens` requests so we send the same content
 187:     shape the assistant turn would produce. Per R4 #43.
 188:     """
 189:     if not isinstance(message, dict):
 190:         return False
 191:     content = message.get("content")
 192:     if not isinstance(content, list):
 193:         return False
 194:     for block in content:
 195:         if isinstance(block, dict) and block.get("type") in {"thinking", "redacted_thinking"}:
 196:             return True
 197:     return False
 198: 
 199: 
 200: # ============================================================
 201: # B-4 â€” roughTokenCountEstimationForBlock (R4 #44)
 202: # ============================================================
 203: 
 204: def rough_token_count_for_block(block: Any) -> int:
 205:     """Per-block-type token estimator.
 206: 
 207:     text/tool_use/tool_result/image â€” each has different size math.
 208:     Images are capped at IMAGE_MAX_TOKEN_SIZE per Anthropic billing.
 209:     """
 210:     if isinstance(block, str):
 211:         return estimate_message_tokens(block)
 212:     if not isinstance(block, dict):
 213:         return 0
 214:     btype = block.get("type")
 215:     if btype == "text":
 216:         return estimate_message_tokens(block.get("text", ""))
 217:     if btype == "tool_use":
 218:         # Tool name + input as JSON (dense, 2 bytes/token).
 219:         name_tokens = estimate_message_tokens(block.get("name", ""))
 220:         import json as _json
 221:         input_tokens = int(len(_json.dumps(block.get("input", {}))) / 2.0 + 0.5)
 222:         return name_tokens + input_tokens
 223:     if btype == "tool_result":
 224:         content = block.get("content", "")
 225:         if isinstance(content, list):
 226:             return sum(rough_token_count_for_block(c) for c in content)
 227:         return estimate_message_tokens(str(content))
 228:     if btype in {"image", "input_image"}:
 229:         return IMAGE_MAX_TOKEN_SIZE
 230:     if btype in {"thinking", "redacted_thinking"}:
 231:         return estimate_message_tokens(block.get("thinking", "") or block.get("data", ""))
 232:     return 0
 233: 
 234: 
 235: def rough_token_count_for_message(msg: Dict[str, Any]) -> int:
 236:     """Sum of `rough_token_count_for_block` for each block in a message."""
 237:     if not isinstance(msg, dict):
 238:         return 0
 239:     content = msg.get("content")
 240:     if isinstance(content, str):
 241:         return estimate_message_tokens(content)
 242:     if isinstance(content, list):
 243:         return sum(rough_token_count_for_block(b) for b in content)
 244:     return 0
 245: 
 246: 
 247: # ============================================================
 248: # TokenTracker â€” verbatim port of v4 + per-agent attribution
 249: # ============================================================
 250: 
 251: # Sentinel for distinguishing "not yet recorded" from "recorded as 0".
 252: _NO_USAGE_RECORD: Optional[Dict[str, int]] = None
 253: 
 254: 
 255: class TokenTracker:
 256:     """Thread-safe tracker for API token usage, cost, and cache hits per session.
 257: 
 258:     v5 extension over v4: per-agent attribution dict so parent and
 259:     sub-agent token costs can be reported separately while still rolling
 260:     up to the same `session_cost` total. Per Plan v3 Â§Block B + B-11.
 261: 
 262:     The agent_kind argument to `add()` is the attribution bucket key
 263:     (default "parent"; sub-agents pass "build", "explore", "verify",
 264:     etc. â€” the type-string from `subagent.spawn`).
 265:     """
 266: 
 267:     def __init__(self, config=None):
 268:         # `config` is injected so tests can build a TokenTracker without
 269:         # importing the runtime CONFIG singleton at module-import time.
 270:         # When None, we resolve CONFIG dynamically on every read so a
 271:         # test that `importlib.reload(runtime.config)` doesn't strand the
 272:         # tracker on a stale instance.
 273:         self._config_override = config
 274:         self._fixed_overhead: Optional[int] = None
 275:         self._lock = threading.Lock()
 276:         self.reset()
 277: 
 278:     @property
 279:     def _config(self):
 280:         """Resolve CONFIG lazily so reloads in tests don't strand us."""
 281:         if self._config_override is not None:
 282:             return self._config_override
 283:         from runtime.config import CONFIG as _CFG  # noqa: F401 â€” late import
 284:         return _CFG
 285: 
 286:     # --------------------------------------------------------
 287:     # Reset / state
 288:     # --------------------------------------------------------
 289: 
 290:     def reset(self):
 291:         """Reset all counters."""
 292:         with self._lock:
 293:             self._reset_unlocked()
 294: 
 295:     def _reset_unlocked(self):
 296:         self.session_input = 0
 297:         self.session_output = 0
 298:         self.session_total = 0
 299:         self.session_cache_read = 0
 300:         self.session_cache_write = 0
 301:         self.last_input = 0
 302:         self.last_output = 0
 303:         self.api_calls = 0
 304:         self.session_cost = 0.0
 305:         self.last_cost = 0.0
 306:         self._model_id = self._config.model_id
 307:         self._budget_warned = False
 308:         self._budget_stopped = False
 309:         # Per-agent attribution (Plan v3 Â§Block B). Parent always tracked
 310:         # by default; sub-agents accumulate under their type-string key.
 311:         self.parent_input_tokens = 0
 312:         self.parent_output_tokens = 0
 313:         self.parent_cost = 0.0
 314:         self.subagent_input_tokens: Dict[str, int] = {}
 315:         self.subagent_output_tokens: Dict[str, int] = {}
 316:         self.subagent_cost: Dict[str, float] = {}
 317:         # Last-usage record for tokenCountWithEstimation walks (B-8).
 318:         self._last_usage_record: Optional[Dict[str, int]] = None
 319: 
 320:     # --------------------------------------------------------
 321:     # Add usage (the singleton write path)
 322:     # --------------------------------------------------------
 323: 
 324:     def add(
 325:         self,
 326:         usage: Dict[str, int],
 327:         model_id: Optional[str] = None,
 328:         agent_kind: str = "parent",
 329:     ):
 330:         """Add usage from API response (thread-safe).
 331: 
 332:         agent_kind: attribution bucket. "parent" (default) for the main
 333:         agent loop; sub-agent type-strings ("build", "explore", "verify",
 334:         "plan", "review", "general") for spawned children. The session
 335:         rollup totals always include both.
 336:         """
 337:         input_tokens = int(usage.get("input_tokens", 0) or 0)
 338:         output_tokens = int(usage.get("output_tokens", 0) or 0)
 339:         cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
 340:         cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)
 341: 
 342:         with self._lock:
 343:             self.last_input = input_tokens
 344:             self.last_output = output_tokens
 345:             self.session_input += input_tokens
 346:             self.session_output += output_tokens
 347:             self.session_total = self.session_input + self.session_output
 348:             self.session_cache_read += cache_read
 349:             self.session_cache_write += cache_write
 350:             self.api_calls += 1
 351:             # B-8 â€” record last usage so estimators can walk back.
 352:             self._last_usage_record = dict(usage)
 353: 
 354:             mid = canonicalize_model_id(model_id or self._config.model_id)
 355:             if model_id:
 356:                 self._model_id = model_id
 357:             pricing = MODEL_COSTS.get(mid)
 358:             cost = 0.0
 359:             if pricing:
 360:                 base_input = pricing["input"]
 361:                 regular_input = max(0, input_tokens - cache_read - cache_write)
 362:                 cost = (
 363:                     (regular_input / 1000) * base_input
 364:                     + (cache_read / 1000) * base_input * 0.1
 365:                     + (cache_write / 1000) * base_input * 1.25
 366:                     + (output_tokens / 1000) * pricing["output"]
 367:                 )
 368:                 self.session_cost += cost
 369:                 self.last_cost = cost
 370:             else:
 371:                 if not hasattr(self, "_warned_models"):
 372:                     self._warned_models = set()
 373:                 if mid not in self._warned_models:
 374:                     self._warned_models.add(mid)
 375:                     logging.warning(
 376:                         f"TokenTracker: no pricing for model '{mid}' â€” cost will show as $0. "
 377:                         f"Add to MODEL_COSTS dict in runtime/tokens.py."
 378:                     )
 379:                 self.last_cost = 0.0
 380: 
 381:             # Per-agent attribution (additive â€” same singleton, separate buckets).
 382:             if agent_kind == "parent":
 383:                 self.parent_input_tokens += input_tokens
 384:                 self.parent_output_tokens += output_tokens
 385:                 self.parent_cost += cost
 386:             else:
 387:                 self.subagent_input_tokens[agent_kind] = (
 388:                     self.subagent_input_tokens.get(agent_kind, 0) + input_tokens
 389:                 )
 390:                 self.subagent_output_tokens[agent_kind] = (
 391:                     self.subagent_output_tokens.get(agent_kind, 0) + output_tokens
 392:                 )
 393:                 self.subagent_cost[agent_kind] = (
 394:                     self.subagent_cost.get(agent_kind, 0.0) + cost
 395:                 )
 396: 
 397:             # Budget gate (verbatim from v4).
 398:             limit = self._config.session_cost_limit
 399:             if limit > 0 and self.session_cost > 0:
 400:                 pct = self.session_cost / limit
 401:                 if pct >= 1.0 and not self._budget_stopped:
 402:                     self._budget_stopped = True
 403:                     logging.warning(
 404:                         f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
 405:                     )
 406:                 elif pct >= 0.8 and not self._budget_warned:
 407:                     self._budget_warned = True
 408:                     logging.warning(
 409:                         f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
 410:                     )
 411: 
 412:     # --------------------------------------------------------
 413:     # Read-only views (v4 verbatim)
 414:     # --------------------------------------------------------
 415: 
 416:     def is_over_budget(self) -> bool:
 417:         limit = self._config.session_cost_limit
 418:         return limit > 0 and self.session_cost >= limit
 419: 
 420:     def get_last(self) -> str:
 421:         return f"In:{self.last_input:,} Out:{self.last_output:,}"
 422: 
 423:     def get_session(self) -> str:
 424:         return (
 425:             f"In:{self.session_input:,} Out:{self.session_output:,} "
 426:             f"Total:{self.session_total:,}"
 427:         )
 428: 
 429:     def get_cache_savings_usd(self) -> float:
 430:         mid = canonicalize_model_id(self._model_id or self._config.model_id)
 431:         pricing = MODEL_COSTS.get(mid)
 432:         if not pricing or self.session_cache_read == 0:
 433:             return 0.0
 434:         full_price_per_1k = pricing["input"]
 435:         return (self.session_cache_read / 1000) * full_price_per_1k * 0.90
 436: 
 437:     def get_cost(self) -> str:
 438:         cost_str = (
 439:             f"${self.session_cost:.4f}"
 440:             if self.session_cost < 0.01
 441:             else f"${self.session_cost:.2f}"
 442:         )
 443:         if self.session_cache_read > 0 and self.session_input > 0:
 444:             cache_pct = min(100, (self.session_cache_read / self.session_input) * 100)
 445:             savings = self.get_cache_savings_usd()
 446:             cost_str += f" (cache {cache_pct:.0f}% | saved ~${savings:.4f})"
 447:         return cost_str
 448: 
 449:     def get_stats(self) -> Dict[str, Any]:
 450:         return {
 451:             "session_input": self.session_input,
 452:             "session_output": self.session_output,
 453:             "session_total": self.session_total,
 454:             "session_cache_read": self.session_cache_read,
 455:             "session_cache_write": self.session_cache_write,
 456:             "last_input": self.last_input,
 457:             "last_output": self.last_output,
 458:             "api_calls": self.api_calls,
 459:             "session_cost_usd": round(self.session_cost, 6),
 460:             "last_cost_usd": round(self.last_cost, 6),
 461:             "parent_input_tokens": self.parent_input_tokens,
 462:             "parent_output_tokens": self.parent_output_tokens,
 463:             "parent_cost_usd": round(self.parent_cost, 6),
 464:             "subagent_input_tokens": dict(self.subagent_input_tokens),
 465:             "subagent_output_tokens": dict(self.subagent_output_tokens),
 466:             "subagent_cost_usd": {k: round(v, 6) for k, v in self.subagent_cost.items()},
 467:         }
 468: 
 469:     def restore(self, stats: Dict[str, Any]):
 470:         """Restore counters from saved session metadata.
 471: 
 472:         Used by Block B+ SessionManager `/resume` to rehydrate cost
 473:         across sessions (Runnable cost-tracker.ts:87-175 / R11 N8).
 474:         """
 475:         with self._lock:
 476:             self.session_input = int(stats.get("session_input", 0))
 477:             self.session_output = int(stats.get("session_output", 0))
 478:             self.session_total = self.session_input + self.session_output
 479:             self.session_cache_read = int(stats.get("session_cache_read", 0))
 480:             self.session_cache_write = int(stats.get("session_cache_write", 0))
 481:             self.last_input = int(stats.get("last_input", 0))
 482:             self.last_output = int(stats.get("last_output", 0))
 483:             self.api_calls = int(stats.get("api_calls", 0))
 484:             self.session_cost = float(stats.get("session_cost_usd", 0.0))
 485:             self.last_cost = float(stats.get("last_cost_usd", 0.0))
 486:             self.parent_input_tokens = int(stats.get("parent_input_tokens", 0))
 487:             self.parent_output_tokens = int(stats.get("parent_output_tokens", 0))
 488:             self.parent_cost = float(stats.get("parent_cost_usd", 0.0))
 489:             self.subagent_input_tokens = dict(stats.get("subagent_input_tokens", {}))
 490:             self.subagent_output_tokens = dict(stats.get("subagent_output_tokens", {}))
 491:             self.subagent_cost = {
 492:                 k: float(v) for k, v in stats.get("subagent_cost_usd", {}).items()
 493:             }
 494: 
 495:     # --------------------------------------------------------
 496:     # B-8 / B-9 â€” context-token math derived from last response
 497:     # --------------------------------------------------------
 498: 
 499:     def final_context_tokens_from_last_response(self) -> int:
 500:         """Best-available estimate of the current context window size.
 501: 
 502:         Per R8 #16: Bedrock returns top-level `usage` only (no per-block
 503:         `cache_creation_input_tokens` breakdown). We use:
 504:           context = last_input + cache_read + cache_write
 505:         as a conservative upper bound for the next turn's prompt.
 506:         """
 507:         rec = self._last_usage_record
 508:         if not rec:
 509:             return self.session_input  # cold start fallback
 510:         return (
 511:             int(rec.get("input_tokens", 0))
 512:             + int(rec.get("cache_read_input_tokens", 0))
 513:             + int(rec.get("cache_creation_input_tokens", 0))
 514:         )
 515: 
 516:     def token_count_with_estimation(self, messages: List[Dict[str, Any]]) -> int:
 517:         """Estimate token count for a message list.
 518: 
 519:         Per R8 #15. Walks back to the last usage record; if it covers
 520:         the same prefix-length as `messages`, reuse the recorded value
 521:         (correct under prompt caching). Otherwise fall back to the
 522:         block-level rough estimator.
 523:         """
 524:         if not messages:
 525:             return 0
 526:         if self._last_usage_record is not None:
 527:             recorded = self._last_usage_record.get("input_tokens", 0)
 528:             if recorded > 0:
 529:                 return int(recorded)
 530:         return sum(rough_token_count_for_message(m) for m in messages)
 531: 
 532: 
 533: # Module-level singleton (parity with v4 `TOKENS = TokenTracker()`).
 534: TOKENS = TokenTracker()
 535: 
 536: 
 537: # Block B+ (PORT_LOG #054): atexit cost-flush via cleanup_registry.
 538: # Per Runnable costHook.ts:6-22 (R11 N14). On normal exit / SIGINT /
 539: # SIGTERM, log the final session cost so operators can audit
 540: # post-hoc even if the user closes the notebook abruptly.
 541: def _flush_cost_on_exit() -> None:
 542:     if TOKENS.session_cost > 0:
 543:         logging.warning(
 544:             f"session-final cost: {TOKENS.get_cost()} "
 545:             f"({TOKENS.api_calls} API calls, "
 546:             f"in={TOKENS.session_input:,} out={TOKENS.session_output:,})"
 547:         )
 548: 
 549: 
 550: try:  # pragma: no cover â€” registration-time best-effort
 551:     from runtime.cleanup_registry import register as _register_cleanup
 552:     _register_cleanup(_flush_cost_on_exit)
 553: except Exception:
 554:     pass
 555: 
 556: 
 557: __all__ = [
 558:     "ToolResult",
 559:     "MODEL_COSTS",
 560:     "EXCLUDED_MODELS_FOR_CACHE_BREAK",
 561:     "IMAGE_MAX_TOKEN_SIZE",
 562:     "TokenTracker",
 563:     "TOKENS",
 564:     "bytes_per_token_for_file_type",
 565:     "estimate_message_tokens",
 566:     "has_thinking_blocks",
 567:     "rough_token_count_for_block",
 568:     "rough_token_count_for_message",
 569:     "canonicalize_model_id",
 570: ]

 succeeded in 948ms:
compact_v5/MAIN/agent\core\compactor.py:13:At 80% of max context, `should_compact()` returns True; the chat loop
compact_v5/MAIN/agent\core\compactor.py:14:calls `Compactor.run(messages, client)` which prunes oversized tool
compact_v5/MAIN/agent\core\compactor.py:245:    def should_compact(cls, messages: List[Dict[str, Any]], max_tokens: int) -> bool:
compact_v5/MAIN/agent\core\compactor.py:465:        if not cls.should_compact(messages, max_tokens):
compact_v5/MAIN/agent\core\compactor.py:498:def apply_cache_control_to_blocks(
compact_v5/MAIN/agent\core\compactor.py:530:def count_tokens_via_haiku_fallback(
compact_v5/MAIN/agent\core\compactor.py:574:AUTO_COMPACT = AutoCompactCircuitBreaker()
compact_v5/MAIN/agent\core\compactor.py:581:    "AUTO_COMPACT",
compact_v5/MAIN/agent\core\compactor.py:582:    "apply_cache_control_to_blocks",
compact_v5/MAIN/agent\core\compactor.py:583:    "count_tokens_via_haiku_fallback",
compact_v5/MAIN/agent\tests\integration\test_block_a.py:9:  - Compactor.run end-to-end (mock client returns canned summary).
compact_v5/MAIN/agent\tests\integration\test_block_a.py:11:  - apply_cache_control_to_blocks marks last block ephemeral.
compact_v5/MAIN/agent\tests\integration\test_block_a.py:12:  - B-2 count_tokens_via_haiku_fallback (mock mode + real path stub).
compact_v5/MAIN/agent\tests\integration\test_block_a.py:61:    assert Compactor.should_compact(msgs, max_tokens=100_000)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:63:    assert not Compactor.should_compact(msgs, max_tokens=400_000)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:70:    assert not Compactor.should_compact(msgs, max_tokens=200_000)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:170:    """Compactor.run: prune → summarize → compact, all in one."""
compact_v5/MAIN/agent\tests\integration\test_block_a.py:184:    result = Compactor.run(client, msgs, max_tokens=100_000)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:197:    result = Compactor.run(client, msgs, max_tokens=200_000)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:241:# T1 — apply_cache_control_to_blocks
compact_v5/MAIN/agent\tests\integration\test_block_a.py:245:    from core.compactor import apply_cache_control_to_blocks
compact_v5/MAIN/agent\tests\integration\test_block_a.py:248:    out = apply_cache_control_to_blocks(blocks)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:254:    from core.compactor import apply_cache_control_to_blocks
compact_v5/MAIN/agent\tests\integration\test_block_a.py:257:    out = apply_cache_control_to_blocks(blocks, cache_break_at=0)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:264:    from core.compactor import apply_cache_control_to_blocks
compact_v5/MAIN/agent\tests\integration\test_block_a.py:265:    assert apply_cache_control_to_blocks([]) == []
compact_v5/MAIN/agent\tests\integration\test_block_a.py:269:# B-2 — count_tokens_via_haiku_fallback
compact_v5/MAIN/agent\tests\integration\test_block_a.py:273:    from core.compactor import count_tokens_via_haiku_fallback
compact_v5/MAIN/agent\tests\integration\test_block_a.py:278:    n = count_tokens_via_haiku_fallback(msgs, client)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:284:    from core.compactor import count_tokens_via_haiku_fallback
compact_v5/MAIN/agent\tests\integration\test_block_a.py:285:    assert count_tokens_via_haiku_fallback([], None) is None

web search: 
web search: Anthropic Bedrock messages must start with user role
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"TOKENS\\.add\\(|add\\(response\\.usage\" compact_v5/MAIN/agent" in D:\Github\sagemaker-coding-agent
 succeeded in 488ms:
compact_v5/MAIN/agent\core\query_engine.py:165:        # Block B: per-agent attribution key for TOKENS.add(). "parent" by
compact_v5/MAIN/agent\core\query_engine.py:376:                _TOKENS.add(
compact_v5/MAIN/agent\core\compactor.py:267:        don't pay main-model rates. Per ADR-022 / B+5: TOKENS.add()
compact_v5/MAIN/agent\core\compactor.py:309:        - Attribute advisor tokens via TOKENS.add(agent_kind='advisor').
compact_v5/MAIN/agent\core\compactor.py:360:                    TOKENS.add(
compact_v5/MAIN/agent\subagent\spawn.py:81:    Block B: `agent_type` is forwarded as `agent_kind` so TOKENS.add()
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:106:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:147:        TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:156:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:305:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:311:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:454:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:487:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_a.py:13:  - B+5 advisor sub-cost attribution via TOKENS.add(agent_kind="advisor").
compact_v5/MAIN/agent\tests\integration\test_block_b.py:53:    TOKENS.add({"input_tokens": 100, "output_tokens": 50}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:54:    TOKENS.add({"input_tokens": 200, "output_tokens": 75}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:150:    TOKENS.add({"input_tokens": 100, "output_tokens": 50}, model_id="test-model", agent_kind="parent")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:151:    TOKENS.add({"input_tokens": 80, "output_tokens": 40}, model_id="test-model", agent_kind="build")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:152:    TOKENS.add({"input_tokens": 60, "output_tokens": 30}, model_id="test-model", agent_kind="explore")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:153:    TOKENS.add({"input_tokens": 50, "output_tokens": 25}, model_id="test-model", agent_kind="parent")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:206:    TOKENS.add({"input_tokens": 100, "output_tokens": 30}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:207:    TOKENS.add({"input_tokens": 120, "output_tokens": 35}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:208:    TOKENS.add({"input_tokens": 140, "output_tokens": 40}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:399:    TOKENS.add({
compact_v5/MAIN/agent\tests\integration\test_block_b.py:466:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_d.py:143:    TOKENS.add(

codex
I’m checking token accounting call sites now to verify whether compactor summary usage is counted exactly once and whether advisor attribution can leak into parent totals.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/core/query_engine.py'; "'$i=1; Get-Content $p | ForEach-Object { if($i -ge 320 -and $i -le 420){ '"'{0,4}: {1}' -f "'$i, $_}; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 472ms:
 320: 
 321:             # Phase 7 wiring contract: per-turn deferral + discovery merge.
 322:             visible_tools, deferred_names = apply_tool_search_deferral(
 323:                 tools, enabled=True,
 324:             )
 325:             if self._discovered_tool_names:
 326:                 # Promote previously-discovered tools from deferred â†’ visible.
 327:                 discovered = {n for n in self._discovered_tool_names if n in deferred_names}
 328:                 if discovered:
 329:                     promoted = [
 330:                         t for t in tools
 331:                         if t.name in discovered and t.name not in {v.name for v in visible_tools}
 332:                     ]
 333:                     visible_tools = visible_tools + promoted
 334:                     deferred_names = [n for n in deferred_names if n not in discovered]
 335: 
 336:             # If any names remain deferred, surface them as a system reminder
 337:             # so the model knows they exist and how to load them.
 338:             turn_messages = list(self.messages)
 339:             if deferred_names:
 340:                 turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)
 341: 
 342:             # Bedrock invocation.
 343:             try:
 344:                 response = self.client.chat(
 345:                     messages=turn_messages,
 346:                     system=effective_system_prompt,
 347:                     tools=_build_tools_api_payload(visible_tools),
 348:                     max_tokens=max_tokens,
 349:                     temperature=temperature,
 350:                     thinking_enabled=thinking_enabled,
 351:                     thinking_budget=thinking_budget,
 352:                 )
 353:             except Exception as exc:  # noqa: BLE001 â€” classify and surface
 354:                 category, recovery, debug = ErrorClassifier.classify(exc)
 355:                 output_fn(f"[Bedrock {category}: {debug}]")
 356:                 if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
 357:                     stop_reason = "context_overflow"
 358:                 else:
 359:                     stop_reason = "fatal_error"
 360:                 return QueryResult(
 361:                     text=last_text,
 362:                     messages=list(self.messages),
 363:                     stop_reason=stop_reason,
 364:                     turns_used=turns_used,
 365:                     budget_used=self.budget.used(),
 366:                     error=f"{category}: {debug}",
 367:                 )
 368: 
 369:             turns_used += 1
 370: 
 371:             # Block B (PORT_LOG #039+#040): record token usage + per-agent
 372:             # attribution. "parent" or sub-agent type-string. Best-effort â€”
 373:             # never break the agent loop if the singleton import fails.
 374:             try:
 375:                 from runtime.tokens import TOKENS as _TOKENS
 376:                 _TOKENS.add(
 377:                     response.usage or {},
 378:                     model_id=getattr(self.client, "model_id", None),
 379:                     agent_kind=self.agent_kind,
 380:                 )
 381:                 # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
 382:                 # warning. v4 sagemaker_agent.py:8787 prints
 383:                 #   `[Cost ${session_cost} passed budget ${limit} â€” continuing.]`
 384:                 # NOT a hard halt â€” per user 2026-05-03 update to plan v3,
 385:                 # v5 matches v4 UX: warn and continue. True hard halt is at
 386:                 # cloud-budget level (AWS Budget Action / GCP).
 387:                 from runtime.config import CONFIG as _CFG
 388:                 limit = getattr(_CFG, "session_cost_limit", 0.0)
 389:                 # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
 390:                 # the warning (`>` would skip parity-100% cases).
 391:                 if limit > 0 and _TOKENS.session_cost >= limit:
 392:                     if not getattr(self, "_warned_over_budget", False):
 393:                         output_fn(
 394:                             f"[Cost ${_TOKENS.session_cost:.4f} passed "
 395:                             f"budget ${limit:.2f} â€” continuing.]"
 396:                         )
 397:                         self._warned_over_budget = True
 398:             except Exception:
 399:                 pass
 400: 
 401:             # Append assistant turn (text + tool_use blocks, plus thinking).
 402:             assistant_content = self._build_assistant_content(response)
 403:             self.messages.append({"role": "assistant", "content": assistant_content})
 404: 
 405:             if response.text:
 406:                 last_text = response.text
 407: 
 408:             # Stop conditions: end_turn / no tool_use blocks â†’ final answer.
 409:             if not response.tool_calls:
 410:                 stop_reason = "end_turn"
 411:                 if response.text:
 412:                     output_fn(response.text)
 413:                 break
 414: 
 415:             # Tool dispatch â€” emit one tool_result per tool_use call.
 416:             tool_results: List[Dict[str, Any]] = []
 417:             for call in response.tool_calls:
 418:                 tool = find_tool_by_name(tools, call.name)
 419:                 if tool is None:
 420:                     # Unknown tool name â€” return error to model so it can

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"Compactor\\.run|create_llm_summary\\(|AUTO_COMPACT|apply_cache_control_to_blocks\\(\" compact_v5/MAIN/agent -g '"'!**/tests/**'"'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"compactor|compact\" compact_v5/MAIN/agent/core -g '"'!**/tests/**'"'" in D:\Github\sagemaker-coding-agent
 succeeded in 446ms:
compact_v5/MAIN/agent/core\retry.py:4:(which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).
compact_v5/MAIN/agent/core\errors.py:4:(which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).
compact_v5/MAIN/agent/core\errors.py:40:      - "compact_retry":     prompt-too-long; caller should compact and retry
compact_v5/MAIN/agent/core\errors.py:61:            return BedrockErrorCategory.CONTEXT_OVERFLOW, "compact_retry", str(exc)[:200]
compact_v5/MAIN/agent/core\query_engine.py:24:- Microcompact / context_collapse — Phase 11 UX (PS Issue #4 widget surface).
compact_v5/MAIN/agent/core\query_engine.py:25:- 2-stage smart compaction (prune + LLM summary) — Phase 11.
compact_v5/MAIN/agent/core\query_engine.py:30:  doesn't reset on compact (no compact in Phase 8).
compact_v5/MAIN/agent/core\compactor.py:1:"""Block A — Compactor + auto-compact circuit breaker + Runnable cache_edits.
compact_v5/MAIN/agent/core\compactor.py:3:v5 port of v4's `Compactor` class (compact_v4/MAIN/agent/sagemaker_agent.py
compact_v5/MAIN/agent/core\compactor.py:5:  - Auto-compact circuit breaker (Hermes-style cooldown)
compact_v5/MAIN/agent/core\compactor.py:10:    per ADR-022 — auxiliary compaction-summary model)
compact_v5/MAIN/agent/core\compactor.py:13:At 80% of max context, `should_compact()` returns True; the chat loop
compact_v5/MAIN/agent/core\compactor.py:36:    """Outcome of a compact() call."""
compact_v5/MAIN/agent/core\compactor.py:51:    """Prevents auto-compact runaway by enforcing a cooldown window.
compact_v5/MAIN/agent/core\compactor.py:53:    Pattern: when auto-compact fires, mark the timestamp. If
compact_v5/MAIN/agent/core\compactor.py:55:    False — caller must continue without re-compacting. Hermes
compact_v5/MAIN/agent/core\compactor.py:56:    run_agent.py uses this to prevent compact-after-compact loops where
compact_v5/MAIN/agent/core\compactor.py:57:    a freshly-compacted context still trips the 80% trigger because
compact_v5/MAIN/agent/core\compactor.py:60:    Per Wave-5-DEEP H5 (auto-compact circuit breaker; A28 cache-invariant).
compact_v5/MAIN/agent/core\compactor.py:71:        """True iff a compact attempt is allowed right now.
compact_v5/MAIN/agent/core\compactor.py:81:                    f"auto-compact session cap reached "
compact_v5/MAIN/agent/core\compactor.py:88:                    f"auto-compact cooldown active "
compact_v5/MAIN/agent/core\compactor.py:95:        """Mark a compact attempt — caller calls this after a successful
compact_v5/MAIN/agent/core\compactor.py:96:        OR failed compact so cooldown applies either way (a failed
compact_v5/MAIN/agent/core\compactor.py:97:        compact still consumed time + tokens)."""
compact_v5/MAIN/agent/core\compactor.py:113:    """Smart context compaction: prune oversized tool results, then
compact_v5/MAIN/agent/core\compactor.py:120:    - Auxiliary-model routing (v4.9.4 compaction_model) preserved with
compact_v5/MAIN/agent/core\compactor.py:241:    # Should compact?
compact_v5/MAIN/agent/core\compactor.py:245:    def should_compact(cls, messages: List[Dict[str, Any]], max_tokens: int) -> bool:
compact_v5/MAIN/agent/core\compactor.py:265:        Per v4.9.4: when CONFIG.compaction_model is set, build a
compact_v5/MAIN/agent/core\compactor.py:272:        aux_model = (getattr(CONFIG, "compaction_model", "") or "").strip()
compact_v5/MAIN/agent/core\compactor.py:286:            logging.info(f"[COMPACT] Using auxiliary compaction model: {aux_model}")
compact_v5/MAIN/agent/core\compactor.py:308:        - Optionally route through CONFIG.compaction_model (advisor).
compact_v5/MAIN/agent/core\compactor.py:437:    def compact(
compact_v5/MAIN/agent/core\compactor.py:463:        """End-to-end: prune → summarize → compact. Single entry point."""
compact_v5/MAIN/agent/core\compactor.py:465:        if not cls.should_compact(messages, max_tokens):
compact_v5/MAIN/agent/core\compactor.py:468:                error="compact not needed (under 80% trigger)",
compact_v5/MAIN/agent/core\compactor.py:483:        new_messages = cls.compact(pruned, summary)
compact_v5/MAIN/agent/core\compactor.py:507:    on subsequent turns. Block A's compaction output is the natural
compact_v5/MAIN/agent/core\budget.py:4:`compact_v4/MAIN/agent/sagemaker_agent.py:8190`. v4 itself adopted this

 succeeded in 471ms:
compact_v5/MAIN/agent\core\compactor.py:14:calls `Compactor.run(messages, client)` which prunes oversized tool
compact_v5/MAIN/agent\core\compactor.py:300:    def create_llm_summary(
compact_v5/MAIN/agent\core\compactor.py:474:        summary = cls.create_llm_summary(client, pruned)
compact_v5/MAIN/agent\core\compactor.py:498:def apply_cache_control_to_blocks(
compact_v5/MAIN/agent\core\compactor.py:574:AUTO_COMPACT = AutoCompactCircuitBreaker()
compact_v5/MAIN/agent\core\compactor.py:581:    "AUTO_COMPACT",

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/core/query_engine.py'; "'$i=1; Get-Content $p | ForEach-Object { if($i -le 70){ '"'{0,4}: {1}' -f "'$i, $_}; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 448ms:
   1: """V5 core/query_engine.py â€” main agent loop (Phase 8 deliverable, ADR-014).
   2: 
   3: Per ADR-014: minimal, focused port of Runnable's `QueryEngine.ts` (1295 LOC)
   4: adapted to the v5 .ipynb shape. v4's monolithic `Agent.run` (~1500 LOC) is
   5: replaced by this ~400 LOC module with explicit IN-SCOPE / OUT-OF-SCOPE.
   6: 
   7: PORT_LOG: #019.
   8: 
   9: IN SCOPE (Phase 8):
  10: - Per-turn loop with end_turn / max_turns / budget exhausted exits.
  11: - IterationBudget gate at the top of each turn (shared with sub-agents).
  12: - Phase 7 deferred-loading wiring contract:
  13:     * `apply_tool_search_deferral(tools, enabled=True)` per turn.
  14:     * `tool_search_discovered_names()` extraction from tool_search results.
  15:     * Discovered names are added to the next turn's tools= API param.
  16: - Tool dispatch via `find_tool_by_name(...).execute(args, context)`.
  17: - tool_use â†’ tool_result message accumulation in the model-visible
  18:   conversation buffer.
  19: - Bedrock invocation through `BedrockClient.chat(...)`.
  20: - System prompt assembly via `prompt.build_system_prompt(ctx)`.
  21: - run_one_turn(...) helper for unit tests (single-turn, no loop).
  22: 
  23: OUT OF SCOPE â€” explicitly deferred to later phases (per ADR-014):
  24: - Microcompact / context_collapse â€” Phase 11 UX (PS Issue #4 widget surface).
  25: - 2-stage smart compaction (prune + LLM summary) â€” Phase 11.
  26: - Skill auto-trigger â€” Phase 10 (`SKILLS.discover_relevant`).
  27: - Plan mode injection of skills into prompt â€” Phase 10.
  28: - Sub-agent forkSubagent â€” Phase 9 (`subagent/spawn.py`).
  29: - File-read state tracking â€” Phase 4 already lands this; engine respects but
  30:   doesn't reset on compact (no compact in Phase 8).
  31: - Diminishing-returns / repetition guard â€” deferred.
  32: - Notebook UX (output_fn callback contract) â€” Phase 11 owns the UI shape;
  33:   Phase 8 takes a `output_fn: Callable[[str], None] = print` so tests can
  34:   capture, but real notebook integration lives in Phase 11.
  35: 
  36: The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
  37: concurrent `run()` calls on the same engine are NOT supported (matches v4).
  38: """
  39: from __future__ import annotations
  40: 
  41: import json
  42: import logging
  43: from dataclasses import dataclass, field
  44: from typing import Any, Callable, Dict, List, Optional, Set, Tuple
  45: 
  46: from .budget import IterationBudget
  47: from .errors import BedrockErrorCategory, ErrorClassifier
  48: 
  49: 
  50: # ============================================================
  51: # Result envelope
  52: # ============================================================
  53: 
  54: @dataclass
  55: class QueryResult:
  56:     """Outcome of a `QueryEngine.run(...)` call.
  57: 
  58:     `text`           â€” final assistant text (last end_turn turn's text block).
  59:     `messages`       â€” full message buffer including the user turn that
  60:                        triggered this call. Caller may discard or persist.
  61:     `stop_reason`    â€” "end_turn" | "max_turns" | "budget_exhausted" |
  62:                        "context_overflow" | "fatal_error".
  63:     `turns_used`     â€” count of model turns executed during this run.
  64:     `budget_used`    â€” IterationBudget.used() snapshot at exit.
  65:     `error`          â€” short message when stop_reason indicates failure.
  66:     """
  67:     text: str = ""
  68:     messages: List[Dict[str, Any]] = field(default_factory=list)
  69:     stop_reason: str = ""
  70:     turns_used: int = 0

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/tests/integration/test_block_a.py'; (Get-Content "'$p).Length' in D:\Github\sagemaker-coding-agent
 succeeded in 463ms:
354

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'pytest -q compact_v5/MAIN/agent/tests/integration/test_block_a.py' in D:\Github\sagemaker-coding-agent
2026-05-03T03:35:14.314239Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.5 seconds
Output:
pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ pytest -q compact_v5/MAIN/agent/tests/integration/test_block_a.py
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (pytest:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 exited 1 in 539ms:
pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ pytest -q compact_v5/MAIN/agent/tests/integration/test_block_a.py
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (pytest:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/core/compactor.py'; "'$i=1; Get-Content $p | ForEach-Object { if($i -ge 188 -and $i -le 239){ '"'{0,4}: {1}' -f "'$i, $_}; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 436ms:
 188:         for msg in pruned:
 189:             content = msg.get("content")
 190:             if isinstance(content, list):
 191:                 for item in content:
 192:                     if isinstance(item, dict) and item.get("type") == "tool_use":
 193:                         tool_name_map[item.get("id", "")] = item.get("name", "")
 194: 
 195:         # Walk most-recent â†’ oldest; protect the last PROTECT_TOKENS worth.
 196:         running_tokens = 0
 197:         tokens_saved = 0
 198:         for msg in reversed(pruned):
 199:             content = msg.get("content")
 200:             if not isinstance(content, list):
 201:                 running_tokens += cls.estimate_tokens(msg)
 202:                 continue
 203:             for block in content:
 204:                 if not (isinstance(block, dict) and block.get("type") == "tool_result"):
 205:                     continue
 206:                 tool_name = tool_name_map.get(block.get("tool_use_id", ""), "")
 207:                 if tool_name in cls.PROTECTED_TOOLS:
 208:                     continue
 209:                 inner = block.get("content")
 210:                 if isinstance(inner, str):
 211:                     block_tokens = cls.estimate_tokens(inner)
 212:                     running_tokens += block_tokens
 213:                     if running_tokens > cls.PRUNE_PROTECT_TOKENS \
 214:                        and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
 215:                         head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
 216:                         tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
 217:                         new_text = (
 218:                             f"{head}\n... [pruned "
 219:                             f"{len(inner) - len(head) - len(tail):,} chars] ...\n{tail}"
 220:                         )
 221:                         block["content"] = new_text
 222:                         tokens_saved += cls.estimate_tokens(inner) - cls.estimate_tokens(new_text)
 223:                 elif isinstance(inner, list):
 224:                     for sub in inner:
 225:                         if isinstance(sub, dict) and sub.get("type") == "text":
 226:                             txt = sub.get("text", "")
 227:                             running_tokens += cls.estimate_tokens(txt)
 228:                             if running_tokens > cls.PRUNE_PROTECT_TOKENS \
 229:                                and len(txt) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
 230:                                 head = txt[: cls.SUMMARY_TOOL_RESULT_HEAD]
 231:                                 tail = txt[-cls.SUMMARY_TOOL_RESULT_TAIL :]
 232:                                 new_text = (
 233:                                     f"{head}\n... [pruned "
 234:                                     f"{len(txt) - len(head) - len(tail):,} chars] ...\n{tail}"
 235:                                 )
 236:                                 sub["text"] = new_text
 237:                                 tokens_saved += cls.estimate_tokens(txt) - cls.estimate_tokens(new_text)
 238:         return pruned, tokens_saved
 239: 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/core/compactor.py'; "'$i=1; Get-Content $p | ForEach-Object { if($i -ge 343 -and $i -le 431){ '"'{0,4}: {1}' -f "'$i, $_}; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 462ms:
 343:         attempts = 0
 344:         while attempts <= cls.MAX_PTL_RETRIES:
 345:             try:
 346:                 response = summary_client.chat(
 347:                     messages=summary_input,
 348:                     system=SUMMARY_SYSTEM_PROMPT,
 349:                     tools=None,
 350:                     max_tokens=2000,
 351:                     temperature=0.0,
 352:                 )
 353:                 if response and response.usage:
 354:                     # B+5 (ADR-022 remap): attribute advisor cost separately.
 355:                     agent_kind = (
 356:                         "advisor"
 357:                         if summary_client is not client
 358:                         else "parent"
 359:                     )
 360:                     TOKENS.add(
 361:                         response.usage,
 362:                         model_id=getattr(summary_client, "model_id", None),
 363:                         agent_kind=agent_kind,
 364:                     )
 365:                 if response and response.text:
 366:                     return response.text
 367:                 return None
 368:             except Exception as exc:  # noqa: BLE001
 369:                 err = str(exc).lower()
 370:                 is_ptl = ("prompt" in err and "long" in err) \
 371:                     or "too many tokens" in err
 372:                 if not is_ptl:
 373:                     logging.warning(f"[COMPACT] LLM summary failed: {exc}")
 374:                     return None
 375:                 attempts += 1
 376:                 summary_input = cls._truncate_head_for_ptl_retry(summary_input)
 377:                 if not summary_input:
 378:                     logging.warning("[COMPACT] PTL retries exhausted")
 379:                     return None
 380:         return None
 381: 
 382:     @classmethod
 383:     def _prune_tool_results_for_summary(
 384:         cls,
 385:         messages: List[Dict[str, Any]],
 386:     ) -> List[Dict[str, Any]]:
 387:         """Cheap pre-LLM pass: drop oversized tool_result bodies."""
 388:         out: List[Dict[str, Any]] = []
 389:         for msg in messages:
 390:             content = msg.get("content")
 391:             if not isinstance(content, list):
 392:                 out.append(msg)
 393:                 continue
 394:             new_blocks: List[Any] = []
 395:             mutated = False
 396:             for block in content:
 397:                 if not (isinstance(block, dict) and block.get("type") == "tool_result"):
 398:                     new_blocks.append(block)
 399:                     continue
 400:                 inner = block.get("content")
 401:                 if isinstance(inner, str) and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
 402:                     head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
 403:                     tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
 404:                     new_block = dict(block)
 405:                     new_block["content"] = (
 406:                         f"{head}\n... [pruned for summary] ...\n{tail}"
 407:                     )
 408:                     new_blocks.append(new_block)
 409:                     mutated = True
 410:                 else:
 411:                     new_blocks.append(block)
 412:             if mutated:
 413:                 new_msg = dict(msg)
 414:                 new_msg["content"] = new_blocks
 415:                 out.append(new_msg)
 416:             else:
 417:                 out.append(msg)
 418:         return out
 419: 
 420:     @classmethod
 421:     def _truncate_head_for_ptl_retry(
 422:         cls,
 423:         messages: List[Dict[str, Any]],
 424:     ) -> Optional[List[Dict[str, Any]]]:
 425:         """Drop the first 25% of messages so PTL retry has a smaller
 426:         input. Returns None when input is already minimal."""
 427:         if len(messages) < 4:
 428:             return None
 429:         drop_n = max(1, len(messages) // 4)
 430:         return messages[drop_n:]
 431: 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/core/compactor.py'; "'$i=1; Get-Content $p | ForEach-Object { if($i -ge 70 -and $i -le 101){ '"'{0,4}: {1}' -f "'$i, $_}; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 418ms:
  70:     def should_attempt(self) -> Tuple[bool, str]:
  71:         """True iff a compact attempt is allowed right now.
  72: 
  73:         Returns (allowed, reason). When False, the reason explains why
  74:         (session cap hit / cooldown active) so the caller can surface
  75:         a clear log message. Session cap checked FIRST â€” once exhausted,
  76:         no further attempts make sense regardless of cooldown.
  77:         """
  78:         with self._lock:
  79:             if self._session_count >= self.max_per_session:
  80:                 return False, (
  81:                     f"auto-compact session cap reached "
  82:                     f"({self._session_count}/{self.max_per_session})"
  83:                 )
  84:             now = time.time()
  85:             since = now - self._last_attempt
  86:             if self._last_attempt > 0 and since < self.cooldown_seconds:
  87:                 return False, (
  88:                     f"auto-compact cooldown active "
  89:                     f"({since:.0f}s elapsed, "
  90:                     f"{self.cooldown_seconds}s required)"
  91:                 )
  92:             return True, ""
  93: 
  94:     def record_attempt(self) -> None:
  95:         """Mark a compact attempt â€” caller calls this after a successful
  96:         OR failed compact so cooldown applies either way (a failed
  97:         compact still consumed time + tokens)."""
  98:         with self._lock:
  99:             self._last_attempt = time.time()
 100:             self._session_count += 1
 101: 

codex
I’ve identified a few concrete parity regressions and one concurrency risk that affect the verdict; I’m validating line-precise evidence now and then I’ll give the three-axis verdict plus final approve/reject outcome.
web search: 
web search: 
codex
1. **HIGH**: PTL retry can produce Bedrock-invalid message starts and abort compaction early.  
   In `_truncate_head_for_ptl_retry`, retries just slice the head and may start with `assistant`, unlike v4 which reinserted a user marker for Bedrock-safe retries. That means a PTL retry can turn into a non-PTL validation failure and immediately return `None`, hurting long-session recovery.  
   Evidence: [compactor.py:421](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:421), [compactor.py:430](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:430), [compactor.py:372](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:372), parity reference [v4_compactor_section.txt:189](C:\Users\winst\AppData\Local\Temp\v4_compactor_section.txt:189).

2. **MEDIUM**: `prune_tool_outputs` dropped v4’s `PRUNE_MIN_SAVINGS` rollback behavior, despite keeping the constant.  
   v4 returned original messages when savings were too small; v5 always returns pruned output, which can reduce fidelity for marginal token wins.  
   Evidence: [compactor.py:127](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:127), [compactor.py:238](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:238), parity reference [v4_compactor_section.txt:84](C:\Users\winst\AppData\Local\Temp\v4_compactor_section.txt:84).

3. **MEDIUM**: Circuit-breaker API is lock-protected internally but not atomic across check+record, so concurrent callers can both pass `should_attempt()` before either `record_attempt()`.  
   This weakens cooldown/session-cap guarantees under concurrency.  
   Evidence: [compactor.py:70](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:70), [compactor.py:94](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:94).

4. **MEDIUM**: Block A features are mostly module-local and not wired into runtime flow in this tree (`AUTO_COMPACT`, `apply_cache_control_to_blocks`, `count_tokens_via_haiku_fallback` have no non-test call sites).  
   This looks like undeclared partial-integration/stub pattern versus “ships” language.  
   Evidence: [compactor.py:498](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:498), [compactor.py:530](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:530), [compactor.py:574](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:574).

**Axis A verdict**: **CHANGES_REQUESTED**  
`estimate_tokens` delegation is correct; advisor attribution appears single-counted correctly in current flow. Main regressions are PTL retry resilience and compaction-prune parity behavior, plus CB concurrency gap.

**Axis B verdict**: **DRIFTED**  
Compared with v4, long-session hardening regressed in retry handling, and Bedrock cache-edits parity for sub-agents is not evidenced as integrated (helper exists but not wired).

**Axis C verdict**: Coverage is **partial**.  
Compactor/B+5 are implemented and tested; auto-compact/cache_edits/B-2 are present but appear unintegrated in non-test runtime usage.  
`UNDECLARED_PATTERN`: helper-only shipment without integration hooks.

**FINAL**: **REJECT**

Could not independently rerun tests here because `pytest` is not installed in this shell.
2026-05-03T03:36:17.396313Z ERROR codex_core::session: failed to record rollout items: thread 019debe5-d275-7e72-ac39-b0edebd9cfcd not found
tokens used
59,740
1. **HIGH**: PTL retry can produce Bedrock-invalid message starts and abort compaction early.  
   In `_truncate_head_for_ptl_retry`, retries just slice the head and may start with `assistant`, unlike v4 which reinserted a user marker for Bedrock-safe retries. That means a PTL retry can turn into a non-PTL validation failure and immediately return `None`, hurting long-session recovery.  
   Evidence: [compactor.py:421](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:421), [compactor.py:430](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:430), [compactor.py:372](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:372), parity reference [v4_compactor_section.txt:189](C:\Users\winst\AppData\Local\Temp\v4_compactor_section.txt:189).

2. **MEDIUM**: `prune_tool_outputs` dropped v4’s `PRUNE_MIN_SAVINGS` rollback behavior, despite keeping the constant.  
   v4 returned original messages when savings were too small; v5 always returns pruned output, which can reduce fidelity for marginal token wins.  
   Evidence: [compactor.py:127](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:127), [compactor.py:238](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:238), parity reference [v4_compactor_section.txt:84](C:\Users\winst\AppData\Local\Temp\v4_compactor_section.txt:84).

3. **MEDIUM**: Circuit-breaker API is lock-protected internally but not atomic across check+record, so concurrent callers can both pass `should_attempt()` before either `record_attempt()`.  
   This weakens cooldown/session-cap guarantees under concurrency.  
   Evidence: [compactor.py:70](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:70), [compactor.py:94](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:94).

4. **MEDIUM**: Block A features are mostly module-local and not wired into runtime flow in this tree (`AUTO_COMPACT`, `apply_cache_control_to_blocks`, `count_tokens_via_haiku_fallback` have no non-test call sites).  
   This looks like undeclared partial-integration/stub pattern versus “ships” language.  
   Evidence: [compactor.py:498](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:498), [compactor.py:530](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:530), [compactor.py:574](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\compactor.py:574).

**Axis A verdict**: **CHANGES_REQUESTED**  
`estimate_tokens` delegation is correct; advisor attribution appears single-counted correctly in current flow. Main regressions are PTL retry resilience and compaction-prune parity behavior, plus CB concurrency gap.

**Axis B verdict**: **DRIFTED**  
Compared with v4, long-session hardening regressed in retry handling, and Bedrock cache-edits parity for sub-agents is not evidenced as integrated (helper exists but not wired).

**Axis C verdict**: Coverage is **partial**.  
Compactor/B+5 are implemented and tested; auto-compact/cache_edits/B-2 are present but appear unintegrated in non-test runtime usage.  
`UNDECLARED_PATTERN`: helper-only shipment without integration hooks.

**FINAL**: **REJECT**

Could not independently rerun tests here because `pytest` is not installed in this shell.
