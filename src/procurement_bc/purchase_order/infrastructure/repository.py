from datetime import datetime
from typing import Optional

import ulid
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    PurchaseOrderStatus,
)
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)
from src.procurement_bc.purchase_order.infrastructure.models import (
    PurchaseOrderItemModel,
    PurchaseOrderModel,
    PurchaseOrderRequestModel,
)


class PurchaseOrderRepository(
    PurchaseOrderRepositoryInterface,
):
    def __init__(self, session: Session):
        self.session = session

    def save(self, po: PurchaseOrder) -> PurchaseOrder:
        existing = self.session.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == po.id,
            )
        ).unique().scalar_one_or_none()

        if existing:
            existing.vendor_id = po.vendor_id
            existing.vendor_name = po.vendor_name
            existing.department_id = po.department_id
            existing.status = po.status.value
            existing.total_amount_cents = po.total_amount_cents
            existing.currency = po.currency
            existing.notes = po.notes
            existing.approved_by = po.approved_by
            existing.approved_at = po.approved_at
            existing.ordered_at = po.ordered_at
            existing.cancellation_reason = po.cancellation_reason

            existing.items.clear()
            self.session.flush()
            for item in po.items:
                existing.items.append(
                    PurchaseOrderItemModel(
                        id=item.id or str(ulid.new()),
                        purchase_order_id=po.id,
                        description=item.description,
                        asset_type=item.asset_type,
                        quantity=item.quantity,
                        unit_cost_cents=item.unit_cost_cents,
                        total_cost_cents=item.total_cost_cents,
                        received_quantity=item.received_quantity,
                        received_at=item.received_at,
                        linked_asset_id=item.linked_asset_id,
                        notes=item.notes,
                    )
                )

            self.session.execute(
                delete(PurchaseOrderRequestModel).where(
                    PurchaseOrderRequestModel.purchase_order_id == po.id,
                )
            )
            for req_id in po.request_ids:
                self.session.add(
                    PurchaseOrderRequestModel(
                        purchase_order_id=po.id,
                        request_id=req_id,
                    )
                )
        else:
            model = PurchaseOrderModel(
                id=po.id,
                company_id=po.company_id,
                po_number=po.po_number,
                vendor_id=po.vendor_id,
                vendor_name=po.vendor_name,
                department_id=po.department_id,
                status=po.status.value,
                total_amount_cents=po.total_amount_cents,
                currency=po.currency,
                notes=po.notes,
                approved_by=po.approved_by,
                approved_at=po.approved_at,
                ordered_at=po.ordered_at,
                cancellation_reason=po.cancellation_reason,
                created_by=po.created_by,
                items=[
                    PurchaseOrderItemModel(
                        id=i.id or str(ulid.new()),
                        purchase_order_id=po.id,
                        description=i.description,
                        asset_type=i.asset_type,
                        quantity=i.quantity,
                        unit_cost_cents=i.unit_cost_cents,
                        total_cost_cents=i.total_cost_cents,
                        received_quantity=i.received_quantity,
                        received_at=i.received_at,
                        linked_asset_id=i.linked_asset_id,
                        notes=i.notes,
                    )
                    for i in po.items
                ],
            )
            self.session.add(model)
            for req_id in po.request_ids:
                self.session.add(
                    PurchaseOrderRequestModel(
                        purchase_order_id=po.id,
                        request_id=req_id,
                    )
                )

        self.session.flush()
        return po

    def find_by_id(
        self, po_id: str, company_id: str,
    ) -> Optional[PurchaseOrder]:
        model = self.session.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == po_id,
                PurchaseOrderModel.company_id == company_id,
            )
        ).unique().scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model, self._get_request_ids(po_id))

    def find_by_number(
        self, po_number: str, company_id: str,
    ) -> Optional[PurchaseOrder]:
        model = self.session.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.po_number == po_number,
                PurchaseOrderModel.company_id == company_id,
            )
        ).unique().scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(
            model, self._get_request_ids(model.id),
        )

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        vendor_id: Optional[str] = None,
        department_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[PurchaseOrder], int]:
        stmt = select(PurchaseOrderModel).where(
            PurchaseOrderModel.company_id == company_id,
        )
        if status:
            stmt = stmt.where(
                PurchaseOrderModel.status == status,
            )
        if vendor_id:
            stmt = stmt.where(
                PurchaseOrderModel.vendor_id == vendor_id,
            )
        if department_id:
            stmt = stmt.where(
                PurchaseOrderModel.department_id
                == department_id,
            )
        if date_from:
            stmt = stmt.where(
                PurchaseOrderModel.created_at >= date_from,
            )
        if date_to:
            stmt = stmt.where(
                PurchaseOrderModel.created_at <= date_to,
            )

        total = self.session.execute(
            select(func.count()).select_from(
                stmt.subquery(),
            )
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(
                    PurchaseOrderModel.created_at.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .unique()
            .all()
        )

        pos = []
        for m in models:
            req_ids = self._get_request_ids(m.id)
            pos.append(self._to_entity(m, req_ids))
        return pos, total or 0

    def get_next_number(
        self, company_id: str, year: int,
    ) -> int:
        prefix_pattern = f"%-{year}-%"
        result = self.session.execute(
            select(
                func.count(PurchaseOrderModel.id),
            ).where(
                PurchaseOrderModel.company_id == company_id,
                PurchaseOrderModel.po_number.like(
                    prefix_pattern,
                ),
            )
        ).scalar()
        return (result or 0) + 1

    def sum_totals_by_department_status(
        self,
        company_id: str,
        department_id: str,
        fiscal_year_start: datetime,
        fiscal_year_end: datetime,
        statuses: list[str],
    ) -> int:
        result = self.session.execute(
            select(
                func.coalesce(
                    func.sum(
                        PurchaseOrderModel.total_amount_cents,
                    ),
                    0,
                )
            ).where(
                PurchaseOrderModel.company_id == company_id,
                PurchaseOrderModel.department_id
                == department_id,
                PurchaseOrderModel.status.in_(statuses),
                PurchaseOrderModel.created_at
                >= fiscal_year_start,
                PurchaseOrderModel.created_at
                < fiscal_year_end,
            )
        ).scalar()
        return result or 0

    def count_by_department_non_terminal(
        self, company_id: str, department_id: str,
    ) -> int:
        terminal = [
            PurchaseOrderStatus.CLOSED.value,
            PurchaseOrderStatus.CANCELLED.value,
        ]
        result = self.session.execute(
            select(
                func.count(PurchaseOrderModel.id),
            ).where(
                PurchaseOrderModel.company_id == company_id,
                PurchaseOrderModel.department_id
                == department_id,
                PurchaseOrderModel.status.not_in(terminal),
            )
        ).scalar()
        return result or 0

    def find_by_request_id(
        self, request_id: str, company_id: str,
    ) -> list[PurchaseOrder]:
        po_ids_stmt = select(
            PurchaseOrderRequestModel.purchase_order_id,
        ).where(
            PurchaseOrderRequestModel.request_id
            == request_id,
        )
        models = (
            self.session.execute(
                select(PurchaseOrderModel).where(
                    PurchaseOrderModel.id.in_(po_ids_stmt),
                    PurchaseOrderModel.company_id
                    == company_id,
                )
            )
            .scalars()
            .unique()
            .all()
        )
        return [
            self._to_entity(m, self._get_request_ids(m.id))
            for m in models
        ]

    def _get_request_ids(self, po_id: str) -> list[str]:
        rows = self.session.execute(
            select(
                PurchaseOrderRequestModel.request_id,
            ).where(
                PurchaseOrderRequestModel.purchase_order_id
                == po_id,
            )
        ).scalars().all()
        return list(rows)

    @staticmethod
    def _to_entity(
        model: PurchaseOrderModel,
        request_ids: list[str],
    ) -> PurchaseOrder:
        return PurchaseOrder(
            id=model.id,
            company_id=model.company_id,
            po_number=model.po_number,
            vendor_id=model.vendor_id,
            vendor_name=model.vendor_name,
            department_id=model.department_id,
            status=PurchaseOrderStatus(model.status),
            total_amount_cents=model.total_amount_cents,
            currency=model.currency,
            created_by=model.created_by,
            notes=model.notes,
            approved_by=model.approved_by,
            approved_at=model.approved_at,
            ordered_at=model.ordered_at,
            cancellation_reason=model.cancellation_reason,
            items=[
                PurchaseOrderItem(
                    id=i.id,
                    purchase_order_id=i.purchase_order_id,
                    description=i.description,
                    quantity=i.quantity,
                    unit_cost_cents=i.unit_cost_cents,
                    total_cost_cents=i.total_cost_cents,
                    asset_type=i.asset_type,
                    received_quantity=i.received_quantity,
                    received_at=i.received_at,
                    linked_asset_id=i.linked_asset_id,
                    notes=i.notes,
                )
                for i in model.items
            ],
            request_ids=request_ids,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
