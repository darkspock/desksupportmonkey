# Feature F3: Post-Mortem & Employee Reporting

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 3
**Dependencies:** F0 (Incident Foundation)
**Complexity:** M

## Scope

### Included
- PostMortem entity (one-to-one with SecurityIncident)
- Create post-mortem endpoint (only when incident is recovered or closed)
- Get and update post-mortem endpoints
- Post-mortem editable indefinitely, each update logged in timeline
- Employee simplified incident reporting endpoint
- Employee "my incidents" read-only list endpoint (basic status only, no sensitive details)
- Notifications for new employee-reported incidents
- Frontend: post-mortem section on incident detail page
- Frontend: employee report incident form (accessible from "My Activity" section)
- Frontend: employee "my reported incidents" list
- i18n: EN/ES for post-mortem and employee reporting UI

### Excluded (in other features)
- Incident CRUD and lifecycle (F0)
- Regulatory reports (F1)
- Asset/vendor linking (F2)
- Dashboard (F4)

## User Value

When this feature is complete:
- **IT managers/admins** can create post-mortems with root cause analysis, lessons learned, and corrective actions for recovered/closed incidents
- **Employees** can report suspected security incidents (phishing, suspicious activity) through a simplified form without needing technical knowledge
- **Employees** can see the status of incidents they reported

## Acceptance Criteria

### Post-Mortem
- [ ] POST `/api/v1/incidents/{id}/post-mortem` creates a post-mortem (admin only)
- [ ] Precondition: incident status must be `recovered` or `closed`
- [ ] Mandatory fields: root_cause, lessons_learned, corrective_actions
- [ ] GET `/api/v1/incidents/{id}/post-mortem` returns the post-mortem (technician, admin)
- [ ] PUT `/api/v1/incidents/{id}/post-mortem` updates the post-mortem (admin only)
- [ ] Post-mortem is editable indefinitely (per resolved decision #6)
- [ ] Each create/update creates a timeline entry
- [ ] One-to-one relationship: only one post-mortem per incident

### Employee Reporting
- [ ] POST `/api/v1/my/report-incident` creates a simplified incident (employee, technician, admin)
- [ ] Simplified form: title, description, incident_type (dropdown) — no severity, no attack_vector
- [ ] System sets default severity P3 (medium) and status `detected`
- [ ] System notifies all admins and technicians
- [ ] GET `/api/v1/my/incidents` returns list of incidents reported by current user
- [ ] Employee view shows only: id, title, incident_type, severity, status, created_at (no sensitive fields)
- [ ] No attack_vector, data_breach_scope, or timeline exposed in employee view

### Frontend
- [ ] Post-mortem section visible on incident detail when status is recovered/closed
- [ ] Post-mortem creation form with root_cause, lessons_learned, corrective_actions
- [ ] Post-mortem edit capability with inline editing
- [ ] Employee "Report Security Incident" accessible from My Activity section
- [ ] Employee simplified form with title, description, incident_type dropdown
- [ ] Employee "My Reported Incidents" list showing basic status
- [ ] i18n: all new strings in EN and ES
- [ ] Unit tests for post-mortem and employee reporting handlers
- [ ] Integration tests for all new endpoints

## Technical Scope

### Entities (owned by this feature)
- `PostMortem` — one-to-one with SecurityIncident

### Entities (used from dependencies)
- `SecurityIncident` from F0
- `IncidentTimeline` from F0

### Key Components
- `src/incident_bc/incident/domain/entities.py` — add PostMortem entity
- `src/incident_bc/incident/application/commands/create_postmortem.py`
- `src/incident_bc/incident/application/commands/update_postmortem.py`
- `src/incident_bc/incident/application/commands/report_incident.py` (employee)
- `src/incident_bc/incident/application/queries/get_postmortem.py`
- `src/incident_bc/incident/application/queries/list_my_incidents.py` (employee)
- `adapters/http/api/incidents/routers.py` — add post-mortem endpoints
- `adapters/http/api/my/routers.py` — add employee reporting endpoints

## Notes

- PostMortem table is already created by F0 migration.
- Employee-reported incidents follow the same creation flow as admin-created ones but with simplified fields and default severity.
- The employee view endpoint (`/api/v1/my/incidents`) returns a restricted DTO that excludes sensitive fields (attack_vector, data_breach_scope, timeline, etc.).
- Post-mortem editability is indefinite per resolved decision #6.
