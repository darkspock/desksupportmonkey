from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.reseller_bc.payout.domain.entities import ResellerPayout
from src.reseller_bc.payout.domain.enums import PayoutStatus
from src.reseller_bc.payout.domain.repository import ResellerPayoutRepositoryInterface
from src.reseller_bc.payout.infrastructure.models import ResellerPayoutModel


class ResellerPayoutRepository(ResellerPayoutRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, payout: ResellerPayout) -> None:
        existing = self.session.execute(
            select(ResellerPayoutModel).where(ResellerPayoutModel.id == payout.id)
        ).scalar_one_or_none()
        if existing:
            existing.reseller_id = payout.reseller_id
            existing.amount_cents = payout.amount_cents
            existing.status = payout.status.value
            existing.requested_at = payout.requested_at  # type: ignore[assignment]
            existing.processed_at = payout.processed_at  # type: ignore[assignment]
            existing.processed_by = payout.processed_by
            existing.payment_reference = payout.payment_reference
            existing.notes = payout.notes
        else:
            model = ResellerPayoutModel(
                id=payout.id,
                reseller_id=payout.reseller_id,
                amount_cents=payout.amount_cents,
                status=payout.status.value,
                requested_at=payout.requested_at,
                processed_at=payout.processed_at,
                processed_by=payout.processed_by,
                payment_reference=payout.payment_reference,
                notes=payout.notes,
            )
            self.session.add(model)
        self.session.flush()

    def find_by_id(self, payout_id: str) -> Optional[ResellerPayout]:
        model = self.session.execute(
            select(ResellerPayoutModel).where(ResellerPayoutModel.id == payout_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerPayout]:
        models = self.session.execute(
            select(ResellerPayoutModel)
            .where(ResellerPayoutModel.reseller_id == reseller_id)
            .order_by(ResellerPayoutModel.requested_at.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(ResellerPayoutModel)
                .where(ResellerPayoutModel.reseller_id == reseller_id)
            ).scalar()
        ) or 0

    def find_active_by_reseller_id(self, reseller_id: str) -> Optional[ResellerPayout]:
        model = self.session.execute(
            select(ResellerPayoutModel)
            .where(
                ResellerPayoutModel.reseller_id == reseller_id,
                ResellerPayoutModel.status.in_([
                    PayoutStatus.REQUESTED.value,
                    PayoutStatus.APPROVED.value,
                ]),
            )
            .limit(1)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all(self, offset: int = 0, limit: int = 50, reseller_id: Optional[str] = None) -> list[ResellerPayout]:
        stmt = select(ResellerPayoutModel)
        if reseller_id:
            stmt = stmt.where(ResellerPayoutModel.reseller_id == reseller_id)
        stmt = stmt.order_by(ResellerPayoutModel.requested_at.desc()).offset(offset).limit(limit)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_all(self, reseller_id: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(ResellerPayoutModel)
        if reseller_id:
            stmt = stmt.where(ResellerPayoutModel.reseller_id == reseller_id)
        return self.session.execute(stmt).scalar() or 0

    def sum_requested_and_approved_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.coalesce(func.sum(ResellerPayoutModel.amount_cents), 0))
                .where(
                    ResellerPayoutModel.reseller_id == reseller_id,
                    ResellerPayoutModel.status.in_([
                        PayoutStatus.REQUESTED.value,
                        PayoutStatus.APPROVED.value,
                    ]),
                )
            ).scalar()
        ) or 0

    @staticmethod
    def _to_entity(model: ResellerPayoutModel) -> ResellerPayout:
        return ResellerPayout(
            id=model.id,
            reseller_id=model.reseller_id,
            amount_cents=model.amount_cents,
            status=PayoutStatus(model.status),
            requested_at=model.requested_at,
            processed_at=model.processed_at,
            processed_by=model.processed_by,
            payment_reference=model.payment_reference,
            notes=model.notes,
        )
