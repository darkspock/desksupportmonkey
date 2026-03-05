# Epic E56 — Platform Support: AI Assistant & Support Tickets

**Date:** 2026-03-03
**Priority:** High
**Status:** Pending
**Bounded Context:** `support_bc` (new)
**Dependencies:** E51 (Contextual Help) — Done

---

## Business Alignment

### Objective

Reduce churn by giving admins and technicians a self-service and assisted support channel directly inside the product. Today, users with questions have two options: read the static contextual help panel (E51) or send an email to support@dsmcontrol.com. There is no interactive assistance, no ticket tracking, and no visibility into whether their issue is being addressed. This creates friction, delays resolution, and makes customers feel unsupported — especially during onboarding and first weeks of use.

### KPI Targets

| KPI | Target |
|-----|--------|
| Support email volume | -60% (AI resolves most questions without human intervention) |
| Average time-to-first-response | < 5 min for AI, < 4h for human tickets |
| Customer satisfaction (support) | > 4.2/5 rating on ticket close |
| Self-service resolution rate | > 70% of queries resolved by AI without escalation |
| Churn reduction | -15% in first 90 days (support-related churn) |

### Evidence

- Users currently email support@dsmcontrol.com with usage questions — no tracking, no SLA, no history
- Onboarding drop-off correlates with unresolved "how do I..." questions in first 48h
- Competitors (Freshservice, Jira SM) all have in-product support channels
- E51 contextual help is static and one-directional — users can't ask follow-up questions
- No way for the platform team to see patterns in support questions (what's confusing, what's broken)

---

## Problem Statement

### Current Situation

1. The only support channel is `support@dsmcontrol.com` — an untracked email inbox
2. The contextual help panel (E51) provides static, read-only guidance per page — no interactivity
3. Users have no way to check the status of a support request they've sent via email
4. The platform team has no dashboard to manage, prioritize, or track support requests
5. Common questions ("How do I import users?", "How do I configure departments?") are asked repeatedly with no way to deflect them to self-service

### Pain Points

| Problem | Impact |
|---------|--------|
| No AI assistance — users must read docs or email | Slow resolution, high friction during onboarding |
| No ticket tracking — email is a black hole | Users don't know if their issue was received or is being worked on |
| No support history — conversations are lost in email | Repeated context-sharing, no pattern detection |
| No prioritization — all emails look the same | Critical issues (data loss, auth problems) get same treatment as "how do I" questions |
| No metrics — can't measure support quality | No way to identify product gaps from support patterns |

### Who Is Affected

- **Admin** — primary user of support; needs help with configuration, user management, billing questions
- **Technician** — needs help with asset management, request workflows, integrations
- **Platform team (Super Admin)** — needs a dashboard to manage tickets across all companies, see patterns, respond efficiently

---

## Proposed Solution

### Overview

1. **AI Support Assistant** — a conversational AI widget (powered by Claude) embedded in the app that answers product usage questions using DSM's help content and documentation as context. Available to admins and technicians from any page.

2. **Support Ticket System** — when the AI can't resolve an issue, or when the user needs human help (bug reports, feature requests, billing issues), they can escalate to a support ticket. Tickets are tracked, have statuses, support conversation threads, and are managed by the platform team via a Super Admin dashboard.

3. **Ticket Management Dashboard** — a Super Admin view to list, filter, assign, and respond to support tickets across all companies.

4. **Satisfaction Rating** — after a ticket is resolved, the user can rate the experience.

---

## Feature 1: AI Support Assistant

### Overview

A floating chat widget (accessible from a button in the app chrome, near the existing help button) that lets admins and technicians ask product-related questions in natural language. The AI responds using DSM's help content, feature documentation, and common workflows as context.

### Rules

- Available to users with role `ADMIN` or `TECHNICIAN` only (employees use the contextual help panel)
- The AI is company-aware — the system prompt includes the user's company name, plan tier, and enabled modules so answers are contextual (e.g., "Your plan doesn't include this feature"). No user-level data (assets, requests, etc.) is passed.
- Conversation history persists within the session (cleared on logout or page refresh)
- The AI can suggest creating a support ticket if it cannot resolve the question
- The widget does not replace the E51 contextual help panel — they coexist

### User Stories

#### US-001: Ask the AI a product question

**As an** admin or technician
**I want** to ask a question about how to use DSM in natural language
**So that** I get an immediate answer without emailing support or searching docs

**Acceptance Criteria:**
- [ ] Floating chat button visible on all authenticated pages (admin/technician only)
- [ ] Clicking the button opens a chat panel (slide-in or modal)
- [ ] User can type a question and receive an AI-generated response
- [ ] AI responses reference DSM features and workflows accurately
- [ ] Conversation supports follow-up questions within the same session
- [ ] Loading state shown while AI generates a response

#### US-002: Escalate from AI to support ticket

**As an** admin or technician
**I want** to create a support ticket directly from the AI chat when my question isn't resolved
**So that** I can get human help without losing the context of my conversation

**Acceptance Criteria:**
- [ ] "Create support ticket" button/link shown in the AI chat
- [ ] Clicking it opens the ticket creation form pre-filled with the AI conversation summary
- [ ] User can edit the pre-filled content before submitting
- [ ] After ticket creation, user sees the ticket ID and a link to track it

### Technical Notes

- **Multi-provider architecture:** The AI assistant supports multiple LLM providers behind a unified interface. The backend abstracts provider-specific APIs so the frontend is provider-agnostic.
- **Supported providers:**
  - **Anthropic (Claude)** — claude-haiku-4-5 (default), claude-sonnet-4-5
  - **Groq** — llama-3.3-70b-versatile (fast inference, cost-effective), llama-4-scout-17b-16e-instruct, deepseek-r1-distill-llama-70b
- **Provider selection:** Configurable via environment variable (`AI_SUPPORT_PROVIDER=anthropic|groq`, `AI_SUPPORT_MODEL=<model-id>`). Super Admin can override per-company from the admin panel in future iterations.
- **Provider interface:** A `SupportAIProvider` abstract class with a single `chat(messages, system_prompt) -> str` method. Concrete implementations: `AnthropicProvider`, `GroqProvider`. The handler instantiates the correct provider based on config.
- **Groq specifics:** Groq uses the OpenAI-compatible chat completions API (`api.groq.com/openai/v1`). Use the official `groq` Python SDK.
- System prompt includes DSM help content from the i18n files (`help.*` keys) and feature descriptions
- No RAG needed initially — the help content is small enough to fit in the system prompt
- API calls go through the DSM backend (not directly from frontend) to protect API keys
- Rate limit: max 20 AI queries per user per hour
- **Failover:** If the primary provider fails, automatically retry with the other provider. If both fail, show "AI assistant is temporarily unavailable" and suggest creating a support ticket.

---

## Feature 2: Support Ticket System

### Overview

A support ticket system that allows admins and technicians to submit, track, and converse on support tickets directed to the platform team. Each ticket has a lifecycle (open → in_progress → resolved/closed), a priority, a category, and a conversation thread.

### Rules

- Tickets are created by admins or technicians within their company context
- Each ticket belongs to one company and one user (the creator)
- The platform team (Super Admin) can view tickets from all companies
- Ticket conversations are between the creator and the platform team — no other company users can see them
- Email notifications are sent on key events (ticket created, response received, ticket resolved). Email-only in V1 — no in-app notifications via notification_bc.
- Tickets cannot be deleted — only closed or resolved

### User Stories

#### US-003: Create a support ticket

**As an** admin or technician
**I want** to submit a support ticket to the DSM team
**So that** I can report a problem or ask for help and track the response

**Acceptance Criteria:**
- [ ] Ticket creation form accessible from a "Contact Support" button in the app
- [ ] Form fields: category (required), subject (required), description (required), priority (auto-assigned, can be overridden by Super Admin)
- [ ] Categories: `bug_report`, `feature_request`, `billing`, `how_to`, `account_access`, `other`
- [ ] Ticket receives a human-readable reference number (e.g., `SUP-001`)
- [ ] Creator receives an email confirmation with ticket details
- [ ] Ticket appears in the user's "My Support Tickets" list

#### US-004: View and track my support tickets

**As an** admin or technician
**I want** to see a list of my support tickets and their current status
**So that** I can track resolution progress without sending follow-up emails

**Acceptance Criteria:**
- [ ] "My Support Tickets" page accessible from user menu or help section
- [ ] List shows: reference number, subject, category, status, priority, created date, last update
- [ ] List sortable and filterable by status
- [ ] Clicking a ticket opens the detail view with full conversation thread
- [ ] Badge/indicator shows unread responses from the platform team

#### US-005: Respond to a support ticket (conversation)

**As an** admin/technician (creator) or Super Admin (platform team)
**I want** to add messages to a support ticket
**So that** we can have a back-and-forth conversation to resolve the issue

**Acceptance Criteria:**
- [ ] Both the creator and Super Admin can add messages to the ticket
- [ ] Messages display with author name, role badge, and timestamp
- [ ] New messages trigger email notification to the other party
- [ ] Messages support basic text (no file attachments in V1)
- [ ] Messages are ordered chronologically

#### US-006: Resolve or close a support ticket

**As a** Super Admin
**I want** to mark a ticket as resolved or close it
**So that** the customer knows their issue has been addressed

**Acceptance Criteria:**
- [ ] Super Admin can change status to `resolved` with a resolution message
- [ ] Creator receives email notification when ticket is resolved
- [ ] Creator can reopen a resolved ticket within 7 days if the issue persists
- [ ] Super Admin can close tickets that are stale (no activity for 30 days)
- [ ] Closed tickets cannot be reopened

---

## Feature 3: Super Admin Ticket Dashboard

### Overview

A dashboard for Super Admins to view, filter, and manage support tickets across all companies. This is the primary interface for the platform team to handle incoming support.

### User Stories

#### US-007: View all support tickets (Super Admin)

**As a** Super Admin
**I want** to see all support tickets across all companies
**So that** I can prioritize and respond to customer issues

**Acceptance Criteria:**
- [ ] Dashboard page at `/super-admin/support-tickets`
- [ ] Table with: reference, company name, creator email, subject, category, status, priority, created date, last update
- [ ] Filterable by: status, priority, category, company
- [ ] Searchable by subject or reference number
- [ ] Sortable by any column
- [ ] Pagination (20 per page)
- [ ] Counters: open, in_progress, resolved (summary cards at top)

#### US-008: Change ticket priority (Super Admin)

**As a** Super Admin
**I want** to change the priority of a ticket
**So that** I can escalate critical issues

**Acceptance Criteria:**
- [ ] Super Admin can change priority (low, medium, high, urgent)
- [ ] Priority change recorded in ticket event log
- [ ] Original creator is NOT notified on priority change (internal action)

---

## Feature 4: Satisfaction Rating

### Overview

After a ticket is resolved, the creator can rate the support experience.

### User Stories

#### US-009: Rate a resolved ticket

**As an** admin or technician
**I want** to rate the support I received after my ticket is resolved
**So that** the DSM team can measure and improve support quality

**Acceptance Criteria:**
- [ ] Rating prompt shown on the ticket detail page after status changes to `resolved`
- [ ] Scale: 1-5 stars + optional comment
- [ ] Rating can only be submitted once per ticket
- [ ] Rating is visible to Super Admin on the ticket detail
- [ ] Average rating shown in Super Admin dashboard summary

---

## Entities

| Entity | Description | States |
|--------|-------------|--------|
| `SupportTicket` | A support request from a company user to the platform team | `open`, `in_progress`, `waiting_on_customer`, `resolved`, `closed` |
| `TicketMessage` | A message in the ticket conversation thread | — (no state machine) |
| `TicketRating` | Customer satisfaction rating for a resolved ticket | — (no state machine) |
| `AIConversation` | An AI chat session (not persisted to DB — session-only) | — (ephemeral) |

### Entity: SupportTicket

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | ULID | Yes | Primary key |
| `reference` | String(10) | Yes | Human-readable reference (e.g., `SUP-0042`), globally unique |
| `company_id` | String | Yes | FK to company |
| `created_by` | String | Yes | FK to user (admin or technician) |
| `category` | Enum | Yes | `bug_report`, `feature_request`, `billing`, `how_to`, `account_access`, `other` |
| `subject` | String(200) | Yes | Short title |
| `description` | Text | Yes | Detailed description |
| `status` | Enum | Yes | `open`, `in_progress`, `waiting_on_customer`, `resolved`, `closed` |
| `priority` | Enum | Yes | `low`, `medium`, `high`, `urgent` |
| `resolved_at` | DateTime | No | When status changed to resolved |
| `closed_at` | DateTime | No | When status changed to closed |
| `ai_conversation_summary` | Text | No | Summary from AI chat if escalated |
| `created_at` | DateTime | Yes | Auto |
| `updated_at` | DateTime | Yes | Auto |

### Entity: TicketMessage

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | ULID | Yes | Primary key |
| `ticket_id` | String | Yes | FK to SupportTicket |
| `author_id` | String | Yes | FK to user (creator or Super Admin) |
| `body` | Text | Yes | Message content |
| `is_from_platform` | Boolean | Yes | True if author is Super Admin (for UI styling) |
| `created_at` | DateTime | Yes | Auto |

### Entity: TicketRating

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | ULID | Yes | Primary key |
| `ticket_id` | String | Yes | FK to SupportTicket, unique |
| `score` | Integer | Yes | 1-5 |
| `comment` | Text | No | Optional feedback |
| `created_at` | DateTime | Yes | Auto |

### State Machine: SupportTicket

```
[open] → in_progress → waiting_on_customer → in_progress
                      → resolved → closed
         open ← (reopen, within 7 days)
                                   closed ← (auto-close after 30 days inactive)
```

### State Transitions

| From | To | Trigger | Actor | Conditions |
|------|----|---------|-------|------------|
| `open` | `in_progress` | Super Admin responds or manually picks up | Super Admin | — |
| `in_progress` | `waiting_on_customer` | Super Admin asks a question | Super Admin | — |
| `waiting_on_customer` | `in_progress` | Customer responds | Creator | — |
| `in_progress` | `resolved` | Super Admin resolves | Super Admin | Resolution message required |
| `waiting_on_customer` | `resolved` | Super Admin resolves (e.g., no customer response) | Super Admin | Resolution message required |
| `open` | `resolved` | Super Admin resolves directly | Super Admin | Resolution message required |
| `resolved` | `open` | Customer reopens | Creator | Within 7 days of resolution |
| `resolved` | `closed` | Auto-close after 7 days with no reopen | System | 7 days since resolved_at |
| `open` / `in_progress` / `waiting_on_customer` | `closed` | Super Admin force-closes | Super Admin | — |

---

## Use Cases

### UC-001: Customer creates a support ticket

**Actor:** Admin or Technician
**Preconditions:** User is authenticated with role ADMIN or TECHNICIAN
**Postconditions:** Ticket created in `open` status, email sent to support@dsmcontrol.com

**Main Flow:**
1. User clicks "Contact Support" (from help panel, user menu, or AI chat escalation)
2. System shows ticket creation form
3. User selects category, enters subject and description
4. User submits the form
5. System creates ticket with auto-generated reference (`SUP-NNNN`), status `open`, priority `medium`
6. System sends confirmation email to user
7. System sends notification email to platform team (support@dsmcontrol.com)
8. User sees success message with ticket reference

**Alternative Flows:**
- A1: Ticket created from AI escalation — description pre-filled with AI conversation summary
- A2: User creates ticket from "My Support Tickets" page (no pre-fill)

**Error Scenarios:**
- E1: Subject or description empty — validation error shown inline
- E2: Rate limit exceeded (max 10 open tickets per company) — error message shown

### UC-002: Platform team responds to a ticket

**Actor:** Super Admin
**Preconditions:** Ticket exists in `open` or `in_progress` status
**Postconditions:** Message added, status updated, email sent to creator

**Main Flow:**
1. Super Admin opens ticket from dashboard
2. Super Admin reads the description and conversation
3. Super Admin writes a response
4. System adds message, transitions status to `in_progress` (if was `open`)
5. System sends email notification to ticket creator

### UC-003: Customer responds to a ticket

**Actor:** Admin or Technician (ticket creator)
**Preconditions:** Ticket exists in `waiting_on_customer` or `in_progress` status
**Postconditions:** Message added, status transitions if needed

**Main Flow:**
1. Creator opens ticket detail page
2. Creator writes a response
3. System adds message, transitions status to `in_progress` (if was `waiting_on_customer`)
4. System sends email notification to platform team

### UC-004: Super Admin resolves a ticket

**Actor:** Super Admin
**Preconditions:** Ticket is in `open`, `in_progress`, or `waiting_on_customer` status
**Postconditions:** Ticket status is `resolved`, email sent, rating prompt shown to creator

**Main Flow:**
1. Super Admin adds final response with resolution
2. Super Admin clicks "Resolve"
3. System sets status to `resolved`, records `resolved_at`
4. System sends email to creator: "Your ticket SUP-NNNN has been resolved"
5. Creator sees rating prompt on ticket detail page

### UC-005: Customer reopens a resolved ticket

**Actor:** Admin or Technician (ticket creator)
**Preconditions:** Ticket is in `resolved` status, less than 7 days since resolution
**Postconditions:** Ticket status returns to `open`

**Main Flow:**
1. Creator clicks "Reopen" on resolved ticket
2. Creator adds a message explaining why
3. System sets status back to `open`
4. System sends email notification to platform team

**Error Scenarios:**
- E1: More than 7 days since resolution — "This ticket can no longer be reopened. Please create a new ticket."

---

## API Endpoints

### Customer-facing (requires ADMIN or TECHNICIAN role)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/my/support-tickets` | Create a new support ticket |
| `GET` | `/api/v1/my/support-tickets` | List my support tickets (paginated, filterable) |
| `GET` | `/api/v1/my/support-tickets/{id}` | Get ticket detail with messages |
| `POST` | `/api/v1/my/support-tickets/{id}/messages` | Add a message to a ticket |
| `POST` | `/api/v1/my/support-tickets/{id}/reopen` | Reopen a resolved ticket |
| `POST` | `/api/v1/my/support-tickets/{id}/rating` | Submit satisfaction rating |

### AI Assistant (requires ADMIN or TECHNICIAN role)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/my/ai-support` | Send a message to the AI assistant, get a response |

### Super Admin (requires SUPER_ADMIN role)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/support-tickets` | List all tickets across companies (paginated, filterable) |
| `GET` | `/api/v1/support-tickets/{id}` | Get ticket detail with messages |
| `POST` | `/api/v1/support-tickets/{id}/messages` | Add a platform response |
| `PATCH` | `/api/v1/support-tickets/{id}/status` | Change ticket status (resolve, close, etc.) |
| `PATCH` | `/api/v1/support-tickets/{id}/priority` | Change ticket priority |
| `GET` | `/api/v1/support-tickets/stats` | Dashboard summary stats |

---

## Database Migration

1. Create `support_tickets` table with all SupportTicket fields
2. Create `ticket_messages` table with all TicketMessage fields
3. Create `ticket_ratings` table with all TicketRating fields
4. Create sequence or counter table for `SUP-NNNN` reference generation
5. Add indexes: `(company_id, status)`, `(created_by, status)`, `(status, priority)`, unique on `reference`

---

## i18n Keys

All UI text must be available in English and Spanish. Key areas:

- AI chat widget: title, placeholder, disclaimer, escalation prompt
- Ticket form: labels, categories, validation messages
- Ticket list: column headers, filters, empty state
- Ticket detail: status badges, conversation, rating prompt
- Super Admin dashboard: page title, summary cards, filters
- Email notifications: ticket created, response received, ticket resolved
- Toasts: ticket created success, message sent, rating submitted

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| Help panel (E51) | Add "Contact Support" link to the help panel footer | Modify `HelpPanel.tsx` |
| User menu / Header | Add "Support" link for admin/technician users | Modify `Header.tsx` |
| Navigation / Sidebar | Add "Support Tickets" link in admin/technician nav | Modify sidebar config |
| Email service (Brevo) | New email templates for ticket notifications | Create 3 templates |
| Super Admin layout | Add "Support Tickets" to Super Admin navigation | Modify super-admin nav |
| Environment config | Add `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `AI_SUPPORT_PROVIDER`, `AI_SUPPORT_MODEL` | Update `.env` and deployment config |
| Python dependencies | Add `groq` SDK package | Update `pyproject.toml` |

---

## Testing Requirements

### Unit Tests

- SupportTicket entity: create, state transitions, reopen window validation
- TicketMessage entity: create with validation
- TicketRating entity: create, score range validation
- CreateTicketCommandHandler: reference generation, email dispatch
- ResolveTicketCommandHandler: status change, resolved_at set
- ReopenTicketCommandHandler: 7-day window check
- AI support endpoint: request/response format, rate limiting
- SupportAIProvider: AnthropicProvider and GroqProvider both conform to interface
- Provider factory: correct provider instantiated based on config

### Integration Tests

- POST /my/support-tickets — create ticket, verify in DB + email sent
- GET /my/support-tickets — list with pagination and filters
- POST /my/support-tickets/{id}/messages — add message, verify notification
- POST /my/support-tickets/{id}/reopen — success within window, fail after window
- POST /my/support-tickets/{id}/rating — submit rating, reject duplicate
- Super Admin endpoints — list all, change status, change priority
- Auth: EMPLOYEE role cannot access support ticket endpoints (403)
- Auth: non-Super Admin cannot access admin endpoints (403)
- Tenant isolation: user cannot see tickets from another company

---

## Definition of Done

- [ ] AI support assistant functional (chat with AI, contextual responses)
- [ ] Support ticket CRUD (create, list, detail, messages)
- [ ] Ticket lifecycle (open → in_progress → resolved → closed)
- [ ] Ticket reopen within 7-day window
- [ ] Satisfaction rating after resolution
- [ ] Super Admin dashboard with filters and stats
- [ ] Email notifications on key events (3 templates)
- [ ] Role-based access (ADMIN/TECHNICIAN for tickets, SUPER_ADMIN for dashboard)
- [ ] Tenant isolation (users only see their company's tickets)
- [ ] Frontend: AI chat widget, ticket pages, Super Admin dashboard
- [ ] i18n: English + Spanish
- [ ] Unit tests for all domain logic
- [ ] Integration tests for all endpoints
- [ ] TypeScript compiles cleanly
- [ ] mypy + flake8 pass

---

## Time Constraints

**Deadline:** None
**Type:** None
**Priority rationale:** High — directly impacts churn during onboarding window. Should be implemented before next customer acquisition push.

---

## Resolved Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| AI providers | Multi-provider: Anthropic (Claude) + Groq (Llama/DeepSeek) | Avoid vendor lock-in; Groq offers fast inference at lower cost; Anthropic as premium fallback |
| Default provider/model | Groq `llama-3.3-70b-versatile` | Best cost/quality ratio for FAQ-style queries; switch to Claude Haiku if quality insufficient |
| Provider abstraction | `SupportAIProvider` interface with `AnthropicProvider` and `GroqProvider` implementations | Clean separation; easy to add OpenAI, Mistral, etc. later |
| AI context source | i18n help keys + static feature descriptions | Simple, no RAG infra needed; help content fits in system prompt |
| Conversation persistence | Session-only (AI), DB-persisted (tickets) | AI chat is ephemeral assistance; tickets need full audit trail |
| Reference format | `SUP-NNNN` (sequential) | Human-readable, easy to communicate via email/phone |
| File attachments | Not in V1 | Simplicity; can add in future iteration |
| Ticket visibility | Creator + Super Admin only | Privacy — other company users cannot see support conversations |
| Auto-close | 7 days after resolved, 30 days stale | Prevents ticket rot, reasonable reopen window |

---

## Open Questions

1. Should the AI assistant have access to the user's company context (company name, plan tier, enabled modules) to give more targeted answers, or stay fully generic?
2. Should there be a "knowledge base" UI (searchable articles) in addition to the AI chat, or is AI chat + contextual help sufficient?
3. Should resolved tickets count toward any SLA metric visible to customers, or is SLA tracking internal-only?
