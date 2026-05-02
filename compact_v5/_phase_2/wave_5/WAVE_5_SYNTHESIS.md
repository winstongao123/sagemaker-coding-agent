# Wave 5 Synthesis — plan deltas before Block 0

**Date**: 2026-05-01
**Inputs**: Runnable scan (0 new), Hermes scan (0 new in-scope), LF scan (5 new; 4 adopt, 1 flagged DEFER), Plan v3 (~11,330 LOC, Codex APPROVE), Q1 matrix (172 rows).
**No-deferrals directive**: enforced — session-end cleanup resolved as DROP-WITH-CONSTRAINT (NOT v5.0.2 punt).

## Verdict

**APPROVE plan v4 with 3 additions** (CSO + task granularity = doc-only; skill-promotion = code in Block D + scaffold in Block K). Tool-failure detection REJECTED as redundant with v4's repetition detector. Session-end cleanup DROPPED-WITH-CONSTRAINT.

## Plan deltas to apply

### Add to Block K (process discipline; doc-only, +60 LOC)
- **CSO "Use when [symptoms]" convention** | LF `hooks/cso-check.sh:1-102` | +30 LOC docs (CLAUDE.md "Conventions" section) | Document in `compact_v5/MAIN/agent/CLAUDE.md` as authoring rule for new skill/agent/command descriptions; NOT enforced via PreToolUse hook (v5 is Python runtime, not Claude Code env). Reviewer-agent prompt template enforces at review time.
- **Task granularity guideline (>15 line atomic blocks)** | LF `hooks/task-granularity-check.sh:1-101` | +20 LOC docs (BUILD_GUIDE.md) | Same rationale: doc-only, enforced by humans/reviewers, not by hook. Already partially captured in CLAUDE.md global rules.
- **`state/skill-proposals/.gitkeep` scaffold + workflow doc** | LF `docs/SKILL_PROMOTION_PROTOCOL.md` | +10 LOC | Wires Block D `/promote-to-skill` output location.

### Add to Block D (slash commands; +200 LOC)
- **`/promote-to-skill <name>` command handler** | LF `commands/promote-to-skill.md` + hermes `D:/Github/hermes-agent/AGENTS.md:promote-to-skill` | +200 LOC at `compact_v5/MAIN/agent/sagemaker_agent.py` slash dispatch + `runtime/skill_proposals.py` (NEW) | Captures current task context (last-N tool calls + user goal) → writes `state/skill-proposals/<name>.md` proposal → user reviews → `/skill apply <name>` (existing Block D handler at v4 `:10892-10954`) promotes to `agent/skills/<name>/SKILL.md`. Distinct from `/skill apply` which APPLIES an existing proposal — `/promote-to-skill` CREATES the proposal from session learnings. No surface conflict.

### Add to Block C (NONE)
- **Tool-failure detection from LF hook**: REJECTED. v4 already implements equivalent at `compact_v4/MAIN/agent/sagemaker_agent.py:9145-9199` (doom-loop / repetition detector with per-tool dedup keys + threshold-2 for read_file / threshold-3 for others). v4's logic is tighter (Bedrock-runtime, not env hook) and is already verbatim-ported in Block C. Adding LF's hook would double-fire. Categorical drop.

### New PORT_LOG rows for Q1 matrix (Block K rows)
```
| 173 | LF | hooks/cso-check.sh:1-102 | PORTED-AS-DOC | Block K | CLAUDE.md Conventions section | doc-only |
| 174 | LF | hooks/task-granularity-check.sh:1-101 | PORTED-AS-DOC | Block K | BUILD_GUIDE.md granularity guideline | doc-only |
| 175 | LF | commands/promote-to-skill.md | PORTED | Block D | runtime/skill_proposals.py + sagemaker_agent.py slash dispatch | new command |
| 176 | LF | docs/SKILL_PROMOTION_PROTOCOL.md | PORTED-AS-DOC | Block K | state/skill-proposals/.gitkeep + workflow doc | scaffold |
| 177 | LF | hooks/tool-failure-detect.sh:1-137 | DROPPED-CATEGORICAL | n/a | redundant with v4 repetition detector :9145-9199 already in Block C | no code |
| 178 | LF | hooks/session-end.sh:1-63 | DROPPED-CATEGORICAL | n/a | covered by Block H (memory extraction) + Block B+ (SessionManager atomic save) | no code |
| 179 | Hermes | run_agent.py:389-720 surrogate sanitization | DROPPED-CATEGORICAL | n/a | Bedrock UTF-8 native; multi-provider concern | no code |
| 180 | Hermes | run_agent.py:547-643 JSON repair | DROPPED-CATEGORICAL | n/a | Claude tool_use structured outputs <1% malformed; Block I/N fuzzy match sufficient | no code |
```

(Note: PORT_LOG schema disallows DEFERRED rows post-no-deferrals; DROPPED-CATEGORICAL is the audit-trail row for items rejected with categorical justification, NOT a deferral.)

### LOC delta
- Block K: 200 → 260 (+60 docs)
- Block D: 700 → 900 (+200 code)
- Block C: 250 → 250 (no change; tool-failure rejected)
- **Plan total: ~11,330 → ~11,590 LOC** (+260 net)

## Architectural fit: clean | minor adjust | conflict

- **CSO convention**: clean — doc-only; LF hook bash-style is irrelevant to v5 Python runtime; convention enforced by review-time, not hook.
- **Task granularity**: clean — same reasoning; already partially in global CLAUDE.md.
- **Skill-promotion `/promote-to-skill`**: clean — orthogonal to Block D `/skill apply` (CREATE proposal vs APPLY proposal). New module `runtime/skill_proposals.py` writes to `state/skill-proposals/<name>.md`; existing `/skill apply <name>` reads from that location.
- **Tool-failure detection**: conflict — v4 repetition detector at `:9145-9199` already covers (with smarter per-tool keys); LF hook would double-fire and over-block.
- **Session-end cleanup**: conflict — v5 has explicit Save (Block B+ SessionManager atomic save) + Block H memory-extraction trigger at session end; LF hook duplicates with no added value.

## Session-end cleanup decision (no-deferrals enforcement)

**DROP-WITH-CONSTRAINT** (not deferral). Categorical reason: LF `hooks/session-end.sh:1-63` is a Claude-Code-env Stop hook that creates `~/.claude/sessions/<date>-session.tmp` markdown. v5 is a Python runtime inside SageMaker — the equivalent functionality is already in scope:
- **Atomic session save** at session boundary: Block B+ `SessionManager` (v4 `:2578` verbatim port) writes session JSON atomically.
- **Memory extraction at session end**: Block H `_extract_and_append_memories` (v4 `:7889-8028` + Runnable extractMemories/sessionMemory) writes to `memory.md`.
- **STATE.md push**: not applicable — v5 is not a multi-session-resume IDE harness; SageMaker session is the unit, no STATE.md doctrine.

PORT_LOG row 178 above documents this drop with line refs. No v5.0.2 punt.

## Hermes drops verified

- **Surrogate/non-ASCII sanitization** (`run_agent.py:389-720`, ~200 LOC): Bedrock InvokeModel API is UTF-8 native; v4 has zero observed surrogate issues across 92/92 tests + production runs. Multi-provider concern (DashScope, Ollama) does not apply to single-provider Bedrock. PORT_LOG row 179.
- **Enhanced JSON argument repair** (`run_agent.py:547-643`, ~170 LOC): Claude Opus/Sonnet via Bedrock tool_use returns structured `input` dict, NOT freeform JSON; <1% malformed rate observed; Block I/N fuzzy tool-name match (`:4689-4720`, 30 LOC) is sufficient. Adding 170 LOC defensive code for an unobserved failure mode violates "build only what proves useful." PORT_LOG row 180.

## Updates required to existing files

- **V5_PHASE_2_PLAN_v3.md**:
  - Block D (line 173 +): add `/promote-to-skill` command spec + `runtime/skill_proposals.py` target; bump LOC est 700 → 900.
  - Block K (line 384-394): add CSO + task-granularity doc requirements + `state/skill-proposals/` scaffold; bump LOC est 200 → 260.
  - Section 5 LOC summary (line 408+): D 700→900, K 200→260, TOTAL ~11,330 → ~11,590.
  - Section 7 Status: append "Wave 5 synthesis 2026-05-01: +3 LF adoptions (CSO doc, task-granularity doc, /promote-to-skill); 1 LF rejection (tool-failure-detect redundant with v4); 1 LF drop-with-constraint (session-end superseded by Block B+/H); 2 Hermes drops (surrogate, JSON repair)."
- **Q1_EVIDENCE_MATRIX.md**: append rows 173-180 per table above. Row count 172 → 180.
- **V5_BUILD_STATUS.md**: status line "Wave 5 synthesis complete 2026-05-01 — plan v4 = v3 + 3 adoptions + 4 documented drops; ready for Block 0 once user approves +260 LOC delta."

---

**Builder action**: apply deltas above to plan + matrix + status, then proceed to Block 0 (sagemaker_agent.py shim).
