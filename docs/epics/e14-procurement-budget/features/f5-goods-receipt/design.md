# Solution Design: F5 — Goods Receipt & Asset Linking

**Requirement:** [requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `procurement_bc.purchase_order`

## Summary

Receive PO items — partial and full receipt, optional asset creation/linking, PO status transitions through receipt flow. Receipt UI on PO detail page. This feature completes the procurement pipeline from ordering to asset deployment.

## Architecture Decision

Goods receipt is implemented as two commands: `ReceiveItemsCommand` (record received quantities, optionally create assets) and `ClosePurchaseOrderCommand` (finalize PO). The asset creation on receipt is handled by a `ReceiptAssetService` that pre-fills asset data from PO item information and calls the existing `CreateAssetCommand` from `asset_bc`. The receipt endpoints are added to the existing purchase-orders router (stubs from F3).

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| PO entity + repo | `src/procurement_bc/purchase_order/` (F0) | Yes | None |
| PO router | `adapters/http/api/purchase_orders/routers.py` (F3) | — | Add receive + close endpoints |
| CreateAssetCommand | `src/asset_bc/asset/application/commands/create_asset.py` | Yes | None (used via service) |
| Asset entity | `src/asset_bc/asset/domain/entities.py` | Yes | Has purchase_cost_cents from F0 |
| Notification subscriber | `src/notification_bc/` | Template | Add po.received event |

## Implementation Plan

### 1. Application Layer

#### Services

| Service | File Path | Description |
|---------|-----------|-------------|
| ReceiptAssetService | `src/procurement_bc/purchase_order/application/services/receipt_asset_service.py` | Create asset from PO item data |

```python
class ReceiptAssetService:
    def __init__(self, asset_repo):
        self.asset_repo = asset_repo

    def create_asset_from_item(
        self,
        company_id: str,
        po_item: PurchaseOrderItem,
        vendor_name: str,
        received_by: str,
    ) -> str:
        # Create asset with:
        # - type: po_item.asset_type
        # - purchase_cost_cents: po_item.unit_cost_cents
        # - purchase_date: now
        # - status: available
        # Returns asset_id
```

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| ReceiveItemsCommand | ReceiveItemsCommandHandler | Record received quantities per item |
| ClosePurchaseOrderCommand | ClosePurchaseOrderCommandHandler | Close from RECEIVED or PARTIALLY_RECEIVED |

```python
@dataclass
class ReceiveItemInput:
    item_id: str
    received_quantity: int
    create_asset: bool = False
    link_asset_id: Optional[str] = None

@dataclass
class ReceiveItemsCommand(Command):
    purchase_order_id: str
    company_id: str
    items: list[ReceiveItemInput] = field(default_factory=list)
    performed_by: str = ""
```

Handler logic:
1. Fetch PO, validate status (ORDERED or PARTIALLY_RECEIVED)
2. For each item input:
   - Find matching PO item
   - Validate: new received_qty <= (quantity - already_received)
   - Update item.received_quantity += input.received_quantity
   - Set item.received_at = now
   - If create_asset and item.asset_type → call ReceiptAssetService
   - If link_asset_id → set item.linked_asset_id
3. Call `po.receive()` — updates status based on overall receipt state
4. If all items fully received → emit `po.received` notification
5. Save

```python
@dataclass
class ClosePurchaseOrderCommand(Command):
    purchase_order_id: str
    company_id: str
    performed_by: str = ""
```

Handler: Fetch PO, validate RECEIVED or PARTIALLY_RECEIVED, call `po.close()`, save.

### 2. Notifications

| Event | Targets | Content |
|-------|---------|---------|
| `po.received` | PO creator + all admins | PO number, vendor, all items received |

### 3. HTTP Layer

Add to existing purchase-orders router:

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/api/v1/purchase-orders/{id}/receive` | technician+ | Record goods receipt |
| POST | `/api/v1/purchase-orders/{id}/close` | technician+ | Close PO |

#### Schemas

```python
class ReceiveItemRequest(BaseModel):
    item_id: str = Field(min_length=1)
    received_quantity: int = Field(ge=1)
    create_asset: bool = False
    link_asset_id: Optional[str] = None

class ReceiveRequest(BaseModel):
    items: list[ReceiveItemRequest] = Field(min_length=1)
```

### 4. Frontend Changes

| Page | Change | Description |
|------|--------|-------------|
| PurchaseOrderDetailPage | Edit | Receipt form, progress bars per item, "Create Asset" button |

Receipt form on PO detail (ORDERED or PARTIALLY_RECEIVED):
- Table showing each item: description, ordered qty, received qty, remaining
- Input field for new received quantity per item
- Checkbox: "Create Asset" (when item has asset_type)
- Or: "Link Existing Asset" dropdown
- Submit button
- Progress bars: received / ordered per item (visual indicator)

- i18n: ~15 keys (EN + ES)

### 5. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `adapters/http/api/purchase_orders/routers.py` | Edit | Implement receive + close endpoints |
| `adapters/http/api/purchase_orders/schemas.py` | Edit | Add receipt schemas |
| `src/notification_bc/notification/domain/enums.py` | Edit | Add po.received event type |
| `src/notification_bc/notification/application/services/notification_subscriber.py` | Edit | Handle po.received |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit | Resolve po.received targets |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | ReceiveItemsCommandHandler — partial receipt | High |
| Unit | ReceiveItemsCommandHandler — full receipt | High |
| Unit | ReceiveItemsCommandHandler — over-receive validation | High |
| Unit | ReceiveItemsCommandHandler — asset creation flow | Medium |
| Unit | ReceiveItemsCommandHandler — link existing asset | Medium |
| Unit | ClosePurchaseOrderCommand — from RECEIVED | High |
| Unit | ClosePurchaseOrderCommand — from PARTIALLY_RECEIVED | High |
| Unit | ClosePurchaseOrderCommand — invalid status | Medium |
| Unit | ReceiptAssetService | Medium |
| Integration | Receive endpoint — partial | High |
| Integration | Receive endpoint — full receipt | High |
| Integration | Receive endpoint — with asset creation | Medium |
| Integration | Close endpoint | Medium |
| Integration | Invalid state transitions | Medium |

~18 tests total (12 unit + 6 integration).

## Implementation Order

1. [ ] Application: ReceiptAssetService
2. [ ] Application: ReceiveItemsCommand + handler
3. [ ] Application: ClosePurchaseOrderCommand + handler
4. [ ] Notifications: po.received event
5. [ ] HTTP: Receipt schemas
6. [ ] HTTP: Receive + close endpoints (implement F3 stubs)
7. [ ] Frontend: Receipt form on PO detail page, progress bars, i18n
8. [ ] Tests: Unit tests
9. [ ] Tests: Integration tests
