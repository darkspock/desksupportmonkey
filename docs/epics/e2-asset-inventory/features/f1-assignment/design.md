# Design: F1 - Asset Assignment + My Equipment

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F1 adds assign/unassign commands to `asset_bc` and a new `my` router for employee self-service.

```
NEW FILES:
src/asset_bc/asset/application/commands/assign_asset.py
src/asset_bc/asset/application/commands/unassign_asset.py
src/asset_bc/asset/application/queries/my_equipment.py

adapters/http/api/my/
├── __init__.py
├── routers.py
└── schemas.py

MODIFIED FILES:
src/asset_bc/asset/domain/entities.py          # Add assign/unassign methods
src/asset_bc/asset/domain/repository.py        # Add find_by_assigned_to
adapters/http/api/assets/routers.py            # Add assign/unassign endpoints
app.py                                         # Register my router
```

---

## Domain Layer

### Asset Entity Extensions

```python
def assign(self, user_id: str, department_id: Optional[str] = None) -> None:
    if self.status != AssetStatus.IN_STOCK:
        raise InvalidAssignmentError("Asset must be in stock to assign")
    self.assigned_to = user_id
    self.department_id = department_id
    self.status = AssetStatus.ASSIGNED

def unassign(self) -> None:
    if self.status != AssetStatus.ASSIGNED:
        raise InvalidAssignmentError("Asset is not currently assigned")
    self.assigned_to = None
    self.department_id = None
    self.status = AssetStatus.IN_STOCK
```

### AssetRepositoryInterface Extensions

```python
def find_by_assigned_to(self, user_id: str, company_id: str) -> list[Asset]: ...
```

---

## Application Layer

### AssignAssetCommand
1. Find asset by id + company_id -> AssetNotFoundError
2. Find user by id + company_id -> UserNotFoundError
3. Validate user is active -> UserInactiveError
4. Call asset.assign(user_id, user.department_id)
5. Save asset + create assigned event
6. Return asset

### UnassignAssetCommand
1. Find asset by id + company_id -> AssetNotFoundError
2. Call asset.unassign()
3. Save asset + create unassigned event
4. Return asset

### MyEquipmentQuery
1. Get current user's id and company_id
2. Query assets where assigned_to = user_id and company_id matches
3. Return list

---

## HTTP Layer

### Asset Router (extend)
- PATCH /api/v1/assets/{id}/assign — technician+
- PATCH /api/v1/assets/{id}/unassign — technician+

### My Router (new)
- GET /api/v1/my/equipment — employee+ (any authenticated user)

---

## Decisions

1. **Department auto-sync**: When assigning, copy the user's current department_id to the asset. On unassign, clear it.
2. **My Equipment uses get_current_user**: No need for require_role — any authenticated user can see their own equipment.
