from abc import ABC, abstractmethod
from typing import Optional

from src.company_bc.classification_config.domain.entities import (
    CompanyClassificationConfig,
)


class ClassificationConfigRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, config: CompanyClassificationConfig,
    ) -> CompanyClassificationConfig: ...

    @abstractmethod
    def find_by_company(
        self, company_id: str,
    ) -> Optional[CompanyClassificationConfig]: ...
