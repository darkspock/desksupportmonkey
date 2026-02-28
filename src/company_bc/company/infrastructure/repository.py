from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import ulid
from sqlalchemy import ColumnElement, and_, case, delete, func, select
from sqlalchemy.orm import Session

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.company_bc.company.infrastructure.models import (
    CompanyEmailDomainModel,
    CompanyModel,
    ProcessedStripeEventModel,
)


class CompanyRepository(CompanyRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, company: Company) -> Company:
        existing = self.session.execute(
            select(CompanyModel).where(CompanyModel.id == company.id)
        ).scalar_one_or_none()
        if existing:
            existing.name = company.name
            existing.status = company.status.value
            existing.is_active = company.is_active
            existing.plan = company.plan.value
            existing.billing_status = company.billing_status.value
            existing.stripe_customer_id = company.stripe_customer_id
            existing.stripe_subscription_id = company.stripe_subscription_id
            existing.grace_period_started_at = company.grace_period_started_at
            existing.current_period_end = company.current_period_end
            existing.pending_downgrade_plan = (
                company.pending_downgrade_plan.value
                if company.pending_downgrade_plan else None
            )
            existing.complimentary = company.complimentary
            existing.trial_ends_at = company.trial_ends_at
            existing.sector = company.sector
            existing.onboarding_completed_at = company.onboarding_completed_at
        else:
            model = CompanyModel(
                id=company.id,
                name=company.name,
                status=company.status.value,
                is_active=company.is_active,
                plan=company.plan.value,
                billing_status=company.billing_status.value,
                stripe_customer_id=company.stripe_customer_id,
                stripe_subscription_id=company.stripe_subscription_id,
                grace_period_started_at=company.grace_period_started_at,
                current_period_end=company.current_period_end,
                pending_downgrade_plan=(
                    company.pending_downgrade_plan.value
                    if company.pending_downgrade_plan else None
                ),
                complimentary=company.complimentary,
                trial_ends_at=company.trial_ends_at,
                sector=company.sector,
                onboarding_completed_at=company.onboarding_completed_at,
            )
            self.session.add(model)
        self.session.flush()
        return company

    def find_by_id(self, company_id: str) -> Optional[Company]:
        model = self.session.execute(
            select(CompanyModel).where(CompanyModel.id == company_id)
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_by_name(self, name: str) -> Optional[Company]:
        model = self.session.execute(
            select(CompanyModel).where(func.lower(CompanyModel.name) == name.lower().strip())
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self, page: int, page_size: int, search: Optional[str] = None
    ) -> tuple[list[Company], int]:
        stmt = select(CompanyModel)
        if search:
            stmt = stmt.where(CompanyModel.name.ilike(f"%{search}%"))
        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()
        models = self.session.execute(
            stmt.order_by(CompanyModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total or 0

    def find_all_with_counts(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        in_trial: Optional[bool] = None,
        plan: Optional[str] = None,
    ) -> tuple[list[tuple[Company, int, int]], int]:
        from src.auth_bc.user.infrastructure.models import UserModel
        from src.asset_bc.asset.infrastructure.models import AssetModel

        user_count_sq = (
            select(func.count())
            .where(UserModel.company_id == CompanyModel.id)
            .where(UserModel.is_active.is_(True))
            .correlate(CompanyModel)
            .scalar_subquery()
        )
        asset_count_sq = (
            select(func.count())
            .where(AssetModel.company_id == CompanyModel.id)
            .where(AssetModel.status != "decommissioned")
            .correlate(CompanyModel)
            .scalar_subquery()
        )

        filters: list[ColumnElement[bool]] = []
        if search:
            filters.append(CompanyModel.name.ilike(f"%{search}%"))
        if in_trial is True:
            filters.append(CompanyModel.trial_ends_at > func.now())  # type: ignore[operator]
        if plan is not None:
            filters.append(CompanyModel.plan == plan)

        base_stmt = select(CompanyModel)
        if filters:
            base_stmt = base_stmt.where(*filters)

        total = self.session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar() or 0

        stmt = select(CompanyModel, user_count_sq.label("user_count"), asset_count_sq.label("asset_count"))
        if filters:
            stmt = stmt.where(*filters)

        rows = self.session.execute(
            stmt.order_by(CompanyModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        result: list[tuple[Company, int, int]] = [
            (self._to_entity(row.CompanyModel), row.user_count or 0, row.asset_count or 0)
            for row in rows
        ]
        return result, total

    def find_domain(self, domain: str) -> Optional[str]:
        result = self.session.execute(
            select(CompanyEmailDomainModel.company_id)
            .where(CompanyEmailDomainModel.domain == domain.lower().strip())
        ).scalar_one_or_none()
        return result if result else None

    def save_domains(self, company_id: str, domains: list[str]) -> None:
        self.session.execute(
            delete(CompanyEmailDomainModel)
            .where(CompanyEmailDomainModel.company_id == company_id)
        )
        for domain in domains:
            model = CompanyEmailDomainModel(
                id=str(ulid.new()),
                company_id=company_id,
                domain=domain.lower().strip(),
            )
            self.session.add(model)
        self.session.flush()

    def count_users(self, company_id: str) -> int:
        from src.auth_bc.user.infrastructure.models import UserModel

        return (
            self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.company_id == company_id)
            ).scalar()
        ) or 0

    def count_departments(self, company_id: str) -> int:
        try:
            from src.company_bc.department.infrastructure.models import DepartmentModel

            return (
                self.session.execute(
                    select(func.count()).select_from(DepartmentModel)
                    .where(
                        DepartmentModel.company_id == company_id,
                        DepartmentModel.is_active.is_(True),
                    )
                ).scalar()
            ) or 0
        except Exception:
            return 0

    def count_assets(self, company_id: str) -> int:
        try:
            from src.asset_bc.asset.infrastructure.models import AssetModel

            return (
                self.session.execute(
                    select(func.count()).select_from(AssetModel)
                    .where(
                        AssetModel.company_id == company_id,
                        AssetModel.status != "decommissioned",
                    )
                ).scalar()
            ) or 0
        except Exception:
            return 0

    def get_dashboard_stats(self, now: datetime) -> dict[str, Any]:
        from src.company_bc.company.application.queries.get_founder_dashboard import (
            UpcomingRenewalDto,
        )

        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (first_of_month - timedelta(days=1)).replace(day=1)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ahead = now + timedelta(days=7)
        thirty_days_ahead = now + timedelta(days=30)

        stmt = select(
            func.count().label("total"),
            func.sum(case(
                (and_(CompanyModel.plan == "premium", CompanyModel.billing_status == "active", CompanyModel.complimentary.is_(False)), 1),
                else_=0,
            )).label("premium_active"),
            func.sum(case(
                (and_(CompanyModel.plan == "enterprise", CompanyModel.billing_status == "active", CompanyModel.complimentary.is_(False)), 1),
                else_=0,
            )).label("enterprise_active"),
            func.sum(case((CompanyModel.billing_status == "grace_period", 1), else_=0)).label("grace_period_count"),
            func.sum(case((CompanyModel.billing_status == "suspended", 1), else_=0)).label("suspended_count"),
            func.sum(case((CompanyModel.complimentary.is_(True), 1), else_=0)).label("complimentary_count"),
            func.sum(case((CompanyModel.status == "active", 1), else_=0)).label("total_active"),
            func.sum(case((CompanyModel.trial_ends_at > now, 1), else_=0)).label("trials_active"),
            func.sum(case(
                (and_(CompanyModel.trial_ends_at > now, CompanyModel.trial_ends_at <= seven_days_ahead), 1),
                else_=0,
            )).label("trials_expiring_7d"),
            func.sum(case(
                (and_(CompanyModel.trial_ends_at > now, CompanyModel.trial_ends_at <= thirty_days_ahead), 1),
                else_=0,
            )).label("trials_expiring_30d"),
            func.sum(case((CompanyModel.created_at >= first_of_month, 1), else_=0)).label("trials_started_this_month"),
            func.sum(case((CompanyModel.created_at >= seven_days_ago, 1), else_=0)).label("new_7d"),
            func.sum(case((CompanyModel.created_at >= thirty_days_ago, 1), else_=0)).label("new_30d"),
            func.sum(case(
                (and_(CompanyModel.created_at >= last_month_start, CompanyModel.created_at < first_of_month), 1),
                else_=0,
            )).label("last_month_count"),
            func.sum(case(
                (and_(
                    CompanyModel.stripe_subscription_id.isnot(None),
                    CompanyModel.current_period_end >= first_of_month,
                    CompanyModel.plan != "free",
                ), 1),
                else_=0,
            )).label("new_paying_this_month"),
        ).select_from(CompanyModel)
        row = self.session.execute(stmt).one()

        renewals_stmt = (
            select(CompanyModel)
            .where(CompanyModel.current_period_end.between(now, seven_days_ahead))
            .where(CompanyModel.billing_status == "active")
            .order_by(CompanyModel.current_period_end)
            .limit(10)
        )
        renewals = [
            UpcomingRenewalDto(
                company_id=c.id,
                company_name=c.name,
                plan=c.plan,
                period_end=c.current_period_end,
            )
            for c in self.session.scalars(renewals_stmt).all()
            if c.current_period_end is not None
        ]

        at_risk_stmt = select(CompanyModel.stripe_customer_id).where(
            and_(
                CompanyModel.billing_status.in_(["grace_period", "suspended"]),
                CompanyModel.stripe_customer_id.isnot(None),
            )
        )
        at_risk_ids = [r for r in self.session.scalars(at_risk_stmt).all() if r]

        last_month = row.last_month_count or 0
        this_month_new = row.new_30d or 0
        mom = round(((this_month_new - last_month) / last_month * 100), 1) if last_month > 0 else None

        return {
            "total_active": row.total_active or 0,
            "plan_counts": {
                PlanTier.PREMIUM: row.premium_active or 0,
                PlanTier.ENTERPRISE: row.enterprise_active or 0,
            },
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
            "churned_this_month_cents": 0,
            "mom_growth_pct": mom,
            "upcoming_renewals_7d": renewals,
            "at_risk_stripe_ids": at_risk_ids,
        }

    def delete(self, company_id: str) -> None:
        self.session.execute(
            delete(CompanyEmailDomainModel)
            .where(CompanyEmailDomainModel.company_id == company_id)
        )
        self.session.execute(
            delete(CompanyModel).where(CompanyModel.id == company_id)
        )
        self.session.flush()

    def find_by_stripe_customer_id(self, customer_id: str) -> Optional[Company]:
        model = self.session.execute(
            select(CompanyModel).where(CompanyModel.stripe_customer_id == customer_id)
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def mark_stripe_event_processed(self, event_id: str) -> None:
        record = ProcessedStripeEventModel(
            id=event_id,
            processed_at=datetime.now(timezone.utc),
        )
        self.session.add(record)
        self.session.flush()

    def is_stripe_event_processed(self, event_id: str) -> bool:
        result = self.session.execute(
            select(ProcessedStripeEventModel).where(ProcessedStripeEventModel.id == event_id)
        ).scalar_one_or_none()
        return result is not None

    def _to_entity(self, model: CompanyModel) -> Company:
        domains = self.session.execute(
            select(CompanyEmailDomainModel.domain)
            .where(CompanyEmailDomainModel.company_id == model.id)
        ).scalars().all()
        return Company(
            id=model.id,
            name=model.name,
            status=CompanyStatus(model.status),
            email_domains=list(domains),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            plan=PlanTier(model.plan),
            billing_status=BillingStatus(model.billing_status),
            stripe_customer_id=model.stripe_customer_id,
            stripe_subscription_id=model.stripe_subscription_id,
            grace_period_started_at=model.grace_period_started_at,
            current_period_end=model.current_period_end,
            pending_downgrade_plan=(
                PlanTier(model.pending_downgrade_plan)
                if model.pending_downgrade_plan else None
            ),
            complimentary=model.complimentary,
            trial_ends_at=model.trial_ends_at,
            sector=model.sector,
            onboarding_completed_at=model.onboarding_completed_at,
        )
