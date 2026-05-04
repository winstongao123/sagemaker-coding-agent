---

# Block C Closure Review (Iter 1)

I independently reconstructed Block C scope from `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:89-113`, then compared the regenerated row list to `blocks/C/LEDGER.md` and inspected each row's claimed code/test/PORT_LOG/ADR evidence on disk.

**Independently regenerated Block C row list (from SYNTHESIS_MASTER.md:93-111):** C-1, C-2, C-3, C-4, C-5, C-6, C-7, C-8, C-9, C-10, C-11, C-12, C-13, C-14, C-15, C-16, C-17, C-18, C-19. Total = 19. Matches `LEDGER_ROWS: 19` and `EXPECTED_ROWS: 19` in the ledger.

```text
EXPECTED ROW COUNT: 19
LEDGER ROW COUNT: 19
DISPOSITION COUNTS:
- SHIPPED: 19
- PARTIAL: 0
- MISSING: 0
- DEFERRED_USER_APPROVED: 0
- DROPPED_USER_APPROVED: 0
- N/A_CONSTRAINT: 0

REVIEWED ROWS:
- C-1: APPROVE - SecurityManager class confirmed at security/manager.py:123-462, singleton at :670, redact_secrets at :440; PORT_LOG #135; ADR-049; unit suite 69/3 skipped passed.
- C-2: APPROVE - SECRET_PATTERNS at security/manager.py:53-95 contains 38 entries (13 v4 + 25 gitleaks); redact_secrets at :440; tests test_block_c.py:139,149,175 cover count, gitleaks samples, and redaction; PORT_LOG #136; ADR-049.
- C-3: APPROVE - normalize_quotes helper at security/edit_file_safety.py:44-57 AND wired into runtime at tools/edit_file.py:160-162 (both file content and old_string normalized before exact match). Reviewer-flagged risk resolved: runtime path uses quote-normalized matching, not helper-only. Test at test_block_c.py:260; PORT_LOG #137.
- C-4: APPROVE - preserve_quote_style at edit_file_safety.py:64-85, runtime wiring at tools/edit_file.py:187-188 re-wraps new_string when original used curly quotes. Test at test_block_c.py:276; PORT_LOG #138.
- C-5: APPROVE - detect_utf16_bom at edit_file_safety.py:97-115; tools/edit_file.py:139-145 selects encoding based on detection. Test at test_block_c.py:285; PORT_LOG #139.
- C-6: APPROVE - is_unc_path_windows at edit_file_safety.py:122-143 with explicit \\?\ and \\.\ extended-prefix exclusion; tools/edit_file.py:90-98 refuses UNC pre-path-validation. Lock tests at test_block_c.py:334 and :553 cover both inclusion and the iter-1 finding-fix exclusion; PORT_LOG #140.
- C-7: APPROVE - normalize_line_endings/restore_line_endings at edit_file_safety.py:150-168; tools/edit_file.py:160-161 normalizes to LF for matching, :200-201 restores original eol on write. Test at test_block_c.py:314; PORT_LOG #141.
- C-8: APPROVE - is_staleness_false_positive at edit_file_safety.py:175-205; tools/edit_file.py:121-127 falls back to content compare on mtime drift. Test at test_block_c.py:314; PORT_LOG #142.
- C-9: APPROVE - interpret_command_result helper at security/bash_safety.py:43-64 with grep/rg/diff/find/test exit-code semantics; tools/bash.py:161-166 emits "[exit code: N - <semantic>]" annotations. Test at test_block_c.py:353; PORT_LOG #143.
- C-10: APPROVE - destructive_command_warning catalog at bash_safety.py:71-113 (rm -rf, force-push, DROP TABLE, kubectl delete, terraform destroy, redis flushall, dd of=/dev/, etc.); tools/bash.py:177-181 annotates output. Test at test_block_c.py:368; PORT_LOG #144.
- C-11: APPROVE_WITH_FIXES - helper has_cd_git_compound_with_bare_repo at bash_safety.py:120-139 with lock test at test_block_c.py:387; PORT_LOG #145; ADR-049 explicitly accepts helper-level ship for Block C with approval-flow consumption deferred to Block C+/permission block. Helper is detection-only and not consumed by tools/bash.py executor or any approval gate. See FINDINGS.
- C-12: APPROVE_WITH_FIXES - helper has_multiple_cd at bash_safety.py:149-158 with lock test at test_block_c.py:397; PORT_LOG #146. SYNTHESIS_MASTER says "requires approval" but no approval gate consumes the helper in Block C; ADR-049 accepts helper-level ship and points to later block. See FINDINGS.
- C-13: APPROVE - split_pipe_segments + pipe_segment_permission_check at bash_safety.py:165-215 with quote-aware splitter; tools/bash.py:182-186 annotates "[!destructive-pipe-segment] ..." in output. Test at test_block_c.py:406; PORT_LOG #147.
- C-14: APPROVE - extract_bash_comment_label at bash_safety.py:225-238 (UI label, LOW priority, no runtime wiring required); test at test_block_c.py:426; PORT_LOG #148.
- C-15: APPROVE - BINARY_EXTENSIONS set + is_binary_content (8KB null-byte sniff) at runtime/file_safety.py:8-57; tools/read_file.py:128 refuses binary content via probe-then-sniff. Tests at test_block_c.py:440 (helper) and :478 (read_file refusal lock); PORT_LOG #149.
- C-16: APPROVE - escape_xml/escape_xml_attr at runtime/tool_surface.py:254-270; xml_tag at :273-274 routes content through escape_xml. Block T regression at test_block_t.py 17/14 skipped pass after the behavior change; helper test at test_block_c.py:440 also exercises xml_tag. PORT_LOG #150.
- C-17: APPROVE_WITH_FIXES - cwd context (contextvars) wired end-to-end: runtime/execution_context.py:10-25 plus consumers at tools/bash.py:221-224 and tools/python_exec.py:236-237,295-298. Combined abort signal helper at execution_context.py:28-45 lock-tested at test_block_c.py:467-475 BUT no production caller (bash, python_exec, query engine) consumes it; long-running subprocess cancellation continues to flow through v4-style security.manager.kill_active_process. ADR-049 + DECISIONS.md item 6 acknowledge this constraint. SYNTHESIS_MASTER labels this row HIGH/NEEDS-ADAPTATION; SYNTHESIS_MASTER C+3 declares "already covered" by C-17, so callers expecting the abort-signal piece may not exist. See FINDINGS.
- C-18: APPROVE - repair_tool_call_arguments at security/json_repair.py:35-136 with the multi-pass ladder (as-is, strip, paren-fix, truncated-value, missing-brace, lone-quote, escape-invalid-chars, {} fallback); core/query_engine.py:1167-1170 routes string tool_call.input through it before dispatch. Test at test_block_c.py:192; PORT_LOG #152.
- C-19: APPROVE - _escape_invalid_chars_in_json_strings at json_repair.py:139-165 (state-machine that escapes \n/\r/\t inside JSON strings only, respecting \-escape state); attempt 4 of repair ladder at :122-129 invokes it. Test at test_block_c.py:192,212; PORT_LOG #153.

FINDINGS:
- LOW C-11 (security/bash_safety.py:120, tools/bash.py): helper detects cd-into-bare-repo + git compound but no approval/refusal site consumes it. SYNTHESIS_MASTER row tags this a "Security bug class" - the detection is necessary but not sufficient until approval-flow wiring lands. ADR-049 + DECISIONS.md item 4 explicitly accept helper-level ship in Block C and defer enforcement to a later bash/permission block. Acceptable as scoped, but the user should confirm that Block C+ or a follow-up block will pick up the consumer wiring before final ship.
- LOW C-12 (security/bash_safety.py:149, tools/bash.py): same pattern as C-11. SYNTHESIS_MASTER text says "`cd a && cd b && X` requires approval"; the helper exists but no caller flips approval based on it. DECISIONS.md item 4 explicitly accepts helper-only ship. Acceptable as scoped, but flag for user awareness.
- LOW C-17 (runtime/execution_context.py:28, tools/bash.py, tools/python_exec.py): combined_abort_signal helper is lock-tested but unused at runtime - bash and python_exec only consume current_cwd, not the abort event. SYNTHESIS_MASTER C+3 declares cancellation "already covered" by C-17, which implies end-to-end consumption was expected. Practical impact is bounded because v4 security.manager.kill_active_process() (security/manager.py:508-516) still provides the existing process-kill path, so this is not a regression vs v4. ADR-049 + DECISIONS.md item 6 acknowledge the runtime-ownership constraint. Acceptable as scoped given v4 parity, but if the user expected new async cooperative-abort behavior beyond v4, that capability is helper-only.
- INFO ledger sentinels: all 19 rows carry historical_review = NOT_YET_CLAUDE_REVIEWED and reviewer_verdict = pending. Per 03_LEDGER_SCHEMA.md these are valid temporary values for a block before its first compliant Claude review. Both fields must be replaced with the path to this saved review and the row-level verdicts after this iter1 lands.
- INFO PORT_LOG commit SHAs: rows #135-#153 carry "(pending)" in the commit_sha column. Worker self-review and STATUS.md state this is intentional: SHA gets filled after Claude review and the close-commit lands. Not ship-blocking, but must be filled at block close.

DISPUTED FINDINGS:
- NONE: worker has not disputed anything in this iter1 cycle (REVIEWER_VERDICT.md is empty/not-yet-reviewed).

REMAINING SHIP-BLOCKING ROWS: 0

VERDICT: APPROVE_WITH_FIXES
SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW
```

## Closure Notes For The User (not part of the required verdict template)

Block C ships 19 of 19 canonical rows with code, test, PORT_LOG, and ADR evidence. The three LOW findings are all worker-acknowledged design choices recorded in `blocks/C/DECISIONS.md` (items 4 and 6) and ADR-049, not silent narrowing. They concern depth of runtime consumption rather than presence of helper code:

1. C-11/C-12 ship as detection helpers; approval-flow wiring is deferred to a later block.
2. C-17's abort-signal half is helper-only; cwd half is fully wired; v4 `kill_active_process` covers existing cancellation needs.

Before closing the block, replace `NOT_YET_CLAUDE_REVIEWED` and `pending` sentinels in `LEDGER.md` with this iter1 review path and per-row `reviewer_verdict`, and fill the `(pending)` commit SHAs in `V5_RUNNABLE_PORT_LOG.md` rows #135-#153 with the Block C close commit. No AWS/R-tier spend was requested or run by this review.
