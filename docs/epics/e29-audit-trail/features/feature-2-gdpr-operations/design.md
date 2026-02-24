# Solution Design: GDPR Operations

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Bounded Context:** `audit_bc` (primary), `auth_bc` (User modification)

## Summary

Add GDPR data subject request management: data export (Article 15) and anonymization (Article 17). GdprRequest entity tracks each request through a state machine. Async Celery tasks collect cross-BC data for ZIP export or perform anonymization across User + AuditEntry tables. Enterprise plan gated.

## Architecture Decision

GdprRequest lives in `audit_bc` because GDPR operations are a compliance concern tightly coupled to audit data. The Celery tasks perform cross-BC reads (for export) and cross-BC writes (for anonymization) — this is acceptable for regulatory compliance operations that inherently span multiple BCs.

Anonymization uses a bulk SQL update for audit entries (actor_email) instead of loading all entities, for performance with large audit logs.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| User entity | `src/auth_bc/user/domain/entities.py` | Yes | Add `is_anonymized` field + `anonymize()` method |
| UserModel | `src/auth_bc/user/infrastructure/models.py` | Yes | Add `is_anonymized` column |
| UserRepository | `src/auth_bc/user/infrastructure/repository.py` | Yes | Add `is_anonymized` to save/convert |
| AuditRepository | `src/audit_bc/audit/infrastructure/repository.py` | Yes | Add `anonymize_actor_email()` bulk method |
| S3StorageService | `core/storage.py` | Yes | `upload()` + `get_signed_url()` |
| Celery task pattern | `core/tasks/audit.py` | Yes | Same SessionLocal + retry pattern |
| EventType enum | `src/notification_bc/notification/domain/enums.py` | Yes | Add 2 GDPR event types |
| require_plan_feature | `adapters/http/api/auth/dependencies.py` | Yes | Reuse for "audit_trail" gating |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| GdprRequest | `src/audit_bc/audit/domain/entities.py` | GDPR request with state machine |

**GdprRequest fields:**
- `id: str` (ULID)
- `company_id: str`
- `target_user_id: str` — user whose data is being exported/anonymized
- `target_user_email: str` — captured at request time (for display after anonymization)
- `requested_by: str` — admin who made the request
- `request_type: str` — "export" or "anonymize"
- `status: str` — pending/processing/completed/failed/cancelled
- `reason: Optional[str]` — reason for anonymization
- `storage_key: Optional[str]` — MinIO key for export ZIP
- `error_message: Optional[str]` — failure reason
- `started_at: Optional[datetime]` — when processing began
- `completed_at: Optional[datetime]` — when completed
- `created_at: Optional[datetime]`

**State machine methods:**
- `start_processing()` — pending → processing, sets started_at
- `complete(storage_key=None)` — processing → completed, sets completed_at
- `fail(error_message)` — processing → failed, sets completed_at
- `cancel()` — pending → cancelled

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| GdprRequestType | `src/audit_bc/audit/domain/enums.py` (NEW) | export, anonymize |
| GdprRequestStatus | `src/audit_bc/audit/domain/enums.py` | pending, processing, completed, failed, cancelled |

#### Exceptions (add to existing exceptions.py)

- `GdprRequestNotFoundError`
- `InvalidGdprStatusTransitionError`
- `CannotAnonymizeSuperAdminError`
- `CannotAnonymizeSelfError`
- `UserAlreadyAnonymizedError`
- `TargetUserNotFoundError`

### 2. Application Layer

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| RequestGdprExportCommand | RequestGdprExportHandler | Create export request, dispatch Celery task |
| RequestGdprAnonymizeCommand | RequestGdprAnonymizeHandler | Validate + create anonymize request, dispatch Celery task |
| CancelGdprRequestCommand | CancelGdprRequestHandler | Cancel pending request |

**RequestGdprExportCommand:**
- Fields: company_id, target_user_email, requested_by
- Handler: Find user by email in company, create GdprRequest(type=export), save, dispatch `gdpr_data_export.delay(gdpr_request_id)`, return request_id

**RequestGdprAnonymizeCommand:**
- Fields: company_id, target_user_id_or_email, requested_by, reason
- Handler: Find user. Reject if super_admin, self, or already anonymized. Create GdprRequest(type=anonymize), save, dispatch `gdpr_anonymize_user.delay(gdpr_request_id)`, return request_id

**CancelGdprRequestCommand:**
- Fields: request_id, company_id
- Handler: Find request. Call `cancel()`. Save.

#### Queries

| Query | Handler | Return |
|-------|---------|--------|
| ListGdprRequestsQuery | ListGdprRequestsHandler | `tuple[list[GdprRequestDto], int]` |
| GetGdprRequestQuery | GetGdprRequestHandler | `GdprRequestDto` |

#### DTOs

**GdprRequestDto** (in dtos.py — add to existing):
- id, company_id, target_user_id, target_user_email, requested_by, request_type, status, reason, storage_key, error_message, started_at, completed_at, created_at

### 3. Infrastructure Layer

#### Models

**GdprRequestModel** — `gdpr_requests` table:
- id (ULID PK)
- company_id (String 26, FK companies.id, NOT NULL)
- target_user_id (String 26, FK users.id, NOT NULL)
- target_user_email (String 255, NOT NULL)
- requested_by (String 26, FK users.id, NOT NULL)
- request_type (String 20, NOT NULL)
- status (String 20, NOT NULL, default "pending")
- reason (Text, nullable)
- storage_key (String 500, nullable)
- error_message (Text, nullable)
- started_at (DateTime TZ, nullable)
- completed_at (DateTime TZ, nullable)
- created_at (DateTime TZ, NOT NULL)
- Indexes: (company_id), (company_id, status), (target_user_id)

#### Repository Methods (add to AuditRepository)

- `save_gdpr_request(request: GdprRequest) -> None`
- `find_gdpr_request_by_id(request_id: str, company_id: Optional[str] = None) -> Optional[GdprRequest]`
- `find_gdpr_requests(company_id: str, filters: dict) -> tuple[list[GdprRequest], int]`
- `anonymize_actor_email(actor_id: str, anonymized_email: str) -> int` — bulk SQL update, returns count

#### Migrations

| Migration | Description |
|-----------|-------------|
| `e5f6g7h8i9j0_create_gdpr_requests.py` | Create gdpr_requests table |
| `f6g7h8i9j0k1_add_user_is_anonymized.py` | Add is_anonymized column to users |

**Revision chain:** d5e6f7g8h9i0 → e5f6g7h8i9j0 → f6g7h8i9j0k1

### 4. HTTP Layer

#### Endpoints (add to audit router, all gated by require_plan_feature + require_role ADMIN)

| # | Method | Route | Description |
|---|--------|-------|-------------|
| 1 | GET | `/api/v1/audit/gdpr` | List GDPR requests (paginated) |
| 2 | GET | `/api/v1/audit/gdpr/{id}` | Get GDPR request detail |
| 3 | POST | `/api/v1/audit/gdpr/export` | Request data export |
| 4 | POST | `/api/v1/audit/gdpr/anonymize` | Request anonymization |
| 5 | POST | `/api/v1/audit/gdpr/{id}/cancel` | Cancel pending request |

**Route ordering:** Static routes (`/gdpr/export`, `/gdpr/anonymize`) BEFORE parameterized `/gdpr/{id}`.

**Note:** These are added to the existing audit router as a `/gdpr` sub-path. Place them BEFORE the `/{entry_id}` catch-all.

#### Schemas

**Request:**
- `GdprExportRequest(target_user_email: str)`
- `GdprAnonymizeRequest(target_user_email: str, reason: str)`

**Response:**
- `GdprRequestResponse(id, target_user_email, request_type, status, reason, error_message, started_at, completed_at, created_at)`
- `GdprRequestDetailResponse` — same + storage_key download_url (signed URL if export completed)

### 5. Celery Tasks

**File:** `core/tasks/gdpr.py` (NEW)

#### gdpr_data_export(self, gdpr_request_id)

1. Load GdprRequest, call `start_processing()`, save
2. Load target user
3. Collect data from all BCs:
   - User profile (from UserRepository)
   - Assigned assets (from AssetModel query)
   - Created requests (from RequestModel query)
   - Comments (from CommentModel query)
   - Notifications (from NotificationModel query)
   - Audit entries where actor_id = user_id (from AuditEntryModel query)
4. Generate ZIP with JSON files for each section
5. Upload ZIP to MinIO: `gdpr-exports/{company_id}/{request_id}.zip`
6. Call `complete(storage_key=key)`, save
7. Create notification (GDPR_DATA_EXPORT_READY) for requesting admin
8. Commit

#### gdpr_anonymize_user(self, gdpr_request_id)

1. Load GdprRequest, call `start_processing()`, save, flush
2. Load target user
3. Generate anonymized email: `anonymized-{hash6}@redacted.local` where hash6 = first 6 chars of SHA256(user.id)
4. Anonymize user fields:
   - email → anonymized email
   - name → "Anonymized User"
   - password_hash → None
   - google_id → None
   - microsoft_id → None
   - is_anonymized → True
   - is_active → False
5. Save user via UserRepository
6. Bulk update audit entries: `anonymize_actor_email(user.id, anonymized_email)`
7. Call `complete()`, save
8. Create notification (GDPR_ANONYMIZATION_COMPLETED) for requesting admin
9. Commit

### 6. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/auth_bc/user/domain/entities.py` | Modify | Add `is_anonymized: bool = False` field |
| `src/auth_bc/user/infrastructure/models.py` | Modify | Add `is_anonymized` column |
| `src/auth_bc/user/infrastructure/repository.py` | Modify | Include `is_anonymized` in save + _to_entity |
| `src/audit_bc/audit/domain/entities.py` | Modify | Add GdprRequest dataclass |
| `src/audit_bc/audit/domain/exceptions.py` | Modify | Add 5 GDPR exceptions |
| `src/audit_bc/audit/domain/repository.py` | Modify | Add 4 GDPR abstract methods |
| `src/audit_bc/audit/infrastructure/models.py` | Modify | Add GdprRequestModel |
| `src/audit_bc/audit/infrastructure/repository.py` | Modify | Implement 4 GDPR methods |
| `src/audit_bc/audit/application/dtos.py` | Modify | Add GdprRequestDto |
| `adapters/http/api/audit/schemas.py` | Modify | Add GDPR schemas |
| `adapters/http/api/audit/routers.py` | Modify | Add 5 GDPR endpoints |
| `src/notification_bc/notification/domain/enums.py` | Modify | Add 2 event types |
| `core/tasks/__init__.py` | Modify | Register GDPR tasks |
| `web/app/src/types/index.ts` | Modify | Add GdprRequest interface |
| `web/app/src/router.tsx` | Modify | Add GDPR route |
| `web/app/src/components/layout/Sidebar.tsx` | Modify | Add GDPR nav item |
| `web/app/src/locales/en.ts` + `es.ts` | Modify | Add ~20 i18n keys |

#### New Files

| File | Description |
|------|-------------|
| `src/audit_bc/audit/domain/enums.py` | GdprRequestType, GdprRequestStatus enums |
| `src/audit_bc/audit/application/commands/request_gdpr_export.py` | Export command |
| `src/audit_bc/audit/application/commands/request_gdpr_anonymize.py` | Anonymize command |
| `src/audit_bc/audit/application/commands/cancel_gdpr_request.py` | Cancel command |
| `src/audit_bc/audit/application/queries/list_gdpr_requests.py` | List query |
| `src/audit_bc/audit/application/queries/get_gdpr_request.py` | Detail query |
| `core/tasks/gdpr.py` | Two Celery tasks |
| `alembic/versions/e5f6g7h8i9j0_create_gdpr_requests.py` | GdprRequest table |
| `alembic/versions/f6g7h8i9j0k1_add_user_is_anonymized.py` | User column |
| `web/app/src/pages/admin/GdprRequestsPage.tsx` | Frontend page |

## Database Schema

```sql
CREATE TABLE gdpr_requests (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    target_user_id VARCHAR(26) NOT NULL REFERENCES users(id),
    target_user_email VARCHAR(255) NOT NULL,
    requested_by VARCHAR(26) NOT NULL REFERENCES users(id),
    request_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    reason TEXT,
    storage_key VARCHAR(500),
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX ix_gdpr_requests_company ON gdpr_requests(company_id);
CREATE INDEX ix_gdpr_requests_company_status ON gdpr_requests(company_id, status);
CREATE INDEX ix_gdpr_requests_target ON gdpr_requests(target_user_id);

ALTER TABLE users ADD COLUMN is_anonymized BOOLEAN NOT NULL DEFAULT FALSE;
```

## State Machine

```
[create] → PENDING → PROCESSING → COMPLETED
                │         │
                │         └── FAILED
                │
                └── CANCELLED
```

Transitions:
- pending → processing (task picks up)
- pending → cancelled (admin cancels)
- processing → completed (task succeeds)
- processing → failed (task fails after retries)

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | GdprRequest entity state machine | High |
| Unit | Command handlers (export, anonymize, cancel) | High |
| Unit | Query handlers | Medium |
| Unit | Validation rules (super_admin, self, already anonymized) | High |
| Integration | All 5 GDPR endpoints | High |
| Integration | Plan gating (402) | Medium |
| Integration | Role gating (403) | Medium |

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Large audit log slows anonymization | Medium | Medium | Bulk SQL update instead of entity-by-entity |
| Export collects too much data | Low | Low | Paginate queries inside task, stream to ZIP |
| Anonymization partially fails | Low | High | Single transaction — rollback on any error |
