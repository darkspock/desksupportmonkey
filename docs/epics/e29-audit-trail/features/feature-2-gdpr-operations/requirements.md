# Feature 2: GDPR Operations

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** F0 (Audit Foundation)
**Complexity:** M

## Scope

### Included

- GdprRequest domain entity with state machine (pending → processing → completed/failed/cancelled)
- GdprRequest infrastructure model + SQLAlchemy table (`gdpr_requests`)
- GDPR data export Celery task (collect data from all BCs, generate ZIP)
- GDPR data anonymization Celery task (anonymize PII across User + audit entries)
- `is_anonymized` field on User entity + UserModel + migration
- GDPR request management: list, detail, create export, create anonymization, cancel
- Application commands: request_gdpr_export, request_gdpr_anonymize, cancel_gdpr_request
- Application queries: list_gdpr_requests, get_gdpr_request
- HTTP endpoints: 5 GDPR endpoints
- Frontend: GDPR requests page (list, create, detail, cancel)
- Feature gating (Enterprise plan)
- Notification on export/anonymization completion
- i18n keys (EN + ES)
- Unit + integration tests

### Excluded (in other features)

- AuditEntry creation/middleware (F0)
- Audit log UI/export (F1)
- Compliance tagging/controls (F1)
- Retention policy and purge (F3)
- Integrity verification (F3)

## User Value

Admins can fulfill GDPR data subject requests: export all personal data for a user (Article 15 — right of access), or anonymize a user's personal data while preserving audit trail integrity (Article 17 — right to erasure). Requests can be cancelled if created by mistake.

## User Stories Covered

- US-E29-007: GDPR data export
- US-E29-008: GDPR data anonymization
- US-E29-009: Cancel pending GDPR request
- UC-008: GDPR Data Export
- UC-009: GDPR Data Anonymization
- UC-010: Cancel Pending GDPR Request

## Acceptance Criteria

- [ ] Admin can request data export for a user by email/ID
- [ ] Export generates ZIP with all personal data: user profile, assigned assets, created requests, comments, notifications, audit entries
- [ ] Export runs as async Celery task
- [ ] Export stored in MinIO with signed URL (24h expiry), download link sent via notification
- [ ] Admin can request anonymization for a user by email/ID + reason
- [ ] Anonymization replaces: name/email → "Anonymized User [hash6]", clears google_id/microsoft_id/password_hash
- [ ] Audit entries: actor_email anonymized for target user's entries
- [ ] User record set `is_anonymized = true`
- [ ] Anonymization is irreversible and logged in audit trail
- [ ] Cannot anonymize super_admin — rejected with error
- [ ] Cannot anonymize the requesting admin themselves — rejected
- [ ] Cannot anonymize already-anonymized user — conflict
- [ ] GDPR request state machine: pending → processing → completed/failed, pending → cancelled
- [ ] Admin can cancel pending GDPR request
- [ ] Cannot cancel once status = processing
- [ ] GdprRequest includes: started_at (set when processing begins), completed_at (set on completion)
- [ ] All GDPR endpoints return 402 for non-Enterprise plans
- [ ] Admin receives notification when export/anonymization completes
- [ ] i18n keys added for EN and ES (~15 keys)

## Technical Scope

### Entities (owned by this feature)

- **GdprRequest** — Data export or anonymization request with state machine

### Entities (used from dependencies)

- **AuditEntry** (from F0) — anonymize actor_email, include in data export

### Entities (modified by this feature)

- **User** (from `auth_bc`) — add `is_anonymized: bool` field

### Key Components

#### Domain Layer (`src/audit_bc/audit/domain/`)

- `entities.py` — Add `GdprRequest` dataclass with state machine methods
- `enums.py` — Add `GdprRequestType` (export/anonymize), `GdprRequestStatus` (pending/processing/completed/failed/cancelled)
- `exceptions.py` — Add `GdprRequestNotFoundError`, `InvalidGdprStatusTransitionError`, `CannotAnonymizeSuperAdminError`, `CannotAnonymizeSelfError`, `UserAlreadyAnonymizedError`
- `repository.py` — Add abstract methods for GDPR requests

#### Application Layer (`src/audit_bc/audit/application/`)

- `commands/request_gdpr_export.py` — Create export request, dispatch Celery task
- `commands/request_gdpr_anonymize.py` — Create anonymization request, dispatch Celery task
- `commands/cancel_gdpr_request.py` — Cancel pending request
- `queries/list_gdpr_requests.py` — List requests for company
- `queries/get_gdpr_request.py` — Get request detail

#### Infrastructure Layer (`src/audit_bc/audit/infrastructure/`)

- `models.py` — Add `GdprRequestModel`
- `repository.py` — Implement GDPR request methods

#### HTTP Layer (`adapters/http/api/audit/`)

- `schemas.py` — Add GDPR request/response schemas
- `routers.py` — Add 5 GDPR endpoints (or separate `gdpr_routers.py`)

#### Celery

- `core/tasks/gdpr.py` — `gdpr_export` task (collect data, generate ZIP, upload to MinIO) + `gdpr_anonymize` task (anonymize across BCs)

#### User Entity Modification

- `src/auth_bc/user/domain/entities.py` — Add `is_anonymized: bool` field
- `src/auth_bc/user/infrastructure/models.py` — Add `is_anonymized` column
- `alembic/versions/xxxx_add_user_is_anonymized.py` — Add column migration

#### Migration

- `alembic/versions/xxxx_create_gdpr_requests.py` — Create `gdpr_requests` table

#### Notification

- `src/notification_bc/notification/domain/enums.py` — Add `gdpr_export_completed`, `gdpr_anonymization_completed` event types

#### Frontend

- `web/app/src/pages/admin/GdprRequestsPage.tsx` — GDPR request management page
- `web/app/src/router.tsx` — Add route
- `web/app/src/components/layout/Sidebar.tsx` — Add nav item under Settings
- `web/app/src/types/index.ts` — Add TypeScript interfaces
- `web/app/src/locales/en.ts` + `es.ts` — i18n keys

## Notes

- Anonymization task must be carefully implemented to handle cross-BC data. It needs direct DB access to audit_entries (actor_email), users (PII fields), and potentially notifications (body content).
- The export task collects data from multiple BCs — it queries users, assets, requests, comments, notifications, and audit_entries tables directly (read-only cross-BC query is acceptable for GDPR compliance).
- Domain events (`RequestEvent`, `AssetEvent`, etc.) store only FKs to actors, not denormalized PII, so they don't need anonymization.
