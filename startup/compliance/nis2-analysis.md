# Why DSM Control is Necessary for NIS2 Compliance

**Date:** 2026-02-26
**Regulation:** Directive (EU) 2022/2555 — Network and Information Security Directive 2
**Status:** Enforceable since October 2024 (transposition deadline for Member States)
**Scope:** Essential and important entities across 18 sectors in the EU

---

## What is NIS2

NIS2 is the EU's cybersecurity directive that replaces the original NIS Directive (2016). It significantly expands the number of organizations in scope, introduces stricter requirements, and adds personal liability for management. It applies to organizations in 18 sectors including energy, transport, health, digital infrastructure, manufacturing, food, chemicals, and public administration.

### Who Must Comply

- **Essential entities:** large organizations in critical sectors (energy, transport, health, digital infrastructure, banking, water)
- **Important entities:** medium organizations (50+ employees or €10M+ revenue) in the same sectors plus manufacturing, food, chemicals, postal services, waste management, and digital providers
- **Supply chain:** any company that provides ICT services or products to essential/important entities, regardless of size

### Penalties

- Essential entities: up to €10M or 2% of global annual turnover
- Important entities: up to €7M or 1.4% of global annual turnover
- **Personal liability:** management bodies can be held personally liable for non-compliance

---

## NIS2 Requirements Mapped to DSM Control

### Article 21 — Cybersecurity Risk-Management Measures

Article 21 is the core of NIS2. It requires organizations to implement "appropriate and proportionate technical, operational and organisational measures to manage the risks posed to the security of network and information systems."

The following table maps each Article 21 requirement to specific DSM Control capabilities.

| NIS2 Article 21 Requirement | What it means in practice | DSM Control Feature | How it works |
|---|---|---|---|
| **(a) Policies on risk analysis and information system security** | Document what systems you have and their risk exposure | Asset inventory with status, type, and classification | Every device is registered with its type, manufacturer, model, serial number, and risk classification. Exportable asset register serves as the foundation for risk analysis. |
| **(b) Incident handling** | Detect, report, and respond to incidents with documented procedures | Incident management with asset-linked tickets | Every incident is created against a specific asset. Timeline shows what happened, when, and what actions were taken. Incidents cannot exist without being linked to a device — this is by design. |
| **(c) Business continuity and crisis management** | Know what assets are critical and plan for their failure | Asset criticality classification + maintenance plans | Assets can be classified by criticality. Preventive maintenance schedules ensure critical devices are proactively maintained. Incident history per asset reveals which devices are reliability risks. |
| **(d) Supply chain security** | Know what hardware and software you deploy and from whom | Purchase orders with vendor tracking | Every asset is traceable to a purchase order, a vendor, and a delivery date. Vendor registry provides a complete view of the supply chain for IT assets. |
| **(e) Security in network and information systems acquisition, development and maintenance** | Track devices from acquisition through their entire lifecycle | Full lifecycle management (purchase → warehouse → assignment → incidents → maintenance → decommission) | DSM Control manages the complete device lifecycle. Every stage is documented with timestamps, responsible persons, and audit trail. |
| **(f) Policies and procedures to assess the effectiveness of cybersecurity risk-management measures** | Measure whether your controls are working | Dashboard with real-time metrics + audit trail | Dashboard shows open incidents, SLA compliance, asset status distribution, and maintenance adherence. Audit trail documents every action taken on every asset. |
| **(g) Basic cyber hygiene practices and cybersecurity training** | Know who has what devices and ensure they are properly managed | Assignment management with user history | Every asset assignment is documented: who has the device, since when, and what incidents occurred during their possession. Offboarding workflows ensure devices are recovered. |
| **(h) Policies on the use of cryptography and encryption** | Know which devices handle encrypted data | Asset metadata and classification | Assets can be tagged with data classification levels, indicating which devices handle sensitive or encrypted data. |
| **(i) Human resources security, access control policies and asset management** | Explicitly mentioned: asset management is a required measure | **Core product functionality** | DSM Control is purpose-built for IT asset management. Asset inventory, access tracking via assignments, and role-based permissions are native capabilities. |
| **(j) Use of multi-factor authentication or continuous authentication solutions** | Know which devices have MFA-protected access | Asset metadata and custom fields | Custom fields can track security configurations per device, including MFA status, encryption status, and compliance flags. |

### Article 23 — Reporting Obligations

NIS2 requires incident reporting to the national CSIRT within strict timelines.

| Reporting Requirement | Timeline | DSM Control Support |
|---|---|---|
| **Early warning** | Within 24 hours of becoming aware | Incident creation timestamp provides documented awareness time. Asset linkage immediately shows which device and where. |
| **Incident notification** | Within 72 hours | Incident detail view provides all required information: affected asset, location, assigned user, impact assessment, and actions taken. |
| **Final report** | Within 1 month | Full incident timeline with all updates, resolution steps, and root cause — exportable as a report. Asset history shows whether the device had prior incidents. |

### Article 20 — Governance (Management Accountability)

NIS2 makes management bodies personally responsible for approving and overseeing cybersecurity risk-management measures. They must be able to demonstrate that appropriate measures are in place.

| Governance Requirement | DSM Control Support |
|---|---|
| Management must approve cybersecurity measures | Dashboard provides executive overview of asset status, open incidents, and compliance posture — suitable for management reporting. |
| Management must oversee implementation | Audit trail documents every action by every user. Role-based permissions ensure separation of duties. |
| Management must ensure adequate resources | Asset cost tracking and purchase order management provide visibility into IT security investment. |

---

## The Three Questions Every NIS2 Auditor Asks

Based on Article 21(i) and the broader directive, NIS2 audits center on three fundamental questions:

| Auditor Question | Without DSM Control | With DSM Control |
|---|---|---|
| **"What devices does your organization have on its network?"** | Spreadsheet, outdated, incomplete, no single source of truth | Complete asset inventory with status, location, and responsible person — always current |
| **"Who has access to which devices?"** | "Let me check with HR" or "I think Maria has that laptop" | Assignment history with temporal traceability — who had what, when, and every change documented |
| **"What incidents have those devices had?"** | "We had some tickets in the helpdesk but they're not linked to specific devices" | Every incident linked to the specific asset, with full timeline, actions taken, and resolution — exportable |

---

## NIS2 Compliance Gaps That DSM Control Closes

| Common Gap in SMBs | NIS2 Risk | How DSM Control Closes It |
|---|---|---|
| No asset inventory | Cannot demonstrate Article 21(i) compliance | Centralized inventory with all devices, status, and metadata |
| Incidents tracked separately from assets | Cannot link incidents to specific devices for Article 23 reporting | Incidents are natively linked to assets — no integration needed |
| No purchase-to-decommission traceability | Cannot demonstrate supply chain security (Article 21(d)) | Full lifecycle from purchase order to decommission with vendor tracking |
| No audit trail | Cannot prove what actions were taken and by whom | Every action on every asset is logged with user, timestamp, and details |
| Offboarding gaps — devices not recovered | Uncontrolled assets in the field | Assignment management with offboarding workflows and device recovery tracking |
| No visibility into device age or maintenance | Cannot demonstrate Article 21(c) business continuity measures | Maintenance plans with calendar, warranty tracking, and device age visibility |
| Reactive incident response | Cannot meet Article 23 reporting timelines | Structured incident workflow with timestamps for every stage |

---

## Why Spreadsheets Are Not Enough for NIS2

| Capability | Excel/Google Sheets | DSM Control |
|---|---|---|
| Single source of truth | No — multiple versions, no access control | Yes — centralized, role-based access |
| Audit trail | No — no history of who changed what | Yes — every change logged automatically |
| Incident-to-asset linking | No — separate systems, manual correlation | Yes — native, enforced by design |
| Reporting for auditors | Manual export, no consistency | Structured exports, always up to date |
| Real-time visibility | No — stale data | Yes — dashboard with live metrics |
| Multi-user concurrent access | Limited, conflict-prone | Yes — designed for teams |
| Automated workflows | No | Yes — assignment, maintenance, incident workflows |

---

## Relevant NIS2 Sectors and DSM Control Fit

| Sector | Why NIS2 applies | DSM Control value |
|---|---|---|
| **Healthcare** | Hospitals and clinics are essential entities. Devices include medical stations, diagnostic equipment, admin laptops. | Full inventory of medical and IT devices with incident tracking per asset. |
| **Manufacturing** | Medium and large manufacturers are important entities. PLCs, control stations, office devices. | Lifecycle management for production and office equipment. Vendor tracking for supply chain compliance. |
| **Financial services** | Banks, insurance, fintechs — also subject to DORA. | Combined NIS2 + DORA compliance from a single platform. |
| **Transport and logistics** | Devices distributed across sites, warehouses, vehicles. | Multi-location asset tracking with assignment management. |
| **Digital infrastructure / SaaS** | Cloud providers, DNS operators, data centers. | Internal IT asset management + audit trail for their own compliance. |
| **Food and beverage** | Production facilities with IT and OT devices. | Asset tracking for both office IT and production floor devices. |

---

## Summary

DSM Control is not a generic cybersecurity tool. It is purpose-built for the specific requirements that NIS2 Article 21(i) explicitly mandates: **asset management.** It provides the documented, auditable, device-level traceability that NIS2 requires — linking every device to its lifecycle, every incident to its device, and every action to its audit trail.

For SMBs entering NIS2 scope for the first time, DSM Control replaces the spreadsheet with a compliance-ready system — without the cost or complexity of enterprise tools like ServiceNow or Freshservice.
