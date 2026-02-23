from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from core.stripe_client import StripeClient
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


class CompanyNotFoundError(Exception):
    pass


@dataclass
class InvoiceDto:
    invoice_id: str
    date: datetime
    period_start: datetime
    period_end: datetime
    amount_cents: int
    currency: str
    status: str
    invoice_url: Optional[str]
    pdf_url: Optional[str]


@dataclass
class GetCompanyInvoicesQuery(Query):
    company_id: str
    limit: int = 20


class GetCompanyInvoicesQueryHandler(
    QueryHandler[GetCompanyInvoicesQuery, list[InvoiceDto]]
):
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        stripe_client: StripeClient,
    ) -> None:
        self.company_repo = company_repo
        self.stripe_client = stripe_client

    def handle(self, query: GetCompanyInvoicesQuery) -> list[InvoiceDto]:
        company = self.company_repo.find_by_id(query.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        if not company.stripe_customer_id:
            return []
        raw = self.stripe_client.list_invoices(
            stripe_customer_id=company.stripe_customer_id,
            limit=min(query.limit, 100),
        )
        return [
            InvoiceDto(
                invoice_id=inv["id"],
                date=datetime.fromtimestamp(inv["created"], tz=timezone.utc),
                period_start=datetime.fromtimestamp(
                    inv["period_start"], tz=timezone.utc
                ),
                period_end=datetime.fromtimestamp(inv["period_end"], tz=timezone.utc),
                amount_cents=(
                    inv["amount_paid"]
                    if inv["status"] == "paid"
                    else inv["amount_due"]
                ),
                currency=inv["currency"],
                status=inv["status"],
                invoice_url=inv.get("hosted_invoice_url"),
                pdf_url=inv.get("invoice_pdf"),
            )
            for inv in raw
        ]
