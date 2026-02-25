# Feature 4: Data Migration

**Parent Epic:** [../../requirement.md](../../requirement.md)
**Feature #:** 4
**Dependencies:** Feature 1
**Complexity:** S

## Scope

### Included
- **Backfill script**: For each company, match existing `service_requests.type` values to `workflow_templates.name` and UPDATE `workflow_template_id`.
- **Subtype backfill**: Match `service_requests.subtype` to `workflow_subtypes.name` and UPDATE `workflow_subtype_id`.
- **Verification**: Report on unmatched requests (type values that don't match any template).
- **Integration tests**: End-to-end tests for workflow template CRUD and checklist endpoints.

### Excluded (in other features)
- Template CRUD (Feature 0)
- Request creation flow (Feature 1)
- Checklist runtime (Feature 2)

## User Value

Existing requests are linked to their workflow templates, enabling template-based filtering, reporting, and checklist functionality on historical data. Integration tests ensure the full flow works end-to-end.

## Acceptance Criteria

- [ ] Backfill script links existing requests to templates by type name
- [ ] Subtype backfill links by subtype name
- [ ] Script reports unmatched requests
- [ ] Script is idempotent (safe to run multiple times)
- [ ] Integration tests for template CRUD endpoints (create, read, update, delete)
- [ ] Integration tests for checklist endpoints (list, add, toggle, assign, remove)
- [ ] Integration test for resolution guard
- [ ] All existing tests still pass

## Technical Scope

### Key Components
- `scripts/backfill_request_templates.py` — Data migration script (new)
- `tests/integration/test_workflow_templates_endpoints.py` — Integration tests (new)
- `tests/integration/test_checklist_endpoints.py` — Integration tests (new)

## Notes

- Run backfill in a transaction. Log every UPDATE for audit trail.
- The denormalized `type` and `subtype` columns remain unchanged — they are the historical record.
- After backfill verification, a future migration could make `workflow_template_id` NOT NULL, but that's optional and can be deferred.
