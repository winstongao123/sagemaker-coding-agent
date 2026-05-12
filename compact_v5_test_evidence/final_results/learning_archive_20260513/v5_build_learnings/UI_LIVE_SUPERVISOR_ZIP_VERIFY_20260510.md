# UI Live Supervisor / S3 Real-Use / Notebook / ask_user / Resume / S3 Follow-Up / Widget Dependency Ship Zip Verify - 2026-05-12

- source_tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- source_tree_meaning: complete v5 development/runtime source tree
- ship_zip_path: `D:\Github\sagemaker-coding-agent\compact_v5_ship.zip`
- ship_zip_meaning: minimum runtime artifact to upload/extract in SageMaker
- retired_ambiguous_name: `compact_v5.zip`
- zip_size_bytes: `523324`
- member_count: `155`
- zip_sha256: `87256ae1ef1cc173896eae9081e58abf31ac542fa96845de8caa3486c696c869`
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
| `chat.ipynb` | `match` | `504f039d7ea0fb0e812715c40af6541c5bdfa6117edc1c4c44b33f8bd9150bbb` | `504f039d7ea0fb0e812715c40af6541c5bdfa6117edc1c4c44b33f8bd9150bbb` |
| `chat.md` | `match` | `d2ccf7a8198354d7d00c3b2e1a3abe97c9f1084b193a2c81c7147cdd5a775cc3` | `d2ccf7a8198354d7d00c3b2e1a3abe97c9f1084b193a2c81c7147cdd5a775cc3` |
| `entry.py` | `match` | `af7c6da1e5f6d1a18266d1842e5938d1a8884b14dc44b63189ac9035e92a64ed` | `af7c6da1e5f6d1a18266d1842e5938d1a8884b14dc44b63189ac9035e92a64ed` |
| `memory.md` | `match` | `520a0ff1603c54cf0fb6db5988790742c999be743db5f35165b2448a44d0f85b` | `520a0ff1603c54cf0fb6db5988790742c999be743db5f35165b2448a44d0f85b` |
| `ui/chat_ui.py` | `match` | `94cc2f33dd18dbbf4e79ca752f0946dae3baf1d1fb2c987521bd70fce91f3cf4` | `94cc2f33dd18dbbf4e79ca752f0946dae3baf1d1fb2c987521bd70fce91f3cf4` |
| `agent.py` | `match` | `6928c0dcf627fdf056f214b06f5a9aa814f662752c0a5e1130beb07095334b23` | `6928c0dcf627fdf056f214b06f5a9aa814f662752c0a5e1130beb07095334b23` |
| `core/query_engine.py` | `match` | `393b3c33b8ce8ded058e99e36f18f979225801a746dac26ae4dd88c5c51281e3` | `393b3c33b8ce8ded058e99e36f18f979225801a746dac26ae4dd88c5c51281e3` |
| `tools/task.py` | `match` | `70918b516c03bee4935b4b661f02174f2fc224a1a0ffc89e28ad3ee566e2526b` | `70918b516c03bee4935b4b661f02174f2fc224a1a0ffc89e28ad3ee566e2526b` |
| `runtime/config.py` | `match` | `22774cdab50d88f8122905aceee182b68b962194a889a506cf12617c68a770da` | `22774cdab50d88f8122905aceee182b68b962194a889a506cf12617c68a770da` |
| `runtime/state.py` | `match` | `36875f581bb6fa55d4db4c22711bd392b2cb4deaeedbe181200b9f0586d76571` | `36875f581bb6fa55d4db4c22711bd392b2cb4deaeedbe181200b9f0586d76571` |
| `sagemaker_agent.py` | `match` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` | `eb20e51869fe5db635c88259662ab54c9dff9d63e3ed1415073362233ee43fa2` |
| `AGENT_STATUS.md` | `match` | `dc5e90ab5e06917a577c6a591e4778c8570ce6efa132ee6e1b855c87016bbfef` | `dc5e90ab5e06917a577c6a591e4778c8570ce6efa132ee6e1b855c87016bbfef` |
| `tools/aws_s3_list.py` | `match` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` | `15922ff1035972ee5d4eb2ebae53c01eb88895572dac04f04ea48ec18b665430` |
| `tools/aws_s3_preview.py` | `match` | `e7e16e8a232809d63a0069f034e2e4b54173a5c4872344c8a191b71193828fa2` | `e7e16e8a232809d63a0069f034e2e4b54173a5c4872344c8a191b71193828fa2` |
| `tools/artifacts.py` | `match` | `304e78f698e2a7137dd319f6356c47c8287554697d5ddbd703830cf3bd2a24ec` | `304e78f698e2a7137dd319f6356c47c8287554697d5ddbd703830cf3bd2a24ec` |
| `security/diagnostics.py` | `match` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` | `c18ce0e105f0e2fd5a45dd56484c5110be9e0afafab9c8edeb73bc472a0f04d0` |
| `tools/ask_user.py` | `match` | `c04ab38b56356c10f9d4dededc3f3dbaa40f907ffdc433e775475b12a9c24b1c` | `c04ab38b56356c10f9d4dededc3f3dbaa40f907ffdc433e775475b12a9c24b1c` |
| `runtime/workspace.py` | `match` | `876eefa25c62e27eaf772b9754b0d228286e26962b612beb68ddcb55df518d32` | `876eefa25c62e27eaf772b9754b0d228286e26962b612beb68ddcb55df518d32` |
| `tools/bash.py` | `match` | `ab15477289088d6af563d18034bc5523ea5ae7ef8ecd2e9f8a6565b7353714fe` | `ab15477289088d6af563d18034bc5523ea5ae7ef8ecd2e9f8a6565b7353714fe` |

## Exclude Policy

Excluded directories: `__pycache__`, `.pytest_cache`, `.ipynb_checkpoints`,
`tests`, `sessions`, `audit_logs`, `_status`, `_phase_2`, `.sageagent_state`,
`compact_v5_test_evidence`, `.git`.

Source-only HTML architecture/reference docs under `docs/htmls/` are kept in
`compact_v5/` but excluded from `compact_v5_ship.zip` to make the ship artifact
smaller and less ambiguous.
