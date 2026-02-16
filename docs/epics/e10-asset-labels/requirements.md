# Requirements: E10 - Asset QR Codes & Barcodes

**Epic:** E10
**Date:** 2026-02-16
**Priority:** Medium
**Depends on:** E2 (Asset Inventory), E7 (Frontend)

---

## Problem Statement

IT teams that manage physical equipment need a way to identify and locate assets quickly. Currently, technicians must manually search by serial number or browse the asset inventory to find a specific device. There is no physical label that can be scanned to instantly access asset details.

## Goals

1. Generate a **QR code** for each asset that links directly to its detail page in the application.
2. Generate a **barcode** (Code 128) encoding the asset's unique ID for physical identification.
3. Provide a **print** function so labels can be printed and attached to physical equipment.
4. If a user scans the QR code while **not authenticated**, redirect to login and then back to the asset page.
5. If a user scans the QR code while **authenticated**, go directly to the asset detail page.

## User Stories

### US-1: View asset label
**As a** technician or admin,
**I want to** see a QR code and barcode on the asset detail page,
**So that** I can identify the asset and scan it later.

**Acceptance Criteria:**
- [ ] QR code is visible on the asset detail page
- [ ] QR code encodes the full URL to the asset detail page (`{origin}/assets/{id}`)
- [ ] Barcode is visible on the asset detail page
- [ ] Barcode uses Code 128 format encoding the asset ID (ULID)
- [ ] Both codes display below the asset info card

### US-2: Print asset label
**As a** technician or admin,
**I want to** print the QR code and barcode for an asset,
**So that** I can physically attach the label to the equipment.

**Acceptance Criteria:**
- [ ] A "Print" button is available next to the label section
- [ ] Clicking Print opens a print-optimized view with QR code, barcode, brand, model, and serial number
- [ ] The print dialog is triggered automatically
- [ ] The printed label is clean and suitable for physical attachment

### US-3: Scan QR code to access asset
**As a** user scanning a QR code,
**I want to** be taken to the asset detail page,
**So that** I can quickly access the asset information.

**Acceptance Criteria:**
- [ ] QR code URL navigates to the asset detail page
- [ ] If not authenticated, the user is redirected to login first (existing auth return route feature handles this)
- [ ] After login, the user lands on the correct asset page

## Technical Constraints

- **Libraries:** `qrcode.react` for QR generation, `jsbarcode` for barcode generation
- **Barcode format:** Code 128 (ASCII-compatible, supports alphanumeric ULID values)
- **QR error correction:** Level M (15% recovery)
- **No backend changes required** — this is a purely frontend feature
- **i18n:** All labels must be translatable (English and Spanish)

## Out of Scope

- Bulk label printing (print multiple assets at once)
- Custom label templates or sizing
- NFC tags or RFID integration
- Barcode scanning from within the application
