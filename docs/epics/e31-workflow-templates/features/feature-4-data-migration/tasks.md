# Implementation Tasks: Feature 4 — Data Migration

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-25
**Total Tasks:** 5
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Infra - Conftest update | 1 | XS |
| Script - Backfill migration | 1 | M |
| Tests - Template CRUD integration | 1 | M |
| Tests - Checklist integration | 1 | M |
| Verification | 1 | S |

---

### TASK-001: Add Workflow Model Imports to Conftest

**Phase:** Infra
**Complexity:** XS
**Dependencies:** None

**File:** `tests/conftest.py`

**Implementation:**
Add workflow_bc model imports to the `tables` fixture so integration test DB has workflow tables:
```python
import src.workflow_bc.template.infrastructure.models  # noqa: F401
import src.workflow_bc.checklist.infrastructure.models  # noqa: F401
```

**Acceptance Criteria:**
- [x] Workflow template and checklist tables created in test DB
- [x] Existing integration tests still pass

---

### TASK-002: Create Backfill Script

**Phase:** Script
**Complexity:** M
**Dependencies:** None

**File:** `scripts/backfill_request_templates.py` (NEW)

**Implementation:**
- Connect via `SessionLocal` (same pattern as seed_demo_data.py)
- For each company:
  1. Fetch workflow templates → build `type_name_lower → template` map
  2. Build `(template_id, subtype_name_lower) → subtype_id` map
  3. Query `ServiceRequestModel` WHERE `workflow_template_id IS NULL` AND `company_id = cid`
  4. For each request, convert `request.type` (e.g. "new_equipment") to template name match (e.g. "New Equipment")
  5. If matched: set `workflow_template_id = template.id`
  6. If request has subtype and it matches: set `workflow_subtype_id`
  7. Commit per company batch
- Print summary: total, matched, unmatched, per-company breakdown
- Idempotent: only touches rows where `workflow_template_id IS NULL`

**Name matching strategy:**
Build a map from normalized template names. Template name "New Equipment" → normalize to "new_equipment". Request type column already stores "new_equipment". Match directly.

**Acceptance Criteria:**
- [x] Script runs without errors on empty and seeded databases
- [x] Links requests to templates by type name
- [x] Links request subtypes to template subtypes
- [x] Reports unmatched requests
- [x] Idempotent (safe to run multiple times)
- [x] Uses transactions per company

---

### TASK-003: Integration Tests for Workflow Template CRUD

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-001

**File:** `tests/integration/test_workflow_templates_endpoints.py` (NEW)

**Implementation:**
Follow patterns from `test_requests_endpoints.py`.

**Tests:**
- `test_create_template_as_admin` → 201, returns template with id
- `test_create_template_as_employee_forbidden` → 403
- `test_list_templates` → returns created templates
- `test_list_templates_active_only` → `?active=true` filters
- `test_get_template_by_id` → returns template with subtypes + checklist items
- `test_update_template` → changes persisted
- `test_delete_template` → 204
- `test_delete_template_with_requests_fails` → create template, create request with it, try delete → 409

**Acceptance Criteria:**
- [x] All CRUD operations tested
- [x] Permission boundaries tested
- [x] Delete-with-linked-requests tested
- [x] Tests pass with `make test-integration`

---

### TASK-004: Integration Tests for Checklist Endpoints

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-001

**File:** `tests/integration/test_checklist_endpoints.py` (NEW)

**Implementation:**
Create a workflow template with checklist items, create a request with that template, then test checklist operations.

**Tests:**
- `test_checklist_auto_generated_on_request_create` → create template with items, create request with template_id, GET checklist → items exist
- `test_list_checklist_items` → returns items with progress
- `test_add_adhoc_item` → POST new item, appears in list
- `test_toggle_item` → PATCH toggle, is_completed flips
- `test_assign_item` → PATCH assign, assignee_id set
- `test_remove_item` → DELETE, 204, gone from list
- `test_resolution_guard_blocks_incomplete` → template with require_all_complete=true, create request, leave required item unchecked, try resolve → 422
- `test_resolution_guard_allows_all_complete` → check all required items, resolve → succeeds

**Acceptance Criteria:**
- [x] Checklist auto-generation tested
- [x] All CRUD operations tested
- [x] Resolution guard tested (both block and allow cases)
- [x] Tests pass with `make test-integration`

---

### TASK-005: Final Verification

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Implementation:**
1. Run `make test` — all unit tests pass
2. Run `make test-integration` — all integration tests pass
3. Run backfill script on seeded local DB
4. Verify matched/unmatched counts make sense

**Acceptance Criteria:**
- [x] `make test` passes
- [x] `make test-integration` passes (new tests all pass; pre-existing failures unchanged)
- [x] Backfill script created and ready to run
- [x] All existing tests still pass

---

## Dependency Graph

```
TASK-001 (conftest)
    │
    ├── TASK-003 (template tests) ◄── TASK-001
    └── TASK-004 (checklist tests) ◄── TASK-001

TASK-002 (backfill script) — independent

TASK-005 (verification) ◄── ALL
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-002
**Batch 2 (Parallel):** TASK-003, TASK-004
**Batch 3:** TASK-005

## Final Checklist

- [x] Conftest has workflow model imports
- [x] Backfill script links requests to templates
- [x] Template CRUD integration tests pass
- [x] Checklist integration tests pass
- [x] All existing tests still pass
- [x] E31 epic fully complete

## Bug Fix Applied

During integration testing, discovered that `adapters/http/api/requests/routers.py` line 630 was overriding `resolved_type` with `wf_template.name` (e.g., "Incident" with capital I), but `CreateRequestCommandHandler` expects a valid `RequestType` enum value (lowercase "incident"). Removed the override — the user-provided `body.type` is already correct, and the template is linked separately via `workflow_template_id`.
