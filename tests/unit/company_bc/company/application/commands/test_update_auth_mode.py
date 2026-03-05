from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.update_auth_mode import (
    UpdateAuthModeCommand,
    UpdateAuthModeCommandHandler,
)
from src.company_bc.company.domain.entities import Company, NoAdminMembershipError
from src.company_bc.company.domain.enums import AuthMode


@pytest.fixture
def company_repo():
    return MagicMock()


@pytest.fixture
def company_user_repo():
    return MagicMock()


@pytest.fixture
def handler(company_repo, company_user_repo):
    return UpdateAuthModeCommandHandler(
        company_repo=company_repo,
        company_user_repo=company_user_repo,
    )


@pytest.fixture
def existing_company():
    company = Company.create(name="Acme Corp", email_domains=["acme.com"])
    company.auth_mode = AuthMode.DOMAIN
    return company


class TestUpdateAuthModeCommandHandler:
    def test_switch_domain_to_membership_only_succeeds(
        self, handler, company_repo, company_user_repo, existing_company,
    ):
        company_repo.find_by_id.return_value = existing_company
        company_user_repo.count_admins_in_company.return_value = 1

        handler.handle(
            UpdateAuthModeCommand(
                company_id=existing_company.id, auth_mode="membership_only",
            )
        )

        assert existing_company.auth_mode == AuthMode.MEMBERSHIP_ONLY
        company_repo.save.assert_called_once_with(existing_company)

    def test_switch_membership_only_to_domain_succeeds(
        self, handler, company_repo, company_user_repo, existing_company,
    ):
        existing_company.auth_mode = AuthMode.MEMBERSHIP_ONLY
        company_repo.find_by_id.return_value = existing_company

        handler.handle(
            UpdateAuthModeCommand(
                company_id=existing_company.id, auth_mode="domain",
            )
        )

        assert existing_company.auth_mode == AuthMode.DOMAIN
        company_repo.save.assert_called_once_with(existing_company)
        company_user_repo.count_admins_in_company.assert_not_called()

    def test_lockout_prevention_zero_admins_raises(
        self, handler, company_repo, company_user_repo, existing_company,
    ):
        company_repo.find_by_id.return_value = existing_company
        company_user_repo.count_admins_in_company.return_value = 0

        with pytest.raises(NoAdminMembershipError):
            handler.handle(
                UpdateAuthModeCommand(
                    company_id=existing_company.id, auth_mode="membership_only",
                )
            )

        company_repo.save.assert_not_called()

    def test_invalid_auth_mode_raises(
        self, handler, company_repo, existing_company,
    ):
        company_repo.find_by_id.return_value = existing_company

        with pytest.raises(ValueError, match="Invalid auth mode"):
            handler.handle(
                UpdateAuthModeCommand(
                    company_id=existing_company.id, auth_mode="invalid_mode",
                )
            )

        company_repo.save.assert_not_called()

    def test_company_not_found_raises(
        self, handler, company_repo,
    ):
        company_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="Company not found"):
            handler.handle(
                UpdateAuthModeCommand(
                    company_id="nonexistent", auth_mode="domain",
                )
            )

        company_repo.save.assert_not_called()

    def test_saves_company_after_mode_change(
        self, handler, company_repo, company_user_repo, existing_company,
    ):
        company_repo.find_by_id.return_value = existing_company
        company_user_repo.count_admins_in_company.return_value = 3

        handler.handle(
            UpdateAuthModeCommand(
                company_id=existing_company.id, auth_mode="membership_only",
            )
        )

        company_repo.save.assert_called_once()
        saved_company = company_repo.save.call_args[0][0]
        assert saved_company.auth_mode == AuthMode.MEMBERSHIP_ONLY

    def test_does_not_save_when_validation_fails(
        self, handler, company_repo, company_user_repo, existing_company,
    ):
        company_repo.find_by_id.return_value = existing_company
        company_user_repo.count_admins_in_company.return_value = 0

        with pytest.raises(NoAdminMembershipError):
            handler.handle(
                UpdateAuthModeCommand(
                    company_id=existing_company.id, auth_mode="membership_only",
                )
            )

        company_repo.save.assert_not_called()
