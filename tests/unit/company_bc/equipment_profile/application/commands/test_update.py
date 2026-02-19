from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.domain.enums import AssetType
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.equipment_profile.application.commands.update_profile import (  # noqa: E501
    ProfileItemInput,
    ProfileNotFoundError,
    UpdateEquipmentProfileCommand,
    UpdateEquipmentProfileCommandHandler,
)
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
    EquipmentProfileItem,
)


class TestUpdateEquipmentProfile:
    def test_success(self):
        profile = EquipmentProfile.create(
            id="prof1",
            company_id="comp1",
            department_id="dept1",
            role=UserRole.EMPLOYEE,
        )
        profile.items = [
            EquipmentProfileItem(
                id="item1",
                profile_id="prof1",
                asset_type=AssetType.LAPTOP,
            ),
        ]
        repo = MagicMock()
        repo.find_by_id.return_value = profile

        handler = UpdateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )
        handler.handle(
            UpdateEquipmentProfileCommand(
                profile_id="prof1",
                company_id="comp1",
                items=[
                    ProfileItemInput(
                        asset_type=AssetType.MONITOR,
                        quantity=2,
                    ),
                ],
                performed_by="admin1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert len(saved.items) == 1
        assert saved.items[0].asset_type == AssetType.MONITOR
        assert saved.items[0].quantity == 2

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = UpdateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        with pytest.raises(ProfileNotFoundError):
            handler.handle(
                UpdateEquipmentProfileCommand(
                    profile_id="bad",
                    company_id="comp1",
                    items=[
                        ProfileItemInput(
                            asset_type=AssetType.LAPTOP,
                        ),
                    ],
                    performed_by="admin1",
                )
            )

        repo.save.assert_not_called()
