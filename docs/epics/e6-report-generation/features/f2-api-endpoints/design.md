# Design: F2 - Notification + Download Integration

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-16

---

## Download Endpoint

### Router Addition
```python
@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
):
    repo = ReportRepository(db)
    report = repo.find_by_id(report_id, current_user.company_id)
    if not report:
        raise HTTPException(404, "Report not found")
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(409, f"Report is {report.status.value}")

    storage = S3StorageService()
    url = storage.get_signed_url(report.storage_key, settings.s3.S3_SIGNED_URL_EXPIRY)
    return {"data": {"download_url": url}}
```

---

## Report Ready Notification

### Why Direct DB Insert (Not EventBus)

The EventBus and ConnectionManager are in-process singletons in the FastAPI web worker. The Celery worker is a separate process — it cannot access the same EventBus or WebSocket connections. Therefore, the Celery task creates the notification record directly using `NotificationRepository`.

The user will see the notification on their next request to `GET /api/v1/my/notifications`. Real-time push for report-ready events can be added later via Redis pub/sub.

### Implementation in Celery Task

After successful report generation (status: completed), add:
```python
from src.notification_bc.notification.domain.entities import Notification
from src.notification_bc.notification.infrastructure.repository import NotificationRepository

notif = Notification.create(
    user_id=report.requested_by,
    company_id=report.company_id,
    event_type=EventType.REPORT_READY,
    title="Report ready",
    body=f"{report.type.value.replace('_', ' ').title()} report is ready for download",
    data={"report_id": report.id},
)
notif_repo = NotificationRepository(session)
notif_repo.save(notif)
```

### EventType Addition

Add to `src/notification_bc/notification/domain/enums.py`:
```python
REPORT_READY = "report.ready"
```

### TargetResolver Addition

Add to `src/notification_bc/notification/application/services/target_resolver.py`:
```python
def _resolve_report_ready(self, payload: dict) -> list[str]:
    return [payload.get("requested_by")] if payload.get("requested_by") else []
```

This is for future use when the EventBus can reach across processes. For now, the Celery task creates the notification directly.

---

## Response Schema

```python
class DownloadResponse(BaseModel):
    download_url: str
```
