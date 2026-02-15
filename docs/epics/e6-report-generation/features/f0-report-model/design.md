# Design: F0 - Report Model + API Endpoints

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-16

---

## Domain

### Report Entity
```python
@dataclass
class Report:
    id: str
    company_id: str
    requested_by: str
    type: ReportType
    status: ReportStatus
    parameters: dict | None
    storage_key: str | None
    error_message: str | None
    created_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime | None
```

### Enums
```python
class ReportType(str, Enum):
    ASSET_INVENTORY = "asset_inventory"
    REQUEST_SUMMARY = "request_summary"
    TECHNICIAN_PERFORMANCE = "technician_performance"

class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

## Infrastructure

### ReportModel
```
Table: reports
- id: String(26) PK (ULID)
- company_id: String(26) FK(companies.id) indexed
- requested_by: String(26) FK(users.id)
- type: String(30)
- status: String(20) default "pending"
- parameters: JSON nullable
- storage_key: String(500) nullable
- error_message: Text nullable
- created_at: DateTime (from TimestampMixin)
- updated_at: DateTime (from TimestampMixin)
- completed_at: DateTime nullable

Index: (company_id, created_at DESC) for listing
```

### Repository Methods
- `save(report) -> Report`
- `find_by_id(report_id, company_id) -> Report | None`
- `find_all(company_id, page, page_size) -> tuple[list[Report], int]`
- `update_status(report_id, status, storage_key?, error_message?, completed_at?) -> bool`

---

## Application

### RequestReport Command
```python
@dataclass
class RequestReportCommand:
    company_id: str
    requested_by: str
    type: str
    parameters: dict | None = None

class RequestReportCommandHandler:
    def handle(self, command) -> Report:
        report = Report.create(...)
        self.report_repo.save(report)
        # Dispatch Celery task
        generate_report.delay(report.id)
        return report
```

### Queries
- `ListReportsQuery` — paginated, company-scoped
- `GetReportQuery` — single report by id + company_id

---

## Router

```
POST /api/v1/reports          → 202 Accepted, {"data": report}
GET  /api/v1/reports          → 200, {"data": [...], "meta": pagination}
GET  /api/v1/reports/{id}     → 200, {"data": report}
```

All endpoints use `require_role(UserRole.ADMIN)`.

---

## Celery Task Skeleton

In F0, create the task file with a placeholder that will be fully implemented in F1:

```python
@celery_app.task(name="core.tasks.reports.generate_report", bind=True, max_retries=3)
def generate_report(self, report_id: str):
    # F1 will implement the actual generation logic
    pass
```
