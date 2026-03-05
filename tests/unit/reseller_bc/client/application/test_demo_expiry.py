from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource


def _make_client(company_id="comp-1"):
    return ResellerClient(
        id="client-1",
        reseller_id="res-1",
        company_id=company_id,
        source=ClientSource.MANUAL,
        is_demo=True,
        demo_expires_at=datetime.utcnow() - timedelta(days=15),
        created_at=datetime.utcnow() - timedelta(days=29),
    )


def _make_company(company_id="comp-1", status=CompanyStatus.ACTIVE):
    return Company(
        id=company_id,
        name="Demo Corp",
        status=status,
    )


class TestExpireDemoAccounts:
    """Tests for the expire_demo_accounts Celery task logic.

    Since the task manages its own session and uses local imports,
    we patch the source modules where the classes are defined.
    """

    def _run_task(self, expired_clients, purgeable_clients, companies_by_id):
        """Helper to run the expire_demo_accounts task with mocked dependencies."""
        session = MagicMock()
        client_repo = MagicMock()
        company_repo = MagicMock()

        client_repo.find_expired_demos.return_value = expired_clients
        client_repo.find_purgeable_demos.return_value = purgeable_clients
        company_repo.find_by_id.side_effect = lambda cid: companies_by_id.get(cid)

        with (
            patch("core.database.SessionLocal", return_value=session),
            patch(
                "src.reseller_bc.client.infrastructure.repository.ResellerClientRepository",
                return_value=client_repo,
            ),
            patch(
                "src.company_bc.company.infrastructure.repository.CompanyRepository",
                return_value=company_repo,
            ),
        ):
            from core.tasks.reseller import expire_demo_accounts
            result = expire_demo_accounts()

        return result, session, company_repo, companies_by_id

    def test_suspend_expired_demo(self):
        company = _make_company("comp-1", CompanyStatus.ACTIVE)
        result, session, company_repo, _ = self._run_task(
            expired_clients=[_make_client("comp-1")],
            purgeable_clients=[],
            companies_by_id={"comp-1": company},
        )

        assert result["suspended"] == 1
        assert result["deactivated"] == 0
        assert company.status == CompanyStatus.SUSPENDED
        company_repo.save.assert_called_once()
        session.commit.assert_called_once()

    def test_deactivate_purgeable_demo(self):
        company = _make_company("comp-2", CompanyStatus.SUSPENDED)
        result, session, company_repo, _ = self._run_task(
            expired_clients=[],
            purgeable_clients=[_make_client("comp-2")],
            companies_by_id={"comp-2": company},
        )

        assert result["suspended"] == 0
        assert result["deactivated"] == 1
        assert company.status == CompanyStatus.DEACTIVATED
        session.commit.assert_called_once()

    def test_no_expired_demos(self):
        result, session, company_repo, _ = self._run_task(
            expired_clients=[],
            purgeable_clients=[],
            companies_by_id={},
        )

        assert result["suspended"] == 0
        assert result["deactivated"] == 0
        company_repo.save.assert_not_called()

    def test_already_suspended_not_double_suspended(self):
        # Company is already suspended, so phase 1 should skip it
        company = _make_company("comp-1", CompanyStatus.SUSPENDED)
        result, _, _, _ = self._run_task(
            expired_clients=[_make_client("comp-1")],
            purgeable_clients=[],
            companies_by_id={"comp-1": company},
        )

        assert result["suspended"] == 0  # Not re-suspended
        assert result["deactivated"] == 0
