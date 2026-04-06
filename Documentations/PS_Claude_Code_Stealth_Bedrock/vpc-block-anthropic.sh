#!/bin/bash
# ============================================================
# OPTIONAL: Network-Level Block for api.anthropic.com
# ============================================================
# This blocks outbound traffic to Anthropic at the network level
# using iptables. This is OPTIONAL — the env vars already prevent
# Claude Code from making these calls, but this adds a guarantee.
#
# REQUIREMENTS: sudo/root access on the SageMaker instance
# NOTE: This does NOT block Bedrock endpoints (those still work)
# ============================================================

echo "=== Blocking api.anthropic.com at network level ==="

# Resolve current IPs for api.anthropic.com
IPS=$(dig +short api.anthropic.com 2>/dev/null)

if [ -z "$IPS" ]; then
    echo "Could not resolve api.anthropic.com — DNS may already be blocked"
    echo "Trying known Anthropic IP ranges..."
    # Fallback: block by domain using iptables string matching
    sudo iptables -A OUTPUT -m string --string "api.anthropic.com" --algo bm -j DROP 2>/dev/null
    echo "Added string-match block for api.anthropic.com"
else
    for ip in $IPS; do
        sudo iptables -A OUTPUT -d "$ip" -j DROP
        echo "Blocked: $ip (api.anthropic.com)"
    done
fi

echo
echo "=== Verification ==="
echo "Testing connection to api.anthropic.com..."
if curl -s --max-time 3 https://api.anthropic.com > /dev/null 2>&1; then
    echo "[FAIL] api.anthropic.com is still reachable"
    echo "       Check iptables rules: sudo iptables -L OUTPUT -n"
else
    echo "[PASS] api.anthropic.com is blocked"
fi

echo
echo "Testing connection to Bedrock (should still work)..."
if curl -s --max-time 5 "https://bedrock-runtime.${AWS_REGION:-us-east-1}.amazonaws.com" > /dev/null 2>&1; then
    echo "[PASS] Bedrock endpoint is reachable"
else
    echo "[INFO] Bedrock endpoint test inconclusive (may need auth)"
fi

echo
echo "NOTE: These iptables rules are NOT persistent across reboots."
echo "To make persistent, add this script to your lifecycle config."
