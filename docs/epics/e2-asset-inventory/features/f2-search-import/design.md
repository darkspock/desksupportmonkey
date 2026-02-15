# Design: F2 - Search, Filters + CSV Import

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F2 extends the existing asset list query with search/filter/sort, and adds a CSV import command.

```
NEW FILES:
src/asset_bc/asset/application/commands/import_assets.py

MODIFIED FILES:
src/asset_bc/asset/domain/repository.py           # Extended find_all signature
src/asset_bc/asset/infrastructure/repository.py    # Implement filters/search/sort
src/asset_bc/asset/application/queries/list_assets.py  # Extended query fields
adapters/http/api/assets/routers.py                # Add query params + import endpoint
adapters/http/api/assets/schemas.py                # Add import response schema
```

---

## Extended List Query

### AssetRepositoryInterface.find_all (extended)

```python
def find_all(
    self, company_id: str, page: int, page_size: int,
    search: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    department_id: Optional[str] = None,
    assigned_to: Optional[str] = None,  # "none" for unassigned
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Asset], int]: ...
```

### SQL Implementation
- search: `WHERE (serial_number ILIKE %s OR brand ILIKE %s OR model ILIKE %s)`
- type filter: `WHERE type = %s`
- status filter: `WHERE status = %s`
- department_id filter: `WHERE department_id = %s`
- assigned_to = "none": `WHERE assigned_to IS NULL`
- assigned_to = user_id: `WHERE assigned_to = %s`
- sort: `ORDER BY {sort_by} {sort_order}` (validated against allowed columns)

---

## CSV Import

### ImportAssetsCommand + Handler

```python
@dataclass
class ImportAssetsCommand:
    company_id: str
    performed_by: str
    csv_content: str  # raw CSV string

@dataclass
class ImportResult:
    total: int
    successful: int
    failed: list[ImportError]  # [{row, error}]
```

### Import Flow
1. Parse CSV with `csv.DictReader`
2. Validate header columns
3. For each row:
   a. Validate required fields
   b. Validate type enum
   c. Validate dates if present
   d. Check serial_number unique (DB + already-seen in this import)
   e. If valid: create Asset + AssetEvent, add to batch
   f. If invalid: add to failures list
4. Flush batch
5. Return ImportResult

### Error Handling
- Invalid CSV structure -> raise error
- Per-row errors collected, don't stop processing
- Entire import in one transaction (all-valid rows committed, or rollback on DB error)

---

## HTTP Layer

### Extended List Endpoint
```
GET /api/v1/assets?search=dell&type=laptop&status=in_stock&sort_by=purchase_date&sort_order=asc
```

### Import Endpoint
```
POST /api/v1/assets/import
Content-Type: multipart/form-data
Body: file=@assets.csv
```

### Import Response Schema
```python
class ImportRowError(BaseModel):
    row: int
    error: str

class ImportResponse(BaseModel):
    total: int
    successful: int
    failed: list[ImportRowError]
```

---

## Decisions

1. **Sort column validation**: Only allow sorting by known columns (created_at, purchase_date, warranty_expiration). Default: created_at desc.
2. **CSV parsing**: Use stdlib `csv.DictReader`. No external dependency needed.
3. **File size limit**: 1MB enforced at FastAPI level via `UploadFile`.
4. **Import atomicity**: Valid rows are committed together. If the DB flush fails, entire import rolls back. This is simpler than partial commits.
