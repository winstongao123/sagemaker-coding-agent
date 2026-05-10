# Prompt 2: Component 1 — End-to-End Claims Validation

> **Pre-requisite**: Read `00_CONTEXT.md` and `output/01_discovery.md` first.
> **Output file**: `output/02_component1.md`
> **Estimated turns**: 20-25
> **Expected output**: ~3000-4000 words, 10 sections

## EXECUTION STRATEGY
- Use `review` sub-agents for bug validation: spawn one per bug with specific instructions.
- Use `explore` sub-agents to find Document Extraction files (Phase 1 code).
- **CRITICAL**: After each section, IMMEDIATELY append to `output/02_component1.md`.
- **Append method**: See `00_CONTEXT.md` "APPEND METHOD" section. Use `write_file` with `mode: "append"`.
- **For files >500 lines**: Read in chunks using the `offset` parameter (e.g., offset=0 limit=500, then offset=500 limit=500). Do NOT try to read the whole file at once — `smart_truncate` will drop the middle.
- **Reference findings by `file:function`** (not line numbers — these shift between versions).

---

## VALIDATION MODE

**If `reference/end_to_end_review.md` exists in the workspace:**
This prompt operates in VALIDATION MODE. For each section:
1. State what the existing review says about this topic
2. Confirm or flag discrepancies based on your code reading
3. Add NEW findings not covered in the review
4. Tag each finding: `[confirmed from review]`, `[contradicts review — actual: X]`, or `[new finding]`

**If the reference file does NOT exist:** Proceed normally — discover everything from code.

---

## PS_ FILE RULE
You will see `PS_*.md` files in Component 1 folders. **Skip them** — they are already synthesized into the End-to-End Review. List them if encountered but do not read them (see `00_CONTEXT.md`).

---

## Tasks

### 2.0 Check for Existing Review (FIRST ACTION)
Attempt to read `reference/end_to_end_review.md`. If it exists and is non-empty, engage **VALIDATION MODE** (see above). If it does not exist or returns an error, proceed in normal discovery mode.

**Write a one-line note to the output file:** either "VALIDATION MODE: end_to_end_review.md loaded" or "DISCOVERY MODE: no reference review found."

### 2.1 Confirm Known Files Exist
Check each file from the known list. For each:
- Does it exist? At what path?
- Line count
- Key functions/classes (list names only)

Known files: `func_check_executor.py`, `func_pipeline_exec.py`, `checks_main.py`, `checks_all_combined.py`, `checks_baseline_policy_defination.py`, `checks_baseline_eligibility.py`, `func_generate_report.py`

Flag any unexpected files or files that have changed.
**Write to output file now**

### 2.2 Validate All 9 Bugs
For EACH bug (BUG-001 through BUG-009):

**Spawn a `review` sub-agent** with a self-contained instruction. Example for BUG-001:

> "Read the file `[ACTUAL_PATH]/func_check_executor.py`. Find the function `load_sources_from_s3`. Check if S3 errors are caught properly or returned as strings without raising exceptions. Report:
> 1. File path and function name
> 2. The problematic code pattern (describe it, 5-10 lines context)
> 3. CONFIRMED or NOT CONFIRMED
> 4. If confirmed: what goes wrong in a real claim assessment?
> 5. If not confirmed: explain why the bug description is wrong"

**Important**: Replace `[ACTUAL_PATH]` with the real path from `output/01_discovery.md`. Never send a sub-agent a placeholder path.

**Efficiency tip**: Batch bugs by file to save turns. Bugs in the same file can share one sub-agent:
- `func_check_executor.py`: BUG-001, BUG-002, BUG-003, BUG-008 (4 bugs, 1 sub-agent)
- `checks_baseline_policy_defination.py`: BUG-007, BUG-009 (2 bugs, 1 sub-agent)
- `checks_baseline_eligibility.py`: BUG-006 (1 bug, 1 sub-agent)
- `checks_main.py`: BUG-005 (1 bug, 1 sub-agent)
- `func_generate_report.py`: BUG-004 (1 bug, 1 sub-agent)
This uses 5 sub-agents instead of 9, saving ~4 main-agent turns.

Collect all 9 results into a table:

| Bug ID | Severity | Confirmed? | File:Function | Actual Impact | Notes |
|--------|----------|-----------|---------------|---------------|-------|

Tag each: `[verified]`
**Write to output file now**

### 2.3 Find Document Extraction Code (Phase 1)
The previous review did NOT list these files. Search for:
- Textract integration code: grep for `textract`, `start_document_text_detection`, `get_document_text_detection`, `start_document_analysis`
- Claude extraction prompts: grep for `extract`, `invoke_model`, `invoke_endpoint`
- Quality validation code: grep for `confidence`, `quality`, `validation`, `two-tier`
- Any code that reads source documents (ClaimForm, Bancs, TDR, AppForm, etc.)

**Fallback if grep returns nothing**: Try `glob("**/*extract*")`, `glob("**/*textract*")`, `glob("**/*ocr*")`, `glob("**/*document*")`

For each found file:
- Path, line count, key functions
- What it does (2-3 sentences)
- Any issues spotted

**Write to output file now**

### 2.4 Extract CHECK_REGISTRY
Find the complete CHECK_REGISTRY dictionary (or equivalent). Search for:
- `CHECK_REGISTRY` (exact name)
- `check_registry`
- Any dictionary mapping check IDs (C001, C002, etc.) to functions

Extract:
- Every check ID (C001, C002, etc.)
- Function name
- Description
- Which pipeline(s) it belongs to

Present as table. Note any checks that seem incomplete or have logic issues.
**Write to output file now**

### 2.5 Pipeline Configurations
Find ALL pipeline configs:
- `baseline_only`
- `tpd_retail_express`
- `tpd_group_express`
- Any others?

Search: grep for `pipeline`, `PIPELINE`, `pipe_config`, `check_list`

For each: which checks are included, in what order, any special config.
**Write to output file now**

### 2.6 Report Generation
Read `func_generate_report.py`:
- PDF generation: what library? what data included? formatting?
- Excel generation: what library? what sheets/columns?
- Any issues with data extraction or formatting?

**Write to output file now**

### 2.7 Invocation Method
How is the assessment invoked?
- Notebook cell? Script? Lambda? API?
- What parameters does it take?
- How would Component 2 call it?
**Write to output file now**

### 2.8 Test Evidence
Search for:
- Test .py files (pytest, unittest)
- Test notebooks (.ipynb) — search for case IDs: C-2024-333837, C-2025-342532
- Output artifacts (.xlsx, .pdf, .csv, .json, log files)
- Any saved results or metrics

For any found artifacts, check if they verify the claimed metrics:
- Processing time: 95.2s — `[verified]` or `[assumed from context]`?
- Tokens: 472K — `[verified]` or `[assumed from context]`?
- Cost: $1.73 — `[verified]` or `[assumed from context]`?
- S3 calls: 74 (62 redundant) — `[verified]` or `[assumed from context]`?

**Write to output file now**

### 2.9 Batch Processing Assessment
Assess Component 1's readiness for batch processing:
- Can multiple claims be processed in parallel? Any shared state that prevents this?
- Is there a queue/job mechanism, or is it purely synchronous?
- What would need to change for batch processing? (e.g., file path parameterisation, state isolation, result aggregation)
- Tag findings as `[verified]` based on code reading.

**Write to output file now**

### 2.10 NEW Bugs
Flag any issues you find that are NOT in the 9 known bugs:
- Error handling gaps
- Logic errors in checks
- PII exposure in prompts (see PII patterns in 00_CONTEXT.md)
- Hardcoded values that break portability
- Race conditions, missing null checks, etc.

For each new bug, provide: File:Function, Description, Severity (CRITICAL/HIGH/MEDIUM/LOW), Business Impact.
**Write to output file now**

## Output Format
Your `output/02_component1.md` should have:
1. File Confirmation Table
2. Bug Validation Table (9 bugs)
3. Document Extraction Code (Phase 1) findings
4. CHECK_REGISTRY (full table)
5. Pipeline Configurations
6. Report Generation Review
7. Invocation Method
8. Test Evidence
9. Batch Processing Assessment
10. New Bugs Found
