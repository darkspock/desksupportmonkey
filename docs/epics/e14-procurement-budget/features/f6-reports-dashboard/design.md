# Solution Design: F6 — Reports, PDF & Dashboard

**Requirement:** [requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** Cross-cutting (`report_bc`, `procurement_bc`, dashboard)

## Summary

Spending report (Celery), PO PDF generation, dashboard cards (Budget Health, Recent POs), request detail linked POs card. Final frontend polish. This feature adds the visibility and reporting layer on top of the procurement data.

## Architecture Decision

The spending report follows the existing E6 report pipeline: Celery task → Jinja2 HTML → WeasyPrint PDF → MinIO upload. PO PDF follows the same pipeline but is triggered per-PO (not from the report list). Dashboard cards use new query handlers that fetch aggregated budget and PO data. The request detail page gets a simple linked-POs section querying POs by request ID.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ReportType enum | `src/report_bc/report/domain/entities.py` | — | Add DEPARTMENT_SPENDING |
| Report Celery tasks | `core/tasks/reports.py` | Template | Add spending report + PO PDF tasks |
| Report templates | `templates/reports/` | Template | Add 2 new templates |
| Dashboard router | `adapters/http/api/dashboard/routers.py` | — | Add budget + PO endpoints |
| Dashboard dependencies | `adapters/http/api/dashboard/dependencies.py` | — | Add procurement repos |
| Request detail page | `web/app/src/pages/technician/RequestDetailPage.tsx` | — | Add linked POs card |
| MinIO storage | `core/storage.py` | Yes | None |

## Implementation Plan

### 1. Reports

#### Spending Report

Add `DEPARTMENT_SPENDING = "department_spending"` to `ReportType` enum.

Celery task: `generate_department_spending_report(report_id, company_id, fiscal_year)`
1. Query all departments with budgets for the fiscal year
2. Compute spending per department (sum of PO totals in countable statuses)
3. Query top 5 vendors by spend
4. Query top 5 asset types by spend
5. Render Jinja2 template → HTML → WeasyPrint PDF
6. Upload to MinIO
7. Update report record status

Template: `templates/reports/department_spending.html`
- Company header
- Per-department table: name, allocated, spent, remaining, utilization %
- Top vendors table
- Top asset types table

#### PO PDF

Celery task: `generate_po_pdf(po_id, company_id)`
1. Fetch PO with items
2. Fetch company info
3. Render template → HTML → WeasyPrint PDF
4. Upload to MinIO with key `po-pdfs/{po_id}.pdf`
5. Store PDF URL on PO record (or return signed URL)

Template: `templates/reports/purchase_order.html`
- Company name and logo placeholder
- PO number, date, status
- Vendor info (name, email, phone, address)
- Items table: #, description, asset type, qty, unit cost, total
- PO total
- Notes

### 2. Dashboard Queries

| Query | Handler | Description |
|-------|---------|-------------|
| GetBudgetHealthQuery | GetBudgetHealthQueryHandler | Total allocated, total spent, at-risk departments |
| GetRecentPurchaseOrdersQuery | GetRecentPurchaseOrdersQueryHandler | Last 5 POs with status |

```python
@dataclass
class GetBudgetHealthQuery(Query):
    company_id: str

# Returns:
# - total_allocated_cents: int
# - total_spent_cents: int
# - departments_at_risk: list[{name, utilization_pct, remaining_cents}]

@dataclass
class GetRecentPurchaseOrdersQuery(Query):
    company_id: str
    limit: int = 5

# Returns: list[{id, po_number, vendor_name, status, total_amount_cents, created_at}]
```

### 3. HTTP Layer

#### PO PDF Endpoints

Add to purchase-orders router:

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/api/v1/purchase-orders/{id}/pdf` | technician+ | Generate PO PDF |
| GET | `/api/v1/purchase-orders/{id}/pdf` | technician+ | Download PO PDF (signed URL) |

#### Dashboard Endpoints

Add to dashboard router:

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| GET | `/api/v1/dashboard/budget-health` | admin | Budget health summary |
| GET | `/api/v1/dashboard/recent-purchase-orders` | technician+ | Recent POs |

### 4. Frontend

| Page | Change | Description |
|------|--------|-------------|
| DashboardPage | Edit | Add Budget Health card, Recent POs card |
| RequestDetailPage | Edit | Add "Linked Purchase Orders" section |
| PurchaseOrderDetailPage | Edit | Add "Download PDF" button |
| ReportsPage (dropdown) | Edit | Add "Department Spending" option |

**Budget Health card:**
- Total allocated vs total spent (with progress bar)
- List of departments at risk (>80% utilization)
- Link to budget summary page

**Recent POs card:**
- Table: PO#, vendor, status badge, amount, date
- Link to PO detail

**Linked POs on RequestDetailPage:**
- List of POs linked to this request (if any)
- Each shows: PO#, status badge, amount
- Link to PO detail

**Download PDF button on PurchaseOrderDetailPage:**
- Visible for APPROVED+ statuses (not DRAFT/SUBMITTED)
- Click → POST to generate (if not cached) → GET to download
- Loading spinner while generating

- i18n: ~20 keys (EN + ES)

### 5. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/report_bc/report/domain/entities.py` | Edit | Add DEPARTMENT_SPENDING to ReportType |
| `core/tasks/reports.py` | Edit | Add spending report + PO PDF tasks |
| `templates/reports/department_spending.html` | Create | Spending report template |
| `templates/reports/purchase_order.html` | Create | PO PDF template |
| `adapters/http/api/purchase_orders/routers.py` | Edit | Add PDF endpoints |
| `adapters/http/api/dashboard/routers.py` | Edit | Add budget + PO card endpoints |
| `adapters/http/api/dashboard/dependencies.py` | Edit | Add procurement repos |
| `web/app/src/pages/admin/DashboardPage.tsx` | Edit | Add 2 cards |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Edit | Add linked POs section |
| `web/app/src/pages/admin/PurchaseOrderDetailPage.tsx` | Edit | Add PDF download button |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | GetBudgetHealthQueryHandler | High |
| Unit | GetRecentPurchaseOrdersQueryHandler | Medium |
| Unit | Spending report data aggregation | High |
| Unit | PO PDF data assembly | Medium |
| Integration | Dashboard budget-health endpoint | High |
| Integration | Dashboard recent-purchase-orders endpoint | Medium |
| Integration | PO PDF generation + download | Medium |
| Integration | Report generation (department_spending type) | Medium |

~14 tests total (8 unit + 6 integration).

## Implementation Order

1. [ ] Domain: Add DEPARTMENT_SPENDING to ReportType enum
2. [ ] Reports: Spending report Celery task + template
3. [ ] Reports: PO PDF Celery task + template
4. [ ] Application: GetBudgetHealthQuery + handler
5. [ ] Application: GetRecentPurchaseOrdersQuery + handler
6. [ ] HTTP: PO PDF endpoints
7. [ ] HTTP: Dashboard endpoints
8. [ ] Frontend: Dashboard cards, request detail linked POs, PO detail PDF button, i18n
9. [ ] Tests: Unit tests
10. [ ] Tests: Integration tests

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| WeasyPrint rendering issues with PO table | Low | Low | Use simple HTML table structure, tested with sample data |
| Large spending report (many departments) | Low | Medium | Celery task handles async; pagination not needed for report |
| MinIO storage for PO PDFs | Low | Low | Follow existing report upload pattern |
