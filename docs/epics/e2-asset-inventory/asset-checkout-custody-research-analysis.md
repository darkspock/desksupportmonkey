# ITAM Asset Checkout, Custody & Handover: Market Research Analysis

**Date:** 2026-02-26
**Tools Analyzed:** Snipe-IT, GLPI, Freshservice, ServiceNow HAM, InvGate Assets, Lansweeper
**Purpose:** Understand market best practices for asset checkout/checkin, custody tracking, digital signatures, location vs. assignment, status lifecycle, and handover documents.

---

## 1. Asset Checkout / Checkin Workflow

### Snipe-IT (Open Source - Gold Standard for Checkout/Checkin)

Snipe-IT has the most explicit and well-defined checkout/checkin model in the open-source ITAM space:

- **Checkout** = marking an asset as being "in the possession of someone else." The asset cannot be checked out to another person until it is checked back in. This prevents "double-booking."
- **Checkin** = indicating the asset is "back in your possession, or potentially out for repair."
- Checkout is a **single-click operation** (or barcode scan).
- Assets can be checked out to three target types:
  - **Users** (preferred and recommended)
  - **Locations** (for shared/communal equipment like conference room projectors)
  - **Other Assets** (nested — e.g., a video card inside a laptop)
- The data model uses **polymorphic assignment**: `assigned_to` (ID) + `assigned_type` (User, Location, or Asset class).
- Additional tracked fields: `last_checkout`, `expected_checkin`, `location_id`, `checkin_counter`.
- Checkout form includes: target selection, status dropdown (deployable labels only), checkout date, expected checkin date, notes (optionally required), and custom fields.
- Checkin clears assignments, updates location to RTD (Return To Default), increments the checkin counter, and logs everything.

**Key Design Insight:** Snipe-IT strongly discourages checking assets out to locations rather than users, because "a location cannot be held responsible if an asset is broken or goes missing." The accountability chain requires a **person**, not a place.

### ServiceNow HAM (Enterprise)

- Uses a **request-fulfillment** model rather than direct checkout.
- Employees submit a **catalog request** (e.g., "New Laptop"), which goes through approval workflows.
- Once approved, IT allocates an asset from a **stockroom**, changes its state from "In Stock" to "In Use", and assigns it to the user.
- **Transfer Orders** enable moving assets between stockrooms before allocation.
- **Stock Rules** automatically trigger purchase orders or transfer orders when inventory drops below thresholds.
- The lifecycle is: Request > Order > Receive > Deploy > Use > Maintain > Retire.

### Freshservice (SaaS)

- Asset assignment can be manual or **automatic via Discovery** tools (agent-based detection of who is using what).
- **Auto Assignment** feature: when enabled, `Used By` and `Department` fields are updated automatically based on discovery data.
- Offboarding triggers a **reclaim assets ticket** that lists all items linked to the departing employee, with auto-assigned tasks per responsible team (IT disables accounts, Facilities retrieves badges, etc.).

### InvGate Assets

- Uses a **6-step workflow** combining Service Management + Asset Management:
  1. User submits a request form (desired dates, equipment type, comments)
  2. Calendar auto-populated with reservation (prevents conflicts)
  3. IT task assigned to validate and prepare the asset
  4. API call transfers ownership and marks asset as loaned
  5. On return, agent initiates collection
  6. API call restores asset to "ready to loan" and removes assigned owner
- Status designations through lifecycle: "Ready to Loan" > "Loaned" > "Back and Ready to Loan."

### GLPI (Open Source)

- Uses **three separate assignment fields** on assets:
  - **User** — the end-user who has the asset
  - **Technician in Charge** — the IT person responsible for managing/supporting the asset
  - **Group in Charge** — the team responsible
- No explicit "checkout/checkin" operation like Snipe-IT. Assignment is more of a field update.
- Ticket auto-assignment rules can use the Technician in Charge field.

### Lansweeper

- Primarily a **discovery-driven** tool; assets are auto-detected on the network.
- Assignment is done through "User/OU/AD Group Relations" with assignment type (e.g., "Used By").
- Location is tracked separately via AD location, IP range, manual entry, or SNMP data.
- No formal checkout/checkin workflow; it is more of a passive inventory tracker.

---

## 2. Custody Chain / Custody Transfer

### Industry Pattern: Assignment History = Custody Chain

No tool reviewed uses a separate "custody transfer" entity. Instead, **the audit log of checkout/checkin events IS the custody chain**.

| Tool | Custody Mechanism |
|------|------------------|
| **Snipe-IT** | Every checkout/checkin creates an `Actionlog` entry with target, timestamp, user who performed the action, and notes. The asset's History tab shows the complete chain. |
| **ServiceNow** | State/substate transitions + assignment history on the asset record + CMDB audit trail. |
| **Freshservice** | Activity log on asset record; document generation for formal handovers. |
| **InvGate** | Activities tab on asset profile logs every ownership change, document creation, and status update. |
| **GLPI** | Change history (logs) on each asset record. |

**Key Finding:** The market standard is that **the assignment log IS the custody chain**. There is no separate "custody transfer" entity. However, some tools (Freshservice, InvGate) layer **document generation** on top of the assignment event to create a formal handover record.

---

## 3. Digital Signature / Acknowledgment

### Snipe-IT (Most Mature Implementation)

Snipe-IT has the most complete digital signature workflow in the ITAM space:

1. **EULA / Terms of Service**: Configurable per asset category. Displayed to the user during acceptance.
2. **Asset Acceptance Email**: When an asset in a category requiring acceptance is checked out, the user receives an email with a link.
3. **Accept / Decline Flow**: User logs in and either:
   - **Accepts** — with optional on-screen signature (mouse or touch)
   - **Declines** — required to provide a reason note
4. **On-Screen Signature**: Available since v3.6.0. Provides a signature pad (drawn with mouse or finger on touch devices).
5. **Signature Storage**: Files stored in `storage/private_uploads/signatures`.
6. **Signature Review**: Visible in the asset's History tab. Clickable to view enlarged.
7. **Configuration**: Enabled at two levels — Admin > Settings (global) and per asset Category.

### Freshservice

- **E-signature** support in document templates (optional).
- Documents can be **auto-sent** to requesters.
- Signatures reduce manual sharing and signing with approving stakeholders.
- Not as granular as Snipe-IT (no in-app signature pad; relies on document-level e-signatures).

### InvGate Assets

- Uses a **physical signature** model:
  1. Generate delivery document from template
  2. Print the document
  3. Deliver asset + collect physical signature
  4. Scan signed document and upload to Attachments section
- Creates a permanent timestamped record in the Activities tab.
- More traditional/paper-based but with digital tracking.

### ServiceNow / GLPI / Lansweeper

- No built-in asset acceptance signature workflow.
- ServiceNow can achieve this through **custom catalog workflows** with approval steps.
- GLPI has no native signature support.

---

## 4. Location vs. Assignment

This is a **critical architectural distinction** that all mature ITAM tools handle:

### The Two Dimensions

| Dimension | Meaning | Example |
|-----------|---------|---------|
| **Assigned To** (User/Person) | Who is **responsible** for the asset | "Juan Macias" |
| **Location** (Physical Place) | Where the asset **physically is** | "Building A, Floor 3, Room 301" |

### How Tools Handle It

**Snipe-IT:**
- Separate `assigned_to` (polymorphic: User, Location, or Asset) and `location_id` fields.
- When checked out to a **User**, the asset's location can inherit from the user's default location OR be set explicitly.
- When checked out to a **Location**, the `assigned_to` becomes the location (discouraged practice).
- RTD (Return To Default) location is used on checkin to reset the physical location.
- GitHub issue #2196 ("Device location vs user location") highlights this as a recurring design challenge.

**ServiceNow:**
- **Stockroom** = physical warehouse location for inventory.
- **Location** field on CI/Asset = where it is deployed.
- **Assigned To** = the user responsible.
- **Transfer Orders** move assets between stockrooms (location changes without assignment changes).

**GLPI:**
- **Location** field on asset = physical location (hierarchical: Site > Building > Room).
- **User** field = who has it.
- **Technician in Charge** = who supports it.
- These are fully independent fields.

**Freshservice:**
- **Location** = where the asset is.
- **Used By** = who is using it.
- **Department** = organizational unit.
- Auto-populated via Discovery or manual.

**Lansweeper:**
- Multiple location sources: AD location, IP range, manual field, SNMP.
- User assignment via "Used By" relation.
- Supports blueprints/maps for visual asset placement.

### Key Design Principle

**Location and Assignment are always separate concerns.** A laptop can be assigned to "Juan" (who is responsible) but located at "Home Office" or "Building A Desk 42." When Juan returns the laptop, the assignment clears but the location changes to "IT Stockroom." These must be independent fields.

---

## 5. Status Lifecycle

### Snipe-IT Status Model

Snipe-IT uses **Status Labels** with four meta-types:

| Meta-Type | Behavior | Example Labels |
|-----------|----------|----------------|
| **Deployable** | Can be checked out. Becomes "Deployed" when assigned. | "Ready to Deploy", "Available" |
| **Pending** | Cannot be checked out. Auto-checks-in if applied. | "Pending Repair", "Pending Setup", "Pending Approval" |
| **Undeployable** | Cannot be checked out. Auto-checks-in if applied. | "Out for Repair", "Broken", "Lost/Stolen" |
| **Archived** | Cannot be checked out. Auto-checks-in if applied. | "Decommissioned", "E-Waste", "Donated" |

**Key Design:** Status labels are user-customizable. The four meta-types control system behavior (can it be checked out or not?), while the label names are freeform. This gives flexibility while enforcing business rules.

### ServiceNow HAM Status Model (Most Granular)

ServiceNow has **8 states** with **substates**:

| State | Substates | Description |
|-------|-----------|-------------|
| **On Order** | — | Asset has been ordered from vendor |
| **In Stock** | Pending Repair, Pending Install, Pending Disposal | In warehouse/stockroom, available or being prepared |
| **In Transit** | Pending Disposal | Being moved between locations |
| **In Use** | — | Deployed to a user; managed as a CI |
| **Consumed** | — | Consumable item that has been used up |
| **In Maintenance** | — | Under repair or scheduled maintenance |
| **Retired** | Disposed, Donated, Sold | End of life |
| **Missing/Absent** | — | Cannot be located after investigation |

### Freshservice Status Model

Five default states:

| State | Description |
|-------|-------------|
| **In Stock** | Available for deployment |
| **In Use** | Currently assigned to someone |
| **In Transit** | Being moved or ordered from vendor |
| **Missing** | Cannot be located |
| **Retired** | End of life, no longer functional |

Custom states can be added per asset type.

### Composite Best-Practice Lifecycle

Based on all tools reviewed, the **market-standard lifecycle** is:

```
Ordered/Procurement
    |
    v
Received/In Stock (in stockroom, ready for setup)
    |
    v
Pending Setup (being configured/imaged)
    |
    v
Ready to Deploy (configured, waiting for assignment)
    |
    v
Deployed/In Use (assigned to a user) <--+
    |                                    |
    v                                    |
In Maintenance/Repair ---> repaired -----+
    |
    v (cannot be repaired)
Retired/Decommissioned
    |
    v
Disposed / Donated / Sold / E-Waste
```

Side states that can occur at any point:
- **Missing / Lost** (investigation required)
- **Stolen** (involves security incident)
- **In Transit** (being shipped between locations)

---

## 6. Handover Document / Receipt

### InvGate Assets (Best Implementation)

1. Click "Create document" from the asset menu.
2. Choose template: onboarding, replacement, offboarding, etc.
3. Fill required fields: recipient name, department, authorized person, location.
4. Select the asset(s) included in the handover.
5. Preview and click "Create and download" — PDF is generated.
6. PDF is **automatically attached** to the asset's profile (Attachments section).
7. Entry is logged in the **Activities tab** (who created it, when, for what purpose).
8. For physical signatures: print, collect signature, scan, upload back.

### Freshservice

Offers **document generation** with templates:

| Document Type | Purpose |
|---------------|---------|
| **Asset Handover** | Formal record of asset transfer between individuals/departments/locations |
| **Asset Receipt** | Acknowledgment when employee receives a company asset |
| **Acceptable Terms of Use** | Guidelines and responsibilities for asset usage |
| **Software Access Request** | Formal request requiring multi-level approval |

Features:
- Placeholders for dynamic data (asset name, date, employee, serial number, etc.)
- Optional e-signature fields
- "Auto send document to requester" automation
- Integration with Service Catalog fulfillment workflows

### Snipe-IT

- No built-in document/PDF generation.
- The **EULA display + digital signature** during acceptance serves as the acknowledgment record.
- Signatures stored as image files, viewable in History tab.
- Some organizations export/print the acceptance record manually.

### ServiceNow

- No out-of-the-box handover document.
- Can be built using **Document Templates** or **PDF Generation** plugins.
- The approval workflow + assignment notification email serves as the audit trail.

---

## 7. Summary: Market Best Practices Synthesis

### What the Best Tools Do

| Capability | Best-in-Class | Pattern |
|------------|--------------|---------|
| **Checkout/Checkin** | Snipe-IT | Explicit operation that changes assignment + status atomically. Prevents double-booking. |
| **Assignment Targets** | Snipe-IT | Polymorphic: User (primary), Location, Asset. User strongly preferred for accountability. |
| **Custody Chain** | Snipe-IT / ServiceNow | Complete audit log of all assignment changes with timestamp, actor, target, and notes. |
| **Digital Signature** | Snipe-IT | On-screen signature pad (mouse/touch), stored as image, reviewable in History tab. |
| **Acceptance Flow** | Snipe-IT | Email notification > User logs in > Sees EULA > Accepts with signature OR Declines with reason. |
| **Document Generation** | InvGate / Freshservice | Template-based PDF generation attached to asset record, with e-signature support. |
| **Location vs Assignment** | All tools | Separate independent fields. Location = where it is. Assigned To = who is responsible. |
| **Status Lifecycle** | ServiceNow HAM | 8 states + substates. Snipe-IT's 4 meta-types (deployable/pending/undeployable/archived) is simpler but effective. |

### Recommended Model for DeskSupportMonkey

Based on this research, the recommended approach would combine:

1. **Snipe-IT's checkout/checkin model** — explicit operations, not just field updates. An asset is "checked out" to a person, creating an event.
2. **Snipe-IT's polymorphic assignment** — assign to User (primary), Location (shared equipment), or Asset (nested).
3. **Snipe-IT's acceptance workflow** — EULA display + accept/decline + optional digital signature.
4. **InvGate's document generation** — template-based PDF handover documents attached to the asset record.
5. **ServiceNow's status model (simplified)** — a pragmatic subset of states:
   - `ordered` / `in_stock` / `pending_setup` / `ready_to_deploy` / `deployed` / `in_maintenance` / `retired` / `missing` / `disposed`
6. **Separate Location and Assignment** — independent fields that track physical location and responsible person.
7. **Complete audit trail** — every checkout, checkin, status change, and location change logged as an event.

---

## Sources

- [Snipe-IT Product Features](https://snipeitapp.com/product)
- [Snipe-IT Asset Acceptance Documentation](https://snipe-it.readme.io/docs/requiring-acceptance)
- [Snipe-IT Managing Assets](https://snipe-it.readme.io/docs/managing-assets)
- [Snipe-IT Asset Checkout & Checkin - DeepWiki](https://deepwiki.com/grokability/snipe-it/2.5-asset-checkout-and-checkin)
- [Snipe-IT Activity Logging - DeepWiki](https://deepwiki.com/grokability/snipe-it/4.4-activity-logging)
- [Snipe-IT Status Label Issue #15679](https://github.com/grokability/snipe-it/issues/15679)
- [Snipe-IT EULA Signing Issue #12135](https://github.com/grokability/snipe-it/issues/12135)
- [Snipe-IT Signed EULA Storage PR #10737](https://github.com/snipe/snipe-it/pull/10737)
- [Freshservice Asset States](https://support.freshservice.com/support/solutions/articles/164414-understanding-the-different-asset-states)
- [Freshservice IT Employee Document Use Cases](https://support.freshservice.com/support/solutions/articles/50000010533-it-employee-document-use-cases)
- [Freshservice Asset Auto Assignment](https://support.freshservice.com/support/solutions/articles/50000000075-asset-auto-assignment)
- [Freshservice Offboarding Asset Retrieval](https://www.readycloud.com/info/how-freshservice-automates-it-asset-retrieval-during-employee-offboarding)
- [Freshservice Electronic Handover Form Discussion](https://community.freshworks.com/assets-11410/automatic-sending-of-electronic-handover-form-to-users-37525)
- [ServiceNow HAM Overview](https://servicenowguru.com/hardware-asset-management/overview-of-servicenow-hardware-asset-management/)
- [ServiceNow Asset Lifecycle States](https://www.servicenow.com/community/ham-forum/asset-life-cycle/m-p/3391251)
- [ServiceNow HAM Substates](https://www.servicenow.com/community/ham-forum/how-do-we-define-the-following-substates-in-servicenow/td-p/2589782)
- [ServiceNow HAM Chapter 2](https://www.servicenow.com/community/ham-articles/mastering-hardware-asset-management-in-servicenow-chapter-2/ta-p/3351555)
- [ServiceNow Asset Management Guide](https://www.reco.ai/hub/servicenow-asset-management)
- [InvGate Equipment Check-Out System](https://blog.invgate.com/equipment-check-out-system)
- [InvGate Track New Employee Equipment](https://blog.invgate.com/how-to-track-new-employee-equipment)
- [GLPI Asset Management](https://deepwiki.com/glpi-project/glpi/5-asset-management)
- [GLPI Asset Definitions FAQ](https://help.glpi-project.org/faq/glpi/asset-definitions)
- [Lansweeper Asset Location Tracking](https://www.lansweeper.com/product/features/it-network-inventory/asset-location-tracking/)
- [Lansweeper Asset Lifecycle](https://community.lansweeper.com/t5/sites/view-assets-lifecycle-information/ta-p/64600)
- [Atlassian Asset Lifecycle Best Practices](https://www.atlassian.com/itsm/it-asset-management/asset-management-lifecycle)
- [IT Asset Lifecycle Best Practices - AssetCues](https://www.assetcues.com/blog/it-asset-management-lifecycle/)
- [NinjaOne IT Asset Lifecycle Management 2025](https://www.ninjaone.com/blog/it-asset-management-best-practices/)
- [Freshworks Asset Lifecycle Guide](https://www.freshworks.com/it-asset-management/lifecycle/)
