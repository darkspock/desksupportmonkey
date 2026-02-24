"""Unit tests for MCP asset tools."""
import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.assets import (  # noqa: E402
    handle_assign_asset,
    handle_change_asset_status,
    handle_create_asset,
    handle_get_asset,
    handle_get_asset_history,
    handle_import_assets,
    handle_list_assets,
    handle_list_assignable_users,
    handle_unassign_asset,
    handle_update_asset,
)
from core.tenant import TenantContext  # noqa: E402
from src.asset_bc.asset.application.commands import (  # noqa: E402
    create_asset as _ca,
    import_assets as _ia,
)

SerialNumberExistsError = _ca.SerialNumberExistsError
ImportResult = _ia.ImportResult
InvalidCSVError = _ia.InvalidCSVError
from src.asset_bc.asset.application.queries.get_asset import (  # noqa: E402
    AssetNotFoundError,
)
from src.asset_bc.asset.domain.entities import (  # noqa: E402
    Asset,
    AssetEvent,
    InvalidAssignmentError,
)
from src.asset_bc.asset.domain.enums import (  # noqa: E402
    AssetStatus,
    InvalidStatusTransitionError,
)


def _make_asset(**overrides) -> Asset:
    defaults = {
        "id": "asset-1",
        "company_id": "company-1",
        "type": "laptop",
        "brand": "Dell",
        "model": "XPS 15",
        "serial_number": "SN-001",
        "status": AssetStatus.IN_STOCK,
        "assigned_to": None,
        "department_id": None,
        "purchase_date": date(2024, 1, 15),
        "warranty_expiration": date(2027, 1, 15),
        "notes": None,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "updated_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return Asset(**defaults)


def _make_tenant(**overrides) -> TenantContext:
    defaults = {
        "company_id": "company-1",
        "user_id": "user-1",
        "role": "technician",
    }
    defaults.update(overrides)
    return TenantContext(**defaults)


def _parse_result(result):
    """Parse the JSON from a TextContent result list."""
    assert len(result) == 1
    return json.loads(result[0].text)


@pytest.fixture
def mock_db():
    with patch(
        "adapters.mcp.tools.assets.SessionLocal"
    ) as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_tenant():
    tenant = _make_tenant()
    with patch(
        "adapters.mcp.tools.assets.get_tenant",
        return_value=tenant,
    ):
        yield tenant


_P = "adapters.mcp.tools.assets"


class TestCreateAsset:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        asset = _make_asset()

        with patch(
            f"{_P}.CreateAssetCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.find_by_serial_number.return_value = asset
            MockHandler.return_value.handle.return_value = (
                None
            )

            result = await handle_create_asset({
                "type": "laptop",
                "brand": "Dell",
                "model": "XPS 15",
                "serial_number": "SN-001",
            })

        data = _parse_result(result)
        assert data["brand"] == "Dell"
        assert data["serial_number"] == "SN-001"
        assert data["type"] == "laptop"

    @pytest.mark.asyncio
    async def test_serial_number_exists(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.CreateAssetCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                SerialNumberExistsError(
                    "Serial 'SN-001' already exists"
                )
            )

            result = await handle_create_asset({
                "type": "laptop",
                "brand": "Dell",
                "model": "XPS 15",
                "serial_number": "SN-001",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "SN-001" in data["error"]


class TestListAssets:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        assets = [
            _make_asset(),
            _make_asset(
                id="asset-2", serial_number="SN-002",
            ),
        ]

        with patch(
            f"{_P}.ListAssetsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                assets, 2,
            )

            result = await handle_list_assets({
                "page": 1, "page_size": 20,
            })

        data = _parse_result(result)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_with_filters(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ListAssetsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                [], 0,
            )

            result = await handle_list_assets({
                "status": "in_stock",
                "type": "laptop",
            })

        data = _parse_result(result)
        assert data["total"] == 0
        assert data["items"] == []


class TestGetAsset:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        asset = _make_asset()

        with patch(
            f"{_P}.GetAssetQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                asset
            )

            result = await handle_get_asset({
                "asset_id": "asset-1",
            })

        data = _parse_result(result)
        assert data["id"] == "asset-1"
        assert data["brand"] == "Dell"

    @pytest.mark.asyncio
    async def test_not_found(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.GetAssetQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                AssetNotFoundError(
                    "Asset 'xyz' not found"
                )
            )

            result = await handle_get_asset({
                "asset_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestUpdateAsset:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        updated_asset = _make_asset(brand="Lenovo")

        with patch(
            f"{_P}.UpdateAssetCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetAssetQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.AssetRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                updated_asset
            )

            result = await handle_update_asset({
                "asset_id": "asset-1",
                "brand": "Lenovo",
            })

        data = _parse_result(result)
        assert data["brand"] == "Lenovo"

    @pytest.mark.asyncio
    async def test_not_found(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.UpdateAssetCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.AssetRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                AssetNotFoundError(
                    "Asset 'xyz' not found"
                )
            )

            result = await handle_update_asset({
                "asset_id": "xyz",
                "brand": "Lenovo",
            })

        data = _parse_result(result)
        assert "error" in data


class TestChangeAssetStatus:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        asset = _make_asset(status=AssetStatus.IN_REPAIR)

        with patch(
            f"{_P}.ChangeAssetStatusCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetAssetQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.AssetRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                asset
            )

            result = await handle_change_asset_status({
                "asset_id": "asset-1",
                "new_status": "in_repair",
            })

        data = _parse_result(result)
        assert data["status"] == "in_repair"

    @pytest.mark.asyncio
    async def test_invalid_transition(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ChangeAssetStatusCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.AssetRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                InvalidStatusTransitionError(
                    AssetStatus.DECOMMISSIONED,
                    AssetStatus.IN_STOCK,
                )
            )

            result = await handle_change_asset_status({
                "asset_id": "asset-1",
                "new_status": "in_stock",
            })

        data = _parse_result(result)
        assert "error" in data


class TestAssignAsset:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        asset = _make_asset(
            status=AssetStatus.ASSIGNED,
            assigned_to="user-2",
        )

        with patch(
            f"{_P}.AssignAssetCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetAssetQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.AssetRepository"
        ), patch(
            f"{_P}.UserRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                asset
            )

            result = await handle_assign_asset({
                "asset_id": "asset-1",
                "user_id": "user-2",
            })

        data = _parse_result(result)
        assert data["assigned_to"] == "user-2"
        assert data["status"] == "assigned"

    @pytest.mark.asyncio
    async def test_invalid_assignment(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.AssignAssetCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.AssetRepository"
        ), patch(
            f"{_P}.UserRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                InvalidAssignmentError(
                    "Asset must be in stock to assign"
                )
            )

            result = await handle_assign_asset({
                "asset_id": "asset-1",
                "user_id": "user-2",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "in stock" in data["error"]


class TestUnassignAsset:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        asset = _make_asset(
            status=AssetStatus.IN_STOCK,
            assigned_to=None,
        )

        with patch(
            f"{_P}.UnassignAssetCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetAssetQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.AssetRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                asset
            )

            result = await handle_unassign_asset({
                "asset_id": "asset-1",
            })

        data = _parse_result(result)
        assert data["status"] == "in_stock"
        assert data["assigned_to"] is None

    @pytest.mark.asyncio
    async def test_not_assigned(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.UnassignAssetCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.AssetRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                InvalidAssignmentError(
                    "Asset is not currently assigned"
                )
            )

            result = await handle_unassign_asset({
                "asset_id": "asset-1",
            })

        data = _parse_result(result)
        assert "error" in data


class TestGetAssetHistory:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        events = [
            AssetEvent(
                id="evt-1",
                asset_id="asset-1",
                event_type="created",
                data={"type": "laptop"},
                performed_by="user-1",
                created_at=datetime(
                    2024, 1, 15, 10, 0, 0,
                ),
            ),
        ]

        with patch(
            f"{_P}.GetAssetHistoryQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                events
            )

            result = await handle_get_asset_history({
                "asset_id": "asset-1",
            })

        data = _parse_result(result)
        assert len(data) == 1
        assert data[0]["event_type"] == "created"
        assert data[0]["performed_by"] == "user-1"

    @pytest.mark.asyncio
    async def test_asset_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.GetAssetHistoryQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                AssetNotFoundError(
                    "Asset 'xyz' not found"
                )
            )

            result = await handle_get_asset_history({
                "asset_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data


class TestImportAssets:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.ImportAssetsService"
        ) as MockService, patch(
            f"{_P}.AssetRepository"
        ):
            MockService.return_value.handle.return_value = (
                ImportResult(
                    total=3, successful=3, failed=[],
                )
            )

            csv = (
                "type,brand,model,serial_number\n"
                "laptop,Dell,XPS,SN1"
            )
            result = await handle_import_assets({
                "csv_content": csv,
            })

        data = _parse_result(result)
        assert data["total"] == 3
        assert data["successful"] == 3
        assert data["failed"] == []

    @pytest.mark.asyncio
    async def test_invalid_csv(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ImportAssetsService"
        ) as MockService, patch(
            f"{_P}.AssetRepository"
        ):
            MockService.return_value.handle.side_effect = (
                InvalidCSVError(
                    "Missing required columns: type"
                )
            )

            result = await handle_import_assets({
                "csv_content": "brand,model\n",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "Missing required columns" in data["error"]


class TestListAssignableUsers:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        mock_user = MagicMock()
        mock_user.id = "user-2"
        mock_user.email = "user@example.com"
        mock_user.name = "John Doe"

        with patch(
            f"{_P}.UserRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.find_all_by_company.return_value = (
                [mock_user],
                1,
            )

            result = await handle_list_assignable_users(
                {}
            )

        data = _parse_result(result)
        assert len(data) == 1
        assert data[0]["id"] == "user-2"
        assert data[0]["email"] == "user@example.com"
        assert data[0]["name"] == "John Doe"
