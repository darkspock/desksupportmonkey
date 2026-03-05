from unittest.mock import MagicMock, patch

import pytest

from src.reseller_bc.reseller.application.commands.register_reseller import (
    RegisterResellerCommand,
    RegisterResellerCommandHandler,
)
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerAlreadyExistsException,
    ResellerInvalidPasswordException,
)


class TestRegisterResellerCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.password_service = MagicMock()
        self.password_service.hash_password.return_value = "hashed_pw"
        self.handler = RegisterResellerCommandHandler(
            repo=self.repo, password_service=self.password_service,
        )

    @patch("core.tasks.reseller_emails.send_reseller_registration_confirmation")
    @patch("core.tasks.reseller_emails.send_reseller_admin_notification")
    def test_register_success(self, mock_admin_email, mock_confirm_email):
        self.repo.exists_by_email.return_value = False

        self.handler.handle(RegisterResellerCommand(
            name="John Doe",
            email="john@example.com",
            company_name="Acme Inc",
            password="securepass123",
        ))

        self.repo.save.assert_called_once()
        saved = self.repo.save.call_args[0][0]
        assert saved.email == "john@example.com"
        assert saved.name == "John Doe"
        assert saved.company_name == "Acme Inc"
        assert saved.status == ResellerStatus.PENDING
        assert saved.password_hash == "hashed_pw"
        mock_confirm_email.delay.assert_called_once()
        mock_admin_email.delay.assert_called_once()

    def test_register_duplicate_email(self):
        self.repo.exists_by_email.return_value = True

        with pytest.raises(ResellerAlreadyExistsException):
            self.handler.handle(RegisterResellerCommand(
                name="John Doe",
                email="existing@example.com",
                company_name="Acme",
                password="securepass123",
            ))

        self.repo.save.assert_not_called()

    def test_register_short_password(self):
        self.repo.exists_by_email.return_value = False

        with pytest.raises(ResellerInvalidPasswordException):
            self.handler.handle(RegisterResellerCommand(
                name="John Doe",
                email="john@example.com",
                company_name="Acme",
                password="short",
            ))

        self.repo.save.assert_not_called()
