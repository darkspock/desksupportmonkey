# Epic E1: Company Management

**Type:** Epic
**Status:** Pending Validation
**Created:** 2026-02-15
**Priority:** Critical
**Depends on:** E0 (Foundation)

---

## Business Alignment

**Objective:** Enable multi-company platform operation by allowing super admins to create and manage companies, and company admins to manage their users and departments.

This epic transforms the platform from a single-use application into a true multi-tenant SaaS. Without E1, no business features (E2-E6) can function because there are no properly configured companies, no email domain matching, and no user management.

---

## Problem Statement

### Current Situation
E0 delivered authentication, RBAC, and multi-tenancy infrastructure, but:
- Companies can only be created manually in the database
- Email domain matching is a stub (returns first active company)
- No user management (no listing, role changes, or deactivation)
- No department structure
- No company lifecycle management (activate, suspend, deactivate)

### What E1 Delivers
A fully operational company management module where:
- Super admins create and configure companies with email domains
- Company admins manage their users and departments
- Email domain matching works properly for magic link authentication
- User auto-creation on first login maps to the correct company via email domain

---

## Proposed Solution

### US-E1-001: Company CRUD (Super Admin)
**As a** super admin
**I want** to create, view, update, and manage companies
**So that** new organizations can be onboarded to the platform

**Acceptance Criteria:**
- [ ] `POST /api/v1/companies` creates a company with name and email domains
- [ ] `GET /api/v1/companies` lists all companies with pagination
- [ ] `GET /api/v1/companies/{id}` returns company details with domains and user count
- [ ] `PUT /api/v1/companies/{id}` updates company name and email domains
- [ ] Only super_admin role can access these endpoints
- [ ] Company is created in `active` status by default
- [ ] Company name is required and must be unique
- [ ] At least one email domain is required on creation

### US-E1-002: Company Email Domains
**As a** super admin
**I want** to configure which email domains belong to each company
**So that** users logging in with those domains are automatically associated with the correct company

**Acceptance Criteria:**
- [ ] Each company has one or more email domains (e.g., "acme.com", "acme.co.uk")
- [ ] Email domains are unique across the platform (no two companies share a domain)
- [ ] `POST /api/v1/auth/magic-link` uses email domain to find the matching company
- [ ] If email domain matches no company, returns 403 "Only corporate email addresses are allowed"
- [ ] If email domain matches a suspended/deactivated company, returns 403 "Company access is currently restricted"
- [ ] Super admin can add/remove domains from a company via PUT

### US-E1-003: Company Status Management
**As a** super admin
**I want** to change company status (active, suspended, deactivated)
**So that** I can control access for companies that are offboarding or in violation

**Acceptance Criteria:**
- [ ] `PATCH /api/v1/companies/{id}/status` changes company status
- [ ] Valid statuses: `active`, `suspended`, `deactivated`
- [ ] Valid transitions: active -> suspended, active -> deactivated, suspended -> active, suspended -> deactivated
- [ ] Cannot transition from `deactivated` back to `active` (permanent)
- [ ] When company is suspended: existing users can't log in (magic link returns 403), but data is preserved
- [ ] When company is deactivated: same as suspended but irreversible
- [ ] Only super_admin role can change company status

### US-E1-004: Department CRUD (Company Admin)
**As a** company admin
**I want** to create and manage departments within my company
**So that** users and assets can be organized by department

**Acceptance Criteria:**
- [ ] `POST /api/v1/departments` creates a department with name
- [ ] `GET /api/v1/departments` lists departments in the admin's company (tenant-scoped)
- [ ] `GET /api/v1/departments/{id}` returns department detail with user count
- [ ] `PUT /api/v1/departments/{id}` updates department name
- [ ] `DELETE /api/v1/departments/{id}` soft-deletes if no users assigned, else returns 409
- [ ] Department name must be unique within a company
- [ ] Only admin role (or above) can manage departments
- [ ] Departments are scoped by company_id (multi-tenancy)

### US-E1-005: User Management (Company Admin)
**As a** company admin
**I want** to view and manage users in my company
**So that** I can control access and assign roles

**Acceptance Criteria:**
- [ ] `GET /api/v1/users` lists users in the admin's company with pagination and filters
- [ ] `GET /api/v1/users/{id}` returns user details
- [ ] `PATCH /api/v1/users/{id}/role` changes a user's role (admin, technician, employee)
- [ ] `PATCH /api/v1/users/{id}/deactivate` deactivates a user (sets is_active=false)
- [ ] `PATCH /api/v1/users/{id}/activate` reactivates a user
- [ ] `PATCH /api/v1/users/{id}/department` assigns user to a department
- [ ] Admin cannot promote beyond their own role level (admin can't create super_admin)
- [ ] Admin cannot deactivate themselves
- [ ] Deactivated users cannot log in (magic link verify returns 403)
- [ ] Only admin role (or above) can manage users
- [ ] Users are scoped by company_id (multi-tenancy)
- [ ] Filters: role, is_active, department_id, search (email/name)

### US-E1-006: Super Admin Assigns Initial Company Admin
**As a** super admin
**I want** to assign the initial admin user when creating a company
**So that** the company has someone who can manage it from day one

**Acceptance Criteria:**
- [ ] `POST /api/v1/companies` optionally accepts `admin_email` field
- [ ] If `admin_email` is provided, creates a user with `admin` role in the new company
- [ ] If user with that email already exists, returns 409 "User already exists"
- [ ] The initial admin receives a magic link email to set up their account
- [ ] If `admin_email` is not provided, company is created without an admin (can be assigned later)

---

## Entities

| Entity | Description | New in E1? |
|---|---|---|
| `Company` | Extend with status, email_domains relationship | Extend |
| `CompanyEmailDomain` | Email domain associated with a company | New |
| `Department` | Department within a company | New |
| `User` | Extend with department_id | Extend |

### Company Entity (extended)

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK (from E0) |
| `name` | string(255) | Unique, NOT NULL (from E0) |
| `status` | enum | `active`, `suspended`, `deactivated`. Default `active` |
| `is_active` | boolean | Derived from status (active=true, else false). Keep for backward compat |
| `created_at` | datetime | Auto (from E0) |
| `updated_at` | datetime | Auto (from E0) |

### CompanyEmailDomain Entity (new)

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `company_id` | ULID | FK to Company, NOT NULL, indexed |
| `domain` | string(255) | Unique across platform, NOT NULL, indexed |
| `created_at` | datetime | Auto |

### Department Entity (new)

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `company_id` | ULID | FK to Company, NOT NULL, indexed |
| `name` | string(255) | NOT NULL |
| `is_active` | boolean | Default true (soft delete) |
| `created_at` | datetime | Auto |
| `updated_at` | datetime | Auto |

**Constraint:** UNIQUE(company_id, name) — department names unique per company

### User Entity (extended)

| Field | Type | Notes |
|---|---|---|
| `department_id` | ULID | FK to Department, nullable, indexed. Added in E1 |

All other User fields remain from E0.

---

## Use Cases

### UC-E1-001: Create Company
**Actor:** Super Admin
**Preconditions:** Authenticated as super_admin

**Main Flow:**
1. Super admin provides company name, email domains, and optional admin_email
2. System validates name is unique
3. System validates email domains are unique across platform
4. System creates Company record (status=active)
5. System creates CompanyEmailDomain records for each domain
6. If admin_email provided, system creates User with admin role
7. If admin_email provided, system sends magic link to admin
8. Returns created company with domains

**Alternative Flows:**
- A1: Company name already exists -> 409 "Company with this name already exists"
- A2: Email domain already taken -> 409 "Domain '{domain}' is already associated with another company"
- A3: admin_email user already exists -> 409 "User with this email already exists"

### UC-E1-002: Suspend Company
**Actor:** Super Admin
**Preconditions:** Company status is `active`

**Main Flow:**
1. Super admin sends PATCH with status=suspended
2. System validates current status is active
3. System updates status to suspended
4. All users in company are blocked from logging in (checked at magic link verify time)

**Alternative Flows:**
- A1: Company already suspended -> 409 "Company is already suspended"
- A2: Company deactivated -> 409 "Cannot change status of a deactivated company"

### UC-E1-003: Change User Role
**Actor:** Company Admin
**Preconditions:** Authenticated as admin within the same company

**Main Flow:**
1. Admin sends PATCH with new role for a user
2. System validates admin has permission (cannot promote to super_admin)
3. System validates target user belongs to same company
4. System updates user role
5. Returns updated user

**Alternative Flows:**
- A1: Target user is in different company -> 404 (tenant isolation)
- A2: Admin tries to set super_admin -> 403 "Cannot assign super_admin role"
- A3: Admin tries to change their own role -> 403 "Cannot change your own role"

### UC-E1-004: Magic Link with Domain Matching (Updated)
**Actor:** Any user
**Preconditions:** None

**Main Flow (updated from E0):**
1. User provides email
2. System extracts domain from email
3. System queries CompanyEmailDomain table for matching domain
4. If found and company is active, proceeds with magic link creation
5. On first login (no user exists), creates user with employee role in matching company

**Alternative Flows:**
- A1: Domain not found -> 403 "Only corporate email addresses are allowed"
- A2: Domain found but company suspended/deactivated -> 403 "Company access is currently restricted"

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `CompanyLookupService` | Must be updated to use CompanyEmailDomain table | Replace stub with real domain matching |
| `CompanyModel` | Add status column | Alembic migration |
| `UserModel` | Add department_id column | Alembic migration |
| Magic link flow | Add company status check during verify | Update VerifyMagicLink handler |
| models_registry.py | Add new models | Update imports |

---

## Bounded Context

This epic adds the `company_bc` domain and application layers, and extends `auth_bc`:

```
src/company_bc/
├── company/
│   ├── domain/
│   │   ├── entities.py         # Company entity with status
│   │   ├── enums.py            # CompanyStatus enum
│   │   └── repository.py       # CompanyRepositoryInterface
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_company.py
│   │   │   └── update_company_status.py
│   │   └── queries/
│   │       ├── list_companies.py
│   │       └── get_company.py
│   └── infrastructure/
│       ├── models.py           # CompanyModel (extend), CompanyEmailDomainModel
│       └── repository.py       # CompanyRepository
├── department/
│   ├── domain/
│   │   ├── entities.py
│   │   └── repository.py
│   ├── application/
│   │   ├── commands/
│   │   │   └── crud.py
│   │   └── queries/
│   │       └── list_departments.py
│   └── infrastructure/
│       ├── models.py           # DepartmentModel
│       └── repository.py

adapters/http/api/
├── companies/
│   ├── routers.py              # Company CRUD (super admin)
│   └── schemas.py
├── departments/
│   ├── routers.py              # Department CRUD (admin)
│   └── schemas.py
├── users/
│   ├── routers.py              # User management (admin)
│   └── schemas.py
```

---

## Definition of Done

- [ ] Super admin can create a company with email domains via API
- [ ] Super admin can list, view, and update companies
- [ ] Super admin can change company status (active/suspended/deactivated)
- [ ] Magic link login uses CompanyEmailDomain table for domain matching
- [ ] Suspended/deactivated companies block user login
- [ ] Company admin can create and manage departments
- [ ] Company admin can list, view, and manage users (role changes, activate/deactivate)
- [ ] Department names unique per company
- [ ] Email domains unique across platform
- [ ] All endpoints respect RBAC (super_admin vs admin)
- [ ] All tenant-scoped queries filtered by company_id
- [ ] Alembic migration adds new tables and columns
- [ ] Unit tests for domain entities and business rules
- [ ] Integration tests for CRUD operations
- [ ] API tests for all endpoints (happy path + error cases)

---

## Time Constraints

**Deadline:** None
**Estimated complexity:** Large (6 user stories, 3 new entities, multiple CRUD endpoints)
**Note:** This is the most entity-heavy epic. Keep it clean and consistent because E2-E6 will follow the same patterns.

---

## Open Questions

1. **Company name uniqueness:** Should company names be globally unique, or just a display name? Recommend: globally unique to avoid confusion.
2. **Department soft delete:** When a department is deleted, what happens to users assigned to it? Recommend: set their department_id to NULL.
3. **Initial admin email:** Should sending the magic link to the initial admin be synchronous (during company creation) or async (Celery task)? Recommend: synchronous since it's a single email.
