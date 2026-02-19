from unittest.mock import MagicMock

import pytest

from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.equipment_profile.application.commands.delete_profile import (  # noqa: E501
    DeleteEquipmentProfileCommand,
    DeleteEquipmentProfileCommandHandler,
    ProfileNotFoundError,
)
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
)


class TestDeleteEquipmentProfile:
    def test_success(self):
        profile = EquipmentProfile.create(
            id="prof1",
            company_id="comp1",
            department_id="dept1",
            role=UserRole.EMPLOYEE,
        )
        repo = MagicMock()
        repo.find_by_id.return_value = profile

        handler = DeleteEquipmentProfileCommandHandler(
            profile_repo=repo,
        )
        handler.handle(
            DeleteEquipmentProfileCommand(
                profile_id="prof1",
                company_id="comp1",
                performed_by="admin1",
            )
        )

        repo.delete.assert_called_once_with("prof1")

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = DeleteEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        with pytest.raises(ProfileNotFoundError):
            handler.handle(
                DeleteEquipmentProfileCommand(
                    profile_id="bad",
                    company_id="comp1",
                    performed_by="admin1",
                )
            )

        repo.delete.assert_not_called()
