# Slicing: E14 - Procurement & Budget

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-18
**Total Features:** 7

## Slicing Rationale

E14 introduces a new bounded context (`procurement_bc`) with 6 database tables, 23 API endpoints, and 5+ frontend pages. The slicing follows bottom-up domain dependency: a foundation feature establishes all entities and persistence (F0), then independent CRUD features for vendors (F1) and config (F2) can run in parallel, the core PO lifecycle (F3) builds on both, budget enforcement (F4) and goods receipt (F5) extend PO independently, and finally reports/dashboard (F6) consumes data from all previous features.

This mirrors the E11/E13 pattern where F0 is domain+infrastructure foundation, middle features deliver independent vertical slices, and the final feature adds cross-cutting visibility (reports, dashboard, frontend polish).

## Dependency Graph

```text
F0: Procurement Domain & Infrastructure (entities, migrations, repos)
 ├── F1: Vendor CRUD (API + frontend)
 ├── F2: Procurement Config (API + frontend)
 └── F3: PO Lifecycle (create, submit, approve, order, cancel — API + frontend)
      ├── F4: Budget Allocation & Enforcement (budget CRUD, warn/strict, alerts)
      ├── F5: Goods Receipt & Asset Linking (receive items, create/link assets)
      └── F6: Reports, PDF & Dashboard (spending report, PO PDF, dashboard cards)
```

## Features Summary

| # | Feature | Covers | Complexity | Depends | Status |
|---|---------|--------|------------|---------|--------|
| F0 | Procurement Domain & Infrastructure | All entities, enums, migrations, repos | High | None | Done |
| F1 | Vendor CRUD | US-E14-006 | Medium | F0 | Done |
| F2 | Procurement Config | US-E14-004 (config part) | Small | F0 | Done |
| F3 | PO Lifecycle | US-E14-001 | High | F0, F1, F2 | Done |
| F4 | Budget Allocation & Enforcement | US-E14-003, US-E14-004 (enforcement), UC-005 | High | F0, F3 | Done |
| F5 | Goods Receipt & Asset Linking | US-E14-002 | Medium | F3 | Done |
| F6 | Reports, PDF & Dashboard | US-E14-005, US-E14-007, UC-006, UC-007 | High | F3, F4, F5 | Done |

---

## F0: Procurement Domain & Infrastructure

**Scope:** Create the entire `procurement_bc` bounded context — domain entities, enums, repository interfaces, SQLAlchemy models, migrations, repository implementations. Also extend Asset entity with `purchase_cost_cents`. Pure backend — no API endpoints, no frontend.

### Domain Layer
- `PurchaseOrderStatus` enum with 8 values and `VALID_TRANSITIONS` dict
- `PurchaseOrder` entity with state machine methods (submit, approve, reject, mark_ordered, receive, close, cancel)
- `PurchaseOrderItem` entity
- `Vendor` entity with activate/deactivate
- `DepartmentBudget` entity
- `CompanyProcurementConfig` entity
- `EnforcementMode` enum (warn, strict)
- Repository interfaces for all entities

### Infrastructure Layer
- 6 migrations: `purchase_orders`, `purchase_order_items`, `purchase_order_requests`, `vendors`, `department_budgets`, `company_procurement_configs`
- 1 migration: add `purchase_cost_cents` to `assets` table
- 6 SQLAlchemy models
- 6 repository implementations
- Asset entity + model extension

### Tests
- Unit: PO state machine transitions (valid + invalid), entity creation, budget computation helpers
- ~20 tests

### Files

| File | Action |
|------|--------|
| `src/procurement_bc/purchase_order/domain/entities.py` | Create |
| `src/procurement_bc/purchase_order/domain/enums.py` | Create |
| `src/procurement_bc/purchase_order/domain/repository.py` | Create |
| `src/procurement_bc/purchase_order/infrastructure/models.py` | Create |
| `src/procurement_bc/purchase_order/infrastructure/repository.py` | Create |
| `src/procurement_bc/vendor/domain/entities.py` | Create |
| `src/procurement_bc/vendor/domain/repository.py` | Create |
| `src/procurement_bc/vendor/infrastructure/models.py` | Create |
| `src/procurement_bc/vendor/infrastructure/repository.py` | Create |
| `src/procurement_bc/budget/domain/entities.py` | Create |
| `src/procurement_bc/budget/domain/repository.py` | Create |
| `src/procurement_bc/budget/infrastructure/models.py` | Create |
| `src/procurement_bc/budget/infrastructure/repository.py` | Create |
| `src/asset_bc/asset/domain/entities.py` | Edit — add purchase_cost_cents |
| `src/asset_bc/asset/infrastructure/models.py` | Edit — add purchase_cost_cents column |
| `alembic/versions/` | Create — 7 migrations |
| `tests/unit/procurement_bc/` | Create — domain tests |

---

## F1: Vendor CRUD

**Scope:** Full vendor management — API endpoints, application layer (commands + queries), HTTP schemas, frontend pages. Vertical slice: admin/technician can create, list, view, edit, activate/deactivate vendors.

### Application Layer
- `CreateVendorCommand` + handler
- `UpdateVendorCommand` + handler
- `ActivateVendorCommand` / `DeactivateVendorCommand` + handlers
- `ListVendorsQuery` + handler
- `GetVendorQuery` + handler

### HTTP Layer
- Router: 6 endpoints (`POST`, `GET` list, `GET` detail, `PUT`, `POST activate`, `POST deactivate`)
- Schemas: `VendorCreate`, `VendorUpdate`, `VendorResponse`, `VendorListResponse`
- Dependencies: `get_vendor_repo`

### Frontend
- `VendorListPage.tsx` — list with search, active/inactive filter
- `VendorDetailPage.tsx` — detail with POs (placeholder until F3)
- Router + sidebar nav entries
- i18n keys (EN + ES)

### Tests
- Unit: command handlers, query handlers (~10 tests)
- Integration: all 6 endpoints (~8 tests)

### Files

| File | Action |
|------|--------|
| `src/procurement_bc/vendor/application/commands/` | Create — 4 command files |
| `src/procurement_bc/vendor/application/queries/` | Create — 2 query files |
| `adapters/http/api/vendors/` | Create — routers, schemas, dependencies |
| `app.py` | Edit — register vendor router |
| `web/app/src/pages/admin/VendorListPage.tsx` | Create |
| `web/app/src/pages/admin/VendorDetailPage.tsx` | Create |
| `web/app/src/router.tsx` | Edit — add routes |
| `web/app/src/components/layout/Sidebar.tsx` | Edit — add nav item |
| `web/app/src/types/index.ts` | Edit — add Vendor type |
| `web/app/src/locales/en.ts` | Edit |
| `web/app/src/locales/es.ts` | Edit |
| `tests/unit/procurement_bc/vendor/` | Create |
| `tests/integration/test_vendors_endpoints.py` | Create |

---

## F2: Procurement Config

**Scope:** Per-company procurement configuration — API endpoints, application layer, frontend settings page. Same pattern as E11 assignment-ai config and E13 classification config.

### Application Layer
- `SaveProcurementConfigCommand` + handler (upsert)
- `GetProcurementConfigQuery` + handler

### HTTP Layer
- Router: 2 endpoints (`PUT`, `GET` on `/api/v1/settings/procurement`)
- Schemas: `ProcurementConfigUpdate`, `ProcurementConfigResponse`
- Dependencies: `get_procurement_config_repo`

### Frontend
- `ProcurementSettingsPage.tsx` — form following `AssignmentAISettingsPage` pattern
- Fields: enforcement mode dropdown, approval threshold, PO prefix, fiscal year start month, currency, auto-create assets toggle
- Router + sidebar entries
- i18n keys (EN + ES)

### Tests
- Unit: save command (create + update), get query (~6 tests)
- Integration: PUT + GET endpoints (~4 tests)

### Files

| File | Action |
|------|--------|
| `src/procurement_bc/budget/application/commands/save_config.py` | Create |
| `src/procurement_bc/budget/application/queries/get_config.py` | Create |
| `adapters/http/api/settings/procurement_routers.py` | Create |
| `adapters/http/api/settings/procurement_schemas.py` | Create |
| `adapters/http/api/settings/procurement_dependencies.py` | Create |
| `app.py` | Edit — register settings router |
| `web/app/src/pages/admin/ProcurementSettingsPage.tsx` | Create |
| `web/app/src/router.tsx` | Edit |
| `web/app/src/components/layout/Sidebar.tsx` | Edit |
| `web/app/src/types/index.ts` | Edit |
| `web/app/src/locales/en.ts` | Edit |
| `web/app/src/locales/es.ts` | Edit |
| `tests/unit/procurement_bc/budget/` | Create |
| `tests/integration/test_procurement_config_endpoints.py` | Create |

---

## F3: PO Lifecycle

**Scope:** Core purchase order management — create, list, get, update, submit, approve, reject, mark-ordered, cancel. PO ↔ Request linkage. Auto-approval based on threshold. Full frontend: PO list page, PO detail page, PO create/edit form. This is the largest feature.

### Application Layer
- `CreatePurchaseOrderCommand` + handler (with PO number generation)
- `UpdatePurchaseOrderCommand` + handler (draft only)
- `SubmitPurchaseOrderCommand` + handler (with auto-approval)
- `ApprovePurchaseOrderCommand` + handler
- `RejectPurchaseOrderCommand` + handler (→ CANCELLED)
- `MarkOrderedCommand` + handler
- `CancelPurchaseOrderCommand` + handler
- `ListPurchaseOrdersQuery` + handler (with filters)
- `GetPurchaseOrderQuery` + handler

### HTTP Layer
- Router: 11 endpoints
- Schemas: `POCreate`, `POUpdate`, `POResponse`, `POListResponse`, `POItemCreate`, etc.
- Dependencies: `get_po_repo`, `get_vendor_repo`, `get_procurement_config_repo`

### Notifications
- `po.submitted` → notify admins
- `po.approved` → notify creator
- `po.cancelled` → notify creator
- Add EventType enum entries + subscriber + resolver

### Frontend
- `PurchaseOrderListPage.tsx` — list with filters (status, vendor, dept, date)
- `PurchaseOrderDetailPage.tsx` — header, items, status timeline, linked requests, action buttons
- `PurchaseOrderFormPage.tsx` — create/edit form with vendor picker, item builder, request linker
- Router entries, sidebar nav
- i18n keys (EN + ES)

### Tests
- Unit: all command handlers, PO number generation, auto-approval logic (~18 tests)
- Integration: all 11 endpoints (~15 tests)

### Files

| File | Action |
|------|--------|
| `src/procurement_bc/purchase_order/application/commands/` | Create — 7 command files |
| `src/procurement_bc/purchase_order/application/queries/` | Create — 2 query files |
| `src/procurement_bc/purchase_order/application/services/` | Create — PO number generator |
| `adapters/http/api/purchase_orders/` | Create — routers, schemas, dependencies |
| `app.py` | Edit — register PO router |
| `src/notification_bc/notification/domain/enums.py` | Edit — add PO event types |
| `src/notification_bc/notification/application/services/notification_subscriber.py` | Edit |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit |
| `web/app/src/pages/admin/PurchaseOrderListPage.tsx` | Create |
| `web/app/src/pages/admin/PurchaseOrderDetailPage.tsx` | Create |
| `web/app/src/pages/admin/PurchaseOrderFormPage.tsx` | Create |
| `web/app/src/router.tsx` | Edit |
| `web/app/src/components/layout/Sidebar.tsx` | Edit |
| `web/app/src/types/index.ts` | Edit |
| `web/app/src/locales/en.ts` | Edit |
| `web/app/src/locales/es.ts` | Edit |
| `tests/unit/procurement_bc/purchase_order/` | Create |
| `tests/integration/test_purchase_orders_endpoints.py` | Create |

---

## F4: Budget Allocation & Enforcement

**Scope:** Department budget management — set/view budgets, compute spending, enforce limits (warn/strict), 80% threshold alerts. Budget display on departments page.

### Application Layer
- `SetDepartmentBudgetCommand` + handler (upsert)
- `GetDepartmentBudgetQuery` + handler (with spending computation)
- `GetBudgetSummaryQuery` + handler (all departments)
- `BudgetChecker` service (check enforcement, compute remaining, fire threshold alerts)

### HTTP Layer
- Router: 3 endpoints on departments + 1 budget summary
- Schemas: `BudgetSet`, `BudgetResponse`, `BudgetSummaryResponse`

### Budget Enforcement Integration
- Edit `ApprovePurchaseOrderCommand` handler to check budget before approval
- In warn mode: approve but include warning in response
- In strict mode: reject if over budget

### Notifications
- `budget.threshold_reached` → notify manager + admins
- Add EventType enum entry + subscriber + resolver

### Frontend
- Departments page: add budget column (allocated / spent / remaining)
- PO form: show department remaining budget when selecting department
- i18n keys (EN + ES)

### Tests
- Unit: budget computation, enforcement modes, threshold detection (~14 tests)
- Integration: budget endpoints, enforcement during PO approval (~8 tests)

### Files

| File | Action |
|------|--------|
| `src/procurement_bc/budget/application/commands/set_budget.py` | Create |
| `src/procurement_bc/budget/application/queries/get_budget.py` | Create |
| `src/procurement_bc/budget/application/queries/get_summary.py` | Create |
| `src/procurement_bc/budget/application/services/budget_checker.py` | Create |
| `adapters/http/api/budgets/` | Create — routers, schemas, dependencies |
| `adapters/http/api/departments/routers.py` | Edit — add budget endpoints |
| `src/procurement_bc/purchase_order/application/commands/approve_po.py` | Edit — add budget check |
| `src/notification_bc/notification/domain/enums.py` | Edit |
| `src/notification_bc/notification/application/services/notification_subscriber.py` | Edit |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit |
| `src/company_bc/department/application/commands/delete_department.py` | Edit — block if open POs |
| `web/app/src/pages/admin/DepartmentsPage.tsx` | Edit — add budget column |
| `web/app/src/pages/admin/PurchaseOrderFormPage.tsx` | Edit — show remaining budget |
| `web/app/src/locales/en.ts` | Edit |
| `web/app/src/locales/es.ts` | Edit |
| `tests/unit/procurement_bc/budget/` | Create |
| `tests/integration/test_budgets_endpoints.py` | Create |

---

## F5: Goods Receipt & Asset Linking

**Scope:** Receive PO items — partial and full receipt, optional asset creation/linking, PO status transitions through receipt flow. Receipt UI on PO detail page.

### Application Layer
- `ReceiveItemsCommand` + handler (with partial/full logic)
- `ClosePurchaseOrderCommand` + handler (from RECEIVED or PARTIALLY_RECEIVED)
- Asset creation service (pre-fill from PO item data)

### HTTP Layer
- Endpoints already defined in F3 router (`/receive`, `/close`) — add handler logic
- Schemas: `ReceiveItemsRequest` (list of item_id + received_qty + optional asset creation flag)

### Notifications
- `po.received` → notify creator + admin

### Frontend
- PO detail: receipt form (enter received quantities per item)
- PO detail: progress bars (received vs ordered per item)
- PO detail: "Create Asset" button per received item
- i18n keys (EN + ES)

### Tests
- Unit: partial receipt, full receipt, over-receive validation, asset creation (~12 tests)
- Integration: receive endpoint, close endpoint, asset creation (~6 tests)

### Files

| File | Action |
|------|--------|
| `src/procurement_bc/purchase_order/application/commands/receive_items.py` | Create |
| `src/procurement_bc/purchase_order/application/commands/close_po.py` | Create |
| `src/procurement_bc/purchase_order/application/services/receipt_asset_service.py` | Create |
| `adapters/http/api/purchase_orders/routers.py` | Edit — implement receive + close |
| `adapters/http/api/purchase_orders/schemas.py` | Edit — add receipt schemas |
| `web/app/src/pages/admin/PurchaseOrderDetailPage.tsx` | Edit — receipt form + progress |
| `web/app/src/locales/en.ts` | Edit |
| `web/app/src/locales/es.ts` | Edit |
| `tests/unit/procurement_bc/purchase_order/application/commands/test_receive.py` | Create |
| `tests/integration/test_purchase_orders_endpoints.py` | Edit — receipt tests |

---

## F6: Reports, PDF & Dashboard

**Scope:** Spending report (Celery), PO PDF generation, dashboard cards (Budget Health, Recent POs), request detail linked POs card. Final frontend polish.

### Reports
- `department_spending` report type added to `ReportType` enum
- Celery task + Jinja2 HTML template + WeasyPrint PDF
- Report includes: per-department budget vs actual, top vendors, top asset types

### PO PDF
- Celery task for PO PDF generation (company name, PO number, vendor, items table, total)
- Jinja2 template + WeasyPrint
- Store in MinIO, download via signed URL

### Dashboard
- Budget Health card: total allocated, total spent, departments at risk (>80%)
- Recent POs card: last 5 POs with status badges
- Backend queries for dashboard data

### Frontend
- Dashboard page: 2 new cards
- Request detail page: linked POs section
- PO detail page: "Download PDF" button
- Reports page: department_spending report type in dropdown
- i18n keys (EN + ES)

### Tests
- Unit: report generation, budget summary computation (~8 tests)
- Integration: dashboard endpoints, report generation, PO PDF (~6 tests)

### Files

| File | Action |
|------|--------|
| `src/report_bc/report/domain/enums.py` | Edit — add DEPARTMENT_SPENDING |
| `core/tasks/reports.py` | Edit — add spending report + PO PDF tasks |
| `templates/reports/department_spending.html` | Create |
| `templates/reports/purchase_order.html` | Create |
| `adapters/http/api/purchase_orders/routers.py` | Edit — add PDF endpoints |
| `adapters/http/api/dashboard/routers.py` | Edit — add budget + PO cards |
| `adapters/http/api/dashboard/dependencies.py` | Edit |
| `web/app/src/pages/admin/DashboardPage.tsx` | Edit — 2 new cards |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Edit — linked POs |
| `web/app/src/pages/admin/PurchaseOrderDetailPage.tsx` | Edit — PDF button |
| `web/app/src/locales/en.ts` | Edit |
| `web/app/src/locales/es.ts` | Edit |
| `tests/unit/report_bc/` | Edit — spending report tests |
| `tests/integration/test_dashboard_endpoints.py` | Edit |
| `tests/integration/test_purchase_orders_endpoints.py` | Edit — PDF tests |

---

## Recommended Implementation Order

1. **F0** — Procurement Domain & Infrastructure (~2 sessions): all entities, migrations, repos, domain tests
2. **F1** — Vendor CRUD (~1 session): API + frontend, can parallelize with F2
3. **F2** — Procurement Config (~1 session): settings API + frontend, can parallelize with F1
4. **F3** — PO Lifecycle (~2-3 sessions): core PO management, largest feature
5. **F4** — Budget & Enforcement (~1-2 sessions): budget CRUD, enforcement on PO approval
6. **F5** — Goods Receipt (~1-2 sessions): receive items, asset creation
7. **F6** — Reports, PDF & Dashboard (~1-2 sessions): spending report, PO PDF, dashboard, final polish

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1/F2 → F3 → F4/F5 → F6)
- [x] Each feature independently deployable (after dependencies)
- [x] Vertical slices — F1 delivers full vendor management, F3 delivers full PO management, etc.
- [x] Shared foundation identified (F0)
- [x] No overlapping scope — each feature owns its files
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered (7 user stories, 8 use cases, 23 endpoints)

## Risk Notes

- **F0 is large (~7 migrations, 6 repos):** Consider splitting domain tests from infrastructure if sessions run long, but keep all in one feature for entity ownership consistency.
- **F3 is the critical path:** PO lifecycle is the largest single feature. If it grows beyond 2-3 sessions, consider splitting PO CRUD from PO status transitions.
- **F4 modifies F3's approve handler:** Budget enforcement hooks into the existing approve command. Design the handler with a clear injection point in F3 to avoid rework.
- **Concurrent PO numbering:** F3's PO number generator must handle concurrent requests with `SELECT ... FOR UPDATE`. Test under concurrency in integration tests.
- **F6 spans many files:** Reports, PDF, dashboard, and request detail all in one feature. This is acceptable because each is a small, independent addition — no shared state between them.
