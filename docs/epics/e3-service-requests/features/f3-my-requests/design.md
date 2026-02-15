# Design: F3 - My Requests (Employee)

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F3 adds a simple query for employee-facing request list. Extends the existing My router.

```
NEW FILES:
src/request_bc/request/application/queries/my_requests.py

MODIFIED FILES:
src/request_bc/request/infrastructure/repository.py    # Implement find_by_created_by()
adapters/http/api/my/routers.py                        # Add my_requests endpoint
adapters/http/api/my/schemas.py                        # Add MyRequestResponse
```

---

## Domain Layer

No changes. Uses existing RequestRepositoryInterface.find_by_created_by() defined in F0.

---

## Infrastructure Layer

### RequestRepository.find_by_created_by()

```python
def find_by_created_by(
    self, user_id: str, company_id: str,
    page: int = 1, page_size: int = 20,
    status: Optional[str] = None,
) -> tuple[list[ServiceRequest], int]:
    stmt = select(ServiceRequestModel).where(
        ServiceRequestModel.company_id == company_id,
        ServiceRequestModel.created_by == user_id,
    )
    if status:
        stmt = stmt.where(ServiceRequestModel.status == status)

    total = session.execute(select(func.count()).select_from(stmt.subquery())).scalar()

    stmt = stmt.order_by(ServiceRequestModel.created_at.desc())
    offset = (page - 1) * page_size
    models = session.execute(stmt.offset(offset).limit(page_size)).scalars().all()
    return [self._to_entity(m) for m in models], total
```

---

## Application Layer

### MyRequestsQuery + Handler

```python
@dataclass
class MyRequestsQuery:
    user_id: str
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
```

Handler: calls `repo.find_by_created_by()` with all params.

---

## HTTP Layer

### New Schema

```python
class MyRequestResponse(BaseModel):
    id: str
    type: str
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### New Endpoint (in My Router)

```python
@router.get("/requests")  # GET /api/v1/my/requests
def my_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = MyRequestsQueryHandler(request_repo=RequestRepository(db))
    requests, total = handler.handle(
        MyRequestsQuery(
            user_id=current_user.id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=status,
        )
    )
    return {
        "data": [MyRequestResponse(...).model_dump(mode="json") for r in requests],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }
```

Note: Uses `get_current_user` (any authenticated user), not `require_role(TECHNICIAN)`.

---

## Decisions

1. **Extends existing My router**: The `/api/v1/my/` router already has My Equipment. My Requests is added alongside it.
2. **Simple default sort**: Newest first (created_at desc) — employees want to see their most recent requests first.
3. **Status filter only**: No search or other filters needed for v1. Employees have a small number of requests.
4. **No complex schemas**: Reuse the MyRequestResponse pattern from MyEquipmentResponse — condensed fields, no full detail.
