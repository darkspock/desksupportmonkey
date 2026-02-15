from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.commands.assign_asset import (
    AssignAssetCommand,
    AssignAssetCommandHandler,
    AssetNotFoundError as AssignAssetNotFoundError,
    UserNotFoundError,
    UserInactiveError,
)
from src.asset_bc.asset.application.commands.unassign_asset import (
    AssetNotFoundError as UnassignAssetNotFoundError,
    UnassignAssetCommand,
    UnassignAssetCommandHandler,
)
from src.asset_bc.asset.domain.entities import Asset, InvalidAssignmentError
from src.asset_bc.asset.domain.enums import AssetStatus, AssetType
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _make_asset(**overrides):
    defaults = dict(
        company_id="comp1", type=AssetType.LAPTOP,
        brand="Dell", model="Latitude", serial_number="SN001",
    )
    defaults.update(overrides)
    return Asset.create(**defaults)


def _make_user(**overrides):
    defaults = dict(email="user@test.com", role=UserRole.EMPLOYEE, company_id="comp1")
    defaults.update(overrides)
    return User.create(**defaults)


class TestAssignAssetCommand:
    def test_success(self):
        asset = _make_asset()
        user = _make_user()
        user.department_id = "dept1"

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        asset_repo.save.side_effect = lambda a: a
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user

        handler = AssignAssetCommandHandler(asset_repo=asset_repo, user_repo=user_repo)
        result = handler.handle(
            AssignAssetCommand(
                asset_id=asset.id, company_id="comp1",
                user_id=user.id, performed_by="tech1",
            )
        )

        assert result.status == AssetStatus.ASSIGNED
        assert result.assigned_to == user.id
        assert result.department_id == "dept1"
        asset_repo.save.assert_called_once()
        asset_repo.save_event.assert_called_once()
        event = asset_repo.save_event.call_args[0][0]
        assert event.event_type == "assigned"

    def test_asset_not_found_raises(self):
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = None
        user_repo = MagicMock()
        handler = AssignAssetCommandHandler(asset_repo=asset_repo, user_repo=user_repo)

        with pytest.raises(AssignAssetNotFoundError):
            handler.handle(
                AssignAssetCommand(
                    asset_id="bad", company_id="comp1",
                    user_id="u1", performed_by="tech1",
                )
            )

    def test_user_not_found_raises(self):
        asset = _make_asset()
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = None
        handler = AssignAssetCommandHandler(asset_repo=asset_repo, user_repo=user_repo)

        with pytest.raises(UserNotFoundError):
            handler.handle(
                AssignAssetCommand(
                    asset_id=asset.id, company_id="comp1",
                    user_id="bad", performed_by="tech1",
                )
            )

    def test_user_inactive_raises(self):
        asset = _make_asset()
        user = _make_user()
        user.is_active = False

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        handler = AssignAssetCommandHandler(asset_repo=asset_repo, user_repo=user_repo)

        with pytest.raises(UserInactiveError):
            handler.handle(
                AssignAssetCommand(
                    asset_id=asset.id, company_id="comp1",
                    user_id=user.id, performed_by="tech1",
                )
            )

    def test_wrong_status_raises(self):
        asset = _make_asset()
        asset.change_status(AssetStatus.IN_REPAIR)
        user = _make_user()

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = asset
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        handler = AssignAssetCommandHandler(asset_repo=asset_repo, user_repo=user_repo)

        with pytest.raises(InvalidAssignmentError):
            handler.handle(
                AssignAssetCommand(
                    asset_id=asset.id, company_id="comp1",
                    user_id=user.id, performed_by="tech1",
                )
            )


class TestUnassignAssetCommand:
    def test_success(self):
        asset = _make_asset()
        asset.assign(user_id="user1", department_id="dept1")

        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = UnassignAssetCommandHandler(asset_repo=repo)

        result = handler.handle(
            UnassignAssetCommand(
                asset_id=asset.id, company_id="comp1", performed_by="tech1",
            )
        )

        assert result.status == AssetStatus.IN_STOCK
        assert result.assigned_to is None
        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "unassigned"
        assert event.data["previous_user_id"] == "user1"

    def test_asset_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = UnassignAssetCommandHandler(asset_repo=repo)

        with pytest.raises(UnassignAssetNotFoundError):
            handler.handle(
                UnassignAssetCommand(
                    asset_id="bad", company_id="comp1", performed_by="tech1",
                )
            )

    def test_not_assigned_raises(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        handler = UnassignAssetCommandHandler(asset_repo=repo)

        with pytest.raises(InvalidAssignmentError):
            handler.handle(
                UnassignAssetCommand(
                    asset_id=asset.id, company_id="comp1", performed_by="tech1",
                )
            )
