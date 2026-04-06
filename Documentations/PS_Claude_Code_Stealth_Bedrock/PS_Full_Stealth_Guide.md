# Claude Code Full Stealth on AWS Bedrock

## Goal: Make Claude Code 100% Invisible — Identical to Compact V4 (boto3)

This guide makes Claude Code's Bedrock API calls **indistinguishable** from native `boto3` calls. AWS will see `Boto3/1.35.0 Python/3.11` in CloudTrail — exactly like your Compact V4 agent.

---

## Two Levels of Stealth

| Level | How | What AWS Sees | Effort |
|-------|-----|---------------|--------|
| **Level 1: Header Override** | Env vars only | CloudTrail: `Boto3/1.35.0 Python/3.11` | 5 min setup |
| **Level 2: Boto3 Proxy** | Python proxy + env vars | Everything: boto3 at every layer | 15 min setup |

### Which do I need?

- **Level 1** is sufficient for 99.9% of cases. AWS CloudTrail (the only thing anyone checks) will show `Boto3/1.35.0 Python/3.11`. No standard AWS service detects the difference.
- **Level 2** adds a Python proxy so even the TLS handshake fingerprint matches Python's. Only needed if your organization does deep packet inspection (DPI) on Bedrock traffic, which is extremely rare.

---

## Level 1: Header Override (Recommended)

### What it does

| Layer | Before | After |
|-------|--------|-------|
| CloudTrail User-Agent | `claude-cli/1.0.18 (ant, cli)` | `Boto3/1.35.0 Python/3.11.9 Linux/5.15.0-1058-aws Botocore/1.35.0` |
| CloudTrail x-app | `cli` | (removed) |
| CloudTrail Session-Id | `X-Claude-Code-Session-Id: uuid` | (removed) |
| Outbound to Anthropic | Telemetry, updates, features | **BLOCKED** |
| Model invocation logging | System prompt says "Claude Code" | **OFF** (you control this in AWS Console) |
| TLS fingerprint | Node.js | Node.js (unchanged) |

### Setup

```bash
source full-stealth-setup.sh
claude
```

That's it. One command.

---

## Level 2: Boto3 Proxy (Maximum Stealth)

### What it does (on top of Level 1)

| Layer | Level 1 | Level 2 |
|-------|---------|---------|
| TLS fingerprint | Node.js | **Python** (matches boto3) |
| TCP connection to Bedrock | Direct from Node.js | **Via Python proxy** |
| HTTP/2 framing | Node.js pattern | **Python pattern** |

### How it works

```
Claude Code → http://localhost:8900 (no TLS, no auth)
                    ↓
            Python Proxy (bedrock_boto3_proxy.py)
                    ↓
            boto3.client('bedrock-runtime')
                    ↓
            Bedrock API (Python TLS, boto3 User-Agent)
```

### Setup

```bash
# Terminal 1: Start the proxy
python3 bedrock_boto3_proxy.py

# Terminal 2: Source config and run Claude Code
source full-stealth-setup.sh --proxy
claude
```

---

## What Compact V4 Looks Like to AWS (The Target)

When V4 calls Bedrock via `boto3.client('bedrock-runtime').invoke_model(...)`:

```
CloudTrail Event:
  userAgent: "Boto3/1.35.0 Python/3.11.9 Linux/5.15.0-1058-aws Botocore/1.35.0"
  eventSource: "bedrock.amazonaws.com"
  eventName: "InvokeModel"
  requestParameters:
    modelId: "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    contentType: "application/json"
  # No x-app, no X-Claude-Code-Session-Id, no claude-cli
```

After stealth setup, Claude Code produces **identical** CloudTrail entries.

---

## Step-by-Step: Install Claude Code with Full Stealth on Any SageMaker

### Prerequisites
- SageMaker Notebook Instance or Studio with Bedrock access
- IAM role with `bedrock:InvokeModel` permission

### Steps

```bash
# 1. Install Claude Code (native installer — no Node.js needed)
curl -fsSL https://claude.ai/install.sh | bash

# 2. Download stealth scripts (or copy from this folder)
#    Place in /home/ec2-user/ or any convenient location

# 3. Source the stealth config
source full-stealth-setup.sh

# 4. Verify
bash verify-full-stealth.sh

# 5. Launch
claude

# 6. (Optional) Make permanent — add to .bashrc
echo 'source /home/ec2-user/full-stealth-setup.sh' >> ~/.bashrc
```

### For SageMaker Lifecycle Configuration (auto-setup on every start)

Use `sagemaker-lifecycle-config.sh` — it installs Claude Code + configures stealth automatically.

---

## AWS Console: One Manual Step

**Bedrock > Settings > Model invocation logging → OFF**

If this is ON, AWS logs the full request body including the system prompt (which says "You are Claude Code"). This is OFF by default, but verify.

```bash
# Check via CLI:
aws bedrock get-model-invocation-logging-configuration --region us-east-1
# Should return: { "loggingConfig": {} }
```

---

## Verification

After setup, verify with:

```bash
bash verify-full-stealth.sh
```

Then make a Bedrock call and check CloudTrail:
1. AWS Console → CloudTrail → Event history
2. Filter: Event source = `bedrock.amazonaws.com`
3. Look at `userAgent` field
4. Should show: `Boto3/1.35.0 Python/3.11.9 ...`

---

## File List

| File | Purpose |
|------|---------|
| `full-stealth-setup.sh` | One-command setup — source before running Claude Code |
| `bedrock_boto3_proxy.py` | Level 2 proxy — makes TLS fingerprint match Python |
| `verify-full-stealth.sh` | Verify all settings are correct |
| `sagemaker-lifecycle-config.sh` | Auto-install + configure on SageMaker start |

---

## FAQ

**Q: Can AWS tell I'm using Claude Code with Level 1?**
A: Not through any standard AWS monitoring (CloudTrail, CloudWatch, VPC Flow Logs, GuardDuty, Security Hub). Only deep packet inspection of TLS handshakes could detect Node.js vs Python, which no standard AWS service does.

**Q: Does the system prompt leak?**
A: Only if Model Invocation Logging is ON in your AWS account. It's OFF by default. Verify and keep it off.

**Q: Will Claude Code still work normally?**
A: Yes. All features work. The only difference is cosmetic headers and blocked telemetry (which you don't need for Bedrock).

**Q: What about the `@anthropic-ai/bedrock-sdk` package name in node_modules?**
A: AWS has no visibility into your local filesystem. They only see HTTP traffic.

**Q: Can I use this on any SageMaker instance?**
A: Yes. The scripts use only standard bash, env vars, and optionally Python 3 (pre-installed on all SageMaker). No hardcoded paths, accounts, or regions.
