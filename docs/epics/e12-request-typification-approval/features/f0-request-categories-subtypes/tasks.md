# Tasks: F0 — Request Categories & Subtypes

## Implementation Tasks

### 1. Domain Enums
- [x] Edit `src/request_bc/request/domain/enums.py`
  - Add `REPAIR = "repair"`, `CONFIGURATION = "configuration"`, `ACCESS_REQUEST = "access_request"` to `RequestType`
  - Create `RequestSubtype` enum with values:
    - `HARDWARE = "hardware"`, `SOFTWARE = "software"`, `NETWORK = "network"`, `SECURITY = "security"`, `OTHER = "other"`
    - `COMPUTER = "computer"`, `MOBILE = "mobile"`, `PERIPHERAL = "peripheral"`, `MONITOR_SUBTYPE = "monitor"`, `SOFTWARE_LICENSE = "software_license"`
    - `SOFTWARE_INSTALL = "software_install"`, `ACCOUNT_SETUP = "account_setup"`, `PERMISSIONS = "permissions"`
    - `SYSTEM_ACCESS = "system_access"`, `PHYSICAL_ACCESS = "physical_access"`, `VPN = "vpn"`
  - Create `VALID_SUBTYPES: dict[RequestType, list[RequestSubtype]]` mapping
  - Update `DEFAULT_PRIORITY` to include new types: `REPAIR → MEDIUM`, `CONFIGURATION → LOW`, `ACCESS_REQUEST → LOW`

### 2. Domain Entity
- [x] Edit `src/request_bc/request/domain/entities.py`
  - Add `subtype: Optional[str]` field to `ServiceRequest`
  - Update `ServiceRequest.create()` to accept optional `subtype` parameter
  - Add validation: if `subtype` is provided, it must be in `VALID_SUBTYPES[type]`

### 3. Infrastructure Model
- [x] Edit `src/request_bc/request/infrastructure/models.py`
  - Add `subtype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)` to `ServiceRequestModel`

### 4. Migration
- [x] Create `alembic/versions/f1a2b3c4d5e6_add_request_subtype.py`
  - Add `subtype` column (`VARCHAR(50)`, nullable) to `service_requests` table
  - Add index: `ix_service_requests_company_subtype` on `(company_id, subtype)`

### 5. Repository
- [x] Edit `src/request_bc/request/infrastructure/repository.py`
  - Update `_to_entity()` to map `subtype`
  - Update `_to_model()` / save to map `subtype`
  - Add `subtype` filter to `find_all()` method
  - Add `subtype` filter to `find_by_created_by()` method

### 6. Command
- [x] Edit `src/request_bc/request/application/commands/create_request.py`
  - Add `subtype: Optional[str] = None` to `CreateRequestCommand` dataclass
  - Pass `subtype` to `ServiceRequest.create()`
  - Validate subtype against `VALID_SUBTYPES` if provided

### 7. Queries
- [x] Edit `src/request_bc/request/application/queries/list_requests.py`
  - Add `subtype: Optional[str] = None` to `ListRequestsQuery`
  - Pass to repository
- [x] Edit `src/request_bc/request/application/queries/my_requests.py`
  - Add `subtype: Optional[str] = None` to `MyRequestsQuery`
  - Pass to repository

### 8. API Schemas
- [x] Edit `adapters/http/api/requests/schemas.py`
  - Add `subtype: Optional[str] = None` to `CreateRequestRequest`
  - Add `subtype: Optional[str] = None` to `RequestResponse` and `RequestListItemResponse`

### 9. API Router
- [x] Edit `adapters/http/api/requests/routers.py`
  - Pass `subtype` from request body to `CreateRequestCommand`
  - Add `subtype: Optional[str] = None` query parameter to list endpoints
  - Pass to queries

### 10. Unit Tests
- [x] Edit `tests/unit/request_bc/request/application/commands/test_commands.py`
  - Test: create request with valid subtype → stored correctly
  - Test: create request with invalid subtype for type → raises error
  - Test: create request with subtype for type that has no subtypes → raises error
  - Test: create request without subtype → works (backward compatible)
  - Test: create request with new types (repair, configuration, access_request) → works

### 11. Integration Tests
- [ ] Edit `tests/integration/test_requests_endpoints.py`
  - Test: POST /requests with subtype → 201, subtype in response
  - Test: POST /requests with invalid subtype → 400/422
  - Test: GET /requests?subtype=hardware → filtered results
  - Test: existing requests without subtype continue to work

### 12. Verification
- [x] `make test` passes
- [ ] `make lint` passes
- [ ] Migration applies cleanly (`make db-upgrade`)
