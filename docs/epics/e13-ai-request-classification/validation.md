# Validation: E13 - AI Request Classification

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-18
**Status:** Validated against codebase

---

## Architecture Fit

| Aspect | Assessment |
|--------|-----------|
| Bounded contexts | `request_bc` (classification service, port, scoring), `company_bc` (config CRUD) |
| Pattern compliance | Port/adapter for AI (mirrors E11 `AITieBreakerPort`), CQRS for config, DDD layering |
| Multi-tenancy | All config and data scoped by `company_id` |
| Backward compatibility | `request.data.ai_classification` is optional — existing requests unaffected |

---

## Dependency Check

| Dependency | Status | What It Provides |
|------------|--------|------------------|
| E0 (Foundation) | Done | FastAPI, SQLAlchemy, Alembic, JWT auth, RBAC |
| E3 (Service Requests) | Done | `ServiceRequest` entity, `CreateRequestCommand`, request CRUD |
| E11 (Equipment Profiles) | Done | `AIProvider` enum, `AITieBreakerPort` adapter pattern, `AutoAssignService` orchestration pattern, `CompanyAssignmentAIConfig` config pattern |
| E12 (Request Typification) | Done | `RequestType` (6 values), `RequestSubtype` (16 values), `VALID_SUBTYPES`, `PriorityScorer`, approval workflow |

All dependencies satisfied.

---

## Codebase Gap Analysis

### F0: Classification Service

| Requirement | Codebase State | Gap |
|-------------|---------------|-----|
| `RequestClassifierPort` (ABC) | `ports.py` has only `UserLookup` | Add new port |
| `ClassificationResult` dataclass | Does not exist | Create |
| `ClassificationService` | Does not exist | Create in `application/services/` |
| OpenAI classifier adapter | `OpenAIAdapter` exists for tiebreaking in `ai_tiebreaker.py` | Create new adapter for classification in `request_bc/infrastructure/ai/` |
| Groq classifier adapter | `GroqAdapter` exists for tiebreaking | Create new adapter |
| `AIProvider` enum | Exists in `assignment_config/domain/enums.py` | Reuse or extract to shared location |

### F1: Company Configuration

| Requirement | Codebase State | Gap |
|-------------|---------------|-----|
| `CompanyClassificationConfig` entity | Does not exist | Create — mirror `CompanyAssignmentAIConfig` with extra fields: `is_enabled`, `confidence_threshold`, `timeout_seconds` |
| `ClassificationConfigRepositoryInterface` | Does not exist | Create — same pattern as `AssignmentConfigRepositoryInterface` |
| `ClassificationConfigModel` | Does not exist | Create — table `company_classification_configs` |
| Migration | Does not exist | Create alembic migration |
| `SaveClassificationConfigCommand` + handler | Does not exist | Create — mirror `SaveCompanyAIConfigCommand` |
| `GetClassificationConfigQuery` + handler | Does not exist | Create — mirror `GetCompanyAIConfigQuery` |
| `PUT /api/v1/settings/request-classification` | Does not exist | Add endpoint |
| `GET /api/v1/settings/request-classification` | Does not exist | Add endpoint |
| Router registration in `app.py` | `settings_router` registered at line 83 | Add new router or extend existing |

### F2: Request Integration

| Requirement | Codebase State | Gap |
|-------------|---------------|-----|
| `PriorityScorer.compute()` extension | Current signature: `(request_type, subtype, dept_weight, user_role)` | Add `ai_priority_hint: int = 0` parameter |
| `CreateRequestCommand` extension | Current fields: type, title, description, data, subtype, dept_weight, user_role, dept_has_manager | Add `ai_priority_hint`, `ai_classification` metadata |
| Classification config lookup in router | `dependencies.py` has repos for requests, users, assets, profiles, assignment config, departments | Add `get_classification_config_repo()` |
| Classification call in create flow | Not present | Add classification call before command construction |
| `request.data.ai_classification` storage | `data: Optional[dict]` exists and stores `priority_scoring` | Add `ai_classification` key alongside existing data |

### F3: Frontend

| Requirement | Codebase State | Gap |
|-------------|---------------|-----|
| `ClassificationSettingsPage.tsx` | Does not exist | Create — mirror `AssignmentAISettingsPage.tsx` |
| AI Classification card on detail | `AutoAssignmentCard` exists as reference pattern | Add `AIClassificationCard` |
| Route `settings/request-classification` | Not in `router.tsx` | Add lazy import + route |
| Sidebar nav item | Not in `Sidebar.tsx` | Add item in management section |
| `CompanyClassificationConfig` TypeScript type | Does not exist | Add to `types/index.ts` |
| i18n keys (~30 per language) | Not present | Add to `en.ts` and `es.ts` |

---

## Scope Integrity

**In scope:**
- Classification service (port + adapters + orchestration)
- Per-company config CRUD
- Integration into request creation flow
- Priority scoring extension
- Frontend settings page and classification result display
- Graceful fallback on AI failure

**Out of scope (explicit non-goals):**
- Real-time reclassification after creation
- Employee-facing AI preview before submission
- Custom per-company types/subtypes (E30)
- AI-generated response suggestions
- Model fine-tuning
- Cost tracking for AI calls

---

## Main Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| AI latency adds 1-3s to request creation | Medium | Configurable timeout (default 10s), graceful fallback |
| AI cost per request creation | Medium | Per-company enable/disable toggle |
| Prompt injection via request descriptions | Low | User content in user message only, JSON mode output |
| AI suggests invalid type/subtype | Medium | Pre-validate against `VALID_SUBTYPES` before override |
| Override confuses employees | Low | "AI Classified" badge + original classification display |
| `AIProvider` enum cross-subdomain coupling | Low | Extract to shared BC or reuse within `company_bc` |

---

## Test Strategy

| Type | Scope | Estimated Count |
|------|-------|----------------|
| Unit — F0 | Classification orchestrator, adapter mocks, result parsing | ~15 |
| Unit — F1 | Save command validation, get query, threshold/provider checks | ~7 |
| Unit — F2 | PriorityScorer extension, ClassificationService logic, command handler | ~13 |
| Integration — F1 | PUT/GET config endpoints, auth guards | ~7 |
| Integration — F2 | Create request with/without AI classification | ~3 |
| Frontend — F3 | TypeScript compilation, build success | 2 |
| **Total** | | **~47** |

---

## Implementation Estimate

| Feature | New Files | Migrations | Commands | Queries | Endpoints | Tests |
|---------|-----------|------------|----------|---------|-----------|-------|
| F0: Classification Service | ~5 | 0 | 0 | 0 | 0 | ~15 |
| F1: Company Configuration | ~10 | 1 | 1 | 1 | 2 | ~14 |
| F2: Request Integration | ~2 | 0 | 0 (edit) | 0 | 0 (edit) | ~16 |
| F3: Frontend UX | ~1 | 0 | 0 | 0 | 0 | 2 |
| **Total** | **~18** | **1** | **1** | **1** | **2** | **~47** |

---

## Go/No-Go

**Go** — with conditions:

1. All E11 and E12 dependencies are complete (verified).
2. `AIProvider` enum reuse strategy must be decided during design (shared BC vs. direct import).
3. Classification business logic placement must be decided during design (application service vs. router helper).
4. Query return type (DTO vs. entity) must be decided during design per architecture rules.
