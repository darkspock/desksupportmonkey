# Slicing: E11 - Department Equipment Profiles

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-17
**Total Features:** 4

## Slicing Rationale

E11 has a strict sequential dependency chain: manager ownership (F0) enables profile authorization (F1), profiles feed the matching engine (F2), and the frontend (F3) visualizes everything. Each feature is independently deployable and testable — F0/F1 are useful even without auto-assignment, and F2 works headless before the UI exists.

## Dependency Graph

```text
F0: Department Managers (domain + API)
  └── F1: Equipment Profile CRUD (domain + API)
        └── F2: Profile Matching & Auto-Assignment Engine (domain + AI)
              └── F3: Frontend UX (React pages + i18n)
```

## Features Summary

| # | Feature | Covers | Complexity | Depends | Status |
|---|---------|--------|------------|---------|--------|
| F0 | Department Managers | US-E11-001 | Medium | E1 | Done |
| F1 | Equipment Profile CRUD | US-E11-002, US-E11-005 | High | F0, E2 | Done |
| F2 | Profile Matching & Auto-Assignment Engine | US-E11-003, US-E11-004, US-E11-005 | High | F1, E2, E3 | Done |
| F3 | Frontend UX for Settings & Assignment Visibility | US-E11-001..US-E11-005 | Medium-High | F0, F1, F2, E7, E9 | Done |

---

## F0: Department Managers

**Scope:** Add `manager_user_id` to departments. Admin assigns/removes a manager. Manager info visible in department list/detail.

### Domain Changes
- Add `manager_user_id: Optional[str]` to `Department` entity
- Add `manager_user_id` column to `DepartmentModel` (FK to `users.id`, nullable, SET NULL on delete)
- Migration: `ALTER TABLE departments ADD COLUMN manager_user_id`

### Commands
- `AssignDepartmentManager(department_id, manager_user_id, performed_by)` — validates same company, user is active
- `RemoveDepartmentManager(department_id, performed_by)`

### API Endpoints
- `PUT /api/v1/departments/{id}/manager` — body: `{ user_id: str }` — Admin only
- `DELETE /api/v1/departments/{id}/manager` — Admin only

### Query Changes
- Update existing `list_departments` and `get_department` to include `manager_user_id`, `manager_email`, `manager_name`
- Update response schemas

### Tests
- Unit: same-company validation, user-active check, idempotent assign/remove
- Integration: admin happy path, forbidden for non-admin, cross-company rejection
- ~8 tests

### Files

| File | Action |
|------|--------|
| `src/company_bc/department/domain/entities.py` | Edit — add `manager_user_id` |
| `src/company_bc/department/infrastructure/repository.py` | Edit — add column, update `_to_entity`/`_to_model` |
| `alembic/versions/xxx_add_department_manager.py` | Create — migration |
| `src/company_bc/department/application/commands/assign_manager.py` | Create |
| `src/company_bc/department/application/commands/remove_manager.py` | Create |
| `src/company_bc/department/application/queries/get_department.py` | Edit — include manager |
| `src/company_bc/department/application/queries/list_departments.py` | Edit — include manager |
| `adapters/http/api/departments/routers.py` | Edit — add 2 endpoints, update schemas |
| `tests/unit/company_bc/department/application/commands/test_manager.py` | Create |
| `tests/integration/test_departments_endpoints.py` | Edit — add manager tests |

---

## F1: Equipment Profile CRUD

**Scope:** New `EquipmentProfile` + `EquipmentProfileItem` entities. CRUD with one-active-profile policy per `company+department+role`. Authorization: Admin OR department manager.

### Domain

**EquipmentProfile:**
- `id`, `company_id`, `department_id`, `role` (UserRole enum subset: employee/technician), `is_active`, `created_at`, `updated_at`
- Unique active constraint: `(company_id, department_id, role, is_active=True)`

**EquipmentProfileItem:**
- `id`, `profile_id`, `asset_type` (AssetType enum), `quantity` (default 1)
- `preferred_brand: Optional[str]`, `preferred_model: Optional[str]`
- `min_ram_gb: Optional[int]`, `min_storage_gb: Optional[int]`

### Migration
- Create `equipment_profiles` table with unique partial index on `(company_id, department_id, role) WHERE is_active = true`
- Create `equipment_profile_items` table with FK to `equipment_profiles.id` (CASCADE delete)

### Commands
- `CreateEquipmentProfile(company_id, department_id, role, items[], performed_by)`
- `UpdateEquipmentProfile(profile_id, company_id, items[], performed_by)`
- `ActivateEquipmentProfile(profile_id, company_id, performed_by)` — deactivates conflicting profile if exists
- `DeactivateEquipmentProfile(profile_id, company_id, performed_by)`
- `DeleteEquipmentProfile(profile_id, company_id, performed_by)`

### Queries
- `ListEquipmentProfiles(company_id, department_id?, role?, is_active?)` — paginated
- `GetEquipmentProfile(profile_id, company_id)` — includes items

### Authorization
- Dual check: `role >= ADMIN` OR `user.id == department.manager_user_id` for the target department
- Create shared authorization helper: `can_manage_department(user, department_id, db) -> bool`

### API Endpoints
- `POST /api/v1/equipment-profiles` — create profile with items
- `GET /api/v1/equipment-profiles` — list (filters: department_id, role, is_active)
- `GET /api/v1/equipment-profiles/{id}` — detail with items
- `PUT /api/v1/equipment-profiles/{id}` — update items
- `POST /api/v1/equipment-profiles/{id}/activate` — activate (deactivates conflicting)
- `POST /api/v1/equipment-profiles/{id}/deactivate` — deactivate
- `DELETE /api/v1/equipment-profiles/{id}` — delete

### Tests
- Unit: profile validation, one-active-profile enforcement, item constraints
- Integration: full CRUD, permission failures (employee, wrong manager), tenant isolation
- ~15 tests

### Files

| File | Action |
|------|--------|
| `src/company_bc/equipment_profile/domain/entities.py` | Create — EquipmentProfile, EquipmentProfileItem |
| `src/company_bc/equipment_profile/domain/enums.py` | Create — if needed |
| `src/company_bc/equipment_profile/infrastructure/repository.py` | Create — ORM model + repository |
| `src/company_bc/equipment_profile/application/commands/*.py` | Create — 5 commands |
| `src/company_bc/equipment_profile/application/queries/*.py` | Create — 2 queries |
| `src/company_bc/equipment_profile/application/ports.py` | Create — if needed |
| `alembic/versions/xxx_create_equipment_profiles.py` | Create — migration |
| `adapters/http/api/equipment_profiles/routers.py` | Create — 7 endpoints |
| `adapters/http/api/equipment_profiles/dependencies.py` | Create — auth helpers |
| `tests/unit/company_bc/equipment_profile/...` | Create — command/query tests |
| `tests/integration/test_equipment_profiles_endpoints.py` | Create |

---

## F2: Profile Matching & Auto-Assignment Engine

**Scope:** Matching service that finds in-stock assets by profile rules. AI tie-break via company-configured provider (OpenAI/Groq). Automatic trigger on `new_equipment`/`onboarding` request creation. Fallback reason codes.

### Domain

**CompanyAssignmentAIConfig:**
- `id`, `company_id` (unique), `provider` (enum: `OPENAI`|`GROQ`), `prompt_template` (text), `model: Optional[str]`, `created_at`, `updated_at`

**FallbackReason enum:**
- `NO_ACTIVE_PROFILE`, `NO_STOCK_FOR_REQUIRED_TYPE`, `SPEC_MISMATCH`, `ASSET_NOT_ASSIGNABLE`, `AI_UNAVAILABLE`, `MANUAL_REVIEW_REQUIRED`

### Matching Algorithm (deterministic)

```
1. Find active profile for (company, department, role)
   → NO_ACTIVE_PROFILE if none
2. For each profile item:
   a. Query in-stock assets matching asset_type in company scope
      → NO_STOCK_FOR_REQUIRED_TYPE if empty
   b. Filter by preferred_brand/preferred_model if set (soft filter — keep candidates if none match)
   c. Filter by min_ram_gb/min_storage_gb if set (hard filter — check asset.notes JSON or metadata)
      → SPEC_MISMATCH if all filtered out
   d. Filter by assignable status (IN_STOCK)
      → ASSET_NOT_ASSIGNABLE if all filtered out
   e. If 1 candidate → assign deterministically
   f. If >1 candidates → AI tie-break:
      - Load company AI config
      - Call provider with candidates + profile context
      - AI returns ranked choice
      → AI_UNAVAILABLE if provider fails (fallback: pick oldest purchase_date)
3. If any item unresolved → MANUAL_REVIEW_REQUIRED
```

### AI Provider Adapter (Port Pattern)

```python
class AITieBreakerPort(ABC):
    @abstractmethod
    def select_best_candidate(
        self, candidates: list[Asset], profile_item: EquipmentProfileItem, prompt: str
    ) -> str:  # returns asset_id
        ...

class OpenAIAdapter(AITieBreakerPort): ...
class GroqAdapter(AITieBreakerPort): ...
```

### Config
- `OPENAI_API_KEY` and `GROQ_API_KEY` in `.env`
- Add to `core/config.py`: `AISettings` with both keys

### Integration Hook
- After `CreateRequestCommand` succeeds for `new_equipment`/`onboarding`:
  - Call `AutoAssignService.attempt_assignment(request, db)`
  - Store result in `request.data['profile_assignment']` (metadata: profile_id, matched items, fallback reasons)
  - If match found: call existing `AssignAssetCommand` for each matched asset

### Commands/Queries
- `SaveCompanyAIConfig(company_id, provider, prompt_template, model?)` — Admin only
- `GetCompanyAIConfig(company_id)` — Admin only
- Service: `AutoAssignService` (not a command — orchestration service)

### API Endpoints
- `PUT /api/v1/settings/assignment-ai` — save company AI config
- `GET /api/v1/settings/assignment-ai` — get company AI config

### Tests
- Unit: matching algorithm (all 6 fallback paths), AI adapter mock, deterministic fallback
- Integration: request creation triggers auto-assignment, fallback stored in request.data
- ~20 tests

### Files

| File | Action |
|------|--------|
| `src/company_bc/assignment_config/domain/entities.py` | Create — CompanyAssignmentAIConfig |
| `src/company_bc/assignment_config/domain/enums.py` | Create — AIProvider, FallbackReason |
| `src/company_bc/assignment_config/infrastructure/repository.py` | Create |
| `src/company_bc/assignment_config/application/commands/*.py` | Create |
| `src/company_bc/assignment_config/application/queries/*.py` | Create |
| `src/company_bc/equipment_profile/application/services/matching.py` | Create — EquipmentProfileMatcher |
| `src/company_bc/equipment_profile/application/services/auto_assign.py` | Create — AutoAssignService |
| `src/company_bc/equipment_profile/application/services/ai_tiebreaker.py` | Create — port + adapters |
| `alembic/versions/xxx_create_assignment_ai_config.py` | Create — migration |
| `core/config.py` | Edit — add AISettings |
| `.env.example` | Edit — add AI keys |
| `src/request_bc/request/application/commands/create_request.py` | Edit — hook auto-assign |
| `adapters/http/api/settings/routers.py` | Create — AI config endpoints |
| `tests/unit/company_bc/equipment_profile/services/test_matching.py` | Create |
| `tests/unit/company_bc/equipment_profile/services/test_auto_assign.py` | Create |
| `tests/unit/company_bc/assignment_config/...` | Create |
| `tests/integration/test_auto_assignment.py` | Create |

---

## F3: Frontend UX for Settings & Assignment Visibility

**Scope:** React pages for profile management, manager assignment UI, company AI settings, and assignment explainability in request/asset detail.

### Pages/Components

1. **Equipment Profiles Page** (`/settings/equipment-profiles`)
   - List profiles by department/role, create/edit/activate/deactivate/delete
   - Profile detail with items table
   - Admin + department manager access

2. **Manager Assignment** (extend DepartmentsPage)
   - Add manager picker (user dropdown) to each department row
   - Admin only

3. **Company AI Settings** (`/settings/assignment-ai`)
   - Provider selector (OpenAI/Groq)
   - Prompt template textarea
   - Optional model field
   - Admin only

4. **Assignment Explainability** (extend RequestDetailPage + AssetDetailPage)
   - Show profile match metadata in request detail (profile name, matched assets, fallback reasons)
   - Show "profile-based assignment" badge in asset events

### Navigation
- Add "Equipment Profiles" to Management section (admin + manager)
- Add "Assignment AI" to Management section (admin only)

### i18n
- EN + ES keys for all profile, AI config, matching, and fallback UI text

### Tests
- TypeScript compiles
- Build succeeds (`npm run build`)

### Files

| File | Action |
|------|--------|
| `web/app/src/pages/admin/EquipmentProfilesPage.tsx` | Create |
| `web/app/src/pages/admin/AssignmentAISettingsPage.tsx` | Create |
| `web/app/src/pages/admin/DepartmentsPage.tsx` | Edit — add manager picker |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Edit — show match metadata |
| `web/app/src/pages/technician/AssetDetailPage.tsx` | Edit — show profile events |
| `web/app/src/types/index.ts` | Edit — add EquipmentProfile, ProfileItem, AIConfig types |
| `web/app/src/router.tsx` | Edit — add 2 routes |
| `web/app/src/components/layout/Sidebar.tsx` | Edit — add 2 nav items |
| `web/app/src/locales/en.ts` | Edit — add ~40 keys |
| `web/app/src/locales/es.ts` | Edit — add ~40 keys |

---

## Recommended Implementation Order

1. **F0** — Foundation: manager FK, 2 commands, 2 endpoints, tests (~1 session)
2. **F1** — Core: profile entities, 5 commands, 2 queries, 7 endpoints, tests (~2 sessions)
3. **F2** — Engine: AI config, matching service, provider adapters, request hook, tests (~2-3 sessions)
4. **F3** — Frontend: 2 new pages, 3 page edits, i18n, routing (~1-2 sessions)

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1 → F2 → F3)
- [x] Each feature independently deployable
- [x] Vertical slices — each feature delivers complete functionality end-to-end
- [x] Shared foundation identified (F0 manager + authorization helper)
- [x] No overlapping scope between features
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered (managers + profiles + auto-assignment + frontend)

## Risk Notes

- **AI provider latency:** OpenAI/Groq calls add latency to request creation. Consider async fallback if response takes >5s.
- **Spec matching from notes field:** Current assets store specs in `notes` (free text). Profile spec matching may need structured asset metadata in a future epic.
- **Manager authorization pattern:** First time dual-check auth is used. Keep helper isolated and well-tested to avoid permission leaks.
