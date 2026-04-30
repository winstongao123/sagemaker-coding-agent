# Data validation — CSV / Excel / dataframes

Reading/validating: row counts match expectations, column types correct, null/NaN handling explicit, no unexpected duplicates.

Merging/joining: join key unique (or explain duplicates), output row count makes sense (inner ≤ min, outer ≥ max), no Cartesian products.

Inflated row counts → flag it. Don't say "OK" without justification. Cross-validate: compare source vs output, check totals, verify samples.
