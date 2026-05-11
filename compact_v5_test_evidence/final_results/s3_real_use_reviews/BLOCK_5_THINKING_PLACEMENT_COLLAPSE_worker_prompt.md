# BLOCK_5_THINKING_PLACEMENT_COLLAPSE Worker Prompt

Mission block: Thinking placement/collapse.

Scope:
- Keep fixes in flattened compact_v5/ runtime tree.
- Make thinking blocks visible as observability but collapsed by default.
- Place per-turn thinking before the metrics line so expanded reasoning does not appear after/inside the footer metrics.
- Preserve thinking signatures and runtime message semantics; UI-only rendering change.

Implementation summary:
- Removed open attribute from standalone thinking details cards.
- Moved turn-level thinking details before the sageagent-turn-metrics div.
- Added a zero-cost UI smoke test proving collapsed thinking and placement before metrics.
