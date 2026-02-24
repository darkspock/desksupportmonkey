# DeskSupportMonkey - Roadmap

## Epic Overview

| # | Epic | Description | Priority | Status |
|---|---|---|---|---|
| E0 | Foundation | Project setup, DB, auth, multi-tenancy base | Critical | Done |
| E1 | Company Management | Super admin: create companies, assign admins, manage domains | Critical | Done |
| E2 | Asset Inventory | Asset CRUD, assignment, history (event sourcing), CSV import | High | Done |
| E3 | Service Requests | Employee portal, request state machine, technician queue, comments | High | Done |
| E4 | Real-time & Notifications | WebSockets, in-app notifications, pub/sub events | Medium | Done |
| E5 | Admin Dashboard | Metrics, charts, alerts, user management | Medium | Done |
| E6 | Report Generation | Celery async tasks, PDF generation, MinIO storage | Medium | Done |
| E7 | Frontend | React app, routing, layouts, pages for all modules | High | Done |
| E8 | Seed Data & Demo | Demo data, demo script, Docker Compose polish | Low | Done |
| E9 | UX Improvements | Invite users, departments edit, frontend quality uplift, and reliability hardening | Medium | Done |
| E10 | Asset QR & Barcodes | QR codes and barcodes on asset detail page with print functionality for physical labels | Medium | Done |
| E11 | Department Equipment Profiles | Department managers, role-based equipment profiles (e.g., Tech → Linux 32GB, Design → MacBook Pro, Heads → MacBook Air), and automatic asset assignment by department and role | High | Done |
| E12 | Request Typification & Approval | Structured request categories (repair, new equipment, configuration, etc.), sub-types for new equipment (computer, mobile, etc.), priority scoring based on department and role, and approval workflow for new equipment requests | High | Done |
| E13 | AI Request Classification | AI-powered automatic classification of service requests — infers category, sub-type, and priority from user description, overriding user-submitted values when the AI assessment is more accurate | Medium | Done |
| E14 | Procurement & Budget | Purchase order management, goods receipt tracking, department budget allocation, and expense control per department with spending reports | High | Done |
| E15 | Appointment Scheduling | Schedule and manage support appointments between technicians and employees — calendar view, time slot availability, booking, reminders, and rescheduling | Medium | Done |
| E16 | Shipping & Logistics | Ship equipment to employee home, other offices, or vendor for repair — shipment tracking, delivery addresses, carrier integration, return management, and shipment status notifications | Medium | Done |
| E17 | Scheduled Maintenance | Recurring and one-off maintenance plans for assets — maintenance templates, calendar integration, technician assignment, completion tracking, and overdue alerts | Medium | Done |
| E18 | Knowledge Base & Self-Service | Built-in wiki with TipTap WYSIWYG editor — articles, FAQs, categorized solutions, version history, native links to assets/tickets/users, full-text search (PostgreSQL tsvector), AI-suggested articles on ticket creation for deflection, and self-service portal for employees | High | Done |
| E19 | SLA Management | Configurable SLA policies per priority and category — response/resolution time targets, automatic escalation rules, breach notifications to managers, and SLA compliance reports | High | Done |
| E20 | Asset Lifecycle & Warranties | Asset depreciation tracking, end-of-life planning, renewal/refresh cycles, lease vs purchase tracking, warranty management with vendor contacts, and warranty claim workflow | Medium | Pending |
| E21 | Software License Management | Track software licenses per user and department — seat compliance (used vs purchased), renewal alerts, cost allocation per department, and license audit reports | Medium | Pending |
| E22 | Employee Onboarding/Offboarding | Automated workflows for new hires (equipment pack based on department + role from E11) and departures (return checklist, account deactivation, asset recovery tracking) | High | Pending |
| E23 | Multi-channel Intake | Email-to-ticket conversion, Slack/Teams integration for creating and tracking requests, and chatbot for guided ticket creation without entering the app | Medium | Pending |
| E24 | Google & Microsoft Login | Google and Microsoft OAuth2 login buttons, backend token verification, account linking by email, new user auto-creation by domain match | High | Done |
| E25 | Vendor & Supply Chain Risk | Vendor directory with contacts and contracts, vendor SLA tracking, incident history per vendor, warranty claim routing, vendor performance reports, third-party risk assessment questionnaires (NIS2/DORA Article 28), supply chain security scoring, and critical ICT provider dependency mapping | Medium | Pending |
| E26 | Observability with Grafana | Prometheus metrics for FastAPI, Celery, PostgreSQL, and Redis — Grafana dashboards for infrastructure health, request rates, queue depth, and business metrics. Sentry already covers error tracking and basic performance monitoring | Low | Pending |
| E27 | Surveys & Feedback | CSAT surveys after ticket resolution (star rating + comment), decision polls for purchase planning (connects with E14), onboarding feedback after equipment delivery (connects with E22), and satisfaction metrics per technician, department, and category | Low | Pending |
| E28 | Mobile / PWA | Progressive Web App for technicians and employees — QR scanning with camera, ticket updates from the field, push notifications, offline support, and responsive mobile-first UI | Low | Pending |
| E29 | Audit Trail & Compliance Evidence | Complete audit log of all user actions (who did what, when), immutable append-only log storage, GDPR data export and deletion requests, compliance evidence tagging (link audit entries to NIS2/DORA/ISO 27001 controls), regulatory data retention policies per company, and audit-ready evidence export for external auditors | Critical | Done |
| E30 | Custom Fields | Admin-defined custom fields for assets, tickets, and companies — text, number, date, dropdown, and multi-select types with validation rules and visibility per role | High | Pending |
| E31 | Workflow Automations | Rule engine for if-then automations — auto-assign tickets by category, auto-escalate after SLA threshold, notify manager on critical priority, auto-close resolved tickets after X days, and trigger actions on asset status changes | High | Pending |
| E32 | Asset Discovery | Automatic network device discovery — agent-based and agentless scanning, sync discovered devices with asset inventory, detect new/removed devices, and scheduled discovery scans | Low | Pending |
| E33 | Change Management (ITIL) | Change request workflow — request, risk assessment, CAB approval board, scheduled implementation, rollback plan, post-implementation review, and change calendar integration | Low | Pending |
| E34 | Feature Voting & Roadmap | In-app feature request board — users submit and upvote ideas, admin reviews and prioritizes, public roadmap view with status (planned, in progress, shipped), and vote-based priority scoring for product decisions | Low | Pending |
| E35 | MCP Server | Expose DSM as an MCP server so AI assistants can manage assets, requests, users, reports, and dashboard data via tool calls — multi-tenant auth, role-based tool visibility, and streaming support | High | Done |
| E36 | Security Incident Management | Security incident lifecycle distinct from service requests — severity classification (P1-P4), mandatory fields (attack vector, affected systems, data breach scope), NIS2 24h/72h regulatory reporting timeline enforcement, auto-generated CSIRT notification reports, and incident post-mortem with root cause analysis | High | Done |
| E37 | Risk Register | Organizational risk management — risk entries linked to assets, departments, and vendors, likelihood-impact scoring matrix, mitigation plan tracking with owner assignment, periodic review cadence enforcement, and risk dashboard with heat map visualization | High | Done |
| E38 | Asset Criticality & CMDB | Asset criticality classification (Critical/High/Medium/Low), Configuration Item (CI) relationship mapping (asset-to-service, asset-to-asset dependencies), business impact analysis per asset, criticality-based SLA escalation rules, and dependency graph visualization | Medium | Pending |
| E39 | Compliance Dashboard | Compliance posture management — control mapping to NIS2, DORA, and ISO 27001 articles, compliance status per control (compliant/partial/non-compliant), evidence collection linking controls to audit logs, incidents, and change records, compliance gap analysis reports, and audit-ready PDF export per framework | Critical | Done |
| E40 | Vulnerability Management | Track known vulnerabilities per asset — CVE tracking linked to asset brand/model/OS, severity scoring (CVSS), remediation ticket auto-creation from vulnerabilities, patch status tracking, vulnerability scan result import (CSV/API), and vulnerability-to-asset exposure dashboard | Medium | Pending |
| E42 | SSO & Directory Sync | SAML/OIDC enterprise single sign-on configuration, LDAP/Active Directory synchronization of users, departments, and roles, automatic provisioning/deprovisioning, group-to-role mapping from identity provider | Critical | Pending |
| E43 | Billing & Subscriptions | Stripe-based subscription management — Free/Premium/Enterprise/Open Source plans, usage limits enforcement, Stripe Checkout for upgrades, Stripe Customer Portal for invoices, grace period and suspension on payment failure, feature gating per plan, super admin complimentary plans | Critical | Done |
| E44 | Super Admin Enhancements | Company list with usage counts and trial visibility, Stripe invoice history per company, revenue overview dashboard (MRR, plan distribution, active trials) | High | Done |
| E45 | Asset Locations & Movement Tracking | Location entity within asset BC, 3 system locations per company, admin-managed custom locations, automatic location changes on assign/unassign/create/decommission/shipping, movement audit trail, location management UI | High | Done |

---

## Dependency Graph

```
E0: Foundation
 │
 ├── E1: Company Management
 │    │
 │    ├── E2: Asset Inventory
 │    │    │
 │    │    └── E6: Report Generation
 │    │
 │    ├── E3: Service Requests
 │    │    │
 │    │    └── E4: Real-time & Notifications
 │    │
 │    └── E5: Admin Dashboard (depends on E2 + E3)
 │
 └── E7: Frontend (parallel, depends on API endpoints from E1-E6)

E8: Seed Data & Demo (after all others)

E10: Asset QR & Barcodes (depends on E2 + E7)
```

---

## Epic Details

### E0: Foundation
- Project scaffolding (FastAPI app, folder structure, base classes)
- PostgreSQL + Alembic setup
- Redis connection
- Magic link authentication (request link, verify token, JWT)
- RBAC middleware (super_admin, admin, technician, employee)
- Multi-tenancy base (company_id scoping in repositories)
- Health check endpoint
- CORS, error handling, API response format

### E1: Company Management
- Company CRUD (super admin only)
- Company email domains configuration
- Company statuses (active, suspended, deactivated)
- Department CRUD (company admin)
- User auto-creation on first magic link login
- User role management (company admin promotes/demotes)
- User deactivation

### E2: Asset Inventory
- Asset CRUD (technician)
- Asset types, statuses, serial numbers
- Asset assignment/unassignment to employees
- Asset event sourcing (append-only history log)
- Asset search and filters
- CSV bulk import
- "My Equipment" view (employee)

### E3: Service Requests
- Request creation (employee): incident, new equipment, onboarding
- Request state machine: submitted -> in_review -> in_progress -> resolved/rejected
- Automatic priority based on type
- Technician queue (claim/self-assign)
- Comments (employee + technician)
- Internal notes (technician only)
- "My Requests" view (employee)

### E4: Real-time & Notifications
- WebSocket endpoint (per user, JWT auth)
- Domain events on state changes
- Pub/sub: route events to subscribers (notifier, audit)
- In-app notification storage and read/unread
- Push events: request status changed, comment added, report ready

### E5: Admin Dashboard
- Open requests summary (by type, priority, status)
- Average resolution time (overall + per technician)
- Assets by status (chart data)
- Requests over time (chart data)
- Warranty expiration alerts
- Aging asset alerts
- SLA breach alerts (hardcoded thresholds)
- User management (list, promote, deactivate)

### E6: Report Generation
- Celery task for async PDF generation
- Jinja2 HTML templates -> WeasyPrint PDF
- Upload to MinIO (S3-compatible)
- Report record (pending -> completed/failed)
- Signed URL for download (1h expiry)
- Report types: asset inventory, request summary, technician performance
- Max 3 retries, 5 min timeout

### E7: Frontend
- React + TypeScript + Vite setup
- Routing by role (employee, technician, admin, super admin)
- Auth flow (magic link request, verify, JWT storage)
- Employee portal: my equipment, submit request, my requests
- Technician panel: request queue, inventory management
- Admin dashboard: metrics, alerts, user management
- Super admin: company management
- WebSocket integration for real-time updates
- Responsive design (desktop + tablet)

### E8: Seed Data & Demo
- Seed script: 2-3 companies, users per role, assets, requests in various states
- Demo walkthrough script (documentation)
- Docker Compose verified end-to-end
- .env.example with defaults

### E9: UX Improvements
- Invite users by email from Users page (admin sends magic link)
- Departments page: add edit/rename functionality
- Asset detail page: proper formatted event history instead of raw JSON
- Resolve user IDs to names/emails across request views, dashboard, and notes
- Asset assignment UI (assign/unassign from asset detail page)
- Standardize date format to YYYY/MM/DD across all pages (11 instances)
- Confirmation dialogs for destructive actions (delete, deactivate, status changes)
- Toast notifications for silent mutations (mark-read, toggle active, status change, delete)
- Empty state CTAs (MyEquipmentPage)
- i18n: Spanish and English with language selector in header
- Asset edit and status change from detail page
- Request priority change from detail page
- User department assignment from Users page
- Dashboard: warranty alerts, aging alerts, request trend chart
- Company edit (name, domains) from Companies page
- Auth refresh with stronger visual hierarchy and branded login experience
- Login uses root README branding image source (`web/site/logo.png`)
- Lightweight design-system foundation (tokens + shared form/action primitives)
- Improved responsive app shell for tablet/mobile navigation
- Accessibility polish (keyboard/focus/labels/tooltips)
- Unified loading/empty/error and mutation feedback patterns

### E10: Asset QR Codes & Barcodes
- QR code on asset detail page encoding full URL to asset (scan-to-access)
- Code 128 barcode encoding asset ID (ULID) for physical identification
- Print button: opens clean print view with QR, barcode, brand, model, serial number
- Auth redirect flow: unauthenticated QR scans redirect to login, then back to asset
- i18n support for all labels (English and Spanish)

### E25: Vendor & Supply Chain Risk
- Vendor directory with contacts, contracts, and renewal dates
- Vendor SLA tracking and performance reports
- Incident history per vendor (linked to service requests and security incidents)
- Warranty claim routing to appropriate vendor
- **NIS2/DORA enhancements:**
  - Third-party risk assessment questionnaires (based on DORA Article 28)
  - Supply chain security scoring (risk level per vendor: Low/Medium/High/Critical)
  - Critical ICT provider dependency mapping (which vendors support essential services)
  - Vendor contract compliance tracking (data processing, security clauses)
  - Concentration risk alerts (over-reliance on single vendor)

### E29: Audit Trail & Compliance Evidence
- Complete audit log of all user actions (who did what, when, from where)
- Immutable append-only log storage (tamper-evident)
- GDPR data export and deletion requests with automated workflows
- **NIS2/DORA enhancements:**
  - Evidence tagging: link audit entries to specific NIS2/DORA/ISO 27001 controls
  - Regulatory data retention policies per company (configurable retention periods)
  - Audit-ready evidence export: filtered PDF/CSV bundles for external auditors
  - Access review logs: periodic access certification records
  - Log integrity verification (hash chain for tamper detection)

### E35: MCP Server
- MCP server using the Python MCP SDK (`mcp` package) exposing DeskSupportMonkey's API as AI-callable tools
- **Asset tools** (10): create, list, get, update, change status, assign, unassign, history, import, assignable users
- **Request tools** (10): create, list, get, change status, change priority, assign, add comment, list comments, add note, list notes
- **User tools** (7): list, invite, get, change role, activate, deactivate, assign department
- **Company tools** (5): create, list, get, update, change status (super admin only)
- **Department tools** (5): create, list, get, update, delete
- **Report tools** (4): request, list, get, download
- **Dashboard tools** (7): request summary, resolution time, trend, asset summary, warranty alerts, aging alerts, SLA alerts
- **My tools** (7): my equipment, my requests, notifications, mark read, mark all read, company settings get/update
- **Auth tools** (2): get current user, set password
- Auth: API key or JWT per-connection, tenant context derived from authenticated user
- Role-based tool filtering: each tool declares its minimum role, tools invisible to lower roles
- Multi-tenant isolation: all tool calls scoped to the user's company
- Streaming: SSE transport for long-running operations (report generation)

### E36: Security Incident Management
- Security incident lifecycle separate from service requests (new bounded context: `incident_bc`)
- Incident severity classification: P1-Critical, P2-High, P3-Medium, P4-Low
- Mandatory fields on creation: incident type (malware, data breach, DDoS, unauthorized access, phishing, other), attack vector, affected systems (linked to assets), estimated data breach scope
- Incident state machine: detected → triaged → contained → eradicated → recovered → closed
- **NIS2 regulatory reporting timeline enforcement:**
  - 24-hour early warning (auto-generated notification to national CSIRT)
  - 72-hour detailed incident report (structured template with impact assessment)
  - 30-day final report (root cause analysis, remediation measures taken)
  - Deadline countdown timers with escalation alerts to admin/management
- Auto-generated regulatory notification reports (PDF, pre-filled with incident data)
- Incident post-mortem: root cause analysis, lessons learned, linked corrective actions
- Incident dashboard: active incidents, mean time to contain (MTTC), incidents by type/severity
- Cross-reference with assets (which assets were affected) and vendors (if third-party involved)
- Notification events: incident created, severity escalated, regulatory deadline approaching, incident closed

### E37: Risk Register
- Risk entry CRUD: title, description, risk category (operational, cyber, compliance, third-party)
- Link risks to assets, departments, vendors, and services
- Likelihood × Impact scoring matrix (5×5 grid): Very Low to Very High
- Risk level auto-calculation: Low / Medium / High / Critical
- Mitigation plans: description, owner (user assignment), target date, status (open/in-progress/mitigated/accepted)
- Risk treatment options: mitigate, accept, transfer, avoid
- Periodic review cadence: configurable review frequency per risk (monthly/quarterly/annually)
- Review reminders and overdue alerts to risk owners
- Risk dashboard: heat map visualization, risk trend over time, open vs mitigated counts
- Risk history: audit trail of all risk score changes and review decisions
- Export: risk register PDF/CSV for board reporting

### E38: Asset Criticality & CMDB
- Asset criticality classification field: Critical / High / Medium / Low
- Criticality assignment rules: auto-suggest based on asset type, department, and linked services
- Configuration Item (CI) relationship types: runs-on, depends-on, connected-to, part-of, backs-up
- CI relationship CRUD: link assets to other assets and to services/applications
- Business impact analysis (BIA) per asset: impact score if unavailable, recovery time objective (RTO), recovery point objective (RPO)
- Dependency graph visualization: interactive diagram showing upstream/downstream dependencies
- Impact propagation: when a critical asset has an incident, highlight all dependent assets/services
- Criticality-based SLA escalation: auto-escalate incidents affecting critical assets
- CMDB dashboard: total CIs by criticality, orphan assets (no relationships), dependency depth
- Enhances E2 (Asset Inventory) — adds fields and relationships to existing asset model

### E39: Compliance Dashboard
- Compliance framework management: admin selects applicable frameworks (NIS2, DORA, ISO 27001)
- Control catalog per framework: pre-loaded control lists with article/clause references
  - NIS2: Article 21 measures (risk analysis, incident handling, business continuity, supply chain, etc.)
  - DORA: Chapter II (ICT risk management), Chapter III (incident reporting), Chapter IV (testing), Chapter V (third-party risk)
  - ISO 27001: Annex A controls (93 controls across 4 themes)
- Control status tracking: compliant / partially compliant / non-compliant / not applicable
- Evidence collection: link each control to supporting evidence (audit log entries, incident reports, change records, risk assessments, policy documents)
- Evidence upload: attach policy PDFs, screenshots, or external documents to controls
- Gap analysis report: list of non-compliant/partial controls with recommendations
- Compliance score: percentage compliance per framework, trend over time
- Compliance dashboard: framework overview cards, control status breakdown, upcoming review deadlines
- Audit-ready export: PDF report per framework with control status, evidence references, and gap list
- Review workflow: periodic control reviews with due dates and reviewer assignment

### E40: Vulnerability Management
- Vulnerability entry CRUD: CVE ID, title, description, CVSS score, severity (Critical/High/Medium/Low)
- Link vulnerabilities to affected assets (many-to-many: one CVE can affect multiple assets)
- Asset matching: auto-suggest affected assets based on brand/model/OS version
- Vulnerability sources: manual entry, CSV import, API import (future: integration with vulnerability scanners)
- Remediation workflow: auto-create service request or change request from vulnerability
- Patch status tracking per asset: unpatched / patch scheduled / patched / not applicable
- Remediation SLA: configurable timelines by severity (e.g., Critical = 48h, High = 7 days)
- Overdue remediation alerts to asset owners and admins
- Vulnerability dashboard: open vulnerabilities by severity, assets at risk, mean time to remediate (MTTR)
- Exposure score per asset: aggregate of unpatched vulnerability severities
- Export: vulnerability report PDF/CSV for compliance evidence

### E42: SSO & Directory Sync
- SAML 2.0 and OIDC enterprise SSO configuration per company
- Admin SSO setup wizard: metadata URL, certificate upload, entity ID, ACS URL
- SP-initiated and IdP-initiated login flows
- LDAP/Active Directory connector: server URL, bind DN, base DN, search filters
- Scheduled directory synchronization (users, departments, groups)
- Automatic user provisioning: create accounts from directory entries
- Automatic user deprovisioning: deactivate accounts removed from directory
- Group-to-role mapping: map AD groups to platform roles (admin, technician, employee)
- Department sync: map AD organizational units to platform departments
- Sync audit log: record each sync run with created/updated/deactivated counts
- Conflict resolution: handle email changes, department renames, role conflicts
- Depends on E24 (Google & Microsoft Login) for foundational OAuth infrastructure

---

## Recommended Implementation Order

| Phase | Epics | Outcome | Status |
|---|---|---|---|
| **Phase 1** | E0 + E1 | App boots, auth works, companies exist, users can log in | Done |
| **Phase 2** | E2 + E3 | Core business: assets and requests fully functional (API) | Done |
| **Phase 3** | E4 + E5 + E6 | Real-time, dashboard, reports (API complete) | Done |
| **Phase 4** | E7 + E8 + E9 | Frontend, seed data, UX polish | Done |
| **Phase 5** | E10-E19 + E24 | Feature expansion — QR, departments, procurement, scheduling, shipping, maintenance, KB, SLA, OAuth | Done |
| **Phase 6** | E35-E37 + E43-E45 | Platform — MCP server, incidents, risk register, billing, super admin, asset locations | Done |
| **Phase 7** | E29 | **Compliance foundation** — audit trail, compliance evidence, GDPR, retention | Done |
| **Phase 8** | E39 + E42 | **Enterprise readiness** — compliance dashboard, SSO & directory sync |  |
| **Phase 9** | E22 + E30 + E31 | **Operational power** — onboarding/offboarding, custom fields, workflow automations |  |
| **Phase 10** | E20 + E25 + E38 | **Asset & risk maturity** — lifecycle & warranties, vendor risk, CMDB |  |
| **Phase 11** | E40 + E21 + E23 | **Security & integration** — vulnerability management, license management, multi-channel |  |
| **Phase 12** | E28 + E32 + E33 | **Advanced** — mobile PWA, asset discovery, ITIL change management |  |
| **Backlog** | E26 + E27 + E34 | Internal tooling, surveys, feature voting — build when needed |  |

**Completed:** 31 epics (E0-E19, E24, E29, E35-E37, E43-E45)
**Remaining:** 17 epics (E20-E23, E25-E28, E30-E34, E38-E40, E42)
