from abc import ABC, abstractmethod
from typing import Optional

from src.workflow_bc.checklist.domain.entities import RequestChecklistItem


class ChecklistItemRepositoryInterface(ABC):
    @abstractmethod
    def save(self, item: RequestChecklistItem) -> None:
        ...

    @abstractmethod
    def save_all(self, items: list[RequestChecklistItem]) -> None:
        ...

    @abstractmethod
    def find_by_id(self, item_id: str) -> Optional[RequestChecklistItem]:
        ...

    @abstractmethod
    def find_by_request(self, request_id: str) -> list[RequestChecklistItem]:
        ...

    @abstractmethod
    def delete(self, item_id: str) -> None:
        ...
