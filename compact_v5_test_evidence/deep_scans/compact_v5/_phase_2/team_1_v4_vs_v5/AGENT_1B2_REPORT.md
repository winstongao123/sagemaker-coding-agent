# V4 to V5 Runtime Contracts Analysis

**Date**: 2026-04-30
**Investigator**: Agent B-2

## Summary of Findings

### 1. Runtime Safety: Rate Limits & Cost Enforcement
**v4**: max_user_messages_per_minute (line 1073), max_user_messages_per_session (line 1074), session_cost_limit (line 1082) all enforced at run() entry (lines 8731-8740) with AUDIT logging.
**v5**: Config fields present in runtime/config.py (lines 82-83, 90) but NOT enforced. No per-minute sliding window. No cost limit check. Audit logging replaced by logging.info() only.
**GAP**: MISSING enforcement + structured audit logging.
**Severity**: HIGH | Effort: M

### 2. Concurrency: Threading Locks
**v4**: _GLOBAL_EXEC_LOCK (line 8229), _FILES_READ_LOCK (line 3765), _RECENT_DIFFS_LOCK (line 4415), AuditLogger._lock (line 2180).
**v5**: IterationBudget._lock (budget.py:40), SkillManager._pending_lock (manager.py:122), _file_read_tracking._LOCK (tools:29). MISSING: _GLOBAL_EXEC_LOCK for bash/python_exec budget protection.
**GAP**: No global exec budget lock despite config field existing.
**Severity**: HIGH | Effort: M

### 3. File-State Tracking (Runnable Parity)
**v4**: _FILES_READ set + _FILE_READ_TIMES dict, lock-protected, enforced by edit_file/write_file.
**v5**: Full port in tools/_file_read_tracking.py with mark_read(), was_read(), is_stale(). Lock present at line 29. Enforcement in edit_file.py:98 + write_file.py:90.
**Status**: PHASE 4 stub, on track for Phase 8/9 migration to core/session.
**Severity**: LOW | Effort: S

### 4. Permission/Approval Flow Wiring
**v4**: on_approval() callback with AUDIT logging (lines 9232, 9449). Structured deny message (lines 9451-9453).
**v5**: Diff widget built in ui/diff_widget.py (lines 54-137) but NOT wired into QueryEngine or tool dispatch. Dead code.
**GAP**: Diff widget rendering complete but not called at approval points.
**Severity**: MED | Effort: M

### 5. Audit-Log Surface
**v4**: AuditLogger class (line 2173) writes JSONL with sanitization (lines 2210-2215). Every rate limit, approval, execution block logged.
**v5**: AuditLogger missing entirely. Only logging.info/warning calls (query_engine.py:251, 400). No structured JSONL, no session isolation, no parameter sanitization.
**GAP**: Audit trail for billing/accountability deleted.
**Severity**: HIGH | Effort: L (port existing class)

### 6. System Prompt Content Fidelity
**v4**: Single monolithic SYSTEM_PROMPT (line 8029-8380), ~5000 tokens. Identity, Tool Classes, Doing Tasks, Critique Handling, Executing Actions, Output Style.
**v5**: 19 sectioned .md files (prompt/), ~2498 tokens. Sections map v4 regions (identity.md, tool_classes.md, doing_tasks.md, critique_handling.md, executing_actions.md, output_style.md).
**Status**: Compression strategy, core content retained.
**Severity**: LOW | Effort: S

### 7. Error Message Recovery Hints
**v4**: Blocked-bash message (lines 9472-9476): "STILL AVAILABLE: read_file, grep, glob... Most diagnostics can finish with these." Deny message (9451-9453).
**v5**: NOT FOUND. Generic warnings only (query_engine.py:251, 269). No recovery guidance when limits hit.
**GAP**: No user-facing guidance at failure points.
**Severity**: MED | Effort: M

### 8. Cost-Ceiling Visibility
**v4**: TokenTracker banners: "Budget: 42% ($2.09 / $5.00)". Warnings at 80%, blocks at 100%.
**v5**: IterationBudgetWidget shows iteration count only. No cost banners. TokenTracker deferred to Phase 12.
**Status**: Expected deferral, but Phase 8 should not claim "cost visibility" as complete.
**Severity**: MED | Effort: M (Phase 12)

### 9. Session Continuity (AGENT_STATUS Load)
**v4**: AGENT_STATUS.md auto-load enabled (line 1097). Loaded at run() entry (line 7654). Bounded to 4000 chars for sub-agents (line 7750).
**v5**: Config present (runtime/config.py:104-105). Loading implemented in subagent/handoff.py (line 53-80). NOT wired into QueryEngine.run().
**GAP**: Configured but not loaded at main agent startup.
**Severity**: MED | Effort: S

### 10. Tool-Listing Budget Cap
**v4**: SkillManager.list_for_prompt(budget_tokens) (line 2838) caps skill descriptions to fit.
**v5**: Equivalent mechanism present (skills/manager.py). tool_search_discovered_names() wiring in place (query_engine.py:14).
**Status**: Parity maintained.
**Severity**: LOW | Effort: S

---

## Critical Integration Checklist

- [ ] Port rate-limit enforcement into QueryEngine.run() entry + structured AUDIT logging
- [ ] Add _GLOBAL_EXEC_LOCK for bash/python_exec budget protection
- [ ] Wire diff_widget.render_*_diff() into approval callback
- [ ] Port AuditLogger class (v4 lines 2173-2258) to core/audit.py with sanitization
- [ ] Wire AGENT_STATUS load into QueryEngine.__init__()
- [ ] Add recovery-hint messages to bash/python_exec limit blocks (v4 lines 9472-9505)
- [ ] Plan Phase 12 CostWidget implementation (track actual $ vs iteration count)

**Estimated effort**: ~3 engineer-days. Recommend tackling HIGH items before Phase 9 sub-agent concurrency (critical for safety).

---

## End Report

This investigation confirms v5 ships feature-narrowed (~40% LOC reduction) but with **critical runtime-safety gaps**: rate-limit enforcement, global exec budgeting, and audit logging are absent or disabled. These are not phase-deferred but actually deleted. Recommend remediation before Phase 9.

