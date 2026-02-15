# Design: F1 - Technician Queue + Assignment

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F1 extends the `request_bc` with list/filter/sort query and assign command. Follows the same search/filter pattern established in E2-F2 (asset list).

```
NEW FILES:
src/request_bc/request/application/commands/assign_request.py
src/request_bc/request/application/queries/list_requests.py

MODIFIED FILES:
src/request_bc/request/infrastructure/repository.py    # Add find_all()
adapters/http/api/requests/routers.py                  # Add list + assign endpoints
adapters/http/api/requests/schemas.py                  # Add list + assign schemas
```

---

## Domain Layer

No new domain entities. Uses existing ServiceRequest, RequestEvent, and RequestRepositoryInterface from F0.

---

## Infrastructure Layer

### RequestRepository.find_all() Implementation

```python
def find_all(
    self, company_id, page=1, page_size=20,
    search=None, status=None, type=None, priority=None, assigned_to=None,
) -> tuple[list[ServiceRequest], int]:
    stmt = select(ServiceRequestModel).where(
        ServiceRequestModel.company_id == company_id
    )

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                ServiceRequestModel.title.ilike(pattern),
                ServiceRequestModel.description.ilike(pattern),
            )
        )
    if status:
        stmt = stmt.where(ServiceRequestModel.status == status)
    if type:
        stmt = stmt.where(ServiceRequestModel.type == type)
    if priority:
        stmt = stmt.where(ServiceRequestModel.priority == priority)
    if assigned_to == "none":
        stmt = stmt.where(ServiceRequestModel.assigned_to.is_(None))
    elif assigned_to:
        stmt = stmt.where(ServiceRequestModel.assigned_to == assigned_to)

    # Count
    total = session.execute(select(func.count()).select_from(stmt.subquery())).scalar()

    # Sort: priority desc (using CASE expression), then created_at asc
    priority_order = case(
        (ServiceRequestModel.priority == "urgent", 4),
        (ServiceRequestModel.priority == "high", 3),
        (ServiceRequestModel.priority == "medium", 2),
        (ServiceRequestModel.priority == "low", 1),
        else_=0,
    )
    stmt = stmt.order_by(priority_order.desc(), ServiceRequestModel.created_at.asc())

    # Paginate
    offset = (page - 1) * page_size
    models = session.execute(stmt.offset(offset).limit(page_size)).scalars().all()
    return [self._to_entity(m) for m in models], total
```

---

## Application Layer

### ListRequestsQuery + Handler

```python
@dataclass
class ListRequestsQuery:
    company_id: str
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
```

Handler: calls `repo.find_all()` with all params.

### AssignRequestCommand + Handler

```python
@dataclass
class AssignRequestCommand:
    request_id: str
    company_id: str
    user_id: str  # technician to assign to
    performed_by: str
```

Handler:
1. Find request -> RequestNotFoundError
2. Validate target user exists and belongs to same company -> UserNotFoundError
3. Validate target user is active -> UserInactiveError
4. request.assign(user_id)
5. Save request
6. Create RequestEvent (type=assigned, data={assigned_to: user_id, assigned_by: performed_by})
7. Return request

Uses `UserRepository.find_by_id_and_company()` to validate the target technician (same pattern as asset assign).

---

## HTTP Layer

### New Schemas

```python
class AssignRequestRequest(BaseModel):
    user_id: str = Field(min_length=1)

class RequestListItemResponse(BaseModel):
    id: str
    type: str
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### New Endpoints

```python
@router.get("")  # GET /api/v1/requests
def list_requests(
    page, page_size, search, status, type, priority, assigned_to,
    current_user = Depends(require_role(UserRole.TECHNICIAN)),
    db = Depends(get_db),
):
    # If assigned_to == "me", replace with current_user.id
    ...

@router.patch("/{request_id}/assign")
def assign_request(
    request_id, body: AssignRequestRequest,
    current_user = Depends(require_role(UserRole.TECHNICIAN)),
    db = Depends(get_db),
):
    ...
```

---

## Decisions

1. **Priority sort via SQL CASE**: Rather than storing a numeric priority column, use a CASE expression in ORDER BY. Keeps the domain clean (string enum) while getting correct sort order.
2. **`assigned_to=me` shorthand**: The router translates `me` to `current_user.id` before passing to the query handler. The query layer doesn't know about "me".
3. **No status restriction on assignment**: Unlike the requirements doc suggesting `submitted` or `in_review` only, we allow assignment at any non-terminal status. This is more flexible for reassignment scenarios.
4. **Reuse UserRepository for validation**: Same pattern as asset assignment — validates the target user exists and is active in the same company.
