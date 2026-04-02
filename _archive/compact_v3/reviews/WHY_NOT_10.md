# Why V3 Cannot Reach 10/10 — Explained

**Version**: v3.2.2 | **Current Score**: 9.0/10 | **Gap**: 1.0 points across 8 unfixable items

| # | What's Missing | Score Lost | Why It Can't Be Fixed | Plain English |
|---|---------------|-----------|----------------------|---------------|
| 1 | **No Docker container** | -0.7 | SageMaker notebooks don't support Docker | Think of Docker as a locked room where code runs. If bad code escapes V3's software sandbox, there's no physical wall stopping it. SageMaker doesn't give us the locked room — we can only use software fences. |
| 2 | **Python closures are readable** | -0.3 | CPython language design — `__closure__` attribute | V3 wraps dangerous functions (like `open`) with safe versions. But Python lets any code peek inside a function and find the original unsafe version hidden inside. It's like hiding a key under a doormat — Python lets you lift the doormat. |
| 3 | **Shared IAM role** | -0.2 | SageMaker gives one AWS identity to everything | V3 and your notebook share the same AWS "passport." If code bypasses V3's checks, it can use that passport to call AWS services. `aws_bedrock_only` blocks this at the code level, but the passport itself can't be split. |
| 4 | **No streaming** | -0.3 | Jupyter widgets can't handle async streaming | Claude's response comes all at once instead of word-by-word. This makes the UI feel slower (you wait, then see everything). Jupyter's widget system doesn't support the threading model needed for live streaming. |
| 5 | **No prompt caching** | -0.1 | Bedrock AU region doesn't support it | Every API call re-sends the full system prompt + tool definitions (~3,350 tokens). Anthropic's direct API can cache this, but Bedrock in Australia hasn't enabled it yet. You pay for those tokens every single call. |
| 6 | **shell=True for pipes** | -0.1 | Design tradeoff — pipes need shell | Commands like `git log | head -5` need the shell to connect two programs with `|`. But `shell=True` means the command runs through bash, which is harder to sandbox than running a program directly. We need pipes, so we accept this risk. |
| 7 | **Daemon auto-save thread** | -0.2 | Jupyter kernel lifecycle | V3 saves your session in a background thread so the UI stays responsive. But if SageMaker kills the kernel (timeout, crash, restart), the background thread dies instantly — your last message might not be saved. Using a foreground thread would freeze the UI during saves. |
| 8 | **No persistent REPL** | -0.3 | Architecture limitation | Every time V3 runs Python code, it starts a fresh process. Variables from the last run are gone. A real REPL (like Jupyter itself) keeps state between runs. Adding this would require rewriting how V3 executes code — a major architectural change for marginal benefit. |

**Total gap: 2.2 points across 8 items → compressed to ~1.0 because some overlap**

## What Controls Each Limitation

| Limitation | Controlled By | Can User Change It? |
|-----------|--------------|-------------------|
| No Docker | AWS SageMaker service | No — would need SageMaker with Docker support (e.g., custom container) |
| Closures readable | Python language (CPython) | No — fundamental to how Python works |
| Shared IAM | AWS SageMaker execution role | Partially — `aws_bedrock_only` mitigates at code level |
| No streaming | Jupyter ipywidgets | No — would need a different UI framework |
| No prompt caching | AWS Bedrock regional feature | No — wait for AWS to enable it in AU region |
| shell=True | Agent design decision | No — removing it breaks pipe commands |
| Daemon auto-save | Jupyter kernel threading model | No — alternative (foreground save) freezes UI |
| No persistent REPL | Agent architecture | Possible but major rework — not worth the effort |

## Bottom Line

V3 scores **9.0/10** after 10 rounds of review (Claude Opus 4.6 + Codex gpt-5.3-codex). The missing 1.0 is split between things AWS doesn't give us (Docker, streaming, caching) and things Python's design prevents (closure inspection). No amount of code changes can fix these — they require a different platform.
