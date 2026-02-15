# Validation: E6 - Report Generation

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-16

---

## Codebase Alignment Check

### Existing Patterns to Follow

| Pattern | Source | Apply to E6 |
|---|---|---|
| Entity as dataclass | `src/request_bc/request/domain/entities.py` | Report entity |
| Repository interface (ABC) | `src/request_bc/request/domain/repository.py` | ReportRepositoryInterface |
| ULIDMixin + TimestampMixin | `core/mixins.py` | ReportModel |
| Command + Handler pattern | `src/request_bc/request/application/commands/` | RequestReport command |
| Query + Handler pattern | `src/request_bc/request/application/queries/` | ListReports, GetReport |
| Router with DI | `adapters/http/api/requests/routers.py` | Report router |
| Celery task pattern | `core/tasks/cleanup.py` | Report generation task |
| S3 storage pattern | `core/storage.py` | Upload PDF, get signed URL |
| EventBus publish | `adapters/http/api/requests/routers.py` | Publish report.ready event |

### Existing Infrastructure to Reuse

| Component | Location | Usage in E6 |
|---|---|---|
| `S3StorageService` | `core/storage.py` | Upload PDF, generate signed download URL |
| `celery_app` | `core/celery.py` | Task decorator, task routing to "reports" queue |
| `SessionLocal` | `core/database.py` | DB session in Celery task (no DI) |
| `ReportSettings` | `core/config.py` | REPORT_RETENTION_DAYS, REPORT_MAX_RETRIES |
| `S3Settings` | `core/config.py` | S3_REPORTS_BUCKET, S3_SIGNED_URL_EXPIRY |
| `RequestRepository` | `src/request_bc/request/infrastructure/repository.py` | Dashboard aggregate methods for report data |
| `AssetRepository` | `src/asset_bc/asset/infrastructure/repository.py` | Dashboard aggregate methods for report data |
| `EventBus` | `src/notification_bc/notification/application/services/event_bus.py` | Publish report.ready events |
| `EventType` | `src/notification_bc/notification/domain/enums.py` | Add REPORT_READY type |
| `TargetResolver` | `src/notification_bc/notification/application/services/target_resolver.py` | Route report.ready to requester |
| `require_role(UserRole.ADMIN)` | `adapters/http/api/auth/dependencies.py` | Admin-only access |
| `PaginationMeta` | `adapters/http/schemas/responses.py` | List reports pagination |

### Key Decision: Celery Task with SessionLocal

Celery tasks run outside the FastAPI request lifecycle, so they can't use `Depends(get_db)`. Instead, they create their own `SessionLocal()` session, following the pattern in `core/tasks/cleanup.py`:
```python
session = SessionLocal()
try:
    # do work
    session.commit()
except Exception:
    session.rollback()
    raise
finally:
    session.close()
```

### Key Decision: WeasyPrint for PDF

WeasyPrint converts HTML+CSS to PDF in pure Python. Templates are Jinja2 HTML files with inline CSS. This avoids external binary dependencies (unlike wkhtmltopdf) and gives full control over layout.

### Key Decision: Event Notification for Report Ready

When the Celery task completes, it publishes a `report.ready` DomainEvent. However, since the task runs outside the HTTP lifecycle, it can't use the router-level EventBus. Instead, the task directly creates a notification using `NotificationRepository` and pushes via `ConnectionManager` (if the user is connected via WebSocket).

**Update:** Actually, the event bus is an in-process singleton. The Celery worker is a separate process, so it can't access the same EventBus or ConnectionManager. For report.ready notifications:
1. The Celery task creates the notification record directly (using NotificationRepository)
2. WebSocket push is skipped (user isn't connected to the worker process)
3. The user will see the notification on their next poll of `/api/v1/my/notifications`

This is acceptable for v1. Real-time push for reports can be added later via Redis pub/sub.

---

## Dependency Check

### Required from E0 (All Exist)

- [x] FastAPI app with router registration — `app.py`
- [x] Base model classes — `core/mixins.py`
- [x] Database session — `core/database.py`
- [x] JWT authentication — `core/jwt.py`
- [x] RBAC — `adapters/http/api/auth/dependencies.py`
- [x] Celery configuration — `core/celery.py`
- [x] S3 storage service — `core/storage.py`
- [x] Report settings — `core/config.py` (ReportSettings)

### Required from E2 (All Exist)

- [x] AssetModel with all fields — `src/asset_bc/asset/infrastructure/models.py`
- [x] AssetRepository with aggregate queries — `src/asset_bc/asset/infrastructure/repository.py`
- [x] `count_by_status`, `count_by_type`, `find_expiring_warranties`, `find_aging_assets`

### Required from E3 (All Exist)

- [x] ServiceRequestModel with all fields — `src/request_bc/request/infrastructure/models.py`
- [x] RequestRepository with aggregate queries — `src/request_bc/request/infrastructure/repository.py`
- [x] `count_by_status`, `count_by_type`, `count_by_priority`, `avg_resolution_time`, `avg_resolution_time_by_technician`, `count_by_period`, `find_open_requests_with_age`

### Required from E4 (All Exist)

- [x] Notification entity and repository — `src/notification_bc/`
- [x] EventType enum — `src/notification_bc/notification/domain/enums.py`
- [x] NotificationRepository — `src/notification_bc/notification/infrastructure/repository.py`

### Required from E5 (All Exist)

- [x] Dashboard aggregate queries in repositories — used by report data collectors
- [x] SLA thresholds — `adapters/http/api/dashboard/routers.py` (SLA_THRESHOLDS_HOURS)

### New Dependencies Required

- [ ] `weasyprint` — Python library for HTML→PDF conversion
- [ ] `jinja2` — Template engine (likely already installed via FastAPI)

---

## Scope Validation

### In Scope (from roadmap)

- [x] Celery task for async PDF generation
- [x] Jinja2 HTML templates → WeasyPrint PDF
- [x] Upload to MinIO (S3-compatible)
- [x] Report record (pending → completed/failed)
- [x] Signed URL for download (1h expiry)
- [x] Report types: asset inventory, request summary, technician performance
- [x] Max 3 retries, 5 min timeout

### Not in Scope (deferred)

- Email delivery of completed reports
- CSV export format
- Report scheduling (periodic auto-generation)
- Report retention cleanup task
- Concurrent report limit / rate limiting

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| WeasyPrint requires system libraries (cairo, pango) | Include in Dockerfile. Document in README. |
| PDF generation may be slow for large datasets | Celery task with 5 min timeout. Paginate data if needed. |
| Celery worker separate process — no EventBus access | Create notifications directly in DB from task |
| S3 upload failure after PDF generation | Celery retry mechanism (max 3 retries) |
| Large PDF files consuming storage | REPORT_RETENTION_DAYS setting for future cleanup |

---

## Observations

### 1. SLA Thresholds Constant Duplication
`SLA_THRESHOLDS_HOURS` is defined in `adapters/http/api/dashboard/routers.py`. The report task also needs it. Extract to a shared location (e.g., `src/request_bc/request/domain/enums.py` or a constants file).

### 2. Asset find_all for Full List
The asset inventory report needs a full asset list (not just aggregates). `AssetRepository.find_all()` exists with pagination. For the report, we'll query all assets (unpaginated) or use a large page_size. Consider adding a `find_all_by_company(company_id)` method without pagination for report use.

### 3. Template Location
HTML templates for PDF generation live in `templates/reports/` at the project root. Jinja2 can load from this directory.

### 4. Company Name in Reports
Reports need the company name for the header. The Celery task will need to query the company name via `CompanyRepository`.

---

## Estimated Complexity

| Area | Items | Complexity |
|---|---|---|
| Domain entity + enums | Report + ReportType + ReportStatus | Low |
| Repository | 1 interface + 1 implementation | Low |
| Migration | 1 table (reports) | Low |
| Commands | 1 (request_report) | Low |
| Queries | 2 (list_reports, get_report) | Low |
| Celery task | 1 task with 3 report type generators | High |
| HTML templates | 3 Jinja2 templates + base | Medium |
| WeasyPrint integration | PDF conversion | Medium |
| Router | 4 endpoints (create, list, detail, download) | Medium |
| Notification integration | Add event type + create notification in task | Low |
| Tests | ~25 unit tests | Medium |

**Overall:** Medium-High. The Celery task is the most complex part — it queries data, renders templates, converts to PDF, uploads to S3, and updates the report record. Individual components are simple, but the async pipeline has multiple failure points.

---

## Validation Result

**Status:** APPROVED — Ready for slicing

All E0-E5 infrastructure is in place. Celery, S3, dashboard queries, and notification system are ready. New dependencies: `weasyprint` (PyPI). The `report_bc` is a new, isolated bounded context. PDF generation runs async in Celery worker.
