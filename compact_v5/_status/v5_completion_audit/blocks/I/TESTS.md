# Block I Tests

Status: PASS
Date: 2026-05-05

Initial local validation already run during implementation:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_i.py -q
```

Result: `23 passed, 1 skipped`.

Close validation:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_i.py compact_v5/MAIN/agent/tests/integration/test_block_d.py compact_v5/MAIN/agent/tests/integration/test_skills.py -q
py -3.11 -m py_compile compact_v5/MAIN/agent/skills/manager.py compact_v5/MAIN/agent/tools/edit_file.py compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/tools/skill.py compact_v5/MAIN/agent/tools/skill_propose_patch.py compact_v5/MAIN/agent/tests/integration/test_block_i.py
py -3.11 compact_v5/_status/scripts/scope_audit.py --block I
```

Results:

- Combined Block I/D/skills tests: `66 passed, 1 skipped`.
- py_compile: `PASS`.
- Scope audit: `READY_TO_REVIEW_CLOSE`, 13 shipped, 0 ship-blocking rows.
- Claude iter1 independently reran the combined Block I/D/skills suite: `66 passed, 1 skipped`.
- Claude iter1 independently reran `scope_audit.py --block I`: `READY_TO_REVIEW_CLOSE`, 13 shipped, 0 ship-blocking rows.

Logs:

- `compact_v5/_status/v5_completion_audit/logs/block-i-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/block-i-py-compile.log`
- `compact_v5/_status/v5_completion_audit/logs/block-i-scope-audit.log`

Coverage target:

- I-1/I-5 path-frontmatter activation and edit hook.
- I-2 model/user skill visibility split.
- I-3 config-gated skill loading.
- I-4 realpath dedup.
- I-6 safe variable substitution.
- I-7/I-8/I-9 folded scaffold prompt skills.
- I-10/I-11 bundled debug/remember skills.
- I-12 parser drift locks.
- I-13 skill tool registry and model-facing restrictions.
