# Tasks: F4 — Dashboard, Report & My Tools (18 MCP Tools)

## Implementation Tasks

### 1. Dashboard Tools (`adapters/mcp/tools/dashboard.py`)
- [x] Create `dashboard.py` with 7 admin dashboard tools
- [x] `dashboard_request_summary` — count by status, type, priority
- [x] `dashboard_resolution_time` — avg resolution time + by technician
- [x] `dashboard_request_trend` — count by period with aggregation
- [x] `dashboard_asset_summary` — count by status, type
- [x] `dashboard_warranty_alerts` — find expiring warranties
- [x] `dashboard_aging_alerts` — find aging assets
- [x] `dashboard_sla_alerts` — open requests with SLA breach detection

### 2. Report Tools (`adapters/mcp/tools/reports.py`)
- [x] Create `reports.py` with 4 admin report tools
- [x] `request_report` — trigger Celery task, return pending metadata
- [x] `list_reports` — paginated list of reports
- [x] `get_report` — get report details
- [x] `download_report` — get signed URL for completed report

### 3. My Tools (`adapters/mcp/tools/my.py`)
- [x] Create `my.py` with 7 personal data tools
- [x] `my_equipment` — list assigned assets (EMPLOYEE)
- [x] `my_requests` — paginated requests with status filter (EMPLOYEE)
- [x] `my_notifications` — paginated notifications with unread count (EMPLOYEE)
- [x] `mark_notification_read` — mark single notification read (EMPLOYEE)
- [x] `mark_all_notifications_read` — mark all notifications read (EMPLOYEE)
- [x] `get_my_company_settings` — get company settings (ADMIN)
- [x] `update_my_company_settings` — update email domains (ADMIN)

### 4. Module Registration
- [x] Update `adapters/mcp/tools/__init__.py` with 3 new imports

### 5. Unit Tests
- [x] `tests/unit/mcp/tools/test_dashboard.py` (9 tests)
- [x] `tests/unit/mcp/tools/test_reports.py` (8 tests)
- [x] `tests/unit/mcp/tools/test_my.py` (11 tests)

### 6. Verification
- [x] Lint passes (`uv run flake8`)
- [x] New tool tests pass (28/28)
- [x] Full unit suite passes (`make test` — 577 passed)

### 7. Progress Tracking
- [x] Mark all tasks above as done
- [x] Update `slicing.md` — F4 status to Done
