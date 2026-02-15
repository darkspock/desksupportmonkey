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
