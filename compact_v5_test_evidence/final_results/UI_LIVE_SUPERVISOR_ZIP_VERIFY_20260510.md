# UI Live Supervisor Zip Verify 20260510

Date verified: `2026-05-11`

Zip path: `D:/Github/sagemaker-coding-agent/compact_v5.zip`

Zip size bytes: `639054`

Member count: `155`

testzip result: `None`

Missing required members: `[]`

Forbidden-member violation count: `0`

Required-member hash mismatches: `[]`

Required member check:

- `chat.ipynb`: present; sha256 parity `True`; live `a486e8b522ce` zip `a486e8b522ce`
- `chat.md`: present; sha256 parity `True`; live `fa1a4d10f980` zip `fa1a4d10f980`
- `ui/chat_ui.py`: present; sha256 parity `True`; live `cefccb58486c` zip `cefccb58486c`
- `agent.py`: present; sha256 parity `True`; live `4e08d4b84228` zip `4e08d4b84228`
- `core/query_engine.py`: present; sha256 parity `True`; live `3fe9be955ea2` zip `3fe9be955ea2`
- `tools/task.py`: present; sha256 parity `True`; live `93fee00f4881` zip `93fee00f4881`
- `runtime/config.py`: present; sha256 parity `True`; live `1fe1b2f96446` zip `1fe1b2f96446`
- `sagemaker_agent.py`: present; sha256 parity `True`; live `eb20e51869fe` zip `eb20e51869fe`
- `AGENT_STATUS.md`: present; sha256 parity `True`; live `22d1916bd3da` zip `22d1916bd3da`

Excluded by policy: `__pycache__`, `.pytest_cache`, `tests`, `_status`, `compact_v5_test_evidence`, `.git`.

Additional smoke: extracted zip to a temporary directory and `import entry` passed.

Post-zip Claude re-review returned `SHIP DECISION: APPROVE` with no findings.
