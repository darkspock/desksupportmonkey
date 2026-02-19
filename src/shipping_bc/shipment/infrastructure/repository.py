from datetime import UTC, datetime, timedelta
from typing import Optional

import ulid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.shipping_bc.shipment.domain.entities import (
    Shipment,
    ShipmentItem,
)
from src.shipping_bc.shipment.domain.enums import (
    ShipmentDirection,
    ShipmentStatus,
    DestinationType,
)
from src.shipping_bc.shipment.domain.repository import (
    ShipmentRepositoryInterface,
)
from src.shipping_bc.shipment.infrastructure.models import (
    ShipmentItemModel,
    ShipmentModel,
)


class ShipmentRepository(ShipmentRepositoryInterface):

    def __init__(self, session: Session):
        self.session = session

    def save(self, shipment: Shipment) -> Shipment:
        existing = (
            self.session.execute(
                select(ShipmentModel).where(
                    ShipmentModel.id == shipment.id,
                )
            )
            .unique()
            .scalar_one_or_none()
        )

        if existing:
            existing.direction = shipment.direction.value
            existing.destination_type = (
                shipment.destination_type.value
            )
            existing.status = shipment.status.value
            existing.origin_address_id = (
                shipment.origin_address_id
            )
            existing.destination_address_id = (
                shipment.destination_address_id
            )
            existing.recipient_name = shipment.recipient_name
            existing.recipient_user_id = (
                shipment.recipient_user_id
            )
            existing.carrier = shipment.carrier
            existing.tracking_number = (
                shipment.tracking_number
            )
            existing.tracking_url = shipment.tracking_url
            existing.request_id = shipment.request_id
            existing.po_id = shipment.po_id
            existing.return_for_shipment_id = (
                shipment.return_for_shipment_id
            )
            existing.notes = shipment.notes
            existing.failure_reason = shipment.failure_reason
            existing.cancellation_reason = (
                shipment.cancellation_reason
            )
            existing.dispatched_at = shipment.dispatched_at
            existing.delivered_at = shipment.delivered_at

            existing.items.clear()
            self.session.flush()
            for item in shipment.items:
                existing.items.append(
                    ShipmentItemModel(
                        id=item.id or str(ulid.new()),
                        shipment_id=shipment.id,
                        asset_id=item.asset_id,
                        notes=item.notes,
                    )
                )
        else:
            model = ShipmentModel(
                id=shipment.id,
                company_id=shipment.company_id,
                direction=shipment.direction.value,
                destination_type=(
                    shipment.destination_type.value
                ),
                status=shipment.status.value,
                origin_address_id=(
                    shipment.origin_address_id
                ),
                destination_address_id=(
                    shipment.destination_address_id
                ),
                recipient_name=shipment.recipient_name,
                recipient_user_id=(
                    shipment.recipient_user_id
                ),
                carrier=shipment.carrier,
                tracking_number=shipment.tracking_number,
                tracking_url=shipment.tracking_url,
                request_id=shipment.request_id,
                po_id=shipment.po_id,
                return_for_shipment_id=(
                    shipment.return_for_shipment_id
                ),
                notes=shipment.notes,
                failure_reason=shipment.failure_reason,
                cancellation_reason=(
                    shipment.cancellation_reason
                ),
                created_by=shipment.created_by,
                dispatched_at=shipment.dispatched_at,
                delivered_at=shipment.delivered_at,
                items=[
                    ShipmentItemModel(
                        id=i.id or str(ulid.new()),
                        shipment_id=shipment.id,
                        asset_id=i.asset_id,
                        notes=i.notes,
                    )
                    for i in shipment.items
                ],
            )
            self.session.add(model)

        self.session.flush()
        return shipment

    def find_by_id(
        self, shipment_id: str, company_id: str,
    ) -> Optional[Shipment]:
        model = (
            self.session.execute(
                select(ShipmentModel).where(
                    ShipmentModel.id == shipment_id,
                    ShipmentModel.company_id == company_id,
                )
            )
            .unique()
            .scalar_one_or_none()
        )
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        direction: Optional[str] = None,
        destination_type: Optional[str] = None,
        request_id: Optional[str] = None,
        po_id: Optional[str] = None,
    ) -> tuple[list[Shipment], int]:
        stmt = select(ShipmentModel).where(
            ShipmentModel.company_id == company_id,
        )
        if status:
            stmt = stmt.where(
                ShipmentModel.status == status,
            )
        if direction:
            stmt = stmt.where(
                ShipmentModel.direction == direction,
            )
        if destination_type:
            stmt = stmt.where(
                ShipmentModel.destination_type
                == destination_type,
            )
        if request_id:
            stmt = stmt.where(
                ShipmentModel.request_id == request_id,
            )
        if po_id:
            stmt = stmt.where(
                ShipmentModel.po_id == po_id,
            )

        total = self.session.execute(
            select(func.count()).select_from(
                stmt.subquery(),
            )
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(
                    ShipmentModel.created_at.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .unique()
            .all()
        )

        return [self._to_entity(m) for m in models], (
            total or 0
        )

    def find_by_asset_id(
        self, asset_id: str, company_id: str,
    ) -> list[Shipment]:
        stmt = (
            select(ShipmentModel)
            .join(ShipmentItemModel)
            .where(
                ShipmentItemModel.asset_id == asset_id,
                ShipmentModel.company_id == company_id,
            )
            .order_by(ShipmentModel.created_at.desc())
        )
        models = (
            self.session.execute(stmt)
            .scalars()
            .unique()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_active_by_asset_id(
        self, asset_id: str, company_id: str,
    ) -> list[Shipment]:
        active_statuses = [
            ShipmentStatus.DRAFT.value,
            ShipmentStatus.DISPATCHED.value,
            ShipmentStatus.IN_TRANSIT.value,
        ]
        stmt = (
            select(ShipmentModel)
            .join(ShipmentItemModel)
            .where(
                ShipmentItemModel.asset_id == asset_id,
                ShipmentModel.company_id == company_id,
                ShipmentModel.status.in_(
                    active_statuses,
                ),
            )
        )
        models = (
            self.session.execute(stmt)
            .scalars()
            .unique()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_recipient_user_id(
        self,
        recipient_user_id: str,
        company_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[Shipment], int]:
        stmt = select(ShipmentModel).where(
            ShipmentModel.recipient_user_id
            == recipient_user_id,
            ShipmentModel.company_id == company_id,
        )

        total = self.session.execute(
            select(func.count()).select_from(
                stmt.subquery(),
            )
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(
                    ShipmentModel.created_at.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .unique()
            .all()
        )

        return [self._to_entity(m) for m in models], (
            total or 0
        )

    def count_by_status(
        self, company_id: str,
    ) -> dict[str, int]:
        rows = self.session.execute(
            select(
                ShipmentModel.status,
                func.count(ShipmentModel.id),
            )
            .where(
                ShipmentModel.company_id == company_id,
            )
            .group_by(ShipmentModel.status)
        ).all()
        return {row[0]: row[1] for row in rows}

    def find_recent_delivered(
        self, company_id: str, days: int,
    ) -> list[Shipment]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(ShipmentModel)
            .where(
                ShipmentModel.company_id == company_id,
                ShipmentModel.status
                == ShipmentStatus.DELIVERED.value,
                ShipmentModel.delivered_at >= cutoff,
            )
            .order_by(ShipmentModel.delivered_at.desc())
        )
        models = (
            self.session.execute(stmt)
            .scalars()
            .unique()
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_status(
        self, company_id: str, status: str,
    ) -> list[Shipment]:
        stmt = (
            select(ShipmentModel)
            .where(
                ShipmentModel.company_id == company_id,
                ShipmentModel.status == status,
            )
            .order_by(ShipmentModel.created_at.desc())
        )
        models = (
            self.session.execute(stmt)
            .scalars()
            .unique()
            .all()
        )
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(model: ShipmentModel) -> Shipment:
        return Shipment(
            id=model.id,
            company_id=model.company_id,
            direction=ShipmentDirection(model.direction),
            destination_type=DestinationType(
                model.destination_type,
            ),
            status=ShipmentStatus(model.status),
            destination_address_id=(
                model.destination_address_id
            ),
            created_by=model.created_by,
            origin_address_id=model.origin_address_id,
            recipient_name=model.recipient_name,
            recipient_user_id=model.recipient_user_id,
            carrier=model.carrier,
            tracking_number=model.tracking_number,
            tracking_url=model.tracking_url,
            request_id=model.request_id,
            po_id=model.po_id,
            return_for_shipment_id=(
                model.return_for_shipment_id
            ),
            notes=model.notes,
            failure_reason=model.failure_reason,
            cancellation_reason=(
                model.cancellation_reason
            ),
            dispatched_at=model.dispatched_at,
            delivered_at=model.delivered_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            items=[
                ShipmentItem(
                    id=i.id,
                    shipment_id=i.shipment_id,
                    asset_id=i.asset_id,
                    notes=i.notes,
                )
                for i in model.items
            ],
        )
