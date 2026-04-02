# Prompt 1: Codebase Discovery & Inventory

> **Pre-requisite**: Read `00_CONTEXT.md` first.
> **Output file**: `output/01_discovery.md`
> **Estimated turns**: 15-20
> **Expected output**: ~2000-3000 words, 9 sections

## EXECUTION STRATEGY
- Use `explore` sub-agents for file discovery (e.g., "list all .py files in [actual_folder_path]")
- Use `bash` for git history commands
- **CRITICAL**: After completing each section below, IMMEDIATELY append findings to `output/01_discovery.md`. Do NOT hold everything in memory — compaction will destroy it.
- **Append method**: See `00_CONTEXT.md` "APPEND METHOD" section. First write creates the file (default mode). All subsequent writes use `mode: "append"`.

---

## PS_ FILE RULE
You will see `PS_*.md` files in ClaRA component folders. **List them in the file inventory** (section 1.2) but:
- Do NOT read Component 1 PS_ files (already synthesized into the End-to-End Review).
- Note Component 2 and 3 PS_ files for later prompts — they contain unreported analysis.

---

## COMPONENT MAPPING RULE
Some files may not obviously belong to one component. Use these rules:
- Files in the "end to end claim process" folder (or similar) → **C1**
- Files containing `create_agent`, `invoke_agent`, `InlineAgent`, `supervisor`, `sub_agent` → **C2**
- Files containing `streamlit`, `flask`, `react`, `cognito`, `.html`, `.jsx` → **C3**
- Files that serve multiple components → **SHARED**
- If unsure, label as `UNKNOWN — [reason]` and move on

---

## Tasks

### 1.1 File Tree
- Complete file/folder tree of the entire repository
- Map every file to its component: C1 (End-to-End Claims), C2 (Agentic Framework), C3 (UI), or SHARED
- Use actual folder names from the codebase (Component 1 folder = "end to end claim process", find C2 and C3 names)
- **Write to output file now**

### 1.2 File Inventory
List ALL files by type in a table:

| File | Component | Type | Purpose (1 sentence) |
|------|-----------|------|---------------------|

Types: .py, .ipynb, .json, .yaml, .env, .md, .png/.jpg/.drawio, .docx, .pdf, other
- Include PS_*.md files with note: "Working notes — C1 files skip, C2/C3 files read in later prompts"
- **Write to output file now**

### 1.3 Dependencies
- Find requirements.txt, pyproject.toml, setup.py — list contents
- If none exist: scan ALL .py files for `import` statements, list every unique external package
- Note version pins (or lack thereof)
- **If grep hits the 100-match cap warning**, break into per-component scans: `grep "import" component1/**/*.py`, then `component2/**/*.py`, etc.
- **Write to output file now**

### 1.4 Git History
Run these commands and capture output:
```
git log --oneline -20
git log --format="%an" | sort -u
git branch -a
cat .gitignore (if exists)
```
**If git is not initialised** (no `.git` folder), report: "No git repository found. Code is not under version control." and move on — do NOT fail.
- **Write to output file now**

### 1.5 AWS Resource Inventory
Grep across ALL files for:
- ARNs (`arn:aws:`)
- S3 buckets (`s3://` or bucket names)
- Region references (`ap-southeast-2` or other regions)
- Lambda function names
- API Gateway endpoints
- IAM role/policy names
- Secrets Manager secret names
- Bedrock model IDs
- Snowflake connection details (host, database, schema, warehouse)

**If grep hits the cap warning**, narrow by searching one component folder at a time.

Present as a table:

| Resource Type | Name/ARN | File:Function | Hardcoded? |
|--------------|----------|---------------|------------|

- **Write to output file now**

### 1.6 Configuration Audit
- Find ALL config files (.json, .yaml, .env, .cfg, .ini)
- For each: list all keys/values (redact actual secrets but note they exist)
- Find ALL hardcoded values that should be config: model IDs, bucket names, regions, endpoints
- **Write to output file now**

### 1.7 Architecture Diagrams
- Find any .png, .jpg, .drawio, .svg, .pdf files
- Read/view each image file to examine it (use the file reading tool, which supports image files)
- If `read_file` cannot render image content (returns binary data or an error), note the file path and file size only. Do not attempt to describe unreadable content.
- Describe what each readable diagram shows
- **Write to output file now**

### 1.8 Code Metrics
Calculate and record:
- Total lines of code (by language: .py, .ipynb code cells, other)
- Lines per component (C1, C2, C3)
- Number of functions/classes per component
- Largest files by line count (top 10)
- **Write to output file now**

### 1.9 Business Metrics Baseline
Search for and extract any existing performance/cost metrics:
- Grep for: `time`, `duration`, `elapsed`, `timer`, `cost`, `token`, `price`
- Grep for: `s3.*call`, `redundant`, `cache`, `throughput`, `cases.*hour`
- Find any benchmark results, timing logs, or cost calculations in notebooks or output files
- Record the baseline values for business case (context says: 95.2s, $1.73/case, 472K tokens, 38 cases/hr, 74 S3 calls)
- **Verify these numbers from code/artifacts — don't just repeat the context.** Tag each as `[verified]` or `[assumed from context]`.
- **Write to output file now**

## Output Format
Your `output/01_discovery.md` should have these sections:
1. File Tree (with component mapping)
2. File Inventory Table
3. Dependency List
4. Git History Summary
5. AWS Resource Inventory Table
6. Configuration Audit
7. Architecture Diagrams Found
8. Code Metrics
9. Business Metrics Baseline
