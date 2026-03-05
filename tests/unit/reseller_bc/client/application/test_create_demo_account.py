from unittest.mock import MagicMock, patch

import pytest

from src.reseller_bc.client.application.commands.create_demo_account import (
    CreateDemoAccountCommand,
    CreateDemoAccountCommandHandler,
    DEMO_LIMIT,
)
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.domain.exceptions import DemoAccountLimitExceededException
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerNotFoundException,
    ResellerSuspendedException,
)


def _make_reseller(status=ResellerStatus.ACTIVE):
    return Reseller(
        id="reseller-123",
        email="partner@example.com",
        name="Partner Inc",
        commission_pct=20,
        min_payout_cents=5000,
        referral_code="abc12345",
        status=status,
    )


class TestCreateDemoAccountCommandHandler:
    def setup_method(self):
        self.client_repo = MagicMock()
        self.reseller_repo = MagicMock()
        self.company_handler = MagicMock()
        self.user_repo = MagicMock()
        self.session = MagicMock()
        self.handler = CreateDemoAccountCommandHandler(
            client_repo=self.client_repo,
            reseller_repo=self.reseller_repo,
            company_handler=self.company_handler,
            user_repo=self.user_repo,
            session=self.session,
        )

    @patch("src.reseller_bc.client.application.commands.create_demo_account.seed_company_data")
    def _make_command(self, seed_mock=None, **overrides):
        """Helper to make a command with defaults."""
        defaults = {
            "id": "client-1",
            "reseller_id": "reseller-123",
            "company_name": "Test Demo Company",
        }
        defaults.update(overrides)
        return CreateDemoAccountCommand(**defaults)

    def test_create_success(self):
        self.reseller_repo.get_by_id.return_value = _make_reseller()
        self.client_repo.count_active_demos_by_reseller_id.return_value = 0

        cmd = CreateDemoAccountCommand(
            id="client-1",
            reseller_id="reseller-123",
            company_name="Test Demo",
        )

        with patch("scripts.seed_demo_data.seed_company_data"):
            self.handler.handle(cmd)

        # Company handler called
        self.company_handler.handle.assert_called_once()
        company_cmd = self.company_handler.handle.call_args[0][0]
        assert "(Demo)" in company_cmd.name
        assert company_cmd.admin_email is None  # No magic link for demo

        # Admin user saved
        self.user_repo.save.assert_called_once()
        saved_user = self.user_repo.save.call_args[0][0]
        assert saved_user.role.value == "admin"
        assert saved_user.password_hash is not None

        # ResellerClient saved
        self.client_repo.save.assert_called_once()
        saved_client = self.client_repo.save.call_args[0][0]
        assert saved_client.is_demo is True
        assert saved_client.source == ClientSource.MANUAL
        assert saved_client.id == "client-1"

        # Result stored
        result = self.handler.result
        assert result is not None
        assert result.company_name == "Test Demo (Demo)"
        assert result.admin_password  # password is set

    def test_reseller_not_found(self):
        self.reseller_repo.get_by_id.return_value = None

        cmd = CreateDemoAccountCommand(
            id="client-1",
            reseller_id="nonexistent",
            company_name="Test",
        )

        with pytest.raises(ResellerNotFoundException):
            self.handler.handle(cmd)

        self.client_repo.save.assert_not_called()

    def test_reseller_suspended(self):
        self.reseller_repo.get_by_id.return_value = _make_reseller(
            status=ResellerStatus.SUSPENDED,
        )

        cmd = CreateDemoAccountCommand(
            id="client-1",
            reseller_id="reseller-123",
            company_name="Test",
        )

        with pytest.raises(ResellerSuspendedException):
            self.handler.handle(cmd)

        self.client_repo.save.assert_not_called()

    def test_demo_limit_exceeded(self):
        self.reseller_repo.get_by_id.return_value = _make_reseller()
        self.client_repo.count_active_demos_by_reseller_id.return_value = DEMO_LIMIT

        cmd = CreateDemoAccountCommand(
            id="client-1",
            reseller_id="reseller-123",
            company_name="Test",
        )

        with pytest.raises(DemoAccountLimitExceededException):
            self.handler.handle(cmd)

        self.client_repo.save.assert_not_called()
        self.company_handler.handle.assert_not_called()

    def test_demo_limit_at_boundary(self):
        """4 active demos (limit - 1) should still allow creation."""
        self.reseller_repo.get_by_id.return_value = _make_reseller()
        self.client_repo.count_active_demos_by_reseller_id.return_value = DEMO_LIMIT - 1

        cmd = CreateDemoAccountCommand(
            id="client-1",
            reseller_id="reseller-123",
            company_name="Test",
        )

        with patch("scripts.seed_demo_data.seed_company_data"):
            self.handler.handle(cmd)

        self.client_repo.save.assert_called_once()
