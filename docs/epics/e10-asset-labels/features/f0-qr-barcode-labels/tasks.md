# Tasks: F0 - QR & Barcode Labels

**Feature:** QR & Barcode Labels
**Epic:** E10 - Asset QR Codes & Barcodes
**Date:** 2026-02-16

---

## Summary

Add a QR code and barcode section to the asset detail page. The QR code encodes the full URL to the asset (enabling scan-to-access). The barcode uses Code 128 format with the asset ID (ULID). A print button opens a clean print view with both codes plus asset identity info.

---

## Phase 1: Dependencies

### T1.1: Install npm packages
- **Packages:** `qrcode.react`, `jsbarcode`
- `qrcode.react` — React component for QR code SVG generation
- `jsbarcode` — Client-side barcode generator (Code 128)
- [x] Done

---

## Phase 2: Component

### T2.1: Create AssetLabel component
- **File:** `web/app/src/components/AssetLabel.tsx`
- Props: `assetId`, `serialNumber`, `brand`, `model`
- **QR Code:**
  - Uses `QRCodeSVG` from `qrcode.react`
  - Encodes: `${window.location.origin}/assets/${assetId}`
  - Size: 120px, error correction level M
  - Displays shortened URL below QR
- **Barcode:**
  - Uses `JsBarcode` on an SVG ref via `useEffect`
  - Format: CODE128
  - Encodes: asset ID (ULID)
  - Displays value below barcode (built-in `displayValue`)
- **Print button:**
  - Opens new window with `window.open`
  - Writes HTML with QR SVG + barcode SVG + asset header (brand, model, serial)
  - Auto-triggers `window.print()` on load
  - Clean layout suitable for label printing
- [x] Done

### T2.2: Add i18n keys
- **Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- Keys:
  - `page.asset_detail.label_title` — "Asset Label" / "Etiqueta del activo"
  - `page.asset_detail.print_label` — "Print" / "Imprimir"
  - `page.asset_detail.qr_code` — "QR Code" / "Código QR"
  - `page.asset_detail.barcode` — "Barcode" / "Código de barras"
- [x] Done

---

## Phase 3: Integration

### T3.1: Add AssetLabel to AssetDetailPage
- **File:** `web/app/src/pages/technician/AssetDetailPage.tsx`
- Import `AssetLabel` component
- Place between asset info card and status card
- Pass `id`, `asset.serial_number`, `asset.brand`, `asset.model` as props
- [x] Done

---

## Phase 4: Verification

### T4.1: TypeScript type check
- Run `npx tsc --noEmit` — no errors
- [x] Done

### T4.2: Production build
- Run `npm run build` — builds successfully
- [x] Done

### T4.3: Deploy and verify
- Push to production
- Verify QR code renders on asset detail page
- Verify barcode renders with correct asset ID
- Verify print button opens print dialog
- Verify QR URL navigates to asset page
- [ ] Pending
