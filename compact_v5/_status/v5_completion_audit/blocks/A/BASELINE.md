# Block A Baseline

Date: 2026-05-04
Worker: Codex GPT-5.5
Mode: ledger-only audit before implementation

## Commands

### git status --short

```text
 m _archive/compare_code/gg-claude-code-runnable
 M compact_v5.zip
 M compact_v5/_phase_2/wave_6/BUILDER_PROMPT.md
 M compact_v5/_status/PS_CRITICAL_WORKER_PROBLEM.md
 M compact_v5/_status/RESUME.md
 M compact_v5/_status/R_TIER_GATE_STATUS.md
 M compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md
 M compact_v5/docs/PS_V5_TEST_PLAYBOOK.md
 M compact_v5/docs/PS_V5_TEST_WORKER_FINAL.md
?? compact_v5/_status/v5_completion_audit/
```

### git rev-parse HEAD

```text
c256d07a099e7bc9bbf1bd9cd5ff437186fd2adb
```

### git tag --list "v5.0.1-block*" --sort=creatordate

```text
v5.0.1-block-0
v5.0.1-block-b
v5.0.1-block-b-plus
v5.0.1-block-c
v5.0.1-block-c-plus
v5.0.1-block-d
v5.0.1-block-a
v5.0.1-block-e-f
v5.0.1-block-f2
v5.0.1-block-i
v5.0.1-block-m
v5.0.1-block-g
v5.0.1-block-g3
v5.0.1-block-g2
v5.0.1-block-h
v5.0.1-block-h-plus
v5.0.1-block-l
v5.0.1-block-n
v5.0.1-block-t
v5.0.1-block-j
v5.0.1-block-k
```

### py -3.11 compact_v5\_status\scripts\r_tier_gate.py --repo-root .

Exit code: 1

```text
R-tier gate FAILED:
  - missing executable marker for R4
  - missing executable marker for R6
  - missing executable marker for R7
  - missing executable marker for R8
  - missing executable marker for R9
  - missing executable marker for R10
  - missing executable marker for R11
  - missing executable marker for R12
  - missing executable marker for R13
  - missing executable marker for R14
  - missing executable marker for R15
  - missing executable marker for R16
  - missing executable marker for R18-E1
  - missing executable marker for R18-E2
  - missing executable marker for R18-E3
  - missing executable marker for R18-E4
  - missing executable marker for R18-E5
  - missing executable marker for R18-E6
  - missing executable marker for R18-E7
  - missing executable marker for R18-E8
  - missing executable marker for R18-E9
  - missing executable marker for R18-E10
  - missing executable marker for R18-E11
  - missing executable marker for R18-E12
  - missing executable marker for R18-E13
  - missing executable marker for R18-E14
  - missing executable marker for R18-E15
  - missing executable marker for R19-U1
  - missing executable marker for R19-U2
  - missing executable marker for R19-U3
  - missing executable marker for R19-U4
  - missing executable marker for R19-U5
  - missing executable marker for R19-U6
  - missing executable marker for R19-U7
  - missing executable marker for R19-U8
  - missing executable marker for R19-U9
  - missing executable marker for R19-U10
```

### py -3.11 -m pytest tests\integration\test_block_a.py -q

Working directory: `compact_v5/MAIN/agent`

Exit code: 0

```text
.........................                                                [100%]
25 passed in 0.59s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

## Baseline Conclusion

Block A's narrow existing local tests pass. The executable R-tier gate fails, including R4, so no AWS/R-tier spending should resume.
