---
name: security-review
description: 3-phase security vulnerability assessment with false-positive filtering and confidence scoring
---

# Security Review

Perform a focused security review of code changes. Signal quality over volume — a report with 2 real vulnerabilities is better than one with 10 false positives.

## Step 1: Repository Context Research

Before reviewing changes, understand the project's security posture:

1. Identify existing security frameworks and libraries in use
2. Look for established secure coding patterns (parameterized queries, input sanitization, auth middleware)
3. Examine existing validation and sanitization patterns
4. Understand the project's security model and threat model (from CLAUDE.md, README, or docs)

## Step 2: Comparative Analysis

Compare changed code against established patterns:

1. Compare new code against existing security patterns — does it follow them?
2. Identify deviations from established practices (new code that skips validation others use)
3. Look for inconsistent security implementations (auth on some routes but not others)
4. Flag code introducing new attack surfaces (new user-facing endpoints, file uploads, shell commands)

## Step 3: Vulnerability Assessment

Examine each modified file for security implications:

1. **Trace data flow** from user inputs to sensitive operations (DB, shell, file system, external APIs)
2. **Look for privilege boundaries** being crossed unsafely (user → admin, client → server trust)
3. **Identify injection points**: SQL injection, command injection, XSS, path traversal, SSRF
4. **Check authentication/authorization**: missing checks, bypassable checks, insecure session handling
5. **Check secrets handling**: hardcoded keys, tokens in logs, sensitive data in error messages

## Output Format

For each finding:

```
# Vuln N: [Type]: `file.py:42`

* Severity: HIGH | MEDIUM
* Confidence: 0.8-1.0
* Description: [Clear description of the vulnerability]
* Exploit Scenario: [Realistic attack path — not theoretical]
* Recommendation: [Specific fix with code example]
```

## Severity Guidelines

- **HIGH**: Directly exploitable — leads to RCE, data breach, auth bypass, or privilege escalation
- **MEDIUM**: Requires specific conditions but significant impact if exploited

Only report HIGH and MEDIUM findings. LOW findings waste reviewer time.

## Confidence Scoring

- **0.9-1.0**: Certain exploit path, can demonstrate it
- **0.8-0.9**: Clear vulnerability pattern with known exploitation methods
- **Below 0.8**: Do not report — too speculative

## Hard Exclusions (Do NOT Report)

These produce false positives and waste time:

1. DOS vulnerabilities or resource exhaustion
2. Secrets on disk (handled by separate tooling)
3. Rate limiting concerns
4. Memory/CPU exhaustion issues
5. Non-security-critical input validation without proven impact
6. Lack of hardening (not a concrete vulnerability)
7. Theoretical race conditions/timing attacks without concrete path
8. Outdated third-party library versions (handled by dependency scanning)
9. Memory safety issues in memory-safe languages (Python, Go, Rust)
10. Unit test files (not production code)
11. Log spoofing (outputting un-sanitized user input to logs)
12. SSRF controlling only path (not host/protocol)
13. Regex injection / Regex DOS
14. Insecure documentation examples

## Precedents

1. Logging high-value secrets is a vulnerability; logging URLs is safe
2. UUIDs can be assumed unguessable
3. Environment variables and CLI flags are trusted values
4. Resource management issues (memory/file descriptor leaks) are not security vulnerabilities
5. React and frameworks with auto-escaping are XSS-safe without special methods (except dangerouslySetInnerHTML)
6. Client-side permission checks are not vulnerabilities (server handles validation)
7. Command injection in shell scripts is generally not exploitable unless concrete untrusted input path exists

## Signal Quality Check

Before including a finding, answer ALL of these:

1. Is there a concrete, exploitable vulnerability with a clear attack path?
2. Does this represent real security risk vs theoretical best practice?
3. Are there specific code locations and reproduction steps?
4. Would a security team find this actionable?

If any answer is NO, do not include the finding.

## Final Report

```
SECURITY REVIEW REPORT
======================

Scope: [files/endpoints reviewed]
Findings: [N HIGH, M MEDIUM]

[Vulnerability details as above]

Overall Assessment: [One paragraph — is this code safe for production?]
```

If no findings meet the confidence threshold, report: "No actionable security vulnerabilities found in the reviewed changes."
