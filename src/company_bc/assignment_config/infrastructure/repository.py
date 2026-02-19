from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.company_bc.assignment_config.domain.entities import (
    CompanyAssignmentAIConfig,
)
from src.company_bc.assignment_config.domain.enums import (
    AIProvider,
)
from src.company_bc.assignment_config.domain.repository import (
    AssignmentConfigRepositoryInterface,
)
from src.company_bc.assignment_config.infrastructure.models import (
    AssignmentAIConfigModel,
)


class AssignmentConfigRepository(
    AssignmentConfigRepositoryInterface,
):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, config: CompanyAssignmentAIConfig,
    ) -> CompanyAssignmentAIConfig:
        existing = self.session.execute(
            select(AssignmentAIConfigModel).where(
                AssignmentAIConfigModel.company_id
                == config.company_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.provider = config.provider.value
            existing.prompt_template = (
                config.prompt_template
            )
            existing.model = config.model
        else:
            model = AssignmentAIConfigModel(
                id=config.id,
                company_id=config.company_id,
                provider=config.provider.value,
                prompt_template=config.prompt_template,
                model=config.model,
            )
            self.session.add(model)

        self.session.flush()
        return config

    def find_by_company(
        self, company_id: str,
    ) -> Optional[CompanyAssignmentAIConfig]:
        model = self.session.execute(
            select(AssignmentAIConfigModel).where(
                AssignmentAIConfigModel.company_id
                == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(
        model: AssignmentAIConfigModel,
    ) -> CompanyAssignmentAIConfig:
        return CompanyAssignmentAIConfig(
            id=model.id,
            company_id=model.company_id,
            provider=AIProvider(model.provider),
            prompt_template=model.prompt_template,
            model=model.model,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
