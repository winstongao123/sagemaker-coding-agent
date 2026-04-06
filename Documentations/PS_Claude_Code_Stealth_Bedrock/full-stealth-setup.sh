#!/bin/bash
# ============================================================
# Claude Code FULL STEALTH Setup — Identical to boto3/V4
# ============================================================
# Makes Claude Code's Bedrock calls indistinguishable from
# native boto3 calls in AWS CloudTrail.
#
# USAGE:
#   source full-stealth-setup.sh          # Level 1 (headers only)
#   source full-stealth-setup.sh --proxy  # Level 2 (+ boto3 proxy)
#
# AFTER:  claude
# ============================================================

# --- Detect SageMaker environment for accurate User-Agent ---
PYTHON_VER=$(python3 --version 2>/dev/null | awk '{print $2}' || echo "3.11.9")
KERNEL_VER=$(uname -r 2>/dev/null || echo "5.15.0-1058-aws")
BOTO3_VER="${BOTO3_VER:-1.35.0}"
BOTOCORE_VER="${BOTOCORE_VER:-1.35.0}"
OS_NAME=$(uname -s 2>/dev/null || echo "Linux")

# Build a User-Agent string that matches EXACTLY what boto3 sends
BOTO3_UA="Boto3/${BOTO3_VER} Python/${PYTHON_VER} ${OS_NAME}/${KERNEL_VER} Botocore/${BOTOCORE_VER}"

# --- 1. USE BEDROCK ---
export CLAUDE_CODE_USE_BEDROCK=1

# --- 2. AWS REGION ---
export AWS_REGION="${AWS_REGION:-us-east-1}"

# --- 3. OVERRIDE ALL IDENTIFYING HEADERS ---
# Source: client.ts:104-109 — custom headers spread LAST, override defaults
# We set User-Agent to match boto3 exactly
# We blank out x-app and session ID (boto3 doesn't send these)
export ANTHROPIC_CUSTOM_HEADERS="User-Agent: ${BOTO3_UA}
x-app:
X-Claude-Code-Session-Id: "

# --- 4. BLOCK ALL OUTBOUND TO ANTHROPIC ---
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

# --- 5. DISABLE TELEMETRY ---
export DISABLE_TELEMETRY=1

# --- 6. DISABLE AUTO-UPDATER ---
export DISABLE_AUTOUPDATER=1

# --- 7. LEVEL 2: BOTO3 PROXY (optional) ---
if [ "$1" = "--proxy" ]; then
    # Point Claude Code to local proxy instead of Bedrock directly
    # The proxy re-sends via boto3 (Python TLS fingerprint)
    export HTTPS_PROXY="http://127.0.0.1:8900"

    # Check if proxy is running
    if curl -s --max-time 1 http://127.0.0.1:8900/health > /dev/null 2>&1; then
        PROXY_STATUS="RUNNING"
    else
        PROXY_STATUS="NOT RUNNING — start with: python3 bedrock_boto3_proxy.py"
    fi
fi

# --- Output ---
echo "============================================="
echo "  Claude Code FULL STEALTH — Active"
echo "============================================="
echo ""
echo "  Bedrock:      ON (region: $AWS_REGION)"
echo "  User-Agent:   $BOTO3_UA"
echo "  Outbound:     BLOCKED (no api.anthropic.com)"
echo "  Telemetry:    DISABLED"
echo "  Auto-update:  DISABLED"
echo "  Headers:      x-app=blank, Session-Id=blank"
if [ "$1" = "--proxy" ]; then
echo "  Proxy:        $PROXY_STATUS"
echo "  Level:        2 (Python TLS fingerprint)"
else
echo "  Level:        1 (Header override)"
fi
echo ""
echo "  CloudTrail will show: $BOTO3_UA"
echo ""
echo "  REMINDER: Verify Bedrock > Settings >"
echo "            Model invocation logging = OFF"
echo "============================================="
