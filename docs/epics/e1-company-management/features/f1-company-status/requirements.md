# Feature F1: Company Status + Auth Integration

**Epic:** E1 - Company Management
**Type:** Feature
**Status:** Pending
**Created:** 2026-02-15
**Dependencies:** F0 (Company CRUD + Email Domains)

---

## Scope

This feature adds company lifecycle management (status transitions) and integrates company status checks into the auth flow so that suspended/deactivated companies are blocked.

**User Stories Covered:** US-E1-003

---

## Requirements

### R1: Company Status Endpoint
- `PATCH /api/v1/companies/{id}/status` changes company status
- Request body: `{ status: "active" | "suspended" | "deactivated" }`
- Only `super_admin` role can access
- Returns updated company

### R2: Valid Status Transitions
- `active` → `suspended` (reversible)
- `active` → `deactivated` (permanent)
- `suspended` → `active` (reactivation)
- `suspended` → `deactivated` (permanent)
- `deactivated` → (none — terminal state, no transitions allowed)
- Invalid transitions return 409 with descriptive message

### R3: is_active Sync
- When status changes, `is_active` is updated:
  - `active` → `is_active = True`
  - `suspended` → `is_active = False`
  - `deactivated` → `is_active = False`

### R4: Auth Flow - Company Status Check on Login
- During magic link verification (`VerifyMagicLinkCommand`):
  - After finding company by domain, check company status
  - If company is `suspended` or `deactivated` → 403 "Company access is currently restricted"
  - This applies to both new users (first login) and existing users

### R5: Auth Flow - Company Status Check on Every Request
- In `get_current_user` dependency:
  - After loading user, query company status
  - If company is `suspended` or `deactivated` → 403 "Company access is currently restricted"
  - This ensures already-issued JWTs are blocked when company is suspended
  - Super admin users (no company) are not affected

### R6: Status Change Logging
- All status changes are logged at INFO level
- Log includes: company_id, old_status, new_status, changed_by (user_id)

---

## Error Responses

| Scenario | Status | Detail |
|---|---|---|
| Invalid transition (e.g., deactivated → active) | 409 | "Cannot transition from '{current}' to '{target}'" |
| Same status (e.g., active → active) | 409 | "Company is already {status}" |
| Company not found | 404 | "Company not found" |
| Company suspended/deactivated (login) | 403 | "Company access is currently restricted" |
| Company suspended/deactivated (request) | 403 | "Company access is currently restricted" |
| Not super_admin | 403 | "Insufficient permissions" |

---

## Acceptance Criteria

- [ ] Super admin can change company status via PATCH endpoint
- [ ] Only valid transitions are allowed (state machine enforced)
- [ ] Deactivated status is terminal (no transitions out)
- [ ] is_active stays in sync with status
- [ ] Suspended/deactivated companies block magic link login (403)
- [ ] Suspended/deactivated companies block authenticated requests (403)
- [ ] Super admin users are not affected by company status checks
- [ ] Status changes are logged
- [ ] Existing auth tests continue to pass (regression)
