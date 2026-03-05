from datetime import datetime
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.reseller_bc.commission.domain.entities import ResellerCommission
from src.reseller_bc.commission.domain.enums import CommissionStatus
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface
from src.reseller_bc.commission.infrastructure.models import ResellerCommissionModel


class ResellerCommissionRepository(ResellerCommissionRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, commission: ResellerCommission) -> None:
        existing = self.session.execute(
            select(ResellerCommissionModel).where(ResellerCommissionModel.id == commission.id)
        ).scalar_one_or_none()
        if existing:
            existing.reseller_id = commission.reseller_id
            existing.reseller_client_id = commission.reseller_client_id
            existing.company_id = commission.company_id
            existing.payment_amount_cents = commission.payment_amount_cents
            existing.commission_pct = commission.commission_pct
            existing.commission_amount_cents = commission.commission_amount_cents
            existing.stripe_invoice_id = commission.stripe_invoice_id
            existing.period_start = commission.period_start
            existing.period_end = commission.period_end
            existing.status = commission.status.value
        else:
            model = ResellerCommissionModel(
                id=commission.id,
                reseller_id=commission.reseller_id,
                reseller_client_id=commission.reseller_client_id,
                company_id=commission.company_id,
                payment_amount_cents=commission.payment_amount_cents,
                commission_pct=commission.commission_pct,
                commission_amount_cents=commission.commission_amount_cents,
                stripe_invoice_id=commission.stripe_invoice_id,
                period_start=commission.period_start,
                period_end=commission.period_end,
                status=commission.status.value,
            )
            self.session.add(model)
        self.session.flush()

    def find_by_stripe_invoice_id(self, stripe_invoice_id: str) -> Optional[ResellerCommission]:
        model = self.session.execute(
            select(ResellerCommissionModel)
            .where(ResellerCommissionModel.stripe_invoice_id == stripe_invoice_id)
            .order_by(ResellerCommissionModel.created_at.asc())
            .limit(1)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerCommission]:
        models = self.session.execute(
            select(ResellerCommissionModel)
            .where(ResellerCommissionModel.reseller_id == reseller_id)
            .order_by(ResellerCommissionModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(ResellerCommissionModel)
                .where(ResellerCommissionModel.reseller_id == reseller_id)
            ).scalar()
        ) or 0

    def find_pending_before(self, before: datetime) -> list[ResellerCommission]:
        models = self.session.execute(
            select(ResellerCommissionModel)
            .where(
                ResellerCommissionModel.status == CommissionStatus.PENDING.value,
                ResellerCommissionModel.created_at <= before,
            )
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def sum_confirmed_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.coalesce(func.sum(ResellerCommissionModel.commission_amount_cents), 0))
                .where(
                    ResellerCommissionModel.reseller_id == reseller_id,
                    ResellerCommissionModel.status == CommissionStatus.CONFIRMED.value,
                )
            ).scalar()
        ) or 0

    def sum_clawbacks_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.coalesce(func.sum(ResellerCommissionModel.commission_amount_cents), 0))
                .where(
                    ResellerCommissionModel.reseller_id == reseller_id,
                    ResellerCommissionModel.status == CommissionStatus.CLAWED_BACK.value,
                )
            ).scalar()
        ) or 0

    def sum_paid_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.coalesce(func.sum(ResellerCommissionModel.commission_amount_cents), 0))
                .where(
                    ResellerCommissionModel.reseller_id == reseller_id,
                    ResellerCommissionModel.status == CommissionStatus.PAID.value,
                )
            ).scalar()
        ) or 0

    def sum_all_commissions_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.coalesce(func.sum(ResellerCommissionModel.commission_amount_cents), 0))
                .where(
                    ResellerCommissionModel.reseller_id == reseller_id,
                    ResellerCommissionModel.status.in_([
                        CommissionStatus.PENDING.value,
                        CommissionStatus.CONFIRMED.value,
                        CommissionStatus.PAID.value,
                    ]),
                )
            ).scalar()
        ) or 0

    def mark_confirmed_as_paid_for_reseller(self, reseller_id: str) -> int:
        result = self.session.execute(
            update(ResellerCommissionModel)
            .where(
                ResellerCommissionModel.reseller_id == reseller_id,
                ResellerCommissionModel.status == CommissionStatus.CONFIRMED.value,
            )
            .values(status=CommissionStatus.PAID.value)
        )
        self.session.flush()
        return result.rowcount

    @staticmethod
    def _to_entity(model: ResellerCommissionModel) -> ResellerCommission:
        return ResellerCommission(
            id=model.id,
            reseller_id=model.reseller_id,
            reseller_client_id=model.reseller_client_id,
            company_id=model.company_id,
            payment_amount_cents=model.payment_amount_cents,
            commission_pct=model.commission_pct,
            commission_amount_cents=model.commission_amount_cents,
            stripe_invoice_id=model.stripe_invoice_id,
            period_start=model.period_start,
            period_end=model.period_end,
            status=CommissionStatus(model.status),
            created_at=model.created_at,
        )
