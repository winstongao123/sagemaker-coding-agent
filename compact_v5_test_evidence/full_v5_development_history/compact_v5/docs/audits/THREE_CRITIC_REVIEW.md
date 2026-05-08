# Three-Critic Review

Block K adopts the Learning Factory three-critic pattern as a process gate for
future block work. These are three separate critic prompts per block, not a
replacement for the required Claude canonical-scope review.

## AXIS A - Value

Ask whether the change delivers user-visible or reliability value that justifies
its complexity. Reject work that only increases parity theater without useful
behavior, safety, or evidence.

## AXIS B - Timing

Ask whether the work belongs in the current block and redo phase. Reject work
that should be moved to an explicitly named owning block, or that needs AWS/R-tier
approval before it can be validated.

## AXIS C - Cost

Ask whether the token, runtime, maintenance, and reviewer cost is justified.
Reject process or code that adds recurring cost without durable evidence value.

## Required Use

Before a block is sent for independent Claude close review, the worker records
how AXIS A, AXIS B, and AXIS C were considered in that block's self-review or
decisions artifact. Claude still reconstructs canonical scope from
`SYNTHESIS_MASTER.md` before using any worker-provided critic summary.

