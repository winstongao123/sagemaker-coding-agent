# Independent Claude CLI Review - S3 Follow-up Tool Discipline

You are an independent reviewer for compact_v5. Review the staged diff in `compact_v5_test_evidence/final_results/S3_FOLLOWUP_TOOL_DISCIPLINE_diff.patch` and the active source tree.

Context: The user observed these real-use regressions in SageMaker with Sonnet 4.5:
1. A simple S3 follow-up like "pick two files to investigate" triggered another broad S3 scan instead of reusing prior S3 results.
2. Thinking was shown after tool results/final answer; user wants thinking, if enabled, as collapsed display-only text before subsequent action/result, and no thinking display when thinking is off.
3. Tool IDs were exposed in the normal card summary and confused non-technical users.
4. Artifact questions like "where is the file" caused a filesystem search instead of using remembered generated artifact paths.
5. Generated deliverables defaulted into the v5 runtime folder (`compact_v5_ship`) when workspace was not configured.
6. ASCII diagram requests produced non-ASCII output.
7. Small S3/report tasks updated AGENT_STATUS.md, adding cost and polluting context.
8. Truncated S3 listings were summarized as complete.

Review goals:
- Verify the fix addresses those eight issues without weakening v5 coding behavior.
- Check no architecture drift: active tree is flat `compact_v5/`; no `compact_v5/compact_v5` assumptions; no rewrite of core engine beyond small guards.
- Check tool-use correctness: S3 follow-ups should reuse prior object paths and use `aws_s3_preview`; full S3 rescans should be capped unless explicitly requested.
- Check cost controls: simple S3 inventory/follow-ups disable thinking for that turn only; no global model/cache/compaction changes.
- Check UI: thinking is a separate collapsed row before the answer/action, not duplicated below metrics; tool card summary hides raw `toolu_...` IDs; details may still include ID for debugging.
- Check artifact policy: relative deliverables in runtime package workspaces rebase to `CONFIG.user_artifacts_root`, source/project files remain project-relative.
- Check tests are meaningful and pass.

Known verification already run:
- `py -3.10 -m py_compile compact_v5/core/query_engine.py compact_v5/ui/chat_ui.py compact_v5/agent.py compact_v5/tools/aws_s3_preview.py compact_v5/tools/artifacts.py compact_v5/tools/v4_documents.py compact_v5/tools/write_file.py compact_v5/runtime/state.py compact_v5/runtime/config.py compact_v5/security/manager.py`
- `py -3.10 -m pytest compact_v5/tests -q` -> 47 passed.
- `git diff --check` -> no whitespace errors.

Return one of:
- `APPROVE` with evidence bullets, or
- `REQUEST_CHANGES` with concrete file/line findings and required fixes.

Focus on high/medium correctness regressions. Do not nitpick wording unless it creates user confusion or cost/tool-use risk.
