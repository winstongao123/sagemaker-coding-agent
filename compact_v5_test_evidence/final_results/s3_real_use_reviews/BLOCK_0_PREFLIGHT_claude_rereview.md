# Block 0 Re-review

**Verdict: APPROVE_WITH_NITS**

## Findings

### MEDIUM — Mitigation #3 (zip baseline) partially failed
`compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_0_PREFLIGHT_status.md:18-19`

```
- zip path: $zip
- zip sha256: $zipHash
```

The PowerShell variables `$zip` and `$zipHash` were not interpolated and appear as literal strings in the file. Net effect:
- Zip path is recoverable from the `Get-ChildItem` block at line 22 (`D:\Github\sagemaker-coding-agent\compact_v5.zip`).
- **Zip sha256 is missing entirely.** Without it, the stated tamper-detection baseline for the zip artifact does not exist.

Recommend re-running the hash step (e.g. `Get-FileHash compact_v5.zip -Algorithm SHA256`) and pasting the literal hash before Block 1 evidence is collected, so later blocks can be checked against an actual baseline.

### NIT — Mitigation #1 is a forward-promise, not Block 0 evidence
`BLOCK_0_PREFLIGHT_status.md:14`

The S3-evidence guarantee is deferred to Block 1 ("Block 1 proof will include direct safe-tool tests and an explicit S3-inventory prompt/tool path"). Acceptable as a process control, but Block 1 review must enforce it — otherwise the drift risk reopens silently.

## Clean
- Source hash/mtime baseline (mitigation #4): 7 files, real sha256 values, real mtimes — valid baseline.
- Mitigation #2 (Block 6 split) and #5 (git-noise annotation): both adequately stated.
- Branch state matches `gitStatus` snapshot; no unexpected source-tree drift.

Proceed to Block 1 after fixing the zip sha256.
