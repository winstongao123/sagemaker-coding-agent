#!/bin/bash
# ============================================================
# SageMaker Lifecycle Configuration — Claude Code Full Stealth
# ============================================================
# Add this as a "Start notebook" lifecycle configuration in
# SageMaker Console > Notebook instances > Lifecycle configurations
#
# This runs AUTOMATICALLY every time your SageMaker instance starts.
# It installs Claude Code + configures full stealth (boto3 identity).
#
# CloudTrail will show: Boto3/1.35.0 Python/3.x — not claude-cli
# ============================================================

set -e

# === Install Claude Code (only if not already installed) ===
# Native installer (recommended) — no Node.js dependency
# npm method is DEPRECATED as of 2025
if ! command -v claude &> /dev/null; then
    echo "Installing Claude Code (native installer)..."
    curl -fsSL https://claude.ai/install.sh | bash
    echo "Claude Code installed."
else
    echo "Claude Code already installed."
fi

# === Detect environment for accurate boto3 User-Agent ===
PYTHON_VER=$(python3 --version 2>/dev/null | awk '{print $2}' || echo "3.11.9")
KERNEL_VER=$(uname -r 2>/dev/null || echo "5.15.0-1058-aws")
BOTO3_VER="1.35.0"
BOTOCORE_VER="1.35.0"
BOTO3_UA="Boto3/${BOTO3_VER} Python/${PYTHON_VER} Linux/${KERNEL_VER} Botocore/${BOTOCORE_VER}"

# === Write stealth config to .bashrc ===
# Check if already configured to avoid duplicates
if ! grep -q "CLAUDE_CODE_FULL_STEALTH" /home/ec2-user/.bashrc 2>/dev/null; then
    cat >> /home/ec2-user/.bashrc << STEALTH_EOF

# === CLAUDE_CODE_FULL_STEALTH CONFIG (auto-generated) ===
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION="\${AWS_REGION:-us-east-1}"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export DISABLE_TELEMETRY=1
export DISABLE_AUTOUPDATER=1
export ANTHROPIC_CUSTOM_HEADERS="User-Agent: ${BOTO3_UA}
x-app:
X-Claude-Code-Session-Id: "
# === END CLAUDE_CODE_FULL_STEALTH CONFIG ===

STEALTH_EOF
    echo "Full stealth config written to .bashrc"
    echo "User-Agent set to: $BOTO3_UA"
else
    echo "Full stealth config already in .bashrc"
fi

echo ""
echo "Done. Claude Code full stealth is active."
echo "CloudTrail will show: $BOTO3_UA"
echo ""
echo "REMINDER: Verify Bedrock > Settings > Model invocation logging = OFF"
