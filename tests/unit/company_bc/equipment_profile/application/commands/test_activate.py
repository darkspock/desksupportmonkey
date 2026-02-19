from unittest.mock import MagicMock

import pytest

from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.equipment_profile.application.commands.activate_profile import (  # noqa: E501
    ActivateEquipmentProfileCommand,
    ActivateEquipmentProfileCommandHandler,
    ProfileNotFoundError,
)
from src.company_bc.equipment_profile.application.commands.deactivate_profile import (  # noqa: E501
    DeactivateEquipmentProfileCommand,
    DeactivateEquipmentProfileCommandHandler,
    ProfileNotFoundError as DeactivateNotFoundError,
)
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
)


class TestActivateEquipmentProfile:
    def test_activate_success(self):
        profile = EquipmentProfile.create(
            id="prof1",
            company_id="comp1",
            department_id="dept1",
            role=UserRole.EMPLOYEE,
        )
        profile.deactivate()
        assert profile.is_active is False

        repo = MagicMock()
        repo.find_by_id.return_value = profile
        repo.find_active.return_value = None

        handler = ActivateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )
        handler.handle(
            ActivateEquipmentProfileCommand(
                profile_id="prof1",
                company_id="comp1",
                performed_by="admin1",
            )
        )

        assert profile.is_active is True
        repo.save.assert_called_once()

    def test_activate_deactivates_conflicting(self):
        profile = EquipmentProfile.create(
            id="prof1",
            company_id="comp1",
            department_id="dept1",
            role=UserRole.EMPLOYEE,
        )
        profile.deactivate()

        conflicting = EquipmentProfile.create(
            id="prof2",
            company_id="comp1",
            department_id="dept1",
            role=UserRole.EMPLOYEE,
        )
        assert conflicting.is_active is True

        repo = MagicMock()
        repo.find_by_id.return_value = profile
        repo.find_active.return_value = conflicting

        handler = ActivateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )
        handler.handle(
            ActivateEquipmentProfileCommand(
                profile_id="prof1",
                company_id="comp1",
                performed_by="admin1",
            )
        )

        assert conflicting.is_active is False
        assert profile.is_active is True
        assert repo.save.call_count == 2

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = ActivateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        with pytest.raises(ProfileNotFoundError):
            handler.handle(
                ActivateEquipmentProfileCommand(
                    profile_id="bad",
                    company_id="comp1",
                    performed_by="admin1",
                )
            )


class TestDeactivateEquipmentProfile:
    def test_deactivate_success(self):
        profile = EquipmentProfile.create(
            id="prof1",
            company_id="comp1",
            department_id="dept1",
            role=UserRole.EMPLOYEE,
        )
        assert profile.is_active is True

        repo = MagicMock()
        repo.find_by_id.return_value = profile

        handler = DeactivateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )
        handler.handle(
            DeactivateEquipmentProfileCommand(
                profile_id="prof1",
                company_id="comp1",
                performed_by="admin1",
            )
        )

        assert profile.is_active is False
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = DeactivateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        with pytest.raises(DeactivateNotFoundError):
            handler.handle(
                DeactivateEquipmentProfileCommand(
                    profile_id="bad",
                    company_id="comp1",
                    performed_by="admin1",
                )
            )
