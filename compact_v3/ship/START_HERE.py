"""
SageAgent V3.2.3 — Quick Start
Run this in a SageMaker notebook cell:

    %run START_HERE.py

Or paste the lines below directly into a cell.
"""

# Step 1: Install dependencies (first time only)
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
    "boto3", "ipywidgets", "python-docx", "pandas", "openpyxl",
    "matplotlib", "reportlab", "Pillow"])

# Step 2: Configure (edit these if needed)
import sagemaker_agent
sagemaker_agent.CONFIG.model_id = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
sagemaker_agent.CONFIG.region = "ap-southeast-2"
sagemaker_agent.CONFIG.aws_bedrock_only = True        # Block all AWS except Bedrock
sagemaker_agent.CONFIG.require_tool_approval = True    # Show approve/deny dialog
sagemaker_agent.CONFIG.session_cost_limit = 1.0        # Max $1.00 per session

# Step 3: Launch
sagemaker_agent.create_chat_ui()
