# Solution Design: Post-Implementation Review (F2)

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-27
**Bounded Context:** `change_bc`

## Summary

Add a PostImplementationReview (PIR) sub-entity to `change_bc` that captures the outcome of implemented changes. PIR is a create-once, immutable record with outcome, issues_found, lessons_learned, and follow_up_actions. For emergency-type changes, PIR is mandatory before closing. The feature follows the PostMortem pattern from `incident_bc` (same BC, single repo interface, dict-based persistence) adapted with a PIROutcome enum instead of free-text required fields.

## Architecture Decision

**Approach:** PIR as a sub-entity within the existing `change_bc.change_request` aggregate, managed through the same `ChangeRequestRepositoryInterface`. This mirrors how PostMortem is handled in `incident_bc` — a sub-entity stored via the parent's repository interface, using dict-based persistence.

**Why not a separate aggregate?** PIR has no independent lifecycle — it is always created in the context of a change request and never exists without one. It has a 1:1 relationship (unique constraint on `change_request_id`). Keeping it in the same aggregate avoids unnecessary complexity.

**PIR enforcement on close:** The `CloseChangeCommandHandler` will be modified to check for PIR existence when the change type is `emergency`. This is a simple query against the repository before allowing the close transition.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ChangeRequest entity | `src/change_bc/.../domain/entities.py` | Yes | No changes |
| ChangeEvent entity | `src/change_bc/.../domain/entities.py` | Yes | No changes |
| ChangeEventType enum | `src/change_bc/.../domain/enums.py` | Yes | Add `PIR_ADDED` value |
| Domain exceptions | `src/change_bc/.../domain/exceptions.py` | Yes | Add 2 new exceptions |
| Repository interface | `src/change_bc/.../domain/repository.py` | Yes | Add 2 PIR methods |
| Repository impl | `src/change_bc/.../infrastructure/repository.py` | Yes | Add 2 PIR methods + model mapping |
| Infrastructure models | `src/change_bc/.../infrastructure/models.py` | Yes | Add `PostImplementationReviewModel` |
| CloseChangeCommand | `src/change_bc/.../commands/close_change.py` | Yes | Add PIR guard for emergency type |
| Detail query/DTO | `src/change_bc/.../queries/get_change_request_detail.py` | Yes | Add PIR to DTO + handler |
| HTTP schemas | `adapters/http/api/changes/schemas.py` | Yes | Add PIR request/response schemas |
| Router | `adapters/http/api/changes/routers.py` | Yes | Add PIR endpoint, modify close handler |
| PostMortem pattern | `src/incident_bc/...` | Reference | Pattern adapted for PIR |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| PostImplementationReview | `src/change_bc/change_request/domain/entities.py` | Dataclass: id, change_request_id, outcome (PIROutcome), issues_found (Optional[str]), lessons_learned (Optional[str]), follow_up_actions (Optional[str]), created_by (str), created_at (Optional[datetime]). Factory method `create()` validates outcome is valid enum. |

**PostImplementationReview entity structure:**
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

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| PIROutcome | `src/change_bc/change_request/domain/enums.py` | successful, partial, failed |
| ChangeEventType | `src/change_bc/change_request/domain/enums.py` | Add `PIR_ADDED = "pir_added"` (total: 13 values) |

#### Domain Exceptions

| Exception | File Path | Description |
|-----------|-----------|-------------|
| PIRAlreadyExistsError | `src/change_bc/change_request/domain/exceptions.py` | Raised when PIR already exists for change (409) |
| PIRRequiredForEmergencyCloseError | `src/change_bc/change_request/domain/exceptions.py` | Raised when closing emergency change without PIR (422) |

#### Repository Interface

Add to `ChangeRequestRepositoryInterface`:

```python
@abstractmethod
def save_pir(self, pir: PostImplementationReview) -> None: ...

@abstractmethod
def find_pir_by_change(self, change_request_id: str) -> Optional[PostImplementationReview]: ...
```

### 2. Application Layer

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| CreatePIRCommand | CreatePIRCommandHandler | `src/change_bc/change_request/application/commands/create_pir.py` | Creates PIR for an IMPLEMENTED change |

**CreatePIRCommand fields:** `change_id`, `company_id`, `outcome` (str), `issues_found` (Optional[str]), `lessons_learned` (Optional[str]), `follow_up_actions` (Optional[str]), `performed_by` (str), `performed_by_role` (str)

**Handler logic:**
1. Find change by id + company_id → 404 if not found
2. Validate role is admin/super_admin → 403 if unauthorized
3. Validate status is IMPLEMENTED → 422 if not
4. Check for existing PIR → 409 if exists
5. Create PIR entity via factory
6. Save PIR via repository
7. Create ChangeEvent (PIR_ADDED)

**Exceptions raised:** `ChangeNotFoundError`, `UnauthorizedApprovalError`, `InvalidStatusTransitionError` (repurposed for status check), `PIRAlreadyExistsError`

Note: For the status check, we use a simple `if change.status != ChangeStatus.IMPLEMENTED` check and raise `InvalidStatusTransitionError(change.status, ChangeStatus.IMPLEMENTED)` to reuse the existing error pattern. Alternatively, a dedicated `PIRNotAllowedInStatusError` could be used, but reusing the existing pattern is simpler and consistent.

#### Modify Existing Command

| Command | File Path | Modification |
|---------|-----------|-------------|
| CloseChangeCommand | `src/change_bc/change_request/application/commands/close_change.py` | Add PIR check for emergency type |

**Modified handler logic (additions):**
1. After finding the change and checking role…
2. If `change.change_type == ChangeType.EMERGENCY`:
   - Call `self.change_repo.find_pir_by_change(change.id)`
   - If None → raise `PIRRequiredForEmergencyCloseError()`
3. Proceed with existing close logic

#### Queries (modification)

| Query | File Path | Modification |
|-------|-----------|-------------|
| GetChangeRequestDetailQuery | `src/change_bc/.../queries/get_change_request_detail.py` | Add `pir` field to DTO, load PIR in handler |

**PIRDto:**
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

**ChangeRequestDetailDto modification:**
- Add field: `pir: Optional[PIRDto] = None`

**Handler modification:**
- After loading events and assets, call `self.change_repo.find_pir_by_change(query.change_id)`
- If PIR exists, map to PIRDto (resolve created_by name via name_map)
- Set on DTO

### 3. Infrastructure Layer

#### Model

| Model | File Path | Table |
|-------|-----------|-------|
| PostImplementationReviewModel | `src/change_bc/change_request/infrastructure/models.py` | `post_implementation_reviews` |

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

#### Repository Implementation

Add to `ChangeRequestRepository`:

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

def find_pir_by_change(self, change_request_id: str) -> Optional[PostImplementationReview]:
    model = self.session.execute(
        select(PostImplementationReviewModel).where(
            PostImplementationReviewModel.change_request_id == change_request_id
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

#### Migration

| Migration | Description |
|-----------|-------------|
| `e33c1_create_post_implementation_reviews_table.py` | Creates `post_implementation_reviews` table with FK to `change_requests`, unique constraint on `change_request_id` |

### 4. HTTP Layer

#### Endpoints

| Method | Route | Auth | Request Schema | Response | Description |
|--------|-------|------|----------------|----------|-------------|
| POST | `/api/v1/changes/{change_id}/pir` | admin+ | `CreatePIRRequest` | `ChangeRequestDetailResponse` (with PIR) | Create PIR |

#### Schemas

**Request:**
```python
class CreatePIRRequest(BaseModel):
    outcome: str = Field(description="successful, partial, or failed")
    issues_found: Optional[str] = None
    lessons_learned: Optional[str] = None
    follow_up_actions: Optional[str] = None
```

**Response (added to existing):**
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

**ChangeRequestDetailResponse modification:**
- Add field: `pir: Optional[PIRResponse] = None`

#### Router Endpoint

```python
@router.post("/{change_id}/pir")
def create_pir(
    change_id: str,
    body: CreatePIRRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    change_repo = Depends(get_change_repo),
    user_repo = Depends(get_user_repo),
    asset_repo = Depends(get_asset_repo),
    db: Session = Depends(get_db),
):
    handler = CreatePIRCommandHandler(change_repo=change_repo)
    try:
        handler.handle(CreatePIRCommand(...))
    except ChangeNotFoundError:
        raise HTTPException(404, "Change request not found")
    except UnauthorizedApprovalError as e:
        raise HTTPException(403, str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(422, str(e))
    except PIRAlreadyExistsError:
        raise HTTPException(409, "A post-implementation review already exists")
    db.commit()
    return _get_detail(change_id, ...)
```

#### Close Endpoint Modification

Add `PIRRequiredForEmergencyCloseError` catch:
```python
except PIRRequiredForEmergencyCloseError as e:
    raise HTTPException(status_code=422, detail=str(e))
```

### 5. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/change_bc/.../domain/enums.py` | Add | PIROutcome enum, PIR_ADDED event type |
| `src/change_bc/.../domain/entities.py` | Add | PostImplementationReview dataclass |
| `src/change_bc/.../domain/exceptions.py` | Add | PIRAlreadyExistsError, PIRRequiredForEmergencyCloseError |
| `src/change_bc/.../domain/repository.py` | Add | 2 abstract methods (save_pir, find_pir_by_change) |
| `src/change_bc/.../infrastructure/models.py` | Add | PostImplementationReviewModel |
| `src/change_bc/.../infrastructure/repository.py` | Add | 2 method implementations |
| `src/change_bc/.../commands/close_change.py` | Modify | Add PIR guard for emergency type |
| `src/change_bc/.../queries/get_change_request_detail.py` | Modify | Add PIRDto, load PIR in handler |
| `adapters/http/api/changes/schemas.py` | Add | CreatePIRRequest, PIRResponse; modify ChangeRequestDetailResponse |
| `adapters/http/api/changes/routers.py` | Add | PIR endpoint; modify close to catch new exception |
| `web/app/src/types/index.ts` | Add | PIR interface; add to ChangeRequestDetail |
| `web/app/src/pages/admin/ChangeDetailPage.tsx` | Add | PIR section, create PIR modal |
| `web/app/src/locales/en.ts` | Add | PIR i18n keys |
| `web/app/src/locales/es.ts` | Add | PIR i18n keys |
| `tests/unit/.../domain/test_enums.py` | Modify | Update ChangeEventType count (12 → 13), add PIROutcome tests |

#### Breaking Changes

None. All changes are additive. The `pir` field on the detail response is `Optional` (defaults to `None`), so existing clients are unaffected. The close endpoint only adds a new error case for emergency type — standard and normal changes are unaffected.

## Database Schema

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

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F0 (Change Request CRUD) | Feature | ChangeRequest entity, repository, close command |
| incident_bc PostMortem | Pattern reference | Structural pattern adapted for PIR |

## Testing Strategy

| Test Type | Scope | Priority | File |
|-----------|-------|----------|------|
| Unit | PIROutcome enum | High | `tests/unit/change_bc/.../domain/test_enums.py` |
| Unit | PostImplementationReview entity | High | `tests/unit/change_bc/.../domain/test_entities.py` |
| Unit | CreatePIRCommandHandler | High | `tests/unit/change_bc/.../commands/test_create_pir.py` |
| Unit | CloseChangeCommandHandler (modified) | High | `tests/unit/change_bc/.../commands/test_close_change.py` |
| Unit | GetChangeRequestDetailQueryHandler (with PIR) | Medium | `tests/unit/change_bc/.../queries/test_get_detail.py` |
| Integration | POST /{change_id}/pir | High | `tests/integration/test_change_request_endpoints.py` |
| Integration | POST /{change_id}/close (emergency guard) | High | `tests/integration/test_change_request_endpoints.py` |

## Implementation Order

1. Domain: PIROutcome enum + PIR_ADDED event type
2. Domain: PostImplementationReview entity
3. Domain: PIRAlreadyExistsError + PIRRequiredForEmergencyCloseError exceptions
4. Domain: Repository interface (add 2 methods)
5. Infrastructure: PostImplementationReviewModel
6. Infrastructure: Repository implementation (2 methods)
7. Infrastructure: Alembic migration
8. Application: CreatePIRCommand + Handler
9. Application: Modify CloseChangeCommandHandler (emergency guard)
10. Application: Modify detail query (PIRDto, load PIR)
11. HTTP: Schemas (CreatePIRRequest, PIRResponse, modify detail response)
12. HTTP: Router (PIR endpoint, close error catch)
13. Unit tests (enums, entity, create PIR handler, close handler, detail query)
14. Integration tests (PIR endpoint, emergency close guard)
15. Frontend: Types, ChangeDetailPage PIR section, i18n keys

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ChangeEventType count test breaks | Certain | Low | Update assertion from 12 to 13 |
| Emergency close existing data | Low | Low | Only affects future closes — existing closed emergency changes are unaffected |
| Unique constraint violation on concurrent PIR creates | Low | Low | DB unique constraint catches race condition; 409 returned |

## Open Technical Questions

None. All design decisions resolved during analysis.
