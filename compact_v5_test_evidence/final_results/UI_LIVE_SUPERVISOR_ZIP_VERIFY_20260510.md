# UI Live Supervisor / S3 Real-Use Zip Verify - 2026-05-11

- zip_path: `D:\Github\sagemaker-coding-agent\compact_v5.zip`
- source_tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- zip_size_bytes: `651929`
- member_count: `158`
- zip_sha256: `9a79daedb7e8d5f43660e6bc9e51009bf6bcf88b9870c22c4e02ecd55a37528f`
- testzip_result: `None`
- required_missing: `[]`
- forbidden_members: `[]`
- required_hash_parity_ok: `True`

## Required Member Hash Parity

| member | status | source_sha256 | zip_sha256 |
|---|---|---|---|
| `chat.ipynb` | `match` | `a486e8b522cea88e222774df35eb27ceb3ab13a3d04441bfc6c883380e6d1854` | `a486e8b522cea88e222774df35eb27ceb3ab13a3d04441bfc6c883380e6d1854` |
| `chat.md` | `match` | `b20f1edaeaae0c4b3fd833924a2a60129db8aabbf4eeb438b81b44c0527ad604` | `b20f1edaeaae0c4b3fd833924a2a60129db8aabbf4eeb438b81b44c0527ad604` |
| `ui/chat_ui.py` | `match` | `ccbe72966858d47df1f42ef812c91d29afdffc1e511fd0cd9da599aa084467f4` | `ccbe72966858d47df1f42ef812c91d29afdffc1e511fd0cd9da599aa084467f4` |
| `agent.py` | `match` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` |
| `core/query_engine.py` | `match` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` |
| `tools/task.py` | `match` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` |
| `runtime/config.py` | `match` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` |
| `sagemaker_agent.py` | `match` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` |
| `AGENT_STATUS.md` | `match` | `6a8b97e0590790ad8a539e18536812177129b5440f7130ef240ce7dc4ffa07da` | `6a8b97e0590790ad8a539e18536812177129b5440f7130ef240ce7dc4ffa07da` |
| `tools/aws_s3_list.py` | `match` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` |
| `security/diagnostics.py` | `match` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` |

## Exclude Policy

Excluded directories: `__pycache__`, `.pytest_cache`, `tests`, `_status`, `compact_v5_test_evidence`, `.git`.
