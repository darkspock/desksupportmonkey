from abc import ABC, abstractmethod
from typing import Optional

from src.company_bc.nav_config.domain.entities import CompanyNavConfig


class NavConfigRepositoryInterface(ABC):

    @abstractmethod
    def save(
        self, config: CompanyNavConfig,
    ) -> CompanyNavConfig: ...

    @abstractmethod
    def find_by_company(
        self, company_id: str,
    ) -> Optional[CompanyNavConfig]: ...
