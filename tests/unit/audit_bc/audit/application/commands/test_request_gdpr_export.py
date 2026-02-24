from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.request_gdpr_export import (
    RequestGdprExportCommand,
    RequestGdprExportHandler,
)
from src.audit_bc.audit.domain.entities import GdprRequest
from src.audit_bc.audit.domain.exceptions import TargetUserNotFoundError
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


class TestRequestGdprExportHandler:
    def _make_handler(self):
        audit_repo = MagicMock()
        user_repo = MagicMock()
        handler = RequestGdprExportHandler(
            audit_repo=audit_repo, user_repo=user_repo
        )
        return handler, audit_repo, user_repo

    def _make_user(self, company_id="c1", email="user@example.com"):
        return User(
            id="u1",
            email=email,
            role=UserRole.EMPLOYEE,
            company_id=company_id,
            name="Test User",
        )

    def test_creates_export_request(self):
        handler, audit_repo, user_repo = self._make_handler()
        user_repo.find_by_email.return_value = self._make_user()

        command = RequestGdprExportCommand(
            company_id="c1",
            target_user_email="user@example.com",
            requested_by="admin1",
        )
        handler.handle(command)

        assert command.request_id is not None
        audit_repo.save_gdpr_request.assert_called_once()
        saved = audit_repo.save_gdpr_request.call_args[0][0]
        assert isinstance(saved, GdprRequest)
        assert saved.target_user_id == "u1"
        assert saved.target_user_email == "user@example.com"

    def test_raises_when_user_not_found(self):
        handler, audit_repo, user_repo = self._make_handler()
        user_repo.find_by_email.return_value = None

        with pytest.raises(TargetUserNotFoundError):
            handler.handle(
                RequestGdprExportCommand(
                    company_id="c1",
                    target_user_email="nobody@example.com",
                    requested_by="admin1",
                )
            )

        audit_repo.save_gdpr_request.assert_not_called()

    def test_raises_when_user_in_different_company(self):
        handler, audit_repo, user_repo = self._make_handler()
        user_repo.find_by_email.return_value = self._make_user(
            company_id="other_company"
        )

        with pytest.raises(TargetUserNotFoundError):
            handler.handle(
                RequestGdprExportCommand(
                    company_id="c1",
                    target_user_email="user@example.com",
                    requested_by="admin1",
                )
            )

        audit_repo.save_gdpr_request.assert_not_called()
