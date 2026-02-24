# Solution Design: F0 — Definition CRUD

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Bounded Context:** `custom_field_bc`

## Summary

Create the `custom_field_bc` bounded context with the `CustomFieldDefinition` entity, full CRUD API, Enterprise plan gating, and an admin UI page. This is the foundation feature — all other features depend on field definitions existing.

## Architecture Decision

New BC: `custom_field_bc` with subdomain `definition`. Follows the same pattern as `sla_bc/sla/` — separate domain, application, infrastructure layers. The BC owns only field definitions; values live on target entities (F1).

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| Framework base classes | `src/framework/application/` | Yes | None — inherit Command, CommandHandler, Query, QueryHandler |
| Plan gate | `src/company_bc/company/domain/plan_gate.py` | Yes | None — `custom_fields` already in `_ENTERPRISE_FEATURES` |
| `require_plan_feature` | `adapters/http/api/auth/dependencies.py` | Yes | None — use `require_plan_feature("custom_fields")` |
| ULIDMixin, TimestampMixin, Base | `src/framework/infrastructure/` | Yes | None — inherit for models |
| `app.py` | `app.py` | — | Add `include_router(custom_fields_router)` |
| `tests/conftest.py` | `tests/conftest.py` | — | Import `CustomFieldDefinitionModel` |

## Implementation Plan

### 1. Domain Layer

#### Enums
| Enum | File Path | Values |
|------|-----------|--------|
| `EntityType` | `src/custom_field_bc/definition/domain/enums.py` | `asset`, `request`, `incident` |
| `FieldType` | `src/custom_field_bc/definition/domain/enums.py` | `text`, `number`, `date`, `select`, `multi_select`, `boolean` |

#### Entities
| Entity | File Path | Description |
|--------|-----------|-------------|
| `CustomFieldDefinition` | `src/custom_field_bc/definition/domain/entities.py` | Main entity |

```python
@dataclass
class CustomFieldDefinition:
    id: str
    company_id: str
    entity_type: str          # EntityType value
    field_key: str             # auto-slug from label
    label: str
    description: Optional[str]
    field_type: str            # FieldType value
    options: Optional[list[str]]  # for select/multi_select
    required: bool
    sort_order: int
    is_active: bool
    visible_to_employees: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, company_id, entity_type, label, field_type, ...) -> "CustomFieldDefinition":
        field_key = cls._slugify(label)
        # validate options required for select/multi_select
        # validate options empty for other types
        return cls(id=str(ulid.new()), ...)

    @staticmethod
    def _slugify(label: str) -> str:
        """lowercase, spaces→underscores, strip special chars, max 50"""

    def update(self, label, description, required, options, visible_to_employees):
        """Update mutable fields. field_type and field_key are immutable."""

    def deactivate(self): ...
    def activate(self): ...
```

#### Exceptions
| Exception | File Path | Description |
|-----------|-----------|-------------|
| `FieldDefinitionNotFoundError` | `src/custom_field_bc/definition/domain/exceptions.py` | 404 |
| `DuplicateFieldKeyError` | same | Slug collision → 409 |
| `MaxFieldsExceededError` | same | > 20 fields → 422 |
| `InvalidFieldTypeError` | same | Bad type value |
| `OptionsRequiredError` | same | select/multi_select without options |

#### Repository Interface
| Method | Signature |
|--------|-----------|
| `save` | `(definition: CustomFieldDefinition) -> None` |
| `find_by_id` | `(id: str, company_id: str) -> Optional[CustomFieldDefinition]` |
| `find_by_entity_type` | `(company_id: str, entity_type: str) -> list[CustomFieldDefinition]` |
| `find_active_by_entity_type` | `(company_id: str, entity_type: str) -> list[CustomFieldDefinition]` |
| `count_by_entity_type` | `(company_id: str, entity_type: str) -> int` |
| `has_field_key` | `(company_id: str, entity_type: str, field_key: str) -> bool` |
| `delete` | `(id: str) -> None` |
| `bulk_update_sort_order` | `(updates: list[tuple[str, int]]) -> None` |

### 2. Application Layer

#### Commands
| Command | Handler | Description |
|---------|---------|-------------|
| `CreateFieldDefinitionCommand` | `CreateFieldDefinitionCommandHandler` | Validates max 20, slug uniqueness, creates entity |
| `UpdateFieldDefinitionCommand` | `UpdateFieldDefinitionCommandHandler` | Updates mutable fields (label, description, required, options, visible_to_employees) |
| `DeleteFieldDefinitionCommand` | `DeleteFieldDefinitionCommandHandler` | Hard delete |
| `DeactivateFieldDefinitionCommand` | `DeactivateFieldDefinitionCommandHandler` | Set is_active=false |
| `ActivateFieldDefinitionCommand` | `ActivateFieldDefinitionCommandHandler` | Set is_active=true |
| `ReorderFieldDefinitionsCommand` | `ReorderFieldDefinitionsCommandHandler` | Bulk update sort_order |

#### Queries
| Query | Handler | Return Type |
|-------|---------|-------------|
| `ListFieldDefinitionsQuery` | `ListFieldDefinitionsQueryHandler` | `list[FieldDefinitionDto]` |
| `GetFieldDefinitionQuery` | `GetFieldDefinitionQueryHandler` | `FieldDefinitionDto` |

#### DTOs
```python
@dataclass
class FieldDefinitionDto:
    id: str
    company_id: str
    entity_type: str
    field_key: str
    label: str
    description: Optional[str]
    field_type: str
    options: Optional[list[str]]
    required: bool
    sort_order: int
    is_active: bool
    visible_to_employees: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

### 3. Infrastructure Layer

#### Model
```python
class CustomFieldDefinitionModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "custom_field_definitions"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    field_key: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    field_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options: Mapped[Any] = mapped_column(JSON, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    visible_to_employees: Mapped[bool] = mapped_column(Boolean, server_default="true")

    __table_args__ = (
        Index("ix_cfd_company_entity", "company_id", "entity_type"),
        UniqueConstraint("company_id", "entity_type", "field_key", name="uq_cfd_company_entity_key"),
    )
```

#### Migration
| Migration | Description |
|-----------|-------------|
| `create_custom_field_definitions` | Create `custom_field_definitions` table with indexes and unique constraint |

### 4. HTTP Layer

#### Endpoints
| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/custom-fields/definitions` | List by entity_type | Enterprise admin |
| GET | `/api/v1/custom-fields/definitions/{id}` | Get single | Enterprise admin |
| POST | `/api/v1/custom-fields/definitions` | Create | Enterprise admin |
| PUT | `/api/v1/custom-fields/definitions/{id}` | Update | Enterprise admin |
| DELETE | `/api/v1/custom-fields/definitions/{id}` | Hard delete | Enterprise admin |
| POST | `/api/v1/custom-fields/definitions/{id}/deactivate` | Deactivate | Enterprise admin |
| POST | `/api/v1/custom-fields/definitions/{id}/activate` | Activate | Enterprise admin |
| PUT | `/api/v1/custom-fields/definitions/reorder` | Bulk reorder | Enterprise admin |

#### Schemas
```python
class CreateFieldDefinitionRequest(BaseModel):
    entity_type: str = Field(pattern=r"^(asset|request|incident)$")
    label: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    field_type: str = Field(pattern=r"^(text|number|date|select|multi_select|boolean)$")
    options: Optional[list[str]] = None
    required: bool = False
    visible_to_employees: bool = True

class UpdateFieldDefinitionRequest(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    options: Optional[list[str]] = None
    required: Optional[bool] = None
    visible_to_employees: Optional[bool] = None

class ReorderRequest(BaseModel):
    field_ids: list[str]  # ordered list — position = sort_order

class FieldDefinitionResponse(BaseModel):
    id: str
    entity_type: str
    field_key: str
    label: str
    description: Optional[str]
    field_type: str
    options: Optional[list[str]]
    required: bool
    sort_order: int
    is_active: bool
    visible_to_employees: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

### 5. Frontend

#### Admin Page: `web/app/src/pages/admin/CustomFieldsPage.tsx`
- Tabs: Assets | Requests | Incidents
- Each tab: table of definitions (label, type, required, status, sort order)
- Actions: Create (modal), Edit (modal), Deactivate/Activate, Delete (confirm dialog)
- Reorder: up/down arrow buttons per row
- Plan gate: page only accessible with Enterprise plan

#### Sidebar & Router
- `Sidebar.tsx`: Add "Custom Fields" under Settings subgroup, admin role
- `router.tsx`: Add `/custom-fields` route → `CustomFieldsPage`

#### i18n Keys (~25)
`page.custom_fields.title`, `page.custom_fields.subtitle`, `page.custom_fields.tab_assets`, `page.custom_fields.tab_requests`, `page.custom_fields.tab_incidents`, `page.custom_fields.add_field`, `page.custom_fields.edit_field`, `page.custom_fields.field_label`, `page.custom_fields.field_type`, `page.custom_fields.field_key`, `page.custom_fields.description`, `page.custom_fields.required`, `page.custom_fields.visible_to_employees`, `page.custom_fields.options`, `page.custom_fields.add_option`, `page.custom_fields.active`, `page.custom_fields.inactive`, `page.custom_fields.deactivate`, `page.custom_fields.activate`, `page.custom_fields.delete_confirm`, `page.custom_fields.delete_warning`, `page.custom_fields.max_fields_warning`, `page.custom_fields.duplicate_key_error`, `page.custom_fields.no_fields`, `page.custom_fields.type_text`, `page.custom_fields.type_number`, `page.custom_fields.type_date`, `page.custom_fields.type_select`, `page.custom_fields.type_multi_select`, `page.custom_fields.type_boolean`

### 6. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `app.py` | Add import + include_router | Register custom_fields router |
| `tests/conftest.py` | Add import | Import `CustomFieldDefinitionModel` |
| `web/app/src/router.tsx` | Add route | `/custom-fields` |
| `web/app/src/components/layout/Sidebar.tsx` | Add nav item | Under Settings |
| `web/app/src/locales/en.ts` | Add keys | ~25 keys |
| `web/app/src/locales/es.ts` | Add keys | ~25 keys |
| `web/app/src/types/index.ts` | Add interface | `CustomFieldDefinition` |

## Database Schema

```sql
CREATE TABLE custom_field_definitions (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    entity_type VARCHAR(20) NOT NULL,
    field_key VARCHAR(50) NOT NULL,
    label VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    field_type VARCHAR(20) NOT NULL,
    options JSON,
    required BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    visible_to_employees BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_cfd_company_entity ON custom_field_definitions(company_id, entity_type);
CREATE UNIQUE INDEX uq_cfd_company_entity_key ON custom_field_definitions(company_id, entity_type, field_key);
```

## State Machine

```
[Created] → Active ⇄ Inactive → [Deleted]
                Active → [Deleted]
```

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | `CustomFieldDefinition.create()` — slug, options validation, max fields | High |
| Unit | `_slugify()` — edge cases (unicode, special chars, max length) | High |
| Unit | All 6 command handlers | High |
| Unit | Both query handlers | High |
| Integration | POST/GET/PUT/DELETE endpoints | High |
| Integration | Plan gating (402 for non-Enterprise) | High |
| Integration | Slug collision (409) | Medium |
| Integration | Max 20 fields (422) | Medium |
| Integration | Deactivate/activate cycle | Medium |
| Integration | Reorder | Medium |

## Implementation Order

1. [ ] Domain: enums (`EntityType`, `FieldType`)
2. [ ] Domain: exceptions
3. [ ] Domain: entity (`CustomFieldDefinition`)
4. [ ] Domain: repository interface
5. [ ] Infrastructure: model + migration
6. [ ] Infrastructure: repository implementation
7. [ ] Application: DTOs
8. [ ] Application: commands (create, update, delete, deactivate, activate, reorder)
9. [ ] Application: queries (list, get)
10. [ ] HTTP: schemas, dependencies, router
11. [ ] Collateral: `app.py`, `tests/conftest.py`
12. [ ] Unit tests
13. [ ] Integration tests
14. [ ] Frontend: CustomFieldsPage + sidebar + router + i18n
15. [ ] `make lint` + `npx tsc --noEmit`
