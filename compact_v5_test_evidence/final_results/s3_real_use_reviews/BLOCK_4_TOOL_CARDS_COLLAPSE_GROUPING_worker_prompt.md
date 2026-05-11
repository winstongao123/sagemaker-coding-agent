# BLOCK_4_TOOL_CARDS_COLLAPSE_GROUPING Worker Prompt

Mission block: Tool cards collapse/grouping.

Scope:
- Keep fixes in flattened compact_v5/ runtime tree.
- Make tool cards v4-style collapsed by default.
- Group tool call and result for the same tool_use_id into one visible card.
- Preserve tool_gen_callback event path and avoid engine changes.

Implementation summary:
- Added UI-side tool card index keyed by tool_use_id.
- Rendered tool cards as collapsed <details> cards with separate Tool input and Tool result sections.
- Updated tool_gen_callback handler to append on tool_generation and update the same card on tool_result.
- Added a zero-cost UI smoke check proving collapsed HTML and grouped call/result behavior.
