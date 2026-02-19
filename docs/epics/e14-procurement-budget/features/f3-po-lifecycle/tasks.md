# Tasks: F3 — PO Lifecycle

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 22
**Estimated Complexity:** XL

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Application - Services | 1 | M |
| Application - Commands | 7 | S-M each |
| Application - Queries | 2 | S |
| HTTP - Schemas + Deps | 2 | M |
| HTTP - Router | 1 | L |
| Notifications | 1 | M |
| Config | 1 | S |
| Frontend | 1 | L |
| Tests - Unit | 1 | L |
| Tests - Integration | 1 | L |
| Verification | 1 | S |

---

## Phase 1: Application Layer — Services

### 1. PO Number Generator service
- [x] Create `src/procurement_bc/purchase_order/application/services/po_number_generator.py`
  - `PONumberGenerator(po_repo)` — constructor takes PO repository
  - `generate(company_id, prefix, year) -> str` — calls `repo.get_next_number()`, returns `"{prefix}-{year}-{seq:03d}"`
  - Handles first PO of the year (seq = 1)

---

## Phase 1: Application Layer — Commands

### 2. CreatePurchaseOrderCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/create_po.py`
  - `POItemInput` dataclass: description, asset_type?, quantity, unit_cost_cents, notes?
  - `CreatePurchaseOrderCommand(Command)`: company_id, vendor_id?, vendor_name, department_id, items[], request_ids[], notes?, performed_by
  - Handler:
    1. Get procurement config (for prefix + year)
    2. Generate PO number via PONumberGenerator
    3. Create PO entity via factory (DRAFT status)
    4. Add items (calculate total_cost_cents per item = quantity × unit_cost_cents)
    5. Set request_ids
    6. Recalculate total
    7. Save to repo

### 3. UpdatePurchaseOrderCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/update_po.py`
  - `UpdatePurchaseOrderCommand(Command)`: purchase_order_id, company_id, vendor_id?, vendor_name, department_id, items[], request_ids[], notes?, performed_by
  - Handler: find PO, validate DRAFT status, update fields + items, recalculate total, save

### 4. SubmitPurchaseOrderCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/submit_po.py`
  - `SubmitPurchaseOrderCommand(Command)`: purchase_order_id, company_id, performed_by
  - Handler:
    1. Find PO, validate DRAFT
    2. Call `po.submit()` (validates items + total)
    3. Get procurement config → check auto-approval threshold
    4. If total ≤ threshold: call `po.approve(performed_by)`, emit `po.approved`
    5. Else: emit `po.submitted` (notifies admins)
    6. Save

### 5. ApprovePurchaseOrderCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/approve_po.py`
  - `ApprovePurchaseOrderCommand(Command)`: purchase_order_id, company_id, approved_by
  - Handler:
    1. Find PO, validate SUBMITTED
    2. *(Extension point for F4 budget check — add optional BudgetChecker parameter)*
    3. Call `po.approve(approved_by)`
    4. Emit `po.approved`
    5. Save

### 6. RejectPurchaseOrderCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/reject_po.py`
  - `RejectPurchaseOrderCommand(Command)`: purchase_order_id, company_id, reason, performed_by
  - Handler: find PO, validate SUBMITTED, call `po.reject(reason)`, emit `po.cancelled`, save

### 7. MarkOrderedCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/mark_ordered.py`
  - `MarkOrderedCommand(Command)`: purchase_order_id, company_id, performed_by
  - Handler: find PO, validate APPROVED, call `po.mark_ordered()`, save

### 8. CancelPurchaseOrderCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/cancel_po.py`
  - `CancelPurchaseOrderCommand(Command)`: purchase_order_id, company_id, reason, performed_by
  - Handler: find PO, validate cancellable state (DRAFT/SUBMITTED/APPROVED/ORDERED), call `po.cancel(reason)`, emit `po.cancelled` (if was past DRAFT), save

---

## Phase 1: Application Layer — Queries

### 9. ListPurchaseOrdersQuery + handler
- [x] Create `src/procurement_bc/purchase_order/application/queries/list_pos.py`
  - `ListPurchaseOrdersQuery(Query)`: company_id, page, page_size, status?, vendor_id?, department_id?, date_from?, date_to?
  - Handler: call repo.find_all() with filters, return (pos, total)

### 10. GetPurchaseOrderQuery + handler
- [x] Create `src/procurement_bc/purchase_order/application/queries/get_po.py`
  - `GetPurchaseOrderQuery(Query)`: purchase_order_id, company_id
  - Handler: find by id + company_id, raise if not found, return with items and request_ids

---

## Phase 2: HTTP Layer

### 11. PO schemas
- [x] Create `adapters/http/api/purchase_orders/schemas.py`
  - `POItemRequest`: description (1-500), asset_type?, quantity (ge=1), unit_cost_cents (ge=0), notes?
  - `POCreateRequest`: vendor_id?, vendor_name (1-200), department_id, items[] (min 1), request_ids[], notes?
  - `POUpdateRequest`: same as create
  - `RejectRequest`: reason (min 1)
  - `CancelRequest`: reason (min 1)
  - `POItemResponse`: all item fields
  - `POResponse`: all PO fields + items[] + request_ids[]

### 12. PO dependencies
- [x] Create `adapters/http/api/purchase_orders/dependencies.py`
  - `get_po_repo(db) -> PurchaseOrderRepository`
  - `get_vendor_repo(db) -> VendorRepository`
  - `get_procurement_config_repo(db) -> CompanyProcurementConfigRepository`

### 13. PO router
- [x] Create `adapters/http/api/purchase_orders/routers.py`
  - `POST /` — create PO (technician+)
  - `GET /` — list POs (technician+, query params for filters)
  - `GET /{id}` — get PO detail (technician+)
  - `PUT /{id}` — update draft PO (technician+)
  - `POST /{id}/submit` — submit (technician+)
  - `POST /{id}/approve` — approve (admin)
  - `POST /{id}/reject` — reject with reason (admin)
  - `POST /{id}/mark-ordered` — mark ordered (technician+)
  - `POST /{id}/cancel` — cancel with reason (technician+)
  - Exception handling: not found → 404, invalid transition → 409, validation → 422
  - Response format: `{"data": {...}, "meta": {...}}`
- [x] Create `adapters/http/api/purchase_orders/__init__.py`

---

## Phase 3: Notifications

### 14. PO notification events
- [x] Edit `src/notification_bc/notification/domain/enums.py` (or equivalent)
  - Add event types: `po.submitted`, `po.approved`, `po.cancelled`
- [x] Edit `src/notification_bc/notification/application/services/notification_subscriber.py`
  - Handle PO events: create notification records
  - po.submitted → message: "PO {number} submitted for approval — {vendor}, total {amount}"
  - po.approved → message: "PO {number} has been approved"
  - po.cancelled → message: "PO {number} has been cancelled: {reason}"
- [x] Edit `src/notification_bc/notification/application/services/target_resolver.py`
  - po.submitted → all admins in company
  - po.approved → PO creator
  - po.cancelled → PO creator

---

## Phase 4: Configuration

### 15. Register PO router
- [x] Edit `app.py`
  - Import and include purchase-orders router with prefix `/api/v1/purchase-orders`

---

## Phase 5: Frontend

### 16. PO frontend pages
- [x] Add PO types to `web/app/src/types/index.ts`
  - `PurchaseOrderStatus` union type
  - `PurchaseOrderItem` interface
  - `PurchaseOrder` interface (all fields)
- [x] Create `web/app/src/pages/admin/PurchaseOrderListPage.tsx`
  - Table with columns: PO#, vendor, department, status badge, total, date
  - Filters: status dropdown, vendor dropdown, department dropdown, date range
  - "New PO" button → link to form
  - Pagination
- [x] Create `web/app/src/pages/admin/PurchaseOrderDetailPage.tsx`
  - Header: PO#, status badge, vendor, department, total, dates
  - Items table: description, type, qty, unit cost, total, received qty
  - Status timeline (visual)
  - Linked requests section
  - Action buttons based on status: Submit (DRAFT), Approve/Reject (SUBMITTED, admin), Mark Ordered (APPROVED), Cancel (pre-RECEIVED)
  - Notes section
- [x] Create `web/app/src/pages/admin/PurchaseOrderFormPage.tsx`
  - Vendor picker: search + select from active vendors, or create new inline
  - Department selector
  - Items builder: dynamic rows with description, asset type, qty, unit cost
  - Request linker: search + select approved requests
  - Notes textarea
  - Save as Draft / Submit buttons
  - Edit mode: load existing DRAFT PO data
- [x] Edit `web/app/src/router.tsx`
  - Add routes: `/purchase-orders`, `/purchase-orders/new`, `/purchase-orders/:id`, `/purchase-orders/:id/edit`
- [x] Edit `web/app/src/components/layout/Sidebar.tsx`
  - Add "Purchase Orders" nav item (technician+)
- [x] Edit `web/app/src/locales/en.ts` — add ~45 PO keys
- [x] Edit `web/app/src/locales/es.ts` — add ~45 PO keys

---

## Phase 6: Tests

### 17. Unit tests
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_create_po.py`
  - Create with items, auto-calculate total
  - Create generates PO number
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_submit_po.py`
  - Submit valid PO
  - Submit with no items → error
  - Submit with auto-approval (below threshold)
  - Submit without auto-approval (above threshold)
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_approve_po.py`
  - Approve submitted PO
  - Approve non-submitted → error
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_reject_po.py`
  - Reject with reason
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_cancel_po.py`
  - Cancel from each valid state (DRAFT, SUBMITTED, APPROVED, ORDERED)
  - Cancel from invalid state (RECEIVED) → error
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_mark_ordered.py`
  - Mark ordered from APPROVED
  - Mark ordered from non-APPROVED → error
- [x] Create `tests/unit/procurement_bc/purchase_order/application/services/test_po_number_generator.py`
  - First PO of year → 001
  - Sequential increment
- ~18 unit tests

### 18. Integration tests
- [x] Create `tests/integration/test_purchase_orders_endpoints.py`
  - POST create PO → 201
  - GET list POs → 200 with pagination
  - GET list with status filter → filtered results
  - GET PO detail → 200 with items
  - PUT update draft PO → 200
  - PUT update non-draft → 409
  - POST submit PO → 200
  - POST submit with auto-approval → status = APPROVED
  - POST approve → 200 (admin)
  - POST approve as technician → 403
  - POST reject → 200 with reason
  - POST mark-ordered → 200
  - POST cancel → 200 with reason
  - Invalid status transition → 409
  - Tenant isolation
- ~15 integration tests

---

## Phase 7: Verification

### 19. Verify
- [x] Lint passes: `make lint`
- [x] Unit tests pass: `make test`
- [x] Integration tests pass: `make test-integration`
- [x] Frontend builds: `cd web/app && npm run build`
- [x] TypeScript compiles: `cd web/app && npx tsc --noEmit`
- [x] Notifications fire correctly for PO events

---

## Dependency Graph

```
PONumberGenerator (1) — depends on F0 PO repo
  └── Commands (2-8) — depend on service + F0 entities/repos + F2 config
        └── Queries (9-10) — depend on F0 repos
              └── Schemas (11) + Deps (12) — depend on entity types
                    └── Router (13) — depends on schemas + commands + queries
                          └── Notifications (14) — depends on PO events
                                └── Config (15) — depends on router
                                      └── Frontend (16) — depends on API
                                            └── Tests (17-18) — after all code
```

## Execution Order

**Batch 1:** Task 1 (PO number generator)
**Batch 2 (Parallel):** Tasks 2-8 (all commands)
**Batch 3 (Parallel):** Tasks 9-10 (queries)
**Batch 4 (Parallel):** Tasks 11-12 (schemas + deps)
**Batch 5:** Task 13 (router)
**Batch 6:** Task 14 (notifications)
**Batch 7:** Task 15 (config)
**Batch 8:** Task 16 (frontend)
**Batch 9 (Parallel):** Tasks 17-18 (tests)
**Batch 10:** Task 19 (verification)

## Final Checklist

- [x] All tasks completed
- [x] All tests passing (unit + integration)
- [x] mypy passes
- [x] Frontend builds
- [x] 9 PO endpoints working
- [x] Full PO lifecycle: DRAFT → SUBMITTED → APPROVED → ORDERED → (F5) → CLOSED
- [x] Auto-approval works when below threshold
- [x] PO notifications fire correctly
