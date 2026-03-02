# Epic E23 — Multi-channel Intake

**Date:** 2026-02-28
**Priority:** Medium
**Status:** Pending
**Bounded Context:** `intake_bc` (new)
**Dependencies:** E3 (Service Requests) — Done, E4 (Real-time & Notifications) — Done

---

## Business Alignment

### Objective

Enable ticket creation from external channels (email, Slack, Teams, Jira, Salesforce, chatbot) so employees can submit requests without logging into the web application — and sync with existing Jira projects or Salesforce Service Cloud — increasing adoption and reducing friction.

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
- Many companies already use Jira for project management and want their IT requests visible alongside development work
- Enterprise customers use Salesforce Service Cloud as their CRM/support platform and need IT asset requests to flow into their existing Salesforce workflows

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
| No Jira integration | Teams using Jira for project management can't see IT requests in their boards |
| No Salesforce integration | Companies using Salesforce Service Cloud must duplicate cases manually between systems |
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
| Jira (Cloud) | Jira REST API + webhooks (bidirectional sync) | Medium |
| Salesforce Service Cloud | Salesforce REST API + Platform Events (bidirectional sync) | Medium |
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

## Feature: Jira Cloud Sync (Future)

### Overview

Bidirectional sync between DSM Control and Jira Cloud. Issues created in a configured Jira project are imported as service requests in DSM Control. Requests created in DSM can optionally be pushed to Jira. Status changes and comments sync in both directions, so teams using Jira for project management have full visibility of IT support activity.

Unlike email or Slack (unidirectional intake), Jira sync is **bidirectional**: DSM → Jira and Jira → DSM.

### User Stories (High-level)

- As an admin, I can connect a Jira Cloud instance to DSM in company settings via OAuth 2.0 (3LO), so that issues can flow between both systems
- As an admin, I can configure which Jira project(s) sync with DSM, and map Jira issue types to DSM request types
- As an admin, I can choose sync direction: Jira→DSM only (intake), DSM→Jira only (push), or bidirectional
- As an employee, when I create a Jira issue in a synced project, a corresponding service request is created in DSM automatically
- As a technician, when I update request status in DSM, the linked Jira issue status transitions accordingly (if bidirectional enabled)
- As a technician, I can see that a request was created via Jira sync, with a direct link to the original Jira issue
- As a system, comments added to a Jira issue are synced as request comments in DSM (and vice versa if bidirectional)

### Entities

#### JiraIntakeConfig (per company)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | FK to company |
| jira_site_url | str(255) | Yes | Jira Cloud site URL (e.g., https://acme.atlassian.net) |
| cloud_id | str(100) | Yes | Jira Cloud ID (from accessible-resources API) |
| access_token_encrypted | text | Yes | Encrypted OAuth 2.0 access token |
| refresh_token_encrypted | text | Yes | Encrypted OAuth 2.0 refresh token |
| token_expires_at | datetime | Yes | Access token expiry |
| sync_direction | enum | Yes | jira_to_dsm / dsm_to_jira / bidirectional |
| is_active | bool | Yes | Enable/disable sync |
| last_sync_at | datetime | No | Last successful sync timestamp |
| consecutive_failures | int | Yes | Counter for alerting (default 0) |
| created_at | datetime | Yes | Record creation |
| updated_at | datetime | Yes | Last modification |

#### JiraProjectMapping (which Jira projects sync)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| config_id | ULID | Yes | FK to JiraIntakeConfig |
| jira_project_key | str(20) | Yes | Jira project key (e.g., "IT", "SUPPORT") |
| jira_project_name | str(255) | Yes | Display name |
| default_request_type | str(50) | No | DSM request type for imported issues |
| jira_issue_type_filter | text | No | JSON array of Jira issue type IDs to sync (null = all) |
| is_active | bool | Yes | Enable/disable this project mapping |

#### JiraSyncLog (audit log of sync events)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | FK to company |
| direction | enum | Yes | jira_to_dsm / dsm_to_jira |
| jira_issue_key | str(50) | Yes | e.g., "IT-123" |
| jira_issue_id | str(50) | Yes | Jira issue numeric ID |
| request_id | ULID | No | FK to DSM request (if linked) |
| event_type | enum | Yes | issue_created / issue_updated / comment_synced / status_changed / sync_failed |
| status | enum | Yes | processed / failed / skipped |
| error_message | text | No | Error details if failed |
| payload_hash | str(64) | No | SHA-256 hash of webhook payload (for dedup) |
| created_at | datetime | Yes | Record creation |

### Enums

```
JiraSyncDirection: jira_to_dsm, dsm_to_jira, bidirectional
JiraSyncEventType: issue_created, issue_updated, comment_synced, status_changed, sync_failed
JiraSyncLogStatus: processed, failed, skipped
```

### Technical Notes

- **Authentication:** Jira Cloud OAuth 2.0 (3LO) — admin authorizes DSM as an Atlassian app. Tokens stored encrypted (Fernet, same key as email intake)
- **Jira → DSM (intake):** Jira webhooks (project-scoped) fire on issue creation/update/comment. DSM receives via a dedicated webhook endpoint, validates signature, and processes
- **DSM → Jira (push):** Domain events from `request_bc` trigger a Celery task that calls Jira REST API v3 to create/update issues
- **Status mapping:** Configurable mapping between Jira workflow statuses and DSM request statuses. Default: "To Do"→open, "In Progress"→in_progress, "Done"→resolved
- **Deduplication:** Webhook payload hash + jira_issue_id + event_type prevent duplicate processing
- **Rate limiting:** Jira Cloud API rate limit is ~100 req/s per app — Celery task with rate limiter for outbound calls
- **Atlassian Connect / Forge:** Register DSM as an Atlassian Connect app (or Forge app) for marketplace listing and easy install. Initial implementation uses OAuth 2.0 (3LO) with manual webhook registration; Forge migration deferred

### API Endpoints

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /api/v1/settings/jira-intake | admin | Get Jira sync config |
| POST | /api/v1/settings/jira-intake/connect | admin | Start OAuth 2.0 flow (returns redirect URL) |
| GET | /api/v1/settings/jira-intake/callback | system | OAuth 2.0 callback (stores tokens) |
| PUT | /api/v1/settings/jira-intake | admin | Update config (sync direction, active) |
| DELETE | /api/v1/settings/jira-intake | admin | Disconnect Jira (revoke tokens, remove webhooks) |
| GET | /api/v1/settings/jira-intake/projects | admin | List available Jira projects (from connected instance) |
| POST | /api/v1/settings/jira-intake/projects | admin | Create/update project mapping |
| DELETE | /api/v1/settings/jira-intake/projects/{id} | admin | Remove project mapping |
| GET | /api/v1/settings/jira-intake/log | admin | List sync log (paginated) |
| POST | /api/v1/settings/jira-intake/log/{id}/retry | admin | Retry failed sync event |
| POST | /api/v1/webhooks/jira/{company_id} | system | Jira webhook receiver (no auth — signature validated) |

### Architecture

```
[Jira Cloud]
     │
     ├── Webhook (issue_created, issue_updated, comment_created)
     │         │
     │         ▼
     │   [POST /api/v1/webhooks/jira/{company_id}]
     │         │
     │         ├── Validate webhook (Jira signature or shared secret)
     │         ├── Deduplicate by payload hash
     │         ├── Map Jira issue → CreateRequestCommand / UpdateRequestCommand
     │         │
     │         ▼
     │   [request_bc command handlers] ← existing
     │
     └── REST API v3 (create/update issue)
               ▲
               │
         [Celery task: sync_request_to_jira]
               │
               ├── Triggered by domain event (RequestCreated, RequestStatusChanged, CommentAdded)
               ├── Only fires if company has active Jira config with dsm_to_jira or bidirectional
               ├── Maps DSM request → Jira issue fields
               └── Logs result in JiraSyncLog
```

---

## Feature: Salesforce Service Cloud Sync (Future)

### Overview

Bidirectional sync between DSM Control and Salesforce Service Cloud. Cases created in Salesforce are imported as service requests in DSM Control. Requests created in DSM can optionally be pushed to Salesforce as Cases. Status changes and comments sync in both directions, so organizations using Salesforce as their CRM/support backbone have unified visibility across IT operations and customer support.

Like Jira sync, Salesforce sync is **bidirectional**: DSM → Salesforce and Salesforce → DSM.

### User Stories (High-level)

- As an admin, I can connect a Salesforce org to DSM in company settings via OAuth 2.0 (Web Server Flow), so that cases can flow between both systems
- As an admin, I can configure which Salesforce Record Types or Case origins sync with DSM, and map them to DSM request types
- As an admin, I can choose sync direction: SF→DSM only (intake), DSM→SF only (push), or bidirectional
- As an admin, I can map Salesforce Case statuses to DSM request statuses (e.g., "New"→open, "Working"→in_progress, "Closed"→resolved)
- As an employee, when a Case is created in Salesforce matching the configured criteria, a corresponding service request is created in DSM automatically
- As a technician, when I update request status in DSM, the linked Salesforce Case status transitions accordingly (if bidirectional enabled)
- As a technician, I can see that a request was created via Salesforce sync, with a direct link to the original Case in Salesforce
- As a system, Case comments (CaseComment / FeedItem) added in Salesforce are synced as request comments in DSM (and vice versa if bidirectional)

### Entities

#### SalesforceIntakeConfig (per company)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | FK to company |
| instance_url | str(255) | Yes | Salesforce org URL (e.g., https://acme.my.salesforce.com) |
| org_id | str(18) | Yes | Salesforce Organization ID |
| access_token_encrypted | text | Yes | Encrypted OAuth 2.0 access token |
| refresh_token_encrypted | text | Yes | Encrypted OAuth 2.0 refresh token |
| token_expires_at | datetime | Yes | Access token expiry |
| sync_direction | enum | Yes | sf_to_dsm / dsm_to_sf / bidirectional |
| case_origin_filter | text | No | JSON array of Case Origin values to sync (null = all) |
| case_record_type_filter | text | No | JSON array of Record Type IDs to sync (null = all) |
| default_request_type | str(50) | No | DSM request type for imported Cases |
| is_active | bool | Yes | Enable/disable sync |
| last_sync_at | datetime | No | Last successful sync timestamp |
| consecutive_failures | int | Yes | Counter for alerting (default 0) |
| created_at | datetime | Yes | Record creation |
| updated_at | datetime | Yes | Last modification |

#### SalesforceStatusMapping (configurable status mapping)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| config_id | ULID | Yes | FK to SalesforceIntakeConfig |
| sf_status | str(100) | Yes | Salesforce Case status value (e.g., "New", "Working", "Escalated") |
| dsm_status | str(50) | Yes | Corresponding DSM request status |
| direction | enum | Yes | sf_to_dsm / dsm_to_sf / both |

#### SalesforceSyncLog (audit log of sync events)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | FK to company |
| direction | enum | Yes | sf_to_dsm / dsm_to_sf |
| sf_case_id | str(18) | Yes | Salesforce Case ID (15 or 18 char) |
| sf_case_number | str(20) | No | Salesforce Case Number (human-readable) |
| request_id | ULID | No | FK to DSM request (if linked) |
| event_type | enum | Yes | case_created / case_updated / comment_synced / status_changed / sync_failed |
| status | enum | Yes | processed / failed / skipped |
| error_message | text | No | Error details if failed |
| replay_id | str(50) | No | Platform Event replay ID (for dedup and resume) |
| created_at | datetime | Yes | Record creation |

### Enums

```
SalesforceSyncDirection: sf_to_dsm, dsm_to_sf, bidirectional
SalesforceSyncEventType: case_created, case_updated, comment_synced, status_changed, sync_failed
SalesforceSyncLogStatus: processed, failed, skipped
```

### Technical Notes

- **Authentication:** Salesforce OAuth 2.0 Web Server Flow — admin authorizes DSM as a Connected App. Tokens stored encrypted (Fernet, same key as other integrations)
- **SF → DSM (intake):** Two options evaluated:
  - **Platform Events (preferred):** Define a custom Platform Event in Salesforce (e.g., `DSM_Case_Event__e`) published by a Flow/Trigger on Case creation/update. DSM subscribes via CometD long-polling (Bayeux protocol) or polls the event bus. Replay ID ensures no missed events on reconnection
  - **Outbound Messages (alternative):** Workflow Rule → Outbound Message sends SOAP XML to DSM webhook. Simpler but less flexible and being deprecated in favor of Platform Events
  - **Decision:** Use Platform Events with CometD subscription via a Celery long-running task. Fallback to polling `/services/data/vXX.0/sobjects/Case` with `LastModifiedDate` filter if Platform Events are not available in the customer's Salesforce edition
- **DSM → SF (push):** Domain events from `request_bc` trigger a Celery task that calls Salesforce REST API to create/update Cases via `/services/data/vXX.0/sobjects/Case`
- **Status mapping:** Fully configurable per company via `SalesforceStatusMapping` table. Default: "New"→open, "Working"→in_progress, "Escalated"→in_progress, "Closed"→resolved
- **Deduplication:** Platform Event replay ID + sf_case_id + event_type prevent duplicate processing
- **Rate limiting:** Salesforce API daily limits vary by edition (Enterprise: 100k/day, Unlimited: 500k/day). Celery task tracks API call count and backs off when approaching limits
- **Salesforce editions:** Platform Events require Enterprise Edition or higher. Integration should degrade gracefully for Professional Edition (polling fallback)
- **Connected App:** DSM registered as a Salesforce Connected App with `api`, `refresh_token`, and `offline_access` scopes

### API Endpoints

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /api/v1/settings/salesforce-intake | admin | Get Salesforce sync config |
| POST | /api/v1/settings/salesforce-intake/connect | admin | Start OAuth 2.0 flow (returns redirect URL) |
| GET | /api/v1/settings/salesforce-intake/callback | system | OAuth 2.0 callback (stores tokens) |
| PUT | /api/v1/settings/salesforce-intake | admin | Update config (sync direction, filters, active) |
| DELETE | /api/v1/settings/salesforce-intake | admin | Disconnect Salesforce (revoke tokens) |
| GET | /api/v1/settings/salesforce-intake/status-mapping | admin | Get status mappings |
| PUT | /api/v1/settings/salesforce-intake/status-mapping | admin | Update status mappings (bulk replace) |
| POST | /api/v1/settings/salesforce-intake/test | admin | Test Salesforce connection (verify token, query org info) |
| GET | /api/v1/settings/salesforce-intake/metadata | admin | Fetch available Case Record Types, Origins, and Statuses from connected org |
| GET | /api/v1/settings/salesforce-intake/log | admin | List sync log (paginated) |
| POST | /api/v1/settings/salesforce-intake/log/{id}/retry | admin | Retry failed sync event |

### Architecture

```
[Salesforce Service Cloud]
     │
     ├── Platform Event (DSM_Case_Event__e)
     │         │
     │         ▼
     │   [Celery long-running task: subscribe_salesforce_events]
     │         │  (CometD / Bayeux long-polling on /event/DSM_Case_Event__e)
     │         │
     │         ├── Deduplicate by replay ID
     │         ├── Fetch full Case data via REST API
     │         ├── Map Case → CreateRequestCommand / UpdateRequestCommand
     │         │
     │         ▼
     │   [request_bc command handlers] ← existing
     │
     └── REST API vXX.0 (create/update Case)
               ▲
               │
         [Celery task: sync_request_to_salesforce]
               │
               ├── Triggered by domain event (RequestCreated, RequestStatusChanged, CommentAdded)
               ├── Only fires if company has active SF config with dsm_to_sf or bidirectional
               ├── Maps DSM request → Salesforce Case fields
               ├── Creates/updates CaseComment for comment sync
               └── Logs result in SalesforceSyncLog
```

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
| settings | Jira OAuth 2.0 app credentials | Add JIRA_CLIENT_ID, JIRA_CLIENT_SECRET env vars |
| settings | Salesforce Connected App credentials | Add SF_CLIENT_ID, SF_CLIENT_SECRET env vars |
| Docker Compose | Mailpit already present — verify IMAP port 1143 exposed | Check docker-compose.yml |
| Frontend | New admin settings pages for email intake config and log | New pages under /settings |
| Frontend | New admin settings page for Jira sync config, project mappings, and sync log | New pages under /settings |
| Frontend | New admin settings page for Salesforce sync config, status mappings, and sync log | New pages under /settings |

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
| Channels priority | Email first, then Slack, Jira, Salesforce, Teams, Chatbot | Email is highest value and most requested. Jira, Salesforce, and Slack are medium priority. Others added incrementally |
| Jira sync approach | OAuth 2.0 (3LO) + webhooks + REST API | Standard Atlassian integration pattern. Webhook for inbound, REST API for outbound. Forge migration deferred |
| Jira sync direction | Configurable per company (intake-only, push-only, or bidirectional) | Different companies have different needs — some only want Jira→DSM, others want full sync |
| Salesforce sync approach | OAuth 2.0 Web Server Flow + Platform Events + REST API | Standard Salesforce integration pattern. Platform Events for inbound (CometD), REST API for outbound |
| Salesforce sync direction | Configurable per company (intake-only, push-only, or bidirectional) | Same flexibility as Jira — some only want SF→DSM, others want full sync |
| Salesforce inbound mechanism | Platform Events with CometD (preferred), polling fallback for lower editions | Platform Events provide near-real-time delivery with replay for resilience. Polling fallback for Professional Edition |

---

## Open Questions

1. **Email thread replies:** Should replies to auto-reply emails add comments to the existing ticket? (Requires In-Reply-To header tracking) — defer to follow-up feature
2. **Attachment size limit:** What's the max attachment size to accept via email? Suggest 25 MB (Gmail's limit)
3. **Spam filtering:** Should the system implement any spam detection, or rely on Google Workspace's built-in spam filter? Recommend relying on Google's filter
4. **CC handling:** If an email has CC recipients, should they be added as watchers to the ticket? — defer to follow-up feature
5. **Jira custom fields:** Should the sync map Jira custom fields to DSM custom fields (E30)? — defer until E30 is implemented
6. **Jira Server/Data Center:** Initial implementation targets Jira Cloud only. Jira Server/Data Center support (different auth, on-premise webhooks) deferred
7. **Jira attachment sync:** Should attachments on Jira issues be downloaded and stored in MinIO? Suggest yes, with same size limit as email (25 MB)
8. **Conflict resolution:** If a request is updated in both DSM and Jira simultaneously, which wins? Suggest last-write-wins with sync log entry for audit
9. **Salesforce edition requirements:** Platform Events require Enterprise Edition or higher. Should DSM support Professional Edition with a polling fallback, or require Enterprise+?
10. **Salesforce custom objects:** Some orgs use custom objects instead of standard Case. Should DSM support mapping to custom objects? — defer to follow-up feature
11. **Salesforce Knowledge sync:** Should Salesforce Knowledge articles sync with DSM knowledge base (E18)? — defer until E18 is implemented
12. **Salesforce sandbox testing:** Integration tests should run against a Salesforce Developer Edition org (free). Document setup steps for contributors
