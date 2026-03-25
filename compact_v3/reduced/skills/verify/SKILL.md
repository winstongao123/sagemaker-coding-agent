---
name: verify
description: Run 6-phase verification (build, type, lint, test, security, diff) before committing or creating a PR
---

# Verification Loop

Run all 6 phases in order. Stop and fix if any CRITICAL phase fails.

## Phase 1: Build Check

Detect the project's build system and run it:

```
# Python
pip install -e . 2>&1 | tail -5
# OR: python setup.py check

# Node.js
npm run build 2>&1 | tail -20
# OR: pnpm build

# Rust
cargo build 2>&1 | tail -20

# Go
go build ./... 2>&1 | tail -20
```

If no build system exists, SKIP this phase and note it.
If build fails: **STOP. Fix build errors before continuing.**

## Phase 2: Type Check

```
# Python
mypy . 2>&1 | head -30
# OR: pyright . 2>&1 | head -30

# TypeScript
npx tsc --noEmit 2>&1 | head -30

# Go (built into compiler)
# Already checked in Phase 1
```

Report all type errors. Fix critical ones before continuing.

## Phase 3: Lint Check

```
# Python
ruff check . 2>&1 | head -30
# OR: flake8 . 2>&1 | head -30
# OR: pylint <package> 2>&1 | head -30

# JavaScript/TypeScript
npm run lint 2>&1 | head -30
# OR: npx eslint . 2>&1 | head -30

# Go
golangci-lint run 2>&1 | head -30
```

Report warnings and errors. Fix errors, note warnings.

## Phase 4: Test Suite

```
# Python
pytest --tb=short -q 2>&1 | tail -30
# With coverage:
pytest --cov=. --cov-report=term-missing --tb=short 2>&1 | tail -50

# Node.js
npm test 2>&1 | tail -30
# With coverage:
npm test -- --coverage 2>&1 | tail -50

# Rust
cargo test 2>&1 | tail -30

# Go
go test ./... 2>&1 | tail -30
```

Report: X/Y tests passed, Z% coverage (if available).
Target: 80% minimum coverage for critical paths.

## Phase 5: Security Scan

Search for common security issues in changed files:

```
# Hardcoded secrets
grep -rn "api_key\|secret\|password\|token\|sk-\|AKIA" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v node_modules | grep -v __pycache__ | head -10

# .env files that shouldn't be committed
git ls-files '*.env' '.env*' 2>/dev/null

# Debug/development artifacts
grep -rn "console\.log\|print(\|pdb\|debugger\|TODO\|FIXME\|HACK" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v node_modules | grep -v __pycache__ | head -10
```

Report any secrets or debug code found.

## Phase 6: Diff Review

```
# What changed
git diff --stat
git diff --name-only

# Full diff of changed files
git diff
```

Review each changed file for:
- Unintended changes
- Missing error handling on new code
- Edge cases not covered
- Consistency with existing patterns

## Output Format

After all phases, produce this report:

```
VERIFICATION REPORT
===================

Build:     [PASS/FAIL/SKIP]
Types:     [PASS/FAIL/SKIP] (X errors)
Lint:      [PASS/FAIL/SKIP] (X warnings, Y errors)
Tests:     [PASS/FAIL/SKIP] (X/Y passed, Z% coverage)
Security:  [PASS/FAIL] (X issues found)
Diff:      [X files changed, Y insertions, Z deletions]

Issues Found:
- [CRITICAL] ...
- [HIGH] ...
- [MEDIUM] ...

Ready for PR: [YES/NO]
```

If any CRITICAL issues exist, answer "NO" and list what must be fixed.
