# Epic Slicing: E56 — Platform Support: AI Assistant & Support Tickets

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Total Features:** 4
**Status:** Done

## Slicing Rationale

E56 creates a new bounded context (`support_bc`) with four distinct capabilities: an AI chat assistant, a support ticket system, a management dashboard for the support team, and a satisfaction rating mechanism. The natural slices follow the value delivery order: AI assistant (independent, highest deflection value) → ticket system (core CRUD + lifecycle) → support dashboard (depends on tickets existing) → satisfaction rating (depends on tickets being resolved).

Key decisions:
- **F1 is independently valuable** — the AI assistant deflects questions without any ticket system. Users can ask questions and get immediate answers. Even if no other feature ships, this alone reduces support email volume.
- **F2 is the core** — creates the `SupportTicket`, `TicketMessage` entities, all customer-facing CRUD endpoints, the ticket lifecycle state machine, email notifications, and the user-facing ticket pages. This is the largest feature.
- **F3 depends on F2** — the support team dashboard needs tickets to exist. It provides the management interface (list all tickets, filter, respond, change status/priority). Without F2, there's nothing to manage.
- **F4 depends on F2** — satisfaction ratings attach to resolved tickets. Without the ticket lifecycle, there's nothing to rate.

## Dependency Graph

```
F1 (AI Support Assistant)          [independent]

F2 (Support Ticket System)
 ├── F3 (Support Dashboard)        [parallel]
 └── F4 (Satisfaction Rating)      [parallel]
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 1 | AI Support Assistant | None | Users can ask product questions and get AI-powered answers instantly | M | Done |
| 2 | Support Ticket System | None | Users can create, track, and converse on support tickets with the platform team | L | Done |
| 3 | Support Dashboard | F2 | Support team can view, filter, respond to, and manage tickets across all companies | M | Done |
| 4 | Satisfaction Rating | F2 | Users can rate support quality after ticket resolution; team sees satisfaction metrics | S | Done |

## Recommended Order

1. **F1: AI Support Assistant** — independent, highest immediate impact (deflects 70%+ queries), validates provider abstraction early
2. **F2: Support Ticket System** — core CRUD, state machine, email notifications; enables F3 and F4
3. **F3: Support Dashboard** — support team management interface; can be developed in parallel with F4 after F2 ships
4. **F4: Satisfaction Rating** — lightest feature, extends ticket detail page with rating prompt; parallel with F3

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F2 → F3/F4; F1 independent)
- [x] Each feature independently deployable
- [x] Vertical slices (each includes backend domain + API + frontend UI)
- [x] Shared foundation identified (F2 provides entities for F3/F4)
- [x] No overlapping scope (entity ownership is clear)
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- **F1 depends on external AI providers** — Anthropic and Groq API availability affects the AI assistant. Failover logic (primary fails → retry with secondary → show fallback message) mitigates this. Both provider SDKs should be tested during F1.
- **F2 is the largest feature** — creates 2 new entities (SupportTicket, TicketMessage), 6 customer-facing API endpoints, state machine with 9 transitions, 3 email templates, and the full frontend (ticket list + detail pages with conversation). Could be split further (CRUD vs. conversation vs. email), but the ticket system is not useful without conversation support.
- **F2 includes Celery beat task** — auto-close for resolved tickets (7 days) and stale tickets (30 days). This introduces a background job dependency that must be tested carefully.
- **F3 requires support team auth** — the support team (who manages tickets) needs login access and a role that allows viewing all tickets across companies. This uses existing SUPER_ADMIN role infrastructure, but the naming in the UI should say "Support" not "Super Admin" for clarity.
- **F1 → F2 escalation path** — while F1 and F2 are independent for deployment, the AI chat has an "escalate to ticket" button. If F1 ships before F2, the escalation CTA should be hidden or disabled until F2 ships. F1's design should account for this.
