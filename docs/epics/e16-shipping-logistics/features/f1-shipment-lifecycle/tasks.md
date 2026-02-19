# Tasks: F1 — Shipment Lifecycle & Notifications

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 16
**Estimated Complexity:** H

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Notifications - EventType | 1 | S |
| Notifications - TargetResolver | 1 | S |
| Application - DeliveryAssetService | 1 | M |
| Application - Commands (9) | 1 | H |
| Application - Queries (5) | 1 | M |
| HTTP - Schemas | 1 | S |
| HTTP - Dependencies | 1 | S |
| HTTP - Shipments Router | 1 | M |
| HTTP - My Router (shipments) | 1 | S |
| HTTP - Dashboard Router (shipments) | 1 | S |
| HTTP - App Registration | 1 | S |
| Tests - Unit Commands | 1 | M |
| Tests - Unit Queries | 1 | S |
| Tests - Integration | 1 | M |
| Tests - Cross-BC | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Notifications

### 1. Add shipment EventType values
- [x] Edit `src/notification_bc/notification/domain/enums.py`
  - Add 5 values to `EventType` enum:
    - `SHIPMENT_CREATED = "shipment.created"`
    - `SHIPMENT_DISPATCHED = "shipment.dispatched"`
    - `SHIPMENT_DELIVERED = "shipment.delivered"`
    - `SHIPMENT_FAILED = "shipment.failed"`
    - `SHIPMENT_CANCELLED = "shipment.cancelled"`

### 2. Add shipment target resolvers
- [x] Edit `src/notification_bc/notification/application/services/target_resolver.py`
  - Add resolver methods for each shipment event:
    - `_resolve_shipment_created` → recipient_user_id from payload (if set)
    - `_resolve_shipment_dispatched` → recipient_user_id from payload
    - `_resolve_shipment_delivered` → recipient_user_id (outbound) or created_by (inbound)
    - `_resolve_shipment_failed` → created_by from payload
    - `_resolve_shipment_cancelled` → recipient_user_id from payload (if dispatched)
  - Register all 5 in the resolver dispatch dict

---

## Phase 2: Application Layer — Services

### 3. Create DeliveryAssetService
- [x] Create `src/shipping_bc/shipment/application/services/__init__.py`
- [x] Create `src/shipping_bc/shipment/application/services/delivery_asset_service.py`
  - **`DeliveryAssetService`** class:
    - `__init__(self, asset_repo: AssetRepositoryInterface)`
    - `update_assets_on_delivery(self, shipment: Shipment) -> None`:
      - If outbound + employee_home → assign each asset to recipient_user_id
      - If inbound → mark each asset IN_STOCK
      - If outbound + office → no change (relocated)
      - If outbound + vendor → no change (stays IN_REPAIR)
    - Private `_assign_assets(self, shipment)` — calls `asset.assign()` for each
    - Private `_mark_assets_in_stock(self, shipment)` — calls `asset.change_status(IN_STOCK)`

---

## Phase 3: Application Layer — Commands

### 4. Create all shipment commands
- [x] Create `src/shipping_bc/shipment/application/commands/create_shipment.py`
- [x] Create `src/shipping_bc/shipment/application/commands/dispatch_shipment.py`
- [x] Create `src/shipping_bc/shipment/application/commands/mark_in_transit.py`
- [x] Create `src/shipping_bc/shipment/application/commands/deliver_shipment.py`
- [x] Create `src/shipping_bc/shipment/application/commands/fail_shipment.py`
- [x] Create `src/shipping_bc/shipment/application/commands/cancel_shipment.py`
- [x] Create `src/shipping_bc/shipment/application/commands/update_shipment.py`
- [x] Create `src/shipping_bc/shipment/application/commands/create_return_shipment.py`
- [x] Create `src/shipping_bc/shipment/application/commands/modify_shipment_items.py`

---

## Phase 4: Application Layer — Queries

### 5. Create all shipment queries
- [x] Create `src/shipping_bc/shipment/application/queries/list_shipments.py`
- [x] Create `src/shipping_bc/shipment/application/queries/get_shipment.py`
- [x] Create `src/shipping_bc/shipment/application/queries/shipments_by_asset.py`
- [x] Create `src/shipping_bc/shipment/application/queries/my_shipments.py`
- [x] Create `src/shipping_bc/shipment/application/queries/shipment_dashboard.py`

---

## Phase 5: HTTP Layer

### 6. Create shipment schemas
- [x] Create `adapters/http/api/shipments/__init__.py`
- [x] Create `adapters/http/api/shipments/schemas.py`
  - Request schemas: `CreateShipmentRequest`, `DispatchShipmentRequest`, `FailShipmentRequest`, `CancelShipmentRequest`, `DeliverShipmentRequest`, `UpdateShipmentRequest`, `CreateReturnRequest`, `ModifyItemsRequest`
  - Response schemas: `ShipmentItemResponse`, `ShipmentResponse` (with item_count computed field), `ShipmentDashboardResponse`
  - All using Pydantic `BaseModel` with primitive types

### 7. Create shipment dependencies
- [x] Create `adapters/http/api/shipments/dependencies.py`
  - `get_shipment_repo(db)` → `ShipmentRepository(db)`
  - `get_delivery_asset_service(db)` → `DeliveryAssetService(AssetRepository(db))`

### 8. Create shipments router
- [x] Create `adapters/http/api/shipments/routers.py`
  - 12 endpoints:
    - `POST /` — create shipment (201)
    - `GET /` — list shipments with filters
    - `GET /{id}` — get shipment detail
    - `PATCH /{id}` — update tracking/notes
    - `POST /{id}/dispatch` — dispatch
    - `POST /{id}/in-transit` — mark in transit
    - `POST /{id}/deliver` — mark delivered (calls DeliveryAssetService)
    - `POST /{id}/fail` — mark failed
    - `POST /{id}/cancel` — cancel
    - `POST /{id}/return` — create return shipment (201)
    - `GET /by-asset/{asset_id}` — asset shipment history
    - `PATCH /{id}/items` — modify items (DRAFT only)
  - Each endpoint: instantiates handler, calls handler.handle(), queries result, publishes event via EventBus
  - Error handling: ValueError → 422, InvalidShipmentStatusTransitionError → 409, not found → 404

### 9. Add my/shipments endpoint
- [x] Edit `adapters/http/api/my/routers.py`
  - Add `GET /api/v1/my/shipments` endpoint
  - Uses `MyShipmentsQuery` with `current_user.id` as `recipient_user_id`
  - Returns paginated list

### 10. Add dashboard/shipments endpoint
- [x] Edit `adapters/http/api/dashboard/routers.py`
  - Add `GET /api/v1/dashboard/shipments/summary` endpoint (admin+)
  - Uses `ShipmentDashboardQuery` with `current_user.company_id`
  - Returns shipment summary with active_by_status, recent_deliveries, failed_count

### 11. Register shipments router
- [x] Edit `app.py`
  - Import and include `shipments_router`

---

## Phase 6: Tests

### 12. Unit tests — Commands
- [x] Create `tests/unit/shipping_bc/shipment/application/__init__.py`
- [x] Create `tests/unit/shipping_bc/shipment/application/commands/__init__.py`
- [x] Create `tests/unit/shipping_bc/shipment/application/commands/test_create.py`
  - `test_create_shipment_saves_draft` — valid data → DRAFT status
  - `test_create_validates_asset_conflict` — asset in active shipment → AssetConflictError
  - `test_create_validates_direction` — invalid direction → ValueError
  - `test_create_return_links_original` — return_for_shipment_id set correctly
  - `test_create_return_original_not_found` — raises ShipmentNotFoundError
- [x] Create `tests/unit/shipping_bc/shipment/application/commands/test_dispatch.py`
  - `test_dispatch_sets_carrier_and_tracking` — updates fields, DISPATCHED
  - `test_dispatch_without_carrier_raises` — carrier None → ValueError
  - `test_dispatch_from_delivered_raises` — InvalidShipmentStatusTransitionError
- [x] Create `tests/unit/shipping_bc/shipment/application/commands/test_deliver.py`
  - `test_deliver_from_dispatched` — DELIVERED, sets delivered_at
  - `test_deliver_from_in_transit` — DELIVERED
  - `test_deliver_calls_asset_service_employee_home` — DeliveryAssetService called
  - `test_deliver_calls_asset_service_for_office` — service called (decides internally)
- [x] Create `tests/unit/shipping_bc/shipment/application/commands/test_transitions.py`
  - `test_mark_in_transit` — DISPATCHED → IN_TRANSIT
  - `test_fail_with_reason` — sets failure_reason
  - `test_cancel_with_reason` — sets cancellation_reason
  - `test_cancel_from_terminal_raises` — error
- [x] Create `tests/unit/shipping_bc/shipment/application/commands/test_items.py`
  - `test_modify_add_items_in_draft` — adds items
  - `test_modify_remove_items_in_draft` — removes items
  - `test_modify_in_dispatched_raises` — error
  - `test_modify_validates_asset_conflict` — active shipment → error
- [x] Create `tests/unit/shipping_bc/shipment/application/commands/test_update.py`
  - `test_update_tracking_fields` — updates non-None fields
  - `test_update_notes` — updates notes only

### 13. Unit tests — Queries
- [x] Create `tests/unit/shipping_bc/shipment/application/queries/__init__.py`
- [x] Create `tests/unit/shipping_bc/shipment/application/queries/test_queries.py`
  - `test_list_returns_paginated` — returns tuple(list, count)
  - `test_get_returns_shipment` — found
  - `test_get_not_found_raises` — raises ShipmentNotFoundError
  - `test_by_asset_returns_history` — list of shipments
  - `test_my_shipments_filters_by_recipient` — filtered by recipient_user_id
  - `test_dashboard_returns_summary` — counts + lists

### 14. Integration tests
- [x] Create `tests/integration/test_shipments_endpoints.py`
  - `test_create_shipment_returns_201`
  - `test_list_shipments_returns_200`
  - `test_get_shipment_returns_200`
  - `test_update_shipment_returns_200`
  - `test_dispatch_shipment_returns_200`
  - `test_mark_in_transit_returns_200`
  - `test_deliver_shipment_returns_200`
  - `test_fail_shipment_returns_200`
  - `test_cancel_shipment_returns_200`
  - `test_create_return_returns_201`
  - `test_shipments_by_asset_returns_200`
  - `test_modify_items_returns_200`
  - `test_my_shipments_returns_200`
  - `test_dashboard_shipments_returns_200`
  - `test_create_with_asset_conflict_returns_409`
  - `test_dispatch_without_tracking_returns_422`
  - `test_invalid_transition_returns_409`

### 15. Cross-BC integration test
- [x] Add to `tests/integration/test_shipments_endpoints.py`:
  - `test_deliver_outbound_employee_assigns_assets` — verify asset status changes to ASSIGNED after delivery

---

## Phase 7: Verification

### 16. Verify
- [x] Lint passes (flake8 clean on new files)
- [x] Unit tests pass: 977 passed (53 shipping + 924 existing)
- [x] Integration tests pass: 18 passed
- [x] All new imports and registrations correct

---

## Dependency Graph

```
EventType additions (1)
  └── TargetResolver (2)
        └── DeliveryAssetService (3)
              └── Commands (4) — uses service + repos
                    └── Queries (5) — uses repos
                          └── Schemas (6)
                                └── Dependencies (7)
                                      └── Router (8) + My Router (9) + Dashboard Router (10)
                                            └── App Registration (11)
                                                  └── Unit Tests Commands (12)
                                                        └── Unit Tests Queries (13)
                                                              └── Integration Tests (14 + 15)
                                                                    └── Verification (16)
```

## Execution Order

**Batch 1 (Parallel):** Tasks 1 + 2 (notification enums + resolver)
**Batch 2:** Task 3 (DeliveryAssetService)
**Batch 3 (Parallel):** Tasks 4 + 5 (commands + queries)
**Batch 4 (Parallel):** Tasks 6 + 7 (schemas + dependencies)
**Batch 5 (Parallel):** Tasks 8 + 9 + 10 (routers)
**Batch 6:** Task 11 (app registration)
**Batch 7 (Parallel):** Tasks 12 + 13 (unit tests)
**Batch 8:** Tasks 14 + 15 (integration tests)
**Batch 9:** Task 16 (verification)

## Final Checklist

- [x] All tasks completed
- [x] 9 command handlers
- [x] 5 query handlers
- [x] 1 cross-BC service (DeliveryAssetService)
- [x] 5 EventType values added
- [x] 5 TargetResolver methods added
- [x] 14 API endpoints (12 shipment + 1 my/shipments + 1 dashboard/shipments/summary)
- [x] 28 unit tests (commands + queries)
- [x] 18 integration tests
- [x] All tests passing
