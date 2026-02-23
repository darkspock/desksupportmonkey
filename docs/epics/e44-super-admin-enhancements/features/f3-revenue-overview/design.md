# Solution Design: F3 — Founder Dashboard

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Bounded Context:** `company_bc`

---

## Summary

Single endpoint backed by one aggregate SQL query + one Stripe batch call (only for at-risk companies). New frontend page as the super admin landing screen. No DB schema changes.

---

## Architecture Decision

**Two-query strategy:**
1. One aggregate SQL query for all DB metrics (MRR, distribution, trials, growth, health)
2. One Stripe batch call for open invoices — only for companies currently in `grace_period` or `suspended` (typically 0-5 at this scale)

This keeps the endpoint fast even as the platform scales to hundreds of companies.

---

## Implementation Plan

### 1. Domain / Application Layer

#### New constants in `src/company_bc/company/domain/plan_gate.py`

```python
# Already added in F1:
PLAN_PRICE_CENTS: dict[PlanTier, int] = {
    PlanTier.FREE: 0,
    PlanTier.PREMIUM: 4900,
    PlanTier.ENTERPRISE: 14900,
    PlanTier.OPEN_SOURCE: 0,
}

# NEW — milestone targets for founder dashboard (in cents):
MILESTONE_TARGETS_CENTS: list[dict] = [
    {"label": "costs_covered", "amount_cents": 25900, "description": "Covers monthly fixed costs"},
    {"label": "founder_salary", "amount_cents": 200000, "description": "Orchestrator draws salary"},
    {"label": "first_advisor", "amount_cents": 300000, "description": "First advisor retainer"},
    {"label": "head_of_growth", "amount_cents": 700000, "description": "Head of Growth hire"},
]
```

#### New: `src/company_bc/company/application/queries/get_founder_dashboard.py`

```python
@dataclass
class RevenueSectionDto:
    mrr_cents: int
    mrr_formatted: str                # "€X,XXX"
    new_mrr_cents: int                # became paying this month
    churned_mrr_cents: int            # lost this month
    net_new_mrr_cents: int            # new - churned
    by_plan: list[PlanMrrDto]         # [{plan, count, mrr_cents}]

@dataclass
class PlanMrrDto:
    plan: str
    count: int
    mrr_cents: int

@dataclass
class TrialPipelineDto:
    active: int
    expiring_7d: int
    expiring_30d: int
    started_this_month: int

@dataclass
class CompanyHealthDto:
    total_active: int
    grace_period: int         # unpaid — churn risk
    suspended: int            # churned / blocked
    complimentary: int        # not revenue-generating
    failed_payments: int      # from Stripe (live)

@dataclass
class GrowthDto:
    new_7d: int
    new_30d: int
    mom_growth_pct: Optional[float]   # month-over-month % if data available

@dataclass
class MilestoneDto:
    label: str
    description: str
    target_cents: int
    current_cents: int
    pct: int                  # 0-100, capped at 100
    achieved: bool

@dataclass
class UpcomingRenewalDto:
    company_id: str
    company_name: str
    plan: str
    period_end: datetime

@dataclass
class FounderDashboardDto:
    revenue: RevenueSectionDto
    trials: TrialPipelineDto
    health: CompanyHealthDto
    growth: GrowthDto
    next_milestone: MilestoneDto        # the next unachieved milestone
    upcoming_renewals_7d: list[UpcomingRenewalDto]
    as_of: datetime

@dataclass
class GetFounderDashboardQuery(Query):
    pass

class GetFounderDashboardQueryHandler(QueryHandler[GetFounderDashboardQuery, FounderDashboardDto]):
    def __init__(self, company_repo: CompanyRepository, stripe_client: StripeClient) -> None:
        self.company_repo = company_repo
        self.stripe_client = stripe_client

    def handle(self, query: GetFounderDashboardQuery) -> FounderDashboardDto:
        now = datetime.now(timezone.utc)
        stats = self.company_repo.get_dashboard_stats(now)

        # MRR from plan price constants
        mrr_cents = sum(
            stats["plan_counts"].get(plan, 0) * PLAN_PRICE_CENTS[plan]
            for plan in [PlanTier.PREMIUM, PlanTier.ENTERPRISE]
            # Note: PREMIUM = Starter/Growth, ENTERPRISE = Scale in current config
        )

        # Failed payments: fetch open Stripe invoices for grace/suspended companies
        failed_payments = 0
        if stats["at_risk_stripe_ids"]:
            for customer_id in stats["at_risk_stripe_ids"]:
                invoices = self.stripe_client.list_invoices(customer_id, limit=5)
                failed_payments += sum(1 for inv in invoices if inv["status"] in ("open", "uncollectible"))

        # Next milestone
        next_milestone = _compute_next_milestone(mrr_cents)

        revenue = RevenueSectionDto(
            mrr_cents=mrr_cents,
            mrr_formatted=f"€{mrr_cents / 100:,.0f}",
            new_mrr_cents=stats["new_paying_this_month"] * _avg_plan_price(stats["plan_counts"]),
            churned_mrr_cents=stats["churned_this_month_cents"],
            net_new_mrr_cents=0,  # computed after
            by_plan=[
                PlanMrrDto(plan=p.value, count=stats["plan_counts"].get(p, 0),
                           mrr_cents=stats["plan_counts"].get(p, 0) * PLAN_PRICE_CENTS[p])
                for p in [PlanTier.PREMIUM, PlanTier.ENTERPRISE]
            ],
        )
        revenue.net_new_mrr_cents = revenue.new_mrr_cents - revenue.churned_mrr_cents

        return FounderDashboardDto(
            revenue=revenue,
            trials=TrialPipelineDto(
                active=stats["trials_active"],
                expiring_7d=stats["trials_expiring_7d"],
                expiring_30d=stats["trials_expiring_30d"],
                started_this_month=stats["trials_started_this_month"],
            ),
            health=CompanyHealthDto(
                total_active=stats["total_active"],
                grace_period=stats["grace_period_count"],
                suspended=stats["suspended_count"],
                complimentary=stats["complimentary_count"],
                failed_payments=failed_payments,
            ),
            growth=GrowthDto(
                new_7d=stats["new_7d"],
                new_30d=stats["new_30d"],
                mom_growth_pct=stats["mom_growth_pct"],
            ),
            next_milestone=next_milestone,
            upcoming_renewals_7d=stats["upcoming_renewals_7d"],
            as_of=now,
        )
```

---

### 2. Infrastructure Layer

#### `CompanyRepository.get_dashboard_stats(now)` — aggregate query

```python
def get_dashboard_stats(self, now: datetime) -> dict:
    from sqlalchemy import case, func, and_, extract

    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (first_of_month - timedelta(days=1)).replace(day=1)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ahead = now + timedelta(days=7)
    thirty_days_ahead = now + timedelta(days=30)

    # === Single aggregate query ===
    stmt = select(
        func.count().label("total"),
        # Plan counts (active, non-complimentary)
        func.sum(case((and_(CompanyModel.plan == "premium", CompanyModel.billing_status == "active", CompanyModel.complimentary == False), 1), else_=0)).label("premium_active"),
        func.sum(case((and_(CompanyModel.plan == "enterprise", CompanyModel.billing_status == "active", CompanyModel.complimentary == False), 1), else_=0)).label("enterprise_active"),
        # Total by plan (all statuses)
        func.sum(case((CompanyModel.plan == "premium", 1), else_=0)).label("premium_total"),
        func.sum(case((CompanyModel.plan == "enterprise", 1), else_=0)).label("enterprise_total"),
        func.sum(case((CompanyModel.plan == "free", 1), else_=0)).label("free_total"),
        func.sum(case((CompanyModel.plan == "open_source", 1), else_=0)).label("open_source_total"),
        # Health
        func.sum(case((CompanyModel.billing_status == "grace_period", 1), else_=0)).label("grace_period_count"),
        func.sum(case((CompanyModel.billing_status == "suspended", 1), else_=0)).label("suspended_count"),
        func.sum(case((CompanyModel.complimentary == True, 1), else_=0)).label("complimentary_count"),
        func.sum(case((CompanyModel.status == "active", 1), else_=0)).label("total_active"),
        # Trial pipeline
        func.sum(case((CompanyModel.trial_ends_at > now, 1), else_=0)).label("trials_active"),
        func.sum(case((and_(CompanyModel.trial_ends_at > now, CompanyModel.trial_ends_at <= seven_days_ahead), 1), else_=0)).label("trials_expiring_7d"),
        func.sum(case((and_(CompanyModel.trial_ends_at > now, CompanyModel.trial_ends_at <= thirty_days_ahead), 1), else_=0)).label("trials_expiring_30d"),
        func.sum(case((CompanyModel.created_at >= first_of_month, 1), else_=0)).label("trials_started_this_month"),
        # Growth
        func.sum(case((CompanyModel.created_at >= seven_days_ago, 1), else_=0)).label("new_7d"),
        func.sum(case((CompanyModel.created_at >= thirty_days_ago, 1), else_=0)).label("new_30d"),
        func.sum(case((and_(CompanyModel.created_at >= last_month_start, CompanyModel.created_at < first_of_month), 1), else_=0)).label("last_month_count"),
        # New paying this month (got subscription this month)
        func.sum(case((and_(CompanyModel.stripe_subscription_id.isnot(None), CompanyModel.current_period_end >= first_of_month, CompanyModel.plan != "free"), 1), else_=0)).label("new_paying_this_month"),
    )
    row = self._session.execute(stmt).one()

    # Upcoming renewals (separate small query — needs names)
    renewals_stmt = (
        select(CompanyModel)
        .where(CompanyModel.current_period_end.between(now, seven_days_ahead))
        .where(CompanyModel.billing_status == "active")
        .order_by(CompanyModel.current_period_end)
        .limit(10)
    )
    renewals = [
        UpcomingRenewalDto(
            company_id=c.id, company_name=c.name, plan=c.plan,
            period_end=c.current_period_end,
        )
        for c in self._session.scalars(renewals_stmt).all()
    ]

    # At-risk Stripe customer IDs for failed payment check
    at_risk_stmt = select(CompanyModel.stripe_customer_id).where(
        and_(
            CompanyModel.billing_status.in_(["grace_period", "suspended"]),
            CompanyModel.stripe_customer_id.isnot(None),
        )
    )
    at_risk_ids = [r for r in self._session.scalars(at_risk_stmt).all() if r]

    # MoM growth %
    last_month = row.last_month_count or 0
    this_month = row.new_30d or 0
    mom = round(((this_month - last_month) / last_month * 100), 1) if last_month > 0 else None

    return {
        "total_active": row.total_active or 0,
        "plan_counts": {
            PlanTier.PREMIUM: row.premium_active or 0,
            PlanTier.ENTERPRISE: row.enterprise_active or 0,
        },
        "premium_total": row.premium_total or 0,
        "enterprise_total": row.enterprise_total or 0,
        "free_total": row.free_total or 0,
        "grace_period_count": row.grace_period_count or 0,
        "suspended_count": row.suspended_count or 0,
        "complimentary_count": row.complimentary_count or 0,
        "trials_active": row.trials_active or 0,
        "trials_expiring_7d": row.trials_expiring_7d or 0,
        "trials_expiring_30d": row.trials_expiring_30d or 0,
        "trials_started_this_month": row.trials_started_this_month or 0,
        "new_7d": row.new_7d or 0,
        "new_30d": row.new_30d or 0,
        "new_paying_this_month": row.new_paying_this_month or 0,
        "churned_this_month_cents": 0,   # simplified — no churn ledger yet
        "mom_growth_pct": mom,
        "upcoming_renewals_7d": renewals,
        "at_risk_stripe_ids": at_risk_ids,
    }
```

---

### 3. HTTP Layer

#### New: `adapters/http/api/super_admin/schemas.py`

```python
class PlanMrrResponse(BaseModel):
    plan: str
    count: int
    mrr_cents: int

class RevenueResponse(BaseModel):
    mrr_cents: int
    mrr_formatted: str
    new_mrr_cents: int
    churned_mrr_cents: int
    net_new_mrr_cents: int
    by_plan: list[PlanMrrResponse]

class TrialPipelineResponse(BaseModel):
    active: int
    expiring_7d: int
    expiring_30d: int
    started_this_month: int

class CompanyHealthResponse(BaseModel):
    total_active: int
    grace_period: int
    suspended: int
    complimentary: int
    failed_payments: int

class GrowthResponse(BaseModel):
    new_7d: int
    new_30d: int
    mom_growth_pct: Optional[float] = None

class MilestoneResponse(BaseModel):
    label: str
    description: str
    target_cents: int
    current_cents: int
    pct: int
    achieved: bool

class UpcomingRenewalResponse(BaseModel):
    company_id: str
    company_name: str
    plan: str
    period_end: datetime

class FounderDashboardResponse(BaseModel):
    revenue: RevenueResponse
    trials: TrialPipelineResponse
    health: CompanyHealthResponse
    growth: GrowthResponse
    next_milestone: MilestoneResponse
    upcoming_renewals_7d: list[UpcomingRenewalResponse]
    as_of: datetime
```

#### New: `adapters/http/api/super_admin/routers.py`

```python
router = APIRouter(prefix="/super-admin", tags=["super-admin"])

@router.get("/dashboard")
def get_founder_dashboard(
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
) -> dict:
    handler = GetFounderDashboardQueryHandler(
        company_repo=company_repo,
        stripe_client=stripe_client,
    )
    dto = handler.handle(GetFounderDashboardQuery())
    return {"data": _dto_to_response(dto).model_dump(mode="json")}
```

---

### 4. Frontend

#### New: `web/app/src/pages/superadmin/FounderDashboardPage.tsx`

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  💰 MRR             📈 Net New MRR    ⚠️ At Risk    🔄 Trials│
│  €X,XXX/mo          +€XXX this month   X grace       XX active│
├─────────────────────────────────────────────────────────────┤
│  Milestone Progress                                          │
│  [━━━━━━━━━━░░░░░░░░░░░░░] 47%  → €2,000 MRR (Salary)      │
├─────────────────────────────────────────────────────────────┤
│  Plan Distribution          │  Trial Pipeline               │
│  Free: XX                   │  Active: XX                   │
│  Starter: XX  €XXX          │  Expiring 7d: XX  ⚡          │
│  Growth: XX   €XXX          │  Expiring 30d: XX             │
│  Scale: XX    €XXX          │  Started this month: XX       │
│  Complimentary: XX          │                               │
├─────────────────────────────────────────────────────────────┤
│  Company Health             │  Growth                       │
│  Active: XX                 │  New 7d: +XX                  │
│  Grace period: XX  🔴       │  New 30d: +XX                 │
│  Suspended: XX   🔴         │  MoM: +XX%                    │
├─────────────────────────────────────────────────────────────┤
│  Upcoming Renewals (next 7 days)                            │
│  Acme Corp  Growth   Feb 28   │  Globex  Starter  Mar 1     │
└─────────────────────────────────────────────────────────────┘
```

**Refresh:** manual refresh button, `staleTime: 5 * 60 * 1000` (5 min cache)

**Route:** `/overview` (replaces the old overview name — this is the main super admin landing)

**Sidebar:** First item in super admin nav, icon: `LayoutDashboard`

---

## Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/company_bc/company/domain/plan_gate.py` | Additive | `MILESTONE_TARGETS_CENTS` |
| `src/company_bc/.../get_founder_dashboard.py` | New | Query, handler, all DTOs |
| `src/company_bc/.../repository.py` | Additive | `get_dashboard_stats()` |
| `adapters/http/api/super_admin/schemas.py` | New | All response schemas |
| `adapters/http/api/super_admin/routers.py` | New | Dashboard endpoint |
| `app.py` | Additive | Register super_admin router |
| `web/app/src/pages/superadmin/FounderDashboardPage.tsx` | New | Dashboard page |
| `web/app/src/router.tsx` | Additive | `/overview` route |
| `web/app/src/components/layout/Sidebar.tsx` | Additive | Dashboard nav link |
| `web/app/src/locales/en.ts` + `es.ts` | Additive | Dashboard i18n keys |

**Breaking changes:** None.

---

## Testing Strategy

| Test | Scope | Priority |
|------|-------|----------|
| Unit | `GetFounderDashboardQueryHandler` — MRR calc, milestone computation, zero-state (no companies) | High |
| Unit | `_compute_next_milestone()` — all milestone transitions | High |
| Integration | `GET /super-admin/dashboard` — correct aggregates with seeded data; 403 for non-super-admin | High |

---

## Implementation Order

1. `plan_gate.py` — add `MILESTONE_TARGETS_CENTS`
2. `get_founder_dashboard.py` — DTOs, query, handler
3. `repository.py` — `get_dashboard_stats()`
4. `super_admin/schemas.py` + `routers.py`
5. `app.py` — register router
6. Unit tests
7. Integration tests
8. Frontend: `FounderDashboardPage.tsx` → router → Sidebar → i18n
