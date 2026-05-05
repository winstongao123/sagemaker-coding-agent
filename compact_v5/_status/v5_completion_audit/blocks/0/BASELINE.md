# Block 0 Baseline

Date: 2026-05-05

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:32-49`

Block 0 has 10 canonical rows. `SYNTHESIS_MASTER.md:34` states the build-time
remap rule: only 0-1 lands directly in Block 0, while 0-2 through 0-10 keep
their Block 0 PORT_LOG origin and are implemented in the owning blocks for the
touched modules.

Current audit task:

- ledger every canonical Block 0 row;
- cite the owning block evidence without reopening completed blocks;
- run local zero-cost remap tests;
- ask Claude to independently verify every row and the remap policy.
