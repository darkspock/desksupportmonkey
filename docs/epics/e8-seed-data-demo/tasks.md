# E8: Seed Data & Demo — Tasks

| Phase | Tasks | Complexity |
|-------|-------|------------|
| F0: Seed Script | 1 | High |
| F1: Makefile Targets | 1 | Low |
| F2: Demo Walkthrough | 1 | Low |
| **Total** | **3** | |

---

## F0: Seed Script

### T1: Create `scripts/seed_demo_data.py` ✅

**File:** `scripts/seed_demo_data.py`
**Complexity:** High

**Description:**
Create a standalone Python script that populates the database with realistic demo data. The script should:

1. Clear existing demo data (delete all rows from all tables in reverse FK order)
2. Create 3 companies with email domains
3. Create 1 super admin user
4. Per company: create departments, users (admin, technicians, employees), assets, service requests with comments/notes/events, notifications, reports
5. Use proper ULID IDs and maintain FK integrity
6. Print summary of created records

**Data Plan:**
- Companies: TechCorp (techcorp.com), FinanceHub (financehub.com), HealthCare Plus (healthcareplus.com)
- Super admin: admin@desksupportmonkey.com
- Users per company: 1 admin, 2 technicians, 5 employees
- Departments per company: 4 (Engineering, Sales, HR, IT)
- Assets per company: ~18 (mix of laptop, monitor, keyboard, mouse, headset, docking_station)
- Requests per company: ~12 (mix of all statuses and types)
- Notifications per user: 2-5
- Reports per company: 3 (one per type)

**Acceptance Criteria:**
- [x] Script runs without errors on a fresh database (after migrations)
- [x] Script is idempotent (can run multiple times safely)
- [x] All foreign key relationships are valid
- [x] Data covers all enum values (asset types, request statuses, priorities, etc.)
- [x] Date ranges span last 90 days for realistic analytics

---

## F1: Makefile Targets

### T2: Add `make seed` and `make demo-reset` ✅

**File:** `Makefile`
**Complexity:** Low

**Description:**
- `make seed` — runs the seed script with proper PYTHONPATH
- `make demo-reset` — drops and recreates all tables, then seeds

**Acceptance Criteria:**
- [x] `make seed` populates demo data
- [x] `make demo-reset` does a clean reset + seed

---

## F2: Demo Walkthrough

### T3: Create demo walkthrough documentation ✅

**File:** `docs/demo-walkthrough.md`
**Complexity:** Low

**Description:**
Document how to start the demo and explore features per role.

**Acceptance Criteria:**
- [x] Quick start instructions (docker, migrate, seed, start)
- [x] Login credentials for each role
- [x] Feature tour per role (employee, technician, admin, super admin)
