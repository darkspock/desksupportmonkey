# Implementation Tasks: F2 — Email Notifications

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-02
**Total Tasks:** 11
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Event Payload Enhancement | 2 | S |
| Infrastructure — Email Templates | 2 | S |
| Infrastructure — Celery Task | 1 | M |
| Application — EmailSubscriber | 1 | M |
| HTTP — Router Enrichment | 1 | S |
| Configuration — DI Registration | 1 | S |
| Tests — Unit | 1 | M |
| Tests — Integration | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Domain — Event Payload Enhancement

### TASK-001: Enrich `RequestEventFactory.comment_added()` with `comment_body` and `title`

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add `comment_body` parameter to `comment_added()` and include both `comment_body` and `title` (request title) in the event payload. The parameter must have a default value of `""` so existing callers are not broken.

**File:** `src/notification_bc/notification/application/services/event_factory.py`

**Implementation:**
```python
@staticmethod
def comment_added(
    request: ServiceRequest, actor_id: str,
    comment_body: str = "",
) -> DomainEvent:
    return DomainEvent(
        event_type=EventType.REQUEST_COMMENT_ADDED,
        company_id=request.company_id,
        actor_id=actor_id,
        payload={
            "request_id": request.id,
            "created_by": request.created_by,
            "assigned_to": request.assigned_to,
            "title": request.title,
            "comment_body": comment_body,
        },
        title="New comment",
        body=f"Comment on: {request.title}",
    )
```

**Acceptance Criteria:**
- [x] `comment_added()` accepts optional `comment_body: str = ""`
- [x] Payload includes `"title": request.title`
- [x] Payload includes `"comment_body": comment_body`
- [x] Existing callers without `comment_body` continue to work (backward compatible)

---

### TASK-002: Add `title` to `RequestEventFactory.status_changed()` payload

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add `request.title` to the `status_changed()` event payload so the email subscriber can render the request title without a database re-query.

**File:** `src/notification_bc/notification/application/services/event_factory.py`

**Implementation:**
Add `"title": request.title` to the payload dict inside `status_changed()`:

```python
payload: dict = {
    "request_id": request.id,
    "created_by": request.created_by,
    "assigned_to": request.assigned_to,
    "old_status": old_status,
    "new_status": new_status,
    "title": request.title,  # NEW
}
```

**Acceptance Criteria:**
- [x] Payload includes `"title": request.title`
- [x] No signature change — fully backward compatible

---

## Phase 2: Infrastructure — Email Templates

### TASK-003: Create comment notification email template

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** None

**Description:**
Create the HTML email template for comment notifications. Uses Jinja2 variables: `to_name`, `actor_name`, `request_title`, `comment_body`, `request_url`, `brand_name`.

**File:** `templates/email/request_comment.html` (CREATE — also create `templates/email/` directory)

**Implementation:**
Copy the template exactly from the design document (section "Email Templates — `request_comment.html`"):
- Header: "New message on your request"
- Greeting: "Hi {{ to_name }}"
- Body: "{{ actor_name }} commented on {{ request_title }}:"
- Quoted comment block with blue left border (only if `comment_body` is non-empty)
- CTA button: "View Request" → `{{ request_url }}` (blue `#2563eb`)
- Footer: "This email was sent by {{ brand_name }}"

**Acceptance Criteria:**
- [x] `templates/email/` directory exists
- [x] Template renders correctly with all variables
- [x] Comment body conditionally shown (`{% if comment_body %}`)
- [x] "View Request" button links to `{{ request_url }}`

---

### TASK-004: Create action required email template

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** None

**Description:**
Create the HTML email template for the "action required" notification when a request is set to `waiting_for_employee`. Uses same Jinja2 variables as comment template.

**File:** `templates/email/request_action_required.html` (CREATE)

**Implementation:**
Copy the template exactly from the design document (section "Email Templates — `request_action_required.html`"):
- Amber warning banner: "Action required"
- Header: "Your response is needed"
- Body: "{{ actor_name }} is waiting for your response on {{ request_title }}"
- Optional quoted comment block with amber left border
- Prompt: "Please reply so the technician can continue working on your request."
- CTA button: "Reply in {{ brand_name }}" → `{{ request_url }}` (amber `#f59e0b`)
- Footer with context explanation

**Acceptance Criteria:**
- [x] Template renders correctly with all variables
- [x] Amber warning banner visible at top
- [x] Comment body conditionally shown (`{% if comment_body %}`)
- [x] "Reply in {{ brand_name }}" button links to `{{ request_url }}`

---

## Phase 3: Infrastructure — Celery Task

### TASK-005: Create `send_request_notification_email` Celery task

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Description:**
Create the Celery task that renders the email template and sends it via `EmailServiceInterface`. Retries 3 times with exponential backoff. Uses Jinja2 `Environment` with `FileSystemLoader` pointing to `templates/email/`.

**File:** `core/tasks/email_notifications.py` (CREATE)

**Implementation:**
Follow the design document exactly:
- Module-level Jinja2 env loading `templates/email/` directory
- Set globals: `brand_name`, `frontend_url`
- Task decorator: `@celery_app.task(name="core.tasks.email_notifications.send_request_notification_email", bind=True, max_retries=3, default_retry_delay=30, retry_backoff=True, retry_backoff_max=600)`
- Parameters: `to_email, to_name, actor_name, request_id, request_title, comment_body, variant`
- Template selection: `request_{variant}.html`
- Deep link: `{FRONTEND_URL}/requests/{request_id}`
- Subject lines: `"[{BRAND_NAME}] Action required: {title}"` for action_required, `"[{BRAND_NAME}] New message on: {title}"` for comment
- Send via `get_email_service().send()`
- On exception: log error + `raise self.retry(exc=exc)`

**Acceptance Criteria:**
- [x] Task registered with Celery via `@celery_app.task`
- [x] Loads correct template based on `variant` parameter
- [x] Generates deep link URL using `FRONTEND_URL`
- [x] Subject line varies by variant
- [x] Retries 3 times with exponential backoff on failure
- [x] Logs success and failure

---

## Phase 4: Application — EmailSubscriber

### TASK-006: Create `EmailSubscriber` class

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Create the EventBus subscriber that listens for `REQUEST_COMMENT_ADDED` and `REQUEST_STATUS_CHANGED` events, resolves the email recipient, and enqueues the Celery task. Follows the same `__call__(event, db)` pattern as `NotificationSubscriber` and `WebSocketSubscriber`.

**File:** `src/notification_bc/notification/application/services/email_subscriber.py` (CREATE)

**Implementation:**
Follow the design document exactly:

- `__call__(self, event, db)` — dispatches to `_handle_comment` or `_handle_status_change` based on `event.event_type`
- `_handle_comment(event, db)`:
  - Looks up actor via `UserRepository(db).find_by_id(actor_id)`
  - If `actor_id == created_by` (employee commented): email `assigned_to` (technician). If no `assigned_to`, return (no email).
  - Else (technician commented): email `created_by` (employee).
  - Guard: no email if recipient not found or has no email.
  - Calls `_enqueue_email(variant="comment")`
- `_handle_status_change(event, db)`:
  - Only acts when `new_status == "waiting_for_employee"`
  - Emails `created_by` (the employee)
  - Guard: skip if `actor_id == created_by` (self-set)
  - Calls `_enqueue_email(variant="action_required")`
- `_enqueue_email(...)` — calls `send_request_notification_email.delay(...)`
- Uses deferred imports to avoid circular dependencies

**Acceptance Criteria:**
- [x] Implements `__call__(self, event: DomainEvent, db: Session) -> None`
- [x] Handles `REQUEST_COMMENT_ADDED` — routes tech→employee and employee→tech
- [x] Handles `REQUEST_STATUS_CHANGED` — only for `waiting_for_employee`
- [x] No email sent to the actor (self-exclusion)
- [x] No email sent when no assigned technician (employee comment)
- [x] No email sent when recipient has no email address
- [x] Enqueues Celery task via `.delay()` (non-blocking)
- [x] Uses deferred imports inside methods

---

## Phase 5: HTTP — Router Enrichment

### TASK-007: Pass `comment_body` to event factory in add_comment endpoint

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Update the `add_comment` endpoint in the requests router to pass the comment body text when creating the `comment_added` domain event. Currently the call at line ~1073 is:
```python
event = RequestEventFactory.comment_added(sr, actor_id=current_user.id)
```
Change to:
```python
event = RequestEventFactory.comment_added(sr, actor_id=current_user.id, comment_body=payload.body)
```

**File:** `adapters/http/api/requests/routers.py`

**Acceptance Criteria:**
- [x] `comment_body=body.body` passed to `RequestEventFactory.comment_added()`
- [x] No other changes to the endpoint logic

---

## Phase 6: Configuration — DI Registration

### TASK-008: Register `EmailSubscriber` in EventBus

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-006

**Description:**
Register the `EmailSubscriber` as a third subscriber in the EventBus alongside the existing `NotificationSubscriber` and `WebSocketSubscriber`.

**File:** `adapters/http/api/dependencies.py`

**Implementation:**
Add import and subscribe call:
```python
from src.notification_bc.notification.application.services.email_subscriber import (
    EmailSubscriber,
)

# After existing subscribes:
_event_bus.subscribe(EmailSubscriber())
```

Note: `EmailSubscriber` takes no constructor arguments — it uses deferred imports internally.

**Acceptance Criteria:**
- [x] `EmailSubscriber` imported
- [x] `_event_bus.subscribe(EmailSubscriber())` added after existing subscribers
- [x] Application starts without import errors

---

## Phase 7: Tests — Unit

### TASK-009: Unit tests for EmailSubscriber and Celery task

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-005, TASK-006

**Description:**
Create unit tests covering the email routing logic in `EmailSubscriber` and template rendering / subject lines in the Celery task.

**File:** `tests/unit/notification_bc/test_email_subscriber.py` (CREATE)

**Test Cases (from design — Testing Strategy):**

**EmailSubscriber routing (mock UserRepository + Celery task):**
1. Technician comments → `_handle_comment` emails employee (`created_by`)
2. Employee comments → `_handle_comment` emails technician (`assigned_to`)
3. Employee comments, no assigned technician → no email enqueued
4. Actor is the only participant (actor == created_by, no assigned_to) → no email
5. Status changes to `waiting_for_employee` → `_handle_status_change` emails employee
6. Status changes to `resolved` → `_handle_status_change` does nothing
7. Status changes to `waiting_for_employee` but actor == created_by → no email
8. Recipient has no email address → no email enqueued
9. Event with missing `created_by` in payload → no email

**Celery task (mock email service):**
10. Comment variant → correct subject line format
11. Action required variant → correct subject line format
12. Template renders with all variables (comment body, request title, URL)
13. Email service failure → task raises for retry

**Acceptance Criteria:**
- [x] All 14 test cases pass (13 planned + 1 additional edge case)
- [x] Uses `unittest.mock.MagicMock` for UserRepository and email service
- [x] Uses `unittest.mock.patch` for `send_request_notification_email.delay`
- [x] No real email sending or Celery execution

---

## Phase 8: Tests — Integration

### TASK-010: Integration tests for email notification flow

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-007, TASK-008

**Description:**
Add integration tests to verify the end-to-end flow: POST comment → EventBus → EmailSubscriber → Celery task enqueued. Uses the existing test infrastructure with mocked email service.

**File:** `tests/integration/test_requests_endpoints.py` (EXTEND)

**Test Cases (from design):**
1. POST comment by technician on assigned request → verify email task enqueued for employee
2. PATCH status to `waiting_for_employee` → verify email task enqueued for employee
3. POST comment by employee when no technician assigned → verify no email task enqueued

**Implementation notes:**
- Mock `send_request_notification_email.delay` to capture calls
- Assert correct `to_email`, `variant`, and `comment_body` in the call args
- Use existing test fixtures for authenticated users and requests

**Acceptance Criteria:**
- [x] All 3 integration tests pass
- [x] Tests verify Celery task is called with correct arguments
- [x] Tests verify no Celery task called when email should be skipped

---

## Phase 9: Verification

### TASK-011: Run full test suite and linter

**Phase:** Verification
**Complexity:** S
**Dependencies:** TASK-009, TASK-010

**Description:**
Run `make test` and `make lint` to ensure no regressions. Fix any failures introduced by F2 changes (e.g., existing tests that mock `comment_added()` and now receive different payload keys).

**Acceptance Criteria:**
- [x] `make test` passes (no new failures — 130 request endpoint tests pass, 14 email subscriber unit tests pass)
- [x] `make lint` passes (only pre-existing E501 line length across entire codebase)
- [x] Any broken existing tests fixed (router variable name `body.body` not `payload.body`, integration tests need `_email_bus` fixture for EventBus with EmailSubscriber)

---

## Dependency Graph

```
TASK-001 (comment_added payload) ──┬──────────────────────── TASK-007 (router enrichment)
                                   │
TASK-002 (status_changed payload)  │
                                   │
TASK-003 (comment template) ───┬── TASK-005 (Celery task) ── TASK-006 (EmailSubscriber) ── TASK-008 (DI registration)
                               │                                     │
TASK-004 (action_required tpl) ┘                                     │
                                                                     │
                                              TASK-009 (unit tests) ─┤
                                                                     │
                               TASK-007 + TASK-008 ── TASK-010 (integration tests)
                                                                     │
                                                      TASK-011 (verification) ─┘
```

## Execution Order

**Batch 1 (Parallel — no dependencies):** TASK-001, TASK-002, TASK-003, TASK-004
**Batch 2 (Sequential):** TASK-005 (depends on templates)
**Batch 3 (Sequential):** TASK-006 (depends on Celery task)
**Batch 4 (Parallel):** TASK-007 (depends on TASK-001), TASK-008 (depends on TASK-006)
**Batch 5 (Parallel):** TASK-009, TASK-010
**Batch 6:** TASK-011

## Final Checklist

- [x] All 11 tasks completed
- [x] All unit tests passing (14/14)
- [x] All integration tests passing (3/3 + 130 existing)
- [x] `make test` passes
- [x] `make lint` passes (only pre-existing E501)
- [x] No emails sent to the actor
- [x] No emails sent when no assigned technician
- [x] Celery retry with backoff verified
- [x] Both email variants render correctly
