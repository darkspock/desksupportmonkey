from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.auth_bc.magic_link.application.commands.create_magic_link import (
    CompanyRestrictedError,
    CreateMagicLinkCommand,
    CreateMagicLinkCommandHandler,
    InvalidEmailDomainError,
    RateLimitExceededError,
)


class TestCreateMagicLinkCommandHandler:
    def setup_method(self):
        self.magic_link_repo = MagicMock()
        self.company_lookup = MagicMock()
        self.email_service = MagicMock()
        self.handler = CreateMagicLinkCommandHandler(
            magic_link_repo=self.magic_link_repo,
            company_lookup=self.company_lookup,
            email_service=self.email_service,
        )

    def test_success(self):
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", True)
        self.magic_link_repo.count_recent_by_email.return_value = 0

        self.handler.handle(CreateMagicLinkCommand(email="user@company.com"))

        self.magic_link_repo.save.assert_called_once()
        self.email_service.send.assert_called_once()

    def test_invalid_email_domain(self):
        self.company_lookup.find_company_by_email_domain.return_value = None

        with pytest.raises(InvalidEmailDomainError):
            self.handler.handle(CreateMagicLinkCommand(email="user@unknown.com"))

        self.magic_link_repo.save.assert_not_called()

    def test_company_restricted(self):
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", False)

        with pytest.raises(CompanyRestrictedError):
            self.handler.handle(CreateMagicLinkCommand(email="user@suspended.com"))

        self.magic_link_repo.save.assert_not_called()

    def test_rate_limit_exceeded(self):
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", True)
        self.magic_link_repo.count_recent_by_email.return_value = 5

        with pytest.raises(RateLimitExceededError):
            self.handler.handle(CreateMagicLinkCommand(email="user@company.com"))

        self.magic_link_repo.save.assert_not_called()

    def test_rate_limit_at_boundary(self):
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", True)
        self.magic_link_repo.count_recent_by_email.return_value = 4

        self.handler.handle(CreateMagicLinkCommand(email="user@company.com"))
        self.magic_link_repo.save.assert_called_once()


class TestCreateMagicLinkScoped:
    """Tests for company-scoped magic link creation (company_id set)."""

    def setup_method(self):
        self.magic_link_repo = MagicMock()
        self.company_lookup = MagicMock()
        self.email_service = MagicMock()
        self.user_repo = MagicMock()
        self.handler = CreateMagicLinkCommandHandler(
            magic_link_repo=self.magic_link_repo,
            company_lookup=self.company_lookup,
            email_service=self.email_service,
            user_repo=self.user_repo,
        )

    def test_scoped_success_email_allowed(self):
        self.company_lookup.is_email_allowed_in_company.return_value = True
        self.magic_link_repo.count_recent_by_email.return_value = 0

        self.handler.handle(
            CreateMagicLinkCommand(email="user@company.com", company_id="comp123")
        )

        self.magic_link_repo.save.assert_called_once()
        saved_link = self.magic_link_repo.save.call_args[0][0]
        assert saved_link.company_id == "comp123"
        self.email_service.send.assert_called_once()

    def test_scoped_email_not_allowed_no_existing_user(self):
        self.company_lookup.is_email_allowed_in_company.return_value = False
        self.user_repo.find_by_email.return_value = None

        with pytest.raises(InvalidEmailDomainError):
            self.handler.handle(
                CreateMagicLinkCommand(email="user@external.com", company_id="comp123")
            )

        self.magic_link_repo.save.assert_not_called()

    def test_scoped_email_not_allowed_but_existing_active_user(self):
        """Existing active user with non-matching domain is allowed (e.g. admin)."""
        from src.auth_bc.user.domain.entities import User
        from src.auth_bc.user.domain.enums import UserRole

        user = User.create(email="admin@external.com", role=UserRole.ADMIN, company_id="comp123")
        self.company_lookup.is_email_allowed_in_company.return_value = False
        self.user_repo.find_by_email.return_value = user
        self.magic_link_repo.count_recent_by_email.return_value = 0

        self.handler.handle(
            CreateMagicLinkCommand(email="admin@external.com", company_id="comp123")
        )

        self.magic_link_repo.save.assert_called_once()

    def test_scoped_email_not_allowed_inactive_user_raises(self):
        from src.auth_bc.user.domain.entities import User
        from src.auth_bc.user.domain.enums import UserRole

        user = User.create(email="user@external.com", role=UserRole.EMPLOYEE, company_id="comp123")
        user.deactivate()
        self.company_lookup.is_email_allowed_in_company.return_value = False
        self.user_repo.find_by_email.return_value = user

        with pytest.raises(InvalidEmailDomainError):
            self.handler.handle(
                CreateMagicLinkCommand(email="user@external.com", company_id="comp123")
            )

    def test_scoped_stores_company_id_on_magic_link(self):
        self.company_lookup.is_email_allowed_in_company.return_value = True
        self.magic_link_repo.count_recent_by_email.return_value = 0

        self.handler.handle(
            CreateMagicLinkCommand(email="user@company.com", company_id="comp999")
        )

        saved_link = self.magic_link_repo.save.call_args[0][0]
        assert saved_link.company_id == "comp999"

    def test_unscoped_does_not_set_company_id_on_link(self):
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", True)
        self.magic_link_repo.count_recent_by_email.return_value = 0

        self.handler.handle(CreateMagicLinkCommand(email="user@company.com"))

        saved_link = self.magic_link_repo.save.call_args[0][0]
        assert saved_link.company_id is None
