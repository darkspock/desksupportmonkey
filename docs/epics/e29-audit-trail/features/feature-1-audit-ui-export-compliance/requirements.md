# Feature 1: Audit UI, Export & Compliance

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** F0 (Audit Foundation)
**Complexity:** L

## Scope

### Included

- Audit log list page (admin) — paginated, filterable, searchable
- Audit entry detail page (admin) — full metadata, before/after diff, compliance tags
- Audit log export (CSV + PDF) via async Celery task
- ComplianceControl entity + CRUD (predefined catalog + custom controls)
- AuditEntryTag join table entity + add/remove tag endpoints
- Predefined compliance control catalog seed (NIS2, DORA, ISO 27001 controls)
- Super admin cross-company audit log page
- Feature gating — audit UI/export/tagging return 402 for non-Enterprise plans
- Application queries: list audit entries, get audit entry detail, list compliance controls
- Application commands: create/update/deactivate compliance control, add/remove audit entry tags, request export
- Celery task: audit log export (CSV/PDF generation, MinIO upload)
- Frontend pages: audit log list, audit entry detail, compliance controls management
- Super admin frontend page: cross-company audit
- Sidebar navigation + routing
- i18n keys (EN + ES)
- Unit + integration tests

### Excluded (in other features)

- AuditEntry creation/middleware (F0 — already deployed)
- GDPR export/anonymization (F2)
- Retention policy and purge (F3)
- Integrity verification (F3)

## User Value

Admins can view a complete audit trail of all actions taken in their company, search and filter by actor/date/resource/action, export compliance evidence packages as CSV or PDF, and tag audit entries with NIS2/DORA/ISO 27001 compliance controls. Super admins can view audit logs across all companies for platform-level investigations.

## User Stories Covered

- US-E29-001: View audit log
- US-E29-002: View audit entry detail
- US-E29-003: Export audit log
- US-E29-004: Tag audit entries with compliance controls
- US-E29-005: Manage compliance control catalog
- US-E29-011: Cross-company audit log (super admin)
- UC-003: Search Audit Log
- UC-004: Export Audit Log
- UC-005: Tag/Untag Entries with Compliance Controls
- UC-006: Manage Compliance Control Catalog
- UC-012: Super Admin Cross-Company Audit

## Acceptance Criteria

- [ ] Audit log UI shows paginated entries: timestamp, actor (name + email), action, resource type, resource ID, IP
- [ ] Filterable by: date range, actor, action type, resource type, compliance tag
- [ ] Searchable by resource ID or actor name
- [ ] Audit entry detail shows full metadata, before/after JSON diff, compliance tags
- [ ] CSV export includes all fields; PDF is formatted as a compliance report
- [ ] Export runs as async Celery task with download link (MinIO, 1h signed URL)
- [ ] Admin can add one or more compliance control tags to audit entries (via join table)
- [ ] Admin can remove tags from entries
- [ ] Export can filter by compliance control tag for per-control evidence bundles
- [ ] Predefined compliance control catalog includes NIS2 Article 21, DORA Ch. II-V, ISO 27001 Annex A controls
- [ ] Predefined controls are read-only (cannot edit/delete)
- [ ] Admin can create custom controls with: code, name, framework, description
- [ ] Admin can deactivate custom controls (soft delete)
- [ ] Super admin can view paginated cross-company audit log with company name column
- [ ] Super admin can filter by: company, date range, actor, action type, resource type
- [ ] All audit UI/export/tagging endpoints return 402 for non-Enterprise plans
- [ ] Only admin role can access company audit endpoints; only super_admin can access cross-company endpoint
- [ ] i18n keys added for EN and ES (~50 keys)

## Technical Scope

### Entities (owned by this feature)

- **AuditEntryTag** — Join table linking audit entries to compliance controls
- **ComplianceControl** — Predefined + custom compliance framework controls

### Entities (used from dependencies)

- **AuditEntry** (from F0)

### Key Components

#### Domain Layer (`src/audit_bc/audit/domain/`)

- `entities.py` — Add `AuditEntryTag` and `ComplianceControl` dataclasses
- `exceptions.py` — Add `ControlNotFoundError`, `ControlCodeExistsError`, `PredefinedControlError`
- `repository.py` — Add abstract methods for tags and controls

#### Application Layer (`src/audit_bc/audit/application/`)

- `queries/list_audit_entries.py` — Paginated, filtered query
- `queries/get_audit_entry.py` — Detail with tags
- `queries/list_compliance_controls.py` — Predefined + custom for company
- `commands/create_compliance_control.py` — Create custom control
- `commands/update_compliance_control.py` — Update custom control
- `commands/deactivate_compliance_control.py` — Soft delete custom control
- `commands/add_audit_tags.py` — Add tags to entries (batch)
- `commands/remove_audit_tags.py` — Remove tags from entries (batch)
- `commands/request_audit_export.py` — Create export Celery task

#### Infrastructure Layer (`src/audit_bc/audit/infrastructure/`)

- `models.py` — Add `AuditEntryTagModel`, `ComplianceControlModel`
- `repository.py` — Implement tag and control repository methods

#### HTTP Layer (`adapters/http/api/audit/`)

- `schemas.py` — Request/response schemas for all endpoints
- `routers.py` — 10 endpoints: audit list, detail, export, verify, tag add, tag remove, controls CRUD
- `dependencies.py` — DI wiring

#### Super Admin HTTP (`adapters/http/api/super_admin/`)

- Add cross-company audit endpoint to super admin routers

#### Celery

- `core/tasks/audit.py` — `audit_export` task (CSV/PDF generation + MinIO upload)

#### Migration

- `alembic/versions/xxxx_create_audit_tags_and_controls.py` — Create `audit_entry_tags` and `compliance_controls` tables + seed predefined controls

#### Frontend

- `web/app/src/pages/admin/AuditLogPage.tsx` — Audit log list with filters
- `web/app/src/pages/admin/AuditEntryDetailPage.tsx` — Entry detail with tags
- `web/app/src/pages/admin/ComplianceControlsPage.tsx` — Controls management
- `web/app/src/pages/superadmin/CrossCompanyAuditPage.tsx` — Super admin view
- `web/app/src/router.tsx` — Add routes
- `web/app/src/components/layout/Sidebar.tsx` — Add nav items
- `web/app/src/types/index.ts` — Add TypeScript interfaces
- `web/app/src/locales/en.ts` + `es.ts` — i18n keys

## Notes

- The predefined compliance control catalog should be seeded via migration (not via seed script) so it's available in all environments.
- The export task reuses the `S3StorageService` pattern from E6 (report generation).
- Feature gating uses `PlanGate` from E43 — `audit_trail` is already in `_ENTERPRISE_FEATURES`.
