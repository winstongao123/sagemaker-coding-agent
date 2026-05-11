# Block 1 - S3 Safe-Read Path

Goal: provide one explicit read-only S3 inventory path when `CONFIG.aws_bedrock_only=False`, without exposing general AWS CLI.

Implementation:
- Added `compact_v5/tools/aws_s3_list.py`.
- Registered `aws_s3_list` as always-loaded, read-only, approval-gated, non-destructive.
- Added `aws_s3_list` to plan-mode read-only allowlist.
- Updated bash security guidance so blocked `aws s3` points to `aws_s3_list`.
- Updated prompt/security guidance for S3 inventory.
- Added fake-client smoke tests.
