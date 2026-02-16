# DeskSupportMonkey — Demo Walkthrough

## Quick Start

```bash
# 1. Start infrastructure (PostgreSQL, Redis, Mailpit, MinIO)
make start-docker

# 2. Apply database migrations
make db-upgrade

# 3. Seed demo data
make seed

# 4. Start backend API + Celery worker
make start

# 5. Open frontend
cd web/app && npm run dev
```

**Services:**
| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| Mailpit (email) | http://localhost:8028 |
| MinIO Console | http://localhost:9001 (minioadmin/minioadmin) |

---

## Demo Login Credentials

Authentication uses **magic links**. Enter an email, check Mailpit for the link.

### Super Admin
| Role | Email |
|------|-------|
| Super Admin | admin@desksupportmonkey.com |

### TechCorp Inc
| Role | Email |
|------|-------|
| Admin | alice.smith@techcorp.com |
| Technician | bob.johnson@techcorp.com |
| Employee | dave.brown@techcorp.com |

### FinanceHub
| Role | Email |
|------|-------|
| Admin | iris.jackson@financehub.com |
| Technician | jack.martin@financehub.com |
| Employee | leo.garcia@financehub.com |

### HealthCare Plus
| Role | Email |
|------|-------|
| Admin | quinn.taylor@healthcareplus.com |
| Technician | rita.moore@healthcareplus.com |
| Employee | tina.martinez@healthcareplus.com |

> **Note:** Exact emails depend on seed script execution. Check the seed output for definitive emails.

---

## Feature Tour by Role

### Employee

1. **My Equipment** — View assigned assets (laptops, monitors, peripherals)
2. **My Requests** — See submitted service requests and their statuses
3. **New Request** — Submit an incident report, equipment request, or onboarding request
4. **Notifications** — View notifications about request updates

**Try it:**
- Log in as an employee
- Go to "My Equipment" to see assigned assets
- Submit a new incident request ("My laptop is slow")
- Check "My Requests" to see it appear as "Submitted"

### Technician

1. **Request Queue** — View all open requests, filter by status/type/priority
2. **Request Detail** — Assign to self, change status, add comments and internal notes
3. **Asset Inventory** — Browse, search, and filter all assets
4. **Asset Detail** — View asset history (events), check warranty status
5. **New Asset** — Register new equipment
6. **CSV Import** — Bulk import assets from CSV file

**Try it:**
- Log in as a technician
- Open "Request Queue" and filter by "Submitted" status
- Click a request, assign it to yourself
- Move status to "In Review", then "In Progress"
- Add a comment (visible to employee) and an internal note (tech-only)
- Go to "Assets" and try the search/filter functionality

### Admin

1. **Dashboard** — Charts showing request stats, asset status, SLA breaches, technician performance
2. **Users** — List all company users, change roles, activate/deactivate
3. **Departments** — Create and manage departments
4. **Reports** — Generate PDF reports (asset inventory, request summary, technician performance)

**Try it:**
- Log in as an admin
- View the Dashboard — check the bar charts and stat cards
- Look at the SLA breach table (demo data includes breaching requests)
- Go to "Reports", generate an "Asset Inventory" report
- Check Celery logs (`/tmp/celery-dsm.log`) for report generation progress
- Go to "Users" and try changing a user's role

### Super Admin

1. **Companies** — View all companies, create new ones, change status (active/suspended/deactivated)

**Try it:**
- Log in as super admin
- View the companies list with user/department counts
- Try creating a new company with an email domain
- Change a company's status to "Suspended"

---

## Reset Demo Data

To start fresh at any time:

```bash
make demo-reset
```

This drops all tables, re-applies migrations, and re-seeds demo data.
