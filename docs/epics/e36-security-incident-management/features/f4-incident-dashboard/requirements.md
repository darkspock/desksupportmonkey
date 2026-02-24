# Feature F4: Incident Dashboard

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 4
**Dependencies:** F0 (Incident Foundation)
**Complexity:** M

## Scope

### Included
- Dashboard query aggregating incident statistics
- Active incidents count by severity (P1/P2/P3/P4)
- Incidents by type distribution (malware, data_breach, ddos, etc.)
- Mean Time to Contain (MTTC) — average time from detected to contained
- Mean Time to Resolve (MTTR) — average time from detected to closed
- Upcoming regulatory deadlines (next 7 days) — requires F1 data
- Recent incidents list (last 10)
- Frontend: incident dashboard page
- Frontend: severity distribution visualization
- Frontend: type distribution visualization
- Frontend: MTTC/MTTR metrics display
- Frontend: upcoming deadlines list
- i18n: EN/ES for dashboard UI

### Excluded (in other features)
- Incident CRUD and lifecycle (F0)
- Regulatory reports (F1)
- Asset/vendor linking (F2)
- Post-mortem (F3)

## User Value

When this feature is complete, IT managers, admins, and technicians can:
- See a real-time overview of their organization's security posture
- Monitor active incident counts by severity level
- Track operational efficiency via MTTC and MTTR metrics
- See upcoming regulatory deadlines to prevent compliance breaches
- Quickly access recent incidents

## Acceptance Criteria

- [ ] GET `/api/v1/incidents/dashboard` returns aggregated stats
- [ ] Response includes: active_by_severity (P1/P2/P3/P4 counts)
- [ ] Response includes: by_type (count per incident_type)
- [ ] Response includes: mttc_hours (average hours from detected to contained, or null if no data)
- [ ] Response includes: mttr_hours (average hours from detected to closed, or null if no data)
- [ ] Response includes: upcoming_deadlines (regulatory reports due in next 7 days)
- [ ] Response includes: recent_incidents (last 10 incidents with basic fields)
- [ ] Response includes: total_active, total_closed counts
- [ ] Dashboard endpoint accessible by technician and admin roles
- [ ] All data scoped to current user's company (tenant isolation)
- [ ] Frontend: dashboard page with stat cards for active incidents by severity
- [ ] Frontend: type distribution display (bar or pie chart data)
- [ ] Frontend: MTTC and MTTR metric cards
- [ ] Frontend: upcoming deadlines list with countdown
- [ ] Frontend: recent incidents table with links to detail
- [ ] i18n: all new strings in EN and ES
- [ ] Unit tests for dashboard query handler
- [ ] Integration tests for dashboard endpoint

## Technical Scope

### Entities (used from dependencies)
- `SecurityIncident` from F0
- `RegulatoryReport` from F1 (for upcoming deadlines)

### Key Components
- `src/incident_bc/incident/application/queries/get_dashboard.py` — aggregation query
- `adapters/http/api/incidents/routers.py` — add dashboard endpoint
- `web/app/src/pages/incidents/Dashboard.tsx` — dashboard page

## Notes

- MTTC is calculated as: average of (`contained_at` - `detected_at`) for all incidents that have reached `contained` status. The `contained_at` can be derived from the timeline (status_change event to "contained").
- MTTR is calculated as: average of (`closed_at` - `detected_at`) for all closed incidents.
- Upcoming deadlines query reads from `regulatory_reports` table (created by F1). If F4 is deployed before F1, this section shows empty.
- Dashboard data should use efficient SQL aggregation queries, not Python-side processing.
- The dashboard is a read-only view — no write operations.
