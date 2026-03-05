# Feature: Satisfaction Rating

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 4
**Dependencies:** F2
**Complexity:** S

## Scope

### Included

- `TicketRating` entity (1-5 score + optional comment, one per ticket)
- Rating prompt shown on ticket detail page after ticket status changes to `resolved`
- `POST /api/v1/my/support-tickets/{id}/rating` endpoint (submit rating)
- Rating visible to support team on the ticket detail view (F3's page)
- Average rating shown in support team dashboard summary (extends F3's stats endpoint)
- Database migration: `ticket_ratings` table
- i18n: rating prompt text in English and Spanish
- Rating can only be submitted once per ticket (duplicate submission returns error)

### Excluded (in other features)

- Ticket system (F2)
- Support team dashboard (F3) — F4 extends the existing dashboard with rating data
- AI assistant (F1)
- Rating update/delete (by design — one-time submission)

## User Value

When this feature is complete, users can rate the support they received after a ticket is resolved. The support team can see individual ratings and the average satisfaction score, enabling them to measure and improve support quality.

## Acceptance Criteria

- [ ] Rating prompt (1-5 stars + optional comment) shown on ticket detail page when status is `resolved`
- [ ] Rating can only be submitted once per ticket
- [ ] Duplicate submission attempt returns clear error message
- [ ] Score range validated: 1-5 only
- [ ] Rating is visible to support team on the ticket detail view
- [ ] Average rating shown in support team dashboard summary cards
- [ ] `POST /api/v1/my/support-tickets/{id}/rating` returns 201 on success
- [ ] EMPLOYEE role gets 403
- [ ] User can only rate their own tickets
- [ ] All rating UI text available in English and Spanish

## Technical Scope

### Entities (owned by this feature)

- `TicketRating` — score (1-5), optional comment, linked to SupportTicket (unique per ticket)

### Entities (used from dependencies)

- `SupportTicket` (from F2) — rating is linked to a ticket

### Key Components

**Backend — Domain:**
- `src/support_bc/ticket/domain/entities.py` — add `TicketRating` entity (extends F2's entities file)

**Backend — Infrastructure:**
- `src/support_bc/ticket/infrastructure/models.py` — add `TicketRatingModel`
- Alembic migration: `ticket_ratings` table with unique constraint on `ticket_id`

**Backend — Application:**
- `src/support_bc/ticket/application/commands/submit_rating.py` — `SubmitRatingCommand` + handler
- Extend F3's stats query to include average rating

**Backend — HTTP:**
- `POST /api/v1/my/support-tickets/{id}/rating` — endpoint implementation (route reserved in F2)

**Frontend:**
- `web/app/src/components/support/TicketRatingForm.tsx` — star rating + comment form
- Modify `TicketDetailPage.tsx` (F2) — add rating prompt when status is `resolved`
- Modify `SupportDashboardPage.tsx` (F3) — add average rating to summary cards
- Modify `SupportTicketDetailPage.tsx` (F3) — show rating on support team's view

## Notes

- F4 is the only feature that touches files owned by both F2 and F3 — but the modifications are additive (adding a component to an existing page, adding a field to an existing stats response). This is acceptable since F4 ships after both F2 and F3.
- The rating entity is simple: one score (1-5), one optional comment, linked to one ticket. No update or delete operations — this is by design to preserve data integrity.
- Future iterations may add: rating trends over time, per-category satisfaction scores, satisfaction-based alerts.
