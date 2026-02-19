from dataclasses import dataclass
from typing import Optional

from src.company_bc.classification_config.domain.repository import (
    ClassificationConfigRepositoryInterface,
)
from src.framework.application.query_bus import Query, QueryHandler


@dataclass(frozen=True)
class ClassificationConfigDTO:
    id: str
    company_id: str
    is_enabled: bool
    provider: str
    model: Optional[str]
    confidence_threshold: float
    prompt_template: Optional[str]
    timeout_seconds: int
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class GetClassificationConfigQuery(Query):
    company_id: str


class GetClassificationConfigQueryHandler(
    QueryHandler[GetClassificationConfigQuery, Optional[ClassificationConfigDTO]],
):
    def __init__(
        self,
        config_repo: ClassificationConfigRepositoryInterface,
    ):
        self.config_repo = config_repo

    def handle(
        self, query: GetClassificationConfigQuery,
    ) -> Optional[ClassificationConfigDTO]:
        config = self.config_repo.find_by_company(query.company_id)
        if not config:
            return None
        return ClassificationConfigDTO(
            id=config.id,
            company_id=config.company_id,
            is_enabled=config.is_enabled,
            provider=config.provider.value,
            model=config.model,
            confidence_threshold=config.confidence_threshold,
            prompt_template=config.prompt_template,
            timeout_seconds=config.timeout_seconds,
            created_at=str(config.created_at) if config.created_at else None,
            updated_at=str(config.updated_at) if config.updated_at else None,
        )
