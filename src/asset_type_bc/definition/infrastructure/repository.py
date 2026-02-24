from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.asset_type_bc.definition.domain.entities import AssetTypeDefinition
from src.asset_type_bc.definition.domain.repository import (
    AssetTypeDefinitionRepositoryInterface,
)
from src.asset_type_bc.definition.infrastructure.models import (
    AssetTypeDefinitionModel,
)


class AssetTypeDefinitionRepository(AssetTypeDefinitionRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def _model_to_entity(
        self, m: AssetTypeDefinitionModel
    ) -> AssetTypeDefinition:
        return AssetTypeDefinition(
            id=m.id,
            company_id=m.company_id,
            code=m.code,
            name=m.name,
            icon=m.icon,
            is_active=m.is_active,
            sort_order=m.sort_order,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def save(self, definition: AssetTypeDefinition) -> None:
        existing = self.session.execute(
            select(AssetTypeDefinitionModel).where(
                AssetTypeDefinitionModel.id == definition.id
            )
        ).scalar_one_or_none()

        if existing:
            existing.code = definition.code
            existing.name = definition.name
            existing.icon = definition.icon
            existing.is_active = definition.is_active
            existing.sort_order = definition.sort_order
            existing.updated_at = definition.updated_at
        else:
            model = AssetTypeDefinitionModel(
                id=definition.id,
                company_id=definition.company_id,
                code=definition.code,
                name=definition.name,
                icon=definition.icon,
                is_active=definition.is_active,
                sort_order=definition.sort_order,
                created_at=definition.created_at,
                updated_at=definition.updated_at,
            )
            self.session.add(model)
        self.session.flush()

    def find_by_id(
        self, id: str, company_id: str
    ) -> Optional[AssetTypeDefinition]:
        m = self.session.execute(
            select(AssetTypeDefinitionModel).where(
                AssetTypeDefinitionModel.id == id,
                AssetTypeDefinitionModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._model_to_entity(m) if m else None

    def find_by_code(
        self, code: str, company_id: str
    ) -> Optional[AssetTypeDefinition]:
        m = self.session.execute(
            select(AssetTypeDefinitionModel).where(
                AssetTypeDefinitionModel.code == code,
                AssetTypeDefinitionModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._model_to_entity(m) if m else None

    def find_all(
        self, company_id: str
    ) -> list[AssetTypeDefinition]:
        models = (
            self.session.execute(
                select(AssetTypeDefinitionModel)
                .where(
                    AssetTypeDefinitionModel.company_id == company_id,
                )
                .order_by(AssetTypeDefinitionModel.sort_order)
            )
            .scalars()
            .all()
        )
        return [self._model_to_entity(m) for m in models]

    def find_active(
        self, company_id: str
    ) -> list[AssetTypeDefinition]:
        models = (
            self.session.execute(
                select(AssetTypeDefinitionModel)
                .where(
                    AssetTypeDefinitionModel.company_id == company_id,
                    AssetTypeDefinitionModel.is_active.is_(True),
                )
                .order_by(AssetTypeDefinitionModel.sort_order)
            )
            .scalars()
            .all()
        )
        return [self._model_to_entity(m) for m in models]

    def has_code(self, company_id: str, code: str) -> bool:
        result = self.session.execute(
            select(AssetTypeDefinitionModel.id).where(
                AssetTypeDefinitionModel.company_id == company_id,
                AssetTypeDefinitionModel.code == code,
            )
        ).scalar_one_or_none()
        return result is not None

    def delete(self, id: str) -> None:
        model = self.session.execute(
            select(AssetTypeDefinitionModel).where(
                AssetTypeDefinitionModel.id == id
            )
        ).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()

    def bulk_update_sort_order(
        self, updates: list[tuple[str, int]]
    ) -> None:
        for definition_id, sort_order in updates:
            model = self.session.execute(
                select(AssetTypeDefinitionModel).where(
                    AssetTypeDefinitionModel.id == definition_id
                )
            ).scalar_one_or_none()
            if model:
                model.sort_order = sort_order
        self.session.flush()
