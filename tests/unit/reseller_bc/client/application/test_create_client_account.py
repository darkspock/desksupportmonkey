from unittest.mock import MagicMock

import pytest

from src.reseller_bc.client.application.commands.create_client_account import (
    CreateClientAccountCommand,
    CreateClientAccountCommandHandler,
)
from src.reseller_bc.client.domain.enums import ClientSource
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


class TestCreateClientAccountCommandHandler:
    def setup_method(self):
        self.client_repo = MagicMock()
        self.reseller_repo = MagicMock()
        self.company_handler = MagicMock()
        self.handler = CreateClientAccountCommandHandler(
            client_repo=self.client_repo,
            reseller_repo=self.reseller_repo,
            company_handler=self.company_handler,
        )

    def test_create_success(self):
        self.reseller_repo.get_by_id.return_value = _make_reseller()

        cmd = CreateClientAccountCommand(
            id="client-1",
            reseller_id="reseller-123",
            company_name="Acme Corp",
            admin_email="admin@acme.com",
        )
        self.handler.handle(cmd)

        # Company handler called with correct domain
        self.company_handler.handle.assert_called_once()
        company_cmd = self.company_handler.handle.call_args[0][0]
        assert company_cmd.name == "Acme Corp"
        assert company_cmd.email_domains == ["acme.com"]
        assert company_cmd.admin_email == "admin@acme.com"

        # ResellerClient saved
        self.client_repo.save.assert_called_once()
        saved_client = self.client_repo.save.call_args[0][0]
        assert saved_client.is_demo is False
        assert saved_client.source == ClientSource.MANUAL
        assert saved_client.id == "client-1"
        assert saved_client.demo_expires_at is None

    def test_reseller_not_found(self):
        self.reseller_repo.get_by_id.return_value = None

        cmd = CreateClientAccountCommand(
            id="client-1",
            reseller_id="nonexistent",
            company_name="Acme",
            admin_email="admin@acme.com",
        )

        with pytest.raises(ResellerNotFoundException):
            self.handler.handle(cmd)

        self.client_repo.save.assert_not_called()

    def test_reseller_suspended(self):
        self.reseller_repo.get_by_id.return_value = _make_reseller(
            status=ResellerStatus.SUSPENDED,
        )

        cmd = CreateClientAccountCommand(
            id="client-1",
            reseller_id="reseller-123",
            company_name="Acme",
            admin_email="admin@acme.com",
        )

        with pytest.raises(ResellerSuspendedException):
            self.handler.handle(cmd)

        self.client_repo.save.assert_not_called()

    def test_derives_domain_from_email(self):
        self.reseller_repo.get_by_id.return_value = _make_reseller()

        cmd = CreateClientAccountCommand(
            id="client-1",
            reseller_id="reseller-123",
            company_name="BigCorp",
            admin_email="john.doe@BIGCORP.COM",
        )
        self.handler.handle(cmd)

        company_cmd = self.company_handler.handle.call_args[0][0]
        assert company_cmd.email_domains == ["bigcorp.com"]

    def test_propagates_company_creation_error(self):
        """CompanyNameExistsError and similar should propagate."""
        from src.company_bc.company.application.commands.create_company import (
            CompanyNameExistsError,
        )

        self.reseller_repo.get_by_id.return_value = _make_reseller()
        self.company_handler.handle.side_effect = CompanyNameExistsError("Acme")

        cmd = CreateClientAccountCommand(
            id="client-1",
            reseller_id="reseller-123",
            company_name="Acme",
            admin_email="admin@acme.com",
        )

        with pytest.raises(CompanyNameExistsError):
            self.handler.handle(cmd)

        self.client_repo.save.assert_not_called()
