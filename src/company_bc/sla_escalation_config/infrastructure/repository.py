from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.company_bc.sla_escalation_config.domain.entities import (
    CompanySlaEscalationConfig,
)
from src.company_bc.sla_escalation_config.domain.repository import (
    SlaEscalationConfigRepositoryInterface,
)
from src.company_bc.sla_escalation_config.infrastructure.models import (
    SlaEscalationConfigModel,
)


class SlaEscalationConfigRepository(SlaEscalationConfigRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, config: CompanySlaEscalationConfig,
    ) -> CompanySlaEscalationConfig:
        existing = self.session.execute(
            select(SlaEscalationConfigModel).where(
                SlaEscalationConfigModel.company_id == config.company_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.enabled = config.enabled
        else:
            model = SlaEscalationConfigModel(
                id=config.id,
                company_id=config.company_id,
                enabled=config.enabled,
            )
            self.session.add(model)

        self.session.flush()
        return config

    def find_by_company(
        self, company_id: str,
    ) -> Optional[CompanySlaEscalationConfig]:
        model = self.session.execute(
            select(SlaEscalationConfigModel).where(
                SlaEscalationConfigModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(
        model: SlaEscalationConfigModel,
    ) -> CompanySlaEscalationConfig:
        return CompanySlaEscalationConfig(
            id=model.id,
            company_id=model.company_id,
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
