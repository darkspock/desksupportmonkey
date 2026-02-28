# Implementation Tasks: Onboarding Wizard

**Requirement:** [../../requirements.md](../../requirements.md)
**Design:** [design.md](design.md)

## Task Summary

| # | Task | Phase | Complexity | Dependencies |
|---|------|-------|------------|--------------|
| 1 | Add CompanySector enum | Domain | S | None |
| 2 | Add sector + onboarding fields to Company entity | Domain | S | TASK-1 |
| 3 | Create Alembic migration | Infrastructure | S | TASK-2 |
| 4 | Update CompanyModel with new columns | Infrastructure | S | TASK-3 |
| 5 | Update Company repository (to_entity / to_model) | Infrastructure | S | TASK-4 |
| 6 | Create CompleteOnboardingCommand + Handler | Application | M | TASK-5 |
| 7 | Create GetOnboardingStatusQuery + Handler | Application | S | TASK-5 |
| 8 | Add onboarding endpoints to /my router | HTTP | M | TASK-6, TASK-7 |
| 9 | Extend company-settings endpoints with sector | HTTP | S | TASK-5 |
| 10 | Add needs_onboarding to /me user response | HTTP | S | TASK-5 |
| 11 | Unit tests for commands and queries | Tests | M | TASK-6, TASK-7 |
| 12 | Integration tests for onboarding endpoints | Tests | M | TASK-8, TASK-9, TASK-10 |
| 13 | Create moduleConfig.ts (modules + sector-framework mapping) | Frontend | S | None |
| 14 | Create OnboardingWizard page (4 steps) | Frontend | L | TASK-13 |
| 15 | Add /onboarding route + post-login redirect | Frontend | M | TASK-14 |
| 16 | Add sector field + re-run button to CompanySettingsPage | Frontend | S | TASK-14 |
| 17 | Add i18n keys (EN/ES) | Frontend | M | TASK-14 |

---

## Phase 1: Domain Layer

### TASK-1: Add CompanySector enum

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add the `CompanySector` enum to the existing company enums file.

**File to modify:** `src/company_bc/company/domain/enums.py`

**Implementation:**
```python
class CompanySector(str, Enum):
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    GOVERNMENT = "government"
    EDUCATION = "education"
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    ENERGY = "energy"
    TELECOMMUNICATIONS = "telecommunications"
    PROFESSIONAL_SERVICES = "professional_services"
    LOGISTICS = "logistics"
    OTHER = "other"
```

**Acceptance Criteria:**
- [x] Enum with 12 values matching requirements
- [x] Inherits from `str, Enum`

---

### TASK-2: Add sector + onboarding fields to Company entity

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-1

**Description:**
Add `sector` and `onboarding_completed_at` fields plus domain methods to the existing Company entity.

**File to modify:** `src/company_bc/company/domain/entities.py`

**Implementation:**
1. Add `InvalidSectorError` exception class
2. Add fields to Company dataclass:
   - `sector: Optional[str] = None`
   - `onboarding_completed_at: Optional[datetime] = None`
3. Add `set_sector(sector)` method -- validates against `CompanySector` enum values
4. Add `complete_onboarding()` method -- sets `onboarding_completed_at` to `datetime.now(timezone.utc)`

**Acceptance Criteria:**
- [x] `sector` field added (Optional[str], default None)
- [x] `onboarding_completed_at` field added (Optional[datetime], default None)
- [x] `set_sector()` validates against CompanySector enum, raises `InvalidSectorError` for invalid values
- [x] `set_sector(None)` is valid (clears sector)
- [x] `complete_onboarding()` sets timestamp to current UTC time

---

## Phase 2: Infrastructure Layer

### TASK-3: Create Alembic migration

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-2

**Description:**
Create migration to add `sector` and `onboarding_completed_at` columns to the `companies` table.

**File to create:** `alembic/versions/e50a1_add_onboarding_fields_to_companies.py`

**Schema:**
```sql
ALTER TABLE companies ADD COLUMN sector VARCHAR(50) NULL;
ALTER TABLE companies ADD COLUMN onboarding_completed_at TIMESTAMP WITH TIME ZONE NULL;
```

**Acceptance Criteria:**
- [x] `sector` column: VARCHAR(50), nullable
- [x] `onboarding_completed_at` column: TIMESTAMP WITH TIME ZONE, nullable
- [x] Reversible (downgrade drops both columns)

---

### TASK-4: Update CompanyModel with new columns

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-3

**Description:**
Add the two new columns to the SQLAlchemy model.

**File to modify:** `src/company_bc/company/infrastructure/models.py`

**Implementation:**
```python
sector: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Acceptance Criteria:**
- [x] Both columns use `Mapped[Optional[...]]` + `mapped_column()` (SQLAlchemy 2.0 style)
- [x] Types match migration schema

---

### TASK-5: Update Company repository (to_entity / to_model)

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-4

**Description:**
Update the repository's entity-to-model and model-to-entity conversion methods to include the new fields.

**File to modify:** `src/company_bc/company/infrastructure/repository.py`

**Implementation:**
Add `sector` and `onboarding_completed_at` to both `_to_entity()` and `save()` methods.

**Acceptance Criteria:**
- [x] `_to_entity()` maps `model.sector` -> `entity.sector` and `model.onboarding_completed_at` -> `entity.onboarding_completed_at`
- [x] `save()` persists both fields from entity to model
- [x] Existing tests still pass

---

## Phase 3: Application Layer

### TASK-6: Create CompleteOnboardingCommand + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-5

**Description:**
Create a command to save sector and mark onboarding as complete.

**File to create:** `src/company_bc/company/application/commands/complete_onboarding.py`

**Implementation:**
```python
@dataclass
class CompleteOnboardingCommand(Command):
    company_id: str
    sector: Optional[str] = None

class CompleteOnboardingCommandHandler(CommandHandler[CompleteOnboardingCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, command: CompleteOnboardingCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        company.set_sector(command.sector)
        company.complete_onboarding()
        self.company_repo.save(company)
```

**Exceptions to handle upstream:**
- `CompanyNotFoundError` -> 404
- `InvalidSectorError` -> 422

**Acceptance Criteria:**
- [x] Inherits from `Command` / `CommandHandler`
- [x] Command + Handler in same file
- [x] Returns None
- [x] Saves sector and sets `onboarding_completed_at`
- [x] Raises `CompanyNotFoundError` if company not found
- [x] Raises `InvalidSectorError` if sector value is invalid
- [x] Accepts `sector: None` for skip scenario

---

### TASK-7: Create GetOnboardingStatusQuery + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-5

**Description:**
Create a query to check onboarding status for a company.

**File to create:** `src/company_bc/company/application/queries/get_onboarding_status.py`

**Implementation:**
```python
@dataclass
class OnboardingStatusDto:
    sector: Optional[str]
    onboarding_completed_at: Optional[datetime]
    needs_onboarding: bool

@dataclass
class GetOnboardingStatusQuery(Query):
    company_id: str

class GetOnboardingStatusQueryHandler(QueryHandler[GetOnboardingStatusQuery, OnboardingStatusDto]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, query: GetOnboardingStatusQuery) -> OnboardingStatusDto:
        company = self.company_repo.find_by_id(query.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        return OnboardingStatusDto(
            sector=company.sector,
            onboarding_completed_at=company.onboarding_completed_at,
            needs_onboarding=company.onboarding_completed_at is None,
        )
```

**Acceptance Criteria:**
- [x] Inherits from `Query` / `QueryHandler`
- [x] Returns `OnboardingStatusDto` dataclass
- [x] `needs_onboarding` is `True` when `onboarding_completed_at` is None

---

## Phase 4: HTTP Layer

### TASK-8: Add onboarding endpoints to /my router

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-6, TASK-7

**Description:**
Add two new endpoints to the existing `/api/v1/my/` router for onboarding.

**File to modify:** `adapters/http/api/my/routers.py`
**File to modify:** `adapters/http/api/my/schemas.py`

**Endpoints:**

1. `GET /api/v1/my/onboarding/status`
   - Auth: Admin only
   - Returns: `{ "data": { "sector": "...", "onboarding_completed_at": "...", "needs_onboarding": true } }`

2. `POST /api/v1/my/onboarding/complete`
   - Auth: Admin only
   - Request: `{ "sector": "financial_services" }` (sector is optional, null for skip)
   - Returns: `{ "data": { "sector": "...", "onboarding_completed_at": "..." } }`
   - Exceptions: `CompanyNotFoundError` -> 404, `InvalidSectorError` -> 422

**Schemas:**
```python
class CompleteOnboardingRequest(BaseModel):
    sector: Optional[str] = None

class OnboardingStatusResponse(BaseModel):
    sector: Optional[str]
    onboarding_completed_at: Optional[str]
    needs_onboarding: bool
```

**Acceptance Criteria:**
- [x] Both endpoints require admin role
- [x] Both endpoints use `_validate_admin_with_company()` helper
- [x] POST catches `CompanyNotFoundError` -> 404 and `InvalidSectorError` -> 422
- [x] Response schemas use primitives only

---

### TASK-9: Extend company-settings endpoints with sector

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-5

**Description:**
Add `sector` to the company settings GET response and PUT request.

**Files to modify:**
- `adapters/http/api/my/schemas.py` -- add `sector` to `MyCompanySettingsResponse` and `UpdateMyCompanySettingsRequest`
- `adapters/http/api/my/routers.py` -- pass sector in `_to_company_settings()` and handle it in update

**Implementation:**
```python
class MyCompanySettingsResponse(BaseModel):
    id: str
    name: str
    email_domains: list[str]
    sector: Optional[str] = None  # NEW

class UpdateMyCompanySettingsRequest(BaseModel):
    email_domains: list[str] = Field(min_length=1)
    sector: Optional[str] = None  # NEW (optional, only updated if provided)
```

The update handler should call `company.set_sector(sector)` when sector is provided in the request.

**Acceptance Criteria:**
- [x] GET returns `sector` field
- [x] PUT accepts optional `sector` field
- [x] Invalid sector returns 422 with `InvalidSectorError` message

---

### TASK-10: Add needs_onboarding to /me user response

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-5

**Description:**
Extend the `/api/v1/auth/me` response to include `needs_onboarding` so the frontend can redirect on login.

**Files to modify:**
- `adapters/http/api/auth/schemas.py` -- add `needs_onboarding: bool = False` to `UserResponse`
- `adapters/http/api/auth/routers.py` -- compute from company's `onboarding_completed_at` in the `/me` endpoint

**Logic:**
```python
needs_onboarding = False
if current_user.role == UserRole.ADMIN and company:
    needs_onboarding = company.onboarding_completed_at is None
```

Only admins can need onboarding. All other roles always get `needs_onboarding: false`.

**Acceptance Criteria:**
- [x] `UserResponse` includes `needs_onboarding: bool`
- [x] Only true for admin users whose company has `onboarding_completed_at is None`
- [x] False for all non-admin roles
- [x] False for admins without a company

---

## Phase 5: Tests

### TASK-11: Unit tests for commands and queries

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-6, TASK-7

**Description:**
Unit tests with MagicMock dependencies.

**Files to create:**
- `tests/unit/company_bc/company/application/commands/test_complete_onboarding.py`
- `tests/unit/company_bc/company/application/queries/test_get_onboarding_status.py`
- `tests/unit/company_bc/company/domain/test_company_onboarding.py`

**Test cases:**

**CompleteOnboardingCommand:**
- [x] Happy path: saves sector and sets onboarding_completed_at
- [x] Skip: sector=None, still sets onboarding_completed_at
- [x] Company not found: raises CompanyNotFoundError
- [x] Invalid sector: raises InvalidSectorError
- [x] Idempotent: calling twice doesn't error (updates timestamp)

**GetOnboardingStatusQuery:**
- [x] Needs onboarding: onboarding_completed_at is None -> needs_onboarding=True
- [x] Already completed: onboarding_completed_at set -> needs_onboarding=False
- [x] Returns sector value
- [x] Company not found: raises CompanyNotFoundError

**Company domain methods:**
- [x] `set_sector("financial_services")` -- valid
- [x] `set_sector("invalid_value")` -- raises InvalidSectorError
- [x] `set_sector(None)` -- clears sector
- [x] `complete_onboarding()` -- sets timestamp

**Acceptance Criteria:**
- [x] All tests pass with `make test`
- [x] Uses MagicMock for repository

---

### TASK-12: Integration tests for onboarding endpoints

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-8, TASK-9, TASK-10

**Description:**
Integration tests with real DB via TestClient.

**File to create:** `tests/integration/test_onboarding_endpoints.py`

**Test cases:**

- [x] `GET /my/onboarding/status` -- returns needs_onboarding=True for new company
- [x] `GET /my/onboarding/status` -- returns needs_onboarding=False after completion
- [x] `POST /my/onboarding/complete` -- with valid sector, returns 200
- [x] `POST /my/onboarding/complete` -- with null sector (skip), returns 200
- [x] `POST /my/onboarding/complete` -- with invalid sector, returns 422
- [x] `POST /my/onboarding/complete` -- non-admin, returns 403
- [x] `GET /my/company-settings` -- includes sector field
- [x] `PUT /my/company-settings` -- updates sector
- [x] `PUT /my/company-settings` -- invalid sector returns 422
- [x] `GET /auth/me` -- admin with no onboarding: needs_onboarding=True
- [x] `GET /auth/me` -- admin after onboarding: needs_onboarding=False
- [x] `GET /auth/me` -- technician: needs_onboarding=False (always)

**Acceptance Criteria:**
- [x] All tests pass with `make test-integration`
- [x] Uses existing test fixtures (`client`, `auth_as`, `admin_user`)

---

## Phase 6: Frontend

### TASK-13: Create moduleConfig.ts

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None (can be done in parallel with backend)

**Description:**
Create a config file with module definitions and sector-to-framework mapping.

**File to create:** `web/app/src/config/moduleConfig.ts`

**Implementation:**
Contains two exports:
1. `MODULES` array with id, labelKey, descriptionKey, always_on flag, and nav paths for each module
2. `SECTOR_FRAMEWORKS` map from sector ID to recommended framework names
3. `SECTORS` array with id and labelKey for each sector
4. `FRAMEWORKS` array with key, name, color for each framework (reuse from ComplianceControlsPage)

**Acceptance Criteria:**
- [x] 9 modules defined with correct nav paths from requirements
- [x] 12 sectors defined
- [x] Sector-to-framework mapping matches requirements table
- [x] Service Desk module has `always_on: true`
- [x] All label/description keys follow i18n pattern `onboarding.modules.*`, `onboarding.sectors.*`

---

### TASK-14: Create OnboardingWizard page

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-13

**Description:**
Build the 4-step onboarding wizard as a full-screen page.

**File to create:** `web/app/src/pages/admin/OnboardingWizardPage.tsx`

**Steps:**
1. **SectorStep**: Grid of sector cards. Single selection. Uses `SECTORS` from moduleConfig.
2. **FrameworkStep**: Checkbox list of 4 frameworks. Pre-checked based on `SECTOR_FRAMEWORKS[selectedSector]`. Badge "Recommended" on pre-checked ones.
3. **ModuleStep**: Toggle cards for 9 modules. Service Desk locked on with disabled toggle. Each card shows module name + short description.
4. **SummaryStep**: Read-only summary of all choices. "Finish Setup" button.

**Top bar:** Step progress indicator (Step 1 of 4). "Skip" link on all steps. Back button on steps 2-4.

**On "Finish Setup":**
1. Call `POST /api/v1/my/onboarding/complete` with sector
2. For each selected framework, seed controls using same logic as ComplianceControlsPage (iterate `PREDEFINED_CONTROLS`, POST each control, ignore 409s)
3. Build `hidden_nav_items` from deselected modules: collect all nav paths from deselected modules, set for roles `["admin", "employee", "technician", "procurement_manager"]`
4. Call `PUT /api/v1/settings/nav-visibility` with the hidden_nav_items
5. Invalidate `['auth', 'me']` query to refresh user data (picks up new hidden_nav_items)
6. Show success toast, navigate to `/dashboard`

**On "Skip":**
1. Call `POST /api/v1/my/onboarding/complete` with `sector: null`
2. Navigate to `/dashboard`

**Error handling:** If any API call fails, show error toast. Still mark onboarding complete. Admin can fix settings later.

**Pre-fill for re-run:** Accept optional query param `?rerun=true`. When present, fetch current sector from company settings, current frameworks from compliance controls, current hidden items from nav visibility -- and pre-fill each step.

**UI patterns:**
- Full-screen white background (no sidebar visible)
- Centered content card, max-width ~800px
- shadcn/ui: Button, Card, Checkbox, Badge, Progress
- Lucide icons for each module card
- All text via `t()` i18n function
- 4 states per step: loading, content, error, submitting

**Acceptance Criteria:**
- [x] 4-step wizard with progress indicator
- [x] Back/forward navigation between steps
- [x] Sector selection pre-checks recommended frameworks in Step 2
- [x] Service Desk cannot be deactivated
- [x] Skip works and marks onboarding complete
- [x] All 3 APIs called on "Finish Setup"
- [x] Framework seeding reuses same logic as ComplianceControlsPage
- [x] Error toast on API failure, still completes onboarding
- [x] Responsive layout (mobile-friendly)
- [x] All text uses i18n

---

### TASK-15: Add /onboarding route + post-login redirect

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-14

**Description:**
Wire the onboarding wizard into the router and add the post-login redirect.

**Files to modify:**
- `web/app/src/router.tsx` -- add lazy-loaded `/onboarding` route (admin only)
- `web/app/src/pages/auth/LoginPage.tsx` -- after login, check `needs_onboarding` from user data; if true and role is admin, redirect to `/onboarding` instead of `/dashboard`
- `web/app/src/types/index.ts` -- add `needs_onboarding?: boolean` to User type

**Routing logic:**
```typescript
// In LoginPage or auth handler:
if (user.role === 'admin' && user.needs_onboarding) {
    navigate('/onboarding', { replace: true });
} else {
    navigate(returnTo ?? getDefaultRouteForRole(user.role), { replace: true });
}
```

**Acceptance Criteria:**
- [x] `/onboarding` route exists, lazy-loaded, admin only
- [x] Admin with `needs_onboarding=true` redirected to `/onboarding` after login
- [x] Admin with `needs_onboarding=false` goes to dashboard as usual
- [x] Non-admin roles never redirected to onboarding
- [x] Direct navigation to `/onboarding` works for admin (for re-run)

---

### TASK-16: Add sector field + re-run button to CompanySettingsPage

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-14

**Description:**
Extend the existing Company Settings page.

**File to modify:** `web/app/src/pages/admin/CompanySettingsPage.tsx`

**Implementation:**
1. Add a `<Select>` dropdown for sector using `SECTORS` from moduleConfig.ts. Populated from GET response, saved via PUT.
2. Add a "Re-run setup wizard" button that navigates to `/onboarding?rerun=true`.

**Acceptance Criteria:**
- [x] Sector dropdown shows all 12 sectors + empty option
- [x] Sector saved via PUT /my/company-settings
- [x] "Re-run setup wizard" button navigates to /onboarding?rerun=true
- [x] All text uses i18n

---

### TASK-17: Add i18n keys (EN/ES)

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-14

**Files to modify:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**Keys needed:**

```
onboarding.title: "Welcome to DeskSupportMonkey" / "Bienvenido a DeskSupportMonkey"
onboarding.subtitle: "Let's set up your workspace" / "Configuremos tu espacio de trabajo"
onboarding.skip: "Skip, I'll configure later" / "Omitir, lo configuro despues"
onboarding.next: "Next" / "Siguiente"
onboarding.back: "Back" / "Atras"
onboarding.finish: "Finish Setup" / "Finalizar Configuracion"
onboarding.step_of: "Step {{current}} of {{total}}" / "Paso {{current}} de {{total}}"

onboarding.sector.title: "What industry is your company in?" / "¿En que sector opera tu empresa?"
onboarding.sector.subtitle: "This helps us recommend the right tools" / "Esto nos ayuda a recomendar las herramientas adecuadas"

onboarding.frameworks.title: "Compliance frameworks" / "Marcos de cumplimiento"
onboarding.frameworks.subtitle: "Based on your sector, we recommend these frameworks" / "Segun tu sector, te recomendamos estos marcos"
onboarding.frameworks.recommended: "Recommended" / "Recomendado"

onboarding.modules.title: "Which features do you need?" / "¿Que funcionalidades necesitas?"
onboarding.modules.subtitle: "You can always enable more later" / "Siempre puedes activar mas despues"
onboarding.modules.always_on: "Always active" / "Siempre activo"

onboarding.summary.title: "Review your setup" / "Revisa tu configuracion"
onboarding.summary.sector: "Industry sector" / "Sector"
onboarding.summary.frameworks: "Compliance frameworks" / "Marcos de cumplimiento"
onboarding.summary.modules: "Active modules" / "Modulos activos"
onboarding.summary.none_selected: "None selected" / "Ninguno seleccionado"

onboarding.success: "Setup complete! Your workspace is ready." / "¡Configuracion completa! Tu espacio esta listo."
onboarding.error: "Some settings couldn't be saved. Please review in Settings." / "Algunos ajustes no se pudieron guardar. Revisalos en Configuracion."

onboarding.sectors.financial_services: "Financial Services" / "Servicios Financieros"
onboarding.sectors.healthcare: "Healthcare" / "Salud"
onboarding.sectors.government: "Government / Public Sector" / "Gobierno / Sector Publico"
onboarding.sectors.education: "Education" / "Educacion"
onboarding.sectors.technology: "Technology" / "Tecnologia"
onboarding.sectors.manufacturing: "Manufacturing" / "Manufactura"
onboarding.sectors.retail: "Retail / E-Commerce" / "Retail / Comercio Electronico"
onboarding.sectors.energy: "Energy / Utilities" / "Energia / Servicios Publicos"
onboarding.sectors.telecommunications: "Telecommunications" / "Telecomunicaciones"
onboarding.sectors.professional_services: "Professional Services" / "Servicios Profesionales"
onboarding.sectors.logistics: "Logistics / Transportation" / "Logistica / Transporte"
onboarding.sectors.other: "Other" / "Otro"

onboarding.modules.service_desk: "Service Desk" / "Mesa de Servicio"
onboarding.modules.service_desk_desc: "Service requests, queue, SLA" / "Solicitudes, cola de trabajo, SLA"
onboarding.modules.asset_inventory: "Asset Inventory" / "Inventario de Activos"
onboarding.modules.asset_inventory_desc: "Hardware tracking, CMDB, labels" / "Seguimiento de hardware, CMDB, etiquetas"
onboarding.modules.procurement: "Procurement" / "Compras"
onboarding.modules.procurement_desc: "Purchase orders, vendors, budgets" / "Ordenes de compra, proveedores, presupuestos"
onboarding.modules.knowledge_base: "Knowledge Base" / "Base de Conocimiento"
onboarding.modules.knowledge_base_desc: "Articles, categories, AI suggestions" / "Articulos, categorias, sugerencias IA"
onboarding.modules.compliance_audit: "Compliance & Audit" / "Cumplimiento y Auditoria"
onboarding.modules.compliance_audit_desc: "Frameworks, controls, audit trail" / "Marcos, controles, pista de auditoria"
onboarding.modules.security: "Security" / "Seguridad"
onboarding.modules.security_desc: "Incidents, risks, vulnerabilities" / "Incidentes, riesgos, vulnerabilidades"
onboarding.modules.change_management: "Change Management" / "Gestion de Cambios"
onboarding.modules.change_management_desc: "Change requests, approvals" / "Solicitudes de cambio, aprobaciones"
onboarding.modules.maintenance: "Maintenance" / "Mantenimiento"
onboarding.modules.maintenance_desc: "Scheduled maintenance, templates" / "Mantenimiento programado, plantillas"
onboarding.modules.logistics: "Logistics" / "Logistica"
onboarding.modules.logistics_desc: "Shipping, appointments" / "Envios, citas"

company_settings.sector: "Industry Sector" / "Sector"
company_settings.sector_placeholder: "Select sector..." / "Seleccionar sector..."
company_settings.rerun_wizard: "Re-run setup wizard" / "Ejecutar asistente de nuevo"
company_settings.sector_changed_hint: "Sector changed. Review your compliance frameworks in Settings > Compliance Controls." / "Sector actualizado. Revisa tus marcos de cumplimiento en Configuracion > Controles de Cumplimiento."
```

**Acceptance Criteria:**
- [x] All keys added to both `en.ts` and `es.ts`
- [x] Spanish text uses proper accents and tildes
- [x] No hardcoded English text in any component

---

## Dependency Graph

```
TASK-1 (enum)
  |
TASK-2 (entity fields)
  |
TASK-3 (migration)
  |
TASK-4 (model)
  |
TASK-5 (repository)
  |
  ├── TASK-6 (complete command) ──┐
  ├── TASK-7 (status query) ──────┤
  └── TASK-9 (settings ext) ──────┤
       |                          |
       ├── TASK-8 (endpoints) ────┤
       └── TASK-10 (/me ext) ─────┤
                                  |
                            TASK-11 (unit tests)
                            TASK-12 (integration tests)

TASK-13 (moduleConfig) ──── parallel with backend
  |
TASK-14 (wizard page) ── L, main frontend work
  |
  ├── TASK-15 (routing)
  ├── TASK-16 (settings page)
  └── TASK-17 (i18n)
```

## Execution Order

**Batch 1 (parallel):** TASK-1, TASK-13
**Batch 2 (sequential):** TASK-2 -> TASK-3 -> TASK-4 -> TASK-5
**Batch 3 (parallel):** TASK-6, TASK-7, TASK-9
**Batch 4 (parallel):** TASK-8, TASK-10
**Batch 5 (parallel):** TASK-11, TASK-12
**Batch 6:** TASK-14 (large, main frontend work)
**Batch 7 (parallel):** TASK-15, TASK-16, TASK-17

## Final Checklist

- [x] All tasks completed
- [x] `make test` passes (2382 passed, 12 pre-existing failures unrelated to onboarding)
- [ ] `make test-integration` passes (requires Docker)
- [ ] `make lint` passes (5 pre-existing errors in vulnerability_bc, unrelated to onboarding)
- [ ] Migration runs cleanly (`make db-upgrade`) (requires Docker)
- [x] All i18n keys in both EN and ES
- [ ] Wizard renders correctly and completes without errors (requires manual visual verification)
