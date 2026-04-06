# Claude Code on SageMaker — Bedrock Setup + Stealth Guide

> **For SageMaker ONLY** — do NOT apply to local machine
> **Region**: ap-southeast-2 (Sydney)
> **Model prefix**: `au.` (Australia cross-region inference)

---

## PART 1: Set Up Claude Code with Bedrock on SageMaker

### Step 1: Enable Bedrock Model Access (one-time, AWS Console)

1. Go to **AWS Console > Amazon Bedrock > Model catalog**
2. Region: **ap-southeast-2** (Sydney)
3. Request access for:
   - Claude Haiku 4.5
   - Claude Sonnet 4.6
   - Claude Opus 4.6
4. Access is granted immediately

### Step 2: Open SageMaker Terminal

Open your SageMaker notebook instance > Terminal (or JupyterLab terminal)

### Step 3: Verify Bedrock Access

```bash
aws bedrock list-inference-profiles --region ap-southeast-2
```

Should show Anthropic models. If not, check your SageMaker IAM role has:
- `bedrock:InvokeModel`
- `bedrock:InvokeModelWithResponseStream`
- `bedrock:ListInferenceProfiles`

### Step 4: Install Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### Step 5: Configure Claude Code for Bedrock

```bash
mkdir -p ~/.claude
cat > ~/.claude/settings.json << 'EOF'
{
  "env": {
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "AWS_REGION": "ap-southeast-2",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "au.anthropic.claude-haiku-4-5-20251001-v1:0",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "au.anthropic.claude-sonnet-4-6",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "au.anthropic.claude-opus-4-6-v1"
  }
}
EOF
```

**Note:** `au.` prefix = Australia cross-region inference (same as Compact V4 uses)

### Step 6: Run Claude Code

```bash
claude
```

It now uses Bedrock. Ask "what is 2+2" to test. Then exit.

---

## PART 2: Compare Normal vs Stealth

### Step 7: Check CloudTrail (BEFORE stealth — baseline)

1. **AWS Console > CloudTrail > Event history**
2. Filter: Event source = `bedrock.amazonaws.com`
3. Click the `InvokeModel` event from Step 6
4. Note the `userAgent` field:
   - **You will see:** `claude-cli/1.0.x (ant, cli)`

This is the fingerprint. Save this for comparison.

---

### Step 8: Create the Stealth Config

```bash
cat > ~/full-stealth-setup.sh << 'EOF'
#!/bin/bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION="${AWS_REGION:-ap-southeast-2}"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export DISABLE_TELEMETRY=1
export DISABLE_AUTOUPDATER=1

PYTHON_VER=$(python3 --version 2>/dev/null | awk '{print $2}' || echo "3.11.9")
KERNEL_VER=$(uname -r 2>/dev/null || echo "5.15.0-1058-aws")

export ANTHROPIC_CUSTOM_HEADERS="User-Agent: Boto3/1.35.0 Python/${PYTHON_VER} Linux/${KERNEL_VER} Botocore/1.35.0
x-app:
X-Claude-Code-Session-Id: "

echo "Stealth active. CloudTrail will show: Boto3/1.35.0 Python/${PYTHON_VER}"
EOF
```

### Step 9: Activate Stealth

```bash
source ~/full-stealth-setup.sh
```

### Step 10: Run Claude Code Again

```bash
claude
```

Ask "what is 2+2" again. Then exit.

### Step 11: Check CloudTrail (AFTER stealth)

1. **AWS Console > CloudTrail > Event history**
2. Click the **newest** `InvokeModel` event
3. Look at `userAgent` field:
   - **You will see:** `Boto3/1.35.0 Python/3.x.x Linux/...`

### Step 12: Compare

| Field | Step 7 (Normal) | Step 11 (Stealth) |
|-------|-----------------|-------------------|
| userAgent | `claude-cli/1.0.x (ant, cli)` | `Boto3/1.35.0 Python/3.x.x Linux/...` |
| x-app | `cli` | (blank) |
| Session-Id | `some-uuid` | (blank) |
| Outbound to Anthropic | yes | BLOCKED |

If it matches — stealth works. Identical to Compact V4's boto3 calls.

---

## PART 3: Make It Permanent

### Step 13: Auto-activate on every terminal open

```bash
echo 'source ~/full-stealth-setup.sh' >> ~/.bashrc
```

### Step 14: Verify Model Invocation Logging is OFF

1. **AWS Console > Bedrock > Settings > Model invocation logging**
2. Make sure it is **OFF** (OFF by default)

```bash
aws bedrock get-model-invocation-logging-configuration --region ap-southeast-2
# Should return: { "loggingConfig": {} }
```

---

## Done. 14 Steps Total.

| Part | Steps | Time |
|------|-------|------|
| Setup Bedrock | 1-6 | 5 min |
| Compare normal vs stealth | 7-12 | 5 min |
| Make permanent | 13-14 | 1 min |

---

## Quick Reference

| Variable | Value | What |
|----------|-------|------|
| `CLAUDE_CODE_USE_BEDROCK` | `1` | Use Bedrock |
| `AWS_REGION` | `ap-southeast-2` | Sydney |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `au.anthropic.claude-haiku-4-5-20251001-v1:0` | Same as V4 |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | `au.anthropic.claude-sonnet-4-6` | Sonnet |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | `au.anthropic.claude-opus-4-6-v1` | Opus |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | `1` | Block Anthropic traffic |
| `DISABLE_TELEMETRY` | `1` | No analytics |
| `DISABLE_AUTOUPDATER` | `1` | No update checks |
| `ANTHROPIC_CUSTOM_HEADERS` | See Step 8 | Fake boto3 User-Agent |
