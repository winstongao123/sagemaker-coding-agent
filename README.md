# SageMaker Coding Agent

A secure AI coding assistant for AWS SageMaker and GCP, powered by Amazon Bedrock Claude or Google Vertex AI Gemini.

**Tested: 10/10 use cases pass on both AWS versions** (see [test results](#test-results))

---

## Three Versions Available

| Version | Platform | Model | Best For |
|---------|----------|-------|----------|
| **[compact/](compact/)** | AWS Bedrock | Claude 3.5 Sonnet | Quick setup, sharing |
| **[complete/](complete/)** | AWS Bedrock | Claude 3.5 Sonnet | Teams, development |
| **[compact_GCP/](compact_GCP/)** | GCP Vertex AI | Gemini 1.5 Pro | GCP/Colab users |

**AWS versions have IDENTICAL features and pass all tests. GCP version has 14 tools (no semantic_search).**

---

## Features

### 15 Tools
| Category | Tools |
|----------|-------|
| File Operations | `read_file`, `write_file`, `edit_file`, `glob`, `list_dir` |
| Search | `grep`, `semantic_search` (AI-powered) |
| Execution | `bash`, `python_exec` |
| Documents | `create_word`, `create_excel`, `create_markdown` |
| Other | `view_image`, `todo_write`, `todo_read` |

### Security
- **Workspace Boundary**: Cannot access files outside project
- **Secret Detection**: Warns about API keys, passwords
- **Command Filtering**: Blocks dangerous commands (`rm -rf`, etc.)
- **Audit Logging**: Records all actions with timestamps

### Model Parameters
- **Temperature**: 0.0 - 1.0 (creativity control)
- **Extended Thinking**: Enable deep reasoning mode
- **Thinking Budget**: 1024 - 16000 tokens for thinking

### Other Features
- **Sessions**: Save and resume conversations
- **Approval System**: Confirms before write operations
- **Context Warnings**: Alerts at 80/90/95% usage
- **Progress Visibility**: See tool calls and results in real-time

---

## Quick Start

### Option 1: AWS Compact (Recommended for First Use)

```bash
cd compact/
```

1. Open `chat.ipynb`
2. Run Cell 1 (install dependencies)
3. Run Cell 2 (configure model/region)
4. Run Cell 3 (start chatting!)

### Option 2: AWS Complete

```bash
cd complete/
```

1. Run `pip install -r requirements.txt`
2. Open `setup.ipynb` (check Bedrock access)
3. Open `agent.ipynb` (start chatting)

### Option 3: GCP Vertex AI (Gemini)

```bash
cd compact_GCP/
```

1. Set up GCP credentials:
   ```bash
   gcloud auth application-default login
   export GCP_PROJECT_ID="your-project-id"
   ```
2. Run `pip install -r requirements.txt`
3. Start in Jupyter/Colab:
   ```python
   from gcp_coding_agent import create_chat_ui
   create_chat_ui()
   ```

---

## Requirements

### AWS Versions
- AWS SageMaker or local Jupyter with AWS credentials
- Bedrock access with Claude models enabled
- Python 3.8+

### GCP Version
- GCP project with Vertex AI API enabled
- Application Default Credentials (ADC)
- Python 3.8+

---

## Documentation

Each version has its own `GUIDE.md` with:
- Beginner explanations of all concepts
- Complete architecture diagrams
- User interaction guide
- Security details
- Troubleshooting

---

## Test Results

Both versions pass all 10 comprehensive use cases with 5+ step flows:

| Test | Description | Compact | Complete |
|------|-------------|---------|----------|
| 1 | Explore codebase | PASS | PASS |
| 2 | Code analysis | PASS | PASS |
| 3 | Project setup with todos | PASS | PASS |
| 4 | Search and analyze | PASS | PASS |
| 5 | Bash operations | PASS | PASS |
| 6 | Python execution | PASS | PASS |
| 7 | Multi-file reading | PASS | PASS |
| 8 | Error handling | PASS | PASS |
| 9 | Security validation | PASS | PASS |
| 10 | Combined workflow | PASS | PASS |

Run tests: `python test_10_cases.py`

---

## Comparison with Anthropic Skills

| Feature | Anthropic Skills | This Agent |
|---------|-----------------|------------|
| Word (.docx) | Prompt-based skill | Direct `create_word` tool |
| Excel (.xlsx) | Prompt-based skill | Direct `create_excel` tool |
| PDF | Yes | Not yet (can add) |
| PowerPoint | Yes | Not yet (can add) |
| Infrastructure | Requires Claude Pro/Max | Self-contained (AWS Bedrock) |
| Deployment | Cloud-dependent | Works in SageMaker |

Our approach uses native Python libraries (python-docx, openpyxl) for direct document creation without external dependencies.

---

## AWS vs GCP Version Comparison

| Feature | AWS (Bedrock/Claude) | GCP (Vertex AI/Gemini) |
|---------|---------------------|------------------------|
| Model | Claude 3.5 Sonnet | Gemini 1.5 Pro |
| Context Window | 200K tokens | 2M tokens |
| Extended Thinking | Yes | Limited (2.0 exp only) |
| Semantic Search | Yes (Titan Embeddings) | Not included |
| Tools | 15 | 14 |
| Auth | IAM Role | ADC / Service Account |
| Best For | SageMaker users | Colab/GCP users |

---

## Based On

Inspired by [OpenCode](https://github.com/anthropics/anthropic-quickstarts) with adaptations for AWS Bedrock, GCP Vertex AI, and Jupyter.
