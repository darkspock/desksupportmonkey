# Design: F2 - SLA Breach Alerts

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## SLA Thresholds

Hardcoded Python constants:

```python
SLA_THRESHOLDS_HOURS = {
    "urgent": 4,
    "high": 24,
    "medium": 72,
    "low": 168,
}
```

---

## Repository Method (Added to RequestRepository)

### find_sla_breaches(company_id) -> list[dict]

Query all open requests (status in submitted, in_review, in_progress) and calculate hours_open:

```sql
SELECT id, title, type, priority, status, assigned_to, created_at,
       EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as hours_open
FROM service_requests
WHERE company_id = ?
  AND status IN ('submitted', 'in_review', 'in_progress')
ORDER BY hours_open DESC
```

The SLA threshold comparison and breached boolean are computed in Python after the query (simpler than encoding threshold logic in SQL with CASE statements):

```python
for request in results:
    threshold = SLA_THRESHOLDS_HOURS[request["priority"]]
    request["sla_threshold_hours"] = threshold
    request["breached"] = request["hours_open"] > threshold
```

---

## Schema (Already in dashboard/schemas.py from F0)

```python
class SlaAlertItem(BaseModel):
    id: str
    title: str
    type: str
    priority: str
    status: str
    assigned_to: str | None
    created_at: datetime
    hours_open: float
    sla_threshold_hours: int
    breached: bool
```

---

## Router Endpoint (Added to dashboard/routers.py)

`GET /alerts/sla`
- Call find_sla_breaches(company_id)
- Enrich each result with sla_threshold_hours and breached flag
- Return list[SlaAlertItem]

---

## Design Decisions

### 1. Threshold Comparison in Python
Rather than encoding CASE WHEN logic in SQL, the query returns all open requests with hours_open, and Python code adds the threshold and breached flag. This is simpler and more maintainable. Performance is fine since open requests per company are bounded.

### 2. All Open Requests Returned (Not Just Breached)
The endpoint returns ALL open requests with their SLA status. The `breached` boolean lets the frontend filter/highlight as needed. This gives admins visibility into requests approaching their SLA threshold too.

### 3. hours_open Is Real-Time
`hours_open` is calculated at query time using `NOW() - created_at`. It reflects the exact current state, not a cached value.
