# Requirements: E11 - Department Equipment Profiles

**Epic:** E11
**Date:** 2026-02-17
**Priority:** High
**Status:** Pending
**Depends on:** E1 (Company Management), E2 (Asset Inventory), E3 (Service Requests), E7 (Frontend), E9 (UX)

---

## Problem Statement

Today, asset assignment is mostly manual and person-dependent. This produces inconsistent setups between departments, slower onboarding, and frequent back-and-forth between admins, technicians, and requesters.

Each department should have a predictable equipment standard by role (for example: Engineering, Design, Leadership), and onboarding/new-equipment flows should apply these rules automatically whenever possible.

---

## Goals

1. Introduce **department managers** as an explicit role capability inside each company.
2. Allow admins/managers to define **equipment profiles** per department and role.
3. Add **automatic asset assignment** for onboarding/equipment requests using profile rules.
4. Keep assignment behavior deterministic, auditable, and reversible.
5. Improve UX so admins/technicians can understand why an asset was selected (or why no match was found).

---

## Validation Decisions (Closed)

1. **Manager model:** one manager per department (`department.manager_user_id`).
2. **Active profile policy:** only one active profile per `company + department + role`.
3. **Tie-breaker policy:** each company defines a custom AI prompt and provider (`OPENAI` or `GROQ`) to decide among equivalent candidates.
4. **Manager authorization:** dual check — `role >= ADMIN` OR `user.id == department.manager_user_id`. Manager is a relationship, not a role.
5. **Spec constraint schema:** typed fields per profile item — `min_ram_gb` (int), `min_storage_gb` (int), `preferred_brand` (str), `preferred_model` (str). No free-form JSON.
6. **Auto-assignment trigger:** automatic on request creation for `new_equipment` and `onboarding` types. No manual step required.
7. **AI provider credentials:** env vars (`OPENAI_API_KEY`, `GROQ_API_KEY`) shared across all companies. Company chooses provider, platform manages keys.

---

## Non-Goals (This Epic)

- Procurement workflows and purchase order lifecycle (E14).
- Shipping and delivery logistics (E16).
- Hardware cost/budget optimization engine.
- AI profile generation.

---

## User Stories

### US-E11-001: Department manager assignment
**As an** admin,  
**I want to** assign a manager to each department,  
**So that** ownership of equipment standards is clear.

**Acceptance Criteria:**
- [ ] Admin can assign or remove a manager for a department.
- [ ] Department supports a single manager at a time.
- [ ] Manager must belong to the same company.
- [ ] Department manager metadata is visible in department detail/list views.
- [ ] Changes are audit-logged.

### US-E11-002: Equipment profile CRUD by department and role
**As an** admin or department manager,  
**I want to** define recommended equipment per role within my department,  
**So that** employees get a consistent setup.

**Acceptance Criteria:**
- [ ] Profiles are scoped by `company + department + role`.
- [ ] Only one active profile is allowed for the same `company + department + role`.
- [ ] Profile supports one or more required assets (type + optional constraints).
- [ ] Constraints can include preferred brand/model and minimum specs (stored as structured fields/JSON).
- [ ] Profile can be activated/deactivated without deletion.
- [ ] Cross-company data isolation is enforced.

### US-E11-003: Automatic assignment from profile
**As a** technician/admin,  
**I want** onboarding/new-equipment requests to auto-select matching in-stock assets,  
**So that** manual assignment effort is reduced.

**Acceptance Criteria:**
- [ ] On request intake/processing, system searches for matching unassigned assets in company scope.
- [ ] Matching performs deterministic candidate filtering, then AI tie-breaker via company prompt/provider when needed.
- [ ] AI provider is configurable per company: `OPENAI` or `GROQ`.
- [ ] If AI provider is unavailable, deterministic fallback tie-breaker is applied.
- [ ] Successful auto-assignments create asset and request events.
- [ ] Assignee and requester can see assignment source (“profile-based”).

### US-E11-004: Graceful fallback when stock does not match
**As a** technician/admin,  
**I want** a clear fallback when profile matching fails,  
**So that** requests do not get stuck silently.

**Acceptance Criteria:**
- [ ] If no matching stock is found, request remains actionable with explicit “no profile match stock” reason.
- [ ] System exposes normalized fallback codes:
  - `NO_ACTIVE_PROFILE`
  - `NO_STOCK_FOR_REQUIRED_TYPE`
  - `SPEC_MISMATCH`
  - `ASSET_NOT_ASSIGNABLE`
  - `AI_UNAVAILABLE`
  - `MANUAL_REVIEW_REQUIRED`
- [ ] Fallback code evaluation order is deterministic and documented.
- [ ] Team can manually override assignment.

### US-E11-005: Visibility and auditability
**As an** admin,  
**I want** profile changes and profile-based assignments to be traceable,  
**So that** operations remain compliant and explainable.

**Acceptance Criteria:**
- [ ] Profile create/update/delete and manager changes are audit events.
- [ ] Auto-assignment events include profile and rule identifiers.
- [ ] History can be viewed in relevant detail screens (request/asset).

---

## Domain & Data (High-Level)

- `Department manager`: single FK relation `department.manager_user_id` to a user in the same company.
- `EquipmentProfile`: `id`, `company_id`, `department_id`, `role`, `is_active`, timestamps.
- `EquipmentProfileItem`: one-to-many profile entries with required `asset_type`, optional preferred fields/spec constraints, optional quantity.
- `CompanyAssignmentAIConfig`: `company_id`, `provider` (`OPENAI`|`GROQ`), `prompt_template`, optional `model`, timestamps.
- Assignment metadata in request/asset events to indicate profile-driven decisions.

---

## Technical Constraints

- Multi-tenant boundaries are mandatory for all read/write paths.
- Existing role hierarchy must remain valid (`super_admin > admin > technician > employee`).
- Deterministic candidate filtering before AI tie-break step.
- AI tie-break must be auditable (store provider/model/prompt version + decision rationale).
- No destructive reassignment without explicit user action/confirmation.
- Keep query performance acceptable for profile matching (indexing and filtered queries).

---

## Definition of Done

- [ ] Backend supports manager assignment and profile CRUD with proper authorization.
- [ ] Auto-assignment logic implemented with explainable fallback reasons and AI tie-break support (`OPENAI`/`GROQ`).
- [ ] Frontend provides manager/profile management and assignment visibility.
- [ ] Frontend provides company-level AI prompt/provider settings for assignment.
- [ ] Profile-based events appear in request/asset history.
- [ ] Unit + integration tests cover happy path and permission/isolation failures.
- [ ] Documentation and API contracts updated.
