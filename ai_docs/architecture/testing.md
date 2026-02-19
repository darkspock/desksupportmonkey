# Testing Standards

## Overview

The project has two test suites that validate the system at different levels:

- **Unit tests** (`tests/unit/`) — Fast, isolated tests using `MagicMock`. Test individual handlers, commands, queries, and domain logic without a database.
- **Integration tests** (`tests/integration/`) — Full-stack tests hitting a real PostgreSQL database. Test the complete flow: HTTP endpoint → handler → repository → DB.

Both suites MUST pass before any implementation is considered complete.

## Running Tests

```bash
make test              # Unit tests only (tests/unit/)
make test-integration  # Integration tests only (requires Docker PostgreSQL)
make test-all          # Both suites together
```

Integration tests require Docker services running (`make start-docker`).

## Test Infrastructure

### Root conftest (`tests/conftest.py`)

Provides shared fixtures used by integration tests:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `create_test_database` | session | Creates `dsm_test` database if it doesn't exist |
| `test_engine` | session | SQLAlchemy engine bound to `dsm_test` |
| `tables` | session | Creates all tables at start, drops at teardown |
| `db_session` | function | Per-test session with transaction rollback isolation |
| `client` | function | FastAPI `TestClient` wired to test DB session |
| `auth_as` | function | Helper to authenticate as a given user |
| `company` | function | Creates a test company with email domains |
| `super_admin_user` | function | Super admin user (no company) |
| `admin_user` | function | Admin user in test company |
| `technician_user` | function | Technician user in test company |
| `employee_user` | function | Employee user in test company |
| `make_user` | function | Factory to create users with custom attributes |

### Transaction Rollback Pattern

Each integration test runs inside a database transaction that is rolled back after the test completes. This provides:

- **Isolation**: Each test starts with a clean state
- **Speed**: No need to recreate/truncate tables between tests
- **Correctness**: Handler `commit()` calls release savepoints (not real commits), and the outer transaction is rolled back

```python
@pytest.fixture()
def db_session(test_engine, tables):
    conn = test_engine.connect()
    trans = conn.begin()
    session = Session(bind=conn)
    session.begin_nested()  # savepoint

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session
    session.close()
    trans.rollback()  # rolls back everything
    conn.close()
```

### Auth Override

The `auth_as` fixture overrides FastAPI's `get_current_user` dependency, which also satisfies all `require_role()` checks:

```python
auth_as(admin_user)  # All subsequent requests authenticate as admin_user
```

### External Service Mocking

Integration tests mock external services to avoid side effects:

- **Email** — `@patch("core.email.get_email_service")` returns `MagicMock()` on endpoints that send emails
- **S3 storage** — `@patch("adapters.http.api.reports.routers.S3StorageService")` for report download
- **EventBus** — Overridden with a subscriber-free `EventBus()` to skip notifications/WebSocket

## Writing New Tests

### When to Write Tests

Every new feature or bug fix MUST include tests:

- **New endpoint** → Add integration test covering happy path + key error cases
- **New command/query handler** → Add unit test with mocked dependencies
- **Bug fix** → Add a regression test that reproduces the bug before fixing

### Unit Test Pattern

```python
# tests/unit/{bounded_context}_bc/{subdomain}/application/commands/test_xxx.py
class TestMyCommand:
    def test_happy_path(self):
        repo = MagicMock()
        handler = MyCommandHandler(repo=repo)
        handler.handle(MyCommand(...))
        repo.save.assert_called_once()

    def test_error_case(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = MyCommandHandler(repo=repo)
        with pytest.raises(NotFoundError):
            handler.handle(MyCommand(...))
```

### Integration Test Pattern

```python
# tests/integration/test_{router}_endpoints.py
class TestMyEndpoint:
    def test_happy_path(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.post("/api/v1/resource", json={...})
        assert resp.status_code == 201
        assert resp.json()["data"]["field"] == "expected"

    def test_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get("/api/v1/resource/nonexistent")
        assert resp.status_code == 404

    @patch("core.email.get_email_service")
    def test_with_email(self, mock_email, client, auth_as, admin_user):
        mock_email.return_value = MagicMock()
        auth_as(admin_user)
        resp = client.post("/api/v1/endpoint-that-sends-email", json={...})
        assert resp.status_code == 200
```

### File Organization

```
tests/
├── conftest.py                          # Shared fixtures (DB, client, auth)
├── unit/                                # Unit tests (no DB)
│   ├── asset_bc/
│   ├── auth_bc/
│   ├── company_bc/
│   ├── notification_bc/
│   ├── report_bc/
│   └── request_bc/
└── integration/                         # Integration tests (real DB)
    ├── test_assets_endpoints.py
    ├── test_auth_endpoints.py
    ├── test_companies_endpoints.py
    ├── test_dashboard_endpoints.py
    ├── test_departments_endpoints.py
    ├── test_my_endpoints.py
    ├── test_registration_endpoints.py
    ├── test_reports_endpoints.py
    ├── test_requests_endpoints.py
    └── test_users_endpoints.py
```

### What to Test in Integration Tests

For each endpoint, cover at minimum:

1. **Happy path** — Successful request with valid data
2. **Not found** — Resource doesn't exist (404)
3. **Conflict/validation** — Duplicate data, invalid transitions (409, 422)
4. **Access control** — Verify role restrictions where applicable

### Important Rules

- NEVER skip tests. Both `make test` and `make test-integration` must pass.
- Mock only external services (email, S3). Let repositories, handlers, and DB work for real in integration tests.
- Use the `auth_as` fixture instead of creating JWT tokens manually.
- Use the `company` fixture for tests that need a company context — it persists both the company and its email domains.
- Each integration test file maps to one router (one file per `adapters/http/api/{resource}/routers.py`).
