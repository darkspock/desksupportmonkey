# Requirements: E14 - Procurement & Budget

**Type:** Epic
**Status:** Validated
**Created:** 2026-02-18
**Author:** AI
**Priority:** High
**Depends on:** E0 (Foundation), E1 (Company Management), E2 (Asset Inventory), E3 (Service Requests), E4 (Real-time & Notifications), E6 (Report Generation), E12 (Request Typification & Approval)

---

## Business Alignment

**Objective:** Operational efficiency and cost control
**KPI Targets:**
- Reduce untracked equipment purchases from 100% to 0% (all purchases go through PO system)
- Provide budget utilization visibility per department (target: 100% of departments have allocated budgets)
- Reduce over-budget spending incidents through enforcement modes (target: zero unapproved over-budget POs in strict mode)
- Decrease time-to-deploy for new equipment by formalizing the procurement pipeline (measurable: average PO cycle time from draft to received)

**Evidence:**
- E12 introduced approval workflow for `new_equipment` requests but stops at approval — there is no system to track the subsequent purchase, delivery, or cost
- Department managers approved requests without cost awareness (no budget data available)
- Equipment is procured through informal channels (email, verbal) with no audit trail
- Asset `purchase_date` field exists but `purchase_cost` does not — financial tracking was deferred at E2

---

## Problem Statement

### Current Situation

After E12, the request lifecycle for equipment is: employee submits `new_equipment` request → department manager approves → request enters technician queue → technician fulfills. Between approval and fulfillment, the system provides no structure. Technicians purchase equipment through informal channels, and there is no record of what was ordered, from whom, at what cost, or when it arrived.

### Pain Points

1. **No purchase tracking** — When a technician needs to buy equipment for an approved request, there is no record of what was ordered, from whom, at what cost, or when it is expected. Purchase details live in emails, spreadsheets, or personal notes.
2. **No goods receipt** — When equipment arrives, there is no formal process to mark it as received and link it to the corresponding asset in the inventory. Items get lost between ordering and deployment.
3. **No budget visibility** — Departments have no allocated budgets, so there is no way to know how much a department has spent or how much remains. Spending is unchecked and unplanned.
4. **No expense control** — Without budget limits, any approved equipment request becomes a purchase regardless of cost. There are no guardrails for overspending, no thresholds for escalation, and no spending reports for management decisions.

### Impact if Not Solved

- Equipment spending remains invisible to management — no data for budget planning
- Duplicate purchases occur because nobody can see what is already ordered
- Assets enter inventory without cost data, making depreciation and TCO analysis impossible (blocks E20)
- Department managers approve requests without knowing their budget position
- Audit trails are incomplete — procurement steps happen outside the system

---

## Goals

1. **Purchase order management** — Provide a structured PO lifecycle so technicians and admins can create, track, approve, and close purchase orders linked to service requests.
2. **Goods receipt tracking** — Allow marking PO items as received (partial or full) and linking received items to asset inventory records.
3. **Department budget allocation** — Let admins allocate annual budgets per department and track spending against allocations in real time.
4. **Budget enforcement** — Enforce spending limits through configurable modes (warn-only or strict block) and escalate high-value POs to admin approval.
5. **Spending visibility** — Provide spending reports per department with budget-vs-actual analysis, and add procurement metrics to the admin dashboard.

---

## Validation Decisions (Closed)

1. **Bounded context:** New `procurement_bc` with three subdomains: `purchase_order`, `vendor`, `budget`. Procurement has its own lifecycle and rules — it crosses request and asset concerns but is a distinct business capability.
2. **PO structure:** A purchase order has a header (vendor, dates, status, currency, total) and line items (description, optional asset type, quantity, unit cost, received quantity). One PO can have multiple items.
3. **PO status machine:** `DRAFT → SUBMITTED → APPROVED → ORDERED → PARTIALLY_RECEIVED → RECEIVED → CLOSED`. A PO can be `CANCELLED` from any pre-`RECEIVED` state (including ORDERED). PARTIALLY_RECEIVED POs can be closed directly when remaining items will never arrive. See status machine in Entities section.
4. **PO numbering:** Auto-generated sequential per company: `{prefix}-{YYYY}-{NNN}` (e.g., `PO-2026-001`). Prefix is company-configurable (default `PO`).
5. **Budget period:** Annual fiscal year. Company configures the fiscal year start month (default January). One budget allocation per department per fiscal year.
6. **Currency:** Amounts stored as integer cents to avoid floating-point issues. Currency code (ISO 4217) is set per company (default `USD`). Single currency per company in this epic.
7. **Budget enforcement modes:** Two modes — `warn` (PO approval succeeds but shows a warning when over budget) and `strict` (PO cannot be approved if it would exceed remaining department budget). Mode is company-configurable.
8. **PO approval threshold:** Company sets a monetary threshold. POs at or below the threshold are auto-approved on submission. POs above the threshold require explicit admin approval. Default threshold: 0 (all POs require approval).
9. **Vendor model:** Minimal entity: name, contact email, phone, notes, active flag. Full vendor management (contracts, SLAs, performance) is deferred to E25.
10. **Goods receipt → Asset:** When a PO item is marked as received and has an `asset_type` matching an `AssetType` enum value, the user can optionally create a new asset record pre-filled with PO data (type, vendor, cost, purchase date). Manual asset linking is also supported.
11. **Request linkage:** POs can optionally reference one or more service requests (typically approved `new_equipment` requests). The linkage is informational — a PO can exist without a linked request (e.g., proactive stock replenishment).
12. **Spending reports:** New Celery report type `department_spending` alongside existing report types. Shows budget vs. actual per department for a given fiscal year.

---

## Non-Goals (This Epic)

- Multi-currency support within a single company (one currency per company for now).
- Recurring POs or blanket purchase agreements.
- Invoice processing or accounts payable integration.
- Full vendor management with contracts, SLAs, or performance tracking (E25).
- Purchase requisitions as a separate entity (POs serve as both requisition and order).
- Approval chains with multiple signers (single admin approval is sufficient for now).
- Depreciation tracking or total cost of ownership analysis (E20).
- Integration with external procurement systems or ERPs.

---

## User Stories

### US-E14-001: Purchase order lifecycle
**As a** technician or admin,
**I want to** create and manage purchase orders for equipment,
**So that** every purchase is tracked from request to delivery.

**Acceptance Criteria:**
- [ ] Technician or admin can create a PO with: vendor (select or create), line items (description, asset type, quantity, unit cost), optional linked request(s), department, and notes.
- [ ] PO number is auto-generated on creation following the pattern `{prefix}-{YYYY}-{NNN}`.
- [ ] PO starts in `DRAFT` status and can be edited freely.
- [ ] Submitting a PO moves it to `SUBMITTED`. If total is at or below the auto-approval threshold, it auto-advances to `APPROVED`.
- [ ] Admin can approve a submitted PO → status moves to `APPROVED`.
- [ ] Admin can reject a submitted PO → status moves to `CANCELLED` with mandatory reason.
- [ ] Approved PO can be marked as `ORDERED` (externally placed with vendor).
- [ ] PO total is auto-calculated as sum of (quantity × unit cost) across all line items.
- [ ] PO can be cancelled from `DRAFT`, `SUBMITTED`, `APPROVED`, or `ORDERED` states with reason (e.g., vendor cancels order).
- [ ] PO list page with filters: status, vendor, department, date range.
- [ ] PO detail page shows full header, line items, status timeline, and linked requests.

### US-E14-002: Goods receipt tracking
**As a** technician,
**I want to** mark PO items as received when equipment arrives,
**So that** I can track deliveries and update the asset inventory.

**Acceptance Criteria:**
- [ ] For POs in `ORDERED` or `PARTIALLY_RECEIVED` status, technician can record received quantities per line item.
- [ ] Partial receipt: if some items are received but not all, PO moves to `PARTIALLY_RECEIVED`.
- [ ] Full receipt: when all items have received_quantity == quantity, PO moves to `RECEIVED`.
- [ ] When marking an item as received, user can optionally create a new asset pre-filled with: asset type (from PO item), vendor name, purchase cost (unit cost), purchase date (receipt date).
- [ ] When marking an item as received, user can optionally link to an existing asset.
- [ ] Received or partially received PO can be moved to `CLOSED` by admin or technician to finalize (partial close when remaining items will never arrive).
- [ ] Receipt date is recorded per line item.
- [ ] PO detail page shows received vs. ordered quantities per item with visual progress.

### US-E14-003: Department budget allocation
**As an** admin,
**I want to** allocate annual budgets per department,
**So that** I can plan and control equipment spending across the organization.

**Acceptance Criteria:**
- [ ] Admin can set a budget amount per department per fiscal year.
- [ ] Budget is displayed on the Departments page alongside department info.
- [ ] Budget summary shows: allocated, spent (sum of approved+ POs for the department), remaining.
- [ ] Spent amount is calculated from POs in status `APPROVED`, `ORDERED`, `PARTIALLY_RECEIVED`, `RECEIVED`, or `CLOSED` that belong to that department for the current fiscal year.
- [ ] Company configures fiscal year start month (default January) in procurement settings.
- [ ] Budget can be updated at any time (admin adjusts allocation up or down).
- [ ] Budget history is not tracked in this epic (only current allocation).

### US-E14-004: Budget enforcement and spending control
**As an** admin,
**I want** the system to enforce spending limits,
**So that** departments cannot exceed their allocated budgets without oversight.

**Acceptance Criteria:**
- [ ] Company has a procurement configuration with: enforcement mode (`warn` or `strict`), PO approval threshold (amount), PO number prefix, fiscal year start month, and currency.
- [ ] In `warn` mode: PO approval succeeds but returns a warning if it would push the department over budget. Warning is visible on PO detail and in the approval notification.
- [ ] In `strict` mode: PO cannot be approved if the total would exceed the department's remaining budget. Admin gets an error message with the budget shortfall amount.
- [ ] PO approval threshold: POs with total at or below the threshold are auto-approved on submission. POs above threshold require explicit admin approval.
- [ ] Admin is notified when a PO is submitted that requires approval.
- [ ] Admin and department manager are notified when a department reaches 80% of its budget.
- [ ] Budget status (remaining amount) is visible on the PO creation form when a department is selected.

### US-E14-005: Spending reports and dashboard
**As an** admin,
**I want to** see spending reports and procurement metrics,
**So that** I can make informed purchasing decisions and track budget health.

**Acceptance Criteria:**
- [ ] New report type: `department_spending` — async Celery PDF report showing per-department budget vs. actual for a fiscal year.
- [ ] Report includes: department name, allocated budget, total spent, remaining, utilization %, top vendors by spend, top asset types by spend.
- [ ] Dashboard gains a "Budget Health" card showing: total allocated across all departments, total spent, departments over 80% utilization (warning list).
- [ ] Dashboard gains a "Recent Purchase Orders" card showing last 5 POs with status.
- [ ] PO list page shows aggregate stats: total POs, total value, by-status breakdown.

### US-E14-006: Vendor directory
**As a** technician or admin,
**I want to** maintain a directory of vendors,
**So that** I can quickly select vendors when creating purchase orders and track who we buy from.

**Acceptance Criteria:**
- [ ] Technician or admin can create a vendor with: name (required), contact email, phone, address, and notes.
- [ ] Vendor list page with search by name and active/inactive filter.
- [ ] Vendor can be edited (name, contact info, notes).
- [ ] Admin can deactivate a vendor (soft delete — vendor remains on existing POs but is not selectable for new POs).
- [ ] Admin can reactivate a deactivated vendor.
- [ ] PO creation form includes a vendor picker (search + select from active vendors, or create inline).
- [ ] Vendor detail page shows all POs associated with the vendor.

### US-E14-007: Purchase order PDF
**As a** technician or admin,
**I want to** download a formatted PDF of a purchase order,
**So that** I can send it to the vendor or keep a physical record.

**Acceptance Criteria:**
- [ ] PO detail page has a "Download PDF" button, available for POs in `APPROVED`, `ORDERED`, `PARTIALLY_RECEIVED`, `RECEIVED`, or `CLOSED` status.
- [ ] PDF includes: company name, PO number, date, vendor info, line items table (description, asset type, qty, unit cost, total), PO total, notes.
- [ ] PDF follows existing report generation pattern (Celery task + WeasyPrint + MinIO).
- [ ] Generated PDF is stored and available for re-download (no regeneration needed).

---

## Entities

| Entity | Description | States |
|--------|-------------|--------|
| PurchaseOrder | Equipment purchase request with line items | DRAFT, SUBMITTED, APPROVED, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CLOSED, CANCELLED |
| PurchaseOrderItem | Individual line item within a PO | (no status — quantity + received_quantity tracking) |
| Vendor | Equipment supplier contact info | active, inactive |
| DepartmentBudget | Annual budget allocation per department | (no status — value entity) |
| CompanyProcurementConfig | Per-company procurement settings | (no status — singleton per company) |

### State Machine: PurchaseOrder

```
                      auto-approve
                     (≤ threshold)
    ┌──────────┐  ─────────────────>  ┌──────────┐
    │  DRAFT   │ ──> ┌───────────┐ ──> │ APPROVED │ ──> ┌─────────┐
    └──────────┘     │ SUBMITTED │     └──────────┘     │ ORDERED │
         │           └───────────┘          │           └────┬────┘
         │                │                 │                │
    cancel│          reject│           cancel│     cancel/receive
         │                │                 │                │
         ▼                ▼                 ▼                ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────────────┐
    │ CANCELLED │   │ CANCELLED │   │ CANCELLED │   │ PARTIALLY_RECEIVED│──> CANCELLED
    └───────────┘   └───────────┘   └───────────┘   └────────┬──────────┘
                                                          │      │
                                                   all    │      │ close
                                                 received │      │ (partial)
                                                          ▼      ▼
                                                       ┌──────────┐
                                                       │ RECEIVED │
                                                       └─────┬────┘
                                                             │
                                                          close
                                                             │
                                                             ▼
                                                       ┌──────────┐
                                                       │  CLOSED  │
                                                       └──────────┘
```

### State Transitions

| From | To | Trigger | Conditions | Side Effects |
|------|----|---------|------------|--------------|
| DRAFT | SUBMITTED | submit() | At least 1 line item, total > 0 | If total ≤ threshold → auto-advance to APPROVED |
| DRAFT | CANCELLED | cancel() | — | Records cancellation reason |
| SUBMITTED | APPROVED | approve() | Admin role. In strict mode: dept remaining budget ≥ PO total | Notifies PO creator. Records approved_by, approved_at |
| SUBMITTED | CANCELLED | reject() | Admin role | Records cancellation reason. Notifies PO creator |
| APPROVED | ORDERED | mark_ordered() | Technician+ role | Records ordered_at |
| APPROVED | CANCELLED | cancel() | — | Records cancellation reason |
| ORDERED | PARTIALLY_RECEIVED | receive() | received_qty < total qty for at least one item | Records received_at per item. Optional asset creation |
| ORDERED | RECEIVED | receive() | All items: received_qty == qty | Records received_at per item. Notifies admin. Optional asset creation |
| PARTIALLY_RECEIVED | PARTIALLY_RECEIVED | receive() | Still partial after this receipt | Records received_at per item |
| ORDERED | CANCELLED | cancel() | Admin role, mandatory reason | Records cancellation reason. Notifies creator |
| PARTIALLY_RECEIVED | PARTIALLY_RECEIVED | receive() | Still partial after this receipt | Records received_at per item |
| PARTIALLY_RECEIVED | RECEIVED | receive() | All items now fully received | Notifies admin |
| PARTIALLY_RECEIVED | CLOSED | close() | Technician+ role | Finalizes PO with partial receipt (remaining items will not arrive) |
| RECEIVED | CLOSED | close() | Technician+ role | Finalizes PO |

### CRUD Operations

| Entity | Create | Read | Update | Delete | List | Filter | Search |
|--------|--------|------|--------|--------|------|--------|--------|
| PurchaseOrder | Yes | Yes | Yes (DRAFT only) | No (cancel instead) | Yes | status, vendor, dept, date | — |
| PurchaseOrderItem | Yes (with PO) | Yes (with PO) | Yes (DRAFT PO only) | Yes (DRAFT PO only) | Yes (with PO) | — | — |
| Vendor | Yes | Yes | Yes | Soft (deactivate) | Yes | active/inactive | By name |
| DepartmentBudget | Yes (upsert) | Yes | Yes (upsert) | No | Yes (via summary) | fiscal year | — |
| CompanyProcurementConfig | Yes (upsert) | Yes | Yes (upsert) | No | No (singleton) | — | — |

### Inverse Operations

| Action | Inverse | Notes |
|--------|---------|-------|
| Submit PO | Cancel PO | Only from SUBMITTED (reject) |
| Approve PO | Cancel PO | Admin can cancel an approved PO before ordering |
| Activate vendor | Deactivate vendor | Soft toggle |
| Allocate budget | Update budget (set to 0) | No formal "remove budget" — set to 0 |
| Receive items | — | Receipt is irreversible (correct via new PO or manual asset edit) |

---

## Use Cases

### UC-001: Create and submit a purchase order

**Actor:** Technician
**Preconditions:** At least one approved `new_equipment` request exists. Company has procurement config.
**Postconditions:** PO is created and either awaiting approval or auto-approved.

**Main Flow:**
1. Technician navigates to Purchase Orders page and clicks "New PO".
2. Selects a vendor from the directory (or creates a new vendor inline).
3. Selects the department (auto-filled if linking to a request).
4. Adds line items: description, asset type, quantity, unit cost.
5. Optionally links one or more service requests.
6. Saves PO as DRAFT.
7. Reviews PO and clicks "Submit".
8. System validates: at least 1 item, total > 0.
9. If PO total ≤ auto-approval threshold → PO auto-advances to APPROVED.
10. If PO total > threshold → PO enters SUBMITTED and admin is notified.

**Alternative Flows:**
- A1: Technician saves as DRAFT without submitting (comes back later to edit/submit).
- A2: PO is created without linking to any request (proactive stock purchase).
- A3: Auto-approval threshold is 0 → all POs require manual admin approval.

**Error Scenarios:**
- E1: Submit with no line items → validation error, PO stays in DRAFT.
- E2: Submit with item quantity ≤ 0 or unit cost ≤ 0 → validation error.

### UC-002: Approve or reject a purchase order

**Actor:** Admin
**Preconditions:** PO is in SUBMITTED status.
**Postconditions:** PO is either APPROVED or CANCELLED.

**Main Flow:**
1. Admin sees pending POs in the PO list (filtered by SUBMITTED status).
2. Opens PO detail and reviews line items, total, department, and budget status.
3. Clicks "Approve" → PO moves to APPROVED. Creator is notified.

**Alternative Flows:**
- A1: Admin clicks "Reject" → enters mandatory rejection reason → PO moves to CANCELLED. Creator is notified.
- A2: Strict budget mode and PO would exceed department budget → system blocks approval with error showing shortfall amount.
- A3: Warn budget mode and PO would exceed department budget → system shows warning but allows approval.

**Error Scenarios:**
- E1: Non-admin attempts to approve → 403 Forbidden.
- E2: PO is not in SUBMITTED status → 409 Conflict.

### UC-003: Receive goods and create assets

**Actor:** Technician
**Preconditions:** PO is in ORDERED or PARTIALLY_RECEIVED status.
**Postconditions:** Items are marked as received. Assets may be created.

**Main Flow:**
1. Technician opens an ORDERED PO.
2. For each arriving item, enters received quantity.
3. For items with asset_type, chooses "Create Asset" → system pre-fills asset with PO data.
4. Submits receipt.
5. System updates received quantities. If all items fully received → RECEIVED. Otherwise → PARTIALLY_RECEIVED.

**Alternative Flows:**
- A1: Technician links an existing asset instead of creating one (equipment was already in stock).
- A2: Partial delivery — only some items/quantities received. Technician records what arrived. PO stays PARTIALLY_RECEIVED.
- A3: Technician receives more items in a subsequent receipt (multiple receipt events per PO).

**Error Scenarios:**
- E1: received_quantity exceeds ordered quantity → validation error.
- E2: PO is in wrong status (not ORDERED or PARTIALLY_RECEIVED) → 409 Conflict.

### UC-004: Allocate and monitor department budget

**Actor:** Admin
**Preconditions:** Departments exist. Procurement config is set (currency, fiscal year).
**Postconditions:** Department has an allocated budget for the fiscal year.

**Main Flow:**
1. Admin navigates to Departments page.
2. Sees budget column showing allocated / spent / remaining for current fiscal year.
3. Clicks "Set Budget" on a department.
4. Enters allocated amount for the current fiscal year.
5. Saves. Budget is visible immediately.

**Alternative Flows:**
- A1: Budget already exists for the fiscal year → admin updates the allocation (increases or decreases).
- A2: Admin views budget summary page showing all departments side by side.

**Error Scenarios:**
- E1: Negative budget amount → validation error.
- E2: No fiscal year configured → defaults to calendar year (January start).

### UC-005: Budget threshold alert

**Actor:** System (automatic)
**Preconditions:** Department has allocated budget. PO is approved that pushes spending past 80%.
**Postconditions:** Department manager and admins receive notification.

**Main Flow:**
1. PO is approved for a department.
2. System recalculates department spending for the fiscal year.
3. Spending crosses 80% of allocated budget.
4. System emits `budget.threshold_reached` event.
5. Notification sent to department manager and all admins.

**Alternative Flows:**
- A1: Department has no budget allocated → no threshold check, no notification.
- A2: Spending was already above 80% before this PO → no duplicate notification (only fire on crossing the threshold).

### UC-006: Generate spending report

**Actor:** Admin
**Preconditions:** Budget data and POs exist for the fiscal year.
**Postconditions:** PDF report is generated and available for download.

**Main Flow:**
1. Admin navigates to Reports page.
2. Selects report type "Department Spending".
3. Selects fiscal year.
4. Clicks "Generate".
5. Celery task generates PDF with: per-department table (allocated, spent, remaining, utilization %), top vendors by spend, top asset types by spend.
6. Report appears in report list with download link.

**Alternative Flows:**
- A1: No POs exist for the selected fiscal year → report generates with zero spending rows.

### UC-007: Generate and download PO PDF

**Actor:** Technician or Admin
**Preconditions:** PO is in APPROVED or later status (not DRAFT or SUBMITTED).
**Postconditions:** PDF is generated and available for download.

**Main Flow:**
1. User opens PO detail page.
2. Clicks "Download PDF".
3. If PDF not yet generated → system generates via Celery task (WeasyPrint), stores in MinIO.
4. PDF is downloaded. Includes: company name, PO number, date, vendor info, line items table, PO total, notes.

**Alternative Flows:**
- A1: PDF already generated → download immediately without regeneration.
- A2: PO is updated after PDF was generated (e.g., receipt recorded) → regenerate on next download.

### UC-008: Cancel an ordered PO

**Actor:** Admin
**Preconditions:** PO is in ORDERED status. Vendor has cancelled the order.
**Postconditions:** PO moves to CANCELLED with reason.

**Main Flow:**
1. Admin opens PO detail of an ORDERED PO.
2. Clicks "Cancel" and enters mandatory cancellation reason (e.g., "Vendor out of stock").
3. PO moves to CANCELLED. Creator is notified.

**Error Scenarios:**
- E1: PO has already received some items (PARTIALLY_RECEIVED) → cannot cancel, must close instead.

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| Asset Entity (`asset_bc`) | Add `purchase_cost_cents` optional field | Migration + entity edit |
| Request Detail Page | Show linked POs on request detail | Frontend edit |
| Dashboard Page | Add Budget Health and Recent POs cards | Frontend edit |
| Report System (`report_bc`) | Add `department_spending` report type to enum; add PO PDF generation | Enum extension + 2 templates + Celery tasks |
| Departments Page | Show budget column (allocated/spent/remaining) | Frontend edit |
| Department Delete (`company_bc`) | Block deactivation if department has open POs (non-CLOSED/CANCELLED) | Add check to `DeleteDepartmentCommandHandler` (follows existing user-count pattern) |
| Notification System (`notification_bc`) | Handle new event types: `po.*`, `budget.threshold_reached` | Enum + subscriber + resolver updates |
| Vendor deactivation | Existing POs with deactivated vendor remain valid; vendor not selectable for new POs | No migration — filter active vendors in PO creation |
| Sidebar Navigation | Add Purchase Orders and Vendors nav items | Frontend edit |
| Router | Add routes for PO pages, vendor pages, procurement settings | Frontend edit |
| app.py | Register new routers (purchase-orders, vendors, budgets, procurement-settings) | Router registration |
| i18n (EN + ES) | ~80-100 new translation keys | Locale file edits |

---

## Domain & Data (High-Level)

### New Bounded Context: `procurement_bc`

#### Subdomain: `purchase_order`

**Entity: `PurchaseOrder`**
- `id` (ULID), `company_id`, `po_number` (string, unique per company)
- `vendor_id` (nullable FK to Vendor), `vendor_name` (denormalized for display)
- `department_id` (FK, for budget scoping — inferred from linked request or set manually)
- `status` (PurchaseOrderStatus enum)
- `total_amount_cents` (integer, auto-calculated)
- `currency` (string, ISO 4217, default from company config)
- `notes` (optional text)
- `approved_by` (nullable, user ID)
- `approved_at` (nullable datetime)
- `ordered_at` (nullable datetime)
- `cancellation_reason` (nullable text)
- `created_by` (user ID)
- `created_at`, `updated_at`

**Entity: `PurchaseOrderItem`**
- `id` (ULID), `purchase_order_id` (FK)
- `description` (string)
- `asset_type` (nullable, AssetType enum — for asset creation on receipt)
- `quantity` (integer, >= 1)
- `unit_cost_cents` (integer)
- `total_cost_cents` (integer, auto-calculated: quantity × unit_cost)
- `received_quantity` (integer, default 0)
- `received_at` (nullable datetime)
- `linked_asset_id` (nullable FK to Asset)
- `notes` (optional text)

**Entity: `PurchaseOrderRequest`** (join table)
- `purchase_order_id` (FK), `request_id` (FK)

**Enum: `PurchaseOrderStatus`**
```
DRAFT, SUBMITTED, APPROVED, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CLOSED, CANCELLED
```

#### Subdomain: `vendor`

**Entity: `Vendor`**
- `id` (ULID), `company_id`
- `name` (string), `contact_email` (nullable), `phone` (nullable)
- `address` (nullable text), `notes` (nullable text)
- `is_active` (bool, default true)
- `created_at`, `updated_at`

#### Subdomain: `budget`

**Entity: `DepartmentBudget`**
- `id` (ULID), `company_id`, `department_id` (FK)
- `fiscal_year` (integer, e.g. 2026)
- `allocated_amount_cents` (integer)
- `currency` (string, ISO 4217)
- `created_at`, `updated_at`
- Unique constraint: `(department_id, fiscal_year)`

**Entity: `CompanyProcurementConfig`**
- `id` (ULID), `company_id` (unique)
- `enforcement_mode` (string: `warn` or `strict`, default `warn`)
- `approval_threshold_cents` (integer, default 0 — all POs require approval)
- `po_number_prefix` (string, default `PO`)
- `fiscal_year_start_month` (integer 1–12, default 1)
- `currency` (string, ISO 4217, default `USD`)
- `auto_create_assets` (bool, default false — prompt to create assets on receipt)
- `created_at`, `updated_at`

### Computed Values (Not Stored)

- **Department spent:** Sum of `total_amount_cents` from all POs in status `APPROVED`, `ORDERED`, `PARTIALLY_RECEIVED`, `RECEIVED`, or `CLOSED` that belong to the department for the current fiscal year.
- **Department remaining:** `allocated_amount_cents - spent`.
- **Budget utilization %:** `(spent / allocated) × 100`.

### New Tables

| Table | Description |
|-------|-------------|
| `purchase_orders` | PO headers |
| `purchase_order_items` | PO line items |
| `purchase_order_requests` | PO ↔ Request many-to-many |
| `vendors` | Vendor directory |
| `department_budgets` | Annual budget per department |
| `company_procurement_configs` | Per-company procurement settings |

### Events

- `po.submitted` — PO submitted for approval. Notifies admins if above threshold.
- `po.approved` — PO approved. Notifies creator.
- `po.cancelled` — PO cancelled. Notifies creator.
- `po.received` — All PO items received. Notifies creator and admin.
- `budget.threshold_reached` — Department spending crosses 80%. Notifies department manager and admins.

### Dashboard Extensions

- **Budget Health card:** Total allocated, total spent, departments at risk (>80%).
- **Recent POs card:** Last 5 POs with status badges.

### Report Extensions

- New report type `department_spending` added to `ReportType` enum.
- Report template: per-department table with allocated, spent, remaining, utilization %, top vendors, top asset types.

---

## API Endpoints (High-Level)

### Purchase Orders
| Method | Path | Role | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/purchase-orders` | technician+ | Create PO |
| `GET` | `/api/v1/purchase-orders` | technician+ | List POs (paginated, filterable) |
| `GET` | `/api/v1/purchase-orders/{id}` | technician+ | Get PO detail with items |
| `PUT` | `/api/v1/purchase-orders/{id}` | technician+ | Update draft PO |
| `POST` | `/api/v1/purchase-orders/{id}/submit` | technician+ | Submit PO for approval |
| `POST` | `/api/v1/purchase-orders/{id}/approve` | admin | Approve PO |
| `POST` | `/api/v1/purchase-orders/{id}/reject` | admin | Reject (cancel) with reason |
| `POST` | `/api/v1/purchase-orders/{id}/mark-ordered` | technician+ | Mark as ordered |
| `POST` | `/api/v1/purchase-orders/{id}/receive` | technician+ | Record goods receipt (item quantities) |
| `POST` | `/api/v1/purchase-orders/{id}/close` | technician+ | Close received PO |
| `POST` | `/api/v1/purchase-orders/{id}/cancel` | technician+ | Cancel PO |
| `POST` | `/api/v1/purchase-orders/{id}/pdf` | technician+ | Generate PO PDF |
| `GET` | `/api/v1/purchase-orders/{id}/pdf` | technician+ | Download PO PDF |

### Vendors
| Method | Path | Role | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/vendors` | technician+ | Create vendor |
| `GET` | `/api/v1/vendors` | technician+ | List vendors |
| `GET` | `/api/v1/vendors/{id}` | technician+ | Get vendor detail |
| `PUT` | `/api/v1/vendors/{id}` | technician+ | Update vendor |
| `POST` | `/api/v1/vendors/{id}/deactivate` | admin | Deactivate vendor |
| `POST` | `/api/v1/vendors/{id}/activate` | admin | Reactivate vendor |

### Budgets
| Method | Path | Role | Description |
|--------|------|------|-------------|
| `PUT` | `/api/v1/departments/{id}/budget` | admin | Set/update department budget for fiscal year |
| `GET` | `/api/v1/departments/{id}/budget` | admin | Get department budget + spending summary |
| `GET` | `/api/v1/budgets/summary` | admin | All departments budget summary for fiscal year |

### Procurement Config
| Method | Path | Role | Description |
|--------|------|------|-------------|
| `PUT` | `/api/v1/settings/procurement` | admin | Save procurement config |
| `GET` | `/api/v1/settings/procurement` | admin | Get procurement config |

---

## Technical Constraints

- **Integer cents:** All monetary amounts stored as integer cents (e.g., $150.00 = 15000). No floating-point currency math.
- **Multi-tenant isolation:** All queries scoped by `company_id`. POs, vendors, budgets, and config are company-scoped.
- **Sequential PO numbers:** PO numbering uses a database sequence or max+1 pattern scoped per company per year. Must handle concurrency (use `SELECT ... FOR UPDATE` or DB sequence).
- **Fiscal year calculation:** Given `fiscal_year_start_month`, the current fiscal year is derived from the current date. Example: if start_month=4 (April), then March 2027 is FY 2026, April 2027 is FY 2027.
- **Budget computation:** Spent amount is always computed at query time (sum of PO totals in countable statuses for the department+fiscal year). Not stored to avoid staleness.
- **Backward compatibility:** Existing requests, assets, and departments are unaffected. Budget and PO fields are additive.
- **E12 integration:** PO creation can reference approved `new_equipment` requests. The request detail page shows linked POs.
- **E2 integration:** Goods receipt can create or link assets. Asset `purchase_date` is set from receipt date, and a new optional `purchase_cost_cents` field is added to the Asset entity.
- **E6 integration:** New `department_spending` report type follows existing Celery + WeasyPrint + MinIO pipeline.
- **E4 integration:** PO events and budget alerts use existing notification pub/sub infrastructure.
- **SQLAlchemy 2.0:** All models use `Mapped[type]` annotations.
- **Framework base classes:** All commands/queries inherit from `Command`/`Query` and `CommandHandler`/`QueryHandler`.

---

## Definition of Done

- [ ] Purchase order CRUD with full lifecycle (draft → submitted → approved → ordered → received → closed).
- [ ] PO line items with quantity, unit cost, and auto-calculated totals.
- [ ] PO auto-approval for amounts within the configured threshold.
- [ ] Goods receipt tracking with partial and full receipt support.
- [ ] Asset creation/linking from goods receipt.
- [ ] Vendor directory (CRUD, activate/deactivate, selection on PO creation).
- [ ] Department budget allocation (set, update, view per fiscal year).
- [ ] Budget enforcement: warn mode and strict mode.
- [ ] Budget alerts at 80% utilization via notification system.
- [ ] Procurement configuration page (admin settings).
- [ ] Spending report generation (department_spending report type via Celery).
- [ ] Dashboard: budget health card and recent POs card.
- [ ] Request detail page shows linked POs.
- [ ] PO events and notifications (submit, approve, cancel, receive, budget threshold).
- [ ] PO PDF generation and download (formatted PDF for sending to vendors).
- [ ] Department deactivation blocked when open POs exist.
- [ ] Asset entity extended with `purchase_cost_cents` field.
- [ ] Unit tests: PO lifecycle, budget computation, enforcement modes, goods receipt, auto-approval, vendor CRUD.
- [ ] Integration tests: all API endpoints, budget enforcement, PO status transitions.
- [ ] Frontend: PO list/detail/form pages, vendor pages, budget display, receipt form, procurement settings page.
- [ ] i18n keys for all new UI text (English + Spanish).

---

## Time Constraints

**Deadline:** None
**Type:** None
**Dependencies:** E12 must be complete (it is). E4 and E6 must be complete (they are).
**Calendar Conflicts:** None identified.

---

## Open Questions

All questions resolved during validation:

1. ~~Should PO numbering use a DB sequence or application-level max+1?~~ → Decided: use `SELECT MAX(po_number) ... FOR UPDATE` scoped by company+year for simplicity.
2. ~~Should the 80% budget alert fire once or every time a new PO pushes further over?~~ → Decided: fire once when crossing the 80% threshold.
3. ~~Should ORDERED POs be cancellable?~~ → Decided: Yes. Admin can cancel an ORDERED PO (e.g., vendor cancels). Mandatory reason.
4. ~~Should PARTIALLY_RECEIVED POs be closeable?~~ → Decided: Yes. Technician+ can close when remaining items will never arrive.
5. ~~Should department deactivation be blocked by open POs?~~ → Decided: Yes. Block if non-terminal POs exist.
6. ~~Should PO PDF generation be included?~~ → Decided: Yes. Formatted PDF via Celery + WeasyPrint for sending to vendors.
