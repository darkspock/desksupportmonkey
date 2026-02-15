# Solution Design: F2 - Async Infrastructure (Celery + MinIO)

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-15
**Bounded Context:** None (cross-cutting infrastructure)

---

## Summary

Consolidate Celery configuration, verify Redis connection, create a ping test task, set up Celery Beat with a magic link cleanup task, create an S3 storage service wrapping boto3 for MinIO, and auto-create the `dsm-reports` bucket.

---

## Architecture Decision

Infrastructure services (storage, task queue) live in `core/` since they're cross-cutting. No bounded context needed. The storage service uses an interface so it works with both MinIO (dev) and AWS S3 (production) by just changing config.

---

## Existing Code Analysis

| Component | Location | Action |
|---|---|---|
| `core/celery.py` | Celery app with autodiscover | Keep, update task routes |
| `core/celery_app.py` | Duplicate celery config | Delete, consolidate into celery.py |
| `core/config.py` | CelerySettings, S3Settings | Already configured |
| `core/tasks/__init__.py` | Empty | Add tasks here |

---

## Implementation Plan

### 1. Consolidate Celery

**Delete** `core/celery_app.py` (duplicate).

**Update** `core/celery.py`:
- App name: `desksupportmonkey`
- Broker: Redis from config
- Task routes: `core.tasks.*` -> `reports` queue
- Beat schedule: magic link cleanup daily
- Autodiscover: `core.tasks`

### 2. Celery Tasks

**Ping task** - `core/tasks/ping.py`
```python
from core.celery import celery_app

@celery_app.task(name="core.tasks.ping")
def ping():
    return "pong"
```

**Magic link cleanup** - `core/tasks/cleanup.py`
```python
from core.celery import celery_app
from datetime import datetime, timedelta

@celery_app.task(name="core.tasks.cleanup_magic_links")
def cleanup_magic_links(days: int = 7):
    # Direct DB access (infrastructure task, not domain)
    cutoff = datetime.utcnow() - timedelta(days=days)
    # DELETE FROM magic_links WHERE created_at < cutoff
    # Return count of deleted records
```

**Celery Beat schedule** in `core/celery.py`:
```python
beat_schedule = {
    "cleanup-magic-links": {
        "task": "core.tasks.cleanup_magic_links",
        "schedule": 86400.0,  # Daily
        "kwargs": {"days": 7},
    },
}
```

### 3. S3 Storage Service

**Interface** - `core/storage.py`
```python
from abc import ABC, abstractmethod

class StorageServiceInterface(ABC):
    @abstractmethod
    def upload(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> None: ...

    @abstractmethod
    def download(self, bucket: str, key: str) -> bytes: ...

    @abstractmethod
    def get_signed_url(self, bucket: str, key: str, expiry: int = 3600) -> str: ...

    @abstractmethod
    def ensure_bucket(self, bucket: str) -> None: ...
```

**Implementation** - `core/storage.py` (same file, below interface)
```python
import boto3
from core.config import settings

class S3StorageService(StorageServiceInterface):
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3.S3_ENDPOINT_URL,
            aws_access_key_id=settings.s3.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.s3.AWS_SECRET_ACCESS_KEY,
            region_name=settings.s3.AWS_REGION,
        )

    def upload(self, bucket, key, data, content_type="application/octet-stream"):
        self.client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)

    def download(self, bucket, key):
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def get_signed_url(self, bucket, key, expiry=3600):
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiry
        )

    def ensure_bucket(self, bucket):
        try:
            self.client.head_bucket(Bucket=bucket)
        except:
            self.client.create_bucket(Bucket=bucket)
```

### 4. Bucket Auto-Creation

In `app.py` startup event:
```python
storage = S3StorageService()
storage.ensure_bucket(settings.s3.S3_REPORTS_BUCKET)
```

---

## Testing Strategy

| Test Type | Scope | Priority |
|---|---|---|
| Integration | Ping task enqueue + execute | High |
| Integration | S3 upload + download + signed URL (against MinIO) | High |
| Integration | Bucket auto-creation | Medium |
| Unit | Cleanup task deletes old records | Medium |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| MinIO not running when app starts | Medium | Low | ensure_bucket catches connection error, logs warning, doesn't crash app |
| Celery Beat in same process | Low | Low | Fine for dev. Production would separate. Out of scope |
