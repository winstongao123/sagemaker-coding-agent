# UI Live Supervisor / S3 Real-Use / Notebook / ask_user Ship Zip Verify - 2026-05-12

- source_tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- source_tree_meaning: complete v5 development/runtime source tree
- ship_zip_path: `D:\Github\sagemaker-coding-agent\compact_v5_ship.zip`
- ship_zip_meaning: minimum runtime artifact to upload/extract in SageMaker
- retired_ambiguous_name: `compact_v5.zip`
- zip_size_bytes: `501656`
- member_count: `152`
- zip_sha256: `58d39db60eb9fe9d14be66b774de0a664dbccbd9863d0cb1a0e931965137983d`
- testzip_result: `None`
- required_missing: `[]`
- forbidden_members: `[]`
- required_hash_parity_ok: `True`
- notebook_default_ui: `v4-style ipywidgets UI; explicit console fallback only`
- ask_user_ui: `inline Agent Question prompt with Submit, Skip, Send fallback, and Stop unblock`
- minimum_ship_excludes: `tests/`, `docs/htmls/`, `sessions/`, `audit_logs/`,
  `__pycache__/`, `.pytest_cache/`, `.ipynb_checkpoints/`, `_status/`,
  `_phase_2/`, `.git/`

## Required Member Hash Parity

| member | status | source_sha256 | zip_sha256 |
|---|---|---|---|
| `chat.ipynb` | `match` | `812d329c53827aa4fd2684a552960a73b5c382caee0ccf3ce0d7f8ab06e8921f` | `812d329c53827aa4fd2684a552960a73b5c382caee0ccf3ce0d7f8ab06e8921f` |
| `chat.md` | `match` | `996fe67b24eb159492a996f2a7834a39611fc60c8e98a83e8ec57488df8ac162` | `996fe67b24eb159492a996f2a7834a39611fc60c8e98a83e8ec57488df8ac162` |
| `entry.py` | `match` | `58e4738aaf792cd6ab257606a0e88dea693ae682a68c5e7e16248cc3caaee189` | `58e4738aaf792cd6ab257606a0e88dea693ae682a68c5e7e16248cc3caaee189` |
| `memory.md` | `match` | `bb98a4de8478e8caafc472f37fc7e0e1b63f9245a5f9d971b84004aed02d3a4e` | `bb98a4de8478e8caafc472f37fc7e0e1b63f9245a5f9d971b84004aed02d3a4e` |
| `ui/chat_ui.py` | `match` | `6c1cd7015725ed3777ad79b456c77497acc978ef67f90ea63346e52bc87fcfd4` | `6c1cd7015725ed3777ad79b456c77497acc978ef67f90ea63346e52bc87fcfd4` |
| `agent.py` | `match` | `11352247ae72815e45a53558f1649dda60fe5a95403b4752cd5e05c9739f5a4c` | `11352247ae72815e45a53558f1649dda60fe5a95403b4752cd5e05c9739f5a4c` |
| `core/query_engine.py` | `match` | `5742b4b4ba96f6d2b113c1c0e9e5838fc7909622f95c5cdf815ca0bc22d3018f` | `5742b4b4ba96f6d2b113c1c0e9e5838fc7909622f95c5cdf815ca0bc22d3018f` |
| `tools/task.py` | `match` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` |
| `runtime/config.py` | `match` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` | `82fed69c8e676df15b79d054439268232ad5f93609313c3304dff7ec6672d68c` |
| `sagemaker_agent.py` | `match` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` |
| `AGENT_STATUS.md` | `match` | `7f671c99a300e51bc690c74b495ee953786f8846a2819475f66f3c2b1e1c72ad` | `7f671c99a300e51bc690c74b495ee953786f8846a2819475f66f3c2b1e1c72ad` |
| `tools/aws_s3_list.py` | `match` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` |
| `security/diagnostics.py` | `match` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` |
| `tools/ask_user.py` | `match` | `c04ab38b56356c10f9d4dededc3f3dbaa40f907ffdc433e775475b12a9c24b1c` | `c04ab38b56356c10f9d4dededc3f3dbaa40f907ffdc433e775475b12a9c24b1c` |

## Exclude Policy

Excluded directories: `__pycache__`, `.pytest_cache`, `.ipynb_checkpoints`,
`tests`, `sessions`, `audit_logs`, `_status`, `_phase_2`,
`compact_v5_test_evidence`, `.git`.

Source-only HTML architecture/reference docs under `docs/htmls/` are kept in
`compact_v5/` but excluded from `compact_v5_ship.zip` to make the ship artifact
smaller and less ambiguous.
