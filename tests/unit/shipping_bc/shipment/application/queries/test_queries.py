from unittest.mock import MagicMock

import pytest

from src.shipping_bc.shipment.application.queries.get_shipment import (
    GetShipmentQuery,
    GetShipmentQueryHandler,
    ShipmentNotFoundError,
)
from src.shipping_bc.shipment.application.queries.list_shipments import (
    ListShipmentsQuery,
    ListShipmentsQueryHandler,
)
from src.shipping_bc.shipment.application.queries.my_shipments import (
    MyShipmentsQuery,
    MyShipmentsQueryHandler,
)
from src.shipping_bc.shipment.application.queries.shipment_dashboard import (
    ShipmentDashboardQuery,
    ShipmentDashboardQueryHandler,
)
from src.shipping_bc.shipment.application.queries.shipments_by_asset import (
    ShipmentsByAssetQuery,
    ShipmentsByAssetQueryHandler,
)
from src.shipping_bc.shipment.domain.entities import (
    Shipment,
)
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    ShipmentDirection,
    ShipmentStatus,
)


def _make_shipment(**overrides):
    defaults = dict(
        id="ship-1",
        company_id="comp-1",
        direction=ShipmentDirection.OUTBOUND,
        destination_type=DestinationType.EMPLOYEE_HOME,
        destination_address_id="addr-1",
        created_by="user-1",
    )
    defaults.update(overrides)
    return Shipment.create(**defaults)


class TestListShipments:
    def test_list_returns_paginated(self):
        repo = MagicMock()
        shipments = [_make_shipment()]
        repo.find_all.return_value = (shipments, 1)
        handler = ListShipmentsQueryHandler(
            shipment_repo=repo,
        )

        result = handler.handle(
            ListShipmentsQuery(
                company_id="comp-1",
                page=1,
                page_size=20,
            )
        )

        items, total = result
        assert len(items) == 1
        assert total == 1


class TestGetShipment:
    def test_get_returns_shipment(self):
        repo = MagicMock()
        shipment = _make_shipment()
        repo.find_by_id.return_value = shipment
        handler = GetShipmentQueryHandler(
            shipment_repo=repo,
        )

        result = handler.handle(
            GetShipmentQuery(
                shipment_id="ship-1",
                company_id="comp-1",
            )
        )

        assert result.id == "ship-1"

    def test_get_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetShipmentQueryHandler(
            shipment_repo=repo,
        )

        with pytest.raises(ShipmentNotFoundError):
            handler.handle(
                GetShipmentQuery(
                    shipment_id="nope",
                    company_id="comp-1",
                )
            )


class TestShipmentsByAsset:
    def test_by_asset_returns_history(self):
        repo = MagicMock()
        repo.find_by_asset_id.return_value = [
            _make_shipment(),
        ]
        handler = ShipmentsByAssetQueryHandler(
            shipment_repo=repo,
        )

        result = handler.handle(
            ShipmentsByAssetQuery(
                asset_id="asset-1",
                company_id="comp-1",
            )
        )

        assert len(result) == 1


class TestMyShipments:
    def test_my_shipments_filters_by_recipient(self):
        repo = MagicMock()
        repo.find_by_recipient_user_id.return_value = (
            [_make_shipment()],
            1,
        )
        handler = MyShipmentsQueryHandler(
            shipment_repo=repo,
        )

        result = handler.handle(
            MyShipmentsQuery(
                recipient_user_id="emp-1",
                company_id="comp-1",
            )
        )

        items, total = result
        assert len(items) == 1
        repo.find_by_recipient_user_id.assert_called_once_with(
            recipient_user_id="emp-1",
            company_id="comp-1",
            page=1,
            page_size=20,
        )


class TestShipmentDashboard:
    def test_dashboard_returns_summary(self):
        repo = MagicMock()
        repo.count_by_status.return_value = {
            "DRAFT": 2,
            "DISPATCHED": 3,
        }
        repo.find_recent_delivered.return_value = [
            _make_shipment(),
        ]
        repo.find_by_status.return_value = []
        handler = ShipmentDashboardQueryHandler(
            shipment_repo=repo,
        )

        result = handler.handle(
            ShipmentDashboardQuery(
                company_id="comp-1",
            )
        )

        assert result.active_by_status["DRAFT"] == 2
        assert len(result.recent_deliveries) == 1
        assert result.failed_count == 0
