# Tasks: F1 — Risk Assessments

**Feature:** [requirements.md](../../requirements.md)
**Date:** 2026-02-26

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: VendorRiskAssessment entity, repository interface, risk level calculation | M | Domain |
| 2 | Infrastructure: VendorRiskAssessmentModel | S | Infra |
| 3 | Infrastructure: Alembic migration | S | Infra |
| 4 | Infrastructure: VendorRiskAssessment repository implementation | M | Infra |
| 5 | Application: CreateAssessmentCommand + handler (with risk_level caching + escalation) | M | App |
| 6 | Application: SoftDeleteAssessmentCommand + handler | S | App |
| 7 | Application: ListAssessmentsQuery + handler | S | App |
| 8 | Application: GetAssessmentQuery + handler | S | App |
| 9 | HTTP: assessment schemas | S | HTTP |
| 10 | HTTP: assessment router + dependencies | M | HTTP |
| 11 | HTTP: Register router in app.py | S | HTTP |
| 12 | Unit tests: domain entity (risk level calculation) | M | Test |
| 13 | Unit tests: command handlers | M | Test |
| 14 | Unit tests: query handlers | S | Test |
| 15 | Integration tests: assessment endpoints | M | Test |
| 16 | Frontend: TypeScript types | S | FE |
| 17 | Frontend: i18n EN/ES translations for assessments | S | FE |

## Detailed Tasks

### Phase 1: Domain

#### Task 1: VendorRiskAssessment entity, repository interface, risk level calculation
- **Files:**
  - `src/procurement_bc/vendor/domain/entities.py` (add VendorRiskAssessment)
  - `src/procurement_bc/vendor/domain/repository.py` (add VendorRiskAssessmentRepositoryInterface)
- **What:**
  - `VendorRiskAssessment` entity with `create()` factory method. All 5 scores validated 1-5. `calculate_risk_level()` class method: avg of 5 scores → 1.0-2.0=low, 2.1-3.0=medium, 3.1-4.0=high, 4.1-5.0=critical. `soft_delete()` method.
  - Risk level escalation logic: `calculate_vendor_risk_level(assessment_level, is_critical_ict, has_security_clauses)` → if is_critical_ict and not has_security_clauses → critical. Else → assessment_level.
  - `VendorRiskAssessmentRepositoryInterface` ABC: save, find_by_id, find_all_by_vendor (paginated), find_latest_by_vendor, soft_delete, find_vendors_with_stale_assessments
  - Exception: `AssessmentNotFoundError`
- **Acceptance:** Risk level calculation correct for all boundary values, escalation rule works
- [x] Done

### Phase 2: Infrastructure

#### Task 2: ORM model
- **File:** `src/procurement_bc/vendor/infrastructure/models.py` (add)
- **What:** `VendorRiskAssessmentModel` with Mapped[] annotations. All 5 score columns as SmallInteger. is_deleted default false. Indexes: (vendor_id, company_id), (company_id, assessment_date).
- **Deps:** Task 1
- **Acceptance:** Model defined with proper indexes
- [x] Done

#### Task 3: Alembic migration
- **File:** `alembic/versions/` (new migration)
- **What:** Create `vendor_risk_assessments` table with all columns and indexes.
- **Deps:** Task 2
- **Acceptance:** Migration runs up and down cleanly
- [x] Done

#### Task 4: Repository implementation
- **File:** `src/procurement_bc/vendor/infrastructure/repository.py` (extend)
- **What:** Implement `VendorRiskAssessmentRepositoryInterface`: save, find_by_id (filter is_deleted=false), find_all_by_vendor (paginated, is_deleted=false, ordered by assessment_date desc), find_latest_by_vendor, soft_delete, find_vendors_with_stale_assessments (latest assessment's next_review_date < today).
- **Deps:** Tasks 1-3
- **Acceptance:** All methods work, soft delete filtering applied
- [x] Done

### Phase 3: Application

#### Task 5: CreateAssessmentCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/create_assessment.py`
- **What:** `CreateAssessmentCommand(vendor_id, company_id, assessed_by, assessment_date, next_review_date?, data_handling_score, security_certs_score, incident_response_score, business_continuity_score, subcontractor_score, justification?)`. Handler: validates vendor exists, creates assessment (auto-calculates overall_risk_level), saves assessment, then updates vendor.risk_level using escalation logic (checks if vendor is_critical_ict and has active contract with security clauses), saves vendor.
- **Deps:** Task 4
- **Acceptance:** Assessment created, vendor risk_level cached with escalation rule applied
- [x] Done

#### Task 6: SoftDeleteAssessmentCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/soft_delete_assessment.py`
- **What:** `SoftDeleteAssessmentCommand(assessment_id, vendor_id, company_id)`. Marks deleted. Then recalculates vendor risk_level from the new latest non-deleted assessment (or null if none remain).
- **Deps:** Task 4
- **Acceptance:** Assessment soft-deleted, vendor risk_level recalculated
- [x] Done

#### Task 7: ListAssessmentsQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/list_assessments.py`
- **What:** `ListAssessmentsQuery(vendor_id, company_id, page, page_size)`. Returns `tuple[list[AssessmentDto], int]`. Include assessed_by user name resolution.
- **Deps:** Task 4
- **Acceptance:** Returns paginated list ordered by assessment_date desc
- [x] Done

#### Task 8: GetAssessmentQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/get_assessment.py`
- **What:** `GetAssessmentQuery(assessment_id, vendor_id, company_id)`. Returns `AssessmentDto`.
- **Deps:** Task 4
- **Acceptance:** Returns assessment detail or raises not found
- [x] Done

### Phase 4: HTTP

#### Task 9: Assessment schemas
- **File:** `adapters/http/api/vendors/assessment_schemas.py` (new)
- **What:** `CreateAssessmentRequest` (all 5 scores required, 1-5 range validation), `AssessmentResponse`, `AssessmentListResponse`.
- **Deps:** Tasks 5-8
- **Acceptance:** All schemas defined with 1-5 score validation
- [x] Done

#### Task 10: Assessment router + dependencies
- **File:** `adapters/http/api/vendors/assessment_router.py` (new), `adapters/http/api/vendors/assessment_dependencies.py` (new)
- **What:** POST create, GET list, GET detail, DELETE soft-delete. Auth: create/delete = admin, list/get = technician+.
- **Deps:** Task 9
- **Acceptance:** All endpoints working with proper auth
- [x] Done

#### Task 11: Register router in app.py
- **File:** `app.py` (extend)
- **What:** Include assessment_router under vendors prefix.
- **Deps:** Task 10
- **Acceptance:** Router registered
- [x] Done

### Phase 5: Tests

#### Task 12: Unit tests — domain entity
- **File:** `tests/unit/procurement_bc/vendor/domain/test_assessment_entities.py` (new)
- **What:** Test calculate_risk_level: boundary values (avg 2.0=low, 2.1=medium, 3.0=medium, 3.1=high, 4.0=high, 4.1=critical), all 1s=low, all 5s=critical. Test escalation: critical_ict without clauses → critical, with clauses → assessment level.
- **Acceptance:** All calculation edge cases covered
- [x] Done

#### Task 13: Unit tests — command handlers
- **File:** `tests/unit/procurement_bc/vendor/application/commands/test_assessment_commands.py` (new)
- **What:** Test CreateAssessmentCommandHandler (creates + caches risk_level + escalation), SoftDeleteAssessmentCommandHandler (deletes + recalculates). Mock repos.
- **Acceptance:** All command handlers tested including escalation logic
- [x] Done

#### Task 14: Unit tests — query handlers
- **File:** `tests/unit/procurement_bc/vendor/application/queries/test_assessment_queries.py` (new)
- **What:** Test ListAssessmentsQueryHandler (pagination), GetAssessmentQueryHandler (found, not found). Mock repo.
- **Acceptance:** All query handlers tested
- [x] Done

#### Task 15: Integration tests — assessment endpoints
- **File:** `tests/integration/test_vendor_assessments_endpoints.py` (new)
- **What:** Create assessment (201, risk_level calculated), list (200, ordered by date desc), get detail (200), soft delete (204). Auth: employee=403, admin=200. Vendor risk_level updated after assessment. Score validation (0 or 6 → 422).
- **Acceptance:** All endpoints tested with real DB
- [x] Done

### Phase 6: Frontend

#### Task 16: TypeScript types
- **File:** `web/app/src/types/index.ts`
- **What:** Add `VendorRiskAssessment` interface.
- **Acceptance:** Type defined
- [x] Done

#### Task 17: i18n EN/ES translations
- **Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** Assessment-related keys: score labels (data_handling, security_certs, incident_response, business_continuity, subcontractor), risk level names, form titles, buttons.
- **Acceptance:** All strings translated EN + ES
- [x] Done
