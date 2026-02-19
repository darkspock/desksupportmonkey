import pytest
from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.commands.receive_items import (
    InvalidReceiveQuantityError,
    InvalidReceiveStatusError,
    ItemNotFoundError,
    OverReceiveError,
    PONotFoundError,
    ReceiveItemInput,
    ReceiveItemsCommand,
    ReceiveItemsCommandHandler,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    PurchaseOrderStatus,
)


def _make_ordered_po() -> PurchaseOrder:
    po = PurchaseOrder.create(
        company_id="comp1",
        po_number="PO-2026-001",
        vendor_name="Vendor",
        department_id="dept1",
        created_by="user1",
    )
    po.items = [
        PurchaseOrderItem(
            id="item1",
            purchase_order_id=po.id,
            description="Laptop Dell",
            quantity=3,
            unit_cost_cents=50000,
            total_cost_cents=150000,
            asset_type="laptop",
        ),
        PurchaseOrderItem(
            id="item2",
            purchase_order_id=po.id,
            description="USB Cable",
            quantity=5,
            unit_cost_cents=500,
            total_cost_cents=2500,
        ),
    ]
    po.recalculate_total()
    po.submit()
    po.approve(approved_by="admin1")
    po.mark_ordered()
    return po


class TestReceiveItemsCommandHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.receipt_service = MagicMock()
        self.handler = ReceiveItemsCommandHandler(
            po_repo=self.po_repo,
            receipt_asset_service=self.receipt_service,
        )

    def test_partial_receipt_sets_partially_received(self):
        po = _make_ordered_po()
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(
            ReceiveItemsCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                items=[
                    ReceiveItemInput(
                        item_id="item1",
                        received_quantity=1,
                    ),
                ],
                performed_by="tech1",
            )
        )

        assert po.status == PurchaseOrderStatus.PARTIALLY_RECEIVED
        assert po.items[0].received_quantity == 1
        assert po.items[0].received_at is not None
        self.po_repo.save.assert_called_once()

    def test_full_receipt_sets_received(self):
        po = _make_ordered_po()
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(
            ReceiveItemsCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                items=[
                    ReceiveItemInput(
                        item_id="item1",
                        received_quantity=3,
                    ),
                    ReceiveItemInput(
                        item_id="item2",
                        received_quantity=5,
                    ),
                ],
                performed_by="tech1",
            )
        )

        assert po.status == PurchaseOrderStatus.RECEIVED
        assert po.items[0].received_quantity == 3
        assert po.items[1].received_quantity == 5

    def test_multiple_receipts_across_sessions(self):
        po = _make_ordered_po()
        self.po_repo.find_by_id.return_value = po

        # First receipt: partial
        self.handler.handle(
            ReceiveItemsCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                items=[
                    ReceiveItemInput(
                        item_id="item1",
                        received_quantity=2,
                    ),
                ],
                performed_by="tech1",
            )
        )
        assert po.status == PurchaseOrderStatus.PARTIALLY_RECEIVED
        assert po.items[0].received_quantity == 2

        # Second receipt: complete everything
        self.handler.handle(
            ReceiveItemsCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                items=[
                    ReceiveItemInput(
                        item_id="item1",
                        received_quantity=1,
                    ),
                    ReceiveItemInput(
                        item_id="item2",
                        received_quantity=5,
                    ),
                ],
                performed_by="tech1",
            )
        )
        assert po.status == PurchaseOrderStatus.RECEIVED
        assert po.items[0].received_quantity == 3
        assert po.items[1].received_quantity == 5

    def test_over_receive_raises(self):
        po = _make_ordered_po()
        self.po_repo.find_by_id.return_value = po

        with pytest.raises(OverReceiveError):
            self.handler.handle(
                ReceiveItemsCommand(
                    purchase_order_id=po.id,
                    company_id="comp1",
                    items=[
                        ReceiveItemInput(
                            item_id="item1",
                            received_quantity=4,
                        ),
                    ],
                    performed_by="tech1",
                )
            )

    def test_zero_quantity_raises(self):
        po = _make_ordered_po()
        self.po_repo.find_by_id.return_value = po

        with pytest.raises(InvalidReceiveQuantityError):
            self.handler.handle(
                ReceiveItemsCommand(
                    purchase_order_id=po.id,
                    company_id="comp1",
                    items=[
                        ReceiveItemInput(
                            item_id="item1",
                            received_quantity=0,
                        ),
                    ],
                    performed_by="tech1",
                )
            )

    def test_invalid_status_raises(self):
        po = PurchaseOrder.create(
            company_id="comp1",
            po_number="PO-001",
            vendor_name="V",
            department_id="d1",
            created_by="u1",
        )
        self.po_repo.find_by_id.return_value = po

        with pytest.raises(InvalidReceiveStatusError):
            self.handler.handle(
                ReceiveItemsCommand(
                    purchase_order_id=po.id,
                    company_id="comp1",
                    items=[
                        ReceiveItemInput(
                            item_id="x",
                            received_quantity=1,
                        ),
                    ],
                    performed_by="tech1",
                )
            )

    def test_item_not_found_raises(self):
        po = _make_ordered_po()
        self.po_repo.find_by_id.return_value = po

        with pytest.raises(ItemNotFoundError):
            self.handler.handle(
                ReceiveItemsCommand(
                    purchase_order_id=po.id,
                    company_id="comp1",
                    items=[
                        ReceiveItemInput(
                            item_id="nonexistent",
                            received_quantity=1,
                        ),
                    ],
                    performed_by="tech1",
                )
            )

    def test_po_not_found_raises(self):
        self.po_repo.find_by_id.return_value = None

        with pytest.raises(PONotFoundError):
            self.handler.handle(
                ReceiveItemsCommand(
                    purchase_order_id="nope",
                    company_id="comp1",
                    items=[
                        ReceiveItemInput(
                            item_id="x",
                            received_quantity=1,
                        ),
                    ],
                    performed_by="tech1",
                )
            )

    def test_receipt_with_asset_creation(self):
        po = _make_ordered_po()
        self.po_repo.find_by_id.return_value = po
        self.receipt_service.create_asset_from_item.return_value = "asset123"

        self.handler.handle(
            ReceiveItemsCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                items=[
                    ReceiveItemInput(
                        item_id="item1",
                        received_quantity=1,
                        create_asset=True,
                    ),
                ],
                performed_by="tech1",
            )
        )

        self.receipt_service.create_asset_from_item.assert_called_once()
        assert po.items[0].linked_asset_id == "asset123"

    def test_receipt_with_link_asset_id(self):
        po = _make_ordered_po()
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(
            ReceiveItemsCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                items=[
                    ReceiveItemInput(
                        item_id="item1",
                        received_quantity=1,
                        link_asset_id="existing-asset",
                    ),
                ],
                performed_by="tech1",
            )
        )

        assert po.items[0].linked_asset_id == "existing-asset"
