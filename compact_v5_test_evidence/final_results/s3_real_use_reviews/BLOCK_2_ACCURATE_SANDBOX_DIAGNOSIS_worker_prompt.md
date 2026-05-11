# BLOCK_2_ACCURATE_SANDBOX_DIAGNOSIS Worker Prompt

Mission block: Accurate sandbox diagnosis.

Scope:
- Keep fixes in flattened compact_v5/ runtime tree.
- Do not rewrite v5 engine.
- Make sandbox/allowlist failures identify the actual enforcement layer.
- Do not misdiagnose Python sandbox import failures or bash allowlist blocks as Bedrock-only when Bedrock-only is off.
- Preserve S3 safe-read work from Block 1.

Implementation summary:
- Added security diagnostics helpers for python_exec static and runtime import allowlist failures.
- Wired python_exec to append [diagnosis] for static validation and runtime import-hook failures.
- Updated prompt/security.md to require actual enforcement-layer wording.
- Added zero-cost smoke checks for bash S3 allowlist wording and python_exec import allowlist wording.
