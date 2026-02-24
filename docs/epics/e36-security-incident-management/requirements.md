# Epic E36: Security Incident Management (NIS2)

**Date:** 2026-02-23
**Priority:** High
**Status:** Pending
**Bounded Context:** `incident_bc`

---

## Business Alignment

**Objective:** Provide SMBs with a purpose-built security incident lifecycle that enforces NIS2 Article 21 regulatory reporting timelines, eliminating the need for external tools or manual tracking.

**KPI Targets:**
- Every security incident has a complete audit trail from detection to closure
- NIS2 24h/72h/30d regulatory deadlines are enforced with countdown timers and escalation alerts
- Auto-generated CSIRT notification reports reduce manual compliance effort to near zero
- Security incidents are cross-referenced with affected assets, providing full impact visibility

**Evidence:** NIS2 Article 21 requires incident reporting within 24 hours (early warning), 72 hours (detailed report), and 30 days (final report). No competitor under €500/month offers this at SMB level. This is our primary differentiator.

---

## Problem Statement

**Current situation:** DeskSupportMonkey handles service requests (E3) for IT operations — equipment issues, onboarding, repairs. These are operational incidents, not security incidents.

**Pain points:**

| Problem | Impact |
|---|---|
| No security incident lifecycle | Companies cannot track breaches, malware, or unauthorized access within the platform |
| No NIS2 reporting timeline enforcement | IT managers risk regulatory penalties by missing 24h/72h deadlines |
| No auto-generated regulatory reports | Manual report creation is error-prone and time-consuming |
| No severity classification for security events | Cannot prioritize response or allocate resources properly |
| No cross-reference between security incidents and assets | Cannot answer "which devices were affected?" during an incident |

**Who is affected:** IT managers, security officers, and company administrators at NIS2-regulated SMBs (10-300 employees).

---

## Proposed Solution

A new bounded context (`incident_bc`) separate from service requests, with its own lifecycle, severity model, and NIS2-specific regulatory features.

### User Stories

#### IT Manager / Security Officer

1. As an IT manager, I can create a security incident with mandatory classification fields (type, severity, attack vector, affected systems), so the incident is properly documented from the start.

2. As an IT manager, I can move a security incident through a defined lifecycle (detected → triaged → contained → eradicated → recovered → closed), so every phase of incident response is tracked.

3. As an IT manager, I can see countdown timers for NIS2 regulatory deadlines (24h early warning, 72h detailed report, 30d final report), so I never miss a compliance deadline.

4. As an IT manager, I can generate pre-filled regulatory notification reports (PDF) with one click, so CSIRT reporting takes minutes instead of hours.

5. As an IT manager, I can link affected assets to a security incident, so I know exactly which devices and systems were compromised.

6. As an IT manager, I can link a vendor to a security incident when a third party is involved, so supply chain incidents are properly tracked.

7. As an IT manager, I can create a post-mortem for a closed incident with root cause analysis, lessons learned, and corrective actions, so the organization improves its security posture.

8. As an IT manager, I can view an incident dashboard showing active incidents, severity distribution, mean time to contain (MTTC), and incidents by type, so I have real-time operational visibility.

#### Company Administrator

9. As an admin, I receive escalation notifications when a regulatory deadline is approaching (at 75% and 90% of elapsed time), so I can intervene before a breach of compliance.

10. As an admin, I can view a list of all security incidents with filters by status, severity, type, and date range, so I can monitor the security posture of my organization.

#### Employee

11. As an employee, I can report a suspected security incident (phishing email, suspicious activity) through a simplified form, so security events are captured quickly without requiring technical knowledge.

---

## Entities & States

### SecurityIncident (aggregate root)

| Field | Type | Required | Description |
|---|---|---|---|
| id | ULID | Auto | Unique identifier |
| company_id | ULID | Auto | Tenant isolation |
| title | string(200) | Yes | Short description |
| description | text | Yes | Detailed description of the incident |
| incident_type | enum | Yes | malware, data_breach, ddos, unauthorized_access, phishing, ransomware, other |
| severity | enum | Yes | P1 (critical), P2 (high), P3 (medium), P4 (low) |
| status | enum | Auto | detected, triaged, contained, eradicated, recovered, closed |
| attack_vector | string(500) | No | How the attack was carried out |
| data_breach_scope | text | No | Estimated scope of data breach (if applicable) |
| reported_by | ULID | Auto | User who created the incident |
| assigned_to | ULID | No | Technician/manager responsible |
| detected_at | datetime | Yes | When the incident was first detected |
| created_at | datetime | Auto | Record creation timestamp |
| updated_at | datetime | Auto | Last update timestamp |
| close_reason | text | Conditional | Mandatory justification when closing from any active state (false alarm, duplicate, etc.). Not required for normal recovered→closed transition. |
| closed_at | datetime | Auto | When status changed to closed |

### IncidentAsset (link table)

| Field | Type | Required | Description |
|---|---|---|---|
| id | ULID | Auto | Unique identifier |
| incident_id | ULID | Yes | Reference to SecurityIncident |
| asset_id | ULID | Yes | Reference to Asset |
| impact_description | text | No | How this asset was affected |

### IncidentVendor (link table)

| Field | Type | Required | Description |
|---|---|---|---|
| id | ULID | Auto | Unique identifier |
| incident_id | ULID | Yes | Reference to SecurityIncident |
| vendor_id | ULID | Yes | Reference to Vendor |
| involvement_description | text | No | How the vendor is involved |

### RegulatoryReport

| Field | Type | Required | Description |
|---|---|---|---|
| id | ULID | Auto | Unique identifier |
| incident_id | ULID | Yes | Reference to SecurityIncident |
| report_type | enum | Yes | early_warning_24h, detailed_72h, final_30d |
| status | enum | Auto | pending, generated, submitted |
| deadline_at | datetime | Auto | Calculated from detected_at + offset |
| generated_at | datetime | No | When the PDF was generated |
| submitted_at | datetime | No | When marked as submitted to CSIRT |
| file_path | string | No | S3 path to generated PDF |

### IncidentTimeline (append-only event log)

| Field | Type | Required | Description |
|---|---|---|---|
| id | ULID | Auto | Unique identifier |
| incident_id | ULID | Yes | Reference to SecurityIncident |
| event_type | enum | Yes | status_change, severity_change, assignment, comment, asset_linked, asset_unlinked, vendor_linked, vendor_unlinked, report_generated, report_regenerated, report_submitted, escalation |
| description | text | Yes | Human-readable event description |
| actor_id | ULID | Yes | User who performed the action |
| created_at | datetime | Auto | Timestamp |
| metadata | jsonb | No | Additional structured data |

### PostMortem

| Field | Type | Required | Description |
|---|---|---|---|
| id | ULID | Auto | Unique identifier |
| incident_id | ULID | Yes | Reference to SecurityIncident (one-to-one) |
| root_cause | text | Yes | What caused the incident |
| lessons_learned | text | Yes | What the organization learned |
| corrective_actions | text | Yes | Actions taken or planned to prevent recurrence |
| created_by | ULID | Auto | Author |
| created_at | datetime | Auto | Timestamp |
| updated_at | datetime | Auto | Last update |

### State Machine: SecurityIncident

```
detected → triaged → contained → eradicated → recovered → closed
                                                            ↑
(any active state can skip to closed if false alarm)  ──────┘
```

**Transitions:**
- `detected → triaged`: Initial assessment complete, severity confirmed
- `triaged → contained`: Threat is isolated, no longer spreading
- `contained → eradicated`: Root cause removed from all systems
- `eradicated → recovered`: Systems restored to normal operation
- `recovered → closed`: Incident response complete, post-mortem done
- `any active → closed`: False alarm or duplicate (requires `close_reason` field to be filled)

### State Machine: RegulatoryReport

```
pending → generated → submitted
```

- `pending`: Deadline is set, report not yet created
- `generated`: PDF has been auto-generated (can be regenerated; new PDF replaces previous, timeline logs each generation)
- `submitted`: User confirmed the report was sent to CSIRT

---

## Use Cases

### UC1: Create Security Incident (Happy Path)

**Actor:** IT Manager / Technician
**Precondition:** User has technician or admin role

1. User navigates to Security Incidents page
2. User clicks "New Incident"
3. System shows creation form with mandatory fields: title, description, incident_type, severity, detected_at
4. User fills mandatory fields and optionally: attack_vector, data_breach_scope, affected assets, involved vendor
5. User clicks "Create"
6. System creates the incident in `detected` status
7. System auto-creates three RegulatoryReport records (24h, 72h, 30d) with calculated deadlines based on `detected_at`
8. System creates a timeline entry: "Incident created"
9. System sends notification to all admins: "New security incident: {title} (severity: {severity})"
10. User sees the incident detail page with timeline and regulatory deadline countdown

### UC2: Advance Incident Status

**Actor:** IT Manager / Technician (assigned or admin)

1. User opens incident detail page
2. User clicks next status transition button (e.g., "Mark as Triaged")
3. System shows confirmation dialog
4. User confirms
5. System updates status and creates timeline entry
6. System sends notification to assigned user and admins

### UC3: Generate Regulatory Report

**Actor:** IT Manager / Admin

1. User opens incident detail page
2. User sees regulatory reports section with 24h/72h/30d deadlines and countdown timers
3. User clicks "Generate Report" on a specific deadline
4. System generates PDF pre-filled with: incident details, timeline, affected assets, severity, current status
5. System uploads PDF to S3 and updates RegulatoryReport record
6. User can download the PDF
7. If incident data has changed, user can click "Regenerate Report" — new PDF replaces the previous one, timeline logs the regeneration
8. User clicks "Mark as Submitted" after sending to CSIRT
9. System updates submission timestamp and creates timeline entry

### UC4: Escalation Alert (Automated)

**Actor:** System

1. System periodically checks regulatory report deadlines (via Celery beat task)
2. When elapsed time reaches 75% of deadline → send warning notification to assigned user and admins
3. When elapsed time reaches 90% of deadline → send urgent notification to all admins
4. When deadline passes without submission → send critical alert to all admins

### UC5: Link Assets to Incident

**Actor:** IT Manager / Technician

1. User opens incident detail page
2. User clicks "Add Affected Asset"
3. System shows asset search/selector (from company's asset inventory)
4. User selects one or more assets and optionally adds impact description
5. System creates IncidentAsset records and timeline entry

### UC6: Create Post-Mortem

**Actor:** IT Manager / Admin
**Precondition:** Incident status is `recovered` or `closed`

1. User opens incident detail page
2. User clicks "Create Post-Mortem"
3. System shows form with: root_cause, lessons_learned, corrective_actions
4. User fills and submits
5. System creates PostMortem record and timeline entry

### UC7: Employee Reports Suspected Incident

**Actor:** Employee

1. Employee navigates to "Report Security Incident" (accessible from My Activity section)
2. System shows simplified form: title, description, incident_type (dropdown)
3. Employee fills and submits
4. System creates incident in `detected` status with P3 (medium) default severity
5. System notifies admins and technicians

### UC8: View Incident Dashboard

**Actor:** IT Manager / Admin / Technician

1. User navigates to Security Incidents dashboard
2. System shows:
   - Active incidents count by severity
   - Incidents by type (pie/bar chart data)
   - Mean Time to Contain (MTTC) — average time from detected to contained
   - Mean Time to Resolve (MTTR) — average time from detected to closed
   - Upcoming regulatory deadlines (next 7 days)
   - Recent incidents list

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `asset_bc` | Assets referenced by IncidentAsset link table | Read-only cross-BC query via asset_id |
| `procurement_bc` (vendors) | Vendors referenced by IncidentVendor link table | Read-only cross-BC query via vendor_id |
| `notification_bc` | New notification events for incidents | Add incident notification types |
| `report_bc` | PDF generation reuse (Celery + WeasyPrint + S3) | Reuse existing infrastructure, add incident report templates |
| Frontend navigation | New "Security" section in sidebar | Add nav items for incidents list, dashboard, and employee reporting |
| Database | New tables: security_incidents, incident_assets, incident_vendors, regulatory_reports, incident_timeline, post_mortems | New Alembic migration |
| Celery | New periodic task for deadline monitoring | Add beat schedule entry |

---

## API Endpoints

### Incidents CRUD

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/api/v1/incidents` | technician, admin | Create security incident |
| GET | `/api/v1/incidents` | technician, admin | List incidents (paginated, filterable) |
| GET | `/api/v1/incidents/{id}` | technician, admin | Get incident detail with timeline |
| PUT | `/api/v1/incidents/{id}` | technician, admin | Update incident fields |
| POST | `/api/v1/incidents/{id}/status` | technician, admin | Change incident status |
| POST | `/api/v1/incidents/{id}/severity` | technician, admin | Change incident severity |
| POST | `/api/v1/incidents/{id}/assign` | admin | Assign incident to user |

### Affected Assets & Vendors

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/api/v1/incidents/{id}/assets` | technician, admin | Link asset(s) to incident |
| DELETE | `/api/v1/incidents/{id}/assets/{asset_id}` | technician, admin | Unlink asset |
| POST | `/api/v1/incidents/{id}/vendors` | technician, admin | Link vendor to incident |
| DELETE | `/api/v1/incidents/{id}/vendors/{vendor_id}` | technician, admin | Unlink vendor |

### Regulatory Reports

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/api/v1/incidents/{id}/reports` | technician, admin | List regulatory reports for incident |
| POST | `/api/v1/incidents/{id}/reports/{report_id}/generate` | admin | Generate PDF report |
| POST | `/api/v1/incidents/{id}/reports/{report_id}/submit` | admin | Mark report as submitted |
| GET | `/api/v1/incidents/{id}/reports/{report_id}/download` | admin | Download generated PDF |

### Post-Mortem

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/api/v1/incidents/{id}/post-mortem` | admin | Create post-mortem |
| GET | `/api/v1/incidents/{id}/post-mortem` | technician, admin | Get post-mortem |
| PUT | `/api/v1/incidents/{id}/post-mortem` | admin | Update post-mortem |

### Dashboard

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/api/v1/incidents/dashboard` | technician, admin | Incident dashboard stats |

### Employee Reporting

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/api/v1/my/report-incident` | employee, technician, admin | Report suspected incident (simplified) |
| GET | `/api/v1/my/incidents` | employee, technician, admin | List incidents reported by the current user (read-only, basic status only) |

---

## Definition of Done

- [ ] New bounded context `incident_bc` follows DDD + CQRS pattern
- [ ] SecurityIncident entity with full state machine (detected → triaged → contained → eradicated → recovered → closed)
- [ ] Incidents are never deletable — no delete endpoints exposed
- [ ] `close_reason` mandatory when closing from any active state (not required for recovered→closed)
- [ ] Mandatory fields enforced on creation (title, description, incident_type, severity, detected_at)
- [ ] Severity classification P1-P4 with color-coded badges
- [ ] RegulatoryReport auto-creation on incident creation (24h, 72h, 30d deadlines)
- [ ] Countdown timers visible on incident detail page
- [ ] Escalation notifications at 75% and 90% of deadline elapsed
- [ ] PDF report generation (pre-filled with incident data) using existing Celery + WeasyPrint infrastructure
- [ ] Report download, regeneration, and "mark as submitted" workflow
- [ ] IncidentAsset link table with asset search/selector
- [ ] IncidentVendor link table with vendor selector
- [ ] Append-only IncidentTimeline tracking all changes
- [ ] PostMortem creation for recovered/closed incidents
- [ ] Incident dashboard with active count, severity distribution, MTTC, MTTR
- [ ] Employee simplified reporting form
- [ ] Notification events for: creation, severity escalation, status change, deadline approaching, deadline passed
- [ ] All API endpoints with proper role authorization
- [ ] Database migration for all new tables
- [ ] Unit tests for all command/query handlers
- [ ] Integration tests for all API endpoints
- [ ] Frontend: incidents list page with filters
- [ ] Frontend: incident detail page with timeline, deadlines, assets, vendor, post-mortem
- [ ] Frontend: incident dashboard
- [ ] Frontend: employee report incident form
- [ ] i18n: EN/ES translations complete
- [ ] Celery periodic task for deadline monitoring

---

## Open Questions

1. **CSIRT notification method:** Should the platform actually send the report to CSIRT via email, or just generate the PDF and let the user send it manually? → **Recommendation:** Generate PDF only, mark as submitted manually. Actual CSIRT submission varies by country and should not be automated in v1.

2. **Severity auto-escalation:** Should P3/P4 incidents auto-escalate to P2/P1 if unresolved after a threshold? → **Recommendation:** Not in v1. Keep manual severity changes with timeline tracking.

3. **Integration with E29 (Audit Trail):** E29 is not yet built. Should E36 implement its own audit logging via IncidentTimeline, or wait for E29? → **Recommendation:** Use IncidentTimeline as incident-specific audit log. When E29 ships, it will capture all actions globally. No dependency.

---

## Resolved Decisions

1. **Delete policy:** Security incidents are **never deletable**. They can only be closed. This ensures NIS2 compliance and complete audit trails. No delete endpoint will be exposed.

2. **Close justification:** A `close_reason` text field is added to SecurityIncident. It is **mandatory when closing from any active state** (detected/triaged/contained/eradicated → closed), but **not required for the normal recovered → closed transition**.

3. **Plan gating:** Security Incident Management is available on **all plans** (Free, Premium, Enterprise). No plan restriction.

4. **Report regeneration:** Regulatory reports can be **regenerated** at any time before submission. The new PDF replaces the previous one. Each generation event is logged in the IncidentTimeline for audit purposes.

5. **Unlink audit trail:** Unlinking assets or vendors from an incident creates a timeline entry (`asset_unlinked`, `vendor_unlinked`). Full audit trail for all link/unlink operations.

6. **Post-mortem editability:** Post-mortems are **editable indefinitely**. Each update is logged in the timeline.

7. **Employee visibility:** Employees can see **read-only basic status** of incidents they reported via `/api/v1/my/incidents`. No sensitive details (attack vector, breach scope) are exposed in this view.

8. **Dashboard access:** Both **technicians and admins** have access to the incident dashboard.
