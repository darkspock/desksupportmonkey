# Feature F0: Bootstrapping

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 0
**Dependencies:** None
**Complexity:** M

---

## Scope

### Included
- FastAPI application entry point (`app.py`)
- Docker Compose verification (all 4 services boot)
- PostgreSQL connection + SQLAlchemy engine + session management
- Alembic configuration and initial migration
- Base model class (ULID PKs, `created_at`, `updated_at`)
- Company model (minimal: id, name, is_active) - schema only, no API
- User model (schema only, no API yet)
- MagicLink model (schema only, no API yet)
- API response standards (success, list, error formats)
- CORS middleware
- Health check endpoint
- `.env.example` with all defaults
- Swagger UI at `/docs`

### Excluded (in other features)
- Authentication endpoints (F1)
- RBAC dependencies (F1)
- Multi-tenancy filtering (F1)
- Super admin bootstrap (F1)
- Celery worker (F2)
- MinIO client (F2)

---

## User Value

After F0, a developer can:
- Run `make start` and see all Docker services running
- Run `make db-upgrade` and have tables created
- Hit `GET /health` and get a 200 response
- Open `GET /docs` and see the Swagger UI
- Start building endpoints with consistent response formats

---

## Acceptance Criteria

- [ ] `make start` launches PostgreSQL, Redis, Mailpit, MinIO without errors
- [ ] `make db-upgrade` creates `users`, `magic_links`, `companies` tables
- [ ] `GET /health` returns `{"status": "healthy"}` with 200
- [ ] `GET /docs` renders Swagger UI
- [ ] `.env.example` exists with all required variables and defaults
- [ ] Base model provides ULID generation, `created_at`, `updated_at`
- [ ] API error handler returns standard error format for 400, 404, 500
- [ ] CORS allows requests from `FRONTEND_URL`

---

## Technical Scope

### Entities (owned by this feature - schema only)

**Company** (minimal)
| Field | Type |
|---|---|
| id | ULID PK |
| name | string |
| is_active | boolean, default true |
| created_at | datetime |
| updated_at | datetime |

**User**
| Field | Type |
|---|---|
| id | ULID PK |
| email | string, unique, indexed |
| name | string, nullable |
| role | enum (super_admin, admin, technician, employee) |
| company_id | ULID FK -> Company, nullable |
| is_active | boolean, default true |
| created_at | datetime |
| updated_at | datetime |

**MagicLink**
| Field | Type |
|---|---|
| id | ULID PK |
| email | string, indexed |
| token | string, unique, indexed |
| expires_at | datetime |
| used_at | datetime, nullable |
| created_at | datetime |

### Key Components
- `app.py` - FastAPI application factory
- `core/base.py` - SQLAlchemy Base (already exists, verify)
- `core/database.py` - Engine, session, get_db (already exists, verify)
- `core/config.py` - Settings (already exists, verify)
- `adapters/http/api/health.py` - Health check router
- `adapters/http/middleware/` - CORS, error handlers
- `adapters/http/schemas/responses.py` - Standard response models
- First Alembic migration with all 3 tables

---

## Notes

This feature creates the DB schema for all 3 entities but does NOT create any business logic or API endpoints for them. Those come in F1 (auth) and E1 (company management). The goal is: app boots, DB has tables, API responds.
