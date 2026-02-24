# Feature 3: Retention & Integrity

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 3
**Dependencies:** F0 (Audit Foundation)
**Complexity:** S

## Scope

### Included

- RetentionPolicy domain entity (per-company config)
- RetentionPolicy infrastructure model + SQLAlchemy table (`retention_policies`)
- Retention policy CRUD (get, update)
- Automatic retention purge via Celery Beat scheduled task (weekly)
- Integrity verification endpoint + async Celery task
- Application commands: update_retention_policy
- Application queries: get_retention_policy
- HTTP endpoints: get retention, update retention, verify integrity (from F1 scope — moved here)
- Frontend: retention config section (within audit settings), integrity verification UI
- Feature gating (Enterprise plan)
- i18n keys (EN + ES)
- Unit + integration tests

### Excluded (in other features)

- AuditEntry creation/middleware (F0)
- Audit log UI/export (F1)
- Compliance tagging/controls (F1)
- GDPR operations (F2)

## User Value

Admins can configure how long audit log entries are retained before automatic purging, ensuring compliance with regulatory minimum retention periods (e.g., NIS2 requires 2+ years). Admins can also verify the integrity of the audit log by running per-entry hash verification to detect any tampered entries.

## User Stories Covered

- US-E29-006: Verify audit log integrity
- US-E29-010: Configure data retention policy
- UC-007: Verify Integrity
- UC-011: Configure Retention Policy

## Acceptance Criteria

- [ ] Admin can view current retention policy (default: 3 years / 36 months)
- [ ] Admin can update retention period: 12, 24, 36, 60, 84 months, or 0 (indefinite)
- [ ] Warning shown if retention < 24 months ("Below NIS2 recommended minimum")
- [ ] Retention purge runs as weekly Celery Beat scheduled task
- [ ] Purge deletes audit entries + associated tags older than retention period
- [ ] Before purging, creates a summary audit entry ("Purged N entries from [date] to [date]")
- [ ] Integrity verification: admin selects date range, clicks "Verify Integrity"
- [ ] Verification runs as async Celery task
- [ ] Task recomputes SHA-256 hash from entry data and compares with stored hash
- [ ] Reports: total entries checked, valid/invalid count, first broken entry details (if any)
- [ ] All retention/integrity endpoints return 402 for non-Enterprise plans
- [ ] i18n keys added for EN and ES (~10 keys)

## Technical Scope

### Entities (owned by this feature)

- **RetentionPolicy** — Per-company retention configuration

### Entities (used from dependencies)

- **AuditEntry** (from F0) — purged by retention, verified for integrity

### Key Components

#### Domain Layer (`src/audit_bc/audit/domain/`)

- `entities.py` — Add `RetentionPolicy` dataclass
- `exceptions.py` — Add `RetentionPolicyNotFoundError` (if needed)
- `repository.py` — Add abstract methods for retention policy

#### Application Layer (`src/audit_bc/audit/application/`)

- `commands/update_retention_policy.py` — Update retention config
- `commands/request_integrity_verification.py` — Start verification Celery task
- `queries/get_retention_policy.py` — Get current policy (or default)

#### Infrastructure Layer (`src/audit_bc/audit/infrastructure/`)

- `models.py` — Add `RetentionPolicyModel`
- `repository.py` — Implement retention policy methods

#### HTTP Layer (`adapters/http/api/audit/`)

- `schemas.py` — Add retention and integrity schemas
- `routers.py` — Add 3 endpoints: GET/PUT retention, POST verify

#### Celery

- `core/tasks/audit.py` — Add `retention_purge` task + `integrity_verification` task
- `core/celery.py` — Add weekly beat schedule for `retention_purge`

#### Migration

- `alembic/versions/xxxx_create_retention_policies.py` — Create `retention_policies` table

#### Frontend

- Retention config section (could be part of audit settings page or a standalone tab)
- Integrity verification button + results display on audit log page
- `web/app/src/locales/en.ts` + `es.ts` — i18n keys

## Notes

- The integrity verification endpoint was originally listed under F1's audit endpoints (`POST /api/v1/audit/verify`), but it logically belongs in F3 since it's about integrity checks. The router file is shared with F1, so F3 adds to the same router.
- Retention purge must also delete associated `audit_entry_tags` rows (cascade or explicit delete).
- Default retention policy (36 months) is created implicitly on first GET if no policy exists for the company.
