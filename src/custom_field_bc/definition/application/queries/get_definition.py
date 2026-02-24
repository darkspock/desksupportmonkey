from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.custom_field_bc.definition.domain.exceptions import (
    FieldDefinitionNotFoundError,
)
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)
from src.custom_field_bc.definition.application.queries.list_definitions import (
    FieldDefinitionDto,
)


@dataclass
class GetFieldDefinitionQuery(Query):
    definition_id: str
    company_id: str


class GetFieldDefinitionQueryHandler(
    QueryHandler[GetFieldDefinitionQuery, FieldDefinitionDto]
):
    def __init__(self, repo: CustomFieldDefinitionRepositoryInterface):
        self.repo = repo

    def handle(self, query: GetFieldDefinitionQuery) -> FieldDefinitionDto:
        definition = self.repo.find_by_id(
            query.definition_id, query.company_id
        )
        if not definition:
            raise FieldDefinitionNotFoundError(query.definition_id)

        return FieldDefinitionDto(
            id=definition.id,
            company_id=definition.company_id,
            entity_type=definition.entity_type,
            field_key=definition.field_key,
            label=definition.label,
            description=definition.description,
            field_type=definition.field_type,
            options=definition.options,
            required=definition.required,
            sort_order=definition.sort_order,
            is_active=definition.is_active,
            visible_to_employees=definition.visible_to_employees,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )
