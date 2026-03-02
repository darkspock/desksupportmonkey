# Solution Design: F2 — Email Notifications

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-02
**Bounded Contexts:** `notification_bc` (primary), `request_bc` (read), `auth_bc` (read)

## Summary

Add an `EmailSubscriber` to the existing EventBus in `notification_bc`. It listens for `REQUEST_COMMENT_ADDED` and `REQUEST_STATUS_CHANGED` (where `new_status == "waiting_for_employee"`) events, resolves the email recipient, and queues a Celery task to send the email asynchronously. Two HTML email templates are used: a "comment notification" variant and an "action required" variant for waiting status. Emails are sent via the existing `EmailServiceInterface` (Brevo in prod, console in dev). Failed emails are retried 3 times with exponential backoff and never block the comment save.

## Architecture Decision

**Approach:** New `EmailSubscriber` (same pattern as `NotificationSubscriber` + `WebSocketSubscriber`) that delegates actual sending to a Celery task. The subscriber runs synchronously inside the EventBus `publish()` call but only enqueues a task — no I/O during the HTTP request.

**Why this approach:**
1. Follows the existing subscriber pattern — the EventBus already has `NotificationSubscriber` and `WebSocketSubscriber` registered in `dependencies.py`. Adding a third subscriber is a natural extension.
2. Celery provides retry, backoff, and failure isolation out of the box. Existing tasks in `core/tasks/` follow the same pattern.
3. No new domain entities or database tables — emails are transient.

**Alternatives considered:**
1. *Send email directly inside the subscriber (no Celery)* — Rejected: HTTP call to Brevo blocks the request thread. EventBus catches exceptions but the latency would degrade comment response time.
2. *Add email sending to the existing `NotificationSubscriber`* — Rejected: violates single-responsibility. The notification subscriber creates DB notifications; email is a separate delivery channel with different retry semantics.
3. *New event types for email-only events* — Rejected: the existing `REQUEST_COMMENT_ADDED` and `REQUEST_STATUS_CHANGED` events already carry the needed payload. Adding new event types would require changes to the router layer for no benefit.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `EventBus` | `src/notification_bc/.../event_bus.py` | Yes | None — just subscribe a new listener |
| `NotificationSubscriber` (pattern) | `src/notification_bc/.../notification_subscriber.py` | Pattern ref | None — new subscriber follows same `__call__(event, db)` pattern |
| `WebSocketSubscriber` (pattern) | `src/notification_bc/.../websocket_subscriber.py` | Pattern ref | None |
| `TargetResolver` | `src/notification_bc/.../target_resolver.py` | No | Not reused — email routing has different logic (1:1 recipient, not broadcast) |
| `DomainEvent` | `src/notification_bc/.../events.py` | Yes | None — payload already includes `request_id`, `created_by`, `assigned_to` |
| `RequestEventFactory` | `src/notification_bc/.../event_factory.py` | Yes | Modify `comment_added()` to include `comment_body` and `request_title` in payload |
| `EmailServiceInterface` | `core/email.py` | Yes | Add `send_request_notification_email()` helper function |
| `get_email_service()` | `core/email.py` | Yes | Used inside Celery task to get the right service |
| `UserRepository` | `src/auth_bc/user/infrastructure/repository.py` | Yes | `find_by_id()` returns `User` with `.email` and `.name` |
| `UserRepository.find_by_ids()` | `src/auth_bc/user/infrastructure/repository.py` | Yes | Batch lookup for recipient + actor names |
| Celery app | `core/celery.py` | Yes | Register new task |
| Jinja2 env | `core/tasks/audit.py` | Pattern ref | Same template loading pattern, reuse `TEMPLATE_DIR` approach |
| `settings.FRONTEND_URL` | `core/config.py` | Yes | Used for deep link generation |
| `settings.BRAND_NAME` | `core/config.py` | Yes | Used in email subject and branding |
| `dependencies.py` | `adapters/http/api/dependencies.py` | Yes | Register `EmailSubscriber` in `_event_bus` |

## Implementation Plan

### 1. Domain Layer

No new entities, value objects, or enums. This feature produces no persisted domain objects — emails are transient side effects.

#### Event Payload Enhancement

The existing `RequestEventFactory.comment_added()` currently only includes `request_id`, `created_by`, and `assigned_to` in the payload. The email subscriber needs the comment body and request title to render the email. Two options:

- **Option A:** Enrich the `comment_added()` factory to include `comment_body` and `request_title` in the payload.
- **Option B:** Have the Celery task re-query the database for the comment and request.

**Decision: Option A.** Enriching the payload avoids a database round-trip in the async task and keeps the task stateless. The DomainEvent is in-memory only, so adding 2 fields has no storage cost.

**RequestEventFactory.comment_added() — updated:**

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

Similarly, `status_changed()` already includes `request_id`, `created_by`, `assigned_to`, `old_status`, `new_status`. Add `title`:

```python
@staticmethod
def status_changed(
    request: ServiceRequest, old_status: str, new_status: str, actor_id: str,
    reason: str | None = None,
) -> DomainEvent:
    payload: dict = {
        "request_id": request.id,
        "created_by": request.created_by,
        "assigned_to": request.assigned_to,
        "old_status": old_status,
        "new_status": new_status,
        "title": request.title,
    }
    ...
```

### 2. Application Layer

#### EmailSubscriber

New file: `src/notification_bc/notification/application/services/email_subscriber.py`

```python
import logging
from typing import Callable

from sqlalchemy.orm import Session

from src.notification_bc.notification.domain.events import DomainEvent
from src.notification_bc.notification.domain.enums import EventType

logger = logging.getLogger(__name__)


class EmailSubscriber:
    """EventBus subscriber that queues email notifications via Celery.

    Listens for:
    - REQUEST_COMMENT_ADDED → email the "other side" (tech→employee or employee→tech)
    - REQUEST_STATUS_CHANGED where new_status == "waiting_for_employee" → email employee
    """

    def __call__(self, event: DomainEvent, db: Session) -> None:
        if event.event_type == EventType.REQUEST_COMMENT_ADDED:
            self._handle_comment(event, db)
        elif event.event_type == EventType.REQUEST_STATUS_CHANGED:
            self._handle_status_change(event, db)

    def _handle_comment(self, event: DomainEvent, db: Session) -> None:
        """Route: technician comment → email employee; employee comment → email technician."""
        from src.auth_bc.user.infrastructure.repository import UserRepository

        actor_id = event.actor_id
        created_by = event.payload.get("created_by")
        assigned_to = event.payload.get("assigned_to")

        if not created_by and not assigned_to:
            return

        user_repo = UserRepository(db)
        actor = user_repo.find_by_id(actor_id)
        if not actor:
            return

        # Determine recipient: if actor is the employee (created_by), email technician; otherwise email employee
        if actor_id == created_by:
            # Employee commented → email assigned technician
            if not assigned_to:
                return  # No technician assigned — skip email (in-app only)
            recipient = user_repo.find_by_id(assigned_to)
        else:
            # Technician/other commented → email the employee (created_by)
            recipient = user_repo.find_by_id(created_by) if created_by else None

        if not recipient or not recipient.email:
            return

        self._enqueue_email(
            to_email=recipient.email,
            to_name=recipient.name or recipient.email,
            actor_name=actor.name or actor.email,
            request_id=event.payload.get("request_id", ""),
            request_title=event.payload.get("title", ""),
            comment_body=event.payload.get("comment_body", ""),
            variant="comment",
            company_id=event.company_id,
        )

    def _handle_status_change(self, event: DomainEvent, db: Session) -> None:
        """Send 'action required' email to employee when status → waiting_for_employee."""
        new_status = event.payload.get("new_status")
        if new_status != "waiting_for_employee":
            return

        created_by = event.payload.get("created_by")
        if not created_by:
            return

        # Don't email the actor if they set the status themselves (unlikely but safe)
        if event.actor_id == created_by:
            return

        from src.auth_bc.user.infrastructure.repository import UserRepository

        user_repo = UserRepository(db)
        actor = user_repo.find_by_id(event.actor_id)
        recipient = user_repo.find_by_id(created_by)

        if not recipient or not recipient.email:
            return

        self._enqueue_email(
            to_email=recipient.email,
            to_name=recipient.name or recipient.email,
            actor_name=actor.name or actor.email if actor else "Technician",
            request_id=event.payload.get("request_id", ""),
            request_title=event.payload.get("title", ""),
            comment_body="",  # status change — no comment body (unless F3 adds combined events)
            variant="action_required",
            company_id=event.company_id,
        )

    def _enqueue_email(
        self,
        to_email: str,
        to_name: str,
        actor_name: str,
        request_id: str,
        request_title: str,
        comment_body: str,
        variant: str,
        company_id: str,
    ) -> None:
        from core.tasks.email_notifications import send_request_notification_email

        send_request_notification_email.delay(
            to_email=to_email,
            to_name=to_name,
            actor_name=actor_name,
            request_id=request_id,
            request_title=request_title,
            comment_body=comment_body,
            variant=variant,
        )
```

**Key design decisions:**
- Uses deferred imports (`from core.tasks...`) inside methods to avoid circular imports (Celery task → SessionLocal → models).
- The subscriber does a synchronous DB lookup for user email (fast, in same session). The expensive part (HTTP call to Brevo) is offloaded to Celery.
- No email sent when `actor_id == recipient_id` (person doesn't email themselves).
- No email sent when there's no assigned technician on an employee comment.

### 3. Infrastructure Layer

#### Celery Task

New file: `core/tasks/email_notifications.py`

```python
import logging
import os

from jinja2 import Environment, FileSystemLoader

from core.celery import celery_app
from core.config import settings
from core.email import get_email_service

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "templates", "email"
)
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
_jinja_env.globals["brand_name"] = settings.BRAND_NAME
_jinja_env.globals["frontend_url"] = settings.FRONTEND_URL


@celery_app.task(
    name="core.tasks.email_notifications.send_request_notification_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # 30s first retry
    retry_backoff=True,       # exponential: 30s, 60s, 120s
    retry_backoff_max=600,    # cap at 10 min
)
def send_request_notification_email(
    self,
    to_email: str,
    to_name: str,
    actor_name: str,
    request_id: str,
    request_title: str,
    comment_body: str,
    variant: str,
) -> None:
    """Send email notification for request comments or waiting status."""
    try:
        template = _jinja_env.get_template(f"request_{variant}.html")
        request_url = f"{settings.FRONTEND_URL}/requests/{request_id}"

        html = template.render(
            to_name=to_name,
            actor_name=actor_name,
            request_title=request_title,
            comment_body=comment_body,
            request_url=request_url,
        )

        # Build subject line
        if variant == "action_required":
            subject = f"[{settings.BRAND_NAME}] Action required: {request_title}"
        else:
            subject = f"[{settings.BRAND_NAME}] New message on: {request_title}"

        email_service = get_email_service()
        email_service.send(to_email, subject, html)
        logger.info(
            "Request email sent: variant=%s, to=%s, request=%s",
            variant, to_email, request_id,
        )
    except Exception as exc:
        logger.error(
            "Failed to send request email: variant=%s, to=%s, request=%s, error=%s",
            variant, to_email, request_id, str(exc),
        )
        raise self.retry(exc=exc)
```

#### Email Templates

Two HTML templates in `templates/email/`:

**`templates/email/request_comment.html`** — Comment notification:

```html
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <h2 style="margin-top: 0; color: #1a1a1a;">New message on your request</h2>
        <p style="color: #4a4a4a;">Hi {{ to_name }},</p>
        <p style="color: #4a4a4a;"><strong>{{ actor_name }}</strong> commented on <strong>{{ request_title }}</strong>:</p>
        {% if comment_body %}
        <div style="background: #f8f9fa; border-left: 4px solid #2563eb; padding: 12px 16px; margin: 16px 0; border-radius: 0 4px 4px 0;">
            <p style="margin: 0; color: #333; white-space: pre-wrap;">{{ comment_body }}</p>
        </div>
        {% endif %}
        <p>
            <a href="{{ request_url }}" style="display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: 500;">
                View Request
            </a>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 32px; border-top: 1px solid #eee; padding-top: 16px;">
            This email was sent by {{ brand_name }}. You received this because you are involved in this request.
        </p>
    </div>
</body>
</html>
```

**`templates/email/request_action_required.html`** — Action required (waiting for employee):

```html
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; padding: 12px 16px; margin-bottom: 24px;">
            <strong style="color: #92400e;">Action required</strong>
        </div>
        <h2 style="margin-top: 0; color: #1a1a1a;">Your response is needed</h2>
        <p style="color: #4a4a4a;">Hi {{ to_name }},</p>
        <p style="color: #4a4a4a;"><strong>{{ actor_name }}</strong> is waiting for your response on <strong>{{ request_title }}</strong>.</p>
        {% if comment_body %}
        <div style="background: #f8f9fa; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 16px 0; border-radius: 0 4px 4px 0;">
            <p style="margin: 0; color: #333; white-space: pre-wrap;">{{ comment_body }}</p>
        </div>
        {% endif %}
        <p style="color: #4a4a4a;">Please reply so the technician can continue working on your request.</p>
        <p>
            <a href="{{ request_url }}" style="display: inline-block; padding: 12px 24px; background-color: #f59e0b; color: #1a1a1a; text-decoration: none; border-radius: 6px; font-weight: 600;">
                Reply in {{ brand_name }}
            </a>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 32px; border-top: 1px solid #eee; padding-top: 16px;">
            This email was sent by {{ brand_name }}. You received this because a technician needs your input on a support request.
        </p>
    </div>
</body>
</html>
```

### 4. HTTP Layer

#### Endpoints

No new endpoints.

#### Router changes (event payload enrichment)

The `add_comment` endpoint in `adapters/http/api/requests/routers.py` currently calls `RequestEventFactory.comment_added()` without passing the comment body. Update to pass `comment_body`:

```python
# In the add_comment endpoint, where comment_added event is published:
comment_event = RequestEventFactory.comment_added(
    sr, actor_id=current_user.id,
    comment_body=payload.body,  # NEW: pass comment text for email
)
event_bus.publish(comment_event, db)
```

Similarly, the `change_status` endpoint already calls `RequestEventFactory.status_changed()` which will now include `title` in the payload (from the factory change above). No router change needed there.

### 5. Registration

#### dependencies.py

Register `EmailSubscriber` as the third subscriber:

```python
from src.notification_bc.notification.application.services.email_subscriber import (
    EmailSubscriber,
)

_event_bus = EventBus()
_event_bus.subscribe(
    NotificationSubscriber(
        user_repo_factory=UserRepository,
        notification_repo_factory=NotificationRepository,
    )
)
_event_bus.subscribe(
    WebSocketSubscriber(
        user_repo_factory=UserRepository,
        notification_repo_factory=NotificationRepository,
    )
)
_event_bus.subscribe(EmailSubscriber())
```

Note: `EmailSubscriber` does not need factory params — it uses deferred imports and creates its own `UserRepository` from the session passed by the EventBus.

### 6. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/notification_bc/notification/application/services/email_subscriber.py` | **Create** | New EventBus subscriber — email routing logic |
| `core/tasks/email_notifications.py` | **Create** | New Celery task — render template + send email |
| `templates/email/request_comment.html` | **Create** | HTML template for comment notification |
| `templates/email/request_action_required.html` | **Create** | HTML template for action required notification |
| `src/notification_bc/notification/application/services/event_factory.py` | Modify | Add `comment_body` param to `comment_added()`, add `title` to `status_changed()` payload |
| `adapters/http/api/requests/routers.py` | Modify | Pass `comment_body=payload.body` when creating comment event |
| `adapters/http/api/dependencies.py` | Modify | Register `EmailSubscriber` in `_event_bus` |

#### Breaking Changes

None. The `comment_added()` factory gains a new optional `comment_body` keyword argument with default `""`. All existing callers continue to work unchanged.

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `notification_bc` | Primary BC | Owns the `EmailSubscriber` and event infrastructure |
| `auth_bc` | Read dependency | `UserRepository.find_by_id()` to look up recipient email and name |
| `request_bc` | Event source | `RequestEventFactory` creates events with request data in payload |
| `core/email.py` | Infrastructure | `EmailServiceInterface` (Brevo / Console) — existing |
| `core/celery.py` | Infrastructure | Celery task queue — existing |
| Jinja2 | Library | Already installed (used by `core/tasks/audit.py`) |
| F1 (Waiting Status) | Feature dep | `waiting_for_employee` status must exist before this feature ships |

## Testing Strategy

| Test Type | Scope | Priority | File |
|-----------|-------|----------|------|
| Unit | `EmailSubscriber._handle_comment()` — tech comment emails employee | High | `tests/unit/notification_bc/test_email_subscriber.py` |
| Unit | `EmailSubscriber._handle_comment()` — employee comment emails technician | High | same |
| Unit | `EmailSubscriber._handle_comment()` — no email when no assigned technician | High | same |
| Unit | `EmailSubscriber._handle_comment()` — no email to self (actor == recipient) | High | same |
| Unit | `EmailSubscriber._handle_status_change()` — waiting status emails employee | High | same |
| Unit | `EmailSubscriber._handle_status_change()` — ignores non-waiting status changes | High | same |
| Unit | Template rendering — comment variant renders with body | Medium | same |
| Unit | Template rendering — action_required variant renders with warning banner | Medium | same |
| Unit | Subject line — correct format per variant | Medium | same |
| Integration | POST comment → verify Celery task enqueued / email sent | High | `tests/integration/test_requests_endpoints.py` |
| Integration | PATCH status to waiting_for_employee → verify email sent | High | same |
| Integration | POST comment by employee when no technician assigned → no email | Medium | same |

### Critical Test Scenarios

1. **Tech comments on request → employee gets email** with comment body, request title, "View Request" button
2. **Employee comments on request → technician gets email** (assigned_to receives it)
3. **Employee comments but no technician assigned → no email** (only in-app notification)
4. **Status changes to waiting_for_employee → employee gets "action required" email** with amber banner
5. **Status changes to resolved → no email** (not a waiting status change)
6. **Actor is the employee and sets waiting_for_employee → no email** (they set it on themselves — edge case guard)
7. **Celery task fails → retried 3 times with backoff** (mock the email service to raise)
8. **Email service unavailable → error logged, comment still saved** (non-blocking)

## Implementation Order

1. [ ] Modify `RequestEventFactory.comment_added()` to accept `comment_body` param
2. [ ] Modify `RequestEventFactory.status_changed()` to include `title` in payload
3. [ ] Create `templates/email/request_comment.html`
4. [ ] Create `templates/email/request_action_required.html`
5. [ ] Create `core/tasks/email_notifications.py` — Celery task
6. [ ] Create `src/notification_bc/notification/application/services/email_subscriber.py`
7. [ ] Register `EmailSubscriber` in `adapters/http/api/dependencies.py`
8. [ ] Update `adapters/http/api/requests/routers.py` — pass `comment_body` to event factory
9. [ ] Unit tests: EmailSubscriber routing logic
10. [ ] Unit tests: Template rendering
11. [ ] Integration tests: end-to-end email flow
12. [ ] Run `make test` and `make lint`

## Open Technical Questions

1. **i18n for email subjects/templates:** The requirements mention ES/EN email subjects (`[DSM-{number}] Nuevo mensaje...`). However, we don't currently store a user's preferred language. **Recommendation for now:** Use English-only templates. Add language preference to User entity in a future feature (E24 or similar). The template structure already supports Jinja2 conditionals, so i18n can be added later without restructuring.

2. **Request number (`DSM-{number}`):** The requirements reference a "request number" in the subject. The current `ServiceRequest` entity uses ULID `id` but doesn't have a sequential human-readable number. **Recommendation:** Use the request title in the subject line for now: `[DSM Control] New message on: {title}`. Add sequential request numbers as a separate future feature.

3. **Combined comment + waiting_for_employee:** When F3 implements the "waiting for employee" dialog that includes a comment, both a `REQUEST_COMMENT_ADDED` and `REQUEST_STATUS_CHANGED` event fire. This means the employee could get 2 emails. **Recommendation:** The `_handle_status_change()` method should check if a `REQUEST_COMMENT_ADDED` event was already handled for the same request in the same EventBus publish cycle. Simplest approach: if the `waiting_for_employee` status change payload includes a `comment_body` (set by F3's combined API call), use the "action required" template with the comment included, and skip the separate comment email. For F2 (without F3), both events come from separate API calls, so this isn't a problem yet.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Brevo rate limiting on high-volume comment activity | Low | Medium | Celery retry with backoff handles transient failures. For sustained rate limiting, batch/throttle can be added later. |
| Email delivery to spam folder | Medium | Medium | Use Brevo's domain verification. Keep email content clean (no excessive images, proper headers). |
| User without email address | Very Low | Low | Guard: `if not recipient.email: return`. The email field is required at registration, so this is just a safety check. |
| Duplicate emails on rapid comment submission | Low | Low | EventBus processes synchronously, so events fire in order. Celery task is idempotent (sending same email twice is annoying but not harmful). |
| Circular import from deferred imports in subscriber | Low | High | Tested pattern: `core/tasks/sla.py` already uses deferred imports for `SessionLocal` and repos inside task functions. |
