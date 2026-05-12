# UI Live Supervisor / S3 Real-Use / Notebook Ship Zip Verify - 2026-05-12

- source_tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- source_tree_meaning: complete v5 development/runtime source tree
- ship_zip_path: `D:\Github\sagemaker-coding-agent\compact_v5_ship.zip`
- ship_zip_meaning: minimum runtime artifact to upload/extract in SageMaker
- retired_ambiguous_name: `compact_v5.zip`
- zip_size_bytes: `499584`
- member_count: `152`
- zip_sha256: `51002673cb6689113f356519d12312e964f07afb7c4dbee03ad0b04268554ad4`
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
| `chat.ipynb` | `match` | `812d329c53827aa4fd2684a552960a73b5c382caee0ccf3ce0d7f8ab06e8921f` | `812d329c53827aa4fd2684a552960a73b5c382caee0ccf3ce0d7f8ab06e8921f` |
| `chat.md` | `match` | `c14acb4221daaf71251d4068088beb51ba5eddcd2b427295e3784efa44ecfd97` | `c14acb4221daaf71251d4068088beb51ba5eddcd2b427295e3784efa44ecfd97` |
| `entry.py` | `match` | `58e4738aaf792cd6ab257606a0e88dea693ae682a68c5e7e16248cc3caaee189` | `58e4738aaf792cd6ab257606a0e88dea693ae682a68c5e7e16248cc3caaee189` |
| `memory.md` | `match` | `e49a2229501ad2372e065e49971de8292706502c9883a20c733901771b11ffd4` | `e49a2229501ad2372e065e49971de8292706502c9883a20c733901771b11ffd4` |
| `ui/chat_ui.py` | `match` | `7f058e82de4be885653f5670e3145e0ab2b148b48c5525fd4b37cdbbc6fbc4b5` | `7f058e82de4be885653f5670e3145e0ab2b148b48c5525fd4b37cdbbc6fbc4b5` |
| `agent.py` | `match` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` | `7bb7218bdeb2e8022fb495c404ac9ede788aef024fef7874736764ae650504f1` |
| `core/query_engine.py` | `match` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` | `fd14f0e69689607e9811308871621ad90e917ec31a945b7427233a91ce50b7e5` |
| `tools/task.py` | `match` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` |
| `runtime/config.py` | `match` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` |
| `sagemaker_agent.py` | `match` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` |
| `AGENT_STATUS.md` | `match` | `dd82123614995e545e72320892fa83283e94994c614e938c2bf8f3d955a94b0e` | `dd82123614995e545e72320892fa83283e94994c614e938c2bf8f3d955a94b0e` |
| `tools/aws_s3_list.py` | `match` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` |
| `security/diagnostics.py` | `match` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` |

## Exclude Policy

Excluded directories: `__pycache__`, `.pytest_cache`, `.ipynb_checkpoints`,
`tests`, `sessions`, `audit_logs`, `_status`, `_phase_2`,
`compact_v5_test_evidence`, `.git`.

Source-only HTML architecture/reference docs under `docs/htmls/` are kept in
`compact_v5/` but excluded from `compact_v5_ship.zip` to make the ship artifact
smaller and less ambiguous.
