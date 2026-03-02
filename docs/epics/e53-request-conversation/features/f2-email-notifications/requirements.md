# Feature: Email Notifications

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** F2
**Dependencies:** F1 (Waiting Status)
**Complexity:** M

## Scope

### Included
- `EmailSubscriber` — new event bus subscriber in `notification_bc` that listens for `REQUEST_COMMENT_ADDED` and `REQUEST_STATUS_CHANGED` (where new status is `waiting_for_employee`)
- Email routing logic: technician comment → email to employee; employee comment → email to assigned technician; `waiting_for_employee` status change → email to employee
- Celery task `send_request_comment_email` with retry (3 attempts, exponential backoff: 30s, 2min, 10min)
- HTML email templates (2 variants): comment notification + "action required" for waiting status
- Deep link URL generation using `FRONTEND_URL`
- Register `EmailSubscriber` in the event bus (`adapters/http/api/dependencies.py`)
- i18n keys for email subjects and CTA buttons (EN + ES)
- Unit tests: EmailSubscriber routing logic, email template rendering
- Integration tests: POST comment → verify email sent; PATCH status to `waiting_for_employee` → verify email sent

### Excluded (in other features)
- `waiting_for_employee` status, transitions, SLA pause → F1 (must be complete)
- Conversation bubble UI, waiting banner, status dialog → F3
- Email reply-to-ticket (replying to the email to add a comment) → deferred to E23
- Email unsubscribe / opt-out → deferred
- Email frequency throttling / batching → deferred

## User Value

Employees receive an email whenever a technician adds a comment to their request or sets it to "waiting for employee". Technicians receive an email when the employee replies. The email contains the message content and a "View Request" button with a direct link. Employees no longer miss technician questions.

## Acceptance Criteria

- [ ] Email sent to employee when technician adds a comment (`REQUEST_COMMENT_ADDED` event, actor is technician)
- [ ] Email sent to assigned technician when employee adds a comment (`REQUEST_COMMENT_ADDED` event, actor is employee)
- [ ] Email sent to employee when request status changes to `waiting_for_employee`
- [ ] No email sent to the actor (the person who wrote the comment doesn't email themselves)
- [ ] No email sent if request has no assigned technician (employee comment — only in-app notification)
- [ ] Email contains: comment body, author name, request title, request number
- [ ] Email contains "View Request" / "Reply in DSM" button linking to `{FRONTEND_URL}/requests/{request_id}`
- [ ] "Action required" email variant used for `waiting_for_employee` status change (different subject line)
- [ ] If technician adds a comment at the same time as setting `waiting_for_employee`, the email includes the comment
- [ ] Celery task retries 3 times with exponential backoff on failure
- [ ] Failed emails are logged but never block the comment save
- [ ] i18n email subjects: ES `[DSM-{number}] Nuevo mensaje en: {title}` / EN `[DSM-{number}] New message on: {title}`
- [ ] Unit tests pass for subscriber routing and template rendering
- [ ] Integration tests pass for end-to-end email sending
- [ ] `make test` and `make lint` pass

## Technical Scope

### Entities (owned by this feature)
- None (no new persisted entities — emails are transient)

### Entities (used from dependencies)
- `ServiceRequest` (from F1) — read `created_by`, `assigned_to`, `title`, `number`, `status`
- `RequestComment` (existing) — read `body`, `author_id`
- `User` (existing) — look up email address by user ID

### Key Components
- `src/notification_bc/notification/application/services/email_subscriber.py` — NEW: listens for events, resolves recipients, queues Celery task
- `core/tasks/email.py` — NEW: Celery task `send_request_comment_email` with retry
- `core/email.py` — Add `send_request_message_email()` and `send_request_waiting_email()` template functions
- `adapters/http/api/dependencies.py` — Register `EmailSubscriber` in the event bus
- `web/app/src/locales/en.ts` + `es.ts` — Email-related i18n keys (for any frontend email preferences, if added later)

## Notes

- The `EmailSubscriber` follows the same pattern as the existing `NotificationSubscriber`: receives `DomainEvent` + `Session`, resolves target users, executes action. The key difference is it queues a Celery task instead of writing to the DB.
- The subscriber needs to look up the recipient's email address from their user ID. Use the existing `UserRepository` to fetch the user object.
- For the `waiting_for_employee` status change email, if a comment was added in the same request (US-09 from F3), the comment event fires first, then the status change event. The status change email should check for the most recent comment to include it. Alternatively, F3's status dialog sends the comment and status change in one API call, and the backend can emit a combined event.
- The `Reply-To` header should be set to a no-reply address for now. When E23 (email intake) is implemented, this can be changed to a per-request address for reply-by-email.
