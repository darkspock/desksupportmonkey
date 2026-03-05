from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from src.company_bc.company.infrastructure.models import CompanyModel
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface
from src.reseller_bc.client.infrastructure.models import ResellerClientModel


class ResellerClientRepository(ResellerClientRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, client: ResellerClient) -> None:
        existing = self.session.execute(
            select(ResellerClientModel).where(ResellerClientModel.id == client.id)
        ).scalar_one_or_none()
        if existing:
            existing.reseller_id = client.reseller_id
            existing.company_id = client.company_id
            existing.source = client.source.value
            existing.is_demo = client.is_demo
            existing.demo_expires_at = client.demo_expires_at
        else:
            model = ResellerClientModel(
                id=client.id,
                reseller_id=client.reseller_id,
                company_id=client.company_id,
                source=client.source.value,
                is_demo=client.is_demo,
                demo_expires_at=client.demo_expires_at,
            )
            self.session.add(model)
        self.session.flush()

    def get_by_id(self, client_id: str) -> Optional[ResellerClient]:
        model = self.session.execute(
            select(ResellerClientModel).where(ResellerClientModel.id == client_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_company_id(self, company_id: str) -> Optional[ResellerClient]:
        model = self.session.execute(
            select(ResellerClientModel).where(ResellerClientModel.company_id == company_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerClient]:
        models = self.session.execute(
            select(ResellerClientModel)
            .where(ResellerClientModel.reseller_id == reseller_id)
            .order_by(ResellerClientModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(ResellerClientModel)
                .where(ResellerClientModel.reseller_id == reseller_id)
            ).scalar()
        ) or 0

    def count_active_demos_by_reseller_id(self, reseller_id: str) -> int:
        now = datetime.utcnow()
        return (
            self.session.execute(
                select(func.count()).select_from(ResellerClientModel)
                .where(and_(
                    ResellerClientModel.reseller_id == reseller_id,
                    ResellerClientModel.is_demo.is_(True),
                    ResellerClientModel.demo_expires_at > now,
                ))
            ).scalar()
        ) or 0

    def find_expired_demos(self, before: datetime) -> list[ResellerClient]:
        models = self.session.execute(
            select(ResellerClientModel)
            .join(CompanyModel, CompanyModel.id == ResellerClientModel.company_id)
            .where(and_(
                ResellerClientModel.is_demo.is_(True),
                ResellerClientModel.demo_expires_at <= before,
                CompanyModel.status == "active",
            ))
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def find_purgeable_demos(self, before: datetime) -> list[ResellerClient]:
        models = self.session.execute(
            select(ResellerClientModel)
            .join(CompanyModel, CompanyModel.id == ResellerClientModel.company_id)
            .where(and_(
                ResellerClientModel.is_demo.is_(True),
                ResellerClientModel.demo_expires_at <= before,
                CompanyModel.status == "suspended",
            ))
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(model: ResellerClientModel) -> ResellerClient:
        return ResellerClient(
            id=model.id,
            reseller_id=model.reseller_id,
            company_id=model.company_id,
            source=ClientSource(model.source),
            is_demo=model.is_demo,
            demo_expires_at=model.demo_expires_at,
            created_at=model.created_at,
        )
