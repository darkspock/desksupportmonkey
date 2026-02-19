# Solution Design: F1 — Vendor CRUD

**Requirement:** [requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `procurement_bc.vendor`

## Summary

Full vendor management vertical slice: application layer (commands + queries), HTTP layer (router, schemas, dependencies), and frontend (list + detail pages). Vendors are a prerequisite for PO creation (F3). Follows the EquipmentProfile CRUD pattern established in E11.

## Architecture Decision

Vendor CRUD is a standard entity management feature. Commands handle create, update, activate, deactivate. Queries handle list (paginated, filtered) and get-by-id. The vendor router is a standalone module registered in `app.py`. Frontend provides a list page with search and a detail page showing vendor info and (later, in F3) associated POs.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| Vendor entity + repo interface | `src/procurement_bc/vendor/domain/` (F0) | Yes | None |
| Vendor model + repo | `src/procurement_bc/vendor/infrastructure/` (F0) | Yes | None |
| EquipmentProfile router pattern | `adapters/http/api/equipment_profiles/` | Template | None |

## Implementation Plan

### 1. Application Layer

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| CreateVendorCommand | CreateVendorCommandHandler | Creates new vendor |
| UpdateVendorCommand | UpdateVendorCommandHandler | Updates vendor name, contact, notes |
| ActivateVendorCommand | ActivateVendorCommandHandler | Reactivates a deactivated vendor |
| DeactivateVendorCommand | DeactivateVendorCommandHandler | Soft-deactivates vendor |

```python
@dataclass
class CreateVendorCommand(Command):
    company_id: str
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    id: str = ""
    performed_by: str = ""

@dataclass
class UpdateVendorCommand(Command):
    vendor_id: str
    company_id: str
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    performed_by: str = ""

@dataclass
class ActivateVendorCommand(Command):
    vendor_id: str
    company_id: str
    performed_by: str = ""

@dataclass
class DeactivateVendorCommand(Command):
    vendor_id: str
    company_id: str
    performed_by: str = ""
```

#### Queries

| Query | Handler | Description |
|-------|---------|-------------|
| ListVendorsQuery | ListVendorsQueryHandler | Paginated list with search and active filter |
| GetVendorQuery | GetVendorQueryHandler | Get vendor by ID |

```python
@dataclass
class ListVendorsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    is_active: Optional[bool] = None

@dataclass
class GetVendorQuery(Query):
    vendor_id: str
    company_id: str
```

### 2. HTTP Layer

#### Endpoints

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/api/v1/vendors` | technician+ | Create vendor |
| GET | `/api/v1/vendors` | technician+ | List vendors (paginated, search, active filter) |
| GET | `/api/v1/vendors/{id}` | technician+ | Get vendor detail |
| PUT | `/api/v1/vendors/{id}` | technician+ | Update vendor info |
| POST | `/api/v1/vendors/{id}/activate` | admin | Reactivate vendor |
| POST | `/api/v1/vendors/{id}/deactivate` | admin | Deactivate vendor |

#### Schemas

```python
class VendorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_email: Optional[str] = Field(default=None, max_length=254)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None

class VendorUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_email: Optional[str] = Field(default=None, max_length=254)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None

class VendorResponse(BaseModel):
    id: str
    company_id: str
    name: str
    contact_email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

#### Dependencies

```python
def get_vendor_repo(db: Session = Depends(get_db)) -> VendorRepository:
    return VendorRepository(db)
```

### 3. Frontend

| Page | File | Description |
|------|------|-------------|
| VendorListPage | `web/app/src/pages/admin/VendorListPage.tsx` | List with search, active/inactive filter, create modal |
| VendorDetailPage | `web/app/src/pages/admin/VendorDetailPage.tsx` | Detail view with edit, POs placeholder |

- Router: 2 routes (`/vendors`, `/vendors/:id`)
- Sidebar: "Vendors" nav item under management section (technician+)
- Types: `Vendor` interface in `types/index.ts`
- i18n: ~25 keys (EN + ES)

### 4. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `app.py` | Edit | Register vendor router |
| `web/app/src/router.tsx` | Edit | Add vendor routes |
| `web/app/src/components/layout/Sidebar.tsx` | Edit | Add Vendors nav item |
| `web/app/src/types/index.ts` | Edit | Add Vendor interface |
| `web/app/src/locales/en.ts` | Edit | Add ~25 vendor keys |
| `web/app/src/locales/es.ts` | Edit | Add ~25 vendor keys |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | CreateVendorCommandHandler | High |
| Unit | UpdateVendorCommandHandler | High |
| Unit | Activate/DeactivateVendorCommandHandler | Medium |
| Unit | ListVendorsQueryHandler | Medium |
| Unit | GetVendorQueryHandler | Medium |
| Integration | All 6 vendor endpoints | High |
| Integration | Permission checks (admin-only activate/deactivate) | High |
| Integration | Tenant isolation | Medium |

~18 tests total (10 unit + 8 integration).

## Implementation Order

1. [ ] Application: Commands (create, update, activate, deactivate)
2. [ ] Application: Queries (list, get)
3. [ ] HTTP: Schemas
4. [ ] HTTP: Dependencies
5. [ ] HTTP: Router
6. [ ] Config: Register router in app.py
7. [ ] Frontend: Types, pages, router, sidebar, i18n
8. [ ] Tests: Unit tests
9. [ ] Tests: Integration tests
