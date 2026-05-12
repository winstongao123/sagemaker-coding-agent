# UI Live Supervisor / S3 Real-Use / Notebook Zip Verify - 2026-05-12

- zip_path: `D:\Github\sagemaker-coding-agent\compact_v5.zip`
- source_tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- zip_size_bytes: `653965`
- member_count: `158`
- zip_sha256: `af11f4760e7855adc765f7a8f28c9fd017e14569c421567538825a3ce20380c4`
- testzip_result: `None`
- required_missing: `[]`
- forbidden_members: `[]`
- required_hash_parity_ok: `True`
- notebook_default_ui: `v4-style ipywidgets UI; explicit console fallback only`

## Required Member Hash Parity

| member | status | source_sha256 | zip_sha256 |
|---|---|---|---|
| `chat.ipynb` | `match` | `652112457f5020af4cf4773c193010f0836f9a92b4d82aec9268cbeb078265f1` | `652112457f5020af4cf4773c193010f0836f9a92b4d82aec9268cbeb078265f1` |
| `chat.md` | `match` | `e5e691dd62df1bf8f8a2979fd632430eec6b6c837bd78a714d7d7858ac0b0486` | `e5e691dd62df1bf8f8a2979fd632430eec6b6c837bd78a714d7d7858ac0b0486` |
| `entry.py` | `match` | `9fd29c53786e116b13e5766510fdf333ed8fc4398102edab690844bf63d7d4f9` | `9fd29c53786e116b13e5766510fdf333ed8fc4398102edab690844bf63d7d4f9` |
| `ui/chat_ui.py` | `match` | `ca2d10eec79eea1f96ba01b089d5437b0a84de30e140a284a43e1bf5846e4626` | `ca2d10eec79eea1f96ba01b089d5437b0a84de30e140a284a43e1bf5846e4626` |
| `agent.py` | `match` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` |
| `core/query_engine.py` | `match` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` |
| `tools/task.py` | `match` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` |
| `runtime/config.py` | `match` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` |
| `sagemaker_agent.py` | `match` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` |
| `AGENT_STATUS.md` | `match` | `619beb25b77da0125672fcceaaf0ebcdee58854a36951922e6f743bc55627953` | `619beb25b77da0125672fcceaaf0ebcdee58854a36951922e6f743bc55627953` |
| `tools/aws_s3_list.py` | `match` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` |
| `security/diagnostics.py` | `match` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` |

## Exclude Policy

Excluded directories: `__pycache__`, `.pytest_cache`, `.ipynb_checkpoints`,
`tests`, `sessions`, `audit_logs`, `_status`, `compact_v5_test_evidence`,
`.git`.
