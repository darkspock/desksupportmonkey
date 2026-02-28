# Epic E23 — Multi-channel Intake

**Date:** 2026-02-28
**Priority:** Medium
**Status:** Pending
**Bounded Context:** `intake_bc` (new)
**Dependencies:** E3 (Service Requests) — Done, E4 (Real-time & Notifications) — Done

---

## Business Alignment

### Objective

Enable ticket creation from external channels (email, Slack, Teams, chatbot) so employees can submit requests without logging into the web application, increasing adoption and reducing friction.

### KPI Targets

| KPI | Target |
|-----|--------|
| Channel adoption | 30%+ of tickets created via non-web channels within 3 months |
| Response time | Email-to-ticket latency < 2 minutes |
| Deflection rate | Chatbot resolves 15%+ of queries without ticket creation |
| Zero data loss | 0 lost emails — every received email becomes a ticket or is logged |

### Evidence

- Industry standard for ITSM tools — ServiceNow, Freshdesk, Zendesk all support multi-channel intake
- Users report friction logging into the portal for quick requests
- Email-to-ticket is the #1 requested feature for IT service desks
- DORA/NIS2 benefit: faster incident reporting when employees can email directly

---

## Problem Statement

### Current Situation

Employees must log into the web application to create service requests. This creates friction for:
- Non-technical employees who prefer email
- Urgent situations where logging in adds delay
- Organizations transitioning from email-based support workflows

### Pain Points

| Problem | Impact |
|---------|--------|
| Web-only intake | Low adoption from non-technical staff |
| No email integration | Support teams maintain parallel email inbox manually |
| No chat integration | Employees switch context between Slack/Teams and DSM |
| No guided creation | Employees often submit incomplete or miscategorized requests |

### Who Is Affected

- **Employees:** Must log in to submit any request
- **Technicians:** Manually copy-paste emails into tickets
- **Admins:** Cannot measure true support volume (email requests go untracked)

---

## Proposed Solution

### Overview

Add external intake channels that funnel into the existing `request_bc` request creation flow. Each channel has a dedicated adapter that parses inbound messages, maps them to `CreateRequestCommand` parameters, and creates tickets via the existing command handler.

**Architecture approach:** Each channel is an adapter in the HTTP/infrastructure layer. The domain layer (`request_bc`) remains unchanged — channels are input adapters, not new bounded contexts. A thin `intake_bc` manages channel configuration (which channels are active, per-company settings) and inbound message logging.

### Channels

| Channel | Mechanism | Priority |
|---------|-----------|----------|
| Email (Google Workspace) | IMAP polling via Celery beat | High — first to implement |
| Slack | Slack Events API webhook | Medium |
| Microsoft Teams | Teams Bot Framework webhook | Medium |
| Chatbot (web widget) | WebSocket + guided flow | Low |

---

## Feature: Email Intake via Google Workspace IMAP

### Decision Record

After evaluating options (webhook via Mailgun/SendGrid vs IMAP polling vs receive-only SMTP), the decision is:

- **Production:** Google Workspace with a catch-all email account, polled via IMAP
- **Development:** Mailpit (already in Docker stack) with IMAP on port 1143
- **Authentication:** OAuth2 with refresh token (or service account with domain-wide delegation for Workspace)

**Rationale:** IMAP polling is more robust than webhooks — if processing fails, the email remains UNSEEN in the inbox and is retried on the next polling cycle. No data loss. Google Workspace provides reliable IMAP access with a 2,500 MB/day bandwidth limit per account (more than sufficient for service desk volumes).

### User Stories

**US-01:** As an admin, I can configure an email intake address for my company, so that employees can create tickets by sending email.

Acceptance Criteria:
- [ ] Admin can set intake email address in company settings
- [ ] Admin can enable/disable email intake per company
- [ ] Admin can set default request type for email-created tickets
- [ ] Admin can configure auto-reply (on/off + template text)

**US-02:** As an employee, I can send an email to the support address and have a ticket created automatically, so that I don't need to log into the app.

Acceptance Criteria:
- [ ] Email subject becomes ticket title
- [ ] Email body (plain text) becomes ticket description
- [ ] Sender email is matched to existing user by email address
- [ ] If sender is not a registered user, ticket is created with sender email stored in metadata
- [ ] Ticket gets default type and priority (configurable by admin)
- [ ] Employee receives auto-reply confirmation with ticket number (if enabled)

**US-03:** As a technician, I can see that a ticket was created via email, so that I have context about the intake channel.

Acceptance Criteria:
- [ ] Request detail shows "Created via email" badge/indicator
- [ ] Original email metadata (from, to, date, message-id) stored in request data field
- [ ] Email attachments are saved to MinIO and linked to the request

**US-04:** As a system, the email polling must be resilient and never lose emails, so that every request is captured.

Acceptance Criteria:
- [ ] Celery beat task polls IMAP every 60 seconds for UNSEEN emails
- [ ] On successful processing, email is marked as READ (IMAP SEEN flag)
- [ ] On processing failure, email stays UNSEEN — retried next cycle
- [ ] Duplicate detection by Message-ID header (idempotent processing)
- [ ] Polling errors are logged and generate admin notification after 3 consecutive failures
- [ ] Health check endpoint reports email polling status (last successful poll timestamp)

**US-05:** As an admin, I can view an email intake log, so that I can troubleshoot failed or unprocessed emails.

Acceptance Criteria:
- [ ] Log shows: timestamp, from, subject, status (processed/failed/duplicate), ticket ID if created
- [ ] Failed emails show error reason
- [ ] Admin can manually retry a failed email

### Entities

#### EmailIntakeConfig (per company)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | FK to company |
| intake_email | str(255) | Yes | Email address to poll (e.g., support@company.com) |
| imap_host | str(255) | Yes | IMAP server host (e.g., imap.gmail.com) |
| imap_port | int | Yes | IMAP port (993 for SSL, 1143 for Mailpit) |
| auth_type | enum | Yes | oauth2 / app_password |
| credentials_encrypted | text | Yes | Encrypted OAuth2 refresh token or app password |
| is_active | bool | Yes | Enable/disable polling |
| default_request_type | str(50) | No | Default type for created tickets |
| auto_reply_enabled | bool | Yes | Send confirmation email |
| auto_reply_template | text | No | Custom auto-reply text (supports {ticket_id}, {title} placeholders) |
| last_poll_at | datetime | No | Last successful poll timestamp |
| consecutive_failures | int | Yes | Counter for alerting (default 0) |
| created_at | datetime | Yes | Record creation |
| updated_at | datetime | Yes | Last modification |

#### InboundEmail (audit log of every received email)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | FK to company |
| message_id | str(500) | Yes | Email Message-ID header (unique, for dedup) |
| from_address | str(255) | Yes | Sender email |
| to_address | str(255) | Yes | Recipient email |
| subject | str(500) | Yes | Email subject |
| body_plain | text | No | Plain text body |
| body_html | text | No | HTML body (stored for reference) |
| received_at | datetime | Yes | Email date header |
| status | enum | Yes | pending / processed / failed / duplicate |
| error_message | text | No | Error details if failed |
| request_id | ULID | No | FK to created request (if processed) |
| retry_count | int | Yes | Number of processing attempts (default 0) |
| created_at | datetime | Yes | Record creation |

### Enums

```
EmailAuthType: oauth2, app_password
InboundEmailStatus: pending, processed, failed, duplicate
```

### Use Cases

**UC-01: Poll Emails (Celery Beat Task)**
- Actor: System (Celery worker)
- Trigger: Celery beat schedule (every 60 seconds)
- Steps:
  1. Query all active EmailIntakeConfig records
  2. For each config, connect to IMAP server
  3. Search for UNSEEN emails in INBOX
  4. For each email:
     a. Check Message-ID not in InboundEmail table (dedup)
     b. Parse from, subject, body, attachments
     c. Create InboundEmail record (status=pending)
     d. Match sender to user by email (company scoped)
     e. Call CreateRequestCommand with parsed data
     f. Update InboundEmail (status=processed, request_id=...)
     g. Mark email as SEEN in IMAP
     h. Send auto-reply if enabled
  5. On error in step 4: set InboundEmail.status=failed, log error, email stays UNSEEN
  6. Update config.last_poll_at, reset consecutive_failures
  7. On connection error: increment consecutive_failures, alert after 3

**UC-02: Configure Email Intake (Admin)**
- Actor: Admin
- Steps:
  1. Admin navigates to Settings > Email Intake
  2. Enters intake email, IMAP credentials
  3. System validates IMAP connection (test connect)
  4. System encrypts and stores credentials
  5. Sets is_active = true
  6. Polling begins on next Celery beat cycle

**UC-03: View Email Intake Log (Admin)**
- Actor: Admin
- Steps:
  1. Admin navigates to Settings > Email Intake > Log
  2. System shows paginated list of InboundEmail records
  3. Admin can filter by status, date range
  4. Admin can retry failed emails (resets status to pending, increments retry_count)

### Architecture

```
[Google Workspace / Mailpit]
         │
         │ IMAP (polling every 60s)
         ▼
[Celery Beat Task: poll_email_intake]
         │
         ├── Parse email (from, subject, body, attachments)
         ├── Deduplicate by Message-ID
         ├── Match sender → User (by email)
         │
         ▼
[CreateRequestCommand] ← existing request_bc command
         │
         ├── Creates ServiceRequest
         ├── Records RequestEvent
         ├── Publishes DomainEvent
         │
         ▼
[Auto-reply email] ← via existing email sending (Celery task)
```

### API Endpoints

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /api/v1/settings/email-intake | admin | Get email intake config for company |
| PUT | /api/v1/settings/email-intake | admin | Create/update email intake config |
| POST | /api/v1/settings/email-intake/test | admin | Test IMAP connection |
| DELETE | /api/v1/settings/email-intake | admin | Delete config (stops polling) |
| GET | /api/v1/settings/email-intake/log | admin | List inbound emails (paginated) |
| POST | /api/v1/settings/email-intake/log/{id}/retry | admin | Retry failed email |
| GET | /api/v1/settings/email-intake/health | admin | Polling health status |

### Infrastructure

- **IMAP client:** `aioimaplib` or `imaplib` (stdlib) — prefer stdlib for simplicity since polling runs in Celery (sync context)
- **Credential encryption:** Fernet symmetric encryption with key from environment variable
- **Email parsing:** `email` stdlib module (parse MIME, extract text/html, attachments)
- **Attachment storage:** MinIO (existing infrastructure) via existing file upload patterns
- **Auto-reply sending:** Existing email sending infrastructure (SMTP via Mailpit in dev, configured SMTP in prod)

---

## Feature: Slack Integration (Future)

### Overview

Slack bot that listens for commands and events to create/track tickets. Uses Slack Events API with webhook delivery.

### User Stories (High-level)

- As an employee, I can create a ticket by messaging the DSM Slack bot with `/support [title]`
- As an employee, I can check ticket status with `/support-status [ticket-id]`
- As an employee, I can add a comment to a ticket from Slack
- As a technician, I receive Slack DMs when assigned a new ticket
- As an admin, I can connect Slack workspace to DSM in company settings (OAuth2 install flow)

### Technical Notes

- Slack Events API webhook receives messages → validates → creates ticket
- Slack OAuth2 app install per company (stores bot token)
- Interactive messages for status updates (Block Kit)
- Thread-based conversation tracking

---

## Feature: Microsoft Teams Integration (Future)

### Overview

Teams bot via Bot Framework for ticket creation and status tracking. Similar scope to Slack integration.

### Technical Notes

- Azure Bot Service registration
- Teams bot receives messages via Bot Framework webhook
- Adaptive Cards for rich ticket display
- Per-company Azure AD app registration

---

## Feature: Chatbot / Web Widget (Future)

### Overview

Embeddable web widget with guided ticket creation flow. Uses WebSocket for real-time conversation.

### Technical Notes

- Guided Q&A flow: type → category → description → attachments
- Integrates with E18 Knowledge Base for article suggestions (deflection)
- Integrates with E13 AI classification for auto-categorization
- Embeddable `<script>` tag for external websites
- WebSocket via existing E4 infrastructure

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| request_bc | Minor — email-created requests use existing CreateRequestCommand | Add `intake_channel` field to request metadata |
| notification_bc | Minor — new EventType for email intake errors | Add EMAIL_INTAKE_FAILED event type |
| core/celery.py | Add beat schedule for email polling task | Register poll_email_intake task |
| alembic | New migration for email_intake_config and inbound_email tables | Create migration |
| settings | New env vars for credential encryption key | Add INTAKE_ENCRYPTION_KEY |
| Docker Compose | Mailpit already present — verify IMAP port 1143 exposed | Check docker-compose.yml |
| Frontend | New admin settings pages for email intake config and log | New pages under /settings |

---

## Definition of Done (Email Intake Feature)

- [ ] EmailIntakeConfig and InboundEmail SQLAlchemy models created
- [ ] Alembic migration for new tables
- [ ] Domain entities with validation
- [ ] IMAP polling Celery beat task (every 60s)
- [ ] Email parsing (from, subject, body, attachments)
- [ ] Duplicate detection by Message-ID
- [ ] User matching by sender email
- [ ] Request creation via existing CreateRequestCommand
- [ ] Attachment upload to MinIO
- [ ] Auto-reply email (optional, configurable)
- [ ] Credential encryption (Fernet)
- [ ] Admin CRUD endpoints for EmailIntakeConfig
- [ ] IMAP connection test endpoint
- [ ] Inbound email log endpoint (paginated)
- [ ] Retry failed email endpoint
- [ ] Health check endpoint
- [ ] Frontend: Email Intake settings page
- [ ] Frontend: Inbound email log page
- [ ] i18n keys (English + Spanish)
- [ ] Unit tests for command/query handlers
- [ ] Unit tests for email parsing logic
- [ ] Integration tests for all endpoints
- [ ] Celery task tested with Mailpit IMAP

---

## Resolved Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Email delivery mechanism | IMAP polling (not webhook) | More robust — failed processing leaves email unread for retry. No data loss |
| Email provider | Google Workspace with catch-all | User already has Google Workspace. Catch-all receives all emails to any address @domain |
| Dev/test email | Mailpit (IMAP port 1143) | Already in Docker stack. No external dependencies for development |
| Polling frequency | 60 seconds | Balance between latency and API load. Google allows 2500 MB/day IMAP bandwidth |
| Authentication | OAuth2 refresh token (prod), plain (Mailpit dev) | Google requires OAuth2 for IMAP. Mailpit has no auth |
| Multi-tenant mailboxes | Deferred — single catch-all for now | If per-tenant mailboxes needed later, upgrade to receive-only SMTP (Haraka/Stalwart) with wildcard MX |
| Channels priority | Email first, then Slack, Teams, Chatbot | Email is highest value and most requested. Others can be added incrementally |

---

## Open Questions

1. **Email thread replies:** Should replies to auto-reply emails add comments to the existing ticket? (Requires In-Reply-To header tracking) — defer to follow-up feature
2. **Attachment size limit:** What's the max attachment size to accept via email? Suggest 25 MB (Gmail's limit)
3. **Spam filtering:** Should the system implement any spam detection, or rely on Google Workspace's built-in spam filter? Recommend relying on Google's filter
4. **CC handling:** If an email has CC recipients, should they be added as watchers to the ticket? — defer to follow-up feature
