# Feature 2: Checklist Runtime

**Parent Epic:** [../../requirement.md](../../requirement.md)
**Feature #:** 2
**Dependencies:** Feature 0
**Complexity:** M

## Scope

### Included
- **Checklist generation on request creation**: After `CreateRequestCommand` succeeds, call `GenerateChecklistCommandHandler` to stamp checklist items from the matched template.
- **Resolution guard**: Before status change to "resolved", check if any `request_checklist_item` has `require_all_complete=true` and `is_required=true` and `is_completed=false`. If so, return HTTP 422.
- **RequestDetailPage checklist card**: Progress bar, checkbox items with toggle/remove, inline add item input, resolution warning.
- **Checklist API**: GET list, POST add, PATCH toggle, PATCH assign, DELETE remove (from Feature 0 routes).

### Excluded (in other features)
- Template CRUD (Feature 0 — already done)
- NewRequestPage dynamic types (Feature 1)
- RequestQueuePage (Feature 3)

## User Value

When a request is created from a template, its checklist items are automatically generated. Technicians can check off items as they complete them, assign items to specific users, and add ad-hoc items. If the template requires all items complete, the request cannot be resolved until they are.

## Acceptance Criteria

- [x] Checklist items generated from template on request creation
- [x] Resolution guard blocks resolving with incomplete required items (HTTP 422)
- [x] RequestDetailPage shows checklist card with progress bar
- [x] Technician can toggle items (check/uncheck)
- [x] Technician can add ad-hoc items
- [x] Technician can remove items
- [x] Resolution warning displayed when required items incomplete
- [x] Checklist data fetched via `GET /requests/{id}/checklist`
- [x] Unit tests for all checklist commands

## Technical Scope

### Entities (used from dependencies)
- RequestChecklistItem (Feature 0)
- WorkflowTemplate (Feature 0)

### Key Components
- `adapters/http/api/requests/routers.py` — Checklist generation hook + resolution guard
- `web/app/src/pages/technician/RequestDetailPage.tsx` — Checklist card UI
- `adapters/http/api/checklist/routers.py` — Checklist endpoints (from F0)
