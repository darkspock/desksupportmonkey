# Feature 3: Retention & Integrity — Technical Design

**Epic:** E29 — Audit Trail & Compliance Evidence
**Feature:** F3 — Retention & Integrity
**Complexity:** S (Small)
**Dependencies:** F0 (Audit Foundation)

---

## Overview

Adds two capabilities to the audit system:
1. **Retention policies** — Per-company configurable retention periods for audit entries, with automatic weekly purge via Celery Beat
2. **Integrity verification** — On-demand hash verification of audit entries to detect tampering

---

## Domain

### RetentionPolicy Entity

```python
@dataclass
class RetentionPolicy:
    id: str
    company_id: str
    retention_months: int  # 12, 24, 36, 60, 84, 0=indefinite
    updated_at: Optional[datetime]
    updated_by: str
```

- No state machine (simple config)
- Default: 36 months (3 years) — aligns with NIS2/ISO requirements
- Valid values: 0 (indefinite), 12, 24, 36, 60, 84

### Repository Additions

Add to `AuditRepositoryInterface`:
- `save_retention_policy(policy: RetentionPolicy) -> None`
- `find_retention_policy(company_id: str) -> Optional[RetentionPolicy]`
- `find_all_retention_policies() -> list[RetentionPolicy]` (for Celery purge task)
- `delete_entries_before(company_id: str, before: datetime) -> int` (for purge)
- `find_entries_for_verification(company_id: str, date_from: datetime, date_to: datetime, page: int, page_size: int) -> list[AuditEntry]` (for verify task)

---

## Infrastructure

### RetentionPolicyModel

Table: `retention_policies`
- `id`: ULID PK
- `company_id`: FK companies.id, unique
- `retention_months`: Integer, not null, default 36
- `updated_at`: DateTime(tz), not null
- `updated_by`: FK users.id, not null

### Migration

- Creates `retention_policies` table
- Revises `f6g7h8i9j0k1` (last audit migration)

---

## Application Layer (CQRS)

### Commands

**UpdateRetentionPolicyCommand**
- Fields: company_id, retention_months, updated_by
- Validation: retention_months must be in [0, 12, 24, 36, 60, 84]
- Creates or updates RetentionPolicy (upsert pattern)

### Queries

**GetRetentionPolicyQuery**
- Fields: company_id
- Returns: RetentionPolicyDto (or defaults if none configured)

### DTOs

**RetentionPolicyDto**: id, company_id, retention_months, updated_at, updated_by

---

## HTTP Endpoints

All gated by `require_plan_feature("audit_trail")` + `require_role(ADMIN)`.
Must be placed BEFORE `/{entry_id}` catch-all in router.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/audit/retention` | Get current retention policy |
| PUT | `/api/v1/audit/retention` | Update retention policy |
| POST | `/api/v1/audit/verify` | Request integrity verification (async) |

### Schemas

- `UpdateRetentionRequest(retention_months: int)`
- `RetentionPolicyResponse(retention_months, updated_at, updated_by)`
- `VerifyIntegrityRequest(date_from?, date_to?)`
- `VerifyIntegrityResponse(task_id, status?, total_checked?, valid_count?, invalid_count?, first_invalid_entry_id?)`

---

## Celery Tasks

### verify_audit_integrity (on-demand)

- Triggered by POST /api/v1/audit/verify
- Iterates entries in chronological order for given company + date range
- Recomputes SHA-256 hash using `AuditEntry.compute_hash()`
- Compares with stored hash
- Returns result dict: total_checked, valid_count, invalid_count, first_invalid_entry_id

### retention_purge (scheduled — weekly)

- Celery Beat schedule: weekly on Sunday at 03:00 UTC
- For each company with a retention policy (retention_months > 0):
  1. Compute cutoff date = now - retention_months
  2. Before deleting, create a summary audit entry: "Purged N entries from [date] to [date]"
  3. Delete audit entries older than cutoff
  4. Log result

---

## Frontend

Add to existing AuditLogPage.tsx:
- **Retention settings** section: dropdown for retention period, save button
- **Verify Integrity** button: opens date range picker, triggers verification, shows results

---

## i18n

~15 new keys for retention settings and integrity verification UI.
