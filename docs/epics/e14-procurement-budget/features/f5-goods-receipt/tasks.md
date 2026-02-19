# Tasks: F5 — Goods Receipt & Asset Linking

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 12
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Application - Services | 1 | M |
| Application - Commands | 2 | M |
| Notifications | 1 | S |
| HTTP - Schemas | 1 | S |
| HTTP - Endpoints | 1 | M |
| Frontend | 1 | M |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Application Layer — Services

### 1. ReceiptAssetService
- [x] Create `src/procurement_bc/purchase_order/application/services/receipt_asset_service.py`
  - `ReceiptAssetService(asset_repo)` constructor
  - `create_asset_from_item(company_id, po_item, vendor_name, received_by) -> str`:
    1. Create Asset entity via `Asset.create()`
    2. Set type from po_item.asset_type
    3. Set purchase_cost_cents from po_item.unit_cost_cents
    4. Set purchase_date to now
    5. Set status to "available"
    6. Save via asset_repo
    7. Return asset.id

---

## Phase 1: Application Layer — Commands

### 2. ReceiveItemsCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/receive_items.py`
  - `ReceiveItemInput` dataclass: item_id, received_quantity, create_asset (bool), link_asset_id?
  - `ReceiveItemsCommand(Command)`: purchase_order_id, company_id, items[], performed_by
  - Handler:
    1. Find PO, validate status (ORDERED or PARTIALLY_RECEIVED)
    2. For each item input:
       - Find matching PO item by id
       - Validate: input.received_quantity > 0
       - Validate: item.received_quantity + input.received_quantity <= item.quantity (no over-receive)
       - Update item.received_quantity += input.received_quantity
       - Set item.received_at = now (if first receipt for this item)
       - If create_asset and item.asset_type → call ReceiptAssetService, set item.linked_asset_id
       - If link_asset_id → set item.linked_asset_id
    3. Call `po.receive()` — checks all items, updates status:
       - All fully received → RECEIVED
       - Some not fully received → PARTIALLY_RECEIVED
    4. If status changed to RECEIVED → emit `po.received` notification
    5. Save

### 3. ClosePurchaseOrderCommand + handler
- [x] Create `src/procurement_bc/purchase_order/application/commands/close_po.py`
  - `ClosePurchaseOrderCommand(Command)`: purchase_order_id, company_id, performed_by
  - Handler: find PO, validate RECEIVED or PARTIALLY_RECEIVED, call `po.close()`, save

---

## Phase 2: Notifications

### 4. po.received notification
- [x] Edit `src/notification_bc/notification/domain/enums.py`
  - Add `po.received` event type
- [x] Edit `src/notification_bc/notification/application/services/notification_subscriber.py`
  - Handle po.received: "PO {number} — all items received from {vendor}"
- [x] Edit `src/notification_bc/notification/application/services/target_resolver.py`
  - po.received → PO creator + all admins

---

## Phase 3: HTTP Layer

### 5. Receipt schemas
- [x] Edit `adapters/http/api/purchase_orders/schemas.py`
  - Add `ReceiveItemRequest`: item_id, received_quantity (ge=1), create_asset (bool, default false), link_asset_id?
  - Add `ReceiveRequest`: items[] (min 1)

### 6. Receive + close endpoints
- [x] Edit `adapters/http/api/purchase_orders/routers.py`
  - `POST /{id}/receive` — record goods receipt (technician+)
    - Parse ReceiveRequest body
    - Execute ReceiveItemsCommand
    - Return updated PO with items
    - Handle errors: not found → 404, invalid status → 409, over-receive → 422
  - `POST /{id}/close` — close PO (technician+)
    - Execute ClosePurchaseOrderCommand
    - Return updated PO
    - Handle errors: not found → 404, invalid status → 409

---

## Phase 4: Frontend

### 7. Receipt UI on PO detail page
- [x] Edit `web/app/src/pages/admin/PurchaseOrderDetailPage.tsx`
  - Receipt section (visible when PO is ORDERED or PARTIALLY_RECEIVED):
    - Table: item description, ordered qty, received qty, remaining qty
    - Progress bar per item (received / ordered)
    - Input field for "Receive" quantity per item
    - Checkbox: "Create Asset" (shown when item has asset_type)
    - Submit receipt button
  - Close button (visible when PO is RECEIVED or PARTIALLY_RECEIVED)
  - After receipt, show updated quantities immediately (invalidate query)
- [x] Edit `web/app/src/locales/en.ts` — add ~15 receipt keys
- [x] Edit `web/app/src/locales/es.ts` — add ~15 receipt keys

---

## Phase 5: Tests

### 8. Unit tests
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_receive.py`
  - Partial receipt → PARTIALLY_RECEIVED
  - Full receipt → RECEIVED
  - Multiple receipts across sessions (partial → partial → full)
  - Over-receive validation → error
  - Receipt with asset creation → asset created, linked_asset_id set
  - Receipt with link_asset_id → linked_asset_id set
  - Invalid status (DRAFT) → error
  - Zero received_quantity → error
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_close.py`
  - Close from RECEIVED → CLOSED
  - Close from PARTIALLY_RECEIVED → CLOSED
  - Close from invalid status (ORDERED) → error
- [x] Create `tests/unit/procurement_bc/purchase_order/application/services/test_receipt_asset.py`
  - Create asset from PO item with correct fields
- ~12 unit tests

### 9. Integration tests
- [x] Edit `tests/integration/test_purchase_orders_endpoints.py`
  - POST receive — partial receipt → 200, status PARTIALLY_RECEIVED
  - POST receive — full receipt → 200, status RECEIVED
  - POST receive — with asset creation → asset created
  - POST receive — over-receive → 422
  - POST receive — wrong status → 409
  - POST close → 200, status CLOSED
- ~6 integration tests

---

## Phase 6: Verification

### 10. Verify
- [x] Lint passes: `make lint`
- [x] Unit tests pass: `make test`
- [x] Integration tests pass: `make test-integration`
- [x] Frontend builds: `cd web/app && npm run build`
- [x] TypeScript compiles: `cd web/app && npx tsc --noEmit`
- [x] Full receipt flow works: ORDERED → receive → PARTIALLY_RECEIVED → receive → RECEIVED → close → CLOSED

---

## Dependency Graph

```
ReceiptAssetService (1) — depends on Asset repo from asset_bc
  └── ReceiveItemsCommand (2) — depends on service + F0 PO entity/repo
  └── ClosePOCommand (3) — depends on F0 PO entity/repo
        └── Notifications (4) — depends on commands
              └── Schemas (5) — depends on entity types
                    └── Endpoints (6) — depends on schemas + commands
                          └── Frontend (7) — depends on API
                                └── Tests (8-9) — after all code
```

## Execution Order

**Batch 1:** Task 1 (ReceiptAssetService)
**Batch 2 (Parallel):** Tasks 2-3 (commands)
**Batch 3:** Task 4 (notifications)
**Batch 4:** Task 5 (schemas)
**Batch 5:** Task 6 (endpoints)
**Batch 6:** Task 7 (frontend)
**Batch 7 (Parallel):** Tasks 8-9 (tests)
**Batch 8:** Task 10 (verification)

## Final Checklist

- [x] All tasks completed
- [x] All tests passing (unit + integration)
- [x] mypy passes
- [x] Frontend builds
- [x] Receive + close endpoints working
- [x] Partial and full receipt flows tested
- [x] Asset creation from receipt works
- [x] po.received notification fires
