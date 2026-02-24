from abc import ABC, abstractmethod
from typing import Optional

from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition


class CustomFieldDefinitionRepositoryInterface(ABC):
    @abstractmethod
    def save(self, definition: CustomFieldDefinition) -> None:
        ...

    @abstractmethod
    def find_by_id(self, id: str, company_id: str) -> Optional[CustomFieldDefinition]:
        ...

    @abstractmethod
    def find_by_entity_type(
        self, company_id: str, entity_type: str
    ) -> list[CustomFieldDefinition]:
        ...

    @abstractmethod
    def find_active_by_entity_type(
        self, company_id: str, entity_type: str
    ) -> list[CustomFieldDefinition]:
        ...

    @abstractmethod
    def count_by_entity_type(self, company_id: str, entity_type: str) -> int:
        ...

    @abstractmethod
    def has_field_key(
        self, company_id: str, entity_type: str, field_key: str
    ) -> bool:
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        ...

    @abstractmethod
    def bulk_update_sort_order(self, updates: list[tuple[str, int]]) -> None:
        ...
