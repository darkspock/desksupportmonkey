from abc import ABC, abstractmethod
from typing import Optional

from src.company_bc.sla_escalation_config.domain.entities import (
    CompanySlaEscalationConfig,
)


class SlaEscalationConfigRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, config: CompanySlaEscalationConfig,
    ) -> CompanySlaEscalationConfig: ...

    @abstractmethod
    def find_by_company(
        self, company_id: str,
    ) -> Optional[CompanySlaEscalationConfig]: ...
