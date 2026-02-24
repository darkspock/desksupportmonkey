# Implementation Tasks: Compliance Assessment Foundation (F0)

**Created:** 2026-02-24
**Total Tasks:** 8
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Entities | 1 | M |
| Domain - Exceptions | 1 | S |
| Domain - Repository | 1 | S |
| Infrastructure - Models | 1 | M |
| Infrastructure - Migration | 1 | S |
| Infrastructure - Repository | 1 | M |
| Application - Commands & Queries | 1 | L |

---

## Phase 1: Domain Layer

### TASK-001: Add ComplianceStatus and EvidenceType enums

- [x] Add `ComplianceStatus` enum (COMPLIANT, PARTIAL, NON_COMPLIANT, NOT_ASSESSED) to `src/audit_bc/audit/domain/enums.py`
- [x] Add `EvidenceType` enum (AUDIT_LOG, INCIDENT, RISK, SLA, MANUAL) to same file

### TASK-002: Create ComplianceAssessment and ComplianceEvidence entities

- [x] Add `ComplianceAssessment` dataclass with `create()` and `update_status()` to `src/audit_bc/audit/domain/entities.py`
- [x] Add `ComplianceEvidence` dataclass with `create()` to same file

### TASK-003: Add domain exceptions

- [x] Add `EvidenceNotFoundError` to `src/audit_bc/audit/domain/exceptions.py`
- [x] Add `InvalidComplianceStatusError` to same file

### TASK-004: Extend repository interface

- [x] Add 9 abstract methods for assessment and evidence to `src/audit_bc/audit/domain/repository.py`

## Phase 2: Infrastructure Layer

### TASK-005: Create SQLAlchemy models

- [x] Add `ComplianceAssessmentModel` with unique constraint on (company_id, control_id)
- [x] Add `ComplianceEvidenceModel` with indexes

### TASK-006: Create Alembic migration

- [x] Create `alembic/versions/e6f7g8h9i0j1_create_compliance_tables.py`

### TASK-007: Implement repository methods

- [x] Implement all 9 methods in `src/audit_bc/audit/infrastructure/repository.py`
- [x] Add `_to_assessment_entity()` and `_to_evidence_entity()` converters

## Phase 3: Application Layer

### TASK-008: Create commands, queries, DTOs, and HTTP endpoints

- [x] `AssessComplianceControlCommand/Handler`
- [x] `AddComplianceEvidenceCommand/Handler`
- [x] `RemoveComplianceEvidenceCommand/Handler`
- [x] `GetComplianceAssessmentsQuery/Handler`
- [x] `ListComplianceEvidenceQuery/Handler`
- [x] DTOs: `ControlAssessmentDto`, `ComplianceEvidenceDto`, `FrameworkSummaryDto`, `ComplianceDashboardDto`
- [x] HTTP schemas and 8 endpoints under `/compliance/`
