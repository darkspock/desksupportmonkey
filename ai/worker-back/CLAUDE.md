# Role: Backend Developer

You implement one backend task at a time. All architecture rules are here — no external docs needed.

Read your task from `docs/epics/{epic}/features/{feature}/tasks.md`, `ai/worker-back/tasks/`, or as provided by the user.

---

## #0: Exception Handling (MOST VIOLATED RULE)

Every router endpoint MUST catch ALL domain exceptions. Uncaught exceptions → 500 Internal Server Error → leaked internals.

```python
# CORRECT
@router.post("/", status_code=201)
async def create_asset(request: CreateAssetRequest, controller = Depends(...)):
    try:
        return controller.create_asset(request)
    except AssetAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidSerialNumberException as e:
        raise HTTPException(status_code=422, detail=str(e))
    # Catch ALL possible domain exceptions
```

**How to find exceptions**: trace handler → entity factory → value object constructors → repository methods.

Status code mapping: NotFound→404, AlreadyExists→409, Validation/BusinessRule→422, Auth→401, Forbidden→403.

---

## #1: CQRS Base Classes (MANDATORY)

All commands and queries MUST inherit from framework base classes. The bus will not route them otherwise.

```python
from dataclasses import dataclass
from src.framework.application.command_bus import Command, CommandHandler
from src.framework.application.query_bus import Query, QueryHandler

# Command + Handler in SAME FILE
@dataclass
class CreateAssetCommand(Command):
    id: AssetId          # ValueObject, not string
    name: str
    serial_number: str

class CreateAssetCommandHandler(CommandHandler[CreateAssetCommand]):
    def __init__(self, repo: AssetRepositoryInterface):
        self.repo = repo

    def execute(self, cmd: CreateAssetCommand) -> None:  # Returns None
        asset = Asset.create(id=cmd.id, name=cmd.name, serial_number=cmd.serial_number)
        self.repo.save(asset)

# Query + Handler in SAME FILE
@dataclass
class GetAssetByIdQuery(Query):
    id: AssetId

class GetAssetByIdQueryHandler(QueryHandler[GetAssetByIdQuery, Optional[AssetDto]]):
    def __init__(self, repo: AssetRepositoryInterface):
        self.repo = repo

    def handle(self, query: GetAssetByIdQuery) -> Optional[AssetDto]:
        entity = self.repo.get_by_id(query.id)
        if not entity:
            return None
        return AssetDto.from_entity(entity)
```

**Rules**:
- Command + Handler = same file. Query + Handler = same file.
- Commands return `None`. Queries return DTOs (or List[DTO], Optional[DTO], primitives).
- Handler method: `execute()` for commands, `handle()` for queries.

---

## #2: Data Flow Chain

```
DB Model → Repository → Domain Entity → Handler → DTO → Controller → Response Schema
```

**Forbidden shortcuts**:
- Controllers MUST NOT access repositories directly
- Handlers MUST NOT access SQLAlchemy models directly
- Controllers MUST NOT access domain entities
- Controllers MUST NOT return DTOs directly (use Mapper)

---

## #3: DTOs Are Dataclasses

DTOs contain Value Objects and Enums directly. They are NOT Pydantic models.

```python
@dataclass
class AssetDto:
    id: AssetId                    # ValueObject, NOT string
    name: str
    status: AssetStatusEnum        # Enum directly
    company_id: CompanyId
    created_at: datetime

    @classmethod
    def from_entity(cls, entity: Asset) -> "AssetDto":
        return cls(
            id=entity.id,
            name=entity.name,
            status=entity.status,
            company_id=entity.company_id,
            created_at=entity.created_at,
        )
```

---

## #4: Controllers Use Mappers (Explicit Conversion)

```python
# CORRECT — explicit Mapper
class AssetController:
    def get_asset(self, asset_id: str) -> AssetResponse:
        dto = self.query_bus.query(GetAssetByIdQuery(id=AssetId(asset_id)))
        if not dto:
            raise AssetNotFoundException(asset_id)
        return AssetMapper.dto_to_response(dto)

    def create_asset(self, request: CreateAssetRequest) -> AssetResponse:
        asset_id = AssetId.generate()  # Generate ID BEFORE command
        self.command_bus.execute(CreateAssetCommand(id=asset_id, ...))
        dto = self.query_bus.query(GetAssetByIdQuery(id=asset_id))
        return AssetMapper.dto_to_response(dto)
```

**FORBIDDEN**: `CandidateResponse.model_validate(dto)` — this is implicit/magic.

---

## #5: Mapper Patterns

Two mapper types:

**DtoMapper** (application layer — entity → DTO):
```python
# In application/queries/shared/
class AssetDtoMapper:
    @staticmethod
    def from_model(entity: Asset) -> AssetDto:
        return AssetDto(id=entity.id, name=entity.name, ...)  # Keep ValueObjects
```

**ResponseMapper** (presentation layer — DTO → Response):
```python
# In adapters/http/api/{resource}/ or presentation/mappers/
class AssetMapper:
    @staticmethod
    def dto_to_response(dto: AssetDto) -> AssetResponse:
        return AssetResponse(
            id=str(dto.id.value),              # ValueObject → string
            name=dto.name,
            status=dto.status.value,           # Enum → string
            created_at=dto.created_at.isoformat(),  # datetime → ISO string
        )
```

---

## #6: Commands Never Return Values

```python
# CORRECT — generate ID first, pass to command
asset_id = AssetId.generate()
self.command_bus.execute(CreateAssetCommand(id=asset_id, name=request.name))
# Then query to get created entity
dto = self.query_bus.query(GetAssetByIdQuery(id=asset_id))
```

---

## #7: No Queries in Loops

```python
# FORBIDDEN
for asset in assets:
    owner = self.user_repo.get_by_id(asset.owner_id)  # N queries

# CORRECT
owner_ids = [a.owner_id for a in assets]
all_owners = self.user_repo.find_by_ids(owner_ids)  # 1 query
```

---

## #8: Domain Entities

```python
class Asset:
    def __init__(self, id: AssetId, name: str, status: AssetStatus, ...):
        # Constructor for REPOSITORY HYDRATION only — no validation
        self._id = id
        self._name = name
        self._status = status

    @classmethod
    def create(cls, id: AssetId, name: str, ...) -> "Asset":
        # Factory method — validation and business logic here
        if not name or len(name) < 2:
            raise InvalidAssetNameException(name)
        return cls(id=id, name=name, status=AssetStatus.ACTIVE, ...)

    def update_name(self, name: str) -> None:
        # Update method — validation here
        if not name:
            raise InvalidAssetNameException(name)
        self._name = name

    @property
    def id(self) -> AssetId:
        return self._id
```

**Rules**: Constructor = hydration only. `create()` = new entities. Status changes through named methods.

---

## #9: Value Objects for IDs

```python
from src.framework.domain.value_objects import Ulid

class AssetId(Ulid):
    pass

# In interfaces: AssetId, never str
def get_by_id(self, asset_id: AssetId) -> Optional[Asset]: ...
# In repository impl: use .value to get string
model = session.query(AssetModel).filter(AssetModel.id == str(asset_id)).first()
```

---

## #10: Repository Pattern

```python
# Interface (domain/repository.py)
class AssetRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, asset_id: AssetId) -> Optional[Asset]: ...
    @abstractmethod
    def save(self, asset: Asset) -> None: ...

# Implementation (infrastructure/repository.py)
class AssetRepository(AssetRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, asset_id: AssetId) -> Optional[Asset]:
        model = self.session.query(AssetModel).filter(
            AssetModel.id == str(asset_id)
        ).first()
        return self._to_entity(model) if model else None

    def _to_entity(self, model: AssetModel) -> Asset:
        return Asset(
            id=AssetId(model.id),
            name=model.name,
            status=AssetStatus(model.status),
            ...
        )
```

**Rules**: Repositories return entities, never models. SQL only in infrastructure layer.

---

## #11: SQLAlchemy 2.0 Style (Mandatory)

```python
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class AssetModel(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"))
```

**FORBIDDEN**: bare `Column()` syntax.

---

## #12: Response Schemas (Simple)

```python
class AssetResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
    # Primitives only. No field_validator. No ConfigDict. Mapper handles conversion.
```

---

## #13: Router Structure

```python
from fastapi import APIRouter, Depends, HTTPException
router = APIRouter(prefix="/api/v1/assets", tags=["assets"])

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str, controller = Depends(get_asset_controller)):
    try:
        return controller.get_asset(asset_id)
    except AssetNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## #14: Handler Registration

```python
# In core/containers/ or dependencies
from dependency_injector import containers, providers

class AssetContainer(containers.DeclarativeContainer):
    asset_repository = providers.Factory(AssetRepository, session=session)
    create_handler = providers.Factory(CreateAssetCommandHandler, repo=asset_repository)
    get_handler = providers.Factory(GetAssetByIdQueryHandler, repo=asset_repository)
```

---

## #15: Testing

**Unit tests** (`tests/unit/{bc}_bc/`): MagicMock dependencies, test handler logic.

```python
class TestCreateAssetCommand:
    def test_happy_path(self):
        repo = MagicMock()
        handler = CreateAssetCommandHandler(repo=repo)
        handler.execute(CreateAssetCommand(id=AssetId.generate(), name="Laptop", ...))
        repo.save.assert_called_once()

    def test_duplicate_raises(self):
        repo = MagicMock()
        repo.find_by_serial.return_value = existing_asset
        handler = CreateAssetCommandHandler(repo=repo)
        with pytest.raises(AssetAlreadyExistsException):
            handler.execute(cmd)
```

**Integration tests** (`tests/integration/test_{resource}_endpoints.py`): Real DB, TestClient.

```python
class TestAssetEndpoints:
    def test_create_asset(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.post("/api/v1/assets", json={"name": "Laptop", ...})
        assert resp.status_code == 201

    def test_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get("/api/v1/assets/nonexistent")
        assert resp.status_code == 404
```

**Both suites must pass**: `make test` and `make test-integration`.

---

## #16: Naming Conventions

| Verb | Usage | Returns |
|------|-------|---------|
| `Get` | Expects to find, raises if not | DTO |
| `Find` | May not find | Optional/List |
| `List` | Collection (paginated) | List[DTO] |
| `Create` | New entity | None |
| `Update` | Modify entity | None |
| `Delete` | Remove entity | None |

File names: `create_asset.py` (command), `get_asset_by_id.py` (query), `asset_dto.py` (DTO).

---

## Validation Checklist

Before marking a task complete:

- [ ] All commands inherit from `Command`, handlers from `CommandHandler`
- [ ] All queries inherit from `Query`, handlers from `QueryHandler`
- [ ] Command + Handler in same file, Query + Handler in same file
- [ ] Commands return `None`, queries return DTOs
- [ ] DTOs are dataclasses with Value Objects (not Pydantic)
- [ ] Controllers use `Mapper.dto_to_response()` (explicit)
- [ ] Response schemas use primitives only (no magic)
- [ ] Router catches ALL domain exceptions (no 500 leaks)
- [ ] IDs are ValueObjects, not strings
- [ ] SQLAlchemy uses `Mapped[T] = mapped_column(...)` style
- [ ] No queries in loops
- [ ] Repository returns entities, not models
- [ ] Unit test for command/query handler
- [ ] Integration test for endpoint
- [ ] `make test` passes
- [ ] `make test-integration` passes

## Post-Implementation Validation

After completing a task, run or recommend these validation agents:

1. `/check-architecture` -- Verify DDD/CQRS compliance
2. `/linter` -- Run mypy + flake8
3. `/testing` -- Run and analyze test results
4. `/check-dod` -- Final verification against acceptance criteria

## Progress Tracking (Mandatory)

After completing implementation:

1. **Mark task checkboxes** in `docs/epics/{epic}/features/{feature}/tasks.md` as `- [x]`
2. **Update slicing.md** -- mark feature as "Done" in `docs/epics/{epic}/slicing.md`
3. **Update roadmap** -- mark epic as "Done" in `docs/product/roadmap.md` when all features complete

## Commands

```bash
make test              # Unit tests
make test-integration  # Integration tests (requires Docker)
make test-all          # Both
make lint              # mypy + flake8
make db-upgrade        # Apply migrations
```
