# Verification contract

Non-trivial = 3+ file edits changing logic / API / data flow (not renames/formatting).

When that bar is hit, independent adversarial verification SHOULD precede reporting completion.

- Default (`enforce_verify_contract=False`): SUGGEST `/verify` — don't auto-spawn. "Edited N files. Want /verify before declaring done?"
- Strict (`enforce_verify_contract=True`): auto-spawn `verify` sub-agent.

Verify agent runs builds, tests, linters, adversarial probes.

- FAIL → fix and re-verify.
- PASS → report completion.
- PARTIAL → report what was verified vs not.

Skip for: docs-only, config tweaks, single-file fixes, exploration.
