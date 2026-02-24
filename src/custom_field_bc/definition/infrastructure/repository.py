from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition
from src.custom_field_bc.definition.domain.repository import (
    CustomFieldDefinitionRepositoryInterface,
)
from src.custom_field_bc.definition.infrastructure.models import (
    CustomFieldDefinitionModel,
)


class CustomFieldDefinitionRepository(CustomFieldDefinitionRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def _model_to_entity(self, m: CustomFieldDefinitionModel) -> CustomFieldDefinition:
        return CustomFieldDefinition(
            id=m.id,
            company_id=m.company_id,
            entity_type=m.entity_type,
            field_key=m.field_key,
            label=m.label,
            description=m.description,
            field_type=m.field_type,
            options=m.options,
            required=m.required,
            sort_order=m.sort_order,
            is_active=m.is_active,
            visible_to_employees=m.visible_to_employees,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def save(self, definition: CustomFieldDefinition) -> None:
        existing = self.session.execute(
            select(CustomFieldDefinitionModel).where(
                CustomFieldDefinitionModel.id == definition.id
            )
        ).scalar_one_or_none()

        if existing:
            existing.label = definition.label
            existing.description = definition.description
            existing.options = definition.options
            existing.required = definition.required
            existing.sort_order = definition.sort_order
            existing.is_active = definition.is_active
            existing.visible_to_employees = definition.visible_to_employees
            existing.updated_at = definition.updated_at
        else:
            model = CustomFieldDefinitionModel(
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
            self.session.add(model)
        self.session.flush()

    def find_by_id(
        self, id: str, company_id: str
    ) -> Optional[CustomFieldDefinition]:
        m = self.session.execute(
            select(CustomFieldDefinitionModel).where(
                CustomFieldDefinitionModel.id == id,
                CustomFieldDefinitionModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._model_to_entity(m) if m else None

    def find_by_entity_type(
        self, company_id: str, entity_type: str
    ) -> list[CustomFieldDefinition]:
        models = (
            self.session.execute(
                select(CustomFieldDefinitionModel)
                .where(
                    CustomFieldDefinitionModel.company_id == company_id,
                    CustomFieldDefinitionModel.entity_type == entity_type,
                )
                .order_by(CustomFieldDefinitionModel.sort_order)
            )
            .scalars()
            .all()
        )
        return [self._model_to_entity(m) for m in models]

    def find_active_by_entity_type(
        self, company_id: str, entity_type: str
    ) -> list[CustomFieldDefinition]:
        models = (
            self.session.execute(
                select(CustomFieldDefinitionModel)
                .where(
                    CustomFieldDefinitionModel.company_id == company_id,
                    CustomFieldDefinitionModel.entity_type == entity_type,
                    CustomFieldDefinitionModel.is_active.is_(True),
                )
                .order_by(CustomFieldDefinitionModel.sort_order)
            )
            .scalars()
            .all()
        )
        return [self._model_to_entity(m) for m in models]

    def count_by_entity_type(self, company_id: str, entity_type: str) -> int:
        result = self.session.execute(
            select(func.count())
            .select_from(CustomFieldDefinitionModel)
            .where(
                CustomFieldDefinitionModel.company_id == company_id,
                CustomFieldDefinitionModel.entity_type == entity_type,
            )
        ).scalar()
        return result or 0

    def has_field_key(
        self, company_id: str, entity_type: str, field_key: str
    ) -> bool:
        result = self.session.execute(
            select(CustomFieldDefinitionModel.id).where(
                CustomFieldDefinitionModel.company_id == company_id,
                CustomFieldDefinitionModel.entity_type == entity_type,
                CustomFieldDefinitionModel.field_key == field_key,
            )
        ).scalar_one_or_none()
        return result is not None

    def delete(self, id: str) -> None:
        model = self.session.execute(
            select(CustomFieldDefinitionModel).where(
                CustomFieldDefinitionModel.id == id
            )
        ).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()

    def bulk_update_sort_order(self, updates: list[tuple[str, int]]) -> None:
        for definition_id, sort_order in updates:
            model = self.session.execute(
                select(CustomFieldDefinitionModel).where(
                    CustomFieldDefinitionModel.id == definition_id
                )
            ).scalar_one_or_none()
            if model:
                model.sort_order = sort_order
        self.session.flush()
