from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus
from src.reseller_bc.client.application.queries.list_reseller_clients import (
    ListResellerClientsQuery,
    ListResellerClientsQueryHandler,
)
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource


def _make_client(company_id="comp-1", is_demo=False, **overrides):
    defaults = dict(
        id="client-1",
        reseller_id="res-1",
        company_id=company_id,
        source=ClientSource.MANUAL,
        is_demo=is_demo,
        demo_expires_at=datetime.utcnow() + timedelta(days=14) if is_demo else None,
        created_at=datetime.utcnow(),
    )
    defaults.update(overrides)
    return ResellerClient(**defaults)


def _make_company(company_id="comp-1", name="Test Corp", **overrides):
    return Company(
        id=company_id,
        name=name,
        status=overrides.get("status", CompanyStatus.ACTIVE),
        plan=overrides.get("plan", PlanTier.FREE),
    )


class TestListResellerClientsQueryHandler:
    def setup_method(self):
        self.client_repo = MagicMock()
        self.company_repo = MagicMock()
        self.handler = ListResellerClientsQueryHandler(
            client_repo=self.client_repo,
            company_repo=self.company_repo,
        )

    def test_empty_list(self):
        self.client_repo.find_by_reseller_id.return_value = []
        self.client_repo.count_by_reseller_id.return_value = 0

        result = self.handler.handle(ListResellerClientsQuery(reseller_id="res-1"))

        assert result.items == []
        assert result.total == 0

    def test_with_clients(self):
        client = _make_client(company_id="comp-1")
        company = _make_company(company_id="comp-1", name="Acme Corp")

        self.client_repo.find_by_reseller_id.return_value = [client]
        self.client_repo.count_by_reseller_id.return_value = 1
        self.company_repo.find_by_id.return_value = company

        result = self.handler.handle(ListResellerClientsQuery(reseller_id="res-1"))

        assert len(result.items) == 1
        assert result.total == 1
        assert result.items[0].company_name == "Acme Corp"
        assert result.items[0].plan == "free"
        assert result.items[0].company_status == "active"
        assert result.items[0].is_demo is False

    def test_with_demo_client(self):
        client = _make_client(company_id="comp-1", is_demo=True)
        company = _make_company(company_id="comp-1")

        self.client_repo.find_by_reseller_id.return_value = [client]
        self.client_repo.count_by_reseller_id.return_value = 1
        self.company_repo.find_by_id.return_value = company

        result = self.handler.handle(ListResellerClientsQuery(reseller_id="res-1"))

        assert result.items[0].is_demo is True
        assert result.items[0].demo_expires_at is not None

    def test_pagination_params_forwarded(self):
        self.client_repo.find_by_reseller_id.return_value = []
        self.client_repo.count_by_reseller_id.return_value = 0

        self.handler.handle(ListResellerClientsQuery(
            reseller_id="res-1", offset=10, limit=25,
        ))

        self.client_repo.find_by_reseller_id.assert_called_once_with(
            "res-1", offset=10, limit=25,
        )

    def test_deleted_company_fallback(self):
        client = _make_client(company_id="comp-deleted")

        self.client_repo.find_by_reseller_id.return_value = [client]
        self.client_repo.count_by_reseller_id.return_value = 1
        self.company_repo.find_by_id.return_value = None  # company not found

        result = self.handler.handle(ListResellerClientsQuery(reseller_id="res-1"))

        assert result.items[0].company_name == "(deleted)"
        assert result.items[0].company_status == "deactivated"

    def test_multiple_clients(self):
        clients = [
            _make_client(id="c1", company_id="comp-1"),
            _make_client(id="c2", company_id="comp-2"),
        ]
        companies = {
            "comp-1": _make_company(company_id="comp-1", name="Corp A"),
            "comp-2": _make_company(company_id="comp-2", name="Corp B"),
        }

        self.client_repo.find_by_reseller_id.return_value = clients
        self.client_repo.count_by_reseller_id.return_value = 2
        self.company_repo.find_by_id.side_effect = lambda cid: companies.get(cid)

        result = self.handler.handle(ListResellerClientsQuery(reseller_id="res-1"))

        assert len(result.items) == 2
        assert result.total == 2
        names = {item.company_name for item in result.items}
        assert names == {"Corp A", "Corp B"}
