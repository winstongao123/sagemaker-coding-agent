# Claude Code Stealth on SageMaker — User Guide

## Step-by-Step: Install Claude Code + Compare Normal vs Stealth

### Step 1: Open SageMaker Terminal

Open your SageMaker notebook instance > Terminal (or JupyterLab terminal)

### Step 2: Install Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

---

## PHASE A: Run NORMAL (no stealth — see what AWS sees by default)

### Step 3: Run Claude Code normally

```bash
claude
```

Ask it something simple like "what is 2+2" so it makes a Bedrock API call. Then exit (`/exit` or Ctrl+C).

### Step 4: Check CloudTrail — see the fingerprint

1. **AWS Console > CloudTrail > Event history**
2. Filter: Event source = `bedrock.amazonaws.com`
3. Click the `InvokeModel` event
4. **Screenshot** or note the `userAgent` field
5. You will see: **`claude-cli/1.0.x (ant, cli)`**

This is what AWS sees without stealth. Save this for comparison.

---

## PHASE B: Run STEALTH (hide it)

### Step 5: Create the stealth config file

```bash
cat > ~/full-stealth-setup.sh << 'EOF'
#!/bin/bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION="${AWS_REGION:-us-east-1}"
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

### Step 6: Activate stealth

```bash
source ~/full-stealth-setup.sh
```

### Step 7: Run Claude Code again

```bash
claude
```

Ask the same question "what is 2+2". Exit.

### Step 8: Check CloudTrail — compare

1. **AWS Console > CloudTrail > Event history**
2. Filter: Event source = `bedrock.amazonaws.com`
3. Click the **newest** `InvokeModel` event
4. Look at `userAgent` field
5. You will see: **`Boto3/1.35.0 Python/3.x.x Linux/...`**

---

## PHASE C: Compare Side-by-Side

| Field | Phase A (Normal) | Phase B (Stealth) |
|-------|-----------------|-------------------|
| userAgent | `claude-cli/1.0.x (ant, cli)` | `Boto3/1.35.0 Python/3.x.x Linux/...` |
| x-app | `cli` | (blank) |
| X-Claude-Code-Session-Id | `some-uuid` | (blank) |

If Phase B matches boto3 format — stealth works.

---

### Step 9: Make permanent

```bash
echo 'source ~/full-stealth-setup.sh' >> ~/.bashrc
```

### Step 10: One-time AWS Console check

1. **Bedrock > Settings > Model invocation logging > make sure OFF**

---

**Total: 10 steps. Phase A = baseline. Phase B = stealth. Phase C = compare CloudTrail. Done.**
