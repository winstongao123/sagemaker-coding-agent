Reading additional input from stdin...
OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.5
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019dece0-9836-7022-829a-d6b2f8d4edf9
--------
user
You are reviewing Block L of v5.0.1 — Error/retry/cache-break +
Bedrock guardrails.

Block L deliverable: extends Phase 8's 9-category error classifier to
the Runnable R4 18-category model, adds 5xx HTML humanization, max-
tokens-overflow detection, Retry-After parsing, per-tool cache-break
detection with Haiku exclusion (R4 #14 MUST 3LOC).

Diff range: v5.0.1-block-h-plus..HEAD (Block L commit).

Files changed:
- EXTENDED compact_v5/MAIN/agent/core/errors.py (~150 LOC added)
  - 9 new BedrockErrorCategory entries:
    MAX_TOKENS_OVERFLOW / BEDROCK_5XX_HTML / REQUEST_TIMEOUT /
    PAYLOAD_TOO_LARGE / CONFLICT_409 / GATEWAY_TIMEOUT /
    MALFORMED_RESPONSE / SIGV4_FAILURE / DEPENDENCY_FAILURE.
  - _RETRYABLE_CATEGORIES frozenset + categorize_retryable() helper.
  - extract_nested_error_message: humanizes JSON / HTML title / h1 /
    body text fallback / strip-tags fallback.
  - parse_max_tokens_context_overflow_error: predicate for compact+retry.
  - get_retry_after_ms: parses int seconds OR HTTP-date.
  - ErrorClassifier.classify extended to recognize all 9 new categories.
    Most-specific-first ordering preserves Phase 8 behavior.
- NEW compact_v5/MAIN/agent/core/cache_break_detection.py (~120 LOC)
  - hash_tool_schema: deterministic SHA256/16chars (sort_keys=True).
  - PerToolCacheBreakDetector: per-tool baseline + diff. First call
    establishes baseline; subsequent calls return list of broken names.
  - is_cache_break_excluded(model_id): R4 #14 MUST. Haiku 4.5 + Haiku
    4.1 + 3.5 Haiku in EXCLUDED frozenset with cross-region prefix
    stripping (au./apac./us./eu./global./ap./in.).
  - notify_cache_deletion(model_id, tool_names): returns False
    (skip) for excluded models, True for others.
- EXTENDED compact_v5/MAIN/agent/core/__init__.py: re-exports.
- NEW compact_v5/MAIN/agent/tests/integration/test_block_l.py
  - 9 tests: 6 TEST_DESIGN-named + 3 behavior locks.
  - 2 T2 daemon-thread + 30s-heartbeat tests SKIPPED with deferral
    note pointing to Block J real-AWS gate per ADR-036 §3.

Reference paths:
- Runnable: _archive/compare_code/gg-claude-code-runnable/src/services/api/errors.ts
- Runnable: _archive/compare_code/gg-claude-code-runnable/src/services/api/cacheBreakDetection.ts
- Plan: compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md (§Block L)
- Tests: compact_v5/_phase_2/wave_6/TEST_DESIGN.md (§Block L)
- ADR-036: compact_v5/_status/V5_DESIGN_DECISIONS.md

Tests: 729 pass + 11 skip (was 720 + 9 at end of Block H+; +9 pass +
2 skip net new).
verify_ship_zip.py: PASS (127 files / 357.2 KB / 36%).

Apply the 3-axis review template. Be specific — cite file:line.

AXIS A — Errors / bugs / regressions
- BedrockErrorCategory has 18 distinct values (lock test asserts via
  set-len).
- categorize_retryable maps each to a sensible verdict:
  - retryable: throttle, service_unavailable, model_not_ready,
    network, validation_cache, context_overflow, max_tokens_overflow,
    bedrock_5xx_html, request_timeout, payload_too_large,
    gateway_timeout, malformed_response, dependency_failure (13).
  - non-retryable: validation_other, access_denied, conflict_409,
    sigv4_failure, unknown (5).
- ErrorClassifier ordering is most-specific-first:
  - MAX_TOKENS_OVERFLOW pattern checked BEFORE CONTEXT_OVERFLOW
    (which would otherwise match the same "too long" substring).
  - HTML-shape check (`<html` / `<body` / `<title`) BEFORE the
    plain-text patterns.
  - Phase 8 patterns preserved at the end.
- extract_nested_error_message:
  - JSON parse first (most specific shape).
  - Then HTML title → h1 → body text.
  - Fallback: strip-all-tags.
  - Always returns ≤200 chars.
  - Empty input returns "(empty error)".
- parse_max_tokens_context_overflow_error:
  - "max_tokens" / "max output tokens" / "output token limit" → True.
  - "prompt is too long" / "too many tokens" / "input length" → True.
  - "context length" / "context_overflow" → True.
- get_retry_after_ms:
  - "Retry-After: <N>" → N*1000 (case-insensitive).
  - HTTP-date format → ms-until-then via parsedate_to_datetime.
  - No header → 0.
- PerToolCacheBreakDetector:
  - First call establishes baseline (returns []).
  - Schema-changed tools listed by name.
  - is_cache_break_excluded short-circuits to [].
  - update_baseline can be called manually.
- is_cache_break_excluded:
  - Strips au./apac./us./eu./global./ap./in. prefixes.
  - 3 model IDs in EXCLUDED set: Haiku 4.5, Haiku 4.1, 3.5 Haiku.
- T2 deferrals declared in ADR-036 §3 + test docstrings + pytest.mark.skip
  with reason text mentioning Block J.

Verdict: PASS | CHANGES_REQUESTED | BLOCKER.

AXIS B — v5 architecture + goals fit
- Constraint #5 (minimum file structures): 1 module extension + 1 new
  module + tests. Matches existing core/ shape.
- Constraint #6 (architecture-first): the 18-category model is the
  Runnable contract; v5 ports it directly.
- Constraint #15 (quality, no rush): T1 tests cover all critical
  algorithms; T2 wall-clock tests deferred to Block J.

FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED.

AXIS C — Reference-repo coverage
- 18 categories: PORTED in #100.
- max-tokens overflow + 5xx HTML humanization + Retry-After: PORTED in #100.
- Per-tool cache-break: PORTED in #101.
- Haiku exclusion (R4 #14 MUST 3LOC): PORTED in #101.
- T2 daemon-thread + heartbeat: DEFERRED to Block J (declared in
  ADR-036 §3 + test deferral note).

Verdict: ALL_PORTED | SOME_DROPPED | UNDECLARED_PATTERN.

FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.

Be specific. Cite file:line for any finding. Where you say "fix",
suggest the minimal patch.
codex
I’ll review this as a code review against the stated Block L contract, starting with the changed files and the referenced runnable/test design where needed. Then I’ll verify behavior with focused test or static checks if the repo makes that cheap.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --name-only v5.0.1-block-h-plus..HEAD' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff --stat v5.0.1-block-h-plus..HEAD' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git status --short' in D:\Github\sagemaker-coding-agent
 succeeded in 592ms:
 m _archive/compare_code/gg-claude-code-runnable
?? compact_v5/_status/codex_reviews/block-l-iter1.md
?? compact_v5/_status/codex_reviews/block-l-prompt.txt
warning: unable to access 'C:\Users\winst/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\winst/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\winst/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\winst/.config/git/ignore': Permission denied

 succeeded in 602ms:
SESSION_STATE.md
compact_v5.zip
compact_v5/MAIN/agent/core/__init__.py
compact_v5/MAIN/agent/core/cache_break_detection.py
compact_v5/MAIN/agent/core/errors.py
compact_v5/MAIN/agent/tests/integration/test_block_l.py
compact_v5/_status/V5_BUILD_STATUS.md
compact_v5/_status/V5_DESIGN_DECISIONS.md
compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
compact_v5/_status/codex_reviews/block-h-plus-iter1.md
compact_v5/_status/codex_reviews/block-h-plus-iter2-prompt.txt
compact_v5/_status/codex_reviews/block-h-plus-iter2.md
compact_v5/_status/codex_reviews/block-h-plus-iter3-prompt.txt
compact_v5/_status/codex_reviews/block-h-plus-iter3.md
compact_v5/_status/codex_reviews/block-h-plus-iter4-prompt.txt
compact_v5/_status/codex_reviews/block-h-plus-iter4.md
compact_v5/_status/codex_reviews/block-h-plus-prompt.txt

 succeeded in 619ms:
 SESSION_STATE.md                                   |   11 +
 compact_v5.zip                                     |  Bin 360890 -> 365766 bytes
 compact_v5/MAIN/agent/core/__init__.py             |   15 +-
 .../MAIN/agent/core/cache_break_detection.py       |  148 +
 compact_v5/MAIN/agent/core/errors.py               |  173 +-
 .../MAIN/agent/tests/integration/test_block_l.py   |  326 ++
 compact_v5/_status/V5_BUILD_STATUS.md              |   16 +-
 compact_v5/_status/V5_DESIGN_DECISIONS.md          |   89 +
 compact_v5/_status/V5_RUNNABLE_PORT_LOG.md         |    4 +-
 .../_status/codex_reviews/block-h-plus-iter1.md    | 2629 +++++++++++
 .../codex_reviews/block-h-plus-iter2-prompt.txt    |   79 +
 .../_status/codex_reviews/block-h-plus-iter2.md    | 2054 +++++++++
 .../codex_reviews/block-h-plus-iter3-prompt.txt    |   80 +
 .../_status/codex_reviews/block-h-plus-iter3.md    |  975 ++++
 .../codex_reviews/block-h-plus-iter4-prompt.txt    |   69 +
 .../_status/codex_reviews/block-h-plus-iter4.md    | 4802 ++++++++++++++++++++
 .../_status/codex_reviews/block-h-plus-prompt.txt  |  107 +
 17 files changed, 11571 insertions(+), 6 deletions(-)

codex
The diff includes the expected Block L files plus status/review artifacts and the zip. I’m narrowing the review to the implementation and test files first, then I’ll check the ADR/test deferral text because the T2 skips are part of the requested contract.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/core/errors.py | ForEach-Object { '"'{0,5}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/core/cache_break_detection.py | ForEach-Object { '"'{0,5}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/core/__init__.py | ForEach-Object { '"'{0,5}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/tests/integration/test_block_l.py | ForEach-Object { '"'{0,5}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 552ms:
    1: """V5 core/ â€” agent loop + retry + errors + budget.
    2: 
    3: Per ADR-014 (Phase 8):
    4:   - core/query_engine.py : main agent loop (Runnable QueryEngine.ts adaptation)
    5:   - core/retry.py        : jittered exponential backoff (Phase-1 RetryPolicy extracted)
    6:   - core/errors.py       : Bedrock error classifier (Phase-1 ErrorClassifier extracted)
    7:   - core/budget.py       : IterationBudget (Hermes pattern via v4)
    8:   - core/cache.py        : prompt-cache block builder + cache-break detection (Phase 6)
    9: 
   10: Phase 7 contract: query_engine MUST call `apply_tool_search_deferral(enabled=True)`
   11: per turn AND extract discovered tool names via `tool_search_discovered_names()`
   12: to wire deferred tools into the next turn's API call.
   13: """
   14: from __future__ import annotations
   15: 
   16: # Re-export the public surface
   17: from .budget import IterationBudget  # noqa: F401
   18: from .errors import (  # noqa: F401
   19:     BedrockErrorCategory,
   20:     ErrorClassifier,
   21:     categorize_retryable,
   22:     extract_nested_error_message,
   23:     parse_max_tokens_context_overflow_error,
   24:     get_retry_after_ms,
   25: )
   26: from .cache_break_detection import (  # noqa: F401
   27:     PerToolCacheBreakDetector,
   28:     is_cache_break_excluded,
   29:     hash_tool_schema,
   30:     notify_cache_deletion,
   31: )
   32: from .retry import RetryPolicy  # noqa: F401
   33: from .query_engine import QueryEngine, run_one_turn, count_tool_calls  # noqa: F401

 succeeded in 573ms:
    1: """V5 core/errors.py â€” Bedrock error classifier (Phase 8 extraction).
    2: 
    3: Per ADR-014: extracted verbatim from Phase-1 `runtime/bedrock_client.py`
    4: (which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).
    5: 
    6: PORT_LOG: #017.
    7: 
    8: Why this lives here in Phase 8 (not Phase 1):
    9: The classifier was bundled with `BedrockClient` in Phase 1 to avoid a
   10: circular Phase-1/Phase-8 dependency. Now that core/ exists, the classifier
   11: gets its own module so:
   12:   - QueryEngine can import without pulling boto3 transitively
   13:   - Tests can exercise classification logic without a Bedrock client
   14:   - Future phases can reuse classifier semantics outside Bedrock invocation
   15: 
   16: Behavior is byte-equivalent with Phase-1. `runtime/bedrock_client.py`
   17: re-imports these names for backwards compatibility (no chat() change).
   18: """
   19: from __future__ import annotations
   20: 
   21: 
   22: class BedrockErrorCategory:
   23:     """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy.
   24: 
   25:     Block L (PORT_LOG #100) extends to 18 categories per Runnable R4 18-categorization.
   26:     The original 9 (Phase 8) cover the v4 surface; the additional 9 distinguish
   27:     finer-grained cases that benefit from differentiated retry/recovery semantics.
   28:     """
   29:     # Phase 8 (v4) categories â€” 9
   30:     THROTTLE = "throttle"  # ThrottlingException, rate-limited
   31:     SERVICE_UNAVAILABLE = "service_unavailable"
   32:     MODEL_NOT_READY = "model_not_ready"
   33:     NETWORK = "network"
   34:     VALIDATION_CACHE = "validation_cache"  # cache_control rejected â€” strip and retry once
   35:     VALIDATION_OTHER = "validation_other"
   36:     CONTEXT_OVERFLOW = "context_overflow"  # prompt-too-long
   37:     ACCESS_DENIED = "access_denied"
   38:     UNKNOWN = "unknown"
   39:     # Block L additions â€” 9 more (R4 18 categories)
   40:     MAX_TOKENS_OVERFLOW = "max_tokens_overflow"  # output capped at max_tokens â€” compact + retry
   41:     BEDROCK_5XX_HTML = "bedrock_5xx_html"  # raw HTML 5xx â€” humanize before user
   42:     REQUEST_TIMEOUT = "request_timeout"  # client-side timeout
   43:     PAYLOAD_TOO_LARGE = "payload_too_large"  # 413 â€” compact request
   44:     CONFLICT_409 = "conflict_409"  # session/state conflict
   45:     GATEWAY_TIMEOUT = "gateway_timeout"  # 504 â€” backoff
   46:     MALFORMED_RESPONSE = "malformed_response"  # body parse failure â€” retry once
   47:     SIGV4_FAILURE = "sigv4_failure"  # auth signature error â€” no retry, surface
   48:     DEPENDENCY_FAILURE = "dependency_failure"  # downstream service error â€” backoff
   49: 
   50: 
   51: # Block L: which categories are retryable. Used by categorize_retryable().
   52: # Per Runnable R4 categorization.
   53: _RETRYABLE_CATEGORIES = frozenset({
   54:     BedrockErrorCategory.THROTTLE,
   55:     BedrockErrorCategory.SERVICE_UNAVAILABLE,
   56:     BedrockErrorCategory.MODEL_NOT_READY,
   57:     BedrockErrorCategory.NETWORK,
   58:     BedrockErrorCategory.VALIDATION_CACHE,  # retry once after stripping
   59:     BedrockErrorCategory.CONTEXT_OVERFLOW,  # retry after compact
   60:     BedrockErrorCategory.MAX_TOKENS_OVERFLOW,  # retry after compact
   61:     BedrockErrorCategory.BEDROCK_5XX_HTML,  # backoff
   62:     BedrockErrorCategory.REQUEST_TIMEOUT,  # retry once
   63:     BedrockErrorCategory.PAYLOAD_TOO_LARGE,  # retry after compact
   64:     BedrockErrorCategory.GATEWAY_TIMEOUT,  # backoff
   65:     BedrockErrorCategory.MALFORMED_RESPONSE,  # retry once
   66:     BedrockErrorCategory.DEPENDENCY_FAILURE,  # backoff
   67: })
   68: 
   69: 
   70: def categorize_retryable(category: str) -> bool:
   71:     """Return True iff `category` is in the retryable set (Block L PORT_LOG #100)."""
   72:     return category in _RETRYABLE_CATEGORIES
   73: 
   74: 
   75: def extract_nested_error_message(exc_or_text) -> str:
   76:     """Block L (R4 #9 MUST): humanize Bedrock 5xx errors that contain raw HTML.
   77: 
   78:     Bedrock occasionally returns HTML error pages on 5xx; the user sees a wall
   79:     of `<html>...<body>The server encountered an error...</body></html>`.
   80:     This helper extracts the readable text from common error shapes:
   81:     - `<title>Error</title>` â†’ use the title.
   82:     - `<body>...text...</body>` â†’ use the body text.
   83:     - `<h1>Error 502</h1>` â†’ use the heading.
   84:     - JSON `{"message": "..."}` â†’ use the message field.
   85: 
   86:     Falls back to the first 200 chars of the input when no pattern matches.
   87:     """
   88:     import re
   89:     import json as _json
   90: 
   91:     text = str(exc_or_text)
   92:     if not text.strip():
   93:         return "(empty error)"
   94: 
   95:     # Try JSON first.
   96:     try:
   97:         data = _json.loads(text)
   98:         if isinstance(data, dict):
   99:             for key in ("message", "Message", "error", "Error"):
  100:                 v = data.get(key)
  101:                 if isinstance(v, str) and v.strip():
  102:                     return v.strip()[:200]
  103:     except (_json.JSONDecodeError, ValueError):
  104:         pass
  105: 
  106:     # Try HTML title.
  107:     m = re.search(r"<title[^>]*>([^<]+)</title>", text, re.IGNORECASE)
  108:     if m:
  109:         return m.group(1).strip()[:200]
  110:     # Try h1.
  111:     m = re.search(r"<h1[^>]*>([^<]+)</h1>", text, re.IGNORECASE)
  112:     if m:
  113:         return m.group(1).strip()[:200]
  114:     # Try body text â€” strip remaining tags.
  115:     m = re.search(r"<body[^>]*>(.*?)</body>", text, re.IGNORECASE | re.DOTALL)
  116:     if m:
  117:         body_text = re.sub(r"<[^>]+>", " ", m.group(1))
  118:         body_text = re.sub(r"\s+", " ", body_text).strip()
  119:         if body_text:
  120:             return body_text[:200]
  121: 
  122:     # Fallback: strip ALL HTML tags from the full input.
  123:     stripped = re.sub(r"<[^>]+>", " ", text)
  124:     stripped = re.sub(r"\s+", " ", stripped).strip()
  125:     return stripped[:200] or text[:200]
  126: 
  127: 
  128: def parse_max_tokens_context_overflow_error(exc) -> bool:
  129:     """Block L (R4 #2 MUST): True iff `exc` is a max-tokens or context-
  130:     overflow error that should trigger compact+retry.
  131: 
  132:     Distinguishes max_tokens (output cap hit) from prompt-too-long
  133:     (context overflow) â€” both trigger compact+retry but for different
  134:     reasons. Returns True for either.
  135:     """
  136:     msg = str(exc).lower()
  137:     if "max_tokens" in msg or "max output tokens" in msg or "output token limit" in msg:
  138:         return True
  139:     if "prompt is too long" in msg or "too many tokens" in msg or "input length" in msg:
  140:         return True
  141:     if "context length" in msg or "context_overflow" in msg:
  142:         return True
  143:     return False
  144: 
  145: 
  146: def get_retry_after_ms(exc) -> int:
  147:     """Block L (R4 retry-after): parse Retry-After header value from exception.
  148: 
  149:     Bedrock 429 responses include a Retry-After header (seconds). This helper
  150:     extracts the integer second value and returns milliseconds. Returns 0
  151:     when no Retry-After is found.
  152: 
  153:     Accepts:
  154:     - integer seconds: "5" â†’ 5000
  155:     - HTTP-date format (RFC 1123): "Wed, 21 Oct 2026 07:28:00 GMT" â†’ ms-until-then
  156:     - error message containing "Retry-After: 5": parses the trailing seconds
  157:     """
  158:     import re
  159:     import time
  160:     from email.utils import parsedate_to_datetime
  161: 
  162:     s = str(exc)
  163:     # Match "Retry-After: <value>" header pattern.
  164:     m = re.search(r"retry-after\s*:?\s*(\d+)", s, re.IGNORECASE)
  165:     if m:
  166:         try:
  167:             return int(m.group(1)) * 1000
  168:         except (ValueError, TypeError):
  169:             return 0
  170:     # Match HTTP-date.
  171:     m = re.search(r"retry-after\s*:?\s*([A-Z][a-z]{2},\s*\d.+\d{4}.+GMT)", s)
  172:     if m:
  173:         try:
  174:             dt = parsedate_to_datetime(m.group(1))
  175:             wait = max(0, int((dt.timestamp() - time.time()) * 1000))
  176:             return wait
  177:         except (ValueError, TypeError):
  178:             return 0
  179:     return 0
  180: 
  181: 
  182: class ErrorClassifier:
  183:     """Classifies Bedrock exceptions into a (category, recovery, debug_msg) triple.
  184: 
  185:     Verbatim port of v4's classifier. Recovery values:
  186:       - "strip_cache_retry": cache_control rejected; strip blocks and retry once
  187:       - "compact_retry":     prompt-too-long; caller should compact and retry
  188:       - "backoff":           transient (throttle/503/network); retry with jitter
  189:       - "no_retry":          permanent (validation/access denied); surface to user
  190:     """
  191: 
  192:     @staticmethod
  193:     def classify(exc: Exception):
  194:         msg_lower = str(exc).lower()
  195:         cls_name = type(exc).__name__.lower()
  196: 
  197:         # Block L additions â€” check most-specific first.
  198:         if "max_tokens" in msg_lower or "max output tokens" in msg_lower or "output token limit" in msg_lower:
  199:             return BedrockErrorCategory.MAX_TOKENS_OVERFLOW, "compact_retry", str(exc)[:200]
  200:         if "<html" in msg_lower or "<body" in msg_lower or "<title" in msg_lower:
  201:             # Raw HTML 5xx error â€” backoff + humanize before user-facing display.
  202:             return BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff", str(exc)[:200]
  203:         if "504" in msg_lower or "gatewaytimeout" in msg_lower:
  204:             return BedrockErrorCategory.GATEWAY_TIMEOUT, "backoff", str(exc)[:200]
  205:         if "413" in msg_lower or "payload too large" in msg_lower or "request entity too large" in msg_lower:
  206:             return BedrockErrorCategory.PAYLOAD_TOO_LARGE, "compact_retry", str(exc)[:200]
  207:         if "409" in msg_lower or "conflictexception" in msg_lower:
  208:             return BedrockErrorCategory.CONFLICT_409, "no_retry", str(exc)[:200]
  209:         if "request_timeout" in msg_lower or "request-timeout" in msg_lower or (
  210:             "408" in msg_lower
  211:         ):
  212:             return BedrockErrorCategory.REQUEST_TIMEOUT, "backoff", str(exc)[:200]
  213:         if "malformed" in msg_lower or "could not parse response" in msg_lower or "decode" in cls_name:
  214:             return BedrockErrorCategory.MALFORMED_RESPONSE, "backoff", str(exc)[:200]
  215:         if "sigv4" in msg_lower or "signature" in msg_lower or "credentialverify" in cls_name:
  216:             return BedrockErrorCategory.SIGV4_FAILURE, "no_retry", str(exc)[:200]
  217:         if "dependency" in msg_lower or "dependencyfailedexception" in msg_lower:
  218:             return BedrockErrorCategory.DEPENDENCY_FAILURE, "backoff", str(exc)[:200]
  219: 
  220:         # Phase 8 categories â€” preserved.
  221:         if "validationexception" in msg_lower and (
  222:             "cache_control" in msg_lower
  223:             or "prompt-caching" in msg_lower
  224:             or "cache" in msg_lower
  225:         ):
  226:             return BedrockErrorCategory.VALIDATION_CACHE, "strip_cache_retry", str(exc)[:200]
  227:         if "validationexception" in msg_lower and (
  228:             "prompt is too long" in msg_lower
  229:             or "too many tokens" in msg_lower
  230:             or "input length" in msg_lower
  231:         ):
  232:             return BedrockErrorCategory.CONTEXT_OVERFLOW, "compact_retry", str(exc)[:200]
  233:         if "validationexception" in msg_lower:
  234:             return BedrockErrorCategory.VALIDATION_OTHER, "no_retry", str(exc)[:200]
  235:         if "throttlingexception" in msg_lower or "rate" in msg_lower:
  236:             return BedrockErrorCategory.THROTTLE, "backoff", str(exc)[:200]
  237:         if "serviceunavailable" in msg_lower or "503" in msg_lower:
  238:             return BedrockErrorCategory.SERVICE_UNAVAILABLE, "backoff", str(exc)[:200]
  239:         if "modelnotready" in msg_lower or "not ready" in msg_lower:
  240:             return BedrockErrorCategory.MODEL_NOT_READY, "backoff", str(exc)[:200]
  241:         if "accessdenied" in msg_lower or "403" in msg_lower or "unauthorized" in msg_lower:
  242:             return BedrockErrorCategory.ACCESS_DENIED, "no_retry", str(exc)[:200]
  243:         if (
  244:             "endpointconnectionerror" in cls_name
  245:             or "connecttimeout" in cls_name
  246:             or "readtimeout" in cls_name
  247:             or "connectionerror" in cls_name
  248:         ):
  249:             return BedrockErrorCategory.NETWORK, "backoff", str(exc)[:200]
  250:         return BedrockErrorCategory.UNKNOWN, "no_retry", str(exc)[:200]

 succeeded in 565ms:
    1: """V5 core/cache_break_detection.py â€” Block L per-tool cache-break detection.
    2: 
    3: PORT_LOG: #101.
    4: 
    5: Source: Runnable services/api/cacheBreakDetection.ts.
    6: 
    7: When a tool's schema changes between turns, the prompt cache is invalidated
    8: for that tool. This module detects per-tool schema changes by hashing each
    9: tool's schema and comparing against a per-engine baseline.
   10: 
   11: R4 #14 MUST: Haiku-4.5 model_id is in the EXCLUDED_MODELS set â€” Haiku
   12: doesn't support prompt-cache deletion notifications, so the detector
   13: skips these models entirely. Bedrock returns a 400 error if you call
   14: notify_cache_deletion() on Haiku; the exclusion preserves API validity.
   15: """
   16: from __future__ import annotations
   17: 
   18: import hashlib
   19: import json
   20: from typing import Any, Dict, List, Optional, Set
   21: 
   22: 
   23: # Block L (R4 #14 MUST): models that don't support prompt-cache
   24: # deletion. Haiku 4.5 in particular: notify_cache_deletion() raises
   25: # ValidationException on these. Cross-region prefixes (au./apac./
   26: # us./eu.) are stripped before lookup.
   27: _EXCLUDED_MODELS_3LOC: frozenset = frozenset({
   28:     "anthropic.claude-haiku-4-5-20251001-v1:0",
   29:     "anthropic.claude-haiku-4-1-20250228-v1:0",  # also exclude prior Haiku
   30:     "anthropic.claude-3-5-haiku-20241022-v1:0",
   31: })
   32: 
   33: 
   34: def _strip_region_prefix(model_id: str) -> str:
   35:     """Strip cross-region inference prefixes (au./apac./us./eu./global.)
   36:     so the EXCLUDED_MODELS lookup matches both `au.anthropic...` and
   37:     `anthropic...` forms.
   38:     """
   39:     for prefix in ("au.", "apac.", "us.", "eu.", "global.", "ap.", "in."):
   40:         if model_id.startswith(prefix):
   41:             return model_id[len(prefix):]
   42:     return model_id
   43: 
   44: 
   45: def is_cache_break_excluded(model_id: str) -> bool:
   46:     """R4 #14 MUST: True iff model_id is in the cache-break-detection
   47:     EXCLUDED set. Haiku 4.5 in particular.
   48:     """
   49:     if not model_id:
   50:         return False
   51:     return _strip_region_prefix(model_id) in _EXCLUDED_MODELS_3LOC
   52: 
   53: 
   54: def hash_tool_schema(tool_schema: Dict[str, Any]) -> str:
   55:     """Stable hash of a tool schema. Two semantically identical schemas
   56:     (different key order) produce the same hash.
   57: 
   58:     Block L per-tool detection: a tool is cache-broken iff its schema
   59:     hash changed between turns.
   60:     """
   61:     canonical = json.dumps(tool_schema, sort_keys=True, separators=(",", ":"))
   62:     return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
   63: 
   64: 
   65: class PerToolCacheBreakDetector:
   66:     """Tracks per-tool schema hashes across turns.
   67: 
   68:     Usage:
   69:         detector = PerToolCacheBreakDetector()
   70:         # Turn 1:
   71:         detector.update_baseline(tools)
   72:         # Turn 2:
   73:         broken = detector.detect_breaks(tools, model_id="anthropic.claude-...")
   74:         # broken is a list of tool names whose schemas changed.
   75: 
   76:     If model_id is in the EXCLUDED set, detect_breaks() returns [] â€”
   77:     skips the entire detection path because notify_cache_deletion()
   78:     isn't supported on those models.
   79:     """
   80: 
   81:     def __init__(self) -> None:
   82:         self._baseline: Dict[str, str] = {}
   83: 
   84:     def update_baseline(self, tools: List[Dict[str, Any]]) -> None:
   85:         """Snapshot the current schema hashes as the baseline."""
   86:         self._baseline = {
   87:             t.get("name", ""): hash_tool_schema(t)
   88:             for t in tools or []
   89:             if t.get("name")
   90:         }
   91: 
   92:     def detect_breaks(
   93:         self,
   94:         tools: List[Dict[str, Any]],
   95:         model_id: str = "",
   96:     ) -> List[str]:
   97:         """Return list of tool names whose schemas changed since the last
   98:         update_baseline() call.
   99: 
  100:         R4 #14: when model_id is in the cache-break EXCLUDED set, skips
  101:         detection entirely (returns []). The notify_cache_deletion()
  102:         call would fail with 400 on those models.
  103:         """
  104:         if is_cache_break_excluded(model_id):
  105:             return []
  106:         if not self._baseline:
  107:             # First call â€” establish baseline; no breaks reported.
  108:             self.update_baseline(tools)
  109:             return []
  110: 
  111:         broken: List[str] = []
  112:         current = {
  113:             t.get("name", ""): hash_tool_schema(t)
  114:             for t in tools or []
  115:             if t.get("name")
  116:         }
  117:         for name, h in current.items():
  118:             prev = self._baseline.get(name)
  119:             if prev is not None and prev != h:
  120:                 broken.append(name)
  121:         # Update baseline so subsequent calls compare against latest.
  122:         self._baseline = current
  123:         return broken
  124: 
  125: 
  126: def notify_cache_deletion(
  127:     model_id: str,
  128:     tool_names: List[str],
  129: ) -> bool:
  130:     """Issue a cache-deletion notification for the given tools.
  131: 
  132:     Block L: when tool schemas change, Bedrock's prompt cache for those
  133:     tool entries is stale; this helper would normally call the Bedrock
  134:     invalidation endpoint. v5's stub: log + return True for non-excluded
  135:     models, return False (skip) for EXCLUDED models.
  136: 
  137:     The actual Bedrock endpoint integration is wired by core/query_engine
  138:     on the next chat() call's `additionalModelRequestFields`.
  139:     """
  140:     if is_cache_break_excluded(model_id):
  141:         return False  # skip
  142:     # Real wiring would go here; v5 stub just signals "should notify".
  143:     import logging
  144:     logging.info(
  145:         "[cache-break] notify_cache_deletion model=%s tools=%s",
  146:         model_id, tool_names,
  147:     )
  148:     return True

 succeeded in 582ms:
    1: """Block L â€” Error/retry/cache-break + Bedrock guardrails + daemon-thread call.
    2: 
    3: Source: Runnable services/api/errors.ts + cacheBreakDetection.ts +
    4: withRetry.ts.
    5: 
    6: Tests per TEST_DESIGN Â§Block L (8 tests; 2 T2 daemon-thread tests
    7: deferred to Block J real-AWS integration):
    8: - test_categorize_retryable_18_error_types
    9: - test_parse_max_tokens_overflow_recovers
   10: - test_extract_nested_error_message_humanizes_5xx_html
   11: - test_retry_after_header_parsed
   12: - test_per_tool_cache_break_detection
   13: - test_haiku_excluded_from_cache_break_3loc
   14: - test_daemon_thread_bedrock_call_responds_to_ctrl_c (DEFERRED)
   15: - test_30s_heartbeat_during_long_call (DEFERRED)
   16: """
   17: from __future__ import annotations
   18: 
   19: import os
   20: import sys
   21: 
   22: import pytest
   23: 
   24: _AGENT_ROOT = os.path.dirname(
   25:     os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   26: )
   27: if _AGENT_ROOT not in sys.path:
   28:     sys.path.insert(0, _AGENT_ROOT)
   29: 
   30: 
   31: # ============================================================
   32: # TEST_DESIGN row 1 â€” 18 error categories with retryable verdicts
   33: # ============================================================
   34: 
   35: def test_categorize_retryable_18_error_types():
   36:     """Each of 18 Runnable error categories â†’ correct retryable verdict.
   37: 
   38:     Retryable (13): throttle, service_unavailable, model_not_ready,
   39:     network, validation_cache, context_overflow, max_tokens_overflow,
   40:     bedrock_5xx_html, request_timeout, payload_too_large,
   41:     gateway_timeout, malformed_response, dependency_failure.
   42: 
   43:     Non-retryable (5): validation_other, access_denied, conflict_409,
   44:     sigv4_failure, unknown.
   45:     """
   46:     from core import BedrockErrorCategory, categorize_retryable
   47: 
   48:     # All 18 categories defined.
   49:     all_18 = [
   50:         BedrockErrorCategory.THROTTLE,
   51:         BedrockErrorCategory.SERVICE_UNAVAILABLE,
   52:         BedrockErrorCategory.MODEL_NOT_READY,
   53:         BedrockErrorCategory.NETWORK,
   54:         BedrockErrorCategory.VALIDATION_CACHE,
   55:         BedrockErrorCategory.VALIDATION_OTHER,
   56:         BedrockErrorCategory.CONTEXT_OVERFLOW,
   57:         BedrockErrorCategory.ACCESS_DENIED,
   58:         BedrockErrorCategory.UNKNOWN,
   59:         BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
   60:         BedrockErrorCategory.BEDROCK_5XX_HTML,
   61:         BedrockErrorCategory.REQUEST_TIMEOUT,
   62:         BedrockErrorCategory.PAYLOAD_TOO_LARGE,
   63:         BedrockErrorCategory.CONFLICT_409,
   64:         BedrockErrorCategory.GATEWAY_TIMEOUT,
   65:         BedrockErrorCategory.MALFORMED_RESPONSE,
   66:         BedrockErrorCategory.SIGV4_FAILURE,
   67:         BedrockErrorCategory.DEPENDENCY_FAILURE,
   68:     ]
   69:     assert len(set(all_18)) == 18, f"Expected 18 distinct categories; got {len(set(all_18))}"
   70: 
   71:     retryable = {
   72:         BedrockErrorCategory.THROTTLE,
   73:         BedrockErrorCategory.SERVICE_UNAVAILABLE,
   74:         BedrockErrorCategory.MODEL_NOT_READY,
   75:         BedrockErrorCategory.NETWORK,
   76:         BedrockErrorCategory.VALIDATION_CACHE,
   77:         BedrockErrorCategory.CONTEXT_OVERFLOW,
   78:         BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
   79:         BedrockErrorCategory.BEDROCK_5XX_HTML,
   80:         BedrockErrorCategory.REQUEST_TIMEOUT,
   81:         BedrockErrorCategory.PAYLOAD_TOO_LARGE,
   82:         BedrockErrorCategory.GATEWAY_TIMEOUT,
   83:         BedrockErrorCategory.MALFORMED_RESPONSE,
   84:         BedrockErrorCategory.DEPENDENCY_FAILURE,
   85:     }
   86:     non_retryable = {
   87:         BedrockErrorCategory.VALIDATION_OTHER,
   88:         BedrockErrorCategory.ACCESS_DENIED,
   89:         BedrockErrorCategory.CONFLICT_409,
   90:         BedrockErrorCategory.SIGV4_FAILURE,
   91:         BedrockErrorCategory.UNKNOWN,
   92:     }
   93: 
   94:     for cat in retryable:
   95:         assert categorize_retryable(cat) is True, f"{cat} should be retryable"
   96:     for cat in non_retryable:
   97:         assert categorize_retryable(cat) is False, f"{cat} should NOT be retryable"
   98: 
   99: 
  100: # ============================================================
  101: # TEST_DESIGN row 2 â€” max-tokens overflow triggers compact + retry (R4 #2 MUST)
  102: # ============================================================
  103: 
  104: def test_parse_max_tokens_overflow_recovers():
  105:     """parseMaxTokensContextOverflowError triggers compact + retry."""
  106:     from core import (
  107:         BedrockErrorCategory,
  108:         ErrorClassifier,
  109:         parse_max_tokens_context_overflow_error,
  110:     )
  111: 
  112:     cases = [
  113:         ValueError("max_tokens 4096 exceeded"),
  114:         RuntimeError("Output token limit reached at 4097"),
  115:         Exception("Prompt is too long: 250000 tokens"),
  116:         Exception("Too many tokens in input length"),
  117:         Exception("context_overflow"),
  118:         Exception("Context length 200001 exceeds 200000"),
  119:     ]
  120:     for exc in cases:
  121:         assert parse_max_tokens_context_overflow_error(exc) is True, (
  122:             f"{exc!r} should be detected as max-tokens/context overflow"
  123:         )
  124: 
  125:     # Non-cases.
  126:     for exc in [Exception("ThrottlingException"), ValueError("unrelated")]:
  127:         assert parse_max_tokens_context_overflow_error(exc) is False
  128: 
  129:     # Classifier maps max-tokens overflow to MAX_TOKENS_OVERFLOW with
  130:     # compact_retry recovery.
  131:     cat, recovery, _ = ErrorClassifier.classify(
  132:         Exception("max_tokens 4096 exceeded")
  133:     )
  134:     assert cat == BedrockErrorCategory.MAX_TOKENS_OVERFLOW
  135:     assert recovery == "compact_retry"
  136: 
  137: 
  138: # ============================================================
  139: # TEST_DESIGN row 3 â€” humanize 5xx HTML errors (R4 #9 MUST)
  140: # ============================================================
  141: 
  142: def test_extract_nested_error_message_humanizes_5xx_html():
  143:     """Bedrock 5xx with raw HTML â†’ user sees clean error message."""
  144:     from core import extract_nested_error_message
  145: 
  146:     # HTML title.
  147:     html_title = "<html><head><title>503 Service Unavailable</title></head><body>x</body></html>"
  148:     out = extract_nested_error_message(html_title)
  149:     assert out == "503 Service Unavailable"
  150: 
  151:     # H1.
  152:     html_h1 = "<html><body><h1>Internal Server Error</h1><p>x</p></body></html>"
  153:     out = extract_nested_error_message(html_h1)
  154:     assert "Internal Server Error" in out
  155: 
  156:     # Body fallback.
  157:     html_body = "<html><body>The server encountered an error.</body></html>"
  158:     out = extract_nested_error_message(html_body)
  159:     assert "The server encountered an error" in out
  160: 
  161:     # JSON.
  162:     json_err = '{"message": "AccessDenied: principal lacks permission"}'
  163:     out = extract_nested_error_message(json_err)
  164:     assert "AccessDenied" in out
  165: 
  166:     # Plain string fallback.
  167:     plain = "ThrottlingException: Rate exceeded"
  168:     out = extract_nested_error_message(plain)
  169:     assert "ThrottlingException" in out
  170: 
  171: 
  172: # ============================================================
  173: # TEST_DESIGN row 4 â€” Retry-After header parsed
  174: # ============================================================
  175: 
  176: def test_retry_after_header_parsed():
  177:     """getRetryAfterMs parses 'Retry-After: 5' â†’ 5000ms."""
  178:     from core import get_retry_after_ms
  179: 
  180:     assert get_retry_after_ms(Exception("HTTP 429: Retry-After: 5")) == 5000
  181:     assert get_retry_after_ms("Retry-After: 30") == 30000
  182:     assert get_retry_after_ms("retry-after:60") == 60000
  183:     # No header â†’ 0.
  184:     assert get_retry_after_ms("ThrottlingException") == 0
  185:     assert get_retry_after_ms("") == 0
  186: 
  187: 
  188: # ============================================================
  189: # TEST_DESIGN row 5 â€” per-tool cache-break detection
  190: # ============================================================
  191: 
  192: def test_per_tool_cache_break_detection():
  193:     """Per-tool schema hash change â†’ cache-deletion fires for that tool only."""
  194:     from core import PerToolCacheBreakDetector
  195: 
  196:     detector = PerToolCacheBreakDetector()
  197: 
  198:     tools_v1 = [
  199:         {"name": "read_file", "description": "Read", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
  200:         {"name": "write_file", "description": "Write", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
  201:     ]
  202:     # First call: establish baseline; no breaks.
  203:     breaks = detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")
  204:     assert breaks == []
  205: 
  206:     # Same tools again â†’ no breaks.
  207:     breaks = detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")
  208:     assert breaks == []
  209: 
  210:     # read_file's schema changes; write_file unchanged.
  211:     tools_v2 = [
  212:         {"name": "read_file", "description": "Read v2", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "encoding": {"type": "string"}}}},
  213:         {"name": "write_file", "description": "Write", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
  214:     ]
  215:     breaks = detector.detect_breaks(tools_v2, model_id="anthropic.claude-sonnet-4-6")
  216:     assert breaks == ["read_file"], f"Expected only read_file broken; got {breaks}"
  217: 
  218: 
  219: # ============================================================
  220: # TEST_DESIGN row 6 â€” Haiku excluded from cache-break (R4 #14 MUST 3LOC)
  221: # ============================================================
  222: 
  223: def test_haiku_excluded_from_cache_break_3loc():
  224:     """Haiku-4.5 model_id in EXCLUDED set â†’ cache-break detector skips."""
  225:     from core import PerToolCacheBreakDetector, is_cache_break_excluded
  226: 
  227:     # Direct exclusion check.
  228:     assert is_cache_break_excluded("anthropic.claude-haiku-4-5-20251001-v1:0") is True
  229:     assert is_cache_break_excluded("au.anthropic.claude-haiku-4-5-20251001-v1:0") is True
  230:     assert is_cache_break_excluded("apac.anthropic.claude-haiku-4-5-20251001-v1:0") is True
  231:     # Non-Haiku: not excluded.
  232:     assert is_cache_break_excluded("anthropic.claude-sonnet-4-6") is False
  233:     assert is_cache_break_excluded("") is False
  234: 
  235:     # Detector skip path: even when schemas change, Haiku model returns [].
  236:     detector = PerToolCacheBreakDetector()
  237:     tools_v1 = [{"name": "x", "description": "y", "input_schema": {"v": 1}}]
  238:     detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")  # establish baseline
  239:     tools_v2 = [{"name": "x", "description": "y", "input_schema": {"v": 2}}]  # schema changed
  240: 
  241:     # Sonnet sees the break.
  242:     breaks_sonnet = detector.detect_breaks(tools_v2, model_id="anthropic.claude-sonnet-4-6")
  243:     assert "x" in breaks_sonnet
  244: 
  245:     # Reset baseline + check Haiku gets [] regardless.
  246:     detector2 = PerToolCacheBreakDetector()
  247:     detector2.detect_breaks(tools_v1, model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
  248:     breaks_haiku = detector2.detect_breaks(
  249:         tools_v2, model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
  250:     )
  251:     assert breaks_haiku == [], "Haiku must be excluded from cache-break detection"
  252: 
  253: 
  254: # ============================================================
  255: # TEST_DESIGN row 7 + 8 â€” DEFERRED to Block J real-AWS integration
  256: # ============================================================
  257: 
  258: @pytest.mark.skip(
  259:     reason="Block L T2 daemon-thread test deferred to Block J real-AWS gate "
  260:     "(timing-sensitive; relies on actual long-running Bedrock call to "
  261:     "interrupt with KeyboardInterrupt). Per ADR-036 Â§3."
  262: )
  263: def test_daemon_thread_bedrock_call_responds_to_ctrl_c():
  264:     pass
  265: 
  266: 
  267: @pytest.mark.skip(
  268:     reason="Block L T2 30s-heartbeat test deferred to Block J real-AWS gate "
  269:     "(timing-sensitive 30s wall-clock test). Per ADR-036 Â§3."
  270: )
  271: def test_30s_heartbeat_during_long_call():
  272:     pass
  273: 
  274: 
  275: # ============================================================
  276: # Behavioral lock tests
  277: # ============================================================
  278: 
  279: def test_classifier_recognizes_new_categories():
  280:     """Classifier maps each new category to a sensible default recovery."""
  281:     from core import BedrockErrorCategory, ErrorClassifier
  282: 
  283:     cases = [
  284:         (Exception("<html><body>503 Service Unavailable</body></html>"),
  285:          BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff"),
  286:         (Exception("HTTP 504 GatewayTimeout"),
  287:          BedrockErrorCategory.GATEWAY_TIMEOUT, "backoff"),
  288:         (Exception("HTTP 413 Payload too large"),
  289:          BedrockErrorCategory.PAYLOAD_TOO_LARGE, "compact_retry"),
  290:         (Exception("HTTP 409 ConflictException"),
  291:          BedrockErrorCategory.CONFLICT_409, "no_retry"),
  292:         (Exception("malformed response: could not parse response"),
  293:          BedrockErrorCategory.MALFORMED_RESPONSE, "backoff"),
  294:         (Exception("SigV4 signature failed"),
  295:          BedrockErrorCategory.SIGV4_FAILURE, "no_retry"),
  296:         (Exception("DependencyFailedException: downstream"),
  297:          BedrockErrorCategory.DEPENDENCY_FAILURE, "backoff"),
  298:     ]
  299:     for exc, expected_cat, expected_recovery in cases:
  300:         cat, recovery, _ = ErrorClassifier.classify(exc)
  301:         assert cat == expected_cat, f"{exc!r} â†’ got {cat}, expected {expected_cat}"
  302:         assert recovery == expected_recovery
  303: 
  304: 
  305: def test_hash_tool_schema_deterministic():
  306:     """Same schema content â†’ same hash regardless of key order."""
  307:     from core import hash_tool_schema
  308: 
  309:     a = {"name": "x", "input_schema": {"type": "object", "properties": {"a": {"type": "string"}}}}
  310:     b = {"input_schema": {"properties": {"a": {"type": "string"}}, "type": "object"}, "name": "x"}
  311:     assert hash_tool_schema(a) == hash_tool_schema(b)
  312:     # Different content â†’ different hash.
  313:     c = {"name": "x", "input_schema": {"type": "string"}}
  314:     assert hash_tool_schema(a) != hash_tool_schema(c)
  315: 
  316: 
  317: def test_notify_cache_deletion_skips_excluded_models():
  318:     """notify_cache_deletion returns False for Haiku (R4 #14 MUST)."""
  319:     from core import notify_cache_deletion
  320: 
  321:     assert notify_cache_deletion(
  322:         "anthropic.claude-haiku-4-5-20251001-v1:0", ["read_file"]
  323:     ) is False
  324:     assert notify_cache_deletion(
  325:         "anthropic.claude-sonnet-4-6", ["read_file"]
  326:     ) is True

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content _archive/compare_code/gg-claude-code-runnable/src/services/api/errors.ts | ForEach-Object { '"'{0,5}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content _archive/compare_code/gg-claude-code-runnable/src/services/api/cacheBreakDetection.ts | ForEach-Object { '"'{0,5}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "Block L|daemon|heartbeat|ADR-036|real-AWS|T2" compact_v5/_status/V5_DESIGN_DECISIONS.md compact_v5/_phase_2/wave_6/TEST_DESIGN.md compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md' in D:\Github\sagemaker-coding-agent
2026-05-03T08:07:43.772193Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.6 seconds
Output:
Get-Content : Cannot find path 'D:\Github\sagemaker-coding-agent\_archive\compare_code\gg-claude-code-runnable\src\serv
ices\api\cacheBreakDetection.ts' because it does not exist.
At line:2 char:7
+ $i=1; Get-Content _archive/compare_code/gg-claude-code-runnable/src/s ...
+       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (D:\Github\sagem...eakDetection.ts:String) [Get-Content], ItemNotFoundEx 
   ception
    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.GetContentCommand
 

 exited 1 in 570ms:
Get-Content : Cannot find path 'D:\Github\sagemaker-coding-agent\_archive\compare_code\gg-claude-code-runnable\src\serv
ices\api\cacheBreakDetection.ts' because it does not exist.
At line:2 char:7
+ $i=1; Get-Content _archive/compare_code/gg-claude-code-runnable/src/s ...
+       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (D:\Github\sagem...eakDetection.ts:String) [Get-Content], ItemNotFoundEx 
   ception
    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.GetContentCommand
 

 succeeded in 602ms:
    1: import {
    2:   APIConnectionError,
    3:   APIConnectionTimeoutError,
    4:   APIError,
    5: } from '@anthropic-ai/sdk'
    6: import type {
    7:   BetaMessage,
    8:   BetaStopReason,
    9: } from '@anthropic-ai/sdk/resources/beta/messages/messages.mjs'
   10: import { AFK_MODE_BETA_HEADER } from 'src/constants/betas.js'
   11: import type { SDKAssistantMessageError } from 'src/entrypoints/agentSdkTypes.js'
   12: import type {
   13:   AssistantMessage,
   14:   Message,
   15:   UserMessage,
   16: } from 'src/types/message.js'
   17: import {
   18:   getAnthropicApiKeyWithSource,
   19:   getClaudeAIOAuthTokens,
   20:   getOauthAccountInfo,
   21:   isClaudeAISubscriber,
   22: } from 'src/utils/auth.js'
   23: import {
   24:   createAssistantAPIErrorMessage,
   25:   NO_RESPONSE_REQUESTED,
   26: } from 'src/utils/messages.js'
   27: import {
   28:   getDefaultMainLoopModelSetting,
   29:   isNonCustomOpusModel,
   30: } from 'src/utils/model/model.js'
   31: import { getModelStrings } from 'src/utils/model/modelStrings.js'
   32: import { getAPIProvider } from 'src/utils/model/providers.js'
   33: import { getIsNonInteractiveSession } from '../../bootstrap/state.js'
   34: import {
   35:   API_PDF_MAX_PAGES,
   36:   PDF_TARGET_RAW_SIZE,
   37: } from '../../constants/apiLimits.js'
   38: import { isEnvTruthy } from '../../utils/envUtils.js'
   39: import { formatFileSize } from '../../utils/format.js'
   40: import { ImageResizeError } from '../../utils/imageResizer.js'
   41: import { ImageSizeError } from '../../utils/imageValidation.js'
   42: import {
   43:   type AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
   44:   logEvent,
   45: } from '../analytics/index.js'
   46: import {
   47:   type ClaudeAILimits,
   48:   getRateLimitErrorMessage,
   49:   type OverageDisabledReason,
   50: } from '../claudeAiLimits.js'
   51: import { shouldProcessRateLimits } from '../rateLimitMocking.js' // Used for /mock-limits command
   52: import { extractConnectionErrorDetails, formatAPIError } from './errorUtils.js'
   53: 
   54: export const API_ERROR_MESSAGE_PREFIX = 'API Error'
   55: 
   56: export function startsWithApiErrorPrefix(text: string): boolean {
   57:   return (
   58:     text.startsWith(API_ERROR_MESSAGE_PREFIX) ||
   59:     text.startsWith(`Please run /login Â· ${API_ERROR_MESSAGE_PREFIX}`)
   60:   )
   61: }
   62: export const PROMPT_TOO_LONG_ERROR_MESSAGE = 'Prompt is too long'
   63: 
   64: export function isPromptTooLongMessage(msg: AssistantMessage): boolean {
   65:   if (!msg.isApiErrorMessage) {
   66:     return false
   67:   }
   68:   const content = msg.message.content
   69:   if (!Array.isArray(content)) {
   70:     return false
   71:   }
   72:   return content.some(
   73:     block =>
   74:       block.type === 'text' &&
   75:       block.text.startsWith(PROMPT_TOO_LONG_ERROR_MESSAGE),
   76:   )
   77: }
   78: 
   79: /**
   80:  * Parse actual/limit token counts from a raw prompt-too-long API error
   81:  * message like "prompt is too long: 137500 tokens > 135000 maximum".
   82:  * The raw string may be wrapped in SDK prefixes or JSON envelopes, or
   83:  * have different casing (Vertex), so this is intentionally lenient.
   84:  */
   85: export function parsePromptTooLongTokenCounts(rawMessage: string): {
   86:   actualTokens: number | undefined
   87:   limitTokens: number | undefined
   88: } {
   89:   const match = rawMessage.match(
   90:     /prompt is too long[^0-9]*(\d+)\s*tokens?\s*>\s*(\d+)/i,
   91:   )
   92:   return {
   93:     actualTokens: match ? parseInt(match[1]!, 10) : undefined,
   94:     limitTokens: match ? parseInt(match[2]!, 10) : undefined,
   95:   }
   96: }
   97: 
   98: /**
   99:  * Returns how many tokens over the limit a prompt-too-long error reports,
  100:  * or undefined if the message isn't PTL or its errorDetails are unparseable.
  101:  * Reactive compact uses this gap to jump past multiple groups in one retry
  102:  * instead of peeling one-at-a-time.
  103:  */
  104: export function getPromptTooLongTokenGap(
  105:   msg: AssistantMessage,
  106: ): number | undefined {
  107:   if (!isPromptTooLongMessage(msg) || !msg.errorDetails) {
  108:     return undefined
  109:   }
  110:   const { actualTokens, limitTokens } = parsePromptTooLongTokenCounts(
  111:     msg.errorDetails,
  112:   )
  113:   if (actualTokens === undefined || limitTokens === undefined) {
  114:     return undefined
  115:   }
  116:   const gap = actualTokens - limitTokens
  117:   return gap > 0 ? gap : undefined
  118: }
  119: 
  120: /**
  121:  * Is this raw API error text a media-size rejection that stripImagesFromMessages
  122:  * can fix? Reactive compact's summarize retry uses this to decide whether to
  123:  * strip and retry (media error) or bail (anything else).
  124:  *
  125:  * Patterns MUST stay in sync with the getAssistantMessageFromError branches
  126:  * that populate errorDetails (~L523 PDF, ~L560 image, ~L573 many-image) and
  127:  * the classifyAPIError branches (~L929-946). The closed loop: errorDetails is
  128:  * only set after those branches already matched these same substrings, so
  129:  * isMediaSizeError(errorDetails) is tautologically true for that path. API
  130:  * wording drift causes graceful degradation (errorDetails stays undefined,
  131:  * caller short-circuits), not a false negative.
  132:  */
  133: export function isMediaSizeError(raw: string): boolean {
  134:   return (
  135:     (raw.includes('image exceeds') && raw.includes('maximum')) ||
  136:     (raw.includes('image dimensions exceed') && raw.includes('many-image')) ||
  137:     /maximum of \d+ PDF pages/.test(raw)
  138:   )
  139: }
  140: 
  141: /**
  142:  * Message-level predicate: is this assistant message a media-size rejection?
  143:  * Parallel to isPromptTooLongMessage. Checks errorDetails (the raw API error
  144:  * string populated by the getAssistantMessageFromError branches at ~L523/560/573)
  145:  * rather than content text, since media errors have per-variant content strings.
  146:  */
  147: export function isMediaSizeErrorMessage(msg: AssistantMessage): boolean {
  148:   return (
  149:     msg.isApiErrorMessage === true &&
  150:     msg.errorDetails !== undefined &&
  151:     isMediaSizeError(msg.errorDetails)
  152:   )
  153: }
  154: export const CREDIT_BALANCE_TOO_LOW_ERROR_MESSAGE = 'Credit balance is too low'
  155: export const INVALID_API_KEY_ERROR_MESSAGE = 'Not logged in Â· Please run /login'
  156: export const INVALID_API_KEY_ERROR_MESSAGE_EXTERNAL =
  157:   'Invalid API key Â· Fix external API key'
  158: export const ORG_DISABLED_ERROR_MESSAGE_ENV_KEY_WITH_OAUTH =
  159:   'Your ANTHROPIC_API_KEY belongs to a disabled organization Â· Unset the environment variable to use your subscription instead'
  160: export const ORG_DISABLED_ERROR_MESSAGE_ENV_KEY =
  161:   'Your ANTHROPIC_API_KEY belongs to a disabled organization Â· Update or unset the environment variable'
  162: export const TOKEN_REVOKED_ERROR_MESSAGE =
  163:   'OAuth token revoked Â· Please run /login'
  164: export const CCR_AUTH_ERROR_MESSAGE =
  165:   'Authentication error Â· This may be a temporary network issue, please try again'
  166: export const REPEATED_529_ERROR_MESSAGE = 'Repeated 529 Overloaded errors'
  167: export const CUSTOM_OFF_SWITCH_MESSAGE =
  168:   'Opus is experiencing high load, please use /model to switch to Sonnet'
  169: export const API_TIMEOUT_ERROR_MESSAGE = 'Request timed out'
  170: export function getPdfTooLargeErrorMessage(): string {
  171:   const limits = `max ${API_PDF_MAX_PAGES} pages, ${formatFileSize(PDF_TARGET_RAW_SIZE)}`
  172:   return getIsNonInteractiveSession()
  173:     ? `PDF too large (${limits}). Try reading the file a different way (e.g., extract text with pdftotext).`
  174:     : `PDF too large (${limits}). Double press esc to go back and try again, or use pdftotext to convert to text first.`
  175: }
  176: export function getPdfPasswordProtectedErrorMessage(): string {
  177:   return getIsNonInteractiveSession()
  178:     ? 'PDF is password protected. Try using a CLI tool to extract or convert the PDF.'
  179:     : 'PDF is password protected. Please double press esc to edit your message and try again.'
  180: }
  181: export function getPdfInvalidErrorMessage(): string {
  182:   return getIsNonInteractiveSession()
  183:     ? 'The PDF file was not valid. Try converting it to text first (e.g., pdftotext).'
  184:     : 'The PDF file was not valid. Double press esc to go back and try again with a different file.'
  185: }
  186: export function getImageTooLargeErrorMessage(): string {
  187:   return getIsNonInteractiveSession()
  188:     ? 'Image was too large. Try resizing the image or using a different approach.'
  189:     : 'Image was too large. Double press esc to go back and try again with a smaller image.'
  190: }
  191: export function getRequestTooLargeErrorMessage(): string {
  192:   const limits = `max ${formatFileSize(PDF_TARGET_RAW_SIZE)}`
  193:   return getIsNonInteractiveSession()
  194:     ? `Request too large (${limits}). Try with a smaller file.`
  195:     : `Request too large (${limits}). Double press esc to go back and try with a smaller file.`
  196: }
  197: export const OAUTH_ORG_NOT_ALLOWED_ERROR_MESSAGE =
  198:   'Your account does not have access to Claude Code. Please run /login.'
  199: 
  200: export function getTokenRevokedErrorMessage(): string {
  201:   return getIsNonInteractiveSession()
  202:     ? 'Your account does not have access to Claude. Please login again or contact your administrator.'
  203:     : TOKEN_REVOKED_ERROR_MESSAGE
  204: }
  205: 
  206: export function getOauthOrgNotAllowedErrorMessage(): string {
  207:   return getIsNonInteractiveSession()
  208:     ? 'Your organization does not have access to Claude. Please login again or contact your administrator.'
  209:     : OAUTH_ORG_NOT_ALLOWED_ERROR_MESSAGE
  210: }
  211: 
  212: /**
  213:  * Check if we're in CCR (Claude Code Remote) mode.
  214:  * In CCR mode, auth is handled via JWTs provided by the infrastructure,
  215:  * not via /login. Transient auth errors should suggest retrying, not logging in.
  216:  */
  217: function isCCRMode(): boolean {
  218:   return isEnvTruthy(process.env.CLAUDE_CODE_REMOTE)
  219: }
  220: 
  221: // Temp helper to log tool_use/tool_result mismatch errors
  222: function logToolUseToolResultMismatch(
  223:   toolUseId: string,
  224:   messages: Message[],
  225:   messagesForAPI: (UserMessage | AssistantMessage)[],
  226: ): void {
  227:   try {
  228:     // Find tool_use in normalized messages
  229:     let normalizedIndex = -1
  230:     for (let i = 0; i < messagesForAPI.length; i++) {
  231:       const msg = messagesForAPI[i]
  232:       if (!msg) continue
  233:       const content = msg.message.content
  234:       if (Array.isArray(content)) {
  235:         for (const block of content) {
  236:           if (
  237:             block.type === 'tool_use' &&
  238:             'id' in block &&
  239:             block.id === toolUseId
  240:           ) {
  241:             normalizedIndex = i
  242:             break
  243:           }
  244:         }
  245:       }
  246:       if (normalizedIndex !== -1) break
  247:     }
  248: 
  249:     // Find tool_use in original messages
  250:     let originalIndex = -1
  251:     for (let i = 0; i < messages.length; i++) {
  252:       const msg = messages[i]
  253:       if (!msg) continue
  254:       if (msg.type === 'assistant' && 'message' in msg) {
  255:         const content = msg.message.content
  256:         if (Array.isArray(content)) {
  257:           for (const block of content) {
  258:             if (
  259:               block.type === 'tool_use' &&
  260:               'id' in block &&
  261:               block.id === toolUseId
  262:             ) {
  263:               originalIndex = i
  264:               break
  265:             }
  266:           }
  267:         }
  268:       }
  269:       if (originalIndex !== -1) break
  270:     }
  271: 
  272:     // Build normalized sequence
  273:     const normalizedSeq: string[] = []
  274:     for (let i = normalizedIndex + 1; i < messagesForAPI.length; i++) {
  275:       const msg = messagesForAPI[i]
  276:       if (!msg) continue
  277:       const content = msg.message.content
  278:       if (Array.isArray(content)) {
  279:         for (const block of content) {
  280:           const role = msg.message.role
  281:           if (block.type === 'tool_use' && 'id' in block) {
  282:             normalizedSeq.push(`${role}:tool_use:${block.id}`)
  283:           } else if (block.type === 'tool_result' && 'tool_use_id' in block) {
  284:             normalizedSeq.push(`${role}:tool_result:${block.tool_use_id}`)
  285:           } else if (block.type === 'text') {
  286:             normalizedSeq.push(`${role}:text`)
  287:           } else if (block.type === 'thinking') {
  288:             normalizedSeq.push(`${role}:thinking`)
  289:           } else if (block.type === 'image') {
  290:             normalizedSeq.push(`${role}:image`)
  291:           } else {
  292:             normalizedSeq.push(`${role}:${block.type}`)
  293:           }
  294:         }
  295:       } else if (typeof content === 'string') {
  296:         normalizedSeq.push(`${msg.message.role}:string_content`)
  297:       }
  298:     }
  299: 
  300:     // Build pre-normalized sequence
  301:     const preNormalizedSeq: string[] = []
  302:     for (let i = originalIndex + 1; i < messages.length; i++) {
  303:       const msg = messages[i]
  304:       if (!msg) continue
  305: 
  306:       switch (msg.type) {
  307:         case 'user':
  308:         case 'assistant': {
  309:           if ('message' in msg) {
  310:             const content = msg.message.content
  311:             if (Array.isArray(content)) {
  312:               for (const block of content) {
  313:                 const role = msg.message.role
  314:                 if (block.type === 'tool_use' && 'id' in block) {
  315:                   preNormalizedSeq.push(`${role}:tool_use:${block.id}`)
  316:                 } else if (
  317:                   block.type === 'tool_result' &&
  318:                   'tool_use_id' in block
  319:                 ) {
  320:                   preNormalizedSeq.push(
  321:                     `${role}:tool_result:${block.tool_use_id}`,
  322:                   )
  323:                 } else if (block.type === 'text') {
  324:                   preNormalizedSeq.push(`${role}:text`)
  325:                 } else if (block.type === 'thinking') {
  326:                   preNormalizedSeq.push(`${role}:thinking`)
  327:                 } else if (block.type === 'image') {
  328:                   preNormalizedSeq.push(`${role}:image`)
  329:                 } else {
  330:                   preNormalizedSeq.push(`${role}:${block.type}`)
  331:                 }
  332:               }
  333:             } else if (typeof content === 'string') {
  334:               preNormalizedSeq.push(`${msg.message.role}:string_content`)
  335:             }
  336:           }
  337:           break
  338:         }
  339:         case 'attachment':
  340:           if ('attachment' in msg) {
  341:             preNormalizedSeq.push(`attachment:${msg.attachment.type}`)
  342:           }
  343:           break
  344:         case 'system':
  345:           if ('subtype' in msg) {
  346:             preNormalizedSeq.push(`system:${msg.subtype}`)
  347:           }
  348:           break
  349:         case 'progress':
  350:           if (
  351:             'progress' in msg &&
  352:             msg.progress &&
  353:             typeof msg.progress === 'object' &&
  354:             'type' in msg.progress
  355:           ) {
  356:             preNormalizedSeq.push(`progress:${msg.progress.type ?? 'unknown'}`)
  357:           } else {
  358:             preNormalizedSeq.push('progress:unknown')
  359:           }
  360:           break
  361:       }
  362:     }
  363: 
  364:     // Log to Statsig
  365:     logEvent('tengu_tool_use_tool_result_mismatch_error', {
  366:       toolUseId:
  367:         toolUseId as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
  368:       normalizedSequence: normalizedSeq.join(
  369:         ', ',
  370:       ) as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
  371:       preNormalizedSequence: preNormalizedSeq.join(
  372:         ', ',
  373:       ) as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
  374:       normalizedMessageCount: messagesForAPI.length,
  375:       originalMessageCount: messages.length,
  376:       normalizedToolUseIndex: normalizedIndex,
  377:       originalToolUseIndex: originalIndex,
  378:     })
  379:   } catch (_) {
  380:     // Ignore errors in debug logging
  381:   }
  382: }
  383: 
  384: /**
  385:  * Type guard to check if a value is a valid Message response from the API
  386:  */
  387: export function isValidAPIMessage(value: unknown): value is BetaMessage {
  388:   return (
  389:     typeof value === 'object' &&
  390:     value !== null &&
  391:     'content' in value &&
  392:     'model' in value &&
  393:     'usage' in value &&
  394:     Array.isArray((value as BetaMessage).content) &&
  395:     typeof (value as BetaMessage).model === 'string' &&
  396:     typeof (value as BetaMessage).usage === 'object'
  397:   )
  398: }
  399: 
  400: /** Lower-level error that AWS can return. */
  401: type AmazonError = {
  402:   Output?: {
  403:     __type?: string
  404:   }
  405:   Version?: string
  406: }
  407: 
  408: /**
  409:  * Given a response that doesn't look quite right, see if it contains any known error types we can extract.
  410:  */
  411: export function extractUnknownErrorFormat(value: unknown): string | undefined {
  412:   // Check if value is a valid object first
  413:   if (!value || typeof value !== 'object') {
  414:     return undefined
  415:   }
  416: 
  417:   // Amazon Bedrock routing errors
  418:   if ((value as AmazonError).Output?.__type) {
  419:     return (value as AmazonError).Output!.__type
  420:   }
  421: 
  422:   return undefined
  423: }
  424: 
  425: export function getAssistantMessageFromError(
  426:   error: unknown,
  427:   model: string,
  428:   options?: {
  429:     messages?: Message[]
  430:     messagesForAPI?: (UserMessage | AssistantMessage)[]
  431:   },
  432: ): AssistantMessage {
  433:   // Check for SDK timeout errors
  434:   if (
  435:     error instanceof APIConnectionTimeoutError ||
  436:     (error instanceof APIConnectionError &&
  437:       error.message.toLowerCase().includes('timeout'))
  438:   ) {
  439:     return createAssistantAPIErrorMessage({
  440:       content: API_TIMEOUT_ERROR_MESSAGE,
  441:       error: 'unknown',
  442:     })
  443:   }
  444: 
  445:   // Check for image size/resize errors (thrown before API call during validation)
  446:   // Use getImageTooLargeErrorMessage() to show "esc esc" hint for CLI users
  447:   // but a generic message for SDK users (non-interactive mode)
  448:   if (error instanceof ImageSizeError || error instanceof ImageResizeError) {
  449:     return createAssistantAPIErrorMessage({
  450:       content: getImageTooLargeErrorMessage(),
  451:     })
  452:   }
  453: 
  454:   // Check for emergency capacity off switch for Opus PAYG users
  455:   if (
  456:     error instanceof Error &&
  457:     error.message.includes(CUSTOM_OFF_SWITCH_MESSAGE)
  458:   ) {
  459:     return createAssistantAPIErrorMessage({
  460:       content: CUSTOM_OFF_SWITCH_MESSAGE,
  461:       error: 'rate_limit',
  462:     })
  463:   }
  464: 
  465:   if (
  466:     error instanceof APIError &&
  467:     error.status === 429 &&
  468:     shouldProcessRateLimits(isClaudeAISubscriber())
  469:   ) {
  470:     // Check if this is the new API with multiple rate limit headers
  471:     const rateLimitType = error.headers?.get?.(
  472:       'anthropic-ratelimit-unified-representative-claim',
  473:     ) as 'five_hour' | 'seven_day' | 'seven_day_opus' | null
  474: 
  475:     const overageStatus = error.headers?.get?.(
  476:       'anthropic-ratelimit-unified-overage-status',
  477:     ) as 'allowed' | 'allowed_warning' | 'rejected' | null
  478: 
  479:     // If we have the new headers, use the new message generation
  480:     if (rateLimitType || overageStatus) {
  481:       // Build limits object from error headers to determine the appropriate message
  482:       const limits: ClaudeAILimits = {
  483:         status: 'rejected',
  484:         unifiedRateLimitFallbackAvailable: false,
  485:         isUsingOverage: false,
  486:       }
  487: 
  488:       // Extract rate limit information from headers
  489:       const resetHeader = error.headers?.get?.(
  490:         'anthropic-ratelimit-unified-reset',
  491:       )
  492:       if (resetHeader) {
  493:         limits.resetsAt = Number(resetHeader)
  494:       }
  495: 
  496:       if (rateLimitType) {
  497:         limits.rateLimitType = rateLimitType
  498:       }
  499: 
  500:       if (overageStatus) {
  501:         limits.overageStatus = overageStatus
  502:       }
  503: 
  504:       const overageResetHeader = error.headers?.get?.(
  505:         'anthropic-ratelimit-unified-overage-reset',
  506:       )
  507:       if (overageResetHeader) {
  508:         limits.overageResetsAt = Number(overageResetHeader)
  509:       }
  510: 
  511:       const overageDisabledReason = error.headers?.get?.(
  512:         'anthropic-ratelimit-unified-overage-disabled-reason',
  513:       ) as OverageDisabledReason | null
  514:       if (overageDisabledReason) {
  515:         limits.overageDisabledReason = overageDisabledReason
  516:       }
  517: 
  518:       // Use the new message format for all new API rate limits
  519:       const specificErrorMessage = getRateLimitErrorMessage(limits, model)
  520:       if (specificErrorMessage) {
  521:         return createAssistantAPIErrorMessage({
  522:           content: specificErrorMessage,
  523:           error: 'rate_limit',
  524:         })
  525:       }
  526: 
  527:       // If getRateLimitErrorMessage returned null, it means the fallback mechanism
  528:       // will handle this silently (e.g., Opus -> Sonnet fallback for eligible users).
  529:       // Return NO_RESPONSE_REQUESTED so no error is shown to the user, but the
  530:       // message is still recorded in conversation history for Claude to see.
  531:       return createAssistantAPIErrorMessage({
  532:         content: NO_RESPONSE_REQUESTED,
  533:         error: 'rate_limit',
  534:       })
  535:     }
  536: 
  537:     // No quota headers â€” this is NOT a quota limit. Surface what the API actually
  538:     // said instead of a generic "Rate limit reached". Entitlement rejections
  539:     // (e.g. 1M context without Extra Usage) and infra capacity 429s land here.
  540:     if (error.message.includes('Extra usage is required for long context')) {
  541:       const hint = getIsNonInteractiveSession()
  542:         ? 'enable extra usage at claude.ai/settings/usage, or use --model to switch to standard context'
  543:         : 'run /extra-usage to enable, or /model to switch to standard context'
  544:       return createAssistantAPIErrorMessage({
  545:         content: `${API_ERROR_MESSAGE_PREFIX}: Extra usage is required for 1M context Â· ${hint}`,
  546:         error: 'rate_limit',
  547:       })
  548:     }
  549:     // SDK's APIError.makeMessage prepends "429 " and JSON-stringifies the body
  550:     // when there's no top-level .message â€” extract the inner error.message.
  551:     const stripped = error.message.replace(/^429\s+/, '')
  552:     const innerMessage = stripped.match(/"message"\s*:\s*"([^"]*)"/)?.[1]
  553:     const detail = innerMessage || stripped
  554:     return createAssistantAPIErrorMessage({
  555:       content: `${API_ERROR_MESSAGE_PREFIX}: Request rejected (429) Â· ${detail || 'this may be a temporary capacity issue â€” check status.anthropic.com'}`,
  556:       error: 'rate_limit',
  557:     })
  558:   }
  559: 
  560:   // Handle prompt too long errors (Vertex returns 413, direct API returns 400)
  561:   // Use case-insensitive check since Vertex returns "Prompt is too long" (capitalized)
  562:   if (
  563:     error instanceof Error &&
  564:     error.message.toLowerCase().includes('prompt is too long')
  565:   ) {
  566:     // Content stays generic (UI matches on exact string). The raw error with
  567:     // token counts goes into errorDetails â€” reactive compact's retry loop
  568:     // parses the gap from there via getPromptTooLongTokenGap.
  569:     return createAssistantAPIErrorMessage({
  570:       content: PROMPT_TOO_LONG_ERROR_MESSAGE,
  571:       error: 'invalid_request',
  572:       errorDetails: error.message,
  573:     })
  574:   }
  575: 
  576:   // Check for PDF page limit errors
  577:   if (
  578:     error instanceof Error &&
  579:     /maximum of \d+ PDF pages/.test(error.message)
  580:   ) {
  581:     return createAssistantAPIErrorMessage({
  582:       content: getPdfTooLargeErrorMessage(),
  583:       error: 'invalid_request',
  584:       errorDetails: error.message,
  585:     })
  586:   }
  587: 
  588:   // Check for password-protected PDF errors
  589:   if (
  590:     error instanceof Error &&
  591:     error.message.includes('The PDF specified is password protected')
  592:   ) {
  593:     return createAssistantAPIErrorMessage({
  594:       content: getPdfPasswordProtectedErrorMessage(),
  595:       error: 'invalid_request',
  596:     })
  597:   }
  598: 
  599:   // Check for invalid PDF errors (e.g., HTML file renamed to .pdf)
  600:   // Without this handler, invalid PDF document blocks persist in conversation
  601:   // context and cause every subsequent API call to fail with 400.
  602:   if (
  603:     error instanceof Error &&
  604:     error.message.includes('The PDF specified was not valid')
  605:   ) {
  606:     return createAssistantAPIErrorMessage({
  607:       content: getPdfInvalidErrorMessage(),
  608:       error: 'invalid_request',
  609:     })
  610:   }
  611: 
  612:   // Check for image size errors (e.g., "image exceeds 5 MB maximum: 5316852 bytes > 5242880 bytes")
  613:   if (
  614:     error instanceof APIError &&
  615:     error.status === 400 &&
  616:     error.message.includes('image exceeds') &&
  617:     error.message.includes('maximum')
  618:   ) {
  619:     return createAssistantAPIErrorMessage({
  620:       content: getImageTooLargeErrorMessage(),
  621:       errorDetails: error.message,
  622:     })
  623:   }
  624: 
  625:   // Check for many-image dimension errors (API enforces stricter 2000px limit for many-image requests)
  626:   if (
  627:     error instanceof APIError &&
  628:     error.status === 400 &&
  629:     error.message.includes('image dimensions exceed') &&
  630:     error.message.includes('many-image')
  631:   ) {
  632:     return createAssistantAPIErrorMessage({
  633:       content: getIsNonInteractiveSession()
  634:         ? 'An image in the conversation exceeds the dimension limit for many-image requests (2000px). Start a new session with fewer images.'
  635:         : 'An image in the conversation exceeds the dimension limit for many-image requests (2000px). Run /compact to remove old images from context, or start a new session.',
  636:       error: 'invalid_request',
  637:       errorDetails: error.message,
  638:     })
  639:   }
  640: 
  641:   // Server rejected the afk-mode beta header (plan does not include auto
  642:   // mode). AFK_MODE_BETA_HEADER is '' in non-TRANSCRIPT_CLASSIFIER builds,
  643:   // so the truthy guard keeps this inert there.
  644:   if (
  645:     AFK_MODE_BETA_HEADER &&
  646:     error instanceof APIError &&
  647:     error.status === 400 &&
  648:     error.message.includes(AFK_MODE_BETA_HEADER) &&
  649:     error.message.includes('anthropic-beta')
  650:   ) {
  651:     return createAssistantAPIErrorMessage({
  652:       content: 'Auto mode is unavailable for your plan',
  653:       error: 'invalid_request',
  654:     })
  655:   }
  656: 
  657:   // Check for request too large errors (413 status)
  658:   // This typically happens when a large PDF + conversation context exceeds the 32MB API limit
  659:   if (error instanceof APIError && error.status === 413) {
  660:     return createAssistantAPIErrorMessage({
  661:       content: getRequestTooLargeErrorMessage(),
  662:       error: 'invalid_request',
  663:     })
  664:   }
  665: 
  666:   // Check for tool_use/tool_result concurrency error
  667:   if (
  668:     error instanceof APIError &&
  669:     error.status === 400 &&
  670:     error.message.includes(
  671:       '`tool_use` ids were found without `tool_result` blocks immediately after',
  672:     )
  673:   ) {
  674:     // Log to Statsig if we have the message context
  675:     if (options?.messages && options?.messagesForAPI) {
  676:       const toolUseIdMatch = error.message.match(/toolu_[a-zA-Z0-9]+/)
  677:       const toolUseId = toolUseIdMatch ? toolUseIdMatch[0] : null
  678:       if (toolUseId) {
  679:         logToolUseToolResultMismatch(
  680:           toolUseId,
  681:           options.messages,
  682:           options.messagesForAPI,
  683:         )
  684:       }
  685:     }
  686: 
  687:     if (process.env.USER_TYPE === 'ant') {
  688:       const baseMessage = `API Error: 400 ${error.message}\n\nRun /share and post the JSON file to ${MACRO.FEEDBACK_CHANNEL}.`
  689:       const rewindInstruction = getIsNonInteractiveSession()
  690:         ? ''
  691:         : ' Then, use /rewind to recover the conversation.'
  692:       return createAssistantAPIErrorMessage({
  693:         content: baseMessage + rewindInstruction,
  694:         error: 'invalid_request',
  695:       })
  696:     } else {
  697:       const baseMessage = 'API Error: 400 due to tool use concurrency issues.'
  698:       const rewindInstruction = getIsNonInteractiveSession()
  699:         ? ''
  700:         : ' Run /rewind to recover the conversation.'
  701:       return createAssistantAPIErrorMessage({
  702:         content: baseMessage + rewindInstruction,
  703:         error: 'invalid_request',
  704:       })
  705:     }
  706:   }
  707: 
  708:   if (
  709:     error instanceof APIError &&
  710:     error.status === 400 &&
  711:     error.message.includes('unexpected `tool_use_id` found in `tool_result`')
  712:   ) {
  713:     logEvent('tengu_unexpected_tool_result', {})
  714:   }
  715: 
  716:   // Duplicate tool_use IDs (CC-1212). ensureToolResultPairing strips these
  717:   // before send, so hitting this means a new corruption path slipped through.
  718:   // Log for root-causing, and give users a recovery path instead of deadlock.
  719:   if (
  720:     error instanceof APIError &&
  721:     error.status === 400 &&
  722:     error.message.includes('`tool_use` ids must be unique')
  723:   ) {
  724:     logEvent('tengu_duplicate_tool_use_id', {})
  725:     const rewindInstruction = getIsNonInteractiveSession()
  726:       ? ''
  727:       : ' Run /rewind to recover the conversation.'
  728:     return createAssistantAPIErrorMessage({
  729:       content: `API Error: 400 duplicate tool_use ID in conversation history.${rewindInstruction}`,
  730:       error: 'invalid_request',
  731:       errorDetails: error.message,
  732:     })
  733:   }
  734: 
  735:   // Check for invalid model name error for subscription users trying to use Opus
  736:   if (
  737:     isClaudeAISubscriber() &&
  738:     error instanceof APIError &&
  739:     error.status === 400 &&
  740:     error.message.toLowerCase().includes('invalid model name') &&
  741:     (isNonCustomOpusModel(model) || model === 'opus')
  742:   ) {
  743:     return createAssistantAPIErrorMessage({
  744:       content:
  745:         'Claude Opus is not available with the Claude Pro plan. If you have updated your subscription plan recently, run /logout and /login for the plan to take effect.',
  746:       error: 'invalid_request',
  747:     })
  748:   }
  749: 
  750:   // Check for invalid model name error for Ant users. Claude Code may be
  751:   // defaulting to a custom internal-only model for Ants, and there might be
  752:   // Ants using new or unknown org IDs that haven't been gated in.
  753:   if (
  754:     process.env.USER_TYPE === 'ant' &&
  755:     !process.env.ANTHROPIC_MODEL &&
  756:     error instanceof Error &&
  757:     error.message.toLowerCase().includes('invalid model name')
  758:   ) {
  759:     // Get organization ID from config - only use OAuth account data when actively using OAuth
  760:     const orgId = getOauthAccountInfo()?.organizationUuid
  761:     const baseMsg = `[ANT-ONLY] Your org isn't gated into the \`${model}\` model. Either run \`claude\` with \`ANTHROPIC_MODEL=${getDefaultMainLoopModelSetting()}\``
  762:     const msg = orgId
  763:       ? `${baseMsg} or share your orgId (${orgId}) in ${MACRO.FEEDBACK_CHANNEL} for help getting access.`
  764:       : `${baseMsg} or reach out in ${MACRO.FEEDBACK_CHANNEL} for help getting access.`
  765: 
  766:     return createAssistantAPIErrorMessage({
  767:       content: msg,
  768:       error: 'invalid_request',
  769:     })
  770:   }
  771: 
  772:   if (
  773:     error instanceof Error &&
  774:     error.message.includes('Your credit balance is too low')
  775:   ) {
  776:     return createAssistantAPIErrorMessage({
  777:       content: CREDIT_BALANCE_TOO_LOW_ERROR_MESSAGE,
  778:       error: 'billing_error',
  779:     })
  780:   }
  781:   // "Organization has been disabled" â€” commonly a stale ANTHROPIC_API_KEY
  782:   // from a previous employer/project overriding subscription auth. Only handle
  783:   // the env-var case; apiKeyHelper and /login-managed keys mean the active
  784:   // auth's org is genuinely disabled with no dormant fallback to point at.
  785:   if (
  786:     error instanceof APIError &&
  787:     error.status === 400 &&
  788:     error.message.toLowerCase().includes('organization has been disabled')
  789:   ) {
  790:     const { source } = getAnthropicApiKeyWithSource()
  791:     // getAnthropicApiKeyWithSource conflates the env var with FD-passed keys
  792:     // under the same source value, and in CCR mode OAuth stays active despite
  793:     // the env var. The three guards ensure we only blame the env var when it's
  794:     // actually set and actually on the wire.
  795:     if (
  796:       source === 'ANTHROPIC_API_KEY' &&
  797:       process.env.ANTHROPIC_API_KEY &&
  798:       !isClaudeAISubscriber()
  799:     ) {
  800:       const hasStoredOAuth = getClaudeAIOAuthTokens()?.accessToken != null
  801:       // Not 'authentication_failed' â€” that triggers VS Code's showLogin(), but
  802:       // login can't fix this (approved env var keeps overriding OAuth). The fix
  803:       // is configuration-based (unset the var), so invalid_request is correct.
  804:       return createAssistantAPIErrorMessage({
  805:         error: 'invalid_request',
  806:         content: hasStoredOAuth
  807:           ? ORG_DISABLED_ERROR_MESSAGE_ENV_KEY_WITH_OAUTH
  808:           : ORG_DISABLED_ERROR_MESSAGE_ENV_KEY,
  809:       })
  810:     }
  811:   }
  812: 
  813:   if (
  814:     error instanceof Error &&
  815:     error.message.toLowerCase().includes('x-api-key')
  816:   ) {
  817:     // In CCR mode, auth is via JWTs - this is likely a transient network issue
  818:     if (isCCRMode()) {
  819:       return createAssistantAPIErrorMessage({
  820:         error: 'authentication_failed',
  821:         content: CCR_AUTH_ERROR_MESSAGE,
  822:       })
  823:     }
  824: 
  825:     // Check if the API key is from an external source
  826:     const { source } = getAnthropicApiKeyWithSource()
  827:     const isExternalSource =
  828:       source === 'ANTHROPIC_API_KEY' || source === 'apiKeyHelper'
  829: 
  830:     return createAssistantAPIErrorMessage({
  831:       error: 'authentication_failed',
  832:       content: isExternalSource
  833:         ? INVALID_API_KEY_ERROR_MESSAGE_EXTERNAL
  834:         : INVALID_API_KEY_ERROR_MESSAGE,
  835:     })
  836:   }
  837: 
  838:   // Check for OAuth token revocation error
  839:   if (
  840:     error instanceof APIError &&
  841:     error.status === 403 &&
  842:     error.message.includes('OAuth token has been revoked')
  843:   ) {
  844:     return createAssistantAPIErrorMessage({
  845:       error: 'authentication_failed',
  846:       content: getTokenRevokedErrorMessage(),
  847:     })
  848:   }
  849: 
  850:   // Check for OAuth organization not allowed error
  851:   if (
  852:     error instanceof APIError &&
  853:     (error.status === 401 || error.status === 403) &&
  854:     error.message.includes(
  855:       'OAuth authentication is currently not allowed for this organization',
  856:     )
  857:   ) {
  858:     return createAssistantAPIErrorMessage({
  859:       error: 'authentication_failed',
  860:       content: getOauthOrgNotAllowedErrorMessage(),
  861:     })
  862:   }
  863: 
  864:   // Generic handler for other 401/403 authentication errors
  865:   if (
  866:     error instanceof APIError &&
  867:     (error.status === 401 || error.status === 403)
  868:   ) {
  869:     // In CCR mode, auth is via JWTs - this is likely a transient network issue
  870:     if (isCCRMode()) {
  871:       return createAssistantAPIErrorMessage({
  872:         error: 'authentication_failed',
  873:         content: CCR_AUTH_ERROR_MESSAGE,
  874:       })
  875:     }
  876: 
  877:     return createAssistantAPIErrorMessage({
  878:       error: 'authentication_failed',
  879:       content: getIsNonInteractiveSession()
  880:         ? `Failed to authenticate. ${API_ERROR_MESSAGE_PREFIX}: ${error.message}`
  881:         : `Please run /login Â· ${API_ERROR_MESSAGE_PREFIX}: ${error.message}`,
  882:     })
  883:   }
  884: 
  885:   // Bedrock errors like "403 You don't have access to the model with the specified model ID."
  886:   // don't contain the actual model ID
  887:   if (
  888:     isEnvTruthy(process.env.CLAUDE_CODE_USE_BEDROCK) &&
  889:     error instanceof Error &&
  890:     error.message.toLowerCase().includes('model id')
  891:   ) {
  892:     const switchCmd = getIsNonInteractiveSession() ? '--model' : '/model'
  893:     const fallbackSuggestion = get3PModelFallbackSuggestion(model)
  894:     return createAssistantAPIErrorMessage({
  895:       content: fallbackSuggestion
  896:         ? `${API_ERROR_MESSAGE_PREFIX} (${model}): ${error.message}. Try ${switchCmd} to switch to ${fallbackSuggestion}.`
  897:         : `${API_ERROR_MESSAGE_PREFIX} (${model}): ${error.message}. Run ${switchCmd} to pick a different model.`,
  898:       error: 'invalid_request',
  899:     })
  900:   }
  901: 
  902:   // 404 Not Found â€” usually means the selected model doesn't exist or isn't
  903:   // available. Guide the user to /model so they can pick a valid one.
  904:   // For 3P users, suggest a specific fallback model they can try.
  905:   if (error instanceof APIError && error.status === 404) {
  906:     const switchCmd = getIsNonInteractiveSession() ? '--model' : '/model'
  907:     const fallbackSuggestion = get3PModelFallbackSuggestion(model)
  908:     return createAssistantAPIErrorMessage({
  909:       content: fallbackSuggestion
  910:         ? `The model ${model} is not available on your ${getAPIProvider()} deployment. Try ${switchCmd} to switch to ${fallbackSuggestion}, or ask your admin to enable this model.`
  911:         : `There's an issue with the selected model (${model}). It may not exist or you may not have access to it. Run ${switchCmd} to pick a different model.`,
  912:       error: 'invalid_request',
  913:     })
  914:   }
  915: 
  916:   // Connection errors (non-timeout) â€” use formatAPIError for detailed messages
  917:   if (error instanceof APIConnectionError) {
  918:     return createAssistantAPIErrorMessage({
  919:       content: `${API_ERROR_MESSAGE_PREFIX}: ${formatAPIError(error)}`,
  920:       error: 'unknown',
  921:     })
  922:   }
  923: 
  924:   if (error instanceof Error) {
  925:     return createAssistantAPIErrorMessage({
  926:       content: `${API_ERROR_MESSAGE_PREFIX}: ${error.message}`,
  927:       error: 'unknown',
  928:     })
  929:   }
  930:   return createAssistantAPIErrorMessage({
  931:     content: API_ERROR_MESSAGE_PREFIX,
  932:     error: 'unknown',
  933:   })
  934: }
  935: 
  936: /**
  937:  * For 3P users, suggest a fallback model when the selected model is unavailable.
  938:  * Returns a model name suggestion, or undefined if no suggestion is applicable.
  939:  */
  940: function get3PModelFallbackSuggestion(model: string): string | undefined {
  941:   if (getAPIProvider() === 'firstParty') {
  942:     return undefined
  943:   }
  944:   // @[MODEL LAUNCH]: Add a fallback suggestion chain for the new model â†’ previous version for 3P
  945:   const m = model.toLowerCase()
  946:   // If the failing model looks like an Opus 4.6 variant, suggest the default Opus (4.1 for 3P)
  947:   if (m.includes('opus-4-6') || m.includes('opus_4_6')) {
  948:     return getModelStrings().opus41
  949:   }
  950:   // If the failing model looks like a Sonnet 4.6 variant, suggest Sonnet 4.5
  951:   if (m.includes('sonnet-4-6') || m.includes('sonnet_4_6')) {
  952:     return getModelStrings().sonnet45
  953:   }
  954:   // If the failing model looks like a Sonnet 4.5 variant, suggest Sonnet 4
  955:   if (m.includes('sonnet-4-5') || m.includes('sonnet_4_5')) {
  956:     return getModelStrings().sonnet40
  957:   }
  958:   return undefined
  959: }
  960: 
  961: /**
  962:  * Classifies an API error into a specific error type for analytics tracking.
  963:  * Returns a standardized error type string suitable for Datadog tagging.
  964:  */
  965: export function classifyAPIError(error: unknown): string {
  966:   // Aborted requests
  967:   if (error instanceof Error && error.message === 'Request was aborted.') {
  968:     return 'aborted'
  969:   }
  970: 
  971:   // Timeout errors
  972:   if (
  973:     error instanceof APIConnectionTimeoutError ||
  974:     (error instanceof APIConnectionError &&
  975:       error.message.toLowerCase().includes('timeout'))
  976:   ) {
  977:     return 'api_timeout'
  978:   }
  979: 
  980:   // Check for repeated 529 errors
  981:   if (
  982:     error instanceof Error &&
  983:     error.message.includes(REPEATED_529_ERROR_MESSAGE)
  984:   ) {
  985:     return 'repeated_529'
  986:   }
  987: 
  988:   // Check for emergency capacity off switch
  989:   if (
  990:     error instanceof Error &&
  991:     error.message.includes(CUSTOM_OFF_SWITCH_MESSAGE)
  992:   ) {
  993:     return 'capacity_off_switch'
  994:   }
  995: 
  996:   // Rate limiting
  997:   if (error instanceof APIError && error.status === 429) {
  998:     return 'rate_limit'
  999:   }
 1000: 
 1001:   // Server overload (529)
 1002:   if (
 1003:     error instanceof APIError &&
 1004:     (error.status === 529 ||
 1005:       error.message?.includes('"type":"overloaded_error"'))
 1006:   ) {
 1007:     return 'server_overload'
 1008:   }
 1009: 
 1010:   // Prompt/content size errors
 1011:   if (
 1012:     error instanceof Error &&
 1013:     error.message
 1014:       .toLowerCase()
 1015:       .includes(PROMPT_TOO_LONG_ERROR_MESSAGE.toLowerCase())
 1016:   ) {
 1017:     return 'prompt_too_long'
 1018:   }
 1019: 
 1020:   // PDF errors
 1021:   if (
 1022:     error instanceof Error &&
 1023:     /maximum of \d+ PDF pages/.test(error.message)
 1024:   ) {
 1025:     return 'pdf_too_large'
 1026:   }
 1027: 
 1028:   if (
 1029:     error instanceof Error &&
 1030:     error.message.includes('The PDF specified is password protected')
 1031:   ) {
 1032:     return 'pdf_password_protected'
 1033:   }
 1034: 
 1035:   // Image size errors
 1036:   if (
 1037:     error instanceof APIError &&
 1038:     error.status === 400 &&
 1039:     error.message.includes('image exceeds') &&
 1040:     error.message.includes('maximum')
 1041:   ) {
 1042:     return 'image_too_large'
 1043:   }
 1044: 
 1045:   // Many-image dimension errors
 1046:   if (
 1047:     error instanceof APIError &&
 1048:     error.status === 400 &&
 1049:     error.message.includes('image dimensions exceed') &&
 1050:     error.message.includes('many-image')
 1051:   ) {
 1052:     return 'image_too_large'
 1053:   }
 1054: 
 1055:   // Tool use errors (400)
 1056:   if (
 1057:     error instanceof APIError &&
 1058:     error.status === 400 &&
 1059:     error.message.includes(
 1060:       '`tool_use` ids were found without `tool_result` blocks immediately after',
 1061:     )
 1062:   ) {
 1063:     return 'tool_use_mismatch'
 1064:   }
 1065: 
 1066:   if (
 1067:     error instanceof APIError &&
 1068:     error.status === 400 &&
 1069:     error.message.includes('unexpected `tool_use_id` found in `tool_result`')
 1070:   ) {
 1071:     return 'unexpected_tool_result'
 1072:   }
 1073: 
 1074:   if (
 1075:     error instanceof APIError &&
 1076:     error.status === 400 &&
 1077:     error.message.includes('`tool_use` ids must be unique')
 1078:   ) {
 1079:     return 'duplicate_tool_use_id'
 1080:   }
 1081: 
 1082:   // Invalid model errors (400)
 1083:   if (
 1084:     error instanceof APIError &&
 1085:     error.status === 400 &&
 1086:     error.message.toLowerCase().includes('invalid model name')
 1087:   ) {
 1088:     return 'invalid_model'
 1089:   }
 1090: 
 1091:   // Credit/billing errors
 1092:   if (
 1093:     error instanceof Error &&
 1094:     error.message
 1095:       .toLowerCase()
 1096:       .includes(CREDIT_BALANCE_TOO_LOW_ERROR_MESSAGE.toLowerCase())
 1097:   ) {
 1098:     return 'credit_balance_low'
 1099:   }
 1100: 
 1101:   // Authentication errors
 1102:   if (
 1103:     error instanceof Error &&
 1104:     error.message.toLowerCase().includes('x-api-key')
 1105:   ) {
 1106:     return 'invalid_api_key'
 1107:   }
 1108: 
 1109:   if (
 1110:     error instanceof APIError &&
 1111:     error.status === 403 &&
 1112:     error.message.includes('OAuth token has been revoked')
 1113:   ) {
 1114:     return 'token_revoked'
 1115:   }
 1116: 
 1117:   if (
 1118:     error instanceof APIError &&
 1119:     (error.status === 401 || error.status === 403) &&
 1120:     error.message.includes(
 1121:       'OAuth authentication is currently not allowed for this organization',
 1122:     )
 1123:   ) {
 1124:     return 'oauth_org_not_allowed'
 1125:   }
 1126: 
 1127:   // Generic auth errors
 1128:   if (
 1129:     error instanceof APIError &&
 1130:     (error.status === 401 || error.status === 403)
 1131:   ) {
 1132:     return 'auth_error'
 1133:   }
 1134: 
 1135:   // Bedrock-specific errors
 1136:   if (
 1137:     isEnvTruthy(process.env.CLAUDE_CODE_USE_BEDROCK) &&
 1138:     error instanceof Error &&
 1139:     error.message.toLowerCase().includes('model id')
 1140:   ) {
 1141:     return 'bedrock_model_access'
 1142:   }
 1143: 
 1144:   // Status code based fallbacks
 1145:   if (error instanceof APIError) {
 1146:     const status = error.status
 1147:     if (status >= 500) return 'server_error'
 1148:     if (status >= 400) return 'client_error'
 1149:   }
 1150: 
 1151:   // Connection errors - check for SSL/TLS issues first
 1152:   if (error instanceof APIConnectionError) {
 1153:     const connectionDetails = extractConnectionErrorDetails(error)
 1154:     if (connectionDetails?.isSSLError) {
 1155:       return 'ssl_cert_error'
 1156:     }
 1157:     return 'connection_error'
 1158:   }
 1159: 
 1160:   return 'unknown'
 1161: }
 1162: 
 1163: export function categorizeRetryableAPIError(
 1164:   error: APIError,
 1165: ): SDKAssistantMessageError {
 1166:   if (
 1167:     error.status === 529 ||
 1168:     error.message?.includes('"type":"overloaded_error"')
 1169:   ) {
 1170:     return 'rate_limit'
 1171:   }
 1172:   if (error.status === 429) {
 1173:     return 'rate_limit'
 1174:   }
 1175:   if (error.status === 401 || error.status === 403) {
 1176:     return 'authentication_failed'
 1177:   }
 1178:   if (error.status !== undefined && error.status >= 408) {
 1179:     return 'server_error'
 1180:   }
 1181:   return 'unknown'
 1182: }
 1183: 
 1184: export function getErrorMessageIfRefusal(
 1185:   stopReason: BetaStopReason | null,
 1186:   model: string,
 1187: ): AssistantMessage | undefined {
 1188:   if (stopReason !== 'refusal') {
 1189:     return
 1190:   }
 1191: 
 1192:   logEvent('tengu_refusal_api_response', {})
 1193: 
 1194:   const baseMessage = getIsNonInteractiveSession()
 1195:     ? `${API_ERROR_MESSAGE_PREFIX}: Claude Code is unable to respond to this request, which appears to violate our Usage Policy (https://www.anthropic.com/legal/aup). Try rephrasing the request or attempting a different approach.`
 1196:     : `${API_ERROR_MESSAGE_PREFIX}: Claude Code is unable to respond to this request, which appears to violate our Usage Policy (https://www.anthropic.com/legal/aup). Please double press esc to edit your last message or start a new session for Claude Code to assist with a different task.`
 1197: 
 1198:   const modelSuggestion =
 1199:     model !== 'claude-sonnet-4-20250514'
 1200:       ? ' If you are seeing this refusal repeatedly, try running /model claude-sonnet-4-20250514 to switch models.'
 1201:       : ''
 1202: 
 1203:   return createAssistantAPIErrorMessage({
 1204:     content: baseMessage + modelSuggestion,
 1205:     error: 'invalid_request',
 1206:   })
 1207: }

 succeeded in 837ms:
compact_v5/_status/V5_DESIGN_DECISIONS.md:1127:## ADR-036 — Block L (v5.0.1): Error/retry/cache-break + Bedrock guardrails
compact_v5/_status/V5_DESIGN_DECISIONS.md:1130:**Phase ID**: v5.0.1 Block L
compact_v5/_status/V5_DESIGN_DECISIONS.md:1134:SYNTHESIS_MASTER §Block L lists ~966 LOC of Bedrock guardrails:
compact_v5/_status/V5_DESIGN_DECISIONS.md:1142:- 30s heartbeat during long calls.
compact_v5/_status/V5_DESIGN_DECISIONS.md:1171:#### 3. T2 daemon-thread + heartbeat tests deferred to Block J
compact_v5/_status/V5_DESIGN_DECISIONS.md:1172:The `test_daemon_thread_bedrock_call_responds_to_ctrl_c` and
compact_v5/_status/V5_DESIGN_DECISIONS.md:1173:`test_30s_heartbeat_during_long_call` T2 tests are timing-sensitive
compact_v5/_status/V5_DESIGN_DECISIONS.md:1175:are deferred to Block J's real-AWS gate where they have natural fit.
compact_v5/_status/V5_DESIGN_DECISIONS.md:1176:Block L ships the underlying mechanism (error classifier + cache-break
compact_v5/_status/V5_DESIGN_DECISIONS.md:1188:The deferred T2 tests are integration-level (timing + Ctrl-C
compact_v5/_status/V5_DESIGN_DECISIONS.md:1198:  (9 tests + 2 T2 deferred-skipped)
compact_v5/_status/V5_DESIGN_DECISIONS.md:1210:- Daemon-thread + heartbeat integration with the actual chat() call
compact_v5/_status/V5_DESIGN_DECISIONS.md:1211:  is wired in Block J (real-AWS gate) where the long-running call
compact_v5/_status/V5_DESIGN_DECISIONS.md:1225:TRIGGER ONLY**. No daemon, no auto-fire, no env-auto-enable, no
compact_v5/_status/V5_DESIGN_DECISIONS.md:1247:#### 2. NO daemon, NO auto-fire (test_dream_no_daemon_no_auto_fire)
compact_v5/_status/V5_DESIGN_DECISIONS.md:1248:The `test_dream_no_daemon_no_auto_fire` test scans the entire
compact_v5/_status/V5_DESIGN_DECISIONS.md:1270:#### 4. T5 real-AWS deferral to R-tier R6
compact_v5/_status/V5_DESIGN_DECISIONS.md:1309:1. v5's /dream is MANUAL TRIGGER ONLY. No daemon, no auto-fire (the
compact_v5/_status/V5_DESIGN_DECISIONS.md:1310:   `test_dream_no_daemon_no_auto_fire` lock test grep-scans the
compact_v5/_status/V5_DESIGN_DECISIONS.md:1500:#### 3. T5 real-AWS deferral to R-tier R3
compact_v5/_status/V5_DESIGN_DECISIONS.md:1506:the rest of the real-AWS suite.
compact_v5/_status/V5_DESIGN_DECISIONS.md:1513:runtime concern. The wiring belongs with Block L (real-Bedrock cache
compact_v5/_status/V5_DESIGN_DECISIONS.md:1533:  in Block L where the real-Bedrock cache-prefix exercise (R-tier R3)
compact_v5/_status/V5_DESIGN_DECISIONS.md:1592:real-AWS test isn't worth burning credit during unit-test phase when
compact_v5/_status/V5_DESIGN_DECISIONS.md:1625:  skip net new). The +1 skip is the T5 real-AWS deferral.
compact_v5/_status/V5_DESIGN_DECISIONS.md:1633:- The T5 real-AWS orchestration test moves to R-tier R3 (sub-agent
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:15:1. R4 #2 `parseMaxTokensContextOverflowError` (Block L)
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:16:2. R4 #9 `extractNestedErrorMessage` Bedrock 5xx HTML (Block L)
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:17:3. R4 #14 `isExcludedModel` Haiku cache-break suppression (Block L)
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:289:| H+1 | autoDream consolidation engine — MANUAL-TRIGGER ONLY (user decision 2026-05-01) | Runnable | services/autoDream/* | 350 | HIGH | NEEDS-ADAPTATION | Memory consolidation engine: 4-phase prompt (Orient → Gather → Consolidate → Prune+Index) + lock + rollback-on-fail. **NO DAEMON, NO AUTO-FIRE, NO ENV AUTO-ENABLE.** Fires ONLY when user invokes `/dream` slash command (D-11). Drop `autoDream` daemon scheduler + 3-gate auto-trigger + `SAGEMAKER_AUTO_DREAM` env var. Target: `runtime/dream.py` (NOT `auto_dream.py`). USER_GUIDE must document `/dream` usage clearly. |
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:293:### Block L (Error/retry/cache-break)
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:326:**Block L total NEW: ~966 LOC.**
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:439:| **H+ — Memory Consolidation Engine (manual `/dream` only)** | R12 R12-1 — fits Q3 long/complex coding axis; pays down memory debt across sessions. ~350 LOC. **NO daemon, NO auto-fire** (user decision 2026-05-01). Fires only when user runs `/dream`. | 350 | After Block H |
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:456:- Block L: most rows (PromptStateSnapshot, Haiku exclude, error humanizer)
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:470:- H+1 (memory consolidation engine, manual /dream only) — synchronous Python (no threading, no asyncio, no daemon)
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:499:| `core/retry.py` RetryHandler (V1 lesser #12) | `compact_v5/MAIN/agent/core/retry.py` | Decide: keep v4 RetryHandler OR Block L's withRetry; CHOOSE Block L (Runnable supersedes per Q3). |
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:523:| V1.12 | `RetryHandler` + `RETRY` | :116, :179 | superseded by Block L (Runnable withRetry) | DECISION | Block L IS the v5 retry path; v4 `RetryHandler` not separately ported |
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:607:| `cron` / scheduled remote agents (R2 ScheduleCronTool) | No daemon in SageMaker | — |
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:659:        → H+  (NEW — memory consolidation engine, manual /dream only, no daemon)
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:660:        → L   (Error/retry/cache-break + Bedrock guardrails + daemon-thread call)
compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:699:- 3 new Blocks: G3 (Coordinator Prompt), F2 (Auto-Continuation), H+ (Memory Consolidation Engine, manual /dream only — no daemon)
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:6:**Constraint**: minimize AWS spend; max real-AWS cost across full build = ~$0.50.
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:15:| **T2 Integration** | pytest integration test, mocked Bedrock with canned responses, real file IO + real subprocess | every Block close | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:26:1. Every T1 + T2 test green
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:46:| `test_widget_chat_ui_renders` | T2 | `create_chat_ui()` returns a chat-UI handle wired to a real Agent. Accepts `WidgetChatUI` (with non-empty `_panel`) when ipywidgets is installed; falls back to `ConsoleChatUI` (with non-empty `render()`) when ipywidgets is unavailable — matches Phase 11 ADR-017 fallback contract. | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:53:- T2 accepts ConsoleChatUI fallback because the Phase 11 factory branches on ipywidgets availability (`_IPYWIDGETS_OK`). On a CI runner without ipywidgets, the WidgetChatUI branch is unreachable; the fallback is the production behavior and is what users with no widget host will see.
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:65:| `test_count_tokens_with_bedrock_mocked` | T2 | mocked `bedrock-runtime.count_tokens` response parsed correctly | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:82:| `test_filecache_thread_local_isolation` | T2 | parent `_FILES_READ` not visible inside sub-agent thread context (uses verified v4 APIs `save_and_clear_context` + `enter_thread_local_context`) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:83:| `test_subagent_token_attribution` | T2 | spawn parent + sub-agent → assert `TOKENS.parent_input_tokens > 0` AND `TOKENS.subagent_input_tokens["build"] > 0` AND `session_cost == sum_of(per_agent_cost) ± $0.0001` | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:94:| `test_exec_limit_200_then_201_blocked` | T2 | run 200 mocked bash → 201st returns exact error including `OTHER TOOLS STILL WORK: read_file, grep, glob, edit_file, write_file, notebook_edit, task, ask_user, view_image, web_fetch are NOT counted by this limit.` (closes PS#7) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:95:| `test_repetition_detector_blocks_3rd_dup` | T2 | same `read_file(path=X)` 3 times → 3rd blocked with dedup message | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:115:| `test_approval_gate_blocks_until_approve` | T2 | write_file with `require_tool_approval=True` blocks; mock approve → unblocks | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:116:| `test_approval_dialog_shows_diff` | T2 | `pending_approval` UI renders colored diff (red/green/gray context) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:117:| `test_approval_per_tool_always_allow` | T2 | "Always allow" sets `_always_allowed[tool_name]=True`; subsequent calls skip dialog | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:118:| `test_rate_limit_100_per_min` | T2 | 101st message in 60s window → rate-limit error with countdown | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:119:| `test_stop_button_halts_run` | T2 | `Agent.stop()` mid-tool-loop sets stop flag; QueryEngine respects it | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:120:| `test_ipywidgets_fallback_text_mode` | T2 | when `ipywidgets` unavailable, `WidgetChatUI` falls back to `ConsoleChatUI` with `ask_user`-text-mode for approvals (60s watchdog timeout) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:121:| `test_permission_dialog_reason_prompt` | T2 | dialog shows model's "reason" string from tool_use args | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:131:| `test_slash_dispatch_/cost` | T2 | `/cost` returns formatted 4-line cost block | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:132:| `test_slash_dispatch_/status` | T2 | `/status` returns status with model + active skills + phase | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:133:| `test_slash_dispatch_/save_<name>` | T2 | `/save mywork` writes `sessions/mywork.json` with full state | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:134:| `test_slash_dispatch_/load_<name>` | T2 | `/load mywork` restores state including `TOKENS.session_cost` | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:135:| `test_slash_dispatch_/compact` | T2 | `/compact` invokes `Compactor.compact()` (Block A trigger) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:136:| `test_slash_dispatch_/clean` | T2 | `/clean` removes `audit_logs/` + `sessions/` + `.snapshots/` files | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:137:| `test_slash_dispatch_/skills_list` | T2 | `/skills` lists all 10 skills | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:138:| `test_slash_dispatch_/skill_use_clara` | T2 | `/skill use clara` resolves `clara` → `clara-review` (fuzzy from Block I) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:139:| `test_slash_dispatch_/skill_apply_proposal` | T2 | `/skill apply <name>` shows diff + applies | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:140:| `test_slash_dispatch_/revert_<file>` | T2 | `/revert path/to/file.py` rolls back to last snapshot | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:141:| `test_slash_dispatch_/context` | T2 | `/context` shows token/context bloat diagnostic | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:142:| `test_slash_dispatch_/verify_quick` | T2 | `/verify quick` invokes verify skill | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:143:| `test_slash_dispatch_/checkpoint_create_v1` | T2 | `/checkpoint create v1` snapshots all touched files | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:144:| `test_slash_dispatch_/checkpoint_restore_v1` | T2 | `/checkpoint restore v1` rolls back all to v1 state | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:145:| `test_slash_dispatch_/phase_text` | T2 | `/phase Phase 2 build` sets work-phase tag in status bar | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:146:| `test_slash_dispatch_/diffs_summary` | T2 | `/diffs summary` shows session edit history summary | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:147:| `test_slash_dispatch_/regression` | T2 | `/regression` runs `git diff HEAD --stat` + suggests test cmd | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:148:| `test_slash_dispatch_/done_quick` | T2 | `/done quick` runs simplify → verify pipeline → READY-TO-SHIP verdict | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:149:| `test_slash_dispatch_/commands` | T2 | `/commands` lists custom commands from `agent_config.json` | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:150:| `test_slash_dispatch_/auth_token` | T2 | `/auth <token>` validates against `os.getenv(CONFIG.auth_token_env)` (when `require_auth=True`) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:151:| `test_slash_dispatch_/simplify_falls_through_to_skill` | T2 | `/simplify` (no dedicated handler) hits expander at `:11330` → resolves to `skills/simplify/SKILL.md` | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:152:| `test_slash_dispatch_/dream_invokes_consolidation` | T2 | `/dream` invokes Block H+ memory consolidation (manual-only) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:153:| `test_slash_dispatch_/init_scaffolds_claude_md` | T2 | `/init` generates project CLAUDE.md from interactive prompt | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:154:| `test_slash_dispatch_/skillify_captures_session` | T2 | `/skillify` runs 4-round AskUserQuestion → saves new skill | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:155:| `test_slash_dispatch_/promote_to_skill` | T2 | `/promote-to-skill` writes proposal to `state/skill-proposals/` | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:156:| `test_dispatcher_unknown_slash_falls_through` | T2 | `/unknown_command` not in registry → falls through to chat (not error) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:166:| `test_compactor_2stage_prune_plus_llm_summary` | T2 | mocked LLM summary; assert prune step removes tool outputs older than threshold; LLM step generates 13-section template | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:167:| `test_microcompact_threshold_70pct` | T2 | when `total_tokens / context_window > 0.70` → microcompact fires | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:168:| `test_context_collapse_threshold_85pct` | T2 | when > 0.85 → context_collapse fires | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:169:| `test_cold_cache_30min_idle_triggers_microcompact` | T2 | mock `time.time()` to simulate 30min idle → next msg → microcompact fires + log line `[i] Cold cache detected` (closes PS#3) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:170:| `test_keep_last_n_cold_cache_1` | T2 | after cold-cache compact, only last 1 message retained | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:171:| `test_post_compact_files_read_clear` | T2 | after compact, `_FILES_READ.clear()` runs (model can re-read files) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:172:| `test_post_compact_todo_restoration_message` | T2 | after compact, `build_todo_restoration_message` injected | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:173:| `test_auto_compact_circuit_breaker_3_failures` | T2 | 3 consecutive `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES` → autoCompact disabled with warning | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:174:| `test_cache_edits_per_tool_invalidation` | T2 | per-tool schema hash change → only that tool's cache invalidated | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:175:| `test_a28_cache_invariant_no_mid_session_rebuild` | T2 | system prompt rebuild attempted mid-conversation → blocked with warning (`/cmd --now` opt-in only) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:176:| `test_h2_stub_injection_for_orphan_tool_use` | T2 | post-compact, dangling `tool_use` block → synthetic `tool_result` stub injected (prevents Bedrock 400) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:192:| `test_dark_mode_toggle_swaps_theme` | T2 | dark-mode toggle swaps theme dict; chat re-renders | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:193:| `test_model_dropdown_lists_all_models` | T2 | dropdown contains Haiku-4.5 + Sonnet-4.6 + Opus options | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:196:| `test_session_dropdown_lists_saves` | T2 | session dropdown lists all `sessions/*.json` files | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:197:| `test_session_load_button_restores` | T2 | clicking load → `SessionManager.load()` → state restored | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:198:| `test_auto_save_on_send` | T2 | every send auto-saves to `last_session.json` | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:210:| `test_f2_auto_continue_at_under_90pct` | T2 | iteration_used < 90% AND not diminishing-returns → auto-continue | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:211:| `test_f2_blocks_at_90pct` | T2 | iteration_used >= 90% → halts + asks user | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:212:| `test_f2_respects_cost_cap` | T2 | even if iteration_used < 90%, if `session_cost > session_cost_limit` → halt | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:225:| `test_skill_paths_frontmatter_auto_activate` | T2 | skill with `paths: ["*.py"]` auto-activates when user edits .py file | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:226:| `test_skill_disable_model_invocation` | T2 | skill with `disable_model_invocation: true` not visible to model but callable by user | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:227:| `test_skill_enabled_when_config_flag` | T2 | skill with `enabled_when: CONFIG.advanced_mode` only loads when flag True | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:228:| `test_skillify_4_round_interview` | T2 | `/skillify` runs 4 AskUserQuestion rounds → writes `skills/<new>/SKILL.md` | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:241:| `test_infinite_loop_blocked_at_retry_limit` | T2 | model returns malformed structured output 3x → halt | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:252:| `test_subagent_build_spawns_worktree` | T2 | `task(subagent_type="build")` creates `worktrees/<id>/` (mocked git) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:253:| `test_subagent_verify_loads_verify_skill` | T2 | `task(subagent_type="verify")` loads verify skill in sub-agent context | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:256:| `test_max_subagent_depth_2_blocks_grandchild` | T2 | parent → child OK; child → grandchild blocked with `MAX_SUBAGENT_DEPTH=2` error (Wave 6 GAP fix) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:257:| `test_iteration_budget_shared_object_identity` | T2 | parent and sub-agent share SAME `IterationBudget` object (object identity check) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:258:| `test_worktree_cleanup_on_completion` | T2 | sub-agent completion removes worktree | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:299:| `test_session_memory_compact_no_400_sequence` | T2 | compact run on session with mixed tool_use/tool_result → resulting messages valid for Bedrock | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:305:### Block H+ — Memory consolidation engine (`/dream` MANUAL ONLY, no daemon)
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:311:| `test_dream_rollback_on_failure` | T2 | mid-run failure → `memory.md.bak` restored; original `memory.md` untouched | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:312:| `test_dream_no_daemon_no_auto_fire` | T1 | search v5 codebase: no `Thread`/`asyncio.create_task`/`atexit.register(dream)`/`SAGEMAKER_AUTO_DREAM` env var (verifies user decision 2026-05-01) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:319:### Block L — Error/retry/cache-break + Bedrock guardrails + daemon-thread call
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:329:| `test_daemon_thread_bedrock_call_responds_to_ctrl_c` | T2 | Bedrock call wrapped in daemon thread; main thread Ctrl-C raises KeyboardInterrupt cleanly | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:330:| `test_30s_heartbeat_during_long_call` | T2 | heartbeat ping every 30s during long call → status bar updates | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:332:**Block L ships when**: 8/8 green. **Total AWS cost: $0.**
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:340:| `test_parallel_exec_3_independent_reads` | T2 | 3 read_file calls dispatched in parallel → completion in MAX(call_time), not SUM | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:341:| `test_parallel_exec_path_conflict_serializes_writes` | T2 | 2 write_file to same path → serialized (not parallel) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:342:| `test_tool_call_dedup_blocks_redundant` | T2 | same `(tool_name, args)` 3x in one batch → 2 calls deduped | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:347:| `test_n7_partial_tool_names_warning_on_disconnect` | T2 | mid-call disconnect → warning + synthetic tool_result stub | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:365:| `test_tool_semantic_search_index_then_search` | T2 | `semantic_search(action="index", path=".")` then `action="search", query="..."` returns hits | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:366:| `test_tool_web_fetch_html_to_markdown` | T2 | mocked HTTP response → `web_fetch` returns markdown text | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:367:| `test_tool_ask_user_blocks_then_unblocks` | T2 | `ask_user` blocks until user responds; mock response unblocks | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:376:This is THE final gate before tagging. **All real-AWS testing concentrates here.**
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:410:## R-tier — high-value real-AWS scenarios (added 2026-05-01 per user directive)
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:429:| **R12** | Multi-tool malformed args stress: model returns `{"path": "/tmp/", "content": "<UNCLOSED` → JSON repair fires; model returns surrogate-pair Unicode → sanitizer fires | Block L Bedrock error categories; H1 surrogate sanitize | Haiku-4.5 | $0.20 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:454:| Run pytest `tests/` (T1+T2) green | end of every Block | pytest | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:474:| All T2 integration tests | ~100 | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:478:| **R-tier high-value end-to-end real-AWS scenarios** (R1-R12, run after Block K, before tag) | 12 scenarios | **~$3-7** (caps total $7) |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:490:pytest tests/                                    # T1 + T2
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:527:- T1/T2/T3/T4 test red

codex
The Python code is compact, so the main risk is semantic mismatch with Runnable or under-matched Bedrock shapes. I found one referenced runnable path casing mismatch and am using `rg` to jump straight to the relevant functions.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "parseMaxTokens|extractNested|getRetryAfter|Retry-After|cacheBreak|isExcluded|notify_cache|cache" _archive/compare_code/gg-claude-code-runnable/src/services/api _archive/compare_code/gg-claude-code-runnable/src -g "*.ts"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem _archive/compare_code/gg-claude-code-runnable/src/services/api | Select-Object Name' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff -- v5.0.1-block-h-plus..HEAD -- compact_v5/MAIN/agent/core/errors.py compact_v5/MAIN/agent/core/cache_break_detection.py compact_v5/MAIN/agent/core/__init__.py compact_v5/MAIN/agent/tests/integration/test_block_l.py' in D:\Github\sagemaker-coding-agent
 succeeded in 521ms:
 succeeded in 686ms:

Name                        
----                        
adminRequests.ts            
bootstrap.ts                
claude.ts                   
client.ts                   
dumpPrompts.ts              
emptyUsage.ts               
errors.ts                   
errorUtils.ts               
filesApi.ts                 
firstTokenDate.ts           
grove.ts                    
logging.ts                  
metricsOptOut.ts            
overageCreditGrant.ts       
promptCacheBreakDetection.ts
referral.ts                 
sessionIngress.ts           
ultrareviewQuota.ts         
usage.ts                    
withRetry.ts                



 succeeded in 4625ms:
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:121:  // CLAUDE.md content cached by context.ts for the auto-mode classifier.
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:123:  cachedClaudeMdContent: string | null
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:202:  // System prompt section cache state
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:220:  // Cached prompt cache 1h TTL allowlist from GrowthBook (session-stable)
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:223:  // evaluation so mid-session overage flips don't change the cache_control
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:224:  // TTL, which would bust the server-side prompt cache.
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:228:  // Shift+Tab toggles don't bust the ~50-70K token prompt cache.
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:232:  // double-bust the prompt cache. The `speed` body param stays dynamic.
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:234:  // Sticky-on latch for the cache-editing beta header. Once cached
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:236:  // GrowthBook/settings toggles don't bust the prompt cache.
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:237:  cacheEditingHeaderLatched: boolean | null
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:239:  // when >1h since last API call (confirmed cache miss — no cache-hit
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:241:  // thinking-cleared cache isn't busted by flipping back to keep:'all'.
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:247:  // Read at shutdown to send cache eviction hints to inference.
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:251:  // correlating cache misses with idle time (cache TTL is ~5min).
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:255:  // distinguish compaction-induced cache misses from TTL expiry.
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:347:    cachedClaudeMdContent: null,
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:398:    // System prompt section cache state
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:409:    // Prompt cache 1h allowlist (null = not yet fetched from GrowthBook)
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:411:    // Prompt cache 1h eligibility (null = not yet evaluated)
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:416:    cacheEditingHeaderLatched: null,
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:713:  return sumBy(Object.values(STATE.modelUsage), 'cacheReadInputTokens')
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:717:  return sumBy(Object.values(STATE.modelUsage), 'cacheCreationInputTokens')
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:1208:  STATE.cachedClaudeMdContent = content
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:1212:  return STATE.cachedClaudeMdContent
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:1725:  return STATE.cacheEditingHeaderLatched
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:1729:  STATE.cacheEditingHeaderLatched = v
_archive/compare_code/gg-claude-code-runnable/src\bootstrap\state.ts:1747:  STATE.cacheEditingHeaderLatched = null
_archive/compare_code/gg-claude-code-runnable/src\context.ts:22:// System prompt injection for cache breaking (ant-only, ephemeral debugging state)
_archive/compare_code/gg-claude-code-runnable/src\context.ts:31:  // Clear context caches immediately when injection changes
_archive/compare_code/gg-claude-code-runnable/src\context.ts:32:  getUserContext.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\context.ts:33:  getSystemContext.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\context.ts:114: * This context is prepended to each conversation, and cached for the duration of the conversation.
_archive/compare_code/gg-claude-code-runnable/src\context.ts:130:    // Include system prompt injection if set (for cache breaking, ant-only)
_archive/compare_code/gg-claude-code-runnable/src\context.ts:145:            cacheBreaker: `[CACHE_BREAKER: ${injection}]`,
_archive/compare_code/gg-claude-code-runnable/src\context.ts:153: * This context is prepended to each conversation, and cached for the duration of the conversation.
_archive/compare_code/gg-claude-code-runnable/src\commands\branch\branch.ts:102:  // as FROZEN and sent as full content (prompt cache miss + permanent overage).
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:507:  // user settings a similar head start. The cached promise is joined in
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:564:  // Without this, the disk cache is empty and all flags fall back to defaults.
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:1147:  // Seed the readFileState cache from the transcript (content the model saw,
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:1149:  // This cache instance must persist across ask() calls, since the edit tool
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:1707:      // settings (fired in main.tsx preAction). downloadUserSettings() caches
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:1753:  // Clear all plugin-related caches, reload commands/agents/hooks.
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:1761:    // refreshActivePlugins handles the full cache sweep (clearAllCaches),
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:1769:    // fresh because refreshActivePlugins cleared its cache.
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:1782:    // the settings cache before setEligibility(true) ran.
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:2172:              setReadFileCache: cache => {
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:2173:                readFileState = cache
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:2286:            const cacheSafeParams = getLastCacheSafeParams()
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:2287:            if (!cacheSafeParams) {
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:2304:                    cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:2801:  // cache is already cleared and the next API call picks up the new creds.
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3029:            // then sees disk > cache.timestamp, re-reads, diffs C_current vs
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3072:              // user's local CLI take effect before the cache sweep.
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3720:          // Route through notifyChange so fanOut() resets the settings cache
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3725:          // would read stale cached settings and silently drop the update.
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3822:          // identical prefix → prompt cache hit.
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3828:          // matches in the common case. May still miss the cache for
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3835:              const cacheSafeParams = saved
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3842:                    // not part of the cache key — swapping in a fresh one is
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:3868:                cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:4929:            getAgentDefinitionsWithOverrides.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:5131:          getAgentDefinitionsWithOverrides.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\cli\print.ts:5493:      // Clear the memoization cache
_archive/compare_code/gg-claude-code-runnable/src\commands\brief.ts:83:        // exactly when brief mode is on. This invalidates prompt cache on
_archive/compare_code/gg-claude-code-runnable/src\buddy\companion.ts:105:// per-turn observer) with the same userId → cache the deterministic result.
_archive/compare_code/gg-claude-code-runnable/src\cli\handlers\plugins.ts:27:import { clearAllCaches } from '../../utils/plugins/cacheUtils.js'
_archive/compare_code/gg-claude-code-runnable/src\cli\handlers\plugins.ts:231:          // Load MCP servers if not already cached
_archive/compare_code/gg-claude-code-runnable/src\constants\common.ts:17:// Memoized for prompt-cache stability — captures the date once at session start.
_archive/compare_code/gg-claude-code-runnable/src\constants\common.ts:20:// an explicit memoized date to avoid busting the cached prefix at midnight.
_archive/compare_code/gg-claude-code-runnable/src\constants\common.ts:23:// stale date after midnight vs. ~entire-conversation cache bust — stale wins).
_archive/compare_code/gg-claude-code-runnable/src\constants\common.ts:27:// Changes monthly, not daily — used in tool prompts to minimize cache busting.
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\index.ts:5: * - clearSessionCaches: import from './clear/caches.js'
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:47:import { clearSessionCaches } from './caches.js'
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:76:  // Signal to inference that this conversation's cache can be evicted.
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:79:    logEvent('tengu_cache_eviction_hint', {
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:88:  // cache wipe below. A task is preserved unless it explicitly has
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:124:  // Clear all session-related caches. Per-agent state for preserved background
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:125:  // tasks (invoked skills, pending permission callbacks, dump state, cache-break
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:194:  // Clear plan slug cache so a new plan file is used after /clear
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:197:  // Clear cached session metadata (title, tag, agent name/color)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\conversation.ts:228:  // wiped both from the cache, but the process is still in the same mode
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:2: * Session cache clearing utilities.
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:36: * Clear all session-related caches.
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:38: * This is a subset of what clearConversation does - it only clears caches
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:44: *   state (pending permission callbacks, dump state, cache-break tracking) is left
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:51:  // Clear context caches
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:52:  getUserContext.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:53:  getSystemContext.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:54:  getGitStatus.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:55:  getSessionStartDate.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:56:  // Clear file suggestion caches (for @ mentions)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:59:  // Clear commands/skills cache
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:62:  // Clear prompt cache break detection state
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:65:  // Clear system prompt injection (cache breaker)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:73:  // files cache with load_reason 'compact').
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:80:  // Override the memory cache reset with 'session_start': clearSessionCaches is called
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:86:  // Clear stored image paths cache
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:89:  // Clear all session ingress caches (lastUuidMap, sequentialAppendBySession)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:103:  // Clear attribution caches (file content cache, pending bash states)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:110:  // Clear repository detection caches
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:112:  // Clear bash command prefix caches (Haiku-extracted prefixes)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:116:  // Clear invoked skills cache (each entry holds full skill file content)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:118:  // Clear git dir resolution cache
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:128:  // Clear WebFetch URL cache (up to 50MB of cached page content)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:132:  // Clear ToolSearch description cache (full tool prompts, ~500KB for 50 MCP tools)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:136:  // Clear agent definitions cache (accumulates per-cwd via EnterWorktreeTool)
_archive/compare_code/gg-claude-code-runnable/src\commands\clear\caches.ts:140:  // Clear SkillTool prompt cache (accumulates per project root)
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeMain.ts:91: * Uses the blocking gate check so a stale disk-cache miss doesn't unfairly
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeMain.ts:92: * deny access. The fast path (cache has true) is still instant; only the
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeMain.ts:94: * disk cache for next time.
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeMain.ts:166:  // Compat-surface ID (session_*) computed once at spawn and cached so
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeMain.ts:601:    // Fetched once per iteration — the GrowthBook cache refreshes every
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeMain.ts:2053:  // Runs after enableConfigs() (GrowthBook cache reads global config) and after
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeMain.ts:2743:        // Clear the memoized OAuth token cache so we re-read from secure
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeEnabled.ts:10:// deferral, but require() hits a CJS cache that diverges from the ESM
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeEnabled.ts:41: * Returns cached `true` immediately (fast path). If the disk cache says
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeEnabled.ts:157: * Uses cached (non-blocking) GrowthBook config. If GrowthBook hasn't
_archive/compare_code/gg-claude-code-runnable/src\cli\transports\ccrClient.ts:553:   * On 429, reads Retry-After (integer seconds) so the uploader can honor
_archive/compare_code/gg-claude-code-runnable/src\cli\transports\SerialBatchEventUploader.ts:19: * duration before retrying (e.g. 429 with Retry-After). When retryAfterMs
_archive/compare_code/gg-claude-code-runnable/src\cli\transports\SerialBatchEventUploader.ts:240:      // Retry-After. Clamp first, then spread — same shape as the
_archive/compare_code/gg-claude-code-runnable/src\components\Spinner\utils.ts:71:  const cached = RGB_CACHE.get(colorStr)
_archive/compare_code/gg-claude-code-runnable/src\components\Spinner\utils.ts:72:  if (cached !== undefined) return cached
_archive/compare_code/gg-claude-code-runnable/src\voice\voiceModeEnabled.ts:11: * off). Default `false` means a missing/stale disk cache reads as "not
_archive/compare_code/gg-claude-code-runnable/src\voice\voiceModeEnabled.ts:29: * cache hits. The memoize clears on token refresh (~once/hour), so one
_archive/compare_code/gg-claude-code-runnable/src\commands\mcp\xaaIdpCommand.ts:127:          // cached id_token's aud claim and the stored secret are both for the
_archive/compare_code/gg-claude-code-runnable/src\commands\mcp\xaaIdpCommand.ts:160:      'Ignore any cached id_token and re-login (useful after IdP-side revocation)',
_archive/compare_code/gg-claude-code-runnable/src\commands\mcp\xaaIdpCommand.ts:167:      'Write this pre-obtained id_token directly to cache, skipping the OIDC browser login',
_archive/compare_code/gg-claude-code-runnable/src\commands\mcp\xaaIdpCommand.ts:177:      // Direct-inject path: skip cache check, skip OIDC. Writing IS the
_archive/compare_code/gg-claude-code-runnable/src\commands\mcp\xaaIdpCommand.ts:183:          `id_token cached for ${idp.issuer} (expires ${new Date(expiresAt).toISOString()})`,
_archive/compare_code/gg-claude-code-runnable/src\commands\mcp\xaaIdpCommand.ts:194:          `Already logged in to ${idp.issuer} (cached id_token still valid). Use --force to re-login.`,
_archive/compare_code/gg-claude-code-runnable/src\commands\mcp\xaaIdpCommand.ts:238:        `Logged in:     ${hasIdToken ? 'yes (id_token cached)' : "no — run 'claude mcp xaa login'"}\n`,
_archive/compare_code/gg-claude-code-runnable/src\commands\mcp\xaaIdpCommand.ts:245:    .description('Clear the IdP connection config and cached id_token')
_archive/compare_code/gg-claude-code-runnable/src\commands\compact\compact.ts:63:        getUserContext.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands\compact\compact.ts:65:        // Reset cache read baseline so the post-compact drop isn't flagged
_archive/compare_code/gg-claude-code-runnable/src\commands\compact\compact.ts:117:    getUserContext.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands\compact\compact.ts:156:    // Hooks and cache-param build are independent — run concurrently.
_archive/compare_code/gg-claude-code-runnable/src\commands\compact\compact.ts:159:    const [hookResult, cacheSafeParams] = await Promise.all([
_archive/compare_code/gg-claude-code-runnable/src\commands\compact\compact.ts:177:      cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\commands\compact\compact.ts:203:    getUserContext.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands\files\files.ts:5:import { cacheKeys } from '../../utils/fileStateCache.js'
_archive/compare_code/gg-claude-code-runnable/src\commands\files\files.ts:11:  const files = context.readFileState ? cacheKeys(context.readFileState) : []
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:418:// Calling it at module scope would populate the memoize cache before
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:949:      // Delete corrupted cache file so it gets re-extracted next run
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2818:  // Phase 2: Load SessionMeta — use cache where available, parse only uncached
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2819:  // Read cached metas in parallel batches to avoid blocking the event loop
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2823:  const uncachedSessions: LiteSessionInfo[] = []
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2830:        cached: await loadCachedSessionMeta(sessionInfo.sessionId),
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2833:    for (const { sessionInfo, cached } of results) {
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2834:      if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2835:        allMetas.push(cached)
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2836:      } else if (uncachedSessions.length < MAX_SESSIONS_TO_LOAD) {
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2837:        uncachedSessions.push(sessionInfo)
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2842:  // Load full message data only for uncached sessions and compute SessionMeta
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2863:  // Load uncached sessions in batches to yield to event loop between batches
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2865:  for (let i = 0; i < uncachedSessions.length; i += LOAD_BATCH_SIZE) {
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2866:    const batch = uncachedSessions.slice(i, i + LOAD_BATCH_SIZE)
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2929:  // Phase 3: Facet extraction — only for sessions without cached facets
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2934:  // Load cached facets for all substantive sessions in parallel
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2935:  const cachedFacetResults = await Promise.all(
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2938:      cached: await loadCachedFacets(meta.session_id),
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2941:  for (const { sessionId, cached } of cachedFacetResults) {
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2942:    if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\commands\insights.ts:2943:      facets.set(sessionId, cached)
_archive/compare_code/gg-claude-code-runnable/src\commands\reload-plugins\reload-plugins.ts:11:  // CCR: re-pull user settings before the cache sweep so enabledPlugins /
_archive/compare_code/gg-claude-code-runnable/src\commands\reload-plugins\reload-plugins.ts:19:  // by design (stale-cache fallback on fetch failure). Interactive
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeUI.ts:61:  let cachedIngressUrl = ''
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeUI.ts:62:  let cachedEnvironmentId = ''
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeUI.ts:296:      cachedIngressUrl = config.sessionIngressUrl
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeUI.ts:297:      cachedEnvironmentId = environmentId
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeUI.ts:298:      connectUrl = buildBridgeConnectUrl(environmentId, cachedIngressUrl)
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeUI.ts:399:          cachedEnvironmentId,
_archive/compare_code/gg-claude-code-runnable/src\bridge\bridgeUI.ts:400:          cachedIngressUrl,
_archive/compare_code/gg-claude-code-runnable/src\bridge\envLessBridgeConfig.ts:127: * value instead of the stale-on-first-read disk cache. The _DEPRECATED suffix
_archive/compare_code/gg-claude-code-runnable/src\commands\release-notes\release-notes.ts:31:    // Either fetch failed or timed out - just use cached notes
_archive/compare_code/gg-claude-code-runnable/src\commands\release-notes\release-notes.ts:39:  // Otherwise check cached notes
_archive/compare_code/gg-claude-code-runnable/src\commands\release-notes\release-notes.ts:40:  const cachedNotes = getAllReleaseNotes(await getStoredChangelog())
_archive/compare_code/gg-claude-code-runnable/src\commands\release-notes\release-notes.ts:41:  if (cachedNotes.length > 0) {
_archive/compare_code/gg-claude-code-runnable/src\commands\release-notes\release-notes.ts:42:    return { type: 'text', value: formatReleaseNotes(cachedNotes) }
_archive/compare_code/gg-claude-code-runnable/src\commands.ts:32:import breakCache from './commands/break-cache/index.js'
_archive/compare_code/gg-claude-code-runnable/src\commands.ts:520: * Clears only the memoization caches for commands, WITHOUT clearing skill caches.
_archive/compare_code/gg-claude-code-runnable/src\commands.ts:521: * Use this when dynamic skills are added to invalidate cached command lists.
_archive/compare_code/gg-claude-code-runnable/src\commands.ts:524:  loadAllCommands.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands.ts:525:  getSkillToolCommands.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands.ts:526:  getSlashCommandToolSkills.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\commands.ts:529:  // caches is a no-op for the outer — lodash memoize returns the cached result
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:262:      // or fall back to standard speed (long delays) to avoid cache thrashing.
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:266:      // keep-alive path instead of fast-mode cache-preservation anyway.
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:284:        const retryAfterMs = getRetryAfterMs(error)
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:287:          // to preserve prompt cache (same model name on retry).
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:389:        const overflowData = parseMaxTokensContextOverflowError(error)
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:431:      const retryAfter = getRetryAfter(error)
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:450:        // Retry-After is a server directive and bypasses maxDelayMs inside
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:519:function getRetryAfter(error: unknown): string | null {
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:550:export function parseMaxTokensContextOverflowError(error: APIError):
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:647: * Clear AWS auth caches if appropriate.
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:685: * Clear GCP auth caches if appropriate.
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:727:  if (parseMaxTokensContextOverflowError(error)) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:771:  // Clear API key cache on 401 and allow retry.
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:803:function getRetryAfterMs(error: APIError): number | null {
_archive/compare_code/gg-claude-code-runnable/src/services/api\withRetry.ts:804:  const retryAfter = getRetryAfter(error)
_archive/compare_code/gg-claude-code-runnable/src/services/api\sessionIngress.ts:500: * Clear cached state for a session
_archive/compare_code/gg-claude-code-runnable/src/services/api\sessionIngress.ts:508: * Clear all cached session state (all sessions).
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:80: * Check cached passes eligibility from GlobalConfig
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:81: * Returns current cached state and cache status
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:106:  const cachedEntry = config.passesEligibilityCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:108:  if (!cachedEntry) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:109:    // No cached entry, needs fetch
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:117:  const { eligible, timestamp } = cachedEntry
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:147: * Get cached referrer reward info from eligibility cache
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:154:  const cachedEntry = config.passesEligibilityCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:155:  return cachedEntry?.referrer_reward ?? null
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:159: * Get the cached remaining passes count from eligibility cache
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:166:  const cachedEntry = config.passesEligibilityCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:167:  return cachedEntry?.remaining_passes ?? null
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:192:      const cacheEntry = {
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:201:          [orgId]: cacheEntry,
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:206:        `Passes eligibility cached for org ${orgId}: ${response.eligible}`,
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:211:      logForDebugging('Failed to fetch and cache passes eligibility')
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:224: * Get cached passes eligibility data or fetch if needed
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:227: * This function never blocks on network - it returns cached data immediately
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:228: * and fetches in the background if needed. On cold start (no cache), it returns
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:242:  const cachedEntry = config.passesEligibilityCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:245:  // No cache - trigger background fetch and return null (non-blocking)
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:247:  if (!cachedEntry) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:249:      'Passes: No cache, fetching eligibility in background (command unavailable this session)',
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:255:  // Cache exists but is stale - return stale cache and trigger background refresh
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:256:  if (now - cachedEntry.timestamp > CACHE_EXPIRATION_MS) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:258:      'Passes: Cache stale, returning cached data and refreshing in background',
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:261:    const { timestamp, ...response } = cachedEntry
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:266:  logForDebugging('Passes: Using fresh cached eligibility data')
_archive/compare_code/gg-claude-code-runnable/src/services/api\referral.ts:267:  const { timestamp, ...response } = cachedEntry
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:25:  return join(getClaudeTempDir(), `cache-break-${suffix}.diff`)
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:31:  /** Hash of system blocks WITH cache_control intact. Catches scope/TTL flips
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:33:  cacheControlHash: number
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:47:  /** AFK_MODE_BETA_HEADER presence — should NOT break cache anymore
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:50:  /** Overage state flip — should NOT break cache anymore (eligibility is
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:53:  /** Cache-editing beta header presence — should NOT break cache anymore
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:55:  cachedMCEnabled: boolean
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:65:  /** Set when cached microcompact sends cache_edits deletions. Cache reads
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:67:  cacheDeletionsPending: boolean
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:76:  cacheControlChanged: boolean
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:81:  cachedMCChanged: boolean
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:117:// Minimum absolute token drop required to trigger a cache break warning.
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:122:// Anthropic's server-side prompt cache TTL thresholds to test.
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:128:// Models to exclude from cache break detection (e.g., haiku has different caching behavior)
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:129:function isExcludedModel(model: string): boolean {
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:135: * Compact shares the same server-side cache as repl_main_thread
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:136: * (same cacheSafeParams), so they share tracking state.
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:139: * isolate tracking state. This prevents false positive cache break
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:144: * are short-lived forked agents where cache break detection provides no
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:146: * nothing meaningful to compare against. Their cache metrics are still
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:164:    if (!('cache_control' in item)) return item
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:165:    const { cache_control: _, ...rest } = item
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:225: *  cache key that we can observe from the client. All fields are optional so
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:238:  cachedMCEnabled?: boolean
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:260:      cachedMCEnabled = false,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:276:    // Hash the full system array INCLUDING cache_control — this catches
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:279:    const cacheControlHash = computeHash(
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:280:      system.map(b => ('cache_control' in b ? b.cache_control : null)),
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:308:        cacheControlHash,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:317:        cachedMCEnabled,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:323:        cacheDeletionsPending: false,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:336:    const cacheControlChanged = cacheControlHash !== prev.cacheControlHash
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:344:    const cachedMCChanged = cachedMCEnabled !== prev.cachedMCEnabled
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:353:      cacheControlChanged ||
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:358:      cachedMCChanged ||
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:384:        cacheControlChanged,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:389:        cachedMCChanged,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:414:    prev.cacheControlHash = cacheControlHash
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:423:    prev.cachedMCEnabled = cachedMCEnabled
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:433: * Phase 2 (post-call): Check the API response's cache tokens to determine
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:434: * if a cache break actually occurred. If it did, use the pending changes
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:439:  cacheReadTokens: number,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:440:  cacheCreationTokens: number,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:453:    if (isExcludedModel(state.model)) return
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:456:    state.prevCacheReadTokens = cacheReadTokens
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:470:    // Cache deletions via cached microcompact intentionally reduce the cached
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:471:    // prefix. The drop in cache read tokens is expected — reset the baseline
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:473:    if (state.cacheDeletionsPending) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:474:      state.cacheDeletionsPending = false
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:476:        `[PROMPT CACHE] cache deletion applied, cache read: ${prevCacheRead} → ${cacheReadTokens} (expected drop)`,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:483:    // Detect a cache break: cache read dropped >5% from previous AND
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:485:    const tokenDrop = prevCacheRead - cacheReadTokens
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:487:      cacheReadTokens >= prevCacheRead * 0.95 ||
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:524:          `global cache strategy changed (${changes.prevGlobalCacheStrategy || 'none'} → ${changes.newGlobalCacheStrategy || 'none'})`,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:528:        changes.cacheControlChanged &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:534:        parts.push('cache_control changed (scope or TTL)')
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:552:      if (changes.cachedMCChanged) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:553:        parts.push('cached microcompact toggled')
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:573:    // Post PR #19823 BQ analysis (bq-queries/prompt-caching/cache_break_pr19823_analysis.sql):
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:590:    logEvent('tengu_prompt_cache_break', {
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:595:      cacheControlChanged: changes?.cacheControlChanged ?? false,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:600:      cachedMCChanged: changes?.cachedMCChanged ?? false,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:623:      // Beta header names and cache strategy are fixed enum-like values,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:637:      cacheReadTokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:638:      cacheCreationTokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:658:    const summary = `[PROMPT CACHE BREAK] ${reason} [source=${querySource}, call #${state.callCount}, cache read: ${prevCacheRead} → ${cacheReadTokens}, creation: ${cacheCreationTokens}${diffSuffix}]`
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:669: * Call when cached microcompact sends cache_edits deletions.
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:670: * The next API response will have lower cache read tokens — that's
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:671: * expected, not a cache break.
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:680:    state.cacheDeletionsPending = true
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:685: * Call after compaction to reset the cache read baseline.
_archive/compare_code/gg-claude-code-runnable/src/services/api\promptCacheBreakDetection.ts:686: * Compaction legitimately reduces message count, so cache read tokens
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:44: * Get cached grant info. Returns null if no cache or cache is stale.
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:51:  const cached = getGlobalConfig().overageCreditGrantCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:52:  if (!cached) return null
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:53:  if (Date.now() - cached.timestamp > CACHE_TTL_MS) return null
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:54:  return cached.info
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:58: * Drop the current org's cached entry so the next read refetches.
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:64:  const cache = getGlobalConfig().overageCreditGrantCache
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:65:  if (!cache || !(orgId in cache)) return
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:74: * Fetch and cache grant info. Fire-and-forget; call when an upsell surface
_archive/compare_code/gg-claude-code-runnable/src/services/api\overageCreditGrant.ts:75: * is about to render and the cache is empty.
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:24:// Disk TTL — org settings rarely change. When disk cache is fresher than this,
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:100:  const cached = getGlobalConfig().metricsStatusCache
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:101:  const unchanged = cached !== undefined && cached.enabled === result.enabled
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:104:  if (unchanged && Date.now() - cached.timestamp < DISK_CACHE_TTL_MS) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:121: * Two-tier cache:
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:122: * - Disk (24h TTL): survives process restarts. Fresh disk cache → zero network.
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:133:  // session would poison the cache for a later full-OAuth session.
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:138:  const cached = getGlobalConfig().metricsStatusCache
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:139:  if (cached) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:140:    if (Date.now() - cached.timestamp > DISK_CACHE_TTL_MS) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:147:      enabled: cached.enabled,
_archive/compare_code/gg-claude-code-runnable/src/services/api\metricsOptOut.ts:158:  memoizedCheckMetrics.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:89:  // https://www.braintrust.dev/docs/guides/proxy — x-bt-used-endpoint, x-bt-cached
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:482:    cachedInputTokens: usage.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:483:    uncachedInputTokens: usage.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:555:    // Log cache_deleted_input_tokens for cache editing analysis. Casts needed
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:557:    // external builds). Set by updateUsage() when cache editing is active.
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:559:    ((usage as unknown as { cache_deleted_input_tokens?: number })
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:560:      .cache_deleted_input_tokens ?? 0) > 0
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:562:          cacheDeletedInputTokens: (
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:563:            usage as unknown as { cache_deleted_input_tokens: number }
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:564:          ).cache_deleted_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:722:    cache_read_tokens: String(usage.cache_read_input_tokens),
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:723:    cache_creation_tokens: String(usage.cache_creation_input_tokens),
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:768:    cacheReadTokens: usage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\logging.ts:769:    cacheCreationTokens: usage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:77:      // Don't cache failures — transient network issues would lock the user
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:80:      // is the only other place the cache is cleared).
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:81:      getGroveSettings.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:111:    getGroveSettings.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:144:    getGroveSettings.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:151: * Check if user is qualified for Grove (non-blocking, cache-first).
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:153: * This function never blocks on network - it returns cached data immediately
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:154: * and fetches in the background if needed. On cold start (no cache), it returns
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:168:  const cachedEntry = globalConfig.groveConfigCache?.[accountId]
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:171:  // No cache - trigger background fetch and return false (non-blocking)
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:173:  if (!cachedEntry) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:175:      'Grove: No cache, fetching config in background (dialog skipped this session)',
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:181:  // Cache exists but is stale - return cached value and refresh in background
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:182:  if (now - cachedEntry.timestamp > GROVE_CACHE_EXPIRATION_MS) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:184:      'Grove: Cache stale, returning cached data and refreshing in background',
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:187:    return cachedEntry.grove_enabled
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:191:  logForDebugging('Grove: Using fresh cached config')
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:192:  return cachedEntry.grove_enabled
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:196: * Fetch Grove config from API and store in cache
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:205:    const cachedEntry = getGlobalConfig().groveConfigCache?.[accountId]
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:207:      cachedEntry?.grove_enabled === groveEnabled &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\grove.ts:208:      Date.now() - cachedEntry.timestamp <= GROVE_CACHE_EXPIRATION_MS
_archive/compare_code/gg-claude-code-runnable/src/services/api\firstTokenDate.ts:10: * This is called after successful login to cache when they started using Claude Code.
_archive/compare_code/gg-claude-code-runnable/src/services/api\errorUtils.ts:169:function extractNestedErrorMessage(error: APIError): string | null {
_archive/compare_code/gg-claude-code-runnable/src/services/api\errorUtils.ts:250:      extractNestedErrorMessage(error) ??
_archive/compare_code/gg-claude-code-runnable/src/services/api\emptyUsage.ts:10:  cache_creation_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src/services/api\emptyUsage.ts:11:  cache_read_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src/services/api\emptyUsage.ts:15:  cache_creation: {
_archive/compare_code/gg-claude-code-runnable/src/services/api\dumpPrompts.ts:15:const cachedApiRequests: Array<{ timestamp: string; request: unknown }> = []
_archive/compare_code/gg-claude-code-runnable/src/services/api\dumpPrompts.ts:33:  return [...cachedApiRequests]
_archive/compare_code/gg-claude-code-runnable/src/services/api\dumpPrompts.ts:37:  cachedApiRequests.length = 0
_archive/compare_code/gg-claude-code-runnable/src/services/api\dumpPrompts.ts:50:  cachedApiRequests.push({
_archive/compare_code/gg-claude-code-runnable/src/services/api\dumpPrompts.ts:54:  if (cachedApiRequests.length > MAX_CACHED_REQUESTS) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\dumpPrompts.ts:55:    cachedApiRequests.shift()
_archive/compare_code/gg-claude-code-runnable/src/services/api\client.ts:180:      // Refresh auth and get credentials with cache clearing
_archive/compare_code/gg-claude-code-runnable/src/services/api\client.ts:181:      const cachedCredentials = await refreshAndGetAwsCredentials()
_archive/compare_code/gg-claude-code-runnable/src/services/api\client.ts:182:      if (cachedCredentials) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\client.ts:183:        bedrockArgs.awsAccessKey = cachedCredentials.accessKeyId
_archive/compare_code/gg-claude-code-runnable/src/services/api\client.ts:184:        bedrockArgs.awsSecretKey = cachedCredentials.secretAccessKey
_archive/compare_code/gg-claude-code-runnable/src/services/api\client.ts:185:        bedrockArgs.awsSessionToken = cachedCredentials.sessionToken
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:283:        // Shallow clone — safeParseJSON is LRU-cached and returns the same
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:285:        // would poison the cache, causing stale values to persist.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:390: * The allowlist is cached in STATE for session stability — prevents mixed
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:391: * TTLs when GrowthBook's disk cache updates mid-request.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:404:  // mid-session overage flips from changing the cache_control TTL, which
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:405:  // would bust the server-side prompt cache (~20K tokens per flip).
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:416:  // TTLs when GrowthBook's disk cache updates mid-request
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:421:    }>('tengu_prompt_cache_1h_config', {})
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:603:              cache_control: getCacheControl({ querySource }),
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:615:              ? { cache_control: getCacheControl({ querySource }) }
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:624:  // to addCacheBreakpoints share the same array and each splices in duplicate cache_edits.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:648:              cache_control: getCacheControl({ querySource }),
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:663:              ? { cache_control: getCacheControl({ querySource }) }
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:922: * join them for cache-hit-rate analysis and incremental token tracking.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1184:  // Determine if cached microcompact is enabled for this model.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1188:  let cachedMCEnabled = false
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1189:  let cacheEditingBetaHeader = ''
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1195:    } = await import('../compact/cachedMicrocompact.js')
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1197:    cacheEditingBetaHeader = betas.CACHE_EDITING_BETA_HEADER
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1200:    cachedMCEnabled = featureEnabled && modelSupported
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1210:  // MCP tools are per-user → dynamic tool section → can't globally cache.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1216:  // Ensure prompt_caching_scope beta header is present when global cache is enabled.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1224:  // Determine global cache strategy for logging
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1329:  // ephemeral prepend (which busts cache whenever the pool changes).
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1350:  // busts the prompt cache when chrome connects late.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1388:    // toolSchemas (which carries the cache_control marker) so toggling /advisor
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1389:    // only churns the small suffix, not the cached prefix.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1407:  // toggles don't change the server-side cache key and bust ~50-70K tokens.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1431:  let cacheEditingHeaderLatched = getCacheEditingHeaderLatched() === true
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1434:      !cacheEditingHeaderLatched &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1435:      cachedMCEnabled &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1439:      cacheEditingHeaderLatched = true
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1462:    // prompt, so they never affect the actual cache key. Including them creates
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1468:    // Capture everything that could affect the server-side cache key.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1482:      cachedMCEnabled: cacheEditingHeaderLatched,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1528:  // Consume pending cache edits ONCE before paramsFromContext is defined.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1531:  const consumedCacheEdits = cachedMCEnabled ? consumePendingCacheEdits() : null
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1532:  const consumedPinnedEdits = cachedMCEnabled ? getPinnedCacheEdits() : []
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1642:    // Fast mode: header is latched session-stable (cache-safe), but
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1644:    // fast-mode request without changing the cache key.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1673:    // (controls cache_edits body behavior) stays live so edits stop when
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1676:      cachedMCEnabled &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1680:      cacheEditingHeaderLatched &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1683:      !betasParams.includes(cacheEditingBetaHeader)
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1685:      betasParams.push(cacheEditingBetaHeader)
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1687:        'Cache editing beta header enabled for cached microcompact',
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:1792:        // once per attempt; on retries the client is usually cached (withRetry
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2382:      // Check if the cache actually broke based on response tokens
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2386:          usage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2387:          usage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2834:  if (feature('CACHED_MICROCOMPACT') && cachedMCEnabled) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2839:  // can send a cache eviction hint to inference. Exclude backgrounded
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2842:  // whose cache should not be evicted when the foreground session clears.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2919: * Input-related tokens (input_tokens, cache_creation_input_tokens, cache_read_input_tokens)
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2936:    cache_creation_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2937:      partUsage.cache_creation_input_tokens !== null &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2938:      partUsage.cache_creation_input_tokens > 0
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2939:        ? partUsage.cache_creation_input_tokens
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2940:        : usage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2941:    cache_read_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2942:      partUsage.cache_read_input_tokens !== null &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2943:      partUsage.cache_read_input_tokens > 0
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2944:        ? partUsage.cache_read_input_tokens
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2945:        : usage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2956:    cache_creation: {
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2957:      // SDK type BetaMessageDeltaUsage is missing cache_creation, but it's real!
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2959:        (partUsage as BetaUsage).cache_creation?.ephemeral_1h_input_tokens ??
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2960:        usage.cache_creation.ephemeral_1h_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2962:        (partUsage as BetaUsage).cache_creation?.ephemeral_5m_input_tokens ??
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2963:        usage.cache_creation.ephemeral_5m_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2965:    // cache_deleted_input_tokens: returned by the API when cache editing
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2966:    // deletes KV cache content, but not in SDK types. Kept off NonNullableUsage
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2972:          cache_deleted_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2973:            (partUsage as unknown as { cache_deleted_input_tokens?: number })
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2974:              .cache_deleted_input_tokens != null &&
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2975:            (partUsage as unknown as { cache_deleted_input_tokens: number })
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2976:              .cache_deleted_input_tokens > 0
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2977:              ? (partUsage as unknown as { cache_deleted_input_tokens: number })
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2978:                  .cache_deleted_input_tokens
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2979:              : ((usage as unknown as { cache_deleted_input_tokens?: number })
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2980:                  .cache_deleted_input_tokens ?? 0),
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:2999:    cache_creation_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3000:      totalUsage.cache_creation_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3001:      messageUsage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3002:    cache_read_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3003:      totalUsage.cache_read_input_tokens + messageUsage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3014:    cache_creation: {
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3016:        totalUsage.cache_creation.ephemeral_1h_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3017:        messageUsage.cache_creation.ephemeral_1h_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3019:        totalUsage.cache_creation.ephemeral_5m_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3020:        messageUsage.cache_creation.ephemeral_5m_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3026:          cache_deleted_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3027:            ((totalUsage as unknown as { cache_deleted_input_tokens?: number })
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3028:              .cache_deleted_input_tokens ?? 0) +
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3030:              messageUsage as unknown as { cache_deleted_input_tokens?: number }
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3031:            ).cache_deleted_input_tokens ?? 0),
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3053:  type: 'cache_edits'
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3054:  edits: { type: 'delete'; cache_reference: string }[]
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3062:// Exported for testing cache_reference placement constraints
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3072:  logEvent('tengu_api_cache_breakpoints', {
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3078:  // Exactly one message-level cache_control marker per request. Mycro's
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3080:  // local-attention KV pages at any cached prefix position NOT in
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3081:  // cache_store_int_token_boundaries. With two markers the second-to-last
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3112:  // Track all cache_references being deleted to prevent duplicates across blocks.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3115:  // Helper to deduplicate a cache_edits block against already-seen deletions
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3118:      if (seenDeleteRefs.has(edit.cache_reference)) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3121:      seenDeleteRefs.add(edit.cache_reference)
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3127:  // Re-insert all previously-pinned cache_edits at their original positions
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3141:  // Insert new cache_edits into the last user message and pin them
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3156:            `Added cache_edits block with ${dedupedNewEdits.edits.length} deletion(s) to message[${i}]: ${dedupedNewEdits.edits.map(e => e.cache_reference).join(', ')}`,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3164:  // Add cache_reference to tool_result blocks that are within the cached prefix.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3165:  // Must be done AFTER cache_edits insertion since that modifies content arrays.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3167:    // Find the last message containing a cache_control marker
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3173:          if (block && typeof block === 'object' && 'cache_control' in block) {
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3180:    // Add cache_reference to tool_result blocks that are strictly before
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3181:    // the last cache_control marker. The API requires cache_reference to
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3182:    // appear "before or on" the last cache_control — we use strict "before"
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3183:    // to avoid edge cases where cache_edits splicing shifts block indices.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3186:    // blocks reused by secondary queries that use models without cache_editing support.
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3202:              cache_reference: block.tool_use_id,
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3229:        block.cacheScope !== null && {
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3230:          cache_control: getCacheControl({
_archive/compare_code/gg-claude-code-runnable/src/services/api\claude.ts:3231:            scope: block.cacheScope,
_archive/compare_code/gg-claude-code-runnable/src/services/api\bootstrap.ts:112: * Fetch bootstrap data from the API and persist to disk cache.
_archive/compare_code/gg-claude-code-runnable/src\commands\review\reviewRemote.ts:176:  // match autoDream.ts — GB cache can return stale wrong-type values.
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:48:let cacheGeneration = 0
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:54:let cachedTrackedFiles: string[] = []
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:56:let cachedConfigFiles: string[] = []
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:59:let cachedTrackedDirs: string[] = []
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:81: * Clear all file suggestion caches.
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:87:  cacheGeneration++
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:89:  cachedTrackedFiles = []
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:90:  cachedConfigFiles = []
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:91:  cachedTrackedDirs = []
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:167: * Merge already-normalized untracked files into the cache
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:173:  if (!fileIndex || cachedTrackedFiles.length === 0) return
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:177:    ...cachedTrackedFiles,
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:178:    ...cachedConfigFiles,
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:179:    ...cachedTrackedDirs,
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:193:    `[FileIndex] rebuilt index with ${cachedTrackedFiles.length} tracked + ${normalizedUntracked.length} untracked files`,
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:200: * Results are cached per repoRoot:cwd combination
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:206:  const cacheKey = `${repoRoot}:${cwd}`
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:208:  // Return cached result if available
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:209:  if (ignorePatternsCacheKey === cacheKey) {
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:235:  ignorePatternsCacheKey = cacheKey
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:300:    cachedTrackedFiles = normalizedTracked
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:326:      const generation = cacheGeneration
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:332:          if (generation !== cacheGeneration) {
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:541:    cachedConfigFiles = configFiles
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:545:    cachedTrackedDirs = directories
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:629: * Starts a background refresh of the file index cache if not already in progress.
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:631: * Throttled: when a cache already exists, we skip the refresh unless git state
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:639:  // Throttle only when a cache exists — cold start must always populate.
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:653:  const generation = cacheGeneration
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:661:      if (generation !== cacheGeneration) {
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:672:        `[FileIndex] cache refresh completed in ${Date.now() - refreshStart}ms`,
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:681:      if (generation === cacheGeneration) {
_archive/compare_code/gg-claude-code-runnable/src\hooks\fileSuggestions.ts:774:      cache_hit: !wasBuilding,
_archive/compare_code/gg-claude-code-runnable/src\history.ts:366:      // Filter out images (they're stored separately in image-cache)
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:166:          cacheReadInputTokens: usage.cacheReadInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:167:          cacheCreationInputTokens: usage.cacheCreationInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:184:    return 'Usage:                 0 input, 0 output, 0 cache read, 0 cache write'
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:195:        cacheReadInputTokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:196:        cacheCreationInputTokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:206:    accumulated.cacheReadInputTokens += usage.cacheReadInputTokens
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:207:    accumulated.cacheCreationInputTokens += usage.cacheCreationInputTokens
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:217:      `${formatNumber(usage.cacheReadInputTokens)} cache read, ` +
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:218:      `${formatNumber(usage.cacheCreationInputTokens)} cache write` +
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:258:    cacheReadInputTokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:259:    cacheCreationInputTokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:268:  modelUsage.cacheReadInputTokens += usage.cache_read_input_tokens ?? 0
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:269:  modelUsage.cacheCreationInputTokens += usage.cache_creation_input_tokens ?? 0
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:294:  getTokenCounter()?.add(usage.cache_read_input_tokens ?? 0, {
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:296:    type: 'cacheRead',
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:298:  getTokenCounter()?.add(usage.cache_creation_input_tokens ?? 0, {
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:300:    type: 'cacheCreation',
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:311:      cache_read_input_tokens: advisorUsage.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:312:      cache_creation_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\cost-tracker.ts:313:        advisorUsage.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\hooks\useApiKeyVerification.ts:48:    // Warm the apiKeyHelper cache (no-op if not configured), then read from
_archive/compare_code/gg-claude-code-runnable/src\hooks\useApiKeyVerification.ts:49:    // all sources. getAnthropicApiKeyWithSource() reads the now-warm cache.
_archive/compare_code/gg-claude-code-runnable/src\constants\outputStyles.ts:178:  getAllOutputStyles.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:54:  DANGEROUS_uncachedSystemPromptSection,
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:68:      require('../services/compact/cachedMCConfig.js') as typeof import('../services/compact/cachedMCConfig.js')
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:106: * Boundary marker separating static (cross-org cacheable) content from dynamic content.
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:108: * Everything AFTER contains user/session-specific content and should not be cached.
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:110: * WARNING: Do not remove or reorder this marker without updating cache logic in:
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:264:- Uploading content to third-party web tools (diagram renderers, pastebins, gists) publishes it - consider whether it could be sensitive before sending, since it may be cached or indexed even if later deleted.
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:344: * Session-variant guidance that would fragment the cacheScope:'global'
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:510:    // per-turn recompute, which busts the prompt cache on late MCP connect.
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:512:    // so a mid-session gate flip doesn't read a stale cached value.
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:513:    DANGEROUS_uncachedSystemPromptSection(
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:541:          // makes it a no-op with no budget active. Was DANGEROUS_uncached
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:561:    // --- Static content (cacheable) ---
_archive/compare_code/gg-claude-code-runnable/src\constants\prompts.ts:872:Use the ${SLEEP_TOOL_NAME} tool to control how long you wait between actions. Sleep longer when waiting for slow processes, shorter when actively iterating. Each wake-up costs an API call, but the prompt cache expires after 5 minutes of inactivity — balance accordingly.
_archive/compare_code/gg-claude-code-runnable/src\coordinator\coordinatorMode.ts:267:${AGENT_TOOL_NAME}({ prompt: "Fix the null pointer in src/auth/validate.ts:42. The user field on Session (src/auth/types.ts:15) is undefined when sessions expire but the token remains cached. Add a null check before user.id access — if null, return 401 with 'Session expired'. Commit and report the hash.", ... })
_archive/compare_code/gg-claude-code-runnable/src\coordinator\coordinatorMode.ts:300:${SEND_MESSAGE_TOOL_NAME}({ to: "xyz-456", message: "Fix the null pointer in src/auth/validate.ts:42. The user field is undefined when Session.expired is true but the token is still cached. Add a null check before accessing user.id — if null, return 401 with 'Session expired'. Commit and report the hash." })
_archive/compare_code/gg-claude-code-runnable/src\bridge\initReplBridge.ts:146:  // instead of a misleading policy error from a stale/wrong-org cache.
_archive/compare_code/gg-claude-code-runnable/src\bridge\initReplBridge.ts:197:    // checkAndRefreshOAuthTokenIfNeeded clears its own cache in every path that
_archive/compare_code/gg-claude-code-runnable/src\upstreamproxy\upstreamproxy.ts:90:  // Every CCR session is a fresh container with no GB cache, so a client-side
_archive/compare_code/gg-claude-code-runnable/src\outputStyles\loadOutputStylesDir.ts:95:  getOutputStyleDirStyles.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\outputStyles\loadOutputStylesDir.ts:96:  loadMarkdownFilesForSubdir.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:112:// NaN-safe equality for layout-cache input comparison
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:434:  // -- Dirty-flag layout cache. Mirrors upstream CalculateLayout.cpp's
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:436:  // asking the same question we cached the answer to. Two slots since
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:451:  // mutated by the multi-entry cache and by subsequent compute calls with
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:454:  // vpH=33→2624 bug. Store + restore outputs like the multi-entry cache does.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:472:  // passes cascade. Basis cache short-circuits at the child boundary.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:480:  // generation have stale cache (subtree changed), but within the SAME
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:481:  // generation the cache is fresh — the dirty chain's measure→layout
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:485:  // scroll) cache-hit after first compute: 105k visits → ~10k.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:487:  // Multi-entry layout cache — stores (inputs → computed w,h) so hits with
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:969:function cacheWrite(
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:990:  // 499 clean messages cache-hit while one dirty leaf recomputes).
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1014:// Store computed layout.width/height into the single-slot cache output fields.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1016:// outputs must be committed HERE (after compute) so a cache hit can restore
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1037:// their cache is written; a cache entry with gen === _generation was
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1047:  cacheHits: number
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1053:    cacheHits: _yogaCacheHits,
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1077:  // holds the answer. A cached layout result also satisfies a measure request
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1081:  // Previous-generation entries need !isDirty_ (a dirty node's cache from
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1083:  // sameGen bypass only for MEASURE calls — a layout-pass cache hit would
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1085:  // stale positions. Measure calls only need w/h which the cache stores.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1105:    // Multi-entry cache: scan for matching inputs, restore cached w/h on hit.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1113:    // call writes cache, rest hit: 105k visits → ~10k for 1593-node tree.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1152:  // Commit cache inputs up front so every return path leaves a valid entry.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1156:  // layout pass hit the STALE _hasL cache from the previous calculateLayout
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1174:    // generation stamping: the cache check requires sameGen || !isDirty_, so
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1192:    // with different inputs than cached.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1271:    // Write cache even for dirty nodes — fresh-mounted items during virtual
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1274:    // lets the 2nd+ calls hit cache (isDirty_ was cleared in the layout pass
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1276:    cacheWrite(
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1302:    // Write cache even for dirty nodes — fresh-mounted items during virtual
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1305:    // lets the 2nd+ calls hit cache (isDirty_ was cleared in the layout pass
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1307:    cacheWrite(
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1585:  // Write cache even for dirty nodes — fresh-mounted items during virtual scroll
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:1586:  cacheWrite(
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:2068:  // Same-generation cache hit: basis was computed THIS calculateLayout, so
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:2074:  // cache from a PREVIOUS generation, also hit if inputs match — isDirty_
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:2075:  // gates since a dirty child's previous-gen cache is stale.
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:2392:    // Invalidate layout cache — without this, unhide → calculateLayout finds
_archive/compare_code/gg-claude-code-runnable/src\native-ts\yoga-layout\index.ts:2393:    // the child clean (!isDirty_) with _hasL intact, hits the cache at line
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\sdk\coreSchemas.ts:21:    cacheReadInputTokens: z.number(),
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\sdk\coreSchemas.ts:22:    cacheCreationInputTokens: z.number(),
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\sdk\coreSchemas.ts:308:        'for always-allow (both the click and later cache hits), user_reject ' +
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\sdk\controlSchemas.ts:298:          cache_creation_input_tokens: z.number(),
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\sdk\controlSchemas.ts:299:          cache_read_input_tokens: z.number(),
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\sdk\controlSchemas.ts:359:      'Seeds the readFileState cache with a path+mtime entry. Use when a prior Read was removed from context (e.g. by snip) so Edit validation would fail despite the client having observed the Read. The mtime lets the CLI detect if the file changed since the seeded Read — same staleness check as the normal path.',
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\mcp.ts:40:  // Use size-limited LRU cache for readFileState to prevent unbounded memory growth
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\init.ts:77:    // before any TLS connections. Bun caches the TLS cert store at boot
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\init.ts:92:    // the module cache by this point (firstPartyEventLogger imports it), so the
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\init.ts:108:    // Populate OAuth account info if it is not already cached in config. This is needed since the
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\init.ts:113:    // Initialize JetBrains IDE detection asynchronously (populates cache for later sync access)
_archive/compare_code/gg-claude-code-runnable/src\entrypoints\init.ts:117:    // Detect GitHub repository asynchronously (populates cache for gitDiff PR linking)
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\WebFetchTool.ts:187:    // cache on each toggle — two consecutive cache misses per flicker event.
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:2:import { LRUCache } from 'lru-cache'
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:71:// Separate cache for preflight domain checks. URL_CACHE is URL-keyed, so
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:73:// HTTP round-trips to api.anthropic.com. This hostname-keyed cache avoids
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:74:// that. Only 'allowed' is cached — blocked/failed re-check on next attempt.
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:355:  // Check cache (LRUCache handles TTL automatically)
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:356:  const cachedEntry = URL_CACHE.get(url)
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:357:  if (cachedEntry) {
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:359:      bytes: cachedEntry.bytes,
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:360:      code: cachedEntry.code,
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:361:      codeText: cachedEntry.codeText,
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:362:      content: cachedEntry.content,
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:363:      contentType: cachedEntry.contentType,
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:364:      persistedPath: cachedEntry.persistedPath,
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:365:      persistedSize: cachedEntry.persistedSize,
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:462:    // bytes — negligible for cache eviction accounting), so skip the O(n)
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:468:  // Store the fetched content in cache. Note that it's stored under
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\utils.ts:479:  // lru-cache requires positive integers; clamp to 1 for empty responses.
_archive/compare_code/gg-claude-code-runnable/src\tools\WebFetchTool\prompt.ts:18:  - Includes a self-cleaning 15-minute cache for faster responses when repeatedly accessing the same URL
_archive/compare_code/gg-claude-code-runnable/src\native-ts\color-diff\index.ts:34:let cachedHljs: HLJSApi | null = null
_archive/compare_code/gg-claude-code-runnable/src\native-ts\color-diff\index.ts:36:  if (cachedHljs) return cachedHljs
_archive/compare_code/gg-claude-code-runnable/src\native-ts\color-diff\index.ts:41:  cachedHljs = 'default' in mod && mod.default ? mod.default : mod
_archive/compare_code/gg-claude-code-runnable/src\native-ts\color-diff\index.ts:42:  return cachedHljs!
_archive/compare_code/gg-claude-code-runnable/src\native-ts\color-diff\index.ts:980:let cachedModule: NativeModule | null = null
_archive/compare_code/gg-claude-code-runnable/src\native-ts\color-diff\index.ts:983:  if (cachedModule) return cachedModule
_archive/compare_code/gg-claude-code-runnable/src\native-ts\color-diff\index.ts:984:  cachedModule = { ColorDiff, ColorFile, getSyntaxTheme }
_archive/compare_code/gg-claude-code-runnable/src\native-ts\color-diff\index.ts:985:  return cachedModule
_archive/compare_code/gg-claude-code-runnable/src\tools\McpAuthTool\McpAuthTool.ts:176:        // (e.g. XAA with cached IdP token — silent auth).
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:69:let cachedBindings: ParsedBinding[] | null = null
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:70:let cachedWarnings: KeybindingWarning[] = []
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:120: * Parse default bindings (cached for performance).
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:241: * Uses cached value if available.
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:244:  if (cachedBindings) {
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:245:    return cachedBindings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:254: * Uses cached values if available.
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:260:  if (cachedBindings) {
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:261:    return { bindings: cachedBindings, warnings: cachedWarnings }
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:268:    cachedBindings = defaultBindings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:269:    cachedWarnings = []
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:270:    return { bindings: cachedBindings, warnings: cachedWarnings }
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:286:      cachedBindings = defaultBindings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:287:      cachedWarnings = [
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:295:      return { bindings: cachedBindings, warnings: cachedWarnings }
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:306:      cachedBindings = defaultBindings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:307:      cachedWarnings = [
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:315:      return { bindings: cachedBindings, warnings: cachedWarnings }
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:322:    cachedBindings = [...defaultBindings, ...userParsed]
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:328:    cachedWarnings = [
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:330:      ...validateBindings(userBlocks, cachedBindings),
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:332:    if (cachedWarnings.length > 0) {
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:334:        `[keybindings] Found ${cachedWarnings.length} validation issue(s)`,
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:338:    return { bindings: cachedBindings, warnings: cachedWarnings }
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:341:    cachedBindings = defaultBindings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:342:    cachedWarnings = []
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:343:    return { bindings: cachedBindings, warnings: cachedWarnings }
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:429:    cachedBindings = result.bindings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:430:    cachedWarnings = result.warnings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:444:  cachedBindings = defaultBindings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:445:  cachedWarnings = []
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:451: * Get the cached keybinding warnings.
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:455:  return cachedWarnings
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:464:  cachedBindings = null
_archive/compare_code/gg-claude-code-runnable/src\keybindings\loadUserBindings.ts:465:  cachedWarnings = []
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:49:// Track deferred tool names to detect when cache should be cleared
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:50:let cachedDeferredToolNames: string | null = null
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:53: * Get a cache key representing the current set of deferred tools.
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:89: * Invalidate the description cache if deferred tools have changed.
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:93:  if (cachedDeferredToolNames !== currentKey) {
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:95:      `ToolSearchTool: cache invalidated - deferred tools changed`,
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:97:    getToolDescriptionMemoized.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:98:    cachedDeferredToolNames = currentKey
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:103:  getToolDescriptionMemoized.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\tools\ToolSearchTool\ToolSearchTool.ts:104:  cachedDeferredToolNames = null
_archive/compare_code/gg-claude-code-runnable/src\types\plugin.ts:273:      type: 'plugin-cache-miss'
_archive/compare_code/gg-claude-code-runnable/src\types\plugin.ts:360:    case 'plugin-cache-miss':
_archive/compare_code/gg-claude-code-runnable/src\types\plugin.ts:361:      return `Plugin "${error.plugin}" not cached at ${error.installPath} — run /plugins to refresh`
_archive/compare_code/gg-claude-code-runnable/src\types\permissions.ts:342:  cacheReadInputTokens: number
_archive/compare_code/gg-claude-code-runnable/src\types\permissions.ts:343:  cacheCreationInputTokens: number
_archive/compare_code/gg-claude-code-runnable/src\types\permissions.ts:379:   * api_usage logs for cache-miss / routing attribution. Also used for the
_archive/compare_code/gg-claude-code-runnable/src\types\logs.ts:176: * for prompt cache stability. Written once per enforcement pass that replaces
_archive/compare_code/gg-claude-code-runnable/src\ink\frame.ts:57:    /** layoutNode() calls this frame (recursive, includes cache-hit returns) */
_archive/compare_code/gg-claude-code-runnable/src\ink\frame.ts:61:    /** early returns via _hasL single-slot cache */
_archive/compare_code/gg-claude-code-runnable/src\ink\frame.ts:91:  // cached by (fromId, toId), zero allocations after warmup.
_archive/compare_code/gg-claude-code-runnable/src\tools.ts:191: * NOTE: This MUST stay in sync with https://console.statsig.com/4aF3Ewatb6xPVpCwxb5nA3/dynamic_configs/claude_code_global_system_caching, in order to cache the system prompt across users.
_archive/compare_code/gg-claude-code-runnable/src\tools.ts:354:  // Sort each partition for prompt-cache stability, keeping built-ins as a
_archive/compare_code/gg-claude-code-runnable/src\tools.ts:355:  // contiguous prefix. The server's claude_code_system_cache_policy places a
_archive/compare_code/gg-claude-code-runnable/src\tools.ts:356:  // global cache breakpoint after the last prefix-matched built-in tool; a flat
_archive/compare_code/gg-claude-code-runnable/src\tools.ts:358:  // cache keys whenever an MCP tool sorts between existing built-ins. uniqBy
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:13:  cacheBreak: boolean
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:18: * Computed once, cached until /clear or /compact.
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:24:  return { name, compute, cacheBreak: false }
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:29: * This WILL break the prompt cache when the value changes.
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:30: * Requires a reason explaining why cache-breaking is necessary.
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:32:export function DANGEROUS_uncachedSystemPromptSection(
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:37:  return { name, compute, cacheBreak: true }
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:46:  const cache = getSystemPromptSectionCache()
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:50:      if (!s.cacheBreak && cache.has(s.name)) {
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:51:        return cache.get(s.name) ?? null
_archive/compare_code/gg-claude-code-runnable/src\constants\systemPromptSections.ts:63: * evaluation of AFK/fast-mode/cache-editing headers.
_archive/compare_code/gg-claude-code-runnable/src\bridge\trustedDevice.ts:62:  readStoredToken.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\bridge\trustedDevice.ts:66: * Clear the stored trusted device token from secure storage and the memo cache.
_archive/compare_code/gg-claude-code-runnable/src\bridge\trustedDevice.ts:70: * enrollment completion would otherwise still read the old cached token).
_archive/compare_code/gg-claude-code-runnable/src\bridge\trustedDevice.ts:86:  readStoredToken.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\bridge\trustedDevice.ts:198:      readStoredToken.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\bridge\remoteBridgeCore.ts:692:    // clears keychain cache + force-refreshes. No proactive refresh on the
_archive/compare_code/gg-claude-code-runnable/src\bridge\remoteBridgeCore.ts:976:  // Unlike bridgeMain.ts (which caches compatId in sessionCompatIds to keep
_archive/compare_code/gg-claude-code-runnable/src\utils\analyzeContext.ts:229:    cache_creation_input_tokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\analyzeContext.ts:230:    cache_read_input_tokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\analyzeContext.ts:282:  // Skip empty strings and the global-cache boundary marker
_archive/compare_code/gg-claude-code-runnable/src\utils\analyzeContext.ts:1166:  // Status line uses: input_tokens + cache_creation_input_tokens + cache_read_input_tokens
_archive/compare_code/gg-claude-code-runnable/src\utils\analyzeContext.ts:1169:      apiUsage.cache_creation_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\utils\analyzeContext.ts:1170:      apiUsage.cache_read_input_tokens
_archive/compare_code/gg-claude-code-runnable/src\bridge\jwtUtils.ts:194:      // becomes available again (e.g. transient cache clear during refresh).
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:72:  cache_control?: {
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:83:  cacheScope: CacheScope | null
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:129:    cacheControl?: {
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:137:  // eager_input_streaming. These are computed once per session and cached to
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:146:  // so including it preserves their GB-flip cache stability.
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:147:  const cacheKey =
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:151:  const cache = getToolSchemaCache()
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:152:  let base = cache.get(cacheKey)
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:208:    cache.set(cacheKey, base)
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:211:  // Per-request overlay: defer_loading and cache_control vary by call
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:212:  // (tool search defers different tools per turn; cache markers move).
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:213:  // Explicit field copy avoids mutating the cached base and sidesteps
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:214:  // BetaTool.cache_control's `| null` clashing with our narrower type.
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:228:  if (options.cacheControl) {
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:229:    schema.cache_control = options.cacheControl
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:238:  // cache_control is allowlisted: the base {type: 'ephemeral'} shape is
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:248:      'cache_control',
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:257:        ...(schema.cache_control && { cache_control: schema.cache_control }),
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:297: * Split system prompt blocks by content type for API matching and cache control.
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:303: *    Returns up to 3 blocks with org-level caching (no global cache on system prompt):
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:304: *    - Attribution header (cacheScope=null)
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:305: *    - System prompt prefix (cacheScope='org')
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:306: *    - Everything else concatenated (cacheScope='org')
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:308: * 2. Global cache mode with boundary marker (1P only, boundary found):
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:310: *    - Attribution header (cacheScope=null)
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:311: *    - System prompt prefix (cacheScope=null)
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:312: *    - Static content before boundary (cacheScope='global')
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:313: *    - Dynamic content after boundary (cacheScope=null)
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:317: *    - Attribution header (cacheScope=null)
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:318: *    - System prompt prefix (cacheScope='org')
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:319: *    - Everything else concatenated (cacheScope='org')
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:327:    logEvent('tengu_sysprompt_using_tool_based_cache', {
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:350:      result.push({ text: attributionHeader, cacheScope: null })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:353:      result.push({ text: systemPromptPrefix, cacheScope: 'org' })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:357:      result.push({ text: restJoined, cacheScope: 'org' })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:389:        result.push({ text: attributionHeader, cacheScope: null })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:391:        result.push({ text: systemPromptPrefix, cacheScope: null })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:394:        result.push({ text: staticJoined, cacheScope: 'global' })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:396:      if (dynamicJoined) result.push({ text: dynamicJoined, cacheScope: null })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:429:    result.push({ text: attributionHeader, cacheScope: null })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:431:    result.push({ text: systemPromptPrefix, cacheScope: 'org' })
_archive/compare_code/gg-claude-code-runnable/src\utils\api.ts:433:  if (restJoined) result.push({ text: restJoined, cacheScope: 'org' })
_archive/compare_code/gg-claude-code-runnable/src\query.ts:370:    // microcompact — cached MC operates purely by tool_use_id (never inspects
_archive/compare_code/gg-claude-code-runnable/src\query.ts:420:    // For cached microcompact (cache editing), defer boundary message until after
_archive/compare_code/gg-claude-code-runnable/src\query.ts:421:    // the API response so we can use actual cache_deleted_input_tokens.
_archive/compare_code/gg-claude-code-runnable/src\query.ts:490:          compactionUsage?.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\query.ts:492:          compactionUsage?.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\query.ts:495:            (compactionUsage.cache_creation_input_tokens ?? 0) +
_archive/compare_code/gg-claude-code-runnable/src\query.ts:496:            (compactionUsage.cache_read_input_tokens ?? 0) +
_archive/compare_code/gg-claude-code-runnable/src\query.ts:877:                  .cache_deleted_input_tokens ?? 0)
_archive/compare_code/gg-claude-code-runnable/src\query.ts:1125:          cacheSafeParams: {
_archive/compare_code/gg-claude-code-runnable/src\ink\dom.ts:6:import { addPendingClear, nodeCache } from './node-cache.js'
_archive/compare_code/gg-claude-code-runnable/src\ink\dom.ts:212:  // Collect cached rects from the removed subtree so they can be cleared
_archive/compare_code/gg-claude-code-runnable/src\ink\dom.ts:237:  const cached = nodeCache.get(elem)
_archive/compare_code/gg-claude-code-runnable/src\ink\dom.ts:238:  if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\ink\dom.ts:239:    addPendingClear(parent, cached, isAbsolute)
_archive/compare_code/gg-claude-code-runnable/src\remote\remotePermissionBridge.ts:39:        cache_creation_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\remote\remotePermissionBridge.ts:40:        cache_read_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\QueryEngine.ts:181: * turn within the same conversation. State (messages, file cache, usage, etc.)
_archive/compare_code/gg-claude-code-runnable/src\QueryEngine.ts:531:    // ref-tracked plugins. CCR populates the cache via CLAUDE_CODE_SYNC_PLUGIN_INSTALL
_archive/compare_code/gg-claude-code-runnable/src\QueryEngine.ts:1240:  setReadFileCache: (cache: FileStateCache) => void
_archive/compare_code/gg-claude-code-runnable/src\utils\asciicast.ts:22: * The path is computed once and cached in recordingState.
_archive/compare_code/gg-claude-code-runnable/src\ink\log-update.ts:590:      // Style transition — cached string, zero allocations after warmup
_archive/compare_code/gg-claude-code-runnable/src\ink\line-width-cache.ts:6:const cache = new Map<string, number>()
_archive/compare_code/gg-claude-code-runnable/src\ink\line-width-cache.ts:11:  const cached = cache.get(line)
_archive/compare_code/gg-claude-code-runnable/src\ink\line-width-cache.ts:12:  if (cached !== undefined) return cached
_archive/compare_code/gg-claude-code-runnable/src\ink\line-width-cache.ts:16:  // Evict when cache grows too large (e.g. after many different responses).
_archive/compare_code/gg-claude-code-runnable/src\ink\line-width-cache.ts:17:  // Simple full-clear is fine — the cache repopulates in one frame.
_archive/compare_code/gg-claude-code-runnable/src\ink\line-width-cache.ts:18:  if (cache.size >= MAX_CACHE_SIZE) {
_archive/compare_code/gg-claude-code-runnable/src\ink\line-width-cache.ts:19:    cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\ink\line-width-cache.ts:22:  cache.set(line, width)
_archive/compare_code/gg-claude-code-runnable/src\ink\measure-text.ts:1:import { lineWidth } from './line-width-cache.js'
_archive/compare_code/gg-claude-code-runnable/src\memdir\memdir.ts:123: * (once per session via systemPromptSection cache) so the model can always
_archive/compare_code/gg-claude-code-runnable/src\memdir\memdir.ts:330:  // this prompt is cached by systemPromptSection('memory', ...) and NOT
_archive/compare_code/gg-claude-code-runnable/src\memdir\memdir.ts:334:  // preserve the prompt cache prefix across midnight.
_archive/compare_code/gg-claude-code-runnable/src\memdir\paths.ts:221: * production and covered by per-test cache.clear.
_archive/compare_code/gg-claude-code-runnable/src\projectOnboardingState.ts:50:  // Short-circuit on cached config — isProjectOnboardingComplete() hits
_archive/compare_code/gg-claude-code-runnable/src\projectOnboardingState.ts:65:  // Short-circuit on cached config before isProjectOnboardingComplete()
_archive/compare_code/gg-claude-code-runnable/src\tools\ConfigTool\ConfigTool.ts:347:      // and the settings cache resets for the next /voice read.
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:112:import { cacheKeys, type FileStateCache } from './fileStateCache.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:510:         * ago" across turns → different bytes → prompt cache bust.
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:1407: * so the model learns the new date without mutating the cached prefix.
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:1409: * keeps the stale date — clearing that cache would regenerate the prefix
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:1410: * and turn the entire conversation into cache_creation on the next turn
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:1413: * Exported for testing — regression guard for the cache-clear removal.
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:1483: * fleet cache_creation: MCP async connect, /reload-plugins, or
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:1484: * permission-mode change → description changes → full tool-schema cache bust.
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:1738:      // stripped frontmatter, truncated MEMORY.md), cache the RAW disk bytes
_archive/compare_code/gg-claude-code-runnable/src\utils\attachments.ts:2066:  const filePaths = cacheKeys(toolUseContext.readFileState)
_archive/compare_code/gg-claude-code-runnable/src\tools\ListMcpResourcesTool\ListMcpResourcesTool.ts:79:    // fetchResourcesForClient is LRU-cached (by server name) and already
_archive/compare_code/gg-claude-code-runnable/src\ink\output.ts:30: * Built once per unique line (cached via charCache), so the per-char hot loop
_archive/compare_code/gg-claude-code-runnable/src\ink\output.ts:34: * styleId is safe to cache: StylePool is session-lived (never reset).
_archive/compare_code/gg-claude-code-runnable/src\ink\output.ts:196:   * becomes a cache hit.
_archive/compare_code/gg-claude-code-runnable/src\ink\output.ts:342:          // cached rect, but the parent ScrollBox may have shrunk (pill mount).
_archive/compare_code/gg-claude-code-runnable/src\ink\output.ts:762:    // Width was computed once during clustering (cached via charCache).
_archive/compare_code/gg-claude-code-runnable/src\ink\output.ts:785:    // style run, cached via charCache). Hot loop is now just property
_archive/compare_code/gg-claude-code-runnable/src\Tool.ts:289:   * by default (cache-sharing forks need identical decisions), or
_archive/compare_code/gg-claude-code-runnable/src\Tool.ts:295:   * Used by fork subagents to share the parent's prompt cache — re-calling
_archive/compare_code/gg-claude-code-runnable/src\Tool.ts:297:   * and bust the cache. See forkSubagent.ts.
_archive/compare_code/gg-claude-code-runnable/src\Tool.ts:478:   * input is never mutated (preserves prompt cache). Not re-applied when a
_archive/compare_code/gg-claude-code-runnable/src\ink\hit-test.ts:4:import { nodeCache } from './node-cache.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:80:/** Default TTL for API key helper cache in milliseconds (5 minutes) */
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:320:  // Check for apiKeyHelper — use sync cache, never block
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:431: * Calculate TTL in milliseconds for the API key helper cache
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:452:// Async API key helper with sync cache for non-blocking reads.
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:455:// mid-flight can't clobber the newer cache/inflight.
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:492:  // Cold cache — deduplicate concurrent calls
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:528:    // Cold cache or prior error — cache ' ' so callers don't fall back to OAuth
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:577: * Sync cache reader — returns the last fetched apiKeyHelper value without executing.
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:783: * Refresh AWS authentication and get credentials with cache clearing
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:799:    // Clear AWS INI cache to ensure fresh credentials are used
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:810:  refreshAndGetAwsCredentials.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:984:  refreshGcpCredentialsIfNeeded.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1157:  // Clear memo cache
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1158:  getApiKeyFromConfigOrMacOSKeychain.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1180:  // Clear memo cache
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1181:  getApiKeyFromConfigOrMacOSKeychain.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1239:    getClaudeAIOAuthTokens.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1303: * Clears all OAuth token caches. Call this on 401 errors to ensure
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1304: * the next token read comes from secure storage, not stale in-memory caches.
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1309:  getClaudeAIOAuthTokens.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1316:// disk (refresh or /login), but this process's memoize caches forever.
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1331:    // the memoize so it delegates to the keychain cache's 30s TTL instead
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1333:    // ~15ms; bounded to once per 30s by the keychain cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1334:    getClaudeAIOAuthTokens.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1340:// caches and re-read the keychain. Without this, each call's clearOAuthTokenCache()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1376:  // Clear caches and re-read from keychain (async — sync read blocks ~100ms/call)
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1455:  // First check if token is expired with cached value
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1474:  getClaudeAIOAuthTokens.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1519:    getClaudeAIOAuthTokens.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1541:    // Clear the cache after refreshing token
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1542:    getClaudeAIOAuthTokens.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1548:    getClaudeAIOAuthTokens.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1766:let cachedOtelHeaders: Record<string, string> | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1767:let cachedOtelHeadersTimestamp = 0
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1777:  // Return cached headers if still valid (debounce)
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1783:    cachedOtelHeaders &&
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1784:    Date.now() - cachedOtelHeadersTimestamp < debounceMs
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1786:    return cachedOtelHeaders
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1828:    cachedOtelHeaders = headers as Record<string, string>
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1829:    cachedOtelHeadersTimestamp = Date.now()
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1831:    return cachedOtelHeaders
_archive/compare_code/gg-claude-code-runnable/src\utils\auth.ts:1951:  // Even keychain-sourced tokens verify server-side: the cached org UUID
_archive/compare_code/gg-claude-code-runnable/src\utils\authFileDescriptor.ts:110:  const cached = getCached()
_archive/compare_code/gg-claude-code-runnable/src\utils\authFileDescriptor.ts:111:  if (cached !== undefined) {
_archive/compare_code/gg-claude-code-runnable/src\utils\authFileDescriptor.ts:112:    return cached
_archive/compare_code/gg-claude-code-runnable/src\ink\reconciler.ts:287:          `${_t0.toFixed(1)} SLOW_YOGA ${layoutMs.toFixed(1)}ms visited=${c.visited} measured=${c.measured} hits=${c.cacheHits} live=${c.live}\n`,
_archive/compare_code/gg-claude-code-runnable/src\tools\EnterWorktreeTool\EnterWorktreeTool.ts:98:    // Clear cached system prompt sections so env_info_simple recomputes with worktree context
_archive/compare_code/gg-claude-code-runnable/src\tools\EnterWorktreeTool\EnterWorktreeTool.ts:100:    // Clear memoized caches that depend on CWD
_archive/compare_code/gg-claude-code-runnable/src\tools\EnterWorktreeTool\EnterWorktreeTool.ts:102:    getPlansDirectory.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\tools\FileReadTool\FileReadTool.ts:526:    // waste cache_creation tokens on every subsequent turn. BQ proxy shows
_archive/compare_code/gg-claude-code-runnable/src\tools\FileReadTool\FileReadTool.ts:528:    // cache_creation). Only applies to text/notebook reads — images/PDFs
_archive/compare_code/gg-claude-code-runnable/src\tools\FileReadTool\FileReadTool.ts:529:    // aren't cached in readFileState so won't match here.
_archive/compare_code/gg-claude-code-runnable/src\utils\aws.ts:58: * Clear AWS credential provider cache by forcing a refresh
_archive/compare_code/gg-claude-code-runnable/src\utils\aws.ts:63:    logForDebugging('Clearing AWS credential provider cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\aws.ts:66:    await iniProvider() // This updates the global file cache
_archive/compare_code/gg-claude-code-runnable/src\utils\aws.ts:67:    logForDebugging('AWS credential provider cache refreshed')
_archive/compare_code/gg-claude-code-runnable/src\utils\aws.ts:69:    // Ignore errors - we're just clearing the cache
_archive/compare_code/gg-claude-code-runnable/src\utils\aws.ts:71:      'Failed to clear AWS credential cache (this is expected if no credentials are configured)',
_archive/compare_code/gg-claude-code-runnable/src\tools\BashTool\prompt.ts:164:// CLI flags) without deduping, so paths like ~/.cache appear 3× in allowOnly.
_archive/compare_code/gg-claude-code-runnable/src\tools\BashTool\prompt.ts:187:  // cross-user global prompt cache. The sandbox already sets $TMPDIR at runtime.
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:7:import { nodeCache, pendingClears } from './node-cache.js'
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:28:// its cached value, or a child was removed. Read by ink.tsx to decide
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:415:        const cached = nodeCache.get(node)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:416:        if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:418:            x: Math.floor(cached.x),
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:419:            y: Math.floor(cached.y),
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:420:            width: Math.floor(cached.width),
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:421:            height: Math.floor(cached.height),
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:423:          // Drop descendants' cache too — hideInstance's markDirty walks UP
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:454:    const cached = nodeCache.get(node)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:459:      cached &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:460:      cached.x === x &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:461:      cached.y === y &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:462:      cached.width === width &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:463:      cached.height === height &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:472:        absoluteRectsCur.push(cached)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:488:      cached !== undefined &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:489:      (cached.x !== x ||
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:490:        cached.y !== y ||
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:491:        cached.width !== width ||
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:492:        cached.height !== height)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:496:    if (cached && (node.dirty || positionChanged)) {
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:499:          x: Math.floor(cached.x),
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:500:          y: Math.floor(cached.y),
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:501:          width: Math.floor(cached.width),
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:502:          height: Math.floor(cached.height),
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:859:          // culled (cache dropped) and every newly-visible child has no
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:860:          // cache — so the children's positionChanged check can't fire.
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:861:          // The content wrapper's cached y (which encodes -scrollTop) is
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:874:              cached?.y === y &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:875:              cached.height === height &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:981:              // check cached.y−delta === screenY reduces to delta === delta
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:996:                  // Uncached = culled last frame, now re-entering. blit
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1020:                // no cache. Re-check precisely: cached.y − delta is where
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1023:                // yogaTop happens to net out). No cache → blit never
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1116:            // self-clear via their own cached-rect clear. Without this, a
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1130:            // child spanning the old bottom edge would blit its full cached
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1352:      const cached = nodeCache.get(elem)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1353:      if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1354:        absoluteRectsCur.push(cached)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1355:        const cx = Math.floor(cached.x)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1356:        const cy = Math.floor(cached.y)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1357:        const cw = Math.floor(cached.width)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1358:        const ch = Math.floor(cached.height)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1387:  // When true (DECSTBM fast path), culled children keep their cache —
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1388:  // the blit+shift put stable rows in next.screen so stale cache is
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1395:  // so cached.top is fresh and the cull check skips yoga. Bottom-append
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1396:  // has the dirty child last → all prior clean children hit cache →
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1405:      const cached = nodeCache.get(childElem)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1409:        cached?.top !== undefined &&
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1413:        top = cached.top
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1414:        height = cached.height
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1419:          cumHeightShift += height - (cached ? cached.height : 0)
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1421:        // Refresh cached top so next frame's cumShift===0 path stays
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1425:        if (cached) cached.top = top
_archive/compare_code/gg-claude-code-runnable/src\ink\render-node-to-output.ts:1429:        // Culled — outside visible window. Drop stale cache entries from
_archive/compare_code/gg-claude-code-runnable/src\ink\render-to-screen.ts:35:// means later calls hit cache more. Root/container reuse saves the
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\agentToolUtils.ts:241:      cache_creation_input_tokens: z.number().nullable(),
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\agentToolUtils.ts:242:      cache_read_input_tokens: z.number().nullable(),
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\agentToolUtils.ts:250:      cache_creation: z
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\agentToolUtils.ts:337:  // Signal to inference that this subagent's cache chain can be evicted.
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\agentToolUtils.ts:340:    logEvent('tengu_cache_eviction_hint', {
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\forkSubagent.ts:49: * child receives the parent's exact tool pool (for cache-identical API
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\forkSubagent.ts:58: * bust the prompt cache; threading the rendered bytes is byte-exact.
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\forkSubagent.ts:75: * tool pool for cache-identical tool definitions, so we reject fork attempts
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\forkSubagent.ts:92: * Must be identical across all fork children for prompt cache sharing. */
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\forkSubagent.ts:98: * For prompt cache sharing, all fork children must produce byte-identical
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\forkSubagent.ts:105: * Only the final text block differs per child, maximizing cache hits.
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\loadAgentsDir.ts:396:  getAgentDefinitionsWithOverrides.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\prompt.ts:53: * The dynamic agent list was ~10.2% of fleet cache_creation tokens: MCP async
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\prompt.ts:55: * description changes → full tool-schema cache bust.
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\prompt.ts:86:- **Research**: fork open-ended questions. If research can be broken into independent questions, launch parallel forks in one message. A fork beats a fresh subagent for this \u2014 it inherits context and shares your cache.
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\prompt.ts:89:Forks are cheap because they share your prompt cache. Don't set \`model\` on a fork \u2014 a different model can't reuse the parent's cache. Pass a short \`name\` (one or two words, lowercase) so the user can see the fork in the teams panel and steer it mid-run.
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\prompt.ts:193:  // tools-block prompt cache doesn't bust every time an agent loads.
_archive/compare_code/gg-claude-code-runnable/src\tools\FileEditTool\utils.ts:602:    // Use cached file read to avoid redundant I/O operations.
_archive/compare_code/gg-claude-code-runnable/src\tools\SyntheticOutputTool\SyntheticOutputTool.ts:108:// cache brings 80-call workflows from ~110ms to ~4ms Ajv overhead.
_archive/compare_code/gg-claude-code-runnable/src\tools\SyntheticOutputTool\SyntheticOutputTool.ts:119:  const cached = toolCache.get(jsonSchema)
_archive/compare_code/gg-claude-code-runnable/src\tools\SyntheticOutputTool\SyntheticOutputTool.ts:120:  if (cached) return cached
_archive/compare_code/gg-claude-code-runnable/src\tools\ScheduleCronTool\prompt.ts:24: * imperative setup, never at module scope — so the disk cache has had a
_archive/compare_code/gg-claude-code-runnable/src\tools\ExitWorktreeTool\prompt.ts:28:- Clears CWD-dependent caches (system prompt sections, memory files, plans directory) so the session state reflects the original directory
_archive/compare_code/gg-claude-code-runnable/src\tools\ExitWorktreeTool\ExitWorktreeTool.ts:145:  getPlansDirectory.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\tools\SleepTool\prompt.ts:17:Each wake-up costs an API call, but the prompt cache expires after 5 minutes of inactivity — balance accordingly.`
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\built-in\statuslineSetup.ts:61:         "cache_creation_input_tokens": number,  // Tokens written to cache
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\built-in\statuslineSetup.ts:62:         "cache_read_input_tokens": number       // Tokens read from cache
_archive/compare_code/gg-claude-code-runnable/src\tools\NotebookEditTool\NotebookEditTool.ts:326:      // Must use non-memoized jsonParse here: safeParseJSON caches by content
_archive/compare_code/gg-claude-code-runnable/src\tools\NotebookEditTool\NotebookEditTool.ts:329:      // Using the memoized version poisons the cache for validateInput() and
_archive/compare_code/gg-claude-code-runnable/src\tools\BashTool\readOnlyValidation.ts:902:      // OMITTED (writes to disk): -D (device cache file build/update)
_archive/compare_code/gg-claude-code-runnable/src\tools\BashTool\readOnlyValidation.ts:1725:      // Using regex to catch spaces, tabs, and other whitespace (not part of other flags like --cached)
_archive/compare_code/gg-claude-code-runnable/src\ink\renderer.ts:4:import { consumeAbsoluteRemovedFlag } from './node-cache.js'
_archive/compare_code/gg-claude-code-runnable/src\ink\screen.ts:34:        const cached = this.ascii[code]!
_archive/compare_code/gg-claude-code-runnable/src\ink\screen.ts:35:        if (cached !== -1) return cached
_archive/compare_code/gg-claude-code-runnable/src\ink\screen.ts:881:  // blitted content (a cached ink-text node) is what set the bit.
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\prompt.ts:26:// full content on invoke, so verbose whenToUse strings waste turn-1 cache_creation
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\prompt.ts:218:  getPrompt.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\state\onChangeAppState.ts:154:  // settings: clear auth-related caches when settings change
_archive/compare_code/gg-claude-code-runnable/src\hooks\useManagePlugins.ts:113:      // cache slot that extractMcpServersFromPlugins fills later, which races
_archive/compare_code/gg-claude-code-runnable/src\hooks\useManagePlugins.ts:116:      // warms the cache for the MCP connection manager.
_archive/compare_code/gg-claude-code-runnable/src\hooks\useManagePlugins.ts:132:      // clears caches first). This reinit is defensive — it reads the same
_archive/compare_code/gg-claude-code-runnable/src\hooks\useManagePlugins.ts:133:      // memoized loadAllPlugins() result as the original init unless a cache
_archive/compare_code/gg-claude-code-runnable/src\hooks\useManagePlugins.ts:275:        has_custom_plugin_cache_dir: !!process.env.CLAUDE_CODE_PLUGIN_CACHE_DIR,
_archive/compare_code/gg-claude-code-runnable/src\hooks\useManagePlugins.ts:289:  // to apply. The previous auto-refresh here had a stale-cache bug (only
_archive/compare_code/gg-claude-code-runnable/src\hooks\useMainLoopModel.ts:19:  // that's the stale disk cache; after, it's the in-memory remoteEval map.
_archive/compare_code/gg-claude-code-runnable/src\utils\betas.ts:431:  getAllModelBetas.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\betas.ts:432:  getModelBetas.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\betas.ts:433:  getBedrockExtraBodyParamsBetas.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\setup.ts:202:      // findGitRoot cache was already warmed by getIsGit() above, so this is ~free.
_archive/compare_code/gg-claude-code-runnable/src\setup.ts:279:    // Clear memory files cache since originalCwd has changed
_archive/compare_code/gg-claude-code-runnable/src\setup.ts:281:    // Settings cache was populated in init() (via applySafeConfigEnvironmentVariables)
_archive/compare_code/gg-claude-code-runnable/src\setup.ts:312:  // races with the install (concurrent copyPluginToVersionedCache / cachePlugin
_archive/compare_code/gg-claude-code-runnable/src\setup.ts:338:      // Prime repo classification cache for auto-undercover mode. Default is
_archive/compare_code/gg-claude-code-runnable/src\setup.ts:340:      // the prompt cache so the next turn picks up the OFF state.
_archive/compare_code/gg-claude-code-runnable/src\setup.ts:463:      last_session_total_cache_creation_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\setup.ts:465:      last_session_total_cache_read_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\utils\binaryCheck.ts:4:// Session cache to avoid repeated checks
_archive/compare_code/gg-claude-code-runnable/src\utils\binaryCheck.ts:24:  // Check cache first
_archive/compare_code/gg-claude-code-runnable/src\utils\binaryCheck.ts:25:  const cached = binaryCache.get(trimmedCommand)
_archive/compare_code/gg-claude-code-runnable/src\utils\binaryCheck.ts:26:  if (cached !== undefined) {
_archive/compare_code/gg-claude-code-runnable/src\utils\binaryCheck.ts:28:      `[binaryCheck] Cache hit for '${trimmedCommand}': ${cached}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\binaryCheck.ts:30:    return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\binaryCheck.ts:49: * Clear the binary check cache (useful for testing)
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\SkillTool.ts:602:    // AKI/GCS (with local cache), injects content directly as a user message.
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\SkillTool.ts:996:      cacheHit: false,
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\SkillTool.ts:1005:    cacheHit,
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\SkillTool.ts:1016:    cacheHit,
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\SkillTool.ts:1049:    remote_cache_hit: cacheHit,
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\SkillTool.ts:1062:    `SkillTool loaded remote skill ${slug} (cacheHit=${cacheHit}, ${latencyMs}ms, ${content.length} chars)`,
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\SkillTool.ts:1072:  // refs like ./schemas/foo.json against the cache dir.
_archive/compare_code/gg-claude-code-runnable/src\tools\SkillTool\SkillTool.ts:1083:  // Register with compaction-preservation state. Use the cached file path so
_archive/compare_code/gg-claude-code-runnable/src\tools\shared\spawnMultiAgent.ts:366:    // If they installed it2 or chose tmux, clear cached detection and re-fetch
_archive/compare_code/gg-claude-code-runnable/src\tools\shared\spawnMultiAgent.ts:1071:  // Backend is available (and now cached) - proceed with pane spawning.
_archive/compare_code/gg-claude-code-runnable/src\skills\loadSkillsDir.ts:807:  getSkillDirCommands.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\skills\loadSkillsDir.ts:808:  loadMarkdownFilesForSubdir.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\skills\loadSkillsDir.ts:828:// Names of skills that have been activated (survives cache clears within a session)
_archive/compare_code/gg-claude-code-runnable/src\skills\loadSkillsDir.ts:836: * Used by other modules to clear caches without creating import cycles.
_archive/compare_code/gg-claude-code-runnable/src\skills\loadSkillsDir.ts:973:  // Notify listeners that skills were loaded (so they can clear caches)
_archive/compare_code/gg-claude-code-runnable/src\skills\loadSkillsDir.ts:1053:    // Notify listeners that skills were loaded (so they can clear caches)
_archive/compare_code/gg-claude-code-runnable/src\services\AgentSummary\agentSummary.ts:9: * to share the prompt cache. Tools are kept in the request for cache
_archive/compare_code/gg-claude-code-runnable/src\services\AgentSummary\agentSummary.ts:49:  cacheSafeParams: CacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\AgentSummary\agentSummary.ts:55:  const { forkContextMessages: _drop, ...baseParams } = cacheSafeParams
_archive/compare_code/gg-claude-code-runnable/src\services\AgentSummary\agentSummary.ts:93:      // Deny tools via callback, NOT by passing tools:[] - that busts cache
_archive/compare_code/gg-claude-code-runnable/src\services\AgentSummary\agentSummary.ts:101:      // thread's prompt cache by sending identical cache-key params (system,
_archive/compare_code/gg-claude-code-runnable/src\services\AgentSummary\agentSummary.ts:104:      // invalidates the cache.
_archive/compare_code/gg-claude-code-runnable/src\services\AgentSummary\agentSummary.ts:113:        cacheSafeParams: forkParams,
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:262:      // or fall back to standard speed (long delays) to avoid cache thrashing.
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:266:      // keep-alive path instead of fast-mode cache-preservation anyway.
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:284:        const retryAfterMs = getRetryAfterMs(error)
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:287:          // to preserve prompt cache (same model name on retry).
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:389:        const overflowData = parseMaxTokensContextOverflowError(error)
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:431:      const retryAfter = getRetryAfter(error)
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:450:        // Retry-After is a server directive and bypasses maxDelayMs inside
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:519:function getRetryAfter(error: unknown): string | null {
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:550:export function parseMaxTokensContextOverflowError(error: APIError):
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:647: * Clear AWS auth caches if appropriate.
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:685: * Clear GCP auth caches if appropriate.
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:727:  if (parseMaxTokensContextOverflowError(error)) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:771:  // Clear API key cache on 401 and allow retry.
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:803:function getRetryAfterMs(error: APIError): number | null {
_archive/compare_code/gg-claude-code-runnable/src\services\api\withRetry.ts:804:  const retryAfter = getRetryAfter(error)
_archive/compare_code/gg-claude-code-runnable/src\services\api\sessionIngress.ts:500: * Clear cached state for a session
_archive/compare_code/gg-claude-code-runnable/src\services\api\sessionIngress.ts:508: * Clear all cached session state (all sessions).
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:80: * Check cached passes eligibility from GlobalConfig
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:81: * Returns current cached state and cache status
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:106:  const cachedEntry = config.passesEligibilityCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:108:  if (!cachedEntry) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:109:    // No cached entry, needs fetch
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:117:  const { eligible, timestamp } = cachedEntry
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:147: * Get cached referrer reward info from eligibility cache
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:154:  const cachedEntry = config.passesEligibilityCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:155:  return cachedEntry?.referrer_reward ?? null
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:159: * Get the cached remaining passes count from eligibility cache
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:166:  const cachedEntry = config.passesEligibilityCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:167:  return cachedEntry?.remaining_passes ?? null
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:192:      const cacheEntry = {
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:201:          [orgId]: cacheEntry,
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:206:        `Passes eligibility cached for org ${orgId}: ${response.eligible}`,
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:211:      logForDebugging('Failed to fetch and cache passes eligibility')
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:224: * Get cached passes eligibility data or fetch if needed
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:227: * This function never blocks on network - it returns cached data immediately
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:228: * and fetches in the background if needed. On cold start (no cache), it returns
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:242:  const cachedEntry = config.passesEligibilityCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:245:  // No cache - trigger background fetch and return null (non-blocking)
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:247:  if (!cachedEntry) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:249:      'Passes: No cache, fetching eligibility in background (command unavailable this session)',
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:255:  // Cache exists but is stale - return stale cache and trigger background refresh
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:256:  if (now - cachedEntry.timestamp > CACHE_EXPIRATION_MS) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:258:      'Passes: Cache stale, returning cached data and refreshing in background',
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:261:    const { timestamp, ...response } = cachedEntry
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:266:  logForDebugging('Passes: Using fresh cached eligibility data')
_archive/compare_code/gg-claude-code-runnable/src\services\api\referral.ts:267:  const { timestamp, ...response } = cachedEntry
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:25:  return join(getClaudeTempDir(), `cache-break-${suffix}.diff`)
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:31:  /** Hash of system blocks WITH cache_control intact. Catches scope/TTL flips
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:33:  cacheControlHash: number
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:47:  /** AFK_MODE_BETA_HEADER presence — should NOT break cache anymore
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:50:  /** Overage state flip — should NOT break cache anymore (eligibility is
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:53:  /** Cache-editing beta header presence — should NOT break cache anymore
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:55:  cachedMCEnabled: boolean
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:65:  /** Set when cached microcompact sends cache_edits deletions. Cache reads
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:67:  cacheDeletionsPending: boolean
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:76:  cacheControlChanged: boolean
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:81:  cachedMCChanged: boolean
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:117:// Minimum absolute token drop required to trigger a cache break warning.
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:122:// Anthropic's server-side prompt cache TTL thresholds to test.
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:128:// Models to exclude from cache break detection (e.g., haiku has different caching behavior)
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:129:function isExcludedModel(model: string): boolean {
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:135: * Compact shares the same server-side cache as repl_main_thread
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:136: * (same cacheSafeParams), so they share tracking state.
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:139: * isolate tracking state. This prevents false positive cache break
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:144: * are short-lived forked agents where cache break detection provides no
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:146: * nothing meaningful to compare against. Their cache metrics are still
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:164:    if (!('cache_control' in item)) return item
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:165:    const { cache_control: _, ...rest } = item
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:225: *  cache key that we can observe from the client. All fields are optional so
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:238:  cachedMCEnabled?: boolean
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:260:      cachedMCEnabled = false,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:276:    // Hash the full system array INCLUDING cache_control — this catches
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:279:    const cacheControlHash = computeHash(
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:280:      system.map(b => ('cache_control' in b ? b.cache_control : null)),
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:308:        cacheControlHash,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:317:        cachedMCEnabled,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:323:        cacheDeletionsPending: false,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:336:    const cacheControlChanged = cacheControlHash !== prev.cacheControlHash
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:344:    const cachedMCChanged = cachedMCEnabled !== prev.cachedMCEnabled
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:353:      cacheControlChanged ||
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:358:      cachedMCChanged ||
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:384:        cacheControlChanged,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:389:        cachedMCChanged,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:414:    prev.cacheControlHash = cacheControlHash
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:423:    prev.cachedMCEnabled = cachedMCEnabled
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:433: * Phase 2 (post-call): Check the API response's cache tokens to determine
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:434: * if a cache break actually occurred. If it did, use the pending changes
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:439:  cacheReadTokens: number,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:440:  cacheCreationTokens: number,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:453:    if (isExcludedModel(state.model)) return
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:456:    state.prevCacheReadTokens = cacheReadTokens
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:470:    // Cache deletions via cached microcompact intentionally reduce the cached
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:471:    // prefix. The drop in cache read tokens is expected — reset the baseline
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:473:    if (state.cacheDeletionsPending) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:474:      state.cacheDeletionsPending = false
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:476:        `[PROMPT CACHE] cache deletion applied, cache read: ${prevCacheRead} → ${cacheReadTokens} (expected drop)`,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:483:    // Detect a cache break: cache read dropped >5% from previous AND
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:485:    const tokenDrop = prevCacheRead - cacheReadTokens
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:487:      cacheReadTokens >= prevCacheRead * 0.95 ||
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:524:          `global cache strategy changed (${changes.prevGlobalCacheStrategy || 'none'} → ${changes.newGlobalCacheStrategy || 'none'})`,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:528:        changes.cacheControlChanged &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:534:        parts.push('cache_control changed (scope or TTL)')
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:552:      if (changes.cachedMCChanged) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:553:        parts.push('cached microcompact toggled')
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:573:    // Post PR #19823 BQ analysis (bq-queries/prompt-caching/cache_break_pr19823_analysis.sql):
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:590:    logEvent('tengu_prompt_cache_break', {
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:595:      cacheControlChanged: changes?.cacheControlChanged ?? false,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:600:      cachedMCChanged: changes?.cachedMCChanged ?? false,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:623:      // Beta header names and cache strategy are fixed enum-like values,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:637:      cacheReadTokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:638:      cacheCreationTokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:658:    const summary = `[PROMPT CACHE BREAK] ${reason} [source=${querySource}, call #${state.callCount}, cache read: ${prevCacheRead} → ${cacheReadTokens}, creation: ${cacheCreationTokens}${diffSuffix}]`
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:669: * Call when cached microcompact sends cache_edits deletions.
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:670: * The next API response will have lower cache read tokens — that's
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:671: * expected, not a cache break.
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:680:    state.cacheDeletionsPending = true
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:685: * Call after compaction to reset the cache read baseline.
_archive/compare_code/gg-claude-code-runnable/src\services\api\promptCacheBreakDetection.ts:686: * Compaction legitimately reduces message count, so cache read tokens
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:44: * Get cached grant info. Returns null if no cache or cache is stale.
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:51:  const cached = getGlobalConfig().overageCreditGrantCache?.[orgId]
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:52:  if (!cached) return null
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:53:  if (Date.now() - cached.timestamp > CACHE_TTL_MS) return null
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:54:  return cached.info
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:58: * Drop the current org's cached entry so the next read refetches.
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:64:  const cache = getGlobalConfig().overageCreditGrantCache
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:65:  if (!cache || !(orgId in cache)) return
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:74: * Fetch and cache grant info. Fire-and-forget; call when an upsell surface
_archive/compare_code/gg-claude-code-runnable/src\services\api\overageCreditGrant.ts:75: * is about to render and the cache is empty.
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:24:// Disk TTL — org settings rarely change. When disk cache is fresher than this,
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:100:  const cached = getGlobalConfig().metricsStatusCache
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:101:  const unchanged = cached !== undefined && cached.enabled === result.enabled
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:104:  if (unchanged && Date.now() - cached.timestamp < DISK_CACHE_TTL_MS) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:121: * Two-tier cache:
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:122: * - Disk (24h TTL): survives process restarts. Fresh disk cache → zero network.
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:133:  // session would poison the cache for a later full-OAuth session.
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:138:  const cached = getGlobalConfig().metricsStatusCache
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:139:  if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:140:    if (Date.now() - cached.timestamp > DISK_CACHE_TTL_MS) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:147:      enabled: cached.enabled,
_archive/compare_code/gg-claude-code-runnable/src\services\api\metricsOptOut.ts:158:  memoizedCheckMetrics.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:89:  // https://www.braintrust.dev/docs/guides/proxy — x-bt-used-endpoint, x-bt-cached
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:482:    cachedInputTokens: usage.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:483:    uncachedInputTokens: usage.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:555:    // Log cache_deleted_input_tokens for cache editing analysis. Casts needed
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:557:    // external builds). Set by updateUsage() when cache editing is active.
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:559:    ((usage as unknown as { cache_deleted_input_tokens?: number })
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:560:      .cache_deleted_input_tokens ?? 0) > 0
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:562:          cacheDeletedInputTokens: (
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:563:            usage as unknown as { cache_deleted_input_tokens: number }
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:564:          ).cache_deleted_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:722:    cache_read_tokens: String(usage.cache_read_input_tokens),
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:723:    cache_creation_tokens: String(usage.cache_creation_input_tokens),
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:768:    cacheReadTokens: usage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\logging.ts:769:    cacheCreationTokens: usage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:77:      // Don't cache failures — transient network issues would lock the user
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:80:      // is the only other place the cache is cleared).
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:81:      getGroveSettings.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:111:    getGroveSettings.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:144:    getGroveSettings.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:151: * Check if user is qualified for Grove (non-blocking, cache-first).
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:153: * This function never blocks on network - it returns cached data immediately
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:154: * and fetches in the background if needed. On cold start (no cache), it returns
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:168:  const cachedEntry = globalConfig.groveConfigCache?.[accountId]
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:171:  // No cache - trigger background fetch and return false (non-blocking)
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:173:  if (!cachedEntry) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:175:      'Grove: No cache, fetching config in background (dialog skipped this session)',
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:181:  // Cache exists but is stale - return cached value and refresh in background
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:182:  if (now - cachedEntry.timestamp > GROVE_CACHE_EXPIRATION_MS) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:184:      'Grove: Cache stale, returning cached data and refreshing in background',
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:187:    return cachedEntry.grove_enabled
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:191:  logForDebugging('Grove: Using fresh cached config')
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:192:  return cachedEntry.grove_enabled
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:196: * Fetch Grove config from API and store in cache
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:205:    const cachedEntry = getGlobalConfig().groveConfigCache?.[accountId]
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:207:      cachedEntry?.grove_enabled === groveEnabled &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\grove.ts:208:      Date.now() - cachedEntry.timestamp <= GROVE_CACHE_EXPIRATION_MS
_archive/compare_code/gg-claude-code-runnable/src\services\api\firstTokenDate.ts:10: * This is called after successful login to cache when they started using Claude Code.
_archive/compare_code/gg-claude-code-runnable/src\services\api\errorUtils.ts:169:function extractNestedErrorMessage(error: APIError): string | null {
_archive/compare_code/gg-claude-code-runnable/src\services\api\errorUtils.ts:250:      extractNestedErrorMessage(error) ??
_archive/compare_code/gg-claude-code-runnable/src\services\api\emptyUsage.ts:10:  cache_creation_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\services\api\emptyUsage.ts:11:  cache_read_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\services\api\emptyUsage.ts:15:  cache_creation: {
_archive/compare_code/gg-claude-code-runnable/src\services\api\dumpPrompts.ts:15:const cachedApiRequests: Array<{ timestamp: string; request: unknown }> = []
_archive/compare_code/gg-claude-code-runnable/src\services\api\dumpPrompts.ts:33:  return [...cachedApiRequests]
_archive/compare_code/gg-claude-code-runnable/src\services\api\dumpPrompts.ts:37:  cachedApiRequests.length = 0
_archive/compare_code/gg-claude-code-runnable/src\services\api\dumpPrompts.ts:50:  cachedApiRequests.push({
_archive/compare_code/gg-claude-code-runnable/src\services\api\dumpPrompts.ts:54:  if (cachedApiRequests.length > MAX_CACHED_REQUESTS) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\dumpPrompts.ts:55:    cachedApiRequests.shift()
_archive/compare_code/gg-claude-code-runnable/src\services\api\client.ts:180:      // Refresh auth and get credentials with cache clearing
_archive/compare_code/gg-claude-code-runnable/src\services\api\client.ts:181:      const cachedCredentials = await refreshAndGetAwsCredentials()
_archive/compare_code/gg-claude-code-runnable/src\services\api\client.ts:182:      if (cachedCredentials) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\client.ts:183:        bedrockArgs.awsAccessKey = cachedCredentials.accessKeyId
_archive/compare_code/gg-claude-code-runnable/src\services\api\client.ts:184:        bedrockArgs.awsSecretKey = cachedCredentials.secretAccessKey
_archive/compare_code/gg-claude-code-runnable/src\services\api\client.ts:185:        bedrockArgs.awsSessionToken = cachedCredentials.sessionToken
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:283:        // Shallow clone — safeParseJSON is LRU-cached and returns the same
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:285:        // would poison the cache, causing stale values to persist.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:390: * The allowlist is cached in STATE for session stability — prevents mixed
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:391: * TTLs when GrowthBook's disk cache updates mid-request.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:404:  // mid-session overage flips from changing the cache_control TTL, which
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:405:  // would bust the server-side prompt cache (~20K tokens per flip).
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:416:  // TTLs when GrowthBook's disk cache updates mid-request
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:421:    }>('tengu_prompt_cache_1h_config', {})
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:603:              cache_control: getCacheControl({ querySource }),
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:615:              ? { cache_control: getCacheControl({ querySource }) }
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:624:  // to addCacheBreakpoints share the same array and each splices in duplicate cache_edits.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:648:              cache_control: getCacheControl({ querySource }),
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:663:              ? { cache_control: getCacheControl({ querySource }) }
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:922: * join them for cache-hit-rate analysis and incremental token tracking.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1184:  // Determine if cached microcompact is enabled for this model.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1188:  let cachedMCEnabled = false
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1189:  let cacheEditingBetaHeader = ''
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1195:    } = await import('../compact/cachedMicrocompact.js')
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1197:    cacheEditingBetaHeader = betas.CACHE_EDITING_BETA_HEADER
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1200:    cachedMCEnabled = featureEnabled && modelSupported
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1210:  // MCP tools are per-user → dynamic tool section → can't globally cache.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1216:  // Ensure prompt_caching_scope beta header is present when global cache is enabled.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1224:  // Determine global cache strategy for logging
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1329:  // ephemeral prepend (which busts cache whenever the pool changes).
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1350:  // busts the prompt cache when chrome connects late.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1388:    // toolSchemas (which carries the cache_control marker) so toggling /advisor
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1389:    // only churns the small suffix, not the cached prefix.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1407:  // toggles don't change the server-side cache key and bust ~50-70K tokens.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1431:  let cacheEditingHeaderLatched = getCacheEditingHeaderLatched() === true
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1434:      !cacheEditingHeaderLatched &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1435:      cachedMCEnabled &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1439:      cacheEditingHeaderLatched = true
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1462:    // prompt, so they never affect the actual cache key. Including them creates
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1468:    // Capture everything that could affect the server-side cache key.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1482:      cachedMCEnabled: cacheEditingHeaderLatched,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1528:  // Consume pending cache edits ONCE before paramsFromContext is defined.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1531:  const consumedCacheEdits = cachedMCEnabled ? consumePendingCacheEdits() : null
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1532:  const consumedPinnedEdits = cachedMCEnabled ? getPinnedCacheEdits() : []
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1642:    // Fast mode: header is latched session-stable (cache-safe), but
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1644:    // fast-mode request without changing the cache key.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1673:    // (controls cache_edits body behavior) stays live so edits stop when
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1676:      cachedMCEnabled &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1680:      cacheEditingHeaderLatched &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1683:      !betasParams.includes(cacheEditingBetaHeader)
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1685:      betasParams.push(cacheEditingBetaHeader)
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1687:        'Cache editing beta header enabled for cached microcompact',
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:1792:        // once per attempt; on retries the client is usually cached (withRetry
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2382:      // Check if the cache actually broke based on response tokens
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2386:          usage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2387:          usage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2834:  if (feature('CACHED_MICROCOMPACT') && cachedMCEnabled) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2839:  // can send a cache eviction hint to inference. Exclude backgrounded
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2842:  // whose cache should not be evicted when the foreground session clears.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2919: * Input-related tokens (input_tokens, cache_creation_input_tokens, cache_read_input_tokens)
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2936:    cache_creation_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2937:      partUsage.cache_creation_input_tokens !== null &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2938:      partUsage.cache_creation_input_tokens > 0
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2939:        ? partUsage.cache_creation_input_tokens
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2940:        : usage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2941:    cache_read_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2942:      partUsage.cache_read_input_tokens !== null &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2943:      partUsage.cache_read_input_tokens > 0
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2944:        ? partUsage.cache_read_input_tokens
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2945:        : usage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2956:    cache_creation: {
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2957:      // SDK type BetaMessageDeltaUsage is missing cache_creation, but it's real!
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2959:        (partUsage as BetaUsage).cache_creation?.ephemeral_1h_input_tokens ??
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2960:        usage.cache_creation.ephemeral_1h_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2962:        (partUsage as BetaUsage).cache_creation?.ephemeral_5m_input_tokens ??
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2963:        usage.cache_creation.ephemeral_5m_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2965:    // cache_deleted_input_tokens: returned by the API when cache editing
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2966:    // deletes KV cache content, but not in SDK types. Kept off NonNullableUsage
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2972:          cache_deleted_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2973:            (partUsage as unknown as { cache_deleted_input_tokens?: number })
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2974:              .cache_deleted_input_tokens != null &&
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2975:            (partUsage as unknown as { cache_deleted_input_tokens: number })
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2976:              .cache_deleted_input_tokens > 0
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2977:              ? (partUsage as unknown as { cache_deleted_input_tokens: number })
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2978:                  .cache_deleted_input_tokens
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2979:              : ((usage as unknown as { cache_deleted_input_tokens?: number })
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2980:                  .cache_deleted_input_tokens ?? 0),
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:2999:    cache_creation_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3000:      totalUsage.cache_creation_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3001:      messageUsage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3002:    cache_read_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3003:      totalUsage.cache_read_input_tokens + messageUsage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3014:    cache_creation: {
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3016:        totalUsage.cache_creation.ephemeral_1h_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3017:        messageUsage.cache_creation.ephemeral_1h_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3019:        totalUsage.cache_creation.ephemeral_5m_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3020:        messageUsage.cache_creation.ephemeral_5m_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3026:          cache_deleted_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3027:            ((totalUsage as unknown as { cache_deleted_input_tokens?: number })
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3028:              .cache_deleted_input_tokens ?? 0) +
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3030:              messageUsage as unknown as { cache_deleted_input_tokens?: number }
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3031:            ).cache_deleted_input_tokens ?? 0),
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3053:  type: 'cache_edits'
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3054:  edits: { type: 'delete'; cache_reference: string }[]
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3062:// Exported for testing cache_reference placement constraints
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3072:  logEvent('tengu_api_cache_breakpoints', {
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3078:  // Exactly one message-level cache_control marker per request. Mycro's
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3080:  // local-attention KV pages at any cached prefix position NOT in
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3081:  // cache_store_int_token_boundaries. With two markers the second-to-last
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3112:  // Track all cache_references being deleted to prevent duplicates across blocks.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3115:  // Helper to deduplicate a cache_edits block against already-seen deletions
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3118:      if (seenDeleteRefs.has(edit.cache_reference)) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3121:      seenDeleteRefs.add(edit.cache_reference)
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3127:  // Re-insert all previously-pinned cache_edits at their original positions
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3141:  // Insert new cache_edits into the last user message and pin them
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3156:            `Added cache_edits block with ${dedupedNewEdits.edits.length} deletion(s) to message[${i}]: ${dedupedNewEdits.edits.map(e => e.cache_reference).join(', ')}`,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3164:  // Add cache_reference to tool_result blocks that are within the cached prefix.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3165:  // Must be done AFTER cache_edits insertion since that modifies content arrays.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3167:    // Find the last message containing a cache_control marker
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3173:          if (block && typeof block === 'object' && 'cache_control' in block) {
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3180:    // Add cache_reference to tool_result blocks that are strictly before
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3181:    // the last cache_control marker. The API requires cache_reference to
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3182:    // appear "before or on" the last cache_control — we use strict "before"
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3183:    // to avoid edge cases where cache_edits splicing shifts block indices.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3186:    // blocks reused by secondary queries that use models without cache_editing support.
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3202:              cache_reference: block.tool_use_id,
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3229:        block.cacheScope !== null && {
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3230:          cache_control: getCacheControl({
_archive/compare_code/gg-claude-code-runnable/src\services\api\claude.ts:3231:            scope: block.cacheScope,
_archive/compare_code/gg-claude-code-runnable/src\services\api\bootstrap.ts:112: * Fetch bootstrap data from the API and persist to disk cache.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\datadog.ts:173:  // Fast path: use cached result if available to avoid await overhead
_archive/compare_code/gg-claude-code-runnable/src\ink\selection.ts:890: * Uses StylePool caches so on drag the only work per cell is a Map
_archive/compare_code/gg-claude-code-runnable/src\services\claudeAiLimits.ts:441:function cacheExtraUsageDisabledReason(headers: globalThis.Headers): void {
_archive/compare_code/gg-claude-code-runnable/src\services\claudeAiLimits.ts:445:  const cached = getGlobalConfig().cachedExtraUsageDisabledReason
_archive/compare_code/gg-claude-code-runnable/src\services\claudeAiLimits.ts:446:  if (cached !== reason) {
_archive/compare_code/gg-claude-code-runnable/src\services\claudeAiLimits.ts:449:      cachedExtraUsageDisabledReason: reason,
_archive/compare_code/gg-claude-code-runnable/src\services\claudeAiLimits.ts:480:  cacheExtraUsageDisabledReason(headersToUse)
_archive/compare_code/gg-claude-code-runnable/src\services\claudeAiLimits.ts:504:      cacheExtraUsageDisabledReason(headersToUse)
_archive/compare_code/gg-claude-code-runnable/src\tools\PowerShellTool\powershellSecurity.ts:272: * certutil -urlcache: classic LOLBAS download. Only flagged with -urlcache;
_archive/compare_code/gg-claude-code-runnable/src\tools\PowerShellTool\powershellSecurity.ts:288:    // certutil / certutil.exe — only when -urlcache is present. certutil has
_archive/compare_code/gg-claude-code-runnable/src\tools\PowerShellTool\powershellSecurity.ts:290:    // certutil.exe accepts both -urlcache and /urlcache per standard Windows
_archive/compare_code/gg-claude-code-runnable/src\tools\PowerShellTool\powershellSecurity.ts:293:      const hasUrlcache = cmd.args.some(a => {
_archive/compare_code/gg-claude-code-runnable/src\tools\PowerShellTool\powershellSecurity.ts:295:        return la === '-urlcache' || la === '/urlcache'
_archive/compare_code/gg-claude-code-runnable/src\tools\PowerShellTool\powershellSecurity.ts:297:      if (hasUrlcache) {
_archive/compare_code/gg-claude-code-runnable/src\services\autoDream\autoDream.ts:71: * per-field validation since GB cache can return stale wrong-type values.
_archive/compare_code/gg-claude-code-runnable/src\services\autoDream\autoDream.ts:226:        cacheSafeParams: createCacheSafeParams(context),
_archive/compare_code/gg-claude-code-runnable/src\services\autoDream\autoDream.ts:250:        `[autoDream] completed — cache: read=${result.totalUsage.cache_read_input_tokens} created=${result.totalUsage.cache_creation_input_tokens}`,
_archive/compare_code/gg-claude-code-runnable/src\services\autoDream\autoDream.ts:253:        cache_read: result.totalUsage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\autoDream\autoDream.ts:254:        cache_created: result.totalUsage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\autoDream\autoDream.ts:317: * Per-turn cost when enabled: one GB cache read + one stat.
_archive/compare_code/gg-claude-code-runnable/src\services\diagnosticTracking.ts:56:    // TODO: Do not cache the connected mcpClient since it can change.
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\runAgent.ts:306:   * the same tool results are re-replaced (prompt cache stability). When
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\runAgent.ts:313:   * prompt cache hits. */
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\runAgent.ts:680:    // parent's API request prefix for prompt cache hits. For regular
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\runAgent.ts:721:  // Expose cache-safe params for background summarization (prompt cache sharing)
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\runAgent.ts:823:    // Clean up prompt cache tracking state for this agent
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\runAgent.ts:827:    // Release cloned file state cache memory
_archive/compare_code/gg-claude-code-runnable/src\tools\AgentTool\resumeAgent.ts:180:    // Fork resume: pass parent's system prompt (cache-identical prefix).
_archive/compare_code/gg-claude-code-runnable/src\services\compact\autoCompact.ts:244:  cacheSafeParams: CacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\autoCompact.ts:298:    // Reset cache read baseline so the post-compact drop isn't flagged as a
_archive/compare_code/gg-claude-code-runnable/src\services\compact\autoCompact.ts:300:    // BQ 2026-03-01: missing this made 20% of tengu_prompt_cache_break events
_archive/compare_code/gg-claude-code-runnable/src\services\compact\autoCompact.ts:316:      cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\apiMicrocompact.ts:79:  // When clearAllThinking is set (>1h idle = cache miss), keep only the last
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:49:import { cacheToObject } from '../../utils/fileStateCache.js'
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:390:  cacheSafeParams: CacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:431:    // 3P default: true — forked-agent path reuses main conversation's prompt cache.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:432:    // Experiment (Jan 2026) confirmed: false path is 98% cache miss, costs ~0.76% of
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:433:    // fleet cache_creation (~38B tok/day), concentrated in ephemeral envs (CCR/GHA/SDK)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:434:    // with cold GB cache and 3P providers where GB is disabled. GB gate kept as kill-switch.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:436:      'tengu_compact_cache_prefix',
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:446:    let retryCacheSafeParams = cacheSafeParams
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:457:        cacheSafeParams: retryCacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:485:      // The forked-agent path reads from cacheSafeParams.forkContextMessages,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:518:    const preCompactReadFileState = cacheToObject(context.readFileState)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:520:    // Clear the cache
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:525:    // skill_listing (~4K tokens) post-compact is pure cache_creation with
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:672:      compactionCacheReadTokens: compactionUsage?.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:674:        compactionUsage?.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:677:          (compactionUsage.cache_creation_input_tokens ?? 0) +
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:678:          (compactionUsage.cache_read_input_tokens ?? 0) +
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:697:    // Reset cache read baseline so the post-compact drop isn't flagged as a break
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:768: *   Prompt cache for kept (earlier) messages is preserved.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:770: *   Prompt cache is invalidated since the summary precedes the kept messages.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:776:  cacheSafeParams: CacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:852:    // 'up_to' prefix hits cache directly; 'from' sends all (tail wouldn't cache).
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:853:    // PTL retry breaks the cache prefix but unblocks the user (CC-1180).
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:857:        ? { ...cacheSafeParams, forkContextMessages: messagesToSummarize }
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:858:        : cacheSafeParams
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:869:        cacheSafeParams: retryCacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:919:    const preCompactReadFileState = cacheToObject(context.readFileState)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1002:      compactionCacheReadTokens: compactionUsage?.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1004:        compactionUsage?.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1142:  cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1149:  cacheSafeParams: CacheSafeParams
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1151:  // When prompt cache sharing is enabled, use forked agent to reuse the
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1152:  // main conversation's cached prefix (system prompt, tools, context messages).
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1154:  // 3P default: true — see comment at the other tengu_compact_cache_prefix read above.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1156:    'tengu_compact_cache_prefix',
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1182:        // prompt cache by sending identical cache-key params (system, tools, model,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1185:        // creating a thinking config mismatch that invalidates the cache.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1187:        // since it doesn't share cache with the main thread.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1190:          cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1214:            logEvent('tengu_compact_cache_sharing_success', {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1217:              cacheReadInputTokens: result.totalUsage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1218:              cacheCreationInputTokens:
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1219:                result.totalUsage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1220:              cacheHitRate:
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1221:                result.totalUsage.cache_read_input_tokens > 0
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1222:                  ? result.totalUsage.cache_read_input_tokens /
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1223:                    (result.totalUsage.cache_read_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1224:                      result.totalUsage.cache_creation_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1232:          `Compact cache sharing: no text in response, falling back. Response: ${jsonStringify(assistantMsg)}`,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1235:        logEvent('tengu_compact_cache_sharing_fallback', {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1242:        logEvent('tengu_compact_cache_sharing_fallback', {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\compact.ts:1250:    // Regular streaming path (fallback when cache sharing fails or is disabled)
_archive/compare_code/gg-claude-code-runnable/src\tools\PowerShellTool\readOnlyValidation.ts:610:    'get-dnsclientcache': {
_archive/compare_code/gg-claude-code-runnable/src\tools\PowerShellTool\readOnlyValidation.ts:1617:    // Note: `--cached`, `--config-env`, etc. already fail startsWith('-c') at
_archive/compare_code/gg-claude-code-runnable/src\skills\bundled\claudeApi.ts:111:**Prompt caching / optimize caching / "why is my cache hit rate low":**
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\firstPartyEventLogger.ts:41: * Uses cached value if available, updates cache in background.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\firstPartyEventLogger.ts:324:  // Uses cached value if available, refreshes in background
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\firstPartyEventLoggingExporter.ts:534:      // cache picks up the cleared flag.
_archive/compare_code/gg-claude-code-runnable/src\utils\bash\ast.ts:2114:  // `hash -p /path cmd` — poisons bash's command-lookup cache. Subsequent
_archive/compare_code/gg-claude-code-runnable/src\utils\caCerts.ts:108: * Clear the CA certificates cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\caCerts.ts:113:  getCACertificates.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\caCerts.ts:114:  logForDebugging('Cleared CA certificates cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\caCertsConfig.ts:24: * Bun caches the TLS certificate store at process boot via BoringSSL.
_archive/compare_code/gg-claude-code-runnable/src\utils\cachePaths.ts:10:// Cache directory names must remain stable across upgrades so existing cache
_archive/compare_code/gg-claude-code-runnable/src\utils\cachePaths.ts:26:  baseLogs: () => join(paths.cache, getProjectDir(getFsImplementation().cwd())),
_archive/compare_code/gg-claude-code-runnable/src\utils\cachePaths.ts:28:    join(paths.cache, getProjectDir(getFsImplementation().cwd()), 'errors'),
_archive/compare_code/gg-claude-code-runnable/src\utils\cachePaths.ts:30:    join(paths.cache, getProjectDir(getFsImplementation().cwd()), 'messages'),
_archive/compare_code/gg-claude-code-runnable/src\utils\cachePaths.ts:33:      paths.cache,
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:9: * conversation that shares the parent's prompt cache.
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:178:    // different tool list would break prompt cache sharing (tools are part of
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:179:    // the cache key — see CacheSafeParams in forkedAgent.ts).
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:372:    const cacheSafeParams = createCacheSafeParams(context)
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:417:        cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:442:        result.totalUsage.cache_creation_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:443:        result.totalUsage.cache_read_input_tokens
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:447:              (result.totalUsage.cache_read_input_tokens / totalInput) *
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:452:        `[extractMemories] finished — ${writtenPaths.length} files written, cache: read=${result.totalUsage.cache_read_input_tokens} create=${result.totalUsage.cache_creation_input_tokens} input=${result.totalUsage.input_tokens} (${hitPct}% hit)`,
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:476:        cache_read_input_tokens: result.totalUsage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:477:        cache_creation_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\services\extractMemories\extractMemories.ts:478:          result.totalUsage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:162: * to bypass remote eval and disk cache. Useful for eval harnesses that need to
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:208: * runtime, and getGlobalConfig() is already memory-cached (pointer-chase)
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:217:    // main.tsx startup path). Same degrade as the disk-cache fallback below.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:224: * (not including overrides). In-memory payload first, disk cache fallback —
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:231:  return getGlobalConfig().cachedGrowthBookFeatures ?? {}
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:318: * local caches. Called after both initial client.init() and after
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:381:  // reliably. So we cache values ourselves and use them in getFeatureValueInternal.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:410:  if (isEqual(config.cachedGrowthBookFeatures, fresh)) {
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:415:    cachedGrowthBookFeatures: fresh,
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:532:      cacheKeyAttributes: ['id', 'organizationUUID'],
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:549:      // No auth available yet — skip HTTP init, rely on disk-cached values.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:668: * @internal Used by both deprecated and cached functions.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:694:  // Use cached remote eval values if available (workaround for SDK bug)
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:727: * Get a feature value from disk cache immediately. Pure read — disk is
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:732: * The value may be stale if the cache was written by a previous process.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:768:  // Fall back to disk cache (survives across process restarts)
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:770:    const cached = getGlobalConfig().cachedGrowthBookFeatures?.[feature]
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:771:    return cached !== undefined ? (cached as T) : defaultValue
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:778: * @deprecated Disk cache is now synced on every successful payload load
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:792: * Check a Statsig feature gate value via GrowthBook, with fallback to Statsig cache.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:797: * - Checks GrowthBook disk cache first
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:798: * - Falls back to Statsig's cachedStatsigGates during migration
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:799: * - The value may be stale if the cache hasn't been updated recently
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:828:  // Return cached value immediately from disk
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:829:  // First check GrowthBook cache, then fall back to Statsig cache for migration
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:831:  const gbCached = config.cachedGrowthBookFeatures?.[gate]
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:835:  // Fallback to Statsig cache for migration period
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:836:  return config.cachedStatsigGates?.[gate] ?? false
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:846: * - Otherwise, returns cached value immediately (Statsig cache first, then GrowthBook)
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:848: * Statsig cache is checked first as a safety measure for security-related checks:
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:849: * if the Statsig cache indicates the gate is enabled, we honor it.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:874:  // Check Statsig cache first - it may have correct value from previous logged-in session
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:876:  const statsigCached = config.cachedStatsigGates?.[gate]
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:881:  // Then check GrowthBook cache
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:882:  const gbCached = config.cachedGrowthBookFeatures?.[gate]
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:887:  // No cache - return false (don't block on init for uncached gates)
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:894: * Fast path: if the disk cache already says `true`, return it immediately.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:921:  // Fast path: disk cache already says true — trust it
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:922:  const cached = getGlobalConfig().cachedGrowthBookFeatures?.[gate]
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:923:  if (cached === true) {
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:957:    // (falls to disk cache). If re-init succeeds, they'll notify again with
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:1006:  getGrowthBookClient.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:1007:  initializeGrowthBook.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\growthbook.ts:1144: * Get a dynamic config value from disk cache immediately. Pure read — see
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:353:  // XAA servers can silently re-auth via cached id_token even without an
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:579:  // so the next performMCPOAuthFlow can use cached scope instead of
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:651: * 1. Acquire an id_token from the IdP (cached in keychain by issuer; if
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:719:  // Acquire id_token (cached or via one OIDC browser pop at the IdP).
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:720:  // Peek the cache first so we can report idTokenCacheHit in analytics before
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:767:      // If the IdP says the id_token is bad, drop it from the cache so the
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:776:            'XAA: cleared cached id_token after token-exchange failure',
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:858:  // If the IdP id_token isn't cached, this pops the browser once at the IdP
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:860:  // the cache and are silent. Tokens land in the same keychain slot, so the
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:903:  // Check for cached step-up scope and resource metadata URL before clearing
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:908:  const cachedEntry = storage.read()?.mcpOAuth?.[serverKey]
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:909:  const cachedStepUpScope = cachedEntry?.stepUpScope
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:910:  const cachedResourceMetadataUrl =
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:911:    cachedEntry?.discoveryState?.resourceMetadataUrl
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:915:  // but we already read the cached values above.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:918:  // Use cached step-up scope and resource metadata URL if available.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:919:  // The transport-attached auth provider caches these when it receives a
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:922:  if (cachedResourceMetadataUrl) {
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:924:      resourceMetadataUrl = new URL(cachedResourceMetadataUrl)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:928:        `Invalid cached resourceMetadataUrl: ${cachedResourceMetadataUrl}`,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:933:    scope: cachedStepUpScope,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1542:    // are picked up via the keychain cache TTL (see macOsKeychainStorage.ts).
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1543:    // In-process writes already invalidate the cache via storage.update().
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1545:    // _commonHeaders on every request, and forcing a cache miss would trigger
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1554:    // XAA: a cached id_token plays the same UX role as a refresh_token — run
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1573:    // anything — fires xaaRefresh. If id_token is cached, SDK short-circuits
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1574:    // there and never reaches the write. If id_token isn't cached, xaaRefresh
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1582:    // isn't cached (or settings.xaaIdp is gone) → we fall through to the
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1612:      // Fall through. Either id_token isn't cached (xaaRefresh returned
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1734:   * XAA silent refresh: cached id_token → Layer-2 exchange → new access_token.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1737:   * Returns undefined if the id_token is gone from cache — caller treats this
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1740:   * On exchange failure, clears the id_token cache so the next interactive
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1741:   * auth does a fresh IdP login (the cached id_token is likely stale/revoked).
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1759:        'XAA: id_token not cached, needs interactive re-auth',
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1776:    // Discover IdP token endpoint. Could cache (fetchCache.ts already
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:1777:    // caches /.well-known/ requests), but OIDC metadata is cheap + idempotent.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2015:    // `cachedState.authorizationServerMetadata ?? await discover...`.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2042:    const cached = data?.mcpOAuth?.[serverKey]?.discoveryState
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2043:    if (cached?.authorizationServerUrl) {
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2046:        `Returning cached discovery state (authServer: ${cached.authorizationServerUrl})`,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2050:        authorizationServerUrl: cached.authorizationServerUrl,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2051:        resourceMetadataUrl: cached.resourceMetadataUrl,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2053:          cached.resourceMetadata as OAuthDiscoveryState['resourceMetadata'],
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2055:          cached.authorizationServerMetadata as OAuthDiscoveryState['authorizationServerMetadata'],
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2215:        // Reuse cached metadata from the initial OAuth flow if available,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2218:        // 1. In-memory cache (same-session refreshes)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2224:          const cached = await this.discoveryState()
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2225:          if (cached?.authorizationServerMetadata) {
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2230:            metadata = cached.authorizationServerMetadata
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2231:          } else if (cached?.authorizationServerUrl) {
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2234:              `Re-discovering metadata from persisted auth server URL: ${cached.authorizationServerUrl}`,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\auth.ts:2237:              cached.authorizationServerUrl,
_archive/compare_code/gg-claude-code-runnable/src\services\lsp\LSPDiagnosticRegistry.ts:2:import { LRUCache } from 'lru-cache'
_archive/compare_code/gg-claude-code-runnable/src\services\lsp\manager.ts:212: * successful init. Called from refreshActivePlugins() after plugin caches
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\channelNotification.ts:125: * avoid double-reading getSettingsForSource (uncached).
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\types.ts:23:  restrictions?: PolicyLimitsResponse['restrictions'] | null // null means 304 Not Modified (cache is valid)
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:71:// Session-level cache for policy restrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:117: * Get the path to the policy limits cache file
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:268:  cachedChecksum?: string,
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:273:    lastResult = await fetchPolicyLimits(cachedChecksum)
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:301:  cachedChecksum?: string,
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:321:    if (cachedChecksum) {
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:322:      headers['If-None-Match'] = `"${cachedChecksum}"`
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:332:    // Handle 304 Not Modified - cached version is still valid
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:334:      logForDebugging('Policy limits: Using cached restrictions (304)')
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:337:        restrictions: null, // Signal that cache is valid
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:338:        etag: cachedChecksum,
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:389: * Load restrictions from cache file
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:408: * Save restrictions to cache file
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:430: * Fails open - returns null if fetch fails and no cache exists
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:439:  const cachedRestrictions = loadCachedRestrictions()
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:441:  const cachedChecksum = cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:442:    ? computeChecksum(cachedRestrictions)
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:446:    const result = await fetchWithRetry(cachedChecksum)
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:449:      if (cachedRestrictions) {
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:450:        logForDebugging('Policy limits: Using stale cache after fetch failure')
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:451:        sessionCache = cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:452:        return cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:458:    if (result.restrictions === null && cachedRestrictions) {
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:460:      sessionCache = cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:461:      return cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:474:    // Empty restrictions (404 response) - delete cached file if it exists
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:478:      logForDebugging('Policy limits: Deleted cached file (404 response)')
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:482:          `Policy limits: Failed to delete cached file - ${e.message}`,
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:488:    if (cachedRestrictions) {
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:489:      logForDebugging('Policy limits: Using stale cache after error')
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:490:      sessionCache = cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:491:      return cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:499: * and the policy cache is unavailable. Without this, a cache miss or network
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:508: * essential-traffic-only mode is active and the cache is unavailable.
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:529: * Get restrictions synchronously from session cache or file
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:542:  const cachedRestrictions = loadCachedRestrictions()
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:543:  if (cachedRestrictions) {
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:544:    sessionCache = cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\policyLimits\index.ts:545:    return cachedRestrictions
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:24:} from '../../utils/plugins/cacheUtils.js'
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:50:  cachePlugin,
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:565: * cached yet, the next load will cache it.
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:640:    // was cached but never declared.
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:710:  // before we write settings and clear the memoized plugin cache.
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:821: * 4. If version differs from currently installed, copies to new versioned cache directory
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:893: * Perform the actual plugin update: fetch source, calculate version, copy to cache, update disk.
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:924:    const cacheResult = await cachePlugin(entry.source, {
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:927:    sourcePath = cacheResult.path
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:929:    gitCommitSha = cacheResult.gitCommitSha
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:932:    // cachePlugin captured the commit SHA before discarding the ephemeral
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:938:      cacheResult.manifest,
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:939:      cacheResult.path,
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:941:      cacheResult.gitCommitSha,
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:1012:    // Check if this version already exists in cache
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\pluginOperations.ts:1033:    // Copy to versioned cache (returns actual path, which may be .zip)
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\PluginInstallationManager.ts:57: *   from the initial cache-only load on fresh homespace/cleared cache)
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\PluginInstallationManager.ts:77:    // plugin load is fast (cache hit or local copy); marketplace clone is the
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\PluginInstallationManager.ts:137:      // "Plugin not found in marketplace" errors from the initial cache-only
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\PluginInstallationManager.ts:138:      // load (e.g., fresh homespace where marketplace cache was empty).
_archive/compare_code/gg-claude-code-runnable/src\services\plugins\PluginInstallationManager.ts:139:      // refreshActivePlugins clears all caches, reloads plugins, and bumps
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\speculation.ts:407:  cacheSafeParams?: CacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\speculation.ts:459:      cacheSafeParams: cacheSafeParams ?? createCacheSafeParams(context),
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:129:  cacheSafeParams: CacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:152:  const cacheReason = getParentCacheSuppressReason(lastAssistantMessage)
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:153:  if (cacheReason) {
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:154:    logSuggestionSuppressed(cacheReason, undefined, undefined, source)
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:169:    cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:191:  const cacheSafeParams = createCacheSafeParams(context)
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:198:      cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:220:        cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:248:  const cacheWriteTokens = usage.cache_creation_input_tokens ?? 0
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:249:  // The fork re-processes the parent's output (never cached) plus its own prompt.
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:252:  return inputTokens + cacheWriteTokens + outputTokens >
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:254:    ? 'cache_cold'
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:297:  cacheSafeParams: CacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:301:  // Deny tools via callback, NOT by passing tools:[] - that busts cache (0% hit)
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:309:  // The fork piggybacks on the main thread's prompt cache by sending identical
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:310:  // cache-key params. The billing cache key includes more than just
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:313:  // busts cache. PR #18143 tried effort:'low' and caused a 45x spike in cache
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:317:  //   - skipCacheWrite (controls cache_control markers, not the cache key)
_archive/compare_code/gg-claude-code-runnable/src\services\PromptSuggestion\promptSuggestion.ts:321:    cacheSafeParams, // Don't override tools/thinking settings - busts cache
_archive/compare_code/gg-claude-code-runnable/src\skills\bundled\simplify.ts:28:1. **Redundant state**: state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls
_archive/compare_code/gg-claude-code-runnable/src\hooks\useSettingsChange.ts:14:      // cleared the cache, re-read from disk, then the next cleared again.
_archive/compare_code/gg-claude-code-runnable/src\utils\bash\commands.ts:516: * Clear both command prefix caches. Called on /clear to release memory.
_archive/compare_code/gg-claude-code-runnable/src\utils\bash\commands.ts:519:  getCommandPrefix.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\utils\bash\commands.ts:520:  getCommandSubcommandPrefix.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemoryUtils.ts:20:   * Uses the same token counting as autocompact (input + output + cache tokens)
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:67:// These functions return cached values from disk immediately without blocking
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:78: * Uses cached gate value - returns immediately without blocking.
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:85: * Get session memory config from cache.
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:214:  // Drop any cached entry so FileReadTool's dedup doesn't return a
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:238: * Uses cached config values - non-blocking.
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:241:  // Load config from cache (non-blocking, may be stale)
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:283:  // Check gate lazily when hook runs (cached, non-blocking)
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:302:  // Create isolated context for setup to avoid polluting parent's cache
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:320:    cacheSafeParams: createCacheSafeParams(context),
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:335:    cache_read_input_tokens: usage?.cache_read_input_tokens ?? undefined,
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:336:    cache_creation_input_tokens:
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:337:      usage?.cache_creation_input_tokens ?? undefined,
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:397:    // Create isolated context for setup to avoid polluting parent's cache
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:410:    // Get system prompt for cache-safe params
_archive/compare_code/gg-claude-code-runnable/src\services\SessionMemory\sessionMemory.ts:422:      cacheSafeParams: {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\timeBasedMCConfig.ts:7: * assistant message exceeds a threshold — the server-side prompt cache has
_archive/compare_code/gg-claude-code-runnable/src\services\compact\timeBasedMCConfig.ts:22:   *  60 is the safe choice: the server's 1h cache TTL is guaranteed expired
_archive/compare_code/gg-claude-code-runnable/src\services\compact\sessionMemoryCompact.ts:401: * Uses cached gate values to avoid blocking on Statsig initialization
_archive/compare_code/gg-claude-code-runnable/src\services\compact\prompt.ts:12:// Aggressive no-tools preamble. The cache-sharing fork path inherits the
_archive/compare_code/gg-claude-code-runnable/src\services\compact\prompt.ts:13:// parent's full tool set (required for cache-key match), and on Sonnet 4.6+
_archive/compare_code/gg-claude-code-runnable/src\services\compact\prompt.ts:206:// 'up_to': model sees only the summarized prefix (cache hit). Summary will
_archive/compare_code/gg-claude-code-runnable/src\services\compact\postCompactCleanup.ts:13: * Run cleanup of caches and tracking state after compaction.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\postCompactCleanup.ts:26: * getUserContext cache); resetting those when a SUBAGENT compacts
_archive/compare_code/gg-claude-code-runnable/src\services\compact\postCompactCleanup.ts:34:  // (context-collapse, memory file cache) for main-thread compacts.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\postCompactCleanup.ts:53:    // getMemoryFiles(). If only the inner getMemoryFiles cache is cleared,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\postCompactCleanup.ts:54:    // the next turn hits the getUserContext cache and never reaches
_archive/compare_code/gg-claude-code-runnable/src\services\compact\postCompactCleanup.ts:59:    getUserContext.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\services\compact\postCompactCleanup.ts:66:  // skill_listing (~4K tokens) post-compact is pure cache_creation. The
_archive/compare_code/gg-claude-code-runnable/src\services\compact\postCompactCleanup.ts:69:  // cacheUtils resets. See compactConversation() for full rationale.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:54:// Lazy-initialized cached MC module and state to avoid importing in external builds.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:56:let cachedMCModule: typeof import('./cachedMicrocompact.js') | null = null
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:57:let cachedMCState: import('./cachedMicrocompact.js').CachedMCState | null = null
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:59:  | import('./cachedMicrocompact.js').CacheEditsBlock
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:63:  typeof import('./cachedMicrocompact.js')
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:65:  if (!cachedMCModule) {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:66:    cachedMCModule = await import('./cachedMicrocompact.js')
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:68:  return cachedMCModule
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:71:function ensureCachedMCState(): import('./cachedMicrocompact.js').CachedMCState {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:72:  if (!cachedMCState && cachedMCModule) {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:73:    cachedMCState = cachedMCModule.createCachedMCState()
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:75:  if (!cachedMCState) {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:77:      'cachedMCState not initialized — getCachedMCModule() must be called first',
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:80:  return cachedMCState
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:84: * Get new pending cache edits to be included in the next API request.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:89:  | import('./cachedMicrocompact.js').CacheEditsBlock
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:97: * Get all previously-pinned cache edits that must be re-sent at their
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:98: * original positions for cache hits.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:100:export function getPinnedCacheEdits(): import('./cachedMicrocompact.js').PinnedCacheEdits[] {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:101:  if (!cachedMCState) {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:104:  return cachedMCState.pinnedEdits
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:108: * Pin a new cache_edits block to a specific user message position.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:113:  block: import('./cachedMicrocompact.js').CacheEditsBlock,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:115:  if (cachedMCState) {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:116:    cachedMCState.pinnedEdits.push({ userMessageIndex, block })
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:125:  if (cachedMCState && cachedMCModule) {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:126:    cachedMCModule.markToolsSentToAPI(cachedMCState)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:131:  if (cachedMCState && cachedMCModule) {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:132:    cachedMCModule.resetCachedMCState(cachedMCState)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:210:  // Baseline cumulative cache_deleted_input_tokens from the previous API response,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:247:// cached-MC `=== 'repl_main_thread'` check was a latent bug — users with a
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:248:// non-default output style were silently excluded from cached MC.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:262:  // last assistant message exceeds the threshold, the server cache has expired
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:265:  // Cached MC (cache-editing) is skipped when this fires: editing assumes a
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:266:  // warm cache, and we just established it's cold.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:272:  // Only run cached MC for the main thread to prevent forked agents
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:274:  // tool_results in the global cachedMCState, which would cause the main
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:284:      return await cachedMicrocompactPath(messages, querySource)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:288:  // Legacy microcompact path removed — tengu_cache_plum_violet is always true.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:289:  // For contexts where cached microcompact is not available (external builds,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:296: * Cached microcompact path - uses cache editing API to remove tool results
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:297: * without invalidating the cached prefix.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:300: * - Does NOT modify local message content (cache_reference and cache_edits are added at API layer)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:303: * - Tracks tool results and queues cache edits for the API layer
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:305:async function cachedMicrocompactPath(
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:335:    // Create and queue the cache_edits block for the API layer
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:336:    const cacheEdits = mod.createCacheEditsBlock(state, toolsToDelete)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:337:    if (cacheEdits) {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:338:      pendingCacheEdits = cacheEdits
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:346:    logEvent('tengu_cached_microcompact', {
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:361:    // Notify cache break detection that cache reads will legitimately drop
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:369:    // Return messages unchanged - cache_reference and cache_edits are added at API layer
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:371:    // actual cache_deleted_input_tokens from the API instead of client-side estimates
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:372:    // Capture the baseline cumulative cache_deleted_input_tokens from the last
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:382:          )?.cache_deleted_input_tokens ?? 0)
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:409: * Unlike cached MC, this mutates message content directly. The cache is cold,
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:410: * so there's no cached prefix to preserve via cache_edits.
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:428:  // undefined as main-thread (for cached-MC backward-compat), but several
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:514:  // cache by changing prompt content. If cached-MC runs next turn with the
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:515:  // stale state, it would try to cache_edit tools whose server-side entries
_archive/compare_code/gg-claude-code-runnable/src\services\compact\microCompact.ts:518:  // We just changed the prompt content — the next response's cache read will
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\sinkKillswitch.ts:23:  // cached JSON null leaks through instead of falling back to {}.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\sink.ts:27: * Falls back to cached value from previous session if not yet initialized.
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\sink.ts:37:  // Fallback to cached value from previous session
_archive/compare_code/gg-claude-code-runnable/src\services\analytics\sink.ts:91: * Updates gate values from server. Early events use cached values from previous
_archive/compare_code/gg-claude-code-runnable/src\hooks\useSkillsChange.ts:15: * 1. Skill file changes (watcher) — full cache clear + disk re-scan, since
_archive/compare_code/gg-claude-code-runnable/src\hooks\useSkillsChange.ts:19: *    reads a flag that isn't in the disk cache yet on first session after
_archive/compare_code/gg-claude-code-runnable/src\hooks\useSkillsChange.ts:31:      // Clear all command caches to ensure fresh load
_archive/compare_code/gg-claude-code-runnable/src\utils\bash\ParsedCommand.ts:292:// Single-entry cache: legacy callers (bashCommandIsSafeAsync,
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:4: * The cache state itself lives in syncCacheState.ts (a leaf, no auth import).
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:25:let cached: boolean | undefined
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:28:  cached = undefined
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:50:  if (cached !== undefined) return cached
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:54:    return (cached = setEligibility(false))
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:59:    return (cached = setEligibility(false))
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:67:    return (cached = setEligibility(false))
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:84:    return (cached = setEligibility(true))
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:93:    return (cached = setEligibility(true))
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:105:      return (cached = setEligibility(true))
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCache.ts:111:  return (cached = setEligibility(false))
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:210:  cachedChecksum?: string,
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:215:    lastResult = await fetchRemoteManagedSettings(cachedChecksum)
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:246: * Optionally pass a cached checksum for ETag-based caching
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:249:  cachedChecksum?: string,
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:253:    // This prevents 401 errors from stale cached tokens
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:274:    if (cachedChecksum) {
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:275:      headers['If-None-Match'] = `"${cachedChecksum}"`
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:287:    // Handle 304 Not Modified - cached version is still valid
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:289:      logForDebugging('Remote settings: Using cached settings (304)')
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:292:        settings: null, // Signal that cache is valid
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:293:        checksum: cachedChecksum,
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:298:    // Return empty object (not null) so callers don't fall back to cached settings.
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:395:  // Clear session cache
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:413: * Fails open - returns null if fetch fails and no cache exists
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:420:  // Load cached settings from file
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:421:  const cachedSettings = getRemoteManagedSettingsSyncFromCache()
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:423:  // Compute checksum locally from cached settings for HTTP caching validation
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:424:  const cachedChecksum = cachedSettings
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:425:    ? computeChecksumFromSettings(cachedSettings)
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:430:    const result = await fetchWithRetry(cachedChecksum)
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:434:      if (cachedSettings) {
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:436:          'Remote settings: Using stale cache after fetch failure',
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:438:        setSessionCache(cachedSettings)
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:439:        return cachedSettings
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:441:      // No cache available - fail open, continue without remote settings
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:445:    // Handle 304 Not Modified - cached settings are still valid
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:446:    if (result.settings === null && cachedSettings) {
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:448:      setSessionCache(cachedSettings)
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:449:      return cachedSettings
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:459:        cachedSettings,
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:463:        // User rejected - don't apply settings, return cached or null
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:465:          'Remote settings: User rejected new settings, using cached settings',
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:467:        return cachedSettings
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:476:    // Empty settings (404 response) - delete cached file if it exists
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:482:      logForDebugging('Remote settings: Deleted cached file (404 response)')
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:487:          `Remote settings: Failed to delete cached file - ${e instanceof Error ? e.message : 'unknown error'}`,
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:494:    if (cachedSettings) {
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:495:      logForDebugging('Remote settings: Using stale cache after error')
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:496:      setSessionCache(cachedSettings)
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:497:      return cachedSettings
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:500:    // No cache available - fail open, continue without remote settings
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:524:  // Cache-first: if we have cached settings on disk, apply them and unblock
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:528:  // the session cache internally — no need to call setSessionCache here.
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:542:    // Trigger hot-reload if settings were loaded (new or from cache).
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:543:    // notifyChange resets the settings cache internally before iterating
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:563:  // Clear caches first
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:576:  // Notify listeners. notifyChange resets the settings cache internally;
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\index.ts:589:  // Get current cached settings for comparison
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:2: * Leaf state module for the remote-managed-settings sync cache.
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:11: * reads the cache from here. syncCache.ts keeps isRemoteManagedSettingsEligible
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:21: * subsequent read hits the cached bool instead of re-running the auth chain.
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:73:  const cachedSettings = loadSettings()
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:74:  if (cachedSettings) {
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:75:    sessionCache = cachedSettings
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:77:    // getSettings_DEPRECATED() result cached before this moment is missing
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:83:    // cache is still null (setSessionSettingsCache runs at :732 after
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:91:    // cache was already poisoned. See managedSettingsHeadless.int.test.ts.
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\syncCacheState.ts:93:    return cachedSettings
_archive/compare_code/gg-claude-code-runnable/src\services\tokenEstimation.ts:321:  const cacheCreationTokens = usage.cache_creation_input_tokens || 0
_archive/compare_code/gg-claude-code-runnable/src\services\tokenEstimation.ts:322:  const cacheReadTokens = usage.cache_read_input_tokens || 0
_archive/compare_code/gg-claude-code-runnable/src\services\tokenEstimation.ts:324:  return inputTokens + cacheCreationTokens + cacheReadTokens
_archive/compare_code/gg-claude-code-runnable/src\services\remoteManagedSettings\types.ts:27:  settings?: SettingsJson | null // null means 304 Not Modified (cache is valid)
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:58:  // Fetch cached fixture
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:60:    const cached = jsonParse(
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:63:    return cached
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:117:  // Fetch cached fixture
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:119:    const cached = jsonParse(
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:122:    cached.output.forEach(addCachedCostToTotalSessionCost)
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:123:    return cached.output.map((message, index) =>
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:366:  // Record messages (or fetch from cache)
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:367:  const cachedBuffer = await withVCR(messages, async () => {
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:374:  if (cachedBuffer.length > 0) {
_archive/compare_code/gg-claude-code-runnable/src\services\vcr.ts:375:    yield* cachedBuffer
_archive/compare_code/gg-claude-code-runnable/src\services\oauth\client.ts:198:    // the re-login path writes cached ?? wiped ?? null = cached; and if secure
_archive/compare_code/gg-claude-code-runnable/src\services\oauth\client.ts:448: * Populate the OAuth account info if it has not already been cached in config.
_archive/compare_code/gg-claude-code-runnable/src\services\tips\tipRegistry.ts:23:import { cacheKeys } from '../../utils/fileStateCache.js'
_archive/compare_code/gg-claude-code-runnable/src\services\tips\tipRegistry.ts:87:    const readFiles = cacheKeys(context.readFileState)
_archive/compare_code/gg-claude-code-runnable/src\services\tools\toolExecution.ts:203: * cache hit — the host knows, we can't tell from {behavior:'allow'} alone).
_archive/compare_code/gg-claude-code-runnable/src\services\tools\toolExecution.ts:1290:    // Map the tool result to API format once and cache it. This block is reused
_archive/compare_code/gg-claude-code-runnable/src\services\settingsSync\index.ts:117:/** Test-only: clear the cached download promise between tests. */
_archive/compare_code/gg-claude-code-runnable/src\services\settingsSync\index.ts:138: * Force a fresh download, bypassing the cached startup promise.
_archive/compare_code/gg-claude-code-runnable/src\services\settingsSync\index.ts:141: * CLI are picked up before the plugin-cache sweep.
_archive/compare_code/gg-claude-code-runnable/src\services\settingsSync\index.ts:484: * After writing, invalidates relevant caches:
_archive/compare_code/gg-claude-code-runnable/src\services\settingsSync\index.ts:570:  // Invalidate caches so subsequent reads pick up new content
_archive/compare_code/gg-claude-code-runnable/src\ink\widest-line.ts:1:import { lineWidth } from './line-width-cache.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:349: * Get cached value of whether Chrome extension is installed. Returns
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:350: * from disk cache immediately, updates cache in background.
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:353: * access is not acceptable. The value may be stale if the cache hasn't
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:357: * filesystem scan is not cached, because it may come from a machine that
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:363:  // Update cache in background without blocking
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:372:    if (config.cachedChromeExtensionInstalled !== isInstalled) {
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:375:        cachedChromeExtensionInstalled: isInstalled,
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:380:  // Return cached value immediately from disk
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:381:  const cached = getGlobalConfig().cachedChromeExtensionInstalled
_archive/compare_code/gg-claude-code-runnable/src\utils\claudeInChrome\setup.ts:382:  return cached ?? false
_archive/compare_code/gg-claude-code-runnable/src\ink\termio\osc.ts:191:      // First call: probe wl-copy (Wayland) then xclip/xsel (X11), cache winner.
_archive/compare_code/gg-claude-code-runnable/src\services\teamMemorySync\index.ts:680: * getMemoryFiles cache or trigger watcher events.
_archive/compare_code/gg-claude-code-runnable/src\services\teamMemorySync\index.ts:1048:      // max_entries (anthropic/anthropic#293258), cache it so the next push
_archive/compare_code/gg-claude-code-runnable/src\services\teamMemorySync\index.ts:1159:  // 1. Pull remote → local (skip ETag cache for full sync)
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:62:import { cacheKeys, type FileStateCache } from './fileStateCache.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:238:  // so callers can cache a `isPartialView` readFileState entry — presence in
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:239:  // cache provides dedup + change detection, but Edit/Write still require an
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1049:    // The one-shot flag is consumed on every !forceIncludeExternal cache miss
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1052:    // followed by a direct .cache.clear() would spuriously fire with a stale
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1090:// compaction clears the cache, so the InstructionsLoaded hook reports the
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1095:// Whether the InstructionsLoaded hook should fire on the next cache miss.
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1097:// by resetGetMemoryFilesCache(). Callers that only need cache invalidation
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1111: * Clears the getMemoryFiles memoize cache
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1114: * Use this for cache invalidation that is purely for correctness (e.g.
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1120:  // ?.cache because tests spyOn this, which replaces the memoize wrapper.
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1121:  getMemoryFiles.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\claudemd.ts:1472:  for (const filePath of cacheKeys(readFileState)) {
_archive/compare_code/gg-claude-code-runnable/src\services\teamMemorySync\secretScanner.ts:226:// Lazily compiled pattern cache — compile once on first scan.
_archive/compare_code/gg-claude-code-runnable/src\hooks\useTasksV2.ts:22: * and cached task list. Multiple hook instances (REPL, Spinner,
_archive/compare_code/gg-claude-code-runnable/src\hooks\useTasksV2.ts:183:   * the last subscriber unsubscribes. Preserves #tasks/#hidden cache so a
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\claudeai.ts:137: * Clears the memoized cache for fetchClaudeAIMcpConfigsIfEligible.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\claudeai.ts:141:  fetchClaudeAIMcpConfigsIfEligible.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\claudeai.ts:142:  // Also clear the auth cache so freshly-authorized servers get re-connected
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:5:import { CACHE_PATHS } from './cachePaths.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:434: * Clean up old npm cache entries for Anthropic packages.
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:439:  const markerPath = join(getClaudeConfigHomeDir(), '.npm-cache-cleanup')
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:444:      logForDebugging('npm cache cleanup: skipping, ran recently')
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:454:    logForDebugging('npm cache cleanup: skipping, lock held')
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:458:  logForDebugging('npm cache cleanup: starting')
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:460:  const npmCachePath = join(homedir(), '.npm', '_cacache')
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:466:    const cacache = await import('cacache')
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:470:    // Previous implementation used cacache.verify() which does a full
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:471:    // integrity check + GC of the ENTIRE cache — O(all content blobs).
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:472:    // On large caches this took 60+ seconds and blocked the event loop.
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:473:    const stream = cacache.ls.stream(npmCachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:508:      keysToRemove.map(key => cacache.rm.entry(npmCachePath, key)),
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:516:        `npm cache cleanup: Removed ${keysToRemove.length} old @anthropic-ai entries in ${durationMs}ms`,
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:519:      logForDebugging(`npm cache cleanup: completed in ${durationMs}ms`)
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:521:    logEvent('tengu_npm_cache_cleanup', {
_archive/compare_code/gg-claude-code-runnable/src\utils\cleanup.ts:528:    logEvent('tengu_npm_cache_cleanup', {
_archive/compare_code/gg-claude-code-runnable/src\services\teamMemorySync\types.ts:147:   * team_memory_too_many_entries. Lets the caller cache the effective
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:162: * Thrown when an MCP session has expired and the connection cache has been cleared.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:262:  return join(getClaudeConfigHomeDir(), 'mcp-needs-auth-cache.json')
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:268:// lodash memoize because we need to null out the cache, not delete by key.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:281:  const cache = await getMcpAuthCache()
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:282:  const entry = cache[serverId]
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:289:// Serialize cache writes through a promise chain to prevent concurrent
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:296:      const cache = await getMcpAuthCache()
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:297:      cache[serverId] = { timestamp: Date.now() }
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:298:      const cachePath = getMcpAuthCachePath()
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:299:      await mkdir(dirname(cachePath), { recursive: true })
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:300:      await writeFile(cachePath, jsonStringify(cache))
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:301:      // Invalidate the read cache so subsequent reads see the new entry.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:307:      // Best-effort cache write
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:337: * emits tengu_mcp_server_needs_auth, caches the needs-auth entry, and returns
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:368: * memoize-cache staleness and clock drift. Without the same here, a single
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:370: * 15-min needs-auth cache.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:386:      // connector's handleOAuth401Error clears the memoize cache, so we'd read
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:576: * Generates the cache key for a server connection
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1237:      // handler below (which clears the memo cache so the next call reconnects).
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1238:      // Calling client.onclose?.() directly would only clear the cache — pending
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1383:        // Clear the memoization cache so next operation reconnects
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1386:        // Also clear fetch caches (keyed by server name). Reconnection
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1389:        fetchToolsForClient.cache.delete(name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1390:        fetchResourcesForClient.cache.delete(name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1391:        fetchCommandsForClient.cache.delete(name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1393:          fetchMcpSkillsForClient!.cache.delete(name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1396:        connectToServer.cache.delete(key)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1397:        logMCPDebug(name, `Cleared connection cache for reconnection`)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1644: * Clears the memoize cache for a specific server
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1664:  // Clear from cache (both connection and fetch caches so reconnect
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1666:  connectToServer.cache.delete(key)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1667:  fetchToolsForClient.cache.delete(name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1668:  fetchResourcesForClient.cache.delete(name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1669:  fetchCommandsForClient.cache.delete(name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1671:    fetchMcpSkillsForClient!.cache.delete(name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1677: * For most server types, uses the memoization cache if available, or reconnects
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1678: * if the cache was cleared (e.g., after onclose). This ensures tool/resource
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1724:// Max cache size for fetch* caches. Keyed by server name (stable across
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:1911:                  // Session expired — the connection cache has been
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:2147:    // Invalidate the keychain cache so we read fresh credentials from disk.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:2151:    // use stale cached data and never notice the tokens were removed.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:2315:        logMCPDebug(name, `Skipping connection (cached needs-auth)`)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:2406:// (connectToServer, fetch*ForClient) is already cached. Memoizing here by
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:3215:      // In both cases, clear the connection cache so the next tool call
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\client.ts:3226:          `MCP session expired during tool call (${isSessionExpired ? '404/-32001' : 'connection closed'}), clearing connection cache for re-initialization`,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\config.ts:1268:  // with loadAllPluginsCacheOnly() inside. Memoized — the awaited call below is a cache hit.
_archive/compare_code/gg-claude-code-runnable/src\utils\bash\ShellSnapshot.ts:148: * - Read deny rules / plugin cache exclusions: require toolPermissionContext
_archive/compare_code/gg-claude-code-runnable/src\utils\cliHighlight.ts:17:// the module cache, so the second import() is a cache hit — no extra bytes
_archive/compare_code/gg-claude-code-runnable/src\utils\cliHighlight.ts:26:    // cache hit — cli-highlight already loaded highlight.js
_archive/compare_code/gg-claude-code-runnable/src\hooks\useTurnDiffs.ts:101:  const cache = useRef<TurnDiffCache>({
_archive/compare_code/gg-claude-code-runnable/src\hooks\useTurnDiffs.ts:109:    const c = cache.current
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:70:   * item's root Box; after Yoga layout, the computed height is cached.
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:146:   * Terminal column count. On change, cached heights are stale (text
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:149:   * uncached item → PESSIMISTIC_HEIGHT=1 → walk 190 to reach
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:268:  // GC stale cache entries (compaction, /clear, screenToggleId bump). Only
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:287:  // Offsets cached across renders, invalidated by offsetVersion ref bump.
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:352:      // unmeasured territory. Once heights are cached (next render),
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:359:      //   (b) K is mounted AND its height is cached. offsets[start+1] uses
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:362:      // The unsafe case — K is mounted but uncached — is the one-render
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:582:  // when the tail item is STREAMING its cached height lags its real height by
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:606:  // MessageRow rendered null" (permanent, cache it): getComputedWidth() > 0
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:609:  // 0, the item is genuinely empty — cache 0 so the start-advance gate
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVirtualScroll.ts:698:      // offsetsRef.current holds latest cached offsets (event handlers run
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVoice.ts:611:        // Voice module is loading (async import resolves from cache as a
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVoice.ts:756:      // Intl failed — omitted from the payload, no retry cost (cached).
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVoiceEnabled.ts:12: * ~180ms total in profile v5 when token refresh cleared the cache mid-session).
_archive/compare_code/gg-claude-code-runnable/src\hooks\useVoiceEnabled.ts:13: * GB is a cheap cached-map lookup and stays outside the memo so a mid-session
_archive/compare_code/gg-claude-code-runnable/src\utils\commitAttribution.ts:95: * Synchronously return the cached repo classification.
_archive/compare_code/gg-claude-code-runnable/src\utils\commitAttribution.ts:103: * Synchronously return the cached result of isInternalModelRepo().
_archive/compare_code/gg-claude-code-runnable/src\utils\commitAttribution.ts:758:      ['diff', '--cached', '--stat', '--', filePath],
_archive/compare_code/gg-claude-code-runnable/src\utils\commitAttribution.ts:799:      ['diff', '--cached', '--name-status', '--', filePath],
_archive/compare_code/gg-claude-code-runnable/src\utils\commitAttribution.ts:823:      ['diff', '--cached', '--name-only'],
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:19:  cacheFile: string
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:30:    const cacheFile = join(claudeDir, 'completion.zsh')
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:34:      cacheFile,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:35:      completionLine: `[[ -f "${cacheFile}" ]] && source "${cacheFile}"`,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:40:    const cacheFile = join(claudeDir, 'completion.bash')
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:44:      cacheFile,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:45:      completionLine: `[ -f "${cacheFile}" ] && source "${cacheFile}"`,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:51:    const cacheFile = join(claudeDir, 'completion.fish')
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:55:      cacheFile,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:56:      completionLine: `[ -f "${cacheFile}" ] && source "${cacheFile}"`,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:72: * Generate and cache the completion script, then add a source line to the
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:81:  // Ensure the cache directory exists
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:83:    await mkdir(dirname(shell.cacheFile), { recursive: true })
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:86:    return `${EOL}${color('warning', theme)(`Could not write ${shell.name} completion cache`)}${EOL}${chalk.dim(`Run manually: claude completion ${shell.shellFlag} > ${shell.cacheFile}`)}${EOL}`
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:89:  // Generate the completion script by writing directly to the cache file.
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:97:    shell.cacheFile,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:100:    return `${EOL}${color('warning', theme)(`Could not generate ${shell.name} shell completions`)}${EOL}${chalk.dim(`Run manually: claude completion ${shell.shellFlag} > ${shell.cacheFile}`)}${EOL}`
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:109:      existing.includes(shell.cacheFile)
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:137: * Regenerate cached shell completion scripts in ~/.claude/.
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:146:  logForDebugging(`update: Regenerating ${shell.name} completion cache`)
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:153:    shell.cacheFile,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:158:      `update: Failed to regenerate ${shell.name} completion cache`,
_archive/compare_code/gg-claude-code-runnable/src\utils\completionCache.ts:164:    `update: Regenerated ${shell.name} completion cache at ${shell.cacheFile}`,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:338:                `Failed to invalidate the server cache: ${client.name}`,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:627:                  // Grab cached promise before invalidating to log previous count
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:628:                  const previousToolsPromise = fetchToolsForClient.cache.get(
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:631:                  fetchToolsForClient.cache.delete(client.name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:680:                  // cache here. fetchMcpSkillsForClient returns the cached result.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:681:                  fetchCommandsForClient.cache.delete(client.name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:717:                  fetchResourcesForClient.cache.delete(client.name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:720:                    // Invalidate prompts cache as well: we write commands here,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:722:                    // us stomp its fresh result with our cached stale one.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:723:                    fetchMcpSkillsForClient!.cache.delete(client.name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:724:                    fetchCommandsForClient.cache.delete(client.name)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:800:        //      cache is empty → real connect attempt → spawn/OAuth just to
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:862:      // Clear claude.ai MCP cache so we fetch fresh configs with current auth
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\useManageMCPConnections.ts:1093:        // Persist disabled state to disk FIRST before clearing cache
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:100:      cacheReadInputTokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:101:      cacheCreationInputTokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:203:  // Timestamp when changelog was last fetched (content stored in ~/.claude/cache/changelog.md)
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:205:  // @deprecated - Migrated to ~/.claude/cache/changelog.md. Keep for migration support.
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:206:  cachedChangelog?: string
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:301:  // Guest passes eligibility cache per org - key is org ID
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:307:  // Grove config cache per account - key is account UUID
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:441:  cachedStatsigGates: {
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:446:  cachedDynamicConfigs?: { [configName: string]: unknown }
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:449:  cachedGrowthBookFeatures?: { [featureName: string]: unknown }
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:497:  cachedChromeExtensionInstalled?: boolean // Cached result of whether Chrome extension is installed
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:550:  // undefined = no cache, null = extra usage enabled, string = disabled reason.
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:551:  cachedExtraUsageDisabledReason?: string | null
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:566:  // Disk cache for /api/claude_code/organizations/metrics_enabled.
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:617:    cachedStatsigGates: {},
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:618:    cachedDynamicConfigs: {},
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:619:    cachedGrowthBookFeatures: {},
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:699:  // so once true we can latch it. false is not cached — it gets re-checked
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:701:  // (lodash memoize doesn't fit here because it would also cache false.)
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:778: * in-memory cache still has. This happens when `getConfig` hits a corrupted
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:787:  const cached = globalConfigCache.config
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:788:  if (!cached) return false
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:790:    cached.oauthAccount !== undefined && fresh.oauthAccount === undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:792:    cached.hasCompletedOnboarding === true &&
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:830:    // the cache is still valid -- touching it would corrupt the guard.
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:840:    // getConfig returns defaults. Refuse to write those over a good cached
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:848:        'saveGlobalConfig fallback: re-read config is missing auth that cache has; refusing to write. See GH #3117.',
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:892:    logEvent('tengu_config_cache_stats', {
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:893:      cache_hits: configCacheHits,
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:894:      cache_misses: configCacheMisses,
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:902:// Register cleanup to report cache stats at session end
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1006:      // overshoot makes cache.mtime > file mtime, so we skip the re-read.
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1013:          // A write-through may have advanced the cache while we were reading;
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1036:// Write-through: what we just wrote IS the new config. cache.mtime overshoots
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1081:    // If anything goes wrong, fall back to uncached behavior
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1150: * whether to invalidate the cache -- invalidating after a skipped write
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1151: * destroys the good cached state the auth-loss guard depends on.
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1219:        'saveConfigWithLock: re-read config is missing auth that cache has; refusing to write to avoid wiping ~/.claude.json. See GH #3117.',
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1671:    // defaults over good cached config. See GH #3117.
_archive/compare_code/gg-claude-code-runnable/src\utils\config.ts:1675:        'saveCurrentProjectConfig fallback: re-read config is missing auth that cache has; refusing to write. See GH #3117.',
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaa.ts:72: * the cached id_token based on OAuth error semantics (not substring matching):
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaa.ts:267:    // 4xx → id_token rejected (invalid_grant etc.), clear cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\contentArray.ts:4: * cache editing directives) correctly within user messages.
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\executor.ts:271:  // call — it caches internally, so screenshot-only flows never pull the
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:3: * standard authorization_code + PKCE flow, then caches it by IdP issuer.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:6: * MCP server auths. The id_token is cached in the keychain and reused until expiry.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:79: * Normalize an IdP issuer URL for use as a cache key: strip trailing slashes,
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:81: * cosmetically but should hit the same cache slot. Exported so the setup
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:96: * Read a cached id_token for the given IdP issuer from secure storage.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:126: * Save an externally-obtained id_token into the XAA cache — the exact slot
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:130: * Parses the JWT's exp claim for cache TTL (same as acquireIdpIdToken).
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:242: * derive a cache TTL.
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:398: * Acquire an id_token from the IdP: return cached if valid, otherwise run
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:406:  const cached = getCachedIdpIdToken(idpIssuer)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:407:  if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:408:    logMCPDebug('xaa', `Using cached id_token for ${idpIssuer}`)
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:409:    return cached
_archive/compare_code/gg-claude-code-runnable/src\services\mcp\xaaIdpLogin.ts:412:  logMCPDebug('xaa', `No cached id_token for ${idpIssuer}; starting OIDC login`)
_archive/compare_code/gg-claude-code-runnable/src\utils\context.ts:121:    cache_creation_input_tokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\context.ts:122:    cache_read_input_tokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\context.ts:132:    currentUsage.cache_creation_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\utils\context.ts:133:    currentUsage.cache_read_input_tokens
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\hostAdapter.ts:30:let cached: ComputerUseHostAdapter | undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\hostAdapter.ts:39:  if (cached) return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\hostAdapter.ts:40:  cached = {
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\hostAdapter.ts:68:  return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\inputLoader.ts:6:let cached: ComputerUseInputAPI | undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\inputLoader.ts:23:  if (cached) return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\inputLoader.ts:29:  return (cached = input)
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\swiftLoader.ts:3:let cached: ComputerUseAPI | undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\swiftLoader.ts:8: * the node_modules prebuilds/ path). We cache the loaded native module.
_archive/compare_code/gg-claude-code-runnable/src\utils\computerUse\swiftLoader.ts:20:  return (cached ??= require('@ant/computer-use-swift') as ComputerUseAPI)
_archive/compare_code/gg-claude-code-runnable/src\utils\cronJitterConfig.ts:22:// restart. The underlying call is a synchronous cache read; the refresh just
_archive/compare_code/gg-claude-code-runnable/src\utils\cronJitterConfig.ts:58: * every tick via the `getJitterConfig` callback — cheap (synchronous cache
_archive/compare_code/gg-claude-code-runnable/src\utils\Cursor.ts:1140:   * Lazily computes and caches wrapped lines.
_archive/compare_code/gg-claude-code-runnable/src\utils\Cursor.ts:1488:    const cached = this.navigationCache.get(key)
_archive/compare_code/gg-claude-code-runnable/src\utils\Cursor.ts:1489:    if (cached !== undefined) return cached as T
_archive/compare_code/gg-claude-code-runnable/src\utils\debug.ts:67:  isDebugMode.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\detectRepository.ts:62: * Synchronously returns the cached github.com repository for the current cwd
_archive/compare_code/gg-claude-code-runnable/src\utils\detectRepository.ts:64: * github.com. Call detectCurrentRepository() first to populate the cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\deepLink\registerProtocol.ts:256: * a cached flag in ~/.claude.json, so:
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:27:// cache is only consulted when both IS_LIBC_MUSL and IS_LIBC_GLIBC are false.
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:30:// Fire-and-forget: populate the musl cache for the node fallback path.
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:50: * whose result is cached at module load. If the cache isn't populated yet, returns false.
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:56:  // Fallback for node: runtime detection via pre-populated cache
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:112:// Synchronous version that returns cached result or falls back to env.terminal
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:119:      // Return cached value if available, otherwise fall back to generic detection
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:120:      // The async version should be called early in app initialization to populate cache
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:124:      // Fall back to generic 'pycharm' if cache not populated yet
_archive/compare_code/gg-claude-code-runnable/src\utils\envDynamic.ts:133: * Call this early in app initialization to populate the cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\envUtils.ts:6:// tests that change the env var get a fresh value without explicit cache.clear.
_archive/compare_code/gg-claude-code-runnable/src\utils\errorLogSink.ts:17:import { CACHE_PATHS } from './cachePaths.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\exampleCommands.ts:19:  /(?:^|\/)(?:dist|build|out|target|node_modules|\.next|__pycache__)\//,
_archive/compare_code/gg-claude-code-runnable/src\utils\exampleCommands.ts:172:  // If no example files cached, kickstart fetch in background
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:346:// In-memory cache of the fast mode status from the API.
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:388: * Resolve orgStatus from the persisted cache without making any API calls.
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:400:  const cachedEnabled = getGlobalConfig().penguinModeOrgEnabled === true
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:402:    isAnt || cachedEnabled
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:425:  // Resolve orgStatus from cache and bail before burning the throttle window.
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:432:    const cachedEnabled = getGlobalConfig().penguinModeOrgEnabled === true
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:434:      isAnt || cachedEnabled
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:512:      // External users: fall back to the cached penguinModeOrgEnabled value;
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:513:      // if no positive cache, disable with network_error reason.
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:515:      const cachedEnabled = getGlobalConfig().penguinModeOrgEnabled === true
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:517:        isAnt || cachedEnabled
_archive/compare_code/gg-claude-code-runnable/src\utils\fastMode.ts:521:        `Failed to fetch org fast mode status, defaulting to ${orgStatus.status === 'enabled' ? 'enabled (cached)' : 'disabled (network_error)'}: ${err}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\file.ts:272: * 1.35B Read calls × 132 lines avg this is 2.18% of fleet uncached input
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:11: * A simple in-memory cache for file contents with automatic invalidation based on modification time.
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:15:  private cache = new Map<string, CachedFileData>()
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:25:    // Get file stats for cache invalidation
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:30:      // File was deleted, remove from cache and re-throw
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:31:      this.cache.delete(filePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:35:    const cacheKey = filePath
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:36:    const cachedData = this.cache.get(cacheKey)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:38:    // Check if we have valid cached data
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:39:    if (cachedData && cachedData.mtime === stats.mtimeMs) {
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:41:        content: cachedData.content,
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:42:        encoding: cachedData.encoding,
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:52:    // Update cache
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:53:    this.cache.set(cacheKey, {
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:59:    // Evict oldest entries if cache is too large
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:60:    if (this.cache.size > this.maxCacheSize) {
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:61:      const firstKey = this.cache.keys().next().value
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:63:        this.cache.delete(firstKey)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:71:   * Clears the entire cache. Useful for testing or memory management.
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:74:    this.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:78:   * Removes a specific file from the cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:81:    this.cache.delete(filePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:85:   * Gets cache statistics for debugging/monitoring.
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:89:      size: this.cache.size,
_archive/compare_code/gg-claude-code-runnable/src\utils\fileReadCache.ts:90:      entries: Array.from(this.cache.keys()),
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:1:import { LRUCache } from 'lru-cache'
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:17:// Default max entries for read file state caches
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:20:// Default size limit for file state caches (25MB)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:25: * A file state cache that normalizes all path keys before access.
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:26: * This ensures consistent cache hits regardless of whether callers pass
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:31:  private cache: LRUCache<string, FileState>
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:34:    this.cache = new LRUCache<string, FileState>({
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:42:    return this.cache.get(normalize(key))
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:46:    this.cache.set(normalize(key), value)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:51:    return this.cache.has(normalize(key))
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:55:    return this.cache.delete(normalize(key))
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:59:    this.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:63:    return this.cache.size
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:67:    return this.cache.max
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:71:    return this.cache.maxSize
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:75:    return this.cache.calculatedSize
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:79:    return this.cache.keys()
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:83:    return this.cache.entries()
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:87:    return this.cache.dump()
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:91:    this.cache.load(entries)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:98: * Note: Images are not cached (see FileReadTool) so size limit is mainly
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:108:// Helper function to convert cache to object (used by compact.ts)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:109:export function cacheToObject(
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:110:  cache: FileStateCache,
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:112:  return Object.fromEntries(cache.entries())
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:115:// Helper function to get all keys from cache (used by several components)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:116:export function cacheKeys(cache: FileStateCache): string[] {
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:117:  return Array.from(cache.keys())
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:121:// Preserves size limit configuration from the source cache
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:122:export function cloneFileStateCache(cache: FileStateCache): FileStateCache {
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:123:  const cloned = createFileStateCacheWithSizeLimit(cache.max, cache.maxSize)
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:124:  cloned.load(cache.dump())
_archive/compare_code/gg-claude-code-runnable/src\utils\fileStateCache.ts:128:// Merge two file state caches, with more recent entries (by timestamp) overriding older ones
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:5: * 1. Share identical cache-critical params with the parent to guarantee prompt cache hits
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:48: * to share the parent's prompt cache. The Anthropic API cache key is composed of:
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:58:  /** System prompt - must match parent for cache hits */
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:60:  /** User context - prepended to messages, affects cache */
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:62:  /** System context - appended to system prompt, affects cache */
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:66:  /** Parent context messages for prompt cache sharing */
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:72:// prompt cache without each caller threading params through.
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:87:  cacheSafeParams: CacheSafeParams
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:98:   * AND budget_tokens (via clamping in claude.ts). If the fork uses cacheSafeParams
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:99:   * to share the parent's prompt cache, a different budget_tokens will invalidate
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:100:   * the cache — thinking config is part of the cache key. Only set this when cache
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:110:  /** Skip writing new prompt cache entries on the last message. For
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:269:  /** Override the readFileState (e.g., fresh cache instead of clone) */
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:302:   * are re-replaced (prompt cache stability). */
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:390:    // Clone by default (not fresh): cache-sharing forks process parent
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:393:    // prefix differs → cache miss. A clone makes identical decisions →
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:394:    // cache hit. For non-forking subagents the parent UUIDs never match
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:465: * Runs a forked agent query loop and tracks cache hit metrics.
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:468: * 1. Uses identical cache-safe params from parent to enable prompt caching
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:476: *   cacheSafeParams: {
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:491:  cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:512:  } = cacheSafeParams
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:523:  // same as the main thread — identical post-repair prefix keeps the cache hit.
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:543:  // Run the query loop with isolated context (cache-safe params preserved)
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:600:    // Release cloned file state cache memory (same pattern as runAgent.ts)
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:607:    `Forked agent [${forkLabel}] finished: ${outputMessages.length} messages, types=[${outputMessages.map(m => m.type).join(', ')}], totalUsage: input=${totalUsage.input_tokens} output=${totalUsage.output_tokens} cacheRead=${totalUsage.cache_read_input_tokens} cacheCreate=${totalUsage.cache_creation_input_tokens}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:646:  // Calculate cache hit rate
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:649:    totalUsage.cache_creation_input_tokens +
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:650:    totalUsage.cache_read_input_tokens
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:651:  const cacheHitRate =
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:653:      ? totalUsage.cache_read_input_tokens / totalInputTokens
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:668:    cacheReadInputTokens: totalUsage.cache_read_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:669:    cacheCreationInputTokens: totalUsage.cache_creation_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:672:    cacheCreationEphemeral1hTokens:
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:673:      totalUsage.cache_creation.ephemeral_1h_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:674:    cacheCreationEphemeral5mTokens:
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:675:      totalUsage.cache_creation.ephemeral_5m_input_tokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\forkedAgent.ts:678:    cacheHitRate,
_archive/compare_code/gg-claude-code-runnable/src\utils\format.ts:97:// `new Intl.NumberFormat` is expensive, so cache formatters for reuse
_archive/compare_code/gg-claude-code-runnable/src\utils\fullscreen.ts:41: * when the env heuristic can't decide; result is cached.
_archive/compare_code/gg-claude-code-runnable/src\utils\fullscreen.ts:57:  // Seed cache with heuristic result so early returns below don't leave it
_archive/compare_code/gg-claude-code-runnable/src\utils\fullscreen.ts:59:  // undefined cache would re-enter this function (re-spawning tmux in the
_archive/compare_code/gg-claude-code-runnable/src\utils\fullscreen.ts:83:  // unavailable. Keep the heuristic result cached.
_archive/compare_code/gg-claude-code-runnable/src\utils\generatedFiles.ts:53:  '/__pycache__/',
_archive/compare_code/gg-claude-code-runnable/src\utils\git.ts:93: * Memoized per startPath with an LRU cache (max 50 entries) to prevent
_archive/compare_code/gg-claude-code-runnable/src\utils\git.ts:101:  cache: typeof findGitRootImpl.cache
_archive/compare_code/gg-claude-code-runnable/src\utils\git.ts:107:  wrapper.cache = findGitRootImpl.cache
_archive/compare_code/gg-claude-code-runnable/src\utils\git.ts:199:  cache: typeof resolveCanonicalRoot.cache
_archive/compare_code/gg-claude-code-runnable/src\utils\git.ts:208:  wrapper.cache = resolveCanonicalRoot.cache
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:6: * and the GitHeadWatcher that caches branch/SHA with fs.watchFile.
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:30:/** Clear cached git dir resolutions. Exported for testing only. */
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:44:  const cached = resolveGitDirCache.get(cwd)
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:45:  if (cached !== undefined) {
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:46:    return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:312:// GitFileWatcher — watches git files and caches derived values.
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:313:// Lazily initialized on first cache access. Invalidates all cached
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:340:  private cache = new Map<string, CacheEntry<unknown>>()
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:434:    // cache correctly serves stale-marked values until the watcher updates.
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:441:    for (const entry of this.cache.values()) {
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:455:   * Get a cached value by key. On first call for a key, computes and caches it.
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:456:   * Subsequent calls return the cached value until a watched file changes,
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:465:    const existing = this.cache.get(key)
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:476:    // Only update the cached value if no new invalidation arrived during compute
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:477:    const entry = this.cache.get(key)
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:482:      this.cache.set(key, { value, dirty: false, compute })
_archive/compare_code/gg-claude-code-runnable/src\utils\git\gitFilesystem.ts:490:    this.cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\utils\gracefulShutdown.ts:489:  // Signal to inference that this session's cache can be evicted.
_archive/compare_code/gg-claude-code-runnable/src\utils\gracefulShutdown.ts:493:    logEvent('tengu_cache_eviction_hint', {
_archive/compare_code/gg-claude-code-runnable/src\utils\groupToolUses.ts:26:  let cached = GROUPING_CACHE.get(tools)
_archive/compare_code/gg-claude-code-runnable/src\utils\groupToolUses.ts:27:  if (!cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\groupToolUses.ts:28:    cached = new Set(tools.filter(t => t.renderGroupedToolUse).map(t => t.name))
_archive/compare_code/gg-claude-code-runnable/src\utils\groupToolUses.ts:29:    GROUPING_CACHE.set(tools, cached)
_archive/compare_code/gg-claude-code-runnable/src\utils\groupToolUses.ts:31:  return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\hash.ts:5: * output (e.g. cache directory names that must survive runtime upgrades).
_archive/compare_code/gg-claude-code-runnable/src\utils\hooks\AsyncHookRegistry.ts:259:      `Invalidating session env cache after SessionStart hook completed`,
_archive/compare_code/gg-claude-code-runnable/src\utils\hooks.ts:4329: * - Eager reload after compaction (getMemoryFiles cache cleared by
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1070:let cachedRunningIDEs: IdeType[] | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1151: * This performs fresh detection (~150ms) and updates the cache for subsequent
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1156:  cachedRunningIDEs = result
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1161: * Returns cached IDE detection results, or performs detection if cache is empty.
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1165:  if (cachedRunningIDEs === null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1168:  return cachedRunningIDEs
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1172: * Resets the cache for detectRunningIDEsCached.
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1176:  cachedRunningIDEs = null
_archive/compare_code/gg-claude-code-runnable/src\utils\ide.ts:1336:        // Always check installation to populate the sync cache used by status notices
_archive/compare_code/gg-claude-code-runnable/src\utils\hooks\hooksConfigManager.ts:24:// toolNames array each render (e.g. HooksConfigMenu) hit the cache instead
_archive/compare_code/gg-claude-code-runnable/src\utils\hooks\hooksConfigSnapshot.ts:105:  // Reset the session cache to ensure we read fresh settings from disk.
_archive/compare_code/gg-claude-code-runnable/src\utils\hooks\hooksConfigSnapshot.ts:106:  // Without this, the snapshot could use stale cached settings when the user
_archive/compare_code/gg-claude-code-runnable/src\utils\hooks\hooksConfigSnapshot.ts:107:  // edits settings.json externally and then runs /hooks - the session cache
_archive/compare_code/gg-claude-code-runnable/src\utils\imageStore.ts:9:const IMAGE_STORE_DIR = 'image-cache'
_archive/compare_code/gg-claude-code-runnable/src\utils\imageStore.ts:12:// In-memory cache of stored image paths
_archive/compare_code/gg-claude-code-runnable/src\utils\imageStore.ts:41:export function cacheImagePath(content: PastedContent): string | null {
_archive/compare_code/gg-claude-code-runnable/src\utils\imageStore.ts:109: * Clear the in-memory cache of stored image paths.
_archive/compare_code/gg-claude-code-runnable/src\utils\imageStore.ts:127: * Clean up old image cache directories from previous sessions.
_archive/compare_code/gg-claude-code-runnable/src\utils\imageStore.ts:150:        logForDebugging(`Cleaned up old image cache: ${sessionPath}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:4: * Intl constructors are expensive (~0.05-0.1ms each), so we cache instances
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:53:// RelativeTimeFormat cache (keyed by style:numeric)
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:70:let cachedTimeZone: string | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:73:  if (!cachedTimeZone) {
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:74:    cachedTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:76:  return cachedTimeZone
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:82:let cachedSystemLocaleLanguage: string | undefined | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:85:  if (cachedSystemLocaleLanguage === null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:88:      cachedSystemLocaleLanguage = new Intl.Locale(locale).language
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:90:      cachedSystemLocaleLanguage = undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\intl.ts:93:  return cachedSystemLocaleLanguage
_archive/compare_code/gg-claude-code-runnable/src\utils\jetbrains.ts:28:// https://www.jetbrains.com/help/pycharm/directories-used-by-the-ide-to-store-settings-caches-plugins-and-logs.html#plugins-directory
_archive/compare_code/gg-claude-code-runnable/src\utils\jetbrains.ts:183: * Returns the cached result of isJetBrainsPluginInstalled synchronously.
_archive/compare_code/gg-claude-code-runnable/src\utils\json.ts:17:// 2. Invalid JSON must also be cached — otherwise repeated calls with the same
_archive/compare_code/gg-claude-code-runnable/src\utils\json.ts:21:// used lodash memoize which cached every unique JSON string forever (settings,
_archive/compare_code/gg-claude-code-runnable/src\utils\json.ts:23:// Note: shouldLogError is intentionally excluded from the cache key (matching
_archive/compare_code/gg-claude-code-runnable/src\utils\json.ts:28:// every CC startup), so the cache never hits anyway.
_archive/compare_code/gg-claude-code-runnable/src\utils\json.ts:31:function parseJSONUncached(json: string, shouldLogError: boolean): CachedParse {
_archive/compare_code/gg-claude-code-runnable/src\utils\json.ts:42:const parseJSONCached = memoizeWithLRU(parseJSONUncached, json => json, 50)
_archive/compare_code/gg-claude-code-runnable/src\utils\json.ts:53:        ? parseJSONUncached(json, shouldLogError)
_archive/compare_code/gg-claude-code-runnable/src\utils\json.ts:57:  { cache: parseJSONCached.cache },
_archive/compare_code/gg-claude-code-runnable/src\utils\lazySchema.ts:6:  let cached: T | undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\lazySchema.ts:7:  return () => (cached ??= factory())
_archive/compare_code/gg-claude-code-runnable/src\utils\localInstaller.ts:18:// populate the memoize cache with that stale value for all 150+ other callers.
_archive/compare_code/gg-claude-code-runnable/src\utils\log.ts:17:import { CACHE_PATHS } from './cachePaths.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:182:// Simple cache for preloaded activity
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:183:let cachedActivity: LogOption[] = []
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:184:let cachePromise: Promise<LogOption[]> | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:191:  if (cachePromise) {
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:192:    return cachePromise
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:196:  cachePromise = loadMessageLogs(10)
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:198:      cachedActivity = logs
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:211:      return cachedActivity
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:214:      cachedActivity = []
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:215:      return cachedActivity
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:218:  return cachePromise
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:222: * Gets cached activity synchronously
_archive/compare_code/gg-claude-code-runnable/src\utils\logoV2Utils.ts:225:  return cachedActivity
_archive/compare_code/gg-claude-code-runnable/src\utils\managedEnv.ts:154:  // getSettingsForSource('policySettings') below consults the remote cache,
_archive/compare_code/gg-claude-code-runnable/src\utils\managedEnv.ts:192:  // Clear caches so agents are rebuilt with the new env vars
_archive/compare_code/gg-claude-code-runnable/src\utils\markdownConfigLoader.ts:428:  // Custom resolver creates cache key from both subdir and cwd parameters
_archive/compare_code/gg-claude-code-runnable/src\utils\mcpInstructionsDelta.ts:31: * False → prompts.ts keeps its DANGEROUS_uncachedSystemPromptSection
_archive/compare_code/gg-claude-code-runnable/src\utils\mcpInstructionsDelta.ts:32: * (rebuilt every turn; cache-busts on late connect).
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:1:import { LRUCache } from 'lru-cache'
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:13:  cache: {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:20:  cache: {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:30: * Creates a memoized function that returns cached values while refreshing in parallel.
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:31: * This implements a write-through cache pattern:
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:32: * - If cache is fresh, return immediately
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:33: * - If cache is stale, return the stale value but refresh it in the background
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:34: * - If no cache exists, block and compute the value
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:37: * @param cacheLifetimeMs The lifetime of cached values in milliseconds
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:42:  cacheLifetimeMs: number = 5 * 60 * 1000, // Default 5 minutes
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:44:  const cache = new Map<string, CacheEntry<Result>>()
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:48:    const cached = cache.get(key)
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:51:    // Populate cache
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:52:    if (!cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:54:      cache.set(key, {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:62:    // If we have a stale cache entry and it's not already refreshing
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:64:      cached &&
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:65:      now - cached.timestamp > cacheLifetimeMs &&
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:66:      !cached.refreshing
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:69:      cached.refreshing = true
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:72:      // identity-guarded: a concurrent cache.clear() + cold-miss stores a
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:79:          if (cache.get(key) === cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:80:            cache.set(key, {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:89:          if (cache.get(key) === cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:90:            cache.delete(key)
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:95:      return cached.value
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:98:    return cache.get(key)!.value
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:101:  // Add cache clear method
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:102:  memoized.cache = {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:103:    clear: () => cache.clear(),
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:110: * Creates a memoized async function that returns cached values while refreshing in parallel.
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:111: * This implements a write-through cache pattern for async functions:
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:112: * - If cache is fresh, return immediately
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:113: * - If cache is stale, return the stale value but refresh it in the background
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:114: * - If no cache exists, block and compute the value
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:117: * @param cacheLifetimeMs The lifetime of cached values in milliseconds
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:122:  cacheLifetimeMs: number = 5 * 60 * 1000, // Default 5 minutes
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:123:): ((...args: Args) => Promise<Result>) & { cache: { clear: () => void } } {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:124:  const cache = new Map<string, CacheEntry<Result>>()
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:128:  // variant awaits before cache.set, so concurrent cold-miss callers would
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:136:    const cached = cache.get(key)
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:139:    // Populate cache - if this throws, nothing gets cached
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:140:    if (!cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:147:        // Identity-guard: cache.clear() during the await should discard this
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:151:          cache.set(key, {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:165:    // If we have a stale cache entry and it's not already refreshing
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:167:      cached &&
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:168:      now - cached.timestamp > cacheLifetimeMs &&
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:169:      !cached.refreshing
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:172:      cached.refreshing = true
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:175:      // identity-guarded against a concurrent cache.clear() + cold-miss
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:180:      const staleEntry = cached
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:183:          if (cache.get(key) === staleEntry) {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:184:            cache.set(key, {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:193:          if (cache.get(key) === staleEntry) {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:194:            cache.delete(key)
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:199:      return cached.value
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:202:    return cache.get(key)!.value
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:205:  // Add cache clear method. Also clear inFlight: clear() during a cold-miss
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:210:  memoized.cache = {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:212:      cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:218:    cache: { clear: () => void }
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:225: * when the cache reaches its maximum size.
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:229: * while maintaining good cache hit rates for typical conversations.
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:232: * @returns A memoized version of the function with cache management methods
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:239:  cacheFn: (...args: Args) => string,
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:242:  const cache = new LRUCache<string, Result>({
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:247:    const key = cacheFn(...args)
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:248:    const cached = cache.get(key)
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:249:    if (cached !== undefined) {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:250:      return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:254:    cache.set(key, result)
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:258:  // Add cache management methods
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:259:  memoized.cache = {
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:260:    clear: () => cache.clear(),
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:261:    size: () => cache.size,
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:262:    delete: (key: string) => cache.delete(key),
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:264:    get: (key: string) => cache.peek(key),
_archive/compare_code/gg-claude-code-runnable/src\utils\memoize.ts:265:    has: (key: string) => cache.has(key),
_archive/compare_code/gg-claude-code-runnable/src\utils\messages.ts:365:    cache_creation_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\messages.ts:366:    cache_read_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\messages.ts:369:    cache_creation: {
_archive/compare_code/gg-claude-code-runnable/src\utils\messages.ts:3712:          // rendered bytes are stable across turns (prompt-cache hit).
_archive/compare_code/gg-claude-code-runnable/src\utils\modelCost.ts:135:    ((usage.cache_read_input_tokens ?? 0) / 1_000_000) *
_archive/compare_code/gg-claude-code-runnable/src\utils\modelCost.ts:137:    ((usage.cache_creation_input_tokens ?? 0) / 1_000_000) *
_archive/compare_code/gg-claude-code-runnable/src\utils\modelCost.ts:191:    cacheReadInputTokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\modelCost.ts:192:    cacheCreationInputTokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\modelCost.ts:198:    cache_read_input_tokens: tokens.cacheReadInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\modelCost.ts:199:    cache_creation_input_tokens: tokens.cacheCreationInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\mtls.ts:155: * Clear the mTLS configuration cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\mtls.ts:158:  getMTLSConfig.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\mtls.ts:159:  getMTLSAgent.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\mtls.ts:160:  logForDebugging('Cleared mTLS configuration cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:83:    const cachedCredentials = await refreshAndGetAwsCredentials()
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:84:    if (cachedCredentials) {
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:86:        accessKeyId: cachedCredentials.accessKeyId,
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:87:        secretAccessKey: cachedCredentials.secretAccessKey,
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:88:        sessionToken: cachedCredentials.sessionToken,
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:128:    const cachedCredentials = await refreshAndGetAwsCredentials()
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:129:    if (cachedCredentials) {
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:131:        accessKeyId: cachedCredentials.accessKeyId,
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:132:        secretAccessKey: cachedCredentials.secretAccessKey,
_archive/compare_code/gg-claude-code-runnable/src\utils\model\bedrock.ts:133:        sessionToken: cachedCredentials.sessionToken,
_archive/compare_code/gg-claude-code-runnable/src\utils\model\check1mAccess.ts:7: * Check if extra usage is enabled based on the cached disabled reason.
_archive/compare_code/gg-claude-code-runnable/src\utils\model\check1mAccess.ts:12:  const reason = getGlobalConfig().cachedExtraUsageDisabledReason
_archive/compare_code/gg-claude-code-runnable/src\utils\model\check1mAccess.ts:13:  // undefined = no cache yet, treat as not enabled (conservative)
_archive/compare_code/gg-claude-code-runnable/src\utils\nativeInstaller\installer.ts:1380:    // Eligible versions: not protected, sorted newest first (reuse cached mtime)
_archive/compare_code/gg-claude-code-runnable/src\utils\pasteStore.ts:8:const PASTE_STORE_DIR = 'paste-cache'
_archive/compare_code/gg-claude-code-runnable/src\utils\pdf.ts:150: * Reset the pdftoppm availability cache. Used by tests only.
_archive/compare_code/gg-claude-code-runnable/src\utils\pdf.ts:158: * The result is cached for the lifetime of the process.
_archive/compare_code/gg-claude-code-runnable/src\utils\model\model.ts:497:    // can tell the user to restart/wait for flag cache refresh to get the latest values.
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:39:  return join(getClaudeConfigHomeDir(), 'cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:60:// Keyed on cache path so tests that set CLAUDE_CONFIG_DIR get a fresh read
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:77:  const cached = loadCache(getCachePath())
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:78:  if (!cached || cached.length === 0) return undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:80:  const exact = cached.find(c => c.id.toLowerCase() === m)
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:82:  return cached.find(c => m.includes(c.id.toLowerCase()))
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:102:      logForDebugging('[modelCapabilities] cache unchanged, skipping write')
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:111:    loadCache.cache.delete(path)
_archive/compare_code/gg-claude-code-runnable/src\utils\model\modelCapabilities.ts:112:    logForDebugging(`[modelCapabilities] cached ${models.length} models`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plans.ts:29: * The slug is generated lazily on first access and cached for the session.
_archive/compare_code/gg-claude-code-runnable/src\utils\plans.ts:34:  const cache = getPlanSlugCache()
_archive/compare_code/gg-claude-code-runnable/src\utils\plans.ts:35:  let slug = cache.get(id)
_archive/compare_code/gg-claude-code-runnable/src\utils\plans.ts:46:    cache.set(id, slug!)
_archive/compare_code/gg-claude-code-runnable/src\utils\plans.ts:155: * Sets the slug in the session cache so getPlanSlug returns it.
_archive/compare_code/gg-claude-code-runnable/src\utils\model\validateModel.ts:49:  // Check cache first
_archive/compare_code/gg-claude-code-runnable/src\utils\model\validateModel.ts:69:              cache_control: { type: 'ephemeral' },
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\cacheUtils.ts:70: * Pass 2: For each cached version not in installed_plugins.json:
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\cacheUtils.ts:75:  // Zip cache mode stores plugins as .zip files, not directories. readSubdirs
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\cacheUtils.ts:85:    const cachePath = getPluginCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\cacheUtils.ts:96:    for (const marketplace of await readSubdirs(cachePath)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\cacheUtils.ts:97:      const marketplacePath = join(cachePath, marketplace)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\cacheUtils.ts:114:    logForDebugging(`Plugin cache cleanup failed: ${error}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\filesystem.ts:680:// Exported for test/preload.ts cache clearing (shard-isolation).
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\filesystem.ts:1199: * @param precomputedPathsToCheck - Optional cached result of
_archive/compare_code/gg-claude-code-runnable/src\utils\powershell\parser.ts:1264:// These should be evicted from the cache so subsequent calls can retry.
_archive/compare_code/gg-claude-code-runnable/src\utils\powershell\parser.ts:1266:// should stay cached since retrying would produce the same result.
_archive/compare_code/gg-claude-code-runnable/src\utils\powershell\parser.ts:1279:    // The current caller still receives the cached promise for this call,
_archive/compare_code/gg-claude-code-runnable/src\utils\powershell\parser.ts:1286:        parsePowerShellCommandCached.cache.delete(command)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\dependencyResolver.ts:76: * even if already enabled, so re-installing a plugin always re-caches it.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\dependencyResolver.ts:112:    // still cache/register it. Without this guard, re-installing a plugin
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\dependencyResolver.ts:113:    // that's in settings but missing from disk (e.g., cache cleared,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\dependencyResolver.ts:115:    // `cacheAndRegisterPlugin` would never fire — user sees
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\getNextPermissionMode.ts:11:// Checks both the cached isAutoModeAvailable (set at startup by
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\fetchTelemetry.ts:29:export type PluginFetchOutcome = 'success' | 'failure' | 'cache_hit'
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\pathValidation.ts:133: * @param precomputedPathsToCheck - Optional cached result of
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\gitAvailability.ts:32: * This is memoized so repeated calls within a session return the cached result.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\gitAvailability.ts:57: * lodash memoize uses a no-arg cache key of undefined.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\gitAvailability.ts:60:  checkGitAvailable.cache?.set?.(undefined, Promise.resolve(false))
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\gitAvailability.ts:64: * Clear the git availability cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\gitAvailability.ts:68:  checkGitAvailable.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\promptShellExecution.ts:36:  let cached: PromptShellTool | undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\promptShellExecution.ts:38:    if (!cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\promptShellExecution.ts:39:      cached = (
_archive/compare_code/gg-claude-code-runnable/src\utils\promptShellExecution.ts:43:    return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:46:    `installPluginsForHeadless: starting${zipCacheMode ? ' (zip cache mode)' : ''}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:53:  // If registration changed state, clear caches so the early plugin-load pass
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:56:  // run with a seed-cached plugin would show 0 plugin commands/agents/skills
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:64:  // Ensure zip cache directory structure exists
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:93:      // with materialized state. Zip cache: skip unsupported source types.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:124:          `installPluginsForHeadless: skipped ${reconcileResult.skipped.length} marketplace(s) unsupported by zip cache: ${reconcileResult.skipped.join(', ')}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:131:      // Clear caches so newly-installed marketplace plugins are discoverable.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:132:      // Plugin caching is the loader's job — after caches clear, the caller's
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:133:      // refreshPluginState() → loadAllPlugins() will cache any missing plugins
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:144:    // Zip cache: save marketplace JSONs for offline access on ephemeral containers.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\headlessPluginInstall.ts:162:    // Zip cache: register session cleanup for extracted plugin temp dirs
_archive/compare_code/gg-claude-code-runnable/src\utils\proxy.ts:421: * Clear proxy agent cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\proxy.ts:424:  getProxyAgent.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\proxy.ts:425:  logForDebugging('Cleared proxy agent cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\hintRecommendation.ts:62: * just to strip a stderr line. The async marketplace-cache check happens
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\hintRecommendation.ts:101: * the plugin isn't in the marketplace cache — the hint is discarded.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\hintRecommendation.ts:118:      : 'not_in_cache') as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\hintRecommendation.ts:123:      `[hintRecommendation] ${pluginId} not found in marketplace cache`,
_archive/compare_code/gg-claude-code-runnable/src\utils\queryContext.ts:2: * Shared helpers for building the API cache-key prefix (systemPrompt,
_archive/compare_code/gg-claude-code-runnable/src\utils\queryContext.ts:31: * Fetch the three context pieces that form the API cache-key prefix:
_archive/compare_code/gg-claude-code-runnable/src\utils\queryContext.ts:82: * main loop will send, preserving the cache hit in the common case.
_archive/compare_code/gg-claude-code-runnable/src\utils\queryContext.ts:84: * May still miss the cache if the main loop applies extras this path doesn't
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:4: * This module fetches and caches plugin install counts from the official
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:5: * Claude plugins statistics repository. The cache is refreshed if older
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:8: * Cache location: ~/.claude/plugins/install-counts-cache.json
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:24:const INSTALL_COUNTS_CACHE_FILENAME = 'install-counts-cache.json'
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:30: * Structure of the install counts cache file
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:52: * Get the path to the install counts cache file
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:59: * Load the install counts cache from disk.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:63:  const cachePath = getInstallCountsCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:66:    const content = await readFile(cachePath, { encoding: 'utf-8' })
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:77:      logForDebugging('Install counts cache has invalid structure')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:81:    const cache = parsed as {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:88:    if (cache.version !== INSTALL_COUNTS_CACHE_VERSION) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:90:        `Install counts cache version mismatch (got ${cache.version}, expected ${INSTALL_COUNTS_CACHE_VERSION})`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:96:    if (typeof cache.fetchedAt !== 'string' || !Array.isArray(cache.counts)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:97:      logForDebugging('Install counts cache has invalid structure')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:102:    const fetchedAt = new Date(cache.fetchedAt).getTime()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:104:      logForDebugging('Install counts cache has invalid fetchedAt timestamp')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:109:    const validCounts = cache.counts.every(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:117:      logForDebugging('Install counts cache has malformed entries')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:121:    // Check if cache is stale (>24 hours old)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:124:      logForDebugging('Install counts cache is stale (>24h old)')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:128:    // Return validated cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:130:      version: cache.version as number,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:131:      fetchedAt: cache.fetchedAt,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:132:      counts: cache.counts,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:138:        `Failed to load install counts cache: ${errorMessage(error)}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:146: * Save the install counts cache to disk atomically.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:150:  cache: InstallCountsCache,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:152:  const cachePath = getInstallCountsCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:153:  const tempPath = `${cachePath}.${randomBytes(8).toString('hex')}.tmp`
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:161:    const content = jsonStringify(cache, null, 2)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:168:    await rename(tempPath, cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:169:    logForDebugging('Install counts cache saved successfully')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:220: * Uses cached data if available and less than 24 hours old.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:226:  // Try to load from cache first
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:227:  const cache = await loadInstallCountsCache()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:228:  if (cache) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:229:    logForDebugging('Using cached install counts')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:230:    logPluginFetch('install_counts', INSTALL_COUNTS_URL, 'cache_hit', 0)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:232:    for (const entry of cache.counts) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installCounts.ts:242:    // Save to cache
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:44:// Small cache size for ask operations which typically access few files
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:351:  const cache = createFileStateCacheWithSizeLimit(maxSize)
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:373:          // Ranged reads are not added to the cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:379:            // Normalize to absolute path for consistent cache lookups
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:392:            // Normalize to absolute path for consistent cache lookups
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:426:            // already cached it. Chronological last-wins would otherwise
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:447:              cache.set(readFilePath, {
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:460:            cache.set(writeToolData.filePath, {
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:473:          // Callers seed the cache once at process start (print.ts --resume,
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:482:              cache.set(editFilePath, {
_archive/compare_code/gg-claude-code-runnable/src\utils\queryHelpers.ts:500:  return cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:62: * Memoized cache of installed plugins data (V2 format)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:91: * Clear the installed plugins cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:102:  logForDebugging('Cleared installed plugins cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:111: * 3. Clean up legacy non-versioned cache directories
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:131:      // Clean up legacy cache directories
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:167:      // Clean up legacy cache directories
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:185: * Clean up legacy non-versioned cache directories.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:187: * Legacy cache structure: ~/.claude/plugins/cache/{plugin-name}/
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:188: * Versioned cache structure: ~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:194:  const cachePath = getPluginCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:204:    // List top-level directories in cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:205:    const entries = fs.readdirSync(cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:213:      const entryPath = join(cachePath, entry)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:215:      // Check if this is a versioned cache (marketplace dir with plugin/version subdirs)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:216:      // or a legacy cache (flat plugin directory)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:231:      // This is a legacy flat cache directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:236:        logForDebugging(`Cleaned up legacy cache directory: ${entry}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:241:    logForDebugging(`Failed to clean up legacy cache: ${errorMsg}`, {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:288:    // V2 format uses versioned cache path: ~/.claude/plugins/cache/{marketplace}/{plugin}/{version}
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:316:  // Return cached V2 data if available
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:383:    // Update cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:496: * Load installed plugins directly from disk, bypassing all caches.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:575:    // Clear cache since disk changed, but do NOT update inMemoryInstalledPlugins
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:715:  // Step 1: Migrate to single file format (consolidates V1/V2 files, cleans up legacy cache)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:955: * Delete a plugin's cache directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:958: * @param installPath - Absolute path to the plugin's cache directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:970:    logForDebugging(`Deleted plugin cache at ${installPath}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:972:    // Clean up empty parent plugin directory (cache/{marketplace}/{plugin})
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:973:    // Versioned paths have structure: cache/{marketplace}/{plugin}/{version}
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:974:    const cachePath = getPluginCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:975:    if (installPath.includes('/cache/') && installPath.startsWith(cachePath)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:976:      const pluginDir = dirname(installPath) // e.g., cache/{marketplace}/{plugin}
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:977:      if (pluginDir !== cachePath && pluginDir.startsWith(cachePath)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:993:      `Failed to delete plugin cache at ${installPath}: ${errorMsg}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:1198:          const cachePath = getPluginCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:1200:          const pluginCachePath = join(cachePath, sanitizedName)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:1202:          // Read the cache directory directly — readdir is the first real
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:1203:          // operation, not a pre-check. Its ENOENT tells us the cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\installedPluginsManager.ts:1216:              `External plugin ${pluginId} not in cache, skipping`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\loadPluginAgents.ts:347:  loadPluginAgents.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissions.ts:754:          classifierResult.usage?.cacheReadInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissions.ts:756:          classifierResult.usage?.cacheCreationInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissions.ts:778:          classifierResult.stage1Usage?.cacheReadInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissions.ts:780:          classifierResult.stage1Usage?.cacheCreationInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissions.ts:797:          classifierResult.stage2Usage?.cacheReadInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissions.ts:799:          classifierResult.stage2Usage?.cacheCreationInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\loadPluginCommands.ts:680:  getPluginCommands.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\loadPluginCommands.ts:945:  getPluginSkills.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\loadPluginHooks.ts:166:  loadPluginHooks.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\loadPluginHooks.ts:229: * See #23085 / #23152 poisoned-cache discussion (Slack C09N89L3VNJ).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\loadPluginHooks.ts:279:      // Clear all plugin-related caches
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:713:  // Sync circuit-breaker check (cached GB read). Prevents the
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:733:          'auto mode circuit breaker active (cached) — falling back to default',
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:764:          'auto mode circuit breaker active (cached) — falling back to default',
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:931:  // Use cached values to avoid blocking on startup
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:1089:  // isAutoModeAvailable. The sync startup path uses stale cache; this
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:1323: * Reads the `enabled` field from tengu_auto_mode_config (cached, may be stale).
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:1335:const NO_CACHED_AUTO_MODE_CONFIG = Symbol('no-cached-auto-mode-config')
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:1338: * Like getAutoModeEnabledState but returns undefined when no cached value
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\permissionSetup.ts:1369: * This is a synchronous version that uses cached Statsig values.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\loadPluginOutputStyles.ts:177:  loadPluginOutputStyles.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:26: * 3. Next time the user starts Claude, the cached changelog is available immediately
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:34: * Get the path for the cached changelog file.
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:35: * The changelog is stored at ~/.claude/cache/changelog.md
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:38:  return join(getClaudeConfigHomeDir(), 'cache', 'changelog.md')
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:41:// In-memory cache populated by async reads. Sync callers (React render, sync
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:42:// helpers) read from this cache after setup.ts awaits checkForReleaseNotes().
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:57:  if (!config.cachedChangelog) {
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:61:  const cachePath = getChangelogCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:63:  // If cache file doesn't exist, create it from old config
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:65:    await mkdir(dirname(cachePath), { recursive: true })
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:66:    await writeFile(cachePath, config.cachedChangelog, {
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:75:  saveGlobalConfig(({ cachedChangelog: _, ...rest }) => rest)
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:79: * Fetch the changelog from GitHub and store it in cache file
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:103:    const cachePath = getChangelogCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:105:    // Ensure cache directory exists
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:106:    await mkdir(dirname(cachePath), { recursive: true })
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:108:    // Write changelog to cache file
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:109:    await writeFile(cachePath, changelogContent, { encoding: 'utf-8' })
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:122: * Get the stored changelog from cache file if available.
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:123: * Populates the in-memory cache for subsequent sync reads.
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:124: * @returns The cached changelog content or empty string if not available
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:130:  const cachePath = getChangelogCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:132:    const content = await readFile(cachePath, 'utf-8')
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:142: * Synchronous accessor for the changelog, reading only from the in-memory cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:145: * the cache is populated before first render via `await checkForReleaseNotes()`.
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:307:  // Ensure the in-memory cache is populated for subsequent sync reads
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:308:  const cachedChangelog = await getStoredChangelog()
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:310:  // If the version has changed or we don't have a cached changelog, fetch a new one
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:312:  if (lastSeenVersion !== currentVersion || !cachedChangelog) {
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:319:    cachedChangelog,
_archive/compare_code/gg-claude-code-runnable/src\utils\releaseNotes.ts:331: * Reads only from the in-memory cache populated by the async version.
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:8:let cachedStdinOverride: ReadStream | undefined | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:13: * Result is cached for the lifetime of the process.
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:16:  // Return cached result if already computed
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:17:  if (cachedStdinOverride !== null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:18:    return cachedStdinOverride
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:23:    cachedStdinOverride = undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:29:    cachedStdinOverride = undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:35:    cachedStdinOverride = undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:41:    cachedStdinOverride = undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:53:    cachedStdinOverride = ttyStream
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:54:    return cachedStdinOverride
_archive/compare_code/gg-claude-code-runnable/src\utils\renderOptions.ts:57:    cachedStdinOverride = undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\lspPluginIntegration.ts:330:  // Use cached servers if available
_archive/compare_code/gg-claude-code-runnable/src\utils\ripgrep.ts:352:  // Test ripgrep on first use and cache the result (fire and forget)
_archive/compare_code/gg-claude-code-runnable/src\utils\ripgrep.ts:518:  // ignorePatterns affect the result, so include them in the cache key.
_archive/compare_code/gg-claude-code-runnable/src\utils\ripgrep.ts:549: * Test ripgrep availability on first use and cache the result
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:283:  // cached in worktreeMainRepoPath. Git operations in a worktree need write
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:418: * Called once during initialize() and cached for the session.
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:607:    // Only return warnings when sandboxing is enabled (check settings directly, not cached value)
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:676:  // Note: Memoized caches auto-invalidate when settings change because they use
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:677:  // the settings object as the cache key (new settings object = cache miss)
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:762:      // Worktree status doesn't change mid-session, so this is cached for all
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:815:  // Clear memoized caches
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:816:  checkDependencies.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\sandbox\sandbox-adapter.ts:817:  isSupportedPlatform.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:448: * described here reflect user intent. cache_control is set because the
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:450: * stable cache prefix across classifier calls.
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:452: * Reads from bootstrap/state.ts cache (populated by context.ts) instead of
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:456: * If the cache is unpopulated (tests, or an entrypoint that never calls
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:473:        cache_control: getCacheControl({ querySource: 'auto_mode' }),
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:615:    cacheReadInputTokens: result.usage.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:616:    cacheCreationInputTokens: result.usage.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:637:    cacheReadInputTokens: a.cacheReadInputTokens + b.cacheReadInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:638:    cacheCreationInputTokens:
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:639:      a.cacheCreationInputTokens + b.cacheCreationInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:746:      cache_control: getCacheControl({ querySource: 'auto_mode' }),
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1022:  // this guard the empty action block + cache_control below hits an API 400.
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1096:  const cacheControl = getCacheControl({ querySource: 'auto_mode' })
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1097:  // Place cache_control on the action block. In the two-stage classifier,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1099:  // breakpoint here gives stage 2 a guaranteed cache hit on the full prefix.
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1101:  // API limit of 4 cache_control blocks.
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1105:    cache_control: cacheControl,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1141:          cache_control: getCacheControl({ querySource: 'auto_mode' }),
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1171:      cacheReadInputTokens: result.usage.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1172:      cacheCreationInputTokens: result.usage.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1174:    // Actual total input tokens the classifier API consumed (uncached + cache)
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1177:      usage.cacheReadInputTokens +
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1178:      usage.cacheCreationInputTokens
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1183:          `(uncached=${usage.inputTokens} ` +
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1184:          `cacheRead=${usage.cacheReadInputTokens} ` +
_archive/compare_code/gg-claude-code-runnable/src\utils\permissions\yoloClassifier.ts:1185:          `cacheCreate=${usage.cacheCreationInputTokens}) ` +
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:55:import { markPluginVersionOrphaned } from './cacheUtils.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:95:  cachePath: string
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:107: * Get the path to the marketplaces cache directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:116: * This caches the marketplace in memory after loading from disk or network.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:120: * Clear all cached marketplace data (for testing)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:123:  getMarketplace.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:377: *   clear caches so earlier plugin-load passes don't keep stale "marketplace
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1067: * If the repository already exists at cachePath, pulls the latest changes.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1080: * @param cachePath - Local directory path to clone/update the repository
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1084:async function cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1086:  cachePath: string,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1096:  // TOCTOU check: gitPull returns non-zero when cachePath is missing or has no .git.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1100:    `Refreshing marketplace cache (timeout: ${timeoutSec}s)…`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1106:  const reconcileResult = await reconcileSparseCheckout(cachePath, sparsePaths)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1109:    const pullResult = await gitPull(cachePath, ref, {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1131:    await fs.rm(cachePath, { recursive: true })
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1134:      `Found stale marketplace directory at ${cachePath}, cleaning up to allow re-clone`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1145:        `Failed to clean up existing marketplace directory. Please manually delete the directory at ${cachePath} and try again.\n\nTechnical details: ${rmErrorMsg}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1148:    // ENOENT — cachePath didn't exist, this is a fresh install, nothing to clean up
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1158:  const result = await gitClone(gitUrl, cachePath, ref, sparsePaths)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1171:      await fs.rm(cachePath, { recursive: true, force: true })
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1232: * Creates the cache directory structure if it doesn't exist.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1252: * @param cachePath - Local file path to save the downloaded marketplace
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1256:async function cacheMarketplaceFromUrl(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1258:  cachePath: string,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1340:  safeCallProgress(onProgress, 'Saving marketplace to cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1341:  // Ensure cache directory exists
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1342:  const cacheDir = join(cachePath, '..')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1343:  await fs.mkdir(cacheDir)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1346:  writeFileSync_DEPRECATED(cachePath, jsonStringify(result.data, null, 2), {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1353: * Generate a cache path for a marketplace source
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1408: * Load and cache a marketplace from its source
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1417: * After loading, validates the marketplace schema and renames the cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1430: * @returns Object containing the validated marketplace and its cache path
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1438:  const cacheDir = getMarketplacesCacheDir()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1440:  // Ensure cache directory exists
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1441:  await fs.mkdir(cacheDir)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1447:  // Generate a temp name for the cache path
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1454:        temporaryCachePath = join(cacheDir, `${tempName}.json`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1456:        await cacheMarketplaceFromUrl(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1471:        temporaryCachePath = join(cacheDir, tempName)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1483:            await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1512:              await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1541:            await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1571:              await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1602:        temporaryCachePath = join(cacheDir, tempName)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1604:        await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1660:        temporaryCachePath = join(cacheDir, source.name)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1708:    // Now rename the cache path to use the marketplace's actual name
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1709:    const finalCachePath = join(cacheDir, marketplace.name)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1711:    // but verify the computed path is a strict subdirectory of cacheDir before fs.rm.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1713:    // cacheDir, nor rm cacheDir itself (e.g. name "." → join normalizes to cacheDir).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1715:    const resolvedCacheDir = resolve(cacheDir)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1718:        `Marketplace name '${marketplace.name}' resolves to a path outside the cache directory`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1729:          onProgress?.('Cleaning up old marketplace cache…')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1737:        // Rename temp cache to final name
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1744:          `Failed to finalize marketplace cache. Please manually delete the directory at ${finalCachePath} if it exists and try again.\n\nTechnical details: ${errorMsg}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1749:    return { marketplace, cachePath: temporaryCachePath }
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1761:          `Warning: Failed to clean up temporary marketplace cache at ${temporaryCachePath}: ${errorMessage(cleanupError)}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1773: * The marketplace is fetched, validated, and cached locally.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1844:  // Load and cache the marketplace to validate it and get its name
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1845:  const { marketplace, cachePath } = await loadAndCacheMarketplace(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1876:    // Clean up the old cache if it's not a user-owned local path AND it
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1877:    // actually differs from the new cachePath. loadAndCacheMarketplace writes
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1878:    // to cachePath BEFORE we get here — rm-ing the same dir deletes the fresh
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1886:    // dir. If it's outside the cache dir, skip cleanup — the stale dir (if
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1890:      const cacheDir = resolve(getMarketplacesCacheDir())
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1892:      const resolvedNew = resolve(cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1897:        resolvedOld === cacheDir ||
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1898:        resolvedOld.startsWith(cacheDir + sep)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1905:            `outside ${cacheDir}. The path is corrupted; leaving it alone and ` +
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1916:    installLocation: cachePath,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1929: * Removes the marketplace configuration and cleans up cached files.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1930: * Deletes both directory caches (for git sources) and file caches (for URL sources).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1961:  // Clean up cached files (both directory and JSON formats)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1963:  const cacheDir = getMarketplacesCacheDir()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1964:  const cachePath = join(cacheDir, name)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1965:  await fs.rm(cachePath, { recursive: true, force: true })
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:1966:  const jsonCachePath = join(cacheDir, `${name}.json`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2052: * Read a cached marketplace from disk without updating it
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2054: * @param installLocation - Path to the cached marketplace
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2077: * Get a specific marketplace by name from cache only (no network).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2078: * Returns null if cache is missing or corrupted.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2102:      `Failed to read cached marketplace ${name}: ${errorMessage(error)}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2112: * First attempts to read from cache. Only fetches from source if:
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2113: * - No cached version exists
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2149:    // Try to read from disk cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2153:      // Log cache corruption before re-fetching
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2181: * Get plugin by ID from cache only (no network calls).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2182: * Returns null if marketplace cache is missing or corrupted.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2186: * @returns The plugin entry or null if not found/cache missing
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2232: * First tries cache-only lookup. If cache is missing/corrupted,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2242:  // Try cache-only first (fast path)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2243:  const cached = await getPluginByIdCacheOnly(pluginId)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2244:  if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2245:    return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2283: * Refresh all marketplace caches
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2292: * - Ensuring caches are up-to-date before browsing
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2337:      const { cachePath } = await loadAndCacheMarketplace(entry.source)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2339:      config[name]!.installLocation = cachePath
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2354: * Refresh a single marketplace cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2359: * Clears the memoization cache and updates the lastUpdated timestamp.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2379:  // Clear the memoization cache for this specific marketplace
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2380:  getMarketplace.cache?.delete?.(name)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2409:    // marketplaces cache dir. A corrupted value (gh-32793, gh-32661 — e.g.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2411:    // user's project. cacheMarketplaceFromGit would then run git ops with that
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2415:      const cacheDir = resolve(getMarketplacesCacheDir())
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2417:      if (resolvedLoc !== cacheDir && !resolvedLoc.startsWith(cacheDir + sep)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2420:            `(${installLocation}) — expected a path inside ${cacheDir}. ` +
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2478:          await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2492:            await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2505:            await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2517:        await cacheMarketplaceFromGit(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\marketplaceManager.ts:2548:      await cacheMarketplaceFromUrl(
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\keychainPrefetch.ts:15: * getApiKeyFromConfigOrMacOSKeychain() then hit their caches.
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\keychainPrefetch.ts:112: * cache invalidation so a stale prefetch doesn't shadow a fresh write.
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:72:  cache: { data: SecureStorageData | null; cachedAt: number } // cachedAt 0 = invalid
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:73:  // Incremented on every cache invalidation. readAsync() captures this before
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:74:  // spawning and skips its cache write if a newer generation exists, preventing
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:82:  cache: { data: null, cachedAt: 0 },
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:88:  keychainCacheState.cache = { data: null, cachedAt: 0 }
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:94: * Prime the keychain cache from a prefetch result (keychainPrefetch.ts).
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:95: * Only writes if the cache hasn't been touched yet — if sync read() or
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:99:  if (keychainCacheState.cache.cachedAt !== 0) return
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainHelpers.ts:110:  keychainCacheState.cache = { data, cachedAt: Date.now() }
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:61: * Metadata stored for each cached MCPB
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:67:  cachedAt: string
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:98: * Get cache directory for MCPB files
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:101:  return join(pluginPath, '.mcpb-cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:105: * Get metadata file path for cached MCPB
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:107:function getMetadataPath(cacheDir: string, source: string): string {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:112:  return join(cacheDir, `${sourceHash}.metadata.json`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:441: * Load cache metadata for an MCPB source
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:444:  cacheDir: string,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:448:  const metadataPath = getMetadataPath(cacheDir, source)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:458:    logForDebugging(`Failed to load MCPB cache metadata: ${error}`, {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:466: * Save cache metadata for an MCPB source
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:469:  cacheDir: string,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:473:  const metadataPath = getMetadataPath(cacheDir, source)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:475:  await getFsImplementation().mkdir(cacheDir)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:627:  const cacheDir = getMcpbCacheDir(pluginPath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:628:  const metadata = await loadCacheMetadata(cacheDir, source)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:631:    // No cache metadata, needs loading
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:670:    const cachedTime = new Date(metadata.cachedAt).getTime()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:671:    // Floor to match the ms precision of cachedAt (ISO string). Sub-ms
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:672:    // precision on mtimeMs would make a freshly-cached file appear "newer"
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:673:    // than its own cache timestamp when both happen in the same millisecond.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:676:    if (fileTime > cachedTime) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:678:        `MCPB file modified: ${new Date(fileTime)} > ${new Date(cachedTime)}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:707:  const cacheDir = getMcpbCacheDir(pluginPath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:708:  await fs.mkdir(cacheDir)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:712:  // Check cache first
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:713:  const metadata = await loadCacheMetadata(cacheDir, source)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:716:      `Using cached MCPB from ${metadata.extractedPath} (hash: ${metadata.contentHash})`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:719:    // Load manifest from cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:797:  // Not cached or changed - need to download/load and extract
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:807:    mcpbFilePath = join(cacheDir, `${sourceHash}.mcpb`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:867:  // Extract to cache directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:868:  const extractPath = join(cacheDir, contentHash)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:884:      // Save cache metadata even though config is incomplete
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:889:        cachedAt: new Date().toISOString(),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:892:      await saveCacheMetadata(cacheDir, source, newMetadata)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:923:    // Save cache metadata
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:928:      cachedAt: new Date().toISOString(),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:931:    await saveCacheMetadata(cacheDir, source, newMetadata)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:948:  // Save cache metadata
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:953:    cachedAt: new Date().toISOString(),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpbHandler.ts:956:  await saveCacheMetadata(cacheDir, source, newMetadata)
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:29:    const prev = keychainCacheState.cache
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:30:    if (Date.now() - prev.cachedAt < KEYCHAIN_CACHE_TTL_MS) {
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:44:        keychainCacheState.cache = { data, cachedAt: Date.now() }
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:54:    // cache and surface as "Not logged in" across all subsystems until the
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:58:      logForDebugging('[keychain] read failed; serving stale cache', {
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:61:      keychainCacheState.cache = { data: prev.data, cachedAt: Date.now() }
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:64:    keychainCacheState.cache = { data: null, cachedAt: Date.now() }
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:68:    const prev = keychainCacheState.cache
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:69:    if (Date.now() - prev.cachedAt < KEYCHAIN_CACHE_TTL_MS) {
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:78:      // If the cache was invalidated or updated while we were reading,
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:83:          logForDebugging('[keychain] readAsync failed; serving stale cache', {
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:88:        keychainCacheState.cache = { data: next, cachedAt: Date.now() }
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:98:    // Invalidate cache before update
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:152:      // Update cache with new data on success
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:153:      keychainCacheState.cache = { data, cachedAt: Date.now() }
_archive/compare_code/gg-claude-code-runnable/src\utils\secureStorage\macOsKeychainStorage.ts:160:    // Invalidate cache before delete
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\mcpPluginIntegration.ts:597:  // Use cached servers if available
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionEnvironment.ts:12:// string = loaded and cached (use cached value)
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionEnvironment.ts:56:  logForDebugging('Invalidating session environment cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceGcs.ts:25:// `{sha}.zip` is content-addressed so CDN can cache it indefinitely;
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceGcs.ts:41: * @param marketplacesCacheDir the plugins marketplace cache root — passed in
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceGcs.ts:54:  // user's project. Refuse any path outside the marketplaces cache dir.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceGcs.ts:57:  const cacheDir = resolve(marketplacesCacheDir)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceGcs.ts:59:  if (resolvedLoc !== cacheDir && !resolvedLoc.startsWith(cacheDir + sep)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceGcs.ts:61:      `fetchOfficialMarketplaceFromGcs: refusing path outside cache dir: ${installLocation}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceGcs.ts:79:    // 1. Latest pointer — ~40 bytes, backend sets Cache-Control: no-cache,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceStartupCheck.ts:221:    const cacheDir = getMarketplacesCacheDir()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceStartupCheck.ts:222:    const installLocation = join(cacheDir, OFFICIAL_MARKETPLACE_NAME)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\officialMarketplaceStartupCheck.ts:225:      cacheDir,
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionIngressAuth.ts:16: * Uses global state to cache the result since file descriptors can only be read once.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionIngressAuth.ts:20:  const cachedToken = getSessionIngressToken()
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionIngressAuth.ts:21:  if (cachedToken !== undefined) {
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionIngressAuth.ts:22:    return cachedToken
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionIngressAuth.ts:96: *     read once and cached.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:11: * `--glob '!<dir>/**'` patterns for their parent directories. The cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:22:// Inlined from cacheUtils.ts to avoid a circular dep through commands.js.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:25:/** Session-scoped cache. Frozen once computed — only cleared by explicit /reload-plugins. */
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:26:let cachedExclusions: string[] | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:32: *   search overlaps the plugin cache directory (avoids unnecessary --glob
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:33: *   args for searches outside the cache).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:41:  const cachePath = normalize(join(getPluginsDirectory(), 'cache'))
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:43:  if (searchPath && !pathsOverlap(searchPath, cachePath)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:47:  if (cachedExclusions !== null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:48:    return cachedExclusions
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:52:    // Find all .orphaned_at files within the plugin cache directory.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:55:    // cache/<marketplace>/<plugin>/<version>/.orphaned_at — don't recurse
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:68:      cachePath,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:72:    cachedExclusions = markers.map(markerPath => {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:76:        ? relative(cachePath, versionDir)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:82:    return cachedExclusions
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:85:    cachedExclusions = []
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:86:    return cachedExclusions
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\orphanedPluginFilter.ts:91:  cachedExclusions = null
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:263:  getAgentDefinitionsWithOverrides.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:345:    // Directory is gone. Override the stale cache so the next
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:360:  // The /resume slash command calls this mid-session after caches have been
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:362:  // (caches aren't populated yet there).
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:365:  getPlansDirectory.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:385:  // Worktree state changed, so cached prompt sections that reference it are
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:389:  getPlansDirectory.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:459:    // → they're classified as FROZEN → full content sent (cache miss, permanent
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:469:  // strip worktreeSession from the fork path so the cache stays unset.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:476:    // Done after restoreSessionMetadata (which caches the worktree state
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionRestore.ts:478:    // the cache before adoptResumedSessionFile writes it.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStart.ts:63:    // with negligible overhead (just a cache lookup).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginAutoupdate.ts:155: *   version cache dir but installed_plugins.json stayed on the old version,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginDirectories.ts:71: * and plugin caches found in the seed are used in place without re-cloning.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginDirectories.ts:75: * seed that contains a given marketplace or plugin cache wins.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginDirectories.ts:81: *     cache/<marketplace>/<plugin>/<version>/...
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginDirectories.ts:93:  // Same character class as the install-cache sanitizer (pluginLoader.ts)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginDirectories.ts:104: * ${CLAUDE_PLUGIN_DATA}. Unlike the version-scoped install cache
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:435:// cache clear needed.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:533:  // Minimal cache for current session only (not all sessions)
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:694:   * Re-append cached session metadata to the end of the transcript file.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:707:   * before re-appending, refresh the cache from the tail scan window. If an
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:709:   * our stale cache absorbs it and the re-append below persists it — not
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:711:   * written by the SDK), the cache is the only source of truth and is
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:719:   * external-writer concern — their caches are authoritative.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:728:    // failure → extract returns null → cache is the only source of truth.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:731:    // Absorb any fresher SDK-written title/tag into our cache. If the SDK
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:732:    // wrote while we had the session open, our cache is stale — the tail
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:734:    // written externally), the cache stands.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:748:        // external writer with customTitle:"" should clear the cache so the
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:774:    // Unconditional: cache was refreshed from tail above; re-append keeps
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:973:   * Create the session file, write cached startup metadata, and flush
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:982:    // mode/agentSetting are cache-only pre-materialization; write them now.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:1288:    const cached = this.existingSessionFiles.get(sessionId)
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:1289:    if (cached) return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:1513: * sessionId, and the cache holds the final metadata (--name title, resumed
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:1520: * the in-memory cache is correct but never written. The resumed file
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:1524: * skipTitleRefresh: restoreSessionMetadata populated the cache from the
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:1527: * CLI title with the stale disk value. After this write, disk == cache and
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:1934:            cache_creation_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:1935:            cache_read_input_tokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2648: *   caches an AI title and `reAppendSessionMetadata` never re-appends one
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2732:  // Only returns tag for current session (the only one we cache)
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2742:  // Only returns title for current session (the only one we cache)
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2754: * Restore session metadata into in-memory cache on resume.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2755: * Populates the cache so metadata is available for display (e.g. the
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2771:  // ??= so --name (cacheSessionTitle) wins over the resumed
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2788: * Clear all cached session metadata (title, tag, agent name/color).
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2808: * Re-append cached session metadata (custom title, tag) to the end of the
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:2870:export function cacheSessionTitle(customTitle: string): void {
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:3851: * Clear the memoized session messages cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:3855:  getSessionMessages.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:3887:  // Prime getSessionMessages cache so recordTranscript (called after REPL
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:3889:  // Guard: only prime if cache is empty. Mid-session callers (e.g. IssueFeedback)
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:3890:  // may call getLastSessionLog on the current session — overwriting a live cache
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:3892:  if (!getSessionMessages.cache.has(sessionId)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\sessionStorage.ts:3893:    getSessionMessages.cache.set(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:9: * Uses a module-level cache so that getFlaggedPlugins() can be called
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:10: * synchronously during React render. The cache is populated on the first
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:33:// Module-level cache — populated by loadFlaggedPlugins(), updated by writes.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:34:let cache: Record<string, FlaggedPlugin> | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:101:    cache = plugins
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:113: * Load flagged plugins from disk into the module cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:132:  cache = all
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:139: * Get all flagged plugins from the in-memory cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:143:  return cache ?? {}
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:152:  if (cache === null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:153:    cache = await readFromDisk()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:157:    ...cache,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:175:  if (cache === null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:176:    cache = await readFromDisk()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:181:  const updated = { ...cache }
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:200:  if (cache === null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:201:    cache = await readFromDisk()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:203:  if (!(pluginId in cache)) return
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:205:  const { [pluginId]: _, ...rest } = cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginFlagging.ts:206:  cache = rest
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:25:import { clearAllCaches } from './cacheUtils.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:44:  cachePlugin,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:113: * 1. Caching a plugin to ~/.claude/plugins/cache/
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:117: * (with object source like {source: "github", ...}) are cached to the same
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:128:export async function cacheAndRegisterPlugin(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:136:  // Cast to PluginSource since cachePlugin handles any string path at runtime
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:142:  const cacheResult = await cachePlugin(source, {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:147:  // because the cached temp directory doesn't have .git (it's copied from a
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:149:  // cached path. For git-subdir sources, cachePlugin already captured the SHA
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:151:  const pathForGitSha = localSourcePath || cacheResult.path
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:153:    cacheResult.gitCommitSha ?? (await getGitCommitSha(pathForGitSha))
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:159:    cacheResult.manifest,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:162:    cacheResult.gitCommitSha,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:165:  // Move the cached plugin to the versioned path: cache/marketplace/plugin/version/
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:167:  let finalPath = cacheResult.path
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:169:  // Only move if the paths are different and plugin was cached to a different location
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:170:  if (cacheResult.path !== versionedPath) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:177:    // Check if versionedPath is a subdirectory of cacheResult.path
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:180:    const normalizedCachePath = cacheResult.path.endsWith(sep)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:181:      ? cacheResult.path
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:182:      : cacheResult.path + sep
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:188:      // Use the parent of cacheResult.path (same filesystem) to avoid EXDEV
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:191:        dirname(cacheResult.path),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:194:      await rename(cacheResult.path, tempPath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:198:      // Move the cached plugin to the versioned location
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:199:      await rename(cacheResult.path, versionedPath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:204:  // Zip cache mode: convert directory to ZIP and remove the directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:232: * External plugins should use cacheAndRegisterPlugin() instead.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:340: *   5. Clears memoization caches.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:370:  // depInfo caches marketplace lookups so the materialize loop doesn't
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:379:  // sees "Successfully installed" while nothing is cached.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:446:  // ── Materialize: cache each closure member ──
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:451:    // for a non-local source). Fetch now; it's needed for the cache write.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginInstallationHelpers.ts:466:    await cacheAndRegisterPlugin(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:124: * Get the path where plugin cache is stored
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:127:  return join(getPluginsDirectory(), 'cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:131: * Compute the versioned cache path under a specific base plugins directory.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:132: * Used to probe both primary and seed caches.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:157:    'cache',
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:165: * Get versioned cache path for a plugin under the primary plugins directory.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:166: * Format: ~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:180: * Get versioned ZIP cache path for a plugin.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:181: * This is the zip cache variant of getVersionedCachePath.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:191: * Probe seed directories for a populated cache at this plugin version.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:212: * When the computed version is 'unknown', probe seed/cache/<m>/<p>/ for an
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:241: * Get legacy (non-versioned) cache path for a plugin.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:242: * Format: ~/.claude/plugins/cache/{plugin-name}/
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:250:  const cachePath = getPluginCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:251:  return join(cachePath, pluginName.replace(/[^a-zA-Z0-9\-_]/g, '-'))
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:351: * Copy plugin files to versioned cache directory.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:361: * @returns Path to the cached plugin directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:372:  // When zip cache is enabled, the canonical format is a ZIP file
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:374:  const cachePath = getVersionedCachePath(pluginId, version)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:377:  // If cache already exists (directory or ZIP), return it
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:381:        `Plugin ${pluginId} version ${version} already cached at ${zipPath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:385:  } else if (await pathExists(cachePath)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:386:    const entries = await readdir(cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:389:        `Plugin ${pluginId} version ${version} already cached at ${cachePath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:391:      return cachePath
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:395:      `Removing empty cache directory for ${pluginId} at ${cachePath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:397:    await rmdir(cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:400:  // Seed cache hit — return seed path in place (read-only, no copy).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:405:      `Using seed cache for ${pluginId}@${version} at ${seedPath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:411:  await getFsImplementation().mkdir(dirname(cachePath))
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:422:      await copyDir(sourceDir, cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:437:      `Copying plugin ${pluginId} to versioned cache (fallback to full copy)`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:439:    await copyDir(sourcePath, cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:442:  // Remove .git directory from cache if present
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:443:  const gitPath = join(cachePath, '.git')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:446:  // Validate that cache has content - if empty, throw so fallback can be used
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:447:  const cacheEntries = await readdir(cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:448:  if (cacheEntries.length === 0) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:450:      `Failed to copy plugin ${pluginId} to versioned cache: destination is empty after copy`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:454:  // Zip cache mode: convert directory to ZIP and remove the directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:456:    await convertDirectoryToZipInPlace(cachePath, zipPath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:458:      `Successfully cached plugin ${pluginId} as ZIP at ${zipPath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:463:  logForDebugging(`Successfully cached plugin ${pluginId} at ${cachePath}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:464:  return cachePath
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:490: * Install a plugin from npm using a global cache (exported for testing)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:497:  const npmCachePath = join(getPluginsDirectory(), 'npm-cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:508:    logForDebugging(`Installing npm package ${packageSpec} to cache`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:522:    `Copied npm package ${packageName} from cache to ${targetPath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:871: * Generate a temporary cache name for a plugin
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:911:export async function cachePlugin(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:917:  const cachePath = getPluginCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:919:  await getFsImplementation().mkdir(cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:922:  const tempPath = join(cachePath, tempName)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:1077:      description: `Plugin cached from ${typeof source === 'string' ? source : source.source}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:1082:  const finalPath = join(cachePath, finalName)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:1085:    logForDebugging(`Removing old cached version at ${finalPath}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:1091:  logForDebugging(`Successfully cached plugin ${manifest.name} to ${finalPath}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:1884: * cache-only per-entry loader. The ONLY difference between loadAllPlugins
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:1889:  cacheOnly,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:1891:  cacheOnly: boolean
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:1957:  // Look up installed versions once so the first-pass ZIP cache check
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2048:      // installed_plugins.json records what's actually cached on disk
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2050:      // the cache-only loader's direct read).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2052:      return cacheOnly
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2094: * Skips network (cachePlugin) and disk-copy (copyPluginToVersionedCache).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2096: * 'plugin-cache-miss'. Still extracts ZIP-cached plugins (local, fast).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2118:        type: 'plugin-cache-miss',
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2132:        type: 'plugin-cache-miss',
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2142:  // Zip cache extraction — must still happen in cacheOnly mode (invariant 4)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2157:        type: 'plugin-cache-miss',
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2181: * - npm/github/url: Caches then loads from cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2184: *   first-pass hint for the versioned cache lookup when the marketplace entry
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2227:    // Always copy local plugins to versioned cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2256:      // Copy to versioned cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2266:        `Resolved local plugin ${entry.name} to versioned cache: ${pluginPath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2272:        `Failed to copy plugin ${entry.name} to versioned cache: ${errorMsg}. Using marketplace path.`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2278:    // External source (npm, github, url, pip) - always use versioned cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2283:      //    exact value the post-clone call at cached.gitCommitSha would see),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2296:      // Check for cached version — ZIP file (zip cache mode) or directory
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2300:          `Using versioned cached plugin ZIP ${entry.name} from ${zipPath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2305:          `Using versioned cached plugin ${entry.name} from ${versionedPath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2309:        // Seed cache probe (CCR pre-baked images, read-only). Seed content is
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2311:        // is what the image builder put there. Primary cache is NOT probed
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2323:            `Using seed cache for external plugin ${entry.name} at ${seedPath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2326:          // Download to temp location, then copy to versioned cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2327:          const cached = await cachePlugin(entry.source, {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2333:          // recomputation with cached.manifest can return a DIFFERENT value
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2335:          // which would cache at e.g. "2.0.0/" while every warm start
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2345:                  cached.manifest,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2346:                  cached.path,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2348:                  cached.gitCommitSha,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2351:          // Copy to versioned cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2354:            cached.path,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2362:          if (cached.path !== pluginPath) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2363:            await rm(cached.path, { recursive: true, force: true })
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2369:      logForDebugging(`Failed to cache plugin ${entry.name}: ${errorMsg}`, {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2376:        error: `Failed to download/cache plugin ${entry.name}: ${errorMsg}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2382:  // Zip cache mode: extract ZIP to session temp dir before loading
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2415: * Once pluginPath is resolved (via clone, cache, or installPath lookup),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:2417: * entry supplementation — is identical. Extracted so the cache-only path
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3098:    loadPluginsFromMarketplaces({ cacheOnly: false }),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3100:  // A fresh full-load result is strictly valid for cache-only callers
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3106:  loadAllPluginsCacheOnly.cache?.set(undefined, Promise.resolve(result))
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3114: * hits the network (no cachePlugin, no copyPluginToVersionedCache). Reads
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3116: * 'plugin-cache-miss' and are skipped.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3126: * BEFORE runHeadless() can warm this cache. First-run CCR/headless has
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3127: * no installed_plugins.json, so cache-only would miss plugin MCP servers
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3131: * Separate memoize cache from loadAllPlugins — a cache-only result must
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3133: * loadAllPlugins warms this cache on completion so refresh paths that run
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3134: * the full loader don't get plugin-cache-miss from their downstream
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3135: * cache-only consumers.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3143:      loadPluginsFromMarketplaces({ cacheOnly: true }),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3152: * session plugins, builtins, merge, verifyAndDemote, and cachePluginSettings
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3204:  cachePluginSettings(enabledPlugins)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3214: * Clears the memoized plugin cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3228:      `clearPluginCache: invalidating loadAllPlugins cache (${reason})`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3231:  loadAllPlugins.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3232:  loadAllPluginsCacheOnly.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3233:  // If a plugin previously contributed settings, the session settings cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3234:  // holds a merged result that includes them. cachePluginSettings() on reload
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3235:  // won't bust the cache when the new base is empty (the startup perf win),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3242:  // TODO: Clear installed plugins cache when installedPluginsManager is implemented
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3278: * Store merged plugin settings in the synchronous cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3281:export function cachePluginSettings(plugins: LoadedPlugin[]): void {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginLoader.ts:3284:  // Only bust the session settings cache if there are actually plugin settings
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\applySettingsChange.ts:24: * The settings cache is reset by the notifier (changeDetector.fanOut) before
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\applySettingsChange.ts:26: * state. Previously this function reset the cache itself, which — combined
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\applySettingsChange.ts:30: * Side-effects like clearing auth caches and applying env vars are handled by
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\changeDetector.ts:405:          // Update the cache so sync readers pick up new values
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\changeDetector.ts:421: * Reset the settings cache, then notify all listeners.
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\changeDetector.ts:423: * The cache reset MUST happen here (single producer), not in each listener
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\changeDetector.ts:428: * subscribed: each listener cleared the cache, re-read from disk (populating
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\changeDetector.ts:435: * repopulates; all subsequent listeners hit the cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginOptionsStorage.ts:64:    // session-lifetime) + keychain's own 30s TTL cache — so one blocking spawn
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginOptionsStorage.ts:80:  loadPluginOptions.cache?.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginOptionsStorage.ts:88: * Clears the load cache on success so the next `loadPluginOptions` sees fresh.
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\powershellDetection.ts:59:let cachedPowerShellPath: Promise<string | null> | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\powershellDetection.ts:62: * Gets the cached PowerShell path. Returns a memoized promise that
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\powershellDetection.ts:66:  if (!cachedPowerShellPath) {
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\powershellDetection.ts:67:    cachedPowerShellPath = findPowerShell()
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\powershellDetection.ts:69:  return cachedPowerShellPath
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\powershellDetection.ts:103: * Resets the cached PowerShell path. Only for testing.
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\powershellDetection.ts:106:  cachedPowerShellPath = null
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginStartupCheck.ts:24:  cacheAndRegisterPlugin,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginStartupCheck.ts:308:        // External plugin - cache and register it with scope
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginStartupCheck.ts:309:        await cacheAndRegisterPlugin(pluginId, entry, scope, projectPath)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:5: * Versions are used for versioned cache paths and update detection.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:64:      // Encode the subdir path in the version so cache keys differ when
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:67:      // collide at cache/<m>/<p>/<sha>/ and serve each other's trees.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:119: * Extract version from a versioned cache path.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:121: * Given a path like `~/.claude/plugins/cache/marketplace/plugin/1.0.0`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:128:  // Versioned paths have format: .../plugins/cache/marketplace/plugin/version/
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:131:  // Find 'cache' index to determine depth
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:132:  const cacheIndex = parts.findIndex(
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:133:    (part, i) => part === 'cache' && parts[i - 1] === 'plugins',
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:136:  if (cacheIndex === -1) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:140:  // Versioned path has 3 components after 'cache': marketplace/plugin/version
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\pluginVersioning.ts:141:  const componentsAfterCache = parts.slice(cacheIndex + 1)
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:182:  const cached = getCachedParsedFile(path)
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:183:  if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:184:    // Clone so callers (e.g. mergeWith in getSettingsForSourceUncached,
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:185:    // updateSettingsForSource) can't mutate the cached entry.
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:187:      settings: cached.settings ? clone(cached.settings) : null,
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:188:      errors: cached.errors,
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:191:  const result = parseSettingsFileUncached(path)
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:194:  // another caller reads the same cache entry.
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:201:function parseSettingsFileUncached(path: string): {
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:312:  const cached = getCachedSettingsForSource(source)
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:313:  if (cached !== undefined) return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:314:  const result = getSettingsForSourceUncached(source)
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:319:function getSettingsForSourceUncached(
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:437:    // cache — mergeWith below mutates its target (including nested refs),
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:438:    // and mutating the cached object would leak unpersisted state if the
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:440:    let existingSettings = getSettingsForSourceUncached(source)
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:505:    // Invalidate the session cache since settings have been updated
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:642: * Load settings from disk without using cache
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:833: * Always reads fresh from disk — resets the session cache so that `effective`
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:837:  // Reset both caches so getSettingsForSource (per-source cache) and
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:838:  // getInitialSettings (session cache) agree on the current disk state.
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:853: * Settings changes require Claude Code restart, so cache is valid for entire session.
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:857:  // Use cached result if available
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:858:  const cached = getSessionSettingsCache()
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:859:  if (cached !== null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:860:    return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settings.ts:863:  // Load from disk and cache the result
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuery.ts:40:  /** Messages to send (supports cache_control on content blocks) */
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuery.ts:213:    cachedInputTokens: response.usage.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuery.ts:214:    uncachedInputTokens: response.usage.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\prefix.ts:84: * and attaches a .catch handler that evicts the cache entry on rejection.
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\prefix.ts:115:        if (memoized.cache.get(command) === promise) {
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\prefix.ts:116:          memoized.cache.delete(command)
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\prefix.ts:132: * a .catch handler evicts the cache entry on rejection to prevent poisoning.
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\prefix.ts:159:        if (memoized.cache.get(command) === promise) {
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\prefix.ts:160:          memoized.cache.delete(command)
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\mdm\settings.ts:50:// Types and cache
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\mdm\settings.ts:112:// Sync cache readers — used by the settings pipeline (loadSettingsFromDisk)
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\mdm\settings.ts:116: * Read admin-controlled MDM settings from the session cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\mdm\settings.ts:141: * Clear the MDM and HKCU settings caches, forcing a fresh read on next load.
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\mdm\settings.ts:150: * Update the session caches directly. Used by the change detector poll.
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\mdm\settings.ts:164: * Does NOT update the cache — caller decides whether to apply.
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuestion.ts:50: * Shares the parent's prompt cache — no thinking override, no cache write.
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuestion.ts:55:  cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuestion.ts:58:  cacheSafeParams: CacheSafeParams
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuestion.ts:82:    // Do NOT override thinkingConfig — thinking is part of the API cache key,
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuestion.ts:83:    // and diverging from the main thread's config busts the prompt cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuestion.ts:85:    cacheSafeParams,
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuestion.ts:94:    // No future request shares this suffix; skip writing cache entries.
_archive/compare_code/gg-claude-code-runnable/src\utils\sideQuestion.ts:109: * thread to preserve the cache key), a thinking response arrives as:
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settingsCache.ts:16: * Per-source cache for getSettingsForSource. Invalidated alongside the
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settingsCache.ts:25:  // undefined = cache miss; null = cached "no settings for this source"
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\settingsCache.ts:37: * Path-keyed cache for parseSettingsFile. Both getSettingsForSource and
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\reconciler.ts:86:  /** Skip a declared marketplace. Used by zip-cache mode for unsupported source types. */
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\readOnlyCommandValidation.ts:143:      '--cached': 'none',
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\readOnlyCommandValidation.ts:411:      '--cached': 'none',
_archive/compare_code/gg-claude-code-runnable/src\utils\shell\readOnlyCommandValidation.ts:682:      '--cached': 'none',
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:30:import { clearAllCaches } from './cacheUtils.js'
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:61: * trigger, AppState plugin arrays. Clears ALL plugin caches (unlike the old
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:75:  logForDebugging('refreshActivePlugins: clearing all plugin caches')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:81:  // Sequence the full load before cache-only consumers. Before #23693 all
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:85:  // read installed_plugins.json before loadAllPlugins() has cloned+cached
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:86:  // the plugin, returning plugin-cache-miss. loadAllPlugins warms the
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:87:  // cache-only memoize on completion, so the awaits below are ~free.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:97:  // cache slots NOT filled by loadAllPlugins() — they're written later by
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\refresh.ts:99:  // Loading here gives accurate metrics AND warms the cache slots so the MCP
_archive/compare_code/gg-claude-code-runnable/src\utils\skills\skillChangeDetector.ts:93:      // Clear memoization caches so new skills are picked up
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\types.ts:100:        'Local cache path where marketplace manifest is stored (auto-generated if not provided)',
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\types.ts:446:                'Common examples: "node_modules", ".cache", ".bin"',
_archive/compare_code/gg-claude-code-runnable/src\utils\settings\types.ts:577:          // installed++ anyway → pointless cache clears. For github/git/url the
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:211: * to join(cacheDir, source.name) BEFORE the post-write PluginMarketplaceSchema
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:213: * PluginMarketplaceSchema leaves orphaned files in the cache (cleanupNeeded=false).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:1039:          'The reconciler writes a synthetic marketplace.json to the cache; ' +
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:1229: * it lives outside the plugins cache dir and marketplace operations on it are
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:1231: * is a cache-dir entry managed by Claude Code and subject to rm/re-clone.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:1583: * Each entry contains the source location, cache path, and last update time.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:1588: *   "installLocation": "/home/user/.claude/plugins/cached/marketplaces/anthropic-tools",
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:1599:      .describe('Local cache path where marketplace manifest is stored'),
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\schemas.ts:1615: * Maps marketplace names to their source and cache metadata.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:16: * Directory structure of the zip cache:
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:17: * /mnt/plugins-cache/
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:53: * Check if the plugin zip cache mode is enabled.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:60: * Get the path to the zip cache directory.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:62: * Returns undefined if zip cache is not enabled.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:73: * Get the path to known_marketplaces.json in the zip cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:76:  const cachePath = getPluginZipCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:77:  if (!cachePath) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:78:    throw new Error('Plugin zip cache is not enabled')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:80:  return join(cachePath, 'known_marketplaces.json')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:84: * Get the path to installed_plugins.json in the zip cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:87:  const cachePath = getPluginZipCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:88:  if (!cachePath) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:89:    throw new Error('Plugin zip cache is not enabled')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:91:  return join(cachePath, 'installed_plugins.json')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:95: * Get the marketplaces directory within the zip cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:98:  const cachePath = getPluginZipCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:99:  if (!cachePath) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:100:    throw new Error('Plugin zip cache is not enabled')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:102:  return join(cachePath, 'marketplaces')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:106: * Get the plugins directory within the zip cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:109:  const cachePath = getPluginZipCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:110:  if (!cachePath) {
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:111:    throw new Error('Plugin zip cache is not enabled')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:113:  return join(cachePath, 'plugins')
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:116:// Session plugin cache: a temp directory on local disk (NOT in the mounted zip cache)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:122: * Get or create the session plugin cache directory.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:135:      logForDebugging(`Created session plugin cache at ${dir}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:143: * Clean up the session plugin cache directory.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:153:      `Cleaned up session plugin cache at ${sessionPluginCachePath}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:156:    logForDebugging(`Failed to clean up session plugin cache: ${error}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:164: * Reset the session plugin cache path (for testing).
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:172: * Write data to a file in the zip cache atomically.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:368: * Both call sites (cacheAndRegisterPlugin, copyPluginToVersionedCache) need the
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:369: * same sequence; getting it wrong (non-atomic write, forgetting rm) corrupts cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:381: * Get the relative path for a marketplace JSON file within the zip cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:392: * Check if a marketplace source type is supported by zip cache mode.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:394: * Supported sources write to `join(cacheDir, name)` — syncMarketplacesToZipCache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:396: * - github/git/url: clone to temp, rename into cacheDir
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:397: * - settings: write synthetic marketplace.json directly to cacheDir (no fetch)
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCache.ts:399: * Excluded: file/directory (installLocation is the user's path OUTSIDE cacheDir —
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:4: * I/O helpers for the plugin zip cache. These functions handle reading/writing
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:5: * zip-cache-local metadata files, extracting ZIPs to session directories,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:8: * The zip cache stores data on a mounted volume (e.g., Filestore) that persists
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:9: * across ephemeral container lifetimes. The session cache is a local temp dir
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:34: * Read known_marketplaces.json from the zip cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:44:        `Invalid known_marketplaces.json in zip cache: ${parsed.error.message}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:56: * Write known_marketplaces.json to the zip cache atomically.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:70: * Read a marketplace JSON file from the zip cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:98: * Save a marketplace JSON to the zip cache from its install location.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:137: * Sync marketplace data to zip cache for offline access.
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:138: * Saves marketplace JSONs and merges with previously cached data
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:147:  // Save marketplace JSONs to zip cache
_archive/compare_code/gg-claude-code-runnable/src\utils\plugins\zipCacheAdapters.ts:157:  // Merge with previously cached data (ephemeral containers lose global config)
_archive/compare_code/gg-claude-code-runnable/src\utils\startupProfiler.ts:44:// plugins reset the settings cache), and the second call would overwrite the
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:322:                cacheReadInputTokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:323:                cacheCreationInputTokens: 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:333:            modelUsageAgg[model]!.cacheReadInputTokens +=
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:334:              usage.cache_read_input_tokens || 0
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:335:            modelUsageAgg[model]!.cacheCreationInputTokens +=
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:336:              usage.cache_creation_input_tokens || 0
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:440:function cacheToStats(
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:441:  cache: PersistedStatsCache,
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:444:  // Merge cache with today's stats
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:446:  for (const day of cache.dailyActivity) {
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:463:  for (const day of cache.dailyModelTokens) {
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:480:  const modelUsage = { ...cache.modelUsage }
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:487:          cacheReadInputTokens:
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:488:            modelUsage[model]!.cacheReadInputTokens +
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:489:            usage.cacheReadInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:490:          cacheCreationInputTokens:
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:491:            modelUsage[model]!.cacheCreationInputTokens +
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:492:            usage.cacheCreationInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:513:  for (const [hour, count] of Object.entries(cache.hourCounts)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:533:  // Compute session aggregates: combine cache aggregates with today's stats
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:535:    cache.totalSessions + (todayStats?.sessionStats.length || 0)
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:536:  const totalMessages = cache.totalMessages + (todayStats?.totalMessages || 0)
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:538:  // Find longest session (compare cache's longest with today's sessions)
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:539:  let longestSession = cache.longestSession
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:549:  let firstSessionDate = cache.firstSessionDate
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:590:    cache.totalSpeculationTimeSavedMs +
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:612:      ...(cache.shotDistribution || {}),
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:638: * Uses a disk cache to avoid reprocessing historical data.
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:647:  // Use lock to prevent race conditions with background cache updates
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:649:    // Load the cache
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:650:    const cache = await loadStatsCache()
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:654:    // - If no cache: process everything up to yesterday, then today separately
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:655:    // - If cache exists: process from day after lastComputedDate to yesterday, then today
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:656:    let result = cache
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:658:    if (!cache.lastComputedDate) {
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:659:      // No cache - process all historical data (everything before today)
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:660:      logForDebugging('Stats cache empty, processing all historical data')
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:669:        result = mergeCacheWithNewStats(cache, historicalStats, yesterday)
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:672:    } else if (isDateBefore(cache.lastComputedDate, yesterday)) {
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:675:      const nextDay = getNextDay(cache.lastComputedDate)
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:677:        `Stats cache stale (${cache.lastComputedDate}), processing ${nextDay} to ${yesterday}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:688:        result = mergeCacheWithNewStats(cache, newStats, yesterday)
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:692:        result = { ...cache, lastComputedDate: yesterday }
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:701:  // This doesn't need to be in the lock since it doesn't modify the cache
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:708:  // Combine cache with today's stats
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:709:  return cacheToStats(updatedCache, todayStats)
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:716: * For 'all', uses the cached aggregation. For other ranges, processes files directly.
_archive/compare_code/gg-claude-code-runnable/src\utils\stats.ts:747: * Used for filtered date ranges that bypass the cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:16:const STATS_CACHE_FILENAME = 'stats-cache.json'
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:19: * Simple in-memory lock to prevent concurrent cache operations.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:24: * Execute a function while holding the stats cache lock.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:49: * Persisted stats cache stored on disk.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:99: * Migrate an older cache to the current schema.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:138:    // check in loadStatsCache fires for v1/v2 caches that lacked this field.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:144: * Load the stats cache from disk.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:145: * Returns an empty cache if the file doesn't exist or is invalid.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:149:  const cachePath = getStatsCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:152:    const content = await fs.readFile(cachePath, { encoding: 'utf-8' })
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:160:          `Stats cache version ${parsed.version} not migratable (expected ${STATS_CACHE_VERSION}), returning empty cache`,
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:165:        `Migrated stats cache from v${parsed.version} to v${STATS_CACHE_VERSION}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:174:          'Migrated stats cache missing shotDistribution, forcing recomputation',
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:189:        'Stats cache has invalid structure, returning empty cache',
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:194:    // If SHOT_STATS is enabled but cache doesn't have shotDistribution,
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:198:        'Stats cache missing shotDistribution, forcing recomputation',
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:205:    logForDebugging(`Failed to load stats cache: ${errorMessage(error)}`)
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:211: * Save the stats cache to disk atomically.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:215:  cache: PersistedStatsCache,
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:218:  const cachePath = getStatsCachePath()
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:219:  const tempPath = `${cachePath}.${randomBytes(8).toString('hex')}.tmp`
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:231:    const content = jsonStringify(cache, null, 2)
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:241:    await fs.rename(tempPath, cachePath)
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:243:      `Stats cache saved successfully (lastComputedDate: ${cache.lastComputedDate})`,
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:257: * Merge new stats into an existing cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:258: * Used when incrementally adding new days to the cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:312:        cacheReadInputTokens:
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:313:          modelUsage[model]!.cacheReadInputTokens + usage.cacheReadInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:314:        cacheCreationInputTokens:
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:315:          modelUsage[model]!.cacheCreationInputTokens +
_archive/compare_code/gg-claude-code-runnable/src\utils\statsCache.ts:316:          usage.cacheCreationInputTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\subprocessEnv.ts:43:  // GitHub Actions artifact/cache API — cache poisoning → supply-chain pivot
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\detection.ts:123: * Resets all cached detection results. Used for testing.
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\inProcessRunner.ts:1042:    // differs → cache miss. Gated on parent to inherit feature-flag-off.
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\inProcessRunner.ts:1082:        // does not clear the main session's readFileState cache or
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:1:import { LRUCache } from 'lru-cache'
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:40:// Initialize LRU cache for directory scans
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:46:// Initialize LRU cache for path scans (files and directories)
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:82: * Uses LRU cache to avoid repeated filesystem calls
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:87:  // Check cache first
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:88:  const cached = directoryCache.get(dirPath)
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:89:  if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:90:    return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:143: * Clears the directory cache
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:166: * Uses LRU cache to avoid repeated filesystem calls
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:172:  const cacheKey = `${dirPath}:${includeHidden}`
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:173:  const cached = pathCache.get(cacheKey)
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:174:  if (cached) {
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:175:    return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:197:    pathCache.set(cacheKey, paths)
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\directoryCompletion.ts:258: * Clears both directory and path caches
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\shellHistoryCompletion.ts:26:  // Return cached result if still fresh
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\shellHistoryCompletion.ts:60: * Clear the shell history cache (useful when history is updated)
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\shellHistoryCompletion.ts:68: * Add a command to the front of the shell history cache without
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\shellHistoryCompletion.ts:69: * flushing the entire cache.  If the command already exists in the
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\shellHistoryCompletion.ts:70: * cache it is moved to the front (deduped).  When the cache hasn't
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:8: * The detected theme is cached module-level so callers can resolve 'auto'
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:9: * without awaiting the async OSC round-trip. The cache is seeded from
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:18:let cachedSystemTheme: SystemTheme | undefined
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:22: * updates the cache on live changes.
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:25:  if (cachedSystemTheme === undefined) {
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:26:    cachedSystemTheme = detectFromColorFgBg() ?? 'dark'
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:28:  return cachedSystemTheme
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:32: * Update the cached terminal theme. Called by the watcher when the OSC 11
_archive/compare_code/gg-claude-code-runnable/src\utils\systemTheme.ts:36:  cachedSystemTheme = theme
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\skillUsageTracking.ts:5:// Process-lifetime debounce cache — avoids lock + read + parse on debounced
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:26:let cachedBackend: PaneBackend | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:31:let cachedDetectionResult: BackendDetectionResult | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:41:let cachedInProcessBackend: TeammateExecutor | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:47:let cachedPaneBackendExecutor: TeammateExecutor | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:140:  // Return cached result if available
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:141:  if (cachedDetectionResult) {
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:143:      `[BackendRegistry] Using cached backend: ${cachedDetectionResult.backend.type}`,
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:145:    return cachedDetectionResult
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:164:    cachedBackend = backend
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:165:    cachedDetectionResult = {
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:170:    return cachedDetectionResult
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:192:        cachedBackend = backend
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:193:        cachedDetectionResult = {
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:198:        return cachedDetectionResult
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:215:      cachedBackend = backend
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:216:      cachedDetectionResult = {
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:221:      return cachedDetectionResult
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:242:    cachedBackend = backend
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:243:    cachedDetectionResult = {
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:248:    return cachedDetectionResult
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:305: * Gets the currently cached backend, if any.
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:309:  return cachedBackend
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:313: * Gets the cached backend detection result, if any.
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:318:  return cachedDetectionResult
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:402: * Creates and caches the instance on first call.
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:405:  if (!cachedInProcessBackend) {
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:406:    cachedInProcessBackend = createInProcessBackend()
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:408:  return cachedInProcessBackend
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:440: * Creates and caches the instance on first call, detecting the appropriate pane backend.
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:443:  if (!cachedPaneBackendExecutor) {
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:445:    cachedPaneBackendExecutor = createPaneBackendExecutor(detection.backend)
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:450:  return cachedPaneBackendExecutor
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:454: * Resets the backend detection cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:458:  cachedBackend = null
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:459:  cachedDetectionResult = null
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:460:  cachedInProcessBackend = null
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\registry.ts:461:  cachedPaneBackendExecutor = null
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:13:const cache = new Map<string, string[]>()
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:137:// Find a cached entry whose key is a prefix of mcpQuery and still has
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:138:// matches for searchToken. Lets typing "c"→"cl"→"cla" reuse the "c" cache
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:146:  for (const [key, channels] of cache) {
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:168:  let channels = cache.get(mcpQuery) ?? findReusableCacheEntry(mcpQuery, lower)
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:176:      cache.set(mcpQuery, channels)
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:183:      if (cache.size > 50) {
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:184:        cache.delete(cache.keys().next().value!)
_archive/compare_code/gg-claude-code-runnable/src\utils\suggestions\slackChannelSuggestions.ts:204:  cache.clear()
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\TmuxBackend.ts:26:let cachedLeaderWindowTarget: string | null = null
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\TmuxBackend.ts:401:    // Return cached value if available
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\TmuxBackend.ts:402:    if (cachedLeaderWindowTarget) {
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\TmuxBackend.ts:403:      return cachedLeaderWindowTarget
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\TmuxBackend.ts:423:    cachedLeaderWindowTarget = result.stdout.trim()
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\backends\TmuxBackend.ts:424:    return cachedLeaderWindowTarget
_archive/compare_code/gg-claude-code-runnable/src\utils\swarm\teammateLayoutManager.ts:12: * detectAndGetBackend() caches internally — no need for a second cache here.
_archive/compare_code/gg-claude-code-runnable/src\utils\tempfile.ts:16: *   invalidate the prompt cache prefix.
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\betaSessionTracing.ts:88:  // Gate reads from disk cache, so first run after allowlisting returns false;
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:11: * - API requests with TTFT, TTLT, prompt length, cache stats, msg ID, speculative flag
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:475:    cacheReadTokens?: number
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:476:    cacheCreationTokens?: number
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:499:  const cacheReadTokens = metadata.cacheReadTokens
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:516:  // Cache hit rate: percentage of prompt tokens from cache
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:517:  const cacheHitRate =
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:518:    cacheReadTokens !== undefined &&
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:521:      ? Math.round((cacheReadTokens / promptTokens) * 10000) / 100
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:534:    cache_read_tokens: cacheReadTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:535:    cache_creation_tokens: metadata.cacheCreationTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:544:    cache_hit_rate_pct: cacheHitRate,
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\perfettoTracing.ts:630:        cache_hit_rate_pct: cacheHitRate,
_archive/compare_code/gg-claude-code-runnable/src\utils\tmuxSocket.ts:144: * This is checked once and cached for the lifetime of the process.
_archive/compare_code/gg-claude-code-runnable/src\utils\tmuxSocket.ts:174: * Returns the cached tmux availability status.
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\sessionTracing.ts:358:    cacheReadTokens?: number
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\sessionTracing.ts:359:    cacheCreationTokens?: number
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\sessionTracing.ts:413:      cacheReadTokens: metadata?.cacheReadTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\sessionTracing.ts:414:      cacheCreationTokens: metadata?.cacheCreationTokens,
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\sessionTracing.ts:438:    if (metadata.cacheReadTokens !== undefined)
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\sessionTracing.ts:439:      endAttributes['cache_read_tokens'] = metadata.cacheReadTokens
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\sessionTracing.ts:440:    if (metadata.cacheCreationTokens !== undefined)
_archive/compare_code/gg-claude-code-runnable/src\utils\telemetry\sessionTracing.ts:441:      endAttributes['cache_creation_tokens'] = metadata.cacheCreationTokens
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:41: * Includes input_tokens + cache tokens + output_tokens.
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:49:    (usage.cache_creation_input_tokens ?? 0) +
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:50:    (usage.cache_read_input_tokens ?? 0) +
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:77: * Both paths exclude cache tokens to match #304930's formula.
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:101:      // window. Match the iterations path's formula (input + output, no cache)
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:103:      // non-cache input + output. Whether the server's budget countdown
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:104:      // (renderer.py:292 calculate_context_tokens) counts cache the same way
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:141:  cache_creation_input_tokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:142:  cache_read_input_tokens: number
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:151:        cache_creation_input_tokens: usage.cache_creation_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:152:        cache_read_input_tokens: usage.cache_read_input_tokens ?? 0,
_archive/compare_code/gg-claude-code-runnable/src\utils\tokens.ts:206: * response's token count (input + output + cache) plus estimates for any
_archive/compare_code/gg-claude-code-runnable/src\utils\toolPool.ts:63:  // Partition-sort for prompt-cache stability (same as assembleToolPool):
_archive/compare_code/gg-claude-code-runnable/src\utils\toolPool.ts:64:  // built-ins must stay a contiguous prefix for the server's cache policy.
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:50: * Defensive: GrowthBook's cache returns `cached !== undefined ? cached : default`,
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:370:// same choices every time (preserves prompt cache prefix).
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:374: * State must be stable to preserve prompt cache:
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:386: * parent's state by default (cache-sharing forks like agentSummary need
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:400: * Clone replacement state for a cache-sharing fork (e.g. agentSummary).
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:403: * prompt cache hit. Mutating the clone does not affect the source.
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:418: * check: GrowthBook's cache returns `cached !== undefined ? cached : default`,
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:473: * or path layout can't silently break prompt cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:643: *  - mustReapply: previously replaced → re-apply the cached replacement for
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:646: *    now would change a prefix that was already cached)
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:751: * re-applied every turn from the cached preview string (zero I/O,
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:753: * later (would break prompt cache).
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:757: * all prior messages just re-apply cached replacements.
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:785:  // prompt cache for already-seen content is preserved regardless.
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:789:  // (all IDs in seenIds) this just re-applies cached replacements. For the
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:838:    // full content while the main thread sends the preview → cache miss.
_archive/compare_code/gg-claude-code-runnable/src\utils\toolResultStorage.ts:941: * made in the original session (prompt cache stability).
_archive/compare_code/gg-claude-code-runnable/src\utils\toolSchemaCache.ts:3:// Session-scoped cache of rendered tool schemas. Tool schemas render at server
_archive/compare_code/gg-claude-code-runnable/src\utils\toolSchemaCache.ts:8:// bytes at first render — mid-session GB refreshes no longer bust the cache.
_archive/compare_code/gg-claude-code-runnable/src\utils\toolSearch.ts:121: * Memoized by deferred tool names — cache is invalidated when MCP servers connect/disconnect.
_archive/compare_code/gg-claude-code-runnable/src\utils\toolSearch.ts:722:  // Try exact token count first (cached, one API call per toolset change)
_archive/compare_code/gg-claude-code-runnable/src\utils\transcriptSearch.ts:20: *  cached — messages are append-only and immutable so a hit is always
_archive/compare_code/gg-claude-code-runnable/src\utils\transcriptSearch.ts:21: *  valid. Lowercased at cache time: the only caller immediately
_archive/compare_code/gg-claude-code-runnable/src\utils\transcriptSearch.ts:25:  const cached = searchTextCache.get(msg)
_archive/compare_code/gg-claude-code-runnable/src\utils\transcriptSearch.ts:26:  if (cached !== undefined) return cached
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:15:let cachedEmail: string | undefined | null = null // null means not fetched yet
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:54:  if (cachedEmail === null && !emailFetchPromise) {
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:56:    cachedEmail = await emailFetchPromise
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:58:    // Clear memoization cache so next call picks up the email
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:59:    getCoreUserData.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:64: * Reset all user data caches. Call on auth changes (login/logout/account switch)
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:68:  cachedEmail = null
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:70:  getCoreUserData.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:71:  getGitEmail.cache.clear?.()
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:138:  // Return cached email if available (from async initialization)
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:139:  if (cachedEmail !== null) {
_archive/compare_code/gg-claude-code-runnable/src\utils\user.ts:140:    return cachedEmail
_archive/compare_code/gg-claude-code-runnable/src\utils\words.ts:162:  'cached',
_archive/compare_code/gg-claude-code-runnable/src\utils\worktreeModeEnabled.ts:6: * before the cache is populated, silently swallowing --worktree.
_archive/compare_code/gg-claude-code-runnable/src\utils\xdg.ts:38: * Get XDG cache home directory
_archive/compare_code/gg-claude-code-runnable/src\utils\xdg.ts:39: * Default: ~/.cache
_archive/compare_code/gg-claude-code-runnable/src\utils\xdg.ts:44:  return env.XDG_CACHE_HOME ?? join(home, '.cache')
_archive/compare_code/gg-claude-code-runnable/src\utils\zodToJsonSchema.ts:11:// same ZodTypeAny reference per session, so we can cache by identity.
_archive/compare_code/gg-claude-code-runnable/src\utils\zodToJsonSchema.ts:12:const cache = new WeakMap<ZodTypeAny, JsonSchema7Type>()
_archive/compare_code/gg-claude-code-runnable/src\utils\zodToJsonSchema.ts:18:  const hit = cache.get(schema)
_archive/compare_code/gg-claude-code-runnable/src\utils\zodToJsonSchema.ts:21:  cache.set(schema, result)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$path='"'_archive/compare_code/gg-claude-code-runnable/src/services/api/promptCacheBreakDetection.ts'; "'$i=1; Get-Content $path | ForEach-Object { if ($i -le 240) { '"'{0,5}: {1}' -f "'$i, $_ }; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "parseMaxTokensContextOverflowError|extractNestedErrorMessage|getRetryAfter|retry-after|Retry-After|categorizeRetryable" _archive/compare_code/gg-claude-code-runnable/src/services/api/errors.ts _archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'git diff v5.0.1-block-h-plus..HEAD -- compact_v5/MAIN/agent/core/errors.py compact_v5/MAIN/agent/core/cache_break_detection.py compact_v5/MAIN/agent/core/__init__.py compact_v5/MAIN/agent/tests/integration/test_block_l.py' in D:\Github\sagemaker-coding-agent
 succeeded in 506ms:
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:284:        const retryAfterMs = getRetryAfterMs(error)
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:286:          // Short retry-after: wait and retry with fast mode still active
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:291:        // Long or unknown retry-after: enter cooldown (switches to standard
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:389:        const overflowData = parseMaxTokensContextOverflowError(error)
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:430:      // Get retry-after header if available
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:431:      const retryAfter = getRetryAfter(error)
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:450:        // Retry-After is a server directive and bypasses maxDelayMs inside
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:519:function getRetryAfter(error: unknown): string | null {
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:521:    ((error as { headers?: { 'retry-after'?: string } }).headers?.[
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:522:      'retry-after'
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:525:      ((error as APIError).headers as Headers)?.get?.('retry-after')) ??
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:550:export function parseMaxTokensContextOverflowError(error: APIError):
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:727:  if (parseMaxTokensContextOverflowError(error)) {
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:803:function getRetryAfterMs(error: APIError): number | null {
_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts:804:  const retryAfter = getRetryAfter(error)
_archive/compare_code/gg-claude-code-runnable/src/services/api/errors.ts:1163:export function categorizeRetryableAPIError(

 succeeded in 555ms:
diff --git a/compact_v5/MAIN/agent/core/__init__.py b/compact_v5/MAIN/agent/core/__init__.py
index 37cd368..c554120 100644
--- a/compact_v5/MAIN/agent/core/__init__.py
+++ b/compact_v5/MAIN/agent/core/__init__.py
@@ -15,6 +15,19 @@ from __future__ import annotations
 
 # Re-export the public surface
 from .budget import IterationBudget  # noqa: F401
-from .errors import BedrockErrorCategory, ErrorClassifier  # noqa: F401
+from .errors import (  # noqa: F401
+    BedrockErrorCategory,
+    ErrorClassifier,
+    categorize_retryable,
+    extract_nested_error_message,
+    parse_max_tokens_context_overflow_error,
+    get_retry_after_ms,
+)
+from .cache_break_detection import (  # noqa: F401
+    PerToolCacheBreakDetector,
+    is_cache_break_excluded,
+    hash_tool_schema,
+    notify_cache_deletion,
+)
 from .retry import RetryPolicy  # noqa: F401
 from .query_engine import QueryEngine, run_one_turn, count_tool_calls  # noqa: F401
diff --git a/compact_v5/MAIN/agent/core/cache_break_detection.py b/compact_v5/MAIN/agent/core/cache_break_detection.py
new file mode 100644
index 0000000..02ca35c
--- /dev/null
+++ b/compact_v5/MAIN/agent/core/cache_break_detection.py
@@ -0,0 +1,148 @@
+"""V5 core/cache_break_detection.py — Block L per-tool cache-break detection.
+
+PORT_LOG: #101.
+
+Source: Runnable services/api/cacheBreakDetection.ts.
+
+When a tool's schema changes between turns, the prompt cache is invalidated
+for that tool. This module detects per-tool schema changes by hashing each
+tool's schema and comparing against a per-engine baseline.
+
+R4 #14 MUST: Haiku-4.5 model_id is in the EXCLUDED_MODELS set — Haiku
+doesn't support prompt-cache deletion notifications, so the detector
+skips these models entirely. Bedrock returns a 400 error if you call
+notify_cache_deletion() on Haiku; the exclusion preserves API validity.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+from typing import Any, Dict, List, Optional, Set
+
+
+# Block L (R4 #14 MUST): models that don't support prompt-cache
+# deletion. Haiku 4.5 in particular: notify_cache_deletion() raises
+# ValidationException on these. Cross-region prefixes (au./apac./
+# us./eu.) are stripped before lookup.
+_EXCLUDED_MODELS_3LOC: frozenset = frozenset({
+    "anthropic.claude-haiku-4-5-20251001-v1:0",
+    "anthropic.claude-haiku-4-1-20250228-v1:0",  # also exclude prior Haiku
+    "anthropic.claude-3-5-haiku-20241022-v1:0",
+})
+
+
+def _strip_region_prefix(model_id: str) -> str:
+    """Strip cross-region inference prefixes (au./apac./us./eu./global.)
+    so the EXCLUDED_MODELS lookup matches both `au.anthropic...` and
+    `anthropic...` forms.
+    """
+    for prefix in ("au.", "apac.", "us.", "eu.", "global.", "ap.", "in."):
+        if model_id.startswith(prefix):
+            return model_id[len(prefix):]
+    return model_id
+
+
+def is_cache_break_excluded(model_id: str) -> bool:
+    """R4 #14 MUST: True iff model_id is in the cache-break-detection
+    EXCLUDED set. Haiku 4.5 in particular.
+    """
+    if not model_id:
+        return False
+    return _strip_region_prefix(model_id) in _EXCLUDED_MODELS_3LOC
+
+
+def hash_tool_schema(tool_schema: Dict[str, Any]) -> str:
+    """Stable hash of a tool schema. Two semantically identical schemas
+    (different key order) produce the same hash.
+
+    Block L per-tool detection: a tool is cache-broken iff its schema
+    hash changed between turns.
+    """
+    canonical = json.dumps(tool_schema, sort_keys=True, separators=(",", ":"))
+    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
+
+
+class PerToolCacheBreakDetector:
+    """Tracks per-tool schema hashes across turns.
+
+    Usage:
+        detector = PerToolCacheBreakDetector()
+        # Turn 1:
+        detector.update_baseline(tools)
+        # Turn 2:
+        broken = detector.detect_breaks(tools, model_id="anthropic.claude-...")
+        # broken is a list of tool names whose schemas changed.
+
+    If model_id is in the EXCLUDED set, detect_breaks() returns [] —
+    skips the entire detection path because notify_cache_deletion()
+    isn't supported on those models.
+    """
+
+    def __init__(self) -> None:
+        self._baseline: Dict[str, str] = {}
+
+    def update_baseline(self, tools: List[Dict[str, Any]]) -> None:
+        """Snapshot the current schema hashes as the baseline."""
+        self._baseline = {
+            t.get("name", ""): hash_tool_schema(t)
+            for t in tools or []
+            if t.get("name")
+        }
+
+    def detect_breaks(
+        self,
+        tools: List[Dict[str, Any]],
+        model_id: str = "",
+    ) -> List[str]:
+        """Return list of tool names whose schemas changed since the last
+        update_baseline() call.
+
+        R4 #14: when model_id is in the cache-break EXCLUDED set, skips
+        detection entirely (returns []). The notify_cache_deletion()
+        call would fail with 400 on those models.
+        """
+        if is_cache_break_excluded(model_id):
+            return []
+        if not self._baseline:
+            # First call — establish baseline; no breaks reported.
+            self.update_baseline(tools)
+            return []
+
+        broken: List[str] = []
+        current = {
+            t.get("name", ""): hash_tool_schema(t)
+            for t in tools or []
+            if t.get("name")
+        }
+        for name, h in current.items():
+            prev = self._baseline.get(name)
+            if prev is not None and prev != h:
+                broken.append(name)
+        # Update baseline so subsequent calls compare against latest.
+        self._baseline = current
+        return broken
+
+
+def notify_cache_deletion(
+    model_id: str,
+    tool_names: List[str],
+) -> bool:
+    """Issue a cache-deletion notification for the given tools.
+
+    Block L: when tool schemas change, Bedrock's prompt cache for those
+    tool entries is stale; this helper would normally call the Bedrock
+    invalidation endpoint. v5's stub: log + return True for non-excluded
+    models, return False (skip) for EXCLUDED models.
+
+    The actual Bedrock endpoint integration is wired by core/query_engine
+    on the next chat() call's `additionalModelRequestFields`.
+    """
+    if is_cache_break_excluded(model_id):
+        return False  # skip
+    # Real wiring would go here; v5 stub just signals "should notify".
+    import logging
+    logging.info(
+        "[cache-break] notify_cache_deletion model=%s tools=%s",
+        model_id, tool_names,
+    )
+    return True
diff --git a/compact_v5/MAIN/agent/core/errors.py b/compact_v5/MAIN/agent/core/errors.py
index aa01a93..0bab9dd 100644
--- a/compact_v5/MAIN/agent/core/errors.py
+++ b/compact_v5/MAIN/agent/core/errors.py
@@ -20,7 +20,13 @@ from __future__ import annotations
 
 
 class BedrockErrorCategory:
-    """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy."""
+    """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy.
+
+    Block L (PORT_LOG #100) extends to 18 categories per Runnable R4 18-categorization.
+    The original 9 (Phase 8) cover the v4 surface; the additional 9 distinguish
+    finer-grained cases that benefit from differentiated retry/recovery semantics.
+    """
+    # Phase 8 (v4) categories — 9
     THROTTLE = "throttle"  # ThrottlingException, rate-limited
     SERVICE_UNAVAILABLE = "service_unavailable"
     MODEL_NOT_READY = "model_not_ready"
@@ -30,6 +36,147 @@ class BedrockErrorCategory:
     CONTEXT_OVERFLOW = "context_overflow"  # prompt-too-long
     ACCESS_DENIED = "access_denied"
     UNKNOWN = "unknown"
+    # Block L additions — 9 more (R4 18 categories)
+    MAX_TOKENS_OVERFLOW = "max_tokens_overflow"  # output capped at max_tokens — compact + retry
+    BEDROCK_5XX_HTML = "bedrock_5xx_html"  # raw HTML 5xx — humanize before user
+    REQUEST_TIMEOUT = "request_timeout"  # client-side timeout
+    PAYLOAD_TOO_LARGE = "payload_too_large"  # 413 — compact request
+    CONFLICT_409 = "conflict_409"  # session/state conflict
+    GATEWAY_TIMEOUT = "gateway_timeout"  # 504 — backoff
+    MALFORMED_RESPONSE = "malformed_response"  # body parse failure — retry once
+    SIGV4_FAILURE = "sigv4_failure"  # auth signature error — no retry, surface
+    DEPENDENCY_FAILURE = "dependency_failure"  # downstream service error — backoff
+
+
+# Block L: which categories are retryable. Used by categorize_retryable().
+# Per Runnable R4 categorization.
+_RETRYABLE_CATEGORIES = frozenset({
+    BedrockErrorCategory.THROTTLE,
+    BedrockErrorCategory.SERVICE_UNAVAILABLE,
+    BedrockErrorCategory.MODEL_NOT_READY,
+    BedrockErrorCategory.NETWORK,
+    BedrockErrorCategory.VALIDATION_CACHE,  # retry once after stripping
+    BedrockErrorCategory.CONTEXT_OVERFLOW,  # retry after compact
+    BedrockErrorCategory.MAX_TOKENS_OVERFLOW,  # retry after compact
+    BedrockErrorCategory.BEDROCK_5XX_HTML,  # backoff
+    BedrockErrorCategory.REQUEST_TIMEOUT,  # retry once
+    BedrockErrorCategory.PAYLOAD_TOO_LARGE,  # retry after compact
+    BedrockErrorCategory.GATEWAY_TIMEOUT,  # backoff
+    BedrockErrorCategory.MALFORMED_RESPONSE,  # retry once
+    BedrockErrorCategory.DEPENDENCY_FAILURE,  # backoff
+})
+
+
+def categorize_retryable(category: str) -> bool:
+    """Return True iff `category` is in the retryable set (Block L PORT_LOG #100)."""
+    return category in _RETRYABLE_CATEGORIES
+
+
+def extract_nested_error_message(exc_or_text) -> str:
+    """Block L (R4 #9 MUST): humanize Bedrock 5xx errors that contain raw HTML.
+
+    Bedrock occasionally returns HTML error pages on 5xx; the user sees a wall
+    of `<html>...<body>The server encountered an error...</body></html>`.
+    This helper extracts the readable text from common error shapes:
+    - `<title>Error</title>` → use the title.
+    - `<body>...text...</body>` → use the body text.
+    - `<h1>Error 502</h1>` → use the heading.
+    - JSON `{"message": "..."}` → use the message field.
+
+    Falls back to the first 200 chars of the input when no pattern matches.
+    """
+    import re
+    import json as _json
+
+    text = str(exc_or_text)
+    if not text.strip():
+        return "(empty error)"
+
+    # Try JSON first.
+    try:
+        data = _json.loads(text)
+        if isinstance(data, dict):
+            for key in ("message", "Message", "error", "Error"):
+                v = data.get(key)
+                if isinstance(v, str) and v.strip():
+                    return v.strip()[:200]
+    except (_json.JSONDecodeError, ValueError):
+        pass
+
+    # Try HTML title.
+    m = re.search(r"<title[^>]*>([^<]+)</title>", text, re.IGNORECASE)
+    if m:
+        return m.group(1).strip()[:200]
+    # Try h1.
+    m = re.search(r"<h1[^>]*>([^<]+)</h1>", text, re.IGNORECASE)
+    if m:
+        return m.group(1).strip()[:200]
+    # Try body text — strip remaining tags.
+    m = re.search(r"<body[^>]*>(.*?)</body>", text, re.IGNORECASE | re.DOTALL)
+    if m:
+        body_text = re.sub(r"<[^>]+>", " ", m.group(1))
+        body_text = re.sub(r"\s+", " ", body_text).strip()
+        if body_text:
+            return body_text[:200]
+
+    # Fallback: strip ALL HTML tags from the full input.
+    stripped = re.sub(r"<[^>]+>", " ", text)
+    stripped = re.sub(r"\s+", " ", stripped).strip()
+    return stripped[:200] or text[:200]
+
+
+def parse_max_tokens_context_overflow_error(exc) -> bool:
+    """Block L (R4 #2 MUST): True iff `exc` is a max-tokens or context-
+    overflow error that should trigger compact+retry.
+
+    Distinguishes max_tokens (output cap hit) from prompt-too-long
+    (context overflow) — both trigger compact+retry but for different
+    reasons. Returns True for either.
+    """
+    msg = str(exc).lower()
+    if "max_tokens" in msg or "max output tokens" in msg or "output token limit" in msg:
+        return True
+    if "prompt is too long" in msg or "too many tokens" in msg or "input length" in msg:
+        return True
+    if "context length" in msg or "context_overflow" in msg:
+        return True
+    return False
+
+
+def get_retry_after_ms(exc) -> int:
+    """Block L (R4 retry-after): parse Retry-After header value from exception.
+
+    Bedrock 429 responses include a Retry-After header (seconds). This helper
+    extracts the integer second value and returns milliseconds. Returns 0
+    when no Retry-After is found.
+
+    Accepts:
+    - integer seconds: "5" → 5000
+    - HTTP-date format (RFC 1123): "Wed, 21 Oct 2026 07:28:00 GMT" → ms-until-then
+    - error message containing "Retry-After: 5": parses the trailing seconds
+    """
+    import re
+    import time
+    from email.utils import parsedate_to_datetime
+
+    s = str(exc)
+    # Match "Retry-After: <value>" header pattern.
+    m = re.search(r"retry-after\s*:?\s*(\d+)", s, re.IGNORECASE)
+    if m:
+        try:
+            return int(m.group(1)) * 1000
+        except (ValueError, TypeError):
+            return 0
+    # Match HTTP-date.
+    m = re.search(r"retry-after\s*:?\s*([A-Z][a-z]{2},\s*\d.+\d{4}.+GMT)", s)
+    if m:
+        try:
+            dt = parsedate_to_datetime(m.group(1))
+            wait = max(0, int((dt.timestamp() - time.time()) * 1000))
+            return wait
+        except (ValueError, TypeError):
+            return 0
+    return 0
 
 
 class ErrorClassifier:
@@ -47,6 +194,30 @@ class ErrorClassifier:
         msg_lower = str(exc).lower()
         cls_name = type(exc).__name__.lower()
 
+        # Block L additions — check most-specific first.
+        if "max_tokens" in msg_lower or "max output tokens" in msg_lower or "output token limit" in msg_lower:
+            return BedrockErrorCategory.MAX_TOKENS_OVERFLOW, "compact_retry", str(exc)[:200]
+        if "<html" in msg_lower or "<body" in msg_lower or "<title" in msg_lower:
+            # Raw HTML 5xx error — backoff + humanize before user-facing display.
+            return BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff", str(exc)[:200]
+        if "504" in msg_lower or "gatewaytimeout" in msg_lower:
+            return BedrockErrorCategory.GATEWAY_TIMEOUT, "backoff", str(exc)[:200]
+        if "413" in msg_lower or "payload too large" in msg_lower or "request entity too large" in msg_lower:
+            return BedrockErrorCategory.PAYLOAD_TOO_LARGE, "compact_retry", str(exc)[:200]
+        if "409" in msg_lower or "conflictexception" in msg_lower:
+            return BedrockErrorCategory.CONFLICT_409, "no_retry", str(exc)[:200]
+        if "request_timeout" in msg_lower or "request-timeout" in msg_lower or (
+            "408" in msg_lower
+        ):
+            return BedrockErrorCategory.REQUEST_TIMEOUT, "backoff", str(exc)[:200]
+        if "malformed" in msg_lower or "could not parse response" in msg_lower or "decode" in cls_name:
+            return BedrockErrorCategory.MALFORMED_RESPONSE, "backoff", str(exc)[:200]
+        if "sigv4" in msg_lower or "signature" in msg_lower or "credentialverify" in cls_name:
+            return BedrockErrorCategory.SIGV4_FAILURE, "no_retry", str(exc)[:200]
+        if "dependency" in msg_lower or "dependencyfailedexception" in msg_lower:
+            return BedrockErrorCategory.DEPENDENCY_FAILURE, "backoff", str(exc)[:200]
+
+        # Phase 8 categories — preserved.
         if "validationexception" in msg_lower and (
             "cache_control" in msg_lower
             or "prompt-caching" in msg_lower
diff --git a/compact_v5/MAIN/agent/tests/integration/test_block_l.py b/compact_v5/MAIN/agent/tests/integration/test_block_l.py
new file mode 100644
index 0000000..58be0fd
--- /dev/null
+++ b/compact_v5/MAIN/agent/tests/integration/test_block_l.py
@@ -0,0 +1,326 @@
+"""Block L — Error/retry/cache-break + Bedrock guardrails + daemon-thread call.
+
+Source: Runnable services/api/errors.ts + cacheBreakDetection.ts +
+withRetry.ts.
+
+Tests per TEST_DESIGN §Block L (8 tests; 2 T2 daemon-thread tests
+deferred to Block J real-AWS integration):
+- test_categorize_retryable_18_error_types
+- test_parse_max_tokens_overflow_recovers
+- test_extract_nested_error_message_humanizes_5xx_html
+- test_retry_after_header_parsed
+- test_per_tool_cache_break_detection
+- test_haiku_excluded_from_cache_break_3loc
+- test_daemon_thread_bedrock_call_responds_to_ctrl_c (DEFERRED)
+- test_30s_heartbeat_during_long_call (DEFERRED)
+"""
+from __future__ import annotations
+
+import os
+import sys
+
+import pytest
+
+_AGENT_ROOT = os.path.dirname(
+    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
+)
+if _AGENT_ROOT not in sys.path:
+    sys.path.insert(0, _AGENT_ROOT)
+
+
+# ============================================================
+# TEST_DESIGN row 1 — 18 error categories with retryable verdicts
+# ============================================================
+
+def test_categorize_retryable_18_error_types():
+    """Each of 18 Runnable error categories → correct retryable verdict.
+
+    Retryable (13): throttle, service_unavailable, model_not_ready,
+    network, validation_cache, context_overflow, max_tokens_overflow,
+    bedrock_5xx_html, request_timeout, payload_too_large,
+    gateway_timeout, malformed_response, dependency_failure.
+
+    Non-retryable (5): validation_other, access_denied, conflict_409,
+    sigv4_failure, unknown.
+    """
+    from core import BedrockErrorCategory, categorize_retryable
+
+    # All 18 categories defined.
+    all_18 = [
+        BedrockErrorCategory.THROTTLE,
+        BedrockErrorCategory.SERVICE_UNAVAILABLE,
+        BedrockErrorCategory.MODEL_NOT_READY,
+        BedrockErrorCategory.NETWORK,
+        BedrockErrorCategory.VALIDATION_CACHE,
+        BedrockErrorCategory.VALIDATION_OTHER,
+        BedrockErrorCategory.CONTEXT_OVERFLOW,
+        BedrockErrorCategory.ACCESS_DENIED,
+        BedrockErrorCategory.UNKNOWN,
+        BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
+        BedrockErrorCategory.BEDROCK_5XX_HTML,
+        BedrockErrorCategory.REQUEST_TIMEOUT,
+        BedrockErrorCategory.PAYLOAD_TOO_LARGE,
+        BedrockErrorCategory.CONFLICT_409,
+        BedrockErrorCategory.GATEWAY_TIMEOUT,
+        BedrockErrorCategory.MALFORMED_RESPONSE,
+        BedrockErrorCategory.SIGV4_FAILURE,
+        BedrockErrorCategory.DEPENDENCY_FAILURE,
+    ]
+    assert len(set(all_18)) == 18, f"Expected 18 distinct categories; got {len(set(all_18))}"
+
+    retryable = {
+        BedrockErrorCategory.THROTTLE,
+        BedrockErrorCategory.SERVICE_UNAVAILABLE,
+        BedrockErrorCategory.MODEL_NOT_READY,
+        BedrockErrorCategory.NETWORK,
+        BedrockErrorCategory.VALIDATION_CACHE,
+        BedrockErrorCategory.CONTEXT_OVERFLOW,
+        BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
+        BedrockErrorCategory.BEDROCK_5XX_HTML,
+        BedrockErrorCategory.REQUEST_TIMEOUT,
+        BedrockErrorCategory.PAYLOAD_TOO_LARGE,
+        BedrockErrorCategory.GATEWAY_TIMEOUT,
+        BedrockErrorCategory.MALFORMED_RESPONSE,
+        BedrockErrorCategory.DEPENDENCY_FAILURE,
+    }
+    non_retryable = {
+        BedrockErrorCategory.VALIDATION_OTHER,
+        BedrockErrorCategory.ACCESS_DENIED,
+        BedrockErrorCategory.CONFLICT_409,
+        BedrockErrorCategory.SIGV4_FAILURE,
+        BedrockErrorCategory.UNKNOWN,
+    }
+
+    for cat in retryable:
+        assert categorize_retryable(cat) is True, f"{cat} should be retryable"
+    for cat in non_retryable:
+        assert categorize_retryable(cat) is False, f"{cat} should NOT be retryable"
+
+
+# ============================================================
+# TEST_DESIGN row 2 — max-tokens overflow triggers compact + retry (R4 #2 MUST)
+# ============================================================
+
+def test_parse_max_tokens_overflow_recovers():
+    """parseMaxTokensContextOverflowError triggers compact + retry."""
+    from core import (
+        BedrockErrorCategory,
+        ErrorClassifier,
+        parse_max_tokens_context_overflow_error,
+    )
+
+    cases = [
+        ValueError("max_tokens 4096 exceeded"),
+        RuntimeError("Output token limit reached at 4097"),
+        Exception("Prompt is too long: 250000 tokens"),
+        Exception("Too many tokens in input length"),
+        Exception("context_overflow"),
+        Exception("Context length 200001 exceeds 200000"),
+    ]
+    for exc in cases:
+        assert parse_max_tokens_context_overflow_error(exc) is True, (
+            f"{exc!r} should be detected as max-tokens/context overflow"
+        )
+
+    # Non-cases.
+    for exc in [Exception("ThrottlingException"), ValueError("unrelated")]:
+        assert parse_max_tokens_context_overflow_error(exc) is False
+
+    # Classifier maps max-tokens overflow to MAX_TOKENS_OVERFLOW with
+    # compact_retry recovery.
+    cat, recovery, _ = ErrorClassifier.classify(
+        Exception("max_tokens 4096 exceeded")
+    )
+    assert cat == BedrockErrorCategory.MAX_TOKENS_OVERFLOW
+    assert recovery == "compact_retry"
+
+
+# ============================================================
+# TEST_DESIGN row 3 — humanize 5xx HTML errors (R4 #9 MUST)
+# ============================================================
+
+def test_extract_nested_error_message_humanizes_5xx_html():
+    """Bedrock 5xx with raw HTML → user sees clean error message."""
+    from core import extract_nested_error_message
+
+    # HTML title.
+    html_title = "<html><head><title>503 Service Unavailable</title></head><body>x</body></html>"
+    out = extract_nested_error_message(html_title)
+    assert out == "503 Service Unavailable"
+
+    # H1.
+    html_h1 = "<html><body><h1>Internal Server Error</h1><p>x</p></body></html>"
+    out = extract_nested_error_message(html_h1)
+    assert "Internal Server Error" in out
+
+    # Body fallback.
+    html_body = "<html><body>The server encountered an error.</body></html>"
+    out = extract_nested_error_message(html_body)
+    assert "The server encountered an error" in out
+
+    # JSON.
+    json_err = '{"message": "AccessDenied: principal lacks permission"}'
+    out = extract_nested_error_message(json_err)
+    assert "AccessDenied" in out
+
+    # Plain string fallback.
+    plain = "ThrottlingException: Rate exceeded"
+    out = extract_nested_error_message(plain)
+    assert "ThrottlingException" in out
+
+
+# ============================================================
+# TEST_DESIGN row 4 — Retry-After header parsed
+# ============================================================
+
+def test_retry_after_header_parsed():
+    """getRetryAfterMs parses 'Retry-After: 5' → 5000ms."""
+    from core import get_retry_after_ms
+
+    assert get_retry_after_ms(Exception("HTTP 429: Retry-After: 5")) == 5000
+    assert get_retry_after_ms("Retry-After: 30") == 30000
+    assert get_retry_after_ms("retry-after:60") == 60000
+    # No header → 0.
+    assert get_retry_after_ms("ThrottlingException") == 0
+    assert get_retry_after_ms("") == 0
+
+
+# ============================================================
+# TEST_DESIGN row 5 — per-tool cache-break detection
+# ============================================================
+
+def test_per_tool_cache_break_detection():
+    """Per-tool schema hash change → cache-deletion fires for that tool only."""
+    from core import PerToolCacheBreakDetector
+
+    detector = PerToolCacheBreakDetector()
+
+    tools_v1 = [
+        {"name": "read_file", "description": "Read", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
+        {"name": "write_file", "description": "Write", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
+    ]
+    # First call: establish baseline; no breaks.
+    breaks = detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")
+    assert breaks == []
+
+    # Same tools again → no breaks.
+    breaks = detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")
+    assert breaks == []
+
+    # read_file's schema changes; write_file unchanged.
+    tools_v2 = [
+        {"name": "read_file", "description": "Read v2", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "encoding": {"type": "string"}}}},
+        {"name": "write_file", "description": "Write", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
+    ]
+    breaks = detector.detect_breaks(tools_v2, model_id="anthropic.claude-sonnet-4-6")
+    assert breaks == ["read_file"], f"Expected only read_file broken; got {breaks}"
+
+
+# ============================================================
+# TEST_DESIGN row 6 — Haiku excluded from cache-break (R4 #14 MUST 3LOC)
+# ============================================================
+
+def test_haiku_excluded_from_cache_break_3loc():
+    """Haiku-4.5 model_id in EXCLUDED set → cache-break detector skips."""
+    from core import PerToolCacheBreakDetector, is_cache_break_excluded
+
+    # Direct exclusion check.
+    assert is_cache_break_excluded("anthropic.claude-haiku-4-5-20251001-v1:0") is True
+    assert is_cache_break_excluded("au.anthropic.claude-haiku-4-5-20251001-v1:0") is True
+    assert is_cache_break_excluded("apac.anthropic.claude-haiku-4-5-20251001-v1:0") is True
+    # Non-Haiku: not excluded.
+    assert is_cache_break_excluded("anthropic.claude-sonnet-4-6") is False
+    assert is_cache_break_excluded("") is False
+
+    # Detector skip path: even when schemas change, Haiku model returns [].
+    detector = PerToolCacheBreakDetector()
+    tools_v1 = [{"name": "x", "description": "y", "input_schema": {"v": 1}}]
+    detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")  # establish baseline
+    tools_v2 = [{"name": "x", "description": "y", "input_schema": {"v": 2}}]  # schema changed
+
+    # Sonnet sees the break.
+    breaks_sonnet = detector.detect_breaks(tools_v2, model_id="anthropic.claude-sonnet-4-6")
+    assert "x" in breaks_sonnet
+
+    # Reset baseline + check Haiku gets [] regardless.
+    detector2 = PerToolCacheBreakDetector()
+    detector2.detect_breaks(tools_v1, model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
+    breaks_haiku = detector2.detect_breaks(
+        tools_v2, model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
+    )
+    assert breaks_haiku == [], "Haiku must be excluded from cache-break detection"
+
+
+# ============================================================
+# TEST_DESIGN row 7 + 8 — DEFERRED to Block J real-AWS integration
+# ============================================================
+
+@pytest.mark.skip(
+    reason="Block L T2 daemon-thread test deferred to Block J real-AWS gate "
+    "(timing-sensitive; relies on actual long-running Bedrock call to "
+    "interrupt with KeyboardInterrupt). Per ADR-036 §3."
+)
+def test_daemon_thread_bedrock_call_responds_to_ctrl_c():
+    pass
+
+
+@pytest.mark.skip(
+    reason="Block L T2 30s-heartbeat test deferred to Block J real-AWS gate "
+    "(timing-sensitive 30s wall-clock test). Per ADR-036 §3."
+)
+def test_30s_heartbeat_during_long_call():
+    pass
+
+
+# ============================================================
+# Behavioral lock tests
+# ============================================================
+
+def test_classifier_recognizes_new_categories():
+    """Classifier maps each new category to a sensible default recovery."""
+    from core import BedrockErrorCategory, ErrorClassifier
+
+    cases = [
+        (Exception("<html><body>503 Service Unavailable</body></html>"),
+         BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff"),
+        (Exception("HTTP 504 GatewayTimeout"),
+         BedrockErrorCategory.GATEWAY_TIMEOUT, "backoff"),
+        (Exception("HTTP 413 Payload too large"),
+         BedrockErrorCategory.PAYLOAD_TOO_LARGE, "compact_retry"),
+        (Exception("HTTP 409 ConflictException"),
+         BedrockErrorCategory.CONFLICT_409, "no_retry"),
+        (Exception("malformed response: could not parse response"),
+         BedrockErrorCategory.MALFORMED_RESPONSE, "backoff"),
+        (Exception("SigV4 signature failed"),
+         BedrockErrorCategory.SIGV4_FAILURE, "no_retry"),
+        (Exception("DependencyFailedException: downstream"),
+         BedrockErrorCategory.DEPENDENCY_FAILURE, "backoff"),
+    ]
+    for exc, expected_cat, expected_recovery in cases:
+        cat, recovery, _ = ErrorClassifier.classify(exc)
+        assert cat == expected_cat, f"{exc!r} → got {cat}, expected {expected_cat}"
+        assert recovery == expected_recovery
+
+
+def test_hash_tool_schema_deterministic():
+    """Same schema content → same hash regardless of key order."""
+    from core import hash_tool_schema
+
+    a = {"name": "x", "input_schema": {"type": "object", "properties": {"a": {"type": "string"}}}}
+    b = {"input_schema": {"properties": {"a": {"type": "string"}}, "type": "object"}, "name": "x"}
+    assert hash_tool_schema(a) == hash_tool_schema(b)
+    # Different content → different hash.
+    c = {"name": "x", "input_schema": {"type": "string"}}
+    assert hash_tool_schema(a) != hash_tool_schema(c)
+
+
+def test_notify_cache_deletion_skips_excluded_models():
+    """notify_cache_deletion returns False for Haiku (R4 #14 MUST)."""
+    from core import notify_cache_deletion
+
+    assert notify_cache_deletion(
+        "anthropic.claude-haiku-4-5-20251001-v1:0", ["read_file"]
+    ) is False
+    assert notify_cache_deletion(
+        "anthropic.claude-sonnet-4-6", ["read_file"]
+    ) is True

 succeeded in 597ms:
    1: import type { BetaToolUnion } from '@anthropic-ai/sdk/resources/beta/messages/messages.mjs'
    2: import type { TextBlockParam } from '@anthropic-ai/sdk/resources/index.mjs'
    3: import { createPatch } from 'diff'
    4: import { mkdir, writeFile } from 'fs/promises'
    5: import { join } from 'path'
    6: import type { AgentId } from 'src/types/ids.js'
    7: import type { Message } from 'src/types/message.js'
    8: import { logForDebugging } from 'src/utils/debug.js'
    9: import { djb2Hash } from 'src/utils/hash.js'
   10: import { logError } from 'src/utils/log.js'
   11: import { getClaudeTempDir } from 'src/utils/permissions/filesystem.js'
   12: import { jsonStringify } from 'src/utils/slowOperations.js'
   13: import type { QuerySource } from '../../constants/querySource.js'
   14: import {
   15:   type AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS,
   16:   logEvent,
   17: } from '../analytics/index.js'
   18: 
   19: function getCacheBreakDiffPath(): string {
   20:   const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
   21:   let suffix = ''
   22:   for (let i = 0; i < 4; i++) {
   23:     suffix += chars[Math.floor(Math.random() * chars.length)]
   24:   }
   25:   return join(getClaudeTempDir(), `cache-break-${suffix}.diff`)
   26: }
   27: 
   28: type PreviousState = {
   29:   systemHash: number
   30:   toolsHash: number
   31:   /** Hash of system blocks WITH cache_control intact. Catches scope/TTL flips
   32:    *  (globalâ†”org, 1hâ†”5m) that stripCacheControl erases from systemHash. */
   33:   cacheControlHash: number
   34:   toolNames: string[]
   35:   /** Per-tool schema hash. Diffed to name which tool's description changed
   36:    *  when toolSchemasChanged but added=removed=0 (77% of tool breaks per
   37:    *  BQ 2026-03-22). AgentTool/SkillTool embed dynamic agent/command lists. */
   38:   perToolHashes: Record<string, number>
   39:   systemCharCount: number
   40:   model: string
   41:   fastMode: boolean
   42:   /** 'tool_based' | 'system_prompt' | 'none' â€” flips when MCP tools are
   43:    *  discovered/removed. */
   44:   globalCacheStrategy: string
   45:   /** Sorted beta header list. Diffed to show which headers were added/removed. */
   46:   betas: string[]
   47:   /** AFK_MODE_BETA_HEADER presence â€” should NOT break cache anymore
   48:    *  (sticky-on latched in claude.ts). Tracked to verify the fix. */
   49:   autoModeActive: boolean
   50:   /** Overage state flip â€” should NOT break cache anymore (eligibility is
   51:    *  latched session-stable in should1hCacheTTL). Tracked to verify the fix. */
   52:   isUsingOverage: boolean
   53:   /** Cache-editing beta header presence â€” should NOT break cache anymore
   54:    *  (sticky-on latched in claude.ts). Tracked to verify the fix. */
   55:   cachedMCEnabled: boolean
   56:   /** Resolved effort (env â†’ options â†’ model default). Goes into output_config
   57:    *  or anthropic_internal.effort_override. */
   58:   effortValue: string
   59:   /** Hash of getExtraBodyParams() â€” catches CLAUDE_CODE_EXTRA_BODY and
   60:    *  anthropic_internal changes. */
   61:   extraBodyHash: number
   62:   callCount: number
   63:   pendingChanges: PendingChanges | null
   64:   prevCacheReadTokens: number | null
   65:   /** Set when cached microcompact sends cache_edits deletions. Cache reads
   66:    *  will legitimately drop â€” this is expected, not a break. */
   67:   cacheDeletionsPending: boolean
   68:   buildDiffableContent: () => string
   69: }
   70: 
   71: type PendingChanges = {
   72:   systemPromptChanged: boolean
   73:   toolSchemasChanged: boolean
   74:   modelChanged: boolean
   75:   fastModeChanged: boolean
   76:   cacheControlChanged: boolean
   77:   globalCacheStrategyChanged: boolean
   78:   betasChanged: boolean
   79:   autoModeChanged: boolean
   80:   overageChanged: boolean
   81:   cachedMCChanged: boolean
   82:   effortChanged: boolean
   83:   extraBodyChanged: boolean
   84:   addedToolCount: number
   85:   removedToolCount: number
   86:   systemCharDelta: number
   87:   addedTools: string[]
   88:   removedTools: string[]
   89:   changedToolSchemas: string[]
   90:   previousModel: string
   91:   newModel: string
   92:   prevGlobalCacheStrategy: string
   93:   newGlobalCacheStrategy: string
   94:   addedBetas: string[]
   95:   removedBetas: string[]
   96:   prevEffortValue: string
   97:   newEffortValue: string
   98:   buildPrevDiffableContent: () => string
   99: }
  100: 
  101: const previousStateBySource = new Map<string, PreviousState>()
  102: 
  103: // Cap the number of tracked sources to prevent unbounded memory growth.
  104: // Each entry stores a ~300KB+ diffableContent string (serialized system prompt
  105: // + tool schemas). Without a cap, spawning many subagents (each with a unique
  106: // agentId key) causes the map to grow indefinitely.
  107: const MAX_TRACKED_SOURCES = 10
  108: 
  109: const TRACKED_SOURCE_PREFIXES = [
  110:   'repl_main_thread',
  111:   'sdk',
  112:   'agent:custom',
  113:   'agent:default',
  114:   'agent:builtin',
  115: ]
  116: 
  117: // Minimum absolute token drop required to trigger a cache break warning.
  118: // Small drops (e.g., a few thousand tokens) can happen due to normal variation
  119: // and aren't worth alerting on.
  120: const MIN_CACHE_MISS_TOKENS = 2_000
  121: 
  122: // Anthropic's server-side prompt cache TTL thresholds to test.
  123: // Cache breaks after these durations are likely due to TTL expiration
  124: // rather than client-side changes.
  125: const CACHE_TTL_5MIN_MS = 5 * 60 * 1000
  126: export const CACHE_TTL_1HOUR_MS = 60 * 60 * 1000
  127: 
  128: // Models to exclude from cache break detection (e.g., haiku has different caching behavior)
  129: function isExcludedModel(model: string): boolean {
  130:   return model.includes('haiku')
  131: }
  132: 
  133: /**
  134:  * Returns the tracking key for a querySource, or null if untracked.
  135:  * Compact shares the same server-side cache as repl_main_thread
  136:  * (same cacheSafeParams), so they share tracking state.
  137:  *
  138:  * For subagents with a tracked querySource, uses the unique agentId to
  139:  * isolate tracking state. This prevents false positive cache break
  140:  * notifications when multiple instances of the same agent type run
  141:  * concurrently.
  142:  *
  143:  * Untracked sources (speculation, session_memory, prompt_suggestion, etc.)
  144:  * are short-lived forked agents where cache break detection provides no
  145:  * value â€” they run 1-3 turns with a fresh agentId each time, so there's
  146:  * nothing meaningful to compare against. Their cache metrics are still
  147:  * logged via tengu_api_success for analytics.
  148:  */
  149: function getTrackingKey(
  150:   querySource: QuerySource,
  151:   agentId?: AgentId,
  152: ): string | null {
  153:   if (querySource === 'compact') return 'repl_main_thread'
  154:   for (const prefix of TRACKED_SOURCE_PREFIXES) {
  155:     if (querySource.startsWith(prefix)) return agentId || querySource
  156:   }
  157:   return null
  158: }
  159: 
  160: function stripCacheControl(
  161:   items: ReadonlyArray<Record<string, unknown>>,
  162: ): unknown[] {
  163:   return items.map(item => {
  164:     if (!('cache_control' in item)) return item
  165:     const { cache_control: _, ...rest } = item
  166:     return rest
  167:   })
  168: }
  169: 
  170: function computeHash(data: unknown): number {
  171:   const str = jsonStringify(data)
  172:   if (typeof Bun !== 'undefined') {
  173:     const hash = Bun.hash(str)
  174:     // Bun.hash can return bigint for large inputs; convert to number safely
  175:     return typeof hash === 'bigint' ? Number(hash & 0xffffffffn) : hash
  176:   }
  177:   // Fallback for non-Bun runtimes (e.g. Node.js via npm global install)
  178:   return djb2Hash(str)
  179: }
  180: 
  181: /** MCP tool names are user-controlled (server config) and may leak filepaths.
  182:  *  Collapse them to 'mcp'; built-in names are a fixed vocabulary. */
  183: function sanitizeToolName(name: string): string {
  184:   return name.startsWith('mcp__') ? 'mcp' : name
  185: }
  186: 
  187: function computePerToolHashes(
  188:   strippedTools: ReadonlyArray<unknown>,
  189:   names: string[],
  190: ): Record<string, number> {
  191:   const hashes: Record<string, number> = {}
  192:   for (let i = 0; i < strippedTools.length; i++) {
  193:     hashes[names[i] ?? `__idx_${i}`] = computeHash(strippedTools[i])
  194:   }
  195:   return hashes
  196: }
  197: 
  198: function getSystemCharCount(system: TextBlockParam[]): number {
  199:   let total = 0
  200:   for (const block of system) {
  201:     total += block.text.length
  202:   }
  203:   return total
  204: }
  205: 
  206: function buildDiffableContent(
  207:   system: TextBlockParam[],
  208:   tools: BetaToolUnion[],
  209:   model: string,
  210: ): string {
  211:   const systemText = system.map(b => b.text).join('\n\n')
  212:   const toolDetails = tools
  213:     .map(t => {
  214:       if (!('name' in t)) return 'unknown'
  215:       const desc = 'description' in t ? t.description : ''
  216:       const schema = 'input_schema' in t ? jsonStringify(t.input_schema) : ''
  217:       return `${t.name}\n  description: ${desc}\n  input_schema: ${schema}`
  218:     })
  219:     .sort()
  220:     .join('\n\n')
  221:   return `Model: ${model}\n\n=== System Prompt ===\n\n${systemText}\n\n=== Tools (${tools.length}) ===\n\n${toolDetails}\n`
  222: }
  223: 
  224: /** Extended tracking snapshot â€” everything that could affect the server-side
  225:  *  cache key that we can observe from the client. All fields are optional so
  226:  *  the call site can add incrementally; undefined fields compare as stable. */
  227: export type PromptStateSnapshot = {
  228:   system: TextBlockParam[]
  229:   toolSchemas: BetaToolUnion[]
  230:   querySource: QuerySource
  231:   model: string
  232:   agentId?: AgentId
  233:   fastMode?: boolean
  234:   globalCacheStrategy?: string
  235:   betas?: readonly string[]
  236:   autoModeActive?: boolean
  237:   isUsingOverage?: boolean
  238:   cachedMCEnabled?: boolean
  239:   effortValue?: string | number
  240:   extraBodyParams?: unknown

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$path='"'_archive/compare_code/gg-claude-code-runnable/src/services/api/withRetry.ts'; "'$lines=Get-Content $path; foreach($range in @(@(500,575),@(780,835),@(700,735))) { for($i=$range[0]; $i -le $range[1]; $i++){ if($i -le $lines.Length){ '"'{0,5}: {1}' -f "'$i, $lines[$i-1] } }; '"'' }" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$path='"'compact_v5/_phase_2/wave_6/TEST_DESIGN.md'; "'$lines=Get-Content $path; for($i=319; $i -le 333; $i++){ '"'{0,5}: {1}' -f "'$i, $lines[$i-1] }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$path='"'compact_v5/_status/V5_DESIGN_DECISIONS.md'; "'$lines=Get-Content $path; for($i=1127; $i -le 1195; $i++){ '"'{0,5}: {1}' -f "'$i, $lines[$i-1] }' in D:\Github\sagemaker-coding-agent
 succeeded in 532ms:
  319: ### Block L â€” Error/retry/cache-break + Bedrock guardrails + daemon-thread call
  320: 
  321: | Test | Tier | Assertion | Cost |
  322: |---|---|---|---|
  323: | `test_categorize_retryable_18_error_types` | T1 | each of 18 Runnable error categories â†’ correct retryable verdict (R4 18 categories) | $0 |
  324: | `test_parse_max_tokens_overflow_recovers` | T1 | `parseMaxTokensContextOverflowError` triggers compact + retry (R4 #2 MUST) | $0 |
  325: | `test_extract_nested_error_message_humanizes_5xx_html` | T1 | Bedrock 5xx with raw HTML â†’ user sees clean error message (R4 #9 MUST) | $0 |
  326: | `test_retry_after_header_parsed` | T1 | `getRetryAfterMs` parses `Retry-After: 5` â†’ 5000ms wait | $0 |
  327: | `test_per_tool_cache_break_detection` | T1 | per-tool schema hash change â†’ `notifyCacheDeletion` fires for that tool only | $0 |
  328: | `test_haiku_excluded_from_cache_break_3loc` | T1 | Haiku-4.5 model_id in EXCLUDED set â†’ cache-break detector skips (R4 #14 MUST) | $0 |
  329: | `test_daemon_thread_bedrock_call_responds_to_ctrl_c` | T2 | Bedrock call wrapped in daemon thread; main thread Ctrl-C raises KeyboardInterrupt cleanly | $0 |
  330: | `test_30s_heartbeat_during_long_call` | T2 | heartbeat ping every 30s during long call â†’ status bar updates | $0 |
  331: 
  332: **Block L ships when**: 8/8 green. **Total AWS cost: $0.**
  333: 

 succeeded in 558ms:
  500:           const chunk = Math.min(remaining, HEARTBEAT_INTERVAL_MS)
  501:           await sleep(chunk, options.signal, { abortError })
  502:           remaining -= chunk
  503:         }
  504:         // Clamp so the for-loop never terminates. Backoff uses the separate
  505:         // persistentAttempt counter which keeps growing to the 5-min cap.
  506:         if (attempt >= maxRetries) attempt = maxRetries
  507:       } else {
  508:         if (error instanceof APIError) {
  509:           yield createSystemAPIErrorMessage(error, delayMs, attempt, maxRetries)
  510:         }
  511:         await sleep(delayMs, options.signal, { abortError })
  512:       }
  513:     }
  514:   }
  515: 
  516:   throw new CannotRetryError(lastError, retryContext)
  517: }
  518: 
  519: function getRetryAfter(error: unknown): string | null {
  520:   return (
  521:     ((error as { headers?: { 'retry-after'?: string } }).headers?.[
  522:       'retry-after'
  523:     ] ||
  524:       // eslint-disable-next-line eslint-plugin-n/no-unsupported-features/node-builtins
  525:       ((error as APIError).headers as Headers)?.get?.('retry-after')) ??
  526:     null
  527:   )
  528: }
  529: 
  530: export function getRetryDelay(
  531:   attempt: number,
  532:   retryAfterHeader?: string | null,
  533:   maxDelayMs = 32000,
  534: ): number {
  535:   if (retryAfterHeader) {
  536:     const seconds = parseInt(retryAfterHeader, 10)
  537:     if (!isNaN(seconds)) {
  538:       return seconds * 1000
  539:     }
  540:   }
  541: 
  542:   const baseDelay = Math.min(
  543:     BASE_DELAY_MS * Math.pow(2, attempt - 1),
  544:     maxDelayMs,
  545:   )
  546:   const jitter = Math.random() * 0.25 * baseDelay
  547:   return baseDelay + jitter
  548: }
  549: 
  550: export function parseMaxTokensContextOverflowError(error: APIError):
  551:   | {
  552:       inputTokens: number
  553:       maxTokens: number
  554:       contextLimit: number
  555:     }
  556:   | undefined {
  557:   if (error.status !== 400 || !error.message) {
  558:     return undefined
  559:   }
  560: 
  561:   if (
  562:     !error.message.includes(
  563:       'input length and `max_tokens` exceed context limit',
  564:     )
  565:   ) {
  566:     return undefined
  567:   }
  568: 
  569:   // Example format: "input length and `max_tokens` exceed context limit: 188059 + 20000 > 200000"
  570:   const regex =
  571:     /input length and `max_tokens` exceed context limit: (\d+) \+ (\d+) > (\d+)/
  572:   const match = error.message.match(regex)
  573: 
  574:   if (!match || match.length !== 4) {
  575:     return undefined

  780:     return true
  781:   }
  782: 
  783:   // Retry internal errors.
  784:   if (error.status && error.status >= 500) return true
  785: 
  786:   return false
  787: }
  788: 
  789: export function getDefaultMaxRetries(): number {
  790:   if (process.env.CLAUDE_CODE_MAX_RETRIES) {
  791:     return parseInt(process.env.CLAUDE_CODE_MAX_RETRIES, 10)
  792:   }
  793:   return DEFAULT_MAX_RETRIES
  794: }
  795: function getMaxRetries(options: RetryOptions): number {
  796:   return options.maxRetries ?? getDefaultMaxRetries()
  797: }
  798: 
  799: const DEFAULT_FAST_MODE_FALLBACK_HOLD_MS = 30 * 60 * 1000 // 30 minutes
  800: const SHORT_RETRY_THRESHOLD_MS = 20 * 1000 // 20 seconds
  801: const MIN_COOLDOWN_MS = 10 * 60 * 1000 // 10 minutes
  802: 
  803: function getRetryAfterMs(error: APIError): number | null {
  804:   const retryAfter = getRetryAfter(error)
  805:   if (retryAfter) {
  806:     const seconds = parseInt(retryAfter, 10)
  807:     if (!isNaN(seconds)) {
  808:       return seconds * 1000
  809:     }
  810:   }
  811:   return null
  812: }
  813: 
  814: function getRateLimitResetDelayMs(error: APIError): number | null {
  815:   const resetHeader = error.headers?.get?.('anthropic-ratelimit-unified-reset')
  816:   if (!resetHeader) return null
  817:   const resetUnixSec = Number(resetHeader)
  818:   if (!Number.isFinite(resetUnixSec)) return null
  819:   const delayMs = resetUnixSec * 1000 - Date.now()
  820:   if (delayMs <= 0) return null
  821:   return Math.min(delayMs, PERSISTENT_RESET_CAP_MS)
  822: }

  700:   }
  701: 
  702:   // Persistent mode: 429/529 always retryable, bypass subscriber gates and
  703:   // x-should-retry header.
  704:   if (isPersistentRetryEnabled() && isTransientCapacityError(error)) {
  705:     return true
  706:   }
  707: 
  708:   // CCR mode: auth is via infrastructure-provided JWTs, so a 401/403 is a
  709:   // transient blip (auth service flap, network hiccup) rather than bad
  710:   // credentials. Bypass x-should-retry:false â€” the server assumes we'd retry
  711:   // the same bad key, but our key is fine.
  712:   if (
  713:     isEnvTruthy(process.env.CLAUDE_CODE_REMOTE) &&
  714:     (error.status === 401 || error.status === 403)
  715:   ) {
  716:     return true
  717:   }
  718: 
  719:   // Check for overloaded errors first by examining the message content
  720:   // The SDK sometimes fails to properly pass the 529 status code during streaming,
  721:   // so we need to check the error message directly
  722:   if (error.message?.includes('"type":"overloaded_error"')) {
  723:     return true
  724:   }
  725: 
  726:   // Check for max tokens context overflow errors that we can handle
  727:   if (parseMaxTokensContextOverflowError(error)) {
  728:     return true
  729:   }
  730: 
  731:   // Note this is not a standard header.
  732:   const shouldRetryHeader = error.headers?.get('x-should-retry')
  733: 
  734:   // If the server explicitly says whether or not to retry, obey.
  735:   // For Max and Pro users, should-retry is true, but in several hours, so we shouldn't.


 succeeded in 583ms:
 1127: ## ADR-036 â€” Block L (v5.0.1): Error/retry/cache-break + Bedrock guardrails
 1128: 
 1129: **Date**: 2026-05-03
 1130: **Phase ID**: v5.0.1 Block L
 1131: **Status**: ACCEPTED
 1132: 
 1133: ### Context
 1134: SYNTHESIS_MASTER Â§Block L lists ~966 LOC of Bedrock guardrails:
 1135: - 18-category error classification with retryable verdicts (Phase 8 had 9).
 1136: - max-tokens-overflow detection â†’ compact+retry (R4 #2 MUST).
 1137: - 5xx HTML error humanization (R4 #9 MUST).
 1138: - Retry-After header parsing.
 1139: - Per-tool cache-break detection.
 1140: - Haiku exclusion from cache-break detection (R4 #14 MUST 3LOC).
 1141: - Daemon-thread Bedrock call + Ctrl-C responsiveness.
 1142: - 30s heartbeat during long calls.
 1143: 
 1144: ### Decisions
 1145: 
 1146: #### 1. Extended error classification (PORT_LOG #100)
 1147: - core/errors.py: 9 new BedrockErrorCategory entries
 1148:   (MAX_TOKENS_OVERFLOW / BEDROCK_5XX_HTML / REQUEST_TIMEOUT /
 1149:   PAYLOAD_TOO_LARGE / CONFLICT_409 / GATEWAY_TIMEOUT /
 1150:   MALFORMED_RESPONSE / SIGV4_FAILURE / DEPENDENCY_FAILURE).
 1151: - categorize_retryable(category) â†’ bool. 13 of 18 are retryable.
 1152: - ErrorClassifier.classify extended to recognize each new category
 1153:   (most-specific-first ordering preserves Phase 8 behavior).
 1154: - extract_nested_error_message â€” humanizes HTML / JSON / plain
 1155:   errors. R4 #9 MUST.
 1156: - parse_max_tokens_context_overflow_error â€” predicate. R4 #2 MUST.
 1157: - get_retry_after_ms â€” parses Retry-After header (integer seconds OR
 1158:   HTTP-date) â†’ milliseconds. Returns 0 on no-match.
 1159: 
 1160: #### 2. Per-tool cache-break detection (PORT_LOG #101)
 1161: - core/cache_break_detection.py:
 1162:   - hash_tool_schema(schema) â€” deterministic SHA256/16chars.
 1163:   - PerToolCacheBreakDetector â€” per-tool baseline with diff.
 1164:   - is_cache_break_excluded(model_id) â€” checks against
 1165:     EXCLUDED_MODELS_3LOC frozenset (Haiku 4.5 + Haiku 4.1 + 3.5
 1166:     Haiku) with cross-region prefix stripping (au./apac./us./eu./
 1167:     global./ap./in.). R4 #14 MUST 3LOC.
 1168:   - notify_cache_deletion(model_id, tools) â€” returns False for
 1169:     excluded models (skip), True for others (signal to notify).
 1170: 
 1171: #### 3. T2 daemon-thread + heartbeat tests deferred to Block J
 1172: The `test_daemon_thread_bedrock_call_responds_to_ctrl_c` and
 1173: `test_30s_heartbeat_during_long_call` T2 tests are timing-sensitive
 1174: (rely on actual long-running Bedrock calls + 30s wall-clock). They
 1175: are deferred to Block J's real-AWS gate where they have natural fit.
 1176: Block L ships the underlying mechanism (error classifier + cache-break
 1177: detection) without the wall-clock tests.
 1178: 
 1179: #### 4. Why this is acceptable
 1180: The 6 T1 tests cover the load-bearing correctness contracts:
 1181: - 18-category classification + retryable verdicts.
 1182: - Max-tokens recovery (R4 #2 MUST).
 1183: - 5xx HTML humanization (R4 #9 MUST).
 1184: - Retry-After parsing.
 1185: - Per-tool cache-break detection.
 1186: - Haiku exclusion (R4 #14 MUST).
 1187: 
 1188: The deferred T2 tests are integration-level (timing + Ctrl-C
 1189: behavior) â€” they verify wiring, not algorithm correctness. The
 1190: algorithm is locked by the T1 tests; wiring is verified end-to-end
 1191: in Block J.
 1192: 
 1193: ### Affected files
 1194: - EXTENDED: `compact_v5/MAIN/agent/core/errors.py` (~150 LOC added)
 1195: - NEW: `compact_v5/MAIN/agent/core/cache_break_detection.py` (~120 LOC)

codex
A concrete issue is emerging in `get_retry_after_ms`: integer `Retry-After` is case-insensitive, but the HTTP-date branch is not, even though the contract says the header parse is case-insensitive. I’m checking whether there are similar shape gaps in the classifier before I write the final verdict.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "Retry-After|retry-after|get_retry_after|ErrorClassifier|BedrockErrorCategory|categorize_retryable|parse_max_tokens" compact_v5/MAIN/agent -g "*.py"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"ClientError|response\\]|HTTPHeaders|headers\" compact_v5/MAIN/agent/runtime compact_v5/MAIN/agent/core -g \"*.py\"" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'pytest compact_v5/MAIN/agent/tests/integration/test_block_l.py -q' in D:\Github\sagemaker-coding-agent
2026-05-03T08:08:38.579956Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.6 seconds
Output:
pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ pytest compact_v5/MAIN/agent/tests/integration/test_block_l.py -q
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (pytest:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 exited 1 in 570ms:
pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ pytest compact_v5/MAIN/agent/tests/integration/test_block_l.py -q
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (pytest:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 succeeded in 589ms:
compact_v5/MAIN/agent/runtime\bedrock_client.py:77:# beta) ride on `anthropic-beta` HTTP headers. Bedrock does NOT accept
compact_v5/MAIN/agent/runtime\bedrock_client.py:78:# those headers; the equivalent goes in `additionalModelRequestFields`
compact_v5/MAIN/agent/runtime\bedrock_client.py:82:# them as headers (which Bedrock would silently drop).
compact_v5/MAIN/agent/runtime\bedrock_client.py:91:    # headers. v5 already implements tool_search via Phase-7 deferred
compact_v5/MAIN/agent/runtime\dream.py:63:Group entries by topic with H2 headers. Each entry stays as a single

 succeeded in 751ms:
compact_v5/MAIN/agent\core\errors.py:22:class BedrockErrorCategory:
compact_v5/MAIN/agent\core\errors.py:23:    """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy.
compact_v5/MAIN/agent\core\errors.py:51:# Block L: which categories are retryable. Used by categorize_retryable().
compact_v5/MAIN/agent\core\errors.py:54:    BedrockErrorCategory.THROTTLE,
compact_v5/MAIN/agent\core\errors.py:55:    BedrockErrorCategory.SERVICE_UNAVAILABLE,
compact_v5/MAIN/agent\core\errors.py:56:    BedrockErrorCategory.MODEL_NOT_READY,
compact_v5/MAIN/agent\core\errors.py:57:    BedrockErrorCategory.NETWORK,
compact_v5/MAIN/agent\core\errors.py:58:    BedrockErrorCategory.VALIDATION_CACHE,  # retry once after stripping
compact_v5/MAIN/agent\core\errors.py:59:    BedrockErrorCategory.CONTEXT_OVERFLOW,  # retry after compact
compact_v5/MAIN/agent\core\errors.py:60:    BedrockErrorCategory.MAX_TOKENS_OVERFLOW,  # retry after compact
compact_v5/MAIN/agent\core\errors.py:61:    BedrockErrorCategory.BEDROCK_5XX_HTML,  # backoff
compact_v5/MAIN/agent\core\errors.py:62:    BedrockErrorCategory.REQUEST_TIMEOUT,  # retry once
compact_v5/MAIN/agent\core\errors.py:63:    BedrockErrorCategory.PAYLOAD_TOO_LARGE,  # retry after compact
compact_v5/MAIN/agent\core\errors.py:64:    BedrockErrorCategory.GATEWAY_TIMEOUT,  # backoff
compact_v5/MAIN/agent\core\errors.py:65:    BedrockErrorCategory.MALFORMED_RESPONSE,  # retry once
compact_v5/MAIN/agent\core\errors.py:66:    BedrockErrorCategory.DEPENDENCY_FAILURE,  # backoff
compact_v5/MAIN/agent\core\errors.py:70:def categorize_retryable(category: str) -> bool:
compact_v5/MAIN/agent\core\errors.py:128:def parse_max_tokens_context_overflow_error(exc) -> bool:
compact_v5/MAIN/agent\core\errors.py:146:def get_retry_after_ms(exc) -> int:
compact_v5/MAIN/agent\core\errors.py:147:    """Block L (R4 retry-after): parse Retry-After header value from exception.
compact_v5/MAIN/agent\core\errors.py:149:    Bedrock 429 responses include a Retry-After header (seconds). This helper
compact_v5/MAIN/agent\core\errors.py:151:    when no Retry-After is found.
compact_v5/MAIN/agent\core\errors.py:156:    - error message containing "Retry-After: 5": parses the trailing seconds
compact_v5/MAIN/agent\core\errors.py:163:    # Match "Retry-After: <value>" header pattern.
compact_v5/MAIN/agent\core\errors.py:164:    m = re.search(r"retry-after\s*:?\s*(\d+)", s, re.IGNORECASE)
compact_v5/MAIN/agent\core\errors.py:171:    m = re.search(r"retry-after\s*:?\s*([A-Z][a-z]{2},\s*\d.+\d{4}.+GMT)", s)
compact_v5/MAIN/agent\core\errors.py:182:class ErrorClassifier:
compact_v5/MAIN/agent\core\errors.py:199:            return BedrockErrorCategory.MAX_TOKENS_OVERFLOW, "compact_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:202:            return BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:204:            return BedrockErrorCategory.GATEWAY_TIMEOUT, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:206:            return BedrockErrorCategory.PAYLOAD_TOO_LARGE, "compact_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:208:            return BedrockErrorCategory.CONFLICT_409, "no_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:212:            return BedrockErrorCategory.REQUEST_TIMEOUT, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:214:            return BedrockErrorCategory.MALFORMED_RESPONSE, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:216:            return BedrockErrorCategory.SIGV4_FAILURE, "no_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:218:            return BedrockErrorCategory.DEPENDENCY_FAILURE, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:226:            return BedrockErrorCategory.VALIDATION_CACHE, "strip_cache_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:232:            return BedrockErrorCategory.CONTEXT_OVERFLOW, "compact_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:234:            return BedrockErrorCategory.VALIDATION_OTHER, "no_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:236:            return BedrockErrorCategory.THROTTLE, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:238:            return BedrockErrorCategory.SERVICE_UNAVAILABLE, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:240:            return BedrockErrorCategory.MODEL_NOT_READY, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:242:            return BedrockErrorCategory.ACCESS_DENIED, "no_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:249:            return BedrockErrorCategory.NETWORK, "backoff", str(exc)[:200]
compact_v5/MAIN/agent\core\errors.py:250:        return BedrockErrorCategory.UNKNOWN, "no_retry", str(exc)[:200]
compact_v5/MAIN/agent\core\query_engine.py:47:from .errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\core\query_engine.py:489:                category, recovery, debug = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\core\query_engine.py:491:                if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
compact_v5/MAIN/agent\core\__init__.py:6:  - core/errors.py       : Bedrock error classifier (Phase-1 ErrorClassifier extracted)
compact_v5/MAIN/agent\core\__init__.py:19:    BedrockErrorCategory,
compact_v5/MAIN/agent\core\__init__.py:20:    ErrorClassifier,
compact_v5/MAIN/agent\core\__init__.py:21:    categorize_retryable,
compact_v5/MAIN/agent\core\__init__.py:23:    parse_max_tokens_context_overflow_error,
compact_v5/MAIN/agent\core\__init__.py:24:    get_retry_after_ms,
compact_v5/MAIN/agent\runtime\bedrock_client.py:14:already battle-tested), but the helper classes (BedrockErrorCategory,
compact_v5/MAIN/agent\runtime\bedrock_client.py:15:ErrorClassifier, RetryPolicy) are imported from a temporary local module
compact_v5/MAIN/agent\runtime\bedrock_client.py:68:from core.errors import BedrockErrorCategory, ErrorClassifier  # noqa: F401
compact_v5/MAIN/agent\runtime\bedrock_client.py:303:                category, recovery, debug_msg = ErrorClassifier.classify(e)
compact_v5/MAIN/agent\runtime\bedrock_client.py:307:                    category == BedrockErrorCategory.VALIDATION_CACHE
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:17:  06. ErrorClassifier categorizes ValidationException/Throttling/etc
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:178:# 06 — ErrorClassifier categorizes Bedrock errors
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:179:# v4 ref: sagemaker_agent.py ErrorClassifier.classify
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:183:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:184:    cat, _, _ = ErrorClassifier.classify(Exception("ThrottlingException: rate"))
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:185:    assert cat == BedrockErrorCategory.THROTTLE
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:186:    cat, _, _ = ErrorClassifier.classify(Exception("ServiceUnavailable 503"))
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:187:    assert cat == BedrockErrorCategory.SERVICE_UNAVAILABLE
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:188:    cat, _, _ = ErrorClassifier.classify(Exception("ValidationException: prompt is too long"))
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:189:    assert cat == BedrockErrorCategory.CONTEXT_OVERFLOW
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:190:    cat, _, _ = ErrorClassifier.classify(Exception("AccessDenied: 403"))
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:191:    assert cat == BedrockErrorCategory.ACCESS_DENIED
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:328:                # ErrorClassifier matches "validationexception" + "cache_control"
compact_v5/MAIN/agent\tests\unit\test_errors.py:1:"""Phase 08 unit tests: core/errors.py — BedrockErrorCategory + ErrorClassifier.
compact_v5/MAIN/agent\tests\unit\test_errors.py:17:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:19:    cat, recovery, _ = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:20:    assert cat == BedrockErrorCategory.VALIDATION_CACHE
compact_v5/MAIN/agent\tests\unit\test_errors.py:25:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:27:    cat, recovery, _ = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:28:    assert cat == BedrockErrorCategory.CONTEXT_OVERFLOW
compact_v5/MAIN/agent\tests\unit\test_errors.py:33:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:35:    cat, recovery, _ = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:36:    assert cat == BedrockErrorCategory.VALIDATION_OTHER
compact_v5/MAIN/agent\tests\unit\test_errors.py:41:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:43:    cat, recovery, _ = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:44:    assert cat == BedrockErrorCategory.THROTTLE
compact_v5/MAIN/agent\tests\unit\test_errors.py:49:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:51:    cat, recovery, _ = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:52:    assert cat == BedrockErrorCategory.SERVICE_UNAVAILABLE
compact_v5/MAIN/agent\tests\unit\test_errors.py:57:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:59:    cat, recovery, _ = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:60:    assert cat == BedrockErrorCategory.MODEL_NOT_READY
compact_v5/MAIN/agent\tests\unit\test_errors.py:65:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:67:    cat, recovery, _ = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:68:    assert cat == BedrockErrorCategory.ACCESS_DENIED
compact_v5/MAIN/agent\tests\unit\test_errors.py:73:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:78:    cat, recovery, _ = ErrorClassifier.classify(EndpointConnectionError("connection failed"))
compact_v5/MAIN/agent\tests\unit\test_errors.py:79:    assert cat == BedrockErrorCategory.NETWORK
compact_v5/MAIN/agent\tests\unit\test_errors.py:84:    from core.errors import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:86:    cat, recovery, _ = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:87:    assert cat == BedrockErrorCategory.UNKNOWN
compact_v5/MAIN/agent\tests\unit\test_errors.py:92:    from core.errors import ErrorClassifier
compact_v5/MAIN/agent\tests\unit\test_errors.py:95:    _, _, debug = ErrorClassifier.classify(exc)
compact_v5/MAIN/agent\tests\unit\test_errors.py:102:    from core.errors import BedrockErrorCategory as CoreCat, ErrorClassifier as CoreCls
compact_v5/MAIN/agent\tests\unit\test_errors.py:103:    from runtime.bedrock_client import BedrockErrorCategory as RuntimeCat, ErrorClassifier as RuntimeCls
compact_v5/MAIN/agent\tests\integration\test_block_l.py:8:- test_categorize_retryable_18_error_types
compact_v5/MAIN/agent\tests\integration\test_block_l.py:9:- test_parse_max_tokens_overflow_recovers
compact_v5/MAIN/agent\tests\integration\test_block_l.py:35:def test_categorize_retryable_18_error_types():
compact_v5/MAIN/agent\tests\integration\test_block_l.py:46:    from core import BedrockErrorCategory, categorize_retryable
compact_v5/MAIN/agent\tests\integration\test_block_l.py:50:        BedrockErrorCategory.THROTTLE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:51:        BedrockErrorCategory.SERVICE_UNAVAILABLE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:52:        BedrockErrorCategory.MODEL_NOT_READY,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:53:        BedrockErrorCategory.NETWORK,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:54:        BedrockErrorCategory.VALIDATION_CACHE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:55:        BedrockErrorCategory.VALIDATION_OTHER,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:56:        BedrockErrorCategory.CONTEXT_OVERFLOW,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:57:        BedrockErrorCategory.ACCESS_DENIED,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:58:        BedrockErrorCategory.UNKNOWN,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:59:        BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:60:        BedrockErrorCategory.BEDROCK_5XX_HTML,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:61:        BedrockErrorCategory.REQUEST_TIMEOUT,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:62:        BedrockErrorCategory.PAYLOAD_TOO_LARGE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:63:        BedrockErrorCategory.CONFLICT_409,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:64:        BedrockErrorCategory.GATEWAY_TIMEOUT,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:65:        BedrockErrorCategory.MALFORMED_RESPONSE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:66:        BedrockErrorCategory.SIGV4_FAILURE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:67:        BedrockErrorCategory.DEPENDENCY_FAILURE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:72:        BedrockErrorCategory.THROTTLE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:73:        BedrockErrorCategory.SERVICE_UNAVAILABLE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:74:        BedrockErrorCategory.MODEL_NOT_READY,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:75:        BedrockErrorCategory.NETWORK,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:76:        BedrockErrorCategory.VALIDATION_CACHE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:77:        BedrockErrorCategory.CONTEXT_OVERFLOW,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:78:        BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:79:        BedrockErrorCategory.BEDROCK_5XX_HTML,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:80:        BedrockErrorCategory.REQUEST_TIMEOUT,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:81:        BedrockErrorCategory.PAYLOAD_TOO_LARGE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:82:        BedrockErrorCategory.GATEWAY_TIMEOUT,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:83:        BedrockErrorCategory.MALFORMED_RESPONSE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:84:        BedrockErrorCategory.DEPENDENCY_FAILURE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:87:        BedrockErrorCategory.VALIDATION_OTHER,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:88:        BedrockErrorCategory.ACCESS_DENIED,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:89:        BedrockErrorCategory.CONFLICT_409,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:90:        BedrockErrorCategory.SIGV4_FAILURE,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:91:        BedrockErrorCategory.UNKNOWN,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:95:        assert categorize_retryable(cat) is True, f"{cat} should be retryable"
compact_v5/MAIN/agent\tests\integration\test_block_l.py:97:        assert categorize_retryable(cat) is False, f"{cat} should NOT be retryable"
compact_v5/MAIN/agent\tests\integration\test_block_l.py:104:def test_parse_max_tokens_overflow_recovers():
compact_v5/MAIN/agent\tests\integration\test_block_l.py:107:        BedrockErrorCategory,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:108:        ErrorClassifier,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:109:        parse_max_tokens_context_overflow_error,
compact_v5/MAIN/agent\tests\integration\test_block_l.py:121:        assert parse_max_tokens_context_overflow_error(exc) is True, (
compact_v5/MAIN/agent\tests\integration\test_block_l.py:127:        assert parse_max_tokens_context_overflow_error(exc) is False
compact_v5/MAIN/agent\tests\integration\test_block_l.py:131:    cat, recovery, _ = ErrorClassifier.classify(
compact_v5/MAIN/agent\tests\integration\test_block_l.py:134:    assert cat == BedrockErrorCategory.MAX_TOKENS_OVERFLOW
compact_v5/MAIN/agent\tests\integration\test_block_l.py:173:# TEST_DESIGN row 4 — Retry-After header parsed
compact_v5/MAIN/agent\tests\integration\test_block_l.py:177:    """getRetryAfterMs parses 'Retry-After: 5' → 5000ms."""
compact_v5/MAIN/agent\tests\integration\test_block_l.py:178:    from core import get_retry_after_ms
compact_v5/MAIN/agent\tests\integration\test_block_l.py:180:    assert get_retry_after_ms(Exception("HTTP 429: Retry-After: 5")) == 5000
compact_v5/MAIN/agent\tests\integration\test_block_l.py:181:    assert get_retry_after_ms("Retry-After: 30") == 30000
compact_v5/MAIN/agent\tests\integration\test_block_l.py:182:    assert get_retry_after_ms("retry-after:60") == 60000
compact_v5/MAIN/agent\tests\integration\test_block_l.py:184:    assert get_retry_after_ms("ThrottlingException") == 0
compact_v5/MAIN/agent\tests\integration\test_block_l.py:185:    assert get_retry_after_ms("") == 0
compact_v5/MAIN/agent\tests\integration\test_block_l.py:281:    from core import BedrockErrorCategory, ErrorClassifier
compact_v5/MAIN/agent\tests\integration\test_block_l.py:285:         BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff"),
compact_v5/MAIN/agent\tests\integration\test_block_l.py:287:         BedrockErrorCategory.GATEWAY_TIMEOUT, "backoff"),
compact_v5/MAIN/agent\tests\integration\test_block_l.py:289:         BedrockErrorCategory.PAYLOAD_TOO_LARGE, "compact_retry"),
compact_v5/MAIN/agent\tests\integration\test_block_l.py:291:         BedrockErrorCategory.CONFLICT_409, "no_retry"),
compact_v5/MAIN/agent\tests\integration\test_block_l.py:293:         BedrockErrorCategory.MALFORMED_RESPONSE, "backoff"),
compact_v5/MAIN/agent\tests\integration\test_block_l.py:295:         BedrockErrorCategory.SIGV4_FAILURE, "no_retry"),
compact_v5/MAIN/agent\tests\integration\test_block_l.py:297:         BedrockErrorCategory.DEPENDENCY_FAILURE, "backoff"),
compact_v5/MAIN/agent\tests\integration\test_block_l.py:300:        cat, recovery, _ = ErrorClassifier.classify(exc)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest compact_v5/MAIN/agent/tests/integration/test_block_l.py -q' in D:\Github\sagemaker-coding-agent
2026-05-03T08:08:58.438464Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 15.4 seconds
Output:
Program 'python.exe' failed to run: The file cannot be accessed by the systemAt line:2 char:1
+ python -m pytest compact_v5/MAIN/agent/tests/integration/test_block_l ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
At line:2 char:1
+ python -m pytest compact_v5/MAIN/agent/tests/integration/test_block_l ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ResourceUnavailable: (:) [], ApplicationFailedException
    + FullyQualifiedErrorId : NativeCommandFailed
 

 exited 1 in 15448ms:
Program 'python.exe' failed to run: The file cannot be accessed by the systemAt line:2 char:1
+ python -m pytest compact_v5/MAIN/agent/tests/integration/test_block_l ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
At line:2 char:1
+ python -m pytest compact_v5/MAIN/agent/tests/integration/test_block_l ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ResourceUnavailable: (:) [], ApplicationFailedException
    + FullyQualifiedErrorId : NativeCommandFailed
 

codex
The focused test command could not run in this shell: `pytest` is not on PATH, and `python -m pytest` failed because `python.exe` is inaccessible in the environment. I’ll treat verification as static plus source comparison unless another test runner is discoverable.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Command py,python,pytest,uv -ErrorAction SilentlyContinue | Select-Object Name,Source' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$path='"'compact_v5/MAIN/agent/core/query_engine.py'; "'$lines=Get-Content $path; for($i=450; $i -le 515; $i++){ '"'{0,5}: {1}' -f "'$i, $lines[$i-1] }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$path='"'compact_v5/MAIN/agent/runtime/bedrock_client.py'; "'$lines=Get-Content $path; for($i=285; $i -le 335; $i++){ '"'{0,5}: {1}' -f "'$i, $lines[$i-1] }' in D:\Github\sagemaker-coding-agent
 succeeded in 430ms:
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

 succeeded in 512ms:
  450:                     f"[Budget exhausted: {used}/{total} iterations used. "
  451:                     "Adjust IterationBudget or start a new session.]"
  452:                 )
  453:                 stop_reason = "budget_exhausted"
  454:                 break
  455: 
  456:             # Phase 7 wiring contract: per-turn deferral + discovery merge.
  457:             visible_tools, deferred_names = apply_tool_search_deferral(
  458:                 tools, enabled=True,
  459:             )
  460:             if self._discovered_tool_names:
  461:                 # Promote previously-discovered tools from deferred â†’ visible.
  462:                 discovered = {n for n in self._discovered_tool_names if n in deferred_names}
  463:                 if discovered:
  464:                     promoted = [
  465:                         t for t in tools
  466:                         if t.name in discovered and t.name not in {v.name for v in visible_tools}
  467:                     ]
  468:                     visible_tools = visible_tools + promoted
  469:                     deferred_names = [n for n in deferred_names if n not in discovered]
  470: 
  471:             # If any names remain deferred, surface them as a system reminder
  472:             # so the model knows they exist and how to load them.
  473:             turn_messages = list(self.messages)
  474:             if deferred_names:
  475:                 turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)
  476: 
  477:             # Bedrock invocation.
  478:             try:
  479:                 response = self.client.chat(
  480:                     messages=turn_messages,
  481:                     system=effective_system_prompt,
  482:                     tools=_build_tools_api_payload(visible_tools),
  483:                     max_tokens=max_tokens,
  484:                     temperature=temperature,
  485:                     thinking_enabled=thinking_enabled,
  486:                     thinking_budget=thinking_budget,
  487:                 )
  488:             except Exception as exc:  # noqa: BLE001 â€” classify and surface
  489:                 category, recovery, debug = ErrorClassifier.classify(exc)
  490:                 output_fn(f"[Bedrock {category}: {debug}]")
  491:                 if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
  492:                     stop_reason = "context_overflow"
  493:                 else:
  494:                     stop_reason = "fatal_error"
  495:                 return QueryResult(
  496:                     text=last_text,
  497:                     messages=list(self.messages),
  498:                     stop_reason=stop_reason,
  499:                     turns_used=turns_used,
  500:                     budget_used=self.budget.used(),
  501:                     error=f"{category}: {debug}",
  502:                 )
  503: 
  504:             turns_used += 1
  505: 
  506:             # Block B (PORT_LOG #039+#040): record token usage + per-agent
  507:             # attribution. "parent" or sub-agent type-string. Best-effort â€”
  508:             # never break the agent loop if the singleton import fails.
  509:             try:
  510:                 from runtime.tokens import TOKENS as _TOKENS
  511:                 _TOKENS.add(
  512:                     response.usage or {},
  513:                     model_id=getattr(self.client, "model_id", None),
  514:                     agent_kind=self.agent_kind,
  515:                 )

2026-05-03T08:09:06.837483Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.7 seconds
Output:

Name       Source                                                       
----       ------                                                       
python.exe C:\Users\winst\AppData\Local\Microsoft\WindowsApps\python.exe
uv.exe     C:\Users\winst\.local\bin\uv.exe                             



 exited 1 in 721ms:

Name       Source                                                       
----       ------                                                       
python.exe C:\Users\winst\AppData\Local\Microsoft\WindowsApps\python.exe
uv.exe     C:\Users\winst\.local\bin\uv.exe                             



exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content compact_v5/MAIN/agent/core/retry.py | ForEach-Object { '"'{0,5}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 412ms:
    1: """V5 core/retry.py â€” jittered exponential backoff (Phase 8 extraction).
    2: 
    3: Per ADR-014: extracted verbatim from Phase-1 `runtime/bedrock_client.py`
    4: (which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).
    5: 
    6: PORT_LOG: #018.
    7: 
    8: Sleep curve:
    9:   attempt 0 -> ~1.0s   (0.7-1.3s with jitter)
   10:   attempt 1 -> ~2.0s   (1.4-2.6s)
   11:   attempt 2 -> ~4.0s   (2.8-5.2s)
   12:   attempt 3 -> ~8.0s   (5.6-10.4s)
   13:   attempt 4 -> stops   (MAX_RETRIES reached)
   14: 
   15: MAX_RETRIES=4 means up to 5 total attempts (initial + 4 retries).
   16: Behavior is byte-equivalent with Phase-1. `runtime/bedrock_client.py`
   17: re-imports these names for backwards compatibility.
   18: """
   19: from __future__ import annotations
   20: 
   21: import random
   22: 
   23: 
   24: class RetryPolicy:
   25:     """Jittered exponential backoff (v4 verbatim)."""
   26:     MAX_RETRIES = 4
   27:     BASE_SECONDS = 1.0
   28:     JITTER_FRACTION = 0.30
   29:     BACKOFF_RECOVERY = {"backoff"}
   30: 
   31:     @staticmethod
   32:     def should_retry(attempt: int, recovery: str) -> bool:
   33:         if attempt >= RetryPolicy.MAX_RETRIES:
   34:             return False
   35:         return recovery in RetryPolicy.BACKOFF_RECOVERY
   36: 
   37:     @staticmethod
   38:     def backoff_seconds(attempt: int) -> float:
   39:         base = RetryPolicy.BASE_SECONDS * (2 ** attempt)
   40:         jitter = base * RetryPolicy.JITTER_FRACTION * (2 * random.random() - 1)
   41:         return max(0.1, base + jitter)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$path='"'compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md'; "'$lines=Get-Content $path; for($i=293; $i -le 326; $i++){ '"'{0,5}: {1}' -f "'$i, $lines[$i-1] }' in D:\Github\sagemaker-coding-agent
 succeeded in 424ms:
  293: ### Block L (Error/retry/cache-break)
  294: 
  295: | # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
  296: |---|---|---|---|---|---|---|---|
  297: | L-1 | `getPromptTooLongTokenGap` parse + drop multiple groups (R4 #1) | Runnable | errors.ts:104-118 | 50 | HIGH | CLEAN | Closes compact-retry stalling PS-class bug. |
  298: | L-2 | `parseMaxTokensContextOverflowError` (R4 #2) | Runnable | withRetry.ts:550-595 | 30 | **MUST** | CLEAN | Without it, context-overflow 400s permanently fail the turn. |
  299: | L-3 | `getRateLimitResetDelayMs` Unix-sec parse (R4 #3) | Runnable | withRetry.ts:814-822 | 15 | HIGH | CLEAN | `anthropic-ratelimit-unified-reset` header. |
  300: | L-4 | `is529Error` + querySource-aware retry-vs-drop (R4 #4) | Runnable | withRetry.ts:610-621, 84-89 | 40 | HIGH | CLEAN | Prevents capacity-cascade amplification. |
  301: | L-5 | `FallbackTriggeredError` Opusâ†’Sonnet on 3x 529 (R4 #5) | Runnable | withRetry.ts:160-168 | 50 | HIGH | NEEDS-ADAPTATION | Bedrock fallback inference profile. |
  302: | L-6 | Stale-connection + keep-alive disable on retry (R4 #6) | Runnable | withRetry.ts:112-118 | 30 | HIGH | CLEAN | Bedrock SDK uses Node-equivalent http; rebuild client. |
  303: | L-7 | Persistent retry mode (env-gated) (R4 #7) | Runnable | withRetry.ts:96-104 | 80 | MED | NEEDS-ADAPTATION | `SAGEMAKER_UNATTENDED_RETRY=1` for SageMaker idle-disconnect. |
  304: | L-8 | `extractConnectionErrorDetails` SSL error walk + hint (R4 #8) | Runnable | errorUtils.ts:42-100 | 80 | HIGH | CLEAN | Corp Zscaler/proxy fixes. |
  305: | L-9 | `sanitizeAPIError` + `extractNestedErrorMessage` (R4 #9) | Runnable | errorUtils.ts:107-198 | 50 | **MUST** | CLEAN | Without it, Bedrock 5xx returns raw HTML to user. |
  306: | L-10 | Full PromptStateSnapshot 12 fields â†’ 8 Bedrock-applicable (R4 #10, #63) | Runnable | promptCacheBreakDetection.ts:170-241 | 30 | HIGH | CLEAN | Drop 4 subscription-specific. |
  307: | L-11 | `MAX_TRACKED_SOURCES=10` LRU eviction (R4 #11) | Runnable | promptCacheBreakDetection.ts:107 | 5 | MED | CLEAN | Trivial. |
  308: | L-12 | `MIN_CACHE_MISS_TOKENS=2_000` (R4 #12) | Runnable | promptCacheBreakDetection.ts:120 | 5 | MED | CLEAN | Combined predicate. |
  309: | L-13 | TTL-expiry classification (1h/5min/server-side) (R4 #13) | Runnable | promptCacheBreakDetection.ts:566-588 | 30 | HIGH | CLEAN | Turns useless break into actionable info. |
  310: | L-14 | `isExcludedModel` Haiku exclusion (R4 #14) | Runnable | promptCacheBreakDetection.ts:128-131 | 3 | **MUST** | CLEAN | Without it, Haiku 4.5 sub-agents emit constant false breaks. |
  311: | L-15 | `writeCacheBreakDiff` for debugging (R4 #15) | Runnable | promptCacheBreakDetection.ts:708-727 | 30 | LOW | CLEAN | Optional debug. |
  312: | L-16 | `stripCacheControl` + `cacheControlHash` dual hash (R4 #62) | Runnable | promptCacheBreakDetection.ts:160-168 | 20 | HIGH | CLEAN | Detects TTL/scope flips. |
  313: | L-17 | API error humanizer (Bedrock-only variant) (H2 N3) | Hermes | run_agent.py:3552-3590 | 40 | HIGH | NEEDS-ADAPTATION | Drop Cloudflare branch; keep JSON-body + status_code. |
  314: | L-18 | Roll-back to last assistant turn helper (H2 N2) | Hermes | run_agent.py:3317-3346 | 30 | MED | CLEAN | Defensive utility. |
  315: | L-19 | One-extra primary-recovery after max retries (H3 G18) | Hermes | run_agent.py:6988-7066 | 30 | MED | CLEAN | Bedrock can hit transient TCP. |
  316: | L-20 | Three-tier recovery ladder pattern (H3 G19) | Hermes | run_agent.py:5528-5610 | 0 (architectural) | HIGH | NEEDS-ADAPTATION | "retry â†’ IAM token refresh â†’ user-error" architectural lesson. |
  317: | L-21 | Daemon-thread Bedrock call for Ctrl-C responsiveness (H3 G1) | Hermes | run_agent.py:5637-5781 | 80 | HIGH | NEEDS-ADAPTATION | v4 blocking; v5 should adopt thread pattern. |
  318: | L-22 | Stale non-stream call detector (context-scaled deadline) (H3 G2) | Hermes | run_agent.py:5704-5762 | 50 | HIGH | CLEAN | Bedrock can hang in throttling-retry. |
  319: | L-23 | Heartbeat callback every 30s during long calls (H3 G3) | Hermes | run_agent.py:5720-5724 | 20 | HIGH | CLEAN | Keeps ipykernel alive. |
  320: | L-24 | `_rebuild_anthropic_client` Bedrock branch (H3 G11) | Hermes | run_agent.py:5617-5635 | 20 | HIGH | CLEAN | Defensive; v5 may have latent bug. |
  321: | L-25 | `invalidate_runtime_client(region)` on stale (H3 G12) | Hermes | run_agent.py:5685, 5938-5941 | 15 | HIGH | CLEAN | Don't reuse poisoned pool. |
  322: | L-26 | `toError`/`shortErrorStack`/`isFsInaccessible`/`classifyAxiosError` (R8 #11, #12) | Runnable | utils/errors.ts:1-238 | 80 | HIGH | CLEAN | 5-frame stack truncation; ENOENT family. |
  323: | L-27 | ShellError + ConfigParseError + TelemetrySafeError classes (R8 #13) | Runnable | utils/errors.ts:3-101 | 30 | MED | CLEAN | Structured errors carry stdout/stderr/code/path/default. |
  324: | L-28 | Bedrock Guardrails config (`bedrock.guardrail.*`) (H1 D) | Hermes | run_agent.py:1287-1312 | 25 | MED | NEEDS-ADAPTATION | Insurance compliance; PII redaction. |
  325: 
  326: **Block L total NEW: ~966 LOC.**

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$path='"'_archive/compare_code/gg-claude-code-runnable/src/services/api/errorUtils.ts'; "'$lines=Get-Content $path; for($i=100; $i -le 210; $i++){ if($i -le $lines.Length){ '"'{0,5}: {1}' -f "'$i, $lines[$i-1] } }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "extract_nested_error_message|nested|5xx|html|HTML|errorUtils" compact_v5/MAIN/agent/tests compact_v5/_phase_2/wave_6/TEST_DESIGN.md compact_v5/_status/V5_DESIGN_DECISIONS.md' in D:\Github\sagemaker-coding-agent
 succeeded in 477ms:
  100: }
  101: 
  102: /**
  103:  * Strips HTML content (e.g., CloudFlare error pages) from a message string,
  104:  * returning a user-friendly title or empty string if HTML is detected.
  105:  * Returns the original message unchanged if no HTML is found.
  106:  */
  107: function sanitizeMessageHTML(message: string): string {
  108:   if (message.includes('<!DOCTYPE html') || message.includes('<html')) {
  109:     const titleMatch = message.match(/<title>([^<]+)<\/title>/)
  110:     if (titleMatch && titleMatch[1]) {
  111:       return titleMatch[1].trim()
  112:     }
  113:     return ''
  114:   }
  115:   return message
  116: }
  117: 
  118: /**
  119:  * Detects if an error message contains HTML content (e.g., CloudFlare error pages)
  120:  * and returns a user-friendly message instead
  121:  */
  122: export function sanitizeAPIError(apiError: APIError): string {
  123:   const message = apiError.message
  124:   if (!message) {
  125:     // Sometimes message is undefined
  126:     // TODO: figure out why
  127:     return ''
  128:   }
  129:   return sanitizeMessageHTML(message)
  130: }
  131: 
  132: /**
  133:  * Shapes of deserialized API errors from session JSONL.
  134:  *
  135:  * After JSON round-tripping, the SDK's APIError loses its `.message` property.
  136:  * The actual message lives at different nesting levels depending on the provider:
  137:  *
  138:  * - Bedrock/proxy: `{ error: { message: "..." } }`
  139:  * - Standard Anthropic API: `{ error: { error: { message: "..." } } }`
  140:  *   (the outer `.error` is the response body, the inner `.error` is the API error)
  141:  *
  142:  * See also: `getErrorMessage` in `logging.ts` which handles the same shapes.
  143:  */
  144: type NestedAPIError = {
  145:   error?: {
  146:     message?: string
  147:     error?: { message?: string }
  148:   }
  149: }
  150: 
  151: function hasNestedError(value: unknown): value is NestedAPIError {
  152:   return (
  153:     typeof value === 'object' &&
  154:     value !== null &&
  155:     'error' in value &&
  156:     typeof value.error === 'object' &&
  157:     value.error !== null
  158:   )
  159: }
  160: 
  161: /**
  162:  * Extract a human-readable message from a deserialized API error that lacks
  163:  * a top-level `.message`.
  164:  *
  165:  * Checks two nesting levels (deeper first for specificity):
  166:  * 1. `error.error.error.message` â€” standard Anthropic API shape
  167:  * 2. `error.error.message` â€” Bedrock shape
  168:  */
  169: function extractNestedErrorMessage(error: APIError): string | null {
  170:   if (!hasNestedError(error)) {
  171:     return null
  172:   }
  173: 
  174:   // Access `.error` via the narrowed type so TypeScript sees the nested shape
  175:   // instead of the SDK's `Object | undefined`.
  176:   const narrowed: NestedAPIError = error
  177:   const nested = narrowed.error
  178: 
  179:   // Standard Anthropic API shape: { error: { error: { message } } }
  180:   const deepMsg = nested?.error?.message
  181:   if (typeof deepMsg === 'string' && deepMsg.length > 0) {
  182:     const sanitized = sanitizeMessageHTML(deepMsg)
  183:     if (sanitized.length > 0) {
  184:       return sanitized
  185:     }
  186:   }
  187: 
  188:   // Bedrock shape: { error: { message } }
  189:   const msg = nested?.message
  190:   if (typeof msg === 'string' && msg.length > 0) {
  191:     const sanitized = sanitizeMessageHTML(msg)
  192:     if (sanitized.length > 0) {
  193:       return sanitized
  194:     }
  195:   }
  196: 
  197:   return null
  198: }
  199: 
  200: export function formatAPIError(error: APIError): string {
  201:   // Extract connection error details from the cause chain
  202:   const connectionDetails = extractConnectionErrorDetails(error)
  203: 
  204:   if (connectionDetails) {
  205:     const { code, isSSLError } = connectionDetails
  206: 
  207:     // Handle timeout errors
  208:     if (code === 'ETIMEDOUT') {
  209:       return 'Request timed out. Check your internet connection and proxy settings'
  210:     }

 succeeded in 720ms:
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:183:### Block E+F — HTML chat rendering + cell 2 widgets + complete session UI + IterationBudgetWidget + ThinkingBudgetWidget
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:187:| `test_render_chat_user_message` | T1 | `render_chat()` produces HTML with user message in correct color | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:188:| `test_render_chat_assistant_markdown` | T1 | `_render_assistant_markdown()` converts markdown → HTML (code blocks, tables, lists) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:194:| `test_iteration_budget_widget_shows_used_total` | T1 | widget HTML shows `<progress>` + `used/total` + color cue (closes PS#2 visible UI) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:195:| `test_thinking_budget_widget_shows_on_off` | T1 | widget HTML shows `thinking=ON\|OFF, budget=N tokens` (closes PS#4 visible UI) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:325:| `test_extract_nested_error_message_humanizes_5xx_html` | T1 | Bedrock 5xx with raw HTML → user sees clean error message (R4 #9 MUST) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:366:| `test_tool_web_fetch_html_to_markdown` | T2 | mocked HTTP response → `web_fetch` returns markdown text | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:368:| `test_tool_create_html_via_write_file_documented` | T1 | docs note: `create_html` not a separate tool; use `write_file(*.html)` (Wave 6 design note) | $0 |
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:443:User directive 2026-05-01: status, git push, HTML, rezip must all be part of implementation plan.
compact_v5/_phase_2/wave_6/TEST_DESIGN.md:459:| **Update HTML companion docs** if architecture changed (Block E+F changes UI; Block A changes compaction; Block B changes cost; Block H changes memory; Block N changes parallel exec). HTML is at `compact_v5/docs/` if exists OR `compact_v4/MAIN/agent/docs/` for v4-comparison HTML | per relevant Block | manual or scripted | $0 |
compact_v5/_status/V5_DESIGN_DECISIONS.md:128:## ADR-004 — Reference HTMLs copied to `compact_v5/docs/htmls/`
compact_v5/_status/V5_DESIGN_DECISIONS.md:132:- Source: User instruction 2026-04-30 + existing v4 HTMLs in `compact_v4/MAIN/agent/` and `PS_ClaudeCode_Insights/`
compact_v5/_status/V5_DESIGN_DECISIONS.md:135:- ADDITION (reference HTMLs to support v5 build context). Not a code feature.
compact_v5/_status/V5_DESIGN_DECISIONS.md:141:- Future v5 architecture HTMLs (to be generated in Phase 13) will sit alongside, enabling v5-vs-v4-vs-Runnable comparison.
compact_v5/_status/V5_DESIGN_DECISIONS.md:144:- Token cost: 0 (HTMLs are not loaded by the agent runtime).
compact_v5/_status/V5_DESIGN_DECISIONS.md:145:- Repo size: +500 KB (6 HTMLs).
compact_v5/_status/V5_DESIGN_DECISIONS.md:155:- compact_v5/docs/htmls/PS_DEEP_DIVE_RUNNABLE.html (Runnable architecture deep-dive)
compact_v5/_status/V5_DESIGN_DECISIONS.md:156:- compact_v5/docs/htmls/PS_FLOWCHART_RUNNABLE.html (Runnable flowchart)
compact_v5/_status/V5_DESIGN_DECISIONS.md:157:- compact_v5/docs/htmls/PS_FLOWCHART_V4.html (v4 flowchart, for comparison)
compact_v5/_status/V5_DESIGN_DECISIONS.md:158:- compact_v5/docs/htmls/PS_RUNNABLE_VS_LANGGRAPH.html (Runnable vs LangGraph comparison)
compact_v5/_status/V5_DESIGN_DECISIONS.md:159:- compact_v5/docs/htmls/HERMES_VS_CODING_AGENT_v4.html (Hermes vs v4 comparison)
compact_v5/_status/V5_DESIGN_DECISIONS.md:160:- compact_v5/docs/htmls/v4_architecture.html (v4 architecture HTML)
compact_v5/_status/V5_DESIGN_DECISIONS.md:163:- compact_v5/docs/htmls/v5_architecture.html (NEW — generated at Phase 13)
compact_v5/_status/V5_DESIGN_DECISIONS.md:164:- compact_v5/docs/htmls/PS_FLOWCHART_V5.html (NEW — generated at Phase 13)
compact_v5/_status/V5_DESIGN_DECISIONS.md:165:- compact_v5/docs/htmls/PS_V5_VS_RUNNABLE.html (NEW — comparison generated at Phase 13)
compact_v5/_status/V5_DESIGN_DECISIONS.md:444:**Why diff_widget.py:** PS_actual_use_problems.md captures a real pattern where v4 users approved edits without seeing the actual change content, then discovered later that the model had edited the wrong region or stripped useful code. Showing the colored diff inline (with ±3 lines context) lets the user catch misplaced edits BEFORE clicking Approve. Runnable solved this with `EditTool/UI.tsx` (Ink JSX). v5 ipywidgets equivalent: an HTML widget with `+` green / `-` red / context gray + a `<details>` block for click-to-expand-full-file.
compact_v5/_status/V5_DESIGN_DECISIONS.md:450:- Token cost (static prompt): 0 (the diff widget is a Python class that returns HTML; not in the system prompt).
compact_v5/_status/V5_DESIGN_DECISIONS.md:452:- Code complexity: ~150 LOC `ui/diff_widget.py` (uses stdlib `difflib.unified_diff` + simple HTML escape + `<details>` markup). No new dependencies (`ipywidgets` already used by v4 chat.ipynb; only HTML strings emitted in Phase 4).
compact_v5/_status/V5_DESIGN_DECISIONS.md:464:  - `ui/diff_widget.py` — generates HTML diff strings (red removed, green added, gray context, file path header, ±3 lines context, `<details>`-wrapped full-file expansion). Phase 11 wires into the ipywidgets approval flow.
compact_v5/_status/V5_DESIGN_DECISIONS.md:473:- `ui/diff_widget.py` renders HTML for ipywidgets, not Ink JSX. Same UX semantics: colored diff, file header, click-to-expand. Constraint = `.ipynb`.
compact_v5/_status/V5_DESIGN_DECISIONS.md:918:- 10 skills directories (`batch`, `clara`, `design`, `html`, `reflexion`, `report`, `review`, `security-review`, `simplify`, `verify`) ported BYTE-FOR-BYTE under `skills/` (no content edits). User memory + V5_PLAN.md require this verbatim preservation.
compact_v5/_status/V5_DESIGN_DECISIONS.md:986:- **ChatUI is much smaller** (~150 LOC vs v4's ~2000 LOC). Most of v4's complexity is HTML rendering of message history; v5 delegates to ipywidgets and lets the browser handle layout. Phase 11 also intentionally drops v4's complex chat-display HTML rendering for the minimal MVP — operators get text output + widgets, not the v4 full-fidelity chat display.
compact_v5/_status/V5_DESIGN_DECISIONS.md:1009:- Phase 11 does NOT ship: full v4 chat-display HTML rendering (defer to Phase 13 polish), v4's compact/clean buttons (microcompact lands as separate phase if at all), parallel sub-agent visualization, model-switcher widget (CONFIG.model_id static), session-history persistence (SessionManager from Phase 1 already exists; Phase 11 doesn't auto-restore).
compact_v5/_status/V5_DESIGN_DECISIONS.md:1059:  - `tests/parity/test_parity_non_critical.py` — 10 non-critical scenarios (≥9/10 must pass). Covers: tool result truncation length, error message exact wording, skill CSO format advisory, audit log line format, widget HTML exact markup, depth-exceeded message wording, plan-mode error message wording, tool-search wire format details, frontmatter parser edge cases, env-details line count.
compact_v5/_status/V5_DESIGN_DECISIONS.md:1085:- **REPLACEMENT** of the v4 ship pipeline for v5: `compact_v5/_rebuild_zip.py` (adapted to walk the nested package layout) + `compact_v5/verify_ship_zip.py` (REUSED verbatim from v4 with light tweaks for v5 file list).
compact_v5/_status/V5_DESIGN_DECISIONS.md:1089:- v4's `_rebuild_zip.py` walks `MAIN/agent/` (monolith). v5 walks `compact_v5/MAIN/agent/` AND preserves the nested-package layout (`core/`, `tools/`, `skills/`, etc.) so imports work in the unzipped directory.
compact_v5/_status/V5_DESIGN_DECISIONS.md:1101:  - `compact_v5/_rebuild_zip.py` — adapted from v4. Walks `MAIN/agent/` in v5 layout. Preserves nested packages. Excludes tests/changelogs/_status/docs/_archive/__pycache__.
compact_v5/_status/V5_DESIGN_DECISIONS.md:1120:- #036 — v4 _rebuild_zip.py → compact_v5/_rebuild_zip.py (ADAPT — walks v5 nested-package layout).
compact_v5/_status/V5_DESIGN_DECISIONS.md:1137:- 5xx HTML error humanization (R4 #9 MUST).
compact_v5/_status/V5_DESIGN_DECISIONS.md:1148:  (MAX_TOKENS_OVERFLOW / BEDROCK_5XX_HTML / REQUEST_TIMEOUT /
compact_v5/_status/V5_DESIGN_DECISIONS.md:1154:- extract_nested_error_message — humanizes HTML / JSON / plain
compact_v5/_status/V5_DESIGN_DECISIONS.md:1183:- 5xx HTML humanization (R4 #9 MUST).
compact_v5/_status/V5_DESIGN_DECISIONS.md:2567:| B+3 | 4-line cost block format (R11 N10) | 15 | **Block I** (UI/widgets) | `ui/widgets.py:CostWidget.render_html` (4-line block: total / per-model / per-agent / cache) | `test_cost_widget_renders_4_line_block` (Block I) |
compact_v5/_status/V5_DESIGN_DECISIONS.md:2707:v5.0.0 reorganized the v4 monolith into nested packages (`runtime/`, `core/`,
compact_v5/MAIN/agent/tests\tools\test_phase4_mutating_tools.py:145:    target = workspace / "deep" / "nested" / "file.txt"
compact_v5/MAIN/agent/tests\parity\test_parity_non_critical.py:17:  05. widget HTML markup contains progress element
compact_v5/MAIN/agent/tests\parity\test_parity_non_critical.py:128:# 05 — Widget HTML markup contains <progress> tag
compact_v5/MAIN/agent/tests\parity\test_parity_non_critical.py:131:def test_noncritical_05_budget_widget_html_has_progress_element():
compact_v5/MAIN/agent/tests\parity\test_parity_non_critical.py:135:    html = w.render_html()
compact_v5/MAIN/agent/tests\parity\test_parity_non_critical.py:136:    assert "<progress" in html
compact_v5/MAIN/agent/tests\parity\test_parity_non_critical.py:137:    assert "max=" in html
compact_v5/MAIN/agent/tests\parity\test_parity_critical.py:280:        "batch", "clara", "design", "html", "reflexion",
compact_v5/MAIN/agent/tests\parity\test_parity_critical.py:355:    # PS #2 — html visibly shows used/total
compact_v5/MAIN/agent/tests\parity\test_parity_critical.py:356:    assert "0/10" in bw.render_html()
compact_v5/MAIN/agent/tests\parity\test_parity_critical.py:358:    assert "2/10" in bw.render_html()
compact_v5/MAIN/agent/tests\parity\test_parity_critical.py:359:    # PS #4 — html visibly shows thinking ON + budget
compact_v5/MAIN/agent/tests\parity\test_parity_critical.py:360:    th_html = tw.render_html()
compact_v5/MAIN/agent/tests\parity\test_parity_critical.py:361:    assert "ON" in th_html
compact_v5/MAIN/agent/tests\parity\test_parity_critical.py:362:    assert "8192" in th_html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:3:Locks the contract for ADR-010 + ADR-011: HTML colored diff widget for
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:8:  - render_inline_diff returns valid HTML containing change markers + file header.
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:13:  - HTML escaping: untrusted content is escaped (no raw `<script>` injection).
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:30:    html = render_inline_diff("/work/foo.py", before, after)
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:31:    assert "/work/foo.py" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:33:    assert "line 2" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:35:    assert "line 2 modified" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:37:    assert "#1a7f37" in html or "1a7f37" in html  # added green
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:38:    assert "#cf222e" in html or "cf222e" in html  # removed red
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:44:    html = render_inline_diff("/work/x.txt", same, same)
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:45:    assert "No changes" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:46:    assert "/work/x.txt" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:49:def test_inline_diff_html_escapes_special_chars():
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:50:    """Untrusted content must be HTML-escaped so a model can't inject <script>."""
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:54:    html = render_inline_diff("/work/<bad>.py", before, after)
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:56:    assert "<script>alert" not in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:58:    assert "&lt;script&gt;alert" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:60:    assert "&lt;bad&gt;" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:67:    html = render_expandable_diff("/work/x.txt", before, after)
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:68:    assert "<details" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:69:    assert "Show full-file diff" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:71:    assert "/work/x.txt" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:77:    html = render_new_file_diff("/work/new.py", content)
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:78:    assert "/work/new.py" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:79:    assert "NEW FILE" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:80:    # Every line should appear (HTML-escaped form is identical for ASCII).
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:81:    assert "first" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:82:    assert "second" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:83:    assert "third" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:85:    assert "#cf222e" not in html and "cf222e" not in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:90:    html = render_new_file_diff("/work/empty.txt", "")
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:91:    assert "/work/empty.txt" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:92:    assert "empty file" in html.lower() or "no content" in html.lower()
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:101:    html = render_inline_diff("/work/foo.py", before, after, context=1)
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:104:    assert "NEW LINE" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:106:    assert "@@" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:130:    html = render_inline_diff("/x.txt", "alpha\nbeta", "alpha\nbeta\n")
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:131:    assert "No content changes" in html
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:132:    assert "newline" in html.lower()
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:134:    html2 = render_inline_diff("/x.txt", "alpha\nbeta\n", "alpha\nbeta")
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:135:    assert "No content changes" in html2
compact_v5/MAIN/agent/tests\unit\test_diff_widget.py:136:    assert "newline" in html2.lower()
compact_v5/MAIN/agent/tests\unit\test_skill_manager.py:23:    "batch", "clara", "design", "html", "reflexion",
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:67:    """When `diff_html` is provided, PermissionDialog includes it in
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:76:        diff_html=diff_sample,
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:81:    assert dlg.diff_html == diff_sample
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:311:    receives a non-empty `diff_html` from ui/diff_widget."""
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:324:    # (we'll spy on PermissionDialog.__init__ to capture diff_html).
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:329:    captured: Dict[str, Any] = {"diff_html": None}
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:334:        captured["diff_html"] = self.diff_html
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:381:    assert captured["diff_html"] is not None, (
compact_v5/MAIN/agent/tests\integration\test_block_c_plus.py:385:    assert "hello" in captured["diff_html"] or "v5" in captured["diff_html"]
compact_v5/MAIN/agent/tests\integration\test_block_l.py:10:- test_extract_nested_error_message_humanizes_5xx_html
compact_v5/MAIN/agent/tests\integration\test_block_l.py:40:    bedrock_5xx_html, request_timeout, payload_too_large,
compact_v5/MAIN/agent/tests\integration\test_block_l.py:60:        BedrockErrorCategory.BEDROCK_5XX_HTML,
compact_v5/MAIN/agent/tests\integration\test_block_l.py:79:        BedrockErrorCategory.BEDROCK_5XX_HTML,
compact_v5/MAIN/agent/tests\integration\test_block_l.py:139:# TEST_DESIGN row 3 — humanize 5xx HTML errors (R4 #9 MUST)
compact_v5/MAIN/agent/tests\integration\test_block_l.py:142:def test_extract_nested_error_message_humanizes_5xx_html():
compact_v5/MAIN/agent/tests\integration\test_block_l.py:143:    """Bedrock 5xx with raw HTML → user sees clean error message."""
compact_v5/MAIN/agent/tests\integration\test_block_l.py:144:    from core import extract_nested_error_message
compact_v5/MAIN/agent/tests\integration\test_block_l.py:146:    # HTML title.
compact_v5/MAIN/agent/tests\integration\test_block_l.py:147:    html_title = "<html><head><title>503 Service Unavailable</title></head><body>x</body></html>"
compact_v5/MAIN/agent/tests\integration\test_block_l.py:148:    out = extract_nested_error_message(html_title)
compact_v5/MAIN/agent/tests\integration\test_block_l.py:152:    html_h1 = "<html><body><h1>Internal Server Error</h1><p>x</p></body></html>"
compact_v5/MAIN/agent/tests\integration\test_block_l.py:153:    out = extract_nested_error_message(html_h1)
compact_v5/MAIN/agent/tests\integration\test_block_l.py:157:    html_body = "<html><body>The server encountered an error.</body></html>"
compact_v5/MAIN/agent/tests\integration\test_block_l.py:158:    out = extract_nested_error_message(html_body)
compact_v5/MAIN/agent/tests\integration\test_block_l.py:163:    out = extract_nested_error_message(json_err)
compact_v5/MAIN/agent/tests\integration\test_block_l.py:168:    out = extract_nested_error_message(plain)
compact_v5/MAIN/agent/tests\integration\test_block_l.py:284:        (Exception("<html><body>503 Service Unavailable</body></html>"),
compact_v5/MAIN/agent/tests\integration\test_block_l.py:285:         BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff"),
compact_v5/MAIN/agent/tests\integration\test_block_h_plus.py:306:    # render_html on it. Build a minimal stub.
compact_v5/MAIN/agent/tests\integration\test_block_h_plus.py:308:        def render_html(self) -> str:
compact_v5/MAIN/agent/tests\integration\test_subagent.py:307:# Test 12 — Codex Phase-09 BLOCKER lock: nested-recursion depth
compact_v5/MAIN/agent/tests\integration\test_subagent.py:310:def test_nested_subagent_recursion_blocked_at_max_depth():
compact_v5/MAIN/agent/tests\integration\test_subagent.py:314:    spawn_subagent, every nested `task` would reset to depth 0 and unbounded
compact_v5/MAIN/agent/tests\integration\test_subagent.py:347:def test_nested_spawn_depth_propagates_through_child_engine():
compact_v5/MAIN/agent/tests\integration\test_subagent.py:348:    """End-to-end nested-spawn lock: a CHILD engine passing through `task`
compact_v5/MAIN/agent/tests\integration\test_subagent.py:351:    Without the BLOCKER fix, every nested spawn would reset to depth=0.
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:180:def test_iteration_budget_widget_html_reflects_consumption():
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:186:    html_initial = w.render_html()
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:187:    assert "0/10" in html_initial
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:189:    html_after = w.render_html()
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:190:    assert "3/10" in html_after
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:195:    otherwise returns the HTML fallback string. Both are truthy."""
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:208:def test_thinking_budget_widget_html_shows_state():
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:216:    html = w.render_html()
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:217:    assert "ON" in html
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:218:    assert "8192" in html
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:221:    html2 = w.render_html()
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:222:    assert "OFF" in html2
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:273:def test_console_ui_render_returns_html_object_when_ipython_available():
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:275:    return an `IPython.display.HTML` object so `display(ui.render())` in
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:276:    the notebook shows rendered HTML, not the literal string."""
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:285:    # In any environment that has IPython (test env does), it's an HTML
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:288:        from IPython.display import HTML
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:289:        assert isinstance(handle, HTML), (
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:290:            f"render() returned {type(handle).__name__}, expected IPython.display.HTML"
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:312:    assert "0/20" in widget.render_html()
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:320:    html_after = widget.render_html()
compact_v5/MAIN/agent/tests\integration\test_notebook_smoke.py:322:    assert "0/20" not in html_after, (

codex
**Findings**

1. **HTTP-date `Retry-After` parsing misses normal header casing.**  
   [errors.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/errors.py:171) parses the HTTP-date branch without `re.IGNORECASE`, so `Retry-After: Wed, ... GMT` returns `0` even though integer headers are case-insensitive and the contract requires HTTP-date support. The tests only cover integer seconds at [test_block_l.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_l.py:180).  
   Minimal fix: add `re.IGNORECASE` to the date regex and add a future-date test.

2. **`extract_nested_error_message` does not actually extract nested API JSON shapes.**  
   Runnable checks `error.error.message` and deeper `error.error.error.message`; see reference behavior mirrored in the comments at `errorUtils.ts:165-190`. The v5 implementation only accepts top-level string keys at [errors.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/errors.py:97), so `{"error":{"message":"..."}}` falls through to raw JSON text instead of the humanized message.  
   Minimal fix: after JSON parse, check nested `error.error.message` first, then `error.message`, and run those strings through the same HTML cleanup path.

3. **`REQUEST_TIMEOUT` is under-matched for common timeout exceptions.**  
   The classifier only catches `request_timeout`, `request-timeout`, or `408` at [errors.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/errors.py:209). Common `ReadTimeout`, `ConnectTimeout`, `APIConnectionTimeoutError`, or `"request timed out"` shapes fall through to `NETWORK` or `UNKNOWN`, while Runnable treats timeout as its own branch.  
   Minimal fix: include `"timeout" in cls_name` and `"timeout" / "timed out"` in `msg_lower`, after the `GATEWAY_TIMEOUT` branch.

**Axis A — Errors / Bugs / Regressions**

Verdict: **CHANGES_REQUESTED**.  
The category set and most ordering are present, but the three parsing/classification gaps above miss stated Block L behavior.

**Axis B — v5 Architecture + Goals Fit**

Verdict: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.  
The shape fits the existing `core/` architecture: one module extension, one new cache-break module, and focused tests. The T2 daemon/heartbeat deferral is declared in ADR-036 and skip reasons.

**Axis C — Reference-Repo Coverage**

Verdict: **SOME_DROPPED**.  
The broad pieces are ported, but Retry-After HTTP-date parsing, nested API error extraction, and timeout classification are incomplete versus the Runnable behavior.

**FINAL: APPROVE_WITH_FIXES**

I could not run the focused pytest locally: `pytest` is not on PATH, and the WindowsApps `python.exe` shim is inaccessible in this shell.
2026-05-03T08:10:18.821055Z ERROR codex_core::session: failed to record rollout items: thread 019dece0-9836-7022-829a-d6b2f8d4edf9 not found
tokens used
106,925
**Findings**

1. **HTTP-date `Retry-After` parsing misses normal header casing.**  
   [errors.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/errors.py:171) parses the HTTP-date branch without `re.IGNORECASE`, so `Retry-After: Wed, ... GMT` returns `0` even though integer headers are case-insensitive and the contract requires HTTP-date support. The tests only cover integer seconds at [test_block_l.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_l.py:180).  
   Minimal fix: add `re.IGNORECASE` to the date regex and add a future-date test.

2. **`extract_nested_error_message` does not actually extract nested API JSON shapes.**  
   Runnable checks `error.error.message` and deeper `error.error.error.message`; see reference behavior mirrored in the comments at `errorUtils.ts:165-190`. The v5 implementation only accepts top-level string keys at [errors.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/errors.py:97), so `{"error":{"message":"..."}}` falls through to raw JSON text instead of the humanized message.  
   Minimal fix: after JSON parse, check nested `error.error.message` first, then `error.message`, and run those strings through the same HTML cleanup path.

3. **`REQUEST_TIMEOUT` is under-matched for common timeout exceptions.**  
   The classifier only catches `request_timeout`, `request-timeout`, or `408` at [errors.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/errors.py:209). Common `ReadTimeout`, `ConnectTimeout`, `APIConnectionTimeoutError`, or `"request timed out"` shapes fall through to `NETWORK` or `UNKNOWN`, while Runnable treats timeout as its own branch.  
   Minimal fix: include `"timeout" in cls_name` and `"timeout" / "timed out"` in `msg_lower`, after the `GATEWAY_TIMEOUT` branch.

**Axis A — Errors / Bugs / Regressions**

Verdict: **CHANGES_REQUESTED**.  
The category set and most ordering are present, but the three parsing/classification gaps above miss stated Block L behavior.

**Axis B — v5 Architecture + Goals Fit**

Verdict: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.  
The shape fits the existing `core/` architecture: one module extension, one new cache-break module, and focused tests. The T2 daemon/heartbeat deferral is declared in ADR-036 and skip reasons.

**Axis C — Reference-Repo Coverage**

Verdict: **SOME_DROPPED**.  
The broad pieces are ported, but Retry-After HTTP-date parsing, nested API error extraction, and timeout classification are incomplete versus the Runnable behavior.

**FINAL: APPROVE_WITH_FIXES**

I could not run the focused pytest locally: `pytest` is not on PATH, and the WindowsApps `python.exe` shim is inaccessible in this shell.
