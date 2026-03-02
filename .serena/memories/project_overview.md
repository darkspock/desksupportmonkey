# DeskSupportMonkey - Project Overview

## Purpose
IT Service Desk & Asset Inventory Platform (SaaS). Multi-tenant, white-label capable.

## Tech Stack

### Backend
- **Language:** Python 3.13
- **Framework:** FastAPI + Uvicorn
- **ORM:** SQLAlchemy 2.0 (Mapped style, NOT bare Column())
- **Database:** PostgreSQL
- **Migrations:** Alembic
- **Queue:** Celery + Redis
- **Auth:** JWT (PyJWT) + bcrypt passwords + magic links
- **Storage:** MinIO (S3-compatible) via boto3
- **Email:** httpx-based
- **Reports:** WeasyPrint + Jinja2 templates
- **Payments:** Stripe
- **Monitoring:** Sentry
- **MCP:** MCP SSE transport (optional, configurable)
- **Package manager:** uv

### Frontend
- **Framework:** React 19 + TypeScript
- **Build:** Vite
- **Styling:** Tailwind CSS
- **Package manager:** npm
- **Location:** `web/app/`

### Infrastructure
- Docker Compose for local dev (PostgreSQL, Redis, Mailpit, MinIO)
- Staging deployment at staging.desksupportmonkey.com

## Entry Point
- `app.py` — FastAPI app factory (`create_app()`)
- Backend runs on port 8001
- Frontend runs on port 5173

## Bounded Contexts (src/)
auth_bc, asset_bc, asset_type_bc, incident_bc, request_bc, change_bc, risk_bc, vulnerability_bc, kb_bc, sla_bc, workflow_bc, appointment_bc, shipping_bc, procurement_bc, maintenance_bc, notification_bc, report_bc, audit_bc, company_bc, custom_field_bc, mcp_bc, framework
