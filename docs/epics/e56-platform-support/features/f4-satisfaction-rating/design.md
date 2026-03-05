# Solution Design: F4 — Satisfaction Rating

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-04
**Bounded Context:** `support_bc`

## Summary

Add a satisfaction rating capability to support tickets. After a ticket is resolved (or closed), the customer can submit a 1-5 star rating with an optional text comment. The rating is one-time and immutable. Rating data flows through existing detail endpoints to both customer and admin views. The admin dashboard stats endpoint is extended with an average satisfaction score.

## Architecture Decision

**Approach: Inline on SupportTicket entity** — rather than creating a separate `TicketRating` entity/table, we add three columns directly to `support_tickets`. Rationale:
- One-to-one relationship (exactly one rating per ticket, or none)
- No independent lifecycle — rating is always accessed in the context of its ticket
- Eliminates JOINs for detail views
- Follows the existing pattern where `resolved_at` and `closed_at` are inline on the ticket

The requirements mention a `TicketRating` entity but the simplest correct implementation is inline fields with a domain method `rate()` on `SupportTicket`, consistent with how `change_status()` and `change_priority()` work.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `SupportTicket` entity | `src/support_bc/ticket/domain/entities.py` | Yes | Add 3 fields + `rate()` method |
| `SupportTicketModel` | `src/support_bc/ticket/infrastructure/models.py` | Yes | Add 3 columns |
| `SupportTicketRepository` | `src/support_bc/ticket/infrastructure/repository.py` | Yes | Update `save()` + `_to_entity()`, add `get_avg_satisfaction()` |
| `SupportTicketRepositoryInterface` | `src/support_bc/ticket/domain/repository.py` | Yes | Add `get_avg_satisfaction()` abstract method |
| Rating endpoint stub | `adapters/http/api/my/support_router.py:304` | Yes | Replace 501 stub with implementation |
| `TicketDetailResponse` schema | `adapters/http/api/support/schemas.py` | Yes | Add 3 rating fields |
| `TicketStatsResponse` schema | `adapters/http/api/support/schemas.py` | Yes | Add `avg_satisfaction_rating` |
| Customer detail `_to_response()` | `adapters/http/api/my/support_router.py:69` | Yes | Pass rating fields |
| Admin detail `_to_response()` | `adapters/http/api/support/router.py:78` | Yes | Pass rating fields |
| Stats endpoint handler | `adapters/http/api/support/router.py:181` | Yes | Include avg rating in response |
| `TicketDetail` TS interface | `web/app/src/hooks/useTickets.ts:27` | Yes | Add 3 rating fields |
| Customer `TicketDetailPage` | `web/app/src/pages/support/TicketDetailPage.tsx` | Yes | Add rating form/display |
| Admin `SupportTicketDetailPage` | `web/app/src/pages/support/SupportTicketDetailPage.tsx` | Yes | Add read-only rating display |
| Admin `SupportDashboardPage` | `web/app/src/pages/support/SupportDashboardPage.tsx` | Yes | Add avg rating to stat cards |

## Implementation Plan

### 1. Domain Layer

#### Entity Modifications

| Entity | File Path | Modification |
|--------|-----------|--------------|
| `SupportTicket` | `src/support_bc/ticket/domain/entities.py` | Add `satisfaction_rating`, `satisfaction_comment`, `rated_at` fields + `rate()` method |

**New fields on `SupportTicket`:**
```python
satisfaction_rating: Optional[int] = None      # 1–5
satisfaction_comment: Optional[str] = None     # max 2000 chars
rated_at: Optional[datetime] = None
```

**New method `rate()`:**
```python
def rate(self, rating: int, comment: Optional[str] = None) -> None:
    if self.satisfaction_rating is not None:
        raise TicketAlreadyRatedError("This ticket has already been rated")
    if self.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
        raise TicketRatingNotAllowedError(
            "Rating is only allowed on resolved or closed tickets"
        )
    if not (1 <= rating <= 5):
        raise ValueError("Rating must be between 1 and 5")
    self.satisfaction_rating = rating
    self.satisfaction_comment = comment.strip() if comment else None
    self.rated_at = datetime.now(timezone.utc)
```

#### New Exceptions

| Exception | File Path | Description |
|-----------|-----------|-------------|
| `TicketAlreadyRatedError` | `src/support_bc/ticket/domain/exceptions.py` | Duplicate rating attempt |
| `TicketRatingNotAllowedError` | `src/support_bc/ticket/domain/exceptions.py` | Rating on wrong status |

### 2. Infrastructure Layer

#### Model Modifications

| Model | File Path | Modification |
|-------|-----------|--------------|
| `SupportTicketModel` | `src/support_bc/ticket/infrastructure/models.py` | Add 3 columns |

**New columns:**
```python
satisfaction_rating: Mapped[int | None] = mapped_column(nullable=True)
satisfaction_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
rated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

#### Repository Modifications

| Method | File Path | Modification |
|--------|-----------|--------------|
| `save()` | `src/support_bc/ticket/infrastructure/repository.py` | Persist 3 new fields on update |
| `_to_entity()` | `src/support_bc/ticket/infrastructure/repository.py` | Map 3 new fields |
| `get_avg_satisfaction()` | `src/support_bc/ticket/infrastructure/repository.py` | NEW — return average rating |

**`save()` update block addition:**
```python
existing.satisfaction_rating = ticket.satisfaction_rating
existing.satisfaction_comment = ticket.satisfaction_comment
existing.rated_at = ticket.rated_at
```

**`_to_entity()` addition:**
```python
satisfaction_rating=model.satisfaction_rating,
satisfaction_comment=model.satisfaction_comment,
rated_at=model.rated_at,
```

**New method `get_avg_satisfaction()`:**
```python
def get_avg_satisfaction(self) -> Optional[float]:
    result = self.session.execute(
        select(func.avg(SupportTicketModel.satisfaction_rating)).where(
            SupportTicketModel.satisfaction_rating.isnot(None)
        )
    ).scalar()
    return round(float(result), 2) if result is not None else None
```

#### Repository Interface Addition

| Method | File Path | Description |
|--------|-----------|-------------|
| `get_avg_satisfaction()` | `src/support_bc/ticket/domain/repository.py` | Abstract method returning `Optional[float]` |

#### Migration

| Migration | Description |
|-----------|-------------|
| `add_satisfaction_rating_to_support_tickets` | ALTER TABLE `support_tickets` ADD 3 columns |

```sql
ALTER TABLE support_tickets ADD COLUMN satisfaction_rating INTEGER;
ALTER TABLE support_tickets ADD COLUMN satisfaction_comment TEXT;
ALTER TABLE support_tickets ADD COLUMN rated_at TIMESTAMP WITH TIME ZONE;
```

### 3. Application Layer

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| `RateTicketCommand` | `RateTicketCommandHandler` | Submits a rating on a resolved/closed ticket |

**File:** `src/support_bc/ticket/application/commands/rate_ticket.py`

```python
@dataclass
class RateTicketCommand(Command):
    ticket_id: str
    company_id: str
    user_id: str
    rating: int
    comment: Optional[str] = None

class RateTicketCommandHandler(CommandHandler[RateTicketCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: RateTicketCommand) -> None:
        ticket = self.ticket_repo.find_by_id(command.ticket_id, command.company_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        if ticket.created_by != command.user_id:
            raise TicketNotFoundError("Ticket not found")  # 404 for auth
        ticket.rate(command.rating, command.comment)
        self.ticket_repo.save(ticket)
```

Note: The handler checks `ticket.created_by != command.user_id` to enforce "only the creator can rate." Returns 404 (not 403) to avoid leaking ticket existence.

### 4. HTTP Layer

#### Schemas

| Schema | File Path | Modification |
|--------|-----------|--------------|
| `SubmitRatingRequest` | `adapters/http/api/support/schemas.py` | NEW request schema |
| `TicketDetailResponse` | `adapters/http/api/support/schemas.py` | Add 3 rating fields |
| `TicketStatsResponse` | `adapters/http/api/support/schemas.py` | Add `avg_satisfaction_rating` |

**New schema:**
```python
class SubmitRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)
```

**`TicketDetailResponse` additions:**
```python
satisfaction_rating: Optional[int] = None
satisfaction_comment: Optional[str] = None
rated_at: Optional[datetime] = None
```

**`TicketStatsResponse` addition:**
```python
avg_satisfaction_rating: Optional[float] = None
```

#### Endpoints

| Method | Route | Action | Request | Response |
|--------|-------|--------|---------|----------|
| POST | `/api/v1/my/support-tickets/{id}/rating` | Submit rating | `SubmitRatingRequest` | `TicketDetailResponse` |

**Implementation** — replace the 501 stub in `adapters/http/api/my/support_router.py`:
```python
@router.post("/{ticket_id}/rating", status_code=status.HTTP_201_CREATED)
def submit_rating(
    ticket_id: str,
    body: SubmitRatingRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = RateTicketCommandHandler(ticket_repo=ticket_repo)
    try:
        handler.handle(
            RateTicketCommand(
                ticket_id=ticket_id,
                company_id=current_user.company_id,
                user_id=current_user.id,
                rating=body.rating,
                comment=body.comment,
            )
        )
    except TicketNotFoundError:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except TicketAlreadyRatedError:
        raise HTTPException(status_code=409, detail="This ticket has already been rated")
    except TicketRatingNotAllowedError:
        raise HTTPException(status_code=409, detail="Rating is only allowed on resolved or closed tickets")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()

    ticket = ticket_repo.find_by_id(ticket_id, current_user.company_id)
    return {"data": _to_response(ticket)}
```

#### Collateral HTTP Changes

**Customer router `_to_response()` and `_to_detail_response()`** — add rating fields:
```python
satisfaction_rating=ticket.satisfaction_rating,
satisfaction_comment=ticket.satisfaction_comment,
rated_at=ticket.rated_at,
```

**Admin router `_to_response()` and `_to_detail_response()`** — same additions.

**Admin stats endpoint** — include avg rating:
```python
avg_rating = ticket_repo.get_avg_satisfaction()
# Add to response:
avg_satisfaction_rating=avg_rating,
```

### 5. Frontend

#### Hook Modifications

**`web/app/src/hooks/useTickets.ts`:**
- Add to `TicketDetail` interface: `satisfaction_rating: number | null`, `satisfaction_comment: string | null`, `rated_at: string | null`
- Add new hook:
```typescript
export function useSubmitRating(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { rating: number; comment?: string }) => {
      const { data } = await api.post(`/my/support-tickets/${ticketId}/rating`, body);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['support-ticket', ticketId] });
      void queryClient.invalidateQueries({ queryKey: ['my-support-tickets'] });
    },
  });
}
```

**`web/app/src/hooks/useSupportAdmin.ts`:**
- Add `avg_satisfaction_rating: number | null` to `TicketStats` interface

#### Customer Ticket Detail Page

**`web/app/src/pages/support/TicketDetailPage.tsx`:**

Add rating UI after the ticket info card, before the conversation:
- When `status === 'resolved'` and `satisfaction_rating === null`: show interactive star rating form (1-5 clickable stars + optional comment textarea + submit button)
- When `satisfaction_rating !== null`: show read-only display of submitted rating (filled stars + comment if present + rated_at date)
- Not shown on other statuses

The star component is simple inline JSX — no need for a separate file given the small scope.

#### Admin Ticket Detail Page

**`web/app/src/pages/support/SupportTicketDetailPage.tsx`:**

Add read-only rating display section (between AI summary and conversation):
- Only shown when `ticket.satisfaction_rating !== null`
- Shows filled/empty stars, comment (if present), rated_at date
- Card with amber/yellow accent styling

#### Admin Dashboard Page

**`web/app/src/pages/support/SupportDashboardPage.tsx`:**

Add a 5th stat card for average satisfaction:
- Label: "Avg. Satisfaction"
- Value: `stats.avg_satisfaction_rating` formatted to 1 decimal + "/ 5"
- Show "—" when null (no ratings yet)
- Color: amber/yellow accent

#### i18n Keys

| Key | English | Spanish |
|-----|---------|---------|
| `support_ticket.rate_experience` | How was your support experience? | ¿Cómo fue tu experiencia de soporte? |
| `support_ticket.rating_comment_placeholder` | Share your feedback (optional)... | Comparte tu opinión (opcional)... |
| `support_ticket.submit_rating` | Submit Rating | Enviar Valoración |
| `support_ticket.rating_submitted` | Thank you for your feedback! | ¡Gracias por tu opinión! |
| `support_ticket.your_rating` | Your Rating | Tu Valoración |
| `support_ticket.rating_already_submitted` | You have already rated this ticket | Ya has valorado este ticket |
| `support_dashboard.stat_satisfaction` | Avg. Satisfaction | Satisfacción Prom. |
| `support_dashboard.rating_label` | Customer Rating | Valoración del Cliente |
| `support_dashboard.no_rating` | No rating | Sin valoración |

## Database Schema

```sql
-- Migration: add_satisfaction_rating_to_support_tickets
ALTER TABLE support_tickets ADD COLUMN satisfaction_rating INTEGER;
ALTER TABLE support_tickets ADD COLUMN satisfaction_comment TEXT;
ALTER TABLE support_tickets ADD COLUMN rated_at TIMESTAMP WITH TIME ZONE;
```

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | `SupportTicket.rate()` — valid rating, already rated, wrong status, out-of-range | High |
| Unit | `RateTicketCommandHandler` — success, not found, wrong user, already rated | High |
| Integration | `POST /api/v1/my/support-tickets/{id}/rating` — 201 success | High |
| Integration | Rating on non-resolved ticket — 409 | High |
| Integration | Duplicate rating — 409 | High |
| Integration | Rating not owned ticket — 404 | High |
| Integration | Rating fields in detail response | Medium |
| Integration | Avg rating in stats response | Medium |

## Implementation Order

1. Domain: Add exceptions (`TicketAlreadyRatedError`, `TicketRatingNotAllowedError`)
2. Domain: Add fields + `rate()` to `SupportTicket` entity
3. Infrastructure: Add columns to `SupportTicketModel`
4. Infrastructure: Update repository (`save()`, `_to_entity()`, `get_avg_satisfaction()`)
5. Infrastructure: Add `get_avg_satisfaction()` to repository interface
6. Infrastructure: Alembic migration
7. Application: `RateTicketCommand` + handler
8. HTTP: `SubmitRatingRequest` schema + extend `TicketDetailResponse` + `TicketStatsResponse`
9. HTTP: Implement rating endpoint (replace 501 stub)
10. HTTP: Update `_to_response()` in both routers + stats endpoint
11. Frontend: Extend hooks (TS interface + `useSubmitRating`)
12. Frontend: Customer rating UI on `TicketDetailPage`
13. Frontend: Admin read-only rating on `SupportTicketDetailPage`
14. Frontend: Avg satisfaction stat card on `SupportDashboardPage`
15. Frontend: i18n keys (en + es)
16. Tests: Unit + integration
17. Verification: Build + test suite

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Migration on large table | Low | Low | Simple ALTER ADD COLUMN — no rewrite, nullable columns |
| Rating on auto-closed tickets | Low | Low | `rate()` accepts both RESOLVED and CLOSED statuses |
