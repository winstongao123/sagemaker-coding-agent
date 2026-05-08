# Block D Decisions

Primary ADR: `compact_v5/_status/V5_DESIGN_DECISIONS.md` ADR-052.

Decisions:

- Use Python `ThreadPoolExecutor` for parallel skill file parsing, then merge in
  deterministic source order.
- Treat `/quit` as canonical and `/q` as alias. Keep `/skill suggestion` as the
  existing v4 parity alias for `/skill suggestions`.
- Keep MCP execution disabled, but preserve `(MCP)` namespace parsing for
  custom command compatibility.
- Mark `init`, `init-verifiers`, and `skillify` bundled prompt skills as
  `disable_model_invocation: true`; these are user-invoked scaffolders.
- Keep `/dream` manual-only. Block D owns command dispatch; Block H+ owns the
  memory consolidation engine.
- Per `PS_SOFTWARE_PROJECT_WORKFLOW.md`, do not add `/project-*` commands.
  Long-running coding support should be hardened through the existing command
  surface (`/status`, `/save`, `/resume`, `/checkpoint`, `/verify`, `/done`,
  `/phase`, `/cost`, `/context`, `/dream`). Any additional workflow proof is a
  pre-AWS hardening item for R16/R19 rather than new Block D command scope.

No defer/drop decision was made for any D row.
