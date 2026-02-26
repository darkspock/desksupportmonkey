from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from src.asset_bc.checkout.domain.entities import AssetCheckout
from src.asset_bc.checkout.domain.enums import AssetCondition
from src.asset_bc.checkout.domain.repository import CheckoutRepositoryInterface
from src.asset_bc.checkout.infrastructure.models import AssetCheckoutModel


class CheckoutRepository(CheckoutRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, checkout: AssetCheckout) -> AssetCheckout:
        existing = self.session.execute(
            select(AssetCheckoutModel).where(AssetCheckoutModel.id == checkout.id)
        ).scalar_one_or_none()
        if existing:
            existing.user_id = checkout.user_id
            existing.checked_out_by = checkout.checked_out_by
            existing.checked_out_at = checkout.checked_out_at
            existing.condition_out = checkout.condition_out.value
            existing.condition_out_notes = checkout.condition_out_notes
            existing.notes_out = checkout.notes_out
            existing.accepted_at = checkout.accepted_at
            existing.checked_in_at = checkout.checked_in_at
            existing.checked_in_by = checkout.checked_in_by
            existing.condition_in = checkout.condition_in.value if checkout.condition_in else None
            existing.condition_in_notes = checkout.condition_in_notes
            existing.notes_in = checkout.notes_in
            existing.cancelled_at = checkout.cancelled_at
            existing.cancelled_by = checkout.cancelled_by
            existing.cancel_reason = checkout.cancel_reason
            existing.maintenance_id = checkout.maintenance_id
            existing.auto_assigned = checkout.auto_assigned
        else:
            model = AssetCheckoutModel(
                id=checkout.id,
                company_id=checkout.company_id,
                asset_id=checkout.asset_id,
                user_id=checkout.user_id,
                checked_out_by=checkout.checked_out_by,
                checked_out_at=checkout.checked_out_at,
                condition_out=checkout.condition_out.value,
                condition_out_notes=checkout.condition_out_notes,
                notes_out=checkout.notes_out,
                accepted_at=checkout.accepted_at,
                checked_in_at=checkout.checked_in_at,
                checked_in_by=checkout.checked_in_by,
                condition_in=checkout.condition_in.value if checkout.condition_in else None,
                condition_in_notes=checkout.condition_in_notes,
                notes_in=checkout.notes_in,
                cancelled_at=checkout.cancelled_at,
                cancelled_by=checkout.cancelled_by,
                cancel_reason=checkout.cancel_reason,
                maintenance_id=checkout.maintenance_id,
                auto_assigned=checkout.auto_assigned,
            )
            self.session.add(model)
            existing = model
        self.session.flush()
        self.session.refresh(existing)
        return self._to_entity(existing)

    def find_by_id(self, checkout_id: str, company_id: str) -> Optional[AssetCheckout]:
        model = self.session.execute(
            select(AssetCheckoutModel).where(
                AssetCheckoutModel.id == checkout_id,
                AssetCheckoutModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_active_by_asset(self, asset_id: str, company_id: str) -> Optional[AssetCheckout]:
        model = self.session.execute(
            select(AssetCheckoutModel).where(
                AssetCheckoutModel.asset_id == asset_id,
                AssetCheckoutModel.company_id == company_id,
                AssetCheckoutModel.checked_in_at.is_(None),
                AssetCheckoutModel.cancelled_at.is_(None),
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_asset(
        self,
        asset_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AssetCheckout], int]:
        base = select(AssetCheckoutModel).where(
            AssetCheckoutModel.asset_id == asset_id,
            AssetCheckoutModel.company_id == company_id,
        )
        total = self.session.execute(
            select(func.count()).select_from(base.subquery())
        ).scalar() or 0
        rows = self.session.execute(
            base.order_by(AssetCheckoutModel.checked_out_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(r) for r in rows], total

    def find_open_by_company(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> tuple[list[AssetCheckout], int]:
        conditions = [
            AssetCheckoutModel.company_id == company_id,
            AssetCheckoutModel.checked_in_at.is_(None),
            AssetCheckoutModel.cancelled_at.is_(None),
        ]
        if user_id:
            conditions.append(AssetCheckoutModel.user_id == user_id)
        if asset_id:
            conditions.append(AssetCheckoutModel.asset_id == asset_id)

        base = select(AssetCheckoutModel).where(and_(*conditions))
        total = self.session.execute(
            select(func.count()).select_from(base.subquery())
        ).scalar() or 0
        rows = self.session.execute(
            base.order_by(AssetCheckoutModel.checked_out_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(r) for r in rows], total

    def find_pending_acceptance_by_user(
        self,
        user_id: str,
        company_id: str,
    ) -> list[AssetCheckout]:
        rows = self.session.execute(
            select(AssetCheckoutModel).where(
                AssetCheckoutModel.user_id == user_id,
                AssetCheckoutModel.company_id == company_id,
                AssetCheckoutModel.checked_in_at.is_(None),
                AssetCheckoutModel.cancelled_at.is_(None),
                AssetCheckoutModel.accepted_at.is_(None),
            ).order_by(AssetCheckoutModel.checked_out_at.desc())
        ).scalars().all()
        return [self._to_entity(r) for r in rows]

    def find_open_by_user(
        self,
        user_id: str,
        company_id: str,
    ) -> list[AssetCheckout]:
        rows = self.session.execute(
            select(AssetCheckoutModel).where(
                AssetCheckoutModel.user_id == user_id,
                AssetCheckoutModel.company_id == company_id,
                AssetCheckoutModel.checked_in_at.is_(None),
                AssetCheckoutModel.cancelled_at.is_(None),
            ).order_by(AssetCheckoutModel.checked_out_at.desc())
        ).scalars().all()
        return [self._to_entity(r) for r in rows]

    def find_history_by_user(
        self,
        user_id: str,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AssetCheckout], int]:
        base = select(AssetCheckoutModel).where(
            AssetCheckoutModel.user_id == user_id,
            AssetCheckoutModel.company_id == company_id,
            AssetCheckoutModel.checked_in_at.isnot(None)
            | AssetCheckoutModel.cancelled_at.isnot(None),
        )
        total = self.session.execute(
            select(func.count()).select_from(base.subquery())
        ).scalar() or 0
        rows = self.session.execute(
            base.order_by(AssetCheckoutModel.checked_out_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(r) for r in rows], total

    def count_open_by_company(self, company_id: str) -> int:
        return self.session.execute(
            select(func.count()).select_from(
                select(AssetCheckoutModel).where(
                    AssetCheckoutModel.company_id == company_id,
                    AssetCheckoutModel.checked_in_at.is_(None),
                    AssetCheckoutModel.cancelled_at.is_(None),
                ).subquery()
            )
        ).scalar() or 0

    def count_pending_acceptance_by_company(self, company_id: str) -> int:
        return self.session.execute(
            select(func.count()).select_from(
                select(AssetCheckoutModel).where(
                    AssetCheckoutModel.company_id == company_id,
                    AssetCheckoutModel.checked_in_at.is_(None),
                    AssetCheckoutModel.cancelled_at.is_(None),
                    AssetCheckoutModel.accepted_at.is_(None),
                ).subquery()
            )
        ).scalar() or 0

    def find_unaccepted_older_than_days(
        self,
        company_id: str,
        days: int,
    ) -> list[AssetCheckout]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = self.session.execute(
            select(AssetCheckoutModel).where(
                AssetCheckoutModel.company_id == company_id,
                AssetCheckoutModel.checked_in_at.is_(None),
                AssetCheckoutModel.cancelled_at.is_(None),
                AssetCheckoutModel.accepted_at.is_(None),
                AssetCheckoutModel.checked_out_at <= cutoff,
            ).order_by(AssetCheckoutModel.checked_out_at.asc())
        ).scalars().all()
        return [self._to_entity(r) for r in rows]

    def _to_entity(self, model: AssetCheckoutModel) -> AssetCheckout:
        return AssetCheckout(
            id=model.id,
            company_id=model.company_id,
            asset_id=model.asset_id,
            user_id=model.user_id,
            checked_out_by=model.checked_out_by,
            checked_out_at=model.checked_out_at,
            condition_out=AssetCondition(model.condition_out),
            condition_out_notes=model.condition_out_notes,
            notes_out=model.notes_out,
            accepted_at=model.accepted_at,
            checked_in_at=model.checked_in_at,
            checked_in_by=model.checked_in_by,
            condition_in=AssetCondition(model.condition_in) if model.condition_in else None,
            condition_in_notes=model.condition_in_notes,
            notes_in=model.notes_in,
            cancelled_at=model.cancelled_at,
            cancelled_by=model.cancelled_by,
            cancel_reason=model.cancel_reason,
            maintenance_id=model.maintenance_id,
            auto_assigned=model.auto_assigned,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
