# Epic Slicing: E54 — Reseller Program

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-03-02
**Total Features:** 5
**Status:** Done

## Slicing Rationale

The reseller program is a new bounded context (`reseller_bc`) with four distinct entities, its own auth system, Stripe webhook integration, and both reseller and super admin UIs. The natural slices follow the reseller lifecycle: onboard → acquire clients → track revenue → get paid. Each feature delivers independent value and can be deployed incrementally.

Key decisions:
- **F1 is the foundation** — creates the `Reseller` entity, auth system, portal shell, and super admin CRUD. Everything else depends on this.
- **F2 owns `ResellerClient`** — account creation is the first feature that links resellers to companies. Both F3 (referral) and F4 (commissions) depend on this entity.
- **F3 and F4 are parallel** — referral attribution and commission tracking are independent capabilities that both depend on F2's `ResellerClient` entity.
- **F5 depends on F4** — payouts require commission balance calculation.

## Dependency Graph

```
F1 (Portal Foundation)
 └── F2 (Account Creation)
      ├── F3 (Referral Link)         [parallel]
      └── F4 (Commission Tracking)   [parallel]
           └── F5 (Payout Requests)
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 1 | Portal Foundation | None | Super admin can onboard resellers; resellers can log in, see dashboard, edit profile | M | Done |
| 2 | Account Creation | F1 | Resellers can create demo/normal client accounts; client list visible | L | Done |
| 3 | Referral Link | F2 | Prospects attributed to resellers via tracked referral links | S | Done |
| 4 | Commission Tracking | F2 | Commissions auto-calculated from Stripe payments; resellers see earnings | M | Done |
| 5 | Payout Requests | F4 | Resellers can request payouts; super admin can approve and process | S | Done |

## Recommended Order

1. **F1: Portal Foundation** — must be first; creates the reseller entity, auth system, and portal shell
2. **F2: Account Creation** — highest business value after foundation; resellers can start acquiring clients
3. **F3: Referral Link** — low effort, adds passive client acquisition channel (can be parallel with F4)
4. **F4: Commission Tracking** — core financial feature; requires Stripe webhook integration
5. **F5: Payout Requests** — completes the financial cycle; depends on commissions existing

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F1 → F2 → F3/F4 → F5)
- [x] Each feature independently deployable
- [x] Vertical slices (each includes backend domain + API + frontend UI)
- [x] Shared foundation identified (F1)
- [x] No overlapping scope (entity ownership is clear)
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- **F2 is the largest feature** — includes demo account creation (seed data refactor), normal account creation, demo expiry Celery task, and the `ResellerClient` entity. Could be split further (normal vs demo) but both account types are core to reseller value proposition.
- **F4 has external dependency** — Stripe webhook integration relies on E43's `StripeWebhookDispatcher`. Verify the dispatcher supports adding new event handlers before starting F4.
- **F3 modifies existing registration flow** — the referral attribution hook touches `POST /auth/register`, which is outside `reseller_bc`. Minimal change (check for referral code + create ResellerClient), but needs careful testing to avoid regression.
