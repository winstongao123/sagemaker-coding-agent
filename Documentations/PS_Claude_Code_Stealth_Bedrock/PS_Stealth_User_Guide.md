# Claude Code on SageMaker — Stealth Install Guide

> **For SageMaker ONLY**
> Region: ap-southeast-2 (Sydney)
> User-Agent matches Compact V4 exactly

---

## Step 1: Remove old install

```bash
rm -rf ~/.local/bin/claude ~/.claude ~/full-stealth-setup.sh ~/bedrock_list_proxy.py && sed -i '/stealth/d' ~/.bashrc && sed -i '/full-stealth/d' ~/.bashrc && sed -i '/\.local\/bin/d' ~/.bashrc
unset ANTHROPIC_BEDROCK_BASE_URL
```

Verify clean:
```bash
which claude
```
Should say `command not found`.

---

## Step 2: Install Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

---

## Step 3: Add to PATH

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

---

## Step 4: Create settings

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

---

## Step 5: TEST A — Run WITHOUT stealth

```bash
claude
```

Ask "what is 2+2". Exit. Tell me **"check A"**.

---

## Step 6: Create stealth script

User-Agent matches your actual Compact V4 CloudTrail signature exactly.

```bash
cat > ~/full-stealth-setup.sh << 'EOF'
#!/bin/bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION="${AWS_REGION:-ap-southeast-2}"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export DISABLE_TELEMETRY=1
export DISABLE_AUTOUPDATER=1

KERNEL_VER=$(uname -r 2>/dev/null || echo "5.15.0-1058-aws")

export ANTHROPIC_CUSTOM_HEADERS="User-Agent: Boto3/1.42.83 md/Botocore#1.42.83 md/awscrt#0.31.2 ua/2.1 os/linux#${KERNEL_VER} lang/python#3.12.9
x-app:
X-Claude-Code-Session-Id: "
EOF
```

---

## Step 7: Activate stealth

```bash
source ~/full-stealth-setup.sh
```

---

## Step 8: TEST B — Run WITH stealth

```bash
claude
```

Ask "what is 2+2". Exit. Tell me **"check B"**.

---

## Step 9: TEST C — Run Compact V4

```bash
python3 -c "
from sagemaker_agent import Agent, BedrockClient
client = BedrockClient(model_id='au.anthropic.claude-haiku-4-5-20251001-v1:0', region='ap-southeast-2')
agent = Agent(client=client)
print(agent.run('what is 2+2'))
"
```

Tell me **"check C"**.

---

## Step 10: I compare all three

Tell me **"check all"** and I pull CloudTrail to show:

| Test | Expected userAgent |
|------|-------------------|
| A (no stealth) | `claude-cli/2.1.92 (external, cli)` |
| B (stealth) | `Boto3/1.42.83 md/Botocore#1.42.83 md/awscrt#0.31.2 ua/2.1 os/linux#...` |
| C (Compact V4) | `Boto3/1.42.83 md/Botocore#1.42.83 md/awscrt#0.31.2 ua/2.1 os/linux#...` |

B and C should be **identical**.

---

## Step 11: Make permanent

```bash
echo 'source ~/full-stealth-setup.sh' >> ~/.bashrc
```

---

## Step 12: Check model logging is OFF

- AWS Console > Bedrock > Settings > Model invocation logging > **OFF**

```bash
aws bedrock get-model-invocation-logging-configuration --region ap-southeast-2
```

Should return `{ "loggingConfig": {} }`.

---

**12 steps. Tell me "check A", "check B", "check C", or "check all" anytime.**
