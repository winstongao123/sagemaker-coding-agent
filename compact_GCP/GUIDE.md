# Vertex AI Gemini Coding Agent

GCP version of the compact coding agent.

## Files
- `gemini_agent.py` - Agent code + UI
- `chat.ipynb` - Launch notebook

## Setup
```bash
pip install google-cloud-aiplatform ipywidgets
gcloud auth application-default login
```

## Usage
1. Open `chat.ipynb` in VS Code/Jupyter
2. Run all cells
3. Chat with the agent

## Features
- 15 tools (file ops, bash, python, search)
- Session management
- Dark mode UI
- Approval workflow for write operations
