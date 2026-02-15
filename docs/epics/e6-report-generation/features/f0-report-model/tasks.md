# Tasks: F0 - Report Model + API Endpoints

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-16

---

## Phase 1: Domain

### Task 1.1: Create Report enums
**File:** `src/report_bc/report/domain/enums.py` (NEW)
- ReportType enum: asset_inventory, request_summary, technician_performance
- ReportStatus enum: pending, processing, completed, failed

### Task 1.2: Create Report entity
**File:** `src/report_bc/report/domain/entities.py` (NEW)
- Report dataclass with create() factory method
- Fields: id, company_id, requested_by, type, status, parameters, storage_key, error_message, created_at, completed_at, updated_at
- Validate type is valid ReportType
- Default status: pending, storage_key: None, error_message: None

### Task 1.3: Create ReportRepositoryInterface
**File:** `src/report_bc/report/domain/repository.py` (NEW)
- Abstract methods: save, find_by_id, find_all, update_status

### Task 1.4: Create __init__.py files
- All necessary __init__.py files for report_bc directory structure

---

## Phase 2: Infrastructure

### Task 2.1: Create ReportModel
**File:** `src/report_bc/report/infrastructure/models.py` (NEW)
- ULIDMixin + TimestampMixin + Base
- All columns matching entity
- Index on (company_id, created_at DESC)

### Task 2.2: Update models_registry.py
**File:** `core/models_registry.py`
- Import ReportModel

### Task 2.3: Create ReportRepository
**File:** `src/report_bc/report/infrastructure/repository.py` (NEW)
- Implement all 4 methods
- `update_status` uses UPDATE statement, sets completed_at when status is completed/failed

### Task 2.4: Create Alembic migration
- `alembic revision --autogenerate -m "add_reports_table"`
- Apply migration

---

## Phase 3: Application

### Task 3.1: Create RequestReport command
**File:** `src/report_bc/report/application/commands/request_report.py` (NEW)
- RequestReportCommand dataclass
- RequestReportCommandHandler
- Creates Report entity, saves to DB
- Dispatches `generate_report.delay(report.id)`
- Returns the report

### Task 3.2: Create ListReports query
**File:** `src/report_bc/report/application/queries/list_reports.py` (NEW)
- ListReportsQuery with company_id, page, page_size
- Handler calls repo.find_all

### Task 3.3: Create GetReport query
**File:** `src/report_bc/report/application/queries/get_report.py` (NEW)
- GetReportQuery with report_id, company_id
- Handler calls repo.find_by_id, raises ReportNotFoundError if None

---

## Phase 4: Celery Task Skeleton

### Task 4.1: Create report generation task (skeleton)
**File:** `core/tasks/reports.py` (NEW)
- `generate_report` task with `bind=True, max_retries=settings.report.REPORT_MAX_RETRIES`
- Skeleton: update status to processing, then placeholder for F1 generation logic
- Error handling: update status to failed on exception

---

## Phase 5: HTTP Layer

### Task 5.1: Create report schemas
**File:** `adapters/http/api/reports/schemas.py` (NEW)
- CreateReportRequest: type (str), parameters (optional dict with from_date, to_date)
- ReportResponse: id, type, status, parameters, created_at, completed_at, error_message
- ReportListItemResponse: id, type, status, created_at, completed_at

### Task 5.2: Create report router
**File:** `adapters/http/api/reports/routers.py` (NEW)
- POST /api/v1/reports — 202 Accepted
- GET /api/v1/reports — paginated list
- GET /api/v1/reports/{id} — detail
- All require_role(UserRole.ADMIN)

### Task 5.3: Create __init__.py
**File:** `adapters/http/api/reports/__init__.py` (NEW)

### Task 5.4: Register router in app.py
**File:** `app.py`

---

## Phase 6: Install WeasyPrint

### Task 6.1: Add weasyprint to dependencies
**File:** `pyproject.toml`
- Add `weasyprint` and `jinja2` to dependencies

---

## Phase 7: Tests

### Task 7.1: Unit tests for Report entity
**File:** `tests/unit/report_bc/report/domain/test_entities.py` (NEW)
- Test create valid report
- Test invalid type raises error
- Test default status is pending
- Test default storage_key is None

### Task 7.2: Unit tests for commands and queries
**File:** `tests/unit/report_bc/report/application/test_commands.py` (NEW)
- Test request_report creates record and dispatches task
- Test list_reports returns paginated
- Test get_report returns report
- Test get_report raises not found

### Task 7.3: Unit tests for report endpoints
**File:** `tests/unit/report_bc/test_endpoints.py` (NEW)
- Test POST /reports returns 202
- Test GET /reports returns list
- Test GET /reports/{id} returns detail
- Test GET /reports/{id} returns 404
- Test all require admin role

---

## Phase 8: Verify

- Run `python -m pytest tests/ -v` — all tests pass
- Verify migration applied
