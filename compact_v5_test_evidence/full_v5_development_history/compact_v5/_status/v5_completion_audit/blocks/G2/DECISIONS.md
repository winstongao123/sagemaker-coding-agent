# Block G2 Decisions

## D-G2-1: Ship helper-level cache-prefix replay locally

Decision: Block G2 ships the fork cache-prefix helper module and deterministic
lock tests locally. It does not perform real Bedrock cache-hit verification.

Rationale:

- ADR-033 records the v5 adaptation: synchronous helper functions preserve the
  byte-identical message prefix across fork children.
- The real cache-hit proof requires Bedrock usage and remains behind R-tier R3
  with explicit user approval.
- This matches the no-AWS rule for completion-audit block closure.

## D-G2-2: Runtime fork orchestration remains evidence-gated

Decision: Do not expand Block G2 into new runtime orchestration beyond the
existing helper evidence unless Claude or strict audit identifies a concrete
ship-blocking gap.

Rationale:

- Block G closed G-8 with Claude approval and accepted the helper-level evidence
  for the canonical row.
- SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN says completed blocks should be reopened
  only on concrete evidence. The runtime cache-prefix exercise belongs to final
  pre-AWS hardening/R-tier R3.
