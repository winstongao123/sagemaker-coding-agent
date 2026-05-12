# UI Live Supervisor / S3 Real-Use / Notebook / ask_user / Resume / S3 Follow-Up / Widget Dependency Ship Zip Verify - 2026-05-12

- source_tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- source_tree_meaning: complete v5 development/runtime source tree
- ship_zip_path: `D:\Github\sagemaker-coding-agent\compact_v5_ship.zip`
- ship_zip_meaning: minimum runtime artifact to upload/extract in SageMaker
- retired_ambiguous_name: `compact_v5.zip`
- zip_size_bytes: `513300`
- member_count: `154`
- zip_sha256: `5042bc50ade5f7d4e2673930d67c0ed757c38517fceec23644c0e17f723bdb5b`
- testzip_result: `None`
- required_missing: `[]`
- forbidden_members: `[]`
- required_hash_parity_ok: `True`
- notebook_default_ui: `v4-style ipywidgets UI; explicit console fallback only`
- widget_dependency_contract: `Cell 1 does not install or upgrade ipywidgets, jupyterlab_widgets, or widgetsnbextension`
- ask_user_ui: `inline Agent Question prompt with Submit, Skip, Send fallback, and Stop unblock`
- resume_ui: `saved sessions rehydrate visible transcript after /resume`
- s3_followup_discipline: `reuse prior S3 object paths, cap follow-up list calls, preview selected files safely`
- user_artifacts_root: `relative deliverables in runtime package workspaces rebase to ~/sageagent_workspace`
- minimum_ship_excludes: `tests/`, `docs/htmls/`, `sessions/`, `audit_logs/`,
  `__pycache__/`, `.pytest_cache/`, `.ipynb_checkpoints/`, `_status/`,
  `_phase_2/`, `.sageagent_state/`, `.git/`

## Required Member Hash Parity

| member | status | source_sha256 | zip_sha256 |
|---|---|---|---|
| `chat.ipynb` | `match` | `ef4029f9ad21f43bb3e1f40ed40eda2e7a5d13cf49d599bb367ddfe32de00cf2` | `ef4029f9ad21f43bb3e1f40ed40eda2e7a5d13cf49d599bb367ddfe32de00cf2` |
| `chat.md` | `match` | `430125ca90a69e4c851195b77f8bf83c0f82906b7988a13567a99ef69d7851a7` | `430125ca90a69e4c851195b77f8bf83c0f82906b7988a13567a99ef69d7851a7` |
| `entry.py` | `match` | `58e4738aaf792cd6ab257606a0e88dea693ae682a68c5e7e16248cc3caaee189` | `58e4738aaf792cd6ab257606a0e88dea693ae682a68c5e7e16248cc3caaee189` |
| `memory.md` | `match` | `ca553d8f53276eeceeb7f923a99cac11e276b4a6e70c8292b97170ad2b782a3a` | `ca553d8f53276eeceeb7f923a99cac11e276b4a6e70c8292b97170ad2b782a3a` |
| `ui/chat_ui.py` | `match` | `0a572ddbf2e6269b26c2b57c40b0b4b7e5ce24c4acd100b587df4746b0f56841` | `0a572ddbf2e6269b26c2b57c40b0b4b7e5ce24c4acd100b587df4746b0f56841` |
| `agent.py` | `match` | `84b1f68baa4f74c723c6ddf7ec45e1f7f2cfff6a0b2cf93d5615d1dc98bd1fdf` | `84b1f68baa4f74c723c6ddf7ec45e1f7f2cfff6a0b2cf93d5615d1dc98bd1fdf` |
| `core/query_engine.py` | `match` | `0ad890c23b2fd503f17c12cc5fb3872e2c617bbdc628ca7c00c0a78251f82602` | `0ad890c23b2fd503f17c12cc5fb3872e2c617bbdc628ca7c00c0a78251f82602` |
| `tools/task.py` | `match` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` | `f36debe7cfaf25978c42a99289bb373a3612bb1e490e178fbbbb6c1a17bb17ed` |
| `runtime/config.py` | `match` | `7d3da39e5f00192ef7ea06d255acc960a770d9d986f9d91bd8ad7f571db4ccd8` | `7d3da39e5f00192ef7ea06d255acc960a770d9d986f9d91bd8ad7f571db4ccd8` |
| `runtime/state.py` | `match` | `1235247893378d5d8845434d38cde866bf029d4e1eda89c7051dfdafb68fb44b` | `1235247893378d5d8845434d38cde866bf029d4e1eda89c7051dfdafb68fb44b` |
| `sagemaker_agent.py` | `match` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` |
| `AGENT_STATUS.md` | `match` | `7f096f44773841bb8fb7a051ecab8b710efc1991770e736c96db353e5f0f1cbf` | `7f096f44773841bb8fb7a051ecab8b710efc1991770e736c96db353e5f0f1cbf` |
| `tools/aws_s3_list.py` | `match` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` |
| `tools/aws_s3_preview.py` | `match` | `e7e16e8a232809d63a0069f034e2e4b54173a5c4872344c8a191b71193828fa2` | `e7e16e8a232809d63a0069f034e2e4b54173a5c4872344c8a191b71193828fa2` |
| `tools/artifacts.py` | `match` | `2a172f8bbc24a74c22f1fb02deb233c3e660f9e4d50ce11bfc92ca6a64007569` | `2a172f8bbc24a74c22f1fb02deb233c3e660f9e4d50ce11bfc92ca6a64007569` |
| `security/diagnostics.py` | `match` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` |
| `tools/ask_user.py` | `match` | `c04ab38b56356c10f9d4dededc3f3dbaa40f907ffdc433e775475b12a9c24b1c` | `c04ab38b56356c10f9d4dededc3f3dbaa40f907ffdc433e775475b12a9c24b1c` |

## Exclude Policy

Excluded directories: `__pycache__`, `.pytest_cache`, `.ipynb_checkpoints`,
`tests`, `sessions`, `audit_logs`, `_status`, `_phase_2`, `.sageagent_state`,
`compact_v5_test_evidence`, `.git`.

Source-only HTML architecture/reference docs under `docs/htmls/` are kept in
`compact_v5/` but excluded from `compact_v5_ship.zip` to make the ship artifact
smaller and less ambiguous.
