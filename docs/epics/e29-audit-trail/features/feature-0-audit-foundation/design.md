# Solution Design: Audit Foundation (F0)

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Bounded Context:** `audit_bc`

## Summary

Create a new `audit_bc` bounded context with a single `AuditEntry` entity that captures all write operations across the platform. The capture is implemented via two mechanisms: (1) a FastAPI `BaseHTTPMiddleware` that intercepts all non-GET HTTP requests, and (2) explicit audit emission in the MCP `call_tool` dispatcher. Both write audit entries in a separate DB transaction using `SessionLocal()` directly.

## Architecture Decisions

1. **New bounded context `audit_bc`** — Follows DDD structure: `src/audit_bc/audit/{domain,application,infrastructure}`. Audit is a cross-cutting concern but has its own entity lifecycle, so it merits its own BC.

2. **No application layer commands/queries in F0** — The middleware creates entities directly via the repository. The application layer (commands, queries) comes in F1 when the UI endpoints are added. F0 is infrastructure-only with a domain layer and a service.

3. **AuditService over command bus** — Since the middleware operates outside the DI container and needs a separate DB session, using a simple `AuditService` class is cleaner than routing through the command bus. The service takes a session, creates the entity, computes the hash, and saves.

4. **ContextVar for changes tracking** — A `ContextVar[dict]` allows command handlers to optionally set before/after diffs that the middleware reads after the handler completes. No coupling between handlers and the audit system.

5. **Action string derived from HTTP path** — The `action` field is derived from the URL pattern (e.g., `POST /api/v1/assets` → `asset.created`, `PATCH /api/v1/requests/{id}/status` → `request.status_changed`). A mapping function converts path patterns to semantic action strings.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| Tenant context | `core/tenant.py` | Yes | Read company_id, user_id from tenant context in middleware |
| SessionLocal | `core/database.py` | Yes | Create separate session for audit writes |
| Base, ULIDMixin, TimestampMixin | `core/base.py`, `core/mixins.py` | Yes | Standard model inheritance |
| SecurityHeadersMiddleware | `app.py` | Pattern | Follow same middleware registration pattern |
| MCP call_tool | `adapters/mcp/server.py:56-77` | Modify | Add audit emission after tool execution |
| Risk entity pattern | `src/risk_bc/risk/domain/entities.py` | Pattern | Follow same dataclass + factory method pattern |
| Risk repository pattern | `src/risk_bc/risk/domain/repository.py` | Pattern | Follow same ABC + abstract methods |
| Risk model pattern | `src/risk_bc/risk/infrastructure/models.py` | Pattern | Follow same Mapped + mapped_column pattern |
| Risk repo impl pattern | `src/risk_bc/risk/infrastructure/repository.py` | Pattern | Follow same Session-based implementation |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| AuditEntry | `src/audit_bc/audit/domain/entities.py` | Immutable audit record with per-entry SHA-256 hash |

**AuditEntry dataclass:**
```python
@dataclass
class AuditEntry:
    id: str
    company_id: Optional[str]       # null for super_admin actions
    actor_id: Optional[str]         # null for unauthenticated (registration)
    actor_email: str                # denormalized, "" if unauthenticated
    action: str                     # e.g. "asset.created"
    resource_type: str              # e.g. "asset"
    resource_id: Optional[str]      # null if no specific resource
    http_method: str                # POST/PUT/PATCH/DELETE/MCP
    http_path: str                  # request path or MCP tool name
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_data: Optional[dict]    # sanitized request body
    response_status: int            # HTTP status or 0 for MCP
    changes: Optional[dict]         # before/after diff
    hash: str                       # SHA-256 of entry data
    created_at: Optional[datetime]

    @classmethod
    def create(cls, ...) -> "AuditEntry":
        entry_id = str(ulid.new())
        hash_value = cls.compute_hash(company_id, actor_id, action, resource_type, resource_id, created_at)
        return cls(id=entry_id, hash=hash_value, ...)

    @staticmethod
    def compute_hash(company_id, actor_id, action, resource_type, resource_id, created_at) -> str:
        data = f"{company_id}|{actor_id}|{action}|{resource_type}|{resource_id}|{created_at.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
```

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| N/A | — | Action strings are free-form (not enum-constrained) since they're derived from paths |

#### Domain Constants

| Constant | File Path | Description |
|----------|-----------|-------------|
| SANITIZED_FIELDS | `src/audit_bc/audit/domain/constants.py` | Set of field names to redact from request_data |

**SANITIZED_FIELDS:**
```python
SANITIZED_FIELDS = {
    "password", "password_hash", "token", "magic_link",
    "secret", "stripe_secret_key", "credentials",
    "current_password", "new_password",
}
```

### 2. Application Layer

#### Services

| Service | File Path | Description |
|---------|-----------|-------------|
| AuditService | `src/audit_bc/audit/application/services/audit_service.py` | Creates AuditEntry from request metadata, persists via repository |

**AuditService:**
```python
class AuditService:
    def __init__(self, repository: AuditRepositoryInterface):
        self.repository = repository

    def record(
        self,
        company_id: Optional[str],
        actor_id: Optional[str],
        actor_email: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        http_method: str,
        http_path: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_data: Optional[dict],
        response_status: int,
        changes: Optional[dict],
    ) -> None:
        entry = AuditEntry.create(...)
        self.repository.save(entry)
```

#### Context Variables

| ContextVar | File Path | Description |
|------------|-----------|-------------|
| audit_changes | `src/audit_bc/audit/application/context.py` | Before/after diff set by command handlers |
| audit_action_override | `src/audit_bc/audit/application/context.py` | Optional action string override (handlers can set semantic action) |

```python
from contextvars import ContextVar
from typing import Optional

audit_changes: ContextVar[Optional[dict]] = ContextVar("audit_changes", default=None)
audit_action_override: ContextVar[Optional[str]] = ContextVar("audit_action_override", default=None)
```

### 3. Infrastructure Layer

#### Repository Interface

| Interface | File Path | Methods |
|-----------|-----------|---------|
| AuditRepositoryInterface | `src/audit_bc/audit/domain/repository.py` | `save(entry)`, `find_by_id(id, company_id)` |

Note: F0 only needs `save()`. Query methods (`find_by_company`, etc.) are added in F1 when the UI endpoints are introduced.

#### Repository Implementation

| Implementation | File Path | Table |
|----------------|-----------|-------|
| AuditRepository | `src/audit_bc/audit/infrastructure/repository.py` | audit_entries |

#### Model

| Model | File Path | Description |
|-------|-----------|-------------|
| AuditEntryModel | `src/audit_bc/audit/infrastructure/models.py` | SQLAlchemy model with composite indexes |

```python
class AuditEntryModel(ULIDMixin, Base):
    __tablename__ = "audit_entries"

    company_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    http_path: Mapped[str] = mapped_column(String(500), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_audit_entries_company_created", "company_id", "created_at"),
        Index("ix_audit_entries_company_actor_created", "company_id", "actor_id", "created_at"),
        Index("ix_audit_entries_company_resource", "company_id", "resource_type", "resource_id"),
    )
```

Note: No `TimestampMixin` — AuditEntry manages its own `created_at` and has no `updated_at` (immutable).

#### Migration

| Migration | File Path | Description |
|-----------|-----------|-------------|
| Create audit_entries | `alembic/versions/xxxx_create_audit_entries.py` | Create table with all columns and composite indexes |

### 4. HTTP Layer (Middleware)

#### Middleware

| Middleware | File Path | Description |
|------------|-----------|-------------|
| AuditMiddleware | `adapters/http/middleware/audit.py` | Intercepts non-GET requests, creates AuditEntry in separate transaction |

**Key middleware logic:**
```python
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Reset context vars
        audit_changes.set(None)
        audit_action_override.set(None)

        response = await call_next(request)

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            try:
                self._record_audit(request, response)
            except Exception:
                logger.exception("Audit recording failed")

        return response

    def _record_audit(self, request, response):
        tenant = get_tenant()
        # Extract metadata from request
        # Create separate session
        db = SessionLocal()
        try:
            repo = AuditRepository(db)
            service = AuditService(repo)
            service.record(
                company_id=tenant.company_id if tenant else None,
                actor_id=tenant.user_id if tenant else None,
                actor_email=...,
                action=self._derive_action(request),
                resource_type=self._extract_resource_type(request.url.path),
                resource_id=self._extract_resource_id(request.url.path),
                http_method=request.method,
                http_path=str(request.url.path),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_data=self._sanitize_body(body),
                response_status=response.status_code,
                changes=audit_changes.get(),
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to save audit entry")
        finally:
            db.close()
```

**Path-to-action mapping:**
```python
def _derive_action(self, request: Request) -> str:
    override = audit_action_override.get()
    if override:
        return override
    # Parse path: /api/v1/assets -> resource_type = "asset"
    # Combine with method: POST -> "created", PUT/PATCH -> "updated", DELETE -> "deleted"
    return f"{resource_type}.{method_action}"
```

**Excluded paths** (no audit for these):
- `/api/v1/health`
- `/docs`, `/openapi.json`
- WebSocket paths (`/ws/`)

#### Registration in app.py

```python
from adapters.http.middleware.audit import AuditMiddleware
application.add_middleware(AuditMiddleware)
```

### 5. MCP Layer

#### MCP Audit Capture

| File | Modification | Description |
|------|-------------|-------------|
| `adapters/mcp/server.py` | Modify `call_tool` | Add audit emission after successful tool execution |

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    # ... existing auth/permission checks ...
    result = await tool.handler(arguments)

    # Audit capture
    try:
        _record_mcp_audit(tenant, name, arguments)
    except Exception:
        logger.exception("MCP audit recording failed for tool %s", name)

    return result
```

```python
def _record_mcp_audit(tenant: TenantContext, tool_name: str, arguments: dict):
    db = SessionLocal()
    try:
        repo = AuditRepository(db)
        service = AuditService(repo)
        # Determine if write tool by checking if tool name implies mutation
        resource_type, resource_id = _extract_mcp_resource(tool_name, arguments)
        service.record(
            company_id=tenant.company_id,
            actor_id=tenant.user_id,
            actor_email="",  # MCP doesn't have email readily available
            action=f"mcp.{tool_name}",
            resource_type=resource_type,
            resource_id=resource_id,
            http_method="MCP",
            http_path=tool_name,
            ip_address=None,  # MCP stdio/SSE doesn't provide IP easily
            user_agent=None,
            request_data=_sanitize_dict(arguments),
            response_status=0,
            changes=None,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### 6. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `app.py` | Add import + middleware | Register `AuditMiddleware` |
| `adapters/mcp/server.py` | Modify `call_tool` | Add audit emission |
| `src/audit_bc/__init__.py` | New file | Empty init |
| `src/audit_bc/audit/__init__.py` | New file | Empty init |
| `src/audit_bc/audit/domain/__init__.py` | New file | Empty init |
| `src/audit_bc/audit/application/__init__.py` | New file | Empty init |
| `src/audit_bc/audit/application/services/__init__.py` | New file | Empty init |
| `src/audit_bc/audit/infrastructure/__init__.py` | New file | Empty init |

## Database Schema

```sql
CREATE TABLE audit_entries (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26),
    actor_id VARCHAR(26),
    actor_email VARCHAR(255) NOT NULL DEFAULT '',
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(26),
    http_method VARCHAR(10) NOT NULL,
    http_path VARCHAR(500) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    request_data JSONB,
    response_status INTEGER NOT NULL,
    changes JSONB,
    hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX ix_audit_entries_company_created ON audit_entries (company_id, created_at);
CREATE INDEX ix_audit_entries_company_actor_created ON audit_entries (company_id, actor_id, created_at);
CREATE INDEX ix_audit_entries_company_resource ON audit_entries (company_id, resource_type, resource_id);
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `hashlib` | stdlib | SHA-256 hash computation |
| `ulid-py` | existing | ULID generation (already in project) |
| `contextvars` | stdlib | ContextVar for changes/action override |
| `core/tenant.py` | internal | Get current user context |
| `core/database.py` | internal | SessionLocal for separate transaction |

## Testing Strategy

| Test Type | Scope | Priority | File |
|-----------|-------|----------|------|
| Unit | AuditEntry.create(), compute_hash() | High | `tests/unit/audit_bc/audit/domain/test_entities.py` |
| Unit | AuditService.record() | High | `tests/unit/audit_bc/audit/application/services/test_audit_service.py` |
| Unit | Request body sanitization | High | `tests/unit/audit_bc/audit/domain/test_sanitization.py` |
| Unit | Path-to-action derivation | Medium | `tests/unit/audit_bc/audit/test_action_mapping.py` |
| Integration | Middleware captures POST/PUT/PATCH/DELETE | High | `tests/integration/test_audit_middleware.py` |
| Integration | Middleware skips GET requests | High | `tests/integration/test_audit_middleware.py` |
| Integration | Audit entry persisted with correct data | High | `tests/integration/test_audit_middleware.py` |

## Implementation Order

1. [ ] Domain: AuditEntry entity + compute_hash + sanitization constants
2. [ ] Domain: AuditRepositoryInterface
3. [ ] Infrastructure: AuditEntryModel
4. [ ] Infrastructure: Migration
5. [ ] Infrastructure: AuditRepository implementation
6. [ ] Application: Context vars (audit_changes, audit_action_override)
7. [ ] Application: AuditService
8. [ ] HTTP: AuditMiddleware
9. [ ] MCP: Audit capture in call_tool
10. [ ] Collateral: Register middleware in app.py
11. [ ] Tests: Unit tests
12. [ ] Tests: Integration tests

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Middleware overhead > 5ms | Low | Medium | Audit write is fire-and-forget; hash is fast (SHA-256 on short string) |
| Request body reading in middleware | Medium | Medium | BaseHTTPMiddleware may have limitations reading body; may need to cache body in middleware or use a different approach |
| MCP tools that don't mutate data | Low | Low | All MCP tool calls are audited; non-write tools generate harmless entries |
