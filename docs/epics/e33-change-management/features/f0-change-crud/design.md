# Solution Design: Change Request CRUD + State Machine + List/Detail Pages

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-27
**Bounded Context:** `change_bc` (new)

## Summary

Create a new `change_bc` bounded context implementing a full change management lifecycle with an 8-state machine, approval workflow, append-only audit trail, and list/detail frontend pages. Follows the direct-handler pattern used by `incident_bc` and `vulnerability_bc` (no controller/mapper layer).

## Design Decisions (validated with user)

1. **Navigation:** "Changes" goes in **Management** section (not Operations)
2. **Creation flow:** Two steps — create as DRAFT, then explicit submit
3. **Creation UI:** Modal with essential fields only (title, type, planned_date), rest edited from detail page
4. **Commands:** 10 separate commands, one per action (explicit, one file each)
5. **Assignment:** Allowed in any non-terminal state
6. **Approve UI:** Modal with optional notes field
7. **Badge colors:** Minimalista — grey (draft), blue (pending/scheduled/in_progress/implemented), green (closed), red (rejected/rolled_back)
8. **Timeline:** Visual timeline with vertical connector line, icons per event type, colors
9. **Notifications:** Basic notification to requester on approve/reject (2 EventType entries + event_bus wiring)

## Architecture Decision

- **Pattern:** Direct handler instantiation in routers (dominant pattern used by 40+ modules — incidents, vulnerabilities, requests, etc.)
- **State machine:** VALID_TRANSITIONS dict + `_transition()` domain method (same as incident_bc, request_bc)
- **Audit trail:** ChangeEvent entity following IncidentTimeline pattern (append-only, metadata dict)
- **Approval workflow:** Same pattern as `approve_request.py` (role check + status guard + domain transition)
- **No hard delete:** DORA audit compliance — no DELETE endpoint for change requests
- **Notifications:** ChangeEventFactory with `change_approved` and `change_rejected` methods, wired via event_bus in approve/reject routes. 2 new EventType entries: `CHANGE_APPROVED`, `CHANGE_REJECTED`. TargetResolver resolves to the `requested_by` user.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| IncidentTimeline pattern | `src/incident_bc/incident/domain/entities.py` | Pattern reference | None — replicate for ChangeEvent |
| VALID_STATUS_TRANSITIONS | `src/incident_bc/incident/domain/enums.py` | Pattern reference | None — replicate for ChangeStatus |
| ApproveRequestCommand | `src/request_bc/request/application/commands/approve_request.py` | Pattern reference | None — replicate for ApproveChangeRequest |
| PaginationMeta | `adapters/http/schemas/responses.py` | Direct reuse | None |
| ULIDMixin, TimestampMixin, Base | `core/mixins.py`, `core/base.py` | Direct reuse | None |
| Framework Command/Query | `src/framework/application/` | Direct reuse | None |
| _user_name_resolver_factory | `adapters/http/api/incidents/routers.py` | Pattern reference | Replicate in change router |

## Implementation Plan

### 1. Domain Layer

#### 1.1 Enums — `src/change_bc/change_request/domain/enums.py`

```python
class ChangeType(str, Enum):
    STANDARD = "standard"
    NORMAL = "normal"
    EMERGENCY = "emergency"

class ChangeStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    CLOSED = "closed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"

    @property
    def is_terminal(self) -> bool:
        return self in {
            ChangeStatus.CLOSED,
            ChangeStatus.REJECTED,
            ChangeStatus.ROLLED_BACK,
        }

VALID_TRANSITIONS: dict[ChangeStatus, list[ChangeStatus]] = {
    ChangeStatus.DRAFT: [ChangeStatus.PENDING_APPROVAL, ChangeStatus.SCHEDULED],
    ChangeStatus.PENDING_APPROVAL: [ChangeStatus.SCHEDULED, ChangeStatus.REJECTED],
    ChangeStatus.SCHEDULED: [ChangeStatus.IN_PROGRESS],
    ChangeStatus.IN_PROGRESS: [ChangeStatus.IMPLEMENTED, ChangeStatus.ROLLED_BACK],
    ChangeStatus.IMPLEMENTED: [ChangeStatus.CLOSED, ChangeStatus.ROLLED_BACK],
    ChangeStatus.CLOSED: [],
    ChangeStatus.REJECTED: [],
    ChangeStatus.ROLLED_BACK: [],
}

class ChangeEventType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    STARTED = "started"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"
    CLOSED = "closed"
    ASSIGNED = "assigned"
```

Note: DRAFT can transition to SCHEDULED (standard auto-approve) or PENDING_APPROVAL (normal/emergency). The submit command enforces which target is used based on change_type.

#### 1.2 Entities — `src/change_bc/change_request/domain/entities.py`

**ChangeRequest** (aggregate root):

```python
@dataclass
class ChangeRequest:
    id: str
    company_id: str
    title: str
    description: Optional[str]
    change_type: ChangeType
    status: ChangeStatus
    business_justification: Optional[str]
    risk_assessment: Optional[str]
    rollback_plan: Optional[str]
    planned_date: Optional[datetime]
    requested_by: str           # user who created
    assigned_to: Optional[str]  # technician assigned
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    started_at: Optional[datetime]
    implemented_at: Optional[datetime]
    implementation_notes: Optional[str]
    rolled_back_at: Optional[datetime]
    rollback_reason: Optional[str]
    closed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, ...) -> "ChangeRequest":
        # Validates title required, strips text
        # Sets status = DRAFT
        # Generates ULID id

    def _transition(self, target: ChangeStatus) -> None:
        # Validates via VALID_TRANSITIONS
        # Raises InvalidStatusTransitionError if invalid

    def submit(self) -> None:
        # For standard type: DRAFT → SCHEDULED (auto-approve)
        # For normal/emergency: DRAFT → PENDING_APPROVAL
        # Validates rollback_plan required for normal/emergency

    def approve(self, approved_by: str) -> None:
        # PENDING_APPROVAL → SCHEDULED
        # Records approved_by, approved_at

    def reject(self, rejected_by: str, reason: str) -> None:
        # PENDING_APPROVAL → REJECTED
        # Reason required, records rejected_by, rejected_at, rejection_reason

    def start(self) -> None:
        # SCHEDULED → IN_PROGRESS
        # Records started_at

    def implement(self, notes: Optional[str] = None) -> None:
        # IN_PROGRESS → IMPLEMENTED
        # Records implemented_at, implementation_notes

    def rollback(self, reason: str) -> None:
        # IN_PROGRESS or IMPLEMENTED → ROLLED_BACK
        # Reason required, records rolled_back_at, rollback_reason

    def close(self) -> None:
        # IMPLEMENTED → CLOSED
        # Records closed_at

    def update_details(self, title, description, ...) -> None:
        # Only allowed in DRAFT or PENDING_APPROVAL
        # Raises ChangeNotEditableError otherwise

    def assign(self, user_id: str) -> None:
        # Allowed in any non-terminal state
        # Sets assigned_to
```

**ChangeEvent** (audit trail, follows IncidentTimeline):

```python
@dataclass
class ChangeEvent:
    id: str
    change_request_id: str
    event_type: ChangeEventType
    description: str
    actor_id: str
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None

    @classmethod
    def create(cls, change_request_id, event_type, description, actor_id, metadata=None) -> "ChangeEvent":
        # Generates ULID, returns instance
```

#### 1.3 Exceptions — `src/change_bc/change_request/domain/exceptions.py`

```python
class ChangeNotFoundError(Exception): ...
class InvalidStatusTransitionError(Exception):
    def __init__(self, current: ChangeStatus, target: ChangeStatus): ...
class ChangeNotEditableError(Exception): ...
class RollbackPlanRequiredError(Exception): ...
class RejectionReasonRequiredError(Exception): ...
class RollbackReasonRequiredError(Exception): ...
class UnauthorizedApprovalError(Exception): ...
```

#### 1.4 Repository Interface — `src/change_bc/change_request/domain/repository.py`

```python
@dataclass
class ChangeRequestFilters:
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    change_type: Optional[str] = None
    assigned_to: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class ChangeRequestRepositoryInterface(ABC):
    # ChangeRequest
    @abstractmethod
    def save(self, change: ChangeRequest) -> None: ...

    @abstractmethod
    def find_by_id(self, change_id: str, company_id: str) -> Optional[ChangeRequest]: ...

    @abstractmethod
    def find_all(self, company_id: str, filters: ChangeRequestFilters) -> tuple[list[ChangeRequest], int]: ...

    # ChangeEvent
    @abstractmethod
    def save_event(self, event: ChangeEvent) -> None: ...

    @abstractmethod
    def find_events(self, change_request_id: str) -> list[ChangeEvent]: ...
```

### 2. Application Layer

#### 2.1 Commands

All commands follow the pattern: `@dataclass Command(Command)` + `CommandHandler(CommandHandler[T])` in the same file. Handler returns `None`.

| Command File | Command | Handler | Description |
|-------------|---------|---------|-------------|
| `commands/create_change_request.py` | CreateChangeRequestCommand | CreateChangeRequestCommandHandler | Creates in DRAFT status |
| `commands/update_change_request.py` | UpdateChangeRequestCommand | UpdateChangeRequestCommandHandler | Updates fields (DRAFT/PENDING_APPROVAL only) |
| `commands/submit_change_request.py` | SubmitChangeRequestCommand | SubmitChangeRequestCommandHandler | DRAFT → PENDING_APPROVAL or SCHEDULED |
| `commands/approve_change_request.py` | ApproveChangeRequestCommand | ApproveChangeRequestCommandHandler | PENDING_APPROVAL → SCHEDULED |
| `commands/reject_change_request.py` | RejectChangeRequestCommand | RejectChangeRequestCommandHandler | PENDING_APPROVAL → REJECTED |
| `commands/start_change.py` | StartChangeCommand | StartChangeCommandHandler | SCHEDULED → IN_PROGRESS |
| `commands/implement_change.py` | ImplementChangeCommand | ImplementChangeCommandHandler | IN_PROGRESS → IMPLEMENTED |
| `commands/rollback_change.py` | RollbackChangeCommand | RollbackChangeCommandHandler | IN_PROGRESS/IMPLEMENTED → ROLLED_BACK |
| `commands/close_change.py` | CloseChangeCommand | CloseChangeCommandHandler | IMPLEMENTED → CLOSED |
| `commands/assign_change.py` | AssignChangeCommand | AssignChangeCommandHandler | Assigns technician |

**Command detail — CreateChangeRequestCommand:**
```python
@dataclass
class CreateChangeRequestCommand(Command):
    """Modal creation: only essential fields. Rest added via Update."""
    change_id: str               # pre-generated ULID
    company_id: str
    requested_by: str
    title: str
    change_type: str = "standard"
    planned_date: Optional[datetime] = None

class CreateChangeRequestCommandHandler(CommandHandler[CreateChangeRequestCommand]):
    def __init__(self, change_repo: ChangeRequestRepositoryInterface):
        self.change_repo = change_repo

    def handle(self, command: CreateChangeRequestCommand) -> None:
        change = ChangeRequest.create(
            id=command.change_id,
            company_id=command.company_id,
            requested_by=command.requested_by,
            title=command.title,
            change_type=ChangeType(command.change_type),
            planned_date=command.planned_date,
        )
        self.change_repo.save(change)
        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.CREATED,
            description="Change request created",
            actor_id=command.requested_by,
        )
        self.change_repo.save_event(event)
```

**Command detail — SubmitChangeRequestCommand:**
```python
@dataclass
class SubmitChangeRequestCommand(Command):
    change_id: str
    company_id: str
    performed_by: str

class SubmitChangeRequestCommandHandler(CommandHandler[SubmitChangeRequestCommand]):
    def __init__(self, change_repo: ChangeRequestRepositoryInterface):
        self.change_repo = change_repo

    def handle(self, command: SubmitChangeRequestCommand) -> None:
        change = self.change_repo.find_by_id(command.change_id, command.company_id)
        if not change:
            raise ChangeNotFoundError(...)
        change.submit()  # domain method handles auto-approve vs pending
        self.change_repo.save(change)
        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.SUBMITTED,
            description=f"Change submitted ({change.change_type.value})",
            actor_id=command.performed_by,
            metadata={"auto_approved": change.status == ChangeStatus.SCHEDULED},
        )
        self.change_repo.save_event(event)
```

**Command detail — ApproveChangeRequestCommand:**
```python
@dataclass
class ApproveChangeRequestCommand(Command):
    change_id: str
    company_id: str
    performed_by: str
    performed_by_role: str
    notes: Optional[str] = None

class ApproveChangeRequestCommandHandler(CommandHandler[ApproveChangeRequestCommand]):
    def __init__(self, change_repo: ChangeRequestRepositoryInterface):
        self.change_repo = change_repo

    def handle(self, command: ApproveChangeRequestCommand) -> None:
        change = self.change_repo.find_by_id(command.change_id, command.company_id)
        if not change:
            raise ChangeNotFoundError(...)
        if command.performed_by_role not in ("admin", "super_admin"):
            raise UnauthorizedApprovalError(...)
        change.approve(approved_by=command.performed_by)
        self.change_repo.save(change)
        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.APPROVED,
            description="Change approved",
            actor_id=command.performed_by,
            metadata={"notes": command.notes} if command.notes else None,
        )
        self.change_repo.save_event(event)
```

**Other commands follow the same pattern** — load entity, validate preconditions, call domain method, save, record event.

#### 2.2 Queries

| Query File | Query | Handler | Returns |
|-----------|-------|---------|---------|
| `queries/list_change_requests.py` | ListChangeRequestsQuery | ListChangeRequestsQueryHandler | `tuple[list[ChangeRequestListDto], int]` |
| `queries/get_change_request_detail.py` | GetChangeRequestDetailQuery | GetChangeRequestDetailQueryHandler | `ChangeRequestDetailDto` |

**Query detail — ListChangeRequestsQuery:**
```python
@dataclass
class ChangeRequestListDto:
    id: str
    title: str
    change_type: str
    status: str
    planned_date: Optional[datetime]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    requested_by: str
    requested_by_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

@dataclass
class ListChangeRequestsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    change_type: Optional[str] = None
    assigned_to: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class ListChangeRequestsQueryHandler(
    QueryHandler[ListChangeRequestsQuery, tuple[list[ChangeRequestListDto], int]]
):
    def __init__(
        self,
        change_repo: ChangeRequestRepositoryInterface,
        user_name_resolver=None,
    ):
        self.change_repo = change_repo
        self.user_name_resolver = user_name_resolver

    def handle(self, query: ListChangeRequestsQuery) -> tuple[list[ChangeRequestListDto], int]:
        changes, total = self.change_repo.find_all(
            company_id=query.company_id,
            filters=ChangeRequestFilters(
                page=query.page,
                page_size=query.page_size,
                status=query.status,
                change_type=query.change_type,
                assigned_to=query.assigned_to,
                search=query.search,
                date_from=query.date_from,
                date_to=query.date_to,
            ),
        )
        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids = set()
            for c in changes:
                if c.assigned_to:
                    user_ids.add(c.assigned_to)
                if c.requested_by:
                    user_ids.add(c.requested_by)
            if user_ids:
                name_map = self.user_name_resolver(list(user_ids))
        return [
            ChangeRequestListDto(
                id=c.id,
                title=c.title,
                change_type=c.change_type.value,
                status=c.status.value,
                planned_date=c.planned_date,
                assigned_to=c.assigned_to,
                assigned_to_name=name_map.get(c.assigned_to) if c.assigned_to else None,
                requested_by=c.requested_by,
                requested_by_name=name_map.get(c.requested_by) if c.requested_by else None,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in changes
        ], total
```

**Query detail — GetChangeRequestDetailQuery:**
```python
@dataclass
class ChangeEventDto:
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str]
    created_at: Optional[datetime]
    metadata: Optional[dict]

@dataclass
class ChangeRequestDetailDto:
    id: str
    company_id: str
    title: str
    description: Optional[str]
    change_type: str
    status: str
    business_justification: Optional[str]
    risk_assessment: Optional[str]
    rollback_plan: Optional[str]
    planned_date: Optional[datetime]
    requested_by: str
    requested_by_name: Optional[str]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    approved_by: Optional[str]
    approved_by_name: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_by_name: Optional[str]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    started_at: Optional[datetime]
    implemented_at: Optional[datetime]
    implementation_notes: Optional[str]
    rolled_back_at: Optional[datetime]
    rollback_reason: Optional[str]
    closed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    timeline: list[ChangeEventDto]

@dataclass
class GetChangeRequestDetailQuery(Query):
    change_id: str
    company_id: str

class GetChangeRequestDetailQueryHandler(
    QueryHandler[GetChangeRequestDetailQuery, Optional[ChangeRequestDetailDto]]
):
    def __init__(self, change_repo, user_name_resolver=None):
        self.change_repo = change_repo
        self.user_name_resolver = user_name_resolver

    def handle(self, query) -> Optional[ChangeRequestDetailDto]:
        change = self.change_repo.find_by_id(query.change_id, query.company_id)
        if not change:
            return None
        events = self.change_repo.find_events(query.change_id)
        # Batch resolve user names
        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids = {change.requested_by}
            if change.assigned_to:
                user_ids.add(change.assigned_to)
            if change.approved_by:
                user_ids.add(change.approved_by)
            if change.rejected_by:
                user_ids.add(change.rejected_by)
            for e in events:
                user_ids.add(e.actor_id)
            name_map = self.user_name_resolver(list(user_ids))
        # Build DTO
        return ChangeRequestDetailDto(
            # ... map all fields from entity, resolve names from name_map
            timeline=[
                ChangeEventDto(
                    id=e.id,
                    event_type=e.event_type.value,
                    description=e.description,
                    actor_id=e.actor_id,
                    actor_name=name_map.get(e.actor_id),
                    created_at=e.created_at,
                    metadata=e.metadata,
                )
                for e in events
            ],
        )
```

### 3. Infrastructure Layer

#### 3.1 Models — `src/change_bc/change_request/infrastructure/models.py`

**ChangeRequestModel:**
```python
class ChangeRequestModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "change_requests"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft")
    business_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_assessment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rollback_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    planned_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(26), nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    implemented_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    implementation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rollback_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_change_requests_company_status", "company_id", "status"),
        Index("ix_change_requests_company_type", "company_id", "change_type"),
        Index("ix_change_requests_planned_date", "planned_date"),
    )
```

**ChangeEventModel:**
```python
class ChangeEventModel(ULIDMixin, Base):
    __tablename__ = "change_events"

    change_request_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("change_requests.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
```

#### 3.2 Repository — `src/change_bc/change_request/infrastructure/repository.py`

Implements `ChangeRequestRepositoryInterface`:
- `save(change)` — insert or update (check by id, flush)
- `find_by_id(change_id, company_id)` — select + company_id filter
- `find_all(company_id, filters)` — paginated with conditional filters, returns `tuple[list[ChangeRequest], int]`
- `save_event(event)` — insert ChangeEventModel
- `find_events(change_request_id)` — select ordered by created_at asc
- `_to_entity(model)` — static helper for ORM → domain conversion
- `_to_event_entity(model)` — static helper for event conversion

#### 3.3 Migration — `alembic/versions/e33a1_create_change_request_tables.py`

Creates tables:
- `change_requests` — all columns, indexes
- `change_events` — FK to change_requests, indexes

### 4. HTTP Layer

#### 4.1 Dependencies — `adapters/http/api/changes/dependencies.py`

```python
def get_change_repo(db: Session = Depends(get_db)) -> ChangeRequestRepository:
    return ChangeRequestRepository(db)

def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
```

#### 4.2 Schemas — `adapters/http/api/changes/schemas.py`

**Request schemas:**
```python
class CreateChangeRequestSchema(BaseModel):
    """Modal creation: only essential fields (title, type, planned_date)."""
    title: str = Field(min_length=1, max_length=255)
    change_type: str = "standard"  # standard/normal/emergency
    planned_date: Optional[datetime] = None

class UpdateChangeRequestSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    change_type: Optional[str] = None
    business_justification: Optional[str] = None
    risk_assessment: Optional[str] = None
    rollback_plan: Optional[str] = None
    planned_date: Optional[datetime] = None

class ApproveChangeRequestSchema(BaseModel):
    notes: Optional[str] = None

class RejectChangeRequestSchema(BaseModel):
    reason: str = Field(min_length=1)

class ImplementChangeSchema(BaseModel):
    notes: Optional[str] = None

class RollbackChangeSchema(BaseModel):
    reason: str = Field(min_length=1)

class AssignChangeSchema(BaseModel):
    assigned_to: str
```

**Response schemas:**
```python
class ChangeRequestListItemResponse(BaseModel):
    id: str
    title: str
    change_type: str
    status: str
    planned_date: Optional[datetime]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    requested_by: str
    requested_by_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class ChangeEventResponse(BaseModel):
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str]
    created_at: Optional[datetime]
    metadata: Optional[dict]

class ChangeRequestDetailResponse(BaseModel):
    id: str
    company_id: str
    title: str
    description: Optional[str]
    change_type: str
    status: str
    business_justification: Optional[str]
    risk_assessment: Optional[str]
    rollback_plan: Optional[str]
    planned_date: Optional[datetime]
    requested_by: str
    requested_by_name: Optional[str]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    approved_by: Optional[str]
    approved_by_name: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_by_name: Optional[str]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    started_at: Optional[datetime]
    implemented_at: Optional[datetime]
    implementation_notes: Optional[str]
    rolled_back_at: Optional[datetime]
    rollback_reason: Optional[str]
    closed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    timeline: list[ChangeEventResponse]
```

#### 4.3 Router — `adapters/http/api/changes/routers.py`

```
router = APIRouter(prefix="/api/v1/changes", tags=["changes"])
```

| Method | Route | Function | Auth | Description |
|--------|-------|----------|------|-------------|
| POST | `/api/v1/changes` | `create_change_request` | technician+ | Create in DRAFT |
| GET | `/api/v1/changes` | `list_change_requests` | technician+ | Paginated list |
| GET | `/api/v1/changes/{change_id}` | `get_change_request` | technician+ | Detail + timeline |
| PATCH | `/api/v1/changes/{change_id}` | `update_change_request` | technician+ | Edit fields |
| POST | `/api/v1/changes/{change_id}/submit` | `submit_change_request` | technician+ | Submit for approval |
| POST | `/api/v1/changes/{change_id}/approve` | `approve_change_request` | admin+ | Approve |
| POST | `/api/v1/changes/{change_id}/reject` | `reject_change_request` | admin+ | Reject |
| POST | `/api/v1/changes/{change_id}/start` | `start_change` | technician+ | Start implementation |
| POST | `/api/v1/changes/{change_id}/implement` | `implement_change` | technician+ | Mark implemented |
| POST | `/api/v1/changes/{change_id}/rollback` | `rollback_change` | technician+ | Rollback |
| POST | `/api/v1/changes/{change_id}/close` | `close_change` | admin+ | Close |
| POST | `/api/v1/changes/{change_id}/assign` | `assign_change` | admin+ | Assign technician |

**Exception mapping in each route:**
```python
try:
    handler.handle(command)
except ChangeNotFoundError:
    raise HTTPException(404, "Change request not found")
except InvalidStatusTransitionError as e:
    raise HTTPException(422, str(e))
except ChangeNotEditableError as e:
    raise HTTPException(422, str(e))
except RollbackPlanRequiredError as e:
    raise HTTPException(422, str(e))
except UnauthorizedApprovalError as e:
    raise HTTPException(403, str(e))
except ValueError as e:
    raise HTTPException(422, str(e))
```

#### 4.4 Router Registration — `app.py`

```python
from adapters.http.api.changes.routers import router as changes_router
app.include_router(changes_router)
```

### 5. Frontend

#### 5.1 ChangeListPage.tsx — `web/app/src/pages/admin/ChangeListPage.tsx`

- Page with filters: status (dropdown), change_type (dropdown), search (text)
- Paginated table: title (link), type badge, status badge, planned_date, assigned_to, created_at
- "New Change Request" button → opens **creation modal** (title, type, planned_date only)
- useQuery with queryKey `['changes', page, status, type, search]`
- **Badge colors (minimalista):**
  - Grey: `draft`
  - Blue: `pending_approval`, `scheduled`, `in_progress`, `implemented`
  - Green: `closed`
  - Red: `rejected`, `rolled_back`

#### 5.2 ChangeDetailPage.tsx — `web/app/src/pages/admin/ChangeDetailPage.tsx`

- All fields display (description, justification, risk, rollback_plan, etc.)
- **Visual timeline** with vertical connector line, icons per event type, color accents
- Action buttons conditional on current status and user role:
  - DRAFT: Submit, Edit (inline edit fields), Assign
  - PENDING_APPROVAL: Approve (admin, **modal with optional notes**), Reject (admin, **modal with required reason**), Edit, Assign
  - SCHEDULED: Start, Assign
  - IN_PROGRESS: Implement (modal with optional notes), Rollback (modal with required reason), Assign
  - IMPLEMENTED: Close (admin), Rollback (modal with required reason), Assign
  - Terminal states: no action buttons
- useMutation for each action, with queryClient.invalidateQueries
- Edit mode: inline fields for title, description, change_type, business_justification, risk_assessment, rollback_plan, planned_date (only in DRAFT/PENDING_APPROVAL)

#### 5.3 Router — `web/app/src/router.tsx`

```typescript
const ChangeListPage = lazy(() => import('./pages/admin/ChangeListPage'));
const ChangeDetailPage = lazy(() => import('./pages/admin/ChangeDetailPage'));

// Routes:
{ path: '/changes', element: <S><ChangeListPage /></S> },
{ path: '/changes/:id', element: <S><ChangeDetailPage /></S> },
```

#### 5.4 Navigation — `web/app/src/config/navSections.ts`

Add to **Management** section:
```typescript
{ to: '/changes', labelKey: 'nav.changes', roles: ['technician', 'admin', 'super_admin'] },
```

#### 5.5 i18n — `web/app/src/locales/en.ts` + `es.ts`

Keys to add:
```typescript
// Navigation
'nav.changes': 'Changes',

// Enums
'enum.change_type.standard': 'Standard',
'enum.change_type.normal': 'Normal',
'enum.change_type.emergency': 'Emergency',
'enum.change_status.draft': 'Draft',
'enum.change_status.pending_approval': 'Pending Approval',
'enum.change_status.scheduled': 'Scheduled',
'enum.change_status.in_progress': 'In Progress',
'enum.change_status.implemented': 'Implemented',
'enum.change_status.closed': 'Closed',
'enum.change_status.rejected': 'Rejected',
'enum.change_status.rolled_back': 'Rolled Back',

// Pages
'page.changes.title': 'Change Management',
'page.changes.subtitle': 'Manage endpoint change requests',
'page.changes.new': 'New Change Request',
'page.changes.search': 'Search changes...',
'page.changes.all_statuses': 'All Statuses',
'page.changes.all_types': 'All Types',

// Detail
'page.change_detail.title': 'Change Request',
'page.change_detail.submit': 'Submit for Approval',
'page.change_detail.approve': 'Approve',
'page.change_detail.reject': 'Reject',
'page.change_detail.start': 'Start Implementation',
'page.change_detail.implement': 'Mark Implemented',
'page.change_detail.rollback': 'Rollback',
'page.change_detail.close': 'Close',
'page.change_detail.assign': 'Assign',
'page.change_detail.timeline': 'Timeline',
'page.change_detail.business_justification': 'Business Justification',
'page.change_detail.risk_assessment': 'Risk Assessment',
'page.change_detail.rollback_plan': 'Rollback Plan',
'page.change_detail.planned_date': 'Planned Date',
'page.change_detail.rejection_reason': 'Rejection Reason',
'page.change_detail.implementation_notes': 'Implementation Notes',
'page.change_detail.rollback_reason': 'Rollback Reason',

// Event types
'enum.change_event.created': 'Created',
'enum.change_event.updated': 'Updated',
'enum.change_event.submitted': 'Submitted',
'enum.change_event.approved': 'Approved',
'enum.change_event.rejected': 'Rejected',
'enum.change_event.started': 'Started',
'enum.change_event.implemented': 'Implemented',
'enum.change_event.rolled_back': 'Rolled Back',
'enum.change_event.closed': 'Closed',
'enum.change_event.assigned': 'Assigned',
```

### 6. Notifications

#### 6.1 EventType entries — `src/notification_bc/notification/domain/enums.py`

Add 2 new entries:
```python
CHANGE_APPROVED = "change_approved"
CHANGE_REJECTED = "change_rejected"
```

#### 6.2 ChangeEventFactory — `src/change_bc/change_request/application/services/event_factory.py`

```python
class ChangeEventFactory:
    @staticmethod
    def change_approved(change: ChangeRequest, actor_id: str) -> DomainEvent:
        # event_type=CHANGE_APPROVED, payload with change_id/title/type
        # title="Change request approved", body=f"{change.title}"

    @staticmethod
    def change_rejected(change: ChangeRequest, actor_id: str, reason: str) -> DomainEvent:
        # event_type=CHANGE_REJECTED, payload with change_id/title/type/reason
        # title="Change request rejected", body=f"{change.title}: {reason}"
```

#### 6.3 TargetResolver — `src/notification_bc/notification/application/services/target_resolver.py`

Add resolvers for both event types. Both resolve to `{change.requested_by}` — notify the person who created the change.

```python
EventType.CHANGE_APPROVED: self._resolve_change_requester,
EventType.CHANGE_REJECTED: self._resolve_change_requester,

def _resolve_change_requester(self, event: DomainEvent) -> set[str]:
    requested_by = event.payload.get("requested_by")
    return {requested_by} if requested_by else set()
```

Note: `requested_by` must be included in the DomainEvent payload by the factory.

#### 6.4 Router wiring

In approve and reject routes, after handler.handle() + db.commit():
```python
event = ChangeEventFactory.change_approved(change, actor_id=current_user.id)
event_bus.publish(event, db)
```

### 7. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `app.py` | Modify | Register changes router |
| `web/app/src/router.tsx` | Modify | Add change routes |
| `web/app/src/config/navSections.ts` | Modify | Add nav entry in Management section |
| `web/app/src/locales/en.ts` | Modify | Add i18n keys |
| `web/app/src/locales/es.ts` | Modify | Add i18n keys (Spanish) |
| `web/app/src/types/index.ts` | Modify | Add ChangeRequest TypeScript interface |
| `src/notification_bc/notification/domain/enums.py` | Modify | Add CHANGE_APPROVED, CHANGE_REJECTED |
| `src/notification_bc/notification/application/services/target_resolver.py` | Modify | Add change requester resolver |
| `tests/unit/notification_bc/notification/domain/test_entities.py` | Modify | Update EventType count (51 → 53) |

### 8. `__init__.py` Files Required

```
src/change_bc/__init__.py
src/change_bc/change_request/__init__.py
src/change_bc/change_request/domain/__init__.py
src/change_bc/change_request/application/__init__.py
src/change_bc/change_request/application/commands/__init__.py
src/change_bc/change_request/application/queries/__init__.py
src/change_bc/change_request/infrastructure/__init__.py
adapters/http/api/changes/__init__.py
```

## Database Schema

```sql
CREATE TABLE change_requests (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    change_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    business_justification TEXT,
    risk_assessment TEXT,
    rollback_plan TEXT,
    planned_date TIMESTAMP WITH TIME ZONE,
    requested_by VARCHAR(26) NOT NULL,
    assigned_to VARCHAR(26),
    approved_by VARCHAR(26),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_by VARCHAR(26),
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    implemented_at TIMESTAMP WITH TIME ZONE,
    implementation_notes TEXT,
    rolled_back_at TIMESTAMP WITH TIME ZONE,
    rollback_reason TEXT,
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_change_requests_company_status ON change_requests (company_id, status);
CREATE INDEX ix_change_requests_company_type ON change_requests (company_id, change_type);
CREATE INDEX ix_change_requests_planned_date ON change_requests (planned_date);

CREATE TABLE change_events (
    id VARCHAR(26) PRIMARY KEY,
    change_request_id VARCHAR(26) NOT NULL REFERENCES change_requests(id),
    event_type VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    actor_id VARCHAR(26) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata_json JSONB
);

CREATE INDEX ix_change_events_change_request_id ON change_events (change_request_id);
```

## State Machine

```
                    ┌─── standard ───┐
                    │                │
DRAFT ──submit──►   ├── normal ──► PENDING_APPROVAL ──approve──► SCHEDULED
                    │                      │
                    │                      └──reject──► REJECTED
                    └────────────────────────────────────┘
                                                            │
                                                         start
                                                            │
                                                            ▼
                            ROLLED_BACK ◄──rollback── IN_PROGRESS
                                  ▲                        │
                                  │                    implement
                                  │                        │
                                  │                        ▼
                                  └──rollback── IMPLEMENTED ──close──► CLOSED
```

## Testing Strategy

| Test Type | Scope | Files | Priority |
|-----------|-------|-------|----------|
| Unit | Domain entities (create, transitions, validations) | `tests/unit/change_bc/change_request/domain/test_entities.py` | High |
| Unit | Domain enums (is_terminal, VALID_TRANSITIONS) | `tests/unit/change_bc/change_request/domain/test_enums.py` | High |
| Unit | Create command handler | `tests/unit/change_bc/change_request/application/commands/test_create_change_request.py` | High |
| Unit | Submit command handler | `tests/unit/change_bc/change_request/application/commands/test_submit_change_request.py` | High |
| Unit | Approve command handler | `tests/unit/change_bc/change_request/application/commands/test_approve_change_request.py` | High |
| Unit | Reject command handler | `tests/unit/change_bc/change_request/application/commands/test_reject_change_request.py` | High |
| Unit | Start/Implement/Rollback/Close handlers | `tests/unit/change_bc/.../test_*.py` | High |
| Unit | Assign command handler | `tests/unit/change_bc/.../test_assign_change.py` | Medium |
| Unit | List query handler | `tests/unit/change_bc/.../queries/test_list_change_requests.py` | High |
| Unit | Detail query handler | `tests/unit/change_bc/.../queries/test_get_change_request_detail.py` | High |
| Integration | All HTTP endpoints | `tests/integration/test_change_request_endpoints.py` | High |

## Implementation Order

1. Domain: Enums (`enums.py`)
2. Domain: Exceptions (`exceptions.py`)
3. Domain: Entities (`entities.py`)
4. Domain: Repository interface (`repository.py`)
5. Infrastructure: Models (`models.py`)
6. Infrastructure: Migration (`e33a1_*.py`)
7. Infrastructure: Repository (`repository.py`)
8. Application: Commands (all 10)
9. Application: Queries (list + detail)
10. HTTP: Schemas (`schemas.py`)
11. HTTP: Dependencies (`dependencies.py`)
12. HTTP: Router (`routers.py`)
13. Config: Register router in `app.py`, `__init__.py` files
14. Notifications: EventType entries, ChangeEventFactory, TargetResolver, router wiring
15. Tests: Unit tests (domain + commands + queries)
16. Tests: Integration tests (endpoints)
17. Frontend: TypeScript types
18. Frontend: ChangeListPage (with creation modal)
19. Frontend: ChangeDetailPage (with visual timeline, action modals)
20. Frontend: Router + navigation (Management section) + i18n

## Open Technical Questions

None — all patterns are well-established in the codebase.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Large feature (10 commands, 2 queries, 2 pages) | Medium | Scope creep | Follow patterns exactly, no extras |
| State machine complexity | Low | Bugs in transitions | Comprehensive unit tests for all transitions |
| Route conflict (dashboard vs /{change_id}) | Low | 404 errors | Dashboard endpoint registered in F3 before /{change_id} route |
