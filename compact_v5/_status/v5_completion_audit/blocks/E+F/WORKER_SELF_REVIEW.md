# Block E+F Worker Self-Review

Date: 2026-05-04

Scope reconstructed from `SYNTHESIS_MASTER.md:199-206` produced eight EF rows.
The implementation closes six local runtime/helper rows and records EF-6/EF-7
as hard no-streaming constraints.

Checks performed:

- EF-1 denial warning is produced only after three denials in one model turn.
- EF-2 hard cap returns before calling Bedrock and does not reuse
  `session_cost_limit`.
- EF-3 fallback retry strips signature variants before replay.
- EF-4 helpers are centralized and exported.
- EF-5 callback fires for visible tool calls before dispatch in the synchronous
  response path.
- EF-8 status/warning callbacks are best-effort and do not replace `output_fn`.

Residual risks:

- Claude must verify that `N/A_CONSTRAINT` is acceptable for EF-6 and EF-7 under
  the active no-streaming rule.
- Claude iter1 noted a `scope_audit.py` N/A count display bug. That tool is
  shared completion-audit infrastructure outside Block E+F ownership; the row
  table and ship-blocking verdict remain correct, and the issue should be
  tracked separately rather than folded into this block's runtime changes.
