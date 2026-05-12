# UI Live Supervisor / S3 Real-Use / Notebook Ship Zip Verify - 2026-05-12

- source_tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- source_tree_meaning: complete v5 development/runtime source tree
- ship_zip_path: `D:\Github\sagemaker-coding-agent\compact_v5_ship.zip`
- ship_zip_meaning: minimum runtime artifact to upload/extract in SageMaker
- retired_ambiguous_name: `compact_v5.zip`
- zip_size_bytes: `498477`
- member_count: `152`
- zip_sha256: `4f740baa44183c131ae3b33da4ec1cdc877d882f7d026847ec283f83fd2023cc`
- testzip_result: `None`
- required_missing: `[]`
- forbidden_members: `[]`
- required_hash_parity_ok: `True`
- notebook_default_ui: `v4-style ipywidgets UI; explicit console fallback only`
- minimum_ship_excludes: `tests/`, `docs/htmls/`, `sessions/`, `audit_logs/`,
  `__pycache__/`, `.pytest_cache/`, `.ipynb_checkpoints/`, `_status/`,
  `_phase_2/`, `.git/`

## Required Member Hash Parity

| member | status | source_sha256 | zip_sha256 |
|---|---|---|---|
| `chat.ipynb` | `match` | `8beb98b801eafb6390662c5dd3e7f9a5c2f42ecaeed90ea06ad07b5736c31858` | `8beb98b801eafb6390662c5dd3e7f9a5c2f42ecaeed90ea06ad07b5736c31858` |
| `chat.md` | `match` | `c8c967714b753b9aefe93b87661cea296b9f4f9e74ac2d157675e531a2622808` | `c8c967714b753b9aefe93b87661cea296b9f4f9e74ac2d157675e531a2622808` |
| `entry.py` | `match` | `9fd29c53786e116b13e5766510fdf333ed8fc4398102edab690844bf63d7d4f9` | `9fd29c53786e116b13e5766510fdf333ed8fc4398102edab690844bf63d7d4f9` |
| `memory.md` | `match` | `5d4d679f169f0e5447a2de1fab7fbb7f171154aea4d7068191a4f824b5396d23` | `5d4d679f169f0e5447a2de1fab7fbb7f171154aea4d7068191a4f824b5396d23` |
| `ui/chat_ui.py` | `match` | `ca2d10eec79eea1f96ba01b089d5437b0a84de30e140a284a43e1bf5846e4626` | `ca2d10eec79eea1f96ba01b089d5437b0a84de30e140a284a43e1bf5846e4626` |
| `agent.py` | `match` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` |
| `core/query_engine.py` | `match` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` |
| `tools/task.py` | `match` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` |
| `runtime/config.py` | `match` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` |
| `sagemaker_agent.py` | `match` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` |
| `AGENT_STATUS.md` | `match` | `446f9e051e8dbfa4c78fa58cf2c658ecf7325468425bcc19e1451aac60994df7` | `446f9e051e8dbfa4c78fa58cf2c658ecf7325468425bcc19e1451aac60994df7` |
| `tools/aws_s3_list.py` | `match` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` |
| `security/diagnostics.py` | `match` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` |

## Exclude Policy

Excluded directories: `__pycache__`, `.pytest_cache`, `.ipynb_checkpoints`,
`tests`, `sessions`, `audit_logs`, `_status`, `_phase_2`,
`compact_v5_test_evidence`, `.git`.

Source-only HTML architecture/reference docs under `docs/htmls/` are kept in
`compact_v5/` but excluded from `compact_v5_ship.zip` to make the ship artifact
smaller and less ambiguous.
