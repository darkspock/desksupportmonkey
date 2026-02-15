from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.auth_bc.magic_link.application.commands.verify_magic_link import (
    CompanyRestrictedError,
    ExpiredTokenError,
    InvalidTokenError,
    UsedTokenError,
    VerifyMagicLinkCommand,
    VerifyMagicLinkCommandHandler,
)
from src.auth_bc.magic_link.domain.entities import MagicLink
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _make_valid_magic_link():
    ml = MagicLink.create(email="user@company.com")
    return ml


def _make_user():
    return User.create(email="user@company.com", role=UserRole.EMPLOYEE, company_id="comp123")


class TestVerifyMagicLinkCommandHandler:
    def setup_method(self):
        self.magic_link_repo = MagicMock()
        self.user_repo = MagicMock()
        self.company_lookup = MagicMock()
        self.jwt_service = MagicMock()
        self.handler = VerifyMagicLinkCommandHandler(
            magic_link_repo=self.magic_link_repo,
            user_repo=self.user_repo,
            company_lookup=self.company_lookup,
            jwt_service=self.jwt_service,
        )

    def test_success_existing_user(self):
        ml = _make_valid_magic_link()
        user = _make_user()
        self.magic_link_repo.find_by_token.return_value = ml
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", True)
        self.user_repo.find_by_email.return_value = user
        self.jwt_service.create_token.return_value = "jwt-token"

        result = self.handler.handle(VerifyMagicLinkCommand(token=ml.token))

        assert result == "jwt-token"
        self.magic_link_repo.update_used_at.assert_called_once()

    def test_success_new_user(self):
        ml = _make_valid_magic_link()
        self.magic_link_repo.find_by_token.return_value = ml
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", True)
        self.user_repo.find_by_email.return_value = None
        self.jwt_service.create_token.return_value = "jwt-token"

        result = self.handler.handle(VerifyMagicLinkCommand(token=ml.token))

        assert result == "jwt-token"
        self.user_repo.save.assert_called_once()

    def test_invalid_token(self):
        self.magic_link_repo.find_by_token.return_value = None

        with pytest.raises(InvalidTokenError):
            self.handler.handle(VerifyMagicLinkCommand(token="bad-token"))

    def test_used_token(self):
        ml = _make_valid_magic_link()
        ml.mark_used()
        self.magic_link_repo.find_by_token.return_value = ml

        with pytest.raises(UsedTokenError):
            self.handler.handle(VerifyMagicLinkCommand(token=ml.token))

    def test_expired_token(self):
        ml = _make_valid_magic_link()
        ml.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        self.magic_link_repo.find_by_token.return_value = ml

        with pytest.raises(ExpiredTokenError):
            self.handler.handle(VerifyMagicLinkCommand(token=ml.token))

    def test_company_restricted(self):
        ml = _make_valid_magic_link()
        self.magic_link_repo.find_by_token.return_value = ml
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", False)

        with pytest.raises(CompanyRestrictedError):
            self.handler.handle(VerifyMagicLinkCommand(token=ml.token))

    def test_deactivated_user(self):
        ml = _make_valid_magic_link()
        user = _make_user()
        user.deactivate()
        self.magic_link_repo.find_by_token.return_value = ml
        self.company_lookup.find_company_by_email_domain.return_value = ("comp123", True)
        self.user_repo.find_by_email.return_value = user

        with pytest.raises(InvalidTokenError):
            self.handler.handle(VerifyMagicLinkCommand(token=ml.token))
