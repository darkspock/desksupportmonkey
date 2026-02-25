from abc import ABC, abstractmethod
from typing import Optional

from src.workflow_bc.template.domain.entities import WorkflowTemplate


class WorkflowTemplateRepositoryInterface(ABC):
    @abstractmethod
    def save(self, template: WorkflowTemplate) -> None:
        ...

    @abstractmethod
    def find_by_id(self, id: str, company_id: str) -> Optional[WorkflowTemplate]:
        ...

    @abstractmethod
    def find_by_company(
        self, company_id: str, active_only: bool = False
    ) -> list[WorkflowTemplate]:
        ...

    @abstractmethod
    def find_by_name(
        self, company_id: str, name: str
    ) -> Optional[WorkflowTemplate]:
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        ...

    @abstractmethod
    def has_requests(self, template_id: str) -> bool:
        ...
