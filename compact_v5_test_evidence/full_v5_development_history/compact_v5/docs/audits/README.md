# Audit Directory Shape

Every new audit directory should use this shape:

```text
<date>-<topic>/
  00-SYNTHESIS.md
  01-<source-or-critic>_1.md
  02-<source-or-critic>_2.md
  ...
```

Rules:

- `00-SYNTHESIS.md` is the canonical entrypoint for the directory.
- Numbered source files keep deterministic reading order.
- The synthesis file must name the canonical scope file when the synthesis is
  a pointer rather than the full text.
- Existing Wave-5-DEEP source filenames are not renamed during the v5 redo
  because `SYNTHESIS_MASTER.md:709-710` marks that retrofit as optional polish,
  not a blocker.

