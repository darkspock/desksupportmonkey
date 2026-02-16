# Tasks: F13 - Dashboard: Missing Alerts & Trend

**Feature:** Dashboard Alerts & Request Trend Chart
**Date:** 2026-02-16

---

## Summary

The dashboard is missing 3 backend endpoints that are already implemented:
- `GET /dashboard/alerts/warranty` — assets with warranty expiring soon
- `GET /dashboard/alerts/aging` — assets older than threshold
- `GET /dashboard/requests/trend` — request volume over time

---

## Phase 1: Frontend

### T1.1: Add warranty expiration alerts section
- **File:** `web/app/src/pages/admin/DashboardPage.tsx`
- New card/section: "Warranty Expiring Soon"
- Fetch `GET /dashboard/alerts/warranty?days=30`
- Show table: brand, model, serial_number, warranty_expiration, days_remaining, assigned_to

### T1.2: Add aging asset alerts section
- **File:** `web/app/src/pages/admin/DashboardPage.tsx`
- New card/section: "Aging Assets"
- Fetch `GET /dashboard/alerts/aging?years=3`
- Show table: brand, model, serial_number, purchase_date, age_years, assigned_to

### T1.3: Add request trend chart
- **File:** `web/app/src/pages/admin/DashboardPage.tsx`
- New card/section: "Request Trend"
- Fetch `GET /dashboard/requests/trend?bucket=week`
- Display as line/bar chart (use recharts or similar)
- Show total requests per period with breakdown by type
