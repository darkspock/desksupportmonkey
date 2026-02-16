# Slicing: E10 - Asset QR Codes & Barcodes

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-16

---

## Features

| # | Feature | Description | Depends | Status |
|---|---------|-------------|---------|--------|
| F0 | QR & Barcode Labels | Generate QR code (asset URL) and barcode (asset ID) on asset detail page with print functionality | - | Done |

## Dependency Graph

```
F0 (QR & barcode labels) — no dependencies, standalone feature
```

## Notes

This is a single-feature epic. The entire scope fits in one feature because:
- No backend changes needed (pure frontend)
- QR and barcode are tightly coupled (same component, same print action)
- The existing auth return route (E9-F23) already handles the unauthenticated QR scan → login → redirect flow
