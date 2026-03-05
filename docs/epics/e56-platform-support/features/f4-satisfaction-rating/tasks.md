# Implementation Tasks: F4 — Satisfaction Rating

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-04
**Total Tasks:** 16
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Exceptions | 1 | S |
| Domain — Entity | 1 | S |
| Infrastructure — Model | 1 | S |
| Infrastructure — Repository Interface | 1 | S |
| Infrastructure — Repository Implementation | 1 | S |
| Infrastructure — Migration | 1 | S |
| Application — Command | 1 | S |
| HTTP — Schemas | 1 | S |
| HTTP — Customer Router | 1 | S |
| HTTP — Admin Router + Stats | 1 | S |
| Frontend — Hooks | 1 | S |
| Frontend — Customer Rating UI | 1 | M |
| Frontend — Admin Rating Display | 1 | S |
| Frontend — Dashboard Stat Card | 1 | S |
| Frontend — i18n | 1 | S |
| Verification + Complete | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Add Rating Exceptions

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add two new domain exceptions for rating validation.

**File:** `src/support_bc/ticket/domain/exceptions.py`

**Implementation:**
```python
class TicketAlreadyRatedError(Exception):
    pass

class TicketRatingNotAllowedError(Exception):
    pass
```

**Acceptance Criteria:**
- [x] `TicketAlreadyRatedError` added
- [x] `TicketRatingNotAllowedError` added

---

### TASK-002: Add Rating Fields and `rate()` Method to SupportTicket

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Add three rating fields and the `rate()` domain method to the `SupportTicket` entity.

**File:** `src/support_bc/ticket/domain/entities.py`

**Implementation:**

Add imports:
```python
from src.support_bc.ticket.domain.exceptions import (
    InvalidTicketTransitionError,
    TicketAlreadyRatedError,
    TicketRatingNotAllowedError,
    TicketReopenWindowExpiredError,
)
```

Add fields to `SupportTicket` dataclass (after `updated_at`):
```python
satisfaction_rating: Optional[int] = None
satisfaction_comment: Optional[str] = None
rated_at: Optional[datetime] = None
```

Add method:
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

**Acceptance Criteria:**
- [x] 3 new fields added with `None` defaults
- [x] `rate()` validates ticket not already rated → `TicketAlreadyRatedError`
- [x] `rate()` validates status is RESOLVED or CLOSED → `TicketRatingNotAllowedError`
- [x] `rate()` validates rating 1-5 → `ValueError`
- [x] `rate()` sets `rated_at` to UTC now
- [x] `rate()` strips whitespace from comment

---

## Phase 2: Infrastructure Layer

### TASK-003: Add Rating Columns to SupportTicketModel

**Phase:** Infrastructure — Model
**Complexity:** S
**Dependencies:** None

**Description:**
Add three new columns to `SupportTicketModel`.

**File:** `src/support_bc/ticket/infrastructure/models.py`

**Implementation:**
Add after `closed_at`:
```python
satisfaction_rating: Mapped[int | None] = mapped_column(nullable=True)
satisfaction_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
rated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Acceptance Criteria:**
- [x] `satisfaction_rating` column added (Integer, nullable)
- [x] `satisfaction_comment` column added (Text, nullable)
- [x] `rated_at` column added (DateTime with TZ, nullable)

---

### TASK-004: Add `get_avg_satisfaction()` to Repository Interface

**Phase:** Infrastructure — Interface
**Complexity:** S
**Dependencies:** None

**Description:**
Add abstract method to the repository interface.

**File:** `src/support_bc/ticket/domain/repository.py`

**Implementation:**
```python
@abstractmethod
def get_avg_satisfaction(self) -> Optional[float]:
    """Average satisfaction rating across all rated tickets."""
    ...
```

**Acceptance Criteria:**
- [x] Abstract method `get_avg_satisfaction()` added returning `Optional[float]`

---

### TASK-005: Update Repository Implementation

**Phase:** Infrastructure — Repository
**Complexity:** S
**Dependencies:** TASK-003, TASK-004

**Description:**
Update `save()`, `_to_entity()`, and add `get_avg_satisfaction()`.

**File:** `src/support_bc/ticket/infrastructure/repository.py`

**Implementation:**

1. In `save()` update block, add:
```python
existing.satisfaction_rating = ticket.satisfaction_rating
existing.satisfaction_comment = ticket.satisfaction_comment
existing.rated_at = ticket.rated_at
```

2. In `_to_entity()`, add:
```python
satisfaction_rating=model.satisfaction_rating,
satisfaction_comment=model.satisfaction_comment,
rated_at=model.rated_at,
```

3. Add new method:
```python
def get_avg_satisfaction(self) -> Optional[float]:
    result = self.session.execute(
        select(func.avg(SupportTicketModel.satisfaction_rating)).where(
            SupportTicketModel.satisfaction_rating.isnot(None)
        )
    ).scalar()
    return round(float(result), 2) if result is not None else None
```

**Acceptance Criteria:**
- [x] `save()` persists 3 new fields on update
- [x] `_to_entity()` maps 3 new fields
- [x] `get_avg_satisfaction()` returns average or None when no ratings exist

---

### TASK-006: Create Alembic Migration

**Phase:** Infrastructure — Migration
**Complexity:** S
**Dependencies:** TASK-003

**Description:**
Create migration to add three columns to `support_tickets`.

**Command:** `alembic revision --autogenerate -m "add_satisfaction_rating_to_support_tickets"`

**Acceptance Criteria:**
- [x] Migration adds `satisfaction_rating` INTEGER nullable column
- [x] Migration adds `satisfaction_comment` TEXT nullable column
- [x] Migration adds `rated_at` TIMESTAMP WITH TIME ZONE nullable column
- [x] Migration runs successfully (`make db-upgrade`)

---

## Phase 3: Application Layer

### TASK-007: Create RateTicketCommand + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-005

**Description:**
Create the command and handler for rating a ticket.

**File:** `src/support_bc/ticket/application/commands/rate_ticket.py` (NEW)

**Implementation:**
```python
from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.support_bc.ticket.domain.exceptions import TicketNotFoundError
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


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
            raise TicketNotFoundError("Ticket not found")
        ticket.rate(command.rating, command.comment)
        self.ticket_repo.save(ticket)
```

**Acceptance Criteria:**
- [x] `RateTicketCommand` has `ticket_id`, `company_id`, `user_id`, `rating`, `comment`
- [x] Handler fetches ticket scoped by company_id
- [x] Handler checks `created_by == user_id` (returns 404 to prevent leaking)
- [x] Handler calls `ticket.rate()` then `save()`
- [x] CommandHandler returns `None`

---

## Phase 4: HTTP Layer

### TASK-008: Add Rating Schemas + Extend Responses

**Phase:** HTTP — Schemas
**Complexity:** S
**Dependencies:** None

**Description:**
Add `SubmitRatingRequest` and extend `TicketDetailResponse` + `TicketStatsResponse`.

**File:** `adapters/http/api/support/schemas.py`

**Implementation:**

1. Add new request schema:
```python
class SubmitRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)
```

2. Add to `TicketDetailResponse` (after `updated_at`):
```python
satisfaction_rating: Optional[int] = None
satisfaction_comment: Optional[str] = None
rated_at: Optional[datetime] = None
```

3. Add to `TicketStatsResponse`:
```python
avg_satisfaction_rating: Optional[float] = None
```

**Acceptance Criteria:**
- [x] `SubmitRatingRequest` with validated `rating` (1-5) and optional `comment` (max 2000)
- [x] `TicketDetailResponse` has 3 new rating fields
- [x] `TicketStatsResponse` has `avg_satisfaction_rating`

---

### TASK-009: Implement Rating Endpoint (Replace 501 Stub)

**Phase:** HTTP — Customer Router
**Complexity:** S
**Dependencies:** TASK-007, TASK-008

**Description:**
Replace the 501 stub at `adapters/http/api/my/support_router.py:304` with the real implementation. Also update `_to_response()` and `_to_detail_response()` to pass rating fields.

**File:** `adapters/http/api/my/support_router.py`

**Implementation:**

1. Add imports: `SubmitRatingRequest`, `RateTicketCommand`, `RateTicketCommandHandler`, `TicketAlreadyRatedError`, `TicketRatingNotAllowedError`

2. Replace the stub:
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

3. Update `_to_response()` and `_to_detail_response()` to include:
```python
satisfaction_rating=ticket.satisfaction_rating,
satisfaction_comment=ticket.satisfaction_comment,
rated_at=ticket.rated_at,
```

**Acceptance Criteria:**
- [x] 501 stub replaced with working implementation
- [x] Returns 201 on success with ticket detail response
- [x] Returns 404 for nonexistent or non-owned ticket
- [x] Returns 409 for already rated or wrong status
- [x] Returns 422 for invalid rating value
- [x] `_to_response()` includes rating fields
- [x] `_to_detail_response()` includes rating fields

---

### TASK-010: Update Admin Router + Stats Endpoint

**Phase:** HTTP — Admin Router
**Complexity:** S
**Dependencies:** TASK-005, TASK-008

**Description:**
Update admin router's `_to_response()` and `_to_detail_response()` to include rating fields. Update stats endpoint to include average satisfaction.

**File:** `adapters/http/api/support/router.py`

**Implementation:**

1. Update `_to_list_item()`, `_to_response()`, and `_to_detail_response()` — add rating fields where `TicketDetailResponse` is constructed.

2. Update `get_ticket_stats()`:
```python
avg_rating = ticket_repo.get_avg_satisfaction()
# In TicketStatsResponse constructor:
avg_satisfaction_rating=avg_rating,
```

**Acceptance Criteria:**
- [x] Admin `_to_response()` includes rating fields
- [x] Admin `_to_detail_response()` includes rating fields
- [x] Stats endpoint includes `avg_satisfaction_rating`

---

## Phase 5: Frontend

### TASK-011: Extend Hooks with Rating Support

**Phase:** Frontend — Hooks
**Complexity:** S
**Dependencies:** TASK-009

**Description:**
Add rating fields to TypeScript interfaces and create `useSubmitRating` hook.

**File:** `web/app/src/hooks/useTickets.ts`

Add to `TicketDetail` interface:
```typescript
satisfaction_rating: number | null;
satisfaction_comment: string | null;
rated_at: string | null;
```

Add new hook:
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

**File:** `web/app/src/hooks/useSupportAdmin.ts`

Add to `TicketStats` interface:
```typescript
avg_satisfaction_rating: number | null;
```

**Acceptance Criteria:**
- [x] `TicketDetail` has 3 new rating fields
- [x] `useSubmitRating` hook created with correct cache invalidation
- [x] `TicketStats` has `avg_satisfaction_rating`

---

### TASK-012: Customer Rating UI on TicketDetailPage

**Phase:** Frontend — Page
**Complexity:** M
**Dependencies:** TASK-011

**Description:**
Add interactive star rating form and read-only rating display to the customer ticket detail page.

**File:** `web/app/src/pages/support/TicketDetailPage.tsx`

**Implementation:**

Import `useSubmitRating` from hooks. Add state for `hoverRating`, `selectedRating`, `comment`.

After the ticket info card and before the conversation card, add a rating section:

1. **When `status === 'resolved'` and `satisfaction_rating === null`:** Show interactive form
   - 5 clickable star icons (filled on hover/selection)
   - Optional comment textarea
   - Submit button
   - Error display for mutation errors

2. **When `satisfaction_rating !== null`:** Show read-only display
   - Filled/empty stars showing the rating
   - Comment text if present
   - "Thank you" message

3. **Other statuses:** Don't show anything

Stars can be simple inline SVGs — `★` (filled) and `☆` (empty) rendered as buttons.

**Acceptance Criteria:**
- [x] Rating form shown when resolved and not yet rated
- [x] 1-5 clickable stars with hover preview
- [x] Optional comment textarea shown
- [x] Submit button calls `useSubmitRating`
- [x] Read-only display shown when already rated
- [x] Error handling for failed submission
- [x] Not shown on non-resolved/closed tickets
- [x] All text uses i18n keys

---

### TASK-013: Admin Read-Only Rating Display

**Phase:** Frontend — Page
**Complexity:** S
**Dependencies:** TASK-011

**Description:**
Show rating on the admin ticket detail page (read-only).

**File:** `web/app/src/pages/support/SupportTicketDetailPage.tsx`

**Implementation:**

Add a rating display section between the AI summary and the conversation. Only shown when `ticket.satisfaction_rating !== null`.

Display:
- Filled/empty stars
- Comment text if present
- `rated_at` date

Use amber/yellow accent styling for the card.

**Acceptance Criteria:**
- [x] Rating section shown when `satisfaction_rating !== null`
- [x] Shows star display + comment + date
- [x] Hidden when no rating
- [x] Read-only (no interactive elements)
- [x] All text uses i18n keys

---

### TASK-014: Add Avg Satisfaction Stat Card to Dashboard

**Phase:** Frontend — Page
**Complexity:** S
**Dependencies:** TASK-011

**Description:**
Add a 5th stat card showing average satisfaction rating.

**File:** `web/app/src/pages/support/SupportDashboardPage.tsx`

**Implementation:**

Add a stat card after the existing 4:
- Label: `t('support_dashboard.stat_satisfaction')`
- Value: `stats?.avg_satisfaction_rating?.toFixed(1)` + " / 5", or "—" if null
- Color: amber/yellow accent (`bg-amber-50 text-amber-700 border-amber-200`)
- Not clickable (no filter action for ratings)

Update the grid from `sm:grid-cols-4` to `sm:grid-cols-5`.

**Acceptance Criteria:**
- [x] 5th stat card shown with avg satisfaction
- [x] Shows "—" when no ratings exist
- [x] Grid layout updated to 5 columns
- [x] Uses amber/yellow accent styling

---

### TASK-015: Add i18n Keys

**Phase:** Frontend — i18n
**Complexity:** S
**Dependencies:** None

**Description:**
Add all rating-related i18n keys.

**Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`

**Keys:**

| Key | English | Spanish |
|-----|---------|---------|
| `support_ticket.rate_experience` | How was your support experience? | ¿Cómo fue tu experiencia de soporte? |
| `support_ticket.rating_comment_placeholder` | Share your feedback (optional)... | Comparte tu opinión (opcional)... |
| `support_ticket.submit_rating` | Submit Rating | Enviar Valoración |
| `support_ticket.rating_submitted` | Thank you for your feedback! | ¡Gracias por tu opinión! |
| `support_ticket.your_rating` | Your Rating | Tu Valoración |
| `support_dashboard.stat_satisfaction` | Avg. Satisfaction | Satisfacción Prom. |
| `support_dashboard.rating_label` | Customer Rating | Valoración del Cliente |
| `support_dashboard.no_rating` | No rating | Sin valoración |

**Acceptance Criteria:**
- [x] All 8 keys added to `en.ts`
- [x] All 8 keys added to `es.ts` with correct Spanish translations

---

## Phase 6: Verification

### TASK-016: Tests + Final Verification

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Description:**

**Unit tests** — `tests/unit/support_bc/ticket/`:
- `test_entities.py`: Add tests for `rate()` — valid rating, already rated, wrong status, out-of-range, comment stripping
- `tests/unit/support_bc/ticket/application/commands/test_rate_ticket.py` (NEW): Handler success, not found, wrong user, already rated, wrong status

**Integration tests** — `tests/integration/test_support_ticket_endpoints.py`:
- `test_submit_rating_returns_201`: Create ticket → resolve → rate → 201
- `test_duplicate_rating_returns_409`: Rate twice → 409
- `test_rating_on_open_ticket_returns_409`: Rate open ticket → 409
- `test_rating_fields_in_detail_response`: Rating fields present after submission
- `test_stats_include_avg_satisfaction`: Stats endpoint returns `avg_satisfaction_rating`

**Verification steps:**
1. `npx tsc --noEmit` — clean
2. `npm run build` — clean
3. `make test` — all pass
4. `make test-integration` — all pass
5. Mark all checkboxes in tasks.md
6. Mark F4 as Done in slicing.md

**Acceptance Criteria:**
- [x] Unit tests for `rate()` method (5 cases)
- [x] Unit tests for `RateTicketCommandHandler` (4 cases)
- [x] Integration tests for rating endpoint (4 cases)
- [x] Integration test for stats avg satisfaction
- [x] TypeScript compiles clean
- [x] Frontend builds clean
- [x] All tests pass
- [x] F4 marked as Done in slicing.md

---

## Dependency Graph

```
TASK-001 (Exceptions)
    │
    ▼
TASK-002 (Entity)
    │
    ├──► TASK-007 (Command + Handler)
    │         │
    │         ▼
    │    TASK-009 (Customer Router) ◄── TASK-008 (Schemas)
    │
TASK-003 (Model) ──► TASK-005 (Repository) ──► TASK-010 (Admin Router)
                          ▲
TASK-004 (Interface) ─────┘

TASK-006 (Migration) ── independent (just needs TASK-003)

TASK-011 (Hooks) ◄── TASK-009
    │
    ├──► TASK-012 (Customer Rating UI)
    ├──► TASK-013 (Admin Rating Display)
    └──► TASK-014 (Dashboard Stat Card)

TASK-015 (i18n) ── independent

TASK-016 (Tests + Verification) ◄── all
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-003, TASK-004, TASK-008, TASK-015
> Exceptions, model columns, repo interface, schemas, i18n — all independent

**Batch 2 (Sequential):** TASK-002, TASK-005, TASK-006
> Entity (needs exceptions) → Repository (needs model + interface) → Migration

**Batch 3:** TASK-007
> Command handler (needs entity + repository)

**Batch 4 (Parallel):** TASK-009, TASK-010
> Customer router + admin router (need handler + schemas)

**Batch 5:** TASK-011
> Frontend hooks (need backend API ready)

**Batch 6 (Parallel):** TASK-012, TASK-013, TASK-014
> All three frontend pages (need hooks)

**Batch 7:** TASK-016
> Tests + verification + mark complete
