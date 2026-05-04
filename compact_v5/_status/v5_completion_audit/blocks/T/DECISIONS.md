# Block T Decisions

Date: 2026-05-04

## T-4 web_fetch

Disposition: `DROPPED_USER_APPROVED`.

Evidence:

- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` row #103-A records
  `web_fetch DECISION-DROP-PER-USER 2026-05-03`.
- `compact_v5/_status/V5_DESIGN_DECISIONS.md` ADR-038 records the same user
  directive and rationale: the v5 single-user SageMaker context is typically
  VPC-isolated, so active web_fetch would be an SSRF surface with no benefit.
- `compact_v5/MAIN/agent/tools/web_fetch.py` raises `NotImplementedError` at
  module import.
- `compact_v5/MAIN/agent/tools/__init__.py` keeps the import and registration
  commented out with disabled markers.
- Block T tests lock module-disabled and not-in-registry behavior.

## T-9 tagMessagesWithToolUseID

Disposition: `N/A_CONSTRAINT`.

Reason:

Runnable's helper tags streaming/UI placeholder messages after tool-use
generation. v5.0.1 is synchronous Bedrock/SageMaker and has no streaming UI
placeholder layer. QueryEngine emits Bedrock `tool_result` blocks directly with
`tool_use_id` in both sequential and parallel paths, so the invariant is already
preserved without a post-hoc tagger.

Evidence:

- `compact_v5/MAIN/agent/core/query_engine.py` `_dispatch_single_tool_call`
  returns direct `tool_result` blocks with `tool_use_id`.
- Block T tool-result-budget test verifies QueryEngine tool-result blocks still
  carry `tool_use_id`.
- Block N parallel-dispatch regression subset verifies parallel safe calls use
  the same single-tool dispatch pipeline that preserves audit/error logging,
  JSON repair, and repetition tracking.

## T-10 view_image API limit

Decision:

The canonical Block T row names API limits of 5 MB image / 20 MB PDF /
100 pages. The previous `view_image` implementation used 20 MB for images.
Block T changes `view_image` to import `MAX_IMAGE_BYTES = 5 * 1024 * 1024`
from `runtime.tool_surface`.

No AWS/R-tier test was run.
