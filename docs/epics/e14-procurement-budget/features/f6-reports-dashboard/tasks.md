# Tasks: F6 — Reports, PDF & Dashboard

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 14
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Reports - Celery tasks | 2 | M each |
| Reports - Templates | 2 | S each |
| Application - Queries | 2 | S |
| HTTP - Endpoints | 2 | S-M |
| Frontend | 1 | M |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Domain — Enums

### 1. Add DEPARTMENT_SPENDING report type
- [x] Edit `src/report_bc/report/domain/entities.py` (or enums file)
  - Add `DEPARTMENT_SPENDING = "department_spending"` to ReportType enum

---

## Phase 2: Reports — Templates

### 2. Spending report HTML template
- [x] Create `templates/reports/department_spending.html`
  - Jinja2 template for WeasyPrint
  - Company header (name, fiscal year)
  - Per-department table: name, allocated amount, spent amount, remaining, utilization %
  - Color coding: red for >100%, yellow for >80%
  - Top 5 vendors by total spend table
  - Top 5 asset types by total spend table
  - Footer with generation date

### 3. PO PDF HTML template
- [x] Create `templates/reports/purchase_order.html`
  - Jinja2 template for WeasyPrint
  - Company name header
  - PO number, date created, status
  - Vendor section: name, email, phone, address
  - Items table: #, description, asset type, quantity, unit cost, total cost
  - PO total (formatted as currency)
  - Notes section (if present)
  - Footer with company name + "Generated on {date}"

---

## Phase 2: Reports — Celery Tasks

### 4. Spending report Celery task
- [x] Edit `core/tasks/reports.py`
  - Add `generate_department_spending_report(report_id, company_id, fiscal_year)` task
  - Logic:
    1. Fetch all departments for company
    2. Fetch all budgets for fiscal year
    3. Compute spending per department (PO totals in countable statuses)
    4. Query top 5 vendors by spend (aggregate)
    5. Query top 5 asset types by spend (aggregate)
    6. Render `department_spending.html` template with data
    7. Convert to PDF via WeasyPrint
    8. Upload to MinIO
    9. Update report record: status = completed, file_url = signed URL
  - Error handling: on failure → report status = failed, log error

### 5. PO PDF Celery task
- [x] Edit `core/tasks/reports.py`
  - Add `generate_po_pdf(po_id, company_id)` task
  - Logic:
    1. Fetch PO with items
    2. Fetch company info (name)
    3. Format amounts (cents → display currency)
    4. Render `purchase_order.html` template
    5. Convert to PDF via WeasyPrint
    6. Upload to MinIO with key `po-pdfs/{po_id}.pdf`
    7. Return signed URL for download
  - Re-generation: if PDF already exists and PO was updated after last generation → regenerate

---

## Phase 3: Application Layer — Queries

### 6. GetBudgetHealthQuery + handler
- [x] Create `src/procurement_bc/budget/application/queries/get_budget_health.py`
  - `GetBudgetHealthQuery(Query)`: company_id
  - Handler:
    1. Get current fiscal year from config
    2. Get all department budgets for fiscal year
    3. Compute spending per department
    4. Aggregate: total_allocated, total_spent
    5. Identify departments at risk (>80% utilization)
    6. Return summary

### 7. GetRecentPurchaseOrdersQuery + handler
- [x] Create `src/procurement_bc/purchase_order/application/queries/get_recent_pos.py`
  - `GetRecentPurchaseOrdersQuery(Query)`: company_id, limit=5
  - Handler: query last N POs ordered by created_at desc
  - Return: list of {id, po_number, vendor_name, status, total_amount_cents, created_at}

---

## Phase 4: HTTP Layer

### 8. Dashboard endpoints
- [x] Edit `adapters/http/api/dashboard/routers.py`
  - `GET /api/v1/dashboard/budget-health` — admin only
    - Returns: total_allocated, total_spent, departments_at_risk[]
  - `GET /api/v1/dashboard/recent-purchase-orders` — technician+
    - Returns: list of recent POs with basic info
- [x] Edit `adapters/http/api/dashboard/dependencies.py`
  - Add `get_budget_repo`, `get_po_repo`, `get_config_repo` dependencies

### 9. PO PDF endpoints
- [x] Edit `adapters/http/api/purchase_orders/routers.py`
  - `POST /{id}/pdf` — generate PO PDF (technician+)
    - Validate: PO must be APPROVED or later (not DRAFT/SUBMITTED)
    - Dispatch Celery task
    - Return: {status: "generating"} or {url: signed_url} if already cached
  - `GET /{id}/pdf` — download PO PDF (technician+)
    - Return signed URL for existing PDF
    - If not generated → 404

---

## Phase 5: Frontend

### 10. Dashboard + request + PO detail frontend
- [x] Edit `web/app/src/pages/admin/DashboardPage.tsx`
  - Add "Budget Health" card:
    - Total allocated vs total spent with progress bar
    - List of departments at risk (name, utilization %)
    - Link to budget summary
  - Add "Recent Purchase Orders" card:
    - Table: PO#, vendor, status badge, amount, date
    - Each row links to PO detail
- [x] Edit `web/app/src/pages/technician/RequestDetailPage.tsx`
  - Add "Linked Purchase Orders" section (shown when request has linked POs)
  - Each PO: PO# (link), status badge, total amount
  - Fetch POs by request_id from PO list endpoint (filter by request)
- [x] Edit `web/app/src/pages/admin/PurchaseOrderDetailPage.tsx`
  - Add "Download PDF" button
  - Visible for APPROVED, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CLOSED statuses
  - Click → POST to generate (if needed) → GET to download
  - Loading state while generating
- [x] Add `department_spending` to report type dropdown (if report page has type selector)
- [x] Edit `web/app/src/locales/en.ts` — add ~20 dashboard/report/PDF keys
- [x] Edit `web/app/src/locales/es.ts` — add ~20 dashboard/report/PDF keys

---

## Phase 6: Tests

### 11. Unit tests
- [x] Create `tests/unit/procurement_bc/budget/application/queries/test_budget_health.py`
  - Returns totals with at-risk departments
  - No budgets → empty response
- [x] Create `tests/unit/procurement_bc/purchase_order/application/queries/test_recent_pos.py`
  - Returns last N POs ordered by date
  - Empty list when no POs
- [x] Edit `tests/unit/report_bc/report/application/test_commands.py`
  - department_spending report type accepted
- ~8 unit tests

### 12. Integration tests
- [x] Edit `tests/integration/test_dashboard_endpoints.py`
  - GET budget-health → 200 with totals
  - GET recent-purchase-orders → 200 with list
  - Budget-health admin only → 403 for technician
- [x] Edit `tests/integration/test_purchase_orders_endpoints.py`
  - POST /{id}/pdf → 200 or 202
  - GET /{id}/pdf for non-existent → 404
  - POST pdf for DRAFT PO → 409
- [x] Edit `tests/integration/test_reports_endpoints.py`
  - Generate department_spending report
- ~6 integration tests

---

## Phase 7: Verification

### 13. Verify
- [x] Lint passes: `make lint`
- [x] Unit tests pass: `make test`
- [x] Integration tests pass: `make test-integration`
- [x] Frontend builds: `cd web/app && npm run build`
- [x] TypeScript compiles: `cd web/app && npx tsc --noEmit`
- [x] Spending report generates correctly with sample data
- [x] PO PDF renders with correct layout

---

## Phase 8: Epic Completion

### 14. Progress tracking
- [x] Update `docs/epics/e14-procurement-budget/slicing.md` — F6 status to Done
- [x] Update `docs/product/roadmap.md` — E14 status to Done
- [x] Verify all 7 features marked Done in slicing.md

---

## Dependency Graph

```
ReportType enum (1) — minimal change
  └── Templates (2-3) — independent
  └── Celery tasks (4-5) — depend on templates + F0 repos
        └── Dashboard queries (6-7) — depend on F0+F4 repos
              └── Dashboard endpoints (8) — depends on queries
              └── PDF endpoints (9) — depends on Celery task
                    └── Frontend (10) — depends on API endpoints
                          └── Tests (11-12) — after all code
                                └── Progress tracking (14) — after verification
```

## Execution Order

**Batch 1 (Parallel):** Task 1 (enum) + Tasks 2-3 (templates)
**Batch 2 (Parallel):** Tasks 4-5 (Celery tasks) + Tasks 6-7 (queries)
**Batch 3 (Parallel):** Tasks 8-9 (endpoints)
**Batch 4:** Task 10 (frontend)
**Batch 5 (Parallel):** Tasks 11-12 (tests)
**Batch 6:** Task 13 (verification)
**Batch 7:** Task 14 (progress tracking)

## Final Checklist

- [x] All tasks completed
- [x] All tests passing (unit + integration)
- [x] mypy passes
- [x] Frontend builds
- [x] Spending report generates PDF with correct data
- [x] PO PDF generates with correct layout
- [x] Dashboard cards show budget health + recent POs
- [x] Request detail shows linked POs
- [x] E14 fully complete — all 7 features Done
