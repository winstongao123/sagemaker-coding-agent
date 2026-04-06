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
