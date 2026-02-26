# Why DSM Control is Necessary for CRA Compliance

**Date:** 2026-02-26
**Regulation:** Regulation (EU) 2024/2847 — Cyber Resilience Act
**Status:** Entered into force December 2024. Reporting obligations from September 2026. Full compliance required by December 2027.
**Scope:** Manufacturers, importers, and distributors of products with digital elements in the EU

---

## What is the CRA

The Cyber Resilience Act (CRA) is an EU regulation that establishes cybersecurity requirements for **products with digital elements** — any hardware or software product that connects to a network. Unlike NIS2 (which targets the organizations that use technology), the CRA targets the organizations that **make, import, or distribute** technology products.

### Who Must Comply

- **Manufacturers** of products with digital elements (hardware with embedded software, standalone software, IoT devices)
- **Importers** who place products from outside the EU on the EU market
- **Distributors** who make products available on the EU market
- **Open source stewards** (limited obligations for non-commercial open source)

### What Products Are Covered

Virtually any product that connects to a network:
- Routers, switches, firewalls, access points
- IoT devices (sensors, cameras, smart devices)
- Industrial control systems and PLCs
- Laptops, servers, mobile devices (hardware aspect)
- Operating systems, firmware, applications (software aspect)
- Smart home devices, wearables

### Penalties

- Up to €15M or 2.5% of global annual turnover for non-compliance with essential requirements
- Up to €10M or 2% for other violations
- Up to €5M or 1% for providing incorrect or misleading information

---

## CRA Requirements Mapped to DSM Control

The CRA has two primary dimensions relevant to DSM Control:

1. **For companies that manufacture/import products with digital elements** — they need to track their own products, vulnerabilities, and incidents
2. **For companies that use products with digital elements** — they need to track what products they have deployed and respond when vulnerabilities are disclosed by manufacturers

### Dimension 1: CRA Obligations for Manufacturers/Importers

Companies that make or import hardware/software products must meet the following requirements. DSM Control helps them manage the internal IT assets and infrastructure they use to develop, test, and ship their products.

| CRA Requirement | What it means | DSM Control Capability |
|---|---|---|
| **Article 13(6) — Documentation and traceability** | Manufacturers must maintain technical documentation for the expected lifetime of the product (minimum 5 years) | Asset lifecycle management provides full traceability from purchase to decommission. Every device used in development, testing, and production is documented. |
| **Article 13(7) — Vulnerability handling** | Manufacturers must identify and document vulnerabilities in their products and remediate them in a timely manner | When a vulnerability is discovered in a component or device used internally, DSM Control allows instant search by manufacturer, model, or firmware version. Affected devices are identified in seconds. |
| **Article 14 — Reporting obligations** | Manufacturers must report actively exploited vulnerabilities and severe incidents to ENISA within 24 hours (early warning) and 72 hours (notification) | Incident management with timestamps provides documented evidence of when a vulnerability was identified and what actions were taken. Asset linkage shows exactly which devices were affected. |
| **Article 13(5) — Secure by default** | Products must be delivered with secure default configurations | Asset inventory with custom fields can track configuration status per device — including whether devices shipped to customers or used internally meet secure-by-default requirements. |
| **Article 13(12) — SBOM (Software Bill of Materials)** | Manufacturers must identify and document components and dependencies in their products | While DSM Control is not an SBOM tool, it provides the hardware inventory layer that complements SBOM: what physical devices run what software, where, and owned by whom. |
| **Article 10(10) — Withdrawal and recall** | If a product has an unmitigable vulnerability, manufacturers must withdraw or recall it | Asset inventory enables instant identification of all units of a specific product model — whether deployed internally, in warehouse, or assigned to users. Facilitates recall execution. |

### Dimension 2: CRA Impact on Companies That Use Products

This is where DSM Control's value is strongest. The CRA creates a new class of obligations for manufacturers to disclose vulnerabilities — which means the companies that **use** those products need to be able to respond.

| Scenario | What happens | Without DSM Control | With DSM Control |
|---|---|---|---|
| **Manufacturer discloses a vulnerability** | CRA Article 14 requires manufacturers to notify ENISA and publish advisories. Your organization receives a notification that a product you use has a critical vulnerability. | "Do we have any of those?" → phone calls, checking spreadsheets, asking around. Days to assess exposure. | Filter by manufacturer + model. In 30 seconds: how many units, where they are, who has them. Create incidents for all affected devices immediately. |
| **Manufacturer issues a firmware update** | CRA Article 13(8) requires manufacturers to provide security updates. Your organization needs to identify all affected devices and apply the update. | Manual inventory check, hope the spreadsheet is current, manually track which devices were updated. | Filter affected devices, create a maintenance task, track update status per device. Dashboard shows completion percentage. |
| **Manufacturer recalls a product** | CRA Article 10(10) requires withdrawal of products with unmitigable vulnerabilities. You need to identify and remove all units from service. | Panic. Count by memory. Miss devices in remote offices. | Instant device list with locations and assigned users. Decommission workflow for each unit. Full audit trail of the recall process. |
| **Auditor asks about your response to CRA disclosures** | Under NIS2, your organization must demonstrate incident handling capabilities — including responding to vulnerabilities disclosed under CRA. | No documented evidence of response process. | Incident timeline shows: when you learned about the vulnerability, what devices were affected, what actions you took, and when each was resolved. |

---

## The CRA-NIS2 Connection

The CRA and NIS2 are designed to work together:

- **CRA** requires manufacturers to report vulnerabilities and provide security updates
- **NIS2** requires organizations to handle incidents and maintain their IT assets securely

When a manufacturer reports a vulnerability under CRA, every NIS2-affected organization that uses that product must be able to:

1. **Know if they have the affected product** → Asset inventory
2. **Know where it is and who has it** → Assignment and location tracking
3. **Respond within the NIS2 reporting timeline** → Incident management
4. **Document the response for auditors** → Audit trail

DSM Control provides all four capabilities in a single platform.

```
CRA: Manufacturer discovers vulnerability
  → Reports to ENISA within 24h
  → Publishes advisory to users

NIS2: Your organization receives the advisory
  → DSM Control: Search by model → 7 devices found
  → DSM Control: Create incident for all 7
  → DSM Control: Track remediation per device
  → DSM Control: Export timeline for auditor
```

---

## CRA Timeline and DSM Control Readiness

| Date | CRA Milestone | Impact on DSM Control Users |
|---|---|---|
| **December 2024** | CRA enters into force | Awareness phase — companies start planning |
| **September 2026** | Reporting obligations begin | Manufacturers start reporting vulnerabilities to ENISA. Organizations using those products need to be able to respond. **DSM Control's "search by model" becomes critical.** |
| **December 2027** | Full compliance required | All products on the EU market must meet CRA cybersecurity requirements. Complete lifecycle tracking and vulnerability response capability required. |

DSM Control launches in March 2026 — **6 months before CRA reporting obligations begin.** Companies that adopt DSM Control before September 2026 will be ready to respond to the first wave of CRA-mandated vulnerability disclosures.

---

## CRA Product Categories and DSM Control Relevance

The CRA categorizes products into three tiers:

| Category | Examples | DSM Control Relevance |
|---|---|---|
| **Default (non-critical)** | Smart speakers, smart TVs, toys, generic IoT | Low — consumer products, not typical enterprise IT |
| **Important Class I** | Routers, switches, OS, password managers, VPNs, firewalls, microcontrollers | **High — these are the core devices in any company's IT inventory. DSM Control tracks exactly these device types.** |
| **Important Class II** | Hypervisors, container runtimes, PKI systems, industrial firewalls, smart meters | **High — critical infrastructure devices. Need lifecycle tracking and incident response.** |
| **Critical** | Hardware security modules, smartcard readers, smart meter gateways | Medium — specialized devices, fewer units but higher impact |

**The majority of CRA Important Class I and II products are exactly the devices that DSM Control manages:** routers, switches, firewalls, servers, endpoints, network equipment, and industrial devices.

---

## Specific CRA Scenarios Where DSM Control is Critical

### Scenario 1: The Zero-Day Disclosure

A manufacturer of network switches discovers a zero-day vulnerability and reports it to ENISA under CRA Article 14. ENISA coordinates disclosure. Your organization receives a CERT advisory.

**Question:** "We use SwitchCo Model X200 in our network. How many do we have, where are they, and are any exposed to the internet?"

- **Without DSM Control:** Hours of investigation, calls to each office, checking old purchase orders in email
- **With DSM Control:** Filter by manufacturer "SwitchCo" + model "X200". Result: 12 units — 4 in Madrid datacenter, 3 in Barcelona office, 2 in Valencia, 3 in warehouse. Incident created for all 12. Remediation tracked per unit.

### Scenario 2: The Firmware Recall

A router manufacturer determines that firmware version 4.2.1 has an unmitigable vulnerability. Under CRA Article 10(10), they issue a recall for all affected devices.

**Question:** "Which of our routers are running firmware 4.2.1?"

- **Without DSM Control:** No way to know without physically checking each router
- **With DSM Control:** Custom field "firmware_version" filtered to "4.2.1". Result: 5 devices. Decommission workflow initiated. Replacement devices assigned from warehouse stock.

### Scenario 3: The Supply Chain Audit

Your organization is audited under NIS2. The auditor asks: "When the CRA-mandated vulnerability report for [product X] was published in October, how did your organization respond?"

- **Without DSM Control:** No documented evidence of response
- **With DSM Control:** Incident #247 created October 3rd at 09:14. Linked to 8 affected devices. Firmware update applied to all 8 by October 5th. Incident closed October 5th at 16:30. Full timeline exportable.

---

## Summary

The CRA creates a new reality: manufacturers will be **required** to disclose vulnerabilities, and organizations that use those products will need to respond rapidly and document their response. This transforms IT asset management from a "nice to have" into a compliance-critical capability.

DSM Control provides the essential layer that connects CRA vulnerability disclosures to the actual devices in your organization:

- **Know what you have** → Asset inventory by manufacturer, model, firmware
- **Know where it is** → Location and assignment tracking
- **Respond fast** → Incident creation linked to affected assets
- **Prove you responded** → Audit trail with timestamps

For manufacturers, DSM Control manages the internal IT infrastructure used to develop and ship products. For users, it provides the response capability that CRA disclosures demand.

The CRA reporting obligations start in **September 2026**. The time to prepare is now.
