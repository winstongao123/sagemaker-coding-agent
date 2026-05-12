I verified the final state by reading `entry.py:228-271` (the new `_apply_control_overrides` + `_option_label`), reading the new test `test_notebook_thin_launcher.py:136-145`, inspecting `chat.ipynb` cells 2/3 (16 + 4 lines, well under the 20/10 caps), and running a live smoke probe of the helper against the documented edge cases:

```
temperature=0.6, budget=5000 → defaults preserved (0.0/4096)  ✓ ignored
temperature=0.3, budget=8192 → 0.3/8192 labels                ✓ exact map
temperature='garbage'        → previous label preserved        ✓ ignored
temperature=None             → skipped via existing None guard ✓
```

`py_compile compact_v5/entry.py` passes. pytest isn't installed in this shell, but the helper's contract is verified directly.

## VERDICT: APPROVE

### HIGH / MEDIUM findings
None.

### Remaining LOW notes
- **`entry.py:245-255` — silent-ignore is now the documented contract** (and the new test pins it). That's fine and consistent with v4 muscle-memory, but a user passing `temperature=0.6` thinking it's valid will see no feedback and silently get `0.0`. Optional, non-blocking: emit a one-line `warnings.warn(...)` when `_option_label` returns `None`, so misconfigured kwargs surface in the notebook output. Not required for ship.
- **`entry.py:253` — float round-trip equality** is safe for the current option values (all are exact binary fractions or integers passed through `float()`/`int()` on both sides), so this isn't a defect today. If someone later adds a non-exact option like `0.1`, the `==` compare on `float()` would still work because both sides go through the same cast — keep that pattern.

Net: the prior LOW (invalid numeric overrides → `KeyError` in `_apply_notebook_config`) is fully resolved by routing temperature/thinking_budget through `_option_label`, and the regression test locks it. Cells 2/3 remain thin; banned-subsystem guard untouched. Ship.

