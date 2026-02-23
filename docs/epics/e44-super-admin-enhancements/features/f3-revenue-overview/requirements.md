# Feature F3: Founder Dashboard

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 3
**Dependencies:** F1 (plan price constants defined in `plan_gate.py`)
**Complexity:** M

---

## Context

The Orchestrator (CEO) is the only human running DeskSupportMonkey. They currently track MRR manually in a spreadsheet. This dashboard replaces that spreadsheet and provides a single view of business health — revenue, trial pipeline, churn risk, and growth — computed in real time from the database and Stripe.

---

## Scope

### Included

**Revenue section (from DB + plan price constants):**
- Current MRR — active paying subscriptions × plan price
- MRR change vs last month (new MRR − churned MRR)
- New MRR this month — companies that became paying this calendar month
- Churned MRR this month — companies that cancelled or downgraded this month
- Plan distribution — count + MRR contribution per plan (Starter/Growth/Scale)

**Trial pipeline (from DB):**
- Active trials count
- Trials expiring in 7 days (urgent — potential conversions or churns)
- Trials expiring in 30 days
- Trials started this month (new top of funnel)

**Company health (from DB):**
- Total active companies (paying + trial + free)
- Companies in grace period (churn risk — unpaid)
- Companies suspended (churned / blocked)
- Complimentary accounts (not revenue-generating)

**Growth (from DB):**
- New signups last 7 days
- New signups last 30 days
- Month-over-month growth rate (companies)

**Milestone tracker (hardcoded targets from `startup/financials/projections.md`):**
- Break-even: €259 MRR — covers fixed costs
- Founder salary: €2,000 MRR
- First advisor: €3,000 MRR
- Current MRR progress bar toward next milestone

**Stripe-sourced (live fetch):**
- Failed payments this month — invoices with `status=open` or `uncollectible` from Stripe
- Upcoming renewals next 7 days — subscriptions with `current_period_end` in the next 7 days (from DB, no Stripe call needed)

### Excluded

- Operational metrics (request resolution time, asset assignment rates) — these are company admin concerns, not CEO concerns
- Historical MRR trend charts (future feature)
- Per-company drill-down (covered by company list + billing modal)
- Revenue forecasting

---

## User Value

The Orchestrator opens this page and knows in 30 seconds: how much money is coming in, what's at risk, who's about to convert or churn, and how far they are from the next personal milestone. No spreadsheet needed.

---

## Acceptance Criteria

**Revenue:**
- [ ] MRR = sum of `PLAN_PRICE_CENTS[plan]` for companies with `billing_status = active` and `complimentary = false` and `plan` in (starter, growth, scale)
- [ ] New MRR = companies where `stripe_subscription_id` was first set this calendar month
- [ ] Churned MRR = companies where subscription was cancelled this calendar month (plan downgraded to free from paid, within current month — derived from `current_period_end` falling this month)
- [ ] Plan distribution shows count and MRR contribution per paid plan

**Trial pipeline:**
- [ ] Active trials = `trial_ends_at > now`
- [ ] Expiring 7d = `now < trial_ends_at <= now + 7 days`
- [ ] Expiring 30d = `now < trial_ends_at <= now + 30 days`
- [ ] Started this month = `created_at >= first day of current month` (all new companies are in trial)

**Company health:**
- [ ] Grace period count = `billing_status = grace_period`
- [ ] Suspended count = `billing_status = suspended`
- [ ] Complimentary count = `complimentary = true`

**Growth:**
- [ ] New signups 7d = companies created in the last 7 days
- [ ] New signups 30d = companies created in the last 30 days

**Milestone tracker:**
- [ ] Shows current MRR vs next milestone with progress percentage
- [ ] Milestones: €259 (costs covered), €2,000 (salary), €3,000 (advisor)

**Stripe:**
- [ ] Failed payments = Stripe invoices with `status = open` fetched for companies in `grace_period` or `suspended`
- [ ] Upcoming renewals 7d = companies with `current_period_end` between now and now+7 days (from DB)

**General:**
- [ ] All DB metrics computed in ≤2 queries (no N+1)
- [ ] Stripe data fetched only for companies with `stripe_customer_id` (batch call)
- [ ] Returns 403 for non-super-admin
- [ ] Page accessible from super admin sidebar
- [ ] Data refreshes on demand (manual refresh button)

---

## Technical Scope

### Key Components

**Backend:**
- `GetFounderDashboardQuery` + `GetFounderDashboardQueryHandler`
- `FounderDashboardDto` with all sections
- `CompanyRepository.get_dashboard_stats()` — single aggregate query
- Stripe batch invoice fetch for grace/suspended companies
- `MILESTONE_TARGETS` constant — hardcoded milestones
- New endpoint `GET /api/v1/super-admin/dashboard`

**Frontend:**
- New page `web/app/src/pages/superadmin/FounderDashboardPage.tsx`
- Route `/dashboard` (super_admin only) — landing page for super admin
- Sidebar link (first item in super admin nav)

---

## Notes

**MRR accuracy note:** New/churned MRR is a simplification — derived from DB timestamps, not from Stripe revenue events. It gives directional accuracy for a bootstrapped founder checking numbers weekly. A more precise MRR ledger can be added later when the business is at scale.

**Stripe failed payments:** Fetched live only for companies currently in `grace_period` or `suspended` (typically 0-5 companies). Not a performance concern.

**Milestone amounts are in EUR** — same as the business model. The `PLAN_PRICE_CENTS` constants are in USD for Stripe but the display converts to EUR at 1:1 (USD ≈ EUR for now; can add FX rate later).
