# Block B+ Decisions

Date: 2026-05-05

Primary design record:

- `compact_v5/_status/V5_DESIGN_DECISIONS.md` ADR-051

Decision summary:

- Implement B+3, B+4, and B+6 directly in B+ instead of leaving them as
  future Block I remaps, because v5.0.1 close policy requires every B+ row to
  have concrete code/test/PORT_LOG/ADR evidence before B+ can close.
- Keep B+5 in `core/compactor.py`, where the auxiliary advisor model is
  actually invoked. The row is still ledgered under B+ and validated with the
  targeted Block A advisor tests.
- Keep local OTel-style counters as in-process dictionaries only. No external
  export path, network sink, AWS call, or telemetry endpoint was introduced.
