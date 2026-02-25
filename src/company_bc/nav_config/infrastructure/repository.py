from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.company_bc.nav_config.domain.entities import CompanyNavConfig
from src.company_bc.nav_config.domain.repository import (
    NavConfigRepositoryInterface,
)
from src.company_bc.nav_config.infrastructure.models import NavConfigModel


class NavConfigRepository(NavConfigRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, config: CompanyNavConfig,
    ) -> CompanyNavConfig:
        existing = self.session.execute(
            select(NavConfigModel).where(
                NavConfigModel.company_id == config.company_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.hidden_nav_items = config.hidden_nav_items
        else:
            model = NavConfigModel(
                id=config.id,
                company_id=config.company_id,
                hidden_nav_items=config.hidden_nav_items,
            )
            self.session.add(model)

        self.session.flush()
        return config

    def find_by_company(
        self, company_id: str,
    ) -> Optional[CompanyNavConfig]:
        model = self.session.execute(
            select(NavConfigModel).where(
                NavConfigModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: NavConfigModel) -> CompanyNavConfig:
        return CompanyNavConfig(
            id=model.id,
            company_id=model.company_id,
            hidden_nav_items=model.hidden_nav_items or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
