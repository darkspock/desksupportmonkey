from abc import ABC, abstractmethod
from typing import Optional

from src.company_bc.assignment_config.domain.entities import (
    CompanyAssignmentAIConfig,
)


class AssignmentConfigRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, config: CompanyAssignmentAIConfig,
    ) -> CompanyAssignmentAIConfig: ...

    @abstractmethod
    def find_by_company(
        self, company_id: str,
    ) -> Optional[CompanyAssignmentAIConfig]: ...
