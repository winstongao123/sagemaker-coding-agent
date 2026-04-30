# Prompt 3: Components 2 & 3 — Agentic Framework + UI Deep Dive

> **Pre-requisite**: Read `00_CONTEXT.md` and `output/01_discovery.md` first.
> **Output file**: `output/03_component2_3.md`
> **Estimated turns**: 20-25
> **Expected output**: ~3000-4000 words, 14 sections

## EXECUTION STRATEGY
- Use `general` sub-agents (NOT explore) for multi-file orchestration tracing — these tasks need 15+ turns to read multiple files and trace logic between them.
- Use `explore` sub-agents for targeted searches (agent IDs, SQL queries, tool definitions — single grep + report).
- **CRITICAL**: After each section, IMMEDIATELY append to `output/03_component2_3.md`.
- **Append method**: See `00_CONTEXT.md` "APPEND METHOD" section. Use `write_file` with `mode: "append"`.

**Why `general` sub-agents for orchestration**: Tracing agent flow requires reading 2-3 files, finding entry points, following function calls across files, and synthesizing a flow diagram. An `explore` agent (Haiku, 20 turns) cannot reason through this. A `general` agent (Sonnet, 25 turns) can read ~3 files and produce analysis.

---

## PS_ FILE INSTRUCTION
**Before starting section 3.1**, search for `PS_*.md` files in Component 2 and Component 3 folders:
```
glob("<component2_folder>/PS_*.md")
glob("<component3_folder>/PS_*.md")
```
(Replace with actual folder paths from `output/01_discovery.md`.)

If PS_ files exist, **read them now**. They contain Winston's working analysis of the agentic framework and UI. Use their findings as a starting point — validate and build on them. Tag findings sourced from PS_ files as `[from PS_ notes — verified]` or `[from PS_ notes — not yet verified]`.

**Write a brief summary of PS_ file contents to output file now** (before other sections).

---

## Tasks — COMPONENT 2: Agentic Framework

### 3.1 Agent Definitions
Find ALL agent definitions. Search for:
- Primary: `create_agent`, `invoke_agent`, `InlineAgentConfiguration`, `agent_instruction`
- Secondary: `supervisor`, `sub_agent`, `sub-agent`, `routing`, `orchestrat`
- Fallback: `bedrock`, `agent`, `boto3.*bedrock-agent`
- Also check: any JSON/YAML/dict that defines agent names, aliases, IDs

For EACH agent found:

| Agent Name | Role | File:Function | Model | Temperature | Tools/Action Groups | Key Instruction Summary (2-3 sentences) | Issues |
|-----------|------|---------------|-------|-------------|--------------------|-----------------------------------------|--------|

**Write to output file now**

### 3.2 Agent Orchestration Map
**Step 1**: Search for routing logic:
- grep for: `router`, `classifier`, `dispatcher`, `intent`, `route`, `classify`
- Also try: `if.*agent`, `switch`, `match`, `dispatch`
- Record file:function for each match.

**Step 2**: Spawn a `general` sub-agent with this instruction (fill in actual file paths from Step 1 and section 3.1 results):
> "Read these specific files: [FILE1_FULL_PATH], [FILE2_FULL_PATH], [FILE3_FULL_PATH]. Trace the complete flow from user input to agent response. For each step, record: file path, function name, what the code does, what decides the next step. Return a numbered list of steps."

**Step 3**: From the sub-agent's output, draw a text flow diagram using ASCII boxes:
```
┌───────────┐     ┌─────────────┐     ┌───────────┐
│ User Msg  │────>│ Supervisor  │────>│ Sub-Agent  │
│           │     │ (file:func) │     │ (file:func)│
└───────────┘     └─────────────┘     └───────────┘
```

**Write to output file now**

### 3.3 Tool/Action Group Definitions
Find ALL tool definitions (action groups in Bedrock terms):
- Search: `actionGroup`, `action_group`, `toolSpec`, `tool_definition`, `function_schema`
- Also check: `openapi`, `swagger`, `api_schema`
- Check for `.sql` files — these may define data access tools

For each tool:

| Tool Name | Description | Parameters | Return Type | File:Function | Used By Agent |
|-----------|-------------|-----------|-------------|---------------|--------------|

**Write to output file now**

### 3.4 Component 1 Integration
How does the Agentic Framework invoke the End-to-End Claims Process?
- Direct Python call? Lambda invoke? API Gateway?
- What parameters does it pass?
- How does it get results back?
- If NOT connected yet: what code exists for future integration? Any stubs or interfaces?
- What would the integration API contract look like? (input format, output format, error responses)

Tag: `[verified]` or `[assumed — C1 and C2 are not yet connected]`
**Write to output file now**

### 3.5 Data Access Methods
For EACH data source, find the access code:

| Data Source | Connection Method | File:Function | Credentials | Error Handling | Notes |
|------------|------------------|---------------|-------------|---------------|-------|
| Snowflake | ? | ? | Secrets Manager / hardcoded? | retry? catch? | |
| S3 | ? | ? | IAM role / hardcoded keys? | retry? catch? | |
| Bancs | ? | ? | ? | ? | May not exist in code |

**Write to output file now**

### 3.6 SQL Queries
Extract ALL SQL queries (Snowflake or other):
- Grep for: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE TABLE`
- Also check `.sql` files: `glob("**/*.sql")`
- Check for string concatenation in queries (SQL injection risk)

For each query:
- File:Function
- Full query text (or summary if very long)
- Purpose
- **SQL injection risk**: parameterised (`%s`, `?`, `:param`) = SAFE. String concatenation (`f"SELECT...{var}"`) = VULNERABLE.

**Write to output file now**

### 3.7 Session & Conversation Management
- How are conversations tracked? Session IDs?
- Is conversation history stored? Where?
- Multi-turn support?
- State management between agent calls?
- Any conversation persistence (database, S3, DynamoDB)?
**Write to output file now**

### 3.8 Hardcoded Values
Find ALL hardcoded:
- Agent IDs, alias IDs, ARNs
- Model IDs
- Bucket names, regions
- Snowflake credentials/connection strings
- Endpoints, URLs

| Value | Type | File:Function | Should Be |
|-------|------|---------------|-----------|

**Write to output file now**

### 3.9 Error Handling & Guardrails
- What happens when an agent call fails? (search: `except`, `error`, `fail`, `retry`)
- Any Bedrock Guardrails configured? (search: `guardrail`, `GuardrailConfiguration`)
- Any knowledge bases attached? (search: `knowledgeBase`, `knowledge_base`)
- Rate limit handling? Token limit handling?
**Write to output file now**

---

## Tasks — COMPONENT 3: UI Layer (Quick Scan Only)
> C3 is expected to be minimal/prototype. Spend no more than 3-4 turns total on C3. The goal is to **document what exists** so the roadmap knows what needs to be built.

### 3.10 UI Inventory & Quick Assessment
Do a single pass to answer ALL of the following:
- What UI files exist? (`glob("**/*.html")`, `glob("**/*.jsx")`, `glob("**/*.tsx")`, `glob("**/*.py")` in UI folder)
- What framework? (React, Streamlit, Flask, raw HTML, Copilot Studio config?)
- How does it connect to C2? (API Gateway? Direct `invoke_agent`? WebSocket?)
- Authentication method? (Cognito? SSO? None?)
- Any streaming/progress handling for the 10-12 min processing time?
- Any deployment config? (EC2 user data, Docker, Cognito pool config?)

Write a single concise section covering all the above. If C3 barely exists, say so — that's a valid finding for the roadmap.
**Write to output file now**

### 3.11 Deployment Architecture Assessment (Across All Components)
This covers the overall system, not just C3:
- **Batch vs real-time**: Is there any queue/async infrastructure? Or is everything synchronous?
- **Scale path**: What would need to change for 50/200/1000 claims per day?
- **Separation of concerns**: Are C1, C2, C3 independently deployable? Or tightly coupled?
- Reference the batch processing context from `00_CONTEXT.md`.

Tag: `[verified]` from code or `[assumed — architecture recommendation]`
**Write to output file now**

---

## Output Format
Your `output/03_component2_3.md` should have:
1. PS_ File Summary (if any found)
2. Agent Definitions Table
3. Orchestration Map (text diagram + step-by-step trace)
4. Tool/Action Group Table
5. Component 1 Integration Analysis
6. Data Access Methods Table
7. SQL Queries (with injection risk assessment)
8. Session Management
9. Hardcoded Values Table
10. Error Handling & Guardrails
11. UI Inventory & Quick Assessment (single section)
12. Deployment Architecture Assessment
