<p align="center">
  <img src="web/site/logo.png" alt="DeskSupportMonkey" width="280" />
</p>

# DeskSupportMonkey

**IT Service Desk & Asset Inventory Platform** — A full-stack, multi-tenant application built entirely with AI-assisted development to demonstrate how production-grade software can be designed, implemented, and validated using AI as a development partner.

---

## What Is This?

DeskSupportMonkey is a working IT service desk where companies manage help desk tickets, IT asset inventory, users, departments, and reports. It supports multi-tenancy, role-based access, real-time notifications, PDF reports, and a modern React frontend.

This project demonstrates a structured AI development methodology. Every epic was developed through an AI agent pipeline that mirrors a professional software team's workflow.

---

## Features

| Role | Capabilities |
|------|-------------|
| **Employee** | View equipment, submit requests (6 types + AI classification), track requests, schedule appointments, view shipments, real-time notifications |
| **Technician** | Request queue, asset inventory with QR/barcodes, maintenance calendar, shipment management, availability settings |
| **Admin** | Dashboard with metrics/SLA alerts, user/department management, equipment profiles, procurement, maintenance templates, PDF reports, API keys |
| **Super Admin** | Multi-tenant company management, status control |

### Platform Highlights

- 20+ bounded contexts following DDD + CQRS + Clean Architecture
- AI-powered request classification and auto-assignment (Groq/OpenAI)
- MCP server with 57+ AI-callable tools for Claude Desktop
- Real-time WebSocket notifications, domain event bus
- Procurement: POs, vendors, budgets, supply chain risk, contracts
- Compliance: NIS2/DORA/ISO 27001 dashboards, audit trail, risk register
- Change management (ITIL), security incident lifecycle, vulnerability tracking
- Background PDF reports (Celery + MinIO), bilingual UI (EN/ES)
- Magic link + password + Google/Microsoft OAuth2 authentication

---

## Tech Stack

**Backend:** Python 3.13, FastAPI, SQLAlchemy, Alembic, Celery + Redis, JWT, MinIO (S3), uv
**Frontend:** React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4, TanStack React Query, React Router 7
**Infrastructure (Docker Compose):** PostgreSQL 15 (:5443), Redis (:6398), Mailpit (:8028/:1028), MinIO (:9000/:9001)

---

## Architecture

Each bounded context follows DDD layers:

```
{bc}_bc/{subdomain}/
├── domain/          # Entities, enums, repository interface (port)
├── application/     # Commands (write) and queries (read) — CQRS
└── infrastructure/  # SQLAlchemy models, repository implementation
```

HTTP adapters in `adapters/http/api/` orchestrate commands/queries. Dependency rule: Domain ← Application ← Infrastructure ← Adapters.

---

## Quick Start

```bash
# 1. Clone and configure
git clone <repo-url> && cd desksupportmonkey
cp .env.example .env

# 2. Start infrastructure
make start-docker

# 3. Install dependencies, migrate, seed
make install && make db-upgrade && make seed

# 4. Start everything
make start
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| Mailpit | http://localhost:8028 |
| MinIO | http://localhost:9001 |

### Demo Accounts (magic link → check Mailpit)

| Company | Role | Email |
|---------|------|-------|
| *(global)* | Super Admin | admin@desksupportmonkey.com |
| TechCorp | Admin | alice.smith@techcorp.com |
| TechCorp | Technician | bob.johnson@techcorp.com |
| TechCorp | Employee | dave.brown@techcorp.com |

---

## Commands

```bash
make start / stop           # All services
make start-backend          # FastAPI only
make start-frontend         # Vite dev server
make queue                  # Celery worker
make test                   # Unit tests
make test-integration       # Integration tests (Docker required)
make lint                   # mypy + flake8
make db-upgrade / db-migrate msg="x" / db-downgrade
make seed / demo-reset      # Load / reset demo data
make scan                   # OWASP ZAP security scan
```

---

## AI Agent Pipeline

10 agents in `ai_docs/agents/` form a complete SDLC — from requirements to validation:

**Requirements:** Write → Validate → Slice → Design → Tasks
**Validation:** DoD Check → Architecture → Quality → Performance → Linter → Testing

Architecture standards enforced by agents are documented in `ai_docs/architecture/`.

---

## License

Built by [Juan Macias](mailto:extjmv@gmail.com).
