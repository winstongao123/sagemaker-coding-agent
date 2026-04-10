---
name: coding-standards
description: Language-agnostic coding quality standards for naming, error handling, design patterns, and testing
triggers: coding standards, naming convention, best practices, code style, design pattern, kiss, dry, yagni
---

# Coding Standards

Apply these standards to all code you write or review.

## Core Principles

1. **KISS** — Keep It Simple. Choose the simplest solution that works correctly.
2. **DRY** — Don't Repeat Yourself. Extract shared logic into reusable functions.
3. **YAGNI** — You Aren't Gonna Need It. Don't build for hypothetical future requirements.
4. **Readability First** — Code is read 10x more than it's written. Optimize for reading.

## Naming Conventions

### Variables
- Use descriptive names. `user_count` not `n`. `is_active` not `flag`.
- Booleans: prefix with `is_`, `has_`, `can_`, `should_`.
- Collections: use plural nouns. `users`, `order_items`, `error_messages`.
- Constants: `UPPER_SNAKE_CASE`. `MAX_RETRIES`, `DEFAULT_TIMEOUT`.

### Functions
- Use verb-noun pattern: `get_user()`, `validate_input()`, `calculate_total()`.
- Return value implied by name: `is_valid()` returns bool, `get_user()` returns user or None.
- Avoid generic names: not `process()`, `handle()`, `do_thing()`.

### Classes
- Use `PascalCase` nouns: `UserManager`, `PaymentProcessor`, `DatabaseConnection`.
- Interface/protocol names describe capability: `Serializable`, `Cacheable`, `Iterable`.

## Function Design

- **Single Responsibility**: Each function does ONE thing.
- **Max 50 lines**: If longer, split into subfunctions.
- **Max 4 parameters**: If more, use a config object/dataclass.
- **Max 4 levels nesting**: If deeper, extract inner logic or use early returns.
- **Early returns**: Handle error cases first, then the happy path.

```python
# BAD: deep nesting
def process(data):
    if data:
        if data.is_valid():
            if data.has_permission():
                return do_work(data)
            else:
                raise PermissionError()
        else:
            raise ValueError()
    else:
        raise TypeError()

# GOOD: early returns
def process(data):
    if not data:
        raise TypeError("data is required")
    if not data.is_valid():
        raise ValueError("invalid data")
    if not data.has_permission():
        raise PermissionError("access denied")
    return do_work(data)
```

## Error Handling

- **Be specific**: Catch specific exceptions, not bare `except:`.
- **Don't swallow errors**: Log or re-raise, never pass silently.
- **Fail fast**: Validate inputs at function entry, not deep inside logic.
- **Error messages**: Include what happened, why, and how to fix it.

```python
# BAD
try:
    result = api.call(data)
except:
    pass

# GOOD
try:
    result = api.call(data)
except ConnectionError as e:
    logger.warning(f"API unreachable: {e}. Retrying in 5s.")
    result = retry_with_backoff(api.call, data)
except ValidationError as e:
    raise ValueError(f"Invalid input for API: {e}") from e
```

## Immutability

- Prefer returning new objects over mutating existing ones.
- Use `tuple` over `list` for fixed collections.
- Use `frozenset` over `set` for fixed sets.
- Use `copy()` or `deepcopy()` when you must pass mutable data.

## Comments and Documentation

- **Explain WHY, not WHAT**: The code shows what, comments explain why.
- **Don't comment obvious code**: `i += 1  # increment i` is noise.
- **Docstrings for public APIs**: Include parameters, returns, raises, and a brief example.
- **TODO format**: `# TODO(author): description — ticket/issue link`

## File Organization

- **One concept per file**: Don't mix unrelated classes/functions.
- **Group by feature, not by type**: `auth/login.py` not `controllers/auth_controller.py`.
- **Keep files under 500 lines**: Split if larger.
- **Imports at top**: Standard library, then third-party, then local.

## Testing Standards

### Structure: Arrange-Act-Assert (AAA)
```python
def test_calculate_discount():
    # Arrange
    order = Order(total=100, customer_tier="gold")

    # Act
    discount = calculate_discount(order)

    # Assert
    assert discount == 15.0
```

### Test Naming
- Use descriptive names: `test_login_fails_with_expired_token`
- NOT: `test_login_1`, `test_case_a`

### Coverage Targets
- **Critical paths**: 80% minimum (auth, payments, data processing)
- **Utilities/helpers**: 90%+ (small, pure functions)
- **UI/display code**: 50%+ (harder to test, lower priority)

### Edge Cases to Always Test
- Empty/null input
- Boundary values (0, -1, MAX_INT)
- Duplicate entries
- Concurrent access (if applicable)
- Error paths and recovery

## Code Smells — Fix These

| Smell | Threshold | Fix |
|-------|-----------|-----|
| Long function | >50 lines | Split into subfunctions |
| Deep nesting | >4 levels | Early returns, extract methods |
| Magic numbers | Any | Named constants |
| God class | >500 lines | Split by responsibility |
| Long parameter list | >4 params | Config object/dataclass |
| Duplicate code | >3 occurrences | Extract to shared function |
| Dead code | Any | Delete it (git has history) |
