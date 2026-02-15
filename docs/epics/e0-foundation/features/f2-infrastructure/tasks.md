# Implementation Tasks: F2 - Async Infrastructure (Celery + MinIO)

**Requirement:** [E0 Foundation Epic - Async Infrastructure]
**Solution Design:** /Users/juanmacias/Projects/desksupportmonkey/docs/epics/e0-foundation/features/f2-infrastructure/design.md
**Created:** 2026-02-15
**Total Tasks:** 11
**Estimated Complexity:** S

---

## Summary

| Phase | Tasks | Complexity |
|---|---|---|
| 1. Infrastructure | 6 | S |
| 2. Application | 1 | S |
| 3. Tests | 3 | S |
| 4. Configuration | 1 | S |

---

## Phase 1: Infrastructure

### TASK-F2-001: Update core/celery.py configuration

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** None

**Description:**
Update the main Celery application configuration with proper app name, Redis broker connection from config, task routes for reports queue, beat schedule for magic link cleanup, and autodiscovery of core.tasks module.

**File:** `core/celery.py`

**Acceptance Criteria:**
- [ ] App name set to "desksupportmonkey"
- [ ] Redis broker URL configured from settings.redis
- [ ] Task routes configured: core.tasks.* -> reports queue
- [ ] Beat schedule configured: cleanup-magic-links runs daily with days=7 kwargs
- [ ] Autodiscover_tasks includes 'core.tasks'

---

### TASK-F2-002: Create ping task

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-F2-001

**Description:**
Create a simple ping task for health checking the Celery worker infrastructure.

**File:** `core/tasks/ping.py`

**Acceptance Criteria:**
- [ ] Task decorated with @celery_app.task
- [ ] Task returns "pong" string
- [ ] Task can be called asynchronously with .delay() or .apply_async()

---

### TASK-F2-003: Create cleanup magic links task

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-F2-001

**Description:**
Create a scheduled task to delete expired magic links from the database. Task accepts configurable days parameter to determine expiration threshold.

**File:** `core/tasks/cleanup.py`

**Acceptance Criteria:**
- [ ] Task decorated with @celery_app.task
- [ ] Accepts days parameter (integer)
- [ ] Deletes magic_links records older than N days
- [ ] Returns count of deleted records
- [ ] Logs cleanup operation with count

---

### TASK-F2-004: Create storage service interface

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** None

**Description:**
Define abstract base class for storage service operations to enable future implementation swapping (S3, local filesystem, etc).

**File:** `core/storage.py`

**Acceptance Criteria:**
- [ ] StorageServiceInterface class inherits from ABC
- [ ] Abstract method: upload(file_path: str, key: str) -> str
- [ ] Abstract method: download(key: str) -> bytes
- [ ] Abstract method: get_signed_url(key: str, expiration: int) -> str
- [ ] Abstract method: ensure_bucket(bucket_name: str) -> bool

---

### TASK-F2-005: Implement S3 storage service

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-F2-004

**Description:**
Implement S3-compatible storage service using boto3 client. Service should read configuration from settings.s3 and support MinIO/S3 endpoints.

**File:** `core/storage.py`

**Acceptance Criteria:**
- [ ] S3StorageService class implements StorageServiceInterface
- [ ] Initializes boto3 client with settings.s3 configuration
- [ ] upload() uploads file to bucket and returns object key
- [ ] download() retrieves object bytes from bucket
- [ ] get_signed_url() generates presigned URL with expiration
- [ ] ensure_bucket() creates bucket if not exists, returns success bool
- [ ] Handles boto3 exceptions appropriately

---

### TASK-F2-006: Create core/tasks/__init__.py

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-F2-002, TASK-F2-003

**Description:**
Create package init file for core.tasks module to enable autodiscovery by Celery.

**File:** `core/tasks/__init__.py`

**Acceptance Criteria:**
- [ ] File exists as Python package marker
- [ ] Imports ping and cleanup tasks for registration
- [ ] Exports task names in __all__ list

---

## Phase 2: Application

### TASK-F2-007: Add bucket auto-creation to app startup

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-F2-005

**Description:**
Ensure reports bucket exists on application startup by calling ensure_bucket() with configured bucket name from settings.

**File:** `app.py`

**Acceptance Criteria:**
- [ ] Import S3StorageService in app.py startup section
- [ ] Call ensure_bucket(settings.s3.S3_REPORTS_BUCKET) during startup
- [ ] Log successful bucket creation/verification
- [ ] Handle exceptions gracefully with appropriate error logging

---

## Phase 3: Tests

### TASK-F2-008: Create integration test for ping task

**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-F2-002

**Description:**
Test that ping task can be called synchronously and asynchronously, and returns expected response.

**File:** `tests/integration/test_celery_tasks.py`

**Acceptance Criteria:**
- [ ] Test calls ping.delay() and waits for result
- [ ] Asserts result equals "pong"
- [ ] Test verifies task executes successfully
- [ ] Uses appropriate fixtures for Celery test configuration

---

### TASK-F2-009: Create integration test for S3 operations

**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-F2-005

**Description:**
Test S3StorageService operations including upload, download, signed URL generation, and bucket creation.

**File:** `tests/integration/test_s3_storage.py`

**Acceptance Criteria:**
- [ ] Test ensure_bucket() creates bucket successfully
- [ ] Test upload() stores file and returns key
- [ ] Test download() retrieves correct file contents
- [ ] Test get_signed_url() returns valid URL
- [ ] Uses test bucket (separate from production)
- [ ] Cleans up test objects after test completion

---

### TASK-F2-010: Create integration test for bucket auto-creation

**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-F2-007

**Description:**
Test that application startup correctly creates reports bucket.

**File:** `tests/integration/test_app_startup.py`

**Acceptance Criteria:**
- [ ] Test mocks S3StorageService.ensure_bucket()
- [ ] Test verifies ensure_bucket() called with correct bucket name
- [ ] Test verifies startup completes without errors
- [ ] Test handles ensure_bucket() failure scenarios

---

## Phase 4: Configuration

### TASK-F2-011: Delete duplicate celery_app.py file

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-F2-001

**Description:**
Remove duplicate Celery configuration file to consolidate configuration in core/celery.py.

**File:** `core/celery_app.py`

**Acceptance Criteria:**
- [ ] File core/celery_app.py deleted
- [ ] No imports reference core/celery_app anywhere in codebase
- [ ] All Celery imports use core/celery instead
- [ ] Application starts successfully without errors

---

## Notes

- All tasks assume Redis is configured and available for Celery broker
- MinIO/S3 credentials must be configured in settings.s3 before testing
- Celery worker and beat processes must be started separately from main application
- Storage service interface allows future migration to other storage backends
- Cleanup task scheduled via Celery Beat for daily execution at midnight
- Reports queue routing enables dedicated worker pools for report generation
