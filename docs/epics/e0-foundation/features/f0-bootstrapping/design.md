# Solution Design: F0 - Bootstrapping

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-15
**Bounded Context:** None (cross-cutting foundation)

---

## Summary

Set up the FastAPI application, database connection, base models with ULID PKs, initial Alembic migration for 3 tables (companies, users, magic_links), standard API response format, CORS, health check, and `.env.example`.

---

## Architecture Decision

Minimal bootstrapping. No business logic, no CQRS yet. Just the skeleton that proves the app runs, the DB has tables, and the API responds with consistent formats. CQRS and bounded contexts start in F1.

---

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|---|---|---|---|
| SQLAlchemy Base | `core/base.py` | Yes | Add ULID mixin, timestamps mixin |
| Database engine | `core/database.py` | Yes | Verify config matches docker-compose ports |
| Config | `core/config.py` | Yes | Already adapted for DSM |
| Alembic | `alembic/` | Yes | Clear old versions (done), verify env.py |
| Docker Compose | `docker-compose.yml` | Yes | Already adapted |
| Makefile | `Makefile` | Yes | Already adapted |

---

## Implementation Plan

### 1. Core Mixins

**ULIDMixin** - `core/mixins.py`
```python
import ulid
from sqlalchemy import Column, String, DateTime, func

class ULIDMixin:
    id = Column(String(26), primary_key=True, default=lambda: str(ulid.new()))

class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

### 2. SQLAlchemy Models (schema only)

**CompanyModel** - `src/company_bc/company/infrastructure/models.py`

| Column | Type | Constraints |
|---|---|---|
| id | String(26) | PK, ULID |
| name | String(255) | NOT NULL |
| is_active | Boolean | DEFAULT true |
| created_at | DateTime | server_default now() |
| updated_at | DateTime | onupdate now() |

**UserModel** - `src/auth_bc/user/infrastructure/models.py`

| Column | Type | Constraints |
|---|---|---|
| id | String(26) | PK, ULID |
| email | String(255) | UNIQUE, NOT NULL, INDEX |
| name | String(255) | NULLABLE |
| role | String(20) | NOT NULL (enum: super_admin, admin, technician, employee) |
| company_id | String(26) | FK -> companies.id, NULLABLE, INDEX |
| is_active | Boolean | DEFAULT true |
| created_at | DateTime | server_default now() |
| updated_at | DateTime | onupdate now() |

**MagicLinkModel** - `src/auth_bc/magic_link/infrastructure/models.py`

| Column | Type | Constraints |
|---|---|---|
| id | String(26) | PK, ULID |
| email | String(255) | NOT NULL, INDEX |
| token | String(500) | UNIQUE, NOT NULL, INDEX |
| expires_at | DateTime | NOT NULL |
| used_at | DateTime | NULLABLE |
| created_at | DateTime | server_default now() |

### 3. Alembic Migration

Single initial migration creating all 3 tables with indexes and FK.

### 4. FastAPI App

**app.py** - Application factory:
- Create FastAPI instance (title, description, version)
- Add CORS middleware (allow FRONTEND_URL)
- Include health router
- Register startup event (verify DB connection)

### 5. API Response Standards

**adapters/http/schemas/responses.py**:
```python
class SuccessResponse(BaseModel, Generic[T]):
    data: T

class ListResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int

class ErrorResponse(BaseModel):
    error: ErrorDetail

class ErrorDetail(BaseModel):
    code: str
    message: str
```

**adapters/http/middleware/error_handler.py** - Global exception handlers for 400, 404, 422, 500.

### 6. Health Check

**adapters/http/api/health.py**:
```python
@router.get("/health")
async def health():
    return {"status": "healthy"}
```

### 7. Environment

**.env.example** with all vars and defaults.

---

## Database Schema

```sql
CREATE TABLE companies (
    id VARCHAR(26) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id VARCHAR(26) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    role VARCHAR(20) NOT NULL,
    company_id VARCHAR(26) REFERENCES companies(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_company_id ON users(company_id);

CREATE TABLE magic_links (
    id VARCHAR(26) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_magic_links_email ON magic_links(email);
CREATE INDEX idx_magic_links_token ON magic_links(token);
```

---

## Testing Strategy

| Test Type | Scope | Priority |
|---|---|---|
| Integration | Health check returns 200 | High |
| Integration | Alembic migration runs cleanly | High |
| Unit | Response schema serialization | Medium |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Port conflicts with other projects | Medium | Low | Use non-standard ports (5443, 6398, 8027) - already done |
| Alembic autogenerate misses indexes | Low | Medium | Verify migration SQL manually |
