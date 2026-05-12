# UI Live Supervisor / S3 Real-Use / Notebook Zip Verify - 2026-05-12

- zip_path: `D:\Github\sagemaker-coding-agent\compact_v5.zip`
- source_tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- zip_size_bytes: `653581`
- member_count: `158`
- zip_sha256: `5458e663e4d5f00362e306195b3ae8250963717b1f400a898509f24fe1a88032`
- testzip_result: `None`
- required_missing: `[]`
- forbidden_members: `[]`
- required_hash_parity_ok: `True`
- notebook_default_ui: `ConsoleChatUI / non-widget fallback`

## Required Member Hash Parity

| member | status | source_sha256 | zip_sha256 |
|---|---|---|---|
| `chat.ipynb` | `match` | `f831b11dc600e2b3e7705b320a3603496b25105c2a519174880c57b1eef0e489` | `f831b11dc600e2b3e7705b320a3603496b25105c2a519174880c57b1eef0e489` |
| `chat.md` | `match` | `5f662df0160987d579eda3bbdbb8a5997f4ff208beb7506f3a89894816f28c55` | `5f662df0160987d579eda3bbdbb8a5997f4ff208beb7506f3a89894816f28c55` |
| `entry.py` | `match` | `28e72ca4315e0af4fb816a317ee6af9f311cc562db8ec1cc221c52fd38669cd9` | `28e72ca4315e0af4fb816a317ee6af9f311cc562db8ec1cc221c52fd38669cd9` |
| `ui/chat_ui.py` | `match` | `ca2d10eec79eea1f96ba01b089d5437b0a84de30e140a284a43e1bf5846e4626` | `ca2d10eec79eea1f96ba01b089d5437b0a84de30e140a284a43e1bf5846e4626` |
| `agent.py` | `match` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` |
| `core/query_engine.py` | `match` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` |
| `tools/task.py` | `match` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` |
| `runtime/config.py` | `match` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` |
| `sagemaker_agent.py` | `match` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` |
| `AGENT_STATUS.md` | `match` | `4220ac72ef764f7ca3c7c1c8dac715cd6cbf0a309e7349d4ae481e3b6fa08ccf` | `4220ac72ef764f7ca3c7c1c8dac715cd6cbf0a309e7349d4ae481e3b6fa08ccf` |
| `tools/aws_s3_list.py` | `match` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` |
| `security/diagnostics.py` | `match` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` |

## Exclude Policy

Excluded directories: `__pycache__`, `.pytest_cache`, `tests`, `_status`, `compact_v5_test_evidence`, `.git`.
