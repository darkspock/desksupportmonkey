# Epic E29: Audit Trail & Compliance Evidence

**Date:** 2026-02-24
**Priority:** High
**Status:** Approved
**Bounded Context:** `audit_bc`
**Plan Gate:** Enterprise (or Open Source mode)

---

## Business Alignment

**Objective:** Revenue & Churn — Enable Enterprise-tier customers to meet NIS2/DORA/ISO 27001 audit requirements without external tools, increasing upgrade conversions from Premium and reducing churn among regulated customers.

**KPI Targets:**
- 100% of write operations captured in the global audit log with actor, timestamp, IP, and resource identifiers
- Audit log entries are immutable (append-only) with per-entry hash integrity verification
- GDPR data export requests fulfilled in < 72 hours via automated pipeline
- Compliance evidence export generates auditor-ready PDF/CSV bundles per framework (NIS2, DORA, ISO 27001)
- Data retention policies automatically purge entries older than the configured retention window per company

**Evidence:**
- NIS2 Article 21 requires "policies and procedures to assess the effectiveness of cybersecurity risk-management measures" — audit logs are foundational evidence
- DORA Article 12 requires ICT-related incident reporting with full traceability — audit trail provides the chain of custody
- ISO 27001 Annex A control A.8.15 (Logging) mandates "event logs recording user activities, exceptions, faults and information security events shall be produced, kept, protected and regularly analyzed"
- No competitor under €500/month provides built-in compliance evidence tagging and export for SMBs — this is an Enterprise-tier differentiator

---

## Problem Statement

**Current situation:** DeskSupportMonkey has domain-specific event logs (`RequestEvent`, `AssetEvent`, `IncidentTimeline`, `RiskHistory`) that track mutations within individual bounded contexts. There is no centralized, system-wide audit trail that captures who did what, when, and from where across the entire platform.

**Pain points:**

| Problem | Impact |
|---|---|
| No centralized audit log | Cannot answer "what did user X do yesterday?" across the platform |
| No IP/user-agent capture | Cannot prove _from where_ an action was taken (required for ISO 27001 A.8.15) |
| No tamper-evidence | Existing event logs can be modified by anyone with DB access — insufficient for regulatory audits |
| No GDPR data export | Cannot fulfill "right of access" requests (GDPR Article 15) — manual process |
| No GDPR data deletion | Cannot fulfill "right to erasure" requests (GDPR Article 17) — no tooling |
| No compliance evidence tagging | Cannot map platform actions to specific NIS2/DORA/ISO 27001 controls |
| No retention policies | No automated data lifecycle management — risk of over-retention (violates GDPR minimization) and under-retention (violates audit requirements) |
| No audit export for external auditors | Auditors must request manual DB extracts — time-consuming and error-prone |

**Who is affected:** Company administrators, compliance officers, external auditors, data protection officers, and regulated SMBs subject to NIS2, DORA, or ISO 27001.

---

## Non-Goals (Out of Scope)

- **Real-time alerting on suspicious activity** — Future epic (E31 Workflow Automations could trigger on audit events)
- **Full SIEM integration** — No syslog/CEF/LEEF export in this epic
- **User behavior analytics** — No anomaly detection or ML-based analysis
- **Replacing domain-specific event logs** — `RequestEvent`, `AssetEvent`, `IncidentTimeline`, `RiskHistory` remain as domain events; E29 is a separate, centralized, cross-cutting audit log
- **Access review campaigns** — Periodic access certifications (noted in roadmap) deferred to future enhancement

---

## Proposed Solution

A new bounded context (`audit_bc`) with a centralized, append-only audit log that captures all write operations across the platform. The audit log is separate from domain event logs — it captures _who_ did _what_ from _where_, while domain events capture _what happened_ in business terms.

### Architecture Decisions

1. **Separate table, not a view over domain events** — Domain events have different schemas per BC and may not capture IP/user-agent. The audit log has a uniform schema optimized for compliance queries.

2. **FastAPI middleware for HTTP capture + explicit MCP capture** — An HTTP middleware intercepts all non-GET requests and emits an audit entry after the response. MCP tool calls are captured explicitly in the MCP handler/dispatcher layer, since mounted sub-apps (`app.mount()`) may bypass `BaseHTTPMiddleware`.

3. **Per-entry hash for tamper detection** — Each audit entry includes a SHA-256 hash of its own data (actor + action + resource + timestamp). This detects per-entry tampering without requiring chaining. No `previous_hash` field — avoids concurrency issues with concurrent writes for the same company. Chain linking across entries can be added as a future enhancement via a nightly batch job.

4. **Separate transaction, best-effort** — Audit entries are written in their own DB transaction, separate from the business operation's transaction. If the audit write fails, the error is logged but the business operation is not rolled back. This is simpler and more resilient than trying to share the handler's session via context vars.

5. **GDPR operations are Celery tasks** — Data export and anonymization are potentially expensive operations that run asynchronously.

6. **Feature-gated to Enterprise** — Audit log capture is always-on (for all plans), but the UI, search, export, and compliance features are gated to Enterprise tier. This ensures that if a company upgrades, historical audit data is available.

7. **Compliance tags in separate join table** — Tags are stored in an `audit_entry_tags` table rather than inline JSON on the AuditEntry. This preserves AuditEntry immutability — the entry itself is never updated after creation.

8. **Compliance control catalog: predefined + extensible** — The platform ships with a predefined catalog of NIS2 Article 21, DORA Ch. II-V, and ISO 27001 Annex A controls. Admins can add custom tags for internal controls or other frameworks.

### Validation Decisions (Closed)

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| V1 | Tag storage vs immutability | Separate `audit_entry_tags` join table | Preserves AuditEntry as truly immutable; hash is never invalidated |
| V2 | Transaction coupling | Separate transaction, best-effort | Middleware can't share handler's DB session; best-effort is simpler and resilient |
| V3 | Hash chain concurrency | Per-entry hash only, no chaining | Avoids concurrent write conflicts; chain linking deferred to future enhancement |
| V4 | MCP audit coverage | Explicit audit in MCP handler layer | Mounted sub-apps may bypass BaseHTTPMiddleware; explicit capture is reliable |
| V5 | GDPR request cancellation | Yes, add `cancelled` state | Admins need an undo for mistakes, especially irreversible anonymization |
| V6 | Remove compliance tags | Yes, add and remove | Admins must be able to correct tagging mistakes |
| V7 | Control catalog | Predefined + admin can add custom | Ships with NIS2/DORA/ISO controls; admins extend for internal frameworks |
| V8 | Super admin visibility | Yes, include in E29 | Super admin gets cross-company audit endpoint for platform investigations |

### User Stories

#### Admin / Compliance Officer

**US-E29-001: View audit log**
As an admin, I can view a paginated audit log of all actions performed in my company, so I can investigate who did what and when.

**Acceptance Criteria:**
- [ ] Paginated list showing: timestamp, actor (name + email), action, resource type, resource ID, IP address
- [ ] Filterable by: date range, actor, action type, resource type, compliance tag
- [ ] Searchable by resource ID or actor name
- [ ] Sorted by timestamp (newest first by default)
- [ ] Only admin role can access

**US-E29-002: View audit entry detail**
As an admin, I can view the full detail of an audit entry, including the before/after data diff and request metadata.

**Acceptance Criteria:**
- [ ] Shows: actor details, timestamp, action, resource type/ID, IP address, user agent
- [ ] Shows before/after JSON diff for update operations
- [ ] Shows the full request path and HTTP method
- [ ] Shows compliance tags applied to this entry
- [ ] Read-only — no edit or delete capability

**US-E29-003: Export audit log**
As an admin, I can export the audit log as CSV or PDF for a given date range, so I can provide evidence to external auditors.

**Acceptance Criteria:**
- [ ] Export formats: CSV, PDF
- [ ] Filter by date range (required), actor, action type, resource type, compliance tag
- [ ] CSV includes all fields; PDF is formatted as a compliance report
- [ ] Export runs as async Celery task (returns download link when complete)
- [ ] Stored in MinIO with signed URL (1h expiry), same pattern as report generation (E6)

**US-E29-004: Tag audit entries with compliance controls**
As an admin, I can add or remove compliance control tags on audit entries, so I can build and correct compliance evidence packages.

**Acceptance Criteria:**
- [ ] Admin can add one or more control tags to any audit entry (e.g., "NIS2-Art21-d", "ISO27001-A.8.15")
- [ ] Admin can remove tags from entries (correct mistakes)
- [ ] Tags are stored in a separate `audit_entry_tags` join table (AuditEntry remains immutable)
- [ ] Tags can be filtered in the audit log view
- [ ] Export can filter by control tag to produce per-control evidence bundles

**US-E29-005: Manage compliance control catalog**
As an admin, I can view the predefined compliance controls and add custom controls for my company.

**Acceptance Criteria:**
- [ ] Predefined catalog includes: NIS2 Article 21 measures, DORA Ch. II-V controls, ISO 27001 Annex A controls
- [ ] Predefined controls are read-only (cannot be edited or deleted)
- [ ] Admin can create custom controls with: code, name, framework (optional), description (optional)
- [ ] Custom controls appear alongside predefined controls in the tag picker
- [ ] Admin can deactivate (soft-delete) custom controls

**US-E29-006: Verify audit log integrity**
As an admin, I can run an integrity check on the audit log to verify no entries have been tampered with.

**Acceptance Criteria:**
- [ ] "Verify Integrity" button on audit log page
- [ ] Runs per-entry hash verification over the selected date range
- [ ] Recomputes SHA-256 hash from entry data and compares with stored hash
- [ ] Reports: total entries checked, result (valid/broken), first broken entry if any
- [ ] Runs as async task with progress indicator

#### Data Protection Officer

**US-E29-007: GDPR data export**
As an admin, I can request a full data export for a specific user (GDPR Article 15 — right of access), so the company can respond to data subject requests.

**Acceptance Criteria:**
- [ ] Admin enters user email or ID
- [ ] System generates a ZIP file containing all personal data across all BCs: user profile, assets assigned, requests created, comments, notifications, audit entries where they are the actor or subject
- [ ] Export runs as async Celery task
- [ ] Download link sent via email to the requesting admin
- [ ] Export stored in MinIO with signed URL (24h expiry)

**US-E29-008: GDPR data anonymization**
As an admin, I can request anonymization of a user's personal data (GDPR Article 17 — right to erasure), so the company can comply with deletion requests while preserving audit integrity.

**Acceptance Criteria:**
- [ ] Admin enters user email or ID + reason
- [ ] System anonymizes (not deletes) personal data: replaces name/email with "Anonymized User [hash]", clears profile fields
- [ ] Audit log entries are preserved but actor_email references are anonymized
- [ ] Domain events (RequestEvent, AssetEvent, etc.) — no denormalized PII (only FKs), so no changes needed
- [ ] User record is marked `is_anonymized = True`
- [ ] Anonymization is irreversible and logged in the audit trail
- [ ] Runs as async Celery task with confirmation step

**US-E29-009: Cancel pending GDPR request**
As an admin, I can cancel a pending GDPR request before processing starts, so I can correct mistakes.

**Acceptance Criteria:**
- [ ] Cancel button shown only when status = pending
- [ ] Cancellation sets status to `cancelled`
- [ ] Cancelled requests are kept in the list for audit purposes
- [ ] Cannot cancel once status = processing (task already running)

#### Admin (Retention)

**US-E29-010: Configure data retention policy**
As an admin, I can configure how long audit log entries are retained before automatic purging.

**Acceptance Criteria:**
- [ ] Retention period options: 1 year, 2 years, 3 years, 5 years, 7 years, indefinite
- [ ] Default: 3 years (aligns with typical NIS2/ISO requirements)
- [ ] Retention applies to the audit log only (domain events have their own lifecycle)
- [ ] Purge runs as a scheduled Celery task (weekly)
- [ ] Purged entries are logged (count + date range) in the audit log itself before deletion
- [ ] Admin is warned if setting retention below 2 years ("Regulatory minimum for NIS2")

#### Super Admin

**US-E29-011: Cross-company audit log**
As a super admin, I can view the audit log across all companies for platform-level investigations.

**Acceptance Criteria:**
- [ ] Paginated list with same columns as company audit log + company name column
- [ ] Filterable by: company, date range, actor, action type, resource type
- [ ] Searchable by resource ID, actor name, or company name
- [ ] Only super_admin role can access
- [ ] No compliance tagging or export from this view (company-level feature)

---

## Entities

| Entity | Description | States | Delete Strategy |
|--------|-------------|--------|-----------------|
| AuditEntry | A single audit log record capturing one action | N/A (immutable, no state machine) | Purge by retention policy only |
| AuditEntryTag | Join table linking audit entries to compliance controls | N/A (simple association) | Cascade on audit entry purge; admin can remove |
| ComplianceControl | A compliance framework control (predefined or custom) | active / inactive | Soft delete (deactivate) for custom; predefined are permanent |
| GdprRequest | A data export or anonymization request | pending → processing → completed / failed / cancelled | Kept indefinitely for audit purposes |
| RetentionPolicy | Per-company configuration for audit data retention | N/A (simple config) | Reset to default on delete |

### AuditEntry (Primary Entity — Immutable)

```
AuditEntry:
  id: ULID (PK)
  company_id: str (FK → companies.id, indexed)
  actor_id: str (FK → users.id, nullable — null for system actions)
  actor_email: str (denormalized for post-anonymization readability)
  action: str (e.g., "asset.created", "request.status_changed", "user.deactivated")
  resource_type: str (e.g., "asset", "request", "user", "incident", "risk")
  resource_id: str (nullable — some actions don't target a resource)
  http_method: str (POST/PUT/PATCH/DELETE)
  http_path: str (request path)
  ip_address: str (nullable)
  user_agent: str (nullable)
  request_data: JSON (nullable — sanitized request body, no passwords/tokens)
  response_status: int (HTTP status code)
  changes: JSON (nullable — before/after diff for update operations)
  hash: str (SHA-256 of entry data for tamper detection)
  created_at: datetime (immutable)
```

**Indexes:** `(company_id, created_at)`, `(company_id, actor_id, created_at)`, `(company_id, resource_type, resource_id)`

**Sanitized fields** (redacted from request_data): `password`, `password_hash`, `token`, `magic_link`, `secret`, `stripe_secret_key`, `credentials`

### AuditEntryTag (Join Table)

```
AuditEntryTag:
  id: ULID (PK)
  audit_entry_id: str (FK → audit_entries.id, indexed)
  control_id: str (FK → compliance_controls.id)
  tagged_by: str (FK → users.id)
  created_at: datetime
```

**Unique constraint:** `(audit_entry_id, control_id)`

### ComplianceControl

```
ComplianceControl:
  id: ULID (PK)
  company_id: str (FK, nullable — null for predefined/global controls)
  code: str (e.g., "NIS2-Art21-d", "ISO27001-A.8.15", "CUSTOM-001")
  name: str (e.g., "Incident handling and response")
  framework: str (nullable — e.g., "NIS2", "DORA", "ISO 27001", "Custom")
  description: str (nullable)
  is_predefined: bool (true for shipped controls, false for custom)
  is_active: bool (default true)
  created_at: datetime
```

**Unique constraint:** `(company_id, code)` — allows same code across companies for custom controls

### GdprRequest

```
GdprRequest:
  id: ULID (PK)
  company_id: str (FK)
  request_type: enum (export | anonymize)
  target_user_id: str (FK → users.id)
  target_user_email: str (denormalized)
  reason: str (nullable)
  status: enum (pending | processing | completed | failed | cancelled)
  requested_by: str (FK → users.id)
  result_file_url: str (nullable — signed URL for export ZIP)
  error_message: str (nullable)
  created_at: datetime
  started_at: datetime (nullable)
  completed_at: datetime (nullable)
```

### State Machine: GdprRequest

```
[pending] → processing → completed
    ↓                 ↘ failed
 cancelled
```

| From | To | Trigger | Conditions | Side Effects |
|------|----|---------|------------|--------------|
| pending | processing | Celery task picks up | — | Sets started_at |
| pending | cancelled | Admin cancels | Status must be pending | — |
| processing | completed | Task finishes | Data exported/anonymized | Sets completed_at, result URL |
| processing | failed | Task error | — | Sets error_message |

### RetentionPolicy

```
RetentionPolicy:
  id: ULID (PK)
  company_id: str (FK, unique)
  retention_months: int (12, 24, 36, 60, 84, or 0 for indefinite)
  updated_at: datetime
  updated_by: str (FK → users.id)
```

---

## Use Cases

### UC-001: Automatic Audit Capture (HTTP Middleware)

**Actor:** System (automatic)
**Preconditions:** Any authenticated user makes a non-GET HTTP request
**Postconditions:** AuditEntry created in a separate transaction (best-effort)

**Main Flow:**
1. User sends POST/PUT/PATCH/DELETE request
2. Route handler processes the request and commits its own transaction
3. Middleware intercepts after route handler completes
4. Middleware extracts: actor from JWT, IP from `request.client.host`, user-agent from headers, resource type/ID from path, response status
5. For PUT/PATCH: if the handler provides `changes` (before/after via a ContextVar), include in the entry
6. Compute SHA-256 hash of entry data: `hash(company_id + actor_id + action + resource_type + resource_id + created_at)`
7. Open a new DB session and insert AuditEntry
8. Commit the audit transaction independently

**Alternative Flows:**
- A1: Unauthenticated request (e.g., registration) — actor_id is null, action is "auth.register"
- A2: Request body contains sensitive fields (password, token) — sanitize before storing
- A3: Route handler returns error (4xx/5xx) — still capture the audit entry (records failed attempts)

**Error Scenarios:**
- E1: Audit DB write fails — log error, do NOT rollback the business operation

### UC-002: Automatic Audit Capture (MCP Tools)

**Actor:** System (automatic)
**Preconditions:** MCP client calls a write tool (create, update, delete, assign, etc.)
**Postconditions:** AuditEntry created

**Main Flow:**
1. MCP tool dispatcher receives a write tool call
2. Tool handler executes the command
3. After successful execution, dispatcher creates an AuditEntry with:
   - actor_id from MCP session context
   - action derived from tool name (e.g., "mcp.create_asset")
   - resource_type/resource_id from tool arguments
   - http_method = "MCP", http_path = tool name
   - ip_address from MCP connection
4. Compute hash and insert in separate transaction

### UC-003: Search Audit Log

**Actor:** Admin
**Preconditions:** User has admin role, company has Enterprise plan (or open source mode)
**Postconditions:** Paginated results returned

**Main Flow:**
1. Admin navigates to Settings > Audit Log
2. System shows paginated log (newest first)
3. Admin applies filters (date range, actor, action type, resource type, compliance tag)
4. System returns filtered results
5. Admin clicks an entry to see full detail

### UC-004: Export Audit Log

**Actor:** Admin
**Preconditions:** Enterprise plan
**Postconditions:** Export file available for download

**Main Flow:**
1. Admin sets date range and optional filters
2. Admin clicks "Export CSV" or "Export PDF"
3. System creates async Celery task
4. Task queries audit entries, generates file, uploads to MinIO
5. Admin receives notification with download link
6. Link expires after 1 hour

### UC-005: Tag/Untag Entries with Compliance Controls

**Actor:** Admin
**Preconditions:** Enterprise plan
**Postconditions:** Entries tagged/untagged via join table, filterable by control

**Main Flow:**
1. Admin selects one or more audit entries
2. Admin picks control tags from catalog (predefined + custom)
3. System inserts rows in `audit_entry_tags` join table (AuditEntry is not mutated)
4. Admin can filter audit log by tag
5. Admin can export entries filtered by a specific control tag

**Alternative Flow:**
- A1: Admin selects entries and removes existing tags — system deletes corresponding rows from `audit_entry_tags`

### UC-006: Manage Compliance Control Catalog

**Actor:** Admin
**Preconditions:** Enterprise plan
**Postconditions:** Custom control created/deactivated

**Main Flow:**
1. Admin navigates to Settings > Compliance Controls
2. System shows predefined controls (read-only) + custom controls
3. Admin creates a custom control: code, name, framework (optional), description
4. Custom control appears in the tag picker alongside predefined controls

**Alternative Flow:**
- A1: Admin deactivates a custom control — control is soft-deleted (is_active = false), no longer appears in tag picker, existing tags remain

### UC-007: Verify Integrity

**Actor:** Admin
**Preconditions:** Enterprise plan, audit entries exist
**Postconditions:** Integrity report displayed

**Main Flow:**
1. Admin selects date range and clicks "Verify Integrity"
2. System creates async task
3. Task iterates entries in chronological order, recomputing SHA-256 hash from entry data
4. Task compares computed hash with stored hash
5. Returns report: entries checked, valid/invalid, first broken entry details

### UC-008: GDPR Data Export

**Actor:** Admin
**Preconditions:** Enterprise plan, target user exists
**Postconditions:** ZIP file with all user's personal data

**Main Flow:**
1. Admin goes to Settings > GDPR Requests > New Export
2. Admin enters user email, confirms
3. System creates GdprRequest (status: pending)
4. Celery task collects data from all BCs: user profile, assigned assets, created requests, comments, notifications, audit entries
5. Task generates ZIP, uploads to MinIO
6. Status → completed, admin notified with download link (24h expiry)

### UC-009: GDPR Data Anonymization

**Actor:** Admin
**Preconditions:** Enterprise plan, target user exists, user not already anonymized
**Postconditions:** User's personal data anonymized across all BCs

**Main Flow:**
1. Admin goes to Settings > GDPR Requests > New Anonymization
2. Admin enters user email, reason, confirms with "I understand this is irreversible"
3. System creates GdprRequest (status: pending)
4. Celery task anonymizes data:
   - users: replace name, email → "Anonymized User [hash6]", clear google_id, microsoft_id, password_hash, set is_anonymized = true
   - audit_entries: replace actor_email → "Anonymized User [hash6]"
   - notifications: anonymize body/data containing user references
5. Task creates an audit entry documenting the anonymization
6. Status → completed

**Error Scenarios:**
- E1: Cannot anonymize super_admin — rejected
- E2: Cannot anonymize the requesting admin themselves — rejected
- E3: User already anonymized (is_anonymized = true) — return conflict

### UC-010: Cancel Pending GDPR Request

**Actor:** Admin
**Preconditions:** GdprRequest status = pending
**Postconditions:** Request cancelled

**Main Flow:**
1. Admin opens GDPR request detail
2. Admin clicks "Cancel"
3. System sets status → cancelled
4. Request remains in the list for audit purposes

**Error Scenarios:**
- E1: Request already processing/completed/failed — return conflict

### UC-011: Configure Retention Policy

**Actor:** Admin
**Preconditions:** Enterprise plan
**Postconditions:** Retention policy saved

**Main Flow:**
1. Admin navigates to Settings > Audit Log > Retention
2. Admin selects retention period from dropdown
3. If < 24 months, system shows warning about NIS2 minimum
4. Admin confirms
5. System saves/updates RetentionPolicy

**Side Effects:**
- Weekly Celery beat task checks retention policies and purges expired entries
- Before purging, creates a summary audit entry ("Purged N entries from [date] to [date]")

### UC-012: Super Admin Cross-Company Audit

**Actor:** Super Admin
**Preconditions:** User has super_admin role
**Postconditions:** Cross-company audit results returned

**Main Flow:**
1. Super admin navigates to Super Admin > Audit Log
2. System shows paginated log across all companies (newest first)
3. Super admin filters by: company, date range, actor, action type, resource type
4. Super admin clicks entry to see full detail

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| **All HTTP routers** | Middleware captures all write operations | Add audit middleware to FastAPI app |
| **MCP handler layer** | Explicit audit capture for MCP write tool calls | Add audit emission in MCP tool dispatcher |
| **Auth dependencies** | Need IP/user-agent from request | Middleware has native access via `request.client.host` and `request.headers` |
| **Celery tasks** | New tasks: audit_export, gdpr_export, gdpr_anonymize, retention_purge | Register in `core/tasks/` |
| **Celery Beat** | Retention purge needs weekly schedule | Add to beat schedule config |
| **MinIO/S3** | Store export files (CSV, PDF, ZIP) | Reuse existing `S3StorageService` pattern from E6 |
| **Feature gating (E43)** | `audit_trail` feature key already in Enterprise | UI endpoints return 402 for non-Enterprise; capture still runs for all plans |
| **User entity** | Anonymization modifies user records | Add `is_anonymized: bool` to User domain entity + UserModel + migration |
| **Notification BC** | Notify admin when export/anonymization completes | Add new notification event types |
| **Sidebar/Routing** | New admin pages: Audit Log, GDPR Requests, Compliance Controls | Add routes and nav items |
| **Super Admin pages** | New super admin page: Cross-Company Audit | Add route and nav item |
| **i18n** | ~60 new translation keys | Add to en.ts and es.ts |
| **DB performance** | audit_entries will be the highest-volume table | Composite indexes required (see entity definition) |

---

## API Endpoints

### Audit Log

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/audit` | admin | List audit entries (paginated, filterable) |
| GET | `/api/v1/audit/{id}` | admin | Get audit entry detail (includes tags) |
| POST | `/api/v1/audit/export` | admin | Request audit log export (async) |
| POST | `/api/v1/audit/verify` | admin | Request integrity verification (async) |

### Compliance Tags

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/v1/audit/entries/tag` | admin | Add tags to audit entries (batch) |
| DELETE | `/api/v1/audit/entries/tag` | admin | Remove tags from audit entries (batch) |

### Compliance Controls

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/audit/controls` | admin | List all controls (predefined + custom) |
| POST | `/api/v1/audit/controls` | admin | Create custom control |
| PUT | `/api/v1/audit/controls/{id}` | admin | Update custom control |
| DELETE | `/api/v1/audit/controls/{id}` | admin | Deactivate custom control (soft delete) |

### GDPR

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/gdpr/requests` | admin | List GDPR requests |
| GET | `/api/v1/gdpr/requests/{id}` | admin | Get GDPR request status/detail |
| POST | `/api/v1/gdpr/export` | admin | Request data export for a user |
| POST | `/api/v1/gdpr/anonymize` | admin | Request data anonymization for a user |
| POST | `/api/v1/gdpr/requests/{id}/cancel` | admin | Cancel pending GDPR request |

### Retention

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/audit/retention` | admin | Get current retention policy |
| PUT | `/api/v1/audit/retention` | admin | Update retention policy |

### Super Admin

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/super-admin/audit` | super_admin | Cross-company audit log (paginated, filterable) |

---

## Acceptance Criteria (Definition of Done)

### Functional
- [ ] All POST/PUT/PATCH/DELETE HTTP requests automatically generate an audit entry via middleware
- [ ] All MCP write tool calls automatically generate an audit entry via explicit capture
- [ ] Audit entries include: actor, action, resource, IP, user-agent, timestamp, response status
- [ ] Per-entry SHA-256 hash is computed and stored for tamper detection
- [ ] Audit entries are truly immutable (no UPDATE after creation; tags are in separate join table)
- [ ] Audit log UI shows paginated, filterable, searchable entries (admin only)
- [ ] Audit entry detail shows full metadata, before/after diff, and compliance tags
- [ ] CSV and PDF export works via async Celery task
- [ ] Compliance tags can be added to and removed from entries via join table
- [ ] Predefined compliance control catalog ships with NIS2/DORA/ISO 27001 controls
- [ ] Admins can create custom compliance controls
- [ ] Integrity verification recomputes hashes and detects tampered entries
- [ ] GDPR data export generates ZIP with all user's personal data
- [ ] GDPR anonymization replaces personal data and sets `is_anonymized = true`
- [ ] GDPR requests can be cancelled while pending
- [ ] Retention policy configurable per company (1-7 years or indefinite)
- [ ] Automatic purge runs weekly based on retention policy
- [ ] Feature-gated to Enterprise plan (capture runs for all; UI/export gated)
- [ ] Super admin can view cross-company audit log
- [ ] Request body is sanitized before storage (passwords, tokens, secrets redacted)

### Non-Functional
- [ ] Audit middleware adds < 5ms overhead per request
- [ ] Hash computation is non-blocking (computed inline, not deferred)
- [ ] Export handles up to 100K entries without timeout
- [ ] Anonymization handles up to 50K records per user without timeout
- [ ] Audit entries are write-once (no UPDATE/DELETE except by retention purge)

### Testing
- [ ] Unit tests: AuditEntry entity, hash computation, GdprRequest lifecycle, ComplianceControl CRUD
- [ ] Unit tests: All command/query handlers
- [ ] Integration tests: Middleware captures HTTP requests, MCP capture, audit endpoints, GDPR endpoints
- [ ] Integration tests: Hash verification, retention purge, tag add/remove
- [ ] Integration tests: Plan gating returns 402 for non-Enterprise

### Infrastructure
- [ ] Alembic migration for: audit_entries, audit_entry_tags, compliance_controls, gdpr_requests, retention_policies tables
- [ ] Alembic migration to add `is_anonymized` column to users table
- [ ] Celery tasks registered and functional
- [ ] Celery Beat schedule for retention purge
- [ ] Predefined compliance controls seeded via migration
- [ ] i18n keys for EN and ES

---

## Time Constraints

**Deadline:** None (no hard deadline)
**Type:** Soft
**Dependencies:**
- E43 (Billing) — for plan gating (already implemented)
- E6 (Report Generation) — for async export pattern (already implemented)
- No blocking dependencies — can start immediately

---

## Resolved Questions

1. **Should audit capture include GET requests?** — No (too noisy). Could add as opt-in in a future enhancement.
2. **Should the hash be per-entry or chained?** — Per-entry hash only. Avoids concurrency issues. Chain linking deferred to future enhancement.
3. **Should anonymized users' audit entries show "Anonymized User" or be removed?** — Show "Anonymized User [hash6]" to preserve audit trail while removing PII.
4. **Should middleware capture request body for all endpoints?** — Yes, for all write operations, but sanitize sensitive fields (passwords, tokens, magic links, stripe keys, credentials).
5. **Compliance control catalog?** — Ship predefined NIS2/DORA/ISO controls. Admins can add custom controls.
6. **Tag storage?** — Separate `audit_entry_tags` join table to preserve AuditEntry immutability.
7. **Transaction model?** — Separate transaction, best-effort. Business operation not affected by audit write failures.
8. **MCP coverage?** — Explicit audit capture in MCP handler/dispatcher layer.
9. **GDPR cancellation?** — Yes, pending requests can be cancelled.
10. **Super admin visibility?** — Yes, cross-company audit endpoint included.
