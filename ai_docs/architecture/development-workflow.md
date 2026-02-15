# Development Workflow

**READ THIS BEFORE IMPLEMENTING ANY FEATURE THAT INVOLVES FRONTEND-BACKEND COMMUNICATION**

---

## CONTRACT-FIRST Development (MANDATORY)

When implementing features that involve both frontend and backend, you MUST follow the CONTRACT-FIRST approach. This prevents the #1 source of bugs: frontend and backend not speaking the same language.

### The Problem We're Solving

Without a shared contract:
- Backend implements `first_name` + `last_name`, frontend sends `full_name`
- Backend expects JSON, frontend sends form-urlencoded
- Backend returns `{tokens: {...}}`, frontend expects `{access_token: ...}`
- Result: 422, 403, 500 errors that waste hours to debug

### The Solution: API Contract as Source of Truth

**BEFORE writing any code**, define the API contract in `/docs/api-contracts/`.

---

## Workflow for Frontend-Backend Features

### Step 1: Define the API Contract FIRST

Create a contract file BEFORE any implementation:

```
/docs/api-contracts/
  auth/
    register.md      # Registration endpoint contract
    login.md         # Login endpoint contract
  users/
    get-me.md        # Get current user contract
```

**Contract file template:**

```markdown
# POST /api/v1/auth/register

## Request

### Headers
- Content-Type: application/json

### Body
```json
{
  "full_name": "string (required) - Will be split into first_name/last_name",
  "email": "string (required) - Valid email format",
  "password": "string (required) - Min 8 chars, 1 uppercase, 1 number, 1 special",
  "organization_name": "string (required)"
}
```

## Response

### Success (201 Created)
```json
{
  "user": {
    "id": "string (ULID)",
    "email": "string",
    "first_name": "string",
    "last_name": "string"
  },
  "organization": {
    "id": "string (ULID)",
    "name": "string"
  },
  "tokens": {
    "access_token": "string (JWT)",
    "refresh_token": "string (JWT)",
    "token_type": "bearer"
  }
}
```

### Error Responses
| Status | Condition | Response |
|--------|-----------|----------|
| 409 | Email already exists | `{"detail": "User with email X already exists"}` |
| 422 | Weak password | `{"detail": "Password must contain..."}` |
| 422 | Missing field | `{"detail": [{"loc": [...], "msg": "..."}]}` |
```

### Step 2: Write Contract Tests BEFORE Implementation

**MANDATORY:** Write tests that verify the contract BEFORE implementing the feature.

Location: `tests/integration/{bc}_bc/test_frontend_{feature}_contract.py`

```python
"""Contract tests for {feature}.

These tests verify that backend accepts the EXACT payload format
that frontend will send, and returns the EXACT response format
that frontend expects.

CONTRACT: /docs/api-contracts/{feature}.md
"""

class TestFrontend{Feature}Contract:
    """Tests for frontend {feature} payload compatibility."""

    def test_{action}_with_frontend_payload_should_succeed(self, test_client):
        """
        Frontend sends THIS EXACT payload format.
        If this test fails, the frontend will break.

        DO NOT change this test without updating the frontend.
        DO NOT change the frontend without updating this test.
        """
        # Exact payload frontend sends
        frontend_payload = {
            "full_name": "Test User",
            "email": "test@example.com",
            # ...
        }

        response = test_client.post("/api/v1/...", json=frontend_payload)

        # Verify exact response structure frontend expects
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert "access_token" in data["tokens"]
```

### Step 3: Implement Backend

Implement the backend to satisfy the contract tests.

**Checklist:**
- [ ] All contract tests pass
- [ ] Error responses match contract (status codes + messages)
- [ ] Response structure matches contract exactly

### Step 4: Implement Frontend

Implement the frontend using the contract as reference.

**Checklist:**
- [ ] Request payload matches contract exactly
- [ ] Response handling matches contract structure
- [ ] Error handling covers all error responses in contract

### Step 5: Run Full Contract Test Suite

```bash
make test-contract
```

ALL contract tests MUST pass before merging.

---

## Contract Test Requirements

### What Contract Tests MUST Verify

1. **Request format**: Exact payload structure frontend sends
2. **Success response**: Exact structure frontend expects
3. **Error responses**: All error cases with correct status codes
4. **Headers**: Content-Type, Authorization format

### Contract Test Naming Convention

```
tests/integration/{bc}_bc/test_frontend_{feature}_contract.py
```

Examples:
- `test_frontend_register_contract.py`
- `test_frontend_login_contract.py`
- `test_frontend_assessment_contract.py`

### Contract Test Class Structure

```python
class TestFrontend{Feature}Contract:
    """Tests for frontend {feature} payload compatibility.

    CONTRACT: /docs/api-contracts/{feature}.md

    These tests are the source of truth for frontend-backend
    communication. If a test fails:
    1. Check if frontend changed (update test + backend)
    2. Check if backend changed (update test + frontend)
    3. NEVER silently fix one side without the other
    """
```

---

## Pre-Implementation Checklist

Before implementing ANY frontend-backend feature:

- [ ] API contract document created in `/docs/api-contracts/`
- [ ] Contract reviewed (request format, response format, error cases)
- [ ] Contract tests written and failing (TDD)
- [ ] Backend implemented, contract tests passing
- [ ] Frontend implemented using contract as reference
- [ ] `make test-contract` passes
- [ ] Manual E2E test performed

---

## When Modifying Existing APIs

If you need to change an existing API:

1. **Update contract document FIRST**
2. **Update contract tests** to reflect new behavior
3. **Run tests** - they should fail
4. **Update backend** - tests should pass
5. **Update frontend** - manual test should pass
6. **Run `make test-contract`** - all must pass

**NEVER:**
- Change backend without updating contract + tests
- Change frontend without verifying contract tests
- Assume "it will work" without running contract tests

---

## Common Mistakes to Avoid

### Mistake 1: Different Field Names
```
Backend: first_name, last_name
Frontend: full_name
```
**Solution:** Contract defines ONE format. Backend adapts if needed.

### Mistake 2: Different Content Types
```
Backend: expects application/json
Frontend: sends application/x-www-form-urlencoded
```
**Solution:** Contract specifies Content-Type. Backend supports what frontend sends.

### Mistake 3: Different Response Structures
```
Backend: {access_token: "..."}
Frontend expects: {tokens: {access_token: "..."}}
```
**Solution:** Contract defines exact structure. Both sides follow it.

### Mistake 4: Unhandled Error Cases
```
Backend: throws WeakPasswordException -> 500
Frontend: expects 422 with message
```
**Solution:** Contract lists ALL error cases. Backend catches ALL exceptions.

---

## Integration with CI/CD

```yaml
# In CI pipeline
- name: Run contract tests
  run: make test-contract

- name: Fail if contract tests fail
  if: failure()
  run: |
    echo "CONTRACT TESTS FAILED"
    echo "Frontend and backend are out of sync"
    exit 1
```

---

## Quick Reference

| Phase | Action | File Location |
|-------|--------|---------------|
| 1. Contract | Define API contract | `/docs/api-contracts/{feature}.md` |
| 2. Tests | Write contract tests | `tests/integration/{bc}_bc/test_frontend_{feature}_contract.py` |
| 3. Backend | Implement endpoint | `src/{bc}/adapters/http/api/.../routers/` |
| 4. Frontend | Implement UI | `web/app/src/...` |
| 5. Verify | Run contract tests | `make test-contract` |

---

**See also:**
- [Critical Rules](critical-rules.md) - Rule #0: Catch ALL exceptions
- [HTTP Layer](http-layer.md) - Error handling patterns
- [Frontend Coding Standards](frontend/CODING_STANDARDS.md) - API error handling
