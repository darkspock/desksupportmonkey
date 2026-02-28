# DSM Control vs InvGate — Feature Comparison

**Date:** 2026-02-27
**Purpose:** Side-by-side feature comparison to identify strengths, gaps, and competitive positioning

---

## Company Overview

| | DSM Control | InvGate |
|---|---|---|
| **HQ** | Spain 🇪🇸 | Buenos Aires, Argentina 🇦🇷 |
| **Founded** | 2025 | 2008 |
| **Employees** | Early stage | ~252 |
| **Revenue** | Pre-revenue | $30.3M (2023) |
| **Funding** | Bootstrapped | $35M (Bossa Invest, Endeavor Catalyst) |
| **Notable customers** | — | NASA JPL, PwC, Collins Aerospace, PeoplesBank |
| **Awards** | — | 2026 Info-Tech Champion (Midmarket ITSM), 2025 Gartner Customers' Choice |
| **Open source** | Yes (AGPL) | No |
| **EU data sovereignty** | Yes (EU-hosted) | No (Argentina/US infrastructure) |
| **Product architecture** | Single unified platform | Two separate products (Service Management + Asset Management) |

---

## Pricing Comparison (50-person company, ~500 assets)

| | DSM Control | InvGate |
|---|---|---|
| **Model** | Flat per-company tier | Per-agent/month + per-node/month |
| **ITSM cost** | Included | ~$40/agent/month × 5 techs = $200/mo |
| **ITAM cost** | Included | ~$0.21/node/month × 500 = $105/mo |
| **Combined** | **€149-299/month** | **~$305/month** (minimum, 5 agents only) |
| **With 10 agents** | Same €149-299/month | ~$505/month |
| **Free tier** | Yes (up to 10 employees) | No (30-day trial only) |
| **Self-hosted option** | Yes (open source) | Enterprise tier only (custom pricing) |
| **Per-agent trap** | No — flat pricing | Yes — scales linearly with agents |

**Verdict:** DSM is 2-4x cheaper, doesn't scale cost with team size, and offers a free tier + open source self-hosting.

---

## Feature-by-Feature Comparison

### SERVICE DESK / ITSM

| Feature | DSM Control | InvGate |
|---|---|---|
| **Ticket/request creation** | ✅ | ✅ |
| **Request types** | ✅ Incident, new equipment, onboarding, repair, configuration, access request | ✅ Customizable categories |
| **Request subtypes** | ✅ Hardware, software, network, security, etc. | ✅ Subcategories |
| **Priority levels** | ✅ Low, medium, high, urgent | ✅ Customizable |
| **Status workflow** | ✅ pending_approval → submitted → in_review → in_progress → resolved/rejected | ✅ Customizable workflows |
| **Visual workflow builder** | ❌ (code-based workflow templates) | ✅ No-code drag & drop |
| **Automation rules** | ✅ AI-powered auto-classification (type, subtype, priority) | ✅ Automation rules, routing, escalation |
| **AI ticket categorization** | ✅ Built-in (infers from description with confidence threshold) | ✅ AI-driven categorization |
| **AI solution suggestions** | ✅ KB article suggestions during ticket creation | ✅ Historical data-based suggestions |
| **AI ticket summaries** | ❌ | ✅ Smart summaries for agents |
| **Public comments** | ✅ | ✅ |
| **Internal notes** | ✅ (technician-only) | ✅ |
| **Technician queue** | ✅ Claim, self-assign, manage | ✅ |
| **Reassignment** | ✅ | ✅ |
| **Approval workflows** | ✅ (pending_approval status) | ✅ Multi-level approval chains |
| **ITIL incident management** | ✅ | ✅ ITIL-certified |
| **ITIL problem management** | ❌ (not a separate process) | ✅ Root cause analysis, recurring incident linking |
| **ITIL change management** | ❌ (on roadmap E33) | ✅ Risk-mitigated change planning, CAB approval |
| **Enterprise Service Management** | ❌ (IT-focused) | ✅ HR, Facilities, Legal service desks |
| **Self-service portal** | ✅ Employee portal with request creation | ✅ Customizable portal with service catalog |
| **Service catalog** | ❌ (request types serve this role) | ✅ Full service catalog with pinned items |
| **Gamification** | ❌ | ✅ Points, rankings, performance indicators |
| **Email-to-ticket** | ❌ (on roadmap E23) | ✅ |
| **Multi-channel intake** | ❌ (on roadmap E23) | ✅ Email, portal, API |
| **Mobile app** | ❌ (PWA on roadmap E28) | ✅ Android + iOS |
| **Chatbot/virtual agent** | ❌ | ✅ Virtual agent with KB article suggestions |
| **Multi-site support** | ✅ Locations and departments | ✅ Multi-location IT support |

**Verdict:** InvGate wins on ITIL maturity (problem/change management, service catalog), no-code workflow builder, multi-channel, mobile app, and gamification. DSM wins on AI classification with confidence scoring and flat pricing. InvGate has more polish here — they've had 18 years to build it.

---

### IT ASSET MANAGEMENT

| Feature | DSM Control | InvGate |
|---|---|---|
| **Hardware asset tracking** | ✅ Full lifecycle | ✅ Full lifecycle |
| **Asset types** | ✅ Configurable per company (no hardcoded list) | ✅ Configurable |
| **Asset status tracking** | ✅ in_stock, assigned, in_repair, decommissioned | ✅ Customizable statuses |
| **Serial number tracking** | ✅ | ✅ |
| **Asset assignment to users** | ✅ With full history | ✅ With ownership transfer tracking |
| **Asset event sourcing** | ✅ Immutable audit trail | ✅ Change tracking |
| **Custom fields** | ✅ Text, number, date, select, multi-select, boolean, file | ✅ Custom fields |
| **QR/barcode generation** | ✅ QR + Code 128 barcode | ✅ (via labels) |
| **CSV bulk import** | ✅ With validation preview | ✅ |
| **Network auto-discovery** | ❌ (on roadmap E32) | ✅ Agent-based + agentless scanning |
| **Software license management** | ❌ (on roadmap E21) | ✅ Software metering, license compliance |
| **Software deployment** | ❌ | ✅ Automated deployment |
| **CMDB** | ✅ CI relationships (depends-on, runs-on, connected-to, part-of, backs-up), dependency graph | ✅ AI-assisted relationship discovery, visual maps |
| **Business Impact Analysis** | ✅ Impact score, RTO, RPO per asset, BIA coverage metrics | ❌ (not as structured feature) |
| **Asset criticality** | ✅ Critical/High/Medium/Low with scoring | ✅ Classification available |
| **Depreciation tracking** | ❌ (on roadmap E20) | ✅ Financial tracking |
| **Warranty management** | ✅ Expiration date + dashboard alerts | ✅ Warranty tracking + alerts |
| **Contract management** | ✅ Full (type, status, renewal, auto-renewal, annual value, security clauses) | ✅ Lease, maintenance, rent, support, warranty contracts |
| **Remote desktop** | ❌ | ✅ Remote desktop integrations |
| **Security compliance view** | ✅ (via vulnerability management) | ✅ Encryption, firewall, antivirus status panel |
| **Native integrations** | MCP server (AI assistants) | SCCM, Filewave, Kandji, Lansweeper |
| **Warehouse/stock management** | ✅ Location-based stock tracking | ✅ Local storage facilities, real-time stock |

**Verdict:** InvGate wins on auto-discovery, software license management, software deployment, and remote desktop. DSM wins on BIA (RTO/RPO), structured CMDB with dependency graphs, and contract management with security clauses. InvGate's auto-discovery is a significant advantage — DSM has this on the roadmap (E32).

---

### PROCUREMENT & SUPPLY CHAIN

| Feature | DSM Control | InvGate |
|---|---|---|
| **Purchase orders** | ✅ Full PO workflow (draft → approved → ordered → received → closed) | ✅ PO number tracking, linked to contracts |
| **PO approval workflow** | ✅ With approval thresholds | ❌ (basic) |
| **Goods receipt** | ✅ Partial/full receiving per item | ❌ (not structured) |
| **Department budget enforcement** | ✅ Warn/strict mode, spending control per department | ❌ |
| **Vendor directory** | ✅ With contacts, categories, risk levels, critical ICT flag | ✅ Supplier tracking |
| **Vendor risk assessment** | ✅ Risk questionnaires, supply chain scoring, concentration risk alerts | ✅ Security questionnaires, vendor status monitoring |
| **Third-party risk (DORA Art.28)** | ✅ Critical ICT provider mapping, dependency analysis | ❌ |
| **Auto-create assets from POs** | ✅ | ❌ |
| **Procurement configuration** | ✅ PO prefix, fiscal year, currency, enforcement mode | ❌ |
| **Equipment profiles** | ✅ Department-role equipment packs for onboarding | ❌ |
| **Spending reports** | ✅ Per department | ✅ Cost center reports |

**Verdict:** DSM wins decisively. InvGate treats procurement as contract/cost tracking. DSM has full PO lifecycle, budget enforcement, equipment profiles for automated onboarding, and DORA-specific vendor risk features.

---

### SHIPPING & LOGISTICS

| Feature | DSM Control | InvGate |
|---|---|---|
| **Shipment management** | ✅ Full (draft → dispatched → in_transit → delivered) | ❌ (warehouse only) |
| **Inbound/outbound tracking** | ✅ Direction-aware (to employee, to office, to vendor) | ❌ |
| **Carrier & tracking** | ✅ Carrier, service level, tracking number, tracking URL | ❌ |
| **Return management** | ✅ Return shipments linked to originals | ❌ |
| **Shipment dashboard** | ✅ Active by status, recent deliveries, failed count | ❌ |

**Verdict:** DSM wins. InvGate has warehouse/stock features but no structured shipping workflow. DSM handles the full logistics chain for remote/hybrid teams.

---

### SCHEDULED MAINTENANCE

| Feature | DSM Control | InvGate |
|---|---|---|
| **Maintenance templates** | ✅ Recurrence, checklists, priority, asset type filter | ❌ (maintenance as contract type, not workflow) |
| **Maintenance plans per asset** | ✅ With next-due tracking | ❌ |
| **Maintenance records** | ✅ Full lifecycle (scheduled → in_progress → completed) | ❌ (via tickets) |
| **Overdue alerts** | ✅ 48h warning + overdue escalation | ❌ |
| **Checklist completion** | ✅ Required/optional items per record | ❌ |
| **Maintenance dashboard** | ✅ Scheduled, overdue, in progress, completed 30d | ❌ |
| **Warranty-aware repair routing** | ❌ | ✅ Broke/Fix with warranty + contract check |

**Verdict:** DSM wins. Structured maintenance-as-a-process vs InvGate's maintenance-as-a-contract-type. DSM enables proactive maintenance scheduling; InvGate handles it reactively via tickets.

---

### KNOWLEDGE BASE

| Feature | DSM Control | InvGate |
|---|---|---|
| **Wiki articles** | ✅ With categories | ✅ With categories |
| **WYSIWYG editor** | ✅ TipTap rich text | ✅ |
| **Article versioning** | ✅ Full version history | ❌ (not documented) |
| **Article status** | ✅ Draft/published | ✅ |
| **Full-text search** | ✅ PostgreSQL tsvector | ✅ Intelligent search |
| **AI article suggestions** | ✅ On ticket creation | ✅ Before and during ticket submission |
| **AI article creation from tickets** | ❌ | ✅ Resolved tickets → articles |
| **View counting** | ✅ | ✅ |
| **Employee KB portal** | ✅ | ✅ Linked to service catalog |

**Verdict:** Roughly equal. InvGate has AI-assisted article creation from resolved tickets (nice). DSM has article versioning. Both serve the purpose well.

---

### SLA MANAGEMENT

| Feature | DSM Control | InvGate |
|---|---|---|
| **SLA policies** | ✅ Per priority and request type | ✅ Per priority, category, service |
| **Response time targets** | ✅ | ✅ |
| **Resolution time targets** | ✅ | ✅ |
| **Auto-escalation on breach** | ✅ | ✅ |
| **Breach notifications** | ✅ To managers/admins | ✅ With configurable actions |
| **SLA dashboard** | ✅ | ✅ |
| **SLA reassessment on change** | ❌ | ✅ Re-evaluates if ticket properties change |
| **End-user SLA visibility** | ❌ | ✅ Expiration visible to requesters |

**Verdict:** InvGate has edge features (SLA reassessment, end-user visibility). Core SLA capabilities are equivalent.

---

### APPOINTMENT SCHEDULING

| Feature | DSM Control | InvGate |
|---|---|---|
| **Technician appointment booking** | ✅ Calendar view, time slots, availability windows | ❌ |
| **Appointment status tracking** | ✅ Pending, confirmed, completed, cancelled, no-show | ❌ |
| **Availability configuration** | ✅ Day/time slots per technician + overrides | ❌ |
| **Duration tracking** | ✅ | ❌ |

**Verdict:** DSM wins. InvGate has no appointment scheduling — a gap for field/on-site IT support.

---

### SECURITY & COMPLIANCE

| Feature | DSM Control | InvGate |
|---|---|---|
| **Security incident management** | ✅ Full lifecycle (detected → closed), types (phishing, malware, ransomware, etc.), severity (P1-P4), attack vectors, data breach scope | ✅ Basic incident tracking via tickets |
| **NIS2 reporting timeline** | ✅ 24h/72h/30d enforcement with countdown timers and escalation | ❌ |
| **DORA incident reporting** | ✅ 4h classification deadline support | ❌ |
| **Incident post-mortem** | ✅ Root cause, lessons learned, corrective actions | ❌ (via problem management records) |
| **Incident timeline** | ✅ Chronological event tracking with actors | ❌ |
| **Linked assets to incidents** | ✅ Which devices were affected | ✅ (via CMDB) |
| **Linked vendors to incidents** | ✅ Which suppliers were involved | ❌ |
| **Compliance dashboard** | ✅ Framework overview (NIS2, DORA, ISO 27001), control status, compliance scoring, evidence coverage % | ❌ (blog-level content, not product feature) |
| **Compliance control mapping** | ✅ Map controls to NIS2 Art.21, DORA Chapter II, ISO 27001 Annex A | ❌ |
| **Evidence collection** | ✅ Link audit entries to controls, manual document upload, evidence types | ❌ |
| **Compliance gap analysis** | ✅ Highlight non-compliant controls | ❌ |
| **Audit-ready export** | ✅ PDF/CSV per framework | ✅ Automated compliance reports |
| **Risk register** | ✅ Likelihood × Impact (5×5), treatment options, mitigation plans, heat map, review cadence | ✅ Centralized risk register, customizable evaluation |
| **Vulnerability management** | ✅ CVE tracking, CVSS scoring, remediation tickets, patch status, exposure score, remediation SLA | ✅ Security compliance panel (encryption, firewall, antivirus status) |
| **Audit trail** | ✅ Immutable append-only log (who, what, when, IP, user agent, HTTP method, response) | ✅ Change tracking and ownership transfers |
| **GDPR requests** | ✅ Data export and deletion handling | ❌ (GDPR mentioned in context, not as product feature) |
| **Regulatory data retention** | ✅ Configurable per company | ❌ |

**Verdict:** DSM wins dramatically. This is the biggest differentiator. InvGate has no product-level compliance features — no NIS2 timelines, no DORA reporting, no compliance dashboard, no control mapping, no evidence collection. They write blog posts about compliance but don't build compliance tools. DSM has a full compliance management system built into the product.

---

### REPORTING & ANALYTICS

| Feature | DSM Control | InvGate |
|---|---|---|
| **Dashboards** | ✅ Request, asset, resolution time, technician performance, budget, shipment, maintenance, incident, SLA, CMDB, vulnerability, compliance | ✅ Customizable dashboards, drill-down tables, full-screen views |
| **Custom dashboards** | ❌ (predefined dashboards) | ✅ Fully customizable |
| **PDF report generation** | ✅ Async (Celery) — asset inventory, request summary, technician performance, department spending | ✅ Automated reports |
| **Report scheduling** | ✅ | ✅ Recurring reports |
| **Advanced analytics** | ❌ | ✅ Business analytics, trend analysis |

**Verdict:** InvGate wins on reporting flexibility (customizable dashboards, advanced analytics). DSM has more specialized dashboards (compliance, vulnerability, CMDB, maintenance) but less customization.

---

### PLATFORM & INTEGRATIONS

| Feature | DSM Control | InvGate |
|---|---|---|
| **REST API** | ✅ Full CRUD + JWT auth | ✅ RESTful API |
| **API key management** | ✅ Create, list, revoke, last_used tracking | ✅ |
| **MCP server (AI assistants)** | ✅ 60+ tools, role-based, multi-tenant | ❌ |
| **Webhook support** | ✅ Domain events / pub-sub | ✅ |
| **Native integrations** | Limited (focus on API) | SCCM, Filewave, Kandji, Lansweeper, Zapier, LDAP/AD |
| **Slack/Teams** | ❌ (on roadmap E23) | ✅ (via Zapier) |
| **SSO (SAML/OIDC)** | ✅ OAuth2 (Google, Microsoft) / SAML on roadmap (E42) | ✅ Multiple SAML support |
| **LDAP/AD sync** | ❌ (on roadmap E42) | ✅ Directory sync |
| **Multi-tenancy** | ✅ Full company_id isolation | ✅ |
| **White label** | ✅ Build-time brand configuration | ❌ |
| **Localization** | ✅ Spanish + English | ✅ Multi-language |
| **Mobile app** | ❌ (PWA on roadmap) | ✅ Android + iOS |
| **On-premise deployment** | ✅ (open source) | ✅ (Enterprise tier only) |
| **BYOAI** | ❌ | ✅ (Enterprise tier) |

**Verdict:** InvGate wins on integration ecosystem (Zapier, SCCM, LDAP, mobile). DSM wins on MCP server for AI, white labeling, and open source self-hosting. InvGate's integration maturity reflects 18 years of development.

---

### ASSET CHECKOUT & CUSTODY

| Feature | DSM Control | InvGate |
|---|---|---|
| **Equipment checkout flow** | ✅ Checkout → acceptance → check-in with condition tracking | ❌ (basic assignment) |
| **Condition tracking** | ✅ Condition out vs condition in | ❌ |
| **Employee acceptance** | ✅ Employee must accept equipment | ❌ |
| **Auto-GDPR sanitization** | ✅ Maintenance triggered on check-in | ❌ |
| **Custody history** | ✅ Full history per employee and asset | ✅ Ownership transfer log |

**Verdict:** DSM wins. The checkout flow with condition tracking, employee acceptance, and GDPR sanitization is unique — designed for the hybrid/remote workforce.

---

### USER MANAGEMENT

| Feature | DSM Control | InvGate |
|---|---|---|
| **RBAC** | ✅ 5 roles (super_admin, admin, technician, procurement_manager, employee) | ✅ Role-based access |
| **User invitation** | ✅ Email + CSV bulk import | ✅ |
| **OAuth login** | ✅ Google + Microsoft | ✅ |
| **SAML SSO** | On roadmap (E42) | ✅ Multiple SAML providers |
| **Directory sync** | On roadmap (E42) | ✅ LDAP/AD |
| **Magic link auth** | ✅ | ❌ |
| **Menu visibility config** | ✅ Admin can hide nav items per role | ❌ |
| **Concurrent licensing** | ❌ | ✅ (Enterprise) |

**Verdict:** InvGate wins on SSO/directory maturity. DSM wins on magic link auth and nav visibility configuration.

---

### WORKFLOW TEMPLATES

| Feature | DSM Control | InvGate |
|---|---|---|
| **Workflow templates** | ✅ Admin-defined per request type | ✅ Visual workflow builder |
| **Checklist items** | ✅ Required/optional items, inline completion | ❌ (checklist as workflow steps) |
| **Resolution guard** | ✅ Block resolve until required items complete | ❌ |
| **No-code builder** | ❌ (code/admin config) | ✅ Drag & drop |
| **Multi-department workflows** | ❌ (IT-focused) | ✅ HR, Facilities, Legal |

**Verdict:** InvGate wins on no-code workflow builder and multi-department support. DSM wins on checklist enforcement (resolution guard).

---

## Summary: Where Each Product Wins

### DSM Control Wins (14 categories)

| Area | Why |
|---|---|
| **Pricing** | 2-4x cheaper. Flat per-company, not per-agent. Free tier + open source |
| **EU compliance (NIS2/DORA/ISO 27001/CRA)** | Full compliance management system — dashboards, control mapping, evidence collection, gap analysis, audit export. InvGate has zero product-level compliance |
| **Security incident management** | Dedicated module: types, severity, attack vectors, NIS2 24h/72h/30d timelines, DORA 4h deadline, post-mortem, linked assets/vendors |
| **Vulnerability management** | CVE tracking, CVSS scoring, remediation tickets, patch status, exposure score — not available in InvGate |
| **Procurement** | Full PO lifecycle, budget enforcement, equipment profiles, auto-asset creation from POs |
| **Shipping & logistics** | Full shipment workflow with carriers, tracking, returns. InvGate has none |
| **Scheduled maintenance** | Templates, plans, records, checklists, overdue alerts. InvGate treats maintenance as contract type |
| **Appointment scheduling** | Calendar-based booking. InvGate has none |
| **Asset checkout/custody** | Condition tracking, employee acceptance, GDPR sanitization. Unique feature |
| **Vendor/supply chain risk** | DORA Art.28 mapping, critical ICT flags, concentration risk, dependency analysis |
| **CMDB depth** | BIA (RTO/RPO), dependency graph visualization, structured CI relationships |
| **Open source** | AGPL tier for self-hosting. InvGate is proprietary only |
| **EU data sovereignty** | EU-hosted. InvGate is Argentina-based |
| **MCP server** | 60+ AI assistant tools. InvGate has no AI integration protocol |

### InvGate Wins (10 categories)

| Area | Why |
|---|---|
| **ITIL maturity** | Problem management, change management (CAB), service catalog — DSM lacks these |
| **No-code workflow builder** | Visual drag & drop. DSM uses code/admin config |
| **Auto-discovery** | Agent-based + agentless network scanning. DSM has this on roadmap only |
| **Software license management** | Metering, compliance, deployment. DSM has on roadmap |
| **Mobile app** | Native Android + iOS. DSM has PWA on roadmap |
| **Integration ecosystem** | SCCM, Filewave, Kandji, Lansweeper, Zapier, LDAP/AD. DSM is API-first but fewer native integrations |
| **SSO/directory sync** | Multiple SAML + LDAP/AD. DSM has OAuth only, SAML on roadmap |
| **Customizable dashboards** | Fully customizable with drill-down. DSM has predefined dashboards |
| **Enterprise Service Management** | HR, Facilities, Legal service desks. DSM is IT-only |
| **Gamification** | Points, rankings, leaderboards for agent motivation |

---

## Strategic Implications

### InvGate's Compliance Blind Spot Is Our Moat

InvGate has 18 years of ITSM/ITAM maturity, $30M revenue, and strong market recognition. In a pure ITSM feature war, they win on polish and breadth.

But compliance is where the market is moving. With NIS2 enforcement in 2026 and DORA already active, EU companies need compliance built into their operational tools — not just blog posts about it. InvGate's compliance positioning is entirely content marketing. Their product has zero compliance dashboards, zero framework mapping, zero evidence collection.

DSM Control has:
- Compliance dashboards with framework overview and scoring
- Control mapping to NIS2 Art.21, DORA Chapter II, ISO 27001 Annex A
- Evidence collection linked to specific controls
- Security incident management with regulatory timelines
- Vulnerability management with CVE tracking
- Risk register with heat map
- Vendor risk with DORA Art.28 compliance
- Audit-ready exports per framework

This is not a feature InvGate can add in a sprint — it's a fundamental architectural choice that DSM built from day one.

### The Pricing Argument Is Clear

A 50-person company with 10 IT agents:
- **InvGate:** ~$505/month ($40×10 agents + $0.21×500 nodes)
- **DSM Control:** €149-299/month (flat, all included)

The per-agent model punishes companies that want to empower more people to handle IT. DSM's flat pricing encourages adoption.

### Where We Need to Catch Up

The honest gaps to close (from roadmap):
1. **Auto-discovery (E32)** — Critical for mid-market. InvGate's agent-based scanning is a selling point
2. **Software license management (E21)** — Table stakes for ITAM buyers
3. **Change management (E33)** — ITIL buyers expect it
4. **Mobile app (E28)** — Increasingly expected
5. **SSO/SAML (E42)** — Enterprise requirement
6. **Multi-channel intake (E23)** — Email-to-ticket is baseline

These are all on the roadmap. The compliance moat buys time to close these gaps.

---

## Sources

- [InvGate Service Management](https://invgate.com/service-management)
- [InvGate Asset Management](https://invgate.com/asset-management)
- [InvGate CMDB](https://invgate.com/asset-management/cmdb)
- [InvGate Self-Service Portal](https://invgate.com/service-management/self-service)
- [InvGate Knowledge Base](https://invgate.com/service-management/knowledge-base)
- [InvGate IT Security](https://invgate.com/asset-management/it-security)
- [InvGate Audits & Compliance](https://invgate.com/solutions/audits-and-compliance)
- [InvGate Pricing](https://invgate.com/pricing)
- [InvGate Integrations](https://invgate.com/integrations)
- [InvGate 2026 Midmarket Champion](https://blog.invgate.com/invgate-named-2026-champion-in-midmarket-itsm-info-tech)
- [InvGate NIS2 Blog](https://blog.invgate.com/nis2-requirements-asset-management)
- [InvGate ISO 27001 Certification](https://blog.invgate.com/invgate-obtains-iso-27001-certification)
- [InvGate $35M Funding](https://blog.invgate.com/invgate-enters-a-new-era)
- [InvGate Revenue (Latka)](https://getlatka.com/companies/invgate.com)
- [InvGate Review (Research.com)](https://research.com/software/reviews/invgate-review)
- [InvGate Review (Siit.io)](https://www.siit.io/tools/trending/invgate-service-desk-review)
- [InvGate Pricing Analysis (SmartSuite)](https://www.smartsuite.com/blog/invgate-pricing)
