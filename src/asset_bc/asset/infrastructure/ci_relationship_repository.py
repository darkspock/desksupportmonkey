from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.asset_bc.asset.domain.entities import CIRelationship
from src.asset_bc.asset.domain.enums import CIRelationshipType
from src.asset_bc.asset.domain.repository import CIRelationshipRepositoryInterface
from src.asset_bc.asset.infrastructure.models import AssetModel, CIRelationshipModel


class CIRelationshipRepository(CIRelationshipRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, relationship: CIRelationship) -> CIRelationship:
        existing = self.session.execute(
            select(CIRelationshipModel).where(CIRelationshipModel.id == relationship.id)
        ).scalar_one_or_none()
        if existing:
            existing.description = relationship.description
            existing.relationship_type = relationship.relationship_type.value
        else:
            model = CIRelationshipModel(
                id=relationship.id,
                company_id=relationship.company_id,
                source_asset_id=relationship.source_asset_id,
                target_asset_id=relationship.target_asset_id,
                relationship_type=relationship.relationship_type.value,
                description=relationship.description,
                created_by=relationship.created_by,
            )
            self.session.add(model)
            existing = model
        self.session.flush()
        self.session.refresh(existing)
        return self._to_entity(existing)

    def find_by_id(self, relationship_id: str, company_id: str) -> Optional[CIRelationship]:
        model = self.session.execute(
            select(CIRelationshipModel).where(
                CIRelationshipModel.id == relationship_id,
                CIRelationshipModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_asset(self, asset_id: str, company_id: str) -> list[CIRelationship]:
        models = self.session.execute(
            select(CIRelationshipModel).where(
                CIRelationshipModel.company_id == company_id,
                or_(
                    CIRelationshipModel.source_asset_id == asset_id,
                    CIRelationshipModel.target_asset_id == asset_id,
                ),
            ).order_by(CIRelationshipModel.created_at.asc())
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def find_duplicate(
        self,
        source_asset_id: str,
        target_asset_id: str,
        relationship_type: str,
        company_id: str,
    ) -> Optional[CIRelationship]:
        model = self.session.execute(
            select(CIRelationshipModel).where(
                CIRelationshipModel.source_asset_id == source_asset_id,
                CIRelationshipModel.target_asset_id == target_asset_id,
                CIRelationshipModel.relationship_type == relationship_type,
                CIRelationshipModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def delete(self, relationship_id: str) -> None:
        model = self.session.execute(
            select(CIRelationshipModel).where(CIRelationshipModel.id == relationship_id)
        ).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()

    def find_all_by_company(self, company_id: str) -> list[CIRelationship]:
        models = self.session.execute(
            select(CIRelationshipModel).where(
                CIRelationshipModel.company_id == company_id,
            )
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_all(self, company_id: str) -> int:
        result = self.session.execute(
            select(func.count()).where(
                CIRelationshipModel.company_id == company_id,
            )
        ).scalar()
        return result or 0

    def count_by_type(self, company_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(
                CIRelationshipModel.relationship_type,
                func.count().label("cnt"),
            ).where(
                CIRelationshipModel.company_id == company_id,
            ).group_by(CIRelationshipModel.relationship_type)
        ).all()
        return {row[0]: row[1] for row in rows}

    def count_incoming_by_asset(self, company_id: str, limit: int = 10) -> list[dict]:
        stmt = (
            select(
                CIRelationshipModel.target_asset_id,
                AssetModel.brand.concat(" ").concat(AssetModel.model).label("asset_name"),
                AssetModel.serial_number.label("asset_tag"),
                func.count().label("cnt"),
            )
            .join(AssetModel, CIRelationshipModel.target_asset_id == AssetModel.id)
            .where(CIRelationshipModel.company_id == company_id)
            .group_by(
                CIRelationshipModel.target_asset_id,
                AssetModel.brand,
                AssetModel.model,
                AssetModel.serial_number,
            )
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = self.session.execute(stmt).all()
        return [
            {
                "asset_id": row[0],
                "asset_name": row[1],
                "asset_tag": row[2],
                "count": row[3],
            }
            for row in rows
        ]

    @staticmethod
    def _to_entity(model: CIRelationshipModel) -> CIRelationship:
        return CIRelationship(
            id=model.id,
            company_id=model.company_id,
            source_asset_id=model.source_asset_id,
            target_asset_id=model.target_asset_id,
            relationship_type=CIRelationshipType(model.relationship_type),
            description=model.description,
            created_at=model.created_at,
            created_by=model.created_by,
        )
