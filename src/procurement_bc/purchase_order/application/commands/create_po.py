import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)
from src.procurement_bc.budget.domain.repository import (
    CompanyProcurementConfigRepositoryInterface,
)
from src.procurement_bc.purchase_order.application.services.po_number_generator import (  # noqa: E501
    PONumberGenerator,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)

logger = logging.getLogger(__name__)


@dataclass
class POItemInput:
    description: str
    asset_type: Optional[str] = None
    quantity: int = 1
    unit_cost_cents: int = 0
    notes: Optional[str] = None


@dataclass
class CreatePurchaseOrderCommand(Command):
    company_id: str
    vendor_name: str
    department_id: str
    items: list[POItemInput] = field(
        default_factory=list,
    )
    request_ids: list[str] = field(
        default_factory=list,
    )
    vendor_id: Optional[str] = None
    notes: Optional[str] = None
    performed_by: str = ""


class CreatePurchaseOrderCommandHandler(
    CommandHandler[CreatePurchaseOrderCommand],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
        config_repo: CompanyProcurementConfigRepositoryInterface,
    ):
        self.po_repo = po_repo
        self.config_repo = config_repo
        self._last_created_id: Optional[str] = None

    def handle(
        self, command: CreatePurchaseOrderCommand,
    ) -> None:
        if not command.items:
            raise ValueError("At least one item is required")

        config = self.config_repo.find_by_company_id(
            command.company_id,
        )
        if not config:
            config = CompanyProcurementConfig.defaults(
                command.company_id,
            )

        now = datetime.now(timezone.utc)
        generator = PONumberGenerator(self.po_repo)
        po_number = generator.generate(
            command.company_id,
            config.po_number_prefix,
            now.year,
        )

        po = PurchaseOrder.create(
            company_id=command.company_id,
            po_number=po_number,
            vendor_name=command.vendor_name,
            department_id=command.department_id,
            created_by=command.performed_by,
            currency=config.currency,
            vendor_id=command.vendor_id,
            notes=command.notes,
        )

        for item_input in command.items:
            total = item_input.quantity * item_input.unit_cost_cents
            po.items.append(
                PurchaseOrderItem(
                    id=str(ulid.new()),
                    purchase_order_id=po.id,
                    description=item_input.description,
                    quantity=item_input.quantity,
                    unit_cost_cents=item_input.unit_cost_cents,
                    total_cost_cents=total,
                    asset_type=item_input.asset_type,
                    notes=item_input.notes,
                )
            )

        po.request_ids = list(command.request_ids)
        po.recalculate_total()
        self.po_repo.save(po)

        logger.info(
            "PO %s created for company %s",
            po.po_number,
            command.company_id,
        )
        self._last_created_id = po.id

    @property
    def last_created_id(self) -> str:
        if not self._last_created_id:
            raise RuntimeError(
                "No PO has been created yet",
            )
        return self._last_created_id
