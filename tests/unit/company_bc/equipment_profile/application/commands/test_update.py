from unittest.mock import MagicMock

import pytest

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
            employee_role_id="er1",
        )
        profile.items = [
            EquipmentProfileItem(
                id="item1",
                profile_id="prof1",
                asset_type="laptop",
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
                        asset_type="monitor",
                        quantity=2,
                    ),
                ],
                performed_by="admin1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert len(saved.items) == 1
        assert saved.items[0].asset_type == "monitor"
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
                            asset_type="laptop",
                        ),
                    ],
                    performed_by="admin1",
                )
            )

        repo.save.assert_not_called()
