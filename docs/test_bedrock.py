#!/usr/bin/env python3
"""
Bedrock Model Access Verification Script

Run this to test if your AWS credentials and Bedrock access are configured correctly.

Usage:
    python test_bedrock.py
    python test_bedrock.py --region us-east-1
"""

import boto3
import json
import sys


def test_aws_identity():
    """Test AWS credentials by calling STS."""
    print("=" * 60)
    print("STEP 1: Verifying AWS Credentials")
    print("=" * 60)

    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()

        print(f"  ✓ Credentials valid")
        print(f"    Account:  {identity['Account']}")
        print(f"    User ARN: {identity['Arn']}")
        return True

    except Exception as e:
        print(f"  ✗ Credentials invalid: {e}")
        print("\n  To fix:")
        print("    aws configure")
        print("    # Enter your Access Key ID and Secret Access Key")
        return False


def test_bedrock_access(region: str = "ap-southeast-2"):
    """Test Bedrock model access."""
    print("\n" + "=" * 60)
    print(f"STEP 2: Testing Bedrock Models (region: {region})")
    print("=" * 60)

    runtime = boto3.client("bedrock-runtime", region_name=region)

    # Claude models to test
    models = [
        ("anthropic.claude-3-5-sonnet-20241022-v2:0", "Claude 3.5 Sonnet v2"),
        ("anthropic.claude-3-5-sonnet-20240620-v1:0", "Claude 3.5 Sonnet"),
        ("anthropic.claude-3-sonnet-20240229-v1:0", "Claude 3 Sonnet"),
        ("anthropic.claude-3-haiku-20240307-v1:0", "Claude 3 Haiku"),
    ]

    available = []
    unavailable = []

    for model_id, display_name in models:
        try:
            response = runtime.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                }),
                contentType="application/json"
            )

            # Parse to confirm success
            json.loads(response["body"].read())
            available.append((model_id, display_name))
            print(f"  ✓ {display_name}")

        except Exception as e:
            error_msg = str(e)

            if "AccessDeniedException" in error_msg:
                status = "Not enabled in Bedrock console"
            elif "ThrottlingException" in error_msg:
                status = "Rate limited (quota exceeded)"
                # Throttling means it IS accessible, just over quota
                available.append((model_id, display_name))
                print(f"  ✓ {display_name} (rate limited but accessible)")
                continue
            elif "ValidationException" in error_msg:
                status = f"Not available in {region}"
            else:
                status = error_msg[:80]

            unavailable.append((model_id, display_name, status))
            print(f"  ✗ {display_name}: {status}")

    return available, unavailable


def print_summary(available, unavailable):
    """Print summary and recommendations."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if available:
        print(f"\n✓ {len(available)} model(s) available:")
        for model_id, name in available:
            print(f"    - {name}")
        print(f"\n  Recommended model: {available[0][0]}")

    if unavailable:
        print(f"\n✗ {len(unavailable)} model(s) unavailable:")
        for model_id, name, reason in unavailable:
            print(f"    - {name}: {reason}")

    if not available:
        print("\n" + "-" * 60)
        print("TO ENABLE BEDROCK MODELS:")
        print("-" * 60)
        print("1. Go to AWS Console → Amazon Bedrock")
        print("2. Click 'Model access' in left sidebar")
        print("3. Click 'Manage model access'")
        print("4. Enable Claude models (Anthropic section)")
        print("5. Click 'Save changes'")
        print("6. Wait for 'Access granted' status")
        print("7. Re-run this script")


def main():
    # Parse region argument
    region = "ap-southeast-2"
    if len(sys.argv) > 1:
        if sys.argv[1] == "--region" and len(sys.argv) > 2:
            region = sys.argv[2]
        elif sys.argv[1].startswith("--region="):
            region = sys.argv[1].split("=")[1]
        elif sys.argv[1] in ["--help", "-h"]:
            print(__doc__)
            sys.exit(0)

    print("\nBedrock Access Verification")
    print("Region:", region)
    print()

    # Test credentials
    if not test_aws_identity():
        sys.exit(1)

    # Test Bedrock
    available, unavailable = test_bedrock_access(region)

    # Summary
    print_summary(available, unavailable)

    # Exit code
    sys.exit(0 if available else 1)


if __name__ == "__main__":
    main()
