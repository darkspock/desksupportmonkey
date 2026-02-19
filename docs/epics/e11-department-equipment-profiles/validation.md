# Validation: E11 - Department Equipment Profiles

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-17
**Status:** Validated against codebase

---

## Architecture Fit

- **Bounded contexts involved**
  - `company_bc` for department manager ownership, profile configuration, and AI assignment config.
  - `asset_bc` for stock matching and assignment execution.
  - `request_bc` for onboarding/new-equipment flow integration.
  - `notification_bc` for assignment/fallback notifications.
- **Pattern fit**
  - Commands for write operations (assign manager, profile CRUD, auto-assign apply).
  - Queries for profile retrieval and assignment diagnostics.
  - Event emission for auditability and UI history feed.

**Verified:** Existing CQRS pattern (`Command`/`CommandHandler`, `Query`/`QueryHandler` from `src/framework/`) supports all planned operations.

---

## Dependency Check

| Dependency | Status | What It Provides |
|---|---|---|
| E1 (Company Management) | Done | Departments, users, roles, multi-tenancy |
| E2 (Asset Inventory) | Done | Asset CRUD, assignment commands, events |
| E3 (Service Requests) | Done | Request types (incident, new_equipment, onboarding), state machine |
| E7 (Frontend) | Done | React shell, routing, design system |
| E9 (UX) | Done | i18n, toast, confirm dialogs, admin page patterns |

**Verdict:** All dependencies are complete. No blockers.

---

## Codebase Gap Analysis

### F0: Department Managers

| Requirement | Codebase State | Gap |
|---|---|---|
| `department.manager_user_id` field | Missing from entity and model | Add field + migration |
| Assign/remove manager commands | Not implemented | Create 2 commands |
| Manager HTTP endpoints | Not implemented | Add to departments router |
| Manager in department responses | Not in DTOs | Update response schemas |

**Current Department entity** (`src/company_bc/department/domain/entities.py`):
- Fields: `id`, `company_id`, `name`, `is_active`, `created_at`, `updated_at`
- Missing: `manager_user_id`

**Current Department DB model** (`src/company_bc/department/infrastructure/repository.py`):
- Uses `Mapped[type]` (SQLAlchemy 2.0) — correct
- Unique constraint on `(company_id, name)` — correct
- Missing: `manager_user_id` FK column

**Migration needed:** Add nullable `manager_user_id` (String(26), FK to `users.id`, SET NULL on delete)

### F1: Equipment Profile CRUD

| Requirement | Codebase State | Gap |
|---|---|---|
| EquipmentProfile entity | Does not exist | Create in `company_bc/equipment_profile/` |
| EquipmentProfileItem entity | Does not exist | Create as value object |
| Profile tables + migration | Not created | New migration |
| Profile CRUD commands/queries | Not implemented | Create 4+ handlers |
| Profile HTTP router | Does not exist | New router |

**Recommendation:** Place profile entities under `company_bc/equipment_profile/` subdomain (consistent with `company_bc/department/` pattern).

### F2: Auto-Assignment Engine

| Requirement | Codebase State | Gap |
|---|---|---|
| CompanyAssignmentAIConfig entity | Does not exist | Create in `company_bc/assignment_config/` |
| Matching service | Does not exist | Implement deterministic filter + AI tie-break |
| AI provider adapters | Does not exist | Port pattern for OpenAI/Groq |
| Request flow hook | `create_request.py` exists, no hook | Add post-creation subscriber |
| Fallback reason enum | Does not exist | Create enum with 6 codes |

**Current request creation** (`src/request_bc/request/application/commands/create_request.py`):
- Simple: validate type → create request → save → emit event
- No auto-assignment logic (correct — should be separate concern)

**Current asset assignment** (`src/asset_bc/asset/application/commands/assign_asset.py`):
- Validates asset/user in company, status check, calls `asset.assign()`, emits event
- Reusable for profile-driven assignment (add metadata to event data dict)

**Event publishing:** `notification_bc` has `EventBus` with `DomainEvent`, but asset/request BCs use local event models (`AssetEvent`/`RequestEvent`). Cross-BC events are not integrated via EventBus.
- **Recommendation:** Keep profile metadata in request/asset event `data` dicts for now. Avoid EventBus refactoring.

### F3: Frontend UX

| Requirement | Codebase State | Gap |
|---|---|---|
| Profile management page | Does not exist | New React page |
| Manager assignment UI | Does not exist | Add to departments page |
| AI settings page | Does not exist | New company settings section |
| Assignment explainability | Not rendered | Add to request/asset detail |
| i18n keys | Not created | Add EN/ES keys |

**Frontend patterns confirmed:**
- Admin pages follow: `useQuery` + `useMutation` + `Table/Card/Badge/ConfirmDialog` pattern
- Role-guarded routing via `RequireRole` component
- i18n via `useI18n()` with `en.ts`/`es.ts` dictionaries

---

## Validation Decisions (Resolved)

1. **Manager cardinality:** one manager per department (`department.manager_user_id`).
2. **Active profile cardinality:** one active profile per `company+department+role`.
3. **Tie-break strategy:** company-defined prompt + provider (`OPENAI` or `GROQ`) decides between equivalent candidates.
4. **Fallback reason taxonomy:** `NO_ACTIVE_PROFILE`, `NO_STOCK_FOR_REQUIRED_TYPE`, `SPEC_MISMATCH`, `ASSET_NOT_ASSIGNABLE`, `AI_UNAVAILABLE`, `MANUAL_REVIEW_REQUIRED`.
5. **Fallback precedence:** evaluate and emit codes in deterministic order (profile → stock → specs → assignment constraints → AI availability → manual review).
6. **Manager FK constraint:** SET NULL on user deletion (department loses manager, continues to exist).
7. **Profile bounded context:** Extend `company_bc` with `equipment_profile/` and `assignment_config/` subdomains.
8. **Manager authorization:** Dual check — `role >= ADMIN` OR `user.id == department.manager_user_id`.
9. **Spec constraint schema:** Typed fields per profile item — `min_ram_gb`, `min_storage_gb`, `preferred_brand`, `preferred_model`.
10. **Auto-assignment trigger:** Automatic on request creation for `new_equipment`/`onboarding` types.
11. **AI provider credentials:** Env vars (`OPENAI_API_KEY`, `GROQ_API_KEY`) shared across all companies.

---

## Scope Integrity

**In scope:**
- Single-manager assignment per department.
- Profile CRUD and activation/deactivation with one-active-profile policy per `company+department+role`.
- Auto-assignment with deterministic candidate filtering, AI tie-break (`OPENAI`/`GROQ`) and fallback reasons.
- UI for management and visibility.

**Out of scope:**
- Procurement/budget automation (E14).
- Shipping lifecycle (E16).
- AI-driven profile inference (E13).

Scope boundaries are clear and coherent with roadmap sequencing.

---

## Main Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Permission drift (admin vs manager vs technician) | Medium | Explicit policy matrix per endpoint + role tests |
| Cross-tenant leakage in profile queries | High | Mandatory `company_id` scoping in repository; negative path tests |
| Non-determinism in AI tie-break | Medium | Temperature 0, structured output, persisted decision metadata |
| Silent failures when stock unavailable | Medium | Explicit fallback reason codes and user-facing messaging |
| Concurrent assignment race conditions | Medium | Database-level constraint or optimistic locking in assign command |
| Dangling manager FK on user deletion | Low | SET NULL constraint on `manager_user_id` |

---

## Test Strategy

- **Unit**
  - Profile validation and matching algorithm.
  - AI prompt routing/adapter selection by company config.
  - Permission checks (admin vs manager vs technician).
  - Fallback reason evaluation order.
- **Integration/API**
  - Manager/profile CRUD auth + company isolation.
  - Auto-assignment success + fallback paths.
  - Override/manual assignment after fallback.
- **Frontend**
  - Profile settings forms, manager assignment controls, assignment explanation rendering.
- **Regression**
  - Existing manual assignment and request flows remain functional (596 existing tests).

---

## Implementation Estimate

| Feature | New Files | Migrations | Commands | Queries | Endpoints | Tests |
|---|---|---|---|---|---|---|
| F0: Managers | ~5 | 1 | 2 | 0 (update existing) | 2 | ~8 |
| F1: Profile CRUD | ~10 | 1 | 4-5 | 2-3 | 5-6 | ~15 |
| F2: Auto-Assignment | ~8 | 1 | 1-2 | 1-2 | 2-3 | ~20 |
| F3: Frontend | ~5 | 0 | 0 | 0 | 0 | TS compile |
| **Total** | **~28** | **3** | **7-9** | **3-5** | **9-11** | **~43+** |

---

## Go/No-Go

**Go**, with conditions:
1. F2 must define the AI decision contract (provider adapter interface, prompt template variables, structured output schema, and fallback behavior) before implementation starts.
2. Migration ordering: manager FK first (F0), then profile tables (F1), then AI config (F2).
3. Run full test suite (`make test` + `make test-integration`) after each feature to catch regressions early.
