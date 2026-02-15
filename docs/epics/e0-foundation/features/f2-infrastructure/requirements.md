# Feature F2: Async Infrastructure (Celery + MinIO)

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** F0 (Bootstrapping)
**Complexity:** S

---

## Scope

### Included
- Celery app configuration (verify/fix existing `core/celery.py`)
- Celery worker starts with `make queue`
- Redis broker connection verified
- Task routes for `reports` queue
- Test task: enqueue and execute a simple ping task
- Periodic task: cleanup magic links older than 7 days (Celery Beat)
- MinIO S3 client service (`core/storage.py`)
- `dsm-reports` bucket auto-creation on startup
- Upload file to MinIO
- Download file from MinIO
- Generate signed URL for a file in MinIO
- MinIO Console accessible at localhost:9001

### Excluded (in other features)
- Report generation logic (E6)
- Actual report templates (E6)
- Any business logic using Celery or MinIO

---

## User Value

After F2:
- A developer can enqueue a Celery task and see it execute
- A developer can upload/download files to MinIO programmatically
- Magic links are automatically cleaned up (no manual DB maintenance)
- Infrastructure is ready for E6 (Report Generation) without any setup work

---

## Acceptance Criteria

### Celery
- [ ] `make queue` starts a Celery worker connected to Redis
- [ ] Worker logs show successful connection to broker
- [ ] A test task (`ping`) can be enqueued via `celery_app.send_task()` and returns result
- [ ] Task routes: any task matching `*.reports.*` goes to `reports` queue
- [ ] Task time limit: 5 minutes, soft limit: 4.5 minutes
- [ ] Serialization: JSON only

### Celery Beat (Periodic Tasks)
- [ ] Magic link cleanup runs daily
- [ ] Deletes MagicLink records where `created_at` < now - 7 days
- [ ] Cleanup task logs how many records were deleted

### MinIO (S3)
- [ ] S3 client connects to MinIO at `localhost:9000`
- [ ] `dsm-reports` bucket is created if it doesn't exist (on app startup or via setup script)
- [ ] `storage.upload(bucket, key, data)` uploads a file
- [ ] `storage.download(bucket, key)` returns file bytes
- [ ] `storage.get_signed_url(bucket, key, expiry=3600)` returns a pre-signed URL
- [ ] MinIO Console at `localhost:9001` shows the bucket and uploaded files

---

## Technical Scope

### Entities (used from F0/F1)
- MagicLink (cleanup task deletes old records)

### Key Components

```
core/
├── celery.py          # Celery app config (exists, verify/fix)
├── celery_app.py      # Alternative celery config (consolidate with celery.py)
├── storage.py         # NEW: S3StorageService (upload, download, signed_url)
└── tasks/
    ├── __init__.py
    ├── ping.py        # NEW: Test task (ping -> pong)
    └── cleanup.py     # NEW: Magic link cleanup periodic task
```

---

## Notes

- `core/celery.py` and `core/celery_app.py` both exist from the AICheck copy. They should be consolidated into a single `core/celery.py` during implementation.
- The S3 storage service should be an abstraction (interface + implementation) so it can work with real AWS S3 in production by just changing config.
- Celery Beat can run in the same worker process for development (`-B` flag). In production it would be a separate process, but that's out of scope for now.
