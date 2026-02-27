# Why DSM Control is Necessary for DORA Compliance

**Date:** 2026-02-27
**Regulation:** Regulation (EU) 2022/2554 — Digital Operational Resilience Act
**Status:** Applicable since January 17, 2025
**Scope:** Financial entities and their critical ICT third-party service providers in the EU

---

## What is DORA

The Digital Operational Resilience Act (DORA) is an EU regulation that establishes a comprehensive framework for the digital operational resilience of the financial sector. It requires financial entities to ensure they can withstand, respond to, and recover from all types of ICT-related disruptions and threats.

Unlike NIS2 (which covers 18 sectors broadly), DORA is sector-specific — it targets the financial industry with deeper, more prescriptive requirements. However, DORA and NIS2 share significant overlap in areas like ICT asset management, incident handling, and third-party risk.

### Who Must Comply

- **Banks and credit institutions**
- **Insurance and reinsurance companies**
- **Investment firms and fund managers**
- **Payment institutions and electronic money institutions**
- **Crypto-asset service providers**
- **Central securities depositories**
- **Trading venues and trade repositories**
- **Credit rating agencies**
- **Crowdfunding service providers**
- **ICT third-party service providers** designated as critical (cloud providers, SaaS platforms, data centers serving financial entities)

### Penalties

- Financial entities: penalties determined by national competent authorities, proportionate to the severity of the breach
- Critical ICT third-party providers: fines up to €5M, or up to 1% of average daily worldwide turnover for up to 6 months
- Management bodies are personally responsible for ensuring ICT risk management compliance
- Supervisory authorities can require remediation, restrict activities, or withdraw authorizations

---

## DORA Requirements Mapped to DSM Control

DORA is structured around five pillars. DSM Control provides direct capabilities for three of them.

### Pillar 1: ICT Risk Management (Articles 5-16)

This is DORA's core pillar and where DSM Control's value is strongest.

| DORA Requirement | What it means | DSM Control Capability |
|---|---|---|
| **Article 8(1) — Identification of ICT assets** | "Financial entities shall identify, classify and adequately document all ICT supported business functions, roles and responsibilities, and the information assets and ICT assets supporting those functions." | **Core product functionality.** DSM Control maintains a complete inventory of ICT assets with classification, owner, location, status, and full metadata. This is the foundational requirement of DORA's risk management framework. |
| **Article 8(4) — Asset inventory maintenance** | Financial entities shall "on a continuous basis, identify all sources of ICT risk, in particular the risk exposure to and from other financial entities, and shall assess cyber threats and ICT vulnerabilities relevant to their ICT supported business functions, information assets and ICT assets." | Asset inventory with manufacturer, model, firmware version enables instant identification of devices affected by newly disclosed vulnerabilities. Continuous inventory maintenance is enforced by the system. |
| **Article 9(1) — Protection and prevention** | Financial entities shall "continuously monitor and control the security and functioning of ICT systems and tools." | Asset lifecycle management tracks every device from purchase to decommission. Status tracking, assignment management, and maintenance schedules ensure continuous monitoring of ICT asset state. |
| **Article 9(2) — ICT security policies** | Policies shall include "the management of ICT assets, including the documentation and control of all ICT assets." | DSM Control is the implementation layer for ICT asset management policies. Every asset is documented, controlled, and auditable. |
| **Article 9(4)(d) — Network security** | Implement policies for "securing the network infrastructure, including documentation of all network connections and data flows." | Network equipment inventory (routers, switches, firewalls, access points) with location and connection documentation. |
| **Article 11 — Response and recovery** | Financial entities shall put in place an ICT response and recovery framework with plans to respond to and recover from ICT-related incidents. | Incident management linked to specific assets. When an ICT incident occurs, the affected devices are immediately identified, documented, and tracked through resolution. |
| **Article 12 — Backup policies** | Maintain backup policies and procedures, and restoration and recovery plans. | Asset inventory identifies all devices that require backup. Maintenance plans can include backup verification tasks. |
| **Article 13 — Learning and evolving** | Financial entities shall gather information on vulnerabilities, cyber threats, and ICT-related incidents and review them after major incidents. | Incident history per asset reveals patterns. Post-incident analysis is documented within the incident timeline. Vulnerability response is tracked per device. |

### Pillar 2: ICT-Related Incident Management (Articles 17-23)

| DORA Requirement | What it means | DSM Control Capability |
|---|---|---|
| **Article 17 — Incident management process** | Financial entities shall define, establish and implement an ICT-related incident management process to detect, manage and notify ICT-related incidents. | Structured incident workflow: creation against specific asset, classification, assignment, status tracking, resolution. Every step timestamped. |
| **Article 18 — Classification of ICT-related incidents** | Incidents shall be classified based on impact, including "the criticality of the services affected, including the financial entity's transactions and operations." | Incidents linked to assets that have criticality classification. Impact assessment informed by which assets and business functions are affected. |
| **Article 19 — Reporting major ICT-related incidents** | Major incidents must be reported to the competent authority: initial notification within 4 hours of classification, intermediate report within 72 hours, final report within 1 month. | Incident creation timestamp documents when the incident was identified. Asset linkage shows exactly which systems were affected. Full timeline provides the evidence base for regulatory reporting at each stage. |

### Pillar 4: ICT Third-Party Risk Management (Articles 28-44)

| DORA Requirement | What it means | DSM Control Capability |
|---|---|---|
| **Article 28(3) — Register of ICT third-party arrangements** | Financial entities shall maintain a register of all contractual arrangements on the use of ICT services provided by ICT third-party service providers. | Vendor registry with purchase orders provides traceability from each ICT asset to its supplier. Asset inventory documents which third-party products and services are deployed. |
| **Article 28(5) — Risk assessment of third-party providers** | Financial entities shall assess the risks arising from third-party ICT arrangements. | Asset inventory by vendor enables instant visibility into exposure to any single third-party provider. If a vendor has a security incident, you immediately know which of your assets are affected. |

---

## DORA Audit: What the Supervisor Expects

DORA gives supervisory authorities (national financial regulators) the power to inspect financial entities' digital operational resilience. Here's what they will ask:

| What the supervisor asks | Without DSM Control | With DSM Control |
|---|---|---|
| "Show me your ICT asset register (Article 8)" | Excel file, possibly outdated, no classification | Live inventory with classification, owners, locations — always current |
| "How do you identify which assets are affected when a vulnerability is disclosed?" | Manual investigation, phone calls, spreadsheet searches | Filter by manufacturer + model + firmware version. Result in seconds. |
| "Show me the incident management process for this ICT event (Article 17)" | Emails and tickets in a separate system, not linked to assets | Incident created against specific asset, full timeline with every action documented |
| "What is your exposure to [third-party provider X]? (Article 28)" | "Let me check..." — days of investigation | Filter assets by vendor. Instant visibility into all devices from that provider: how many, where, who has them. |
| "Show me that you responded to the [product X] vulnerability within the required timeline" | No documented evidence | Incident timeline: detection timestamp, affected assets identified, remediation actions, completion — all exportable |
| "How do you ensure ICT assets are maintained? (Article 9)" | Ad-hoc maintenance, no records | Maintenance module with scheduled and completed tasks per asset, full history |

---

## DORA Compliance Gaps That DSM Control Closes

| Common Gap | DORA Risk | How DSM Control Closes It |
|---|---|---|
| No ICT asset inventory | Cannot demonstrate Article 8 compliance — the foundational requirement | Centralized inventory with all ICT assets, classification, owners, and metadata |
| Assets not classified by criticality | Cannot assess operational impact of incidents (Article 18) | Asset classification fields with criticality levels |
| Incidents not linked to assets | Cannot demonstrate which systems were affected during an incident (Article 17-19) | Incidents natively linked to assets — impact assessment based on real asset data |
| No vendor visibility | Cannot manage third-party ICT risk (Article 28) | Vendor registry with asset-to-vendor traceability |
| No maintenance records | Cannot demonstrate protection and prevention measures (Article 9) | Maintenance module with scheduling, completion tracking, and history |
| Manual vulnerability response | Days to assess exposure, cannot meet reporting timelines (Article 19) | Instant search by manufacturer, model, firmware — affected devices identified in seconds |
| No audit trail | Cannot demonstrate compliance to supervisors | Every action on every asset logged with user, timestamp, and details |

---

## DORA-NIS2 Synergy

Financial entities subject to DORA are also often in scope for NIS2. The two regulations complement each other:

| Requirement | DORA Reference | NIS2 Reference | DSM Control Coverage |
|---|---|---|---|
| ICT asset inventory | Article 8 | Article 21(i) | Yes — single source |
| Incident management | Articles 17-19 | Article 21(b), Article 23 | Yes — asset-linked incidents |
| Third-party/supply chain risk | Articles 28-44 | Article 21(d) | Yes — vendor and asset tracking |
| Business continuity | Articles 11-12 | Article 21(c) | Yes — maintenance plans, criticality |
| Audit trail | Article 8, Article 17 | Article 21(f) | Yes — full audit trail |
| Response and recovery | Article 11 | Article 21(c) | Yes — incident workflow with resolution tracking |

**One platform, dual compliance.** DSM Control provides the ICT asset management evidence base that both DORA and NIS2 require.

---

## DORA Timeline

| Date | DORA Milestone | Impact |
|---|---|---|
| **January 2023** | DORA enters into force | Preparation phase begins |
| **January 17, 2025** | DORA becomes applicable | Financial entities must comply. Supervisory inspections can begin. |
| **March 2026** | DSM Control available | Financial entities that adopt DSM Control gain immediate Article 8 compliance capability |
| **2026-2027** | First wave of DORA supervisory reviews | Supervisors assess digital operational resilience. Asset inventory is the first thing they check. |

DORA is already applicable — financial entities should be in compliance **now**. Organizations still relying on spreadsheets for ICT asset management are exposed to supervisory findings.

---

## Specific DORA Scenarios Where DSM Control is Critical

### Scenario 1: Critical ICT Third-Party Incident

Your cloud provider suffers a security breach. Under DORA Article 28, you must assess the impact on your operations.

**Question:** "What services and devices do we have from this provider?"

- **Without DSM Control:** Manual investigation across departments. Days to compile a complete picture.
- **With DSM Control:** Filter assets by vendor. Instant list of all devices, services, and locations. Incident created for each affected asset. Impact assessment completed in minutes.

### Scenario 2: Vulnerability in Banking Software

A critical vulnerability is discovered in the core banking platform's infrastructure component (a network switch model used across branch offices).

**Question:** "How many branch offices have the affected switch model?"

- **Without DSM Control:** Call each branch, check old purchase records. Weeks of uncertainty.
- **With DSM Control:** Filter by model. Result: 23 switches across 8 branches. Maintenance tasks created for firmware update. Dashboard tracks completion per branch.

### Scenario 3: DORA Supervisory Inspection

The national financial supervisor conducts a DORA inspection and requests evidence of your ICT risk management framework.

**Question:** "Demonstrate your ICT asset identification and documentation process (Article 8)"

- **Without DSM Control:** Scramble to compile spreadsheets, hope they're current, no audit trail.
- **With DSM Control:** Live asset inventory with full history. Every asset documented from purchase to current state. Audit trail shows every change. Export for the supervisor in minutes.

---

## Summary

DORA makes ICT asset management a regulatory requirement for the entire EU financial sector. Article 8's mandate to "identify, classify and adequately document all ICT assets" is not optional — it's the foundation of the entire DORA compliance framework.

DSM Control provides the implementation layer for DORA's ICT asset management requirements:

- **Identify** → Complete ICT asset inventory with manufacturer, model, serial number
- **Classify** → Asset classification by criticality and business function
- **Document** → Full lifecycle documentation from purchase to decommission
- **Monitor** → Continuous maintenance and status tracking
- **Respond** → Incident management linked to specific assets
- **Prove** → Audit trail with timestamps for every action

For financial entities, DSM Control transforms Article 8 compliance from a manual, error-prone process into an automated, auditable system. For ICT service providers to the financial sector, it demonstrates the operational maturity that financial clients increasingly demand.

DORA is applicable now. The time to comply was January 2025. Every day without proper ICT asset management is a day of regulatory exposure.
