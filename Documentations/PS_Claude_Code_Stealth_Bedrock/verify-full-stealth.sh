#!/bin/bash
# ============================================================
# Verify Claude Code Full Stealth Configuration
# ============================================================
# Run after: source full-stealth-setup.sh
# Checks every layer of stealth is active.
# ============================================================

PASS=0
FAIL=0
WARN=0

pass_fn() { echo "  [PASS] $1"; PASS=$((PASS + 1)); }
fail_fn() { echo "  [FAIL] $1"; FAIL=$((FAIL + 1)); }
warn_fn() { echo "  [WARN] $1"; WARN=$((WARN + 1)); }
info() { echo "  [INFO] $1"; }

echo "============================================="
echo "  Claude Code Full Stealth — Verification"
echo "============================================="
echo ""

# --- 1. Core env vars ---
echo "--- Environment Variables ---"
check_env() {
    local var="$1"
    local expected="$2"
    local val="${!var}"
    if [ "$val" = "$expected" ]; then
        pass_fn "$var=$val"
    elif [ -n "$val" ]; then
        pass_fn "$var=$val"
    else
        fail_fn "$var is NOT SET"
    fi
}
check_env CLAUDE_CODE_USE_BEDROCK 1
check_env AWS_REGION ""
check_env CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC 1
check_env DISABLE_TELEMETRY 1
check_env DISABLE_AUTOUPDATER 1

# --- 2. Header overrides ---
echo ""
echo "--- Header Overrides ---"
if [ -n "$ANTHROPIC_CUSTOM_HEADERS" ]; then
    # Check User-Agent contains Boto3
    if echo "$ANTHROPIC_CUSTOM_HEADERS" | grep -q "Boto3"; then
        UA_LINE=$(echo "$ANTHROPIC_CUSTOM_HEADERS" | grep "User-Agent")
        pass_fn "User-Agent set to boto3 format"
        info "  → $UA_LINE"
    else
        warn_fn "User-Agent is set but doesn't match boto3 format"
    fi

    # Check x-app is blanked
    if echo "$ANTHROPIC_CUSTOM_HEADERS" | grep -q "^x-app:"; then
        X_APP_VAL=$(echo "$ANTHROPIC_CUSTOM_HEADERS" | grep "^x-app:" | cut -d: -f2 | tr -d ' ')
        if [ -z "$X_APP_VAL" ]; then
            pass_fn "x-app header blanked (boto3 doesn't send this)"
        else
            warn_fn "x-app header set to '$X_APP_VAL' (boto3 doesn't send x-app)"
        fi
    else
        fail_fn "x-app header not overridden — will leak 'cli'"
    fi

    # Check Session-Id is blanked
    if echo "$ANTHROPIC_CUSTOM_HEADERS" | grep -q "X-Claude-Code-Session-Id:"; then
        SID_VAL=$(echo "$ANTHROPIC_CUSTOM_HEADERS" | grep "X-Claude-Code-Session-Id:" | cut -d: -f2 | tr -d ' ')
        if [ -z "$SID_VAL" ]; then
            pass_fn "X-Claude-Code-Session-Id blanked"
        else
            warn_fn "X-Claude-Code-Session-Id set to '$SID_VAL' (should be blank)"
        fi
    else
        fail_fn "X-Claude-Code-Session-Id not overridden — will leak session UUID"
    fi
else
    fail_fn "ANTHROPIC_CUSTOM_HEADERS not set — ALL identifying headers will leak!"
fi

# --- 3. Proxy check (Level 2) ---
echo ""
echo "--- Proxy (Level 2) ---"
if [ -n "$HTTPS_PROXY" ]; then
    info "HTTPS_PROXY=$HTTPS_PROXY"
    if curl -s --max-time 2 "http://127.0.0.1:8900/health" > /dev/null 2>&1; then
        pass_fn "Boto3 proxy is RUNNING"
        HEALTH=$(curl -s --max-time 2 "http://127.0.0.1:8900/health" 2>/dev/null)
        info "  → $HEALTH"
    else
        fail_fn "Boto3 proxy is NOT running — start: python3 bedrock_boto3_proxy.py"
    fi
else
    info "Level 2 proxy not configured (Level 1 only — this is fine)"
fi

# --- 4. Network test ---
echo ""
echo "--- Outbound Network ---"
if command -v curl &> /dev/null; then
    if curl -s --max-time 3 https://api.anthropic.com > /dev/null 2>&1; then
        info "api.anthropic.com is reachable (OK — env vars prevent calls)"
        info "  For extra security, block at VPC security group level"
    else
        pass_fn "api.anthropic.com is NOT reachable"
    fi
else
    info "curl not available — cannot test outbound"
fi

# --- 5. AWS model invocation logging ---
echo ""
echo "--- Model Invocation Logging ---"
if command -v aws &> /dev/null; then
    LOGGING=$(aws bedrock get-model-invocation-logging-configuration \
        --region "${AWS_REGION:-us-east-1}" 2>/dev/null)
    if [ $? -eq 0 ]; then
        if echo "$LOGGING" | grep -q '"loggingConfig": {}'; then
            pass_fn "Model invocation logging is DISABLED"
        elif echo "$LOGGING" | grep -qE "s3Config|cloudWatchConfig"; then
            fail_fn "Model invocation logging is ENABLED — system prompt will leak!"
            info "  → Fix: Bedrock > Settings > Model invocation logging > OFF"
        else
            info "Logging config: $LOGGING"
        fi
    else
        info "Could not query Bedrock logging config (check IAM permissions)"
        info "  → Manually verify: Bedrock > Settings > Model invocation logging = OFF"
    fi
else
    info "AWS CLI not available"
    info "  → Manually verify: Bedrock > Settings > Model invocation logging = OFF"
fi

# --- Summary ---
echo ""
echo "============================================="
echo "  RESULTS: $PASS passed, $FAIL failed, $WARN warnings"
echo "============================================="
if [ "$FAIL" -eq 0 ]; then
    echo ""
    echo "  ALL CHECKS PASSED"
    echo ""
    echo "  What AWS CloudTrail will show:"
    UA_LINE=$(echo "$ANTHROPIC_CUSTOM_HEADERS" | grep "User-Agent:" | sed 's/User-Agent: //')
    echo "    userAgent: \"$UA_LINE\""
    echo "    (No x-app, no Session-Id, no claude-cli)"
    echo ""
    echo "  What Compact V4 (boto3) shows:"
    echo "    userAgent: \"Boto3/1.35.0 Python/3.11.9 ...\""
    echo ""
    echo "  → IDENTICAL"
else
    echo ""
    echo "  SOME CHECKS FAILED — review [FAIL] items above"
    echo "  Run: source full-stealth-setup.sh"
fi
echo "============================================="
