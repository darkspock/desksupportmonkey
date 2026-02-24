from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)


@dataclass
class FieldDefinitionDto:
    id: str
    company_id: str
    entity_type: str
    field_key: str
    label: str
    description: Optional[str]
    field_type: str
    options: Optional[list[str]]
    required: bool
    sort_order: int
    is_active: bool
    visible_to_employees: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class ListFieldDefinitionsQuery(Query):
    company_id: str
    entity_type: str


class ListFieldDefinitionsQueryHandler(
    QueryHandler[ListFieldDefinitionsQuery, list[FieldDefinitionDto]]
):
    def __init__(self, repo: CustomFieldDefinitionRepositoryInterface):
        self.repo = repo

    def handle(
        self, query: ListFieldDefinitionsQuery
    ) -> list[FieldDefinitionDto]:
        definitions = self.repo.find_by_entity_type(
            company_id=query.company_id,
            entity_type=query.entity_type,
        )
        return [
            FieldDefinitionDto(
                id=d.id,
                company_id=d.company_id,
                entity_type=d.entity_type,
                field_key=d.field_key,
                label=d.label,
                description=d.description,
                field_type=d.field_type,
                options=d.options,
                required=d.required,
                sort_order=d.sort_order,
                is_active=d.is_active,
                visible_to_employees=d.visible_to_employees,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in definitions
        ]
