# Tasks: F0 — Risk Foundation

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: enums, entities, exceptions, repository interface | M | Domain |
| 2 | Infrastructure: ORM models | S | Infra |
| 3 | Infrastructure: Alembic migration | S | Infra |
| 4 | Infrastructure: repository implementation | L | Infra |
| 5 | Application: CreateRiskCommand + handler | S | App |
| 6 | Application: UpdateRiskCommand + handler | S | App |
| 7 | Application: AssessRiskCommand + handler | S | App |
| 8 | Application: ChangeRiskStatusCommand + handler | S | App |
| 9 | Application: SetTreatmentCommand + handler | S | App |
| 10 | Application: DeleteRiskCommand + handler | S | App |
| 11 | Application: ListRisksQuery + handler | S | App |
| 12 | Application: GetRiskDetailQuery + handler | M | App |
| 13 | HTTP: schemas (request + response) | M | HTTP |
| 14 | HTTP: dependencies + routers (CRUD + assess + status + treatment) | L | HTTP |
| 15 | HTTP: Register router in app.py | S | HTTP |
| 16 | Unit tests: domain entities | M | Test |
| 17 | Unit tests: command handlers | M | Test |
| 18 | Unit tests: query handlers | S | Test |
| 19 | Integration tests: risk endpoints | L | Test |
| 20 | Frontend: TypeScript types | S | FE |
| 21 | Frontend: RiskListPage | M | FE |
| 22 | Frontend: RiskDetailPage | L | FE |
| 23 | Frontend: CreateRiskPage + EditRiskPage | M | FE |
| 24 | Frontend: routes + sidebar entries | S | FE |
| 25 | Frontend: i18n EN/ES translations | S | FE |

## Detailed Tasks

### Phase 1: Domain

#### Task 1: Enums, entities, exceptions, repository interface
- **Files:** `src/risk_bc/risk/domain/enums.py`, `src/risk_bc/risk/domain/entities.py`, `src/risk_bc/risk/domain/exceptions.py`, `src/risk_bc/risk/domain/repository.py`, `src/risk_bc/__init__.py`, `src/risk_bc/risk/__init__.py`, `src/risk_bc/risk/domain/__init__.py`
- **What:** All enums (RiskCategory, RiskLevel, RiskStatus, RiskTreatment, ReviewCadence, MitigationStatus, RiskLinkType, RiskHistoryEventType). VALID_STATUS_TRANSITIONS dict. RISK_LEVEL_MATRIX dict with calculate_risk_level function. Risk entity with create, assess, change_status, set_treatment, update_details methods. MitigationPlan, RiskLink, RiskHistory entities. All domain exceptions. ABC repository interface.
- **Acceptance:** All domain types defined, Risk.assess() auto-calculates level from matrix
- [x] Done

### Phase 2: Infrastructure

#### Task 2: ORM models
- **Files:** `src/risk_bc/risk/infrastructure/__init__.py`, `src/risk_bc/risk/infrastructure/models.py`
- **What:** RiskModel, MitigationPlanModel, RiskLinkModel, RiskHistoryModel with Mapped[] annotations, ULIDMixin, TimestampMixin, indexes.
- **Deps:** Task 1
- **Acceptance:** All models defined with proper indexes
- [x] Done

#### Task 3: Alembic migration
- **File:** `alembic/versions/y2a3b4c5d6e7_create_risk_tables.py`
- **What:** Create risks, mitigation_plans, risk_links, risk_history tables with all indexes and constraints.
- **Deps:** Task 2
- **Acceptance:** Migration runs up and down cleanly
- [x] Done

#### Task 4: Repository implementation
- **File:** `src/risk_bc/risk/infrastructure/repository.py`
- **What:** Implement all RiskRepositoryInterface methods: save, find_by_id, find_all (with filters + pagination), delete, add_history, get_history, save_mitigation, find_mitigation_by_id, get_mitigations, delete_mitigation, add_link, get_links, delete_link, get_dashboard_stats, find_overdue_reviews. User name resolution via join.
- **Deps:** Tasks 1-3
- **Acceptance:** All repo methods implemented, find_all supports category/status/level/treatment filters + pagination
- [x] Done

### Phase 3: Application

#### Task 5: CreateRiskCommand + handler
- **File:** `src/risk_bc/risk/application/commands/create_risk.py`, `src/risk_bc/risk/application/__init__.py`, `src/risk_bc/risk/application/commands/__init__.py`
- **What:** CreateRiskCommand(company_id, title, description, category, created_by, owner_id?). Handler creates Risk entity, saves, adds CREATED history entry.
- **Deps:** Task 4
- **Acceptance:** Creates risk with OPEN status, history recorded
- [x] Done

#### Task 6: UpdateRiskCommand + handler
- **File:** `src/risk_bc/risk/application/commands/update_risk.py`
- **What:** UpdateRiskCommand(risk_id, company_id, actor_id, title?, description?, category?, owner_id?, review_cadence?). Handler finds risk, calls update_details, saves, adds UPDATED history entry. Calculates next_review_at if cadence set.
- **Deps:** Task 4
- **Acceptance:** Updates allowed fields, history recorded
- [x] Done

#### Task 7: AssessRiskCommand + handler
- **File:** `src/risk_bc/risk/application/commands/assess_risk.py`
- **What:** AssessRiskCommand(risk_id, company_id, actor_id, likelihood, impact). Handler finds risk, calls assess(), saves, adds SCORE_CHANGED history entry with old/new values in metadata.
- **Deps:** Task 4
- **Acceptance:** Risk level auto-calculated, history records old and new values
- [x] Done

#### Task 8: ChangeRiskStatusCommand + handler
- **File:** `src/risk_bc/risk/application/commands/change_risk_status.py`
- **What:** ChangeRiskStatusCommand(risk_id, company_id, actor_id, new_status). Handler finds risk, calls change_status, saves, adds STATUS_CHANGED history entry.
- **Deps:** Task 4
- **Acceptance:** Valid transitions allowed, invalid rejected, history recorded
- [x] Done

#### Task 9: SetTreatmentCommand + handler
- **File:** `src/risk_bc/risk/application/commands/set_treatment.py`
- **What:** SetTreatmentCommand(risk_id, company_id, actor_id, treatment). Handler finds risk, calls set_treatment, saves, adds TREATMENT_CHANGED history entry.
- **Deps:** Task 4
- **Acceptance:** Treatment set, history recorded
- [x] Done

#### Task 10: DeleteRiskCommand + handler
- **File:** `src/risk_bc/risk/application/commands/delete_risk.py`
- **What:** DeleteRiskCommand(risk_id, company_id). Handler calls repo.delete().
- **Deps:** Task 4
- **Acceptance:** Risk and related data deleted
- [x] Done

#### Task 11: ListRisksQuery + handler
- **File:** `src/risk_bc/risk/application/queries/list_risks.py`, `src/risk_bc/risk/application/queries/__init__.py`
- **What:** ListRisksQuery(company_id, page, page_size, category?, status?, risk_level?, treatment?). Handler calls repo.find_all, maps to RiskListDto with owner_name resolution.
- **Deps:** Task 4
- **Acceptance:** Returns paginated, filtered list with total count
- [x] Done

#### Task 12: GetRiskDetailQuery + handler
- **File:** `src/risk_bc/risk/application/queries/get_risk_detail.py`
- **What:** GetRiskDetailQuery(risk_id, company_id). Handler calls repo.find_by_id, gets mitigations, links, history, resolves user names, maps to RiskDetailDto.
- **Deps:** Task 4
- **Acceptance:** Returns full risk detail with mitigations, links, history, resolved names
- [x] Done

### Phase 4: HTTP

#### Task 13: Schemas
- **File:** `adapters/http/api/risks/schemas.py`, `adapters/http/api/risks/__init__.py`
- **What:** CreateRiskRequest, UpdateRiskRequest, AssessRiskRequest, SetTreatmentRequest, ChangeStatusRequest. RiskListItemResponse, RiskDetailResponse, MitigationResponse, RiskLinkResponse, RiskHistoryResponse.
- **Deps:** Tasks 5-12
- **Acceptance:** All request/response schemas defined with validation
- [x] Done

#### Task 14: Dependencies + routers
- **File:** `adapters/http/api/risks/dependencies.py`, `adapters/http/api/risks/routers.py`
- **What:** get_risk_repo dependency. All F0 endpoints: POST /risks, GET /risks, GET /risks/:id, PUT /risks/:id, DELETE /risks/:id, POST /risks/:id/assess, POST /risks/:id/treatment, POST /risks/:id/status, GET /risks/:id/history.
- **Deps:** Task 13
- **Acceptance:** All endpoints working with proper auth
- [x] Done

#### Task 15: Register router in app.py
- **File:** `app.py`
- **What:** Import and include risks router.
- **Deps:** Task 14
- **Acceptance:** Router registered, endpoints accessible
- [x] Done

### Phase 5: Tests

#### Task 16: Unit tests — domain entities
- **File:** `tests/unit/risk_bc/risk/domain/test_entities.py`, `tests/unit/risk_bc/__init__.py`, `tests/unit/risk_bc/risk/__init__.py`, `tests/unit/risk_bc/risk/domain/__init__.py`
- **What:** Test Risk.create validation, Risk.assess with matrix calculation, Risk.change_status valid/invalid transitions, Risk.set_treatment. Test MitigationPlan.create, update_status.
- **Acceptance:** All domain logic covered
- [x] Done

#### Task 17: Unit tests — command handlers
- **File:** `tests/unit/risk_bc/risk/application/commands/test_commands.py`, `tests/unit/risk_bc/risk/application/__init__.py`, `tests/unit/risk_bc/risk/application/commands/__init__.py`
- **What:** Test CreateRiskCommandHandler, AssessRiskCommandHandler, ChangeRiskStatusCommandHandler, SetTreatmentCommandHandler, UpdateRiskCommandHandler, DeleteRiskCommandHandler. Mock repo.
- **Acceptance:** All command handlers tested
- [x] Done

#### Task 18: Unit tests — query handlers
- **File:** `tests/unit/risk_bc/risk/application/queries/test_queries.py`, `tests/unit/risk_bc/risk/application/queries/__init__.py`
- **What:** Test ListRisksQueryHandler, GetRiskDetailQueryHandler. Mock repo.
- **Acceptance:** All query handlers tested
- [x] Done

#### Task 19: Integration tests
- **File:** `tests/integration/test_risks_endpoints.py`
- **What:** Test all F0 endpoints: create risk (201), list risks (200, pagination, filters), get risk detail (200), update risk (200), delete risk (204), assess risk (200, level calculated), change status (200, invalid=422), set treatment (200), get history (200). Test auth: employee=403, admin=200. Test not found=404.
- **Acceptance:** All endpoints tested with real DB
- [x] Done

### Phase 6: Frontend

#### Task 20: TypeScript types
- **File:** `web/app/src/types/index.ts`
- **What:** Add Risk, RiskListItem, RiskDetail, MitigationPlan, RiskLink, RiskHistoryEntry interfaces.
- **Acceptance:** All types defined
- [x] Done

#### Task 21: RiskListPage
- **File:** `web/app/src/pages/technician/RiskListPage.tsx` (NEW)
- **What:** Paginated table with category/status/level/treatment filters. Color-coded risk level badges. Link to detail. Create button (admin only).
- **Acceptance:** List renders with filters and pagination
- [x] Done

#### Task 22: RiskDetailPage
- **File:** `web/app/src/pages/technician/RiskDetailPage.tsx` (NEW)
- **What:** Risk info section with scoring visualization. Status badge + change button. Treatment badge. Mitigations list (placeholder for F1). Links section (placeholder for F1). History timeline. Edit/Delete buttons (admin).
- **Acceptance:** Full detail page renders with all sections
- [x] Done

#### Task 23: CreateRiskPage + EditRiskPage
- **File:** `web/app/src/pages/technician/CreateRiskPage.tsx` (NEW), `web/app/src/pages/technician/EditRiskPage.tsx` (NEW)
- **What:** Form with title, description, category dropdown, owner selection. Edit reuses form with pre-filled data. Assess and treatment as separate actions on detail page.
- **Acceptance:** Create and edit forms work correctly
- [x] Done

#### Task 24: Routes + sidebar entries
- **File:** `web/app/src/router.tsx`, `web/app/src/components/layout/Sidebar.tsx`
- **What:** Add routes: /risks, /risks/new, /risks/:id, /risks/:id/edit. Sidebar entry under Security section with shield icon.
- **Acceptance:** Navigation works, sidebar shows entry
- [x] Done

#### Task 25: i18n translations
- **File:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** All risk labels: page titles, form fields, status names, category names, level names, treatment names, buttons, table headers, history events.
- **Acceptance:** All strings translated EN + ES
- [x] Done
