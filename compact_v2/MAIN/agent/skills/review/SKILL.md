---
name: code-review
description: Conduct a thorough code review following best practices
---

## Code Review Skill

When reviewing code, follow this checklist:

### Security
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] No SQL injection, XSS, or command injection vulnerabilities
- [ ] Proper authentication and authorization checks

### Code Quality
- [ ] Functions are focused and do one thing well
- [ ] No unnecessary complexity or over-engineering
- [ ] Error handling is appropriate (not too broad, not missing)
- [ ] Variable and function names are clear and descriptive

### Performance
- [ ] No N+1 queries or unnecessary database calls
- [ ] No memory leaks or unbounded growth
- [ ] Expensive operations are cached or optimized

### Testing
- [ ] Critical paths have test coverage
- [ ] Edge cases are handled
- [ ] Tests are maintainable and readable

### Output Format
Provide your review as:
1. **Summary**: One paragraph overview
2. **Issues**: Bulleted list with severity (Critical/High/Medium/Low)
3. **Suggestions**: Improvements that aren't bugs
4. **Rating**: X/10 with justification
