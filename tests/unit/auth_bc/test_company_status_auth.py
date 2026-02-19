from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone

import pytest

from src.auth_bc.magic_link.application.commands.create_magic_link import (
    CompanyRestrictedError,
    CreateMagicLinkCommand,
    CreateMagicLinkCommandHandler,
)
from src.auth_bc.magic_link.application.commands.verify_magic_link import (
    CompanyRestrictedError as VerifyCompanyRestrictedError,
    VerifyMagicLinkRequest,
    VerifyMagicLinkService,
)
from src.auth_bc.magic_link.domain.entities import MagicLink


class TestCreateMagicLinkCompanyStatus:
    def test_suspended_company_raises(self):
        handler = CreateMagicLinkCommandHandler(
            magic_link_repo=MagicMock(),
            company_lookup=MagicMock(),
            email_service=MagicMock(),
        )
        # Domain found but company not active
        handler.company_lookup.find_company_by_email_domain.return_value = ("company-123", False)

        with pytest.raises(CompanyRestrictedError):
            handler.handle(CreateMagicLinkCommand(email="user@suspended.com"))

    def test_deactivated_company_raises(self):
        handler = CreateMagicLinkCommandHandler(
            magic_link_repo=MagicMock(),
            company_lookup=MagicMock(),
            email_service=MagicMock(),
        )
        handler.company_lookup.find_company_by_email_domain.return_value = ("company-123", False)

        with pytest.raises(CompanyRestrictedError):
            handler.handle(CreateMagicLinkCommand(email="user@deactivated.com"))


class TestVerifyMagicLinkCompanyStatus:
    def test_suspended_company_raises(self):
        magic_link = MagicLink.create(email="user@suspended.com")
        handler = VerifyMagicLinkService(
            magic_link_repo=MagicMock(),
            user_repo=MagicMock(),
            company_lookup=MagicMock(),
            jwt_service=MagicMock(),
        )
        handler.magic_link_repo.find_by_token.return_value = magic_link
        handler.company_lookup.find_company_by_email_domain.return_value = ("company-123", False)

        with pytest.raises(VerifyCompanyRestrictedError):
            handler.handle(VerifyMagicLinkRequest(token=magic_link.token))

    def test_active_company_succeeds(self):
        magic_link = MagicLink.create(email="user@active.com")
        user_mock = MagicMock()
        user_mock.is_active = True
        user_mock.id = "user-123"
        user_mock.company_id = "company-123"
        user_mock.role.value = "employee"

        handler = VerifyMagicLinkService(
            magic_link_repo=MagicMock(),
            user_repo=MagicMock(),
            company_lookup=MagicMock(),
            jwt_service=MagicMock(),
        )
        handler.magic_link_repo.find_by_token.return_value = magic_link
        handler.company_lookup.find_company_by_email_domain.return_value = ("company-123", True)
        handler.user_repo.find_by_email.return_value = user_mock
        handler.jwt_service.create_token.return_value = "jwt-token"

        result = handler.handle(VerifyMagicLinkRequest(token=magic_link.token))
        assert result == "jwt-token"
