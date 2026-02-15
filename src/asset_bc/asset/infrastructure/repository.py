from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.asset_bc.asset.domain.entities import Asset, AssetEvent
from src.asset_bc.asset.domain.enums import AssetStatus, AssetType
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.asset_bc.asset.infrastructure.models import AssetModel, AssetEventModel


class AssetRepository(AssetRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, asset: Asset) -> Asset:
        existing = self.session.execute(
            select(AssetModel).where(AssetModel.id == asset.id)
        ).scalar_one_or_none()
        if existing:
            existing.type = asset.type.value
            existing.brand = asset.brand
            existing.model = asset.model
            existing.serial_number = asset.serial_number
            existing.status = asset.status.value
            existing.assigned_to = asset.assigned_to
            existing.department_id = asset.department_id
            existing.purchase_date = asset.purchase_date
            existing.warranty_expiration = asset.warranty_expiration
            existing.notes = asset.notes
        else:
            model = AssetModel(
                id=asset.id,
                company_id=asset.company_id,
                type=asset.type.value,
                brand=asset.brand,
                model=asset.model,
                serial_number=asset.serial_number,
                status=asset.status.value,
                assigned_to=asset.assigned_to,
                department_id=asset.department_id,
                purchase_date=asset.purchase_date,
                warranty_expiration=asset.warranty_expiration,
                notes=asset.notes,
            )
            self.session.add(model)
            existing = model
        self.session.flush()
        self.session.refresh(existing)
        return self._to_entity(existing)

    def find_by_id(self, asset_id: str, company_id: str) -> Optional[Asset]:
        model = self.session.execute(
            select(AssetModel).where(
                AssetModel.id == asset_id, AssetModel.company_id == company_id
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_serial_number(self, serial_number: str, company_id: str) -> Optional[Asset]:
        model = self.session.execute(
            select(AssetModel).where(
                func.lower(AssetModel.serial_number) == serial_number.lower().strip(),
                AssetModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all(
        self, company_id: str, page: int, page_size: int
    ) -> tuple[list[Asset], int]:
        stmt = select(AssetModel).where(
            AssetModel.company_id == company_id
        )
        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()
        models = self.session.execute(
            stmt.order_by(AssetModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total

    def find_by_assigned_to(self, user_id: str, company_id: str) -> list[Asset]:
        models = self.session.execute(
            select(AssetModel).where(
                AssetModel.assigned_to == user_id,
                AssetModel.company_id == company_id,
                AssetModel.status == AssetStatus.ASSIGNED.value,
            ).order_by(AssetModel.created_at.desc())
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def save_event(self, event: AssetEvent) -> AssetEvent:
        model = AssetEventModel(
            id=event.id,
            asset_id=event.asset_id,
            event_type=event.event_type,
            data=event.data,
            performed_by=event.performed_by,
        )
        self.session.add(model)
        self.session.flush()
        return event

    def find_events(self, asset_id: str) -> list[AssetEvent]:
        models = self.session.execute(
            select(AssetEventModel)
            .where(AssetEventModel.asset_id == asset_id)
            .order_by(AssetEventModel.created_at.asc())
        ).scalars().all()
        return [self._event_to_entity(m) for m in models]

    @staticmethod
    def _to_entity(model: AssetModel) -> Asset:
        return Asset(
            id=model.id,
            company_id=model.company_id,
            type=AssetType(model.type),
            brand=model.brand,
            model=model.model,
            serial_number=model.serial_number,
            status=AssetStatus(model.status),
            assigned_to=model.assigned_to,
            department_id=model.department_id,
            purchase_date=model.purchase_date,
            warranty_expiration=model.warranty_expiration,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _event_to_entity(model: AssetEventModel) -> AssetEvent:
        return AssetEvent(
            id=model.id,
            asset_id=model.asset_id,
            event_type=model.event_type,
            data=model.data,
            performed_by=model.performed_by,
            created_at=model.created_at,
        )
