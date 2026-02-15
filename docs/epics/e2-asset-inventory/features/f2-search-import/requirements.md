# Requirements: F2 - Search, Filters + CSV Import

**Epic:** [E2 - Asset Inventory](../../requirements.md)
**Date:** 2026-02-15

---

## Overview

Enhance the asset list endpoint with advanced search, filtering, and sorting. Add CSV bulk import for onboarding existing inventory.

---

## Requirements

### R1: Asset Search
- Search by serial_number, brand, model (partial match, case-insensitive)
- Single `search` parameter searches across all three fields (OR)

### R2: Asset Filters
- Filter by: type, status, department_id, assigned_to
- `assigned_to=none` filters unassigned assets
- Multiple filters combine with AND

### R3: Asset Sorting
- Sort by: created_at, purchase_date, warranty_expiration
- Sort order: asc or desc (default: created_at desc)

### R4: CSV Bulk Import
- POST /api/v1/assets/import accepts multipart file upload
- CSV columns: type, brand, model, serial_number, purchase_date, warranty_expiration, notes
- Each row validated independently
- Returns summary: total, successful, failed (with row number and error)
- Duplicate serial numbers reported in failures, don't block other rows
- Each successfully imported asset gets a `created` event
- Max file size: 1MB
- Only technician+ role

### R5: Import Validation Rules
- type must be valid AssetType value
- brand, model, serial_number are required non-empty
- purchase_date and warranty_expiration must be valid ISO dates if provided
- serial_number must be unique within company (check both existing DB and within CSV)
