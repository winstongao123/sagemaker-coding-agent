---
name: code-review
description: Conduct a thorough code review checking security, quality, performance, architecture, and testing
---

# Code Review Skill

When reviewing code, analyze all changed files systematically using this checklist.

## 1. Security (CRITICAL — must fix before merge)

- [ ] No hardcoded secrets (API keys, passwords, tokens, connection strings)
- [ ] No SQL injection (string concatenation in queries → use parameterized queries)
- [ ] No command injection (unsanitized input passed to shell commands)
- [ ] No XSS vulnerabilities (unescaped user input rendered in HTML)
- [ ] Input validation on all user-facing endpoints
- [ ] No path traversal risks (user-controlled file paths → validate and sanitize)
- [ ] Authentication and authorization checks present on protected routes
- [ ] Sensitive data not logged or exposed in error messages
- [ ] Dependencies checked for known vulnerabilities

## 2. Code Quality (HIGH — should fix)

- [ ] Functions are focused and do one thing well (<50 lines)
- [ ] No unnecessary complexity or over-engineering
- [ ] Nesting depth <4 levels (use early returns to simplify)
- [ ] Error handling is specific (not bare `except:`, not swallowed)
- [ ] Variable and function names are clear and descriptive
- [ ] No dead code, unused imports, or commented-out blocks
- [ ] No debug statements left (print(), console.log, pdb, debugger)
- [ ] No duplicated logic (DRY violations — extract to shared function)
- [ ] Consistent code style with surrounding codebase
- [ ] Magic numbers replaced with named constants

## 3. Performance (MEDIUM — consider fixing)

- [ ] No N+1 queries or unnecessary database/API calls
- [ ] No O(n^2) algorithms where O(n log n) or O(n) is possible
- [ ] Expensive operations cached or memoized
- [ ] No unnecessary memory allocation or deep copies
- [ ] Large collections processed lazily (generators, iterators) where appropriate
- [ ] Database queries select only needed columns/fields

## 4. Architecture (MEDIUM — consider fixing)

- [ ] Separation of concerns (business logic not mixed with I/O or UI)
- [ ] New code follows existing patterns and conventions
- [ ] No circular dependencies introduced
- [ ] Configuration externalized (not hardcoded paths, URLs, or values)

## 5. Testing (MEDIUM — should fix for critical paths)

- [ ] Critical paths have test coverage (auth, payments, data processing)
- [ ] Edge cases handled (empty input, null, boundaries, duplicates)
- [ ] Tests test behavior, not implementation details
- [ ] Tests are independent (no shared mutable state between tests)
- [ ] Error paths tested (what happens when things fail?)

## Output Format

### 1. Summary
One paragraph overview of overall code quality and readiness.

### 2. Issues Found
List each issue with severity and location:
- **[CRITICAL]** `file.py:42` — Description of the security/correctness issue
- **[HIGH]** `file.py:87` — Description of the quality issue
- **[MEDIUM]** `file.py:123` — Description of the improvement
- **[LOW]** `file.py:156` — Minor style or readability note

### 3. Positive Observations
Note what was done well (good patterns, clean abstractions, thorough error handling).

### 4. Suggestions
Non-blocking improvements for future consideration.

### 5. Rating
**X/10** — with brief justification. Criteria:
- 9-10: Production-ready, well-tested, no issues
- 7-8: Good quality, minor issues only
- 5-6: Functional but needs improvements before production
- 3-4: Significant issues that must be addressed
- 1-2: Major security or correctness problems
