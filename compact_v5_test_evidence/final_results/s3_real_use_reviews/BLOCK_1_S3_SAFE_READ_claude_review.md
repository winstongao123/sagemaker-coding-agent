# Block 1 — S3 Safe Read Path: Independent Review

**Verdict: APPROVE_WITH_NITS**

The fix achieves the stated goal: a read-only `aws_s3_list` tool replaces the broken `aws s3` / `boto3 via python_exec` paths, with a directive error message guiding the model away from re-trying the blocked CLI. No destructive S3 surface is exposed. Tests cover bucket-list, prefix/object-list, Bedrock-only block, registration shape, and the CLI-redirect guidance — the local proof gate is satisfied; deferring real AWS smoke to Block 7 is acceptable given the stated block order.

---

## Findings

### HIGH
None.

### MEDIUM

**M1 — `aws s3` regex requires a trailing space** (`compact_v5/security/manager.py:300`)
`\baws\s+s3(?:api)?\s+` matches `aws s3 ls` but **not** a bare `aws s3` (no trailing arg). Unlikely to occur in practice, but the model could trip the generic Layer-1 allowlist message instead of the helpful "use `aws_s3_list`" guidance. Suggest `\baws\s+s3(?:api)?\b` to also catch the trailing-only form.

**M2 — Single-page listing silently truncates** (`compact_v5/tools/aws_s3_list.py:102-126`)
`list_objects_v2` is called once with `MaxKeys=max_items` (capped at 200). Buckets/prefixes with >200 entries return only the first page. The user is told "narrow prefix or increase max_items," but max_items is hard-capped at 200, so deep buckets cannot be fully enumerated through this tool. Acceptable for a v1, but worth a `ContinuationToken` follow-up or a clearer error message stating the 200 ceiling.

### LOW

**L1 — Read-only tool with `requires_approval=True`** (`aws_s3_list.py:144`)
Defensible (cloud egress + credential use), but inconsistent with the other plan-mode read-only tools (`read_file`, `glob`, `grep`, `list_dir`) which don't gate. If intentional, fine; if accidental, drop the gate so the tool is friction-free in plan mode.

**L2 — `bucket` input not normalized** (`aws_s3_list.py:76`)
A user/model passing `bucket="s3://foo/"` or `bucket="foo/"` will hit a boto3 client error rather than a friendly "strip the `s3://` prefix" message. Two-line normalization would harden the UX.

**L3 — Region/profile not configurable** (`aws_s3_list.py:51-56`)
`boto3.client("s3")` uses ambient defaults. Fine for the SageMaker IAM-role case, but if a notebook ever needs cross-region inventory, there's no knob. Out of scope for this block.

**L4 — Schema lacks `additionalProperties: false`** (`aws_s3_list.py:31-48`)
Extra fields are silently ignored. Consistent with other tools in the registry, but noting it for completeness.

**L5 — Description duplicates safety prose** (`aws_s3_list.py:9-28` + `prompt/security.md:13-15`)
The "WHEN to use / WHEN NOT to use" block plus the security.md addition are both visible to the model. Acceptable token cost (~300 chars), no real bloat, but watch for redundancy if more block-specific guidance accumulates.

---

## Architecture / Drift / Cache / Zip

- **Layout**: file-per-tool ADR-001 respected; module imported in `tools/__init__.py:47` and bootstrapped at `:99`. ✓
- **Plan-mode allowlist**: `aws_s3_list` correctly added to `PLAN_MODE_ALLOWED_TOOLS` (`registry.py:49`). ✓
- **Cache invariant**: New built-in slots into the alphabetical built-in prefix via `assemble_tool_pool()`; cache breakpoint shifts as expected for any new built-in — no interleaving risk. ✓
- **UI**: No `chat_ui.py` changes; tool renders through the generic tool-call path. ✓
- **Zip**: Assuming the flat-zip step globs `tools/*.py`, the new file is picked up automatically; no `__init__`-only manifest to update found. Worth a one-line check during Block 7 packaging.
- **Security manager ordering**: New S3-CLI block is placed *after* the Bedrock-only short-circuit (`manager.py:297-305`), so Bedrock-only users still get the Bedrock-only message rather than the S3 redirect. Correct precedence.

## Proof gate

5/5 tests PASS in `BLOCK_1_S3_SAFE_READ_tests.log`. Coverage is appropriate for local/mock scope:
- Behavior with `aws_bedrock_only=False` (bucket + prefix listing via fake client)
- Behavior with `aws_bedrock_only=True` (executor refuses)
- Registry shape (read-only, non-destructive, in plan-mode allowlist, no destructive verbs in schema text)
- Security manager redirect message contains `aws_s3_list` and omits Bedrock-only language

Real-AWS smoke deferral to Block 7 is the right call — not a blocker for this block.
