from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface
from src.reseller_bc.reseller.infrastructure.models import ResellerModel


class ResellerRepository(ResellerRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, reseller: Reseller) -> None:
        existing = self.session.execute(
            select(ResellerModel).where(ResellerModel.id == reseller.id)
        ).scalar_one_or_none()
        if existing:
            existing.email = reseller.email
            existing.name = reseller.name
            existing.google_id = reseller.google_id
            existing.microsoft_id = reseller.microsoft_id
            existing.avatar_url = reseller.avatar_url
            existing.company_name = reseller.company_name
            existing.tax_id = reseller.tax_id
            existing.commission_pct = reseller.commission_pct
            existing.min_payout_cents = reseller.min_payout_cents
            existing.referral_code = reseller.referral_code
            existing.status = reseller.status.value
            existing.password_hash = reseller.password_hash
            existing.reset_token = reseller.reset_token
            existing.reset_token_expires_at = reseller.reset_token_expires_at
        else:
            model = ResellerModel(
                id=reseller.id,
                email=reseller.email,
                name=reseller.name,
                google_id=reseller.google_id,
                microsoft_id=reseller.microsoft_id,
                avatar_url=reseller.avatar_url,
                company_name=reseller.company_name,
                tax_id=reseller.tax_id,
                commission_pct=reseller.commission_pct,
                min_payout_cents=reseller.min_payout_cents,
                referral_code=reseller.referral_code,
                status=reseller.status.value,
                password_hash=reseller.password_hash,
                reset_token=reseller.reset_token,
                reset_token_expires_at=reseller.reset_token_expires_at,
            )
            self.session.add(model)
        self.session.flush()

    def get_by_id(self, reseller_id: str) -> Optional[Reseller]:
        model = self.session.execute(
            select(ResellerModel).where(ResellerModel.id == reseller_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_email(self, email: str) -> Optional[Reseller]:
        model = self.session.execute(
            select(ResellerModel).where(ResellerModel.email == email.lower().strip())
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_google_id(self, google_id: str) -> Optional[Reseller]:
        model = self.session.execute(
            select(ResellerModel).where(ResellerModel.google_id == google_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_microsoft_id(self, microsoft_id: str) -> Optional[Reseller]:
        model = self.session.execute(
            select(ResellerModel).where(ResellerModel.microsoft_id == microsoft_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_referral_code(self, code: str) -> Optional[Reseller]:
        model = self.session.execute(
            select(ResellerModel).where(ResellerModel.referral_code == code)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def list_all(self, offset: int, limit: int) -> list[Reseller]:
        models = self.session.execute(
            select(ResellerModel)
            .order_by(ResellerModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_all(self) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(ResellerModel)
            ).scalar()
        ) or 0

    def exists_by_email(self, email: str) -> bool:
        result = self.session.execute(
            select(ResellerModel.id).where(
                ResellerModel.email == email.lower().strip()
            ).limit(1)
        ).scalar_one_or_none()
        return result is not None

    def exists_by_referral_code(self, code: str) -> bool:
        result = self.session.execute(
            select(ResellerModel.id).where(
                ResellerModel.referral_code == code
            ).limit(1)
        ).scalar_one_or_none()
        return result is not None

    def find_by_reset_token(self, token: str) -> Optional[Reseller]:
        model = self.session.execute(
            select(ResellerModel).where(ResellerModel.reset_token == token)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: ResellerModel) -> Reseller:
        return Reseller(
            id=model.id,
            email=model.email,
            name=model.name,
            google_id=model.google_id,
            microsoft_id=model.microsoft_id,
            avatar_url=model.avatar_url,
            company_name=model.company_name,
            tax_id=model.tax_id,
            commission_pct=model.commission_pct,
            min_payout_cents=model.min_payout_cents,
            referral_code=model.referral_code,
            password_hash=model.password_hash,
            reset_token=model.reset_token,
            reset_token_expires_at=model.reset_token_expires_at,
            status=ResellerStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
