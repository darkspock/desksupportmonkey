from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.domain.enums import AssetType
from src.company_bc.equipment_profile.application.commands.create_profile import (  # noqa: E501
    ActiveProfileExistsError,
    CreateEquipmentProfileCommand,
    CreateEquipmentProfileCommandHandler,
    ProfileItemInput,
)
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
)


class TestCreateEquipmentProfile:
    def test_success(self):
        repo = MagicMock()
        repo.find_active.return_value = None
        handler = CreateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        handler.handle(
            CreateEquipmentProfileCommand(
                id="prof1",
                company_id="comp1",
                department_id="dept1",
                employee_role_id="er1",
                items=[
                    ProfileItemInput(
                        asset_type=AssetType.LAPTOP,
                        quantity=1,
                    ),
                ],
                performed_by="admin1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.id == "prof1"
        assert saved.department_id == "dept1"
        assert saved.employee_role_id == "er1"
        assert len(saved.items) == 1
        assert saved.items[0].asset_type == AssetType.LAPTOP

    def test_active_profile_exists_raises(self):
        existing = EquipmentProfile.create(
            company_id="comp1",
            department_id="dept1",
            employee_role_id="er1",
        )
        repo = MagicMock()
        repo.find_active.return_value = existing
        handler = CreateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        with pytest.raises(ActiveProfileExistsError):
            handler.handle(
                CreateEquipmentProfileCommand(
                    company_id="comp1",
                    department_id="dept1",
                    employee_role_id="er1",
                    items=[
                        ProfileItemInput(
                            asset_type=AssetType.LAPTOP,
                        ),
                    ],
                    performed_by="admin1",
                )
            )

        repo.save.assert_not_called()

    def test_multiple_items(self):
        repo = MagicMock()
        repo.find_active.return_value = None
        handler = CreateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        handler.handle(
            CreateEquipmentProfileCommand(
                id="prof2",
                company_id="comp1",
                department_id="dept1",
                employee_role_id="er2",
                items=[
                    ProfileItemInput(
                        asset_type=AssetType.LAPTOP,
                        quantity=1,
                        min_ram_gb=16,
                        min_storage_gb=512,
                    ),
                    ProfileItemInput(
                        asset_type=AssetType.MONITOR,
                        quantity=2,
                        preferred_brand="Dell",
                    ),
                ],
                performed_by="admin1",
            )
        )

        saved = repo.save.call_args[0][0]
        assert len(saved.items) == 2
        assert saved.items[0].min_ram_gb == 16
        assert saved.items[1].preferred_brand == "Dell"
        assert saved.items[1].quantity == 2

    def test_items_with_budget_cents(self):
        repo = MagicMock()
        repo.find_active.return_value = None
        handler = CreateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        handler.handle(
            CreateEquipmentProfileCommand(
                id="prof3",
                company_id="comp1",
                department_id="dept1",
                employee_role_id="er1",
                items=[
                    ProfileItemInput(
                        asset_type=AssetType.LAPTOP,
                        quantity=1,
                        budget_cents=120000,
                    ),
                    ProfileItemInput(
                        asset_type=AssetType.MONITOR,
                        quantity=1,
                        budget_cents=None,
                    ),
                ],
                performed_by="admin1",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.items[0].budget_cents == 120000
        assert saved.items[1].budget_cents is None

    def test_different_employee_role(self):
        repo = MagicMock()
        repo.find_active.return_value = None
        handler = CreateEquipmentProfileCommandHandler(
            profile_repo=repo,
        )

        handler.handle(
            CreateEquipmentProfileCommand(
                id="prof4",
                company_id="comp1",
                department_id="dept1",
                employee_role_id="er3",
                items=[
                    ProfileItemInput(
                        asset_type=AssetType.LAPTOP,
                        quantity=1,
                    ),
                ],
                performed_by="admin1",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.employee_role_id == "er3"
