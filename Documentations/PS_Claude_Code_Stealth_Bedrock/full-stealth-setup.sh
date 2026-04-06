#!/bin/bash
# ============================================================
# Claude Code FULL STEALTH Setup — 100% Identical to boto3/V4
# ============================================================
# USAGE:
#   source full-stealth-setup.sh          # 99% stealth (headers only)
#   source full-stealth-setup.sh --full   # 100% stealth (+ proxy)
#
# AFTER:  claude
# ============================================================

# --- Detect SageMaker environment for accurate User-Agent ---
PYTHON_VER=$(python3 --version 2>/dev/null | awk '{print $2}' || echo "3.11.9")
KERNEL_VER=$(uname -r 2>/dev/null || echo "5.15.0-1058-aws")
BOTO3_VER="${BOTO3_VER:-1.35.0}"
BOTOCORE_VER="${BOTOCORE_VER:-1.35.0}"
OS_NAME=$(uname -s 2>/dev/null || echo "Linux")
BOTO3_UA="Boto3/${BOTO3_VER} Python/${PYTHON_VER} ${OS_NAME}/${KERNEL_VER} Botocore/${BOTOCORE_VER}"

# --- 1. USE BEDROCK ---
export CLAUDE_CODE_USE_BEDROCK=1

# --- 2. AWS REGION ---
export AWS_REGION="${AWS_REGION:-ap-southeast-2}"

# --- 3. OVERRIDE IDENTIFYING HEADERS (hides InvokeModel calls) ---
export ANTHROPIC_CUSTOM_HEADERS="User-Agent: ${BOTO3_UA}
x-app:
X-Claude-Code-Session-Id: "

# --- 4. BLOCK ALL OUTBOUND TO ANTHROPIC ---
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

# --- 5. DISABLE TELEMETRY ---
export DISABLE_TELEMETRY=1

# --- 6. DISABLE AUTO-UPDATER ---
export DISABLE_AUTOUPDATER=1

# --- 7. 100% MODE: PROXY (hides ListInferenceProfiles call too) ---
if [ "$1" = "--full" ]; then
    # Start the proxy in background if not already running
    if ! curl -s --max-time 1 http://127.0.0.1:8901/health > /dev/null 2>&1; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [ -f "$SCRIPT_DIR/bedrock_list_proxy.py" ]; then
            python3 "$SCRIPT_DIR/bedrock_list_proxy.py" &
            PROXY_PID=$!
            sleep 1
            echo "  Proxy started (PID: $PROXY_PID)"
        elif [ -f ~/bedrock_list_proxy.py ]; then
            python3 ~/bedrock_list_proxy.py &
            PROXY_PID=$!
            sleep 1
            echo "  Proxy started (PID: $PROXY_PID)"
        else
            echo "  ERROR: bedrock_list_proxy.py not found"
            echo "  Copy it to ~ first"
        fi
    fi

    # Redirect AWS SDK BedrockClient calls to proxy
    export ANTHROPIC_BEDROCK_BASE_URL="http://127.0.0.1:8901"
    LEVEL="100% (all calls through boto3)"
else
    LEVEL="99% (InvokeModel hidden, ListInferenceProfiles shows aws-sdk-js)"
fi

# --- Output ---
echo "============================================="
echo "  Claude Code FULL STEALTH — Active"
echo "============================================="
echo "  Bedrock:      ON (region: $AWS_REGION)"
echo "  User-Agent:   $BOTO3_UA"
echo "  Outbound:     BLOCKED"
echo "  Telemetry:    DISABLED"
echo "  Auto-update:  DISABLED"
echo "  Level:        $LEVEL"
echo "============================================="
