# PS_PS_PS Check v5 vs v4

Date: 2026-05-10

## Why This Check Exists

The live SageMaker run showed that v5 was not yet clear enough for an operator:

- A user asked to inspect S3 buckets while `CONFIG.aws_bedrock_only=True`.
- v5 correctly blocked S3, but the main chat UI did not make that mode obvious enough.
- Assistant markdown was displayed too literally in places, unlike v4's readable markdown renderer.
- Cache/cost metrics existed, but the words were too compact to make prompt caching obvious.
- Thinking was enabled for a simple S3 question, which made the turn more expensive than needed.

Explain it like you are 9: v5 had the right lock on the AWS door, but the sign on the door was too small. It also wrote some answers like raw notebook text instead of making them look nice.

## Findings

| Finding | v4 behavior | v5 issue | Fix |
|---|---|---|---|
| Bedrock-only mode was hidden in the main UI | v4 had a visible setup toggle and banner | v5 relied too much on notebook setup text; the chat footer did not say why S3 was blocked | Added a live `Bedrock-only` checkbox and an AWS scope footer line |
| S3 read vs delete distinction was not obvious | v4 security manager allowed read-only S3 only outside Bedrock-only mode and blocked delete/admin | v5 security matched this, but the UI wording made the user think S3 should always work | UI now says either `Bedrock-only; S3/Textract/Lambda blocked` or `S3 list/get allowed with approval; delete/admin blocked` |
| Markdown readability regressed | v4 rendered safe markdown: bullets, numbered lists, code fences, tables, inline code/bold | v5 escaped assistant text in the chat body | Ported the v4 safe markdown renderer into `ui/chat_ui.py` |
| Cache display was too terse | v4 emphasized cost/status in the footer | v5 showed `Cache R/W`, but the user wanted prompt caching called out directly | Footer and per-turn metrics now say `Prompt Cache R/W` and `Cache saved` |
| Thinking cost visibility needed clearer guidance | v4 thinking was less central | v5 can show thinking, but using it on simple operational questions is expensive | Footer already shows thinking state; docs now call out: use Thinking OFF for simple AWS/listing tasks, ON for hard coding/reasoning |

## Zero-Cost Checks Run

These checks do not call AWS:

```text
py -3.11 compact_v5/docs/checks/ps_ps_ps_v5_vs_v4_zero_cost_check.py

ui_zero_cost_smoke=PASS
security_zero_cost_smoke=PASS
PS_PS_PS_Check_v5_vs_v4 zero-cost UI/security lock: PASS
```

Rendered evidence:

- `compact_v5_test_evidence/final_results/PS_PS_PS_Check_v5_vs_v4_rendered_sample.html`
- `compact_v5_test_evidence/final_results/PS_PS_PS_Check_v5_vs_v4_rendered_sample.png`

What they verify:

- v5 can instantiate the production chat UI in mock mode.
- The UI has a live `Bedrock-only` checkbox.
- Bedrock-only mode visibly says S3/Textract/Lambda are blocked.
- Turning Bedrock-only off visibly says S3 list/get is allowed with approval and delete/admin is blocked.
- Assistant markdown renders as HTML for bold text, code blocks, bullets, and tables.
- The security manager blocks S3 under Bedrock-only.
- The security manager allows Bedrock runtime under Bedrock-only.
- The security manager blocks S3 delete even when Bedrock-only is off.
- The markdown renderer escapes raw HTML such as `<script>`.

## Why Earlier Tests Missed This

Earlier tests proved the engine, R-tier gates, and many UI elements existed. They did not put the user in this exact live operator situation:

1. Ask for S3 while Bedrock-only mode is on.
2. Read the assistant answer as rendered notebook HTML.
3. Judge whether cache/thinking/AWS-scope information is obvious enough without reading source code.

This check adds that missing operator-facing layer.

## Production Decision

This was a real usability gap, not a core engine failure. The fix is architectural fit:

- keep v5's stricter Bedrock-only mode;
- keep v4's S3 read / no-delete guardrail when Bedrock-only is off;
- make the selected mode visible in the chat UI;
- restore v4-style markdown readability;
- keep cache/reasoning metrics visible inline.
