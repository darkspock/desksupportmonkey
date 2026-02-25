# Solution Design: Feature 4 — Data Migration

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-25
**Bounded Context:** Cross-cutting (scripts + tests)

## Summary

Create a backfill script that links existing `service_requests` to their `workflow_templates` by matching `type` column values to template names. Also create integration tests for the workflow template CRUD and checklist endpoints.

## Architecture Decision

**Backfill approach: Direct SQL with repository pattern**

The script uses SQLAlchemy ORM queries to:
1. For each company, fetch all workflow templates (name → id map)
2. For each company, fetch all workflow subtypes (template_id + name → subtype_id map)
3. UPDATE `service_requests` rows where `type` matches a template name, setting `workflow_template_id`
4. UPDATE `service_requests` rows where `subtype` matches a subtype name within the matched template, setting `workflow_subtype_id`

This avoids raw SQL and leverages existing models. The script is idempotent — it only updates rows where `workflow_template_id IS NULL`.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ServiceRequestModel | `src/request_bc/request/infrastructure/models.py` | Yes | None |
| WorkflowTemplateModel | `src/workflow_bc/template/infrastructure/models.py` | Yes | None |
| WorkflowSubtypeModel | `src/workflow_bc/template/infrastructure/models.py` | Yes | None |
| seed_demo_data.py | `scripts/seed_demo_data.py` | Pattern reference | None |
| conftest.py | `tests/conftest.py` | Yes | Add workflow model imports |
| Checklist router | `adapters/http/api/checklist/routers.py` | Yes | None (testing it) |
| Template router | `adapters/http/api/workflow_templates/routers.py` | Yes | None (testing it) |

## Implementation Plan

### 1. Backfill Script

**File:** `scripts/backfill_request_templates.py` (NEW)

Logic:
```
For each company:
  1. Fetch templates → build name_lower → template map
  2. Fetch subtypes → build (template_id, name_lower) → subtype_id map
  3. Query requests WHERE workflow_template_id IS NULL
  4. For each request:
     - Match request.type (lowered/underscored→name) to template
     - If matched: set workflow_template_id
     - If request.subtype matches a subtype under that template: set workflow_subtype_id
  5. Commit per company
  6. Report: matched, unmatched, total
```

Name matching: template names are like "New Equipment", request types are like "new_equipment". Convert by replacing underscores with spaces and title-casing, or build a reverse map.

### 2. Integration Tests

**File:** `tests/integration/test_workflow_templates_endpoints.py` (NEW)

Tests:
- Create template (admin) → 201
- Create template (employee) → 403
- List templates → returns created templates
- Get template by ID → returns template with subtypes + items
- Update template → changes persisted
- Delete template → 204
- Delete template with linked requests → 422

**File:** `tests/integration/test_checklist_endpoints.py` (NEW)

Tests:
- Create request with template → checklist auto-generated
- List checklist items → returns generated items
- Add ad-hoc item → appears in list
- Toggle item → is_completed flips
- Assign item → assignee_id updated
- Remove item → 204, gone from list
- Resolution guard: resolve with incomplete required items → 422
- Resolution guard: resolve with all items complete → succeeds

### 3. Conftest Update

**File:** `tests/conftest.py`

Add workflow model imports to the `tables` fixture so integration tests can use workflow tables.

## Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `scripts/backfill_request_templates.py` | New | Migration script |
| `tests/integration/test_workflow_templates_endpoints.py` | New | Template CRUD tests |
| `tests/integration/test_checklist_endpoints.py` | New | Checklist endpoint tests |
| `tests/conftest.py` | Modify | Add workflow model imports |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Integration | Template CRUD endpoints | High |
| Integration | Checklist endpoints | High |
| Integration | Resolution guard | High |
| Manual | Run backfill on local DB | Medium |
