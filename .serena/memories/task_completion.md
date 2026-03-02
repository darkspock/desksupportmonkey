# Task Completion Checklist

When completing a coding task, always perform these steps:

## 1. Code Quality
- Run `make lint` (mypy + flake8) — fix any errors
- Ensure SQLAlchemy 2.0 Mapped style is used
- Verify all domain exceptions are caught in routers
- Check Commands inherit from Command, Queries from Query

## 2. Testing
- Run `make test` for unit tests
- Run `make test-integration` if database changes involved
- Add new tests for:
  - New endpoint → tests/integration/test_{router}_endpoints.py
  - New command/query → tests/unit/{bc}/
  - Bug fix → regression test
- Both suites must pass

## 3. Progress Tracking (mandatory per project rules)
- Update `docs/epics/{epic}/features/{feature}/tasks.md` — mark checkboxes [x]
- Update `docs/epics/{epic}/slicing.md` — mark feature as "Done"
- Update `docs/product/roadmap.md` — mark epic as "Done" when all features complete

## 4. Deployment (if deploying)
- After deployment, verify:
  - API health endpoint responds
  - Service status with systemctl (no restart loops)
  - Review recent logs for errors (journalctl)
  - Test key API endpoints
  - Kill zombie processes if port conflicts
