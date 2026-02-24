from abc import ABC, abstractmethod
from typing import Optional

from src.asset_type_bc.definition.domain.entities import AssetTypeDefinition


class AssetTypeDefinitionRepositoryInterface(ABC):
    @abstractmethod
    def save(self, definition: AssetTypeDefinition) -> None:
        ...

    @abstractmethod
    def find_by_id(
        self, id: str, company_id: str
    ) -> Optional[AssetTypeDefinition]:
        ...

    @abstractmethod
    def find_by_code(
        self, code: str, company_id: str
    ) -> Optional[AssetTypeDefinition]:
        ...

    @abstractmethod
    def find_all(self, company_id: str) -> list[AssetTypeDefinition]:
        ...

    @abstractmethod
    def find_active(self, company_id: str) -> list[AssetTypeDefinition]:
        ...

    @abstractmethod
    def has_code(self, company_id: str, code: str) -> bool:
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        ...

    @abstractmethod
    def bulk_update_sort_order(
        self, updates: list[tuple[str, int]]
    ) -> None:
        ...
