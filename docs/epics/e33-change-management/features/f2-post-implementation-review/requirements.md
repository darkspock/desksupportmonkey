# Feature: Post-Implementation Review

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** F0
**Complexity:** S

## Scope

### Included

- PostImplementationReview entity: outcome (successful/partial/failed), issues_found, lessons_learned, follow_up_actions, created_by, created_at
- PIR outcome enum: successful, partial, failed
- One PIR per change request (unique constraint on change_request_id)
- Create PIR command: POST /{change_id}/pir
- Get PIR query: included in change detail response
- PIR enforcement: emergency changes cannot be closed without a PIR (422 if attempting IMPLEMENTED → CLOSED without PIR for emergency type)
- ChangeEvent entry for pir_added
- PIR section on change detail page
- Alembic migration for post_implementation_reviews table

### Excluded (in other features)

- Change Request CRUD and state machine (F0)
- Asset linking (F1)
- Change dashboard (F3)
- PIR editing after creation (out of scope — create once, immutable)

## User Value

When this feature is complete, admins can record the outcome of a completed change — whether it was successful, what issues were found, lessons learned, and follow-up actions needed. For emergency changes, this review is mandatory before closing, ensuring DORA compliance with post-change review requirements.

## Acceptance Criteria

- [ ] Can create a PIR for a change in IMPLEMENTED status: outcome, issues_found, lessons_learned, follow_up_actions
- [ ] Only one PIR per change (409 if already exists)
- [ ] PIR creation requires admin role
- [ ] Emergency type changes cannot transition IMPLEMENTED → CLOSED without a PIR (422)
- [ ] Standard and normal type changes can close without PIR (PIR optional)
- [ ] ChangeEvent recorded when PIR is added
- [ ] Change detail page shows PIR section (outcome badge, issues, lessons, follow-up)
- [ ] PIR section hidden if no PIR exists (show "Add Review" button for IMPLEMENTED changes)
- [ ] i18n keys for PIR section and outcome enum
- [ ] Unit tests for create PIR command and close enforcement
- [ ] Integration tests for PIR endpoint and emergency close guard

## Technical Scope

### Entities (owned by this feature)

- **PostImplementationReview** — sub-entity linked to ChangeRequest

### Entities (used from dependencies)

- **ChangeRequest** (F0) — parent entity, close command modified
- **ChangeEvent** (F0) — audit trail

### Key Components

- `src/change_bc/change_request/domain/entities.py` — add PostImplementationReview dataclass
- `src/change_bc/change_request/domain/enums.py` — add PIROutcome enum
- `src/change_bc/change_request/infrastructure/models.py` — add PostImplementationReviewModel
- `src/change_bc/change_request/domain/repository.py` — add PIR repository methods
- `src/change_bc/change_request/application/commands/create_pir.py`
- `src/change_bc/change_request/application/commands/close_change.py` — modify to enforce PIR for emergency
- `adapters/http/api/changes/routers.py` — add PIR endpoint
- `adapters/http/api/changes/schemas.py` — add PIR request/response schemas
- `alembic/versions/e33c1_*.py` — migration for post_implementation_reviews table

## Notes

- Follows the PostMortem pattern from incident_bc but simpler (no required fields beyond outcome)
- PIR is immutable after creation — no update/delete
- The close_change command (from F0) must be aware of PIR requirement. Design options: (a) F0's close command checks for PIR on emergency type from the start, returning a clear error; (b) F2 modifies the close command to add the check. Option (a) is cleaner — F0 can include the check with a simple "PIR not found" error, and F2 provides the entity and endpoint to create it.
