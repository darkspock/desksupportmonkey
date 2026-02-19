from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.company_bc.assignment_config.domain.enums import AIProvider
from src.company_bc.classification_config.domain.entities import (
    CompanyClassificationConfig,
)
from src.company_bc.classification_config.domain.repository import (
    ClassificationConfigRepositoryInterface,
)
from src.company_bc.classification_config.infrastructure.models import (
    ClassificationConfigModel,
)


class ClassificationConfigRepository(ClassificationConfigRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, config: CompanyClassificationConfig,
    ) -> CompanyClassificationConfig:
        existing = self.session.execute(
            select(ClassificationConfigModel).where(
                ClassificationConfigModel.company_id == config.company_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.is_enabled = config.is_enabled
            existing.provider = config.provider.value
            existing.model = config.model
            existing.confidence_threshold = config.confidence_threshold
            existing.prompt_template = config.prompt_template
            existing.timeout_seconds = config.timeout_seconds
        else:
            model = ClassificationConfigModel(
                id=config.id,
                company_id=config.company_id,
                is_enabled=config.is_enabled,
                provider=config.provider.value,
                model=config.model,
                confidence_threshold=config.confidence_threshold,
                prompt_template=config.prompt_template,
                timeout_seconds=config.timeout_seconds,
            )
            self.session.add(model)

        self.session.flush()
        return config

    def find_by_company(
        self, company_id: str,
    ) -> Optional[CompanyClassificationConfig]:
        model = self.session.execute(
            select(ClassificationConfigModel).where(
                ClassificationConfigModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(
        model: ClassificationConfigModel,
    ) -> CompanyClassificationConfig:
        return CompanyClassificationConfig(
            id=model.id,
            company_id=model.company_id,
            is_enabled=model.is_enabled,
            provider=AIProvider(model.provider),
            model=model.model,
            confidence_threshold=model.confidence_threshold,
            prompt_template=model.prompt_template,
            timeout_seconds=model.timeout_seconds,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
