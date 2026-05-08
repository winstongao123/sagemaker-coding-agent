# Block C Decisions

Date: 2026-05-04

## ADR Link

Primary decision record: `compact_v5/_status/V5_DESIGN_DECISIONS.md` ADR-049.

## Decisions

1. Keep `SecurityManager` as the v4-derived security boundary and close C-1 with explicit redo evidence instead of duplicating the class.

2. Implement C-2 redaction as `SecurityManager.redact_secrets()` using the same regex catalog as `scan_secrets()`. This keeps detection/redaction behavior in one audited surface.

3. Keep edit-file safety helpers in `security/edit_file_safety.py` and wire them through `tools/edit_file.py`. This preserves the Runnable semantics without growing the tool executor into a second safety library.

4. Treat C-11 and C-12 as shipped runtime-consumed safety evidence in Block C. Claude iter1 flagged helper-only evidence, so SecurityManager now consumes both helpers in `validate_command()` and blocks those cwd-sensitive command shapes before execution.

5. Adapt Runnable `combinedAbortSignal` and `AsyncLocalStorage` cwd to Python with `asyncio.Event` fan-in and `contextvars`.

6. For C-17, wire cwd and pre-launch abort consumption into runtime paths now. QueryEngine forwards abort events into tool context, and bash/python_exec combine and check them before launching subprocess work. The current local runtime still uses `security.manager.kill_active_process()` for already-running process termination; C-17's cooperative abort helper covers the pre-launch/shared-state path without replacing that v4 kill surface.

7. Route `xml_tag()` text through XML escaping. The focused Block T regression passed after this behavior change, so existing XML tag callers remain compatible.

No defer/drop/user decision is required for Block C at this point. No AWS/R-tier spend has been run or requested.
