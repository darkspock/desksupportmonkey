# Tasks: F3 — Frontend — Shipment & Address UX

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 14
**Estimated Complexity:** H

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Types | 1 | S |
| i18n - English | 1 | S |
| i18n - Spanish | 1 | S |
| Pages - ShipmentsPage | 1 | M |
| Pages - ShipmentDetailPage | 1 | H |
| Pages - ShipmentCreatePage | 1 | H |
| Pages - AddressesPage | 1 | M |
| Pages - MyShipmentsPage | 1 | S |
| Collateral - Asset Detail | 1 | S |
| Collateral - Request Detail | 1 | S |
| Collateral - Dashboard | 1 | S |
| Routing & Sidebar | 1 | S |
| Build Verification | 1 | S |
| Progress Tracking | 1 | S |

---

## Phase 1: Types & i18n

### 1. Add TypeScript types
- [x] Edit `web/app/src/types/index.ts`
  - Add `ShipmentItem` interface: id, shipment_id, asset_id, notes?
  - Add `Shipment` interface: id, company_id, direction, destination_type, status, addresses, carrier, tracking, items, dates, etc.
  - Add `ShippingAddress` interface: id, company_id, label, street lines, city, state, postal_code, country, phone, user_id, is_office, is_active, timestamps
  - Add `ShipmentDashboard` interface: active_by_status, recent_deliveries, failed_count

### 2. Add English i18n keys
- [x] Edit `web/app/src/locales/en.ts`
  - Add ~80 keys organized by:
    - `nav.*` — shipments, addresses, my_shipments
    - `page.shipments.*` — list page (title, new, empty, filters)
    - `page.shipment_detail.*` — detail page (info cards, actions)
    - `page.shipment_create.*` — create form (direction, destination, assets, carrier, etc.)
    - `page.addresses.*` — address management (title, new, fields, actions)
    - `page.my_shipments.*` — employee view
    - `page.asset_detail.shipment_history` + `no_shipments`
    - `page.request_detail.shipments` + `create_shipment`
    - `page.dashboard.active_shipments` + `failed_shipments` + `recent_deliveries`
    - `enum.shipment_status.*` — 6 status labels
    - `enum.shipment_direction.*` — outbound, inbound
    - `enum.destination_type.*` — employee_home, office, vendor
    - `confirm.*` — dispatch, cancel, fail, deactivate
    - `toast.*` — success messages

### 3. Add Spanish i18n keys
- [x] Edit `web/app/src/locales/es.ts`
  - Same ~80 keys in Spanish
  - Use Unicode escapes for accented characters (e.g., `\u00ed` for í, `\u00f3` for ó, `\u00f1` for ñ)
  - Key translations:
    - Shipments → Env\u00edos
    - Addresses → Direcciones
    - Draft → Borrador
    - Dispatched → Despachado
    - In Transit → En tr\u00e1nsito
    - Delivered → Entregado
    - Failed → Fallido
    - Cancelled → Cancelado
    - Outbound → Salida
    - Inbound → Entrada
    - Carrier → Transportista
    - Tracking → Seguimiento

---

## Phase 2: Pages

### 4. Create ShipmentsPage (list)
- [x] Create `web/app/src/pages/technician/ShipmentsPage.tsx`
  - Fetch `GET /api/v1/shipments` with useQuery, pagination params
  - Table columns: status (Badge), direction badge, destination type, carrier, tracking, recipient, item_count, dispatched_at
  - Filter dropdowns: status (all + 6 values), direction (all/outbound/inbound), destination_type
  - Pagination component
  - "New Shipment" button → `/shipments/new`
  - Row click → `/shipments/{id}`
  - Status badge color mapping: draft=gray, dispatched=blue, in_transit=yellow, delivered=green, failed=red, cancelled=gray

### 5. Create ShipmentDetailPage
- [x] Create `web/app/src/pages/technician/ShipmentDetailPage.tsx`
  - Route param: `id` from `useParams()`
  - Fetch `GET /api/v1/shipments/{id}` with useQuery
  - Fetch origin/destination addresses by ID (2 additional queries)
  - Header: direction + destination_type + status badges
  - Cards:
    - **Shipping Info:** carrier, tracking_number (link if tracking_url), dispatched_at, delivered_at
    - **Addresses:** formatted origin + destination
    - **Linked Records:** links to request, PO, return-for shipment (if any)
    - **Notes:** notes, failure_reason, cancellation_reason
  - Items table: asset_id (link to asset), notes
  - Action buttons by status:
    - DRAFT: Dispatch (with inline carrier/tracking form), Cancel (ConfirmDialog), Edit Items
    - DISPATCHED: In Transit, Deliver, Fail (ConfirmDialog with reason), Cancel (ConfirmDialog with reason)
    - IN_TRANSIT: Deliver, Fail, Cancel
    - DELIVERED: Create Return (→ /shipments/new?return_for={id})
    - FAILED/CANCELLED: none
  - useMutation for each action, invalidateQueries on success, showToast

### 6. Create ShipmentCreatePage
- [x] Create `web/app/src/pages/technician/ShipmentCreatePage.tsx`
  - Direction radio: outbound / inbound
  - Destination type radio: employee_home / office / vendor
  - Address picker:
    - Fetch `GET /api/v1/addresses?is_active=true` with useQuery
    - Dropdown with existing addresses (formatted: label — city, state)
    - "Create New Address" expandable section with inline form
    - Auto-filter by user when employee_home selected
  - Asset multi-select:
    - Fetch `GET /api/v1/assets?page_size=100` with useQuery
    - Searchable list with checkboxes
    - Selected assets shown as tags with remove button
  - Carrier, tracking_number, tracking_url text inputs
  - Optional: request_id selector (if URL has ?request_id), po_id selector
  - Recipient name + recipient_user_id (auto-populated from address.user_id)
  - Notes textarea
  - "Save as Draft" button → POST create, on success navigate to detail
  - Handle `?return_for={id}` URL param: pre-fill as return shipment (direction=inbound, origin=original destination)

### 7. Create AddressesPage
- [x] Create `web/app/src/pages/technician/AddressesPage.tsx`
  - Fetch `GET /api/v1/addresses` with useQuery, pagination
  - Table: label, recipient_name, city/state/postal_code, country, type badge (Office/Employee), active badge
  - Filter: type (all/office/employee), active (all/active/inactive)
  - "New Address" button → opens modal/inline form
  - Create/edit form fields: label, recipient_name, street_line_1, street_line_2, city, state, postal_code, country (default US), phone, user picker (fetch users), is_office checkbox
  - Edit: pencil icon opens pre-filled form
  - Deactivate: trash icon with ConfirmDialog(tone="danger") → DELETE endpoint
  - useMutation for create/update/deactivate, invalidateQueries, showToast

### 8. Create MyShipmentsPage (employee)
- [x] Create `web/app/src/pages/employee/MyShipmentsPage.tsx`
  - Fetch `GET /api/v1/my/shipments` with useQuery, pagination
  - Table: status badge, carrier, tracking (clickable link if tracking_url), item_count, dispatched_at, delivered_at
  - Read-only (no actions)
  - Pagination
  - Empty state: "No shipments found"

---

## Phase 3: Collateral Edits

### 9. Asset detail — Shipment history
- [x] Edit `web/app/src/pages/technician/AssetDetailPage.tsx`
  - Add "Shipment History" Card section (after existing sections)
  - Fetch `GET /api/v1/shipments/by-asset/{asset_id}` with useQuery
  - Table: direction badge, destination (type + address label), carrier, status badge, dispatched_at, delivered_at
  - Row click → navigate to `/shipments/{id}`
  - Empty state: "No shipments recorded for this asset"
  - Add `Shipment` to type imports

### 10. Request detail — Linked shipments
- [x] Edit `web/app/src/pages/technician/RequestDetailPage.tsx`
  - Add "Shipments" Card section
  - Fetch `GET /api/v1/shipments?request_id={id}` with useQuery
  - Compact list: status badge, direction, carrier, tracking, dispatched_at
  - "Create Shipment" button → `/shipments/new?request_id={id}`
  - Only render section if data loaded (not in loading state, even if empty)

### 11. Dashboard — Shipments card
- [x] Edit `web/app/src/pages/admin/DashboardPage.tsx`
  - Add "Active Shipments" Card
  - Fetch `GET /api/v1/dashboard/shipments` with useQuery
  - Show: Draft count, Dispatched count, In Transit count (with colored badges)
  - Failed count in red (if > 0)
  - "View All" link → `/shipments`

---

## Phase 4: Routing & Navigation

### 12. Add routes and sidebar items
- [x] Edit `web/app/src/router.tsx`
  - Add 5 lazy imports: ShipmentsPage, ShipmentDetailPage, ShipmentCreatePage, AddressesPage, MyShipmentsPage
  - Employee section: `{ path: 'my/shipments', element: <MyShipmentsPage /> }`
  - Technician+ section (RequireRole roles=['technician', 'admin', 'super_admin']):
    - `{ path: 'shipments', element: <ShipmentsPage /> }`
    - `{ path: 'shipments/new', element: <ShipmentCreatePage /> }`
    - `{ path: 'shipments/:id', element: <ShipmentDetailPage /> }`
    - `{ path: 'addresses', element: <AddressesPage /> }`
- [x] Edit `web/app/src/components/layout/Sidebar.tsx`
  - General section: `{ to: '/my/shipments', labelKey: 'nav.my_shipments' }`
  - Operations section: `{ to: '/shipments', labelKey: 'nav.shipments', roles: ['technician', 'admin', 'super_admin'] }`
  - Management section: `{ to: '/addresses', labelKey: 'nav.addresses', roles: ['technician', 'admin', 'super_admin'] }`

---

## Phase 5: Verification

### 13. Build verification
- [x] TypeScript compilation: `cd web/app && npx tsc --noEmit`
- [x] Build succeeds: `cd web/app && npm run build`
- [x] Spot check: no hardcoded strings in new pages
- [x] All imports resolve correctly

### 14. Update progress tracking
- [x] Mark all F3 tasks as done in this file
- [x] Update `docs/epics/e16-shipping-logistics/slicing.md` — F3 → Done
- [x] If all features done: Update `docs/product/roadmap.md` — E16 → Done

---

## Dependency Graph

```
Types (1)
  ├── i18n EN (2) + ES (3) — parallel
  │
  └── Pages (parallel after types + i18n):
        ├── ShipmentsPage (4)
        ├── ShipmentDetailPage (5) — uses types
        ├── ShipmentCreatePage (6) — uses types
        ├── AddressesPage (7) — uses types
        └── MyShipmentsPage (8) — uses types
              │
              └── Collateral (after pages):
                    ├── Asset Detail (9)
                    ├── Request Detail (10)
                    └── Dashboard (11)
                          │
                          └── Routing + Sidebar (12)
                                └── Build Verification (13)
                                      └── Progress Tracking (14)
```

## Execution Order

**Batch 1:** Task 1 (types)
**Batch 2 (Parallel):** Tasks 2 + 3 (i18n EN + ES)
**Batch 3 (Parallel):** Tasks 4 + 5 + 6 + 7 + 8 (all pages — independent from each other)
**Batch 4 (Parallel):** Tasks 9 + 10 + 11 (collateral edits)
**Batch 5:** Task 12 (routing + sidebar)
**Batch 6:** Task 13 (build verification)
**Batch 7:** Task 14 (progress tracking)

## Final Checklist

- [x] All tasks completed
- [x] 5 new pages created (ShipmentsPage, ShipmentDetailPage, ShipmentCreatePage, AddressesPage, MyShipmentsPage)
- [x] 3 existing pages edited (AssetDetailPage, RequestDetailPage, DashboardPage)
- [x] TypeScript types added (Shipment, ShipmentItem, ShippingAddress, ShipmentDashboard)
- [x] 5 routes added + 3 sidebar items
- [x] ~80 i18n keys in EN and ES
- [x] TypeScript compiles
- [x] Build succeeds
