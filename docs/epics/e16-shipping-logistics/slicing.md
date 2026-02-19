# Slicing: E16 - Shipping & Logistics

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-18
**Total Features:** 4

## Slicing Rationale

E16 introduces a new bounded context (`shipping_bc`) with 2 subdomains (`shipment` and `address`), 3 database tables, 20 API endpoints, 5 notification event types, cross-BC asset status updates, and frontend pages. The slicing follows the established bottom-up pattern from E14 and E15: F0 builds all domain entities, enums, migrations, and repositories (no API). F1 delivers the core shipment lifecycle with state machine, notifications, my/shipments, dashboard, and cross-BC asset side effects. F2 adds address management as an independent vertical. F3 delivers all frontend pages.

Unlike E15 which had a Celery tasks feature (F3), E16 has no scheduled tasks — shipment status updates are manual. This reduces the epic to 4 features instead of 5.

## Dependency Graph

```text
F0: Shipping Domain & Infrastructure (entities, enums, migrations, repos for shipment + address)
 ├── F1: Shipment Lifecycle & Notifications (CRUD, state machine, events, my/shipments, dashboard, asset side effects)
 ├── F2: Address Management (CRUD, 6 endpoints)
 └── F3: Frontend (shipment pages, address pages, collateral edits, i18n)
      └── depends on F1 + F2
```

## Features Summary

| # | Feature | Covers | Complexity | Depends | Status |
|---|---------|--------|------------|---------|--------|
| F0 | Shipping Domain & Infrastructure | Entities, enums, migrations, repos, domain tests | Medium | None | Done |
| F1 | Shipment Lifecycle & Notifications | US-E16-001, US-E16-002, US-E16-004, US-E16-005, US-E16-006, US-E16-007, US-E16-008 | High | F0 | Done |
| F2 | Address Management | US-E16-003 | Medium | F0 | Done |
| F3 | Frontend | All pages, routing, sidebar, dashboard, i18n | High | F1, F2 | Done |

---

## F0: Shipping Domain & Infrastructure

**Scope:** Create the entire `shipping_bc` bounded context — domain entities, enums, repository interfaces, SQLAlchemy models, migrations, repository implementations. Covers both `shipment` and `address` subdomains. Pure backend — no API endpoints, no frontend.

### Domain Layer
- `ShipmentStatus` enum with 6 values and `VALID_TRANSITIONS` dict
- `ShipmentDirection` enum (OUTBOUND, INBOUND)
- `DestinationType` enum (EMPLOYEE_HOME, OFFICE, VENDOR)
- `Shipment` entity with state machine methods (dispatch, mark_in_transit, deliver, fail, cancel)
- `ShipmentItem` entity (child of Shipment)
- `ShippingAddress` entity with soft-delete
- Repository interfaces for Shipment and ShippingAddress
- `InvalidShipmentStatusTransitionError` exception

### Infrastructure Layer
- 3 migrations: `shipments`, `shipment_items`, `shipping_addresses`
- 3 SQLAlchemy models (all using `Mapped[type]` annotations)
- 2 repository implementations with tenant isolation (`company_id` scoping)

### Tests
- Unit: shipment state machine transitions (valid + invalid), entity creation, item management
- ~18 tests

### Files

| File | Action |
|------|--------|
| `src/shipping_bc/shipment/domain/entities.py` | Create — Shipment + ShipmentItem |
| `src/shipping_bc/shipment/domain/enums.py` | Create — ShipmentStatus, ShipmentDirection, DestinationType |
| `src/shipping_bc/shipment/domain/repository.py` | Create — ShipmentRepositoryInterface |
| `src/shipping_bc/address/domain/entities.py` | Create — ShippingAddress |
| `src/shipping_bc/address/domain/repository.py` | Create — ShippingAddressRepositoryInterface |
| `src/shipping_bc/shipment/infrastructure/models.py` | Create — ShipmentModel + ShipmentItemModel |
| `src/shipping_bc/address/infrastructure/models.py` | Create — ShippingAddressModel |
| `src/shipping_bc/shipment/infrastructure/repository.py` | Create — ShipmentRepository |
| `src/shipping_bc/address/infrastructure/repository.py` | Create — ShippingAddressRepository |
| `alembic/versions/` | Create — 3 migrations |
| `tests/unit/shipping_bc/shipment/domain/test_entities.py` | Create |
| `tests/unit/shipping_bc/address/domain/test_entities.py` | Create |

---

## F1: Shipment Lifecycle & Notifications

**Scope:** Full shipment lifecycle — create, dispatch, in_transit, deliver, fail, cancel, update, return, modify items, list, get, by-asset history, my/shipments, dashboard summary. Notification events for dispatch, delivery, failure, cancellation. Cross-BC asset status updates on delivery.

### Application Layer
- `CreateShipmentCommand` + handler (validates asset ownership, checks active shipment conflict)
- `DispatchShipmentCommand` + handler (DRAFT → DISPATCHED, requires carrier + tracking)
- `MarkInTransitCommand` + handler (DISPATCHED → IN_TRANSIT)
- `DeliverShipmentCommand` + handler (DISPATCHED/IN_TRANSIT → DELIVERED, asset side effects)
- `FailShipmentCommand` + handler (DISPATCHED/IN_TRANSIT → FAILED, requires reason)
- `CancelShipmentCommand` + handler (any non-terminal → CANCELLED, requires reason)
- `UpdateShipmentCommand` + handler (PATCH tracking, notes)
- `CreateReturnShipmentCommand` + handler (creates inbound from outbound, links via return_for_shipment_id)
- `ModifyShipmentItemsCommand` + handler (add/remove items in DRAFT only)
- `ListShipmentsQuery` + handler (filters: status, direction, destination_type, asset_id, request_id, po_id)
- `GetShipmentQuery` + handler
- `ShipmentsByAssetQuery` + handler (asset shipment history)
- `MyShipmentsQuery` + handler (employee's own shipments via recipient_user_id)
- `ShipmentDashboardQuery` + handler (active counts, recent deliveries, failed count)

### HTTP Layer
- Router: 14 endpoints on `/api/v1/shipments` + 1 on `/api/v1/my/shipments` + 1 on `/api/v1/dashboard/shipments`
- Schemas: request/response models for all endpoints
- Dependencies: `get_shipment_repo`, `get_asset_repo`

### Notifications
- Add 5 EventType values: `SHIPMENT_CREATED`, `SHIPMENT_DISPATCHED`, `SHIPMENT_DELIVERED`, `SHIPMENT_FAILED`, `SHIPMENT_CANCELLED`
- Add `ShipmentEventFactory` for creating domain events
- Add 5 resolver methods to TargetResolver (recipient ↔ technician routing)

### Cross-BC Impact
- On outbound delivery to employee_home: mark linked assets as ASSIGNED
- On inbound delivery (return from repair): mark linked assets as IN_STOCK
- On outbound delivery to office: assets remain IN_STOCK (relocated)
- On outbound delivery to vendor: assets remain IN_REPAIR

### Tests
- Unit: all command handlers, state transitions, overlap detection, asset side effects (~25 tests)
- Integration: all 16 endpoints (~18 tests)

### Files

| File | Action |
|------|--------|
| `src/shipping_bc/shipment/application/commands/create_shipment.py` | Create |
| `src/shipping_bc/shipment/application/commands/dispatch_shipment.py` | Create |
| `src/shipping_bc/shipment/application/commands/mark_in_transit.py` | Create |
| `src/shipping_bc/shipment/application/commands/deliver_shipment.py` | Create |
| `src/shipping_bc/shipment/application/commands/fail_shipment.py` | Create |
| `src/shipping_bc/shipment/application/commands/cancel_shipment.py` | Create |
| `src/shipping_bc/shipment/application/commands/update_shipment.py` | Create |
| `src/shipping_bc/shipment/application/commands/create_return_shipment.py` | Create |
| `src/shipping_bc/shipment/application/commands/modify_shipment_items.py` | Create |
| `src/shipping_bc/shipment/application/queries/list_shipments.py` | Create |
| `src/shipping_bc/shipment/application/queries/get_shipment.py` | Create |
| `src/shipping_bc/shipment/application/queries/shipments_by_asset.py` | Create |
| `src/shipping_bc/shipment/application/queries/my_shipments.py` | Create |
| `src/shipping_bc/shipment/application/queries/shipment_dashboard.py` | Create |
| `adapters/http/api/shipments/` | Create — routers, schemas, dependencies |
| `app.py` | Edit — register shipment router |
| `adapters/http/api/my/routers.py` | Edit — add my/shipments endpoint |
| `adapters/http/api/dashboard/routers.py` | Edit — add dashboard/shipments endpoint |
| `src/notification_bc/notification/domain/enums.py` | Edit — add 5 shipment event types |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit — add 5 shipment resolvers |
| `tests/unit/shipping_bc/shipment/application/commands/` | Create — command tests |
| `tests/unit/shipping_bc/shipment/application/queries/` | Create — query tests |
| `tests/integration/test_shipments_endpoints.py` | Create |

---

## F2: Address Management

**Scope:** Full shipping address lifecycle — create, list, get, update, deactivate, by-user lookup. Independent from shipment CRUD (both depend on F0).

### Application Layer
- `CreateAddressCommand` + handler
- `UpdateAddressCommand` + handler
- `DeactivateAddressCommand` + handler (soft-delete)
- `ListAddressesQuery` + handler (filters: user_id, is_office, is_active)
- `GetAddressQuery` + handler
- `AddressesByUserQuery` + handler

### HTTP Layer
- Router: 6 endpoints on `/api/v1/addresses`
- Schemas: `AddressCreateRequest`, `AddressUpdateRequest`, `AddressResponse`
- Dependencies: `get_address_repo`

### Tests
- Unit: create/update/deactivate handlers (~6 tests)
- Integration: all 6 endpoints (~8 tests)

### Files

| File | Action |
|------|--------|
| `src/shipping_bc/address/application/commands/create_address.py` | Create |
| `src/shipping_bc/address/application/commands/update_address.py` | Create |
| `src/shipping_bc/address/application/commands/deactivate_address.py` | Create |
| `src/shipping_bc/address/application/queries/list_addresses.py` | Create |
| `src/shipping_bc/address/application/queries/get_address.py` | Create |
| `src/shipping_bc/address/application/queries/addresses_by_user.py` | Create |
| `adapters/http/api/addresses/` | Create — routers, schemas, dependencies |
| `app.py` | Edit — register address router |
| `tests/unit/shipping_bc/address/application/commands/` | Create — command tests |
| `tests/unit/shipping_bc/address/application/queries/` | Create — query tests |
| `tests/integration/test_addresses_endpoints.py` | Create |

---

## F3: Frontend — Shipment & Address UX

**Scope:** All frontend pages and components for shipping and address management. Shipment list, detail, create form, address management page, asset detail shipment history, request detail shipments section, dashboard shipments card, routing, sidebar, i18n.

### Frontend Pages
- `ShipmentsPage.tsx` — Technician/admin list view
  - Table with status, direction, destination, carrier, tracking, dates
  - Filters: status, direction, destination_type
  - Create button opens form
  - Click row to navigate to detail
- `ShipmentDetailPage.tsx` — Full shipment detail
  - Status timeline (DRAFT → DISPATCHED → IN_TRANSIT → DELIVERED)
  - Shipment info card (carrier, tracking, addresses, notes)
  - Items list (linked assets with names)
  - Action buttons based on current status (dispatch, deliver, fail, cancel, create return)
  - Tracking link (clickable URL)
- `ShipmentCreatePage.tsx` — New shipment form
  - Direction selector (outbound/inbound)
  - Destination type selector
  - Address picker (select from existing or create new inline)
  - Asset selector (multi-select from company assets)
  - Carrier, tracking number, tracking URL fields
  - Optional request/PO link
  - Notes field
- `AddressesPage.tsx` — Address management
  - Table with label, recipient, city, type (office/employee)
  - Create/edit/deactivate actions
  - Filter by type (office/employee/all)
- `MyShipmentsPage.tsx` — Employee view of own shipments
  - List with status, carrier, tracking (clickable), dates
  - Read-only view

### Collateral Edits
- `AssetDetailPage.tsx` — Add "Shipment History" section
- `RequestDetailPage.tsx` — Show linked shipments
- `DashboardPage.tsx` — Add active shipments card

### Routing & Navigation
- Add 4 lazy imports and routes: ShipmentsPage, ShipmentDetailPage, ShipmentCreatePage, AddressesPage
- Add 1 employee route: MyShipmentsPage
- Sidebar: add "Shipments" and "Addresses" for technician+, "My Shipments" for employee

### i18n
- ~80 keys for both EN and ES covering all pages, enums, actions

### Tests
- Frontend build: `npm run build`
- TypeScript compilation: `npx tsc --noEmit`

### Files

| File | Action |
|------|--------|
| `web/app/src/pages/technician/ShipmentsPage.tsx` | Create |
| `web/app/src/pages/technician/ShipmentDetailPage.tsx` | Create |
| `web/app/src/pages/technician/ShipmentCreatePage.tsx` | Create |
| `web/app/src/pages/technician/AddressesPage.tsx` | Create |
| `web/app/src/pages/employee/MyShipmentsPage.tsx` | Create |
| `web/app/src/pages/technician/AssetDetailPage.tsx` | Edit — add shipment history |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Edit — add linked shipments |
| `web/app/src/pages/admin/DashboardPage.tsx` | Edit — add shipments card |
| `web/app/src/types/index.ts` | Edit — add Shipment, ShipmentItem, ShippingAddress types |
| `web/app/src/router.tsx` | Edit — add 5 routes |
| `web/app/src/components/layout/Sidebar.tsx` | Edit — add 3 nav items |
| `web/app/src/locales/en.ts` | Edit — ~80 keys |
| `web/app/src/locales/es.ts` | Edit — ~80 keys |

---

## Recommended Implementation Order

1. **F0** — Shipping Domain & Infrastructure (~1 session): entities, enums, migrations, repos, domain tests
2. **F1** — Shipment Lifecycle & Notifications (~2 sessions): all command/query handlers, 16 endpoints, events, cross-BC, tests. Core feature.
3. **F2** — Address Management (~1 session): address CRUD, 6 endpoints, tests. Can parallelize with F1.
4. **F3** — Frontend (~2 sessions): all pages, routing, sidebar, collateral edits, i18n

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1/F2 → F3)
- [x] Each feature independently deployable (after dependencies)
- [x] Vertical slices — F1 delivers full shipment lifecycle, F2 delivers full address management
- [x] Shared foundation identified (F0)
- [x] No overlapping scope — each feature owns its files
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered (8 user stories, 6 use cases, 20 endpoints)

## Risk Notes

- **Cross-BC asset updates:** Delivery triggers asset status changes. Follow E14's `ReceiptAssetService` pattern — use a service class to isolate the cross-BC dependency. Keep coupling minimal.
- **Active shipment validation:** Checking that an asset isn't in another active shipment requires querying across all shipments. Use a repo method with `status IN ('draft', 'dispatched', 'in_transit')` filter. Consider a unique partial index for production optimization.
- **Return shipment linking:** `return_for_shipment_id` creates a logical chain. The return can have different items than the original — design the UI to pre-fill but allow modification.
- **Address reuse by E22:** `ShippingAddress` entity is designed with `user_id` FK and `is_office` flag to serve E22's onboarding needs. No changes should be needed when E22 is implemented.
