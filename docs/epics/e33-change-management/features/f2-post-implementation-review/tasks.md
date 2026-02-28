# Implementation Tasks: Post-Implementation Review (F2)

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-27
**Total Tasks:** 18
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 (TASK-001) | S |
| Domain - Entities | 1 (TASK-002) | S |
| Domain - Exceptions | 1 (TASK-003) | S |
| Domain - Repository Interface | 1 (TASK-004) | S |
| Infrastructure - Model | 1 (TASK-005) | S |
| Infrastructure - Repository | 1 (TASK-006) | S |
| Infrastructure - Migration | 1 (TASK-007) | S |
| Application - Commands | 2 (TASK-008, TASK-009) | S, S |
| Application - Query Modification | 1 (TASK-010) | S |
| HTTP - Schemas | 1 (TASK-011) | S |
| HTTP - Router | 1 (TASK-012) | S |
| Unit Tests | 3 (TASK-013, TASK-014, TASK-015) | S, M, M |
| Integration Tests | 1 (TASK-016) | M |
| Frontend | 2 (TASK-017, TASK-018) | M, S |

---

## Phase 1: Domain Layer

### TASK-001: Add PIROutcome Enum + PIR_ADDED Event Type

**Phase:** Domain - Enums
**Complexity:** S
**Dependencies:** None

**Description:**
Add `PIROutcome` enum and `PIR_ADDED` value to `ChangeEventType` in the existing enums file.

**File:** `src/change_bc/change_request/domain/enums.py`

**Implementation:**

1. Add `PIROutcome` enum class:
```python
class PIROutcome(str, Enum):
    SUCCESSFUL = "successful"
    PARTIAL = "partial"
    FAILED = "failed"
```

2. Add to `ChangeEventType`:
```python
PIR_ADDED = "pir_added"
```

**Acceptance Criteria:**
- [x] `PIROutcome` enum with 3 values: successful, partial, failed
- [x] Inherits from `str, Enum`
- [x] `ChangeEventType.PIR_ADDED = "pir_added"` added (total: 13 values)

---

### TASK-002: Add PostImplementationReview Entity

**Phase:** Domain - Entities
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Add `PostImplementationReview` dataclass to the existing entities file. Follows the same pattern as `ChangeAsset` and `ChangeEvent` in the same file.

**File:** `src/change_bc/change_request/domain/entities.py`

**Implementation:**

Add import of `PIROutcome` from enums, then add dataclass:

```python
@dataclass
class PostImplementationReview:
    id: str
    change_request_id: str
    outcome: PIROutcome
    issues_found: Optional[str]
    lessons_learned: Optional[str]
    follow_up_actions: Optional[str]
    created_by: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        change_request_id: str,
        outcome: PIROutcome,
        created_by: str,
        issues_found: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        follow_up_actions: Optional[str] = None,
    ) -> "PostImplementationReview":
        return cls(
            id=str(ulid.new()),
            change_request_id=change_request_id,
            outcome=outcome,
            issues_found=issues_found,
            lessons_learned=lessons_learned,
            follow_up_actions=follow_up_actions,
            created_by=created_by,
        )
```

**Acceptance Criteria:**
- [x] Dataclass with all fields: id, change_request_id, outcome, issues_found, lessons_learned, follow_up_actions, created_by, created_at
- [x] `outcome` typed as `PIROutcome` enum
- [x] `create()` factory method generates ULID id
- [x] Optional fields default to None

---

### TASK-003: Add PIR Domain Exceptions

**Phase:** Domain - Exceptions
**Complexity:** S
**Dependencies:** None

**Description:**
Add `PIRAlreadyExistsError` and `PIRRequiredForEmergencyCloseError` to the existing exceptions file.

**File:** `src/change_bc/change_request/domain/exceptions.py`

**Implementation:**

```python
class PIRAlreadyExistsError(Exception):
    def __init__(self, change_id: str):
        super().__init__(
            f"A post-implementation review already exists for change '{change_id}'"
        )
        self.change_id = change_id


class PIRRequiredForEmergencyCloseError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Emergency changes require a post-implementation review before closing"
        )
```

**Acceptance Criteria:**
- [x] `PIRAlreadyExistsError` stores `change_id`, maps to HTTP 409
- [x] `PIRRequiredForEmergencyCloseError` has descriptive message, maps to HTTP 422

---

### TASK-004: Add PIR Methods to Repository Interface

**Phase:** Domain - Repository Interface
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add `save_pir` and `find_pir_by_change` abstract methods to `ChangeRequestRepositoryInterface`.

**File:** `src/change_bc/change_request/domain/repository.py`

**Implementation:**

1. Add import of `PostImplementationReview` from entities
2. Add abstract methods:

```python
# PostImplementationReview
@abstractmethod
def save_pir(self, pir: PostImplementationReview) -> None: ...

@abstractmethod
def find_pir_by_change(
    self, change_request_id: str
) -> Optional[PostImplementationReview]: ...
```

**Acceptance Criteria:**
- [x] `save_pir(pir: PostImplementationReview) -> None` abstract method added
- [x] `find_pir_by_change(change_request_id: str) -> Optional[PostImplementationReview]` abstract method added
- [x] `PostImplementationReview` imported from entities

---

## Phase 2: Infrastructure Layer

### TASK-005: Add PostImplementationReviewModel

**Phase:** Infrastructure - Model
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add `PostImplementationReviewModel` SQLAlchemy model to the existing models file. Uses `ULIDMixin` and `Base` like existing models.

**File:** `src/change_bc/change_request/infrastructure/models.py`

**Implementation:**

```python
class PostImplementationReviewModel(ULIDMixin, Base):
    __tablename__ = "post_implementation_reviews"

    change_request_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("change_requests.id"), nullable=False
    )
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    issues_found: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_actions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("change_request_id", name="uq_pir_change_request"),
    )
```

**Acceptance Criteria:**
- [x] Table name `post_implementation_reviews`
- [x] All columns with `Mapped[]` annotations (SQLAlchemy 2.0 style)
- [x] FK to `change_requests.id`
- [x] UniqueConstraint on `change_request_id`
- [x] Uses `ULIDMixin`, `Base`

---

### TASK-006: Add PIR Repository Methods

**Phase:** Infrastructure - Repository
**Complexity:** S
**Dependencies:** TASK-004, TASK-005

**Description:**
Add `save_pir` and `find_pir_by_change` implementations to `ChangeRequestRepository`.

**File:** `src/change_bc/change_request/infrastructure/repository.py`

**Implementation:**

1. Add imports: `PostImplementationReview` from entities, `PIROutcome` from enums, `PostImplementationReviewModel` from models
2. Add methods:

```python
def save_pir(self, pir: PostImplementationReview) -> None:
    model = PostImplementationReviewModel(
        id=pir.id,
        change_request_id=pir.change_request_id,
        outcome=pir.outcome.value,
        issues_found=pir.issues_found,
        lessons_learned=pir.lessons_learned,
        follow_up_actions=pir.follow_up_actions,
        created_by=pir.created_by,
    )
    self.session.add(model)
    self.session.flush()

def find_pir_by_change(
    self, change_request_id: str
) -> Optional[PostImplementationReview]:
    model = self.session.execute(
        select(PostImplementationReviewModel).where(
            PostImplementationReviewModel.change_request_id
            == change_request_id
        )
    ).scalar_one_or_none()
    if not model:
        return None
    return PostImplementationReview(
        id=model.id,
        change_request_id=model.change_request_id,
        outcome=PIROutcome(model.outcome),
        issues_found=model.issues_found,
        lessons_learned=model.lessons_learned,
        follow_up_actions=model.follow_up_actions,
        created_by=model.created_by,
        created_at=model.created_at,
    )
```

**Acceptance Criteria:**
- [x] `save_pir` persists model and flushes
- [x] `find_pir_by_change` returns entity with `PIROutcome` enum or None
- [x] Model-to-entity conversion maps all fields correctly

---

### TASK-007: Create Alembic Migration

**Phase:** Infrastructure - Migration
**Complexity:** S
**Dependencies:** TASK-005

**Description:**
Create Alembic migration for `post_implementation_reviews` table.

**File:** `alembic/versions/e33c1_create_post_implementation_reviews_table.py`

**Schema:**
```sql
CREATE TABLE post_implementation_reviews (
    id VARCHAR(26) PRIMARY KEY,
    change_request_id VARCHAR(26) NOT NULL REFERENCES change_requests(id),
    outcome VARCHAR(20) NOT NULL,
    issues_found TEXT,
    lessons_learned TEXT,
    follow_up_actions TEXT,
    created_by VARCHAR(26) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_pir_change_request UNIQUE (change_request_id)
);
CREATE INDEX ix_pir_change_request_id ON post_implementation_reviews(change_request_id);
```

**Acceptance Criteria:**
- [x] Creates `post_implementation_reviews` table
- [x] FK to `change_requests(id)`
- [x] Unique constraint on `change_request_id`
- [x] Index on `change_request_id`
- [x] Reversible (downgrade drops table)

---

## Phase 3: Application Layer

### TASK-008: Create CreatePIRCommand + Handler

**Phase:** Application - Commands
**Complexity:** S
**Dependencies:** TASK-002, TASK-003, TASK-004

**Description:**
Create command and handler for PIR creation. Command and handler in same file per architecture rules.

**File:** `src/change_bc/change_request/application/commands/create_pir.py`

**Implementation:**

```python
@dataclass
class CreatePIRCommand(Command):
    change_id: str
    company_id: str
    outcome: str
    issues_found: Optional[str]
    lessons_learned: Optional[str]
    follow_up_actions: Optional[str]
    performed_by: str
    performed_by_role: str


class CreatePIRCommandHandler(CommandHandler[CreatePIRCommand]):
    def __init__(self, change_repo: ChangeRequestRepositoryInterface):
        self.change_repo = change_repo

    def handle(self, command: CreatePIRCommand) -> None:
        # 1. Find change
        change = self.change_repo.find_by_id(command.change_id, command.company_id)
        if not change:
            raise ChangeNotFoundError(command.change_id)

        # 2. Auth check
        if command.performed_by_role not in ("admin", "super_admin"):
            raise UnauthorizedApprovalError()

        # 3. Status check
        if change.status != ChangeStatus.IMPLEMENTED:
            raise InvalidStatusTransitionError(change.status, ChangeStatus.IMPLEMENTED)

        # 4. Duplicate check
        existing = self.change_repo.find_pir_by_change(command.change_id)
        if existing:
            raise PIRAlreadyExistsError(command.change_id)

        # 5. Create PIR
        pir = PostImplementationReview.create(
            change_request_id=command.change_id,
            outcome=PIROutcome(command.outcome),
            created_by=command.performed_by,
            issues_found=command.issues_found,
            lessons_learned=command.lessons_learned,
            follow_up_actions=command.follow_up_actions,
        )
        self.change_repo.save_pir(pir)

        # 6. Audit event
        event = ChangeEvent.create(
            change_request_id=command.change_id,
            event_type=ChangeEventType.PIR_ADDED,
            description="Post-implementation review added",
            actor_id=command.performed_by,
        )
        self.change_repo.save_event(event)
```

**Acceptance Criteria:**
- [x] Inherits `Command` / `CommandHandler` from framework
- [x] Validates change exists (404)
- [x] Validates admin role (403)
- [x] Validates IMPLEMENTED status (422)
- [x] Checks for existing PIR (409)
- [x] Creates PIR entity via factory
- [x] Saves PIR via repository
- [x] Creates PIR_ADDED ChangeEvent

---

### TASK-009: Modify CloseChangeCommandHandler for Emergency PIR Guard

**Phase:** Application - Commands
**Complexity:** S
**Dependencies:** TASK-003, TASK-004

**Description:**
Modify existing `CloseChangeCommandHandler` to check for PIR existence when closing emergency-type changes.

**File:** `src/change_bc/change_request/application/commands/close_change.py`

**Modifications:**

1. Add imports: `ChangeType` from enums, `PIRRequiredForEmergencyCloseError` from exceptions
2. After auth check, before `change.close()`, add:

```python
if change.change_type == ChangeType.EMERGENCY:
    pir = self.change_repo.find_pir_by_change(change.id)
    if not pir:
        raise PIRRequiredForEmergencyCloseError()
```

**Acceptance Criteria:**
- [x] Emergency type changes: raise `PIRRequiredForEmergencyCloseError` if no PIR exists
- [x] Standard type changes: close without PIR check (unchanged behavior)
- [x] Normal type changes: close without PIR check (unchanged behavior)
- [x] Existing close logic unchanged after the guard

---

### TASK-010: Modify Detail Query to Include PIR

**Phase:** Application - Query Modification
**Complexity:** S
**Dependencies:** TASK-004, TASK-006

**Description:**
Add `PIRDto` dataclass and modify `GetChangeRequestDetailQueryHandler` to load and include PIR data.

**File:** `src/change_bc/change_request/application/queries/get_change_request_detail.py`

**Implementation:**

1. Add `PIRDto` dataclass:
```python
@dataclass
class PIRDto:
    id: str
    outcome: str
    issues_found: Optional[str]
    lessons_learned: Optional[str]
    follow_up_actions: Optional[str]
    created_by: str
    created_by_name: Optional[str]
    created_at: Optional[datetime]
```

2. Add to `ChangeRequestDetailDto`:
```python
pir: Optional[PIRDto] = None
```

3. In handler, after loading affected_assets and before returning DTO:
```python
# Resolve PIR
pir_dto: Optional[PIRDto] = None
pir = self.change_repo.find_pir_by_change(query.change_id)
if pir:
    if pir.created_by and pir.created_by not in name_map and self.user_name_resolver:
        extra = self.user_name_resolver([pir.created_by])
        name_map.update(extra)
    pir_dto = PIRDto(
        id=pir.id,
        outcome=pir.outcome.value,
        issues_found=pir.issues_found,
        lessons_learned=pir.lessons_learned,
        follow_up_actions=pir.follow_up_actions,
        created_by=pir.created_by,
        created_by_name=name_map.get(pir.created_by),
        created_at=pir.created_at,
    )
```

4. Include `pir=pir_dto` in the returned `ChangeRequestDetailDto(...)`.

**Acceptance Criteria:**
- [x] `PIRDto` dataclass with all fields from design
- [x] `pir: Optional[PIRDto] = None` added to `ChangeRequestDetailDto`
- [x] Handler loads PIR via `find_pir_by_change`
- [x] PIR `created_by` resolved to name via `user_name_resolver`
- [x] Returns `None` when no PIR exists (existing responses unaffected)

---

## Phase 4: HTTP Layer

### TASK-011: Add PIR Schemas

**Phase:** HTTP - Schemas
**Complexity:** S
**Dependencies:** TASK-010

**Description:**
Add request and response schemas for PIR. Modify `ChangeRequestDetailResponse` to include PIR.

**File:** `adapters/http/api/changes/schemas.py`

**Implementation:**

1. Add request schema:
```python
class CreatePIRRequest(BaseModel):
    outcome: str = Field(description="successful, partial, or failed")
    issues_found: Optional[str] = None
    lessons_learned: Optional[str] = None
    follow_up_actions: Optional[str] = None
```

2. Add response schema:
```python
class PIRResponse(BaseModel):
    id: str
    outcome: str
    issues_found: Optional[str] = None
    lessons_learned: Optional[str] = None
    follow_up_actions: Optional[str] = None
    created_by: str
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
```

3. Add to `ChangeRequestDetailResponse`:
```python
pir: Optional[PIRResponse] = None
```

**Acceptance Criteria:**
- [x] `CreatePIRRequest` with outcome (required) and 3 optional text fields
- [x] `PIRResponse` with all fields from design
- [x] `ChangeRequestDetailResponse.pir: Optional[PIRResponse] = None`

---

### TASK-012: Add PIR Router Endpoint + Modify Close Handler

**Phase:** HTTP - Router
**Complexity:** S
**Dependencies:** TASK-008, TASK-009, TASK-011

**Description:**
Add `POST /{change_id}/pir` endpoint and modify the close endpoint to catch `PIRRequiredForEmergencyCloseError`.

**File:** `adapters/http/api/changes/routers.py`

**Implementation:**

1. Add imports: `CreatePIRCommand`, `CreatePIRCommandHandler`, `CreatePIRRequest`, `PIRResponse`, `PIRAlreadyExistsError`, `PIRRequiredForEmergencyCloseError`

2. Add PIR endpoint:
```python
@router.post("/{change_id}/pir")
def create_pir(
    change_id: str,
    body: CreatePIRRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo=Depends(get_asset_repo),
    db: Session = Depends(get_db),
):
    handler = CreatePIRCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            CreatePIRCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                outcome=body.outcome,
                issues_found=body.issues_found,
                lessons_learned=body.lessons_learned,
                follow_up_actions=body.follow_up_actions,
                performed_by=current_user.id,
                performed_by_role=current_user.role.value,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except UnauthorizedApprovalError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PIRAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="A post-implementation review already exists for this change",
        )
    db.commit()
    return _get_detail(
        change_id, current_user.company_id, change_repo, user_repo, asset_repo
    )
```

3. Modify existing `close_change` endpoint — add to except chain:
```python
except PIRRequiredForEmergencyCloseError as e:
    raise HTTPException(status_code=422, detail=str(e))
```

4. Update `_get_detail` helper to handle PIR in the detail response serialization (map `pir` field from DTO to `PIRResponse` if present).

**Acceptance Criteria:**
- [x] `POST /{change_id}/pir` endpoint with admin+ auth
- [x] Catches all domain exceptions: 404, 403, 422, 409
- [x] Returns full change detail response (with PIR)
- [x] Close endpoint catches `PIRRequiredForEmergencyCloseError` → 422
- [x] `_get_detail` handles `pir` field in DTO → PIRResponse serialization

---

## Phase 5: Tests

### TASK-013: Unit Tests — Domain (Enums + Entity)

**Phase:** Tests - Unit
**Complexity:** S
**Dependencies:** TASK-001, TASK-002

**Description:**
Add PIROutcome enum tests and PostImplementationReview entity tests. Update ChangeEventType count test.

**Files:**
- `tests/unit/change_bc/change_request/domain/test_enums.py` (modify)
- `tests/unit/change_bc/change_request/domain/test_entities.py` (modify or create)

**Test Cases for PIROutcome:**
- Test values: successful, partial, failed
- Test count: 3

**Test Cases for PostImplementationReview entity:**
- `create()` factory sets all fields correctly
- `create()` generates ULID id
- `create()` sets optional fields to None when not provided
- `create()` preserves provided optional fields

**Test case for ChangeEventType:**
- Update count assertion from 12 to 13
- Test `PIR_ADDED == "pir_added"`

**Acceptance Criteria:**
- [x] PIROutcome enum: values and count tests
- [x] PostImplementationReview: factory method tests
- [x] ChangeEventType count updated to 13
- [x] ChangeEventType.PIR_ADDED tested

---

### TASK-014: Unit Tests — CreatePIRCommandHandler

**Phase:** Tests - Unit
**Complexity:** M
**Dependencies:** TASK-008

**Description:**
Unit tests for CreatePIRCommandHandler with all validation paths.

**File:** `tests/unit/change_bc/change_request/application/commands/test_create_pir.py`

**Test Cases:**
- Happy path: creates PIR for IMPLEMENTED change with admin role
- Change not found → raises `ChangeNotFoundError`
- Non-admin role → raises `UnauthorizedApprovalError`
- Change not in IMPLEMENTED status → raises `InvalidStatusTransitionError`
- PIR already exists → raises `PIRAlreadyExistsError`
- Verify PIR entity saved via `save_pir`
- Verify ChangeEvent created with `PIR_ADDED` type
- Verify all fields passed through to entity

**Acceptance Criteria:**
- [x] All 8 test cases
- [x] Uses `MagicMock` for repository
- [x] Validates correct exception types raised
- [x] Verifies `save_pir` and `save_event` calls

---

### TASK-015: Unit Tests — CloseChangeCommandHandler (Emergency PIR Guard)

**Phase:** Tests - Unit
**Complexity:** M
**Dependencies:** TASK-009

**Description:**
Unit tests for the modified close handler with emergency PIR enforcement.

**File:** `tests/unit/change_bc/change_request/application/commands/test_close_change.py`

**Test Cases:**
- Emergency change with PIR exists → closes successfully
- Emergency change without PIR → raises `PIRRequiredForEmergencyCloseError`
- Standard change without PIR → closes successfully (no PIR check)
- Normal change without PIR → closes successfully (no PIR check)

**Acceptance Criteria:**
- [x] Emergency type: PIR required test
- [x] Emergency type: PIR present allows close
- [x] Standard type: closes without PIR
- [x] Normal type: closes without PIR
- [x] Uses `MagicMock` for repository

---

### TASK-016: Integration Tests — PIR Endpoint + Emergency Close Guard

**Phase:** Tests - Integration
**Complexity:** M
**Dependencies:** TASK-012

**Description:**
Integration tests for the PIR HTTP endpoint and the emergency close guard.

**File:** `tests/integration/test_change_request_endpoints.py` (add to existing)

**Test Cases:**
- `POST /{change_id}/pir` — happy path: change in IMPLEMENTED status, admin creates PIR, response includes PIR
- `POST /{change_id}/pir` — 409: duplicate PIR creation
- `POST /{change_id}/pir` — 422: change not in IMPLEMENTED status
- `POST /{change_id}/pir` — 404: change not found
- `POST /{change_id}/close` — emergency change without PIR → 422
- `POST /{change_id}/close` — emergency change with PIR → 200
- `POST /{change_id}/close` — standard change without PIR → 200 (unchanged behavior)
- Detail endpoint returns PIR data when PIR exists
- Detail endpoint returns `pir: null` when no PIR exists

**Acceptance Criteria:**
- [x] PIR creation happy path returns detail with PIR section
- [x] Duplicate PIR returns 409
- [x] Invalid status returns 422
- [x] Emergency close without PIR returns 422
- [x] Emergency close with PIR succeeds
- [x] Standard close without PIR still succeeds
- [x] Detail response includes PIR when present

---

## Phase 6: Frontend

### TASK-017: Add PIR Section to ChangeDetailPage

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-012

**Description:**
Add PIR TypeScript interface, PIR section on change detail page, and create PIR modal.

**Files:**
- `web/app/src/types/index.ts` — Add `PIR` interface, add `pir` field to `ChangeRequestDetail`
- `web/app/src/pages/admin/ChangeDetailPage.tsx` — Add PIR section and create modal

**TypeScript interface:**
```typescript
export interface PIR {
  id: string;
  outcome: string;
  issues_found: string | null;
  lessons_learned: string | null;
  follow_up_actions: string | null;
  created_by: string;
  created_by_name: string | null;
  created_at: string | null;
}

// Add to ChangeRequestDetail:
pir: PIR | null;
```

**ChangeDetailPage additions:**
- Add `pir_added` to eventIcon (ClipboardCheck) and eventColor (green) maps
- Add state: `showCreatePIR` (boolean)
- Add `createPIRMutation` (POST `/{change_id}/pir`)
- PIR section card between affected assets and timeline:
  - If PIR exists: show outcome badge (green/yellow/red), issues_found, lessons_learned, follow_up_actions, created_by_name, created_at
  - If no PIR and status is IMPLEMENTED: show "Add Review" button
  - If no PIR and status is not IMPLEMENTED: hide section
- Create PIR modal:
  - Outcome select (successful/partial/failed)
  - Issues found textarea (optional)
  - Lessons learned textarea (optional)
  - Follow-up actions textarea (optional)
  - Submit button

**Acceptance Criteria:**
- [x] PIR TypeScript interface added
- [x] PIR section shows outcome badge + text fields when PIR exists
- [x] "Add Review" button shown for IMPLEMENTED changes without PIR
- [x] Section hidden when no PIR and status is not IMPLEMENTED
- [x] Create PIR modal with outcome select + 3 optional textareas
- [x] Mutation invalidates change detail query on success
- [x] `pir_added` event type in timeline icon/color maps

---

### TASK-018: Add PIR i18n Keys

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None

**Description:**
Add i18n keys for PIR section and outcome enum values.

**Files:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**Keys to add (en):**
```typescript
'page.change_detail.event_pir_added': 'Review Added',
'page.change_detail.pir_section': 'Post-Implementation Review',
'page.change_detail.pir_outcome': 'Outcome',
'page.change_detail.pir_outcome_successful': 'Successful',
'page.change_detail.pir_outcome_partial': 'Partial Success',
'page.change_detail.pir_outcome_failed': 'Failed',
'page.change_detail.pir_issues_found': 'Issues Found',
'page.change_detail.pir_lessons_learned': 'Lessons Learned',
'page.change_detail.pir_follow_up_actions': 'Follow-up Actions',
'page.change_detail.pir_add_review': 'Add Review',
'page.change_detail.pir_create_title': 'Create Post-Implementation Review',
'page.change_detail.pir_select_outcome': 'Select outcome...',
'page.change_detail.toast_pir_created': 'Post-implementation review created',
'page.change_detail.error_pir_create': 'Failed to create review',
```

**Keys to add (es):**
```typescript
'page.change_detail.event_pir_added': 'Revisión Agregada',
'page.change_detail.pir_section': 'Revisión Post-Implementación',
'page.change_detail.pir_outcome': 'Resultado',
'page.change_detail.pir_outcome_successful': 'Exitoso',
'page.change_detail.pir_outcome_partial': 'Éxito Parcial',
'page.change_detail.pir_outcome_failed': 'Fallido',
'page.change_detail.pir_issues_found': 'Problemas Encontrados',
'page.change_detail.pir_lessons_learned': 'Lecciones Aprendidas',
'page.change_detail.pir_follow_up_actions': 'Acciones de Seguimiento',
'page.change_detail.pir_add_review': 'Agregar Revisión',
'page.change_detail.pir_create_title': 'Crear Revisión Post-Implementación',
'page.change_detail.pir_select_outcome': 'Seleccionar resultado...',
'page.change_detail.toast_pir_created': 'Revisión post-implementación creada',
'page.change_detail.error_pir_create': 'Error al crear la revisión',
```

**Acceptance Criteria:**
- [x] 14 English i18n keys added
- [x] 14 Spanish i18n keys added
- [x] Keys cover: event type, section title, outcome values, field labels, modal, toasts

---

## Dependency Graph

```
TASK-001 (Enums) ─────────────────┐
                                   ├──→ TASK-002 (Entity) ──→ TASK-004 (Repo Interface)
TASK-003 (Exceptions) ────────────┤                                    │
                                   │                                    │
                                   │    TASK-005 (Model) ──────────────┤
                                   │                                    │
                                   │                      TASK-006 (Repo Impl) ──┐
                                   │                                              │
                                   ├──→ TASK-008 (CreatePIR Cmd) ───────────────┤
                                   │                                              │
                                   ├──→ TASK-009 (Close Cmd Mod) ───────────────┤
                                   │                                              │
                                   │    TASK-010 (Detail Query Mod) ────────────┤
                                   │                                              │
                                   │    TASK-011 (Schemas) ────────────────────┤
                                   │                                              │
                                   └──→ TASK-012 (Router) ─────────────────────┤
                                                                                │
TASK-007 (Migration) ── standalone                                              │
TASK-018 (i18n) ── standalone                                                   │
                                                                                │
                                   TASK-013 (Unit: Domain) ←── TASK-001,002     │
                                   TASK-014 (Unit: CreatePIR) ←── TASK-008      │
                                   TASK-015 (Unit: Close) ←── TASK-009          │
                                   TASK-016 (Integration) ←── TASK-012          │
                                   TASK-017 (Frontend) ←── TASK-012             │
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-003, TASK-018
**Batch 2 (Sequential after Batch 1):** TASK-002
**Batch 3 (Parallel after Batch 2):** TASK-004, TASK-005
**Batch 4 (Parallel after Batch 3):** TASK-006, TASK-007
**Batch 5 (Parallel after Batch 4):** TASK-008, TASK-009, TASK-010
**Batch 6 (Sequential after Batch 5):** TASK-011
**Batch 7 (Sequential after Batch 6):** TASK-012
**Batch 8 (Parallel after Batch 7):** TASK-013, TASK-014, TASK-015, TASK-016, TASK-017

## Final Checklist

- [x] All 18 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] TypeScript compiles (`npx tsc --noEmit`)
- [x] mypy passes
- [x] Progress tracking updated (tasks.md, slicing.md, roadmap.md)
