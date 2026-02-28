from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import case, func, literal, not_, or_, select
from sqlalchemy.orm import Session

from src.asset_bc.asset.domain.entities import Asset, AssetEvent, AssetLocation
from src.asset_bc.asset.domain.enums import AssetCriticality, AssetStatus
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.asset_bc.asset.infrastructure.models import AssetLocationModel, AssetModel, AssetEventModel, CIRelationshipModel


class AssetRepository(AssetRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, asset: Asset) -> Asset:
        existing = self.session.execute(
            select(AssetModel).where(AssetModel.id == asset.id)
        ).scalar_one_or_none()
        if existing:
            existing.type = asset.type
            existing.brand = asset.brand
            existing.model = asset.model
            existing.serial_number = asset.serial_number
            existing.status = asset.status.value
            existing.assigned_to = asset.assigned_to
            existing.department_id = asset.department_id
            existing.location_id = asset.location_id
            existing.purchase_date = asset.purchase_date
            existing.warranty_expiration = asset.warranty_expiration
            existing.notes = asset.notes
            existing.custom_fields_data = asset.custom_fields_data or {}
            existing.criticality = asset.criticality.value if asset.criticality else None
            existing.impact_score = asset.impact_score
            existing.rto_minutes = asset.rto_minutes
            existing.rpo_minutes = asset.rpo_minutes
            existing.bia_justification = asset.bia_justification
            existing.bia_reviewed_at = asset.bia_reviewed_at
            existing.bia_reviewed_by = asset.bia_reviewed_by
        else:
            model = AssetModel(
                id=asset.id,
                company_id=asset.company_id,
                type=asset.type,
                brand=asset.brand,
                model=asset.model,
                serial_number=asset.serial_number,
                status=asset.status.value,
                assigned_to=asset.assigned_to,
                department_id=asset.department_id,
                location_id=asset.location_id,
                purchase_date=asset.purchase_date,
                warranty_expiration=asset.warranty_expiration,
                notes=asset.notes,
                custom_fields_data=asset.custom_fields_data or {},
                criticality=asset.criticality.value if asset.criticality else None,
                impact_score=asset.impact_score,
                rto_minutes=asset.rto_minutes,
                rpo_minutes=asset.rpo_minutes,
                bia_justification=asset.bia_justification,
                bia_reviewed_at=asset.bia_reviewed_at,
                bia_reviewed_by=asset.bia_reviewed_by,
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
        location_id: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        custom_field_filters: Optional[dict[str, str]] = None,
        custom_field_search_keys: Optional[list[str]] = None,
        criticality: Optional[str] = None,
    ) -> tuple[list[Asset], int]:
        stmt = select(AssetModel).where(AssetModel.company_id == company_id)

        if search:
            pattern = f"%{search}%"
            or_conditions = [
                AssetModel.serial_number.ilike(pattern),
                AssetModel.brand.ilike(pattern),
                AssetModel.model.ilike(pattern),
            ]
            if custom_field_search_keys:
                for cf_key in custom_field_search_keys:
                    or_conditions.append(
                        AssetModel.custom_fields_data[cf_key].as_string().ilike(pattern)
                    )
            stmt = stmt.where(or_(*or_conditions))

        if custom_field_filters:
            for key, value in custom_field_filters.items():
                stmt = stmt.where(
                    AssetModel.custom_fields_data[key].as_string() == value
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
        if location_id is not None:
            stmt = stmt.where(AssetModel.location_id == location_id)
        if criticality is not None:
            if criticality == "unclassified":
                stmt = stmt.where(AssetModel.criticality.is_(None))
            else:
                stmt = stmt.where(AssetModel.criticality == criticality)

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
        return [self._to_entity(m) for m in models], total or 0

    def find_by_ids(self, asset_ids: list[str], company_id: str) -> list[Asset]:
        if not asset_ids:
            return []
        stmt = select(AssetModel).where(
            AssetModel.company_id == company_id,
            AssetModel.id.in_(asset_ids),
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

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
        result: dict[str, int] = {}
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

    def find_in_stock_by_type(
        self, company_id: str, asset_type: str,
    ) -> list[Asset]:
        models = self.session.execute(
            select(AssetModel).where(
                AssetModel.company_id == company_id,
                AssetModel.type == asset_type,
                AssetModel.status == AssetStatus.IN_STOCK.value,
            ).order_by(AssetModel.purchase_date.asc().nullslast())
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def find_all_by_company(self, company_id: str) -> list[Asset]:
        models = self.session.execute(
            select(AssetModel)
            .where(AssetModel.company_id == company_id)
            .order_by(AssetModel.type.asc(), AssetModel.brand.asc())
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_by_criticality(self, company_id: str) -> dict[str, int]:
        label_col = case(
            (AssetModel.criticality.is_(None), literal("unclassified")),
            else_=AssetModel.criticality,
        )
        rows = self.session.execute(
            select(label_col.label("level"), func.count().label("cnt"))
            .where(
                AssetModel.company_id == company_id,
                AssetModel.status != AssetStatus.DECOMMISSIONED.value,
            )
            .group_by(label_col)
        ).all()
        return {row[0]: row[1] for row in rows}

    def bia_coverage_stats(self, company_id: str) -> dict:
        base = select(AssetModel).where(
            AssetModel.company_id == company_id,
            AssetModel.status != AssetStatus.DECOMMISSIONED.value,
        ).subquery()
        row = self.session.execute(
            select(
                func.count().filter(
                    base.c.criticality.in_(["critical", "high"])
                ).label("total"),
                func.count().filter(
                    base.c.criticality.in_(["critical", "high"]),
                    base.c.impact_score.isnot(None),
                    base.c.rto_minutes.isnot(None),
                ).label("has_bia"),
            ).select_from(base)
        ).one()
        total = row[0] or 0
        has_bia = row[1] or 0
        return {
            "total_critical_high": total,
            "has_bia": has_bia,
            "coverage_pct": round((has_bia / total * 100), 1) if total > 0 else 0.0,
        }

    def count_orphan_critical_assets(self, company_id: str) -> int:
        ci_sub = select(literal(1)).where(
            CIRelationshipModel.company_id == company_id,
            or_(
                CIRelationshipModel.source_asset_id == AssetModel.id,
                CIRelationshipModel.target_asset_id == AssetModel.id,
            ),
        ).correlate(AssetModel)
        result = self.session.execute(
            select(func.count()).where(
                AssetModel.company_id == company_id,
                AssetModel.criticality == "critical",
                AssetModel.status != AssetStatus.DECOMMISSIONED.value,
                not_(ci_sub.exists()),
            )
        ).scalar()
        return result or 0

    def find_overdue_bia_reviews(self, company_id: str, months: int) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=months * 30)
        stmt = select(
            AssetModel.id,
            AssetModel.brand.concat(" ").concat(AssetModel.model).label("name"),
            AssetModel.serial_number.label("asset_tag"),
            AssetModel.criticality,
            AssetModel.bia_reviewed_at,
        ).where(
            AssetModel.company_id == company_id,
            AssetModel.criticality.in_(["critical", "high"]),
            AssetModel.status != AssetStatus.DECOMMISSIONED.value,
            or_(
                AssetModel.bia_reviewed_at.is_(None),
                AssetModel.bia_reviewed_at < cutoff,
            ),
        ).order_by(AssetModel.criticality.asc(), AssetModel.brand.asc())
        rows = self.session.execute(stmt).all()
        return [
            {
                "id": row[0],
                "name": row[1],
                "asset_tag": row[2],
                "criticality": row[3],
                "bia_reviewed_at": row[4],
            }
            for row in rows
        ]

    # --- Location methods ---

    def save_location(self, location: AssetLocation) -> AssetLocation:
        existing = self.session.execute(
            select(AssetLocationModel).where(AssetLocationModel.id == location.id)
        ).scalar_one_or_none()
        if existing:
            existing.name = location.name
            existing.in_use = location.in_use
            existing.street_line_1 = location.street_line_1
            existing.street_line_2 = location.street_line_2
            existing.city = location.city
            existing.state = location.state
            existing.postal_code = location.postal_code
            existing.country = location.country
            existing.phone = location.phone
            existing.is_personal = location.is_personal
            existing.user_id = location.user_id
        else:
            model = AssetLocationModel(
                id=location.id,
                company_id=location.company_id,
                name=location.name,
                is_system=location.is_system,
                system_key=location.system_key,
                in_use=location.in_use,
                street_line_1=location.street_line_1,
                street_line_2=location.street_line_2,
                city=location.city,
                state=location.state,
                postal_code=location.postal_code,
                country=location.country,
                phone=location.phone,
                is_personal=location.is_personal,
                user_id=location.user_id,
            )
            self.session.add(model)
            existing = model
        self.session.flush()
        self.session.refresh(existing)
        return self._location_to_entity(existing)

    def find_location_by_id(self, location_id: str, company_id: str) -> Optional[AssetLocation]:
        model = self.session.execute(
            select(AssetLocationModel).where(
                AssetLocationModel.id == location_id,
                AssetLocationModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._location_to_entity(model) if model else None

    def find_locations_by_company(self, company_id: str) -> list[AssetLocation]:
        models = self.session.execute(
            select(AssetLocationModel)
            .where(AssetLocationModel.company_id == company_id)
            .order_by(
                AssetLocationModel.is_system.desc(),
                AssetLocationModel.name.asc(),
            )
        ).scalars().all()
        return [self._location_to_entity(m) for m in models]

    def find_system_location(self, company_id: str, system_key: str) -> Optional[AssetLocation]:
        model = self.session.execute(
            select(AssetLocationModel).where(
                AssetLocationModel.company_id == company_id,
                AssetLocationModel.system_key == system_key,
            )
        ).scalar_one_or_none()
        return self._location_to_entity(model) if model else None

    def delete_location(self, location_id: str) -> None:
        model = self.session.execute(
            select(AssetLocationModel).where(AssetLocationModel.id == location_id)
        ).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()

    def count_assets_at_location(self, location_id: str) -> int:
        result = self.session.execute(
            select(func.count()).where(AssetModel.location_id == location_id)
        ).scalar()
        return result or 0

    def find_location_by_name(self, name: str, company_id: str) -> Optional[AssetLocation]:
        model = self.session.execute(
            select(AssetLocationModel).where(
                func.lower(AssetLocationModel.name) == name.lower().strip(),
                AssetLocationModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._location_to_entity(model) if model else None

    def find_personal_location_by_user(self, user_id: str, company_id: str) -> Optional[AssetLocation]:
        model = self.session.execute(
            select(AssetLocationModel).where(
                AssetLocationModel.user_id == user_id,
                AssetLocationModel.company_id == company_id,
                AssetLocationModel.is_personal.is_(True),
            )
        ).scalar_one_or_none()
        return self._location_to_entity(model) if model else None

    @staticmethod
    def _location_to_entity(model: AssetLocationModel) -> AssetLocation:
        return AssetLocation(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            is_system=model.is_system,
            system_key=model.system_key,
            in_use=model.in_use,
            street_line_1=model.street_line_1,
            street_line_2=model.street_line_2,
            city=model.city,
            state=model.state,
            postal_code=model.postal_code,
            country=model.country,
            phone=model.phone,
            is_personal=model.is_personal,
            user_id=model.user_id,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_entity(model: AssetModel) -> Asset:
        return Asset(
            id=model.id,
            company_id=model.company_id,
            type=model.type,
            brand=model.brand,
            model=model.model,
            serial_number=model.serial_number,
            status=AssetStatus(model.status),
            assigned_to=model.assigned_to,
            department_id=model.department_id,
            location_id=model.location_id,
            purchase_date=model.purchase_date,
            warranty_expiration=model.warranty_expiration,
            notes=model.notes,
            custom_fields_data=model.custom_fields_data or {},
            criticality=AssetCriticality(model.criticality) if model.criticality else None,
            impact_score=model.impact_score,
            rto_minutes=model.rto_minutes,
            rpo_minutes=model.rpo_minutes,
            bia_justification=model.bia_justification,
            bia_reviewed_at=model.bia_reviewed_at,
            bia_reviewed_by=model.bia_reviewed_by,
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
