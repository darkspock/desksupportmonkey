from unittest.mock import MagicMock

import pytest

from src.company_bc.nav_config.application.commands.save_nav_config import (
    InvalidRoleError,
    SaveNavConfigCommand,
    SaveNavConfigCommandHandler,
)
from src.company_bc.nav_config.domain.entities import CompanyNavConfig


class TestSaveNavConfigCommand:
    def test_save_creates_new_config(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = SaveNavConfigCommandHandler(nav_config_repo=repo)

        handler.handle(
            SaveNavConfigCommand(
                company_id="comp123",
                hidden_nav_items={
                    "employee": ["/my/shipments"],
                    "technician": ["/vendors"],
                },
                performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.company_id == "comp123"
        assert saved.hidden_nav_items == {
            "employee": ["/my/shipments"],
            "technician": ["/vendors"],
        }

    def test_save_updates_existing_config(self):
        existing = CompanyNavConfig.create(
            company_id="comp123",
            hidden_nav_items={"employee": ["/my/shipments"]},
        )
        repo = MagicMock()
        repo.find_by_company.return_value = existing
        handler = SaveNavConfigCommandHandler(nav_config_repo=repo)

        handler.handle(
            SaveNavConfigCommand(
                company_id="comp123",
                hidden_nav_items={
                    "technician": ["/vendors", "/shipments"],
                },
                performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        assert existing.hidden_nav_items == {
            "technician": ["/vendors", "/shipments"],
        }

    def test_accepts_admin_role(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = SaveNavConfigCommandHandler(nav_config_repo=repo)

        handler.handle(
            SaveNavConfigCommand(
                company_id="comp123",
                hidden_nav_items={"admin": ["/some/path"]},
                performed_by="user1",
            )
        )

        repo.save.assert_called_once()

    def test_rejects_super_admin_role(self):
        repo = MagicMock()
        handler = SaveNavConfigCommandHandler(nav_config_repo=repo)

        with pytest.raises(InvalidRoleError, match="super_admin"):
            handler.handle(
                SaveNavConfigCommand(
                    company_id="comp123",
                    hidden_nav_items={"super_admin": ["/some/path"]},
                    performed_by="user1",
                )
            )

        repo.save.assert_not_called()

    def test_empty_dict_clears_config(self):
        existing = CompanyNavConfig.create(
            company_id="comp123",
            hidden_nav_items={"employee": ["/my/shipments"]},
        )
        repo = MagicMock()
        repo.find_by_company.return_value = existing
        handler = SaveNavConfigCommandHandler(nav_config_repo=repo)

        handler.handle(
            SaveNavConfigCommand(
                company_id="comp123",
                hidden_nav_items={},
                performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        assert existing.hidden_nav_items == {}

    def test_strips_empty_lists(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = SaveNavConfigCommandHandler(nav_config_repo=repo)

        handler.handle(
            SaveNavConfigCommand(
                company_id="comp123",
                hidden_nav_items={
                    "employee": ["/my/shipments"],
                    "technician": [],
                },
                performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert "technician" not in saved.hidden_nav_items
        assert saved.hidden_nav_items == {"employee": ["/my/shipments"]}

    def test_accepts_procurement_manager_role(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = SaveNavConfigCommandHandler(nav_config_repo=repo)

        handler.handle(
            SaveNavConfigCommand(
                company_id="comp123",
                hidden_nav_items={
                    "procurement_manager": ["/maintenance"],
                },
                performed_by="user1",
            )
        )

        repo.save.assert_called_once()
