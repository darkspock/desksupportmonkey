from unittest.mock import MagicMock

import pytest

from core.stripe_client import StripeUnavailableError
from src.company_bc.company.application.queries.billing.get_company_invoices import (
    CompanyNotFoundError,
    GetCompanyInvoicesQuery,
    GetCompanyInvoicesQueryHandler,
)
from src.company_bc.company.domain.entities import Company


def _make_company(**kwargs) -> Company:
    company = Company.create(name="Acme", email_domains=["acme.com"])
    for k, v in kwargs.items():
        setattr(company, k, v)
    return company


def _make_handler(company=None, invoices=None):
    repo = MagicMock()
    repo.find_by_id.return_value = company
    stripe = MagicMock()
    stripe.list_invoices.return_value = invoices or []
    return GetCompanyInvoicesQueryHandler(company_repo=repo, stripe_client=stripe)


SAMPLE_INVOICE = {
    "id": "inv_123",
    "created": 1700000000,
    "period_start": 1699900000,
    "period_end": 1700000000,
    "amount_paid": 4900,
    "amount_due": 4900,
    "currency": "usd",
    "status": "paid",
    "hosted_invoice_url": "https://stripe.com/inv",
    "invoice_pdf": "https://stripe.com/inv.pdf",
}


class TestGetCompanyInvoicesQueryHandler:
    def test_not_found_raises(self):
        handler = _make_handler(company=None)
        with pytest.raises(CompanyNotFoundError):
            handler.handle(GetCompanyInvoicesQuery(company_id="nonexistent"))

    def test_no_stripe_customer_id_returns_empty(self):
        company = _make_company(stripe_customer_id=None)
        handler = _make_handler(company=company)
        result = handler.handle(GetCompanyInvoicesQuery(company_id=company.id))
        assert result == []

    def test_maps_stripe_response_correctly(self):
        company = _make_company(stripe_customer_id="cus_abc")
        handler = _make_handler(company=company, invoices=[SAMPLE_INVOICE])
        result = handler.handle(GetCompanyInvoicesQuery(company_id=company.id))
        assert len(result) == 1
        inv = result[0]
        assert inv.invoice_id == "inv_123"
        assert inv.amount_cents == 4900
        assert inv.status == "paid"
        assert inv.currency == "usd"
        assert inv.invoice_url == "https://stripe.com/inv"
        assert inv.pdf_url == "https://stripe.com/inv.pdf"

    def test_open_invoice_uses_amount_due(self):
        open_inv = {**SAMPLE_INVOICE, "status": "open", "amount_due": 9900, "amount_paid": 0}
        company = _make_company(stripe_customer_id="cus_abc")
        handler = _make_handler(company=company, invoices=[open_inv])
        result = handler.handle(GetCompanyInvoicesQuery(company_id=company.id))
        assert result[0].amount_cents == 9900

    def test_limit_capped_at_100(self):
        company = _make_company(stripe_customer_id="cus_abc")
        handler = _make_handler(company=company)
        handler.handle(GetCompanyInvoicesQuery(company_id=company.id, limit=200))
        handler.stripe_client.list_invoices.assert_called_once_with(
            stripe_customer_id="cus_abc", limit=100
        )

    def test_stripe_error_propagates(self):
        company = _make_company(stripe_customer_id="cus_abc")
        handler = _make_handler(company=company)
        handler.stripe_client.list_invoices.side_effect = StripeUnavailableError("down")
        with pytest.raises(StripeUnavailableError):
            handler.handle(GetCompanyInvoicesQuery(company_id=company.id))
