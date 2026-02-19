# Solution Design: F3 — Frontend — Shipment & Address UX

**Requirement:** [../../requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** Frontend (React)
**Depends on:** F1 (Shipment Lifecycle), F2 (Address Management)

## Summary

F3 delivers all frontend pages for shipping and address management: shipment list, detail, create form, address management page, employee "My Shipments" view, asset detail shipment history section, request detail linked shipments, dashboard shipments card. Includes routing, sidebar navigation, TypeScript types, and i18n (EN + ES).

## Architecture Decision

Follows existing frontend patterns: React 19 + TypeScript + Vite + Tailwind CSS + TanStack React Query. Each page is a standalone component with lazy loading. API calls via Axios. State management via React Query (useQuery/useMutation). UI components reuse existing Card, Badge, Table, Pagination, ConfirmDialog, and form primitives.

### Existing Code Reuse

| Component | Location | Reuse |
|-----------|----------|-------|
| Card | `web/app/src/components/ui/Card.tsx` | Layout |
| Badge | `web/app/src/components/ui/Badge.tsx` | Status badges |
| Pagination | `web/app/src/components/ui/Pagination.tsx` | List pagination |
| ConfirmDialog | `web/app/src/components/ui/ConfirmDialog.tsx` | Delete confirmation |
| api (Axios) | `web/app/src/lib/api.ts` | HTTP client |
| useAuth | `web/app/src/hooks/useAuth.ts` | Current user |
| formatDate | `web/app/src/lib/date.ts` | Date formatting |
| useTranslation | `web/app/src/hooks/useTranslation.ts` | i18n |
| RequireRole | `web/app/src/components/auth/RequireRole.tsx` | Route guard |

## Implementation Plan

### 1. TypeScript Types

**File:** `web/app/src/types/index.ts` — Add:

```typescript
interface ShipmentItem {
  id: string;
  shipment_id: string;
  asset_id: string;
  notes?: string | null;
}

interface Shipment {
  id: string;
  company_id: string;
  direction: 'outbound' | 'inbound';
  destination_type: 'employee_home' | 'office' | 'vendor';
  status: 'draft' | 'dispatched' | 'in_transit' | 'delivered' | 'failed' | 'cancelled';
  origin_address_id?: string | null;
  destination_address_id: string;
  recipient_name?: string | null;
  recipient_user_id?: string | null;
  carrier?: string | null;
  tracking_number?: string | null;
  tracking_url?: string | null;
  request_id?: string | null;
  po_id?: string | null;
  return_for_shipment_id?: string | null;
  notes?: string | null;
  failure_reason?: string | null;
  cancellation_reason?: string | null;
  created_by: string;
  dispatched_at?: string | null;
  delivered_at?: string | null;
  created_at: string;
  updated_at?: string | null;
  items: ShipmentItem[];
  item_count: number;
}

interface ShippingAddress {
  id: string;
  company_id: string;
  label: string;
  street_line_1: string;
  street_line_2?: string | null;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  recipient_name?: string | null;
  phone?: string | null;
  user_id?: string | null;
  is_office: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

interface ShipmentDashboard {
  active_by_status: Record<string, number>;
  recent_deliveries: Shipment[];
  failed_count: number;
}
```

### 2. Shipment Pages

#### 2.1 ShipmentsPage.tsx — List view

**File:** `web/app/src/pages/technician/ShipmentsPage.tsx`

- Table: status (Badge), direction, destination type, carrier, tracking, recipient, item count, dispatched_at, delivered_at
- Filters: status (dropdown: all/draft/dispatched/in_transit/delivered/failed/cancelled), direction (all/outbound/inbound), destination_type
- Pagination with page/page_size
- "New Shipment" button → navigates to `/shipments/new`
- Row click → navigates to `/shipments/{id}`
- Status badge color mapping:
  - draft → gray
  - dispatched → blue
  - in_transit → yellow
  - delivered → green
  - failed → red
  - cancelled → gray/strikethrough

#### 2.2 ShipmentDetailPage.tsx — Detail view

**File:** `web/app/src/pages/technician/ShipmentDetailPage.tsx`

- Fetches `GET /api/v1/shipments/{id}` via useQuery
- Header: direction badge + destination type badge + status badge
- Info cards:
  - **Shipping Info:** carrier, tracking number (clickable link if tracking_url), dispatched_at, delivered_at
  - **Addresses:** origin and destination address details (fetch addresses by ID)
  - **Linked Records:** request link, PO link, return-for link (if applicable)
  - **Notes:** shipment notes, failure_reason, cancellation_reason
- Items table: asset_id, per-item notes (link to asset detail)
- Action buttons (based on current status):
  - DRAFT: "Dispatch" button, "Cancel" button, "Edit Items" button
  - DISPATCHED: "In Transit", "Deliver", "Fail", "Cancel" buttons
  - IN_TRANSIT: "Deliver", "Fail", "Cancel" buttons
  - DELIVERED: "Create Return" button
  - FAILED/CANCELLED: no actions
- Each action uses ConfirmDialog where destructive (cancel, fail)
- Dispatch button opens mini-form for carrier + tracking if not already set

#### 2.3 ShipmentCreatePage.tsx — Create form

**File:** `web/app/src/pages/technician/ShipmentCreatePage.tsx`

- Direction selector: outbound/inbound radio
- Destination type selector: employee_home/office/vendor radio
- Address picker:
  - Dropdown of existing addresses (fetched from `GET /api/v1/addresses?is_active=true`)
  - "Create New" option opens inline address form
  - Pre-filter by user when destination_type=employee_home and user selected
- Asset multi-select:
  - Fetches assets from `GET /api/v1/assets?status=in_stock&page_size=100` (or searchable)
  - Checkbox list or tag-based selector
  - Shows selected assets with remove button
- Optional fields: carrier, tracking_number, tracking_url
- Optional links: request_id (searchable dropdown), po_id (searchable dropdown)
- Recipient name and recipient_user_id (auto-set when selecting employee address)
- Notes textarea
- "Save as Draft" button → POST create
- On success → navigate to detail page

#### 2.4 MyShipmentsPage.tsx — Employee view

**File:** `web/app/src/pages/employee/MyShipmentsPage.tsx`

- Fetches `GET /api/v1/my/shipments` via useQuery
- Read-only list: status (Badge), carrier, tracking number (clickable if tracking_url), item count, dispatched_at, delivered_at
- Pagination
- No actions (employees don't manage shipments)
- Click row shows expanded detail (inline, no navigation)

### 3. Address Page

#### 3.1 AddressesPage.tsx — Address management

**File:** `web/app/src/pages/technician/AddressesPage.tsx`

- Table: label, recipient_name, city/state, country, type (office/employee badge), active status
- Filters: type (all/office/employee), active (all/active/inactive)
- "New Address" button opens create form (modal or inline)
- Create/edit form: label, recipient_name, street_line_1, street_line_2, city, state, postal_code, country (default US), phone, user_id (user picker), is_office checkbox
- Edit: pencil icon → opens edit form pre-filled
- Deactivate: trash icon with ConfirmDialog → DELETE endpoint (soft-delete)
- Active toggle: eye/eye-off icon to toggle visibility

### 4. Collateral Edits

#### 4.1 Asset Detail — Shipment History

**File:** `web/app/src/pages/technician/AssetDetailPage.tsx` — Add section:

- New Card after existing sections: "Shipment History"
- Fetches `GET /api/v1/shipments/by-asset/{asset_id}` via useQuery
- Table: direction badge, destination, carrier, status badge, dispatched_at, delivered_at
- Row click → navigate to `/shipments/{id}`
- Empty state: "No shipments recorded for this asset"

#### 4.2 Request Detail — Linked Shipments

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx` — Add section:

- New Card: "Shipments"
- Fetches `GET /api/v1/shipments?request_id={id}` via useQuery
- Compact list: status badge, direction, carrier, tracking, dates
- "Create Shipment" button → navigates to `/shipments/new?request_id={id}`
- Only shown if request has any linked shipments or status allows shipping

#### 4.3 Dashboard — Shipments Card

**File:** `web/app/src/pages/admin/DashboardPage.tsx` — Add card:

- New Card: "Active Shipments"
- Fetches `GET /api/v1/dashboard/shipments` via useQuery
- Shows:
  - Draft count, Dispatched count, In Transit count (with status badges)
  - Failed count (red, if > 0)
  - "View All" link → navigates to `/shipments`

### 5. Routing

**File:** `web/app/src/router.tsx` — Add:

```typescript
const ShipmentsPage = lazy(() => import('./pages/technician/ShipmentsPage'));
const ShipmentDetailPage = lazy(() => import('./pages/technician/ShipmentDetailPage'));
const ShipmentCreatePage = lazy(() => import('./pages/technician/ShipmentCreatePage'));
const AddressesPage = lazy(() => import('./pages/technician/AddressesPage'));
const MyShipmentsPage = lazy(() => import('./pages/employee/MyShipmentsPage'));
```

Routes:
- Employee section: `{ path: 'my/shipments', element: <MyShipmentsPage /> }`
- Technician+ section (RequireRole):
  - `{ path: 'shipments', element: <ShipmentsPage /> }`
  - `{ path: 'shipments/new', element: <ShipmentCreatePage /> }`
  - `{ path: 'shipments/:id', element: <ShipmentDetailPage /> }`
  - `{ path: 'addresses', element: <AddressesPage /> }`

### 6. Sidebar

**File:** `web/app/src/components/layout/Sidebar.tsx` — Add:

General section (all authenticated):
- `{ to: '/my/shipments', labelKey: 'nav.my_shipments' }` — employee

Operations section (technician+):
- `{ to: '/shipments', labelKey: 'nav.shipments', roles: ['technician', 'admin', 'super_admin'] }`

Management section (technician+):
- `{ to: '/addresses', labelKey: 'nav.addresses', roles: ['technician', 'admin', 'super_admin'] }`

### 7. i18n

**File:** `web/app/src/locales/en.ts` — Add ~80 keys:

```
nav.shipments, nav.addresses, nav.my_shipments

page.shipments.title, page.shipments.new, page.shipments.empty, page.shipments.filters.*
page.shipment_detail.title, page.shipment_detail.shipping_info, page.shipment_detail.addresses,
page.shipment_detail.linked_records, page.shipment_detail.notes, page.shipment_detail.items,
page.shipment_detail.actions.dispatch, page.shipment_detail.actions.in_transit,
page.shipment_detail.actions.deliver, page.shipment_detail.actions.fail,
page.shipment_detail.actions.cancel, page.shipment_detail.actions.create_return,
page.shipment_detail.actions.edit_items

page.shipment_create.title, page.shipment_create.direction, page.shipment_create.destination_type,
page.shipment_create.address, page.shipment_create.assets, page.shipment_create.carrier,
page.shipment_create.tracking, page.shipment_create.notes, page.shipment_create.save_draft

page.addresses.title, page.addresses.new, page.addresses.empty, page.addresses.edit,
page.addresses.deactivate, page.addresses.label, page.addresses.recipient, page.addresses.street,
page.addresses.city, page.addresses.state, page.addresses.postal_code, page.addresses.country,
page.addresses.phone, page.addresses.user, page.addresses.office, page.addresses.type

page.my_shipments.title, page.my_shipments.empty, page.my_shipments.tracking

page.asset_detail.shipment_history, page.asset_detail.no_shipments
page.request_detail.shipments, page.request_detail.create_shipment
page.dashboard.active_shipments, page.dashboard.failed_shipments, page.dashboard.recent_deliveries

enum.shipment_status.draft, enum.shipment_status.dispatched, enum.shipment_status.in_transit,
enum.shipment_status.delivered, enum.shipment_status.failed, enum.shipment_status.cancelled
enum.shipment_direction.outbound, enum.shipment_direction.inbound
enum.destination_type.employee_home, enum.destination_type.office, enum.destination_type.vendor

confirm.dispatch_shipment, confirm.cancel_shipment, confirm.fail_shipment, confirm.deactivate_address
toast.shipment_created, toast.shipment_dispatched, toast.shipment_delivered,
toast.shipment_failed, toast.shipment_cancelled, toast.address_created, toast.address_updated,
toast.address_deactivated
```

**File:** `web/app/src/locales/es.ts` — Same keys in Spanish.

## Testing Strategy

- TypeScript compilation: `npx tsc --noEmit`
- Build succeeds: `npm run build`
- No hardcoded strings (spot check)

## Implementation Order

1. TypeScript types
2. i18n keys (EN + ES)
3. ShipmentsPage (list)
4. ShipmentDetailPage (detail with actions)
5. ShipmentCreatePage (create form)
6. AddressesPage (address CRUD)
7. MyShipmentsPage (employee view)
8. Asset detail collateral (shipment history)
9. Request detail collateral (linked shipments)
10. Dashboard collateral (shipments card)
11. Router + Sidebar
12. Build verification

## Risks

- **Asset selector UX:** Multi-select for assets may need search/filter if company has many assets. Keep it simple — paginated list with checkboxes, can enhance later.
- **Address inline creation:** Creating an address within the shipment create flow adds UX complexity. Use a simple expandable form section.
- **i18n volume:** ~80 keys per language is significant. Organize by page prefix to keep manageable.
