## Review: APPROVE

The staged diff addresses all eight regressions with bounded, well-scoped guards. No architecture drift, no engine rewrite, no global model/cache/compaction changes. 47 tests pass.

### Evidence per issue

1. **S3 follow-up triggers fresh scan** — `core/query_engine.py:1352-1364` caps `aws_s3_list` to 2 calls per follow-up turn (`_s3_list_calls_this_run`), and `_inject_s3_followup_reminder_if_needed` (`:2386-2407`) anchors the model to recent `s3://bucket/key` paths extracted from history. New `aws_s3_preview` tool offers bounded Range reads.
2. **Thinking shown after answer** — `ui/chat_ui.py` removes `meta["thinking"]` from `_render_turn_meta` (`:1041-1057`), and the engine now streams `[thinking]\n…` via `output_fn` (`core/query_engine.py:875-882`). UI router (`:1255-1260`) appends a separate collapsed `thinking` message before the assistant text. Test `test_live_thinking_renders_before_assistant_and_metrics` asserts the order; default-off thinking emits nothing.
3. **Tool IDs in summary confuse users** — `_render_tool_card` (`ui/chat_ui.py:657-674`) drops `id_part` from the summary and moves "Tool id: …" to the bottom of `<details>`. Test asserts `toolu_…` is not in the pre-summary slice.
4. **Artifact questions search filesystem** — `runtime/state.py` adds durable `artifacts.json`, `tools/artifacts.py:record_artifact` writes on every successful `write_file`/`create_*`, and `_inject_artifact_reminder_if_needed` returns those paths on phrases like "where is the file" / "cannot find".
5. **Deliverables land in runtime folder** — `runtime/config.py:user_artifacts_root` default `~/sageagent_workspace`. `tools/artifacts.py:resolve_user_artifact_path` rebases relative deliverable-extension files only when `workspace` basename is `compact_v5`/`compact_v5_ship`. Source files (`.py` etc.) stay project-relative. `security/manager.py:_build_singleton` adds `user_artifacts_root` to `allowed_paths` so writes don't trip path validation.
6. **Non-ASCII output despite ASCII request** — `_requests_ascii_only(self._run_requested_text)` injected as `context["ascii_only"]` in dispatch (`:1592-1597`); `_ascii_contract_check` in `write_file.py` and `v4_documents.py` (word/md/notebook/pdf) returns an error before write.
7. **AGENT_STATUS.md spam on small tasks** — `_is_blocked_status_doc_update` (`core/query_engine.py:2566-2585`) blocks `write_file`/`edit_file` of `AGENT_STATUS.md` when request is S3 inventory/follow-up and not an explicit status/handoff request. Scope is narrow (only S3 tasks) so regular coding tasks still update status.
8. **Truncated S3 summarized as complete** — `_s3_truncation_guard_message` (`:2451-2487`) injects a one-shot reminder if the model claims "complete/all/entire/everything" without a partial qualifier while recent `aws_s3_list` output contains "output truncated" or "continuation_token".

### Cost/tool-use sanity
- Thinking is disabled only for the simple-inventory or follow-up turn (`agent.py:341-357`); model/cache/compaction unchanged.
- `_simple_s3_low_cost` requires the engine has actual S3 paths in history before treating the message as a follow-up — won't fire on unrelated "investigate" prompts.
- `_s3_list_calls_this_run` only enforces on follow-up requests, so initial inventories with pagination still work.
- `aws_s3_preview` is in `PLAN_MODE_ALLOWED_TOOLS` (read-only), bedrock-only guard respected, hard cap 65536 bytes, binary content not dumped.

### Minor (non-blocking) notes
- `[truncation guard: …]` from `output_fn` isn't in `_is_status_output` prefixes, so it renders as an assistant chunk. Same was already true for `[intent-drift guard: …]` and `[final-claim guard: …]` (the latter is whitelisted, the former isn't), so this is consistent with existing behavior.
- `security/manager._build_singleton` does `os.makedirs(artifact_root, exist_ok=True)` at module import — creates `~/sageagent_workspace` even in mock/test sessions. Harmless but worth noting.
- `"document" in requested and "status" in requested` in `_is_blocked_status_doc_update` is the intended `or … or (E and F)` per Python precedence; fine.

No regressions to core engine, guards, or v5 coding behavior. Approved.
