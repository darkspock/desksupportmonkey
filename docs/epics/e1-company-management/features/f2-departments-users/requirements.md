# Feature F2: Departments + User Management

**Epic:** E1 - Company Management
**Type:** Feature
**Status:** Pending
**Created:** 2026-02-15
**Dependencies:** F0 (Company CRUD + Email Domains)

---

## Scope

This feature delivers department management and user management for company admins. It enables full organizational structure within a company.

**User Stories Covered:** US-E1-004, US-E1-005

---

## Requirements

### Department Management

#### R1: Create Department
- `POST /api/v1/departments` creates a department in the admin's company
- Request body: `{ name: string }`
- Department is scoped to admin's company_id (from tenant context)
- Department name must be unique within the company
- Only `admin` role (or above) can access

#### R2: List Departments
- `GET /api/v1/departments` lists departments in the admin's company
- Tenant-scoped: only shows departments for current user's company
- Query params: `page` (default 1), `page_size` (default 20), `include_inactive` (default false)
- Only `admin` role (or above) can access

#### R3: Get Department Detail
- `GET /api/v1/departments/{id}` returns department with user count
- Must belong to admin's company (tenant isolation)
- Returns 404 if not found or wrong company

#### R4: Update Department
- `PUT /api/v1/departments/{id}` updates department name
- Validates name uniqueness within company
- Must belong to admin's company
- Only `admin` role (or above) can access

#### R5: Delete Department (Soft)
- `DELETE /api/v1/departments/{id}` soft-deletes (sets is_active=false)
- Returns 409 if users are assigned to the department
- Admin must reassign users first
- Must belong to admin's company

### User Management

#### R6: List Users
- `GET /api/v1/users` lists users in admin's company with pagination
- Tenant-scoped: only shows users for current user's company
- Query params: `page`, `page_size`, `role` (filter), `is_active` (filter), `department_id` (filter), `search` (email/name)
- Only `admin` role (or above) can access

#### R7: Get User Detail
- `GET /api/v1/users/{id}` returns user details
- Must belong to admin's company (tenant isolation)
- Returns 404 if not found or wrong company

#### R8: Change User Role
- `PATCH /api/v1/users/{id}/role` changes user's role
- Request body: `{ role: "admin" | "technician" | "employee" }`
- Admin cannot promote to `super_admin`
- Admin cannot change their own role
- Must belong to admin's company

#### R9: Deactivate User
- `PATCH /api/v1/users/{id}/deactivate` sets is_active=false
- Admin cannot deactivate themselves
- Must belong to admin's company
- Deactivated users cannot log in

#### R10: Activate User
- `PATCH /api/v1/users/{id}/activate` sets is_active=true
- Must belong to admin's company

#### R11: Assign User to Department
- `PATCH /api/v1/users/{id}/department` assigns user to a department
- Request body: `{ department_id: string | null }` (null to unassign)
- Department must belong to same company
- Department must be active
- Must belong to admin's company

### User Model Extension

#### R12: Add department_id to User
- Add `department_id` column to users table (nullable FK to departments)
- Alembic migration required

---

## Entities

### Department (NEW)

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `company_id` | ULID | FK to companies.id, NOT NULL, indexed |
| `name` | String(255) | NOT NULL |
| `is_active` | Boolean | Default true (soft delete) |
| `created_at` | DateTime | Auto |
| `updated_at` | DateTime | Auto |

**Constraint:** UNIQUE(company_id, name) — department names unique per company

### User (EXTEND)

| Field | Type | Notes |
|---|---|---|
| `department_id` | ULID | FK to departments.id, nullable, indexed. Added in E1-F2 |

---

## Error Responses

| Scenario | Status | Detail |
|---|---|---|
| Department name exists in company | 409 | "Department with this name already exists" |
| Delete department with users | 409 | "Cannot delete department with assigned users. Reassign users first" |
| Department not found / wrong company | 404 | "Department not found" |
| User not found / wrong company | 404 | "User not found" |
| Cannot promote to super_admin | 403 | "Cannot assign super_admin role" |
| Cannot change own role | 403 | "Cannot change your own role" |
| Cannot deactivate self | 403 | "Cannot deactivate your own account" |
| Department not active (for assignment) | 409 | "Cannot assign to inactive department" |
| Department wrong company (for assignment) | 404 | "Department not found" |
| Not admin | 403 | "Insufficient permissions" |

---

## Acceptance Criteria

- [ ] Admin can create departments in their company
- [ ] Admin can list departments (tenant-scoped)
- [ ] Admin can view department detail with user count
- [ ] Admin can update department name
- [ ] Admin can soft-delete department (blocked if users assigned)
- [ ] Department names unique per company
- [ ] Admin can list users with filters (role, is_active, department, search)
- [ ] Admin can view user detail
- [ ] Admin can change user role (not to super_admin)
- [ ] Admin cannot change their own role
- [ ] Admin can deactivate/activate users
- [ ] Admin cannot deactivate themselves
- [ ] Admin can assign users to departments
- [ ] All endpoints respect tenant isolation (company_id scoping)
- [ ] All endpoints require admin role minimum
- [ ] department_id added to users table via migration
