# AWS Setup & Verification Guide

This document shows how to configure AWS credentials and verify Bedrock access.

---

## Step 1: Configure AWS Credentials

### Option A: Using AWS CLI commands
```bash
# Set credentials directly
aws configure set aws_access_key_id YOUR_ACCESS_KEY_ID
aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY
aws configure set region ap-southeast-2
aws configure set output json
```

### Option B: Interactive configuration
```bash
aws configure
# Prompts for:
#   AWS Access Key ID: YOUR_ACCESS_KEY_ID
#   AWS Secret Access Key: YOUR_SECRET_ACCESS_KEY
#   Default region name: ap-southeast-2
#   Default output format: json
```

### Where to get credentials:
1. Go to AWS Console → IAM → Users → Your User
2. Click "Security credentials" tab
3. Click "Create access key"
4. Select "Command Line Interface (CLI)"
5. Copy both keys (secret shown only once!)

---

## Step 2: Verify AWS Identity

```bash
aws sts get-caller-identity
```

**Expected output:**
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/youruser"
}
```

**If you see an error:**
- `InvalidClientTokenId` → Credentials are wrong or expired
- `SignatureDoesNotMatch` → Secret key is wrong
- `AccessDenied` → IAM permissions issue

---

## Step 3: Check Required IAM Permissions

Your IAM user/role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        }
    ]
}
```

Or use managed policy: `AmazonBedrockFullAccess`

---

## Step 4: Test Bedrock Model Access

### Python verification script:

```python
import boto3
import json

def test_bedrock_access(region: str = "ap-southeast-2"):
    """
    Test Bedrock model access and return results.
    """
    runtime = boto3.client("bedrock-runtime", region_name=region)

    # Claude models to test (newest first)
    models = [
        ("anthropic.claude-3-5-sonnet-20241022-v2:0", "Claude 3.5 Sonnet v2"),
        ("anthropic.claude-3-5-sonnet-20240620-v1:0", "Claude 3.5 Sonnet"),
        ("anthropic.claude-3-sonnet-20240229-v1:0", "Claude 3 Sonnet"),
        ("anthropic.claude-3-haiku-20240307-v1:0", "Claude 3 Haiku"),
    ]

    results = {
        "region": region,
        "available": [],
        "unavailable": [],
        "recommended": None
    }

    print(f"Testing Bedrock models in region: {region}\n")

    for model_id, display_name in models:
        try:
            # Test with minimal tokens
            response = runtime.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                }),
                contentType="application/json"
            )

            # Parse response to confirm it worked
            result = json.loads(response["body"].read())

            results["available"].append({
                "id": model_id,
                "name": display_name,
                "status": "OK"
            })
            print(f"  ✓ {display_name}: Available")

            # Set first available as recommended
            if results["recommended"] is None:
                results["recommended"] = model_id

        except Exception as e:
            error_msg = str(e)
            status = "Unknown error"

            if "AccessDeniedException" in error_msg:
                status = "Not enabled - enable in Bedrock console"
            elif "ValidationException" in error_msg:
                status = f"Not available in {region}"
            elif "ThrottlingException" in error_msg:
                status = "Rate limited - quota exceeded"
            elif "ResourceNotFoundException" in error_msg:
                status = "Model not found in region"
            else:
                status = error_msg[:100]

            results["unavailable"].append({
                "id": model_id,
                "name": display_name,
                "error": status
            })
            print(f"  ✗ {display_name}: {status}")

    return results


if __name__ == "__main__":
    results = test_bedrock_access()

    print("\n" + "="*50)
    if results["available"]:
        print(f"✓ {len(results['available'])} model(s) available")
        print(f"  Recommended: {results['recommended']}")
    else:
        print("✗ No models available")
        print("\nTo enable models:")
        print("  1. Go to AWS Console → Amazon Bedrock")
        print("  2. Click 'Model access' in left sidebar")
        print("  3. Click 'Manage model access'")
        print("  4. Enable Claude models (Anthropic)")
        print("  5. Click 'Save changes'")
```

### Run the test:
```bash
cd sagemaker-coding-agent
python -c "exec(open('docs/test_bedrock.py').read())"
```

---

## Step 5: Enable Bedrock Models (if needed)

If you see "Not enabled" errors:

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Select your region (e.g., `ap-southeast-2` Sydney)
3. Click **"Model access"** in left sidebar
4. Click **"Manage model access"**
5. Find **Anthropic** section
6. Enable these models:
   - Claude 3.5 Sonnet (recommended)
   - Claude 3 Haiku (fast/cheap)
7. Click **"Save changes"**
8. Wait for status to show "Access granted"

---

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `InvalidClientTokenId` | Credentials expired/invalid | Create new access key in IAM |
| `AccessDeniedException` | Model not enabled | Enable in Bedrock console |
| `ThrottlingException` | Rate limit exceeded | Wait or request quota increase |
| `ValidationException` | Model not in region | Try different region |
| `ResourceNotFoundException` | Model ID wrong | Check model ID spelling |

---

## Quota Limits

Default Bedrock quotas (may vary):
- Tokens per minute: 100,000
- Tokens per day: 1,000,000
- Requests per minute: 60

To request increase:
1. Go to AWS Console → Service Quotas
2. Search "Amazon Bedrock"
3. Select the quota to increase
4. Click "Request quota increase"

---

## Verification Checklist

- [ ] AWS CLI installed (`aws --version`)
- [ ] Credentials configured (`aws configure list`)
- [ ] Identity verified (`aws sts get-caller-identity`)
- [ ] Bedrock permissions in IAM policy
- [ ] Claude models enabled in Bedrock console
- [ ] Test script passes

---

## File Locations

| File | Purpose |
|------|---------|
| `~/.aws/credentials` | Access keys (Linux/Mac) |
| `~/.aws/config` | Region settings (Linux/Mac) |
| `%USERPROFILE%\.aws\credentials` | Access keys (Windows) |
| `%USERPROFILE%\.aws\config` | Region settings (Windows) |
