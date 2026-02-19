# Tasks: F2 — Approval Workflow

## Implementation Tasks

### 1. Status Enum Extension
- [x] Edit `src/request_bc/request/domain/enums.py`
  - Add `PENDING_APPROVAL = "pending_approval"` to `RequestStatus`
  - Update `VALID_STATUS_TRANSITIONS`:
    - Add `PENDING_APPROVAL: [SUBMITTED, REJECTED]`
  - Note: `PENDING_APPROVAL` is NOT in any existing status's transition list (it's an entry-only status)

### 2. Entity — Approval Routing on Create
- [x] Edit `src/request_bc/request/domain/entities.py`
  - Update `ServiceRequest.create()` to accept `requires_approval: bool = False` parameter
  - If `requires_approval` is True: set initial status to `PENDING_APPROVAL`
  - If False: set initial status to `SUBMITTED` (existing behavior)

### 3. Create Request — Approval Decision
- [x] Edit `src/request_bc/request/application/commands/create_request.py`
  - Add `requires_approval: bool` decision logic:
    - If `type == NEW_EQUIPMENT`: check if requester's department has a manager
    - If manager exists → `requires_approval = True`
    - If no manager → `requires_approval = False`
  - Pass `requires_approval` to `ServiceRequest.create()`
  - Add `department_has_manager: bool = False` to command
- [x] Edit `adapters/http/api/requests/routers.py`
  - Look up department manager when type is `new_equipment`
  - Pass information to command

### 4. Approve Request Command
- [x] Create `src/request_bc/request/application/commands/approve_request.py`
  - `ApproveRequestCommand(request_id, company_id, performed_by, performed_by_role, department_manager_id)`
  - Handler:
    1. Fetch request by ID
    2. Validate status is `PENDING_APPROVAL`
    3. Validate actor authorization: admin/super_admin or matching department manager
    4. Call `request.change_status(RequestStatus.SUBMITTED)`
    5. Save request
    6. Create request event: type `approved`, data includes `approved_by`

### 5. Reject Request Command
- [x] Create `src/request_bc/request/application/commands/reject_request.py`
  - `RejectRequestCommand(request_id, company_id, performed_by, performed_by_role, reason, department_manager_id)`
  - Handler:
    1. Validate reason is non-empty
    2. Fetch request by ID
    3. Validate status is `PENDING_APPROVAL`
    4. Validate actor authorization
    5. Call `request.change_status(RequestStatus.REJECTED)` (sets resolved_at)
    6. Save request
    7. Create request event: type `rejected`, data includes `rejected_by`, `reason`

### 6. API Endpoints
- [x] Edit `adapters/http/api/requests/routers.py`
  - Add `POST /requests/{request_id}/approve`
  - Add `POST /requests/{request_id}/reject`
- [x] Edit `adapters/http/api/requests/schemas.py`
  - Add `RejectRequestRequest(BaseModel): reason: str = Field(min_length=1)`

### 7. Notification — Event Types
- [x] Edit `src/notification_bc/notification/domain/enums.py`
  - Add `REQUEST_APPROVAL_NEEDED = "request.approval_needed"`
  - Add `REQUEST_APPROVED = "request.approved"`
- [x] Edit `src/notification_bc/notification/application/services/event_factory.py`
  - Add factory method `approval_needed(request, actor_id, department_manager_id, department_id)`
  - Add factory method `request_approved(request, actor_id)`

### 8. Notification — Target Resolver
- [x] Edit `src/notification_bc/notification/application/services/target_resolver.py`
  - Add routing for `REQUEST_APPROVAL_NEEDED` → department manager user ID
  - Add routing for `REQUEST_APPROVED` → request creator

### 9. Notification — Subscriber
- [x] Generic subscriber handles new event types (no changes needed)

### 10. Publish Events
- [x] Edit `adapters/http/api/requests/routers.py` (create_request endpoint)
  - After creating request with `pending_approval` status: publish `REQUEST_APPROVAL_NEEDED` event
- [x] Edit `adapters/http/api/requests/routers.py` (approve_request endpoint)
  - After approval: publish `REQUEST_APPROVED` event + `REQUEST_STATUS_CHANGED` event
- [x] Edit `adapters/http/api/requests/routers.py` (reject_request endpoint)
  - After rejection: publish `REQUEST_STATUS_CHANGED` event

### 11. Unit Tests — Approve Command
- [x] Create `tests/unit/request_bc/request/application/commands/test_approval.py`
  - Test: admin can approve → status submitted
  - Test: super_admin can approve
  - Test: department manager can approve
  - Test: non-manager non-admin → UnauthorizedApprovalError
  - Test: wrong manager → UnauthorizedApprovalError
  - Test: request not found → RequestNotFoundError
  - Test: not pending_approval → NotPendingApprovalError
  - Test: event saved with approved_by data

### 12. Unit Tests — Reject Command
- [x] Added to `tests/unit/request_bc/request/application/commands/test_approval.py`
  - Test: admin can reject → status rejected, resolved_at set
  - Test: department manager can reject
  - Test: empty reason → ValueError
  - Test: whitespace-only reason → ValueError
  - Test: unauthorized → UnauthorizedRejectionError
  - Test: request not found → RequestNotFoundError
  - Test: not pending_approval → NotPendingApprovalError
  - Test: event saved with reason and rejected_by

### 13. Unit Tests — Creation Routing
- [x] Added `TestCreateRequestApprovalRouting` to `tests/unit/request_bc/request/application/commands/test_commands.py`
  - Test: new_equipment with manager → pending_approval
  - Test: new_equipment without manager → submitted
  - Test: incident with manager → submitted
  - Test: onboarding → submitted
  - Test: repair → submitted

### 14. Unit Tests — Notifications
- [x] Added to `tests/unit/notification_bc/notification/domain/test_entities.py`
  - Updated EventType count to 9
  - Added new enum value assertions
- [x] Added to `tests/unit/notification_bc/notification/application/services/test_target_resolver.py`
  - Test: approval_needed targets manager
  - Test: approval_needed excludes actor if same as manager
  - Test: approval_needed no manager → empty
  - Test: request_approved targets creator
  - Test: request_approved no creator → empty

### 15. Integration Tests
- [ ] Edit `tests/integration/test_requests_endpoints.py` (requires Docker)

### 16. Frontend Status Support
- [x] Edit `web/app/src/types/index.ts`
  - Added `'pending_approval'` to `RequestStatus` type
  - Added new `RequestType` values: `'repair' | 'configuration' | 'access_request'`

### 17. Verification
- [x] `make test` passes (681 unit tests)
- [ ] `make lint` passes
- [ ] `make test-integration` passes
