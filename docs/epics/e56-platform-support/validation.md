# Requirement Validation Report

**Document:** E56 — Platform Support: AI Assistant & Support Tickets
**Date:** 2026-03-03
**Type:** Epic (FULL validation)
**Status:** Valid — minor gaps flagged below

## Summary

Strong, well-structured epic with clear business alignment, comprehensive entity definitions, thorough state machine, and detailed use cases. The multi-provider AI architecture is well thought out. A few gaps around CRUD completeness, inverse operations, and edge cases are flagged below — none are blockers.

---

## Business Alignment Assessment

**Primary Objective:** Churn reduction
**Contribution:** Clear — directly ties support friction to onboarding drop-off and churn
**KPIs Defined:** Yes — 5 measurable targets
**Justification Type:** Objective with qualitative data (no specific customer counts or ticket IDs, but product-stage context makes this acceptable for a pre-revenue/early-stage product)

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Partial | KPI targets are specific (-60%, < 5 min, > 4.2/5, > 70%, -15%) but evidence section lacks concrete counts (e.g., "X emails/month") |
| Evidence sources | Partial | References email inbox and onboarding drop-off but no ticket IDs or customer names (acceptable — no ticketing system exists yet) |
| Revenue impact | Indirect | Churn reduction → revenue retention. No direct revenue number, but valid for current stage |
| Customer names/tickets | No | No existing tracking to reference — this is the gap the epic solves |

**RED FLAGS:**
- [ ] ~~Subjective justification detected~~ — No, rationale is grounded in product gaps
- [ ] ~~Missing revenue/cost impact~~ — Indirect but present (churn reduction)
- [ ] ~~No evidence provided~~ — Evidence is qualitative but valid for pre-ticketing era

**Assessment:** Acceptable. The absence of specific support volume data is itself evidence of the problem (no tracking exists).

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| `SupportTicket` | CR—L (no Update, no Delete) | Yes — 5 states, full transition table | Soft (close, never hard delete) |
| `TicketMessage` | C-R-L (no Update, no Delete) | N/A (stateless) | Not specified |
| `TicketRating` | C-R (no Update, no Delete) | N/A (stateless) | Not specified |
| `AIConversation` | Ephemeral (session-only) | N/A | N/A (not persisted) |

### CRUD Gap Analysis

| Entity | Missing Operation | Severity | Recommendation |
|--------|-------------------|----------|----------------|
| `SupportTicket` | Update (edit subject/description) | Low | Creator might want to fix a typo in subject after submission. Consider allowing edit within first 5 min or while `open`. Proceed without — not critical. |
| `SupportTicket` | Delete | None | Correctly excluded — tickets should never be deleted |
| `TicketMessage` | Update/Delete | Low | No edit/delete for messages is reasonable for audit trail. Accepted. |
| `TicketRating` | Update | Low | Rating is one-time. If user makes a mistake, no recourse. Consider allowing update until ticket is `closed`. Minor. |
| `TicketRating` | Delete strategy | Low | Not specified, but since it's one-per-ticket and never deleted, this is fine |

---

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| `SupportTicket` | Auto-close for stale open tickets | The doc says "30 days stale" in Resolved Decisions but the state transitions only define auto-close for `resolved → closed` (7 days). What happens to `open` or `waiting_on_customer` tickets with no activity for 30 days? Add a transition `open/waiting_on_customer → closed` after 30 days? |
| `SupportTicket` | `waiting_on_customer` to `resolved` | Can Super Admin resolve directly from `waiting_on_customer`? The transition table allows `in_progress → resolved` but not `waiting_on_customer → resolved`. Should it? |

---

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| UC: Super Admin force-closes a ticket | Mentioned in state transitions but no use case defined | Low | What message does the customer see? Is there a reason required? |
| UC: Auto-close resolved tickets after 7 days | Defined in transitions but no use case describing the mechanism | Low | Is this a Celery periodic task or checked on read? |
| UC: AI assistant error handling | What happens when the AI provider is down or returns an error? | Medium | Show a fallback message? Suggest creating a ticket instead? |
| UC: AI rate limit hit | What does the user see when they exceed 20 queries/hour? | Low | Toast message? Greyed-out input? Timer showing when they can retry? |
| UC: Provider failover | If Groq is down, does the system automatically fall back to Anthropic? | Medium | Silent failover or error? This affects availability. |
| UC: Ticket list — empty state | First-time user with no tickets | Low | Show a "No tickets yet" message with a CTA to create one? |

---

## Inverse Operation Check

| Action | Inverse | Defined | Gap |
|--------|---------|---------|-----|
| Create ticket | — (no delete, by design) | Yes | — |
| Resolve ticket | Reopen ticket | Yes | 7-day window clearly defined |
| Close ticket | — (cannot reopen) | Yes | — |
| Add message | — (no edit/delete) | Accepted | Audit trail preserved |
| Submit rating | — (no update/delete) | Accepted | One-time submission |
| Open → in_progress | — (no way to revert to `open`) | Gap | Minor — Super Admin might want to "un-pick" a ticket. Not critical. |

---

## Collateral Impact Assessment

| Component | Type | Impact | Action Required | Verified |
|-----------|------|--------|-----------------|----------|
| Help panel (E51) | UI modification | Add "Contact Support" link | Modify `HelpPanel.tsx` | Yes |
| Header | UI modification | Add "Support" link | Modify `Header.tsx` | Yes |
| Sidebar/nav | UI modification | Add nav link | Modify sidebar config | Yes |
| Email service (Brevo) | New templates | 3 new email templates | Create templates | Yes |
| Super Admin layout | UI modification | New nav item | Modify SA nav | Yes |
| Environment config | New env vars | 4 new vars + Groq SDK | Update `.env` + `pyproject.toml` | Yes |
| **Notification system** | **Missing** | Should ticket events create in-app notifications (bell icon)? | **Decide: email-only or email + in-app** | **Not addressed** |
| **Existing request_bc** | **Clarification** | Users might confuse "Support Tickets" (to DSM team) with "Service Requests" (internal IT). Naming clarity needed in UI. | **Ensure clear labeling** | **Not addressed** |

---

## Slicing Assessment

**Size:** Large (4 features, 3 new entities, AI integration, 2 UI surfaces, email templates)
**Slicing needed:** Yes — the epic defines 4 features which is a natural slicing
**Suggested slicing order:**
1. F1: AI Support Assistant (independent, high value, validates provider abstraction)
2. F2: Support Ticket System (core CRUD + lifecycle)
3. F3: Super Admin Dashboard (depends on F2)
4. F4: Satisfaction Rating (depends on F2)

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| Celery periodic task for auto-close | Architecture decision | Need to know if auto-close runs as Celery beat task or lazy check |
| Brevo email template IDs | At implementation time | Can defer to design phase |
| `groq` SDK compatibility | At implementation time | Verify SDK version and Python 3.13 compatibility |

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** Strategic priority, no hard date
**Realistic:** Yes — scope is well-defined
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis

No deadline risks — this is a prioritized backlog item without time pressure.

---

## Testing Assessment

**Tests defined:** Yes — comprehensive
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | Provider interface tests well specified |
| Integration | Yes | Yes | Tenant isolation test included |
| E2E | No | No | Not required for V1 |
| UAT | No | No | No formal UAT process defined |

**Critical scenarios identified:** Yes — auth, tenant isolation, rate limiting, state transitions
**Test data requirements:** Not explicitly defined but straightforward (create company + admin user + tickets)

### Testing Gap
- AI provider tests should mock external API calls (Anthropic/Groq). Not mentioned but implied.
- Email notification tests should verify Brevo integration or mock it.

---

## Definition of Done Assessment

**DoD defined:** Yes — 15 items
| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | Yes — per user story + DoD checklist |
| Quality gates | Yes | mypy, flake8, TypeScript, tests |
| Sign-off process | No | No formal sign-off defined |
| Training needs | No | No training plan (acceptable — the feature is self-explanatory) |

---

## Red Flags

- [ ] ~~Subjective justification~~ — Not detected
- [ ] ~~Missing entities~~ — Not detected
- [x] **Notification system gap** — Epic mentions email notifications but doesn't address in-app notifications (bell icon). Should ticket events appear in the existing `notification_bc`?
- [x] **Naming confusion risk** — "Support Tickets" (to DSM team) vs "Service Requests" (internal IT). Users could confuse these. Clear labeling in UI needed.
- [x] **Auto-close mechanism undefined** — Is it a Celery periodic task or lazy evaluation? Needs architectural decision.
- [ ] ~~Provider failover~~ — Not defined, but acceptable to defer to design phase

---

## Open Questions for Stakeholder

1. **In-app notifications:** Should ticket events (new response, resolved) also create in-app notifications via `notification_bc`, or is email-only sufficient?
2. **Auto-close mechanism:** Should auto-close run as a Celery beat periodic task (proactive) or be checked lazily when the ticket is read (reactive)?
3. **Naming clarity:** How to differentiate "Support Tickets" (DSM platform support) from "Service Requests" (internal IT)? Suggestion: use "Platform Support" or "DSM Support" in the navigation to make the distinction clear.
4. **`waiting_on_customer` → `resolved`:** Can Super Admin resolve a ticket directly from `waiting_on_customer` status (e.g., customer never responded, issue deemed resolved)? Recommend: yes.
5. *(Plus the 3 open questions already in the document)*

---

## Checklist Summary

### Business Alignment: 4/5 passed
- [x] Objective identified (Churn)
- [x] Contribution explained
- [x] KPIs with measurable targets
- [x] Evidence provided (qualitative)
- [ ] Specific customer data (acceptable gap — no tracking exists yet)

### Content Completeness: 8/9 passed
- [x] Problem statement clear
- [x] Solution overview clear
- [x] User stories with acceptance criteria (9 stories)
- [x] API endpoints defined (13 endpoints)
- [x] Database migration defined
- [x] i18n requirements noted
- [x] Resolved decisions documented (9 decisions)
- [x] Multi-provider architecture well-specified
- [ ] In-app notification strategy undefined

### Use Case Coverage: 5/7 passed
- [x] Happy paths (5 use cases)
- [x] Error scenarios (validation, rate limit, reopen window)
- [x] Alternative flows (AI escalation, direct creation)
- [ ] AI error handling / provider failover
- [x] Auth/role checks
- [x] Tenant isolation
- [ ] Auto-close mechanism

### Entity States: 5/6 passed
- [x] SupportTicket states defined (5 states)
- [x] Transitions defined (8 transitions)
- [x] Actors defined per transition
- [x] Conditions defined
- [x] Delete strategy (soft close)
- [ ] Stale ticket auto-close transition for non-resolved statuses

### Collateral Impact: 6/8 passed
- [x] Help panel modification
- [x] Header modification
- [x] Navigation modification
- [x] Email templates
- [x] Super Admin nav
- [x] Environment config + dependencies
- [ ] In-app notification system
- [ ] Naming disambiguation with request_bc

### Slicing: 3/3 passed
- [x] Features identified (4)
- [x] Natural dependency order
- [x] Each feature independently valuable

### Time Constraints: 3/3 passed
- [x] No deadline — strategic priority
- [x] No calendar conflicts
- [x] Scope is realistic

### Testing: 4/5 passed
- [x] Unit tests defined
- [x] Integration tests defined
- [x] Critical scenarios identified
- [x] Auth/isolation tests included
- [ ] AI provider mocking strategy not mentioned

### Definition of Done: 3/4 passed
- [x] Acceptance criteria defined
- [x] Quality gates defined
- [x] Testing requirements defined
- [ ] No formal sign-off process (minor)

---

## Recommendations

1. **Add `waiting_on_customer → resolved` transition** — Super Admin should be able to resolve from any active status. Simple addition to the state table.
2. **Clarify auto-close mechanism** — Decide between Celery beat task or lazy evaluation. Recommend Celery beat (consistent with existing notification patterns).
3. **Address notification integration** — Decide if ticket events should create in-app notifications via `notification_bc` or stay email-only. Recommend: email-only for V1, add in-app later.
4. **Add naming guidance** — Use "Platform Support" or "DSM Support" in navigation to distinguish from internal "Service Requests".
5. **Add AI failover strategy** — Define behavior when the configured provider is unavailable. Recommend: show error message + suggest creating a ticket directly.

**Overall: The epic is ready to proceed to slicing.** The gaps identified are minor and can be resolved during the design phase.
