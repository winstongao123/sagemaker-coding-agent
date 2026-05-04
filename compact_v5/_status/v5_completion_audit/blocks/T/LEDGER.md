# Block T Ledger

Status: IMPLEMENTING
Date: 2026-05-04

Canonical scope: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:354-371`.

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T-1 | `notebook_edit` (v4 :5921 schema :7275) (R2 finding #1, V1 gap #2) | v4 `sagemaker_agent.py:5921 + 7275`; `SYNTHESIS_MASTER.md:358` | MUST | FALSE-POSITIVE-ALREADY-IN-V5 | `tools/notebook_edit.py`; explicit Block T PORT_LOG row | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Audit existing Phase 4 code/test evidence and add explicit T row evidence. | pending |
| T-2 | `view_image` (v4 :6419 schema :7307) (V1 gap #3) | v4 `sagemaker_agent.py:6419 + 7307`; `SYNTHESIS_MASTER.md:359` | MUST | FALSE-POSITIVE-ALREADY-IN-V5 | `tools/view_image.py`; explicit Block T PORT_LOG row | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Audit existing Phase 4 code/test evidence and add explicit T row evidence. | pending |
| T-3 | `SemanticSearch` class verbatim port (V1 gap #4) | v4 `sagemaker_agent.py:6461-6610`; `SYNTHESIS_MASTER.md:360` | MUST | CLEAN | `tools/semantic_search.py` | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Verify current semantic_search depth against v4 class and fill gaps. | pending |
| T-4 | WebFetch fold-ins: 15-min URL LRU cache + same-host redirect + Turndown (R3 row 20) | Runnable `utils.ts:63-243`; `SYNTHESIS_MASTER.md:361`; user drop 2026-05-03 | HIGH | NEEDS-ADAPTATION / USER-DROPPED-ACTIVE-TOOL | `tools/web_fetch.py` disabled guard plus explicit user-approved disposition | NONE_FOUND | NONE_FOUND | PORT_LOG #103-A likely | ADR-038 likely | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Verify explicit user drop evidence and disabled module lock tests; ledger as non-blocking only if evidence is concrete. | pending |
| T-5 | `tool_skill` + `tool_skill_propose_patch` registry rows (R2 finding #2) | v4 `sagemaker_agent.py:6674, 6703`; `SYNTHESIS_MASTER.md:362` | LOW | doc-only | Block D dispatcher / skills manager evidence | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Audit existing Block D/I skill command evidence and add explicit T row evidence. | pending |
| T-6 | `semanticBoolean` / `semanticNumber` coerce (R8 #2) | Runnable `utils/semantic*.ts`; `SYNTHESIS_MASTER.md:363` | MED | CLEAN | shared coercion utility and tool schema consumers | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Implement/verify semantic boolean/number coercion for quoted Bedrock args. | pending |
| T-7 | `readFileInRange` fast/streaming with FileTooLargeError (R8 #35) | Runnable `utils/readFileInRange.ts`; `SYNTHESIS_MASTER.md:364` | HIGH | NEEDS-ADAPTATION | Python large-file range reader / read_file path | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Implement/verify range read and FileTooLargeError adaptation without streaming. | pending |
| T-8 | `lockfile` lazy wrapper (R8 #36) | Runnable `utils/lockfile.ts:1-44`; `SYNTHESIS_MASTER.md:365` | LOW | CLEAN | Python lockfile helper, likely portalocker-equivalent or stdlib fallback | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Implement/verify lazy lockfile wrapper or document stdlib constraint with tests. | pending |
| T-9 | `tagMessagesWithToolUseID` (R3 row utils.ts) | Runnable `tools/utils.ts`; `SYNTHESIS_MASTER.md:366` | DROPPED | low-value | no streaming UI placeholders | NONE_FOUND | NO_TEST_JUSTIFICATION: pending verification of no-streaming/low-value drop evidence | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Verify categorical drop evidence; needs explicit non-blocking constraint/user approval if not implemented. | pending |
| T-10 | API limits constants (5MB image / 20MB PDF / 100 pages) (R8 #29) | Runnable `constants/apiLimits.ts`; `SYNTHESIS_MASTER.md:367` | HIGH | CLEAN | API/tool limit constants and fail-fast checks | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Implement/verify API limits constants and fail-fast tests. | pending |
| T-11 | Tool result limits + per-message budget (R8 #30) | Runnable `constants/toolLimits.ts`; `SYNTHESIS_MASTER.md:368` | HIGH | CLEAN | tool result limits / per-message budget enforcement | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Implement/verify 200K char per-message aggregate cap. | pending |
| T-12 | XML tag constants (R8 #27) | Runnable `constants/xml.ts`; `SYNTHESIS_MASTER.md:369` | LOW | CLEAN | centralized XML tag constants | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | NOT_YET_CLAUDE_REVIEWED | pending | MISSING | Implement/verify centralized XML tag names. | pending |

EXPECTED_ROWS: 12
LEDGER_ROWS: 12
SHIPPED: 0
PARTIAL: 0
MISSING: 12
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 12

