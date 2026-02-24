from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.request_gdpr_anonymize import (
    RequestGdprAnonymizeCommand,
    RequestGdprAnonymizeHandler,
)
from src.audit_bc.audit.domain.entities import GdprRequest
from src.audit_bc.audit.domain.exceptions import (
    CannotAnonymizeSelfError,
    CannotAnonymizeSuperAdminError,
    TargetUserNotFoundError,
    UserAlreadyAnonymizedError,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


class TestRequestGdprAnonymizeHandler:
    def _make_handler(self):
        audit_repo = MagicMock()
        user_repo = MagicMock()
        handler = RequestGdprAnonymizeHandler(
            audit_repo=audit_repo, user_repo=user_repo
        )
        return handler, audit_repo, user_repo

    def _make_user(
        self,
        user_id="u1",
        company_id="c1",
        role=UserRole.EMPLOYEE,
        is_anonymized=False,
    ):
        return User(
            id=user_id,
            email="user@example.com",
            role=role,
            company_id=company_id,
            name="Test User",
            is_anonymized=is_anonymized,
        )

    def test_creates_anonymize_request(self):
        handler, audit_repo, user_repo = self._make_handler()
        user_repo.find_by_email.return_value = self._make_user()

        command = RequestGdprAnonymizeCommand(
            company_id="c1",
            target_user_email="user@example.com",
            requested_by="admin1",
            reason="GDPR request",
        )
        handler.handle(command)

        assert command.request_id is not None
        audit_repo.save_gdpr_request.assert_called_once()
        saved = audit_repo.save_gdpr_request.call_args[0][0]
        assert isinstance(saved, GdprRequest)
        assert saved.reason == "GDPR request"

    def test_raises_when_user_not_found(self):
        handler, audit_repo, user_repo = self._make_handler()
        user_repo.find_by_email.return_value = None

        with pytest.raises(TargetUserNotFoundError):
            handler.handle(
                RequestGdprAnonymizeCommand(
                    company_id="c1",
                    target_user_email="nobody@example.com",
                    requested_by="admin1",
                    reason="test",
                )
            )

    def test_rejects_super_admin(self):
        handler, audit_repo, user_repo = self._make_handler()
        user_repo.find_by_email.return_value = self._make_user(
            role=UserRole.SUPER_ADMIN
        )

        with pytest.raises(CannotAnonymizeSuperAdminError):
            handler.handle(
                RequestGdprAnonymizeCommand(
                    company_id="c1",
                    target_user_email="user@example.com",
                    requested_by="admin1",
                    reason="test",
                )
            )

        audit_repo.save_gdpr_request.assert_not_called()

    def test_rejects_self_anonymization(self):
        handler, audit_repo, user_repo = self._make_handler()
        user_repo.find_by_email.return_value = self._make_user(
            user_id="admin1"
        )

        with pytest.raises(CannotAnonymizeSelfError):
            handler.handle(
                RequestGdprAnonymizeCommand(
                    company_id="c1",
                    target_user_email="user@example.com",
                    requested_by="admin1",
                    reason="test",
                )
            )

        audit_repo.save_gdpr_request.assert_not_called()

    def test_rejects_already_anonymized(self):
        handler, audit_repo, user_repo = self._make_handler()
        user_repo.find_by_email.return_value = self._make_user(
            is_anonymized=True
        )

        with pytest.raises(UserAlreadyAnonymizedError):
            handler.handle(
                RequestGdprAnonymizeCommand(
                    company_id="c1",
                    target_user_email="user@example.com",
                    requested_by="admin1",
                    reason="test",
                )
            )

        audit_repo.save_gdpr_request.assert_not_called()
