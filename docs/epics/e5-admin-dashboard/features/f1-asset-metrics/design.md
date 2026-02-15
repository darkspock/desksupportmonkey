# Design: F1 - Asset Metrics + Alert Endpoints

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Repository Methods (Added to AssetRepository)

### count_by_status(company_id) -> dict[str, int]
```sql
SELECT status, COUNT(*) FROM assets WHERE company_id = ? GROUP BY status
```
Returns dict with all 4 status values, defaulting to 0 for missing.

### count_by_type(company_id) -> dict[str, int]
```sql
SELECT type, COUNT(*) FROM assets WHERE company_id = ? GROUP BY type
```
Returns dict with all 7 type values, defaulting to 0 for missing.

### find_expiring_warranties(company_id, days) -> list[dict]
```sql
SELECT id, brand, model, serial_number, warranty_expiration, assigned_to,
       (warranty_expiration - CURRENT_DATE) as days_remaining
FROM assets
WHERE company_id = ?
  AND status != 'decommissioned'
  AND warranty_expiration IS NOT NULL
  AND warranty_expiration <= CURRENT_DATE + interval 'N days'
  AND warranty_expiration >= CURRENT_DATE
ORDER BY warranty_expiration ASC
```
Only returns assets whose warranty hasn't already expired (>= CURRENT_DATE).

### find_aging_assets(company_id, years) -> list[dict]
```sql
SELECT id, brand, model, serial_number, purchase_date,
       EXTRACT(YEAR FROM age(CURRENT_DATE, purchase_date)) as age_years,
       assigned_to
FROM assets
WHERE company_id = ?
  AND status != 'decommissioned'
  AND purchase_date IS NOT NULL
  AND purchase_date <= CURRENT_DATE - interval 'N years'
ORDER BY purchase_date ASC
```

---

## Schemas (Already in dashboard/schemas.py from F0)

### AssetSummaryResponse
```python
class AssetStatusCounts(BaseModel):
    in_stock: int
    assigned: int
    in_repair: int
    decommissioned: int

class AssetTypeCounts(BaseModel):
    laptop: int
    monitor: int
    keyboard: int
    mouse: int
    headset: int
    docking_station: int
    other: int

class AssetSummaryResponse(BaseModel):
    by_status: AssetStatusCounts
    by_type: AssetTypeCounts
    total: int
```

### WarrantyAlertItem / AgingAlertItem
```python
class WarrantyAlertItem(BaseModel):
    id: str
    brand: str
    model: str
    serial_number: str
    warranty_expiration: date
    assigned_to: str | None
    days_remaining: int

class AgingAlertItem(BaseModel):
    id: str
    brand: str
    model: str
    serial_number: str
    purchase_date: date
    age_years: float
    assigned_to: str | None
```

---

## Router Endpoints (Added to dashboard/routers.py)

- `GET /assets/summary` — calls count_by_status + count_by_type, computes total
- `GET /alerts/warranty?days=30` — calls find_expiring_warranties, returns list
- `GET /alerts/aging?years=3` — calls find_aging_assets, returns list

All admin+ only via require_role dependency.
