# Design: F1 — Company Configuration

**Requirement:** [../../requirements.md](../../requirements.md)
**Feature:** F1 — Company Configuration
**Date:** 2026-02-18

---

## Architecture Overview

```
NEW FILES:
src/company_bc/classification_config/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities.py                  # CompanyClassificationConfig
│   └── repository.py               # ClassificationConfigRepositoryInterface
├── infrastructure/
│   ├── __init__.py
│   ├── models.py                    # ClassificationConfigModel
│   └── repository.py               # ClassificationConfigRepository
└── application/
    ├── __init__.py
    ├── commands/
    │   ├── __init__.py
    │   └── save_config.py           # SaveClassificationConfigCommand + Handler
    └── queries/
        ├── __init__.py
        └── get_config.py            # GetClassificationConfigQuery + Handler

adapters/http/api/settings/
├── classification_router.py         # PUT/GET endpoints
├── classification_schemas.py        # Request/Response schemas
└── classification_dependencies.py   # DI factory

alembic/versions/
└── xxx_create_classification_config.py

MODIFIED FILES:
app.py                               # Register new router
```

---

## Domain Layer

### CompanyClassificationConfig Entity

```python
from src.company_bc.assignment_config.domain.enums import AIProvider

@dataclass
class CompanyClassificationConfig:
    id: str
    company_id: str
    is_enabled: bool
    provider: AIProvider
    model: Optional[str]
    confidence_threshold: float
    prompt_template: Optional[str]
    timeout_seconds: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, company_id, is_enabled, provider, model,
               confidence_threshold, prompt_template, timeout_seconds,
               id=None) -> "CompanyClassificationConfig":
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            is_enabled=is_enabled,
            provider=provider,
            model=model,
            confidence_threshold=confidence_threshold,
            prompt_template=prompt_template,
            timeout_seconds=timeout_seconds,
            created_at=None,
            updated_at=None,
        )
```

### Repository Interface

```python
class ClassificationConfigRepositoryInterface(ABC):
    @abstractmethod
    def save(self, config: CompanyClassificationConfig) -> CompanyClassificationConfig: ...

    @abstractmethod
    def find_by_company(self, company_id: str) -> Optional[CompanyClassificationConfig]: ...
```

---

## Infrastructure Layer

### SQLAlchemy Model

```python
class ClassificationConfigModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "company_classification_configs"
    __table_args__ = (UniqueConstraint("company_id"),)

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.7)
    prompt_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=10)
```

### Migration

```sql
CREATE TABLE company_classification_configs (
    id CHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    provider VARCHAR(20) NOT NULL,
    model VARCHAR(100),
    confidence_threshold FLOAT NOT NULL DEFAULT 0.7,
    prompt_template TEXT,
    timeout_seconds INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (company_id)
);
CREATE INDEX ix_company_classification_configs_company_id ON company_classification_configs(company_id);
```

### Repository Implementation

```python
class ClassificationConfigRepository(ClassificationConfigRepositoryInterface):
    def __init__(self, db: Session): ...
    def save(self, config) -> CompanyClassificationConfig:
        # Upsert pattern: check existing by company_id, update or insert
    def find_by_company(self, company_id) -> Optional[CompanyClassificationConfig]:
        # Select by company_id
    @staticmethod
    def _to_entity(model) -> CompanyClassificationConfig:
        # Reconstruct AIProvider(model.provider) enum
```

---

## Application Layer

### Save Command

```python
@dataclass
class SaveClassificationConfigCommand(Command):
    company_id: str
    is_enabled: bool
    provider: str
    model: Optional[str]
    confidence_threshold: float
    prompt_template: Optional[str]
    timeout_seconds: int
    performed_by: str

class SaveClassificationConfigCommandHandler(CommandHandler[SaveClassificationConfigCommand]):
    def __init__(self, config_repo: ClassificationConfigRepositoryInterface): ...
    def handle(self, command) -> None:
        # Validate AIProvider(command.provider) — raise InvalidProviderError
        # Validate 0.5 <= confidence_threshold <= 1.0
        # Validate timeout_seconds >= 1
        # Create or update config
```

### Get Query

```python
@dataclass
class GetClassificationConfigQuery(Query):
    company_id: str

@dataclass(frozen=True)
class ClassificationConfigDTO:
    id: str
    company_id: str
    is_enabled: bool
    provider: str
    model: Optional[str]
    confidence_threshold: float
    prompt_template: Optional[str]
    timeout_seconds: int
    created_at: Optional[str]
    updated_at: Optional[str]

class GetClassificationConfigQueryHandler(
    QueryHandler[GetClassificationConfigQuery, Optional[ClassificationConfigDTO]]
):
    def __init__(self, config_repo: ClassificationConfigRepositoryInterface): ...
    def handle(self, query) -> Optional[ClassificationConfigDTO]:
        # Return DTO (not entity) per architecture Rule #2
```

---

## HTTP Layer

### Schemas

```python
class SaveClassificationConfigRequest(BaseModel):
    is_enabled: bool
    provider: str = Field(min_length=1)
    model: Optional[str] = Field(default=None, max_length=100)
    confidence_threshold: float = Field(ge=0.5, le=1.0, default=0.7)
    prompt_template: Optional[str] = Field(default=None)
    timeout_seconds: int = Field(ge=1, le=60, default=10)

class ClassificationConfigResponse(BaseModel):
    id: str
    company_id: str
    is_enabled: bool
    provider: str
    model: Optional[str]
    confidence_threshold: float
    prompt_template: Optional[str]
    timeout_seconds: int
    created_at: Optional[str]
    updated_at: Optional[str]
```

### Router

```python
router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

@router.put("/request-classification")
def save_classification_config(
    body: SaveClassificationConfigRequest,
    current_user = Depends(require_role(UserRole.ADMIN)),
    config_repo = Depends(get_classification_config_repo),
): ...

@router.get("/request-classification")
def get_classification_config(
    current_user = Depends(require_role(UserRole.ADMIN)),
    config_repo = Depends(get_classification_config_repo),
): ...
```

### Registration in app.py

```python
from adapters.http.api.settings.classification_router import router as classification_settings_router
application.include_router(classification_settings_router)
```

---

## Testing Strategy

### Unit (~7 tests)
- Save: creates new config, updates existing, invalid provider raises, invalid threshold raises, invalid timeout raises
- Get: returns DTO when found, returns None when not found

### Integration (~7 tests)
- PUT: admin saves → 200, non-admin → 403, invalid provider → 422, invalid threshold → 422
- GET: returns config → 200, no config → 200 null, non-admin → 403

---

## Design Decisions

1. **`AIProvider` reused from `assignment_config.domain.enums`** — cross-subdomain import within same BC (`company_bc`). Acceptable since both subdomains share the AI provider concept. If a third subdomain needs it, extract to a shared `ai_bc`.
2. **Entity field `provider: AIProvider`** — typed enum, not raw string. Matches `CompanyAssignmentAIConfig` pattern.
3. **Query returns `ClassificationConfigDTO`** — follows architecture Rule #2 (queries return DTOs, not entities).
4. **Separate router file** (`classification_router.py`) — avoids modifying the existing `settings/routers.py`. FastAPI supports multiple routers with the same prefix. No path collision since endpoints use different paths (`/request-classification` vs `/assignment-ai`).
5. **`prompt_template` is nullable** — unlike `assignment_config` where it's required, classification custom instructions are optional.
