# Solution Design: F2 — Address Management

**Requirement:** [../../requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `shipping_bc`
**Depends on:** F0 (complete)

## Summary

F2 delivers the full shipping address lifecycle: create, list, get, update, deactivate (soft-delete), and by-user lookup. 6 API endpoints, independent from F1 (shipment lifecycle). Follows standard CRUD patterns.

## Architecture Decision

Address management is a straightforward CRUD vertical. No state machine, no events, no cross-BC effects. Uses the `ShippingAddress` entity and `ShippingAddressRepository` created in F0.

### Existing Code Reuse

| Component | Location | Reuse |
|-----------|----------|-------|
| Command/CommandHandler | `src/framework/application/command_bus.py` | Inherit |
| Query/QueryHandler | `src/framework/application/query_bus.py` | Inherit |
| ShippingAddress entity | `src/shipping_bc/address/domain/entities.py` (F0) | Use |
| ShippingAddressRepository | `src/shipping_bc/address/infrastructure/repository.py` (F0) | Use |

## Implementation Plan

### 1. Application Layer — Commands

#### 1.1 CreateAddressCommand

**File:** `src/shipping_bc/address/application/commands/create_address.py`

```python
@dataclass
class CreateAddressCommand(Command):
    company_id: str
    label: str
    street_line_1: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    street_line_2: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: bool = False
```

Handler: create `ShippingAddress.create(...)`, save, return ID.

#### 1.2 UpdateAddressCommand

**File:** `src/shipping_bc/address/application/commands/update_address.py`

```python
@dataclass
class UpdateAddressCommand(Command):
    address_id: str
    company_id: str
    label: Optional[str] = None
    street_line_1: Optional[str] = None
    street_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: Optional[bool] = None
```

Handler: load address, call `address.update(...)` with non-None fields, save.

#### 1.3 DeactivateAddressCommand

**File:** `src/shipping_bc/address/application/commands/deactivate_address.py`

```python
@dataclass
class DeactivateAddressCommand(Command):
    address_id: str
    company_id: str
```

Handler: load address, call `address.deactivate()`, save.

### 2. Application Layer — Queries

#### 2.1 ListAddressesQuery

**File:** `src/shipping_bc/address/application/queries/list_addresses.py`

```python
@dataclass
class ListAddressesQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    user_id: Optional[str] = None
    is_office: Optional[bool] = None
    is_active: Optional[bool] = True
```

Handler: delegates to `address_repo.find_all(...)`, returns paginated list.

#### 2.2 GetAddressQuery

**File:** `src/shipping_bc/address/application/queries/get_address.py`

```python
@dataclass
class GetAddressQuery(Query):
    address_id: str
    company_id: str
```

Handler: `find_by_id()`, raise if not found.

#### 2.3 AddressesByUserQuery

**File:** `src/shipping_bc/address/application/queries/addresses_by_user.py`

```python
@dataclass
class AddressesByUserQuery(Query):
    user_id: str
    company_id: str
```

Handler: delegates to `address_repo.find_by_user_id(...)`.

### 3. HTTP Layer

#### 3.1 Router

**File:** `adapters/http/api/addresses/routers.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/addresses` | technician+ | Create address |
| GET | `/api/v1/addresses` | technician+ | List addresses |
| GET | `/api/v1/addresses/{id}` | technician+ | Get detail |
| PUT | `/api/v1/addresses/{id}` | technician+ | Update address |
| DELETE | `/api/v1/addresses/{id}` | technician+ | Deactivate (soft-delete) |
| GET | `/api/v1/addresses/by-user/{user_id}` | technician+ | Addresses for user |

#### 3.2 Schemas

**File:** `adapters/http/api/addresses/schemas.py`

```python
class AddressCreateRequest(BaseModel):
    label: str
    street_line_1: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    street_line_2: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: bool = False

class AddressUpdateRequest(BaseModel):
    label: Optional[str] = None
    street_line_1: Optional[str] = None
    street_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: Optional[bool] = None

class AddressResponse(BaseModel):
    id: str
    company_id: str
    label: str
    street_line_1: str
    street_line_2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str
    recipient_name: Optional[str]
    phone: Optional[str]
    user_id: Optional[str]
    is_office: bool
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

#### 3.3 Dependencies

**File:** `adapters/http/api/addresses/dependencies.py`

```python
def get_address_repo(db = Depends(get_db)):
    return ShippingAddressRepository(db)
```

### 4. App Registration

**File:** `app.py` — Add:
```python
from adapters.http.api.addresses.routers import router as addresses_router
app.include_router(addresses_router)
```

## Testing Strategy

### Unit Tests (~6 tests)

**`tests/unit/shipping_bc/address/application/commands/test_commands.py`:**
- Create with valid data saves address
- Create defaults country to "US"
- Update modifies only provided fields
- Deactivate sets is_active to False
- Deactivate non-existent address raises not found

**`tests/unit/shipping_bc/address/application/queries/test_queries.py`:**
- List returns paginated results with filters
- Get returns address or raises not found
- ByUser returns addresses for user

### Integration Tests (~8 tests)

**`tests/integration/test_addresses_endpoints.py`:**
- POST create → 201
- GET list → 200 with pagination
- GET detail → 200
- PUT update → 200
- DELETE deactivate → 200 (or 204)
- GET by-user → 200
- GET deactivated address still accessible by ID
- List defaults to active only

## Implementation Order

1. Commands (create, update, deactivate)
2. Queries (list, get, by_user)
3. Schemas + Dependencies
4. Router + App registration
5. Unit tests
6. Integration tests
7. Verification
