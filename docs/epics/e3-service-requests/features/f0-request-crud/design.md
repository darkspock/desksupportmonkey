# Design: F0 - Request CRUD + State Machine

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F0 introduces the `request_bc` bounded context with four entities (ServiceRequest, RequestEvent, RequestComment, RequestNote) and core CRUD with state machine + event sourcing.

```
NEW FILES:
src/request_bc/
├── request/
│   ├── domain/
│   │   ├── entities.py           # ServiceRequest, RequestComment, RequestNote, RequestEvent
│   │   ├── enums.py              # RequestType, RequestStatus, RequestPriority + transitions
│   │   └── repository.py         # RequestRepositoryInterface
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_request.py
│   │   │   ├── change_request_status.py
│   │   │   └── change_request_priority.py
│   │   └── queries/
│   │       └── get_request.py
│   └── infrastructure/
│       ├── models.py             # ServiceRequestModel, RequestEventModel, RequestCommentModel, RequestNoteModel
│       └── repository.py         # RequestRepository

adapters/http/api/requests/
├── routers.py
└── schemas.py

MODIFIED FILES:
core/models_registry.py           # Add 4 new models
app.py                            # Register requests router
```

---

## Domain Layer

### RequestType Enum

```python
class RequestType(str, Enum):
    INCIDENT = "incident"
    NEW_EQUIPMENT = "new_equipment"
    ONBOARDING = "onboarding"
```

### RequestStatus Enum + Transitions

```python
class RequestStatus(str, Enum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"

VALID_STATUS_TRANSITIONS: dict[RequestStatus, list[RequestStatus]] = {
    RequestStatus.SUBMITTED: [RequestStatus.IN_REVIEW],
    RequestStatus.IN_REVIEW: [RequestStatus.IN_PROGRESS, RequestStatus.REJECTED],
    RequestStatus.IN_PROGRESS: [RequestStatus.RESOLVED, RequestStatus.IN_REVIEW],
    RequestStatus.RESOLVED: [],
    RequestStatus.REJECTED: [],
}
```

### RequestPriority Enum

```python
class RequestPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

PRIORITY_SORT_ORDER: dict[RequestPriority, int] = {
    RequestPriority.LOW: 1,
    RequestPriority.MEDIUM: 2,
    RequestPriority.HIGH: 3,
    RequestPriority.URGENT: 4,
}

DEFAULT_PRIORITY: dict[RequestType, RequestPriority] = {
    RequestType.INCIDENT: RequestPriority.HIGH,
    RequestType.NEW_EQUIPMENT: RequestPriority.LOW,
    RequestType.ONBOARDING: RequestPriority.MEDIUM,
}
```

### ServiceRequest Entity

```python
@dataclass
class ServiceRequest:
    id: str
    company_id: str
    created_by: str
    type: RequestType
    title: str
    description: str
    status: RequestStatus
    priority: RequestPriority
    assigned_to: Optional[str] = None
    data: Optional[dict] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, company_id, created_by, type, title, description, data=None): ...
        # validates title/description not empty
        # auto-assigns priority from DEFAULT_PRIORITY[type]
        # status = submitted

    def change_status(self, new_status: RequestStatus) -> None: ...
        # validates transition
        # sets resolved_at if resolved/rejected

    def change_priority(self, new_priority: RequestPriority) -> None: ...
        # updates priority (no transition validation needed)

    def assign(self, user_id: str) -> None: ...
        # sets assigned_to
```

### RequestEvent Entity

```python
@dataclass
class RequestEvent:
    id: str
    request_id: str
    event_type: str
    data: dict
    performed_by: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, request_id, event_type, data, performed_by): ...
```

### RequestComment Entity (defined in F0, used in F2)

```python
@dataclass
class RequestComment:
    id: str
    request_id: str
    author_id: str
    body: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, request_id, author_id, body): ...
```

### RequestNote Entity (defined in F0, used in F2)

```python
@dataclass
class RequestNote:
    id: str
    request_id: str
    author_id: str
    body: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, request_id, author_id, body): ...
```

### RequestRepositoryInterface

```python
class RequestRepositoryInterface(ABC):
    # Core request operations
    def save(self, request: ServiceRequest) -> ServiceRequest: ...
    def find_by_id(self, request_id: str, company_id: str) -> Optional[ServiceRequest]: ...

    # Events
    def save_event(self, event: RequestEvent) -> RequestEvent: ...

    # Comments (used by F2)
    def save_comment(self, comment: RequestComment) -> RequestComment: ...
    def find_comments(self, request_id: str) -> list[RequestComment]: ...
    def count_comments(self, request_id: str) -> int: ...

    # Notes (used by F2)
    def save_note(self, note: RequestNote) -> RequestNote: ...
    def find_notes(self, request_id: str) -> list[RequestNote]: ...

    # List queries (used by F1, F3)
    def find_all(self, company_id, page, page_size, ...) -> tuple[list[ServiceRequest], int]: ...
    def find_by_created_by(self, user_id, company_id, ...) -> tuple[list[ServiceRequest], int]: ...
```

Note: The full interface is defined in F0 but some methods are only implemented in later features. F0 implements: save, find_by_id, save_event, count_comments.

---

## Infrastructure Layer

### ServiceRequestModel

```python
class ServiceRequestModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "service_requests"
    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    created_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    assigned_to: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="submitted")
    priority: Mapped[str] = mapped_column(String(10))
    data: Mapped[Optional[dict]] = mapped_column(JSON)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index("ix_service_requests_company_status", "company_id", "status"),
        Index("ix_service_requests_company_created_by", "company_id", "created_by"),
        Index("ix_service_requests_company_assigned_to", "company_id", "assigned_to"),
    )
```

### RequestEventModel

```python
class RequestEventModel(ULIDMixin, Base):
    __tablename__ = "request_events"
    request_id: Mapped[str] = mapped_column(String(26), ForeignKey("service_requests.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    data: Mapped[dict] = mapped_column(JSON)
    performed_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### RequestCommentModel

```python
class RequestCommentModel(ULIDMixin, Base):
    __tablename__ = "request_comments"
    request_id: Mapped[str] = mapped_column(String(26), ForeignKey("service_requests.id"), index=True)
    author_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### RequestNoteModel

```python
class RequestNoteModel(ULIDMixin, Base):
    __tablename__ = "request_comments"
    request_id: Mapped[str] = mapped_column(String(26), ForeignKey("service_requests.id"), index=True)
    author_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

No TimestampMixin on event/comment/note models — they are immutable (no updated_at).

---

## Application Layer

### CreateRequestCommand
1. Validate type is valid RequestType -> `ValueError`
2. Create ServiceRequest entity (auto-priority from type)
3. Save request
4. Create RequestEvent (type=created, data={type, title, priority})
5. Return request

### ChangeRequestStatusCommand
1. Find request by id + company_id -> `RequestNotFoundError`
2. Record old_status
3. change_status() validates transition -> `InvalidStatusTransitionError`
4. **Side effect:** If new status is `in_review` and request.assigned_to is None, auto-assign to performing technician
5. Save request
6. Create RequestEvent (type=status_changed, data={old_status, new_status})
7. If auto-assigned, also create RequestEvent (type=assigned, data={assigned_to})
8. Return request

### ChangeRequestPriorityCommand
1. Find request -> `RequestNotFoundError`
2. Validate new priority is valid -> `ValueError`
3. Record old_priority
4. change_priority()
5. Save request
6. Create RequestEvent (type=priority_changed, data={old_priority, new_priority})
7. Return request

### GetRequestQuery
1. Find request by id + company_id -> `RequestNotFoundError`
2. Get comment_count from repo
3. Return request + comment_count

---

## HTTP Layer

### Schemas

```python
class CreateRequestRequest(BaseModel):
    type: str
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    data: Optional[dict] = None

class ChangeStatusRequest(BaseModel):
    status: str

class ChangePriorityRequest(BaseModel):
    priority: str

class RequestResponse(BaseModel):
    id: str
    company_id: str
    created_by: str
    assigned_to: Optional[str] = None
    type: str
    title: str
    description: str
    status: str
    priority: str
    data: Optional[dict] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    comment_count: int = 0
```

### Router

```python
router = APIRouter(prefix="/api/v1/requests", tags=["requests"])

# POST "" — create (employee+, uses get_current_user not require_role since any authenticated user)
# GET "/{request_id}" — detail (employee own / technician+)
# PATCH "/{request_id}/status" — change status (technician+)
# PATCH "/{request_id}/priority" — change priority (technician+)
```

Access control on GET detail:
- If current_user role < TECHNICIAN and request.created_by != current_user.id -> 404
- This is a router-level check

---

## Decisions

1. **All 4 tables in single migration**: service_requests, request_events, request_comments, request_notes created upfront in F0. Avoids migration ordering issues.
2. **Entity definitions in F0, usage deferred**: RequestComment and RequestNote entities defined but commands/queries for them are in F2.
3. **Repository interface complete, implementation incremental**: Full interface defined in F0, but only F0-needed methods implemented. F1/F2/F3 add remaining methods.
4. **Auto-assign is an application-level side effect**: Not in the domain entity, handled in the ChangeRequestStatusCommandHandler.
5. **JSON data field for type-specific payload**: Keeps request_bc decoupled from asset_bc. No foreign key to assets table.
6. **Employee access control in router**: The GetRequestQuery returns any request in the company. The router checks if the current user is allowed to see it. Returns 404 (not 403) for security.
