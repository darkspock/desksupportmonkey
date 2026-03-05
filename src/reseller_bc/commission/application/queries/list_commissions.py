from dataclasses import dataclass

from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.commission.application.dtos import CommissionDto, CommissionListDto
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface


@dataclass
class ListCommissionsQuery(Query):
    reseller_id: str
    offset: int = 0
    limit: int = 50


class ListCommissionsQueryHandler(QueryHandler[ListCommissionsQuery, CommissionListDto]):
    def __init__(
        self,
        commission_repo: ResellerCommissionRepositoryInterface,
        company_repo: CompanyRepositoryInterface,
    ):
        self.commission_repo = commission_repo
        self.company_repo = company_repo

    def handle(self, query: ListCommissionsQuery) -> CommissionListDto:
        commissions = self.commission_repo.find_by_reseller_id(
            query.reseller_id, query.offset, query.limit
        )
        total = self.commission_repo.count_by_reseller_id(query.reseller_id)

        # Batch-load company names to avoid N+1
        company_ids = list({c.company_id for c in commissions})
        companies = {c.id: c for c in self.company_repo.find_by_ids(company_ids)} if company_ids else {}

        items = []
        for c in commissions:
            company = companies.get(c.company_id)
            items.append(CommissionDto(
                id=c.id,
                reseller_id=c.reseller_id,
                company_id=c.company_id,
                company_name=company.name if company else "Unknown",
                payment_amount_cents=c.payment_amount_cents,
                commission_pct=c.commission_pct,
                commission_amount_cents=c.commission_amount_cents,
                stripe_invoice_id=c.stripe_invoice_id,
                period_start=c.period_start,
                period_end=c.period_end,
                status=c.status.value,
                created_at=c.created_at,
            ))
        return CommissionListDto(items=items, total=total)
