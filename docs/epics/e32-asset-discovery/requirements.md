# Epic E32: Asset Discovery

**Date:** 2026-02-27
**Priority:** Medium
**Status:** Draft
**Bounded Context:** Extends `asset_bc` (discovery is an asset creation pathway, not a separate domain)

## Business Alignment

**Objective:** Enable automatic detection of devices on a customer's network via a lightweight, standalone scanner tool that outputs a CSV file compatible with DSM Control's existing CSV import. No cloud connectivity required from the scanner — the admin uploads the CSV manually through the existing import flow.

**KPI Targets:**
- Scanner runs in < 5 minutes on a /24 subnet (254 hosts)
- Zero dependencies: single binary download, no Python/Java/Node required
- CSV output is 100% compatible with DSM Control's existing import (validated, preview, dedup)
- Detects > 90% of active network devices on a standard office LAN
- Admin can go from download to imported assets in < 15 minutes

**Evidence:**
- NIS2 Article 21(2)(a): "risk analysis and information system security" — requires complete asset inventory
- NIS2 Article 21(2)(d): "supply chain security" — requires knowing what hardware is deployed
- DORA Article 8(1): "identify, classify and adequately document all ICT assets" — explicit asset identification requirement
- ISO 27001 Annex A.5.9: "Inventory of information and other associated assets" — requires maintaining an accurate asset inventory

## Problem Statement

**Current situation:** DSM Control supports manual asset creation, CSV import, and auto-creation from purchase orders. However, administrators have no way to discover what devices are actually on their network. In a 50-person company, the gap between "assets we know about" and "devices actually connected" can be 20-40%. Shadow IT, personal devices, printers, switches, and forgotten hardware go untracked.

| Pain Point | Impact | Regulatory Gap |
|-----------|--------|----------------|
| No network scanning | Unknown devices on the network = unknown risk surface | NIS2 Art. 21(2)(a): can't do risk analysis on assets you don't know exist |
| Manual-only inventory | Time-consuming, error-prone, always outdated | DORA Art. 8(1): ICT asset documentation must be accurate |
| Shadow IT blind spot | Employees connect personal/unauthorized devices | ISO 27001 A.5.9: inventory must be complete |
| No device type detection | Even discovered devices need manual classification | Operational: admin spends hours classifying found devices |
| No scheduled rescanning | Inventory drifts from reality over time | Compliance: periodic reassessment required |

**Who is affected:**
- **Admins:** Need to discover all devices on their network without manual enumeration
- **Technicians:** Need accurate inventory to link incidents to the right assets
- **Auditors:** Need evidence that asset inventory reflects reality (discovery scan reports)

## Existing Foundation

| Component | Status | Source |
|-----------|--------|--------|
| Asset CRUD with all fields | Done | E2 |
| CSV bulk import with validation, preview, dedup by serial | Done | E2 |
| Custom fields (extra CSV columns auto-captured) | Done | E30 |
| Configurable asset types per company | Done | E47 |
| Asset locations (where to place discovered assets) | Done | E45 |
| Asset event sourcing (audit trail) | Done | E2 |
| Audit trail & compliance evidence | Done | E29 |

**Key insight:** The CSV import flow already handles everything we need on the platform side — validation, preview, deduplication, custom fields, event logging. E32 is primarily about building the **scanner tool** that generates the CSV.

---

## Solution Overview

### Architecture: Standalone Scanner + Existing CSV Import

```
┌─────────────────────────────────────────────────────┐
│                Customer's Network                    │
│                                                      │
│  Admin downloads dsm-scanner.exe (or .dmg / linux)  │
│                     │                                │
│                     ▼                                │
│  ┌─────────────────────────────────┐                │
│  │        DSM Scanner CLI          │                │
│  │                                 │                │
│  │  1. Detect local subnet         │                │
│  │  2. ARP scan (L2 discovery)     │                │
│  │  3. Ping sweep (L3 fallback)    │                │
│  │  4. DNS reverse lookup          │                │
│  │  5. MAC → vendor (OUI database) │                │
│  │  6. Port scan (top ports)       │                │
│  │  7. Device type heuristics      │                │
│  │  8. SNMP query (if enabled)     │                │
│  │                                 │                │
│  │  Output: discovery-YYYY-MM-DD.csv│                │
│  └─────────────────────────────────┘                │
│                     │                                │
│                     ▼                                │
│            CSV file on disk                          │
└─────────────────────────────────────────────────────┘
                      │
            Admin uploads CSV
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              DSM Control (Cloud)                     │
│                                                      │
│  Existing: POST /api/v1/assets/import               │
│  → Validation, preview, dedup by serial_number      │
│  → Custom fields: hostname, ip, mac, os             │
│  → Admin reviews and confirms import                │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Why This Architecture

1. **Zero cloud dependency from scanner** — Scanner runs fully offline. No API keys, no tokens, no internet required. Privacy-friendly.
2. **No new backend code needed (Phase 1)** — CSV import already exists with validation, preview, dedup, custom fields.
3. **Admin stays in control** — They review discovered devices before importing. No surprise assets appearing.
4. **Open source scanner** — Separate repo, AGPL licensed, builds trust with the community.
5. **Cross-platform** — One Go codebase compiles to Windows .exe, macOS binary, Linux binary.

---

## Scanner Tool: DSM Scanner

### Technology: Go

**Why Go over Python/C#/Rust:**
- Compiles to a **single static binary** — no runtime, no dependencies, no installer
- **Cross-platform** from one codebase: `GOOS=windows`, `GOOS=darwin`, `GOOS=linux`
- Small binary size (~5-10MB)
- Excellent networking libraries: `gopacket` (ARP/packet capture), `gosnmp`, `gopsutil`
- Large ecosystem of infrastructure tools written in Go (Docker, Terraform, Prometheus)
- Good concurrency model for parallel port scanning

### Repository

Separate repo: `desksupportmonkey/dsm-scanner` (or monorepo subfolder `tools/scanner/`)

### Scanner Features

#### Phase 1: Basic Discovery (MVP)

```bash
# Simplest usage — auto-detect subnet, scan, output CSV
dsm-scanner

# Specify subnet
dsm-scanner --subnet 192.168.1.0/24

# Specify output file
dsm-scanner --output my-network.csv

# Verbose mode
dsm-scanner -v
```

**Discovery methods (Phase 1):**

| Method | What it finds | Requires |
|--------|--------------|----------|
| ARP scan | All devices on L2 segment (most reliable) | Same subnet, may need admin/root |
| Ping sweep (ICMP) | Devices that respond to ping | Some devices block ICMP |
| DNS reverse lookup | Hostname from IP | DNS server on network |
| MAC OUI lookup | Manufacturer from MAC address | Embedded OUI database (~3MB) |
| TCP port probe | Top 20 ports → device type heuristics | Network access |

**Device type heuristics (Phase 1):**

| Signal | Inferred type |
|--------|--------------|
| Port 80/443 + MAC=HP/Brother/Canon | printer |
| Port 22 + MAC=Apple | laptop (macOS) |
| Port 3389 (RDP) | laptop/desktop (Windows) |
| Port 631 (IPP) | printer |
| Port 62078 (Apple) | phone (iPhone) |
| Port 5353 (mDNS) | Various — resolve via mDNS name |
| MAC vendor = Cisco/Ubiquiti/Netgear | network_device |
| MAC vendor = Dell/Lenovo/HP + RDP | laptop |
| No identifiable ports | unknown |

**CSV output format:**

```csv
type,brand,model,serial_number,hostname,ip_address,mac_address,os,open_ports,discovery_date
laptop,Dell,,UNKNOWN-AA-BB-CC-DD-EE-01,PC-JUAN,192.168.1.45,AA:BB:CC:DD:EE:01,Windows (inferred),3389;445;139,2026-02-27
printer,HP,,UNKNOWN-11-22-33-44-55-01,hp-laserjet,192.168.1.100,11:22:33:44:55:01,,80;443;631;9100,2026-02-27
phone,Apple,,UNKNOWN-66-77-88-99-AA-01,,192.168.1.67,66:77:88:99:AA:01,iOS (inferred),62078,2026-02-27
unknown,Ubiquiti,,UNKNOWN-FF-EE-DD-CC-BB-01,ubnt,192.168.1.1,FF:EE:DD:CC:BB:01,,22;80;443,2026-02-27
```

**Serial number handling:**
- Without SNMP/WMI credentials, real serial numbers are NOT available
- Scanner generates a placeholder: `UNKNOWN-{MAC-ADDRESS}` (MAC is unique per device)
- On re-scan, same MAC → same placeholder → DSM import deduplicates correctly
- Admin can edit serial numbers after import in DSM UI

#### Phase 2: Enhanced Discovery

- **SNMP v2c/v3 support** (`--snmp-community public`): get real serial number, model, OS version, uptime
- **WMI support** (`--wmi-user admin --wmi-pass ***`): Windows-specific deep data (serial, RAM, CPU, disk, installed software)
- **SSH support** (`--ssh-key ~/.ssh/id_rsa`): Linux/macOS system info via `dmidecode`, `lshw`
- **mDNS/Bonjour discovery**: Apple devices, printers, Chromecasts
- **Subnet auto-detection across multiple interfaces**: scan all local subnets
- **Diff mode** (`--diff previous-scan.csv`): show new/removed/changed devices since last scan
- **JSON output** (`--format json`): for programmatic consumption
- **Exclude list** (`--exclude 192.168.1.1,192.168.1.2`): skip known infrastructure

#### Phase 3: Scheduled & Connected

- **Scheduled mode** (`dsm-scanner --schedule "0 2 * * *"`): runs as a background service, scans nightly
- **Direct API upload** (`--api-url https://app.dsmcontrol.com --token XXXX`): skip CSV, push directly to DSM
- **Delta sync**: only send new/changed devices to API
- **Agent mode**: lightweight daemon that monitors ARP table continuously, reports new devices in real-time
- **Scan history**: local SQLite database of past scans for trend analysis

#### Phase 4: Endpoint Data Import (osquery / Fleet)

Instead of building a custom per-device agent, DSM integrates with **osquery** (Meta, open source) and **Fleet** (open source osquery manager) — tools that already run on every endpoint and expose system data as SQL-queryable tables.

**Why osquery, not a custom agent:**
- osquery has thousands of contributors, runs on Windows/macOS/Linux, is battle-tested at Facebook/Meta scale
- Building a custom agent would be reinventing the wheel against 10+ years of open source development
- osquery already collects exactly what we need: OS version, installed software, pending patches, hardware serial, disk encryption status
- Fleet adds central management: schedule queries across all endpoints, collect results, alert on changes

**What osquery exposes (relevant tables):**

| osquery table | Data | DSM use |
|---------------|------|---------|
| `system_info` | Hostname, hardware vendor, model, serial number, CPU, RAM | Asset fields: brand, model, serial_number |
| `os_version` | OS name, version, build, platform | Custom field: os, os_version |
| `patches` (Windows) | Installed KB updates, missing patches | Custom field: pending_patches_count |
| `disk_encryption` | FileVault (Mac) / BitLocker (Win) status | Compliance evidence (ISO 27001 A.8.24) |
| `interface_addresses` | IP addresses, MAC addresses per interface | Custom fields: ip_address, mac_address |
| `programs` (Win) / `apps` (Mac) | Installed software with versions | Future: software license management (E21) |
| `uptime` | System uptime, last reboot | Maintenance: detect stale machines |
| `usb_devices` | Connected USB devices | Security: unauthorized device detection |

**Integration architecture:**

```
Endpoints (customer network)              DSM Control (cloud)
┌───────────────────────┐
│ osquery agent          │                ┌─────────────────────────┐
│ (installed on each PC) │                │                         │
│                        │                │  GET /api/fleet/hosts    │
│ Reports to:            │                │  → Fetch all hosts       │
│         │              │                │  → Map to asset fields   │
│         ▼              │                │  → Upsert by serial_no   │
│ ┌─────────────────┐   │                │  → Update custom fields  │
│ │  Fleet server    │───── REST API ──▶ │  → Flag pending patches  │
│ │  (on-prem or     │   │                │  → Store compliance data │
│ │   Fleet Cloud)   │   │                │                         │
│ └─────────────────┘   │                └─────────────────────────┘
└───────────────────────┘
```

**Fleet API integration (DSM backend):**

```python
# Celery scheduled task — runs daily
# Pulls host data from Fleet API, upserts assets in DSM

GET https://fleet.customer.com/api/v1/fleet/hosts
→ Returns: hostname, hardware_serial, os_version, platform,
   primary_ip, primary_mac, disk_encryption_enabled,
   software (list), policies (pass/fail)

For each host:
  1. Find asset by serial_number = hardware_serial
  2. If exists → update custom fields (ip, os, patches)
  3. If new → create asset with type inferred from platform
  4. Flag: pending_patches > 0 → create notification
```

**DSM platform changes for Phase 4:**

- **New integration settings page**: Admin configures Fleet server URL + API token (or Fleet Cloud credentials)
- **Celery task** `core/tasks/fleet_sync.py`: scheduled daily, pulls Fleet API, upserts assets
- **Sync status dashboard widget**: "Last Fleet sync: 2h ago — 52 hosts, 3 with pending patches"
- **Pending patches alert**: Dashboard widget showing assets with outstanding OS/software updates
- **Disk encryption compliance**: Auto-link BitLocker/FileVault status to ISO 27001 A.8.24 control evidence
- **Sync history**: Log each sync run (timestamp, hosts synced, new/updated/unchanged counts)

**What the admin gets without building anything custom:**

| Data point | Source | DSM value |
|-----------|--------|-----------|
| Real serial numbers for all PCs | osquery `system_info` | Accurate asset inventory, dedup with network scan |
| OS version on every device | osquery `os_version` | Vulnerability matching, compliance evidence |
| Pending Windows/macOS updates | osquery `patches` | Dashboard alert: "12 devices have pending security patches" |
| Disk encryption status | osquery `disk_encryption` | Auto-evidence for ISO 27001 A.8.24 and NIS2 Art.21(2)(d) |
| Installed software list | osquery `programs`/`apps` | Foundation for software license management (E21) |
| Hardware specs (RAM, CPU, disk) | osquery `system_info` | Asset detail enrichment |

**Alternative: Microsoft Intune / WSUS integration (future):**
For companies already using Microsoft 365 Business Premium, an Intune connector via Microsoft Graph API would provide similar data without deploying osquery. This is a separate integration but follows the same pattern (scheduled pull → asset upsert → custom field update). Documented here for roadmap awareness but not in scope for E32.

---

## DSM Platform Changes

### Phase 1: No Changes Required

The existing CSV import handles everything:
- `type`, `brand`, `model`, `serial_number` → standard asset fields
- `hostname`, `ip_address`, `mac_address`, `os`, `open_ports`, `discovery_date` → auto-captured as custom fields
- Deduplication by `serial_number` (the MAC-based placeholder ensures consistency across scans)
- Preview UI lets admin review and edit before confirming import

### Phase 2: Discovery-Aware Import (Optional Enhancement)

- **Import source tag**: Mark imported assets with `source: network_discovery` in event data
- **Discovery dashboard widget**: "Last scan: 47 devices found, 12 new, 2 removed since last scan"
- **Discovery custom field definitions**: Pre-create `hostname`, `ip_address`, `mac_address`, `os` as system custom fields so they render properly in asset detail
- **Merge logic**: When reimporting, match by MAC address (not just serial) to update IP/hostname changes

### Phase 3: Full Integration

- **Discovery API endpoint**: `POST /api/v1/discovery/upload` — accepts scanner JSON, processes in background (Celery)
- **Discovery scan history**: Store scan results with timestamps, device counts, diff from previous
- **New/removed device alerts**: Notify admin when new device appears or known device disappears
- **Compliance evidence**: Auto-link discovery scans to NIS2 Art.21(2)(a) and DORA Art.8(1) controls

### Phase 4: Endpoint Data via osquery/Fleet

- **Integration settings page**: Admin configures Fleet server URL + API token
- **Celery task** `core/tasks/fleet_sync.py`: scheduled daily pull from Fleet API → asset upsert
- **Sync dashboard widget**: "Last sync: 2h ago — 52 hosts, 3 with pending patches"
- **Pending patches alert**: Dashboard notification for assets with outstanding updates
- **Disk encryption status**: Auto-link BitLocker/FileVault status to ISO 27001 A.8.24 evidence
- **Sync history log**: Each run recorded with new/updated/unchanged counts
- **Software inventory enrichment**: Store installed software list per asset (foundation for E21)

---

## Competitive Positioning

| Feature | DSM Scanner | Lansweeper | InvGate | Snipe-IT |
|---------|------------|------------|---------|----------|
| Single binary, zero deps | ✅ | ❌ (installer) | ❌ (agent install) | N/A |
| Works offline (no cloud) | ✅ | ❌ | ❌ | N/A |
| Open source | ✅ | ❌ | ❌ | N/A |
| Cross-platform | ✅ Win/Mac/Linux | ✅ | ✅ | N/A |
| ARP + ping discovery | ✅ | ✅ | ✅ | N/A |
| SNMP deep scan | Phase 2 | ✅ | ✅ | N/A |
| WMI Windows scan | Phase 2 | ✅ | ✅ | N/A |
| Auto-discovery of OT | ❌ | ✅ | ❌ | N/A |
| Direct API integration | Phase 3 | ✅ | ✅ | N/A |
| Linked to service desk | ✅ (via DSM) | ❌ | ✅ | ❌ |
| Linked to compliance | ✅ (via DSM) | ✅ | ❌ | ❌ |
| osquery/Fleet integration | Phase 4 | ❌ | ❌ | N/A |
| Pending patches dashboard | Phase 4 | ✅ | ✅ | N/A |
| Disk encryption compliance | Phase 4 | ✅ | ❌ | N/A |
| SMB pricing | Free (open source) | $2,400+/yr | $105+/mo | N/A |

**Our pitch:** "Download. Scan. Import. 5 minutes from zero to full network inventory — free, offline, open source. Then link every discovered device to incidents, SLAs, and compliance in DSM Control."

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ARP scan requires admin/root privileges | High | Medium | Document clearly. Provide fallback to ping-only mode (no root needed but less accurate) |
| Firewalls block ICMP/ARP | Medium | Medium | Multiple discovery methods (ARP + ping + port probe). Document firewall exceptions |
| MAC-based serial placeholders pollute asset inventory | Medium | Low | Clear naming convention (`UNKNOWN-XX-XX-...`). Admin can bulk-edit after import |
| Go binary flagged by antivirus | Medium | High | Sign binaries with code signing certificate. Publish checksums. Document false positive handling |
| Customer expects real-time sync, not CSV | Low | Medium | Phase 3 roadmap. Phase 1 messaging: "CSV-first for maximum control and privacy" |
| SNMP/WMI credential management in scanner | Medium | High | Phase 2. Never store credentials — pass via CLI flags or env vars. Document security best practices |

---

## Success Criteria

### Phase 1 (MVP) — Scanner CLI + CSV

- [ ] Go binary compiles for Windows amd64, macOS arm64, Linux amd64
- [ ] Single binary < 15MB (including embedded OUI database)
- [ ] Auto-detects local subnet without configuration
- [ ] ARP scan finds > 90% of devices on a /24 subnet
- [ ] Ping sweep fallback for non-root execution
- [ ] DNS reverse lookup resolves hostnames
- [ ] MAC OUI lookup identifies manufacturer (brand column)
- [ ] Port-based heuristics classify device type with > 70% accuracy
- [ ] CSV output compatible with DSM Control import (validated with real import)
- [ ] MAC-based placeholder serial numbers enable deduplication across scans
- [ ] Scan completes in < 60 seconds for /24 subnet
- [ ] Open source repo with README, build instructions, release binaries
- [ ] Downloads page on dsmcontrol.com with platform-specific links

### Phase 2 — Enhanced Discovery

- [ ] SNMP v2c/v3 queries return real serial numbers, model, OS
- [ ] WMI queries return Windows device details (serial, RAM, CPU, disk)
- [ ] SSH queries return Linux/macOS device details
- [ ] Diff mode shows new/removed/changed devices
- [ ] Multiple subnet scanning
- [ ] Exclude list support

### Phase 3 — Full Integration

- [ ] Direct API upload from scanner to DSM Control
- [ ] Discovery scan history in DSM dashboard
- [ ] New device / removed device notifications
- [ ] Auto-link scans to compliance controls
- [ ] Scheduled scanning mode (daemon/service)

### Phase 4 — Endpoint Data (osquery/Fleet)

- [ ] Fleet API integration settings page (URL + API token)
- [ ] Celery task `fleet_sync` pulls hosts from Fleet API daily
- [ ] Map Fleet host data to asset fields (serial, brand, model, os, ip, mac)
- [ ] Upsert logic: match by serial_number, create new or update existing
- [ ] Custom fields populated: os_version, pending_patches_count, disk_encryption, ram, cpu
- [ ] Dashboard widget: sync status + pending patches count
- [ ] Notification: alert admin when assets have pending security patches
- [ ] Disk encryption status linked to ISO 27001 A.8.24 compliance evidence
- [ ] Sync history log with per-run statistics
- [ ] Documentation: how to deploy osquery + Fleet for DSM Control users
