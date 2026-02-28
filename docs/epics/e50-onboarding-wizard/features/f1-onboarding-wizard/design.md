# Design: Onboarding Wizard

**Requirement:** [../../requirements.md](../../requirements.md)

## Overview

A 3-step onboarding wizard that appears on first admin login. It saves sector to the Company entity, enables compliance frameworks via the existing controls API, and configures module visibility via the existing nav visibility API. Minimal backend changes (2 new fields + 1 new command + 1 new query). The wizard is primarily a frontend orchestrator.

## Domain Model

### Company Entity (modified)

Two new fields on the existing `Company` dataclass:

```python
@dataclass
class Company:
    # ... existing fields ...
    sector: Optional[str] = None
    onboarding_completed_at: Optional[datetime] = None

    def set_sector(self, sector: Optional[str]) -> None:
        if sector is not None and sector not in VALID_SECTORS:
            raise InvalidSectorError(sector)
        self.sector = sector

    def complete_onboarding(self) -> None:
        self.onboarding_completed_at = datetime.now(timezone.utc)
```

### CompanySector Enum (new)

```python
# In src/company_bc/company/domain/enums.py
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

### InvalidSectorError (new)

```python
# In src/company_bc/company/domain/entities.py
class InvalidSectorError(Exception):
    pass
```

## Commands & Queries

### CompleteOnboardingCommand (new)

```python
# src/company_bc/company/application/commands/complete_onboarding.py
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

### GetOnboardingStatusQuery (new)

```python
# src/company_bc/company/application/queries/get_onboarding_status.py
@dataclass
class GetOnboardingStatusQuery(Query):
    company_id: str

@dataclass
class OnboardingStatusDto:
    sector: Optional[str]
    onboarding_completed_at: Optional[datetime]
    needs_onboarding: bool

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

## HTTP Endpoints

### POST /api/v1/my/onboarding/complete

Saves sector and marks onboarding as complete. Called when wizard finishes or is skipped.

```
Request: { "sector": "financial_services" | null }
Response: { "data": { "sector": "financial_services", "onboarding_completed_at": "2026-02-28T..." } }
Auth: Admin only
Exceptions: CompanyNotFoundError -> 404, InvalidSectorError -> 422
```

### GET /api/v1/my/onboarding/status

Returns onboarding status for the current user's company.

```
Response: { "data": { "sector": "financial_services" | null, "onboarding_completed_at": "..." | null, "needs_onboarding": true } }
Auth: Admin only
```

### Existing Endpoints (no changes)

- `PUT /api/v1/settings/nav-visibility` -- Called by wizard Step 3 to hide module nav paths
- `POST /api/v1/audit/controls` -- Called by wizard Step 2 to seed framework controls (same logic as ComplianceControlsPage.tsx)
- `GET /api/v1/my/company-settings` -- Extended to return `sector` field
- `PUT /api/v1/my/company-settings` -- Extended to accept optional `sector` field

## Database Schema

### Migration: Add sector and onboarding_completed_at to companies

```sql
ALTER TABLE companies ADD COLUMN sector VARCHAR(50) NULL;
ALTER TABLE companies ADD COLUMN onboarding_completed_at TIMESTAMP WITH TIME ZONE NULL;
```

No indexes needed (these are not queried by value in any hot path).

## Frontend Components

### OnboardingWizard (new page component)

Route: `/onboarding` (admin only, lazy-loaded)

Full-screen modal overlay with 3 steps + summary:

```
Step 1: SectorStep       -- Grid of sector cards, single selection
Step 2: FrameworkStep     -- Checkboxes for 4 frameworks, pre-checked based on sector mapping
Step 3: ModuleStep        -- Toggle cards for 9 modules, Service Desk locked on
Step 4: SummaryStep       -- Review choices, "Finish Setup" button
```

**State management:** Local React state in the wizard (no global state needed). On "Finish Setup", the wizard calls 3 APIs in sequence:

1. `POST /api/v1/my/onboarding/complete` with sector
2. `POST /api/v1/audit/controls` for each selected framework's predefined controls (reuse seeding logic from ComplianceControlsPage)
3. `PUT /api/v1/settings/nav-visibility` with hidden_nav_items built from deselected modules

**Skip button:** Calls only `POST /api/v1/my/onboarding/complete` with `sector: null`, then redirects to dashboard.

### Routing Integration

In `router.tsx`, add the `/onboarding` route.

In `LoginPage.tsx` or the auth context `/me` response handler: after login, if user is admin and `needs_onboarding` is true, redirect to `/onboarding`.

The `/me` endpoint already loads company data. We extend the `UserResponse` schema to include `needs_onboarding: bool` computed from the company's `onboarding_completed_at`.

### CompanySettingsPage (modified)

Add:
1. Sector dropdown (read/write via existing company settings endpoints)
2. "Re-run setup wizard" button that navigates to `/onboarding` (wizard pre-fills current values)

### Module-to-Nav Path Mapping (frontend constant)

```typescript
// web/app/src/config/moduleConfig.ts
export const MODULES = [
  { id: 'service_desk', labelKey: 'onboarding.modules.service_desk', always_on: true, paths: ['/sla/policies', '/sla/dashboard'] },
  { id: 'asset_inventory', labelKey: 'onboarding.modules.asset_inventory', paths: ['/assets', '/cmdb/dashboard', '/settings/asset-types'] },
  { id: 'procurement', labelKey: 'onboarding.modules.procurement', paths: ['/purchase-orders', '/vendors', '/vendors/supply-chain', '/settings/procurement', '/settings/equipment-profiles'] },
  { id: 'knowledge_base', labelKey: 'onboarding.modules.knowledge_base', paths: ['/knowledge-base', '/kb', '/kb/categories'] },
  { id: 'compliance_audit', labelKey: 'onboarding.modules.compliance_audit', paths: ['/compliance/dashboard', '/settings/compliance', '/audit'] },
  { id: 'security', labelKey: 'onboarding.modules.security', paths: ['/incidents', '/incidents/dashboard', '/risks', '/risks/dashboard', '/vulnerabilities', '/vulnerabilities/dashboard'] },
  { id: 'change_management', labelKey: 'onboarding.modules.change_management', paths: ['/changes', '/changes/dashboard'] },
  { id: 'maintenance', labelKey: 'onboarding.modules.maintenance', paths: ['/maintenance', '/my/maintenance', '/maintenance-templates'] },
  { id: 'logistics', labelKey: 'onboarding.modules.logistics', paths: ['/shipments', '/my/shipments', '/my/appointments', '/my/tasks/appointments', '/calendar'] },
] as const;
```

### Sector-to-Framework Mapping (frontend constant)

```typescript
// web/app/src/config/moduleConfig.ts
export const SECTOR_FRAMEWORKS: Record<string, string[]> = {
  financial_services: ['DORA', 'NIS2', 'ISO 27001', 'GDPR'],
  healthcare: ['NIS2', 'ISO 27001', 'GDPR'],
  government: ['NIS2', 'ISO 27001', 'GDPR'],
  education: ['GDPR', 'ISO 27001'],
  technology: ['ISO 27001', 'GDPR', 'NIS2'],
  manufacturing: ['NIS2', 'ISO 27001'],
  retail: ['GDPR', 'ISO 27001'],
  energy: ['NIS2', 'DORA', 'ISO 27001'],
  telecommunications: ['NIS2', 'ISO 27001', 'GDPR'],
  professional_services: ['GDPR', 'ISO 27001'],
  logistics: ['NIS2', 'GDPR'],
  other: [],
};
```

## Testing Strategy

### Unit Tests
- `CompleteOnboardingCommandHandler`: happy path, company not found, invalid sector, idempotent (re-run)
- `GetOnboardingStatusQueryHandler`: needs onboarding (null), completed, company not found
- `Company.set_sector()`: valid sector, invalid sector, null
- `Company.complete_onboarding()`: sets timestamp

### Integration Tests
- `POST /api/v1/my/onboarding/complete`: happy path (201), skip with null sector, invalid sector (422), non-admin (403)
- `GET /api/v1/my/onboarding/status`: needs onboarding, already completed
- `GET /api/v1/my/company-settings`: returns sector field
- `PUT /api/v1/my/company-settings`: updates sector field
