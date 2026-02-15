# Feature F0: Company CRUD + Email Domains

**Epic:** E1 - Company Management
**Type:** Feature
**Status:** Pending
**Created:** 2026-02-15
**Dependencies:** E0 (Foundation)

---

## Scope

This feature delivers full company lifecycle management for super admins, including:
- Company CRUD (create, read, update)
- Email domain management (add/remove domains per company)
- Real domain matching replacing the E0 stub
- Initial admin assignment on company creation

**User Stories Covered:** US-E1-001, US-E1-002, US-E1-006

---

## Requirements

### R1: Create Company
- `POST /api/v1/companies` creates a company with name and email domains
- Request body: `{ name: string, email_domains: string[], admin_email?: string }`
- Company is created in `active` status by default
- Company name is required and must be unique (case-insensitive)
- At least one email domain is required on creation
- Only `super_admin` role can access
- Returns created company with domains

### R2: List Companies
- `GET /api/v1/companies` lists all companies with pagination
- Query params: `page` (default 1), `page_size` (default 20), `search` (optional, filters by name)
- Only `super_admin` role can access
- Returns list with pagination metadata

### R3: Get Company Detail
- `GET /api/v1/companies/{id}` returns company details
- Includes: name, status, email domains, user count, department count, timestamps
- Only `super_admin` role can access
- Returns 404 if not found

### R4: Update Company
- `PUT /api/v1/companies/{id}` updates company name and email domains
- Can add/remove email domains (full replacement of domain list)
- Validates name uniqueness on update
- Validates email domain uniqueness on update (not just creation)
- Only `super_admin` role can access
- Returns 404 if not found, 409 if name/domain conflict

### R5: Email Domain Uniqueness
- Email domains are unique across the entire platform
- No two companies can share the same domain
- Domain is stored lowercase and trimmed
- Validation on both create and update

### R6: Real Domain Matching (Replace E0 Stub)
- `CompanyLookupService` queries `company_email_domains` table instead of returning first active company
- Extracts domain from email, looks up in `company_email_domains`
- If domain not found → returns None (auth flow returns 403)
- If domain found but company not active → returns None (auth flow returns 403)

### R7: Initial Admin Assignment
- `POST /api/v1/companies` optionally accepts `admin_email` field
- If provided, creates a User with `admin` role in the new company
- If user with that email already exists → 409 "User already exists"
- The initial admin receives a magic link email to set up their account
- If not provided, company is created without an admin

---

## Entities

### CompanyEmailDomain (NEW)

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `company_id` | ULID | FK to companies.id, NOT NULL, indexed |
| `domain` | String(255) | UNIQUE across platform, NOT NULL, indexed, lowercase |
| `created_at` | DateTime | Auto |

### Company (EXTEND)

| Field | Type | Notes |
|---|---|---|
| `status` | String(20) | `active`, `suspended`, `deactivated`. Default `active`. Added in E1 |

Note: `is_active` remains as backward-compat derived field. In F0 we add the `status` column. In F1 we add the status management logic.

---

## Error Responses

| Scenario | Status | Detail |
|---|---|---|
| Company name already exists | 409 | "Company with this name already exists" |
| Domain already taken | 409 | "Domain '{domain}' is already associated with another company" |
| Admin email user already exists | 409 | "User with this email already exists" |
| Company not found | 404 | "Company not found" |
| Not super_admin | 403 | "Insufficient permissions" |

---

## Acceptance Criteria

- [ ] Super admin can create a company with name + domains via POST
- [ ] Super admin can list companies with pagination via GET
- [ ] Super admin can view company detail with user/department counts via GET /{id}
- [ ] Super admin can update company name and domains via PUT
- [ ] Company name uniqueness enforced (case-insensitive)
- [ ] Email domain uniqueness enforced across platform
- [ ] CompanyLookupService uses real domain matching (E0 stub replaced)
- [ ] Magic link flow works with real domain matching
- [ ] Initial admin can be assigned on company creation
- [ ] Initial admin receives magic link email
- [ ] Non-super-admin users get 403 on all endpoints
- [ ] All endpoints return standard response format (SuccessResponse/ErrorResponse)
