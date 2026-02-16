# E7: Frontend - Requirements

**Date:** 2026-02-16
**Depends on:** E0-E6 (all backend APIs complete)
**Directory:** `web/app/`

---

## User Stories

### US-E7-001: Authentication
**As a** user, **I want** to log in with my corporate email via magic link **so that** I can access the platform without passwords.

### US-E7-002: Role-Based Navigation
**As a** user, **I want** to see only the sections relevant to my role **so that** the interface is focused and uncluttered.

### US-E7-003: Employee Portal
**As an** employee, **I want** to view my equipment, submit requests, track my requests, and manage notifications **so that** I can interact with IT support.

### US-E7-004: Technician Panel
**As a** technician, **I want** to manage the request queue, assign/resolve requests, and manage asset inventory **so that** I can fulfill IT support duties.

### US-E7-005: Admin Dashboard
**As an** admin, **I want** to see metrics, alerts, manage users/departments, and generate reports **so that** I can oversee IT operations.

### US-E7-006: Super Admin
**As a** super admin, **I want** to manage companies **so that** I can onboard and manage tenants.

### US-E7-007: Real-Time Updates
**As a** user, **I want** to receive real-time notifications **so that** I stay informed about request updates.

---

## Tech Stack

- React 18 + TypeScript
- Vite
- React Router v6
- TanStack Query (data fetching + caching)
- Tailwind CSS
- Recharts (dashboard charts)
- WebSocket (native API)

---

## API Surface

61 endpoints across 10 modules. All use envelope format `{ data, meta? }`.
Auth: Bearer JWT in Authorization header.
Pagination: `page` + `page_size` query params, response has `meta.total`.

---

## Role Hierarchy & Access

| Role | Sees |
|------|------|
| EMPLOYEE | My Equipment, My Requests, Submit Request, Notifications |
| TECHNICIAN | + Request Queue, Asset Inventory, Internal Notes |
| ADMIN | + Dashboard, Users, Departments, Reports |
| SUPER_ADMIN | + Company Management (no company_id) |
