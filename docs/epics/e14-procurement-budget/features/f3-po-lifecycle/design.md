# Solution Design: F3 — PO Lifecycle

**Requirement:** [requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `procurement_bc.purchase_order`

## Summary

Core purchase order management — create, list, get, update, submit, approve, reject, mark-ordered, cancel. PO ↔ Request linkage. Auto-approval based on threshold. PO number generation. Notifications for PO events. Full frontend: list page, detail page, create/edit form. This is the largest feature in E14.

## Architecture Decision

PO lifecycle is implemented as individual commands for each status transition, matching the request status pattern from E3. The PO number generator is an application service that reads the max PO number for the company+year and increments it. Auto-approval on submit is handled in the SubmitPurchaseOrderCommandHandler by checking the procurement config threshold. Notifications use the existing pub/sub infrastructure.

The approve command handler is designed with a clear extension point for F4's budget enforcement — it calls an optional `budget_checker` service that defaults to a no-op.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| PO domain entities + repos | `src/procurement_bc/purchase_order/` (F0) | Yes | None |
| Vendor repo | `src/procurement_bc/vendor/` (F0+F1) | Yes | None |
| Config repo | `src/procurement_bc/budget/` (F0+F2) | Yes | None |
| Notification subscriber | `src/notification_bc/notification/application/services/` | Template | Add PO event types |
| Target resolver | `src/notification_bc/notification/application/services/` | Template | Add PO resolution logic |
| Request status pattern | `src/request_bc/request/application/commands/` | Template | None |

## Implementation Plan

### 1. Application Layer

#### Services

| Service | File Path | Description |
|---------|-----------|-------------|
| PONumberGenerator | `src/procurement_bc/purchase_order/application/services/po_number_generator.py` | Generate sequential PO numbers per company+year |

```python
class PONumberGenerator:
    def __init__(self, po_repo: PurchaseOrderRepositoryInterface):
        self.po_repo = po_repo

    def generate(self, company_id: str, prefix: str, year: int) -> str:
        next_seq = self.po_repo.get_next_number(company_id, year)
        return f"{prefix}-{year}-{next_seq:03d}"
```

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| CreatePurchaseOrderCommand | CreatePurchaseOrderCommandHandler | Create PO in DRAFT with items and request links |
| UpdatePurchaseOrderCommand | UpdatePurchaseOrderCommandHandler | Update DRAFT PO (items, vendor, dept, notes) |
| SubmitPurchaseOrderCommand | SubmitPurchaseOrderCommandHandler | Submit PO; auto-approve if within threshold |
| ApprovePurchaseOrderCommand | ApprovePurchaseOrderCommandHandler | Approve SUBMITTED PO |
| RejectPurchaseOrderCommand | RejectPurchaseOrderCommandHandler | Reject PO with reason → CANCELLED |
| MarkOrderedCommand | MarkOrderedCommandHandler | Mark APPROVED PO as ORDERED |
| CancelPurchaseOrderCommand | CancelPurchaseOrderCommandHandler | Cancel from DRAFT/SUBMITTED/APPROVED/ORDERED |

**CreatePurchaseOrderCommand:**
```python
@dataclass
class POItemInput:
    description: str
    asset_type: Optional[str] = None
    quantity: int = 1
    unit_cost_cents: int = 0
    notes: Optional[str] = None

@dataclass
class CreatePurchaseOrderCommand(Command):
    company_id: str
    vendor_id: Optional[str] = None
    vendor_name: str = ""
    department_id: str = ""
    items: list[POItemInput] = field(default_factory=list)
    request_ids: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    performed_by: str = ""
```

Handler logic:
1. Generate PO number (from config prefix + year)
2. Create PurchaseOrder entity via factory
3. Add items, calculate totals
4. Link request IDs
5. Save to repository

**SubmitPurchaseOrderCommand:**
```python
@dataclass
class SubmitPurchaseOrderCommand(Command):
    purchase_order_id: str
    company_id: str
    performed_by: str = ""
```

Handler logic:
1. Fetch PO, validate DRAFT status
2. Validate at least 1 item, total > 0
3. Call `po.submit()`
4. Check procurement config threshold
5. If total ≤ threshold → auto-approve: `po.approve(performed_by)` and emit `po.approved`
6. Else → emit `po.submitted`
7. Save

**ApprovePurchaseOrderCommand:**
```python
@dataclass
class ApprovePurchaseOrderCommand(Command):
    purchase_order_id: str
    company_id: str
    approved_by: str = ""
```

Handler logic:
1. Fetch PO, validate SUBMITTED status
2. *(F4 extension point: budget check here)*
3. Call `po.approve(approved_by)`
4. Emit `po.approved` event
5. Save

#### Queries

| Query | Handler | Description |
|-------|---------|-------------|
| ListPurchaseOrdersQuery | ListPurchaseOrdersQueryHandler | Paginated list with filters |
| GetPurchaseOrderQuery | GetPurchaseOrderQueryHandler | PO detail with items and request IDs |

```python
@dataclass
class ListPurchaseOrdersQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    vendor_id: Optional[str] = None
    department_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

@dataclass
class GetPurchaseOrderQuery(Query):
    purchase_order_id: str
    company_id: str
```

### 2. Notifications

#### New Event Types

| Event | Targets | Content |
|-------|---------|---------|
| `po.submitted` | All admins in company | PO number, vendor, total, requester |
| `po.approved` | PO creator | PO number, approved by |
| `po.cancelled` | PO creator | PO number, cancellation reason |

Add to `EventType` enum in notification_bc. Add cases to `notification_subscriber.py` and `target_resolver.py`.

### 3. HTTP Layer

#### Endpoints

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/api/v1/purchase-orders` | technician+ | Create PO |
| GET | `/api/v1/purchase-orders` | technician+ | List POs |
| GET | `/api/v1/purchase-orders/{id}` | technician+ | Get PO detail |
| PUT | `/api/v1/purchase-orders/{id}` | technician+ | Update draft PO |
| POST | `/api/v1/purchase-orders/{id}/submit` | technician+ | Submit PO |
| POST | `/api/v1/purchase-orders/{id}/approve` | admin | Approve PO |
| POST | `/api/v1/purchase-orders/{id}/reject` | admin | Reject PO |
| POST | `/api/v1/purchase-orders/{id}/mark-ordered` | technician+ | Mark as ordered |
| POST | `/api/v1/purchase-orders/{id}/cancel` | technician+ | Cancel PO |

(Receive and close endpoints are placeholder stubs — implemented in F5. PDF endpoints in F6.)

#### Schemas

```python
class POItemRequest(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    asset_type: Optional[str] = None
    quantity: int = Field(ge=1)
    unit_cost_cents: int = Field(ge=0)
    notes: Optional[str] = None

class POCreateRequest(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: str = Field(min_length=1, max_length=200)
    department_id: str = Field(min_length=1)
    items: list[POItemRequest] = Field(min_length=1)
    request_ids: list[str] = []
    notes: Optional[str] = None

class POUpdateRequest(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: str = Field(min_length=1, max_length=200)
    department_id: str = Field(min_length=1)
    items: list[POItemRequest] = Field(min_length=1)
    request_ids: list[str] = []
    notes: Optional[str] = None

class RejectRequest(BaseModel):
    reason: str = Field(min_length=1)

class CancelRequest(BaseModel):
    reason: str = Field(min_length=1)

class POItemResponse(BaseModel):
    id: str
    description: str
    asset_type: Optional[str]
    quantity: int
    unit_cost_cents: int
    total_cost_cents: int
    received_quantity: int
    received_at: Optional[datetime]
    linked_asset_id: Optional[str]
    notes: Optional[str]

class POResponse(BaseModel):
    id: str
    company_id: str
    po_number: str
    vendor_id: Optional[str]
    vendor_name: str
    department_id: str
    status: str
    total_amount_cents: int
    currency: str
    notes: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    ordered_at: Optional[datetime]
    cancellation_reason: Optional[str]
    created_by: str
    items: list[POItemResponse]
    request_ids: list[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

### 4. Frontend

| Page | File | Description |
|------|------|-------------|
| PurchaseOrderListPage | `web/app/src/pages/admin/PurchaseOrderListPage.tsx` | List with status/vendor/dept/date filters |
| PurchaseOrderDetailPage | `web/app/src/pages/admin/PurchaseOrderDetailPage.tsx` | Header, items, status timeline, actions |
| PurchaseOrderFormPage | `web/app/src/pages/admin/PurchaseOrderFormPage.tsx` | Create/edit form with vendor picker, item builder |

- Router: 3 routes (`/purchase-orders`, `/purchase-orders/:id`, `/purchase-orders/new`, `/purchase-orders/:id/edit`)
- Sidebar: "Purchase Orders" nav item (technician+)
- Types: `PurchaseOrder`, `PurchaseOrderItem`, `PurchaseOrderStatus` in types/index.ts
- i18n: ~45 keys (EN + ES)

### 5. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `app.py` | Edit | Register purchase-orders router |
| `src/notification_bc/notification/domain/enums.py` | Edit | Add po.submitted, po.approved, po.cancelled event types |
| `src/notification_bc/notification/application/services/notification_subscriber.py` | Edit | Handle PO events |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit | Resolve PO event targets |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | CreatePurchaseOrderCommandHandler | High |
| Unit | SubmitPurchaseOrderCommandHandler (with auto-approval) | High |
| Unit | ApprovePurchaseOrderCommandHandler | High |
| Unit | RejectPurchaseOrderCommandHandler | Medium |
| Unit | MarkOrderedCommandHandler | Medium |
| Unit | CancelPurchaseOrderCommandHandler (all valid source states) | High |
| Unit | PONumberGenerator | High |
| Unit | ListPurchaseOrdersQueryHandler | Medium |
| Unit | GetPurchaseOrderQueryHandler | Medium |
| Integration | All 9 endpoints | High |
| Integration | Auto-approval flow | High |
| Integration | Status transition validation (invalid transitions → 409) | High |
| Integration | Admin-only approve/reject | Medium |

~33 tests total (18 unit + 15 integration).

## Implementation Order

1. [ ] Application: PONumberGenerator service
2. [ ] Application: CreatePurchaseOrderCommand + handler
3. [ ] Application: UpdatePurchaseOrderCommand + handler
4. [ ] Application: SubmitPurchaseOrderCommand + handler (with auto-approval)
5. [ ] Application: ApprovePurchaseOrderCommand + handler
6. [ ] Application: RejectPurchaseOrderCommand + handler
7. [ ] Application: MarkOrderedCommand + handler
8. [ ] Application: CancelPurchaseOrderCommand + handler
9. [ ] Application: ListPurchaseOrdersQuery + handler
10. [ ] Application: GetPurchaseOrderQuery + handler
11. [ ] HTTP: Schemas
12. [ ] HTTP: Dependencies
13. [ ] HTTP: Router (9 endpoints)
14. [ ] Notifications: Event types + subscriber + resolver
15. [ ] Config: Register router in app.py
16. [ ] Frontend: Types, pages, router, sidebar, i18n
17. [ ] Tests: Unit tests
18. [ ] Tests: Integration tests

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PO number race condition | Low | High | `get_next_number` uses `SELECT ... FOR UPDATE` |
| Auto-approval threshold edge cases | Low | Medium | Unit test for equal-to-threshold case |
| F4 integration: approve handler must be extensible | Medium | Medium | Design handler with injection point for budget check |
