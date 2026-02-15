from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func, or_, select
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

    ALLOWED_SORT_COLUMNS = {
        "created_at": AssetModel.created_at,
        "purchase_date": AssetModel.purchase_date,
        "warranty_expiration": AssetModel.warranty_expiration,
    }

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        department_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Asset], int]:
        stmt = select(AssetModel).where(AssetModel.company_id == company_id)

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    AssetModel.serial_number.ilike(pattern),
                    AssetModel.brand.ilike(pattern),
                    AssetModel.model.ilike(pattern),
                )
            )
        if type is not None:
            stmt = stmt.where(AssetModel.type == type)
        if status is not None:
            stmt = stmt.where(AssetModel.status == status)
        if department_id is not None:
            stmt = stmt.where(AssetModel.department_id == department_id)
        if assigned_to is not None:
            if assigned_to == "none":
                stmt = stmt.where(AssetModel.assigned_to.is_(None))
            else:
                stmt = stmt.where(AssetModel.assigned_to == assigned_to)

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        sort_column = self.ALLOWED_SORT_COLUMNS.get(sort_by, AssetModel.created_at)
        order = sort_column.asc() if sort_order == "asc" else sort_column.desc()

        models = self.session.execute(
            stmt.order_by(order)
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

    def count_by_status(self, company_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(
                AssetModel.status,
                func.count().label("cnt"),
            ).where(
                AssetModel.company_id == company_id
            ).group_by(AssetModel.status)
        ).all()
        result = {s.value: 0 for s in AssetStatus}
        for row in rows:
            result[row[0]] = row[1]
        return result

    def count_by_type(self, company_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(
                AssetModel.type,
                func.count().label("cnt"),
            ).where(
                AssetModel.company_id == company_id
            ).group_by(AssetModel.type)
        ).all()
        result = {t.value: 0 for t in AssetType}
        for row in rows:
            result[row[0]] = row[1]
        return result

    def find_expiring_warranties(self, company_id: str, days: int) -> list[dict]:
        today = date.today()
        threshold = today + timedelta(days=days)
        stmt = select(
            AssetModel.id,
            AssetModel.brand,
            AssetModel.model,
            AssetModel.serial_number,
            AssetModel.warranty_expiration,
            AssetModel.assigned_to,
        ).where(
            AssetModel.company_id == company_id,
            AssetModel.status != AssetStatus.DECOMMISSIONED.value,
            AssetModel.warranty_expiration.isnot(None),
            AssetModel.warranty_expiration >= today,
            AssetModel.warranty_expiration <= threshold,
        ).order_by(AssetModel.warranty_expiration.asc())

        rows = self.session.execute(stmt).all()
        return [
            {
                "id": row[0],
                "brand": row[1],
                "model": row[2],
                "serial_number": row[3],
                "warranty_expiration": row[4],
                "assigned_to": row[5],
                "days_remaining": (row[4] - today).days,
            }
            for row in rows
        ]

    def find_aging_assets(self, company_id: str, years: int) -> list[dict]:
        today = date.today()
        threshold_date = date(today.year - years, today.month, today.day)
        stmt = select(
            AssetModel.id,
            AssetModel.brand,
            AssetModel.model,
            AssetModel.serial_number,
            AssetModel.purchase_date,
            AssetModel.assigned_to,
        ).where(
            AssetModel.company_id == company_id,
            AssetModel.status != AssetStatus.DECOMMISSIONED.value,
            AssetModel.purchase_date.isnot(None),
            AssetModel.purchase_date <= threshold_date,
        ).order_by(AssetModel.purchase_date.asc())

        rows = self.session.execute(stmt).all()
        return [
            {
                "id": row[0],
                "brand": row[1],
                "model": row[2],
                "serial_number": row[3],
                "purchase_date": row[4],
                "age_years": round((today - row[4]).days / 365.25, 1),
                "assigned_to": row[5],
            }
            for row in rows
        ]

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
