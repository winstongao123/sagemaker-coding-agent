# Block H Decisions

Date: 2026-05-05

## Completion-Audit Deferral Supersession

Historical PORT_LOG #098 and ADR-034 recorded H-13/H-15/H-16/H-17 and
H-18/H-19/H-20 as explicit deferrals. The completion audit treats canonical
scope from `SYNTHESIS_MASTER.md` as authoritative, so Block H now ships those
rows directly instead of preserving the historical deferral.

## Adaptations

- H-13 replaces Runnable GrowthBook configuration with local `agent_config.json`
  / `agent_config.jsonc` defaults, matching v5's config-file architecture.
- H-18 loads CLAUDE.md hierarchy by default. AGENTS.md remains Codex-facing repo
  control and is not silently bundled into runtime model prompts.
- H-19 uses `git --no-optional-locks status --short`, memoizes per workspace,
  caps output at 2K chars, and degrades to no block outside git workspaces.
- H-20 is a small persisted onboarding state model. It does not add a new slash
  command or a parallel project workflow surface.

## AWS Boundary

No AWS/R-tier spend was run. The software-builder suite result is local
zero-cost readiness evidence only.
