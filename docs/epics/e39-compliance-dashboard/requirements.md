# E39: Compliance Dashboard — Requirements

## Overview

Add compliance posture management to the IT service desk platform. Organizations need to track their compliance status against regulatory frameworks (NIS2, DORA, ISO 27001), collect evidence linking controls to incidents/risks/audit entries, visualize overall compliance posture, and generate audit-ready PDF exports.

## Business Goals

1. **Compliance Visibility** — Admins can see at a glance which controls are compliant, partial, non-compliant, or not yet assessed.
2. **Evidence Collection** — Link controls to evidence from across the platform (audit logs, incidents, risks, SLA data, manual uploads).
3. **Gap Analysis** — Identify non-compliant and unassessed controls to prioritize remediation.
4. **Audit Readiness** — Generate PDF compliance reports per framework for external auditors.

## Functional Requirements

### FR-1: Compliance Assessment
- Admins can assess each compliance control with a status: compliant, partial, non_compliant, not_assessed.
- One assessment per company+control (upsert semantics).
- Assessment includes optional notes and tracks who assessed and when.

### FR-2: Evidence Collection
- Admins can attach evidence items to any compliance control.
- Evidence types: audit_log, incident, risk, sla, manual.
- Evidence includes title, optional description, optional reference_id (cross-BC link), optional URL.
- Evidence can be removed.

### FR-3: Compliance Dashboard
- Dashboard shows overall compliance percentage, per-framework breakdown, and gap analysis.
- Framework filter to scope to a single framework.
- Gap controls section highlights non-compliant and not-assessed controls.
- Evidence coverage percentage shown.

### FR-4: PDF Report Export
- Admins can trigger async PDF generation via Celery.
- Report includes summary cards, per-framework control tables, gap analysis.
- Generated PDF uploaded to MinIO and downloadable via signed URL.
- Notification sent when report is ready.

## Non-Functional Requirements

- All endpoints gated behind `require_plan_feature("audit_trail")` (Enterprise plan).
- All endpoints require admin role.
- All entities live within the existing `audit_bc` bounded context.
- Evidence references entities from other BCs by ID only — no cross-BC imports or foreign keys.
- All new tables indexed appropriately for query performance.

## Out of Scope

- Automated evidence collection (e.g., auto-linking incidents to controls).
- Compliance control mapping editor (controls already managed via E29).
- Real-time compliance scoring updates via WebSocket.
