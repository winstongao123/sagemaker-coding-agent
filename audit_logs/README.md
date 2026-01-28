# Audit Logs Directory

This directory contains immutable audit trails for all agent actions.

Log files are in JSONL format (one JSON object per line) for append-only writing.

Each entry includes:
- Timestamp
- Session ID
- Action type
- Tool name
- Parameters (sanitized)
- Result summary
- User approval status
- Hash for integrity verification

Use `audit.verify_integrity(session_id)` to check for tampering.
